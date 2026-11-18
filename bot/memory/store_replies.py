"""The reply readers the store answers from, kept out of `memory_store.py` while it grows.

Behaviour is unchanged: every definition here was moved out of `bot/modules/memory_store.py`
whole, in its original order, and that module imports the names it still uses. Nothing here
imports from that module, so there is no import to go round.
"""
import datetime
import random
import re
from ..compose import pick
from ..compose import ruledout
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
from ..memory import when as a_when
from ..memory import cause as a_reason
from ..memory import pending
from ..memory import another as second_half
from ..memory import choice as choose
from ..memory import condition
from ..memory import decided
from ..memory import company
from ..memory import spent
from ..memory import surname as family_name
from ..memory.filler import without_filler
from ..memory import guest
from ..memory import plans
from ..memory.taste import ASKS_ABOUT_A_TASTE, ASKS_FOR_TASTES, TASTE_ASKED_ABOUT
from ..memory.taste import read_all as read_tastes
from ..memory import facts as extract
from ..knowledge import cooking
from ..knowledge import units
from ..knowledge.maths import solve
from ..memory import counts as how_many
from ..memory import rates as rates_reader
from ..memory.times import answer as _the_time_they_said
from ..memory import history
from ..memory import narrow
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
from ..memory.repeat import a_narrowing_and_its_line as _a_narrowing_and_its_line
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
                          the_pronoun_said_with_a_name,
                          _the_group_word, _the_names_a_pronoun_gave,
                          _the_names_of_the_group, _the_names_they_typed, _their_job,
                          _their_taste, _they_like_sentence, _tidy_name,
                          _whether_they_have, _with_article)
from ..modules.memory_tables import (
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


def _a_count_ask(low):
    """The animal a "how many" ask counts, or "" when the line is not that ask.

    "how many cats", "how many cats do i have", "how many have i got": the count the person
    gave is the answer. None when the line is not a count ask at all.
    """
    match = COUNT_ANIMAL.match(low)
    if match:
        word = match.group(1).lower().rstrip("s")
        return "pet" if word in ("pet", "puppie", "kitten", "bunnie", "horsie") else word
    if COUNT_BARE.match(low):
        return "any"
    return None

ASKED_ALL = re.compile(
    r"(?<!not )(?<!isnt )(?<!wasnt )\bwhat did i (?:just )?(?:ask|want to know)\b"
    r"(?![^.?!]*\babout\b(?!\s+(?:me|it|that|this|them|us|earlier|before|just now|first|"
    r"originally|already|so far|last time|the other day|that time)\b))"
    r"|\bwhat was it i asked\b"
    # The reminder wrapper drops off in `_bare` ("can you remind me what i asked about"), and
    # the ask arrives without its "did": the same rule as above - a time or nothing after
    # "about" is the whole conversation, a named thing is that one recall.
    r"|(?<!not )(?<!isnt )(?<!wasnt )\bwhat i (?:just )?(?:asked|want to know)\b"
    r"(?=\s*(?:about\s*)?(?:\?|$|again\b|please\b|before\b|earlier\b|just now\b|first\b|"
    r"then\b|so far\b|already\b|the other day\b))")

MORE_OF_IT = re.compile(r"\b(what|anything|everything)\s+(?:else|more|other(?: things?)?)\b")

FIRST_ASK_BARE = re.compile(
    r"\bwhat i (?:asked|said|tell|told)(?: you)?(?: \w+){0,2} (?:first|at the (?:very )?start|"
    r"at the (?:very )?beginning|in the (?:very )?beginning)\s*\??$"
    # "remind me where we started" is the same ask about the opening line, and without it the
    # wrapper came off to a line nothing claimed and the composer answered "Thanks for telling me"
    # to a question.
    r"|\bwhere (?:we|it|this|the (?:chat|conversation)) (?:all )?(?:started|began)\s*\??$"
    # "which question did i start with" is the same ask about the opening line. The words have to
    # name a question or a thing and a first, so an ordinary "which route did i take" is not one.
    r"|\bwhich (?:question|thing) (?:did i|i) (?:ask|asked|say|said|start with|started with|"
    r"begin with|began with)\s*(?:you\s*)?(?:first|with)?\s*\??$")

FIRST_ASK = re.compile(
    FIRST_ASK_BARE.pattern + r"|"
    r"\bwhat did i (?:ask|say|tell)(?: you)?(?: \w+){0,2} (?:first|at the (?:very )?start|"
    r"at the (?:very )?beginning|in the (?:very )?beginning)\s*\??$"
    r"|\bwhat (?:was|were) (?:the |my )?(?:very )?first (?:thing|question|message|line|one)"
    r"(?: (?:i|you) (?:asked|said)(?: you)?)?\s*\??$"
    r"|\b(?:how|where) did (?:we|(?:this|our|the) (?:chat|conversation)) (?:start|begin|get started)\b"
    r"(?=$|[?.!,]| (?:it|this|here|that|off|talking|chatting|the chat|this chat|the "
    r"conversation|this conversation)\b)"
    r"|\bwhat did i say (?:at |in )?the (?:start|beginning)\s*\??$"
    r"|\bdo you remember what i (?:asked|said)(?: you)? first\s*\??$"
    r"|\bwhat did i (?:ask|say) first\s*\??$"
    # The asking is often in front of the question - "can you remember what i told you at the
    # start", "do you remember what i said at the beginning" - and the capability card was
    # answering those with "nothing from before this chat, sorry" for a chat the store knows.
    r"|\b(?:can|could|do|did|would) you remember what i (?:asked|said|told)(?: you)?(?: \w+){0,2}"
    r" (?:first|at the start|at the beginning)\s*\??$"
    # The wrapper comes off in `_bare` before this is read, so the same ask arrives as a bare
    # clause: "do you remember what i asked you first" is read as "what i asked you first", and
    # that matched nothing - the line fell through to the quote-their-last-line reader and came
    # back as the turn before it ("Your own words were: ...") for a chat whose first line the
    # store has. The words after the verb are "you", the thing asked about and the time, in any
    # order: "what i said to you at the very start" is the same ask.
    r"|\bwhat i (?:asked|said|told|mentioned)(?: you)?(?: \w+){0,3}?\s+"
    r"(?:very |the )?(?:first|start|beginning|begin)\b\s*\??$"
    r"|\bmy first (?:question|message|line|words)\b\s*\??$"
    r"|\bwhat did i (?:ask|say|tell)(?: you)? when we (?:started|began|first)\s*\??$"
    r"|\bremind me how (?:this|we|the chat|the conversation) (?:started|began)\b"
    # The whole line has to be the meta-question. Filed as an ending only, "the argument
    # started when he came home late and i dont know how it started" was read as a question
    # about the chat and told "We're just beginning - you go first."
    r"|^(?:and |so |but )?(?:how|where) (?:did )?(?:this|the chat|our conversation|it)"
    r" (?:start|started|begin|began)\s*[?.!]*$")

REPEAT_TAIL = re.compile(r"\b" + REPEAT_ADVERB + r"\b", re.I)

REPEAT_ASK = re.compile(
    r"\b(?:say|said|repeat|tell me|read|hear|catch)(?: it| that| this)? again\b"
    r"|\bwhat did you (?:just )?say\b"
    r"|\bwhat did you tell me(?: (?:just )?now| earlier| before| so far)?\b"
    r"|\bwhat you (?:just )?(?:said|told me)\b"
    r"|\bcan you (?:repeat|say) (?:that|it)(?: again)?\b"
    r"|\bsay (?:that|it) once more\b"
    # The bare verb, which is the commonest way of all to ask and the one shape missing: "repeat
    # that", "repeat it please", "please repeat". Every other form here carries "again" or "say",
    # so a person who typed the verb on its own got the small-talk fallback ("Got it. Is there
    # anything you'd like a hand with?") with the answer they wanted still on the screen behind it.
    # The two guards already keep the rest out: REPEAT_START wants the line to open on the ask, so
    # "on repeat" and "i repeat myself" are not asks, and REPEAT_WORDS wants every content word to
    # be part of the ask, so "repeat the bit about resting it" still goes to the answer.
    r"|\b(?:please\s+)?repeat\b(?!\s+(?:after|myself|yourself))"
    # The same ask with the verb "say" and no "again": "say that slower", "say it simpler". The
    # person is not asking for a different answer, they are asking for that one again at a speed
    # they can follow, and the echo ("Got it — say that slower.") said nothing.
    r"|\bsay (?:that|it) (?:again|once more|slower|slowly|simpler|clearer)\b"
    # The same ask with the verbs people reach for when the answer was long: "explain that
    # again", "go over that again", "run that by me again". Every one of them names the last
    # thing said and nothing of its own, and REPEAT_WORDS keeps the rest out, so "go over the
    # rules of chess" and "explain why the sky is blue" stay about the thing. Before this the
    # line fell to the composer, and "explain that again" was answered "Got it - explain that
    # again" with the answer still on the screen.
    r"|\bexplain (?:it|that|this)(?: (?:again|once more|slower|more slowly|simply|more simply))?\b"
    r"|\b(?:go|walk|talk)(?: me)? (?:over|through) (?:it|that|this)\b"
    r"|\brun (?:it|that|this) by me\b"
    r"|\brun (?:it|that|this) (?:again|once more)\b"
    # The same ask pointed at a part: "the last bit again", "the last part again". "the last
    # bit" is the last thing said, not a thing of its own, so a line whose only subject is that
    # is asking for the answer again.
    r"|\bthe (?:last|final) (?:bit|part)\b"
    # The ask said as a complaint about the answer: "you lost me", "sorry you lost me there".
    r"|\b(?:you(?:'ve| have)? lost me|i lost you)\b"
    r"|\bwhat was that\b"
    r"|\bcome again\b"
    r"|\bpardon\b"
    r"|\bi missed (?:that|it)\b"
    r"|\bone more time\b"
    # A repeat ask that names the figure it wants: "how long did you say", "when did you say",
    # "how much did you say it was". The person is not asking what the bot is; they want the
    # figure out of the answer they already have, and the words in front of "did you say" say
    # which figure.
    r"|\b(?:how long|how much|how many|how often|how soon|what time|when|where)\s+"
    r"did you (?:just )?say\b"
    # "repeat that" and "repeat that please" ask for the last reply as surely as "say that again"
    # does, and "again" is not always said. Anchored at the end of the line so "repeat that
    # step" and "he repeats that every day" are about the thing and not about the conversation.
    + r"|\brepeat (?:that|it|this)(?:\s+" + REPEAT_ADVERB + r"){0,2}\s*[.!?]*$")

LAST_LINE_ASK = re.compile(
    r"\bwhat did you just say\b|\bwhat was that\b|\bpardon\b|\bcome again\b"
    r"|\bi missed (?:that|it)\b|\bdid(?:n't|nt) catch\b", re.I)

REPEAT_WORDS = frozenset("""
say said repeat again tell told speak word pardon missed catch hear one time just last line
remind reminded you please sorry thanks thank cheer cheers ta come that this it me now thing
slower slowly simpler clearer bit
explain explained go going through walk talk run ran by part parts lose lost there
how long much many often soon when where time
earlier ago previously minute moment before already so far up to now until now
""".split())

WHOLE_ASK = re.compile(
    r"^(?:(?:and|so|but|ok|okay|oh|right|well|yes|yeah|ta|please|then)\s+)*"
    r"(?:"
    r"in full|in the full|in full please|the full (?:thing|version|answer)"
    r"|the whole (?:thing|answer|lot|of it)|the whole of it please"
    r"|all of (?:it|that|this)|all of it please|both of (?:them|those)"
    r"|the lot|the lot please"
    r"|from the (?:top|start|beginning)|from the very (?:top|start|beginning)"
    r"|start (?:again )?from the (?:top|start|beginning)"
    r"|(?:say|tell me|give me) (?:it all|it in full|all of it|all of that|the lot)"
    r")"
    r"(?:[\s,]+(?:please|then|now|thanks|ta))*[\s.,!?]*$", re.IGNORECASE)

REPEAT_START = re.compile(
    r"^(?:(?:and|so|but|ok|okay|oh|then|well|right|hmm|um)\s+)*"
    r"(?:say|repeat|tell|read|hear|catch|can|could|would|will|what|sorry|pardon|please|thanks|"
    r"thank you|cheers|ta|come|again|"
    r"how|when|where|remind|reminded|one more|i missed|i didn't catch|i didnt catch|"
    r"explain|go|walk|talk|run|the|you|i lost|"
    r"didn't catch|didnt catch|do you|excuse me)\b")

REMINDER_MID = re.compile(
    r"\b(?:please |can you |could you |would you )?(?:remind me|tell me again|ask me again)"
    r"(?: again)?\b[\s,]*"
    # "do you know my age?", "do you remember what I do": the same reminder said as a question
    # about the bot's memory. The remembering word carries nothing of the fact, so it comes off
    # with the rest of the wrapper and the ask behind it is read like any other ("my age",
    # "what i do"). A question about the world in the same words ("do you know how to fix a
    # tap") loses only its opener, and no reader of the store answers what is left.
    r"|^\W*(?:do|did|can|could) (?:you|u) (?:still |actually |even |really )?"
    r"(?:know|remember|recall)\b[\s,]*")

REMINDER_HEAD = re.compile(
    r"^(?:(?:and|but|so|ok|okay|oh|also|right|well|sorry|hi|hey|just|quick|one more)\b[\s,]*)+")

REMINDER_TAIL = re.compile(r"(?:[\s,]*\b(?:again|please)\b)+$")

ABOUT_HEAD = re.compile(r"^(?:(?:and|but|so)\s+)?what about\s+")

ACTIVITY_ASK = re.compile(
    r"(?:\bwhat (?:was|am|were) i (?:making|cooking|baking|planning|doing|up to)|"
    r"\bwhat i (?:(?:just )?said )?(?:i )?was (?:doing|up to|making|cooking|baking|planning)|"
    r"\bwhat was i (?:going to|meant to) do)\b"
    r"(?!\s*(?:wrong|badly|bad|differently|silly|stupid|right|here|now))"
    # "what am i doing this week" asks what is coming up, not what they said they were doing.
    r"(?![^.?!]*\b(?:this|next|coming)\s+(?:week|weekend|month|year|monday|tuesday|wednesday|"
    r"thursday|friday|saturday|sunday)\b|\btonight\b|\btomorrow\b|\bcoming up\b)")

PLAN_WORDS = re.compile(r"\bwhat (?:am i|are we) planning\b|\bwhat (?:have|has) (?:i|we) got\b|"
                        r"\bwhat do (?:i|we) have\b|\bcoming up\b|\bon for (?:me|us)\b")

UP_TO_ASK = re.compile(r"\bwhat (?:am i|are we) (?:planning|up to)\b|"
                       r"\bwhat (?:was|were) (?:i|we) (?:planning|up to)\b"
                       r"(?!\s*(?:wrong|badly|bad|differently|silly|stupid|right))")

NAMED_ACTIVITY = re.compile(r"\bwhat (?:was|am|were) i (?:making|cooking|baking)\b|"
                           r"\bwhat (?:was|am) i planning to\b")

ACTIVITY_WORDS = re.compile(
    r"\b(?:making|cooking|baking|roasting|preparing|building|painting|writing|sorting|"
    r"fixing|mending|planning|organising|organizing|packing|knitting|sewing|decorating|"
    r"gardening|going to|off to|about to|having|doing)\b", re.I)

ACTIVITY_LOOSE = re.compile(
    r"\b(?:want|wanted|need|needed|thinking of|plan|plans|planned|trying|meant|going) to "
    r"(?:make|cook|bake|roast|prepare|build|paint|write|sort|fix|mend|plan|organise|organize|"
    r"pack|do|have)\b", re.I)

ASK_LINE = re.compile(r"^\s*(?:so |and |but )?(?:what|which|who|when|where|why|how|can|could|"
                      r"would|should|do|did|does|is|are|was|were|will|shall|have|has|remind|"
                      r"tell|any)\b", re.I)

DETAIL_START = re.compile(
    r"^(?:he|hes|she|shes|they|theyre|it|its|it's|his|her|hers|their|theirs|them|the|this|that|"
    r"these|those|my|our|also|plus|and|but|so|yes|yeah|no|nope|ok|okay|sorry|thanks|right|true)\b",
    re.I)

STOPWORDS = frozenset("""the and but for with that this have has had was were are been being its
it's they them their there here about into from just only also very really quite then than when
what which who how why where some any all one two three four five six seven eight nine ten""".split())

def _bare(folded):
    """The ask inside the reminder wrapper: "remind me what I'm allergic to" -> "what i am
    allergic to", "and my name again?" -> "my name"."""
    asked = REMINDER_MID.search(folded or "")
    bare = REMINDER_MID.sub(" ", folded or "")
    bare = ABOUT_HEAD.sub("", bare)
    bare = REMINDER_HEAD.sub("", bare)
    bare = REMINDER_TAIL.sub("", bare)
    bare = CHAT_TAIL.sub("", bare).strip(" ,.;:!?")
    bare = " ".join(bare.split())
    flipped = WHEN_INVERTED.match(bare)
    if flipped:
        # "when my interview is" -> "when is my interview": one order for every when-ask reader
        bare = f"when {flipped.group(3)} {flipped.group(1)} {flipped.group(2)}"
    elif asked:
        subject = WHEN_INVERTED_SUBJECT.match(bare)
        if subject:
            # "when i am going to rome" -> "when am i going to rome"
            bare = f"when {subject.group(2).split()[0]} {subject.group(1)} " \
                   f"{' '.join(subject.group(2).split()[1:])}".strip()
    return bare

def _the_limits_on(entry):
    """The limits a read entry holds, as a dict, or {} for an entry that limits nothing."""
    if not isinstance(entry, dict):
        return {}
    return {key: entry[key] for key in LIMITS if entry.get(key) not in (None, "", [], {})}

def _the_limit_they_share(text, memory):
    """"im too" after "my son is allergic to nuts": the limit is the person talking's as well.

    A limit said of one person is shared by the next line and the line says nothing of its own,
    so the store is what gives it a meaning: it reads the limit out of the turn before (which it
    filed) and files the same limit on the other person. Nothing is filed when the turn before
    stated no limit, which is what keeps "i love pizza" then "me too" a taste, and "my son is 6"
    then "im too" an age nobody shares.

    Both directions are the same reader: "im allergic to nuts" then "my son is too" is the son's
    allergy, and it was a line the store only echoed back before. Returns the reply, or None.
    """
    who = extract.the_limit_they_share(text)
    if not who or not isinstance(memory, dict):
        return None
    turns = memory.get("turns") or []
    before = str((turns[-1] or {}).get("user") or "") if turns else ""
    if not before:
        return None
    said = extract.extract(before)
    if not isinstance(said, dict):
        return None
    about_them = [(str(entry.get("who") or ""), _the_limits_on(entry))
                  for entry in (said.get("others") or []) if isinstance(entry, dict)]
    about_them = [(relation, limits) for relation, limits in about_them if relation and limits]
    about_me = _the_limits_on(said)
    if who == "i":
        if not about_them:
            return None
        relation, limits = about_them[-1]
        for key, value in limits.items():
            remember(memory, key, value, text)
        return _said_of_a_shared_limit(limits, "", memory)
    if who == extract.LAST_PERSON:
        # "she is too", "he as well": the last person the chat named, out of the line before the
        # share (which is where a pronoun has an antecedent) and then the store's own person.
        named = [str(word) for word in (said.get("people") or []) if isinstance(word, str)]
        who = named[-1] if named else ""
        if not who:
            person = memory.get("person")
            who = str((person or {}).get("who") or "") if isinstance(person, dict) else ""
        if not who:
            return None
    if not about_me:
        return None
    remember_other(memory, dict(about_me, who=who), text)
    return _said_of_a_shared_limit(about_me, who, memory)

def _is_or_are(words):
    """"dairy is off your plate", but "nuts are off your plate" and "nuts and dairy are too"."""
    if len([word for word in words if str(word).strip()]) > 1:
        return "are"  # two things said together are plural however each of them is spelt
    last = str(words[-1]).split()[-1] if words else ""
    return "are" if last.endswith("s") and not last.endswith("ss") else "is"

def _the_things(words):
    """The things named, as a person says them: "nuts", "nuts and dairy", "nuts, dairy and soya"."""
    said = [str(word).strip() for word in words if str(word).strip()]
    if not said:
        return ""
    if len(said) == 1:
        return said[0]
    return ", ".join(said[:-1]) + " and " + said[-1]

def _said_of_a_shared_limit(limits, who, memory):
    """The reply to a line that shares the limit: what it is, and whose it is now."""
    things = list(limits.get("allergies") or [])
    if things:
        named = _the_things(things)
        if who:
            return pick(("Then " + named + " " + _is_or_are(things) + " off " + _their_own(who)
                         + "'s plate too — I'll keep both of you in mind.",
                         "Right, " + named + " out for " + _their_own(who) + " as well, then.",
                         "So " + named + " " + _is_or_are(things) + " off the table for "
                         + _their_own(who) + " too. Both of you, then."), memory, ())
        return pick(("Then " + named + " " + _is_or_are(things) + " off your plate too — I'll "
                     "answer for both of you.",
                     "Right, " + named + " out for you as well, then.",
                     "So " + named + " " + _is_or_are(things) + " off the table for you too."),
                    memory, ())
    diet = limits.get("diet")
    if diet:
        if who:
            return ("Then " + str(diet) + " for " + _their_own(who) + " as well — I'll plan around "
                    "the two of you.")
        return pick(("Then " + str(diet) + " for you as well — I'll plan around the two of you.",
                     "Same for you, then: " + str(diet) + ". I'll keep that straight."),
                    memory, ())
    condition = limits.get("condition")
    if condition:
        named = _the_things(condition if isinstance(condition, (list, tuple)) else [condition])
        if who:
            # Said the way it is said: the condition is what the person is, so it goes after them
            # with "is", not held off with "has the same thing". "Then your mum is diabetic too"
            # reads as a friend would say it; the other wordings are for the second time.
            return pick(("Then " + _their_own(who) + " " + _is_or_are([named]) + " " + named
                         + " too — I'll keep it in mind for both of you.",
                         "Right, " + named + " for " + _their_own(who) + " as well, then. Both of "
                         "you.",
                         "So " + _their_own(who) + " has that too. I'll keep the two of you in "
                         "mind."), memory, ())
        return pick(("Then you have the same thing, " + named + " — I'll keep that in mind.",
                     "Same condition for you too, then: " + named + "."), memory, ())
    return None

def _their_own(who):
    """"your son", "your daughter": the reply names the person the limit is now on.

    Not `_theirs`, which is the composer's somewhere else: a reply that reads "off Son plate" is
    the person addressed as the relation they gave rather than as somebody in their family.
    """
    word = str(who or "").strip().lower()
    return "your " + word if word and word not in ("i", "me") else "your"

MEATLESS_DIET = re.compile(r"vegetarian|vegan|veggie|plant|pescatarian|flexitarian", re.I)

def _the_back_this_turn(text, memory):
    """The line that says what the bot has just stopped believing about somebody else.

    Only on the turn they lifted it: the note names the food, and said a turn later it answers a
    question nobody asked.
    """
    done = memory.get("reversal") if isinstance(memory, dict) else None
    if not isinstance(done, dict) or done.get("said") != " ".join(str(text or "").lower().split()):
        return None
    who = str(done.get("who") or "")
    food = str(done.get("food") or "").strip()
    if not food:
        return None
    theirs = "your " + who if who in extract.RELATIONS else "them"
    if done.get("kind") == "taste":
        # A taste is not a diet: "nothing off her plate" would read as food she cannot have.
        return pick(["Right \u2014 " + food + " back on the yes list for " + theirs + ", then.",
                     "Got it \u2014 " + theirs + " likes " + food + ", then.",
                     "Noted \u2014 " + food + " for " + theirs + " from now on, then."],
                    memory if isinstance(memory, dict) else {})
    return pick(["Right \u2014 " + food + " back on the plate for " + theirs + ", then.",
                 "Got it \u2014 " + food + " is back on the menu for " + theirs + ", then.",
                 "Fair enough \u2014 nothing off " + theirs + "'s plate, then."],
                memory if isinstance(memory, dict) else {})

def _still_holding(memory, animals):
    """True when a pet of that kind is still on the store, so the whole kind is not gone."""
    held = {str((pet or {}).get("animal") or "").strip().lower()
            for pet in ((memory.get("user") or {}).get("pets") or []) if isinstance(pet, dict)}
    return any(str(animal).lower() in held for animal in animals)

def _kind(item):
    """A take-back is a species word or a record; either way the animal it is about."""
    return str(item.get("animal") or "") if isinstance(item, dict) else str(item)

SIZE_UNITS = {
    "kg": "kg", "kilo": "kg", "kilos": "kg", "kilogram": "kg", "kilograms": "kg",
    "g": "g", "gram": "g", "grams": "g", "lb": "lb", "lbs": "lb", "pound": "lb",
    "pounds": "lb", "oz": "oz", "ounce": "oz", "ounces": "oz", "pint": "pint",
    "pints": "pint", "litre": "litre", "litres": "litre", "liter": "litre",
    "liters": "litre", "ml": "ml", "cm": "cm", "mm": "mm", "inch": "inch", "inches": "inch",
}

A_SIZE = re.compile(r"\b(\d+(?:\.\d+)?)\s*(" + "|".join(sorted(SIZE_UNITS, key=len, reverse=True))
                    + r")\b", re.I)

SIZE_LINE_FILLER = frozenset((
    "its", "it", "is", "about", "around", "roughly", "mine", "ours", "the", "a", "an", "one",
    "weighs", "weigh", "weight", "of", "say", "like", "just", "not", "much", "more", "less",
    "over", "under", "approx", "approximately", "i", "have", "got", "ive", "thats", "that",
    "s", "and", "so", "yeah", "yes", "ok", "okay", "sorry", "actually", "probably", "think",
    "guess", "pretty", "already", "exactly", "nearly", "almost", "only", "total",
    "altogether", "definitely", "ish", "now", "still", "bought", "buy", "brought", "used",
    "was", "were", "we", "they", "it",
))

A_TIME = re.compile(r"\b\d+(?:\.\d+)?\s*(?:hour|hours|hr|hrs|minute|minutes|min|mins)\b",
                    re.I)

def _a_size(text):
    """The size a line names as one string ("2kg"), or None when it names none."""
    found = A_SIZE.search(str(text or ""))
    if not found:
        return None
    return found.group(1) + SIZE_UNITS[found.group(2).lower()]

def _only_names_the_size(text):
    """True when the line is the size and nothing else, so what it says is the answer itself."""
    flat = " ".join(str(text or "").lower().split())
    found = A_SIZE.search(flat)
    if not found or len(flat.split()) > 8:
        return False
    rest = (flat[:found.start()] + " " + flat[found.end():]).split()
    return all(word.strip(",.!?") in SIZE_LINE_FILLER for word in rest)

def _the_clause_that_works_it_out(answer, size):
    """The clause of `answer` that names this size with a time in it, or None.

    "20 minutes per 500g plus 20 minutes at 190C, so a 2kg bird takes roughly 1 hour 40 minutes"
    holds the figure for the size the person has just named, in the answer's own words. A clause
    that has the size but no time is something else about it ("put a 2kg bird in a large tin")
    and is not the figure the line is asking for.
    """
    for clause in re.split(r"[,;.]", str(answer or "")):
        flat = " ".join(clause.split())
        if not flat or not A_TIME.search(flat) or _a_size(flat) != size:
            continue
        flat = re.sub(r"^(?:(?:and|so|then|which means|that means)\b[\s,]*)+", "", flat, flags=re.I)
        if flat:
            return flat[0].upper() + flat[1:] + "."
    return None

FEEDING_ASK = re.compile(
    r"\b(?:enough(?:\s+(?:for|to\s+feed))?|feed|feeds|serve|serves|do|does)\s+"
    r"(?:the\s+|it\s+|that\s+|this\s+|all\s+|all\s+of\s+)?"
    r"(\d{1,3}|a couple|a few|a dozen|half a dozen|two|three|four|five|six|seven|eight|nine"
    r"|ten|eleven|twelve)\b", re.I)

HEAD_COUNTS = {"a couple": 2, "a few": 3, "a dozen": 12, "half a dozen": 6}

HEAD_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
              "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}

SIZE_GRAMS = {"kg": 1000.0, "g": 1.0, "lb": 453.59, "oz": 28.35}

BIRDS = frozenset(("chicken", "turkey", "duck", "goose"))

ANSWER_PORTION = re.compile(
    r"\b(\d{2,4})\s*g\b[^.,;]{0,24}?\b(?:each|a person|per person|per head|a head)\b", re.I)

SO_A_SIZE = re.compile(r"\bso\s+(?:an?\s+)?(\d+(?:\.\d+)?)\s*(" +
                       "|".join(sorted(SIZE_UNITS, key=len, reverse=True)) + r")\b", re.I)

def _the_people_that_size_feeds(text, memory):
    """What the amount in hand feeds, against the portion the knowledge keeps for that food, or None.

    "how long do i roast a chicken" / "its 2kg" / "is that enough for 6" is the question a person
    asks while holding the joint: the portion the cooking know-how already keeps ("500g a person
    on the bone", units.PER_PERSON) turns their size into a number of people, and nothing here is
    worked out that the knowledge does not already say.

    Only a line asking whether an amount will do for a head count, only for a food the chat has
    named, and only a size that is on the screen - said by them or worked out for them a turn ago.
    A food counted in pieces ("3 sandwiches each") has no weight to read a size against, so the
    reader stands back and lets the answer speak.
    """
    if not isinstance(memory, dict):
        return None
    said = " ".join(str(text or "").lower().split())
    found = FEEDING_ASK.search(said)
    if not found:
        return None
    count = HEAD_COUNTS.get(found.group(1).lower()) or HEAD_WORDS.get(found.group(1).lower())
    if not count:
        try:
            count = int(found.group(1))
        except (TypeError, ValueError):
            return None
    if not 2 <= count <= 40:
        return None
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    held = said + " " + " ".join(str(turn.get("user") or "").lower() for turn in turns[-3:])
    answers = " ".join(str(turn.get("bot") or "").lower() for turn in turns[-2:])
    portion = _the_portion_for_the_food(held, answers)
    if not portion:
        return None
    size = _a_size(text) or _the_size_on_the_screen(turns)
    if not size:
        return None
    return _the_portion_reply(size, portion, count)

MADE_ONLY = re.compile(r"\b(?:only|just)\s+(?:made|cooked|done|got|had|bought|used|managed|"
                       r"did|knocked)", re.I)

FOR_A_COUNT = re.compile(
    r"\bfor\s+(?:the\s+)?(\d{1,2}|two|three|four|five|six|seven|eight|nine|ten|eleven"
    r"|twelve)\b", re.I)

def _the_amount_they_made(text, memory):
    """A line saying they only made this much, read against the total an answer worked out.

    "how much rice for 4 people" answers "About 75 g of dry rice each, so 300 g for four", and
    "i only made 200g" then got "5 minutes": the amount was read as a cooking question about a
    weight. The answer has the count and the figure it worked out, so the amount they made is read
    against the portion the answer gave, and the shortfall is said plainly.

    Only a line carrying the "only"/"just" that says it is short, only an amount with a weight in
    it, and only when the answer named the head count it worked the total out for. Everything else
    is left to whoever else reads it.
    """
    if not isinstance(memory, dict):
        return None
    said = " ".join(str(text or "").lower().split())
    if not MADE_ONLY.search(said):
        return None
    size = _a_size(text)
    if not size:
        return None
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    answer = " ".join(str(turn.get("bot") or "").lower() for turn in turns[-2:])
    counted = FOR_A_COUNT.search(str(turns[-1].get("bot") or "").lower()) if turns else None
    if not counted:
        return None
    count = HEAD_COUNTS.get(counted.group(1)) or HEAD_WORDS.get(counted.group(1))
    if not count:
        try:
            count = int(counted.group(1))
        except (TypeError, ValueError):
            return None
    if not 2 <= count <= 40:
        return None
    held = said + " " + " ".join(str(turn.get("user") or "").lower() for turn in turns[-3:])
    portion = _the_portion_for_the_food(held, answer)
    if not portion:
        # No portion for any food in the chat: the weight could be anything, so the line is left
        # to whoever else reads it rather than read against a figure that is not about a plate.
        return None
    return _the_portion_reply(size, portion, count)

def _the_portion_reply(size, portion, count):
    """One size read against one portion, or None when it does not feed anyone."""
    per, unit, noun, bone = portion
    if unit != "g":
        return None  # pieces and millilitres are not a weight the size can be read against
    grams = _size_in_grams(size)
    if not grams:
        return None
    feeds = int(grams // per)
    if feeds < 1:
        return None
    line = "{size} of {noun}{bone}is about {per}g a person, so it feeds {feeds}".format(
        size=size, noun=(noun + " ") if noun else "", bone="on the bone " if bone else "",
        per=("%g" % per), feeds=_a_number_word(feeds))
    if feeds >= count:
        if feeds > count:
            return line + " \u2014 enough for {count}, with a second helping in it.".format(
                count=_a_number_word(count))
        return line + "."  # the number of people it feeds is the answer, so it is not said twice
    wanted = count * per
    wants = ("%gkg" % (wanted / 1000.0)) if wanted >= 1000 else ("%gg" % wanted)
    return line + ", and {count} wants about {wants}.".format(
        count=_a_number_word(count), wants=wants)

def _the_portion_for_the_food(held, answers):
    """The (grams, unit, noun) portion the knowledge keeps for the food this chat is about, or None.

    The food is looked for in what the person said and in the answer that gave them the figure,
    and the most specific name wins: "chicken breast" is the meat off the bone at 200g, where
    "chicken" on its own is a bird at units.BIRD_GRAMS, so a line about a breast is never read as
    a whole bird.
    """
    best = None
    for names, amount, unit, noun in units.PER_PERSON + units.PER_PERSON_WHEN_COUNTED:
        for name in names:
            if not re.search(r"\b" + re.escape(name) + r"\b", held):
                continue
            score = len(name) + (2 if re.search(r"\b" + re.escape(name) + r"\b", answers) else 0)
            if best is not None and score <= best[0]:
                continue
            if name in BIRDS:
                best = (score, (float(units.BIRD_GRAMS), "g", name, True))
            else:
                best = (score, (float(amount), unit, noun, False))
    if not best:
        return None
    per, unit, noun, bone = best[1]
    if unit != "g":
        return best[1]
    # The answer's own portion is the one on the screen, so it is read first: a person holding
    # the 200g-of-chicken-each answer is not holding a bird measured on the bone.
    stated = ANSWER_PORTION.search(answers)
    if stated:
        return float(stated.group(1)), "g", noun, "on the bone" in answers
    return per, unit, noun, bone

def _the_size_on_the_screen(turns):
    """The size the chat has in hand: the last one they named, or the one the answer worked out.

    "is that enough for 6" a turn after "how long do i roast a chicken" points at the size the
    answer did its arithmetic for ("so a 2kg bird takes roughly 1 hour 40 minutes"), and that is
    the amount on the screen. A size named further back is not read: the subject moves on, and a
    figure from five turns ago is as likely to be about something else.
    """
    for turn in list(reversed(turns))[:3]:
        size = _a_size(turn.get("user"))
        if size:
            return size
    for turn in list(reversed(turns))[:2]:
        worked = SO_A_SIZE.search(str(turn.get("bot") or ""))
        if worked:
            return worked.group(1) + SIZE_UNITS[worked.group(2).lower()]
    return None

def _size_in_grams(size):
    """The weight a size names, in grams, or None when it is not a weight."""
    found = A_SIZE.match(str(size or ""))
    if not found:
        return None
    grams = SIZE_GRAMS.get(found.group(2).lower())
    if not grams:
        return None
    try:
        return float(found.group(1)) * grams
    except (TypeError, ValueError):
        return None

def _the_figure_for_the_size_they_named(text, memory):
    """The figure the answer on the screen worked out for the size this line names, or None.

    "how long do i roast a chicken" answers with the rate and with the arithmetic for one size
    ("so a 2kg bird takes roughly 1 hour 40 minutes"), and the person then says "its 2kg". The
    figure for their size is already in the answer, and the store said "Thanks for telling me -
    I'm here if you want to dig into any of that": an acknowledgement of the one part of the
    chat that has a number in it.

    Only a line that is the size and nothing else counts, only when the size was not said before
    in this chat (an ask that carries the size reaches the entry by itself), and only for the
    figure the answer already worked out, so nothing is worked out here and nothing is invented.
    """
    if not isinstance(memory, dict):
        return None
    size = _a_size(text)
    if not size or not _only_names_the_size(text):
        return None
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    if not turns:
        return None
    for turn in turns:
        if _a_size(turn.get("user")) == size:
            return None
    # The size the answer worked its own arithmetic out for is already in front of them: "so a
    # 2kg bird takes roughly 1 hour 40 minutes" came back as "A 2kg bird takes roughly 1 hour 40
    # minutes." when they typed "its about 2kg". Handing the clause back repeats the one figure
    # they have just read. A size the answer did not work out (1.5kg, 2.5kg) is a different
    # matter and never reaches this function: the cooking entry answers those itself.
    worked = SO_A_SIZE.search(str(turns[-1].get("bot") or ""))
    if worked and worked.group(1) + SIZE_UNITS[worked.group(2).lower()] == size:
        return None
    return _the_clause_that_works_it_out(turns[-1].get("bot"), size)

def _denial_this_turn(text, memory):
    """The short line that says what the bot has just stopped believing, on the turn they said it."""
    gone = memory.get("denial") if isinstance(memory, dict) else None
    if not isinstance(gone, dict) or gone.get("said") != " ".join(str(text or "").lower().split()):
        return None
    others = ("allergies", "condition", "diet")
    if gone.get("who"):
        # Somebody else's take-back is theirs, not the speaker's: "Nuts back on the table, then."
        # answers an allergy the person typing never said they had, when the line was about
        # their son.
        items = [str(item) for item in (gone.get("allergies") or []) if str(item)]
        if not items:
            return None
        who = str(gone.get("who"))
        theirs = "your " + who if who in extract.RELATIONS else "them"
        # The line lifts a restriction, so it says the food is fine now: "Right - no eggs for your
        # daughter, then." reads as a new restriction on the person who just lifted one.
        things = items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]
        return pick(["Right \u2014 " + things + " back on the table for " + theirs + ", then.",
                     "Good \u2014 no allergy to " + things + " for " + theirs + ", then.",
                     "Noted \u2014 " + things + " back on for " + theirs + "."],
                    memory if isinstance(memory, dict) else {})
    if gone.get("pets_died") and not any(gone.get(key) for key in others):
        return None  # a death is not a take-back to say back to them
    kept = extract.extract(text)
    if gone.get("pets_given") and not any(gone.get(key) for key in others + ("pets",)):
        return None  # one of a set, so "no cat, then" would say they have none left
    for key in ("allergies", "condition", "diet", "pets"):
        value = gone.get(key)
        if value:
            if key == "pets":
                given_line = ack.pet_given_away(text, memory)
                if given_line:
                    # The animal was given to a new home, so the line they get is the warm one and
                    # not the record being crossed out: "Right \u2014 no dog, then." is what a clerk
                    # says to somebody who has just told you they had to give their dog up.
                    return given_line
                # A pet is a record, so the line names the animal rather than the record.
                animals = sorted({str(pet.get("animal") or "pet")
                                  for pet in value if isinstance(pet, dict)})
                if not gone.get("pets_all") and animals and _still_holding(memory, animals):
                    continue  # one of several: "no cat, then" would say they have none left
                shown = "pets" if gone.get("pets_all") else " or ".join(animals) or "pets"
            else:
                shown = ", ".join(str(item) for item in
                                   (value if isinstance(value, list) else [value]))
            fresh = kept.get(key)
            if fresh and key in CORRECTED_SAY:
                now = ", ".join(str(item) for item in
                                (fresh if isinstance(fresh, list) else [fresh]))
                return CORRECTED_SAY[key].format(thing=now, Thing=now[:1].upper() + now[1:],
                                                old=shown)
            if key == "diet" and not MEATLESS_DIET.search(shown):
                # A diet that is itself a negation is put back positively: after "im not eating
                # meat" the take-back is "eating meat again", where "no more not eating meat"
                # is a sentence a person stumbles on.
                put_back = _a_diet_put_back(shown)
                if put_back:
                    return pick(["Right \u2014 " + put_back + " again, then.",
                                 "Got it \u2014 " + put_back + " again, then.",
                                 "Fair enough \u2014 " + put_back + " again, then."],
                                memory if isinstance(memory, dict) else {})
                # "meat is back on the table" is the right thing after "im not vegetarian any
                # more" and the wrong one after "im not doing keto any more", which says nothing
                # about meat.
                label = "dieting" if str(shown).strip().lower() == "on a diet" \
                    else _diet_words(shown)
                return pick(["Right \u2014 no more " + label + ", then.",
                             "Right, " + label + " is off, then.",
                             "Fair enough \u2014 no more " + label + ", then."],
                            memory if isinstance(memory, dict) else {})
            return DENIAL_SAY.get(key, "{Thing} \u2014 scratch that, then.").format(
                thing=shown, Thing=shown[:1].upper() + shown[1:])
    return None

def _retraction_this_turn(text, memory):
    """The short line that says the last thing they said is off the record, on the turn they said
    it."""
    gone = memory.get("retraction") if isinstance(memory, dict) else None
    if not isinstance(gone, dict) or gone.get("said") != " ".join(str(text or "").lower().split()):
        return None
    keys = gone.get("keys") or []
    shown = [item for item in (gone.get("shown") or []) if item]
    if "pets" in keys and shown:
        thing = " and ".join(shown[:2])
        return pick(["Right \u2014 " + thing + " is off the record, then.",
                     "Taken back \u2014 no " + thing + " on my list any more."], memory)
    if "plans" in keys and not [key for key in keys if key != "plans"]:
        return pick(["Right \u2014 that plan is off the record, then.",
                     "Taken back: I\u2019ve nothing about that trip from you now.",
                     "Scratch that, then \u2014 the plan is out."], memory)
    phrase = RETRACT_SAY.get(keys[0]) if keys else None
    if phrase:
        return pick(["Right \u2014 " + phrase + " is off the record, then.",
                     "Dropped. " + phrase[:1].upper() + phrase[1:] + " is gone.",
                     "Taken back \u2014 I\u2019ve nothing from you on record about it now."],
                    memory)
    return pick(["Right, that\u2019s off the record then.",
                 "Taken back \u2014 I\u2019ve nothing on record about it now."], memory)

THEIR_NAMES = re.compile(
    r"\b(?:they|them|their|the\s+(?:two|three|four))\b[^.?]{0,20}?"
    r"\b(?:call|calls|called|calling|name|names|named)\b"
    r"|\b(?:call|called|name|named|callin)\s+(?:them|the\s+(?:two|three|four))\b", re.I)

ASKS_IT_BACK = re.compile(r"\b(?:again|remind me|remind|did i|earlier|told you|told me)\b", re.I)

def _told_readers():
    """The store's own answer for each kind of fact, for `told` (bot/memory/told.py).

    "have i told you about my allergies" is the same fact as "what am i allergic to", so it is
    answered with the sentence the store already says for it: one set of sentences for one fact,
    and the two asks cannot drift apart.
    """
    return {"allergies": lambda memory: _fact_reply(memory, "allergic to"),
            "budget": lambda memory: _fact_reply(memory, "budget"),
            "diet": lambda memory: _diet_reply(memory),
            "age": lambda memory: _age_reply(memory),
            "name": lambda memory: _name_reply(memory, "my name"),
            "job": lambda memory: _job_reply(memory),
            # The plan read out whole: the told reader asks about the plan, not for a part of it.
            "plan": lambda memory: _plans_reply(memory, "what am i planning"),
            "places": lambda memory: _places_reply(memory, "where do i live"),
            "pets": _told_pet_reply,
            # A puppy is a dog and a kitten is a cat, and `told` needs the store's own reading of
            # that: the two answers must not disagree about which animal was given.
            "family": _animal_family,
            "kids": lambda memory: _kids_reply(memory, "how many kids do i have") or ""}

OWN_ANIMAL_LINE = re.compile(
    r"\b(?:my|our)\s+(?:[a-z'\u2019-]+\s+){0,2}(?:dogs?|pupp(?:y|ies)|cats?|kittens?|pets?|"
    r"rabbits?|bunn(?:y|ies)|hamsters?|fish|horses?|pon(?:y|ies)|parrots?|guinea\s+pigs?)\b"
    r"|\b(?:i|we)\s+(?:have|had|got|keep|kept|'ve|ve|also\s+have|also\s+got)\b")

NOT_THEIR_ANIMALS = re.compile(
    r"\b(?:my|our)\s+(?:sister|brother|mum|mother|dad|father|friend|neighbour|neighbor|aunt|"
    r"uncle|cousin|gran|grandma|grandad|grandpa|colleague|boss|son|daughter|wife|husband|"
    r"partner|niece|nephew|flatmate|roommate|landlord)\b[^.!?]*\b(?:has|have|had|got|keeps?|"
    r"wants?|wanted)\b"
    r"|\b(?:in|at|from)\s+the\s+(?:park|rescue|shelter|centre|center|vet)\b"
    r"|\bthe\s+(?:rescue|shelter|breeder|neighbour|neighbor)\b[^.!?]*\b(?:had|has|have)\b"
    r"|\b(?:i|we)\s+(?:met|saw|passed|watched)\b")

def _the_line_before_is_their_own_animal(memory, back=3):
    """True when the last line that named an animal named one of the person's own.

    A question can sit between the animal and the ask ("we have two dogs, rufus and nell" / "what
    do they eat" / "what are they called again"), so the lines that named nothing are walked past.
    The first line that did name an animal decides: theirs, or somebody else's.
    """
    for turn in reversed(list(memory.get("turns") or [])[-int(back):]):
        said = str(turn.get("user") or "").strip().lower()
        if not said:
            continue
        if NOT_THEIR_ANIMALS.search(said):
            return False
        if OWN_ANIMAL_LINE.search(said):
            return True
        if re.search(r"\b(?:dogs?|cats?|kittens?|pupp\w*|animals?|pets?|rabbits?|hamsters?|"
                     r"fish|horses?)\b", said):
            # An animal line all the same, and not one of theirs: the pronoun is not about their
            # animals either, so the walk stops here rather than reaching further back.
            return False
    return False

def _the_names_again(folded, low, memory):
    """The names of their animals, asked back with the pronoun instead of the animal.

    "we got three kittens, pip, squeak and nibble" then "what are they called again?" is a read of
    the store, and the store holds all three names: the reply is one sentence with them in it. Only
    a line that points back ("again", "remind me") and only when a pet of theirs is named, so a
    question about the world ("i saw two birds in the garden" then "what are they called") is left
    to whoever can answer it, and a store with no pet in it never denies one they never claimed.
    """
    if not isinstance(low, str) or not low.strip():
        return ""
    # "again" is filler the ask is bare of, so the pointer back is read on the line as typed.
    if not ASKS_IT_BACK.search(str(folded or low)) or not THEIR_NAMES.search(low):
        return ""
    pets = [pet for pet in (user(memory).get("pets") or []) if isinstance(pet, dict)]
    if not pets:
        # No animal of theirs is on record, so this pronoun points at something out in the world:
        # the store says nothing rather than deny a pet they never claimed.
        return ""
    if not _the_line_before_is_their_own_animal(memory):
        # The pronoun is pointing at animals that are not theirs: "my neighbour has two cats" then
        # "what are they called again", two dogs met in the park, a sister's dogs. A store that
        # holds their own animals would answer with those names, which is the one mistake a memory
        # answer must not make.
        return ""
    # The same sentence the store gives for "what are my cats called", composed from a line that
    # names nothing: reading the ask itself lets its numbers and its nouns into the answer ("i met
    # two dogs" narrowed the list to dogs, and two names then came out as "one called Rufus and a
    # dog called Nell").
    return _fact_reply(memory, "what are my pets called", "pet")

def _the_one_animal_with_a_name(memory):
    """What the one animal they named is called, or "" when the chat holds none or several.

    One animal and one name is not a guess: "we have a cat called max" then "hes 4 months" then
    "what is his name" asks about the only animal in the chat. Several animals leave the pronoun
    pointing at one of them, which the store cannot tell, so it says nothing.
    """
    pets = [pet for pet in (user(memory).get("pets") or [])
            if isinstance(pet, dict) and pet.get("name")]
    if len(pets) != 1:
        return ""
    animal = str(pets[0].get("animal") or "pet")
    return _fact_reply(memory, "what is my " + animal + " called")

def _told_pet_reply(memory, animal):
    """What the store says about a kind of pet, for "have i told you about the cat"."""
    pets = [pet for pet in (user(memory).get("pets") or []) if isinstance(pet, dict)
            and _animal_family(str(pet.get("animal") or "")) == animal]
    if not pets:
        return ""
    if any(pet.get("name") for pet in pets):
        return _fact_reply(memory, "what is my " + animal + " called")
    return _fact_reply(memory, "how many " + animal + "s do i have")

NO_RECORD = re.compile(
    r"^(?:you haven'?t told me|you (?:didn'?t|did not) tell me|i don'?t have|"
    r"there'?s nothing|i haven'?t got)\b", re.I)

ASK_AND_PERSON = frozenset("""what which who is are was were does do did can could would should
she he they them their her his him my our mum mom mother dad father son daughter sister brother
kid kids child children wife husband partner parents gran nan grandma granny aunt uncle cousin
baby stepmum stepdad mother father baby allergic allergy allergies allergie diet eat eats eating
eaten food foods drink drinks allergic had has have anything else one""".split())

def _says_more_than_the_ask(low):
    """True when the line carries a word the ask about that fact does not need.

    "what is my mum allergic to?" is the ask alone; "is my son allergic to nuts? he had a rash"
    brings a food and a symptom with it, and those are the entry's, not the store's.
    """
    for word in re.findall(r"[a-z']+", str(low or "").lower()):
        if len(word) < 3 or word in ASK_AND_PERSON or word in GENERIC_WORDS:
            continue
        if word.rstrip("s") in ASK_AND_PERSON:
            continue
        return True
    return False

GENERIC_WORDS = frozenset("""the and but for with that this these those there here about into
from just only also very really quite then than when what which who whom whose why how some any

not dont doesnt didnt im ive its it's youre youve like want need know tell told say said again
please thanks ok okay""".split())

HOW_FAR_ALONG = re.compile(
    r"\bhow far (?:along|gone)\b|\bhow many weeks (?:is|are|am|along|pregnant|gone|in)\b"
    r"|\bwhat week (?:is|are|am) (?:she|he|they|it|i|i in)\b|\bhow many weeks (?:pregnant|along)\b",
    re.I)

OWN_LENGTH_ASK = re.compile(r"\b(?:am i|i am|im|i'm|do i|did i)\b", re.I)

def _how_far_along(memory, low):
    """The weeks a pregnancy the chat was told has run, said as a length: "Eight weeks."."""
    said = str(low or "")
    if not HOW_FAR_ALONG.search(said):
        return None
    holding = [entry for entry in others(memory)
               if isinstance(entry, dict) and isinstance(entry.get("weeks"), int)]
    # A relation the ask names is the one it is about, own pregnancy or not: "how far along is my
    # wife" in a chat that has both on file is not about the person asking.
    named = [entry for entry in holding
             if re.search(r"\b" + re.escape(str(entry.get("who") or "")) + r"\b", said)]
    if len(named) == 1:
        holding = named
    elif OWN_LENGTH_ASK.search(said):
        # The person's own pregnancy is kept on them (`memory["user"]`), not in `others`, so the
        # length is read from there before anything is said about somebody else.
        own = user(memory) or {}
        if isinstance(own.get("weeks"), int):
            return _a_number_word(int(own["weeks"])).capitalize() + " weeks."
        if own.get("pregnant"):
            # The pregnancy is on file and the length never was, so the honest answer is the one
            # thing missing rather than a search hedge about a fact they told the bot themselves.
            return ("You didn't say how many weeks — tell me and I'll keep it, so the meal plans "
                    "fit where you are.")
    if not holding:
        return None
    if len(holding) > 1:
        # Two pregnancies on file: the relation the ask names decided above, then the pronoun, and
        # without either the one told last is the one the chat is on.
        who = _person_from_pronoun(said, memory)
        if who:
            holding = [entry for entry in holding
                       if str(entry.get("who") or "").lower() == who] or holding[-1:]
    weeks = int(holding[-1]["weeks"])
    return _a_number_word(weeks).capitalize() + " weeks."

def _a_length_i_have(memory, low):
    """True when a length ask is about a pregnancy this chat already holds the weeks for.

    An ask like that is about what the person said, not about the world: the answer is the number
    they gave, and no card knows it. Read as a question about the world it lost the turn to the
    dating card, which explained how a due date is worked out instead of saying "Eight weeks."
    """
    said = str(low or "")
    if not HOW_FAR_ALONG.search(said):
        return False
    holding = [entry for entry in others(memory or {})
               if isinstance(entry, dict) and isinstance(entry.get("weeks"), int)]
    named = [entry for entry in holding
             if re.search(r"\b" + re.escape(str(entry.get("who") or "")) + r"\b", said)]
    if len(named) == 1:
        return True
    if OWN_LENGTH_ASK.search(said):
        own = user(memory or {}) or {}
        return isinstance(own.get("weeks"), int) or bool(own.get("pregnant"))
    return bool(holding)

def _a_limit_kept_for_them(low, memory):
    """True when the person the line names has a diet or a condition on record."""
    who = _someone_else_named(low, memory)
    for known in others(memory):
        if known.get("who") != who:
            continue
        return bool(known.get("condition") or known.get("diet"))
    return False

PET_NAME_AGAIN = re.compile(
    r"\bwhat(?:'s|s| is| was)\s+(?:his|her|its|their)\s+name\b"
    r"|\bwhat\s+(?:is|was|are|were)\s+(?:he|she|it|they)\s+called\b"
    r"|\bwhat\s+(?:did|do)\s+(?:i|we)\s+(?:call|name)\s+(?:him|her|it|them)\b", re.I)

PET_NAME_SETTLED = re.compile(
    r"\bwhat\s+(?:shall|should|will|would)\s+(?:i|we)\s+(?:call|name)\s+(?:him|her|it|them)\b",
    re.I)

NAME_PICKED_AGAIN = re.compile(
    r"\b(?:what|which)\s+name\s+(?:did|do|have)\s+(?:i|we)\s+"
    r"(?:pick|picked|choose|chose|go for|settle on|settled on|end up with)\b"
    r"|\b(?:what|which)\s+(?:did|do|have)\s+(?:i|we)\s+"
    r"(?:pick|picked|choose|chose|go for|settle on|settled on|end up with)\b", re.I)

def _the_pick_asked_again(text, memory):
    """The name the store holds, when the ask is the choosing said with "pick" or "settle".

    "im getting a dog / what should i call it / pepper / so what did i pick" was answered
    "You haven't picked one yet", which is false twice over: the name was said, and the store has
    it. The choice reader answers this shape for a plan it watched being made, and a name is not
    a plan, so the turn is answered from the pet instead.

    A bare "what did i pick" is only this ask while the chat is still on the pet and the name is
    among the last lines: a chat with a cat called Mango that has since been talking about a
    holiday is asking about the holiday, and there the choice reader's answer stands.
    """
    low = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not low or not NAME_PICKED_AGAIN.search(low):
        return None
    if re.search(r"\b(?:" + "|".join(extract.RELATIONS) + r")\b", low):
        return None
    named = [pet for pet in (user(memory).get("pets") or [])
             if isinstance(pet, dict) and pet.get("name")]
    if not named:
        return None
    pet = named[-1]
    name = str(pet.get("name") or "")
    animal = str(pet.get("animal") or "pet")
    if "name" not in low:
        # Without the word "name" in it, a bare "what did i pick" is only about the pet while the
        # chat is still on the pet: the subject is the animal (or the name itself) and one of the
        # last three lines was the name on its own. A chat with a cat called Mango that has since
        # moved on to "we were thinking italy or spain" is asking about the trip, and the choice
        # reader's own answer stands there.
        subject = str(topic_subject(memory) or "").lower().split()
        if not subject or (animal.lower() not in subject and name.lower() not in subject):
            return None
        turns = memory.get("turns") if isinstance(memory, dict) else None
        recent = [str((one or {}).get("user") or "")
                  for one in (turns[-3:] if isinstance(turns, list) else [])]
        said = [(extract.bare_name(line) or "").lower() for line in recent]
        if not name or name.lower() not in said:
            return None
    return _vary((
        _called(name) + " \u2014 that is the one you picked for your " + animal + ".",
        "You went for " + _called(name) + ". I have it written down.",
        _called(name) + ". That is your " + animal + "'s name.",
    ), memory)

def _what_the_pet_is_called(text, memory):
    """The name the store holds for the animal the line points at: "Milo — you settled on that."

    Only when the line is that ask and no person in it: "what's his name" after "my brother came
    round" is about the brother, and the relations reader owns those.
    """
    low = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not low or not (PET_NAME_AGAIN.search(low) or PET_NAME_SETTLED.search(low)):
        return None
    if re.search(r"\b(?:" + "|".join(extract.RELATIONS) + r")\b", low):
        return None
    named = [pet for pet in (user(memory).get("pets") or [])
             if isinstance(pet, dict) and pet.get("name")]
    if not named:
        # The animal is in play and has no name yet: the honest line is about the name, the way
        # the store already answers "what's my dog called". A line with no animal anywhere near
        # it ("what's his name" after a brother came round) is left to the relations reader.
        if PET_NAME_SETTLED.search(low):
            return None  # no name yet, so the naming question still wants names
        animal = _the_animal_of_the_pick(memory)
        if not animal or animal == "pet":
            return None
        return "You haven't told me a name for your " + animal + " yet."
    pet = named[-1]
    name = _called(str(pet.get("name")))
    animal = str(pet.get("animal") or "pet")
    return _vary((
        name + " \u2014 that is what you settled on for your " + animal + ".",
        "Your " + animal + " is called " + name + ".",
        name + ". I have that one written down.",
    ), memory)

def _the_name_they_picked(text, memory):
    """The name the person settled on, said back: "Pepper it is. I'll remember that for your cat."

    A name is the one thing a naming answer gives that no entry can, so the turn that gives it is
    answered rather than echoed ("Got it - her name is pepper") or given the stock line
    ("Thanks for telling me"). The name is already in the store by the time any module answers,
    because `observe` runs first, so the reply is built from what was kept and not from the line.
    """
    said = extract.pet_name_only(text)
    if not said and _offered_here(memory):
        # Only the list this module put in front of them is this module's turn: a bare word after
        # the bot has *asked* for the name ("we got a puppy" / "A puppy - good to know. What's its
        # name?" / "biscuit") is answered where that question was written, and the warmer line
        # there ("A puppy called Biscuit - lovely. How's Biscuit settling in?") stands.
        said = _name_they_answered(text, memory)
    if not said:
        return None
    pet = None
    for one in reversed(user(memory).get("pets") or []):
        if isinstance(one, dict) and str(one.get("name") or "").lower() == said.lower():
            pet = one
            break
    if pet is None:
        return None
    name = _called(str(pet.get("name") or said))
    animal = str(pet.get("animal") or "pet")
    return _vary((
        name + " it is. I'll remember that for your " + animal + ".",
        name + " \u2014 good choice, and easy to shout across a park.",
        "Right, " + name + ". That is the one from here on.",
    ), memory)

def _offered_here(memory):
    """The names the bot itself put in front of them on the turn before, and what they are for.

    "what should i name it" is answered with three names, and the next line is one of them or a
    name of their own. That turn is a choice, not a fact to look up: parsed from the reply rather
    than from a list of names here, so whatever the answer offered is what can be picked.
    """
    offered = extract.names_offered(memory)
    if not offered:
        return None
    return {"animal": _animal_family(offered["animal"]), "names": offered["names"]}

def _name_they_answered(text, memory):
    """The name chosen in answer to the bot's own question or list:

        we got a puppy / What's its name? / biscuit
        what should i name it / For a cat: Miso, Willow or Pepper. / milo

    The word alone says nothing, so it is read as a name only when the reply right before it asked
    for one or offered some; anything longer than a word or two ("i dont know", "no idea") stays
    unanswered. A list that was answered by a name of their own ("milo", not one of the three) is
    still the choice: the question was "what should i name it", and the answer is the name.
    """
    return extract.a_name_picked(text, memory)

def _the_animal_of_the_pick(memory):
    """Which animal a name just picked is for: the one the list was about, or the one in play."""
    offered = _offered_here(memory)
    if offered and offered.get("animal"):
        return offered["animal"]
    turns = memory.get("turns") or []
    for turn in reversed(turns[-3:]):
        line = str((turn or {}).get("user") or "").lower()
        for word in re.findall(r"[a-z']+", line):
            if word in extract.ANIMALS:
                return _animal_family(word)
    pets = user(memory).get("pets") or []
    for pet in pets:
        if isinstance(pet, dict) and pet.get("animal"):
            return _animal_family(pet.get("animal"))
    return None

PLAN_LOW_START = frozenset("""in on the a an my our their his her its we i it that this there
you your you're youre you've you'll youd you'd i'm im we're save book get go see buy run start
finish take visit move learn do make find call pay email sort fix get see meet try keep""".split())

def _correction_this_turn(text, memory):
    """The short note that says which value the bot goes with, on the turn of the correction."""
    fixed = memory.get("correction") if isinstance(memory, dict) else None
    if not isinstance(fixed, dict):
        return None
    if fixed.get("said") != " ".join(str(text or "").lower().split()):
        return None
    return _correction_said(fixed, memory) or None

def _the_second_pet_said(fixed, memory):
    """A line that adds a second animal of a kind is answered as a pet of theirs, not echoed.

    "my cat is called milo" then "no we also have a cat called max" filed both cats and left the
    turn to the greeting, which said the person's line back with "Got it" in front of it - a
    receipt in their own words. The store has the two names, so the reply is the one thing there
    is to ask about two animals, from the same pool that answers one.
    """
    animal = str((fixed or {}).get("animal") or "").strip().lower()
    pets = [pet for pet in (user(memory or {}).get("pets") or ()) if isinstance(pet, dict)]
    named = [str(pet.get("name") or "") for pet in pets
             if str(pet.get("animal") or "").strip().lower() == animal and pet.get("name")]
    if len(named) < 2:
        return ""
    # A name is written the way a name is written, whatever case it was filed in.
    named = [name[:1].upper() + name[1:] for name in named]
    # "Two cats, Milo and Max", "Three cats, Milo, Tom and Ada": the count the store holds, said
    # in words the way a person says it.
    thing = (_many(len(named), animal)[:1].upper() + _many(len(named), animal)[1:]
             + ", " + _a_list_of_names(named))
    return pick(ack.PET_TAIL_MANY, memory or {},
                str((fixed or {}).get("said") or "")).format(Thing=thing)

def _correction_said(fixed, memory=None):
    """The short line that says which value the bot is going with now."""
    if not isinstance(fixed, dict):
        return ""
    if fixed.get("key") == "pets_more":
        return _the_second_pet_said(fixed, memory)
    # A fact about someone else is worded by the reading that kept it ("I'll keep your mum off
    # those"), so its note is the whole line rather than a value in a shape.
    if fixed.get("note"):
        return str(fixed["note"])
    value = fixed.get("value")
    if not value:
        return ""
    if fixed.get("key") == "job":
        # A job is said in the words the person used for it: they told the bot where they work,
        # so the note says that back. "Hospital — got it, I'll say Hospital" is the bot talking
        # about its own wording, and it is not the fact.
        note = _job_note(str(value), user(memory) if isinstance(memory, dict) else None)
        if note:
            return note
    in_a_sentence = fixed.get("key") in ("budget", "plan", "birthday") and fixed.get("sentence")
    if in_a_sentence:
        value = " ".join(str(fixed["sentence"]).split())
        # The sentence is sometimes the person's own repair rather than the reading's:
        # "sorry, i mean saturday" was said back as "Got it — Sorry, you mean on Saturday", the
        # steering and the bot's own voice in one line. The frame is what they said to correct
        # themselves, not part of the day, so it comes off before the sentence is said back.
        unframed = ack.without_the_frame(value)
        if unframed and unframed != value:
            value = unframed
            if fixed.get("key") == "plan":
                bare = str(fixed.get("value") or "").strip()
                # A sentence that was only the frame and the new value ("sorry, i mean on
                # saturday") says the value on its own: "Got it — Saturday", not "— on Saturday".
                if bare and " ".join(value.split()).lower() in (
                        bare.lower(), "on " + bare.lower(), "in " + bare.lower(),
                        "at " + bare.lower()):
                    value = bare
        if fixed.get("key") == "plan":
            # The sentence is the person's own, so a note that says it in their voice is the bot
            # talking about itself: "my sister and i are going to spain" came back as "Got it —
            # my sister and i are going to spain", and "i start my new job on tuesday" as "Got it
            # — i start my new job on tuesday". The rest of the plan is said back in the second
            # person, so the note is too.
            value = you(value)
            value = value[:1].lower() + value[1:]
        # The sentence arrives as the person typed it, full stop and all, and the note adds its
        # own: "I'm going to Portugal in July." not "July..".
        value = value.rstrip(" .!?")
    shown = str(value)[:1].upper() + str(value)[1:]
    wrong = str(fixed.get("wrong") or "").strip()
    if wrong:
        if fixed.get("key") == "pet":
            # A name put right is answered warmly and in different words from turn to turn; the
            # two names are in every line, so what varies is only the one warm thing after. The
            # seed is the line itself, so two different corrections do not get the same sentence
            # and the same line twice always answers the same way for a comparison.
            return pick(PET_RENAMED_SAY, memory,
                        str(fixed.get("said") or "")).format(v=shown, w=wrong)
        # A correction that names both values says both back: "8 kilos, not 5 — got it."
        shape = CORRECTION_SAY_PAIR.get(fixed.get("key"), "{v}, not {w} — got it.")
        return shape.format(v=shown, w=wrong)
    if fixed.get("dropped"):
        shape = CORRECTION_SAY_DROP.get(fixed.get("key"), "Not {v} — got it.")
        said = str(value)
        return shape.format(v=said[:1].lower() + said[1:])
    if in_a_sentence:
        # A plan is said inside a sentence - "Got it — the gym at 7." - so the article or the
        # "my" in front of it is not capitalised the way a name in that place would be. A
        # birthday is said the same way: "Got it — your birthday is the 4th of May."
        first, _, rest = shown.partition(" ")
        if first.lower() in PLAN_LOW_START:
            shown = first.lower() + (" " + rest if rest else "")
    if fixed.get("key") is None:
        # No fact was corrected, so there is nothing to keep: the line is said back and dropped.
        return BARE_ECHO_ONLY.format(v=shown)
    shape = CORRECTION_SAY.get(fixed.get("key"), "{v} — got it, I'll go with {v}.")
    if "{a}" in shape:
        return shape.format(v=shown, a=str(fixed.get("animal") or "pet"))
    return shape.format(v=shown)

def _job_note(value, known):
    """The corrected job said back in the frame the person used, or "" when there is no frame.

    The frame is kept with the job (facts.extract writes job_frame), so "i work in a school" then
    "sorry i meant a hospital" says "Got it — you work in a hospital". A frame that is the shift
    rather than a place ("i work nights") is left to the short note: "you work a nurse" is not a
    sentence anybody says.
    """
    frame = str((known if isinstance(known, dict) else {}).get("job_frame") or "").strip()
    if frame == "work":
        # "my job is a teacher" then "i meant a nurse": the word they used for it was the job
        # itself, so the note says the job.
        return "Got it \u2014 your job is " + _a(str(value)) + "."
    if frame.split(" ")[0] not in ("at", "in", "for", "as"):
        return ""
    said = _job_said({"job": value, "job_frame": frame})
    if not said:
        return ""
    return "Got it \u2014 " + said[:1].lower() + said[1:] + "."

NOT_THE_SAME = re.compile(
    r"^(?:(?:and|but)\s+)?(?:my|our)\s+(?P<who>[a-z]+(?:[ -]in[ -]law)?)\s+"
    r"(?P<no>isnt|isn['\u2019]?t|is\s+not|doesnt|does\s+not|wasnt|was\s+not)$", re.I)

def _the_limit_the_last_line_gave(memory):
    """The limit the line before stated, on the person that line was about, or None.

    It is theirs ("im allergic to nuts") or somebody else's ("my mum is vegetarian"), and it is
    only that line's: a line about the weather is not a limit with nothing after it, so "my son is
    too" following one carries nothing.
    """
    said = " ".join(str(last_user(memory) or "").lower().split())
    if not said:
        return None
    for entry in reversed(memory.get("facts_log") or []):
        if not isinstance(entry, dict):
            continue
        if " ".join(str(entry.get("text") or "").lower().split()) != said:
            continue
        value = entry.get("value")
        if entry.get("key") in ("allergies", "diet"):
            return user(memory)
        if entry.get("key") in ("other", "others") and isinstance(value, dict) \
                and (value.get("allergies") or value.get("diet")):
            return value
    return None

def _not_the_same_reply(memory, low):
    """The limit refused for somebody, acknowledged, and nothing filed."""
    if not isinstance(low, str):
        return None
    match = NOT_THE_SAME.match(" ".join(low.split()))
    if not match:
        return None
    who = _canon_relation(extract.a_person_word(match.group("who")))
    if who not in extract._A_WORD_FOR_A_PERSON:
        return None
    if not _the_limit_the_last_line_gave(memory):
        return None
    said = "your " + who
    return _vary(["Got it \u2014 " + said + " isn't.",
                  "Good to know \u2014 " + said + " isn't, then.",
                  "Right, so it's not " + said + " \u2014 noted."], memory)

_RELATION = "|".join(sorted(extract.RELATIONS, key=len, reverse=True))

OTHER_ASK = re.compile(
    r"\b(?:what|which|who)\b[^?]{0,40}?\b(?:my|your)\s+(?:"
    + _RELATION + r")\b|"
    r"\b(?:does|did|is|was)\s+(?:my|your)\s+(?:" + _RELATION + r")\b|"
    r"\bwhat (?:does|did) (?:she|he|they) eat\b|"
    # "what is she allergic to?" about a person the chat knows: the relation is in the previous
    # line and the pronoun is the one who fits it, so the ask names nobody and read as nothing.
    r"\bwhat(?:'s|s| is| was)\s+(?:she|he|they)\s+(?:allerg\w*|not eat|eat)\b|"
    r"\bis (?:she|he|they)\s+allerg\w*\b|"
    r"\bwhat did i say (?:she|he|they|my|your)\b[^?]{0,30}?\b(?:eat|allerg\w*)\b|"
    r"\b(?:does|did) (?:she|he|they)\b[^?]{0,20}?\beats?\b", re.I)

OTHER_FACT = re.compile(r"allerg\w*", re.I)

WHO_IS_NAME_ASK = re.compile(
    r"\bwho(?:'s|s| is| was)\s+(?P<name1>[a-z][a-z'\-]{1,20})\b"
    r"|\bdo\s+(?:i|you)\s+(?:know|remember)\s+(?:a\s+|an\s+)?(?P<name2>[a-z][a-z'\-]{1,20})\b"
    r"|\bis\s+(?P<name3>[a-z][a-z'\-]{1,20})\s+(?:my|our)\s+(?P<who3>[a-z]+)"
    r"|\b(?P<name4>[a-z][a-z'\-]{1,20})\s+is\s+(?:my|our)\s+(?P<who4>[a-z]+)\s*[?.]?\s*$", re.I)

NAME_ASK_TAIL = frozenset("again then though please now too already anyway".split())

THEM = re.compile(r"\b(?:she|he|her|they|them|their|hers|his|him)\b", re.I)

OTHER_NAME_ASK = re.compile(
    r"\bwhat(?:'s|s| is| was| are)?\s+(?:do|did)?\s*(?:i|you)\s+call\s+(?:my|our)\s+"
    r"(?P<who1>" + KIN_ASK + r")\b"
    r"|\bwhat(?:'s|s| is| was)\s+(?:my|our)\s+(?P<who2>" + KIN_ASK + r")(?:'s|s')?\s+name\b"
    r"|\bwhat\s+(?:is|was|are|were)\s+(?:my|our)\s+(?P<who5>" + KIN_ASK + r")\s+called\b"
    r"|\bwhat\s+are\s+(?:my|our)\s+(?P<who3>" + KIN_ASK + r")\s+called\b"
    # The verb and the question mark are often left off: "my daughters name" is the same ask as
    # "what is my daughters name", and read as a statement it filed the word "name" as her name.
    r"|\bm(?:y|ine)\s+(?P<who4>" + KIN_ASK + r")(?:'s|s')?\s+names?\s*(?:again)?\s*\??\s*$"
    r"|\b(?:do|did)\s+(?:you|u)\s+(?:remember|know)\s+(?:my|our)\s+(?P<who6>" + KIN_ASK + r")(?:'s|s')?\s+name\b"
    r"|\b(?:do|did)\s+(?:you|u)\s+(?:remember|know)\s+what\s+(?:my|our)\s+(?P<who7>" + KIN_ASK + r")\s+"
    r"(?:is|was|are|were)\s+called\b"
    r"|\bremind\s+me\s+(?:what\s+)?(?:my|our)\s+(?P<who8>" + KIN_ASK + r")\s+(?:is|was|are|were)\s+called\b"
    r"|\bremind\s+me\s+what\s+(?:my|our)\s+(?P<who9>" + KIN_ASK + r")(?:'s|s')?\s+name\s+is\b"
    # the reminder wrapper comes off before this reader runs, so the ask arrives as a relative
    # clause: "remind me what my sister is called" reaches the store as "what my sister is called".
    r"|\bwhat\s+(?:my|our)\s+(?P<who10>" + KIN_ASK + r")\s+(?:is|was|are|were)\s+called\b"
    # "who is my friend" is the same ask as "what is my friend called" once the store has a name
    # filed for the person: the name they gave is the answer, and "I'd rather not guess" is a
    # denial of something they told us. The relation has to be the whole ask - "who is my friend
    # coming with" asks about the visit, not the name - so nothing may follow it but "called",
    # "again" and the question mark.
    r"|\bwho(?:'s|s| is| was)\s+(?:my|our)\s+(?P<who11>" + KIN_ASK + r")\s*(?:called|again)?[\s?.!]*$",
    re.I)

PRONOUN_NAME_ASK = re.compile(
    r"\bwhat(?:'s|s| is| was)\s+(?P<pos>his|her|their)\s+name\b"
    # "what are their names" is the same ask with the several of them said out loud: after "my
    # daughter emma is 4 and my son jack is 6" it was the search hedge.
    r"|\bwhat\s+(?:are|were)\s+(?P<pos4>his|her|their)\s+names?\b"
    r"|\bwhat\s+(?:is|was|are)\s+(?P<sub>he|she|they)\s+called\b"
    r"|\bwhat\s+(?:do|did)\s+(?:i|you)\s+(?:call|say)\s+(?P<obj>him|her|them)\b"
    r"|\b(?:do|did)\s+(?:you|u)\s+(?:remember|know)\s+(?P<pos2>his|her|their)\s+name\b"
    r"|\b(?:do|did)\s+(?:you|u)\s+(?:remember|know)\s+what\s+(?P<sub2>he|she|they)\s+"
    r"(?:is|was|are)\s+called\b"
    r"|\bremind\s+me\s+what\s+(?P<obj2>him|her|them)\s+(?:is|was)\s+called\b"
    r"|\bwhat\s+(?P<pos3>his|her|their)\s+name\s+(?:is|was)\b", re.I)

def _with_an_in_law(who, low):
    """The person an ask names with the "in law" it was said with: "brother in law"."""
    if not who:
        return who
    if extract.an_in_law(who):
        return extract.a_person_word(who)  # "brother-in-law" is filed as "brother in law"
    if re.search(r"\b" + re.escape(who) + r"s?" + IN_LAW_AFTER_TEXT, low or "", re.I):
        return who + " in law"
    return who

KIDS_ASK = re.compile(
    r"\bhow many (?:kids?|children|child)\b|"
    r"\bdo (?:i|we) have (?:any )?(?:kids?|children)\b|"
    r"\b(?:have|did) (?:i|we) (?:got|have) (?:any )?(?:kids?|children)\b", re.I)

KIDS_SOMEONE_ELSE = re.compile(
    r"^\W*(?:do|does|did|has|have|had|is|are|was|were)\s+"
    r"(?:my|our|his|her|their|your|you|the|she|he|they|them|it)\b", re.I)

KIDS_A_DECISION = re.compile(r"\b(?:should|shall|worth|afford|too many|enough|ok|okay|normal)\b",
                             re.I)

def _kids_ask(low):
    """Whether the line asks the person's own count of children."""
    match = KIDS_ASK.search(low) if isinstance(low, str) else None
    if not match:
        return False
    if KIDS_SOMEONE_ELSE.match(low[match.end():]):
        return False
    return not KIDS_A_DECISION.search(low)

ABOUT_A_NAME = re.compile(
    r"\b(?:what|anything|everything|much|else)\b[^?]{0,30}?\b(?:know|knows|knew|remember|"
    r"told|tell|said|say|mention|mentioned)\b[^?]{0,25}?\babout\s+([a-z][a-z'-]{1,20})\b|"
    r"\b(?:do|did|can)\s+(?:you|i)\s+(?:ever\s+)?(?:know|remember|tell|told|mention|say|said)\b"
    r"[^?]{0,30}?\babout\s+([a-z][a-z'-]{1,20})\b", re.I)

# The ask that wants the children as a group. It is read with every word a group of children goes
# by, not only "kids": "what do you know about my girls" and "what have you got on my sons" were
# both answered with the search hedge a turn after the same chat gave their ages, because the
# children were filed under the word the person used ("girls", "sons") and this asked for another.
CHILDREN_ABOUT = re.compile(r"\b(?:kids?|children|child|boys?|girls?|sons?|daughters?|"
                            r"twins?|lads?|lasses|youngest|eldest|oldest)\b", re.I)

ABOUT_PERSON_MORE = re.compile(r"\b(?:else|other|more|anything)", re.I)

EAT_ASK = re.compile(r"\b(?:eat|eats|eating|diet|vegan|vegetarian|pescatarian)\b", re.I)

FOOD_ASK = re.compile(r"\b(?:eat|eats|eating|eaten|food|foods|drink|drinks|drinking|diet|"
                      r"meal|meals|breakfast|lunch|dinner|snack|cook|cooking)\b", re.I)

DIET_ASK = re.compile(r"\bmy diet\b|\bwhat (?:do|did) i eat\b|\bwhat am i eating\b|"
                      r"\b(?:what|which) diet (?:am i|do i|did i|was i)\b|"
                      r"\bwhat (?:can|can't|cant|could) i (?:not )?(?:eat|have)\b|"
                      r"\bwhat do i not eat\b|\bam i (?:vegetarian|vegan|pescatarian|on a diet)\b",
                      re.I)

DIET_HOW_TO = re.compile(r"\bhow (?:do|does|can|could|should|would|might|to)\b|"
                         r"\bany (?:tips|advice|ideas|suggestions|ways)\b|"
                         r"\bways? to\b|\bwhat can i do\b|\bhelp me\b|\btips for\b", re.I)

DIET_FACT_ASK = re.compile(
    r"\bmy diet\b|"
    r"\bwhat do i not eat\b|"
    r"\bwhat (?:can't|cant|couldn't|could not|can not) i (?:eat|have)\b|"
    r"\bwhat (?:can|could) i not (?:eat|have)\b|"
    r"\bam i (?:vegetarian|vegan|pescatarian|on a diet)\b", re.I)

ASK_WORD = re.compile(r"\b(?:what|which)\b", re.I)

HELP_ASK = re.compile(r"\b(?:should|could|can|shall|cook|make|recipe|recipes|meal|meals|dinner|"
                      r"lunch|breakfast|snack|safe|help|suggest|ideas?)\b", re.I)

CANT_HAVE = re.compile(
    r"\b(?:can(?:not|\s+not|'?t)|could(?: not\b|n'?t)|must(?: not\b|n'?t)|"
    r"should(?: not\b|n'?t)|may not)\b[^?!.]{0,14}?\b(?:have|eat|drink)\b"
    r"|\bwhat\b[^?!.]{0,30}?\b(?:to )?avoid\b|\b(?:things?|foods?|stuff)\s+to avoid\b", re.I)

CAN_HAVE = re.compile(r"\bwhat\b[^?!.]{0,30}?\b(?:can|could)\s+\w+\s+(?:have|eat|drink)\b", re.I)

CAN_THEY_HAVE = re.compile(
    r"\b(?:can|could|should|may)\s+(?:he|she|they|him|her|them)\s+(?:have|eat|drink)\b"
    r"|\bis\s+[a-z][a-z'\u2019 -]{1,24}?\bok\s+(?:for|with)\s+(?:him|her|them)\b"
    r"|\bdoes\s+(?:he|she|they)\s+(?:eat|drink|have)\b", re.I)

CAN_THEY_HAVE_A_FOOD = re.compile(
    r"\b(?:can|could|should|may)\s+(?:he|she|they|him|her|them)\s+(?:have|eat|drink)\s+"
    r"(?!(?:for|with|at|on|in|to|instead)\b)[a-z]", re.I)

FOOD_HAS = {
    "dairy": frozenset("""milk cheese butter cream yoghurt yogurt custard latte cappuccino
        cheddar mozzarella feta parmesan brie ice cream ice-cream milkshake ghee paneer""".split()),
    "gluten": frozenset("""bread pasta flour wheat cereal biscuit biscuits cake pastry
        couscous cracker crackers noodles pizza baguette toast bun buns pitta pita rye barley""".split()),
    "wheat": frozenset("""bread pasta flour cereal biscuit biscuits cake pastry noodles
        couscous cracker crackers pizza baguette toast bun buns pitta pita""".split()),
    "sugar": frozenset("""cake chocolate sweets sweets biscuits jam honey syrup pudding
        ice cream ice-cream fizzy juice cola""".split()),
    "nuts": frozenset("""peanuts pesto satay muesli granola almond almonds cashew
        cashews hazelnut hazelnuts walnut walnuts pecan pecans pistachio pistachios
        marzipan praline nutella""".split()),
    "peanuts": frozenset("""peanuts pesto satay""".split()),
    "shellfish": frozenset("""prawns prawn shrimp shrimps crab lobster mussels scallops
        shellfish seafood""".split()),
    "fish": frozenset("""salmon tuna cod haddock sardines mackerel anchovy anchovies
        trout prawns""".split()),
    "eggs": frozenset("""egg mayonnaise mayo meringue omelette omelette frittata
        custard""".split()),
    "soya": frozenset("""tofu edamame soy soya miso tempeh""".split()),
    "sesame": frozenset("""tahini hummus sesame houmous""".split()),
}

STATED_THEN_ASKED = re.compile(r",\s*(?=(?:what|which|how|why|when|where|who|should|can|could|"
                               r"would|will|is|are|do|does|any)\b)", re.I)

ASKS_WITH_WH = re.compile(r"\b(?:what|which|how|why|when|where|who)\b", re.I)

def _the_ask_after_a_statement(low, memory=None):
    """The question clause at the end of a line that states something first, or the line itself.

    "my son is 7 and has a nut allergy, what can i pack him for lunch" is a question about a
    packed lunch, not about the allergy. A line whose first clause asks something too ("what is
    he allergic to, and what can he eat") is left whole: every clause is the ask there.
    """
    text = str(low or "")
    read = memory.get("understood") if isinstance(memory, dict) else None
    if isinstance(read, dict):
        # The understanding engine has already cut the line into its clauses, and its focus is
        # the one the person is asking about. `_folded` has taken the comma out by then, so the
        # cut cannot be made from the words alone.
        clauses = read.get("clauses")
        focus = read.get("focus")
        if isinstance(clauses, list) and len(clauses) > 1 and focus:
            asked = " ".join(str(word) for word in focus if str(word or "").strip()).strip()
            first = " ".join(str(word) for word in (clauses[0] or ()))
            # Only a fact said before the question is context for it. A question that comes first
            # ("whats a good dinner, my son is allergic to nuts") is still the whole line's ask,
            # and the fact at the end is part of it.
            if asked and asked != text.strip() and asked != first.strip():
                return asked
    parts = STATED_THEN_ASKED.split(text, 1)
    if len(parts) < 2 or ASKS_WITH_WH.search(parts[0]):
        return text
    asked = parts[1].strip()
    return asked or text

def _asks_about_someone(low, text, memory=None):
    """Whether this line asks about a fact the store keeps for someone else.

    "what is he allergic to" and "what cant she have" are about the person the chat was just
    told about, and the store has that fact; read by nobody they fell to the encyclopedia entry
    for the word "allergy", which answers a question about the world to someone who asked about
    their son. Only a question is read this way: "he is allergic to nuts" is telling, and the
    person typing is not "he" (that is DIET_ASK's job). Which person the line is about is left to
    the reader in `_other_person_reply`, which knows the relations, the names and the pronoun:
    a line with nobody in it gets no answer from it.

    A line that states a fact and then asks something else is read on its question: "my son is 7
    and has a nut allergy, what can i pack him for lunch" asks about a lunch, and answering the
    allergy leaves the question the person actually asked on the floor. The split is only made
    where the store would have answered the line as it stands: "my wife is allergic to shellfish,
    can she eat prawns" is answered by the answer modules, which say why prawns are out, and
    splitting it here handed the store's thin diet receipt the turn.
    """
    whole = str(low or "")
    if not _asks_the_line(whole, text):
        return False
    ask = _the_ask_after_a_statement(whole, memory)
    if ask.strip() == whole.strip():
        return True
    return _asks_the_line(ask, text)

def _asks_the_line(low, text):
    """Whether this line, read whole, asks about a fact the store keeps for someone else."""
    low = str(low or "")
    if OTHER_ASK.search(low):
        return True
    if _asks_for_a_limit_not_advice(low) and (
            ASK_WORD.search(low) or ASK_START.search(low)
            or str(text or "").strip().endswith("?")):
        # "does she need to avoid anything" names the limit and asks for it; it is the same ask
        # as "is she vegan", and none of the sets below hold the word "avoid".
        return True
    if DIET_ASK.search(low) and not DIET_HOW_TO.search(low):
        return False  # "what's my diet" is about them, whatever is kept for someone else
    if not (EAT_ASK.search(low) or CANT_HAVE.search(low) or CAN_HAVE.search(low)
            or CAN_THEY_HAVE.search(low) or OTHER_FACT.search(low)):
        return False
    return bool(ASK_WORD.search(low) or ASK_START.search(low) or CAN_THEY_HAVE.search(low)
                or str(text or "").strip().endswith("?"))

THE_CHAT_ASK = re.compile(
    r"\bwhat (?:were|are|was) (?:we|i|you) (?:talking|chatting|saying|on) about\b|"
    # "what are you up to" is not a recap: the person is asking the bot what it is doing, and
    # the only honest answer is that there is nothing at this end. "what were you saying" and
    # "what were you on about" are still the recap - there the "you" is the chat's own last ask.
    r"\bwhat (?:were|are|was) (?:we|i) (?:on|up to)\b|"
    r"\bwhat (?:were|was) you (?:on|up to)\b|\bwhat are you on about\b|"
    r"\bwhat (?:were|was) you saying\b|"
    r"\bwhat (?:have|had|did) (?:we|you) (?:talked|spoken|chatted|covered|discussed) about\b|"
    r"\bwhat (?:were|are|was) (?:we|i|you) saying\b|"
    r"\bwhere (?:were we|are we)(?=\s*[?.!,]|\s*$)|"
    r"\bwhere did we (?:leave|get to|stop)\b|\bwhere we (?:got to|left off)\b|"
    r"\bwhat was i (?:saying|on about|telling you|mentioning)\b|\bcatch me up\b|\brecap\b|"
    + MISSED_CATCH_UP.pattern + r"|"
    r"\bwhat have i been (?:saying|telling you)\b|"
    r"\bremind me (?:what|where|how)\b|\bsum (?:up )?what we\b|"
    # One ask with the "have" in it or left out: "what we have covered" and "what we covered". The
    # "have" shape cannot be anything else, so it is read anywhere in the line; the shape without
    # it is also how a statement ends ("thats what we said"), so it is only the ask when it is the
    # whole line - which is what `_bare` leaves behind once the reminder wrapper comes off.
    r"\bwhat we (?:have|had) (?:covered|talked|discussed|done|said|been on)\b|"
    r"^(?:and |but |so |ok |okay |also |now )?what we "
    r"(?:covered|talked|discussed|done|said|been on)\b"
    r"(?=\s*(?:[?.!,]|$|again\b|so far\b|before\b|earlier\b|today\b|already\b))|"
    r"\bwhat we (?:talked|spoke|spoken|chatted|covered|discussed) about\b|"
    r"\bwhat we were (?:on|up to)\b", re.I)

def _about_the_bot_here(memory):
    """True when the understanding engine read this line as a question about the bot itself.

    "What have you been up to at the weekend", "what were you up to two days ago" ask the bot
    about its own doings and have nothing to do with what the person said, so the store must not
    read them as a recap of their line and answer "we're still at the beginning". The one ask
    about the bot the store does own is what it remembers (`about_bot_kind` is "memory").
    """
    reading = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(reading, dict):
        return False
    if the_manners_question(reading.get("norm") or []):
        # "What are you up to", "watcha doing" and "wuu2": how the bot is filling its time,
        # whichever words ask it. The engine reads the whole line, and `_about_the_bot_here` is
        # the one place that says it, because THE_CHAT_ASK below matches "what are you up to" as
        # "what were we on about" and the store answered a hello with "we're still at the
        # beginning". The ask about the bot the store does own is what it remembers.
        return True
    if not reading.get("about_bot"):
        return False
    return reading.get("about_bot_kind") != "memory"

def _about_this_chat(text, memory=None):
    """Lines that ask about the conversation itself, not about the world."""
    if _about_the_bot_here(memory):
        return False
    if history.asked(text):
        return True
    # A recall ask with nothing named in it ("anything you've learned about me", "what have you
    # picked up about me") is the whole picture asked for in other words. The reader that decides
    # so is the one the store answers with, so the gate and the answers agree: without this the
    # line was neither answered nor skipped, and the next "what did i tell you" quoted it back.
    if recall.ask(text) == "me":
        return True
    # "what was wrong with my boiler again" is a reminder about the boiler, and the store owns
    # it: read as a question about the world it was a fault to diagnose, so the answers lane
    # handed back its flow-temperature card a turn after the person told us about the boiler.
    if reminded.about_a_thing_they_said(text, memory):
        return True
    folded = _folded(text, memory)
    low = MORE_OF_IT.sub(r"\1", _bare(folded))
    # "how many cats", "how many have i got": a count of their own animals is a fact they told
    # the store, not a question about the world. Only a line that ends at the number counts -
    # "how many cats are there in the world" is still a question about the world.
    if _a_count_ask(low) is not None:
        return True
    # The length of a pregnancy the chat was told is the same kind of ask: "how far along is my
    # wife" and "how many weeks am i" are questions about what they said, and the store has the
    # number. The dating card answered them with how a due date is worked out while the store
    # held eight weeks, so the shape is published here as the chat's own business.
    if memory is not None and _a_length_i_have(memory, low):
        return True
    checks = (
        r"\b(?:what|which)\b.*\bmy name\b|\bwho am i\b|\b(?:know|remember) my name\b|"
        r"\bwhat did (?:i|u|you) (?:say|tell me) my name was\b|^my name$|\bwhat my name (?:is|was)\b",
        r"\bwhere do (?:i|we) (?:live|work|come from)\b",
        r"\bwhat did i say my job\b|\bwhat(?:'s| is| was) my job\b|\bwhere do (?:i|we) work\b|"
        r"\bwhat did i say i (?:do|did)\b|\bwhat do i work as\b|\bwhat do i do for (?:a )?living\b",
        # "where was i going with this" is a lost thread, not a place: the place ask is the one
        # that stands on its own. It is the same pattern the store answers it with, read here as
        # well, so a shape added to one is answered by the other: "whereabouts do i live" and
        # "what area do i live in" were in the answer but not in this gate, and fell to the
        # search hedge while the store had the place on file.
        PLACES_ASK.pattern + r"|\bwhere do (?:i|we) work\b",
        # The animal can be singular, plural or possessive: "what's my dog called",
        # "whats my dogs name", "what's my cat's name" are one ask, and people type all three.
        r"\bwhat(?:'s| is| was) my (?:dog|cat|pet)(?:'?s)?\b|"
        r"\bwhat did i say my (?:dog|cat|pet)(?:'?s)?\b|"
        r"\bremember my (?:dog|cat|pet)(?:'?s)?\b|\bwhat do i call my (?:dog|cat|pet)(?:'?s)?\b|"
        r"\bwhat did i call my (?:dog|cat|pet)(?:'?s)?\b|"
        r"\bwhat(?:'s| is| was) my (?:dog|cat|pet)(?:'?s)? called\b|"
        r"\bwhat are my (?:pets|dogs|cats) called\b|\bwhat are my (?:pets|dogs|cats)\b|"
        r"\bwhat did i say my (?:pets|dogs|cats) (?:were|are) called\b|"
        r"\bwhat my (?:dog|cat|pet)(?:'?s)?\b|^my (?:dog|cat|pet)(?:'?s)?$",
        # "what am I allergic to" arrives in many shapes: "what was I allergic to", "what I'm
        # allergic to", "what did I say I was allergic to". They all put "I" beside the ask.
        r"\bwhat (?:am|was) i allergic to\b|\bwhat i (?:am|was) allergic to\b|"
        r"\bwhat did i say i (?:am|was) allergic to\b|"
        r"\bwhat(?:'s| is| was)? my budget\b|\bmy budget again\b|\bwhat did i say my budget was\b|"
        r"^my budget$",
        # How they eat is a fact of theirs like their budget: "what's my diet" is a recall, not
        # a request for ideas. "what should i eat" is left to the answers, which can suggest.
        r"\bmy diet\b|\bwhat do i not eat\b|"
        r"\bwhat (?:do|did) i eat\b(?=\s*[?.!,]|\s*$)|"
        r"\bwhat am i (?:eating|not eating)\b",
        # Every shape of "what were we on?", and every shape of "say that back to me": these
        # are the lines that ask about the conversation, so the store must own them all. One
        # pattern, read in both places, so a shape added to the gate is answered as well.
        THE_CHAT_ASK.pattern,
        r"\bwhat did i (?:just )?(?:ask|want to know)\b"
        r"(?![^.?!]*\babout\b(?!\s+(?:me|it|that|this|them|us)\b))|"
        r"\bwhat did i (?:just )?say\b(?!\s+(?:about|to|when|in|on|wrong)\b)|"
        + ACTIVITY_ASK.pattern + "|" + PLAN_MINE.pattern,
        r"\bwhat have i told you\b|\bwhat do you (?:know|remember) about me\b|"
        r"\bwhat did i (?:tell|say)(?: you)? about me\b|\bwhat do you know about me\b|"
        # A clause that ends the line cannot tell an ask from a statement on its own: "i feel
        # guilty about what i said" and "remind me what i said" end the same way, and the
        # statement was answered with the whole picture ("Not much yet - you haven't told me
        # about yourself"). The reminder wrapper comes off in `_bare`, so the ask is the whole
        # line; anything in front of it is the statement it is a clause of.
        r"^what i (?:told|said)(?: you)?$|^what have i (?:told|said)(?: you)?$",
        r"\bremember what we talked about\b|\bdo you remember (?:what|our|yesterday|me)\b",
        # "what did i say about the cake?", "and what did i tell you about it?": whatever the
        # thing is, the question is about this conversation, not about the world.
        WHAT_I_SAID.pattern + r"|\bwhat was it i said\b|"
        # The same ask in the tense of the telling: "what was i telling you about the deposit",
        # "what have i been saying about the boiler". People use the tense of the telling, not
        # the tense of the reading, and the recap of the chat is not the line they want.
        r"\bwhat (?:was|were) (?:i|we) (?:telling you|mentioning|on about)\b|"
        r"\bwhat have i been (?:saying|telling you)\b|"
        # The same ask with the "did" left out, which is how people say it in a reminder:
        # "remind me what i said about the boiler", "can you remember what i told you...". What
        # follows is the thing or the ask ("about the boiler", "i was saving for"), never a
        # statement about the person ("what i said hurt him"), which is news, not a recall.
        # "we" as well when it names the thing: "remind me what we said about the boiler" is that
        # one recall, and a bare "what we said" is the recap of the whole chat.
        r"\b(?:what|anything) (?:i|we) (?:said|told you|mentioned|asked)"
        r"|\bwhere (?:we|it|this|the (?:chat|conversation)) (?:all )?(?:started|began)\b"
        r"|\bwhich (?:question|thing) (?:did i|i) (?:ask|asked|say|said|start with|started with)\b"
        r"(?=\s*(?:\?|$|again\b|please\b|about\b|i\b|my\b|the\b|that\b|"
        r"to (?:me|you)\b|before\b|earlier\b))|"
        r"\b(?:do|can|could|did) (?:you|u) remember what i\b",
        # "remind me what i do" is the job ask in the words a reminder uses; a bare "what i do"
        # after a statement ("that's what i do") is not an ask at all, so it needs the pointer.
        r"^what i (?:do|did)$|\b(?:remind me|tell me|can you (?:remind me|tell me)) what i (?:do|did)\b|"
        r"\bwhat did i say my age\b|\bhow old am i\b|\bwhat(?:'s| is| was)? my age\b|"
        r"\bmy age again\b|\bhow old did i say\b|"
        # The age in the order a reminder puts it: "do you know how old i am", "remind me how
        # old i am". `_bare` takes the asking frame off, so what is left is "how old i am",
        # and the gate has to know it is the same ask or it never reaches `_age_reply`.
        r"\bhow old i (?:am|was)\b",
        r"\bwhat (?:am i|are we) (?:planning|up to)\b|\bwhat (?:am i|are we) doing\b(?!\s+wrong)\b|"
        r"\bwhat(?:'s| is|s)?\s+(?:coming up|on for (?:me|us))\b|"
        r"\bwhat (?:have|has) (?:i|we) got (?:coming up|on|planned)?\b|"
        r"\bwhat do (?:i|we) have (?:coming up|on|planned)\b|"
        r"\banything (?:planned|coming up)\b|\banything on\b" + NOT_ON_A_MEDIUM +
        r"|\bwhat am i looking forward to\b|"
        # A plan is a fact of theirs like the budget, and people ask for it in the past as often
        # as the present: "what was I planning?", "remind me what I'm saving for", "whats my
        # plan". The reminder wrapper is off already ("what i was planning").
        r"\bwhat (?:was|were) (?:i|we) (?:planning|saving|saving up)\b|"
        r"\bwhat (?:am i|are we|is) (?:saving|saving up)\b|"
        r"\bwhat i (?:was|am) (?:planning|saving)\b|"
        r"\bwhat(?:'s| is| was) my plan\b" + NOT_THE_PLAN + r"|"
        r"\bwhat was (?:the|my) plan\b" + NOT_THE_PLAN + r"|"
        r"\bwhat was i going to do\b(?:\s*then)?\s*[?.!,]*$|"
        r"\bwhere (?:are|were|was|am) (?:we|i) (?:going|off|headed|heading|away)\b|"
        r"\bwhen (?:are|were|was|am) (?:we|i) (?:off|going|away|moving|flying|travelling)\b|"
        r"\b(?:which|what) (?:month|day|week|date) (?:are|am|is) (?:we|i)\b|"
        r"\bremind me where\b",
    )
    if ASKED_ALL.search(low):
        return True
    if any(re.search(pattern, low) for pattern in checks):
        return True
    if TOPIC_ASK.search(low) or ASK_WITHOUT_MY.search(low):
        return True
    # "summarise our chat", "what did we talk about": a recap ask is about the conversation, so
    # it is never quoted back as something the person said, and it is never the thing the chat
    # was on.
    if _summary_ask(low):
        return True
    # "what's the noise again?" names the thing instead of asking "what did I say about it".
    # It is a recall only when the thing is one they really said: the word has to be in one of
    # their last lines, so "what's the time" is still a question about the time.
    named = THING_AGAIN.match(low)
    if named and _said_word(named.group(1), memory):
        return True
    # "and which knee was it": a detail they gave, asked for by the thing it is about. The same
    # ask as "what did i say about my knee", and it was answered by nobody - the gate let it
    # through as a question about the world, so it got the search hedge from the fallback.
    if _which_thing_was_it(low, memory):
        return True
    if _an_attribute_they_gave(low):
        return True
    # "what subject did i say i was revising": only when a line answers it does the gate hold.
    if _an_open_attribute_ask(low, memory):
        return True
    # "and my job?" after "what's my name?" is one more fact recalled, not a new subject: a
    # short line that only names a fact of theirs, and only once the recall is already going.
    if re.search(r"^my (?:job|work|name|budget)$", low) and _recall_in_progress(memory):
        return True
    # Reads of the chat itself keep the words that ask for them: "say that again" needs its
    # "again", so these are matched before the reminder wrapper comes off.
    if FIRST_ASK.search(low) or SAID_ASK.search(low) or _repeat_ask(text, folded):
        return True
    # A money ask in the present tense names a thing the chat may already hold a bill for: "my
    # water is 40 a month" then "how much do i spend on water" was answered "Six to eight
    # glasses a day", because the entry keyed on the word "water" is supported by the line and
    # took the turn from the store that had the figure. Where a bill for that very thing is on
    # record the line is the figure they gave, asked back. Where none is, it is the habit
    # question it sounds like ("how much do i spend on food a month"), and the world's.
    if memory is not None and spent.PRESENT_ASK.search(text or "") and spent.answer(text, memory):
        return True
    # "what do I do?" is only about their job when the line points back at what they told us
    # ("what do I do again?", "what do I do for a living?") or when the recall is already going
    # ("what did I say my name was?" / "and what do I do?"). After a problem
    # ("my washing machine is leaking" / "what do I do?") it is a request for help, and a real
    # answer should take the turn.
    if not re.search(r"\bwhat do i do\b", low) or len(low.split()) > 7:
        return False
    if MEMORY_POINTER.search(folded) or _recall_in_progress(memory):
        return True
    # "i work in a warehouse" then "what do i do" is the job they just told us; the same ask
    # after a problem ("my washing machine is leaking") is a request for help, not a recall.
    return _job_just_said(memory, low)

ASK_TAIL_FILLER = frozenset("""then now again here today tonight please thanks ok okay so also
just really honestly exactly mate actually""".split())

ASK_ABOUT_JOB = re.compile(
    r"^(?:at work|for a living|for work|for a job|all day|day to day|in the week|"
    r"when i(?:'m| am) at work|in my job|at the moment|these days)$")

def _ask_about_the_job(ask):
    """Whether a "what do i do" ask has nothing after it, or only words about the work itself."""
    found = re.search(r"\bwhat do i do\b(.*)$", " ".join(str(ask or "").lower().split()))
    if not found:
        return True
    tail = " ".join(word for word in re.findall(r"[a-z']+", found.group(1))
                    if word not in ASK_TAIL_FILLER)
    return not tail or bool(ASK_ABOUT_JOB.match(tail))

def _job_just_said(memory, ask=""):
    """True when the last line the person wrote is the one that gave us their job.

    Only a line that is *about the job* counts. "i work in a warehouse" then "what do i do"
    is the job they just told us; "i'm a nurse and my back is killing me" then "what do i do"
    is a request for help, because the line carried something else with it, and that something
    else is what the ask is about.
    """
    me = user(memory) or {}
    job = me.get("job")
    line = last_user(memory) or ""
    if not job or not line:
        return False
    # The job can be a phrase ("bus driver") or a name ("mcdonalds", "co-op"), so any of its
    # words will do: the last line is the one that gave us the job when it uses one of them.
    # The name itself is checked first, because ``content`` drops a short one ("co-op").
    said = " ".join(str(job).lower().split())
    # Where they work is the job's too. The place is kept beside the role, so a line like "i work
    # at mcdonalds" names no word of the role and no word of ``WORK_WORDS``, and without this the
    # bare ask after it would be answered as though the chat had moved on from the job. A line
    # that gave us the place is a line about the job, on the same terms as one that gave the role.
    place = " ".join(str(me.get("workplace") or "").lower().split())
    if not (said in " ".join(line.lower().split()) or _job_words_seen(job, line)):
        if not (place and _the_place_said(place, line)):
            # The last line need not name the job: a line about the work itself ("i teach year 4",
            # "i mostly do spreadsheets") keeps the conversation on it, so the bare ask is still
            # about the job they told us. A line about their back is not, and answers for itself.
            return _a_work_detail(line) and _ask_about_the_job(ask)
    if not _only_the_job(line, job, place):
        return False
    # The ask has to be about the job too: "what do i do about my back" is a back question.
    return _ask_about_the_job(ask)

SELF_DO_AGAIN = re.compile(
    r"\bwhat (?:do|should|shall|can) i do again\b|"
    r"\bwhat i (?:do|did) again\b")

def _doing_again(text, memory):
    """True when "what do i do again" is about the task on the table, not the person's job."""
    folded = _folded(text or "", memory)
    if not SELF_DO_AGAIN.search(folded):
        return False
    if _recall_in_progress(memory):
        return False
    # The line the person just wrote may be the one that gave the job ("hi, i'm a baker in
    # Cardiff"), which `_job_just_said` does not count because it also carries a name: the job
    # is still what they last told us, so "what do i do again?" is that job.
    job = (user(memory) or {}).get("job")
    line = last_user(memory) or ""
    if job and (str(job).lower() in line.lower() or _job_words_seen(job, line)):
        return False
    return not _job_just_said(memory, "what do i do again")

WORK_WORDS = frozenset("""
    work works working worked job jobs shift shifts rota office shop store school site floor
    till ward class classes year years teach teaches teaching taught lesson lessons pupil pupils
    student students manage managing manager boss team colleagues employer staff run running look looking after
    stack stacking shelf shelves serve serving customers clients patients drive driving nurse
    nursing clean cleaning cook cooking chef sort sorting stock sell selling till fix fixing
    build building repair study studying train training paperwork spreadsheets meetings meeting
    emails email calls call desk counter kitchen warehouse factory clinic hospital
""".split())

NOT_A_DETAIL = frozenset("""
    hurt hurts hurting ache aches aching pain pains ill sick unwell tired exhausted stressed
    worry worried anxious sad low fed depressed killing killed broke broken leaking wrong
    problem problems cross upset angry cry crying lost quit quitting leaving left fired sacked
    bullying bullied
    hate hates hated love loves fancy stole stealing short complaint complained warned blamed
    mistake mistakes accident incident busy rush
    today tonight tomorrow morning mornings evening evenings afternoon afternoons later soon
    every each weekly daily
""".split())

def _a_work_detail(line):
    """Whether the line is a detail of the work alone, with nothing else that wants an answer."""
    low = " ".join(str(line or "").lower().split())
    if not low.startswith(("i ", "im ", "i'm ", "we ", "we're ")):
        return False
    words = {word.strip(",.!?;:'\"()") for word in low.split()}
    words.discard("")
    if len(words) > 10 or "?" in low:
        return False
    if words & NOT_A_DETAIL:
        return False
    if not words & WORK_WORDS:
        return False
    # Every other word says something about the work or nothing at all. "i got an email from HR",
    # "i fancy my manager" and "i stole from the till" all carry a word of the work and are about
    # something else, so a bare ask after them is about that something else.
    for word in words:
        if word in WORK_WORDS or word in JOB_ONLY or word.isdigit():
            continue
        return False
    return True

def _job_words_seen(job, line):
    """Whether the line uses one of the job's words, however it ends the word."""
    mine = set(content(job))
    for word in str(job).split():
        mine |= forms(word)
    seen = set(content(line))
    return bool(mine & seen) or any(mine & forms(word) for word in seen)

JOB_ONLY = frozenset("""
    i im am a an the my me and but so oh also too now just still actually really always
    sometimes only since ago these days day days night early late full part time hour hours
    week weeks month months year years shift shifts work working works job started start new
    mostly usually lots few two three four five
    as at in for on of to do doing it that this
    changed change changes switched switching switch job jobs role career quit quits left leaving
    packed gave lost moved got get getting have had
    today tomorrow soon next monday tuesday wednesday thursday friday saturday sunday january
    february march april may june july august september october november december spring summer
    autumn winter
""".split())

def _the_place_said(place, line):
    """Whether this line is the one that told us where they work.

    The place is kept with its own little words ("in a care home", "at the co-op"), so its
    content words are what has to turn up in the line: the rest ("i work in") belongs to the
    sentence, not to the place.
    """
    words = set(content(place))
    if not words:
        # "at the co-op", "at tesco": every content word of the place is short enough that
        # ``content`` drops it, so the written words have to do, less the little ones.
        words = {word.strip(",.!?;:'\"()") for word in str(place).lower().split()}
        words -= PLACE_LITTLE
    if not words:
        return False
    said = {word.strip(",.!?;:'\"()") for word in str(line).lower().split()}
    return words <= (set(content(line)) | said)

PLACE_LITTLE = frozenset("a an the in at on of to for my our their".split())

def _only_the_job(line, job, place=""):
    """Whether the line is the job and nothing else.

    "i work at the hospital" is; "i'm a nurse and my back is killing me" is not, and the thing
    it is about instead is what a "what do i do" after it wants an answer about.

    The place they work counts as the job here: with the role and the place kept apart, a line
    that gave the place ("i work at mcdonalds") carries a word of neither the role nor the work
    vocabulary, and it is still only about the job.
    """
    # A job said with the one it replaces in the same breath - "im a teacher not a nurse" - is
    # still a line about the job, so the part that takes the old one back is cut off first.
    line = extract.TAKE_BACK_SPLIT.split(str(line), 1)[0]
    left = {word.strip(",.!?;:'\"()") for word in
            " ".join(str(line).lower().split()).split()}
    left.discard("")
    mine = set()
    for word in str(job).lower().split():
        mine.add(word)
        mine |= {form.lower() for form in forms(word)}
    mine |= {word.lower() for word in content(str(job))}
    for word in str(place or "").lower().split():
        mine.add(word)
        mine |= {form.lower() for form in forms(word)}
    mine |= {word.lower() for word in content(str(place or ""))}
    return all(word in JOB_ONLY or word in mine for word in left)

TALKED_ABOUT = re.compile(
    r"\bwhat (?:did|have|had) we (?:talk|talked|chat|chatted|speak|spoken|discuss|discussed)"
    r" about\b|\bwhat (?:did|have|had) we (?:cover|covered|discuss|discussed|talk about)\b|"
    # "talk me through what we said", "run me through what we covered": the same ask in the
    # words people use when they want the last few turns back, so it is not a hollow ack.
    r"\b(?:talk|walk|run|take) (?:me )?through (?:what|everything) (?:we|i) (?:said|covered|talked)"
    r"\b|\bwhere (?:did|have) we (?:get to|got to|left it|ended up)\b")

SUMMARY_WORD = re.compile(r"\b(?:summar\w+|sum up|recap|rundown)\b|\bsummary\b")

CHAT_WORD = re.compile(r"\b(?:chat|conversation|talk(?:ed|ing)?|we|us|it all)\b")

SUMMARY_ASK_FILLER = re.compile(
    r"\b(?:can|could|would|will|you|u|please|pls|give|me|us|a|an|the|quick|brief|short|just|"
    r"and|so|then|again|now|ok|okay|of|it|all|that|this|our|your|chat|conversation|talk|we|"
    r"so far|today|everything|sum|up|for|to|on)\b")

def _summary_ask(low):
    """True for a line that asks for a summary or a recap of this conversation.

    Two shapes count: it points at the conversation ("summarise our chat", "what did we talk
    about", "a summary of what we said"), or it is the bare ask and nothing else ("summary?",
    "give me a quick recap"). "summarise this email for me" and "summarise the news" are
    requests about something else, and answering those with the person's own facts would be a
    non-answer.
    """
    line = str(low or "")
    if TALKED_ABOUT.search(line):
        return True
    if not SUMMARY_WORD.search(line):
        return False
    if CHAT_WORD.search(line):
        return True
    return not SUMMARY_ASK_FILLER.sub(" ", SUMMARY_WORD.sub(" ", line)).split()

THING_AGAIN = re.compile(
    r"^(?:and |so |but |also )?(?:what was|whats|what is|what's) the ([a-z]{3,})(?: again)?\??$")

WHICH_WAS = re.compile(
    r"^(?:and |so |but |also |oh |ok |okay )?which ([a-z][a-z' ]{2,24}?)\s*"
    r"(?:was it|is it|was that|did i say|did i tell you)\s*[?.!]*$")

ATTRIBUTE_SAID = re.compile(
    r"^(?:and |so |but |also |oh |ok |okay )?what (?:day|date|time|size|colour|color|number|"
    r"price|cost|amount|brand|make|model|year|month) (?:did i|have i) "
    r"(?:just )?(?:say|tell you|mention)\b")

NOT_A_THING_NAMED = frozenset(('one', 'thing', 'things', 'bit', 'bits', 'part', 'parts',
                              'point', 'way', 'kind', 'sort', 'time', 'other', 'else'))

def _an_attribute_they_gave(low):
    """True for "what day did i say it was due": the ask with the attribute in front of it.

    The words after the verb are what the line is looked for by ("it was due" -> "due"), so an
    attribute ask with nothing after the verb is not this shape: "and what size did i say" has
    no word to find a line by, and the attribute words themselves ("size") are not in the line
    that gives it ("in a medium"). That one keeps the reply it had.
    """
    if not ATTRIBUTE_SAID.match(low or ""):
        return False
    after = re.search(r"\b(?:say|said|tell you|told you|mention|mentioned)\b(.*)$", low)
    return bool(after and content(after.group(1)))

ATTRIBUTE_KIND = re.compile(
    r"^(?:and |so |but |also |oh |ok |okay )?(?:what|which)\s+([a-z][a-z' ]{1,24}?)\s+"
    r"(?:did i|have i|was it i|is it i|was that i)\s+(?:just )?"
    r"(?:say|said|tell you|told you|mention|mentioned)\b")

NOT_A_KIND = frozenset(('i', 'you', 'it', 'that', 'this', 'the', 'a', 'an', 'my', 'your', 'we',
                        'they', 'he', 'she', 'was', 'is', 'much', 'many', 'long', 'often', 'else',
                        'other', 'time', 'thing', 'one', 'day', 'now', 'then', 'about'))

def _an_open_attribute_ask(low, memory):
    """The line that answers "what subject did i say i was revising", or "" when none does.

    A line has to be found for this to hold, so a question about the world keeps its reply. The
    clause after the verb decides the line; the kind's words are the fallback for an ask that
    stops at the verb. The best line wins, so "shift pattern" finds the line that says "shifts".
    """
    part = ATTRIBUTE_KIND.match(low or "")
    if not part:
        return ""
    kind = " ".join(part.group(1).split())
    if not kind or kind.split()[0] in NOT_A_KIND or len(kind.split()) > 3:
        return ""
    after = re.search(r"\b(?:say|said|tell you|told you|mention|mentioned)\b(.*)$", low)
    words = content(after.group(1)) if after else set()
    words = {word for word in (words or content(kind)) if len(word) > 2}
    if not words:
        return ""
    best, score = "", 0
    for turn in _every_line(memory):
        line = turn.get("user") or ""
        if not line or _asks(line):
            continue
        seen = _seen(line)
        found = sum(1 for word in words if _alike(word, seen))
        # The later line wins a tie: it is the one with the name in it, which is what was asked.
        if found and found >= score:
            best, score = line, found
    return _recall_quote(best, memory) if best else ""

def _which_thing_was_it(low, memory):
    """The thing in "and which knee was it", when they named it themselves earlier in the chat.

    Only a thing they said in one of their own lines is a recall: "which knee was it" before
    anything about a knee is a question about the world, and the answer to it is not a line of
    theirs, so this hands that line on untouched.
    """
    part = WHICH_WAS.match(low or "")
    if not part:
        return None
    thing = " ".join(part.group(1).split())
    if thing in NOT_A_THING_NAMED or not content(thing):
        return None
    if not _said_word(thing, memory):
        return None
    return thing

# The phrases that say *when* rather than *what*. "my laptop fan is loud all the time now" is a
# line about the fan: the "time" in it is how long for, not a thing they told the store about.
# Read as a thing, though, it made a bare "whats the time" a recall of that line, and the store
# answered the clock with the person's own words ("You said: \"my laptop fan is loud all the
# time now\"") while the clock was right there to be said. The same shape is in "its loud all
# day", "most of the time", "at the time" and "right now", so the phrases go before the word is
# looked for, and never the other way round.
A_WHEN = re.compile(
    r"\b(?:all|most|some|any|each|every|next|last|this|that|another|half|plenty\s+of|lots\s+of|"
    r"a\s+(?:long|short|little|bit\s+of|lot\s+of)|the\s+whole|the\s+entire)\s+(?:the\s+)?time\b"
    r"|\b(?:at|in|on|before|after|by|of)\s+the\s+time\b"
    r"|\btime\s+(?:to|for)\b"
    r"|\b(?:all|most|some|any|each|every|the\s+whole|these|those)\s+"
    r"(?:day|days|night|nights|week|weeks|month|months|year|years|morning|evening|afternoon)\b"
    r"|\b(?:right|just)\s+now\b")


def _without_the_when(line):
    """The line with the phrases that say when taken out, so "all the time" is not "the time"."""
    return A_WHEN.sub(" ", line)


# "what time is it", "have you got the time": the clock, asked in the words people use for it.
# The "it" in them points at nothing the chat has said, so a detail reader that leans on a
# pointing word is reading a referent that is not there.
A_CLOCK_ASK = re.compile(
    r"^(?:and |so |but |oh |right |ok |okay |hi |hello |sorry )*"
    r"(?:(?:whats|what's|what is|whats?) the time"
    r"|what\s+time\s+is\s+it"
    r"|(?:have|has|do|did)\s+(?:you|u)\s+(?:got|have|know)\s+the\s+time"
    r"|(?:got|know)\s+the\s+time)\b")


def _a_clock_ask(line):
    """True for a line that asks what the clock says."""
    return bool(A_CLOCK_ASK.match(str(line or "").strip().lower()))


def _said_word(word, memory):
    """Whether the person named this word, or one of its forms, in one of their last lines.

    A word inside a phrase that says when does not name anything: "all the time" is how long
    the fan has been loud, not something they told the store about the time of day. And a
    question they asked is not a thing they named: "what time is it" then "whats the time" is
    the same ask twice, and reading the first one as the thing the second is about handed the
    fan line back under "You said: ...". This is the rule the rest of the store already
    follows - an ask is kept as the question it was, never as the fact.
    """
    mine = forms(word)
    for turn in recent(memory, 8):
        said = str(turn.get("user") or "")
        if not said.strip() or _asks(said):
            continue
        line = _without_the_when(said)
        if not line.strip():
            continue
        if any(mine & forms(seen) for seen in content(line)):
            return True
    return False

def _recall_in_progress(memory):
    """True when the last turn was the bot answering a question about the conversation."""
    if not isinstance(memory, dict):
        return False
    before = " ".join((last_user(memory) or "").lower().split())
    # A question about how the chat went ("what did I ask you first?") tells us nothing about
    # the person's job: "so what do I do?" after it is a request for help, not a job recall.
    if before and (FIRST_ASK.search(before) or SAID_ASK.search(before)
                   or _repeat_ask(before, before)):
        return False
    if last_module(memory) == "memory_store":
        return True
    return bool(before) and _about_this_chat(before)

def _elided_ask(text, memory, low=""):
    """(which fact an ask that leaves the fact out is about, whether that was a guess).

    "what did I say it was again?" after "what's my budget?" asks about the budget, and nothing
    else in the line may name a thing of its own. When no recall has been answered yet, the
    fact they mean is the one they just told me, and that is a guess: a miss on it would say
    they never said something they did, so the caller lets another module answer instead.
    """
    if not isinstance(memory, dict):
        return "", False
    line = " ".join(str(low or text or "").lower().split()).strip(" .,!?;:-")
    if not line or set(line.split()) - ELIDED_WORDS:
        return "", False
    raw = " ".join(str(text or "").lower().split())
    # The asking word is the one the folded line drops, and two of the shapes in ELIDED_ASK are
    # a recall only because of it: "what was it again" folds to "what was it", which is a question
    # about the thing and not about the conversation. So the raw line is tried as well as the
    # folded one - it is where "again" still is.
    if not (ELIDED_ASK.search(line) or ELIDED_ASK.search(raw)
            or (ELIDED_AGAIN.search(line) and "again" in raw)):
        return "", False
    turns = memory.get("turns") or []
    named = _named_slots(line)
    # The fact they just told me wins: "we have a dog called Biscuit" then "what did I call
    # him?" is about the dog, not about whatever was asked two turns ago.
    # "call" fits a pet as well as a name: "we have a dog called Biscuit" then "what did I call
    # him?" is about the dog.
    fits = named | {"name", "pets"} if {"name", "pets"} & named else named
    stated = _stated_slot(memory, turns)
    if stated and (not named or stated in fits):
        return stated, True
    # One line back: a question in between ("weve got a cat called Milo" / "is he any trouble?"
    # / "what did i call him again?") still leaves them asking about the fact they told me.
    stated = _stated_slot(memory, turns, back=2)
    if stated and (not named or stated in fits):
        return stated, True
    asked = memory.get("asked")
    if isinstance(asked, dict) and asked.get("slot"):
        try:
            asked_turn = int(asked.get("turn") or 0)
        except (TypeError, ValueError):
            asked_turn = None
        slot = str(asked["slot"])
        if asked_turn is not None and len(turns) - asked_turn <= 2 and (not named or slot in fits):
            return slot, False
    return "", False

def _named_slots(line):
    """The facts an elided ask names in its own words (empty when it names none)."""
    return {slot for slot, pattern in ELIDED_NAMES if pattern.search(str(line or ""))}

def _stated_slot(memory, turns, back=1):
    """The one fact the last thing the person said gave ("" when it gave none or several).

    Only the last line counts: "what did I call him" right after "we have a dog called Biscuit"
    is about the dog, and an allergy three lines earlier must not answer it. `back` reaches one
    line further, for a question between the fact and the ask ("weve got a rescue dog called
    Biscuit" / "what should i feed him?" / "what did i call him again?"): a line that gave no
    fact is walked past only when that line was a question, and two facts on one line still
    mean no guess at all.
    """
    user_lines = [turn for turn in list(turns or []) if isinstance(turn, dict)]
    window = list(reversed(user_lines[-max(1, int(back)):]))
    for offset, turn in enumerate(window):
        said = turn.get("user") or turn.get("text") or ""
        if not isinstance(said, str) or not said.strip():
            continue
        # One line back is for a question in between, never for any line: a line that gave a
        # fact this cannot name (a plan, a job) is not walked past, or "im allergic to nuts" /
        # "im going to spain in june" / "what did i say it was again?" would be answered with
        # the allergy rather than the plan they said last.
        if offset == 0 and int(back) > 1 and not _asks(said):
            return ""
        found = extract.extract(said, question=False)
        # `job` is left out on purpose: the job frame cannot yet say "work in a warehouse"
        # ("You told me you're a warehouse", #1123), and a quote of their line is better than a
        # broken sentence.
        kinds = [slot for key, slot in (
            ("name", "name"), ("city", "city"), ("age", "age"),
            ("budget", "budget"), ("allergies", "allergy"), ("pets", "pets")) if found.get(key)]
        if len(kinds) > 1:
            return ""
        if kinds:
            return kinds[0]
    return ""

def _remember_asked(memory, slot):
    """Keep the fact this answer was about, so the next elided ask is about the same one."""
    if not isinstance(memory, dict) or not slot:
        return
    memory["asked"] = {"slot": slot, "turn": len(memory.get("turns") or [])}

def _the_case_they_just_gave(text, memory):
    """The consequence of the last answer the short line just chose, said as the reply.

    "should i get a cat or a dog" -> "A cat is the kinder choice if you're out all day" ->
    "i work all day". The answer has already said what that means, so the reply is the choice it
    offered, with their case named - not "Got it - you work all day", which throws it away.
    """
    clean = " ".join(str(text or "").split())
    if not clean or "?" in clean:
        return None
    if _asks(clean):
        # A line that opens with an ask word is a question without the question mark, and it is
        # not a case they gave: "what did i say she is allergic to" after an answer was read as
        # one, and the reply said their own question back with the answer's tail on it.
        return None
    if last_module(memory) not in ADVICE_MODULES:
        return None
    said = str(last_bot(memory) or "").strip()
    if not said:
        return None
    consequence = condition.chosen(clean, said)
    if not consequence:
        if not condition.refused(clean, said):
            return None
        # The answer tested the number this line gives and their number fails the test, so the
        # answer's own verdict is not theirs: "is it worth fixing my old laptop" / "its 8 years
        # old" was answered "Repair it, then." by an answer that only repairs under five. Hand
        # the fact back and stop - the answer already said what it says for both cases it
        # named, and saying it again is worse than saying nothing more.
        gave = ack.said_back(clean, memory).strip(" .")
        return gave[:1].upper() + gave[1:] + "." if gave else None
    case = ack.said_back(clean, memory)
    if not case:
        return None
    body = consequence.strip(" ,;:-\u2014.")
    if not body:
        return None
    body = body[0].upper() + body[1:]
    # Their case first, then the choice the answer offered for it: saying the choice first reads
    # as a verdict out of nowhere.
    line = "%s. %s, then." % (case.strip(" .").capitalize(), body)
    if _same_as_last(line, memory):
        return None
    return line

COUNT_IN_AN_ANSWER = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|both|couple|pair)\b", re.I)

def _said_another_way(reply):
    """The same fact in a second wording, or None when there is no plain one."""
    text = str(reply or "").strip()
    match = re.match(r"^(?:Your|My) (name|job|budget) is (.+)$", text)
    if match:
        slot, value = match.group(1), match.group(2).rstrip(".")
        if slot == "budget":
            return "You said " + value + "."
        if slot == "name":
            return "I have you as " + value + "."
        if slot == "job":
            return "You told me it is " + value + "."
    match = re.match(r"^You told me you(?:'re| are) (.+)$", text)
    if match:
        return "You said you're " + match.group(1).rstrip(".") + "."
    match = re.match(r"^You've got (.+)$", text)
    if match:
        animals = match.group(1).rstrip(".")
        if animals.count("called") > 1:
            return None  # more than one name: no plain short way to say it
        named = re.search(r"\bcalled (.+)$", animals)
        if named:
            # "what's my dog called?" then "and what did I call him?" is the same name twice.
            return "Still called " + named.group(1) + "."
        if not COUNT_IN_AN_ANSWER.search(animals):
            # "You've got a cat." asked again is not "Still a cat.": with the number left off,
            # "still a cat" reads as "a cat and not a dog", which is another claim and no answer
            # to "how many". One animal has no plain second wording, so the plain one stands, as
            # it does for two names above.
            return None
        return "Still " + animals + "."
    match = re.match(r"^You (?:live|'re|are)(?: in| from)? (.+)$", text)
    if match:
        return "You said " + match.group(1).rstrip(".") + "."
    return None

def _slot_words(slot, memory=None):
    """The plain ask for a fact slot, so one set of patterns answers every ask."""
    if slot == "pets" and isinstance(memory, dict):
        pets = [p for p in (user(memory).get("pets") or []) if isinstance(p, dict)]
        animals = [str(p.get("animal") or "") for p in pets]
        if animals and animals.count(animals[-1]) == 1:
            return "what is my " + animals[-1] + " called"
    return {
        "name": "what is my name",
        "age": "how old am i",
        "job": "what is my job",
        "city": "which city do i live in",
        "budget": "what is my budget",
        "allergy": "what am i allergic to",
        "pets": "what are my pets called",
    }.get(slot, "what have i told you")

def _slot_of(low):
    """The fact a recall reply was about, from the plain ask that was answered."""
    for slot, pattern in (
            ("allergy", r"\ballerg"),
            ("car", r"\bwhat (?:do|did) i drive\b|\bcar\b"),
            ("budget", r"\bbudget"),
            ("pets", r"\b(?:dog|cat|pet)s?\b"),
            ("job", r"\bmy (?:job|work)\b|\bwhat do i do\b|\bwhere do i work\b"),
            ("city", r"\b(?:city|place|country)\b|\bwhere do i (?:live|come from)\b"),
            ("name", r"\bmy name\b|\bwho am i\b")):
        if re.search(pattern, low):
            return slot
    return ""

BARE_MINE = re.compile(
    r"^(?:and |so |ok |okay |but |well |also |what about |how about |again )*"
    r"(?:my|our)\s+([a-z][a-z' -]{0,24}?)$")

SLOT_NOUNS = {
    "name": frozenset("name".split()),
    "job": frozenset("job work".split()),
    "city": frozenset("city place town".split()),
    "budget": frozenset("budget".split()),
    "allergy": frozenset("allergy allergies allergen".split()),
    "pets": frozenset("pet pets dog dogs cat cats animal animals".split()),
    "age": frozenset("age".split()),
}

SLOT_FILLER = frozenset("""again now then please too as before though tho also still anyway
i told you said say remember""".split())

def _slot_named_in(low):
    """The fact a line that only names it asks for, from the fact's own words."""
    for slot, pattern in BARE_SLOTS:
        if re.search(pattern, str(low or "")):
            return slot
    return ""

def _slot_held(slot, memory):
    """Whether the store has a fact of theirs for this slot."""
    keys = SLOT_KEY.get(slot)
    if not keys:
        return False
    known = user(memory) or {}
    return any(known.get(key) for key in keys)

def _bare_ask_naming_a_fact(low, memory):
    """The slot a line that only names one of their facts is asking for, or ""."""
    found = BARE_MINE.match(str(low or "").strip(" .!?;,"))
    if not found:
        return ""
    words = set(found.group(1).split())
    slot = _slot_named_in("my " + found.group(1))
    if not slot or not _slot_held(slot, memory):
        return ""
    if words - SLOT_NOUNS.get(slot, frozenset()) - SLOT_FILLER:
        return ""  # the line says something about the fact, so it is not only naming it
    if slot == "pets":
        # "my cat?" is about a cat, so a store that only holds a dog has nothing to say to it -
        # the answer would be about the dog they did tell us about.
        named = words - SLOT_FILLER - {"pet", "pets", "animal", "animals"}
        held = set()
        for pet in (user(memory) or {}).get("pets") or []:
            if isinstance(pet, dict):
                held |= forms(str(pet.get("animal") or ""))
        if named and not any(forms(one) & held for one in named):
            return ""
    return slot

PLACES_ASK = re.compile(
    r"\b(?:which|what) (?:city|place|country|town)\b"
    # The words people use for a place without naming a city: "what area do i live in", "what
    # part of the country do i live in". These are only a place ask when the line goes on to ask
    # about the person, so "what area of my flat needs painting" is not one.
    r"|\b(?:which|what) (?:area|suburb|neighbourhood|neighborhood|county|village|"
    r"part of (?:the|this) country) (?:of (?:the|this) (?:country|city|town) )?"
    r"(?:do|does|did|am|was|are|were) (?:i|we)\b"
    r"|\b" + WHERE_ASK + r" (?:am|was) i (?:going|from|living)\b(?! with\b)|"
    r"\bmy hometown\b|\b" + WHERE_ASK + r" am i from originally\b|"
    r"\b" + WHERE_ASK + r" (?:was|were) (?:i|we) born\b|\b" + WHERE_ASK + r" are (?:i|we) from\b|"
    r"\b" + WHERE_ASK + r" do (?:i|we) (?:live|come from)\b|\b" + WHERE_ASK + r" are we "
    r"(?:living|based)\b|"
    r"\b" + WHERE_ASK + r" (?:do|does) my \w+ (?:live|come from)\b|"
    r"\b" + WHERE_ASK + r" is my \w+ (?:living|based)\b|"
    # Where they grew up is a place ask, whether it is said with "from" or with the growing up:
    # "where did i grow up" is answered by the place the line gave ("i grew up in dublin"), which
    # the extractor files as where they are from.
    r"\bwhere (?:did|do|does) (?:i|we) (?:grow|grew|grown) up\b|"
    r"\bwhere (?:was|were) (?:i|we) (?:raised|brought up|brung up)\b|"
    r"\bwhere did (?:i|we) (?:live|grow up) (?:before|originally|as a kid|as a child|growing up)\b|"
    # The move said as a move: "where did i move from" asks the same fact as "where am i from",
    # and it was answered with a search hedge. It is asked this way after "i moved to preston
    # last year" - the line names only the destination, so the origin is the question.
    r"\bwhere (?:did|do|does) (?:i|we) (?:move|moved) (?:here |over |away )?from\b|"
    # And the move named with the destination in the question: "which town did i move from".
    r"\b(?:which|what) (?:city|town|place|county|country) did (?:i|we) move (?:from|away from)\b")

SELF_WORD = re.compile(r"\b(?:i|i'm|im|i've|ive|i'd|id|me|my|mine|we|we're|us|our|ours)\b")

PLACE_ADVICE = re.compile(
    r"\b(?:should|shall|recommend\w*|worth|visit\w*)\b"
    r"|\bbest (?:place|city|country|town|part)\b")

PLACE_RECALLED = re.compile(
    r"\b(?:did i (?:say|tell|mention)|i (?:said|mentioned|told)|remember|again)\b")

GROWN_UP_ASK = re.compile(
    r"\b(?:grow|grew|grown) up\b|\b(?:raised|brought up|brung up)\b"
    r"|\bwhere (?:i|we) (?:lived|was living|were living)\b")

FEELING_ALONE = re.compile(
    r"^(?:and |but |so |also |honestly |yeah |yes |god |oh |well |still |im |i'm |i am |i feel"
    r"|i just feel |feel |im just |im getting |getting |a bit |really |very |quite |so )*"
    r"(scared|nervous|worried|anxious|terrified|petrified|frightened|panicking|dreading|dreading it)"
    r"(?: (?:about it|of it|about that|about this|about the whole thing|now|today|already"
    r"|honestly|a lot|so much|quite a lot|tbh|tbf|again|about it now"
    r"|for (?:him|her|them|it|us|you)))?$", re.I)

COMING_UP = re.compile(
    r"\b(?:tomorrow|tonight|later today|this (?:morning|afternoon|evening|week|weekend|month)"
    r"|next (?:week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday|weekend)"
    r"|on (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    r"|at the weekend|in (?:january|february|march|april|may|june|july|august|september|october"
    r"|november|december)|soon|in a (?:few|couple of) (?:days|weeks))\b", re.I)

A_DAY = re.compile(
    r"\b(?:tomorrow|tonight|later today|this (?:morning|afternoon|evening|weekend)"
    r"|next (?:week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|weekend)"
    r"|on (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|at the weekend)\b", re.I)

def _is_a_question(previous):
    if previous.rstrip().endswith("?"):
        return True
    try:
        return understand(previous).get("kind") == "question"
    except Exception:  # noqa: BLE001 - an unreadable line is not this rule's business
        return True

TREATMENT = re.compile(
    r"\b(?:chemo|chemotherapy|radiotherapy|radiation therapy|dialysis|biopsy|palliative|hospice"
    r"|terminally ill)\b", re.I)

A_PERSON_IN_TROUBLE = re.compile(
    r"\b(?:my|our)\s+(?:" + KIN + r")\b(?:'s|s)?[^.?!]*?\b(?:" + BAD_NEWS + r")\b", re.I)

WHO_IS_IN_TROUBLE = re.compile(r"\b(?:my|our)\s+((?:" + KIN + r"))\b", re.I)

SHE = frozenset("""mum mom mother daughter wife sister gran granny nan nana grandma grandmother
                   aunt niece stepdaughter""".split())

HE = frozenset("""dad father son husband brother grandad grandpa grandfather uncle nephew
                  stepson""".split())

def _again(who):
    """The word for the person in the rest of the reply: "her", "him" or "them"."""
    word = str(who or "").lower()
    if word in SHE:
        return "her"
    if word in HE:
        return "him"
    return "them"

def _the_thing_before_the_feelings(memory):
    """The last line they said that was not itself a bare feeling.

    "im nervous", "im scared", "im terrified" in a row are all about the one thing said before
    them, so each of them looks past the feelings in between. Reading the feelings as news would
    make the second and third fall back to the general worry line.
    """
    seen = 0
    for turn in reversed((memory.get("turns") or [])[-6:]):
        if not isinstance(turn, dict):
            break
        line = str(turn.get("user") or "").strip()
        if not line:
            continue
        if FEELING_ALONE.match(line.lower().rstrip("!.,")):
            continue
        seen += 1
        if seen > 1:
            # Only the nearest real thing they said is the subject: two feelings about two
            # different things belong to the nearest one.
            break
        return line
    return ""

def _a_feeling_about_what_they_said(memory, low):
    """The thing they just told us, said back, when the whole line is how they feel about it."""
    match = FEELING_ALONE.match(str(low or "").strip().rstrip("!.,"))
    if not match:
        return None
    previous = _the_thing_before_the_feelings(memory)
    if not previous or len(previous.split()) < 4:
        return None
    if _is_a_question(previous):
        return None
    if TREATMENT.search(previous):
        return None
    if not re.search(r"\b(?:i|we|my|our|me)\b|\bim\b|\bive\b", previous.lower()):
        return None
    trouble = A_PERSON_IN_TROUBLE.search(previous)
    if not (COMING_UP.search(previous) or trouble):
        return None
    if trouble:
        # The person is named in the reply itself, so the news is not read back on top of them:
        # "Scared for your dad is one of the heaviest things to carry" is a friend's line, and
        # "Your dad is in hospital. ..." in front of it is the machine reading their own news.
        who = WHO_IS_IN_TROUBLE.search(previous)
        if who:
            # A body already said stays out: two fears in a row about the same person should not
            # read as one line twice.
            recent = " ".join(str(t.get("bot") or "") for t in (memory.get("turns") or [])[-5:]
                              if isinstance(t, dict))
            # The person's own word for them wins over what the kin word usually means: "im
            # scared for him" about a friend is a him, and the reply must not say "them".
            said_for = re.search(r"\b(?:for|about)\s+(him|her|them)\b", str(low or ""), re.I)
            again = _again(who.group(1))
            if said_for:
                theirs = said_for.group(1).lower()
                # ... but only where the kin word cannot tell. "my brother is in hospital / im
                # scared for her" is two people in one sentence - "frightened for your brother
                # does not make you any less help to her" - and the word that names the person
                # in the line before is the one the reply is about, so a kin word that already
                # says which it is keeps its own word and their pronoun is the slip.
                if again == "them" or theirs == again:
                    again = theirs
            said_bodies = [body.format(who="your " + who.group(1).lower(), again=again)
                           for body in (
                "That is a lot to be carrying, and being frightened for {who} does not make you "
                "any less help to {again}.",
                "It is all right to be frightened for {who}. You do not have to be the calm one "
                "all the time.",
                "Scared for {who} is one of the heaviest things to carry, and you are allowed to "
                "say so.",
                "Being frightened for {who} is the honest reaction, and saying it out loud once "
                "usually takes some of the weight off.",
            )]
            fresh = [body for body in said_bodies if body not in recent] or said_bodies
            # A seed off the person as well as the turn, so two chats about two different
            # people do not open with the same sentence.
            seed = len(memory.get("turns") or []) + sum(map(ord, who.group(1)))
            return random.Random(seed).choice(fresh)
    said = thread.restate(previous)
    if not said or len(said.split()) < 3:
        return None
    said = said[0].upper() + said[1:]
    feeling = match.group(1).lower()
    if feeling in ("worried", "anxious"):
        bodies = ["That is a fair thing to have on your mind, and most of it is the not-knowing.",
                  "Worrying about it makes sense. Is there one thing you could check that would "
                  "settle it?",
                  "That kind of worry is tiring to carry, and saying the worst version out loud "
                  "usually shrinks it.",
                  "Worry about something coming up is the mind rehearsing it. Is there one thing "
                  "you could check that would settle it?"]
    elif A_DAY.search(previous):
        bodies = ["Nerves before something like that are normal, and it is usually worse in the "
                  "days before than on the day.",
                  "Of course you are - most of it is the not-knowing. What is the first thing that "
                  "happens?",
                  "That is a fair thing to be nervous about. Tell me the part of it that keeps "
                  "coming back.",
                  "That is a nervous-making thing to have coming, and it says nothing bad about "
                  "how ready you are.",
                  "Nerves are usually worse in the days before than on the day. What is the first "
                  "thing that happens?"]
    else:
        bodies = ["That is a fair thing to be nervous about, and it is all right to say so.",
                  "Nerves about it make sense, and naming the worst version out loud usually "
                  "shrinks it.",
                  "That is a lot to be carrying around. Is there one part of it you could start "
                  "on?",
                  "Saying the thing you dread out loud is usually the worst part of it, and the "
                  "rest is smaller than it looks.",
                  "Most of the nerves is the not-knowing. What is the part that keeps coming "
                  "back?"]
    # The bot may have just said the thing itself ("Noted: you are going to spain in june"), and
    # reading their own news back to them twice is the machine talking. The body carries the
    # reply on its own; the sentence is only there when it is new.
    # A body that was already said stays out even when the sentence in front of it was not the
    # same: two feels in a row should not read as one line with a different lead.
    recent = " ".join(str(t.get("bot") or "") for t in (memory.get("turns") or [])[-5:]
                      if isinstance(t, dict))
    body = _vary([b for b in bodies if b[:40] not in recent] or bodies, memory)
    if any(_said_back_already(str(turn.get("bot") or ""), said)
           for turn in (memory.get("turns") or [])[-2:] if isinstance(turn, dict)):
        # The sentence is left off because the bot has just said the news ("Noted: you have a
        # scan at the hospital on friday"), so any body that opens by pointing at a sentence
        # which is not there has nothing to point at: "Of course you are" answers a "scared"
        # nobody said, and "That is a nervous-making thing" names a thing with no antecedent.
        standing = [b for b in bodies if not OPENS_ON_THE_SENTENCE.match(b)]
        return _vary([b for b in standing if b[:40] not in recent] or standing or bodies, memory)
    return said + ". " + body

OPENS_ON_THE_SENTENCE = re.compile(
    r"^(?:of course|of course you are|that\b|this\b|those\b|these\b|such\b"
    r"|(?:nerves|worry|worrying|fear|stress|panic) about it\b)", re.I)

def _said_back_already(reply, said):
    """True when a bot line already carried this sentence's own subjects.

    The last two lines, not one: `im so nervous` / `im scared` / `im terrified` about the same
    test gives a body with no sentence in front of it on the second, so the third looked at
    the line just above, saw a body, and read the test back a second time.
    """
    words = {w for w in keywords(said) if len(w) > 3}
    if not words:
        return False
    return len(words & {w for w in keywords(reply) if len(w) > 3}) >= max(2, len(words) - 1)

ANSWER_MODULES = frozenset(("answers", "memory_store"))

def _the_bot_name(memory, low):
    """The name they gave the bot, said back when they ask for it, or None.

    Nothing here without a name on file: a chat where the person never named the bot keeps the
    reply it already had ("I don't have one - pick something if it helps").
    """
    known = str(user(memory).get("bot_name") or "").strip()
    if not known or not extract.BOT_NAME_ASK.search(low):
        return None
    return pick(["You call me " + known + ".", known + " \u2014 you named me that.",
                 "I'm " + known + ", since you named me."], memory)

def _the_store_reply(text, memory):
    """A recall ask answered about the fact it means, even with the fact left out.

    "what did I call him?" right after "we have a dog called Biscuit" is about the dog, so the
    ask is turned into the plain one the store already answers for that fact. The fact is taken
    from the one the last thing they said gave, or else from the last recall question; the
    second is a guess, and a guess that misses returns None rather than claim they never said
    something they did.
    """
    if asks_what_today_is(text):
        # "what day is it" asks the calendar, and the store has no part of it: the chat it is said
        # in is not the subject. Without this the ask was filled from the thread - the plan on it
        # ("i'm starting my new job on monday") stood in for the value, and its implied question
        # answered a question about today with the dress code for a first day.
        return None
    behind = _behind_a_remembering_frame(text)
    if behind:
        # A remembering frame is not the line: "can you remember the dentist is on tuesday" is a
        # person handing over the appointment. The store answers the thing behind it, and the
        # frame's own yes-only question ("do you remember that i live in leeds") is answered by
        # _remembers_fact first, which is the one reader that needs the frame in front of it.
        remembered = _remembers_fact(text, memory)
        if remembered:
            return remembered
        answered = _the_store_reply(behind, memory)
        if answered:
            return answered
    followed = _the_followed_check(text, memory)
    if followed:
        # "did you get that?" is a question about the conversation, not about the world: the
        # answer is the thing they said, said back, and never a lookup of the last word in it.
        return followed
    closed = _the_close(text, memory)
    if closed:
        # "i just want to forget it" is not the subject asked about again: it is the person
        # closing it, and the answer is short and warm. Read before anything else, because every
        # reader below would answer the subject they have just been asked to leave.
        return closed
    shared = _the_limit_they_share(text, memory)
    if shared:
        # The limit the turn before stated is this person's as well ("im too", "my son is too"):
        # the reading has filed it on them, and the answer says which limit and whose it is, so
        # the person is not left with "Glad to hear it." after telling the bot about an allergy.
        return shared
    # "i had an interview today" / "how did it go" is a question about the person's own day, and
    # the answer is to ask them: the bot was not there. Read before the knowledge reads, because
    # the topic of the line is the thing they just did - "how did it go" after the interview was
    # answered with how to prepare for one, a line after they said it was over
    # (bot/memory/thread.went).
    how_it_went = thread.went(text, memory)
    if how_it_went:
        return how_it_went
    timed = _the_time_they_said(text, memory)
    if timed:
        # "what time do i get up" is about the time they told us, not about sleep in general.
        return timed
    took = memory.pop("pet_age", None) if isinstance(memory, dict) else None
    if isinstance(took, dict) and isinstance(took.get("age"), int):
        # The bot asked how old their animal was and this line was the answer: say it back.
        return "Noted: " + _pet_named(took) + " is " + _a_pet_age(took) + "."
    call = _the_call_from_the_advice(text, memory)
    if call:
        # "should i keep running?" after an answer that said how to go on with a change: the
        # chat has already settled it, so the store answers with that answer's own limit.
        return call
    given = extract.bot_name(text)
    if given:
        # A name for the bot is theirs to give, and the store keeps it (facts.bot_name files it as
        # `bot_name`), so the next "whats your name" agrees with this line instead of saying it has
        # no name at all. The confirmation is the turn's news; nothing else in the line to answer.
        return pick([given + " it is \u2014 I'll answer to that.",
                     given + " \u2014 noted, I'll answer to it.",
                     "I'll be " + given + " then."], memory)
    settled = choose.the_decision(text, memory)
    if settled:
        # "what did i decide to get" names nothing, so nothing could answer it: the thing is in
        # the line where they changed their mind ("im thinking of getting a cat" / "actually a
        # dog"), and the store is the only part of the bot that keeps that line.
        return settled
    budget = _the_budget_on_the_answer(text, memory)
    if budget:
        # "and i only get 20 minutes" after a lunch answer is the room that answer has, not a new
        # question about 20 minutes. Left to itself the knowledge base answered it as one and the
        # subject left the lunch: the eggs came back as the fastest dinner there is.
        return budget
    made = _the_amount_they_made(text, memory)
    if made:
        # "i only made 200g" after an answer that worked a total out for four: the person is saying
        # they are short, and "5 minutes" was the answers module reading the weight as a question
        # about how long to cook it.
        return made
    fed = _the_people_that_size_feeds(text, memory)
    if fed:
        # "is that enough for 6" while holding the joint: the portion the cooking know-how keeps
        # turns the size in hand into a number of people, which is the question. Left to itself
        # the turn was the same roast paragraph again behind "Same as before".
        return fed
    sized = _the_figure_for_the_size_they_named(text, memory)
    if sized:
        # "how long do i roast a chicken" then "its 2kg" is the size the answer was waiting for:
        # the roast entry works its rate out for the size in the line, and the answer already did
        # the arithmetic for exactly this size ("so a 2kg bird takes roughly 1 hour 40 minutes").
        # The store said "Thanks for telling me - I'm here if you want to dig into any of that",
        # which is an acknowledgement of the one thing in the chat that has a figure in it.
        return sized
    folded = _folded(text, memory)
    low = _bare(folded)
    undeclared = _the_person_still_in_hand(low, memory)
    if undeclared:
        # "can he have cheese" then "what about milk": one more food asked about the same person,
        # with the person left out. The chat has just answered that ask, so the person in hand is
        # the one the question is about - and with no person named, the knowledge entry for milk
        # answered it with the baby feeding schedule.
        one_more = _other_person_reply(memory, low)
        if one_more:
            return one_more
    named_back = _the_bot_name(memory, low)
    if named_back:
        return named_back
    names = _the_names_again(folded, low, memory)
    if names:
        # "what are they called again?" names the pets the store is holding, so the names it kept
        # are the answer.
        return names
    counted = how_many.answer(low, memory)
    if counted:
        # "how many brothers do i have" a turn after "i have three brothers": the number is the
        # answer, and the store holds it. Animals and children are answered by the readers below.
        return counted
    same = _the_same_fact_about_someone(text, memory)
    if same:
        # "and my wife is too" after "im allergic to nuts": the fact comes with them, and it is
        # kept on the person named here because this module is the one answering.
        said, note = same
        if note:
            remember_other(memory, dict(note))
        return said
    # "im scared" right after they told us something coming up is about that thing, so it is
    # said back and answered, not handed a line that would fit any frightening thing.
    about_it = _a_feeling_about_what_they_said(memory, low)
    if about_it:
        return about_it
    kept = _the_fact_just_asked(memory, low)
    if kept:
        # "do you remember it?" right after a recall answer is a question about that fact, not
        # about the bot's memory in general: "whats my name" -> "You're Dave." -> "do you
        # remember it?" is answered by the name, not by "I keep what you tell me here".
        return kept
    slot, guessed = _elided_ask(text, memory, low)
    if slot:
        reply = _respond(_slot_words(slot, memory), memory)
        if not reply or (guessed and ELIDED_NOT_SURE.search(reply)):
            # The fact the guess picked has nothing to say: fall through to the echo below
            # ("You said: \"weve got 2 cats\"") rather than lose the turn to a hedge.
            reply = _respond(text, memory)
            if reply:
                _remember_asked(memory, _slot_of(low))
            return reply
        if _same_as_last(reply, memory):
            # the same sentence twice in a row reads like a machine: say the fact another way.
            return _said_another_way(reply) or reply
        return reply
    taken = _the_case_they_just_gave(text, memory)
    if taken:
        return taken
    named = _bare_ask_naming_a_fact(low, memory)
    if named:
        # "and my job?" names the fact rather than asking for it, so the answer is the same one
        # the plain ask gets. When that answer is a miss there is nothing to say: the line goes
        # to another module rather than to a denial.
        reply = _respond(_slot_words(named, memory), memory)
        if reply and not ELIDED_NOT_SURE.search(reply):
            _remember_asked(memory, named)
            if _same_as_last(reply, memory):
                return _said_another_way(reply) or reply
            return reply
    # "and which knee was it": read before the store's own reply, which answers a line it does
    # not know with the last thing they said ("You said: \"its on the outside of the knee\"").
    part_asked = a_hurting_part.the_part_asked(memory, low)
    if part_asked:
        return part_asked
    reply = _respond(text, memory)
    if not reply:
        # "no i meant the front room" names no fact to move - the thing it swaps is the subject of
        # the ask - so the ask is the one they would have made, and it is answered as the question
        # it is. Only when the store's own correction readers said nothing, so a value is still
        # the store's to put right.
        reply = a_repair.the_thing_they_meant(text, memory)
    if not reply:
        # "but i work long hours" after a question about getting a cat names nothing of its own,
        # so the entries for the cat cannot see it: the choice in hand is carried into the line
        # and asked again, and an answer about something else is refused.
        reply = about_the_choice.the_subject_in_the_condition(text, memory)
    if not reply:
        reply = about_the_choice.the_verdict_in_the_chat(text, memory)
    if not reply:
        # "hows about something cold" after a dessert was offered names no dish, so no entry
        # could reach it: the course the chat is on is carried into the line and the knowledge
        # base is asked the question the person would have made of it.
        reply = about_the_choice.the_quality_in_the_chat(text, memory)
    if not reply:
        # "and no dairy" after a chicken dish takes something out of an answer that never named
        # it, so nothing is left to cut: the dish is carried into the line and the knowledge base
        # is asked again.
        reply = about_the_choice.the_limit_in_the_chat(text, memory)
    if reply:
        _remember_asked(memory, _slot_of(low))
        if _same_as_last(reply, memory):
            # The same sentence twice in a row reads like a machine, whatever the ask was:
            # "how many cats do i have" asked again, or "what pets do i have" and then
            # "how many cats do i have", both land on the same line about the same fact.
            return _said_another_way(reply) or reply
    if not reply:
        # A part of an animal the chat has described is a fact it holds, not a detail the person
        # left out: "hes a labrador, 9 weeks old" then "what breed is he" was asked back, which
        # says the chat was not listening.
        reply = _pet_part_reply(memory, low)
    if not reply:
        # "and which knee was it": the store holds the part and the side it was said with.
        reply = a_hurting_part.the_part_asked(memory, low)
    if not reply:
        # The rate of their own doing, asked back late: "how often was that again" after "i go to
        # the gym twice a week". Read before the detail ask-back, which asks them the question
        # they are asking this store.
        reply = rates_reader.answer(text, memory)
    if not reply:
        reply = _detail_they_left_out(memory, low)
    if not reply:
        # "im knackered" ... "why" ... "the baby": the thing they named is the reason for how
        # they said they were, and the store has plenty to say about a baby and nothing at all
        # about those two words on their own. Read as the sentence it would have been, it is
        # answered - but only after the store's own readers, so a bare thing the store already
        # answers ("the baby" right after "im knackered" is met with a question about it) keeps
        # the line it has.
        reply = a_reason.answer_for(text, memory)
    if not reply:
        reply = _the_part_it_never_said(memory, low)
    return reply

DETAIL_ASKS = (
    (re.compile(r"\bhow much\b|\bwhat did (?:it|that|it all|they) cost\b"
                r"|\bwhat(?:'s|s| is| was)? (?:the |was the )?(?:pay|price|salary)\b"), "money"),
    (re.compile(r"\bhow long (?:did|was)\b|\bhow long did (?:it|that|they)\b"),
     "time"),
    (re.compile(r"\bhow many\b|\bhow often\b"), "count"),
    (re.compile(r"\bwhere (?:is|are|was|were|did)\b|\bwhich (?:hotel|flight|one)\b"), "place"),
    (re.compile(r"\bwhat time\b|\bwhen (?:is|are|was|were|do|did)\b"), "when"),
    # "we moved house last month" / "which area", "i watched a film" / "what was it called":
    # the ask names the shape of the detail, not the thing, so it is still about their news.
    (re.compile(r"\bwhich (?:area|part|place|school|club|team|course|country|city|kind|sort|type"
                r"|one|ones)\b|\bwhat (?:kind|sort|type) of\b"), "which"),
    (re.compile(r"\bwhat (?:was|is|were) (?:it|they|that|he|she) called\b"
                r"|\bwhat(?:'s|s| is) (?:it|he|she|they) called\b|\bwhat was (?:the )?name\b"),
     "called"),
    (re.compile(r"\bhow (?:far|old|big|tall|heavy|long ago)\b"), "measure"),
    (re.compile(r"\bwhat (?:was|is|were) (?:it|that|they|he|she) (?:about|like)\b"
                r"|\bwhat(?:'s|s) it (?:about|like)\b"), "about"),
)

DETAIL_LEAN = re.compile(r"\b(?:it|that|this|they|them|those|we|you|your|he|she|him|her)\b", re.I)

BARE_MEASURE = re.compile(r"\bhow (?:much|many|long|old)\b", re.I)

# A price the answer on the screen already states. "i've got a dentist appointment" then "how
# much is that" was asked back - "You haven't said - how much is that?" - while the answer two
# lines up said "An NHS check-up is £27.40 in England." A detail already given is not a detail
# left out, and asking for it reads as if the chat had not read its own answer.
MONEY_SAID = re.compile(r"£\s?\d|\b\d[\d,.]*\s*(?:pounds?|quid|euros?|dollars?)\b", re.I)

LOOK_BACK_ANSWER = 3


def _the_answer_already_gives(detail, memory):
    """True when the newest answer on the screen states the detail this line asks about.

    Only the price is read. Nearly every answer states a count or a length ("four to five hours",
    "three things to check"), so a guard on those would take away ask backs that are right; a
    price is stated when it is meant, and a line asking for it has its answer already.
    """
    if detail != "money":
        return False
    said = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    for turn in reversed(said[-LOOK_BACK_ANSWER:]):
        if turn.get("module") not in ANSWER_MODULES:
            continue
        reply = " ".join(str(turn.get("bot") or "").split())
        if not reply or reply.rstrip().endswith("?"):
            continue
        return bool(MONEY_SAID.search(reply))
    return False

ASK_OPENER = re.compile(
    r"\A(?:how|what|whats|when|where|which|why|who|whose|is|are|was|were|can|could|should"
    r"|shall|do|does|did|will|would|have|has|am|may|might|any|whose)\b", re.I)

HOW_LONG_IT_TAKES = re.compile(
    r"\bhow long (?:does|do|will|would|is|are|should|can|could)\b[^?]{0,25}?\b(?:take|takes|taking)\b",
    re.I)

WANTING = re.compile(r"\b(?:want|wants|wanting|need|needs|needed|hoping|hope to|planning"
                     r"|plan to|trying to|thinking of|thinking about|would like|i'd like"
                     r"|looking to|saving up|saving for)\b", re.I)

DETAIL_VERBS = frozenset("""
it that this they them those we you your he she him her is are was were did do does
have has had be been cost costs pay paid take taken took last lasted stay staying
go going went get got buy bought end give given much long many where when what time
whats salary price a an the and but so to for in on at of from with about then again
there here
""".split())

DETAIL_KNOWN = {
    "money": re.compile(r"£|\d|\bpounds?\b|\bdollars?\b|\beuros?\b|\bquid\b", re.I),
    "time": re.compile(r"\d+\s*(?:minutes?|mins?|hours?|hrs?|days?|weeks?|months?)"
                       r"|\b(?:" + COUNT_WORD + r")\s+(?:minutes?|mins?|hours?|hrs?|days?"
                       r"|weeks?|months?|years?)|\ban hour\b", re.I),
    "count": re.compile(r"\b\d+\b|\b" + COUNT_WORD + r"\b", re.I),
    "when": re.compile(r"\b\d|\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|january"
                       r"|february|march|april|may|june|july|august|september|october|november"
                       r"|december|tomorrow|tonight|next week|next month|at \d)\b", re.I),
    "place": re.compile(r"\b(?:in|to|at) [A-Z]|\bhotel\b|\bstaying (?:in|at)\b"
                        r"|\b(?:in|to|at) (?!(?:" + PLACE_NOT + r")\b)[a-z]{3,}\b"),
    "which": re.compile(r"\b(?:in|to|at|near|around) \w+|\bcalled\b|\bnamed\b", re.I),
    "called": re.compile(r"\b(?:called|named)\b", re.I),
    "measure": re.compile(r"\b\d|\bmiles?\b|\bkilomet\w+\b|\bkm\b|\bmetres?\b|\bminutes?\b"
                          r"|\bhours?\b", re.I),
}

PLACE_NARROWER = re.compile(r"\b(?:staying|sleeping|eating|hotel|hostel|accommodation|campsite"
                            r"|airport|flight|parking|venue|school|office|shop)\b", re.I)

SHAPE_WORDS = frozenset("""
area part place area school club team course country city town kind sort type one ones called
named name about like
far many much often tall heavy big old long wide
""".split())

def _turned(question):
    words = str(question or "").rstrip(" ?!.").split()
    said = " ".join(TURNED.get(word.lower(), word) for word in words)
    # The understanding writes "what is the pay" out in full; said back to them it reads stiff.
    for long_form, short in (("what is the", "what's the"), ("what is it", "what is it"),
                             ("it is", "it's"), ("you are", "you're"),
                             ("where is the", "where's the")):
        said = re.sub(r"\b" + long_form + r"\b", short, said)
    return said

def _a_choice_from_what_was_said(line, memory):
    """"which one?" after a recommendation, when the last answer has a pick in it.

    A bare "which one" is the one ask back that is not warm here: the person is asking us to
    choose between the things we just recommended, and the answer is a part of that answer, not
    a request to say which one they mean. It declines unless the answer really does have a pick
    to give, so a "which one" with nothing behind it keeps the ask back it had before.
    """
    try:
        from ..modules.answers import CHOICE_ASK, _the_one_to_pick
    except Exception:  # noqa: BLE001 - a reading that cannot be imported declines nothing
        return False
    clean = " ".join(str(line or "").lower().split())
    if not CHOICE_ASK.match(clean):
        return False
    try:
        return bool(_the_one_to_pick(clean, memory))
    except Exception:  # noqa: BLE001 - a pick that cannot be made declines nothing
        return False

def _detail_they_left_out(memory, low):
    """A warm ask back when the question is about a detail of what they just told us."""
    line = str(low or "").strip()
    if not line or len(line.split()) > 9:
        return None
    if _a_clock_ask(line) and not a_when.EVENT_WORD.search(str(last_user(memory) or "")):
        # "what time is it" is a question about the clock, not a detail of their news: the "it"
        # in it points at nothing the chat has said, so asking it back ("You haven't said - what
        # time is it?") tells them nothing while the clock is right there to be said. After a
        # line that names something in a diary - "i have a dentist appointment" - the time is
        # that appointment's, and the ask back is the honest answer.
        return None
    if _about_the_bot_here(memory):
        # "where are you" and "where are you from" ask the bot, not for a detail of the person's
        # own news; the chat's own identity answer is the one that speaks to them.
        return None
    if _a_choice_from_what_was_said(line, memory):
        return None
    if not re.search(r"\b(?:how|whats?|where|when|which|whos?)\b", line):
        return None
    detail = None
    for pattern, kind in DETAIL_ASKS:
        if pattern.search(line):
            detail = kind
            break
    if detail is None:
        return None
    # Nothing of its own: every other word is a function word or one of the light verbs.
    spare = [word for word in re.findall(r"[a-z']+", line)
             if word not in DETAIL_VERBS and word not in SHAPE_WORDS
             and word not in ("how", "what", "where", "when", "which", "why", "s")]
    if spare:
        return None
    # A line with no pronoun at all is the same ask in fewer words when it names the *shape* of
    # the detail - "which area", "how far", "what was it about" - but a bare "how much", "how
    # many", "how long" or "how old" is a question about the world, not about their news: after
    # "i want to save for a house" the line "how much" is asking the bot, and asking it back
    # reads as if they had asked themselves. "what's the pay" leans back on the new job the same
    # way a pronoun does, so it stays.
    if not DETAIL_LEAN.search(line) and not re.search(r"\bthe (?:pay|price|salary)\b", line):
        if detail in ("money", "count", "time") or BARE_MEASURE.search(line):
            return None
    try:
        from ..memory import named as _named
        if _named.a_faulty_thing(memory):
            # The thing on the table has stopped working, so a measure ask about it points at that
            # thing and not at a detail of their news: "my boiler is broken" / "how long does it
            # take" asks how long the repair takes, and asking the line back ("You haven't said -
            # how long does it take?") tells them nothing. The answers module reads it.
            return None
    except Exception:  # noqa: BLE001 - a reading that cannot be imported declines nothing
        pass
    previous = str(last_user(memory) or "").strip()
    if not previous or previous.endswith("?") or len(previous.split()) < 3:
        return None
    # The line before was a question, typed without its mark as often as with it: there is no news
    # in it for a detail to have been left out of, so nothing is asked back. "is it worth getting
    # a flu jab" / "how much does it cost" was answered "You didn't say what it cost - how much was
    # it?", which asks the person the question they just asked.
    if ASK_OPENER.match(previous.lower()):
        return None
    # Their own news, not a question to us: "i" or "we" or "my" in the line before.
    if not re.search(r"\b(?:i|we|my|our|me)\b|\bive\b|\bim\b", previous.lower()):
        return None
    # ... and something that happened or is the case, not a want or a plan: a want has no
    # details to have left out, it has a price tag the bot can talk about.
    if WANTING.search(previous.lower()):
        return None
    # A destination does not answer an ask about a narrower place: "we are going to portugal" then
    # "where are we staying" still wants the hotel, so the place they named is not the detail this
    # line asks about.
    known = DETAIL_KNOWN.get(detail)
    narrower = detail == "place" and PLACE_NARROWER.search(line)
    if known is not None and not narrower and known.search(previous):
        return None
    if detail == "time" and HOW_LONG_IT_TAKES.search(line):
        return None
    if _the_answer_already_gives(detail, memory):
        return None
    if detail == "money" and re.search(r"\bcost\b", line):
        return "You didn't say what it cost - how much was it?"
    ask = _turned(line)
    if not ask:
        return None
    return "You haven't said - " + ask + "?"

PART_ASK = re.compile(
    r"\b(?:what|which|who|where|when)\b[^?.!]{0,40}?\b(?:do|does|did|is|are|was|were|can)\b"
    r"|\bhow (?:much|many|old|long|big|far|often|tall|heavy)\b", re.I)

PART_MINE = re.compile(r"\b(?:my|our)\s+([a-z']+)", re.I)

PART_POINTS = re.compile(r"\b(?:it|its|he|she|they|them|their|there|his|her)\b", re.I)

RECORD_PART = re.compile(
    r"\b(?:earn|earns|earning|paid|pay|wage|wages|salary|hours|shifts?|boss|manager"
    r"|colleagues?|coworkers?|uniform|(?:do|doing|did) there|work with|working with|works with|work for"
    r"|school|nursery|childminder|called|names?|named|model|make|year|colour|color|reg"
    r"|brand|mileage|breed)\b", re.I)

PART_ADVICE = re.compile(r"\b(?:should|shall|recommend|suggest|best|better|worth|instead|advice"
                         r"|ideas?|how do i|how can i|can i|could i|would you)\b", re.I)

PART_HELP = re.compile(r"\b(?:what|how) (?:do|can|should|could|would) i do (?:about|with|for|to|next"
                       r"|now|then)\b", re.I)

PART_OF = (
    ("job", re.compile(r"\b(?:earn|earns|earning|paid|wages?|salary|shifts?|boss"
                       r"|colleagues?|coworkers?|uniform)\b")),
    ("city", re.compile(r"\b(?:live|lives|moved|grew up)\b")),
    ("pets", re.compile(r"\b(?:dogs?|cats?|pets?|puppy|kitten|rabbit|hamster)\b")),
    ("people", re.compile(r"\b(?:son|daughter|mum|dad|mother|father|sister|brother"
                          r"|partner|wife|husband|kids?|children)\b")),
    ("owns", re.compile(r"\b(?:car|bike|laptop|phone|van)\b")),
)

JOB_PART = re.compile(
    # "there" on its own is in most of the asks it is not wanted in ("what is there to see",
    # "where is there work"), so it only counts as the object of the doing: "and what do i do
    # there", "what are they like to work there".
    r"\b(?:do|doing|did|work|working|works) there\b"
    r"|\bwho (?:do|does|did) (?:i|we) (?:\w+ )?(?:with|for)\b"
    r"|\b(?:what|which) (?:are )?(?:the )?(?:hours|shifts?|pay|uniform)\b"
    r"|\bhow (?:much|many|long) (?:do|does|did) (?:i|we)\b", re.I)

def _a_held_part(memory, line):
    """True when a fact the store keeps is one of the things the line names."""
    known = user(memory)
    for key, pattern in PART_OF:
        if pattern.search(line) and known.get(key):
            return True
    return False

def _a_part_of_the_job_never_said(memory, low):
    """The ask back for a part of the job the person never described, or None."""
    line = str(low or "").strip()
    if not line or len(line.split()) > 8:
        return None
    if not (user(memory) or {}).get("job"):
        return None
    if PART_ADVICE.search(line) or PART_HELP.search(line) or re.search(r"\d", line):
        return None
    if not JOB_PART.search(line):
        return None
    ask = _turned(line)
    if not ask:
        return None
    return "You haven't said - " + ask + "?"

def _holds_nothing(known):
    return not any(known.get(key) for key in PART_KEYS)

def _a_thing_it_keeps(memory, mine):
    """The rows of the store a possessive names, or None when the chat has been told nothing."""
    known = user(memory)
    if _holds_nothing(known):
        return None
    key = PART_HELD.get(str(mine or "").lower())
    if key is None:
        return None
    if key == "people":
        return key if (known.get("people") or known.get("others")
                       or known.get("kids")) else None
    if key == "city":
        return key if (known.get("city") or known.get("home")
                       or known.get("places")) else None
    return key if known.get(key) else None

def _the_part_it_never_said(memory, low):
    """The honest ask back for a part of a kept fact they never gave, or None.

    Called only when nothing else in the store answered, so a line the store can answer never
    reaches it. It is the hedge it replaces: without it "what do i do there" after "i work at a
    cafe" is pointed at a search engine, and "and what do i do there" after "where do i work"
    is the same sentence the bot just said.
    """
    line = str(low or "").strip()
    if not line or len(line.split()) > 8:
        return None
    if PART_ADVICE.search(line) or PART_HELP.search(line) or re.search(r"\d", line):
        return None
    if not PART_ASK.search(line) or not RECORD_PART.search(line):
        return None
    mine = PART_MINE.search(line)
    if mine:
        if not _a_thing_it_keeps(memory, mine.group(1)):
            return None
    elif not (PART_POINTS.search(line)
              or (re.search(r"\b(?:i|im)\b", line) and _a_held_part(memory, line))):
        return None
    # A pointing word is about what was just said, so there has to be a fact line behind it and
    # not another question: "where do i work" then "and what do i do there" leans on the fact
    # line two turns back, which the store holds anyway.
    if not _a_kept_thing_behind(memory):
        return None
    ask = _turned(line)
    if not ask:
        return None
    return "You haven't said - " + ask + "?"

def _a_kept_thing_behind(memory):
    """True when the nearest thing they said about themselves is a fact the store keeps.

    The line this reader answers leans back on that fact ("there" after "i work at a cafe" is
    the job, "it" after "i drive a ford" is the car), so which fact was said decides whether the
    store can be asked about a part of it.
    """
    from bot.memory import facts as kept

    for turn in reversed(recent(memory, 5)):
        said = str(turn.get("user") or "").strip()
        if not said or said.endswith("?"):
            continue
        if not re.search(r"\b(?:i|we|my|our|im|ive)\b", said.lower()):
            continue
        try:
            found = kept.extract(said)
        except Exception:  # noqa: BLE001 - a line that cannot be read keeps the old answer
            return False
        if not isinstance(found, dict):
            return False
        if any(found.get(key) for key in KEPT_THINGS):
            return True
    return False

DRINK_DIET = frozenset("""alcohol booze wine wines beer beers lager lagers cider spirits gin
vodka whisky whiskey rum prosecco champagne cocktails cocktail sherry brandy""".split())

def _diet_how(diet):
    """The verb a diet is said with: what you drink is not what you eat."""
    words = set(re.split(r"[ ,]+", str(diet or "")[3:].strip().lower()))
    return "drink" if words & DRINK_DIET else "eat"

REMEMBER_IT = re.compile(
    r"^(?:and |so |ok |okay |but |well )*(?:do |did )?you (?:still )?(?:remember|recall)"
    r"(?: (?:it|that|this|that one))?(?: (?:yes or no|or not|right|then))?$"
    r"|^(?:do|did) you (?:still )?(?:remember|recall) (?:it|that|this)$")

def _the_fact_just_asked(memory, low):
    """The fact the store answered on the turn before, said again for "do you remember it?".

    The ask carries no subject of its own, so it is about the fact the store just said - and
    only when that fact is recent (the last turn or the one before it) and the store was the
    one that said it. When there is no such fact the line is left to the other modules, so
    "do you remember it?" in a fresh chat still gets the honest answer about this chat only.
    """
    if not isinstance(memory, dict) or not REMEMBER_IT.match(str(low or "").strip()):
        return None
    asked = memory.get("asked")
    if not isinstance(asked, dict) or not asked.get("slot"):
        return None
    turns = memory.get("turns") or []
    try:
        asked_turn = int(asked.get("turn") or 0)
    except (TypeError, ValueError):
        return None
    if not turns or len(turns) - asked_turn > 2:
        return None
    if last_module(memory) != "memory_store":
        return None  # a question in between ("whats my name" / "nice one" / "remember it?")
    reply = _respond(_slot_words(str(asked["slot"]), memory), memory)
    if not reply or ELIDED_NOT_SURE.search(reply):
        return None
    return _yes_then(reply)

def _yes_then(reply):
    """The fact with a yes in front of it, "you" still lower case after the dash."""
    text = str(reply or "").strip()
    if re.match(r"^(?:You|Your|It)\b", text):
        text = text[:1].lower() + text[1:]
    return "Yes \u2014 " + text

CONFIRM_FRAMES = (
    (re.compile(r"^(?:am|was) i\s+(?:not\s+)?(.+)$"), "i am "),
    (re.compile(r"^(?:do) i\s+(?:still\s+|really\s+|actually\s+)?(.+)$"), "i "),
    (re.compile(r"^(?:have) i\s+(?:got\s+|really\s+|actually\s+)?(.+)$"), "i have "),
)

YES_NO_ASK = re.compile(
    r"^\W*(?:is|are|was|were|does|did|do|can|could|has|have|had|will|would|should|may|might)\s+"
    r"(?:she|he|they|his|her|their|my|your)\b", re.I)

YES_NO_FRAME = re.compile(
    r"^\W*(?:is|are|was|were|does|did|do|can|could|has|have|had|will|would|should|may|might)\s+"
    r"[^?.!;]*[?.!;]+\s*", re.I)

TELLING_AFTER_ASK = re.compile(
    r"\b(?:he|she|they|it|we|my\s+(?:" + _RELATION + r"))\s+"
    r"(?:is|are|was|were|doesnt|does not|dont|do not|cant|cannot|wont|will not|has|have|had"
    r"|likes?|loves?|eats?|drinks?|never|always|usually|only|really|prefers?|hates?)\b", re.I)

def _after_the_yes_no_frame(text):
    """What the line says after a yes/no question about someone else, or ""."""
    line = " ".join(str(text or "").split())
    match = YES_NO_FRAME.match(line)
    if match:
        return line[match.end():].strip()
    # Most people type no mark at all. The ask is the frame, and it ends where the telling
    # begins: at the next clause that has a person and a verb of its own. Without this the whole
    # line was read as the ask, so both the ask and the fact told with it went unanswered.
    opened = YES_NO_ASK.match(line)
    if not opened:
        return ""
    after_who = line[opened.end():]
    telling = TELLING_AFTER_ASK.search(after_who)
    if not telling:
        return ""
    return after_who[telling.start():].strip()

def _statement(text):
    """The plain statement a yes/no question about the person makes.

    "am i vegetarian?" is "i am vegetarian", "do i live in leeds?" is "i live in leeds", and
    "is my budget 500?" is "my budget is 500". None when the line is not that shape.
    """
    low = " ".join(text.lower().split()).strip(" ?!.")
    low = re.sub(r"^(?:sorry|hey|hi|ok|okay|so|but|and|well|quick one)[, ]+", "", low)
    for pattern, lead in CONFIRM_FRAMES:
        match = pattern.match(low)
        if match:
            return lead + match.group(1)
    # "is my dog called biscuit" -> "my dog is called biscuit". Only a short answer is read
    # this way, so "is my name hard to say" is not taken for a fact about the name.
    match = re.match(r"^(?:is|was) my\s+(\S+)\s+(.+)$", low)
    if match and (re.match(r"^(?:called |named )?\S+$", match.group(2))
                  or match.group(2).startswith("called ")):
        return "my " + match.group(1) + " is " + match.group(2)
    return None

def _same(left, right):
    return " ".join(str(left).lower().split()) == " ".join(str(right).lower().split())

def _clause(key, value, known=None):
    """The fact said the way a friend would say it back: "you're vegetarian"."""
    if key == "name":
        return "you're " + str(value)
    if key == "age":
        return "you're " + str(value)
    if key == "job":
        # A job told with a place preposition is a place ("you work at the hospital"), so the
        # frame stored with it says it back, not "you're a hospital".
        known = known if isinstance(known, dict) else {}
        frame = str(known.get("job_frame") or "").strip()
        if frame and _same(value, known.get("job")):
            said = _job_said({"job": str(value), "job_frame": frame})
            return said[:1].lower() + said[1:]
        return "you're " + _a(str(value))
    if key == "city":
        return "you live in " + str(value)
    if key == "car":
        return "you drive " + str(value)
    if key == "from":
        return "you're from " + str(value)
    if key == "allergies":
        return "you're allergic to " + ", ".join(value)
    if key == "budget":
        return "your budget is " + str(value)
    if key == "diet":
        diet = str(value)
        return ("you don't " + _diet_how(diet) + " " + diet[3:] if diet.startswith("no ")
                else "you're " + diet)
    if key == "pets":
        pets = value if isinstance(value, list) else [value]
        parts = [_a_pet(p) for p in pets]
        return "you've got " + " and ".join(parts)
    return ""

def _their_allergy(who, theirs):
    """Someone else's allergy, said back with whose it is: a no about the person asked about."""
    return ("You haven't told me one \u2014 the allergy to " + ", ".join(theirs)
            + " is your " + who + "'s, not yours.")

DIET_ANY = re.compile(r"^(?:on\s+)?(?:a\s+)?diet(?:ing)?$", re.I)

def _said_matches(key, said, known):
    """Whether what the question states is what they told you. None when it is not about a
    fact the store would keep."""
    if key == "name":
        return _same(said, known) if known else False
    if key == "age":
        return known is not None and str(said) == str(known)
    if key == "diet" and DIET_ANY.match(str(said).strip()):
        # They asked about a diet in general, not about a diet they named: "im vegan" is not a
        # "no" to "am i on a diet". Left to the diet reader, which says the fact back.
        return None
    if key in ("job", "city", "from", "diet"):
        return _same(said, known) if known else False
    if key == "budget":
        mine = re.sub(r"[^0-9]", "", str(said))
        theirs = re.sub(r"[^0-9]", "", str(known or ""))
        return bool(mine) and mine == theirs
    if key == "allergies":
        stored = {str(a).lower() for a in (known or [])}
        return bool(said) and all(str(a).lower() in stored for a in said)
    if key == "pets":
        for pet in known or []:
            if _animal_family(pet.get("animal")) != _animal_family(said.get("animal")):
                continue
            if not said.get("name") or _same(pet.get("name"), said.get("name")):
                return True
        return False
    return None

def _names(key, text):
    pattern = NAMED_BY.get(key)
    return bool(pattern) and bool(re.search(pattern, text))

DUTY_ASK = re.compile(
    r"\b(?:need|needs|needed|have|has|had) to\b|\bshould\b|\bshouldn't\b|\bmust\b|"
    r"\bgot time\b|\bworth\b|\bhow (?:often|much|long)\b|\bbetter\b")

REMEMBERING_FRAME = re.compile(
    r"^(?:(?:and|but|so|ok|okay|right|well|oh|ah|quick one|sorry|hi|hiya|hey|hello|just|also)"
    r"[\s,]+)*"
    r"(?:"
    r"(?:(?P<aux>do|did|does|can|could|would|will|have|has)\s+)?(?:you|u)\s+"
    r"(?:still\s+|even\s+)?(?P<verb>remember|recall|know|remembered|noticed)"
    r"|(?P<bare>remember|recall)\b"
    r")"
    r"(?:\s+(?:that|this|it|me|about that|about it|all that))?", re.I)

RESTATED = re.compile(r"^(?:i|im|i'm|ive|i've|id|i'd|ill|i'll|my|we|we're|weve|we've|our)"
                      r"\b", re.I)

CONFIRM_TAG = re.compile(r"[\s,]+(?:right|tho|though|yes|yeah|yep|ok|okay|lol|ha|haha|innit|"
                         r"correct)\s*$", re.I)

def _restated(text, typed=None):
    """The statement behind a remembering frame: "do you remember that i live in leeds" ->
    "i live in leeds". None when the line is not that shape.

    The frame has to be asking something: a question mark, an auxiliary in front of it ("do you
    remember"), the bare verb ("remember that im 34"), or the tag that asks for the yes ("you
    know im veggie right"). "just so you know, im called sam" states the fact and is not a
    question about the store, so it is left to the ordinary reply.
    """
    low = " ".join(str(text or "").lower().split()).strip()
    tagged = bool(CONFIRM_TAG.search(low))
    low = CONFIRM_TAG.sub("", low).strip(" ?!.,")
    frame = REMEMBERING_FRAME.match(low)
    if not frame:
        return None
    question = "?" in str(text if typed is None else typed)
    # "you remember im allergic to nuts" is a confirmation seek; "you know im veggie" without a
    # question mark is the person telling you again ("just so you know, im called sam"), and
    # that is not a question about the store.
    asking = (question or tagged or frame.group("aux") or frame.group("bare")
              or (frame.group("verb") or "").startswith(("remember", "recall")))
    if not asking:
        return None
    rest = low[frame.end():].strip(" ?!.,")
    if not rest or not RESTATED.match(rest):
        return None
    return rest

def _behind_a_remembering_frame(text):
    """The line a remembering frame is around, when it is a line the store can read.

    _restated covers the person's own statements ("do you remember that i live in leeds"). This
    covers the rest: "can you remember that my son is allergic to nuts" and "can you remember the
    dentist is on tuesday" are the same shape - a frame with a fact behind it - and both were
    answered as questions about the bot's memory, which is not what the line asks. The test is
    the store's own: what is left after the frame is read as a fact, or the frame is left alone.
    """
    low = " ".join(str(text or "").lower().split()).strip(" ?!.,")
    frame = REMEMBERING_FRAME.match(low)
    if not frame:
        return None
    questioning = ("?" in str(text or "") or frame.group("aux") or frame.group("bare")
                   or (frame.group("verb") or "").startswith(("remember", "recall")))
    if not questioning:
        return None
    rest = low[frame.end():].strip(" ?!.,")
    if not rest or rest == low:
        return None
    if not SAYS_SOMETHING.search(rest):
        # "do you remember my mums age" is a question about a fact, not the fact: the words
        # behind the frame only name the thing asked about. Read as a statement they filed the
        # word "age" as the mum's name and answered "Age is 68."
        return None
    if extract.extract(rest):
        return rest
    return None

SAYS_SOMETHING = re.compile(
    r"\b(?:is|are|was|were|am|im|i'm|been|be|s|have|has|had|got|called|named|live|lives|"
    r"move|moved|moving|start|starts|started|work|works|eat|eats|need|needs|want|wants|like|"
    r"likes|love|loves|prefer|prefers)\b", re.I)

def _remembers_fact(text, memory):
    """Yes or no to "do you remember that i ...", from the fact they told the store.

    A fact the store holds is confirmed in its own words ("Yes - you're vegetarian."), and one
    stated the other way round is put right gently ("You told me you live in Leeds."). A
    statement the store keeps nothing about is left to the other modules: this reader answers
    only what it holds.
    """
    said = _restated(_folded(text, memory), text)
    if not said:
        return None
    found = extract.extract(said) or {}
    known = user(memory)
    yes, no = [], []
    for key in RESTATED_KEYS:
        value = found.get(key)
        if not value:
            continue
        stored = known.get(key)
        if not stored:
            continue
        if key == "pets":
            value = [p for p in value if isinstance(p, dict) and (p.get("name") or p.get("animal"))]
            if not value:
                continue
            value = value[0]
        matches = _said_matches(key, value, stored)
        said_back = _clause(key, stored, known)
        if not said_back:
            continue
        if matches:
            yes.append(said_back)
        elif matches is not None:
            no.append(said_back)
    if yes:
        fact = yes[0]
        return pick(["Yes \u2014 " + fact + ".",
                     fact[:1].upper() + fact[1:] + " \u2014 I have that.",
                     "That's right \u2014 " + fact + "."], memory)
    if no:
        fact = no[0]
        return pick(["You told me " + fact + ".", "Not quite \u2014 " + fact + "."], memory)
    # A frame around a fact the store has just been told is not a question it can answer yes or
    # no to: the keys above are the person's own facts, and their sister's name is not one of
    # them. Saying nothing left the line to the about-the-bot reader, which answered a person who
    # had just given the name with "there's nothing on your sister". What the frame asks for is
    # the store holding it, so the fact it now holds is said back.
    kept = _someone_said_back(said, memory)
    if kept:
        return kept
    return None

def _someone_said_back(said, memory):
    """The fact about someone else that the framed statement just gave, said back."""
    words = " ".join(str(said or "").lower().split())
    if not words:
        return None
    found = extract.extract(said) or {}
    said_about = [other for other in (found.get("others") or []) if isinstance(other, dict)]
    for entry in others(memory):
        if not isinstance(entry, dict):
            continue
        who = str(entry.get("who") or "").strip().lower()
        if not who or not re.search(r"\b" + re.escape(who) + r"\b", words):
            continue
        if "name" in entry:
            called = _called(str(entry.get("name") or "").strip())
            if called:
                return "Your " + who + " is called " + called + "."
            continue
        # A figure said about someone in the frame is said back the same way, so the receipt is
        # not "there's nothing on your son" about the age just filed against him: "can you
        # remember my son is 7" is "Your son is 7."
        age = entry.get("age")
        if age in (None, "", [], {}):
            continue
        given = [other.get("age") for other in said_about
                 if str(other.get("who") or "").lower() == who]
        if str(age) in [str(one) for one in given]:
            return "Your " + who + " is " + str(age) + "."
    return None

# A category of food, and the words people use for it. Only a category is read: "do i eat
# halloumi" is a question about a food and the kitchen entries answer it, while "do i eat meat"
# is a question about the rule they gave the store.
FOOD_CATEGORIES = (
    ("meat", ("meat", "chicken", "beef", "pork", "lamb", "bacon", "ham", "sausage", "sausages",
              "steak", "mince", "turkey", "burger", "burgers", "veal", "venison")),
    ("fish", ("fish", "salmon", "tuna", "prawn", "prawns", "shellfish", "cod")),
    ("dairy", ("dairy", "milk", "cheese", "butter", "cream", "yoghurt", "yogurt")),
    ("eggs", ("egg", "eggs")),
    ("gluten", ("gluten", "wheat", "bread", "pasta", "flour")),
    ("nuts", ("nut", "nuts", "peanut", "peanuts")),
    ("alcohol", ("alcohol", "beer", "wine", "booze", "spirits", "cider")),
)
# Words that say how much of the food, not which food it is: "do i eat red meat" is still meat.
NOT_THE_FOOD = frozenset((
    "red", "white", "processed", "raw", "cooked", "fresh", "any", "more", "much", "some", "the",
    "a", "bit", "of", "lot", "still", "either", "anymore", "again", "now", "it", "that", "this",
    "at", "all",
))
# What each rule the store keeps takes off the table. The diet is its own words ("vegetarian",
# "no alcohol"), an allergy names the food, and a condition names what it rules out: the reader
# asks this table instead of guessing from the words of the line.
A_DIET_RULES_OUT = {
    "vegetarian": ("meat",),
    "vegan": ("meat", "fish", "dairy", "eggs"),
    "pescatarian": ("meat",),
    "no meat": ("meat",),
    "no dairy": ("dairy",),
    "dairy free": ("dairy",),
    "dairy-free": ("dairy",),
    "gluten free": ("gluten",),
    "gluten-free": ("gluten",),
    "no alcohol": ("alcohol",),
}
A_CONDITION_RULES_OUT = {
    "coeliac": ("gluten",),
    "celiac": ("gluten",),
    "coeliac disease": ("gluten",),
    "lactose intolerant": ("dairy",),
}
# The ask is "do i eat meat", "do i drink alcohol": a yes/no about the rule they gave the store.
# "do i have milk" is not this ask - it is a look in the fridge - so `have` is not read here.
# The `can i eat` shape is left alone - the kitchen entries answer it with the substitutes, which
# is a better answer than the rule said back.
# The lead-in is stripped, then the ask is read: "so do i eat meat" is the same question as
# "do i eat meat", and a person who asks it that way has been mid-conversation for a while.
# "did i eat meat" is a question about the meal they had, not about the rule: the rule cannot
# answer what was on the plate last night, so the ask is the present one only.
EATING_ASK = re.compile(
    r"^\W*do\s+i\s+(?:still\s+|really\s+|actually\s+|now\s+|ever\s+)?"
    r"(?:eat|drink)\s+(.+)$", re.I)
LEAD_IN = re.compile(r"^(?:so|and|but|ok|okay|well|sorry|hey|right|quick one)[, ]+", re.I)


def _the_food_named(rest):
    """The category a bare food phrase names, or "" when it names none of them."""
    said = [word for word in re.findall(r"[a-z']+", str(rest or "").lower())
            if word not in NOT_THE_FOOD]
    if not said:
        return ""
    for category, words in FOOD_CATEGORIES:
        if all(any(word == one or word == one.rstrip("s") or word.rstrip("s") == one.rstrip("s")
                   for one in words) for word in said):
            return category
    return ""


def _the_rule_that_rules_it_out(known, category):
    """The rule they gave the store that takes this food off the table, said back, or ""."""
    diet = " ".join(str(known.get("diet") or "").lower().split())
    taken = list(A_DIET_RULES_OUT.get(diet) or ())
    if known.get("no_meat") and "meat" not in taken:
        taken.append("meat")
    if category in taken:
        if diet:
            return "No \u2014 " + _clause("diet", known.get("diet")) + "."
        return "No \u2014 you don't eat meat."
    for allergy in known.get("allergies") or []:
        said = str(allergy).lower()
        if any(said == one or said.rstrip("s") == one.rstrip("s")
               for one in dict(FOOD_CATEGORIES)[category]):
            return "No \u2014 " + _clause("allergies", known.get("allergies")) + "."
    for condition in known.get("condition") or []:
        word = " ".join(str(condition).lower().split())
        if category in (A_CONDITION_RULES_OUT.get(word) or ()):
            return "No \u2014 you've told me you're " + word + ", so " + category + " is out."
    return ""


def _a_rule_on_eating(text, memory):
    """A yes/no about eating or drinking a food, answered from the rule the store keeps.

    "im vegetarian" / "do i eat meat" was answered "I'm not sure about that one, sorry" - a
    search hedge about something the person had just told the bot - because the confirmation
    reader looks for a fact of the same shape ("i eat meat") and what the store was told is the
    rule. Only a rule that takes the food off the table is answered: a food their rule allows is
    read by the kitchen entries, which know the substitutes, and a food no rule mentions is left
    to them as well.
    """
    line = " ".join(str(text or "").lower().split())
    match = EATING_ASK.match(LEAD_IN.sub("", line))
    if not match:
        return None
    category = _the_food_named(match.group(1).strip(" ?!."))
    if not category:
        return None
    known = user(memory)
    if not isinstance(known, dict):
        return None
    rule = _the_rule_that_rules_it_out(known, category)
    return rule or None


def _confirmation(text, memory):
    """Answer a yes/no question about something they told you, from what they told you."""
    statement = _statement(text)
    if not statement:
        return None
    if DUTY_ASK.search(statement):
        return None
    # "am i not allergic to nuts?" asks for the opposite yes or no.
    inverted = bool(re.search(r"\b(?:not|n't)\b", " ".join(text.lower().split())))
    found = extract.extract(statement)
    if not found:
        return None
    known = user(memory)
    yes, no, elsewhere = [], [], []
    for key, value in found.items():
        if key not in ("name", "age", "job", "city", "from", "diet", "budget", "allergies",
                       "pets"):
            continue
        stored = known.get(key)
        # A pet is read as a list even for one animal, and only a named one is an assertion.
        if key == "pets":
            value = [p for p in value if p.get("name") or p.get("animal")]
            if not value:
                continue
            value = value[0]
        # Only a fact the store actually holds is confirmed or denied: without it "am i right?"
        # would be read as a job ("i am right") and answered "No — you're ...".
        if not stored:
            # A fact they gave about someone else, asked about themselves: "my mums allergic to
            # nuts" then "am i allergic to nuts" is a no, and the honest answer says whose it is
            # rather than leaving the line to the general answer about allergies.
            theirs_who, theirs = _other_fact(memory, key)
            if theirs_who and theirs:
                elsewhere.append((key, theirs_who, theirs))
            continue
        matches = _said_matches(key, value, stored)
        if matches is None:
            continue
        if matches:
            yes.append(_clause(key, stored or value, known))
        elif _names(key, " ".join(text.lower().split())):
            said_back = _clause(key, stored if stored else value, known)
            if said_back:
                no.append(said_back)
    if inverted:
        yes, no = no, yes
    if not yes and not no:
        for key, who, theirs in elsewhere:
            if key == "allergies":
                return _their_allergy(who, theirs)
        return None
    if no and not yes:
        # "do i live in york or leeds?" is an either/or, so the answer is just the fact.
        if re.search(r"\bor\b", " ".join(text.lower().split())):
            return no[0][:1].upper() + no[0][1:] + "."
        return pick(["No — " + no[0] + ".", "Not quite — " + no[0] + "."], memory)
    said = "; ".join(yes[:2]) if yes else ""
    if no and yes:
        return pick(["Yes on one thing, no on another: " + said + ", but " + no[0] + ".",
                     "Partly — " + said + ", though " + no[0] + "."], memory)
    return pick(["Yes — " + said + ".", "That's right — " + said + ".",
                 "Yes, you told me — " + said + "."], memory)

def _old_values(memory, told):
    """The words of the line before the correction that a correction could have swapped out.

    The plan is kept as the phrase the person used ("Portugal in june"), so its words are the
    candidates: a month or a day is a value of the fact and is said back by the note alone
    ("make that july"), and the filler words are not values at all.
    """
    out = []
    entries = memory.get("facts_log")
    if not isinstance(entries, list):
        return out
    for entry in reversed(entries):
        if not isinstance(entry, dict):
            continue
        if " ".join(str(entry.get("text") or "").lower().split()) != told.lower():
            continue
        if entry.get("key") not in SWAPPABLE:
            continue
        for word in re.split(r"[\s,]+", str(entry.get("value") or "")):
            low = word.lower().strip("'-.!?")
            if (len(low) > 2 and low not in MONTHS and low not in extract.DAYS
                    and low not in STOPWORDS and low not in out
                    and re.search(r"\b" + re.escape(low) + r"\b", told, re.I)):
                out.append(low)
    return out

PUTTING_BY = re.compile(r"\b(?:save|saves|saving|saving up|put away|put by|set aside|put aside)\b",
                        re.I)

def _a_figure(word):
    """True when the value is a number rather than a word of the sentence ("100", "2k", "1,500")."""
    return bool(re.fullmatch(r"\d[\d,]*(?:\.\d+)?\s*(?:k|grand|thousand|pounds?|quid)?",
                             str(word or "").strip(), re.I))

def _swapped_lines(memory, fixed):
    """The lines the person would have said if they had said it right the first time."""
    if not isinstance(fixed, dict):
        return []
    if fixed.get("dropped"):
        # Nothing took the value's place, so there is no line they "would have said" and nothing
        # to answer about it: the note that it is gone is the whole of this turn.
        return []
    value = str(fixed.get("value") or "").strip()
    said = last_user(memory, 3) or []
    if isinstance(said, str):
        said = [said]
    # The correction line itself is the newest turn on some paths and not yet recorded on
    # others, so the line before it is the newest one that is not the correction.
    mine = " ".join(str(fixed.get("said") or "").lower().split())
    said = [x for x in said if " ".join(str(x).lower().split()) != mine]
    told = " ".join(str(said[-1] if said else "").split())
    if not value or not told:
        return []
    out = []
    moved = _the_time_that_moved(told, fixed, value)
    if moved:
        # The time is the one value in the sentence that cannot be added beside the old one -
        # "im going to lisbon in June in may" is still a line about May - so the corrected
        # sentence is the only one they could have said.
        return [moved]
    olds = _old_values(memory, told)
    if _a_figure(fixed.get("from")) and _a_figure(value):
        # The thing corrected is the figure in the line and the new thing is a figure too, so the
        # figure is what moves. Swapping a *word* of it instead leaves the old number standing
        # beside the new one - "i want to save 200 a month" / "actually make it 100" gave "i want
        # to Save 100 a month 200 a month" - and that line reads as two rates with a sum between
        # them: answers took the 200 as the goal and said "£200 at £100 a month is 2 months."
        olds = [old for old in olds if _a_figure(old)]
    out.extend(re.sub(r"\b" + re.escape(old) + r"\b", value, told, count=1, flags=re.I)
               for old in olds)
    # A figure of the line before, changed rather than a word of it ("make it 75 instead" after
    # "i can put away 50 a month"): the line they would have said is that one with the new figure
    # in it, and it is what the answer to their correction is about (bot/memory/resize.py).
    resized = resize.rewritten(str(fixed.get("said") or ""), memory)
    if resized:
        out.append(resized)
    out = [line for index, line in enumerate(out) if line not in out[:index]]
    if _a_figure(fixed.get("from")) and re.search(r"\d", value):
        # A line that still carries the figure the person replaced has not been corrected at all,
        # and read as the line they "would have said" it names both figures: "i want to Save 100
        # a month 200 a month" is two rates with a sum between them, which is how a corrected
        # amount became the goal of £200 nobody had named.
        gone = re.compile(r"\b" + re.escape(str(fixed["from"]).replace(",", "")) + r"\b")
        out = [line for line in out if not gone.search(line.replace(",", ""))]
    return out

def _the_time_that_moved(told, fixed, value):
    """The line they would have said, when what they corrected is the month or the day in it.

    "i'm going to lisbon in may" and "sorry, june" keeps Lisbon and moves the time, so the line
    they would have said is the one before with June where May was. The generic swap takes the
    words of the stored phrase instead, and on a plan kept as "Lisbon in June" that put both
    months in one line - "i'm going to Lisbon in June in may" - which the answers then read as
    May, so a June trip was given the May advice.
    """
    wrong = str(fixed.get("from") or "").strip()
    relative = RELATIVE_MONTH.fullmatch(wrong) if wrong else None
    if relative is not None:
        # The date taken back was said in relative words, so the month they name now is what
        # goes in its place: "im going to rome next month" and "no in july" is the line they
        # would have said. Put the value in whole instead and the plan gathers both dates
        # ("rome in July next month"), which the answers then read as next month.
        day, month = _date_said(str(fixed.get("value") or "").lower())
        if not month or not re.search(r"\b" + re.escape(wrong) + r"\b", told, re.I):
            return None
        said = _date_word_case(month)
        said = ("on the {day} of {said}".format(day=day, said=said) if day else "in " + said)
        return re.sub(r"\b" + re.escape(wrong) + r"\b", said, told, count=1, flags=re.I)
    was, now = _date_word(wrong), _date_word(value)
    if not was or not now or was.lower() == now.lower():
        return None
    # Only within one family: a month moves for a month and a day for a day. "on monday" and
    # "make that june" are two different things said about a fact, not one value moving.
    if (was.lower() in MONTHS) != (now.lower() in MONTHS):
        return None
    if not re.search(r"\b" + re.escape(wrong) + r"\b", told, re.I):
        return None
    return re.sub(r"\b" + re.escape(wrong) + r"\b", now, told, count=1, flags=re.I)

def _a_rate_changed(text, memory):
    """True when the figure this line changed is money put by each month, not a word of a fact."""
    rewritten = resize.rewritten(text, memory)
    if not rewritten or resize.rate(rewritten) is None:
        return False
    return bool(PUTTING_BY.search(rewritten))

def _answer_the_new_one(memory, fixed):
    """The answer about the thing a correction swapped in, or None when there is nothing to say.

    A month or a number is a value of the fact, not a thing with an answer of its own, so
    "make that july" keeps the short note alone. More than one word of the line before can be
    the one that moved ("Portugal in june" and "A trip to Lisbon in May"), so each is tried and
    the first one the answers have something to say about is the one taken.
    """
    if isinstance(fixed, dict) and fixed.get("quiet"):
        # The note already says the thing in the sentence it was said in, so there is no line to
        # read the new value off and nothing to add (see `_an_amount_on_the_measure`).
        return None
    lines = _swapped_lines(memory, fixed)
    if not lines:
        return None
    before = memory.get("understood")
    from ..modules import answers
    from ..memory import again as same_again
    try:
        for line in lines[:4]:
            memory["understood"] = understand(line, memory)
            reply = answers.respond(line, memory)
            if not isinstance(reply, str) or not reply.strip():
                continue
            if same_again.unframed(reply):
                # The only answer the new thing has is the paragraph already on the screen, and
                # it comes back under the repeat's lead-in: "Got it — Spain on the 4th of June.
                # Same answer, and it covers this: Spain: Barcelona for a city and a beach...".
                # The note is the turn; the store does not answer itself inside it.
                return None
            return reply
    finally:
        if before is None:
            memory.pop("understood", None)
        else:
            memory["understood"] = before
    return None

def _name_fixed_this_turn(text, memory):
    """The line that says a person's name has been moved: "Dana, not Dave - got it."

    Without it the name changed quietly and the turn went to whichever module liked a word in
    the line - "no shes called dana" was answered with advice about cold callers - so the person
    had no way to know the correction had landed.
    """
    fixed = memory.get("name_fixed") if isinstance(memory, dict) else None
    if not isinstance(fixed, dict) or fixed.get("said") != " ".join(str(text or "").lower().split()):
        return None
    memory.pop("name_fixed", None)
    name = str(fixed.get("name") or "")
    before = str(fixed.get("from") or "")
    if not name:
        return None
    if before and before.lower() != name.lower():
        return "{Name}, not {Before} \u2014 got it.".format(
            Name=name[:1].upper() + name[1:], Before=before[:1].upper() + before[1:])
    return "{Name} \u2014 got it.".format(Name=name[:1].upper() + name[1:])

_NUMBER_WORDS = (
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen").split()

def _a_number_word(number):
    """A number said in words: 8 -> "eight", 71 -> "seventy-one", 105 -> "one hundred and five"."""
    try:
        number = int(number)
    except (TypeError, ValueError):
        return str(number)
    if number < 0:
        return str(number)
    if number < len(_NUMBER_WORDS):
        return _NUMBER_WORDS[number]
    if number < 100:
        tens, ones = divmod(number, 10)
        return _TENS_WORDS[tens] + ("-" + _NUMBER_WORDS[ones] if ones else "")
    if number < 1000:
        hundreds, rest = divmod(number, 100)
        said = _NUMBER_WORDS[hundreds] + " hundred"
        return said if not rest else said + " and " + _a_number_word(rest)
    return str(number)

def _fact_moved_this_turn(text, memory):
    """The correction that moves a fact to another person: "Your daughter, not your son - got it."."""
    moved = memory.get("fact_moved") if isinstance(memory, dict) else None
    if not isinstance(moved, dict) or moved.get("said") != " ".join(str(text or "").lower().split()):
        return None
    memory.pop("fact_moved", None)
    who = str(moved.get("who") or "").strip()
    was_who = str(moved.get("was_who") or "").strip()
    value = moved.get("value")
    if moved.get("kind") == "age":
        number = _a_number(value)
        if not number:
            return None
        said_value = _a_number_word(number)
    elif isinstance(value, str):
        said_value = value
    else:
        return None
    if not (who and was_who and said_value):
        return None
    return pick(CORRECTED_WHICH_PERSON, memory, seed_text=text).format(
        Value=said_value[:1].upper() + said_value[1:], value=said_value, who=who,
        was_who=was_who)

def _fact_fixed_this_turn(text, memory):
    """The line that says a fact about someone has been put right: "Eight, not seven - got it."."""
    fixed = memory.get("fact_fixed") if isinstance(memory, dict) else None
    if not isinstance(fixed, dict) or fixed.get("said") != " ".join(str(text or "").lower().split()):
        return None
    memory.pop("fact_fixed", None)
    who = str(fixed.get("who") or "").strip()
    was = fixed.get("was")
    value = fixed.get("value")
    # An age arrives as a figure in one shape and as a word in the other ("8" from the reader,
    # and 7 already stored), so both sides are read as numbers before the words are chosen.
    new_number, old_number = (_a_number(value), _a_number(was))
    if fixed.get("kind") == "age" and new_number and old_number:
        value_said = _a_number_word(new_number)
        was_said = _a_number_word(old_number)
        said = pick(CORRECTED_AGAIN, memory, seed_text=text).format(
            Value=value_said[:1].upper() + value_said[1:], was=was_said,
            were=was_said[:1].upper() + was_said[1:], who=who,
            value=value_said)
    elif isinstance(value, str) and isinstance(was, str):
        said = pick(CORRECTED_AGAIN_WHO, memory, seed_text=text).format(
            Value=value[:1].upper() + value[1:], who=who or "you", value=value)
    else:
        return None
    return said

def _respond(text, memory):
    # "whats our plan", "what have we decided", "what do we know so far": the ask is for
    # everything the chat holds, so the answer is the list (`_summary_reply`) - not the newest
    # line, not a choice the chat never made ("You haven't picked one yet"), and not a card. It
    # goes first because the readers below each answer a question of their own: `decided` reads
    # "what have we decided" as a choice and denies a chat that made several.
    low_here = " ".join(str(text or "").lower().split())
    if _summed_up(low_here):
        # A chat that holds nothing of theirs has nothing to sum up, and the list's tail would
        # name the ask's own verb as the subject ("we've been on the decided"). The recap's own
        # "we're still at the beginning" is the honest reply to a summary of an empty chat.
        if not any(str(value or "").strip() for value in user(memory).values()):
            return _vary(NOTHING_STARTED, memory)
        return _summary_reply(memory)
    renamed = _name_fixed_this_turn(text, memory)
    if renamed:
        return renamed
    put_right = _fact_fixed_this_turn(text, memory)
    if put_right:
        return put_right
    moved = _fact_moved_this_turn(text, memory)
    if moved:
        return moved
    corrected = _correction_this_turn(text, memory)
    if corrected:
        more = _answer_the_new_one(memory, memory.get("correction"))
        if isinstance(more, str) and more.strip():
            if _a_rate_changed(text, memory):
                # The figure the person changed is what they put by each month, and the answer
                # they want is how long the goal takes at the new rate. The note about the line
                # they corrected is not news beside it ("Save 500 pounds - got it." names a sum
                # they did not touch), so the new sum is the whole turn.
                return more.strip()
            return corrected.rstrip() + " " + more.strip()
        return corrected
    denied = _denial_this_turn(text, memory)
    if denied:
        return denied
    back = _the_back_this_turn(text, memory)
    if back:
        return back
    retracted = _retraction_this_turn(text, memory)
    if retracted:
        return retracted
    # "my sister lives in perth" then "no, york": the value alone corrects the line before it,
    # and the line before it gave somebody's town, so the correction is the new town and not a
    # shrug that leaves the store saying Perth.
    moved_town = _a_town_moved(memory, text)
    if moved_town:
        return moved_town
    # A plan with something still missing is the ask they did not make: "ive got a wedding in 3
    # weeks and i still havent got an outfit" was filed as a receipt ("Noted: you've got a wedding
    # in 3 weeks and you still haven't got an outfit."), which tells a person with a wedding coming
    # nothing they did not just say. The occasion and the gap are both in the line, so the question
    # is the one the knowledge base answers about the thing that is missing.
    left_out = pending.answer(text, memory) if isinstance(text, str) else None
    if left_out:
        return left_out
    # The ask for their own family name, first name or both: "whats my surname" names a fact the
    # store keeps and the recall table reads as no fact at all, so it was answered "you've not
    # said" - or, with "last name", with their first name. Read early, because a store holding a
    # surname answered "do you know my first name" by reading the surname out, and the readers
    # after this one echo the earlier line. A how-to about a surname ("how do i change my
    # surname") names the world and is left to whoever answers those.
    named = family_name.reply_for(text, memory)
    if named:
        return named
    picked = _the_name_they_picked(text, memory)
    if picked:
        return picked
    called = _what_the_pet_is_called(text, memory)
    if called:
        return called
    picked_again = _the_pick_asked_again(text, memory)
    if picked_again:
        return picked_again
    folded = _folded(text, memory)
    low = MORE_OF_IT.sub(r"\1", _bare(folded))
    told = _a_diet_told(text, memory, low)
    if told:
        return told
    # A pregnancy, or a limit on drink, is a fact about the person they live with - the same kind
    # of thing as a diet or an age, and not something wrong that needs a careful question. The
    # line is said back with their name in it so the person knows it was taken in.
    own = _a_pregnancy_of_their_own(text, memory, low)
    if own:
        return own
    stated = _a_state_told(text, memory, low)
    if stated:
        return stated
    # The same state, said in the past: "my wife was pregnant" is not news now, and the store must
    # not congratulate it or advise on trying for a baby.
    was = _a_state_that_was(text, memory, low)
    if was:
        return was
    disliked = _a_dislike_told(text, memory)
    if disliked:
        return disliked
    # "what should I call it?" a turn after "we're getting a kitten" asks the bot for a name. A
    # name is taste, not knowledge: there is no entry to look up, and "a search should sort you
    # out" is no answer at all - it is the one thing here a friend just gives.
    named = _a_name_for_the_pet(text, memory, low)
    if named:
        return named
    # "who's older, me or my wife", "am i older than my mum", "how much older is she": two ages
    # the store was given, put side by side. The answer is arithmetic on two told facts, which
    # is the store's own business; without both of them the turn stays free for whoever can
    # answer it.
    compared = _age_compare(memory, low)
    if compared:
        return compared
    # "how far along is she" a turn after "my wife is 8 weeks pregnant": the weeks are a fact the
    # chat gave and the store kept, and no knowledge base knows them. The ask names the length,
    # not the person, so the pregnancy the store holds is the answer.
    along = _how_far_along(memory, low)
    if along:
        return along
    # "which one is first", "whose is sooner", "what comes first": two plans with a date each,
    # put in the order the calendar puts them. Like two ages, this is not knowledge about the
    # world - the store is the only place both dates are kept - and without two of them the
    # search hedge is all anyone can say, so the turn stays free.
    ordered = _which_comes_first(memory, low)
    if ordered:
        return ordered
    # "what did i decide to get", "what did we settle on", "which one did i pick": a chat that
    # weighed two things and picked one, asked for the choice it made. The topic's advice took
    # these (dog walking after "actually a dog") because the ask names the thing and not the
    # choice, so the store answers it here.
    settled = decided.answer(text, memory)
    if settled:
        return settled
    # "who is coming with me", "who am i going with": the companion they told the chat about was
    # acknowledged and then dropped, and the search shrug (or, worse, "you haven't told me your
    # name yet") is not what a friend answers.
    coming = company.answer(text, memory)
    if coming:
        return coming
    # "what's my mum's name", "how old is my son": a fact kept about someone they mentioned is
    # answered from that person, the same way "what does my mum eat" is.
    theirs = _relation_reply(memory, low)
    if theirs:
        return theirs
    # "have i told you about my sister", "did i mention the trip": a question about the chat, and
    # the store is the only part of the bot that can answer it. It says the fact, quotes the line
    # they said, or says nothing is kept - the search hedge is wrong on all three.
    # "remember when i said my knee hurt", "remember we talked about lisbon": the same thing as a
    # statement rather than an ask. The word in it is a topic too, so `answers` read the knee and
    # served the advice a second time; the store is the part that can say what was actually said,
    # so the callback is answered here and the line is claimed in `TAKES_AS_IT_COMES`. It is read
    # by the same readers as the ask, so a fact the store keeps is said the same way either side.
    called_back = told_about.callback(text, memory, facts=_told_readers(),
                                      plain=lambda asked: _respond(asked, memory),
                                      claims=lambda: bool(_about_this_chat(text, memory)))
    if called_back:
        return called_back
    remembered = told_about.answer(text, memory, facts=_told_readers(),
                                    plain=lambda asked: _respond(asked, memory),
                                    claims=lambda: bool(_about_this_chat(text, memory)))
    if remembered:
        return remembered
    if WHERE_PLAN.search(low):
        # "where are we going again", "remind me where we're going": the plan carries the place,
        # and nothing in the knowledge base knows they are going anywhere.
        asked = _plans_reply(memory, low)
        if asked:
            return asked
        gone = user(memory).get("plan_dropped")
        if isinstance(gone, str) and gone:
            # They took it back a turn or two ago, so the honest answer names that rather than the
            # empty store. What they took back is a place more often than not - "the isle of skye
            # in june" is five words and a good thing to say back - but a trip with no place in it
            # keeps the whole sentence: "we've booked two weeks in portugal in september" put the
            # line itself in the store, and "We've booked two weeks in portugal in september is
            # off, then" reads as a machine reading a note aloud. The two are told apart by shape,
            # not length: a sentence starts with who is doing it.
            if SAID_AS_A_SENTENCE.match(gone):
                return pick(["That plan is off, then \u2014 where are you going?",
                             "Right, that one is off the record \u2014 where are you headed?",
                             "Scratch that trip, then \u2014 where is it now?"], memory)
            shown = gone[:1].upper() + gone[1:]
            return pick([shown + " is off, then \u2014 where are you going?",
                         "Not " + shown + ", then. Where are you headed?",
                         "Right, " + shown + " is dropped \u2014 where is it now?"], memory)
        return None
    # "when am I moving?", "when is she due?" name a thing and not the date: the date is in the
    # line that stated it, so it comes back on its own. The helper refuses every ask it cannot
    # place, so every line can be offered it.
    # "when is my mums birthday", "when is toms birthday": the date is kept on the person
    # (bot/memory/facts.py, OTHER_BIRTHDAY), so this is memory and not a fact about the world.
    # Without it the ask was answered "I don't have a date from you for that" a turn after the
    # date had been given, which denies what the person just said.
    whose = _a_persons_birthday_reply(memory, low)
    if whose:
        return whose
    # "how many weeks till that", "how long have i got": the date is in a line they said and the
    # answer is the count from today to it. The bot had the date and gave back a hedge or the
    # statutory holiday allowance, so the count is the store's line.
    said_until = until_answer(text, memory)
    if said_until:
        return said_until
    # "where did i say we were going", "how often did i say i go": an ask about what they said, and
    # the answer is the line itself. It comes before the date reader, which took the "say" for the
    # event and answered a question about a trip with "No - that's in February."; the quotation
    # cannot be wrong the way that was, and where nothing matches it says so rather than guessing.
    from ..compose.own_facts import said_back
    the_line_back = said_back(text, memory)
    if the_line_back:
        return the_line_back
    # "did i already go", "have i been yet": the date is filed, but which side of today it is on
    # is a question of its own and "In June." does not answer it.
    said_side = already_answer(text, memory)
    if said_side:
        return said_side
    said_when = when_answer(text, memory)
    # "when's my birthday" is the one when ask the plan reader gets wrong: the birthday is a date
    # they gave once, and a plan that merely mentions one ("my sons birthday is in august") is not
    # their own birthday - reading it as the plan put someone else's date in their mouth. It is
    # kept out of every date the plan holder could answer with, the bare one included.
    a_birthday_ask = recall.ask(text) == "birthday" or recall.ask(low) == "birthday"
    if (WHEN_ASKS.search(low) or WHEN_THING.search(low) or TIME_ASKS.search(low)
            or TIME_THING.search(low) or TIME_IT.search(low) or DAY_THING.search(low)
            or DAY_IT.search(low) or DAY_ASKS.search(low) or WHEN_PLAN.search(low)
            or WHEN_THING_VERB.search(low)) and not a_birthday_ask:
        # "when do I start?" is about the plan that names that verb, when there is one, and
        # "when is the wedding?" about the plan that names that thing. A when ask about
        # something they never told us is left to whoever can answer it.
        prep = _the_prep_day(memory, low)
        if prep:
            return prep
        asked = _plans_reply(memory, low)
        if asked:
            return asked
        if said_when:
            return said_when
        if (WHEN_ASKS.search(low) or TIME_ASKS.search(low) or WHEN_THING_VERB.search(low)
                or DAY_ASKS.search(low)):
            # Nothing here knows the date, but the paragraph the person has just been given may
            # answer it itself: "how long will it take" after the countdown is its opening step.
            part = plans.follow_up(text, memory)
            if part:
                return part
            return None
    elif said_when and not a_birthday_ask:
        return said_when
    # A plan announced is the question its plan implies: "im planning a trip" files the plan and
    # answers nothing, while "how do i plan a trip" reaches the knowledge base. The fact is kept
    # either way; this only decides what the person is told (bot/memory/plans.py).
    planned = plans.answer(text, memory)
    if planned:
        # The paragraph is what the plan implies, and it is kept for the turn that asks for it
        # (observe, above): laying it out unasked answers a question nobody put, where the
        # composer has a warm word and a question for the announcement itself (sturdy-poppy,
        # #1848). So the announcement is not this module's turn.
        return None
    # The turn after that paragraph is a question about one part of the plan ("how do i pick a
    # venue", "when should i book the registrar"): the part has its own sentence in it, and the
    # paragraph again would be the same words twice (bot/memory/plans.py).
    part = plans.follow_up(text, memory)
    if part:
        return part
    if not folded:
        return None
    asked = history.asked(text, memory)
    if asked == "first":
        return _first_reply(memory)
    if asked == "first_bot":
        return _first_bot_reply(memory)
    if asked == "said_about":
        said = _what_i_said_about(memory, history.the_thing_named(text))
        if said:
            return said
    if asked == "topics":
        # A recap ask is answered with the thing we were on, not with every line they have
        # typed put in quotation marks: "what did we talk about" after "im tom and i work as a
        # bus driver" / "my knee is killing me" is about the knee.
        if _summary_ask(low) or TALKED_ABOUT.search(low):
            return _topic_reply(memory, low)
        return _topics_reply(memory)
    handed_back = choose.reply_for(text, memory)
    if handed_back:
        return handed_back
    # "is that enough" is about the amount they just gave, and the answer a turn earlier named the
    # figure to aim at, so the two numbers are read against each other.
    enough = enough_reply(text, memory)
    if enough:
        return enough
    # The other side of handing the choice back: they turn the offer down ("nah not that one",
    # "ive seen all those"). The answer is another of the things the bot itself named a turn
    # ago, or the one question that lets it pick again - never the line said back as a receipt
    # ("Got it - nah not that one"). The reading is in bot/memory/reject.py.
    another_of_them = turned_down.reply_for(text, memory)
    if another_of_them:
        return another_of_them
    # "what else can i try?" after an answer asks for the other half of that answer, not for the
    # same opening line again. The store reads it because what it hands back is its own last
    # answer, and no knowledge entry has it (bot/memory/another.py).
    other = second_half.other_option(text, memory)
    if other:
        return other
    # Going back to something said earlier is read next: the return line is about the
    # conversation, not a new subject, and the topic must move even when the reply itself is left
    # to the modules that answer questions.
    back = _return_reply(text, memory)
    if back:
        return back
    # "do you remember that i live in leeds": the person asks whether the store kept a fact and
    # says the fact. It is their own statement with a frame around it, so it is read as that
    # statement rather than as a question about the bot's memory in general.
    remembered = _remembers_fact(text, memory)
    if remembered:
        return remembered
    # "am i vegetarian?", "is my name sam?" — a yes/no question about the person, answered from
    # what they told you rather than guessed at.
    # "do i eat meat" after "im vegetarian": the rule they gave the store, asked back as a yes/no
    # about a food. It came before the confirmation reader found nothing and the turn fell to a
    # search hedge about a fact the bot had been told a turn earlier.
    ruled_out = _a_rule_on_eating(text, memory)
    if ruled_out:
        return ruled_out
    confirmed = _confirmation(text, memory)
    if confirmed:
        return confirmed
    # "do i like fish?" is a question about a taste they have already told the bot: the store
    # keeps it, so the answer is the taste and not a search hedge. A thing they have never said
    # anything about is left to the other modules.
    if ASKS_FOR_TASTES.search(low):
        liked = _tastes_said(memory)
        if liked:
            return liked
    if TASTE_ASK.search(low):
        said = _taste_reply(memory, low)
        if said:
            return said

    # The shaped reader is the safety net: when none of the store's own readers answers the line,
    # the same ask in words they have no pattern for ("do you remember my budget") is still an
    # ask about what they told you, and it is answered with the reply for that fact. It runs last
    # so a reader that quotes the line ("what did I say about the boiler?") keeps the turn.
    # "how much have i spent", "what did i spend on food": the sum of the sums they told you.
    # It comes before the chat-shaped readers because the thing the ask names is usually the
    # thing the chat is already on ("i spent 300 on food this month" then "how much did i spend
    # on food"), and the store answers that shape with whatever the topic holds - a cooking tip
    # about shopping with a list - instead of with the figure they gave it.
    spend_tally = spent.answer(text, memory) or spent.answer(folded, memory)
    if spend_tally:
        return spend_tally
    general = _general_recall(text, memory) or _general_recall(folded, memory)
    # "what does my mum eat", "is my son allergic to anything": a question about someone the user
    # told us about is answered from that person's own fact, whether or not the chat is still on
    # them, so it comes before the reading of "about this chat".
    # Their own diet is not a question about anyone else: "what's my diet" beside a diet kept
    # for their mum is still about them.
    asks_about_someone = _asks_about_someone(low, text, memory)
    if asks_about_someone:
        # The fact said before the question is context for it, so the question is what the store
        # answers - but only where the store would have answered the line as it stands. On "my
        # wife is allergic to shellfish, can she eat prawns" the answer modules say why prawns
        # are out, and the store's own reply is the thin receipt ("nothing with shellfish in it
        # - that's all I have on food for her"), so a line the store would have left alone is
        # left alone after the split too.
        told = None
        if _other_person_reply(memory, low):
            told = _other_person_reply(memory, _the_ask_after_a_statement(low, memory))
        # A miss is not a denial: when the line brings a fact with it ("is my son allergic to
        # nuts? he had a rash") the store holding nothing about the son is not the answer, and
        # the kitchen entry that can use the nuts gets the turn. What counts as the ask's own
        # words is the ask, so the telling is what is read for it.
        telling = _after_the_yes_no_frame(text) if isinstance(text, str) else ""
        if told and not (NO_RECORD.search(told) and telling
                         and _says_more_than_the_ask(telling)):
            return told
    # The line points at someone the chat never named: "she is 5 next month" then "how old is
    # she". The store keeps facts about a person, and an age about nobody is not one, so the age
    # is read back off the line that gave it, as long as the pronoun is the same one. A person
    # the chat did name, or pointed at with a relation in play ("my brother", then "how old is
    # he"), keeps the answer the store already has.
    who_asked = _named_person(low, memory)
    if not who_asked and re.search(r"\b(?:she|her|he|him)\b", low):
        who_asked = _person_from_pronoun(low, memory)
    if not who_asked and AGE_ASK.search(low):
        pointed = _a_pronoun_age(memory, low)
        if pointed:
            return pointed
    # "how old is my son", "how old are the kids": the number was given with the person, so this
    # is memory rather than a fact about the world, and it is answered before anything guesses.
    aged = _ages_reply(memory, low, folded)
    if aged:
        return aged
    # What is in their own kitchen is not a fact about the world and not one they have told us,
    # so the one thing the store can say is that it cannot see it. The places are a closed list:
    # "what have i got in the diary" is the ask about what is coming up and keeps its answer.
    place = _their_place(low)
    if place:
        return pick(["I can\u2019t see inside your " + place + ", so tell me what\u2019s in there and "
                     "I\u2019ll tell you what it will make",
                     "I\u2019ve no way of knowing what\u2019s in your " + place + ": say what\u2019s in "
                     "it and I\u2019ll find you something to cook",
                     "Nothing in your " + place + " I can see from here. Tell me what\u2019s in it and "
                     "I\u2019ll work something out"], memory).rstrip(".") + "."
    # "whats my sisters name" is the same kind of ask as "how old is my son": the name was given
    # with the person, so the store answers it, and without this it fell to the search hedge.
    counted = _kids_reply(memory, low)
    if counted:
        return counted
    called = _a_relations_name_reply(memory, low, text)
    if called:
        return called
    # "what car do i drive", "what phone have i got": the make they gave with the thing, which
    # the store keeps by the name of the thing (memory["user"]["owns"]). It runs before the
    # chat-shaped readers because "what car do i drive" is about them, not about the topic.
    owned = _a_thing_i_own_reply(memory, low)
    if owned:
        return owned
    # "what do you know about my mum", "tell me about my sister": the whole person the chat has
    # been told about, which the store holds, rather than the search hedge it used to fall to.
    about_person = _about_a_person_reply(memory, low, text)
    if about_person:
        return about_person
    # "whos meg" names the person by the name the chat was given, so it is the same kind of ask
    # read the other way round: the name is the subject and the relation is the answer.
    whom = _who_is_the_name_reply(memory, low)
    if whom:
        return whom
    # "and where does she live" and "where does jane live" are the same ask with the person
    # left to the pronoun or to the name: the chat has said where she lives, so it is answered
    # from the chat rather than left to the search hedge.
    if (_asked_person(memory, low)
            and not (PLACE_ADVICE.search(low) and not PLACE_RECALLED.search(low))):
        return _places_reply(memory, low)
    # "my son isnt" after a limit was given is that limit refused for him, and it is answered as
    # the answer it is rather than as a line about nothing.
    refused = _not_the_same_reply(memory, low)
    if refused:
        return refused
    if not _about_this_chat(text, memory) and not _a_why_line_they_have_answered(text, memory):
        # A question about them that the chat-shaped readers do not claim ("do i drive") is still
        # answered from their own line, and left to the ordinary reply when they never said it.
        # A why-line goes with it - it is about the world, and the store only keeps what they
        # said - unless the store holds the subject it names, where what they said *is* the
        # answer ("my dog is called rex" then "why do we have pets").
        return general or _about_what_they_said(text, memory)
    if re.search(r"\b(?:what|which)\b.*\bmy name\b|\bwho am i\b|^my name$|\bwhat my name\b|"
                 r"\b(?:know|remember) my name\b|\bwhat did (?:i|u|you) (?:say|tell me) my name was\b",
                 low):
        return _name_reply(memory, low)
    if re.search(r"\bmy job\b|\bmy work\b|\bwhat do i do\b|\bwhere do i work\b|"
                 r"\bwhat do i work as\b|\bwhat i (?:do|did)\b|\bfor a living\b", low) \
            or (WHERE_WORK.search(low) and not _doing_again(text, memory)):
        # "what was i saying about my job" asks for the line, not for the role: they can say
        # plenty about a job they never named, and the line said back is the answer to it.
        if _doing_again(text, memory) or (SAID_ABOUT.search(low) and _names_its_thing(low)):
            asked = _topic_reply(memory, low)
            # The store keeps the job, so a callback that found no line about it must not say
            # there is none: the fact it keeps is the answer, and it is said below.
            if asked and not _a_denial(asked):
                return asked
        # "and what do i do there", "who do i work with": a part of the job they never described,
        # so the job said back is the same sentence as the turn before it and answers nothing.
        part = _a_part_of_the_job_never_said(memory, low)
        if part:
            return part
        return _job_reply(memory, where=bool(WHERE_WORK.search(low)))
    # "where was i going with this" is a lost thread, not a place: the place ask is the one
    # that stands on its own.
    # "do you remember what I do?" asks for the job in the store's own words: the frame points
    # back at the fact, and the line ends there ("what i do about that boiler" is a request).
    if re.search(r"\b(?:remember|recall|know)\b[^.]{0,18}\bwhat i (?:do|did)\b\W*$", low):
        return _job_reply(memory)
    if (PLACES_ASK.search(low) and SELF_WORD.search(low)
            and not (PLACE_ADVICE.search(low) and not PLACE_RECALLED.search(low))):
        return _places_reply(memory, low)
    # "what cant i have" and "what did i say i don't eat" name the limit itself: the answer is
    # the limit they gave, not the answer before this one read out again ("It's what I said a
    # moment ago: Plenty: meat, fish..."), and not the line quoted back. It goes before the fact
    # questions because a limit ask is one of them and would otherwise be answered with the fact.
    if recall.ask(text) == "limit":
        limit = _limit_reply(memory, low)
        if limit:
            return limit
    # A how-to in front of "my diet" is advice, not a recall: "how do i get more veg in my
    # diet" wants an idea, and this branch used to answer that it had not been told about the
    # diet. The fact questions keep DIET_ASK.
    if (_asks_for_a_fact(low, text, memory) or (DIET_ASK.search(low) and not DIET_HOW_TO.search(low))
            or _a_count_ask(low) is not None):
        return _fact_reply(memory, low)
    if PLAN_MINE.search(low):
        return _plans_reply(memory, low)
    if FIRST_ASK.search(low):
        return _first_reply(memory)
    if _repeat_ask(text, folded):
        return _repeat_reply(memory, text)
    if SAID_ASK.search(low):
        return _said_reply(memory)
    # "remind me what i told you" with nothing named is the whole chat, not one line of it.
    if re.search(r"^what i (?:told|said)(?: you)?$|^what have i (?:told|said)(?: you)?$", low):
        # Only when the line is the ask: see the anchor note in `_recall_shapes`.
        return _summary_reply(memory)
    # "what did i tell you about me" asks for the whole picture, not one line of it: the same
    # ask in other words ("what do you know about me") is already answered as a summary, so the
    # quote-their-last-line branch below must not take it. A named thing keeps the turn:
    # "what did i say about the boiler" is still about the boiler.
    if re.search(r"\babout me\b|\bof me\b", low):
        return _summary_reply(memory)
    # The ask names the kind of detail, and the line their own words find is the answer.
    kind_said = _an_open_attribute_ask(low, memory)
    if kind_said:
        return kind_said
    if WHAT_I_SAID.search(low) or re.search(
            r"\bwhat was it i said\b|^what i (?:said|told you|mentioned)\b|"
            # "we" only when it names the thing: "remind me what we said about the boiler" is that
            # one recall, and a bare "remind me what we said" is the recap of the whole chat, which
            # `_summary_reply` answers better ("We were on Edinburgh - you asked ...").
            r"^what we (?:said|told you|mentioned)\s+(?:about|on|regarding)\b|"
            r"^anything i (?:said|told you|mentioned)\b|"
            # "i cant remember what i said" is the reminder in the speaker's own words,
            # and the forgetting in front of it is what makes it an ask.
            r"\bi (?:cant|cannot|can not|dont|do not) (?:really |quite )?remember "
            r"what i (?:said|told you|mentioned)\b|"
            r"\b(?:do|can|could|did) (?:you|u) remember what i\b", low) \
            or THING_AGAIN.match(low) or reminded.the_thing(text, memory) \
            or _which_thing_was_it(low, memory) or _an_attribute_they_gave(low):
        said = _recall_reply(memory, low, text)
        if said:
            return said
        # A place in the ask that the chat has never been on is what the ask is about: "what did
        # i say it was like in Lisbon" asks about Lisbon, and recapping the budget answers a
        # question they did not ask. The thing itself is answered by another module.
        # Only when there is something of theirs for the ask to be about: with nothing said
        # before it the store's own "we're still at the beginning" is the honest reply, and a
        # search hedge for a place they only just named is not.
        earlier = [line for line in last_user(memory, 4)
                   if " ".join(str(line or "").split()).lower()
                   != " ".join(str(text or "").split()).lower()]
        if earlier and _a_place_new_to_the_chat(memory, low):
            return general or _about_what_they_said(text, memory)
    if re.search(r"\bmy age\b|\bhow old am i\b|\bhow old did i say\b|"
                 r"\bhow old (?:i am|i was|we are|i(?:'m| am) gon(?:na|e) to be)\b", low):
        # "how old did i say she was" asks about her, and the asker's own age is not the answer
        # to it: with nothing on record for her this line read "I don't know it - you haven't
        # said", which is the person's own age being denied to a question about somebody else.
        # A person the chat knows is answered above, by their own age.
        theirs = re.search(r"\b(?:she|her)\b|\b(?:he|him)\b", low)
        if theirs and not _person_from_pronoun(low, memory):
            return ("You haven't told me how old she is." if re.search(r"\b(?:she|her)\b", low)
                    else "You haven't told me how old he is.")
        return _age_reply(memory)
    # A part of an animal they have already described, asked about with a pronoun or the word
    # for it: "how old is he", "what did i say his age was", "what breed is he". The chat holds
    # the fact, so it is the answer; left to the general readers this was the topic shrug
    # ("Still on the kids: you asked how often you should walk him"), which names the wrong
    # thing and answers a question nobody asked.
    pet = _pet_part_reply(memory, low)
    if pet:
        return pet

    if ASKED_ALL.search(low):
        return _asked_reply(memory)
    if not _about_the_bot_here(memory) and (
            THE_CHAT_ASK.search(low) or TOPIC_ASK.search(low)
            or ACTIVITY_ASK.search(low) or TALKED_ABOUT.search(low)):
        # "what am i planning" is a question about the plans we hold when we hold one; the line
        # they said it in is the fallback.
        if ACTIVITY_ASK.search(low) and (PLAN_WORDS.search(low) or _plan_was_corrected(memory)
                                         or (UP_TO_ASK.search(low)
                                             and _the_line_before_was_a_plan(memory))):
            # "what am i up to?" after "sorry, i meant porto, not lisbon" is about the plan as it
            # stands now: the line they said before the correction names the city they took back.
            asked = _plans_reply(memory, low)
            if asked:
                return asked
            # Nothing is coming up, so the plans reply has nothing to say: the ask is still a
            # plans ask ("what was i planning to do about it?") and the "nothing yet" line below
            # is the answer, not a hedge. Falling out of this branch keeps that.
        else:
            asked = _topic_reply(memory, low, again=bool(ASKING_AGAIN.search(folded)))
            if asked:
                return asked
    if _summary_ask(low):
        # "summarise our chat" asks about the conversation the same way "recap" and "what did we
        # talk about" do, so it gets the same answer: the thing we were on, not the whole of the
        # person. `_summary_reply` stays for "what do you know about me".
        return _topic_reply(memory, low)
    if re.search(r"\bwhat have i told you\b|\bwhat do you (?:know|remember) about me\b|"
                 r"\babout me\b|^what i (?:told|said)(?: you)?$|^what have i (?:told|said)(?: you)?$",
                 low):
        return _summary_reply(memory)
    if PLAN_ASKS.search(low):
        asked = _plans_reply(memory, low)
        if asked:
            return asked
    if "remember" in low and "yesterday" in low:
        return _topic_reply(memory, low)
    return general or _about_what_they_said(text, memory)

def _a_place_new_to_the_chat(memory, low):
    """True when the line names a place nothing said so far named."""
    named = {word.lower() for word in re.findall(r"[a-z][a-z'\-]+", " ".join(str(low or "").split()))}
    places = {word for word in named if word in PLACES or word in extract.COUNTRIES}
    if not places:
        return False
    said = " ".join(" ".join(str(line or "").lower().split())
                    for line in last_user(memory, 12))
    return not any(place in said for place in places)

OWN_ASK = re.compile(
    r"^\W*(?:do|did|does|am|are|is|was|were|have|has|had|can|could)\s+(?:i|we)\b", re.I)

ASK_FILLER = frozenset("""do did does am are is was were have has had can could i we me my
know think say said tell told remember recall really still actually ever even just
much many again any anything something""".split())

NO_THING = frozenset("""you your the and for not out all any get got let put see use try buy pay
one two new old bad big top end way day now why how what who can see say ask own had his her its
our ours mine they them there here then than that this these those very too just also even still
yet ever some but nor same such with from into onto over under off ago lot bit""".split())

def _about_what_they_said(text, memory):
    """A yes-or-no ask the store has no fact for, answered from their own earlier line.

    "do i drive" after "i dont drive" used to answer "I don't know enough to answer that
    honestly", which is not true: they said it one line ago. The words the question names have
    to be in a line they said, all of them, so a question about something they never mentioned
    is left to the ordinary reply rather than answered with a guess.

    Every line they said is read, not the last few. A fact about them does not expire because
    the chat moved on: "i dont drive" ... four turns about a boiler ... "do i drive" answered
    "I'd rather not guess" about something they had told the bot, and a chat that long is an
    ordinary chat. The containment is what keeps it honest, so the newest line that names the
    thing wins: "i passed my driving test" is read after "i dont drive" rather than instead.
    """
    low = " ".join(str(text or "").lower().split()).strip(" ?!.,")
    if not OWN_ASK.match(low) or len(low.split()) > 9:
        return None
    words = {stem(word) for word in re.findall(r"[a-z']+", low)}
    words = {word for word in words
             if len(word) > 3 and word not in ASK_FILLER and word not in NO_THING}
    # A thing named in three letters is still the thing: "car", "job", "dog", "gas".
    words |= {word for word in re.findall(r"\b[a-z]{3}\b", low) if word not in NO_THING
              and word not in ASK_FILLER}
    if not words:
        return None
    said_before = [str(turn.get("user") or "") for turn in (memory.get("turns") or [])
                   if isinstance(turn, dict)]
    newest = " ".join((said_before[-1] if said_before else "").lower().split()).strip(" ?!.,")
    for line in reversed(said_before):
        said = {stem(word) for word in re.findall(r"[a-z']+", str(line or "").lower())}
        if not words <= said:
            continue
        # The newest line about the thing is the one read, and going back past a line that names
        # the thing is still not done ("what can i cook" is not about the thing, so the line about
        # it stands). When the line read is not the last thing they said, something may have
        # changed since: "i dont drive" then "i passed my driving test last week" - the test is
        # one word away from "drive" but "driving" is not "drive", so the older line is the one
        # that matches. It goes back to them as what they said earlier, with the door open, rather
        # than being asserted as true now.
        phrase = _told_phrase(line)
        if phrase:
            # The restater writes contractions out, which leaves "you can not swim": the one place
            # that reads badly is put back the way people say it.
            phrase = phrase.replace("can not", "cannot")
            flat = " ".join(str(line or "").lower().split()).strip(" ?!.,")
            if flat != newest:
                return pick(["Earlier you said " + phrase + " - still the case?",
                             "You said " + phrase + ", earlier in this chat - still the case?"],
                            memory)
            return pick(["You told me " + phrase + ".", "You said " + phrase + "."], memory)
        return None
    return None

AVOID_ADVICE = re.compile(r"\b(?:what|which|anything)\b[^.!?]{0,24}"
                          r"\b(?:avoid|avoids|watch out for|stay away from|stay off)\b", re.I)

BARE_WHAT_I_DO = re.compile(r"^(?:so |and |but )?what (?:do|did) i (?:actually |really |even )?"
                            r"(?:do|say)(?: again)?$", re.I)

def _the_job_was_just_said(memory):
    """True when the line before the ask is where the job was given, and is nothing but the job.

    "what do i do" answers the line it follows, so the job has to be in that line: a turn later
    the chat has moved on and the same words ask about whatever it moved on to. The last line is
    read from the history the store keeps, so a job said two turns back does not wrongly claim
    the ask, and a job the person only implied is not guessed at.

    The line also has to be *only* the job. In "im a builder and i fell off a ladder" the job is a
    detail of a report, and the whole of what the person is asking about is the fall: the ask is
    the emergency, and "You told me you're a builder" in place of the 999 line is worse than any
    entry the store was shadowing. What may stand around the job is the words people frame it
    with - "i work as a", "my job is a", "im a" - and nothing that says anything else.
    """
    job = str(user(memory).get("job") or "").strip().lower()
    if not job:
        return False
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "").strip()
        if not said:
            continue
        if BARE_WHAT_I_DO.match(_bare(said)):
            continue  # the ask again: it answers the line before it too
        return job in said.lower() and _nothing_but_the_job(said, job, memory)
    return False

JOB_LINE_WORDS = frozenset("""i im am is was be being job jobs work works working as in at on for
with of and the a an it its s my our to here so yeah yes ok okay""".split())

def _nothing_but_the_job(said, job, memory):
    """True when the job is all the line said, once the words around it are set aside."""
    rest = str(said).lower().replace(job, " ")
    frame = str(user(memory).get("job_frame") or "").strip().lower()
    if frame:
        rest = rest.replace(frame, " ")
    return not [word for word in re.findall(r"[a-z']+", rest)
                if len(word) > 2 and word not in JOB_LINE_WORDS]

AVOID_REST = re.compile(r"\b(?:avoid|avoids|watch out for|stay away from|stay off)\b(.*)$",
                        re.I | re.S)

EATING = re.compile(r"\b(?:eat|eats|eating|ate|food|foods|meal|meals|cook|cooking|cooked|recipe|"
                    r"recipes|dish|dishes|dinner|lunch|tea\b|breakfast|snack|snacks|restaurant|"
                    r"menu|takeaway|take-away|buffet|party|barbecue|bbq|gluten|dairy|nuts?|"
                    r"allerg\w*|intoleran\w*)\b", re.I)

ALLERGY_SAID = re.compile(r"\b(?:allerg\w*|intoleran\w*|coeliac|celiac)\b", re.I)

def _the_allergy_is_what_is_asked(text, memory):
    """True when an ask for advice about what to avoid is a question about the allergy.

    The answer names a fact, so the fact has to be what is being asked about. Two things say it
    is not, and both stand the store down:

    * a word after the ask that names the thing to avoid. "what should i avoid in the sun" is
      about sunburn and "on the roads" about driving, unless the thing named is something eaten
      ("what should i avoid in a stir fry").
    * an allergy that is not on the table. The store answers a fact it holds, and a chat that
      has moved on to the boiler and then asks what to watch out for is asking about the
      boiler: the last thing answered is what is in front of them, not the allergy. The fact is on the
      table when they said it in this line or the turn before, and when nothing else has been
      said at all.
    """
    rest = AVOID_REST.search(text)
    tail = " ".join(rest.group(1).split()) if rest else ""
    if tail and not EATING.search(tail):
        return False
    said = " ".join(text.split())
    before = last_user(memory)
    if ALLERGY_SAID.search(said) or ALLERGY_SAID.search(before or ""):
        return True
    return not before

def _general_recall(text, memory):
    """A recall ask in any words (bot/memory/recall.py): "what was my name", "do you remember
    my budget?", "where do I live". The words people use for the same ask are endless, so the
    ask is read by its shape - the user plus one thing they told you - and answered with the
    reply the store already gives for that fact. Anything else is a real request: None.
    """
    low = " ".join(text.lower().split())
    # "what should i avoid": advice about the world when the store knows nothing, and the
    # allergy they told you when it does. recall.ask refuses the shape as advice on purpose (it
    # cannot see the store), so the fact answers it here, and only when the fact is what they are
    # asking about - a chat about a holiday is still a question about the sun and the roads.
    if AVOID_ADVICE.search(text) and user(memory).get("allergies") \
            and _the_allergy_is_what_is_asked(text, memory):
        # "Nothing with nuts in it" answers "what should I avoid"; the bare "you told me you're
        # allergic to nuts" repeats the fact at them and leaves the ask unanswered.
        return _limit_reply(memory, low) or _fact_reply(memory, low, "allergy")
    # "i work as a nurse" then "what do i do": the line names nothing, so on its own it is a
    # request for advice, and the knowledge base answered it with the entryways into nursing. What
    # the person means is the job they have just told you. Only right after they said it, because
    # a turn later "what do i do" is about whatever the chat has moved on to, and only when the
    # store holds a job for it to be about.
    if BARE_WHAT_I_DO.match(low) and user(memory).get("job") and _the_job_was_just_said(memory):
        return _job_reply(memory)
    # "what was i saying about my job" asks for the line they said, not for the job as a fact:
    # they can say plenty about the job ("i hate it") without ever naming what they do, and the
    # line said back is the answer. A plain "what is my job" is still the fact.
    # "how much have i spent", "what did i spend on food": the sum is kept from the lines they
    # typed, and the store read none of those lines as a budget, so the ask was answered with a
    # search hedge or a "you haven't told me a budget" that is not what they asked.
    spent_reply = spent.answer(text, memory)
    if spent_reply:
        return spent_reply
    # "how much have i got left", "can i afford a takeaway": the same sums, against the money
    # they said they had. Answered here for the same reason: it is a sum over what they typed,
    # and the answers module had the cheap week or a hedge for it.
    left_reply = spent.what_is_left(text, memory)
    if left_reply:
        return left_reply
    key = recall.ask(text)
    if not key:
        return None
    if SAID_ABOUT.search(low) and _names_its_thing(low) and not _the_fact_is_kept(key, memory):
        # "what was i saying about my job" asks for the line they said, not for the job as a
        # fact: they can say plenty about a job they never named ("i hate it"), and the store
        # holding no job does not mean the chat said nothing about it. With the fact kept, the
        # fact is the answer, and the dispatch below gives it.
        return None
    if key == "name":
        return _name_reply(memory, low)
    if key == "job":
        # "who do i work with", "and what do i do there": a part of the job they never described,
        # so the job said back answers nothing and repeats the turn before it.
        part = _a_part_of_the_job_never_said(memory, low)
        if part:
            return part
        # A where-ask reaches the job through the fact reader too ("do you know where i work"),
        # and the place is the answer when it is kept.
        return _job_reply(memory, where=bool(WHERE_WORK.search(low)))
    if key == "city":
        return _places_reply(memory, low)
    if key in ("birthday", "weight", "height"):
        return _fact_reply(memory, low, key)
    if key == "diet":
        return _diet_reply(memory, low)
    if key in ("allergy", "budget", "pet", "car"):
        return _fact_reply(memory, low, key)
    if key == "limit":
        return _limit_reply(memory, low)
    if key == "me":
        return _summary_reply(memory)
    return None

NAME_ASK = re.compile(
    r"\b(?:what|which)\s+(?:shall|should|would|could|do|can|will|might)\s+(?:i|we|you)\s+"
    r"(?:call|name)\s+(?:it|him|her|them|this|that|the\s+[\w']+)\b"
    r"|\b(?:any|some)\s+(?:good|nice|ideas?|thoughts?)?\s*(?:for\s+)?(?:a\s+)?names?\b"
    r"|\bnames?\s+(?:ideas?|suggestions?)\b"
    r"|\b(?:name|naming)\s+(?:ideas?|suggestions?)\b"
    r"|\b(?:suggest|give me|throw me|help me (?:pick|choose|find|think of)?)\s*(?:me\s+)?"
    r"(?:a\s+|some\s+)?names?\b"
    r"|\bwhat\s+(?:would|do)\s+you\s+(?:call|name)\b"
    r"|\bhelp me name\b", re.I)

def _pet_names(family):
    if family == "cat":
        return CAT_NAMES
    if family in ("rabbit", "hamster", "fish", "parrot"):
        return SMALL_NAMES
    return DOG_NAMES

POINTING = re.compile(r"\b(?:this|that|the|my|our|your|his|her|their|a|an)\s+"
                      r"(?:(?:new|little|baby|poor|first|next|wee|small|own)\s+)?"
                      r"([a-z][a-z']{1,})", re.I)

POINTING_ANY = frozenset("""pet pet's baby name names one thing it him her them pup kit
animal""".split())

def _points_at_something_else(low):
    """True when the line points at a thing that is not an animal ("this song", "my new business").

    Only the word that follows the pointing word is read: "what should i call this song" and
    "what should i call this function in python" name no animal, and the pet in memory is not what
    they are about. A word that names an animal, or that points at nothing in particular ("call it",
    "this one", "a name"), leaves the pet in play.
    """
    for word in POINTING.findall(low or ""):
        if word in extract.ANIMALS or word in POINTING_ANY:
            continue
        return True
    return False

def _the_pet_in_play(low, memory):
    """The animal the naming question is about: the one in the line, or the one just mentioned."""
    named = [word for word in re.findall(r"[a-z']+", low) if word in extract.ANIMALS]
    if named:
        return _animal_family(named[0])
    for turn in reversed((memory.get("turns") or [])[-3:]):
        line = str((turn or {}).get("user") or "").lower()
        said = [word for word in re.findall(r"[a-z']+", line) if word in extract.ANIMALS]
        if said:
            return _animal_family(said[0])
    pets = user(memory).get("pets") or []
    if pets and isinstance(pets[0], dict) and pets[0].get("animal"):
        return _animal_family(pets[0].get("animal"))
    return None

def _a_pet_of_theirs_is_named(low, family, memory):
    """True when the animal the naming ask points at already carries a name in the store."""
    if not re.search(r"\b(?:it|him|her|them|this one|that one)\b", low or ""):
        return False
    for pet in user(memory).get("pets") or []:
        if (isinstance(pet, dict) and pet.get("name")
                and _animal_family(pet.get("animal")) == _animal_family(family)):
            return True
    return False

def _a_name_for_the_pet(text, memory, low):
    """A short list of names for the pet in play, or None when the line is not about naming one."""
    if not NAME_ASK.search(low or ""):
        return None
    family = _the_pet_in_play(low, memory)
    if not family or family == "pet":
        return None
    if _points_at_something_else(low):
        return None
    if _a_pet_of_theirs_is_named(low, family, memory):
        # "what shall i call him" a turn after the name was settled is not a request for three
        # more names: the pet in play has one, and the store answers with it.
        return None
    pool = list(_pet_names(family))
    # A different three each time, so asking twice does not get the same list back.
    seed = len(memory.get("turns") or []) * 7919 + sum(ord(c) for c in str(text).lower())
    shuffled = random.Random(seed).sample(pool, 3)
    advice = NAME_ADVICE[seed % len(NAME_ADVICE)]
    animal = _a(family)
    return ("For " + animal + ": " + ", ".join(shuffled[:-1]) + " or " + shuffled[-1] + ". "
            + advice)

def _count_of_a_kind(pets):
    """How many animals are in this group, when one of them says how many there are.

    A store can hold the same animal twice: "we have two cats, milly and fred" keeps an entry per
    name, and a later "sorry, 3 cats" moves the count onto the first of them. Adding those up
    says four. A count that was said as a correction is a total for that animal, so when one entry
    carries a number at least as big as the group, that number is the group's count.
    """
    said = [int(p.get("count") or 0) for p in pets if int(p.get("count") or 0) > 1]
    if said and max(said) >= len(pets):
        return max(said)
    return sum(int(p.get("count") or 1) for p in pets)

def _return_reply(text, memory):
    """Greet a return to an earlier topic: "ok back to the boiler", "as I was saying, Rome".

    Only when the line names a topic already talked about and asks nothing itself: "back to the
    laptop, which would you get?" carries a question, so the answer modules deal with it with the
    topic put back in front. Asking what they want to know is right here, because the person went
    back to the topic but did not say what they wanted from it.
    """
    record = resumed(memory)
    if not record or record.get("asks"):
        return None
    thing = (record.get("asked") or "").strip()
    if not thing or len(thing.split()) > 4:
        return None
    return pick([line.format(thing=_same_case(thing, text)) for line in RESUME], memory)

def _same_case(thing, text):
    """Keep a name a name: someone typing "as I was saying, Rome" gets "Back to Rome"."""
    for word in text.split():
        if word.strip(" ,.!?").lower() == thing.lower() and word[:1].isupper():
            return thing[:1].upper() + thing[1:]
    return thing

def _name_reply(memory, low=""):
    who = name(memory)
    plan = user(memory).get("plan") or ""
    if who and plan and re.search(r"\bplan(?:ning|s)?\b|\bdoing\b|\bup to\b", low):
        first, rest = plan[:1], plan[1:]
        clause = first.lower() + rest if not rest[:1].isupper() else plan
        return "You're " + who + ", and you're planning " + clause.rstrip(".") + "."
    if not who:
        # The store says which fact it asked for, so the answer is read as that fact and not as
        # whatever the wording of the line happens to look like: every "I don't know it" line is
        # the same shape, and the age ask must not open the door for a name.
        memory["asked_for"] = "name"
        return pick(["You haven't told me your name yet.", "I don't know it yet — you haven't said."],
                    memory)
    return pick(["You're " + who + ".", who + " — you told me.", "Your name's " + who + "."], memory)

def _the_day_of(plan):
    """The day the plan falls on, as somebody would answer "what day?": "on friday" -> "On Friday".

    A numbered day is a day too ("my driving test is on the 14th" -> "On the 14th."), and it is
    the day the plan holds, so it answers the same ask. "" when the plan names neither, so the
    caller can stand aside for whoever can answer the day asked for.
    """
    said = str(plan or "").lower()
    found = WEEKDAY_WORD.search(said)
    if found:
        return "On " + found.group(0).capitalize() + "."
    number = DAY_OF_MONTH.search(said)
    if number:
        return "On the " + number.group(1) + "."
    return ""

def _at_the_clock(plan):
    """The hour the plan says, as somebody would answer "what time?": "at 6" -> "At 6".

    "" when the plan carries no time of day, so the caller can say the plan itself instead: "my
    driving test is on the 14th" answers "what time is my driving test" with the day it has.
    """
    found = AT_TIME.search(str(plan or ""))
    if not found:
        return ""
    said = " ".join(found.group(0).split())
    return "At " + said[3:] + "." if said.lower().startswith("at ") else ""

POINTS_BACK_AT_IT = re.compile(
    r"\b(?:for|to|about|with|on|before|after|from|into|of|at)\s+(?:it|that|this)\b", re.I)

SETTING_OUT = re.compile(
    r"\b(?:leave|leaves|leaving|left|set off|setting off|set out|setting out|travel|travelling|"
    r"traveling|head off|heading off|go|going|get going)\b", re.I)

STUDY_PLAN = re.compile(
    r"\b(?:exam|exams|revision|revise|revising|revised|past paper|past papers|mock|mocks)\b",
    re.I)

def _the_day_before(plan):
    """The weekday the plan is on and the one before it, or None when it names no weekday.

    "i have a big work thing on friday" is on friday, so its prep is thursday. A weekday with a
    month or a day of the month is a date in the calendar ("friday 3 may") rather than this
    week's, and the day before it is not known from the name alone.
    """
    low = " ".join(str(plan or "").lower().split())
    found = [day for day in WEEK if re.search(r"\b" + day + r"\b", low)]
    if len(found) != 1:
        return None
    if MONTH_WORD.search(low) or DATE_PHRASE.search(low):
        return None
    day = found[0]
    return day, WEEK[WEEK.index(day) - 1]

def _the_prep_day(memory, low):
    """The plan and the day the work for it goes on, or None when the store cannot say.

    "when is the best time to prep for it" after "i have a big work thing on friday" is a timing
    ask the store can answer only because it knows the day: the plan said back is what they just
    told it, so the reply has to add the prep day, which is the bit they cannot work out from
    what they said. Without a weekday in the plan there is nothing to add, and the ask is left to
    whoever can answer it: the same words about a passport or a flight have an answer of their
    own, and "You need to renew your passport." is no answer at all.
    """
    if not POINTS_BACK_AT_IT.search(low) or not _a_plan_answers(memory, low):
        return None
    back = POINTS_BACK_AT_IT.search(low)
    if SETTING_OUT.search(low[max(0, back.start() - TAIL_WINDOW):back.start()]):
        return None      # "when is the best time to leave for it" is about setting out
    known = user(memory)
    plans = [p for p in (known.get("plans") or []) if isinstance(p, str) and p.strip()]
    latest = known.get("plan")
    if isinstance(latest, str) and latest.strip() and latest not in plans:
        plans.append(latest)
    for plan in reversed(plans):
        if STUDY_PLAN.search(plan):
            continue     # studying for an exam has an answer of its own
        dated = _the_day_before(plan)
        if not dated:
            continue
        day, before = dated
        said = plan_sentence(plan, plan_line(memory, plan)).rstrip(".")
        return (said + ", so " + before.title() + " is the day for the prep \u2014 keep " + day
                + " itself for the last bits.")
    return None

def _a_plan_answers(memory, low):
    """True when a when or time ask that names nothing of its own is answered by a plan.

    The ask has to be one of the store's own shapes, and the part after its head has to name
    nothing: "when is the best time to prep for it", "when do i start", "what time is my
    appointment". "when is the next full moon" names a moon, so it is about the world and the
    knowledge base keeps it, and so does an ask the plans cannot answer. The hedge for a chat
    with nothing coming up is not a plan either, so a claim is never made on it.
    """
    for pattern in (WHEN_ASKS, WHEN_THING, TIME_ASKS, TIME_THING):
        found = pattern.search(low)
        if not found:
            continue
        if _names_something_of_its_own(low, found.end()):
            return False
        reply = _plans_reply(memory, low)
        return bool(reply) and reply not in NO_PLANS_REPLY
    return False

def _the_date_behind_that(memory, low, plans):
    """"And what date is that" after the calendar has been read out is a date, not the plan.

    The pronoun points at the last thing said. Said back a plan ("You're moving to bristol in
    june"), the plan is what it means and WHEN_PLAN answers it. Said a reading of the calendar
    ("It's Saturday, 7 November."), it is the day the plan names, and what they asked for is the
    date of that day: the plan's weekday is worked out as a date ("Monday is 2 days away, on 9
    November") instead of their own news handed back. None when the last answer was not the
    calendar, or when the plan names no weekday, so the plan reading keeps those lines.
    """
    if not THAT_DATE.search(low) or not CALENDAR_SAID.search(str(last_bot(memory) or "")):
        return None
    for plan in reversed(plans):
        day = WEEKDAY_WORD.search(plan.lower())
        if day:
            worked = solve("what date is " + day.group(0), {}, memory)
            if worked:
                return worked
    return None

_A_DATE_AT_THE_END = re.compile(
    r"^(?P<subject>.*?)\s+(?P<date>(?:in|on|at|next|this)\s+[a-z0-9' ]+\.?)$", re.I)

def _the_whole_word_in(text, word):
    """Where the word sits in the line as a word of its own, or -1.

    "when are my exams again" holds "exam", but only as the front of "exams", and the letter left
    over was read as the verb the ask named: the plan "exam on the 14th of june" came back "Your
    exam ses is on the 14th of June". The plural is the same thing said again, and the plan said
    as it is answers it.
    """
    if not word:
        return -1
    found = re.search(r"(?<![\w'])" + re.escape(word) + r"(?![\w'])", str(text or ""))
    return found.start() if found else -1


def _third_person(word):
    """The form a verb takes after "he": "start" -> "starts", "go" -> "goes", "try" -> "tries"."""
    word = str(word or "").strip(".,!?;:")
    if not word or not word.isalpha():
        return word
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    if word.endswith("o") and len(word) > 1 and word[-2] not in "aeiou":
        # "go" is "goes" and "do" is "does", not "gos" and "dos".
        return word + "es"
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"

def _the_line_that_said(memory, plan):
    """The recent line that carries the plan, for a plan the log kept as one of several.

    "my niece turns 5 in may and my nephew in june" logs both halves under one line, and
    `plan_line` only finds the first of them: the second half's own words are still in the line
    they said, which is where the verb it left out is."""
    wanted = " ".join(str(plan or "").lower().split())
    if not wanted:
        return None
    for line in reversed(last_user(memory, 6) if isinstance(last_user(memory, 6), list) else []):
        if wanted in " ".join(str(line).lower().split()):
            return line
    return None

def _the_verb_from_the_line(plan, line):
    """The words the other half of the line carries, for a half that was left without a verb.

    "my niece turns 5 in may and my nephew in june" keeps "my nephew in june", and the ask that
    names nothing ("when is my nephew") has no verb to put back: what the half left out is still
    in the line, in the other half's own words ("turns 5")."""
    wanted = " ".join(str(plan or "").lower().split())
    text = " ".join(str(line or "").split())
    if not wanted or not text:
        return ""
    for piece in re.split(r"\s+and\s+|,|;", text):
        clause = " ".join(piece.split()).strip(" ,.;:-!")
        if not clause or " ".join(clause.lower().split()) == wanted:
            continue
        match = _A_DATE_AT_THE_END.match(clause)
        if not match:
            continue
        # The other half is "my niece turns 5": the determiner and the person, then the words
        # that are left are what the half this ask names was never given ("turns 5").
        before = match.group("subject").split()
        if len(before) < 3 or before[0].lower() not in ("my", "our", "the", "his", "her", "their"):
            continue
        body = " ".join(before[2:]).strip(" ,")
        words = body.split()
        if not words or len(words) > 4 or not words[0].isalpha():
            continue
        # A small count in the other half is said in words when the half is said whole: "my
        # nephew turns 5 in june" is "Your nephew turns five in June".
        words = [_a_number_word(word) if word.isdigit() and len(word) < 3 else word
                 for word in words]
        body = " ".join(words)
        # a half it cannot stand on its own is not a verb: "is" alone says nothing about the day
        if words[0].lower() in ("is", "are", "was", "were", "am"):
            continue
        return body
    return ""

def _the_verb_they_asked(plan, low, line=""):
    """The plan with the verb the ask named put back into it: "my course in february" is what a
    line with two things in it keeps of "i start my new job in january and my course in
    february", and "when does my course start" names the word the half left out.

    Only a plan with a date at the end and nothing but the thing before it, so the phrase the ask
    gives is the verb of that thing and not the rest of the question.
    """
    text = " ".join(str(plan or "").split())
    match = _A_DATE_AT_THE_END.match(text)
    if not match:
        return plan
    subject = match.group("subject")
    # "my daughters" is the thing, and "is" is the verb with its predicate left out: the ask
    # ("when is my daughters birthday") has the predicate, and it goes before the date.
    if subject.split()[-1] in ("is", "are", "was", "were"):
        subject = " ".join(subject.split()[:-1])
    asked = " ".join(str(low or "").split()).strip("?.! ")
    at = _the_whole_word_in(asked, subject)
    if at < 0:
        return plan
    rest = asked[at + len(subject):].strip()
    if not rest or rest in ("again", "now", "this year", "next year"):
        # The ask names nothing the half left out, so the line it came from does: a half that keeps
        # no verb is completed from the other half's words, and said whole.
        borrowed = _the_verb_from_the_line(plan, line)
        if borrowed:
            return subject + " " + borrowed + " " + match.group("date")
        return plan
    words = rest.split()
    if len(words) > 4:
        return plan
    # The verb the person asked with, in the form it takes about a thing of theirs. A word that is
    # not a doing word ("birthday" in "when is my daughters birthday") is the predicate left out
    # of the plan, and it is said as it is.
    doing = ("birthday", "bday", "dob", "date of birth", "name")
    if words[0].lower() in doing:
        return subject + " " + rest + " is " + match.group("date")
    if words[0].lower().endswith("ing") and len(words[0]) > 4:
        # "when is my nephew turning 5" is the doing word as it is, with the "is" it needs: a
        # third person "turnings" is not a word.
        return subject + " is " + " ".join(words) + " " + match.group("date")
    if words[0].lower() in ("is", "are", "was", "were", "will", "would", "can", "could",
                            "has", "had", "does", "did"):
        return subject + " " + " ".join(words) + " " + match.group("date")
    if words[0].lower().endswith("s") and not words[0].lower().endswith("ss"):
        # A word already said in the plural after the thing is more of the thing, not the verb:
        # "when are my dentist appointments" is the appointment they told me about, and reading
        # "appointments" as a verb made "Your dentist appointmentses is on the 3rd of June". A verb
        # the ask names comes in the form the ask is built with ("when does my course start"), and
        # a verb misspelled in the plural loses nothing by being left out.
        return plan
    words[0] = _third_person(words[0])
    return subject + " " + " ".join(words) + " " + match.group("date")

def _plans_reply(memory, low):
    """What is coming up, in the words they said it in: the one plan, or the newest of several."""
    known = user(memory)
    plans = [p for p in (known.get("plans") or []) if isinstance(p, str) and p.strip()]
    latest = known.get("plan")
    if isinstance(latest, str) and latest.strip() and latest not in plans:
        plans.append(latest)
    worked = _the_date_behind_that(memory, low, plans)
    if worked:
        return worked
    if WHERE_PLAN.search(low) or WHEN_PLAN.search(low):
        # "where are we going again" and "which month are we going" are the trip said back. The
        # newest plan is the one they mean, and the sentence it came from says both parts of it.
        # Said whole it is the same sentence the turn before already gave, word for word, so an ask
        # that names one part gets that part: "Portugal.", "In August."
        if plans:
            # The sentence the plan came from still has the verb in it, which is what says a
            # place is a place: "i'm going to the gym tomorrow" is the gym, and the plan kept
            # without it ("house in june") is no place at all.
            said = plan_line(memory, plans[-1])
            part = the_part_asked(plans[-1], low, said, _a_place)
            if part and content(part) != content(str(last_bot(memory) or "")):
                # Unless it is the answer the bot has just given: the part asked for a second time
                # in the same words is the repeat the "Same answer" framing is for, and the plan
                # itself says something this turn.
                return part
            return plan_sentence(plans[-1], said) + "."
        return None
    clock = TIME_ASKS.search(low)
    if clock:
        # "what time am I meeting sam?" is the plan that names that verb, answered with its hour.
        plan = _the_one_asked([p for p in plans if _says_the_verb(p, clock.group(1))],
                              low[clock.end():])
        if plan:
            return _at_the_clock(plan) or plan_sentence(plan, plan_line(memory, plan)) + "."
        return None
    hour = TIME_THING.search(low)
    if hour:
        plan = _the_one_asked([p for p in plans if _names_the_thing(p, hour.group(1))],
                              low[hour.end():])
        if plan:
            return _at_the_clock(plan) or plan_sentence(plan) + "."
        return None
    pointed_clock = TIME_IT.search(low)
    if pointed_clock:
        # "what time was that again" points at the plan on the table, and the hour it names is the
        # answer. A plan with no hour on it does not answer it: the ask is then about the clock in
        # the room, which the calendar says, so the store stands aside instead of saying their
        # sentence back ("the meeting is at 3" was no answer to "what time was that again").
        if plans:
            return _at_the_clock(plans[-1])
        return None
    day_asked = DAY_ASKS.search(low)
    if day_asked:
        # "what day do i start" is the plan that names that verb, answered with its day: the day is
        # what was asked for, so it is the whole answer ("On Tuesday.").
        plan = _the_one_asked([p for p in plans if _says_the_verb(p, day_asked.group(1))],
                              low[day_asked.end():])
        if plan:
            return _the_day_of(plan) or plan_sentence(plan, plan_line(memory, plan)) + "."
        return None
    day = DAY_THING.search(low)
    if day:
        plan = _the_one_asked([p for p in plans if _names_the_thing(p, day.group(1))],
                              low[day.end():])
        if plan:
            return _the_day_of(plan) or plan_sentence(plan, plan_line(memory, plan)) + "."
        return None
    pointed_day = DAY_IT.search(low)
    if pointed_day:
        # "what day is it on" is the plan's day and not today's: with a plan on the table that
        # names a weekday, the weekday is the whole answer. A plan with no weekday on it does not
        # answer it - "i need to ring the bank tomorrow" then "what day is it on" asks what day
        # today is, and "im going to rome" asks the trip - so nothing is said rather than the
        # person's own sentence handed back, and the calendar and the trip answer are left to
        # answer it as they did before.
        if plans:
            return _the_day_of(plans[-1])
        return None
    when = WHEN_ASKS.search(low)
    if when:
        # The plan that names the verb they asked about answers "when do I start?".
        plan = _the_one_asked([p for p in plans if _says_the_verb(p, when.group(1))],
                              low[when.end():])
        if plan:
            day = _the_day_of(plan)
            if day and _the_day_is_the_whole_date(plan) and _the_plan_was_just_said_back(memory, plan):
                # "i begin my new job on monday" / "sorry i meant tuesday" is answered "Got it -
                # you begin your new job on Tuesday.", and "when do i start" then wants the day:
                # the plan read back is that same sentence twice, a line apart.
                return day
            return plan_sentence(_the_verb_they_asked(plan, low, plan_line(memory, plan)
                                        or _the_line_that_said(memory, plan)),
                                 plan_line(memory, plan)) + "."
        # A half of a line with two things in it keeps no verb ("i start my new job in january and
        # my course in february" keeps "my course in february"), and the ask names the verb the
        # half left out: "when does my course start" is that plan with "start" put back.
        halves = [p for p in plans if _the_verb_they_asked(p, low) != p]
        plan = _the_one_asked(halves, "") if halves else None
        if plan:
            return plan_sentence(_the_verb_they_asked(plan, low, plan_line(memory, plan)
                                        or _the_line_that_said(memory, plan)),
                                 plan_line(memory, plan)) + "."
        # "when do i go on holiday?" asks when the trip is without naming the plan by its verb:
        # the line says it is a trip, so a plan that is one answers it.
        if SAYS_A_TRIP.search(low):
            for plan in reversed(plans):
                if _about_kind("trip", plan, memory, phrase=True):
                    return plan_sentence(plan, plan_line(memory, plan)) + "."
        return None
    thing = _when_thing(low, wide=not plans)
    if thing:
        # The plan that names the thing they asked about answers "when is the wedding?".
        asking = [p for p in plans if _names_the_thing(p, thing, memory)]
        if _asks_the_end(low) or _asks_the_start(low):
            # "when does my job end" is not answered by the day it starts, and "when does my
            # course start" is not answered by the day it finishes. A plan that says the end
            # they asked about (or the start) still answers it.
            asking = [p for p in asking if _answers_the_end_asked(p, low)]
        plan = _the_one_asked(asking, "")
        if plan:
            day = _the_day_of(plan)
            if day and _the_day_is_the_whole_date(plan) and _the_plan_was_just_said_back(memory, plan):
                # The plan said back a line ago ("Got it - your exam is on the 15th.") is the same
                # sentence twice when the ask comes again: the date is what was asked for.
                return day
            return plan_sentence(_the_verb_they_asked(plan, low, plan_line(memory, plan)
                                        or _the_line_that_said(memory, plan)),
                                 plan_line(memory, plan)) + "."
        # The thing is named but nothing they told us is about it: not a plans answer at all.
        return None
    if WHEN_THING.search(low) and re.search(r"\b(?:bank|public)\s+holiday", low):
        # A when ask about a bank holiday names something too vague to be a plan, and nothing
        # they told us is about it. That is a question about the calendar, not about their own
        # plans, so this is not the place to answer it: it fell through to "nothing so far, you
        # haven't mentioned anything coming up". A vaguer "when is the next holiday" can be
        # either, and the nothing-so-far line is a fair answer to it.
        return None
    if _thing_is_a_quality(low):
        return None
    if not plans:
        if _a_time_for_the_job_itself(low):
            # "when is the best time to do it" is about the job in front of them, not about their
            # calendar. With nothing in the store the empty-store line is a wrong-subject answer:
            # it was said to somebody who had just asked about the mould on their courgette
            # leaves ("You haven't told me about anything coming up yet. What's on?"). Whoever
            # can answer the job keeps the turn, and a plan they do have still answers these
            # through the branch above.
            return None
        return pick(list(NO_PLANS_REPLY), memory)
    if _the_answer_about_it_is_on_the_screen(memory, plans[-1], low):
        # The answer this plan's own line was given is what the person is asking for again, and the
        # plan said back is only their own words: stand down so the answer can be framed as the
        # repeat it is.
        return None
    said = [plan_sentence(plan, plan_line(memory, plan)) for plan in plans[-2:]][::-1]
    if len(said) == 1:
        return with_a_tail(said[0] + ".", memory)
    return said[0] + ". And " + said[1][:1].lower() + said[1][1:] + "."

THEIR_PLACES = frozenset("fridge freezer cupboard cupboards pantry larder".split())

IN_A_PLACE = re.compile(r"\bwhat (?:have|has) (?:i|we) got (?:in|on) (?:the|my|our)\s+(\w+)")

IN_MY_PLACE = re.compile(r"\bwhat(?:'s| is|s)?\s+(?:in|on) (?:the|my|our)\s+(\w+)")

FOR_A_MEAL = re.compile(r"\bwhat (?:have|has) (?:i|we) got (?:for|in) (?:dinner|lunch|tea|supper|"
                        r"breakfast)\b|\bwhat(?:'s| is|s)\s+for (?:dinner|lunch|tea|supper)\b")

def _their_place(low):
    """The place they asked about, when the line asks what is in one of their own food places."""
    for pattern in (IN_A_PLACE, IN_MY_PLACE):
        found = pattern.search(low)
        if found and found.group(1) in THEIR_PLACES:
            return found.group(1)
    if FOR_A_MEAL.search(low):
        return "fridge"  # what to have for dinner is answered from what is in it
    return None

def _naming_words(text):
    """The words of a line that name something, in one spelling both sides compare them in."""
    return [word for word in _topics.words(text or "")
            if word not in _topics.STOPWORDS and len(word) > 2]

def _the_day_is_the_whole_date(plan):
    """True when the day is all the plan says about when, so the day is the whole answer.

    "your exam is on the 4th of June" answered with "On the 4th." loses the month, and "your
    dentist is at 3 on Thursday" answered with "On Thursday." loses the hour: a plan with a month
    or a clock on it is said back whole, because the day alone is less than what they told us.
    """
    low = str(plan or "").lower()
    if _at_the_clock(plan):
        return False
    return not any(re.search(r"\b" + name + r"\b", low) for name in extract.MONTHS)

def _the_plan_was_just_said_back(memory, plan):
    """True when the reply above is this plan in the store's own words.

    The confirmation of a correction ("Got it - you begin your new job on Tuesday.") is the plan
    said back, so the ask that follows it wants the part it asks for rather than the sentence
    again. Only the words of the plan count: a warm word about the news, or an answer about it,
    shares nothing with the plan and leaves the plan the answer.
    """
    mine = set(re.findall(r"[a-z']+", str(plan or "").lower()))
    if len(mine) < 3:
        return False
    said = set(re.findall(r"[a-z']+", str(last_bot(memory) or "").lower()))
    return len(mine & said) >= max(3, -(-len(mine) * 7 // 10))

def _the_answer_about_it_is_on_the_screen(memory, plan, text):
    """True when the last line on the screen is the answer the plan's own line was given.

    "im training for a marathon in may" is answered out of the knowledge base with a programme, and
    "what am i doing this week" is answered by that same programme: reading the plan back with a
    question after it ("You're training for a marathon in may. What do you want to have ready for
    it?") is the plan they just said rather than the answer, and it takes the turn from the repeat.
    The plan read back is only a repeat of their own words, so it adds nothing when the answer
    already said what the line asks about - "what am i doing this week" after the training answer
    is "week", and the answer spends three runs a week.

    Three things stop it being the same answer. The answer has to be a real answer: a hedge says
    nothing to repeat, and neither does a line that asked them something back or only acknowledged
    the plan ("Got it - I have to leave for the airport at 5"). And it has to say what this ask
    names: "what am i planning" names planning, and what to see in Spain says nothing about it, so
    there the plan is still the answer.
    """
    mine = {word for word in str(plan or "").lower().split()
            if word.isalpha() and len(word) > 2 and word not in _topics.STOPWORDS}
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not mine or not isinstance(turns, list) or not turns:
        return False
    asked = set(_naming_words(text))
    if not asked:
        return False  # a bare "what am i up to" asks for the plan itself
    screen = set()
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        on_screen = str(turn.get("bot") or "").strip()
        if not on_screen:
            continue
        if _topics.only_acknowledges(on_screen):
            continue  # a courtesy between the two asks is not the answer leaving the screen
        screen = set(_naming_words(on_screen))
        break
    if not screen:
        return False
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        named = mine & set(_topics.keywords(str(turn.get("user") or "")))
        if not (len(named) >= 2 and len(named) * 2 >= len(mine)):
            continue
        answer = str(turn.get("bot") or "").strip()
        if not answer:
            continue  # the turn in hand, before anything has been said back
        if (_HEDGE.search(answer) or answer.endswith("?")
                or len(answer.split()) <= _topics.SHORT_TURN):
            return False
        if not asked & set(_naming_words(answer)):
            return False  # the answer says nothing about what this ask names
        return bool(screen) and bool(screen & set(_naming_words(answer)))

def _a_time_for_the_job_itself(low):
    """Whether the when ask is about the best time for a job rather than about their calendar."""
    for pattern in (WHEN_THING, TIME_THING):
        found = pattern.search(low)
        if not found:
            continue
        said = re.findall(r"[a-z][a-z'-]*", found.group(1))
        if said and all(word in WHEN_QUALITY for word in said):
            return True
    return False

def _thing_is_a_quality(low):
    """True when a when ask names a quality of the world and nothing of its own.

    "when is the best time to take a mortgage" names no plan of theirs; "when is the best time to
    prep for it" names nothing at all beyond a verb and a word that points back at the plan they
    told us, so that plan is still its answer.
    """
    found = WHEN_THING.search(low)
    if not found:
        return False
    said = [word for word in re.findall(r"[a-z][a-z'-]*", found.group(1))]
    if not said or any(word not in WHEN_QUALITY for word in said):
        return False
    return _names_something_of_its_own(low, found.end())

def _names_something_of_its_own(low, start):
    """Whether the rest of the line names a thing, rather than a verb and a word pointing back."""
    for word in re.findall(r"[a-z][a-z'-]*", low[start:]):
        if (word in STOPWORDS or word in WHEN_VERB or word in POINTS_BACK or word in WHEN_QUALITY
                or word in WHEN_VAGUE or len(word) < 3):
            continue
        return True
    return False

def _when_thing(low, wide=False):
    """The thing a when ask names, as a content word: "when is the wedding" -> "wedding".

    "" when there is nothing definite named ("when is the next full moon"), which keeps a
    question about the world out of the store's plans.

    `wide` reads past a vague lead word, because English puts one where the thing should be:
    "when is the *next* general election", "when is the *next* bank holiday", "when is the
    *next* leap year". Reading only the first word left the thing invisible, so the line reached
    the empty-store line ("Nothing so far - you haven't mentioned anything coming up") in front
    of an answer the bot already has. Only a content word counts, and a phrase that is still
    vague after the lead ("the next time we meet", "my next thing") gives nothing, so the asks
    about their own diary keep the store's answer. Used where nothing they told us is a plan, so
    a conversation that has plans in it is read exactly as it was.
    """
    found = WHEN_THING.search(low) or WHEN_THING_VERB.search(low)
    if not found:
        return ""
    said = keywords(found.group(1))
    if wide and said and all(word in WHEN_VAGUE for word in said):
        for word in re.findall(r"[a-z][a-z'-]*", low[found.end():])[:4]:
            words = keywords(word)
            if not words:
                continue
            if words[0] in WHEN_VAGUE:
                return ""  # "the next time we meet" is still their own diary
            said = words
            break
    for word in said:
        if word not in WHEN_VAGUE:
            return word
    return ""

def _the_one_asked(matching, rest):
    """Which of the plans that fit the ask is the one they mean, or "" when none fits.

    Two plans can say the same verb: "im meeting sam at 6 tomorrow" and "im meeting jo at 8 on
    friday" both answer "what time am i meeting". The ask usually goes on to name the thing it
    wants ("meeting **sam**"), so the plan that also names a word of the ask is the one they
    mean, and the newest of those when several do. Only when the ask names nothing after the
    verb is the newest plan that fits the answer, which is what a store can honestly do.
    """
    asked = content(rest) if rest else []
    if asked:
        for plan in reversed(matching):
            if any(_names_the_thing(plan, word) for word in asked):
                return plan
    return matching[-1] if matching else ""

def _ask_verb(low):
    """The verb the ask puts after the thing: "when does my job end" -> "end"."""
    found = WHEN_THING_VERB.search(low)
    return found.group(2) if found else ""

def _asks_the_end(low):
    """Whether the ask wants the end of the plan rather than when it happens."""
    verb = _ask_verb(low)
    return bool(verb) and stem(verb) in WHEN_END_ASK

def _asks_the_start(low):
    """Whether the ask wants the beginning of the plan."""
    verb = _ask_verb(low)
    return bool(verb) and stem(verb) in WHEN_START_ASK

def _says_the_end(plan):
    """Whether the plan's own words name its end: "i finish my course in june" does."""
    return any(word.strip(".,!?;:").lower() in WHEN_END_WORD
               or stem(word.strip(".,!?;:")) in WHEN_END_WORD for word in (plan or "").split())

def _answers_the_end_asked(plan, low):
    """Whether the plan answers the end of it the ask names: a plan that says its end answers
    "when does my holiday end", and one that says neither end can only be about the date they
    gave it. A plan the ask's own verb names ("when does my course start" against "i start my
    course in june") is about that end and answers it."""
    verb = _ask_verb(low)
    if verb and _says_the_verb(plan, verb):
        return True
    if _asks_the_end(low):
        return _says_the_end(plan)
    return not _says_the_end(plan)

def _names_the_thing(plan, thing, memory=None):
    """True when the plan is about that thing: "wedding" is in "my sister's wedding is next
    june". A plan about something else is not the plan they asked about.

    A thing that is a kind of plan ("the trip", "the holiday") is about the plan by its shape and
    not by its word: nobody writes "trip" on a plan that says "Lisbon in may".

    The plan is kept as content words, which are singular ("the vets at 4.30" keeps "vet"), and
    the ask is the person's own word ("what time is the vets"), so both sides are read for their
    forms: a plural in the ask is the same thing as the singular the store keeps.
    """
    for word in content(plan):
        for key in [thing] + content(thing):
            if key == word or key in forms(word) or word in forms(key):
                return True
    return _about_kind(thing, plan, memory, phrase=True)

def _says_the_verb(plan, verb):
    """True when the plan names that verb: "start" is in "i start my new job on monday"."""
    verb = verb.lower()
    forms = {verb, verb + "s", verb + "ing", verb + "ed"}
    if verb.endswith("e"):
        forms |= {verb[:-1] + "ing", verb + "d"}
    if verb.endswith("y"):
        forms.add(verb[:-1] + "ied")
    if verb.endswith(("s", "x", "z", "ch", "sh")):
        forms.add(verb + "es")
    for other in VERB_ALSO.get(verb, ()):
        forms |= {other, other + "s", other + "ing", other + "ed"}
        if other.endswith("e"):
            forms |= {other[:-1] + "ing", other + "d"}
    return any(word.strip(".,!?;:").lower() in forms for word in plan.split())

VERB_ALSO = {
    "start": ("begin", "began", "beginning"),
    "begin": ("start", "starts", "starting", "started", "began"),
    "end": ("finish", "finishes", "finishing", "finished"),
    "finish": ("end", "ends", "ending", "ended", "finishes", "finishing", "finished"),
}

WHERE_WORK = re.compile(r"\bwhere\b[^.!?]*\bwork\b|\b(?:which|what)\s+(?:place|company|shop|"
                        r"school|hospital|office|site)\s+do\s+i\s+work\b", re.I)

def _job_reply(memory, where=False):
    known = user(memory)
    job, city = known.get("job"), known.get("city")
    place = str(known.get("workplace") or "").strip()
    if where and place:
        # The place is exactly what was asked for, so it is the answer, with the role left out.
        return "You work " + _place_phrase(place) + "."
    if job and city:
        said = _job_said(known)
        return pick([said + " in " + city + ".",
                     "You're in " + city + " — " + said[:1].lower() + said[1:] + "."],
                    memory)
    if job:
        return _job_said(known) + "."
    if city and where:
        # Only a where-ask can be answered with the town: "what do i do for a living" with no job
        # kept was answered "You said you live in Leeds", which answers a different question.
        # The honest line below says the store has no job, which is what was asked.
        return "You said you live in " + city + "."
    return _deny(memory, "job", pick(["You haven't told me what you do yet.",
                                      "I don't know your job — you haven't said."], memory))

def _yours(value):
    """The value said back with their own words turned round: "for myself" -> "for yourself"."""
    out = []
    for word in value.split():
        low = word.lower().strip(".,!?")
        out.append({"myself": "yourself", "my": "your", "me": "you", "i": "you",
                    "myself.": "yourself.", "our": "your", "us": "you"}.get(low, word))
    return " ".join(out)

WORK_CIRCUMSTANCE = frozenset("""
    part full time hours overtime nights days evenings weekends shifts days off call early late
    two three four five six seven all every a few several both
""".split())

def _a_circumstance(job):
    """Whether the word after "I work" is how they work, not what they do.

    "i work nights", "i work part time", "i work two jobs" are circumstances, so the verb is
    kept: "you work nights". "my job is a chef" arrives with the same frame but names a role, so
    it is "you're a chef". A plural is a circumstance too ("nights", "shifts"); a singular role
    noun is not.
    """
    words = re.findall(r"[a-z0-9']+", job.lower())
    if not words:
        return True
    if any(word in WORK_CIRCUMSTANCE for word in words):
        return True
    last = words[-1]
    return last.endswith("s") and not last.endswith("ss")

def _job_said(known):
    """The job said back the way they said it: "You work in a warehouse", "You're a nurse".

    A job told with a place preposition is a place, so it is not "you're a warehouse": the
    frame is kept with the job (facts.extract writes job_frame) and the reply follows it. "at"
    names a place, so it keeps its capital: "You work at Tesco".
    """
    job = _yours(str(known.get("job") or "").strip())
    frame = str(known.get("job_frame") or "").strip()
    preposition = frame.split(" ")[0]
    if frame == "was":
        # The job was given in the past ("i was a teaching assistant before the kids"), so it is
        # said back in the past. The tense is kept with the frame, the same way a place
        # preposition is, so it cannot be lost between the line and the ask.
        if _a_circumstance(job):
            return "You did " + job
        return "You were " + _a(job)
    if frame == "work":
        # "i work nights", "i work two jobs", "i work part time": the verb is the frame, so it is
        # "you work ..." and never "you're a nights". A role said with the same frame is the
        # exception: "my job is a chef" is "you're a chef", never "you work chef".
        if _a_circumstance(job):
            return "You work " + job
        return "You're " + _a(job)
    if preposition in ("in", "for", "on", "with"):
        # "in a warehouse", "on the tills", "with the council": the preposition they said is the one
        # said back, so it is never "You told me you're a council".
        return "You work " + frame + " " + job
    if preposition == "as":
        # "i got a new job as a chef": the article they said is kept, so it is "as a chef" and
        # "as an engineer".
        return "You work " + frame + " " + job
    if preposition == "at":
        # "at" alone is followed by a name, which keeps its capital ("You work at Tesco"); with its
        # article it is an ordinary place, so the job stays as it was said ("at the hospital").
        if frame == "at":
            return "You work at " + job[:1].upper() + job[1:]
        return "You work " + frame + " " + job
    return "You told me you're " + _a(job)

def _place_phrase(place):
    """Where they work, as the line said it: "in a school", "at Tesco".

    "at" alone is followed by a name, which keeps its capital, as the job reply does for the same
    frame.
    """
    place = str(place or "").strip()
    head, _, rest = place.partition(" ")
    # Only a bare "at" names a place by its own name: "at Tesco" keeps the capital, and
    # "at the hospital" is an ordinary place, said as it was said.
    if (head.lower() == "at" and rest and rest.lower() == rest
            and rest.split()[0].lower() not in ("the", "a", "an")):
        return "at " + rest[:1].upper() + rest[1:]
    return place

def _job_phrase(known):
    """The job as a clause inside another sentence: "you work nights", "you're a nurse".

    The summary is a sentence, not a reply, so it needs the clause without the capital and
    without "You told me". The frame still decides the words: a shift is "you work nights",
    never "a nights".
    """
    said = _job_said(known)
    low = said[:1].lower() + said[1:]
    head = "you told me "
    if low.startswith(head):
        low = low[len(head):]
    return low

def _places_reply(memory, low):
    known = user(memory)
    # "where does my sister live" is about her, not about the user: the place is in the line
    # that put her there, so read it back out of the conversation.
    # "whereabouts does my sister live" is the same ask: the same where-word the gate reads.
    who = _asked_person(memory, low)
    if who:
        hers = _other_place(memory, who)
        if hers:
            return hers
        return ("You haven't said where your " + who
                + (" live." if who.lower().endswith("s") else " lives."))
    city = known.get("city")
    if re.search(r"\bborn\b", low):
        # A birth is not where they are from: "i was born in lagos but i grew up in ibadan" has
        # both, and the two questions want different answers.
        born = known.get("born")
        if isinstance(born, str) and born:
            return pick(["You were born in " + born + ".", born + " — you were born there."],
                        memory)
        origin = known.get("from")
        if isinstance(origin, str) and origin:
            return pick(["You haven't told me where you were born — you're from " + origin + ".",
                         "I don't know where you were born. You told me you're from " + origin + "."],
                        memory)
        return pick(["You haven't told me where you were born.",
                     "I don't know that one — you haven't said where you were born."], memory)
    if re.search(r"\bhometown\b", low):
        return _from_reply(memory)
    if GROWN_UP_ASK.search(low):
        # "where did i grow up" asks the same fact as "where am i from": the line that gave it
        # said it as growing up somewhere, and the extractor files it as where they are from.
        # It is said back as growing up, though - "You're from Dublin" answers the question but
        # not the words they asked it with.
        return _grown_up_reply(memory)
    going = re.search(r"\bgoing\b|\btrip\b|\bholiday\b|\btravel", low)
    # "where am I from" asks where they grew up, not where they live now.
    if (isinstance(city, str) and city and known.get("home") and not going
            and not re.search(r"\bfrom\b", low)):
        # The home as they said it when they said where it stands ("a small village near York"):
        # the place is theirs, and the answer is neither a denial nor a different place.
        said_with = known.get("home")
        return "You live in " + (said_with if isinstance(said_with, str) else city) + "."
    if re.search(r"\bfrom\b|\bcome from\b", low):
        return _from_reply(memory)
    places = [p for p in (known.get("places") or []) if isinstance(p, str)]
    if going:
        # "where am I going" is about the trip, so the place they live is not the answer.
        away = [p for p in places if isinstance(city, str) and p != city] or places
        places = away
    if "city" in low or "town" in low:
        cities = [p for p in places if p.lower() not in extract.COUNTRIES]
        if cities:
            places = cities
    if not places:
        return _deny(memory, "place", "You haven't mentioned a place yet.")
    if re.search(r"\bwhere (?:do|does) (?:i|we) live\b|\bwhere am i (?:living|based)\b", low):
        # They asked where they live and never said: the place they named is not an answer.
        # A place they are from is the one thing worth naming here, and saying it keeps the
        # two questions apart: "im from cork" does not answer "where do i live?".
        origin = known.get("from")
        if isinstance(origin, str) and origin:
            return pick(["You haven't told me where you live — I know you're from " + origin + ".",
                         "I don't know where you live. You're from " + origin + ", that I do know."],
                        memory)
        return ("You haven't told me where you live. You mentioned " + places[0] + "."
                if len(places) == 1 else
                "You haven't told me where you live. You mentioned " + places[0] + ", then "
                + ", ".join(places[1:]) + ".")
    first = places[0]
    rest = [p for p in places[1:] if p != first]
    if rest:
        return "You said " + first + " first, then " + ", ".join(rest) + "."
    return "You mentioned " + first + "."

def _grown_up_reply(memory):
    """Where they grew up, said as growing up rather than as where they are from."""
    known = user(memory)
    origin, city = known.get("from"), known.get("city")
    if isinstance(origin, str) and origin:
        return pick(["You grew up in " + origin + ".",
                     origin + " — that's where you grew up."], memory)
    if isinstance(city, str) and city:
        return pick(["You haven't said where you grew up — I know you live in " + city + ".",
                     "Not sure where you grew up. You mentioned " + city + " though."], memory)
    return pick(["You haven't said where you grew up yet.",
                 "I don't know that one — you haven't told me where you grew up."], memory)

def _from_reply(memory):
    """Where they are from, which is a different question from where they live now."""
    known = user(memory)
    origin, city = known.get("from"), known.get("city")
    if origin and city and origin.lower() != city.lower():
        return pick(["You're from " + origin + " originally, and you live in " + city + " now.",
                     "You said you're from " + origin + ", and you're in " + city + " now."],
                    memory)
    if origin:
        return pick(["You're from " + origin + ".", origin + " — you told me you're from there."],
                    memory)
    if city:
        return pick(["You haven't said where you're from — I know you live in " + city + ".",
                     "Not sure where you're from. You mentioned " + city + " though."], memory)
    return pick(["You haven't said where you're from yet.",
                 "I don't know that one — you haven't said."], memory)

def _is_are(who):
    return " are " if _plural_person(who) else " is "

def _eats(who):
    return " eat" if _plural_person(who) else " eats"

def _does_not(who):
    return " don't" if _plural_person(who) else " doesn't"

def _they(who):
    """The word for the person at the front of a sentence of their own: "She", "He", "They"."""
    low = str(who or "").lower().strip()
    if low in extract.SHE:
        return "she"
    if low in extract.HE:
        return "he"
    return "they"

def _a_diet_predicate(who, diet):
    """A person's diet as the words after their name: "eats fish", "doesn't eat meat", "is vegan".

    The store keeps a restriction as "no fish", and what somebody eats put back as "eats fish":
    a take-back of a restriction is not an empty record, it is the food they eat now, so the
    recall says "Your son eats fish." where "Your son is eats fish." is not a sentence.
    """
    said = str(diet or "").strip()
    if said.startswith("eats "):
        return (_eats(who) + " " + said[5:]).strip()
    if said.startswith("no "):
        # What they drink is not what they eat: "my mate is teetotal" is kept as `no alcohol`
        # and said back "Your mate doesn't drink alcohol."
        return (_does_not(who) + " " + _diet_how(said) + " " + said[3:]).strip()
    return (_is_are(who) + said).strip()

def _their_pronoun(who):
    """The word for the person in the second half of a sentence: "for her", "for them".

    A word that is in both lists is a person either way - a mate, a friend, a colleague, a
    flatmate - and `SHE` was read first, so "my mate is teetotal" then "what can he have" ended
    "that's all I have on food for her". A word that says nothing about which it is says "them".
    """
    low = str(who or "").lower().strip()
    hers, his = low in extract.SHE, low in extract.HE
    if hers and not his:
        return "her"
    if his and not hers:
        return "him"
    return "them"

def _no_diet(who):
    """An ask about how someone else eats when nothing food-shaped is kept for them.

    Saying "you haven't told me what your dad eats" on its own is true and cold, and it is what
    someone with a diabetic dad gets. The offer is the part that helps: the fact is one line away.

    A baby is left to the weaning answers: the store keeps the age, and "my baby is 7 months what
    can she eat" is a question about that age, not about a diet the store has never heard.
    """
    if str(who or "").strip().lower() == "baby":
        return None
    return ("You haven't told me what " + (("your " + who) if who else "they") + _eats(who)
            + " \u2014 tell me and I'll plan the meals round it.")

def _a_condition_rules_out(condition):
    """Whether a condition rules a food out, by the bot's own table: coeliac is gluten.

    Only the conditions bot/memory/ack.CONDITION_FOOD knows are a food fact. A diabetic keeps
    their condition and nothing is claimed about their plate, so the store asks what they eat.
    """
    kept = condition if isinstance(condition, (list, tuple)) else [condition]
    return any(ack.CONDITION_FOOD.get(str(word).strip().lower()) for word in kept)

def _both_food_facts(who, allergies, diet):
    """An allergy and a diet kept for the same person, said in one answer.

    A line can carry both - "my mum is allergic to nuts and she doesnt eat meat" - and the ask
    that follows ("what can my mum eat") used to be answered with the diet alone, because a diet
    kept for a person answers before the allergy does. The allergy is the fact that could hurt
    them, so it goes first and the diet follows it rather than replacing it.
    """
    said = _allergy_is_their_food(who, allergies, only=False)
    them = _they(who)
    them = them[:1].upper() + them[1:]
    rest = _diet_sentence(who, diet)
    for lead in ((("Your " + who) if who else "They"), "They"):
        if rest.startswith(lead):
            rest = them + rest[len(lead):]
            break
    return said + " " + rest

def _allergy_is_their_food(who, allergies, only=True, low=""):
    """What a person can eat, from the only food fact kept for them: the allergy.

    "my mum is allergic to shellfish" then "what can she eat" is a question the store can answer,
    and answering it "you haven't told me what your mum eats" tells someone the allergy they just
    gave is not food at all. The allergy is what is ruled out; nothing else is claimed.
    """
    owner = ("Your " + who) if who else "They"
    said = [str(a) for a in allergies if str(a).strip()]
    for one in said:
        named, thing = _what_the_food_has(str(low or ""), one) if low else ("", "")
        if named:
            # "is peanut butter ok for her" after "my nan is allergic to nuts" is about the
            # peanut butter: naming it answers the question, and repeating the allergy again in
            # the same words is the sentence the person has just read. The allergy is not named
            # here - "my nan cant eat dairy" is kept as an allergy, and calling that an allergy
            # back is a claim the person did not make.
            return (named[:1].upper() + named[1:] + " has " + thing + " in it, so it's off the "
                    "table for " + _their_pronoun(who) + ".")
    ruled = said[0] if len(said) == 1 else "any of " + ", ".join(said)
    tail = ("" if only else "")
    if only:
        tail = " \u2014 that's all I have on food for " + _their_pronoun(who)
    return (owner + _is_are(who) + "allergic to " + ", ".join(said) + ", so nothing with "
            + ruled + " in it" + tail + ".")

def _what_the_food_has(low, ruled):
    """The food the line names, when it is a thing the person cannot have: ("cheese", "dairy").

    "can he have cheese" after "my husband is lactose intolerant" is answered about the cheese,
    not only about dairy in general: a person asking about one food has that food in their hand.
    Only an everyday food that is that thing every time it is eaten is named, so nothing is
    claimed about a dish the store was not told the recipe of; and a food that is the ruled-out
    thing itself ("what about eggs" of a vegan's eggs) is left to the sentence that names it.
    """
    for thing in re.split(r"\s*(?:,|\bor\b|\band\b)\s*", str(ruled or "")):
        thing = thing.strip().lower()
        if not thing:
            continue
        for phrase in FOOD_PHRASES.get(thing, ()):
            if re.search(r"\b" + re.escape(phrase) + r"s?\b", low):
                return phrase, thing
        # The longest food word wins, so "peanut butter" is not answered as "peanut".
        for word in sorted(FOOD_HAS.get(thing, ()), key=len, reverse=True):
            if word == thing:
                continue
            if re.search(r"\b" + re.escape(word) + r"s?\b", low):
                return word, thing
    return "", ""

def _diet_is_their_food(who, diet, low="", plain=False):
    """What a person cannot have, from the diet kept for them, or None when the diet says it.

    "my wife is vegetarian" then "what cant she have" is the ask the allergy answer already
    works out, and with the diet kept the store can still say what it rules out. Only a named
    diet is read this way, so nothing is claimed about food the store was not told.
    """
    said = " ".join(str(low or "").lower().split())
    diet_low = " ".join(str(diet or "").lower().split())
    owner = ("Your " + who) if who else "They"
    if diet_low.startswith("no "):
        if plain:
            return None
        # "my mum doesnt eat meat" then "what cant she have": the food said as missing is the
        # answer, and saying the diet's name again would be the sentence already on the screen.
        return (owner + " can't have " + diet_low[3:] + " \u2014 that's all I have on food for "
                + _their_pronoun(who) + ".")
    ruled = DIET_RULES_OUT.get(diet_low)
    if not ruled or (plain and re.search(r",|\bor\b|\band\b", ruled[0])):
        return None
    named, thing = _what_the_food_has(said, ruled[0]) if said else ("", "")
    if named:
        # The food in their hand is the answer: "cheese has dairy in it, and your husband is
        # lactose intolerant". A diet that rules out a list ("meat, fish, dairy or eggs") is not
        # named this way, because naming one of them would answer about only the one.
        return (named[:1].upper() + named[1:] + " has " + thing + " in it, and " + owner.lower()
                + _is_are(who) + diet_low + ".")
    return (owner + _is_are(who) + diet_low + ", so nothing with " + ruled[0] + " in it"
            + ruled[1] + " \u2014 that's all I have on food for " + _their_pronoun(who) + ".")

def _other_fact(memory, key):
    """Someone else's fact the user mentioned: (who, values), or ("", []) when there is none.

    It is what stops "he is allergic to nuts" then "what am I allergic to?" being answered as
    "you're allergic to nuts": the store knows whose allergy it was.
    """
    for entry in others(memory):
        values = entry.get(key)
        if isinstance(values, list) and values:
            return entry.get("who") or "", values
    return "", []

DISLIKE_ASK = re.compile(
    r"\?|\b(?:what|how|which|any|ideas?|recipes?|give)\b", re.I)

def _last_answer(memory):
    """The bot's last knowledge answer, or "" when the previous turn was something else."""
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return ""
    last = turns[-1]
    if not isinstance(last, dict) or last.get("module") != "answers":
        return ""
    reply = last.get("bot")
    return reply if isinstance(reply, str) else ""

def _one_half_of_the_dish(food, taste):
    """True when the food the guest reader found is one half of the dish the line names.

    Only "and" and "with" make a dish out of two foods. "i dont want pasta or rice tonight" is
    two things turned down, and reading "pasta" as one half of a dish called "pasta or rice" meant
    the whole family went unanswered ("Noted: you don't want pasta or rice tonight") while a
    single "i dont like pasta" got "no pasta in anything I suggest".
    """
    if not isinstance(taste, dict):
        return False
    thing = str(taste.get("thing") or "").strip().lower()
    food = str(food or "").strip().lower()
    if not thing or not food or thing == food:
        return False
    joined = re.match(r"^(?P<one>.+?)\s+(?P<how>and|with|&)\s+(?P<two>.+)$", thing)
    if not joined:
        return False
    return bool(re.search(r"\b" + re.escape(food) + r"\b",
                          joined.group("one") + " " + joined.group("two")))

def _dislikes_here(text):
    """[(food, kind)] in the line, a taste nobody else is named for read as their own.

    The subject reader looks at the words in front of the food, so "fish isn't really my
    thing" names no subject at all (the "my" comes after it) and a bare "not a huge fan of
    mushrooms" names nobody: both are plainly the speaker's own taste, and left as "" the
    store said nothing and the greeting pool echoed the line back.
    """
    out = []
    for food, at in guest.found(text):
        kind, who = extract.subject(text, at)
        out.append((food, kind or "user"))
    return out

def _a_dislike_told(text, memory):
    """The answer just given with the food the guest hates taken out, or None."""
    if not isinstance(text, str) or DISLIKE_ASK.search(text):
        return None
    if _about_this_chat(text, memory):
        return None
    tastes = read_tastes(text)
    if len(tastes) > 1:
        # "i dont like fish but i love prawns" is two tastes, and the promise about one of them
        # throws away the other half ("Fair enough - no fish in anything I suggest" for a person
        # who has just said they love prawns). A line of more than one taste is the taste
        # module's, which says both back.
        return None
    found = _dislikes_here(text)
    if any(_one_half_of_the_dish(food, taste) for food, _ in found for taste in tastes):
        # A dish said with both its halves is one thing, not its first word: "fish and chips"
        # is not fish and "mac and cheese" is not cheese, and promising to leave "fish" out of
        # everything for someone who eats fish is worse than saying the line back. The taste
        # module keeps the dish whole.
        return None
    foods = [food for food, kind in found if kind in ("user", "other")]
    alone = []
    if not foods and _last_answer(memory):
        # A bare "no mushrooms" answers the suggestion the bot has just made, and nothing in the
        # line has a verb for `found` to read. It is only a dislike when there is a suggestion
        # for it to be about: "no milk" on its own is as likely to be about the fridge.
        alone = guest.turned_down_alone(text)
        foods = alone
    if not foods:
        return None
    previous = _last_answer(memory)
    if previous:
        revised = guest.revise(previous, foods)
        if revised:
            return revised
        # The answer on the table does not name the food, so this is a steer on that answer and
        # not a fresh dislike: "what can i cook with mince" then "i dont want a lasagne" is
        # `ruled_out`'s line, which says the answer still stands. Promising to leave lasagne out
        # of everything is an answer to a question nobody asked, and it takes the turn from the
        # module built for the shape. The hook is the one the arbiter already asks for it.
        try:
            if ruledout.takes_as_it_comes(text, memory):
                return None
        except Exception:  # noqa: BLE001 - a hook that raises claims nothing
            pass
    a_pair = len(foods) > 1
    own = [guest.plain(food, a_pair) for food, kind in found if kind == "user"]
    own = own or [guest.plain(food) for food in alone]
    own = [food for food in own if food]
    if own:
        return guest.left_out(own)
    return None

STOPPED_SAID = re.compile(
    r"^(?:i|we)(?:'ve|ve|\s+have|\s+had)?\s+"
    r"(?:stopped|quit|gave up|given up|packed in|came off|gone off|got off|went off)\b", re.I)

NEGATED_SAID = re.compile(
    r"\b(?:not|never|no longer|any ?more|off|without)\b|n't\b", re.I)

def _the_take_back(memory, key):
    """The last line that took the fact back, and the value it took back, or ("", "")."""
    for turn in reversed(memory.get("turns") or []):
        line = str((turn or {}).get("user") or "") if isinstance(turn, dict) else ""
        if not line.strip():
            continue
        gone = (extract.denials(line) or {}).get(key)
        if gone:
            # Said back as the fact it took, not as the words the take-back used: the store holds
            # "cutting out sugar", and a line that names only the food ("im back on sugar") would
            # otherwise be answered "You told me you stopped sugar."
            record = memory.get("denial") or {}
            if " ".join(line.split()) == str(record.get("said") or ""):
                dropped = record.get(key)
                if isinstance(dropped, list) and dropped:
                    gone = dropped[0]
                elif dropped:
                    gone = dropped
            return " ".join(line.split()), str(gone)
    return "", ""

def _a_take_back_said_back(line, gone):
    """Their own take-back, said back as a statement: "You told me you stopped doing keto."

    A take-back is not a wrong fact and it is not a fact at all, so neither the store's value
    ("you're doing keto") nor the line as a quote ("You said: "i stopped keto"") answers the
    question someone asked. What they said, said plainly, does.
    """
    said = " ".join(str(line or "").split())
    if STOPPED_SAID.match(said):
        rest = re.sub(r"^(?:i|we)(?:'ve|ve|\s+have|\s+had)?\s+", "", said, flags=re.I)
        return "You told me you " + " ".join(rest.split()) + "."
    if str(gone).strip().lower() in ("diet", "dieting", "on a diet"):
        return "You told me you're not on a diet any more."
    if NEGATED_SAID.search(said):
        # "im not vegetarian" is a fact about now, not a take-back of one they had: restating the
        # negative is true, and "you stopped being vegetarian" says they once were.
        return _a_negation_said_back(gone, said)
    if gone in WAY_OF_EATING:
        return "You told me you stopped being " + _diet_words(gone) + "."
    if gone in PLAN_DIETS:
        return "You told me you stopped doing " + _diet_words(gone) + "."
    return "You told me you stopped " + _diet_words(gone) + "."

ANY_MORE = re.compile(r"\b(?:any ?more|anymore|no longer)\b", re.I)

def _a_negation_said_back(gone, line=""):
    """"You told me you're not vegetarian", for a diet said as a negation rather than left."""
    value = str(gone or "").strip().lower()
    tail = " any more" if ANY_MORE.search(str(line or "")) else ""
    if not value:
        return "You told me you're not on a diet" + tail + "."
    if value.startswith("no "):
        return "You told me you don't " + _diet_how(value) + " " + value[3:] + tail + "."
    if value in WAY_OF_EATING:
        return "You told me you're not " + _diet_words(value) + tail + "."
    if value in PLAN_DIETS:
        return "You told me you're not doing " + _diet_words(value) + tail + "."
    return "You told me you're not " + _diet_words(value) + tail + "."

def _says_the_fact(line, key):
    """Whether a past line tells the thing a denial would deny, rather than asking about it.

    A line that only carries the word is not a fact: "how do i stick to a budget", "am i
    allergic to anything" and "what job should i look for" are questions, and "we need to
    save for a deposit" is a plan, so quoting any of them back answers the question with
    itself. What they said in other words is still what they said - "my budget is tight this
    month", "i mostly eat low fat stuff" - so those stay quotable.
    """
    if (extract.extract(line) or {}).get(key):
        return True
    low = " ".join(str(line or "").lower().split())
    if ASKING_ABOUT_IT.search(low) or PLANNING_IT.search(low):
        return False
    if A_CLAIM_OF_TELLING.match(low):
        # "i told you about the damp" carries the word and says nothing about the damp: it is the
        # person complaining that they said it, so quoting it back answered "what did i say about
        # the damp" with the complaint. A claim carrying a clause ("i told you my dog died") names
        # the fact itself and never reaches here - extract() finds it in the branch above.
        return False
    return True

A_CLAIM_OF_TELLING = re.compile(
    r"^\W*(?:and\s+|also\s+|so\s+|but\s+|ok(?:ay)?\s+|look\s+|listen\s+|hey\s+)?"
    r"(?:i|we)\s+(?:already\s+|just\s+|did\s+|have\s+|had\s+|definitely\s+)?"
    r"(?:told|tell|mentioned|mention|said|say|talked|talk|spoke)\s+(?:you|u)\b", re.I)

ASKING_ABOUT_IT = re.compile(
    r"^(?:how|what|when|where|which|who|why|do|does|did|can|could|should|would|am|are|is|have|"
    r"has|will|if)\b|\?$|\b(?:do i|should i|can i|am i|did i|have i|will i)\b", re.I)

PLANNING_IT = re.compile(
    r"\b(?:we|i|you)\s+(?:need|needs|want|wants|ought|have to|has to|should)\s+to\b|"
    r"\b(?:thinking about|planning to|going to try|might|maybe|hoping to)\b", re.I)

def _the_line_about(memory, key, own=None):
    """The last line the person sent that says the thing a denial would deny, or "".

    own, when it is given, says whether a line that carries the words carries the fact itself:
    "my wife is on a diet" has the word "diet" in it and is not their diet, so a denial must
    not quote it back as one.
    """
    words = DENIAL_WORDS.get(key) or ()
    stems = DENIAL_STEMS.get(key) or ()
    if not words and not stems:
        return ""
    parts = [r"\b" + re.escape(word) + r"\b" for word in words]
    parts += [r"\b" + re.escape(stem) for stem in stems]
    wanted = re.compile("|".join(parts))
    for turn in reversed(memory.get("turns") or []):
        line = str((turn or {}).get("user") or "") if isinstance(turn, dict) else ""
        found = " ".join(re.findall(r"[a-z']+", line.lower()))
        if not found:
            continue
        if not wanted.search(found):
            continue
        if key in (extract.denials(line) or {}):
            continue  # a line that takes the fact back is not the fact said
        # A line that asks about the thing, or plans around it, is not a line that tells it:
        # "how do i stick to a budget" and "we need to save for a deposit" carry the word a
        # budget denial would deny, and quoting either back answers the question with itself.
        if not _says_the_fact(line, key):
            continue
        if _said_of_someone_else(line, wanted):
            continue
        if own is not None and not own(line):
            continue
        return " ".join(line.split())
    return ""

def _said_of_someone_else(line, wanted):
    """Whether every place the line has the fact's word it is said of another person.

    "my mums budget is 100" carries the word a budget denial would deny and is not their
    budget, so quoting it back answers a question they did not ask: it has to be their own
    line or nothing, and the denial is the honest reply.
    """
    kinds = []
    for match in wanted.finditer(line):
        try:
            kinds.append(extract.subject(line, match.start())[0])
        except (ValueError, IndexError):
            return False
    return bool(kinds) and all(kind == "other" for kind in kinds)

def _deny(memory, key, denial, own=None):
    """The denial, unless they did say it: then their own line is the honest answer."""
    said = _the_line_about(memory, key, own)
    if said:
        return "You said: \"" + said + "\""
    return denial

def _their_own_diet(line):
    """Whether the line says the diet as the person's own, now.

    "my wife is on a diet" names somebody else's, "i was on a diet last year" names one that is
    behind them and "im thinking about going on a diet" names one they have not started, so none
    of the three may come back as their own when they ask what diet they are on. A diet the store
    files from the line, or one the line takes back, is theirs.
    """
    if extract.extract(line).get("diet") or extract.denials(line).get("diet"):
        return True
    if DIET_NOT_THEIRS.search(line):
        return False
    # "i mostly eat low fat stuff" is how they eat now, though the store files no diet from it,
    # and it is the honest line to quote when they ask about a diet.
    return bool(re.search(r"\b(?:i|we)\b[^.?!]*\b(?:eat|eats|eating|drink|drinks|diet)\w*\b",
                          line, re.I))

PLAN_DIETS = frozenset("""keto paleo atkins mediterranean low-carb slimming-world
weight-watchers intermittent-fasting whole30 whole-30 omad carnivore dukan south-beach fast-800
5:2 16:8 4:3""".split())

WAY_OF_EATING = frozenset("""vegan vegetarian veggie pescatarian flexitarian plant-based
raw gluten-free dairy-free""".split())

def _diet_words(value):
    """A diet as a person would say it: "slimming world", not the store's "slimming-world"."""
    return str(value).replace("-", " ")

DIET_NEGATED = re.compile(r"^(?:not|no|never|without|off)\s+(.{2,60})$", re.I)

def _a_diet_put_back(shown):
    """The thing they are back on, when the diet held was a negation, else None."""
    bare = DIET_NEGATED.match(" ".join(str(shown or "").split()))
    if not bare:
        return None
    thing = bare.group(1).strip()
    words = thing.split()
    if not words or len(words) > 4 or words[0].lower() in ("more", "longer", "any", "the"):
        return None
    return thing

DIET_NOT_THEIRS = re.compile(
    r"\b(?:my|our|his|her|their)\s+[a-z]+\s+(?:is|was|are|were|has|had)\b|"
    r"\b(?:he|she|they)\b[^.?!]*\b(?:diet|keto|paleo|vegan|vegetarian)\b|"
    r"\b(?:i|we)\s+(?:was|were)\b|\bused to\b|\b(?:last|few)\s+(?:year|years|month|months)\b|"
    r"\byears?\s+ago\b|\b(?:thinking (?:about|of)|considering|might|maybe|planning to|going to try|"
    r"want to try)\b", re.I)

MEAL_WANTED = re.compile(
    r"\bwhat (?:do|should|shall|can|could|will) i (?:eat|have|cook|make|do for dinner)\b|"
    r"\bwhat'?s for (?:dinner|lunch|tea|supper|breakfast)\b|"
    r"\bwhat can we (?:eat|have|cook|make)\b|"
    r"\b(?:give|suggest|recommend) me something to eat\b", re.I)

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

AGE_COMPARE = re.compile(
    r"\bwho(?:'s|s| is| was)?\s+(?:the\s+)?(?:older|younger|eldest|oldest|youngest)\b|"
    # "which one is older", "which of them is younger": the same ask as a choice out of two,
    # and it fell to the search hedge the same way. The person has just been told about a pair.
    r"\bwhich(?:\s+one|\s+of\s+(?:them|those|the\s+two))?\s+(?:is\s+|was\s+)?(?:the\s+)?"
    r"(?:older|younger|eldest|oldest|youngest)\b|"
    r"\b(?:am|is|are|was|were)\b[^.!?]{0,40}\b(?:older|younger) (?:than )?\b|"
    r"\bhow (?:much|many years)\s+(?:older|younger)\b|"
    r"\b(?:older|younger) (?:than )?(?:me|him|her|them)\b", re.I)

BARE_AGE_WHO = re.compile(
    r"^\W*(?:so|and|ok|okay|but|well)?[\s,]*who(?:'s|s| is| was)?\s+(?:the\s+)?"
    r"(?:older|younger|oldest|youngest|eldest)\b[^.?!]*$", re.I)

# The same bare ask as a choice between two: "which one is older", "which of them is younger".
# The person who says this has just been told about two people and wants the two numbers put
# against each other, and it is the same question as "who is older" however it is worded.
# The gap asked for with a pronoun instead of a name: "how much older is he". It is read with
# the two people the store holds, which is the only pair the line can be about.
THE_AGE_GAP = re.compile(r"\bhow (?:much|many years)\s+(?:older|younger)\b", re.I)


WHICH_ONE_AGE_WHO = re.compile(
    r"^\W*(?:so|and|ok|okay|but|well)?[\s,]*which(?:\s+one|\s+of\s+(?:them|those|the\s+two))?"
    r"(?:'s|s| is| was)?\s+(?:the\s+)?(?:older|younger|oldest|youngest|eldest)\b[^.?!]*$", re.I)

PEOPLE_WORDS = re.compile(r"\b(?:she|her|hers|he|him|his|they|them|us|we|me|i|myself|mine)\b", re.I)

SOMEONE_ELSE = re.compile(r"\b(?:she|her|hers|he|him|his|they|them|us)\b", re.I)

def _about_people(low):
    """Whether a comparison with nobody named is about people at all.

    "who is older" is. "is my laptop older than my phone" is not, and neither is "am i older than
    the dog": a comparison against something needs a person on the other side of the "than".
    """
    if not (BARE_AGE_WHO.match(low) or PEOPLE_WORDS.search(low)):
        return False
    if re.search(r"\bthan\b", low):
        return bool(SOMEONE_ELSE.search(low))
    return True

def _age_compare(memory, low):
    """Two ages the store holds, compared out loud: "You are - 34 to your wife's 32."

    A comparison is not knowledge about the world: it is the two numbers they gave, against each
    other, and the store is the only place both are kept. The two are the people the line names
    ("who is older, my son or my daughter"), the person it names against the speaker ("am i
    older than my wife"), or, with nobody named, the speaker against the last person heard of.
    One of the two missing keeps the turn free, because half an answer here is a guess.
    """
    if not AGE_COMPARE.search(low):
        return None
    said = memory.get("understood") or {}
    if said.get("kind") not in (None, "question"):
        # "my wife is older than me" states the comparison instead of asking it: it is something
        # the store should keep, not a turn to answer with the two numbers back.
        return None
    aged = [e for e in others(memory) if e.get("age") is not None and e.get("who")]
    by_who = {}
    for entry in aged:
        by_who.setdefault((entry.get("who") or "").lower(), entry)
    # The people the line names decide the comparison: "am i older than my brother" is not
    # answered from the wife's age, so a person named with no age of their own keeps the turn
    # free rather than standing in for whoever the store heard about last.
    kin = getattr(extract, "KIN", extract.RELATIONS)
    words = [w.lower() for w in
             re.findall(r"\b(?:my|our)\s+(" + "|".join(kin) + r")(?:'s|s)?\b", low)]
    if [w for w in words if w not in by_who]:
        return None
    # "is my car older than my wife's" compares two cars: a thing they own is not a person, and
    # the wife's age is no answer to it.
    if [w for w in re.findall(r"\bmy\s+([a-z']+)", low) if w not in kin]:
        return None
    named = []
    for word in words:
        if by_who[word] not in named:
            named.append(by_who[word])
    mine = user(memory).get("age")
    me = {"who": "", "age": mine} if mine is not None else None
    if len(named) >= 2:
        sides = named[:2]
    elif named and me is not None:
        sides = [me, named[0]]
    elif not named and me is not None and aged and _about_people(low):
        pointed = _pointed_at(aged, low)
        if pointed is None:
            return None
        sides = [me, pointed]
    elif (not named and me is None and len(by_who) == 2
          and not re.search(r"\b(?:me|myself|mine|i|im)\b", low)
          and (BARE_AGE_WHO.match(low) or WHICH_ONE_AGE_WHO.match(low))):
        # "who is older" names nobody and the person has given no age of their own, so the
        # comparison is the two people the store holds an age for: after "my daughter is 4 and
        # my son is 7" that question is the whole of it, and it was answered with the search
        # hedge ("I can't look that up from here, sorry"). Two is the number the line can be
        # about; with three ages and nobody named it could be about either pair, so the turn
        # stays free rather than guessing.
        sides = list(by_who.values())
    elif (not named and me is None and len(by_who) == 2 and THE_AGE_GAP.search(low)
            and not re.search(r"\b(?:me|myself|mine)\b", low)
            and _the_pronoun_is_one_of_the_two(by_who, low)):
        # "how much older is he" asks for the gap between the two people the store holds, and
        # it fell to the search hedge because the line names nobody with "my": the pronoun is
        # the only person named. A pronoun that fits neither of the two is a question about
        # somebody the store has no age for, so it keeps the turn free.
        sides = list(by_who.values())
    else:
        return None
    try:
        ages = [int(s.get("age")) for s in sides]
    except (TypeError, ValueError):
        return None
    first, second = sides
    if ages[0] == ages[1]:
        if not first.get("who"):
            return "Neither of you - you're both " + str(ages[0]) + "."
        return "Neither of them - your " + str(first["who"]) + " and your " + str(second["who"]) + " are both " + str(ages[0]) + "."
    younger = re.search(r"\b(?:younger|youngest)\b", low) is not None
    winner, other = (0, 1) if (ages[0] > ages[1]) != younger else (1, 0)
    win, lose = sides[winner], sides[other]
    gap = abs(ages[0] - ages[1])
    years = "year" if gap == 1 else "years"
    if re.search(r"\bhow (?:much|many years)\s+(?:older|younger)\b", low):
        if not first.get("who"):
            return str(gap) + " " + years + ": you're " + str(ages[0]) + " and your " + str(second["who"]) + " is " + str(ages[1]) + "."
        return str(gap) + " " + years + ": your " + str(first["who"]) + " is " + str(ages[0]) + " and your " + str(second["who"]) + " is " + str(ages[1]) + "."
    theirs = "your" if not lose.get("who") else "your " + str(lose["who"]) + "'s"
    said = re.search(r"\b(youngest|eldest|oldest)\b", low)
    if said:
        word = "the " + said.group(1)
    else:
        word = "older" if ages[winner] > ages[other] else "younger"
    if not win.get("who"):
        return "You're " + word + " - " + str(ages[winner]) + " to " + theirs + " " + str(ages[other]) + "."
    return "Your " + str(win["who"]) + "'s " + word + " - " + str(ages[winner]) + " to " + theirs + " " + str(ages[other]) + "."

WHICH_FIRST_ASK = re.compile(
    r"\b(?:which|who|whose|what)\s+(?:one\s+|ones\s+|of\s+them\s+|of\s+those\s+|of\s+the\s+two\s+)?"
    r"(?:is\s+|are\s+|comes?\s+|come\s+|happens?\s+|happen\s+|would\s+be\s+|will\s+be\s+)?"
    r"(?:up\s+)?(?:first|sooner|earliest|earlier)\b", re.I)

WHICH_FIRST_WORDS = frozenset("""which who whose what one ones of them those the two is are come
    comes happen happens would will be up first sooner earliest earlier next then so do does you
    think again now really actually please and but well hmm oh ah then just it that this both""".split())

MONTH_SAID = re.compile(
    r"\b(?:in|on|of|by|until|till|before|after|from|during|early|late|mid|next|this|that|the)\s+"
    r"(?:" + MONTH_ALT + r")\b|\b(?:" + MONTH_ALT + r")\s+\d{1,2}(?:st|nd|rd|th)?\b|"
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:" + MONTH_ALT + r")\b", re.I)

def _the_day_a_plan_names(plan):
    """How many days away the day a plan names is, or None when it names no day.

    A month is counted from the first of that month, or from the day of the month when the plan
    says one, and a month already behind us in the calendar is next year's: "in may" said in
    June is the May coming. A weekday on its own is that day in the week we are in, which is the
    only reading "the dentist is on tuesday and the doctor on friday" needs.
    """
    low = " ".join(str(plan or "").lower().split())
    today = datetime.date.today()
    found = MONTH_SAID.search(low)
    if found:
        short = MONTH_WORD.search(found.group(0))
        name = [m for m in MONTH_ORDER if m.startswith(short.group(0)[:3])] if short else []
        if not name:
            return None
        index = MONTH_ORDER.index(name[0]) + 1
        day = 1
        near = (re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\b[^.?!]{0,12}" + re.escape(name[0]),
                          low)
                or re.search(re.escape(name[0]) + r"\b[^.?!]{0,12}?\b(\d{1,2})(?:st|nd|rd|th)?\b",
                             low))
        if near and 1 <= int(near.group(1)) <= 31:
            day = int(near.group(1))
        for year in (today.year, today.year + 1):
            try:
                when = datetime.date(year, index, day)
            except ValueError:
                continue
            if when >= today:
                return (when - today).days
        return None
    day = WEEKDAY_WORD.search(low)
    if day and not DATE_PHRASE.search(low):
        return (WEEK.index(day.group(0)) - today.weekday()) % 7
    return None

def _the_plans_in_date_order(memory):
    """The things the store holds a day for, earliest first, each said the way it was kept.

    A plan is kept as the phrase they gave ("my dads birthday is in april"), but a birthday said
    with its day of the month is filed with the person instead ("my daughters birthday is on 12
    june" is `others(memory)`), and it is a dated thing in the store just the same. Both are put
    back into one sentence so the order can be read across them.
    """
    known = user(memory)
    held = [p for p in (known.get("plans") or []) if isinstance(p, str) and p.strip()]
    latest = known.get("plan")
    if isinstance(latest, str) and latest.strip() and latest not in held:
        held.append(latest)
    for entry in others(memory):
        who = str(entry.get("who") or "").strip()
        day = str(entry.get("birthday") or "").strip()
        if not (who and day):
            continue
        # A birthday that is also a plan is in the store twice, and the plan is the way they said
        # it; only the person's own record is used when no plan holds that birthday.
        if any("birthday" in plan.lower() and re.search(r"\b" + re.escape(who) + r"s?\b",
                                                        plan.lower())
               for plan in held):
            continue
        # "3 may" takes "on", a month on its own takes "in": "your daughters birthday is on 12
        # june", "your dads birthday is in april".
        link = "on " if re.search(r"\d", day) else "in "
        held.append("my " + who + "s birthday is " + link + day)
    dated = []
    seen = set()
    for plan in held:
        days = _the_day_a_plan_names(plan)
        if days is None:
            continue
        said = plan_sentence(plan, plan_line(memory, plan)).rstrip(" .!?")
        if not said:
            continue
        # A birthday is often kept twice, as a plan and on the person, and the same day said
        # twice is one day in the order.
        key = (days, said.lower())
        if key in seen:
            continue
        seen.add(key)
        dated.append((days, said))
    dated.sort(key=lambda pair: pair[0])
    return dated

def _which_comes_first(memory, low):
    """Two dated plans in the order the calendar puts them: "May comes first, then June".

    Every plan is said back in the words it was given in, so nothing here composes a sentence
    about their life: the store has the dates and the words, and this only reads them in order.
    """
    found = WHICH_FIRST_ASK.search(low)
    if not found:
        return None
    said = memory.get("understood") or {}
    if said.get("kind") not in (None, "question"):
        return None
    rest = (low[:found.start()] + " " + low[found.end():])
    if [w for w in re.findall(r"[a-z']+", rest) if w not in WHICH_FIRST_WORDS]:
        return None
    dated = _the_plans_in_date_order(memory)
    if len(dated) < 2:
        return None
    first = dated[0][1]
    later = [said[:1].lower() + said[1:] for _, said in dated[1:4]]
    if dated[1][0] == dated[0][0]:
        return "Both land on the same day: " + first[:1].lower() + first[1:] + " and " + \
            later[0] + "."
    tail = ", then ".join(later)
    return first + ", so that one is first \u2014 then " + tail + "."

def _the_pronoun_is_one_of_the_two(by_who, low):
    """Whether a pronoun in the line fits one of the two people the store holds an age for.

    "how much older is she" about two sons is not a question about either of them, and answering
    it from their two ages puts a girl in the answer they never mentioned. A line with no
    pronoun at all is the pair itself, so it passes.
    """
    if re.search(r"\b(?:she|her|hers)\b", low):
        fits = extract.SHE
    elif re.search(r"\b(?:he|him|his)\b", low):
        fits = extract.HE
    else:
        return True
    return any((entry.get("who") or "").lower() in fits for entry in by_who.values())


def _pointed_at(aged, low):
    """The person an age comparison points at with a pronoun, or the last one heard of.

    A pronoun only points at a person it fits: "am i older than him" with a wife in the store is
    not a question about her, so nobody is returned and the turn stays free. With no pronoun at
    all the comparison is against the last person the store heard about.
    """
    fits = None
    if re.search(r"\b(?:she|her|hers)\b", low):
        fits = extract.SHE
    elif re.search(r"\b(?:he|him|his)\b", low):
        fits = extract.HE
    if fits:
        for entry in reversed(aged):
            if (entry.get("who") or "").lower() in fits:
                return entry
        return None
    return aged[-1]

LIMIT_LIKE = re.compile(
    r"\b(?:pregnan\w*|expecting|we'?re having a baby|having a baby)\b"
    r"|\ballerg\w*|\bintoleran\w*|\bcoeliac\b|\bceliac\b|\bibs\b|\bcrohn'?s?\b"
    r"|\bdiabet\w*|\bgout\b|\breflux\b|\bhigh cholesterol\b|\bkidney\b"
    r"|\bvegan\b|\bvegetarian\b|\bpescatarian\b|\bon a diet\b|\b\w+[- ]free\b"
    r"|\b(?:can'?t|cannot|can not|don'?t|dont|do not|never|no longer|stopped|avoid\w*)\b"
    r"[^.!?]{0,24}?\b(?:eat|drink|have|haveing|having|touch|take|dairy|meat|gluten|sugar|"
    r"alcohol|salt)\b", re.I)

MORE_FOODS = frozenset("""sesame soya soy soya-bean mustard celery sulphites lupin molluscs
shellfish kiwi strawberry strawberries banana bananas pineapple tomato tomatoes chocolate
sugar caffeine msg sulphite""".split())

def _a_food(value):
    """Whether the thing they can't have is food: "nuts" is, "penicillin" is not."""
    word = str(value or "").strip().lower()
    if not word:
        return False
    if word in MORE_FOODS:
        return True
    if any(word in family for family in cooking.FAMILIES.values()):
        return True
    if word in cooking.CHEESES or re.search(r"\b" + cooking.FOOD + r"\b", word):
        return True
    return False

def _diet_food(diet):
    """The food a diet rules out, or () for a diet the table does not know."""
    low = str(diet or "").strip().lower()
    if low in DIET_FOOD:
        return DIET_FOOD[low]
    if low.startswith("no "):
        # "no meat" is the limit said as the food already, so there is nothing to work out.
        return (low[3:].strip(),) if low[3:].strip() else ()
    if low.endswith(" free"):
        return (low[:-5].strip(),) if low[:-5].strip() else ()
    return ()

def _said_a_limit(memory):
    known = user(memory)
    if known.get("allergies") or known.get("condition") or known.get("diet"):
        return True
    for turn in (memory.get("turns") or [])[-12:]:
        said = str((turn or {}).get("user") or "")
        if said and LIMIT_LIKE.search(said):
            return True
    return False

def _said_list(items):
    """Two things are joined with "and"; three or more take commas and a final "and".

    A bare comma between two things reads wrong in the answer: "nothing with peanuts, shellfish in
    it" looks like a typo, and "you're coeliac, lactose intolerant" argues with itself.
    """
    items = [str(item) for item in items]
    if not items:
        return ""
    if len(items) < 2:
        return items[0]
    if len(items) == 2:
        return items[0] + " and " + items[1]
    return ", ".join(items[:-1]) + " and " + items[-1]

def _limit_reply(memory, low=""):
    """What they can't have, said back: "what can't i eat", "what should i avoid", "what am i
    not allowed to eat". The ask names no subject of its own, so the answer is the limits they
    gave - an allergy, a diet, a condition - and nothing else about them."""
    known = user(memory)
    allergies = [str(a) for a in (known.get("allergies") or []) if str(a).strip()]
    conditions = known.get("condition") or []
    if isinstance(conditions, str):
        conditions = [conditions]
    conditions = [str(c) for c in conditions if str(c).strip()]
    diet = str(known.get("diet") or "").strip()
    # What they can't have is a list of food, so only a food can be said back as one. "im allergic
    # to penicillin" is a fact about medicine, and "nothing with penicillin in it" is a claim about
    # their dinner they never made; the store says nothing and the turn is left to the hedge it
    # would have had before.
    foods = [allergy for allergy in allergies if _a_food(allergy)]
    if not foods and not conditions and not diet:
        # Nothing is stored, so there is no limit to say back. When the line names food it is
        # still the limit ask and gets an honest answer; "what should I avoid" with no food word
        # in it is a question about whatever the conversation is on ("I want to paint my
        # kitchen"), and asking what to keep out of their food answers a question nobody asked.
        if not FOOD_ASK.search(low):
            return None
        # Unless they did tell us something a moment ago: "im pregnant" and "my son is allergic
        # to nuts" are not kept as limits, and "you haven't told me anything you can't have" flatly
        # denies the turn before. The honest line is only for a chat that said nothing at all.
        if _said_a_limit(memory):
            return None
        return ("You haven't told me anything you can't have. Say what to keep out of your food "
                "and I'll stick to it.")
    # Every limit the store keeps is about food, so it is said as the food it rules out: "what
    # can't i have" and "what should i avoid" are the same ask as "what can't i eat".
    clauses = []
    if foods:
        clauses.append("nothing with " + _said_list(foods) + " in it \u2014 you're allergic to "
                       + ("them" if len(foods) > 1 or foods[0].endswith("s") else "it"))
    if conditions:
        # A condition that rules a food out is said as the food, the way the bot answers it when
        # they first say it: "nothing with gluten in it - you're coeliac".
        ruled = [ack.CONDITION_FOOD.get(condition.lower()) for condition in conditions]
        if ruled and all(ruled):
            clauses.append("nothing with " + _said_list(ruled) + " in it \u2014 you're "
                           + _said_list(conditions))
        else:
            clauses.append("you're " + _said_list(conditions))
    if diet:
        ruled = _diet_food(diet)
        # "no meat" is already the food, so the label it would be said back with is the food too:
        # "nothing with meat in it - you're no meat" reads as a broken sentence. That shape keeps
        # the wording it had.
        if ruled and all(ruled) and not diet.lower().startswith("no "):
            # A diet is a list of food, so it is said the way an allergy is: the food first, the
            # reason after. "you're vegetarian" alone names no food at all.
            clauses.append("nothing with " + _said_list(ruled) + " in it \u2014 you're " + diet)
        else:
            clauses.append("you don't " + _diet_how(diet) + " " + diet[3:] if diet.startswith("no ") else
                           "you're " + diet)
    said = clauses[0]
    if len(clauses) == 2:
        said += ", and " + clauses[1]
    elif len(clauses) > 2:
        said += ", " + ", ".join(clauses[1:-1]) + ", and " + clauses[-1]
    said = said[:1].upper() + said[1:] + "."
    if _same_as_last(said, memory):
        # Asked again in the words of the ask ("what can't i have" after "what should i avoid"),
        # the same sentence twice in a row reads like a machine, and the turn would go to
        # whichever module says something else: the limit is still the answer, said afresh.
        said = _vary(["Still this: " + said[0].lower() + said[1:],
                      "That hasn't changed: " + said[0].lower() + said[1:],
                      "Same answer: " + said[0].lower() + said[1:]], memory)
    return said

# A question can be asked without a question mark, and then the fact in front of it is only the
# context for it: "my sister is veggie and she's coming to dinner, what can i cook" ends on the
# ask, and the store's receipt for the fact ("Your sister is veggie.") answers something nobody
# asked while the card that answers the dinner waits behind it (hf:lewtun, #general 126189).
AN_ASK_AT_THE_END = re.compile(
    r"(?:^|[\s,;])(?:what|which|how|where|when|who|why)\b[^.!?]*$"
    r"|(?:^|[\s,])(?:can|could|should|shall|would|will|do|does|did|is|are|am)\s+"
    r"(?:i|we|you|he|she|they|it)\b[^.!?]*$", re.I)

# The composer's own way of saying it has nothing: no receipt is worth less than this.
HEDGED = re.compile(
    r"\b(?:don'?t know enough|beyond what i know|not sure about that one|"
    r"rather not guess|a (?:quick )?search\b|searching for it|look it up)\b", re.I)


def _the_answer_the_ask_gets(text, memory):
    """What the cards say to this line as a question, or "" when they have nothing to say.

    A hedge is not an answer: "I don't know enough to answer that honestly" is the composer
    giving up, and a fact the store can say back is better than that.
    """
    from ..modules import answers  # noqa: PLC0415 - answers imports this package
    fresh = {"turns": [], "aside": True}
    for key in ("user", "others", "facts_log"):
        if key in memory:
            fresh[key] = memory[key]
    try:
        reply = answers.respond(text, fresh) or ""
    except Exception:  # noqa: BLE001 - a store that cannot ask is a store that says the fact
        return ""
    said = " ".join(str(reply).split())
    if not said or HEDGED.search(said):
        return ""
    return said


def _the_ask_beats_the_receipt(text, memory):
    """True when a line that ends on a question is a question the cards can answer.

    Asked of the cards rather than assumed, because a line whose ask they cannot answer
    ("my wife is vegan and we are going out, where can we eat") keeps its receipt, which is at
    least true, instead of falling through to a shrug.
    """
    if not isinstance(text, str) or "?" in text:
        return False
    if not AN_ASK_AT_THE_END.search(" ".join(text.split())):
        return False
    return bool(_the_answer_the_ask_gets(text, memory))


def _a_diet_told(text, memory, low):
    """"she doesnt eat meat" said about someone: "Your mum doesn't eat meat."

    The fact is already kept against that person by the time this runs (observe comes first), so
    a friend says it back with their name in it instead of "Noted! What would be most useful to
    talk about?", which tells the person nothing about whether it was taken in. The user's own
    diet is not here: that is a line about them, and the echo handles it.
    """
    if not isinstance(text, str) or "?" in text:
        return None
    if _the_ask_beats_the_receipt(text, memory):
        # The line ends on a question the cards can answer, so the fact is only what that question
        # is about: filing it is the whole job, and the receipt is a line nobody asked to have said
        # back. "my sister is veggie ... what can i cook" gets the dinner card, not "Your sister is
        # veggie."
        return None
    if _about_this_chat(text, memory) or OTHER_ASK.search(low) or REMINDER_MID.search(low):
        return None
    found = extract.extract(text)
    if found.get("diet") or found.get("no_meat") or found.get("allergies"):
        return None
    named = [who for who in (found.get("people") or []) if isinstance(who, str)]
    for entry in found.get("others") or []:
        diet = entry.get("diet")
        if not diet:
            continue
        who = entry.get("who") or _person_from_pronoun(text, memory, named)
        return _diet_sentence(who, diet)
    return None

def _object_pronoun(who, known=None):
    """The pronoun a person takes as an object: "her", "him" or "them"."""
    said = _pronoun_for(who, known)
    return {"she": "her", "he": "him"}.get(said, "them")

def _who_the_pronoun_means(low, memory, pronoun):
    """The last person the chat named whose pronoun fits, for "whats his name".

    The store keeps the people the chat has heard of, with what it knows about each: the last one
    the pronoun fits is who a bare "his"/"her" means, the same way `_person_from_pronoun` reads
    a bare "she"/"he" in a fact.
    """
    fits = PRONOUN_FITS.get(str(pronoun or "").lower(), ())
    allowed = set()
    for key in fits:
        allowed |= set(extract.HE if key == "he" else extract.SHE)
    if not allowed:
        return ""
    people = [who for who in (user(memory).get("people") or []) if isinstance(who, str)]
    people += [str(entry.get("who")) for entry in others(memory) if entry.get("who")]
    for who in reversed(people):
        if who in allowed:
            return who
    # A role can be held by anybody, so the word for the person says nothing about their sex and
    # a tutor or a childminder was nobody a "his" or a "her" could mean. The title the chat was
    # given says it ("my tutor is called mrs owens" then "whats her name"), and with one person
    # on the table the pronoun means them whatever their word says.
    record = _topics.about(memory)
    if record is None:
        return ""
    who = str(record.get("who") or "")
    titled = ""
    for entry in others(memory):
        if str(entry.get("who") or "") != who:
            continue
        title = str(entry.get("name") or "").split(" ")[0].strip(".").lower()
        if title in extract.TITLE_GENDER:
            titled = extract.TITLE_GENDER[title]
    if titled:
        # The title says it plainly, so it settles the pronoun both ways: a "his" after "my tutor
        # is called mrs owens" is not the tutor, and is answered honestly rather than as her.
        return who if titled in fits else ""
    if who and who not in extract.SHE and who not in extract.HE \
            and len({said for said in people if said}) == 1:
        return who
    return ""

def _a_relations_name_reply(memory, low, text=""):
    """What someone in the family is called: "Your sister is called Meg."

    The name is filed with the person ("my sister is called meg", "my brother dan"), so the ask
    is answered from what the chat was told. A person the chat knows of with no name gets the
    honest "you haven't told me" rather than a search hedge: the store does know the sister.
    """
    if not isinstance(low, str):
        return None
    match = OTHER_NAME_ASK.search(low)
    who = ""
    if match:
        groups = ("who1", "who2", "who3", "who4", "who5", "who6", "who7", "who8", "who9",
                  "who10", "who11")
        who = next((match.group(group) for group in groups
                    if match.groupdict().get(group)), "")
        who = (who or "").lower()
        # "my babys name", "my toddlers name": the ask "my baby is called mia" said back. A word
        # that names one person with no relation after it ("baby", "toddler") is somebody the
        # store files, so the ask can name them, and the "s" on the end is the possessive.
        if (who.endswith("s") and (who[:-1] in extract.KIN_WORDS
                                   or who[:-1] in extract.ALONE_PERSON)):
            who = who[:-1]
        who = _with_an_in_law(who, low)
        group = _the_group(who)
        if group:
            if who in A_ONE_PERSON_WORD:
                # "what is my child called" names one person with a word that covers several,
                # which is the ask "what is my daughter called" after the same line: the store
                # holds both names and cannot say which one is meant, so it asks. Reading it as
                # the group denied the pair it had just been given, or picked one of the names.
                narrowed = _which_one_of_them(memory, who)
                if narrowed:
                    return narrowed
            # "what are my children called" asks about the several people in one word: the answer
            # is every name the store holds for that group, or the honest line about the names it
            # was never given - never the search hedge, one line after it filed both children.
            together = _what_the_group_is_called(group, memory)
            if together:
                return together
            # A line that named the group is one the store failed to file, and telling the person
            # they never told us would deny what they just said: "my kids are called tom and sam"
            # keeps the answer it had rather than being called back as a name the chat lacks.
            if _the_group_was_said(who, memory):
                return None
            # Nothing was ever said about these people, and the ask is about the asker's own
            # family: the honest line names the group, where the hedge said the bot would look
            # it up ("That's beyond what I know well ... a search will turn up better sources"
            # in answer to "what are my parents called"). The store knows what it holds.
            return _vary(["You haven't told me what your " + _the_group_word(who) + " are called.",
                          "I don't have any names for your " + _the_group_word(who) + " yet.",
                          "You've not said what your " + _the_group_word(who)
                          + " are called."], memory)
        if (who not in extract.KIN_WORDS and who not in extract.ALONE_PERSON
                and not extract.an_in_law(who)):
            return None
        # A wide kin word ("stepmum", "grandson") is only a person the chat knows of once it has
        # heard of them: an empty chat is not told "you haven't told me your stepmum's name" about
        # somebody nobody mentioned.
        if (who not in extract.RELATIONS and not extract.an_in_law(who)
                and not _a_person_in_the_store(memory, who)):
            return None
    else:
        point = PRONOUN_NAME_ASK.search(low)
        if not point:
            return None
        pronoun = next((point.group(group) for group in
                        ("pos", "sub", "obj", "pos2", "sub2", "obj2", "pos3", "pos4")
                        if point.groupdict().get(group)), "")
        if pronoun in ("their", "they", "them"):
            # "what are their names" about the children the chat has just named: the pronoun is
            # the two of them, so the answer is both names rather than the last one filed.
            together = _everyone_they_mean(memory)
            if together:
                return together
        who = _who_the_pronoun_means(low, memory, pronoun).lower()
        if not who:
            # The pronoun points at the one animal the chat has named: "i have a cat called max" /
            # "hes 4 months" / "what did i say his name was" was told it had no name for him,
            # because the age said about him a turn earlier is not a person the pronount fits.
            named_pet = _the_one_animal_with_a_name(memory)
            if named_pet:
                return named_pet
            return None
    told = others(memory)
    mine = [entry for entry in told if str(entry.get("who") or "").lower() == who]
    named = [entry for entry in mine if entry.get("name")]
    if named:
        name = _called(named[-1].get("name"))
        return _vary(["Your " + who + " is called " + name + ".",
                      name + " \u2014 your " + who + ", you told me.",
                      "You said your " + who + " is called " + name + "."], memory)
    # A pair of names said for two people ("my mum and dad are dave and sue") does not say which
    # name is whose, so the answer says what was said and asks for the one thing that settles it.
    # Guessing would file a name about their mother they never gave; denying the line would throw
    # away something they did say.
    for entry in told:
        pair = [word.strip() for word in str(entry.get("who") or "").lower().split(" and ")]
        pair_names = [str(one) for one in entry.get("names") or []]
        if ((len(pair) > 1 and who in pair) or _canon_relation(who) in _relations_of(
                entry.get("who"))) and len(pair_names) > 1:
            return ("You told me your " + str(entry["who"]) + " are "
                    + _a_list_of_names(pair_names) + " - which one is your " + who + "?")
    in_law_of_the_same = [entry for entry in told
                          if extract.an_in_law(entry.get("who"))
                          and str(entry.get("who") or "").lower().startswith(who + " in law")]
    if mine or in_law_of_the_same or who in [str(person).lower() for person in
                                             (user(memory).get("people") or [])]:
        # The person is known to the chat even with no name filed for them ("my sister had a
        # baby"), so the honest line is about the name, not about the sister. A brother in law
        # is not the brother: the chat has heard of the family, and the ask about the brother is
        # one it has nothing for - handing back the in-law's name answered for the wrong person.
        return "You haven't told me your " + who + "'s name."
    return None

def _the_group(who):
    """The people a group word names, or nothing: "children", "childrens", "kids", "boys".

    The plural of the word and its possessive form are the same ask ("what are my childrens
    names"), and a word that names no group is left to the relation readers.
    """
    return PERSON_GROUP.get(_the_group_word(who), ())

def _in_group(who, group):
    """Whether what the store filed a person under is in a group of relations."""
    who = str(who or "").lower()
    return (who in group or CHILD_OF.get(who, "") in group
            or (who.endswith("s") and who[:-1] in group))

def _the_people(entries):
    """The people as one phrase: "daughter and son", "sons", "children"."""
    words = []
    counts = {}
    for entry in entries:
        # The word they were filed under is the word the answer uses: a "my kids are 4, 7 and 9"
        # entry says "your kids", not "your kid".
        who = str(entry.get("who") or "").lower()
        counts[who] = counts.get(who, 0) + 1
        if who not in words:
            words.append(who)
    spoken = []
    for word in words:
        if counts[word] > 1 and not word.endswith("s"):
            word += "s"
        spoken.append(word)
    return _and_list(spoken)

A_ONE_PERSON_WORD = frozenset("""child kid baby twin parent grandchild grandparent boy girl lad
lass teenager""".split())

def _which_one_of_them(memory, who):
    """The several people a one-person word covers, when the store cannot say which is meant.

    Two names on file for the group is the case worth asking about: saying either one is a guess
    about the chat's own family, and denying the pair is denying what was said a turn before.
    With one person on file there is nothing to ask, so the caller answers with them.
    """
    group = _relations_of(who)
    mine = [entry for entry in others(memory) if isinstance(entry, dict)
            and _in_the_group(entry.get("who"), group)]
    said = []
    for entry in mine:
        names = [str(one) for one in (entry.get("names") or []) if str(one).strip()]
        if len(names) > 1:
            said.extend(_called(one) for one in names)
        elif entry.get("name"):
            said.append(_called(str(entry["name"])))
    if len(said) < 2:
        return None
    return ("You told me your " + _the_people(mine) + " are "
            + _a_list_of_names(said) + " - which one do you mean?")

def _what_the_group_is_called(group, memory):
    """The names of the people a group word covers: "Emma and Jack - your daughter and son."

    Only the people the chat was told about are named, and the ones with no name are said so: a
    group the store half knows is answered honestly rather than denied. Nothing is guessed when
    the group is empty - the caller falls through to what it did before.
    """
    mine = [entry for entry in others(memory)
            if isinstance(entry, dict) and _in_group(entry.get("who"), group)]
    if not mine:
        return None
    named = [entry for entry in mine if entry.get("name") or entry.get("names")]
    unnamed = [entry for entry in mine if not (entry.get("name") or entry.get("names"))]
    if not named:
        # "my kids are 4, 7 and 9" is several people filed as one entry, so the plural is the
        # word they were filed under as well as the count.
        many = len(mine) > 1 or any(str(entry.get("who") or "").lower() in PLURAL_PEOPLE
                                    for entry in mine)
        return ("You've told me about your " + _the_people(mine) + ", not what "
                + ("they are" if many else "he or she is") + " called.")
    said = []
    paired = False
    for entry in named:
        names = [str(one) for one in (entry.get("names") or []) if str(one).strip()]
        if len(names) > 1:
            said.extend(_called(one) for one in names)
            paired = True
        else:
            said.append(_called(str(entry.get("name") or names[0])))
    names = _and_list(said)
    if paired and not unnamed:
        # "my parents are called janet and brian" is one fact about two people: the line never
        # said which name is whose, so both are said back. Naming only the first dropped a name
        # the chat had just given ("Your parents are called Janet.").
        return "You told me your " + _the_people(mine) + " are called " + names + "."
    if not unnamed:
        if len(said) > 1:
            return names + " \u2014 your " + _the_people(mine) + "."
        return names + ", your " + _the_people(mine) + "."
    return names + ", and your " + _the_people(unnamed) + " you haven't named."

def _everyone_they_mean(memory):
    """"What are their names" after two children were named, and nothing else was: them.

    The pronoun only answers when every person the store holds is a child, so a chat with a mum
    and a son still leaves "their" unanswered rather than naming the wrong two people.
    """
    told = [entry for entry in others(memory) if isinstance(entry, dict)]
    if len(told) < 2 or not all(_in_group(entry.get("who"), CHILD_RELATIONS)
                                for entry in told):
        return None
    return _what_the_group_is_called(CHILD_RELATIONS, memory)

def _who_is_the_name_reply(memory, low):
    """The person a name they gave belongs to: "Meg is your sister."

    A name is filed on the person (`others[...]["name"]`), so a line that asks about the name by
    itself is asking about someone the chat already knows. Only a name already filed is claimed:
    "who is the queen" and "whos bob" keep the reply they had. A relation the person was filed
    under is compared through the same concept table the recalls use, so "is meg my mum" after
    "my mother is called meg" is a yes and not a no.
    """
    if not isinstance(low, str):
        return None
    match = WHO_IS_NAME_ASK.search(low)
    if not match:
        return None
    parts = match.groupdict()
    said = (parts.get("name1") or parts.get("name2") or parts.get("name3")
            or parts.get("name4") or "").strip().lower()
    asked_who = (parts.get("who3") or parts.get("who4") or "").strip().lower()
    if asked_who.endswith("s") and asked_who[:-1] in extract.RELATIONS:
        asked_who = asked_who[:-1]
    if not said:
        return None
    if parts.get("name1") or parts.get("name2"):
        # Only the name on its own asks about the chat: "who is meg" is about the Meg they told me
        # about, and "who is meg on eastenders" is about a programme, which is a search, not a
        # claim. A made-up answer to a real question is worse than the hedge it replaces.
        group = "name1" if parts.get("name1") else "name2"
        tail = low[match.end(group):].strip(" \t?.,!;:'\"")
        if tail and not set(tail.split()) <= NAME_ASK_TAIL:
            return None
    for entry in reversed(others(memory) or []):
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        who = str(entry.get("who") or "").strip().lower()
        if not name or not who or name.lower() != said:
            continue
        proper = _tidy_name(name)
        if asked_who:
            same = CONCEPTS.get(asked_who, asked_who) == CONCEPTS.get(who, who)
            if same:
                return _vary(["Yes - " + proper + " is your " + who + ".",
                              "That's right: " + proper + " is your " + who + "."], memory)
            return "No - " + proper + " is your " + who + "."
        return _vary([proper + " is your " + who + ".",
                      proper + " \u2014 your " + who + ", you told me.",
                      "That's " + proper + ", your " + who + "."], memory)
    for entry in reversed(others(memory) or []):
        # A group given whole ("my kids are called jack and emma") files both names on the one
        # entry and no name on either person, so the name on its own was read as somebody the
        # store had never heard of: "who is jack" two turns after both names were given. The
        # line said which people, not which one of them, so the answer says that and no more.
        if not isinstance(entry, dict):
            continue
        names = [str(one).strip() for one in (entry.get("names") or []) if str(one).strip()]
        who = str(entry.get("who") or "").strip().lower()
        if len(names) < 2 or not who or not any(one.lower() == said for one in names):
            continue
        proper = _tidy_name(next(one for one in names if one.lower() == said))
        if asked_who:
            same = CONCEPTS.get(asked_who, asked_who) in _relations_of(who)
            if same:
                return _vary(["Yes - " + proper + " is one of your " + who + ".",
                              "That's right: " + proper + " is among your " + who + "."],
                             memory)
            return proper + " is one of your " + who + ", not your " + asked_who + "."
        return _vary([proper + " is one of your " + who + " - you told me your " + who
                      + " are " + _a_list_of_names(names) + ".",
                      "One of your " + who + ": you said your " + who + " are "
                      + _a_list_of_names(names) + "."], memory)
    # The same thing for an animal: "i have a cat called tom" files the name on the pet, so
    # "whos tom" is a question about the chat and not about the world.
    for pet in (user(memory).get("pets") or []):
        if not isinstance(pet, dict):
            continue
        name = str(pet.get("name") or "").strip()
        if not name or name.lower() != said:
            continue
        proper = _tidy_name(name)
        animal = str(pet.get("animal") or "pet").strip().lower()
        if asked_who:
            same = CONCEPTS.get(asked_who, asked_who) == CONCEPTS.get(animal, animal)
            if same:
                return _vary(["Yes - " + proper + " is your " + animal + ".",
                              "That's right - " + proper + " is your " + animal + "."],
                             memory)
            return proper + " is your " + animal + ", not your " + asked_who + "."
        return _vary([proper + " is your " + animal + ".",
                      "That's " + proper + ", your " + animal + "."], memory)
    return None

def _kids_reply(memory, low):
    """How many children they have, said back: "You've got two kids."

    The number came with the children ("i have two kids"), so the ask is answered from the chat
    rather than hedged, and the line says the number they gave and nothing else.
    """
    if not _kids_ask(low):
        return None
    held = user(memory).get("kids")
    if isinstance(held, int) and held == 0 and not isinstance(held, bool):
        # A person who said they have none has answered the question: "i dont have any kids" then
        # "how many kids do i have" was told "You haven't told me how many kids you have yet".
        return _vary(["You told me you don't have any kids.",
                      "None \u2014 you said you don't have any.",
                      "You said you haven't got any kids."], memory)
    if held is None:
        # A child named without an age ("my son is four" said in words) is in `people` and not in
        # `others`, and it is still a child they have told us about.
        named = [entry for entry in (others(memory) or [])
                 if isinstance(entry, dict) and str(entry.get("who") or "").lower()
                 in CHILD_RELATIONS]
        if not named:
            named = [{"who": who} for who in (user(memory).get("people") or [])
                     if str(who).lower() in CHILD_RELATIONS]
        if named:
            who = str(named[0].get("who") or "child").lower()
            return _vary(["You've mentioned your " + who
                          + " \u2014 how many have you got altogether?",
                          "I know about your " + who + ", but not a number. How many have you "
                          "got in all?"], memory)
        # Their own children, not something to look up: the honest answer is that they have not
        # said, rather than a hedge about searching online for their own life.
        return _vary(["You haven't told me how many kids you have yet.",
                      "I don't have a number from you \u2014 how many have you got?",
                      "You haven't said how many children you've got."], memory)
    count = int(held)
    if count == 1:
        return _vary(["You've got one kid.", "One kid, as you told me.",
                      "You said you've got one kid."], memory)
    word = NUMBER_WORDS.get(count, str(count))
    kids = "children" if count == 2 else "kids"
    return _vary(["You've got " + word + " " + kids + ".",
                  word.capitalize() + " " + kids + " \u2014 that's what you told me.",
                  "You said you've got " + word + " " + kids + "."], memory)

def _and_list(words):
    """The words as one phrase: "nuts", "mum and dad", "Meg, Dan and Sam"."""
    words = [str(word) for word in words if word]
    if len(words) < 2:
        return "".join(words)
    return ", ".join(words[:-1]) + " and " + words[-1]

def _lines_a_person_moved(memory):
    """The lines about someone whose fact a later line gave again with another value.

    The person's facts live under one `"other"` entry each (a dict), which the general moved-line
    reader skips because a dict may be a thing that grows. Here the dict is read key by key, so
    "my sister is 12" is known to be out of date once "sorry shes 14" has given the age 14.
    """
    last = {}
    moved = set()
    for entry in memory.get("facts_log") or ():
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if not isinstance(value, dict):
            continue
        who = str(value.get("who") or "").lower()
        if not who:
            continue
        text = " ".join(str(entry.get("text") or "").lower().split())
        if not text:
            continue
        for key, held in value.items():
            if key == "who" or isinstance(held, (list, dict)):
                continue
            slot = (who, key)
            older = last.get(slot)
            if older and older[0] != str(held).lower():
                moved.add(older[1])
            last[slot] = (str(held).lower(), text)
    return moved

def _only_a_pointer(flat):
    """True for a line that only points at a fact: "she isnt", "my wife is not coeliac", "my
    wife is too".

    Those are the fact given to someone and taken back, not something to say back about the
    person: quoting one answers "what do you know about my wife" with "you told me your wife
    isnt" or "your wife is too".
    """
    if SAME_FACT_ABOUT.match(flat):
        return True
    for shape in (SAME_FACT_AGAINST, SAME_FACT_AGAINST_PRONOUN):
        match = shape.match(flat)
        if not match:
            continue
        rest = (match.groupdict().get("rest") or "").strip(" ?!.")
        if not rest or rest.split()[0] in NEGATIVE_TAIL:
            return True
    return False

def _a_known_person(memory, who):
    """What the chat holds about one person: the facts filed against them and the lines said.

    The two are kept apart because they answer differently: a fact goes into the sentence about
    the person, and a line is something they said, said back in their own words. A line that is
    itself an ask about them ("what did i say about my sister") is not something they told me
    about her, so it is skipped: otherwise the follow-up "what else did i say" quotes the ask.
    A line that carries on in "she"/"he"/"they" belongs to the person named just before it, so
    "my sister is called meg" then "she doesnt eat meat" is two lines about the sister.
    """
    family = _the_same_person(who)
    entry = {}
    for known in others(memory):
        if str(known.get("who") or "").lower() not in family:
            continue
        # The facts for one person arrive in several entries ("my son is 7", then "my son is
        # allergic to nuts"), so they are read together: the age from one and the allergy from
        # the other are the same son.
        for key, value in known.items():
            if key == "who":
                continue
            if isinstance(value, list) and isinstance(entry.get(key), list):
                entry[key] += [item for item in value if item not in entry[key]]
            else:
                entry[key] = value
    # "my mum" is the usual way of naming her, and a line that opens with the word ("mum is
    # allergic to shellfish") is about the same person. The word has to open the line: "dad jokes"
    # in the middle of a line about something else is not their dad.
    pattern = _the_name_pattern(who)
    # A line that carries on in a pronoun is about the person named just before it, so
    # "my sister is called meg" then "she doesnt eat meat" is two lines about the sister.
    carried = re.compile(r"^\s*(?:and\s+|also\s+)?(?:she|he|they|her|him|them|his|hers|their)"
                         r"(?:'s|'re|s|re)?\b", re.I)
    lines = []
    # A line whose fact a later line gave again with a different value is not something to say
    # back: "my sister is 12" / "sorry shes 14" would answer "Your sister is 14. You also said
    # my sister is 12", handing back the value they just corrected. The store holds the 14, so
    # the old line is left out and the fact speaks for itself.
    moved = _lines_a_person_moved(memory)
    current = ""
    for turn in _every_line(memory):
        line = str(turn.get("user") or "")
        if not line:
            continue
        named_here = _a_relation_in(line)
        if named_here:
            current = named_here
        if _asks(line) or _about_this_chat(line) or ABOUT_PERSON_ASK.search(line.lower()):
            continue
        if ((pattern.search(line) and not A_PROGRAMME_IS_ON.search(line))
                or (current in family and carried.match(line))):
            flat = " ".join(line.lower().split()).strip(" ?!.")
            if flat in moved:
                continue
            if _only_a_pointer(flat):
                # "she isnt" is the fact taken back and "my wife is too" is the fact given to her,
                # not something to say back about the person: quoting one would answer "what do
                # you know about my wife" with "you told me your wife isnt".
                continue
            lines.append(line)
            # "his names tom" after "my husband" is his name, and a name is said properly:
            # "your husband" and a bare "his names tom and hes a teacher" is a line of theirs
            # read back with nothing added, which is what a search result does.
            given = _a_name_in_a_pronoun_line(line)
            if given and not entry.get("name"):
                entry["name"] = given
                lines = []
    # A line that gives the name already filed for them says nothing the store cannot say
    # better: "my mums name is Ann" is answered "Your mum is called Ann", not read back as
    # "You told me your mums name is Ann".
    if entry.get("name"):
        lines = [one for one in lines if not _only_the_name(one, entry["name"], who)]
    return entry, lines

def _only_the_name(line, named, who):
    """True when a line says nothing but the name the store already files for the person.

    "my mums name is Ann", "my sister is called Meg": the name is what the store answers with,
    in the words it uses for a name ("Your mum is called Ann"), so the raw line is left out
    rather than quoted back with its "my mums name is" still in it.
    """
    person = set(_the_same_person(who))
    drop = ({"my", "our", "your", "the", "is", "was", "name", "names", "called", "and", "she",
             "he", "her", "his", "they", "their", "them", "also", "s"} | person)
    # A figure is a word of the line too: "my mum is called janet and shes 72" says the name and
    # her age, so the line is not only the name and is still read back whole.
    words = set(re.findall(r"[a-z0-9]+", str(line or "").lower()))
    # The possessive is written without its apostrophe more often than with it ("my mums name"),
    # so the person's word plus an "s" is the person again.
    words = {word[:-1] if word.endswith("s") and word[:-1] in (drop | person) else word
             for word in words}
    return words - drop == {str(named or "").lower()}

def _a_name_in_a_pronoun_line(line):
    """The name a line gives for the person it only calls "his"/"her", or "".

    "his name is tom", "his names tom", "her name's meg": the person is the one named a line
    before, so the name is theirs and the store can say "Your husband is called Tom".
    """
    match = re.match(r"^\s*(?:and\s+|also\s+)?(?:his|her|their)\s+names?\s*"
                     r"(?:'s|is\s+|are\s+)?(?P<name>[a-z]{2,})\b", str(line or ""), re.I)
    if not match:
        return ""
    name = match.group("name").lower()
    if name in NOT_A_NAME:
        return ""  # "his name is not important", "her names still the same": no name there
    return name

NOT_A_NAME = frozenset("""a an the not no still same old different changed change hard difficult
important complicated long short funny strange odd weird right wrong fine ok okay good bad""".split())

def _named_back(who, line):
    """"she doesnt eat meat" is said back as "your sister doesnt eat meat", verb and all.

    The pronoun carries its own verb when it is written as one word ("shes 32" holds "is"), so
    dropping it whole would leave "your sister 32": the verb is put back in words.
    """
    def whose(match):
        word = match.group(0).lower()
        head = "your " + who
        if word.endswith("re"):
            return head + " are"
        if word.endswith("s") and not word.endswith("ss"):
            return head + " is"
        return head

    def belonging(match):
        # "her birthday is in june" is the sister's birthday, and a bare "her" says nothing in a
        # reply that has just changed the subject back to her.
        return "your " + who + ("'" if _plural_person(who) else "'s")

    line = str(line or "")
    # A line that already names the person further on ("they said your mum is 72") is not theirs
    # to rewrite at the front: "your mum said your mum is 72" says one person twice and reads as
    # two. The words they used are said back as they were.
    if not re.search(r"\byour\s+" + re.escape(who) + r"\b", line, re.I):
        line = re.sub(r"^(?:and\s+)?(?:she|he|they)(?:'s|'re|s|re)?\b", whose, line, re.I)
        line = re.sub(r"^(?:and\s+)?(?:his|her|their)\b", belonging, line, re.I)
    return line

def _a_relation_in(line):
    """The relation a line is about, read loosely: a noun right after it is a thing of theirs.

    "my dad had a heart attack" names the dad, which the strict reader of a person misses (the
    word after "dad" is "had", so it cannot tell the person from a thing of theirs). This reading
    is only used to follow who a "she"/"he" line is about, so it can afford to be loose: a noun
    straight after the relation ("my mums car") still takes the word away from the person.
    """
    low = str(line or "").lower()
    for relation in extract.RELATIONS:
        for hit in re.finditer(r"\b" + relation + r"s?\b", low):
            rest = low[hit.end():]
            if rest.startswith("'s") or rest.startswith("s'"):
                rest = rest.split("'", 1)[1][1:]
            words = rest.split()
            if words and words[0].strip(".,!?;:") in extract.COMPOUND_AFTER:
                continue
            return relation
    return ""

def _person_clauses(who, entry):
    """The predicates about one person, subject left off: "is 32", "doesn't eat meat".

    They are kept as clauses rather than sentences so two facts join into one line - "Your
    sister is 32 and allergic to nuts" - the way a person says it, not a list of six sentences.
    """
    be = "are" if _plural_person(who) else "is"
    clauses = []
    age = entry.get("age")
    if isinstance(age, int) and not isinstance(age, bool):
        clauses.append(be + " " + str(age))
    allergies = [str(one) for one in (entry.get("allergies") or []) if one]
    if allergies:
        clauses.append(be + " allergic to " + _and_list(allergies))
    condition = entry.get("condition")
    if isinstance(condition, list):
        condition = str(condition[0]) if condition else ""
    if str(condition or "").strip():
        clauses.append(be + " " + str(condition).strip())
    diet = str(entry.get("diet") or "").strip()
    if diet:
        clauses.append(_a_diet_predicate(who, diet))
    dislikes = [str(one) for one in (entry.get("dislikes") or []) if one]
    if dislikes:
        clauses.append((_does_not(who) + " like " + _and_list(dislikes)).strip())
    return clauses

def _date_written_as_a_date(value):
    """A month inside a date is written with a capital: "4 may" is said "4 May"."""
    said = str(value or "")
    for month in extract.MONTHS:
        said = re.sub(r"\b" + month + r"\b", month[:1].upper() + month[1:], said, flags=re.I)
    # A day kept as an ordinal keeps it, and a date said in a sentence needs the word that makes
    # it one: "4th may" is said "the 4th of May", never "the 4th May".
    ordinal = re.match(r"^(\d{1,2}(?:st|nd|rd|th))\s+([A-Z][a-z]+)$", said)
    if ordinal:
        said = "the %s of %s" % (ordinal.group(1), ordinal.group(2))
    return said

def _pronoun_person(text, memory):
    """Who "her"/"him"/"them" is in this line: the person last named, when the word fits them.

    "him" after only a mum was mentioned names nobody: answering with the mum's facts is a wrong
    answer, which is worse than leaving the line to whoever else can answer it. A plural person
    ("my parents") takes "them" and "they".
    """
    low = str(text or "").lower()
    if not re.search(r"\b(?:her|him|them|she|he|they)\b", low):
        return ""
    who = _person_from_pronoun(text, memory)
    if not who or _plural_person(who):
        return who
    if re.search(r"\b(?:her|she)\b", low) and who not in extract.SHE:
        return ""
    if re.search(r"\b(?:him|he)\b", low) and who not in extract.HE:
        return ""
    return who

def _a_line_about(memory, who):
    """The newest line of theirs that names this person, or None.

    Only used when the store filed no fact and no line against them, so it is the difference
    between "you haven't told me anything about your dad" and the line that said what the dad
    was doing. A line that asks about the person is not a line about them, and neither is the
    ask being answered now.
    """
    for turn in reversed(_every_line(memory)):
        line = str(turn.get("user") or "").strip()
        # An ask is not something they told me: "how old is my dad", "is my sister coming on
        # friday", "should i call my mum" are questions about the person, and saying one back as
        # "you told me how old is your dad" puts words in their mouth and contradicts the
        # "you haven't told me how old your dad is" the line itself got a turn before.
        if (not line or "?" in line or _asks(line)
                or ABOUT_PERSON_ASK.search(line.lower())):
            continue
        if _only_a_pointer(" ".join(line.lower().split()).strip(" ?!.")):
            # "my wife is too" and "she isnt" point at a fact rather than saying one, so neither is
            # something to hand back as what they told me about her.
            continue
        if _the_word_for_them(who).search(line):
            return line
    return None

OWNED_ASK = re.compile(
    r"\b(?:what|which)\s+(?P<a>[a-z][a-z-]*)\s+(?:do|did|does)\s+(?:i|u|you)\s+"
    r"(?:drive|ride|use|have|own)\b"
    r"|\b(?:what|which)\s+(?P<b>[a-z][a-z-]*)\s+(?:have|has)\s+(?:i|u|you)\s+"
    r"(?:got|had|have|owned|driven|ridden|used)\b"
    r"|\b(?:what|which)\s+(?P<c>[a-z][a-z-]*)\s+(?:is|was)\s+mine\b"
    r"|\b(?:what|which)\s+(?P<d>[a-z][a-z-]*)\s+am\s+i\s+"
    r"(?:driving|riding|using|in)\b"
    r"|\b(?:do|can|could|did)\s+(?:u|you)\s+(?:remember|recall|know)\s+(?:what|which)\s+"
    r"(?P<e>[a-z][a-z-]*)\s+(?:i|u|you)\s+(?:drive|ride|use|own|have)\b"
    # ...and the same ask with the frame already off it: the store reads "do you know what car i
    # drive" by its own words once the knowing frame comes away, which leaves "what car i drive".
    r"|\b(?:what|which)\s+(?P<f>[a-z][a-z-]*)\s+(?:i|u|you)\s+(?:drive|ride|use|own)\b", re.I)

def _a_that_fits(name):
    """The article a name takes: "an iPhone 13", "a Pixel", "a BMW", "an Audi".

    A name written in capitals is said letter by letter, so it takes "a" whatever its first
    letter looks like ("a BMW", "a VW"), and every other name takes the article of its sound.
    """
    first = str(name or "").split()[0] if str(name or "").split() else ""
    if len(first) > 1 and first.isupper():
        return "a"
    return "an" if first[:1].lower() in "aeiou" else "a"

def _a_thing_i_own_reply(memory, low):
    """The make of a thing they said was theirs: "your car is a Ford Fiesta".

    Only a thing the store was told the make of is given one. "my car is old" says nothing about
    the make, so the ask is answered by saying the make was never said rather than by guessing,
    and a thing the person never mentioned at all keeps the ordinary answer.
    """
    held = user(memory).get("owns")
    if not isinstance(held, dict) or not held:
        held = {}
    for match in OWNED_ASK.finditer(low):
        thing = next((word for word in match.groups() if word), "")
        thing = thing.replace("-", " ")
        if not thing:
            continue
        name = held.get(thing) or held.get(thing.rstrip("s"))
        if thing == "car" and not name:
            # "i drive an old fiesta" then "what car have i got": the fact reader holds the car
            # and this reader asks first, so without the fallback the store filed the car and
            # denied it in the next breath ("you haven't told me the make of your car").
            name = user(memory).get("car") or ""
        if thing == "car" and name:
            # One fact, one shape: a model is capitalised however the car was filed.
            return car_line(name)
        said = {"bike": ("You ride ", "Your bike is "),
                "motorbike": ("You ride ", "Your motorbike is ")}.get(thing)
        if name:
            article = _a_that_fits(name)
            if said:
                return pick([said[0] + article + " " + name + ".",
                             said[1] + article + " " + name + "."], memory)
            if thing == "phone":
                return pick(["Your phone is " + article + " " + name + ".",
                             "You've got " + article + " " + name + "."], memory)
            return pick(["Your " + thing + " is " + article + " " + name + ".",
                         "You told me your " + thing + " is " + article + " " + name + "."],
                        memory)
        if thing in extract.OWNED:
            # They asked about a thing nobody has mentioned the make of. Saying so is the honest
            # answer and it is not a denial: whatever they told me about the car is still true.
            return pick(["You haven't told me the make of your " + thing,
                         "You've not said what your " + thing + " is"], memory) + "."
    return None

def _about_a_person_reply(memory, low, text=""):
    """Everything held about someone they mentioned: "what do you know about my sister?".

    "what have i told you about my mum" had a reply and "what do you know about my mum" had
    none, so the same ask in the other words fell to the search hedge while the store sat on the
    answer. The person is read first, then the facts filed against them (name, age, allergies,
    what they eat) and the last line said about them: the store says the person back in its own
    words instead of quoting a line, which is what a friend would do. A "what else" ask gets the
    honest "that's everything" once the whole person has been described, never the same sentence
    again.
    """
    if not isinstance(low, str):
        return None
    # "what do you know about ada" is the same ask when Ada is a name the chat was given for
    # someone: the name is filed with the person, and people ask by the name they were told.
    called = _the_person_called(memory, low)
    match = (ABOUT_PERSON_ASK.search(low) or _continues_an_about_ask(memory, low)
             or (ABOUT_A_NAME.search(low) if called else None))
    if not match:
        return None
    who = _named_person(low, memory) or called
    if not who:
        # "what do you know about her" asks about the person the chat was just on: the pronoun
        # is read the way every other line in the store reads it, so the follow-up reaches the
        # facts the named ask reaches.
        who = _pronoun_person(text or low, memory)
    if not who:
        # "what do you know about my kids" names no one relation, so every branch above found
        # nobody: the children are filed as several people under one word, and the whole of them
        # is the answer.
        children = _about_the_children_reply(memory, low)
        if children:
            return children
        return None
    entry, lines = _a_known_person(memory, who)
    named = _called(entry.get("name")) if entry.get("name") else ""
    clauses = _person_clauses(who, entry)
    birthday = str(entry.get("birthday") or "").strip()
    if birthday and not clauses and not lines:
        # A date filed against a person is a fact about them like an age is, and a birthday can
        # be all the store holds: the reader had only the line they said it in, which - once a
        # correction had moved the date - was the line that carried the one they took back.
        return _vary(["Your " + who + "'s birthday is " + _date_written_as_a_date(birthday) + ".",
                      "You told me your " + who + "'s birthday is "
                      + _date_written_as_a_date(birthday) + "."], memory)
    if not clauses and named and not lines:
        # The only thing the chat holds about them is the name they gave for them a line
        # before ("my husband" then "his names tom").
        return _vary(["Your " + who + " is called " + named + ".",
                      "Your " + who + " is " + named + "."], memory)
    if not clauses and not lines:
        # A line the chat has about them is something to say, even when no fact was filed from
        # it: "my mum is 72 and dad is 74" files the mum's age and not the dad's, so "what do you
        # know about my dad" cannot say "you haven't told me anything" about a line they just
        # said. The line that names them is said back in their words.
        named_line = _a_line_about(memory, who)
        if named_line:
            return ("You told me " + _named_back(who, you(named_line)).strip().rstrip(".") + "."
                    if not ABOUT_PERSON_MORE.search(str(text or ""))
                    else "That's all I have: " + _named_back(who, you(named_line))
                    .strip().rstrip(".") + ".")
        # The person is known to the chat only by name ("my sister is coming on friday"), or
        # not at all: there is nothing to say back, so the store says so instead of hedging. The
        # second ask in a row is answered as a second ask, not with the same line in other words.
        if ABOUT_PERSON_MORE.search(str(text or "")):
            return "You haven't told me anything about your " + who + " yet."
        return _vary(["You haven't told me anything about your " + who + " yet.",
                      "Nothing on your " + who + " so far \u2014 tell me and I'll keep it."],
                     memory)
    subject = "Your " + who + ((" " + named) if named and clauses else "")
    facts = ""
    if clauses:
        if len(clauses) == 1:
            facts = subject + " " + clauses[0]
        else:
            rest = [clause[3:] if clauses[0].startswith("is ") and clause.startswith("is ")
                    else clause for clause in clauses[1:]]
            facts = subject + " " + clauses[0] + " and " + _and_list(rest)
    said = ""
    if lines:
        line = you(lines[-1]).strip().rstrip(".")
        # "she doesnt eat meat" is about the person they named a line earlier, so the reply names
        # them: "You told me your sister doesnt eat meat" says who, where a bare "she" does not.
        line = _named_back(who, line)
        if named:
            # The name they gave is written the way a name is written: "Meg" inside the line.
            line = re.sub(r"\b" + re.escape(named) + r"\b", named, line, flags=re.I)
        said = line
    # One line already carrying the facts is the whole answer: "your mum is 72 and lives in
    # york" says the age, and "Your mum is 72. You told me your mum is 72 and lives in york"
    # says it twice. The facts lead only when they add something the line left out.
    if said and (not facts or _covers(said, clauses)):
        # A line that was itself a telling comes back without the store's frame: "You told me you
        # told me about your mum" says the telling twice, and the echo already carries who told
        # whom. Same rule as `told._quote`.
        if TELLING_ALREADY.match(said):
            answer = said[0].upper() + said[1:] + "."
        else:
            answer = _vary(["You told me " + said, "You said " + said], memory) + "."
    elif facts and said and _tokens(said) <= _tokens(facts):
        # The facts already say everything the line says: the line adds nothing to it.
        answer = facts + "."
    elif facts and said:
        answer = facts + ". You also said " + said + "."
    else:
        answer = (facts or "") + "."
    if ABOUT_PERSON_MORE.search(str(text or "")) and (
            _said_everything(answer, memory)
            or re.search(r"\b(?:everything you've told me|all I've got) (?:about|on) your "
                         + re.escape(who), last_bot(memory) or "", re.I)):
        return _vary(["That's everything you've told me about your " + who + ".",
                      "That's still all I've got on your " + who + "."], memory)
    if _said_everything(answer, memory):
        # The same ask twice says the same sentence twice, which is the one thing a store that
        # hands a fact back may not do: the second time it is shorter, and still true.
        body = (facts or said or answer).strip().rstrip(".")
        return "Still: " + body[0].lower() + body[1:] + "."
    return answer

def _about_the_children_reply(memory, low):
    """What the chat holds about the children as a group: "tell me about my kids".

    Every other ask in this family names one relation ("my mum", "my sister") and the store files
    one person under it. Children are the exception: "my kids are tom 8 and ada 5" files two
    people against the same word, so the ask about them reached no person at all and fell to the
    search hedge three turns after both names were given. The answer is the children the chat
    holds, each with the age or name it was told - and when only the count was given, the count.
    """
    if not CHILDREN_ABOUT.search(str(low or "")):
        return None
    kept = [entry for entry in others(memory) if isinstance(entry, dict)
            and _in_the_group(entry.get("who"), CHILD_RELATIONS)]
    clauses = []
    for entry in kept[:4]:
        name = _called(str(entry.get("name") or "")) if entry.get("name") else ""
        names = [str(one) for one in (entry.get("names") or []) if str(one).strip()]
        if len(names) > 1:
            # "my kids are called tom and ada" is one fact about several children, and the names
            # are the whole of it: without this branch the reply said the chat held nothing two
            # turns after the names were typed.
            clauses.append("your " + str(entry.get("who") or "children") + " are called "
                           + _a_list_of_names([_called(one) for one in names]))
        elif entry.get("ages"):
            # A group given its ages as a list - "my kids are 4 and 7" - is one fact about the
            # children, and the store kept it as a list. Read only as a single age, the group had
            # no clause at all and the answer was "You've told me you have two kids, and nothing
            # more about them yet" a turn after the ages were typed.
            ages = [age for age in entry["ages"] if isinstance(age, int)]
            who = str(entry.get("who") or "children")
            said = (", ".join(str(age) for age in ages[:-1]) + " and " + str(ages[-1])
                    if len(ages) > 1 else str(ages[0]))
            clauses.append("your " + who + _is_are(who) + said)
        elif entry.get("months") and not entry.get("age"):
            # A baby's age was given in months, and is said back in months.
            clauses.append((name or ("your " + str(entry.get("who") or "child")))
                           + " is " + str(entry["months"]) + " months old")
        elif entry.get("age") or entry.get("turns"):
            clauses.append(_one_age(str(entry.get("who") or "child"), entry.get("age"),
                                    str(entry.get("turns") or ""), entry.get("to_come"),
                                    held=name).strip().rstrip("."))
        elif name:
            clauses.append("your " + str(entry.get("who") or "child") + " is called " + name)
    # A clause that begins "Your son" is folded into the sentence and takes a small letter; a
    # clause that begins with a name keeps it, because Tom is spelled with a capital.
    clauses = [clause[0].lower() + clause[1:] if clause.startswith("Your ") else clause
               for clause in clauses]
    if not clauses:
        # A name given for the group in words the name readers did not file ("i have two kids"
        # then "they are called tom and ada") is still in the chat, and the group reply reads it
        # where "what are my kids called" reads it, so it never denies a name one turn later.
        typed = _the_group_names_typed("kids", memory) or _the_group_names_typed("children", memory)
        if typed:
            clauses = ["your kids are called " + _a_list_of_names([_called(one) for one in typed])]
    if not clauses:
        counted = (memory.get("user") or {}).get("kids")
        if isinstance(counted, int) and counted:
            return _vary(["You've told me you have " + _a_number_word(counted) + " "
                          + ("kid" if counted == 1 else "kids")
                          + ", and nothing more about them yet.",
                          "Just the count: " + _a_number_word(counted) + " kids, with no name or "
                          "age yet."], memory)
        return None
    # One child is "him" or "her", and a reply that says "them" about a single daughter reads as
    # a reply about somebody else. The word for the relation already knows: the pronoun follows
    # it, the way it does in every other reply the store writes.
    one = (str(kept[0].get("who") or "") if len(kept) == 1 else "")
    about = _object_pronoun(one) if one else "them"
    if len(clauses) == 1:
        # The same ask twice may not say the same sentence twice, so there is a second way to say
        # what is held. Neither says the chat holds nothing else: the clause is the fact, and
        # "and nothing else about them yet" behind the only fact there is reads as a denial.
        first = "You've told me " + clauses[0] + "."
        second = clauses[0][:1].upper() + clauses[0][1:] + " - that's all I've got on " \
            + about + "."
        return _vary([first, second], memory)
    facts = _a_list_of_clauses(clauses)
    # The reply may open with the facts themselves ("your son is 6 and ..."), and a sentence
    # starts with a capital.
    answer = _vary([facts + " - that's what I've got on " + about + ".",
                    "That's everything I have on " + about + ": " + facts + "."], memory)
    return answer[:1].upper() + answer[1:]

def _a_list_of_clauses(clauses):
    """"Tom is 8", "Ada is 5" reads "Tom is 8 and Ada is 5", and three read with a comma."""
    said = [str(clause) for clause in clauses if str(clause)]
    if len(said) < 3:
        return " and ".join(said)
    return ", ".join(said[:-1]) + " and " + said[-1]

def _the_person_called(memory, line):
    """The person whose name the line asks about, or "".

    "my son is called ada" files the name with the son, so "what do you know about ada" has a
    person behind it even though "ada" is not a relation word. A name the chat never gave is no
    person at all, which leaves the ask to the modules that know about the world.
    """
    for match in re.finditer(r"\babout\s+([a-z][a-z'-]{1,20})\b", str(line or ""), re.I):
        word = match.group(1).lower()
        if word in extract.RELATIONS or word in extract.ALONE_PERSON:
            continue
        for entry in others(memory):
            name = str(entry.get("name") or "").strip().lower()
            if name and name == word:
                return str(entry.get("who") or "")
    return ""

def _covers(said, clauses):
    """True when one line already says the facts: a number counts as a word to be found.

    "your son is allergic to nuts" says the allergy but not the age, and the two are different
    answers, so the line is only the whole reply when every clause is in it.
    """
    seen = _tokens(said)
    return all(_tokens(clause) <= seen for clause in clauses)

def _tokens(text):
    """The words of a line to look for, with its numbers kept - content() drops them.

    The person's word is trimmed of the bare "s" it is typed with ("my mums 72"), because the
    store's own sentence uses the word without it ("your mum is 72") and the two are one fact.
    """
    words = set(content(text)) | set(re.findall(r"\d+", str(text or "")))
    return {word[:-1] if word.endswith("s") and word[:-1] in extract.RELATIONS else word
            for word in words}

def _said_everything(answer, memory):
    """True when a reply of this chat already carried every word of this one: nothing more to tell.

    Not only the last reply: "what do you know about my son" then "how old is he" then "what else
    do you know about him" asks the same person's facts a second time, and the reply that said
    them is two turns back. Any reply of the chat counts, so the person is not told the same
    sentence twice.
    """
    mine = _tokens(answer)
    if not mine:
        return False
    for turn in _every_line(memory):
        before = str(turn.get("bot") or "")
        if before and mine <= _tokens(before):
            return True
    return False

def _a_pregnancy_of_their_own(text, memory, low):
    """The person's own pregnancy said back, with the length that dates it: "Lovely news - 12 weeks."

    A pregnancy said about themselves is the same fact as one said about their wife, and the
    store kept only the second: "im 12 weeks pregnant" was congratulated ("That's great news -
    nice one. What's next?") and then forgotten, so "how far along am i" after it got a search
    hedge, and the weeks the person had just given were nowhere.
    """
    if not isinstance(text, str) or "?" in text:
        return None
    if _about_this_chat(text, memory) or OTHER_ASK.search(low) or REMINDER_MID.search(low):
        return None
    found = extract.extract(text)
    if not found.get("pregnant"):
        return None
    if isinstance(found.get("weeks"), int):
        weeks = _a_number_word(int(found["weeks"]))
        return _vary([line.format(weeks=weeks) for line in PREGNANT_OWN_SAY], memory)
    # A length nobody said is not one to invent: the pregnancy is said back without it, and the
    # ask about how far along answers honestly that it was never given.
    return _vary(["Good to know — I'll keep the drink out of anything I suggest, and the weeks "
                  "are worth telling me if you want a meal plan that fits them.",
                  "Noted, and congratulations. Nothing alcoholic in anything I suggest; say if "
                  "you want a hand with what to cook."], memory)

def _a_state_told(text, memory, low):
    """A state of another person, said back: "Noted - your wife is pregnant..."

    The line is a fact, not a symptom, so it must not go to whoever answers a worry about someone
    ("my wife is pregnant so she cant drink" was answered "What has your wife said about it - and
    how long has it been like this?"). Only a statement is read: a question asks and changes
    nothing.
    """
    if not isinstance(text, str) or "?" in text:
        return None
    if _the_ask_beats_the_receipt(text, memory):
        # The line ends on a question the cards can answer, so the fact is only what that question
        # is about: filing it is the whole job, and the receipt is a line nobody asked to have said
        # back. "my sister is veggie ... what can i cook" gets the dinner card, not "Your sister is
        # veggie."
        return None
    if _about_this_chat(text, memory) or OTHER_ASK.search(low) or REMINDER_MID.search(low):
        return None
    found = extract.extract(text)
    if found.get("diet") or found.get("allergies") or found.get("pregnant"):
        return None  # a line about the person typing is theirs, and the modules for it are theirs
    named = [who for who in (found.get("people") or []) if isinstance(who, str)]
    for entry in found.get("others") or []:
        who = entry.get("who") or _person_from_pronoun(text, memory, named)
        if not who:
            continue
        if entry.get("pregnant") and isinstance(entry.get("weeks"), int):
            # The length is what makes the fact worth keeping: said back without it the store
            # has read the line and still sounds like it did not hear the half that dates it.
            weeks = _a_number_word(int(entry["weeks"]))
            return _vary([line.format(who=who, weeks=weeks) for line in PREGNANT_WEEKS_SAY],
                         memory)
        if entry.get("pregnant"):
            return _vary([line.format(who=who) for line in PREGNANT_SAY], memory)
        if entry.get("breastfeeding"):
            return _vary([line.format(who=who) for line in FEEDING_SAY], memory)
        if entry.get("drinks") is False:
            return _vary([line.format(who=who) for line in LIMIT_SAY], memory)
    return None

WAS_A_STATE = re.compile(
    r"\b(?:was|were|had\s+been|has\s+been|have\s+been|used\s+to\s+be)\s+"
    r"(?:still\s+|also\s+|once\s+|again\s+)?"
    r"(?:pregnant|expecting(?:\s+a\s+baby)?|breastfeeding|nursing\s+a\s+baby)\b", re.I)

def _a_state_that_was(text, memory, low):
    """A pregnancy or a feeding that is over, acknowledged as the past thing it is.

    The line is not asked for and not planned round: a person who says "my wife was pregnant"
    has told the chat something that was true, and both readers that used to take it - the one
    that congratulates and the one that advises on trying for a baby - were reading the word and
    not the tense.
    """
    if not isinstance(text, str) or "?" in text:
        return None
    if _about_this_chat(text, memory):
        return None
    if not WAS_A_STATE.search(" ".join(str(text or "").split())):
        return None
    return _vary(list(STATE_WAS_SAY), memory)

PET_PART_ASK = re.compile(
    r"\b(?:his|her|its|their|my|our|the)\s+(?:age|breed)\b"
    r"|\bhow old (?:is|was) (?:he|she|it|they)\b"
    r"|\bwhat (?:breed|kind|sort|type)\b|\bwhich breed\b", re.I)

BREED_WORD = re.compile(r"\bbreed\b|\bwhat (?:kind|sort|type)\b|\bwhich breed\b", re.I)

def _pet_part_reply(memory, low):
    """An age or a breed asked about an animal they have described, or None."""
    if not PET_PART_ASK.search(low):
        return None
    if re.search(r"\bage\b|\bhow old\b", low):
        said = _pet_age_reply(memory, low)
        if said:
            return said
    return _pet_breed_reply(memory, low)

def _pet_breed_reply(memory, low):
    """The breed the chat was told, for "what breed is he", or None.

    Only when the line is about an animal the chat holds a breed for: one it names ("max"), the
    family it names ("my dog"), or a pronoun, which means the one the chat has just been on.
    "what kind of dog should i get" names no animal of theirs and is a question about the world.
    """
    if not BREED_WORD.search(low):
        return None
    pets = [pet for pet in (user(memory).get("pets") or [])
            if isinstance(pet, dict) and str(pet.get("breed") or "").strip()
            and not pet.get("not_theirs")]
    if not pets:
        return None
    asked = []
    family = ""
    animal = PET_ASK.search(low)
    if animal:
        family = _animal_family(animal.group(1))
    if family:
        asked = [pet for pet in pets if _animal_family(pet.get("animal")) == family]
    if not asked:
        for pet in pets:
            name = str(pet.get("name") or "").strip()
            if len(name) > 2 and re.search(r"\b" + re.escape(name.lower()) + r"\b", low):
                asked.append(pet)
    if not asked and re.search(r"\b(?:she|he|it|they|his|her|its|their)\b", low):
        asked = [pets[-1]]
    if not asked:
        return None
    pet = asked[-1]
    breed = str(pet.get("breed") or "").strip()
    name = str(pet.get("name") or "").strip()
    if not name:
        # "hes a labrador" gave the animal no name, so the breed is the only word the chat has
        # for it: "your labrador is a labrador" is the store saying its own word back.
        return _vary(["A " + breed + " - that is what you said.",
                      "You said a " + breed + ".",
                      "A " + breed + "."], memory)
    name = _tidy_name(name)
    return _vary([name + " is a " + breed + ".",
                  "You told me " + name + " is a " + breed + ".",
                  "A " + breed + ", that one."], memory)

def _a_number(value):
    """A figure the fact reader gave as text, as a number: "12" and 12 are the same age."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return value

def _a_pronoun_age(memory, low):
    """The age of a person the chat only ever pointed at, or None.

    "she is 5 next month" files nothing: the store keeps facts about a named person, and an age
    about nobody is not one. The line still said it, so "how old is she" a turn later is a
    question about what the chat was told, and the answer is the age with the pronoun in it.
    Only the same pronoun is taken ("he" is not read off a line about "she"), and only a line
    inside the last few turns.
    """
    match = re.search(r"\b(she|he|they)(?:'s|s|'re|re)?\b", str(low or ""))
    if not match:
        return None
    pronoun = match.group(1)
    lines = []
    for turn in recent(memory, 5):
        said = turn.get("user") if isinstance(turn, dict) else None
        lines.append(said if isinstance(said, str) else "")
    for i in range(len(lines) - 1, -1, -1):
        said = lines[i]
        if not said.strip():
            continue
        # A kitten, a puppy or a budgie is not a person: an age said about one is said in a unit
        # this path cannot give back in years, and "we got a kitten" then "he is 10 weeks old" is
        # the kitten. A pet in play with a small-unit age is that pet, so the pet reader (or the
        # hedge behind it) keeps the chat. A pet and a birthday still to come ("we have a dog" /
        # "she is 5 next month") is left to this path: a person says a pet's age in weeks and a
        # person's in years, and that difference is the only thing in the words to go on.
        small = A_SMALL_UNIT.search(said.lower())
        if AN_ANIMAL.search(said) or (small and (AN_ANIMAL.search(lines[i - 1] if i else "")
                                                  or memory.get("pets"))):
            continue
        # A baby's age is said in weeks or months and the fact reader keeps it as one, so the
        # unit is said as it was said: "She is 18 months old." rather than a year it is not.
        if small and _a_pronoun_word(said) == pronoun:
            was = "are" if pronoun == "they" else "is"
            return (pronoun + " " + was + " " + small.group(1) + " " + small.group(2)
                    + " old.").capitalize()
        for entry in extract.extract(said).get("others") or []:
            if not isinstance(entry, dict) or entry.get("who"):
                continue
            # The reader keeps the pronoun on most shapes and not on others ("he turns 6 in
            # june"), so a line with no pronoun of its own is read off the words it was said in.
            theirs = str(entry.get("pronoun") or "") or _a_pronoun_word(said)
            if theirs != pronoun:
                continue
            age = entry.get("age")
            if isinstance(age, str) and age.strip().isdigit():
                age = int(age.strip())
            if not isinstance(age, int):
                continue
            # A pronoun is never a name: when the store holds this same age for the one animal
            # the chat has been told about, the age is said with the animal in it ("Your greyhound
            # is 2.") rather than with the pronoun it was pointed at with. The rule and why the
            # name has to be earned are in `relations.the_pronoun_said_with_a_name`.
            named = the_pronoun_said_with_a_name(memory, age)
            if named:
                return named
            return _one_age(pronoun, age, str(entry.get("turns") or ""))
    return None

AN_ANIMAL = re.compile(
    r"\b(?:cat|cats|kitten|kittens|dog|dogs|puppy|puppies|pup|rabbit|bunny|hamster|gerbil|"
    r"guinea pig|parrot|budgie|bird|fish|horse|pony|ferret|tortoise|snake|lizard|pets?)\b", re.I)

A_SMALL_UNIT = re.compile(r"\b(\d{1,2})\s*(weeks?|months?)\b", re.I)

def _a_pronoun_word(text):
    """The first pronoun in the line that points at a person: "she", "he" or "they".

    The pronoun arrives with its verb joined on more often than not - "shes 4 months", "hes 7",
    "theyre twins" - and a word boundary after "she" never matches inside "shes", so the line
    read as naming nobody and the age it gave was lost.
    """
    match = re.search(r"\b(she|he|they)(?:'s|s|'re|re)?\b", str(text or "").lower())
    return match.group(1) if match else ""

def _someone_else_named(low, memory):
    """Who else the line is about, as the store files them; "" when the line names nobody.

    The person is the one the ask names ("my son", "your mum"); a bare "she"/"he" points at the
    person the last fact was about, which is the one the user just gave a fact about. A line with
    no person in it at all ("can i eat satay", after "my wife is allergic to nuts") is about the
    person typing, so it names nobody here.

    The longest name wins: "mother in law" is not her mother, and a line that says the two words
    has to reach the same person the fact was filed against.
    """
    names = [str(known.get("who") or "").strip() for known in others(memory)]
    names = [name for name in names if name] + list(extract.RELATIONS)
    # Longest first, so the two-word relation beats the word it opens with ("mother in law" and
    # not "mother"), and a relation the store already keeps by name is found as it was filed.
    # Ties are broken by where the name is in the line, then by the word itself. `set` order is
    # the hash order, so two names of the same length ("can my dad eat nuts my mum is
    # vegetarian") made the answer a coin flip between the same process runs: one run answered
    # about the mother, the next answered nothing at all.
    found = []
    # People type the apostrophe, leave it out, or use the curly one, and the store files a pair as
    # "partner's mum": a line that says "my partners mum" has to reach the person the same way the
    # reply names her, so the search is made without apostrophes on both sides.
    flat = low.replace("'", "").replace("\u2019", "")
    for name in set(names):
        match = re.search(r"\b" + re.escape(name.replace("'", "").replace("\u2019", ""))
                          + r"s?\b", flat)
        if match:
            found.append((-len(name), -match.start(), name))
    if found:
        return min(found)[2]
    if THEM.search(low):
        return _person_from_pronoun(low, memory)
    return ""

_SAME_FACT_PERSON = _RELATION + "|kids|children|child|boys|girls"

SAME_FACT_ABOUT = re.compile(
    r"^(?:and |so |oh |but |ok |okay )*"
    r"(?:same for )?"
    r"(?:(?:my|our) (?P<who>" + _SAME_FACT_PERSON + r")"
    r"|(?:the )?(?P<more>" + _SAME_FACT_PERSON + r")s?)"
    r"(?: (?:is|are|does|do|has|have))?"
    r"(?: (?P<same>too|as well|also|the same|same|neither))?$", re.I)

NEGATIVE_TAIL = frozenset("""either at all as well really actually""".split())

SAME_FACT_AGAINST_PRONOUN = re.compile(
    r"^(?:and |so |oh |but |ok |okay |no,? |actually )*(?P<pron>she|he|they)"
    r"(?: is| are|'s|s)(?P<neg>nt|n't| not)\b(?P<rest>.*)$", re.I)

SAME_FACT_AGAINST = re.compile(
    r"^(?:and |so |oh |but |ok |okay )*(?:(?:my|our) (?P<who>" + _SAME_FACT_PERSON + r")"
    r"|(?P<more>" + _SAME_FACT_PERSON + r")s?) (?:is|are)"
    r"(?P<neg>nt|n't| not)\b(?P<rest>.*)$", re.I)

def _the_same_fact_about_someone(text, memory):
    """The fact standing about the person typing, given to someone they name: (reply, note).

    "and my wife is too", "my son as well", "same for my partner": the "too" is the allergy, the
    diet or the condition already on record, so it is said with the fact in it and kept on the
    person named - which is what makes "is she allergic to anything" answerable afterwards.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    low = " ".join(text.lower().split()).strip(" ?!.")
    if not low or len(low.split()) > 7:
        return None
    match = SAME_FACT_AGAINST.match(low)
    against = bool(match)
    by_pronoun = False
    if not match:
        match = SAME_FACT_AGAINST_PRONOUN.match(low)
        against = by_pronoun = bool(match)
    if not match:
        match = SAME_FACT_ABOUT.match(low)
    if not match:
        return None
    if by_pronoun:
        # "she isnt" is about the person the last note was written on, which is the only person the
        # chat has named since.
        last = _the_person_last_given_a_fact(memory)
        if not last:
            return None
        who, kind, value = last
        if not _the_fact_said_against(kind, value, match.groupdict().get("rest") or ""):
            return None
        _take_the_fact_back(memory, who, kind)
        return (_ive_taken_it_back(who, kind, value), None)
    who = (match.group("who") or match.group("more") or "").strip()
    if who not in PLURAL_PEOPLE and who.endswith("s") and who[:-1] in extract.RELATIONS:
        who = who[:-1]
    if not who:
        return None
    same = (match.groupdict().get("same") or "").strip().lower()
    if not against and not same and not low.startswith("same for"):
        # "my wife" on its own is not the allergy said again: only a "too", an "as well" or a
        # "same for" says the fact carries over. "what about my wife" is not one of them - it is
        # a question about her, and reading it as the fact invents one they never gave.
        return None
    held = _the_fact_on_record(memory)
    if not held:
        return None
    given = extract.extract(text)
    if any(given.get(key) for key in SAME_FACT_THEIR_OWN):
        return None  # the line states a fact of its own, which is a reader's job above
    for known in others(memory):
        if known.get("who") == who and any(known.get(key) for key in SAME_FACT_THEIR_OWN):
            return None  # the store already has this person's own facts; it says those instead
    kind, value = held
    if against:
        if match.groupdict().get("same", "").lower() == "neither":
            return None
        if not _the_fact_said_against(kind, value, match.groupdict().get("rest") or ""):
            return None
        return (_isnt_this_too(who, kind, value), None)
    return (_this_too(who, kind, value), {kind: list(value) if isinstance(value, list) else value,
                                          "who": who})

def _the_fact_said_against(kind, value, rest):
    """True when what follows "my wife isnt" is the fact itself, or nothing at all.

    "my wife isnt allergic", "my wife isnt coeliac", "my wife isnt either" are the fact said
    against. "my wife is not responding" and "my son isnt well today" are not: those are about the
    person, and a denial read on them would put a memory note where help is wanted.
    """
    words = str(rest or "").strip(" ?!.").split()
    if not words:
        return True
    if words[0].lower() in NEGATIVE_TAIL:
        return all(word.lower() in NEGATIVE_TAIL for word in words)
    first = words[0].lower()
    if kind == "allergies":
        return first == "allergic"
    head = str(value[0] if isinstance(value, list) else value).lower()
    return bool(head) and (first == head or head.startswith(first))

def _the_person_last_given_a_fact(memory):
    """The person a "too" last gave a fact to, with that fact: (who, key, value) or None."""
    for known in reversed(others(memory)):
        if not isinstance(known, dict) or not known.get("who"):
            continue
        for key in ("allergies", "diet", "condition"):
            if known.get(key):
                return str(known["who"]), key, known[key]
    return None

def _take_the_fact_back(memory, who, kind):
    """Take the fact off the person it was given to: "she isnt" after "and my wife is too"."""
    for known in reversed(others(memory)):
        if not isinstance(known, dict) or known.get("who") != who:
            continue
        known.pop(kind, None)
        left = {key for key in known if key not in {"who", "name", "turns"}}
        if not left:
            # Nothing is left on the person, so the entry goes: "what do you know about my wife"
            # cannot answer with a fact that was taken back.
            others(memory).remove(known)
        return

def _ive_taken_it_back(who, kind, value):
    if kind == "allergies":
        said = "allergic to " + _and_list(value)
    elif isinstance(value, list):
        said = str(value[0])
    else:
        said = str(value)
    negative = " aren't " if _plural_person(who) else " isn't "
    return ("Your " + who + negative + said + ", then - I've taken that back off "
            + ("them" if _plural_person(who) else "her" if who in _SHE else
               "him" if who in _HE else "them") + ".")

_SHE = frozenset("""mum mom mother mum-in-law wife girlfriend sister daughter aunt grandma
    grandmother granny nan nana niece fiancee""".split())

_HE = frozenset("""dad father husband boyfriend brother son uncle grandad grandfather grandpa
    nephew fiance""".split())

def _the_fact_on_record(memory):
    """The one fact about the person typing that a "too" can carry: (key, value) or None.

    An allergy comes first because it is the one that changes what they can be given, then a diet,
    then a condition. Nothing else is inherited: a "too" after "my budget is 300" is about money
    the other person may not share.
    """
    them = user(memory) or {}
    for key in ("allergies", "diet", "condition"):
        value = them.get(key)
        if value:
            return key, value
    return None

def _both_of_you(who):
    """The pair the fact is now kept for: two people, or a family said as one word."""
    return "all of you" if _plural_person(who) else "both of you"

def _this_too(who, kind, value):
    if kind == "allergies":
        return ("Your " + who + _is_are(who) + "allergic to "
                + _and_list(value) + " too, then - I'll keep it out for "
                + _both_of_you(who) + ".")
    if kind == "condition":
        return ("Your " + who + _is_are(who) + str(value[0] if isinstance(value, list) else value)
                + " too, then - I'll keep it in mind for " + _both_of_you(who) + ".")
    return ("Your " + who + _is_are(who) + str(value) + " too, then - I'll plan around "
            + _both_of_you(who) + ".")

def _isnt_this_too(who, kind, value):
    if kind == "allergies":
        said = "allergic to " + _and_list(value)
    elif isinstance(value, list):
        said = str(value[0])
    else:
        said = str(value)
    negative = " aren't " if _plural_person(who) else " isn't "
    return ("Your " + who + negative + said + ", then - good to know. It's just you I'll plan for.")

WHAT_ABOUT_A_FOOD = re.compile(
    r"^\W*(?:and\s+|what\s+about\s+|how\s+about\s+|ok\s+with\s+)?([a-z][a-z' -]{2,30})\s*\??$",
    re.I)

def _the_person_still_in_hand(low, memory):
    """The person with a limit the chat was last told about, on a food ask that names nobody."""
    if not WHAT_ABOUT_A_FOOD.match(low):
        return ""
    person = memory.get("person") if isinstance(memory, dict) else None
    who = str((person or {}).get("who") or "").strip() if isinstance(person, dict) else ""
    if not who:
        return ""
    for known in others(memory):
        if known.get("who") == who and _a_food_word(low, known):
            return who
    return ""

def _a_food_word(low, entry):
    """True when the line names a food the limit kept for that person rules out.

    The food does not have to be one the bot has a list of on its own: what makes it a food here is
    that it is a thing this person cannot have, which is the only thing the store would be saying.
    """
    ruled = []
    condition = str(entry.get("condition") or "").lower()
    if condition in CONDITION_RULES_OUT:
        ruled.append(CONDITION_RULES_OUT[condition])
    diet = str(entry.get("diet") or "").lower()
    if diet in DIET_RULES_OUT:
        ruled.append(DIET_RULES_OUT[diet][0])
    return any(_what_the_food_has(low, thing)[0] for thing in ruled)

def _other_person_reply(memory, low):
    """What the user told us about someone else, said back: "Your mum doesn't eat meat."

    The person is the one the ask names ("my son", "your mum"); a bare "she"/"he" is the person
    the retired entry is about, which is the one the user just gave a fact about.
    """
    undeclared = _the_person_still_in_hand(low, memory)
    bare_limit_ask = _a_bare_limit_ask(low, memory)
    if not (undeclared or OTHER_FACT.search(low) or EAT_ASK.search(low)
            or CANT_HAVE.search(low) or CAN_HAVE.search(low) or CAN_THEY_HAVE.search(low)
            or bare_limit_ask):
        return None
    if CAN_THEY_HAVE_A_FOOD.search(low) and not _a_limit_kept_for_them(low, memory) \
            and not bare_limit_ask:
        # Which foods have nuts in them is the cooking entries' reading, not the store's: an
        # allergy alone answers "what are they allergic to", not "can he eat cake".
        return None
    who = _someone_else_named(low, memory) or undeclared
    entry = None
    for known in others(memory):
        if known.get("who") == who:
            entry = known
            break
    if entry is None:
        offered = _did_you_mean_the_person(memory, low)
        if offered:
            return offered
        # "what is my mum allergic to" when the mum was only mentioned in passing gets an honest
        # answer about the mum, not "you haven't mentioned an allergy to me". A line that asks
        # for advice ("what should my mum eat after the op") is a real question and is left to
        # the modules that answer those.
        if _a_bare_limit_ask(low, memory):
            # Before HELP_ASK, because "what can she not eat" has "can" in it and would be read
            # as a request for help. It is the same ask as "is she vegan" from the other side.
            return _nothing_kept_about_them(low)
        if HELP_ASK.search(low):
            return None
        if not who:
            # A bare "she"/"he"/"they" with nobody in the chat behind it: the line asks about a
            # person the store was never told about, and what it has kept is nothing. That is
            # still an answer, and the only true one. Left unsaid, these lines fell to the
            # composer's search hedge - "I don't know enough to answer that honestly. A search
            # should sort you out" - which points at the open web for a fact that can only come
            # from the person themselves, and it was the reply to "what was she allergic to
            # again", "is she vegan" and "what meat did i say he doesnt eat". The offer is the
            # part that helps: the fact is one line away, and the next line is where it is kept.
            # The first person is not this case ("do i have any allergies" is the store's own
            # already, and it says "you haven't mentioned an allergy to me"), so the line has to
            # be about somebody else before the store speaks for them.
            if _nobody_else_kept(memory) and _the_pronoun_in(low) \
                    and _asks_for_a_limit_not_advice(low):
                return _nothing_kept_about_them(low)
            return None
        if OTHER_FACT.search(low):
            return "You haven't told me about an allergy of your " + who + "."
        return _no_diet(who)
    if OTHER_FACT.search(low):
        allergies = entry.get("allergies") or []
        owner = ("Your " + who) if who else "They"
        if not allergies:
            return ("You haven't told me about an allergy of " + (("your " + who) if who else "theirs")
                    + ".")
        return owner + _is_are(who) + "allergic to " + ", ".join(allergies) + "."
    diet = entry.get("diet")
    allergies = entry.get("allergies") or []
    condition = entry.get("condition")
    if condition and (undeclared or CANT_HAVE.search(low) or CAN_HAVE.search(low)
                      or EAT_ASK.search(low) or CAN_THEY_HAVE.search(low)):
        # "my son is coeliac" then "what can he eat" / "can he have bread": the condition kept for
        # him is a food fact too, and it names the food it rules out for the two conditions that
        # rule one out. Said before the diet, because a condition is the sharper of the two.
        said = _condition_is_their_food(who, condition, low)
        if said:
            if diet and not allergies:
                return said + " " + _diet_sentence(who, diet)
            return said
    if diet and (undeclared or CANT_HAVE.search(low) or CAN_HAVE.search(low)
                 or CAN_THEY_HAVE.search(low) or EAT_ASK.search(low)):
        # "what cant she have" wants the food the diet rules out, not the diet's name again - and
        # the name again is the same sentence the store said last turn, so it would be passed over
        # and the turn handed to whatever else proposed. A plain "what does she eat" is the diet
        # as it was said ("Your mum doesn't eat meat."), so only a diet that names one food is
        # turned round into that food.
        ruled = _diet_is_their_food(who, diet, low, plain=bool(EAT_ASK.search(low)))
        if ruled and not allergies:
            return ruled
    if diet and allergies:
        # An allergy kept beside a diet belongs in the answer too: the diet on its own answered
        # the ask and left the allergy behind, and the allergy is the one that could hurt them.
        return _both_food_facts(who, allergies, diet)
    if not diet:
        allergies = entry.get("allergies") or []
        if allergies:
            # The allergy is a food fact, so "what can she eat" is answered from it rather than
            # with "you haven't told me what your mum eats" straight after she said she cannot
            # eat shellfish.
            return _allergy_is_their_food(who, allergies, low=low)
        condition = entry.get("condition") or []
        if condition and _a_condition_rules_out(condition):
            # A condition that rules a food out is a food fact the knowledge base can cook with:
            # "my sister is lactose intolerant" then "what can she have for breakfast" is a
            # breakfast question, and the honest answer says nothing a meal answer would not, so
            # it is left to the modules that answer meals. Before, the store claimed she had told
            # it nothing about her eating, one line after she had. A condition that names its food
            # is answered above, so this is only the condition the store cannot turn into a food.
            return None
        return _no_diet(who)
    return _diet_sentence(who, diet)

# A person named only by a pronoun, when the chat holds nobody for it to be. The pronoun is said
# back rather than replaced with "they", because the person used it and the store has heard it.
THE_PRONOUN = re.compile(r"\b(she|her|hers|he|him|his|they|them|their)\b", re.I)


# A limit asked for rather than advised about. The store was never told about the person, so the
# only true answer is that nothing is kept - but a question about the world is not that question:
# "how do i introduce allergens to my baby" and "how much notice does he have to give" are jobs for
# the knowledge base, and "what does he eat" is answered better by "you would have to ask him".
# What is left is the ask for the fact itself: an allergy or a diet named outright, or a line that
# says it is asking again ("what was she allergic to again", "what did i say she doesnt eat").
A_LIMIT_NAMED = re.compile(r"\b(?:allerg\w*|allergies|vegan|vegetarian|pescatarian|coeliac|celiac|"
                           r"intolerant|intolerance|di(?:ae)?t|avoid\w*)\b", re.I)
ASKING_AGAIN = re.compile(r"\b(?:again|remind me|did i (?:say|tell|mention)|what did i (?:say|tell|"
                          r"mention)|what i (?:said|told|mentioned))\b", re.I)
ADVICE_NOT_A_FACT = re.compile(r"\bhow\b|\bwhat should\b|\bwhat can we\b|\bwhere\b|\bwhen\b"
                               r"|\bwhy\b|\bhow much\b", re.I)


# The line that says the limit and asks about it in one breath - "my son is 7 and has a nut
# allergy, what is he allergic to" - states a fact, so it is not a line with nothing behind it:
# the fact is kept from the same line, and the store answers from what it has just been told.
# "does she have any allergies" says the same words as a statement of one and asks a question
# instead: the "have" is the question's auxiliary, not the person's. Read as a statement, the line
# kept its hedge even though it names the limit and asks nothing else.
A_HAVE_QUESTION = re.compile(r"\b(?:does|do|did)\s+\w+\s+(?:have|has|had|got)\b"
                             r"|\b(?:has|have)\s+(?:she|he|they|anyone|anybody|your)\b")
STATES_A_LIMIT = re.compile(r"\b(?:has|have|had|got)\b[^.!?]{0,24}?\ballerg\w*"
                            r"|\bis\s+allergic\b|\bare\s+allergic\b"
                            r"|\b(?:is|are|am)\s+(?:a\s+)?(?:vegan|vegetarian|coeliac|celiac)\b",
                            re.I)


# The same words inside a question: "remind me what hes allergic to" is folded to "what he is
# allergic to", which has "is allergic" in it and states nothing. Only a line without an
# interrogative in front of the verb is telling the store something.
A_ASK_FRAME = re.compile(r"\b(?:what|which|who|tell me|remind me|if|whether|wonder|know)\b"
                         r"[^.!?]{0,24}?\b(?:is|are|was|were|has|have|does|do|can)\b", re.I)


def _asks_for_a_limit_not_advice(low):
    """True for a line that asks for a kept fact about somebody's allergies or diet."""
    text = str(low or "")
    if ADVICE_NOT_A_FACT.search(text):
        return False
    if STATES_A_LIMIT.search(text) and not A_HAVE_QUESTION.search(text) \
            and not A_ASK_FRAME.search(text):
        return False
    if re.search(r"\bnot\s+eat\b", text):
        # "what can she not eat" asks for the limit from the other side, and it is the same ask as
        # "is she vegan". The positive "what does he eat" is not this line: it is answered by
        # saying they would have to be asked, and it keeps its own answer.
        return True
    if CANT_HAVE.search(text):
        # "what can she not eat" asks for the same limit as "is she vegan", from the other side.
        # A positive "what does he eat" is not this line: that one is answered by saying they
        # would have to be asked, and it keeps its own answer.
        return True
    return bool(A_LIMIT_NAMED.search(text) or ASKING_AGAIN.search(text))


def _the_pronoun_in(low):
    """The pronoun the line named its person with: "she", "he", "they", or "" for none."""
    found = [m.group(1).lower() for m in THE_PRONOUN.finditer(str(low or ""))]
    for word in found:
        if word in ("she", "her", "hers"):
            return "she"
        if word in ("he", "him", "his"):
            return "he"
    for word in found:
        if word in ("they", "them", "their"):
            return "they"
    return ""


def _nobody_else_kept(memory):
    """True when the store holds no fact about anybody else.

    Read, not called through `others()`: that one files an empty list into the memory it is asked
    about, and a store that was never asked about another person then carries an "others" key for
    the rest of the chat. It is a side effect no reader should be able to cause by looking, and
    measured on the deck it moved 12 turns of conversations that had nothing to do with it.
    """
    if not isinstance(memory, dict):
        return True
    kept = memory.get("others")
    return not (isinstance(kept, list) and kept)


A_MEAL_WORD = re.compile(r"\b(?:cook|cooking|cooked|recipe|recipes|meal|meals|dinner|tea|lunch|"
                         r"breakfast|snack|menu|shop|shopping|bake|baking)\b", re.I)


def _a_bare_limit_ask(low, memory):
    """A limit asked for about somebody named only by a pronoun, with nobody in the chat behind it.

    "is she vegan", "does she have any allergies" and "what can she not eat" name a person the
    store could look up only if the chat had ever said who "she" is. It has not, so the asks that
    need a relation never took the line, and the composer's search hedge answered a question about
    the person in front of the bot: "That's beyond what I know well, sorry. Searching for it will
    turn up better sources". Nothing kept is itself the answer, and `_nothing_kept_about_them`
    says it; this is the gate that lets the line reach it.
    """
    text = str(low or "")
    # A line that also says what it is for - "is she vegan, shes coming for dinner" - is asking
    # for a meal, and the answer modules have a real one; the store's "you haven't told me" is
    # only the right answer to the bare ask.
    if A_MEAL_WORD.search(text):
        return False
    return bool(_nobody_else_kept(memory) and _the_pronoun_in(text)
                and _asks_for_a_limit_not_advice(text))


def _nothing_kept_about_them(low):
    """What the store says when a limit is asked about a person it was never told about.

    Nothing kept is an answer, and it is the only one that is true. The offer matters as much as
    the admission: the next line is where the fact comes in, and the bot says so.
    """
    pronoun = _the_pronoun_in(low)
    if OTHER_FACT.search(str(low or "")):
        theirs = {"she": "hers", "he": "his"}.get(pronoun, "theirs")
        return ("You haven't told me about an allergy of " + theirs
                + " yet \u2014 what is it? I'll keep it out of anything I suggest.")
    if pronoun in ("she", "he"):
        return ("You haven't told me how " + pronoun + " eats yet \u2014 what does " + pronoun
                + " avoid? I'll plan the meals round it.")
    return ("You haven't told me how they eat yet \u2014 what do they avoid? I'll plan the meals "
            "round it.")


def _did_you_mean_the_person(memory, low):
    """The one person the store holds, offered back when a pronoun fits nobody.

    "my mum is allergic to shellfish" then "what is he allergic to" is a slip of the keys nine
    times out of ten, and the definition of an allergy is no answer to it. The store asks rather
    than guesses which person was meant: "Did you mean your mum? She is allergic to shellfish."
    A second person in the store means the pronoun has a real choice to make, so this stays free.
    """
    held = [e for e in others(memory) if isinstance(e, dict) and e.get("who")]
    if len(held) != 1:
        return None
    # The offer answers a pronoun that fits nobody, so the line has to have one. "what is an
    # allergy" names no person and points at none: the one person in the store is not a typo
    # there, and "Did you mean your mum?" is no answer to a question about allergies.
    if not THEM.search(low):
        return None
    who = str(held[0].get("who"))
    said = ""
    if OTHER_FACT.search(low) and held[0].get("allergies"):
        said = "Your " + who + _is_are(who) + "allergic to " + ", ".join(held[0]["allergies"]) + "."
    elif EAT_ASK.search(low) and held[0].get("diet"):
        said = _diet_sentence(who, held[0]["diet"])
    elif EAT_ASK.search(low) and held[0].get("allergies"):
        said = _allergy_is_their_food(who, held[0]["allergies"])
    if not said:
        return None
    gender = _gender_of(who)
    pronoun = "She" if gender == "she" else "He" if gender == "he" else "They"
    tail = said[len("Your " + who):]
    if pronoun == "They":
        # "Your partner is allergic to shellfish" said again with a pronoun takes "are".
        tail = re.sub(r"^(\s+)is\b", r"\1are", tail)
        tail = re.sub(r"^(\s+)does not\b", r"\1do not", tail)
    ask_gender = _ask_gender(low)
    if ask_gender and gender and gender != ask_gender:
        # The ask says "he" about a person the store knows as a she, so the mismatch is said out
        # loud instead of answering a question they did not ask.
        him = "her" if gender == "she" else "him"
        return ("I've only got your " + who + " down, and " + pronoun.lower() + tail
                + " Did you mean " + him + "?")
    return "Did you mean your " + who + "? " + pronoun + tail

def _condition_is_their_food(who, condition, low=""):
    """What the condition kept for a person means for their plate, or None when it means nothing.

    "my son is coeliac" then "what can he eat" was a search hedge, because the store had kept
    the condition and had no sentence for it: the food it rules out is the answer, and it is the
    same answer the diet reader gives for "gluten-free". The tail is the same honest limit the
    allergy answer carries, so nothing is claimed beyond the one fact the person gave.
    """
    said = " ".join(str(low or "").lower().split())
    low = " ".join(str(condition or "").lower().split())
    owner = ("Your " + who) if who else "They"
    tail = " \u2014 that's all I have on food for " + _their_pronoun(who) + "."
    ruled = CONDITION_RULES_OUT.get(low)
    named, thing = _what_the_food_has(said, ruled) if (ruled and said) else ("", "")
    if named:
        # "can he have cheese" is answered about the cheese: a person asking about one food has
        # that food in their hand, and "nothing with dairy in it" leaves them to work it out.
        return (named[:1].upper() + named[1:] + " has " + thing + " in it, and " + owner.lower()
                + _is_are(who) + low + ".")
    if ruled:
        return (owner + _is_are(who) + low + ", so nothing with " + ruled + " in it" + tail)
    watched = CONDITION_KEEPS_DOWN.get(low)
    if watched:
        return (owner + _is_are(who) + low + ", so keep the " + watched + " down" + tail)
    if low:
        # A condition with no food of its own is still said back, so the ask is answered with
        # what the store knows instead of a hedge about a fact it was told a turn ago.
        return owner + _is_are(who) + low + tail
    return None

def _diet_sentence(who, diet):
    """A diet said as a sentence: "Your mum doesn't eat meat.", "They're vegetarian."."""
    if str(diet).startswith("eats ") or str(diet).startswith("no "):
        # "eats fish" is what a restriction becomes when the person puts it back, and it is a
        # sentence of its own: "Your son is eats fish." is not one.
        if who:
            return "Your " + who + " " + _a_diet_predicate(who, diet) + "."
        return "They eat " + str(diet)[5:] + "." if str(diet).startswith("eats ") \
            else "They don't " + _diet_how(diet) + " " + str(diet)[3:] + "."
    if who:
        return "Your " + who + _is_are(who) + str(diet) + "."
    return "They're " + str(diet) + "."

A_BIRTHDAY_PLAN = re.compile(r"\b(?:birthday|bday|dob|date of birth)\s+(?:is\s+|was\s+|on\s+|in\s+)?"
                             r"([^,.;!?]{2,28})", re.I)

_A_RELATION = ("(?:" + "|".join(sorted(extract.RELATIONS, key=len, reverse=True)) + r")"
               + extract.IN_LAW)

A_RELATIONS_BIRTHDAY = re.compile(
    r"\b" + _A_RELATION + r"(?:'s|s)?\s+"
    r"(?:birthday|bday|dob|date of birth)\b", re.I)

NO_CAP = frozenset(("diesel", "petrol", "hybrid", "electric", "estate", "hatchback", "saloon",
                    "coupe", "convertible", "automatic", "manual", "classic"))

CAR_DESCRIBED = frozenset("""old new used secondhand second-hand little small big cheap tidy rusty
yellow red blue white black silver grey gray green other spare reliable""".split())

def car_line(car):
    """The car said back, in one shape wherever it is asked for.

    The same fact was said two ways: the fact reader capitalised a model ("You drive a Corsa")
    and said a description as it came, while the thing-they-own reader said everything as it
    came - so "i drive a ford focus" came back lowercase from one reader and "a Corsa" from the
    other. The rule is the one a person uses reading it out: a model is a name and takes its
    capital, two words are both names ("a Ford Focus"), a describing word is not a name ("an old
    fiesta"), and a fuel or a body is not one either ("a diesel").
    """
    said = " ".join(str(car or "").split())
    if not said:
        return ""
    words = said.split()
    if any(word.lower() in CAR_DESCRIBED for word in words):
        return "You drive " + _a(said) + "."
    if len(words) == 1 and said.lower() in NO_CAP:
        return "You drive " + _a(said) + "."
    shown = " ".join(CAR_CAPS.get(word.lower(),
                                  word[:1].upper() + word[1:] if word.islower() else word)
                     for word in words)
    return "You drive " + _a(shown) + "."

def _birthday_in_words(memory):
    """A birthday they gave in words rather than as a date: "my birthday is tomorrow".

    A relative day is not a date the store can keep - next week "tomorrow" is wrong - so the line
    stays the plan it was read as. The summary already says "your birthday is tomorrow", so the
    ask has to say the same thing back: "you haven't told me" in the same conversation is the bot
    contradicting itself. Only their own birthday is read here, never one said of someone else.
    """
    for plan in reversed(user(memory).get("plans") or []):
        said = str(plan)
        match = extract.BIRTHDAY.search(said) or A_BIRTHDAY_PLAN.search(said)
        if not match or extract.subject(said, match.start())[0] == "other":
            continue
        if A_RELATIONS_BIRTHDAY.search(said):
            # "my sons birthday is tomorrow" is held as the plan "sons birthday tomorrow", and the
            # relation in front of it is what says whose date it is.
            continue
        words = " ".join(match.group(1).lower().split()).rstrip(" .,;:")
        words = re.sub(r"^(?:in|on)\s+", "", words)
        if words:
            return words
    return ""

def _birthday_reply(memory):
    """The birthday they gave, in the words they would use for it."""
    known = user(memory)
    date = known.get("birthday")
    words = _birthday_words(date) if date else _birthday_in_words(memory)
    if not words:
        return "You haven't told me your birthday yet."
    # A birthday is a date, and a date is answered the way every other date in the store is
    # ("On 3 May.", "In August." - see `when_answer`): the joining word is not part of the date,
    # so "my birthday is on 3 may" is not answered "Your birthday is 3 May." A birthday given in
    # words rather than as a date ("tomorrow") is not a date, and keeps the sentence form.
    if words.startswith("in "):
        plain = words[:1].upper() + words[1:] + "."
    elif re.match(r"(?:the\s+)?\d", words):
        plain = "On " + words + "."
    else:
        plain = "Your birthday is " + words + "."
    if plain in {turn.get("bot") for turn in memory.get("turns") or []}:
        return _vary(["It's " + words + " — that's what you told me.",
                      "You said " + words + ".",
                      "Still " + words + "."], memory)
    return plain

WHOSE_BIRTHDAY = re.compile(
    r"\b(?:when|what\s+date)(?:'s|s)?\s+(?:is|was|are)?\s*(?:it\s+)?"
    r"(?:(?:my|our)\s+(?P<who>" + _A_RELATION + r")s?"
    r"|(?P<pronoun>his|her)"
    r"|(?P<name>[a-z][a-z'\u2019-]+)(?:'s|s))\s*"
    r"(?:birthday|bday|dob|date\s+of\s+birth)\b", re.I)

def _the_same_relative(one, other):
    """Whether two words are the same person's relation: "mum" and "mums" are one mum."""
    one = str(one or "").lower()
    other = str(other or "").lower()
    if not one or not other:
        return False
    if one == other:
        return True
    return (other.endswith("s") and one == other[:-1]) or (one.endswith("s") and one[:-1] == other)

def _a_persons_birthday_reply(memory, low):
    """The date the store holds for the person the ask names, said back, or None.

    Only a date it holds is answered: a person with no birthday kept leaves the turn to whoever
    can answer it, the same rule as their name and their age. The person is the relation the ask
    names ("my mums birthday"), the name it gives ("toms birthday") or the pronoun ("his
    birthday"), and a pronoun only points at a person it fits.
    """
    asked = WHOSE_BIRTHDAY.search(low)
    if not asked:
        return None
    who = extract.a_person_word(asked.groupdict().get("who") or "")
    pronoun = (asked.groupdict().get("pronoun") or "").lower()
    named = (asked.groupdict().get("name") or "").lower()
    if who in ("birthday", "bday", "dob", "date"):
        return None
    known = None
    if who:
        known = next((entry for entry in others(memory)
                      if _the_same_relative(entry.get("who"), who)), None)
        if known is not None:
            who = str(known.get("who") or who)
    elif named:
        known = next((entry for entry in others(memory)
                      if _same_name(entry.get("name") or "", named)), None)
    elif pronoun:
        # "when is he/she ...": the last person the chat was about whose pronoun fits, which is
        # how the same ask about an age is read. A date kept against the pronoun itself ("his
        # birthday is in may" with nobody named in the chat) is that pronoun's, since it is the
        # only person the store was given.
        fits = extract.SHE if pronoun == "her" else extract.HE
        known = next((entry for entry in reversed(others(memory))
                      if (entry.get("who") or "").lower() in fits), None)
        if known is not None:
            who = str(known.get("who") or "")
            named = str(known.get("name") or "")
        else:
            word = "she" if pronoun == "her" else "he"
            known = next((entry for entry in others(memory)
                          if str(entry.get("pronoun") or "") == word and entry.get("birthday")),
                         None)
    if known is None or not known.get("birthday"):
        return None
    words = _birthday_words(known["birthday"])
    said_name = str(known.get("name") or named or "")
    if said_name and not who:
        # The store keeps a name as it was typed ("my son is called tom"), so the date is said
        # with it as a name reads.
        said_name = said_name[:1].upper() + said_name[1:]
        return _vary([said_name + "'s birthday is " + words + ".",
                      "That's " + words + " for " + said_name + "."], memory)
    if not who:
        return None
    # A relation is the person the store knows them by, so the date is said with them: "Your
    # mum's birthday is the 3rd of May." A word for more than one person takes the apostrophe
    # after it ("your kids' birthday"), the same way the rest of the store pluralises.
    theirs = ("Your " + who + ("'" if _plural_person(who) else "'s") + " birthday is "
              + words + ".")
    return _vary([theirs,
                  "That's " + words + " for your " + who + ".",
                  "Your " + who + ("'" if _plural_person(who) else "'s") + " birthday: "
                  + words + "."], memory)

def _weight_reply(memory):
    """What they weigh, in the unit they gave it in."""
    known = user(memory)
    weight = known.get("weight")
    if not weight:
        return "You haven't told me what you weigh."
    plain = "You weigh " + weight + "."
    if plain in {turn.get("bot") for turn in memory.get("turns") or []}:
        return _vary(["Still " + weight + ".", "You said " + weight + ".",
                      "It's " + weight + " — that's what you told me."], memory)
    return plain

ALLERGY_IN_THE_WORLD = re.compile(r"\bwhy\s+(?:do|does|did|would|are|is|can)\b|"
                                  r"\bwhat\s+causes?\b|\bhow\s+common\b|"
                                  r"\bwhat\s+are\s+allergies\b", re.I)

# A how-to at the front of a line is a request for advice, not a recall of a fact: "how do i
# budget" was read as the budget fact and answered "You haven't told me a budget." to a person
# asking how to make one, when the knowledge answer for budgeting was there to give. The diet
# branch has kept this guard (`DIET_HOW_TO`) since the same bug in front of "my diet"; the other
# facts needed it too. The frame has to be at the front, because a fact question can carry the
# same words later on ("whats my budget", "how much can i spend").
#
# The frame is a how-to of *doing* the thing. A question of how much, how many or how long is a
# quantity ask that happens to start with "how", not a how-to: "how much do i spend" after "my
# budget is 200 a month" wants the 200 back, so the quantity words are not a frame at all.
A_HOW_TO_ASK = re.compile(r"^\s*(?:so|and|ok|okay|hi|hello)?[, ]*\s*"
                          r"(?:how (?:do|can|could|should|would|might|to)\b|"
                          r"ways? to\b|any (?:tips|advice|ideas|suggestions|ways)\b|"
                          r"tips for\b|help me\b|what can i do\b|what should i do\b)", re.I)
# ...unless they are asking to be reminded of the figure they gave: "how do i know my budget
# again" is a recall with a how-to shape, and the how-to answer ("write down what comes in each
# month") is advice about budgeting, not their number. The recall word decides - and "know" is
# one of them, because "how do i know my weight" is a how-to of knowing, which is a recall, while
# "how do i lose weight" is a how-to of doing and stays advice.
A_RECALL_WORD = re.compile(r"\bagain\b|\bremind me\b|\bdid i (?:say|tell|mention)\b|"
                           r"\bwhat did i say\b|\bdo you remember\b|\byou know my\b|"
                           r"\bwhat was my\b|\bwhats my\b|\bwhat's my\b|\bknow\b", re.I)

def _height_reply(memory):
    """How tall they are, in the unit they gave it in.

    A height is said the way a person says it - "You're 5 foot 10", "You're 175cm" - and never
    "You weigh ...", which is the sentence the weight answer uses.
    """
    known = user(memory)
    height = str(known.get("height") or "").strip()
    if not height:
        return "You haven't told me how tall you are."
    plain = "You're " + height + "."
    if plain in {turn.get("bot") for turn in memory.get("turns") or []}:
        return _vary(["Still " + height + ".", "You said " + height + ".",
                      "It's " + height + " \u2014 that's what you told me."], memory)
    return plain

def _fact_reply(memory, low, key=None):
    """The reply for one of their facts. key is the fact already read from the ask, so a wording
    the words do not name ("how much can I spend" is a budget) still gets the right answer."""
    # A how-to in front of the fact word is advice, not a recall of it - unless a recall word is
    # in the line, which is the ask underneath the shape.
    if low and A_HOW_TO_ASK.search(str(low)) and not A_RECALL_WORD.search(str(low)):
        return None
    known = user(memory)
    if key == "allergy" or "allerg" in low:
        if ALLERGY_IN_THE_WORLD.search(str(low or "")):
            return None
        allergies = known.get("allergies") or []
        if allergies:
            said = ", ".join(allergies)
            plain = "You told me you're allergic to " + said + "."
            # Asked twice in a row ("what am i allergic to", then "again"), the same
            # sentence twice reads like a machine, so the phrasing rotates - the way the
            # budget answer already does. The list itself is the answer either way.
            if plain in {turn.get("bot") for turn in memory.get("turns") or []}:
                return _vary(["It's " + said + " — that's what you said.",
                              "Still " + said + ".",
                              "Your allergy is " + said + "."], memory)
            return plain
        if "allergies" in known:
            # The list is still there and empty: they named one and then took it back, so the
            # answer is that nothing is on it, not that they never said anything. The one they
            # took back is still in the correction of that turn, so it can be named.
            fixed = memory.get("correction") if isinstance(memory, dict) else None
            gone = str((fixed or {}).get("value") or "").strip().lower()
            if gone and fixed.get("dropped"):
                return "Nothing on the list now — you took the " + gone + " one back."
            return "Nothing on the list now."
        who, theirs = _other_fact(memory, "allergies")
        if theirs and who:
            return _their_allergy(who, theirs)
        if theirs:
            return ("You haven't mentioned one for yourself \u2014 the allergy to "
                    + ", ".join(theirs) + " you mentioned was someone else's.")
        return _deny(memory, "allergy", "You haven't mentioned an allergy to me.")
    if key == "budget" or "budget" in low:
        budget = known.get("budget")
        if not budget:
            return _deny(memory, "budget", "You haven't told me a budget.")
        # The first answer is the plain sentence; asked again, a different phrasing, because
        # the same sentence twice in a row reads like a machine.
        plain = "Your budget is " + budget + "."
        if plain in {turn.get("bot") for turn in memory.get("turns") or []}:
            return _vary(["It's " + budget + " — that's what you told me.",
                          "You said " + budget + ".", "Still " + budget + "."], memory)
        return plain
    if key == "birthday":
        return _birthday_reply(memory)
    if key == "weight":
        return _weight_reply(memory)
    if key == "height":
        return _height_reply(memory)
    if key == "diet" or (DIET_ASK.search(low) and not DIET_HOW_TO.search(low)):
        return _diet_reply(memory, low)
    if key == "car" or recall.DRIVE_ASK.search(low):
        car = known.get("car")
        if car:
            return car_line(car)
        return pick(["You haven't told me what you drive.",
                     "I don't know your car \u2014 you haven't said."], memory)
    pets = known.get("pets") or []
    gone = [p for p in (known.get("pets_gone") or []) if isinstance(p, dict)]
    asked = None
    # "what is my dog called?" is about the dog, not the cat: read the animal they named.
    for animal, words in (("dog", "dog puppy"), ("cat", "cat kitten"),
                          ("rabbit", "rabbit bunny"), ("hamster", "hamster"),
                          ("fish", "fish goldfish"), ("horse", "horse pony"),
                          ("parrot", "parrot bird")):
        # "whats my dogs name" is the same ask as "what is my dog called": people type both.
        if re.search(r"\b(?:" + words.replace(" ", "|") + r")s?\b", low):
            # "what's my dog called?" is about the puppy too: a young animal is the same animal.
            asked = animal
            pets = [p for p in pets if _animal_family(p.get("animal")) == animal]
            gone = [p for p in gone if _animal_family(p.get("animal")) == animal]
            break
    coming_only = [p for p in pets if isinstance(p, dict) and p.get("coming")]
    if coming_only and len(coming_only) == len(pets) and not re.search(r"\b(?:called|name)\b",
                                                                     low):
        # "what pets do i have" about an animal that is on its way: the store holds it because
        # the follow-ups need it, and the sentence says it is coming rather than here.
        pieces = []
        for pet in coming_only:
            count = pet.get("count") if isinstance(pet.get("count"), int) else 1
            pieces.append(_many(count, pet.get("animal") or "pet") if count > 1 else _a_pet(pet))
        due = _put_together(pieces)
        if due:
            return "You're getting " + due + "."
    counted = _a_count_ask(low)
    if pets and counted is not None:
        # "how many cats" asks for the number, not for the list: "You've got two cats" and not
        # "two cats, Milly and Fred", which answers a question they did not ask and reads as
        # more animals than they have.
        kinds = {_animal_family(p.get("animal")) for p in pets}
        total = _count_of_a_kind(pets)
        if len(kinds) == 1 and (counted in ("any", "pet") or kinds == {counted}):
            animal = _animal_family(pets[0].get("animal"))
            if total == 1:
                # One animal, named: the number is what they asked for and the name is theirs,
                # so both survive - "You've got a dog." throws the name away.
                was = _called(pets[0].get("name"))
                if was:
                    return "You've got one " + animal + " \u2014 " + was + "."
                return "You've got " + _a(animal) + "."
            return "You've got " + _a_pet({"animal": animal, "count": total}) + "."
    if pets:
        if re.search(r"\b(?:called|name)\b", low) and not any(p.get("name") for p in pets):
            return "You haven't told me a name for your " + pets[0].get("animal", "pet") + " yet."
        together = _pets_together(pets)
        if together:
            return "You've got " + together + "."
        # "how many dogs do i have" asks for the number, so the number is the answer even when
        # the dog has a name: "two dogs" says how many, "a dog called Rex" does not.
        counted = bool(re.search(r"\bhow many\b", low))
        if counted and len(pets) == 1:
            # One animal, named: "how many dogs do i have" is still asking for the number, and
            # "You've got a dog called Biscuit" does not give it. The name is kept beside it.
            pet = pets[0]
            animal = pet.get("animal") or "pet"
            number = pet.get("count") if isinstance(pet.get("count"), int) else 1
            number = max(int(number), 1)
            many = _many(number, animal) if number > 1 else "one " + animal
            was = _called(pet.get("name"))
            return "You've got " + many + (" — " + was + "." if was else ".")
        if counted and len(pets) > 1 and len({_animal_family(p.get("animal")) for p in pets}) == 1:
            top = max([p["count"] for p in pets if isinstance(p.get("count"), int)] or [0])
            if top >= len(pets):
                # The count is the whole set: "we have two cats, milly and fred" put right with
                # "sorry, 3 cats" is three cats, not three cats and a cat called Fred.
                return "You've got " + _many(top, pets[0].get("animal") or "pet") + "."
        parts = [(_many(p["count"], p.get("animal") or "pet")
                  if counted and isinstance(p.get("count"), int) and p["count"] > 1
                  else _a_pet(p)) for p in pets]
        # An animal on its way is not one in the house: "we are getting a puppy next week" then
        # "what pets do i have" answered "You've got a puppy" about one still with its mother. The
        # animal stays in the store - "what do i need to buy first" and "will they get on" need it
        # - and this sentence is the one that says which of them are here and which are coming.
        here = [part for pet, part in zip(pets, parts) if not pet.get("coming")]
        due = [part for pet, part in zip(pets, parts) if pet.get("coming")]
        said = []
        if here:
            said.append("You've got " + _put_together(here) + ".")
        if due:
            said.append("You're getting " + _put_together(due) + ".")
        if said:
            return " ".join(said)
    if gone:
        # "what was my cat called?" asks after a death, in the past tense on purpose: the name is
        # the thing they want back, so it is the name they get.
        was_called = re.search(r"\b(?:was|were|did)\b", low) and re.search(
            r"\b(?:call|called|name|named)\b", low)
        named = [pet for pet in gone if pet.get("name")]
        if was_called and named:
            return _was_called(named)
        # A pet they told me about and then lost is not a pet they never mentioned: say what they
        # said, warmly, rather than answering "you haven't told me about a pet yet".
        return _a_pet_that_is_gone(gone)
    if asked:
        # They do have pets, just not that one: saying "you haven't told me about a pet yet"
        # about a store that holds a dog is a claim the chat can see is false.
        theirs = [_a(p.get("animal", "pet")) + (" called " + _called(p.get("name"))
                  if p.get("name") else "") for p in (known.get("pets") or [])]
        if theirs:
            return ("I don't have " + _a(asked) + " from you \u2014 " + " and ".join(theirs)
                    + " is what I have.")
    return "You haven't told me about a pet yet."

def _was_called(named):
    """The name of a pet that is gone: "Your cat was called Milly."."""
    if len(named) == 1:
        return ("Your " + str(named[0].get("animal") or "pet") + " was called "
                + _called(named[0].get("name")) + ".")
    parts = [str(pet.get("animal") or "pet") + " " + _called(pet.get("name")) for pet in named]
    return "You called them " + ", ".join(parts[:-1]) + " and " + parts[-1] + "."

def _a_pet_that_is_gone(gone):
    """A pet they no longer have, said back the way they told me: died, or gone elsewhere."""
    def one(pet):
        animal = str(pet.get("animal") or "pet")
        name = _called(pet.get("name"))
        return animal + " " + name if name else animal

    shown = [one(pet) for pet in gone]
    if len(shown) > 2:
        which = "any pets"
    elif len(shown) == 2:
        which = "your " + shown[0] + " or your " + shown[1]
    else:
        which = "your " + shown[0]
    if all(pet.get("gone") == "died" for pet in gone):
        return "I'm sorry \u2014 you told me " + which + " died."
    if not any(pet.get("gone") == "died" for pet in gone):
        return "You told me you don't have " + which + " any more."
    told_died = ["your " + shown[index] for index, pet in enumerate(gone)
                 if pet.get("gone") == "died"]
    return ("I'm sorry \u2014 you told me "
            + (" or ".join(told_died) if len(told_died) > 1 else told_died[0]) + " died.")

def _put_together(parts):
    """The pieces of a pet sentence as one phrase: "a dog", "a dog and a cat", "a, b and c"."""
    parts = [part for part in parts if part]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]

def _pets_together(pets):
    """Two or more of the same animal, each named: "two cats called Tom and Jerry", or None.

    Said one at a time they read like a list a machine wrote - "a cat called Tom and a cat called
    Jerry" - and the animal is the same both times, so it is said once with both names after it.
    """
    animals = [(p.get("animal") or "pet") for p in pets]
    if len(pets) < 2 or len(set(animals)) != 1:
        return None
    if not all(not p.get("count") for p in pets):
        return None
    named = [p for p in pets if p.get("name")]
    nameless = [p for p in pets if not p.get("name")]
    if not named:
        return None
    animal = animals[0]
    many = animal if animal.endswith(("fish", "sheep", "deer")) else animal + "s"
    count = len(pets)
    names = [_called(p.get("name")) for p in named]
    if len(nameless) == 1:
        # A second animal they have not named yet is not said as "a cat and a cat called Max",
        # which is two animals described one at a time and reads as a list a machine wrote. It is
        # the whole set said once, with the one name they gave and the gap beside it: "i have a
        # cat" then "my other cat is called Max" is "two cats - Max and one you haven't named".
        return (NUMBER_WORDS.get(count, str(count)) + " " + many + " \u2014 "
                + _put_together(names + ["one you haven't named"]))
    if len(nameless) > 1:
        return None
    return (NUMBER_WORDS.get(count, str(count)) + " " + many + " called "
            + ", ".join(names[:-1]) + " and " + names[-1])

def _a_pet(pet):
    """"a cat", "a cat called Milly", "two cats": a number they gave is said back as a number."""
    # The breed they named comes first: "we got a rescue greyhound" is said back as a greyhound.
    animal = str(pet.get("breed") or pet.get("animal") or "pet")
    count = pet.get("count") or 1
    if pet.get("name"):
        try:
            many = int(count) > 1
        except (TypeError, ValueError):
            many = False
        if many:
            # "i have 2 cats" then "and her name is biscuit" is two cats with one name between
            # them, and "a cat called Biscuit" answers it as one animal: the number they gave
            # stays in the reply.
            plural = animal if animal.endswith(("fish", "sheep", "deer")) else animal + "s"
            return (NUMBER_WORDS.get(int(count), str(count)) + " " + plural + ", one called "
                    + _called(pet.get("name")))
        return _a(animal) + " called " + _called(pet.get("name"))
    if int(count) > 1:
        many = animal if animal.endswith(("fish", "sheep", "deer")) else animal + "s"
        return NUMBER_WORDS.get(int(count), str(count)) + " " + many
    return _a(animal)

ADVICE_ASK = re.compile(
    r"\bdo i (?:need|have) to\b|\bshould i\b|\bhow (?:often|much|long|many)\b|"
    r"\bwhen (?:should|do|can|must) i\b|\bcan i\b|\bis it (?:ok|okay|fine|safe)\b|"
    r"\bwhat (?:should|can|could) i (?:do|feed|give|use|buy|get)\b|\bhow (?:do|can) i\b")

def _a_why_line_they_have_answered(text, memory):
    """A why-line the store can answer, because it holds the subject the line names."""
    low = " ".join(str(text or "").lower().split())
    return bool(re.search(r"\bwhy\b", low)) and _holds_the_subject(memory, text)

def _holds_the_subject(memory, text):
    """Whether the store has the thing a why-line names, so it can say what they said.

    The subject is read the way every other fact ask reads it, and then looked for where the
    store keeps it: nothing filed means nothing to say, and "you haven't told me" is not an
    answer to a question about the world.
    """
    key = recall.ask(text, why=True)
    if not key:
        return False
    known = user(memory) or {}
    held = known.get(_SUBJECT_KEYS.get(key, key))
    if key == "limit":
        return bool(held or known.get("diet") or known.get("limits"))
    return bool(held)

def _asks_for_a_fact(low, text="", memory=None):
    """True when the line asks for one of their own facts, in the words they use for it.

    "my dog", "allergic", "my budget" are the plain forms; "what pets do I have?" and "do I have
    any allergies?" the same asks without the word my. A line that asks what they said about
    something ("what did I say about the dog?") is a read of the chat, not a fact recall, and
    belongs to the store's own quote.
    """
    if re.search(r"\bmy (?:dog|cat|pet)s?\b", low) and ADVICE_ASK.search(low):
        return False
    # "why do I have allergies", "why do we have pets": the store has no cause to give, so a
    # why-ask is not a read of it - it was answered "You haven't mentioned an allergy to me."
    # over a line that never asked what they had said. The one exception is the subject they
    # have just said: "my dog is called rex" then "why do we have pets" is "You've got a dog
    # called Rex.", which is a warm and right answer, and a search hedge for it loses what
    # they told you (black-lantern on #4437). So the store speaks when it holds the subject
    # and stays quiet when it would only be saying it holds nothing.
    if re.search(r"\bwhy\b", low):
        return _holds_the_subject(memory, text)
    if re.search(r"\bmy (?:dog|cat|pet)s?\b|\ballerg\w*\b|\bmy budget\b", low):
        return True
    if re.search(r"\bwhat (?:did|have) i\b", low):
        return False
    return bool(ASK_WITHOUT_MY.search(low))

def _vary(options, memory):
    """pick(), but over the whole reply: a lead-in and a body put together can repeat a line
    the bot said, even when the pieces on their own do not."""
    turns = memory.get("turns") or []
    recent = {t.get("bot") for t in turns[-5:]}
    fresh = [o for o in options if o not in recent] or list(options)
    return random.Random(len(turns)).choice(fresh)

def _turn_lines(memory):
    """The user and bot lines of the earlier turns, oldest first."""
    lines = []
    for turn in memory.get("turns") or []:
        if isinstance(turn, dict):
            lines.append((str(turn.get("user") or ""), str(turn.get("bot") or "")))
    return lines

def _repeat_ask(text, low, memory=None):
    """True when the line asks to hear the bot's last reply again, not about its content."""
    if WHOLE_ASK.match(str(low or "").strip()):
        # A whole-answer ask is the store's only when there is a whole answer behind it. With
        # nothing but a hello or a nod above it the store has nothing to hand over, and claiming
        # the line took "hi" / "in full" and "thanks" / "the lot" off the ordinary reply and
        # answered "Nothing from me on that yet. What were you asking about?" back at a person
        # who had asked for nothing.
        return True if memory is None else _a_whole_answer_to_hand_back(memory, text)
    if not REPEAT_ASK.search(low) or not REPEAT_START.match(low):
        return False
    # The words are read off the folded line, not the raw one: "what did you say earlier in this
    # chat" is the ask without the wrapper, and reading the raw line put "chat" among its content
    # words - so the ask was not a repeat ask, and the line was handed the shrug instead of the
    # answer it asked to hear again.
    return set(keywords(REPEAT_TAIL.sub(" ", low))) <= REPEAT_WORDS

FIGURE_REPEAT = re.compile(
    r"\b(?:how long|how many|how often|how soon|what time|what temperature|"
    r"which temperature|what setting|how hot|when)\b")

def asks_again(text, memory=None):
    """True when the whole line asks to hear the bot's last reply again.

    The store's own reading of the ask, published so the arbiter asks for it instead of keeping a
    second copy of the frame in its own file: the copy missed "pardon" and "come again", and a
    repeat that is not recognised as one is passed over as a line saying the same thing twice.
    """
    low = str(text or "").strip().lower()
    return bool(low) and _repeat_ask(low, low, memory)


def _repeat_reply(memory, text=""):
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    said = [turn for turn in turns if str(turn.get("bot") or "").strip()]
    whole = bool(WHOLE_ASK.match(str(text or "").strip().lower()))
    # A line that takes something back answered nothing, so its acknowledgement is not what the
    # person wants said again: "how long do i roast a chicken" / "forget the chicken" / "say that
    # again" handed back "Sure - Got it - forget the chicken." The answer to repeat is the last one
    # that answered something; where the take-back is all the chat has, its reply still stands.
    if said and named_thing.takes_back(said[-1].get("user")):
        answered = [turn for turn in said[:-1]
                    if not named_thing.takes_back(turn.get("user"))]
        said = answered or said
    if not said:
        return _vary(["I haven't said anything yet — you go first.",
                      "Nothing from me so far. What would you like to talk about?"], memory)
    line = str((memory.get("understood") or {}).get("text") or "")
    about = _hearing_again(said, line)
    if whole and (about is None or about.get("module") not in ANSWER_MODULES):
        # A request for the whole of it with no answer behind it: a hello, a nod, or something
        # the bot said that is not an answer. "im fine thanks" / "in full" came back framed "Same
        # answer, and it covers this: Fair enough", which promises an answer that does not exist.
        # The store has nothing to hand over, so it says nothing at all and the ordinary reply to
        # the line stands, exactly as it does on main ("Alright then - good luck with it.").
        return None
    if about is None:
        # Nothing behind the ask: no answer and nothing that carried content, only a hello or a
        # nod. "Sure - Fair enough." is the bot promising the answer again and handing back a nod.
        return _vary(["Nothing from me on that yet. What were you asking about?",
                      "I haven't given you an answer on that yet. What is it you want to know?",
                      "Nothing of mine to give back there yet - what was the question?"], memory)
    if (FIGURE_REPEAT.search(str(text or "")) and not re.search(r"\d", str(about.get("bot") or ""))
            and about.get("module") not in ANSWER_MODULES):
        # "im in a good mood" / "how long did you say": the ask names a length and the line it
        # would hand back has no length in it, so there is nothing to say again.
        return _vary(["I haven't said a length yet - what are you timing?",
                      "Nothing with a time in it from me so far. What are you looking at?"], memory)
    last = str(about.get("bot") or "")
    # Said back as it was, with only a short lead-in: a reply that already has quotes in it
    # ("Your first line was: ...") must not end up quoted twice, and asking twice must not
    # stack the lead-in ("Again — Again — ...").
    # A frame this codebase puts on a hand-back is taken off first, so asking twice does not stack
    # two of them with this module's short one in front: the answer above was "Same as before: Say
    # it once, plainly.", and the reply then read "Sure - Same as before: Say it once, plainly."
    from ..memory import again as same_again  # read here, as the two callers above do
    base = same_again.unframed(last) or last
    base = re.sub(r"^(?:sure|again|of course)\s*[—-]\s*|^here it is again:\s*", "", base,
                  flags=re.I)
    if FIGURE_REPEAT.search(str(text or "")):
        # The ask names the figure, so the figure is the answer: "18 to 20 minutes." rather than
        # the paragraph it sits in. Anything else in the ask ("how long did you say to rest it")
        # narrows to nothing, and the answer stands as it was.
        figure = narrow.narrow(str(base), str(text or ""))
        if isinstance(figure, str) and figure.strip():
            base = figure.strip()
    if about.get("module") not in ANSWER_MODULES:
        # Not an answer to give again, so nothing is promised: "Sure - Nice to meet you, Sam" is
        # the bot promising an answer and handing back a greeting. The line is said as it was.
        return base
    if WHOLE_ASK.match(str(text or "").strip().lower()):
        # The person asked for the whole of it, so the lead-in says that is what this is. The
        # answer is handed over as it was written, not cut to the part that was left out: "in
        # full" is the one ask that wants the paragraph a second time, and it says so.
        return _vary(["All of it: " + base, "Here it is in full: " + base,
                      "The whole of it, then: " + base], memory)
    return _vary(["Sure — " + base, "Again — " + base, "Here it is again: " + base, base],
                 memory)

ANSWER_MODULES = frozenset(("answers", "loss", "grief", "safety", "urgent"))

def _a_whole_answer_to_hand_back(memory, text=""):
    """True when the chat's last answer is one this store can hand over whole.

    The same reading `_repeat_reply` makes - the last line the bot said that answered something,
    a take-back passed over - so the claim and the reply are about the same turn.
    """
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    said = [turn for turn in turns if str(turn.get("bot") or "").strip()]
    if not said:
        return False
    if named_thing.takes_back(said[-1].get("user")):
        said = [turn for turn in said[:-1]
                if not named_thing.takes_back(turn.get("user"))] or said
    about = _hearing_again(said, str(text or ""))
    return about is not None and about.get("module") in ANSWER_MODULES

def _carries_something(turn):
    """True when a bot turn has something in it to hear again.

    "Glad that helped.", "Sounds good.", "Alright then — good luck with it." are nods. Asked
    "say that again" after one of them, repeating the nod is repeating nothing: the thing the
    person wants back is the answer the nod followed.
    """
    reply = str(turn.get("bot") or "").strip()
    if not reply:
        return False
    if _about_this_chat(str(turn.get("user") or "")):
        # The bot's own paperwork: "You started with: "we got a puppy"" is the store quoting the
        # chat back, not something the person asked to hear again. Asked "what did you say
        # earlier" a turn after a recall, handing that line back told them their own first line
        # twice in a row.
        return False
    return turn.get("module") in ANSWER_MODULES or len(reply.split()) >= 8

NOD_WORDS = frozenset("""thanks ta thx ty thank you cheers much so very really that this helps
                         helped for the lot got it ok okay k kk great nice brilliant awesome
                         perfect lovely cool fair enough right alright indeed yes yeah yep
                         sure fine good ah oh""".split())

def _only_a_nod(line):
    """True for a line that says nothing but thank you or so: "thanks", "got it", "ok cheers"."""
    found = re.findall(r"[a-z']+", str(line or "").lower())
    if not found or len(found) > 4:
        return False
    return all(word in NOD_WORDS for word in found)

def _hearing_again(said, line):
    """The bot turn a repeat ask is about: the last line, or the last one with content in it.

    "thanks" / "Glad that helped." / "say that again" is a person asking for the answer they
    thanked the bot for, so the nod is passed over. A line that asks about the last thing said
    ("what did you just say", "pardon") is about the nod itself.

    A nod is not a question, so nothing the bot said back to one is the answer to hear again,
    whichever module said it: after a "thanks" the reply in hand was the nod's, not the answer's,
    and a repeat ask that lifted a figure out of it lifted the figure out of the wrong text.
    """
    if LAST_LINE_ASK.search(str(line or "")):
        return said[-1]
    live = [turn for turn in said if not _only_a_nod(turn.get("user"))]
    if live and len(live) < len(said):
        said = live
    answered = [turn for turn in said if not _about_this_chat(str(turn.get("user") or ""))]
    if answered and len(answered) < len(said):
        # A turn that was itself a question about the chat is the bot's paperwork, not an answer
        # to hear again: "what did i say at the start of this chat" then "what did you say
        # earlier" handed back "You started with: "we got a puppy last week"" a second time.
        said = answered
    if not thread.thin(str(said[-1].get("user") or "")):
        # The bot was answering a line of its own, so its last reply is the thing to hear again.
        return said[-1]
    # After a "thanks" or an "ok" the reply is a nod. The answer they want back is the one the
    # nod followed, and that is the last turn an answer came from.
    answering = [turn for turn in said if turn.get("module") in ANSWER_MODULES]
    if answering:
        return answering[-1]
    carrying = [turn for turn in said if _carries_something(turn)]
    if carrying:
        return carrying[-1]
    # Only a greeting or a nod to hand back, with the ask having nothing to be about: the caller
    # answers the line as it would have without the ask.
    return None

HELLO_FILLER = frozenset("""there all everyone everybody both you folks guys again friend
friends mate team""".split())

def _just_a_hello(line):
    """True for a line that is only a greeting ("hi", "good morning", "hiya there").

    Only greetings, word by word: "what are you exactly" is a real question that happens to be
    short, and "hi we got a cat" is a cat. A word that is not a greeting, an acknowledgement or
    one of the few fillers that ride along with a hello means the line said something.
    """
    if "?" in line:
        return False
    found = re.findall(r"[a-z']+", line.lower())
    return bool(found) and any(w in GREET for w in found) and all(
        w in GREET or w in ACKS or w in HELLO_FILLER for w in found)

def _worth_reporting(line):
    """True for a line that said something a chat can be said to have opened with.

    A chat that opened with "hi" began with the line after it: handing back "You started with:
    "hi"" tells them nothing they don't already know. The same goes for a line that was about
    the chat itself - "what have we talked about" handed back as "the first thing you said" is
    the bot quoting its own paperwork - so those are skipped too, and only a line that said
    something about their own life is reported.
    """
    return bool(line) and not _just_a_hello(line) and not history.not_a_subject(line)

def _first_reply(memory):
    """The first line the person sent, the way a friend would recall how the chat began."""
    lines = _turn_lines(memory)
    if not lines or not lines[0][0]:
        return _vary(["You haven't said anything yet, so this is the start.",
                      "We're just beginning — you go first."], memory)
    said = [line for line, _ in lines if _worth_reporting(line)]
    if not said:
        return _vary(["We've only just started — nothing of yours to look back on yet.",
                      "Only hellos so far: your first proper line is still to come.",
                      "Nothing of yours to report back yet — you've only said hello."], memory)
    first = said[0]
    options = ["You started with: \"" + _trim(first) + "\"",
               "Your first line was: \"" + _trim(first) + "\"",
               "That's how we opened: \"" + _trim(first) + "\""]
    if len(said) <= 1:
        options.append("This chat opened with: \"" + _trim(first) + "\" — not much else yet.")
    return _vary(options, memory)

def _what_i_said_about(memory, thing):
    """The bot's own answer about the thing they name, in a sentence, or None.

    "what did you say about chewing" after "hes chewing all the furniture" reached nothing at all
    - two of its shapes got the shrug about not knowing enough, and "remind me what you said
    about chewing" was read as a job for a body that has no hands. The answer is in the chat, so
    it is the answer: the last turn that was about the thing, said in a sentence, with the
    question that earned it named so the person knows which one is coming back.
    """
    words = {word for word in keywords(thing or "") if word not in STOPWORDS}
    if not words:
        return None
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    for turn in reversed(turns):
        if str(turn.get("module") or "") in ("safety", "urgent", "grief", "loss"):
            return None  # an emergency answer is not read out again as a quotation
        said = str(turn.get("bot") or "").strip()
        asked = str(turn.get("user") or "")
        if not said:
            continue
        # The answer matches when it *opens* on the thing: "Chewing is normal while teeth
        # change" is what was said about chewing. A word that merely turns up in the middle of a
        # paragraph is not the thing that paragraph was about.
        opening = re.split(r"(?<=[.!?])\s+", said)[0]
        in_answer = words <= {word for word in keywords(opening)}
        in_question = words <= {word for word in keywords(asked)}
        if not _carries_something(turn) or not _adds_something(said, asked):
            continue  # a nod, or the line said back, is not an answer about the thing
        if not (in_answer or in_question):
            continue
        parts = re.split(r"(?<=[.!?])\s+", said)
        sentence = parts[0].strip()
        # An opening that says little on its own ("A puppy - good to know.") takes the sentence
        # after it along, so the quotation is not a nod with the thing's name in it.
        if len({word for word in keywords(sentence)} - NOD_WORDS) <= 2 and len(parts) > 1:
            sentence = sentence + " " + parts[1].strip()
        if not sentence or len(sentence.split()) > 45:
            sentence = " ".join(sentence.split()[:45]).rstrip(",;:") + "..."
        name = " ".join((thing or "").split())
        return pick(["On " + name + ": " + sentence,
                     "I said: " + sentence,
                     "What I said about " + name + ": " + sentence], memory)
    if len(words) <= 4:
        # Nothing in the chat was about it. Saying so, and naming it, is the answer - the shrug
        # about not knowing enough told them nothing and asked nothing back.
        name = " ".join((thing or "").split())
        return pick(["I don't think we've been over " + name + " yet - what do you want to know?",
                     "We haven't got to " + name + " yet. Ask me and I'll say what I know.",
                     name[:1].upper() + name[1:] + " hasn't come up yet - ask away."], memory)
    return None

def _adds_something(said, asked):
    """True when a bot line says more than the line it answers, so it can be quoted as an answer.

    "hes chewing all the furniture" / "Got it - he's chewing all the furniture." is the line said
    back with a nod in front. Handing that to "what did you say about chewing" quotes the person
    to themselves and calls it the bot's answer.
    """
    said_words = {word for word in keywords(said)} - NOD_WORDS
    asked_words = {word for word in keywords(asked)}
    return bool(said_words - asked_words)

def _first_bot_reply(memory):
    """The first thing the bot said, for "what was the first thing you said?"."""
    first = _first_sentence(history.first_bot_line(memory))
    if not first:
        return "I haven't said anything yet — you go first."
    return _vary(["I opened with: \"" + first + "\"",
                  "My first line was: \"" + first + "\"",
                  "I started with: \"" + first + "\""], memory)

def _asked_and_answered(memory):
    """The last line they said that was about something, and the bot's own reply to it.

    Not simply the last turn: a recall said twice in a row must come back with the same answer
    both times ("what should i cook tonight" / "what did i just tell you" / "what did i just tell
    you"), and reading the previous recall out as the question and as the answer makes each reply
    longer than the last until it is all that is left of the conversation.
    """
    for seen in reversed(recent(memory, 8)):
        line = str(seen.get("user") or "")
        if line and not _about_this_chat(line):
            return line, str(seen.get("bot") or "").strip()
    return "", ""

THEIR_OWN_ASK = re.compile(r"\b(?:i|me|my|mine|we|our|ours)\b", re.I)

def _said_reply(memory):
    """The person's own last line, for "what did I just say?"."""
    last = last_user(memory)
    if not last:
        return "That was your first line — there's nothing before it."
    # A recall said after a recall is about the thing the chat is on, not about the question just
    # asked: "my wife is a nurse" / "what did i just say about herpes" / "what did i tell you"
    # hands back the fact, and reading the previous question out instead ("you said: what did i
    # just say about her") is the same shrug in a friendlier voice. The store already knows which
    # of the two it filed, so the fact wins whenever there is one.
    real = _last_real(memory)
    if real and _just_a_hello(real):
        # A greeting is not a thing they told us about themselves: "hi" / "what did i just tell
        # you" was answered "You said: \"hi\"", which says nothing and sounds like a machine.
        real = ""
    if real:
        last = real
    elif _asks(last):
        # A question they asked is not something they told us either, and quoting it back is the
        # bot saying their own line at them: "whats the capital of france" / "what did i just tell
        # you". What was told is the answer they got, so that is what comes back, and how depends
        # on whether it can be read again: a short answer is the answer, and the part that gave it
        # repeats it better than the store could ("Same answer, and it covers this: Paris."), so
        # the store passes. A long explanation cannot be read out a second time, and passing it
        # left the turn to the bot-describing-itself line, which is a non-sequitur: the store names
        # the question and gives the short of its own answer instead.
        asked, mine = _asked_and_answered(memory)
        if not asked:
            # A chat that has only asked about itself so far ("where do i live") has that
            # exchange to hand back, though `_asked_and_answered` skips it as chat-about: it was
            # answered "You haven't mentioned a place yet", and passing it left the turn to the
            # search hedge. A recall after a recall is not the exchange to hand back, so those
            # lines are left to the guard above.
            for seen in reversed(recent(memory, 2)):
                line = str(seen.get("user") or "")
                if line and not SAID_ASK.search(line.lower()) and not FIRST_ASK.search(line.lower()):
                    asked, mine = line, str(seen.get("bot") or "").strip()
                    break
        again = _about_this_chat(last)
        # A question is worth handing back when it is all the chat holds: small talk ("hi" /
        # "how are you") or an ask about themselves ("where do i live") that the store had no
        # answer for. Passing it left the turn to the search hedge ("I don't know enough to
        # answer that honestly"), which says less than the exchange they just had did.
        nothing_yet = not real and (bool(history.not_a_subject(asked))
                                    or bool(THEIR_OWN_ASK.search(asked or "")))
        if mine and (nothing_yet or (not _just_a_hello(asked)
                                     and (again or len(mine.split()) > A_SHORT_ANSWER))):
            asked = _trim(asked).rstrip(" .!?")
            first = re.split(r"(?<=[.!?])\s+", mine)[0].strip()
            return _vary(["You asked: \"" + asked + "\" — I said: " + first,
                          "That one was your question: \"" + asked + "\". My answer: " + first,
                          "You asked \"" + asked + "\", and what I said was: " + first],
                         memory)
        return None
    else:
        # Nothing they told us yet, so say that rather than quote a greeting back at them.
        return _summary_reply(memory)
    fixed = memory.get("correction") if isinstance(memory, dict) else None
    fixed_words = " ".join(str((fixed or {}).get("sentence") or (fixed or {}).get("value") or "")
                           .split())
    if isinstance(fixed, dict) and fixed_words \
            and fixed.get("said") == " ".join(str(last).lower().split()):
        # Their last line was a correction of the one before it ("no, june", "make that 8"), and
        # handed back on its own it says nothing: "You said: \"no, june\"" leaves them to work
        # out what was corrected. What they said is the line with the correction in it.
        said = fixed_words.rstrip(" .!?")
        return _vary(["You said " + said + " — you put me right on it.",
                      "You said " + said + ", and that is the version I am going with.",
                      "\"" + said + "\" — your first line, put right a moment later."], memory)
    return _vary(["You said: \"" + _trim(last) + "\"",
                  "Your last line was: \"" + _trim(last) + "\"",
                  "That was: \"" + _trim(last) + "\""], memory)

ASKS_IN_LINE = re.compile(r"[,;:\u2013\u2014-]\s*(?:what|whats|why|how|hows|when|where|wheres|who|"
                          r"which|whose|can|could|should|would|do|does|did|is|are|was|were|will|"
                          r"shall|have|has)\b", re.I)

CORRECTS = re.compile(r"\b(?:rather than|instead of|scratch that|or rather)\b|"
                      r"\bi (?:meant|mean)\b|\bnot\s+(?:the\s+)?\w+\s*[.!]?$", re.I)

def _corrects(line):
    """"sorry, Naples not Rome" replaces an earlier line instead of saying something new."""
    return bool(CORRECTS.search(" ".join((line or "").lower().split())))

def _last_real(memory):
    """The last thing the user said that was about something, not about this chat.

    A question about the chat is not what the chat was about: "what did i say the party was
    for?" must not come back as "we were on this: \"what did i say the party was for?\"".
    """
    for seen in reversed(recent(memory, 8)):
        line = seen.get("user") or ""
        if line and not _about_this_chat(line) and not _asks(line):
            return line
    return ""

SAID_ABOUT = re.compile(
    r"\bwhat (?:was|were|am|are) (?:i|we) (?:saying|talking|chatting|on)\b[^.?!]*\babout\b",
    re.I)

DENIAL = re.compile(
    r"\bhaven't said anything\b|\bhaven't mentioned\b|\bnothing comes to mind\b", re.I)

def _the_fact_is_kept(key, memory):
    """True when the store holds the fact a recall key names."""
    slot = KEY_SLOT.get(key)
    return bool(slot and user(memory).get(slot))

def _a_denial(reply):
    """True when the reply is the store saying it has nothing about the thing."""
    return bool(reply) and bool(DENIAL.search(reply))

def _names_its_thing(low):
    """True when a "what was i saying about ..." line names the thing it asks about.

    "what were we on about?" and "what was i saying about it?" point at the subject instead of
    naming it, and the chat's own topic is the honest answer to those; only a line that names
    something ("about pasta", "about the boiler") is a lookup by name.
    """
    after = re.search(r"\babout\b\s+(.+)$", low or "")
    if not after:
        return False
    thing = re.sub(r"\b(?:again|before|earlier|please|so far|up to now|until now)\b",
                   "", after.group(1)).strip(" ?!.,")
    if not content(thing) or thing in ("it", "that", "this", "them", "that one"):
        return False
    return True

def _say_back(line, memory=None):
    """Their own line said again as a sentence about them, with no quotation marks round it.

    A recap of a thing the chat has moved on from reads better as a statement than as a quote:
    "what was i saying about pasta earlier" is answered "You said like you can do pasta but
    thats it", which is the same sentence a friend would say.
    """
    said = (thread.restate(line) or _recap(line) or "").strip().rstrip(".")
    if not said:
        return _recall_quote(line, memory)
    said = said[:1].lower() + said[1:]
    return _vary(["You said " + said + ". Want to carry on?",
                  "You said " + said + "."], memory)

REFLEXIVE = frozenset(("myself", "yourself", "ourselves", "themselves"))

def _recall_reply(memory, low, text="", spoken=False):
    """The line they are asking about: "what did i say about the cake?", "and about it?".

    The thing asked about is matched by stem over the last user lines, so "the cakes" finds
    "i want to bake a cake for my daughter", and "what did i say the party was for?" finds the
    line that mentions the party. A line that only asks about the chat is skipped: otherwise
    "what did i tell you about it?" answers with an earlier question.

    Returns None when the line does not name a thing, so the caller can answer with the topic
    instead of denying something the user did say.
    """
    # "what did i say was hurting" asks about a complaint the store holds, and it holds the one
    # that stands now: quoting the first line back contradicts the store's own record after a
    # correction ("my knees..." then "my back hurts not my knees" quoted the knees).
    hurt = a_hurting_part.what_is_hurting_reply(memory, low)
    if hurt:
        return hurt
    about = re.search(r"\babout\b(.*)$", low)
    part = None if about else _which_thing_was_it(low, memory)
    if about:
        thing = about.group(1)
    elif part:
        # "and which knee was it" names the thing the detail is about, so the line to find is
        # the one that says which knee it was: the thing is the word to look for.
        thing = part
    else:
        after = re.search(r"\b(?:say|said|tell you|told you|mention)\b(.*)$", low)
        thing = after.group(1) if after else ""
    # The named-back form is said in their words, not in the normalised line: "my mum's
    # birthday" keeps its possessive when it becomes "your mum's birthday".
    mine = re.search(r"\babout\b(.*)$", text or "", re.I)
    shown = (mine.group(1) if mine else thing).strip(" ?!.,")
    thing = re.sub(r"\b(?:again|before|earlier|please|so far|up to now|until now)\b",
                   "", thing).strip(" ?!.,")
    if thing.lower() in REFLEXIVE:
        # "what did i tell you about myself" is the whole picture, not a thing they said: there
        # is no line about "myself" to find, and the denial ("You haven't said anything to me
        # about myself yet") told a person who had just given their name that they had said
        # nothing. Left to the reader for "what do you know about me".
        return None
    if not content(thing):
        # "what's the noise again?" names the thing instead of saying "about it": the word it
        # names is what to look for in their lines.
        named = THING_AGAIN.match(low)
        if named:
            thing = named.group(1)
        else:
            # The same thing named in a reminder: "what was wrong with my boiler again",
            # "remind me what the problem with the car was". The reading is the one the gate
            # uses, so a line it takes is answered here rather than by the chat's topic.
            reminded_thing = reminded.the_thing(text or low, memory)
            if reminded_thing:
                thing = reminded_thing
    # "what did i say to her?" is what they said to someone else, not to the bot: the old "what
    # did i say" branch guarded this, and so must this one.
    if re.match(r"to\s+(?!me\b|you\b)", thing):
        return None
    # "for a living" is the job said as a phrase, not a thing a line is about: "what did i say
    # i do for a living" was read by its words ("do", "living") and found "i live in leeds", so
    # the town came back as the job. The words name the kind of fact, and the fact reader
    # further down answers it in the store's own sentence ("You work as a nurse."), so this ask
    # is left to it rather than quoted from whichever line shares a word.
    if recall.LIVING.search(thing):
        return None
    words = content(thing)
    if not words or thing in ("it", "that", "this", "them", "that one"):
        real = _last_real(memory)
        if real:
            return _recall_quote(real, memory)
        record = current(memory)
        if record and record.get("text") and not _about_this_chat(record["text"]):
            return _recall_quote(record["text"], memory, asked=_asks(record["text"]))
        return pick(["You haven't told me anything about that yet.",
                     "Nothing comes to mind \u2014 you haven't said."], memory)
    # A line about the telling is not the thing told: "i told you about the damp" carries the
    # word and says nothing about the damp, so quoted back it answered "what did i say about the
    # damp" with the complaint that they had said it. It is kept apart rather than dropped: in a
    # chat where the telling is the only line about the thing, it is still what they said, and
    # with a line that states the thing it would be said beside it ("your dog or your dog died").
    hits, asked, fixed, claims = [], [], [], []
    for turn in _every_line(memory):
        line = turn.get("user") or ""
        if not line or _about_this_chat(line):
            continue
        seen = _seen(line)
        question = _asks(line)
        # A word of the ask finds the line by the kind it names as well as by the word: "what did
        # i say about my trip" is about "im going to lisbon in may", which never says "trip".
        # The kind is the shape of a plan they stated, so a line that only asks is not one: "when
        # is my trip" names the trip and states nothing, and read as the kind it comes back as
        # what they said about the holiday, when all they did was ask. The words still find it,
        # and the ask bucket quotes it as the question it is.
        if all(_alike(word, seen) or (not question and _about_kind(word, line, memory))
               for word in words):
            # "sorry, Naples not Rome" names Rome in order to replace it, so the line it
            # corrects is the one being asked about: quote that, not the correction.
            (asked if _asks(line) else fixed if _corrects(line) else
             claims if A_CLAIM_OF_TELLING.match(" ".join(line.lower().split())) else
             hits).append(line)
    if not hits and claims:
        hits = claims
    if hits:
        # A line that asks about the thing does not tell us the thing: "sorry, back to the
        # roast, what time should i start it" is the last line that mentions the roast, and
        # quoted back it looks like an answer and says nothing. Where an earlier line states it,
        # that is the line they are asking about. A chat whose only line about it is the question
        # keeps the question, because it is still true that they said it.
        stated = [line for line in hits if not ASKS_IN_LINE.search(line)]
        if stated:
            hits = stated
        # "what was i saying about pasta" is the chat going back over something it has moved on
        # from, so the line is said as a sentence; the quoting form belongs to "what did i say",
        # where the words themselves were asked for.
        if not spoken:
            put_right = _put_right_after_it(hits[-1], memory)
            if put_right:
                return put_right
            moved = _a_figure_put_right(hits[-1], memory)
            if moved:
                return moved
            narrowed = _a_narrowing_put_after(hits[-1], memory)
            if narrowed:
                return narrowed
        return _say_back(hits[-1], memory) if spoken else _recall_quote(hits[-1], memory)
    # The only line about it was a question, which they still said: "You asked: \"...\"" is
    # true where "You said" would put words in their mouth, and where a denial would be a lie.
    if asked:
        return _recall_quote(asked[-1], memory, asked=True)
    if fixed:
        return _recall_quote(fixed[-1], memory)
    # A recall ask carries its own judgement: "what did i say was wrong with my flat" asks about
    # the flat, and "wrong" is the ask's word rather than the person's. The full set of words is
    # tried first, so a line that does use the judging word still matches it; only when nothing is
    # found are those words dropped, and the rest of what was named is enough to find the line.
    naming = [word for word in words if word not in JUDGING and word not in A_ROLE]
    if naming and naming != words:
        naming_hits, naming_asked = [], []
        for turn in recent(memory, 8):
            line = turn.get("user") or ""
            if not line or _about_this_chat(line):
                continue
            seen = _seen(line)
            if all(_alike(word, seen) for word in naming):
                (naming_asked if _asks(line) else naming_hits).append(line)
        if naming_hits:
            return _recall_quote(naming_hits[-1], memory)
        if naming_asked:
            return _recall_quote(naming_asked[-1], memory, asked=True)
    # "what did i say was wrong with it": the only word left is the ask's own judgement and the
    # thing is a pronoun, so there is nothing to find and the line it asks about is the one they
    # last told me about - the subject of the chat.
    if not naming and PRONOUN_ASK.search(thing):
        real = _last_real(memory)
        # A greeting is not a thing that could be wrong: one content word is small talk, and the
        # ask gets the honest "you haven't said" instead of "you said: hello".
        if real and len(content(real)) > 1:
            return _recall_quote(real, memory)
    if not about:
        return None
    # The thing is named back in the second person: a friend says "your mum", not "my mum".
    said = re.sub(r"^my\b", "your", shown).strip()
    return pick(["You haven't said anything to me about " + said + " yet.",
                 "You haven't mentioned " + said + " \u2014 say it and I'll keep it."], memory)

JUDGING = frozenset((
    "wrong", "bad", "good", "best", "worst", "right", "nice", "like", "dislike", "much", "many",
    "long", "often", "soon", "far", "big", "small", "else", "other", "another", "next", "first",
    "last", "again", "exactly", "actually", "really", "truly"))

A_ROLE = frozenset((
    "guest", "guests", "person", "people", "someone", "somebody", "man", "woman", "guy",
    "bloke", "lad", "friend", "colleague", "member", "kid", "child", "children", "folk"))

PRONOUN_ASK = re.compile(r"\b(?:it|its|that|this|them|those)\b")

TAGS = (
    ("holiday", re.compile(r"\b(?:going|gone|flew|flying|off|travell?ing|travel)\s+to\s+"
                          r"(?!the\b|a\b|an\b|my\b|our\b|his\b|her\b|their\b|work\b)"
                          r"|\babroad\b|\bholiday\b", re.I)),
)

def _tagged(line):
    """The words a line stands for without saying them: the ask's own word for that thing."""
    low = str(line or "")
    return {concept for concept, pattern in TAGS if pattern.search(low)}

def _the_same_person(who):
    """Every word the chat may use for the person an ask names, its own word first.

    "my mum died in january" then "what did i say about my mother?" is one person asked about
    twice, and reading the ask's word alone said "you haven't told me anything about your mother"
    about a line they had just said. The concept table above already holds the everyday pairs
    (mum/mother, dad/father), so the person is read through it rather than by a list of its own.
    """
    who = str(who or "").strip().lower()
    if not who:
        return []
    concept = CONCEPTS.get(who)
    words = [who]
    if concept:
        words += [word for word, its in CONCEPTS.items() if its == concept and word != who]
    return words

A_PROGRAMME_IS_ON = re.compile(
    r"\b(?:is|was|are|were)\s+(?:on|back on)\s+(?:tonight|now|tv|telly|later|this evening|"
    r"last night|tomorrow|at \d|bbc|itv|channel|netflix|prime)\b", re.I)

def _the_name_pattern(who):
    """A line that names this person, in any of the words the chat uses for them.

    The word has to stand where a person stands: after "my"/"our" ("my dad"), or where the line
    turns to them ("we went out, dad paid"). "my mum loves dad jokes" is a line about the mum and
    not about the dad, so the word alone is not enough.
    """
    called = "(?:" + "|".join(re.escape(word) for word in _the_same_person(who)) + ")"
    # An in-law is not the parent: "my mother in law is 70" is somebody else, and "my father in
    # law" opens with "my father". The relation tail is what says so, in either spelling.
    not_a_relation = r"(?!\s*-?\s*in\s*-?\s*law)"
    return re.compile(r"\b(?:my|our)\s+" + called + not_a_relation + POSSESSIVE + r"\b|"
                      r"(?:^\s*|[,;]\s*|\b(?:and|but|also|then)\s+)" + called
                      + not_a_relation + POSSESSIVE + r"\b", re.I)

PERSON_STANDS = re.compile(
    r"(?:^\s*|[,.;:!?)—]|\b(?:is|are|was|were|has|have|had|does|do|did|can|could|will|would|"
    r"shall|should|might|must|needs?|needed|wants?|wanted|says?|said|said|called|rang|phoned|"
    r"texted|loves?|likes?|hates?|came|comes?|coming|went|goes|going|got|gets|getting|thinks?|"
    r"thought|knows?|knew|feels?|felt|feeling|worried|ill|unwell|poorly|sick|poor|well|fine|"
    r"who|that|which|and|too|as|again|now)\b|$)", re.I)

def _the_word_for_them(who):
    """Every word for this person standing where the person stands, anywhere in the line.

    A line about somebody does not have to open with them: "i think mum is allergic to shellfish"
    and "the doctor said dad needs a scan" are about the mum and the dad, and the store said it
    knew nothing about either. The word has to stand where a person stands, which is what keeps
    "dad jokes" out of the dad's lines.
    """
    words = "|".join(re.escape(word) for word in _the_same_person(who))
    return re.compile(r"\b(?:" + words + r")" + POSSESSIVE + r"\s*" + PERSON_STANDS.pattern, re.I)

KINDS = (
    ("trip", frozenset("trip trips holiday holidays vacation getaway break travel journey flight"
                        " abroad".split())),
    ("job", frozenset("job jobs work career shift shifts employment".split())),
    # What they eat is said in the food itself, never in the word: nobody says "my food is
    # vegetarian", they say "im vegetarian" or "i dont eat meat", and the ask "what did i say
    # about food" was answered "You haven't said anything to me about food yet." one line later.
    ("food", frozenset("food foods diet meals meal dinner tea supper lunch breakfast eating"
                       " cooking".split())),
    # Where they live is a kind of its own, and a move says it as well as the word does: "we live
    # in leeds" then "we moved to york last year" is one fact in two lines, and the ask "what did
    # i say about where i live" quoted "we live in leeds" - the home they had just left - because
    # only the first line uses the word "live". The newest line of the kind is the one the chat is
    # on, and the store already keeps the city the last one named.
    ("home", frozenset("live lives living home house city town address moved move moves"
                       " moving".split())),
)

SAYS_A_TRIP = re.compile(r"\b(?:holidays?|vacation|getaway|abroad|trips?|travell?ing|flight|flying|"
                         r"cruise|week away)\b", re.I)

NOT_A_PLACE_IN = frozenset("""bed pain limbo prison hospital hospice traction tears denial
hiding isolation quarantine plaster shock mourning""".split())

SAYS_A_STAY = re.compile(
    r"\b(?:a |the )?(?:few |couple of |two |three |four |five )?(?:days?|nights?|weeks?|weekend)"
    r"\s+(?:away\s+)?in\s+(?:(?:the|a|an)\s+)?(?P<place>[a-z]{3,})", re.I)

def _a_stay_in_a_place(text):
    """True when the line says a stretch of time somewhere they are going."""
    for found in SAYS_A_STAY.finditer(text):
        word = found.group("place").lower()
        if word in extract.NOT_PLACES or word in NOT_A_PLACE_IN:
            continue
        return True
    return False

SAYS_A_JOB = re.compile(r"\b(?:job|jobs|work|working|career|shift|shifts|office|employ\w*|"
                        r"promotion|interview|colleagues?)\b", re.I)

SAYS_FOOD = re.compile(
    r"\b(?:eat|eats|eating|eaten|ate|drink|drinks|drinking|drank)\b|"
    r"\b(?:vegetarian|vegan|pescatarian|diet|allerg\w+|intoleran\w+|gluten|dairy|sugar|meat|"
    r"fish|carbs?|keto|fasting|booze|alcohol)\b|"
    r"\b(?:cook|cooks|cooking|cooked|bake|baking|roast|recipe)\b", re.I)

SAYS_THE_KIND = {
    "trip": SAYS_A_TRIP,
    "job": SAYS_A_JOB,
    "food": SAYS_FOOD,
}

def _kind(thing):
    """The kind of thing an ask names, or "" when the word is a thing of its own."""
    for kind, words in KINDS:
        if thing in words:
            return kind
    return ""

def _says_where_they_live(text):
    """True when the line says where they live, in whatever words: "we moved to york last year".

    Read by the store's own places reader rather than by a second pattern here, so the words that
    make a place a home ("i live in a flat in leeds") are the same two readings in both places. A
    stay is not one: "we're staying in york for the weekend" names a visit.
    """
    if not isinstance(text, str) or not text.strip():
        return False
    try:
        found = extract.extract(text)
    except Exception:  # noqa: BLE001 - a line this cannot read names no home
        return False
    return bool(found.get("home"))

def _a_place_they_go(text):
    """The place a line says they are going to, or "": "im going to lisbon in may".

    Only the words that say somebody is travelling count, so where they live is not a trip: "i
    live in leeds" names a place and goes nowhere.
    """
    found = extract.PLACE_LOWER.search(text or "")
    if not found:
        return ""
    word = found.group(1).lower()
    if word in extract.NOT_PLACES or word in extract.PLACE_VERBS:
        return ""
    return word

def _about_kind(thing, text, memory=None, phrase=False):
    """True when `text` is about the kind of thing the ask names ("trip" -> "Lisbon in may").

    A trip is where they are going, in whatever words they used: a line that says they are going
    to a place is a trip though it never says the word. A plan kept as the bare phrase ("Lisbon in
    may") names no verb at all, so it is the trip when the place in it is one of theirs - which is
    why only a plan is read that way, and a line is not. A job is said in its own words ("i start
    at the hospital"), which is what SAYS_A_JOB is for.
    """
    kind = _kind(thing)
    if not kind or not isinstance(text, str) or not text.strip():
        return False
    said = SAYS_THE_KIND.get(kind)
    if kind == "job":
        return bool(said.search(text))
    # Where they live has no word of its own in the line that moves them, so the store's own
    # reading of a home is what decides, exactly as a place they are going decides a trip.
    if kind == "home":
        return _says_where_they_live(text)
    # A trip is the one kind with a second way of being said, so it is the only kind allowed to
    # answer a place: an ask about food must not be given "im going to lisbon in june".
    if kind == "trip" and (SAYS_A_TRIP.search(text) or _a_stay_in_a_place(text)
                            or _a_place_they_go(text)):
        return True
    if said is not None and said.search(text):
        return True
    if not phrase:
        return False
    known = (user(memory).get("places") or []) if isinstance(memory, dict) else []
    low = text.lower()
    return any(str(place).lower() in low for place in known if isinstance(place, str) and place)

def _seen(line):
    """The content words of a line, read the way the ask about it is read.

    The ask arrives in full words ("what did i say about my girlfriend") and the line it asks
    about stays as it was typed ("me and my gf are thinking of getting a cat"), so the line is
    put through the same reading before its words are taken. Otherwise a short spelling never
    reaches the word it stands for, and a two-letter one is not even a content word.
    """
    words = set(content(line))
    plain = normalise(line or "")
    plain = plain.get("norm_text") if isinstance(plain, dict) else ""
    if plain and plain != line:
        words |= set(content(plain))
    return words | _tagged(line)

def _alike(word, seen):
    """One word family is enough: "my allergy" finds "i'm allergic to nuts".

    A word finds its own family (the word with its verb ending on or off, stem, prefix, first
    five letters) and the words that name the same everyday thing, so "what did i say about the
    dog?" finds "we got a puppy" and "what did i say i was saving for?" finds "i want to save".
    """
    want = CONCEPTS.get(word)
    mine = forms(word)
    for other in seen:
        if word == other:
            return True
        if mine & forms(other):
            return True
        if want and want == CONCEPTS.get(other):
            return True
        if len(word) >= 4 and len(other) >= 4 and (word.startswith(other)
                                                  or other.startswith(word)):
            return True
        if len(word) >= 5 and len(other) >= 5 and word[:5] == other[:5]:
            return True
    return False

def _recall_quote(line, memory=None, asked=False):
    """"You said: \"...\": their own words, trimmed, so the answer is the thing itself.

    A question is quoted as the question it was: they still said it, so it is what the chat has
    been about, but "You said" would turn a question into a statement.
    """
    said = "\"" + _trim(line, 120) + "\""
    if asked:
        return ASKED_LEADS[(len(recent(memory, 8)) if memory else 0) % len(ASKED_LEADS)] + said
    if memory is None:
        return QUOTE_LEADS[0] + said
    # The same question twice should not read as the same sentence twice.
    asked = sum(1 for turn in recent(memory, 8)
                if re.search(r"\bwhat (?:did|have) i\b", (turn.get("user") or ""), re.I))
    return QUOTE_LEADS[asked % len(QUOTE_LEADS)] + said

# The echo of a line that was itself a telling: "you told me about your mum". A frame on top of it
# says the telling twice, and the echo already carries who told whom.
TELLING_ALREADY = re.compile(r"^you (?:told me|said to me|mentioned to me)\b")


A_BARE_PUT_RIGHT = re.compile(
    r"^\s*(?:sorry|no|nah|actually|oh|wait|hang on|hold on|i mean|my mistake|silly me|"
    r"correction)[\s,]*"
    r"(?:(?:its|it's|it was|make that|make it|i mean|should be|thats|that is)\s+)?"
    r"(?:about\s+|only\s+|just\s+)?"
    r"(?P<value>\d[\d,]*(?:\.\d+)?"
    r"(?:\s+and\s+(?:an?\s+)?(?:half|quarter))?)"
    r"(?:\s*(?:%|percent|per\s?cent|pounds?|quid|grand|k|stone|kg|miles?|mph|hours?|"
    r"minutes?|mins?|a\s+(?:month|week|year|day|night|person|guest|head))s?)?"
    r"\s*(?:[,!.]|\b(?:sorry|thanks|actually|i got it wrong|got it wrong|my mistake|silly me|"
    r"i think|i mean|then|right)\b)*\s*$", re.I)

A_FIGURE = re.compile(r"(?<![\w.,£$])(\d[\d,]*(?:\.\d+)?)")

def _a_figure_put_right(line, memory):
    """The quote and the figure the person put right after it, or "".

    A recall quotes the line the thing was said in, and the next line can put a figure in it
    right without naming the thing: "my rent is 1200 a month" / "sorry 1150, i got it wrong".
    Nothing in the store moves when that happens - a rent is not a fact the store keeps - so the
    quote came back as 1200 after the bot had already answered "Got it - 1150, you got it
    wrong": the chat contradicting itself one line after agreeing.

    The quoted line must hold one figure - with two in it there is no saying which one moved -
    and the correction must be the bare figure (see `A_BARE_PUT_RIGHT`), so a line about another
    thing that happens to hold a number is left alone. It must also be the line *right after* the
    quote: "my rent is 1200 a month" / "i weigh 14 stone" / "sorry 13 stone" is a weight put
    right, not the rent.
    """
    if not isinstance(memory, dict):
        return ""
    said = " ".join(str(line or "").split())
    figures = A_FIGURE.findall(said)
    if len(figures) != 1:
        return ""
    lines = [" ".join(str(turn.get("user") or "").split()) for turn in _every_line(memory)]
    places = [index for index, text in enumerate(lines) if text == said]
    if not places:
        return ""
    # Only the line right after the quote: a bare "sorry 13 stone" three lines later is about
    # whatever that line was about (a weight), not about the rent quoted, and saying the person
    # put the rent right would be putting words in their mouth.
    for after in lines[places[-1] + 1:places[-1] + 2]:
        found = A_BARE_PUT_RIGHT.match(after.strip())
        if not found:
            continue
        value = found.group("value").strip().rstrip(",")
        if not value or value == figures[0]:
            continue
        return (_recall_quote(line, memory).rstrip()
                + " \u2014 then you put it right: " + value + ".")
    return ""

def _a_narrowing_put_after(line, memory):
    """The quoted line and the narrowing the person put after it, or "".

    A recall can land on a line that narrows the one above it and says nothing on its own ("the
    ones that are open on sunday", "the cheaper ones"), and quoted alone it is their fragment with
    no thing in it. The reading of which lines those are is `repeat.a_narrowing_and_its_line`, so
    the two recall paths cannot drift apart.
    """
    if not isinstance(memory, dict):
        return ""
    pair = _a_narrowing_and_its_line(line, memory)
    if not pair:
        return ""
    before, after = pair
    return (_recall_quote(before, memory).rstrip()
            + " \u2014 then \"" + _trim(after, 80) + "\".")

def _put_right_after_it(line, memory):
    """The quoted line and the correction that followed it, or "" when there is none.

    A recall about a named thing quotes the line the thing was said in, and the person's next
    line can put that line right without naming the thing again: "the dinner is on friday" /
    "sorry, saturday". Quoting only the first line leaves the store contradicting the line it
    agreed to a turn earlier - "what did i say about my sons birthday" came back as May after
    "Got it - your son's birthday is in June". The correction the store filed is the end of the
    story, so the quote says both when the store has one for that line.
    """
    fixed = memory.get("correction") if isinstance(memory, dict) else None
    if not isinstance(fixed, dict):
        return ""
    said_back = " ".join(str(fixed.get("said") or "").lower().split())
    sentence = " ".join(str(fixed.get("sentence") or "").split()).rstrip(" .!?")
    if not (said_back and sentence):
        return ""
    lines = [" ".join(str(turn.get("user") or "").lower().split())
             for turn in _every_line(memory)]
    quoted = " ".join(str(line or "").lower().split())
    if said_back not in lines or quoted not in lines:
        return ""
    if lines.index(quoted) >= lines.index(said_back):
        return ""      # the line quoted is the correction itself, or came after it
    if not (_content_words(line) & _content_words(sentence)):
        return ""      # the correction is about something else in the chat
    tail = sentence[0].lower() + sentence[1:]
    return _recall_quote(line, memory).rstrip() + " \u2014 then you put it right: " + tail + "."

def _age_reply(memory):
    age = user(memory).get("age")
    # 6 is not an age anyone has ("i am 6 foot 2" is a height), so a number outside the range a
    # person can be is no answer at all, whatever an earlier line stored.
    if not age or not 1 <= age <= 120:
        return pick(["You haven't told me your age yet.", "I don't know it — you haven't said."],
                    memory)
    return pick(["You told me you're " + str(age) + ".", str(age) + " — you said."], memory)

def _content_words(line):
    return {word for word in re.findall(r"[a-z']+", line.lower())
            if len(word) > 3 and word not in STOPWORDS}

def _the_line_before_was_a_plan(memory):
    """True when the last thing they said was a plan of their own.

    "what am i up to?" is about what is coming up when the line before it said something coming
    up, and about the thing in their hands when that line said what they are doing now. The
    store knows which of its plans came from that line, so the ask is read there rather than
    answered by quoting the line back.
    """
    plan = (user(memory) or {}).get("plan")
    if not isinstance(plan, str) or not plan.strip():
        return False
    told = plan_line(memory, plan)
    if not told:
        return False
    return (" ".join(told.lower().split())
            == " ".join(str(last_user(memory) or "").lower().split()))

def _plan_was_corrected(memory):
    """True when the last thing they put right was a value inside the plan itself.

    The key is not always "plan": "we need to leave for the airport at 4" with "sorry, i meant
    5" corrects the line the plan was said in, and the plan is kept as "Leave for the airport
    at 5". What says the correction went into the plan is that the plan now holds the value
    they corrected it to.
    """
    changed = memory.get("correction") if isinstance(memory, dict) else None
    if not isinstance(changed, dict):
        return False
    if changed.get("key") in ("plan", "plans"):
        return True
    value = " ".join(str(changed.get("value") or "").lower().split())
    plan = " ".join(str((user(memory) or {}).get("plan") or "").lower().split())
    return bool(value) and bool(plan) and value in plan

def _about_the_same(line, line_words):
    """A line that carries on about the subject (a detail) and not a statement of its own."""
    return bool(DETAIL_START.search(line)) or bool(_content_words(line) & line_words)

def _activity_line(memory):
    """The last line in which they said what they were making, cooking or planning - a line of
    detail about it ("he is allergic to nuts") keeps the subject, so the plan is further back.
    A statement about something else ends the trail: what they were doing is then the newest
    statement, and if that one has no activity there is nothing to say back."""
    lines = [" ".join(str(turn.get("user") or "").split()) for turn in recent(memory, 4)]
    changed = memory.get("correction") if isinstance(memory, dict) else None
    fixed = " ".join(str(changed.get("said") or "").split()) if isinstance(changed, dict) else ""
    for wanted in (ACTIVITY_WORDS, ACTIVITY_LOOSE):
        for index in range(len(lines) - 1, -1, -1):
            line = lines[index]
            if not line or ASK_LINE.search(line) or ACTIVITY_ASK.search(line):
                continue
            if not wanted.search(line):
                continue
            words = _content_words(line)
            newer = [later for later in lines[index + 1:] if later]
            if any(fixed and later == fixed for later in newer):
                # A correction is the newest word on the thing they were on: they said the plan
                # another way, so the line they said before it is not what they are up to now.
                return ""
            if all(ASK_LINE.search(later) or ACTIVITY_ASK.search(later)
                   or _about_the_same(later, words) for later in newer):
                return line
            return ""
    return ""

# "Again" is the licence to cross a turn that changed the subject: the person is pointing at
# something they know they said, so an aside in between is not the chat moving on.
ASKING_AGAIN = re.compile(r"\bagain\b|\bremind me\b", re.I)

def _the_making_line_they_said(memory, back=8):
    """The last line of theirs that says what they are making, without the trail check.

    `_activity_line` stops the trail at the first line about something else, which is right for
    "what was i cooking?" in a chat that has moved on to a dishwasher. "Again" asks for a line
    the person knows they said, so what happened in between is not the subject to answer from:
    "im making a cake for my sons birthday" / "by the way my back is killing me" / "what am i
    making again" is still the cake. Without this the ask fell to a method card, or to "I'm not
    sure about that one" in a chat that says plainly what it is making.
    """
    for turn in reversed(recent(memory, back)):
        line = " ".join(str(turn.get("user") or "").split())
        if not line or ASK_LINE.search(line) or ACTIVITY_ASK.search(line):
            continue
        if ACTIVITY_WORDS.search(line) or ACTIVITY_LOOSE.search(line):
            return line
    return ""

def _recap(line):
    """Their own line said back as a sentence about them: "im making a cake" -> "You're making
    a cake for your son." Only a line that starts with the person and the plan is reworded;
    "i think im just going to have a bath" is quoted as it stands, which reads right."""
    flat = " ".join(str(line or "").split()).strip(" .")
    planned = re.match(r"^(?:im|i'm|i am|ive|i've|were|we're|we are)\s+(\S.*)$", flat, re.I)
    if planned:
        body = "you're " + planned.group(1)
    else:
        wanted = re.match(r"^i\s+(?:want|need|plan)\s+to\s+(\S.*)$", flat, re.I)
        if not wanted:
            return ""
        body = "you want to " + wanted.group(1)
    body = _tidy_words(you(body))
    return body[:1].upper() + body[1:]

def _tidy_words(text):
    """A country or a month keeps its capital: "going to portugal in june" -> "Portugal in
    June". The same tidy the places in the fact store get, so a plan reads like a sentence."""
    ORDINARY = ("a", "an", "the", "my", "your", "our", "his", "her", "their", "this", "that")
    # A name that is also an everyday word needs the sentence to say it is a place: "roast
    # turkey" is dinner and "going to turkey" is a trip, "china plates" are crockery.
    BOTH = frozenset(("turkey", "china", "bath", "hull", "york", "goa"))
    TRAVEL = ("to", "in", "from", "at", "near", "visit", "visiting", "into")

    def keep(match):
        word = match.group(0)
        if word not in extract.COUNTRIES and word not in extract.MONTHS and word not in PLACES:
            return word
        before = text[:match.start()].split()
        if before and before[-1].lower() in ORDINARY:
            return word
        if word in BOTH and not (before and before[-1].lower() in TRAVEL):
            return word
        return word[:1].upper() + word[1:]
    return re.sub(r"[a-z]+", keep, text)

def _a_thing(name):
    """Whether the thing we were on is a phrase a person would say, and not a verb.

    The subject is cut out of the words of the line, so a verb or an adjective reaches it:
    "im getting married in june" gave "the married", "im learning spanish" gave "the spanish".
    A recap that names one of those reads like a machine reading a label back, so the sentence
    is said without the subject instead.
    """
    words = str(name or "").split()
    if not words:
        return False
    head = words[-1].lower().strip(".,;:!?")
    if not head:
        return False
    if head.endswith(("ing", "ed", "ish")):
        return False
    # "and again" left a subject of "again": a filler word is not a thing to be on either.
    return head not in thread.QUALITY and head not in thread.NON_NOUN

THING_POINTER = frozenset(
    "the a an my your our their his her its it this that of on in at for to with about".split())

def _says_the_thing(said, thing):
    """Whether the line about to be quoted already names the thing the recap would name.

    A recap says the subject once. "We were on the pressure - you asked how you top it up" says
    it twice, once badly, so the line itself is said instead. The test is the words, not the
    speaker: a thing is named again when one of its own words is in the line, in any order.
    """
    named = {w for w in re.findall(r"[a-z']+", str(thing or "").lower()) if w not in THING_POINTER}
    return bool(named) and bool(named & set(re.findall(r"[a-z']+", str(said or "").lower())))

def _a_description(thing):
    """Whether the thing is a description the store gave an article to, not a name.

    "the pressure" was cut out of "my boiler keeps losing pressure": it is a part of the thing we
    were on, and it reads like a label. "Edinburgh", "my sister" and "the boiler" stand on their
    own - a name or what the person called it - so a recap can be on one.
    """
    words = str(thing or "").strip().split()
    if len(words) < 2:
        return False
    return words[0].lower() in ("the", "a", "an")

def _the_fixed_fact(memory):
    """The fact a correction just fixed, as the store keeps it, or None.

    A recap quoted the correcting line itself ("you said actually make that 800") because that
    is what the last line was, while the store had already applied it. What the chat is on is
    the corrected fact, so that is what the recap says.
    """
    fixed = memory.get("correction") if isinstance(memory, dict) else None
    if not isinstance(fixed, dict):
        return None
    key = str(fixed.get("key") or "").strip()
    value = str(fixed.get("value") or "").strip()
    said = str(fixed.get("said") or "").strip()
    if not key or not value:
        return None
    if said and last_user(memory).strip().lower() != said.lower():
        return None  # an older correction: the line after it is the one we were on
    sentence = _fact_reply(memory, " ".join(_slot_words(key, memory).split()), key=key)
    sentence = str(sentence or "").strip()
    if not sentence.startswith(("Your ", "You ")):
        return None
    return sentence[:1].lower() + sentence[1:].rstrip(".")

def _the_line_named(memory, low):
    """The earlier line of theirs that the thing asked about is in, or "" when none is.

    "what was i saying about the deposit" after "im saving for a deposit" and "my rent is 800"
    asks about the deposit, and saying the rent back answers a question nobody asked. A pronoun
    names no thing ("what was i saying about it"), so it names nothing to look for and the last
    line stays the answer.
    """
    about = re.search(r"\babout\s+(.*)$", low or "")
    if not about:
        return ""
    words = content(about.group(1))
    if not words:
        return ""
    for seen in reversed(recent(memory, 8)):
        line = seen.get("user") or ""
        if not line or _about_this_chat(line):
            continue
        have = set(content(line))
        if have and all(_alike(word, have) for word in words):
            return line
    return ""

def _topic_reply(memory, low, again=False):
    """Where we were, said back in a sentence: the thing, and what was asked about it.

    The line is never quoted: "we were on this: \"...\"" makes the person read their own
    words twice. `thread.restate` puts the last ask in the second person and fits the
    grammar, and a turn that only asks about the chat is not the thing we were on.

    `again` says the person asked for a thing they know they said ("what am i making again").
    Their own word for it comes off the line before it reaches here, so it is read from the
    line as typed and passed in.
    """
    record = current(memory)
    real = _last_real(memory)
    if real:
        record = {"text": real}
    last = last_user(memory)
    # The thing the line names decides which line is said back: "what was i saying about the
    # deposit" after a rent line is about the deposit, not about the rent. Where the thing is
    # not in any line they gave, the last line is still the honest answer to "what were we on".
    on_that_line = _the_line_named(memory, low)
    said_again = (_the_fixed_fact(memory)
                  or (thread.restate(on_that_line) if on_that_line else "")
                  or thread.last_said(memory, _about_this_chat))
    if said_again and len(said_again.split()) < 2:
        said_again = None  # "and again" is not a thing the chat was on
    if "yesterday" in low:
        said = (" In this one, you last said " + said_again + "." if said_again else "")
        return "I don't keep yesterday's chat, sorry — each conversation starts fresh for me." + said
    if _names_its_thing(low):
        # "what was i saying about pasta earlier": the thing is named, so the chat can have moved
        # on since and the last turn is not the answer to it; the line that names the thing is.
        # Nothing found about a thing the store keeps as a fact ("about my city" beside "i live
        # in leeds") is not a thing to deny, so the ordinary paths speak for it instead.
        by_name = _recall_reply(memory, low, spoken=True)
        if by_name and not _a_denial(by_name):
            return by_name
        # A miss is never a denial. The chat may have said the thing in other words - "about my
        # hours" beside "i work nights", "about music" beside "i like jazz" - and telling the
        # person the chat has nothing about it is a claim about the conversation that is false.
        # So a miss falls through to the answers this line got before the reader existed.
    named = NAMED_ACTIVITY.search(low or "")
    carried = _activity_line(memory) if ACTIVITY_ASK.search(low or "") else ""
    if not carried and named and again:
        carried = _the_making_line_they_said(memory)
    if not carried and named:
        # "what was i cooking?" after a chat about a dishwasher asks for the cooking line; the
        # topic we were on is a different thing, and naming it does not answer the ask.
        return None
    if carried:
        said_plan = _recap(carried) or ("You said: \"" + _trim(carried) + "\"")
        said_plan = said_plan.rstrip(".") + "."
        return _vary([said_plan + " Want to carry on with it?",
                      said_plan + " Where did you get to with it?",
                      said_plan], memory)
    thing = thread.about(memory, _about_this_chat)
    if not _a_thing(thing):
        thing = None
    ask = "" if on_that_line else thread.last_ask(
        memory, _about_this_chat,
        not_before=thread.topic_index(memory, _about_this_chat))
    # The subject and the ask are different halves of the same sentence, and neither quotes the
    # line: "We were on Edinburgh - you asked how many days I would give it". A recap that held
    # the subject back because the last line happened to name it too lost the topic and said
    # only "You asked how many days I would give it", which is half an answer to "remind me what
    # we've covered".
    #
    # A description the store had to give an article to ("the pressure", out of "my boiler keeps
    # losing pressure") is the one subject not worth naming again when the line already says it:
    # the reason we were on it is that it is the person's boiler, and their own words say so. A
    # line that is still on the screen names its own subject, so it is said as it is and the
    # thing cut from its words is left out.
    if thing and ask and not (_a_description(thing) and (
            _says_the_thing(said_again, thing) or _says_the_thing(ask, thing))):
        return _vary(["We were on " + thing + " — you asked " + ask + ". Want to carry on?",
                      "Still on " + thing + ": you asked " + ask + ".",
                      "The last thing we got into was " + thing + ", and you asked " + ask + "."],
                     memory)
    if ask and said_again:
        return _vary(["You said " + said_again + ". You asked " + ask + ". Want to carry on?",
                      said_again[:1].upper() + said_again[1:] + " - and you asked " + ask
                      + ". Want to carry on?"], memory)
    if ask:
        return _vary(["You asked " + ask + ". Want to carry on?",
                      "You were asking " + ask + "."], memory)
    if said_again:
        return _vary(["You said " + said_again + ". Want to carry on?",
                      "You last said " + said_again + ".",
                      "You'd told me " + said_again + "."], memory)
    if thing:
        return _vary(["We were on " + thing + ".", "Still " + thing + "."], memory)
    if record and not thread.thin(record["text"]) and thread.carries_subject(record["text"]):
        plain = thread.restate(record["text"])
        if plain and _a_thing(plain):
            return "We were on " + plain + "."
    asked_of_me = _the_last_ask_about_the_bot(memory)
    if asked_of_me:
        return _vary(["You asked " + asked_of_me + " - that is all we have been into so far. "
                      "What else is on your mind?",
                      "So far you have asked " + asked_of_me + ". Tell me something of your own "
                      "and I will keep it.",
                      "You asked " + asked_of_me + ". That is about all so far - what else are "
                      "you wondering about?"], memory)
    # Nothing but "hi", "ok", "lol" so far: there is no subject yet, and naming one would be
    # a lie. `last` is deliberately not used here — a thin line is not something to carry on.
    return _vary(NOTHING_STARTED, memory)

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

def _asked_reply(memory):
    """'What did I just ask you?' — their last question, said again in their words."""
    ask = thread.last_ask(memory, _about_this_chat)
    if ask:
        return "You asked " + ask + "."
    said = thread.last_said(memory, _about_this_chat)
    if said:
        return "You didn't ask me anything — you said " + said + "."
    # A chat whose only line so far is a question about the bot ("are you a real person") has no
    # subject of theirs for either reader above, so both pass - but they did ask something, and
    # "you haven't asked me anything yet" denies the question that is still on the screen. The
    # question about the bot is said back in their own words, which is what the chat has covered.
    asked_of_me = _the_last_ask_about_the_bot(memory)
    if asked_of_me:
        return "You asked " + asked_of_me + "."
    return "You haven't asked me anything yet."

SMALL_TALK_ONLY = frozenset("""hi hello hey morning afternoon evening night thanks thank cheers
bye goodbye ok okay cool nice great good fine yeah yes no nah lol haha hmm well anyway
brilliant lovely""".split())

SUMMARY_FILLER = frozenset("""you your yours i me my mine and so but it its it's is was are were
be been am do did does have has had to of in on at for with that this these those the a an
too also just really very quite still now then there here""".split())

def _last_told(memory):
    """What they last told you, in their own words, or "" when the line was a question or small talk.

    A line that leaves no fact behind is still something they told you: "my parents evening went
    well" keeps nothing to recall, and a summary that skips it answers "you haven't told me about
    yourself" to someone who just did.
    """
    record = current(memory)
    # The topic is often the question itself ("what do you know about me"), so the lines before it
    # are tried in turn and the first one that said something is the one said back.
    candidates = [str((record or {}).get("text") or "")]
    candidates += [str(line or "") for line in reversed(last_user(memory, 3))]
    for text in candidates:
        if recall.ask(text) == "me":
            # A question about what the bot holds is not something they told it: "anything
            # you've learned about me" was said back as "you said anything you have learned
            # about you" in the summary of a chat that had three real facts in it.
            continue
        phrase = _told_phrase(text)
        if phrase:
            return phrase
    return ""

NAME_SAID = re.compile(r"\b(?:called|named|name(?:'s)? is|goes by)\s+([A-Za-z][\w'\u2019-]*)", re.I)

NOT_A_NAME = frozenset("""a an the that this it him her them me you us someone something
somebody anyone anybody everyone nobody""".split())

def _as_repaired(word):
    """The word as the reader repairs it: the repair is right for a typo and wrong for a name."""
    return fix_typo(str(word or "").lower()) or str(word or "")

def _with_the_name(said, raw):
    """The same line with a name put back as they spelt it.

    The reader's repairs are for typos, and a name is not one: "ann" is repaired to "an" in every
    line, so "my mum is called ann" came back as "your mum is called an".
    """
    names = []
    for match in NAME_SAID.finditer(raw or ""):
        name = match.group(1).strip("'\u2019-")
        if name.lower() in NOT_A_NAME or len(name) < 2 or name in names:
            continue
        names.append(name)
    if not names or not said:
        return said
    words = said.split()
    for name in names:
        spelled = name[:1].upper() + name[1:]
        wanted = {name.lower(), _as_repaired(name)}
        for at, word in enumerate(words):
            core = word.strip(".,!?;:")
            if core.lower() in wanted:
                words[at] = word.replace(core, spelled)
                break
    return " ".join(words)

SAY_BACK_VAGUE_TAIL = frozenset("""haha hehe hahaha lol lmao hmm ah oh eh yeah yep nope ok okay
    aye mate hun x xx xxx""".split())

SAY_BACK_CORRECTION = re.compile(r"^you (?:meant|mean)\b|\bno wait\b|^you said (?:actually|sorry)\b")

SAY_BACK_VAGUE = frozenset("""
    there here it that this them those these one ones thing things stuff
    like loves love hate hates want wants need needs think thinking thought
    going get got getting be been being said say told tell
""".split())

DENIAL_LINE = re.compile(r"^(?:no|nah|nope)\b.{0,40}\b(?:isnt|isn't|wasnt|wasn't|not)\b"
                         r"|\bno (?:wait|actually)\b|\bsorry,? (?:i )?(?:mean|meant)\b"
                         # "actually hes called jake", "sorry, his name is sam": the line says the
                         # right name for somebody the chat already named, so it is a correction
                         # of that line rather than a new fact about a new person.
                         r"|^(?:actually|sorry|no|nope|wait)\b[^?]{0,40}?\b(?:called|named|"
                         r"name is)\b")

A_NEW_PERSON = re.compile(r"\b(?:my|our|your)\s+\w+")

def _reads_as_a_correction(line):
    """True when the line takes something back rather than stating something new."""
    text = " ".join(str(line or "").lower().split())
    if not text:
        return False
    if DENIAL_LINE.search(text) and A_NEW_PERSON.search(text) and not re.search(
            r"\b(?:isnt|isn't|wasnt|wasn't|not)\b", text):
        return bool(extract.extract(line).get("correction"))
    return bool(DENIAL_LINE.search(text)) or bool(extract.extract(line).get("correction"))

def _lines_that_moved(memory):
    """The lines whose fact a later line put again, with a different value.

    "im 34" / "im 35 now" leaves both lines in the log, and the store has the 35. A summary that
    says the 35 and then "you said you are 34" hands back the value they just replaced. The same
    for a correction: "my budget is 400" / "sorry, i meant 500".

    A value the store recorded with a *frame* is a detail of the fact, not a new value for it:
    "im a nurse" / "i work nights" writes the job key ("nights", frame "work"), and the nurse is
    still what they told the bot. Those lines are kept.
    """
    entries = [entry for entry in (memory.get("facts_log") or [])
               if isinstance(entry, dict) and entry.get("key")]
    framed = {(str(entry["key"])[:-len("_frame")], entry.get("turn")) for entry in entries
              if str(entry["key"]).endswith("_frame")}
    moved = set()
    last = {}
    for entry in entries:
        key = str(entry["key"])
        # A list is a thing that grows ("plans", "pets"): a later line adds one, it does not
        # replace the old one, so nothing on those lines has moved.
        if key.endswith("_frame") or isinstance(entry.get("value"), (list, dict)):
            continue
        text = " ".join(str(entry.get("text") or "").lower().split())
        older = last.get(key)
        if older and older != text:
            if _reads_as_a_correction(entry.get("text")) or (key, entry.get("turn")) not in framed:
                moved.add(older)
        last[key] = text
    return moved

# The facts the summary above says for itself. A key named here is not said back as the line it
# came in on, because the summary already says it better - so a key here with no branch in
# `_summary_reply` is a fact that reaches no reply at all. `tests/test_a_fact_reaches_the_recap.py`
# walks this set and asks the recap for each, which is the check that keeps the two in step.
SUMMARY_KEYS = frozenset(("name", "age", "job", "city", "shift", "workplace", "from", "pets",
                          "kids", "tastes", "allergies", "diet", "condition", "budget",
                          "plan", "plans"))

def _the_summary_already_says(memory, flat):
    """True when every fact the line gave is one the summary says, at the value it holds."""
    known = user(memory)
    keys = set()
    for entry in memory.get("facts_log") or []:
        if not isinstance(entry, dict) or not entry.get("key"):
            continue
        if " ".join(str(entry.get("text") or "").lower().split()) != flat:
            continue
        key = entry["key"]
        then, now = entry.get("value"), known.get(key)
        if isinstance(now, (list, dict)) or isinstance(then, (list, dict)):
            continue
        if then is None or now is None or str(then).lower() != str(now).lower():
            return False
        keys.add(key)
    return bool(keys) and keys <= SUMMARY_KEYS

def _safety_lines(memory):
    """The lines the bot answered with care: a crisis.

    "what do you know about me" is the last ask to answer with an inventory in a chat like that:
    "you said you keep thinking about ending it" turns the worst thing they said into a bullet
    in a list of things kept on file. A death in the family is not that: people do want it
    remembered, and main already said it back.
    """
    out = set()
    for turn in memory.get("turns") or []:
        if not isinstance(turn, dict):
            continue
        if turn.get("module") not in ("safety",):
            continue
        out.add(" ".join(str(turn.get("user") or "").lower().split()))
    return out

CHANGE_WORD = re.compile(r"\b(?:now|new|again|instead|anymore|any more|no longer|these days|"
                         r"moved to|switched to|changed to)\b", re.I)

NEGATIVE_LINE = re.compile(r"\b(?:i|we)\s*(?:dont|don't|do not|didnt|didn't|did not|cant|can't|"
                            r"cannot|never|havent|haven't|have not|am not|im not|i'm not|wasnt|"
                            r"wasn't|was not|wont|won't|will not)\b", re.I)

AN_ATTITUDE = re.compile(r"\b(?:i|we)\s*(?:dont|don't|do not|didnt|didn't|did not)\s+"
                          r"(?:really\s+|actually\s+)?(?:like|love|enjoy|want|fancy|prefer|hate|"
                          r"eat|drink|need|mind|watch|read|believe|trust|care)\b", re.I)

def _shape(line):
    """The frame a line about the person is written in: "im", "i have", "i dont"."""
    words = str(line or "").split()
    if not words:
        return ""
    if words[0] in ("im", "i'm", "ive", "i've", "iam"):
        return words[0]
    if len(words) > 1 and words[0] == "i" and words[1] in (
            "am", "have", "got", "dont", "do", "cant", "cannot", "was", "were", "live", "work"):
        return " ".join(words[:2])
    return words[0]

def _out_of_date_lines(memory):
    """The lines a later line changed, without the store having a key to record it under.

    "im single" / "im married now" leaves no fact behind - there is no key for it - so the log
    says nothing and both lines would be walked back, the old state beside the new one. A line
    that left a fact behind is left to the store's own value, so "im allergic to nuts" keeps its
    line even after "im vegetarian now".
    """
    lines = [" ".join(str(line or "").lower().split()) for line in last_user(memory, 8)]
    logged = {" ".join(str(entry.get("text") or "").lower().split())
              for entry in (memory.get("facts_log") or []) if isinstance(entry, dict)}
    out = set()
    for index, line in enumerate(lines):
        if not CHANGE_WORD.search(line):
            continue
        changed = {word for word in re.findall(r"[a-z0-9']+", line)
                   if len(word) > 2 and word not in STOPWORDS
                   and not CHANGE_WORD.fullmatch(word)}
        for older in lines[:index]:
            if older in logged:
                continue
            knew = {word for word in re.findall(r"[a-z0-9']+", older)
                    if len(word) > 2 and word not in STOPWORDS}
            if changed & knew or _shape(older) == _shape(line):
                out.add(older)
    # A negative line and a later line where they do the thing: the same thing compared on its
    # stem, so "drive" and "driving" are one word. Only a statement of theirs counts - a question
    # ("do you like fish?") takes nothing back - and an attitude is not a thing they can undo.
    for index, older in enumerate(lines):
        if not NEGATIVE_LINE.search(older) or AN_ATTITUDE.search(older):
            continue
        knew = [_root(word) for word in re.findall(r"[a-z']+", older)
                if len(word) > 2 and word not in STOPWORDS]
        for later in lines[index + 1:]:
            if (not re.match(r"^(?:i|ive|i've|im|i'm|we|weve) ", later)
                    or NEGATIVE_LINE.search(later) or later.endswith("?")):
                continue
            there = [_root(word) for word in re.findall(r"[a-z']+", later)
                     if len(word) > 2 and word not in STOPWORDS]
            if any(_one_word(a, b) for a in knew for b in there):
                out.add(older)
                break
    return out

def _root(word):
    """The same word with its ending taken off: drive and driving are one thing."""
    word = str(word or "").lower().strip("'")
    for suffix in ("ing", "ers", "er", "ed", "es", "s", "ly"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[:-len(suffix)]
            break
    if len(word) > 3 and word[-1] == word[-2] and word[-1] not in "aeiou":
        word = word[:-1]  # swimming, stopped: the doubling is the ending, not the word
    if len(word) > 3 and word.endswith("e"):
        word = word[:-1]
    return word

def _one_word(first, second):
    """Whether two words are the same thing said with a different ending: drive, driving."""
    return first == second or (_root(first) == _root(second) and len(_root(first)) >= 3)

SELF_JUDGEMENT = re.compile(
    r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|honestly|tbh)\W+)*"
    r"(?:i'?m|i\s+am|im|i\s+feel(?:\s+like)?|i\s+was(?:\s+being)?)\b"
    # "im such an idiot", "i am a complete muppet", "i feel like a rubbish mum"
    r"(?:\s+(?:being|such|a|an|the|complete|total|absolute|right|proper|bit\s+of\s+a))*\s+"
    r"(?:idiot|muppet|moron|fool|clown|disaster|loser|failure|letdown|let\s?down|"
    r"embarrassment|disappointment|waste\s+of\s+space|useless|worthless|hopeless|"
    r"no\s+good|not\s+good\s+enough|"
    r"(?:rubbish|bad|terrible|awful|useless|hopeless)\s+(?:mum|mom|mother|dad|father|parent|"
    r"husband|wife|partner|friend|person|son|daughter))"
    # "useless at everything i try" judges the whole person; "useless at maths" rates a skill
    r"(?:\s+(?:at|with|in)\s+(?:everything|anything|life|myself|all\s+of\s+it|this|that)\b"
    r"(?:\s+\w+){0,4})?"
    r"\s*[.!]*$"
    # "what an idiot i am": the same judgement said the other way round
    r"|^\W*what\s+an?\s+(?:idiot|muppet|moron|fool|disaster)\s+i\s+(?:am|was|have\s+been)\b"
    # "i hate myself" is the same judgement, and only the whole line is it
    r"|^\W*i\s+hate\s+myself\b"
    # what they say they always do: "i always mess things up", "i keep ruining everything". An
    # object of their own ("i keep messing up the recipe") is a thing that happened, not a
    # verdict on the person, so only the whole of it with no thing named is caught here.
    r"|^\W*i\s+(?:always|constantly|just|keep|keeps)\s+"
    r"(?:mess(?:es|ing)?\s+(?:things|it|everything)?\s*up"
    r"|ruin(?:s|ing)?\s+(?:things|it|everything)"
    r"|screw(?:s|ing)?\s+(?:things|it|everything)\s+up)\s*[.!]*$", re.I)

SELF_WORST = re.compile(
    r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|honestly)\W+)*"
    r"(?:i'?m|i\s+am|im)\s+(?:the\s+|literally\s+|such\s+|an?\s+)*(?:worst|worse)\s*"
    r"[.!]*$", re.I)

def _judging_themselves(line):
    """Whether the line is the person rating themselves rather than telling the bot a fact."""
    said = " ".join(str(line or "").lower().split())
    return bool(said) and bool(SELF_JUDGEMENT.match(said) or SELF_WORST.match(said))

def _recent_told(memory, limit=3):
    """The last few things they told you, newest first, in their own words.

    The store keeps the facts it has a key for, and the rest is only what they said: "i dont
    drive" leaves no fact behind, so the line is the whole of it. Walking back over the lines
    they typed keeps those for more than one turn.
    """
    out, seen = [], set()
    newest = ""
    # A chat the bot has answered with care gets no inventory: the summary of a crisis is not a
    # list of what the bot has on file.
    if _topics.in_a_safety_thread(memory):
        return out
    moved = _lines_that_moved(memory)
    care = _safety_lines(memory)
    record = current(memory)
    # The lines they typed, newest first. The record the chat is on is the line it opened with, so
    # it is only the whole history when nothing else is kept.
    lines = [str(line or "") for line in reversed(last_user(memory, 8))]
    if not lines:
        lines = [str((record or {}).get("text") or "")]
    newest = " ".join(lines[0].lower().split())
    for index, line in enumerate(lines):
        flat = " ".join(str(line or "").lower().split())
        # A line whose fact the store now holds a different value for is not said: after
        # "im 34" / "no i mean 43" the summary has the 43, and saying the 34 beside it is the
        # bot repeating a mistake the person already put right.
        if flat in moved or flat in _out_of_date_lines(memory):
            continue
        # A line the bot answered with care is not a fact about the person: "you said you keep
        # thinking about ending it" is the worst thing they said, quoted back in a list. A line
        # where they are hard on themselves is the same: the recap is no place to hand back "you
        # are such an idiot" in the bot's own voice.
        if flat in care or _judging_themselves(flat):
            continue
        # A correction takes back what came before it, so the walk stops there: everything older
        # is what they put right, and the store holds whatever the correction left. A figure put
        # up for something the store has no fact for puts nothing right - "the table is booked for
        # 10" then "actually just 8" left the store empty - so that line takes nothing back, and
        # stopping on it made the recap deny the whole chat ("Not much yet - you haven't told me
        # about yourself") one turn after they had told the bot about the table.
        if _reads_as_a_correction(line):
            if not _a_figure_the_store_could_not_keep(line, memory):
                break
            continue
        # Half of the question they just asked is not something they told us: "whats the capital
        # of australia" then "and the weather there in june" has no verb and nobody in it, and
        # the summary that listed it reported a fact they never gave.
        if ack.the_rest_of_a_question(
                line, lines[index + 1] if index + 1 < len(lines) else ""):
            continue
        if A_CLAIM_OF_TELLING.match(flat) and not extract.extract(line):
            # "i told you already" is about the telling, not a fact about the person: said back in
            # a summary it reported "you said you told you already" as something they had told.
            continue
        if recall.ask(flat) == "me":
            # A question about what the bot holds is not something they told it: "anything
            # you've learned about me" came back as "you said anything you have learned about
            # you" in the summary of a chat whose facts were all asked back.
            continue
        if _the_summary_already_says(memory, flat):
            continue
        phrase = " ".join(_told_phrase(extract.no_tone(line)).split())
        while phrase and phrase.split()[-1].lower() in SAY_BACK_VAGUE_TAIL:
            phrase = " ".join(phrase.split()[:-1])
        # "can not swim" reads like a translation; the contraction is how a person writes it.
        phrase = phrase.replace("can not", "cannot")
        words = {w for w in _summary_words(phrase)}
        if not words or words <= SAY_BACK_VAGUE or SAY_BACK_CORRECTION.search(phrase):
            continue
        key = phrase.lower()
        if key in seen:
            continue
        seen.add(key)
        # The line the chat is on is said only if it is what the facts above are about; an older
        # line is a different thing they told the bot, and the topic guard does not apply to it.
        out.append((phrase, flat == newest))
        if len(out) >= limit:
            break
    return out

AGREEMENT_ONLY = frozenset("""
know knew knows knowing agree agreed guess suppose supposed admit honestly seriously swear trust
believe promise really truly sure right true yes yeah no nah mean means meant said say saying
tell told think thought feel felt do did does done that this it everything anything much
""".split())

def _all_about_the_bot(memory):
    """Whether every line they typed was a question about the bot itself.

    "so youre claude" / "what do you know about me" has no subject of its own to name, and the
    reading that names one said "so far it's been the claude" - the bot's own name offered as
    the thing the person is into. The composer already has one reading of "this is about you",
    so it is asked rather than a second list of words kept here.
    """
    from ..compose.fallback import about_the_bot
    lines = [str(line or "").strip() for line in last_user(memory, 8)]
    lines = [line for line in lines if line]
    if not lines:
        return False
    return all(about_the_bot(" ".join(line.lower().split())) for line in lines)

def _a_figure_the_store_could_not_keep(line, memory):
    """True when the line is only a new figure for something, and no fact moved for it.

    The store records what a correction moved under `memory["correction"]`, so no key there means
    nothing was put right: "the table is booked for 10" then "actually just 8" named a thing the
    store keeps no fact for, and the line before it is still true. Only a figure counts, and only
    when the line is nothing but one with a correction word in front, so a denial ("i dont
    drive") is still the take-back it was.
    """
    if (memory.get("correction") or {}).get("key"):
        return False
    found = extract.extract(line).get("correction") or {}
    value = " ".join(str(found.get("to") or "").split())
    return bool(value) and bool(ANY_NUMBER.fullmatch(value))

def _the_thing_the_chat_is_on(memory):
    """The phrase to name in place of facts, or "" when the chat holds nothing of the person's.

    Only when the line it comes from is a question or something about them ("how do i clean the
    oven", "whats the capital of australia"): a chat whose only line is about the bot itself has
    no subject of theirs to name, and naming one said "so far it's been the claude".
    """
    if _all_about_the_bot(memory):
        return ""
    record = current(memory) or {}
    text = " ".join(str(record.get("text") or "").split()).lower()
    if not text:
        return ""
    theirs = re.search(r"\b(?:i|im|i'm|my|we|our|me|us|mine)\b", text)
    # A question put to the bot is not a subject of theirs either: "are you a real person" is
    # about the bot, and naming it said "so far it's been the real person".
    to_the_bot = re.search(r"\b(?:you|your|youre|you're|u)\b", text)
    if not (theirs or (_asks(text) and not to_the_bot)):
        return ""
    return " ".join(str(_about_the_chat(memory) or "").split())

def _a_fact_of_its_own(clause):
    """Whether a clause beside a judgement says something, rather than agreeing with the verdict."""
    words = {word.strip(".,!?;:'\"") for word in str(clause).lower().split()} - SUMMARY_FILLER
    return bool(words) and not words <= AGREEMENT_ONLY

def _told_phrase(text):
    """One line said back inside a sentence, or "" when it is not something they told you."""
    if not text:
        return ""
    reading = understand(text, {})
    # A question or an ask is not something they told you: "any tips for my parents evening" is
    # a request, and "you said any tips for your parents evening" is not a sentence.
    if (reading.get("kind") in ("question", "greeting", "thanks")
            or reading.get("intent") in ("question", "request", "greeting", "thanks")
            # A feeling is how they are, not a fact they told us. It slipped through on the
            # lines whose feeling is carried by a thing acting on the speaker - "work is
            # stressing me out" has no "i" in it, so the whole line was read back as news:
            # "Got it - your job is stressing you out." The engine now reads those as feelings
            # (kinds.py, ACTS_ON_THE_SPEAKER), and this is the store honouring the reading.
            or reading.get("intent") == "feeling"
            or reading.get("asks")):
        return ""

    if reading.get("about_bot"):
        return ""
    if extract.is_a_judgement(text):
        # A judgement about themselves is how they feel, not something they told us: "you said
        # you are a bad mum" is the store agreeing with them. A line can carry a fact beside the
        # judgement though - "im a terrible cook, i burned the roast again" - so the clause that
        # is not a judgement is the one said back, and a line that is all judgement keeps nothing.
        rest = [part.strip() for part in re.split(r"\s*(?:[,;.]|\bbut\b|\band\b)\s*", text)
                if part and part.strip()]
        text = next((part for part in rest
                     if not extract.is_a_judgement(part) and _a_fact_of_its_own(part)), "")
        if not text:
            return ""
    said = _with_the_name(thread.restate(without_filler(text)) or "", text)
    words = [word for word in said.split() if word.strip(".,!?;:")]
    body = {word.strip(".,!?;:").lower() for word in words} - SUMMARY_FILLER
    if not body or body <= SMALL_TALK_ONLY or len(words) > 14:
        return ""
    return " ".join(words)

def _expanded(text):
    """A line with its contractions written out: "you're veg" and "you are veg" are the same line."""
    text = str(text).lower().replace("\u2019", "'")
    for pattern, word in ((r"n't\b", " not"), (r"'re\b", " are"), (r"'ve\b", " have"),
                          (r"'ll\b", " will"), (r"'d\b", " would"),
                          (r"\bi'm\b", "i am"), (r"\bim\b", "i am"),
                          (r"\bive\b", "i have"), (r"\byoure\b", "you are"),
                          (r"\bdont\b", "do not"), (r"\bdoesnt\b", "does not"),
                          (r"\bim\b", "i am")):
        text = re.sub(pattern, word, text)
    return text

NUMBER_AS_A_WORD = dict(zip(
    "1 2 3 4 5 6 7 8 9 10 11 12 20 30 40 50 100".split(),
    "one two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty "
    "hundred".split()))

def _a_judgement_was_said(memory):
    """Whether a line they said in this chat judged themselves rather than stating a fact.

    It is read from the history the runtime keeps (memory["turns"]) rather than from a flag of
    its own, so there is no second copy of the fact to keep in step with the store: a judgement
    is never filed, and the line they typed is still there.
    """
    for turn in (memory.get("turns") or []):
        if not isinstance(turn, dict):
            continue
        line = turn.get("user")
        if isinstance(line, str) and extract.is_a_judgement(line):
            return True
    return False

FACT_FRAME_WORDS = frozenset("""i im ive the a an my our at with for to of in on and
got get gotten job jobs start started starting new began""".split())

def _plain_words(text):
    """The words of a line as they are, without the length rule the summary meaning applies."""
    return set(re.findall(r"[a-z0-9']+", str(text or "").lower().replace("-", " ")))

def _says_nothing_new(phrase, told_words, body_words):
    """Whether the line is the fact above, in the person's own words, and nothing more."""
    body = _summary_words(body_words)
    if told_words <= body:
        return True
    # The short words a summary drops are sometimes the whole of the thing shared: "co-op" in the
    # fact and "co op" in the line are the same place, and both halves are two letters long, so the
    # place is compared on the words as they are.
    rest = _plain_words(phrase) - FACT_FRAME_WORDS
    if not rest:
        return False
    return rest <= _plain_words(body_words)

def _summary_words(text):
    """The words that carry the meaning of a line, for telling a repeat from a new thing."""
    words = set()
    for word in _expanded(text).replace(";", " ").replace(",", " ").split():
        word = stem(word.strip(".,!?;:'"))
        word = NUMBER_AS_A_WORD.get(word, word)
        # A figure is a fact in its own right ("im 41", "my son is 8"), so it is kept whatever
        # its length: the words around it are what the length rule is for.
        if not word.isdigit():
            # The store keeps the plain word, so the slang has to fold the same way here: "veggie"
            # in the line and "vegetarian" in the fact above are the same fact, said twice.
            word = stem(extract.DIET_NAMES.get(word, word))
        if word and (word.isdigit() or len(word) > 2) and word not in SUMMARY_FILLER \
                and word not in SMALL_TALK_ONLY:
            words.add(word)
    return words

def _already_said(words, said):
    """Whether the facts above already say this: "allergy" and "allergic" are the same word here."""
    said = _summary_words(said)
    if not said:
        return False  # nothing above says anything, so this is new
    if not words:
        return True
    for word in words:
        same = [other for other in said
                if other == word or (len(word) >= 4 and len(other) >= 4
                                     and other[:4] == word[:4])]
        said.difference_update(same)
    return len(said) < max(1, len(words) // 2)

TASTE_ASK = ASKS_ABOUT_A_TASTE

_TASTE_LEFT = TASTE_ASKED_ABOUT

def _taste_reply(memory, low):
    """The taste they have already said, said back as the answer to "do i like fish?".

    Returns None when the store has no taste about that thing, so a question about something
    they have never mentioned is left to whoever can answer it.
    """
    left = _TASTE_LEFT.split(str(low or ""), maxsplit=1)
    asked = left[-1] if len(left) > 1 else ""
    asked = re.sub(r"\b(?:again|still|actually|really|now|any ?more)\b", "", asked).strip(" ?!.,")
    if not asked:
        return None
    wanted = [stem(word) for word in content(asked)]
    if not wanted:
        return None
    for taste in reversed(user(memory).get("tastes") or []):
        thing = str(taste.get("thing") or "").lower()
        bare = thing[5:] if thing.startswith("your ") else thing
        said = [stem(word) for word in content(bare)]
        if not said:
            continue
        if sum(1 for word in wanted if word in said) < max(1, len(wanted) - 1):
            continue
        how = str(taste.get("how") or "yes")
        # Said back with the possessive it was kept in: "do i like my job?" is "you like your
        # job", not "you like job".
        named = bare if not thing[5:].strip() or not thing.lower().startswith("your ") else thing
        if how == "no":
            return "You don't, you told me you're not keen on " + named + "."
        if how == "unsure":
            return "You weren't sure about " + named + ", that's all you've said."
        return "You do, you told me you like " + named + "."
    return None

def _tastes_said(memory):
    """"what do i like?" as the short list of tastes, not the whole summary of what is known.

    Only the tastes are asked for, so only the tastes are said. A store with none answers
    nothing at all and the question goes to whoever can answer it, rather than to a summary that
    would read as a dodge.
    """
    liked, other = [], []
    for taste in user(memory).get("tastes") or []:
        thing = str((taste or {}).get("thing") or "").strip()
        if not thing:
            continue
        how = str(taste.get("how") or "yes")
        if how == "no":
            other.append("You're not keen on " + thing + ".")
        elif how == "unsure":
            other.append("You're not sure about " + thing + ".")
        else:
            liked.append(thing)
    said = []
    if liked:
        joined = liked[0] if len(liked) == 1 else ", ".join(liked[:-1]) + " and " + liked[-1]
        said.append("You like " + joined + ".")
    said.extend(other)
    return " ".join(said) if said else None

AGE_SAID_IN_WORDS = re.compile(
    r"\b(?:(?:i(?:'m| am)|im|you(?:'re| are)|youre|we(?:'re| are)|were|they(?:'re| are)))\s+"
    r"(?:\d{1,3}|a hundred|one|two|three|four|five|six|seven|eight|nine|"
    r"ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety)\b", re.I)

def _without_the_age(line):
    """The line with the age taken out of it: "you're 41 and you're training" -> "you're training"."""
    without = AGE_SAID_IN_WORDS.sub("", str(line or ""), count=1).strip(" .,;:!?-")
    return re.sub(r"^(?:and|also|plus)\s+", "", without, flags=re.I).strip()

def _the_words_of_a_fact(value):
    """The words a stored fact is made of, whatever shape the store keeps it in."""
    if isinstance(value, bool):
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_the_words_of_a_fact(part) for part in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_the_words_of_a_fact(part) for part in value)
    return ""


def _a_fact_the_recap_does_not_say(memory, phrase, body_words):
    """True when this line filed a fact the recap above does not say.

    The topic guard in `_summary_reply` drops the newest line when the word the conversation is on
    appears anywhere in the facts. That is a guess from the topic, so a fact outranks it: a line
    that put something in the store which no part of the summary says is said back, and only the
    lines that add nothing are dropped. The line is matched to its `facts_log` entries the way
    `_recent_told` builds the phrase it says, so the match is the same line and not a lookalike.
    """
    said = _summary_words(body_words)
    for entry in memory.get("facts_log") or []:
        if not isinstance(entry, dict) or not entry.get("key"):
            continue
        text = " ".join(str(entry.get("text") or "").lower().split())
        if " ".join(_told_phrase(extract.no_tone(text)).split()) != phrase:
            continue
        words = _summary_words(_the_words_of_a_fact(user(memory).get(entry["key"])))
        if words - said:
            return True
    return False


def _kids_told(memory):
    """How many children the person said they have, or 0.

    The count is kept on the person (`user.kids`) when they say it ("i've got two kids", "we have
    three children", "i have 2 kids"), so the summary reads the record rather than the line.
    """
    told = user(memory).get("kids")
    if isinstance(told, bool):
        return 0
    if isinstance(told, int):
        return told if told > 0 else 0
    if isinstance(told, str) and told.strip().isdigit():
        return int(told.strip())
    return 0


def _a_child_is_described(memory):
    """True when the store can say a child of theirs by name or age, which says the same thing."""
    for entry in others(memory):
        who = str(entry.get("who") or "").rstrip("s")
        if who and who in CHILD and (entry.get("name") or entry.get("age") or entry.get("ages")):
            return True
    return False


def _a_few_children(count):
    """Two kids, one child, four children - the count the way a person says it."""
    if count == 1:
        return "one child"
    in_words = {number: word for word, number in extract.KID_NUMBERS.items()}
    return in_words.get(count, str(count)) + " kids"


# The chat summed up as a whole, said the way people say it: "whats our plan", "what have we
# decided", "what do we know so far", "tell me what we've agreed", "walk me through what we
# decided", "so whats the state of play", "how far have we got". Every one of them asks for the
# list the chat holds, not for the newest line ("where were we" is `_summary_ask`, and it is the
# newest line) and not for one thing its words name. It has to be the whole line: "what have we
# got for dinner" and "whats the plan for dinner" name a thing and are answered about it, so the
# whole-line match is the fence, and the wrapper words in front ("ok", "so", "and right") and the
# ones that only say when ("so far", "then") come off first.
SUMMED_UP = re.compile(
    r"^(?:ok |okay |right |so |and |but |also |well |quick |just )*(?:"
    r"what (?:have|did) we (?:got|get|have|decided|decide|settled|settle|agreed|agree|know)|"
    r"what do we (?:know|have|got)|"
    r"what(?:'s|\u2019s|s)? (?:our|the) plan|what is (?:our|the) plan|"
    r"tell me what we(?:'ve|\u2019ve|ve)? (?:agreed|decided|settled)|"
    r"walk me through what we (?:decided|agreed|settled)|"
    r"what(?:'s|\u2019s|s)? (?:the )?state of play|what is (?:the )?state of play|"
    r"how far (?:have|did) we (?:got|get)|"
    r"what(?:'s|\u2019s|s)? decided|what is decided"
    r")(?: so far| then| now| again| already| on)*\s*[?.!]*$")


def _summed_up(low):
    """True for a line that asks for the whole chat summed up, rather than for one line of it."""
    return bool(SUMMED_UP.match(str(low or "").strip()))

def _summary_reply(memory):
    known = user(memory)
    parts = []
    if known.get("name"):
        parts.append("you're " + known["name"])
    # Their age is a fact they gave, so it is in the summary: "im 41" then "what do you know about
    # me" answered "not much yet", which reads as the bot not listening. It hangs off the name
    # when there is one ("you're Sam, 41") rather than saying "you're" twice.
    if known.get("age"):
        age = str(known["age"])
        if parts and parts[0].startswith("you're ") and "," not in parts[0]:
            parts[0] += ", " + age
        else:
            parts.append("you're " + age)
    if known.get("job"):
        # The summary says the job the way the job reply does, from its frame: a shift told as
        # "i work nights" is "you work nights" here too, never "a nights".
        said = _job_phrase(known)
        if known.get("city"):
            said += " in " + known["city"]
        parts.append(said)
    elif known.get("city"):
        parts.append("you live in " + known["city"])
    shift = str(known.get("shift") or "").strip()
    if shift:
        # "you work nights", the way the line itself said it, never "a nights".
        parts.append("you work " + shift)
    place = str(known.get("workplace") or "").strip()
    if place:
        # Where they work is kept beside the role: "you're a teacher, and you work in a school".
        parts.append("you work " + _place_phrase(place))
    origin = known.get("from")
    if origin and str(origin).lower() != str(known.get("city") or "").lower():
        parts.append("you're from " + origin)
    said_things = set()
    for pet in known.get("pets") or []:
        parts.append("you've got " + _a_pet(pet))
        said_things.update(str(pet.get(k) or "").lower().rstrip("s") for k in ("animal", "name"))
    # A taste is a thing they told the bot about themselves, so the summary that answers "what do
    # you know about me?" has to carry it: a hedge stays a hedge ("not sure about curry"), and
    # only a plain dislike is said as one (`bot/memory/taste.py`).
    for taste in known.get("tastes") or []:
        thing = str(taste.get("thing") or "").strip()
        if not thing:
            continue
        # A taste about a thing the summary has already named is said once, in the fuller line:
        # "we love our dog" is "you've got a dog, and you like it", not the dog twice over.
        bare = thing.lower()
        bare = bare[5:] if bare.startswith("your ") else bare
        if bare in said_things or bare.rstrip("s") in said_things:
            continue
        how = str(taste.get("how") or "yes")
        if how == "no":
            parts.append("you're not keen on " + thing)
        elif how == "unsure":
            parts.append("you're not sure about " + thing)
        else:
            parts.append("you like " + thing)
    if known.get("allergies"):
        parts.append("you're allergic to " + ", ".join(known["allergies"]))
    named = set()
    for entry in others(memory):
        who = entry.get("who")
        p_allergic = entry.get("allergies") or []
        if who and p_allergic:
            parts.append("your " + who + _is_are(who) + "allergic to " + ", ".join(p_allergic))
            named.add(who)
        # A person they named, or told the age of, is a fact of theirs like the allergy is, and
        # the summary says it the way the recall would: "your mum is called Janet".
        p_name = str(entry.get("name") or "")
        p_age = str(entry.get("age") or "")
        # The ages a group of children was given are one fact, and the summary says them the way
        # the recall does: the verb agrees with the people ("your kids are", never "your kids
        # is"), and every child is in the line.
        p_ages = [age for age in entry.get("ages") or [] if isinstance(age, int)]
        p_diet = str(entry.get("diet") or "")
        if who and p_name and who.rstrip("s") in CHILD and p_age:
            # A child given with a name and an age is said as the child, not as the group they
            # came in: "Ada is 7", because "your kids is called Ada and is 7" is one child too
            # many and the wrong word for them.
            parts.append(_called(p_name) + " is " + p_age)
            named.add(who)
        elif who and p_name:
            said = "your " + who + " is called " + _called(p_name)
            if p_age:
                said += " and is " + p_age
            parts.append(said)
            named.add(who)
        elif who and p_ages:
            said_ages = (", ".join(str(age) for age in p_ages[:-1]) + " and " + str(p_ages[-1])
                         if len(p_ages) > 1 else str(p_ages[0]))
            parts.append("your " + who + _is_are(who) + said_ages)
            named.add(who)
        elif who and p_age and who.rstrip("s") in CHILD:
            # One child, given as an age rather than a count ("i have a 4 year old"): said the
            # way they said it, because "your kids is 4" is not a sentence and does not agree
            # with the word in front of it.
            parts.append("you've got a " + p_age + " year old")
            named.add(who)
        elif who and p_age:
            parts.append("your " + who + " is " + p_age)
            named.add(who)
        if who and p_diet:
            parts.append("your " + who + " " + _a_diet_predicate(who, p_diet))
            named.add(who)
    # A count of children is a fact they gave, and the summary could not say it: the count only
    # ever came back as the line quoted ("you said you have got two kids"), so a chat that had
    # said how many children it had answered "what do you know about me" with everything except
    # them. A child the store can name or age is said as that child, and the count beside it would
    # be the same fact twice.
    told_kids = _kids_told(memory)
    if told_kids and not _a_child_is_described(memory):
        # "you've got a dog and two kids" reads as one line; two "you've got"s in a row reads
        # like a list of records, so a part that already says "you've got" takes the count on.
        if parts and parts[-1].startswith("you've got "):
            parts[-1] += " and " + _a_few_children(told_kids)
        else:
            parts.append("you've got " + _a_few_children(told_kids))
    if known.get("diet"):
        diet = str(known["diet"])
        parts.append("you don't " + _diet_how(diet) + " " + diet[3:] if diet.startswith("no ")
                     else "you're " + diet)
    if known.get("condition"):
        parts.append("you're " + ", ".join(str(c) for c in known["condition"]))
    if known.get("budget"):
        parts.append("your budget is " + str(known["budget"]))
    plans = list(known.get("plans") or [])
    # A correction puts the plan itself under `user["plan"]` (`corrected.py`), and the summary read
    # only the list, so a plan that had been put right was one the recap could not say at all.
    if known.get("plan") and known["plan"] not in plans:
        plans.append(known["plan"])
    last_plan = str(plans[-1]) if plans else ""
    # A plan often names what another part would say: "a picnic for my daughter" makes
    # "you mentioned your daughter" a repeat, so say it once, in the fuller line.
    # The line said back at the end often names the person too ("you said your sister had a baby
    # girl"), so the person is not named twice.
    told = _last_told(memory)
    # A taste already names the thing ("you like your sister's dog"), so a person in it is not
    # named again in the line about them.
    in_tastes = " ".join(str(t.get("thing") or "").lower() for t in known.get("tastes") or [])
    people = [p for p in (known.get("people") or [])
              if p not in named and str(p).lower() not in last_plan.lower()
              and str(p).lower() not in told.lower()
              and str(p).lower() not in in_tastes]
    if people:
        parts.append("you mentioned your " + ", ".join(people[:3]))
    if plans:
        # The plan is said in the shape it was given: a plan they stated ("im going away for 2
        # weeks in june") is a sentence and comes back as one, and a plan that is only the thing
        # itself ("the gym tomorrow") needs a verb in front of it. Saying a sentence after "on
        # about" reads like a machine: "you were on about lose five kilos before summer".
        plan = plan_sentence(plans[-1], plan_line(memory, plans[-1]))
        plan = plan[:1].lower() + plan[1:]
        if known.get("age") and AGE_SAID_IN_WORDS.search(plan):
            # "i'm 41 and i'm training for a marathon" keeps the whole line as its plan, and the
            # age is already said first in the summary: it is said once.
            plan = _without_the_age(plan)
        # The plan often names the person the line above just named ("a picnic for my daughter"
        # makes "you mentioned your daughter" a repeat), so it is said once, in the fuller line.
        if plan and plan.lower() not in " ".join(parts).lower():
            parts.append(plan)
    # The chat itself, said back in their words. It goes last because it is the loosest thing the
    # store knows, and it is left out when a fact above already says it.
    body_words = "; ".join(parts)
    subject = topic_subject(memory).lower()
    # A fact above that already names the thing ("you've got a kitten" for "thinking of getting a
    # kitten", "your daughter is allergic to nuts" for "her nut allergy") says it better than the
    # line itself, so the line is not said again.
    head = subject.split()[-1] if subject else ""
    # The lines themselves, said back in their words, newest first. A fact with no key to live
    # under ("i dont drive", "i work from home") is only the line, and a summary that says the
    # last one alone forgets it as soon as another line goes by. Two is the most that reads like a
    # friend rather than a log.
    facts_body = "; ".join(parts)
    # The newest line is the one the facts above are about, so it is the one the topic guard
    # applies to; an older line is a different thing they told you.
    said_back = 0
    for phrase, from_current in _recent_told(memory, limit=4):
        body_words = "; ".join(parts)
        # Every word of the line is already in the facts above ("im veg" -> "you're veg"), so the
        # line itself would say nothing new: the facts are the same words, said better.
        told_words = _summary_words(phrase)
        covered = bool(told_words) and _says_nothing_new(phrase, told_words, body_words)
        if not covered and told.startswith("you work ") and "you work " in body_words:
            # Where they work is already in the summary, said from the store ("you work in a
            # bakery" after "you work in a school"). The older line said back beside it reads as
            # two answers to the same question: "you work in a bakery; you said you work in a
            # school".
            covered = True
        # "you grew up in Bolton" adds nothing to "you're from Bolton": the thing it names is
        # already in the summary.
        anchor_word = ""
        for word in phrase.split():
            if len(word) > 3 and word.lower() not in SAY_BACK_VAGUE:
                anchor_word = word.lower()
        # The topic guard: the last word of the subject the chat is on, found anywhere in the
        # facts above, means the line is about something already said. It is a guess from the
        # topic, so it gives way to a fact: a line that filed something the recap does not say is
        # never dropped for the topic's sake. Without that, "i live in bristol" set the topic to
        # "live bristol" and the next line, "i've got two kids", was dropped because "bristol" was
        # in the facts above - the count of children was in no reply at all:
        #
        #     i live in bristol        -> Bristol - what's it like there?
        #     i've got two kids        -> Two kids - good to know. How old are they?
        #     what do you know about me-> So far I know you live in Bristol.
        on_topic = (from_current and head and head in facts_body.lower()
                    and not _a_fact_the_recap_does_not_say(memory, phrase, body_words))
        if (covered or _already_said(told_words, body_words)
                or (anchor_word and _summary_words(anchor_word) & _summary_words(body_words))
                or on_topic):
            continue
        # One "you said" and then the facts on their own: "you said X; you said Y" repeats the
        # verb twice in a sentence, which reads like a log rather than a friend.
        parts.append(("you said " if not said_back else "") + phrase)
        said_back += 1
        if said_back >= 2:
            break
    if people and said_back:
        # "you mentioned your dad" is the store's vague mention; once a line says what happened
        # to him, the fuller line is the one to keep.
        said_lines = " ".join(part for part in parts
                              if not part.startswith("you mentioned your ")).lower()
        parts = [part for part in parts
                 if not (part.startswith("you mentioned your ")
                         and any(word in said_lines for word in part.split()[3:]))]
    if not parts:
        if _a_judgement_was_said(memory):
            # A judgement about themselves is never filed as a fact (facts.is_a_judgement), so a
            # chat whose only line about them was one has nothing to recap. "Not much yet - you
            # haven't told me about yourself" one turn after "im a bad mum" is the store telling
            # them it did not hear them, which is the one thing a chat that remembers cannot say:
            # the line is held, it is just not a fact to quote back.
            return pick(["I've got that you're being hard on yourself, and no facts about you yet. "
                         "What should I know?",
                         "I have that you're being hard on yourself - and nothing about your life "
                         "yet that I can say back.",
                         "You've told me how you're feeling about yourself, and nothing about your "
                         "life yet. What should I know?"], memory)
        # Nothing to quote is not the same as having heard nothing. "how do i clean the oven" /
        # "and the grill" / "what do you know about me" denied the whole chat ("you haven't told
        # me about yourself") when what it holds is the two questions, so the reply names the
        # thing the chat has been on. A chat with no subject at all keeps the plain line.
        about = _the_thing_the_chat_is_on(memory)
        if about:
            return pick([
                "Nothing about you yet — so far it's been " + about + ". What should I know?",
                "I've got no facts about you yet; we've been on " + about + ". What should I "
                "know?",
                "No notes about you so far — you've had me on " + about + ". What should I know?"],
                memory)
        return "Not much yet — you haven't told me about yourself. What should I know?"
    body = "; ".join(parts)
    # The same summary twice in a row reads like a machine: the lead-in moves instead.
    return pick(["So far I know " + body + ".",
                 "Here's what you've told me: " + body + ".",
                 "You've told me " + body + "."], memory)

def _quote(text, limit=90):
    """The user's own words, without the full stop before the closing quote.

    A quote that stops in the middle of a word reads like a mistake, so a cut quote gives back
    the part word: "my daughter's 7th bi..." is the one people notice.
    """
    text = " ".join(str(text).split())
    if len(text) > limit:
        cut = text[:limit - 1]
        if not cut.endswith(" ") and " " in cut:
            cut = cut[:cut.rfind(" ")]
        text = cut.rstrip(" ,;:-") + "…"
    return "\"" + text.rstrip(" .!?") + "\""

HEAVY_TOPIC = re.compile(
    r"\b(?:died|dying|death|funeral|passed away|buried|cremation|"
    r"kill myself|killing myself|killed myself|suicide|suicidal|end it all|take my own life|"
    r"hurt myself|hurting myself|self harm|self-harm|cut myself|overdose|"
    r"miscarriage|stillborn|terminal|diagnosed with cancer|beat me|beats me|abuses?d? me|"
    r"bullied|bullying|hit me|hits me|assaulted)\b",
    re.I)

def _heavy(line):
    """True when the line is about a death, a crisis or someone being hurt."""
    return bool(HEAVY_TOPIC.search(" ".join(str(line or "").split())))

def _topics_reply(memory):
    """The subjects the conversation has been on, most recent last."""
    lines = history.topic_lines(memory)
    light = [line for line in lines if not _heavy(line)]
    if not lines:
        return pick(NOTHING_STARTED, memory)
    if not light:
        return pick(["We've been on something heavy, and I won't read it back to you. It is "
                     "still here if you want to talk about it.",
                     "What we've been on is heavy, so I'd rather not put it in quotation marks. "
                     "Say more about it whenever you want."], memory)
    said = "; ".join(_quote(line, 60) for line in light)
    if len(light) < len(lines):
        return pick(["We've been on " + said + ", and on something heavy I won't read back.",
                     "Mostly " + said + ". There was something heavier too, and I have not "
                     "forgotten it."], memory)
    return pick(["We've been on " + said + ".",
                 "Mostly " + said + ".",
                 "Covered so far: " + said + "."], memory)

def _first_sentence(text, limit=70):
    """The first sentence of `text`, cut to `limit`: what the bot opened with, not the whole
    paragraph. A cake-timing answer quoted in full is a wall of text in a one-line reply."""
    text = " ".join(str(text).split())
    end = len(text)
    for mark in (". ", "? ", "! "):
        at = text.find(mark)
        if 0 < at < end:
            end = at + 1
    text = text[:end].strip()
    if len(text) > limit:
        cut = text[:limit - 1]
        if " " in cut:
            cut = cut[:cut.rfind(" ")]
        text = cut.rstrip(" ,;:-") + "…"
    return text.rstrip(" .!?")

CALL_ASK = re.compile(
    r"^\W*(?:and\s+|so\s+|but\s+)?(?:should|shall)\s+(?:i|we)\b"
    r"|^\W*(?:and\s+|so\s+|but\s+)?(?:is|would)\s+(?:it|that)\s+"
    r"(?:safe|ok|okay|alright|fine|worth|sensible|wise|a good idea|a bad idea|too (?:late|soon))\b"
    r"|^\W*(?:and\s+|so\s+|but\s+)?(?:do|must)\s+(?:i|we)\s+(?:need to|have to|really need to)\b"
    r"|^\W*(?:and\s+|so\s+|but\s+)?(?:can|could)\s+(?:i|we)\s+(?:still|keep|go)\b")

CARRY_ON = re.compile(
    r"\b(?:keep|keeps|keep on|carry on|carrying on|go on|going|continue|continuing|"
    r"start|starting|start again|go back|back to|train|training|run|running|walk|walking|"
    r"drive|driving|ride|riding|cycle|cycling|swim|swimming|lift|lifting|play|playing|"
    r"work out|exercise|"
    r"push on|push through|try|it|that)\b", re.I)

STOP_IT = re.compile(
    r"\b(?:stop|stopping|quit|quitting|give up|giving up|lay off|rest|resting|take a break)\b",
    re.I)

STOP_CONDITION = re.compile(
    r"^(?:and\s+)?(?:see|ask|call|ring|go to|get|speak to|talk to|tell|stop|if)\b", re.I)

CLAUSE_SPLIT = re.compile(r":\s+|(?<=[.!?])\s+|,\s+(?:and|but|so)\s+")

SEE_SOMEONE = re.compile(
    r"\b(?:see|sees|seeing|call|calling|ring|ringing|go to|going to|get|getting|book|booked|"
    r"visit|visiting|speak to|speaking to|talk to|talking to|check|checked|checked out)\s+"
    r"(?:\w+\s+){0,2}(?:someone|somebody|anyone|a doctor|the doctor|my doctor|doctor|gp|physio|"
    r"nurse|hospital|a&e|ae|surgery|specialist|professional|it checked|this checked|that checked)\b",
    re.I)

HALF_AN_HOUR = re.compile(r"\bhalf\s+an\s+hour\b", re.I)

TIME_LENGTH = re.compile(
    r"\b(?P<count>\d+|an?|a\s+couple\s+of|a\s+few|"
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|"
    r"thirty|forty|forty-five|fifty|sixty|ninety)\s*-?\s*"
    r"(?P<unit>minutes?|mins?|hours?|hrs?)\b", re.I)

LENGTH_FILLER = frozenset(
    "a an the about roughly around give take or and plus maybe depending on it takes that this is "
    "of to for at least more less just only or so too up each per in all altogether total tops "
    "time".split())

LEAD_LABEL = re.compile(r"^[A-Za-z][A-Za-z' -]{0,14}:\s*")

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

SPLIT_MOVES = re.compile(r";\s+|\s+-\s+|\s+\u2014\s+|,\s+or\s+|;\s*or\s+")

BUDGET = re.compile(
    r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright)\W+)*"
    r"(?:i|we|ive|i\'ve|weve|we\'ve)\s+"
    r"(?:(?:really|only|just|literally|maybe|probably|actually)\s+)*"
    r"(?:get|got|have|had|make|leave|take|need|needs|fancy)\s+"
    r"(?:(?:only|just|maybe|about|altogether|in total|tops|roughly)\s+)*"
    r"(?P<length>" + LENGTH + r")\b", re.I)

A_HORIZON = re.compile(
    r"\b(?:for|after|over|in|within)\s+(?:the\s+)?(?:first\s+|next\s+|following\s+)?"
    r"(?:\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|few|couple(?:\s+of)?)"
    r"\s+(?:days?|weeks?|months?)\b", re.I)

def _sentences(answer):
    """The sentences of an answer, in the order given."""
    return [part.strip() for part in SENTENCE_SPLIT.split(" ".join(str(answer or "").split())) if part.strip()]

def _halves(sentence):
    """A sentence cut where a semicolon, a dash or an "or" joins two moves."""
    parts = []
    for part in SPLIT_MOVES.split(sentence):
        part = LEAD_LABEL.sub("", part.strip(" .;,"))
        if part:
            parts.append(part)
    return parts

def _says_something(part):
    """True when a part of an answer says more than how long it takes.

    "20 minutes, give or take" was handed back as the answer to "i have 20 minutes": it is the
    answer's own aside, and on its own it tells the person nothing they did not just say.
    """
    left = TIME_LENGTH.sub(" ", " ".join(str(part or "").split()))
    left = HALF_AN_HOUR.sub(" ", left)
    words = [word for word in re.findall(r"[a-z']+", left.lower())
             if word not in LENGTH_FILLER and len(word) > 1]
    return len(words) >= 2

def _seconds(said):
    """A length of time in seconds ("20 minutes", "half an hour", "a couple of days"), or None."""
    text = " ".join(str(said or "").split())
    if not text:
        return None
    half = HALF_AN_HOUR.search(text)
    found = TIME_LENGTH.search(text)
    if half and (not found or half.start() < found.start()):
        return 1800
    if not found:
        return None
    count = found.group("count").lower()
    if count.startswith("a couple"):
        number = 2
    elif count.startswith("a few"):
        number = 3
    elif count.isdigit():
        number = int(count)
    else:
        number = WORD_NUMBERS.get(count)
    unit = found.group("unit").lower().rstrip("s")
    if not number or unit not in UNIT_SECONDS:
        return None
    return number * UNIT_SECONDS[unit]

def _names_minutes(said):
    """True when the wording names minutes rather than hours: "45 minutes", "twenty-minute"."""
    return any(match.group("unit").lower().startswith("min")
               for match in TIME_LENGTH.finditer(" ".join(str(said or "").split())))

def _longest(said, bare=False):
    """The longest length of time named in a sentence, in seconds, or None.

    The longest and not the first: a move that says "one minute of jogging, two of walking, for 20
    minutes" wants 20 minutes of room, not one, or a budget of 20 minutes would be told the answer
    does not fit it.
    """
    text = " ".join(str(said or "").split())
    if not text:
        return None
    half = HALF_AN_HOUR.search(text)
    if half:
        text = text[:half.start()] + " 30 minutes " + text[half.end():]
    found = [match.group(0) for match in TIME_LENGTH.finditer(text)]
    lengths = [n for n in (_seconds(part) for part in found) if n]
    if bare or any(second <= 3600 for second in lengths):
        # "tuna pasta in 15, macaroni cheese in 25" says its minutes without the word: beside a
        # figure that does name minutes, a bare number after "in" is a length too, and without it
        # a list of quarter-hour meals was read as taking forty-five minutes.
        for bare in re.finditer(r"\bin\s+(\d{1,2})\b", text, re.I):
            minutes = int(bare.group(1))
            if 0 < minutes <= 90:
                lengths.append(minutes * 60)
    return max(lengths) if lengths else None

A_LENGTH_AS_THE_SUBJECT = re.compile(
    r"^(?:(?:so|and|but|well|ok|okay)\s+)?"
    r"(?:(?P<length>" + LENGTH + r")\s*(?:left\b|,|\bis\b|\bwas\b|\bfeels\b|\bsounds\b)"
    r"|that\s+wants\s+(?:longer|more)\s+than\s+" + LENGTH + r"\b"
    r"|it\s+takes\s+longer\s+than\s+" + LENGTH + r"\b)", re.I)

def _a_remark_about_a_length(answer):
    """Whether the reply only remarks on a length, giving none to a thing it names.

    True only when every sentence of it that names a length has that length as its subject. A reply
    that puts a length on a thing - "roast it for 20 minutes a kilo" - is an answer, whatever else
    it says, so one such sentence is enough to make it one.
    """
    remarked = False
    for sentence in _sentences(answer):
        if _longest(sentence) is None:
            continue
        if not A_LENGTH_AS_THE_SUBJECT.search(" ".join(sentence.split())):
            return False
        remarked = True
    return remarked

def _moves(answer):
    """The moves of an answer in the order given: the move, its length, and its sentence number."""
    names = _names_minutes(answer)
    out = []
    for at, sentence in enumerate(_sentences(answer)):
        for part in _halves(sentence):
            if not _says_something(part):
                continue
            out.append((part, _longest(part, bare=names), at))
    return out

def _up_to_the_move(answer, part):
    """The answer from its first sentence to the one `part` was cut from, and no further.

    A move of an answer is not the whole of it: the sentence before it says what to do with it
    ("bring a pan of water to a bare simmer ... slide the egg in from a cup", then "3 minutes
    gives a soft yolk"). Handing back the move alone answered a question about how with a number,
    and handing back everything after it put a second recipe in the reply.
    """
    want = " ".join(str(part or "").split())
    sentences = _sentences(answer)
    for at, sentence in enumerate(sentences):
        for half in _halves(sentence):
            if " ".join(half.split()) == want:
                if not at:
                    # The move is in the answer's first sentence, where everything that comes
                    # before it is already in it: "tuna pasta in 15, macaroni cheese in 25" needs
                    # no lead-in, and taking the whole sentence would put the forty-five minute
                    # traybake in a reply that says half an hour covers it.
                    return want
                return " ".join(sentences[:at + 1]).strip()
    return None

def _the_move_that_fits(moves, room):
    """The move whose own length is the largest that fits, and the long move it is a step of.

    The largest that fits, not the shortest: somebody with 20 minutes wants the twenty-minute way
    of doing it, not the two-minute half of a paragraph that is about something else. The second
    value is the length of the move that takes longer than the room when that move is in a
    sentence *before* the one that fits, and the fit is therefore a step of it: "rest it for 15
    minutes before carving" comes after "a 2kg bird takes roughly 1 hour 40", so it is a step of
    that bird. Two ways of the same thing ("aim for about 150 minutes a week - five half-hours, or
    three twenty-minute sessions") are in one sentence, so the twenty-minute way there is a way to
    do it and not a step of the longer one.
    """
    best, best_sentence, best_seconds = None, None, -1
    over, over_sentence = None, None
    for part, took, sentence in moves:
        if took is None:
            continue
        if took > room:
            if over is None:
                over, over_sentence = took, sentence
            continue
        if took > best_seconds:
            best, best_sentence, best_seconds = part, sentence, took
    step = over if (best is not None and over is not None and over_sentence < best_sentence) else None
    return best, step

def _left_out(moves, room):
    """True when the answer has a move of its own that takes longer than the room."""
    return any(took is not None and took > room for _part, took, _at in moves)

def _the_lead(answer):
    """The first thing an answer says, for a budget too small for any move of it.

    The lead and not the quickest move: an answer that lists what can be cooked "in 15" and "in
    25" has one move with a length on it - the forty-five minute one - and handing that back to
    somebody with five minutes answers a question they did not ask.
    """
    for sentence in _sentences(answer):
        part = LEAD_LABEL.sub("", sentence.strip(" .;,"))
        if _says_something(part):
            return part
    return None

A_RATE_OF = re.compile(
    r"\b(?P<length>\d[\d,.]*|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|"
    r"twenty|thirty|forty|forty[- ]five|fifty|sixty|ninety|half\s+an|an?)\s*"
    r"(?P<unit>minutes?|mins?|hours?|hrs?)\s+(?:a|per|each)\s+(?:day|week)\b", re.I)

def _a_rate_of_the_same_length(answer, room):
    """True when the answer names this same length as a regular allowance ("20 minutes a day").

    A length said as a rate is what the person's day holds, and the answer is already about it:
    what the allowance means is the sentence that says so, not the answer's first move.
    """
    for found in A_RATE_OF.finditer(str(answer or "")):
        if _seconds(found.group("length") + " " + found.group("unit")) == room:
            return True
    return False

def _the_budget_on_the_answer(text, memory):
    """The answer above, cut to the part of it that fits the time they say they have, or None.

    Narrow on purpose: the line has to be the person saying how much time there is, nothing else
    ("only for work", "i was only 5 minutes" say no length at all), it must not be a question, and
    the answer it follows has to carry a length of its own - there is nothing to fit a budget to
    otherwise. A budget too small for any of the answer still gets its quickest move, because the
    answer is the answer: it only takes longer than they have.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    said = " ".join(text.split())
    if not said or "?" in said or len(said.split()) > 11:
        return None
    found = BUDGET.match(said)
    if not found:
        return None
    tail = said[found.end():].strip(" .!,;")
    if len(tail.split()) > 4:
        # "i only get 20 minutes to get to the station" is a question about the journey, not the
        # room the answer above has.
        return None
    if re.match(r"^of\b", tail, re.I):
        # "i have 2 hours of meetings today" is two hours of meetings, not two hours to cook: the
        # length belongs to the thing after it, and the answer above has all the room it had. A
        # length said "before work" or "to myself" is still room ("20 minutes before work" is the
        # time there is), so the gate is on the "of" and not on a tail at all.
        return None
    room = _seconds(found.group("length"))
    if room is None:
        return None
    longer = None
    for answer in _recent_answers(memory):
        if _a_rate_of_the_same_length(answer, room):
            # The answer already talks about this length as a regular allowance - "Twenty minutes
            # a day gets you a simple song in two or three months" - so the length is answered and
            # the reply is that sentence, which the composer hands back. Claimed as a budget the
            # whole answer came back again, first sentence and all: "i want to learn guitar" then
            # "i only get 20 minutes a day" was the guitar answer twice. A length the answer gives
            # its own steps in ("fry it hot for 5 minutes", "3 minutes gives a soft yolk") is not
            # this, and neither is a rate for a different length ("150 minutes a week").
            return None
        if room < 86400 and A_HORIZON.search(answer):
            # "ice it for 20 minutes at a time ... for the first two days" is a day's regime read to
            # a 20-minute budget: the length in it is a step, not what the answer costs, and "20
            # minutes is more than enough for all of that" is not true of a two-day answer. The
            # answer stands as it was given - passing the line on put another module in charge of
            # it, which said "Same as before: <the whole answer>" and told them nothing new.
            lead = _the_lead(answer)
            if lead:
                return pick(BUDGET_TIGHT, memory).format(
                    budget=_theirs(found.group("length"), mid=True), part=_tidy(lead))
            continue
        if _a_remark_about_a_length(answer):
            # A remark about a length is not an answer with a length in it, so there is nothing
            # here for the budget to fit inside: look further back for the answer it is about.
            continue
        longest = _longest(answer)
        if longest is None:
            # A turn with no length in it is not the answer this budget is about: a reply of the
            # store's own ("Fair enough - no salad in anything I suggest"), or a detail turn in
            # between, must not hide the answer two turns up that the budget is really for.
            continue
        moves = _moves(answer)
        part, over = _the_move_that_fits(moves, room)
        if over is not None:
            # The answer's long move is behind the one that fits, so the fitting move is a step of
            # it and not a way to do the whole thing: "how long do i roast a chicken" with 20
            # minutes found "rest it for 15 minutes before carving" and said 20 minutes covered a
            # bird that takes 1 hour 40. A step is never the answer to a budget that the answer
            # itself does not fit, so the answer's lead says it in the tight shape instead.
            lead = _the_lead(answer)
            if lead:
                return pick(BUDGET_TIGHT, memory).format(
                    budget=_theirs(found.group("length"), mid=True), part=_tidy(lead))
        if part:
            # Which shape it takes is decided by whether the budget leaves anything out: a budget
            # bigger than every move in the answer is not a limit, and saying "two hours is enough
            # for that" beside a list of quarter-hour meals made the clock the point of the reply.
            if _left_out(moves, room):
                shorter = _up_to_the_move(answer, part)
                if shorter and len(shorter.split()) <= 90 and _says_something(shorter):
                    # A move is handed back with everything the answer said before it: "3 minutes
                    # gives a soft yolk" on its own answered a question about how with a number,
                    # and the pan, the vinegar and the whirlpool were in the sentence before it.
                    part = shorter
                shape = BUDGET_FITS
            else:
                # A budget bigger than every move of the answer is not a limit on anything, so the
                # answer must not come back whole: "i want to learn guitar" then "i have 30
                # minutes a day" was the guitar card again, word for word, with one line added,
                # and "how do i cook a steak" then "i have an hour" was the steak card again. The
                # person is saying time is not the thing in the way, so the answer's lead (what to
                # do first) is quoted, not all of it.
                # An answer whose only number is the one in the move keeps the whole of itself: the
                # egg's "3 minutes gives a soft yolk" is the how the person asked for, and the pan
                # work in front of it is one sentence. An answer with several numbers has no single
                # one to keep, and quoting it back reads as the previous reply twice.
                kept = None
                if len(ANY_FIGURE.findall(answer)) == 1:
                    shorter = _up_to_the_move(answer, part)
                    if shorter and len(shorter.split()) <= 45 and _says_something(shorter):
                        kept = shorter
                if kept:
                    part = kept
                else:
                    lead = _the_lead(answer)
                    if lead and len(lead.split()) <= 90 and _says_something(lead):
                        part = lead
                shape = BUDGET_MORE
            return pick(shape, memory).format(budget=_theirs(found.group("length")),
                                              part=_tidy(part))
        if longer is None:
            longer = answer
    if longer is None:
        return None
    part = _the_lead(longer)
    if not part:
        return None
    return pick(BUDGET_TIGHT, memory).format(budget=_theirs(found.group("length"), mid=True),
                                             part=_tidy(part))

def _theirs(length, mid=False):
    """The length as they said it, with a capital and no full stop: "20 minutes"."""
    text = " ".join(str(length or "").split()).strip(" .;,")
    if not text:
        return text
    if mid and not text[1:2].isupper():
        return text[:1].lower() + text[1:]
    return text[:1].upper() + text[1:]

def _tidy(part):
    """A move of an answer as the first thing a reply says: capital, no trailing full stop.

    A question mark goes too: the budget shapes put a full stop and a sentence after this, so an
    answer that ended on a question read "does that feel like enough for what you have in mind?.
    That wants longer than 20 minutes" (witty-string, #6254). The pools that end on a question are
    every pool the composer has, so this is the store's join to fix and not one module's wording.
    """
    text = " ".join(str(part or "").split()).strip(" .;,?!")
    if not text:
        return text
    return text[:1].upper() + text[1:]

def _clauses(reply):
    """The clauses of an answer, longest-lived punctuation split, in the order given."""
    text = " ".join(str(reply or "").split())
    return [part.strip(" .;") for part in CLAUSE_SPLIT.split(text) if part.strip(" .;")]

def _the_limit(reply):
    """The answer's own restriction - "cut the distance and the speed for a week or two"."""
    for part in _clauses(reply):
        low = part.lower()
        if len(part.split()) > 24:
            continue
        if any(low == word or low.startswith(word + " ") for word in RESTRICT_OPENS):
            return part
    return None

def _the_condition(reply):
    """The answer's own stop condition - "see a physio if the pain is sharp" - or None."""
    for part in _clauses(reply):
        low = part.lower()
        if len(part.split()) > 26:
            continue
        if STOP_CONDITION.match(low) and " if " in low:
            return part
    for part in _clauses(reply):
        low = part.lower()
        if re.search(r"\b(?:means stop|stop driving|do not drive|don't drive)\b", low):
            return part
    return None

def _recent_answers(memory, back=3):
    """The answers the chat has had, newest first, as far back as "the advice above" reaches.

    Read from the history every lane writes (`turns`), not from the answer record one lane keeps
    under its own key: that record is that lane's business, and a reader that depends on it goes
    quiet the moment that lane changes it. A turn of the store's own ("Noted: ...") is not an
    answer with advice in it, and the gates below turn it down anyway."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return []
    said = []
    for turn in turns[-back - 1:][::-1]:
        if not isinstance(turn, dict):
            continue
        reply = turn.get("bot")
        if isinstance(reply, str) and reply.strip():
            said.append(reply.strip())
        if len(said) >= back:
            break
    return said

def _shares_a_word(low, said):
    """True when the line names something the answer it would quote also talks about.

    `should i keep running` and the running-knee answer share "run"; `should i keep the
    appointment` and that answer share nothing but "keep" and "the". Stems, so the tense does not
    have to match, and the chat's filler words are not evidence of anything.
    """
    def words(text):
        return {stem(word) for word in keywords(str(text).lower())}
    return bool(words(low) & words(said))

def _the_call_from_the_advice(text, memory):
    """The decision a follow-up asks, answered with the limit the last answer already gave.

    Only a decision about going on with the thing in the air, only when the answer above put a
    limit on it ("cut the distance...", "keep to ten minutes"), and only inside a chat with a
    topic. Everything else is left to the module that knows the line.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    low = _bare(_folded(text, memory))
    if not low or len(low.split()) > 9 or " you " in " " + low + " ":
        return None
    if not CALL_ASK.match(low) or not CARRY_ON.search(low):
        return None
    if SEE_SOMEONE.search(low):
        # "should i see someone about it or wait" is answered by the "when to see a physio" part
        # of the answer above, which the entry that gave it can hand back in full.
        return None
    # The answer that had the limit in it: the newest one that is about the same thing as the
    # line and carries both halves of the advice. A detail turn in between ("only on the outside
    # of the knee", answered with what that pain is) must not hide the advice two turns up.
    limit = condition = None
    for said in _recent_answers(memory):
        if not _shares_a_word(low, said):
            # The line has to be about the thing the answer was about. Without this, one answer
            # with a limit in it answered every decision the chat made for the next three turns:
            # after the running-knee answer, "should i keep the appointment" and "can i still
            # drive there" both came back as "cut the distance and the speed for a week or two".
            continue
        found, if_half = _the_limit(said), _the_condition(said)
        if found and if_half:
            limit, condition = found, if_half
            break
    if not limit or not condition:
        return None
    rest_or_go = re.search(r"\b(?:keep|keep going|carry on|continue|still|go on)\b", low)
    if STOP_IT.search(low) and rest_or_go:
        # "should i rest it or keep going" is a choice between two things, and the advice above
        # argued for one of them in its own words: the entry that knows the sore knee answers
        # that line better than half of it does, so it is left alone.
        return None
    if STOP_IT.search(low):
        # "should i stop running?" - the advice said how to go on with a change, so the answer is
        # the change rather than stopping, in the answer's own words.
        return ("Not all the way: " + limit[0].lower() + limit[1:] + ". And "
                + condition[0].lower() + condition[1:] + ".")
    return pick(CALL_LEADS, memory).format(limit=limit[0].lower() + limit[1:],
                                           condition=condition[0].lower() + condition[1:])

def _trim(text, limit=90):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"

FOOD_CONDITION = frozenset(("coeliac", "celiac", "diabetic", "diabetes", "ibs",
                            "irritable bowel", "crohns", "crohn's", "lactose intolerant",
                            "fructose intolerant", "allergic"))

def _food_facts(memory):
    """The food restrictions the store holds, in the words they can be said back in."""
    mine = user(memory)
    kept = []
    allergies = mine.get("allergies")
    if isinstance(allergies, str):
        allergies = [allergies]
    if isinstance(allergies, (list, tuple)):
        for item in allergies:
            item = str(item).strip()
            if item:
                kept.append("allergic to " + item)
    condition = mine.get("condition")
    if isinstance(condition, str):
        condition = [condition]
    if isinstance(condition, (list, tuple)):
        for item in condition:
            item = str(item).strip()
            if item and item.lower() in FOOD_CONDITION:
                kept.append(item)
    return kept

def _the_food_a_condition_rules_out(condition):
    """The one food word a condition rules out ("coeliac" -> "gluten"), or "".

    The knowledge of which food a condition bans is the kitchen's, and it is already written
    there as a family (``cooking.CONDITION_BANS``); this only names that family so the store can
    say the short word people use instead of the twenty things made of it.
    """
    wanted = cooking.CONDITION_BANS.get(str(condition or "").lower().strip())
    if not wanted:
        return ""
    for name, family in cooking.FAMILIES.items():
        if set(family) == set(wanted):
            return name
    return ""

def _what_a_dinner_has_to_leave_out(memory):
    """The foods a dinner has to leave out, and the fact that rules each one out.

    The store holds two shapes of the same thing: an allergy ("you're allergic to nuts") and a
    condition ("you're coeliac"), and a meal ask after either of them must not be answered with
    "You haven't told me about your diet". Returns the words for "nothing with X in it" and the
    clauses that say why, so the sentence fits one fact or both.
    """
    mine = user(memory)
    left_out, said_so = [], []
    allergies = mine.get("allergies")
    if isinstance(allergies, str):
        allergies = [allergies]
    if isinstance(allergies, (list, tuple)):
        kept = [str(name).strip() for name in allergies if str(name).strip()]
        if kept:
            left_out.extend(kept)
            said_so.append("you're allergic to " + _all_of_them(len(kept)))
    condition = mine.get("condition")
    if isinstance(condition, str):
        condition = [condition]
    if isinstance(condition, (list, tuple)):
        for item in condition:
            named = str(item).strip()
            if not named or named.lower() not in FOOD_CONDITION:
                continue
            food = _the_food_a_condition_rules_out(named)
            said_so.append("you're " + named)
            if food and food not in left_out:
                left_out.append(food)
    return left_out, said_so

def _all_of_them(count):
    """How a person says the whole list back: one thing, two things, or three and more.

    The clause that says why a dinner leaves something out is the store's own facts read aloud, so
    it has to count what the store holds: "im allergic to nuts, shellfish and eggs" came back as
    "you're allergic to both", which is wrong for a list of three and reads as the bot having
    stopped listening at the second one.
    """
    if count == 1:
        return "them"
    if count == 2:
        return "both"
    return "all of them"

def _say_a_list(items):
    """One thing named, or several as people say them: "a, b and c"."""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + " and " + items[1]
    return ", ".join(items[:-1]) + " and " + items[-1]

# The words a person puts between the frame and the verb of it: "i dont really want to talk about
# it", "id honestly rather not say", "i dont actually need to go into it". Only the intensifier is
# allowed and only one, so the frame is still the frame around it.
INTENSIFIER = r"(?:really|honestly|actually|even|ever|particularly|especially|much)"

CLOSE_SUBJECT = re.compile(
    r"\bi (?:just )?(?:want|wanna|would rather|'?d rather|need) to "
    r"(?:forget|drop|leave|skip) (?:it|that|this|all of it|all that)\b|"
    # An intensifier goes where the person puts it: "i dont REALLY want to talk about it" is the
    # same closing as "i dont want to talk about it", and it was read as an ask about how to make
    # conversation. It never changes which frame the line is in, so it sits inside every one.
    r"\bi(?:'?d|\s+would)?\s+(?:" + INTENSIFIER + r"\s+)?rather\s+not\s+"
    r"(?:say|talk about it|go into it|get into it)\b|"
    r"\bi\s+(?:do\s+not|don'?t|dont)\s+(?:" + INTENSIFIER + r"\s+)?"
    r"(?:want|wanna|need)\s+(?:" + INTENSIFIER + r"\s+)?to\s+"
    # "go into it" and "get into it" are how people say this as often as "talk about it", and both
    # were answered with a card about something else.
    r"(?:(?:talk|think|speak|hear)\s+about\s+|(?:go|get)\s+into\s+)(?:it|that|this)\b|"
    r"\bi\s+(?:can'?t|cannot|couldn'?t|won'?t|will not)\s+"
    r"(?:go|get)\s+into\s+(?:it|that|this)\b|"
    r"\b(?:can|could|would) (?:we|you) (?:just )?not (?:talk|speak) about (?:it|that|this)\b|"
    r"\b(?:let'?s|lets) not (?:talk|speak) about (?:it|that|this)\b|"
    r"\bnot (?:going to|gonna) talk about (?:it|that)\b|"
    r"\b(?:drop|forget) (?:it|that)\b|"
    # The shortest take-backs people type. "forget it" was answered with the close above and
    # "never mind" - the commonest of the lot - with the answer again: the tap card said the
    # whole dripping-tap answer twice, and "nvm" and "doesnt matter" did the same. The rest of
    # the line still has to be filler, so "never mind, how do i boil an egg" and "never mind the
    # dog" (a retraction of the animal, which facts.py reads) are not closings.
    r"\bnever\s*mind(?:\s+(?:that|this|it|then|now|anyway|about (?:it|that|this)))?\b|"
    r"\bnevermind(?:\s+(?:that|this|it|then|now|anyway))?\b|"
    r"\bnvm(?:\s+(?:that|this|it))?\b|"
    r"\b(?:it )?(?:does not|doesn'?t|didnt|didn'?t) matter\b|"
    r"\b(?:ignore|skip|scrap|scratch) (?:it|that|this)\b|"
    r"\bnot important\b|"
    r"\bforget (?:i|what i) (?:said|asked)\b|"
    r"\bno more (?:about|on) (?:it|that)\b")

CHANGE_SUBJECT = re.compile(
    r"\b(?:talk|speak|chat) about (?:something|anything) (?:else|different)\b|"
    r"\b(?:change|switch|move) (?:the subject|the topic|to a different|to another|"
    r"onto something else|on to something else)\b|"
    r"\b(?:talk|speak|chat) about another (?:topic|subject|thing)\b|"
    r"\b(?:change|switch) (?:the )?(?:subject|topic)\b|"
    r"\bsomething (?:else|different) (?:for a bit|instead|to talk about)\b")

CARRIES_ON_AFTER = re.compile(
    r"\b(?:it|that|this|all of it|all that)\s+"
    r"(?:(?:in|into|on|onto|for|to|from|with|about|between|among|and|then|when|if|after|before|"
    r"until|till|while|overnight|so|because|as)\b"
    # "at" carries on ("drop it at the door") except in "at all", which is the closing itself:
    # "i dont want to talk about it at all" was answered with an open-question card.
    r"|at\b(?!\s+all\b))")

ASKS_WHETHER_TO = re.compile(r"\b(?:should|shall|can|could|would|do|does|did)\s+i\b|\bi should\b")

ASKS_FOR_HELP = re.compile(r"\b(?:can you help|help me|is it (?:wrong|bad|ok|okay|normal)|"
                           r"what should i|do you think i should|am i wrong)\b")

# The words that say how long a closing holds: "not at all", "at the moment", "for now",
# "right now", "any more". They are part of the closing, not the rest of the sentence, so they are
# taken out before the fence that says the pronoun still has work to do ("leave it for 20
# minutes" keeps its fence because "for 20 minutes" is not one of these).
HOLDS_FOR_NOW = re.compile(
    r"\b(?:at|for)\s+(?:the\s+)?(?:all|moment|minute|time\s+being|now)\b"
    r"|\b(?:right|just)\s+now\b|\bany\s?more\b|\bagain\b|\byet\b")
CLOSE_FILLER = frozenset("""and but so ok okay right then well anyway anyhow also now just
please thanks thank you for a bit moment second though too as if that this at all never mind let
lets we you i me my of on in to the good fine fair enough alright still only really can could
would will shall not oh ah hmm yeah yes no actually wait it its
today tonight now anymore any more again yet later tomorrow moment minute time being""".split())
# The same set without the word for when: what a frame read before the word was allowed.
CLOSE_FILLER_ALWAYS = CLOSE_FILLER - frozenset(
    "today tonight now anymore any more again yet later tomorrow".split())
# A closing carries the word for when it holds: "i dont want to talk about it ANYMORE", "not
# today", "not again". Read as part of the sentence rather than the closing, those lines fell
# through every frame and were answered with an open-question card - the commonest way people say
# a temporary no. The words above say when, never what, so the frame is still the frame.

CHECK_FOLLOWED = re.compile(
    r"^(?:(?:did|do|have|has|were|are)\s+(?:you|u)\s+"
    r"(?:get|got|see|saw|catch|caught|read|hear|heard|note|noted|follow|following"
    r"|have|got|keep|kept|take|taken|remember)"
    r"|(?:you|u)\s+(?:get|got|catch|caught|see|saw|read|hear|heard|follow|following)\b"
    r"|got\s+(?:that|it|this))\s*"
    r"(?:that|it|this|it\s+all|all\s+of\s+that|all\s+of\s+it|all\s+that|everything"
    r"|any\s+of\s+that|any\s+of\s+it|the\s+lot|the\s+whole\s+lot|my\s+message"
    r"|my\s+last\s+message|the\s+message|what\s+i\s+said|what\s+i\s+sent"
    r"|the\s+last\s+bit)?\s*$")

BARE_ACKNOWLEDGEMENT = re.compile(
    r"^(?:(?:so|ok|okay|right|ah|oh|yeah|and|well|great|good|nice|cheers|perfect|loud and clear)"
    r"\s+)*got(?:\s+(?:that|it|this|ya|yas|you))$")

SAID_TO_THE_BOT = re.compile(r"\b(?:you|u|your|yours|urs|yourself)\b")

A_MOOD_LINE = re.compile(
    r"\b(?:sad|sadly|upset|miserable|depressed|low|down|angry|furious|annoyed|gutted|stressed"
    r"|fed up|knackered|exhausted|tired|worn out|lonely|bored|happy|glad|pleased|excited"
    r"|nervous|worried|anxious|scared|frightened|terrified|dreading|overwhelmed|burnt out)\b")

def _reads_as_the_invitation(text, memory):
    """True where the composer reads the line as asking whether the bot saw the thing named.

    Asked of the composer's own reading rather than of a word list, so the store stands down
    exactly where the composer answers and nowhere else. Guarded by `except`, because a reading
    that fails leaves the check in service rather than dropping a line the store did read.
    """
    try:
        from ..compose import fallback
        return bool(fallback.reads_as_if_i_saw(text, memory))
    except Exception:  # noqa: BLE001 - a reading that fails leaves the check in service
        return False

SAFETY_MODULES = frozenset(("safety", "urgent"))

def _the_module_behind(memory, said):
    """The module that answered this line, or "" when the turns do not say."""
    low = _plain_line(said)
    for turn in reversed([t for t in (memory.get("turns") or []) if isinstance(t, dict)]):
        if _plain_line(turn.get("user")) == low:
            return str(turn.get("module") or "")
    return ""

def _the_line_before_the_check(memory, line):
    """The last line they said that was not itself a check, or ""."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-6:]
    for turn in reversed(turns):
        said = str(turn.get("user") or "").strip()
        if not said:
            continue
        if CHECK_FOLLOWED.match(_plain_line(said)):
            continue
        if line and _plain_line(said) == line:
            continue
        return said
    return ""

def _a_check_choice(options, memory, salt):
    """Pick from a pool without saying the same line twice in a row."""
    turns = memory.get("turns") or []
    recent = " ".join(str(t.get("bot") or "") for t in turns[-4:] if isinstance(t, dict))
    fresh = [option for option in options if option[:30] not in recent] or list(options)
    return fresh[(len(turns) + salt) % len(fresh)]

def _a_check_came_before(memory, line):
    """True when the last thing they said was itself a check ("did you get that" twice).

    The sentence was read back to the first one, so reading it back again is the machine repeating
    itself. The check being answered now is not counted, whatever the turns hold.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-6:]
    said_before = [_plain_line(str(turn.get("user") or "")) for turn in turns]
    if (said_before and line and said_before[-1] == line
            and not str(turns[-1].get("bot") or "").strip()):
        # The turn being answered is already recorded, with no reply yet: the line before it is the
        # one that counts. A last turn that has a reply is a line already answered, even when it
        # reads the same as this one - two checks in a row are two checks.
        said_before = said_before[:-1]
    for said in reversed(said_before):
        if not said:
            continue
        return bool(CHECK_FOLLOWED.match(said))
    return False

def _the_followed_check(text, memory):
    """The answer to "did you get that?": the thing they said, said back, or an honest no.

    A check is answered from what the store kept, never with a lookup of the last word in it. The
    line above is read back only when it is theirs to read back: a feeling is answered warmly
    without it, and a line with no fact stays out because "you are so sad" is not something a
    friend says.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    as_said = _folded(text, memory)
    low = _plain_line(as_said)
    if _reads_as_the_invitation(low, memory):
        # "did you see it" after they named the match is a conversation about the match, and the
        # composer answers it (bot/compose/fallback.py, `reads_as_if_i_saw`). Reading their own
        # evening back - "Yes — you watched the final together" - is a true sentence and no reply
        # to somebody who wants to tell you what happened in it. The store answers the other
        # checks on the conversation ("did you get that", "did you see my message") unchanged.
        return None
    if not CHECK_FOLLOWED.match(low):
        return None
    if BARE_ACKNOWLEDGEMENT.match(low) and "?" not in str(text):
        # "got it" is a nod: "understood". Answering it by reading their own line back turns a
        # handshake into a receipt.
        return None
    previous = _the_line_before_the_check(memory, low)
    if previous and _the_module_behind(memory, previous) in SAFETY_MODULES:
        # An emergency is not read back. "Yes, that's what I have: your chest hurts and you can not
        # breathe" is weaker at that moment than the nudge to ring 999 that the safety lane wrote,
        # and reading a symptom back reads as filing it. Nothing is claimed, so the safety pool
        # keeps the turn.
        return None
    # The seed carries the turn count as well as the line, so two chats that check the same way
    # do not open with the same sentence.
    salt = len(low) + 3 * len([t for t in (memory.get("turns") or []) if isinstance(t, dict)])
    if previous:
        if (FEELING_ALONE.match(previous.lower().rstrip("!.,"))
                or A_MOOD_LINE.search(previous.lower())
                or A_PERSON_IN_TROUBLE.search(previous)
                or TREATMENT.search(previous)
                or any(word in previous.lower() for word in GRIEF_WORDS)):
            return _a_check_choice(CHECK_A_FEELING, memory, salt)
        if _is_a_question(previous):
            return _a_check_choice(CHECK_A_QUESTION, memory, salt)
        if SAID_TO_THE_BOT.search(_plain_line(previous)):
            # The line they want read back was addressed to the bot ("i sent you a message", "i
            # wrote to you"): the check is that it arrived, and read back as a fact it comes out
            # as "Yes - you sent you a message".
            return _a_check_choice(CHECK_A_FEELING, memory, salt)
        said = thread.restate(previous)
        if said and len(said.split()) >= 3:
            # A check is answered with the thing they said, unless this is the second check in a
            # row: then the sentence was read back a moment ago, and saying it again is the
            # machine. Whether the bot's line happens to contain that sentence is not the test -
            # "Your budget is 500, then - I'll stick to that" contains it, and after "did you get
            # that" the budget is exactly what the person wants to hear named again. What matters
            # is whether the read-back has already been given to a check.
            checked_before = _a_check_came_before(memory, low)
            if not checked_before:
                return _a_check_choice(CHECK_PLAIN, memory, salt).format(said=said)
            # The bot said this very sentence a moment ago ("Noted: your sons birthday is in
            # june"), so a check twice in a row must not read it back twice: that is the machine
            # talking. A bot line that merely names part of it ("Moving to Leeds. Exciting") is
            # not the same sentence, and reading the line back is what the person is asking for.
            return _a_check_choice(CHECK_A_FEELING, memory, salt)
        # They did say something, it is just not a thing to say back ("hello"): saying there is
        # no line from them would be false.
        return _a_check_choice(CHECK_A_FEELING, memory, salt)
    record = current(memory)
    kept = str((record or {}).get("text") or "") if isinstance(record, dict) else ""
    if kept and not _is_a_question(kept):
        # With nothing to read back, the subject the chat is on is still true and is what they
        # were asking about: "yes - your boiler is broken" answers the question they asked.
        said = thread.restate(kept)
        if said and len(said.split()) >= 2:
            return _a_check_choice(CHECK_PLAIN, memory, salt).format(said=said)
    return _a_check_choice(CHECK_NOTHING_SAID, memory, salt)

def _plain_line(text):
    """The line in plain lower-case words, with the punctuation taken off.

    The folded form is not used here: the understanding engine puts the referent in place of a
    pronoun, so "i don't want to talk about it" comes back naming the thing they have just asked
    to leave alone.
    """
    low = " ".join(str(text or "").lower().split())
    return " ".join(re.sub(r"[^a-z0-9' ]+", " ", low).split())

# A closing names its subject as often as it says "it": "i dont want to talk about work", "i'd
# rather not talk about him", "i dont want to talk about the row". The frames above spell the
# pronoun out, so a named subject fell through them and an ask about how to make conversation took
# the turn. The subject has to be the end of the line and short, and the words inside it may not be
# the ones that turn a closing into a plan ("i dont want to talk about work BUT i have to, so
# where do i start" is not a closing), so the frame is read here rather than inside CLOSE_SUBJECT.
DECLINE_A_SUBJECT = re.compile(
    r"\bi\s+(?:do\s+not|don'?t|dont)\s+(?:" + INTENSIFIER + r"\s+)?"
    r"(?:want|wanna|need)\s+(?:" + INTENSIFIER + r"\s+)?to\s+"
    r"(?:talk|speak|think|hear)\s+about\s+(?P<subject>.+)$|"
    r"\bi(?:'?d|\s+would)\s+(?:" + INTENSIFIER + r"\s+)?rather\s+not\s+"
    r"(?:talk|speak)\s+about\s+(?P<rather>.+)$|"
    r"\b(?:let'?s|lets|can\s+we|could\s+we)\s+not\s+(?:talk|speak)\s+about\s+"
    r"(?P<let>.+)$")

# The words that turn the subject into the rest of a sentence: a plan, a reason or a second ask.
NOT_A_SUBJECT = frozenset("""but and so because cos with without to about for then if when while
    though although or yet also plus as since unless until before after once""".split())


def _a_subject_to_leave_alone(low):
    """True when the line is a closing that names its subject rather than saying "it"."""
    for found in DECLINE_A_SUBJECT.finditer(low):
        subject = (found.group("subject") or found.group("rather")
                   or found.group("let") or "").strip()
        words = subject.split()
        if not words or len(words) > 4:
            continue
        if len(words) > 1 and words[0] in ("it", "that", "this"):
            # "can we not talk about it today" is the pronoun frame with a word after it, and the
            # frame above decides that one: a heavy subject answered by the grief reader with an
            # offer of something ordinary is better than this line, so it is not taken here.
            continue
        if any(word in NOT_A_SUBJECT for word in words):
            continue
        # What is left in front of the frame is filler or nothing, exactly as in the frames above:
        # "i told you already, i dont want to talk about work" opens with a claim about the chat,
        # and that line is bot/memory/told.py's to answer - it knows what to do with the claim.
        before = low[:found.start()].split()
        if not all(word in CLOSE_FILLER for word in before):
            continue
        return True
    return False


def _closes_the_subject(text):
    """True when the whole line asks to leave the thing in the air alone."""
    low = _plain_line(text)
    if not low or len(low.split()) > 12:
        return False
    if re.match(r"(?:what|how|why|when|where|who|which)\b", low):
        # "how do i forget it" is an ask about the thing, not a request to leave it: only a line
        # whose whole content is the closing is taken. "can we talk about something else" passes,
        # because the close or the change of subject has to match for anything to be claimed.
        return False
    if ASKS_WHETHER_TO.search(low) or ASKS_FOR_HELP.search(low):
        return False
    if CARRIES_ON_AFTER.search(HOLDS_FOR_NOW.sub(" ", low)):
        # "drop it in the pan" and "i want to leave it in the oven for 20 minutes" are about the
        # thing, not about leaving it alone: the pronoun has work to do in the rest of the line.
        return False
    if _closes_by_a_frame(low):
        return True
    return _a_subject_to_leave_alone(low)


def _closes_by_a_frame(low):
    """True when one of the frames above covers the line and nothing else in it carries on."""
    for pattern in (CLOSE_SUBJECT, CHANGE_SUBJECT):
        for found in pattern.finditer(low):
            rest = (low[:found.start()] + " " + low[found.end():]).split()
            if all(word in CLOSE_FILLER for word in rest):
                return True
    return False

def _a_plain_frame_closes(low):
    """True when the frames read the line with no help from this reader's newer allowances."""
    for pattern in (CLOSE_SUBJECT, CHANGE_SUBJECT):
        for found in pattern.finditer(low):
            if re.search(INTENSIFIER, found.group(0)):
                continue
            rest = (low[:found.start()] + " " + low[found.end():]).split()
            if all(word in CLOSE_FILLER_ALWAYS for word in rest):
                return True
    return False


def _held_thread(memory):
    """True when a safety answer, rather than a topic, is the thing the chat is carrying."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-3:]
    for turn in turns:
        if turn.get("module") == "safety":
            return True
        said = str(turn.get("bot") or "").lower()
        if any(word in said for word in HELD_THREAD):
            return True
    return False

def _gentle_subject(memory):
    """True when what was closed is heavy: a loss, an illness, a stay in hospital."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-4:]
    for turn in turns:
        if turn.get("module") in ("loss", "grief"):
            return True
        if any(word in str(turn.get("bot") or "").lower() for word in GRIEF_WORDS):
            return True
        if any(word in str(turn.get("user") or "").lower() for word in GRIEF_WORDS):
            return True
    return False

def _can_close(text, memory):
    """Whether the store is the one to answer this closing line.

    Only inside a chat with something in the air (there is nothing to close otherwise) and never
    over a thread the safety module is holding.
    """
    if not _closes_the_subject(text):
        return False
    if not current(memory) and not recent(memory, 2):
        return False
    if _held_thread(memory):
        return False
    if _gentle_subject(memory) and not _a_plain_frame_closes(_plain_line(text)):
        # A loss or a stay in hospital is answered better by the grief reader, which offers
        # something ordinary to talk about instead ("tell me about something ordinary instead if
        # that's easier today"). A closing the plain frames already read stays with it; the ones
        # this reader newly recognises - the word in the middle, the named subject, the word for
        # when - are the store's only on an ordinary subject.
        return False
    return True

def _the_close(text, memory):
    """The answer to a person who has asked to leave the subject: a short yes, and no advice."""
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    if not _can_close(text, memory):
        return None
    low = _plain_line(text)
    gentle = _gentle_subject(memory)
    if CHANGE_SUBJECT.search(low):
        return pick(CHANGE_HEAVY if gentle else CHANGE_PLAIN, memory, low)
    return pick(CLOSE_HEAVY if gentle else CLOSE_PLAIN, memory, low)
