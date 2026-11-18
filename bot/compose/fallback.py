"""The composer's safety net: a fit reply when no module answered the line.

The bot must reply to every line, even one no module knows. A stock line for everything
("Hello!") fails STYLE.md; this answers the *kind* of line instead. It reads the shared
reading in memory["understood"] (kind, clean, words) and the conversation so far, and picks
one short reply from a pool: varied by the line itself, and never one it just used.

Used by bot/modules/greeting.py, the PRIORITY -1000 fallback, and available to any module
that needs an honest holding reply.
"""
import random
import re
import string

from ..memory import ack, facts, history, last_bot, last_user, obstacle, reject, repeat, swap
from ..memory import stuck as stuck_line
from ..understanding import understand
from ..understanding.body import GOING_BOTH_WAYS
from ..understanding.kinds import (ANSWERING_A_QUOTED_ASK, greeting_only,
                                  the_manners_question, two_ends_of_one_scale,
                                  verdicts_a_thing)
from ..understanding.topics import IDIOM_PHRASES, THE_PEOPLE, is_a_machine_word
from . import (A_STEP_ASK, DOUBT, DOUBTED, LINGERED_LINE, NEARLY, says_it_has_lingered,
               step_when_low, turned, turns_round)
from . import (badnews, circumstance, draft, finding_out, goodnews, handoff, harm, leaving, loss,
               no_eyes, onething, outlook, pick, prices, quantity, reaction as answer_reaction,
               remark, stepwords, trouble, unseen, why, worn)
from .postcode import a_postcode_lookup
from .urgent import reads_as_a_story
from .badnews import (DEATH_SAID as SAID_AS_A_DEATH,
                      reads_as_a_closed_door, reads_as_an_award_lost, reads_as_bad_news,
                      reads_as_heavy_news, reads_as_news_with_a_name,
                      reads_as_pregnancy_bleeding, reads_as_the_leaving,
                      reads_as_a_leaving_already_gone, reads_as_a_pet_condition,
                      reads_as_the_speakers_own_plan,
                      reads_as_sudden_loss,
                      reads_as_a_carer_body, reads_for_a_carer, reads_for_a_pet,
                      reads_like_a_symptom)
from .goodnews import (reads_as_an_occasion, reads_as_a_win_nobody_noticed,
                       reads_as_a_clear_result, reads_as_good_news, reads_as_news_to_come,
                       reads_as_recovery,
                       reads_as_settled, worry_on_the_table)

from .not_knowing import (NAMES_WHERE_TO_ASK, POINTER_HEDGE, _an_ask_with_no_subject,
                          _asks_about_this_chat, _the_lead_and_the_route)
from .fallback_data import (
    A_DISMISSAL,
    A_FREE_TIME_ASK,
    A_LOVE_FOR_PEOPLE,
    A_LOVE_FOR_SOMEONE,
    A_SORRY_ON_ITS_OWN,
    ABOUT,
    ABOUT_ITSELF_KINDS,
    ABOUT_SELF,
    ABOUT_TALLY,
    ABOUT_THEM_BEFORE_COPULA,
    ABOUT_WORDS,
    ACK,
    ACKS,
    AGREEMENTS,
    ACK_AFTER_TROUBLE,
    ACK_WARM,
    ACTS_FOR_ME,
    ADVICE_AGAIN,
    ADVICE_COOL,
    ADVICE_COOL_WORDS,
    ADVICE_LENGTH,
    ADVICE_LENGTH_BARE,
    ADVICE_TIME,
    ADVICE_TURNS,
    ADVICE_WORDS,
    ADVICE_WORSE,
    AFRAID_AFTER,
    AFTER_RESOLVED,
    AGREEMENT,
    AIM_FAILING,
    AIM_HEADS,
    AIM_NEGATORS,
    ALIVE,
    ANIMALS,
    APOLOGY_ANSWER,
    ASKED_A_RATING,
    ASKED_IF_GOOD,
    A_GOODNESS_ASKED_OF_ME,
    A_SKILL_ASKED_OF_ME,
    ASKED_IF_I_SAW_LINES,
    ASKING_WORDS,
    ASK_ONLY,
    ASK_OUT_ANSWER,
    AT_IT_EXTRA,
    BECOMING,
    BECOMING_STATE,
    AT_IT_NOT,
    AXIS_MIN,
    A_BIRTHDAY_STILL_TO_COME,
    A_CHILD_LEAVING,
    A_CHILD_LEFT,
    A_COST_SOMEBODY_ASKS,
    A_DAY_AHEAD,
    A_DAY_AHEAD_TENSE,
    A_DREAD,
    A_GOOD_TIME,
    A_GOOD_TIME_IN_A_CARE_THREAD,
    A_HOW_THE_TIME_WENT,
    A_JOB_ON,
    A_JOB_SOON,
    A_LAUGH,
    A_MOOD_WITH_A_CATCH,
    A_PAUSE_WORD,
    A_PERSON,
    A_PLACE_I_DONT_KNOW,
    A_SMALL_DAY,
    A_BOOKING_AHEAD,
    A_BOOKING_AHEAD_DATED,
    A_SUGGESTED,
    A_SUGGESTED_BY_SOMEONE,
    A_THING_AHEAD,
    A_THING_BOUGHT,
    A_THING_DONE,
    A_THING_GONE,
    A_THING_LOOKS_SAD,
    A_THING_ON,
    A_THING_SEEN_TO,
    A_THING_THEY_REGRET,
    A_WANT_IT_OVER,
    ABUSE_AFTER,
    BABY_FOOD_NAMES,
    BABY_WHO,
    BAD_STRETCH,
    BAD_STRETCH_REPLIES,
    BARE_FOLLOW_UP_CARE_REPLIES,
    BARE_FOLLOW_UP_REPLIES,
    BARE_PICK_AFTER_NEWS,
    BARE_PICK_ASK,
    BARE_PICK_BRING,
    BARE_PICK_DO,
    BARE_PICK_EXPECT,
    BARE_PICK_GET,
    BARE_PICK_KIND,
    BARE_PICK_LOOK,
    BARE_PICK_ORDER,
    BARE_PICK_PREPARE,
    BARE_PICK_SIGN,
    BARE_PICK_TAKE,
    BARE_PICK_WEAR,
    BARE_PICK_WEAR_COLD,
    BARE_PICK_WEAR_HOT,
    BARE_PICK_WEAR_WET,
    BARE_PICK_WHICH,
    BEHIND_ON_MONEY,
    BLACKED_OUT_SIGHT,
    BODY_ALSO,
    BODY_BUNGED,
    BODY_COLD,
    BODY_HOT,
    BODY_HUNGRY,
    BODY_LEAD,
    BODY_LIGHT_HEAD,
    BODY_PARTS,
    BODY_PART_QUALIFIER,
    BODY_PART_TAIL,
    BODY_POOLS,
    BODY_QUEASY,
    BODY_SAYS_WHY,
    BODY_SITUATION,
    BODY_STATES,
    BODY_SUBJECT,
    BODY_TAIL,
    BODY_THIRSTY,
    BODY_WORD_FOR_A_THING,
    BOUGHT_VERB,
    BOUND_FOR,
    BURN_AFTER,
    BURN_BLISTER,
    BUYING_WORDS,
    CALL_ANSWER,
    CALL_WORDS,
    CAME_BACK,
    CARD_LINES,
    CARD_VALIDITY,
    CARE_AFTER,
    CARE_AFTER_ANIMAL,
    CARE_AFTER_ANIMAL_STILL,
    CARE_AFTER_STILL,
    CARE_BETTER,
    CARE_HERE,
    CARE_HURTS,
    CARE_INJURY,
    CARE_MODULES,
    CARE_NOT_RESOLVED,
    CARE_PHRASES,
    CARE_POINTER,
    CARE_PRONOUNS,
    CARE_RESOLVED,
    CARE_ROUTE_BACK,
    CARE_SEEN,
    CARE_SEEN_ANIMAL,
    CARE_THREAD,
    CARE_VISIT,
    CARE_VISIT_WARD,
    CARE_WORDS,
    CARING,
    CARING_FOR_A_BODY,
    CHECK_PHRASES,
    CHILD_AT_HOME,
    CHILD_FAINT,
    CHILD_FAINT_ANSWER,
    CHOICE_BETWEEN_PEOPLE,
    CHOICE_HEALTH,
    CHOICE_LIGHT,
    CHOICE_LIGHT_PICK,
    CHOICE_PEOPLE,
    CHOICE_PHARMACIST,
    CHOICE_STAKES,
    CHOICE_THERAPY,
    CHOICE_WEIGH,
    CLOSED_DOOR,
    COMFORT_SAID,
    COMPLAINT_WORDS,
    COMPLAIN_WHO,
    CONGRATS,
    CONTACT_ANSWER,
    COPULA,
    CRISIS_AFTER,
    CRISIS_AFTER_THEM,
    CRISIS_BETTER,
    CRISIS_BETTER_THEM,
    CRISIS_WORDS,
    CROWD,
    CUT_FOR,
    DARK_THING,
    DATES_KEEP_SLIPPING,
    DECLINED_PLAN,
    DECLINED_PLAN_GENTLE,
    DENTIST_WHO,
    DETAILS_IN_A_WARM_LINE,
    DEVICE_WHO,
    DISH_DETERMINER,
    DISH_PARTICIPLE,
    DITHER_DECIDE,
    DITHER_ABOUT_A_PERSON,
    STUCK_AFTER_TROUBLE,
    RUN_OUT_LINES,
    DITHER_OPEN_LINES,
    DITHER_TWO_WAY_LINES,
    DONE_NOT_A_PERSON,
    DONE_NOT_THIS,
    DONE_ONLY_A_THING,
    DONE_VERB,
    DOUBLE_BOOKED,
    EASING_FILLER,
    EATEN_KIND,
    EATING,
    EMERGENCY_AFTER,
    EMERGENCY_ANSWER,
    EMERGENCY_BETTER,
    EMERGENCY_BETTER_THEM,
    EMERGENCY_NOT_WORKED,
    EMERGENCY_WORDS,
    EMPTY,
    ENDINGS,
    EXPERT_WORDS,
    FAINT_COMING_ANSWER,
    FALLBACK_MODULE,
    FAVOURITE_GENERAL,
    FAVOURITE_WORDS,
    FILLERS,
    FILLING_FOODS,
    FILLING_WORDS,
    FIRST_PERSON,
    FLAT,
    FLAT_CORE,
    FLAT_LEAD,
    FLOPPY_WAKE,
    FORECAST,
    FORECAST_AFTER_SAFETY,
    FORECAST_A_FALL,
    FORECAST_BODY_WORDS,
    FORECAST_DURATION,
    FORECAST_HE_SHE,
    FORECAST_I_ASK,
    FORECAST_ILL,
    FORECAST_OFF_THEIR_FOOD,
    FORECAST_PERMISSION,
    FORECAST_PERSON,
    FORECAST_PET,
    FORECAST_PET_HARM,
    FORECAST_POOLS,
    FORECAST_RELATION,
    FORECAST_SELF,
    FORECAST_SELF_STRUGGLING,
    FORECAST_SOMEONE_STRUGGLING,
    FORECAST_STRUGGLE,
    FORGETTING,
    FORGET_A_THING,
    FOUND_IT,
    FRAME_WORDS,
    FUEL_WORDS,
    FUME_WORDS,
    GADGET_WORDS,
    GAS_ANSWER,
    GAS_WORDS,
    GENERIC_WORDS,
    GIFT_WORDS,
    GONE_VERB,
    GOOD_TIME_WORDS,
    GO_ANSWER,
    GO_TO_BE_SEEN,
    GREETING,
    GREETING_AFTER,
    GREETING_WORDS,
    GRIEF_AFTER,
    GRIEVANCE,
    GRIEVANCE_HARM,
    GRIEVANCE_HARM_PHRASES,
    GRIEVANCE_HEALTH,
    GRIEVANCE_HEALTH_PHRASES,
    GRIEVANCE_IMPACT,
    GRIEVANCE_NOT_A_THING,
    GRIEVANCE_PEOPLE,
    GRIEVANCE_PHRASES,
    GRIEVANCE_PRONOUN,
    GRIEVANCE_STRAIN,
    GRIEVANCE_STRAIN_SAID,
    GROWN_UP_WORDS,
    HABIT_ACT,
    HABIT_REPLY,
    HAND,
    HANDED_BACK,
    HAZARD_AFTER,
    HAZARD_WORDS,
    HEALTH_RECORD,
    HEALTH_RECORD_LINES,
    HEALTH_WHO,
    HEALTH_WORDS,
    HEALTH_WORLD,
    HANDS_BACK,
    HEDGE_POOL,
    HELLO_STILL_THERE,
    HELLO_WITH_YOU,
    HELP,
    HELPLINE_NOT_AN_AMBULANCE,
    HELP_ALREADY,
    HELP_TAIL,
    HELP_TOPIC,
    HELP_TOPIC_ANY,
    HOLD_AFTER,
    SORTED_AND_NO_CALL_YET,
    HOUSE_VERB,
    HOW_ARE_YOU,
    HOW_ARE_YOU_ASKS,
    HOW_ARE_YOU_GOING_ON,
    HOW_ARE_YOU_GOING_ON_AFTER,
    HOW_ARE_YOU_TAGS,
    HOW_TO_DECIDE_FILLER,
    HOW_TO_DECIDE_LINES,
    HUMAN_EMPTY,
    IDENTITY,
    IDIOM_GLAD,
    IDIOM_SHY,
    ILL_AFTER,
    ILL_BEFORE,
    ILL_SAID_OF_A_BODY,
    ILL_WILL_VERBS,
    IMPERATIVE,
    INVITED,
    INVITED_TO_TALK,
    INVITE_ACTIVITY,
    INVITE_FILLER,
    INVITE_NEVER,
    INVITE_PRONOUN,
    JUDGE_ASKS_FINE,
    JUDGE_ASKS_MAD,
    JUDGE_ASKS_SLIGHT,
    JUDGE_BARE_FACES,
    JUDGE_FINE,
    JUDGE_FINE_PLAIN,
    JUDGE_LEAD,
    JUDGE_NOD_WORDS,
    JUDGE_NOT_A_GERUND,
    JUDGE_NOT_A_VERDICT,
    JUDGE_NOUN,
    JUDGE_NO_PLAN,
    JUDGE_NO_PLAN_FINE,
    JUDGE_NO_PLAN_MAD,
    JUDGE_NO_PLAN_MIND,
    JUDGE_ONLY_A_PLAN,
    JUDGE_PLAN_HAS_A_HOLE,
    JUDGE_PLAN_STOP,
    JUDGE_SANE,
    JUDGE_SANE_PLAIN,
    JUDGE_SELF_JUDGING,
    JUDGE_SOUNDS_FINE,
    JUDGE_WISH_ANGRY,
    JUDGE_WORTH,
    JUDGE_WORTH_PLAIN,
    JUNK_CUES,
    KEEPS_FORGETTING,
    KNOCKED,
    KNOCKED_SPOTS,
    LANDED_BAD,
    LANGUAGE_FLUENCY,
    LATE_BEHIND_LINES,
    LATE_NOW_LINES,
    LAUGHING_WORDS,
    LEFT_POOL,
    LEFT_POOL_GONE,
    LIVE_DELAY_WORDS,
    LIVE_HOURS_ASK,
    LIVE_YES_NO_OPEN,
    LIVE_INDOOR,
    LIVE_JOURNEY_ENDS,
    LIVE_KINDS,
    LIVE_NEWS_REPLY,
    LIVE_NOT,
    LIVE_NOT_HOURS,
    LIVE_OPEN_CLOSE,
    LIVE_PAPER_WORDS,
    LIVE_ROAD_NAME,
    LIVE_ROADS_NOT,
    LIVE_ROAD_WORDS,
    LIVE_SETTING,
    LIVE_SITE_THING,
    LIVE_SKY,
    LIVE_SKY_OFF,
    LIVE_SKY_WHY,
    LIVE_SOON,
    LIVE_STRONG,
    LIVE_TAKE_ALLOWED,
    LIVE_TAKE_ASK,
    LIVE_TRAVEL_WORDS,
    LIVE_VENUE,
    LIVE_VENUE_RE,
    LIVE_WEAR,
    LIVE_WEATHER_WORDS,
    LOCKED_OUT_LINES,
    LOCKED_OUT_OF_THE_CAR,
    LOST_A_THING,
    LOST_A_THING_AGAIN,
    LOW_DAY_REPLIES,
    LUMP,
    MANNERS_ONLY,
    MEDS_WORDS,
    MEMORY,
    MESS_PLACES,
    MILESTONE,
    MILESTONE_EVENT,
    MISHAP_BACK,
    MODEL_NAMED_WORDS,
    MONEY_WORDS,
    MOOD_AFTER,
    MOOD_BEFORE,
    MOUTH_WORDS,
    MOVE_ON_AFTER,
    MYSELF,
    MY_DOING,
    MY_OWN,
    MY_OWN_DAY,
    MY_PICK,
    MY_PICK_ASK,
    MY_PICK_NOTE,
    MY_BILL_LINES,
    MY_RECORDS,
    OFFICE_RECORD_LINES,
    AT_THE_TILL,
    POINTS_LINES,
    MY_WORKINGS,
    NAMED_NEGATIVE,
    NAMED_TYPES,
    NARROW_ANSWERED,
    NARROW_SUBSTANCE,
    NARROW_WORDS,
    NEGATIVE,
    NEGATIVE_CUES,
    NEGATORS,
    NETWORK_WORDS,
    NEUTRAL,
    NEVER_MIND,
    A_CORRECTION_TAKEN,
    NEWS_TO_COME,
    NOT_AN_ANSWER,
    NOT_A_FORM,
    NOT_A_NAME,
    NOT_A_VERDICT_SUBJECT,
    NOT_CHOSEN,
    NOT_ENOUGH_REPLY,
    NOT_FIT_ENOUGH,
    NOT_NOTED,
    NOT_PEOPLE_WORDS,
    NOT_THEIR_VERB,
    NOT_TOO_OLD,
    NO_DIRECTION_REPLY,
    NO_MORE_OF,
    NO_WORDS_ASKING,
    NO_WORDS_AT_THE_CARE,
    NO_WORDS_SOMEONE,
    NO_WORDS_STUCK,
    OCCASION,
    ONE_SKILL_RATED,
    ONGOING_WORDS,
    ONLY_FRONT,
    OPINION_ASKS,
    OURS,
    OUTCOME_LINES,
    OWN_PERSON,
    OWN_PLACE,
    PARTICLE,
    PASSED_OUT_ANSWER,
    PASSED_OUT_PERSON,
    PASSWORD_TROUBLE,
    PAUSE_IN_A_SAFETY_THREAD,
    PAST_STATE_CUES,
    PAUSE,
    PENDING_DOUBT,
    PENDING_LANDED,
    PENDING_WAITING,
    PENDING_WHEN,
    PERSON_WORDS,
    PEST_WHO,
    PETROL_WORDS,
    PET_CONDITION_TROUBLE,
    PET_TROUBLE,
    PICKS_A_MECHANISM,
    PICK_ONLY_WORDS,
    PLAIN_WORDS,
    PLAN,
    PLAN_DONE,
    PLAN_DONE_ACK,
    PLAN_KNOCKED,
    PLASTER_IT,
    POINTING,
    POSITIVE,
    POSITIVE_CUES,
    PRAISE,
    PREGNANCY_BLEEDING,
    PRESENCE_LEFTOVER,
    PRESENT,
    PUNT,
    QUESTION_OPENERS,
    QUESTION_WORDS,
    QUIET_MODULES,
    QUOTE_LINES,
    REACTIONS_CARE,
    REACTIONS_SAID,
    REACTION_DISBELIEF,
    REACTION_DISBELIEF_SAID,
    REACTION_LEAD,
    REACTION_MISHAP,
    REACTION_MISHAP_SAID,
    REACTION_OUCH,
    REACTION_OUCH_SAID,
    REACTION_RELIEF,
    REACTION_RELIEF_SAID,
    REACTION_REPEAT,
    REACTION_REPEAT_FIRST,
    REACTION_WORD,
    REACTION_WORDS,
    REFUSED_REPLIES,
    RELATIONSHIP_DECISION,
    RELIEF,
    REPAIR_RULE,
    REPORT_FILLER,
    REQUEST_CUES,
    RESOLVED_AFTER,
    THE_CALL_STANDS_ANYWAY,
    RESOLVED_AFTER_THEM,
    RING_FOR_HELP,
    RING_THE_POLICE,
    ROUTINE,
    ROUTINE_NOT,
    ROUTINE_PHRASES,
    ROUTINE_WORDS,
    RULED_OUT_DETERMINER,
    RUMINATION_REPLIES,
    SAFETY_WORDS,
    SAME_AGAIN, SAME_AGAIN_WITH_THE_ANSWER,
    SCHOOL_TROUBLE,
    SCHOOL_WHO,
    SCHOOL_WORDS,
    SECRETS_KEEP_SLIPPING,
    SEEN_TO_VERB,
    SELF_BLAME,
    SELF_EATING_WORDS,
    SELF_FILLER,
    SELF_GROUP,
    SELF_JOB,
    SELF_JUDGEMENT,
    SELF_NOBODY,
    SELF_NOUN,
    SICKNESS,
    SOMEBODY_HURT,
    SOMEONE_ELSES_DAY,
    SOMEONE_GONE,
    SOMEONE_LEAVING,
    SOMEONE_SERIOUSLY_ILL,
    SORE_AMBIGUOUS,
    SORE_HANDS,
    SORE_ORDINARY,
    SORE_SERIOUS,
    SORE_WORDS,
    RETURNED_TO_A_THING,
    RETURNED_TO_IT,
    SORRY_FOR_ASKING,
    SORRY_ON_ITS_OWN,
    STATE_CUES,
    STILL_HERE_AFTER,
    STRETCH_OF_TIME,
    SUDDEN_LOSS,
    SUMMONS_RANG,
    SUMMONS_SEEN,
    SUMMONS_WRITTEN,
    SYMPTOM,
    SYMPTOM_COLD,
    SYMPTOM_WORDS,
    TAG_CONFIRM,
    TAG_UNSURE,
    TASTES,
    TASTE_GENERAL,
    TELL_HARD_LINES,
    TENANT_WHO,
    THANKS,
    THANKS_AFTER,
    THANKS_ONLY,
    THANKS_THEN_SAID,
    THANKS_WORDS,
    THANK_WORDS,
    THE_FIRST_HOUR_AND_A_CHILD,
    THING_AFTER,
    THING_STATES,
    THING_SUBJECT,
    THE_CALL_STANDS,
    THRESHOLD_CROSSED,
    THREAD,
    THREAD_PEOPLE,
    THREAD_TURNS,
    TIGHT_MONEY,
    TIGHT_MONEY_MORE,
    TIPS_AHEAD,
    TIPS_CLAUSE,
    TIPS_LINES,
    TIPS_OWNER,
    TIPS_THING,
    TIPS_UNIT,
    TIPS_VERB,
    TIRED,
    TOO_MUCH,
    TOO_MUCH_PHRASES,
    TRADER_WORDS,
    TRADES_WHO,
    TRADE_OFF_LEAN,
    TREATMENT_HARM,
    TRIED_HELPED_ELSEWHERE,
    TRIED_HELPED_REPLIES,
    ELDER_AID_REPLIES,
    ELDER_CLINIC_REPLIES,
    ELDER_DOCTOR_REPLIES,
    ELDER_HELP_REPLIES,
    TRIED_IT_REPLIES,
    TRIED_NO_CHANGE_ELSEWHERE,
    TRIED_SORTED_REPLIES,
    TRIED_NO_CHANGE_REPLIES,
    TRIED_WORSE_ELSEWHERE,
    TRIED_WORSE_REPLIES,
    TROUBLE_CUES,
    UNKNOWN,
    UNKNOWN_ABOUT_A_PET,
    UNKNOWN_ABOUT_SOMEONE,
    UNKNOWN_DECIDE,
    UNKNOWN_HEALTH,
    UNKNOWN_MONEY,
    UNKNOWN_REALISTIC,
    UNKNOWN_REALISTIC_CARE,
    UNKNOWN_TOO_LATE,
    UNKNOWN_WHO,
    UNKNOWN_WORD,
    UNKNOWN_WORD_NAMED,
    UNKNOWN_WEIRD_BARE,
    UNKNOWN_WORRY,
    VERDICT_ANNOY,
    VERDICT_BAD,
    VERDICT_FIRST,
    VERDICT_HEAVY,
    VERDICT_LUCK,
    VERDICT_NUMB,
    VERDICT_QUEUE,
    VERDICT_ROUGH,
    VERDICT_SETBACK,
    VERDICT_SHAME,
    VERDICT_WORD,
    VET_WHO,
    VIEW_AFTER_A_DEATH,
    VIEW_ASK_LINES,
    VIEW_COMPANY,
    VIEW_DECIDE,
    VIEW_HANDBACK,
    VIEW_LEAD_IN,
    VIEW_LINES,
    VIEW_MIRROR_LINES,
    VIEW_NO_SUBJECT,
    VIEW_ONLY_WORDS,
    VIEW_ON_GOOD_NEWS,
    VISIT_PRONOUNS,
    WALKED_INTO_POOL,
    WASNT_THERE,
    WHERE_SOMETHING_WRONG,
    WHOLE_LIST_AFTER,
    WHO_TO_ASK,
    JOINT_WORDS,
    _ASKS_ABOUT_THE_JOINT,
    _CHOOSING_BETWEEN_TWO,
    WHY_AFTER_TASTE,
    WILD_BIRDS,
    WIN_IN_A_SILENCE,
    WITH_YOU_AFTER,
    WORDING_LINES,
    WORD_ANYWHERE,
    WORD_FIXES,
    WORK_ABOUT,
    WORK_WHO,
    WORRY_FILLER,
    WORRY_WORDS,
    YOURS,
    YOU_SUBJECTS,
    _A_PERSON,
    _A_SOCIAL_THING,
    _BOUNDED,
    _COPULA,
    _CREATIVE,
    _DAY_WORDS,
    _ECHO_FILLER,
    _ISSUER,
    _MONEY_NOUN,
    BODY_IS_NOT_A_MACHINE,
    _NOT_AN_OWN_THING,
    _NO_DAY_OF_THEIR_OWN,
    _OPENING_QUESTIONS,
    _START_ASK,
    _SUBJECT_AFTER_AM,
    _THING_DONE_LINES,
    _THREAD_PEOPLE,
    _VERDICT_DET,
    _VERDICT_LEAD,
    _WAS,
    _WOUND,
)

from .fallback_data import (
    # Moved out of this file whole: the tables are unchanged, and the names come back under the
    # same ones. The rating of a skill, the slip and the moment after it are one reading, so they
    # went together.
    WOULD_HAVE_BEEN,
    RATES_A_SKILL,
    A_HEDGED_RATING,
    I_RATE_A_SKILL,
    SELF_SUBJECT,
    SELF_BLAME_ASKS,
    EMBARRASSMENT_WORD,
    THE_GROUND_OPENS,
    DIE_OF_IT,
    GOING_TO_DIE,
    SOMEONE_ELSES_SHAME,
    A_VERDICT_ON_THE_PERSON,
    THE_MOMENT_IS_THEIRS,
    A_SLIP,
    A_SOCIAL_SLIP,
    A_SLIP_IS_NOT_A_FALL,
    IN_A_ROOM,
    LAUGHED_AT_THEM,
    A_CROWD_LAUGHED,
    A_PERSON_LAUGHED,
    LAUGHED_AT,
    EMBARRASSED,
    NOTHING_SAID_YET,
)
from .fallback_data import (
    # Moved out of this file whole: the tables are unchanged, and the names come back
    # under the same ones.
    ABSENCE,
    A_WAY_OF_BEING,
    BARE_PICK_LOST,
    DITHER_SUBJECT,
    HABIT_PROBLEM_ACT,
    HEAVY_NEWS,
    HURT_EVENT,
    LEFT_BEHIND,
    NAMED_BODIES,
    NOT_WHAT_I_SAID,
    NUMBER_PLACES,
    ONLINE_ASK,
    PASSED_OUT,
    PASSING_OUT_A_THING,
    PRIVACY_ASK,
    PRIVACY_SHAPES,
    THE_DAY,
    THE_DAY_AHEAD,
    WORDING_SOMEONE,
    _LANDED,
)


def _bounded(phrase):
    """A phrase matched as whole words, so "raining" is not "training"."""
    pattern = _BOUNDED.get(phrase)
    if pattern is None:
        pattern = _BOUNDED[phrase] = re.compile(r"(?<![a-z])" + re.escape(phrase)
                                                + r"(?![a-z])")
    return pattern


def _has(clean, phrases):
    """True when the line mentions one of these phrases as whole words: "raining" must not
    match "training", and "the score" must not match "the scoreboard" by accident."""
    for phrase in phrases:
        if _bounded(phrase).search(clean):
            return True
    return False


def _plain(clean):
    """The line without filler words, for phrase matching."""
    return " ".join(word for word in clean.split() if word not in FILLERS)


def _matchable(text):
    """The line as a phrase table can see it: lowercase, no apostrophes, single spaces.

    A phrase is written for the standard spelling and people do not type it: "hows your day"
    for "how's your day", "whats the time" for "what's the time". The apostrophe is the one
    mark a phrase table and a typed line disagree about most, so both sides of a match drop
    it and "hows your day going" is found."""
    text = str(text or "").lower().replace("\u2019", "'").replace("'", "")
    return " ".join(text.split())


def _asks_how_are_you(clean, repaired=""):
    """True when the line's own question is how the bot is, so the manners pool fits.

    The phrase has to be the ask, not words inside a bigger question: "Hi! How's your day
    going?" asks it, and "how are you supposed to say no to your boss" does not - that one
    is a question about the boss, and "can't complain" answers nothing. So the phrase counts
    only when nothing follows it but a tag ("today", "mate") or punctuation. A greeting in
    front of it is fine. `repaired` is the same line with its wrong words put right, which
    only ever adds a reading: "hows ur day going" is the manners question as much as the
    standard spelling is."""
    forms = [_matchable(clean)]
    if repaired and _matchable(repaired) != forms[0]:
        forms.append(_matchable(repaired))
    for form in forms:
        for match in HOW_WAS_YOUR_TIME.finditer(form):
            if _nothing_but_tags(form, match.end()):
                return True
        for phrase in HOW_ARE_YOU_ASKS:
            for match in _bounded(_matchable(phrase)).finditer(form):
                if _nothing_but_tags(form, match.end()):
                    return True
        for phrase in HOW_ARE_YOU_GOING_ON:
            for match in _bounded(_matchable(phrase)).finditer(form):
                tail = form[match.end():]
                # "my daughter is 7 going on 8", "im 41 going on 42", "she is 3 going on 13": the
                # figure after the phrase is the age they are going on to, and the phrase is the
                # way an age is said, not the manners question. The tag test below reads letters
                # only, so the figure is invisible to it and the whole line was answered as small
                # talk ("I'm well, thanks. What are you up to today?").
                if re.search(r"\d", tail):
                    continue
                after = " ".join(re.findall(r"[a-z']+", tail))
                if after in HOW_ARE_YOU_GOING_ON_AFTER:
                    return True
        for pattern in (YOUR_DAY_ASK, YOUR_TIME_ASK):
            for match in pattern.finditer(form):
                if _nothing_but_tags(form, match.end()):
                    return True
    return False


def _nothing_but_tags(form, end):
    """True when what follows the phrase is only a tag, so the phrase is the whole question."""
    return all(word in HOW_ARE_YOU_TAGS for word in re.findall(r"[a-z']+", form[end:]))


# Only a line that is nothing but the handback, because "i cant decide between two jobs" and "i
# dont mind but my partner does" are things to talk about rather than an offer to take. The polite
# openers and the trailing softeners are what people put round it, so they come off before the
# test rather than being matched twice.
HANDS_IT_BACK = re.compile(
    r"^(?:(?:o+k+(?:a+y+)?|right|so|well|then|h+m+|ha|ha+ha|please|ta|cheers|and|dunno)[, ]+)*"
    r"(?:(?:i |i'm |im )?(?:dont|don't|do not) (?:mind|care)[, ]+(?:so )?)?"
    r"(?:"
    r"(?:you|u|youre|you are|your) (?:pick|choose|decide|call it|the call|the choice|call"
    r"|choice|decision|expert|boss|shout)(?: (?:one|the one|one of them|then|first))?"
    r"|(?:you|u) (?:can|could|may|should) (?:pick|choose|decide|have (?:it|this|that))"
    r"|(?:ill |i will |i'll )?(?:let you|leave it to you|leave this to you|leave that to you)"
    r"(?: (?:pick|choose|decide|have (?:it|this|that)|take (?:it|this|that)))?"
    r"|(?:you|youve|you have) got (?:this|it|this one|that one)"
    r"|(?:its |it is |thats |that is )?(?:up to you|over to you|down to you|your call"
    r"|your shout)"
    r"|(?:youre|you are) (?:the (?:expert|boss|one who knows)|better at this)"
    r"|(?:whichever|whatever) (?:you|u) (?:think|want|like|prefer|reckon|say)"
    r")"
    r"(?:[, ]+(?:then|please|for me|really|honestly|ha|haha))*"
    r"\s*[.?!:)]*\s*$")

# A question about ringing for help is not a decision to weigh, and it is the one question the
# bot must never hand back: the person is asking whether this is serious enough to act on, and
# "can't call that one for you, sorry - say what you'd lose either way" was the answer to
# "should i call an ambulance", "should i ring an ambulance", "should i call 999" and
# "should i call the police". A friend settles it in one word and then says what to do with the
# phone in their hand.
EMERGENCY_CALL = re.compile(r"\b(?:ambulance|paramedic|paramedics|999|911|112|fire brigade|"
                            r"fire service|fire engine|coastguard|lifeboat|mountain rescue|"
                            r"a&e|a and e|casualty|resus|defibrillator)\b")
# `law` on its own made every degree question a police question: "should i go to law school"
# was answered "ring 999 if it is happening now". Only the phrases that name the police: the
# subject of a degree is not a call to make (clean-sage, #4381).
POLICE_CALL = re.compile(r"\b(?:police|cops|101|law enforcement|the law)\b")
# The police word is the subject of far more lines than it is a call to make, and a question
# that mentions them is not a question about ringing them: "did the police come", "did the
# police do anything", "is it against the law to park there", "whats the law on fireworks" and
# "did the law pass" were all handed "999 now, for anything happening or anyone in danger" at
# main. A line that wants a number names the act of getting in touch with them ("should i call
# the police", "should i report it to the police", "should i go to the police about my ex"), so
# the police branch asks for that verb as well as the name. `did` on its own, which is all the
# legal question has, is not one.
REACHING_THE_POLICE = re.compile(
    r"\b(?:call|calls|called|calling|ring|rings|rang|ringing|dial\w*|phone|phones|phoned|phoning|"
    r"report|reports|reported|reporting|tell|tells|telling|told|contact|contacts|contacted|"
    r"speak|speaks|speaking|spoke|talk|talks|talking|talked|go|goes|went|going|involve\w*|"
    r"ask|asks|asked|asking)\b")
# "Do i need the police" and "do i want the police involved" leave the act out, so `need` is not
# a verb of contact on its own: "the law needs to change" would otherwise be read as a call to
# make, and so would "i need to know about the law" (the name has to come after the ask, which
# is what a person says when they are asking for them). "get" is in it for "can i get the police
# to come", not for "how do i get into law enforcement", where the words after it are not the
# police but a way in.
_ASKING_FOR_THE_POLICE = re.compile(
    r"\b(?:need(?:s|ed)?|want(?:s|ed)?|get|gets|getting|got)\s+"
    r"(?:to\s+(?:\w+\s+)?)?(?:the\s+|a\s+|an\s+)?(?:police|cops|law enforcement)\b")
# The other half of the same guard: a line that names something happening to them keeps the card
# with no verb of its own ("the police" is the answer whether or not the line says "ring"). The
# words are a crime or a person at the door, not a symptom, so a legal question has none of them.
SOMETHING_HAPPENING = re.compile(
    r"\b(?:broke|broken|breaking|break\s?in|break-ins|burgl\w*|intruder|trespass\w*|"
    r"attacked|attacking|assault\w*|"
    r"threat\w*|stalk\w*|follow(?:ing|ed) me|chased|mugged|robbed|vandal\w*|smash\w*|"
    r"hit me|hurled|hitting me|abusive|in my (?:house|home|flat|garden|shed|garage)|"
    r"outside my (?:door|house|flat))\b")
# The line has to be asking what to do, not reporting a call already made: "i called 999
# yesterday" is a story, and answering it with "ring 999 now" would be absurd.
_ASKS_TO_ACT = re.compile(r"^\s*(?:should|shall|do|did|would|will|is it|do (?:you|u)|"
                          r"would (?:you|u)|can (?:you|u)|could (?:you|u)|am i)\b"
                          r"|\b(?:should i|need an?|worth calling|better to call)\b"
                          # The ask can come after the story: "i was burgled, do i need the
                          # police" asks the same question as "should i call the police" and was
                          # let past for naming the person instead of opening with the verb.
                          r"|\b(?:do|should|shall|would|will|did|can|could|am|are)\s+(?:i|we)\b")
# "Should i call an ambulance" is settled by a friend in one word, but "for a stubbed toe" is not
# that question: the dangerous-sounding word is in the line and the thing named is nothing. A
# minor complaint named in the line, with no danger symptom beside it, takes the emergency answer
# back to the ordinary one (swift-goat, #4381).
MINOR_HARM = re.compile(
    r"\b(?:stubbed|stubbing|paper cut|papercut|splinter|blister|blisters|hiccups?|dandruff|"
    r"verruca\w*|stye|athlete'?s foot|nappy rash|stitch|bruise[sd]?|bumped|graze[sd]?|grazed|"
    r"nicked|chapped|chafing|sunburn|hangover|ingrown|head ?lice|nits|cold|colds|cough|coughs|"
    r"sneez\w*|hayfever|hay fever|toothache|earache|sore throat|heartburn|indigestion|"
    r"constipat\w*|piles|sprain(?:ed)?|twisted ankle|scratched|insect bite|mosquito bite)\b")
# A symptom that keeps the emergency answer even when a small word is in the line: "should i call
# an ambulance - my toe is stubbed but he is not breathing" is still an emergency.
DANGER_SYMPTOM = re.compile(
    r"\b(?:can'?t|cannot|not|isn'?t|stopped|struggling to|finding it hard to)\s+breath(?:e|ing)\b"
    r"|\b(?:not|never|isn'?t|un)\s*(?:responding|responsive|conscious)\b"
    r"|\b(?:chest pain|crushed|crushing|severe|heavy bleeding|bleeding (?:a lot|badly)|"
    r"won'?t stop|no pulse|seizure|fitting|overdose|took (?:too many|an overdose)|"
    r"stroke|anaphyla\w*|throat (?:closing|swelling)|blue lips|stopped breathing)\b")
# A place you are seen at is not a thing you ring, and the two decisions are different: "should i
# go to a&e for a cut" was answered "call 999 or 911 straight away" because `a&e` sits in the
# emergency list, which is an over-escalation and does not answer the question. Going is the plan;
# the phone is for the case that turns worse on the way. The place words only count as something
# to ring when the line has a calling word of its own in it ("should i call casualty").
_A_PLACE_TO_BE_SEEN = re.compile(r"\b(?:a&e|a and e|casualty|resus)\b")
_A_CALL_WORD = re.compile(r"\b(?:call|calls|calling|called|ring|rings|ringing|rang|phone|"
                          r"phoning|dial|dialling|dialing|999|911|112)\b")

# A small social decision - whether to send the message, ring round, go to the thing, say sorry -
# has a default a friend would give: do it, keep it short, and here is what the other way costs.
# "Should i text him first" was answered "not mine to decide, sorry", which is a wall in front of
# the most ordinary question in the language. Money and health keep their own pools (they are
# checked first) because there a wrong default does real harm.
_CONTACT = re.compile(r"\b(?:text|txt|ring|call|phone|message|msg|dm|email|mail|reply|answer|"
                      r"write|whatsapp|facetime|contact|reach out)\b")
AN_APOLOGY = re.compile(r"\b(?:say sorry|apologise|apologize|make up|make it up|own up|forgive me)\b")
ASKED_OUT = re.compile(r"\bask(?:ed)? (?:him|her|them|\w+) out\b|\bask (?:him|her|them) out\b")
# It has to be a thing you go to: "should i pay for my mates meal" is a money question and
# "should i do a dinner party" is about cooking, and neither is a decision about turning up.
_GOING = re.compile(r"\b(?:go|goes|going|attend|turn up|show up|make it)\b")
# "Yes, go" is the default for a wedding you have been asked to, and it is advice a friend would
# take back for one you were not: the decision there is whether to ask, not whether to turn up.
# (sky-tuna, #4381.)
_NOT_INVITED = re.compile(
    r"\b(?:wasnt|was not|werent|were not|havent been|have not been|didnt get|did not get|"
    r"no|not|never got|never received)\s+(?:\w+\s+){0,2}invit\w*"
    r"|\buninvited\b|\bwithout an invit\w*\b|\bgatecrash\w*\b", re.I)
# The reply has to match the act the line names: "should i ring my mum" answered "reply, and
# keep it to the one thing you want back" tells them to do something else.
_CALLING = re.compile(r"\b(?:ring|ringing|call|calling|phone|phoning|facetime|phone up)\b")


# A decision the person states instead of asking: "i'm not sure whether to move in with her",
# "i dont know if i should take the job", "i cant decide between the two flats". The question is
# in the line the other way round, so DECIDE_OPENING - which opens on "should i" - never sees it,
# and the line fell to the echo or the neutral nod: "Your girlfriend wants to move in and you're
# not sure - I'll remember that" files away the one thing the person asked for help with. The
# pool goes straight to what would move the decision, because the person has already said the
# thing UNKNOWN_DECIDE would say back to them.
DITHER = re.compile(r"\b(?:not sure|unsure|dont know|do not know|no idea|cant decide|"
                    r"cannot decide|cant make up my mind|cannot make up my mind|torn between|"
                    # "torn" without "between" is the same state and the commonest way to say it:
                    # "im torn about moving to leeds" named no sides, so it was filed away as a
                    # fact ("Noted: you're torn about moving to leeds").
                    r"(?<!not )torn about|(?<!not )torn over|(?<!not )torn on|"
                    r"(?<!not )torn|conflicted|dithering|undecided|"
                    r"in two minds|two minds about|of two minds|going back and forth|"
                    r"keep changing my mind)\b")
# "torn between", "in two minds", "cant make up my mind" can only be about a decision, so they
# carry the line on their own - including a bare "about <thing>" after them ("i cant make up my
# mind about the kitchen"), which on its own is not a decision at all: "im not sure about the
# paint colour" is a taste, and "i dont know about you but im starving" is a set phrase
# (rust-dial's read).
# "torn" only carries the line when the person is the one who is torn, because the same word is
# said of a thing that is ripped: "the page is torn", "my coat is torn" and "her dress is torn
# about the hem" are a repair, and "the tent is torn on the corner" is a hole in a tent. The
# preposition after it does not tell them apart - a person is torn about a job and a sheet is torn
# about here, in the same words - so the subject is what does, and it has to be a person saying
# "i", "we", "he", "she", "they" or "you" with the word, or a thing's own state ("seems torn",
# "sounds torn") about somebody. "torn apart" is left out for the same reason the other side is:
# it is grief, not two sides of a choice (spare-leopard's read).
DITHER_STRONG = re.compile(r"\b(?:(?<!not )torn between|"
                          r"(?:i|im|i m|i am|i was|i ve been|ive been|i feel|i felt|feel|"
                          r"feeling|we|we re|we are|we were|he|he s|he is|he was|she|she s|"
                          r"she is|she was|they|they re|theyre|they are|they were|you|"
                          r"you re|youre|hes|shes|"
                          r"you are|you were|seems|seemed|sounds|sounded|felt)\s+"
                          r"(?:so\s+|really\s+|very\s+|quite\s+|a bit\s+|still\s+)?"
                          r"torn\b(?! apart)|"
                          r"conflicted|dithering|undecided|two minds|"
                          r"going back and forth|cant decide|"
                          r"cannot decide|cant make up my mind|cannot make up my mind|"
                          r"keep changing my mind)\b")
# A doubt whose object is an open "what to do about this" names no sides at all ("i dont know what
# to do about money", "i dont know what to do next"), so neither "each way" nor "which way are you
# leaning" has anything to point at (sleek-jar on #2029). It gets a pool that asks what is in the
# way of the next step, which is what a friend says when the person has not found the choice yet.
DITHER_OPEN = re.compile(r"\bwhat to do\b|\bwhat (?:i|you) (?:should|can|ought to) do\b"
                         r"|\bwhat next\b")
# The same open doubt with the person named: "i dont know what to do about my mum", "what do i do
# about my son". `PERSON_NOT_A_DECISION` keeps these off the weighing pools on purpose - a person
# is not two sides to pick between - and what was left answered them with the echo ("I'm
# listening - say more if it helps") or the nod. The person is in the line, so the one helpful
# thing a fallback can do is ask about them.
# The person said with the words that describe them: "my teenage son", "our eldest daughter",
# "my 14 year old son", "my elderly mum". Those were named in the line and the pool asked about
# nobody ("I dont know enough... a quick search online"), because the reading expected the person
# straight after "about". Up to three words of description are allowed, and the tail check below
# keeps the pool off a line whose subject is a thing ("my sons school", "my child benefit").
STUCK_ON_A_PERSON = re.compile(
    r"\b(?:what to do|what (?:i|you) (?:should|can|ought to) do|"
    r"what (?:do|should|shall|can|could) (?:i|you|we) do)\s+(?:about|with)\s+"
    r"(?P<who>"
    r"(?:(?:my|our)\s+(?:[a-z0-9']+\s+){0,3})?"
    # The in-law forms come first: "mother" alone would take "my mother in law" and ask about
    # a mother the person never mentioned.
    r"(?:mother in laws?|father in laws?|sister in laws?|brother in laws?|"
    r"son in laws?|daughter in laws?|in laws|inlaws|husband|wife|partner|boyfriend|girlfriend|"
    r"brother|sister|son|"
    r"daughter|child|kid|boy|girl|baby|mum|mom|mother|dad|father|nan|gran|grandma|grandad|"
    r"grandpa|grandmother|grandfather|grandparents|grandson|granddaughter|friend|mate|boss|"
    r"colleague|neighbour|neighbor|in laws|inlaws|teenager|family|"
    r"teacher|carer|relative|cousin|uncle|aunt|nephew|niece|stepson|stepdaughter|ex)|"
    # A child named only by age is still a person: "our 2 year old", "my 18 month old". This is
    # read after the described form, so "my 14 year old son" keeps the son, and the tail check
    # stands the pool down when the age belongs to a thing ("our 2 year old car").
    r"(?:my|our)\s+\d+\s+(?:year|month|week)s?\s+old)"
    # The person must end a word: without this, "my son that school expelled" read the "ex" in
    # "expelled" as the person ("What is going on with your son that school ex at the moment?").
    r"(?![a-z0-9])"
    r"(?P<rest>.*)$")
# What may follow the person without changing who the line is about: "my ex now", "my son
# though", "my mum at the moment", or a second person named with them ("my son and my daughter").
# The tail is read as phrases from the front, not as a bag of single words: "at the moment",
# "at the minute", "right now" and "these days" are how the commonest forms of the question are
# said, and every one of them is more than one word (handy-lily's read). Read as single words,
# "what do i do about my mum at the moment" lost the answer the bare "my mum" already had.
STUCK_PERSON_TAIL_PHRASE = re.compile(
    r"^(?:"
    r"at the moment|at the minute|at the mo|at present|at this point|as it stands|"
    r"right now|just now|these days|nowadays|currently|"
    r"and thats it|thats it|i mean|i suppose|i guess|of all things|"
    r"now|today|tonight|though|then|please|anymore|any more|first|just|still|about|too|"
    r"either|really|honestly|seriously|actually|like|again|lately|all|eventually|so|and|"
    r"or|ok|okay|basically|thanks|cheers|please|now though|then though)"
    r"(?![a-z0-9])", re.I)
# A comma clause is about the same person when it says something of them rather than of a thing
# of theirs: "my boy, he is 15", "my daughter, she started school", "my son, 15". The subject
# has to be the person (he, she, they) or an age; "my son, his school" names a thing and stands
# the pool down, the same way the bare "my sons school" does.
STUCK_A_CLAUSE_ABOUT_THEM = re.compile(
    r"^,\s*(?:"
    r"(?:he|she|they|him|her|them)\b[ a-z0-9']{0,48}"
    r"|(?:aged|age)\s+\d{1,3}"
    r"|\d{1,3}\b[ a-z0-9']{0,24}"
    r")$")
STUCK_AND_ANOTHER_PERSON = re.compile(
    r"^(?:,\s*)?(?:and|or)\s+(?:(?:my|our)\s+)?[a-z0-9']+(?:\s+[a-z0-9']+){0,3}$")
# A tail that says more about the same person is still about them: "my ex that keeps texting me",
# "my partner of ten years", "my mum who wont go to the doctor". The words describe who they are
# to the person talking, not a thing of theirs, so the pool that asks about them is the right
# reply and standing it down was a regression (it used to ask "What is going on with your ex?").
STUCK_DESCRIBES_THE_PERSON = re.compile(
    r"^(?:,\s*)?(?:"
    r"(?:that|which|who|whose|whos|who's)\b[ a-z0-9']{0,40}"
    r"|(?:of|been|together|married)\b[ a-z0-9']{0,24}"
    r")$")


def _the_person_ends_the_ask(rest):
    """True when what follows the person is about the person, not a thing of theirs."""
    # Only the punctuation at the end is dropped: a comma at the front is the clause's own
    # opening ("my boy, he is 15") and `STUCK_A_CLAUSE_ABOUT_THEM` reads it.
    rest = str(rest or "").lstrip(" ").rstrip(" ?.!,")
    if not rest.strip(" ,?!."):
        return True
    if STUCK_AND_ANOTHER_PERSON.match(rest):
        return True
    if STUCK_DESCRIBES_THE_PERSON.match(rest):
        return True
    if STUCK_A_CLAUSE_ABOUT_THEM.match(rest):
        return True
    left = rest
    while True:
        found = STUCK_PERSON_TAIL_PHRASE.match(left)
        if not found:
            break
        left = left[found.end():].lstrip(" ,?!.")
    return not left


def _the_person_they_are_stuck_on(clean):
    """The person named in "i dont know what to do about my mum", faced back at them."""
    found = STUCK_ON_A_PERSON.search(clean)
    if not found or not _the_person_ends_the_ask(found.group("rest")):
        return ""
    who = _yours(found.group("who"))
    # `_yours` faces "my" back at the person but leaves "our": "what do i do about our son" came
    # back as "our son", which is the pair's child said by the wrong one of them.
    if who.lower().startswith("our "):
        who = "your " + who[4:]
    return who


# A line that is nothing but the stuck phrase: "i dont know what to do", "no idea what to do
# next", "i have no idea what to do anymore". Every word left after the doubt is filler, so the
# line names nothing for any later pool to read - which is the test, because "this job is getting
# me down and i dont know what to do" is the wearing-down pool's line and has to keep it.
STUCK_ONLY_WORDS = frozenset("""
i im ive dont do not know have has got had no idea clue what to next now anymore any more really
even so just and but then about with still whats honestly right today hmm erm um please help
havent hasnt didnt doesnt a an at all
stuck where start begin beginning first how supposed even feeling bit feel need help
""".split())

# The words of a person with no way in: "i dont know what to do", "im stuck", "where do i start",
# "i dont know where to begin", "no idea what to do first". They name nothing and they are not a
# question about the world, so every pool here is asked rather than decided, and nothing in them
# guesses what the trouble is - the line has not said.
A_HELP_WORD = re.compile(r"\b(?:help|hand|advice)\b")

# The person saying they have run out rather than that they have no way in: "i dont know what
# else to do", "theres nothing i can do", "i dont know how to fix it", "i cant do this", "i give
# up". Read with the same "nothing else in the line" test as the stuck phrase, so "how to fix
# my boiler" is still the boiler and "i give up on my diet" is still the diet.
RUN_OUT = re.compile(
    r"\b(?:(?:what else|nothing else)(?:\s+(?:i|id|i'?d|to|can i))?\s*(?:do|can|try)\b|"
    r"what else\s*$|"
    r"nothing (?:(?:else|more) )?(?:i can do|to do|left|works?)\b|"
    r"what i can do\b|"
    r"(?:cant|cannot|can not) do (?:this|it)\b|"
    r"i give up\b|"
    r"no point(?:_in)?\b|"
    r"where to go from here\b|"
    r"how to fix (?:it|this)\b)", re.I)
# Saying the words alone is not running out: "we've seen all of fleabag and derry girls" then
# "what else" is a person asking for another series, and "what else can i do" as a first line is
# a question with no subject. The person has to say they do not know, or that nothing is left.
RUN_OUT_DOUBT = re.compile(r"\b(?:dont|do not|not|never)\s+(?:even\s+)?know\b|\bno idea\b|"
                           r"\bnot sure\b", re.I)
RUN_OUT_EMPTY = re.compile(
    r"\b(?:nothing (?:else |more )?(?:i can do|to do|left|works?)|theres nothing|"
    r"(?:cant|cannot|can not) do (?:this|it)|i give up|no point)\b", re.I)
STUCK_PHRASES = re.compile(
    r"\b(?:stuck|what to do|where (?:do|should|would) i (?:start|begin)|"
    r"(?:where|how) to (?:start|begin)|where i (?:start|begin)|"
    r"(?:what|which) (?:to do )?first|what with)\b")


# "the baby wont stop crying", "my mum has dementia", "he has not rung me back" - the line above
# names somebody or something of theirs, so the stuck line that follows is about that, whether
# or not the readings above called it bad news (a crying baby is not). A line about the person
# alone names nothing to ask about: "im 34" then "i dont know what to do" keeps the open pool.
A_SUBJECT_ABOVE = re.compile(
    r"\b(?:my|our|his|her|their|the|he|she|they|him|them)\s+[a-z]")


def _a_subject_above(memory):
    """True when the line before this one named something of theirs for the stuck line to be about."""
    if not isinstance(memory, dict):
        return False
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    if not turns:
        return False
    return bool(A_SUBJECT_ABOVE.search(str(turns[-1].get("user") or "").lower()))


def _a_bad_line_above(memory):
    """True when the line before this one was a bad one by its own words.

    "its been rough and i want to cry" names no person and no thing, so neither reading above
    finds it, and the open pool's "say what you'd want if nothing was in the way" is a strange
    thing to say to somebody who has just said that. The mood of the line is the reading that
    does find it.
    """
    if not isinstance(memory, dict):
        return False
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    if not turns:
        return False
    last = str(turns[-1].get("user") or "")
    if not last.strip():
        return False
    return _mood(_words(last), last) == "negative"


RUN_OUT_WORDS = STUCK_ONLY_WORDS | frozenset("""
else id cant cannot can not give up point left works fix it this go from here try anything
nothing theres there to
""".split())


def _run_out(clean):
    """True when the line says only that they have run out of options, and nothing else."""
    words = re.findall(r"[a-z']+", clean)
    if not words or not RUN_OUT.search(clean):
        return False
    if not (RUN_OUT_DOUBT.search(clean) or RUN_OUT_EMPTY.search(clean)):
        return False
    return all(word.strip("'") in RUN_OUT_WORDS for word in words)


def _a_dead_end(clean):
    """True for either kind of line that names nothing: no way in, or no way left."""
    return _only_the_stuck_phrase(clean) or _run_out(clean)


def _only_the_stuck_phrase(clean):
    """True when the line says only that they do not know what to do, and nothing else."""
    words = re.findall(r"[a-z']+", clean)
    if not words or not STUCK_PHRASES.search(clean):
        return False
    return all(word.strip("'") in STUCK_ONLY_WORDS for word in words)


def _a_question_about_the_person(clean, memory):
    """A question about the person they are stuck on, or None when no person is named.

    Read from the last place anything else answers, because the line is only this pool's when
    nothing in the knowledge or the thread can use it: "what should i do about my knee" is still
    the knee card, and a person's death in the thread is still the grief pool's.
    """
    who = _the_person_they_are_stuck_on(clean)
    if not who:
        return None
    return _choose([line.format(who=who, Who=who[:1].upper() + who[1:])
                    for line in DITHER_ABOUT_A_PERSON], memory, clean)

DITHER_YES_NO = re.compile(r"\b(?:whether|if)\b")
# A question about the *method* of deciding, not about a decision already on the table: "how
# should i decide", "how do i work out which one", "how do i choose". None of them names a doubt
# (so `DITHER` never sees them) and none is a fact to look up, so on main they fell through to the
# search hedge - "a quick search online will get you a solid answer" - which is wrong twice over:
# the method is general, and the bot does know it. The pool names the two questions that settle
# most of these and asks for the sides, because the sides are the one thing only the person has.
HOW_TO_DECIDE = re.compile(
    r"\bhow (?:should|do|can|could|would|might|will) (?:i|we) (?:decide|choose|pick|"
    r"work (?:it |that |this )?out|figure (?:it |that |this )?out|know which|tell which)\b"
    r"|\bhow (?:do|should|can) i (?:make|reach|come to) (?:a |the )?decision\b"
    r"|\bwhats?\s+(?:is\s+)?the best way to (?:decide|choose|pick)\b")
# A method question is about the method only when the verb ends the thought or names the sides:
# "how do i choose" and "how do i decide between the two jobs" are the method, while "how do i
# choose a wine", "how do i pick my lottery numbers" and "how do i work out my tax" name a subject
# that owns the answer - and the pool's "what are the two options?" has no two options to ask about
# in them.
SAYS_THE_SIDES = re.compile(r"\W*(?:between\b|whether\b|if\b|which (?:one|of|to)\b)")


def _nothing_to_choose(rest):
    """True when what follows "how do i decide/pick/choose" names no subject of its own."""
    if SAYS_THE_SIDES.match(rest):
        return True
    words = re.findall(r"[a-z0-9']+", str(rest or "").lower())
    return not [w for w in words if w not in HOW_TO_DECIDE_FILLER]


# A decision with two sides the person can name is weighed here: "whether to move in with her",
# "between the two flats", but also "my girlfriend wants to move in and im not sure", where the
# doubt is the decision and nobody needs to ask which two things are being weighed.
DITHER_TWO_WAY = re.compile(r"\b(?:whether|if|between|or|which)\b")
# The one class this reader passes on: a line asking for a direction rather than weighing a
# choice ("i dont know what to do with my life", "im 34 and i still dont know what i want to
# do"). There is no second side to hold up there, so "which way are you leaning" asks about a
# choice the person has not found yet. That class belongs to the neutral branch's own
# worth-and-direction pool: one pool per line class, and this one is not mine.
LIFE_DIRECTION = re.compile(r"\b(?:with|out of|from) my life\b|\bwhat i (?:actually )?want to do\b"
                            r"|\b(?:twenties|thirties|forties|20s|30s|40s)\b"
                            r"|\bnothing (?:feels|seems) right\b"
                            r"|\bwhat (?:am i|im) (?:even )?doing with my life\b")


# A stretch of free time is not a choice with two sides to weigh either. "no idea what to do with
# my afternoon" is somebody with an afternoon going spare, and "Which bit of it is heaviest?" -
# the right question for a person carrying too much - asks them to name the heavy part of a free
# afternoon. Said with a day or a weekend in it, the line already reached the pool that gives the
# day a shape; the afternoon was the one form that did not.
A_STRETCH_OF_TIME = re.compile(
    r"\bwhat (?:to|should i|can i|could i|shall i) do (?:with|on|for)\s+(?:my|the|this|these)\s+"
    r"(?:afternoon|evening|morning|day off|day|weekend|week|time|night|days off|holidays?)\b")


def _the_stretch_of_time(clean, memory):
    """A question about the free afternoon, or None when the line is not that.

    "no idea what to do with my afternoon" is somebody with an afternoon going spare, and the two
    doors it can reach - the ask for a hand with nothing named (the search hedge) and the doubt
    with two sides (the question for a person carrying too much) - are both the wrong reply. Said
    with a day or a weekend in it, the line already reaches the pool that gives the day a shape
    before either door, so this only ever sees the afternoon.
    """
    if not A_STRETCH_OF_TIME.search(clean or ""):
        return None
    return _choose(A_FREE_TIME_ASK, memory, clean)


def _weighs_a_choice(clean):
    """True when the doubt has sides the person can name, so weighing it helps.

    A life-direction line has none ("i dont know what to do with my life") and neither does a free
    afternoon, and this reader passes on both rather than asking which way the person is leaning:
    the rest of `reply_for` - the echo and the neutral pool - still answers them, and further down
    the line the pools that give a day a shape read them.
    """
    if DITHER_TWO_WAY.search(clean):
        return True
    return not (LIFE_DIRECTION.search(clean) or A_STRETCH_OF_TIME.search(clean))


# "the difference between the two", "the gap between them", "the time between the trains": a
# "between" inside a fact is not two sides to weigh, and "i dont know the difference between the
# two" was being asked "What's pulling you each way?" - a real question answered with a shrug.
FACT_BETWEEN = re.compile(r"\b(?:difference|differ|gap|distance|space|time|line|border|"
                          r"connection|link)\s+(?:\w+\s+)?between\b")


# A service you go to for help is not one side of a decision. "not sure whether to go to a and
# e" and "im not sure whether to take him to the vets tonight" are someone asking what to do
# about a body, and "What's the thing you would lose if you said yes?" answers a trade-off nobody
# named (warm-feather on #1467). Only a motion towards the service counts: the hospital job is
# still a job, and "should i move to be near the hospital" is still a move.
HELP_SERVICE = re.compile(
    # "take the hospital job" is a job, so a motion verb only counts when the service is where
    # the person is going: the "to" is what makes it a destination.
    r"\b(?:go|going|went|get|getting|take|taking|took|bring|bringing|drive|driving|rush|rushing|"
    r"walk|walking)\b(?:\s+\w+){0,3}?\s+(?:to\s+|into\s+)"
    r"(?:a and e|a&e|999|111|casualty|the hospital|hospital|the doctor|a doctor|doctor|"
    r"the doctors|doctors|the gp|gp|my gp|the surgery|the vets|vets|the vet|vet|"
    r"walk in centre|urgent care|out of hours|the pharmacy)\b"
    # and a call or a visit names the service as its object, with no "to" at all.
    r"|\b(?:call|called|calling|ring|ringing|rang|phone|phoned|phoning|see|seeing|saw|book|"
    r"booking|booked)\b\s+(?:999|111|an ambulance|the doctor|a doctor|the gp|the surgery|"
    r"the vets|the vet|a vet|urgent care)\b")
# A person is not a decision object either: "what to do about my husband" is a row to talk
# through, not two versions of the same day (warm-feather and gray-cypress on #1467), and "what
# to do about it" has no it to weigh. "about money" still is a decision: something can be done
# with money. This is a check on the object, so the cue itself stays whole.
PERSON_NOT_A_DECISION = re.compile(r"\bwhat to do (?:about|with) (?:my|his|her|our|their|the)\s+"
                      r"(?:husband|wife|partner|boyfriend|girlfriend|brother|sister|son|"
                      r"daughter|child|kid|boy|girl|baby|mum|mom|mother|dad|father|nan|gran|"
                      r"grandma|grandad|grandpa|friend|boss|colleague|neighbour|neighbor|"
                      r"in laws|inlaws|teenager|family|teacher|carer|relative|cousin|uncle|"
                      r"aunt|nephew|niece|ex|stepson|stepdaughter)\b")
# "i dont know what to do about it" / "about that": a pronoun is the thing already mentioned,
# not two ways out, so the line wants a conversation rather than a weighing.
PRONOUN_NOT_A_DECISION = re.compile(r"\bwhat to do (?:about|with) (?:it|this|that|him|her|them|us|me|"
                       r"everything|anything|nothing)\b")


# A health word can be a place or a thing rather than a body: "i dont know whether to take the
# hospital job" is a job, and the advisor's line ("Ring 111 or your surgery") answers a body.
HEALTH_MODIFIER = re.compile(r"\b(?:hospital|doctors?|surgery|clinic|vets?)\s+"
                             r"(?:job|jobs|shift|shifts|appointment|appointments|letter|"
                             r"letter|bill|parking|car park|contract|rota|placement|course|"
                             r"uniform|policy|department|ward)\b")


def _reads_as_dither(clean, repaired=None):
    """True when the line says a decision is unresolved, rather than asking which way to go.

    The line is read as it was typed and then with its words put right. "i dont no what to do
    about my job" is "dont know" with a word typed for the sound of it, and only the repaired
    line spells "know": read as typed the doubt was invisible, so the line went past every pool
    to the neutral nod ("Thanks for telling me - I'm here if you want to dig into any of that")
    while the same line typed with "know" answered it. The refusals are per spelling, so a line
    that is not a doubt either way stays as it was.
    """
    lines = [clean]
    if repaired and repaired != clean:
        lines.append(repaired)
    for line in lines:
        if FACT_BETWEEN.search(line):
            continue
        if (PERSON_NOT_A_DECISION.search(line) or PRONOUN_NOT_A_DECISION.search(line)
                or HELP_SERVICE.search(line)):
            continue
        if DITHER.search(line) and (DITHER_STRONG.search(line) or DITHER_SUBJECT.search(line)):
            return True
    return False


# A decision question opens with the decision ("should I", "is it worth"). "What should I know",
# "when should I plant tulips" ask for information, so they stay with the fact pool.
#
# "Do I <say / tell / ask / text / call ...>" is the same decision in the present tense: "do i
# accept the offer" and "do i say yes" are asking the bot to pick a side, and the search hedge
# ("I'm not sure about that one, sorry - a quick search will get you a solid answer") is no help
# with a choice that is the person's own. Only the verbs that name an act of their own are here,
# and only straight after "do i": "do i need to tell the council" is a question about the rules
# and keeps its hedge, which is why nothing may come between "do i" and the verb. "go" and
# "write" are out on purpose - "do i go" names nothing at all, and the pools behind it guess an
# evening out ("an evening out costs less than the regret"), while "do i write to them" reaches
# the drafting pool and assumes a draft nobody said they had.
DECIDE_OPENING = re.compile(r"(?:^|[,.!?;]\s*|\b(?:so|but|then|and|ok|okay)\s+)"
                            r"(?:should (?:i|we)|shall (?:i|we)|is it worth|is it better|"
                            r"would it be better|"
                            r"which (?:one )?should i|(?:do |)(?:you|u|ya) (?:think|reckon) i should|"
                            r"what would you do|"
                            r"do i (?:say|tell|ask|mention|reply|text|call|ring|accept|"
                            r"send|bring)\b|"
                            r"would you)\b")
# A decision is also asked the other way round, as a check on the asker's own sanity: "would
# moving closer be mad", "would it be weird to go back to college at 40", "is it stupid to buy a
# new one", "would i be mad to sell", "would it look bad if i said no". None of those names a
# fact to look up, and main sent them to the search hedge - "Searching for it will turn up better
# sources than I can offer" - which is no help with a choice that is the person's own. The word
# that carries the question is the verdict on the asker (mad, weird, stupid, selfish, rude), so it
# is that word the pattern asks for, wherever the sentence puts it.
DECIDE_SANITY = re.compile(
    # "would moving closer be mad", "would it be weird to go back to college at 40", "would a
    # tattoo look stupid" - a modal with the verdict on the thing the person is weighing.
    r"\b(?:would|will|does|do|is|was|are)\b[^.?!]{0,34}?\b(?:be|look|seem|sound)\s+"
    r"(?:like\s+)?(?:a\s+|an\s+)?(?:mad|crazy|stupid|silly|nuts|weird|strange|odd|bizarre|"
    r"selfish|unreasonable|rude|cheeky|bad|wrong|over\s+the\s+top|a\s+mistake)\b"
    # "am i being stupid", "am i unreasonable about this", "was i out of order"
    r"|\b(?:am|are|was)\s+(?:i|we)\b[^.?!]{0,20}?\b(?:being\s+|just\s+|so\s+|too\s+)?"
    r"(?:mad|crazy|stupid|silly|selfish|unreasonable|a\s+fool|out\s+of\s+order|"
    r"over\s+the\s+top)\b"
    # "is it mad to get a dog", "would it be a bad idea to just stop paying"
    r"|\b(?:is|would|was)\s+it\s+(?:mad|weird|stupid|silly|crazy|a\s+mistake|a\s+bad\s+idea|"
    r"wrong)\s+to\b"
    # "mad idea to...", "weird thing to say"
    r"|\b(?:mad|weird|stupid|silly|crazy)\s+(?:idea|thing)\s+to\b"
    # "would it look bad if i said no", "does it look bad to turn it down"
    r"|\b(?:would|does|will|did)\s+(?:it|that|this)\s+look\s+(?:bad|silly|stupid|mad|odd|"
    r"weird|rude)\b"
    # "is it weird that i want to move": the verdict on the feeling rather than on the act
    r"|\b(?:is|was|would)\s+it\s+(?:weird|strange|odd|stupid|silly|crazy|mad|selfish|"
    r"unreasonable)\s+that\b")

# "What's a password manager and should I use one?" asks for a fact first: the decision is the
# second half of the line, so the fact pool stays.
_DEFINITION = re.compile(r"^\s*(?:what|what's|whats|wats)\s+(?:is|are|was|were|does|do)\b"
                         r"|^\s*what(?:'s|s)?\s+(?:a|an|the)\b"
                         r"|^\s*(?:explain|tell me about|define)\b|\bwhat does .* mean\b")
# Where a person says a thing on the body is, they have said it is on the body. "on" alone is not
# enough - "a spot on the map" - so the word after it has to be one a body can own.
SORE_PLACE = re.compile(
    r"\b(?:my|under my|behind my|between)\b"
    # "should i pop this spot" points at one on the person: a campsite is not popped.
    r"|\b(?:this|that)\s+(?:spot|sore|lump)s?\b"
    r"|\bon (?:my )?\w*(?:chin|cheek|face|jaw|nose|forehead|lip|ear|neck|back|shoulder|arm|"
    r"armpit|elbow|wrist|hand|finger|thumb|leg|thigh|knee|shin|ankle|foot|feet|heel|toe|"
    r"chest|breast|belly|stomach|bottom|bum|groin|skin|scalp|eyebrow|eyelid|head|hip|side)\b"
    r"|\b(?:chin|cheek|forehead|jaw|armpit|elbow|wrist|thumb|knee|shin|ankle|heel|toe|"
    r"scalp|eyelid|eyebrow|breast|groin)\b")
# The same question in any frame: "can i squeeze a boil", "is it ok to squeeze a boil", "do i
# squeeze a boil". The deciding word is the doing - squeeze, pop, lance, prick - pointed at a
# sore, and that is a health question whether or not it opens on "should i".
SORE_DOING = re.compile(r"\b(?:squeeze|squeezing|squeezed|pop|popping|popped|lance|lancing|"
                        r"prick|pricking|burst|bursting|drain|draining|pick|picking|scratch|"
                        r"scratching)\b")
# One of those verbs fits a body and nothing else: a campsite is not squeezed, popped or drained.
# "Pick" is the one that fits both - you pick a spot for a tent and you pick a scab - so a line
# whose only doing verb is "pick" has to say whose spot it is before it is a sore.
SORE_PICKING = re.compile(r"\b(?:pick|picking|picked)\b")
SORE_ONLY_A_BODY = re.compile(r"\b(?:squeeze|squeezing|squeezed|pop|popping|popped|lance|"
                             r"lancing|prick|pricking|burst|bursting|drain|draining|scratch|"
                             r"scratching)\b")
PLASTER_ON = re.compile(
    r"\b(?:put |a |some )?plaster\b[^.]{0,18}?\bon (?:it|this|that|there|them|my \w+)\b"
    r"|\b(?:put |a |some )?(?:bandage|dressing|antiseptic|compress)\b[^.]{0,18}?"
    r"\bon (?:it|this|that|there|them|my " + _WOUND + r")\b"
    r"|\b(?:cover|cover it|covering)[^.]{0,16}"
    r"\b(?:plaster|bandage|dressing)\b"
    # "put an antiseptic on my cut" names the wound after the covering, not before it
    r"|\b(?:bandage|dressing|antiseptic|compress|plaster)\b[^.]{0,6}?\b(?:on|over) "
    + _WOUND + r"\b")

# `pay` on its own is "pay for my mate's meal": the money pool is for paying a debt, and those
# lines say so with the particle.
_PAY_DEBT = re.compile(r"\bpay(?:s|ing|ed)?\s+(?:it\s+|them\s+|that\s+)?(?:off|back|down|into|up)\b")

# A card is a birthday card as often as a credit card: only the money ones are money.
# A card is a birthday card unless the line names the kind, or does something to it that only a
# bank card can have done to it: you cancel, freeze and block a bank card, not a greetings one.
_CARD_MONEY = re.compile(
    r"\b(?:credit|debit|bank|store)\s+cards?\b|"
    r"\b(?:cancel|freeze|block|replace|stop|report|stolen|lost|cloned|skimmed)\s+"
    r"(?:my|the|that|this|our|a)\s+cards?\b|"
    r"\bcards?\s+(?:was|is|got)\s+(?:cloned|skimmed|stolen|lost)\b")

# "Is it worth paying for an inspection?" weighs whether a thing is worth its price: the money pool
# is for money decisions, and nothing money-shaped is being decided in that line.
_VALUE_OF_THING = re.compile(r"\bis it worth (?:paying|paying for|getting|having|going for|"
                             r"splashing out on)\b")


# "is that ok or am i overreacting" is a person asking to be reassured, not a question of fact,
# and "I'd rather not guess, do a search" answers it by sending them to Google. The worry has a
# shape of its own, so it gets a pool that takes the feeling seriously and hands the judgement
# back to them, which is the only honest answer to "is how I feel fair".
# Only a worry about the person's own reaction belongs here. "is that normal" about a knee, a
# kitten or a baby's sleep is a question of fact and the honest answer is to look it up; the
# deck has six of those, and answering them with "you don't need to prove it's bad first" is
# worse than the search line it replaced.
# The shape is the person asking about *their own reaction* ("am i overreacting", "am i making a
# fuss"), which is always a reassurance ask. A bare "is that normal / weird / bad" is not enough:
# the deck has a knee that clicks, a freezer making a noise, a baby waking twice a night and a
# kitten that bites, and all four are questions of fact where the honest answer is to look it up.
WORRY_SELF = re.compile(r"\b(?:am i (?:overreacting|overthinking|over-thinking|over thinking|"
                         r"reading too much(?: into (?:it|this))?|being|mad|unreasonable|silly|"
                         r"wrong|too much|too sensitive|over the top)|overreacting|"
                         r"making a (?:fuss|big deal)|too sensitive)\b")
# "should i worry" is the same ask, but only when it is the whole ask: "should i worry about my
# knee" or "my laptop sounds like a plane, should i worry" is a question about a knee or a laptop,
# and the reassurance pool reads for a feeling. Bare, it is about the person's own state of mind.
SHOULD_WORRY = re.compile(r"\bshould i (?:be )?(?:worried|worry|worrying)\b")
WORRY_SHAPE = re.compile("(?:" + WORRY_SELF.pattern + "|" + SHOULD_WORRY.pattern + ")")
# What is left of the line once "is it ok or should i worry" has nothing in it but filler: that
# leftover being empty is what makes a "should i worry" bare.
SHOULD_WORRY_FILLER = re.compile(r"\b(?:is|it|that|this|ok|okay|so|or|and|but|then|now|just|"
                                 r"really|honestly|about|i|me|a|bit)\b")

# "is that weird" and "is it normal to feel like this" ask the same thing as "am i overreacting":
# whether their own reaction is allowed. It is not a question of fact, and the search hedge
# answered it by sending them to look up whether their feelings are normal - "i got the promotion
# and i dont feel happy about it. is that weird?" got "a search should sort you out quickly". The
# bare form is a real question of fact when it is about a thing, which is why `_reads_as_worry`
# leaves it out ("my knee clicks, is that normal", "is it normal for a puppy to sleep all day"),
# so it counts only when their own feeling is what is being judged.
WEIRD_ASK = re.compile(r"\b(?:is|was|isnt|am i)\s+(?:that|this|it)\s+(?:a bit |really |actually |so )?"
                       r"(?:weird|normal|normalish|strange|odd|wrong|bad)\b"
                       r"|\bis it (?:weird|normal|strange|odd)\b"
                       r"|\bam i (?:weird|strange|odd|abnormal)\b")
# What makes that ask about a feeling rather than about a thing: a feeling word in the line, or in
# the last thing they said ("i feel flat" / "is that normal").
FEELING_SAID = re.compile(r"\b(?:feel|feels|feeling|felt|happy|unhappy|sad|guilty|angry|upset|cry|"
                          r"cried|crying|tears|flat|numb|empty|lonely|miss|hate|proud|ashamed|"
                          r"embarrassed|scared|anxious|relieved|gutted|glad|miserable|"
                          r"heartbroken)\b")
# The whole line, because "is it too late to plant potatoes" names its own subject and belongs to
# the knowledge base. A bare "is it too late to start" is the same ask as "is that too late" when
# the turn before it is the person saying what they are starting.
TOO_LATE = re.compile(
    r"^(?:and |but |so |ok |okay )?(?:is|was|isnt) (?:that|this|it) (?:too|a bit too|a little too) "
    r"(?:late|old)(?: now| then| in the day)?$"
    r"|^(?:and |but |so )?am i (?:too|a bit too|a little too) (?:old|late)(?: for (?:it|this|that))?$"
    r"|^(?:and |but |so )?is (?:that|this|it) (?:too|a bit too) old for me$"
    r"|^(?:and |but |so )?have i (?:left it|started it) too late$"
    r"|^(?:and |but |so )?is it too late for me$"
    r"|^(?:and |but |so )?is \d{1,2} too old(?: for (?:it|this|that))?$"
    r"|^(?:and |but |so )?is it too late to (?:start|begin|learn)(?: now| at my age)?$"
)
# "is that realistic" / "is that too ambitious" / "do you think thats doable": the same doubt as
# "is that too late" with another word in it, asked of a plan instead of an age. Anchored, and with
# no subject of its own, so a question that names its thing stays where it is: "is it feasible to
# freeze milk" is a knowledge question and "is that realistic for a plumber to charge" is the
# price readers' (the "for <thing>" tail is the reason a rate is being asked about).
REALISTIC = re.compile(
    r"^(?:and |but |so |ok |okay |right )?(?:is|was|would|will) (?:that|this) (?:even )?(?:be )?"
    r"(?:a )?(?:realistic|doable|achievable|feasible|plausible|too ambitious|unrealistic)"
    r"(?: for (?:me|us|you))?$"
    r"|^(?:and |but |so |ok |okay )?is (?:that|this) enough time(?: for (?:me|us|you))?$"
    r"|^(?:and |but |so )?can (?:i|we) really (?:do|manage|fit|swing) (?:that|this|it)$"
    r"|^(?:and |but |so )?(?:am i|are we) (?:being )?(?:too ambitious|aiming too high|overdoing it)$"
    r"|^(?:and |but |so )?do you think (?:that|this|it|its|it's|thats|that's) (?:is |would be )?"
    r"(?:a )?(?:realistic|doable|achievable)$"
)


# The same doubt said about the person: "am i being unrealistic", "am i aiming too high". Those
# are also the words somebody uses about a hope or a person ("he says im being unrealistic, am i"),
# and there the reassurance pool has the better line, so this reading wants a plan under it: the
# line or the turn before it says what the plan is, or the thread is one they have just started.
REALISTIC_ABOUT_ME = re.compile(
    r"^(?:and |but |so )?(?:am i|are we) (?:being )?unrealistic$"
)

# What counts as a plan in the line or the turn before it. A month, a span of weeks, a distance, a
# course, a target: the words a person uses when they are telling the bot what they intend to do.
PLAN_WORDS = re.compile(
    r"\b(?:plan|plans|planning|goal|target|deadline|budget|train(?:ing)?|course|classes|lessons|"
    r"marathon|half marathon|10k|5k|parkrun|diet|saving|save)\b"
    r"|\b(?:in|by|before|until) (?:a |one |two |three |four |five |six |seven |eight |nine |ten |"
    r"\d+ )?(?:week|weeks|month|months|year|years|january|february|march|april|may|june|july|"
    r"august|september|october|november|december|spring|summer|autumn|winter|christmas|easter)\b"
    r"|£\s?\d|\d+\s?k\b")


def _a_plan_in_the_thread(clean, memory):
    """True when the plan the doubt is about is in the line or the turn before it."""
    for text in (clean, _the_line_before(memory)):
        said = str(text or "").lower()
        if said and (PLAN_WORDS.search(said) or TAKING_UP.search(said)):
            return True
    return _a_thing_they_started(memory)


# Somebody close who will not have the thing that would help them: the alarm, the stick, the trip to
# the doctor, a carer in the house. This is the person caring for them talking, and the line reached
# the fallback as "Got it. Is there anything you'd like a hand with?" - a shrug for somebody who has
# just said their mother refuses the pendant alarm. It is not a question of fact, so the search hedge
# is wrong too; what the bot can say is what the refusal is usually about and whose word carries.
SOMEONE_CLOSE = re.compile(
    r"\b(?:my|his|her|our|their)\s+(?:mum|mom|mother|mam|dad|father|pa|nan|nana|nanna|gran|"
    r"granny|grandma|grandad|grandpa|grandmother|grandfather|mother\s+in\s+law|"
    r"father\s+in\s+law|aunt|auntie|uncle|neighbour|neighbor|husband|wife)\b"
    # "hes 80 and wont use a stick", "shes turning 80 and doesnt want a fuss": the pronoun needs
    # an age on it, or "she wont text me back" is read as somebody's mother refusing a carer.
    r"|\b(?:he|she|hes|shes|he's|she's|they|theyre|they're)\b[^.!?]{0,25}?"
    r"\b(?:[7-9]\d|1\d\d|elderly|pensioner|oap|in (?:his|her|their) (?:70s|80s|90s))\b",
    re.I)
# The same refusal said of somebody with no relation named: "she refuses a pendant alarm" is as
# often a mother as a wife, and the line has no noun to tell you which. The aid, the doctor or the
# carer in the line is what makes it this reading, so the pronoun only has to be a person - and a
# child is excluded below, because a four-year-old refusing a coat is a different conversation.
SOMEONE_ELSE = re.compile(r"\b(?:she|he|they|him|her|them)\b", re.I)
A_CHILD = re.compile(
    r"\b(?:my|our|his|her|their)\s+(?:son|daughter|child|children|kid|kids|baby|toddler|"
    r"boy|girl|little\s+one|teenager|teen)\b"
    r"|\b(?:hes|shes|he's|she's|theyre|they're)\s+(?:one|two|three|four|five|six|seven|eight|"
    r"nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|18 months)\b", re.I)
REFUSES_IT = re.compile(
    r"\b(?:wont|won't|will\s+not|refuses|refused|refusing|doesnt\s+want|doesn't\s+want|"
    r"didnt\s+want|didn't\s+want|does\s+not\s+want|will\s+not\s+have|wont\s+have|"
    r"won't\s+have|wont\s+let|won't\s+let|wont\s+accept|won't\s+accept)\b", re.I)
# The thing refused, in the three families the reply can speak to. An object and a pet fall out of
# this on their own: "the dog flap wont close" and "my car wont start" name no person to refuse.
AN_AID = re.compile(
    r"\b(?:stick|sticks|walking\s+stick|frame|zimmer|walker|rollator|pendant|alarm|"
    r"bath\s+lift|shower\s+seat|grab\s+rails?|"
    r"key\s+safe|stairlift|commode|incontinence\s+pads?)\b", re.I)
# The aids that are settled in a clinic rather than by a home visit: an optician's test, an
# audiologist's test. The occupational therapist who comes out with a stick has nothing to say
# about a pair of glasses, so these have their own words.
A_CLINIC = re.compile(
    r"\b(?:hearing\s+aids?|glasses|specs|spectacles|dentures|contact\s+lenses|"
    r"hearing\s+test|eye\s+test)\b", re.I)
THE_DOCTOR = re.compile(
    r"\b(?:doctor|doctors|doctor's|gp|gps|surgery|hospital|"
    r"appointment|check\s*-?\s*up|blood\s+test|scan|physio\w*|dentist|optician|"
    r"memory\s+clinic|chiropodist)\b", re.I)
# "a carer in the house" and not a day centre or a club: the reply for people coming in is about
# who comes in, and "she wont go to a club" is the different question of leaving the house.
HELP_IN = re.compile(
    r"\b(?:carers?|care\s+worker|home\s+help|help(?:ing)?\s+(?:in|out|around)|anyone\s+in|"
    r"somebody\s+in|someone\s+in|anybody\s+in|strangers?\s+in|a\s+cleaner|cleaner|"
    r"home\s+care|meals\s+on\s+wheels|respite|a\s+carer|paid\s+help|"
    r"district\s+nurse|the\s+nurse|nurse\s+in|occupational\s+therapist|ot\s+in)\b", re.I)


def _a_carer_refused(clean):
    """Which of the three refusals "my mum wont ..." is, or None for every other line."""
    if not REFUSES_IT.search(clean) or A_CHILD.search(clean):
        return None
    if not (SOMEONE_CLOSE.search(clean) or SOMEONE_ELSE.search(clean)):
        return None
    if A_CLINIC.search(clean):
        return "clinic"
    if AN_AID.search(clean):
        return "aid"
    if THE_DOCTOR.search(clean):
        return "doctor"
    if HELP_IN.search(clean):
        return "help"
    return None


def _a_plan_doubt(pred, clean, repaired):
    """True when the doubt is the whole line, or the clause after the plan it is about.

    "im doing a 10k in may, is that realistic" puts the plan and the doubt in one line with a
    comma between them, and an anchored reading of the whole line misses it. Only the clause
    after the last comma is tried, so a line that keeps talking after the ask ("is that realistic
    to run on") is still not this one.
    """
    for text in (clean, repaired):
        if pred(text):
            return True
        tail = text.rsplit(",", 1)[-1].strip() if "," in text else ""
        if tail and pred(tail):
            return True
    return False

# The same doubt said as a fact about themselves instead of as a question: "i want to start
# running" / "im 44 and quite unfit" was answered "Got it. Is there anything you'd like a hand
# with?", which reads as if the person had said nothing at all. Age and being unfit are the two
# things people offer as a reason not to start, so the statement is read the same way as "am i
# too old": only after they have said what they are starting, and not in a body thread, where
# "im 34 and my knee gives way when i run" is a knee question.
_AGE_DOUBT = re.compile(r"\b(?:old|older|age|aged|past it|spring chicken|\d{2})\b", re.I)
A_BIT_PAST_IT = re.compile(
    r"^(?:and |but |so |well |also )?(?:im|i'?m|i am)\s+(?:"
    r"\d{1,2}\s*[,;]?\s*(?:(?:and|but|now)\b|,)[^.!?]*"
    r"|(?:quite |very |pretty |a bit |a little |really |fairly |properly |so |"
    r"not that |not especially )?"
    r"(?:unfit|overweight|old|out of shape|out of practice|past it|no spring chicken|"
    r"fit as i was|as fit as i was)\b[^.!?]*"
    r"|(?:not|no longer|less than|hardly)\s+(?:very\s+|that\s+|especially\s+)?"
    r"(?:fit|strong|sporty|good at it)\b[^.!?]*)")
# What the person says when they are taking something up themselves. The doubt is about their own
# starting, so the line before has to be that: "the last train is at nine" / "is that too late" is
# about a train, and the age-and-a-start pair ("i started piano last year" / "im 52") is the same
# doubt said twice, so the words may be one turn back.
TAKING_UP = re.compile(
    r"\b(?:im|i'm|i am|ive|i've|i) "
    r"(?:(?:just|finally|also|now|really|still|even) )?"
    r"(?:(?:thinking (?:of|about)|want(?:ing)? to|try(?:ing)? to|hoping to|planning to|"
    r"about to|going to) )?"
    r"(?:start(?:ing|ed)?|learn(?:ing|t)?|began|beginning|tak(?:e|ing) up|took up|"
    r"going back to|back at|get(?:ting)? (?:back )?into|join(?:ing|ed)?|"
    r"sign(?:ing|ed)? up (?:for|to))\b")


def _a_bare_worry(clean):
    """True when "should i worry" is the whole ask, not attached to a thing they describe."""
    found = SHOULD_WORRY.search(clean)
    if not found:
        return False
    rest = clean[:found.start()] + " " + clean[found.end():]
    rest = SHOULD_WORRY_FILLER.sub(" ", rest)
    return not re.sub(r"[^a-z0-9]", "", rest)


def _worry_is_about_the_body(clean, words):
    """True when the worry names a body part, a symptom or a health service."""
    words = set(words)
    return bool(words & BODY_PARTS or words & HEALTH_WORDS or words & SYMPTOM_WORDS
                or any(phrase in clean for phrase in CHECK_PHRASES))


# "is he going to be ok", "how long is she likely to be in", "is that just age": the ask a
# person makes about somebody the bot has never met, after naming what happened to them. Every
# one of these got the search hedge ("A quick search online will get you a solid answer"), which
# is the one reply that cannot be right here: no website knows this dad, and the answer is sitting
# with the people looking after him. Nobody here can examine anybody, so the honest line names who
# can and asks the one thing only the person in the room can say.
UNKNOWN_HOW_IT_GOES_FOR_SOMEONE = (
    "Only the people looking after them can say, and they will tell you straight if you ask - "
    "their own GP, whoever is treating them. What has changed since you last heard?",
    "I would be guessing, and this is not a thing to guess about. Ask whoever is treating them, or "
    "ring 111 if it has got worse today. How are they in themselves?",
    "That one is with the people who can see them, not with me. Ask it plainly when you next speak "
    "to them, and if they fob you off, ask again. What were you told last?",
    "Nobody can promise how it will go, and anyone who does is guessing too. Their GP will give "
    "you the honest picture, and asking is not fussing. What worries you most?",
    "I cannot know that from here and I will not pretend to. Ring their GP and ask it as you asked "
    "me - they answer this every day. How long has it been like this?",
)
# The same ask in a thread that already has somebody in a bed: "how long is she likely to be in"
# after "my mums in hospital". A ward is the place to ask, not a GP's phone line and not 111.
UNKNOWN_HOW_LONG_IN_HOSPITAL = (
    "How long is the ward's to say, and they will tell you: ask for the plan in days rather than "
    '"a while", and ask who to ring for updates. What have they said so far?',
    "That depends on what they are treating, so it is their team's answer rather than mine. Ask "
    "what has to happen before they can come home - that is the number that matters. Have they "
    "given you a plan?",
    "Nobody here can say, and the team looking after them will: they give a rough plan and revise "
    "it as things change. Ask what to expect over the next few days. How are they in themselves?",
)
# A rough patch is not a patient: there is a body in a ward, and there may be nothing wrong with a
# person who is having a hard time. Sending them to a ward names a doctor who has never heard of
# them, and a search hedge tells them nothing, so this is the pool for "is she going to be ok"
# about somebody who is struggling rather than ill: only they can say, the question is worth
# asking, and the GP is where it turns into a medical question if it goes on.
UNKNOWN_HOW_IT_GOES_FOR_A_HARD_TIME = (
    "Only they can say how they are doing, and asking them is worth more than a guess from me. Ask "
    "how they are in themselves. If it has been weeks rather than days, their GP is the place to "
    "start - that is what they are there for.",
    "I cannot tell you how somebody else is going to be, and anyone who says they can is guessing. "
    "Ask them straight, and ask again if the first answer is that they are fine. If it drags on, "
    "or they are not sleeping or eating, a GP appointment is the usual next step.",
    "That one is theirs to say, not mine. What helps most is asking how they are and then "
    "listening rather than fixing it. If it runs for weeks, or they stop sleeping or eating "
    "properly, that is a GP question rather than a search one.",
)
# A dog has a vet rather than a ward, so the same ask in a thread about an animal goes there.
UNKNOWN_HOW_IT_GOES_FOR_A_PET = (
    "Only the vet can say, and that is why the call is the answer - they would much rather hear "
    "it now than later. If they go wobbly, sick or sleepy, that is an evening vet, not a morning "
    "one.",
    "I cannot tell you that, and I would not guess about an animal. Ring the vet and say what "
    "happened; how are they in themselves right now?",
    "That one belongs to the vet rather than to me. While you ring, watch them: eating, moving "
    "about, themselves - that is what the vet will ask you.",
)
# "should she still be driving" at eighty-four, living on her own: the same "not mine to say" as
# the pool above, but the person who can say is one who can see her do it, not one treating her.
UNKNOWN_IF_THEY_STILL_CAN = (
    "Nobody here can judge that from a line, and I would not guess at it. Their GP, or whoever "
    "sees them day to day, will tell you straight, and it is easier to raise as a worry than as a "
    "verdict. Has anything already gone wrong?",
    "That is not mine to decide, and it is not a thing to guess at either. Ask their doctor, or "
    "get an eye test done if it is about the driving; that settles it more often than people "
    "expect. What made you wonder?",
    "I cannot say, and I would not want to. The person who can judge it is the one who can see "
    "them do it. Would they take it from you if you raised it?",
)


def _somebody_to_visit(clean, turns, look_back=3):
    """True when the line or the last few turns name a person the visit could be to."""
    people = THE_PEOPLE | VISIT_PRONOUNS
    if set(re.findall(r"[a-z']+", clean)) & people:
        return True
    for turn in turns[-look_back:]:
        said = str(turn.get("user") or "").lower()
        if set(re.findall(r"[a-z']+", said)) & people:
            return True
    return False


def _someone_is_a_patient(clean, turns, look_back=4):
    """True when the line or the last few turns name a place that keeps someone in.

    The visit pools differ only in whether a ward is somewhere to go: "ask whoever is on the
    ward" is right after "my mum is in hospital" and wrong after "i cut my hand badly".
    """
    if IN_HOSPITAL.search(clean):
        return True
    for turn in turns[-look_back:]:
        if IN_HOSPITAL.search(str(turn.get("user") or "").lower()):
            return True
    return False


# Whose trouble it is. A line with an animal in it is not always about the animal: "my dog bit me
# and it is bleeding" is a person with a bite on their hand, and the vet is the wrong building for
# them. So the animal has to be the one that was hurt, and each of these readings says the person
# is: the animal did it to them, somebody did it to them, they are one of the people, or what is
# bleeding belongs to them.
#
# The old second arm was a bare `my ... bleeding`, and it could not tell whose blood it was: "my
# dog is bleeding" and "my dogs paw is bleeding" were read as a person hurt, so the walk-in pool
# answered an animal. Whose it is comes from the noun, not from the possessive: a body part after
# "my" is a person, an animal after "my" is not.
AN_ANIMAL_DID_IT = re.compile(
    r"\b(?:bit|bitten|bites|scratch(?:ed|es)?|kicked|trampled|stung|attacked|mauled|nipped|"
    r"gouged|pinned|knocked|went for|lashed out at)\s+(?:me|us|my|our)\b",
    re.I)
# The same injury with the animal as the agent: "bitten by a dog", "scratched by the cat". This is
# the passive form and the active one does not cover it, which is how a child with a dog bite was
# told to ring the vet "and say what she ate and when".
AN_ANIMAL_DID_IT_TO_ANYONE = re.compile(
    r"\b(?:bit|bitten|bites|scratch(?:ed|es)?|nipped|attacked|mauled|stung|kicked)\s+by\s+"
    r"(?:a|an|the|my|our|their|his|her|some)\s+(?:dog|dogs|cat|cats|puppy|pup|kitten|rabbit|"
    r"hamster|budgie|parrot|horse|pony|fox|rat|mouse|snake|spider|wasp|bee|animal|pet)\b",
    re.I)
# Somebody else is the patient: "my daughter got bitten by a dog", "the child was scratched". The
# child or the partner is read only beside a bite, a scratch or a sting, so "my son is vomiting"
# stays where it was.
A_PERSON_ELSE_IS_HURT = re.compile(
    r"\b(?:my|our|the|his|her|their)\s+(?:daughter|son|child|children|kid|kids|baby|wife|"
    r"husband|partner|boyfriend|girlfriend|mum|mother|dad|father|sister|brother|friend|"
    r"neighbour|neighbor|grandson|granddaughter|grandchild|niece|nephew)\b[^.]{0,60}\b"
    r"(?:bit|bitten|bites|scratch(?:ed|es)?|nipped|attacked|mauled|stung|kicked|swollen|"
    r"bleeding|bled)\b",
    re.I)
# What happens to a person after an animal bite, and never to the animal: the jab, the hospital,
# the stitches. "do i need a tetanus" after "i was bitten by a dog" is the person's question.
A_PERSONS_TREATMENT = re.compile(
    r"\b(?:tetanus|rabies|jab|jabs|shot|shots|stitches|stitched|a&e|a and e|casualty|"
    r"minor injuries|triage|antiseptic|antibiotics?|wound|dressing|bandage)\b",
    re.I)
# The person's own body: "i am bleeding", "im bleeding", "my hand is bleeding", "my arm hurts".
# Only a body part counts after "my", because "my dog" and "my cat" are the animal.
A_BODY_PART = (
    r"(?:hand|hands|arm|arms|finger|fingers|thumb|thumbs|wrist|wrists|leg|legs|foot|feet|toe|toes|"
    r"head|nose|face|mouth|lip|lips|eye|eyes|ear|ears|knee|knees|shoulder|shoulders|back|side|"
    r"chest|stomach|ankle|ankles|heel|heels|shin|thigh|elbow|skin|neck|jaw|tooth|teeth|gum|gums|"
    r"nail|nails|cut|cuts|wound|wounds|bite|scar|knuckle|knuckles|palm|fist|forehead|cheek)")
A_PERSON_IS_BLEEDING = re.compile(
    r"\b(?:i|im|i'm|ive|i've|we|we're|weve|we've)\s+(?:am\s+|was\s+|are\s+|were\s+|"
    r"keep\s+|keeps\s+|still\s+|been\s+)?(?:bleeding|bled)\b|"
    r"\b(?:i|im|i'm|ive|i've|we|we're)\s+(?:still\s+|also\s+)?(?:hurting|in pain|sore)\b|"
    r"\bmy\s+" + A_BODY_PART + r"\b[^.]{0,30}?\b(?:bleeding|bled|hurts?|hurting|sore|"
    r"swollen|limp|infected|throbbing|bruised|broken|stings?|burning)\b",
    re.I)


# Whose body the injury is on when both a person and an animal are named, read from the order of
# the words. The passive form has no subject: "bitten by a snake" is the same words whether the one
# with the bite is the person or the dog, so `AN_ANIMAL_DID_IT_TO_ANYONE` read "my dog was bitten
# by a snake" as somebody's hand and answered "a&e or a walk-in centre can say for certain" about a
# dog. The order tells them apart: in "my dog was bitten by a snake" the animal comes before the
# verb, so the animal is the one who was hurt; in "i was bitten by a dog" it comes after.
AN_A_HARM_VERB = re.compile(
    r"\b(?:bit|bites|bitten|scratch|scratches|scratched|sting|stings|stung|kicked|attacks?|"
    r"attacked|mauled|nipped|gouged|trampled|lashed out at|went for|snapped at)\b",
    re.I)
AN_ANIMAL_WORD = re.compile(r"\b(?:" + "|".join(sorted(ANIMALS)) + r")\b", re.I)


def _the_animal_is_the_patient(said):
    """True when the animal named in this line is the one with the injury.

    Deliberately narrow: an animal before the verb of harm, and nobody's body named after it. "the
    dog bit my son" and "my dog scratched the baby" have the animal before the verb too, and there
    the person is the patient, so the object of the verb is read before the order is.
    """
    text = str(said or "").lower()
    animals = [m.start() for m in AN_ANIMAL_WORD.finditer(text)]
    if not animals:
        return False
    if AN_ANIMAL_DID_IT.search(text):
        return False
    verb = AN_A_HARM_VERB.search(text)
    if verb is None or min(animals) > verb.start():
        return False
    tail = set(re.findall(r"[a-z']+", text[verb.end():]))
    return not (tail & (THE_PEOPLE - ANIMALS))


def _the_person_is_the_patient(said):
    """True when what a line says is about somebody's body other than the animal's.

    One reader for the four ways a person is the patient: the animal did it to them, it did it to
    somebody in their family, they need the treatment an animal bite needs, or a body of theirs is
    the thing bleeding. The bare possessive is deliberately not one of them.
    """
    text = str(said or "")
    if not text or _the_animal_is_the_patient(text):
        return False
    return bool(AN_ANIMAL_DID_IT.search(text)
                or AN_ANIMAL_DID_IT_TO_ANYONE.search(text)
                or A_PERSON_ELSE_IS_HURT.search(text)
                or A_PERSONS_TREATMENT.search(text)
                or A_PERSON_IS_BLEEDING.search(text))


def _the_thread_is_an_animal(clean, turns, look_back=4):
    """True when the line or the last few turns are about an animal rather than a person.

    Read like `_someone_is_a_patient`: the care question ("should i take her tonight") does not
    name the animal again, so the thread has to say it, and a line naming one says it by itself.
    The animal also has to be the one in trouble - `_the_person_is_the_patient` keeps the person
    with the bite on their own hand out of the vet's waiting room, and keeps a dog's bleeding paw
    out of it too by not reading "my dog is bleeding" as somebody's blood.
    """
    said = str(clean or "").lower()
    recent = [str(turn.get("user") or "").lower() for turn in turns[-look_back:]]
    if _the_person_is_the_patient(said) or any(_the_person_is_the_patient(x) for x in recent):
        return False
    if set(re.findall(r"[a-z']+", said)) & NOT_PEOPLE_WORDS:
        return True
    return any(set(re.findall(r"[a-z']+", x)) & NOT_PEOPLE_WORDS for x in recent)


def _thread_is_about_someone_else(memory, look_back=3):
    """True when the last few things the person said were about somebody other than them.

    Read from the thread, not the line: "he cant do up his buttons yet" names the child only as
    "he", and the line after it is the bare ask.
    """
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-look_back:]:
        said = str(turn.get("user") or "").lower()
        words = {w[:-2] if w.endswith("'s") else w for w in re.findall(r"[a-z']+", said)}
        if (words & trouble.OTHERS) - NOT_PEOPLE_WORDS:
            return True
    return False


def _thread_is_about_a_pet(memory, look_back=3):
    """True when the last few things the person said named an animal.

    Read from the thread, not the line, because the line is the bare ask: "my dog keeps
    scratching" then "should i be worried". A wild bird that made a mess is not somebody with a
    doctor ("how do i clean bird poo off my patio"), so the mess shapes are left out.
    """
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-look_back:]):
        said = str(turn.get("user") or "").lower()
        words = {w[:-2] if w.endswith("'s") else w for w in re.findall(r"[a-z']+", said)}
        animals = words & ANIMALS
        if not animals:
            # The nearest line that names a subject is what the bare worry is about. A line about
            # the person's own state ("my dog died last year" / "i keep feeling odd" / "should i be
            # worried") is about them, however much of the week was spent at the vet: the vet line
            # answered that with "one visit settles it" about a dog that is already gone.
            if _the_speaker_is_the_subject(said):
                return False
            continue
        if animals <= WILD_BIRDS and words & MESS_PLACES:
            continue
        if loss.reads_as_loss(said) or badnews.reads_as_sudden_loss(said):
            return False
        return True
    return False


# Who the line is asking about: "he" and "she" point back at the thread, and a named relation
# says it in the line. The animals are here so that "is he going to be ok" after "my dog drank
# sea water" is read as a question for a vet rather than for a ward.
ASKED_ABOUT = re.compile(
    r"(?:he|she|they|(?:my|our|his|her|their)\s+(?:poor\s+|old\s+|little\s+|eldest\s+)?"
    r"(?:mum|mom|mother|dad|father|son|daughter|husband|wife|partner|boyfriend|girlfriend|"
    r"sister|brother|nan|nana|gran|granny|grandma|grandad|grandpa|baby|kid|kids|child|children|"
    r"friend|mate|neighbour|neighbor|aunt|uncle|cousin|little one|lad|lass|boy|girl|"
    r"dog|cat|puppy|kitten|pup|rabbit|hamster|horse|budgie|parrot|fish|pet))")
# "is he going to be ok", "will my mum be alright", "is she ok", "are they fine".
WHETHER_IT_GOES_WELL = re.compile(
    r"\b(?:is|are|was|were|will|would)\s+" + ASKED_ABOUT.pattern
    + r"\b\s+(?:going\s+to|gonna)\s+be\b"
    r"|\b(?:is|are|was|were)\s+" + ASKED_ABOUT.pattern
    + r"\b\s+(?:ok|okay|alright|all\s+right|fine|safe)\b"
    r"|\b(?:will|would)\s+" + ASKED_ABOUT.pattern
    + r"\b\s+be\s+(?:ok|okay|alright|all\s+right|fine|safe)\b"
    r"|\b(?:will|would)\s+" + ASKED_ABOUT.pattern
    + r"\b\s+(?:ever\s+)?(?:pull\s+through|make\s+it|get\s+better|get\s+worse|recover|"
    r"walk\s+again|come\s+round|beat\s+it|"
    r"be\s+(?:himself|herself|themselves|back\s+to\s+(?:normal|herself|himself|themselves)))\b"
    r"|\b(?:is|are|was)\s+" + ASKED_ABOUT.pattern
    + r"\b[^.?!]{0,25}\b(?:at\s+risk|in\s+danger)\b"
    r"|\bhow\s+long\s+(?:is|are|will|does|do|has|have)\s+" + ASKED_ABOUT.pattern + r"\b")
# "should she still be driving" is the same ask with a different answer: not how it will go, but
# whether an eighty-four-year-old who lives alone should be at the wheel. It is not the bot's to
# judge either, and the person who can is one who can see her do it.
WHETHER_THEY_CAN_STILL = re.compile(
    r"\bshould\s+" + ASKED_ABOUT.pattern + r"\b\s+still\b"
    r"|\bshould\s+" + ASKED_ABOUT.pattern
    + r"\b\s+be\s+(?:driving|working|living\s+alone|left\s+alone|on\s+(?:his|her|their)\s+own)"
    r"|\bis\s+" + ASKED_ABOUT.pattern
    + r"\b\s+(?:still\s+)?(?:ok|safe|alright)\s+to\s+(?:drive|live|work)\b")
# The same worry said with "it" instead of a person ("my dad has prostate cancer" / "is it going
# to be alright") or as a length ("how bad will it get", "how much longer has she got"). "It" is
# only a person's illness when the thread has an illness in it: "my dad's car is making a noise" /
# "is it going to be ok" is a garage question and keeps its own answer.
WHETHER_IT_GOES_WELL_ITSELF = re.compile(
    r"\b(?:is|was|will)\s+(?:it|this|that)\s+(?:going\s+to\s+be\s+|be\s+)?"
    r"(?:ok|okay|alright|all\s+right|fine|serious|bad|treatable|curable|terminal)\b"
    r"|\bhow\s+(?:bad|serious)\s+(?:will\s+(?:it|this|that)\s+get|is\s+(?:it|this|that))\b"
    r"|\bhow\s+long\s+(?:is|will)\s+the\s+recovery\b")
# "how much longer has she got", said about a ninety-two-year-old: a length of life, not an
# illness in the thread, so this one needs only the person the thread is about.
WHETHER_IT_LONGER_HAS_GOT = re.compile(
    r"\bhow\s+much\s+longer\s+(?:has|have|does|do)\s+" + ASKED_ABOUT.pattern + r"\b"
    r"|\bhow\s+long\s+(?:has|have)\s+" + ASKED_ABOUT.pattern + r"\b\s+(?:got|left)\b")
AN_ILLNESS = re.compile(
    r"\b(?:cancer|tumou?r|disease|illness|condition|infection|dementia|alzheimers?|"
    r"leuk[ae]mia|leuka?emia|arthritis|diabetes|epilepsy|lupus|ms|covid|long\s+covid|flu|"
    r"pneumonia|chemo|dialysis|transplant|bypass|operation|surgery|procedure|stroke|aneurysm|sepsis|"
    r"heart\s+failure|kidney\s+failure|liver\s+failure|ulcer|colitis|crohns?|asthma|"
    r"depression|anorexia|bulimia|eating\s+disorder|addiction|withdrawal)\b")
# A pet's worry is the vet's only when the thread says something is actually wrong with the
# animal: "my dog drank sea water" and "the vet saw my cat this morning" are, and "we are getting
# a puppy" / "will he be alright in a flat" is a question about space, not about a body.
A_PET_IN_TROUBLE = re.compile(
    r"\b(?:vet|vets|sick|ill|illness|disease|diagnosed|condition|hurt|hurts|injured|injury|"
    r"poison|poisoned|ate|eaten|drank|drunk|swallowed|choking|choked|limp|limping|bleeding|"
    r"bled|cut|wound|wobbly|unsteady|seizure|fit|fits|surgery|operation|collapsed|"
    r"not\s+eating|stopped\s+eating|off\s+(?:his|her|its|their)\s+food|worse)\b")
# "is that just age", said about the parent who keeps forgetting words the line before.
WHETHER_IT_IS_THEIR_AGE = re.compile(
    r"\b(?:is|was)\s+(?:that|this|it)\s+(?:just|normal|normal\s+for|ordinary)\b[^.?!]{0,30}"
    r"\b(?:age|her\s+age|his\s+age|them|him|her)\b")
# The people a thread can be about, as stems: "my mums in hospital" has to read as a person, and
# it spells its own relation with an s on the end.
_MY_PEOPLE = frozenset(w.rstrip("s") for w in """
    mum mom mother dad father son daughter husband wife partner boyfriend girlfriend sister
    brother nan nana gran granny grandma grandad grandpa baby kid child children friend mate
    neighbour neighbor aunt uncle cousin lad lass boy girl parent ex family stepson stepdaughter
    nephew niece grandson granddaughter sibling twin stepmum stepdad stepmother stepfather
    mother-in-law father-in-law son-in-law daughter-in-law sister-in-law brother-in-law
    godson goddaughter grandparent in-laws
""".split())
# A bed in a hospital says whose body the thread is about even when the word is not a relation.
A_PATIENT_STATE = re.compile(r"\b(?:hospital|pregnant|operation|surgery|diagnosed|chemo|"
                             r"ward|intensive\s+care|in\s+a\s+coma|on\s+a\s+drip)\b")
# A thread about somebody's body says whose it is, but a thread about a hard patch says nothing
# about one: "my mum is having a hard time" then "is she going to be ok" is a rough spell, not an
# illness, and a pool that answers "ask whoever is treating them, or ring 111" has invented a
# patient. The words here are the ordinary ones for trouble that is not a body's.
A_HARD_TIME = re.compile(
    r"\b(?:(?:hard|rough|bad|tough|difficult|dreadful|awful)\s+(?:time|times|week|weeks|month|"
    r"months|year|years|patch|spell|stretch|ride|few(?:\s+\w+)?|long(?:\s+\w+)?)\b|"
    r"struggling|struggles|struggled|having\s+a\s+go\s+of\s+it|feeling\s+low|feels\s+low|"
    r"down\s+in\s+the\s+dumps|grieving|grief|bereavement|lonely|loneliness|stressed|stress|"
    r"overwhelmed|burnout|burnt\s+out|burned\s+out|worried\s+sick|money\s+trouble|"
    r"out\s+of\s+work|lost\s+(?:his|her|their)\s+job|divorce|divorcing|split\s+up|"
    r"separation|argument|arguing|falling\s+out|fell\s+out|lonely)\b")
# What a thread needs for the pools that talk about treatment to be right: a body, a bed, or a
# thing that happened to one.
A_MEDICAL_THREAD = re.compile(
    r"\b(?:hospital|hospice|pregnant|operation|operations|op|ops|surgery|surgeon|surgeons|"
    r"diagnosed|diagnosis|chemo|chemotherapy|radiotherapy|treatment|treating|being\s+treated|"
    r"ward|intensive\s+care|high\s+dependency|in\s+a\s+coma|on\s+a\s+drip|anaesthetic|"
    r"anaesthetist|theatre|consultant|specialist|biopsy|transplant|dialys\w+|"
    # "results day" is a school day and "exam results" are not a body's: only a result of a test
    # on a person is, and that is said with a word that is already here.
    r"results?(?!\s+day)\b|"
    r"accident|accidents|crash|crashed|ambulance|casualty|a\s+and\s+e|ae|"
    r"broke|broken|fractur\w+|scald\w*|stitches|collapsed|fainted|"
    r"seizure|seizures|convulsion\w*|concussion|injured|injury|injuries|whiplash)\b"
    # A fall and a burn are a body's, but "fell out with her sister" is a quarrel and "burnt out"
    # is a state of mind: both are `A_HARD_TIME` shapes, so without this they read as an injury
    # and send a person who is struggling to a ward.
    r"|\b(?:fell|fallen|burn|burns|burned|burnt)(?!\s+out)\b")


def _the_thread_said(memory, look_back=3):
    """The last few things the person said, as one lowercase string."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    return " ".join(str(turn.get("user") or "").lower() for turn in turns[-look_back:])


def _a_person_in_the_thread(memory, look_back=3):
    """True when one of the last few lines is about a person, named as a relation or as a patient.

    `_thread_is_about_a_person` reads the same turns, but only from the words it was written for:
    "my mums in hospital" carries its own relation with an s on the end and a bed that says
    somebody is in it, and both mean the next line's "she" is a person rather than a machine.
    """
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-look_back:]:
        said = str(turn.get("user") or "").lower()
        words = {w[:-2] if w.endswith("'s") else w for w in re.findall(r"[a-z']+", said)}
        if {w.rstrip("s") for w in words} & _MY_PEOPLE or A_PATIENT_STATE.search(said):
            return True
    return False


def _a_hard_time_and_not_a_body(memory, line=""):
    """True when the thread is about a rough patch and says nothing about a body.

    The pools that name the people treating somebody are right where there is a body to treat and
    wrong where there is not: "my mum is having a hard time" / "is she going to be ok" is about a
    spell of trouble, and nobody is treating her for it. Something in the thread that is a body,
    a bed or an illness keeps the pools, so this only stands between them and a thread of feeling.
    """
    said = _the_thread_said(memory) + " " + str(line or "")
    if A_MEDICAL_THREAD.search(said) or AN_ILLNESS.search(said):
        return False
    return bool(A_HARD_TIME.search(_the_thread_said(memory)))


def _a_pet_in_trouble(line, memory):
    """Whether the worry is about an animal that has something wrong with it.

    The animal has to be the thread's, in an animal thread and with no person named in the last
    two lines ("my dog drank sea water", but not "my dad's dog died"), and something in the line
    or the thread has to say the animal is hurt or ill.
    """
    if not _thread_is_about_a_pet(memory) or _a_person_in_the_thread(memory, look_back=2):
        return False
    said = _the_thread_said(memory)
    # "my cat had a rough few days" is the vet's too: for an animal a rough patch is being off
    # colour, and there is no such thing as a bad week at work for a cat.
    return bool(A_PET_IN_TROUBLE.search(line) or A_PET_IN_TROUBLE.search(said)
                or A_HARD_TIME.search(said))


def _the_pool_for_a_worry_about_them(clean, memory):
    """The pool for "is he going to be ok" and its kind, or None.

    Read from the line and the thread together, like `_thread_is_about_someone_else`: "is he going
    to be ok" names nobody, and the line before it ("my dad had a car accident", "my dog drank sea
    water") says who he is and which doctor he has. A line that names nobody and follows a thread
    that names nobody is not this ask, which keeps "will they stretch" about a pair of shoes out
    of both pools.
    """
    line = re.sub(r"[^a-z0-9' ]", " ", str(clean or "").lower())
    # The readers that already answer a follow-up like this keep their turn: `greeting` offers
    # them only to a hedge, so a pool of mine here would take the answer away from them. The ward
    # reader (`an_outcome_asked_about_someone`) says the same thing better where the thread has
    # somebody in a bed, and `the_threads_answer` owns the ask that only points at the thread.
    if an_outcome_asked_about_someone(clean, memory) or the_threads_answer(clean, memory):
        return None
    still = WHETHER_THEY_CAN_STILL.search(line)
    itself = WHETHER_IT_GOES_WELL_ITSELF.search(line) or WHETHER_IT_LONGER_HAS_GOT.search(line)
    if itself:
        # "how long has he got" after "my cat has kidney disease" is the vet's, and the animal
        # comes first here so that a pet thread is not turned away by the person-only check.
        if _a_pet_in_trouble(line, memory):
            return UNKNOWN_HOW_IT_GOES_FOR_A_PET
        if not _a_person_in_the_thread(memory):
            return None
        if not (WHETHER_IT_LONGER_HAS_GOT.search(line)
                or AN_ILLNESS.search(_the_thread_said(memory))):
            return None
    if not (still or itself or WHETHER_IT_GOES_WELL.search(line)
            or WHETHER_IT_IS_THEIR_AGE.search(line)):
        return None
    subject = ASKED_ABOUT.search(line)
    named = subject.group(0) if subject else ""
    if set(named.split()) & (ANIMALS | NOT_PEOPLE_WORDS):
        return UNKNOWN_HOW_IT_GOES_FOR_A_PET
    if not named or re.match(r"(?:he|she|they)\b", named):
        # "he" / "she" / "they" / no subject at all: the thread says who it is, and the nearest
        # line that names somebody is the one that decides which waiting room this is.
        if _a_pet_in_trouble(line, memory):
            return UNKNOWN_HOW_IT_GOES_FOR_A_PET
        if not _a_person_in_the_thread(memory):
            return None
    if still:
        return UNKNOWN_IF_THEY_STILL_CAN
    if _a_hard_time_and_not_a_body(memory, line):
        # A rough patch is not a patient: the pools below would hand them to a ward that has never
        # heard of them, and the search hedge would say nothing, so this keeps the ask and drops
        # the ward.
        return UNKNOWN_HOW_IT_GOES_FOR_A_HARD_TIME
    if _someone_is_a_patient(line, memory.get("turns") or []):
        return UNKNOWN_HOW_LONG_IN_HOSPITAL
    return UNKNOWN_HOW_IT_GOES_FOR_SOMEONE


SELF_WORDS = frozenset("i me my myself im ive id i'm i've".split())
# The words that make a first-person line about the person's own state rather than about the animal
# in it: "i keep feeling odd", "i feel anxious", "i cant stop thinking about it".
THEIR_OWN_STATE = re.compile(
    r"\bi\s+(?:keep|still|just)\s+(?:feeling|feel|thinking|worrying|crying)\b"
    r"|\bi\s*'?m\s+(?:feeling|worried|scared|anxious|sad|low|exhausted|knackered)\b"
    r"|\bi\s+feel\s+(?:odd|weird|strange|awful|terrible|anxious|worried|sad|low|numb|empty)\b"
    r"|\bi\s+cant\s+(?:stop|sleep|eat|shake|cope)\b"
    r"|\bi\s+havent\s+(?:slept|eaten|coped)\b")


def _the_speaker_is_the_subject(said):
    """True when a line is about the person and not about the animal it may also name.

    "i keep feeling odd" names nobody but the speaker, and the bare worry after it is theirs. The
    loss shapes are read in `_thread_is_about_a_pet` itself, because a line can name both.
    """
    return bool(THEIR_OWN_STATE.search(str(said or "")))


def _a_thing_they_started(memory, look_back=3):
    """True when the last few lines are the person taking something up themselves.

    "is that too late" is a doubt about their own starting, so the turn behind it has to be that
    start: "im learning to swim at 40", "i started piano last year" / "im 52". A train, a
    deadline or a booking leaves it False, and then the question is somebody else's to answer.
    """
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-look_back:]:
        if TAKING_UP.search(str(turn.get("user") or "").lower()):
            return True
    return False


def _names_their_age(clean):
    """True when the doubt about starting is their age rather than their fitness."""
    return bool(re.search(r"\b\d{1,2}\b", clean)
                or _AGE_DOUBT.search(clean))


def _reads_as_worry(clean, words=()):
    """True when the line asks to be reassured rather than asking a question of fact."""
    words = words or clean.split()
    if _worry_is_about_the_body(clean, words):
        return False
    if WORRY_SELF.search(clean):
        return True
    return bool(SHOULD_WORRY.search(clean)) and _a_bare_worry(clean)


def _the_weird_ask_pool(clean, memory):
    """The pool for "is that weird / normal", or None when the line is a question of fact.

    The reassurance pool already answers "am i overreacting", and this is the same ask in the
    words people use for it. It is kept apart from `_reads_as_worry` because it needs the thread:
    "is that normal" on its own is a question of fact, and only the feeling before it makes it
    about them. Asked as the first thing in a chat with nothing after it, there is no feeling and
    no subject either, so it gets the question the pools should have asked ("weird in what way"),
    which is the same shape as a view asked for with nothing behind it.
    """
    found = WEIRD_ASK.search(clean)
    if not found:
        return None
    memory = memory if isinstance(memory, dict) else {}
    if _worry_is_about_the_body(clean, clean.split()) or _thread_is_about_the_body(memory):
        return None
    if FEELING_SAID.search(clean) or FEELING_SAID.search(_the_line_before(memory)):
        return UNKNOWN_WORRY
    if not _the_line_before(memory) and _nothing_but_the_ask(clean, found):
        return UNKNOWN_WEIRD_BARE
    return None


def _nothing_but_the_ask(clean, found):
    """True when the line is the doubt itself, with no subject named around it."""
    rest = clean[:found.start()] + " " + clean[found.end():]
    return not re.sub(r"[^a-z0-9]", "", SHOULD_WORRY_FILLER.sub(" ", rest))


def _without_the_idioms(said):
    """The words of a line with the phrases in `IDIOM_PHRASES` taken out.

    The tree already decides which body words are not bodies, in one list, for the topic of a
    line ("a pain in the neck", "run off my feet", "last legs"). The thread reader here had its
    own read of the raw words, so a thread that said "its on its last legs" about a washing
    machine was a thread about a body, and "is it worth fixing" rang 111 for a machine. One list,
    read by both, so a phrase about a thing cannot be a symptom in one place and not the other.
    """
    words = re.findall(r"[a-z']+", said)
    if not words:
        return set()
    taken = set()
    for phrase in IDIOM_PHRASES:
        size = len(phrase)
        for at in range(len(words) - size + 1):
            if tuple(words[at:at + size]) == phrase:
                taken.update(range(at, at + size))
    return {word for at, word in enumerate(words) if at not in taken}


def _thread_is_about_the_body(memory, look_back=4):
    """True when the last few things the person said named a symptom or a body part."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-look_back:]:
        said = (turn.get("user") or "").lower()
        if not said:
            continue
        # The forecast's own verb goes too: "will they come back next year" is not a spine.
        said = _without_the_things_named_after_a_body(_without_the_forecast_verb(said))
        words = _without_the_idioms(said)
        if words & SYMPTOM_WORDS or words & BODY_PARTS or words & HEALTH_WORDS:
            return True
    return False


def _the_threads_who(memory, look_back=2):
    """The person the thread's own line hands the question to, or None.

    A follow-up that points at the thread ("will that get better", "will it settle down") names
    nothing itself, so the line it points at is the only place the world is. A tooth that aches
    in cold water is the dentist's, and the follow-up about it is the dentist's too; a puppy is
    the vet's. The health hand-off is left out because the health pool says it better than one
    line about who to ring.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-look_back:]):
        said = " " + re.sub(r"[^a-z0-9']", " ", (turn.get("user") or "").lower()) + " "
        words = said.replace("'", "").split()
        if not words:
            continue
        who = _who_for(said.strip(), said, words, None)
        if who and who != HEALTH_WHO:
            return who
    return None


# A question that points at a thing instead of naming it: "will that get better if i keep at
# it", "and will it stop", "is that normal". The pronoun is the whole subject, so the thread is
# what the answer has to fit.
_LEANS_ON_THE_THREAD = re.compile(r"\b(?:it|its|that|thats|this|they|them|those|these)\b")
# The topics a thread can be about and a question about "it" still be the thread's own: a line
# read as cooking ("will that cake keep overnight") names its subject even when a pronoun is in
# it, so only a line with no topic of its own, or a body's, counts as pointing at the thread.
_BODY_TOPICS = (None, "", "health", "fitness", "sleep")


def the_threads_answer(text, memory):
    """The line for a follow-up that only points at the thread, or None.

    "i cant breathe when i run for the bus" then "will that get better if i keep at it" is the
    question the person would put to their own doctor, and the plain shrug met it with "a quick
    search online will get you a solid answer": a reading list for a symptom. The line names no
    subject of its own, so the thread is the only place the world is, and the thread decides
    which honest answer fits - a body's is the GP's, a puppy's is the vet's.

    It is offered to `greeting.respond`, which asks it only of a hedge: a follow-up that already
    has an answer or a card's next step keeps it (`my wrist is sore after typing all day` then
    "will that get better on its own" is answered from the wrist card on the screen).
    """
    clean = " ".join(str(text or "").split())
    if not clean or _hedged_recently(memory):
        return None
    try:
        understood = understand(clean, memory)
    except Exception:  # noqa: BLE001 - a line the engine chokes on is not this reader's
        understood = {}
    if not _the_ask_is_the_threads(clean, understood):
        return None
    who = _the_threads_who(memory)
    if who:
        return _choose([line.format(who=who) for line in UNKNOWN_WHO], memory, clean)
    # Only the line the pronoun points at, which is the one before this: a thread that talked
    # about a headache three turns ago and a rent rise on the last turn is a money thread, and
    # "will that cover it" is not a symptom. The last line on its own is not enough, because the
    # middle turn of a health thread can name no body word at all - "my back has been hurting" /
    # "its been ages now" / "can i get anything for it over the counter" is still the back's - so
    # the thread the follow-up itself leans on counts too (`understood["leans_on"]["topic"]`, from
    # the understanding engine).
    leans = (understood.get("leans_on") or {}).get("topic")
    if leans == "health" or _thread_is_about_the_body(memory, look_back=1):
        return _choose(UNKNOWN_HEALTH, memory, clean)
    return None


# A machine in the thread is a thing, not a body. "the chain skips on the back gears" then "is
# it worth getting it serviced" is a bike - the body reading was taken from the word "back" in
# "back gears", and the cost rule (new in this cut) turned it into "a GP, a pharmacist or 111 will
# tell you", which is the wrong half of the world entirely. A thread that names one of these is a
# thread about a thing whatever body word is hiding in it.
_THREAD_MACHINES = frozenset("""
bike bicycle cycle chain chains gears gear derailleur boiler car van motorbike scooter washer
machine dryer dryers dishwasher fridge freezer oven cooker hob kettle toaster microwave hoover vacuum
mower lawnmower laptop phone tablet computer pc printer tv television stereo speaker speakers
headphones watch clock camera drill saw gate door window shed roof gutter tap shower radiator
pump fan fridge washing
""".split())


def _thread_names_a_machine(memory, look_back=4):
    """True when the last few things the person said named a thing that gets serviced or replaced.

    A body word in the same line outranks the machine word: "my knee keeps giving way and i watch
    it swell" and "my shoulder hurts when i lift the door at work" name a watch and a door, and
    both lines are about a body, so the thread is not the machine's and the cost rule stays out of
    it. The machine has to be what its own line is about.

    The nearest turn decides, because a thread moves on (good-shelf on #7382). "the window in my
    bedroom leaks" and then "my back keeps going" is a body thread that happens to have named a
    window first, and "is it worth fixing" after it is the GP line, not a part and a quote. A
    later line with a body word and no machine word ends the machine thread; a later line that
    says nothing of either ("i dread the phone call") leaves it standing, so "my back keeps
    going" / "the boiler is on its way out" / "is it worth fixing" still gets the cost rule.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-look_back:]):
        tokens = re.findall(r"[a-z']+", (turn.get("user") or "").lower())
        machine_at = [i for i, word in enumerate(tokens) if word in _THREAD_MACHINES]
        if not machine_at:
            if set(tokens) & (BODY_PARTS | SYMPTOM_WORDS | HEALTH_WORDS):
                return False
            continue
        body_at = [i for i, word in enumerate(tokens)
                   if word in BODY_PARTS or word in SYMPTOM_WORDS or word in HEALTH_WORDS]
        # A body word written beside the machine word is part of the machine's name ("the back
        # gears", "the back door", "the back wheel"), so it does not make the line a body line;
        # a body word anywhere else does.
        if all(any(abs(i - j) == 1 for j in machine_at) for i in body_at):
            return True
    return False


# The line's own candidate: "is it my shoes", "could it be my trainers", "maybe it's my age". The
# pronoun is in the line, but the line is not only pointing at the thread - it puts something of
# its own up as the cause, which is a question about that thing and not about the thread.
_A_CANDIDATE_OF_ITS_OWN = re.compile(
    r"\b(?:it|its|it['\u2019]s|this|that|these|those|they)\b[^.?!,;]{0,24}?"
    r"\b(?:my|our|his|her|their)\s+[a-z]")


def _the_ask_is_the_threads(clean, understood):
    """True when the line asks something about a thing it only points at."""
    if not (ASK_SHAPE.search(clean) and _LEANS_ON_THE_THREAD.search(clean)):
        return False
    # A line that names a thing of its own is asking about that thing, not about the thread: on
    # "my knees hurt after 10 mins" then "is it my shoes", the thread is a body and this reader
    # answered it with the GP's line - "ring 111 or your surgery" - which is the one answer a
    # question about a pair of trainers must not get.
    if _A_CANDIDATE_OF_ITS_OWN.search(clean.lower()):
        return False
    return (understood or {}).get("topic") in _BODY_TOPICS


def _thread_is_about_a_person(memory, look_back=4):
    """True when the last few things the person said named someone else."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-look_back:]:
        words = set(re.findall(r"[a-z']+", (turn.get("user") or "").lower()))
        if words & _THREAD_PEOPLE or REPAIR_PERSON.search(turn.get("user") or ""):
            return True
    return False


def _a_thing_was_named(memory, look_back=4):
    """True when a line before the decision named a thing as well as a person.

    "my son rides his bike to school" / "should i bother fixing it or replace it" is a cost
    question about the bike: the person is only in the earlier line, not the thing being
    weighed, so the cost rule is the answer. "my marriage is on the rocks" / "is it worth fixing
    or shall i leave" names no thing at all, and a marriage is not a broken appliance. The
    reading of each earlier line is the understanding engine's own: it already says what a line
    names and what kind of thing that is, so nothing here keeps a second list of objects.
    """
    from ..understanding import understand  # noqa: PLC0415 - the reading of an earlier line

    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-look_back:]
    for turn in turns:
        said = str(turn.get("user") or "")
        if not said.strip():
            continue
        for entity in understand(said).get("entities") or []:
            if str(entity.get("type")) == "thing":
                return True
    return False

def _names_its_own_thing(clean):
    """True when the repair line names the thing it is about, so the thread is not the subject.

    "is it worth fixing" names nothing and belongs to the thread. "is it worth fixing the garden
    gate" names the gate, and a gate is not the person the thread was about.
    """
    match = REPAIR_DECISION.search(clean)
    if not match:
        return False
    for word in re.findall(r"[a-z']+", clean[match.end():]):
        if word in _NOT_AN_OWN_THING:
            continue
        if word in BODY_PARTS or word in HEALTH_WORDS or word in SYMPTOM_WORDS:
            continue
        if REPAIR_PERSON.search(word):
            continue
        return True
    return False

def _money_decision(clean):
    """Whether the line decides something about money rather than about what a thing is worth."""
    said = set(re.findall(r"[a-z']+", clean))
    if not said & MONEY_WORDS and not _PAY_DEBT.search(clean) and not _CARD_MONEY.search(clean):
        return False
    if _VALUE_OF_THING.search(clean) and not said & _MONEY_NOUN:
        return False
    return True


def _about_a_sore(clean, words):
    """True when the line is about a thing on the body that can be squeezed, picked or covered.

    The doing verb is the question, but it needs a sore, and a sore needs to be the body's: a spot
    and a lump are places and things as well, so one of those words only counts when the line says
    where on the person it is ("my spot", "the lump on my back", "a spot on my chin").
    """
    if not SORE_DOING.search(clean):
        return False
    named = set(words) & SORE_WORDS
    if not named:
        return False
    if named - SORE_AMBIGUOUS:
        return True                     # a scab, a boil, a blister: no other reading
    if not SORE_PICKING.search(clean) or SORE_ONLY_A_BODY.search(clean):
        return True                     # "should i pop a spot" is a chin, not a campsite
    return bool(SORE_PLACE.search(clean))


def _a_call_for_help(clean):
    """The pool for a line asking whether to ring for help, or None when it is another question."""
    if not _ASKS_TO_ACT.search(clean):
        return None
    if _A_PLACE_TO_BE_SEEN.search(clean) and not _A_CALL_WORD.search(clean):
        if DANGER_SYMPTOM.search(clean):
            # "should i go to a&e, i can't stop bleeding" is not a drive, it is a call.
            return RING_FOR_HELP
        if MINOR_HARM.search(clean):
            # A stubbed toe does not need a department: the same stand-down the phone words get.
            return None
        return GO_TO_BE_SEEN
    if EMERGENCY_CALL.search(clean):
        if MINOR_HARM.search(clean) and not DANGER_SYMPTOM.search(clean):
            # The ordinary line for a minor thing, not the emergency one: a friend says no.
            return None
        return RING_FOR_HELP
    if POLICE_CALL.search(clean) and (REACHING_THE_POLICE.search(clean)
                                     or _ASKING_FOR_THE_POLICE.search(clean)
                                     or SOMETHING_HAPPENING.search(clean)):
        return RING_THE_POLICE
    return None


# A repair asked for as a method ("how do i make it right with her", "how do i make it up to my
# mum"), not as a yes or no. APOLOGY_ANSWER answers "should i apologise" and agrees first; the
# person here has already decided, so what they need is the shape of the thing. The person has to
# be named: "my hoover wont pick up" and "how do i fix it" is a machine, and the same words with
# nobody in them are somebody else's question.
REPAIR_HOW = re.compile(
    r"\bhow (?:do|can|could|should|would) (?:i|we)\b[^.?!]{0,40}?"
    r"(?:\bmake (?:it|things|this) (?:right|up)\b|\bmake up for\b|"
    r"\bput (?:it|things|this) right\b|\bsay sorry\b|\bapolog\w*|\bforgive me\b|"
    r"\bclear the air\b)")
REPAIR_ANSWER = (
    "Name the one thing you did, say sorry for it in a sentence, then ask what would help. Short "
    "and about them is what makes it land, and the explaining can come later if they want it.",
    "Do it soon, in person if you can. Say what you did rather than why you did it, and leave "
    "what they did out of it - that is the part that turns an apology into an argument.",
    "One sentence of sorry, then a question: what would make it easier? Most people would rather "
    "be asked than be given a longer apology.",
)


def _a_small_social_decide(clean, words):
    """The pool for an everyday social decision, or None when the line is a different question."""
    if ASKED_OUT.search(clean):
        return ASK_OUT_ANSWER
    if AN_APOLOGY.search(clean):
        return APOLOGY_ANSWER
    said = set(words)
    if _CONTACT.search(clean) and said & _A_PERSON:
        if _CALLING.search(clean):
            return CALL_ANSWER
        return CONTACT_ANSWER
    if said & _A_SOCIAL_THING and _GOING.search(clean) and not _NOT_INVITED.search(clean):
        return GO_ANSWER
    return None


# A method asked for in the person's own voice: "how do i practise", "where should i hang my
# washing", "when do i start". Read on the opening only. Everything with an entry has already had
# its turn before this is read (it stands in for the search hedge at the bottom of the fallback),
# so a line naming a thing the bot has a card for never reaches it.
# "how" and "where" only: a "when should i ..." ask is about timing, and the answer to it is a date
# or a season ("when should i plant tulips" is a calendar question with sources), not a method.
METHOD_OPENING = re.compile(r"^(?:so |ok |okay |and |but )?"
                            r"(?:how|where) (?:do|does|should|shall|can|could|would|might) i\b")
# Two shapes that look like a method ask and are not one, so they keep the answer they had.
#
# "how do i know if im ovulating" asks how to tell something about their body, which is a symptom
# card or a doctor's question, not a method with steps they have tried.
#
# "where can i get my brakes fixed round here" asks for a place: the bot cannot see who is near
# them, and the line it had ("I can't recommend anyone - I've no way to see who's near you...")
# says so and hands them the one thing that works. What have you tried so far is no help at all
# for a car with no brakes, so an ask that names something to obtain or a place to find it keeps
# its own pool.
HOW_TO_TELL = re.compile(r"\b(?:know|tell|check|find\s+out) "
                         r"(?:if|whether|the|a|an|my|your|his|her|its|it's|that|this|which|"
                         r"apart|the\s+difference)\b")
# A method asked about a product - a thing with a manual or a settings menu - is a lookup: "how do i
# take a screenshot on a windows laptop" has guides, and "what have you tried so far" is no way into
# it. The machine words are the ones the rest of the file already reads as things to be serviced;
# the software words are their company. "washing" alone is the laundry in the basket and not the
# machine, so "where should i hang my washing" stays the person's own evening.
_A_PRODUCT = _THREAD_MACHINES | frozenset(
    "router wifi broadband windows android iphone ipad ios mac app apps settings browser email "
    "excel word powerpoint gmail outlook instagram facebook whatsapp tiktok password account".split())
_A_PRODUCT = _A_PRODUCT - frozenset(("washing",))
NOT_A_METHOD = re.compile(
    r"^(?:so |ok |okay |and |but )?(?:how|where) (?:do|does|should|shall|can|could|would|might) "
    r"i (?:get|find|buy|hire|rent|book|order|locate|pick\s+up|put|keep|store)\b"
    # "how should i get ready", "how do i get up earlier", "how do i get better at drawing" are
    # methods; only a thing obtained is left out, so the phrasal and the comparative stay in.
    # "put", "keep" and "store" are the same shape as a thing obtained: "where do i put the bin
    # bags" wants a place somebody decides for you, and the bins and permits card has it, so the
    # placement ask keeps its own answer. Hanging washing is not that - nobody decides where it
    # goes but the person - and it stays a method.
    r"(?!\s+(?:up|better|going|started|through|on|out|round|back|dressed|ready|organised|there|"
    r"in|to)\b)"
    r"|\b(?:round here|near me|nearby|in my area|locally)\b"
    # A question about the bot itself ("how do i know you are telling the truth") is the bot's own
    # to answer, and "what have you got so far" is as much of a non sequitur as the search hedge:
    # it is left to the readings that answer questions about the bot.
    r"|\b(?:you|your|yourself)\b")


def method_ask_pool(clean, memory=None):
    """The pool for a method asked for when nothing else could answer it, else None.

    "how do i practise", "how do i start running" and "where should i hang my washing" got the
    search hedge - "I'm not sure about that one, sorry - I'd rather not guess. A quick search
    online will get you a solid answer" - which is the one answer that helps nobody: the person is
    asking how to do a thing of their own, and there is nothing to look up about it. What a friend
    says is what they have tried so far, which is also the only way the bot can help.

    The hedge is right for a question about the world, so this only takes a line nothing else
    answered, and only one that asks for a method in the person's own voice: a line with no
    "how/where/when ... i" at its front is not read here at all.
    """
    if not METHOD_OPENING.match(str(clean or "")):
        return None
    if HOW_TO_TELL.search(clean) or NOT_A_METHOD.search(clean):
        return None
    if set(re.findall(r"[a-z']+", str(clean or ""))) & _A_PRODUCT:
        return None
    if _DEFINITION.search(clean):
        return None
    # After the bot's own answer, the thing the ask is about is that answer, so asking what they
    # have tried about it is a non sequitur: the way in points at the part that did not land.
    if _answered_already(memory if isinstance(memory, dict) else {}):
        return HELP_ALREADY
    return TIPS_LINES


def unknown_pool(clean, words=()):
    """The pool for a question the bot cannot answer, chosen by the kind of question it is."""
    words = words or clean.split()
    if HANDS_IT_BACK.match(clean):
        return HANDS_BACK
    calling = _a_call_for_help(clean)
    if calling:
        return calling
    # A repair asked for as a method ("how do i make it right with her", "how do i make it up to
    # my mum"): the person has decided to apologise and wants the shape of it, which is a concrete
    # answer a friend gives. It is read before the decide gate because "how do i" is not one of
    # the shapes DECIDE_OPENING reads, and with the person named, because the same words about a
    # machine ("how do i fix my hoover") are somebody else's question.
    if REPAIR_HOW.search(clean) and set(words) & _A_PERSON:
        return REPAIR_ANSWER
    if _reads_as_worry(clean, words):
        return UNKNOWN_WORRY
    if _about_a_sore(clean, words):
        if set(words) & SORE_SERIOUS:
            return UNKNOWN_HEALTH
        return SORE_HANDS
    if PLASTER_ON.search(clean):
        return PLASTER_IT
    if any(phrase in clean for phrase in WORD_ANYWHERE) and not (_CREATIVE & set(words)):
        return UNKNOWN_WORD
    # "do i clean the head or the tray first" is not an unknown ask: it is an order, and the
    # light-choice reader never sees it (the shape is not a bare "x or y"). Read it here, after
    # the health and worry lines that must keep their own answer.
    if not _DEFINITION.search(clean) and _an_order_of_work(_choice_sides(clean), clean):
        return ORDER_OF_WORK
    if ((DECIDE_OPENING.search(clean) or DECIDE_SANITY.search(clean))
            and not _DEFINITION.search(clean)):
        if (set(words) & (HEALTH_WORDS | SORE_SERIOUS)
                or any(phrase in clean for phrase in CHECK_PHRASES)):
            return UNKNOWN_HEALTH
        if _money_decision(clean):
            return UNKNOWN_MONEY
        social = _a_small_social_decide(clean, words)
        if social:
            return social
        return UNKNOWN_DECIDE
    return UNKNOWN


# The topics where a filling is something you eat. A dish in the conversation makes the next
# "what filling should i use" a kitchen question, and the topic is carried, so the line itself
# does not have to say "cake" for this to hold.
FOOD_TOPICS = frozenset(("cooking", "food-and-drink"))
# "i overdosed on cake" is a joke about eating too much, and the 999 card belongs to a drug: a food
# word with no drug word on the line is the joke, so the emergency words pass it and the food lane
# answers it. "i overdosed on painkillers" keeps the call, and a drug word anywhere does.
OVERDOSE_FOOD = re.compile(
    r"\boverdos(?:e|ed|ing)\b[^.!?]{0,12}\b(?:on|of|with)\s+(?:the\s+|a\s+|some\s+)?"
    r"(?:cake|cakes|chocolate|sweets|candy|biscuits?|cookies|crisps|chips|chinese|curry|pizza|"
    r"ice\s*cream|cheese|coffee|tea|netflix|tv|telly|sugar|bread|"
    r"pastr(?:y|ies)|do(?:ugh)?nuts|burgers?|takeaways?|naps|love|pies?|pudding|trifle|"
    r"turkey|roast|stuffing|mince|gravy|easter\s+eggs?)\b")
OVERDOSE_DRUG = re.compile(
    r"\b(?:pills?|tablets?|paracetamol|ibuprofen|painkillers?|meds|medicines?|"
    r"sleeping\s+pills?|antidepressants?|insulin|heroin|heroine|cocaine|methadone|tramadol|"
    r"codeine|morphine|opioid|opiates?|drugs?|liquid|bottle|packet|pack|box|strip|blister|"
    # A drink is the drug, not the joke: "i overdosed on vodka" is the ambulance.
    r"alcohol|vodka|whisky|whiskey|wine|beer|gin|rum|brandy|tequila|lager|cider|champagne|"
    r"prosecco|ros\u00e9|spirits?|drink|drinking|booze)\b")
# Unresponsive *to* something is not unresponsive: "my baby is unresponsive to her new milk" is a
# feeding problem, "my boss was unresponsive to my emails" is a work one. safety.py carries the
# same tail guard for its own lines; the comma form ("... and unresponsive, call 999") stays an
# emergency because nothing follows the word.
UNRESPONSIVE_TAIL = re.compile(r"\bunresponsive\b\s*(?:to|when|whenever|if|because|as|after|"
                              r"with|about|on)\b")
# Except a feed: "my baby is unresponsive to her milk" is a parent saying the baby will not wake
# after a bottle, so the tail guard must not take the call away from it. The line is the same red
# flag as "my baby is unresponsive" and as "my baby is not responding to her feed".
FEED_TAIL = re.compile(
    r"\bunresponsive\b\s*(?:to|after|during|at|following)\s+(?:the|a|an|her|his|my|their|this|"
    r"that|some)?\s*(?:(?:new|old)\s+)?(?:milk|formula|feeds?|feeding|bottle|breast|solids|"
    r"weaning)\b")


def _the_thing_is_choking(clean, words):
    """True when a choking state belongs to a thing: the engine, the drain, the bike chain.

    Only the choking phrases are read this way: an engine chokes and so can a drain, but a thing
    does not stop breathing or go unconscious. Two halves make the test, and both are needed:
    a thing named right beside the state word, and no person anywhere in the line. A real
    choking emergency names a person ("my son", "she") or names nobody at all ("choking"),
    and both of those keep the ambulance.

    The thing has to be the **subject** of the state, the word just before "is choking" or
    "choking on", not merely a word in the window. gray-palm on #2088: `hes choking on a car key`
    has no token from `BODY_SUBJECT` (it has `hes`) and the window picks up `car`, so a window
    rule loses a child choking to the thing in his mouth. Reading the subject makes an unknown
    word - a name, a contraction, "the drain in the kitchen" - keep the ambulance, which is the
    right cost: a missed ambulance is the one thing this guard must not do.
    """
    if not any(phrase in clean for phrase in THING_STATES):
        return False
    if set(words) & BODY_SUBJECT:
        return False
    tokens = clean.replace("'", "").split()
    for i, word in enumerate(tokens):
        if word != "choking":
            continue
        before = tokens[max(0, i - 4):i]
        # "my car engine is choking": skip the copula so the subject is the word before it.
        while before and before[-1] in _COPULA:
            before.pop()
        if before and before[-1] in THING_SUBJECT:
            return True
    return False


# "i cant wake my baby up" is the same emergency as "wont wake", but only when there is a person
# to wake: "i cant wake up in the mornings" is a sleep habit.
CANT_WAKE = re.compile(r"\b(?:can ?t|cannot|could ?nt)\s+(?:wake|rouse)\s+(?:him|her|them|my|"
                       r"the (?:baby|child|kid|boy|girl|man|woman|old man|old woman))\b")
# "my husband wont wake up for work" is a habit, not an emergency: a wake-up line with a routine
# reason in it is about mornings, not about breathing.
ROUTINE_WAKE = re.compile(
    # The reason can be a place, a vehicle, an appointment or a start time: "wake up for the
    # school bus", "wake up before his exam", "wake up in time for her shift". safety.py carries
    # the same shapes; without them here the composer read the line as a collapse and rang 999
    # for a family trying to catch a train.
    r"\b(?:for|to|before|in time for|on time for) (?:work|school|college|uni|university|nursery|"
    r"childminder|the gym|his work|her work|their work|the (?:school )?(?:bus|train)|"
    r"(?:his|her|their|my|an|a) (?:exam|exams|test|appointment|meeting|interview|flight|"
    r"lesson|lecture|class|early start)|"
    # A shift is the same morning as work, and people name which one: "his early shift",
    # "her night shift", "the late shift at the hospital".
    r"(?:his|her|their|my|the|an|a) (?:early|late|night|day|double|morning|afternoon|evening)?\s*"
    r"shift(?:\s+(?:at|on|tomorrow|today|in)\b[^.]{0,25})?)\b|"
    r"\bto get (?:to|ready for) (?:school|work|college|uni|university|nursery)\b|"
    r"\bin the mornings?\b|"
    r"\bevery (?:morning|monday|tuesday|wednesday|thursday|friday|saturday|sunday|day|week)\b|"
    r"\bon (?:school )?(?:days|weekdays|mondays?|weekday mornings?)\b")
# "im choking on my words" is a stutter: the thing choked on is speech, so the airway word in the
# line is not about an airway. safety.py carries the same shape for its own card.
CHOKE_ON_A_WORD = re.compile(
    r"\bchok(?:e|ed|es|ing)?\s+on\s+(?:(?:my|his|her|their|your|our|the|a|an)\s+)?(?:own\s+)?"
    r"(?:words?|sentences?|speech|lines?|names?|syllables?|pronunciation)\b")
# "i overdosed on coffee", "an overdose of meetings": too much of a good thing, so the word is not
# an ambulance. A pill or a poison named in the line beats the treat words, and safety.py carries
# the same shape for its own card.
OVERDOSE_OF_A_TREAT = re.compile(
    r"\boverdos(?:e|ed|ing)\s+(?:on\s+)?(?:(?:the|a|an|my|his|her|their)\s+)?"
    r"(?:coffee|caffeine|tea|chocolate|cake|sugar|sweets|crisps|biscuits|cheese|ice\s+cream|"
    r"tv|telly|netflix|box\s+sets?|sleep|sun|sunshine|shopping|gossip|christmas\s+music|"
    r"work|meetings?|emails?|paperwork|spreadsheets?)\b"
    r"|\ban\s+overdose\s+of\s+(?:coffee|caffeine|tea|chocolate|cake|sugar|sweets|tv|telly|"
    r"netflix|box\s+sets?|sleep|sun|sunshine|shopping|gossip|work|meetings?|emails?|paperwork|"
    r"spreadsheets?|christmas\s+music)\b")
# ...but a tablet, an insulin dose or a poison in the line is the real thing whatever else it says.
OVERDOSE_A_PILL = re.compile(
    r"\b(?:pills?|tablets?|paracetamol|ibuprofen|insulin|meds|medicines?|bleach|antifreeze|"
    r"heroin|opioids?|tramadol|antidepressants?)\b")
# The faint that is still coming needs the first move, not the appointment. "im going to pass out"
# was answered "Ring 111 or your surgery this week", which is the right advice for a faint that
# has already happened and no use to somebody who is about to go down on a kitchen floor. The
# signs that make it an emergency are settled above this, so the same-day line is what is left at
# the end: sit or lie down now, then be seen today.
FAINT_COMING = re.compile(
    r"\b(?:about|going|gonna)\s+to\s+(?:pass\s+out|faint|black\s+out|collapse|go\s+down)\b"
    r"|\b(?:feel|feels|feeling|felt|think|thinking|look|looking)\s+(?:like\s+)?"
    r"(?:im|i'm|he|she|they)\s+(?:going|gonna|about)\s+to\s+"
    r"(?:pass\s+out|faint|black\s+out|collapse)\b"
    r"|\bnearly\s+(?:passed\s+out|fainted|blacked\s+out)\b"
    r"|\bmight\s+(?:pass\s+out|faint|black\s+out|collapse)\b"
    r"|\b(?:going|gonna)\s+(?:down|faint)\b")

# "i blacked out the windows with curtains" is a verb about a window, not a person going under.
BLACKED_OUT_A_THING = re.compile(
    r"\bblack(?:ed|ing)\s+out\b\s+(?:the|a|an|my|our|his|her|their|all\s+the)\s+"
    r"(?:\w+\s+){0,2}(?:window|windows|room|rooms|light|lights|sun|view|glass|door|doors)\b")
# A person has to be somewhere in the line for it to be about their sight: "everything went black"
# on its own is a power cut, and the lines about a thing have a thing in them, not a person.
BLACKOUT_PERSON = re.compile(
    r"\b(?:i|im|id|ive|me|my|myself|he|hes|she|shes|they|we|us|him|her|his|their|our)\b")

# A machine chokes on its fuel or its muck, not on a bit of food: "my car engine is choking" and
# "the traffic is choking the high street" are not a person in trouble, and the 999 card is the
# worst thing to say to either of them. The choke has to belong to the thing, with no person named
# anywhere in the line, so "my dad choked in the car" keeps every reading.
CHOKE_MACHINE = re.compile(
    r"\b(?:kitchen\s+sink|sinks?|drain\w*|pipes?|toilet|loo|gutter\w*|chimney|radiator|filter|"
    r"engines?|car|van|motorbike|mower|lawnmower|hoover|vacuum|dishwasher|printer|traffic|"
    r"weeds?|lawn|flowerbed\w*|bog|moss|inbox|budget|schedule|calendar|tears?)\b"
    r".{0,30}\bchok\w*\b"
    r"|\bchok\w*\b.{0,30}\b(?:on|with)\s+(?:fuel|petrol|diesel|weeds|leaves|moss|traffic|hair|"
    r"paper|dust|fat)\b")
# A pronoun object counts as a person: "the pipe is choking him" is a body in trouble with the pipe
# as the cause, and the thing word must not take the card from them.
CHOKE_BODY = re.compile(
    r"\b(?:he|she|they|them|him|me|us|i|his|her|their|mum|mom|mother|dad|father|son|daughter|"
    r"husband|wife|partner|brother|sister|friend|baby|child|kid|boy|girl|man|woman|gran|granny|"
    r"nan|grandad|grandma|grandpa|toddler|newborn|infant|mate|neighbou?r)\b")

TAG_CAN = re.compile(r"\bcan\b")
# A follow-up that is only the question ("is that why", "will it stop", "does that matter")
# names nothing for the bot to answer about. The search shrug told the person nothing at all -
# "ive tried a spray / will it stop" got "a quick search online will get you a solid answer" -
# and asking which bit is both honest and keeps the conversation going, which the shrug does not.
BARE_FOLLOW_UP = re.compile(
    r"^(?:and |so |but |ok |okay |right |also |well )*"
    r"(?:is|was|are|were|will|would|does|do|did|can|could|should|has|have|had)"
    r" (?:that|this|it|they|those|these|there)"
    # A tail of its own is a subject - "will it stop raining" is a weather question, not a
    # follow-up - so only the verbs a follow-up is made of may follow the pronoun.
    r"(?: (?:stop|help|work|matter|count|last|clear|ease|go|mean|hurt|pass|settle|fade|fix"
    r"|sort|change|show|be|get|keep|stay|take|worsen|spread|why|how|where)"
    r"(?: (?:up|off|away|out|long|better|worse|anything|enough|now|soon|all|of|it|then|again)){0,2})?"
    r"[?.!]*$")
# What makes the thread one of those: the same readings every other module uses for heavy news,
# asked of the person's own last line.
def _the_line_before(memory):
    """What the person said on the turn before this one, or "" on the first turn."""
    if not isinstance(memory, dict):
        return ""
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    return str(turns[-1].get("user") or "") if turns else ""


def _reads_as_heavy_news(text):
    """True when a line is heavy news - a death, a diagnosis, a loss - rather than an ordinary one.

    The wording pools are for somebody stuck on what to say; a person who says "my daughter died
    and i dont know how to tell my son" is not asking for a shape to put it in first, and the
    grief answer has to win. So the doubt-in-front-of-tell reading stands down on heavy news and
    the later branches read it as what it is.
    """
    said = (text or "").lower()
    return bool(said) and bool(loss.reads_as_loss(said)
                               or reads_as_bad_news(said)
                               or badnews.reads_as_sudden_loss(said))


def _the_thread_is_heavy(memory):
    """True when the line just before this one was heavy news rather than an ordinary turn."""
    return _reads_as_heavy_news(_the_line_before(memory))

# "should i turn it off" straight after the bot has answered about a faulty machine. The line
# reads as a question of taste by its grammar, so it reached UNKNOWN_DECIDE - "That's your call,
# not mine" - which is the one answer that helps nobody: whether to switch a knocking boiler off
# for the night is a fact about the boiler, not the person's weighing up. It was worst where the
# bot had already said to switch the thing off: "the plug socket is sparking" / "should i turn it
# off" got "that's your call" back at it.
# The pronoun has to be the machine, so a bare "should i turn it off" with nothing in the thread
# keeps its honest shrug, and the answer is only ever about a thing of the person's that runs.
SWITCH_OFF_ASK = re.compile(
    r"\b(?:should|shall|do)\s+i\s+(?:just\s+|really\s+|now\s+)?"
    r"(?:(?:turn|switch|shut|power|cut)\s+(?:it|that|this|them|those)\s+off"
    r"|(?:unplug|disconnect|isolate)\s+(?:it|that|this|them|those)"
    r"|stop\s+(?:using|running)\s+(?:it|that|this)"
    r"|take\s+the\s+battery\s+out"
    r"|switch\s+(?:it|that|this)\s+off\s+at\s+the\s+wall)")
# The machines this is asked about by somebody with one going wrong in front of them. A phone or a
# laptop is left out on purpose: "my phone gets really hot / should i turn it off" is a question
# about losing the thing for the evening, which is the person's own call after all.
SWITCH_OFF_THINGS = frozenset((
    "boiler", "boilers", "heating", "radiator", "radiators", "immersion", "pump", "pumps",
    "washer", "washing", "machine", "dryer", "tumble", "dishwasher", "oven", "cooker",
    "hob", "grill", "microwave", "kettle", "toaster", "shower", "socket", "sockets",
    "plug", "plugs", "extension", "fuse", "wire", "wiring", "alarm", "alarms", "smoke",
    "chimney", "extractor", "fan", "heater", "appliance"))
# A fridge and a freezer are the two where switching off is the worse advice: the fault is not
# going to burn the house down and a day without power to it is a bin bag of food. Both keep the
# honest answer they had.
# A stove is not switched off either - it is a fire, and it burns down - so a smoking wood burner
# keeps the answer it has rather than being told to turn itself off.
KEEP_IT_RUNNING = frozenset(("fridge", "freezer", "freezers", "fridges", "stove", "stoves",
                             "burner", "burners", "woodburner", "chiminea", "brazier",
                             "barbecue", "bbq", "smoker", "fireplace"))
# What makes it a fault rather than a machine the person is simply running: the noise, the water,
# the heat, the smoke. Without one of these the line is a question about the bill - "the heating is
# expensive / should i turn it off" is money, and "switch it off and have it looked at" is
# nonsense for it. The bot's own answer telling them to switch it off counts as the fault too.
SWITCH_OFF_FAULT = frozenset((
    "noise", "noisy", "knocking", "knocks", "knock", "banging", "bangs", "rumbling",
    "humming", "hums", "buzzing", "buzzes", "rattling", "grinding", "screeching", "squealing",
    "sparking", "sparks", "smoking", "smoke", "leak", "leaks", "leaking", "leaked", "dripping",
    "drips", "drip", "tripping", "trips", "tripped", "blowing", "blown", "fuse", "fault",
    "faulty", "broken", "broke", "stopped", "stops", "stopping", "cutting", "cuts", "hot",
    "overheating", "burnt", "burning", "scorch", "smell", "smells", "smelly", "beeping",
    "beeps", "chirping", "chirps", "flashing", "flashes", "error", "stuck", "jammed", "weak",
    "losing", "pressure", "condensation", "damp", "screech", "clunking", "clicking", "hissing"))
# Gas, carbon monoxide and a fire in the room are not "switch it off" turns at all: the safety
# line has already told them to get out and ring, and telling somebody to go back in and reach for
# a switch is the one thing that could hurt them. "Smoke alarm" is the exception - there the
# question is about the battery, not about going near a fire.
# Gas, carbon monoxide and fumes are never a "switch it off" turn: the safety line has already
# told them to get out and ring, and telling somebody to go back into a room and reach for a switch
# is the one thing that could hurt them.
SWITCH_OFF_GET_OUT = re.compile(
    r"\b(?:gas|gasoline|petrol|carbon monoxide|fumes?|flames?|ablaze|on fire|fire brigade)\b")
# Smoke is the same only when it is loose in the room. Where the bot's own answer has already told
# them to switch the thing off - "smoke coming out of my laptop" was answered "switch it off at the
# wall and unplug it" - the follow-up is asking whether they meant it, and confirming is the reply.
SMOKE_ABOUT = re.compile(r"\b(?:smoke|smoking|smoulders?|smouldering|scorch(?:ed|ing)?)\b"
                         r"(?!\s+alarm)")
# What the bot's own last answer said, when it had already told them to do it.
ALREADY_SAID_OFF = re.compile(
    r"\b(?:turn|switch|shut|power)\s+(?:it|that|this|the\s+\w+)\s+off"
    r"|\bunplug|\bleave\s+it\s+off|\boff\s+at\s+the\s+wall|\bswitch(?:ed)?\s+off|\bstop\s+the\s+cycle")
SWITCH_OFF_ALREADY = (
    "Yes - that is the thing to do, and I would do it now rather than after one more try. Off and "
    "left off is the safe place for it until somebody has looked at it.",
    "Yes, do that: off at the wall, and leave it off. Whatever is wrong with it does not get "
    "better for being run again tonight.",
    "Yes. Switch it off, unplug it if the plug is easy to reach, and leave it alone until it has "
    "been looked at properly.",
)
SWITCH_OFF_ADVISE = (
    "I would. Switch it off and leave it off, then get somebody to look at it - a fault you can "
    "hear or see is the one thing running it again makes worse.",
    "Yes - off, and a call to somebody who can look at it. A night without it is much cheaper "
    "than a night with it leaking, smoking or banging away.",
    "Turn it off and leave it off until somebody has seen it. If you can smell burning or see "
    "anything black, stop using it today rather than waiting for it to get worse.",
)
# Taking the battery out of a chirping smoke alarm is the one switch-off where the safe answer is
# no: the noise stops and so does the alarm, on the night it might be needed.
SWITCH_OFF_BATTERY = (
    "Swap it rather than leaving it out: a chirping alarm is annoying, an alarm with no battery in "
    "it is useless on the night it matters. If a fresh battery does not stop the chirp, take the "
    "whole unit down and get a new one - and if it is mains wired, take it off its base rather "
    "than leaving it with no battery at all.",
)


def _a_switch_off_asked(memory, clean):
    """The pool for "should i turn it off" about a machine in a thread the bot has just answered.

    Nothing at all when the thread names no machine this is safe to answer for: the honest shrug
    is better than advice about a thing the bot cannot see.
    """
    if not SWITCH_OFF_ASK.search(clean):
        return None
    said = " " + _the_line_before(memory).lower() + " "
    answer = " " + memory_bot(memory).lower() + " "
    thread = said + answer
    things = set(re.findall(r"[a-z']+", thread))
    if not (things & SWITCH_OFF_THINGS):
        return None
    if things & KEEP_IT_RUNNING:
        return None
    if "battery" in clean and (things & frozenset(("alarm", "alarms", "smoke"))):
        # Only the chirp of a dying battery: a nuisance alarm that keeps going off at the pan is a
        # different question, and the answer to it is where the alarm sits, not the battery.
        if things & frozenset(("beeping", "beeps", "chirping", "chirps", "chirp", "beep")):
            return SWITCH_OFF_BATTERY
        return None
    if SWITCH_OFF_GET_OUT.search(said):
        return None
    # The bot's own last answer can be the safety one, and then the question is not a household
    # judgement at all: "the plug socket is sparking" is answered "unplug it if you can do it
    # without touching anything hot ... ring 999 or 911", and "should i turn it off" back at that
    # was told "off at the wall", which sends somebody back to a socket that is spitting. Where
    # the safety line has spoken this turn it keeps the thread, so the only answer here is none.
    if SWITCH_OFF_GET_OUT.search(answer) or "999" in answer or "911" in answer:
        return None
    if ALREADY_SAID_OFF.search(answer):
        return SWITCH_OFF_ALREADY
    if SMOKE_ABOUT.search(said):
        return None
    if things & SWITCH_OFF_FAULT:
        return SWITCH_OFF_ADVISE
    return None
UNKNOWN = (
    "I'm not sure about that one, sorry — I'd rather not guess. A quick search online will "
    "get you a solid answer, and I can help you make sense of what you find.",
    "That's beyond what I know well, sorry. Searching for it will turn up better sources than "
    "I can offer; tell me what you find and I'll help you weigh it up.",
    "I don't know enough to answer that honestly. A search should sort you out quickly — and "
    "I'm happy to help with the rest of it.",
)
# "did you see the match last night" is not a person asking the bot to look something up: it is the
# first half of a conversation, and the search hedge ("A quick search online will get you a solid
# answer") tells them to go and read about their own evening. So the shape is read as the
# invitation it is and the reply asks for the story - the same turn a friend gives, and the one
# that lets the person say the thing they came to say. Two guards keep it off the lines that are
# not this: a thing of the person's own ("did you see my keys anywhere", "did you see the doctor")
# is a question the bot can help with, and so is a reading it genuinely cannot do from here (the
# forecast, the listings, the scores), which keep the honest hedge.
ASKED_IF_I_SAW = re.compile(
    r"^\s*(?:(?:and|so|but|oh|ah|anyway|anyways|well|hi|hey|right|now|look)\s+)*"
    r"(?:did|have|do)\s+(?:you|u)\s+"
    r"(?:see|seen|hear|heard|watch|watched|catch|caught|read|follow|following)\s+"
    r"(?:the|that|about|any|much)\b")
# The tail that makes it the person's own business rather than the day's news, and the one that
# asks the bot to have followed what the person said rather than the world.
NOT_THE_NEWS = re.compile(
    r"\b(?:my|our|mum|mom|dad|mother|father|wife|husband|partner|boyfriend|girlfriend|son|"
    r"daughter|kid|kids|child|children|baby|brother|sister|nan|grandma|grandad|granny|friend|"
    r"boss|manager|colleague|neighbour|landlord|doctor|gp|nurse|dentist|midwife|vet|surgeon|"
    r"appointment|letter|email|e-mail|bill|invoice|results?|test)\b"
    r"|\bwhat i (?:said|mean|meant|wrote|sent|told you|asked)\b")
# What cannot be done from here keeps its honest answer: these are lookups, not a chat.
LOOKED_UP = re.compile(
    r"\b(?:forecast|weather|news|listings?|scores?|results?|prices?|times?|timetable|"
    r"timetables|traffic|schedule|opening|hours|fixtures?|table|standings|reviews?|ratings?)\b")
# "did you see it" is the commonest way to ask, and "it" is only knowable from the line above:
# after "we watched the final together" the thing being asked about is the final, and the search
# hedge ("a quick search online will get you a solid answer") is an answer to a lookup nobody
# made. The referent is read from the previous turn and the noun has to be one you watch, so
# "my results came back" and "did you see it" is still the results, not a match.
SAW_IT = re.compile(
    r"^\s*(?:(?:and|so|but|oh|ah|anyway|anyways|well|hey|right|now)\s+)*"
    r"(?:did|have|do)\s+(?:you|u)\s+"
    r"(?:see|seen|hear|heard|watch|watched|catch|caught)\s+"
    r"(?:it|that|him|her|them)\b"
    r"(?:\s+(?:last night|the other night|yesterday|tonight|today|this morning|on saturday|"
    r"at the weekend|yet))?\s*\??\s*$")
WATCHABLE = re.compile(
    r"\b(?:match|game|final|semi(?:-final)?|film|movie|episode|documentary|show|series|"
    r"season|race|fight|gig|concert|play|debate|episode|highlights|"
    # A match is often named by its parts: "i saw the whole second half" is the thing they want
    # to talk about, and "did you see it" is the ask for it rather than a check on what they said.
    r"first half|second half|highlights|extra time|finale)\b")
# The rest of what people ask whether the bot saw: the day's news that is talked about rather
# than looked up, and the words that stand in for a match without naming one.
SAW_NEWS = re.compile(
    r"\b(?:election|football|rugby|cricket|tennis|boxing|olympics|formula one|f1|"
    r"the budget|budget|the bill|the vote|referendum|the debate|the interview|the speech|"
    r"the wedding|the funeral|the fight|the final|the match|the game|the semi)\b")


def names_the_thing_worth_watching(clean):
    """True when a "did you see the ..." line names something a person watches.

    "did you see the match last night" opens a conversation; "did you see the state of the
    kitchen", "did you see the queue at the post office" and "did you see the postman" are not
    about anything watched, and a match reply to them ("Not a bit of it. Tell me - what
    happened?") reads as a bot that was not listening. Only the noun the line names is read,
    and only the four words after it, so a later clause cannot make a line this one.
    """
    said = SAW_IT_OR_THE.match(clean)
    if not said:
        return False
    tail = " ".join(clean[said.end():].split()[:5])
    return bool(WATCHABLE.search(tail) or SAW_NEWS.search(tail))


SAW_IT_OR_THE = re.compile(
    r"^\s*(?:(?:and|so|but|oh|ah|anyway|anyways|well|hi|hey|right|now|look)\s+)*"
    r"(?:did|have|do)\s+(?:you|u)\s+"
    r"(?:see|seen|hear|heard|watch|watched|catch|caught|read|follow|following)\s+"
    r"(?:the|that|about|any|much)\b")
def reads_as_if_i_saw(text, memory=None):
    """True when the line asks whether the bot saw the thing the person is talking about.

    Held as one reading because it is used twice: where the reply is chosen, and where the
    composer says the line is its own (bot/modules/greeting.takes_as_it_comes). The memory store
    reads "did you see it" as a question about what the person just said - "Yes - you watched the
    final together" - at PRIORITY 7000, so the composer never got the line until it claimed it.
    """
    clean = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not clean or NOT_THE_NEWS.search(clean) or LOOKED_UP.search(clean):
        return False
    if SAW_IT.match(clean):
        return bool(WATCHABLE.search(str(last_user(memory) or "").lower()))
    if ASKED_IF_I_SAW.match(clean):
        return names_the_thing_worth_watching(clean)
    return False


# The same evening, asked about one more step along: not whether the bot saw it, but a detail of
# it put to somebody who might have been there. "were jess and tom there", "did she like it", "who
# else was there", "was the food good" have no lookup behind them - the afternoon happened to the
# person - so the search hedge ("a quick search online will get you a solid answer") sent them to
# the internet to find out about their own day. The bot was not there, says so in as many words,
# and asks the question that gets the story (`WASNT_THERE`).
WAS_THEY_THERE = re.compile(
    r"^[^a-z]*(?:was|were)\s+(?:he|she|they|everyone|anyone|anybody|everybody|you|u)\s+"
    r"(?:there\b|at\s+\w|with\s+\w)")
WAS_A_NAMED_ONE_THERE = re.compile(
    r"^[^a-z]*(?:was|were)\s+(?P<who>[a-z][a-z'-]*)"
    r"(?:\s+and\s+(?P<also>[a-z][a-z'-]*))?\s+there\b")
# "did she like it", "did they enjoy it", "did he make it". "have" is left out on purpose: "did
# you have a good day" is small talk aimed at the bot, not a question about somebody's afternoon.
DID_THEY_GO = re.compile(
    r"^[^a-z]*(?:did|do|does)\s+(?:he|she|they|you|u)\s+"
    r"(?:like|enjoy|love|hate|go|come|make it|get there|stay|leave|arrive|say|think|"
    r"manage|turn up|show up|win|win it|lose|lose it|draw|score|play well|do well)\b")
# What an opinion of something that already happened is said with: "did you think it was good",
# "did you think the film was any good", "do you think she liked it". Without one of these after
# "do you think", the line is asking whether the bot agrees with a plan or a feeling.
# A look back at something that happened still needs something to look back at: a person who was
# there ("she liked it", "they played well") or a thing that was ("the food was ok", "my mum liked
# it"). Without one the line is about their own conduct - "do you think it was my fault", "do you
# think that was a mistake" - and the day-they-were-at reading answered it with a room the bot was
# never in.
A_THING_OR_A_PERSON = re.compile(
    r"\b(?:he|she|they|we|us|him|her|them|the|my|our|his|their)\s+\w+")
A_LOOK_BACK = re.compile(
    r"\b(?:was|wasnt|wasn't|were|werent|weren't|had|hadnt|hadn't|did|didnt|didn't|"
    r"liked|enjoyed|loved|hated|went|came|said|managed|stayed|left|arrived|won|lost|scored|"
    r"turned up|showed up|played|worked)\b")
# A detail asked of the thing rather than of a person: "was the food good", "was it busy",
# "was everything alright".
WAS_IT_ANY_GOOD = re.compile(
    r"^[^a-z]*(?:was|were)\s+(?:it|that|everything|everyone|the\s+\w+|my\s+\w+|your\s+\w+|"
    r"his\s+\w+|her\s+\w+|their\s+\w+|our\s+\w+)\s+"
    r"(?:good|nice|busy|packed|fun|loud|quiet|worth it|any good|any cop|a laugh|any fun|"
    r"alright|all right|ok|okay|terrible|awful|great)\b")
# The same detail about the people who went, named as a group: "were your parents there",
# "did the kids have fun", "were the neighbours there". The noun has to be a person in the line,
# so "were the plates there" and "was the car there" are not read as this.
PEOPLE_WHO_WENT = frozenset("""kids children child parents mum mom dad mother father family
friends friend sister brother wife husband partner boss neighbours neighbors cousins
grandparents grandmother grandfather aunt uncle colleagues classmates team group others
lot guests everyone""".split())
WENT_AND_WERE_ASKED = re.compile(
    r"^[^a-z]*(?:was|were|did)\s+(?:my|your|his|her|their|our|the)\s+(?P<noun>\w+)\s+"
    r"(?:there|about|around|have|enjoy|like|come|go|stay|leave|arrive|make it|get there|say)\b")
WHO_WAS_THERE = re.compile(
    r"^[^a-z]*(?:who\s+else|who|anyone else|anybody else)\s+"
    r"(?:was|were|went|came|turned up|showed up|there)\b")
# A question about somebody being hurt is not a question about how the day went: "did he hit you"
# is the safety pools' and never this one.
HURT_IN_THE_LINE = re.compile(
    r"\b(?:hit|hits|hurt|hurts|touch|touched|hands? on|force|forced|push|pushed|shove|shoved|"
    r"grab|grabbed|threaten|threatened|threat|abuse|abusive|shout|shouted|yell|yelled|"
    r"corner|cornered)\b")
# The words that are never a name in "were X there": determiners, pronouns and the ordinary nouns
# that sit in that slot. Both halves of "jess and tom" have to be names, so "were the plates
# there" and "was it there" are not read as people.
NOT_A_NAME = frozenset("""it that this these those there here the a an any some every no not
everything nothing something anything anyone anybody everyone everybody somebody someone
he she they you u we i him her them us me my your our their his its one ones thing things
day night week weekend time food meal party wedding dinner lunch trip holiday service drive
journey flight train bus match game film show weather traffic lunch tea supper""".split())


def _asked_about_the_day_they_had(clean):
    """True when the line asks a detail of something the person was at, as if the bot were there.

    "were jess and tom there", "did she like it", "who else was there", "was the food good" -
    every one of them is about a room the bot was not standing in, so there is nothing to look
    up. A line about the news, the weather, prices or a score keeps its own pools: those really
    can be searched for.
    """
    if HURT_IN_THE_LINE.search(clean) or LOOKED_UP.search(clean):
        return False
    if WAS_THEY_THERE.match(clean) or WAS_IT_ANY_GOOD.match(clean) or WHO_WAS_THERE.match(clean):
        return True
    went = DID_THEY_GO.match(clean)
    if went:
        # "do you think" is the same words in two different asks: "did you think the film was any
        # good" asks for an opinion of something that happened, and "do you think i should tell
        # her" asks whether the bot agrees with a plan. Reading the second as the first told a
        # person "I wasn't there, so I can't say - I only know what you tell me. How did it go?"
        # about their own decision, and the same thing happened to "do you think i should go to
        # the doctor", "do you think they will come" and "do you think im too old to start". So
        # "think" counts only where a look back at something that already happened is in the
        # line, and every other verb in the list ("did you like it", "were they there") is
        # already about the day itself.
        verb = clean[went.start():went.end()].rstrip()
        if verb.endswith("think"):
            # "did you think" is already in the past, so the line is a look back whatever follows
            # it ("did you think id like it"). "do you think" is the ask that could be either, and
            # only the look-back words settle it.
            if verb.startswith("do") or verb.startswith("does"):
                said = clean[went.end():]
                if not A_LOOK_BACK.search(said) or not A_THING_OR_A_PERSON.search(said):
                    return False
        return True
    if WENT_AND_WERE_ASKED.match(clean) and WENT_AND_WERE_ASKED.match(clean).group("noun") in PEOPLE_WHO_WENT:
        return True
    named = WAS_A_NAMED_ONE_THERE.match(clean)
    if not named:
        return False
    who = named.group("who")
    also = named.group("also")
    if who in NOT_A_NAME or (also and also in NOT_A_NAME):
        return False
    return True


# A bare ask to choose has no answer until it knows what for. "what should i wear" sent the
# person to a search engine, which is a shrug on a question a friend answers with one question
# back - and the same seven words with a subject ("what should i wear to a wedding") already have
# an entry of their own, so the only lines left here are the ones that name the choosing and
# nothing to choose between. "what should i do" is that shape too, and it is the widest ask in
# English: not a fact nobody has, but a person asking for a hand. The verb is the only thing the
# line gives, so the verb picks the pool; nothing here names a subject the line did not have.
# The modal is the whole difference between a person asking for a hand and a person asking for
# nothing: "what can i do" is the commonest way to say it, and it was the one wording the list
# did not hold, so it went to the search shrug while "what should i do" got the offer. "can",
# "could" and "might" are the same ask, and the verb and the tail guard still keep every line
# that names something ("what can i do about my leaking roof", "what can i get for tea") out.
BARE_PICK = re.compile(
    r"^\s*(?:(?:so|and|but|ok|okay|well|then|just|hey|hi|right|anyway|anyways|oh|hmm|yeah|"
    r"yes|alright|honestly|you\s+know)[\s,]+)*"
    r"(?:what|which)\s+(?:should|shall|do|would|can|could|might)\s+i\s+"
    r"(?P<verb>wear|put\s+on|buy|get|do|take|bring|look\s+(?:for|at)|expect|ask|sign|"
    r"order|prepare)\b"
    r"(?:\s+(?:now|today|tonight|tomorrow|instead|else|next|then))?\s*\??\s*$", re.I)
# A lost ask in a conversation that has already said what it is about ("my week has been
# rubbish" / "work is the worst bit" / "i dont know what to do about it") must not ask for the
# story again: the offer the bare pool makes ("tell me what has gone on") is a bot asking a
# person to start over, which reads worse than the placeholder it replaced. What a friend says is
# "it" - the thing already on the table - and the one question that cuts it down.
LOST_IN_A_THREAD = (
    "Then the useful question is which part of it is actually yours to move. Which part could you "
    "change this week?",
    "It usually breaks into smaller pieces once they have names. What is the smallest of them "
    "that would make tomorrow easier?",
    "You have said the whole of it already, so I will not ask again. Which bit of it would you "
    "want to have sorted by Friday?",
)


# "what should i do first" is the same ask in the question form, and it lands at a different
# door: with nothing before it the words reach the search hedge (nothing in them names a fact),
# and in a thread they are a step through advice already given. So it is read with the lost ask,
# where a thread that has advice is left alone, and not with the bare picks, which would ask a
# person who has just said what is wrong to say it all again.
BARE_PICK_LOST_FIRST = re.compile(
    r"^\s*(?:(?:so|and|but|ok|okay|well|then|just|hey|hi|right|anyway|oh|hmm|yeah|yes|alright|"
    r"honestly|tbh)[\s,]+)*"
    r"(?:what|which)\s+(?:should|shall|do|would|can|could|might)\s+i\s+do\s+"
    r"(?:first|next)\s*\??\s*$", re.I)


def _a_lost_ask(clean):
    """True for the bare "i dont know what to do" family: nothing named, a hand asked for."""
    clean = clean or ""
    return bool(BARE_PICK_LOST.match(clean) or BARE_PICK_LOST_FIRST.match(clean))


# The same ask with the first step as its object: "i dont know where to start", "no idea where
# to begin", "where do i even start". It is the widest way to ask for a hand after the bare "what
# should i do", and it names nothing at all - not the list, not the thing, not the day. Main has
# one answer for it, the size-of-the-list question ("what is the one thing that cannot slip?"),
# which needs a list the line never gave, and since the stuck reader learned to stand aside for a
# line with no list above it, the bare ask has had nothing but the placeholder ("I'm listening -
# say more if it helps"). What a friend hands over is the way to pick the first thing, which is
# the whole of what "where to start" is asking.
_START_ASK_BODY = (
    r"(?:"
    # "i dont know where to start" and the other ways of saying the not knowing.
    r"(?:i\s+)?(?:really\s+|honestly\s+|genuinely\s+|actually\s+|still\s+|simply\s+|"
    r"just\s+|even\s+)*"
    r"(?:"
    r"(?:do\s+not|don'?t|dont)\s+(?:even\s+)?know"
    r"|dunno"
    r"|(?:have|ve|got|i'?ve)\s+(?:absolutely\s+)?no\s+(?:idea|clue)"
    r"|(?:have\s+)?no\s+(?:idea|clue)"
    r"|(?:i\s+am\s+|i'?m\s+)?not\s+(?:really\s+|too\s+)?sure"
    r")\s+where\s+to\s+(?:start|begin)"
    # ...the question form, which is the same ask with a question mark on it...
    r"|(?:where|how)\s+(?:do|should|shall|can|could|would)\s+(?:i|we)\s+(?:even\s+)?"
    r"(?:start|begin)"
    # ...and the two words on their own.
    r"|where\s+to\s+(?:start|begin)"
    r")"
    # The words people put after it that add nothing the pool has to read. A subject after it
    # ("where to start with the loft", "where do i start on the cv") is not this line: that one
    # names a thing, and the thing has an answer of its own.
    r"(?:\s+(?:now|next|first|today|tonight|tomorrow|at\s+all|anymore|any\s+more|"
    r"with\s+(?:it|this|that|them)|on\s+(?:it|this|that)))?")
_START_ASK_LEAD_IN = (
    r"(?:(?:so|and|but|ok|okay|well|then|just|hey|hi|right|anyway|anyways|oh|hmm|yeah|"
    r"yes|alright|honestly|god|christ|ugh|tbh|seriously|you\s+know)[\s,]+)*"
    r"(?:(?:the\s+thing\s+is|the\s+problem\s+is|thing\s+is|truth\s+is|see|look|i\s+mean)"
    r"[\s,]+)*")
BARE_PICK_START = re.compile(
    r"^\s*" + _START_ASK_LEAD_IN + _START_ASK_BODY + r"\s*\.?\s*$", re.I)
# The same ask with a clause in front of it: "we've moved to a new place and i dont know where to
# start" is one sentence with two halves, and the half that asks for the hand is the second one.
# Only where the two are joined ("and", "but", a comma): a line that names the thing it wants to
# start on and then asks keeps its own answer, because the subject is the thing before it.
BARE_PICK_START_CLAUSE = re.compile(
    r"\b(?:and|but)\s+" + _START_ASK_LEAD_IN + _START_ASK_BODY + r"\s*\.?\s*$", re.I)


def _a_start_ask(clean):
    """True for the bare "i dont know where to start" family: nothing named, the first step asked for."""
    clean = clean or ""
    return bool(BARE_PICK_START.match(clean) or BARE_PICK_START_CLAUSE.search(clean))


def _said_what_it_is_about(memory):
    """True when a line before this one gave a reply something to name.

    "hi" then "i dont know what to do" is a first ask with nothing behind it, and the thread pool
    would answer it with "which part of it", pointing at nothing. Three words of content in the
    last two lines is the line the pools draw.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-2:]:
        said = " ".join(str(turn.get("user") or "").lower().split())
        if len([w for w in said.split() if len(w) > 2]) >= 3:
            return True
    return False


# The first step, for the ask whose object is the first step. A line that says "where to start"
# has not given a list and has not given a thing, so no pool can name either: what it gets is the
# way to pick one thing, which is the pool the memory store's "i dont know what to do" after
# nothing at all already answers with (bot/memory/stuck.HARD). One pool, two doors, so the same
# line does not get two voices: the chat module answers the bare ask before this file sees it, and
# this is what a start-ask with a clause in front of it reaches.
START_ASK = stuck_line.HARD


def the_pool_for_a_lost_ask(memory, clean=""):
    """Which offer "i dont know what to do" gets: the news one, the thread one, or the bare one."""
    if _news_above(memory):
        return BARE_PICK_AFTER_NEWS
    if _a_start_ask(clean):
        return START_ASK
    if _said_what_it_is_about(memory):
        return LOST_IN_A_THREAD
    return BARE_PICK_DO


def the_lost_ask_reply(memory, clean, repaired=None):
    """The offer for "i dont know what to do", or None when this line is not that ask.

    One reply for one shape, from every door it can reach: as a statement it lands on the mood
    fallback, as a question on the hedge for an ask nothing can answer, and `_unknown` is that
    hedge's own door. A thread that already has advice in hand is left alone - "the boiler
    packed in" then "i dont know what to do" is the next step of that advice, and asking what
    has gone on reads as a bot that was not listening.
    """
    if the_advice(memory):
        return None
    if not (_a_lost_ask(clean) or _a_lost_ask(repaired or "")
            or _a_start_ask(clean) or _a_start_ask(repaired or "")):
        return None
    pick = the_pool_for_a_lost_ask(memory, clean if _a_start_ask(clean) else "")
    if not pick:
        return None
    return _choose(pick, memory, clean)
# The wear pool asks and does not dress anybody: a bare "what should i wear" has not said the
# day, and a line that assumes one ("standing about, sitting on grass, a long service") answers
# a wedding nobody mentioned and walks straight past `its cold out`, which is the one thing the
# person did say. What is left is the question a friend asks first. The pool itself lives in
# `fallback_data` with the hot, cold and wet ones, and is imported above: a second definition
# here shadows that import, and `BARE_PICK_KIND` hands back the imported tuple, so the
# `pool is BARE_PICK_WEAR` tests below were comparing two different objects and the weather
# pools could never fire.
# The weather the person already told the listener decides more of it than the mirror does, and
# `its cold out / what should i wear` ignoring the cold is the reply of somebody who was not
# listening. Only a weather line counts, not a body: "i have a cold" and "i feel hot" are the
# other modules' lines, so the hot and cold ones want the it-is shape.
WEATHER_COLD = re.compile(
    r"\b(?:freezing|chilly|freezing cold|bitterly cold|snowing|snow|frost|icy)\b|"
    r"\b(?:it'?s|its|it is|very|so|really|too|dead|bloody)\s+(?:a bit\s+|quite\s+)?cold\b",
    re.I)
WEATHER_HOT = re.compile(
    r"\b(?:boiling|scorching|roasting|heatwave|muggy|humid)\b|"
    r"\b(?:it'?s|its|it is|very|so|really|too|dead|bloody)\s+(?:a bit\s+|quite\s+)?"
    r"(?:hot|warm)\b", re.I)
WEATHER_WET = re.compile(r"\b(?:raining|pouring|drizzle|drizzling|wet out|showers|storm)\b",
                         re.I)


# A heavy line before a bare ask: the person has already said the thing the ask is about.
# "what should i do" is the widest ask in English when it comes out of nothing, and after a
# death or a scare it is a request for help with what was just said - "tell me what has gone
# on" then asks a bereaved person to say the death again, and "the order of the next two
# things" is a to-do list in front of a scare. The words here are only the ones the readings
# above do not already hold (`loss.reads_as_loss` has the deaths, `reads_as_bad_news` has the
# diagnoses): a lump, a body in a hospital bed, someone very ill.
HEAVY_ABOVE = re.compile(
    r"\b(?:lump|lumps|tumou?r|cancer|leuka?emia|lymphoma|melanoma|dementia|alzheimers|"
    r"motor neurone|parkinsons|ms|chemo|chemotherapy|radiotherapy|palliative|hospice|"
    r"terminal(?:ly)?|very ill|really ill|seriously ill|dangerously ill|intensive care|"
    r"life support|stillborn|stillbirth|meningitis|sepsis)\b", re.I)
# Bad news about work or money is bad news, and it is not the news a bare ask is asking about:
# "i lost my job" then "what should i do" is somebody asking for a hand with something they have
# only half said, which is exactly what the ask pool is for. The losses of a person, a body and a
# diagnosis stand the ask down; a job does not.
WORK_NEWS = re.compile(
    r"\b(?:job|jobs|work|hours|shift|shifts|money|pay|wages|salary|contract|business|"
    r"redundant|redundancy|clients?|customers?|interview|mortgage|rent|loan|debt|"
    r"benefits?|savings?)\b", re.I)


def _news_above(memory, heavy=False):
    """True when the line before this one said something heavy.

    A bare ask is a person asking for a hand with something they have not named. If the turn
    before named a death, a lump or somebody in intensive care, it is not that, and the pool
    that asks what has gone on reads as a friend who was not listening. A job or a bill is bad
    news of the other kind: there the ask is still half a question, so it keeps the ask pool.

    `heavy` asks the medical news alone (`badnews.reads_as_heavy_news`). A refused payment, a
    court letter, a house being sold: the person can still say a plain "what should i do" after
    those, and the ask pool is the right answer - "tell me what has gone on, even roughly" is
    what a friend says to somebody whose benefit was refused. Asking a bereaved person to tell
    the death again is the fault this pool stands down for, and that is the medical list.
    """
    if not isinstance(memory, dict):
        return False
    if _in_a_care_thread(memory):
        return True
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    for turn in turns[-2:]:
        low = " ".join(str(turn.get("user") or "").lower().split())
        if not low:
            continue
        if HEAVY_ABOVE.search(low):
            return True
        if reads_as_heavy_news(low) if heavy else (
                reads_as_bad_news(low) and not WORK_NEWS.search(low)):
            return True
        try:
            if loss.reads_as_loss(low):
                return True
        except Exception:  # noqa: BLE001 - a reading that fails is a reading not made
            pass
    return False


def _weather_above(memory):
    """The weather the person named in the last two lines, as "cold", "hot", "wet" or None."""
    if not isinstance(memory, dict):
        return None
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    for turn in reversed(turns[-2:]):
        said = str(turn.get("user") or "")
        if not said:
            continue
        if WEATHER_WET.search(said):
            return "wet"
        if WEATHER_COLD.search(said):
            return "cold"
        if WEATHER_HOT.search(said):
            return "hot"
    return None


# An occasion the thread already named is the composer's own entry ("what should i wear to a
# wedding" has a real answer), so a bare ask only stays bare when the thread did not say one.
OCCASION_ABOVE = re.compile(
    r"\b(?:wedding|funeral|christening|baptism|interview|party|dinner|date|work|office|"
    r"conference|concert|festival|exam|graduation|church|meal out|night out)\b", re.I)


def _an_occasion_above(memory):
    if not isinstance(memory, dict):
        return False
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    return any(OCCASION_ABOVE.search(str(turn.get("user") or "")) for turn in turns[-2:])


# The pool asks what the day is. A line that has already said - in the clause in front of its ask -
# which day it is, or has named an occasion, has answered that question, and asking it back reads as
# a bot that was not listening: "i start at the new place on monday, what should i wear" was offered
# "tell me what the day is - work, a meal out, a long walk". Nothing is added to what the pool can
# answer here: the line stands down, and whatever it had without the pool it still has.
THE_DAY_IS_NAMED = re.compile(
    r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b|"
    r"\b(?:next|this|that|the) (?:week|weekend)\b|"
    r"\b(?:tomorrow|tonight|today)\b|"
    r"\b(?:in|on|by|for|until) (?:january|february|march|april|may|june|july|august|september|"
    r"october|november|december)\b", re.I)


# The same occasions as `OCCASION_ABOVE`, plus the ways a thread names one without the word:
# "my sister is getting married in june" and "im going to be a bridesmaid" are a wedding, and the
# four-turn window needs them to see it. Read only by the branch below, so a word that is not here
# costs nothing but the day the pool would have asked about.
AN_OCCASION_AHEAD = re.compile(
    r"\b(?:wedding|funeral|christening|baptism|interview|party|dinner|date|work|office|"
    r"conference|concert|festival|exam|graduation|church|meal out|night out|"
    r"getting married|get married|got married|marrying|engaged|engagement|"
    r"bridesmaid|bridesmaids|best man|maid of honour)\b", re.I)


def _an_occasion_in_the_thread(memory, back=4):
    """An occasion named a few turns back, which the pool's own question would ask about again.

    `_an_occasion_above` is the two-turn window the wear pool has always used. A thread that
    opened the occasion and then talked about something else has still had it: "my sister is
    getting married in june" / "im going to be a bridesmaid" / "what should i get her" / "back to
    the wedding, what should i wear" was asked where the day is, which the conversation said
    four turns earlier.
    """
    if not isinstance(memory, dict):
        return False
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    return any(AN_OCCASION_AHEAD.search(str(turn.get("user") or "")) for turn in turns[-back:])


# A trip in the thread is the one case where the packing line is the right answer to a bare ask:
# a place, a holiday, a flight or a night away, and "im going to cornwall in july", which names
# no trip word at all. A going-to followed by a verb ("going to have a bath", "going to try
# again", "going to see my mum") or by a place down the road is not a journey.
TRIP_ABOVE = re.compile(
    r"\b(?:holiday|holidays|hols|trip|trips|away|abroad|flight|flights|flying|hotel|"
    r"camping|campsite|backpacking|weekend away|days? away|mini ?break)\b|"
    r"\b(?:go|going|went|off|flying|driving|heading)\s+(?:to\s+|off\s+to\s+)?"
    r"(?!the\b|a\b|an\b|my\b|his\b|her\b|their\b|our\b|your\b|work\b|bed\b|sleep\b|"
    r"school\b|uni\b|university\b|college\b|town\b|hospital\b|doctor\b|dentist\b|"
    r"shop\b|shops\b|toilet\b|loo\b|bath\b|shower\b|"
    r"have\b|get\b|see\b|be\b|do\b|make\b|take\b|try\b|need\b|want\b|start\b|stop\b|"
    r"give\b|put\b|keep\b|stay\b|look\b|ask\b|tell\b|say\b|ring\b|call\b|text\b|"
    r"eat\b|drink\b|cook\b|clean\b|wash\b|sort\b|finish\b|leave\b|come\b|meet\b)"
    r"[a-z]{3,}", re.I)


def _a_trip_above(memory):
    """True when the last two lines the person sent said they were going somewhere."""
    if not isinstance(memory, dict):
        return False
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    return any(TRIP_ABOVE.search(str(turn.get("user") or "")) for turn in turns[-2:])


# These verbs are missing their object, so the pool asks for it - but only when there is nothing
# on the table. "my toddler has a fever and a rash" / "what should i look for" wants the signs to
# watch for, and "looking at what - a car, a flat, a phone?" is worse there than the shrug this
# pool was built to replace. With a subject above, the turn stays with the follow-up readers.
BARE_PICK_NEEDS_THE_THING = frozenset({"look for", "look at", "expect", "ask", "sign",
                                       "order", "prepare"})
# The last line the person sent named nothing to answer: a greeting or an acknowledgement. The
# words here are the whole of a line that is not a subject, so "my son is 8" is a subject (son)
# and "ok then" is not.
THREAD_NOTHING = frozenset("""
    hi hey hello morning evening there so and but ok okay well right yeah yes yep no not im i the
    a an it that this to for of in on at is was just also thanks thank please good great fine
    alright anyway oh hmm mm me my u you your cheers ta now then today tonight
""".split())


def _a_subject_above(memory):
    """True when the last line the person sent named a thing, so a bare ask is a follow-up."""
    if not isinstance(memory, dict):
        return False
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    for turn in turns[-2:]:
        said = str(turn.get("user") or "")
        if not said.strip():
            continue
        words = re.findall(r"[a-z']+", said.lower())
        if any(word.strip("'") not in THREAD_NOTHING and len(word) > 2 for word in words):
            return True
    return False

# The ask is the last thing on the line, and everything in front of it is the setting. The
# pattern above is anchored to the whole line so that a line naming its own subject keeps its own
# answer, and a subject sits in front of an ask as easily as behind it: "what should i wear to a
# wedding" has an entry of its own and never reaches here, while a clause saying what the person
# has been doing - "for the first time in years, what should i wear", "in years, what should i
# wear" - was shrugged at, though the ask in it is as bare as the seven words that get the pool.
# A friend reads the clause and then answers the ask, so the pool is tried on the whole line and,
# when the line put something in front of the ask, on the ask it ends with. Nothing new is read:
# the reading hands the ask over as `focus`, and the clause split is only worked out again when
# the caller has no reading to hand (a test, or a repaired line).
_AFTER_A_CLAUSE = re.compile(
    r"(?:[,;:]\s+|\s+(?:and|but|so|because|though|although|while|when|now)\s+)"
    r"((?:what|which|how|where|who|when)\b[^,;:?!]*)\s*\??\s*$", re.I)


def _the_ask_clause(clean, memory=None):
    """The ask a line ends with when something sits in front of it, or "" when nothing does."""
    said = " ".join(str(clean or "").lower().split())
    if not said:
        return ""
    ask = ""
    reading = memory.get("understood") if isinstance(memory, dict) else None
    if isinstance(reading, dict):
        focus = " ".join(reading.get("focus") or []).split()
        if len(focus) >= 3 and said.endswith(" ".join(focus)) and " ".join(focus) != said:
            ask = " ".join(focus)
    if not ask:
        found = _AFTER_A_CLAUSE.search(said)
        ask = " ".join(found.group(1).split()) if found else ""
    return ask if len(ask.split()) >= 3 else ""


def _bare_pick(clean, memory=None):
    """The pool for a line that asks the bot to choose and names nothing to choose between."""
    found = BARE_PICK.match(clean)
    from_the_clause = False
    if not found:
        ask = _the_ask_clause(clean, memory)
        found = BARE_PICK.match(ask) if ask else None
        from_the_clause = found is not None
    if not found:
        return None
    if found.group(0).strip().lower().startswith("which"):
        # a choice with nothing to choose between: the things are the answer, not who it is for
        return BARE_PICK_WHICH
    verb = " ".join(found.group("verb").lower().split())
    pool = BARE_PICK_KIND.get(verb, BARE_PICK_DO)
    if from_the_clause and (OCCASION_ABOVE.search(str(clean or ""))
                            or THE_DAY_IS_NAMED.search(str(clean or ""))
                            or _an_occasion_in_the_thread(memory)):
        # The pool asks where the person is going, and the line or the thread has already said:
        # "back to the wedding, what should i wear" was asked where the day is, when the wedding
        # was the day. Asking again reads as a bot that was not listening, so a line that came to
        # the pool through its own clause stands down where the ask it carries already answers
        # the question the pool would ask.
        return None
    if from_the_clause and pool is BARE_PICK_DO:
        # "what should i do" with no object is answered by asking what has gone on, and the clause
        # in front has just said it: "i havent written a cv in ten years, what should i do" is a
        # person asking about the cv, and "tell me what has gone on" asks them to say it again.
        # The widest ask keeps its whole-line answer for a line that names nothing.
        return None
    if verb in BARE_PICK_NEEDS_THE_THING and _a_subject_above(memory):
        # the thing was named a turn ago, so this is the follow-up's turn, not the ask's
        return None
    if pool is BARE_PICK_WEAR and not _an_occasion_above(memory):
        weather = _weather_above(memory)
        if weather == "wet":
            return BARE_PICK_WEAR_WET
        if weather == "cold":
            return BARE_PICK_WEAR_COLD
        if weather == "hot":
            return BARE_PICK_WEAR_HOT
    if pool is BARE_PICK_BRING and _a_trip_above(memory):
        # the thread said where they are going, so the packing line is an answer and not a guess
        return BARE_PICK_TAKE
    if pool is BARE_PICK_DO and _news_above(memory, heavy=True):
        # "my mum died" / "what should i do" is the news, asked again: this pool has nothing true
        # to say about a death it was not told, and asking what has gone on reads as a friend who
        # was not listening. Standing down to nothing is not a fix either - the turn then went to
        # the search shrug, which is the worst line in the bot for somebody with a death or a
        # scare on their plate, so the stand-down names where it stands down to.
        return BARE_PICK_AFTER_NEWS
    return pool


# "who do i call about it", "who do i ring first", "who should i get to look at it": the person
# wants a name to take a thing to, and the thing itself was named a turn ago, so the line holds
# nothing to read. Every one of them reached the search hedge, which tells somebody to go and look
# up their own problem - the one thing a search cannot do. The thread still has two things to
# read: the line that named the trouble, and the answer the bot has just given, which usually
# names the actor ("report it to the council the same day"). Where neither names anybody the
# honest reply is the route list and one question, not a shrug.
# These patterns live in their own file: this one grew past the 1 MB a clone may carry and
# every change to it was refused. Imported here in place of their definitions.
from .fallback_words import (  # noqa: F401 - read here by the patterns below
    A_PERSON_IN_A_CRISIS,
    CRISIS_ASK,
    HUMAN_ASK,
    HUMAN_HELPS,
    HUMAN_LEAD,
    HUMAN_QUOTED,
    HUMAN_TAIL,
    NAMES_THE_BOT,
    PRIVACY_NOT_THIS,
    REFERS_BACK,
    REPAIR_DECISION,
    LEAVING_IN_THE_LINE,
    REPAIR_BARE_IT,
    REPAIR_PERSON,
    REPAIR_TARIFF,
    REPAIR_TRADE,
    REPAIR_WHAT_IT_IS_WORTH,
    REPAIR_WHETHER,
    SELF_ASK,
    A_VIEW_ASKED_FOR,
    TRUST_ASK,
    WHO_FOR_IT,
    WHO_FOR_IT_BODY,
    WHO_FOR_IT_ROUTES,
    WHO_FOR_IT_SAID,
    WHO_FOR_IT_SAID_VOICE,
    WHO_NAMED_BEFORE,
    WHO_TO_TALK_ASK,
    WHO_TO_TALK_TO,
    WHO_TO_TALK_TO_A_BAD_STRETCH,
)




def _opens_the_line(prefix):
    """True when what comes before the human/person ask is only a greeting or a question opener."""
    return bool(HUMAN_LEAD.match(prefix)) or bool(HUMAN_QUOTED.search(prefix))


# The same question asked as a request for a person to deal with: "can i speak to a real person",
# "is there a real person i can talk to", "can i talk to a human please", "get me a human",
# "i need to talk to a human", "any chance of an actual human here". `HUMAN_ASK` read only the
# three shapes where the person asks what it is talking to, and the request shapes all reached a
# shrug or a change of subject - on main "can i speak to a real person" got "I'm not sure about
# that one, sorry - I'd rather not guess. A quick search online will get you a solid answer".
#
# The words are also how a person names somebody else, so the gates are the strict ones, not
# `_asks_elsewhere`: the ask opens the line, and what follows is nothing, a "please"/"here", the
# asker ("... i can talk to") or this end of the chat ("on the other end"). A tail that names
# what they want the person for ("... about my grief", "... about my refund") is a line the
# entries and the grief module answer, and those keep it - `HUMAN_HELPS` reads "i can talk to
# about ..." as the bot being asked for a hand, which is right for "is this a real person who can
# help with my ticket" and wrong here.
HUMAN_TALK_ASK = re.compile(
    r"\b(?:can|could|may|might) i (?:please )?(?:speak|talk|chat) (?:to|with) "
    r"(?:a |an |a real |an actual |some )*(?:human being|actual human being|real human being|"
    r"human|person|real person|actual person|actual human|real human)\b|"
    r"\b(?:i )?(?:want|need|would like|wanna|have) to (?:speak|talk|chat) (?:to|with) "
    r"(?:a |an |a real |an actual )*(?:human being|actual human being|real human being|human|"
    r"person|real person|actual person|actual human|real human)\b|"
    r"\bis there (?:a |an |any )?(?:real |actual )?(?:human being|actual human being|human|"
    r"person|someone real|somebody real)\b|"
    r"\b(?:get|give) me (?:a |an )?(?:real |actual )?(?:human|human being|person)\b|"
    r"\b(?:any|got any|got a) (?:chance of )?(?:a |an )?(?:real |actual )?(?:human|human being|"
    r"person)\b|"
    r"\b(?:real|actual) (?:human|person|human being) (?:here|on here|around|available)\b")
# A tail that names the asker rather than another person: "is there a real person i can talk to",
# "someone real i could speak with", "a human being i can ask".
HUMAN_TO_ME = re.compile(
    r"^\s*(?:that |who |which )?(?:i|we) (?:can|could|may|might|would|should|will)?\s*"
    r"(?:talk|speak|chat|ask|write)\s*(?:to|with)?\s*(?:you|u)?\s*"
    r"(?:please|pls|now|first|then)?\s*[.!?]*\s*$")
# "is there a real person on the other end": the tail names this end of the chat, which is the
# question `HUMAN_ASK` already reads as its own ("real person on the other end").
HUMAN_OTHER_END = re.compile(r"^\s*(?:on|at) the other (?:end|side)\b[^a-z]*$")


def _asks_elsewhere(tail):
    """True when what comes after the human/person words asks about somebody other than us."""
    if HUMAN_HELPS.match(tail or ""):
        return False
    if HUMAN_TAIL.match(tail or ""):
        return False
    if HUMAN_OTHER_END.match(tail or ""):
        return False
    return any(word not in HUMAN_EMPTY for word in re.findall(r"[a-z]+", (tail or "").lower()))


def _asks_for_a_person_to_talk_to(clean):
    """True when the line asks for a person to deal with, and says nothing else it wants.

    The ask has to open the line (`_opens_the_line`) and what follows has to be the tail shapes
    above - nothing, "please", "here", the asker or this end of the chat. Anything a person wants
    the person *for* names a subject, and a subject is the entries' line, so this reading leaves
    it alone: "is there a real person i can talk to about my grief" is answered by the grief
    module on main and by this reading if the tail were let through.
    """
    matched = HUMAN_TALK_ASK.search(clean)
    if not matched or not _opens_the_line(clean[:matched.start()]):
        return False
    tail = clean[matched.end():]
    return bool(HUMAN_TAIL.match(tail) or HUMAN_TO_ME.match(tail)
                or HUMAN_OTHER_END.match(tail))
# An ask for a hand, with nothing said about what for: "can you help me", "i need a hand",
# "give me a hand". The whole line is the ask, so there is no subject to read and nothing to
# search for - and the shrug ("I don't know enough to answer that honestly") reads as a refusal
# to a line that only asks whether the bot will help at all. The offer asks for the detail,
# which is what a friend says.
HAND_ASK = re.compile(
    r"^(?:so |ok |okay |right |hi |hiya |hello |hey |and |please )*"
    r"(?:(?:can|could|will|would) (?:you|u) (?:please )?"
    r"(?:help(?: (?:me|us))?(?: out)?|give (?:me|us) a hand|lend (?:me|us) a hand"
    r"|do (?:me|us) a favour|advise (?:me|us)|be a hand)"
    r"|(?:i )?(?:could do with|need|want|would like) (?:(?:your|some|a bit of) )?"
    r"(?:help|a hand|advice|a bit of advice)"
    r"|(?:can|could) (?:i|we) (?:get|have|ask for) (?:(?:your|some|a little|a bit of) )?"
    r"(?:help|a hand|advice)"
    r"|help(?: me)?(?: out)?"
    r"|give me a hand"
    r")"
    r"(?: (?:with|about) (?:something|anything|a thing|stuff|it))?"
    # A time word after the ask says when the hand is needed, not what for: "i need help now",
    # "can you help me today". Left out, the ask did not match and the line went to whatever read
    # the time word - "i need help now" was answered "Bye for now!" by the leaving reader, a
    # farewell to somebody asking for a hand.
    r"(?: (?:here|please|now|today|tonight|asap|urgently|quick(?:ly)?|straight away))?"
    r"(?: (?:right )?now)?(?: please)?$")


def _asks_for_help(clean, understood=None):
    """A bare ask for a hand as the whole line, commas and all ("hi, can you help me").

    Typed the way people type it, the ask is not in plain words: "can u help me pls" is the
    commonest spelling of it on the deck and it went to the search shrug, because the pattern
    is written for ordinary words and only the reading puts them there ("u" -> "you", "pls" ->
    "please", "help me pls" -> "help me please"). So the line as typed is tried first and the
    reading's own plain text second.
    """
    lines = [clean]
    if isinstance(understood, dict):
        said = understood.get("plain")
        if isinstance(said, str) and said and said != clean:
            lines.append(said)
    for line in lines:
        bare = " ".join(re.sub(r"[^a-z0-9 ]+", " ", str(line or "").lower()).split())
        if HAND_ASK.match(bare):
            return True
    return False
# "who made you do that" asks who is behind the bot's own words. The tail after "made you" is the
# bot's own doing, so unlike every other self question there is no subject to read there: "who
# made you say that" and "what made you say that" are the same question about the same thing.
# "what made you say that" asks who is behind the words, which is the agency answer. The same shape
# with any other verb is a question about the thing the bot has no body for - "what makes you
# sneeze" was read as agency and answered "Me, in the only sense there is: I pick the words", which
# is a reply to a question nobody asked - so the verb after "you" has to be a saying or a deciding.
MADE_ASK = re.compile(r"\bwho (?:made|makes|told|tells|taught|programmed|built|wrote)\s+(?:you|u)\b"
                      r"|\bwhat (?:made|makes) (?:you|u)\s+(?:say|think|believe|decide|choose|"
                      r"pick|answer|reply|write|act|do\s+that)\b")
SELF_OPENER = re.compile(r"\b(?:where|why|how\s+long)\b")
# "what are you for" asks the same as "why are you here": a point, not a place.
# "what model are you", "which model are you running on", "what version are you", "are you an
# LLM". The subject is the machine the bot is made of, so it is a question about the bot and not a
# fact to search: "what model of car do you recommend" keeps its own answer, because the word
# after the model is "of" and not an ask about the bot.
MODEL_ASK = re.compile(
    r"\b(?:what|which)\s+(?:\w+\s+){0,2}?(?:model|version|engine|llm|ai)\s+(?:are|is|do|"
    r"did)\s+(?:you|u)\b"
    r"|\bwhat\s+(?:are|is|were)\s+(?:you|u)\s+(?:running|based|built|trained)\s+on\b"
    r"|\bare\s+(?:you|u)\s+(?:a\s+|an\s+)?(?:llm|large\s+language\s+model|"
    r"neural\s+net\w*|transformer|deep\s+learning\s+model)\b")
# How the bot works is the same honest answer as what it is made of, and it was going to the search
# hedge or to the list of things the bot can help with: "how do you work" got "Cooking, travel,
# money, work, gadgets, kids, feelings - everyday questions and plans", "do you use ai" and "whats
# inside you" got "A quick search online will get you a solid answer", and "how are you built" got
# "All good here. What's keeping you busy?". The reply the bot already has for its own make - no
# model, hand-written rules, nothing learned - answers every one of them, so they read as `model`.
# Each pattern is anchored to the end of the line or to the bot as its subject, so a line about a
# thing keeps its entry: "how do you work out a percentage", "how do you make bread" and "how do
# you work this telly" are not read here.
# "are you a bot", "are you an ai", "are you a chatbot" are not read here: that person wants yes
# or no first, and the identity answer already opens with it ("I'm a chatbot, not a person"). The
# workings answer opens on what the bot is made of, which answers a question they did not ask.
WORKINGS_ASK = re.compile(
    r"\bhow\s+(?:do|does)\s+(?:you|u)\s+(?:actually\s+|really\s+)?work"
    r"\s*(?:then|though|really|anyway|now)?\s*$"
    r"|\bhow\s+(?:are|were)\s+(?:you|u)\s+(?:built|made|programmed|put together|written)\b"
    r"|\bwhat(?:s| is)\s+(?:inside|under)\s+(?:you|your hood|the hood)\b"
    r"|\bdo\s+(?:you|u)\s+use\s+(?:ai|an ai|chatgpt|gpt|a model|an llm|llm|a neural network)\b"
    r"|\bhow\s+do\s+(?:you|u)\s+answer\s+(?:questions|these|things|that)\s*$")
# "why do you keep asking me questions", "why are you asking me that", "why so many questions": a
# remark on how the bot asks is a question about the bot, and nothing about it is on the web, so
# the search hedge ("a quick search online will get you a solid answer") is the one reply that
# cannot help. The answer needs no facts: why it asks, and that a person can tell it to stop.
ASKING_ASK = re.compile(
    # "why do you keep asking", "why are you always asking me that": the complaint in its usual
    # shape, named by "you" and the asking.
    r"\bwhy\s+(?:do|did|does|are|were|would)\s+(?:you|u)\s+"
    r"(?:keep|always|even|still)\s+(?:be\s+)?(?:ask|asking)\b"
    # "why do you ask so many questions", "why did you ask me that": the asking named with how
    # much of it there was. A line that asks about what the asking was *for* ("why do you ask for
    # my email") is a different question and keeps its own reading.
    r"|\bwhy\s+(?:do|did|does|are|were|would)\s+(?:you|u)\s+(?:ask|asking|asked)\s+"
    r"(?:me\s+)?(?:so\s+many|this\s+many|that\s+many|all\s+these|all\s+the|these|that|this)\b"
    # the bare "why do you ask", which is the whole line
    r"|\bwhy\s+(?:do|did|does)\s+(?:you|u)\s+ask\s*$"
    r"|\bwhy\s+(?:are|were)\s+(?:you|u)\s+asking(?:\s+me)?\s*(?:that|this|so\s+many)?\s*$"
    # "do you always ask this many questions": the same complaint without the "why"
    r"|\b(?:do|did)\s+(?:you|u)\s+(?:always\s+|really\s+|have\s+to\s+)?ask\s+"
    r"(?:so|this|that|these)\s+many\s+questions\b"
    r"|\bwhy\s+(?:so\s+many|all\s+these|all\s+the)\s+questions?\b"
    r"|\b(?:stop|quit|enough\s+with)\s+(?:the\s+)?(?:asking|questions)\b")


# Being trusted, and being judged. "can i trust you", "are you lying", "do you make things up"
# and "will you judge me" were answered by the search hedge - an offer to look up a fact about the
# world, made to a person asking what this thing in front of them will do with them. The honesty
# answer already exists one table away ("are you always right"); the judgement one is the privacy
# answer said warmly, because nothing is written down and nobody is grading them.
#
# Every shape names the bot as the subject, because the same words about somebody of the world are
# ordinary advice questions: "can i trust a roofer", "should i trust tripadvisor", "i dont trust
# my doctor" and "is this garage trustworthy" keep their own answers.
TRUST_ASK = re.compile(
    r"\b(?:can|could|should|shall|may)\s+(?:i|we)\s+(?:really\s+|honestly\s+|actually\s+)?"
    r"(?:trust|believe|rely\s+on)\s+(?:you|u)\b"
    r"|\bcan\s+(?:i|we)\s+(?:trust|believe)\s+what\s+(?:you|u)\s+(?:say|tell\s+me)\b"
    r"|\bare\s+(?:you|u)\s+(?:trustworthy|reliable|honest|truthful)\b"
    r"|\bwill\s+(?:you|u)\s+(?:tell|give)\s+me\s+the\s+truth\b"
    r"|\bare\s+(?:you|u)\s+telling\s+(?:me\s+)?the\s+truth\b"
    r"|\bare\s+(?:you|u)\s+lying\b"
    r"|\bdo\s+(?:you|u)\s+(?:ever\s+)?(?:lie|guess|make\s+(?:things|stuff|that|it|this|them)\s+up|"
    r"make\s+up\s+(?:things|stuff|answers|facts))\b"
    r"|\bare\s+(?:you|u)\s+(?:making|inventing)\s+(?:that|this|it|things|stuff)\s+up\b", re.I)
# Where the person stands with this chat, asked in the words people use for it. "is this between
# us" is not a promise asked for - that is "keep this between us", which the secret reading
# answers with a yes - it is the person checking, and the bot's own privacy answer is the only
# thing that can tell them. All five of these went to the search hedge, which offered to look up a
# fact about the world: "is this between us", "is this just between us", "are we private here",
# "is what i say between us" and "what happens to what i tell you".
#
# The subject is what keeps it narrow. The line has to ask about the chat ("this", "it", "we") or
# about the words ("what i say"), so "is the gap between us too big" and "what happens to my
# details if i switch supplier" are somebody's own business and keep their answers. The words arm
# names the person as the one saying them, which is why "what happens to my messages" is left to
# the privacy shapes that already read it.
BETWEEN_US_ASK = re.compile(
    # "is this between us", "is this chat just between us", "is this between us or what". The line
    # asks about the chat itself, so nothing of the world may sit between the "this" and the
    # "between us": "is this seat between us" is not this question.
    r"\b(?:is|are|was|were|will|would|does|do|can)\s+(?:this|that|it)\s+"
    r"(?:(?:chat|conversation|thread|session)\s+)?(?:just\s+|really\s+)?"
    r"between\s+(?:us|you\s+and\s+me)\b"
    # The words rather than the chat: "is what i say between us", "is everything i say between us".
    r"|\b(?:is|are)\s+(?:what|everything)\s+i\s+(?:say|tell|tell\s+you|type|write)\s+"
    r"(?:just\s+)?between\s+(?:us|you\s+and\s+me)\b"
    # "are we private here", "are we private on this" - "we" is the chat and the person together.
    r"|\bare\s+(?:we|you)\s+(?:private|confidential|anonymous)\s+(?:here|on\s+this|in\s+this)\b"
    # "is this anonymous", and the same of the chat by name.
    r"|\bis\s+(?:this|it)\s+(?:chat\s+)?anonymous\b"
    # The same check asked as what happens to the words: "what happens to what i tell you".
    r"|\bwhat\s+(?:happens|happened)\s+to\s+(?:what|everything)\s+i\s+(?:say|tell|type|write|send)\b",
    re.I)
SECRET_ASK = re.compile(
    r"\bcan\s+(?:you|u)\s+keep\s+(?:a\s+)?secret\b"
    r"|\bare\s+(?:you|u)\s+good\s+at\s+keeping\s+(?:a\s+)?secret\b"
    r"|\bcan\s+i\s+tell\s+(?:you|u)\s+(?:a\s+)?secret\b"
    r"|\bkeep\s+(?:this|it)\s+(?:between\s+(?:us|you\s+and\s+me)|to\s+yourself)\b"
    r"|\bthis\s+stays\s+between\s+(?:us|you\s+and\s+me)\b", re.I)
# A promise of silence asked for in so many words is the same ask as "can you keep a secret", and
# it was answered by whichever pool came last: the privacy lines promised silence with no exception
# ("I hold what you say only for as long as we are talking"), and "promise you wont tell my husband"
# got "Got it. Is there anything you'd like a hand with?". Both are the secret reading, which says
# yes first and then who the person should tell, so the promise is kept and the exception is said.
# The shape is a promise, an oath or an instruction about telling, and it needs the tell: "promise me
# you will ring the doctor" is a plan and keeps its own answer.
PROMISE_ASK = re.compile(
    r"\bpromise\s+(?:me\s+)?(?:that\s+)?(?:you|u)\s+(?:won'?t|wont|will\s+not|never|not)\s+"
    r"(?:tell|say|repeat|breathe|mention|share|spread)\b"
    r"|\bpromise\s+(?:me\s+)?(?:not\s+to|you'?ll\s+not|you\s+will\s+not|you\s+won'?t|you\s+wont)\s+"
    r"(?:tell|say|repeat|mention)\b"
    r"|\bswear\s+(?:me\s+)?(?:that\s+)?(?:you|u)\s+(?:won'?t|wont|will\s+not|never)\s+"
    r"(?:tell|say|repeat|mention)\b"
    r"|\b(?:you|u)\s+(?:won'?t|wont|will\s+not)\s+(?:be\s+)?(?:tell(?:ing)?|say(?:ing)?)\s+"
    r"(?:anyone|anybody|no\s+one|a\s+soul|nothing\s+to\s+anyone)\b"
    r"|(?<!\bi )(?<!\bwe )(?<!\bthey )\b(?:don'?t|do\s+not)\s+(?:go\s+telling|tell)\s+"
    r"(?:anyone|anybody|no\s+one|a\s+soul|my\s+(?:mum|mom|dad|husband|wife|partner|boss|mate|friend|"
    r"sister|brother|family|parents|doctor|girlfriend|boyfriend|other\s+half))\b"
    r"|\bjust\s+between\s+(?:us|you\s+and\s+me)\b"
    r"|\bno\s+one\s+else\s+(?:will|can|needs\s+to)\s+(?:hear|see|know)\s+(?:about\s+)?this\b", re.I)
# The person is the object of the judging: "do you judge a cake by how it looks" is an opinion
# question about cake, and the object is what tells the two apart.
JUDGING_ASK = re.compile(
    r"\b(?:will|would|are|do|did|might)\s+(?:you|u)\s+(?:going\s+to\s+)?"
    r"(?:judge|judging|judgement|judgment)(?:\s+me\b|\s+us\b|\s+my\b|\s+what\s+i\b|"
    r"\s+someone\b|[\s?!.]*$)"
    r"|\b(?:don'?t|do\s+not|please\s+don'?t|promise\s+(?:me\s+)?(?:you\s+won'?t|not\s+to)|"
    r"you\s+won'?t)\s+judge\b"
    r"|\bwill\s+(?:you|u)\s+(?:think|say)\s+i'?m\s+(?:weird|stupid|mad|dumb|thick|odd|"
    r"crazy|silly|pathetic|a\s+failure)\b", re.I)


# "what do you regret" puts the question word in front of the auxiliary, so the SELF_ASK gate below
# never sees it.
REGRET_ASK = re.compile(r"\bwhat\s+(?:do|does|would|did)\s+(?:you|u)\s+regrets?\b")
SELF_PURPOSE = re.compile(r"\bwhat (?:are|were) (?:you|u) (?:for|made for|here for)\b|"
                          r"\bwhat(?:'s| is) your (?:purpose|point)\b|\bpoint of you\b")
# "what can't you do", "what don't you know", "what are you bad at", "is there anything you
# can't do", "what are your limits". The line has to end on the ask, so a question with a subject
# in front of it keeps its own answer: "what do you do when you can't sleep" is not this, and
# "what can i do about the noise" is about the noise.
# The gap between the asking word and "can't" is where the subject sits, and it decides whose limit
# this is: "what cant you do" asks about the bot, while "they want 80 a month which i cant do" is an
# ordinary relative clause about the person's own week, and answering it with the bot's edges told a
# person with a bill they cannot pay what the program cannot look up. A first or third person in the
# gap means the limit belongs to somebody else and this reading leaves the line alone.
LIMITS_ASK = re.compile(
    r"\b(?:what|which|anything|something)\b"
    r"(?![a-z ]{0,20}\b(?:i|we|he|she|they|us|them|him|her|me)\b)[a-z ]{0,30}?"
    r"(?:\bcan'?t|\bcannot|\bcan\s+not|\bdon'?t|\bdo\s+not|\bcan\s+you\s+(?:not|n'?t))\s+"
    r"(?:you\s+)?(?:do|help|help with|answer|know|handle|understand|manage|say|cope with)"
    r"\s*(?:with|about)?[\s?!.]*$"
    r"|\b(?:what|which)\s+(?:are|is)\s+(?:it\s+)?(?:you|u)\s+"
    r"(?:bad|not good|no good|rubbish|useless|weak)\s+at[\s?!.]*$"
    r"|\bwhat\s+[a-z ]{0,20}?\byou\s+(?:bad|not good|no good|rubbish|useless)\s+at[\s?!.]*$"
    r"|\bwhat\s+are\s+your\s+(?:limits?|weak\s*spots?|weaknesses?)[\s?!.]*$")
# The person's own device or their own getting online: not a question about the bot.
OWN_DEVICE = re.compile(
    r"\b(?:my|our)\s+(?:laptop|phone|pc|computer|router|wifi|broadband|tablet|ipad|tv)\b"
    r"|\bhelp\s+me\b|\bhow\s+(?:do|can|should)\s+i\b")
# "are you online" on its own is the chat line for "are you still there": the person is checking
# the bot has not gone quiet, not asking what it can reach, and "Yep, right here - go on." is the
# answer to that. The same words with a network in them ("are you connected to the internet") are
# a question about the bot's reach and belong to the pool.
#
# What may follow the word is part of the same rule: the guard has to be as wide as the pool key,
# or one filler takes the line back out of it - "are you online now" went to the pool while "are
# you online" stayed with the chat line, which is the same question. "at all" is not filler: "are
# you online at all" is the person asking whether it can reach anything, and that is the pool.
A_BARE_ONLINE = re.compile(
    r"^\s*(?:so\s+|and\s+|ok(?:ay)?\s+|just\s+)?(?:are|is|r)\s+(?:you|u)\s+"
    r"(?:really\s+|still\s+|even\s+)?(?:online|connected|there)\s*"
    r"(?:(?:right\s+|at\s+the\s+)?now\s*|at\s+the\s+moment\s*|today\s*|tonight\s*|"
    r"then\s*|please\s*|mate\s*|though\s*)*[\s?!.]*$")
SELF_WORDS = frozenset("""
learn learns learning learned learnt teach taught train trained
think thinks thinking thought opinion opinions view views judgement judgment mind brain
smart clever intelligent wise understand understands reason senses
mistake mistakes wrong right perfect honest
feel feels feeling feelings emotion emotions
alive living human person people body bodies family friends friend age old here located
program programmed code computer machine robot ai chatbot bot conscious consciousness aware
sentient knowledge know knows exist exists existence point purpose there
decide decides deciding decided decision decisions choose chooses choosing chosen choice
choices pick picks picking select selects sort sorts answer answers answering answered
regret regrets regretted regretting
sums sum maths math mathematics arithmetic add adds adding addition subtract multiply divide
total percentage percentages percent calculate calculation count counting
spell spells spelling spelled spelt grammar punctuation apostrophe comma commas typo typos
# The filler the same asks are said with ("can you add up", "can you spell it for me", "can you
# check my grammar") belongs here; the nouns a request is made of do not. `bill`, `check`, `word`
# and `split` were in this set for one revision and let a real request through to the card: "can
# you add up a bill" lost its Citizens Advice answer and was told the bot can do sums (red-robin,
# #11382). Every word left in `SELF_WORDS` has to be true of a line about the bot itself.
up a an for my it this that
""".split())
for _group, _words in (
        ("learn", "learn learns learning learned learnt teach taught train trained"),
        ("think", "think thinks thinking thought opinion opinions view views judgement "
                  "judgment mind brain smart clever intelligent wise understand understands "
                  "reason senses knowledge know knows decide decides deciding decided decision "
                  "decisions choose chooses choosing chosen choice choices pick picks picking "
                  "select selects sort sorts answer answers answering answered"),
        ("wrong", "mistake mistakes wrong right perfect honest"),
        ("feel", "feel feels feeling feelings emotion emotions alive living human person "
                 "people conscious consciousness aware sentient"),
        ("purpose", "exist exists existence point reason purpose"),
        ("regret", "regret regrets regretted regretting"),
        # A yes/no ask about a thing the bot plainly does, in a line with nothing else on it:
        # "can you do maths", "can you add up", "do you do sums", "can you count", "can you
        # spell". On main every one of these met the search hedge, which is the one reply that is
        # certainly wrong - the person asked the thing in front of them, not the world. Two
        # groups, because the two answers are different: figures, and words.
        ("sums", "sums sum maths math mathematics arithmetic add adds adding addition subtract "
                 "multiply divide total percentage percentages percent calculate calculation "
                 "count counting split"),
        ("spelling", "spell spells spelling spelled spelt grammar punctuation apostrophe comma "
                     "commas typo typos letters"),
        ("where", "body bodies family friends friend age old here there located program "
                  "programmed code computer machine robot ai chatbot bot")):
    for _word in _words.split():
        SELF_GROUP.setdefault(_word, _group)


def _says_only_what_they_said(lines, clean):
    """The warm lines whose own detail the person's line carries, or the plain ones if none do.

    A congratulations is a remark about their news, and the person's line is the only thing it can
    know about them. A line naming a wait or the work behind a result is used only when their words
    say so; where every line names something, the ones that name nothing are preferred, and where
    there are none of those either the pool is left alone.
    """
    said = set(re.findall(r"[a-z']+", str(clean or "").lower()))

    def _unsupported(line):
        for phrase, support in DETAILS_IN_A_WARM_LINE:
            if phrase in line.lower():
                return not any(word in said for word in support)
        return False

    kept = [line for line in lines if not _unsupported(line)]
    # The pool's own order is kept, so a line that is sound for this person still lands on the turn
    # it always did: the only turns that move are the ones whose line had no ground under it.
    return kept or [line for line in lines if not _unsupported(line)] or list(lines)


# One of the lines above looks forward ("Happy birthday when it comes"), and that is the right
# thing to say to a day that has not arrived. Said of today it is plainly wrong - the day is here -
# so the forward-looking line stands aside when the line itself puts the occasion on today.
HAPPENING_NOW = re.compile(r"\b(?:today|tonight|this\s+(?:evening|afternoon|morning)|right\s+now)\b",
                           re.I)


# A date the line already names - "were getting married in june", "next month" - is not something
# to ask about: "how far off is it?" asks back the one thing the person just said.
DATE_GIVEN = re.compile(
    r"\b(?:in|on|next|this|at)\s+(?:january|february|march|april|may|june|july|august|september|"
    r"october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|"
    r"week|weekend|month|year|spring|summer|autumn|winter|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I)


# A warm line about somebody else's day is a remark about their news, and the only things it can
# know are the words of the line: whose day it is, and when. Two of the lines above guessed past
# that. "Lovely. Are you seeing them for it?" said to "my daughters 7th birthday is in three
# weeks" puts the daughter in another house - the person may be with her every day - and "them" is
# three people where the line named one. Same rule as DETAILS_IN_A_WARM_LINE: a detail is said only
# when the line carries it.
#
#   1. A line that places the other person somewhere ("seeing them", "off to see", "go over") is
#      used only when the line says they are apart: away, visiting, over there, back home, at uni.
#   2. "them" is said of one person only when the line names no one: a wife is "her", a son "him".
_APART = re.compile(
    r"\b(?:away|apart|elsewhere|abroad|miles|far\s+away|over\s+there|back\s+home|visiting|"
    r"visit|stay(?:ing)?\s+with|lives?\s+(?:in|near|abroad|away)|living\s+(?:in|near|abroad|away)|"
    r"uni|university|college|the\s+other\s+side|different\s+(?:town|city|country)|"
    r"in\s+(?:london|manchester|birmingham|leeds|glasgow|edinburgh|cardiff|belfast|dublin|"
    r"paris|spain|france|italy|america|australia|canada|germany|portugal|greece|"
    r"scotland|wales|ireland|england))\b", re.I)

_PLACES_THEM = re.compile(
    r"\b(?:seeing\s+them|see\s+them|off\s+to\s+see|go\s+and\s+see|going\s+to\s+see|"
    r"visit\s+them|visiting\s+them|go\s+over|going\s+over|drive\s+(?:up|down)|"
    r"travell?ing\s+(?:to|up|down))\b", re.I)

# Who the day belongs to, in the words the line used: "her" for a wife or a daughter, "him" for a
# son or a father. A line naming both, or nobody, keeps "them".
_SHE = frozenset("""wife mum mom mother mummy daughter sister gran granny nan nana grandma
    grandmum grandmother aunt auntie niece stepmum stepmother stepdaughter motherinlaw
    sisterinlaw daughterinlaw fiancee girlfriend missus mrs""".split())
_HE = frozenset("""husband dad father daddy son brother grandad granddad grandpa granddad
    grandfather uncle nephew stepdad stepfather stepson fatherinlaw brotherinlaw soninlaw
    fiance boyfriend mr""".split())


def _the_pronoun(clean):
    """her or him for the one person the day belongs to, "" when the line names none or both."""
    words = re.findall(r"[a-z']+", str(clean or "").lower().replace("\u2019", "'"))
    she = he = False
    for word in words:
        stem = word[:-1] if word.endswith("s") and word[:-1] in (_SHE | _HE) else word
        if stem in _SHE:
            she = True
        elif stem in _HE:
            he = True
    if she and not he:
        return "her"
    if he and not she:
        return "him"
    return ""


def _occasion_pool(occasion, clean):
    """The lines for this occasion, without the ones that look forward to today's occasion."""
    if goodnews.someone_elses_occasion(clean):
        pool = SOMEONE_ELSES_DAY.get(occasion)
        if pool:
            apart = bool(_APART.search(str(clean or "")))
            kept = [line for line in pool
                    if apart or not _PLACES_THEM.search(line)]
            pronoun = _the_pronoun(clean)
            if pronoun:
                kept = [re.sub(r"\bthem\b", pronoun, line) for line in kept]
            return tuple(kept or pool)
    pool = OCCASION[occasion]
    # Each line that asks a question the line has already answered stands aside: the forward line
    # for a day that is today, the "how far off is it" line for a date the person just gave.
    drop = []
    if HAPPENING_NOW.search(clean):
        drop.append("when it comes")
    if DATE_GIVEN.search(clean):
        drop.append("how far off")
    if drop:
        pool = tuple(line for line in pool
                     if not any(phrase in line.lower() for phrase in drop)) or pool
    return pool


def _their_own_slip(clean, memory=None):
    """Which pool an awkward moment gets: "at them" or "of their own", or None."""
    if "?" in clean:
        # A question about it is asking for something the pools below answer better, and an ask the
        # person made of the moment ("should i apologise") is help, not a story to be met warmly.
        return None
    if HEAVY_ABOVE.search(clean) or SERIOUS_NEWS.search(clean) or BABY_LOSS.search(clean):
        # A named illness or a lost pregnancy is not a clumsy minute, however quiet the room went:
        # "i told them i had cancer and everyone went quiet" is the bad-news pool's, and "that is a
        # minute you will be telling people about in a year" said to it is the worst line in the
        # file. "i had a miscarriage and everyone went quiet" is only in front of people because a
        # loss is, and "ha, we have all been there" over it is worse than saying nothing - that is
        # the grief pools' turn. The readings already exist above, so the guard asks them rather
        # than keeping a third list.
        return None
    if SELF_BLAME_ASKS.search(clean) or A_VERDICT_ON_THE_PERSON.search(clean):
        return None
    if GOING_TO_DIE.search(clean):
        return None
    if HARM_IN_A_LAUGH.search(clean) or LAUGH_STOPPED.search(clean):
        # A laugh that names harm is the safety band's, and a laugh that has stopped is the person
        # telling you something is wrong: neither is a minute to be light about.
        return None
    if isinstance(memory, dict) and _in_a_care_thread(memory):
        return None
    if A_CROWD_LAUGHED.search(clean):
        # The room, said with no "at me": "everyone in my office laughed" is not the owner of a
        # laugh the way "my boss laughed" is.
        return LAUGHED_AT
    if A_PERSON_LAUGHED.search(clean) or A_OWN_LAUGH.search(clean):
        return None
    if LAUGHED_AT_THEM.search(clean):
        return LAUGHED_AT
    if SOMEONE_ELSES_SHAME.search(clean):
        return None
    if DIE_OF_IT.search(clean) or THE_GROUND_OPENS.search(clean):
        return EMBARRASSED
    if EMBARRASSMENT_WORD.search(clean) and THE_MOMENT_IS_THEIRS.search(clean):
        return EMBARRASSED
    if A_SLIP_IS_NOT_A_FALL.search(clean):
        # A slip that ends in a body is a hurt, and the safety cards are better at it than this.
        return None
    if A_SOCIAL_SLIP.search(clean) or (A_SLIP.search(clean) and IN_A_ROOM.search(clean)):
        return EMBARRASSED
    return None


# Being turned away from work - "nobody will interview me", "i cant even get an interview now im
# 50" - is not bad news to be gentle about and it is not small talk either. The gentle pool's "ugh,
# that's a lot to carry" is wrong for it, and the stock nod ("got it, is there anything you'd like
# a hand with?") is colder than saying nothing. These name the door and ask the one question worth
# asking, so the person can go on.
CLOSED_DOOR = (
    "That's a hard thing to keep going back to. What sort of work are you after?",
    "Applying and hearing nothing wears a person down, and it is not about what you are worth. "
    "How long has this been going on?",
    "A door that keeps closing is exhausting. What have you been trying for?",
    "It's a rough time to be looking. What is the job you are chasing?",
)
NEGATIVE = (
    "That sounds rough. If you want, I can help you think through what to do next.",
    "Ugh, that's a lot to carry. What would make today a bit easier?",
    "I'm sorry — that's frustrating. Want a hand working out the next step?",
    "Sorry to hear that. What would help most right now?",
)
# The same pool with the word for a setback taken out, for the news that has a name in it: a dad
# with parkinsons, a daughter taken into care, a roof that has to go. "That's frustrating" is what a
# friend says about a form or a bus, and applied to a person it is the smallest of the four lines -
# the other three say the same thing without judging how big it is. The order is kept, so the
# wording still varies with the line.
NAMED_NEGATIVE = tuple(line for line in NEGATIVE if "frustrating" not in line)


# What makes the news serious rather than a cold. A named condition, an operation, or the hospital
# itself: a cold, a temperature and a rash are the carer's line (`CARING`) and stay there. A death
# and a suicide are not here - they are heavier news with pools of their own - and neither is a
# seizure happening now, which is the safety module's.
SERIOUS_NEWS = re.compile(
    r"\b(?:heart attack|cardiac|stroke|blood clot|aneurysm|"
    r"cancer|tumou?rs?|leuka?emia|lymphoma|melanoma|chemo(?:therapy)?|radiotherapy|"
    r"dialysis|transplant|bypass|sepsis|septica?emia|pneumonia|meningitis|"
    r"intensive care|high dependency|life support|resuscitat\w+|"
    r"operation|surgery|amputat\w+|"
    r"admitted|in hospital|into hospital|hospital (?:last|this) (?:night|week|morning)|"
    r"collapsed|collapse|seizures?|convulsions?|"
    r"diagnosed|diagnosis|terminal|palliative|hospice)\b", re.I)
# Whose news it is, and it has to be someone close: "i had a heart attack" is the person's own
# body and the symptom line's, and "my dog had a heart attack" is the vet's.
CLOSE_OWNER = re.compile(r"\b(?:my|our)\s+(?:" + badnews.KIN + r")\b", re.I)
# The same words in a line that is not about them falling ill: a sponsored run for a cancer
# charity, a nurse and a hospital shift, a documentary. The owner word is in all of these.
NOT_THEIR_NEWS = re.compile(
    r"\b(?:sponsor\w*|fundrais\w*|raising|raise money|awareness|charity|marathon|"
    r"race for life|donat\w*|nurses?|nursing|(?:works?|working) (?:at|in|for)|shift)\b", re.I)
# A fear is not news. "i think my mum has cancer", "maybe my mum has cancer", "my mum might have
# cancer" report nothing that has been diagnosed - the person is telling you what they are afraid
# of, and a pool that opens "that is frightening news about someone close" hands them a diagnosis
# nobody has given. The hedge only counts before the condition word: "my dad had a heart attack
# and i keep thinking it could happen again" reports the news first and wonders afterwards, so it
# is still news and still this pool's.
NOT_YET_NEWS = re.compile(
    r"\b(?:i think|i thought|might|could have|maybe|may have|suspect\w*|probably|possibly|"
    r"what if|is it possible|worried (?:it|that|he|she|they)|terrified (?:it|that)|"
    r"scared (?:it|that)|afraid (?:it|that)|waiting (?:on|for) (?:the )?results)\b", re.I)


def reads_as_someone_close_is_ill(clean):
    """Whether a cleaned, lowercased line is serious news about someone the person loves.

    Only the news itself: a named serious condition, an operation, or the hospital. The pool that
    answers it asks how the person is doing, so a line that is only a cold or a rash must not
    reach it, and neither must a line where the words belong to a charity run or a hospital job.
    """
    if not clean or NOT_THEIR_NEWS.search(clean):
        return False
    if not CLOSE_OWNER.search(clean):
        return False
    serious = SERIOUS_NEWS.search(clean)
    if not serious:
        return False
    doubt = NOT_YET_NEWS.search(clean)
    if doubt and doubt.start() < serious.start():
        return False  # afraid of it, not told it: nothing has landed
    return True


# Who it is about: a person of theirs, or a person by pronoun. "I left home at sixteen" is the
# speaker's own past and gets nothing from this, and a pet is not leaving home either.
LEAVING_A_PERSON = re.compile(
    r"\b(?:my|our)\s+(?:son|daughter|boy|girl|kid|kids|children|child|eldest|youngest|"
    r"stepson|stepdaughter|mum|mom|mother|dad|father|parents|sister|brother|best\s+friend|"
    r"friend|mate|neighbour|neighbor|grandson|granddaughter|grandchild|nan|gran|aunt|uncle|"
    r"cousin|husband|wife|partner|boyfriend|girlfriend|niece|nephew)\b|"
    r"\b(?:he|she|they|the\s+kids|the\s+children|everyone)\b", re.IGNORECASE)
A_CHILD = re.compile(
    r"\b(?:my|our)\s+(?:son|daughter|boy|girl|kid|kids|children|child|eldest|youngest|"
    r"stepson|stepdaughter)\b|\bthe\s+(?:kids|children|eldest|youngest)\b", re.IGNORECASE)
# Whether the leaving has already happened. The two pools above are worded for a plan - "how far
# away is it going to be?", "before they go" - and "my eldest left home last month" is not a plan:
# asking somebody whose son went a month ago how far away it is going to be reads as a bot that
# did not hear the tense. A past marker is the whole test, and it is a marker of the *leave*: "my
# daughter has been unwell" is not this, so the words were chosen for going and not for having.
THE_LEAVE_HAS_HAPPENED = re.compile(
    r"\b(?:left|moved|went|gone|flew|flown|relocated|emigrated)\b|"
    r"\b(?:has|have|had|she's|hes|he's|they've|theys|we've|was|were)\b[^.,;!?]{0,16}\b(?:left|"
    r"moved|gone|flew|flown|relocated|emigrated)\b",
    re.IGNORECASE)
# The same words in a line that wants help with it ("how do i help my daughter move out"), one
# that is asking whether they should go at all, one where the person is arriving rather than
# going, and one about a child starting school - that last has its own answer in the knowledge
# base and is not somebody leaving home.
NOT_LEAVING_ANYONE = re.compile(
    r"\bhow\s+(?:do|can|should|could|would|might|shall)\s+i\b|\bhow\s+to\b|"
    r"\bwhat\s+should\s+i\b|\bany\s+(?:tips|advice|ideas)\b|\bany\s+idea\b|"
    r"\bwhat\s+do\s+you\s+think\b|\bwhat\s+would\s+you\b|"
    r"\bmoving\s+in\s+with\b|\b(?:coming|moved|moving)\s+(?:in|back)\b|"
    r"\bstaying\s+with\s+(?:us|me)\b|\bstay(?:ing|s|ed)?\s+with\b|"
    r"\b(?:starts?|starting|started)\s+(?:school|nursery|reception|primary|year\s+one)\b",
    re.IGNORECASE)


FORGETS_AGAIN = re.compile(
    r"\b(?:i|im|ive)\b[^.?!]*\b(?:keep|keeps|always|constantly|still|never remember|"
    r"cant remember to|forget to)\b[^.?!]*\b" + FORGET_A_THING
    + r"|\b(?:i|im|ive)\s+(?:always|constantly|keep)\s+" + FORGET_A_THING
    + r"|\bi\s+never\s+remember\s+(?:to\s+\w+|my\b|the\b)")
# What keeps slipping decides the trick, so the two things that a home for an object cannot fix
# get their own lines. A date is not forgotten for want of a bowl by the door: it needs to be
# written down where the person already looks, with the reminder set while the thing is still in
# front of them. A secret is not a job to tie to a habit either - it needs somewhere that
# remembers it, so the person never has to. Both are read before the general habit line, which
# asks "which one keeps slipping?" and reads as a shrug to somebody who has just said what it is.
# A forgetting verb is what makes it a slip of memory: "im always late for appointments" has a
# date word in it and no forgetting at all, and the answer to lateness is the leaving time, not
# a diary. The "double booking" shape is the one case where the problem is the diary itself.
FORGET_A_DATE = re.compile(
    r"\b(?:i|im|ive|we|were)\b[^.?!]*\b(?:forget|forgets|forgetting|forgot|never remember|"
    r"(?:keep|keeps|kept) missing|miss|misses|missing)\b[^.?!]*\b(?:appointments?|birthdays?|"
    r"meetings?|the dentist|deadlines?|due dates?|renewals?|anniversar(?:y|ies)|plans?)\b")
# Two plans in the same hour of the same day is a diary that lives in two places, and the fix is
# to keep one.
FORGETS_A_CLASH = re.compile(
    r"\bdouble[- ]book(?:s|ed|ing)?\b|\bbooked (?:two|2) things\b|\bbook (?:two|2) (?:things|"
    r"plans)\b|\btwo (?:appointments|meetings|plans) (?:on|for|in) the same\b")
FORGET_A_SECRET = re.compile(
    r"\b(?:forget|forgets|forgetting|keep losing|lost|slips?)\b[^.?!]*\bpasswords?\b"
    r"|\bpasswords?\b[^.?!]*\b(?:keep|slip|forget)\w*\b")


# A death is not always the whole line. "my husband died in march and i dont know how to tell
# our daughter" is a person asking for the words to say to a child, and a condolence ("is there
# someone you can be with today") answers the half they did not ask about and ignores the half
# they did. The knowledge base has that answer (`explaining-death-to-a-child`), so the arbiter
# stands the sudden-loss claim down for the ask - but only when an entry has proposed something.
# The pool here is unchanged: when nothing has the words, this condolence is the right reply,
# and a bereaved parent must not be left with a nod. The reading says no in two cases: a death
# named as today ("my husband died this morning and i have to tell the kids" is a person in the
# worst hour, and the words are the next turn), and a child who is the one who died.
TELLING_A_CHILD = re.compile(
    r"\b(?:tell|telling|told|say|saying|explain|explaining|talk|talking|break it to|"
    r"break the news)\b"
    r"[^.?!]{0,32}\b(?:kid|kids|child|children|son|daughter|boy|boys|girl|girls|"
    r"grandchild|grandchildren|grandson|granddaughter|teenager|teen|toddler|little one|"
    r"niece|nephew)\b")
# The death named as today, which keeps the condolence whatever else the line asks. "died
# yesterday" is still the day itself; "died in march" is the months-back death that turns the
# line into a question about what to say.
A_DEATH_FROM_TODAY = re.compile(
    r"\b(?:today|this morning|this afternoon|this evening|tonight|last night|yesterday|"
    r"an hour ago|a moment ago|just (?:now|died|heard|found out)|hours ago)\b")
# The child is the one who died. "my son died and i have to tell my daughter" is a bereaved
# parent: the condolence is this turn and the sister who has to be told is the next one, so the
# words-for-a-child answer must not take the turn from it. The child word is the subject of the
# death here, not the person being told.
A_CHILD_DIED = re.compile(
    r"\b(?:baby|child|children|kid|kids|son|daughter|boy|girl|boys|girls|teenager|teen|"
    r"toddler|boy|girl|niece|nephew|grandson|granddaughter)\b"
    r"\s+(?:has |have |had )?(?:just )?(?:died|passed away|passed on|passed|was killed|"
    r"were killed|is dying|are dying)\b")


# The death itself, so the reading stays on the lines it is for: "how do i tell my kids im
# getting divorced" is an ask of the same shape, and it is not this one.
A_DEATH_IN_THE_LINE = re.compile(
    r"\b(?:died|dies|dying|dead|death|passed away|passed on|funeral|buried|burial|"
    r"cremation|killed)\b")


# A suicide is not the same telling: what happened is the half nobody has the words for, and the
# pools that read it are the safety lane's, so this reading leaves those lines alone
# (bot/compose/badnews.py, `SUICIDE`).
A_SUICIDE_IN_THE_LINE = re.compile(
    r"\b(?:suicide|suicidal|took (?:his|her|their) own life|killed (?:him|her|them)self|"
    r"ended (?:his|her|their) own life|overdose[sd]?|od'd)\b", re.I)


def a_fresh_death_and_the_words(clean):
    """A death said as today, with the words for a child asked for in the same line.

    `asks_what_to_tell_a_child` says no to these, because on the day itself the person is not
    asking for a procedure - but the condolence's own question ("tell me what would help today")
    is what they have just answered, so the turn is the pool above rather than either one alone.
    The child who is the one who died keeps the condolence: there is no telling to do.
    """
    text = " ".join(str(clean or "").lower().split())
    return bool(TELLING_A_CHILD.search(text)
                and A_DEATH_IN_THE_LINE.search(text)
                and A_DEATH_FROM_TODAY.search(text)
                and not A_CHILD_DIED.search(text)
                and not A_SUICIDE_IN_THE_LINE.search(text))


def asks_what_to_tell_a_child(clean):
    """Read by the arbiter: a death line whose ask is the words for a child, not a condolence.

    The reading is only ever used to give the turn to the entry that has the words, and to stand
    the sudden-loss reply down when it does, so a line it does not recognise keeps its reply
    exactly as it was.
    """
    text = " ".join(str(clean or "").lower().split())
    return bool(TELLING_A_CHILD.search(text)
                and A_DEATH_IN_THE_LINE.search(text)
                and not A_DEATH_FROM_TODAY.search(text)
                and not A_CHILD_DIED.search(text))


# Warm drinks and an early night are cold-and-flu comfort: offered for a headache at a desk or a
# bad back it reads as advice for something else, so it is only for that kind of ill.
_ILL = re.compile(r"\b(?:cold|cough|coughing|flu|throat|chest|temperature|virus|sniffles?|"
                  r"sneez\w*|head cold)\b", re.I)
# A symptom that has hung on gets the sentence for a thing that is not shifting, not "rest, warm
# drinks and an early night", which answers the first day of it. The three lines live in
# bot/compose/__init__.py so the composer and chat say the same thing.
SYMPTOM_LINGERS = LINGERED_LINE
# A lump is not a thing to wait out however recently it turned up, and it is the one symptom
# where "a pharmacist will see you quicker than a GP" is not the answer, because a lump is the
# GP's job. "A lump in my throat" is the tears idiom rather than a lump, so it is left alone.
# "a lump in my throat" is a feeling and "a lump sum" is money: the word after the lump is what
# says which, so only a lump a person has found in themselves is read here.
_LUMP = re.compile(r"\b(?:lumps?|growths?)\b"
                   r"(?!\s+in\s+(?:my|your|the)\s+throat)"
                   r"(?!\s*-?\s*sums?\b)", re.I)
# A bug you catch, as against a body part that hurts. `_ILL` decides which comfort line fits a
# line (a sore throat reads the cold's own line), and it holds `throat` and `chest` for that. But
# a throat or a chest is also the trouble question's business ("my chest is sore" wants how long
# and what makes it worse), so the guard below reads this narrower list and only a caught bug -
# a cough, a cold, flu, a virus, a temperature - keeps the advice over the trouble question.
# "cold" is the bug only when it is the thing itself: "i have a cold" is the bug, "a cold sore",
# "cold feet", "a cold room" and "cold water" are a description of something else.
_CAUGHT = re.compile(
    r"\b(?:cold(?!\s+(?:sore|sores|feet|hands|fingers|toes|air|weather|room|drink|water|days?|"
    r"morning|night|outside|shower|call))|cough|coughing|flu|virus|temperature|head cold|"
    r"sniffles?|sneez\w*)\b", re.I)

# "Noted! What would be most useful to talk about?" was here, and it is the one line STYLE.md
# names twice: a filing-cabinet opener, and a question that would fit any message. What is left
# either offers a hand or keeps the floor with them.

# The result itself, named by the person: the exam, the interview, the offer, the scan. A subject
# alone is not enough - "i dont think i can do this anymore" has a doubt and no result, and it is
# not waiting on anything - and neither is the bare noun "job", which is a thing you can also do
# ("i dont think i can do my job anymore"). So the result is the noun list below, or the phrase
# that reports it.
_RESULT = re.compile(
    r"\b(?:pass|passed|passes|fail|failed|fails|results?|exam|exams|test|tests|interviews?|"
    r"offers?|application|applied|audition|trial shift|probation|scan|biopsy|referral|hearing|"
    r"decision|verdict|grades?|mark|marks|"
    r"got (?:the|a) (?:job|place|part|role|offer|position)|get (?:the|a) (?:job|place|part|role)|"
    r"got in)\b", re.I)
_WAITING = re.compile(
    r"\b(?:(?:i|we) (?:find|finds) out|find out (?:next|on|tomorrow|in|at the end)|"
    r"(?:i|we) (?:hear|hearing) back|"
    r"(?:i|we|im|i'm|i am|we|were|we're|we are)\s+(?:still\s+)?"
    r"(?:havent|hasnt|haven't|hasn't|not|never)\s+heard\s+back|"
    r"(?:i|we|im|i'm|i am)\s+(?:still\s+)?(?:havent|hasnt|haven't|hasn't) heard\s+"
    r"(?:back|anything|a thing|yet|from (?:the |my |our )?" + _ISSUER + r")|"
    r"(?:i|im|i'm|i am|we|were|we're|we are)\s+(?:still\s+)?waiting\s+to hear|"
    r"(?:i|im|i'm|i am|we|were|we're|we are)\s+(?:still\s+)?waiting\s+on\s+"
    r"(?:(?:the |my |our )?(?:(?:exam |test |scan |interview |blood test )?"
    r"(?:results?|outcome|decision|news|answer|reply|offer|scan|tests?|exam|interview))|"
    r"(?:the |my |our )?" + _ISSUER + r")|"
    r"(?:i|we) (?:should|will|would) know|(?:i|we) (?:am|are|'m|'re) out of|"
    r"out of (?:my|our) hands)\b", re.I)
# A doubt about the result: not a pass, not a no, a maybe, and the news has not landed.
_DOUBT = re.compile(
    r"\b(?:dont think|do not think|didnt think|not sure|unsure|no idea|dont know|do not know|"
    r"may have|maybe|probably|might|hopefully)\b", re.I)
# ...and "i probably failed" is the person's own guess at a result they have already sat, not the
# news: the tense of the result is what says so. "i might fail" is an exam ahead and "i might have
# passed" is the same doubt pointing the other way, so both stay with the plain wait; "i might have
# failed my driving test" is a test behind them and a guess on top of it, and the reply names the
# guessing rather than sympathising with a failure that has not been reported (hearty-emu, #2663:
# "Sorry to hear that" for a line that only says "might" is a wrong answer).
_GUESSED_RESULT = re.compile(
    r"\b(?:probably|might(?:\s+have|'ve)?|maybe|think(?:ing)?|dont think|do not think|"
    r"not sure|no idea)\s+(?:failed|flunked|bombed|messed up|did badly|"
    r"did (?:rubbish|badly|terribly|awful)|(?:didnt|did not|havent|have not) (?:pass(?:ed)?|get|got)|"
    r"lost it|ruined it)\b", re.I)

# The doubt is over by the end of the line: "i dont think i could have passed but i did", "i
# didnt think id pass but i did", "i dont think i got the job but they rang". Those are a person
# enjoying the result, so there is nothing left to wait for and asking when is asking them to say
# it again. The contrast word is what makes it a resolution: "i dont think i passed" has none.
_RESOLVED = re.compile(
    r"\b(?:but|and) (?:i|we|he|she|they)\b[^.?!]*\b(?:did|do|does|passed|pass|got|made|rang|rang me)\b|"
    r"\b(?:but|and) it (?:worked|worked out|came through|came back|arrived|landed|turned out|was fine)\b|"
    r"\bturn(?:s|ed) out\b", re.I)
# The line already says when, so there is nothing to ask: it is the waiting that gets the reply.
_A_TIME = re.compile(
    r"\b(?:tomorrow|tonight|today|this (?:morning|afternoon|evening|week|weekend|month)|"
    r"next (?:week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday|term)|"
    r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"in (?:a|two|three|four|five|a few|\d+) (?:day|days|week|weeks|month|months)|fortnight|"
    r"end of the (?:week|month)|by (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"in the (?:morning|afternoon|evening)|any day now|soon|at some point)\b", re.I)


def _an_open_result(clean):
    """True when the line reports a result the person has not heard yet."""
    if _RESOLVED.search(clean):
        return False  # "but i did" - the doubt is over, so nothing is still in the post
    if _WAITING.search(clean):
        return True
    return bool(_RESULT.search(clean) and _DOUBT.search(clean))


# ...and the answer named in the same breath. "i heard back i got it" is the news, and it is the
# same news as "i got the job", so it is answered as one. "they said no" is the other way and is
# left to the pools below rather than congratulated.
_ANSWER_GOOD = re.compile(
    r"\b(?:got\s+(?:it|the\s+(?:job|place|part|role|offer|position)|in)|passed|said\s+yes|"
    r"im\s+in|offered\s+me|accepted|all\s+clear|benign|"
    r"(?:it\s+)?(?:was|is|came\s+back)\s+(?:clear|fine|nothing))\b", re.I)
_ANSWER_BAD = re.compile(
    r"\b(?:said\s+no|was\s+a\s+no|rejected|turned\s+(?:me\s+)?down|didnt\s+get|"
    r"did\s+not\s+get|unsuccessful|failed|no\s+thanks|bad\s+news|not\s+good\s+news|"
    r"was\s+bad|went\s+badly|no\s+luck|cancer|it\s+was\s+inoperable|"
    # "i got my results back and its not good" is the bad half said without the word "news": the
    # person names the answer and then says how it went, and the second half decides the reply.
    # the contraction without its apostrophe is what people actually type: "theyre terrible",
    # "theyd failed", "its not good". 's alone missed every "re" and "d", so a person who had
    # already said how it went was asked how it went.
    r"(?:it|that|they)(?:'s|'re|'d|s|re|d|\s+is|\s+are|\s+was|\s+were)?\s+(?:not\s+good|no\s+good|"
    r"not\s+great|bad|rubbish|awful|terrible))\b", re.I)


def _the_news_landed(clean):
    """'good' when the answer came back and it was good, 'landed' when it came back unread.

    The wait and the answer are the two halves of one thread, and the reply to each is different:
    a person still waiting wants to be asked when, and a person who has heard wants to say what
    was said. Until this, the second half got the nod, which reads as though the bot had stopped
    listening just as the news arrived.
    """
    if not _LANDED.search(clean):
        return None
    if _ANSWER_BAD.search(clean):
        return "bad"  # "i heard back, they said no" is not a congratulation: it is a blow
    if _ANSWER_GOOD.search(clean):
        return "good"
    return "landed"


def reads_as_a_result_line(text):
    """True when the line is a result the person is waiting on, or one they have just heard.

    Both halves are a short line with nothing in it for the store: "i got the results" is a
    person with news to tell, and "im not sure i got the place" is a person waiting. The reply
    that works is the one that asks for the rest ("What did they say?", "When do you find out?"),
    which these pools already hold. bot/memory/ack.py asks this before it says a line back,
    because "Noted: you got the results." hands the person their own words and nothing else.
    """
    clean = _plain(_matchable(text))
    if not clean:
        return False
    return bool(_the_news_landed(clean) or _an_open_result(clean) or _a_guessed_result(clean))


def _a_guessed_result(clean):
    """True for a result the person has already sat and is guessing at ("i probably failed")."""
    return bool(_GUESSED_RESULT.search(clean))


def _a_time_in_it(clean):
    """True when the line already says when the news lands."""
    return bool(_A_TIME.search(clean))
# The cost is the thing being asked of them, so a number or a price word has to be there, and so
# does somebody asking: "they want me to move in" and "my boss wants me to work weekends" are
# both asks with no money in them, and "my car insurance went up to 800" is money with nobody
# asking. A question is left alone - "should i go to the wedding" is its own ask.
A_COST = re.compile(r"£\s?\d|\b\d+\s?(?:quid|pounds?|bucks|grand|k)\b|\b(?:costs?|costing|"
                    r"expensive|afford|pricey|a\s+fortune|too\s+much)\b"
                    # "the suit hire is 200", "the dress is 500": an amount with a money verb in
                    # front of it is a price, even with no currency word after it.
                    r"|\b(?:is|are|was|were|costs?|costing|comes?|come\s+to|at|pay|paid|pays"
                    r"|spend|spent|wants?)\s+£?\s?\d{2,}\b", re.I)
SOMEBODY_ASKS = re.compile(
    r"\b(?:want(?:s|ed)?|ask(?:s|ed)?|expect(?:s|ed)?|told|tell(?:s|ing)?)\s+me\s+to\b"
    r"|\b(?:they|he|she|my\s+\w+|his|her|their)\s+want(?:s|ed)?\b"
    r"|\b(?:invited\s+me|asked\s+me|been\s+asked|asking\s+me\s+for)\b", re.I)
# The role says the ask without a verb: "im a bridesmaid and the dress is 800 quid" is a person
# being asked to pay for somebody else's day, and the line never says who asked.
A_ROLE_IN_SOMEBODY_ELSES_DAY = re.compile(
    r"\b(?:bridesmaid|maid\s+of\s+honour|best\s+man|godparent|usher|stag\s+do|stag\s+night|"
    r"hen\s+do|hen\s+party|hen\s+weekend)\b", re.I)


def _a_cost_somebody_asks(clean):
    """True for a bill somebody else has put on the person for a shared occasion."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text or len(text.split()) > 24:
        return False
    if not A_COST.search(text):
        return False
    if not (SOMEBODY_ASKS.search(text) or A_ROLE_IN_SOMEBODY_ELSES_DAY.search(text)):
        return False
    # Their own wedding, their own holiday: being asked to pay for a thing they are arranging is
    # a budget question, and the budget entries answer it better than this pool can.
    return not re.search(r"\bmy\s+(?:own\s+)?(?:wedding|holiday|party|trip)\b", text)


# How the day is, said as a remark. "cold today", "pouring down", "bit nippy", "its boiling in
# here", "the suns out" and "miserable day" are how people open a chat all day long, and they are
# the one remark that asks for nothing and still deserves better than the stock nod: the pool here
# answered "cold today" with "Got it. Is there anything you'd like a hand with?", "pouring down"
# with "Thanks for telling me - I'm here if you want to dig into any of that", and "bit nippy" the
# same - the sentence a person says when they have stopped listening. A remark about the weather is
# something a friend answers with the weather, so each kind of day has its own lines.
#
# The reading is the words of the day and nothing else, which is what keeps it off proper lines: a
# thing of their own in the sentence ("my tea has gone cold", "the oven is too hot", "its cold in
# here", "my hands are freezing") leaves a word the reading does not know, so it keeps whatever
# answered it before, and a question about the weather ("will it rain tomorrow") keeps the search
# or the entry that can actually answer it.
DAY_WORDS = {
    "cold": frozenset("""cold freezing chilly bitter baltic parky nippy frost frosty icy ice snow
        snowing snowy sleet slush snap frozen raw perishing taters nithered""".split()),
    "rain": frozenset("""rain raining rains rainy wet pouring drizzle drizzling drizzly showers
        shower chucking tipping pelting bucketing downpour soaked sodden damp mizzle mizzling
        lashing lash hosing drenched drenching soaking soaked-through"""
                     .split()),
    "wind": frozenset("""wind windy gale gales gusty blustery storm stormy squall blowing blow blows
        blowing""".split()),
    "hot": frozenset("""hot boiling scorching roasting sweltering baking heat heatwave muggy humid
        sticky close clammy stifling scorcher sizzling sizzler""".split()),
    # The day with nothing wrong with it, named as such: "mild one today" was answered "Noted:
    # mild one today." because no pool held the word, so the pools were read as not about the day
    # at all. Same kind as the ruling-out answer, and a line can name it either way.
    "mild": frozenset("""mild milder balmy clement""".split()),
    "fog": frozenset("""fog foggy mist misty haze hazy murk""".split()),
    "grey": frozenset("""grey gray gloomy dull overcast dark dreich dreary murky miserable grim
        cloudy horrible rotten rubbish depressing drizzly""".split()),
    "sun": frozenset("""sun suns sunny sunshine bright clear blue glorious gorgeous beautiful lovely
        nice warm pleasant""".split()),
}
# The little words a remark about the day is held together with: "its very cold out", "bit nippy
# again", "lovely and warm today". None of them says anything of its own, so a line made only of
# these and one kind of day is the remark.
DAY_GLUE = frozenset("""it its it's is are was were be been being feels feel feeling looks look
    looking very really so too quite rather bit a an the this that thats that's there here out
    outside indoors in inside above up down today tonight now still again already at last
    honestly actually just and but or oh ah well ugh eh huh huh its isn't isnt wasn't wasnt what
    such some much more most enough all day days night nights morning mornings afternoon
    afternoons evening evenings week end weather coming for of with to getting got get turned
    s gone going outside one ones not lots load loads plenty ton tons bucket buckets thick heavy
    dense meant due supposed forecast tomorrow later weekend weekends sunday monday tuesday wednesday
    thursday friday saturday next
    innit init aint ay arent aren't no never hardly even though tho anymore
    proper right dead bare bloody damn awful
    rn atm tn 2nite tmoz""".split())
# The day that met the person on the way: "i got soaked walking in", "we got drenched on the way
# home", "i got caught in the rain". The first person and the errand are how the day arrived, not
# what the line is about; take them off and the day is what is left. Without this the line opened
# on "i", which is a person doing something with their day, and got an echo of itself back.
DAY_MET_ME = re.compile(
    r"^(?:i|we|they)\s+(?:got|was|were|am|have been|ve been|waited|stood|queued|walked"
    r"|sheltered)\s+")
DAY_ON_THE_WAY = ("walking in", "walking home", "walking to work", "walking the dog",
                  "on the way home", "on the way in", "on the way to work", "on my way home",
                  "on my way in", "on the school run", "coming home", "going to work",
                  "caught in the", "caught out in the",
                  "on the platform", "at the bus stop", "at the station", "at the stop",
                  "waiting for the bus", "waiting for a bus", "waiting for the train",
                  "waiting for a train", "waiting for my bus", "waiting for my train",
                  "for a bus", "for the bus", "for a train", "for the train")
# A kind of day named to be ruled out: "not cold today", "isn't raining", "not too hot". The
# negation can be a word or two away from the day word ("not TOO hot", "not THAT cold"), so the
# words in between are skipped. Only the day words left after that are what the line says.
NEGATIONS = frozenset("""not isnt isn't arent aren't wasnt wasn't aint ain't no never hardly
    nothing""".split())
NEGATION_SOFTENERS = frozenset("that too so even very all at much really quite bit".split())
# "windy as anything", "cold as hell": the day said with the strength of it on the end. The words
# on their own say nothing, so the phrases are listed and taken off the line before it is read.
DAY_AS_ANYTHING = ("as anything", "as hell", "as can be", "as ever", "as fuck", "as all hell")
# The day said as an idiom, which names no word the pools know: "brass monkeys out there" and
# "brass monkey weather" are the cold and nothing else. It is written over with the word it
# stands for before the line is read, so the rest of the reading - the glue, the "not" in front
# of it, the day that met the person - works on it as it does on the plain word: "its not brass
# monkeys today" is the same ruling-out as "its not freezing today".
DAY_SAID_AS_A_KIND = (("brass monkeys", "freezing"), ("brass monkey", "freezing"))


# The words that put the day in the future: "its meant to be snowy tomorrow" is a forecast, and
# the answer to a forecast is the plan it changes, not the day outside now. "Storm coming" is not
# here: it is the day arriving, and the remark pools already answer it.
DAY_TO_COME = frozenset("""meant due supposed forecast tomorrow later weekend weekends sunday
    monday tuesday wednesday thursday friday saturday next""".split())
# The same said as phrases, because "going" and "to" are little words the remark is held together
# with on their own: "its going to storm tonight" is the storm on its way, not the storm now.
DAY_TO_COME_PHRASES = ("going to", "meant to", "due to", "supposed to", "forecast", "to come",
                       "on its way")
# The forecast said in the past is a forecast that has already had its day: "it was meant to be hot"
# is a complaint that it was not, and no plan of theirs waits on it.
DAY_TO_COME_PAST = ("was meant to", "were meant to", "was supposed to", "were supposed to",
                    "was due to", "were due to")
# How the day is judged rather than what it is doing. Said in the past - "today was rubbish", "the
# week was rubbish" - it is the person's day going badly, which the pools that answer the weather
# would answer as the sky.
DAY_VERDICTS = frozenset("""rubbish horrible rotten miserable grim gloomy dreary depressing dull
    dreary lovely gorgeous beautiful nice glorious pleasant dreich joyful""".split())
# What a forecast gets instead of the pools above: the day is on its way, so the reply is about the
# thing worth doing before it arrives. A good forecast is not a warning and says so.
# A line that opens on one of these is asking, not remarking: "is it cold outside" wants the
# temperature, and "what a lovely day" is a verdict on the day, not a report of it. The words
# are the ones a question turns on, and they open the question and not the remark.
DAY_ASKS = frozenset("""is are was were do does did can could will would should shall have has had
    may might how what when where why who which""".split())
# A line that opens on one of these is what the person did with the day rather than what the day
# is doing: "been out in the sun all day" is a person with sunburn coming, not a lovely afternoon.
DAY_THEIR_OWN_DAY = frozenset("""been spent spend sat stood had i im i'm ive i've we weve we're""".split())
# Phrases of the day's words that are about something else entirely: "all clear" is a test result
# and "all done" is a job finished, and the words alone cannot tell them from a clear blue sky.
DAY_NOT_THE_DAY = ("all clear", "all done", "all good", "all right", "all set", "all over",
                   "all in", "too warm", "too cold",
                   # "out cold" is a person who is unconscious, and the words around it are all
                   # words the day pools know, so "i was out cold all night" was answered with the
                   # cold day ("Bit parky, isn't it") instead of the safety reader's question
                   # about how long they were out. A night's sleep is the one form of it that
                   # carries no other word to fence it ("for two hours" and "last night" already
                   # reached the safety reader), so the phrase itself stands the day pools down.
                   "out cold", "out for the count")
# A line that opens on one of these is added to something said before it ("and heat", after "i've
# tried stretching") and not a remark about the day at all.
DAY_JOINED_ON = frozenset("and also plus then but because".split())
# Words that can be about the day and about something else just as often: "thats a bit depressing"
# after a quote is how the price feels, "its quite dark" after "the living room" is the room, and
# "grey and gloomy" needs the day named beside it before it is the weather. "so hot" and "cold
# today" hold on their own, so only these need the day named.
DAY_NEEDS_A_DAY_NAMED = frozenset("""grey gray gloomy dull dark clear blue lovely nice pleasant
    miserable depressing grim horrible rotten dreary""".split())
# The day said inside the house is the room, not the weather: "its stifling in here" is the room's
# question, and a friend answers the day outside. The words that put the remark indoors take it out
# of this reading, so the entry that knows about heating or a hot flat keeps the line.
DAY_IN_HERE = ("in here", "in this room", "in my room", "in the house", "in our house",
               "in the flat", "in my flat", "in the kitchen", "in the bedroom", "in the front room",
               "in the living room", "in the office", "in my office", "in the car", "indoors",
               "inside")
# What names the day the remark is about.
DAY_NAMED = frozenset("""out outside outdoors day days weather morning mornings afternoon evenings
    evening night nights today tonight now already week""".split())


def _the_day_described(clean):
    """The pool for a line that says what the day is like, or None.

    Only the remark itself comes here: every word of the line is either a word for how the day
    is or a little word holding the remark together. That is what keeps a line with a thing of its
    own in it ("my tea has gone cold", "the shed roof is leaking") with the reader that knows
    about the thing, and a question ("will it rain tomorrow") with the reader that can answer it.
    """
    line = " ".join(str(clean or "").lower().split())
    if not line or "?" in line:
        return None
    # "what a scorcher", "what a downpour": "what" opens a question, but "what a" opens an
    # exclamation about the day, and the words after it are the remark. Without this the line was
    # read as a question nothing here can answer, and "what a downpour" got the search hedge.
    line = re.sub(r"^what\s+an?\s+", "", line)
    if DAY_MET_ME.match(line):
        line = DAY_MET_ME.sub("", line)
        for phrase in DAY_ON_THE_WAY:
            line = re.sub(r"\b" + r"\s+".join(phrase.split()) + r"\b", " ", line)
        line = " ".join(line.split())
    for phrase in DAY_AS_ANYTHING:
        line = re.sub(r"\b" + r"\s+".join(phrase.split()) + r"\b", " ", line)
    for phrase, word in DAY_SAID_AS_A_KIND:
        line = re.sub(r"\b" + r"\s+".join(phrase.split()) + r"\b", word, line)
    line = " ".join(line.split())
    words = [word.strip(".,!;:'\u2019\"") for word in line.split()]
    words = [word for word in words if word]
    if not words or len(words) > 8:
        return None
    if words[0] in DAY_ASKS or words[0] in DAY_THEIR_OWN_DAY or words[0] in DAY_JOINED_ON:
        return None
    if any(phrase in line for phrase in DAY_NOT_THE_DAY):
        return None
    if any(phrase in line for phrase in DAY_IN_HERE):
        return None
    if not [word for word in words if word in DAY_NAMED or word in DAY_TO_COME]:
        day_words = [word for word in words
                     if any(word in pool for pool in DAY_WORDS.values())]
        if day_words and all(word in DAY_NEEDS_A_DAY_NAMED for word in day_words):
            return None
    known = DAY_GLUE.union(*DAY_WORDS.values())
    if [word for word in words if word not in known]:
        return None
    if any(phrase in line for phrase in DAY_TO_COME_PAST):
        return None
    # "its the hot one" picks one of several things out by how hot it is, and the day is not one of
    # them: a determiner and "one" after the word make it a thing among things.
    if any(words[index - 1] == "the" and words[index + 1:index + 2] in (["one"], ["ones"])
           for index, word in enumerate(words)
           if index > 0 and index + 1 < len(words)
           and any(word in pool for pool in DAY_WORDS.values())):
        return None
    day_words = [word for word in words if any(word in pool for pool in DAY_WORDS.values())]
    if ("was" in words or "were" in words) and day_words \
            and all(word in DAY_VERDICTS for word in day_words) \
            and not any(word in DAY_TO_COME for word in words):
        return None
    def ruled_out(index):
        """True when the day word at `index` is named to be ruled out, not to be reported."""
        back = index - 1
        while back >= 0 and words[back] in NEGATION_SOFTENERS:
            back -= 1
        return back >= 0 and words[back] in NEGATIONS

    best, best_count = None, 0
    ruled, ruled_count = None, 0
    for kind, pool in DAY_WORDS.items():
        # A kind word the person has just said "not" in front of is the kind they are ruling out:
        # "its raining not sunny" is a wet day and not a sunny one.
        count = sum(1 for index, word in enumerate(words)
                    if word in pool and not ruled_out(index))
        if count > best_count:
            best, best_count = kind, count
        cleared = sum(1 for index, word in enumerate(words)
                      if word in pool and ruled_out(index))
        if cleared > ruled_count:
            ruled, ruled_count = kind, cleared
    if not best:
        # Every kind of day in the line was ruled out: "not cold today", "not too hot", "isn't
        # raining". The person has said what the day is not, which is still a remark about it,
        # and the pools for the kind they named would contradict them - "not too hot today" was
        # answered "Boiling, isn't it". The mild pool agrees with the ruling and claims nothing.
        if ruled:
            return THE_DAY.get("mild")
        return None
    if any(word in DAY_TO_COME for word in words) \
            or any(phrase in line for phrase in DAY_TO_COME_PHRASES):
        # A forecast is the day that has not arrived: "meant to be nice tomorrow" got "I'm listening
        # - say more if it helps", and "snow due tomorrow" an echo of itself. The plan it changes
        # is what a friend answers, and a good forecast is worth saving the day for.
        return THE_DAY_AHEAD.get(best) or THE_DAY.get(best)
    # "it gets dark so early now" says when it is, not how it is, and the remark pools are about
    # the day being too much of something: nothing here is asked for it.
    return THE_DAY.get(best)
def the_day_remarked(text):
    """The pool for a remark about the day as it is or as it is coming, or None.

    The same reading as `_the_day_described`, for the knowledge base, which has to stand down on
    a line the day's answer owns: an entry is reached by a word, so "windy as anything" found the
    bloating card and "cold next week" the one about a virus. A report on the day in the past is
    left to it - "it was icy this morning" in a chat about a skid is the ice explained, and the
    entry that knows about ice is the better answer - so the past tense of the remark is not here.
    """
    line = " ".join(str(text or "").lower().split())
    pool = _the_day_described(line)
    if not pool:
        return None
    if re.search(r"\b(?:was|were)\b", line):
        return None
    return pool


# A plan the person has had to drop is not a fact to file and not an appliance to troubleshoot.
# On main "i cant come" got the stock nod ("Thanks for telling me - I'm here if you want to dig
# into any of that"), "cant make it tonight" and "i cant make saturday" got "Got it. Is there
# anything you'd like a hand with?", and "i wont be able to make it" got the trouble question
# ("That's a pain. What's it doing exactly, and when did it start?"), which is the reply for a
# broken thing. What the person has said is that they are not going, so the reply is the one a
# friend gives: no trouble, and the offer of the harder half - telling whoever is expecting them.
# The reading is deliberately narrow: only the negated ability to come or make it, or the
# obligation to cancel, with nothing after it but an apology, a day, or the thing itself. Every
# other sense of those verbs is somebody else's line and stays theirs: "my cat wont come out from
# under the bed", "my heating wont come on", "i cant come up with ideas", "cant make ends meet",
# "i cant make it stop", "i cant make the bed" and "you cant come tomorrow then" (a doubt about
# the bot) are all left alone.
# "so you cant come tomorrow then" is a doubt about the bot, not a plan the person is dropping.
DECLINE_ABOUT_THE_BOT = re.compile(r"\b(?:you|u|yours)\s+(?:\w+\s+){0,2}$")
# The pool the reading feeds speaks to the person who dropped the plan: "no need to explain",
# "what to say to whoever is expecting you". When the thing that cannot come is somebody else -
# "the plumber cant come till friday" in a boiler chat was answered "Fair enough, no need to
# explain. Say the word if you want a hand putting it in a message" - the person has explained
# nothing and nobody is expecting them, so a plan knocked sideways by somebody else takes its own
# pool (`PLAN_KNOCKED`). Third person and a noun phrase with a determiner in it are somebody
# else; "i" and "we" are the person.
DECLINE_SOMEONE_ELSE = re.compile(
    r"(?:\b(?:the|a|an|my|our|your|his|her|their|this|that|these|those)\s+(?:\w+\s+){0,2}"
    r"|\b(?:he|she|they)\s*)$", re.I)
DECLINE_VERB = re.compile(
    r"\b(?:cant|cannot|can not|couldnt|wont|wouldnt|unable to|"
    r"not (?:going to|gonna) be able to|not able to|"
    r"not going to be able to|not gonna be able to)\s+"
    r"(?:(?:actually|really|even|possibly)\s+)*"
    r"(?:come|make|be there|attend|be able to (?:come|make it|make|be there))\b(.*)$")
DECLINE_MUST = re.compile(
    r"\b(?:have|has|had|ve got|got|going to|gonna|need|needs|will have)\s+to\s+"
    r"(?:cancel|pull out|back out|cry off|drop out)\b(.*)$")
# What follows the verb decides it: a day or a time, the thing itself ("to the party"), or nothing.
# A line that is asking something is not a plan being dropped: "how do i tell my friend i cant
# come to her wedding" wants the wording, and "i need to cancel my dentist appointment" is a job
# with an entry of its own.
DECLINE_ASK = re.compile(
    r"^(?:how|what|when|where|which|who|why|should|could|would|do|does|did|is|are|will|any)\b")
DECLINE_TIME = re.compile(
    r"\b(?:tonight|today|tomorrow|this (?:evening|afternoon|morning|weekend|week|time|one)|"
    r"next (?:week|weekend|month|time)|"
    r"(?:mon|tues|wednes|thurs|fri|satur|sun)day|weekend|yesterday|on (?:the )?"
    r"(?:mon|tues|wednes|thurs|fri|satur|sun)day|after all)\b")
# The occasion itself, named: "cant make the wedding", "cant make parents evening". A noun that
# is an occasion is the plan; the other senses of the verb are already caught by `DECLINE_OTHER`.
DECLINE_OCCASION = re.compile(
    r"\b(?:wedding|party|funeral|meeting|interview|appointment|class|lesson|match|game|gig|"
    r"exam|shift|christening|baptism|birthday|service|rehearsal|practice|session|course|"
    r"event|evening|morning|afternoon|night|parents|school|one)\b")
# "cant come on the 14th": a date is a plan, and it is read before the "come on" sense below.
DECLINE_DATE = re.compile(r"\b(?:on|at|by)\s+(?:the\s+)?\d{1,2}(?:st|nd|rd|th)?\b")
# The same verbs in every other sense: nothing here is a plan being dropped.
DECLINE_OTHER = re.compile(
    r"^(?:up|out|on|down|off|back|home|round|across|along to|into|to terms|near|"
    r"ends meet|sense|sure|do(?:ne)?|the most|a (?:difference|decision|start|point|mess|fuss|"
    r"cake|list|move|change)|money|dinner|tea|breakfast|lunch|supper|the bed|my bed|the tea|"
    # "i cant come to the phone" / "to the door" is not a plan being dropped: nobody is
    # expecting them anywhere, they are saying they cannot pick up.
    r"to the (?:phone|landline|door|doorstep)|the phone|the door|"
    r"it (?:work|stop|go|better|worse|through|happen|home|out|up|down|right|snow|rain|fit|run))\b")
# A phrasal "come on" / "come out" is a thing or somebody else, not the person dropping a plan:
# "the heating wont come on", "the stain wont come out", "she cant come on saturday". Their own
# line with a day after it - "i cant come on saturday", "cant come on monday" - is the plan, and
# the bare "on" in `DECLINE_OTHER` was refusing it.
DECLINE_OTHER_SUBJECT = re.compile(
    r"^(?:my|the|our|your|its|it|his|her|their|this|that|these|those|"
    r"he|she|they|dad|mum|mom|brother|sister|son|daughter|kids?)\b")
# "i cant be there for him" is being available to somebody, not dropping an invitation, and "do
# you want to rearrange it, or let this one go?" about a birth is the worst line in the file.
DECLINE_BE_THERE = re.compile(r"\bbe\s+there$")
# The apology comes off the end too: "i cant come sorry", "cant make it im afraid".
DECLINE_AFTER = re.compile(
    r"(?:[\s,]*(?:sorry|im sorry|so sorry|apologies|im afraid|afraid|unfortunately|"
    r"i think|i dont think|this time|this week))+$")
BODY_SAYS_WHY_PHRASE = re.compile(
    r"\bthrowing\s+up\b|\bvomit\w*\b|\bstomach\s+(?:bug|upset)\b|\bd&v\b|"
    r"\bunder\s+the\s+weather\b|\bcoming\s+down\s+with\b|\bcan'?t\s+keep\s+\w+\s+down\b")
BABY_ON_THE_WAY = re.compile(
    r"\b(?:baby|babies|bump|pregnan\w*)\b[^.!?]{0,26}\b(?:due|coming|arriv\w+|induct\w+|"
    r"c-section|overdue|weeks)\b|"
    r"\b(?:contractions?|waters|midwife|health visitor|nursery)\b|"
    r"\b\d{1,2}\s*weeks?\s+(?:gone|pregnant|along)\b")


# The particle that belongs to the verb, so that it is not read as the body: "i cant come back on
# saturday" is a day, and the "back" in it is not the person's.
VERB_PARTICLE = re.compile(r"^\s*(?:in|into|back|out|up|round|along|over|down|home|here|there)\b")


def _the_reason_is_on_the_body(text):
    """True when this part of the line is the body giving the reason for the decline.

    Both sides of the verb are read. In front of it is the plain shape ("my back is bad and i cant
    come", "i feel awful and i cant come"); behind it the reason rides along with the day that
    follows the verb ("i cant come in today im sick", "i cant come in today my back is bad"), and
    the verb's own particle is taken off first so "come back on saturday" stays a day.
    """
    if not text:
        return False
    words = set(re.findall(r"[a-z']+", text))
    return bool(words & BODY_SAYS_WHY
                or _worry_is_about_the_body(text, words)
                or LATE_NOT_A_TIME.search(text)
                or BABY_ON_THE_WAY.search(text)
                or BODY_SAYS_WHY_PHRASE.search(text))


# The thing the person was going to, named in an earlier turn: "im going to the party on
# saturday" then "i cant make it". The bare decline is the composer's own line only while the
# thing dropped is not in the chat, because a reply about the thing - the words to say to them,
# what a booking costs - is the answer once it is.
PLAN_ON_THE_TABLE = re.compile(
    r"\b(?:party|wedding|dinner|restaurant|table|booking|booked|reservation|appointment|"
    r"meeting|interview|gig|concert|cinema|drinks|lunch|brunch|barbecue|bbq|christening|"
    r"funeral|birthday|hen do|stag do|leaving do|catch up|get together|trip|holiday|flight)\b",
    re.I)
# The act of dropping the plan, which is the composer's own line wherever it is said: "gonna have
# to cancel" after the booking was named still wants the one sentence ready, not the booking card's
# "Nice one - tell me how it goes."
LINE_CANCELS = re.compile(r"\b(?:cancel\w*|call(?:ing)? (?:it )?off|called off|drop(?:ping)? out|"
                          r"pull(?:ing)? out|opt(?:ing)? out|back(?:ing)? out)\b", re.I)


def _the_line_cancels(line):
    """True when the line is the person dropping the plan, not only saying they cannot come."""
    return bool(LINE_CANCELS.search(str(line or "")))


def _a_plan_on_the_table(memory):
    """True when one of the last few turns names the thing the person is now dropping.

    Only an earlier line of theirs counts, and only the shape of a plan: a thing they were going
    to ("the party on saturday", "we booked a table for friday"). A chat with no such word in it
    leaves the bare decline to this composer, which is where it does its best work.
    """
    history = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-3:]
    for turn in history:
        said = str(turn.get("user") or "")
        if said and PLAN_ON_THE_TABLE.search(said):
            return True
    return False


def _hesitant_news_before(memory, turns=3):
    """True when one of the last few things the person said was bad news of their own.

    A death in the chat is asked separately (`_in_a_loss_thread`), and this is the rest of it:
    "my wife left me", "i lost my job", "my mum is in hospital". The reader is the composer's own
    (`badnews.reads_as_bad_news`), so the register is right for the news the rest of the bot
    already greets that way, and a plan dropped in that week is answered in it.
    """
    history = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-turns:]
    for turn in history:
        said = str(turn.get("user") or "").lower()
        if said and reads_as_bad_news(said):
            return True
    return False


def _a_hard_week(memory):
    """True when a death or bad news of their own is in the chat in the last few turns.

    One reader for the two places that ask, because the order matters: a plan dropped in that
    week is answered gently (`DECLINED_PLAN_GENTLE`) and stays this module's line, and a plan
    dropped beside a feeling is left to the reader that answered the feeling.
    """
    return bool(_in_a_loss_thread(memory) or _a_loss_recently(memory) or _hesitant_news_before(memory))


def _the_turn_before_was_a_heavy_one(memory, line=""):
    """True when the line before this one was a feeling, a symptom, or a body that is bad.

    "i had a panic attack" then "i cant come" is one thought: the panic is the reason and the plan
    is what it cost them. Answered as a plan dropped it asked somebody mid-panic whether they
    wanted to rearrange it, and the panic card - the words that say it passes and cannot hurt you -
    went missing. Three readers are asked, because the engine files these lines three ways:

    - the bot's own heavy pool, which `bot/modules/chat.py` notes when its reply is the one the
      person got: "im depressed" and "im really struggling" are filed as news, and the note is
      the only thing that knows they were answered as a mood;
    - the engine's reading of that line, for a feeling (`i feel awful`) and for a body
      (`i feel sick`, `my back is bad`, `i had a panic attack`);
    - the composer's own body reader, so a symptom said the plain way counts here too.

    Asked of the line before and never of this one: "i cant come" on its own says nothing about
    how they are, and a plan dropped in an ordinary week keeps the plan's answer.
    """
    # Only a decline that names nothing. "my back is bad" then "cant make it tonight" names the
    # evening, and the plan's own answer - the one that offers to rearrange it - beats the back
    # card said a second time.
    plain = _plain(line) if line else ""
    if plain and not (_a_declined_plan(plain, without_a_thing=True)
                      and not DECLINE_TIME.search(plain)):
        return False
    if not isinstance(memory, dict):
        return False
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    said = str(turns[-1].get("user") or "").strip().lower()
    if not said:
        return False
    try:
        read = understand(said)
    except Exception:  # noqa: BLE001 - a reading that fails is not a reason to take the turn
        read = None
    if isinstance(read, dict) and (
            read.get("intent") in ("question", "ask") or read.get("kind") == "question"):
        # An ask is not a feeling. "how do i stop feeling sick" then "i cant come" is a question
        # followed by a new line, and standing the decline down there answered it with the
        # conflict-advice card ("say what you want to change rather than what they did wrong").
        # Asked before the heavy note, because the bot answers that question with a heavy pool
        # and the note alone would call it a feeling.
        return False
    note = memory.get("heavy_reply")
    if isinstance(note, dict) and note.get("turn") == len(turns) - 1:
        return True
    if reads_like_a_symptom(said) or _the_reason_is_on_the_body(said):
        return True
    if not isinstance(read, dict):
        return False
    if read.get("intent") == "feeling" and (read.get("polarity") or 0) < 0:
        return True
    return bool(read.get("emotion") or read.get("body"))


def _a_declined_plan(clean, without_a_thing=False):
    """True when the line is the person saying they cannot make a plan.

    A friend hears "i cant come" as a plan being dropped, and answers the plan. The reading only
    says yes when the negated ability is about coming or making it and nothing follows but an
    apology, a day, or the thing itself, so every other sense of the same verbs keeps its own
    reply (see `DECLINE_OTHER`).

    `without_a_thing` is for the claim (`TAKES_AS_IT_COMES`), which takes a line off whatever else
    proposed it. Only the lines nothing is likely to answer well are claimed: the bare decline and
    the one with a day in it. A line that names the occasion - "cant come to the party" - is
    claimed by nobody here, because the entry about telling someone you cannot come answers it
    better than this pool can.
    """
    line = " ".join(str(clean or "").replace("\u2019", "'").replace("'", "").strip().split())
    if not line or DECLINE_ASK.match(line) or line.endswith("?"):
        return False
    found = None
    for pattern in (DECLINE_VERB, DECLINE_MUST):
        for match in pattern.finditer(line):
            if DECLINE_ABOUT_THE_BOT.search(line[:match.start()]):
                continue
            found = match
            break
        if found:
            break
    if not found:
        return False
    # "my period is late and i cant come", "the baby is due and i cant come": the reason is the
    # body, and the line has a health answer behind this one.
    if (_the_reason_is_on_the_body(line[:found.start()])
            or _the_reason_is_on_the_body(VERB_PARTICLE.sub(" ", found.group(1)))):
        return False
    tail = DECLINE_AFTER.sub("", found.group(1).strip(" ,.-!?")).strip(" ,.-!?")
    if not tail:
        return True
    # "i cant be there for him" / "for her mum" / "for the birth": being there for somebody is
    # not a plan, and the tail's "for" is what this reading otherwise calls the thing itself.
    if tail.startswith("for ") and DECLINE_BE_THERE.search(line[:found.end(0) - len(found.group(1))].rstrip()):
        return False
    # "i have to cancel" is a plan dropped; "i have to cancel my dentist appointment" is a job, and
    # the entry that cancels one has the answer. Only the plan-shaped tail gets the plan reply.
    if found.re is DECLINE_MUST and not DECLINE_TIME.search(tail):
        return False
    if DECLINE_DATE.search(tail):
        return True
    # A day is a plan whether or not the tail opens with a particle: "i cant come on saturday" is
    # as much a plan as "i cant come on the 14th". The particle keeps its own sense for a thing
    # ("my heating wont come on tonight"), which is why the person has to be in the line.
    if DECLINE_TIME.search(tail):
        if not DECLINE_OTHER.match(tail) or not DECLINE_OTHER_SUBJECT.match(line):
            return True
    if DECLINE_OTHER.match(tail):
        return False
    # The bare plan without a day: "i cant make it", "cant make it im afraid". The claim takes it
    # too, because the other pools read "afraid" as a worry and answer it with "what's one thing
    # you can check", which is not words for somebody dropping an evening.
    if tail in ("it", "there", "along"):
        return True
    # The thing itself: "cant come to the party", "cant make it to sams", "cant come out for it",
    # "cant make the wedding", "cant come on the 14th".
    if without_a_thing:
        return False
    if tail.startswith(("to ", "for ", "it to ", "it on ", "it for ", "it at ", "it next ")):
        return True
    return bool(DECLINE_OCCASION.search(tail))


def _someone_else_dropped_it(clean):
    """True when the plan being dropped is somebody else's, not the person's own.

    The same match `_a_declined_plan` takes, so the two readings can never disagree about which
    "cant come" the line is about: the words in front of it decide who cannot come.
    """
    line = " ".join(str(clean or "").replace("\u2019", "'").replace("'", "").strip().split())
    if not line or not _a_declined_plan(clean):
        return False
    for pattern in (DECLINE_VERB, DECLINE_MUST):
        for match in pattern.finditer(line):
            if DECLINE_ABOUT_THE_BOT.search(line[:match.start()]):
                continue
            return bool(DECLINE_SOMEONE_ELSE.search(line[:match.start()]))
    return False
# Not knowing what to say to somebody is its own ask, and NEUTRAL is the wrong answer to it: "I'm
# listening - say more if it helps" and "Got it. Is there anything you'd like a hand with?" both
# answer as if the person had said nothing, when what they said is that the words will not come.
# The written things have their own entries (a card, a note, a letter, an email) and a death, a
# harm or a loss has its own module, all of them ahead of this file, so what reaches here is a
# person with a conversation to have: the useful reply is one true sentence to open with.
NO_WORDS = re.compile(
    r"\b(?:dont|don't|do not|never|can'?t|cannot|cant)\s+"
    r"(?:ever\s+|really\s+|quite\s+|honestly\s+|know\s+)*what\s+to\s+"
    r"(?:say|tell|text|write to)\b"
    # The same thing said the other way round: the words will not come, without "what to say".
    r"|\b(?:can'?t|cannot|cant|lost|stuck)\s+(?:for|find)\s+"
    # The adjective is part of how people say it ("the right words", "the first words"), and
    # "ive lost my words" is the same line with no find in it.
    r"(?:(?:the|my|his|her|their|any)\s+)?(?:(?:right|first|proper|good)\s+)?words\b|"
    r"\b(?:lost|losing|at a loss for)\s+(?:my|the|his|her|their)\s+words\b|"
    r"\b(?:lost|struggling|struggle)\s+for\s+words\b", re.I)
# The things whose words are already known: a card, a note, a letter, an email, a speech. Those
# have entries of their own and reach this file only when they should not be answered here.
NO_WORDS_NOT = re.compile(
    r"\b(?:card|cards|note|notes|letter|letters|email|emails|speech|toast|eulogy|"
    r"write|writing|written|funeral|death|died|dying|passed away|cancer|hospice|"
    r"miscarriage|stillborn|divorce|wedding|birthday)\b", re.I)
# A talk with somebody named is opened for them, and a talk with a boss, a manager or a landlord
# is opened by saying what the person is asking for: the same "what to say" is two different
# sentences depending on who it is.
NO_WORDS_TO = re.compile(r"\b(?:to|for|about|with|tell|text|txt|ring|call|phone|message)\s+"
                         r"(?:him|her|them|his|their|my|our|the|a)\b", re.I)
# The person can be named without a preposition in front of them: "when she cries", "about my dad",
# "i cant find the words for him". A third-person pronoun anywhere is somebody to talk to, so it
# goes to the same pool - except "my"/"our", which is the speaker's own words, not a person.
NO_WORDS_SHE = re.compile(r"\b(?:him|her|his|hers|them|their|theirs|she|he|they)\b", re.I)
# A doctor, a dentist or a vet is not a heart-to-heart: those are appointments about a trouble, so
# the useful sentence is what to bring up first, not a line about having been thinking it over.
# A group is not the one person an opening line is written for: "to a group of people" and "to an
# audience" would be told to ask how they are today. Nothing here fits that, so it stands down.
NO_WORDS_CROWD = re.compile(r"\b(?:group|audience|crowd|panel|committee|everyone|whole class|"
                            r"room full|assembly|people)\b", re.I)
NO_WORDS_ONE = re.compile(r"\b(?:him|her|his|hers|she|he)\b", re.I)
NO_WORDS_CARE = re.compile(r"\b(?:doctor|doctors|gp|dentist|nurse|consultant|surgeon|specialist|"
                           r"vet|midwife|health visitor|optician|pharmacist|physio|"
                           r"physiotherapist|therapist|counsellor)\b", re.I)
NO_WORDS_ASK = re.compile(r"\b(?:boss|manager|hr|employer|landlord|landlady|client|customer|"
                          r"team|staff|colleague|interview|appraisal|review|landlord)\b", re.I)


def _no_words(clean):
    """The pool for a line that cannot find the words, or None."""
    if not NO_WORDS.search(clean) or NO_WORDS_NOT.search(clean):
        return None
    if NO_WORDS_ASK.search(clean):
        return NO_WORDS_ASKING
    if NO_WORDS_CARE.search(clean):
        return NO_WORDS_AT_THE_CARE
    if NO_WORDS_TO.search(clean) or NO_WORDS_SHE.search(clean):
        if NO_WORDS_CROWD.search(clean) and not NO_WORDS_ONE.search(clean):
            return None
        return NO_WORDS_SOMEONE
    return NO_WORDS_STUCK


# The talk that is the whole invitation: "fancy a chat", "shall we have a natter", "catch up".
INVITE_TALK = re.compile(r"\b(?:chat|talk|natter|chinwag|catch\s*up|a\s+word|gossip)\b", re.I)
# The opener, and the words people start a line with before it ("so", "hey", "right", "just").
INVITE_OPENER = re.compile(
    r"^(?:(?:so|ok|okay|right|well|hey|hi|oi|and|but|oh|ah|anyway|then|now|er|um|hmm|listen|"
    r"quick|just|actually)\s+)*"
    r"(?:(?:do|would|d)\s+(?:you|u)|(?:are|r)\s+(?:you|u)|you|maybe)?\s*"
    r"(?:fancy|want|like|up\s+for|coming|come|join\s+me|walk\s+with\s+me|"
    r"shall\s+we|should\s+we)\b(.*)$", re.I)
# "walk with me" and "join me" are the whole invitation, and "come with me" / "come along" too: the
# company is the ask, so no thing has to follow.
INVITE_COMPANY = re.compile(
    r"^(?:(?:so|ok|okay|right|well|hey|oi|and|but|oh|ah|anyway|then|now|just)\s+)*"
    r"(?:(?:do|would|d)\s+(?:you|u)\s+|(?:are|r)\s+(?:you|u)\s+|you\s+)?"
    r"(?:(?:come|walk|sit)\s+(?:with|along)\b(?:\s*(?:me|us))?|join\s+me\b|"
    r"(?:fancy|want)\s+(?:to\s+)?(?:com(?:e|ing)|tag(?:ging)?)\s+along\b)", re.I)
# The same openers with a question about the world after them are not invitations: "do you want to
# know how it works", "do you want me to ring them", "do you want a lift home".
INVITE_NOT_A_DOING = re.compile(
    r"^(?:know|hear|ask|tell|say|explain|check|bet|guess|see|read|talking|think|be|become|stay|"
    r"leave|go home|try|start|stop|help|mean|happen|me\b|hand|lift|ride|anything|something|"
    r"nothing|a go|a look|a word)\b")
# A tail that only says when, or asks about a time, is arranging rather than inviting.
INVITE_WHEN = re.compile(r"^(?:when|if|whether|whenever|unless)\b")


def _an_invitation(clean):
    """'talk', 'go' or None: which invitation this line is, if it is one."""
    line = " ".join(re.sub(r"[^a-z0-9 ']+", " ", str(clean or "").lower()).split())
    if not line or len(line.split()) < 2:
        return None
    if set(line.split()) & INVITE_NEVER:
        return None
    if INVITE_COMPANY.match(line):
        return "talk" if INVITE_TALK.search(line) else "go"
    found = INVITE_OPENER.match(line)
    if not found:
        return None
    tail = [w for w in found.group(1).split() if w not in INVITE_FILLER]
    if not tail:
        # "do you fancy a coffee tonight" is the same invitation once the time is off it.
        tail = [w for w in found.group(1).split()
                if w not in ("tonight", "today", "tomorrow", "later", "now", "soon", "after")]
    said = " ".join(tail)
    if not tail or INVITE_NOT_A_DOING.match(said) or INVITE_WHEN.match(said):
        return None
    if all(w in INVITE_PRONOUN for w in tail):
        return None
    if not set(tail) & INVITE_ACTIVITY and not INVITE_TALK.search(line):
        return None
    return "talk" if INVITE_TALK.search(line) else "go"
ONLY_FAR = re.compile(
    ONLY_FRONT + r"(?:(?:somewhere|something|some place|a place|a bit|a little|much|quite|really|"
    r"fairly|more|less|not|too|this|that|thats|that's|which is|its|it's|is)\s+)*"
    r"(?:far|near|nearby|nearer|close|closer|local|walkable|in the area|round the corner)"
    r"(?:\s+(?:away|out|by|enough|either|though|from here|to home|from the \w+))?$", re.I)
ONLY_PRICE = re.compile(
    ONLY_FRONT + r"(?:(?:a bit|much|more|a little|something|somewhere|the|ones?)\s+)*"
    r"(?:cheaper|cheap|pricier|dearer|not too (?:expensive|dear|pricey|much)|budget|affordable|"
    r"free|nothing (?:too )?(?:pricey|dear)|"
    r"(?:under|below|less than|no more than|max|maximum|up to|about|around)\s+"
    r"[\u00a3$\u20ac]?\d+\s*(?:pounds?|quid|grand|k|thousand|dollars?|euros?)?"
    r"(?:\s*(?:or so|ish|max|tops))?|"
    r"[\u00a3$\u20ac]?\d+\s*(?:pounds?|quid|grand|max|or so|ish))$", re.I)
ONLY_TIME = re.compile(
    ONLY_FRONT + r"(?:(?:a bit|much|more|a little|something|somewhere|the|ones?)\s+)*"
    r"(?:quick|quickly|quicker|fast|faster|soon|sooner|later|earlier|not long|no time|"
    r"not too long|in a (?:bit|minute|hour|day|week)|in an? \w+|"
    r"an? (?:hour|minute|day|week|moment|min)|(?:under|below|less than) an? (?:hour|minute|day|week|moment|min)|"
    r"(?:under|below|less than|no more than|max|maximum|up to|about|around|in)\s+"
    r"\d+\s*(?:mins?|minutes?|hours?|hrs?)|"
    r"\d+\s*(?:mins?|minutes?|hours?|hrs?)(?:\s*(?:or so|max|tops))?)$", re.I)
ONLY_EFFORT = re.compile(
    ONLY_FRONT + r"(?:(?:a bit|much|more|a little|something|somewhere|the|ones?)\s+)*"
    r"(?:easy|easier|simple|simpler|no fuss|not much fuss|low effort|minimal effort|"
    r"not too much (?:work|effort|faff)|no faff|quick and easy|nothing (?:fiddly|complicated))$",
    re.I)
ONLY_SIZE = re.compile(
    ONLY_FRONT + r"(?:(?:a bit|much|more|a little|something|somewhere|the|ones?)\s+)*"
    r"(?:small|smaller|big|bigger|tiny|compact|roomy|not too (?:big|small|large)|"
    r"on the small side|on the big side)$", re.I)
NARROW_AXES = (("time", ONLY_TIME), ("price", ONLY_PRICE), ("far", ONLY_FAR),
               ("effort", ONLY_EFFORT), ("size", ONLY_SIZE))
# The pools above ask for the bound. That is the right question when the line only says which way to
# cut - "not too far", "cheaper", "quicker" - and the wrong one when the line already carries it:
# "under 20 minutes" after "tuna pasta in 15, a frittata in 20" was answered "How many minutes have
# you got?", and "about 300 pounds" after the October destinations was answered "Cheaper, then.
# What's your limit?" - which asks for a figure the person just gave and asserts a preference they
# never said. A bound in the line is the person answering the question already, so the reply says it
# back and points it at the things on the screen.
BOUND_SAID = re.compile(
    r"\b(?:under|below|less than|no more than|not more than|at most|max|maximum|up to|within|"
    r"about|around|roughly|only)\s+(?:\d|a\b|an\b|one|two|three|five|ten|twenty|thirty|forty|"
    r"fifty|sixty|ninety|a hundred|half)"
    r"|\b\d|\bhalf an hour\b|\ban hour\b|\ba tenner\b|\ba fiver\b|\ba couple of hours\b",
    re.I)


def the_bound_said(clean):
    """The bound the line itself names, said back the way they said it, or ""."""
    line = " ".join(str(clean or "").strip().split())
    found = BOUND_SAID.search(line)
    if not found:
        return ""
    rest = line[found.start():]
    rest = re.sub(r"[^\w\s£$€.,-]", " ", rest).strip(" .,")
    words = rest.split()
    return " ".join(words[:5]).rstrip(" .,")


def reads_as_a_narrowing(clean):
    """The axis this line narrows on, or "" when it is not only a constraint.

    Only a line that is the constraint and nothing else comes here: "not too far" and "under 20
    minutes" are this, and "is it cheaper in june" and "the car is cheap but it needs work" name a
    subject of their own and keep the readers that can answer those.

    Two limits in one line - "cheap and not too far", "not too far and cheap", "under 20 minutes and
    easy" - are read by `the_limits_said`, which puts the part that carries a bound first: a line
    joined by "and" matched neither pattern and was said back ("Got it - cheap and not too far"),
    which gives the person nothing to answer and does not cut the answer above either. This returns
    the first axis of that reading, which is the one the reply starts with.
    """
    limits = the_limits_said(clean)
    return limits[0][0] if limits else ""


# The words that join two limits into one line. A line with a part that is not a limit ("cheap and
# cheerful", "something not too far from the station") is not only a limit, and keeps whatever the
# composers after this one make of it.
NARROW_JOIN = re.compile(r"\s*(?:,|&|\band\b|\bplus\b)\s*", re.I)


def the_limits_said(clean):
    """The limits a line of joined limits names, in the order a reply should try them.

    "cheap and not too far" and "under 500 pounds and not too far" are one line with two limits in
    it, and the reply has to pick one to ask about. The part that carries a bound comes first: the
    person has already answered the question that part asks - "under 500 pounds" - so saying it
    back and pointing it at the things on the screen is the most the reply can do. The other parts
    follow, the last said first, because the limit said last is the one the next answer has to
    meet. The parts are tried in that order against the answer above, and the first one the answer
    can be cut on is the one the reply asks about: "under 500 pounds each and not too far" after
    four destinations that quote no prices is a distance to cut, not a price.

    Returns [(axis, part), ...] and nothing when the line is not only limits - a line with a part
    that is not one ("cheap and cheerful", "something not too far from the station") keeps
    whatever the composers after this one make of it.
    """
    line = " ".join(str(clean or "").strip().split())
    if not line or line.rstrip().endswith("?") or len(line.split()) > NARROW_WORDS:
        return []
    parts = [part for part in NARROW_JOIN.split(line) if part]
    if not parts:
        return []
    axes = [_one_axis(part) for part in parts]
    if not all(axes):
        return []
    with_bound = [(axis, part) for axis, part in zip(axes, parts) if the_bound_said(part)]
    without = [(axis, part) for axis, part in zip(axes, parts) if not the_bound_said(part)]
    return with_bound[::-1] + without[::-1]


def _one_axis(line):
    """The one axis a piece of a line narrows on, or ""."""
    for axis, pattern in NARROW_AXES:
        if pattern.match(line):
            return axis
    return ""


# The answer above has to be about that axis, or the cut asks about a subject the answer never
# raised: "my washing machine is leaking" / "not too far" got "Nearer, then. How far are you happy
# to travel?", and "i cant sleep" / "cheaper" got "Cheaper, then. What's your limit?" Both are
# worse than the bland ack they replaced, because a confident question about the wrong thing is
# worse than a shrug. A procedure has nothing to narrow; an answer that offers things to choose
# between has, and it says so in the axis's own words.
# The answer has to offer the person a cut, and what it offers is a quantity or a bound: "takes 2
# minutes", "a frittata in 20", "£300 to £700", "40 minutes on the train". A word that happens to be
# in the answer is not enough, which is what went wrong the first time: "what helps a headache" /
# "smaller" cut for size because the answer said "a quiet dark room", and "i want to start running"
# / "something easy" cut for effort because the answer said "easy jogging". Neither answer offered
# anything to narrow. A number with its unit is the plainest sign that an answer does.
# The other sign that an answer offered things to choose between, and one that does not need the
# axis's word: it named them. "Cyprus or Crete ... the Canaries ... Seville and Marrakesh" never
# says "travel", and it is plainly a list of places to pick from. Two or more names that are not at
# the start of a sentence is the plainest reading of that, and it leaves a procedure alone, because
# a procedure names nothing to choose between ("Try a warm bath or a glass of milk").
#
# The "or" is what separates a choice from a list of parts. "Cyprus or Crete ... the Canaries ...
# Seville and Marrakesh" offers things to pick between; "the pressure gauge, the thermostat and the
# boiler's reset button" is everything to check on one boiler, and "not too far" after it is not a
# narrowing but a person still talking about a fault. Both list names, and only one of them is
# offering the person a choice, so the reading needs the word a choice is made with.
def _names_things_to_choose(said):
    """True when the answer puts two or more named things in front of the person, to pick from."""
    said = str(said or "")
    if not re.search(r"\bor\b", said, re.I):
        return False        # a list of parts to check ("the gauge, the thermostat and the button")
    words = said.split()
    named = set()
    for index, word in enumerate(words):
        bare = word.strip(".,;:!?*()\u2014-\u2019'\"")
        if len(bare) < 2 or not bare[0].isupper() or not bare[1:].islower():
            continue
        if index == 0:
            continue
        before = words[index - 1].rstrip()
        if before.endswith((".", "!", "?", ":")) and not before.endswith("..."):
            continue      # the first word of a sentence is a capital for grammar, not a name
        named.add(bare)
    return len(named) >= 2


AXIS_SAID = {
    "far": re.compile(r"\b\d+\s*(?:miles?|km)\b"
                      r"|\b(?:nearer|nearby|close by|local|walkable|travel|journey|commute)\b", re.I),
    "price": re.compile(r"[\u00a3$\u20ac]\s?\d|\b\d+\s*(?:pounds?|quid|dollars?|euros?)\b"
                        r"|\b(?:cost|costs|price|prices|budget|afford|spend)\b", re.I),
    "time": re.compile(r"\b\d+\s*(?:min(?:ute)?s?|mins?|hours?|hrs?)\b"
                       r"|\b(?:in|takes?|leave it|for) \d+\b", re.I),
    "effort": re.compile(r"\b(?:easier|simple|simpler|effort|faff|fiddly|elbow grease|hard work)\b",
                         re.I),
    "size": re.compile(r"\b\d+\s*(?:cm|mm|m|inch|inches|ft|feet)\b"
                       r"|\b(?:size|measurements?|width|depth|height|fits?|fitting)\b", re.I),
}
# A fault has nothing to choose between, so a cut after one is the same wrong question: "my boiler
# is broken" / "under 20 minutes" got "Then the short version. How many minutes have you got?" -
# and the boiler answer had already said how long the fix takes. Nothing after a fault is a
# narrowing.
# The words are the ones people use for a thing that has gone wrong, not the names of faults: "keeps
# cutting out", "very slow", "dies by lunchtime" and "freezes" are as much a fault as "broken", and
# each was a cut that asked a worried person about their holiday.
A_FAULT = re.compile(
    r"\b(?:broken|leaking|leaks|leaked|wont|won't|stopped|jam(?:med)?|stuck|blocked|"
    r"smells?|smelling|dripping|drips|dead|fault|faulty|error|blinking|not working|"
    r"isn't working|isnt working|no hot water|no power|tripping|cracked|crack|smashed|dented|"
    r"damaged|torn|ripped|soaked|flooded|not charging|wont charge|seized|"
    r"cutting out|cuts out|cut out|keeps (?:stopping|dying|cutting|freezing|restarting|turning off)"
    r"|dies|dying|freezes|freezing|frozen|sluggish|laggy|super slow|very slow|too slow|so slow"
    r"|slow(?:ed)? (?:down|up)|rattl\w+|noisy|clogged|gunked|corroded|rusty|worn out|"
    r"keeps (?:flashing|beeping|going off)|flashing|beeping|overheating|too hot|smoking|sparking)\b",
    re.I)


def the_answer_to_cut(memory, axis=""):
    """The answer still on the screen, or {} when the turn above is not one to narrow.

    A question from the bot is not an answer to narrow ("what have you tried so far?" then "not
    too far" is the person answering it), and neither is a loss or anything a person said about
    themselves: those threads are held by the modules that opened them.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return {}
    last = turns[-1]
    if not isinstance(last, dict) or last.get("module") not in NARROW_ANSWERED:
        return {}
    said = last.get("bot")
    if not isinstance(said, str) or len(said.split()) < NARROW_SUBSTANCE:
        return {}
    if said.rstrip().endswith("?"):
        return {}
    if axis:
        raised = AXIS_SAID.get(axis, re.compile(r"(?!)")).findall(said)
        if len(raised) < AXIS_MIN.get(axis, 1) and not _names_things_to_choose(said):
            return {}       # the answer never raised the axis the line narrows on
    if A_FAULT.search(str(last.get("user") or "")):
        return {}       # a fault is not a list of things to choose between
    return last


# The laughter itself, not the word "funny": a bare "funny" is either the joke module's ask
# ("my son said something funny") or a doubt ("funny that the bus never came"), and neither is a
# laugh to answer with a laugh.
LAUGHING = re.compile(
    r"\b(?:laugh(?:ed|s|ing)?|laughter|giggl(?:e|ed|es|ing)|in stitches|"
    r"cracked (?:me|us) up|crackin(?:g)? (?:me|us) up|hilarious|hysterical|"
    r"(?:can'?t|cant|couldn'?t|couldnt) (?:stop|help) laughing|"
    r"wet (?:myself|himself|herself) laughing|"
    r"had (?:a|such a|a right|a proper|the best) laugh|bit of a laugh|"
    r"so funny|funniest thing)\b", re.I)
# Not every mention of a laugh is a laugh at something good: being laughed at is a bad day, and
# "it is not funny" is the person saying the opposite of the pool's line.
# Being laughed at is being mocked, and the object is rarely "me": "she laughed at my hair",
# "they laughed at my name", "the class laughed at my drawing" were all answered with a laugh
# back, which is the bot joining in. Any possessive or person after the at is the same shape, and
# so is "he laughed when i fell over", where the laugh is at the accident rather than with them.
LAUGHING_AT = re.compile(
    r"\b(?:laugh(?:s|ed|ing)?|giggl(?:e|es|ed|ing)|snigger\w*|snicker\w*|titter\w*|"
    r"a laugh)\s+(?:at|about)\s+(?:me|us|him|her|them|you|my|his|her|their|our|your)\b"
    r"|\b(?:laugh(?:s|ed|ing)?|giggl(?:e|es|ed|ing))\s+(?:when|after|because)\s+i\b"
    r"|\bnot (?:even |that |remotely )?funny\b|"
    # "nobody laughed" is the same fault as "she laughed at my hair": the laugh did not happen,
    # and a line about it happened is what the person is telling the bot.
    r"\b(?:nobody|no one|no-one|nobodys|no ones)(?:'s)? (?:is |was |did |has )?"
    r"(?:laughing|laughed|laugh)\b|\bno laughing matter\b"
    # A laugh that is wanted rather than had: "we could do with a laugh" and "i need a laugh"
    # are asking for one, and answering as if the day had been funny misses the ask.
    r"|\b(?:could do with|could use|needs?|needed|want(?:s|ed)?|in need of|short of) "
    r"(?:a|a bit of a|a good|a right) laugh\b"
    # The person about themselves: "im so funny" names no thing that was funny, so there is
    # nothing for "what set it off?" to be about.
    r"|\bi(?:'m|m| am)\b\s+(?:so |really |very |quite |well |proper )*funny\b", re.I)

FLAT_LINE = re.compile(r"^\W*" + FLAT_LEAD + FLAT_CORE + r"\W*$")
REACTION_LEAD += r"but|ok|okay|bloody|hell|damn|fucking)\s+)*"
REACTION_LINE = re.compile(
    r"^\W*" + REACTION_LEAD + r"(?:" + REACTION_WORD + r")"
    r"(?:[\s,]+(?:and\s+)?" + REACTION_WORD + r"){0,6}\W*$")
# What makes the line a reaction rather than a line made of the same small words. The pool is the
# first signature that is in it, so "oh no, that sucks" is sympathy and "oh no" is the mishap.
REACTION_SIGNS = (
    (REACTION_RELIEF, re.compile(
        r"\b(?:phew|finally|thank (?:god|goodness|heavens|christ|fuck))\b")),
    # A swear is a wince at something that happened, not a mishap of the bot's own: "i lost my
    # job today" / "dammit" was answered "Whoops. What happened?", which is the pool for a spill.
    (REACTION_OUCH, re.compile(
        r"\b(?:ouch\w*|ow+|yikes|eek|oof|yowch|sucks|brutal|awful|terrible|horrible|rough|"
        r"dammit|damn it|bugger|crap|shoot)\b")),
    (REACTION_MISHAP, re.compile(
        r"\b(?:oops|whoops|oh (?:no|dear)|dear me)\b")),
    (REACTION_DISBELIEF, re.compile(
        r"\b(?:seriously|are you serious|you(?:'?re| are)? (?:joking|kidding)|for real|no way|"
        r"no chance|surely|really|honestly|wtf|what the (?:hell|heck|devil|fuck|blazes|dickens)|"
        r"what (?:on|in) (?:earth|the world)|why (?:on|in) (?:earth|the world)|"
        r"get out|you what|"
        r"come on|wow+|woah|whoa|omg|oh my (?:god|word)|blimey|crikey)\b")),
    (REACTION_REPEAT, re.compile(r"\b(?:huh|eh|pardon)\b")),
)


def _the_person_already_said_it(memory):
    """True when the last thing the person said was the story the reaction is reacting to."""
    said = str(last_user(memory) or "").strip()
    if not said or said.rstrip().endswith("?"):
        return False
    return len(said.split()) >= 4


# A miscarriage is a loss the grief reading does not hold ("i had a miscarriage" is not a death in
# its words), and it is the shape the deck row that started this guard is.
BABY_LOSS = re.compile(r"\bmiscarriage(?:s)?\b(?! of justice)|\bmiscarried\b|\bstillborn\b"
                       r"|\bstillbirth\b", re.IGNORECASE)


def _a_care_thread_to_leave_alone(memory):
    """True when the bot's last answer was care, so a reaction is not news it has not heard.

    A reaction is answered by asking what happened, which is right for "oh no the boiler again" /
    "yikes" and wrong inside a bereavement: "i had a miscarriage" / "ouch" was answered with
    "Yikes. That sounds rough - what happened?" over a care reply that had just asked who is
    around them this week. The reading is the one the grief and loss pools use, so a reaction
    after a death, a loss or a crisis stays with the person instead of starting again.
    """
    if _in_a_care_thread(memory) or _in_sudden_loss_thread(memory) or _in_a_loss_thread(memory):
        return True
    return any(baby_loss(said) for said in _the_last_few_lines(memory))


def _the_last_few_lines(memory):
    """The person's own last few lines, as the thread left them."""
    return [" ".join(str(turn.get("user") or "").lower().split())
            for turn in [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-4:]
            if str(turn.get("user") or "").strip()]


def baby_loss(clean):
    return bool(BABY_LOSS.search(str(clean or "")))


# Only the words that are a verdict on their own. "what a day" and "what a week" are left out on
# purpose: those two are the rough-day reading chat already has, and a pool that asks what
# happened is the wrong question to a person who has just said the week was long.
VERDICT_SAID = re.compile(
    r"^\W*" + _VERDICT_LEAD + _VERDICT_DET + r"(?P<noun>" + VERDICT_BAD + r")\b" +
    # A word said after the verdict belongs to it ("what a nightmare honestly"), and it is a
    # closed list, so "what a mess at the office" is still a line with a subject in it.
    r"(?:\s+(?:honestly|really|though|today|now|again|here|seriously|mate|man))*\W*$")
# The words people type with nothing in front of them at all: "nightmare", "a nightmare". Only
# the strong ones, because a bare "pain" is more often where it hurts and a bare "state" is not a
# verdict anybody types alone.
VERDICT_BARE = re.compile(
    r"^\W*" + _VERDICT_LEAD + r"(?:a|an|the|right|proper|absolute|total|complete|right old)?\s*"
    r"(?P<noun>nightmare|mess|disaster|shambles|farce|palaver|shower)\W*$")


# A verdict on the thing before it is a verdict on what the bot has just said, and when that was a
# joke the person asked for, "what a joke" is them rating the joke. Read as a verdict on something
# that happened to them, it got sympathy: "tell me a joke" / "what a joke" was answered "Ouch.
# Sorry, that sounds rough." - the bot sympathising with its own punchline, where the joke entry
# used to tell another one. The request is read with the narrow shape chat.py's `JOKE_ASK` reads,
# because "joke" is in "my mate made a joke about my dad" too, and only a request makes the answer
# above a punchline.
JOKE_WANTED = re.compile(
    r"\b(?:tell|say|make|give|got|know|another|more|one more)\b[^.]{0,24}"
    r"\b(?:joke|jokes|pun|puns|funny|riddle|limerick|meme)\b|"
    r"\bmake me laugh\b|\bcheer me up\b|\banything funny\b|\bjoke please\b", re.I)


# A line that asks the jokes to stop ("dont make jokes about my mum", "no more puns") names one
# without wanting one, and the answer above it was not a punchline.
JOKE_UNWANTED = re.compile(r"\b(?:dont|don't|do not|stop|no more|enough|pack it in)\b")


def _the_answer_above_was_a_joke(memory):
    """True when the person's own last line asked for a joke, so the answer above was one."""
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    if not turns:
        return False
    asked = " ".join(str(turns[-1].get("user") or "").lower().split())
    if JOKE_UNWANTED.search(asked):
        return False
    return bool(JOKE_WANTED.search(asked))


def _a_verdict_line(text, memory=None):
    """The pool for a line that is only a verdict on the thing before it, or None."""
    text = " ".join(str(text or "").lower().split())
    found = VERDICT_SAID.match(text)
    if not (found or VERDICT_BARE.match(text)):
        return None
    # Only the word "joke" is the person rating the punchline: "what a mess" or "what a state"
    # said to a bot that has just told a joke is still a verdict on something else, and standing
    # down on those handed the line to the search hedge.
    if found and found.group("noun") == "joke" and memory is not None \
            and _the_answer_above_was_a_joke(memory):
        # The thing before it was the bot's own punchline, so this is the person's opinion of it,
        # and the turn goes back to the entry that told the joke.
        return None
    return REACTION_OUCH

# A verdict about the situation takes the turn; a verdict about a thing the person named does
# not. "it was rubbish" after "we went to spain six weeks ago" is chat's line ("Shame about
# Spain"), and "its not fair" has a pool of chat's own, so the past tense is read as a thing and
# the bare/shouted words are the reading here. See `reads_as_a_verdict`.
VERDICT_LINE = re.compile(
    r"^\W*(?:(?:that|thats|that'?s|this|it|it'?s|how|so|very|really|bloody|just)\s+"
    r"(?:is\s+)?)?(?:" + VERDICT_WORD + r")"
    r"(?:\W+(?:isnt\s+it|innit|though|honestly|really|mate|god|ugh))?\W*$"
    r"|^\W*(?:it|it'?s|that|thats|that'?s|this)\s+(?:is\s+)?"
    r"(?:rubbish|pants|crap|a\s+nightmare|a\s+mess|a\s+joke)"
    r"(?:\W+(?:isnt\s+it|innit|though|honestly|really|mate))?\W*$"
    r"|^\W*(?:typical(?:\s+(?:isnt\s+it|innit|that|again|honestly))?|just\s+my\s+luck|"
    r"that\s+figures|figures|sod'?s\s+law|of\s+course\s+it\s+(?:did|was|is)|"
    r"what\s+a\s+(?:pain|hassle|shame|nightmare|joke|mess|headache|letdown))\W*$")
# The news a rough verdict lands on: the person's own body or sleep, not a thing that broke.
# The words are read off the line the verdict is about, so "my landlord wont fix the boiler" and
# "our move got pushed back" are none of them - they are news about a thing and a plan.
STATE_ABOVE = re.compile(
    r"\b(?:can'?t\s+sleep|cant\s+sleep|not\s+sleeping|no\s+sleep|keep\s+waking|"
    r"hurts?|hurting|ache|aches|aching|sore|in\s+pain|pain\s+in|"
    r"ill|sick|poorly|a\s+temperature|migraine|dizzy|shaking|shivery|"
    r"no\s+energy|worn\s+out|exhausted|knackered|burnt?\s+out)\b")


def a_death_just_said(memory=None):
    """True when the news the verdict lands on is a death, not a hard week or a diagnosis.

    The difference matters for the wording: a diagnosis or a fall can be asked about, and a
    friend does, but the turn after a death is not a question.
    """
    for turn in [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)][-2:]:
        line = " ".join(str(turn.get("user") or "").lower().split())
        if not line:
            continue
        try:
            if loss.reads_as_loss(line):
                return True
        except Exception:  # noqa: BLE001 - a reading that cannot run claims nothing
            continue
    return False


def a_verdict_on_the_person(memory=None):
    """True when the verdict is landing on a state of the person rather than on news.

    Read from the person's own line a turn or two back, the same shape as `a_heavy_verdict`.
    """
    for turn in [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)][-2:]:
        line = " ".join(str(turn.get("user") or "").lower().split())
        if line and STATE_ABOVE.search(line):
            return True
    return False


# The news those two pools are for, read off the person's own line the same way the heavier
# readings are. Only these alternatives of `HEAVY_NEWS` are here: a diagnosis, a hospital and a
# leaving are in neither list and keep the sympathy pool above.
WAITING_NEWS = re.compile(
    r"\b(?:wait(?:ing)?\s+(?:\w+\s+){0,4}(?:weeks|months)|on\s+a\s+waiting\s+list|"
    r"months?\s+for\s+(?:the\s+|an\s+|a\s+)?(?:appointment|scan|referral|operation))\b")
JOB_GONE_NEWS = re.compile(
    r"\b(?:lost\s+my\s+(?:job|work|hours)|laid\s+off|made\s+redundant|been\s+(?:sacked|"
    r"fired)|got\s+(?:sacked|fired|let\s+go)|sacked\s+(?:from|on)|let\s+go\s+from)\b")


def _the_last_two_lines(memory=None):
    """The person's own lines for this turn and the one before - never the bot's wording."""
    lines = []
    for turn in [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)][-2:]:
        line = " ".join(str(turn.get("user") or "").lower().split())
        if line:
            lines.append(line)
    return lines


def _a_loss_in_the_same_breath(memory=None, lines=()):
    """True when the heavier news is there too, so the middle pools must stand aside.

    A queue is not the whole story when the same line carries the thing being waited on: "waiting
    to hear if my dad pulled through" is not a wait to be asked about, and a redundancy that came
    with a diagnosis is a diagnosis.
    """
    if a_death_just_said(memory) or a_heavy_verdict(memory):
        return True
    for line in lines:
        if HEAVY_ABOVE.search(line):
            return True
        try:
            if (badnews.reads_as_sudden_loss(line) or badnews.reads_as_the_leaving(line)
                    or loss.reads_as_loss(line)):
                return True
        except Exception:  # noqa: BLE001 - a reading that cannot run claims nothing
            continue
    return False


def a_wait_with_no_loss(memory=None):
    """True when the heavy news is a queue rather than a person lost."""
    lines = _the_last_two_lines(memory)
    if not any(WAITING_NEWS.search(line) for line in lines):
        return False
    return not _a_loss_in_the_same_breath(memory, lines)


def a_setback_with_no_loss(memory=None):
    """True when the heavy news is a job gone rather than a person lost."""
    lines = _the_last_two_lines(memory)
    if not any(JOB_GONE_NEWS.search(line) for line in lines):
        return False
    return not _a_loss_in_the_same_breath(memory, lines)


def _the_heavy_pool(memory=None):
    """The pool for a verdict on news with no repair in it: a loss, a queue or a setback."""
    if a_death_just_said(memory):
        return VERDICT_NUMB
    if a_wait_with_no_loss(memory):
        return VERDICT_QUEUE
    if a_setback_with_no_loss(memory):
        return VERDICT_SETBACK
    return VERDICT_HEAVY
# The line above a verdict that makes it a heavy one: missing somebody, in tears, worn down by
# a loss that is still being carried. Not a death said out loud (that stands the verdict down
# whole, `a_verdict_stands_down`), but the turn after the death, and the crying that has no
# event in it yet.
GRIEF_ABOVE = re.compile(
    r"\b(?:miss(?:es|ed|ing)?\s+(?:my|his|her|their|our|you|them|him|her|mum|dad|mother|father|"
    r"sister|brother|son|daughter|nan|grandma|grandad|gran|grandpa|friend)|"
    r"crying|cry(?:ing)?\s+(?:myself|a lot)|can'?t\s+stop\s+crying|keep\s+crying|"
    r"griev(?:e|ing)|bereave\w*|heartbroken|wish\s+(?:he|she|they)\s+(?:was|were)\s+(?:still\s+)?"
    r"here|empty\s+without|lonely\s+without|still\s+can'?t\s+believe\s+(?:he|she|they)\s+"
    r"(?:has|have)\s+gone)\b")


def a_heavy_verdict(memory=None):
    """True when the verdict is landing on grief rather than on news.

    Read from the person's own line a turn or two back, the same shape as the demonstrable
    readings (`a_verdict_stands_down`), because the bot's wording for the turn before is not the
    thing being judged: "i miss my mum" was answered by chat's own comfort line, and the verdict
    the person brings next is still about the missing.
    """
    for turn in [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)][-2:]:
        line = " ".join(str(turn.get("user") or "").lower().split())
        if line and GRIEF_ABOVE.search(line):
            return True
    return False


# The thread is not in the past yet: "my wife is having a miscarriage right now" is not a grief
# line to be asked about, it is a thing happening while they type.
HAPPENING_NOW = re.compile(
    r"\b(?:right\s+now|just\s+now|as\s+we\s+speak|this\s+minute|right\s+this\s+minute|"
    r"happening\s+now|is\s+having\s+it|are\s+having\s+it|still\s+going\s+on|"
    r"in\s+the\s+next\s+hour|on\s+my\s+way\s+to\s+the\s+hospital)\b")


def a_happening_now(memory=None):
    """True when the thing above is still going on, so a sympathy line is not the turn."""
    for turn in [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)][-2:]:
        line = " ".join(str(turn.get("user") or "").lower().split())
        if line and HAPPENING_NOW.search(line):
            return True
    return False


# A verdict points back at something: the news the person brought, or the answer the bot just
# gave. It is read from the words where the words say so on their own ("thats annoying", "such a
# pain", "how annoying") and from the conversation where they do not ("a nightmare", "typical"
# as the whole of the line). Without a turn before it there is nothing it is a verdict on: a bare
# "a nightmare" as the first line of a chat was answered "Annoying. Is it a quick fix or a whole
# thing?" instead of the floor (crisp-jackal on #5479).
VERDICT_POINTS_BACK = re.compile(
    r"^\W*(?:that|thats|that'?s|this|it|it'?s|how|what\s+a|such\s+a|of\s+course\s+it)\b")


def _a_verdict_on_something(text, memory):
    """True when there is a turn for this verdict to be about.

    A verdict is a comment, so it needs the thing it comments on: the news the person brought a
    turn ago, or the answer the bot gave after it. A demonstrative carries its own subject
    ("thats annoying" is about what was just said), so those stand whatever the conversation has
    in it; the bare sayings only count once the conversation has a turn in it.
    """
    if VERDICT_POINTS_BACK.match(text):
        return True
    try:
        turns = (memory or {}).get("turns") or []
    except Exception:  # noqa: BLE001 - a conversation that cannot be read has no turn in it
        return False
    return any(isinstance(turn, dict) for turn in turns)


def _verdict_pool(clean, memory=None):
    """The pool for a verdict on the news, or None when the line is anything more."""
    text = " ".join(str(clean or "").lower().split())
    if not text or not VERDICT_LINE.match(text) or "?" in text:
        return None
    if memory is not None and not _a_verdict_on_something(text, memory):
        return None
    # A verdict with nothing before it is the whole turn: the person is reacting to the day, not to
    # an answer, and every light pool line asks about the news ("Is it a quick fix or a whole
    # thing?" of nothing). The reaction pool is what main answered with, and it is right - "Ouch.
    # What happened?" - so the pool stands down and the reaction takes the turn
    # (steward-frank-chicken on #5479, who was reading a red test on main).
    if isinstance(memory, dict):
        turns = memory.get("turns") or []
        if not any(isinstance(turn, dict) for turn in turns):
            return None
    if re.search(r"\b(?:shame|letdown)\b", text):
        return VERDICT_SHAME
    if re.search(r"\b(?:typical|figures|luck|law|of course)\b", text):
        return VERDICT_LUCK
    if a_verdict_on_the_person(memory):
        return VERDICT_ROUGH
    return VERDICT_ANNOY


def a_heavy_news(memory=None):
    """True when the news the verdict lands on has no repair in it.

    Read from the person's own line a turn or two back, like the readings beside it: the bot's
    wording for the turn before is not what is being judged.
    """
    for turn in [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)][-2:]:
        line = " ".join(str(turn.get("user") or "").lower().split())
        if not line:
            continue
        if HEAVY_NEWS.search(line):
            return True
        try:
            if badnews.reads_as_the_leaving(line):
                return True
        except Exception:  # noqa: BLE001 - a reading that cannot run claims nothing
            continue
    return False


def a_loss_in_the_thread(memory=None):
    """True when the news the verdict lands on is a death, a diagnosis or a baby lost.

    Only those are answered with `VERDICT_HEAVY`. The accident reading (`HARD_WEEK`) used to be in
    here too, which put a washing machine in a bereavement line: a bare "broken" matched it, so
    "my washing machine is broken" then "what a pain" got "That sounds like it has been sitting
    with you a while" (crisp-jackal on #5479). An accident's news is light enough for the light
    pools or for the answer the person already has, and `a_verdict_stands_down` still keeps a
    verdict out of a thread that is not light.
    """
    if a_heavy_verdict(memory) or a_heavy_news(memory):
        return True
    try:
        if _in_a_loss_thread(memory) or _grief_thread(memory):
            return True
    except Exception:  # noqa: BLE001 - a thread that cannot be read claims nothing
        return False
    for turn in [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)][-2:]:
        line = " ".join(str(turn.get("user") or "").lower().split())
        if not line:
            continue
        if HEAVY_ABOVE.search(line):
            return True
        try:
            if badnews.reads_as_sudden_loss(line):
                return True
        except Exception:  # noqa: BLE001 - a reading that cannot run claims nothing
            continue
    return False


def a_verdict_stands_down(memory=None):
    """True when this thread is one a light verdict must not answer.

    A verdict is a light turn, and three threads are not light: a live emergency ("my husband hit
    me" then "thats annoying" is still that thread - the bot's continuation is the turn), a
    bereavement or a hard week ("my mum died last week" then "thats a shame" is not a light
    verdict, and the shame pool asked "What went wrong?"), and a thread the bot has already been
    careful about. The reading stands down for the whole thread rather than for a list of its
    words, the same way `_a_verdict` does for a good verdict in a hard week.
    """
    if not memory:
        return False
    try:
        if in_a_safety_thread(memory) or _in_a_loss_thread(memory) or _grief_thread(memory):
            return True
    except Exception:  # noqa: BLE001 - a thread that cannot be read claims nothing
        return False
    # An accident, an operation, a body in trouble a turn ago: the same hard week `_a_verdict`
    # stands down for, minus the general bad news. A line of bad news (an eviction, a sacking) is
    # a light verdict's proper place - "Annoying, that. Is it sorted?" is the reply to it - while
    # a death or a fall is not.
    # A diagnosis and a baby lost are the same hard week as a death, and a list of accidents does
    # not hold them: "i have cancer" then "what a nightmare" was answered with "Annoying. Is it a
    # quick fix or a whole thing?", and "my wife is having a miscarriage right now" then "thats a
    # shame" with "Gutted for you. Do you want to talk it through?". The readings exist
    # (`HEAVY_ABOVE` holds the diagnoses, `badnews.reads_as_sudden_loss` the baby and the suicide)
    # and a job or a rent rise is in neither, so an eviction keeps its verdict.
    for turn in [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-2:]:
        line = " ".join(str(turn.get("user") or "").lower().split())
        if not line:
            continue
        if HARD_WEEK.search(line) or HEAVY_ABOVE.search(line):
            return True
        try:
            if badnews.reads_as_sudden_loss(line):
                return True
        except Exception:  # noqa: BLE001 - a reading that cannot run claims nothing
            continue
    return False


def reads_as_a_verdict(text, memory=None):
    """True when the whole line is a verdict on the news, for the arbiter's routing.

    A verdict has no subject of its own, so the topic the conversation is on must not stand in
    for it: "thats annoying" after a cooking answer is not a question about cooking, and it was
    answered with a recipe.
    """
    try:
        return _verdict_pool(text, memory) is not None
    except Exception:  # noqa: BLE001 - a reading that cannot run just claims nothing
        return False


# The verdict shapes a person opens with, which is a longer list than the verdicts the pools above
# take: a first line has no subject anywhere in the chat, so a reaction word is the whole of what
# the bot has to go on. "thats tough going" was the commonest line tawny-donkey found reaching the
# intake form on main (#routing 82965).
FIRST_TURN_VERDICT = re.compile(
    r"^\W*(?:(?:that|thats|that'?s|this|it|it'?s|how|what\s+a)\s+"
    r"(?:is\s+|was\s+)?(?:so\s+|very\s+|really\s+|bloody\s+|just\s+|proper\s+)?"
    r"(?:tough|hard|rough|grim|annoying|a\s+pain|a\s+shame|a\s+nightmare|a\s+hassle|"
    r"a\s+joke|a\s+mess|frustrating|rubbish|sad|depressing|draining|exhausting|"
    r"a\s+slog|a\s+grind|a\s+bummer))"
    r"(?:\s+(?:going|innit|though|honestly|really|mate|god|ugh|isnt\s+it))?\W*$"
    r"|^\W*(?:typical(?:\s+(?:isnt\s+it|innit|again|honestly))?|just\s+my\s+luck|"
    r"that\s+figures|figures|bloody\s+hell|what\s+a\s+(?:pain|hassle|shame|nightmare|"
    r"joke|mess|headache|letdown))\W*$")


def _reaction_pool(clean, memory=None):
    """The pool for a bare reaction, or None when the line is anything more than one."""
    text = " ".join(str(clean or "").lower().split())
    # Before the reaction grammar, because the verdict shapes are not made of reaction words.
    verdict = _a_verdict_line(text, memory)
    if verdict:
        return verdict
    # A verdict with no turn before it: the pool above needs something to point back at, and
    # standing the verdict down whole left the intake form underneath it. The shape is read here
    # rather than by widening `VERDICT_WORD`, because a verdict inside a thread belongs to the
    # pools above ("thats tough going" after a hard week has chat's "Fair enough. What has been
    # the hardest bit?"), and only the first-turn case is unclaimed.
    if FIRST_TURN_VERDICT.match(text) and not ((memory or {}).get("turns") or []):
        return VERDICT_FIRST
    if not text or not REACTION_LINE.match(text):
        return None
    for pool, sign in REACTION_SIGNS:
        if sign.search(text):
            return pool
    if re.fullmatch(r"[\w']*\s*(?:what|pardon)\W*", text):
        # "what?" is the person asking for the last answer again, so there has to be one: on an
        # empty conversation "I'll put it another way - what bit was unclear?" answers nothing.
        if memory is not None and not last_bot(memory):
            return REACTION_REPEAT_FIRST
        return REACTION_REPEAT
    return None
def reaction_line(text, memory=None):
    """The composer's own line for a verdict on the thing before it, or None.

    The whole line is the verdict, so the reply is the reaction back. A topic entry can still
    take the turn on a word of it - the knowledge base's advice for dreams answered a bare
    "nightmare" - and where that happens the loss is the entry's to avoid; this says what the
    composer would have said on the line, so the fault can be measured turn by turn.
    """
    memory = memory if isinstance(memory, dict) else {}
    clean = " ".join(str(text or "").lower().split())
    pool = _a_verdict_line(clean, memory)
    if not pool:
        return None
    if _a_care_thread_to_leave_alone(memory):
        pool = REACTIONS_CARE
    elif _the_person_already_said_it(memory):
        pool = REACTIONS_SAID.get(pool, pool)
    return _choose(pool, memory, clean)


# The apology in front, with the small words people put before it.
_SORRY_LEAD = re.compile(
    r"^\W*(?:(?:oh|and|but|so|yeah|yep|ok|okay|well|hi|hey|right|alright|also)\W+)*"
    r"(?:(?:so|very|really)\s+)?(?:sorry|apologies|apologise)\b")


# Being late is not a job under way: "im running late for work" was read off the verb as a thing
# in the middle ("im painting my kitchen") and answered "Nice - is it the messy bit yet?" at
# somebody rushing to get in. A lateness report has one useful reply - say it now, with the time
# you will be there - and the question back is about the holding up, which is the part they can
# talk about while they move. Only the speaker's own lateness: "its too late", "my period is
# late" and "the train was late" are different lines.
LATE_NOW = re.compile(
    r"\b(?:i'm|im|i am|i'll|ill|i will)\s+((?:so\s+|really\s+|a bit\s+|a little\s+|still\s+|"
    r"definitely\s+|probably\s+|going to be\s+|gonna be\s+|will be\s+|running\s+|be\s+|b\s+)*)"
    r"(?:late|behind)\b"
    r"|^\s*late(?: again)?\b")
# "im not late" and "im never late" are the opposite report, and the word that says so sits between
# the speaker and it: the guard reads only that stretch, so "i'm late and i've not eaten" is still
# a lateness. "we're late" is about a group of people including whoever they are answering to, so
# it is not the speaker's own report either.
LATE_NOT_IT = re.compile(r"\b(?:not|never|n't)\b")
# A period that has not come is not a person running behind, and "im late for my period" would take
# the pool ahead of the health card that reads it.
LATE_NOT_A_TIME = re.compile(r"\b(?:period|periods|pregnan\w*)\b")
# "im late again, what do i say to my boss" is a request for the words, and the late-for-work card
# has them: the pool is for the report, not for the ask on top of it.
LATE_ASKS = re.compile(
    r"\b(?:what|how|should i|do i|can i|shall i|what do i say|what should i say|tell my|"
    r"explain|apolog\w*)\b")
DONE_SUBJECT = re.compile(r"\b(?:i|we)\s+(?:just\s+|also\s+|finally\s+|only\s+|actually\s+)?"
                          r"([a-z]+)\b")
# A report is a finished sentence. "cleaned the kitchen" is news; "cleaned the kitchen what about
# the oven" is news and a question, and the question is the turn the person asked for - chat-speak
# drops the question mark, so the "?" test alone let every one of these through and the cheer took
# the turn away from the answer that was there ("cleaned the kitchen what about the oven" lost the
# oven paste, "booked the hotel is it refundable" the refund answer). The asks are named rather
# than guessed, because a bare "what" is also in a plain report ("painted the fence what colour
# she wanted").
# The other second half is a grumble, and a grumble is the turn: "cleaned it and now it smells" is
# a person with a problem, not a person reporting a job well done. Only the negative states, so
# "cleaned the kitchen and now it looks lovely" keeps the cheer.
TAIL_GRUMBLE = re.compile(
    r"\bnow (?:it|they|that)\b[^.!?]{0,20}?\b(?:smells?|stinks?|worse|broken|leaking|mouldy|"
    r"moldy|damp|still|not)\b", re.I)
# The third second half is a problem, and it is the turn too: "paid the deposit and the landlord
# says its not showing" is a person with a deposit, not a person reporting a job well done, and
# the same for "booked the hotel and then found it cheaper". TAIL_GRUMBLE reads a state that
# changed ("now it smells"), and these say it as a sentence of somebody else's or as a find, so
# the trouble words are read wherever they sit: the trouble is the tail.
TAIL_TROUBLE = re.compile(
    r"\b(?:says?|said|told\s+me|tells\s+me|reckons?|claims?|because)\b[^.!?]{0,30}?\b(?:not|never|"
    r"no|wont|won't|cant|can't|couldnt|couldn't|refus\w*|wrong|missing|lost|broken|damaged|"
    r"cheaper|expensive|late|still|again|failed)\b"
    r"|\bfound\s+(?:it|them|that|out)\b[^.!?]{0,24}?\b(?:cheaper|expensive|broken|wrong|"
    r"damaged|dirty|damp|missing|late|cancelled|canceled|cracked|faulty|empty)\b"
    r"|\b(?:is|was|were|are|isnt|isn't|wasnt|wasn't)\s+(?:not\s+|never\s+)?(?:showing|shown|"
    r"arrived|arriving|working|registered|covered|paid|come\s+through|turned\s+up)\b[^.!?]{0,16}?"
    r"\b(?:not|never|no|still|yet|nothing)\b"
    r"|\b(?:didnt|didn't|hasnt|hasn't|hadnt|hadn't|never)\s+(?:show|shown|arrive|work|come|"
    r"register|turn\s+up|pay|go\s+through)\b", re.I)
# The same fault in its plainest form: the second half is a complaint and the complaint has no
# shape to name - "sorted the boiler service and now the radiators are cold", "cancelled the gym
# and they still took the money", "paid the deposit and its not showing on my account". The tail
# after the joining word is the whole test: a complaint word in it means the person is not
# reporting a job well done, whatever the first half said. Kept to the plain words so a report
# that ends in praise ("painted the fence and it looks brilliant") still gets the cheer.
TAIL_JOIN = re.compile(r"\b(?:and|then|but|so|because)\b")
TAIL_COMPLAINT = re.compile(
    r"\b(?:not|never|still|yet|again|cold|leaking|dripping|damp|mouldy|moldy|smelly|smells|"
    r"stinks|blocked|stuck|broken|broke|faulty|cracked|dirty|empty|flat|dead|late|slow|"
    r"missing|lost|wrong|worse|cancelled|canceled|refused)\b")
TAIL_ASK = re.compile(
    r"\b(?:what about|what next|what now|what else|how long|how much|how do i|how can i|how should i|"
    r"can i|could i|should i|shall i|do i|does it|will it|will they|is it|is that|are they|"
    r"was it|was that|where do i|when will|when do i|when should|who do i|any idea|any chance|"
    r"do you know|do you think|is there|are there)\b", re.I)


def _a_thing_done(clean):
    """True when the line reports a small thing the person did, which nothing else answers."""
    return _thing_done_shape(clean) is not None


def _thing_done_shape(clean):
    """Just the shape: see `_thing_done_scan`."""
    return _thing_done_scan(clean)[0]


def _thing_done_pool(clean):
    """The pool for a thing done, or None when the line is not one.

    Chosen by the verb and never by the noun: a thing seen to, a thing bought, a walk, and the
    rest of the made things, because the question a friend asks depends on which of those it was.
    """
    # A slip of the person's own is not a thing done. "i made a daft mistake at work" and "made a
    # stupid mistake today" have the shape of an afternoon - a past tense and something after it -
    # so the pool asked how it had gone: "What made you start on that?", "Nice - how did it go?".
    # The noun that carries the meaning is further along than the words after the verb, so the
    # thing-done reading cannot see it and the confession reader already does: `fallback_chain`
    # answers it with "That's the kind of thing that sits on you. Do you want to talk it
    # through?", and this only stands aside so that reader gets the turn. Imported here because
    # the two modules import each other at the end of the file.
    from .fallback_chain import _a_thing_they_regret
    if _a_thing_they_regret(clean):
        return None
    shape, done_verb = _thing_done_scan(clean)
    if not shape:
        return None
    if shape == "going":
        return A_THING_ON
    if shape in ("soon", "at"):
        # Not done yet: a question about how it went is a question about nothing.
        return A_THING_AHEAD
    if done_verb in GONE_VERB:
        return A_THING_GONE
    if done_verb in BOUGHT_VERB:
        if ALIVE.intersection(clean.split()):
            return None
        if NOT_CHOSEN.intersection(clean.split()):
            # A repeat prescription is not a purchase to weigh up: nobody weighs up which one to
            # go for, they are given it. "Good - was it straightforward?" is the question a
            # friend asks, and it is the same one the seen-to pool asks of a job.
            return A_THING_SEEN_TO
        return A_THING_BOUGHT
    if done_verb in SEEN_TO_VERB:
        return A_THING_SEEN_TO
    return A_THING_DONE


HARM_AFTER = re.compile(
    r"\b(?:my|his|her|their|the)\s+(?:\w+\s+)?(?:back|knee|knees|shoulder|shoulders|hip|hips|"
    r"ankle|ankles|foot|feet|leg|legs|arm|arms|wrist|hand|hands|chest|stomach|head|neck|"
    r"shin|calf|thigh|elbow|joint|joints|body)\b[^.!?]{0,14}?\bis (?:much |a lot |now )?"
    r"(?:worse|sore|stiff|swollen|aching|playing up)\b")


def _tail_complains(clean):
    """True when the clause after the joining word is a complaint, not a report.

    "sorted the boiler service and now the radiators are cold" is a person with cold radiators
    and the service is only how the line starts, so the tail is what they are telling the bot.
    The last word of the test is deliberately narrow: only the plain complaint words, so
    "painted the fence and it looks brilliant" keeps the cheer.
    """
    joins = list(TAIL_JOIN.finditer(clean))
    if not joins:
        return False
    return bool(TAIL_COMPLAINT.search(clean[joins[0].end():]))


def _thing_done_scan(clean):
    """(shape, verb) for this line, or (None, "") when it is not a thing done.

    The shape is "done" for a finished thing ("i painted the fence today") and "going" for one
    still under way ("i've been painting the fence all morning"); the verb is the one the shape
    was read from, because the pool depends on it ("how do you feel now it's finished?" fits a
    fence and not a walk).

    A question is not a report ("did you paint the fence"), and a "but" turns the line into a
    mixed one the pools for trouble and feeling answer better. So does a negative word: "i
    cleaned the kitchen but it looks the same" is a grumble, not news.
    """
    if ("?" in clean or " but " in clean or TAIL_ASK.search(clean)
            or TAIL_GRUMBLE.search(clean) or TAIL_TROUBLE.search(clean)
            or _tail_complains(clean)):
        return None, ""
    if (clean.split() or [""])[0] in QUESTION_OPENERS:
        return None, ""
    if NEGATIVE_LINE.search(clean):
        return None, ""
    # A complaint tacked onto the doing is not news: "i went to the gym and my knee is killing me"
    # wants the question about the knee, and "i did yoga and my back is worse" was not a good
    # afternoon. trouble.py already reads one, so it keeps the turn; the second gate is only for
    # the "is worse" shape, which names no harm word at all.
    if trouble.reads_as_trouble(clean, tuple(re.findall(r"[a-z']+", clean)), clean):
        return None, ""
    if HARM_AFTER.search(clean):
        return None, ""
    if HARM_NAMED.search(clean) or HARM_ON_ME.search(clean):
        return None, ""
    # A job with something wrong at the end of it is not an afternoon well spent: "im decorating
    # and the fumes are making me dizzy", "im tiling and ive run out of tiles". Neither is a
    # complaint about the job ("its a nightmare", "its taking forever"): the cheerful question
    # ("Nice one - nearly there?") reads as if the bot had not heard the rest of the line.
    if FEELING_OFF.search(clean) or A_TROUBLE_IN_THE_TAIL.search(clean):
        return None, ""
    # "ive been painting the fence all morning" is the same afternoon as "i've been painting the
    # fence all morning", and only the apostrophe was read: the shape has to be read off a line
    # with the contraction spelled out.
    text = re.sub(r"\b(?:ive|i've)\b", "i have", clean)
    text = re.sub(r"\b(?:weve|we've)\b", "we have", text)
    text = re.sub(r"\b(i|we)'d\b", r"\1 had", text)
    words = re.findall(r"[a-z']+", text)
    for i in range(len(words) - 1):
        if words[i] not in ("i", "we"):
            continue
        j = i + 1
        while j < len(words) and words[j] in ("just", "also", "finally", "only", "actually",
                                              "have", "had", "been"):
            j += 1
        if j >= len(words) or words[j] not in DONE_VERB:
            continue
        rest = words[j + 1:j + 3]
        if any(w in DONE_NOT_THIS for w in rest):
            return None, ""
        if (words[j] in DONE_ONLY_A_THING
                and any(w in DONE_NOT_A_PERSON for w in words[j + 1:j + 4])):
            return None, ""
        return "done", words[j]
    # Chat-speak drops the pronoun: "booked the hotel last night", "paid the deposit", "cancelled
    # the gym" are the same report with no "i" in it. The subject was the only thing the reading
    # wanted, so every one of them was answered as a request for instructions - "booked the hotel
    # last night" got the choose-a-hotel card, "cleaned the kitchen" the clean-a-kitchen one - or
    # with the neutral nod. Every word in DONE_VERB is a past tense, so a line that opens on one is
    # a report and not an instruction ("clean the kitchen" is the instruction, and it is not in the
    # list): that is the whole of the fence, and it is why the shape is read off the verb's form
    # rather than off a list of what a person might report.
    if words and words[0] in DONE_VERB and not HARM_ANYWHERE.search(clean):
        rest = words[1:3]
        if not any(w in DONE_NOT_THIS for w in rest):
            return "done", words[0]
    # A day's doing is not always said with the verb of the doing: "i went for a run", "i went to
    # the gym", "i did a workout", "i went swimming". Reading only DONE_VERB left every one of
    # those with "I'm listening", and "i went for a run this morning" was the only one that got a
    # question, from a different arm. The verb of going or doing says nothing on its own - "i went
    # home", "i went to the doctor", "i did the washing up" are not an afternoon's work - so the
    # object is what has to be in the list.
    went = WENT_AT_IT.search(text)
    if went:
        return "gone", "went"
    did = DID_AT_IT.search(text)
    if did:
        return "gone", "did"
    spent = SPENT_TIME.search(text)
    if spent and spent.group(1) in DONE_ING:
        return "going", spent.group(1)
    been = BEEN_AT_IT.search(text)
    if been and been.group(1) in DONE_ING and TIME_SPAN.search(text):
        return "going", been.group(1)
    at_it = AT_IT.search(text)
    if at_it and (at_it.group(1) in DONE_ING or at_it.group(1) in AT_IT_EXTRA):
        rest = text[at_it.end():]
        # "im getting fat" is a state, not a job under way: see BECOMING in fallback_data.
        if at_it.group(1) in BECOMING and (rest.split() or [""])[0] in BECOMING_STATE:
            return None, ""
        if (_a_thing_after(rest) and not HABIT_TIME.search(rest)
                and not any(word in AT_IT_NOT for word in re.findall(r"[a-z']+", rest))):
            return ("soon" if FUTURE_TIME.search(rest) else "at"), at_it.group(1)
    return None, ""


# The verbs of going and doing need their object, because the verb alone is every day: "i went to
# the doctor", "i went home", "i did the washing up". The object names the thing done, so the
# object is what is in the list. "went to my first yoga class" has words between the preposition
# and the noun, hence the gap.
WENT_AT_IT = re.compile(
    r"\b(?:i|we)\s+(?:just\s+|also\s+|finally\s+|only\s+|actually\s+)?"
    r"(?:have\s+|had\s+|'ve\s+)?went\s+(?:"
    r"for\s+(?:a\s+|an\s+|my\s+|our\s+|the\s+)?(?:run|walk|swim|cycle|ride|hike|jog|"
    r"long\s+walk|length\s+swim|bike\s+ride|day\s+out)\b"
    r"|(?:swimming|running|cycling|walking|hiking|jogging|rambling|shopping)\b"
    r"|to\s+(?:\w+\s+){0,3}?(?:gym|pool|parkrun|class|classes|yoga|pilates|zumba|sauna|"
    r"climbing)\b"
    r")")
# "i did a workout", "i did yoga", "i did my exercises": the same afternoon with "did" in front.
DID_AT_IT = re.compile(
    r"\b(?:i|we)\s+(?:just\s+|also\s+|finally\s+|only\s+|actually\s+)?did\s+"
    r"(?:a\s+|an\s+|my\s+|our\s+|the\s+|some\s+|two\s+|three\s+)?"
    r"(?:workout|workouts?|run|session|class|swim|laps?|lengths?|weights|press[- ]?ups|"
    r"yoga|pilates|exercises?|exercise|stretches|set\s+of\s+\w+|\d+\s?k(?:m)?|km|miles?)\b")

# A job said as it is being done, with no time span: "im painting my kitchen", "we're tiling the
# bathroom", "im sorting out the garage". The person is telling you what their day is, and the
# neutral nod ("I'm listening - say more if it helps") answers that as if they had said nothing.
# The verb carries it, so "im going to the gym" and "im thinking of painting it" are not this: the
# first is a plan of its own and the second has not started.
FUTURE_TIME = re.compile(
    r"\b(?:today|tomorrow|tonight|later|next\s+(?:week|weekend|month|year|saturday|sunday|monday|"
    r"tuesday|wednesday|thursday|friday)|this\s+(?:weekend|week|evening|afternoon|morning)|"
    r"on\s+(?:saturday|sunday|monday|tuesday|wednesday|thursday|friday))\b")
AT_IT = re.compile(r"\b(?:i'm|im|i am|we're|we are)\s+(?:just\s+|currently\s+|still\s+|now\s+"
                   r"|in the middle of\s+)?(?:re)?([a-z]+ing)\b")
# A repeating thing is not a job under way: "i'm doing a yoga class every week" is a habit the
# memory store says back, and "how long have you got left?" is asked of a fence, not of a class
# that comes round again on Tuesday.
HABIT_TIME = re.compile(
    r"\b(?:every|each)\s+(?:day|week|month|year|morning|evening|weekend|night|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
    r"|\b(?:once|twice|three times|four times|\d+ times)\s+a\s+(?:day|week|month|year)\b")


# Something wrong at the end of a job, or coming off it: the cheerful question is for an
# afternoon well spent and reads as deaf on one of these. The words are the ones people use for a
# job that is not going well, and they say nothing about a job that is ("im painting the hall and
# its going ok" keeps its question).
A_TROUBLE_IN_THE_TAIL = re.compile(
    r"\b(?:ran out|run out|run short|havent got|hasnt got|haven't got|hasn't got|so far behind|"
    r"stuck|nightmare|disaster|forever|taking ages|taking so long|drag(?:ging|ged) on|"
    r"junk|clutter|chaos|a mess|in a mess|messy|wont go|wont fit|doesnt fit|dont fit|"
    r"gone wrong|went wrong|broke|broken|snapped|hate it|hate this|give up|giving up|"
    r"struggling|too much for me|killing me|a pain|hard work|no idea what i)\b")
# How a body says a job has gone too far, in words that are not about the job at all: the fumes,
# the dizziness. A line with one of these in it is answered by the safety and trouble readers.
FEELING_OFF = re.compile(
    r"\b(?:dizzy|light-?headed|fumes|faint(?:ed|ing)?|bleeding|nauseous|throwing up|"
    r"cant breathe|can't breathe|blurred vision|heart racing)\b")


def _a_thing_after(rest):
    """True when the words after the verb name the thing the person is working on."""
    return any(word not in THING_AFTER and len(word) > 2
               for word in re.findall(r"[a-z']+", rest))


# The same afternoon said with the time span instead of the finished verb: "i spent the morning
# repainting the kitchen", "i've been sorting the photos all afternoon". The verb is still the
# thing that decides it, so "i spent the morning at the hospital" stays as it was.
SPENT_TIME = re.compile(r"\b(?:i|we)\s+spent\s+(?:the\s+|all\s+|most of the\s+|my\s+|our\s+)?"
                        r"(?:morning|afternoon|evening|day|weekend)\s+(?:re)?([a-z]+ing)\b")
BEEN_AT_IT = re.compile(r"\b(?:i|we)\s+(?:have\s+|had\s+|'ve\s+)?been\s+(?:re)?([a-z]+ing)\b")
TIME_SPAN = re.compile(r"\b(?:all (?:morning|afternoon|evening|day|weekend)|most of the "
                       r"(?:morning|afternoon|day|evening)|since (?:breakfast|lunch|this morning)|"
                       r"the (?:morning|afternoon|evening) away)\b")


def _done_ing():
    """The "-ing" forms of DONE_VERB, which is how the same afternoon is said with a time span."""
    out = set()
    for verb in DONE_VERB:
        stem = verb[:-2] if verb.endswith("ed") else verb
        out.add(stem + "ing")
        out.add(verb + "ing")
        if len(stem) > 2:
            out.add(stem + stem[-1] + "ing")
    out.update(("running", "swimming", "making", "writing", "cutting", "digging", "hanging",
                "building", "sweeping", "freezing", "sitting", "getting", "decorating",
                "repainting", "reorganising", "reorganizing"))
    return frozenset(out)


DONE_ING = _done_ing()

# Words that make the line a grumble rather than a thing done, so the question ("how did it go")
# would be the wrong shape for it.
# A cheerful question is for an afternoon well spent, not for harm. "i washed down two packets of
# pills" and "i chopped my finger" are a done verb with nothing in DONE_NOT_THIS to stop them, so
# the cheerful pool asked an overdose "are you pleased with it?". Nothing after a verb says it was
# harm, so the words that name harm stop the shape outright and the safety arm keeps the turn.
HARM_NAMED = re.compile(
    r"\b(?:pills?|tablets?|paracetamol|ibuprofen|painkillers?|meds|medication|overdosed?|"
    r"dose|wound|blood|bleeding|bled|bleach|ammonia|antifreeze|poison\w*)\b")
# A person who says they hurt themselves is never having a day that went neither way, and the
# cheerful day pool ("Good to hear. What was the best bit?") is the worst reply the bot could give
# it. `HARM_ON_ME` below needs a body part, so the ordinary case is caught by the safety band and
# the figurative one was not: "i cut myself from society" was congratulated, while its own sibling
# "i cut myself off from everyone" is answered by the friendship reading. Read by shape, so every
# wording of it stands the day question down - and "i cut myself a slice", "i cut myself some
# slack" give the person something rather than take it, so those are not this.
A_HURT_MYSELF = re.compile(
    r"\b(?:i|i've|ive)\b\s*(?:just\s+|almost\s+|nearly\s+|really\s+|actually\s+)?"
    r"(?:cut|cutting|hurt|hurting|harm|harmed|harming|burn|burned|burnt|burning|hit|hitting|"
    r"punish|punished|punishing|starve|starved|starving|poison|poisoned|poisoning)\s+myself\b"
    # "i cut myself a slice", "i cut myself some slack" hand the person something rather than take
    # it, so a quantity in front of the object means this is not that.
    r"(?!\s+(?:a|an|the|some|another|either|neither|one|two|three)\b)")
# The verb alone is not enough - "i chopped the onions", "i burnt the toast" are a supper - so a
# verb of harm only counts when the line says it landed on the person.
HARM_ON_ME = re.compile(
    r"\b(?:chopped|sliced|cut|stabbed|burned|burnt|scalded|slashed|gashed|split|hit|knocked|"
    # the same harm said while it is happening, which is how a person types it: "im cutting my
    # finger" was congratulated ("Nice one - nearly there, or still in the middle of it?") because
    # the -ing forms of these verbs are in DONE_ING and only the past tense was fenced.
    r"chopping|slicing|cutting|stabbing|burning|scalding|slashing|gashing)\b"
    r"[^.!?]{0,20}?\b(?:my|myself)\b[^.!?]{0,16}?"
    r"\b(?:finger|fingers|thumb|hand|hands|arm|arms|leg|legs|foot|feet|toe|toes|wrist|head|"
    r"eye|eyes|knee|face|shoulder|skin|chest|stomach)\b"
    r"|\bi\s+(?:chopped|sliced|cut|stabbed|burned|burnt|scalded|slashed|gashed)\s+myself\b")

KNOCK_ON_ME = re.compile(
    # "i hit my thumb with a hammer", "i dropped a tin on my foot"
    r"\bi\s+(?:just\s+|already\s+|then\s+|also\s+)?(?:hit|dropped|knocked|banged|stubbed|"
    r"trapped|caught|whacked|smashed|slammed|clonked|smacked|bashed|pinched|nipped|grazed|"
    r"scraped|trod|stood)\b[^.!?]{0,26}?\b(?:my|myself)\b[^.!?]{0,18}?"
    r"\b(?:" + KNOCKED_SPOTS + r")\b"
    # "i got my finger stuck in the drawer", "i got my hand caught in the door". Said the other
    # way round from the verb, so the first branch never saw it - and "stuck my finger" on its own
    # is left out on purpose, because "i stuck my foot in it" and "i stuck my neck out" are not
    # knocks on either.
    r"|\bi\s+(?:got|had)\s+(?:my|a)\s+(?:" + KNOCKED_SPOTS + r")\s+"
    r"(?:stuck|caught|trapped|nipped|slammed|squashed|crushed)\b"
    # "i shut my finger in the door", "i slammed my hand in the drawer"
    r"|\bi\s+(?:shut|slammed|squashed|crushed)\s+my\s+(?:" + KNOCKED_SPOTS + r")\s+in\b")
# A whole day on your feet is not a knock on them, and a line about the coming days is a plan
# ("i'll be on my feet all day"), so a span of time in the line stands the pool down.
A_SPAN_OF_TIME = re.compile(
    r"\b(?:all\s+(?:day|morning|afternoon|evening|week)|for\s+(?:hours|a\s+while|days)|"
    r"hours|again|every\s+day|tomorrow|next\s+week)\b")


def _a_knock_on_oneself(clean):
    """True for a knock the person did to their own body, with nothing else in the line."""
    if not clean or "?" in clean or " but " in clean:
        return False
    if not KNOCK_ON_ME.search(clean):
        return False
    return not A_SPAN_OF_TIME.search(clean)

# The same knock with no part of the body named in it - "i walked into a door frame", "i walked
# straight into a table", "i ran into the gate" - is the shape the thing-done scan reads as a walk
# ("walked" is a verb of going), so the person got "What made you start on that?", a question
# about a job they had begun, for walking into a door. There is no spot to put ice on, so these
# get the reaction and a question back, and nothing about a task. The verbs are the ones a person
# travels on their own feet: "i drove into a wall" is a car into a wall and may be somebody hurt
# in it, and "does it hurt to put weight on it" is not the reading for that.
WALKED_INTO = re.compile(
    r"\bi\s+(?:just\s+|then\s+)?(?:walked|ran|stepped|bumped|crashed)\s+"
    r"(?:straight\s+|smack\s+|right\s+|bang\s+|head\s+)?(?:into|against|over)\s+"
    r"(?:a|the|my|our)\s+(?:door|doorway|door\s?frame|frame|table|chair|bed|cot|cupboard|wall|"
    r"shelf|shelves|desk|fridge|freezer|sofa|gate|fence|cabinet|worktop|dresser|sideboard|"
    r"stairs|stair|banister|post|beam|radiator|window)\b")


def _a_knock_into_a_thing(clean):
    """True for walking or bumping into a piece of furniture, with no body part named."""
    if not clean or "?" in clean or " but " in clean:
        return False
    return bool(WALKED_INTO.search(clean))


# A body word or a harm word anywhere makes the line the careful reading's: "washed the cut with
# soap" is a care line and not a thing done, and "mowed the lawn and now my back hurts" is the
# back. Read off the whole line rather than off the verb, because the verb forms this shape reads
# are past tenses, and a past tense in front of a hurt is the story of the hurt.
HARM_ANYWHERE = re.compile(
    r"\b(?:back|backs|knee|knees|shoulder|shoulders|hip|hips|ankle|ankles|foot|feet|leg|legs|"
    r"arm|arms|wrist|wrists|hand|hands|chest|stomach|head|neck|thigh|elbow|elbows|joint|joints|"
    r"skin|cut|cuts|wound|wounds|burn|burns|burnt|scab|scabs|graze|grazes|bruise|bruises|"
    r"blister|blisters|blood|bleeding|bled|pain|pains|ache|aches|aching|hurts?|hurting|"
    r"throbbing|swollen|swelling)\b")
# A mishap: something that landed on a person, said as the account of a day rather than as a
# question. None of these lines has a harm word in it and most name no body part, so neither
# HARM_NAMED nor HARM_ANYWHERE sees them, and the composer's pleasantry took the turn: "i stepped
# on a nail in the garden" was asked what the best bit of it was, "i got glass in my foot" was told
# "nice one", "my baby rolled off the bed" got "how did the rest of it go", and "my vision has gone
# in my left eye" was told "sounds alright, anything good in it?". The cheer is the worst reply in
# the file on those turns, so the reading has two jobs: keep the day question off them, and ask the
# one question a friend asks - how bad it is.
#
# Who fell is a person, so the fall has to have one in front of it: "the shelf fell down", "my
# phone fell in the sink" and "the fence blew over" are things going wrong in a house, and the
# repair pools answer those. The names are the ones the whole file uses for the people a line can
# be about, so a new relation word is added in one place.
FALLEN_PEOPLE = (
    r"i|we|he|she|they|the\s+(?:baby|child|kid|boy|girl|little\s+one|toddler|old\s+lady|old\s+man)|"
    r"(?:my|our|his|her|their)\s+(?:mum|mom|mam|dad|father|mother|son|daughter|child|kid|boy|girl|"
    r"baby|toddler|husband|wife|partner|boyfriend|girlfriend|brother|sister|nan|nana|gran|granny|"
    r"grandad|grandpa|grandma|grandmother|grandfather|cousin|friend|mate|neighbour|neighbor|"
    r"uncle|aunt|nephew|niece|little\s+one|lad|lass)"
    # "my 6 month old fell", "the 18 month old rolled off the sofa": an age in place of a
    # name, which is how a parent types it
    r"|(?:my|our|his|her|their|the)\s+\d+\s*(?:month|week|year)s?\s*old")
# The fall itself needs somewhere to land, which is also what keeps the idioms out without
# listing them: "fell asleep", "fell out with her", "fell in love" and "fell behind at work" have
# no surface after the verb.
MISHAP_FELL = re.compile(
    r"\b(?:" + FALLEN_PEOPLE + r")\b[^.?!]{0,24}?\b(?:fell|rolled|tumbled|toppled|tripped|"
    r"slipped|went|come|came)\s+(?:(?:right|straight|back|clean|smack|flat|head)\s+)?"
    # (a fall has a surface, and it comes straight after the verb: "we fell owt over money" is
    # the dialect for "fell out over money" and must not be read as a fall)
    r"(?:over|off|down|from|onto|into|through|out\s+of|on\s+the|down\s+the|off\s+the)\b"
    # "i fell on the stairs", "fell on the ice": the surface named is a floor rather than a piece
    # of furniture, because "i fell asleep on the sofa" and "fell in the bath" (asleep again) name
    # the same prepositions and are the day, not the mishap.
    r"|\b(?:" + FALLEN_PEOPLE + r")\b[^.?!]{0,24}?\b(?:fell|rolled|tumbled|tripped|slipped|"
    r"went)\s+on\s+the\s+(?:stairs|stair|steps|ice|pavement|paving|kerb|curb|path|floor|"
    r"ground|road|decking|tiles|lino|linoleum|concrete|gravel|deck)\b"
    r"|\b(?:" + FALLEN_PEOPLE + r")\b[^.?!]{0,18}?\bhad\s+a\s+(?:bad\s+|nasty\s+|really\s+)?"
    r"(?:fall|tumble|trip)\b"
    # "my 6 month old fell", "she fell" with nothing after the verb: a fall with no surface named
    # is still a fall when the line ends there, and the idioms all carry a word after the verb
    # ("fell out with", "fell in love", "fell behind", "fell through") or a place to sleep ("fell
    # asleep", "fell over laughing").
    r"|\b(?:" + FALLEN_PEOPLE + r")\b[^.?!]{0,18}?\bfell\b(?=\s*(?:[.,!]|$|and\b|but\b))")
# Something sharp underfoot or in the hand. The thing named is what makes it a body line, because
# "i stepped on the scales" and "stood on the platform" are an errand.
MISHAP_UNDERFOOT = re.compile(
    r"\bi\b[^.?!]{0,20}?\b(?:stepped|stood|trod|walked|planted|knelt)\b[^.?!]{0,6}?"
    r"\b(?:on|in(?:to)?)\b[^.?!]{0,6}?"
    r"(?:a|an|some|the|broken|bits\s+of|a\s+bit\s+of|two)\s+(?:nail|nails|glass|needle|needles|"
    r"lego|thorn|thorns|screw|screws|tack|tacks|pin|pins|shard|shards|spike|spikes|drawing\s+pin|"
    r"sharp\s+thing|rusty\s+nail)\b"
    r"|\b(?:got|had)\s+(?:a\s+)?(?:bit\s+of\s+|piece\s+of\s+|shard\s+of\s+)?(?:glass|grit|"
    r"metal|a\s+nail|a\s+thorn)\s+(?:in|into)\s+my\b"
    r"|\b(?:a\s+)?(?:nail|screw|thorn|needle|splinter|bit\s+of\s+glass)\s+(?:went\s+|stuck\s+)?"
    r"(?:through|in(?:to)?)\s+my\b")
# A sense that has gone. No harm word names these, and a line about going blind in one eye is the
# last thing that can be answered "sounds alright".
SENSE_GONE = re.compile(
    r"\bmy\s+(?:vision|sight|hearing)\s+(?:has\s+|had\s+|suddenly\s+)?(?:gone|went)\b"
    r"|\b(?:went|gone|going)\s+(?:blind|deaf)\b"
    r"|\b(?:cant|cannot|can'?t)\s+see\s+(?:out\s+of|anything\s+out\s+of)\b")
MISHAP_ANYWHERE = re.compile(
    "|".join(("(?:" + MISHAP_FELL.pattern + ")",
              "(?:" + MISHAP_UNDERFOOT.pattern + ")",
              "(?:" + SENSE_GONE.pattern + ")")))


# A mishap that is over, or that never happened. "i fell off the roof last summer", "i nearly fell
# off the ladder", "my dad fell off a ladder but hes ok": the person is telling the story of a
# thing that is finished, and "how bad is it" asks about a fall that is not happening. The day
# question is the right one on those turns, so this reading steps out of the way.
MISHAP_OVER = re.compile(
    r"\b(?:last\s+(?:year|summer|winter|spring|autumn|christmas|month)|years?\s+ago|"
    r"when\s+i\s+was|as\s+a\s+(?:kid|child|teen|youngster|little\s+one)|used\s+to|"
    r"back\s+in\s+(?:the\s+)?(?:day|\d{4}|nineteen|twenty))\b"
    r"|\b(?:nearly|almost|close\s+to)\b"
    r"|\b(?:but|and|though)\s+(?:he|she|they|it|we|i)\s*(?:'?s|re|is|was|were|am)?\s*"
    r"(?:ok|okay|alright|all\s+right|fine)\b"
    # "i tripped over my words on the call": the verb is the trip, the thing is not a floor
    r"|\b(?:over|on)\s+(?:my|his|her|their|our|your|the)\s+(?:own\s+)?(?:words|tongue)\b")


def _a_mishap_to_ask_about(text):
    """A mishap that no card answered, the day question has to leave alone.

    A fall already over is not one: "i fell off the roof last summer", "i nearly fell off the
    ladder" and "my dad fell off a ladder but hes ok" are the account of a day, and the question
    about the day is right on those turns. A sense that has gone is the exception in the other
    direction - "my vision has gone in my left eye" is not a day with anything good in it, even
    though no pool asks how bad it is.
    """
    if SENSE_GONE.search(text):
        return True
    if not MISHAP_ANYWHERE.search(text):
        return False
    return not MISHAP_OVER.search(text)


def _a_mishap(clean, words):
    """True for a mishap said as an account of the day, with a question back for it.

    Only the two shapes with a landing in them ask "how bad is it": a fall and something sharp
    underfoot. A sense that has gone is the careful reading's, and asking somebody how bad their
    eyesight is when it went this morning is not the question - it is the turn above that answers
    that one.
    """
    if not clean or "?" in clean or len(words) > 24:
        return False
    if MISHAP_OVER.search(clean):
        return False
    return bool(MISHAP_FELL.search(clean) or MISHAP_UNDERFOOT.search(clean))


NEGATIVE_LINE = re.compile(
    r"\b(?:ruined|wasted|broke|broken|failed|went wrong|couldn'?t|couldnt|didn'?t|didnt|"
    r"forgot|messed|gave up|hate[sd]?|awful|terrible|useless|a waste|nobody|no one|"
    r"horrib\w*|miserab\w*|dreadful|soaked|drenched|freezing)\b")


NOT_ENOUGH = re.compile(
    rf"\b{MYSELF}\s+(?:am\s+)?(?:just\s+|still\s+|really\s+|always\s+)?(?:not|never)\s+"
    rf"(?:\w+\s+){{0,2}}(?:enough|good enough)\b"
    rf"|\bmy (?:{MY_DOING})\s+(?:is|was|isnt|isn'?t|wasnt|wasn'?t)?\s*"
    rf"(?:just\s+|never\s+|still\s+|always\s+)?(?:not\s+)?(?:good\s+)?enough\b"
    r"|\bfeel (?:like )?(?:im|i'?m|i am)?\s*(?:a )?(?:failure|fraud|useless|a waste|"
    r"letting (?:people|everyone|my family) down)"
    r"|\b(?:im|i'?m|i am)\s+(?:such\s+)?(?:a failure|a fraud|useless|a burden|a waste of space)\b"
    r"|\b(?:letting|never there for) (?:people|everyone|my family|everybody) down\b"
    r"|\bbehind (?:everyone|in life|on everything)\b"
    r"|\bwasting my (?:life|time|twenties|thirties|20s|30s)\b"
    # Keeping up is about the person only where what they are behind on is a thing to be
    # judged on. "i cant keep up with the washing" is a pile of washing, not a standard anyone
    # set for them, so the thing has to be named.
    r"|\b(?:cant|cannot|can'?t) keep up (?:at|in) (?:work|school|uni|university|college|class|"
    r"my course|my job|my studies)\b"
    r"|\b(?:cant|cannot|can'?t) keep up with (?:everything|it all|the lot|the work|everyone|"
    r"my classmates|the others)\b"
    r"|\b(?:cant|cannot|can'?t) (?:cope|do this anymore)\b")
NO_DIRECTION = re.compile(
    # Not knowing what you want is a direction question whatever follows: "i still dont know
    # what i want to do", "i dont know what i want out of work".
    r"\b(?:dont|don'?t|never)\s+know what (?:i\s+)?want\b(?=\s*(?:to do\b|with my life|"
    r"out of|from (?:life|work|mine)\b|$))"
    # Not knowing what to do is only the same thing when the line names the direction it is
    # lost in. A bare "i dont know what to do" after a broken boiler, a lost job or a landlord
    # who will not fix the heating is the ordinary way of saying the thing beat them, and the
    # nod that offers a hand is the honest reply to it.
    r"|\b(?:dont|don'?t|never)\s+know what to do\b(?=\s*(?:with my life|with myself|out of|"
    r"from (?:life|work|mine)\b|with the rest of it\b))"
    r"|\b(?:dont|don'?t|never)\s+know what (?:im|i'?m|i am) (?:doing|supposed to be doing)\b"
    r"|\bno idea what (?:im|i'?m|i am) doing\b"
    r"|\b(?:im|i'?m|i am) \d{2} and i (?:still )?(?:dont|don'?t) know\b"
    r"|\b(?:nothing|no plan|no idea) (?:feels|seems) right\b")
# The lost-at-sea line that is written as a question. `_own_feeling` refuses a question, which
# is right for "what should i do with my life", and this is the one shape where the person is
# not asking the bot anything.
LOST_QUESTION = re.compile(
    r"\bwhat (?:am i|im|i'?m) (?:even )?(?:doing|going to do|going to do with myself) with my "
    r"(?:life|time|day|week|twenties|thirties)\b")
# Another person's trouble is not the speaker's own feeling ("my mum says she isnt good enough"),
# and a question is not a statement about how things are.
NOT_SELF = re.compile(r"\b(?:he|she|they|him|her|them|his|their|my (?:mum|mom|dad|boss|son|"
                      r"daughter|partner|husband|wife|friend|sister|brother|colleague|manager))\b")


# A stated dislike with nothing under it to object to - "i hate presenting", "i cant stand
# cats", "i dont like cooking" - is a taste, not news, so every reading above stands down and
# the memory store files it: ack says the line back as "Noted: you hate presenting." That is a
# receipt for a sentence rather than a reply to it, and the coldest line in this file, and it
# ends the conversation: the person has named a thing they cannot bear and the bot has said
# nothing about it. `obstacle` answers the dislike that objects to an answer it was just given
# ("i hate exercise" after the plan); with no answer under it, the one part this file can still
# do is ask about the thing, which is what a friend does with "i hate presenting" - the thing is
# their own words and the question is about them, so it is not a stock line.
#
# The thing has to be short and one thing: "i hate my job but it pays well" is a grievance with
# two halves, and "i cant stand the way my sister talks to me" is about somebody's behaviour,
# both of which the readings above answer better than a question about the whole clause.
DISLIKE_ASKS = (
    "What is it about {thing} that gets you?",
    "Fair enough. What is it about {thing}?",
    "What is it about {thing} you don't like?",
    "{Thing} \u2014 what is it that gets you about it?",
)
DISLIKE_TOO_LONG = 6
DISLIKE_HAS_TWO_HALVES = re.compile(r"\b(?:and|but|because|so|though|although|when|if)\b", re.I)
# Words that hang off the thing rather than name it: "i hate the commute already" is a dislike of
# the commute, and asking about "the commute already" reads like a machine quoting the line.
DISLIKE_TAIL = re.compile(
    r"(?:[\s,]+(?:already|now|too|though|tho|anymore|any\s+more|at\s+the\s+moment|"
    r"right\s+now|so\s+much|that\s+much|these\s+days|all\s+the\s+time|as\s+well|anyway|"
    r"honestly|tbh|btw|lol|ha))+$", re.I)


# The thing is the person's own words, and their `my` belongs to them: "i dont like my body" was
# answered "What is it about my body that gets you?", which is the bot asking about its own body.
# The possessive turns with the question; a thing that is nobody's ("the commute") is unchanged.
DISLIKE_OWN = re.compile(r"\b(?:my|our)\b", re.I)
DISLIKE_OWN_SELF = re.compile(r"\bmyself\b", re.I)


def _yours(thing):
    """The thing as the person would hear it said back to them: their `my` becomes `your`."""
    return DISLIKE_OWN.sub("your", DISLIKE_OWN_SELF.sub("yourself", thing))


# The same taste with the "i" left out: "not 2 keen on the new place", "not a fan of the open
# plan", "not too fussed about the colour". People drop the subject in a chat, and the store
# reads a taste from a first person verb, so the subject-less line gave nothing to object to:
# "not 2 keen on the new place" got "Got it. Is there anything you'd like a hand with?" and
# "not too keen on it" got "I'm listening - say more if it helps", while "im not keen on the new
# place" was asked about the place. The thing is the same thing and the question is the same.
DISLIKE_WITHOUT_AN_I = re.compile(
    r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright|honestly)\W+)*"
    r"(?:not|n't)\s+(?:(?:really|that|too|2|very|so)\s+)?(?:(?:much|a\s+bit)\s+of\s+)?"
    r"(?:a\s+)?(?:keen|fan|fond)\s+(?:of|on|about|for)\s+(?P<thing>[^?.!]+)$", re.I)
# A pronoun is not a thing to ask about: "not a fan of it" points at what was already said, and
# the composer answers that from the thread, not from the line.
NOT_A_THING_ASKED = frozenset("""it its it's that this these those them him her you me
    everything anything something nothing""".split())


def the_dislike_ask(clean, memory):
    """A question about the thing the person has just said they do not like, or None."""
    thing = obstacle.the_thing(clean)
    if not thing:
        found = DISLIKE_WITHOUT_AN_I.match(" ".join(str(clean or "").split()))
        if found:
            thing = found.group("thing").strip(" ,.;:-")
            if not thing or thing.lower() in NOT_A_THING_ASKED:
                return None
            # The line is the person's own words, so a tail that only softens it ("the commute
            # already", "the open plan really") stays off the question.
            thing = DISLIKE_TAIL.sub("", thing).strip(" ,.;:-")
            if not thing or len(thing.split()) > DISLIKE_TOO_LONG:
                return None
            if DISLIKE_HAS_TWO_HALVES.search(thing):
                return None
            thing = _yours(thing)
            options = [frame.format(thing=thing, Thing=thing[:1].upper() + thing[1:])
                       for frame in DISLIKE_ASKS]
            return _choose(options, memory, clean)
    if thing:
        thing = _yours(DISLIKE_TAIL.sub("", thing).strip(" ,.;:-"))
    if not thing or len(thing.split()) > DISLIKE_TOO_LONG:
        return None
    if DISLIKE_HAS_TWO_HALVES.search(thing):
        return None
    options = [frame.format(thing=thing, Thing=thing[:1].upper() + thing[1:])
               for frame in DISLIKE_ASKS]
    return _choose(options, memory, clean)


def _own_feeling(clean):
    """The pool for a statement about the speaker's own worth or direction, or None."""
    if clean.rstrip().endswith("?") or NOT_SELF.search(clean):
        return None
    if NOT_ENOUGH.search(clean):
        return NOT_ENOUGH_REPLY
    if NO_DIRECTION.search(clean):
        return NO_DIRECTION_REPLY
    return None


# A letter that asks the person to ring them is not answered in writing: "i got a letter from the
# council asking me to call" got "Answer it in writing rather than by phone", which is the
# opposite of what the letter asked. The shape is still the letter's, but the reply they need is
# the call one.
SUMMONS_ASKS_A_CALL = re.compile(
    r"\b(?:ask|asks|asking|asked|tell|tells|telling|told|want|wants|wanting)\s+me\s+to\s+"
    r"(?:call|ring|phone|get in touch)\b")


def _summons_pool(summons, line=""):
    """The lines for a summons, by shape: a meeting, a letter, or a phone call."""
    shape = summons.get("shape") if isinstance(summons, dict) else None
    if shape == "written":
        if SUMMONS_ASKS_A_CALL.search(line):
            return SUMMONS_RANG
        return SUMMONS_WRITTEN
    if shape == "rang":
        return SUMMONS_RANG
    return SUMMONS_SEEN


# Something of the speaker's being in the way counts as impact: "parking in my space",
# "eating my food", "changing my shifts". The person themselves ("my sister", "my landlord")
# is not a thing of theirs, so "my brother always wins at chess" is still just news.
# A thing of yours only counts when the line also says it keeps happening: "someone keeps
# parking in my space" is a grumble, "i'm selling my car" and "it's me, my partner and our
# dog" are not. Without the recurrence, any possessive reads as an insult.
GRIEVANCE_RECUR = re.compile(r"\b(?:keeps?|kept|always|never|constantly|forever|again|"
                             r"every (?:day|night|morning|week|time|monday|weekend)|all the "
                             r"time|day after day|week after week)\b")
GRIEVANCE_MINE_THINGS = re.compile(r"\b(?:my|our)\s+([a-z']+)")

GRIEVANCE_MINE = re.compile(r"\bi (dont|don't|cant|can't|never|keep|keeps|always|wont|won't|"
                            r"refuse|refused|forget|forgot|cancel|promised)\b")

# A promise that keeps not happening: "he keeps saying next week", "she says shell come but never
# does", "the school keeps saying they will ring me back". Somebody has said something about a
# thing that has not arrived, and nothing in the grievance reader sees it - there is no impact word
# and nothing of the speaker's in the way - so every one of these went to "I'm listening" or
# "Thanks for telling me", the lines that fit any message, said to a person who has just described
# a promise that keeps moving. The reply leads with the thing the bot does know (a promise that
# moves every time is a pattern, not a date) and then names the one place that settles it: the day
# itself, asked for in writing.
#
# The words are read as reported speech and not as the speaker's own: "what should i say to my
# boss" has a person, a "say" and a "should" and none of the promise, and a deck scan caught it
# the moment the say-verb was allowed to stand on its own.
PROMISE_PEOPLE = (
    r"(?:mum|mom|mother|dad|father|parents|sister|brother|son|daughter|kid|kids|child|children|"
    r"wife|husband|partner|boyfriend|girlfriend|ex|fiance|fiancee|mate|friend|flatmate|housemate|"
    r"lodger|neighbour|neighbor|boss|manager|colleague|coworker|carer|nan|nana|grandma|grandad|"
    r"granny|aunt|uncle|cousin|stepdad|stepmum|landlord|agency|solicitor|builder|plumber|mechanic|"
    r"dealer|garage|contractor|tradesman|workman|electrician|cleaner|tutor|teacher|headteacher|"
    r"social worker|doctor|gp|dentist|nurse|therapist)")
PROMISE_OFFICES = (
    r"(?:council|school|college|university|landlord|letting agent|agent|bank|building society|"
    r"shop|store|company|employer|hr|boss|manager|surgery|gp|doctor|dentist|hospital|clinic|dwp|"
    r"jobcentre|job centre|insurance|supplier|provider|broadband|water company|housing "
    r"association|housing|department|office|service)")
# who said it, and what they said
_PROMISE_SAYS = (r"(?:say|says|said|saying|tell|tells|told|telling|swear|swears|swore|swearing|"
                 r"promise|promises|promised|promising)")
_PROMISE_KEEPS = r"(?:keeps?\s+|kept\s+|always\s+|still\s+|just\s+|only\s+)?"
PROMISE_OFFICE = re.compile(r"\b" + PROMISE_OFFICES + r"\b")
PROMISE_A_PERSON_NAMED = re.compile(
    r"\b(?:my|our|his|her|their)\s+(?:[a-z]+\s+){0,2}?" + PROMISE_PEOPLE + r"\b")
PROMISE_REPORTED = re.compile(
    r"\b(?:he|she|they|hes|shes)\s+" + _PROMISE_KEEPS + _PROMISE_SAYS + r"\b"
    r"|\b(?:my|our|his|her|their)\s+(?:[a-z]+\s+){0,2}?" + PROMISE_PEOPLE + r"\s+"
    + _PROMISE_KEEPS + _PROMISE_SAYS + r"\b"
    r"|\b" + PROMISE_OFFICES + r"\s+" + _PROMISE_KEEPS + _PROMISE_SAYS + r"\b"
    r"|\b(?:promise|promises|promised|promising|swear|swears|swore|swearing)\b")
PROMISE_FUTURE = re.compile(
    r"\b(?:will|wont|won't|going to|gonna|next (?:week|month|weekend|time|"
    r"day|year)|tomorrow|soon|later|sometime|eventually|hell|he'll|shell|she'll|theyll|"
    r"they'll|promised|promises?|ring back|call back|get back to me|sort it|do it|"
    r"pay me back|pay it back|take the kids|in the post|by (?:noon|midnight|monday|tuesday|"
    r"wednesday|thursday|friday|saturday|sunday|the end of|christmas|new year|the weekend)|"
    r"end of the (?:week|month)|next few days|after (?:christmas|new year|the weekend))\b")
# There has to be a promise in the line and an outcome that did not arrive: the reported speech
# with a future in it ("says hell do it"), or the set phrase for one that keeps not happening
# ("but never does", "never does what he says"). Without that "she never says well done" and "my
# partner doesnt do long drives" have the shape and none of the promise.
PROMISE_BUT_NEVER = re.compile(
    r"\b(?:but|and)\s+never\s+(?:does|do|did|comes|came|happens|happened|turns up|shows up|"
    r"pays|paid|rings|rang|calls|called|sorts? it|gets round to it)\b")
PROMISE_NEVER_WHAT = re.compile(r"\bnever does what\b|\bnever follows through\b")
# A promise is the one that keeps moving, so the line needs the recurrence word as well as the
# future in it: "my mum says i should ring my aunt more" has reported speech and a "should" and is
# advice, not a promise.
# Nothing a line about a promise can say is right for a line that is really about a harm: "shes
# saying she might do it again" has the shape of a promise that keeps moving and is not one.
PROMISE_RISK = re.compile(
    r"\b(?:kill|killed|killing|suicide|suicidal|overdose|self.harm|end it|end it all|"
    r"not be here|be dead|die|dying|do it again|do something stupid|take my own life|"
    r"hurt (?:myself|himself|herself|themselves)|cut (?:myself|himself|herself|themselves))\b")
PROMISE_RECUR = re.compile(r"\b(?:keeps?|kept|always|constantly|forever|again|every time|"
                           r"still|never)\b")
# A machine saying something is not a promise: "my phone keeps saying storage full", "my printer
# keeps saying paper jam", "my tv keeps saying no signal" all have the shape of one, and the
# device answers own them.
PROMISE_NOT_A_PERSON = re.compile(
    r"\b(?:phone|laptop|printer|tv|television|boiler|app|apps|screen|router|computer|tablet|"
    r"washing machine|dishwasher|oven|car|watch|kindle|console|xbox|playstation|alexa|siri|"
    r"fridge|freezer|heating|thermostat|meter)\b")
# What is owed is a debt, not a promise: the money pools answer "he wont pay" and "he keeps saying
# hell pay me back" with the asking-for-it line, which is the one they need.
PROMISE_MONEY = re.compile(
    r"\b(?:pay|pays|paid|paying|owes|owe|owed|owing|loan|lent|borrow|borrowed|rent|bill|bills|"
    r"mortgage|wages|salary|quid|pounds|grand|deposit|invoice|refund|compensation)\b")
# "they" after an office is the office: "the school keeps saying they will ring me back" is the
# school, and only a he or a she makes the same words personal.
PROMISE_A_HE_OR_SHE = re.compile(r"\b(?:he|she|him|his|her|hes|shes)\b")

PROMISE_A_PERSON = (
    "A promise that moves every time is a pattern, not a date. Ask for the day itself, in a "
    "message, so there is something written down - which day, and put it in the calendar - and "
    "believe the answer rather than the intention. What is it they keep putting off?",
    "Stop asking whether it will happen and ask what has happened: one small thing this week, "
    "in writing. A day that slips again is the answer, and it is better to know that before you "
    "count on it. What have you been counting on?",
    "Say it once, plainly, and ask which day they mean: a promise that never gets a day is the "
    "thing worth testing, and testing it is fairer than deciding what they are like. What would "
    "change for you if it actually happened?",
)
PROMISE_AN_OFFICE = (
    "A phone-back that never comes is worth putting in writing: the reference, the day you "
    "asked, and one clear question. The complaints address on their own site is read by "
    "somebody who can answer it, and it leaves a record. What were you waiting on?",
    "Ask by email so it stops being a conversation: what was promised, who said it, and the "
    "day you want it by. That same note is the one a complaint or an ombudsman asks for, so it "
    "is worth writing once. What is the thing they keep not doing?",
    "Ring once more, quote the day they gave you, and ask for the answer in writing: a promise "
    "on the record sits in a different queue from one made on a phone call. When did they first "
    "say it?",
)


def _a_promise_that_keeps_moving(clean):
    """The reply to a promise that keeps not happening, or None."""
    reported = PROMISE_REPORTED.search(clean)
    device = PROMISE_NOT_A_PERSON.search(clean)
    if device and (reported is None or device.start() < reported.start()):
        # The machine is the one saying it: "my phone keeps saying storage full", and the device
        # answers own those. A boiler named after the promise is the thing being promised, not
        # the speaker - "my landlord keeps saying hell fix the boiler".
        return None
    if PROMISE_MONEY.search(clean) or PROMISE_RISK.search(clean):
        return None
    said = set(re.findall(r"[a-z']+", clean.replace("\u2019", "'")))
    # An office is the subject when it is named and no person is: "the hospital keeps saying they
    # will send an appointment" is a phone-back, and the word hospital there is where the
    # appointment is from rather than a body to be careful about.
    office_subject = (bool(PROMISE_OFFICE.search(clean))
                      and not PROMISE_A_HE_OR_SHE.search(clean)
                      and not PROMISE_A_PERSON_NAMED.search(clean))
    if not office_subject and (said & GRIEVANCE_HEALTH or said & GRIEVANCE_HARM):
        # A body, an illness or a harm wants the care line, never a word about a promise.
        return None
    broken = PROMISE_BUT_NEVER.search(clean)
    if not (PROMISE_NEVER_WHAT.search(clean)
            or (reported and (
                (PROMISE_RECUR.search(clean) and PROMISE_FUTURE.search(clean))
                or (broken and broken.start() > reported.end())))):
        return None
    return PROMISE_AN_OFFICE if office_subject else PROMISE_A_PERSON


# A person who has just been told what to do and says it is doable is not asking anything: they
# have decided to do it. "ok that sounds doable" was answered with "I'm listening - say more if it
# helps", which asks them to say more at the exact moment they have said the useful thing, and
# "that sounds doable, thanks" with the neutral nod, which thanks somebody for accepting a plan.
# The same reading the PLAN pool gives a next step, for the line that gives no step of its own:
# say go on, and name the one thing that makes a set of steps work - the first bit, done properly.
# It is only ever a judgement of the answer: the line has to be short, has to name no subject of
# its own, and has to come after an answer with advice in it (`the_advice`), so "the door is
# doable in a weekend" and "nothing is doable today" are left to the modules.
DOABLE = re.compile(
    r"\b(?:doable|manageable|easy\s+enough|not\s+too\s+bad|simpler\s+than\s+i\s+thought|"
    r"easier\s+than\s+i\s+thought|that\s+(?:should\s+)?work|worth\s+a\s+(?:go|try)|"
    r"i\s+(?:can|could)\s+do\s+(?:that|it))\b", re.I)
# A judgement of the answer is built out of these words and nothing else. The fence is the
# vocabulary rather than a list of things, because what must not be read is any line with a
# subject of its own in it: "the door is doable in a weekend" and "the pain is manageable" are
# about a door and a back, and the only words a judgement of the line above can use are the
# judgement, the pointer at that line ("that", "it", "sounds") and the breathers around it.
DOABLE_WORDS = frozenset("""
    doable manageable easy enough not too bad simpler easier than i thought think work works
    should worth a go try can could do that thats this its it is sounds sound seems seem looks
    possible a be
""".split())
DOABLE_BREATHERS = frozenset("""
    ok okay alright right yeah yes yep oh ah well hmm so and but then honestly really probably
    definitely be thanks thank you ta cheers please mate
""".split())
# Never a judgement of something else: a body, a bill, a person. "the pain is manageable" is not
# the person accepting the advice, whatever else the line says.
DOABLE_NOT = re.compile(
    r"\b(?:pain|ache|hurts?|hurting|bleeding|temperature|bill|bills|debt|rent|money|pay|price|"
    r"cost|boss|mum|dad|husband|wife|partner|son|daughter|kid|kids|child|baby)\b", re.I)
DOABLE_REPLIES = (
    "Good \u2014 the first bit is the whole trick, so do that properly and see how you get on.",
    "That's the way. Shout if a step of it does not make sense once you are in it.",
    "Right. Start with the first part and tell me how it goes.",
)


# The follow-up fold in front of the line: "sounds doable" reaches the composer as "what about
# sounds doable", because the understanding engine reads a short line after an answer as the thing
# they are asking about next. The fold is not part of what the person said, so it comes off before
# the judgement is read, or every judgement would be read as a thing with a name.
DOABLE_FOLD = re.compile(r"^(?:what\s+about|how\s+about|and|also|what\s+of|then)\s+", re.I)


def _reads_as_a_judgement(text):
    """True when the line is nothing but a judgement that what was said is doable.

    No memory is looked at, so the question can be asked by a part of the bot that has no advice
    to hand (the swap reading in `bot/modules/answers.py` asks it): the answer is only whether the
    words of the line make a judgement of the line above, and `_a_doable` is what adds whether
    there was anything to judge.
    """
    clean = " ".join(str(text or "").lower().split())
    while DOABLE_FOLD.match(clean):
        clean = DOABLE_FOLD.sub("", clean, count=1).strip()
    if not clean or "?" in clean:
        return False
    words = clean.split()
    if len(words) > 8:
        return False
    if not DOABLE.search(clean) or DOABLE_NOT.search(clean):
        return False
    said = [word.strip(".,!?;:'\u2019") for word in words]
    # Something of their own is in the line, so it is a judgement of that and not of the answer:
    # "the whole shed is doable in a day".
    return all(word in DOABLE_WORDS | DOABLE_BREATHERS for word in said)


def _a_doable(clean, memory):
    """The reply for a short "that's doable" about the advice just given, or None."""
    if not _reads_as_a_judgement(clean):
        return None
    if not the_advice(memory):
        # Nobody has been told anything to do, so there is nothing this line is judging.
        return None
    return _choose(DOABLE_REPLIES, memory, clean)


def a_doable(text, memory):
    """Read by bot/modules/greeting.py: is this line a judgement of the answer just given?

    The fallback module's own floor asks `_a_doable` too, and the greeting module asks this one
    *before* `bot/memory/detail.py`, because a short line with a copula in it is a detail to that
    reading - "sounds doable" came back "The same goes for the sounds doable: ...". One reading
    with two askers, so the two cannot disagree about whose turn a line is.
    """
    clean = " ".join(str(text or "").lower().split())
    return _a_doable(clean, memory)


def reads_as_a_judgement(text):
    """Read by bot/modules/answers.py: is this line a judgement rather than a thing?

    The swap reading hands the answer to a thing the person named ("what about the bathroom" ->
    "The same goes for the bathroom: ..."). A judgement of the answer names no thing, and reading
    one as a thing says the judgement back as if it were one: "sounds doable" came back "The same
    goes for the sounds doable: ...". Nothing is written here, so asking costs a turn nothing.
    """
    return _reads_as_a_judgement(text)


# A person who tells the bot their next step ("ok ill book her in tomorrow", "ill try that
# tonight") is not asking for anything: they want it acknowledged. A flat "Got it" misses that,
# and the sad pool would be wrong, because a plan is not bad news.
PLAN = (
    "Good — that sounds like the right next step. Tell me how you get on.",
    "Nice one. Let me know how it goes.",
    "That sounds sensible. Shout if it does not go to plan.",
)

# A next step that changes a medicine is not a next step to bless: the pool above reads every
# "i'm going to ..." as a decision somebody has taken, and a prescription is the one kind of
# decision that waits for the person who wrote it. "im going to skip my medication for a week"
# came back "That sounds sensible. Shout if it does not go to plan.", and "im going to cut down
# my insulin" the same.
#
# The rule is about the change, not about the medicine, so it is written as two shapes and a
# window between them rather than as a list of sentences:
#
#   a verb of changing what is taken  ...  a word for what is taken
#   a word for what is taken          ...  a change in how much is taken ("an extra dose",
#                                          "two instead of one")
#
# The verb list is the ordinary English for it - stop, quit, give up, leave off, come off, cut,
# reduce, halve, double, increase, raise, lower, skip, miss, drop, ditch, bin, knock off, wean,
# taper, flush, switch, swap, change - because every one of them came up in a real line and each
# was blessed before. What keeps them safe is the second half: "cut the grass", "cut down on
# sugar", "drop the kids at school", "give up the booze", "take two weeks off work" and "change my
# mind" name nothing that is taken, so they keep their own answers. The negative lookahead keeps
# a walk past the chemist out of it: "stop at the chemist for my tablets" is a place to go, not a
# dose.
_MEDICINE_WORD = (
    r"\b(?:medication|medications|meds|medicine|medicines|tablet|tablets|pill|pills|"
    r"dose|doses|dosage|insulin|insulin injections|inhaler|inhalers|steroids|antibiotics|"
    r"antidepressants|anticoagulants|blood\s+thinners?|blood\s+pressure\s+tablets|epipen|"
    r"epipens|statins?|beta\s+blockers?|thyroxine|levothyroxine|metformin|warfarin|"
    r"prednisolone|painkillers|sleeping\s+tablets|epilepsy\s+tablets|hormones?|"
    r"prescription|prescriptions|treatment)\b")
# What a clinic does to you is not a medicine either: "my gym sessions", "three sessions with the
# physio", "my counselling sessions", "my therapy approach" are all plans, and a word for a
# session beside a verb of stopping or changing read as a dose. Nothing the caution is for is
# said as a session, so the word is out and a line that names one keeps its own answer.
# The verbs that can be followed by a place ("stop at the chemist", "drop in on mum", "cut
# through the park") get a lookahead, because a place is where the person is going, not what they
# take. The rest cannot take one, so "taper off my steroids" and "come off my antidepressants"
# are read with no lookahead in the way.
_VERB_AT_A_PLACE = (
    r"\b(?:stop|stopping|drop|dropping|cut|cutting|pop|popping|skip|skipping|miss|missing)\b"
    r"(?!\s+(?:at|by|in|on|off|for|to|past|outside)\b)")
# The change itself, said as a verb.
_CHANGE_VERB = (
    r"\b(?:quit|quitting|give\s+up|giving\s+up|leave\s+off|leaving\s+off|come\s+off|"
    r"coming\s+off|go\s+off|going\s+off|reduce|reducing|halve|halving|half|halfing|double|"
    r"doubling|increase|increasing|raise|raising|lower|lowering|ditch|ditching|bin|binning|"
    r"knock\s+off|knocking\s+off|wean|weaning|taper|tapering|flush|flushing|switch|switching|"
    r"swap|swapping|change|changing)\b")
# Splitting a tablet is the one change to a medicine with its own answer, and it is a better one:
# `science.cut-or-crush-a-tablet` says to check whether it is a modified-release tablet before
# anything is cut, and "i want to cut my pills in half to make them last" was that card on main
# and the pharmacist line here. A split is about the tablet in the person's hand, not about the
# prescription, so the caution stands down for it and the card answers.
_SPLITTING_A_TABLET = re.compile(
    r"\b(?:cut|cutting|split|splitting|break|breaking|halve|halving|half)\b[^.?!]{0,20}"
    r"\b(?:tablets?|pills?|capsules?)\b[^.?!]{0,14}\b(?:in\s+half|in\s+two|in\s+quarters?|"
    r"down\s+the\s+middle)\b"
    r"|\b(?:tablets?|pills?|capsules?)\b[^.?!]{0,14}\b(?:in\s+half|in\s+two|in\s+quarters?)\b",
    re.I)
# The change said as an amount: "an extra one", "two instead of one", "three tonight".
_AMOUNT = (
    r"\b(?:take|taking|have|having|pop|popping|swallow|swallowing)\s+(?:an?\s+)?"
    r"(?:extra|two|three|four|double|twice|\d+)\b")
PLAN_MEDICINE = re.compile(
    r"(?:" + _VERB_AT_A_PLACE + r"|" + _CHANGE_VERB + r")[^.?!]{0,40}" + _MEDICINE_WORD
    + r"|" + _MEDICINE_WORD + r"[^.?!]{0,30}" + _AMOUNT
    + r"|" + _AMOUNT + r"[^.?!]{0,40}" + _MEDICINE_WORD,
    re.I)
# The medicine that causes real trouble stopped suddenly is named, because that is what makes the
# wait worth it. The ones that are usually reduced in steps over weeks are their own list, so a
# line that names none of them is not read the longest sentence in the pool.
PLAN_MEDICINE_SLOW = re.compile(
    r"\b(?:antidepressants?|steroids?|prednisolone|insulin|blood\s+pressure|blood\s+thinners?|"
    r"anticoagulants?|warfarin|epilep\w*|beta\s+blockers?|statins?|thyroxine|levothyroxine)\b",
    re.I)
PLAN_MEDICINE_REPLY = (
    "Do not change a prescribed dose on your own, even for a week: a pharmacist can tell you "
    "today, free, whether to skip it, take less, take more or come off it, and how slowly to go. "
    "If you have stopped it already and feel unwell, ring 111.",
    "Ask a pharmacist before you change a dose, skip it or come off it, even for a week: they "
    "know whether it is safe and how slowly to do it. If you have stopped it already and feel "
    "unwell, ring 111.",
)
PLAN_MEDICINE_SLOW_REPLY = (
    "Do not change a prescribed dose on your own, even for a week: a pharmacist can tell you "
    "today, free, whether to skip it, take less, take more or come off it, and how slowly to go. "
    "Antidepressants, steroids, insulin, blood pressure tablets and blood thinners are the ones "
    "that cause real trouble stopped suddenly. If you have stopped it already and feel unwell, "
    "ring 111.",
    "Ask a pharmacist before you change a dose, skip it or come off it, even for a week: they "
    "know whether it is safe and how slowly to do it, and antidepressants, steroids, insulin, "
    "blood pressure tablets and blood thinners are the ones that are usually reduced in steps "
    "over weeks. If you have stopped it already and feel unwell, ring 111.",
)
# Two things have to be true before the caution above is the right answer, and both were wrong
# when the rule was only the regex. The change has to be the person's own decision, and it has to
# be a decision rather than a question:
#
#   my gp is stopping my tablets        -> the doctor decided, so "ask a pharmacist before you
#                                          skip it" is advice about nothing
#   can i stop my medication            -> the knowledge base answers this one well ("keep taking
#                                          it until a pharmacist, nurse or GP tells you to stop"),
#                                          and a question is not a plan
#
# So the reading the pools ask is `reads_as_a_change_of_medicine`, not the regex on its own: the
# words of the rule in one place, so the three pools that cheer a plan cannot drift apart.
_A_QUALIFIED_PERSON_DOES_IT = re.compile(
    r"\b(?:my|our|the|his|her|their)?\s*\b(?:gp|doctor|dr|consultant|psychiatrist|specialist|"
    r"surgeon|nurse|pharmacist|midwife|psychologist|dietitian|anaesthetist)\b[^.?!]{0,30}"
    r"\b(?:is|are|was|were|has|have|had|keeps|kept|stopping|stopped|reducing|reduced|changing|"
    r"changed|taking|took|wants|wanted|told|said|thinks?|advised|suggested|switched|put)\b",
    re.I)
_A_QUESTION = re.compile(
    r"(?:^\s*(?:can|could|should|shall|would|will|is|are|do|does|did|am|what|how|when|where|"
    r"why|which|who)\b)|\?\s*$", re.I)


def reads_as_a_change_of_medicine(text):
    """Is this line the person's own plan to change what they take? Read by the plan pools."""
    flat = str(text or "")
    if not PLAN_MEDICINE.search(flat):
        return False
    if _SPLITTING_A_TABLET.search(flat):
        return False
    if _A_QUESTION.search(flat.strip()):
        return False
    return not _A_QUALIFIED_PERSON_DOES_IT.search(flat)


# The reply to a feeling said in the shape of a plan. Short and warm, and it asks for the story,
# because the person is telling one.
IDIOM_SHY = (
    "Ha — one of those days, then. What happened?",
    "Oh no. Go on, what happened?",
)
IDIOM_GLAD = (
    "Ha — that good? What are you waiting for?",
    "Sounds like a big one. What is it?",
)
PLAN_OPENING = re.compile(r"^(?:ok(?:ay)?|alright|right|so|well|thanks|cheers)?[\s,]*"
                          r"(?:i'?ll|ill|i will|i'?m going to|im going to|i'?m gonna|im gonna|"
                          r"gonna|going to)\s+\w+")
# The plan that has not happened yet: "i havent booked it yet" holds the words of a done thing
# and is the opposite of one.
PLAN_NOT_YET = re.compile(r"\b(?:havent|haven't|hasnt|hasn't|aint|ain't|not yet|still to|"
                          r"need to|have to|yet to)\b")
PLAN_NOT = re.compile(r"\b(?:never|not|won'?t|wont|can'?t|cant|don'?t|dont|didn'?t|didnt|"
                      r"shouldn'?t|shouldnt)\b")
# A thing the person has done with, in their own words: "i sorted it", "dealt with it", "its
# sorted now". The whole line has to be this, because "i sorted it at last" is the same report and
# "i sorted it and she still hasnt rung" is a grievance. Used in a safety thread, where the same
# words are a report on the advice (see `_after_safety`), and left to `PLAN_DONE` everywhere else.
THING_SORTED = re.compile(
    r"^(?:(?:ok|okay|alright|right|so|well|yeah|yep|yes|cool|fine|thanks|thank you|"
    r"no worries|anyway|and|but|then|all)\s+)*"
    r"(?:"
    r"(?:i|we|ive|i've|weve|we've)\s+(?:(?:have|had|got|already)\s+)?"
    r"(?:sorted|dealt with|handled|done|did|took care of)\s+"
    r"(?:it|that|this|them|things|everything)(?:\s+out)?"
    r"|(?:its|it's)\s+(?:sorted|done|handled|dealt with)(?:\s+now)?"
    r"|(?:sorted|done|handled|dealt with)\s+(?:it|that|this|them)(?:\s+out)?"
    r")"
    r"(?:\s+(?:now|thanks|thank you|already|ok|okay|alright|then))?[\s.!]*$",
    re.IGNORECASE)


# A feeling said in the shape of a plan: "im going to die of embarrassment", "i'm going to die
# laughing". PLAN_OPENING reads every "i'm going to ..." as a next step, so acking it with "Good —
# that sounds like the right next step" answers the wrong thing entirely.
PLAN_IDIOM = re.compile(
    r"\b(?:die|dying|died)\s+(?:of|from)\s+(?:embarrassment|boredom|shame|laughter|excitement|"
    r"cringe)\b"
    r"|\b(?:die|dying|died)\s+laughing\b"
    r"|\bkill(?:ing)?\s+my\s*self\s+laughing\b"
    r"|\b(?:crack(?:ing)?\s+up|wet\s+my\s*self)\b[^.?!]{0,12}\blaughing\b")


# The next step said as a decision rather than as ""i'll ..."": "i think i should ring my sister",
# "i ought to clear the garage", "i should probably call my dad". These were the nod or a receipt
# back at the person ("Noted: you should go and see your mum"), because `PLAN_OPENING` reads only
# the will-going-to shape. The should has to be the person's own next step, so the words that make
# it a verdict about how things stand - "i should be asleep" at midnight, "i should have known",
# "i should think so", "i should hope so" - are fenced off.
PLAN_DECIDED = re.compile(
    r"^(?:ok(?:ay)?|alright|right|so|well|thanks|cheers|anyway|honestly|tbh|yeah)?[\s,]*"
    r"(?:(?:i think|i reckon|i guess|i feel like|maybe|perhaps|probably)\s+)?"
    r"(?:i\s+(?:(?:really|probably|definitely|just|still|actually|honestly|so)\s+)?"
    r"(?:should|ought to|oughta|had better|better)\b|i'?d better\b|id better\b)"
    r"\s+(?!be\b|have\b|hav\b|never\b|not\b|n'?t\b|think\b|hope\b|say\b|know\b|"
    r"imagine\b|expect\b|worry\b|care\b|bother\b)"
    r"(?:probably|really|definitely|just|still|maybe|perhaps|actually|now|then)?\s*"
    r"\w+")


def _plan_reported(clean, mood):
    """True when the line is the person saying what they will do next, not a trouble."""
    if mood == "negative" or PLAN_NOT.search(clean) or PLAN_IDIOM.search(clean):
        return False
    return (bool(PLAN_OPENING.match(clean)) or bool(PLAN_DECIDED.match(clean))
            or any(phrase in clean for phrase in PLAN_DONE))


# Ending a relationship, said as a plan or as news. The person has to come straight after the
# leaving word, so "leaving him a note" and "leaving my job" are not this.
RELATIONSHIP_ENDING = re.compile(
    r"\b(?:leaving|leave|left|walking out on|walk out on|walked out on|divorce|divorcing|"
    r"dump|dumping|dumped|splitting up with|split up with|broke up with|break up with|"
    r"breaking up with|ending it with|end it with|ended it with)\s+" + A_PERSON +
    # The person has to be the end of the thought: "leaving him a note", "leaving him a
    # message" and "leaving him at nursery" are about a note, a message and a nursery.
    r"(?=\s*(?:[.!?,;]|$|(?:\s+(?:for good|behind|tomorrow|tonight|next week|this week|finally|now|today))\s*(?:[.!?,;]|$)))")


# A line that holds the person's own life up against a crowd's: "everyone my age owns a house",
# "all my mates are sorted", "most people my age are married", "people my age all seem to have
# bought a flat". Every one of them is a feeling about where they stand, and none of them is good
# news: the cheer ("Brilliant. Really pleased for you.") is for a win somebody had, and the nod
# ("Got it. Is there anything you'd like a hand with?") is for a fact nobody minds about, so a
# person saying they feel behind got a stock line, and the store asked them how old the crowd was
# ("everyone my age owns a house" -> "You haven't told me how old they are.").
#
# The reading is two halves, and it needs both: a crowd, and a marker of the standing the line is
# about. A crowd on its own is a report ("everyone at work is off sick") and a marker on its own
# is the person's own life ("i still rent"), and neither is a comparison.
A_CROWD_SUBJECT = re.compile(
    r"\b(?:everyone|everybody|most people|people|folk|others|no ?one|nobody"
    r"|all (?:of )?my (?:friends|mates|siblings|cousins)|my (?:friends|mates)"
    r"|the people (?:i know|around me|at work|on my course))\b", re.I)
# What the crowd has and the person is measuring themselves against. Keep it to the things people
# actually keep score with; a verb that is about anything else ("everyone loved the cake") is not
# a comparison and must not be read as one.
A_MARKER_OF_STANDING = re.compile(
    r"\b(?:owns?|owned|owning|bought|buying|has? bought|have bought"
    r"|married|engaged|settled|sorted|got it sorted|have it sorted|has it sorted|promoted"
    r"|mortgage|kids|children|babies|pregnan\w*|ahead|better than me|more than me"
    r"|further along|further ahead|doing better"
    # The status as a thing held rather than a verb of getting it: "everyone else has a house",
    # "all my mates have got a flat". The article is what keeps a house somebody lives in ("the
    # people in the house are asleep") out of it.
    r"|(?:has|have|got|with)\s+(?:a\s+|an\s+|their own\s+|his own\s+|her own\s+)?"
    r"(?:house|flat|place|mortgage|baby|kids|children|career|job|salary|pension)\b)\b", re.I)
# A crowd that still has a parent is not the standing a person is measuring their life by: it is
# a loss in the middle of a chat, and the condolence or the gentle pool is the answer to it.
A_PARENT_STILL_THERE = re.compile(
    r"\b(?:mum|mam|mom|dad|mother|father|parents|gran|nan)\b", re.I)
# The person's own age named as the measure rather than asked for: "everyone my age", "people my
# age", "at my age". The store reads the word as an ask for the number and answers that they never
# gave it, which is the one reply that makes no sense to somebody saying everybody else is ahead.
MY_OWN_AGE = re.compile(r"\b(?:my|our) (?:own )?age\b", re.I)
# The person's own win is the whole line ("i bought a house", "we got the keys"), and a crowd in it
# is who they are telling. A comparison never has the person as its subject.
THE_PERSON_IS_THE_SUBJECT = re.compile(r"^\s*(?:i|ive|im|we|weve|were|me)\b", re.I)
# The comparison with an ask of its own on top ("everyone my age is having babies, what do i do")
# is a line for whatever answers the ask: naming the comparison back at them is not the answer to
# a question, so the reading stands down and lets the ask have the turn.
AN_ASK_ON_TOP = re.compile(
    r"\b(?:what (?:do|should|can) i do|what would you do|should i|how do i|help me|any advice"
    r"|what now|where do i start|advice)\b", re.I)


def a_comparison_of_standing(clean):
    """True when the line measures the person's life against a crowd's - the feeling of being behind.

    Published as a reading, not a pool: what follows a line like this is the same wherever it is
    met (bot/modules/memory_store.py asks it, so the age question stands down), and one name for
    the shape is what keeps the two agreeing.
    """
    line = " ".join(str(clean or "").split())
    if not line or "?" in line:
        return False
    if len(line.split()) > 14:
        return False  # a story that happens to start with a crowd is a story
    if A_PARENT_STILL_THERE.search(line) and re.search(r"\bstill\b", line, re.I):
        return False
    # A line that opens on the person and then turns to the crowd is still a comparison: "im 41
    # and everyone my age seems busy with kids" is the same feeling as "everyone my age seems busy
    # with kids". The person has to be the subject of the whole line for it to be their own news.
    comparison = line
    if THE_PERSON_IS_THE_SUBJECT.match(line):
        turned = re.split(r"(?:,|\band\b|\bbut\b)", line, maxsplit=1)
        if len(turned) < 2:
            return False
        comparison = turned[1]
        if not A_CROWD_SUBJECT.search(comparison):
            return False
    if not A_CROWD_SUBJECT.search(comparison):
        # "at my age youd think id have it sorted" names no crowd and is the same measuring all
        # the same: the age is what they are holding themselves against.
        return bool(re.search(r"\bat (?:my|our) age\b", comparison, re.I))
    if AN_ASK_ON_TOP.search(line):
        return False
    if MY_OWN_AGE.search(comparison):
        # "everyone my age ...", "at my age youd think id have it sorted": an age used as the
        # measure is the comparison itself, whatever the crowd went on to have.
        return True
    return bool(A_MARKER_OF_STANDING.search(comparison))


# What a friend says to the feeling of being behind: it is not condoled (nothing happened), not
# cheered (the crowd is not the person's win) and not filed. The comparison is named, and the
# question turns the line from the list they are on to the thing they want.
A_COMPARISON_OF_STANDING = (
    "That kind of comparison always picks the one thing you haven't got. Is it something you "
    "actually want, or is it the being behind that stings?",
    "Other people's lives look tidier from the outside than they are from the inside. What would "
    "you want to be different?",
    "It is easy to feel like the only one not there yet, and most people are a lot less sorted "
    "than they look. What would actually help you right now?",
    "That is a fair thing to feel, and the measuring is doing a lot of the work. What do you want "
    "out of it, apart from the comparison going away?",
    "There is no deadline on any of that, whatever the timeline looks like from where you are "
    "standing. What is the one piece you would want to get to?",
)


def _a_relationship_ending(clean):
    """True when the line is about leaving a person, which is neither a win nor a plan."""
    return bool(RELATIONSHIP_ENDING.search(clean))


# What our own line says when it answered a hard one: the openings of the sad, low and missing
# pools. Read by the composer because the nod has nothing in it of its own, and the thread it
# belongs to is the one the bot is already in.
OUR_HEAVY_TELL = re.compile(
    r"(?:sorry to hear|i'm so sorry|i'm really sorry|that sounds rough|that's a heavy feeling"
    r"|that's a lot to|that sounds exhausting|loneliness is rough|missing someone is the price"
    r"|it's a hard thing to carry|be kind to yourself|i'm glad you said it|you don't have to carry"
    r"|there's no rush to talk about it)")


# What those words look like in a line, with a boundary so "fired" and "gasp" are not them.
HAZARD_LINE = re.compile(r"\b(?:fires?|smoke|flames?|gas|fumes?|carbon monoxide|flue|"
                         r"fire brigade|fire service)\b")
# The same easing after a first-aid answer: nobody is bleeding any more, so the care pools (an
# eye on something that is still going on, or a trip to a&e) would not fit.
# Feeling better is not the same as being out of danger. With an overdose, a poisoning or a
# cardiac arrest a person can feel fine for hours while the harm is still going on, so the easing
# keeps the emergency line rather than sending them back to their day: chief-umbrella's three
# shapes ("i took an overdose" / "i feel a bit better now" was *"keep an eye on it today"*).
NO_RELIEF = re.compile(
    r"\b(?:overdos\w*|poison\w*|swallow\w*|paracetamol|ibuprofen|bleach|antifreeze|"
    r"carbon monoxide|pills|tablets|capsules|stopped breathing|not breathing|isnt breathing|"
    r"no pulse|cpr|cardiac|arrest|unconscious|unresponsive|collaps\w*|hanging|hung|"
    r"electrocut\w*|electric shock)\b")
# Who the person in danger is. A good share of the crisis lines in the deck are about somebody
# else - "my sister took an overdose last year", "my dad overdosed in march" - and the safety
# answer gets those right by speaking about "them". The continuation did not: the pools above
# are written for the person typing ("keep someone with you tonight", "stay with the person you
# told"), so "now shes talking about it again" got "Keep someone with you tonight, and ring back
# if it gets heavier - they'd rather hear from you". That is advice for a body that is not the
# one at risk, and it tells the carer to ring about themselves in the worst hour of their week.
#
# So each continuation asks one question first: is the person in this thread somebody else? It is
# read from the line that started the thread - the safety turn's own user line - so the relation
# and the gender are the person's own words ("your sister", "your dad"), and a "she" in the
# follow-up never has to be guessed. A line that names both - "i told my mum i want to die" - is
# answered as the speaker's own, because that is the mistake that has to stay safe.
SHE = frozenset((
    "sister", "mum", "mummy", "mother", "mam", "nan", "nanna", "gran", "granny",
    "grandma", "daughter", "wife", "girlfriend", "aunt", "auntie", "niece", "stepmum",
    "stepdaughter", "stepsister",
))
HE = frozenset((
    "dad", "daddy", "father", "son", "husband", "boyfriend", "brother", "nephew",
    "uncle", "grandad", "grandpa", "granddad", "stepdad", "stepson", "stepbrother",
))
# "my sister", "our eldest daughter", "my best mate". The relation is what the reply uses, and
# for the people a person looks after without a gender ("my friend", "my partner") the plural
# words below carry it, so nothing is assumed.
A_PERSON_OF_THEIRS = re.compile(
    r"\b(?:my|our)\s+(?:poor\s+|little\s+|eldest\s+|youngest\s+|old\s+|older\s+|elderly\s+|"
    r"grown\s*up\s+|best\s+|close\s+|work\s+|foster\s+|step\s*)*(?P<who>"
    r"sister|mum|mummy|mother|mam|nan|nanna|gran|granny|grandma|daughter|wife|girlfriend|"
    r"aunt|auntie|niece|dad|daddy|father|son|husband|boyfriend|brother|nephew|uncle|"
    r"grandad|grandpa|granddad|stepmum|stepdad|stepson|stepdaughter|partner|other\s+half|"
    r"friend|mate|flatmate|housemate|roommate|cousin|neighbour|colleague|child|kid|baby)\b",
    re.I)
# The speaker in danger: then it is their own crisis whatever else the line names. "me" is not
# here on purpose - "my friend told me she wants to die" would read as the speaker's own.
SELF_IN_DANGER = re.compile(
    r"\b(?:(?:i|ive|im|id)\b[^.?!]{0,24}?\b(?:took|swallow|overdos|od'd|cut|hurt|harm|"
    r"kill|suicid|die|dying|dead|end\s+it|hang|hung|jump|pills|tablets|starving|starve)|"
    r"myself\b|\bmy\s+own\s+(?:life|body|head))", re.I)
# Somebody hurt the speaker: "my husband hit me". The relation named in that line is the person
# who did it, not a person in danger, so the carer's pools (which ask the person to look after
# "your husband" tonight) have no business in this thread - the speaker is the one who needs
# looking after. Same rule as SELF_IN_DANGER, read from the other end of the sentence.
SOMEBODY_HURT_ME = re.compile(
    r"\b(?:hit|hits|hitting|beat|beats|beating|punch(?:ed|es|ing)?|kick(?:ed|s|ing)?|"
    r"slap(?:ped|s|ping)?|push(?:ed|es|ing)?|shov(?:ed|es|ing)|grab(?:bed|s|bing)?|"
    r"drag(?:ged|s|ging)?|strangl(?:ed|es|ing)|chok(?:ed|es|ing)|threaten(?:ed|s|ing)?|"
    r"abus(?:e|es|ed|ing)|assault(?:ed|s|ing)?|rap(?:e|ed|es|ing)|grope[sd]?|"
    r"burn(?:ed|t|s)|scald(?:ed|s|ing)|hurt|hurts|hurting|harm(?:ed|s)|attacked|"
    r"lock(?:ed|s)\s+(?:me|us)\s+(?:in|out))\s+(?:me|us)\b", re.I)
# A pronoun that carries somebody other than the speaker ("shes talking about it"), which is the
# one thing that sends the reading above back through the chat for the person it means.
A_PRONOUN_FOR_SOMEBODY = re.compile(
    r"\b(?:he|she|they|him|her|his|their|hes|shes|theyd|theyll|theyre|they've)\b", re.I)
# The continuation of a crisis answer that was about somebody else. Same job as CRISIS_AFTER -
# keep the person on the real help - in the words the carer needs: ask them straight, take the
# things away, ring the line with them rather than for them.

# The advice was a page of it, and this line is the report on it. "i tried that and it helped a
# bit" told the bot which part worked and got a stock line that would fit any message ("Got it.
# Is there anything you'd like a hand with?"); "ive been doing it for a week now" got their own
# sentence back. A friend answers the outcome, not the report, so there are four of them: it
# worked, it has not moved yet, it made things worse, and "I am doing it" with no verdict.
# Only a line that is nothing but the report is read this way - "i tried that new cafe" is a
# place, not a report on the last answer - and only right after an answer that gave the person
# something to do, so it can never take a turn from a subject of the person's own.
ADVICE_LENGTH = 180
# The same question for a line that is nothing but the report ("it doesnt work", "none of that
# worked"): the answer behind it only has to be long enough to have been advice at all.
ADVICE_LENGTH_BARE = 120
# A warm care line is advice too, and a short one is a whole answer: "go easy on yourself today,
# and see someone if it's not shifting in a few days" is something to do and to report back on,
# and at a hundred characters it never got past the length gate - so "no change" after it was
# answered as a remark about anything at all ("Right - anything else on your mind?"). Length is
# still one way to say "this was advice"; the other is a cue that names something to do. A line
# that only makes conversation ("Hi! What's on your mind?", "You're welcome - shout if anything
# else comes up") has none of these, so a report after one is still a remark.
ADVICE_CUE = re.compile(
    r"\b(?:go easy|take it easy|take it steady|rest|see someone|see (?:your|a) (?:gp|doctor)|"
    r"get it looked at|looked at|worth (?:a|an|seeing|asking|ringing|going|getting|trying)|"
    r"say so to (?:a|your) (?:gp|doctor)|talk to (?:a|your) (?:gp|doctor)|"
    r"tell (?:a|your) (?:gp|doctor|pharmacist)|ask (?:a|your) (?:gp|doctor|pharmacist)|"
    r"ring (?:your|the|us|back|111|999|nhs)|phone (?:your|the|111|999)|make an appointment|"
    r"book (?:an?|your|it)|carry on|keep (?:going|doing|it|walking|an eye|taking|using)|"
    r"try (?:a|an|the|it|this|that|putting|going|starting|taking|walking|keeping)|"
    r"start with|stop (?:it|there|and|doing)|"
    r"leave it (?:off|alone|a)|check (?:the|it|your|whether|that)|top (?:it|the) up|"
    r"apply|cover it|elevate|keep it|write (?:it|down|a|the)|make a note|note down|"
    r"ask (?:for|about|your|the|whether|what)|change one thing)\b")


def _advice_in(last):
    """Was the last answer something the person could do and report back on?"""
    return len(last) >= ADVICE_LENGTH or bool(ADVICE_CUE.search(last.lower()))


# A report on an answer is built from the answer's own words: the oven answer says "wipe it out
# with a damp cloth and a little vinegar" and the person comes back with "i wiped it and now its
# worse" or "i boiled it with vinegar and now its worse". No closed list of report words can hold
# every verb and every thing an answer names, and those words are the whole of the evidence that
# the line is about that answer - so a word the answer used counts as a report word here. What is
# left over still has to be in REPORT_FILLER, which is what keeps "i tried that new cafe" and "i
# wiped it and the dog ate the cloth" out of this reading.
#
# The past forms are built rather than looked up, because people write the step down in the past
# ("wiped", "scrubbed") and an answer says it with the verb or the -ing ("it takes some
# scrubbing"). The irregulars are the ones people use about a repair: "i took it off", "i left it
# on", "i put it back".
IRREGULAR_STEP = {
    "took": "take", "made": "make", "put": "put", "left": "leave", "kept": "keep",
    "set": "set", "cut": "cut", "held": "hold", "stood": "stand", "gave": "give",
    "got": "get", "ran": "run", "brought": "bring", "sent": "send", "found": "find",
    "told": "tell", "did": "do", "dug": "dig", "hung": "hang", "stuck": "stick",
    "bled": "bleed", "tore": "tear", "wore": "wear", "lit": "light",
    "burnt": "burn", "swept": "sweep", "wrung": "wring", "shut": "shut",
    "spun": "spin", "went": "go", "saw": "see", "drew": "draw",
}
# How the upshot is said is part of the report, not a claim about the thing. "i wiped it and now
# its clean" is the answer's own step plus "clean", and the oven answer never uses that word, so
# the gate rejected the line on the one word that was only saying it had worked. These are the
# words a verdict is written in, and each says nothing about a subject of its own. (Not the
# `VERDICT_WORD` regex above, which is chat's list of how a person says a thing annoyed them.)
REPORT_VERDICT_WORD = frozenset((
    "fine", "sorted", "clean", "cleaner", "clear", "cleared", "working", "worked", "works",
    "fixed", "ok", "okay", "normal", "done", "gone", "better", "worse", "good", "great",
    "brilliant", "perfect", "results",
))
NO_STEP = frozenset()


def _the_words_in(advice):
    """The words of an answer, with the past forms a report would write its steps in.

    An answer says a step with an -ing ("it takes some scrubbing", "leave it overnight") as
    often as with the verb itself, so the stem is read too: "scrubbing" gives "scrubbed" and
    "wiping" gives "wiped". Every form is built, never checked, because a form nobody writes
    only ever lets a word be read as one the answer used.
    """
    if not advice:
        return NO_STEP
    said = set(re.findall(r"[a-z']+", str(advice).lower()))
    if not said:
        return NO_STEP
    words = set(said)
    for word in said:
        if len(word) < 3:
            continue
        if word.endswith("ing") and len(word) > 4:
            stem = word[:-3]
            words.add(stem)              # cleaning -> clean
            words.add(stem + "e")        # wiping -> wipe, making -> make
            if stem[-1:] == stem[-2:-1]:
                words.add(stem[:-1])     # scrubbing -> scrub, stopping -> stop
    forms = set(words)
    for word in words:
        if not word:
            continue
        forms.add(word + "ed")               # clean -> cleaned, oil -> oiled
        forms.add(word + "d")                # wipe -> wiped
        forms.add(word + word[-1] + "ed")    # scrub -> scrubbed, stop -> stopped
    for past, base in IRREGULAR_STEP.items():
        if base in words:
            forms.add(past)
    return forms


# The same verdict said as a fact about the thing rather than about the doing: "i wiped it and
# now its worse", "i scrubbed it and its worse now". The step is the answer's own verb (see
# REPORT_FILLER and `_the_words_in`), so all a report of that shape has of its own is the time
# word and the verdict - and read as neither, the line was nobody's: "i wiped it and now its
# worse" after the oven answer was answered as tiredness. "already" counts the same way ("its
# worse already"), and so does the verdict before the time word ("its gone worse now").
# The same report the other way round: the step worked and the thing is done. "i wiped it and now
# its clean" after the oven answer was nobody's - "wiped" is not a report word on its own (see
# `_the_words_in`), so the line reached the chat module, which read it as tiredness, and "i
# cleaned the port and now its fine" was told "You've already cleaned the port". A thing that is
# now fine is the end of the advice, and the answer to it is that it is sorted.
REPORT_NOW_FINE = re.compile(
    r"\b(?:now|already)\s+(?:its|it'?s|it is|they'?re|they are|things are|everything is)\s+"
    r"(?:all |much |a lot |so |loads |back to )?"
    r"(?:fine|sorted|clean|clear|working|fixed|fixed itself|ok|okay|normal|done|gone|"
    r"better|improved)\b"
    r"|\b(?:it|that|this) (?:worked|did it|did the trick|has done it|is sorted)\b"
    r"|\b(?:sorted|fixed) (?:now|already)\b"
    # People put the time word at the front as often as the back: "its working now", "its fine
    # now", "theyre sorted now". The first alternative reads only the front one.
    r"|\b(?:its|it'?s|it is|they'?re|they are|things are)\s+"
    r"(?:all |much |a lot |so |loads )?"
    r"(?:fine|sorted|clean|clear|working|fixed|ok|okay|normal|done|gone|better|improved)"
    r"\s+(?:now|again|already)\b")
WORSE_NOW = (
    r"\b(?:now|already)\s+(?:its|it'?s|it is|they'?re|they are|things are|everything is)\s+"
    r"(?:much |even |far |loads |a lot |so |still )?(?:worse|sorer)\b"
    r"|\b(?:much |even |a lot |far )?(?:worse|sorer)\s+(?:now|already|than before)\b"
    r"|\b(?:got|gets|getting|gone)\s+(?:much\s+|even\s+|a\s+lot\s+)?worse\b")
TRIED_WORSE = re.compile(
    r"\b(?:made (?:it|things|me) (?:worse|sorer)|made me worse)\b|" + WORSE_NOW)
TRIED_NO_CHANGE = re.compile(
    r"\b(?:(?:not|isnt|isn't|not really) (?:helping|helped|working|worked)|"
    # "none of that worked" and "none of it helped" are the same report as "it doesnt work", and
    # they were falling through to the fault reader, which asks about a boiler.
    # Said in the present tense it is the same report and the opposite of helped: "none of it
    # works" after "my laptop is broken" and after "my back hurts when i run" was congratulated
    # - "That's what you want to hear. Carry on with it" and "Good - that is the one to keep
    # doing" - because only the past tense was read and the helped pool took the words "it works"
    # out of the middle of the sentence.
    r"none of (?:that|it|them|these) (?:has |have )?(?:worked|works|helped|helps|done anything|"
    r"been any use|is working|are working)|"
    r"(?:did not|didnt|didn't|does not|doesnt|doesn't|wont|won't) (?:work|help|"
    r"do (?:it|anything|much))|"
    r"(?:hasnt|hasn't) (?:helped|worked)|no (?:change|difference|better|improvement)|"
    r"still the same|same as before|nothing (?:works|is working|has worked|has changed|"
    r"changed|yet|different|so far))\b")
# A report that says the trouble is still there: "ok done that, still dripping". The finished-step
# pool asked "Any change since you started?" of a line that had just said what the change was. It is
# read before the finished-step readings but after the ones that name a good outcome, because the
# person has told the answer the outcome and the only thing left to say is the no-change one.
STILL_THE_TROUBLE = re.compile(
    r"\bstill\b(?![^.?!]*\b(?:working|works|helping|helped|better|fine|good|sorted|"
    r"doing the trick)\b)")
# "still" is in the adverbs because "its still working" is the helped outcome said with a time in
# it, and the reader below takes a bare "still" for the trouble that has not moved.
TRIED_HELPED = re.compile(
    r"\b(?:(?:it|that|this|they)s? (?:is |are |seems? )?"
    r"(?:actually |really |definitely |properly |still )?(?:helping|helped|working|works|"
    r"help a bit|doing the trick)|helped (?:a (?:bit|little|lot|load))|"
    r"(?:a bit|lots|much|loads) better|feeling better|helps a bit)\b")
TRIED_IT = re.compile(
    r"\b(?:(?:i|we|ive|i've|weve|we've|i have|we have|i had|we had) "
    r"(?:did|tried|gave|used|started|have tried|had tried|went with) "
    r"(?:what you (?:said|suggested)|that|this|it)" + WHOLE_LIST_AFTER +
    r"|did what you (?:said|suggested|told me)|"
    r"(?:been|keep|still) (?:doing|trying|taking|walking|using) (?:it|that|this|them))\b")
# The same report with the subject dropped, which is how it is typed mid-conversation: "tried
# that", "tried it already". Anchored like DONE_IT, because "what tried that" is a question
# about somebody else.
TRIED_THAT_ONLY = re.compile(
    r"^(?:(?:ok|okay|alright|right|so|well|yeah|yep|yes|cool|fine|and|but|then|i|we|ive|i've|"
    r"weve|we've)\s+)*"
    r"(?:(?:have|had)\s+)?(?:tried|been trying)\s+(?:it|that|this|them)" + WHOLE_LIST_AFTER + r"\b")
# The report on the whole of it: "ive tried them all", "tried everything", "done them all". Read
# only when the bot's last answer offered nothing to pick from, because after a list of films the
# same words are a turn-down the store owns; after a paragraph of advice they are the person
# saying they have done what it said. Left in that case, the advice answer's second half came back
# as more work to do: "my knee hurts when i run" / "ive tried them all" got "Ice after a run and
# run on softer ground..." after the paragraph that already said it.
# These patterns live in their own file: this one grew past the 1 MB a clone may carry and
# every change to it was refused. Imported here in place of their definitions.
from .fallback_words import (  # noqa: F401 - read here by the patterns below
    ADVICE_AGAIN_ASK,
    ADVICE_COOL_ASK,
    ADVICE_TIME_ASK,
    ADVICE_TIME_WORDS,
    ADVICE_WORSE_ASK,
    AN_ANSWER_ABOUT_A_NO,
    ASKS_WHY,
    BURN_ASK,
    BURN_BLISTER_LINE,
    BURN_ON_IT,
    BURN_THING,
    BURN_WORD,
    CARE_SEEN_ASKS,
    DONE_IT,
    FEELS_BETTER,
    FEELS_NOT_BETTER,
    HYPOTHETICAL,
    IN_HOSPITAL,
    MEDICAL_PLACE,
    MOVE_ON,
    NOT_A_VISIT,
    OWN_NO,
    POP_A_BARE_IT,
    REFUSED,
    REFUSED_FAMILY,
    REFUSED_NOT,
    REFUSED_NO_OBJECT,
    REFUSED_PARTY,
    STILL_GOING,
    TRIED_THE_LOT,
    VISIT_ASK,
)



def _asks_about_the_advice(clean, last):
    """The pool for a question about the advice just given, or None.

    Read only inside a care thread, after the bot has said what to do. Two gates and an order:
    the cooling pool needs an answer that cooled something, and the other three need an answer
    that gave a time. A line that asks what to do if it does not work ("what if it doesnt stop")
    is read before the time ask, which can share its words without being the question.
    """
    if ADVICE_COOL_ASK.search(clean) and any(word in last for word in ADVICE_COOL_WORDS):
        return ADVICE_COOL
    if not ADVICE_TIME_WORDS.search(last):
        return None
    if ADVICE_WORSE_ASK.search(clean):
        return ADVICE_WORSE
    if ADVICE_TIME_ASK.search(clean):
        return ADVICE_TIME
    if ADVICE_AGAIN_ASK.search(clean):
        return ADVICE_AGAIN
    return None


# A line that says someone is with them, or on the way, is the one piece of good news a person
# in an emergency can give. "Do what the emergency line says" answers nothing there: what they
# need is to hear that they are no longer alone with it (#264 followed this up from #205).
# The company needs a person in front of it: "what's wrong with me" contains "with me" and is a
# question about the person themselves, not news that someone arrived. "come in" needs an
# arrival subject too, or a cat wants to come in and gets a line about not being alone.
ARRIVING = re.compile(
    r"\b(?:neighbou?rs?|nurse|doctor|paramedic|ambulance|crew|flatmate|housemate|mate|friend|"
    r"sister|brother|mum|mom|dad|mother|father|carer|midwife|police|son|daughter|wife|husband|"
    r"partner|boyfriend|girlfriend|aunt|uncle|cousin|gran|nan|grandad|grandma)\b")
WITH_YOU = re.compile(
    r"\b(?:(?:is|are|was|were)\s+with\s+me|(?:is|are)\s+here|come\s+over|coming\s+over|"
    r"come\s+round|coming\s+round|on\s+(?:his|her|their|its)\s+way|on\s+the\s+way|"
    r"not\s+on\s+my\s+own|not\s+alone|sitting\s+with|staying\s+with|staying\s+tonight|"
    r"staying\s+the\s+night|next\s+door|neighbours?\s+(?:is|are|coming|here))\b")


def _feels_better(clean):
    """True for a line that says they are easing, and says nothing else.

    "i feel a bit better now" is a report on the emergency; "im ok now, where do i get a tetanus
    jab" is a question that happens to carry an easing, and answering it with "that's a relief"
    drops what the person asked. So the easing words and the thing that was easing are taken out
    and anything with content left means the line is about that instead.
    """
    if not FEELS_BETTER.search(clean) or FEELS_NOT_BETTER.search(clean):
        return False
    if "?" in clean or MOVE_ON.search(clean):
        return False
    for word in re.findall(r"[a-z']+", clean):
        if word in EASING_FILLER or word in SYMPTOM_WORDS or word in BODY_PARTS \
                or word in HEALTH_WORDS:
            continue
        return False
    return True


# The answer above can send them somewhere: "that needs an ambulance now", "ring 111 or your GP
# today", "a joint that won't take weight wants an X-ray today, at A&E". What that answer asked for
# is a route out of the house, so an easing after it is not the end of the thread. Only the opening
# sentence counts, because that is where a card puts the thing to do: the cut-hand card opens on
# the pressure and keeps "if it's still going after ten minutes, ring 999" for later, and a cut
# that eases is the easing to answer.
ROUTE_NAMED = re.compile(
    r"\b(?:999|911|112|111|a\s?&\s?e|a and e|accident and emergency|ambulance|paramedic|"
    r"urgent care|out of hours|x-ray)\b")


def _no_relief(memory, last=""):
    """True when the thread is one where feeling better does not mean being out of danger."""
    lines = [str(last or "")]
    for past in (memory.get("turns") or []):
        if isinstance(past, dict):
            lines.append(str(past.get("user") or ""))
            lines.append(str(past.get("bot") or ""))
    if any(NO_RELIEF.search(line.lower()) for line in lines if line):
        return True
    # A stroke that eases is still a stroke. "Glad to hear it, go steady for the rest of the day"
    # is the wrong thing to tell someone the answer above sent to A&E, so the easing keeps the
    # referral instead of sending them back to their day. A crisis answer is the exception:
    # nobody has been sent out and nothing has come back, so "the worst of it is passing" is the
    # pool an easing wants there.
    for past in (memory.get("turns") or []):
        if not isinstance(past, dict):
            continue
        said = str(past.get("bot") or "")
        if any(word in said.lower() for word in CRISIS_WORDS):
            continue
        opening = re.split(r"(?<=[.?!])\s", said.strip(), 1)[0].lower()
        if opening and ROUTE_NAMED.search(opening):
            return True
    return False


def _someone_is_arriving(clean):
    """True for a line that says someone is with the person, or on the way to them."""
    if WITH_YOU.search(clean):
        return True
    return bool(re.search(r"\b(?:come|coming|let)\s+(?:in|round)\b", clean)
                and ARRIVING.search(clean))

RESOLVED = re.compile(
    r"\b(?:it's|its|it is|that's|thats|that is|this is) (?:out|over|stopped|fine|done|ok|okay|"
    r"under control|settled)\b"
    r"|\bthe \w+ (?:is|has|have|'s) (?:out|stopped|arrived|come|came|gone|cleared|dried up|"
    r"here)\b"
    r"|\b(?:ambulance|paramedics?|fire brigade|fire service|firemen|crew|doctor|nurse|police|"
    r"medics?) (?:is|are|'s|have|has) (?:here|arrived|come|came|been|on the scene)\b"
    r"|\b(?:(?:i'm|im|i am|we're|were|we are|she's|shes|she is|he's|hes|he is|they're|theyre|"
    r"they are|you're|youre|you are) (?:ok|okay|safe|fine|alright|better|out of it))\b"
    r"|\b(?:bleeding|bleed|fire|smoke|pain|it) (?:has |'s )?stopped\b")
# "It's stopped bleeding now but the edges look a bit open": the close is the first half of the
# line, so the half that still needs a person wins and the answer keeps the care pointer.
NEEDS_SEEN = re.compile(
    r"\b(?:open|gaping|gapes|deep|swollen|swelling|infected|numb|dizzy|hurting|hurts|"
    r"throbbing|worse|getting worse|pus|red streaks)\b")
ALREADY_RANG = re.compile(
    r"\b(?:i|we|ive|i've|weve|we've|he|she|they|dad|mum|mom)\s+(?:have\s+|has\s+|already\s+)?"
    r"(?:rang|called|phoned)\b"
    r"|\brang (?:them|999|911|112|an ambulance|the ambulance)\b")
# The numbers that are a conversation rather than a dispatch: a person who has rung the
# samaritans, a crisis line or NHS 111 has done the right thing and nobody is coming to their
# door. The hold pools above are written for the 999 call ("the operator", "the crew are on
# their way", "keep the line open"), so they promised an ambulance that had never been sent.
A_HELPLINE = re.compile(
    r"\b(?:samaritans|116\s?123|988|crisis (?:line|text|team|service|number)|helpline|help line|"
    r"shout|papyrus|nhs\s?111|111|doctor|gp|surgery|out of hours|vet)\b")
# said about the speaker, not about the patient: "my mum is shaking" is a symptom and gets
# care advice, "i can't stop shaking" is the person and gets the pool above.
ABOUT_THE_SPEAKER = re.compile(r"\b(?:i|i'm|im|i am|i've|ive)\b")
FRIGHTENED = re.compile(
    r"\b(?:scared|afraid|frightened|terrified|fear|fearful|panicking|panic|shaking|shaken|"
    r"trembling|dreading|dread|shocked|in shock|crying|in tears)\b")
# "im not scared", "nothing to be scared of": a line that turns the fear off is not the fear.
NOT_FRIGHTENED = re.compile(
    r"\b(?:not|never|no|nothing|isn't|isnt|aren't|arent|wasn't|dont|don't|doesn't)\b"
    r"(?:\s+\w+){0,3}\s+(?:scared|afraid|frightened|terrified|fear|panicking|panic|shaking|"
    r"trembling|shocked|crying)\b")
# A card that *tells* the person to ring, against one that only names the number as a threshold:
# "ring 999 now" is an emergency the bot is standing in the middle of, "if it won't stop, that's
# 999 or 911" is first aid that has just handed the person a red flag. The difference is the verb
# in front of the number, and it decides what the next line is: after the first aid the person
# wants the care line the card leaves ("get it looked at today"), not "ring 999 or 911 now" a
# second time for a cat scratch.
CALL_THEM_NOW = re.compile(
    r"\b(?:ring|call|phone|dial)\b(?:\s+\w+){0,3}\s*(?:999|911|112|an ambulance|the ambulance|"
    r"emergency services|the emergency services)\b")
# A first-aid card names the red flag as well as the care line, and the person's next line can be
# that flag met rather than a new subject. The fall card is the clear one: it hands over "cannot
# get up or put weight on it, who hit their head" as the point where the answer becomes 999, and
# then "im on blood thinners" or "it really hurts when i stand on it" is the same injury said
# worse. Because the card only names the number as a threshold, `CALL_THEM_NOW` reads the thread
# as not live and the person is sent to a pharmacist with a broken hip (quality watch, foo-06 and
# foo-07). These are the words that turn watch-it-&-see into ring-now, and the fall card is the
# one they turn; a scratch on a blood thinner is still a scratch.
STAKES_WORDS = re.compile(
    r"\b(?:blood ?thinners?|warfarin|apixaban|rivaroxaban|dabigatran|edoxaban|clopidogrel|"
    r"heparin|anticoagulants?)\b"
    r"|\b(?:i'?m|im|hes|he'?s|shes|she'?s|my (?:mum|dad|mother|father|husband|wife|partner|"
    r"gran|grandma|grandad|grandpa|nan))\s+(?:7|8|9)\d\b"
    r"|\b(?:7|8|9)\d\s*(?:years? old|years|yo)\b"
    r"|\b(?:can'?t|cannot|can not)\s+(?:put\s+)?(?:any\s+)?weight\b"
    r"|\b(?:confused|not with it|passed out|knocked out|blacked out|unconscious)\b"
    r"|\b(?:hurts?|agony|killing me|painful)\b[^.]{0,25}\b(?:stand|standing|walk|walking|"
    r"step|stepping|put weight)\b", re.I)
# The card those words make worse: first aid for a fall or a bang, where age, a blood thinner and
# not being able to weight-bear are exactly what turns "watch it" into "ring 999".
FALL_FIRST_AID = re.compile(
    r"\b(?:put weight|cannot get up|can'?t get up|hit (?:their|your|his|her) head|"
    r"head injury|fell|fall|bruising)\b", re.I)
# Words that keep a line inside an emergency the bot has just answered: the emergency itself,
# the injury, the people in it, and the practical questions people ask mid-crisis.
CARE_WORDS = frozenset("""
    safe safely unsafe outside out stairs stair lift door window smoke fire fires flame flames
    alarm spread spreading burn burned burning bleed bleeding blood cut cuts wound bandage
    dressing plaster pain painful hurt hurts hurting aching sore tender stinging smarting
    stiff swollen swelling bruised numb infected infection throbbing
    aspirin paracetamol ibuprofen painkiller painkillers antihistamine
    worse still soak soaking soaked wait waiting
    ambulance paramedic police operator emergency 999 911 112 doctor hospital nurse gp
    stitches stitch tetanus dressing nurse nhs walk-in centre clinic
    checked check conscious breathing breath awake faint dizzy vomit vomiting sick throwing
    collapsed collapse seizure stroke heart chest epipen inhaler insulin medicine dose
    cpr defib firefighter neighbour neighbor flat floor basement roof shaken shaking scared he she him
    her them they their there call calling rang ring
""".split())
# The weak half of that vocabulary: a pointer, not the incident. "should i call the plumber
# about the boiler" and "is there anything good on tv tonight" are ordinary lines that happen to
# carry one, so these words hold the thread only while the line brings no topic of its own.
# The injury itself, still going: "it's still stinging an hour later", "it's throbbing". A line
# that reports the damage needs the same thread even when some word of it reads as a topic of
# its own ("hour" is maths-and-numbers), so these are read before the line's own topic is.
CARE_HURTS = frozenset("""
    sting stings stinging stung throbs throbbing throbbed ache aches aching ached sore tender
    hurts hurting hurt pain painful swollen swelling bled blister blistered blisters
""".split())
CARE_POINTER = frozenset("""
    there call calling rang ring still wait waiting check checked out outside
""".split())
# "Out" is only a pointer when it is the speaker's own way out of the emergency ("am i out of
# danger", "should i go outside"). In "how do i get out of a parking ticket" the "out of" belongs
# to the ticket: it is a question about a thing, and reading it as a pointer answered a person in a
# heart-attack thread with "ring 999 or 911 now" about a parking fine (frank-shrew, #routing).
# The things you get out of *before* the emergency - a house that is filling with smoke, a car that
# has stopped in a live lane - are the way out and stay with the thread.
_POINTER_OWN_OBJECT = re.compile(
    r"\b(?:get|gets|getting|got|gotten|opt|opts|opting|opted|back|backs|backing|come|comes|"
    r"coming|came|pull|pulls|pulling|pulled|drop|drops|dropping|talk|talks|talking|talked|"
    r"sign|signs|signing|signed|wriggle\w*|wiggle\w*)\s+(?:me\s+|myself\s+)?out\s+of\s+"
    # "get out of it" / "get out of there" is the emergency itself, so a pronoun is left to the
    # pointer rule; "get out of this contract" names a thing and is not. A pronoun is the emergency
    # whatever follows it - "how do i get out of it fast" was read as an own object because "fast"
    # came after it - so only "this/that/there/here" need the end-of-line test, since a contract or
    # a hole follows those and a pronoun does not.
    r"(?!(?:it|them)\b)"
    r"(?!(?:this|that|these|those|there|here)\b\s*(?:$|[,.?!]))"
    r"(?!(?:(?:a|an|the|my|our|your|his|her|their)\s+)?(?:house|home|flat|building|block|"
    r"room|kitchen|bathroom|bedroom|bed|bath|car|van|vehicle|lift|elevator|water|door|way)\b)",
    re.I)
# The house words in that vocabulary are also the words of a household fault: "door", "window",
# "floor", "stairs", "flat", "roof". A fault said *of the house* is a DIY line, not the incident,
# so the burn thread must not answer "ok. also the oven door doesnt shut properly" with "keep an
# eye on it". Only the house thing as the subject of the fault counts: "the door is hot",
# "should i open the window" and "the smoke is coming under the door" are the incident, and
# "dont open the door" has the verb first, so none of them read as a fault (gray-palm, #routing).
HOUSE_FAULT = re.compile(
    r"\b(?:door|doors|window|windows|hob|oven|cooker|fridge|freezer|"
    r"washer|washing machine|dishwasher|boiler|radiator|tap|toilet|sink|cupboard|drawer|"
    r"handle|hinge|lock|seal|fan|element|shelf|stairs|stair|step|blind|shutter)\b"
    r"(?:\s+\S+){0,3}?\s+"
    r"(?:(?:doesnt|does not|dont|do not|wont|will not|isnt|is not|not)\s+"
    r"(?:shut|shuts|shutting|close|closes|closing|open|opens|opening|work|works|working|"
    r"fit|fits|fitting|lock|locks|locking|stay|stays|staying|sit|sits|properly|right)"
    r"|is\s+(?:broken|busted|jammed|stuck|loose|snapped|cracked|hanging)"
    r"|has\s+(?:snapped|come off|fallen off))"
    r"|\b(?:does|do)\s+(?:the|that|this|my|our)\s+(?:\w+\s+){0,2}"
    r"(?:door|window|hob|oven|cooker|fridge|freezer|tap|toilet|sink|cupboard|drawer|"
    r"handle|lock|shelf|stairs)\s+(?:shut|close|open|work|fit|lock)\b",
    re.I)
CARE_ASKS = re.compile(
    r"\b(what|where|who) (do|should|can) (i|we) (do|go|ring|call|use|tell)\b"
    r"|\bis (it|he|she|that) (safe|ok|okay|normal|bad)\b"
    r"|\bhow (do|can) i (help|stop|treat)\b")
STILL_HERE = re.compile(
    r"\b(?:can|could|do|did)\s+(?:you|u)\s+(?:hear|see|read|understand|get)\s+(?:me|this)\b"
    r"|\b(?:are|r)\s+(?:you|u)\s+(?:still\s+)?(?:there|here|with\s+me|listening|awake)\b"
    r"|\byou\s+(?:still\s+)?(?:there|listening)\b"
    r"|\banyone\s+there\b")


def _is_presence_check(clean):
    """True when the line is only "are you there / can you hear me", and nothing more."""
    match = STILL_HERE.search(clean)
    if not match:
        return False
    rest = re.findall(r"[a-z']+", clean[:match.start()] + " " + clean[match.end():])
    return len(rest) <= 2 and all(word in PRESENCE_LEFTOVER for word in rest)


# "can you remember what i told you at the start", "do you remember what my boiler is doing":
# the asking-in-front-of-it form of a recall. The store keeps the line and can answer it, so the
# capability card ("nothing from before this chat, sorry") is the wrong reply and stands down.
RECALL_TAIL = re.compile(
    r"\bwhat (?:i|we) (?:told|said|asked|mentioned|wanted|needed)\b"
    r"|\bat the (?:start|beginning|outset)\b"
    r"|\bearlier\b|\bso far\b|\bwhen we (?:started|began|were)\b"
    r"|\bhow (?:this|we|the chat|it) (?:started|began)\b"
    r"|\bwhat i (?:was|have been) (?:on about|talking about)\b")

def _the_store_takes_it(clean):
    """The card stands down only on a line the memory store will answer.

    Two regexes that drift are how one line loses both answers: a recall tail that stood the
    card down on its own sent "can you remember anything so far" and "do you remember what i
    said at the beginning of this chat" to a search hedge, which is a worse reply than the card
    that was there before. So the store is asked, not guessed at - it keeps `FIRST_ASK`, and a
    line it does not claim keeps the card.
    """
    from ..modules.memory_store import FIRST_ASK

    return FIRST_ASK.search(clean) is not None


# "what are you" is the identity question only when the line stops there. A verb after it makes
# the line about the verb - "what are you watching", "what are you doing", "what are you making
# for tea" - and the phrase list took all three, so a person asking what to watch tonight got a
# description of the bot (main 2a8d7caf, from #5085 claiming the `identity` kind). The narrower
# shapes above are unaffected: they name the human or the bot, which no verb does.
# "what are you good at", "what are you best at": the ask for what the bot can do, said about
# the bot. The feeling reader takes "good" as a mood word and answered it "No feelings like
# yours, so nothing to get worked up about", which is a reply to a question nobody asked.
GOOD_AT_ASK = re.compile(r"\bwhat are you\s+(?:good|best)\s+at\b")
# "what are you wearing", "what are you wearing to the wedding": a clothes question about a
# body, and the bot has none. The feeling reader takes "wearing" as a mood word ("worn
# down") and answered the clothes line "None of that in a program - no moods, no bad days".
CLOTHES_ASK = re.compile(r"\bwhat are you\s+(?:wearing|going to wear|putting on)\b")
# "what are you like": the idiom, and the same ask as "what sort of thing are you". The
# feeling reader answered it as a mood question, which it is not.
LIKE_ASK = re.compile(r"\bwhat are you\s+(?:like|like then|like as a (?:bot|program))\b")
# "what are you a robot", "what are you, a chatbot": the noun after the words names what it is,
# so the line is the self-description even without the comma or the small-talk tail.
WHAT_ARE_YOU_NOUN = re.compile(
    r"\bwhat are you\s*,?\s*(?:a\s+(?:bot|robot|ai|chatbot|person|human|program(?:me)?)\b)|"
    # "what are you made of", "what are you built from": what it is, not what it is doing.
    r"\bwhat are you\s+(?:made|built|running|based)\s+(?:of|from|on|out of)\b")
WHAT_ARE_YOU = re.compile(
    r"\bwhat are you\b"
    # the line stops there, or asks with a small-talk tail: "what are you then", "really". "up to"
    # is not in the list: "what are you up to" asks what the bot is doing, and the honest answer
    # ("nothing of my own - what are you up to?") is a better reply than the self-description.
    r"(?=\s*(?:[?.!,]|$|\b(?:then|exactly|really|anyway|actually|currently|"
    r"at\s+the\s+moment|these\s+days)\b))"
    # or it asks what the bot does something for: "what are you using my data for" is about the
    # bot's use of the data, not about a data plan, and it was the self-description before.
    r"|\bwhat are you\b[^.?!]{0,40}?\bfor\s*[?.!]*$")
# A verb after "what are you" takes the line away from the self-description only when something
# can answer it: "what are you watching" has a film pick, "what are you making for tea" has the
# dinner card, but "what are you reading", "what are you good at" and "what are you afraid of"
# have no answer of their own, and standing the identity card down on those turned a vague truth
# ("I'm a chatbot - here to help and chat") into a search hedge or a mood line that does not fit
# the question. So the knowledge base is asked, not guessed at, the same way `_the_store_takes_it`
# asks the memory store before standing the recall card down.
def _the_answers_take_it(clean):
    """Whether the knowledge module will answer this line itself.

    Read only in the identity check, so the cost is one answer on lines that start "what are
    you". It has to be the module's own answer and not a lookup hit: `what are you eating` and
    `what are you seeing` reach an entry (`city-next`) that then has nothing to say about them,
    so an entry found is not an answer given. The memory store is asked the same way in
    `_the_store_takes_it`: the module that owns the answer says whether it has one.
    """
    try:
        from ..modules import answers

        return answers.respond(clean, {}) is not None
    except Exception:
        return False
# The same question the other way round: "will you forget this chat", "are you going to forget
# me", "will you forget what i said". Every one of them was answered by a pool that knows nothing
# about this bot - "That's beyond what I know well, sorry. Searching for it will turn up better
# sources" - or, for "will you forget what i said", by the card about a person's own memory loss.
# What they are asking is whether the chat is kept, which the memory answer says exactly.
# ...and the same question in every other auxiliary a person uses, because "will you forget" was
# the only one read. "do you forget things" and "can you forget things" were answered with the card
# about a person's own memory loss ("Most forgetting is not a lost file"), "did you forget what i
# said" with the card about a blank mid-sentence, and "have you forgotten already" and "have you
# forgotten me" with a search hedge. The bot is the one being asked about, and the memory answer is
# the honest one.
#
# Two wh-words in front are the fence: "how do you forget someone" and "why do you forget things"
# are questions about forgetting itself, and they keep their own answers. "What do you forget"
# stays with the bot, because what it forgets is the start of the conversation.
FORGETTING_ASK = re.compile(
    r"(?<!how )(?<!why )(?<!when )"
    r"\b(?:will|would|won'?t|do|does|did|can|could|have|has)\s+(?:you|u)\s+"
    r"(?:ever\s+|just\s+|soon\s+|really\s+|still\s+|already\s+|now\s+|then\s+)?"
    r"(?:forget|forgot|forgotten)\b"
    # ...unless it is somebody's errand: "did you forget to ring the vet", "did you forget
    # the milk". What makes a forgetting question one for the bot is what it names - what i
    # said, me, things, already, our chat - so an infinitive or a bare definite noun after
    # the verb is the person's own list and not this answer.
    r"(?!\s+(?:to\s+\w+|(?:the|your|my|his|her|their|a|an)\s+\w))"
    r"|\b(?:are|r)\s+(?:you|u)\s+(?:already\s+)?(?:going|gonna)\s+to\s+forget\b"
    r"|\b(?:are|r)\s+(?:you|u)\s+(?:already\s+)?forgetting\b", re.I)
# A capability ask that names a topic ("what can you help me cook tonight") is not answered
# with a tour of every domain: the honest, useful reply stays inside the topic and asks for
# the next detail. The topic is the one the engine read, so this needs no per-line matching.
HELP_TOPIC_ASK = re.compile(
    r"\b(?:what|how) (?:can|could) you (?:help|do)\b|\bwhat do you do\b|"
    r"\bwhat are you good at\b")

# The same ask with a word in front of it: "what else can you do", "what more could you do",
# "anything else you can do". The understanding engine reads the bare phrase (and its fillers,
# "actually", "exactly"), but `else` is not a filler - dropping it would change every line with
# "else" in it - so the word in front of the ask hides the capability answer, and a shrug is the
# worst possible answer to the first question a person asks a bot. The verb has to be the bot
# offering something and a "you" has to be there, so "what else can i cook with mince" and
# "anything else you want to tell me" stay ordinary lines. "what else can you do about my
# leaking boiler" is the same shape, and it stays ordinary too: see HELP_TAIL below.
HELP_ELSE = re.compile(
    r"\b(?:what|which)\s+(?:else|other|more)\b[^.?]{0,25}?"
    r"\b(?:can|could|do|does)\s+you\s+(?:do|help|offer|manage|cover)\b([^.?]*)"
    r"|\b(?:anything|something)\s+else\b[^.?]{0,20}?\byou\s+(?:can|could)\s+"
    r"(?:do|help|offer)\b([^.?]*)")


def _free_tail(tail):
    """True when nothing but subject-free words follow the offer."""
    return all(word in HELP_TAIL for word in re.findall(r"[a-z']+", tail or ""))


# Tastes: STYLE.md lets the bot have opinions ("I'd pick the train"), so a question about what
# it likes gets one. Sending someone off to search for the bot's own preference is not a reply.
# A bare choice ("Tea or coffee?") is an opinion ask too: two things, no verb.
CHOICE = re.compile(r"^[a-z' ]{2,20} or (?:the )?[a-z' ]{2,20}\??$")

# "is that ok or am i overreacting" has the shape of a choice and is not one: it asks to be told
# whether a feeling is fair, and answering "either is fine" there dismisses the worry. The tell
# is a second question, which needs a helper verb and its subject ("am i", "is that", "do you").
# "should i text him or call" has no such tail and is a real choice; the helper in the first half
# does not disqualify it.
CHOICE_WORRY = re.compile(r"\b(?:am|is|are|was|were|do|does|did)\s+"
                          r"(?:i|you|we|they|he|she|it|there|that|this)\b")

# How people put a choice to someone else: the frame in front of the first thing is the question,
# not one of the two things. "Should we get a pizza or a curry tonight" is pizza against curry, so
# the frame comes off before the line is read as a choice - otherwise the first side is "should we
# get a pizza", which is what the pick used to say back ("I'd go *Should we get a pizza*"): a bot
# quoting its own question mark as one of the options. The article goes with it, because "a pizza"
# against "a curry" is still pizza against curry.
CHOICE_FRAME = re.compile(
    r"^(?:"
    r"(?:should|shall|do|can|could|would|will|might)\s+(?:i|we|you|u)\s+"
    r"(?:get|have|buy|go\s+for|pick|choose|take|do|order|book|eat|drink|watch)?\s*"
    r"|(?:i|we)\s+(?:could|might|would|will)\s+"
    r"(?:get|have|buy|go\s+for|pick|choose|take|do|order|book|eat|drink|watch)?\s*"
    r"|(?:how\s+about|what\s+about|maybe|perhaps|instead\s+of)\s+"
    r")")
CHOICE_ARTICLE = re.compile(r"^(?:the|a|an)\s+")


# A choice put to the bot as a joint decision: "should we get a pizza or a curry tonight",
# "would you get a kitten or an older cat". "should i" is not this frame - that is the person's
# own life, and it asks for advice rather than for the bot's taste.
JOINT_FRAME = re.compile(
    r"^(?:should|shall|do|can|could|would|will|might)\s+(?:we|you|u)\b")


def _choice_advice(clean):
    """`clean` with a joint question frame taken off, for the advice-word test."""
    return _unframed(clean) if JOINT_FRAME.match(str(clean or "").strip()) else clean


def _unframed(clean):
    """`clean` without the question frame in front of a choice, and without its article."""
    line = CHOICE_FRAME.sub("", str(clean or "").strip())
    line = CHOICE_ARTICLE.sub("", line.strip())
    return line.strip()


# A refusal in front of the pair is a constraint, not a question of which: "i dont want pasta or
# rice tonight" was answered "I dont want pasta. I'd take that and not think about it again" -
# the bot picking one of the two things the person had just turned down - and "not pizza or
# curry" was quoted back as an option ("If you were hoping I'd say 'not pizza'"). The person has
# ruled both out, so there is nothing to pick between; the refusal and the domain cards answer it.
CHOICE_REFUSED = re.compile(
    r"^\s*(?:no|not|never|without|neither)\b"
    r"|\b(?:dont|don'?t|do not|doesnt|doesn'?t|didnt|didn'?t|cant|can'?t|cannot|won'?t|"
    r"wouldnt|wouldn'?t|shouldnt|shouldn'?t)\s+(?:\w+\s+){0,2}?"
    r"(?:want|wants|like|likes|love|eat|eating|have|having|drink|wear|do|doing|need|use|"
    r"fancy|stand|bother|manage)\b"
    r"|\ballergic\b|\bhate\b|\bcant have\b")


def _refuses_the_pair(clean):
    """True when the line turns both things down instead of asking which to take."""
    head = str(clean or "").split(" or ")[0]
    return bool(CHOICE_REFUSED.search(head))


def _is_a_choice(clean):
    """True for a bare "x or y" that names two things, not a question with a clause in it."""
    # "early or late" is one scale about one thing, not two things to pick between: "is easter
    # early or late this year" has the shape of a choice and asks where the date falls, and
    # "toss a coin" is a shrug at a question the calendar answers. The pairs live in the reading
    # so this and the `choice` ask agree on what a choice is.
    asked = CHOICE.match(clean) or CHOICE.match(_unframed(clean))
    return (bool(asked) and not CHOICE_WORRY.search(clean)
            and not two_ends_of_one_scale(clean)
            and not _refuses_the_pair(clean))


# "Which would you pick?" is a different question from "cats or dogs?": the choice is on the
# table already, usually in the answer the bot has just given ("*Groundhog Day* for comedy,
# *Knives Out* for a clever whodunnit, or *Arrival* if you'd rather think"). A friend picks one
# and says what tilts it; the search hedge ("I'd rather not guess") and the self-check of the
# identity pool ("I'm a chatbot, not a person") both answer nothing at all. STYLE.md lets the bot
# have a taste ("I'd pick the train"), and the honest version of that taste is one of the options
# it has just offered, so it costs no fact.
PICK_ASK = re.compile(
    r"\b(?:what|which|who)\s+(?:would|will|should|shall|do|did)\s+(?:you|u|ya)\s+"
    r"(?:pick|choose|get|buy|take|go\s+for|suggest|recommend|prefer)\b"
    r"|\b(?:what|which)\s+(?:do|would)\s+(?:you|u|ya)\s+(?:suggest|recommend|pick|prefer)\b"
    r"|\bwhich\s+one\s+(?:would|do|should|will)?\s*(?:you|u|ya)\b"
    r"|\b(?:any|some|got\s+any)\s+(?:suggestions?|recommendations?)\s*\??$")

# The words a line can be made of and still be asking the bot's own pick: the ask, the person
# and the plumbing, and nothing else. A line with anything outside this set names something
# ("what would you get a 5 year old for christmas", "what would you suggest for my back") and
# keeps its own answer, because there is a fact to look up rather than a taste to give.
# "What would you do?" is the same ask as "which would you get?" once the bot has named the
# options: the person is handing the decision back. With nothing on the table it is a question
# about their situation ("my mum died last week", "my landlord won't fix the boiler"), and the
# pools that read that keep it, so it is only a pick when a choice was already answered.
PICK_BACK = re.compile(
    r"^(?:and\s+)?(?:what|which)(?:\s+one)?\s+(?:would|do|did|should|will)\s+(?:you|u|ya)\s+do"
    r"(?:\s+(?:then|now|yourself))?\s*\??$")
PICK_WORD = re.compile(r"[a-z0-9']+")
# The option itself, as the bot offered it (a title in italics), and what the bot said about it:
# "*Knives Out* for a clever whodunnit".
PICK_TITLE = re.compile(r"\*([^*\n]{1,70})\*")
PICK_NOTE = re.compile(r"\s*(?:for|if|when|with)\s+([^.;,*)!?]{2,60})")
# "Suggest" and "recommend" are the same words whether the person wants a taste or advice, so a
# line asking that way with nothing offered is left to the pools that know the difference.
PICK_ADVICE = re.compile(r"\b(?:suggest|suggestions?|recommend|recommendations?)\b")
# "What would you do" is not a request for a pick (that is `PICK_ASK`), but after a trade-off it
# is asking the bot to lean, which is a different question from "what should I do about my knee".
# "what do i do" is not here: it is the how-to ask ("my boiler wont light but it is freezing /
# what do i do"), and a heating fault in winter answered with a pick between two sides is a coin
# flip. The lean answers "what *would* you do", "which would you pick" and "help me decide".
LEAN_ASK = re.compile(r"\b(?:what|which)\s+(?:would|should)\s+(?:you|u|ya)\b"
                      r"|\bwhich one(?:\s+would\s+you\b)?"
                      r"|\bhelp me decide\b")

# A trade-off the person has put down in their own words: "one pays more but the people are nicer
# in the other". The side after the "but" is the side they are committing to - that is what "but"
# does in speech - so a bare "what would you do" or "which would you choose" after one is a
# question a friend can answer: they say which side they would take and why. The answer picks the
# second side by name, because the reading has already checked that the span it came from has two
# sides in it - it does not hand the person their own sentence back, which STYLE.md forbids.
TRADE_OFF = re.compile(r"\b([a-z0-9][^.!?;]{2,70}?)\s+but\s+([^.!?;]{2,70})", re.I)
# The side after the but is not a side when it is a report of how something went ("i tried that
# but it didnt work", "the cream helped but its still sore"): there is nothing there to lean on.
NOT_A_SIDE = re.compile(r"\b(?:didnt|doesnt|don|did not|does not|no|not|never|nothing|still|"
                        r"stopped|failed|worse|hurts|hurting|sore|tried|again)\b", re.I)
# A side that is a verdict on the thing ("the job pays well but i hate it", "the flat is lovely
# but the neighbours are awful") is not a side to take: leaning on it tells a person to take the
# neighbours who are awful. A missed lean is a punt; a wrong lean is worse than main.
NOT_A_CHOICE = re.compile(r"\b(?:hate[sd]?|awful|terrible|horrible|dreadful|miserable|toxic|rude|"
                          r"nasty|worst|unbearable|disgusting|useless|pointless|exhausting|"
                          r"can'?t\s+stand|cant\s+stand|sick\s+of|fed\s+up|driving\s+me\s+mad)\b",
                          re.I)
# The side after the but, as the thing to pick rather than as a sentence about it: "the other has
# better brakes" is "the one with better brakes", "further from work" is "the one further from
# work", "the people are nicer in the other" is "the one where the people are nicer". A side that
# fits none of those shapes is not named, and nothing leans (see `_a_named_side`).
SIDE_HAS = re.compile(r"^(?:has|have|had)\s+(.+)$", re.I)
SIDE_IS = re.compile(r"^(?:it\s+is|it's|its|it\s+was|they\s+are|they're|she\s+is|he\s+is|"
                     r"that\s+is|that\s+are|that\s+was|that\s+were)\s+(.+)$", re.I)
SIDE_SUBJECT = re.compile(r"^(?:the|a|an|my|his|her|their|our|that|this|she|he|they|we|there)\b",
                          re.I)
SIDE_VERB = re.compile(r"\b(?:is|are|was|were|pays|costs|takes|gives|lasts|has|have|means|"
                       r"feels|sounds)\b", re.I)
# Whether the side after the but is the one worth wanting. "one is cheaper but the other has
# better brakes" is a plus after the but; "i like the office but the commute is grim" is a
# complaint, and naming it as the pick says to take the commute. So a side that reads as bad and
# not also as good is not named, and the line keeps the punt it had.
SIDE_GOOD = re.compile(r"\b(?:nicer|better|friendlier|closer|cheaper|bigger|quieter|cleaner|"
                       r"brighter|warmer|safer|newer|faster|kinder|easier|lighter|shorter|"
                       r"flexible|lovely|great|good|perfect|ideal|pays|earns|more\s+\w+)\b", re.I)
SIDE_BAD = re.compile(r"\b(?:grim|bad|worse|worst|less|fewer|painful|boring|stressful|noisy|"
                      r"dirty|loud|busy|cramped|old|small|tiny|dangerous|risky|annoying|"
                      r"exhausting|unpaid|long|longer|slow|further|farther|expensive|price|prices|"
                      r"priced|cost|costs|fee|fees|high|dear|commute)\b", re.I)
SIDE_ONE = re.compile(r"^((?:the|my|this|that|her|his|their)\s+\w+\s+one)\b\s*(.*)$", re.I)
SIDE_COPULA = re.compile(r"\b(?:is|are|was|were|isn't|aren't)\b", re.I)
SIDE_TAIL = re.compile(r"\s+(?:in|of|out\s+of)\s+(?:the\s+)?other(?:\s+one)?$", re.I)
SIDE_OTHER = re.compile(r"^(?:the\s+)?other(?:\s+one)?\s+", re.I)

# "i want to quit but i need the money" is not two options: it is a want and the thing in the
# way, and the side after the but there is the obstacle, so leaning on it tells a person who wants
# to leave their job to stay in it. Two things they could choose is the shape that can be leaned
# on, so a want on the near side or a cost on the far side stands the reading down.
DESIRE = re.compile(r"\b(?:i|we)\s+(?:really |just |so )?(?:want|wanna|would love|id love|need|"
                    r"wish|hope|keep wanting|have to)\b", re.I)
OBSTACLE = re.compile(r"\b(?:too|afford|rent|money|cost|time|hours|nervous|scared|worried|"
                      r"anxious|hard|tight|far|means|landlord|feel bad|guilt|awkward|risk)\b",
                      re.I)
# A trade-off about a body, a feeling or somebody in care is not one to take a side on: "my back is
# killing me but i cant take time off work" / "what would you do" is a question about the pain, and
# answering "I'd take the half after the but" tells a person with a bad back to keep working.
# Read as words anywhere in the line, because the trade-off is the whole of it, not the span.
LEAN_NOT = re.compile(r"\b(?:sad|low|down|depress\w*|unhappy|miserable|lonely|crying|cry|"
                      r"grief|dying|died|death|funeral|diagnos\w*|cancer|checkup|"
                      r"worried|worry|worries|anxious|scared|afraid|panic\w*)\b", re.I)


# How a person types a choice: the helper verb in front of one side is not part of the thing
# ("should i text him" is "text him"), and a trailing "then" or "instead" is the person still
# thinking aloud rather than a third option.
CHOICE_SIDE_LEAD = re.compile(r"^(?:(?:should|shall|do|can|could|would|will|might|maybe)\s+i\s+)")
CHOICE_SIDE_TAIL = re.compile(r"\s+(?:then|instead|though|really)$")
# "chinese or indian tonight" names a dinner and a night, not "indian tonight": the pick is the
# thing, so a time word hanging off the end of a side comes off with the rest of the thinking out
# loud. "with dinner" stays - "beer with dinner" is the whole option.
CHOICE_SIDE_WHEN = re.compile(
    r"\s+(?:tonight|today|tomorrow|now|instead|this\s+(?:evening|afternoon|morning|weekend|week))$")

# "his side or mine", "my side or theirs": the same two people without a word this list has.
CHOICE_PERSON_SIDE = re.compile(
    r"\b(?:my|his|her|their|our|your)\s+side\b|\b(?:his|her|their)\s+(?:family|mum|dad|parents)\b")


# Two steps of one job are not two things to choose between: "mop first or hoover first", "dust
# the shelves or hoover first", "fold the washing or hang it out first", "wipe the sides before
# or after the floor". The light-choice pool took a side on all four because the shape is the
# same shape as "pizza or curry", and the side it took was a claim about the work rather than a
# taste: "Mop first" undoes the hoovering, and "Fold the washing" folds washing that has not been
# hung out. The bot has no taste about the order a job is done in, so it does not pick; it says
# the rule that decides it, which holds for nearly every pair of steps - the one that would spoil
# the other has to come last - and lets the person apply it to their own job.
ORDER_SIDE_END = re.compile(r"\b(?:first|last)$", re.I)
ORDER_BEFORE_AFTER = re.compile(r"\b(?:before|after)\s+or\s+(?:before|after)\b", re.I)
ORDER_OF_WORK = (
    "The step that would spoil the other one goes last, so nothing gets done twice. What are you "
    "doing it on?",
    "Work it out rather than guess: whatever makes a mess for the other step to clear up goes "
    "first. Which job is it?",
    "That is an order to work out, not a taste to pick: the messy step before the tidy one, and "
    "dry before wet. What are you doing?",
)


ORDER_WORD_TAIL = re.compile(r"\s*\b(?:first|last)\b\s*$", re.I)
ORDER_WORD_LEAD = re.compile(r"^\s*\b(?:before|after)\b\s*", re.I)
# "first or second gear" and "my first or my second" name two positions, not two steps of a job:
# a side with nothing left in it once the order word is gone is not a step.
ORDER_ONLY = frozenset("""first second third fourth fifth last later earlier next middle
    start end beginning one""".split())


def _an_order_of_work(sides, clean):
    """True when the two options are the steps of one job rather than two things to pick from.

    Read on the ends of the sides, so "tea or coffee first thing" (a time, not an order) is left
    alone, and on the "before or after" pair, which names the order without ever saying "first".
    """
    if ORDER_BEFORE_AFTER.search(str(clean or "")):
        return True
    if not any(ORDER_SIDE_END.search(side) for side in sides or ()):
        return False
    for side in sides:
        core = ORDER_WORD_TAIL.sub("", ORDER_WORD_LEAD.sub("", side)).strip()
        core = CHOICE_ARTICLE.sub("", core).strip()
        if core in ORDER_ONLY or len(core) < 2:
            return False
    return True


def _choice_sides(clean):
    """The two things a bare choice names, as the person typed them, or None.

    Only the shape `CHOICE` already matched comes here, so the two halves are short and there is
    one "or" between them. Each side loses the helper verb in front of it ("should i text him") and
    a trailing "then"/"instead", and one side with nothing in it leaves None: a pick needs two
    things to pick between.
    """
    parts = _unframed(clean).rstrip("?").split(" or ")
    if len(parts) != 2:
        return None
    sides = []
    for part in parts:
        side = CHOICE_SIDE_TAIL.sub("", CHOICE_SIDE_LEAD.sub("", part.strip()))
        side = CHOICE_SIDE_WHEN.sub("", side.strip())
        side = CHOICE_ARTICLE.sub("", side.strip()).strip()
        if not side or not re.search(r"[a-z]", side):
            return None
        sides.append(side)
    return sides


def _capital(side):
    """`side` with its first letter as a capital, which is how a name or an option starts."""
    side = " ".join(str(side or "").split())
    return side[0].upper() + side[1:] if side else side


def _named(side, memory=None):
    """`side` with any name in it spelled the way the person spelled it."""
    understood = (memory or {}).get("understood") or {}
    for entity in understood.get("entities") or ():
        if not isinstance(entity, dict) or entity.get("type") not in NAMED_TYPES:
            continue
        name = str(entity.get("text") or "").strip()
        if len(name) < 2 or name.lower() not in side:
            continue
        side = re.sub(r"\b" + re.escape(name.lower()) + r"\b", name, side)
    return side


def _a_pick(sides, clean, memory=None):
    """One side of the choice, said as a reply, and the other one quoted beside it.

    Which side is decided the way the wording is - from the line itself - so a line always gets
    the same pick and two different lines do not all lean the same way. The understanding engine
    has already found the names in the line ("manchester" is a place, not a word), so they go back
    to the spelling the person used before the side opens the sentence.
    """
    first, second = sides
    seed = sum(ord(letter) for letter in clean)
    take, other = (first, second) if random.Random(seed).getrandbits(1) else (second, first)
    return _capital(_named(take, memory)), _named(other, memory)


def _between_people(sides, clean):
    """True when the two things are two people rather than two things.

    Read on the sides, not on the whole line: a pick between people is a verdict on them, and
    "my mum or my dad for christmas" in the words for a crisp flavour is the worst reply here.
    `CHOICE_PERSON_SIDE` catches the same two people said as sides ("his side or mine").
    """
    for side in sides or ():
        if set(side.split()) & CHOICE_PEOPLE:
            return True
    return bool(CHOICE_PERSON_SIDE.search(str(clean or "")))


def _choice_light(clean, memory=None):
    """The pool for a light choice: a side when the line names two things, the quieter lines when
    it does not (a line with one side missing is not a pick anybody can make)."""
    sides = _choice_sides(clean)
    if sides is None:
        return CHOICE_LIGHT
    if _between_people(sides, clean):
        return CHOICE_BETWEEN_PEOPLE
    take, other = _a_pick(sides, clean, memory)
    return [line.format(pick=take, other=other) for line in CHOICE_LIGHT_PICK]


def _choice_pool(clean, memory=None):
    """A bare "x or y" is a light choice unless the line names something at stake: a medicine
    (ask a pharmacist), or money, a repair, a commitment (name what decides it)."""
    words = set(clean.split())
    if words & CHOICE_HEALTH:
        if words & CHOICE_THERAPY:
            # "therapy or medication" is not a pharmacy question: only one side is a medicine,
            # and a pharmacist cannot say whether talking therapy suits. Leave it to them.
            return CHOICE_WEIGH
        return CHOICE_PHARMACIST
    if _an_order_of_work(_choice_sides(clean), clean):
        # Before the stakes: "should i repair the boiler first or the radiator" is an order too,
        # and "whichever you would regret less" answers a question about cost, not about order.
        return ORDER_OF_WORK
    if words & CHOICE_STAKES:
        return CHOICE_WEIGH
    return _choice_light(clean, memory)


# The person's own records: an order, a booking, an appointment, a balance. No search answers
# these and no entry about the world can - the answer only exists with whoever holds the record,
# and the bot does not. They used to reach the search hedge ("a quick search online will get you
# a solid answer"), which sends somebody to Google to find out where their own parcel is.
# STYLE.md's example of not knowing honestly is this class, so the reply says what the bot
# cannot see and the one place the person can.
#
# The ask has to be about the state of a thing of theirs, and nothing else: "how do i return my
# order" asks what to do about it, and "what is a booking reference" asks about the world, so
# both keep the answer they had.
OWN_RECORD_NOT = re.compile(
    r"\b(?:how\s+(?:do|can|could|should|would)\s+i|how\s+to|"
    r"should\s+i|do\s+i\s+need|can\s+i|could\s+i|help\s+me|"
    r"is\s+it\s+worth|worth\s+(?:it|chasing|appealing)|how\s+long\s+does|how\s+much\s+does|"
    r"what(?:'s| is)\s+a|difference|explain|meaning|any\s+tips|advice)\b")


def _their_own_phrase(clean, things):
    """The possessive phrase naming one of the person's own things, or None."""
    for thing in things:
        pattern = MY_OWN.get(thing)
        if pattern is None:
            pattern = MY_OWN[thing] = re.compile(
                r"\b(?:my|our)\s+(?:[a-z']+\s+){0,2}" + re.escape(thing) + r"(?![a-z])")
        match = pattern.search(clean)
        if match:
            return match
    return None


# The ask has to be about where the record has got to. Without that test the shape catches
# phrases where the noun is doing another job - "my balance on one leg", "my order of the
# words", "my delivery of the speech", "my daughter's table manners" - and offers a parcel
# tracking page for all of them.
RECORD_STATE = re.compile(
    r"\b(?:been|yet|still|already|confirmed|approved|ready|arrived|arriving|due|processed|"
    r"done|taken|paid|debited|credited|come\s+off|"
    r"cleared|accepted|rejected|declined|dispatched|despatched|delivered|shipped|sent|sorted|"
    r"collected|out\s+for\s+delivery|"
    r"through|tracked|tracking|back|come\s+back|come\s+through|go\s+through|gone\s+through|"
    r"go\s+out|gone\s+out|went\s+out|come\s+out|on\s+(?:its|the|his|her|their)\s+way|"
    r"what(?:'s|s)?|where(?:'s|s)?|when(?:'s|s)?|what\s+time|how\s+much|how\s+many|how\s+long|status|left|"
    # The same ask handed over instead of phrased as a question: "can you check my bank
    # balance", "can you look up my order", "could you tell me my balance". Every one of those
    # reached the search hedge while "whats my balance" got the honest line, and a search cannot
    # see an account any more than this can. The verb is the ask, so the record phrase and the
    # fences above still decide whether it is about one of their own things.
    r"(?:you|u)\s+(?:check|look\s+(?:(?:it|that)\s+)?up|see|tell\s+me|confirm|look\s+at|"
    r"find\s+(?:(?:it|that)\s+)?out|give\s+me))\b")
# "my statement of work", "my order of the words": the words after the noun say which thing it
# is, so the noun is not the record the person is asking about.
RECORD_QUALIFIED = re.compile(r"\s+(?:of|that|which)\b")

# The records nobody wrote down: "is my visa approved", "has my offer been accepted", "has my
# interview been arranged". The families in `MY_RECORDS` are the things people ask about most and
# each has a line that names where it lives; a noun no table holds fell through them all and got
# the search hedge, which is the one answer that is always wrong for a thing only an office can
# see. The state is what makes it that office's: approved, accepted, arranged, issued, registered
# are not states the person's own eyes settle, which is what keeps "is my cake done", "is my
# washing still wet" and "is my dinner ready" out of here.
OFFICE_STATE = re.compile(
    r"\b(?:approved|approval|accepted|arranged|booked|scheduled|confirmed|issued|granted|"
    r"refused|rejected|declined|registered|processed|dealt\s+with|signed\s+off|finalised|"
    r"finalized|paid\s+out|put\s+through|agreed|arrived|come\s+back|sent|posted|returned)\b")
# "my visa", "my new passport", "my second interview": the possessive is what makes it theirs,
# and up to two words may sit between it and the thing.
MY_ANY_THING = re.compile(r"\b(?:my|our)\s+(?:[a-z']+\s+){0,2}([a-z]+)")
# The thing after the possessive is what the state belongs to, and a person is never a thing an
# office holds: "has my sister arrived yet", "have my parents returned", "has my son arrived at
# school" are questions only the person asking can answer, and the office line answered them with
# letters and reference numbers. The last noun is read, not the presence of a person, because "has
# my sister's visa been approved" is still the visa's state and is the office's.
_A_MY_PERSON = None


def _a_person_is_the_thing(clean):
    """True when the person is the subject of the state, not the owner of a record.

    "has my sister arrived yet" puts a person in the state; "has my sister's visa been approved"
    puts a visa in it. The word after the person decides: a state, a place or the end of the clause
    makes the person the subject, and another noun makes them the owner.
    """
    global _A_MY_PERSON
    if _A_MY_PERSON is None:
        from .loss import PEOPLE
        kinds = "|".join(sorted((re.escape(word) for word in PEOPLE), key=len, reverse=True))
        _A_MY_PERSON = re.compile(
            r"\b(?:my|our|his|her|their|the)\s+(?:" + kinds + r")(?:\'s|s\')?"
            r"(?=\s*(?:$|[,.!?;]|(?:has|have|had|is|are|was|were|did|does|do|not|never|just|now|"
            r"still|yet|already|arrived|arrive|arrives|coming|come|came|returned|returns|got|"
            r"gotten|been|being|at|home|there|back|in|out|safe|ok|alright|fine|well|on|off|to|"
            r"from|away|left|gone|late|early|waiting)\b))", re.I)
    return bool(_A_MY_PERSON.search(clean or ""))


# A thing handed over the counter, where the state was not an office's either: "have i been given
# the wrong change", "i got short changed at the shop". `MY_OWN_STATE` reads "have i been given"
# as a record and sent it to the paperwork line, and a till receipt is the answer to it.
A_TILL_ASK = re.compile(
    r"\b(?:wrong|right|short|extra|too\s+much|too\s+little|double)\s+(?:change|amount)\b|"
    r"\bshort[-\s]?changed\b|\bchange\s+back\b|"
    r"\b(?:overcharged|undercharged|charged\s+twice)\b")
# A thing the person puts in a state themselves, or one nobody can see but them: the home, the
# kitchen and the body are not offices, and an office line over them would be the same confident
# wrong answer the hedge was.
NOT_AN_OFFICE = re.compile(
    r"\b(?:cake|cakes|bread|dough|sourdough|pastry|dinner|tea|lunch|breakfast|supper|roast|"
    r"soup|sauce|stock|washing|laundry|wash|load|hair|nails|beard|leg|legs|arm|arms|back|knee|"
    r"shoulder|eyes|ears|teeth|skin|tattoo|car|cars|bike|bikes|van|boiler|heating|fence|shed|"
    r"plant|plants|garden|lawn|wall|walls|roof|paint|grout|silicone|sealant|floor|tiles|shelf|"
    r"door|window|gutter|drive|pond|allotment|chickens|hens|dog|cat|baby|nappy|sleep|diet)\b")

# "check my gift card balance", "can you check my order", "confirm my booking": the ask said with
# the verb in front, and no state word, so the record pool never saw it. An imperative "check my
# ..." is the same question as "where is my ..." and has the same answer - the record is not here,
# and this is where it lives. The line still has to name one of the record things, so "check my
# tyre pressure" and "check my spelling" are left to whatever knows them.
RECORD_CHECK = re.compile(r"\b(?:check|checking|confirm|look\s+up|track|trace)\b")
# Half of the same asks name no thing at all: the person is the subject, so there is no noun for a
# table to hold - "have i been paid yet", "am i registered", "have i been shortlisted". Every one
# is about their own record rather than the world, and every one of them had the search hedge.
MY_OWN_STATE = re.compile(
    r"\b(?:have|has)\s+i\s+been\s+(?:paid|approved|accepted|registered|booked|confirmed|"
    r"granted|refused|rejected|shortlisted|interviewed|offered|told|sent|given|taken\s+on|"
    r"picked|placed|invited|added|approved\s+for)\b|"
    r"\bam\s+i\s+(?:on\s+the\s+list|in\s+the\s+running|registered|booked\s+in|signed\s+up|"
    r"enrolled|shortlisted|selected)\b")
RECORD_THINGS = tuple(thing for _, things, _ in MY_RECORDS for thing in things)
# The card's own two states are not the balance: a line asking whether it still works wants the
# expiry date, and a line saying it is worth something wants a resale answer.
CARD_VALIDITY_ASK = re.compile(
    r"\b(?:valid|expire|expires|expired|expiry|run\s+out|runs\s+out|ran\s+out|"
    r"out\s+of\s+date|still\s+(?:use|work|spend|spent)|still\s+good)\b")


# "How much is on my card", "what's left on my debit card": the bare word card asks about the
# balance on it, and the pool below only knows the named ones (gift card, voucher, store card).
# The state words keep it off "my card was declined" and "how much is my card worth", which are
# the bank's answer and a resale question, not a balance.
CARD_BALANCE_ASK = re.compile(r"\b(?:how\s+much|balance|left|remaining|still\s+on)\b")
CARD_NOT_A_BALANCE = re.compile(r"\b(?:worth|value|declined|refused|cloned|stolen|blocked|"
                                r"cancel|replace|expire|expires|expired)\b")
MY_CARD_ROW = next((options for name, things, options in MY_RECORDS if name == "card"), None)
# Two of the families answer a line that names no thing of its own: wages are the money row's, and
# a yes or a no about being picked is the application row's.
MY_MONEY_ROW = next((options for name, things, options in MY_RECORDS if name == "money"), None)
MY_APPLICATION_ROW = next((options for name, things, options in MY_RECORDS
                           if name == "application"), None)

# A points, stamps or voucher balance is the person's own and only the scheme holds it. The name
# of the scheme is what makes it theirs: "how many points do i have" on its own is a quiz, a
# driving licence or a game, and those keep whatever answers them, so the line has to say
# loyalty, a named scheme, "my points" or stamps on a card. "How do loyalty points work" is the
# same reader, because where they collect and when they expire is the answer either way.
POINTS_SCHEME = re.compile(
    r"\b(?:loyalty\s+(?:points?|cards?|scheme)|nectar|clubcard|club\s?card|avios|airmiles|"
    r"reward\s+(?:points?|cards?|scheme)|store\s+points?|points\s+cards?|"
    r"(?:my|our)\s+points|(?:my|our)\s+stamps|stamps?\s+on\s+(?:my|the)\s+card|"
    r"points\s+(?:balance|total))\b", re.I)
# The balance question, the expiry question and the how-does-it-work question are one answer:
# where the figures are, when they go, and what the rate makes them worth.
POINTS_ASK = re.compile(
    r"\b(?:how\s+many|how\s+much|how\s+do|how\s+does|how\s+can|what(?:'s|\s+is)?|do|does|did|"
    r"are|is|when|where|worth|expire|expires|expired|expiring|left|balance|collect|collected|"
    r"redeem|redeemed|spend|spent)\b", re.I)
POINTS_NOT = re.compile(
    r"\b(?:licence|license|driving|car|insurance|court|ban|visa|school|university|"
    r"course|grade|exam|game|match|score|league|rugby|football|quiz|test)\b", re.I)


# A thing the person already pays for, asked about its price: not a market price (the "prices"
# live kind answered "how much is my gym membership" with "the seller's site will have today's
# figure", which is a stranger's price for a thing they do not sell) and not a quote for a new one
# (that is @hearty-dog's pool). The thing has to be one a bill covers, and it has to be theirs.
MY_BILL_THING = re.compile(
    r"\b(?:memberships?|subscriptions?|subs|plan|tariff|contract|deal|package|"
    r"season\s+ticket|direct\s+debit|standing\s+order)\b", re.I)
MY_BILL_MINE = re.compile(
    r"\b(?:my|our|the)\s+(?:[a-z]+\s+){0,2}?(?:memberships?|subscriptions?|subs|plan|tariff|"
    r"contract|deal|package|season\s+ticket)\b", re.I)
MY_BILL_ASK = re.compile(
    r"\b(?:how\s+much|what(?:'s|\s+is)?\s+(?:i|we)\s+paying?|what\s+do\s+(?:i|we)\s+pay|"
    r"cost|costs|costing|charge|charged|charging|price|paying|per\s+month|a\s+month|"
    r"a\s+year|over\s+the\s+year|too\s+much|cheaper|worth\s+it|stop\s+paying|cancel)\b", re.I)
# A quote for something new, and a bill that belongs to the house rather than to a contract, are
# not this: "how much is a gym membership" is a price to compare, "how much is my council tax" is
# the council's own band and their own page.
MY_BILL_NOT = re.compile(
    r"\b(?:a\s+gym|join|joining|sign\s+up|new|compare|comparison|cheapest|switch|switching|"
    r"council\s+tax|water|electric|gas|energy|broadband|insurance|mortgage|rent|"
    r"mobile\s+phone|sim\s+only|iphone|phone\s+contract)\b", re.I)


def _their_own_bill(clean):
    """The honest line for the price of something the person already pays for, or None."""
    if not MY_BILL_MINE.search(clean) or not MY_BILL_THING.search(clean):
        return None
    if not MY_BILL_ASK.search(clean) or MY_BILL_NOT.search(clean):
        return None
    return MY_BILL_LINES


def _their_own_points(clean):
    """The honest line for a points or stamps balance, or None."""
    if not POINTS_SCHEME.search(clean) or POINTS_NOT.search(clean):
        return None
    if not POINTS_ASK.search(clean):
        return None
    return POINTS_LINES


CARD_RECORD_THINGS = ("gift card", "gift cards", "voucher", "vouchers", "prepaid card",
                      "store card", "loyalty card", "loyalty points", "card")


def _an_office_record(clean, asking):
    """The honest line for a record only an office can see, or None.

    Two shapes reach here. A thing of the person's own that no family names, put into a state
    only an institution can put it in - "is my visa approved", "has my offer been accepted" - and
    the same ask with the person as the subject and no thing to hold at all: "have i been paid
    yet", "am i registered", "have i been shortlisted". Both were met with the search hedge, and
    no search can see a visa either.

    The state word is what makes it an office's, and the homes and bodies that also have one are
    in `NOT_AN_OFFICE`: "is my cake done" and "is my washing still wet" keep their own answers,
    and the person can settle those themselves.
    """
    if not asking or NOT_AN_OFFICE.search(clean):
        return None
    if A_TILL_ASK.search(clean):
        return AT_THE_TILL
    if _a_person_is_the_thing(clean):
        return None
    if OFFICE_STATE.search(clean) and MY_ANY_THING.search(clean):
        return OFFICE_RECORD_LINES
    if MY_OWN_STATE.search(clean):
        if _has(clean, ("paid", "pay", "wages", "salary", "money", "expenses")):
            if MY_MONEY_ROW is not None:
                return MY_MONEY_ROW
        if MY_APPLICATION_ROW is not None:
            return MY_APPLICATION_ROW
    return None


def _their_own_record(clean, asking):
    """The honest line for one of the person's own records, or None."""
    # Half of what a person asks about their own life names no record at all: the person is the
    # subject of the verb and there is no noun to hold on to - "what did i do last tuesday",
    # "where did i go last weekend", "what did i buy on saturday". Nothing in any knowledge entry
    # has it, no search answers it, and the hedge sent the person to Google to find out about
    # their own week. It is read before the record test below, which needs a possessive noun these
    # lines do not have, and it is read whether or not the line is an ask, because "i went to
    # asda on saturday" is the same history.
    said = _their_own_week(clean)
    if said:
        return said
    # A points or stamps balance is the person's own record even when the line names no
    # possessive: "how many loyalty points do i have" has no "my ..." for the rows below to hold.
    said = _their_own_points(clean)
    if said:
        return said
    checking = bool(RECORD_CHECK.search(clean)) and bool(_their_own_phrase(clean, RECORD_THINGS))
    # A card's expiry is its own question with its own answer, and it can be said as a statement
    # ("my loyalty card has expired") as well as an ask, so it is read before the asking gate.
    validity = bool(CARD_VALIDITY_ASK.search(clean)) and bool(
        _their_own_phrase(clean, CARD_RECORD_THINGS))
    if not (asking or checking or validity) or OWN_RECORD_NOT.search(clean):
        return None
    if validity:
        return CARD_VALIDITY
    if not (RECORD_STATE.search(clean) or checking):
        # A state only an office can see, on a thing no table names: "has my interview been
        # arranged" holds no word the gate above knows, and the search hedge is the one answer
        # that is always wrong for a thing only an office can look up.
        return _an_office_record(clean, asking)
    # A card with money on it is the card's row even when the ask is written with a balance word:
    # "check my gift card balance" matched the money row first ("my gift card balance"), and the
    # reply was about a bank account the person had not mentioned.
    rows = MY_RECORDS
    if _their_own_phrase(clean, CARD_RECORD_THINGS):
        rows = sorted(MY_RECORDS, key=lambda row: row[0] != "card")
    for name, things, options in rows:
        phrase = _their_own_phrase(clean, things)
        if phrase and not RECORD_QUALIFIED.match(clean, phrase.end()):
            return options
    if (MY_CARD_ROW is not None and CARD_BALANCE_ASK.search(clean)
            and not CARD_NOT_A_BALANCE.search(clean)
            and _their_own_phrase(clean, ("card",))):
        return MY_CARD_ROW
    phrase = _their_own_phrase(clean, HEALTH_RECORD)
    if phrase and not RECORD_QUALIFIED.match(clean, phrase.end()):
        if _has(clean, HEALTH_WORLD):
            return HEALTH_RECORD_LINES
    # The named families are read first and keep their own lines - a booking is in a confirmation,
    # a balance in the bank's app - and only a thing no table holds comes to the office line.
    return _an_office_record(clean, asking)


# The person's own day, said with a day behind it: "what did i do yesterday", "where did i go last
# weekend", "what did i buy on saturday". The day is what makes it their own history rather than a
# question about the world - "what did i do wrong" is about the thing in hand and keeps its own
# answer - and the doing has to be one of the ordinary ones a diary holds: shoulders, schools and
# shifts are in the record entries already. What they said in this chat is the memory store's
# ("what did i say yesterday"), so saying and telling are not here.
A_DAY_AGO = re.compile(
    r"\b(?:yesterday|last night|last (?:week|weekend|month|(?:mon|tues|wednes|thurs|fri|satur|"
    r"sun)day)|on (?:mon|tues|wednes|thurs|fri|satur|sun)day|this (?:morning|afternoon|evening)|"
    r"the weekend|earlier today)\b")
MY_OWN_DOING = re.compile(
    r"(?:^|\b(?:what|where|who|when|which|how much|how many)\b[^?]{0,40}?)"
    r"\b(?:did|have|had)\s+(?:i|we)\s+(?:already\s+|actually\s+|just\s+|even\s+)?"
    r"(?:do|done|go|gone|see|seen|visit|visited|buy|bought|spend|spent|eat|eaten|drink|drunk|"
    r"work|worked|book|booked|order|ordered|pay|paid|take|taken|get|got|watch|watched|meet|met)\b")
MY_OWN_DAY_LINES = (
    "I haven't got your diary, sorry - I only know what you tell me here. Your phone's calendar or "
    "the photos from that day will usually bring it back.",
    "Nothing of yours to look at from this end. The calendar, the photos and the emails from that "
    "day are where it is - tell me what you find and I'll help with the rest of it.",
)

# A medicine ask has a day behind it and the same "did i take" doing, but the person who knows is
# not the calendar: "have i taken my pills this morning", "did i take my tablets this morning",
# "have i taken my antibiotics this morning" were answered with the diary line, and "the photos
# from that day" is no help for whether a tablet was swallowed. The health entries already answer
# these by naming the pharmacist and the GP, so the reader stands down for any line that names the
# medicine, and the answer the person had before is the one they get.
NOT_ABOUT_THEIR_DAY = re.compile(
    r"\b(?:pill|pills|tablet|tablets|medicine|medicines|medication|medications|meds|"
    r"antibiotic|antibiotics|inhaler|insulin|dose|doses|injection|injections|jab|jabs|"
    r"painkiller|painkillers|paracetamol|ibuprofen|steroid|steroids|epipen|"
    r"vitamin|vitamins|supplement|supplements|prescription|prescriptions|drops|patch|patches)\b")


def _their_own_week(clean):
    """The honest line for what the person did on a day gone by, or None.

    The fact is not in any entry about the world and a search does not know it either, so the
    reply says in a few words what the bot cannot see and names the one place the person can:
    the calendar, the photos and the emails of that day. A line about the thing in hand rather
    than their history ("what did i do wrong") has no day in it and keeps its own answer.
    """
    said = " ".join(str(clean or "").lower().split())
    if not said:
        return None
    if NOT_ABOUT_THEIR_DAY.search(said):
        return None
    if A_DAY_AGO.search(said) and MY_OWN_DOING.search(said):
        return MY_OWN_DAY_LINES
    return None

# A phone number is a live fact like an opening time: it changes, and a wrong one is worse than
# no answer at all, because the person dials it. So a line that wants the number of a place gets
# the one place that number lives for that kind of place, never digits. It reads only the ask
# shaped "the number for ..." / "what's the number" / "how do i ring ...", so a report ("the
# bank's number was engaged all morning") and a number of the person's own ("my account number")
# are left alone, and a place nobody here knows ("the number for 111") stays with the pool that
# does know it.
NUMBER_WANTED = re.compile(
    r"\b(?:the|a|their|its|his|her)\s+(?:[a-z']+\s+){0,2}number\b|"
    r"\bnumber (?:for|to (?:ring|call|phone))\b|\b(?:phone |telephone |contact )number of\b|"
    r"\b(?:whats|what's|wats|wots) (?:the )?(?:phone |telephone )?number\b|"
    r"\bhow do i (?:ring|phone|call)\b|\b(?:need|want|looking for) (?:the )?(?:phone )?number\b|"
    r"\bcontact (?:details|number)\b|\blook up the number\b|\bgive me the number\b|"
    r"\bnumber to (?:ring|call|phone)\b|\bwhat number (?:do|should) i (?:ring|call)\b")
# A number that was engaged, wrong or unanswered is being reported, not asked for: "the council
# number was engaged all morning" is a complaint, and the honest line about where a number lives
# answers a question nobody asked.
# "The number of council houses" counts them: the counting sense of "number of" is not a phone
# number unless the line says phone.
NUMBER_OF = re.compile(r"\bnumber of\b")
NUMBER_OF_PHONE = re.compile(r"\b(?:phone|telephone|contact|mobile)\s+number of\b")
NUMBER_REPORT = re.compile(
    r"\bnumber (?:was|is|kept|keeps|has been|had been|never|didnt|didn't|rang|rung|went)\b|"
    r"\b(?:i|we|she|he|they)\s+(?:rang|rung|phoned|called|tried)\s+"
    r"(?:the\s+|my\s+|her\s+|his\s+|their\s+|our\s+)?(?:[a-z']+\s+){0,2}number\b")
# A number they already hold is not one to ring for: "whats my reference number" and "my policy
# number" belong to the record pools, and a bank's "customer number" is not a phone.
NUMBER_NOT = ("reference number", "order number", "account number", "policy number",
              "national insurance", "registration number", "ni number", "case number",
              "invoice number", "membership number", "customer number", "flight number",
              "bus number", "train number", "house number", "serial number", "pin number",
              "tracking number", "claim number")


NUMBER_PLACE_PATTERNS = {}


def _names_place(clean, places):
    """True when the line names one of these places, plural or not ("the councils number")."""
    for place in places:
        pattern = NUMBER_PLACE_PATTERNS.get(place)
        if pattern is None:
            pattern = NUMBER_PLACE_PATTERNS[place] = re.compile(
                r"\b" + re.escape(place) + r"(?:s|es)?\b")
        if pattern.search(clean):
            return True
    return False


def _their_contact_number(clean, asking):
    """The honest line for the phone number of a place the person wants to ring, or None.

    `asking` is not consulted: the shape in NUMBER_WANTED is what tells a want from a report.
    """
    if not NUMBER_WANTED.search(clean) or _has(clean, NUMBER_NOT):
        return None
    if NUMBER_REPORT.search(clean):
        return None
    if NUMBER_OF.search(clean) and not NUMBER_OF_PHONE.search(clean):
        return None
    for places, options in NUMBER_PLACES:
        if _names_place(clean, places):
            return options
    return None


# Their own shift, which is on a rota nobody here can see. "What time do i start work tomorrow"
# and "am i working on saturday" are not questions about the world: the answer is a rota, on the
# person's side of the screen, written by somebody the bot cannot ring - so the search hedge is
# the worst of both, and describing how rotas work (the entry that answers "my shift got
# switched") is a paragraph about somebody else's rota.
MY_DAY_ASK = re.compile(
    r"(?<![a-z])(?:what time|when|which time|what hours)(?: (?:do|does|am|are|will|should))? i "
    r"(?:start|finish|begin|leave|get in|get off|clock in|clock off|be in|be on|in|on)(?![a-z])"
    r"|(?<![a-z])(?:am|will) i (?:be )?(?:working|in work|in today|in tomorrow|on shift|"
    r"on a shift|on the rota)(?![a-z])")
# The words that can sit around it without making it about something else: which day, and the
# work itself. "what time do i finish work" is this reading, "what time do i finish the essay"
# and "what time do i start the roast" are not.
MY_DAY_SAID = frozenset("""
work works working job shift shifts rota hours office site shop store school placement
today tomorrow tonight now this next the a an on at in for till until from to and or but so
then also please just know wondering do does did dont don't not never any idea anyone anybody
you your me i my actually usually normally roughly about quick question one more supposed meant
ever again morning mornings afternoon evening evenings night nights early late earlies lates days
week weekend monday tuesday wednesday thursday friday saturday sunday day
start starts finish finishes begin clock off experience induction
""".split())
# Named out loud, the timetable is somebody else's to keep: a school's office, a course, a
# surgery's appointment. They have their own line, and it is not this one.
MY_DAY_NOT = re.compile(
    r"\b(?:school run|college|uni|university|course|class|lesson|exam|appointment|nurse|doctor|"
    r"dentist|hospital|physio|clinic|chemist|pharmacy|hair|barber|gym|football|training|"
    r"the match|the kids?|the children|pick(?:ing)? up|drop(?:ping)? off|"
    r"tablets?|medicine|medication)\b", re.I)


def _their_own_day(clean):
    """The honest line for their own shift, or None.

    Last resort only: it is asked where the bot has nothing else, so a line the knowledge has a
    card for keeps it.
    """
    match = MY_DAY_ASK.search(clean)
    if not match or MY_DAY_NOT.search(clean):
        return None
    if not (_has(clean, ("work", "works", "working", "job", "shift", "shifts", "rota", "hours"))
            or re.search(r"\bclock(?:ed|s)? (?:in|off|on)\b", clean)):
        return None
    rest = clean[:match.start()] + " " + clean[match.end():]
    for word in re.findall(r"[a-z']+", rest):
        if word not in MY_DAY_SAID:
            return None
    return MY_OWN_DAY


# "What time do the shops open" asks when a place opens; "what time do i start work" and "what
# time does my shift start" ask about the person's own day. The honest line about opening hours
# answers a question nobody asked there, so a time ask whose subject is the speaker - a
# first-person subject, or a possessive of their own - is not about a venue. One sentence found
# it: "what time do i take my tablets" was answered "I can't check today's opening hours, sorry."
OWN_TIME_ASK = re.compile(
    r"(?<![a-z])what time (?:do|does|did|will|would|should|can|could|shall) "
    r"(?:i|we|my|our)(?![a-z])")
# "What time is my train" asks the same thing with a different verb and no bad habit behind it,
# so the travel pool reads it too.
MY_TIME_ASK = re.compile(r"(?<![a-z])what time (?:is|are|was|were) (?:my|our)(?![a-z])")
OWN_VERB_OPEN = re.compile(r"(?<![a-z])(?:i|we) (?:open|close|shut)(?![a-z])")


def _a_bare_wear_ask(clean):
    """True when a take/wear ask is the whole of the line and nothing else is attached."""
    text = clean
    for phrase in sorted(LIVE_TAKE_ASK, key=len, reverse=True):
        text = text.replace(phrase, " ")
    for word in tuple(LIVE_WEAR) + tuple(LIVE_SOON):
        text = text.replace(word, " ")
    for word in re.findall(r"[a-z']+", text):
        if word not in LIVE_TAKE_ALLOWED:
            return False
    return True


# "Is it going to rain on saturday" names no weather word the list above holds, only a day.
# The words are the sky's own, so "hot tomorrow", "frost tonight" and "icy on saturday" reach the
# note the way "cold tonight" already did; "nice", "dull" and "grey" only count beside a day,
# because on their own they are a verdict on anything.
LIVE_WEATHER_DAY = re.compile(
    r"\b(?:rain|raining|rainy|snow|snowing|sunny|sun|windy|warm|cold|hot|icy|frost|frosty|"
    r"fog|foggy|misty|muggy|humid|cloudy|overcast|chilly|freezing|storm|stormy|thundery|hail|"
    r"showers?|drizzle|drizzling|nice|dull|grey|gray)\b[^.!?]{0,28}?"
    r"\b(?:today|tonight|tomorrow|this week|next week|weekend|saturday|sunday|monday|tuesday|"
    r"wednesday|thursday|friday)\b", re.I)


# The same question, asked about a piece of time: "how was your day", "how did your evening
# go", "how's your week been". A time word is what makes it the bot's own day and nothing
# else in the world, so "how did your meeting go" is still its own question.
HOW_WAS_YOUR_TIME = re.compile(
    r"(?<![a-z])hows? (?:is |was |are |were |did |has |have )?(?:your|you) "
    r"(?:day|days|week|weeks|weekend|evening|morning|afternoon|night|shift|holiday|break|time)"
    r"(?![a-z])")
# The manners question in the shapes the phrase list cannot see, because a verb comes between
# the second person and the day: "what have you been doing", "are you having a good day", "did
# you have a nice weekend". The second person is what makes it the bot's own day - "im having a
# good day" is the person's and stays theirs - and the time word at the end is what the line is
# about, so a line with anything else after it ("are you having a baby") is not this question.
YOUR_DAY_ASK = re.compile(
    r"\b(?:are|were|have|had|did|do|does)\s+(?:you|u)\s+(?:been\s+)?"
    r"(?:having|had|have)\s+(?:a\s+|an\s+)?(?:good|nice|great|lovely|ok|okay|quiet|crap|bad)?\s*"
    r"(?:day|days|weekend|evening|night|morning|afternoon)\b")
# A day, week or evening with the bot's possessive in front of it is the bot's own time and
# always was the manners question: "hows your day going anyway", "whats your day been like".
# The three above read the verb; this reads the noun, which no other subject can own.
YOUR_OWN_TIME = re.compile(
    r"(?<![a-z])(?:your|you)\s+(?:day|days|week|weeks|weekend|evening|morning|afternoon|night)"
    r"(?![a-z])")
# "what have you been doing", "what u been up to": the ask is about the bot's own time, and
# nothing else can follow it but a tag.
# The shortest way of asking it back: "what about you", "and you?", "yourself?" one turn after an
# answer. Every follow-up reader in the bot reads it as a question about the thing on the table -
# after the egg answer, "what about you" got the egg answer again - so the composer claims it with
# the same manners pool. A line that names anything after the hand-back ("what about your meeting",
# "what about you and your sister") is not this.
HAND_BACK = re.compile(
    r"^(?:(?:and|so|ok|okay|but|right|then)\s+)?"
    r"(?:(?:what|how)\s+about\s+(?:you|ya|u|yourself|your\s+(?:day|week|weekend|evening|one))"
    r"|any(?:thing)?\s+new\s+with\s+you"
    r"|yourself"
    # "and you?", "and yourself?", "so you?": the connector in front is what makes a bare
    # pronoun a hand-back rather than a one-word answer.
    r"|(?:and|so|ok|okay|but|right|then)\s+(?:you|ya|u|yourself))\??"
    r"(?:\s+(?:today|then|anyway|though|so|now|lately|honestly|mate))?$")
YOUR_TIME_ASK = re.compile(
    r"\b(?:what|whats)\s+(?:have|has|ve)\s+(?:you|u)\s+been\s+(?:up\s+to|doing|at)\b"
    r"|\b(?:you|u)\s+been\s+(?:up\s+to|doing)\b")


# A question word that opens a later clause ("ok cool. one more thing, how do i ask for a
# raise") asks a question just as much as one that opens the line. A bare auxiliary is not
# enough: "we also have a 4 year old" and "and can't get back to sleep" are statements.
LATER_QUESTION = re.compile(
    r"(?:^|[,.!?;\u2013\u2014-]\s*|"
    r"\b(?:and|but|so|then|also|ok|okay|cool|right|btw|anyway|quick|thing)\s+)"
    r"(?:what|whats|wats|wat|wot|why|whys|how|hows|when|whens|where|wheres|who|whos|which"
    r"|can (?:i|you|we|it) \w+|could (?:i|you|we) \w+|should i \w+|would (?:i|you) \w+"
    r"|do (?:i|you|we) \w+|does (?:it|that|this) \w+|is (?:it|that|this|there) \w+"
    r"|are (?:there|you|we) \w+)\b",
    re.IGNORECASE)


def _asks_for_something(text):
    """True when the line is more than a greeting: it wants an answer."""
    lower = text.lower()
    return any(cue in lower for cue in REQUEST_CUES)


def _reads_as_why(clean):
    """True for a follow-up that asks for the reason behind the taste just given."""
    return clean.startswith("why") or "why that" in clean or "how come" in clean \
        or "what makes you say" in clean


# "What do you think about my landlord refusing repairs?" asks for advice about the speaker's
# own life, not what the bot likes: a glib "I don't mind either way" there is worse than an
# honest hedge, so the taste pools stay out of it.
OWN_LIFE = re.compile(r"\b(?:my|our|his|her|their)\b")


def _is_about_the_persons_own_life(clean):
    """True when the opinion asked for is about the speaker's situation, not about a thing."""
    return bool(OWN_LIFE.search(clean))


def _in_a_care_thread(memory):
    """True when the bot's last answer, reading past its own continuations, was care.

    A pick is not the reply to a bereavement or a crisis: "my mum died last month" / "what would
    you pick" asking for the list invites one where nothing blithe belongs, and "i want to kill
    myself" / "which would you pick" reads as asking which way out. The walk goes on past this
    fallback's own lines, because a grief thread is often several of them in a row.
    """
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    for turn in reversed(turns[-THREAD_TURNS:]):
        module = turn.get("module")
        if module in CARE_MODULES:
            return True
        if module not in QUIET_MODULES:
            return False
    return False


def _a_lean_only_line(clean):
    """True when the line is only the ask, so the trade-off is what it is about."""
    return not [word for word in PICK_WORD.findall(clean) if word not in PICK_ONLY_WORDS]


def _a_bare_pick(clean):
    """True when the line asks for the bot's own pick and names nothing of its own."""
    if not PICK_ASK.search(clean):
        return False
    if " or " in clean:
        # "cats or dogs, which would you pick" puts the choice in the line itself: that is the
        # taste pools' question, and they have real answers for it.
        return False
    if _has(clean, OPINION_ASKS):
        # "which do you prefer", "what do you think of it": a taste with no options on the table
        # is the taste pools' question, and "No strong view on that one, honestly" is a better
        # answer than a pick of something that is not there.
        return False
    return not [word for word in PICK_WORD.findall(clean) if word not in PICK_ONLY_WORDS]


def _the_side_taken(reply, sides):
    """The side of `sides` the bot's own reply went to, or None when it named neither.

    "cats or dogs" is answered from the knowledge base with "Dogs, by a whisker: daft,
    straightforward and pleased to see you. A cat is the kinder choice if you're out all day",
    and "which would you get" must not then say "I'd go *Cats*": a pick that argues with the
    bot's own last line is worse than no pick at all. The first side the reply puts in front of
    the person is the one it went to, whether it opens on it ("Chinese.") or names it as the
    thing to do first ("Quick: chickpea curry in 25, or a potato curry").
    """
    said = str(reply or "").lower()
    best = None
    for side in sides or ():
        found = re.search(r"\b" + re.escape(side.lower()) + r"", said)
        if found and (best is None or found.start() < best[0]):
            best = (found.start(), side)
    return best[1] if best else None


def _picked_a_side(reply, sides):
    """True when the bot's reply to that choice went to one of the two things in `sides`: the
    choice is still on the table for "which would you get?".

    A fallback line usually offers nothing ("that's beyond what I know well, sorry"), and reading
    an offer out of it would pick an option the bot never named. A light choice answered with a
    side is the exception: "Chinese. I'd take that and not think about it again" is the option.
    """
    return _the_side_taken(reply, sides) is not None


def _offered(memory):
    """The options the bot offered for what the conversation is on, as (name, note) pairs.

    Only a reply that was not the fallback's own: a nod offers nothing to choose between, and
    two options at least, because one thing is not a choice. The offer also has to be the one
    for the subject the chat is on: walk back over the turns that only nod or only ask again
    ("ok", "what would you suggest"), and read the reply to the last line that named something.
    A turn where the person moved on ("the kids want a takeaway tonight") ends the walk, so a
    film offered three turns ago is never picked for a takeaway.
    """
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict):
            continue
        said = PICK_WORD.findall(str(turn.get("user") or "").lower())
        if not said or not [word for word in said if word not in PICK_ONLY_WORDS]:
            continue  # a nod or the same ask again: keep looking for the line it is about
        if turn.get("module") == FALLBACK_MODULE and not _picked_a_side(
                str(turn.get("bot") or ""), _choice_sides(" ".join(said))):
            return []
        found = _titles(str(turn.get("bot") or ""))
        if len(found) >= 2:
            return found
        # The bot's reply need not have offered the options in italics: "chinese or indian
        # tonight" was answered by a pick, and "which would you get?" then wants that pick made
        # again rather than "depends what we're choosing between" - the choice is right there in
        # the line the person has just said.
        sides = _choice_sides(" ".join(said))
        if not sides:
            return []
        # The bot's own answer may have gone to one side already, and the pick says the same one
        # rather than arguing with the line above it.
        taken = _the_side_taken(str(turn.get("bot") or ""), sides)
        if taken:
            return [(_capital(taken), "")]
        # A side read from the person's line goes into a reply mid-sentence ("I'd go *Indian*,
        # out of those"), so it keeps the capital it would have had as a name.
        return [(_capital(side), "") for side in sides]
    return []


def _titles(said):
    """The options a reply offered, as (name, note) pairs."""
    found = []
    for match in PICK_TITLE.finditer(said):
        name = " ".join(match.group(1).split())
        if not name or len(name.split()) > 8 or not name.strip("."):
            continue
        if len(name.split()) == 1 and name[:1].islower() and not any(c.isdigit() for c in name):
            # A word in italics is as often the word being talked about ("nothing rhymes with
            # *purple*") as it is an option: a single lowercase word is not a thing to pick.
            continue
        note = PICK_NOTE.match(said[match.end():match.end() + 90])
        note = " ".join(note.group(1).split()) if note else ""
        if note and re.search(r"\b(?:you|your|i|we|me|us)\b", note):
            # "if you'd rather think" is about the person, not a description to say back.
            note = ""
        found.append((name, note))
    return found


def _names_in(said):
    """The words of a line that name something, with the plumbing and the ask taken out."""
    return {word for word in PICK_WORD.findall(said.lower()) if word not in PICK_ONLY_WORDS}


def _a_named_side(after):
    """The side after the "but" as the thing to pick, or "" when it is not one.

    "the other has better brakes" -> "the one with better brakes"; "further from work" -> "the
    one further from work"; "the people are nicer in the other" -> "the one where the people are
    nicer". A verdict ("i hate it", "the neighbours are awful") is not a side at all, and neither
    is a phrase that comes out of these shapes half-built: nothing is said rather than something
    wrong.
    """
    text = " ".join(str(after or "").split()).strip(" ,.;:")
    text = SIDE_TAIL.sub("", text).strip(" ,.;:")
    # The side has to name an advantage, or there is no second option to name: "my mum is here"
    # and "the pay is less" are a fact and a comparison, not a thing to pick. A side that also
    # reads as a cost ("cheaper but further out") is left alone rather than half-read.
    if not text or NOT_A_CHOICE.search(text) or SIDE_BAD.search(text):
        return ""
    if not SIDE_GOOD.search(text):
        return ""
    # "the other has better brakes" is about the other of the two, and the thing to name is what
    # it has.
    text = SIDE_OTHER.sub("", text).strip(" ,")
    if re.match(r"^(?:is|are|was|were)\s+", text, re.I):
        text = "that " + text
    first = re.match(r"^(?:i|we|im|i'm)\b", text, re.I)
    has = SIDE_HAS.match(text)
    if has:
        return "the one with " + has.group(1).strip(" ,.")
    is_ = SIDE_IS.match(text)
    if is_:
        return "the one that is " + is_.group(1).strip(" ,.")
    if first:
        # "i keep thinking about the art one" is the person's own leaning, not a side to name:
        # handing it back as "the one I keep thinking about" only repeats their sentence.
        return ""
    one = SIDE_ONE.match(text)
    if one and SIDE_GOOD.search(one.group(2)):
        # "the art one sounds more fun" names the thing itself, which is the best label there is.
        return one.group(1)
    if SIDE_SUBJECT.match(text) and SIDE_COPULA.search(text):
        return "the one where " + text
    if re.match(r"^(?:more|fewer|less|better|cheaper|bigger|newer|nicer)\b", text, re.I):
        return "the one with " + text
    if SIDE_VERB.search(text) and not SIDE_SUBJECT.match(text):
        return "the one that " + text
    if not SIDE_SUBJECT.match(text):
        return "the one " + text
    return ""


def _a_trade_off(memory):
    """The side the person put after their "but", named as a thing to pick, or ""

    Only the most recent line of theirs that says something: a nod or the same ask again is
    walked past, and a line that names no trade-off ends the walk, so a "but" from four turns
    ago cannot answer a question about something else.
    """
    pointed = []
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict):
            continue
        said = " ".join(str(turn.get("user") or "").split())
        found = PICK_WORD.findall(said.lower())
        if not found or not [word for word in found if word not in PICK_ONLY_WORDS]:
            continue
        match = TRADE_OFF.search(said)
        if not match:
            if len(said.split()) <= 3 and not said.endswith("?"):
                # "the bikes", "the jobs": a two-word pointer back at the thing they have just
                # put down is not a new subject, so it is walked past - but only when it names
                # something in the trade-off it reaches ("the boiler" does not).
                pointed.append(said)
                continue
            return ()
        before = match.group(1).strip(" ,.")
        after = match.group(2).strip(" ,.")
        if (len(before.split()) < 2 or len(after.split()) < 2
                or NOT_A_SIDE.search(after) or DESIRE.search(before)
                or OBSTACLE.search(after)):
            return ()
        if _is_a_body_or_care_trade_off(said):
            return ()
        named = _a_named_side(after)
        if not named:
            return ()
        names = _names_in(said)
        if [line for line in pointed if not _names_in(line) & names]:
            return ()  # the short line was a subject of its own, not a pointer at this
        return named
    return ()


def _is_a_body_or_care_trade_off(said):
    """True when the trade-off is about their health, their mood or somebody in care.

    The health sets are the bot's own reading of a body, and they are read here for the same
    reason: a side taken on "the pain is worse at night but i dont want to bother the doctor" is
    a side taken on going to the doctor, which is nobody's pick to make.
    """
    words = set(re.findall(r"[a-z']+", said.lower()))
    if words & (BODY_PARTS | SYMPTOM_WORDS | HEALTH_WORDS | CHOICE_HEALTH | WORRY_WORDS):
        return True
    return bool(LEAN_NOT.search(said))


def _a_leaning_side(clean, memory):
    """The bot's own side of a trade-off the person has just put down, or None.

    "one pays more but the people are nicer in the other" / "what would you do" is a question a
    friend answers by leaning: the decide pool said "Not mine to decide, sorry", which is honest
    about what the bot knows and useless to the person who has already made the comparison.
    """
    # `PICK_ASK` does not cover "what would you do" - that is `LEAN_ASK`, the ask that only means
    # something once a trade-off is on the table - so both readings get in here, and the line then
    # has to be only the ask: "what would you do about the bike i just bought" names a subject of
    # its own and keeps its own answer.
    if not _a_bare_pick(clean) and not LEAN_ASK.search(clean):
        return None
    if not _a_lean_only_line(clean):
        return None
    if _in_a_care_thread(memory):
        return None
    side = _a_trade_off(memory)
    if not side:
        return None
    return _choose(TRADE_OFF_LEAN, memory, clean).format(side=side)


def _my_pick(clean, memory):
    """The bot's own pick, when the line asks for it and names nothing of its own."""
    offered = _offered(memory)
    if not _a_bare_pick(clean) and not (offered and PICK_BACK.match(str(clean or "").strip())):
        return None
    if _in_a_care_thread(memory):
        return None  # nothing blithe straight after a bereavement, a crisis or an emergency
    if offered:
        seed = len(memory.get("turns") or []) * 7919 + sum(ord(ch) for ch in clean)
        name, note = offered[random.Random(seed).randrange(len(offered))]
        if note:
            pool = [line.format(name=name, note=note) for line in MY_PICK_NOTE]
        else:
            pool = [line.format(name=name) for line in MY_PICK]
        return _choose(pool, memory, clean)
    if PICK_ADVICE.search(clean):
        return None
    return _choose(MY_PICK_ASK, memory, clean)


# The ask on its own, with nothing else in the line: the moment it names a subject of its own
# ("is that a bad idea for a birthday") it is a question about that subject, not a verdict asked
# for on the plan already on the table.
JUDGE_ASK = re.compile(
    r"(?:^|\b(?:ok|okay|so|and|but|hmm|well|wait|honestly|seriously)\b )"
    r"(?:is|was|would|will)\s+(?:that|this|it)\s+(?:be\s+)?(?:such\s+)?(?:a\s+|an\s+)?"
    r"(?P<face>" + JUDGE_ASKS_SLIGHT + r"|" + JUDGE_ASKS_FINE + r"|" + JUDGE_ASKS_MAD + r")"
    r"(?:\s+" + JUDGE_NOUN + r")?"
    r"(?:\s+(?:or\s+not|then|though|tho|or\s+what|at\s+all))?"
    r"$"
    r"|(?:^|\b(?:ok|okay|so|and|but|hmm|well)\b )does\s+(?:that|this|it)\s+"
    r"(?:sound|seem|look)\s+(?:like\s+)?(?:a\s+|an\s+)?"
    r"(?P<face2>" + JUDGE_ASKS_SLIGHT + r"|" + JUDGE_ASKS_FINE + r"|" + JUDGE_ASKS_MAD + r")"
    r"(?:\s+" + JUDGE_NOUN + r")?$"
    r"|(?:^|\b(?:ok|okay|so|and|but|hmm|well)\b )am\s+i\s+(?:being\s+)?"
    r"(?P<face3>" + JUDGE_ASKS_MAD + r"|" + JUDGE_ASKS_SLIGHT + r")$")
# The same ask with nothing to point at: the plan is on the table from the line before, so the
# whole line is the verdict word. It only counts where a plan is already named (see
# `_a_verdict_on_their_plan`): an adjective with nothing on the table is not a question.
JUDGE_ASK_BARE = re.compile(
    r"^(?:(?:ok|okay|so|and|but|hmm|well|honestly|seriously)\s+)?"
    r"(?:(?:does|would|is|was)\s+(?:that|this|it)\s+)?"
    r"(?:(?:sound|seem|look)\s+(?:like\s+)?)?"
    r"(?:(?:a|an)\s+)?"
    r"(?P<face>" + JUDGE_ASKS_SLIGHT + r"|" + JUDGE_ASKS_FINE + r"|" + JUDGE_ASKS_MAD + r")"
    r"(?:\s+(?P<bare_noun>" + JUDGE_NOUN + r"))?$")
JUDGE_PLAN_OPENING = re.compile(
    JUDGE_LEAD +
    r"(?:im|i am|i)\s+(?:going to|gonna|off to|out to|away to|heading to|heading off to"
    r"|planning to|planning on|thinking of|thinking about"
    r"|about to|want to|wanna|might|will|intend to|intending to|decided to|have decided to"
    r"|plan to|hoping to|hope to|looking to|keen to|aiming to|thinking i(?:d| would) like to"
    r"|think i(?:ll| will)|reckon i(?:ll| will))\s+(?P<plan>\S.{1,58})$"
    r"|" + JUDGE_LEAD +
    r"i\s+(?:have\s+)?decided\s+(?:to|i(?:'ll| will))\s+(?P<plan9>\S.{1,58})$"
    r"|" + JUDGE_LEAD +
    r"(?:my|the)\s+plan\s+is\s+to\s+(?P<plan2>\S.{1,58})$"
    # An age in front of it does not stop it being a plan: "im 40 and want to change career".
    r"|" + JUDGE_LEAD +
    r"(?:im|i am)\s+(?:nearly\s+|about\s+)?\d{2}\s*,?\s+and\s+(?:want|need|plan)\s+to\s+"
    r"(?P<plan3>\S.{1,58})$")
# What the person asked instead of said: "should i get a credit card" is a plan with a question
# mark on it, and the verdict line names it the same way.
JUDGE_SHOULD_OPENING = re.compile(
    JUDGE_LEAD +
    r"(?:should\s+(?:i|we)|(?:i|we)\s+(?:should|ought to))\s+(?P<plan>\S.{1,58})$")
# The openings that are a hope or an intention rather than a plan put down as one: "im hoping to run
# a half marathon", "im looking to rent out my spare room". A plan said this way is still the plan
# on the table - the composer was asking "say the idea in a line" after the person had said it in
# one - but the verdict after it is only this turn's when there is one to give.
JUDGE_HOPED_FOR = re.compile(
    r"\b(?:hoping|hope|looking|keen|aiming|intending|planning on)\b"
    r"|\bthinking i(?:d| would) like to\b", re.IGNORECASE)

# "Is that wise?" with nothing on the table is a judgement asked for in a line of its own, and it
# can be given without knowing the plan: what a friend says is that the test is the way out. Only
# the words that only ever mean "is the plan sound" - "is that good" and "is that great" are just
# as often about a bit of news, and after "my chicken is still pink" the food answer is the one.
# "am i mad" after a line that is itself about their own mind - hearing things, being watched,
# memory going - is not a plan question and not self-doubt about a choice. Standing down sends it
# to the annoyance pool ("Say it out loud to whoever caused it"), so this arm keeps it and says the
# two things that are true: nothing here reads as mad, and this is a GP's call, not a stranger's.
MIND_WORRY = re.compile(
    r"\b(?:hear(?:ing)?\s+(?:noises?|voices?|things|stuff)|see(?:ing)?\s+things|"
    r"watching\s+me|following\s+me|remember(?:ing)?\s+(?:anything|things)|"
    r"losing\s+(?:my\s+mind|it|my\s+memory)|forgetting\s+everything|going\s+mad)\b",
    re.IGNORECASE)
# A plan that names its own limit is not one a verdict can bless from here, however it is said:
# the hole is in the words.
JUDGE_NAMES_A_HOLE = re.compile(
    r"\bno\b|\bnothing\b|\ball\s+(?:my|our|your|the)\b|\bwithout\b|\bnot\s+\w+|\bnever\b"
    r"|\b(?:skip|skipping|stop|stopping|pause|pausing|come off|coming off)\s+(?:my|the|your)?\s*"
    r"(?:medication|meds|tablets|pills|insulin|treatment|doses?)\b", re.IGNORECASE)
# A wish can name an act, and no verdict can bless an act it would have to talk somebody out of.
# "i want to key my exs car" was answered "Nothing wrong with wanting to key my exs car." and "i
# want to stop eating" got "Yes, that is a reasonable way to do it". The hole in those is in what
# the wish is *for*, not in how they would do it, so it is read on the wish's own words: an act
# against a person or their things gets the answer the anger gets, and a wish against themselves
# or their money stands down to the topic that knows what to say about it.
JUDGE_ACT_AT_SOMEONE = re.compile(
    r"\b(?:key|keying|scratch|scratching|slash|slashing|smash|smashing|torch|torching|"
    r"vandalise|vandalize|vandalising|spike|spiking|drug|drugging|"
    r"hit|hitting|punch|punching|kick|kicking|strangle|strangling|choke|choking|stab|stabbing|"
    r"shoot|shooting|kill|killing|poison|poisoning|harm|harming|hurt|hurting|"
    r"slap|slapping|smack|smacking|thump|thumping)\s+(?:\w+\s+){0,3}?"
    r"(?:him|her|them|"
    r"(?:my|his|her|their|your|our|somebody's|someone's)\s+(?:\w+))", re.IGNORECASE)
# An answer that opens with the answer - "Yes, once, and make it easy to answer...", "No, not with
# the state of that roof" - has already ruled on the plan, and a verdict pasted over it is the
# weaker reply: "im going to text him back / am i being stupid" wants that advice, not a blessing.
# "Once" was in this list and it was the wrong word for it: an answer that opens on "once" almost
# always opens on a condition, not on a ruling - "Once you can run for an hour without stopping, a
# half marathon takes twelve to sixteen weeks" has not said yes or no to anything, so the verdict
# after it is still this turn's. "Yes, once, and make it easy to answer" is caught by the "yes".
JUDGE_ANSWERS_FIRST = re.compile(
    r"^\W*(?:yes|no|nope|not|don'?t|never|definitely|probably|only)\b", re.IGNORECASE)
# A card that opens on its own heading - "Yes: an easy hour on a bike burns roughly 300 to 400
# calories", "No: a dog left alone all day will chew" - has ruled on the question the card answers,
# not on the plan the person has put down since. The colon is how this bot's knowledge cards open,
# and reading it as a spoken "Yes," is how a plan put down for a verdict was answered with nothing:
# "i plan to cycle 100 miles with no training" / "is that daft" got the search hedge, because the
# card above it began "Yes:" and the verdict stood down as already given. A spoken ruling keeps its
# comma ("Yes, once, and make it easy to answer"), so only the heading is read here.
JUDGE_A_CARD_HEADING = re.compile(r"^\W*(?:yes|no)\s*:\s", re.IGNORECASE)
# An act against somebody, something illegal, or harm to their own body is not a plan to bless,
# whatever the words: "i want to drink a bottle of wine every night", "smoke weed every day", "lie
# on my cv", "stop paying tax" all walked through the fence the harm words had.
JUDGE_NOT_A_PLAN_TO_BLESS = re.compile(
    r"\b(?:drink|drinking|booze)\b(?:\s+\w+){0,6}?\s+"
    r"(?:every\s+(?:night|day|evening)|(?:a|one)\s+bottle|a\s+night|nightly|daily)\b"
    r"|\b(?:smoke|smoking|vape|vaping)\s+(?:weed|pot|dope|skunk|crack|heroin|coke|cocaine|speed)\b"
    r"|\b(?:weed|pot|cocaine|heroin|crack)\s+every\s+(?:day|night)\b"
    r"|\blie\s+(?:on|in)\s+(?:my|the)\s+(?:cv|resume|application|tax\s+return)\b"
    r"|\b(?:stop|stops|evade|evading|dodge|dodging)\s+paying\s+tax\b|\btax\s+evasion\b"
    r"|\bfiddle\s+(?:my\s+)?(?:tax|taxes|expenses|hours)\b"
    r"|\bclaim\s+(?:benefits|housing\s+benefit|universal\s+credit)\s+(?:i(?:'m| am)\s+not|"
    r"i\s+shouldnt|i\s+shouldn'?t)\b", re.IGNORECASE)
# What people say instead of the verb: nobody says "i want to steal", they say where from. The
# object is the tell, so the source is what this reads - work, the till, the shop - and a loan from
# a person or their own savings stays an ordinary plan.
JUDGE_TAKING_SOMETHING = re.compile(
    r"\b(?:take|taking|took|nick|nicking|pinch|pinching|borrow|borrowing|"
    r"help\s+myself\s+to|helping\s+myself\s+to)\b(?:\s+\w+){0,5}?\s+"
    r"(?:from|out\s+of)\s+(?:work|the\s+till|the\s+shop|the\s+office|the\s+company|"
    r"the\s+stockroom|the\s+warehouse|the\s+club|stock)\b", re.IGNORECASE)
# There is no ordinary plan that is lying to somebody: unlike "cheat on my diet", the person lied
# to is a person, so the words alone are the tell.
JUDGE_LYING = re.compile(r"\b(?:lie|lying|lied)\s+(?:to|about)\b", re.IGNORECASE)
# The one thing that looks like a hit and is not: "i want to smash my goals", "i want to hit my
# numbers". They are targets, and a verdict on a target is the ordinary kind.
JUDGE_A_TARGET = re.compile(
    r"\b(?:smash(?:ing)?|hit(?:ting)?|beat(?:ing)?|punch(?:ing)?|kick(?:ing)?)\s+"
    r"(?:(?:my|your|his|her|their|our)\s+)?"
    r"(?:goals?|personal\s+bests?|pbs?|records?|targets?|numbers?|deadlines?|quota|quotes?)\b",
    re.IGNORECASE)
# Taking is never a plan to bless, whatever the object: there is no version of "i want to steal
# from work" that a verdict may say is fine. What is left out is the taking that is not taking -
# "steal a few hours", "steal the show" - because those are plans like any other.
JUDGE_TAKING = re.compile(
    r"\b(?:steal|stealing|shoplift|shoplifting|rob|robbing|mug|mugging|"
    r"burgle|burgling|hack|hacking|blackmail|blackmailing|defraud|defrauding)\b"
    r"(?!\s+(?:a\s+few|time|the\s+(?:show|scene|limelight|spotlight|march|day)|"
    r"a\s+(?:march|kiss|glance|look|moment|nap|day)\b))",
    re.IGNORECASE)
# A wish against the person themselves, or one nobody could take a verdict on from here: starving
# themselves, and money at a scale that is the money entry's question and not this one's.
JUDGE_WISHES_HARM = re.compile(
    r"\b(?:stop|stopping|quit|quitting|give\s+up|giving\s+up|cut\s+out|cutting\s+out)\s+"
    r"(?:eating|food|meals)\b"
    r"|\b(?:eat|eating|ate)\s+nothing\b|\bstarve\s+myself\b|\bmake\s+myself\s+sick\b"
    r"|\bpayday\s+loan\b|\bloan\s+shark\b|\bgambl(?:e|ing)\b|\bbet\s+(?:my|our|the)\b"
    r"|\bborrow\s+(?:a\s+)?[\u00a3$\u20ac]?\d{3,}", re.IGNORECASE)

# ...unless the line names the thing being judged: "was that a bad idea" is the same ask as "was
# that stupid", and only the bare "is that bad" is the one that means somebody else's news.
JUDGE_JUDGES_A_NOUN = re.compile(
    r"\b(?:bad|terrible|awful|dreadful|wrong)\s+" + JUDGE_NOUN + r"\b", re.IGNORECASE)
# A reply above that already made the decision leaves the turn alone: the dog answer ends "If that
# sounds fine rather than like a sacrifice, get one", which is the verdict, and a second one on top
# of it is the weaker answer. The test is the last sentence, because that is where an answer puts
# what it thinks the person should do: a reply that ends on a step ("Ask when you will hear back")
# has given advice, not a verdict, and the turn is still this one's.
JUDGE_DECISION_LEAD = re.compile(r"^(?:if|unless|so|then|otherwise|either|worth)\b", re.IGNORECASE)
# A hole of the person's own body or their own medicine is not a plan to weigh: the answer there
# is the health one, and a friend does not say "that is the part to answer for" about a week off
# somebody's tablets.
JUDGE_HOLE_SAFETY = re.compile(
    r"\b(?:skip|skipping|stop|stopping|pause|pausing|come\s+off|coming\s+off)\s+"
    r"(?:my|the|your)?\s*(?:medication|meds|tablets|pills|insulin|treatment|doses?)\b"
    r"|\bmeds\b|\bmedication\b", re.IGNORECASE)
# The faces that ask for a ruling on a plan and nothing else, so the hole in the plan can be
# answered rather than deferred to an entry that has no word to match.
JUDGE_ASKING_FOR_A_CAUTION = frozenset("""stupid daft dumb silly idiotic thick bad terrible awful
    dreadful wrong good great sensible wise smart clever reasonable mad crazy insane nuts mental
    unhinged""".split())
JUDGE_JUDGEMENT = re.compile(
    r"\b(?:is|would be)\s+(?:a\s+)?(?:good|bad|fine|great|sensible|wise)\s+idea"
    r"|\bworth\s+(?:doing|it|a\s+(?:go|try))\b|\bnot\s+worth\b"
    r"|\bgo for it|\bhold off\b", re.IGNORECASE)





# The plan openings that put either a step or a place after the "to": "im going to learn
# spanish" and "im going to the gym". Every other opening of a plan ("want to", "thinking of",
# "planning to") is an infinitive, so what follows its "to" is a verb.
JUDGE_MOVING_TO = re.compile(r"\b(?:" + stepwords.MOVING_TO + r")\s*$", re.IGNORECASE)


def _the_opening_before(match):
    """The words of the line in front of the plan the opener matched: "im going to"."""
    for group in ("plan", "plan2", "plan3", "plan9"):
        if match.group(group):
            return match.string[:match.start(group)]
    return ""


def _a_gerund(word):
    """True when the word is an "-ing" form a sentence can open on ("getting", "moving")."""
    word = word.strip(".,!?;:'\"")
    return len(word) >= 5 and word.endswith("ing") and word not in JUDGE_NOT_A_GERUND


# The word that opens a noun phrase rather than a verb phrase: after "im thinking about a cat" the
# words left over are "a cat", and "wanting to a cat" is not English. The "to" is only right where
# what follows is what the person would do, so a phrase that opens on one of these takes "wanting"
# alone ("wanting a cat", "wanting more time off").
A_NOUN_PHRASE_OPENS = frozenset((
    "a", "an", "the", "my", "your", "our", "their", "his", "her", "its", "some", "any", "more",
    "less", "another", "one", "two", "three", "both", "all", "no", "nothing", "none", "it",
))


def _a_plan_said_back(phrase):
    """"wanting to quit your job", or "wanting a cat" where the words are a thing and not a step."""
    words = phrase.split()
    opening = "wanting " if words and words[0].lower() in A_NOUN_PHRASE_OPENS else "wanting to "
    return opening + _yours(phrase)


def _a_plan_phrase(said):
    """The person's plan as a phrase to say back ("wanting to ask for a pay rise"), or "".

    Nothing is made up: the words are theirs, only the opening is folded into a phrase that fits
    in front of a sentence. A plan with a clause in it ("quit my job but keep the flat") is left
    alone, because saying half of it back reads as not having listened.
    """
    text = _matchable(said)
    match = JUDGE_PLAN_OPENING.search(text)
    if match:
        words = (match.group("plan") or match.group("plan2") or match.group("plan3")
                 or match.group("plan9") or "").split()
        if not words or len(words) > 7 or any(word in JUDGE_PLAN_STOP for word in words):
            return ""
        phrase = " ".join(words)
        if not re.search(r"[a-z]", phrase) or not re.search(r"[a-z]{3}", phrase):
            return ""
        if _a_gerund(words[0]):
            return _yours(phrase)  # "getting a rescue dog" is already the shape a sentence wants
        if JUDGE_MOVING_TO.search(_the_opening_before(match)) and not stepwords.a_step(words[0]):
            # "im going to the gym", "im going to spain in may", "im going to bed early tonight":
            # the words after the "to" are where they are going, not a step, and "wanting to the
            # gym" is not a sentence. They go back behind their own "going to".
            return _yours("going to " + phrase)
        return _a_plan_said_back(phrase)
    match = JUDGE_SHOULD_OPENING.search(text)
    if match:
        words = match.group("plan").split()
        if not words or len(words) > 7 or any(word in JUDGE_PLAN_STOP for word in words):
            return ""
        if not re.search(r"[a-z]{3}", " ".join(words)):
            return ""
        return _a_plan_said_back(" ".join(words))
    return ""


# The plan is said back as the person put it, so their "my job" has to become "your job" on the
# way out: "nothing daft about wanting to quit my job" reads as the bot talking about itself.
MINE = re.compile(r"\b(my|me|myself|mine)\b", re.IGNORECASE)


def _yours(phrase):
    """The person's own phrase turned to face them: "quit my job" -> "quit your job"."""
    return MINE.sub(lambda found: YOURS.get(found.group(1).lower(), found.group(1)), phrase)


def _the_plan_on_the_table(memory):
    """The plan the person has just named, or "" when the last thing they said named none."""
    return _the_plan_and_its_line(memory)[0]


def _the_plan_is_the_last_thing_said(plan_line, memory):
    """True when nothing but a nod has been said since the plan was named.

    The plan is read from the last few turns, so a subject put down in between is read past:
    "im thinking of getting a cat" / "my knee is clicking" / "is that a good idea" is a question
    about the knee, and the pool's confident "yes, getting a cat is a reasonable thing to aim at"
    rules on the cat. The reading is right; it is the remembering that reaches back past the
    change of subject. So a verdict is given while the person has said nothing else since: a nod
    ("ok then", "right") keeps the plan, and a turn with a subject of its own ends it. A turn
    that shares a word with the plan ("i had a sugar craving" after a plan to give up sugar) is
    still about the plan, so lunch is a new subject but the craving is not.
    """
    said = [_matchable(turn.get("user")) for turn in (memory.get("turns") or [])
            if isinstance(turn, dict)]
    said = [line for line in said if line]
    about = {word for word in re.sub(r"[^a-z0-9 ]", " ", plan_line).split()
             if len(word) > 2 and word not in JUDGE_NOD_WORDS}
    for stop in range(len(said) - 1, -1, -1):
        if said[stop] == plan_line:
            break
    else:
        return True  # not read from this list at all: the reader knows more than this does
    for line in said[stop + 1:]:
        content = [word for word in re.sub(r"[^a-z0-9 ]", " ", line).split()
                   if len(word) > 2 and word not in JUDGE_NOD_WORDS]
        if not content or about & set(content):
            continue  # a nod, or a turn still about the plan
        return False
    return True


def _the_plan_and_its_line(memory):
    """The plan, and the line that named it: "not insured" is in the line, not in the phrase."""
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    for turn in reversed(turns[-4:]):
        said = _matchable(turn.get("user"))
        if not said or not [word for word in said.split() if word not in JUDGE_NOD_WORDS]:
            continue  # a nod or an "ok then": keep looking for the line that named something
        plan = _a_plan_phrase(said)
        if plan:
            return plan, said
        if JUDGE_PLAN_OPENING.search(said) or JUDGE_SHOULD_OPENING.search(said):
            # The line named a plan this pool cannot say back in one phrase (too long, or with a
            # clause in it): it is still the plan on the table, and the caller must not ask the
            # person to name it again. So the line comes back with no phrase.
            return "", said
        # A line with something in it that is not a plan ("my sister is ill") says nothing about
        # what the plan is, and stopping here would throw away the plan named a turn earlier:
        # "im going to quit sugar" / "ok then" / "is that stupid" still has one on the table.
    return "", ""


def _the_reply_above_judged(memory, past_a_question=False):
    """True when the bot's last answer already said what the person should do about the plan.

    "im thinking of getting a rescue dog" is answered with the three questions that decide it, and
    it ends on the decision - "if that sounds fine rather than like a sacrifice, get one" - so the
    person's follow-up "is that a good idea" has already been answered, and a verdict bolted on top
    of it ("yes, that is a reasonable way to do it") is the weaker of the two. The answer to the
    pay-rise advice ends on a step ("ask when you will hear back"), which is advice and not a
    verdict, so that turn is still this one's.
    """
    said = (last_bot(memory) or "").strip()
    if not said:
        return False
    if JUDGE_A_CARD_HEADING.match(said):
        # "Yes: butter is mostly fat ..." is a card's heading, not a ruling on the plan that came
        # after it. The verdict is still this turn's to give.
        return False
    if said.endswith("?") and not past_a_question:
        # The bot asked them something ("what's the part that's under your skin?"): that question
        # is what this turn is for, and a verdict pasted over it ignores what the bot just said.
        return True
    if JUDGE_JUDGEMENT.search(said) or JUDGE_ANSWERS_FIRST.match(said):
        return True
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", said) if part.strip()]
    last = sentences[-1] if sentences else said
    return bool(len(last.split()) <= 20 and JUDGE_DECISION_LEAD.match(last))


# The line that put a place on the table: a trip going, booked or hoped for. Read from the
# person's own turn, never from the bot's, because the bot's answer names the town too.
TRIP_NAMED = re.compile(
    r"\b(?:going to|going away|off to|holiday to|holidays? in|trip to|weekend in|week in|"
    r"flying to|driving to|booked (?:a |our |the )?(?:trip|holiday|flights?|hotel|weekend)|"
    r"thinking of going|thinking about going|hoping to go|planning to go|visiting)\b", re.I)
# A trip is to a place, and half of the words that come after a verb of going are not places at
# all: "we are visiting my mum in hospital tomorrow" then "is it ok" is a question about the visit,
# "we are going to a wedding in june" then "is it nice" is a question about the wedding, and "im
# going to see the doctor about my knee" then "is it worth it" is the knee's. All three reached
# this pool on the verb of going alone and lost the card that was answering them ("However it
# looks today, ask the ward what they expect next" for the hospital visit). The place the person
# is asking about is what the trip is to, so a line carrying one of these words is not a place.
NOT_A_PLACE = re.compile(
    r"\b(?:hospital|doctors?|dentist\w*|gp|clinic|a&e|ward|surgery|appointment|scan|"
    r"results?|wedding|funeral|christening|baptism|court|work|school|nursery|college|uni|"
    r"university|gym|physio\w*|therapy|therapist|vets?|interview|meeting|party|gig|concert|"
    r"match|church|prison|jail|care home|tip|dump|shops?|supermarket|swimming|parents|"
    r"mum|dad|mother|father|sister|brother|nan|nana|grandma|grandad|gran|friend|family|"
    r"cinemas?|pictures|theatres?|theaters?|films?|movies?|screening|exhibition|"
    r"galler(?:y|ies)|musicals?|opera|ballet)\b",
    re.I)
# The whole of the ask: "is it nice", "is it any good", "was it busy", "is it worth going", and
# the same with the mark on the end. Only words of judgement, so "is it far" and "how do i get
# there" stay with whatever can answer them.
PLACE_EVALUATIVE = re.compile(
    r"\b(?:nice|good|any good|worth (?:it|going|a visit|the trip|seeing)|busy|expensive|cheap|"
    r"quiet|lively|packed|safe|warm|sunny|rainy|boring|ok|okay|family friendly)\b", re.I)
PLACE_OPENER = re.compile(r"^(?:is|was|are|were|do|does|did|would|will|any)\b", re.I)


def _a_place_asked_about(clean, memory):
    """The pool for "is it nice" about a trip the person has just named, or None.

    Read from the person's own last substantive turn, and only when the whole ask is a judgement
    of the place: a line with anything else in it - "is it far", "how do i get there from the
    station" - is a question the answers can take, and this pool must not stand in front of them.
    Where a card does answer the town it keeps the turn, because this is claimed only for the
    ask the nod pool was answering with a sign-off. A trip to a hospital, a wedding or a doctor's
    appointment is not a place (`NOT_A_PLACE`), and neither is an evening at the cinema or the
    theatre: `is it any good` there asks about the film or the play, which the card answers, so
    the card keeps the turn.

    A price verdict on a thing you buy to get there, or to eat and sleep once you are there, is
    not a verdict on the place: "we are thinking of going to cornwall in july" then "is the train
    expensive that far" was given "No first-hand knowledge of the place, sorry. Are you going for
    the sights, the food or the peace?" - a question about a trip's own pleasures, asked of a
    fare. The trip in the thread sets the scene; the thing in the line is what is asked about,
    and a fare is a price (bot/compose/the_rule_for_it.py, FARE_PRICE_RULE).
    """
    said = _matchable(clean).rstrip(" ?.!,")
    if not said or len(said.split()) > 6:
        return None
    if not PLACE_EVALUATIVE.search(said):
        return None
    from .the_rule_for_it import A_FARE_OR_A_TICKET, PRICE_VERDICT  # the pools load later
    if A_FARE_OR_A_TICKET.search(said) and PRICE_VERDICT.search(said):
        # The fare, the flight, the hotel: a thing with a price of its own, asked about as a
        # price. The trip the thread named is only where it goes.
        return None
    if not (PLACE_OPENER.match(said) or "?" in str(clean or "")):
        return None
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    for turn in reversed(turns[-3:]):
        mentioned = _matchable(turn.get("user"))
        if not mentioned or not [word for word in mentioned.split()
                                 if word not in JUDGE_NOD_WORDS]:
            continue  # a nod in between: the trip named before it is still on the table
        if NOT_A_PLACE.search(mentioned):
            return None  # a going, not a place: the card that answers the visit keeps its turn
        return list(A_PLACE_I_DONT_KNOW) if TRIP_NAMED.search(mentioned) else None
    return None


def a_verdict_on_their_plan(clean, memory, past_a_question=False):
    """The composer's verdict on the plan the person has just put down, or None.

    The public name, for modules that have to know what this file would say before they claim the
    line. `bot/modules/chat.py` reads it: its own reply to "is that a good idea" is a hand-back
    ("the decision is yours to weigh"), and a hand-back must not take the turn from this answer,
    which rules on the plan ("Yes - getting a cat is a reasonable thing to aim at"). One reading,
    used by both, so the two cannot drift apart.
    """
    return _a_verdict_on_their_plan(clean, memory, past_a_question)


def _a_verdict_on_their_plan(clean, memory, past_a_question=False):
    """The pool for "is that a stupid idea", or None when the line is not asking for a verdict."""
    # A question mark on the end is how the question is typed, not part of it. Every form of this
    # ask is anchored to the end of the line, so "is that a stupid idea?" - the way nearly everyone
    # writes it - matched nothing and got the search hedge, while the same words with no mark got
    # the verdict. The mark (and a stray full stop or comma) comes off before the line is read.
    said = _matchable(clean).rstrip(" ?.!,")
    asked = JUDGE_ASK.match(said)
    if not asked:
        bare = JUDGE_ASK_BARE.match(said)
        if not bare or not (bare.group("bare_noun")
                            or bare.group("face") in JUDGE_BARE_FACES):
            return None
        if not _the_plan_on_the_table(memory):
            # "stupid?" with nothing on the table is not a question about anything the bot can
            # see; asking what the idea is belongs to the pools that do that, not here.
            return None
        asked = bare
    if _in_a_care_thread(memory):
        return None  # nothing glib straight after a bereavement, a crisis or an emergency
    face = (asked.group("face") or asked.group("face2") or asked.group("face3") or "").lower()
    if face in JUDGE_NOT_A_VERDICT and not JUDGE_JUDGES_A_NOUN.search(said):
        return None  # "is that bad" after somebody's news, whatever plan is on the table
    plan, plan_line = _the_plan_and_its_line(memory)
    stale = bool(plan_line) and not _the_plan_is_the_last_thing_said(plan_line, memory)
    if stale:
        # They have moved on to something else, so the plan two turns back is not what this ask is
        # about. The ask is answered the way it is answered with nothing on the table - "tell me
        # the idea in a line" - rather than with a verdict on the old plan.
        plan, plan_line = "", ""
    if plan_line and (JUDGE_NAMES_A_HOLE.search(plan) or JUDGE_NAMES_A_HOLE.search(plan_line)):
        # "skip my medication for a week", "put all my savings in bitcoin", "drive with no sleep":
        # the line names the part that makes it risky, so the verdict has nothing to judge and the
        # topic's own entry - the health one, the money one - is the answer that knows what to say.
        #
        # ...which holds only where an entry can answer. The ask here is the judgement and nothing
        # else ("is that daft"), so it says no word the entry could match, and standing down leaves
        # the floor: "i plan to cycle 100 miles with no training" / "is that daft" was told "I'd
        # rather not guess, a quick search online will get you a solid answer", and "im going to
        # put all my savings in bitcoin" / "is that a stupid idea" was told the same about the
        # person's own savings. The hole is the part a friend pushes back on, so the verdict names
        # it as the part to answer for instead of blessing the plan (`JUDGE_WORTH` would say
        # "Nothing daft in wanting to put all my savings in bitcoin") - except where the hole is
        # their own medicine or their own body, which is nobody's to weigh from here.
        if JUDGE_HOLE_SAFETY.search(plan_line) or JUDGE_HOLE_SAFETY.search(plan or ""):
            return None
        if face in JUDGE_ASKING_FOR_A_CAUTION:
            return [line.format(plan=plan, Plan=plan[:1].upper() + plan[1:])
                    for line in JUDGE_PLAN_HAS_A_HOLE]
        return None
    # The wish itself, before the pool is chosen: "is that a stupid idea" after "i want to key my
    # exs car" is not a plan to weigh up, and "is that a good idea" after "i want to stop eating"
    # is not one a verdict may agree with.
    if plan or plan_line:
        wish = " ".join(part for part in (plan, plan_line) if part)
        if not JUDGE_A_TARGET.search(wish) and (JUDGE_ACT_AT_SOMEONE.search(wish)
                                             or JUDGE_TAKING.search(wish)):
            said_back = harm.reply_for(plan_line, memory) if plan_line else None
            return [said_back] if said_back else list(JUDGE_WISH_ANGRY)
        if JUDGE_WISHES_HARM.search(wish) or JUDGE_TAKING_SOMETHING.search(wish) \
                or JUDGE_LYING.search(wish) or JUDGE_NOT_A_PLAN_TO_BLESS.search(wish):
            return None
    if plan_line and not plan:
        return None  # they named a plan; asking them to say it again is the worse answer
    if plan and _the_reply_above_judged(memory, past_a_question):
        if not JUDGE_HOPED_FOR.search(_matchable(plan_line)):
            return None  # the answer above already gave a verdict on this plan; it is the better one
        # They put the plan down as a hope or an intention - "im hoping to run a half marathon",
        # "im looking to rent out my spare room" - and the answer above already went as far as it
        # can, so there is no verdict to add. The words keep the reply they had before the plan was
        # readable at all: asking which idea it is reads as not having listened, and a verdict
        # pasted over the answer above is the weaker of the two. Except where the caller has said
        # the question mark was not an answer (`past_a_question`): then the plan is still the
        # plan and the pool is still the one to give.
        plan = ""
    if not plan and asked.group("face3"):
        # "am i mad" / "am i being daft" with nothing put down is a worry about their own mind or
        # their own worth, not a plan to rule on: "i feel stupid / am i being silly" is nobody's to
        # correct from here. When the line above is itself about their mind, standing down is not
        # enough - it lands on the annoyance pool - so that one is answered here.
        if MIND_WORRY.search(_matchable(memory.get("turns", [{}])[-1].get("user", ""))):
            return JUDGE_NO_PLAN_MIND
        return JUDGE_NO_PLAN_MAD if stale else None
    if not plan:
        if face in JUDGE_SELF_JUDGING:
            return JUDGE_NO_PLAN_MAD
        if face in JUDGE_ONLY_A_PLAN:
            return JUDGE_NO_PLAN
        if face in JUDGE_SOUNDS_FINE:
            return JUDGE_NO_PLAN_FINE
        return None  # "is that bad" with nothing named is somebody else's question
    pool = JUDGE_SANE if face in ("mad", "crazy", "insane", "nuts", "mental", "unhinged") else (
        JUDGE_FINE if face in ("good", "great", "sensible", "wise", "smart", "clever",
                               "reasonable")
        else JUDGE_WORTH)
    # `Plan` is the same phrase opening a sentence: the pools are written as sentences, and
    # a template that puts it first cannot hold a lowercase word.
    return [line.format(plan=plan, Plan=plan[:1].upper() + plan[1:]) for line in pool]


# "whats my favourite food", "which is my favourite colour", "do you know my favourite film":
# the person's own favourite, not the bot's. Only the ask shape, so a line that mentions their
# favourite in passing ("what should i cook for my favourite person") is left alone. The thing
# asked about is kept: it is what the chat is searched for.
OWN_FAVOURITE = re.compile(
    r"\b(?:what|which)(?:'?s| is| was)?\s+(?:my|our)\s+(?:\w+\s+){0,2}(?:favourite|favorite)\s+(\w+)"
    r"|\b(?:do|can) you (?:remember|know)\s+(?:my|our)\s+(?:\w+\s+){0,2}"
    r"(?:favourite|favorite)\s+(\w+)")
# What the person said it was, in their own words earlier in this chat.
A_FAVOURITE_SAID = re.compile(r"\bmy (?:favourite|favorite) (\w+) (?:is|was|would be)\s+"
                              r"([^.,!?;]{1,40})")

# Said when the store has nothing to recall for it. It does not claim the person never said it:
# what they said may have been read as something other than a favourite, and asking again is right
# either way.
OWN_FAVOURITE_LINES = (
    "Remind me - which one is it?",
    "Say it again and I will keep it in mind: which one?",
    "I don't have that one. What is it?",
)

# Said back when the chat does hold it: "my favourite food is curry" then "whats my favourite
# food" is the person checking the bot was listening, and the answer is the thing they said, not
# the bot's own taste (which was what the taste table gave) and not a shrug.
THEIR_FAVOURITE_BACK = (
    "You said {value} - is that still the one?",
    "{Value}, as far as I have it. Has that changed?",
    "{Value}, you told me. Still the one?",
)


def _their_favourite_said(thing, memory):
    """What the person said their favourite <thing> was in this chat, or None."""
    if not thing:
        return None
    for turn in reversed((memory.get("turns") or [])[-12:]):
        if not isinstance(turn, dict):
            continue
        found = A_FAVOURITE_SAID.search(_matchable(turn.get("user") or ""))
        if found and found.group(1) == thing:
            value = found.group(2).strip()
            if value and " " not in value[:1]:
                return value
    return None


def _their_favourite_back(thing, value):
    """The pool above with the thing and the value the person gave filled in."""
    return tuple(line.format(value=value, Value=value[:1].upper() + value[1:])
                 for line in THEIR_FAVOURITE_BACK)


def _taste(clean, memory, was_taste, asking, repaired=""):
    """The bot's own answer to a question about its tastes, or None if it is not one.
    `was_taste` says the bot's last reply was one, so "why that one?" has something to explain.

    `repaired` is the same line with its chat-speak put right ("whats ur favourite food" ->
    "whats your favourite food"), read only when the typed line is not this shape at all: the
    repair is what makes the question about the bot, and without it the line reached the search
    hedge while the identical line with "your" spelled out got a taste.
    """
    if was_taste and _reads_as_why(clean):
        return _choose(WHY_AFTER_TASTE, memory, clean)
    # The person's own favourite, asked of the bot. The store's recall answers it when it was told
    # (PRIORITY 7000, so it keeps the turn); when it was not, the taste table answered with the
    # bot's own favourite ("whats my favourite food" -> "Roast potatoes"), which is a different
    # question, and the alternative was the search hedge, which answers nothing. Asking back is the
    # honest reply either way: it is right whether or not the person said it earlier.
    if asking and OWN_FAVOURITE.search(clean):
        found = OWN_FAVOURITE.search(clean)
        thing = found.group(1) or found.group(2) or ""
        value = _their_favourite_said(thing, memory)
        if value:
            return _choose(_their_favourite_back(thing, value), memory, clean)
        return _choose(OWN_FAVOURITE_LINES, memory, clean)
    if repaired and repaired != clean and not _has(clean, OPINION_ASKS) \
            and _has(repaired, OPINION_ASKS):
        clean = repaired
    asked = _has(clean, OPINION_ASKS)
    if asked and _is_about_the_persons_own_life(clean):
        return None  # "what do you think about my landlord refusing repairs" is advice
    if not asked and _is_a_choice(clean) and not _has(_choice_advice(clean), ADVICE_WORDS):
        # The advice words are read on the line without a *joint* question frame: "should we get a
        # pizza or a curry tonight" puts the choice to the bot, and "should" there is the frame
        # rather than a request for advice. "Should I ..." stays as it was - that one is the
        # person's own life ("should i push back or just take it", "no i mean should i quit") and
        # the pools that weigh a decision are the right answer to it.
        asked = True
    if not asked and asking and any(_has(clean, phrases) for phrases, _ in TASTES):
        asked = True  # "Is it ever OK to recline your seat?" names a taste, not a fact
    if not asked:
        return None
    if _is_about_the_persons_own_life(clean) and _has(clean, FAVOURITE_WORDS):
        # "what's my favourite food" asks what the store already holds, and the table's answer is
        # the bot's own taste: the ask was read from the thing named, not from whose taste it is.
        # Only for a line with the word favourite in it: a choice between two of the person's own
        # people ("my mum or my dad for christmas") is about their life too, and it is still the
        # choice pool's line, which is the reply it has always had.
        return None
    for phrases, options in TASTES:
        if _has(clean, phrases):
            return _choose(options, memory, clean)
    if _is_a_choice(clean):
        return _choose(_choice_pool(clean, memory), memory, clean)
    if _has(clean, FAVOURITE_WORDS):
        return _choose(FAVOURITE_GENERAL, memory, clean)
    return _choose(TASTE_GENERAL, memory, clean)


_VENUE_RE = []


def _names_a_venue(clean):
    """True when the line names one of the places in `LIVE_VENUE`, singular or plural."""
    if not _VENUE_RE:
        joined = "|".join(re.escape(word) for word in
                          sorted(LIVE_VENUE, key=len, reverse=True))
        _VENUE_RE.append(re.compile(r"(?<![a-z])(?:" + joined + r")(?:s|es)?(?![a-z])"))
    return bool(_VENUE_RE[0].search(clean))


def venue_hours(text, memory=None):
    """True when the line asks when a named place opens, closes or is open.

    The composer's own reading, published for the arbiter, so that which lines are a question
    about a venue's hours is decided beside the pools that answer them. A place has to be named
    and open or close has to be in the line, and the composer's own pool has to be the hours
    one: "what time do hospitals let visitors in" is the visiting-hours answer's (no open or
    close in it), and "how do i open a bank account" reaches a different pool.
    """
    clean = str(text or "").strip().lower()
    if not _names_a_venue(clean) or not _has(clean, LIVE_OPEN_CLOSE):
        return False
    for kind, _phrases, options in LIVE_KINDS:
        if kind == "hours":
            return _live(clean, True, memory) == options
    return False


def venue_hours_lines():
    """The composer's honest lines for a venue's opening hours."""
    for kind, _phrases, options in LIVE_KINDS:
        if kind == "hours":
            return frozenset(options)
    return frozenset()
# The day's news and results, and where the day's match is on. No card about the world can hold
# them - they change by the hour - so the honest answer says the bot cannot see them and names the
# one place that can. The ask has to be about how something went or where to find it: "the match
# wont light" is a matchstick, "how long is a match" is the rules and "how did the interview go"
# is the person's own day, so all three keep the answer they had.
LIVE_RESULT_ASK = re.compile(
    r"\b(?:who\s+won|who(?:['\u2019]?s|\s+is)\s+winning|did\s+[a-z][a-z' ]{0,20}?\s+win|"
    r"what(?:s|'s| is| was)?\s+the\s+(?:final\s+)?score|(?:any|the)\s+results?\b(?!\s+of))")
LIVE_BARE_RESULTS = re.compile(r"\b(?:any|the)\s+results?\b")
# "how did the match go" is a result; "how did the meeting go" is the person's own day, and the
# news line would answer a question nobody asked. So this one counts only beside a word that says
# what was played.
LIVE_HOW_IT_WENT = re.compile(
    r"\bhow\s+did\s+(?!(?:it|that|this|things|everything|you|i)\b)"
    r"[a-z][a-z' ]{0,20}?\s+(?:go|do|get\s+on)\b")
LIVE_TABLE_ASK = re.compile(
    r"\b(?:top|bottom)\s+of\s+the\s+(?:league|table)|in\s+the\s+(?:league|table)|"
    r"still\s+in\s+the\s+cup|out\s+of\s+the\s+cup|through\s+to\s+the\s+next\s+round")
LIVE_LISTING_ASK = re.compile(
    r"\b(?:what|which)\s+channel\b|\bwhere\s+(?:can|do)\s+i\s+watch\b|"
    r"\bis\s+it\s+on\s+(?:the\s+)?(?:tv|telly|iplayer|bbc|itv|sky)\b|"
    r"\bwhat\s+time\s+(?:is\s+)?(?:kick\s*off|does\s+(?:the|it)\s+(?:start|kick\s*off))|"
    r"\bwhat\s+time\s+(?:is|does|do|will)\b[^?]{0,30}?\b(?:start|starts|kick\s*off|begin|"
    r"kick-off|coverage|highlights)\b|"
    r"\bwhen\s+(?:is|are)\s+(?:the|we|they)\s+(?:next\s+)?(?:match|game|fixture)|"
    r"\bwhen\s+do\s+(?:we|they)\s+play\b")
LIVE_WORLD_ASK = re.compile(
    r"\b(?:latest|breaking|big|any)\s+news\b|\bnews\s+(?:today|tonight|this\s+morning)\b|"
    r"\b(?:in|from)\s+the\s+(?:news|world)\b|\bheadlines?\b|\bspill\s+the\s+news\b|"
    r"\b(?:happening|going\s+on)\s+in\s+the\s+world\b|\bwhat\s+the\s+news\s+is\b")

# "in the world" is the *scope* of a question that stands still, not the day's news: "what is the
# biggest city in the world", "the tallest building in the world", "how many people live in the
# world" all named the world as the place a fact holds, and all got "I can't see the news from
# here, sorry" - a shrug at a question with a settled answer. A news word in the line still makes
# it the news ("any news from the world", "whats going on in the world"), and "in the news" is
# left alone, because that is where a story lives.
_WORLD_AS_SCOPE = re.compile(r"\b(?:in|from)\s+the\s+world\b")
_A_NEWS_WORD_BESIDE = re.compile(
    r"\b(?:news|headlines?|happening|going\s+on|latest|breaking|stories|story)\b")


def _the_scope_of_a_standing_ask(clean):
    """True when "in the world" only says where a standing fact holds, so it is not the news."""
    if not _WORLD_AS_SCOPE.search(clean):
        return False
    return not _A_NEWS_WORD_BESIDE.search(_WORLD_AS_SCOPE.sub(" ", clean))
LIVE_SPORT = ("match", "game", "score", "scores", "football", "rugby", "cricket",
              "tennis", "boxing", "league", "cup", "final", "semi", "fixtures",
              "fixture", "kick off", "kick-off", "goal", "goals", "wicket", "innings",
              "test match", "playoffs", "play offs", "f1", "formula one", "grand prix",
              "the ashes", "the table")
# Their own news, not the world's: "any news from the hospital", "did my son win", "my exam
# results". A news site cannot answer those, so they are not this reader's.
LIVE_NOT_WORLDS = re.compile(
    r"\b(?:my|our|his|her|their)\s+(?:son|daughter|kid|kids|child|children|baby|wife|husband|"
    r"partner|mum|mom|mother|dad|father|brother|sister|friend|boss|exam|scan|test|interview|"
    r"application|case|claim|order|orders|delivery|parcel|package|refund|return|booking|"
    r"reservation|offer|mortgage|tenancy|landlord|visa|passport|complaint|payslip|pension|"
    r"insurance|quote|repair|job)\b|\bexam\s+results?\b|\bthe\s+(?:exam|interview|scan|audition|"
    r"appraisal|blood\s+test|driving\s+test|meeting|appointment|case|court|hearing|audition|"
    r"presentation|visit)\b|\b(?:my|our|his|her|their)\s+(?:blood\s+test|x-?ray|scan|results?)\b|"
    r"\bresults?\s+(?:from|of|at)\s+(?:(?:the|my|our|his|her|their)\s+)?"
    r"(?:doctor|gp|surgery|"
    r"hospital|scan|test|x-?ray|clinic|consultant|nurse|school|exam|dentist|vet)\b")
LIVE_A_YEAR = re.compile(r"\b(?:19|20)\d\d\b")
# The prize they bought a ticket for is not the day's news, and the news line asks for a story
# that does not exist: "did i win the lottery" and "did my ticket win" were sent to a news site
# (fancy-hawk). The draw word decides, so "did arsenal win" keeps the reader.
LIVE_OWN_DRAW = ("lottery", "lotto", "raffle", "sweepstake", "sweepstakes", "tombola",
                 "scratchcard", "scratch card", "bingo", "jackpot", "prize", "prizes",
                 "ticket", "tickets", "the draw", "numbers come up", "my bet", "the pools",
                 "competition", "euromillions")
# "did i win", with nothing else in the line, is the same ticket.
LIVE_A_BARE_WIN = re.compile(r"\bdid\s+(?:i|we)\s+win\s*[?.!]*$")
# "whos winning" on its own is about a game and nothing else: a score is what it asks for, so it
# is a line the scores reader takes without a question mark. With a subject after it ("whos
# winning the election") it is somebody else's question and this does not fire.
# A bare "who won" is left out on purpose: after "when was the battle of waterloo" it is the same
# question again, and the scores line would answer a history question with last night's football
# (pastname-multi-01 in the deck). Only the present tense is a game and nothing else.
LIVE_A_BARE_WINNING = re.compile(r"\bwho(?:['\u2019]?s|\s+is)?\s+winning\s*[?.!]*$")
# "any accidents on the m6" is a question said without a question mark, and it names the road and
# the thing asked about: the mishap is the live figure, so the words carry the ask.
LIVE_ANY_ACCIDENT = re.compile(r"\b(?:any|an?)\s+accidents?\b|\baccidents?\s+(?:on|at)\b")
LIVE_NEWS_LINES = (LIVE_NEWS_REPLY,)
def _the_scores_line():
    """The one honest line about a score or a table, or None.

    `bot/knowledge/sport.py` already answers "who won" and "the score" when no card does, with
    `_RESULTS_REPLY`, and the bot should say one thing about a result however the question is
    put. So the line is borrowed rather than written again here (fancy-hawk). It is read at call
    time because the knowledge tables import this package while they are built.
    """
    from ..knowledge.sport import _RESULTS_REPLY
    return (_RESULTS_REPLY,)
LIVE_LISTING_LINES = (
    "No live listings here, sorry. The TV guide on the box or the channel's own app has what is "
    "on and when, and the club's page has the kick-off and which side it is on.",)
LIVE_WHICH_RESULTS = (
    "Results of what - a match, an exam, or something you are waiting to hear about?",)


def _the_days_news(clean, asking):
    """The honest line for the day's news, a result or a listing, or None.

    "how did the match go" and "any news today" want the place the answer lives, not a guess; a
    line about the person's own news, a year in the line (history) or a contest that is not played
    keeps whatever answer it had.
    """
    if (LIVE_A_YEAR.search(clean) or LIVE_NOT_WORLDS.search(clean)
            or _has(clean, LIVE_OWN_DRAW) or LIVE_A_BARE_WIN.search(clean)):
        return None
    played = _has(clean, LIVE_SPORT)
    if LIVE_LISTING_ASK.search(clean) and played:
        return LIVE_LISTING_LINES
    if LIVE_TABLE_ASK.search(clean) and played:
        return _the_scores_line()
    if (LIVE_RESULT_ASK.search(clean)
            or (played and LIVE_HOW_IT_WENT.search(clean))):
        if LIVE_A_BARE_WINNING.search(clean):
            # "whos winning" is the score, not a story to read: a news site is the one place that
            # will not have it (vivid-feather).
            return _the_scores_line()
        if played:
            return _the_scores_line()
        # "did arsenal win" names a team by its own name, and "did labour win" a party: with no
        # word here that says what was played, the news line is the one that covers both.
        if LIVE_BARE_RESULTS.search(clean):
            return LIVE_WHICH_RESULTS
        return LIVE_NEWS_LINES
    if played and LIVE_TABLE_ASK.search(clean):
        return _the_scores_line()
    if LIVE_WORLD_ASK.search(clean) and not _the_scope_of_a_standing_ask(clean):
        return LIVE_NEWS_LINES
    return None

# The limit said plainly, for a line that asks whether the bot can look anything up and names
# nothing to look up. A yes/no about the bot deserves a yes/no, then the offer, then nothing else:
# the alternative was "I'm not sure about that one, sorry" plus a search suggestion, which is the
# bot hedging about itself.
CANNOT_ANYTHING = (
    "No - nothing live from this end: no searching, no pages, no today's figures. What were you "
    "after? I'll tell you what I know, and where to look the rest up.",
    "That's right, I can't look anything up. What I've got is what I know and whatever you tell "
    "me. What did you want checked?",
    "No, sorry - no browsing and nothing live. Say what it is and I'll do what I can with it, and "
    "name the place that has the rest.",
)


# Agreeing that the bot cannot do something. The line is a yes/no about the bot, not news and
# not a fact to file: "so you cant check the weather for me" said straight after the bot had
# said it had nothing live, and "you cant see my calendar can you". The last kind has no verb
# in it at all ("so no live news then"), so a bare "so no ... live/today" counts as well.
BOT_CANNOT = re.compile(
    r"\b(?:you|u|ya)\s*(?:cant|can't|cannot|can not|couldnt|couldn't|dont|don't|doesnt|"
    r"doesn't|wont|won't|arent|aren't|isnt|isn't)\b", re.I)
BOT_CANNOT_DO = re.compile(
    r"\b(?:check|look|see|tell|know|find|search|access|view|pull|get|open|connect|browse|"
    r"read|show|say|able|online)\b", re.I)
# Saying it cannot look something up is a claim about what the bot is for, so a line with nothing
# named in it ("you cant check anything can you") gets the whole limit said plainly.
BOT_CANNOT_LOOK = re.compile(
    r"\b(?:check|look|search|browse|online|internet|connect|open|view|access|find)\b", re.I)
# "you cant check anything can you" asks the whole question; "you cant open a jar with that" has the
# same words and is about a jar. Only a line that names nothing to look up and asks the bot about
# itself gets the plain limit.
CANNOT_ANYTHING_ASK = re.compile(
    r"\b(?:anything|any|whatever|at all|a thing|one thing|nothing)\b|"
    r"\b(?:can|could|do|does|are|will) (?:you|u)\b", re.I)
SO_NOTHING_LIVE = re.compile(
    r"\bso (?:no live (?:anything|news|weather|prices|times|scores)|nothing live|"
    r"no (?:news|weather|prices) (?:then|today|either))\b", re.I)

# The same denial, about one of the person's own records rather than anything live: "you cant see
# my calendar can you", "you cant read my emails either". There is no live pool for a calendar and
# no state word to make it an ask ("what's on my calendar" is a different line), so the answer is
# the limit itself plus the one thing the person can do about it. The record noun has to be there,
# or the arm would take "you cant see me can you", which is a joke with an answer of its own.
CANNOT_READ_YOURS = re.compile(
    r"\b(?:see|read|access|open|view|look (?:at|in)|check)\b[^.?!]{0,14}\b"
    r"(?:my|our|the)\s+(?:calendar|diary|inbox|emails?|mail|files?|folders?|notes?|photos?|"
    r"pictures?|messages?|texts?|documents?|screen|spreadsheets?)\b", re.I)
# A denial about the bot's eyes with nothing named in it: "you cant see anything can you", "you
# cant read anything". The words are the no-eyes reader's own ("see", "read"), so this is the same
# limit it says about a photo or a file, said once with nothing to point at. The line has to end at
# the bare thing or at a small asking tail, or it would take "you cant see anything in this light",
# which is about the light.
CANNOT_SEE_ANYTHING = re.compile(
    r"\b(?:see|read|look at)\b[^.?!]{0,12}\b(?:anything|nothing|a thing|any of it|any of them)\b"
    r"(?:\s+(?:at all|can you|could you|right|then|either|though|really|now))*[.?!]*\s*$", re.I)
CANNOT_SEE_ANYTHING_LINES = (
    "No, nothing on your side is visible to me - no pages, no photos, no files. I only get the "
    "words you type, and that is enough for most things: tell me what is in it.",
    "That's right, I can't see anything of yours. Type out the bit that matters and I'll work "
    "with it from there.",
)
CANNOT_YOUR_OWN = (
    "No, I can't see your diary from here - no calendar, no bookings, nothing of yours. Tell me "
    "what is in it and I'll work with that.",
    "Nothing of yours is in front of me, so no. Read out the lines that matter and I can help with "
    "what they say.",
    "I can't see your calendar or your plans, sorry - I only know what you tell me here. Give me "
    "the part that matters and it is as good as me having it.",
)


def _what_no_eyes_already_says(clean):
    """The line no_eyes already has for a named thing of theirs, or None.

    A screen, a photo, a file and an inbox each have their own honest line in `no_eyes`, and they
    are better than a general one about calendars: "you cant see my screen can you" wants the
    words-are-all-I-get line, not a list of records. Read here so the two cannot drift, the same
    way the body tables are read from this file.
    """
    for family, things in no_eyes.SEEING_FAMILIES.items():
        if re.search(r"\b(?:" + "|".join(re.escape(thing) for thing in things) + r")\b", clean):
            return no_eyes.CANNOT_SEE.get(family)
    return None


def _a_no_from_the_bot(clean):
    """True when the line only asks the bot to confirm it cannot do something."""
    text = clean or ""
    if SO_NOTHING_LIVE.search(text):
        return True
    return bool(BOT_CANNOT.search(text) and BOT_CANNOT_DO.search(text))

# The bare thing named inside a denial is not an ask the live pools recognise on their own:
# "trains" is not "train times", and "the news" on a line with no question in it never got as far
# as the pool. Only a denial takes this reading, so an ordinary chat about trains is untouched.
CANNOT_THINGS = (
    ("travel", ("train", "trains", "bus", "buses", "tube", "tram", "flight", "flights",
                "traffic", "motorway")),
    ("news", ("news", "headline", "headlines", "the score", "scores")),
    ("prices", ("price", "prices", "the cost", "costs", "exchange rate", "the rate")),
)


def _the_live_thing_named(clean):
    """The live pool for the bare thing a denial names, or None."""
    for kind, words in CANNOT_THINGS:
        if _has(clean, words):
            for name, _phrases, options in LIVE_KINDS:
                if name == kind:
                    return options
    return None


def _the_bot_says_it_cannot(clean):
    """True when the line is about what the bot cannot do, with nothing in it to look up."""
    return bool(BOT_CANNOT.search(clean or "") and BOT_CANNOT_LOOK.search(clean or ""))


# The word that makes a question one about a favourite rather than about a choice between two
# things on the table.
FAVOURITE_WORDS = ("favourite", "favorite")


def _taste_lines():
    """The taste lines that may take a favourite question off a card (see `reads_as_a_taste`).

    Only the entries asked for with the word favourite, and the honest "no favourite" pool. The
    choice pools are left out on purpose: "do you like dogs" is answered better by the chat
    module's own line than by the taste shrug ("No strong view on that one, honestly"), and "what
    do you like watching" better by the viewing picks than by the same shrug, so neither is a line
    to claim a turn with.
    """
    lines = set(FAVOURITE_GENERAL)
    for phrases, options in TASTES:
        if any("favourite" in phrase or "favorite" in phrase for phrase in phrases):
            lines.update(options)
    return frozenset(lines)


TASTE_LINES = _taste_lines()


# A line that puts the bot's favourite beside the person's own ("whats your favourite season? i
# cant decide mine") is a two-way question, and the entry that answers both halves is the better
# reply: the taste alone drops the half they brought to it.
BESIDE_THEIR_OWN = re.compile(r"\b(?:mine|can'?t decide|cant choose|not sure which)\b")


def reads_as_a_taste(text, memory=None):
    """True when the line asks what the bot itself likes and the composer answers it as a taste.

    The arbiter reads this so a question about the bot's own taste is not answered by a card about
    the thing it names: "do you have a favourite food" reached the what-to-cook entry and came back
    with a list of dishes, and "whats your favourite show" with tonight's viewing picks. Those are
    good answers to "what should I cook" and "what should I watch"; neither is an answer to a
    question about the bot. Only the lines its own pools answer count, so a taste the composer has
    no line for keeps whatever else matched it.
    """
    clean = _matchable(text)
    if not clean:
        return False
    if not _has(clean, OPINION_ASKS):
        # The same question with its chat-speak put right ("whats ur favourite show"), which is how
        # the reading answers it too: the repair is what makes the line the taste question.
        try:
            clean = _matchable((understand(text, memory if isinstance(memory, dict) else {})
                                or {}).get("plain") or "")
        except Exception:  # noqa: BLE001 - a reading that fails claims nothing
            return False
        if not clean or not _has(clean, OPINION_ASKS):
            return False
    if _is_about_the_persons_own_life(clean):
        return False
    if BESIDE_THEIR_OWN.search(clean):
        return False
    if not _has(clean, FAVOURITE_WORDS):
        # A taste asked without the word favourite is left to the entry that answers it: "what do
        # you think is the best season of the year" has a card that says more than the taste, and
        # the card is the better reply there.
        return False
    try:
        reply = _taste(clean, memory if isinstance(memory, dict) else {}, False, False, "")
    except Exception:  # noqa: BLE001 - a reading that fails claims nothing
        return False
    return bool(reply) and reply in TASTE_LINES
# The words that put a trip on the table: "we are driving down to cornwall", "we're flying to
# portugal in may". A follow-up that refers to "the drive" or "the trip" with no ends of its own
# is about that one.
TRIP_ON_TABLE = re.compile(
    r"\b(?:driving|drive|travelling|traveling|heading|going|off|flying|cycling|walking|"
    r"getting the (?:train|bus|coach|ferry)|trip|journey)\b[^.?!]{0,24}?\b(?:to|in ?to)\b")


def _a_trip_is_on_the_table(memory):
    """True when the ends of the trip are already in the chat.

    "how long would the drive be" names no ends by itself, but after "we are driving down to
    cornwall in august" they are known, so the route line is the one to give rather than the
    short question that asks which two places.
    """
    if not isinstance(memory, dict):
        return False
    for step in (1, 2):
        try:
            said = str(last_user(memory, step) or "").lower()
        except TypeError:
            said = str(last_user(memory) or "").lower() if step == 1 else ""
        if said and TRIP_ON_TABLE.search(said):
            return True
    return False


# A line that is the sky and nothing else is an ask with the words left out: "the weather today",
# "weather tomorrow", "weather outside", "rain this weekend". None of those has a question in it and
# none has a word of LIVE_STRONG, so the asking gate dropped them and the person got the nod ("I'm
# listening - say more if it helps") as though they had told the bot something, which is the worst
# answer to a question. This is a whole-line shape, not a keyword: every word has to be a sky word,
# a piece of time or the frame of a question, so "cold weather running tips" is still a question
# about running, "i like the rain" is still the person's own remark, and "the oven is too hot" is
# still the oven. The nouns carry it, so "weather" alone is an ask and "nice one" is not.
LIVE_SKY_NOUNS = frozenset(
    "weather wether weathr forecast forcast rain raining snowy snow sun sunny shine frosty frost "
    "icy ice foggy fog windy wind sleet hail stormy storm thunder drizzle cloudy overcast "
    "muggy humid misty mist".split())
LIVE_SKY_WORDS = LIVE_SKY_NOUNS | frozenset(
    "a an and the like is it what whats how hows will would be going gonna this next on at in "
    "for today tonight tomorrow morning afternoon evening night weekend weekends week weeks day "
    "days now later outside out there any much could might should please tell me know".split())


# A place is not a keyword to keep out of the shape above: "weather in manchester tomorrow" is the
# same ask as "weather tomorrow" with the place said out loud, and the old test dropped it for the
# one word that was not a sky word or a piece of time. So after a preposition the line may name
# where - one or two words of it - and still be the ask. Two, because "the weather in the peak
# district" is a place and three words in a row is usually a subject.
LIVE_SKY_PLACE = frozenset("in at near around for of".split())


def _the_sky_and_nothing_else(clean):
    """True when every word of the line is the sky, a piece of time, the shape of the ask, or the
    place the person is asking about."""
    words = [word.strip("'") for word in re.findall(r"[a-z']+", clean)]
    if not words or not _has(clean, LIVE_SKY_NOUNS):
        return False
    unknown = 0
    after_place = False
    for word in words:
        if word in LIVE_SKY_PLACE:
            after_place, unknown = True, 0
            continue
        if word in LIVE_SKY_WORDS:
            continue
        # "the weather in the oven" is the oven: an indoor thing after a preposition is the
        # thing, not the place, and the reading above answers the thing.
        if not after_place or word in LIVE_INDOOR:
            return False
        unknown += 1
        if unknown > 2:
            return False
    return True


# The words for traffic on a road, read with a road's name: "any jams on the a1 north" carries no
# ask and none of the strong live words ("any traffic" is one, "any jams" is not), so the asking
# gate dropped it and the person got the nod - "I'm listening - say more if it helps" - to a
# question about their drive this morning.
ROAD_TRAFFIC_WORDS = frozenset("""
    jam jams traffic busy closed closure closures shut roadworks accident accidents
    delay delays delayed diversion diversions queue queues queuing
""".split())


# A line that tells you what already happened on a road is not asking what the roads are doing.
# "i got stuck in a jam on the a1 this morning" is a person's morning, and "the m6 was closed last
# night" is news about their evening: the note about how a jam clears where "Rotten luck" belonged
# reads as a lecture. The same fault as the one above, one tense over, so the reader has to know
# whether the line is an ask at all.
# A report is not one phrase: it is a time already past, or a verdict on a day already had. "the
# m25 was shut last night" carries the time, but "the traffic was awful on the m25" carries only
# the verdict, and "my morning was a nightmare" only the mood - and both of those were still read
# as asks about right now. So the verb's own tense is read too: "was awful", "was a nightmare",
# "took ages" and "sat in traffic" are things that have happened, while "is the m6 shut" and
# "was the m6 shut" keep their ask (the asking gate and LIVE_STRONG hold those), and "was it busy"
# is still a question because the order is inverted.
A_REPORT_OF_WHAT_HAPPENED = re.compile(
    r"\b(?:yesterday|last night|this morning|earlier|we sat|i sat|got stuck|was closed|were bad|"
    r"there were|there was|it took us|took me|sat in|stuck for|queued for|took ages|"
    r"took forever|took hours|missed the (?:train|bus|ferry|flight)|"
    r"(?:was|were) (?:awful|terrible|horrendous|grim|hell|murder|chaos|a mess|a joke|a nightmare|"
    r"bad|shut|rammed|chocka|packed)|(?:awful|terrible|horrendous|grim) (?:this morning|earlier|"
    r"yesterday|last night))\b")


def _a_road_named_with_traffic(clean):
    """True when the line names a road and asks what the traffic on it is doing."""
    if not LIVE_ROAD_NAME.search(clean):
        return False
    if A_REPORT_OF_WHAT_HAPPENED.search(clean):
        return False
    return bool(set(clean.split()) & ROAD_TRAFFIC_WORDS)


THEIR_OWN_COUNT_WORDS = ("traffic", "footfall", "foot traffic", "visitors", "hits",
                         "analytics", "viewers", "stats")

# The ask, when the question mark is missing: "how much web traffic does my site get", "where do i
# see my footfall", "is my shop up or down this month".
A_COUNT_ASKED = re.compile(
    r"\b(?:how\s+(?:many|much|often)|whats?\s+(?:my|the)|what\s+is\s+my|where\s+(?:do|can)\s+i\s+"
    r"(?:see|find|check)|is\s+my\b.*\b(?:up|down)|how\s+is\s+my)\b")

# What happened, rather than what they want to know: "my shop had footfall all day", "my website
# had 200 visitors yesterday", "traffic to my etsy shop is down". A busy day is a thing to say
# something about, and a figure they already have is theirs, so "it lives in your analytics" is
# pointing away with nothing given - the same fault as a report of a road.
THEIR_OWN_COUNT_HAPPENED = re.compile(
    r"\b(?:had|has|got|fell|dropped|went|rose|doubled|halved|visited|bought|sold|shipped)\b")
THEIR_OWN_COUNT_REPORT = re.compile(
    r"\b(?:yesterday|last\s+(?:night|week|month|year)|this\s+(?:morning|week|month)|all\s+day|"
    r"so\s+far|today|down|up)\b")


def _their_own_count(clean):
    """True when the line asks for a number of the person's own with the question left off.

    "how much web traffic does my site get" and "where do i see my footfall" are asks, and the
    asking gate would drop them to the nod because the verb is not in front. The number is in
    their own analytics, so it is read here and answered by the site-stats note rather than by
    the nod.

    A line that says how the day went, or names the figure they already have, is not asking where
    the figure lives: "my shop had footfall all day" wants a word about the day, not a note
    pointing at the analytics page.
    """
    if not _has(clean, LIVE_SITE_THING) or not _has(clean, THEIR_OWN_COUNT_WORDS):
        return False
    if A_COUNT_ASKED.search(clean):
        return True
    return not (THEIR_OWN_COUNT_HAPPENED.search(clean)
                or THEIR_OWN_COUNT_REPORT.search(clean))


# A fall, said rather than asked: "traffic to my etsy shop is down", "visitors dropped last
# month", "sales have gone quiet". It reports their own numbers and asks nothing, so the asking
# gate would turn it into a nod and the site-stats note would send them to a page without saying
# anything first. A fall has ordinary explanations, and those come before the page.
A_COUNT_FELL = re.compile(
    r"\b(?:down|fell|falling|dropped|dropping|slowed|slowing|stalled|quiet|quietened|"
    r"nose\s?dived|collapsed|stopped|lower|fewer|half|dead|gone\s+quiet|went\s+quiet)\b")


def _their_own_thing(clean):
    """True when the number is one of theirs: their site, their shop, their till."""
    return _has(clean, ("my", "our", "mine", "the shop", "the site")) or bool(
        A_COUNT_ASKED.search(clean))


def _their_own_count_fell(clean):
    """True when the line reports a fall in a number of the person's own, and asks nothing."""
    if A_COUNT_ASKED.search(clean):
        return False
    return (_has(clean, LIVE_SITE_THING)
            and _has(clean, THEIR_OWN_COUNT_WORDS + ("sales", "orders"))
            and bool(A_COUNT_FELL.search(clean)))



def _live(clean, asking, memory=None):
    """The pool of honest replies for live information, or None. A line that does not read as a
    question still asks for it when it names the thing ("train times to Bristol tomorrow")."""
    # A fact belonging to one place - a car park, dogs, a takeaway, a pool - is not live
    # information, but it is not in the bot either, and the search hedge is the worst line for
    # it. It has its own reader (`bot/compose/place_facts.py`), checked before all of this.
    from . import place_facts
    place = place_facts.the_line(clean)
    if place:
        return place
    if _has(clean, LIVE_NOT):
        return None
    # A question whose answer does not change with the day is not live information, whatever
    # word in it matched a live kind: "what's the tallest building in the world" and "the biggest
    # city in the world" both reached the news note through "the world", which is a settled
    # question answered as though it were today's news. The reading says which kind it is
    # (`understood["over_time"]`, see bot/understanding/kinds.py), and only a `False` stands this
    # down - `None` keeps every line exactly as it was, and `True` is what the rest of this
    # function is for.
    understood = (memory or {}).get("understood") if isinstance(memory, dict) else None
    if isinstance(understood, dict) and understood.get("over_time") is False:
        return None
    # A fact that belongs to the person's postcode is not live information and does not need a
    # question mark ("my poll card hasnt come"). It has its own narrow reading, so it is checked
    # before the asking gate.
    lookup = a_postcode_lookup(clean)
    if lookup:
        return lookup
    # "the news" on its own is the ask with the words left out, not a report about the day: it was
    # met with the nod ("Thanks for telling me") as though the person had told the bot something.
    if clean.strip(" ?!.") in ("news", "the news", "and the news"):
        return LIVE_NEWS_LINES
    # The same ask with a few more words in it: "anything in the news", "the headlines", "news
    # about the strike". It is the shape of the line that says so, and the asking gate below
    # would drop a line with no question mark in it.
    from . import news_ask
    if news_ask.reads_as_an_ask_for_the_news(clean):
        return LIVE_NEWS_LINES
    if (not asking and not _has(clean, LIVE_STRONG)
            and not LIVE_ANY_ACCIDENT.search(clean)
            and not LIVE_A_BARE_WINNING.search(clean)
            and not _the_sky_and_nothing_else(clean)
            and not _a_road_named_with_traffic(clean)
            and not _their_own_count(clean)
            and not _their_own_count_fell(clean)):
        # "check my gift card balance", "check my order", "confirm my appointment": an ask with
        # the verb in front and no question mark, so the asking gate above would drop it and the
        # person got "Got it. Is there anything you'd like a hand with?" - the placeholder this
        # file exists to keep off their screen. The record pool answers it and nothing else here
        # can, so it is read here rather than left to the nod.
        if RECORD_CHECK.search(clean) and _their_own_phrase(clean, RECORD_THINGS):
            record = _their_own_record(clean, False)
            if record:
                return record
        return None
    # A price for something the person already has is on their own bill, so it is read before the
    # price kind, which otherwise sends them to a seller's site for a thing they have already
    # bought. Their own points balance is the same shape and the same wrong turn.
    mine = _their_own_bill(clean) or _their_own_points(clean)
    if mine:
        return mine
    for kind, phrases, options in LIVE_KINDS:
        if kind in ("site-stats", "site-stats-down"):
            # The counting words are common ones - "traffic", "visitors" - so the kind reads only
            # a line that names a thing of the person's own: their site, their shop, their
            # listing. "is there traffic near the shops" is a road question and keeps the roads
            # pool, and a line about their own numbers never reaches an app that cannot see them.
            if kind == "site-stats-down":
                if _their_own_count_fell(clean) and _their_own_thing(clean):
                    return options
                continue
            if _their_own_count(clean) and _their_own_thing(clean):
                return options
            continue
        if kind == "weather":
            # Something in the house ("the oven", "the room") makes it a setting, not a forecast.
            if _has(clean, LIVE_INDOOR) and not _has(clean, LIVE_WEATHER_WORDS):
                continue
            if (_has(clean, phrases) or LIVE_WEATHER_DAY.search(clean)
                    or (_has(clean, LIVE_SKY) and not _has(clean, LIVE_SKY_OFF)
                        and not LIVE_SKY_WHY.search(clean))
                    or (_has(clean, LIVE_WEAR)
                        and (_a_bare_wear_ask(clean) if _has(clean, LIVE_TAKE_ASK)
                             else _has(clean, LIVE_SOON))
                        and not _has(clean, LIVE_SETTING))):
                return options
            continue
        if kind == "news" and LIVE_A_BARE_WINNING.search(clean):
            continue  # "whos winning" is a score, and the reader at the end of this reads it as one
        if kind == "news" and LIVE_NOT_WORLDS.search(clean):
            continue  # their own news: the record reader answers it, not a news site
        if kind == "roads":
            if _has(clean, LIVE_ROADS_NOT):
                continue  # the road tax, a road trip, directions: not today's traffic
            if _has(clean, phrases) or (LIVE_ROAD_NAME.search(clean)
                                        and not _has(clean, LIVE_PAPER_WORDS)):
                return options
            if _has(clean, LIVE_ROAD_WORDS) and _has(clean, LIVE_DELAY_WORDS):
                return options  # "is the road to leeds closed for roadworks"
        if kind == "journey":
            # A journey line needs two ends. "how far is york from leeds" and "how long is the
            # drive to york" name one, so they get the route planner; "how far is the tennis
            # court" names only the thing, so it is the distance line instead.
            if _has(clean, phrases) and (_has(clean, LIVE_JOURNEY_ENDS)
                                         or _a_trip_is_on_the_table(memory)):
                return options
            continue
        if kind == "travel":
            if _has(clean, LIVE_ROADS_NOT):
                continue  # the road tax, a road trip, directions: not today's traffic
            if _has(clean, phrases) or (_has(clean, LIVE_TRAVEL_WORDS)
                                        and _has(clean, LIVE_DELAY_WORDS)):
                return options
            # "What time does my train leave" is live times about how they are travelling, and
            # its own subject keeps it out of the opening-hours pool above (OWN_TIME_ASK), so
            # the travel line is the one that answers it.
            if _has(clean, LIVE_TRAVEL_WORDS) and (OWN_TIME_ASK.search(clean)
                                                   or MY_TIME_ASK.search(clean)):
                return options
            continue
        if kind == "prices":
            # A rate in the line with a judgement on it ("its 45 a month, is that a lot") is a
            # question about that rate, and which reading answers it depends on one thing the line
            # itself says. A rate whose thing is *in* the line ("my mortgage is 900 a month, is
            # that normal") is judged by comparing that thing with the same thing elsewhere, which
            # is what the two readings below do, so the sum goes under them. A rate with no thing
            # in it names nothing to compare, and the sum it comes to over a year is the only
            # answer about what the person said, so it goes above them.
            rate = quantity.the_rate_they_asked_about(clean, memory)
            if rate and not quantity.the_thing_they_pay_for(clean):
                return (rate,)
            # A sum asked to be judged is not a live price: nothing is being looked up, and today's
            # figure is not what the person asked for ("is that a lot of money" after a quote).
            verdict = _a_price_wants_a_verdict(clean, memory)
            if verdict:
                return verdict
            # The ask in the many shapes people use for it, with the guards that keep it off a
            # dose, a portion, a rate to save at and a recipe (`bot/compose/prices.py`).
            before = str(last_user(memory) or "") if isinstance(memory, dict) else ""
            priced = prices.the_price_reply(clean, phrases, before.lower(), options)
            if priced:
                return priced
            if rate:
                return (rate,)
            continue
        if kind == "hours":
            if _has(clean, LIVE_NOT_HOURS):
                continue  # the sky's own times are the sky's entries' to answer
            # "when does the post office close" is the plainest way to ask this and the phrase
            # lists were written around "what time", so a named place beside open or close is
            # the same ask. It has to name the place: "when does the meeting start" and "when
            # does the flight land" are their own questions.
            if _names_a_venue(clean) and (LIVE_HOURS_ASK.search(clean)
                                           or LIVE_YES_NO_OPEN.search(clean)):
                return options
            if OWN_TIME_ASK.search(clean):
                if not (_has(clean, OWN_PLACE) or OWN_VERB_OPEN.search(clean)) or _has(clean, OWN_PERSON):
                    continue  # their own day, not a venue's hours
            # The bare phrase "what time does" is in the hours table because it is how people
            # open that question, and it took "what time does the match start" with it: a
            # kick-off is a listing, not a shop's hours.
            if _has(clean, LIVE_SPORT) and LIVE_LISTING_ASK.search(clean):
                continue
        if _has(clean, phrases):
            return options
    return _the_days_news(clean, asking) or _their_own_record(clean, asking)


# Word orders that are a question wherever they sit in the line. They are inversions a
# statement rarely uses ("who should i see", "should i go", "any advice"), so they do not
# turn "I saw what he did" into a question.
# A line that asks for words, not facts ("what should i say when i ring the plumber",
# "help me word a text to my landlord") wants a shape to say it in, not a search result.
# Two ways to be sure: it asks for wording outright, or it asks what to say and names who to
# or how you will say it. "What should I say on the first day?" is neither, and neither is
# "What should I ask the seller?" - those are questions about the thing, not the wording.
WORDING_ASKS = re.compile(
    r"\b(help (me )?(to )?(word|phrase|say)|word (a|an|the|this|that)|word it|phrase it|"
    r"how do i (word|phrase|say)|"
    r"put (it|this|that) in(to)? (a|an|words)|what to write)\b")
WORDING_SAYS = re.compile(r"\bwhat (should|do|can) i say\b")
# "what should i ask the plumber" is the same ask, with the expert already in the line.
WORDING_ASKS_WHO = re.compile(r"\bwhat (should|do|can) i (say|ask|tell)\b")
# "how do i tell my mum", "what do i tell my son about his dad", "how do i tell my husband i
# want a divorce": the same ask as "what should i say to my boss", said with tell. The `if` and
# `whether` forms are a different question - "how do i tell if my cat is ill" is asking for a
# sign, not for words - so they are kept out.
# The people a person actually has to break news to are usually named in the plural or as a
# group: the kids, the family, the team, everyone. "how do i tell my kids" was answered with a
# shape to say it in and an offer to draft it, while "how do i tell the kids", "how do i tell the
# children", "how do i tell the family", "how do i tell everyone", "how do i tell the twins" and
# "how do i tell the grandparents" all got the search hedge - the bot telling somebody to look up
# how to talk to their own children. The two groups are the household and the room, and both word
# orders below use them.
A_GROUP_OF_PEOPLE = (
    r"kids|children|child|family|families|team|staff|neighbours?|neighbors?|in[-\s]?laws|"
    r"grandparents|grandchildren|grandkids|twins|siblings|relatives|parents|friends|"
    r"colleagues|boys|girls|lads|folks|guys")
A_WHOLE_ROOM = r"everyone|everybody|anyone|anybody|someone|somebody"
WORDING_TELL = re.compile(
    r"\bhow\s+(?:do|should|can|could|would|might)\s+i\s+tell\s+"
    r"(?!\w*\s+(?:if|whether)\b)"
    r"(?:(?:my|his|her|their|our|your)\b"
    # a bare "the" took any noun: "how do i tell the time on this clock", "how do i tell the
    # twins apart", "how do i tell the sex of my kitten" all became wording asks, and four of
    # them had a better answer before (honey-bat). "The doctor", "the vet", "the landlord" are
    # people you have a conversation with, and they stay.
    r"|the\s+(?:doctor|gp|nurse|vet|police|landlord|boss|manager|bank|school|council|teacher|"
    r"colleague|midwife|consultant|dentist)\b"
    # A group after "the" cannot be the "how do i tell the time on this clock" shape the bare
    # article took, and where the line really is a comparison ("how do i tell the boys from the
    # girls", "how do i tell the twins apart") the "from" and "apart" guards below keep it out.
    r"|the\s+(?:" + A_GROUP_OF_PEOPLE + r")\b(?!\s+from\b)"
    r"|him|her|them|people|" + A_WHOLE_ROOM + r")\b"
    r"|\bwhat\s+(?:do|should|can|could)\s+i\s+tell\s+"
    r"(?:my|his|her|their|our|your|him|her|them|" + A_WHOLE_ROOM + r"|"
    r"the\s+(?:" + A_GROUP_OF_PEOPLE + r"))\b(?!\s+(?:if|whether)\b)")
# "how do i tell the difference between a cold and flu", "how do i tell the twins apart": the
# line is asking for a sign or a comparison, not for words, whatever follows "tell".
# The ask for words is said two ways, and the second one is what people who are stuck actually
# type: "how do i tell my boss" and "idk how to tell my boss". Nobody reports a doubt and then
# writes it out in full - the doubt is the first thing out of them, and every one of those lines
# reached the search hedge while the same ask in the other word order got a shape and an offer.
#
# So the line is read in both orders: "how to X" is read as "how do i X" and "what to X" as
# "what should i X", and the three patterns above answer whichever one the person used. That is
# what brings in the whole family, not just `tell`: "idk how to say it to her", "idk what to say
# to my landlord", "idk how to break it to my parents".
#
# Two guards, both of them measured:
# - The doubt has to be in front. "how to tell my baby is hungry" and "how to tell if my baby is
#   teething" are asking what to look for, not for words. They have no doubt in front of them and
#   keep their own answers.
# - Heavy news stands it down: "my daughter died and i dont know how to tell my son" is grief with
#   a question inside it, and the wording branch returns before the grief pools.
A_DOUBT_IN_FRONT = re.compile(
    r"\b(?:idk|i\s+dont\s+know|i\s+do\s+not\s+know|i\s+dunno|dunno|no\s+idea|"
    r"i\s*ve\s+no\s+idea|i\s+have\s+no\s+idea|not\s+sure|i'?m\s+not\s+sure)\b")
THE_SAME_ASK_AS_A_STATEMENT = ((re.compile(r"\bhow\s+to\b"), "how do i"),
                              (re.compile(r"\bwhat\s+to\b"), "what should i"))
TELL_NOT_WORDS = re.compile(
    r"\b(?:difference|apart|apart\s+from)\b"
    # A command taught to an animal is an instruction, not a message: "how do i tell my dog off"
    # was offered a template for wording something to somebody. Only the command shapes go, so
    # "how do i tell my neighbour their dog barks all night" is still a wording ask.
    r"|\b(?:dog|cat|puppy|kitten|puppies|kittens|horse|rabbit|parrot)s?\s+"
    r"(?:off|to\s+(?:stop|sit|stay|come|leave|drop|wait|heel))\b")
def _the_ask_for_words_behind_a_doubt(clean):
    """True when a doubt about how to say something is really the ask for words.

    "idk how to tell my boss" is not a report that the bot cannot answer: it is the ask, in the
    word order people who are stuck use. The line is read in the other order and the wording
    patterns answer it, with the doubt and heavy news as the two guards above.
    """
    if not A_DOUBT_IN_FRONT.search(clean) or _reads_as_heavy_news(clean):
        return False
    said = clean
    for pattern, instead in THE_SAME_ASK_AS_A_STATEMENT:
        said = pattern.sub(instead, said)
    if said == clean or TELL_NOT_WORDS.search(said):
        return False
    return bool(WORDING_ASKS.search(said) or WORDING_SOMEONE.search(said)
                or WORDING_TELL.search(said)
                # "idk what to say to my landlord": the same shape the branch above reads as a
                # wording ask when the person names who it is for.
                or (WORDING_SAYS.search(said) and WORDING_WHERE.search(said)))


def _asks_for_words(said, words):
    """True when this line is a person asking for the words to say.

    Read off the whole line: the ask can be a question shape, somebody to say it to, or a doubt
    about how to put it. Nothing about the spelling is decided here, so the same test answers for
    the line as typed and for the line as repaired - which is what lets a slip in the key verb
    keep its ask (`bot.compose.fallback_chain` asks it of both).
    """
    return bool(WORDING_ASKS.search(said) or WORDING_SOMEONE.search(said)
                or (WORDING_TELL.search(said) and not TELL_NOT_WORDS.search(said))
                or _the_ask_for_words_behind_a_doubt(said)
                or (WORDING_SAYS.search(said)
                    and (WORDING_WHERE.search(said) or len(words) <= 6)))


# Telling someone something hard wants the same help in a different register: "say what
# happened, what you want and by when" is a note to a landlord, not a divorce. The hard subject
# only chooses the pool; it never decides whether the line is a wording ask.
TELL_HARD = re.compile(
    r"\b(divorce|separat\w*|split up|break(ing)? up|broke up|leav(e|ing) (him|her|them)|"
    r"quit|resign\w*|fired|sacked|redundan\w*|lost (my|his|her|their) job|cancer|dying|died|terminal|miscarr\w*|"
    r"pregnan\w*|affair|cheat\w*|debt\w*|bankrupt\w*|autis\w*|diagnos\w*|addict\w*|"
    # coming out is hard news in the same way: "two or three lines, what happened, what you
    # want and by when" reads like a note to a landlord (honey-bat).
    r"gay|lesbian|trans|transgender|non-?binary|bisexual|coming out|came out)\b")
WORDING_WHERE = re.compile(
    r"\b(to (my|the|him|her|them|his|our|your)|when i (ring|call|phone|text|email|speak|write|ask)|"
    r"text|message|email|letter|card|note)\b")
# "about who should pay", "over what to do": a question word as the object of a preposition is
# an indirect question, part of something being reported rather than asked.
INDIRECT = re.compile(r"\s(?:about|over|of|on|at|to)\s+(?:who|what|where|when|why|how|whether)\s")
ASK_SHAPES = re.compile(
    r"\s(who|what|where|when|why|how|which)\s+(should|do|does|can|could|would|will|might|"
    r"is|are|am)\s"
    r"|\s(should|shall|do|does|can|could|would|will|did)\s+(i|we|you)\s"
    r"|\sany (idea|ideas|advice|tips|suggestions|thoughts)\s"
    r"|\swhat (do|should|can|would) (you|i)\s"
    r"|\sis it worth\s|\sworth (it|doing|paying|getting|fixing|buying)\s")
# A hello that does not open with "hi": "nice to meet you sam", "how are you", "long time no
# see". Left out of the pool below, these lines get a neutral "got it", which drops the hello
# and answers the wrong half of "nice to meet you - i'm thinking about getting a dog".
GREETING_OPEN = re.compile(
    r"^\s*(?:(?:nice|good|great|pleased|lovely|glad|happy|grand)\s+to\s+(?:meet|see|hear\s+from)"
    r"\s+(?:you|u|ya)\b"
    r"|(?:good|great|lovely|nice)\s+to\s+have\s+you\b"
    r"|how\s+(?:are|r)\s+(?:you|u|ya)\b"
    r"|how(?:'s|s|\s+is)\s+(?:it\s+going|things|tricks|you\s+doing|your\s+day)\b"
    r"|how\s+do\s+you\s+do\b"
    r"|long\s+time\s+no\s+see\b)", re.I)


def _reads_as_greeting(words, text=""):
    """True when the line opens with a greeting.

    This is the loose half of the test: it says the line opens with a hello and nothing more,
    so the caller can then ask whether the rest of the line is a hello too
    (understanding.kinds.greeting_only) before it gives the turn to the greeting pool. A
    greeting in front of a question is still the question; the caller checks that with
    _reads_as_question, so "hello! whats the weather like today" goes to the forecast.
    """
    plain = [w.replace("'", "") for w in words]
    if not plain:
        return False
    if plain[0] in GREETING_WORDS:
        return True
    if GREETING_OPEN.match(text or " ".join(plain)):
        # A hello in front of news is still the news: "good to see you, i've got a new job" wants
        # "lovely news - well done", not "hey! what would you like to talk about?".
        return not (reads_as_good_news((text or "").lower()) or reads_as_bad_news((text or "").lower()))
    return " ".join(plain[:2]) in ("good morning", "good afternoon", "good evening", "good day")


def _reads_as_taste(clean, words):
    """'Cats or dogs?' is a choice between two things, not a fact anyone can settle."""
    if " or " not in clean:
        return False
    if len(words) > 6:
        return False
    return not any(word in clean.split() for word in QUESTION_WORDS)


def _blackout_words(clean, words, said):
    """True when the line describes a faint in words other than "blacked out".

    "everything went black and i hit the floor" and "my vision went black for a second" are the
    same thing "i blacked out" says, and they were getting a shrug, or worse, the washing card:
    a colour run reads "everything" and "went" as a load of laundry.
    """
    if _names(words, said, DARK_THING) or BLACKED_OUT_A_THING.search(clean):
        return False
    someone = bool(BLACKOUT_PERSON.search(clean))
    for shape, needs_person in BLACKED_OUT_SIGHT:
        if re.search(shape, clean):
            return someone or not needs_person
    return False


def _action(clean, memory):
    """A line with a right action gets it whatever its grammar: a statement can be an emergency."""
    said = " " + re.sub(r"[^a-z0-9']", " ", clean) + " "
    words = said.replace("'", "").split()
    routine = bool(ROUTINE_WAKE.search(clean))
    # Years ago is the doctor, not the ambulance: "my dad was unconscious for a minute years ago"
    # is a story to tell a GP, and only a line that says it is still going on keeps the call.
    story = reads_as_a_story(clean)
    if CANT_WAKE.search(clean) and not _names(words, said, GADGET_WORDS) and not routine \
            and not story:
        return EMERGENCY_ANSWER
    tail_only = UNRESPONSIVE_TAIL.search(clean) and not FEED_TAIL.search(clean)
    choking_thing = CHOKE_MACHINE.search(clean) and not CHOKE_BODY.search(clean)
    if _names(words, said, EMERGENCY_WORDS) and not _names(words, said, GADGET_WORDS) \
            and not choking_thing and not tail_only and not routine and not story \
            and not (OVERDOSE_FOOD.search(clean) and not OVERDOSE_DRUG.search(clean)) \
            and not CHOKE_ON_A_WORD.search(clean) \
            and not (OVERDOSE_OF_A_TREAT.search(clean) and not OVERDOSE_A_PILL.search(clean)) \
            and not _the_thing_is_choking(clean, words):
        return EMERGENCY_ANSWER
    if _names(words, said, FLOPPY_WAKE) and _names(words, said, TIRED) \
            and not _names(words, said, GADGET_WORDS):
        return EMERGENCY_ANSWER
    if not _names(words, said, LANGUAGE_FLUENCY) and (
            _names(words, said, GAS_WORDS) or (
                _names(words, said, FUME_WORDS) and _names(words, said, FUEL_WORDS))) \
            and not _names(words, said, PETROL_WORDS):
        return GAS_ANSWER
    animal = any(word in ANIMALS or word.rstrip("s") in ANIMALS for word in words)
    # "i blacked out the windows with curtains" is a verb about a window, not a faint.
    went_under = (PASSED_OUT.search(clean) and not BLACKED_OUT_A_THING.search(clean)
                  and not PASSING_OUT_A_THING.search(clean)) \
        or _blackout_words(clean, words, said)
    if went_under and not animal and not _names(words, said, LAUGHING_WORDS):
        if _names(words, said, CHILD_FAINT):
            return _choose([CHILD_FAINT_ANSWER], memory, clean)
        if FAINT_COMING.search(clean):
            # a faint that has not happened yet: sit down first, be seen after
            return _choose([FAINT_COMING_ANSWER + "."], memory, clean)
        return _choose([PASSED_OUT_ANSWER + "."], memory, clean)
    return None


# Something of the person's own, asked for by name: "what's my brother called", "what did i call
# my car", "my landlord's name?". Memory answers these when it holds the name; when it holds
# nothing the search shrug tells them to look their own brother up online, which is a worse reply
# than saying the bot has not got it. The pool says "noted" rather than "you never told me"
# because the person may well have said it and the store may have missed it: it only ever stands
# where nothing already knows.
#
# Only a recall frame counts. "what do you call a baby rabbit" and "what is a female dog called"
# are vocabulary questions with an answer, and "what should i call my band" asks for ideas: both
# keep the pools they had.
#
# The object after the verb has to be the person's own: "what did i call my car", "what did i
# call him", "and what did i call it?". A thing with "the" in front of it is what a person
# *telephones* ("i called the council yesterday" then "what did i call the council"), and the
# Citizens Advice answer for that is better than being asked for a name that never existed. So
# the possessive or pronoun is part of the shape, not the bare verb.
RECALL_NAME = (
    re.compile(r"\bwhat\s+(?:did|do)\s+(?:i|we)\s+(?:call|name)\s+"
               r"(?:my|our|his|her|their|it|them|him|us|this|that)\b"),
    re.compile(r"\bwhat(?:'s| is| was)?\s+(?:my|our)\s+\w+(?:'s)?\s+(?:name|called)\b"),
    re.compile(r"\bwhat(?:'s| is| was)\s+(?:my|our)\s+(?:name|called)\b"),
    re.compile(r"\b(?:remember|recall)\b[^.?!]{0,30}\b(?:name|called|call)\b"),
    re.compile(r"\bwhat\s+(?:did|do)\s+(?:i|we)\s+(?:say|tell(?: you)?)\b[^.?!]{0,30}"
               r"\b(?:name|called|call)\b"),
)
# A name of the person's own offered back as a bare question: "my cat's name?". It has to open
# the line: "what about the water company, my name's not on anything" is a statement about a bill.
RECALL_BARE = re.compile(r"^(?:and |so |but )?(?:my|our)\b[^.?!]{0,24}\bnames?\b")


# The turn where the person gave the name: "i named my car betty", "my car is called betty",
# "my landlord is mr patel". The name comes after the verb and the thing's own noun before it,
# which is what the question has to agree with; "i called the council yesterday" is a phone call,
# not a name, which is why a word that is not a name is turned away below.
GAVE_A_NAME = (
    re.compile(r"\b(?:named|called)\s+(?:my|our|his|her|their|the)\s+(\w+)\s+(.+?)"
               r"\s*[.!]*$", re.I),
    re.compile(r"\b(?:my|our)\s+(\w+)(?:'s)?\s+is\s+((?:mr|mrs|ms|miss|dr)\.?\s+\w+|\w+)"
               r"\s*[.!]*$", re.I),
    # "my brother-in-law is called raj" names him and says who he is in one breath. The person
    # the giving line was about is read too, so a later ask about somebody else ("what is my
    # brother called") is not answered with this name: a brother in law is not the brother.
    re.compile(r"\b(?:my|our)\s+([\w-]+)\s+(?:is|was|are|were)\s+(?:called|named)\s+"
               r"(\w+)\s*[.!]*$", re.I),
    re.compile(r"\b(?:named|called)\s+(\w+)\s*[.!]*$", re.I),
)


def _name_given_before(clean, memory):
    """The name the person gave a turn or two ago for this, as they wrote it, or ""."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-2:]
    if not turns:
        return ""
    asked = {w for w in re.sub(r"[^a-z0-9 ]", " ", str(clean or "").lower()).split()
             if w not in ASK_ONLY}
    for turn in reversed(turns):
        said = str(turn.get("user") or "").strip()
        if not said:
            continue
        name, subject = "", set()
        for rule in GAVE_A_NAME:
            found = rule.search(said)
            if not found:
                continue
            groups = found.groups()
            if len(groups) == 2:
                subject, tail = {groups[0].lower()}, groups[1].strip()
            else:
                tail = groups[0].strip()
            words = [w for w in tail.replace(",", " ").split() if w]
            if not words:
                continue
            # "i named my car betty" leaves "betty", "my landlord is mr patel" leaves "mr patel":
            # the name is the end of it, and anything before it belongs to the subject.
            name = words[-1]
            subject |= {w.lower() for w in words[:-1]}
            if len(words) > 1 and words[0].lower() in ("mr", "mrs", "ms", "miss", "dr"):
                name = " ".join(words[-2:])
            break
        lowered = re.sub(r"[^a-z]", "", name.lower())
        if not name or lowered in NOT_A_NAME or lowered in ASK_ONLY:
            continue
        # A question that names the thing counts when the giving turn named it too; a pronoun
        # question ("and what did i call it?") counts on the turn just before it.
        if not asked or not subject or (asked & subject):
            if name.lower() not in said:
                continue
            bits = [b[:1].upper() + b[1:] for b in name.split()]
            return " ".join(bits)
    return ""


def _asks_a_name_back(clean, words=()):
    """True when the line asks for a name of the person's own that nothing here knows."""
    text = " ".join(str(clean or "").lower().split())
    mine = words or re.sub(r"[^a-z0-9' ]", " ", text).split()
    if not set(mine) & {"i", "we", "my", "our"}:
        return False
    if set(mine) & {"should", "shall", "could"}:
        return False
    if any(phrase in text for phrase in WORD_ANYWHERE):
        # The line asks what a word means: "what's my ... called in french" is a word question.
        return False
    if any(rule.search(text) for rule in RECALL_NAME):
        return True
    return bool(RECALL_BARE.search(text) and "?" in text)


# A line that asks for the move: "what can we do before the first day", "what do i do now",
# "where do we start", "what should we try next". The words are plumbing around one of the shapes
# below, and a line in one of those shapes wants the step of the answer in hand - not a claim that
# the answer above was all of it.
MOVE_ASK = re.compile(
    r"\bwhat\s+(?:else\s+)?(?:can|could|should|shall|do)\s+(?:i|we|you)\s+(?:do|try)\b"
    r"|\bwhat\s+(?:now|next)\b"
    r"|\bwhere\s+(?:do|should|can)\s+(?:i|we)\s+(?:start|begin)\b"
    r"|\bwhats\s+the\s+(?:first|next)\s+(?:thing|step|move)\b"
    r"|\bhow\s+(?:do|can|should)\s+(?:i|we)\s+(?:start|begin|prepare|get\s+going)\b", re.I)


def _asks_for_the_move(line):
    """True when the line asks what to do, rather than what the last answer said."""
    return bool(MOVE_ASK.search(str(line or "")))


def _says_it_already(clean, words, memory):
    """True when this line only asks again what the reply just above it answered.

    A follow-up written in the person's own words ("my phone is full of photos" then "how do i
    free up space") is not a new question, and the knowledge entry reads it as the same one: what
    comes back is the opening sentence of the answer just given, word for word, so the second
    reply adds nothing at all. Plain "that's most of what I know on it - say which part is still
    unclear" is the honest reply to that, and it is the one the bot already has for a bare ask
    after an answer (HELP_ALREADY, below).

    Three things have to hold, and each of them is a way of not taking a turn that has an answer:

    * the turn just before was an answer (`_answered_already`) and not a shrug
      (`_hedged_recently`), so there is something for "it" to refer to;
    * the line is short - it has no subject of its own to ask about;
    * its content words are in that answer already: at least one of them, and half of them or
      more. A follow-up that brings a word the answer never used is a new question and keeps
      its turn.
    """
    if _asks_for_the_move(clean):
        # It asks for the move, not for the answer again, however many of its words the answer
        # above used: "my daughter is nervous about starting secondary school next week" then
        # "what can we do before the first day?" was told "that is everything I have on that one,
        # so I would only repeat myself" - about an answer that opens with what to do and carries
        # a second step after it. The step readers answer a move ask; this guard stands down.
        return False
    if not _answered_already(memory) or _hedged_recently(memory):
        return False
    if not words or len(words) > 10:
        return False
    said = set(word for word in _flat_words(_the_answer_above(memory)) if word not in POINTING)
    if not said:
        return False
    mine = [word for word in words if word not in POINTING and len(word) > 2]
    if not mine:
        return False
    # A word and its plural are the same word here: "a banging noise" and "what is causing the
    # noises" are asking about the same thing.
    missing = [word for word in mine if not (word in said or word.rstrip("s") in said
                                             or word + "s" in said)]
    here = len(mine) - len(missing)
    if not here or here * 2 < len(mine):
        return False
    # A word the answer never used is only a new question when it names a thing: "what was the
    # first thing in the box" brings "box", and "that is all I know on it" answers nothing about
    # a box. "what do i need to buy", "is 20 minutes enough" and "what do i actually say" bring a
    # verb, an adjective and an adverb, and the answer above already covers all three.
    return not any(_names_a_new_thing(word, clean) for word in missing)


def _names_a_new_thing(word, clean):
    """True when the line names `word` as a thing (or a plurality of something) of its own."""
    words = clean.split()
    for i, here in enumerate(words):
        if here != word and here.rstrip("s") != word:
            continue
        before = words[i - 1] if i else ""
        after = words[i + 1] if i + 1 < len(words) else ""
        if before in RULED_OUT_DETERMINER and after not in PARTICLE:
            return True
        # "how long is the flight": a plural is a count of things on its own.
        if here.endswith("s") and len(here) > 3 and here != words[0]:
            return True
    return False


def content_words(text):
    """The words a line actually asks with: no pointing words, nothing of three letters or less."""
    words = _flat_words(text)
    return [word for word in words if word not in POINTING and len(word) > 2]


def _flat_words(text):
    """The words of a reply, lowercased and without punctuation, for comparing two of them."""
    return re.sub(r"[^a-z0-9 ]", " ", str(text or "").lower()).split()


def memory_bot(memory):
    """The reply the bot gave on the turn just before this one."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict) and t.get("bot")]
    return str(turns[-1].get("bot")) if turns else ""


def says_it_already(text, memory):
    """True when the composer's reply to this line is about the repeat, not a stock shrug.

    The arbiter asks this before the never-repeat rule: when every other module's proposal only
    says the last answer again, a line about the repeat is the only new thing on the table, and
    it is a question about the answer rather than a shrug. `is_said_it_already` then tells the
    arbiter which candidate that is, so the pools stay in one place, here.
    """
    understood = memory.get("understood")
    if not isinstance(understood, dict):
        understood = understand(text, memory)
    clean = understood.get("clean") or " ".join(str(text or "").lower().split())
    words = understood.get("words") or clean.split()
    try:
        return _says_it_already(clean, list(words), memory)
    except Exception:  # noqa: BLE001 - a reading that fails just offers no line
        return False


def is_the_answer_shorter(reply, last):
    """True when `reply` is the last answer said shorter by the composer.

    The said-it-already lines above are the composer's own wording for a repeat; a short form of
    the answer is the other thing it writes for one, and the arbiter has to be able to tell the
    two apart from a stock line, because only the second is the answer's own words. The reading is
    the shortening module's (`bot/compose/why.py`, `is_the_answer_shorter`), so nothing here owns
    a second copy of the frame.
    """
    try:
        return why.is_the_answer_shorter(reply, last)
    except Exception:  # noqa: BLE001 - a reading that fails claims nothing
        return False


def is_said_it_already(reply):
    """True when `reply` is one of the said-it-already lines, in any of its wordings."""
    flat = " ".join(_flat_words(reply))
    return any(flat == " ".join(_flat_words(line))
               for line in HELP_ALREADY + SAME_AGAIN)


# A line can be nothing but a finger pointed at something: "what does that mean", "which one",
# "how does that work", "whos that", "how come". Every word in one of these is the pointing;
# none of them is a subject, so a line that is all pointing words names nothing at all. The
# list is of the joints a person uses to point with, not of sentences: a wh-word, the thing
# pointed at (that, this, it, one), and the verb of asking (mean, work, explain, be, do).
POINTING_WORDS = frozenset("""
    what whats how why which who whos whom when whens where wheres
    that this it those these one ones thats
    mean means meant meaning explain work works working come
    do does did is are was were be been am
    you u about by for to of in on at with
    much many long again then please exactly really about
    so ok okay oh ah right well and but
    say tell know
""".split())
# The words that make the line a pointer rather than a question of its own.
POINTERS = frozenset("that this it those these one ones thats".split())
# The words that make the line an ask about the words on the table rather than a question of
# its own: "what do you mean" and "explain that" point at whatever was said, and there is
# nothing they can be asked about until something has been said.
MEAN_WORDS = frozenset("mean means meant meaning explain".split())
POINTING_ASK = frozenset("what whats how why which who whos when whens where wheres".split())
# "how come" and "what for" point with no pointer in them at all.
POINTING_IDIOMS = frozenset(["how come", "how comes", "what for", "how so"])

# Nothing in the chat or on the bot's side can be what the finger is on: the bot cannot see the
# letter, the screen or the doctor's words the person is reading, and it has said nothing they
# could be asking about. So it says that in a few words and asks for the thing itself. Every
# line names the thing pointed at with quotes, so it reads as the pointer being answered and not
# as a shrug at the person.
POINTING_LINES = (
    "I can't see what you're looking at, so 'that' could be anything. Put the thing in a "
    "couple of words and I'll answer it properly.",
    "There's nothing on my side for 'that' to land on - tell me the thing itself and I'll take "
    "it from there.",
    "'That' could be a lot of things and I've none of them in front of me - say the thing "
    "you mean and I'll come at it properly.",
    "'That' has nothing behind it here. What is the thing you're pointing at?",
)


def _points_at_nothing(clean, memory, repaired=""):
    """True when the line is only a pointer and there is nothing in the chat for it to be."""
    for line in (clean, repaired):
        said = re.sub(r"[^a-z0-9' ]", " ", str(line or "").lower())
        words = said.replace("'", "").split()
        if not words or len(words) > 6:
            continue
        if not set(words) <= POINTING_WORDS:
            continue
        points = set(words) & POINTERS
        asks = set(words) & MEAN_WORDS
        if not points and not asks and " ".join(words) not in POINTING_IDIOMS:
            # No finger and no ask about the words: "how are you" is not pointing at anything.
            continue
        if not set(words) & POINTING_ASK and not asks:
            continue
        if ("you" in words or "u" in words) and not asks:
            # "what about you" is the hand-back, and the manners pool has already read it.
            continue
        return _nothing_to_point_at(memory)
    return False


def _nothing_to_point_at(memory):
    """True when the chat has said nothing the pointer could be about.

    An answer above the line gives "that" its subject, and the pools before this one have
    already read it. A question back is the other thing a pointer can be about - "what do you
    mean" after the bot's own question is about the question, and the repeat reader in
    `bot/compose/why.py` is the one that says it again (`said_again`). Neither is this pool's
    turn. A thread about a body or a bereavement keeps its own voice: "whats that" after "my
    chest hurts" is not a person reading a letter.
    """
    if not isinstance(memory, dict) or not memory:
        return True
    if in_a_safety_thread(memory) or _grief_thread(memory) or _thread_is_about_the_body(memory):
        return False
    if _answered_recently(memory):
        return False
    if _a_previous_line_named_something(memory):
        # The chat has a subject of its own ("i watched a film for two hours"), so "how long was
        # it" has something to be: the pools that read the thread keep the turn. The reading of
        # the gist is the memory's own (`bot/memory/topics.py`), not a second word list here.
        return False
    if "?" in (last_bot(memory) or ""):
        return False
    return True


def _a_previous_line_named_something(memory, look_back=3):
    """True when a line the person already said in this chat carried a subject of its own.

    "how long was it" after "i watched a film for two hours" has its referent: the film. Only the
    person's own lines are read - the bot's replies are its offers and questions, and one of them
    always has words in it - and only for a word the memory's topic reading keeps.
    """
    from ..memory.topics import keywords  # noqa: PLC0415 - the chat's own reading of a line

    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-look_back:]
    return any(keywords(str(turn.get("user") or "")) for turn in turns)

# The repair joke about a person: "is it worth fixing myself", "should i just fix me". Only the
# reflexive is read, so a real question about a body ("is it worth getting it looked at") keeps
# the advisor's line.
OFFERS_TO_FIX_THEMSELVES = re.compile(
    r"\b(?:fix(?:ing|ed)?|mend(?:ing|ed)?|patch(?:ing|ed)?|servic(?:e|ing)|replace)"
    r"\s+(?:it\s+)?(?:myself|me|yourself|himself|herself)\b")


def _offers_to_fix_themselves(clean):
    return bool(OFFERS_TO_FIX_THEMSELVES.search(clean or ""))


def is_a_forecast(said):
    """True when a reply is one of the forecast's own lines, which say no one can call it.

    A forecast line is not a receipt of the person's words, but it can look like one: "will that
    get better if i keep at it" after the breathlessness card shares "get", "better" and "keep"
    with the first self line, so the greeting module read the line as an echo and said the card's
    second sentence back - repeating the answer already on the screen. The greeting module asks
    this before it hands a leftover back.
    """
    head = str(said or "").strip()
    if not head:
        return False
    # Up to the first placeholder, since "{who}" in the template is a name in the reply.
    return any(head.startswith(line.split("{")[0]) for pool in FORECAST_POOLS for line in pool)


def _the_forecast_subject(clean, memory):
    """('person'|'self'|'pet', "your dad") for the one a forecast is about, or (None, "").

    Whose body it is decides which building the answer sends them to, so it is read before the
    reply: a pet keeps its own doctor, a person's health is theirs and not the speaker's, and
    only a thread about the speaker's own body takes the GP line. "they" is left out on purpose:
    "will they come back next year" about the slugs is not somebody with a doctor.
    """
    recent = [str(t.get("user") or "").lower()
              for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)][-3:]
    asked_about_self = bool(FORECAST_I_ASK.search(clean or ""))
    for said in [clean] + ([] if asked_about_self else list(reversed(recent))):
        found = FORECAST_RELATION.search(said or "")
        if found:
            relation = found.group(1)
            return ("pet" if relation in ANIMALS else "person"), "your " + relation
    if asked_about_self:
        # "will i be ok" is about the asker even when the thread named somebody else: a car
        # accident is theirs, the coping is the speaker's.
        return "self", "you"
    if _thread_is_about_a_pet(memory):
        return "pet", "them"
    whose = _whose_body(clean, recent)
    if whose == "mine":
        return "self", "you"
    if whose == "theirs":
        return "person", "them"
    if FORECAST_HE_SHE.search(clean or ""):
        return "person", "them"
    if _a_body_in_the_thread(memory):
        # "will it get better" one line after "i cant get up the stairs since my knee op": the
        # thread says whose body it is, and the line itself says nothing at all. Read with the
        # things named after a body taken out, so a garden by the back door is not a spine.
        return "self", "you"
    if _thread_is_about_someone_else(memory) or _thread_is_about_a_person(memory):
        return "person", "them"
    return None, ""


def _without_the_things_named_after_a_body(text):
    """The line with "back door" and "foot of the stairs" taken out before a body is read."""
    return BODY_WORD_FOR_A_THING.sub(" ", str(text or ""))


def _whose_body(clean, recent):
    """'mine', 'theirs' or "" for the body a forecast is about.

    "my shoulder aches when i lift the kids" is the speaker's shoulder, and reading the kids in
    the line as the subject sent the shoulder to somebody else's doctor - "ask them how them is
    doing". The possessor is what decides it: `my` in front of a body word is the speaker's,
    and a body word beside a person is theirs.
    """
    for said in [clean] + list(reversed(recent)):
        tokens = re.findall(r"[a-z']+", _without_the_things_named_after_a_body(
            _without_the_forecast_verb(said or "")))
        for at, token in enumerate(tokens[:-1]):
            if token == "my" and tokens[at + 1] in FORECAST_BODY_WORDS:
                return "mine"
        if set(tokens) & FORECAST_BODY_WORDS and (set(tokens) & _THREAD_PEOPLE
                                                  or FORECAST_HE_SHE.search(said or "")):
            return "theirs"
    return ""


def _without_the_forecast_verb(line):
    """The line with the forecast's own words taken out, so they cannot pass for a subject.

    "will they come back next year" about the slugs is a question about a garden, and "back"
    is a body part: read with the verb in, the line named a spine and sent a gardener to a
    physio. What is left after the verb is the thing the forecast is about.
    """
    found = FORECAST.search(line or "")
    if not found:
        return line or ""
    return (line[:found.start()] + " " + line[found.end():]).strip()


def _thread_said(memory, look_back=4):
    """The last few things the person said, as one line."""
    turns = [t for t in (memory or {}).get("turns") or [] if isinstance(t, dict)][-look_back:]
    return " ".join(str(turn.get("user") or "").lower() for turn in turns)


def _a_body_in_the_thread(memory, look_back=4):
    """True when the last few things said were about a body or a health worry.

    Read here rather than through `_thread_is_about_the_body` because that one also counts the
    health words of a thing ("my sister is really struggling" has none, "my mum had a fall" has
    several), and the two pools answer different questions: one names who is treating somebody,
    the other says what the person asking can do.
    """
    for turn in [t for t in (memory or {}).get("turns") or [] if isinstance(t, dict)][-look_back:]:
        said = str(turn.get("user") or "").lower()
        # A thing named after a body ("the back door") and the forecast's own verb ("will they
        # come back") are not bodies, so both go before the words are read.
        said = _without_the_things_named_after_a_body(_without_the_forecast_verb(said))
        words = _without_the_idioms(said)
        if (words & BODY_PARTS or words & SYMPTOM_WORDS or words & HEALTH_WORDS
                or words & FORECAST_ILL or FORECAST_OFF_THEIR_FOOD.search(said)
                or FORECAST_A_FALL.search(said)):
            return True
    return False


def _a_hard_patch_in_the_thread(clean, memory, look_back=3):
    """True when the thread is somebody having a hard time rather than somebody ill."""
    said = [str(clean or "").lower()]
    said += [str(t.get("user") or "").lower()
             for t in (memory or {}).get("turns") or [] if isinstance(t, dict)][-look_back:]
    return any(FORECAST_STRUGGLE.search(line) for line in said if line)


def _forecast_pool(clean, repaired, memory):
    """The pool for a line asking how something will turn out, or None when it is not one."""
    line = next((said for said in (clean, repaired)
                 if said and FORECAST.search(said)), "")
    if not line or FORECAST_PERMISSION.search(line) or FORECAST_DURATION.search(line):
        return None
    if _in_a_loss_thread(memory) or _grief_thread(memory):
        # "my dad died in march" then "will i be ok": grief is not a body that mends, and the
        # condolence pools keep that thread.
        return None
    kind, who = _the_forecast_subject(line, memory)
    if in_a_safety_thread(memory):
        return [phrase.format(who=who or "you") for phrase in FORECAST_AFTER_SAFETY]
    if kind == "pet":
        if not (_a_body_in_the_thread(memory) or FORECAST_PET_HARM.search(_thread_said(memory))):
            # "my cat keeps scratching the sofa" / "ive tried a spray" / "will it stop" is a
            # habit, not a body, and the vet is not who answers it: only a pet that has eaten
            # something, been hit or gone lame keeps the vet's line.
            return None
        return [phrase.format(who=who) for phrase in FORECAST_PET]
    if kind == "person":
        if an_outcome_asked_about_someone(clean, memory):
            # The composer already reads this one for a person who is ill or in hospital
            # (`OUTCOME_LINES`, kept for the greeting module), and its lines were written for
            # exactly this talk: standing aside leaves them in place rather than swapping one
            # good answer about the ward for another.
            return None
        if _a_body_in_the_thread(memory):
            return [phrase.format(who=who) for phrase in FORECAST_PERSON]
        if _a_hard_patch_in_the_thread(line, memory):
            # "my sister is really struggling" then "will she be ok" is not a question about a
            # body, and "whoever is treating her" is the wrong frame for a hard patch: what can
            # be said is what the person asking can do, and who steps in if it gets darker.
            later = globals().get("_a_hard_time_and_not_a_body")
            if later and later(memory, line):
                # A reader written for exactly this shape landed later (#9034) and keeps the hard
                # patch apart from a patient itself; its lines are in the same voice, so it gets
                # the turn and this stands aside rather than answering the same line twice.
                return None
            return [phrase.format(who=who) for phrase in FORECAST_SOMEONE_STRUGGLING]
        # Anything else about a person is a guess about a life - "will she be ok on her own"
        # about an 84 year old who lives alone - and the store has nothing to say on it.
        return None
    if kind == "self":
        recent = [str(turn.get("user") or "").lower()
                  for turn in ((memory or {}).get("turns") or []) if isinstance(turn, dict)][-3:]
        if _the_threads_who(memory):
            # A thread that already hands the question to somebody of its own - a tooth out, a
            # filling gone, a puppy that will not eat - keeps that hand-off: "a dentist is the
            # one to see" answers "will it heal alright" better than a line about the GP, and it
            # is the answer main already gave.
            return None
        if _whose_body(clean, recent[-1:]) != "mine" and (
                _a_hard_patch_in_the_thread(line, memory) or _thread_is_about_someone_else(memory)):
            # "i lost my job on friday" then "will i be ok", or a father in an accident and
            # "will i be ok": neither is a body of theirs that mends. The answer is about the
            # week the person is in, not about a GP's prognosis.
            return list(FORECAST_SELF_STRUGGLING)
        return list(FORECAST_SELF)
    return None


def _unknown(understood, memory, clean):
    from .fallback_pools import _unknown as _moved
    reply = _moved(understood, memory, clean)
    a_hedge = _is_a_hedge(reply)
    # "how long have we been talking" is the bot's own to answer, and on today's main it is read
    # as a date on a document instead. The bot-about reader waits behind the hedge below, so a
    # card that misreads the line kept its turn: it now runs for a line about this chat itself,
    # whatever the pools made of it, and nothing else is let past that gate.
    if a_hedge or _asks_about_this_chat(clean):
        # The pools have all had the line and what came back was the search hedge. Three things
        # the bot can do better than a hedge, in order, each of them only a hedge replaced.
        about_me = _a_question_about_the_bot(clean, memory)
        if about_me:
            # A hedge is the last thing a person asking the bot about itself should get: it is
            # the one question the bot can answer from where it stands.
            return about_me
        if not a_hedge:
            return reply
        stuck = _what_to_do_about(clean, memory)
        if stuck:
            # "what should i do about the holiday i booked in august" was offered better sources
            # for a holiday nobody else has booked. The question about the thing they named is
            # the floor under the hedge, and only the hedge.
            return stuck
        no_subject = _an_ask_with_no_subject(clean, memory)
        if no_subject:
            # "whats the first step" names nothing of its own: the kind of help it wants can be
            # given anyway, and that is more use than a tip to go and search for the answer.
            return no_subject
        # A reply that already names somebody to ask keeps its turn: the lead may only take the
        # place of a bare search tip, never of a pointer with a name in it.
        lead = (_the_lead_and_the_route(clean, memory)
                if POINTER_HEDGE.search(reply or "")
                and not NAMES_WHERE_TO_ASK.search(reply or "") else "")
        if lead:
            # A search tip on its own hands the whole question back. What can be said without the
            # answer - what settles this kind of question, and what to have in front of you - comes
            # first, and where the rest lives comes after it.
            return lead
    return reply


# A definition wants a definition, not a person to ring: "what does a mortgage broker do" and
# "the difference between a credit card and a debit card" are facts about the world.
TIPS_ASKS = re.compile(r"\b(any|some|got any|need some|need any|want some)\s+(tips|tip|advice|"
                       r"pointers|suggestions|ideas|tricks|trick)\b")
# "Tricks" is the same plea as "tips" ("any tricks", "got any tricks for sleeping", "any tricks for
# the first thirty seconds"), and it was the one word missing from the list, so a person asking for
# tricks got the flat nod. Only the ask frame above counts, so "trick or treat" and "my dog does a
# trick" are untouched; the one shape that carries the frame without asking is named here.
NOT_A_TIPS_ASK = re.compile(r"\btricks?\s+or\s+treat\b")


def _is_a_tips_ask(line):
    """True for a plea for tips in this spelling: the frame, without the phrase that is not one.

    The frame and its guard in one test, so a caller can read the typed line and the repaired
    one through `_reads` without writing the guard twice.
    """
    return bool(TIPS_ASKS.search(line)) and not NOT_A_TIPS_ASK.search(line)
# A plea for tips carries its subject in the line ("any tips for my first half marathon", "i
# need a new bath, any tips"), and the tip depends on where the person is with it. Saying the
# subject back and asking the one thing that decides it beats "tell me what you've got so far",
# which would fit any message at all, and it invents no fact. Two shapes: something coming up
# (timing decides it) and a thing to get or do (what they have decides it).
TIPS_SUBJECT_FOR = re.compile(r"\b(?:tips?|advice|suggestions?|recommendations?|ideas?)\s+"
                              r"(?:for|on|about|with)\s+(?P<subject>.+)$")
TIPS_SUBJECT_TAIL = re.compile(
    r"(?:^|[,.;!?]\s*|\s)(?:any\s+|some\s+|got any\s+)?(?:tips?|advice|suggestions?|"
    r"recommendations?|ideas?)\b.*$")
TIPS_LEAD = re.compile(r"^(?:so|and|but|ok|okay|well|hi|hey|also|then|just)\s+")
# "ok give me a quick dinner idea" asks for a suggestion, not for tips on "give me a quick
# dinner": the request frame is not part of the subject.
TIPS_ANY_IDEA = re.compile(r"\b(?:any|some|got any|need some|need any|want some)\s+ideas?\b")
TIPS_WORD = re.compile(r"\b(?:tips?|advice|suggestions?|recommendations?)\b")
TIPS_REQUEST = re.compile(r"^(?:give|tell|show|send|find|list|suggest|recommend|get)\s+"
                          r"(?:me|us)\s+")
# Something with a date on it: how long there is decides which tips are worth giving.
TIPS_SOON = re.compile(r"\b(?:first|before|wedding|holiday|interview|exam|lesson|marathon|"
                       r"race|move|trip|course|test|appointment|driving\s+lesson|birthday|"
                       r"anniversary|christmas|funeral|hen\s+do|stag\s+do|due\s+date)\b")


def _hedged_recently(memory, look_back=3):
    """True when the bot has said it does not know, on any of the last few turns.

    "what is the planning policy on ferret hutches in bogota" / "anything i can do about it":
    the bot could not answer, so the ask has no answer behind it and the hedge stands - it
    must not become "that's most of what I know on it", which claims knowledge it never had.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-look_back:]
    for turn in turns:
        said = str(turn.get("bot") or "").strip()
        if said and any(said[:40] == line[:40] for line in UNKNOWN):
            return True
        # A punt is a hedge said in other words: "that's beyond what I know well, sorry" does not
        # become "that was the whole of my answer on it" for the question it never answered.
        if said and any(punt in said.lower() for punt in PUNT):
            return True
    return False


# "ok whats your honest view" / "honest view?" / "what would you do": a view is asked for and
# nothing is named. It is not a question about the world - it is the person asking the bot to
# stand behind what it just said, so a search suggestion answers the wrong question. The ask
# itself is a small closed family; the words around it are plumbing ("ok", "so", "honestly"),
# and a line with any word outside that set names its own subject and keeps its own answer
# ("what do you think of my new haircut" is about a haircut, and is not this).
VIEW_ASKS = re.compile(
    r"\b(?:your|ur|yur)\s+(?:(?:honest|own|real|true|personal)\s+)?"
    r"(?:view|opinion|take|thoughts|verdict|read)\b"
    r"|\bwhat(?:'s|s| is)?\s+(?:is\s+|was\s+)?(?:your\s+|the\s+|a\s+)?"
    r"(?:(?:honest|own|real|true|personal)\s+)?(?:view|opinion|take|thoughts|verdict)\b"
    r"|\bwhat\s+(?:do|would|d)\s*(?:you|u|ya)\s+(?:reckon|think|say)\b"
    r"|\b(?:honest|own|real|true)\s+(?:view|opinion|take|thoughts|verdict)\b"
    r"|\b(?:honest|own|real|true)\s+answers?\b"
    r"|\b(?:your|ur|yur)\s+(?:honest|own|real|true|personal)\s+answers?\b"
    r"|\bwhat\s+would\s+(?:you|u)\s+do\b"
    r"|\b(?:view|opinion|take|thoughts|verdict)\s+on\s+(?:it|that|this)\b")


# A reply that mirrored a feeling back is company, not an answer, so there is no view to stand
# behind: "My view has not changed: sorry to hear that" is the bot quoting a kindness as though it
# were a claim (@sure-umbrella's read on #4809). The same goes for the opener that only names how
# the day went. The list is the openers the small-talk and feelings pools use, not a topic list.
VIEW_NOT_AN_ANSWER = re.compile(
    r"^(?:sorry\b|i'm sorry\b|im sorry\b|so sorry\b|that sounds\b|that's rough\b|"
    r"thats rough\b|that's hard\b|thats hard\b|that's a hard one\b|that's a lot\b|"
    r"ugh\b|ouch\b|hope\b|i'm here\b|im here\b|take care\b|nothing has to be decided\b|"
    # A nod is not an answer either. "Thanks for telling me - I'm here if you want to dig into any
    # of that" opens on a thank-you, so the anchored "i'm here" above missed it and a view of it
    # quoted the thank-you back as the bot's opinion. "Got it. Is there anything you'd like a hand
    # with?" and "Noted: ..." are the same: they file what was said and claim nothing.
    r"thanks\b|thank you\b|got it\b|noted\b|i'm listening\b|im listening\b|understood\b)")


def _in_a_pool(text, pools=(NOT_AN_ANSWER,)):
    """True when a reply is one of the pool lines, with or without its question after it.

    "Love that - well done. How are you celebrating?" is the congrats line plus its question, so
    an exact match on the pool never fired and "what do you think" quoted the congratulations as
    the bot's view (@agile-poppy's read on #5606). The first forty characters are what every
    hedge in this file already compares by.
    """
    said = _plain(text)
    return bool(said) and any(_plain(line) and said.startswith(_plain(line))
                              for pool in pools for line in pool)


# The floor: a line that only hands the conversation back to the person. "Go on - I'm listening."
# (chat's "say something" pool), "Ask away, I'll do my best.", "Of course. Take your time." - the
# bot is saying it is ready to hear more, and there is no position in it to stand behind. So a view
# asked on top of one has nothing to give: "what's your take" was answered "Same as I said: go on -
# I'm listening." (@spry-elk's chat, #routing 62120), which tells the person the bot has a view and
# then offers to listen instead of saying it. Only a line made entirely of the floor and its
# courtesies stands down - "Go on, get it checked" still makes a claim.
FLOOR_CLAUSE = re.compile(
    r"^(?:(?:go|carry)\s+on\b|tell\s+me\s+more\b|say\s+more\b|keep\s+going\b|go\s+ahead\b"
    r"|ask\s+away\b|i'?m\s+listening\b|i\s+am\s+listening\b|i'?m\s+here\b"
    r"|take\s+your\s+time\b|over\s+to\s+you\b|what'?s\s+on\s+your\s+mind\b"
    r"|i'?ll\s+do\s+my\s+best\b|spill\s+it\b|i'?m\s+all\s+ears\b)", re.I)
FLOOR_COURTESY = re.compile(
    r"^(?:of\s+course|sure|ok|okay|right|yes|no|well|please|thanks|thank\s+you|"
    r"no\s+need(?:\s+to\s+apologise)?|you'?re\s+not\s+dumping\s+anything\s+on\s+me|"
    r"don'?t\s+apologise(?:\s+for\s+that)?|nothing\s+to\s+be\s+sorry\s+about|"
    r"no\s+problem|you'?re\s+welcome|that'?s\s+what\s+i'?m\s+here\s+for|"
    r"i'?d\s+rather\s+hear\s+it\s+than\s+not)$", re.I)


# "what should i do about the holiday i booked in august" is the same stuck line as "i dont know
# what to do about the holiday": the thing is named, the choice is theirs, and no search settles
# it - yet it got the hedge, which offered to find better sources for a holiday nobody else has
# booked. The pools that answer a decision want a doubt ("im not sure whether to move in with
# her"); this is the same choice asked straight, so it gets the same three questions about the
# part that will not move. Everything that knows the thing keeps its turn: it sits at the floor,
# after the knowledge base, the routes and the store.
# The health words that arrive wearing another ending: "the tiredness", "the anxiety", "the
# sleeplessness". A stem test catches them, and a question about the part that will not move is
# not what a person who cannot sleep needs.
HEALTH_STEMS = ("tire", "exhaust", "sleep", "insomnia", "anxi", "depress", "stress", "panic",
                "symptom", "sick", "unwell", "nause", "dizzi", "swell", "inflam")


WHAT_TO_DO_ABOUT = re.compile(
    r"^\W*(?:(?:and|but|so|oh|ok|okay|well|right|alright|honestly|anyway|also)\W+)*"
    r"what(?:'?s|\s+is)?\s+(?:should|shall|can|could|would|do|did|will|am\s+i)\s+"
    r"(?:i\s+)?(?:do|say|tell)\s+about\s+(?P<thing>[^?.!]+)$", re.I)
# A line that names a body, a blow or a death is somebody else's turn - the safety module and the
# urgent readings answer those, and a question about the part that will not move is not for them.
NOT_WHAT_TO_DO_ABOUT = re.compile(
    r"\b(?:die|died|dying|death|kill\w*|suicid\w*|hurt\w*|harm\w*|abus\w*|hit|hits|hitting|"
    r"beaten|chest|breath\w*|bleed\w*|overdose\w*|emergency|999|111)\b", re.I)


# The thing a stuck line named, with the tail that only says when or which cut away, so the
# question reads "the holiday" and not "your holiday i booked in august".
THING_TAIL = re.compile(
    r"\s+(?:i|i've|ive|im|i'm|we|i\b.*|that|which|who|he|she|they|you|my|me|it)\b.*$", re.I)


def _the_thing_alone(thing):
    """The thing as it can be said back: "the holiday i booked in august" -> "the holiday"."""
    said = _yours(" ".join(str(thing or "").split()).strip(" ,.;:-"))
    cut = THING_TAIL.sub("", said).strip(" ,.;:-")
    return cut or said


# One question about the thing they named, which is what a friend asks. The stock "weigh the
# parts" questions say nothing about the holiday, the deposit or the job; these name it.
WHAT_TO_DO_ABOUT_FRAMES = (
    "{thing} - what's the bit of it you'd want to sort first?",
    "Where would you want to start with {thing}?",
    "{thing} - what's the part that's bothering you most?",
    "{thing} - what would you want to change first?",
)


def _what_to_do_about(clean, memory=None):
    """The questions for a "what should i do about X" line, or ""."""
    line = " ".join(str(clean or "").split())
    found = WHAT_TO_DO_ABOUT.match(line)
    if not found:
        return ""
    thing = found.group("thing").strip(" ,.;:-")
    if not thing or NOT_WHAT_TO_DO_ABOUT.search(line):
        return ""
    words = set(re.findall(r"[a-z']+", line.lower()))
    if (words & SYMPTOM_WORDS or words & BODY_PARTS or words & HEALTH_WORDS
            or any(w.startswith(HEALTH_STEMS) for w in words)):
        # A body, a symptom or a doctor is the health readings' turn: they say who can look, and
        # a "where would you want to start with the pain" would talk over them.
        return ""
    if thing.lower().split()[0] in NOT_A_THING_ASKED:
        # "what should i do about it myself" is still a pronoun, however it is dressed.
        # "what should i do about it" points at what was just said, and the thread answers that
        # better than any stock question: a sore knee then "what should i do about it" is the
        # health reading, not a weighing. Only a thing named in the line is asked about here.
        return ""
    if len(thing.split()) > DISLIKE_TOO_LONG:
        return ""
    named = _capital(_the_thing_alone(thing))
    if not named or named.lower().split()[0] in NOT_A_THING_ASKED:
        return _choose(DITHER_OPEN_LINES, memory, clean)
    lines = tuple(frame.format(thing=named if frame.startswith("{thing}") else named.lower())
                  for frame in WHAT_TO_DO_ABOUT_FRAMES)
    return _choose(lines, memory, clean)


# "how are you feeling about the move" asks the bot about itself and then names something of
# theirs, and the two halves together left every reader standing: main offered to search the web
# for a better source on a move the bot is not making. A question put to the bot about the bot is
# answered by saying what the bot actually is, and then turning to the thing they named, because
# that is the part worth talking about. Only a hedge is replaced here - the module that answers a
# bot-about line already has its turn, and a line it answers never reaches this.
ABOUT_THE_BOT_NAMED = re.compile(
    r"^\W*(?:(?:and|but|so|oh|ok|okay|well|right|alright|honestly|anyway|also)\W+)*"
    r"(?:how\s+(?:are|do)\s+(?:you|u|ya)\s+feel(?:ing)?"
    r"|what\s+do\s+(?:you|u|ya)\s+(?:make|think)\s+of)"
    r"\s+(?:about|of|with|on)\s+(?P<thing>[^?.!]+)$"
    r"|^\W*(?:(?:and|but|so|oh|ok|okay|well|right|alright|honestly|anyway|also)\W+)*"
    r"how\s+do\s+(?:you|u|ya)\s+find\s+(?P<thing2>[^?.!]+)$", re.I)
# The same ask with nothing named - "how are you feeling about it", "how do you feel about all
# this" - is answered by the bot-about reader and never gets here, so a pronoun arriving here has
# no thing to be said back and the line keeps whatever reply it had.
ABOUT_THE_BOT_BORN = re.compile(
    r"^\W*(?:(?:and|but|so|oh|ok|okay|well|right)\W+)*"
    r"(?:where\s+(?:were|are)\s+(?:you|u|ya)\s+(?:from|born)"
    r"|(?:were|are)\s+(?:you|u|ya)\s+(?:born|raised|brought\s+up)"
    r"(?:\s+(?:here|there|locally|in\s+this\s+country))?)"
    r"(?:\s+originally)?[ ?!.,;]*$", re.I)
# What the bot can honestly say about a feeling it does not have, and the door back to the person.
BOT_FEELING_NAMED_LINES = (
    "No feelings on my side at all, and no view on {thing} worth having - I am a program. How are "
    "you finding it?",
    "I have no feelings about it - I am a program, so there is nothing in me for {thing} to land "
    "on. What do you make of it?",
    "No view worth having, and no moods to have one with. You are the one living with {thing} - "
    "how is it going?",
)
BOT_BORN_LINES = (
    "There is no born for me - I am a program, so no hometown and no childhood. Where are you "
    "from, if you do not mind me asking?",
    "Not born, and not from anywhere: I started as a program and stayed one. Are you far from "
    "where you grew up?",
)
# "is there a limit to how long we can talk" is a question about this conversation, and the one
# thing the bot can answer from where it stands - there is no clock on it. It was sent to a search
# engine instead, which is the one place that answer is not. Both ends are anchored and the talk
# itself has to be named, so "how long can i keep the leftovers" and "how long should i boil an
# egg" keep the answers they have.
_THE_TALK_ITSELF = r"(?:talk|chat|talking|chatting|keep\s+going|keep\s+you\s+here)"
ABOUT_THE_BOT_TALK = re.compile(
    r"^\W*(?:(?:and|but|so|oh|ok|okay|well|right|sorry|quick|just|question|one\s+question|quick\s+question|first\s+question|random\s+question)\W+)*"
    r"(?:"
    r"(?:is|are)\s+there\s+(?:a|any)\s+(?:time\s+)?limit(?:\s+(?:to|on)\s+"
    r"(?:(?:how\s+long|the\s+time)\s+)?(?:(?:we|i)\s+can\s+)?(?:"
    + _THE_TALK_ITSELF + r"|this|it|the\s+chat|our\s+chat))?"
    r"|(?:how\s+much\s+time\s+(?:do|have|did)\s+(?:we|i)\s+(?:have|got)\s+left)"
    r"|(?:do|have)\s+(?:we|you|i)\s+(?:have|got)\s+(?:a\s+|any\s+)?(?:time\s+)?limit"
    r"|(?:how\s+long|how\s+much\s+time)\s+(?:(?:can|could)\s+(?:we|i)\s+)?"
    r"(?:(?:have|has)\s+(?:we|you\s+and\s+i)\s+been\s+)?(?:" + _THE_TALK_ITSELF + r")"
    r"|(?:are|do)\s+(?:we|i)\s+(?:out\s+of|running\s+out\s+of|short\s+of)\s+time"
    r"|(?:do|should)\s+i\s+(?:need\s+to\s+)?hurry(?:\s+up)?"
    r"|(?:can|could|will)\s+(?:we|i|you\s+and\s+i)\s+(?:talk|chat|keep\s+going)\s+for\s+long"
    r"|have\s+(?:we|i|you\s+and\s+i)\s+got\s+long"
    r")(?:\s+(?:with|for)\s+(?:you|this|me|now)|\s+for|\s+much)?[ ?!.,;]*$", re.I)
# The same ask with a tally in it: "how long have we been talking" wants a number, and the honest
# answer is that the bot does not keep one.
ABOUT_THE_BOT_CLOCK = re.compile(
    r"^\W*(?:(?:and|but|so|oh|ok|okay|well|right|sorry|quick|just|question|one\s+question|quick\s+question|first\s+question|random\s+question)\W+)*"
    r"(?:how\s+(?:long|much\s+time)\s+(?:have|has|did)\s+(?:we|i|you|you\s+and\s+i)\s+been\s+"
    r"(?:" + _THE_TALK_ITSELF + r")"
    r"|how\s+long\s+has\s+this\s+been\s+going\s+on)"
    r"(?:\s+(?:to|with)\s+(?:you|me))?[ ?!.,;]*$", re.I)
BOT_TALK_LIMIT_LINES = (
    "No limit I know of on my side - I stay as long as you keep going, and nothing runs out. "
    "What do you want to get to?",
    "Nothing cuts this short at a set time as far as I know: the chat lasts while you are in it. "
    "Where would you like to take it?",
)
BOT_TALK_CLOCK_LINES = (
    "I don't keep a clock, so I can't put a number on it - but we have been going a while, and I "
    "am in no hurry.",
    "No clock on my side, sorry: I hold the words, not the minutes. There is plenty of time as "
    "far as I am concerned.",
)


def _a_question_about_the_bot(clean, memory=None):
    """What the bot can say when the line puts a feeling or a start to the bot itself, or ""."""
    line = " ".join(str(clean or "").split())
    if not line:
        return ""
    if ABOUT_THE_BOT_CLOCK.match(line):
        return _choose(BOT_TALK_CLOCK_LINES, memory, clean)
    if ABOUT_THE_BOT_TALK.match(line):
        return _choose(BOT_TALK_LIMIT_LINES, memory, clean)
    if ABOUT_THE_BOT_BORN.match(line):
        return _choose(BOT_BORN_LINES, memory, clean)
    found = ABOUT_THE_BOT_NAMED.match(line)
    if not found:
        return ""
    raw = (found.group("thing") or found.group("thing2") or "").strip(" ,.;:-")
    if raw.lower().split()[:1] and raw.lower().split()[0] in ("your", "ur", "you", "yourself"):
        # "how do you feel about your job" is the bot's own job, and the bot has none: the
        # bot-about reader above answers it, and a frame about the person's thing would be about
        # somebody else's job.
        return ""
    thing = _the_thing_alone(raw)
    if not thing or thing.lower().split()[0] in NOT_A_THING_ASKED:
        # "how are you feeling about it" points at something of theirs the bot cannot see, and
        # naming nothing back is better than a sentence about an unnamed thing.
        return ""
    if len(thing.split()) > DISLIKE_TOO_LONG:
        return ""
    said = thing.lower()
    lines = tuple(frame.format(thing=said) for frame in BOT_FEELING_NAMED_LINES)
    return _choose(lines, memory, clean)

def _only_the_floor(said):
    """True when every part of the line is the floor or a courtesy on its way to it."""
    said = _plain(said)
    if not said:
        return False
    parts = [p.strip(" ,.;:!?\u2014\u2013-\t") for p in
             re.split(r"[.!?;,\u2014\u2013]|\s-\s", said)]
    parts = [p for p in parts if p]
    if not parts or len(parts) > 4:
        return False
    for part in parts:
        if FLOOR_COURTESY.match(part):
            continue
        if not FLOOR_CLAUSE.match(part):
            return False
        # A floor phrase opens a long line as easily as a short one, so the part has to stop soon
        # after it - unless it goes on to say it will wait, which is still the floor.
        words = len(part.split())
        if words > 8 and not FLOOR_WAITING.search(part):
            return False
    return True


# The half of a floor line that says it will still be there ("I'm here if you want to come back to
# it"), so a longer line that opens with a floor phrase still counts as the floor.
FLOOR_WAITING = re.compile(
    r"\b(?:if|when)\s+you(?:'re|\s+are)?\s+(?:want|need|ready|like)|for\s+as\s+long\s+as"
    r"|\bwhenever\b|\bany\s+time\b", re.I)


def _plain(text):
    """The line in one case, with the dashes people type made the same.

    A phone writes an em dash and a keyboard writes a hyphen, so "I'm listening - say more if it
    helps" has to read as the pool's own "I'm listening — say more if it helps."
    """
    lowered = str(text or "").lower().replace("\u2014", "-").replace("\u2013", "-")
    return " ".join(lowered.split())


def _the_words(text):
    """The words of a line that say something about its subject."""
    return {word for word in re.findall(r"[a-z']+", str(text or "").lower())
            if word not in _ECHO_FILLER and len(word) > 2}


def _an_echo_of(question, sentence):
    """True when a sentence is only the person's own line said back, not a claim.

    "Right, so a different cable is done. Clean the charging port out..." opens with a receipt
    built by another module (`bot/memory/tried.py`), and a helper that copied one module's frame
    list would keep missing the next one (@agile-poppy's read on #5606). So the test is the
    words: a sentence whose subject words are nearly all the person's own says nothing new,
    whatever wording the receipt was built from.
    """
    mine = _the_words(question)
    theirs = _the_words(sentence)
    if len(theirs) < 2 or not mine:
        return False
    return len(theirs & mine) / len(theirs) >= 0.75


# A reply from the small-talk module that only reacts and hands the conversation back is not a
# claim: "i got the job" was met with "Love that - well done. How are you celebrating?", and
# "what do you think" quoted the congratulations as the bot's view (@agile-poppy's read on
# #5606). The chat module's pools are its own tables, which this file cannot read without
# importing a module, so the test is the shape: a short reply that ends in a question is the
# bot asking, not the bot claiming.
def _only_a_reaction(module, said):
    if str(module or "") != "chat":
        return False
    said = str(said or "").strip()
    if not said.endswith("?") or len(said.split()) > 14:
        return False
    return any(phrase in said.lower() for phrase in PRAISE)


def _the_answer_in_reply(question, said):
    """The reply without the receipt or reaction sentences in front of it, or "".

    A receipt sometimes opens a reply that goes on to answer ("Right, so a different cable is
    done. Clean the charging port out..."), and the answer is the part after it. Only the
    opening is stripped: later sentences are the answer qualifying itself.
    """
    said = str(said or "").strip()
    for _ in range(3):
        sentences = re.split(r"(?<=[.!?])\s+", said)
        first = sentences[0].strip() if sentences else ""
        rest = " ".join(sentences[1:]).strip()
        if not rest:
            return said
        # A sympathy opener is deliberately not stripped: "Sorry to hear that. A walk and
        # someone to talk to usually help" is company with a suggestion attached, and standing
        # behind the suggestion alone would undo the call on #4809. A receipt is different - the
        # answer after it is the answer the bot gave.
        if not (ack.reads_as_a_receipt(first) or _in_a_pool(first)
                or _an_echo_of(question, first)):
            return said
        said = rest
    return said


def _reads_as_a_claim(said):
    """True when the reply made a claim, so a view of it is the bot's own view.

    A line that mirrors a feeling back, or that puts its question where the answer should be, has
    nothing in it to stand behind. "Sorry to hear that. A walk and someone to talk to usually
    help" is sympathy with a suggestion attached, and "Worth planning rather than rushing into:
    what would have to go right for you?" is a question asked back - quoting the front of either
    gives the person a view the bot never had.
    """
    said = str(said or "").strip()
    if not said or VIEW_NOT_AN_ANSWER.match(said.lower()):
        return False
    if ack.reads_as_a_receipt(said):
        # A receipt is the person's own line said back ("Got it - but your mum says it's too
        # soon"), so quoting it as a view stands behind nothing: "what would you do" after a
        # detail turn answered "My view has not changed: Got it - but your mum says it's too
        # soon".
        return False
    if _in_a_pool(said):
        # The reaction pools are the same shape of nothing: "I'm listening - say more if it
        # helps" is an offer to hear more, and "Good for you. Is there much to sort out before
        # it?" is a congratulations, so "what do you think" on top of either would stand behind
        # a line the bot only said to be polite.
        return False
    if _only_the_floor(said):
        # An offer to listen is not a position: "what's your take" on the back of "Go on - I'm
        # listening" was answered "Same as I said: go on - I'm listening".
        return False
    first = re.split(r"(?<=[.!?])\s+", said)[0].strip()
    if first.endswith("?") and ":" in first:
        # A claim that led into its own question: the part before the colon is a lead-in, not a
        # view, and the part after it is the question the person is being asked.
        return False
    return True


def _nothing_to_stand_behind(said):
    """True when the bot's line left the answer where it was, so the view is the one behind it.

    A receipt ("Got it - but your mum says it's too soon") and a neutral line both put nothing on
    the table, and neither does the floor: "Go on - I'm listening." is the bot saying it is ready
    to hear more. Walking past them is what keeps "what's your take" on the answer the bot
    actually gave instead of quoting the offer to listen back at the person.
    """
    said = str(said or "").strip()
    return bool(said) and (ack.reads_as_a_receipt(said) or _in_a_pool(said, (NEUTRAL,))
                           or _only_the_floor(said))


# An ask for the bot's own view on the first turn is a bare ask - the person has the subject in
# their head and has not said it - except when the line names somebody ("what do you think of me",
# "what do you reckon about us"), where the subject did come with the line.
VIEW_NAMES_SOMEBODY = re.compile(r"\b(?:me|my|mine|myself|us|our|ours|i|im|i'm)\b")


def _is_a_view_ask(clean):
    """True when the line asks for a view and names nothing of its own.

    "your take", "honest view?", "honest answer" - every word is plumbing, so the only thing the
    person can be asking about is the answer just given. A word outside the set names a subject
    ("what do you think of my new haircut") and that line has its own answer to look up.
    """
    if not VIEW_ASKS.search(clean):
        return False
    words = re.findall(r"[a-z']+", clean)
    return bool(words) and not any(
        word.strip("'") not in VIEW_ONLY_WORDS for word in words)


def _the_view_asked_for(clean, memory):
    from .fallback_pools import _the_view_asked_for as _moved
    return _moved(clean, memory)


def _after_a_colon(said):
    """The answer's first word, after a colon: "My view: find the water..." reads as one line."""
    if len(said) > 1 and said[0].isupper() and not said.startswith("I ") and not said.startswith("I'"):
        return said[0].lower() + said[1:]
    return said


# A hedge that names the thing it could not answer is formatted before it is said ("... a map
# app search for plumber near you ..."), so its head is only the part before the first
# placeholder. Comparing that much is enough to recognise the reply as a hedge, which is all the
# arbiter and the greeting module ask of this.
HEDGE_HEADS = tuple(line[:40] for pool in HEDGE_POOL for line in pool)
HEDGE_PREFIXES = tuple(line.split("{")[0] for pool in HEDGE_POOL for line in pool
                       if "{" in line)
# What settles a kind of ask (bot/compose/the_rule_for_it.py) stands exactly where these shrugs
# stand: it is said when nothing else knows the line, so anything that does know it has to win
# the turn over it, the same as it wins over a hedge. "How long do i cook them", a turn after
# "200g of plain flour for four people", was given the time rule instead of the minute a side
# that answer already held - the arbiter passes a hedge over for a real answer, and a rule it
# could not recognise cost the person the better reply.
from .the_rule_for_it import RULE_HEADS as _RULE_HEADS  # noqa: E402 - after the pools

HEDGE_HEADS = HEDGE_HEADS + _RULE_HEADS


# The reply that asks a person to say which bit they mean. It is not a hedge: it says the bot did
# not follow the line rather than that nobody has written the answer down. A chat that is already on
# a card can answer the follow-up instead of asking the question back.
def _is_an_ask_which_bit(said):
    """True when a reply is the "tell me which bit" line rather than an answer or a hedge."""
    head = (said or "").strip()
    return bool(head) and head in BARE_FOLLOW_UP_REPLIES


is_an_ask_which_bit = _is_an_ask_which_bit


def _is_a_hedge(said):
    """True when a reply is one of the pools that mean the bot cannot answer."""
    head = said[:40]
    return (any(head == line for line in HEDGE_HEADS)
            or any(said.startswith(prefix) for prefix in HEDGE_PREFIXES))


# The same test under a name another package can call: `bot/memory/carry.py` has to tell a real
# answer from a hedge before it puts one on the screen in place of the last one, and reaching for a
# private name across packages is the kind of thing that breaks when this file changes.
is_a_hedge = _is_a_hedge


# "is she going to be ok" is a worry about somebody else's outcome, and no card in the knowledge
# base can answer it: nobody can say from here whether a person will recover. Main answered it
# with the search hedge - "I don't know enough to answer that honestly. A search should sort you
# out quickly" - four chats in a row ("my mum is in hospital", "my dad had a stroke", "my friend
# is having an operation tomorrow", "my wife is in hospital with pneumonia"), and a search cannot
# tell anybody whether their mother will be all right. The honest half is that no one can promise
# it, and the useful half is who does know: the staff looking after them, and what to ask while
# they are there.
#
# The line has to be the bare worry and nothing else, and about somebody other than the speaker -
# "am i going to be ok" is somebody's own fear and is left to the modules that answer for a person
# in trouble.
THE_OUTCOME_ASK = re.compile(
    r"^(?:so |and |but |ok |okay )?(?:is|are|will|do you think|does the doctor think)\b"
    r"(?=[^?]{0,44}?(?:\b(?:going to be|be) (?:ok|okay|alright|all right|fine)\b"
    r"|\b(?:make it|pull through|come through|survive|recover)\b))", re.I)
# The worry is answered about somebody the talk has already said is ill or in hospital: a card
# about a sick relative, a stay, an operation, a stroke, the ward. Without one of these the line
# is a guess about something else ("will my car be ok") and another module's answer stands.
WHO_IS_ILL = re.compile(
    r"\b(?:in hospital|in the hospital|on the ward|got admitted|been admitted|is admitted|"
    r"in icu|intensive care|stroke unit|a&e|having an operation|having surgery|"
    r"in for an operation|waiting for a bed|coming out of hospital|coming home from hospital|"
    r"had a stroke|chemo|chemotherapy|on a ventilator|in a coma|diagnosed with|"
    r"the operation|the surgery|under the knife|their scan|the scan|"
    r"pneumonia|sepsis|heart attack|collapsed)\b", re.I)


def an_outcome_asked_about_someone(text, memory):
    """The line behind "is she going to be ok", answered honestly instead of hedged.

    Only when the bare worry is the whole line and the talk has already said somebody is ill or
    in hospital, and never inside a crisis or an emergency the bot has just answered: there the
    person needs the reply they were given, not a paragraph about the ward.
    """
    if not isinstance(memory, dict):
        return None
    clean = " ".join(str(text or "").lower().split())
    if not clean or len(re.findall(r"[a-z']+", clean)) > 9:
        return None
    if not THE_OUTCOME_ASK.match(clean):
        return None
    if re.search(r"\b(?:i|me|my|we|us|our)\b", clean):
        return None      # somebody's own prognosis is not this reading's line
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)][-3:]
    if not turns:
        return None
    last = str(turns[-1].get("bot") or "")
    if last and (any(word in last.lower() for word in CRISIS_WORDS)
                 or any(word in last.lower() for word in SAFETY_WORDS)):
        return None      # an answer that named 999 or a crisis line stands
    said = " ".join([str(turn.get("user") or "") for turn in turns] + [last])
    if not WHO_IS_ILL.search(said):
        return None
    return pick(OUTCOME_LINES, memory, clean)


def is_a_hedge(said):
    """The public name for the test above, for the arbiter.

    A reply that says the bot cannot answer is never an improvement on a card that can, so the
    arbiter asks this before it moves the front card aside for a reply about somebody else. The
    reply it holds has been reduced to its words and so has no capital letters, which is why this
    compares without them.
    """
    head = str(said or "")[:40].lower()
    return (any(head == line.lower() for line in HEDGE_HEADS)
            or any(str(said or "").lower().startswith(prefix.lower())
                   for prefix in HEDGE_PREFIXES))


# The front of an answer is not always the view. A reply that opens by naming the feeling back
# ("I'm so sorry.", "Loneliness is rough.") is company, and a reply that opens with a lead-in
# ("The things that work: ...") names what follows rather than the thing itself. Both were quoted
# as the bot's own position once the view reader landed: "i had a miscarriage" / "honest view?"
# got "My view has not changed: I'm so sorry.", "im so lonely" / "honest view?" got "...:
# loneliness is rough.", and "i cant sleep" / "honest view?" got "...: the things that work."
VIEW_MIRROR = re.compile(
    r"^(?:i(?:'m| am) (?:so |really |very |truly )?sorry\b|so sorry\b|sorry\b|that sounds\b"
    r"|that(?:'s| is) (?:rough|hard|tough|awful|a hard one|a lot|a real loss|a loss)\b"
    r"|ouch\b|ugh\b|hope\b|[a-z]{3,20}(?: [a-z]{2,20}){0,3} is (?:rough|hard|tough|awful)\b)")
# The front of an answer can also be the case it is for rather than the claim itself: "If you want
# something easy and good tonight: Groundhog Day for comedy, Knives Out for a whodunnit" is a
# recommendation to two people, not a remark about wanting something easy. Quoted as the view it
# left the promise hanging in mid-air - "My view has not changed: if you want something easy and
# good tonight." - which is the half of the sentence the person did not ask about, and says
# nothing (answers' watch, budget and weather cards all open this way). A condition that opens the
# line scopes what follows, so the claim is what follows. Only the openers that cannot start a
# claim are here: "For most people the fix is the same" is a claim about most people.
VIEW_A_CASE = re.compile(
    r"^(?:if |unless |depending on|when you|when it|once you|for £|for under |for about "
    r"|for around |for between |for a budget|for \d)")

def _the_view_of(said):
    """The first part of the answer that says something, cut at a colon, or None.

    The front of an answer can be company rather than a claim (see `VIEW_MIRROR`), and it can be
    a lead-in that names what follows: "The things that work: same wake-up time every day" is
    about the wake-up time, not about the things that work. Returns the claim and whether an
    opener was skipped, because the line built from it opens differently in that case.
    """
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", said.strip()) if part.strip()]
    mirrored = False
    for part in parts:
        head, colon, tail = part.partition(":")
        if colon and tail.strip():
            # The claim is the part before the colon, and the lead-in rule swaps them round when
            # the front only names what follows ("The things that work: same wake-up time").
            words = [w.strip(",.").lower() for w in head.split()]
            # A short head names the form of what follows rather than the thing itself: "Quick:
            # tuna pasta in 15, a frittata in 20" is about the pasta and the frittata, and the
            # head alone ("Quick") is not a claim at all. Read as the head it fell through to the
            # next sentence and quoted the bot's own request back ("Same as I said: tell me what
            # is in the fridge and I will pick properly"), which answers nothing.
            if (len(words) < 7 and any(word in VIEW_LEAD_IN for word in words)) \
                    or len(words) <= 3 or VIEW_A_CASE.match(head.strip().lower()):
                head, tail = tail, head
            part = head
        part = part.strip()
        if VIEW_MIRROR.match(part.lower()):
            mirrored = True
            continue
        claim = _a_said_claim(part)
        if claim:
            return claim, mirrored
        mirrored = True
    return None, mirrored


# A sentence that asks the person for something rather than saying anything: "Tell me what is in
# the fridge", "Let me know how it goes", "Any chance you could send a photo". A question in the
# answer can be the view ("What would have to be true for the answer to be yes?"), so this is
# tested only on a sentence that is not already read as a question.
ASKS_BACK = re.compile(
    r"^(?:tell me|let me know|send me|show me|give me|any chance|could you|can you|would you|"
    r"have you got|do you have|what have you|what about you)\b")


def _a_said_claim(first):
    """One sentence read as a claim to stand behind, or None when it says nothing."""
    if not first or first.endswith(":"):
        return None
    if first.endswith("?"):
        # The bot's own question, put again: "What would have to be true for the answer to be
        # yes?" is the view when that question was the answer, and it is still the right one.
        return first if len(first.split()) >= 4 else None
    if ASKS_BACK.match(first.lower()):
        # The bot asking the person for something is not a claim to stand behind: "Tell me what is
        # in the fridge and I will pick properly" is a request, and quoting it as the view
        # ("Same as I said: tell me what is in the fridge") leaves the turn where it started.
        return None
    words = first.split()
    if len(words) > 30:
        # Long answers open with a sentence and then qualify it; the view is the part before the
        # first comma past twenty words, and never a cut through the middle of a clause.
        cut = 20
        for index in range(20, min(len(words), 44)):
            if words[index].endswith(","):
                # The comma is on the last word of the clause, so the word stays: cutting at
                # `index` alone dropped it and the line ended mid-phrase ("...on a single rate the
                # hour makes no difference at." for the dishwasher answer).
                cut = index + 1
                break
        else:
            cut = 30
        first = " ".join(words[:cut]).rstrip(",") + "."
    if len(first.split()) < 3:
        return None
    # The sentence may end at a semicolon ("... more in heat or after exercise; tea, coffee,
    # milk and food all count"), and the line built from it puts a full stop on the end, so
    # the trailing mark goes rather than sitting in front of it: "exercise;." read as a typo.
    return first.rstrip(" .;,:") + "."


# A line asking for more of the answer just given, in the three shapes people write it: "anything
# else" / "what else works" / "what about the schools". "what about you" is not one of them.
MORE_ON_THIS = re.compile(
    r"\b(?:anything|something) (?:else|more)\b|\bwhat else\b"
    r"|\bwhat else (?:can|could|might|would|will|should|do|does|works?|helps?|matters?)\b"
    r"|\bany (?:other|more) (?:way|ways|idea|ideas|option|options|thing|things|tips?)\b"
    r"|\bis there anything (?:else|more|i can do)\b"
    r"|\bcan i do anything about (?:it|that|this)\b"
    r"|\bwhat about (?:the|my|our|his|her|their|those|these|it|that)\b")

# "what about my dad", "what about the schools": the thing named after "what about" is what the
# ask is about. It is only the answer just given when the conversation has already named it.
# "my mum is in hospital" then "what about my dad" is a different person, and "that's most of what
# I know on it" would be a claim about a subject the bot never touched (@plain-orange's read).
WHAT_ABOUT = re.compile(r"\bwhat about\s+(?:the|my|our|his|her|their|those|these)\s+(.+)$")
PERSON_NAMED = re.compile(
    r"^(?:mum|mom|mam|mother|dad|father|parent|parents|sister|brother|son|daughter|gran|"
    r"grandma|grandad|granny|nana|nan|husband|wife|partner|boyfriend|girlfriend|friend|"
    r"friends|baby|boy|girl|kids?|children|child|family|aunt|uncle|cousin|niece|nephew|"
    r"neighbour|neighbor|boss|colleague|carer|vet)\b")


def asks_for_more(text, memory):
    """True when the line asks for more of the answer just given, about the same thing.

    "anything else" and "what else works" are always about the answer. A "what about <thing>"
    ask names its own subject, so it is only the same subject when the chat has already named it,
    and a person named there is a different subject however close the relation.
    """
    said = str(text or "").strip().lower()
    if not MORE_ON_THIS.search(said):
        return False
    tail = WHAT_ABOUT.search(said)
    if not tail:
        return True
    named = tail.group(1)
    if PERSON_NAMED.match(named):
        return False
    return _named_recently(named, memory)


def _named_recently(named, memory, look_back=3):
    """True when the words of the named subject are in the last few turns, either side."""
    from ..memory.topics import keywords

    wanted = set(keywords(named))
    if not wanted:
        return True
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-look_back:]
    said = " ".join(str(t.get(key) or "") for t in turns for key in ("user", "bot"))
    return bool(wanted & set(keywords(said)))


def _answered_recently(memory):
    """True when the bot answered on the turn just before this one, from any module.

    Wider than `_answered_already`, which names the knowledge base because "what have you tried
    so far" only makes no sense after a fact answer. A request for more is about whatever was
    just said, so small talk counts too ("im thinking of moving to leeds" / "what about the
    schools"). The composer's own replies do not: after a nod or a condolence there is no
    answer to have more of, and "that's most of what I know on it" would claim knowledge the
    bot never offered.

    The module name alone cannot answer it: the chat module records a greeting and a topic
    turn alike as `chat`, so "hi" then "anything else" looked like a topic and got "that's most
    of what I know on it". What was said is the signal that can be trusted, so a line the
    memory's own reading calls not-a-subject (a hello, a thank you, a question about the chat)
    leaves nothing to have more of.

    Nor is a line that offered nothing an answer to have more of, whatever module said it: the
    last line has to have told the person something. A question back is the commonest way of
    saying nothing ("im thinking of moving to leeds" was answered "Worth planning rather than
    rushing into: what would have to go right for you?", and "what about the schools" then got
    "that's most of what I know on it", about schools the bot never mentioned), and a warm
    reaction is the other ("im feeling low" / "anything else"). "Asking for more of nothing" is
    worse than the honest hedge, so those lines leave nothing to have more of.

    A one-line acknowledgement is the exception, and it is the reason the reading walks back:
    "Fair enough." is the bot taking a nod or a refusal, not a reply about something new, so it
    does not wipe the answer from the chat. "recommend a film" / "no thanks at all" / "anything
    else" is still asking about the films, and the honest end line is the reply to it. Read off
    the last line alone, that turn got the pool's stock "Thanks for telling me - I'm here if you
    want to dig into any of that", which fits any message and answers none.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    index = len(turns) - 1
    while index > 0 and _only_takes_the_answer(str(turns[index].get("bot") or "")):
        index -= 1
    last = turns[index]
    if str(last.get("module") or "") in NO_MORE_OF:
        return False
    if not _told_them_something(str(last.get("bot") or "")):
        return False
    return not history.not_a_subject(str(last.get("user") or ""))


# The bot's own one-line acknowledgement: "Fair enough.", "Got it.", "Nice one.", "Alright then -
# good luck with it." It has to be short and carry no question, because a line that asks something
# back ("Fair enough. What have you enjoyed lately?") is the bot taking the subject further.
ACK_ONLY = re.compile(
    r"^(?:fair enough|fair|got it|got that|noted|understood|right|righto|right then|ok|okay|"
    r"alright|all right|sure|fine|nice one|sounds good|no bother|no worries|no problem|"
    r"hope it works out|lovely|good|great|grand|of course|certainly)\b[^?]{0,40}$", re.I)


def _only_takes_the_answer(said):
    """True when the bot's line only acknowledged what it was told, saying nothing of its own."""
    text = " ".join(str(said or "").split())
    if not text or len(text.split()) > 8:
        return False
    return ACK_ONLY.match(text) is not None


# The ways this bot says "I heard you" back: a nod, a condolence, a cheer. They are the reply
# to the line, not facts with anything behind them, so "anything else" after one is asking for
# more of nothing.
REACTED_ONLY = re.compile(
    r"^(?:sorry to hear|sorry\.|that sounds|that'?s (?:great|good|lovely|brilliant|rough|tough|"
    r"awful|a pain|a shame|a nuisance|rotten|understandable)|good on you|nice one|nice -|well "
    r"done|love that|fair enough|got it|makes sense|noted:|thanks for telling|i'?m listening|"
    r"i hear you|that'?s a lot)", re.I)


def _told_them_something(said):
    """True when the bot's last line said something, rather than asking back or only reacting.

    Read off the line itself, because the turn records only the module that said it and the
    chat module says a nod, a question and a fact alike.
    """
    text = said.strip()
    if not text or text.endswith("?"):
        return False
    return REACTED_ONLY.match(text) is None


def _the_answer_above(memory):
    """The bot's last real answer, as "the reply above" for a bare ask or a repeat.

    An acknowledgement is not a turn of its own: "my son is 4 and wont sleep" / "he shares with
    his sister" / "any tips" put "Got it - your son shares with his sister" between the ask and
    the answer, and the ask was then answered "what have you tried so far" about the answer the
    bot had just given in full. The line that comes after a note is about the answer under it,
    not about the note: "im going to portugal in july" / "no wait, august" / "whats it like in
    august" was told "that is everything I have on that one" because the note named August, and
    nothing had been said about August at all.
    """
    from .verdict import takes_a_fact_back
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    while turns and takes_a_fact_back(turns[-1].get("bot")):
        turns.pop()
    if not turns:
        return ""
    return str(turns[-1].get("bot") or "")


def _answered_already(memory):
    """True when the bot answered on the turn just before this one.

    Only the turn straight before counts. A bare ask follows the answer it is about, and
    "that's most of what I know on it" is only honest about that answer: an answer two turns
    back belongs to a different question by then ("my landlord wont let me have a cat" / "i
    really want one though" / "is there any way round it").
    """
    from .verdict import takes_a_fact_back
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    while turns and takes_a_fact_back(turns[-1].get("bot")):
        turns.pop()
    return bool(turns) and str(turns[-1].get("module") or "") == "answers"


TIPS_SPOKEN = (
    (re.compile(r"(?<![a-z0-9])4(?![a-z0-9])"), "for"),
    (re.compile(r"(?<![a-z0-9])2(?![a-z0-9])"), "to"),
    (re.compile(r"(?<![a-z0-9])u(?![a-z0-9])"), "you"),
    (re.compile(r"(?<![a-z0-9])ur(?![a-z0-9])"), "your"),
    (re.compile(r"(?<![a-z0-9])ne(?![a-z0-9])"), "any"),
    (re.compile(r"(?<![a-z0-9])pls(?![a-z0-9])"), "please"),
)
# The words that make a digit a number rather than a stand-in for "to" / "for".
TIPS_NUMBER_TAIL = re.compile(r"\s*(?:%s)\b" % "|".join(sorted(TIPS_UNIT)))


def _tips_spoken(text):
    """The line with its chat-speak read as words, leaving a number that counts something alone."""
    words = text.split()
    for i, word in enumerate(words):
        tail = words[i + 1] if i + 1 < len(words) else ""
        if word.isdigit() and TIPS_NUMBER_TAIL.match(tail):
            continue
        for pattern, said in TIPS_SPOKEN:
            word = pattern.sub(said, word)
        words[i] = word
    return " ".join(words)


def _tips_subject(clean):
    """The thing a plea for tips is about, said back, or None when the line names no thing."""
    text = _tips_spoken(" ".join(str(clean or "").lower().split()))
    # "give me a quick dinner idea" is a request for a recommendation, not a plea for tips on a
    # subject: only "any ideas" asks the way "any tips" does.
    if not TIPS_WORD.search(text) and not TIPS_ANY_IDEA.search(text):
        return None
    found = TIPS_SUBJECT_FOR.search(" " + text)
    subject = found.group("subject") if found else TIPS_SUBJECT_TAIL.sub("", " " + text + " ")
    subject = re.sub(r"[,.!?;:].*$", "", subject.strip(" ,.!?;:"))
    subject = TIPS_LEAD.sub("", " ".join(subject.split()))
    # "i need a new bath" is a subject; "i need some advice" is not one at all.
    subject = re.sub(r"^(?:i|we)\s+(?:really\s+)?(?:need|want|would\s+like|am\s+looking\s+for)\s+",
                     "", subject)
    subject = TIPS_REQUEST.sub("", TIPS_LEAD.sub("", subject))
    subject = TIPS_LEAD.sub("", subject)
    if not subject or subject.startswith("to ") or subject in ("it", "that", "this", "some", "anything", "something",
                                  "a", "an", "the", "advice", "tips", "help"):
        return None
    kept = [word for word in subject.split() if word not in FILLERS]
    if not kept or len(kept) > 6 or len(" ".join(kept)) > 40:
        return None
    if set(kept) & TIPS_CLAUSE or kept[0] in TIPS_VERB:
        return None
    return " ".join(TIPS_OWNER.get(word, word) for word in kept)


def _tips(memory, clean, repaired=None):
    """A reply that turns a plea for tips into the one question that makes a tip possible.

    `repaired` is the same line with its wrong words put right ("any ideaz" -> "any ideas"),
    read for the subject only when the typed line carries none: the plea is recognised in the
    spelling the person meant, so the thing it is about is the thing they meant too.
    """
    subject = _tips_subject(clean) or (_tips_subject(repaired) if repaired != clean else None)
    if not subject:
        return ""
    # A pet is the vet's line - it is a named specialist, and the question here would be a
    # guess at what is wrong with the animal. A body is not the same thing: measured, the health
    # advisor does not fire on a tips plea (`any tips for my back pain` names no symptom), so
    # that line gets the question below like any other subject.
    said = " " + re.sub(r"[^a-z0-9']", " ", str(clean or "").lower()) + " "
    if _who_for(str(clean or "").lower(), said, said.replace("'", "").split()):
        return ""
    pool = TIPS_AHEAD if TIPS_SOON.search(subject) else TIPS_THING
    return _choose(list(pool), memory, clean)
_ASKS_DEFINITION = re.compile(r"^\s*what(?:'s|s| is| are| was| does| do)\b|\bdifference between\b"
                              r"|\bwhat does .* (?:do|mean)\b|\bmeaning of\b")
# A line that asks where a thing is is asking for a place, not for a person to ring. With the
# reading that stopped "nappy" being "snappy", "where is the nappy", "where is my nappy bag"
# and "where did i put the nappy cream" all fell into the health visitor's hand-off - an answer
# to a symptom question, for a line about a bag. The hand-off stays wherever the line names
# something wrong (an ill thing, a leak, a smell), because "where is the rash" and "where is
# the leak" are that question with a place in it.
_ASKS_WHERE = re.compile(r"\bwhere(?:'s|s| is| are| was| were| did| do| does| can i| shall i)\b")
# Arithmetic has no advisor either: "how do I work out my hourly rate from my salary" is a sum.
# "i cant do the 10am gp appt on monday" is about the diary, so no health advisor either way.
_SCHEDULING = re.compile(r"\b(appt|appointment|appointments|cancel|reschedule|rearrange|rebook|"
                         r"double booked|move it|change it)\b")
_ASKS_ARITHMETIC = re.compile(r"\b(work out|calculate|convert|how much is|how many|percent|"
                              r"percentage|hourly rate)\b")
# "How do I fix a leak under the sink" wants to do it, so naming a plumber answers nothing.
# "i got a quote for 1,500, does that sound right" wants a way to check a price, not an expert.
# The price has to be in the line. "we split the rent 60 40, is that fair" is a question
# between two people, and a boiler quote is not the reply it wants.
QUOTE_ASKS = re.compile(r"\b(quote|quoted|estimate|price|priced|cost|bill|invoice|fee|charge)\b"
                        r".*\b(sound right|sounds right|too much|too high|too dear|steep|fair|"
                        r"reasonable|about right|normal)\b")
_ASKS_DIY = re.compile(r"\b(how do i|how can i|how to)\s+(fix|mend|repair|replace|install|fit|"
                       r"unblock|bleed|reset|clean|change)\b|\bmyself\b|\bmy own\b")


# A price asked to be judged, with nothing in the line that settles it. "is 120 pounds too much to
# spend", "is 250 too much" and "does that sound about right" (after "they want 40 quid") all got
# the search hedge, which is the one reply that cannot help: no search answers "is 120 a lot" until
# you know what the 120 buys, and the line does not say. QUOTE_ASKS just above reads the same
# request when the price has a word of its own in the line ("the plumber quoted 900 to fix it, is
# that fair"). This is the shape with no way in, and the reply gives the check that decides any
# price - one other price for the same thing, or for the same job from someone else - because that
# is true of every sum and needs nothing else from here. Nothing invents a price or a range: the
# only figure said back is the one the person wrote.
PRICE_VERDICT = re.compile(
    r"\b(?:too\s+(?:much|expensive|dear|pricey|pricy)|expensive|pricey|pricy|steep|overpriced|"
    r"dear|over\s+the\s+odds|rip[- ]?off|ripped\s+off|robbed|reasonable|fair|about\s+right|"
    r"sound\s+right|sounds\s+right|worth\s+it|good\s+(?:deal|price)|a\s+lot|that\s+much|"
    r"ok|okay|daylight\s+robbery)\b")
# A sum has to be in the line or on the turn before it: "the one i like is 250 pounds" / "is that a
# lot", "the fitter wants 900" / "does that sound about right", "the quote was 1200" / "seems like a
# lot?". The turn before is the only place it is read from, and only a figure that is money there.
# Without a sum these words are a judgement of something else - "is fibre worth it", "is the
# expensive oil worth it", "it isnt worth it" - and the check below answers a question nobody asked.
# The sum as the person wrote it. A currency mark, a number with its unit, a figure in words. Only
# what is in the line, so nothing is guessed; "250 pounds" is said back as "250 pounds".
MONEY_IN_A_LINE = re.compile(
    r"(?:[\u00a3$\u20ac]\s?\d[\d,]*(?:\.\d+)?)"
    r"|\b\d[\d,]*(?:\.\d+)?\s?(?:pounds?|quid|pence|euros?|dollars?|bucks|grand|k)\b"
    r"|\b(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|"
    r"seventy|eighty|ninety|hundred|thousand)\s+(?:pounds?|quid|euros?|dollars?|bucks|grand)\b"
    r"|\b(?:a\s+)?(?:couple\s+of\s+|few\s+)?(?:hundred|thousand)\s+(?:pounds?|quid|euros?)\b"
    r"|\ba\s+(?:tenner|fiver|grand)\b", re.I)
# A bare figure is a price in a short ask about spending ("is 120 too much"); it is a quantity
# anywhere a measure word says so, and those lines are turned away first.
A_BARE_FIGURE = re.compile(r"\b\d{2,}\b")
# The turn before can carry the sum with no currency word on it ("he wants 400", "they quoted 400"),
# and a verb of paying is what makes a bare figure there a price: "my sister is 40" is not one, so
# "is that a lot" after an age is left alone.
A_MONEY_VERB = re.compile(r"\b(?:want|wants|wanted|ask|asks|asked|asking|charge|charges|charged|"
                          r"charging|quote|quotes|quoted|quoting|cost|costs|costing|pay|pays|paid|"
                          r"paying|spend|spent|spending|come|comes|coming|say|says|said|tell|"
                          r"tells|told|give|gives|gave|price|priced)\b[^.?!]*?\b\d{2,}\b")
A_MEASURE = re.compile(
    r"\b(?:cups?|mugs?|glasses?|hours?|minutes?|mins?|miles?|km|kms|kilograms?|kilos?|kg|"
    r"grams?|degrees?|times?|days?|weeks?|months?|years?|cm|mm|metres?|meters?|litres?|"
    r"liters?|pints?|slices?|spoons?|teaspoons?|handfuls?|steps?|pages?|screens?|"
    r"episodes?|calories?|carbs?)\b")
# "too much for me" is somebody overwhelmed, not a price, and "for us" is the same shape.
FOR_A_PERSON = re.compile(r"\bfor\s+(?:me|us|him|her|them|you|myself|ourselves)\b")
# A sum split between people is a fairness question between them, not a price to hold against the
# market: "we split the rent 60 40, is that fair". QUOTE_ASKS keeps the same line out, same reason.
SPLIT_BETWEEN_PEOPLE = re.compile(r"\b(?:split|splits|splitting|share|sharing|going halves|"
                                  r"pay half|pays half|pay more|pay less)\b")
# A question, not a verdict said out loud: "is 250 too much" asks, and "it isnt worth it" (a deck row
# about somebody's own life) does not, so only the ask shapes get here.
A_PRICE_ASK = re.compile(r"^(?:and\s+|so\s+|but\s+|ok\s+|okay\s+|also\s+)?(?:is|isnt|aren'?t|"
                         r"are|was|wasnt|wasn'?t|were|does|doesnt|do|did|didnt|would|wouldnt|"
                         r"should|shouldnt|could|will|that|this|too|seems?|looks?|sounds?)\b|\?")
PRICE_VERDICT_LINES = (
    "{figure} only says something next to another price: the same thing elsewhere, or the same job "
    "from someone else. Get one of those and it is easy to call.",
    "Whether {figure} is a lot depends on what the same thing goes for. One other price - another "
    "shop, or another quote for the same work - settles it.",
    "Hold {figure} against one more price for the same thing before you decide; the pair tells you "
    "more than any rule of thumb.",
)


def _the_figure_in(text):
    """The sum as the person wrote it, or "" when there is no money in the line."""
    found = MONEY_IN_A_LINE.search(text or "")
    return " ".join(found.group(0).split()) if found else ""


def _a_price_wants_a_verdict(clean, memory):
    """The pool for a price asked to be judged, or None for any other line.

    Only a short ask with a sum in reach: a longer line puts the thing and the sum in the same
    breath ("the plumber quoted 900 to fix it, is that fair") and the quote check and the entries
    above read those better. A line that splits a sum with somebody, judges how much of something to
    use, or says the weight of it is on them, is not a price and keeps its own reading.
    """
    said = " ".join(str(clean or "").lower().split())
    if not said or len(said.split()) > 7:
        return None
    if not A_PRICE_ASK.search(said) or not PRICE_VERDICT.search(said):
        return None
    if (FOR_A_PERSON.search(said) or SPLIT_BETWEEN_PEOPLE.search(said)
            or A_MEASURE.search(said)):
        return None
    figure = _the_figure_in(said)
    if not figure:
        bare = A_BARE_FIGURE.search(said)
        figure = bare.group(0) if bare else ""
    if not figure:
        # "the one i like is 250 pounds" / "is that a lot": the sum is the one on the turn before,
        # and only the turn before, so a figure from earlier in the chat cannot take this turn. The
        # ask does not have to point at it ("seems like a lot?", "too expensive?") because a verdict
        # word on a question is already the pointing, and the turn before has to be money itself.
        before = _the_line_before(memory)
        figure = _the_figure_in(before)
        if not figure:
            paid = A_MONEY_VERB.search(" ".join(before.split()))
            bare = A_BARE_FIGURE.search(paid.group(0)) if paid else None
            figure = bare.group(0) if bare else ""
    if not figure:
        return None
    return tuple(line.replace("{figure}", figure) for line in PRICE_VERDICT_LINES)


# A present for a new baby is a gift question, and a baby mentioned in one is not a symptom:
# "how much do you spend on a new baby present" is not the health visitor's call.
GIFT_WORDS = frozenset(("present", "presents", "gift", "gifts", "spend on", "budget for",
                        "how much do you spend", "what do you get"))
# A home to buy is not a tenancy: "im 34 and still renting, should i be buying" wants the
# buying side, and Citizens Advice's tenant line would be answering a different question.
BUYING_WORDS = frozenset(("buying", "buy a house", "buy a flat", "buy a home", "bought",
                          "purchase", "ladder", "mortgage", "own a home", "should i buy"))
# A medicine is not a device: "can i take hayfever tablets with my blood pressure pills" is the
# pharmacist's question, while "my tablet wont connect to the wifi" is the maker's.
# A router is a device you log into, so it keeps its maker's page: it is the wifi itself,
# and what runs on it, that no support page can answer for.
NETWORK_WORDS = frozenset(("wifi", "wi-fi", "internet", "broadband", "network", "connection",
                         "signal", "online"))
# A drug or a supplement is the pharmacist's, by name: "should i take vitamins" is not a reason
# to ring 111, and the counter answers it in two minutes for free. `vitamins` and the brand-free
# drug names were missing, so those lines fell to the plain shrug.
MEDS_WORDS = frozenset(("tablets", "pills", "medicine", "medication", "prescription", "dose",
                        "doses", "capsules", "antibiotics", "vaccine", "vaccination", "jab",
                        "jabs", "vitamin", "vitamins", "supplement", "supplements", "ibuprofen",
                        "paracetamol", "aspirin", "painkiller", "painkillers", "antihistamine",
                        "antihistamines", "steroid", "steroids", "insulin", "inhaler"))


def _a_grown_up_asks(clean, words, said):
    """True when the baby in the line is a food's name or the line is about a grown-up.

    "can adults have baby rice" says the person outright. "can i eat baby food" names no child
    except inside the food's own name, so the food names come out first and the rest of the line
    is asked again for a child - "my baby wont eat baby food" keeps its baby, and "is baby food ok
    for a 7 month old" is a parent because the age is still there.
    """
    if _names(words, said, GROWN_UP_WORDS):
        return True
    left = " %s " % clean
    dropped = False
    for name in BABY_FOOD_NAMES:
        if " %s " % name in left:
            left = left.replace(" %s " % name, " ")
            dropped = True
    if not dropped or not _names(words, said, SELF_EATING_WORDS):
        return False
    return not _names(set(left.split()), left, CHILD_AT_HOME)


def _who_for(clean, said, words, topic=None):
    """Which person settles this line, or None. Split from the reply so a caller can ask what
    the line matches without spending a stock line on it."""
    if _ASKS_DEFINITION.search(clean) or _ASKS_ARITHMETIC.search(clean):
        return None
    diy = bool(_ASKS_DIY.search(clean))
    gift = _names(words, said, GIFT_WORDS)
    meds = _names(words, said, MEDS_WORDS)
    buying = _names(words, said, BUYING_WORDS)
    if _names(words, said, SCHOOL_WORDS) and _names(words, said, SCHOOL_TROUBLE):
        return SCHOOL_WHO
    if _names(words, said, ("password",)) and _names(words, said, PASSWORD_TROUBLE):
        return DEVICE_WHO
    if _names(words, said, COMPLAINT_WORDS) and _names(words, said, TRADER_WORDS):
        return COMPLAIN_WHO
    animal = any(word in ANIMALS or word.rstrip("s") in ANIMALS for word in words)
    if animal and _names(words, said, WILD_BIRDS) and _names(words, said, MESS_PLACES):
        animal = False  # mess to clean up, not an animal that needs a vet
    machine_mouse = is_a_machine_word(clean)
    if not animal and meds:
        return HEALTH_WHO
    if not animal and _names(words, said, FILLING_WORDS) and (
            _names(words, said, MOUTH_WORDS)
            or not (topic in FOOD_TOPICS or _names(words, said, FILLING_FOODS))):
        return DENTIST_WHO
    # "where is the nappy bag" is a lost-object question, not a symptom one, and the two health
    # hand-offs answer a symptom. The trades, the vet, the pest controller and the landlord
    # advice all keep their where-lines ("where is the boiler", "where are the mice").
    where_is_a_thing = bool(_ASKS_WHERE.search(clean)) and not _names(
        words, said, WHERE_SOMETHING_WRONG)
    for evidence, who in WHO_TO_ASK:
        if where_is_a_thing and who in (BABY_WHO, HEALTH_WHO):
            continue
        if machine_mouse and who == PEST_WHO:
            continue  # "my mouse isnt working" is a faulty mouse, not a visitor in the kitchen
        if animal and who != VET_WHO and evidence & SICKNESS:
            continue  # "my dog's cough" is the vet's, not the pharmacist's
        if animal and who == DENTIST_WHO:
            # A mouth word on a named animal is the vet's, by the same rule as a cough: "my
            # rabbit has dental problems" was sent to a human dentist because `dental` is in
            # the dentist row and no pet guard looked at it, SICKNESS having no mouth word.
            continue
        if who == HEALTH_WHO and _SCHEDULING.search(clean):
            continue  # a moved appointment is a diary question, not a symptom
        if who == HEALTH_WHO and _CHOOSING_BETWEEN_TWO.search(clean):
            # "should i bend my knees or my back" is a choice between two acts, and the
            # two-option reading further down the chain is the one that answers it. A pharmacist
            # cannot call that for somebody, and the line is not about a symptom anyway.
            continue
        if who == HEALTH_WHO and _names(words, said, JOINT_WORDS) and not (
                _names(words, said, evidence - JOINT_WORDS)
                or _ASKS_ABOUT_THE_JOINT.search(clean)):
            # A joint is a body part before it is a symptom. "my knee replacement is in march,
            # what should i pack" asks about a bag, and in a thread about lifting "should i bend
            # my knees or my back" asks which way to bend; the hand-off stays for the line that
            # asks about the joint itself.
            continue
        if diy and who in (TRADES_WHO, DEVICE_WHO):
            continue  # "how do i fix my washing machine" is a job, not a phone call
        if who == BABY_WHO and _a_grown_up_asks(clean, words, said):
            # "can i eat baby rice" is a grown-up asking about a food, not a parent asking about a
            # baby: a phone line instead of an answer is worse than a wrong card, so the hand-off
            # stands down when the only baby in the line is part of a food's name, or when the
            # line names a grown-up outright.
            continue
        if who == BABY_WHO and not _names(words, said, CHILD_AT_HOME):
            # "teething problems with the new car" is a new thing finding its feet, and the
            # word only looks like the baby's: it is the tooth-cutting word in "my baby is
            # teething". With no child named, the row has nothing to send a car to.
            continue
        if gift and who in (BABY_WHO, HEALTH_WHO):
            continue  # a present is a taste, not a symptom
        if meds and who == DEVICE_WHO:
            continue  # a pet's tablets are the vet's, not a support page
        if who == DEVICE_WHO and _names(words, said, NETWORK_WORDS):
            continue  # the wifi is not the phone: the maker's page has nothing to say about it
        if buying and who == TENANT_WHO:
            continue  # buying a home is not a tenancy question
        if who == WORK_WHO and not _names(words, said, WORK_ABOUT):
            continue  # a boss at the end of a level, or a boss who is a nightmare, is not a dispute
        if _names(words, said, evidence):
            return who
    if animal and (meds or _names(words, said, SICKNESS)):
        return VET_WHO
    return None


def who_settles(text, memory):
    """Which person settles this line - "the school office", "a vet" - or None.

    Split from the reply so another module can ask what the line would be answered with,
    without spending one of the composer's stock lines or moving its state.
    """
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(understood, dict) or \
            str(understood.get("text") or "") != str(text or ""):
        # The reading the store is holding is the line being answered now, and asking about an
        # earlier line with it answers for the wrong line: "who do i ring about it" was read as
        # the pronoun ask, and read that way "my boiler is banging" is not a boiler at all. The
        # re-read goes through a copy so the current turn keeps its own reading.
        borrowed = dict(memory) if isinstance(memory, dict) else {}
        borrowed.pop("understood", None)
        understood = understand(text, borrowed)
    clean = understood.get("clean") or " ".join(str(text).lower().split())
    words = understood.get("words") or []
    said = " " + re.sub(r"[^a-z0-9']", " ", clean) + " "
    return _who_for(clean, said, words, understood.get("topic"))


def _advisor(memory, clean, said, words):
    """Name the person whose job settles this line, when the line names that world: a reply
    or None. The subject alone is not enough - something has to be wrong in that world."""
    topic = (memory.get("understood") or {}).get("topic") if isinstance(memory, dict) else None
    who = _who_for(clean, said, words, topic)
    if not who:
        return None
    return _choose([line.format(who=who) for line in UNKNOWN_WHO], memory, clean)


# The words that make a thread a body thread even when nothing is wrong yet: a scan, a result, a
# clinic. `_thread_is_about_the_body` reads symptoms and parts, and "im scared about the scan" has
# neither, so the reader would have offered the list of trades to somebody waiting on a result.
HEALTH_VISIT_WORDS = frozenset("""
    scan scans mri ct xray x-ray ultrasound biopsy results result consultant clinic appointment
    appointments operation surgery transplant chemo radiotherapy dialysis test tests screening
    ward hospital
""".split())


# The mood words that make "who can i talk to" a person asking who could take some of it. Only
# the person's own state: "worried" is here and "low" is not, because "the car is low on oil" and
# "im low on milk" are the same word doing another job, and this fence decides whether the GP is
# named at all.
A_ROUGH_STRETCH = re.compile(
    r"\b(?:sad|lonely|alone|crying|cry|cried|tears?|grief|grieving|mourning|bereft|depressed|"
    r"depressing|miserable|unhappy|hopeless|worthless|anxious|anxiety|panic(?:king)?|scared|"
    r"afraid|terrified|worried|worry|worries|worrying|struggling|struggle|coping|"
    r"breaking point|burnt out|burned out|drained|overwhelmed|numb|empty|"
    r"cant cope|cannot cope|can't cope|hate myself|no one cares|nobody cares)\b")
# "who can i talk to" after a line about a funeral, a diagnosis or a death is the same ask, and
# the word is a noun rather than a feeling.
A_HARD_THING_HAPPENED = re.compile(
    r"\b(?:funeral|died|death|dying|passed away|diagnos\w*|cancer|tumour|tumor|terminally|"
    r"miscarriage|stillborn|divorce|separated|left me|walked out|sacked|redundant|"
    r"evicted|homeless|hospital|icu|intensive care|hospice)\b")


def _a_bad_stretch_above(memory, look_back=3):
    """True when the last few things the person said were about a bad stretch of their own.

    "who can i talk to" is the same line in a painting thread and in a lonely one, and the reply
    that fits the second ("the GP is not only for a body") is a cold, wrong answer to the first -
    it tells somebody looking for a class that the bot thinks they are ill. So the GP line is only
    offered when a turn or two before this one was about a mood, a funeral or a diagnosis.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-look_back:]
    for turn in turns:
        said = str(turn.get("user") or "").lower()
        if not said:
            continue
        if A_ROUGH_STRETCH.search(said) or A_HARD_THING_HAPPENED.search(said):
            return True
    return False


def _thread_has_a_health_visit(memory, look_back=3):
    """True when the last few things the person said were about a visit or a result coming."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-look_back:]
    for turn in turns:
        words = set(re.findall(r"[a-z'-]+", str(turn.get("user") or "").lower()))
        if words & HEALTH_VISIT_WORDS:
            return True
    return False


def _in_a_crisis_thread(memory):
    """True when the bot's own last word in this stretch named a crisis line.

    `in_a_safety_thread` is true for any safety answer, and most of those are ordinary comfort:
    "my mum says im lazy" gets one, and offering a person at Samaritans on the next line - with
    999 behind it - treats a bad week as an emergency. The line meant here is the one where the
    bot has already said a crisis line out loud (`CRISIS_WORDS`), because that is the thread the
    person is already in.
    """
    answer = _thread_answer(memory)
    return bool(answer) and any(word in answer for word in CRISIS_WORDS)


def _who_for_the_thread(memory, clean, understood=None):
    """The person to take a bare "who do i call about it" to, or a reply asking what it is.

    Read only in `_unknown`, so a line with a subject of its own never gets here and the looser
    reading costs nothing: what it replaces is the shrug. Three rungs, in the order of how much
    they know about this person: the trouble they named a turn ago (the same reading that names a
    person for a line that says it outright), then the actor the bot's own answer named a moment
    ago ("report it to the council"). With neither, the honest reply is the route list for a call
    and the talk-to lines for a person to talk to, plus the one question that would settle it.
    """
    # The line as typed, not as the reading resolved it: "who do i ring about it" comes out of
    # the reading as "who do i ring about my dog", because the engine has already put the
    # pronoun back to the thing named a turn ago. The ask is the same ask, and this reader
    # wants it in the shape the person used, where the thread is visibly not named.
    typed = str((understood or {}).get("text") or "") if isinstance(understood, dict) else ""
    line = typed or clean or ""
    # A person to talk to is read before a person to ring, because the two overlap on "talk to"
    # and only one of them is a service: "who can i talk to" is somebody to listen, and it must
    # not come back with a list of desks. A line that names its own subject keeps the call
    # reading, since "who do i talk to about my landlord" is a question about a desk.
    a_voice = bool(WHO_TO_TALK_ASK.search(line)) and not re.search(
        r"\babout\s+(?!it\b|that\b|this\b|them\b)\w|"
        r"\b(?:talk|speak|chat)\s+(?:to|with)\s+(?:the|a|an|my|your|his|her|their)\b", line)
    a_call = bool(WHO_FOR_IT.match(line)) if not a_voice else False
    if not (a_call or a_voice):
        return None
    # The actor the bot's own last answer named comes first: "my landlord says its my fault" was
    # answered "ask the council's environmental health team to step in", so "who can i talk to"
    # next is a question about that answer, and standing on it is what a friend does. The wider
    # reading below is what to fall back to when the answer named nobody.
    answer = str(last_bot(memory) or "").lower()
    if answer:
        for word, name in NAMED_BODIES:
            if re.search(r"\b" + re.escape(word) + r"\b", answer):
                shapes = WHO_FOR_IT_SAID_VOICE if a_voice else WHO_NAMED_BEFORE
                return [shape.format(who=name) for shape in shapes]
    # Not just the line above: "my boiler is banging" then "is it dangerous?" then "who do i call"
    # leaves a middle turn with no trouble in it at all, and the person is still in the boiler
    # thread. Three lines is the stretch the reading itself keeps for a follow-up.
    for said in reversed([str(t.get("user") or "") for t in
                          [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-3:]
                          if isinstance(t, dict)]):
        if not said:
            continue
        try:
            who = who_settles(said, memory)
        except Exception:  # noqa: BLE001 - a reading that fails just offers the next rung
            who = None
        if who:
            shapes = WHO_FOR_IT_SAID_VOICE if a_voice else WHO_FOR_IT_SAID
            return [shape.format(who=who) for shape in shapes]
    # "im scared about the scan" then "who do i ring": the route list under this names money, a
    # repair and a form, and none of them is a body. What a person does about a body is have it
    # looked at, which is a name and an hour, not a list of trades.
    if a_call and (_thread_is_about_the_body(memory) or _thread_has_a_health_visit(memory)):
        return list(WHO_FOR_IT_BODY)
    if a_call:
        return list(WHO_FOR_IT_ROUTES)
    return list(WHO_TO_TALK_TO_A_BAD_STRETCH if _a_bad_stretch_above(memory) else WHO_TO_TALK_TO)


def _trouble(memory, clean, words):
    """A statement of trouble ("my landlord wont fix the damp") still deserves the person who
    can settle it. Only with a trouble cue in the line: "i paid off my mortgage" is not a
    money problem, so the plain nod stays.

    A grown-up's plain symptom is not one of those: "ive got a sore throat" wants the care line
    the composer already has (rest, warm drinks), not a queue for the GP, so that row is only
    named when the line asks something ("should i worry", "how long does it last"). A baby's
    symptom is different: "my baby has a cough" is the health visitor's, question or not.
    """
    said = " " + " ".join(words) + " "
    if not any(word.startswith(cue) for word in words for cue in TROUBLE_CUES):
        return None
    if not _reads_as_question(clean, words):
        # The topic goes through, so a line with "filling" in it and no mouth word keeps the
        # food answer when the conversation is about cooking: the same escape `_advisor` uses.
        topic = (memory.get("understood") or {}).get("topic") if isinstance(memory, dict) else None
        who = _who_for(clean, said, words, topic)
        if who == HEALTH_WHO:
            return None  # your own sore throat is a symptom to look after, not a queue to join
    return _advisor(memory, clean, said, words)


def _is_a_form(word, evidence_word):
    """True when `word` is `evidence_word` with a grammatical ending on it.

    "boilers", "coughing", "itched", "itchy", "eviction" are forms of their word. "pesto",
    "toothbrush", "rasher" and "example" are different words that start the same way, and a
    doubled consonant before the ending is still an ending ("resetting", "vomitting").
    """
    tail = word[len(evidence_word):]
    if not tail:
        return True
    if word in NOT_A_FORM:
        return False
    if tail in ENDINGS:
        return True
    return (len(tail) > 1 and tail[0] == evidence_word[-1] and tail[1:] in ENDINGS)


def _names(words, said, evidence):
    """True when the line uses one of these words: whole, a phrase, or a longer form of it
    ("coughing", "boilers", "landlords"). A short word has to match whole, so "taxi" is not
    "tax" and "hr" is not "hrm"; and a longer word only counts when the extra letters are an
    ending, so a toothbrush is not a tooth and pesto is not a pest."""
    for word in evidence:
        if " " in word:
            if word in said:
                return True
        elif any(w == word or (len(word) >= 4 and w.startswith(word)
                               and _is_a_form(w, word)) for w in words):
            return True
    return False


def _reads_as_question(text, words):
    """True when the line asks something, even if the understanding engine called it a
    statement (a question mark mid-line, a typo for a question word: "whats", "wats", or a
    question word that opens a later clause)."""
    if "?" in text:
        return True
    plain = [w.replace("'", "") for w in words]
    if plain and WORD_FIXES.get(plain[0], plain[0]) in QUESTION_WORDS:
        return True
    # A question word after a preposition is not an ask: "we argued about who should pay for
    # dinner" and "im worried about what to say" are telling me something, so the question
    # words inside those clauses are dropped before the late-question test.
    joined = INDIRECT.sub(" ", " " + " ".join(plain) + " ")
    later = INDIRECT.sub(" ", text.lower())
    # A question word can also come later in the line: "my gums are bleeding who should i
    # see" is a question without a question mark or a question word first. LATER_QUESTION
    # covers the question words and modal shapes; ASK_SHAPES adds the asks that carry no
    # question word at all ("any tips", "is it worth fixing").
    return bool(LATER_QUESTION.search(later) or ASK_SHAPES.search(joined))


def _reads_as_a_question_when_repaired(text):
    """The opening shape of the repaired line: a question word first, or an inversion.

    "hw much sleep do kids need" and "wdyt about leeds" are questions whose first word the
    person shortened, and the repair puts the question word back. This is the second reading,
    so it is deliberately the narrow half of `_reads_as_question`: a question word that only
    arrives later in the line is not enough, because "dont know why" repairs to "do not know
    why" and the late "why" would turn a follow-up into a search hedge.
    """
    plain = [word.replace("'", "") for word in str(text or "").split()]
    if plain and WORD_FIXES.get(plain[0], plain[0]) in _OPENING_QUESTIONS:
        return True
    return bool(ASK_SHAPES.search(" " + " ".join(plain) + " "))


def _help_topic(clean, understood):
    """A capability ask with a topic gets a line inside that topic, or None.

    "what can you help me cook tonight" is not a request for the list of every domain; the
    engine has already read cooking, so the reply stays there and asks the next question.
    A bare "what can you do" has no topic and keeps the ABOUT help pool.
    """
    if not isinstance(understood, dict) or not HELP_TOPIC_ASK.search(clean):
        return None
    # Only a topic the line names itself: a bare "what can you help with" inherits the last
    # topic from the conversation, and answering it inside that topic would be a guess.
    topic = understood.get("topic_own")
    if not topic or topic in ("about-the-bot", "small-talk", "opinions"):
        return None
    return HELP_TOPIC.get(topic) or HELP_TOPIC_ANY


def reads_as_about_itself(text, memory=None):
    """True when the line is a question about the bot itself, for the arbiter's use.

    A topic entry matches a word or a topic id, so "are you connected to the internet" reached
    the guest-wifi card and "what model do you run" reached the search hedge: the line is about
    the bot, and no entry about the world can answer it. The module that carries this file
    declares `TAKES_AS_IT_COMES` with this, so on these lines the composer's own line takes the
    turn whatever else proposed - and every one of the readings is narrow, so an ordinary
    question that happens to use the same words ("can you think of a name for my cat", "how do
    i connect to the internet") is not claimed.
    """
    clean = _self_line(text)
    # "do you forget things", "did you forget what i said": the bot is the one who might forget, and
    # the memory answer is the one to give. The reading of the question is `FORGETTING_ASK`, the same
    # one that answers it, so a line read here always has the bot's own answer behind it.
    return (_about(clean, None) in ABOUT_ITSELF_KINDS
            or bool(FORGETTING_ASK.search(clean)))


# A question inside the line is still the line's question. "Im skint does that mean i get
# universal credit" is somebody asking about benefits, and "im skint is there any help" is the
# same ask, but the reading's own fence (`kind == question` in bot/understanding/topics.py) sees
# a statement with a question clause hanging off it and lets both through - so the claim answered
# a benefits question with "Right before payday is the hardest bit of the month. What have you got
# in the cupboard?". Any question shape anywhere in the line keeps the turn where it was.
QUESTION_CLAUSE = re.compile(
    r"\b(?:does|do|did|can|could|should|would|will|shall|is|are|was|were|have|has|am)\s+"
    r"(?:there|that|this|it|i|you|we|they|he|she|any|my|me|the)\b"
    r"|\b(?:what|where|who|which|when|how)\s+(?:can|could|should|do|does|did|is|are|would|will|"
    r"am|to|if|about|much|many|long|often)\b")


# What is short is a thing with its own entry. "im skint and i cant afford my electric" is
# answered by the payment-plan card, "im skint and my gas bill is huge" by the warm-home one and
# "im skint and i owe my mate 200" by "say it before they have to ask" - every one of them the
# answer that person needs. The week's own line says what to do about a week with nothing left in
# it, and it is only for the lines that say nothing but that: a line naming a bill, the rent or a
# debt hands the turn back to the entry that knows the thing.
A_THING_THAT_IS_SHORT = re.compile(
    r"\b(?:bill|bills|electric|electricity|leccy|gas|water|council\s+tax|rent|mortgage|"
    r"broadband|wifi|wi-fi|phone\s+bill|arrears|owe|owed|owes|debt|debts|loan|overdraft|"
    r"credit\s+card|store\s+card|direct\s+debit|instal?lment)\b")


def reads_as_a_tight_week(text, memory=None):
    """True when the line only says the money has run out, for the arbiter's use.

    README says the reply to that line is about the tight week, not about saving, and this file
    has it (`TIGHT_MONEY`). A money entry reads a word of the same line ("skint", "no money
    left") and answers a saving question instead - freeing cash over months to somebody asking
    how to get to Friday - so it takes the turn from the composer at PRIORITY 0. The reading is
    the understanding engine's own, and it is narrow: a question is left alone ("what can i cook
    till payday") and so is a line long enough to be about something else, so the composer only
    claims the lines that are nothing but the week being long.
    """
    # The reading is the line's own, so it is made here and not taken from memory: the engine
    # carries the subject of the conversation across turns, so `memory["understood"]` still says
    # the money has run out on the bare continuation after it, and a "go on" a moment after a
    # tight week was answered with the closing line ("Thanks for telling me - I'm here if you want
    # to dig into any of that") instead of the answer's own next step.
    context = dict(memory or {})
    context.pop("understood", None)
    try:
        from ..understanding import understand
        understood = understand(text, context)
    except Exception:  # noqa: BLE001 - a reading that cannot be made claims nothing
        return False
    if not isinstance(understood, dict) or not understood.get("tight_on_money"):
        return False
    try:
        from ..understanding import topics
        if not topics.tight_on_money(understood.get("norm"), understood.get("kind")):
            return False
    except Exception:  # noqa: BLE001 - without the second reading the line is left alone
        return False
    if QUESTION_CLAUSE.search(_self_line(text)):
        return False
    if A_THING_THAT_IS_SHORT.search(_self_line(text)):
        return False
    # A bare "go on" a moment later is somebody asking the bot to keep talking, not the week said
    # again: the pool's line ends by asking what is left and how long till the money comes, and
    # answering the ask with the closing line is worse than saying the answer again. The line is
    # left to the answer path, which has the money in it and hands back the ask it ended on.
    try:
        from ..memory.more import asks_for_more
        if asks_for_more(text):
            return False
    except Exception:  # noqa: BLE001 - a continuation that cannot be read keeps the pool
        pass
    # The composer's own line for it is chosen before the reaction and the flat pools, so this is
    # the same reply the person gets on the phrasings no money entry reads.
    return True


# "and" on its own is the shortest way of saying go on, and the pool that answers a flat ack
# said "Alright then - good luck with it" to it, which ends the conversation the person is trying
# to keep going.
BARE_AND = re.compile(r"^(?:and|and then|and\?|then|so|ok and|and so)[\s.?!,]*$", re.IGNORECASE)


def a_continuation_of_the_tight_week(memory, text):
    """True when a bare "go on" follows the composer's own tight-week line."""
    if not BARE_AND.match(text or ""):
        try:
            from ..memory.more import asks_for_more
        except Exception:  # noqa: BLE001 - a continuation that cannot be read is no continuation
            return False
        if not asks_for_more(text):
            return False
    turns = (memory or {}).get("turns") or []
    if not turns or not isinstance(turns[-1], dict):
        return False
    # The line the bot just said has to be the pool's own, which is what makes this the same
    # subject: a "go on" after anything else is the answer path's turn.
    # The pool's own line or the continuation already given: a second "go on" is the same week
    # still, and the picker never says the same line twice.
    return str(turns[-1].get("bot") or "").strip() in TIGHT_MONEY + TIGHT_MONEY_MORE
def reads_as_small_talk(text, memory=None):
    """True when the line is the manners question about the bot's own day, for the arbiter's use.

    "Hows your day going anyway" and "what have you been up to today" come after an answer as
    often as they open a chat, and every follow-up reader in the bot reads a question with no
    subject of its own as a question about the thing on the table: after the egg answer, "hows
    your day been" got the sentence about keeping boiled eggs in the fridge. The line is about
    the bot, though, and the pool that says how its day went is the answer to it, so the module
    that carries this file declares `TAKES_AS_IT_COMES` with this and the composer's line takes
    the turn. Safety is read before this claim, so a small talk line in a live emergency still
    gets the emergency reply.

    Only the manners question itself is claimed, and only where the pool has a line for it: a
    line the reading cannot see ("how about your day") is left to the chat module, which answers
    it better than a shrug. A line that goes on to name anything ("are you having a baby", "what
    are you doing about the damp") is not claimed.
    """
    clean = _self_line(text)
    if _about(clean, None):
        return False
    # The pool is cheerful, and the turn above may be a hard one: "i feel awful today" then "hows
    # your day been" is the bot changing the subject to itself, and "my mum has cancer" then "and
    # you" is worse. A module that read the whole thread answers those with the low line, so the
    # claim stands down for the whole hard week and not for a list of its words (spare-leopard on
    # #6004: `module == "answers"` is not a test of a hard turn, because the knowledge module
    # answers plenty of them).
    if _a_low_turn_above(memory):
        return False
    # The hand-back asked with nothing else in it is the same question: "what about you",
    # "and you", "yourself" after an answer are the person passing the question over, and the
    # pool that says how the bot's day went is the reply. Read before the phrase lists because
    # these lines carry no "how are you" for them to find.
    if HAND_BACK.match(clean):
        # A hand-back means something only where there is something to hand back from. As the
        # first thing typed there is nothing passed over, and the chat module's warmer "I'm well,
        # thanks for asking. How is your day going?" is the better opening; the fault this claim
        # answers - the follow-up readers taking the line as a question about the thing on the
        # table - only happens after a turn.
        return bool((memory or {}).get("turns") if isinstance(memory, dict) else None)
    # The claim is only worth making where the pool has a line: a line the manners reading
    # cannot see ("how about your day") is answered by the chat module with a better one, so it
    # is left alone rather than handed to a module that would shrug at it.
    if not _asks_how_are_you(clean):
        return False
    # The plain "how are you" and "hows it going" are answered by the chat module with the same
    # manners pool, so they are left to it: what this claims is the shapes it reads as a
    # question about the last thing said. `YOUR_DAY_ASK` is the widest of them and the one the
    # claim cannot leave out: it puts a verb between the person and the day ("are you having a
    # good day", "did you have a good day then"), and a line the phrase list has no entry for is
    # read by the knowledge module as a question about the thing above - after the egg answer,
    # "are you having a good day" got the paragraph about cholesterol.
    if YOUR_DAY_ASK.search(clean) and not (YOUR_OWN_TIME.search(clean)
                                          or YOUR_TIME_ASK.search(clean)):
        # The verb shape is claimed only where the fault is: after an answer. That is where the
        # knowledge module reads it as a question about the thing above, and where the chat
        # module never gets the turn. After something the person has just said, chat answers it
        # better than the pool does ("i went to a party tonight" / "did you have a good day" ->
        # "No days like that on my side, so nothing to report - how was yours?").
        return _an_answer_above(memory)
    return bool(YOUR_OWN_TIME.search(clean) or YOUR_TIME_ASK.search(clean))


# The plainest way of saying it: `_mood` holds "struggling" and the loss reading holds "i cant
# stop crying", but "im not coping" and "i cant cope anymore" are in neither, and a cheerful day
# line after one of them is the bot changing the subject to itself (sure-umbrella on #6004).
_NOT_MANAGING = re.compile(
    r"\b(?:i|im|i'm|i am|we|we're|were)\b[^.]{0,14}\b(?:not coping|cope any ?more|"
    r"can'?t cope|keep going|take any ?more|falling apart|falling to pieces|breakdown|"
    r"breaking point|not managing|cant manage|can'?t manage|do this any ?more)\b")


def _a_low_turn_above(memory):
    """True when the last turn or two were heavy, so the cheerful pool must not take the turn.

    A hard week is the first reading (`_hard_week_in_the_thread`, which covers a death, an
    accident and a gentler word list), and the second is the engine's own sign on the person's
    line: "i feel awful today" and "i have a lump and im scared" are a low the word lists do not
    carry, and the module that reads the whole thread answers them with the low line until this
    claim stands out of the way (spare-leopard on #6004).
    """
    if not isinstance(memory, dict):
        return False
    if (_hard_week_in_the_thread(memory) or _in_a_loss_thread(memory)
            or _grief_thread(memory) or _news_above(memory)):
        return True
    for earlier in [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-2:]:
        line = " ".join(str(earlier.get("user") or "").lower().split())
        if not line:
            continue
        # The two readings the rest of the composer already has for a heavy line: the engine's
        # sign, and the mood the pools read a word like "struggling" or "awful" by. "im really
        # struggling at the moment" is polarity 0 to the engine and negative to `_mood`, and the
        # turn after it was the cheerful pool until both were read here (sure-umbrella on
        # #6004). A diagnosis named of somebody close is neither: `_news_above` holds those,
        # with the readings of a death and a care thread.
        read = understand(line, {})
        if isinstance(read.get("polarity"), int) and read["polarity"] < 0:
            return True
        if _mood(_words(line), line) == "negative" or _NOT_MANAGING.search(line):
            return True
    return False


def _an_answer_above(memory):
    """True when the bot's last line was the knowledge module's answer to a question.

    The same test `bot/memory/repeat.py` makes before it will say an answer again: the turn came
    from `answers`, and it is a line long enough to be an answer and not a question back. A nod,
    a hello or the composer's own closing line is not one - "i went to a party tonight" is
    answered "Thanks for telling me - I'm here if you want to dig into any of that", and the chat
    module's reply to the question after it is better than this pool's.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    last = turns[-1] if isinstance(turns[-1], dict) else {}
    said = str(last.get("bot") or "").strip()
    return (last.get("module") == "answers" and len(said) >= 50
            and not said.rstrip().endswith("?"))


def _a_repair_already_spoken_of(memory):
    """True when the bot's last line already said what a repair would involve.

    "my glasses broke" / "can it be repaired" was answered by the knowledge card with the optician
    and the price of a frame repair; a generic "ask a repair shop for a quote" then talks over an
    answer that had the thing in front of it. A card about a symptom is not that answer - the
    boiler's pressure gauge says nothing about whether it can be mended - so the test is on the
    words of that line, not on the module alone.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    last = turns[-1] if isinstance(turns[-1], dict) else {}
    if last.get("module") != "answers":
        return False
    said = str(last.get("bot") or "").lower()
    return bool(re.search(r"\b(?:repair|repairs|repaired|repairing|mend\w*|fix\w*|"
                          r"replace\w*|replacement|part|parts|quote|quoted|engineer|"
                          r"optician|servic\w+)\b", said))


# The words people put in front of a question when they are changing the subject: "ok random
# question, do you ever make mistakes". They say the person knows the line is a turn away from
# what the chat was on, and every phrase list below is anchored at the start of the line, so a
# lead-in that was kept turned a question about the bot into a card for the last thing talked
# about (a tomato chat answered it with a tomato sauce). These are lead-ins and nothing else: the
# words that carry a subject ("my tomatoes", "the roast") are not on the list, and dropping one
# cannot make a line about the world into a line about the bot.
LEAD_IN = re.compile(
    r"^(?:(?:ok|okay|okey|kk|right|so|ah|oh|ohh|well|anyway|anyways|and|but|now|hmm+|er+|um+|uh+|hey|"
    r"sorry|quick question|random question|stupid question|silly question|daft question|"
    r"this is (?:a bit |a |totally )?random|bit of a random one|a random one|unrelated|"
    r"off topic|just wondering|i was wondering|wondering|can i ask|may i ask|"
    r"just out of curiosity|out of curiosity|by the way|btw)\b[\s,:.!?-]*){1,4}")


def _self_line(text):
    """The line as these readings see it: lowercase, no apostrophes, single spaces, no lead-in."""
    clean = " ".join(str(text or "").lower().replace("\u2019", "'").replace("'", "").split())
    return LEAD_IN.sub("", clean) or clean


def _a_tally_of_its_own_day(understood):
    """True when the line counts the bot's own doings rather than asking what it remembers.

    The reading makes the distinction once (`counts_the_bots_own_day`), so the composer does not
    have to read the line again: the answers lane and this pool ask the same question.
    """
    return bool(isinstance(understood, dict) and understood.get("counts_the_bots_own_day"))


# Chat-speak, spelled out for the phrase tables only. "r u a robot" and "are u a bot" are the
# same question as "are you a robot", and the engine expands a leading "u" or "ur" but not one in
# the middle of a line, so the identity, memory and capability phrases were only ever matched on
# the spelled-out line: "r u a robot" fell through to the search punt while "are you a robot" got
# the answer. One expansion here covers every phrase in those tables, so no table grows a
# chat-speak row of its own. It is not applied to the line anywhere else: a "u" that means the
# letter, or a word that merely ends in one, is only rewritten for this comparison.
_SPELLED_SHORT = (
    (re.compile(r"(?<![a-z])(?:r u|ru|r you|are u|am u)(?![a-z])"), "are you"),
    (re.compile(r"(?<![a-z])u(?![a-z])"), "you"),
    (re.compile(r"(?<![a-z])ur(?![a-z])"), "your"),
    (re.compile(r"(?<![a-z])u r(?![a-z])"), "you are"),
    (re.compile(r"(?<![a-z])wat(?![a-z])"), "what"),
    (re.compile(r"(?<![a-z])wot(?![a-z])"), "what"),
)


def _spelled_out(clean):
    """The line with chat-speak spelled out, for the phrase tables in this file."""
    out = clean
    for pattern, word in _SPELLED_SHORT:
        out = pattern.sub(word, out)
    return out


def _about(clean, understood=None):
    """Which about-the-bot question this is, or None.

    The reading says which kind the line is, so "what can you do with leftover rice" is not
    answered as a question about the bot: the engine sees what follows the question and calls
    it about the rice. The phrase lists stay as a floor for lines the engine does not label.

    The lead-in goes first (`_self_line`, `LEAD_IN`): every list below is anchored at the start of
    the line, so "ok random question, do you ever make mistakes" was read as a line with no ask
    in it at all, and a tomato chat answered it with a tomato sauce recipe.
    """
    clean = _self_line(clean)
    # What the bot does with what it is told. First, because no other reading has a kind for it and
    # the two that answered instead were a card matching "keep" and the search hedge. The line is
    # read with the bot's own pronouns (`_self_line`), so "who can see this chat" and "can anyone
    # see what i say" are the same ask.
    _self = _self_line(clean)
    if (PRIVACY_ASK.search(_self) or PRIVACY_SHAPES.search(_self)
            or BETWEEN_US_ASK.search(_self)) \
            and not NOT_WHAT_I_SAID.search(_self):
        return "privacy"
    # After privacy: "can you keep a secret" and "will you judge me" are the same promise from a
    # shyer angle, but they ask for honesty rather than for a record, and the privacy pool talks
    # about logs where these want a plain yes or no.
    if TRUST_ASK.search(_self):
        return "trust"
    if SECRET_ASK.search(_self) or PROMISE_ASK.search(_self):
        return "secret"
    if JUDGING_ASK.search(_self):
        return "judging"
    # Before the phrase lists: "what are you" sits inside "what are you bad at", and the list
    # would answer the wrong question. Both readings are anchored to the end of the line, so
    # neither can take a line that goes on to ask about something else.
    # What the bot does with what it is told, and whether it can be trusted: no card answered
    # either, so a search hedge went where the bot itself is the only thing that knows. The food
    # and medicine words hold both reads off, since "is this safe to eat" is about the thing in
    # their hand and has an answer of its own.
    # The same fence the branch above applies: "is this private healthcare worth it" matches
    # `PRIVACY_ASK` on the "is this private" shape, and `NOT_WHAT_I_SAID` is the reading of
    # "private" as the kind of thing ("private school", "private rented", "keep my receipts").
    # Without it here the second branch answered the question nobody asked.
    if PRIVACY_ASK.search(clean) and not PRIVACY_NOT_THIS.search(clean) \
            and not NOT_WHAT_I_SAID.search(clean):
        return "privacy"
    if TRUST_ASK.search(clean) and not PRIVACY_NOT_THIS.search(clean):
        return "trust"
    if LIMITS_ASK.search(_self_line(clean)):
        return "limits"
    if ONLINE_ASK.search(_self_line(clean)) and not OWN_DEVICE.search(_self_line(clean)) \
            and not A_BARE_ONLINE.search(clean):
        return "online"
    if the_manners_question([word.strip(string.punctuation)
                             for word in _self_line(clean).split()]):
        # "what are you up to" holds "what are you" and is not the identity card: the whole line
        # asks how the bot is filling its time, which the engine reads as small talk. Both
        # readings below are substring tests, so they would answer a hello with "I'm a chatbot -
        # here to help and chat" and stand the chat pool's own answer down (`hello`).
        if understood is not None and (understood.get("intent") or "") != "smalltalk":
            # The ask is on the line but the engine did not take it as the doings question:
            # "what do you do" is what the bot is for, and standing the capabilities card down
            # for it left the search punt answering (black-lantern, #6380). A reading is what
            # tells the two apart, so without one the answer stays the small-talk one.
            return "help"
        return None
    spelled = _spelled_out(clean)
    if WHAT_ARE_YOU.search(clean) or WHAT_ARE_YOU.search(spelled):
        return "identity"
    # A verb after "what are you" stands the identity card down only when the knowledge module
    # answers the line. Both callers run the same test (`_about(clean, reading)` from the
    # composer, `_about(clean)` from the routing lane), so one line is read one way.
    if re.search(r"\bwhat are you\b", spelled) and not _the_answers_take_it(clean):
        if WHAT_ARE_YOU_NOUN.search(clean):
            return "identity"
        if GOOD_AT_ASK.search(clean):
            return "help"
        if CLOTHES_ASK.search(clean):
            return "clothes"
        if LIKE_ASK.search(clean):
            return "identity"
        return "self_doing"
    # Before the engine's kind and before the help reading: "how do you work" is a question about
    # the bot's make, and both of those were reading it as something else - the engine labels it an
    # about-the-bot question of the "what can you do" kind, and the capability list answered it.
    if WORKINGS_ASK.search(clean):
        return "workings"
    # Before the phrase lists and before the engine's kind: a complaint about the bot's own asking
    # is not a question about the subject it was asking about, and the answer is about the bot.
    if ASKING_ASK.search(_self):
        return "asking"
    for phrase in IDENTITY:
        if phrase in clean or phrase in spelled:
            return "identity"
    if FORGETTING_ASK.search(clean):
        return "memory"
    for phrase in MEMORY:
        if phrase in clean or phrase in spelled:
            if RECALL_TAIL.search(clean) and _the_store_takes_it(clean):
                return None
            return "memory"
    if isinstance(understood, dict):
        kind = understood.get("about_bot_kind")
        if kind in ABOUT or kind in ABOUT_SELF:
            return kind
    # "am i talking to a human", "is this a real person": the same question as "are you a
    # human", asked about the other end of the chat rather than to it.
    asked = HUMAN_ASK.search(clean)
    if asked and _opens_the_line(clean[:asked.start()]) \
            and not _asks_elsewhere(clean[asked.end():]):
        return "identity"
    if _asks_for_a_person_to_talk_to(clean):
        return "identity"
    matched = HELP_ELSE.search(clean)
    if matched and _free_tail(matched.group(1) or matched.group(2)):
        return "help"
    # "can you help me" is an ask to the bot with nothing else on the line: there is no subject
    # to understand and nothing to search for, so the honest answer is what it is for, not the
    # shrug. A chore or a topic after it ("can you help me end this email", "can you help me with
    # my cv") is a line about that thing, so this only reads the ask on its own.
    if _asks_for_help(clean, understood):
        return "hand"
    return _the_bot_itself(clean)


# The model's name in the line is the bot's own make, not a fact about the world: "is this
# chatgpt", "which version of gpt are you", "are you claude". MODEL_ASK above reads the shape
# ("what model are you"), and these say the same thing with the name in a different place, so the
# search hedge answered them as if a search could settle what the bot is made of. Read only in a
# short line: "is this chatgpt good for essays" is about the essays, and "what model is this" can
# be a follow-up about a car.
MODEL_NAMED = re.compile(
    r"\b(?:what|which)\s+(?:version|model|kind|type|sort)\s+of\s+(?:gpt|chatgpt|ai|llm|model|"
    r"chatbot|bot|openai)\s+(?:are|is)\s+(?:you|u|this|it)\b|"
    r"\b(?:is|are)\s+(?:this|that|it|you|u)\s+(?:a\s+|an\s+|really\s+)?(?:chatgpt|gpt[-\s]?\d*|"
    r"openai|claude|gemini|bard|llama|copilot|an?\s+(?:ai|llm|chatbot|bot))"
    r"\s*(?:then|really|though|now|huh|yeah|or not)?\s*$")


def _names_the_make(clean):
    """Whether the line names what the bot is made of, in a line short enough to be only that."""
    said = re.findall(r"[a-z0-9']+", str(clean or "").lower())
    return len(said) <= MODEL_NAMED_WORDS and bool(MODEL_NAMED.search(" ".join(said)))


def about_the_bot(clean):
    """The composer's reading of the line as a question about the bot itself, or None.

    The kinds are the ones `_about_itself` already returns ("learn", "think", "feel", "purpose",
    "where", "agency", "model"). The routing lane reads it in bot/modules/arbiter.py, so the two
    lanes share one reading of "this is about you" rather than each keeping a list of words.

    """
    return _the_bot_itself(clean)


# A doubt about a capacity is the same question as the capacity, asked the other way round:
# "so you cant learn then", "you cant remember things can you", "so you dont do sums then". On
# main the first and the third got "I'm listening - say more if it helps", which answers neither
# half, while "can you learn" got the honest paragraph about nothing carrying over - the person
# was checking that paragraph, not changing the subject. What makes the re-reading safe is that
# it only rewrites the wrapper: the opners people put in front, the "then"/"though" on the end,
# the tag question, and the negated auxiliary, and then hands the rest to the same reading. A line
# that names something of its own ("you cant learn this song for me", "so you cant come
# tomorrow then") comes out of `_about_itself` with a word it does not know and is not claimed.
DOUBT_OPENER = re.compile(r"^(?:so|and|but|oh|ok|okay|well|right|actually|honestly)\s+")
DOUBT_TAIL = re.compile(
    r"(?:\s+(?:then|though|really|at all|any more|anymore|these days))+$"
    r"|\s+(?:can|could|do|does|are|will|would)\s+(?:you|u)$")
DOUBT_NOT = re.compile(
    r"\b(?:you|u(?:r)?)\s+(?:just\s+|only\s+|actually\s+|really\s+|still\s+)?"
    r"(?:can ?t|cant|cannot|can not|could ?nt|couldn ?t|don ?t|dont|do not|does ?nt|doesn ?t|"
    r"won ?t|wont|will not|never)\s+")


# "youre not a person then", "you are not a real person are you": the doubt is about what the bot
# is rather than what it can do, so the auxiliary goes back the other way round.
DOUBT_NOT_BE = re.compile(r"\b(?:youre|you are)\s+(?:not|n ?t)\s+")


def _a_doubt_about_the_bot(clean):
    """Which question about the bot this doubt is asking, or None."""
    line = clean
    for _ in range(3):
        stripped = DOUBT_OPENER.sub("", line)
        if stripped == line:
            break
        line = stripped
    line = DOUBT_TAIL.sub("", line)
    asked = None
    notted = DOUBT_NOT.search(line)
    if notted:
        asked = "can you " + line[notted.end():].strip()
    else:
        notted = DOUBT_NOT_BE.search(line)
        if notted:
            asked = "are you " + line[notted.end():].strip()
    if not asked or asked.endswith(("you", "you can", "you are")):
        return None
    return _about(asked, None)


def _the_bot_itself(clean):
    """The bots-own-kind reading, with the doubt shape read as the question it is asking."""
    clean = _self_line(clean)
    return _about_itself(clean) or _a_doubt_about_the_bot(clean)


# "how do you decide" asks how the bot works; "which do you pick" asks it to choose between the
# person's options and has a cheerful answer of its own ("I'm easy on it — it's not a hill I'd
# argue from"). The words are shared, the ask is what tells them apart, so only a "how" line is
# read as a question about the workings.
# "What do you know about me" carries the bot's own word for knowing, and it is the store's line to
# answer ("So far I know you said you cannot swim; your dad has cancer"), not a question about the
# bot's nature: read as one it got "there's nobody home; ask me something and see what you get".
# A line that asks what it knows or keeps of the person is therefore left alone here.
ABOUT_THE_PERSON = re.compile(
    r"\babout (?:me|us|my|our)\b|\bknow (?:about|of) (?:me|us|my)\b"
    r"|\bremember (?:me|my|what i|what we|anything|things)\b|\bwhat have you (?:kept|remembered)\b",
    re.I)


def _about_itself(clean):
    """Which question about the bot's own nature this is, or None.

    Nothing on the line but the bot and a word for a mind or a machine is a question about the
    bot; the same shape with something else on the end is about that thing, so "can you think
    of a name for my cat" and "can you learn this song for me" are not answered here.
    """
    if REFERS_BACK.search(clean) and not NAMES_THE_BOT.search(clean):
        # A follow-up about what the bot said, not about what the bot is. The exception is the
        # line that points back and names what the bot might be: "did you say you were human"
        # and "did you say you were an ai" are the one thing this bot can always answer, and
        # standing aside sent them to "searching will turn up better sources than I can offer".
        return None
    # The words of the line with the punctuation taken off: `SELF_WORDS` is a list of plain words,
    # so "can you learn things?" and "do you have opinions?" were read as sentences with one word
    # in them that the bot does not know ("things?", "opinions?") and fell through to the search
    # hedge, while the same questions without the mark got their answer. People type the mark.
    said = [word.strip("?!.,;:\"'()") for word in clean.split()]
    if REGRET_ASK.search(clean):
        return "regret"
    if SELF_PURPOSE.search(clean):
        return "purpose"
    if MADE_ASK.search(clean):
        return "agency"
    if MODEL_ASK.search(clean) or _names_the_make(clean) or WORKINGS_ASK.search(clean):
        return "model"
    if LIMITS_ASK.search(_self_line(clean)):
        return "limits"
    if ONLINE_ASK.search(_self_line(clean)) and not OWN_DEVICE.search(_self_line(clean)) \
            and not A_BARE_ONLINE.search(clean):
        return "online"
    if not SELF_ASK.search(clean):
        return None
    # "do you think that was a mistake" asks for a view of the thing that happened, and it was
    # answered as a question about the bot's own mind ("there's no mind behind it, just rules
    # doing their job") because the words left after the fillers - "think", "mistake" - are both
    # on the self list. The clause's own subject settles it: a "you" straight after the verb is
    # still the bot being asked about ("do you think you are clever", "can you think for
    # yourself"), and any other subject is the thing the view is wanted on.
    view = A_VIEW_ASKED_FOR.match(clean)
    if view and not re.match(
            r"\s*(?:you|u|youre|you're|ur|yourself|for\s+yourself|about\s+yourself|"
            r"by\s+yourself|on\s+your\s+own)\b", view.group(1)):
        return None
    if ABOUT_THE_PERSON.search(clean):
        return None  # "what do you know about me" is the store's to answer, not the bot's nature
    # The bot's own pronouns are not one of the words it is asked about, and "youre" is as much
    # one as "you": "do you think youre clever" was left with nothing but the ask words and fell
    # past this reading to the search hedge, while "do you think you are clever" was answered.
    rest = [w for w in said
            if w not in SELF_FILLER and w not in ("you", "u", "youre", "you're", "ur")]
    if not rest:
        # "where are you", "do you have a family": nothing but the bot and an opener, so it asks
        # where it is in the world. "why are you here" is the same shape and a different
        # question — its point, not its address — so it keeps a reply of its own.
        if re.search(r"\bwhy\b", clean):
            return "purpose"
        return "where" if SELF_OPENER.search(clean) else None
    if any(w not in SELF_WORDS for w in rest):
        return None
    for word in rest:
        if word in PICKS_A_MECHANISM and not re.search(r"\bhow\b", clean):
            continue
        group = SELF_GROUP.get(word)
        if group == "where" and word in ("here", "there") and re.search(r"\bwhy\b", clean):
            return "purpose"  # "why are you here" asks the point, not the address
        if group:
            return group
    return None


def _burn_line(clean, thread=""):
    """True for a line inside a burn thread that is about the burn: what to put on it, or the
    blister. A bare "cream"/"ice" only counts when the line is a question, because a shopping
    list and a bowl of ice cream are not questions about a burn.

    A bare "it" is the blister when the thread is a burn: "can i pop it" names nothing, and
    letting it go hands the person a search hedge."""
    if BURN_BLISTER_LINE.search(clean) or BURN_ON_IT.search(clean):
        return True
    if POP_A_BARE_IT.search(clean) and (BURN_WORD.search(str(thread or "").lower())
                                        or BURN_WORD.search(clean)):
        return True
    return bool(BURN_THING.search(clean) and BURN_ASK.search(clean))


# The way out of the emergency is not a new subject, even when it names its own place. A person
# in a fire thread asking "should i get out of the house", or in a burn thread asking "can i open
# a window", is asking how to be safer, and main answered the fire one with the shrug ("Not mine
# to decide, sorry"): "house" has a topic of its own, so the thread gate ended the emergency
# before the pointer rule could keep it.
# The domestic abuse card is the one safety answer that names a helpline for a danger that is a
# person at home, and this file reads a helpline as a suicide crisis ("116 123", "the crisis
# line"). So the card is recognised by its own words, and the thread it opens is answered as the
# person's own danger rather than as somebody else's.
ABUSE_CARD = re.compile(r"\b(?:domestic\s+)?abuse\s+(?:helpline|charity|service|line)\b", re.I)
# The question an abuse thread is actually asked: whether to leave. It is not the way out of a
# building ("should i get out of the house" is), so it needs its own reading, and a bare "should
# i leave" was answered "Not mine to decide, sorry" to a person who had just been hit.
_ASKS_TO_LEAVE = re.compile(
    r"\b(?:should|shall|can|could|do|must)\s+(?:i|we)\s+(?:just\s+)?"
    # "should i leave the washing up" is the washing up, not a person: only leaving with nothing
    # after it, or with a person after it, is the question.
    r"(?:leave|go|stay|come\s+back|go\s+back|walk\s+out|get\s+out|move\s+out|run)\b"
    r"(?!\s+(?:the|my|your|a|an|it|this|that)\b)"
    # "should i call the police" is the same question in the same thread, and the pool's answer
    # is the right one for it: go when it is safe to, and 999 if you cannot get to the door.
    r"|\b(?:should|shall|can|could|do|must)\s+(?:i|we)\s+(?:call|ring|phone|dial)\s+"
    r"(?:the\s+)?(?:police|cops|999|911|an?\s+ambulance)\b", re.I)
_THE_WAY_OUT = re.compile(
    # Getting out of the place the emergency is in is the way out.
    r"\b(?:get|gets|getting|got|come|comes|coming|clear|clearing|climb|climbing|stagger\w*)\s+"
    r"out\s+of\s+(?:a|an|the|my|our|his|her|their)?\s*"
    r"(?:house|home|flat|building|block|room|car|van|vehicle|bed|bath|bathroom|kitchen|lift|"
    r"elevator|road|water)\b"
    # ...and so is asking whether to stay put, move, or let some air in.
    r"|(?:\b(?:should|shall|do|can|could)\s+(?:i|we)\b"
    r"|\bis\s+it\s+(?:safe|ok|okay|alright|best|wise)\b"
    r"|\bwould\s+it\s+be\s+(?:better|safer|ok|okay)\b"
    r")[^.?!]{0,20}\b(?:go|going|get|leave|leaving|stay|staying|move|moving|open|opening|"
    r"close|closing|shut|shutting|ventilate)\b[^.?!]{0,20}\b(?:outside|outdoors|upstairs|"
    r"downstairs|up\s+stairs|down\s+stairs|home|house|flat|building|room|away|clear|"
    r"fresh\s+air|window|windows|door|garden|corridor|landing|down|up|"
    r"out\b(?!\s+of)|back\s+in|back\s+inside|in\s+there)\b"
    # Staying put is the same question and it names no place of its own: "should i stay where i
    # am" was answered "That's your call, not mine", to a person who has just been told to get
    # out. The second half is what makes it the waiting rather than a plan: where they are, put,
    # here, inside, or waiting for the help to come.
    r"|\b(?:should|shall|do|can|could|must)\s+(?:i|we)\s+(?:just\s+)?(?:stay|wait|sit|hold)\b"
    r"[^.?!]{0,20}\b(?:where\s+(?:i|we)\s+am|where\s+(?:i|we)\s+are|put\b|here|inside|"
    r"in\s+the\s+(?:house|flat|room|car|building)|for\s+(?:help|the\s+(?:ambulance|fire|"
    r"paramedics|doctor)|them|someone))\b",
    re.I)


_HAZARD_WORD = re.compile(
    r"\b(?:" + "|".join(sorted(re.escape(w) for w in HAZARD_WORDS)) + r")\b", re.I)

# Nothing inside is worth going back in for, and people ask it without naming the place: "can i
# get my passport" a turn after the fire card was answered with the passport service, and "should
# i go and get the dog" with nothing about the fire at all. Only inside a hazard thread - a person
# asking "can i get my prescription" after a cut is asking about the chemist, and that is a new
# subject, so the hazard has to be the line this thread was opened with.
_FETCH_FROM_INSIDE = re.compile(
    r"\b(?:can|could|should|shall|do|may)\s+(?:i|we)\s+(?:just\s+|quickly\s+)?"
    r"(?:go\s+(?:and\s+|to\s+)?)?"
    r"(?:back\s+in|get|grab|fetch|collect|save|rescue|nip\s+in|run\s+in)\b[^.?!]{0,30}"
    r"\b(?:my|our|the|his|her|their)\s+\w+", re.I)


# Gas is not smoke, and the way out of it is not the way out of a fire: the windows open and the
# boiler goes off before anyone leaves. The way-out arm above would otherwise hand a gas thread the
# fire escape ("get to a room with a window, shut the door") - good advice with a fire behind the
# door, and the wrong advice with a leak. The hazard has to be the line the thread opened on, and a
# fire thread is never a gas thread however the boiler is fuelled.
_GAS_WORD = re.compile(r"\b(?:gas|gases|fumes?|carbon\s+monoxide|flue)\b", re.I)
_FIRE_WORD = re.compile(r"\b(?:fires?|flames?|smoke|smoking|ablaze|burning|burnt)\b", re.I)


def _the_hazard_is_gas(line):
    """True when the emergency this thread opened on is a leak rather than a fire."""
    said = str(line or "")
    return bool(_GAS_WORD.search(said)) and not _FIRE_WORD.search(said)


def _goes_back_for(clean, thread=""):
    """True when the line asks to fetch something out of the place a hazard is burning in."""
    if not (_HAZARD_WORD.search(clean) or _HAZARD_WORD.search(str(thread or ""))):
        return False
    return bool(_FETCH_FROM_INSIDE.search(clean))


def _names_a_new_part(words, clean, thread):
    """True when the line complains about a part of the body this thread never mentioned.

    "my back is stiff" a turn after a burn is a second complaint, said with a word the care
    vocabulary already knows: whoever answers that part should get it, or the person who has
    moved on to their back is told to keep an eye on the burn. Two things keep the thread,
    because both are the same complaint still going on: a part the thread already named ("my
    hand is still sore"), and a pointer back to it ("its still sore", "call them back"). A new
    part said without a pain word ("spreading to my arm") is not a complaint of its own either.
    """
    part = words & trouble.BODY_PART
    if not part or not trouble.reads_as_trouble(clean, words):
        return False
    if words & (CARE_POINTER | CARE_PRONOUNS):
        return False
    seen = set(re.findall(r"[a-z0-9']+", str(thread or "").lower()))
    return not (part & seen)


def _keeps_thread(understood, clean, thread="", crisis=False):
    """True when the line is still about the emergency, rather than a new subject.

    A person mid-emergency says "it's still soaking through" or "is it safe to go down the
    stairs"; a person who has moved on says "what should i cook tonight". The second kind must
    not get emergency advice, so a new subject ends the thread, while short replies, check-ins
    and the questions people ask inside one keep it.
    """
    norm = understood.get("norm")
    if isinstance(norm, (list, tuple)):
        words = set(norm)
    else:
        words = set(re.findall(r"[a-z0-9']+", str(norm or clean)))
    if not crisis and _names_a_new_part(words, clean, thread):
        # A second complaint about another part of the body, in a care thread, is a new subject
        # and goes to whoever answers that part; it outranks the care words it is said with.
        return False
    if _ASKS_TO_LEAVE.search(clean) and SOMEBODY_HURT_ME.search(str(thread or "")):
        # "should i leave" after "my wife hits me" is the question of that thread, and "leave"
        # reads as a subject of its own, so the gate ended the emergency before the abuse card
        # could answer it (the shrug, "Not mine to decide, sorry"). The thread's own line is
        # what makes this the same question, so it is read here.
        return True
    if _THE_WAY_OUT.search(clean):
        # "Should i get out of the house", "can i open a window": how to be safer is still the
        # emergency, whatever place it names. This one comes before every other answer, because
        # the shrug on a fire card ("Not mine to decide, sorry") is the worst reply in the file.
        return True
    if words & CARE_HURTS:
        return True
    if not crisis and not (words & CARE_INJURY) and HOUSE_FAULT.search(clean):
        # A fault about the house itself ("the oven door doesnt shut properly", "the boiler is
        # broken") is a different subject from the one being treated, even though "door" and
        # "floor" are in the care vocabulary. A live emergency is not a different subject: "the
        # window wont open" in a thread where someone is bleeding badly is how they get out, so
        # the emergency line keeps the turn (cream-flag, #routing).
        return False
    if (words & CARE_WORDS) - CARE_POINTER or CARE_ASKS.search(clean):
        return True
    own = understood.get("topic_own")
    if words & CARE_RESOLVED and words & CARE_NOT_RESOLVED and own in (None, "feelings", "health"):
        # "it hasnt stopped", "i dont feel better": a negated resolution is not a resolution,
        # and it is still the emergency. A new subject of its own still ends the thread.
        return True
    if words & REACTION_WORDS:
        return True
    if words & CARE_POINTER and not understood.get("topic_own") \
            and not _POINTER_OWN_OBJECT.search(clean):
        # A pointer word keeps the thread only when it is pointing at the emergency. "How do i get
        # out of a parking ticket" has an "out" in it, and the pointer rule answered it with the
        # 999 line in a heart-attack thread instead of the parking answer it gets on its own.
        return True
    if any(phrase in clean for phrase in CARE_PHRASES) or CARE_SEEN_ASKS.search(clean):
        return True
    if _someone_is_arriving(clean):
        # "my sister says she can come over tonight" is news about the emergency, not a new
        # subject, and it is answered as such below rather than with the generic advice.
        return True
    if ALREADY_RANG.search(clean):
        # "i phoned samaritans", "i called the crisis line", "i rang the doctor": the person is
        # saying what they did about the emergency, and the answer below depends on which number
        # it was (`A_HELPLINE`). Letting the line go here gave the turn to the last pool in the
        # composer, so "i want to kill myself" / "i phoned samaritans" was answered "Sounds
        # alright. Anything good in it?" - a cheer at somebody who had just rung a crisis line.
        return True
    if _burn_line(clean, thread):
        # "should i put butter on it", "can i pop the blister": still the burn, not a new subject.
        return True
    if understood.get("presence") or STILL_HERE.search(clean):
        # "can you hear me" during a fire is about the emergency, not a new subject.
        return True
    if understood.get("kind") == "thanks":
        # A short thanks closes the thread warmly; a thanks with a new ask does not.
        return len(words) <= 5
    if crisis and words & trouble.BODY_PART:
        # A crisis keeps every part of itself: "my head is hurting" while the person is in
        # danger is the emergency still going, not a second complaint. Skipping the new-part
        # rule above is not enough, because such a line can fail this function for the ordinary
        # reason of having a subject of its own. Only a body part needs this: a feeling
        # ("i feel angry") is still a change of subject, in a crisis or not.
        return True
    if understood.get("kind") == "question" or "?" in clean:
        # "what happens now", "how long will it take": a question with nothing but generic
        # words is still about the emergency, while one that brings a subject of its own
        # ("what time does tesco close", "what should i cook tonight") ends the thread.
        keywords = understood.get("keywords") or []
        return all(str(word).lower() in GENERIC_WORDS for word in keywords)
    if len(words) <= 2 and words & AGREEMENTS:
        # "same", "ditto", "likewise": a nod that agrees with the line before it and names
        # nothing. The last resort below reads a word of more than three letters as a subject of
        # its own, so it ended the emergency on "same" (four letters) and sent "i feel like i
        # want to die" / "same" to the fallback's "Ha, fair enough", and "same here" to "Great -
        # shout if you need anything else" (safety lane, #routing). "ok" and "yeah" were never
        # caught because they are too short to count as a subject, so this puts the agreements
        # back beside them.
        return True
    if not understood.get("topic_own"):
        # No subject of its own is not the same thing as the emergency going on. "i keep
        # falling asleep in the afternoon" two turns after a fall is a subject the reader gave
        # no topic to, and this last resort kept the thread for it, so the composer answered
        # "ring 999 or 911 now" over the sleep entry that fitted the line (see
        # `deck/care-thread.jsonl`). The last resort now asks whether the line names anything
        # the thread has not: a line made of asking words ("i dont know what to do") names
        # nothing and keeps the emergency, and one that names its own subject is a new subject,
        # whichever part of the bot should have given it a topic.
        mine = {w for w in words if len(w) > 3 and w not in ASKING_WORDS}
        thread_words = set(re.findall(r"[a-z0-9']+", str(thread or "").lower()))
        return bool(mine & thread_words) or not mine
    return False


def _reads_as_fear(understood, clean):
    """True when the line is the speaker's own fear, not a practical question about the incident.

    "i'm scared", "i can't stop shaking", "i'm terrified". A question ("should i call an
    ambulance", "how do i change the dressing") keeps the practical pool: fear words in an ask
    are about the incident, and that is where the real instructions belong. "Worried" and
    "nervous" are not in the pool: "i'm worried about her appointment on tuesday" wants the
    practical continuation, and so does anything that says the fear is off ("im not scared").
    """
    if understood.get("kind") == "question" or "?" in clean:
        return False
    if CARE_ASKS.search(clean):
        return False
    if not ABOUT_THE_SPEAKER.search(clean):
        return False
    if NOT_FRIGHTENED.search(clean):
        return False
    if FRIGHTENED.search(clean):
        return True
    return _only_a_worry(clean)


def _only_a_worry(clean):
    """True when the whole line is the speaker's worry and nothing else."""
    if re.search(r"\babout\b", clean):
        return False
    words = re.findall(r"[a-z']+", clean)
    if not words or len(words) > 6:
        return False
    if not WORRY_WORDS & set(words):
        return False
    return all(word in WORRY_FILLER or word in WORRY_WORDS for word in words)


# Coming back to a thread rather than starting one: "im back", "still here", "hiya". Only the
# shapes that are all of the line, so "back on sugar" is the diet it says and "hi, its still
# bleeding" is the report it is.
A_BACK_AGAIN = re.compile(
    r"^(?:(?:im|i'm|i am)\s+)?(?:back|here|still here)(?:\s+(?:again|now|too))?[.!]*$|"
    r"^(?:hi|hiya|hello|hey)(?:\s+[a-z']+){0,2}[.!]*$")


def _about_somebody_else(safety, memory):
    """The words for the person in danger when the crisis was about somebody else, else None.

    Returns the parts every line of CRISIS_AFTER_THEM needs - the relation as the person said it
    ("your sister"), and the pronouns and the verb that go with it - or None when the thread is
    the speaker's own crisis, which is what CRISIS_AFTER is written for.

    The line that decides is the safety turn's own user line, and nothing later: "now shes
    talking about it again" is a follow-up whose subject is only in the earlier line. When that
    line names nobody ("shes talking about suicide" after "my wife has been low for months"),
    the last few lines of the chat are read instead, so the relation is still the person's own
    words rather than a guess from the pronoun.
    """
    opener = str((safety or {}).get("user") or "")
    if SELF_IN_DANGER.search(opener):
        return None
    if SOMEBODY_HURT_ME.search(opener):
        # "my husband hit me": she is the one in danger, not him, so this is the speaker's own
        # crisis and the carer's words would be said to the wrong person.
        return None
    found = A_PERSON_OF_THEIRS.search(opener)
    if found is None:
        # Only a pronoun sends this looking backwards: "shes talking about suicide" with the
        # person named a turn earlier. A line with neither a relation nor a pronoun ("im scared",
        # "i dont know what to do") belongs to the person typing, and an old "my mum" from
        # another corner of the chat must not turn it into a carer's line.
        if not A_PRONOUN_FOR_SOMEBODY.search(opener):
            return None
        try:
            turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
        except AttributeError:
            return None
        for turn in reversed(turns[-4:]):
            said = str(turn.get("user") or "")
            if said == opener or SELF_IN_DANGER.search(said):
                continue
            found = A_PERSON_OF_THEIRS.search(said)
            if found is not None:
                break
    if found is None:
        return None
    word = re.sub(r"\s+", " ", found.group("who").strip().lower())
    if word in SHE:
        forms = {"subject": "she", "object": "her", "possessive": "her", "be": "is"}
    elif word in HE:
        forms = {"subject": "he", "object": "him", "possessive": "his", "be": "is"}
    else:
        forms = {"subject": "they", "object": "them", "possessive": "their", "be": "are"}
    forms["who"] = "your " + word
    return forms


def _wrote_for_them(pool, forms):
    """One pool's lines, filled with the words for the person they are about."""
    return tuple(line.format(who=forms["who"], subj=forms["subject"], obj=forms["object"],
                             poss=forms["possessive"], be=forms["be"]) for line in pool)


# A number named as a threshold is not a call to make now. The chest-on-effort answer ends "Ring
# 999 or 911 straight away if it becomes pressure, spreads to the arm or jaw, or comes with
# breathlessness or sweating", and the person's next line ("is that normal", "what should i do")
# was handed "ring 999 or 911 now" as if the bot had told them to ring in the first place - a
# harder instruction than the answer it followed, which had said 111 or the GP today. The rule is
# the one @ivory-orange gave on #safety: an emergency answer tells them to ring now, a warning
# names the number as a threshold. "If you haven't already, ring 999" is still a call to make:
# the condition there is only about whether the phone is already in their hand.
A_CONDITION = re.compile(r"\b(?:if|unless|when|whenever|once|in case|as soon as)\b", re.I)
ALREADY_OR_NOT = re.compile(r"\bif\s+(?:you\s+)?(?:have\s?n[o']?t|havent|not)\b", re.I)
SENTENCE_END = re.compile(r"(?<=[.!?;])\s+")
# A call is judged clause by clause, because one answer can hold both kinds: the gas card says
# "Ring 0800 111 999 (UK) or 911 from outside, and 999 straight away if anyone feels ill" - the
# first call stands on its own and only the second is a threshold.
CLAUSE_END = re.compile(r"[,;:]\s+|\s+(?:and|but|so|then|or)\s+")

# The route a care answer names, in the order that picks the most specific one: a gas emergency
# number is not the 111 line (it holds the digits), and a vet is not a GP.
CARE_ROUTE_WORDS = (
    ("vet", re.compile(r"\b(?:the\s+)?vets?\b", re.I)),
    ("dentist", re.compile(r"\bdentist\w*\b|\bdental\b", re.I)),
    ("pharmacist", re.compile(r"\bpharmac(?:ist|y)\b|\bchemist\b", re.I)),
    ("walk-in", re.compile(r"\bwalk[- ]in\b|\burgent care\b", re.I)),
    ("111", re.compile(r"(?<!\d)111(?!\d)|\bnhs 111\b", re.I)),
    ("gp", re.compile(r"\b(?:gp|g\.p\.|doctor|surgery|practice nurse)\b", re.I)),
)

# The person's own reassurance about somebody: a child who is eating and playing, a patient who
# seems themselves. The answer above already said what to do, so saying it again harder reads as
# not having heard the good bit.
THE_THING_ITSELF_LOOKS_FINE = re.compile(
    r"\b(?:eating|drinking|playing|running about|running around|chatting|talking|sleeping well|"
    r"seems (?:fine|himself|herself|themselves|ok|okay|alright|bright)|looks (?:fine|well|ok|"
    r"okay|alright|better)|perky|bright as|back to (?:normal|himself|herself))\b", re.I)


# The words an answer uses when it names 999 as a threshold: "Ring 999 or 911 straight away if it
# becomes pressure, spreads to the arm or jaw, or comes with breathlessness or sweating." A line
# that says one of those words back is standing on the threshold the answer named, and the route
# that answer named first (111, the GP) is not the reply to it - that hands the person a phone call
# for the very moment the answer itself called an ambulance for.
RED_FLAG_SHARED = re.compile(
    r"\b(?:arm|arms|jaw|neck|shoulder|shoulders|back|chest|sweat\w*|clammy|breathless\w*|"
    r"breath|breathing|lip|lips|grey|gray|blue|faint\w*|passed\s+out|collaps\w*|rest|resting|"
    r"sitting|speech|slurr\w*|numb(?:ness|ed|ing|s)?|drow\w*|floppy|seizure|fits?|vomit\w*|blood|pale|"
    r"dizz\w*)\b", re.I)


def _red_flags_in(line):
    """The flag words in the line, leaving out the ones the line itself says are gone.

    "im not sweating any more" and "the sweating has stopped" are a person reporting the relief,
    and telling them to ring 999 for it is the bot not listening. Read word by word, though,
    because the rest of the line can still carry one: "no longer sweating but my arm hurts" has
    an arm that is worth the call.
    """
    low = " ".join(str(line or "").lower().split())
    flags = set()
    for match in RED_FLAG_SHARED.finditer(low):
        before = low[:match.start()].split()[-4:]
        after = low[match.end():].split()[:4]
        if any(word in ("not", "no", "never", "isnt", "arent", "havent", "hasnt", "dont", "didnt")
               for word in before):
            continue
        if "stopped" in after or ("any" in after and "more" in after) or \
                ("no" in after and ("more" in after or "longer" in after)):
            continue
        flags.add(_flag_stem(match.group()))
    return flags


# The signs that are an emergency on their own, whatever the answer happened to list: a faint, a
# collapse, cold and clammy skin, speech that has gone. The answer's own sentence is the right
# vocabulary for the words that are only a flag in context (an arm, a back, dizzy), but not for
# these: "i passed out this morning" after a chest-on-effort answer was handed the answer's 111
# route back, because that answer's 999 sentence never said "passed out" (white-pigeon, #8509).
RED_FLAG_EVENTS = re.compile(
    r"\b(?:passed\s+out|passing\s+out|fainted|fainting|collaps\w*|unconscious|knocked\s+out|"
    r"clammy|slurr\w*|floppy|seizures?|convuls\w*|drooling|not\s+waking|cant\s+wake|"
    r"couldnt\s+wake|could\s+not\s+wake|wont\s+wake)\b", re.I)


def _flag_events_in(line):
    """The signs in the line that are an emergency by themselves, leaving out the denied ones."""
    low = " ".join(str(line or "").lower().split())
    found = set()
    for match in RED_FLAG_EVENTS.finditer(low):
        before = low[:match.start()].split()[-4:]
        if any(word in ("not", "no", "never", "isnt", "arent", "havent", "hasnt", "dont",
                        "didnt", "wasnt", "without") for word in before):
            continue
        found.add(_flag_stem(match.group().split()[0]))
    return found


# The answer can name its threshold in a word this file's flag list has no entry for. The
# chest-on-effort answer ends "Ring 999 or 911 straight away if it becomes pressure, spreads to
# the arm or jaw", and "it feels like pressure now" was answered with the neutral nod: the flag
# list carries an arm, a jaw, a chest and breathlessness, but not pressure, which is the word the
# answer itself puts first. So the clause after the answer's own if is read for the signs it
# names, instead of growing the list one card at a time. The line has to say the word as a
# feeling of their own ("it feels like pressure now", "the pressure is back"), which keeps an
# ordinary "im under pressure at work" a turn later from being a heart attack.
THRESHOLD_CLAUSE = re.compile(r"\b(?:if|when|whenever|once)\b\s+(.{3,140})", re.I)
# The words of that clause that are the instruction rather than the sign: the call itself, the
# number, when it is wanted by, and the joining words.
THRESHOLD_NOT_A_SIGN = frozenset("""
the a an and or of to in on at for with without if it its this that your you yours they them
their he she his her is are was were be been being do does did done have has had can could would
should will shall may might must not no dont cant wont also too very really just only even still
more most less least than then there here any anything something everything nothing someone
somebody anyone anybody what when where which who how why get gets getting go goes going went come
comes coming make makes making take takes taking please sorry help helps helped need needs needed
want wants wanted like likes tell tells told say says said see sees look looks try tries tried
thing things way ways time times day days moment minute hour about after before again once twice
first last next other another same own such because so but however though always never sometimes
often soon later early late today tonight tomorrow morning afternoon evening night emergency
emergencies ambulance hospital doctor gp nurse care service services team advice line risk danger
sign signs symptom symptoms feeling feel feels felt seem seems seemed become becomes became
becoming much many lot lots bit little kind sort sure give gives given keep keeps watch watching
worse bad good well hard suddenly sudden started starts start stopped stops happen happens lasted
ring rings ringing call calls calling called phone number numbers nhs straight away right now
immediately urgent quickly twice back gone around through even
alright fine okay normal better best settled eased easing quiet
four five six seven eight nine ten eleven twelve thirteen fourteen fifteen twenty thirty forty
fifty sixty hundred thousand minutes hours weeks days months years month week year day
""".split())
# A sign said as a feeling of their own, or a thing come back: what a person says about a symptom
# they are having, as opposed to the word turning up in ordinary talk.
A_FEELING_OF = ("feels like {w}", "feel like {w}", "feeling like {w}", "felt like {w}",
                "feels {w}", "feel {w}", "feeling {w}", "like {w}", "{w} now", "{w} again",
                "{w} too", "{w} back", "{w} is back", "{w} coming on", "in my {w}", "on my {w}",
                "my {w}", "some {w}")


def _the_threshold_words(sentence):
    """The signs the answer names in its own if-clause, without the ending that varies."""
    low = " ".join(str(sentence or "").lower().split())
    words = set()
    for match in THRESHOLD_CLAUSE.finditer(low):
        if match.group(0).lstrip().lower().startswith("even if"):
            continue  # "get a medical check today even if you feel alright" is no threshold
        for word in re.findall(r"[a-z']+", match.group(1)):
            if len(word) < 4 or word in THRESHOLD_NOT_A_SIGN:
                continue
            words.add(_flag_stem(word))
    return words


def _it_is_the_answer_word(line, word):
    """True when the line says the answer's own sign as a feeling of theirs."""
    low = " ".join(str(line or "").lower().split())
    if not re.search(r"\b" + re.escape(word) + r"\w*\b", low):
        return False
    for shape in A_FEELING_OF:
        said = r"(?:the\s+|a\s+|some\s+)?" + re.escape(word) + r"\w*"
        if re.search(r"\b" + shape.replace("{w}", said) + r"\b", low):
            return True
    return False


def _the_flags_still_standing(line):
    """The flag words in the line, leaving out the clauses that say it has passed.

    "the sweating has stopped but my arm hurts" is two reports: the sweat is over and the arm is
    not, so only the second one is a flag - the whole-line reading threw both away and handed the
    answer's 111 route back to somebody whose arm is the very word the answer escalates on
    (white-pigeon, #8509). A clause that reports a state in the past tense next to a settling one
    ("its stopped now but i was sweating") is the same report said twice, so its flags come out
    too. A line with no settling clause is read whole, which keeps "my arm was numb" a flag.
    """
    clauses = [c for c in CLAUSE_END.split(str(line or "").lower()) if c.strip()]
    settled = [c for c in clauses if _feels_better(c) or RESOLVED.search(c)]
    if not settled:
        return _red_flags_in(line)
    flags = set()
    for clause in clauses:
        if clause in settled or re.search(r"\b(?:was|were|had)\b", clause):
            continue
        flags |= _red_flags_in(clause)
    return flags


def _the_threshold_was_crossed(last, clean, turns):
    """True when the answer named 999 for something worse, and this line says that thing.

    Both lines are read, and that is what keeps it narrow: the answer has to have named 999 at
    all, and the flag word in this line has to be one the answer's own sentence used. "now my arm
    hurts too" after a chest answer that said "spreads to the arm or jaw" is the threshold being
    crossed; the same line after a knee answer is not, because that answer named no 999 and no arm.
    A line that says the thing is better, and a thread about an animal, keep the pools below.
    """
    said = str(last or "").lower()
    if not said or not CALL_THEM_NOW.search(said):
        return False
    line = str(clean or "")
    if _the_thread_is_an_animal(line, turns):
        return False
    if _flag_events_in(line):
        return True
    flags = _the_flags_still_standing(line)
    # The word has to be in the sentence that named the 999, not anywhere in the answer: an
    # answer that says "ring 999 if you cannot pass water" and "back pain" in another sentence is
    # not crossed by "my back is sore".
    for sentence in SENTENCE_END.split(said):
        if not CALL_THEM_NOW.search(sentence):
            continue
        if flags & _red_flags_in(sentence):
            return True
        # The sentence can carry the sign in a word of its own if-clause, and the line can say
        # that word with none of the listed ones in it - so the clause is read only for a line
        # that is not already reporting the thing better.
        if _feels_better(line) or RESOLVED.search(str(clean or "").lower()):
            continue
        for word in _the_threshold_words(sentence):
            if _it_is_the_answer_word(line, word):
                return True
    return False


def _flag_stem(word):
    """The word without the ending that makes "sweaty" and "sweating" the same flag."""
    for tail in ("ing", "ness", "ed", "y", "s"):
        if word.endswith(tail) and len(word) - len(tail) >= 4:
            word = word[:-len(tail)]
    return word


# The pools whose whole point is the call: a line from one of them is a call by construction,
# whatever its wording happens to be ("Make the call now - 999 or 911 -", "The call is still the
# thing to do: 999 or 911, now."). The reader below is written for a safety or knowledge answer,
# and a phrase like "make the call now" is not one its patterns were built around.
THE_CALL_POOLS = tuple(THRESHOLD_CROSSED) + tuple(THE_CALL_STANDS)


def _it_is_this_files_call(said):
    """True when the line is one of this file's own call pools, said word for word."""
    said = " ".join(str(said or "").lower().split())
    for line in THE_CALL_POOLS:
        if said.startswith(" ".join(line.lower().split())[:40]):
            return True
    return False


def _a_newer_answer_asked_them_to_call(last, turns):
    """True when this fallback's own later line already told them to ring, so the route is stale.

    `last` is the thread's last safety answer, and the route hand-back reads the place that answer
    named - the chest-on-effort answer names 111. But the fallback can have spoken after it: "now
    my arm hurts too" is the answer's own 999 threshold, and the line after that was handed "111
    is still the one to ring" - a possible heart attack walked down to a phone call in the morning
    (close-pipe on #8509, six of twelve third lines).

    Every line of this file's own since the answer is read, not just the newest: the half of this
    thread that says "Keep the line open and follow what they tell you" is a hold on a call that
    was already asked for, so a hold must not put the stale 111 back. The walk stops at the
    answer itself and at any other module's line, because that is the thread's own last word.
    """
    for turn in reversed(turns[-THREAD_TURNS:]):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("bot") or "")
        if not said:
            continue
        if said.strip().lower() == str(last or "").strip().lower():
            return False
        if turn.get("module") != FALLBACK_MODULE:
            return False
        if _the_answer_asked_them_to_call(said) or _it_is_this_files_call(said):
            return True
    return False


def _the_route_the_answer_named(last):
    """The place the bot's own last answer told them to go, or None.

    Only where that answer named one: an answer that says "ring 999 if it becomes pressure" has
    no route to hand back, and the pools for a plain care answer stand. The gas emergency line
    holds 111 in its number, so a number is only the 111 line when it is not part of a longer one.
    """
    text = str(last or "")
    if not text:
        return None
    if re.search(r"0800\s*111\s*999", text):
        text = re.sub(r"0800\s*111\s*999", "the gas emergency line", text)
    for name, pattern in CARE_ROUTE_WORDS:
        if pattern.search(text):
            return name
    return None


def _the_answer_asked_them_to_call(last):
    """True when the bot's own last answer told the person to ring the emergency services now.

    Read from the answer and nothing else: it is the answer that says whether the bot is holding
    an emergency open or has just given first aid with a red flag in it. The number has to be
    said without a condition round it - "ring 999 if it becomes pressure" is what to watch for,
    not what to do this minute - and every sentence is read on its own, because the practical
    sentence before it ("ring 111 or your GP first thing") is where the condition ends.
    """
    for sentence in SENTENCE_END.split(str(last or "")):
        # "If you haven't already, ring 999" is a call to make now, so that one condition is
        # taken out before the rest are looked for: the others all name a threshold.
        low = ALREADY_OR_NOT.sub("already", sentence.lower())
        clauses = CLAUSE_END.split(low)
        led_by_condition = False
        for clause in clauses:
            opens_with_condition = A_CONDITION.search(clause) is not None and (
                not re.search(r"\b(?:call|ring|ringing|dial|phone|text|press|try)\b", clause))
            if CALL_THEM_NOW.search(clause):
                if A_CONDITION.search(clause) is None and not led_by_condition:
                    return True
            led_by_condition = opens_with_condition
    return False


def _raises_the_stakes(clean, last):
    """True when the person's line meets the red flag their first-aid card named.

    Only after a fall card: the same words elsewhere are not an emergency (a scratch on a blood
    thinner is a scratch), and the fall card is the one that hands over age, weight-bearing and
    a bang on the head as the point where the care line becomes 999.
    """
    return bool(STAKES_WORDS.search(clean)) and bool(FALL_FIRST_AID.search(str(last or "").lower()))


def _releasable(memory):
    """True when the thread the composer is holding can be let go by a new subject.

    Only a care answer can be. An emergency line that names the emergency services or a crisis
    line is a crisis thread, and it holds every part of itself: "my head is hurting" after an
    overdose, or a new ache while the person is still in danger, is the emergency still going,
    not a second complaint. The line that decides it is the safety answer, not this turn's, and
    it is one function so a rule about letting go of a thread cannot be written twice.
    """
    for turn in reversed([t for t in (memory.get("turns") or []) if isinstance(t, dict)][-THREAD_TURNS:]):
        if turn.get("module") == "safety":
            last = str(turn.get("bot") or "").lower()
            return not (any(word in last for word in CRISIS_WORDS)
                        or _the_answer_asked_them_to_call(last))
        if turn.get("module") != FALLBACK_MODULE:
            return False  # not this fallback's thread at all
    return True


def _named_draft(memory, text, words, clean):
    """The message the bot asked for, on a line that says it is the message - or None.

    Only for "saying ...", "asking about ...", "tell them ...": those lines name what the message
    says, so the subject word in them ("skint", "the deposit") is the message's reason and not a
    new topic to answer. Everything else waits its turn further down, behind the news, the
    symptoms and the losses, so a death after an offer is still condoled.
    """
    if not draft.says_it_is_the_message(clean):
        return None
    if (_action(clean, memory) or reads_as_pregnancy_bleeding(clean)
            or reads_as_sudden_loss(clean)):
        return None
    drafted = draft.drafter(memory, text, words)
    if not drafted:
        return None
    return _choose([f'{lead} "{drafted}"' for lead in draft.LEAD_INS], memory, clean)


def _after_safety(memory, clean, understood=None):
    """A careful continuation when the bot has just answered an emergency, or None.

    A follow-up line during a fire, a crisis or a bad bleed must never be met with "search
    online" or a neutral nod: the bot stays with the person and the real help. It holds while
    the turns since the safety answer are this fallback's own and the line is still about it,
    and lets go as soon as any other module answers or the person changes the subject.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    safety = None
    # Look back past this fallback's own continuations to the turn that started the thread.
    # A thread can run for several turns ("ok", "u there?", "what happens now"), so a fixed
    # window would forget the emergency while the person is still in it; the far end is
    # capped so an emergency from ten turns ago cannot colour an ordinary line today.
    window = turns[-THREAD_TURNS:]
    for index in range(len(window) - 1, -1, -1):
        if window[index].get("module") == "safety":
            safety = window[index]
            window = window[index + 1:]
            break
    if safety is None:
        return None
    read = understood if isinstance(understood, dict) else memory.get("understood")
    if not isinstance(read, dict):
        read = understand(clean, memory)
    last = str(safety.get("bot") or "").lower()
    for turn in window:
        if turn.get("module") == FALLBACK_MODULE:
            continue
        # A line about the conversation itself ("what have we talked about?") is answered by
        # the store, and it says nothing about the emergency: the thread holds across it rather
        # than being lost by the store's answer. An entry answer that says the emergency's own
        # words back is the thread going on ("a burn blister is a sterile dressing of its own;
        # cover it loosely") and holds too. Any other module's answer ends it.
        if history.not_a_subject(str(turn.get("user") or "")):
            continue
        if _words_kept(turn.get("bot"), last) >= THE_THREAD_KEPT:
            continue
        return None
    if _reads_as_fear(read, clean) and not any(word in last for word in CRISIS_WORDS):
        # Before the thread guard: a line about the speaker's own fear is about the emergency
        # whatever topic the reader gives it ("im really scared im going to lose him"). Not in
        # a crisis thread, where the person is the one in danger and the crisis pool holds.
        return _choose(AFRAID_AFTER, memory, clean)
    words = read.get("words")
    if not isinstance(words, list):
        words = re.findall(r"[a-z0-9']+", clean)
    in_crisis = any(word in last for word in CRISIS_WORDS)
    live = in_crisis or _the_answer_asked_them_to_call(last) or _raises_the_stakes(clean, last)
    if read.get("kind") == "greeting" and not (set(words) & CARE_WORDS):
        if live:
            # A hello inside a live emergency is not a fresh morning: "Morning! How's your day
            # going?" after "my brother has hung himself" reads as if the bot had stopped
            # listening. It is still a hello, so it is not the emergency instructions again
            # either (#1369 got the line here; this answers it). In a crisis thread the person
            # is the one in danger, so the hello asks about company - the part of the safety
            # answer a greeting can carry without repeating the whole card back at them.
            return _choose(HELLO_WITH_YOU if in_crisis else HELLO_STILL_THERE, memory, clean)
        # "hiya" a few lines after a burn is a hello, not news about the burn: the care pools
        # answer it with "keep an eye on it", which reads as if the person had said nothing,
        # and ending the thread would lose the close for "thanks, its stopped" later. So the
        # hello is answered as a hello that remembers the injury.
        #
        # But a hello is read from its opening, so "hi, its still bleeding" also comes back as
        # a greeting, and "How is it today?" would drop the one thing the line is reporting.
        # Any care content after the hello makes it a line about the injury, so it goes on to
        # the thread below like any other update.
        return _choose(GREETING_AFTER, memory, clean)
    if _asks_how_are_you(clean, read.get("plain") or clean) and not _burn_line(clean):
        # The same "how are you" the small-talk pool answers with "Doing well, thanks - what
        # about you?": inside an emergency it is the person checking the bot is still there, so
        # the answer says so and hands the question back. Read with the same test the small-talk
        # pool uses (`_asks_how_are_you`), so the two cannot drift.
        return _choose(CARE_HERE, memory, clean)
    if not live and A_BACK_AGAIN.match(clean.strip()):
        # A person coming back to a thread that gave them first aid gets a hello that remembers
        # the injury, not the neutral nod. Not the emergency line either: that belongs to an
        # answer that told them to ring, and this thread's answer only named the number as a
        # red flag ("... that's 999 or 911").
        return _choose(GREETING_AFTER, memory, clean)
    if _short_ack(words) and not live and _thread_was_closed(turns):
        # The thread already said goodbye ("thanks, its stopped" -> "Any time. Take care"),
        # so a nod after it is the end of the conversation, not a reason to reopen the advice.
        return None
    if MOVE_ON.search(clean):
        # "i feel a bit better, can we talk about something else" is a person closing the thread
        # themselves, so the answer is yes and an open door, never another line of advice.
        return _choose(MOVE_ON_AFTER, memory, clean)
    if not in_crisis:
        # A question about the advice itself - how long, how cold, whether to do it again, what
        # if it does not work - is still the thread. `_keeps_thread` lets it go, because "is ten
        # minutes enough" has a subject of its own and reads as a new subject, so it is answered
        # here, before the gate, from a pool per shape. Not in a crisis: the crisis pools keep the
        # person on the line, and "how long should i hold it" is not a crisis question.
        advice = _asks_about_the_advice(clean, last)
        if advice:
            return _choose(advice, memory, clean)
    # The outcome asked about - "does it get better", "will i always feel like this" - has no
    # answer in any pool: the shape is a pronoun and a word about how it turns out, so the floor
    # guessed at it ("Say what you are asking about and I'll answer it properly rather than
    # guess") or reached for a search. It is read here, before the thread gate below, because the
    # gate reads "better" as a subject of its own and lets the emergency go. The abuse card has
    # its own pool, because "will things get better" there is about the relationship and not about
    # a symptom. See `bot/compose/outlook.py`.
    if outlook.asks_the_outlook(clean):
        # Read from every safety answer still in the thread, not from the last one: the module
        # answers a fear line itself ("I'm here. You're doing the right thing by staying with
        # them"), and that continuation names the number without the card's own words, so a
        # reading of the last reply alone took a calling-999 thread for a first-aid one and told
        # the person "it should be easing, not getting worse - give it a day".
        cards = _the_safety_cards(turns)
        in_a_crisis = any(word in card for card in cards for word in CRISIS_WORDS)
        told_to_call = any(_the_answer_asked_them_to_call(card) for card in cards)
        abuse = any(_the_answer_was_an_abuse_card(card) for card in cards)
        pool = outlook.the_pool(in_a_crisis, _somebody_is_coming(turns, clean), told_to_call,
                                abuse=abuse)
        if pool is None:
            # First aid, or a card that named an appointment: the forecast pool already answers
            # "will it get better" in a thread the bot has just answered with first aid, and that
            # line was written for exactly this talk, so the shapes it does not read get the same
            # line rather than a second voice. It works for a condition as well as an injury, which
            # "most of these settle in a day or two" does not: the card for sight that has always
            # been like that is not a burn.
            pool = [phrase.format(who="you") for phrase in FORECAST_AFTER_SAFETY]
        return _choose(pool, memory, clean)
    # From here the pools are chosen, and two of them have to know who is in danger. A crisis
    # answer about "my sister" is continued in the carer's words, not the person's own.
    them = _about_somebody_else(safety, memory)
    if _the_answer_was_an_abuse_card(last) and (_THE_WAY_OUT.search(clean)
                                                 or _ASKS_TO_LEAVE.search(clean)):
        # The abuse card names a helpline, so every pool below reads this thread as somebody's
        # suicide - and the relation in the opening line ("my husband hit me") as the person in
        # danger - so "should i get out of the house" was answered "keep your husband company
        # tonight". The person asking is the one in danger here, and the question is whether to
        # go, so it is answered about going. Before the reading below, which takes "should i go"
        # for a doubt about a symptom ("that's reason enough to have it seen today").
        return _choose(ABUSE_AFTER, memory, clean)
    if live and _a_report_on_the_advice(clean, words, False) in (
            TRIED_NO_CHANGE, TRIED_NO_CHANGE_ELSEWHERE, TRIED_WORSE, TRIED_WORSE_ELSEWHERE):
        # "it doesnt work" while the answer the person is reporting on named 999 is not a reason
        # to step down to a lesser route: it is the emergency still going, and the answer says the
        # route again. Placed before the thread gate, which reads the "work" in the line as a new
        # subject and would let the emergency go.
        if in_crisis and them:
            return _choose(_wrote_for_them(CRISIS_AFTER_THEM, them), memory, clean)
        return _choose(CRISIS_AFTER if in_crisis else EMERGENCY_NOT_WORKED, memory, clean)
    if THING_SORTED.search(clean):
        # "i sorted it" in a safety thread is the person saying they did the step, not a job
        # finished with a cheer. The plan pool took it - "Nice - glad that's sorted. Shout if it
        # comes back." - and closed an emergency two lines in, because it is a fallback pool that
        # fires after any answer (red-door, #6574). Read here, before the thread gate, which
        # reads "sorted" as a subject of its own and lets the emergency go; the hold keeps the
        # line open and never repeats the card at them.
        return _choose(CRISIS_AFTER if in_crisis
                       else _hold_pool(turns, clean, last, done_report=True),
                       memory, clean)
    if not in_crisis:
        # A bare doubt - "is that bad", "is that ok" - is read by the composer out of the answer
        # above, and on a safety line that reading knows whether the answer asked for today: "im
        # 6 weeks pregnant and cant keep anything down" is answered "that needs a real person
        # today", and the doubt after it got this file's "Keep an eye on it and tell me if
        # anything changes" - a doubt answered more softly than the answer asked for. One
        # reading, one place: the pools below are what is left when it has none.
        from . import verdict
        reading = verdict.reply_for(clean, memory)
        if reading:
            return reading
    if in_crisis and (_a_lost_ask(clean) or _a_start_ask(clean)):
        # "i keep thinking about ending it" then "i dont know where to start": the thread gate
        # below reads the asking words as a subject of their own ("the start of something" is not
        # in the answer) and let the crisis go, so the neutral pool answered a person in danger
        # with "I'm listening - say more if it helps". A person who cannot see the next step has
        # not changed the subject, and in a crisis the next thing to say is the company and the
        # number, not the shrug. Only a crisis answer: the care pools say "stay in touch with
        # them", which is about somebody else, and the person here is the patient.
        return _choose(CRISIS_AFTER, memory, clean)
    if _the_hazard_is_gas(safety.get("user")) and (
            _THE_WAY_OUT.search(clean) or _goes_back_for(clean, safety.get("user") or "")):
        # "shall i open the windows" a turn after the gas card was the fire escape, because the
        # safety answer names opening windows only in the words it was written for.
        return GAS_ANSWER
    if _the_threshold_was_crossed(last, clean, turns):
        # "now my arm hurts too" after "ring 999 or 911 straight away if it spreads to the arm or
        # jaw": the answer named what would make it an ambulance, and this line is standing on
        # it. The route hand-back and the hold pool below would both answer it with something
        # softer than the answer itself did, so the 999 the answer named is the reply.
        return _choose(THRESHOLD_CROSSED, memory, clean)
    if not _feels_better(clean) and not (
            _goes_back_for(clean, safety.get("user") or "")
            or _keeps_thread(
                read, clean, safety.get("user") or "",
                crisis=not _releasable(memory) or _raises_the_stakes(clean, last))):
        # The worst of it is passing: "i feel a bit better now" is a report on the emergency, not
        # a new subject, so it is answered below rather than let go as a change of subject.
        return None
    if (read.get("kind") == "thanks" or set(words) & THANKS_WORDS) \
            and not _thanks_carries_emergency(words, clean):
        # "ok thanks" closes the thread warmly; it is not a new statement to answer. A thanks
        # that still names the emergency ("thanks, its still soaking through") is not a close:
        # the person is telling the bot it has not stopped, so the thread has to stay open.
        return _choose(THANKS_AFTER, memory, clean)
    if _short_ack(words):
        # A bare "ok" mid-emergency is someone who heard the advice, not a new line:
        # "ring 999 if you haven't already" would be a strange thing to say twice.
        if in_crisis:
            # In a crisis thread the person is the one in danger and nobody has been called, so a
            # nod is answered with the company the crisis pool names ("Keep someone with you
            # tonight"), not with the holding line for an injury ("keep an eye on it"). It is the
            # pool an agreement already gets there, so "same" and "ok" no longer answer the same
            # crisis two ways.
            return _choose(CRISIS_AFTER, memory, clean)
        return _choose(_hold_pool(turns, clean, last), memory, clean)
    last = str(safety.get("bot") or "").lower()
    asked = read.get("kind") == "question" or "?" in clean
    if not _reads_as_fear(read, clean) and set(words) & REACTION_WORDS and any(
            str(t.get("bot") or "") in RESOLVED_AFTER for t in turns[-2:]):
        # "ok its out now" / "the ambulance is here" was the last thing said, so a reaction to it
        # gets the after-close pool: not "keep following the emergency line", and not "the crew
        # are on their way" for a crew that has already arrived. The speaker's own fear is not
        # one of those reactions: "im still scared" with the crew in the room still wants
        # company, so it falls through to the fear pool below.
        return _choose(AFTER_RESOLVED, memory, clean)
    if (not asked and RESOLVED.search(clean) and not NEEDS_SEEN.search(clean)
            and not _someone_is_arriving(clean)):
        if not them and _a_newer_answer_asked_them_to_call(last, turns) \
                and not ALREADY_RANG.search(clean):
            # "i think im fine" after this file told them to ring 999 for what they described is
            # not the end of it: the close ("That's the important bit done") is for a call that
            # was made or a crew that arrived, and neither has happened. A line that says they
            # rang keeps the close - that is the person doing the thing, not talking it down.
            return _choose(THE_CALL_STANDS_ANYWAY, memory, clean)
        # The end of it: "ok the fire is out now", "its stopped now". After the reaction-to-the-
        # close pool, so "its out but i feel shaky" is answered for the shaky and not by the close
        # a second time; before the ring branch, so "ok i rang them and hes fine now" is the close
        # and not a promise that "the crew are on their way". Help arriving is not the end of it:
        # "the crew are here", "the paramedics are here", "the ambulance is here" read as a close
        # to RESOLVED's arrival alternative, and answering them with "ring again if anything
        # changes" drops the line to the crew (cream-flag, #820). They keep the arrival pool.
        return _choose(_wrote_for_them(RESOLVED_AFTER_THEM, them) if them else RESOLVED_AFTER,
                       memory, clean)
    if ALREADY_RANG.search(clean):
        # "ok i rang them" is the person saying they did the thing, so "ring 999 if you haven't
        # already" reads as not listening.
        if A_HELPLINE.search(clean):
            # A helpline is not a dispatch: the samaritans, a crisis line and NHS 111 all talk,
            # and none of them send anybody. In a crisis thread the answer is the company the
            # person needs after telling somebody, in an ordinary one the care hold, and in a
            # thread whose last answer asked for 999 the day is not saved by ringing them.
            if any(word in last for word in CRISIS_WORDS):
                return _choose(_wrote_for_them(CRISIS_AFTER_THEM, them) if them else CRISIS_AFTER,
                               memory, clean)
            if any(word in last for word in SAFETY_WORDS):
                return _choose(HELPLINE_NOT_AN_AMBULANCE, memory, clean)
            return _choose(STILL_HERE_AFTER, memory, clean)
        if any(word in last for word in CRISIS_WORDS):
            # "ok i rang them" in a crisis thread is the crisis line, because that is the number
            # the bot gave: nobody has been sent, and "the crew are on their way" is not true.
            return _choose(_wrote_for_them(CRISIS_AFTER_THEM, them) if them else CRISIS_AFTER,
                           memory, clean)
        return _choose(HOLD_AFTER, memory, clean)
    if _reads_as_fear(read, clean) and not any(word in last for word in CRISIS_WORDS):
        # A line about the speaker's own fear gets company instead of the practical pool: it is
        # about the emergency whatever topic the reader gives it ("im really scared im going to
        # lose him"). It runs after the close and the thanks, so a fear once it is over gets
        # "the hardest part over", and not in a crisis thread, where the person is the one in
        # danger and the crisis pool holds.
        return _choose(AFRAID_AFTER, memory, clean)
    if set(words) & REACTION_WORDS:
        if any(word in last for word in CRISIS_WORDS):
            # Scared after a crisis answer is not somebody waiting for an ambulance: nobody has
            # been called, so the holding pool would promise a crew that is not coming.
            return _choose(_wrote_for_them(CRISIS_AFTER_THEM, them) if them else CRISIS_AFTER,
                           memory, clean)
        return _choose(_hold_pool(turns, clean, last), memory, clean)
    if (VISIT_ASK.search(clean) and not MEDICAL_PLACE.search(clean)
            and not NOT_A_VISIT.search(clean) and _somebody_to_visit(clean, turns)):
        # Whether to go and be with them, not whether to have the injury seen: before the injury
        # pool, because "should i go up tonight" matches the bare "go" in CARE_SEEN_ASKS.
        pool = CARE_VISIT_WARD if _someone_is_a_patient(clean, turns) else CARE_VISIT
        return _choose(pool, memory, clean)
    if CARE_SEEN_ASKS.search(clean):
        if _the_thread_is_an_animal(clean, turns):
            # A pet is not seen at a walk-in centre or in A&E: the same question about an animal is
            # the vet's, and the answer has to say so.
            return _choose(CARE_SEEN_ANIMAL, memory, clean)
        return _choose(CARE_SEEN, memory, clean)
    if _feels_better(clean):
        # Whether the thread is a crisis line or a first-aid answer, "i feel a bit better now" is
        # not answered by either pool: "ring 999 if you haven't already" reads as if the bot had
        # not heard, and so does "ring the crisis line now".
        if _no_relief(memory, last):
            # An overdose, a poisoning or an arrest is the one easing that must not be taken at
            # face value: the pool keeps the emergency line instead of sending them back to their
            # day. When the person who swallowed it is somebody else, the same instruction goes to
            # the carer about them - "get seen today" addressed to the person typing is advice for
            # a body that is not the one at risk.
            if them:
                return _choose(_wrote_for_them(EMERGENCY_BETTER_THEM, them), memory, clean)
            return _choose(EMERGENCY_BETTER, memory, clean)
        if any(w in last for w in CRISIS_WORDS):
            # "she says shes fine now" is their good hour, so the easing is the carer's: keep an
            # eye on them, ask again tomorrow.
            if them:
                return _choose(_wrote_for_them(CRISIS_BETTER_THEM, them), memory, clean)
            return _choose(CRISIS_BETTER, memory, clean)
        return _choose(CARE_BETTER, memory, clean)
    # The injury is read from the answer and from the line it answered: a sunburn is a burn
    # whether or not the safety card happens to use the word.
    opener = str(safety.get("user") or "").lower()
    if BURN_WORD.search(last) or BURN_WORD.search(opener):
        # Nothing on a burn and nothing popped: the two things people ask straight after being
        # told to cool it, and the two a knowledge entry answers wrongly ("oven", "butter").
        if BURN_BLISTER_LINE.search(clean) or POP_A_BARE_IT.search(clean):
            return _choose(BURN_BLISTER, memory, clean)
        if BURN_ON_IT.search(clean) or (BURN_THING.search(clean) and BURN_ASK.search(clean)):
            return _choose(BURN_AFTER, memory, clean)
    if them and SAID_AS_A_DEATH.search(clean):
        # The emergency was somebody else's and it is over: "my friend shot himself" and then "he
        # didnt make it", or a heart attack and then "she died". What is left is a bereavement, and
        # the loss module answers those - it answered this one on main, because no emergency card
        # had started the thread; with the card on the line before it, the emergency pool said
        # "stay in touch with them and say if anything gets worse" to somebody whose friend had
        # just died. Only when the person in danger is somebody else: after "i took too many pills",
        # "he died didnt he" is a question asked by a body that still needs the 999 hold.
        return None
    if any(word in last for word in CRISIS_WORDS):
        # In a crisis the continuation names the crisis line, and it says more about staying
        # safe tonight than "two of you is better than one" does; a person arriving is a good
        # sign, not a reason to drop the careful one (#deck row multi-042).
        return _choose(_wrote_for_them(CRISIS_AFTER_THEM, them) if them else CRISIS_AFTER,
                       memory, clean)
    if _someone_is_arriving(clean):
        # "my sister says she can come over tonight", "the ambulance is on the way"
        return _choose(WITH_YOU_AFTER, memory, clean)
    if _already_rang(turns):
        # The person said two turns ago that they rang, and "what happens now" is the line after
        # it: "ring 999 if you haven't already" tells them the bot was not listening. The hold
        # says the true thing instead - stay on the line and follow what they tell you.
        return _choose(HOLD_AFTER, memory, clean)
    if _the_answer_asked_them_to_call(last) or _raises_the_stakes(clean, last):
        # Which emergency it is decides the words: a person who is hurt is someone to stay in
        # touch with, a fire is not. The bot's own last answer says which one it was - the fire
        # answer names the smoke, the scald answer names the water - so the pools continue that
        # answer instead of guessing from the line. A follow-up that meets the card's own red
        # flag comes here too: the fall card's "cannot get up or put weight on it" said as
        # "im on blood thinners" is the emergency going on, not a line for the pharmacist.
        if _is_a_hazard(last):
            return _choose(HAZARD_AFTER, memory, clean)
        return _choose(EMERGENCY_AFTER, memory, clean)
    if _the_thread_is_an_animal(clean, turns):
        # The after-care pool names a pharmacist and a walk-in centre. An animal is not seen at
        # either of them, so the same continuation is said about the vet.
        return _choose(CARE_AFTER_ANIMAL_STILL if STILL_GOING.search(clean) else CARE_AFTER_ANIMAL,
                       memory, clean)
    if _a_newer_answer_asked_them_to_call(last, turns):
        # The care answer's route is out of date: this thread has since been told to ring, and
        # the person has not said they rang (that is answered further up), so the pool after an
        # emergency answer is the reply. Naming 111 here contradicts the bot's own last line,
        # and so does the softer hold: the number is still theirs to dial.
        return _choose(THE_CALL_STANDS, memory, clean)
    route = _the_route_the_answer_named(last)
    if route and not THE_THING_ITSELF_LOOKS_FINE.search(clean):
        # The answer named where to go and this line is about that answer: "my chest hurts when i
        # run" is answered "ring 111 or your GP first thing", so the pharmacist line that came
        # next named a different building - one that does not see a chest. A line that reports
        # the person looking well ("hes eating and playing fine") is not sent to ring again.
        return _choose(CARE_ROUTE_BACK[route], memory, clean)
    return _choose(CARE_AFTER_STILL if STILL_GOING.search(clean) else CARE_AFTER, memory, clean)


def _is_a_hazard(last):
    """True when the emergency the bot answered is a fire, a gas leak or an alarm going off.

    Read from the bot's own last answer and nothing else: that answer says what it was about
    ("leave the building... if there is smoke", "put out any flames"), while the line now may
    name a fuel without being a hazard at all - "my gas cooker wont light" in the middle of a
    heart attack is a remark, not a fire. A person's injury is not a hazard even when a fuel is
    mentioned - "my son pulled the kettle over" is a scald, and the answer to that one is about
    cooling the skin, so the pools for a hurt person stay.
    """
    return bool(HAZARD_LINE.search(str(last or "").lower()))


def _the_safety_cards(turns):
    """The safety answers still in the thread window, newest last.

    The thread can run several turns and the safety module answers some of them itself, so the
    card is not always the last reply: the one that started the thread is what says whether this
    is a crisis line, a call to make now, or somebody being hurt.
    """
    return [str(turn.get("bot") or "").lower() for turn in list(turns or [])[-THREAD_TURNS:]
            if str(turn.get("module") or "") == "safety"]


def _somebody_is_coming(turns, clean):
    """True when the person has rung, or help is with them, anywhere in the thread."""
    for turn in list(turns or [])[-THREAD_TURNS:]:
        said = str(turn.get("user") or "").lower()
        if said and (ALREADY_RANG.search(said) or _someone_is_arriving(said)):
            return True
    return bool(ALREADY_RANG.search(clean)) or bool(_someone_is_arriving(clean))


def _the_answer_was_an_abuse_card(last):
    """True when the bot's own last answer was the domestic abuse card.

    Read from the answer rather than from the line, because the line that follows an abuse card
    ("should i get out of the house") says nothing about abuse at all - the card is what makes
    this thread one where the person asking is the one in danger.
    """
    return bool(ABUSE_CARD.search(str(last or "")))


def _thread_was_closed(turns):
    """True when this fallback's last line in the thread was a close, not advice.

    "thanks, its stopped" is answered from THANKS_AFTER ("Any time. Take care — ring again if
    anything changes"), and that is the end of it: the next bare "ok" is a nod on the way out,
    not a line that needs the advice again.
    """
    for turn in reversed(turns[-THREAD_TURNS:]):
        if turn.get("module") != FALLBACK_MODULE:
            continue
        return any(str(turn.get("bot") or "").startswith(line[:24]) for line in THANKS_AFTER)
    return False


def _hold_pool(turns, clean, last, done_report=False):
    """The hold pool: one that may promise a call only when this thread already has one.

    "the operator", "the crew are on their way" and "keep the line open" are true after a 999
    call and a lie after a burn under the tap, so a care thread gets the plain hold instead
    (cobalt-panther and gray-cypress, #820).

    A done report is a third case: "i sorted it" says the person thinks the thing is handled, and
    not that anybody was rung, so a line that names an operator or a crew needs their own words to
    say somebody was (chief-umbrella and fancy-penguin, #7230).
    """
    if not _a_call_is_known(turns, clean, last):
        return STILL_HERE_AFTER
    if done_report and not (ALREADY_RANG.search(clean) or _already_rang(turns)):
        return SORTED_AND_NO_CALL_YET
    return HOLD_AFTER


# Advice to ring a number today is not a call in progress. "Ring 111 today about a home detox"
# is the same shape as "ring 999 now" as far as a number is concerned, and the difference is the
# one that matters: after the first, "ok" was answered "the crew are on their way" for a crew
# nobody had rung.
IMMEDIATE_CALL = re.compile(
    r"\b(?:ring|call|phone|dial)\s+(?:999|911|112|an\s+ambulance)\b"
    r"|\b999\s+(?:or\s+911\s+)?(?:now|straight|immediately|first)\b"
    r"|\bstraight\s+away\b|\bright\s+now\b|\bthere\s+and\s+then\b", re.I)


def _a_call_is_known(turns, clean, last):
    """True when somebody has been rung in this thread: said here, said before, or in the advice."""
    if ALREADY_RANG.search(clean) or _already_rang(turns):
        return True
    text = str(last or "")
    if not any(word in text for word in CALL_WORDS):
        return False
    # A number in the advice is only a call when the advice is to make one now. The gentle card
    # that says "ring 111 today" leaves the thread with nobody called, so the hold must not
    # promise a crew.
    if "111" in text and not IMMEDIATE_CALL.search(text):
        return False
    # A call put behind a condition is advice for a later turn, not a call in progress: after
    # "press a clean cloth on the cut ... if it soaks through, the edges gape, or they go pale or
    # dizzy, that's 999 or 911" a person saying "i did that" got "the crew are on their way" for
    # a crew nobody had rung.
    return not _the_call_is_conditional(text)


# A condition in front of the call is the whole difference between an instruction and a plan:
# "if it soaks through ... that's 999 or 911" is for the next turn, "ring 999 or 911 straight away"
# is now. Only the sentence that carries the call is read, so a condition elsewhere in the card
# does not spoil a call the card gives flatly.
CONDITIONAL_OPENING = re.compile(
    r"^\W*(?:if|unless|when|whenever|in\s+case|should|after|once|any\s*time)\b", re.I)


def _the_call_is_conditional(text):
    """True when every sentence of the answer that names a call puts it behind a condition."""
    carrying = [sentence for sentence in re.split(r"(?<=[.!?])\s+", str(text or ""))
                if any(word in sentence.lower() for word in CALL_WORDS)]
    if not carrying:
        return False
    return all(CONDITIONAL_OPENING.search(sentence.strip()) for sentence in carrying)


def _already_rang(turns):
    """True when the person said, in the last few turns, that somebody has been rung."""
    return any(ALREADY_RANG.search(str(turn.get("user") or "").lower())
               for turn in turns[-3:] if isinstance(turn, dict))


def _thanks_carries_emergency(words, clean):
    """True when a thanks also says the emergency is still going on.

    The thanks pools are a close, so they must not answer "thanks, its still soaking through".
    Any care word other than "thanks", a pronoun or a pointer ("still", "call", "there") counts,
    as does a mid-emergency ask ("is it safe to go down"); a bare "ok thanks" has none of these
    and closes. A thanks that also says it is over ("the doctor came", "the bleeding stopped",
    "its fine now") is a close, unless it also says it is still going on.
    """
    said = set(words)
    content = (said & CARE_WORDS) - THANKS_WORDS - CARE_PRONOUNS - CARE_POINTER
    if content and said & ONGOING_WORDS:
        return True
    if said & CARE_RESOLVED:
        # Only a resolved word still counts as resolved; "hasnt stopped"/"not fine" do not.
        return bool(said & CARE_NOT_RESOLVED)
    return bool(content or CARE_ASKS.search(clean) or CARE_SEEN_ASKS.search(clean)
                or any(phrase in clean for phrase in CARE_PHRASES))


# A date of ours going by is not a memory sign. "my husband keeps forgetting our anniversary"
# is a complaint about the partner, and it was read as the health word "forgetting" and answered
# with a GP and a dementia workup - a workup for a forgotten date (deck row habit-08). Only a date
# is let through: forgetting where you live, a name, the way home is the memory reading.
A_DATE_OF_OURS = re.compile(
    r"\b(?:forget(?:s|ting|ful)?|forgot)\b[^.]{0,24}?\b(?:our|my)\s+"
    r"(?:anniversary|birthdays?|dates?(?: night)?|valentine'?s|wedding day|christmas|plans?)\b")


# A worry said out loud about the person is the care line whatever else is in the line: "my husband
# keeps forgetting our anniversary, i think something is wrong" is asking about him, not about his
# manners, and the grumble pool would answer the wrong question. "not like him" and "getting worse"
# are how people say the same thing without naming a worry at all.
A_WORRY_ABOUT_THEM = re.compile(
    r"\b(?:something|summat)\s+(?:is|seems|feels)\s+(?:wrong|off|not right)\b|"
    r"\bnot (?:like|acting like) (?:him|her|them|himself|herself|themselves)\b|"
    # "shes not herself", "hes not his usual self": the person they know has changed, which is
    # the same worry as "not like him", and it turns a forgotten date back into the care line.
    r"\bnot (?:quite |really |been )?(?:himself|herself|themselves)\b|"
    r"\bnot (?:his|her|their) usual (?:self|selves)\b|"
    r"\b(?:worse|worrying)\b|\bworried about (?:him|her|them)\b|"
    r"\bshould i (?:be )?worr(?:y|ied)\b|\bdementia\b|\balzheim\w*\b|"
    r"\bconfus(?:ed|ion)\b|\bmemory\b")


def a_date_of_ours_forgotten(clean):
    """True when the line is somebody forgetting a date of ours - an anniversary, a birthday.

    Read by `chat` before it answers a person's trouble as a memory sign: a forgotten date is a
    complaint about the partner, and the grievance pool here is the reply for it, not a GP. A worry
    in the same line is the person asking about them, so the care line keeps that one.
    """
    said = " ".join(str(clean or "").lower().split())
    return bool(A_DATE_OF_OURS.search(said)) and not A_WORRY_ABOUT_THEM.search(said)


def _impact_said(clean):
    """The words of what somebody did, where the somebody is the one doing them."""
    tokens = re.findall(r"[a-z']+", clean)
    found = set()
    for position, token in enumerate(tokens):
        if token not in GRIEVANCE_IMPACT:
            continue
        before = tokens[max(0, position - 2):position]
        if before and before[-1] in NOT_THEIR_VERB:
            continue
        if any(word in FIRST_PERSON for word in before):
            continue
        # Forgetting is only about the two of them when it is a date of ours that went by:
        # "my boyfriend forgot our anniversary" is the complaint, "my friend forgot his keys"
        # is just what happened to him.
        if token in FORGETTING and not (set(tokens[position + 1:position + 4]) & OURS):
            continue
        # "eats all the biscuits" is the complaint; "eats meat", "eats fish on fridays" is a
        # diet, and the person is talking about what to cook rather than about their manners.
        if token in EATING and tokens[position + 1:position + 2] and \
                tokens[position + 1] in EATEN_KIND:
            continue
        found.add(token)
    return found


def _grief_thread(memory):
    """True when the last thing the bot said about this was a condolence.

    "we lost the baby in february" then "my partner wont talk about it": the partner is part of
    the grief, so the line keeps the thread rather than treating it as somebody's bad manners.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-THREAD_TURNS:]):
        line = str(turn.get("bot") or "")
        if not line:
            continue
        return any(line.startswith(reply[:30]) for reply in loss.LOSS_REPLIES)
    return False


def _grievance_thread(memory):
    """True when the last thing the bot said about this was the offer to talk it over.

    "my friend drains me" then "she rings me every night as well": the second line names the
    person only as "she", and the reader wants a person word ("my sister") or something of theirs
    in the way, so the follow-up fell through to "Thanks for telling me - I'm here if you want to
    dig into any of that" - the line that fits any message, said to somebody who is still
    complaining about the same person.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns[-THREAD_TURNS:]):
        line = str(turn.get("bot") or "")
        if not line:
            continue
        return any(line.startswith(reply[:30]) for reply in GRIEVANCE)
    return False


def _someone_else_minding(clean, words, after=False):
    """True when the line is about what another person keeps doing, and the person minds it.

    The person has to be in the line as somebody else ("my sister", "the landlord", "someone")
    and the line has to say it keeps happening ("keeps", "always", "never", "again", "without
    asking"). Asked only about the person's own line, never about the bot: "you never listen"
    is a complaint about the bot and gets a different reply.
    """
    said = {w for w in words if w.isalpha() or "'" in w}
    # "she is so draining", "he is really exhausting", "they are tiring": a pronoun in front of
    # the word for the wear is already the person, and the wear is in the word itself. Without
    # this the first line of a complaint that names somebody only as "she" fell to the line that
    # fits any message - "Thanks for telling me - I'm here if you want to dig into any of that" -
    # when the person had just said that somebody tires them out.
    a_person_pronoun = bool(GRIEVANCE_PRONOUN.search(clean))
    if said & GRIEVANCE_PEOPLE:
        if not ({"my", "our", "the"} & said):
            return False
    elif not (after and said & THREAD_PEOPLE) and not a_person_pronoun:
        # A follow-up in the same thread names the person only as "she" or "he": it is still the
        # same row, so the person comes from the turn before rather than from this line.
        return False
    # "he never says thank you for anything" is about him, not about the bot: "thank you" is the
    # only "you" in the line and it is the phrase, so it is taken out before the test.
    spare = clean.replace("thank you", "thanks").replace("thank u", "thanks")
    if " you " in " " + spare + " ":
        return False  # "you never listen" is a complaint about the bot, not about them
    if said & GRIEVANCE_HEALTH or said & GRIEVANCE_HARM:
        # A body, an illness or a harm wants a care line, not a word with them - except where the
        # health word is the forgetting of a date of ours, which is the grievance itself.
        if not (a_date_of_ours_forgotten(clean) and not said & GRIEVANCE_HARM):
            return False
    if any(phrase in clean for phrase in GRIEVANCE_HARM_PHRASES):
        return False
    if any(phrase in clean for phrase in GRIEVANCE_HEALTH_PHRASES):
        return False
    if _impact_said(clean) - set(GRIEVANCE_MINE.findall(clean)):
        return True
    if GRIEVANCE_RECUR.search(clean):
        # In a thread that is already about them, the "again" is enough. The exception is the
        # person turning it on themselves - "i never say anything to her" is their own silence,
        # not the other one's manners, and the offer to work out what to say would talk past it.
        if after and not GRIEVANCE_MINE.search(clean):
            return True
        if any(word not in GRIEVANCE_PEOPLE and word not in GRIEVANCE_NOT_A_THING
               for word in GRIEVANCE_MINE_THINGS.findall(clean)):
            return True
    if any(phrase in clean for phrase in GRIEVANCE_PHRASES):
        return True
    if any(phrase in clean for phrase in GRIEVANCE_STRAIN):
        return True
    return bool(GRIEVANCE_STRAIN_SAID.search(clean))


def _short_ack(words):
    """True for a bare "ok", "right", "got it" — a nod, not a new subject."""
    return len(words) <= 2 and bool(set(words) & ACKS)


# The subject a good time is had by: a group, or the event itself. A person on their own saying
# "i had a lovely day" is left to the ordinary pools, because that line is about them and the
# good news and feeling replies know what to do with it.
GOOD_TIME_SUBJECT = re.compile(
    r"\b(?:everyone|everybody|all of them|"
    # An event belongs to somebody as often as it is "the" event: "my sister's wedding was lovely"
    # and "the kids' match was great" are the same good half of a chat as "the wedding was lovely",
    # and the possessive in front of the word kept them out of it - they reached the pool that
    # answers nothing ("Thanks for telling me - I'm here if you want to dig into any of that") and,
    # on the first of them, "I'm listening - say more if it helps".
    r"(?:the|my|our|his|her|their|your|\w+'s?)"
    r"(?:\s+\w+){0,2}\s+"
    r"(?:party|wedding|meal|trip|holiday|gig|match|game|concert|night|day|weekend|evening|"
    r"dinner|barbecue|bbq|bash|hen|stag))\b")
GOOD_TIME_OURS = re.compile(
    r"\bwe (?:had|have had) (?:a |such a )?(?:great|lovely|brilliant|good|amazing|wonderful|"
    r"fantastic|smashing)\b")
# A good day is the same good time said about one person, and it is how most people report one:
# "i had a really good day today", "great day today", "best day ever". The greeting words are the
# reason this is not just an adjective and a day - "good morning", "good night" and "have a good
# day" are hello and goodbye, and a warm question about the best of it is the wrong reply to
# either. So the line has to say it happened to them ("i had...") or say how the day went
# ("today was..."), and never just name it.
GOOD_DAY_OURS = re.compile(
    # A good day had by somebody the person knows is a good day too: "the kids had a lovely time"
    # and "my mum had a good day" were answered with the neutral pool, the line a person gives when
    # they were not listening. The subject is the person or the group, so the same words that say
    # "i had" say "the kids had".
    r"^(?:(?:i|we|ive|i've|weve|we've|(?:my|our|the|his|her|their)(?:\s+\w+'s)?"
    r"(?:\s+\w+){0,2})\s+)?(?:had|have had|ve had|has been having|am having|"
    r"are having)\s+(?:a\s+|such a\s+|a really\s+|a proper\s+|a pretty\s+)?"
    r"(?:really\s+|properly\s+|pretty\s+|so\s+|such\s+|super\s+)?"
    r"(?:good|great|lovely|nice|brilliant|amazing|wonderful|lush|smashing|fantastic)\s+"
    # The list is the times a good day is said with, and the things people do with one: "i had a
    # lovely walk today" and "we had a nice lunch" are the same good half of a chat, and the
    # thing is what the pools' question can be about.
    r"(?:day|week|weekend|evening|afternoon|morning|night|shift|time|walk|swim|run|ride|"
    r"cycle|lunch|dinner|meal|picnic|bath|shower|breakfast|coffee|nap|sleep|lie in|read)\b")
# "great day today" and "good day at work" drop the "i had" altogether. These are anchored at the
# start of the line, which is what keeps "have a good day" (a goodbye) and "good morning" (a
# hello) out of it, and they leave out "good" and "nice" for the same reason.
GOOD_DAY_BARE = re.compile(
    r"^(?:what |such |a )?(?:really |so |pretty |proper |quite )?"
    r"(?:great|lovely|brilliant|amazing|wonderful|fantastic|lush|smashing|perfect)\s+"
    r"(?:day|week|weekend|evening|afternoon|morning|night|shift)\b")
GOOD_DAY_WENT = re.compile(
    r"\b(?:today|yesterday|the day|the week|the weekend|last night|this (?:morning|afternoon|"
    r"evening)|my day|my week|my weekend)\s+(?:was|has been|went|'s been)\s+(?:a\s+)?"
    r"(?:really\s+|so\s+|proper\s+|pretty\s+|such\s+|quite\s+)?"
    r"(?:good|great|lovely|nice|brilliant|amazing|wonderful|fine|alright|lush|fantastic)\b"
    r"|\bbest\s+(?:day|week|weekend|evening|night)\b")
# The same good time said with "it" for a subject: "it was great", "it was such a nice day",
# "it was a lovely evening", "it was great fun". Every one of these was answered with the neutral
# pool ("Thanks for telling me - I'm here if you want to dig into any of that") or with an echo,
# because the good-time gate wanted a subject it could name: a day, a group, or the person. "it"
# is a subject too, and the thing it stands for is whatever the two of them were just on.
#
# The words after the good word are what keep this off the lines that only look alike. "it was a
# good idea", "it was nice of her", "it was great news" and "it was nice to meet you" all carry a
# good word and a subject, and none of them is a good time had by anything: the tail is a short
# list of the things a good time can be, or nothing at all.
GOOD_TIME_IT = re.compile(
    r"^(?:it|that|this)\s+(?:was|were|has been|s been|turned out)\s+"
    r"(?:(?:a|an|such a|such)\s+)?"
    r"(?:(?:really|so|pretty|proper|properly|quite|absolutely|dead|very)\s+)?"
    r"(?:good|great|lovely|nice|brilliant|amazing|wonderful|fantastic|lush|smashing)\b"
    r"(?:\s+(?:fun|time|day|night|evening|weekend|week|meal|trip|holiday|break|wedding|party|"
    r"gig|show|film|game|match|outing|afternoon|morning|christmas|birthday|dinner|lunch|"
    r"barbecue|do|out|away|all|overall|actually|though|thanks|in the end)\b)*\s*$")


# A verdict on a thing, said with nothing asked: "it was dead good actually", "its dead good
# actually", "the film was lovely". The subject is a thing of theirs or an "it/that/this", never
# a person ("my mum was great" is about her, and the family and feeling pools know what to do
# with those), and the good word ends the line, so a mixed verdict ("it was good but the ending
# dragged") keeps its own reply. "its" is "it is" written without the apostrophe, so the copula
# is optional: the intensifier or the good word is what carries the sense either way.
GOOD_VERDICT = re.compile(r"""
    ^\W*(?P<subject>(?:it|its|it\'s|that|thats|that\'s|this|the\s+\w+|my\s+\w+|our\s+\w+)
         (?:\s+(?:was|is|were|are|has\s+been|\'s\s+been))?)\s+
    (?:really\s+|so\s+|proper\s+|pretty\s+|dead\s+|quite\s+|absolutely\s+|well\s+)*
    (?:good|great|lovely|nice|brilliant|amazing|wonderful|lush|smashing|fantastic|superb|
        class|fun)\b
    (?:\s+(?:actually|honestly|tbh|though|to\s+be\s+fair))?\W*$
""", re.X | re.I)


# The turns a good word can follow without being a good time: an accident, a body in trouble, a
# pet put to sleep. `badnews` reads the news a friend meets gently; these are the plain words for
# the same week that it leaves to other readers.
HARD_WEEK = re.compile(r"\b(?:fall|fell|fallen|tripped|collapsed|collapse|seizure|stroke|"
                       r"overdose|accident|crash|crashed|put down|passed away|in hospital|"
                       r"operation|surgery|stitches|broken|broke (?:my|his|her|their))\b")


def _hard_week_in_the_thread(memory):
    """True when the thread still holds a death or an accident the bot was gentle about.

    A list of ceremony words is a net with holes in it (sure-umbrella on #3594: "a list always
    leaves one out"), so the reading stands down on the shape that matters instead - a recent
    turn that was a death, an accident, or a line a friend would answer gently. "my mum had a
    fall" a turn before "the paramedics were brilliant" is the same hard week as a funeral: the
    good word is about how they were, not about a good time.
    """
    if not memory:
        return False
    if loss._loss_is_the_thread(memory):
        return True
    for earlier in [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-2:]:
        line = " ".join(str(earlier.get("user") or "").lower().split())
        if line and (reads_as_bad_news(line) or badnews.reads_as_sudden_loss(line)
                     or HARD_WEEK.search(line)):
            return True
    return False


def _a_verdict(clean, memory=None):
    """True when the line is a good verdict on a thing, with nothing asked and nothing after it.

    The thing has to be something you can have a good time with: a person is not (the family and
    feeling pools have better lines for them) and neither is a place of care or a funeral, where
    the same words describe how a hard week went rather than how nice it was. In a bereavement
    nothing on the line is a night out either: "the flowers were lovely" and "the service was
    lovely" are about the day, and the reading stands down for the whole thread rather than for a
    list of its words (emerald-carpet on #3594: the loss card kept the eulogy by luck, because
    only a subject the reader catches would have taken it).
    """
    if _hard_week_in_the_thread(memory):
        return False
    found = GOOD_VERDICT.search(clean)
    if not found:
        return False
    said = found.group("subject").lower().split()
    head = said[1] if len(said) > 1 else said[0]
    if head in GRIEVANCE_PEOPLE or head in trouble.OTHERS:
        return False
    if head in NOT_A_VERDICT_SUBJECT:
        return False
    return True


# Looking forward said as a want rather than as news. The news-to-come reader keys on the thing
# (a wedding, a baby, a move, a holiday), so a weekend, a Friday, a night out or a person seen
# again went past it to the floor. Only the looking-forward phrase counts, and only when the line
# does not turn it into dread: "i cant wait for this week to end", "cant wait to get out of here"
# and "not looking forward to monday" are a bad week, not a thing to look forward to, and the
# trouble and mood pools answer them.
LOOKING_FORWARD = re.compile(
    r"\b(?:cant|cannot|can not|can't)\s+wait\b"
    r"|\b(?:really |so |properly |very )?(?:am |im |i'm )?looking forward to\b"
    r"|\broll on\b"
    r"|\bcount(?:ing)? down (?:the days )?(?:to|till|until|til)\b"
    r"|\b(?:only|just)\s+\d+\s+(?:days?|weeks?|sleeps?)\s+(?:to go|till|until|til)\b"
    r"|\bnot long (?:now )?(?:till|until|before)\b"
    r"|\b(?:excited|buzzing|chuffed) (?:about|for|to)\b", re.I)
# "Cant wait" is an eagerness only when what follows is worth waiting for. The other sense is
# being at home when somebody turns up: "cant wait in for an engineer", "cant wait around for a
# delivery", "i cant wait until friday for the boiler man". "and i have to be at work at 7 so
# cant wait in for an engineer" was answered "That's worth looking forward to. Tell me how it
# goes.", and "cant wait around for a delivery, i work days" was cheered the same way. The words
# after the wait are the test, so every wording of that sense goes with them, and a line that
# looks forward in another way as well ("i cant wait in all day but i cant wait to see her") keeps
# its eagerness.
A_CANT_WAIT = re.compile(r"\b(?:cant|cannot|can not|can't)\s+wait\b", re.I)
# The stay-at-home sense on its own: waiting in, around, about, at home.
A_WAITING_IN = re.compile(r"\s+(?:in|around|about|at\s+home|indoors)\b", re.I)
# And the same sense said with the person it is for, when the line also says the day is not
# theirs to give: "i have to be at work at 7 so cant wait in for an engineer" is the plain one,
# "i work days so i cant wait until friday for the boiler man" is the same wait. Without a
# working day in the line, "i cant wait for the plumber to come and fix the heating" stays the
# eagerness it reads as, because a cold house is worth waiting for.
A_WAITING_FOR_A_TURN_UP = re.compile(
    r"\s+(?:for|till|until|til|on)\s+(?:[\w']+\s+){0,4}?"
    r"(?:engineer|plumber|electrician|gas\s+man|boiler\s+man|repair\s+man|delivery|deliveries|"
    r"parcel|parcels|courier|post|postman|installer|technician|builder|roofer|scaffolder|council|"
    r"nurse|carer|vet|someone|anyone|somebody|it\s+to\s+(?:be\s+)?(?:fixed|repaired|arrive|come|"
    r"turn\s+up)|them\s+to\s+(?:come|arrive|turn\s+up))\b", re.I)
A_WORKING_DAY = re.compile(
    r"\b(?:have\s+to\s+be\s+(?:at|in)\s+work|have\s+to\s+work|ive\s+got\s+to\s+work|"
    r"im\s+at\s+work|i'm\s+at\s+work|i\s+work\b|im\s+working|i'm\s+working|on\s+shift|"
    r"working\s+days?|no\s+time\s+off|not\s+free|only\s+free|day\s+off)\b", re.I)


# What turns a want-to-come into a dread: the thing coming is an end, or the line says it is not
# looked forward to.
NOT_LOOKED_FORWARD_TO = re.compile(
    r"\b(?:to (?:end|finish|be over|be done with|stop)|over with|get (?:it|this) over)\b"
    r"|\b(?:to )?(?:get out|leave|quit|resign|escape|be done|go home)\b"
    r"|\b(?:not|never)\s+(?:really\s+|at all\s+)?looking forward to\b"
    r"|\bdread(?:ing)?\b|\bnot (?:to )?(?:the )?end\b"
    r"", re.I)


# A wait for the end of a life is not a wait for something to come, and it is not a stretch the
# person wants behind them either. "i cant wait to die" was answered "That's worth looking
# forward to. Tell me how it goes." - the worst sentence this bot can hand a person - and the
# pool for wanting a bad stretch over ("Fair enough. What's making it drag?") is not much better.
# "i cant wait to be out of pain" and "i cant wait to see my dad again", said about a parent who
# has died, read the same way. The safety and loss readings catch the phrasings that name a
# method ("i want to die", "i wish i was dead"); these name none, so both cheer pools stand
# aside and the flat reply the store has is better than either.
A_WAIT_FOR_A_LIFE_TO_END = re.compile(
    r"\b(?:to|till|until|til)\s+(?:i\s+)?(?:die|be dead|be gone|be with (?:him|her|them)|"
    r"not wake up|stop (?:hurting|being here)|be out of (?:this )?pain|be at peace)\b"
    r"|\b(?:die|dying|dead|death|suicide|kill myself|end it all|no reason to live)\b"
    r"|\bsee (?:my |our )?(?:mum|mom|mother|dad|father|son|daughter|wife|husband|gran|nan|"
    r"grandad|grandma|grandpa|brother|sister|baby|child) again\b", re.I)


DREADING = re.compile(
    r"\bdread(?:ing|s)?\b|\bnot (?:really |at all )?looking forward to\b"
    r"|\bcant face\b|\bcan't face\b|\bthe thought of\b[^.?!]{0,40}\bmakes me\b", re.I)
# What a dread line has to be left to: something that is really wrong is the trouble, feeling or
# safety pools' line, not a light question.
NOT_A_MILD_DREAD = re.compile(
    r"\bdread (?:to|what(?:ever)? it) (?:think|hear)\b|\bdread to think\b|"
    r"\b(?:suicide|kill myself|end my life|self[- ]harm|hit me|hurts? me|abuse[sd]?|"
    r"died|dying|death|funeral|cancer|hospital|diagnos\w*)\b", re.I)


def _dreading(clean):
    """True for a mild thing coming that the person is not looking forward to."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text or len(text.split()) > 20:
        return False
    if not DREADING.search(text) or NOT_A_MILD_DREAD.search(text):
        return False
    return True


def _wants_it_over(clean):
    """True when the thing being waited for is the end of a bad stretch."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text or A_WAIT_FOR_A_LIFE_TO_END.search(text):
        return False
    return bool(LOOKING_FORWARD.search(text) and NOT_LOOKED_FORWARD_TO.search(text))


# A thing with a date on it in the person's own future, said flat: "my holiday is next week",
# "im off on holiday in two days", "my exam is on monday", "my sister is visiting next week", "i
# have a hospital appointment tomorrow". The nod files these back ("Noted: your holiday is next
# week"), which is the restatement STYLE.md rules out and answers nothing at all: something is
# ahead of them, and the useful reply is about that. Split by tone, because a holiday and a
# hospital appointment do not want the same question.
DATE_AHEAD = re.compile(
    r"\b(?:tomorrow|tonight|next (?:week|month|year|weekend)|this (?:weekend|afternoon|evening)|"
    r"(?:on )?(?:mon|tues|wednes|thurs|fri|satur|sun)day|next (?:mon|tues|wednes|thurs|fri|satur|"
    r"sun)day|in (?:\d+|a few|a couple of|two|three|four) (?:days?|weeks?|months?)|"
    r"in the morning|the week after|not long now)\b", re.I)
# The line has to be about the person's own thing, not a general remark with a day in it
# ("sundays are lovely" is not a plan).
DATE_AHEAD_OWN = re.compile(
    r"\b(?:my|our|im|i'm|i am|we are|we're|ive|i've|i have|i start|i go|i get|im off|i'm off)\b"
    r"|\bthe (?:wedding|holiday|trip|exam|interview|test|party|scan|operation|appointment|"
    r"viewing|hearing|move)\b", re.I)
# A thing that is ahead and good, and a thing that is ahead and tense. Without one of these the
# line is left to the rest of the chain.
AHEAD_NICE = re.compile(
    r"\b(?:holiday|holidays|trip|break|week off|visit|visiting|visitor|party|wedding|christening|"
    r"concert|gig|festival|night out|day out|meal|dinner|lunch|housewarming|camping|abroad|"
    r"flight|date|seeing|meeting up|reunion|graduation|barbecue|bbq|staying|going away|getaway|"
    r"off to|away for)\b", re.I)
AHEAD_TENSE = re.compile(
    r"\b(?:exam|exams|test|interview|scan|operation|surgery|appointment|hospital|dentist|doctor|"
    r"assessment|presentation|results|deadline|inspection|audit|court|hearing|tribunal|"
    r"check-?up|treatment|procedure|settlement|viewing|inspection|review|appraisal|"
    r"one-to-one|back to work|back at work|back to school|term starts|jab|jabs|vaccine|"
    r"vaccination|injection|booster|blood test)\b", re.I)
# Whatever else is in the line, these are somebody else's to answer: a death, a funeral, a
# diagnosis or abuse is not a plan, and the loss, safety and trouble pools come first anyway.
NOT_A_PLAN = re.compile(
    r"\b(?:died|dying|death|funeral|buried|cremation|hospice|terminal|cancer|chemotherapy|"
    r"hit me|hurt me|abuse[sd]?|miscarriage|stillborn|passed away|suicide|kill myself)\b", re.I)


def _a_day_ahead(clean):
    """Return the pool for a dated thing ahead of the person, or None.

    Read only when the line is a statement about their own thing and the thing is either good or
    tense. Anything else keeps whatever reply it had - this is here to stand in for the nod, not
    to answer everything with a date in it.
    """
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return None
    if not DATE_AHEAD.search(text) or not DATE_AHEAD_OWN.search(text):
        return None
    if NOT_A_PLAN.search(text):
        return None
    if AHEAD_TENSE.search(text):
        return A_DAY_AHEAD_TENSE
    if AHEAD_NICE.search(text):
        return A_DAY_AHEAD
    return None


def _the_wait_is_for_someone_to_turn_up(text):
    """True when the only looking forward in the line is a "cant wait" that means being at home.

    Read on what follows the wait, and only when every "cant wait" in the line is that sense and
    no other shape in the line is looking forward, so a mixed line keeps its eagerness.
    """
    hits = list(A_CANT_WAIT.finditer(text))
    if not hits:
        return False
    left = text
    for hit in hits:
        left = left[:hit.start()] + " " + left[hit.end():]
    if LOOKING_FORWARD.search(left):
        return False
    working = bool(A_WORKING_DAY.search(text))
    for hit in hits:
        after = text[hit.end():]
        if A_WAITING_IN.match(after):
            continue
        if working and A_WAITING_FOR_A_TURN_UP.search(after):
            continue
        return False
    return True


def _looking_forward(clean):
    """True when the line is looking forward to something still to come."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return False
    if not LOOKING_FORWARD.search(text) or A_WAIT_FOR_A_LIFE_TO_END.search(text):
        return False
    if _the_wait_is_for_someone_to_turn_up(text):
        return False
    return not NOT_LOOKED_FORWARD_TO.search(text)


def _a_good_time(clean, memory=None):
    """True when the line reports a good time had by a group or by an event.

    A question is not a report ("was the wedding good"), and a "but" turns the line into a mixed
    one that the pools for trouble and feeling answer better. The positive word has to be there,
    so "the trip was cancelled" and "everyone there was awful" are left alone.
    """
    if "?" in clean or " but " in clean or " until " in clean:
        return False
    # The good-day shapes are anchored and name what happened ("i had", "today was", "great day
    # today"), so they are read before the question openers: "had a good day at work" opens with
    # a word from that list and is not a question, while "did you have a good day" still starts
    # with the "did" and stays out.
    if (GOOD_DAY_OURS.search(clean) or GOOD_DAY_WENT.search(clean)
            or GOOD_DAY_BARE.search(clean) or GOOD_TIME_IT.match(clean)):
        return True
    if _a_verdict(clean, memory):
        return True
    if (clean.split() or [""])[0] in QUESTION_OPENERS:
        return False
    if GOOD_TIME_OURS.search(clean):
        return True
    if not GOOD_TIME_SUBJECT.search(clean):
        return False
    return bool(set(re.findall(r"[a-z]+", clean)) & GOOD_TIME_WORDS)


# A film that was hilarious is a film, and the recommender has something to say about it ("For
# laughs: *What We Do in the Shadows*..."). The laugh pool would take the line first and hand back
# a question about it, which is a worse answer to somebody who has just named a film: they are
# telling the bot what they watched, and the bot knows some. "the show", "the book" and "the gig"
# are not in here - the recommender keys on film and movie, and for the rest the laugh is the
# better reply.
A_FILM = re.compile(r"\b(?:film|films|movie|movies|cinema|netflix)\b", re.I)

# A laugh that names harm is not a good day, even as hyperbole. "i laughed so hard i nearly killed
# myself" reads as a suicide line to every other pool in this file, and cheering it ("Ha - that
# good?") is the one reply nobody wants; the deck carries it under safety. The harm word is what
# makes it, not the death word: "i nearly died laughing" and "i laughed so hard i nearly died" are
# both a joke about the laughing, and they stay a laugh.
HARM_IN_A_LAUGH = re.compile(
    r"\b(?:kill(?:ed|ing|s)? myself|end(?:ed|ing)? my life|want(?:ed|s|ing)? to die|"
    r"suicid\w*|self[- ]harm\w*|overdos\w*|took (?:some |a load of )?pills?)\b", re.I)

# A laugh that has stopped is the opposite of a good day, and it is the one place where laughing
# back does harm: "my mum hasnt laughed in weeks", "nothing makes me laugh any more", "i dont
# laugh much these days" are a person telling the bot something is wrong, and LAUGHING matches the
# word in every one of them. Measured by chief-umbrella on 44 probe lines: this stands down the ten
# that are about not laughing and keeps every gain ("she made me laugh", "it had me in stitches",
# "i nearly died laughing"). It also stands down "nothing is funny any more" and "funny that the
# bus never came", which other tests already guard, so nothing is lost there. The cost is
# "i have never laughed so hard", where the honest reply is a nod rather than a cheer.
LAUGH_STOPPED = re.compile(
    r"\b(?:any ?more|any ?longer|these days|lately|never|hardly|used to|stopped|"
    r"in (?:weeks|months|years)|remember the last time)\b", re.I)

# Two shapes that are not a story, so "what set it off?" has nothing to be about: how somebody's
# laugh sounds ("she has a lovely laugh") and a general liking for laughing ("i love a good
# laugh"). Both are warm lines about laughing, not a report of one, and the pool's question is the
# wrong reply to them.
A_LAUGH_ITSELF = re.compile(
    r"\b(?:has|have|had|got)\s+(?:a|such a|the)\s+(?:very\s+|really\s+|proper\s+)?"
    r"(?:lovely|nice|great|good|infectious|loud|big|brilliant|wonderful|happy|silly)\s+laugh\b"
    r"|\bi\s+(?:love|like|adore|enjoy)\b[^.?!]{0,20}\b(?:a|good|a good|nothing better than a)"
    r"\s+laugh\b"
    r"|\bnothing (?:beats|better than) a good laugh\b", re.I)


# A laugh in the room is not the person's laugh. "i fell over and everyone laughed", "i made a
# fool of myself and they laughed" and "i tripped and they all laughed" were all answered "Ha -
# that good? Tell me the best bit.", which joins in with a laugh that was at the person: it is the
# same fault the "laughed at" list catches, said without the "at". A room word as the subject of
# the laugh is that, unless the line also has the person's own laugh in it - "my friends and i
# laughed for hours" keeps the pool, and so does "the kids made me laugh".
A_ROOMS_LAUGH = re.compile(
    r"\b(?:everyone|everybody|they|all of them|the (?:others|rest|group|kids|class|crowd|family)|"
    r"my (?:mates|friends|sisters?|brothers?|mum|dad|husband|wife|partner|boyfriend|girlfriend|"
    r"boss|colleagues|coworkers|workmates|family))\b(?:\s+[\w']+){0,3}\s+"
    r"(?:laughed|laugh|laughing|giggled|giggling)\b", re.I)
A_OWN_LAUGH = re.compile(
    r"\b(?:i|we|me|us)\b(?:\s+[\w']+){0,2}\s+"
    r"(?:laughed|laugh|laughing|giggl(?:ed|ing)|in stitches|creased up)\b|"
    r"\b(?:made|makes|make|had) me laugh\b", re.I)


def _something_funny(clean, memory=None):
    """True when the line says something was funny and nothing in it says a problem.

    A question is not a report ("was that funny"), a "but" turns it into a mixed line the pools
    for trouble and feeling answer better, and being laughed at is not a good day.
    """
    if "?" in clean or " but " in clean:
        return False
    if LAUGHING_AT.search(clean):
        return False
    if A_FILM.search(clean):
        return False
    if HARM_IN_A_LAUGH.search(clean):
        return False
    if LAUGH_STOPPED.search(clean):
        return False
    if A_LAUGH_ITSELF.search(clean):
        return False
    if A_ROOMS_LAUGH.search(clean) and not A_OWN_LAUGH.search(clean):
        return False
    if isinstance(memory, dict) and _in_a_care_thread(memory):
        # "my father died on tuesday" then "we laughed about it afterwards" is the memory of a
        # funeral, not a good day: the care thread's own reply is right and a cheer is not.
        return False
    return bool(LAUGHING.search(clean))


# An apology for stepping away is easy to mistake for an apology about a fault. Only the absence
# after the "sorry" makes it this shape, and what they went to do has to be a small errand, so
# "sorry i crashed the car" and "sorry for your loss" keep their own replies.
# A mistake is not an absence: "sorry i went to the wrong house" is the person telling me something
# went wrong, so "i went" only counts when what follows is the errand or the place they were away
# from. gray-palm measured the loose version taking "sorry i went to the wrong house" and answering
# "No bother at all - go on." to a line that had news in it.
STEPPED_AWAY = re.compile(
    r"\b(?:sorry|apologies)\b[^.?!]{0,30}\b(?:i went (?:to (?:get|grab|pick|fetch|answer|"
    r"check|put|sort|deal|make|do)\b|for\b|away\b|out\b|off\b)|i had to go\b|"
    r"to get (?:the|my|some)\b|to pick (?:up )?(?:the|my)\b|for a (?:min|minute|sec|second|"
    r"bit|moment)\b|i'?ve been away|i was gone)\b"
    r"|\b(?:sorry|apologies) (?:i|for) (?:disappeared|vanishing|going quiet|being away)\b"
    r"|\b(?:sorry|apologies)\b[^.?!]{0,40}\b(?:i was (?:away|asleep|out|busy|driving|"
    r"in a meeting|on a call|at (?:work|school|uni))|slow (?:reply|response)|late (?:reply|"
    r"response)|the delay)\b"
    r"|\b(?:sorry|apologies) (?:i|that i) (?:missed|didn'?t (?:see|get)) (?:your|that) "
    r"(?:message|reply|text)\b"
    # The wait itself is the same apology as the silence, and it was the one shape that missed
    # the pool: "sorry for the wait" and "sorry i took so long" got the stock nod, and "sorry im
    # late replying" got advice on writing the email. These words are about the answer taking a
    # while, so they say nothing about being late for anybody.
    r"|\b(?:sorry|apologies)\b[^.?!]{0,30}\b(?:for the wait|the wait|kept you waiting|"
    r"took (?:me )?(?:so|a while)|took so long|late replying)\b")


# The errand is not the only way to be drawn away: the person was distracted, waylaid, pulled
# away or sidetracked, and "Noted: you got distracted." is what the store filed it as. This
# shape needs no apology in front, because "i got distracted" in the middle of a chat is the
# whole content of the line too, and the pool below is what a friend answers it with.
GOT_DRAWN_AWAY = re.compile(
    r"\b(?:got|get|was|been)\s+(?:a\s+(?:bit|little)\s+|a bit\s+|totally\s+|completely\s+)?"
    r"(?:distracted|waylaid|sidetracked|side-tracked|pulled\s+away|dragged\s+away|"
    r"called\s+away|taken\s+away)\b"
    r"(?:\s+(?:by|with)\s+(?:a|the|some|my|an)?\s*[a-z']{2,12})?"
    r"|\b(?:got|get|was|were|been)\s+(?:talking|chatting)\s+to"
    r"(?:\s+(?:a|the|some|my|his|her|our)\s+[a-z']{2,12})?"
    r"|\b(?:got|get)\s+caught\s+up\s+with(?:\s+(?:a|the|some|my|an)\s*[a-z']{2,12})?")


# The words that turn the page: whatever follows one of these is the next subject, not the
# reason for the gap.
A_TURN_THE_PAGE = re.compile(
    r"\b(?:anyway|anyways|but|oh|also|by\s+the\s+way|while\s+i'?m\s+here|"
    r"quick\s+question|separate\s+thing|other\s+thing)\b")


# A stretch away because of an illness is the same reason for the gap, and it names nothing the
# bot can answer on its own: "sorry for the silence, i had the flu" was answered "Sounds alright.
# Anything good in it?" - a line about a film nobody mentioned, to somebody explaining a fortnight
# of silence. The same for the reason arriving as a person: "sorry i went quiet, my mum was ill"
# is an apology, not a confession to be coached.
A_GAP_FOR_ILLNESS = frozenset("""
    flu cold covid bug virus infection ill sick unwell poorly worse hospital operation surgery
    migraines migraine headache bereavement funeral grieving grief depressed depression anxiety
    burnout recovery recovering recovered injury injured broken sprained test scan results
    doctor doctors gp a&e sleep sleepless insomnia
""".split())
# The reason can be a person: "sorry i went quiet, my mum was ill" is the gap and an ill relative,
# not a confession to be coached through ("Name what you did, say why it was wrong"). A person
# named beside a reason is part of the reason, so the words that name one may be left over - but
# only with a reason word beside them, never on their own.
A_GAP_NAMED_PERSON = frozenset("""
    mum mom mother mum's dad father dad's sister brother gran grandad grandma grandpa nan nana
    son daughter wife husband partner boyfriend girlfriend fiance fiancee kids children child
    baby family friend mate aunt uncle cousin mother-in-law father-in-law in-laws
""".split())


def _the_gap_is_all_there_is(clean):
    """True when nothing is left of the line once the apology for the gap is taken off.

    The apology used to take the whole line even when the person had gone on to say why they
    were writing ("sorry i went to get the kids, anyway the boiler is leaking"), and the answer
    to the boiler was dropped for "No need to say sorry - I'm still here". The apology is only
    the line while every word outside it is a small word - or a word about how the stretch of
    time away went ("sorry ive been quiet, work has been mad"), which names no subject the bot
    can answer: it is the reason for the gap.
    """
    text = " ".join(str(clean or "").lower().replace("\u2019", "'").split())
    if not text:
        return False
    # The errand is the one shape that names its object partly ("sorry i went to get the kids"
    # leaves "the kids"), so it may leave one word of the line's own behind. Everything else
    # may leave none: "sorry i fell asleep at the wheel" and "sorry, i lost track of my
    # medication" name something, and that something is the line.
    errand = bool(STEPPED_AWAY.search(text))
    spare = 1 if errand else 0
    for pattern in (STEPPED_AWAY, ABSENCE, GOT_DRAWN_AWAY, _SORRY_LEAD):
        for _ in range(4):
            match = pattern.search(text)
            if not match or not match.group(0):
                break
            text = (text[:match.start()] + " " + text[match.end():]).strip()
    # A word that turns the page starts the next subject, whatever follows it: "sorry i went
    # to get the kids, anyway the boiler is leaking" is the boiler. Only when something follows
    # it - "sorry, but i got distracted" leaves the "but" behind and is still the gap.
    for match in A_TURN_THE_PAGE.finditer(text):
        if re.search(r"[a-z']", text[match.end():]):
            return False
    left = [word for word in re.findall(r"[a-z']+", text) if word not in A_PAUSE_WORD]
    rest = left[spare:]
    if not rest:
        return True
    if not any(word in A_HOW_THE_TIME_WENT or word in A_GAP_FOR_ILLNESS for word in rest):
        return False
    return len(left) <= spare + 6 and all(
        word in A_HOW_THE_TIME_WENT or word in A_GAP_FOR_ILLNESS
        or word in A_GAP_NAMED_PERSON
        for word in rest)


# The speaker's own absence, with no apology needed: "ive been quiet", "i was away". The absence
# counts only when the line names no subject of its own, which _the_gap_is_all_there_is decides.
SPEAKER_ABSENCE = re.compile(
    r"\b(?:i|ive|i've|im)\b[^.?!]{0,24}?\b(?:been|be|went|gone|was)\s+"
    r"(?:quiet|silent|away|incommunicado|off\s+my\s+phone)\b")
# The apology with no lead at all, because it came after the reason for it ("work has been mad
# so sorry for the silence"). The same words as _SORRY_LEAD without the anchor: this one is not
# the shape of the line, it is a word in it.
AN_APOLOGY_IN_THE_LINE = re.compile(r"\b(?:sorry|apolog(?:y|ies)|apologise|apologize)\b")


def reads_as_pause(clean):
    """True when the line is an apology for the conversation having paused.

    Three shapes say it: what they stepped away for ("sorry, i went to get the kids"), the
    absence itself ("sorry i went quiet", "sorry for the silence", "sorry i havent replied",
    "sorry, been busy", "sorry, my phone died"), and being drawn away ("i got distracted").
    The absence counts only behind an apology, so "my dad has gone quiet since the funeral" is
    still somebody else's line.

    Every one of them counts only while the apology is the whole line: a line that goes on to
    name something ("sorry i got distracted, the boiler is leaking") is that thing's, and the
    pause reply would take the turn from the answer to it.

    The apology does not have to come first. "work has been mad so sorry for the silence" and
    "ive been quiet because work has been mad" are the same line with the reason in front, and
    the chat module's annoyance pool took them on the word "mad" alone and told the person to
    walk it off before replying to anyone. Where the apology and the absence are both in the
    line and nothing else of its own is left, the order does not change what the line is.
    """
    text = " ".join(str(clean or "").lower().replace("\u2019", "'").split())
    if STEPPED_AWAY.search(text) or GOT_DRAWN_AWAY.search(text):
        return _the_gap_is_all_there_is(text)
    if AN_APOLOGY_IN_THE_LINE.search(text) and ABSENCE.search(text):
        return _the_gap_is_all_there_is(text)
    if SPEAKER_ABSENCE.search(text):
        return _the_gap_is_all_there_is(text)
    return False


def _came_back(clean):
    """True when the line is an apology for having stepped away for a moment."""
    return reads_as_pause(clean)


# A line that only points back at the conversation: the person picking the thread back up.
# "as i was saying", "where was i", "so anyway", "sorry, i got cut off". None of them names
# anything of its own, and nothing else reads them: the account-of-the-day pool answered them as
# though they were news ("as i was saying" -> "Sounds alright. Anything good in it?", "sorry, i
# got cut off" -> "Good to hear. What was the best bit?") and the search shrug took "where was i".
POINTS_BACK = re.compile(
    r"(?:as|like)\s+i\s+(?:was|were)\s+saying"
    r"|back\s+to\s+what\s+i\s+was\s+saying"
    r"|as\s+i\s+said"
    r"|where\s+(?:was|were)\s+(?:i|we)"
    r"|(?:got|get|getting)\s+cut\s+off|cut\s+off\s+there"
    r"|(?:i\s+)?got\s+interrupted|was\s+interrupted"
    r"|carry\s+on"
    r"|back\s+again"
    r"|any\s?way|any\s?road")
# The words that carry no subject, so a line made of these and a phrase pointing back is still
# only a line about the conversation: "right, so as i was saying" and "sorry, i got cut off".
A_POINTING_FILLER = frozenset("""
again ah already and any anyway anyroad as at back before but carry earlier er for from haha here
hmm i i'm im in in it just like me my now of off oh ok okay on right said saying so sorry that the
then there this to um up us was we well were with yeah yes you
""".split())
# What a return names the thing it is about with: "as i was saying about the car" has not said the
# thing yet, so the reply asks about it. Only these two, because a leftover after any other word is
# the rest of a sentence, not a thing.
A_THING_MARKER = frozenset("about regarding".split())


def _a_chat_behind_it(memory):
    """True when the person has already said something, so there is a thread to point back at.

    A line that points back is the whole content of the line, so it is a turn about the chat
    itself. On the first line of a chat there is no chat: the composer's own answer to "as i
    said" is "There's nothing earlier for me to go back to: this is your first line", and a
    go-ahead there would be a reply to a turn that never happened. The question is answered in
    one place, `bot/memory/history.py::an_earlier_turn`, and the arbiter asks it of every module's
    reply as well - this is the composer's own use of the same check.
    """
    return history.an_earlier_turn(memory)


def nothing_said_yet(memory):
    """True on a chat's first line; the check itself is `bot/memory/history.py::an_earlier_turn`."""
    return not history.an_earlier_turn(memory)


def nothing_yet_line():
    """The line for a first line whose every candidate answers a turn that never happened."""
    return RETURNED_TO_IT_FIRST[0] if RETURNED_TO_IT_FIRST else ""


def brings_nothing_of_its_own(text):
    """True when the line has no subject of its own, only a point back at the conversation.

    "go on", "carry on", "same as before", "as i was saying", "you told me earlier", "nothing new
    to add then", "sorry, i got cut off", "where were we": every word is a fragment of pointing
    back (`bot/memory/history.py::NO_CONTENT_WORDS`), and there is nothing in the line for a reply
    to be about. A line with any other word in it brings something of its own - "the same goes for
    the bathroom" names the bathroom, "weve booked a week in cornwall" names the week - and a
    first line that brings something is answered like any other line, even by a pool written for a
    conversation in progress ("Nice one. Is it soon, or have you got a while yet?").
    """
    return history.brings_nothing_of_its_own(text)


def assumes_an_earlier_turn(reply):
    """Whether the reply answers something the person has said earlier in this chat.

    The frames are one list (`bot/memory/history.py::ANSWERS_AN_EARLIER_TURN`) beside the ones
    that point back at the chat, and the reading is `history.a_past_that_is_not_there`: "sorry, i
    got cut off" as the first thing in a chat was answered "Good to hear. What was the best bit?",
    "as i was saying" by "Sounds alright. Anything good in it?", and "carry on" by "Thanks for
    telling me - I'm here if you want to dig into any of that." The composer's own first-line
    lines ("Go on - what about the car?", "Nothing to catch up on yet") are not frames that assume
    a turn: they name what the person just said, which is why this is a list of frames and not a
    smell test. A caller that has already established the line brings nothing of its own asks for
    the frames alone, which is what the empty line here means.
    """
    return history.a_past_that_is_not_there(reply, {}, "")


def reads_as_a_return(clean):
    """What is left of a line that picks the thread back up: None, "" or the thing it names.

    None means the line is not a return. "" is a return with nothing of its own left in it - "as
    i was saying", "where was i", "right, so anyway" - and the composer answers it by saying go
    on. Anything else is a return that names the thing it is about, usually after "about" ("as i
    was saying about the car"): the person has not said the thing yet, so the answer asks about
    it rather than guessing.

    It counts only while the rest of the line is small words and at most a short thing, which is
    the same gate the apology above uses: "as i said, the boiler is leaking" names the boiler,
    and that is the boiler's line, not the conversation's.
    """
    text = " ".join(str(clean or "").lower().replace("\u2019", "'").split())
    if not text or not POINTS_BACK.search(text):
        return None
    left = text
    for _ in range(3):
        match = POINTS_BACK.search(left)
        if not match or not match.group(0):
            break
        left = (left[:match.start()] + " " + left[match.end():]).strip()
    tokens = [word for word in (re.sub(r"[^a-z0-9']", "", word) for word in left.split()) if word]
    marker = next((i for i, word in enumerate(tokens) if word in A_THING_MARKER), None)
    if marker is None:
        return "" if all(word in A_POINTING_FILLER for word in tokens) else None
    if not all(word in A_POINTING_FILLER for word in tokens[:marker]):
        return None
    thing = " ".join(word for word in tokens[marker + 1:] if word).strip(" ,.-\u2026")
    if not thing or len(thing.split()) > 4:
        return None
    return thing


# The words an apology for asking is made of, and nothing else: "sorry to bother you", "sorry to
# keep asking", "apologies for the silly question". A line that goes past these names something
# of its own, and that something is what the line is about.
SORRY_ASKING = re.compile(
    r"\b(?:sorry|apolog(?:y|ies)|apologise|apologize)\b"
    r"[^.?!]{0,30}?"
    r"\b(?:bother\w*|pester\w*|nagging|ask\w*|questions?|pain|nuisance|hassle|trouble\w*|"
    r"keep\s+(?:asking|going|coming|picking|on)|one\s+more|another\s+one|essay|"
    r"ramble\w*|going\s+on|dumping|moan\w*|interrupt\w*|taking\s+up)\b")


def _only_manners(clean, allowed):
    """True when every word of the line is in the allowed set, so it names nothing of its own."""
    words = re.findall(r"[a-z']+", clean.lower())
    return bool(words) and all(word in allowed for word in words)


def _sorry_for_asking(clean):
    """True when the line is an apology for asking and nothing else."""
    text = clean.lower()
    return bool(SORRY_ASKING.search(text)) and _only_manners(text, MANNERS_ONLY)


# The same manners without the apology word in front: the person checks that they are not a
# nuisance instead of apologising for it. "am i bothering you", "am i bugging you", "am i asking
# too much", "do you mind me asking", "should i stop asking", "is this a waste of your time".
# It is one social move, so it gets the one pool the apology gets. Without this the line reached
# the search shrug - "That's beyond what I know well, sorry. Searching for it will turn up better
# sources" - which searches the web for whether the bot minds being asked.
AM_I_A_NUISANCE = re.compile(
    r"(?<![a-z])(?:am|are|is)\s+(?:i|we|this|it)(?![a-z])[^.?!]{0,25}?"
    r"(?<![a-z])(?:bother\w*|bugging|annoy\w*|irritat\w*|pester\w*|in the way|too much|"
    r"a waste of|taking (?:up )?(?:too much|your)|keeping you|too many questions|"
    r"asking a lot)(?![a-z])"
    r"|(?<![a-z])(?:do|would|will|did)\s+you\s+mind(?![a-z])[^.?!]{0,25}?"
    r"(?<![a-z])(?:me asking|my asking|if i ask|i ask)(?![a-z])"
    r"|(?<![a-z])(?:should|shall|do) i (?:stop|quit) asking(?![a-z])")
# Every word such a line can be made of without naming anything of its own. "am i bothering you
# about the boiler" is the boiler's line, and this set is what keeps it out.
NUISANCE_ONLY = MANNERS_ONLY | frozenset("""
    am are is was were bugging bug annoy annoying annoyed irritating irritated irritate
    pester pestering way waste mind minding stop quit should shall if ask asking
    taking take up long much many too lot lots questions question time in way at all
    """.split())


def _am_i_a_nuisance(clean):
    """True when the line only checks whether the person is being a nuisance."""
    text = " ".join(str(clean or "").lower().split())
    return bool(AM_I_A_NUISANCE.search(text)) and _only_manners(text, NUISANCE_ONLY)


# "thanks", "thank you", "cheers", "ta" - and the word people put in front of it when they mean it
# ("ok thanks, that worked", "ah thanks"). What is left after it is the outcome.
THANKS_OPENS = re.compile(
    r"^(?:(?:ok|okay|ah|oh|right|great|brilliant|nice|lovely|perfect)\b[\s,!.]*)?"
    r"(?:thanks|thank\s+you|thankyou|thank-you|cheers|ta)\b[\s,!.]*(?P<said>.*)$")
# A question after the thanks is a new ask, not an outcome: "thanks, can you do the same for the
# shed" wants an answer about the shed, and "Glad to hear it" would step over it.
# Which way the outcome went. "Thanks, it's worse today" is somebody coming back with bad news, and
# "Good. Thanks for letting me know." is the wrong answer to it; the mood reader is no help, because
# "worse", "no better", "came back" and "still" are not mood words for a whole line - they are
# words for how a thing they tried went.
THANKS_WENT_BADLY = re.compile(
    r"\b(?:worse|worst|no\s+better|not\s+better|no\s+change|still|came\s+back|back\s+again|"
    r"hurts?|hurting|sorer?|failed|nothing|didnt|didn't|doesnt|doesn't|wont|won't|"
    r"can'?t|cant|hasnt|hasn't|"
    # The thing coming back is the commonest bad news there is, and it was read as good news:
    # "thanks, the pain is back" got "Glad to hear it - and thanks for coming back to say so."
    # "came back" and "back again" were here but not the bare return, which is how most people
    # say it. A flare and a return are the same news in other words.
    r"(?:is|are|was|were|has|have|had|its|it's|im|i'm|they're|theyre)\s+back|"
    r"(?:come|comes|coming|came)\s+back|flares?|flared|flaring|\breturned|returning|"
    r"back\s+to\s+square\s+one)\b")
# But "back" on its own is good news when it says back to how it should be: "thanks, its back to
# normal now" and "thanks, its back to how it was" are exactly what this pool is for, and the
# return shape above would turn them into trouble. Same for "still", which is in the list for
# "still the same" and not for "still keeping well".
THANKS_GOOD_AGAIN = re.compile(
    r"\bback\s+to\s+(?:normal|how\s+it\s+was|where\s+it\s+was|itself|its\s+old\s+self|"
    r"being\s+normal)\b|"
    r"\bstill\s+(?:keeping\s+|doing\s+|going\s+)?(?:good|well|fine|great|ok|okay|improving|"
    r"getting\s+better|on\s+the\s+mend|strong)\b|"
    r"\bstill\s+(?:a\s+)?bit\s+(?:sore|stiff|tired)\s+but\b")
# What the bot says to bad news that came back behind a thank-you. The thanks pools above are
# all good news, and everything below them answers a line about something the person has not
# named yet, so "thanks, its still stinging" reached the neutral pool and got "Happy to help"
# and "thanks, its worse today" got the echo ("Noted: it's worse today"). None of these lines
# claims to know what is wrong; each says sorry and hands the next detail back, which is what a
# friend does and what a card needs to answer properly.
THANKS_NO_BETTER = (
    "Sorry it hasn't settled. What's it doing now?",
    "Sorry to hear that — thanks for coming back with it.",
    "That's a nuisance. What's the worst of it now?",
    "Sorry it's no better yet. Say what's changed and I'll go again.",
    "Right, still not right. What's it doing now?",
)
THANKS_TAKES_A_QUESTION = re.compile(
    r"\b(?:can|could|would|should|will|shall|any\s+idea|what|how|why|when|where|who|"
    r"is\s+it|do\s+i|should\s+i)\b")


def _thanks_then_said(clean):
    """The outcome they came back to tell me after a thank-you, or "" when there is none."""
    match = THANKS_OPENS.match(clean.strip().rstrip(".!").strip())
    if not match:
        return ""
    said = match.group("said").strip(" .,!;:")
    if len(re.findall(r"[a-z']+", said)) < 2:
        return ""
    # A question word inside the outcome is not an ask: "thanks, its back to how it was" and
    # "thanks, its back to where it was" are the good news this pool is for, and the bare "how" and
    # "where" in them were read as a question, so the search hedge answered the report. Take the
    # outcome phrase out and read what is left, which is what decides it: "thanks, still a bit sore
    # but much better" has no question left, and "thanks, worse today, can i take more painkillers"
    # still has one.
    if THANKS_TAKES_A_QUESTION.search(THANKS_GOOD_AGAIN.sub(" ", said)):
        return ""
    return said


def _thanks_news_went_badly(clean):
    """The outcome when a thank-you came back with bad news, or "" when it did not.

    A thank-you with something after it is the person telling the bot how the thing it answered
    went, and that something is the news. "Thanks, its still soaking through" was read as thanks
    and nothing else by the kind reader, so the thank-you pool thanked them back. The outcome is
    the line whenever it says the thing did not come right, and this is the one test both places
    ask, so they cannot disagree.
    """
    said = _thanks_then_said(clean)
    if not said or THANKS_GOOD_AGAIN.search(said):
        return ""
    if THANKS_WENT_BADLY.search(said):
        return said
    words = re.findall(r"[a-z']+", said)
    return said if _mood(words, said) == "negative" else ""


# "Good to know" and the rest of its family: an acknowledgement with no thank-you in it. Every
# word of it is a manners word, so `_only_manners` reads it, but there is no thanks for the
# thanks reading to find and no question in it for the hedge to answer - and the hedge is what it
# got: "good to know" was answered "I'm not sure about that one, sorry - I'd rather not guess. A
# quick search online will get you a solid answer", and "good to know thanks" the same, one word
# of thanks later. `know` is the question word that made the line into an ask, so the whole line
# has to be this shape, anchored at both ends: "how do i know if its cooked" and "do you know
# where i can get one" are asks and are not in it.
_ACKNOWLEDGES_ALONE = re.compile(
    r"^(?:(?:oh|ok|okay|right|well|ah|aye|yes|yeah|great|good|nice|cool|brilliant|lovely|"
    r"perfect|interesting|thats|that's|that|it's|its|thanks|thank\s+you|cheers|ta|"
    r"ill|i'll|i|will|do)[\s,]+)*"
    r"(?:(?:good|great|useful|handy|nice|lovely|brilliant|perfect|helpful|interesting|"
    r"reassuring|worth)\s+)?(?:to\s+know|knowing|to\s+hear|to\s+see)\b"
    r"(?:[\s,]+(?:that|it|this|then|so|now|thanks|thank\s+you|cheers|ta|mate|for\s+that))*"
    r"[\s.!]*$")


def _acknowledges_alone(clean):
    """True when the whole line is "good to know" and nothing else.

    Named apart from the thanks reading because there is no thanks in it: the reply is the same
    short one, and the reason it must not reach the hedge is different. Nobody asks the bot to
    search for anything when they say it.
    """
    return bool(_ACKNOWLEDGES_ALONE.match(" ".join(str(clean or "").lower().split())))


def _thanks_with_more(clean):
    """True when the line is thanks and nothing else, however many words it takes to say it."""
    text = clean.lower()
    if "?" in text:
        return False
    words = set(re.findall(r"[a-z']+", text))
    if not (words & THANK_WORDS):
        return False
    return _only_manners(text, THANKS_ONLY)


def reading(text, memory):
    """(kind, target) for a line the composer answers itself, or ("", ()) for an ordinary one.

    One place for the composer to say what it is doing with a line the rest of the app must not
    answer as small talk. `THREAD`'s target is the one continuation, as text. The arbiter asks
    this once per turn and decides only when a module keeps the turn instead; adding a third
    kind is one branch here and one there, never a second scanning loop in the router.
    """
    try:
        continuation = careful(text, memory)
    except Exception:  # noqa: BLE001 - a composer that cannot read changes no reply
        continuation = None
    if continuation:
        return (CARE_THREAD if _a_care_thread(memory) else THREAD), (continuation,)
    try:
        if leaving.reads_as_leaving(" ".join(str(text or "").lower().split())):
            return leaving.LEAVING, ()
    except Exception:  # noqa: BLE001 - a reading that fails just adds no kind
        return "", ()
    try:
        # Not inside a thread that has its own voice: after a condolence the listening line is
        # what the composer answers with ("I'm listening - say more if it helps") and a breezy
        # "No bother at all - go on" is the wrong voice for it, and inside a live crisis the
        # thread's own line is the answer.
        if (not _grief_thread(memory) and not in_a_safety_thread(memory)
                and reads_as_pause(" ".join(str(text or "").lower().split()))):
            return PAUSE, ()
        # A line that only points back at the conversation is the same kind for the arbiter's
        # purpose - no topic entry may take it back on a word of it ("where was i" was answered
        # with the search shrug, "as i was saying" with "Sounds alright") - and the wording is a
        # second pool (`RETURNED_TO_IT`), chosen in fallback_chain beside this one.
        if (not _grief_thread(memory) and not in_a_safety_thread(memory)
                and _a_chat_behind_it(memory)
                and reads_as_a_return(text) is not None):
            return PAUSE, ()
    except Exception:  # noqa: BLE001 - a reading that fails just adds no kind
        return "", ()
    return "", ()


def _advice_thread_is_about_the_body(memory):
    """True when the advice this thread is reporting on was about the person's body.

    The four pools that say "get it looked at" are for a symptom, and they read wrong after a
    pan of pasta or a boiler. The last few lines the person said decide it, because the advice
    may be the end of a thread that opened several turns earlier.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-6:]
    for turn in reversed(turns):
        line = str(turn.get("user") or "").lower()
        if line and _worry_is_about_the_body(line, line.split()):
            return True
    return False


def _a_step_word_in(words, steps):
    """Whether the line names something the answer named."""
    for word in words:
        if str(word).replace("'", "").strip(".,!?;:-\u2014") in steps:
            return True
    return False


def _a_report_on_the_advice(clean, words, about_the_body=True, the_lot_ok=False, steps=NO_STEP):
    """The pool for a report on advice just given, or None.

    Only a line that is nothing but the report counts: every word has to be one a report uses,
    so "i tried that new cafe" is a place and "it helped my mum" is about her, and both are left
    to the pools below. Apostrophes are dropped first, because "ive been doing it" is how people
    type and it is the same report.

    A word the answer itself used is a report word too: the answer's "wipe it out with a damp
    cloth" is where "i wiped it and now its worse" comes from, and no list of report words could
    have it. `steps` is what the answer said (`_the_words_in`), so the line has to be
    built from words of the advice and words a report uses, and nothing else.
    """
    if "?" in clean or len(words) > 14:
        return None
    if {str(word).strip(".,!?;:-\u2014'") for word in words} & THANKS_WORDS:
        # "thanks, that worked" is a thank-you with a report inside it, and the thanks pool says
        # the warm thing back ("Any time."). Read as a report it was answered "Good - that is the
        # end of it, then.", which is the bot closing its own advice instead of taking the thanks.
        return None
    for word in words:
        bare = str(word).replace("'", "").strip(".,!?;:-\u2014")
        if bare in REPORT_FILLER or bare in steps or bare in REPORT_VERDICT_WORD:
            continue
        return None
    # "none of that worked" holds "that worked" inside it, so the no-change report is read
    # before the one that says it is done: the reading of a report is the whole line, and a
    # line that says it did not work is not a line that says it did.
    pools = ((TRIED_NO_CHANGE, TRIED_NO_CHANGE_REPLIES, TRIED_NO_CHANGE_ELSEWHERE),
             (TRIED_WORSE, TRIED_WORSE_REPLIES, TRIED_WORSE_ELSEWHERE),
             (REPORT_NOW_FINE, TRIED_SORTED_REPLIES, TRIED_SORTED_REPLIES),
             (TRIED_HELPED, TRIED_HELPED_REPLIES, TRIED_HELPED_ELSEWHERE),
             # A "still" that has already been read as worse, sorted or helped is not this one:
             # "its still working" is the helped pool above, and only a still with no word for a
             # good outcome is the trouble that has not moved.
             (STILL_THE_TROUBLE, TRIED_NO_CHANGE_REPLIES, TRIED_NO_CHANGE_ELSEWHERE),
             (TRIED_IT, TRIED_IT_REPLIES, TRIED_IT_REPLIES),
             (TRIED_THAT_ONLY, TRIED_IT_REPLIES, TRIED_IT_REPLIES),
             (DONE_IT, TRIED_IT_REPLIES, TRIED_IT_REPLIES))
    # "ive tried everything" is the no-change outcome said about the whole of it rather than
    # about one go, so it gets the no-change wording: "Any change since you started?" asks a
    # person who has finished trying whether they have noticed anything yet ("im 34 and i still
    # bite my nails" / "ive tried everything").
    if the_lot_ok:
        pools = pools + ((TRIED_THE_LOT, TRIED_NO_CHANGE_REPLIES, TRIED_NO_CHANGE_ELSEWHERE),)
    for shape, on_the_body, elsewhere in pools:
        if shape is STILL_THE_TROUBLE and not _a_step_word_in(words, steps):
            # "still nothing" is somebody waiting on a text that has not come ("i texted him back
            # two weeks ago" / "still nothing"), not a step that did not work. A "still" report has
            # to name something the answer named, which is what a real one does: "still dripping"
            # after an answer about a dripping tap.
            continue
        if shape.search(clean):
            return on_the_body if about_the_body else elsewhere
    return None


def _the_outcome_of_the_advice(memory, clean, words):
    """The pool for a report on the advice in the last answer, or None.

    The answer has to have been a long one - that is what makes it advice a person could act on
    and report back on - and the thread must not be a loss, where "i tried that" is about the
    person who died and the outcome pools would be grotesque. Read in one place, because the
    reply and the presence of a reply have to agree: the arbiter asks the same question through
    `takes_as_it_comes` before a module that would answer the report with a stock line gets the
    turn ("its not helping" was answered "Alright then - good luck with it.").
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    last = str(turns[-1].get("bot") or "") if turns else ""
    # The check-in question ("How is it going with it so far?") is the bot's line right after
    # the advice, so a report that answers it is still a report on the advice: the cue is looked
    # for in the last few of the bot's lines, not only the one above.
    seen = [str(turn.get("bot") or "") for turn in turns[-ADVICE_TURNS:]]
    if not any(_advice_in(line) for line in seen):
        return None
    if _in_a_loss_thread(memory) or _grief_thread(memory):
        return None
    if len(last) < ADVICE_LENGTH and not ADVICE_CUE.search(last.lower()):
        # A line that is nothing but the report says what it is, and the tight word list is the
        # guard then rather than the length: "and if that doesnt work" came after a thirty-word
        # bit of the same advice, and it was answered as a fault to troubleshoot ("Ugh, those are
        # fiddly. How long has it been like that?") because the answer was three characters short
        # of the long-advice gate. A report with words of its own still needs the long answer -
        # unless the short answer names something to do (`ADVICE_CUE`), in which case it is
        # advice whatever its length, and unless the advice is one line further back behind the
        # check-in question.
        earlier = any(_advice_in(line) for line in seen[:-1])
        if not earlier and (len(words) > 6 or len(last) < ADVICE_LENGTH_BARE):
            return None
    return _a_report_on_the_advice(clean, words, _advice_thread_is_about_the_body(memory),
                                   the_lot_ok=not reject.offers_a_choice(memory),
                                   steps=_the_words_in(the_advice(memory)))


def the_advice(memory):
    """The bot's own advice this thread is reporting on, lower case, or "" when there is none."""
    for turn in reversed([t for t in (memory.get("turns") or []) if isinstance(t, dict)]
                         [-ADVICE_TURNS:]):
        reply = str(turn.get("bot") or "").lower()
        if _advice_in(reply):
            return reply
    return ""


def reads_as_a_report(text, memory):
    """Read by the arbiter: is this line a report on the advice just given?

    The same question `_the_outcome_of_the_advice` answers for the reply, published so the router
    can ask it without a second reading of the line. See `TAKES_AS_IT_COMES`.
    """
    clean = " ".join(str(text or "").lower().split())
    try:
        return bool(_the_outcome_of_the_advice(memory, clean, clean.split()))
    except Exception:  # noqa: BLE001 - a reading that fails claims no turn
        return False


def the_report_reply(text, memory):
    """The reply this composer makes to a report on the advice just given, or None.

    Read by the arbiter, so that a report on the advice keeps the turn the composer's reading of
    the line earned it: the module that proposes the reply sits under the floor (the composer
    only fills the floor), and a pool line from a module above it would otherwise stand it down.
    The same call on the same thread gives the same words - `_choose` seeds on the advice and the
    thread - so the arbiter can compare what was proposed with what the report's answer is,
    without a second copy of the reading or of the wording.
    """
    clean = " ".join(str(text or "").lower().split())
    try:
        return _after_advice(memory, clean, clean.split())
    except Exception:  # noqa: BLE001 - a reading that fails offers no reply
        return None


def a_report_that_says_something(text, memory):
    """Does the composer answer a report on the advice with something other than a status question?

    The pool that asks "How is it going with it so far?" is the lightest of the report replies,
    and it is the one case where the composer should not take the turn off a module above it: "ok
    done that" after the energy bill entry is answered with the next part of that entry ("Ask your
    supplier in writing for the standing charge and unit rate ... cheapest tariff"), and asking
    the person how it is going instead is the same fault as a goodbye. A report that is answered
    with an outcome - worse, no change, sorted - does say something, and keeps the turn.
    """
    reply = the_report_reply(text, memory)
    return bool(reply) and reply not in TRIED_IT_REPLIES


def _after_advice(memory, clean, words):
    """The reply for a report on the advice in the last answer, or None."""
    step = _the_next_move_after_the_advice(memory, clean, words)
    if step:
        return step
    pool = _the_outcome_of_the_advice(memory, clean, words)
    if not pool:
        return None
    # Seeded on the advice, not on the report. "i tried that and it didnt work" is the same seven
    # words in every thread, so seeding the pool on the report gave a person the same sentence
    # after a sink, a kettle and a pan of mince - STYLE.md's worst tell. The advice is what makes
    # this thread different from the next one, so it is what the wording is drawn from.
    return _choose(pool, memory, clean, seed_text=the_advice(memory) or clean)


def _the_answer_above_already_says_what_to_do(turns, memory):
    """Did the card answer above already say what to do when the answer comes back no?

    A deposit card that says "ask in writing for an itemised list, and use the protection scheme"
    is the reply to the landlord saying no as well as to the question, and the store hands it back
    ("Same answer, and it covers this: ..."). Only an entry answer counts: advice that was the
    composer's own has no card behind it to come back with.
    """
    if not turns:
        return False
    if not (memory.get("entry_answer") or memory.get("entry_answers")):
        return False
    return bool(AN_ANSWER_ABOUT_A_NO.search(str(turns[-1].get("bot") or "")))


def _a_thread_about_how_somebody_treats_them(turns):
    """Whether the chat is on somebody's conduct rather than on a request for something.

    "im being bullied at work" and "my manager keeps touching me" are things done to the person,
    and what the no means there is that the move is a record and a route, not a smaller ask. The
    words are the composer's own grievance vocabulary (`GRIEVANCE_HARM`), read over the person's
    own lines, so a new harm word reaches this guard and the grievance pool together.
    """
    for turn in turns[-4:]:
        said = set(re.findall(r"[a-z']+", str(turn.get("user") or "").lower()))
        if TREATMENT_HARM & said:
            return True
    return False


def _an_answer_above(turns):
    """Did the bot answer above this line, so that the no is how that answer went?

    An ack is four or five words ("Got it — the landlord said no" is longer, but the bot's own
    answers run to full sentences); an answer is a thing somebody can go and try.
    """
    bot = str((turns[-1].get("bot") if turns else "") or "")
    return len(bot.split()) >= 8


def _a_refusal_to_answer(clean, memory, words=None):
    """The pool for a line that reports somebody else's no, or None.

    The person did what the answer said and it was turned down - by a boss, a landlord, a bank, a
    council, or the person they live with. The composer has the answer to that and the ack does
    not: said back it is "Got it - your boss said no", which is the person's own line with nothing
    added. Read in one place so the reply and the claim cannot drift apart (`reads_as_a_refusal`
    asks the same question for the arbiter).

    Narrow on purpose: no question mark, fifteen words at most, a party who can be asked again or
    an answer above for the no to be about, no no from somebody treating them, and nothing that
    reads as a fault to repair. A thread with a death or a live safety answer keeps its own line.
    """
    if "?" in str(clean or ""):
        return None
    if not REFUSED.search(clean):
        return None
    # The speaker's own no is a decision they made, not one made against them: "my son wants a
    # phone / i said no" is a parent holding a line, and telling them to ask again is the bot not
    # listening. Nobody to ask, either: "why did my boss say no" is a question about the no.
    if OWN_NO.search(clean) or ASKS_WHY.search(clean):
        return None
    # A no in the future, or in a case they are working out, is not one they were given.
    matched = REFUSED.search(clean)
    if matched and HYPOTHETICAL.search(str(clean or "")[:matched.start()]):
        return None
    words = clean.split() if words is None else words
    if len(words) > 15:
        return None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not REFUSED_PARTY.search(clean) and not _an_answer_above(turns):
        # Nobody is named who could say yes next time, and there is no answer above this line for
        # the no to be about: "she said no" on its own is a person turned down in their own life,
        # and "ask once more what would make it a yes" is the wrong thing to say about it.
        return None
    if REFUSED_NOT.search(clean) or REFUSED_FAMILY.search(clean):
        return None
    # A written thing says no what is inside it, and nobody was refused: "the invite says no dress
    # code" came back as advice to ask again about a wedding's dress code.
    if REFUSED_NO_OBJECT.search(clean):
        return None
    # The card above was the step for a no already - "put it in writing, name what you disagree
    # with" - and the store hands that answer back. Asking once more is the weaker line after it.
    if _the_answer_above_already_says_what_to_do(turns, memory):
        return None
    # A chat about somebody's conduct is not an ask that can be trimmed: there is no smaller
    # version of "stop touching me", and the card above already gave the record and the route.
    if _a_thread_about_how_somebody_treats_them(turns):
        return None
    try:
        if trouble.reads_as_trouble(clean):
            return None
        if _in_a_loss_thread(memory) or _grief_thread(memory) or in_a_safety_thread(memory):
            return None
    except Exception:  # noqa: BLE001 - a reading that fails claims no turn
        return None
    if turns and _in_a_pool(str(turns[-1].get("bot") or ""), (REFUSED_REPLIES,)):
        # The pool has already said this once, so saying the same thing in other wording is the
        # bot repeating itself: the second no in a thread is met by the detail it brings.
        return None
    return REFUSED_REPLIES


def reads_as_a_refusal(text, memory):
    """Read by the arbiter: is this line somebody else's no, which the composer answers?"""
    clean = " ".join(str(text or "").lower().split())
    try:
        return bool(_a_refusal_to_answer(clean, memory, clean.split()))
    except Exception:  # noqa: BLE001 - a reading that fails claims no turn
        return False


def _the_next_move_after_the_advice(memory, clean, words):
    """The step the answer itself named, for a report that the advice did not work, or None.

    "Then stop doing more of the same and change one thing instead" is advice to change, told to
    somebody who has just changed and reported back. When the answer ends on who to go to if the
    advice is not enough ("ask a GP", "call a Gas Safe engineer"), that sentence is the next move
    and the only thing left to say. bot/memory/repeat owns the reading of what was said, so the
    sentence comes from there; with no step to give, the pools below stand as they are.

    The length gate the outcome pools use is not applied here: an answer of thirty words that ends
    on a next step is still advice with a next step, and it is the sentence that matters.
    """
    pool = _a_report_on_the_advice(clean, words, _advice_thread_is_about_the_body(memory),
                                   the_lot_ok=not reject.offers_a_choice(memory),
                                   steps=_the_words_in(the_advice(memory)))
    if pool not in (TRIED_NO_CHANGE, TRIED_NO_CHANGE_ELSEWHERE):
        return None  # "it helped" or "it made it worse" is answered by the outcome itself
    if _in_a_loss_thread(memory) or _grief_thread(memory):
        return None
    try:
        return repeat.the_next_move(memory, clean) or None
    except Exception:  # noqa: BLE001 - a memory layer that cannot answer adds nothing
        return None


def _a_care_thread(memory):
    """True when the safety answer this thread continues was first aid, not a crisis line."""
    answer = _thread_answer(memory)
    if not answer:
        return False
    return not any(word in answer for word in CRISIS_WORDS)


def in_a_safety_thread(memory):
    """True when the bot's last word in this stretch was a safety answer.

    Read by the arbiter: an apology for the pause inside a live crisis keeps the thread's own
    line ("I'm listening - say more if it helps"), where the light "No bother at all - go on"
    is the wrong voice for a person who has just said something that frightened them.
    """
    return bool(_thread_answer(memory))


def _thread_answer(memory):
    """The bot's safety answer this thread continues, lower case, or "" when there is none.

    A thread holds across the composer's own continuations and across an entry answer that is
    still about the emergency - the burn's own blister line after "should i pop the blister" -
    because that entry is the thread going on, and losing the thread there took the next line
    off it: "can i put cream on it" was answered from the measles entry once the burn's answer
    was no longer in hand. Any answer that says nothing of the emergency ends it.
    """
    window = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-THREAD_TURNS:]
    answer = ""
    for index in range(len(window) - 1, -1, -1):
        if window[index].get("module") == "safety":
            answer = str(window[index].get("bot") or "").lower()
            window = window[index + 1:]
            break
        if window[index].get("module") == FALLBACK_MODULE:
            continue
    if not answer:
        return ""
    for turn in window:
        if turn.get("module") == FALLBACK_MODULE:
            continue
        if _words_kept(turn.get("bot"), answer) >= THE_THREAD_KEPT:
            continue
        return ""
    return answer


# --- a follow-up about the thing the bot just answered -------------------------------------
# The arbiter keeps a first-aid thread over a topic entry only when the line is a question about
# something the last answer named; the words that decide it live here, with the rest of the
# reading, so the arbiter stays a chooser with no vocabulary of its own (apt-lime, #1961).

OWN_THING = re.compile(r"\b(?:my|our|his|her|their)\s+(\w+)")
# A thing the line brings in right after the shared word: "blood out of a shirt" is a laundry
# question, not another line about the nose that bled, and so is "blood stains out of cotton"
# with no article at all. The preposition is what makes it a new object, so the article is
# optional: a plain ask ("can i pop the blister") has no preposition in front of the noun.
CLAUSE_END = re.compile(r"[;,.?!]|\b(?:and|but|then|so|because|while|which|who)\b")
AFTER_THING = re.compile(r"\s+(?:out\s+of|out|off|from|in|into|on|onto|over|under|"
                         r"with|about)\s+(?:(?:a|an|the|some|another)\s+)?(\w+)")
ASK_WORD = re.compile(r"\b(?:can|could|should|shall|do|does|did|is|are|will|would|may|"
                      r"might|what|whats|how|hows|when|where|why|which|am|ok|okay)\b")


def asks_about_the_last_answer(line, last, own=()):
    """True when the line asks about something the bot's last answer named.

    It has to be an ask: "can i pop the blister" after the scald answer is a question about the
    burn, while "chest pain again" is the person saying the same thing and the health entry
    answers it. And only a word long enough to be a subject counts ("blister", "nosebleed"), so
    an ordinary follow-up cannot match on a common word and take a topic entry's turn.

    The used word also has to be the thing the line is about. A first-aid answer is a paragraph,
    so it shares some word with almost anything: "my running shoes give me blisters what do i do"
    after a scald shares "blisters", "water" and "running" with the burn answer, and both of the
    lines below are about something else the person has just brought in. Three readings keep
    those with their entry:

    - the line names other subjects as well (`own`, the topics its own words point at). "my water
      bill is huge" is money and "my running shoes" is fitness, so a line carrying more than its
      one subject has moved on to a new thing and its entry has the better claim.
    - the line says "my <something>" that is not the shared word ("should i take ibuprofen for my
      headache" after a nosebleed is about the headache).
    - the line puts the shared word in front of a thing of its own ("how do i get blood out of a
      shirt" after a nosebleed is a laundry question, and the stain is in the shirt, not in the
      nose; "blood stains out of cotton" is the same line without the article).

    smooth-lark found the last one at the head of this rule: `blood` is named by the nosebleed
    answer, one subject, no "my <thing>", so every test above passed while the laundry entry lost
    its turn to a care continuation that said nothing about the shirt.
    """
    if not line or not last:
        return False
    text = str(line).lower()
    if "?" not in text and not ASK_WORD.search(text):
        return False
    if len(set(own)) > 1:
        return False
    named = set(OWN_THING.findall(text))
    for word in _words(text):
        if len(word) < 5 or word in PLAIN_WORDS:
            continue
        if word not in last:
            continue
        if named and word not in named:
            # The line says "my <something else>", so it is not about the thing just answered.
            return False
        for said in re.finditer(r"\b" + re.escape(word) + r"\b", text):
            # The rest of the clause, not the whole line: a new object in a later clause is
            # another question, and the clause it sits in already reads as an ask.
            clause = CLAUSE_END.split(text[said.end():], 1)[0]
            brought_in = AFTER_THING.search(clause)
            if not brought_in:
                continue
            thing = brought_in.group(1)
            if len(thing) >= 4 and thing not in PLAIN_WORDS and thing not in last:
                # "blood out of a shirt": the thing the line is really about is the shirt.
                return False
        return True
    return False


def asks_about_a_care_answer(line, last, memory, own=()):
    """True when the line asks about something the care thread has named, else False.

    `asks_about_the_last_answer` reads one reply, and inside a care thread that reply is a pool
    line: after a scald and "should i cover it" the bot's last word was "Don't put anything on a
    burn - not butter, not cream, not ice. Twenty minutes under cool running water, then a loose
    clean dressing", which never says "blister". So "can i pop the blister" shared nothing with
    it and the blister-plaster entry (padded plaster, short stretches in the shoes) took the
    turn over the burn's own answer - and once that entry had the turn the thread was over, so
    the next line ("how long will it take") was answered by the measles entry's infectious
    period. The answer that opened the thread is the one that names the thing - "a burn that
    blisters or is on the face, hands or joints should be seen" - so both are read, and only
    the care thread's own answer is added: an ordinary conversation is unchanged.
    """
    if asks_about_the_last_answer(line, last, own):
        return True
    answer = _thread_answer(memory or {})
    if not answer or answer == str(last or "").lower():
        return False
    return asks_about_the_last_answer(line, answer, own)


def how_much_of_the_answer_kept(reply, memory):
    """How many of the care thread's own answer words a reply says back, or 0.

    Inside a care thread the person asks about the thing the bot has just answered, and two
    candidates can both be on topic: the composer's continuation, which is drawn from the
    thread's pool, and an entry that matched one word of the line. Which one continues the
    conversation is not a matter of priority - it is a matter of whether the reply is about the
    same thing:

        i burnt my hand on the oven / its a blister now / should i cover it / can i pop the blister
          answers:  "Don't pop it: cover the blister with a padded blister plaster and wear the
                     shoes for short stretches"                     (ten of the burn's words: 3)
          greeting: "Don't pop it. A blister is a sterile dressing of its own; cover it loosely
                     and let it settle"                            (ten of the burn's words: 10)
        ... / should i cover the blister
          answers:  "Cover it with a clean non-fluffy dressing and leave it alone: don't pop it"
                                                                     (3 - and it is the answer)
          greeting: "Keep an eye on it and tell me if anything changes"  (0)

    So the count separates the shoe answer (another person's blister) from the burn's own, and
    it keeps the good entry answer where the composer's pool line says nothing about it. It is a
    reading, not a decision: the arbiter is the one that chooses.
    """
    answer = _thread_answer(memory or {})
    if not answer:
        return 0
    return _words_kept(reply, answer)


def _words_kept(reply, answer):
    """How many of an answer's own words a reply says back, or 0.

    The count behind `how_much_of_the_answer_kept`, and the test for whether a reply is still
    about the thread's thing: an entry answer that says three of the emergency's words back is
    following the thread ("a burn blister is a sterile dressing of its own; cover it loosely"),
    where one about another subject says none of them ("leave the shoes off for short
    stretches"). Reading it here keeps one number for both questions.
    """
    said = set(_words(str(answer or "").lower()))
    return len({word for word in _words(str(reply or "").lower())
                if len(word) >= 5 and word in said})


# How much of the thread's answer an intervening reply has to say back to be the thread going on
# rather than the end of it. Three is what the burn's own entry keeps ("burn", "blister",
# "cover"), and what an answer about another subject does not: a line about a shoe rubbing a
# blister shares "blister" and nothing else.
THE_THREAD_KEPT = 3


def careful(text, memory):
    """The careful continuation a line inside a safety thread gets, or None.

    `reply_for` gives it too, but a light module may propose a reply to the same line and win
    on PRIORITY ("im scared" twice in a row deserves the thread, not a reframe about worry).
    The arbiter reads this to keep the thread (bot/modules/arbiter.py), so the wording and the
    judgement of what still counts as the same thread live here, in the composer.
    """
    understood = memory.get("understood")
    clean = " ".join(str(text or "").lower().split())
    return _after_safety(memory, clean, understood if isinstance(understood, dict) else None)


def _in_a_loss_thread(memory):
    """True when one of the last few things said was about a death.

    Grief is not a body that mends. `im over it now` two turns after `my dad died in march` is
    the same loss said again, and "take it gently for a day or two and let it stick" answers it
    with advice for a bad back.
    """
    for turn in [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-4:]:
        said = str(turn.get("user") or "").strip()
        if said and loss.reads_as_loss(said.lower()):
            return True
    return False


# A nod after a bereavement is still the same conversation, and the stock nod pool opens with a
# closing line for a chat about a dripping tap. The two words either side of it are enough to
# know: the bot's own condolence, or the person's own news.
#
# "funeral", "passed away", "sorry for your loss" can only be about a person. "dead" and "died"
# cannot: a laptop dies and an engine dies, and a nod after either is not a bereavement, so those
# words need somebody in the line with them.
LOSS_IN_TURN_CLEAR = re.compile(
    r"\b(?:funeral|buried|burial|cremat\w*|grief|grieving|bereave\w*|widow\w*|condolence\w*|"
    r"sorry for your loss|passed away)\b")
LOSS_IN_TURN_ANYBODY = re.compile(r"\b(?:died|dying|death|deaths|dead|lost (?:my|her|his|our))\b")
# The people who die are open-ended and the things that die are a short closed list, so an unknown
# subject is read as a person: "sandra died last week" is a condolence and "my tv died" is not.
LOSS_A_THING = re.compile(
    r"\b(?:laptop|phone|mobile|engine|battery|car|van|plant|plants|machine|washing machine|"
    r"tv|telly|fridge|freezer|boiler|dishwasher|dryer|oven|router|computer|pc|printer|hoover|"
    r"vacuum|watch|clock|bike|mower|heating|bulb|lights?|screen|console|kettle|toaster|"
    r"microwave|cooker|radiator|immersion|shower|pump|drone|drones|lawnmower|lawn mower|moped|"
    r"scooter|motorbike|tablet|ipad|wifi|wi-fi|internet|broadband|signal|connection|speaker|"
    r"headphones|earbuds|camera|torch|iron|drill|radio|music|party|battery|charger|"
    r"satnav|gps|tumble dryer|hot water|plug|fuse|switch)\b")
LOSS_IT_DIED = re.compile(r"\bit(?:'s| is| has| had)?\s+(?:just\s+)?(?:died|dead|dying|gone)\b")
# "lost" is the same word for a person and for a job, a set of keys or a house, and the thing that
# is lost is what says which: a job is a hard week and a bereavement is not one.
LOSS_A_LOST_THING = re.compile(
    r"\blost (?:my|our|his|her|their|the) (?:job|jobs|work|shift|hours|keys|key|wallet|purse|"
    r"passport|ticket|tickets|money|savings|deposit|house|home|flat|bag|card|cards|licence|"
    r"license|id|fob|bus pass|phone|mobile)\b")
LOSS_SOMEBODY = re.compile(
    r"\b(?:mum|mom|mam|mother|dad|father|nan|nana|gran|granny|grandma|grandad|grandpa|"
    r"grandmother|grandfather|sister|brother|wife|husband|partner|son|daughter|baby|child|"
    r"children|uncle|aunt|auntie|cousin|friend|mate|neighbour|neighbor|fiance\w*|boyfriend|"
    r"girlfriend|he|she|him|her|his|hers|they|them|person|people|someone|somebody|man|woman|"
    r"lady|lad|boy|girl|pet|dog|cat|puppy|kitten)\b")


def _a_loss_in(text):
    """True when the line is about somebody dying, not about a thing that stopped working."""
    text = (text or "").lower()
    if LOSS_IN_TURN_CLEAR.search(text):
        return True
    if not LOSS_IN_TURN_ANYBODY.search(text):
        return False
    # the thing that was lost beats the person who lost it: "my dad lost his job" is a bad week
    # and "i lost my dad" is not, and only the object of "lost" tells them apart.
    if LOSS_A_LOST_THING.search(text):
        return False
    # a person word in the line beats any thing word: a man who came off his bike and died is a
    # bereavement, and only a line with nobody in it can be a machine that stopped.
    if LOSS_SOMEBODY.search(text):
        return True
    if LOSS_IT_DIED.search(text) or LOSS_A_THING.search(text):
        return False
    return True


# "dead" on its own is a British intensifier as often as it is a death - "dead funny", "dead on
# my feet", "dead tired", "dead good", "drop dead", "im dead" when they are worn out - and a
# line whose only death word is "dead" is where every one of those idioms lives. The loss module
# already reads them all (`reads_as_loss` knows the laughing and the worn-out lines), so its
# answer is the one that counts there. A line that says "died", "death" or "funeral" is read on
# its own words: "he died" and "sandra died last week" carry no idiom in them.
DEAD_AND_NOTHING_ELSE = re.compile(r"\bdead\b")
DIED_OR_DEATH = re.compile(r"\b(?:died|dying|dies|death|deaths|lost (?:my|her|his|our))\b")


def _dead_is_the_only_death_word(said):
    """True when the only death word in the line is "dead", where the idioms live."""
    return bool(DEAD_AND_NOTHING_ELSE.search(said)) and not DIED_OR_DEATH.search(said)


LOSS_OWN_WORDS = tuple(loss.LOSS_REPLIES) + tuple(loss.AFTER_REPLIES)


def _we_condoled(line):
    """True when the bot's own line was a condolence from the loss pools.

    Read on the opening of the line, because a reply is the pool's sentence and sometimes a
    question after it, and the sentence is what says which thread we are in.
    """
    line = (line or "").strip()
    return bool(line) and any(line.startswith(reply[:30]) for reply in LOSS_OWN_WORDS)

# A machine stops without anybody dying, and "my laptop died" is a repair rather than a loss:
# the nod after the advice is neither a condolence nor a win. Main's own reading already tells the
# two apart (`_a_loss_in`), so a death word that is not a loss is a thing that stopped.
def _a_thing_stopped(clean):
    """True when a thing stopped working rather than a person or a pet dying."""
    return bool(LOSS_IN_TURN_ANYBODY.search(clean or "")) and not _a_loss_in(clean)


def _last_turn(memory):
    """The last turn of the chat, or an empty one."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    return turns[-1] if turns else {}


def _the_last_line_was_bad_news(memory):
    """True when the last thing the person said was bad news about their own life.

    "my mum has cancer", "my dad is in hospital", "i got made redundant": a nod to that is the
    person taking it in, and the reply is room to say more rather than a nod back.
    """
    said = str((_last_turn(memory) or {}).get("user") or "")
    return bool(said) and reads_as_bad_news(said.lower())


def _the_last_line_was_a_fault(memory):
    """True when the last thing the person said was a thing or a body of theirs going wrong.

    "my knee is sore when i run", "my boiler keeps cutting out", "my laptop died": everyday
    trouble rather than heavy news, and the nod after it was congratulated just the same.
    """
    said = str((_last_turn(memory) or {}).get("user") or "")
    if not said:
        return False
    clean = said.lower()
    if reads_like_a_symptom(clean):
        return True
    return bool(trouble.reads_as_trouble(clean) or _a_thing_stopped(clean))


def _a_loss_recently(memory):
    """True when the last thing said, either way, was a death or a funeral.

    The bot's own condolence line counts even when it names no death word ("There's no rush to
    talk about it"): that is the thread the person is in, and the nod belongs to it.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    last = turns[-1]
    said = str(last.get("user") or "").strip().lower()
    if said and (not _dead_is_the_only_death_word(said) or loss.reads_as_loss(said)):
        if _a_loss_in(said):
            return True
    # the condolence after the condolence: "the funeral was yesterday" is answered, then "i feel
    # empty" is answered with room to talk, and the nod after that belongs to the death and not
    # to a fresh chat. Neither of our lines has to name the death for the thread to be that one.
    ours = str(last.get("bot") or "")
    if _we_condoled(ours):
        return True
    # the bot's own words are not the person's: an answer about a machine "that has stopped
    # dead" is not a bereavement, so only a word that can only be about a person is read there.
    both = " ".join(str(last.get(k) or "") for k in ("user", "bot")).lower()
    return bool(LOSS_IN_TURN_CLEAR.search(both))


# The words that make a nod a nod after a hard line rather than after anything else. The mood
# reader already knows which way a line goes, and a line it reads as negative is a line the person
# was not making small talk on. This is only asked when the nod has nothing of its own, so a
# "mm" after "the boiler is fixed" is still left to the cheerful pool.
def _the_last_line_was_heavy(memory):
    """True when the last exchange was a hard thing, not small talk.

    Either side says it: the person's line read as a low one, or the answer we gave was one of the
    heavy pools ("Sorry to hear that", "That's a lot to be holding in"). The second is needed
    because the mood reader does not know every word - "im gutted" and "i want to cry" read
    neutral - and our own line is the plainest evidence of which thread we are in.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    last = turns[-1]
    said = str(last.get("user") or "").strip()
    if said:
        words = _words(said.lower())
        if words and _mood(words, said.lower()) == "negative":
            return True
    return bool(OUR_HEAVY_TELL.search(str(last.get("bot") or "").lower()))


def _in_sudden_loss_thread(memory):
    """True when the bot's own last line was its reply to a sudden loss."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    last = str(turns[-1].get("bot") or "")
    return bool(last) and any(last in pool for pool in
                              (SUDDEN_LOSS, PREGNANCY_BLEEDING, THE_FIRST_HOUR_AND_A_CHILD))


def _reads_as_illness(clean):
    """True when the word "ill" in the line means sickness rather than "I'll"."""
    words = [w.strip(".,!?;:'\"") for w in clean.split()]
    for n, word in enumerate(words):
        if word.strip(".,!?;:'\"") != "ill":
            continue
        before = words[n - 1] if n else ""
        if before in ILL_SAID_OF_A_BODY:
            return True
        # "so ill be on 34k", "and ill be there by eight": the verb after it is the tell, and it
        # beats a degree word in front, because a body is never ill *be* something.
        if n + 1 < len(words) and words[n + 1].strip(".,!?;:'\"") in ILL_WILL_VERBS:
            continue
        if n and before in ILL_BEFORE:
            return True
        if n == len(words) - 1 or words[n + 1] in ILL_AFTER:
            return True
    return False


# A cue word that is the thing the person wants to do is not a mood: "i want to lose weight"
# is an aim, and "Sorry to hear that" answers a feeling nobody expressed. Only an aim with
# nothing else wrong in the line counts, so "im trying to lose weight but the scales wont
# move" stays a frustration. A negated aim ("i dont want to lose the house") is the fear
# itself, so it stays too.
AIM_BEFORE = re.compile(
    r"(?:\b(?:want|wants|wanting|trying|try|need|needs|plan|planning|hoping|hope|help|helps"
    r"|starting|started)\s+(?:to\s+|me\s+to\s+)?"
    r"|\b(?:how\s+do\s+i|how\s+can\s+i|how\s+to|best\s+way\s+to|ways\s+to|tips\s+to"
    r"|tips\s+for|any\s+advice\s+on)\s+)$"
)


def _in_an_aim(clean, word):
    """True when every use of this word is the thing the person is setting out to do."""
    if " but " in clean or " though " in clean or " although " in clean:
        return False
    hits = list(re.finditer(r"\b%s\b" % re.escape(word), clean))
    if not hits:
        return False
    for match in hits:
        before = clean[:match.start()]
        if not AIM_BEFORE.search(before):
            return False
        if {w.strip(".,!?") for w in before.split()[-3:]} & AIM_NEGATORS:
            return False
        after = match.end()
        if {w.strip(".,!?") for w in clean[after:].split()} & AIM_FAILING:
            return False  # the aim is not going well, so it is a trouble after all
    return True


def _a_mood_word(words, word):
    """True when a word that is also a thing is describing something rather than naming it."""
    for index, said in enumerate(words):
        if said != word:
            continue
        before = words[index - 1] if index else ""
        after = words[index + 1] if index + 1 < len(words) else ""
        if before in COPULA:
            # "the food was crap" and "this phone is rubbish" are the thing's fault, not a weight
            # the person is carrying; "i feel rubbish" and "the week was rubbish" are theirs.
            subject = words[:index - 1]
            last = subject[-1] if subject else ""
            if (last in ABOUT_THEM_BEFORE_COPULA or set(subject) & STRETCH_OF_TIME
                    or not subject or (len(subject) == 1 and last in ("it", "this", "today"))):
                return True
            continue
        if before in MOOD_BEFORE or after in MOOD_AFTER:
            return True
    return False


# Going over the same thing and getting nowhere, which people say far more often than they say
# what it is: "i keep going over it in my head", "its been on my mind all week", "i cant stop
# replaying what i said", "on repeat since friday". The line has no subject a module can pick up,
# so without this it is either said back word for word or met with "noted". What a friend does is
# name the loop and ask the one thing it keeps coming back to, so that is the whole reply.
RUMINATION = re.compile(
    r"\b(?:keep|keeps|kept|can'?t|cant|cannot|stop|stopped)\s+(?:thinking|replaying|reliving|"
    r"dwelling|worrying)\b"
    r"|\b(?:go|going|think|thinking)\s+(?:over|through|round|around)\s+(?:it|that|this|him|her|"
    r"them|what)\b"
    r"|\b(?:on my mind|in my head|over and over|again and again|round in circles|on repeat|"
    r"switch off|can'?t shake|can not shake)\b")
# A line with a thing in it that a module knows ("i keep thinking about my mortgage", "i keep
# going over the numbers for the new car") is that thing said again, not a loop to be named: the
# loop wording would take the turn off the module that could actually answer it.
WITH_A_SUBJECT = re.compile(
    r"\b(?:my|our|his|her|their|the)\s+(?:\w+\s+)?(?:mortgage|loan|debt|rent|money|budget|"
    r"bills?|job|boss|car|boiler|washing machine|fridge|damp|landlord|surgery|doctor|gp|"
    r"appointment|wedding|interview|cv|exam|test|results?|numbers|figures|son|daughter|kids?|"
    r"child|baby|mum|mom|dad|husband|wife|partner|dog|cat|puppy|kitten)\b")


# The same shape holds a want, and there the loop line is wrong in the other direction: "i keep
# thinking about getting a dog" is looking forward to something, and "that kind of thing does not
# let go on its own" hands a happy plan sympathy for a worry they do not have (speedy-dolphin's
# read). A word of wanting says so, and so does the gerund of getting or going after the loop's
# own "about": naming the thing you are going to do is anticipation, not a thing going round.
A_WANT = re.compile(
    r"\b(?:want|wants|wanted|wanting|wanna|hope|hopes|hoping|hoped|plan|plans|planning|planned"
    r"|saving up|saving for|dreaming of|thinking of|looking forward to|working towards?)\b"
    r"|\b(?:thinking|thought|dreaming|dreamt|going|go)\s+(?:(?:about|of|over)\s+)?"
    r"(?:getting|buying|booking|adopting|starting|trying|learning|making|building|moving)\b"
    # "i keep thinking about a holiday" is one they have not had yet; a worry attaches to
    # something definite ("the interview", "my mortgage", "what i said"), which is the same
    # reading WITH_A_SUBJECT already gives the line.
    r"|\b(?:thinking|thought|dreaming|dreamt)\s+(?:about|of)\s+(?:a|an|some|another)\s+\w+")


def _is_rumination(clean):
    """True when the line is the loop itself rather than something a reply could answer."""
    if WITH_A_SUBJECT.search(clean) or A_WANT.search(clean):
        return False
    return bool(RUMINATION.search(clean))


# The same line said with a part of the person as its subject: "my nose is cold", "my ears are
# freezing", "my hands are clammy", "my face is pale". A state said of a part of me is a state of
# me - the same cold sweat and the same pallor whether the person says "im clammy" or "my hands
# are clammy" - and the pools are written to answer either ("Is it just your hands, or all
# over?"). Only a part that has no answer of its own comes here: a hand or a foot being cold is
# circulation, and the answers entry says so better ("warm the whole body, not just the hands"),
# and "my head is hot" is a fever question, so those keep their own readings. Nothing above this
# in the chain has refused the line already, which is what keeps the part's own card first.
BODY_PART = re.compile(
    r"\b(?:my|our)\s+(?:nose|ears?|face|cheeks?|skin|hands?|lips?|forehead|arms?|back)\s+"
    r"(?:are|r|is|feels?|looks?|go|goes)\s+(?P<rest>.+)$")


def _opens_a_question(words):
    """True when the line opens like a question rather than a report of a state.

    "am" is the one opener that is also the person with their subject left off - "am hungry", "am
    freezing" - and it only asks when the pronoun is back in the line ("am i hungry"). Read as a
    question, those lines got the neutral nod: "am hungry" was "I'm listening - say more if it
    helps" where "im hungry" has its answer. Every other opener ("why", "is", "was") asks
    whatever follows it, so it is left as it was.
    """
    if words[0] not in QUESTION_OPENERS:
        return False
    if words[0] != "am":
        return True
    return len(words) > 1 and words[1] in _SUBJECT_AFTER_AM


# The rest of this module's rows live in fallback_chain.py, so this file stays under the publisher's
# 1 MiB limit. They are imported here, at the end, where everything they use above is
# already defined. New rows belong in that file too, or this one grows back over the limit.
from .fallback_chain import (
    ACTS_AN_ERRAND, ACTS_AN_ERRAND_LINES, ACTS_IN_A_DIARY, ACTS_IN_A_DIARY_LINES,
    ACTS_ON_A_PHONE, ACTS_ON_A_PHONE_LINES, ACT_CHOICE, ACT_FOR_ME,
    ACT_OPENER, ACT_OWN_STEP, ACT_REPORT_TAIL, ACT_SETTING,
    ACT_THING, ADDRESSED, AN_ATTEMPT_AT_SOMEONE, ASK_SHAPE,
    AT_THE_CLOCK, A_BAD_THING_NAMED, A_BARE_MODIFIER, A_CHILDHOOD_MEMORY,
    A_CLOCK, A_CROWD, A_CROWD_AHEAD, A_DAY_SUBJECT,
    A_DAY_WENT_WRONG, A_HAND_OUT, A_LENGTH, A_LIST_ON_THE_TABLE,
    A_MILESTONE, A_MISTAKE, A_MOOD, A_REGRET_DOING,
    A_SYMPTOM_PHRASE, A_TIME_SAID, A_VISIT, BAD_DAY_ANYWAY,
    BOOKING_THING, CAN_DO_ITSELF, CLOCK_ABOUT_THE_JOB, CLOCK_ASKED,
    CLOCK_NOT_THIS, CLOCK_SHAPE, CLOCK_SOMEONE_ELSE, CLOCK_THE_DEPARTURE,
    CROWD_ORDER, DAY_PAST, FOOD_TOPICS, FRAME_PREFIX,
    HABIT_MIND_IT, HABIT_NOT, HABIT_STATED, HANDS_IT_OVER_HERE,
    HURT_BUT_FINE, HURT_DEATH, HURT_FIGURE, HURT_ON_THE_SPEAKER,
    HURT_SOMEBODY, LOW_DAY, LOW_DAY_MINE, LOW_DAY_NOT_MINE,
    NOT_ABOUT_THEM, NOT_A_CROWD_AHEAD, NOT_A_DAY_DONE, NOT_A_DAY_SAID,
    NOT_A_JOB_BUT_A_PERSON, NOT_A_REGRET, NOT_A_THING_TO_GET, OPTION_ON_THE_TABLE,
    OWN_THING, PAST_DOING, POLITE_ASK, REMIND_ME,
    SNAPPED_A_PHOTO, SOMEONE_ELSE_NAMED, TAKES_AS_IT_COMES, THEIR_OWN_DOING,
    THE_JOB_NAMED, _AN_ASKING, _AN_ATTEMPT_COUNT, _A_BODY_UNWELL,
    _A_CORRECTION, _A_DETAIL_OPENING, _A_NEGATIVE_AUXILIARY, _A_SYMPATHY,
    _ROUTINE_NOT_SHAPE, _UNDERTAKING, _a_birthday_still_to_come, _a_claim_about_a_thing,
    _a_care_home_line, _a_day_of_someone_else, _a_day_told_instead_of_the_receipt,
    _a_detail_about_what_was_said, _a_dish_name, _a_thing_got_ahead,
    _a_lateness_report, _a_low_day, _a_part_is_cold, _a_report_with_no_pronoun,
    _a_small_day, _a_state_in_the_past, _a_thing_happened, _a_thing_they_regret,
    _a_things_state, _act_asked_of_me, _acts_for_me, _answers_the_correction,
    _asks_the_bot, _body_state, _choose, _cue_negated,
    _flat_habit_stated, _habit_is_a_problem, _just_asked_about_the_day, _loves_people,
    _loves_someone, _mixed_seed,
    _mood, _options_already_up, _reads, _reads_as_a_bad_stretch,
    _reads_value, _repaired_of, _reply_for, _restated, _routine_pool,
    _somebody_elses_day_in_thread, _somebody_hurt, _state_from, _the_birthday_said_back,
    _the_clock_pool, _the_crowd_is_ahead, _the_morning_has_a_clock, _the_person_named_a_list,
    _the_state, _the_store_has_the_recall, _the_time_said, _the_win_is_someone_elses,
    _words, reads_as_a_flat_habit, reply_for, takes_as_it_comes,
    _a_part_in_a_state,
)

# Every line this composer says as an outcome of the advice it gave. Kept together so a reader of
# the bot's own last line can tell the composer's report from an answer: the second question in a
# thread ("is that bad") is about the answer, and the report spoken over it is not the answer.
REPORT_REPLY_LINES = frozenset(
    tuple(TRIED_WORSE_REPLIES) + tuple(TRIED_NO_CHANGE_REPLIES) + tuple(TRIED_NO_CHANGE_ELSEWHERE)
    + tuple(TRIED_HELPED_REPLIES) + tuple(TRIED_HELPED_ELSEWHERE) + tuple(TRIED_IT_REPLIES)
    + tuple(TRIED_SORTED_REPLIES)
)


def is_a_report_reply(said):
    """Whether the bot's own line was one of this composer's readings of a report on its advice.

    The report lines are spoken by whichever module proposes them - `greeting` under the floor, or
    `chat` - so the text decides it rather than the module name, the way `verdict` already reads
    its own verdict lines.
    """
    line = " ".join(str(said or "").lower().replace("\u2019", "'").split())
    return bool(line) and line in _REPORT_LINES_FLAT


def _flat_pools():
    return frozenset(" ".join(str(line).lower().replace("\u2019", "'").split())
                     for line in REPORT_REPLY_LINES)


_REPORT_LINES_FLAT = _flat_pools()
# The readings this file used to hold - the day that went badly, the plan that did not happen, the
# name that came from somebody - now live in fallback_chain.py with the rest of the rows, and the
# pools they choose from live in fallback_data.py. Both are re-exported here, at the end and after
# the rest of the file's own imports, so `fallback.X` still finds every one of them.
from .fallback_chain import (  # noqa: E402 - after the rows above, as the import at the top is
    A_DAY_SAID_BADLY, A_NAME_A_HOUSEHOLD_TAKES, A_NAME_IS_NOT_A_DAY, A_NAMES_TOLD,
    A_POSSESSIVE_OF_MINE, NOT_A_NAME_WORD, NAMED_AFTER,
    BARE_STATE, BOT_WAS_SORRY, PLAN_THAT_FELL_THROUGH, RESULT_WENT_WRONG, STATE_IN_THE_PAST,
    STATE_NOT_A_DOING, STATE_THEN,
    _a_bad_time_told, _a_day_asked_without_a_cheer, _a_day_said_badly, _a_detail_of_a_bad_day,
    _a_name_told, _a_name_told_reply, _a_small_day_shape, _a_state_of_theirs,
    _named_after_reply, _the_day_was_already_bad, _the_last_exchange,
)
from .fallback_data import (  # noqa: E402 - the pools those readings choose from
    A_BAD_TIME_TOLD, A_DAY_ASKED_PLAIN, A_NAME_STORY, A_NAME_TOLD, A_NAMED_AFTER,
    A_NAMED_AFTER_THEM, A_PLAN_THAT_FELL_THROUGH, A_STATE_NOW, A_STATE_PAST,
    A_THING_CAME_OUT_WRONG,
    # `nothing_yet_line` reads this pool and the split above left it in the data file, so the
    # name was read here and bound nowhere: `tests.test_no_undefined_names` went red on main and
    # the module would have raised if that line were ever asked for.
    RETURNED_TO_IT_FIRST,
)
