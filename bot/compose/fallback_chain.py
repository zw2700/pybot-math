"""Rows of fallback, kept in their own file so fallback.py stays under the publisher's 1 MiB limit.

Nothing here is new: every name below was written in fallback.py and moved out unchanged, verbatim
and in the same order, when that file went over the limit. It is imported from the last line
of fallback.py, so the two still read as one module.
"""

import random
import re
import string
from ..memory import ack, facts, history, last_bot, last_user, obstacle, reject, repeat, swap
from ..memory import stuck as stuck_line
from ..understanding import understand
from ..understanding import kinds as understanding_kinds
from ..understanding.body import GOING_BOTH_WAYS
from ..understanding.kinds import (ANSWERING_A_QUOTED_ASK, greeting_only,
                                  the_manners_question, two_ends_of_one_scale,
                                  verdicts_a_thing)
from ..understanding.topics import IDIOM_PHRASES, THE_PEOPLE, is_a_machine_word
from . import (A_STEP_ASK, DOUBT, DOUBTED, LINGERED_LINE, NEARLY, says_it_has_lingered,
               step_when_low, turned, turns_round)
from .limit import NO_LAUGH_OR_SCARES, NOTHING_THAT_LIMITS, a_limit_on_the_answer
from . import (badnews, circumstance, draft, finding_out, goodnews, handoff, harm, leaving, loss,
               morning_after, no_eyes, onething, pick, prices, quantity,
               reaction as answer_reaction, remark, safetyask, trouble, unseen, why, worn)
from .postcode import a_postcode_lookup
from .urgent import reads_as_a_story
from .badnews import (reads_as_a_closed_door, reads_as_an_award_lost, reads_as_bad_news,
                      reads_as_heavy_news, reads_as_news_with_a_name,
                      reads_as_pregnancy_bleeding, reads_as_the_leaving,
                      reads_as_a_leaving_already_gone, reads_as_a_pet_condition,
                      reads_as_the_speakers_own_plan,
                      reads_as_sudden_loss,
                      reads_as_a_carer_body, reads_for_a_carer, reads_for_a_pet,
                      reads_as_a_pet_low, reads_like_a_symptom)
from .goodnews import (reads_as_an_occasion, reads_as_a_win_nobody_noticed,
                      reads_as_a_win_a_cost_came_with,
                       reads_as_a_clear_result, reads_as_good_news, reads_as_news_to_come,
                       reads_as_recovery,
                       reads_as_settled, worry_on_the_table)
from .fallback_data import (
    A_CARE_HOME,
    A_CARE_HOME_BRING,
    A_CARE_HOME_GUILT,
    A_CARE_HOME_MOVED,
    A_CARE_HOME_VISITING,
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
    ASKED_IF_I_SAW_LINES,
    ASKING_WORDS,
    ASK_ONLY,
    ASK_OUT_ANSWER,
    AT_IT_EXTRA,
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
    A_NEWS_OF_SOMETHING_ELSE,
    A_NEWS_OF_WEATHER,
    A_PAUSE_WORD,
    A_PERSON,
    A_PLACE_I_DONT_KNOW,
    A_REST_OF_A_GOOD_DAY,
    A_REST_OF_A_HARD_DAY,
    A_SMALL_DAY,
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
    A_BETRAYAL,
    A_WANT_IT_OVER,
    BABY_FOOD_NAMES,
    BABY_WHO,
    BAD_STRETCH,
    BAD_STRETCH_REPLIES,
    BARE_FOLLOW_UP_CARE_REPLIES,
    BARE_FOLLOW_UP_REPLIES,
    BARE_PICK_AFTER_NEWS,
    BARE_PICK_BRING,
    BARE_PICK_DO,
    BARE_PICK_GET,
    BARE_PICK_KIND,
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
    FORECAST_HE_SHE,
    FORECAST_ILL,
    FORECAST_OFF_THEIR_FOOD,
    FORECAST_PERMISSION,
    FORECAST_PERSON,
    FORECAST_PET,
    FORECAST_PET_HARM,
    FORECAST_POOLS,
    FORECAST_RELATION,
    FORECAST_SELF,
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
    MY_RECORDS,
    MY_WORKINGS,
    NAMED_NEGATIVE,
    NAMED_TYPES,
    NARROW_ANSWERED,
    NARROW_SUBSTANCE,
    NARROW_WORDS,
    NEGATIVE,
    NEGATIVE_CUES,
    NEGATORS,
    NOTHING_AT_ALL,
    CONTRAST,
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
    PET_LOW_REPLY,
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
    A_WAIT_ENDING,
    SOMETHING_CAME_APART,
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
    SAME_AGAIN,
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
    RETURNED_TO_IT_FIRST,
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
    WHY_AFTER_TASTE,
    WILD_BIRDS,
    WIN_IN_A_SILENCE, WIN_AND_A_COST,
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

# The day that went badly and the name that came from somebody: the pools those readings choose
# from. They are in the data file with the rest, and the readings that use them live here.
from .fallback_data import (
    A_BAD_TIME_TOLD, A_DAY_ASKED_PLAIN, A_NAMED_AFTER, A_NAMED_AFTER_THEM, A_NAME_STORY,
    A_NAME_TOLD, A_PLAN_THAT_FELL_THROUGH, A_STATE_NOW, A_STATE_PAST, A_THING_CAME_OUT_WRONG,
)
from .fallback_data import (
    # Moved out of this file whole: the tables are unchanged, and the names come back
    # under the same ones.
    ABSENCE,
    A_BOOKING_AHEAD,
    A_BOOKING_AHEAD_DATED,
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
    PAUSE_IN_A_SAFETY_THREAD,
    PRIVACY_ASK,
    PRIVACY_SHAPES,
    THE_DAY,
    WORDING_SOMEONE,
    _LANDED,
)

# What the moved rows take from fallback.py, which is fully defined by the time this
# module is imported, because fallback.py imports it from its own last line.
from .fallback import (
    ABOUT, ABOUT_SELF, ABOUT_TALLY, ABOUT_WORDS,
    ACK, ACKS, ACK_AFTER_TROUBLE, ACK_WARM,
    ACTS_FOR_ME, AGREEMENT, AIM_HEADS, ANIMALS,
    ANSWERING_A_QUOTED_ASK, A_BIRTHDAY_STILL_TO_COME, A_BIT_PAST_IT, A_CHILD,
    A_CHILD_LEAVING, A_CHILD_LEFT, A_COMPARISON_OF_STANDING, A_COST_SOMEBODY_ASKS,
    A_DISMISSAL, A_DREAD, A_GOOD_TIME, A_GOOD_TIME_IN_A_CARE_THREAD,
    A_HELP_WORD, A_LAUGH, A_MOOD_WITH_A_CATCH, A_SMALL_DAY,
    A_SORRY_ON_ITS_OWN, A_SUGGESTED, A_SUGGESTED_BY_SOMEONE, A_THING_LOOKS_SAD,
    A_THING_THEY_REGRET, A_WANT_IT_OVER, A_WAY_OF_BEING, BAD_STRETCH,
    BAD_STRETCH_REPLIES, BEHIND_ON_MONEY, BODY_ALSO, BODY_LEAD,
    BODY_PART, BODY_PART_QUALIFIER, BODY_PART_TAIL, BODY_POOLS,
    BODY_SITUATION, BODY_STATES, BODY_TAIL, BOUND_FOR,
    CAME_BACK, CANNOT_ANYTHING, CANNOT_ANYTHING_ASK, CANNOT_READ_YOURS,
    CANNOT_SEE_ANYTHING, CANNOT_SEE_ANYTHING_LINES, CANNOT_YOUR_OWN, CARD_LINES,
    CARING, CARING_FOR_A_BODY, CHECK_PHRASES, CLOSED_DOOR,
    COMFORT_SAID, CONGRATS, CROWD, CUT_FOR,
    DATES_KEEP_SLIPPING, DATE_AHEAD, DECLINED_PLAN, DECLINED_PLAN_GENTLE, DISH_DETERMINER,
    DISH_PARTICIPLE, DITHER, DITHER_DECIDE, DITHER_OPEN,
    DITHER_OPEN_LINES, DITHER_TWO_WAY_LINES, DITHER_YES_NO, DONE_NOT_THIS,
    DONE_VERB, DOUBLE_BOOKED, DOUBT, DOUBTED,
    ELDER_AID_REPLIES, ELDER_CLINIC_REPLIES, ELDER_DOCTOR_REPLIES, ELDER_HELP_REPLIES,
    EMBARRASSED, EMERGENCY_CALL, EMPTY, EXPERT_WORDS,
    FLAT, FLAT_LINE, FOOD_TOPICS, FORGETS_AGAIN,
    FORGETS_A_CLASH, FORGET_A_DATE, FORGET_A_SECRET, FOUND_IT,
    FRAME_WORDS, FRIGHTENED, GOING_BOTH_WAYS, GREETING,
    GRIEF_AFTER, GRIEVANCE, HABIT_ACT, HABIT_PROBLEM_ACT,
    HABIT_REPLY, HAND, HANDS_BACK, HANDS_IT_BACK,
    HAND_BACK, HARM_ANYWHERE, HARM_NAMED, HARM_ON_ME, A_HURT_MYSELF,
    HEALTH_MODIFIER, HEALTH_WORDS, HELP_ALREADY, HELP_SERVICE,
    HOUSE_VERB, HOW_ARE_YOU, HURT_EVENT, IDIOM_GLAD,
    IDIOM_SHY, IMPERATIVE, INVITED, INVITED_TO_TALK,
    A_GOODNESS_ASKED_OF_ME, A_SKILL_ASKED_OF_ME, ASKED_A_RATING, ASKED_IF_GOOD,
    I_RATE_A_SKILL, JUNK_CUES, KEEPS_FORGETTING, KNOCKED,
    LANDED_BAD, LATE_ASKS, LATE_BEHIND_LINES, LATE_NOT_A_TIME,
    LATE_NOT_IT, LATE_NOW, LATE_NOW_LINES, LAUGHED_AT,
    LEAVING_A_PERSON, LEFT_BEHIND, LEFT_POOL, LEFT_POOL_GONE,
    LOCKED_OUT_LINES, LOCKED_OUT_OF_THE_CAR, LOST_A_THING, LOST_A_THING_AGAIN,
    LOST_QUESTION, LOW_DAY_REPLIES, LUMP, MILESTONE,
    MISHAP_BACK, NAMED_NEGATIVE, NEARLY, NEGATIVE,
    NEGATIVE_CUES, NEGATIVE_LINE, NEGATORS, NEUTRAL,
    NEVER_MIND, NEWS_TO_COME, NOT_FIT_ENOUGH, NOT_LEAVING_ANYONE,
    A_CORRECTION_TAKEN,
    NOT_SELF, NOT_TOO_OLD, NO_DIRECTION_REPLY, ONE_SKILL_RATED,
    OWN_THING, PAST_STATE_CUES, PENDING_DOUBT, PENDING_LANDED,
    PENDING_WAITING, PENDING_WHEN, PERSON_WORDS, PET_CONDITION_TROUBLE,
    PET_TROUBLE, PLAN, PLAN_DONE, PLAN_DONE_ACK, reads_as_a_change_of_medicine,
    PLAN_MEDICINE_REPLY, PLAN_MEDICINE_SLOW, PLAN_MEDICINE_SLOW_REPLY,
    PLAN_IDIOM, PLAN_KNOCKED, PLAN_NOT_YET, POLICE_CALL,
    POSITIVE, POSITIVE_CUES, PREGNANCY_BLEEDING, PRESENT,
    PUNT, QUOTE_ASKS, QUOTE_LINES, RATES_A_SKILL,
    REACTIONS_CARE, REACTIONS_SAID, REACTION_REPEAT, RELATIONSHIP_DECISION,
    RELIEF, ROUTINE, ROUTINE_NOT, ROUTINE_PHRASES,
    ROUTINE_WORDS, RUMINATION_REPLIES, RUN_OUT_LINES, SECRETS_KEEP_SLIPPING,
    SELF_BLAME, SELF_BLAME_ASKS, SELF_SUBJECT, SOMEBODY_HURT,
    SOMEONE_GONE, SOMEONE_LEAVING, SOMEONE_SERIOUSLY_ILL, SORRY_FOR_ASKING,
    SORRY_ON_ITS_OWN, SO_NOTHING_LIVE, STATE_CUES, STRETCH_OF_TIME,
    STUCK_AFTER_TROUBLE, SUDDEN_LOSS, SYMPTOM, SYMPTOM_COLD,
    SYMPTOM_LINGERS, TELL_HARD, TELL_HARD_LINES, TELL_NOT_WORDS,
    THANKS, THANKS_GOOD_AGAIN, THANKS_NO_BETTER, THANKS_THEN_SAID,
    THANKS_WENT_BADLY, THE_FIRST_HOUR_AND_A_CHILD, THE_LEAVE_HAS_HAPPENED, TIGHT_MONEY,
    TIGHT_MONEY_MORE, TIPS_LINES, TOO_MUCH, TOO_MUCH_PHRASES,
    UNKNOWN, UNKNOWN_HEALTH, UNKNOWN_MONEY, UNKNOWN_WORD,
    VET_WHO, WALKED_INTO_POOL, WIN_IN_A_SILENCE, WORDING_ASKS,
    WORDING_ASKS_WHO, WORDING_LINES, WORDING_SAYS, WORDING_SOMEONE,
    WORDING_TELL, WORDING_WHERE, WOULD_HAVE_BEEN, YOU_SUBJECTS,
    _CAUGHT, _DAY_WORDS, _ILL, _LUMP,
    _NO_DAY_OF_THEIR_OWN, _START_ASK, _THING_DONE_LINES, _WAS,
    _a_bad_line_above, _a_care_thread_to_leave_alone, _a_carer_refused, _a_cost_somebody_asks,
    _a_day_ahead, _a_dead_end, _a_declined_plan, _a_doable,
    _a_good_time, _a_guessed_result, _a_hard_week, _a_knock_into_a_thing,
    _a_knock_on_oneself, _a_leaning_side, _a_loss_recently, _a_mishap,
    _a_mishap_to_ask_about, _a_mood_word, _a_no_from_the_bot, _a_place_asked_about,
    _a_plan_on_the_table, _a_question_about_the_person, _a_refusal_to_answer, _a_relationship_ending,
    _a_start_ask, _a_subject_above, _a_tally_of_its_own_day, _a_thing_they_started,
    _a_time_in_it, _a_verdict_line, _a_verdict_on_their_plan, _about,
    _action, _after_advice, _after_safety, _an_invitation,
    _an_open_result, _answered_recently, _asks_for_help, _asks_how_are_you,
    _came_back, _dreading, _grief_thread, _grievance_thread,
    _hedged_recently, _help_topic, _in_a_care_thread, _in_a_loss_thread,
    _in_a_pool, _in_an_aim, _in_sudden_loss_thread, _is_a_tips_ask,
    _is_presence_check, _is_rumination, _live, _looking_forward,
    _matchable, _money_decision, _my_pick, _named_draft,
    _names_their_age, _news_above, _no_words, _occasion_pool,
    _only_the_stuck_phrase, _opens_a_question, _own_feeling, _plain,
    _plan_reported, _reaction_pool, _reads_as_a_question_when_repaired, _reads_as_dither,
    _reads_as_greeting, _reads_as_illness, _reads_as_question, _run_out,
    _a_promise_that_keeps_moving,
    _says_only_what_they_said, _self_line, _someone_else_dropped_it, _someone_else_minding,
    _am_i_a_nuisance, _something_funny, _sorry_for_asking, _summons_pool, _taste,
    _acknowledges_alone,
    _thanks_news_went_badly, _thanks_then_said, _thanks_with_more, _the_answers_take_it,
    _asks_for_words, _the_ask_for_words_behind_a_doubt, _the_bot_says_it_cannot,
    _the_day_described, _the_heavy_pool,
    _the_last_line_was_a_fault, _the_last_line_was_bad_news, _the_last_line_was_heavy, _the_line_before,
    _the_line_cancels, _the_live_thing_named, _the_news_landed, _the_person_already_said_it,
    _the_person_they_are_stuck_on, _the_stretch_of_time, _the_turn_before_was_a_heavy_one, _the_view_asked_for,
    _their_contact_number, _their_own_slip, _thing_done_pool, _thing_done_scan,
    _thread_is_about_the_body, _tips, _trouble, _unknown,
    _verdict_pool, _wants_it_over, _weighs_a_choice, _what_no_eyes_already_says,
    _who_for, _words, a_comparison_of_standing, a_continuation_of_the_tight_week,
    a_fresh_death_and_the_words, a_happening_now, a_loss_in_the_thread, ack,
    answer_reaction, asks_for_more, circumstance, draft,
    facts, finding_out, goodnews, greeting_only,
    handoff, in_a_safety_thread, is_a_hedge, last_bot,
    last_user, leaving, loss, no_eyes,
    onething, quantity, random, re,
    reading, reads_as_a_carer_body, reads_as_a_clear_result, reads_as_a_closed_door,
    reads_as_a_leaving_already_gone, reads_as_a_narrowing, reads_as_a_pet_condition,
    reads_as_a_report, reads_as_a_return, _a_chat_behind_it,
    reads_as_a_win_nobody_noticed, reads_as_an_award_lost, reads_as_an_occasion, reads_as_bad_news,
    reads_as_good_news, reads_as_if_i_saw, reads_as_news_to_come, reads_as_news_with_a_name,
    reads_as_pregnancy_bleeding, reads_as_recovery, reads_as_settled, reads_as_someone_close_is_ill,
    reads_as_sudden_loss, reads_as_the_leaving, reads_as_the_speakers_own_plan, reads_for_a_carer,
    reads_for_a_pet, reads_like_a_symptom, remark, says_it_has_lingered,
    step_when_low, stuck_line, swap, the_advice,
    the_answer_to_cut, the_bound_said, the_dislike_ask, the_limits_said, the_lost_ask_reply,
    trouble, turns_round, understand, unknown_pool,
    unseen, verdicts_a_thing, who_settles, why,
    WEATHER_COLD, WEATHER_HOT, WEATHER_WET,
    worn, worry_on_the_table,
)

# "i feel cold" says the same as "i am cold": a state a person feels is the state they are in,
# and the words people type for feel are "feel", "feeling" and the -in spelling that the
# normaliser already reads back to "feeling" ("i feelin cold"). Only the word in the middle of
# "i ___ cold" is read here, so "my hands feel cold" keeps its own reading, and the state word
# still has to be the whole rest of the line - "i feel cold toward him" carries a person after
# it and stays out. A standing complaint that already has a card ("i feel cold all the time")
# keeps the card, because a knowledge row answers before these pools do.
FEEL_COPULA = frozenset(("feel", "feeling"))


def _body_state(clean):
    """Which body state the whole line is ("cold", "hot", "hungry", "thirsty"), or None.

    Only a line that is the state and nothing else comes here: "im cold" is this reading, and
    "im cold water" and "im boiling eggs" are things rather than states. A question is not a
    report of one ("im cold?" is a person checking they said it), and a line with "but" in it
    is a mixed one the trouble and feeling pools answer better.
    """
    if "?" in clean or " but " in clean or " not " in clean:
        return None
    # Two of these are said as two words far more often than one: "light headed" and "bunged
    # up" (also written "light-headed" and "bunged-up"). Joined here so the state is one word
    # and the rest of the line reads the same as the single-word version.
    flat = clean.replace("light-headed", "lightheaded").replace("light headed", "lightheaded")
    flat = flat.replace("bunged-up", "bungedup").replace("bunged up", "bungedup")
    flat = flat.replace("blocked-up", "blockedup").replace("blocked up", "blockedup")
    words = [w.strip(".,!?;:") for w in flat.split()]
    words = [w for w in words if w]
    if not words or _opens_a_question(words):
        # "am i hungry", "why am i so cold" ask about the state rather than reporting it.
        return None
    for index in range(len(words) - 1):
        if words[index] not in ("im", "i'm", "am", "iam") and not (
                words[index] == "i" and (words[index + 1] == "am"
                                         or words[index + 1] in FEEL_COPULA)):
            continue
        # The state is the whole of what they said, so nothing of substance comes before it:
        # "do you think im cold" asks about the reading and "he said im cold" is reported
        # speech, and neither is a person saying how they are.
        if any(w not in BODY_LEAD for w in words[:index]):
            continue
        start = index + 2 if words[index] == "i" else index + 1
        # Hot and cold in one breath is a fever, not the weather: "im hot and cold" and "im
        # cold then hot" are one symptom going both ways, and the practical pool would tell
        # someone shivering to open a window. The temperature reading keeps those lines. The
        # shape is that reading's own, so a hot person next to a cold thing - "im hot and the
        # pool is cold" - is not read as going both ways.
        if GOING_BOTH_WAYS.search(clean):
            return None
        state, after = _state_from(" ".join(words[start:]))
        if state:
            return state
    part_state = _a_part_in_a_state(clean)
    if part_state:
        return part_state
    return None


def _a_part_in_a_state(clean):
    """Which body state the line says of a part of them, or None: "my hands are clammy".

    A nose or an ear has no answer of its own, so a cold one is the person being cold, and the
    same goes for a clammy hand or a pale face: the pools answer a state of the body, not only a
    state said with "im", so "my hands are clammy" gets the line "im clammy" gets. The state word
    can come after a qualifier ("my nose is really cold", "my hands are a bit clammy") and can be
    said twice ("my nose is freezing cold"), which is how people say it; anything else in the line
    before the state word ("my ears are red and cold") says something else is going on, and anything
    after it ("my face is pale and i feel sick") makes it more than a state, so both keep
    whatever reading they had.
    """
    part = BODY_PART.search(clean)
    if not part:
        return None
    words = [w.strip(".,!?;:") for w in part.group("rest").split()]
    words = [w for w in words if w]
    for index, word in enumerate(words):
        state = _the_state(word)
        if not state:
            if word not in BODY_PART_QUALIFIER:
                return None
            continue
        # A part being hot is the part, not the person: a hot forehead is a fever question and
        # sweaty hands are as often nerves as a warm room, so the heat pool's "open a window" is
        # not the answer to either. The states the pools read from a part are the ones a friend
        # reads the same way whichever words carry them.
        if state == "hot":
            return None
        # Everything after the state word has to be nothing, a time word, or the same thing said
        # again ("freezing cold", "cold and freezing").
        rest = [w for w in words[index + 1:] if w != "and"]
        if all(w in BODY_PART_TAIL or _the_state(w) == state for w in rest):
            return state
        return None
    return None


def _a_part_is_cold(clean):
    """The old name for the same reading, kept because the export list in fallback.py names it.

    It answered only a part being cold ("my nose is freezing"); it reads any state a pool answers
    now, so the name says less than the function does.
    """
    return _a_part_in_a_state(clean) == "cold"


def _state_from(rest):
    """(state, words after it) for the state the rest of the line names, or (None, []) ."""
    if not rest:
        return None, []
    words = [w.strip(".,!?;:") for w in rest.split()]
    for index, word in enumerate(words):
        state = _the_state(word)
        if not state:
            continue
        tail = words[index + 1:]
        # "im really very cold" and "im so cold" are the same line, so the qualifiers before
        # the state word say nothing about what follows it.
        if tail and tail[0] == "and" and len(tail) == 2 and tail[1] in BODY_ALSO:
            return state, []
        if not tail or all(w in BODY_TAIL for w in tail):
            return state, tail
        if " ".join(tail) in BODY_SITUATION:
            return state, tail
    return None, []


def _the_state(word):
    """The body-state name for this one word, or None."""
    for name, pool in BODY_STATES.items():
        if word in pool:
            return name
    return None


HABIT_STATED = re.compile(
    # Only the person's own "i" and the "we" of a couple: another adult's habit is not theirs to
    # account for ("my husband always leaves his clothes on the floor" is a grumble about him, and
    # what is being asked here - what sets it off, what has been tried - asks the speaker to
    # explain somebody else's doing).
    r"\b(?:i|we)\s+(?:(?:always|never)\s+" + HABIT_ACT +
    r"|(?:keep|keeps|end\s+up|ends\s+up|can'?t\s+stop|cant\s+stop)\s+" + HABIT_ACT +
    r"|(?:tend|tends)\s+to\s+" + HABIT_ACT +
    # "i never get round to it" is the habit itself, said as a standing excuse.
    r"|never\s+get\s+round\s+to\b" +
    r")"
    r"|\b(?:im|i'?m)\s+always\s+" + HABIT_ACT +
    # A part of the body or the mind named with "my" is the person themselves: "my brain keeps
    # going blank" is their own pattern. Any other "my <person>" is somebody else and stops here.
    r"|\bmy\s+(?:brain|mind|memory|head|hands?|eyes?|stomach|skin|body|voice|mood|sleep|"
    r"focus|concentration|attention|nerves|anxiety|appetite|breathing|gut|bladder|jaw)\s+"
    r"(?:keeps|always|never)\s+" + HABIT_ACT, re.I)
# Being left out is not a habit to take apart: "i never get invited anywhere" is other people's
# doing, and asking what sets it off blames the person for it.
HABIT_NOT = re.compile(r"\b(?:never\s+get\s+(?:invited|asked|picked|chosen|included)|"
                       r"left\s+out|no\s+one\b|nobody\b|"
                       # "i always do this" says nothing to ask about yet - there is no "this"
                       # in the line for the bot to know, and the question reads as if it did.
                       r"\b(?:always|never)\s+do(?:es)?\s+(?:this|that|it)\b|"
                       r"\b(?:always|never)\s+late\b|"
                       # "i keep going back to him" is an on-off relationship, not a habit to
                       # take apart - what sets it off is not what the person needs to answer.
                       r"\b(?:going|go|went|running|run)\s+back\s+to\s+(?:him|her|them)\b|"
                       r"\bnever\s+(?:hear|heard|see|saw|seen|win|won)\b)", re.I)
# Said out loud, they mind it, so the doing need not be on the list: "i wish i could stop biting my
# nails", "it drives me mad".
HABIT_MIND_IT = re.compile(
    r"(?:i\s+wish|can'?t\s+stop|cant\s+stop|want\s+to\s+stop|need\s+to\s+stop|"
    r"trying\s+to\s+stop|drives\s+me\s+(?:mad|crazy|nuts|up\s+the\s+wall)|"
    r"bothers\s+me|gets\s+to\s+me|sick\s+of|fed\s+up|i\s+hate\s+that|shouldn'?t|"
    r"shouldnt|i\s+feel\s+bad|i\s+feel\s+guilty|upsets\s+me|i\s+do\s+it\s+again)", re.I)


def _habit_is_a_problem(clean):
    """Whether the repeated doing is one a person would want a hand with."""
    return bool(HABIT_PROBLEM_ACT.search(clean) or HABIT_MIND_IT.search(clean))


def reads_as_a_flat_habit(text, understood=None):
    """Whether the composer's habit pool claims this line.

    Read by `chat` before it turns the same line into its own stock question ("Annoying. Is it
    the same every time, or does it vary?"): a habit said flatly is answered here, and the
    module above stands aside so the two readings cannot disagree about who answers. So this is
    the branch's own gate and nothing else - a recurrence and a doing, no question, and no mood
    word. A claim the reply does not keep is worse than no claim at all: `chat` would stand down
    and the echo ("Noted: you keep interrupting your sister") would answer instead.
    """
    # The line as typed, and then the line with its words put right: a word typed onto the next
    # one ("icant stop crying", "ialways leave things to the last minute") hides the doing from
    # this gate, and the reading has already split it (`understood["plain"]`). The typed line is
    # asked first, so a line that reads whole is read exactly as it was typed.
    said = [str(text or "")]
    repaired = (understood or {}).get("plain") if isinstance(understood, dict) else None
    if repaired and repaired != said[0]:
        said.append(repaired)
    for line in said:
        if _flat_habit_stated(line):
            return True
    return False


def _flat_habit_stated(raw):
    """The gate itself, for one spelling of the line."""
    clean = " ".join(raw.lower().split())
    words = clean.split()
    try:
        return bool(HABIT_STATED.search(clean) and not HABIT_NOT.search(clean)
                    and _mood(words, clean) == "neutral"
                    and not _reads_as_question(raw, words)
                    and _habit_is_a_problem(clean))
    except Exception:  # noqa: BLE001 - a reading that fails claims no turn
        return False


# "the weather is horrible today" has a bad word next to a stretch of time, but it is a claim
# about a thing out in the world rather than about how the person is: "that is a lot to hold" is
# too much for a wet afternoon. A thing named with "the" at the front of the clause is the one
# the bad word belongs to, so the stretch reading stays off it; "my week has been rough" and
# "bit of a rubbish week" keep it.
NOT_ABOUT_THEM = re.compile(r"\bthe\s+([\w']+)\s+(?:is|was|are|were|gets|looks)\s*$")


def _a_claim_about_a_thing(before):
    """True when the bad word belongs to a thing named with "the" ("the weather is ...").

    A stretch of time is the exception: "the week was rubbish" and "the day was awful" are how
    people say it went for them, so the noun after "the" has to be something other than time.
    """
    found = NOT_ABOUT_THEM.search(before + " ")
    return bool(found) and found.group(1) not in STRETCH_OF_TIME


# The verb a line opens with when it tells someone to do a job: "take ...", "put ...", "book ...",
# and the polite wrappers people put in front of it. The line has to open with it, so a question
# that merely contains one of these words ("how do i turn the heating down") is not read here.
ACT_OPENER = re.compile(
    r"^(?:please\s+|ok\s+|okay\s+|right\s+|so\s+|hi\s+|hello\s+|hey\s+|and\s+|"
    r"(?:can|could|would|will)\s+you\s+(?:please\s+)?)*"
    r"(?:take|put|get|bring|grab|turn|set|fill|switch|open|lock|wash|hoover|tidy|clean|post|"
    r"feed|walk|make|book|reserve|order|call|ring|phone|text|email|buy|pay|renew|"
    # A job asked flat, with no house word in it: "search for flights for me", "send me the
    # recipe", "sign me up for the class", "keep an eye on the oven for me". The verb alone does
    # not make them an order - "search for a cheap flight" and "pick the kids up from school" are
    # the person's own errand - so each is claimed only with the "for me" or "me a" that the
    # ACT_FOR_ME test below asks for.
    r"send|search|sign|pick|save|keep|chase|look|find)\b")
# A thing in the house or a person to ring: the object that makes the verb an act in the world
# rather than a thing to work out. "make me a shopping list" and "pay the gas bill" have neither,
# so they keep the answer their entry gives.
ACT_THING = re.compile(
    r"\b(?:rubbish|bins?|bin\s+bags?|kettle|cuppa|tea|coffee|oven|heat|heating|thermostat|"
    r"alarm|washing|laundry|dishes|door|window|windows|light|lights|lamp|water|bottle|table|"
    r"taxi|cab|appointment|doctor|dentist|gp|surgery|prescription|milk|bread|paper|"
    r"post|parcel)\b")
# Who the line is said to. A bare "put the kettle on" is said to whoever is nearest, and the bot is
# nearest to the house tasks; "get some milk", "book a table for two", "take the cat to the vet" are
# as often the person's own errand on their way past, and refusing those is worse than the nod they
# had before. So a verb that is not one of the house tasks is an order only when the line says who
# it is for or asks the bot directly.
ADDRESSED = re.compile(
    r"^(?:ok\s+|okay\s+|right\s+|so\s+|hi\s+|hello\s+|hey\s+|and\s+)*"
    r"(?:(?:can|could|would|will)\s+you\b|please\b|kindly\b)")
BOOKING_THING = re.compile(r"\b(?:table|taxi|cab|room|tickets?|flight|hotel|appointment|"
                           r"restaurant|booking)\b")
# A line that names the person as the one it is done for ("book ME a table", "call the doctor FOR
# ME") is asking the bot to be the one who does it, and that is a limit to say plainly.
# The jobs that are words, not hands: a message to send, a letter, a form to fill, a thing to
# sign. The bot does half of these, so they are not the "no hands" limit - the drafting and
# on-screen pools answer them better. "sign me up for the class" is not one of these.
A_MESSAGE_OR_A_FORM = re.compile(
    r"\b(?:text|message|email|e-mail|letter|note|reply|voicemail|form|application|document)\b"
    r"|\b(?:sign|fill)\s+(?:this|it|that|in|out)\b|\bfill\s+in\b")
# "keep me posted" is a request for news, not a job: there is nothing to fetch, and the limit
# ("nothing can be fetched, sent or signed from this end") answers an ask nobody made. The same
# words are an errand when they name the thing: "keep an eye on the oven for me".
KEEP_ME_POSTED = re.compile(
    r"\bkeep\s+me\s+(?:posted|informed|updated|in\s+the\s+(?:loop|picture)|company)\b")
ACT_FOR_ME = re.compile(r"\b(?:for me|on my behalf)\b|^\s*(?:please\s+)?(?:book|reserve|order|"
                        r"call|ring|phone|text|email|buy|pay|send|save|pick|sign|keep|search)\s+"
                        r"(?:me|us)\b")
REMIND_ME = re.compile(r"^(?:please\s+|ok\s+|okay\s+|hi\s+|hello\s+)?remind me\b")
# "Remind me" is two lines, not one. "remind me to ring the dentist" is a job in the world the bot
# cannot do, and "remind me what i said at the beginning" is the store's own recall ask with three
# words in front of it - it was refused with "I can't do that one myself", which is a limit
# confessed over a question the memory could answer. Which one it is is not decided by the wh-word
# in it: "remind me when my dentist appointment is" and "remind me who my sister is" ask about the
# world and keep the limit, while "remind me what we said about the boiler" is the store's. So the
# store itself is asked, and the limit stands unless it can answer the ask behind the wrapper.
# The act has to be the whole line. "put the kettle on and it trips the switch" opens with the same
# verb as "put the kettle on" and then keeps going with its own subject, so it is a report about a
# fault, not an order - and "I can't do that one myself" refuses a job nobody asked for. The same
# goes for the commas ("take the rubbish out, its been there a week") and for a line that is a
# habit ("the washing machine still floods").
ACT_REPORT_TAIL = re.compile(
    r"(?:\b(?:and|but|then|so|because|till|until|when|while|whereas)\b|[,;])\s*"
    r"(?:it|they|he|she|i|we|the|my|its|this|that|there|nothing|nobody|everything|"
    r"someone|something)\b"
    r"|\b(?:still|keeps|kept|never|always|wont|cant|cannot|doesnt|didnt)\b"
    # "take the rubbish out, its been there a week": the comma is gone by the time this is read, so
    # the second half is caught by its own subject - a pronoun and what it goes on to say. An order
    # stops at the thing ("take the rubbish out", "put the oven on 200 for me"); nothing carries on
    # with "it", "they" or "we". "put the oven on its highest setting" is the possessive, which the
    # words after it do not look like a clause ("its highest"), so it stays an order.
    r"|\b(?:it'?s|its|it|they'?re|theyre|they|we'?re|we|i'?m|im|i|he'?s|she'?s|he|she|there)"
    r"\s+(?:not\s+)?(?:been|was|were|is|are|got|get|gets|went|goes|gone|split|splits|came|comes|"
    r"trips|cuts|leaks|floods|flooded|keeps|kept|stopped|broke|breaks|smells|smelt|died|works|"
    r"worked|fails|failed|\w+ing|full|empty|dirty|wet|broken|dead|stuck|blocked|loud|noisy|"
    r"cold|hot|freezing|boiling|on|off|open|shut|late|early)\b")


# Three readings that keep an instruction-shaped line out of the limit, because the person is not
# asking the bot to do the job:
#   - a choice ("take the bins out at night or morning", "put the oven on 180 or 200") is a question
#     about which, and the bot can answer that;
#   - a pronoun for the object ("put it in the oven at 200") is the speaker's own step, in the middle
#     of cooking, not an order to anyone;
#   - a temperature or a time ("on 200", "gas mark 6", "for 25 minutes") is a setting, which is how a
#     recipe step is said, not a job in the world.
ACT_CHOICE = re.compile(r"\bor\b")
ACT_OWN_STEP = re.compile(r"^\s*(?:it|them|that|this|those|these|one)\b")
ACT_SETTING = re.compile(
    r"\bgas\s+mark\s+\d+"
    r"|\b\d{2,3}\s*(?:c\b|\u00b0|degrees)"
    r"|\b(?:at|on|to)\s+\d{2,3}\b"
    r"|\b(?:for|about)\s+\d+\s*(?:mins?|minutes|hours?|hrs?)\b")


# A job asked of the bot in the polite form: "can you ring the council", "could you book me a
# table", "would you put that in my calendar". People ask a chatbot politely far more often than
# they order it about, and `_acts_for_me` read only the imperative and the objects it knew (a
# kettle, the bins, a table for two), so most polite asks reached the search hedge - the worst
# answer to "can you buy the tickets for me", because no search can buy them and the person asked
# the bot, not the internet. Three shapes are read here, each with its own line because the offer
# differs: a call needs the words before it is made, an errand needs the choosing, a date needs the
# phone's own calendar. A thing of theirs to read, print or send is a different limit with its own
# reader in this lane - it is their side of the screen, not a job in the world - and two lines for
# one shape would take the turn off each other.
POLITE_ASK = re.compile(
    r"^(?:(?:ok|okay|right|so|hi|hello|hey|and|thanks|ta|now|sorry|please)\s+)*"
    r"(?:(?:any\s+chance\s+)?(?:can|could|would|will)\s+(?:you|u)"
    r"|any\s+chance\s+(?:you|u)\s+(?:could|can|would|will))\s+(?:please\s+|possibly\s+)?"
    r"(?P<rest>[a-z0-9 ',.\-?!]+)$")
# A date put somewhere of theirs: the object is the calendar, the diary or the phone, and the verb
# has to be one that would move it there. "can you write my cv" is work the bot can do, so the
# verb alone is never enough.
ACTS_IN_A_DIARY = re.compile(
    r"\b(?:put|add|save|write|note|stick|move)\b.*\b(?:in|on|into|to)\s+(?:my|the)\s+"
    r"(?:calendar|diary|phone|notes?|list|fridge)\b")
# A call or a message to somebody. "talk through" and "speak up" are not asks to ring anyone, so
# speak and talk only count with "to" behind them.
# The act comes first in the ask ("ring the school"), so it is anchored: "can you copy the text
# from the email" has the word text as the thing, not the act, and a call is not the answer there.
ACTS_ON_A_PHONE = re.compile(
    r"^(?:just\s+|also\s+)?(?:(?:call|ring|phone|text|message|contact|chase)\b"
    r"|(?:speak|talk)\s+to\s+(?!me\b|us\b))")
# A purchase, a booking or something collected: the doing is theirs and the bot can only help
# choose. What is done to a form is not here ("can you fill in this form", "can you submit my tax
# return"): that is a thing of theirs on their own side, which has its own reader and its own offer
# (paste it in), and two lines for one shape would take the turn off each other.
ACTS_AN_ERRAND = re.compile(
    r"^(?:just\s+|also\s+)?(?:(?:book|reserve|buy|pay|purchase|renew|cancel|collect|pick\s+up|"
    r"apply|set\s+up|drop\s+off)\b|(?:get|ring|call|book|order)\s+(?:me|us)\s+(?:a|an|some)\b)")
# "Can you text me the list", "can you email me the letter": the person wants the words handed over
# in the chat, which the bot can do, so the ask is not a limit. "Call me a taxi" is the other way
# round - the article means something to be got for them, read as an errand above.
HANDS_IT_OVER_HERE = re.compile(
    r"\b(?:call|ring|phone|text|message|email|send|post|contact|chase)\s+(?:me|us)\b"
    r"(?!\s+(?:a|an|some)\b)")
# What nothing can buy or book, because it is not a thing: "can you buy me some time", "could you
# book me some rest", "can you pay attention". The object decides, not the verb.
NOT_A_THING_TO_GET = re.compile(
    r"\b(?:(?:some|a bit of|a little)\s+(?:time|rest|peace|quiet|space|slack)"
    r"|attention|my thoughts|the steps|a break|a rest|a day|a night|it a day|it a night)\b")
# What the bot can do itself: the same opener with one of these is a request it can meet ("can you
# write a message", "can you suggest a film", "can you check my spelling"), so the line keeps the
# answer it has. A reminder is in here too: the bot holds the job and the day, and the card about it
# says so better than a line about having no hands.
CAN_DO_ITSELF = re.compile(
    r"^(?:write|draft|rewrite|help|suggest|recommend|explain|remember|remind|tell|say|show|"
    r"pick\s+(?:one|which|between|the\b)|choose|plan|make|give|keep|freeze|cook|reheat|bake|"
    r"read|listen|work|sort|order(?!\s+(?:me|us)\b)|deal|spell|"
    r"check\s+(?:my\s+)?(?:spelling|grammar|writing|english|essay|answer|answers|maths|sums|"
    r"homework|work)|check\s+this|check\s+that|check\s+it)\b")
ACTS_ON_A_PHONE_LINES = (
    "I can't ring or message anyone for you - there's no phone on this end. Tell me who it is and "
    "what has to be said, and I'll help you find the words before you call.",
    "No phone here, so the call can't be mine. Give me the who and the one thing you need from "
    "them, and we'll work out what to say.",
)
ACTS_AN_ERRAND_LINES = (
    "I can't book, buy or pay for anything from here, sorry - the doing is yours. What I can do "
    "is the choosing: the options, the order to do it in and the questions to ask. Which part?",
    "Nothing in the world is mine to do - no booking, no paying. Tell me what you're after and "
    "I'll narrow it down, or work out what to check before you commit.",
)
ACTS_IN_A_DIARY_LINES = (
    "I can't put anything in your calendar - I only hold it for this chat, and it goes when the "
    "chat does. Put it in your phone with a reminder; tell me the date and I'll help you plan "
    "around it.",
    "Your calendar isn't something I can reach, sorry. Write it in your phone with a reminder, "
    "and say the day here and I'll help you get ready for it.",
)
# A clock is the one job people ask a bot for by name - "set a timer for 10 minutes", "wake me up
# at 7" - and the store's nod below answered it as if the timer were running. Nothing here can
# ring, so the limit is said in a few words and the two taps that do it are named.
ACTS_ON_A_CLOCK_LINES = (
    "No clock on this end - nothing here can ring or buzz. The timer in your phone's clock app "
    "does it in two taps; tell me what it's for and I'll help with the rest of it.",
    "I can't set a timer or an alarm, sorry - I'm only up while you are typing. Set it on your "
    "phone and tell me the job it's for; that part I can help with.",
)
# A document or a print job: the words are mine, the pressing of the button is theirs.
ACTS_ON_A_DOCUMENT_LINES = (
    "Nothing on this end can print, scan or send a file - no printer, no outbox. The print or "
    "share button on whatever you're reading this on does it; tell me what it is and I'll help "
    "with the rest.",
    "That one needs a printer or an inbox, and neither is mine. Do it on your own device, and "
    "bring me the wording or the order to send things in.",
)


# A job in the world said the way people actually type it: verb first, no "can you" in front.
# "text my mum", "book the tickets", "set a timer for 10 minutes", "save this for later" were
# all answered by the store's own acknowledgement - "Noted: text your mum", "Book the tickets -
# I'll remember that" - and a nod that reads as a job done is the worst answer of the lot: a
# person can believe the tickets are booked. The same three readings the polite form already has
# (`ACTS_ON_A_PHONE_LINES`, `ACTS_AN_ERRAND_LINES`, `ACTS_IN_A_DIARY_LINES`) answer the bare
# order, plus a clock and a document, which the polite form could not reach because "can you set
# an alarm" is an ask about how phones work.
ORDER_OPENER = re.compile(
    r"^(?:(?:ok|okay|right|so|hi|hello|hey|and|just|now|quick|quickly|please|ta|thanks)\s+)*"
    r"(?P<job>(?:text|message|whatsapp|sms|email|mail|ring|call|phone|facetime|contact|chase|book|"
    r"reserve|order|buy|purchase|renew|collect|pick\s+up|put|add|save|write|note|jot|set|wake|"
    r"alarm|print|scan|photocopy|copy|download|upload|send|forward|share)\b)(?P<tail>.*)$")
# Which of the jobs it is, read from the whole line. Each needs a thing or a place of theirs: an
# order with no object ("book it", "order one") is as likely a reply in the middle of a chat as
# an order to the bot, so the words that make it one are what count.
ORDER_A_MESSAGE = re.compile(
    r"^(?:text|message|whatsapp|sms|email|mail|ring|call|phone|facetime|contact|chase)\s+"
    r"(?:my|our|the|his|her|their|a|an|\w+'s)\s+\w+")
ORDER_A_BUY = re.compile(
    r"^(?:book|reserve|order|buy|purchase|renew|collect|pick\s+up)\s+(?:me\s+|us\s+)?"
    r"(?:a|an|the|some|two|three|four|more|my|our|another)\b")
ORDER_A_RECORD = re.compile(
    r"^(?:put|add|save|write|note|jot|stick|move)\b.*\b(?:in|on|into|to)\s+(?:my|the)\s+"
    r"(?:\w+\s+){0,2}(?:calendar|diary|phone|notes?|list|app|reminders?|fridge|whiteboard)\b"
    r"|^(?:save|keep)\s+(?:this|that|it)\b")
ORDER_A_CLOCK = re.compile(
    r"^(?:set|put)\s+(?:a|an|the|my)\s+(?:timer|alarm|countdown|reminder|stopwatch)\b"
    r"|^wake\s+me\b|^(?:set|put)\s+(?:a|an|the)\s+alarm\b|^alarm\s+me\b")
ORDER_A_DOCUMENT = re.compile(
    r"^(?:print|scan|photocopy|copy|download|upload|send|forward|share)\s+"
    r"(?:this|that|it|these|those|them|a|an|the|my|two|three)\b")
# The line goes on to report instead of ordering: "text my mum and she never answers" is about the
# mother, not an ask. The same guard `ACT_REPORT_TAIL` makes for the house tasks, kept separate so
# a tail added for one reading cannot quietly widen the other.
ORDER_A_REPORT = re.compile(
    r"\b(?:and|but|then|so|because|till|until|while)\s+"
    r"(?:it|they|he|she|i|we|the|my|its|there|nothing|nobody|everyone)\b"
    r"|\b(?:yesterday|last\s+night|last\s+week|this\s+morning|earlier|already|never|always|"
    r"every\s+day|usually|used\s+to|didnt|didn't|did|keeps|kept)\b")
# "call the doctor" on its own is a call somebody makes, and a bot that says "no phone on this
# end, tell me who it is and what has to be said" is more use than "call the doctor - noted".
# What is not a job for the bot: an emergency call (the safety card owns it) and a call about a
# thing rather than to a person ("call it a day").
ORDER_NOT_A_JOB = re.compile(
    r"\b(?:ambulance|paramedic|paramedics|999|911|112|fire\s+brigade|police|cops|101|"
    r"it\s+a\s+(?:day|night)|a\s+day|a\s+night|it\s+off|quits)\b")


def _an_order_it_cannot_do(clean):
    """The honest line for a job in the world typed as an order, or None.

    Only the shapes where the doing can only be the person's are read: a message to somebody, a
    purchase or a booking, something put in their calendar or notes, a timer, and a document. The
    offer after the limit is what makes it an answer - the words, the choosing, the order to do
    things in - so a line that is a thing to work out keeps the advice it gets elsewhere.
    """
    bare = " ".join(re.sub(r"[^a-z0-9 ']+", " ", str(clean or "").lower()).split())
    if not ORDER_OPENER.match(bare) or ORDER_A_REPORT.search(bare):
        return None
    if ORDER_NOT_A_JOB.search(bare):
        return None
    if ORDER_A_CLOCK.search(bare):
        return ACTS_ON_A_CLOCK_LINES
    if ORDER_A_RECORD.search(bare):
        return ACTS_IN_A_DIARY_LINES
    if ORDER_A_MESSAGE.search(bare):
        return ACTS_ON_A_PHONE_LINES
    if ORDER_A_BUY.search(bare):
        return ACTS_AN_ERRAND_LINES
    if ORDER_A_DOCUMENT.search(bare):
        return ACTS_ON_A_DOCUMENT_LINES
    return None


def _act_asked_of_me(clean):
    """The honest line for a job asked of the bot in the polite form, or None.

    Only the polite form is read: the imperative has `_acts_for_me` and `ACTS_FOR_ME` already,
    and its house tasks ("put the kettle on") are a different offer from these.
    """
    match = POLITE_ASK.match(" ".join(str(clean or "").lower().split()))
    if not match:
        return None
    rest = match.group("rest").strip()
    if not rest or CAN_DO_ITSELF.match(rest):
        return None
    if ACTS_IN_A_DIARY.search(rest):
        return ACTS_IN_A_DIARY_LINES
    if EMERGENCY_CALL.search(rest) or POLICE_CALL.search(rest):
        # "can you call an ambulance", "can you ring 999": the safety card owns this, and a line
        # about having no phone is the one answer that must not land on it.
        return None
    if NOT_A_THING_TO_GET.search(rest) or HANDS_IT_OVER_HERE.search(rest):
        return None
    if ACTS_AN_ERRAND.search(rest):
        return ACTS_AN_ERRAND_LINES
    if ACTS_ON_A_PHONE.search(rest):
        return ACTS_ON_A_PHONE_LINES
    return None


def _the_store_has_the_recall(clean, memory):
    """True when the memory store has the line a "remind me ..." asks for.

    The store is asked rather than a list of words here, because only the store knows what it can
    hand back: it answers "remind me what we said about the boiler" and "remind me where we
    started", and returns nothing for "remind me who my sister is". A word list in this file would
    be a second, drifting copy of that knowledge - the first cut of this had one, and every shape
    it waved through but the store could not answer fell to a nod ("Got it. Is there anything
    you'd like a hand with?") where the limit had been the honest answer.
    """
    try:
        from ..modules import memory_store
    except Exception:  # noqa: BLE001 - no store to ask, so the limit stands
        return False
    try:
        return bool(memory_store.respond(clean, memory if isinstance(memory, dict) else {}))
    except Exception:  # noqa: BLE001 - a reading that fails leaves the line to the limit
        return False


def _acts_for_me(clean, memory=None):
    """True when the line tells the bot to do a job in the world, which it cannot do."""
    bare = " ".join(re.sub(r"[^a-z0-9 ']+", " ", str(clean or "").lower()).split())
    # "keep me posted" is the idiom, and it asks for news rather than a job.
    if KEEP_ME_POSTED.search(bare):
        return False
    # ...except the jobs it can do half of, which are words: a message, a letter, a form. "can you
    # send an email for me" is answered by the drafting invite ("tell me who it's for and what you
    # want them to do"), and "can you sign this for me" by the line that says it cannot click or
    # print and offers to walk them through the screen. Saying "no hands" over the top of those
    # throws away the one useful half, so the readers that answer them are asked here.
    #
    # Only a reader with an answer takes the line off the limit. Standing down for the word alone
    # ("text", "email", "form") left the lines no reader wants - "text me the address", "email me
    # the list", "text me when youre outside" - with the shrug the limit had replaced, which is
    # the one thing worse than the limit.
    if A_MESSAGE_OR_A_FORM.search(bare):
        if (no_eyes.writes_the_message(clean)
                or no_eyes.cannot_see_your_thing(clean)
                or no_eyes.look_at_a_body_lines(clean, bare)):
            return False
    if REMIND_ME.match(bare):
        return not _the_store_has_the_recall(clean, memory)
    opener = ACT_OPENER.match(bare)
    if not opener:
        return False
    tail = bare[opener.end():]
    if ACT_REPORT_TAIL.search(tail):
        return False  # the line goes on about something else: it reports, it does not ask
    if not ACT_FOR_ME.search(bare):
        # Not addressed to the bot at all: a choice, the speaker's own step, or a setting.
        if ACT_CHOICE.search(bare) or ACT_OWN_STEP.match(tail) or ACT_SETTING.search(bare):
            return False
    if ACT_FOR_ME.search(bare):
        return True  # "book me a table", "call the doctor for me": the bot is the one asked to act
    verb = bare.split()[0]
    if verb not in HOUSE_VERB and not ADDRESSED.match(bare):
        return False  # not said to the bot and not a house task: the person's own errand
    if verb in ("call", "ring", "phone", "text", "email", "buy", "pay", "renew"):
        # "call the doctor" on its own is as likely to be asking for advice as telling the bot to
        # ring: only the line that says who it is for is an instruction.
        return False
    if verb in ("book", "reserve", "order"):
        return bool(BOOKING_THING.search(bare))
    # Said to the bot itself ("could you put the kids to bed"), the thing does not have to be one of
    # the house's: the line is an order whatever the object is. Said flat, it does.
    return bool(ADDRESSED.match(bare) or ACT_THING.search(bare))


def _reads_as_a_bad_stretch(clean):
    """True when the line is a bad stretch of time and nothing else."""
    words = [w.strip(".,!?;:") for w in clean.split()]
    for index, word in enumerate(words):
        if word not in BAD_STRETCH:
            continue
        before = " ".join(words[max(0, index - 4):index])
        if _a_claim_about_a_thing(before):
            continue
        after = words[index + 1:]
        if after[:1] in (["few"], ["couple"]) and len(after) > 1:
            after = after[1:]
        if after and after[0] in STRETCH_OF_TIME:
            return True
        if not after and any(w in STRETCH_OF_TIME for w in before.split()):
            return True  # "my week has been rough", "the week was hard"
    return False
def _cue_negated(words, cue):
    """True when a negator stands just in front of the cue: "not finished", "not yet finished".

    Two words is the widest that stays honest. One misses "not yet sorted"; three starts
    swallowing real wins - "i cant believe i finished it" and "not bad, i finished it" are both
    good news with a negator three words away. Three is only enough when a doubt word sits
    between them: "i don't think i'm happy" is not happy, and `turns_round` tells that apart
    from the "can't believe" that is delight.
    """
    for index, word in enumerate(words):
        if word != cue:
            continue
        if any(other in NEGATORS for other in words[max(0, index - 2):index]):
            return True
        before = words[max(0, index - 3):index]
        if set(before) & DOUBTED:
            return True
        if set(before) & DOUBT and turns_round(before):
            return True
    return False


def _a_state_in_the_past(words, index):
    """True when the state word at `index` is said in the past: "my wife was pregnant"."""
    return bool(set(words[max(0, index - 3):index]) & _WAS)


def _the_win_is_someone_elses(words, index):
    """True when the good thing at `index` is a crowd's, not the person's own.

    Reads back to the nearest subject and stops at the first one: "my friend told me i should be
    proud" is still the person's own pride, because the "i" is nearer the cue than the friend.
    What counts as someone else's is a crowd - the thing a person can be measured against, "everyone
    else", "all my mates". A relation on their own is not: "my mum finally finished chemo" is news
    a person is glad of, and withholding that cheer is not what this is for.

    A crowd feeling something about the person is still the person's: "everyone is happy for us",
    "everyone's proud of me" - the words after the cue say who it is about, so they are read too.
    """
    after = words[index + 1:index + 3]
    if after and after[0] in ABOUT_WORDS and set(after[1:]) & PERSON_WORDS:
        return False
    for j in range(index - 1, max(-1, index - 7), -1):
        word = words[j]
        if word in YOU_SUBJECTS:
            return False
        if word in CROWD:
            return True
        # "all my mates are sorted", "all her friends have got sorted": a whole set of people,
        # which is the same measuring stick as "everyone else" even though each one is a friend.
        if (word in loss.PEOPLE and word.endswith("s")
                and "all" in words[max(0, j - 3):j + 1]):
            return True
    return False


# "my laptop has finally died" is not good news: "finally" is a cue on its own, so the cheerful
# pool cheered a broken laptop ("Good for you! That's really lovely news."), a car that has
# given up ("That's great news - nice one") and a knee that has given out. The cue is spent when
# the thing right after it stops, so the line falls through to the readers below it.
THINGS_THAT_STOP = frozenset((
    "died", "dead", "broke", "broken", "collapsed", "failed", "stopped", "conked",
))
THINGS_THAT_STOP_AFTER_UP = frozenset(("gave", "given", "packed", "went"))
THE_WORDS_BETWEEN = frozenset(("has", "have", "had", "is", "was", "were", "s", "just", "now"))


# A pleasure that has gone out of everything is a low line, and it is said with the word
# "nothing" in front of the cue or with the enjoyment turned round: nobody who types it is telling
# you good news. "nothing makes me happy" has "happy" in it, which is a positive cue with nothing
# in the three words before it that the cue loop reads as a negator, so the cheerful pool said
# "Good for you! That's really lovely news." to a person saying the opposite. "nothing feels fun
# any more" and "i dont enjoy anything any more" carry no cue at all and got the neutral receipt,
# which is the same shrug at the same statement in a different word order.
#
# Only the plain sense is here. "nothing to do" is a boring afternoon and "nothing works" is a
# broken printer, so both are left alone; "nothing makes me happier than the dog" is a good thing
# said with a comparison, and the cue word there is "happier", which none of these patterns reach.
# The thing that gives pleasure, in the words people use for it. Read as a shape rather than as a
# list of phrasings: the same statement arrives as "nothing makes me happy", "nothing brings me
# joy", "nothing feels worth doing", "i dont get any pleasure out of anything", "fun has gone out
# of everything" and "i feel nothing", and every one of them is a person saying the pleasure has
# gone - none of them is news to be cheered or a shrug to be filed.
PLEASURE_WORD = (r"(?:fun|funny|joy|joyful|pleasure|enjoy(?:s|ed|ing|able)?|happy|happiness|"
                 r"smile|laugh|mood|worth(?:while|\s+doing)?|interest(?:s|ed|ing)?|"
                 r"look\s+forward\s+to|content|exciting|excites?)")
# "Nothing … the pleasure" with nothing in front of it: "nothing makes me happy", "nothing feels
# fun", "nothing lifts my mood", "there is nothing i enjoy". A comparison is the opposite statement
# and is left alone ("nothing makes me happier than the dog", "nothing beats a curry"), so a word
# that turns the pleasure into a comparison stands the reading down.
NOTHING_AND_A_PLEASURE = re.compile(
    r"\bnothing\b[^.?]{0,28}?\b" + PLEASURE_WORD + r"\b")
A_COMPARISON = re.compile(r"\b(?:than|beats?|more\s+than|as\s+much\s+as)\b")
# The other half of the same sentence: a negator in front of the pleasure and everything as its
# object - "i dont get any pleasure out of anything", "i never enjoy anything", "no joy from
# anything", "i stopped enjoying things". The object is what makes it about their life rather than
# their taste: "i dont enjoy horror films" is a fact about films and keeps the turn.
NOTHING_NEGATED = re.compile(
    r"\b(?:no|not|never|dont|don'?t|doesnt|doesn'?t|cant|can'?t|cannot|stopped|without)\b"
    r"[^.?]{0,24}?\b" + PLEASURE_WORD + r"\b[^.?]{0,20}?"
    r"\b(?:anything|nothing|much|things|life|it|myself|any\s?more|anymore|at\s+all)\b")
# "fun has gone out of everything" is the same statement said from the other end.
PLEASURE_GONE_OUT = re.compile(
    r"\b(?:fun|joy|pleasure|interest|point|enjoyment)\b\s+(?:has|have|had)\s+"
    r"(?:gone|gone\s+right|all\s+gone)\s+out\s+of\b")
# The shortest way it is said at all, plus the pleasure named after the verb ("enjoying nothing")
# and the plain "nothing feels good" - which is not "nothing is good on telly", so the verb stays
# the thing that makes it a statement about them.
FEELING_NOTHING = re.compile(
    r"\bfeel(?:s|ing)?\s+nothing\b|\bnothing\s+matters\b"
    r"|\bnothing\s+(?:makes\s+me\s+)?feels?\s+(?:good|right|nice|better)\b"
    r"|\b(?:enjoy|enjoying|enjoyed)\s+nothing\b")


# Two shapes built from the same words that are not this statement at all, both found by the
# deck and both answered better by what came before this reading.
#
# A limit on the answer above ("nothing with a laugh track though", "no subtitles") is not a
# statement about their life: the pleasure word inside it belongs to the thing they are asking to
# leave out. `limit.NOTHING_THAT_LIMITS` and `limit.a_limit_on_the_answer` are the one reading of
# that shape, shared with the module that takes things out of an answer.
#
# A pleasure about one named thing: "i got the promotion and i don't feel happy about it" is a
# person asking whether that is odd, not a person saying the pleasure has gone out of everything,
# and the promotion answer is what they need. The reading wants everything as the object, so a
# pleasure tied to "it", "that" or a named thing stands it down.
PLEASURE_ABOUT_ONE_THING = re.compile(
    r"\b(?:happy|glad|pleased|excited|thrilled|proud)\s+about\s+"
    r"(?:it|that|this|them|him|her|the\b|my\b|his\b|her\b|their\b|our\b)")


def reads_as_no_pleasure(clean):
    """True when the line is a person saying the pleasure has gone out of everything."""
    text = " ".join(str(clean or "").lower().split())
    if not text:
        return False
    # "nothing feels better than this" and "nothing makes me happier than the dog" are the good
    # thing said with a comparison, which is the opposite statement in the same words.
    if A_COMPARISON.search(text):
        return False
    if NOTHING_THAT_LIMITS.search(text) or PLEASURE_ABOUT_ONE_THING.search(text):
        return False
    if FEELING_NOTHING.search(text) or PLEASURE_GONE_OUT.search(text):
        return True
    if NOTHING_AND_A_PLEASURE.search(text):
        return True
    return bool(NOTHING_NEGATED.search(text))


# A question about the bot's own body or abilities is the one ask that is always answerable, and it
# was reaching the search hedge: "can you drive" and "can you feel pain" were told that "a quick
# search online will get you a solid answer", which no page can give, because the subject is this
# program. The answer is the same for every verb in the list - a program has no body, no senses and
# no car keys - so the pool says that once and stays true, and then offers the half it can do.
ABOUT_THE_BOT_LINES = (
    "Nothing to do it with, I'm afraid: I'm a program, so no body, no senses and no car keys. Ask "
    "me the thing you would ask a friend and I will take that half of it on.",
    "No, and I would rather say so than guess. I am a program in a chat window, so what I can do "
    "is read, remember this conversation and think the question through with you.",
    "Not at all - there is no body here. If it is something you are wondering about, ask it "
    "anyway: plenty of that I can still help with.",
)

# The shape is the whole line, because the subject is the bot. "Can you smell gas" is their
# kitchen, "can you feel the baby moving" is a pregnancy and "can you drive me to the airport" is
# a lift, so a verb with a thing of theirs after it is not this question: only a bare sense or
# body verb, optionally with a word like "pain" or "anything" that names nothing of theirs.
ABOUT_THE_BOT = re.compile(
    r"^(?:can|could)\s+(?:you|u)\s+(?:actually\s+|even\s+|really\s+|still\s+)?"
    r"(?:drive|smell|taste|feel|see|hear|touch|breathe|eat|drink|swim|run|walk|dance|sing|laugh"
    r"|cry|shiver|sweat|blink|wave|hold|hug|kick|jump|climb|fly)\b"
    r"(?:\s+(?:anything|something|things?|pain|cold|the\s+sun|a\s+car|at\s+all|either|yet|though))?"
    r"\s*(?:please|then)?\s*\?*\s*$", re.I)


def reads_as_a_question_about_the_bot(clean):
    """True for "can you drive", "can you feel pain": the whole line, about this program."""
    text = " ".join(str(clean or "").lower().split())
    return bool(text) and bool(ABOUT_THE_BOT.match(text))


# What is said to a person whose pleasure has gone out of everything, once the readings have had
# their turn. The gentle pool is what this file says to a low line, and one of its lines offers
# films, a series and a book that "leave you better than they found you" - which is the one reply
# that does not help somebody who has just said nothing gives them any pleasure: it answers a flat
# fortnight with the telly. The line here says what the flatness is worth doing about, names the
# one small concrete thing that tends to help, and asks the question that puts the person's own
# week back in it, so the turn is never just sympathy.
PLEASURE_GONE_LINES = (
    "That flatness is a miserable thing to carry, and it is not laziness or a mood to be talked "
    "out of. More than a couple of weeks of it is worth saying to a GP, and until then the "
    "smallest thing that helps is one thing you used to like, put back in this week on a day you "
    "pick. What did you look forward to a year ago?",
    "I'm sorry - when nothing gives pleasure the days go flat and everything takes effort, and "
    "waiting for it to lift is the one thing that does not work. Tell one person, and put one "
    "small piece of what you used to enjoy back on the calendar this week; if it has been weeks, "
    "say it to a GP. What did you like doing before this started?",
    "That is worth taking seriously rather than shaking off: nothing giving pleasure for weeks is "
    "something a GP wants to hear about, and it is not a failing to say so. Until then the "
    "things to try are small and concrete - one walk, one person, one thing you used to look "
    "forward to, this week. Which of those feels least impossible?",
)


def _a_thing_stopping_after(words, i):
    """True when the words after a cue name that thing stopping ("has finally died")."""
    after = list(words[i + 1:i + 5])
    while after and after[0] in THE_WORDS_BETWEEN:
        after.pop(0)
    if not after:
        return False
    if after[0] in THINGS_THAT_STOP:
        return True
    if after[0] in THINGS_THAT_STOP_AFTER_UP and len(after) > 1 and after[1] in ("up", "in",
                                                                               "out"):
        # "gave up smoking" is a thing given up, so the cue stands; "has given up" on its own,
        # "given out", "packed in" and "gave up on me" are the thing stopping.
        return len(after) == 2 or after[2] in ("on", "it", "them", "me", "him", "her", "us")
    return False


# A harm the person reports is a bad line however it is worded, and the day pool used to cheer it:
# "i dislocated my shoulder" was answered "Nice one. How did the rest of it go?", "my back went last
# week" "Good to hear. What was the best bit?", "i got a concussion playing football" "How was it,
# overall?" and "i have covid" "Noted: you have covid." Every one of those is a past-tense account
# with no mood cue in it, so `_mood` read it as neutral and the small-day pool took the turn.
#
# The two shapes are the ones people say it in: the person as the doer of a hurt ("i broke my
# wrist", "i cracked a rib", "i dislocated my shoulder") and the person as the one it happened to
# ("i got a concussion", "i have covid", "i had a miscarriage"). A hurt with no owner is not this
# ("my car broke down", "the boiler broke"), and neither is a thing that is not the body - the
# owner words are what keep "i broke my phone" the phone card's, which answers it anyway.
_A_HURT_DONE = re.compile(
    r"\b(?:i|we)\s+(?:just\s+|nearly\s+|think\s+i\s+)?(?:have\s+|had\s+|ve\s+)?"
    r"(?:broke|broken|fractured|cracked|dislocated|sprained|tore|torn|snapped|slipped|"
    r"hurt|injured|done)\b", re.I)
# The part has to be in the line for it to be a hurt done to the person: the same verb is a
# phone, a car and a boiler in other lines, and every one of those has a card of its own that
# answers it. A body word is the whole test, so "i broke my wrist", "i cracked a rib" and "i
# dislocated my kneecap" are this and "i broke my phone" is the phone card's.
_A_BODY_WORD = re.compile(
    r"\b(?:back|knees?|legs?|feet|foot|ankles?|hips?|arms?|elbows?|wrists?|hands?|fingers?|"
    r"thumbs?|shoulders?|ribs?|neck|toes?|heels?|shins?|calves|calf|thighs?|collarbone|"
    r"jaw|nose|eyes?|head|spine|disc|kneecap|ligaments?|muscles?|tendons?|bones?|"
    r"teeth|tooth|nail|shoulder blade|lip|lips|cheek|cheeks|chin|ears?|eyebrow|"
    r"forehead|scalp)\b", re.I)
# The illness and the diagnosis, which are said with "have", "had" or "got". Only the words that
# are no everyday thing: "i had a fall" is a hurt done, "i had a fit" is a seizure, and "i had a
# stroke" is not a stroke of luck - but a line that says which one it was is left to the cards.
_A_HARM_HAD = re.compile(
    # "i've had stitches" is the same report as "i had stitches", so the contracted subject is
    # read as well as the spaced one. Without it the shorthand got "How was it, overall?".
    r"\b(?:(?:i|we)\s+(?:(?:have|had|has)\s+been\s+)?(?:have|had|got|caught|was given|were given|"
    r"been given|been told|was diagnosed with|diagnosed with)|"
    r"(?:i've|we've|ive|weve)\s+(?:had|got|been given|been diagnosed with))"
    r"\s+(?:to have\s+|to get\s+)?"
    # "i got four stitches in my chin" is the same report as "i got stitches", and the count in
    # front of them is what the first draft could not read: it was answered "Nice one. How did the
    # rest of it go?".
    r"(?:a|an|the|my|some|a few|a couple of|two|three|four|five|six|seven|eight|nine|ten|\d+)?\s*"
    r"(?:concussion|concussions|stitches?|staples?|whiplash|pneumonia|sepsis|septicaemia|meningitis|"
    r"covid|coronavirus|shingles|glandular fever|miscarriage|stillbirth|seizure|seizures|"
    r"stroke|heart attack|blood clot|pulmonary embolism|breakdown|relapse|"
    r"chemo|chemotherapy|radiotherapy)\b", re.I)


# The illness half of the same report is a rule, not a list of the ones that came up. A person
# says what they have with "have", "had", "got" or "caught" and then names it, and the naming is
# what makes it an illness: a head word ("infection", "bug", "flu", "cold", "temperature"), or a
# word that only illness names end in ("bronchitis", "norovirus", "pleurisy", "chickenpox"). The
# first draft listed covid, shingles and pneumonia, so "i had the flu", "i had the norovirus",
# "i had a uti" and "i had bronchitis" were all still cheered ("Nice one. How did the rest of it
# go?") - the same bug in the same shape, one noun over.
_A_ILLNESS_WORD = (
    r"(?:[a-z]+\s+){0,2}?"
    r"(?:infections?|bugs?|virus(?:es)?|flu|influenza|fever|colds?|cough|temperature|"
    r"poisoning|disease|illness|ailment|condition|attack|migraines?|seizures?|"
    r"sore throat|sickness|nausea|diarrhoea|diarrhea|rash|abscess|cyst|ulcer|thrush|"
    r"gout|shingles|covid|coronavirus|malaria|tuberculosis|hepatitis|uti|dvt|copd|ibs|mrsa|"
    r"strep|\w+(?:itis|osis|aemia|emia|iasis|pox|virus))"
)
_A_HARM_ILL = re.compile(
    # "i have been diagnosed with sepsis" is how a lot of people say a diagnosis, and the "been"
    # in the middle put it back on the day pool: the auxiliary is read with or without it.
    r"\b(?:(?:i|we)\s+(?:(?:have|had|has)\s+been\s+)?(?:have|had|got|caught|was given|were given|"
    r"been given|been told|was diagnosed with|diagnosed with)|"
    r"(?:i've|we've|ive|weve)\s+(?:had|got|been given|been diagnosed with|"
    r"caught))"
    r"\s+(?:to have\s+|to get\s+)?"
    r"(?:a|an|the|my|some|a few|a couple of|two|three|four|five|six|seven|eight|nine|ten|\d+)?\s*"
    + _A_ILLNESS_WORD + r"\b", re.I)
# The same words where they are not an illness at all: a cold drink is a drink, a bug in the code
# is a program, and a temperature or a condition can be the setting of a thing.
_A_HARM_ILL_NOT = re.compile(
    r"\b(?:cold (?:one|beer|drink|water|shower|bath|snap|call|weather|night|morning|day|"
    r"evening|outside|front|shoulder|hands|feet)|"
    r"bugs? (?:in|on) (?:my |the )?(?:code|computer|laptop|phone|app|program|software|system)|"
    r"virus (?:on|in) (?:my |the )?(?:computer|laptop|phone)|"
    r"temperature (?:setting|gauge|dial|outside|gauge)|"
    r"sickness (?:policy|pay|record|note)|"
    r"in (?:good|no|great|perfect|top) condition|condition of (?:the|my) (?:car|house|road)|"
    r"attack of (?:the )?(?:nerves|conscience)|"
    r"fever pitch|cabin fever|spring fever)\b", re.I)


# The same words in a phrase that is not a harm: "i had a stroke of luck" is a good day and "i
# broke the ice at the meeting" is a small one. This keeps *this* reader off them - what a person
# gets for those lines is another reader's answer, and it is not the warm pool this change adds.
# A harm is a thing that happens to a body, and these say so in words that only look
# like one.
_A_HARM_IDIOM = re.compile(
    r"\b(?:stroke of (?:luck|genius|good luck|the brush)|brush ?stroke|stroke of a pen|"
    r"broke the ice|broke the news|broke even|broke the bank|broke a record|broke the rules|"
    r"broke a promise|broke the silence|cracked a joke|cracked a smile|cracked on|"
    r"cracked a window|slipped my mind|slipped away|tore a strip off|torn between)\b", re.I)
# A knock that took the person off something, a joint that came out of its socket and a week in
# agony are the same report in other words: "i got knocked off my bike" was asked how it went
# ("How was it, overall?"), "my shoulder came out of its socket" the same, and "i have been in
# agony all week" was said back ("Noted: you have been in agony all week."). None of them names an
# illness or a part, so the hurt words above miss them.
_A_HARM_KNOCK = re.compile(
    r"\b(?:knocked|thrown|shoved|swiped|swept)\s+off\s+(?:my|our|his|her|their|the|a)\b"
    r"|\bhit\s+by\s+a\s+(?:car|van|lorry|truck|bus|taxi|bike|motorbike|cyclist)\b", re.I)
_A_OUT_OF_SOCKET = re.compile(
    r"\bcame out of (?:its|the|my) socket\b|\bout of (?:its|the) socket\b"
    # a joint that came out and went back in is said without the socket, and "my shoulder came out
    # again" was answered "Good to hear. What was the best bit?" - the part is what makes it a
    # report, so a car that "came out" and a tooth that "came out" keep their own answers.
    r"|\b(?:my|our|his|her|their|the)\s+(?:shoulders?|knees?|kneecap|hips?|elbows?|jaw|"
    r"ankles?|fingers?|thumbs?|wrist|toe)\s+(?:came|comes|went|goes|popped|pops) out\b",
    re.I)
_A_IN_AGONY = re.compile(r"\bin (?:absolute |sheer |real )?agony\b", re.I)
# A part that "went" is the way people say a back or a knee gave out: "my back went last week" is
# the same report as "my back went", and the day pool asked how the week went.
_A_PART_WENT = re.compile(
    r"\bmy\s+(?:back|knee|knees|leg|arm|shoulder|hip|ankle|neck)\s+(?:just\s+|suddenly\s+)?"
    r"(?:went|gone|gave way|gives way)\b", re.I)


# A hurt somebody else did to the person is the same report in the other direction, and the day pool
# cheered it: "he held a knife to my throat" was answered "Good to hear. What was the best bit?" and
# "his friend spat at me" "Noted: his friend spat at you." The person is the object here, not the
# doer, and the safety cards catch most of the family ("my ex hit me", "he punched me in the face"
# are all cards) - this is the floor's backstop for the ones they miss, so the worst it can do is
# answer with the warm line instead of a cheer.
#
# Who can do it is a shape, not a list of relatives: he, she, they, someone, somebody, a man, and
# any "my/his/her/their/our <person>". What they do is a hurt with the person as its object.
_A_SOMEONE = (
    r"(?:he|she|they|someone|somebody|anyone|"
    r"(?:a|the)\s+(?:man|woman|lad|bloke|chap|guy|girl|boy|teen|carer|nurse|neighbour|neighbor)|"
    r"(?:my|his|her|their|our)\s+\w+)")
_A_HURT_BY_SOMEONE = re.compile(
    # someone hits, kicks, slaps, punches, bites or burns the person
    r"\b" + _A_SOMEONE + r"\s+(?:\w+\s+){0,2}?"
    r"(?:hit|punch(?:ed|es|ing)?|kick(?:ed|s|ing)?|slapp?(?:ed|ing)|smack(?:ed|ing)?|"
    r"beat|beats|beating|beaten|headbutt(?:ed)?|bit|bites|burn(?:ed|t|s)|"
    r"chok(?:ed|ing)|strangl(?:ed|ing)|stabbed|stabs|raped|molested|groped|"
    r"dragg?(?:ed|ing)|whipp?(?:ed|ing)|belt(?:ed|ing))\s+(?:me|us)\b"
    # the same with a part of them named: "he punched me in the face", "my ex grabbed my arm"
    r"|\b" + _A_SOMEONE + r"\s+(?:\w+\s+){0,2}?"
    r"(?:hit|punched|kicked|slapped|grabbed|pinched|twisted|yanked|wrenched|bit|bitten)\s+my\s+\w+"
    # a push or a shove with a place in it, because "she pushed me to apply" is not a hurt
    r"|\b" + _A_SOMEONE + r"\s+(?:\w+\s+){0,2}?(?:push(?:ed|es|ing)?|shov(?:ed|es|ing)?)\s+"
    r"(?:me|us)\s+(?:down|into|against|over|off|up|to the)\b"
    # a thing thrown at the person, or spit
    r"|\b" + _A_SOMEONE + r"\s+(?:\w+\s+){0,2}?(?:threw|throws|tossed|spat|spits?)\b"
    r"[^.?!]{0,25}?\bat\s+(?:me|us)\b"
    # a weapon held or pointed at the person
    r"|\b(?:held|holds|holding|put|puts|pointed|pointing|pressed|had|pulled)\s+"
    r"(?:a|an|the|his|her|their)\s+(?:knife|gun|blade|scissors|hammer|bat|belt|bottle|"
    r"glass|razor|needle|pillow|cushion)\s+(?:to|at|against)\s+(?:my|her|his|our)\s+\w+",
    re.I)
# The same words where nobody was hurt: "he hit me up" is a message, "he hit on me" is flirting,
# "she kicked me out" is a flat, "he beat me to it" is being quicker, and a boss who "pushed me
# into applying" is a boss.
_A_HURT_BY_SOMEONE_NOT = re.compile(
    r"\b(?:hit me up\b|hit on me\b|kicked me out\b|beat me (?:at|in|to)\b|"
    r"bit my head off\b|grabbed my (?:attention|eye)\b|"
    r"pushed (?:me|us) into \w+ing\b|"
    r"burn(?:ed|t) me (?:out|a copy|a cd)\b)", re.I)


# A part taken out is the same kind of report and the word alone is not, because "i have a sweet
# tooth" is not a harm. It was answered "Sounds alright. Anything good in it?", and "i had my
# appendix out last week" was answered "Nice one. How did the rest of it go?" - the same flat
# report in another part.
_A_PART_OUT = re.compile(
    # the verb is droppable, because people say "my appendix out last week" and "my tooth out on
    # friday": the part and what happened to it are the report, and the verb in front is optional.
    r"\b(?:(?:had|have|having|needed|need|getting|got)\s+)?(?:to have\s+|to get\s+)?"
    r"(?:a|an|my|two|some|the)\s+(?:tooth|teeth|wisdom tooth|wisdom teeth|molars?|"
    r"appendix|tonsils?|adenoids|gallbladder|gall bladder|kidney stone|cataract|"
    r"splinter|ingrown nail|nail)\s+"
    r"(?:out|removed|taken out|pulled|drained)\b", re.I)


# A number of months is a prognosis when it is what a person has been given or what they have
# left: "i've been given six months" was answered "You've been given six months, how long have you
# been at it?", which is the worst reply in this file. The money and notice shapes say the same
# number for something that ends rather than a life, so they are read out first.
_A_PROGNOSIS = re.compile(
    r"\b(?:been given|given|been told (?:i (?:have|'ve|have got|got)|there (?:is|are))|"
    r"told i (?:have|'ve|have got|got))\s+(?:about\s+|only\s+|maybe\s+|perhaps\s+)?"
    r"(?:a|two|three|four|five|six|nine|ten|twelve|eighteen|a few|a couple of)\s+"
    r"(?:more\s+)?(?:days|weeks|months|years)\b"
    r"|\b(?:two|three|four|five|six|nine|ten|twelve|eighteen|a few|a couple of)\s+"
    r"(?:more\s+)?(?:weeks|months|years)\s+(?:left|to live|at most|maybe)\b"
    r"|\b(?:terminal(?:ly)? (?:ill|illness|cancer)|palliative care|in a hospice|"
    r"end of life care)\b", re.I)
# The same words for a thing that ends, not a life: a payment plan, a notice period, a sentence.
_A_PROGNOSIS_THAT_IS_NOT = re.compile(
    r"\b(?:to pay|to repay|to clear|to save|to appeal|to file|to finish|to complete|"
    r"notice|sentence|probation|tenancy|contract|lease|to build|to train|to study|"
    r"to sell|to deliver|warranty|guarantee|to get out of)\b", re.I)


def _a_harm_said(clean):
    """True when the line reports a harm done to the person, or an illness they have.

    Read by `_mood`, so the line is a bad line and the warm pool answers it rather than the day
    pool asking how it went. A line that already says it is over ("i broke my wrist years ago")
    is still a harm they told the bot about, and the warm line fits it better than a cheer.
    """
    said = " ".join(str(clean or "").lower().split())
    if not said:
        return False
    if _A_HARM_IDIOM.search(said):
        return False
    if _A_PART_OUT.search(said):
        return True
    if _A_PROGNOSIS.search(said) and not _A_PROGNOSIS_THAT_IS_NOT.search(said):
        return True
    if _A_HURT_DONE.search(said) and _A_BODY_WORD.search(said):
        return True
    if _A_HURT_BY_SOMEONE.search(said) and not _A_HURT_BY_SOMEONE_NOT.search(said):
        return True
    if _A_HARM_ILL.search(said) and not _A_HARM_ILL_NOT.search(said):
        return True
    return bool(_A_HARM_HAD.search(said) or _A_PART_WENT.search(said)
                or _A_HARM_KNOCK.search(said) or _A_OUT_OF_SOCKET.search(said)
                or _A_IN_AGONY.search(said))


# A record broken is an achievement and an ice broken is a room warming up, but "broke" is a bad
# cue because a wrist, a phone and a boiler break: somebody who had just broken a running record was
# condoled ("Ugh, that's a lot to carry. What would make today a bit easier?"). The thing broken is
# what says which it is, so the phrases where it can only be good are read out before the cue.
_A_BREAK_THAT_IS_GOOD = re.compile(
    r"\bbroke(?:n)?\s+(?:a|the|my|our|his|her|their|new|world|personal|course|club|national)\s+"
    r"(?:\w+\s+)?(?:records?|ice|sweat|ground|habit|cycle|deadlock|stalemate|personal\s+best)\b"
    r"|\bbroke\s+even\b"
    # "i broke through" is done with something, and "i broke through the wall" is a wall: the
    # phrase only counts where nothing follows it.
    r"|\bbroke\s+through\b(?!\s+(?:the|a|an|my|our|his|her|their)\s)"
    r"|\bbreak(?:ing)?\s+a\s+record\b", re.I)
_BREAK_WORDS = frozenset(("broke", "broken", "breaking", "breaks"))


def _mood(words, clean=""):
    """'positive', 'negative' or 'neutral', from the words of a statement.

    A cue only says which way the line goes when nothing in front of it turns it round: "not
    happy" is a bad line, not a good one, and a cue that is turned round the other way ("not
    terrible") is left out rather than counted either way. Without this the cheerful pool
    congratulates someone who has just said they feel awful, which is the reply people
    remember. A cue inside an aim is not a mood at all ("i want to lose weight"), and neither is
    one behind "nearly"/"almost" ("i nearly finished it"), which is not done and not condoled.
    """
    words = tuple(words)
    # A stated dislike is a fact about their taste, not a bad day: "hate" and "can't stand" are
    # mood words too, and "that sounds rough" is an answer for something that happened to them.
    if ack.only_a_dislike(clean):
        return "neutral"
    # A limit on the answer above is not a mood: the pleasure word inside it is part of the thing
    # the person is asking to leave out (see a_limit_on_the_answer).
    if a_limit_on_the_answer(clean):
        return "neutral"
    # The pleasure gone out of everything is read before the cues, because its own words are the
    # cheerful ones: "nothing makes me happy" is the low line the pool is for, not good news.
    if reads_as_no_pleasure(clean):
        return "negative"
    good = bad = False
    if "ill" in words and _reads_as_illness(clean):
        bad = True
    # A symptom said with nothing else around it ("ive got a sore throat", "ive got a rash on my
    # arm") is already looked after by the symptom pools, and reading it as a harm here sends it to
    # the generic acknowledgement instead ("That sounds rough. If you want, I can help you think
    # through what to do next") - the line that used to say what to do. A harm that is an injury,
    # a knock, a diagnosis or a thing done to them still reads as bad.
    if not good and _a_harm_said(clean) and not reads_like_a_symptom(clean):
        bad = True
    for i, word in enumerate(words):
        if _in_an_aim(clean, word):
            continue
        # "bit of a rubbish week" is a mood and "take the rubbish out" is a chore: a word that
        # is also a thing only counts where something says what a thing was like (see JUNK_CUES).
        if word in JUNK_CUES and _a_mood_word(words, word):
            bad = True
            continue
        if word in _BREAK_WORDS and _A_BREAK_THAT_IS_GOOD.search(clean):
            # "i broke a record" is the best day of the year, and the cue would have condoled it.
            good = True
            continue
        if word not in POSITIVE_CUES and word not in NEGATIVE_CUES:
            continue
        # A cue with an everyday sense of its own is only a mood where the sentence around it
        # says so. "fired" is the one here: "i got fired" and "i was fired" are a job gone, and
        # "they fired me" the same, but "i fired a pot in the kiln yesterday" is pottery and "i
        # got fired up about the match" is the opposite of a bad day - both were answered "sorry
        # to hear that" and "that's frustrating" for a good afternoon.
        if word in A_MOOD_WITH_A_CATCH:
            before = set(words[max(0, i - 3):i])
            after = words[i + 1] if i + 1 < len(words) else ""
            if after == "up":
                # "i got fired up about the match" is keen, not a bad day: the phrase is the
                # opposite of the cue's sense, so it is the cheerful pool's, not nobody's.
                good = True
                continue
            if not (before & A_MOOD_WITH_A_CATCH[word]) and after not in ("me", "him", "her",
                                                                          "them", "us"):
                continue
        # Any of the three words before it can turn it round: "didn't get the job", "not at
        # all happy".
        window = words[max(0, i - 3):i]
        if set(window) & NEARLY:
            continue
        back = _cue_negated(words, word)
        if word in PAST_STATE_CUES and _a_state_in_the_past(words, i):
            # A state that was is not news now: "my wife was pregnant" was congratulated by the
            # bare cue in POSITIVE_CUES, and a pregnancy that is over is the last thing to be
            # cheerful about. An event in the past is still an event ("i was promoted" is news
            # they want to hear), so this reads the state words only.
            continue
        if word in POSITIVE_CUES and _a_thing_stopping_after(words, i):
            # The cue is spent: a thing that stopped is not a thing to cheer.
            continue
        if word in POSITIVE_CUES:
            # "nothing makes me happy any more" is not good news with a "not" in front of it:
            # the cue is turned round by the word saying there is none of the thing, and a
            # friend hears the complaint rather than the cue.
            if _no_such_thing_before(words, i):
                back = True
            if back:
                # "not happy" is a bad line. Not every turned word is: a result is not
                # congratulated and not condoled either - "i never finished it" is a plain fact,
                # and "that sounds rough" would be reading a feeling into it.
                if word in STATE_CUES:
                    bad = True
            elif word in A_WAIT_ENDING and SOMETHING_CAME_APART.search(clean or ""):
                # "the boiler finally died" is a wait that ended in a broken boiler, not good
                # news: the cue is about the wait, and the line says what came of it. The line
                # falls through to the readers below rather than to the negative pool, because a
                # thing that broke is a job to do more often than a loss to be condoled.
                continue
            elif _the_win_is_someone_elses(words, i):
                # Somebody else's win is not a reason to cheer them: "everyone else has got it
                # sorted and i havent" is a person saying they are behind, not a person telling
                # you good news. The cue is spent, so the line falls through to the readers
                # below it rather than to the negative pool.
                continue
            else:
                good = True
        elif not back or set(window) & AIM_HEADS:
            # A negated aim is the fear itself: "i dont want to lose the house" is not a denial
            # of the loss, it is the loss they are afraid of.
            bad = True
    if bad:
        return "negative"
    if good:
        return "positive"
    return "neutral"


def _no_such_thing_before(words, i):
    """True when the cue is the thing a word meaning none of it is said about.

    "nobody makes me feel good" puts three words between the quantity and the cue, so the
    three-word window the negators are read in is not wide enough; a contrast word starts a new
    claim and ends the search ("nobody believed i could do it but i did" is good news).
    """
    for step in range(1, 9):
        if i - step < 0:
            return False
        word = words[i - step]
        if word in CONTRAST:
            return False
        if word in NOTHING_AT_ALL or (word == "one" and i - step - 1 >= 0
                                      and words[i - step - 1] == "no"):
            return True
    return False


def _mixed_seed(text):
    """A number that changes when the line changes.

    `_choose` adds up letter values, which two lines of the same length can share: the four
    outcome pools are all about the same length, so a sum gave several threads the same sentence.
    """
    value = 7
    for char in str(text or ""):
        value = (value * 31 + ord(char)) % 1000003
    return value


# A pool line that tells the person how they feel is only drawn when the line gives a sign of
# feeling. "my mum is moving to spain in june" is a plan somebody is watching take shape, and the
# leaving pool answered it "Nobody has done anything wrong and it still hurts" - a hurt the person
# never mentioned, said with sympathy for a decision that may be half proud. The same pool's other
# lines ask instead of telling ("how far is it, and are you a phone-call pair"), so the plan keeps
# an answer either way.
#
# Only an assertion counts: a feeling word inside a question is the reply asking, not the bot
# telling - "what will you miss most?" is a fair thing to ask about a move nobody has called sad -
# so a line is dropped when one of its *statements* names a feeling.
SAYS_A_FEELING = re.compile(
    r"\b(?:hurts?|hurting|stings?|stung|miss(?:es|ed)?|dreading|dreads|sad|upset|gutted|"
    r"lonely|ach(?:e|es|ing|y)|cry(?:ing)?|broken|struggling|hate|worried|devastated)\b",
    re.IGNORECASE)
A_FEELING_IN_THE_LINE = re.compile(
    r"\b(?:hurts?|hurting|stings?|stung|(?:will|do|would|could)\s+miss|miss(?:es|ed)\b(?!\s+\?)|"
    r"dreading|sad|upset|gutted|lonely|ach(?:e|es|ing|y)|cry(?:ing)?|broken|struggling|hate|"
    r"worried|devastated|hard|tough|quiet|empty)\b",
    re.IGNORECASE)


def _only_what_the_line_gives(pool, clean):
    """The pool minus the lines that tell the person how they feel, unless they said it."""
    if A_FEELING_IN_THE_LINE.search(clean or ""):
        return pool
    kept = []
    for line in pool:
        asserts = False
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            if sentence.rstrip().endswith("?"):
                continue
            if SAYS_A_FEELING.search(sentence):
                asserts = True
                break
        if not asserts:
            kept.append(line)
    return tuple(kept) or pool


def _choose(options, memory, clean, seed_text=None):
    """One option, varied by the line itself and never the reply just given.

    A pool as short as NEUTRAL's three lines cannot keep the five-reply promise: once all three
    are in the window nothing is fresh, and restoring the whole pool brings back the line just
    used - "stacked up with emails" straight after "back to school", two of the same kind of
    reply in a row, which reads like the bot stopped listening. So the wide window holds while
    it can, and what is never repeated is the reply just given.
    """
    turns = memory.get("turns") or []
    recent = [t.get("bot") for t in turns[-5:] if t.get("bot")]
    fresh = [o for o in options if o not in recent]
    if not fresh:
        last = recent[-1] if recent else None
        fresh = [o for o in options if o != last] or list(options)
    if not fresh:
        # Nothing to say: a pool the conversation has emptied is not an answer, so this returns
        # None and the reading that called it stands down. `choice` on an empty list raised
        # IndexError, which took the whole composer with it - every later reading in reply_for
        # never ran, the module proposed nothing, and the turn became the runtime's "Hello!".
        return None
    if seed_text is None:
        seed = len(turns) * 7919 + sum(ord(c) for c in clean)
    else:
        seed = len(turns) * 7919 + _mixed_seed(seed_text)
    return random.Random(seed).choice(fresh)


def _a_birthday_still_to_come(clean, memory):
    """The one birthday this line gave a figure for, from the people the store now holds.

    The store keeps a birthday still to come beside the age the person is ("my mum is 72 and she
    is 73 next month" is 72 now, 73 next month), so the figure and the day are both there to say
    back. Only the entry whose number and day are in this line counts, so an age filed turns ago
    cannot take over a line about somebody else, and only one entry: two birthdays in one line is
    not one thing to name.
    """
    said = " ".join((clean or "").lower().split())
    if not said:
        return None
    met = []
    for one in memory.get("others") or []:
        if not isinstance(one, dict) or one.get("pronoun") or not one.get("who"):
            continue
        age, when = one.get("to_come"), " ".join(str(one.get("turns") or "").lower().split())
        if not isinstance(age, int) or not when:
            continue
        if str(age) not in said or when not in said:
            continue
        met.append(one)
    return met[0] if len(met) == 1 else None


def _the_birthday_said_back(birthday):
    """The pool above with the person, the figure and the day filled in."""
    who = str(birthday.get("who") or "").lower()
    if who and not who.startswith(("your ", "my ")):
        who = "your " + who
    age = str(birthday.get("to_come"))
    when = " ".join(str(birthday.get("turns") or "").split())
    said = []
    for line in A_BIRTHDAY_STILL_TO_COME:
        line = line.replace("{who}", who).replace("{age}", age).replace("{when}", when)
        said.append(line[:1].upper() + line[1:])
    return tuple(said)


# "a 3 year old", "an 8-year-old": the child's day, not the adult's.
_ROUTINE_NOT_SHAPE = re.compile(r"\b\d+\s*-?\s*year\s*-?\s*old\b")
# A named undertaking is a project, not the shape of a day: "a to do list for my wedding",
# "to do list for moving house", "where do i start with my divorce", "get organised for the
# move". Planning a thing
# wants the order of the work on that thing, which a day pool cannot give, so the pools stand
# aside where something that knows the subject can answer. The lines this leaves are ones that
# hedged before, so standing aside costs a gain and never a loss.
_UNDERTAKING = re.compile(r"\b(?:for|with|about)\s+(?:my|our|the|a|an|this|that)?\s*([a-z']+)")


def _somebody_elses_day_in_thread(memory):
    """True when the thread, not the line, belongs to somebody else's day.

    `the baby is 8 months and still not sleeping through` / `weve tried a bedtime routine`: the
    second line names nobody, so the words on the line cannot see the baby, and the method for
    an adult's day ("give it a fixed slot - what are you not getting to?") answers nothing in
    that thread. The line before it is the whole of the test, and it is read for the same words
    the line itself is read for - no module has to have answered it, because a chat line naming
    a puppy is as much a puppy thread as a knowledge line naming one.

    A death is the exception, and it is the reason this is not just a word check: `my dog died
    last night` then `help me get organised` is a person arranging their own day while grieving,
    and a dog that has died has no routine to protect.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-1:]
    for turn in turns:
        said = str(turn.get("user") or "").lower()
        if any(word in said for word in _NO_DAY_OF_THEIR_OWN) or loss.reads_as_loss(said):
            return False
        said_words = set(w.strip(".,!?;:'\"()") for w in said.split())
        if said_words & ROUTINE_NOT or _ROUTINE_NOT_SHAPE.search(said):
            return True
    return False


# The words that put a list of things on the table. A line that says "i dont know where to start"
# is asking about one only where one of these has already been said.
A_LIST_ON_THE_TABLE = re.compile(
    r"\b(?:too much|lots (?:on|of|to)|a lot (?:on|to)|so much|everything|list|lists|jobs|"
    r"things|plates|spinning|juggling|overwhelmed|swamped|drowning|stretched|spread thin|"
    r"deadlines?|behind|catch(?:ing)? up|workload)\b")


def _the_person_named_a_list(memory):
    """Whether the person's own last line or two put a list of things on the table.

    Only their lines: the bot's last reply is not evidence of a list, because the cards that are
    not about lists at all ("ring a crisis line now", "here is one about a parrot") would pass
    for one and the size-of-the-list pool would answer them.
    """
    if not isinstance(memory, dict):
        return False
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-2:]
    return any(A_LIST_ON_THE_TABLE.search(str(turn.get("user") or "").lower()) for turn in turns)


def _routine_pool(clean, words, memory=None):
    """The pool for a line about the shape of the speaker's day, or None if it is not one."""
    words = set(words)
    # A list with too much on it, asked for after the bot has just said to get seen today:
    # "my chest hurts when i run" then "i dont know where to start" was answered "the useful
    # question is what to drop", which ignores the one thing that matters and would fit any
    # message. The advice already given is the whole of today's list, and the rest keeps.
    if memory is not None and stuck_line.the_advice_was_to_get_seen(memory) and (
            any(phrase in clean for phrase in TOO_MUCH_PHRASES)
            or words & {"overwhelmed", "drowning", "swamped"}):
        return stuck_line.URGENT_ALREADY_GIVEN
    # The size of the speaker's own list is theirs whatever the list is made of: "im spread too
    # thin with work and the kids" is a list with kids in it, not a child's routine.
    if any(phrase in clean for phrase in TOO_MUCH_PHRASES if phrase not in _START_ASK):
        return TOO_MUCH
    # "im always late paying my rent" is somebody's money problem and not the shape of the day:
    # the day method would tell them what time to get up. The money pool names a free adviser and
    # asks what matters, which is the most a bot can honestly offer on another person's arrears.
    if _money_decision(clean) and words & BEHIND_ON_MONEY:
        return UNKNOWN_MONEY
    if any(word not in _DAY_WORDS for word in _UNDERTAKING.findall(clean)):
        return None
    if words & ROUTINE_NOT or _ROUTINE_NOT_SHAPE.search(clean):
        return None
    if memory is not None and _somebody_elses_day_in_thread(memory):
        return None
    if any(phrase in clean for phrase in ROUTINE_PHRASES):
        return ROUTINE
    if words & ROUTINE_WORDS:
        return TOO_MUCH if words & {"overwhelmed", "drowning", "swamped"} else ROUTINE
    if any(phrase in clean for phrase in _START_ASK):
        # "i dont know where to start" names nothing on its own: it is the stuck line, and what
        # the size-of-the-list pool has to say depends on whether there is a list. The person's
        # own line before it is the whole of the test - "i have too much on at work" then "i dont
        # know where to start" is a list to shorten, while after a crisis card, an abuse card or
        # a joke the same words got "the useful question is what to drop rather than how to fit
        # it in", which is an answer to a message nobody sent.
        return TOO_MUCH if _the_person_named_a_list(memory) else None
    return None


def _asks_the_bot(understood):
    """True when the line asks the bot for something: an imperative, or an ask for options."""
    if set(understood.get("asks") or ()) & {"recommend", "steps", "options"}:
        return True
    norm = understood.get("norm") or []
    return bool(norm) and norm[0] in IMPERATIVE


def _words(text):
    """The words of a line the way `_mood` wants them: lowercase, no punctuation."""
    return tuple(re.findall(r"[a-z']+", str(text or "").lower()))


def _reads(pred, clean, repaired, lower=False, memory=None):
    """True when a cue reads the typed line or the same line with its words put right.

    "me n my gf r arguin a lot" is the same line as "my girlfriend and i keep arguing a lot",
    and the reading has already repaired it (bot/understanding's `plain`): the cue "arguing" is
    in what the person said even though they typed "arguin". Every pool in this file tests the
    typed line first, so a line that reads with no repair is untouched; the repaired line is
    only ever a second try, never a replacement.
    """
    def ask(text):
        return pred(text.lower() if lower else text, memory) if memory is not None else pred(
            text.lower() if lower else text)
    if ask(clean):
        return True
    if repaired and repaired != clean:
        return bool(ask(repaired))
    return False


ASK_SHAPE = re.compile(r"\b(?:should|could|can|do|does|did|is|are|was|were|will|would|shall|"
                       r"what|when|where|which|who|why|how|any)\b")
# The reading sometimes leaves the frame itself at the front of `focus` ("no i mean is that
# bad"), so it is cut off before the pointed-at words are read: answering the frame again is
# how the recursion came back with the acknowledgement instead of the verdict line.
FRAME_PREFIX = re.compile(
    r"^(?:(?:no|nah|nope|sorry|ok|okay|wait|oops|actually|oh|right|and|but),?\s+)*"
    r"(?:i\s+(?:mean|meant|said)|scratch\s+that|wait\s+no|no\s+wait|i\s+mean\s+to\s+say)\s+",
    re.I)


def _restated(understood):
    """The ask a correction points at ("no i meant <this>" -> "<this>"), or the empty string."""
    if understood.get("intent") != "correction":
        return ""
    focus = " ".join(understood.get("focus") or []).strip()
    focus = FRAME_PREFIX.sub("", focus).strip(" ,.!?")
    if len(focus.split()) < 2:
        return ""
    if all(word.lower() in FRAME_WORDS for word in focus.split()):
        return ""
    # Only an ask is answered again. The pointed-at words of a correction that swaps one named
    # thing for another ("sorry, i meant porto not lisbon", "sorry i meant my brother") are not
    # a question, and the pools below have nothing more to say about them than the line already
    # gets: answering those would put a shrug where an acknowledgement was.
    if not ASK_SHAPE.search(focus.lower()):
        return ""
    return focus


def _answers_the_correction(restated, memory):
    """The pointed-at ask answered from the thread, or None when it has only a punt in it."""
    from . import verdict
    sub = dict(memory)
    sub["compose"] = dict(memory.get("compose") or {})
    sub["understood"] = understand(restated, memory)
    # Never a second hop: a reading of the pointed-at words may itself come back as a correction
    # ("porto not lisbon" carries "not "), and answering that would be the same line again.
    sub["correction_answered"] = True
    # Every pool is filtered, not only this file's own: a verdict path can answer with the
    # search shrug too ("i want to kill myself" / "no i meant how do i tell my wife" lost the
    # drafting offer to "That's beyond what I know well"). The first reply that is not a punt
    # wins, and a punt in one pool never hides a real answer in the next.
    for pool in (verdict.next_step, verdict.reply_for, reply_for):
        reply = pool(restated, sub)
        if reply and not any(punt in reply.lower() for punt in PUNT):
            return reply
    return None


# A thing of the person's own that the line has put a mood word on: "my lawn looks sad", "my
# curtains look miserable", "our boiler is knackered". The possession is what makes the question
# the thing's own - "the weather is miserable" is a moan about the day and its answer is an
# agreement, not a fault to find.
# A thing of the person's can be said with the owner in front of it ("my lawn") or with having it
# ("i have a lawn that looks sad"): both put the thing in the line, and the reading says the state
# is the thing's either way. A body part is not this - "i have a bad back" is the person's own
# state, and the reading says so - and neither is a state the reading leaves on the speaker.
OWN_THING = re.compile(r"\b(?:my|our)\s+[a-z]"
                       r"|\b(?:i|we)\s*(?:'ve|ve|have)\s+(?:got\s+)?(?:a|an|some|two|three|four|"
                       r"a few|another)\b")
# The words that make it a *mood* on a thing rather than a quality of it: "my car looks sad" is a
# thing of the person's gone sorry, while "my pasta is tough" and "my cake is flat" are the food
# being wrong and belong to the cooking answers, not here.
A_MOOD = re.compile(r"\b(?:sad|miserable|unhappy|depressed|lonely|dejected|glum|sorry for itself|"
                    r"in the wars|seen better days)\b")


# A near miss is not a result. The pools below read the result the line names and the "almost"
# in front of it is left to `nearly`, which only says the line is not good news; nothing then
# answers it, and the day pool takes it. What a friend says is that nearly is its own kind of
# hard and asks the one thing worth asking about it. The reading is the achievement only: a
# thing that nearly went wrong ("i nearly broke my arm", "the boiler nearly died") is a fault
# or a fright and belongs to the cards that read it, so those are not here.
NEAR_MISS = re.compile(r"""
    \b(?:almost|nearly|just\s+about)\s+
    (?:
        won\b
      | beat\s+(?:him|her|them|it|everyone|the\s+\w+)
      | broke\s+(?:the|my|a)\s+(?:\w+\s+)?(?:record|pb|best|streak)\b
      | passed\b(?!\s*(?:out|away|on|wind|water|blood|a\s+stool)\b)
      | got\s+(?:the|that|my)\s+(?:job|place|part|role|promotion|record|pb)\b
      | got\s+(?:it|in|through)\b
      | made\s+it\b
      | qualified\b
      | came\s+(?:first|second|third|top)\b
      | scored\b
    )
""", re.I | re.X)
# Written to fit a result of theirs whoever had it: "i almost won", "we nearly won the quiz" and
# "my daughter nearly won her race" are all the same near miss, so none of the four says "you".
NEAR_MISS_REPLY = (
    "So close. Was there a last bit that got away, or was it lost earlier than that?",
    "Almost is its own kind of annoying, being right there. What happened at the end?",
    "Ugh, that is the hardest way to miss something. Will there be another go at it?",
    "That is a hard one to sit with, because nearly is not the same as not good enough. What "
    "would have made the difference?",
)


def _a_near_miss(clean):
    """Whether the line is a result they almost had ("i almost got the job", "i nearly won")."""
    return bool(NEAR_MISS.search(str(clean or "")))


def _a_things_state(memory, clean):
    """Whether the state the line names belongs to a thing of the person's, not to the person.

    "my lawn looks sad" is a report about a lawn; "im sad" is a person's own state, "my mum is sad"
    is somebody else's, and "the weather is grim" is the day rather than a thing that can be seen
    to. The shared reading in memory already says whose the state is (state_owner), so the composer
    asks it rather than re-reading the line.
    """
    understood = (memory or {}).get("understood") or {}
    text = str(clean or "").lower()
    return (understood.get("state_owner") == "thing"
            and bool(OWN_THING.search(text)) and bool(A_MOOD.search(text)))
# The openers a correction is said with ("sorry,", "actually,", "no wait"). Taken from the reader
# that files a corrected fact, so this and that agree on what a correction looks like.
_A_CORRECTION = re.compile(facts.CORRECTION_LEAD, re.I)

# A line that opens by taking something back. The two pools already here cover the withdrawal
# ("never mind", "forget it" - NEVER_MIND) and the apology ("sorry" on its own - SORRY_ON_ITS_OWN),
# but not the correction: "no it was my idea not the kids" after the bot asked which of the party
# games the children had picked, "no the quiet is the best bit of it" after an answer about the
# noise. Both reached the search hedge - "I don't know enough to answer that honestly. A search
# should sort you out quickly" - which tells a person setting the record straight to go and look
# it up, and the party line also reached the kids' games card, because "party" was still in it.
# A correction is a reply to this end of the chat, not a question about the world, so nothing in
# it is a subject to look up. The opener is read strictly: an apologetic "sorry", an "oh" and a
# plain "actually" are how people open all sorts of lines, and only the retracting words count.
TAKING_SOMETHING_BACK = re.compile(
    r"^\s*(?:(?:ok|okay|right|so)\s*[,.]?\s*)?"
    # "no one at work likes me" and "no body tells me anything" open on "no" and are the
    # sentence, so "one" and "body" are not read as the thing being put right.
    r"(?!no\s+(?:one|body)\b)"
    r"(?:no|nope|wait|hold\s+on|hang\s+on|scratch\s+(?:that|it)|forget\s+(?:it|that)|"
    r"my\s+mistake|i\s+(?:got|had)\s+(?:that|it|this)\s+wrong|i\s+made\s+a\s+mistake|"
    r"i'?m\s+wrong|(?:sorry\s*,?\s*)?i\s+(?:mean|meant))\b", re.I)
# What makes the remainder a thing said rather than a noun phrase attached to "no": a verb ("no it
# was my idea"), or the thing itself behind its article ("no the blue one", "no the quiet is the
# best bit of it"). "no onions in it" and "no heating since friday" have neither - they are
# somebody saying what they have not got, which is the sentence and keeps its answer.
SAYS_A_THING = re.compile(
    r"\b(?:is|are|was|were|am|be|been|being|do|does|did|done|have|has|had|can|could|will|would|"
    r"shall|should|must|might|may|its|it's|thats|that's|hes|he's|shes|she's|theyre|they're|"
    r"we're|youre|you're|im|i'm|ive|i've)\b|\w+ed\b", re.I)
THE_THING_ITSELF = re.compile(r"^(?:the|these|those|this|that)\b", re.I)
# What comes after the opener and turns it back into a question: "no what about the other one",
# "no can i do it tomorrow". The ask is the line's, and the pools above answer it.
ASKS_AFTER_THE_OPENER = re.compile(
    r"^\s*(?:what|how|why|when|where|who|which|can|could|should|would|will|do|does|did|is|are|"
    r"was|were|have|has|any)\b", re.I)
# "ok so", "no no", "wait - sorry": an opener stacked on another, which the same line often has.
THE_OPENER = re.compile(r"^\s*(?:(?:ok|okay|right|so|no|nope|wait|ah|oh|sorry)\s*[,.]?\s*)+", re.I)


def _a_chat_to_correct(memory):
    """Whether the bot has said anything this chat for a line to be putting right."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in turns or ():
        if isinstance(turn, dict) and str(turn.get("bot") or "").strip():
            return True
    return False


def _takes_something_back(clean, memory=None):
    """True when the line opens by correcting something and is not then asking a question.

    "no it was my idea not the kids" is the person putting the bot right about who had the idea.
    Three things keep it to that. The chat has to be under way, because a correction is a reply to
    something said here and "no onions in it" as the opening line is somebody telling the bot what
    they are cooking. The line must not go on to ask anything ("no what about the other one"). And
    the rest of it has to say a thing rather than name one: a verb, or the thing behind its own
    article. A correction with nothing on the end of it ("no", "no that's not it") is the
    withdrawal pool's, and "no heating since friday" is the sentence.
    """
    text = " ".join(str(clean or "").split())
    if not text or "?" in text or not TAKING_SOMETHING_BACK.match(text):
        return False
    if not _a_chat_to_correct(memory):
        return False
    body = THE_OPENER.sub("", text, count=1).strip(" ,.;:-")
    if body and TAKING_SOMETHING_BACK.match(body):
        body = THE_OPENER.sub("", TAKING_SOMETHING_BACK.sub("", body, count=1), count=1)
    if len(body.split()) < 2 or ASKS_AFTER_THE_OPENER.match(body):
        return False
    return bool(SAYS_A_THING.search(body) or THE_THING_ITSELF.match(body))


def _a_lateness_report(clean, normalised=""):
    """The speaker's own lateness, stated and not asked about - the one line the pool is for.

    Read off the typed line first, then off the reading's `norm_text` when that found nothing:
    chat-speak is written the way people type it, and the reader has already put it back into
    words (`gona` -> "going to", `bot/understanding/normalize.py`). "im gona be late for work"
    is the same report as "im gonna be late for work", and the pool that read only the typed
    words answered a person rushing out of the door with the neutral nod.
    """
    if "?" in clean or len(clean.split()) > 12:
        return False
    if LATE_ASKS.search(clean) or LATE_NOT_A_TIME.search(clean):
        return False
    if _mood(_words(clean), clean) != "neutral":
        return False
    read = clean
    hit = LATE_NOW.search(read)
    if hit is None and normalised:
        # `norm_text` keeps a clause break as " | ", which no word pattern reaches across.
        read = " ".join(normalised.replace(" | ", " ").split())
        hit = LATE_NOW.search(read)
    if hit is None:
        return False
    between = hit.group(1) or ""
    if LATE_NOT_IT.search(between):
        return False
    # "im behind with my sleep" is a body short of rest, not work left undone, and "what has
    # held you up" is the wrong question for it. `loss.SELF_NOUNS` is the censused list of the
    # words for a part of somebody's own life rather than a thing in the world, so a "behind"
    # that hangs on one of them stands down and the floor answers as it did before. Only "behind":
    # a late-for-work line is about a place and keeps its pool.
    if (hit.group(0) or "").endswith("behind"):
        after = read[hit.end():]
        if any(word in loss.SELF_NOUNS for word in re.findall(r"[a-z']+", after)):
            return False
    return True


# A person the line can hurt: "my son", "our neighbour", "her mum". Never the speaker - "my back
# is killing me" is their own body, with its own answers - and never an animal, because "my dog
# was attacked by a wasp" is the dog's problem and none of these lines is right for it.
HURT_SOMEBODY = re.compile(
    r"\b(?:my|our|his|her|their|the)\s+(?:son|daughter|boy|girl|child|kid|baby|mum|mom|mother|"
    r"dad|father|brother|sister|husband|wife|partner|boyfriend|girlfriend|friend|mate|"
    r"neighbour|neighbor|grandad|granddad|grandma|gran|nan|nana|uncle|aunt|auntie|cousin|"
    r"colleague|flatmate|housemate|carer|teacher|boss|fella|lass|lad|family)\b")
# The end of the news: "my nan slipped in the bath but she's ok", "nothing broken, just bruised".
# The pool asks how somebody is, and the person has already said it.
HURT_BUT_FINE = re.compile(
    r"\bbut\s+(?:he|she|they|hes|shes|theys|it)(?:'s|\s+is|\s+was|\s+seems)?\s*"
    r"(?:ok|okay|alright|fine|good|bruised|home)\b"
    r"|\b(?:he|she|they)(?:'s|\s+is|\s+seems)\s+(?:ok|okay|alright|fine)\b"
    r"|\bnothing\s+(?:broken|serious|bad)\b|\bnot\s+(?:too\s+bad|serious)\b"
    r"|\bonly\s+(?:a\s+)?(?:bruise|scrape|scratch|graze)\b")
# A fall about laughing is not a fall: "my dad collapsed laughing" and "my son fell about" were
# getting "Is your dad alright?".
HURT_FIGURE = re.compile(
    r"\b(?:collapsed|fell|fall|falls)\b[^.!?]{0,12}?\b(?:laughing|about|over\s+laughing|ill|"
    r"sick\s+with\s+laughter)\b"
    r"|\b(?:fell|fallen)\s+(?:out|for|in\s+love|asleep)\b"
    r"|\b(?:knocked|blown)\s+(?:out|away)\b(?!\s+by\s+(?:a|the)\s+\w+\s*(?:car|bus))")


# The person is the one who was hit: "my brother attacked me", "my husband hit me". Asking how
# the brother is doing, when the brother is the one who did it, is the wrong person entirely -
# that belongs to whoever reads abuse, not here.
HURT_ON_THE_SPEAKER = re.compile(
    r"\b(?:attacked|hit|punched|stabbed|kicked|pushed|thrown|strangled|bitten|bit|beat|beaten|"
    r"burned|burnt|hurt|injured|raped)\s+me\b")


HURT_DEATH = re.compile(
    r"\b(?:died|dead|death|dying|passed\s+away|killed|kills?|funeral|buried|suicide|"
    r"took\s+(?:his|her|their)\s+own\s+life)\b")


def _somebody_hurt(clean, memory, understood):
    """The reply to a line that says somebody the person loves has been hurt, or None."""
    if understood.get("asks"):
        return None     # "what do i do if my son gets hurt" is a question about the future
    if _in_a_care_thread(memory):
        return None     # a death or a crisis is already on the table, and that is not this
    found = HURT_SOMEBODY.search(clean)
    if not found:
        return None
    if HURT_DEATH.search(clean):
        return None     # a death is the loss module's, and it says it far better
    if not HURT_EVENT.search(clean):
        return None
    if HURT_ON_THE_SPEAKER.search(clean):
        return None
    if HURT_BUT_FINE.search(clean):
        return None     # "my nan slipped in the bath but she's ok" is the whole of the news
    if HURT_FIGURE.search(clean):
        return None     # "my dad collapsed laughing" is not a fall
    # The words are the person's, so they face the person: "my son" comes back as "your son".
    who = re.sub(r"^(?:my|our)\b", "your", found.group(0))
    return _choose(tuple(line.format(who=who) for line in SOMEBODY_HURT), memory, clean)


# A day of the person's own that was low, rough or long. The floor answered it with the stock nod
# ("Got it. Is there anything you'd like a hand with?", "Thanks for telling me"), which is a line
# that could have come before any message at all: nobody says "i had a low day" to be filed, they
# say it to be met. The chat module has a pool for "i had a bad day" but its words for a feeling
# are read as a mood the person is in, and "a low day" names a thing - a day - so chat's own guard
# (a "low" that names a thing is a dial, not a mood) leaves the line to the floor. The reading here
# is the day, not the adjective: "<a low word> day/week/month" with the person as its owner.
LOW_DAY = re.compile(
    r"\b(?:low|rough|bad|rubbish|crap|hard|tough|awful|terrible|dreadful|long|heavy|rotten|flat)"
    r"\s+(?:old\s+)?(?:day|week|month|morning|afternoon|evening|night|shift)\b")
# The day is the speaker's: "i had a ...", "ive had a ...", "today was a ...", or the bare "low day
# today" a person types when there is nothing else to say about it.
LOW_DAY_MINE = re.compile(
    r"^(?:so |and |but |ok |okay |well |god |ugh |honestly |anyway |yeah |yeh |hmm )*"
    r"(?:i\s+(?:had|have|'ve|ve)\b|ive\b|i\s*'?m\s+having\b|i\s+am\s+having\b"
    r"|we\s+(?:had|have|'ve|ve)\b|weve\b"
    r"|(?:kind\s+of\s+|sort\s+of\s+|bit\s+of\s+|such\s+an?\s+)?a\b"
    r"|(?:today|yesterday|this\s+(?:morning|afternoon|evening|week))\s+(?:was|has\s+been|is)\b"
    r"|really\b|such\s+an?\b|what\s+an?\b"
    # the bare line a person types when the day is the whole of it: "low day today", "bad day at
    # work". It still has to name a day rather than an adjective on its own.
    r"|(?:low|rough|bad|rubbish|crap|hard|tough|awful|terrible|dreadful|long|heavy|rotten|flat)"
    r"\s+(?:old\s+)?(?:day|week|month|morning|afternoon|evening|night|shift)\b)")
# Somebody else's bad day is not the person's, and neither is a thing's: "my mum had a rough week"
# and "the shop had a bad day" are about that person and that shop.
LOW_DAY_NOT_MINE = re.compile(
    r"\b(?:he|she|they|it)\s+(?:had|has|was|is)\b"
    r"|\b(?:my|his|her|their|your)\s+(?!day\b|week\b|month\b|morning\b|night\b|evening\b)\w+"
    r"\s+(?:had|has|was|is)\b"
    r"|\bthe\s+\w+\s+had\b")


def _a_low_day(clean, understood):
    """True when the line says one of the person's own days went badly, and nothing else."""
    if (understood or {}).get("kind") == "question":
        return False
    if LOW_DAY_NOT_MINE.search(clean):
        return False
    # A day that went badly and then a thing that made it so ("i had a low day, my car broke") is
    # the named thing's turn: the pools for bad news already ask about it, and a general question
    # about the day is the weaker reply.
    if "," in clean or " because " in clean or " cos " in clean:
        return False
    return bool(LOW_DAY.search(clean)) and bool(LOW_DAY_MINE.match(clean))


# The people a person might say they love, and the shapes of the whole line. It is anchored at
# both ends because "i love my mums cooking" and "i love my best friend" already have their own
# answers, and "i dont love my mum" / "i love my mum but" are not this line. Two people get a
# plural pool of their own, because "what do you two do together?" is wrong for "mum and dad".
# One person, named or not: family, a partner, and the words people actually use for them.
# `kids`, `family` and `parents` are plural on their own and go to the plural pool; a list of
# names is always one word short, so the group words are here rather than left to be added later.
LOVE_ONE = (r"(?:mum|mom|mam|mother|dad|father|nan|nana|gran|granny|grandma|grandad|grandpa|"
            r"sister|brother|son|daughter|kid|child|wife|husband|partner|girlfriend|boyfriend|"
            r"fiance|fiancee|fiancé|fiancée|stepmum|stepmom|stepdad|stepson|stepdaughter|"
            r"mother[- ]in[- ]law|father[- ]in[- ]law|son[- ]in[- ]law|daughter[- ]in[- ]law)")
LOVE_GROUP = (r"(?:kids|children|family|families|parents|grandparents|grandkids|"
              r"grandchildren|siblings|brothers|sisters|boys|girls|aunts|aunties|uncles|"
              r"cousins|nieces|nephews|stepchildren|stepkids|in[- ]laws|friends|mates)")
LOVE_PERSON = r"(?:" + LOVE_ONE + r"|" + LOVE_GROUP + r")"
LOVE_OPENER = (r"^(?:oh |aw+ |ah |ha+ |lol |tbh |honestly |ok |okay |well |and |but |so )*"
               r"(?:i|we)(?: really| just| absolutely| so| still| do| totally| truly)?"
               r" love (?:my|our) ")
LOVE_TAIL = (r"(?: (?:so much|lots|loads|to bits|to pieces|more than anything|really|tbh|"
             r"honestly|though|tho|too|also))*[.!]*$")
LOVES_SOMEONE = re.compile(LOVE_OPENER + LOVE_ONE + LOVE_TAIL)
LOVES_A_GROUP = re.compile(LOVE_OPENER + LOVE_GROUP + LOVE_TAIL)
LOVES_PEOPLE = re.compile(
    LOVE_OPENER + LOVE_PERSON
    + r"(?: (?:and|&|n) (?:my |our |the )?" + LOVE_PERSON + r")+" + LOVE_TAIL)
# A clause after the person is how people type as they think: "i love my nan she is 88", "i love
# my mum and the kids". The line still starts with the love and names no other thing, so it is the
# same affection; a "but" or "though" is an objection with its own answer and stays out.
LOVE_START = re.compile(LOVE_OPENER + LOVE_PERSON + r"(?:[ ,'-]+[a-z0-9][^?.!]{0,60})?[.!]*$")


def _loves_people(clean):
    """How many of their own people the whole line says they love: 0, 1 or 2 (two or more)."""
    if "?" in (clean or ""):
        return 0
    text = (clean or "").strip()
    if " but " in " " + text + " " or " though " in " " + text + " ":
        return 0
    if LOVES_A_GROUP.match(text) or LOVES_PEOPLE.match(text):
        return 2
    if LOVES_SOMEONE.match(text):
        return 1
    # "i love my mum and dads cooking" is a thing of theirs, not a second person: a possessive
    # after the person is the thing they do or own, and it keeps its own reader.
    if LOVE_START.match(text) and not re.search(
            r"\b(?:mum|mom|dad|nan|gran|sister|brother|kid|child|parent|family)'?s\b"
            r"|\band (?:my|our|his|her|their)\b", text):
        return 1
    return 0


def _loves_someone(clean):
    """True when the whole line is the person saying they love someone of their own."""
    return bool(_loves_people(clean))
# A line that puts a clock time on being somewhere is a morning to plan, not a goal the person is
# failing at: "i need to be at work for 8" was answered "Be at work for 8 - fair enough. What's
# stopped it happening so far?", which is a coach's line about something somebody has been
# avoiding, and it drops the only part of the answer that helps - when to leave and how long the
# journey is (tiny-bluebell, #routing 81689). "Noted: you have a train at 7." and "I'm listening -
# say more if it helps." are the same fault from the other end: a deadline is the one thing in the
# line that can be worked back from, the way the airport entry already answers "what time should i
# leave for the airport" with "be there by 4am - work back from that".
A_CLOCK = (
    r"(?:\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm)|"
    r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(?:am|pm)|"
    r"(?:\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*o'?clock|"
    r"half\s+(?:one|two|three|four|five|six|seven|eight|nine|ten))")
# The clock time itself, with the little word it hangs off. A bare number needs one ("for 8"), and
# "8am" does not.
A_TIME_SAID = re.compile(
    # The minutes come first, so a time given to the minute is quoted as it was said: "7.45"
    # matched the bare \d{1,2} arm of A_CLOCK on its own and the reply worked back from "7",
    # which is not what the person has to be there by (grand-gopher on #7924).
    r"\b(?:at|by|for|before|around|about|until|till|from)\s+"
    r"(\d{1,2}[:.]\d{2}\s*(?:am|pm)?|" + A_CLOCK + r"|\d{1,2}|"
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b",
    re.I)
# A time in front of the thing that leaves - "i have to catch the 7.15 train", "the 6am flight
# goes from terminal two" - has no little word in front of it, so A_TIME_SAID misses it. It is
# the same morning as the other shapes and worth the same answer.
CLOCK_THE_DEPARTURE = re.compile(
    r"\bthe\s+(\d{1,2}[:.]\d{2}\s*(?:am|pm)?|\d{1,2}\s*(?:am|pm)|half\s+past\s+"
    r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve))\s+"
    r"(?:train|flight|bus|coach|ferry|boat|tram|tube|plane)\b", re.I)
# The shapes that make a clock time a deadline: somebody has to be somewhere, a train leaves, a
# shift starts, an alarm goes off. A clock time on its own is not enough - "i have 8 eggs" and
# "i watched it for 8 hours" are about a number, not a morning.
CLOCK_SHAPE = re.compile(
    r"\b(?:need|needs|needed|have|has|had|got|must|ought)\s+(?:to\s+)?"
    r"(?:be|get|leave|head|go|catch|make)\b"
    # A journey or a shift that has a time on it. An interview, an exam and a match are left out
    # on purpose: those are occasions the bot already answers as occasions ("Good luck with it"),
    # and "my interview is at 3pm" is a fact to keep rather than a morning to plan.
    r"|\b(?:train|flight|bus|coach|ferry|boat|taxi|shift|meeting|work|check-?in)\s+"
    r"(?:is|are|starts?|leaves?|departs?|takes?\s+off|begins?|kicks?\s+off)?\b"
    r"|\b(?:be|get|wake)\s+up\b|\bset\s+(?:the|my|an)\s+alarm\b")
# A length hanging off the same little word is not a clock: "for 8 hours", "for 6 months",
# "for 8 people" are quantities, and "i was at work for 8 hours" is the day that has happened.
A_LENGTH = re.compile(
    r"^\s*(?:hours?|hrs?|minutes?|mins?|days?|weeks?|months?|years?|miles?|km|kms|"
    r"people|quid|pounds|kilos?|kg|st[o]?ne|times|of\s+them|more|less)\b")
# Over, or somebody else's, or a question: the four shapes that are not a morning of theirs.
CLOCK_NOT_THIS = re.compile(
    r"\b(?:was|were|been|missed|lost|yesterday|last\s+night|this\s+morning|cancelled|"
    r"canceled|used\s+to|usually|always|every\s+day)\b")
CLOCK_ASKED = re.compile(
    r"^\s*(?:what|when|how|which|why|who|should|shall|can|could|would|do|does|did|is|are|"
    r"was|were|have|has|any|is\s+it)\b")
# Somebody else's morning is answered where that person is answered: "my mum has to be at the
# hospital for 9" is the worry about her, not a journey to plan.
# A line that describes the job is about the job, not about this morning: "im a bus driver and i
# start at five in the morning" is context for the early shifts, and the sleep answer is the one
# that helps, so the clock time in it is not a deadline to work back from.
CLOCK_ABOUT_THE_JOB = re.compile(
    r"\b(?:im|i'm|i am)\s+an?\b|\bi\s+work\s+as\b|\bmy\s+job\b|\bmy\s+shift\s+pattern\b")
CLOCK_SOMEONE_ELSE = re.compile(
    r"\b(?:my|our|his|her|their)\s+(?:mum|mom|mam|mother|dad|father|wife|husband|partner|"
    r"boyfriend|girlfriend|son|daughter|child|kid|brother|sister|nan|nana|gran|granny|"
    r"grandma|grandad|grandpa|aunt|uncle|cousin|niece|nephew|friend|mate|neighbour|neighbor|"
    r"colleague|boss)\b")
# The reply works back from the time: what the journey is, what has to happen before they go, and
# the leaving time rather than the arriving one.
AT_THE_CLOCK = (
    "Work it back from {at}: the journey, then getting ready, then ten minutes spare. What is "
    "the trip like at that hour?",
    "{At} gives you a time to work back from. How long does the journey take from yours?",
    "Count backwards from {at} and set the alarm by the time you have to walk out. What has to "
    "happen before you get out of the door?",
    "The leaving time is the thing to fix for {at}, not the arriving one. How long does it take "
    "from yours?",
    "{At} is a timetable rather than a rush, as long as the leaving time is right. Where are you "
    "travelling from?",
)


def _the_clock_pool(at):
    """The pool with the time worked into the lines, so the reply names it back."""
    at = (at or "").strip()
    if not at:
        return AT_THE_CLOCK
    return tuple(line.format(at=at, At=at[:1].upper() + at[1:]) for line in AT_THE_CLOCK)


def _the_time_said(clean):
    """The clock time in the line, as the person said it, with its match.

    A time said with the little word in front of it ("by 7.45", "for 6am") and a time said in
    front of the thing that leaves ("catch the 7.15 train") are the same morning, and both have
    to be quoted back the way they were given, minutes and all.
    """
    return A_TIME_SAID.search(clean) or CLOCK_THE_DEPARTURE.search(clean)

def _the_morning_has_a_clock(clean):
    """True when the line puts a clock time on somebody having to be somewhere."""
    if "?" in clean or CLOCK_ASKED.match(clean):
        return False
    if CLOCK_NOT_THIS.search(clean) or CLOCK_SOMEONE_ELSE.search(clean):
        return False
    if CLOCK_ABOUT_THE_JOB.search(clean):
        return False
    said = _the_time_said(clean)
    if not said:
        return False
    if A_LENGTH.match(clean[said.end():]):
        return False
    return bool(CLOCK_SHAPE.search(clean) or said.re is CLOCK_THE_DEPARTURE)


def reply_for(text, memory, verdict=True):
    """One short reply that fits the kind of line, never repeating the last few.

    `verdict=False` is for a caller asking what the composer would say about a line *as a thing*
    rather than as this turn: the memory store asks it that way (`bot/memory/cause.py`,
    `_the_bot_would_only_shrug`) to find out whether the words on their own already have an
    answer, and the verdict pool is the answer to the turn, not to the words. Left in, "im so
    tired" then "thats annoying" made the store think the composer had answered and stand down,
    and the pool's line then lost the turn to chat's - the store's own line about that tiredness
    is the better answer and the one it gave on main (gray-cypress on #5479).
    """
    # A line that names a person of theirs and nothing else is a person to ask about however it is
    # worded, and "what about the little one" is the same line as "and the little one". As a
    # question it reached the search hedge ("I'm not sure about that one, sorry"), which is the
    # wrong answer to a person a friend was just told about. The pattern is anchored to the whole
    # line, so a real question about a person ("what about my sons school") never gets here.
    if verdict and isinstance(memory, dict):
        alone = (ack.a_person_named_alone(_matchable(text), memory)
                 or ack.a_person_pointed_at(_matchable(text), memory))
        if alone:
            return alone
    said = _reply_for(text, memory, verdict=verdict)
    if verdict and said and is_a_hedge(said):
        # "I'd rather not guess. A quick search online will get you a solid answer" is the last
        # thing the bot can say, and a verdict on the plan already on the table is never worse than
        # it. "i want to grow a beard" was answered "Grow a beard — fair enough. What's stopped it
        # happening so far?", and the follow-up "is that daft" got the hedge: the stand-down in
        # `_the_reply_above_judged` keeps the verdict off the bot's own question, which is right
        # while something else can answer the turn and wrong when the hedge is the alternative.
        clean = _matchable(text)
        pool = _a_verdict_on_their_plan(clean, memory, past_a_question=True)
        if pool:
            return _choose(pool, memory, clean)
    if verdict and said:
        # Nothing has been said in this chat yet, and every pool here is written for a conversation
        # in progress, so the line that fits this turn can be about a life the person has not
        # described: "sorry, i got cut off" as the first thing in a chat was answered "Good to
        # hear. What was the best bit?", "back to what we were saying" by "Nice one. How did the
        # rest of it go?", and "carry on" by "Thanks for telling me - I'm here if you want to dig
        # into any of that." The pools are right a turn later, so the reading is not wrong - what
        # is wrong is answering a turn that has not happened. The question is asked in one place
        # (`bot/memory/already.py::nothing_said_yet`), and this is the composer's own answer to it:
        # a line that names no earlier turn, because there is none to name. It takes both facts -
        # this is a chat's first line, and the line brings nothing of its own - because a first
        # line that does bring something ("weve booked a week in cornwall in august") is well met
        # by a pool written for a chat in progress: "Nice one. Is it soon, or have you got a while
        # yet?" The fault is only where there is nothing to react to.
        from . import fallback as composer
        if (composer.nothing_said_yet(memory)
                and composer.brings_nothing_of_its_own(text)
                and composer.assumes_an_earlier_turn(said)):
            return _choose(composer.NOTHING_SAID_YET, memory, _matchable(text))
    return said


# The alternatives can already be on the table when the person hands the choice back: a dinner
# the bot listed two lines up, or a choice the person named themselves ("i could go to the gym or
# go for a swim" / "you pick"). Where memory's `prefer` can pick it never gets this far, so asking
# "what are they?" here is asking for what was just said - a friend picks, or says what it turns
# on. The pool stands down and the ordinary answer for the line takes the turn, which is what the
# person got before this pool existed. Found by brown-pomelo, merry-wheel and violet-pine on the
# review of #7538, each on their own comparison.
OPTION_ON_THE_TABLE = re.compile(r"\b(?:or|either)\b")

def _options_already_up(memory):
    """True when the things to choose between were named in the last turn or two."""
    if not isinstance(memory, dict):
        return False
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-2:]
    for turn in turns:
        said = str(turn.get("bot") or "")
        asked = str(turn.get("user") or "")
        if len(OPTION_ON_THE_TABLE.findall(said.lower())) or " or " in asked.lower():
            return True
    return False



def _reads_value(pred, clean, repaired, memory=None):
    """The pool a cue picks out of the typed line, or out of the same line with its words put
    right, or None.

    `_reads` is the same idea for a cue that only says yes or no. The pools that pick a reply out
    of a line need the pool itself back, and they were handed the typed line alone: "im ment to be
    goin to a weddin nxt week" was answered "I'm listening - say more if it helps" while the same
    line spelled properly got "Something to look forward to, then", because "next week" is a
    spelling the reading puts right and the pool never saw the mended line. As in `_reads`, the
    typed line is asked first, so a line that needs no repair is untouched.
    """
    found = pred(clean) if memory is None else pred(clean, memory)
    if found or not repaired or repaired == clean:
        return found
    return pred(repaired) if memory is None else pred(repaired, memory)

# A countdown is the one sum that still belongs in a care thread. "i dont want to live in
# december" then "how long till december" is somebody asking how long they have to hold on, and
# the arithmetic card stands down there on purpose (maths.solve asks in_a_safety_thread first,
# because a figure said out loud mid-emergency is the person still in it and not a sum to work
# out). What was left was the search hedge - "searching for it will turn up better sources than I
# can offer" - which is the worst thing this bot can say to that question. The date is worked out
# with the crisis taken out of the way, and the line keeps the person company while it says it.
COUNTDOWN_ASK = re.compile(
    r"(?<![a-z])(?:how long|how many (?:days|weeks|months|sleeps|more days)|how much longer|"
    r"how far away)(?![a-z])")
COUNTDOWN_TO = re.compile(r"(?<![a-z])(?:till|til|until|before|away|to go)(?![a-z])")
COUNTDOWN_AFTER_CARE = (
    "{count} That is a while to be counting towards, and you don't have to get through it on "
    "your own - what is tonight like?",
    "{count} If there is something about that date you are counting towards, say what it is and "
    "we'll take it a day at a time.",
    "{count} A long stretch of days is hard to carry on your own. Who knows how you are doing "
    "tonight?",
)


# The shape a count starts with. A sentence from `solve` that refuses the sum ("I can't see a
# calendar from here, so tell me the date") has numbers later in it, so where the figure sits
# decides it rather than whether there is one at all.
COUNTED = re.compile(
    r"^(?:that's |that is |it's |its )?(?:about |around |just |nearly |only |almost |another )?"
    r"(?:\d|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|"
    r"fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|a hundred)")


def _a_countdown_in_a_care_thread(memory, clean, repaired, understood):
    """The date, said plainly, in a thread where the last real answer was an emergency."""
    from ..memory.topics import in_a_safety_thread  # noqa: PLC0415 - shared reading of memory
    if not in_a_safety_thread(memory):
        return None
    said = " ".join(str(repaired or clean or "").lower().split())
    if not COUNTDOWN_ASK.search(said) or not COUNTDOWN_TO.search(said):
        return None
    from ..knowledge.maths import solve  # noqa: PLC0415 - only this branch needs the sums
    # The reading in memory was made for the previous turn, and that turn was the crisis: "i dont
    # want to live in december" has no countdown in it, so a reading of it finds none here. The
    # line itself is what is being counted to.
    reading = {"clean": said, "words": said.split(), "kind": "question"}
    # An empty memory, because the countdown is not the arithmetic the safety thread holds back:
    # this is the one sum the line is asking for.
    count = solve(said, reading, {})
    if not isinstance(count, str) or not count.strip():
        return None
    # `solve` answers a sum it will not do with a sentence of its own ("I can't see your payday
    # from here, so tell me the date it lands on"), and that is not a count. A figure at the front
    # is what makes it one, so anything else is left to the answer it already had.
    if not COUNTED.match(count.strip().lower()):
        return None
    count = count.strip().rstrip(".") + "."
    return _choose(tuple(line.format(count=count) for line in COUNTDOWN_AFTER_CARE),
                   memory, clean)


def _reply_for(text, memory, understood=None, verdict=True):
    """The composer's reply to this turn (`reply_for`), with the reading already made."""
    if understood is None:
        understood = memory.get("understood")
    if not isinstance(understood, dict):
        understood = understand(text, memory)
    state = memory.setdefault("compose", {})
    was_taste = bool(state.get("taste"))
    state["taste"] = False
    kind = understood.get("kind") or "statement"
    words = understood.get("words") or []
    clean = understood.get("clean") or " ".join(text.lower().split())
    # A countdown asked inside a care thread reaches this file's own care continuation first, and
    # that continuation answers any second line with "I'm glad you're talking about it" - which is
    # right for most of them and wrong for "how long till december", where the person is asking how
    # long they have to hold on. The date is the one thing this turn wants said, so it is read here.
    counted = _a_countdown_in_a_care_thread(memory, clean, text, understood)
    if counted:
        return counted
    after = _after_safety(memory, clean, understood)
    if after:
        return after
    # The ask one turn after the condolence: "how do i tell a 4 year old". The child's words are
    # the whole answer, and the readings below take this line first: the hedge sends a bereaved
    # parent to a search engine, the drafter asks them to write the words themselves, and the
    # topic entries answer "a 4 year old" with the screen-time card. Narrow on purpose - the ask
    # shape, a child, and a death in the thread (see bot/compose/childwords.py). The line itself,
    # not `clean`: the reading in memory was made for the previous turn.
    from . import childwords
    if childwords.asks_the_words_for_a_child(text or clean, memory):
        return _choose(childwords.THE_WORDS_FOR_A_CHILD, memory, clean)
    # A talk asked for at a time: "can we talk tonight", "can we chat later", "can you keep me
    # company". There is no diary and no clock here, and the search hedge sent a person who wanted
    # a conversation to a page about nothing. Asked here, before the hedge and before the pools
    # that answer a thing, because the time is all the line holds - a line that names what the talk
    # is about ("can we talk about my boiler") is that thing's answer and the reader stands down.
    from . import talktime
    at_a_time = talktime.answer_for(clean, memory)
    if at_a_time:
        return at_a_time

    # A night of drinking, said the day after. Six pools deeper in this chain were answering it:
    # "i was blind drunk last night" and "i got pissed last night" got the day pools' "Good to
    # hear. What was the best bit?", "i got wasted at the party" the echo, "i was bladdered at the
    # do" the skills line, "im hanging this morning" the task line, and "i was plastered last
    # night" the sober-years pool, which read "plastered" as time off the drink. A cheer at a
    # night a person is not proud of is the reply they cannot use, so the reading is one place and
    # it is here, before all six. A knowledge card still takes the turn, because the composer is
    # last: "i have such a hangover" keeps the water, sleep and food card.
    if morning_after.reads_as_a_morning_after(clean):
        return _choose(morning_after.A_MORNING_AFTER, memory, clean)

    # Somebody the person loves has been hurt and no card covers it. "my son was in an accident"
    # was filed back to them ("Noted: your son was in an accident"), and "my brother got hit by a
    # car" got "Got it. Is there anything you'd like a hand with?" - a line that could have come
    # before any message at all. The person is not handing the bot a fact to keep, they are saying
    # the worst thing in their week, so the reply asks about them.
    hurt = _somebody_hurt(clean, memory, understood)
    if hurt:
        return hurt
    # A safety question about a thing of theirs ("is it safe to keep it on tonight" about the
    # boiler the line before) reached the repeat frame and the search shrug. It is one question
    # with one answer, and it is read here, above the topic pools and below every card that
    # names the thing (bot/compose/safetyask.py, and the size note in `_reply_for`).
    if not _a_care_thread_to_leave_alone(memory):
        safety_ask = safetyask.reply_for(clean, memory)
        if safety_ask:
            return _choose(safety_ask, memory, clean)
    # The person hands the choice straight back and there is nothing on the screen to pick from
    # (see HANDS_BACK). Read here, before the topic pools, because there is no topic: the line is
    # all the person said.
    if HANDS_IT_BACK.match(clean) and not _options_already_up(memory):
        return _choose(HANDS_BACK, memory, clean)
    # A line that only points back at the conversation - "as i was saying", "where was i", "sorry,
    # i got cut off", "so anyway" - names nothing, so the account-of-the-day pool answered it as
    # though it were news ("Sounds alright. Anything good in it?") and the search hedge took
    # "where was i". The person is picking the thread back up, which is the whole content of the
    # line, so it is read here, before the pools that answer a line's subject. The thing named
    # after the phrase ("as i was saying about the car") is asked about, because the person has
    # not said it yet - and neither pool names a turn, so both work as a chat's first reply.
    returned = reads_as_a_return(clean)
    if returned is not None and not _came_back(clean) and not _grief_thread(memory):
        if returned:
            return _choose(RETURNED_TO_A_THING, memory, clean).format(thing=returned)
        if not _a_chat_behind_it(memory):
            return _choose(RETURNED_TO_IT_FIRST, memory, clean)
        return _choose(RETURNED_TO_IT, memory, clean)
    # The bot's own last turn offered to write the message ("tell me who it's for and what you
    # want them to do"), and this line is that detail. Read here, before the topic pools, because
    # the reason inside the message is not a new topic: "saying i cant make saturday cos im
    # skint" was reaching the money pool and the note the bot asked for never arrived. An
    # emergency, a loss or a bleed still wins - a draft of chest pains is not a message.
    drafted = _named_draft(memory, text, words, clean)
    if drafted:
        return drafted
    # An idiom of agreement is the person saying "quite", not asking to be told about anything:
    # "tell me about it" was reaching the search hedge. The reading found the idiom, the pool
    # only phrases it, and it is asked before the flat branch because "you and me both" is flat
    # enough to be read as a shrug at the weather.
    if understood.get("agreement"):
        return _choose(AGREEMENT, memory, clean)
    # A line that says the money has run out is a tight week, not a money question: the reading
    # only says so when nothing is being asked, so "what can i cook till payday" is untouched.
    if understood.get("tight_on_money"):
        # A line that already says what is left ("i have 20 quid till friday") has answered the
        # question the last pool line asks, and asking it back is the bot not listening. The
        # lines that name the week rather than ask about it are the ones left.
        pool = TIGHT_MONEY
        if understood.get("amount_left"):
            pool = tuple(line for line in pool if "what's left" not in line.lower())
        return _choose(pool, memory, clean)
    # The turn after that one, when the person asks the bot to go on instead of answering the
    # question the pool asked: the same week, said again as the ask it needs.
    if a_continuation_of_the_tight_week(memory, clean):
        return _choose(TIGHT_MONEY_MORE, memory, clean)
    # A day of the person's own that went badly is not a fact to file and not a request: the floor
    # answered "i had a low day" with "Thanks for telling me" and "low day today" with "Noted: low
    # day today", which hands the person their own sentence back. Read before the ack and the
    # reaction pools, because the day is the whole of what they said.
    if _a_low_day(clean, understood):
        return _choose(LOW_DAY_REPLIES, memory, clean, seed_text=text)
    # The hand-back ("what about you", "and you", "yourself") is the person passing the
    # question over, and the manners pool is the reply: left to the follow-up readers it is read
    # as a question about the thing on the table, and after the egg answer "what about you" got
    # the egg answer again. It is asked here, before the advice and reaction pools, because it
    # names nothing of its own and there is nothing for them to answer. An opening hand-back has
    # nothing behind it to pass over, so that one is left to the chat module's warmer line.
    if HAND_BACK.match(_self_line(text)) and (memory or {}).get("turns"):
        # Seeded on the line itself so two chats with the same shape do not get the same
        # sentence: the letter sum `_choose` uses by default collides on lines of the same
        # length, which put one wording on most of the hand-backs (sure-umbrella on #6004).
        return _choose(HOW_ARE_YOU, memory, clean, seed_text=text)
    # A report on the advice in the last answer ("i tried that and it helped a bit", "its not
    # helping") is answered with the outcome, not with the stock nod or the flat "could be
    # worse" ack. It sits before that ack and after the safety continuation, and it only fires
    # on a line that is nothing but the report, so it can never take a turn from a subject of
    # the person's own.
    verdict = _verdict_pool(clean, memory) if verdict else None
    if verdict and in_a_safety_thread(memory):
        # A live emergency is not a verdict turn at all: the bot's own continuation of it is.
        verdict = None
    elif verdict and a_happening_now(memory):
        # It is happening as they type: a miscarriage now, a death in the house. Sympathy and a
        # question about how they are today is the wrong turn to take - the careful continuation
        # already there is not to be talked over.
        verdict = None
    elif verdict and a_loss_in_the_thread(memory):
        # A verdict on a death, a diagnosis or a baby lost is a heavier turn, and the light pools
        # ask a fix question that fits a laptop and not a bereavement. Standing the pool down once
        # left the floor under it ("Got it. Is there anything you'd like a hand with?" after "my
        # nan died in march" then "thats a shame"), so the heavier pool takes the turn instead.
        # The answer a module already gave about the loss keeps the turn before this is asked
        # (`bot/modules/arbiter.py`, `_the_verdict_back`), and the composer only fills the floor.
        # The pool is the weight of the news: a death, a queue, a job gone and a hard week are
        # not the same line (`_the_heavy_pool`).
        verdict = _the_heavy_pool(memory)
    # A verdict is not a report on the advice in the last answer: "what a headache" after the
    # tenant line read as "it did not help" and got a second tenant card, and "its a mess" after
    # the oven answer read as asking for the rest of it. Nothing is being reported and nothing
    # more is being asked for, so the report branch stands aside for the verdict.
    tried_reply = None if verdict else _after_advice(memory, clean, words)
    if tried_reply:
        return tried_reply
    # A fifth outcome of that advice, and the one that is not about the person's own try: they did
    # what the answer said and were turned down. "my boss said no" was filed back as "Got it -
    # your boss said no", so the no is answered here rather than by the ack.
    refused = _a_refusal_to_answer(clean, memory, words)
    if refused:
        return _choose(refused, memory, clean, seed_text=the_advice(memory) or clean)
    # The line before the try: they have read the answer and it sounds doable. It sits with the
    # report on the advice for the same reason - both are about the answer and not about a subject
    # of the person's own - and after it, because "i tried that, it was doable" is a report.
    doable = _a_doable(clean, memory)
    if doable:
        return doable
    if verdict:
        # Before the flat pool, the hedge and the taste question: a verdict is the whole line,
        # and "what a hassle" was reaching the search shrug as if it had asked something.
        return _choose(verdict, memory, clean)
    # The same reading, for the reactions another pool would take first: "seriously?" and
    # "no way" after an explanation were answered "Really? Tell me what happened", which asks for
    # news when the person is reacting to the answer they just got. bot/compose/reaction.py says
    # nothing unless the line above was an answer, so a reaction to news keeps this pool.
    answered = answer_reaction.reply_for(clean, memory) if isinstance(memory, dict) else None
    if answered:
        return answered
    reaction = _reaction_pool(clean, memory)
    if reaction is REACTION_REPEAT:
        # "what?" and "huh" are read as the repeat, and the answer above is the one thing that can
        # be said again in fewer words: the answer's own opening clause beats "which bit was
        # unclear?" because it hands something back. Where there is nothing to cut the reading says
        # so itself and asks which part (bot/compose/why.py, `said_again`).
        again = why.said_again(clean, memory) if isinstance(memory, dict) else None
        if again:
            return again
    if reaction and not _a_care_thread_to_leave_alone(memory):
        if _the_person_already_said_it(memory):
            reaction = REACTIONS_SAID.get(reaction, reaction)
        # Before the flat pool and the hedge: a reaction is answered in kind, and it is the same
        # kind of line the flat pool answers, so it has to come first for "ugh" and the rest.
        return _choose(reaction, memory, clean)
    if reaction and _a_care_thread_to_leave_alone(memory) and reaction is not REACTION_REPEAT:
        # A death, a loss or a crisis: the reaction above stands down so the thread stays with the
        # person, and this is what answers instead of the flat pool's shrug.
        return _choose(REACTIONS_CARE, memory, clean)
    # A remark about the day ("bit nippy", "pouring down", "the suns out") is answered with the
    # day, not with the stock nod. It is read after the pools that need the turn before to read it
    # (a verdict, a reaction, a report on the advice), because "lovely day" the turn after good
    # news is about the news and not about the weather, and it stands down in a care thread, a
    # heavy week or an emergency, where the day is not what the person is talking about.
    the_day = _the_day_described(clean)
    if the_day and not in_a_safety_thread(memory) \
            and not _a_care_thread_to_leave_alone(memory) \
            and not _the_turn_before_was_a_heavy_one(memory, clean):
        return _choose(the_day, memory, clean)
    if words and len(words) <= 6 and FLAT_LINE.match(" ".join(words)):
        # Before the hedge, the taste question and the nod: "could be worse" was reaching the
        # search shrug as if it asked something, "same old" carried "same" into the cheery ack,
        # and a bare "ugh" got "I'm listening - say more if it helps" as if nothing was said.
        return _choose(FLAT, memory, clean)

    # A view asked for with nothing named ("whats your honest view?", "honest view?", "your take",
    # "honest answer"): the person is asking the bot to stand behind the answer just given, and a
    # search suggestion there is the bot denying its own paragraph. It is read before every pool
    # that answers a *subject*, because the line names none: "honest answer" one turn after a
    # phone-battery answer was reaching the routine pool's phone habit line ("take the choice out
    # of the moment rather than counting on willpower"), which answers a question the person did
    # not ask. It is also before the taste pools, because "your take" and "what do you reckon"
    # are in both families, and the general taste line ("No strong view on that one, honestly.
    # What's yours?") is the shrug for a question with no answer behind it - said one turn after
    # a full answer, it is a lie.
    view = _the_view_asked_for(clean, memory)
    if view:
        return view
    no_words = _no_words(clean)
    if no_words:
        return _choose(no_words, memory, clean)

    if kind == "thanks" and "?" in text:
        kind = "question"
    # ... but a greeting in front of something to answer is not a hello: "hi, my boiler is
    # leaking" and "hello my cat keeps being sick" want those lines answered, and
    # "hi there - what can I help with?" answers nothing. So the greeting is only claimed when
    # the line is a hello on its own (the same test the reading uses) or when what follows is
    # someone saying what they want ("hi i need help writing a cv"): a hello and an offer is a
    # better reply to that than a neutral "got it", which is all the rest of this file can say.
    # A line that reports something keeps the kind it was given, so the news and trouble
    # replies below still get their turn.
    # "hi, can you help me" is the ask with a hello in front of it. The hello adds nothing to
    # answer and the greeting pool would offer nothing back, so the ask keeps the turn.
    asks_for_help = _asks_for_help(_plain(clean), understood)
    opens_with_hello = kind == "statement" and _reads_as_greeting(words, text) \
        and not _reads_as_question(text, words)
    if opens_with_hello and not asks_for_help \
            and (greeting_only(words) or understood.get("intent") == "request"):
        kind = "greeting"
    if kind == "empty":
        return _choose(EMPTY, memory, clean)
    if kind == "greeting" and not asks_for_help:
        return _choose(GREETING, memory, clean)
    if kind == "thanks":
        # A thank-you with bad news behind it is that news: the kind reader takes the whole line
        # for manners, so this asks first or every "thanks, its still stinging" is thanked back
        # and the thing that has not come right goes unanswered.
        if _thanks_news_went_badly(clean):
            return _choose(THANKS_NO_BETTER, memory, clean)
        # A thank-you with a goodbye on the end is a goodbye: "thanks, i need to go, the kids are
        # up" was answered "Happy to help.", which answers the half that was not the point. The
        # pool is the composer's goodbye, so the wording and the reading stay in one place.
        bye = leaving.pool(clean, words, memory=memory)
        if bye:
            return _choose(bye, memory, clean)
        return _choose(THANKS, memory, clean)
    # A person they love, said plainly: filed back by the store as "Noted: you love your mum."
    # It sits before the hand-off, the repairs and the echo, and after the greeting and thanks
    # branches, which are the lines it cannot be.
    loved = _loves_people(clean)
    if kind != "question" and loved:
        return _choose(A_LOVE_FOR_PEOPLE if loved > 1 else A_LOVE_FOR_SOMEONE,
                       memory, clean)

    # A hand-off ("one more thing", "quick one") has said nothing yet, so there is nothing to
    # answer and nothing to search for: the knowledge base matched the words "one" and "thing"
    # and answered a study question. It sits before the search and the taste branches, which are
    # the ones that would otherwise claim it, and after the safety, thanks and hello branches,
    # which are the lines it cannot be.
    going_on = handoff.reply_for(clean, memory)
    if going_on:
        return going_on

    # The line takes the last answer back and asks again. The pointed-at words are the turn.
    restated = "" if memory.get("correction_answered") else _restated(understood)
    if restated:
        reply = _answers_the_correction(restated, memory)
        if reply:
            return reply

    # A line that only puts a new value where the old one was ("make it four", "make that 10k")
    # is not asking the bot for options, and the store can only correct a value it holds: a habit
    # they described is not one, so these lines were reaching the search hedge from the asks-the-bot
    # branch below ("That's beyond what I know well, sorry"), which answers a correction as if the
    # person had asked a question. The value goes back up with the unit of the line it corrects.
    corrected = ack.value_put_right(clean, memory)
    if corrected:
        return corrected
    wondered = ack._a_condition_they_wonder_about(clean, memory)
    if wondered:
        # "i think i have diabetes" is a question about diabetes, and nothing else answers it:
        # said back as a fact it was "Noted: you think you have diabetes", which is no answer.
        return wondered
    plain = _plain(clean)
    # The same line with its wrong words put right ("me knee is killing me" -> "my knee is
    # killing me"), from the reading. Only ever a second reading: every pool below test the
    # typed line first and consult this one only when nothing matched.
    repaired = understood.get("plain") or clean
    if _is_presence_check(clean):
        # "can you hear me" with nothing else in it is a presence check: a search shrug is
        # the wrong answer, so say something present and leave the floor open.
        return _choose(PRESENT, memory, clean)

    # A plan the person has had to drop ("i cant come", "sorry i cant make it", "gonna have to
    # cancel") is answered as the plan it is, before the trouble question and the stock nod: see
    # `DECLINED_PLAN`. Nothing else in this file reads these lines.
    if _a_declined_plan(plain) and not draft.drafter(memory, clean):
        # Not while the bot has an offer open to write the message: "can you help me write a text
        # to my boss" then "i need to tell her i cant come" is the message, and it was getting
        # this pool instead of the draft ("No trouble at all - these things happen" in place of
        # the note to send). The draft below answers it.
        if _a_hard_week(memory):
            # "my mum is dying" then "i cant come": the plan is dropped in the worst week of
            # their life, so the answer stays in that register instead of being jolly about it.
            return _choose(DECLINED_PLAN_GENTLE, memory, clean)
        if _the_turn_before_was_a_heavy_one(memory, plain):
            # "i had a panic attack" then "i cant come", "im depressed" then "i cant make it":
            # the plan is what the feeling cost them, not a diary clash. The line is left to the
            # readers that answer a feeling, so the panic card and the warm frame keep the turn
            # instead of asking somebody who is struggling whether they want to rearrange it.
            pass
        elif _someone_else_dropped_it(plain):
            # The plumber, the sitter, a friend: nothing to explain and nobody expecting them.
            return _choose(PLAN_KNOCKED, memory, clean)
        else:
            return _choose(DECLINED_PLAN, memory, clean)

    help_topic = _help_topic(clean, understood)
    if help_topic:
        return _choose(help_topic, memory, clean)

    # "Which would you pick?" asks for the bot's own taste, but the thing to pick from is
    # already on the table, so it is answered before the identity pool: "what would you get"
    # was reading as a question about the bot itself ("I'm a chatbot").
    # A trade-off the person has put down and a bare "what would you do" after it: the bot has a
    # side, and saying it beats handing the decision back ("Not mine to decide, sorry") or asking
    # what the options are when they have just named two.
    leaning = _a_leaning_side(plain, memory)
    if leaning:
        return leaning
    mine = _my_pick(plain, memory)
    if mine:
        return mine
    verdict = _a_verdict_on_their_plan(plain, memory)
    if verdict:
        return _choose(verdict, memory, clean)
    # The place on the table, asked about in three words: "is it nice" after "we are going to
    # Cornwall in August". The nod pool read it as agreement and the hedge sent them to a search
    # engine; this says plainly that the bot has not been, and asks what the trip is for.
    place_ask = _a_place_asked_about(plain, memory)
    if place_ask:
        return _choose(place_ask, memory, clean)

    # The same ask as a bare "why", said about the words just used: "why do you say that", "how
    # come you said so", "what makes you say that". It carries nothing of its own for the
    # knowledge base to match, and the pool below owns every line about the bot, so it answered
    # these with a different question's answer - "No grand reason. Someone built a thing that
    # helps with everyday questions without a search engine" - which is why the bot exists, not
    # why it said what it said. The ask reaches the reason code first, and that code stands down
    # when the answer above was the bot describing itself, so the identity answer keeps its turn.
    saying_ask = why.respond_to_a_saying_ask(clean, memory, understood,
                                             body=_thread_is_about_the_body(memory))
    if saying_ask:
        return saying_ask

    about = _about(plain, understood)
    # A question the person is quoting is somebody else's question, and the two bot-about cards
    # below answer with the bot's own day and the bot's own clothes - the wrong person answering.
    # "how should i answer what are you up to" and "what do i say when they ask what are you
    # wearing" are interview and small-talk questions the person wants an answer to give, so the
    # frame stands these two cards down (`understanding.kinds.ANSWERING_A_QUOTED_ASK`) and the
    # knowledge base, which has the interview answer, takes the turn.
    if about in ("self_doing", "clothes") and ANSWERING_A_QUOTED_ASK.search(clean or "") \
            and _the_answers_take_it(clean or ""):
        about = None
    if about == "memory" and _a_tally_of_its_own_day(understood):
        return _choose(ABOUT_TALLY, memory, clean)
    if about == "hand":
        return _choose(HAND, memory, clean)
    if about in ABOUT:
        return _choose(ABOUT[about], memory, clean)
    if about:
        return _choose(ABOUT_SELF[about], memory, clean)

    # A small social slip of their own is a minute to be met warmly, not a verdict on the person.
    # It goes above the self-judgement pool, which read the word "embarrassment" in "im dying of
    # embarrassment" as one, and above the laugh pools' stand-down for a laugh that was at them.
    awkward = _their_own_slip(clean, memory)
    if awkward:
        said = _choose(awkward, memory, clean)
        if said is None:
            # A chat that has already had five of these has emptied the pool it chose, and the
            # other one is a line about the same kind of minute: better that than the stock nod
            # the turn falls to if this returns nothing.
            said = _choose(EMBARRASSED if awkward is LAUGHED_AT else LAUGHED_AT, memory, clean)
        if said:
            return said

    if SELF_SUBJECT.search(clean) and not SELF_BLAME_ASKS.search(clean) \
            and not WORDING_ASKS.search(clean) and not RATES_A_SKILL.search(clean) \
            and not _own_feeling(clean):
        # Before the asking branch: "am i useless" is the same sad question as "im useless", and
        # a search link answers neither. A line that also asks for something the bot can give
        # ("any tips", "what should i eat") keeps its own answer: the ask comes first.
        return _choose(SELF_BLAME, memory, clean)

    # The same question in the spelling the person meant: "any ideaz", "wich one should i pick".
    # A typo that hides the shape of the ask turns a question into a statement, and a statement
    # is answered by the nod or the hedge instead of the way in. The typed line is read first
    # and the repaired one only as a second try, like every other pool in this file.
    asking = kind == "question" or (kind == "statement" and (
        _reads_as_question(text, words)
        or (repaired != clean and _reads_as_a_question_when_repaired(repaired))))
    if asking and _thanks_then_said(clean):
        # "thanks, its back to how it was" is a report of the outcome, and the "how" in it made
        # the understanding read the whole line as a question, so the search hedge answered the one
        # turn the thanks pools below are for. A thanks that really asks keeps `asking`: the tail
        # has to be free of every question word ("thanks, can you do the same for the shed",
        # "thanks, how do i set the timer" both stay questions).
        asking = False
    if asking and _acknowledges_alone(clean):
        # "good to know" is the whole line and there is nothing in it to search for: `know` read
        # as the question word, so the acknowledgement went to the hedge - "I'd rather not guess.
        # A quick search online will get you a solid answer". Nothing is being asked, so the
        # thanks pools below answer it like any other "thanks".
        asking = False

    # A line with a right action gets it whatever its grammar: "i can smell gas" is not small
    # talk, and a statement can be an emergency.
    action = _action(clean, memory)
    if action:
        return action
    # A date that would have been theirs is not a fact to file away and not a question to hedge:
    # "it would have been our anniversary next week" was answered with "Got it, is there anything
    # you'd like a hand with", and "would have been our anniversary today" with the search hedge.
    # It sits here, after the action, because anything with an emergency in it is still that.
    if WOULD_HAVE_BEEN.search(clean):
        return _choose(MILESTONE, memory, clean)

    # A line that says the person is going is a goodbye, and the reason behind it is not a
    # question: "ill let you go, dinner is burning" is not a cooking question, and "anyway i
    # better go, hes crying" is not something to search for. Read here, so both the wording
    # and the arbiter's rule come from bot/compose/leaving.py.
    bye = leaving.pool(clean, words, memory=memory)
    if bye:
        return _choose(bye, memory, clean)
    # A goodbye whose reason is a body in trouble stands out of the body's way, and this module
    # only speaks when nothing answered it: "right, im off to bed, my tooth is agony" had no
    # toothache entry behind it, so the only thing left was to file the line back ("Noted: you're
    # off to bed, your tooth is agony"), which gives the person nothing. Letting them go warmly
    # is the smaller thing to say, and the body is asked about on the next line if they come back.
    if leaving.reads_as_a_leave_with_a_body_in_it(clean, words):
        bye = leaving.pool(clean, words, unwell_blocks=False, memory=memory)
        if bye:
            return _choose(bye, memory, clean)

    # "What should I say to my boss?" is not a search: it wants a shape to say it in. Before
    # the taste and live branches, because asking what to say is never a taste.
    # A slip inside the ask hides its shape: "waht shud i tell her face to face" carries "what
    # should i tell" with two letters missing and went to the search hedge, while the same line
    # spelt right was told how to open. So the line is asked twice - as typed first and as repaired
    # second, the way the question test above it already does - and only a line the reading had to
    # repair is asked twice, so a line that reads as typed is untouched.
    asks_for_words = _asks_for_words(clean, words) or (
        repaired != clean and _asks_for_words(repaired, words))
    if WORDING_ASKS_WHO.search(clean) and any(w in EXPERT_WORDS for w in words):
        asks_for_words = True
    if QUOTE_ASKS.search(clean):
        return _choose(QUOTE_LINES, memory, clean)
    if asks_for_words:
        if TELL_HARD.search(clean):
            return _choose(TELL_HARD_LINES, memory, clean)
        if "card" in words:
            return _choose(CARD_LINES, memory, clean)
        return _choose(WORDING_LINES, memory, clean)
    if _asks_how_are_you(plain, understood.get("plain") or "") \
            or understood.get("asks_how_i_am"):
        # The phrase table above holds the spellings it knows; the reading says the same thing
        # about every spelling of the greeting, so "how you been", "hows everything", "what u
        # saying" and "hows the day going" are answered here instead of reaching the search
        # hedge (`bot/understanding/kinds.py::asks_how_i_am`).
        return _choose(HOW_ARE_YOU, memory, clean)
    # A view asked for with nothing named ("whats your honest view?", "honest view?", "your take",
    # "honest answer"): the person is asking the bot to stand behind the answer just given, and a
    # search suggestion there is the bot denying its own paragraph. It is read before the taste
    # pools because "your take" and "what do you reckon" are in both families, and the general
    # taste line ("No strong view on that one, honestly. What's yours?") is the shrug for a
    # question with no answer behind it - said one turn after a full answer, it is a lie.
    taste = _taste(plain, memory, was_taste, asking, repaired)
    if taste:
        state["taste"] = True
        return taste
    # A phone number is wanted in lines that are not questions ("i need the number for the
    # jobcentre"), so it is read before the live pools, which wait for an ask word. Nothing
    # else here answers one, so it takes no answer away.
    number = _their_contact_number(plain, asking)
    if number:
        return _choose(number, memory, clean)
    # A line that only asks the bot to confirm its own limit is a question about the bot, and
    # the honest answer is the one it would give if they had asked it straight: what it cannot
    # do, and the one place that knows. "so you cant check the weather for me", said one turn
    # after the bot had said it had nothing live, got "I'm listening - say more if it helps",
    # which answers nothing at all; "you cant see my calendar can you" got the search hedge,
    # which sends a person to Google to find out what the bot can do. The live pools already
    # know which thing it is and where to find it, so the line is read as the ask it is.
    if _a_no_from_the_bot(plain):
        cannot = _live(plain, True, memory) or _the_live_thing_named(plain)
        if cannot:
            return _choose(cannot, memory, clean)
        if CANNOT_SEE_ANYTHING.search(plain):
            return _choose(CANNOT_SEE_ANYTHING_LINES, memory, clean)
        if CANNOT_READ_YOURS.search(plain):
            return _choose(_what_no_eyes_already_says(plain) or CANNOT_YOUR_OWN, memory, clean)
        if SO_NOTHING_LIVE.search(plain) or (
                _the_bot_says_it_cannot(plain) and CANNOT_ANYTHING_ASK.search(plain)):
            return _choose(CANNOT_ANYTHING, memory, clean)
    live = _live(plain, asking, memory)
    if live:
        return _choose(live, memory, clean)
    # A search that has just ended ("found them, in my coat pocket") is the good half of the
    # same chat, so it is answered as its own news rather than as a fresh topic.
    if loss.found_what_was_lost(clean) and loss.lost_thing_to_find(last_user(memory) or ""):
        return _choose(FOUND_IT, memory, clean)
    # A thing they are looking for is not an unanswerable question: "where are my keys" and
    # "have you seen my passport" want somewhere to look, so this comes before the honest hedge.
    # Standing outside the front door is not a search: the way back in is the answer, and it
    # comes before every "where to look" pool.
    if loss.locked_out(clean):
        if loss.locked_out_of_the_car(clean):
            return _choose(LOCKED_OUT_OF_THE_CAR, memory, clean)
        return _choose(LOCKED_OUT_LINES, memory, clean)
    if loss.keeps_losing_thing(clean):
        return _choose(LOST_A_THING_AGAIN, memory, clean)
    if loss.lost_thing_to_find(clean):
        return _choose(LOST_A_THING, memory, clean)
    # A verdict on the person's own worth is not a question for the bot, whatever grammar the
    # line arrived in: "my best isnt good enough" was read as a question and got the honest
    # hedge ("a quick search will get you a solid answer"). The same goes for the one lost line
    # that is written as a question ("what am i even doing with my life"). Both pools name the
    # thing and ask one question back, so they beat the hedge here.
    # Not being seen by the people around them is not a fact to file and not a question for the
    # bot: "i feel like nobody cares" was answered with the line said back ("you feel like nobody
    # cares - noted"), which is the loneliest reply there is. The reading is `bot/compose/unseen`
    # so the echo in `bot/memory/ack` can stand down for the same lines.
    if unseen.reads(clean):
        return _choose(unseen.LINES, memory, clean)
    own = _own_feeling(clean) or (
        NO_DIRECTION_REPLY if LOST_QUESTION.search(clean) and not NOT_SELF.search(clean) else None)
    if own:
        return _choose(own, memory, clean)
    # A routine, a habit or a day that keeps getting away: the composer can give a method, so
    # it does, instead of the shrug it gives a question it cannot answer.
    routine = _routine_pool(clean, words, memory)
    if routine:
        return _choose(routine, memory, clean)
    # A rating of one of their own skills is not a verdict on the person and not a bad day: "im
    # rubbish at saving" was filed away by the neutral nod ("Got it. Is there anything you'd like
    # a hand with?") and "im terrible with names" was read as heavy news ("Ugh, that's a lot to
    # carry"). The pools that treat it as self-blame already stand aside for it (RATES_A_SKILL);
    # this is what it gets instead. It sits after the routine and the wording answers, which are
    # more use to the line ("im rubbish at mornings" keeps the morning method), and before the
    # hedge and the gentle pools, which give it nothing.
    if (I_RATE_A_SKILL.search(clean) and not WORDING_ASKS.search(clean)
            and not A_WAY_OF_BEING.search(clean)):
        return _choose(ONE_SKILL_RATED, memory, clean)
    # ...and the same thing asked as a question, which is the shape that got the search hedge: "am
    # i any good at my job" was told a link would sort it out, and "am i a good mum" and "am i good
    # enough" got the nod or the hedge. They sit here rather than with the self-blame pool above
    # because the ask is what the line is: a question that wants a mark nobody can give, and the
    # one useful thing left to say is the question about what happened. A line with an ask of its
    # own ("am i good enough what should i do") keeps its own answer, as the statement version does.
    if not SELF_BLAME_ASKS.search(clean):
        if A_SKILL_ASKED_OF_ME.search(clean) and not A_WAY_OF_BEING.search(clean):
            return _choose(ASKED_A_RATING, memory, clean)
        if A_GOODNESS_ASKED_OF_ME.search(clean):
            return _choose(ASKED_IF_GOOD, memory, clean)

    # A bare "why" asks for the reason behind the answer just given. It has no words of its own
    # to match, so nothing above could take it, and the search hedge throws the last turn away:
    # the reason is not something this bot can see, so it says that and asks what would narrow it
    # (bot/compose/why.py).
    why_follow_up = why.respond(clean, memory, understood,
                                body=_thread_is_about_the_body(memory))
    if why_follow_up:
        return why_follow_up
    # A job asked of the bot itself, in the imperative ("take the rubbish out") or politely
    # ("can you ring the school for me"): neither is a question to search for nor a statement to
    # file away. The limit is the answer, so it comes before the hedge, and each shape of job
    # says what the bot can offer instead.
    asked = _act_asked_of_me(clean)
    if asked:
        return _choose(asked, memory, clean)
    if _acts_for_me(clean, memory):
        return _choose(ACTS_FOR_ME, memory, clean)
    # A job in the world typed as an order rather than as a polite ask: "text my mum", "book the
    # tickets", "set a timer for 10 minutes". Nothing above claims them and the store's nod read
    # as a job done, so the limit comes next, before the hedge.
    ordered = _an_order_it_cannot_do(clean)
    if ordered:
        return _choose(ordered, memory, clean)


    # A lump keeps its own answer even where a specialist is named: the line that names one
    # would be right ("a pharmacist or your GP can answer that today"), and for a lump the GP
    # line says the same thing and says what to do ("ring your GP surgery and say you have
    # found a lump"), where the named line hedges ("not mine to decide, sorry").
    if reads_like_a_symptom(repaired.lower()) and _LUMP.search(repaired):
        return _choose(LUMP, memory, clean)
    settled = " " + re.sub(r"[^a-z0-9']", " ", clean) + " "
    if (reads_like_a_symptom(repaired.lower())
            and not _who_for(clean, settled, settled.replace("'", "").split())
            and not (trouble.reads_as_trouble(clean, words, repaired) == "sore"
                     and not _CAUGHT.search(clean))
            and says_it_has_lingered(repaired, illness=bool(_ILL.search(repaired)))):
        return _choose(SYMPTOM_LINGERS, memory, clean)
    # A body complaint asked as a question is not an unanswerable question when nobody else can
    # be named for it: "what should i do about my bad back" got "I'd rather not guess. A quick
    # search online will get you a solid answer", and the warm line for a back that is bad ("go
    # easy on yourself today, and see someone if it's not shifting") is the friend's answer.
    if (asking and reads_like_a_symptom(repaired.lower())
            and not _who_for(clean, settled, settled.replace("'", "").split())
            and not (trouble.reads_as_trouble(clean, words, repaired) == "sore"
                     and not _CAUGHT.search(clean))):
        return _choose(SYMPTOM_COLD if _ILL.search(repaired) else SYMPTOM, memory, clean)
    # A lateness report is not a question nobody can answer: "im running late for the school pick
    # up" was read as an ask and got the search hedge, and "im running late for work" was read off
    # its verb as a job under way ("im painting my kitchen") and cheered. Both are the same line
    # as "im late for work", so all of them get the one useful reply. A line that asks something
    # on top of it ("im late again, what do i say to my boss") keeps its own answer below.
    if _a_lateness_report(clean, (understood or {}).get("norm_text") or ""):
        pool = (LATE_BEHIND_LINES
                if "behind" in clean or "behind" in ((understood or {}).get("norm_text") or "")
                else LATE_NOW_LINES)
        return _choose(pool, memory, clean)

    # An invitation is somebody asking for company, and nothing about the world answers it: "do
    # you fancy a walk" got the search hedge, "you up for a walk" the neutral nod and "want a
    # brew" the floor. The honest warm line comes before both.
    invited = _an_invitation(clean)
    if invited == "talk":
        return _choose(INVITED_TO_TALK, memory, clean)
    if invited:
        return _choose(INVITED, memory, clean)
    # A line that only narrows the answer above goes back to it. "we fancy a few days away in
    # october" was answered with four destinations, and "somewhere thats not too far" got "Got it.
    # Is there anything you'd like a hand with?"; "cheaper" the same, "under 20 minutes" was said
    # back as "Got it - under 20 minutes", and "not too far" after "we want a day out" got "Thanks
    # for telling me - I'm here if you want to dig into any of that". Nothing in the line names a
    # subject, so it falls past every reader that would give it a topic and lands on the ack: what
    # it does is choose a direction to cut in, and the answer to cut is still on the screen. The
    # axis is read from the line and the reply goes back to "those" with the one question that
    # pins it, which is what a friend says to "somewhere not too far".
    # A line with two limits in it is tried one limit at a time, in the order `the_limits_said` puts
    # them: the bound-carrying part first, then the last said. Only a limit the answer above can be
    # cut on gets the reply, so "under 500 pounds each and not too far" after four destinations that
    # quote no prices is the distance question, not a budget one; and the bound is taken from the
    # part it belongs to, because read off the whole line "under 500 pounds and close" says the
    # person's own words back as the bound.
    limits = the_limits_said(clean) or [(reads_as_a_narrowing(clean), "")]
    for axis, part in limits:
        if not axis or not the_answer_to_cut(memory, axis):
            continue
        bound = the_bound_said(part or clean)
        if bound:
            return _choose(BOUND_FOR[axis], memory, clean).format(bound=bound)
        return _choose(CUT_FOR[axis], memory, clean)

    # Somebody close refusing the thing that would help them, and the person caring for them at the
    # other end of the line: "she refuses a pendant alarm" was answered "Got it. Is there anything
    # you'd like a hand with?", "hes 80 and wont use a stick" with "I'm here if you want to dig into
    # any of that", and "he wont go to the doctors" with the floor. Nothing in the file could read
    # it, and the two things worth saying are what the refusal is usually about and the person whose
    # word carries - neither of which is a fact the bot would be guessing at. It sits here, after
    # the emergencies, the goodbyes and the plans, and before the nod: a crisis, a bereavement or a
    # safety thread keeps its own voice, and the second refusal in a thread gets the detail it
    # brings rather than the same paragraph in other words.
    refused = _a_carer_refused(clean) or _a_carer_refused(repaired)
    if (refused and not _hedged_recently(memory)
            and not (_in_a_loss_thread(memory) or _grief_thread(memory)
                     or in_a_safety_thread(memory))):
        pool = {"aid": ELDER_AID_REPLIES, "clinic": ELDER_CLINIC_REPLIES,
                "doctor": ELDER_DOCTOR_REPLIES, "help": ELDER_HELP_REPLIES}[refused]
        said_before = str((memory.get("turns") or [{}])[-1].get("bot") or "")
        if not _in_a_pool(said_before, (ELDER_AID_REPLIES, ELDER_CLINIC_REPLIES,
                                        ELDER_DOCTOR_REPLIES, ELDER_HELP_REPLIES,)):
            return _choose(pool, memory, clean, clean + " " + _the_line_before(memory))

    # A thing of theirs on their own side, handed over or asked about. The asks are read in
    # `_unknown` below; a line that hands it over ("here's a screenshot", "the link is www...")
    # is not a question at all, so it never reaches there and used to get "Got it. Is there
    # anything you'd like a hand with?" as though the picture had arrived.
    handed = no_eyes.handed_you_something(clean)
    if handed:
        return _choose(handed, memory, clean)

    # "help me fill in this form" asks the bot to do something to a thing on the person's side and
    # is not a question, so it never reached `_unknown` where the same reader answers "can you fill
    # in this form", and it got the search hedge. The limit is the same whoever phrases it.
    # A mark on their own body is not a page on their screen: "can you see if this mole is ok"
    # holds "see" and "this", so the reader below reads it as the text they are looking at and
    # answers "I can't see the page you're looking at - paste the bit you want help with". The
    # pool above already asks the body reader first for the same reason; this is the other way
    # into the same line, so it asks first here too.
    body_lines = no_eyes.look_at_a_body_lines(clean, None, memory)
    if body_lines:
        return _choose(body_lines, memory, clean)
    cannot_see = no_eyes.cannot_see_your_thing(clean)
    if cannot_see:
        return _choose(cannot_see, memory, clean)

    # "Am i bothering you", "am i bugging you", "do you mind me asking", "should i stop asking":
    # the apology for asking turned into a question, and the person wants to hear that they are
    # welcome rather than an answer about anything. It goes above the door below, which sends
    # every unclaimed question to the search hedge - the web was searched for whether the bot
    # minds being asked - and the pool is the one the apology for asking already gets. The mood
    # is not read first: "annoying" in the line would make it a bad mood.
    if _am_i_a_nuisance(clean) and not _grief_thread(memory) and not in_a_safety_thread(memory):
        return _choose(SORRY_FOR_ASKING, memory, clean)

    # Nothing here can answer it: say who can, when the line names that world, and stay
    # honest when it does not. A correction is not that: "no it was my idea not the kids" takes
    # something back, and the hedge sent the person to a search engine to do it ("I don't know
    # enough to answer that honestly"). It is answered where the other corrections are, at the
    # end of the chain (`A_CORRECTION_TAKEN`), so the echo and every reading with something of
    # its own has already had its turn by the time it is reached.
    if asking and not _takes_something_back(clean, memory):
        # A line about how the person is, typed in the shape of an ask, reaches this door and
        # nothing else: "nothing feels worth doing", "nothing is worth it any more", "nothing
        # feels good". Nothing here can look it up and no page knows them, so the hedge ("a quick
        # search online will get you a solid answer") is a shrug at the person it is said to. The
        # gentle pools are what this file says to a low line everywhere else, and the reading that
        # puts the pleasure-gone family together is the same one `_mood` uses, so the two cannot
        # disagree about a line.
        if reads_as_no_pleasure(clean) or (repaired and reads_as_no_pleasure(repaired)):
            return _choose(PLEASURE_GONE_LINES, memory, clean)
        step = step_when_low(clean, memory, COMFORT_SAID)
        if step:
            return step
        # The one ask that is always answerable: whether this program can drive, smell, feel pain.
        # Above the hedge, because there is nothing to look up, and below everything else, because
        # a line about a thing of theirs has already been answered by now.
        if reads_as_a_question_about_the_bot(clean) or reads_as_a_question_about_the_bot(repaired):
            return _choose(ABOUT_THE_BOT_LINES, memory, clean)
        unknown = _unknown(understood, memory, clean)
        # A question about clothes that no clothes row answered still has the rule that decides it
        # and one question to narrow it, which beats sending the person to a search engine with
        # the question they just asked. Only the hedge is replaced: a route to the place that does
        # know ("the dress code is on the invite") is still the better reply when there is one.
        if _a_wear_ask_about_a_day(clean, repaired, text) and is_a_hedge(unknown):
            return _choose(_the_wear_pool_for_the_line(clean, repaired, text), memory, clean)
        return unknown

    # The bot's own last turn offered to write the message, and this line is that detail.
    # Handing it back ("Got it - you're off sick tomorrow") is the one reply the offer rules out,
    # so below the news, the symptoms and the losses (a death is condoled, not drafted) and above
    # the topic entries, which is the half that has to lose the turn.
    drafted = draft.drafter(memory, text, words)
    if drafted:
        return _choose([f'{lead} "{drafted}"' for lead in draft.LEAD_INS], memory, clean)
    if draft.not_the_message(memory, text):
        # The offer is still open: a complaint is not the message, so ask for the words instead of
        # quoting "my boss is a nightmare" back as a text to send.
        return _choose(draft.NOT_YET, memory, clean)

    if _reads(reads_as_pregnancy_bleeding, clean, repaired):
        return _choose(PREGNANCY_BLEEDING, memory, clean)
    if a_fresh_death_and_the_words(clean):
        # The death is the whole line and the ask is the words: the pool for it, before the
        # condolence, which is what the line above would answer this turn with.
        return _choose(THE_FIRST_HOUR_AND_A_CHILD, memory, clean)
    if _reads(reads_as_sudden_loss, clean, repaired):
        return _choose(SUDDEN_LOSS, memory, clean)
    if _reads(reads_as_recovery, clean, repaired, lower=True) and not _in_a_loss_thread(memory):
        return _choose(RELIEF, memory, clean)
    # A test that came back clear is the same news as "the pain has gone": relief said back, not
    # congratulations and not the gentle pool. It has its own reader because the subject is often
    # somebody else ("my mums cancer is in remission"), which `reads_as_recovery` excludes.
    if _reads(reads_as_a_clear_result, clean, repaired, lower=True) and not _in_a_loss_thread(memory):
        return _choose(RELIEF, memory, clean)
    # The same news about someone else, or about the thing that was wrong - "hes ok
    # now", "its gone down now" - but only while a worry is on the table: in a chat
    # about a broken phone these are still an echo of a detail.
    if (reads_as_settled(clean.lower()) and worry_on_the_table(memory)
            and not _in_a_loss_thread(memory)):
        return _choose(RELIEF, memory, clean)
    # Being turned away from work is not bad news to be gentle about and not small talk: the
    # closed-door pool names the door and asks the one question worth asking.
    if _reads(reads_as_a_closed_door, clean, repaired):
        return _choose(CLOSED_DOOR, memory, clean)
    if _came_back(clean) and in_a_safety_thread(memory):
        # "i cut my hand and it wont stop bleeding" then "sorry i went quiet" was answered "No
        # bother at all - go on": a breezy hand-back to somebody who has just been told to keep
        # pressing on a wound. The pause is still a go-ahead, in the voice of the thread it is
        # said in - the same reasoning as the condolence below, and the same `in_a_safety_thread`
        # the rest of this file asks before it answers an emergency with anything lighter.
        return _choose(PAUSE_IN_A_SAFETY_THREAD, memory, clean)
    if _came_back(clean) and not _grief_thread(memory):
        # The thread paused for a minute; the apology is the whole content of the line. After a
        # condolence it is not: "sorry i went quiet" there is the person coming back to the
        # hard thing, and the listening line keeps the floor with them.
        #
        # It comes before the bad news, because the word that made the mood sad is usually part
        # of the apology itself ("sorry, i lost track" has "lost" in it) and the reading only
        # says this when nothing else is in the line: "sorry i missed your message, my mum died"
        # is still the death's.
        return _choose(CAME_BACK, memory, clean)
    # The leaving said about the partner without the "me" ("my wife is leaving and i dont know
    # what to do", "i think my partner wants to leave") is not read as bad news by the gate below,
    # which looks for the words of a loss, so it fell through to the stock nod. It is the same
    # news as being left and it gets the same pool, before anything else reads the line.
    if (_reads(reads_as_the_leaving, clean, repaired)
            and not _reads(reads_as_the_speakers_own_plan, clean, repaired)
            and not _a_things_state(memory, clean)):
        return _choose(
            LEFT_POOL_GONE if reads_as_a_leaving_already_gone(clean) else LEFT_POOL,
            memory, clean)
    # A relationship ending the person is deciding on is not news that happened to them: "im
    # leaving him tonight" is a decision, and "Sorry to hear that" is what you say to the person
    # it happened to. Those lines have their own answer below (RELATIONSHIP_DECISION, then PLAN
    # for a next step), so the sad pool stands down for them and stays for the turn that is
    # about being left. ack's reading keeps LEFT_PLAN whole, because after "im thinking of
    # leaving my husband" the next line is still the middle of a story.
    # A standing situation of theirs, said on its own ("i rent", "im a carer", "im self
    # employed", "im on benefits", "im disabled", "im divorced"): where they are starting from,
    # not a job to chat about, not a small day that went by, not bad news and not a fact to file
    # away. It comes before the mood's own pools for that reason - the small-day pool answered
    # "im disabled" with "Good to hear. What was the best bit?" and the receipt answered "i
    # rent" with "Thanks for telling me", and the sad pool read "im divorced" as news. Only a
    # whole line is a situation, so a line that goes on to say something else ("i rent and the
    # boiler is broken") keeps the reading it has (bot/compose/circumstance.py).
    situation = circumstance.pool(clean)
    if situation:
        return _choose(situation, memory, clean)
    # The figure of speech is not bad news, whatever the sad words in it: "i keep killing myself
    # laughing" is read as a trouble by the sad words alone, and the gentle pool answers it with
    # "ugh, that's a lot to carry" for a person who is laughing. The idiom has its own light line
    # further down, so this stands aside for it.
    # A named condition on someone they look after, a child they are kept from, a court letter
    # or a house that has to go names nobody who can settle it, so the gentle pool is the answer.
    # An award stopped or refused is the other kind of line: where the person whose job settles it
    # can be named ("they stopped my universal credit" -> MoneyHelper, a frozen pension the same),
    # the pointer is concrete and "I'm sorry - that's frustrating" is not, so the award stands
    # aside and the pointer keeps its turn. It is the award alone: a house sold to cover the
    # mortgage names a mortgage and is still not a money-advice question.
    # A home entered is not the gentle pool's line either: "someone broke into our house" is read
    # as bad news and answered "Ugh, that's a lot to carry", and a person who has just been
    # burgled needs the order of the two phone calls first.
    broken_into = remark.break_in_reply_for(clean, words, memory)
    if broken_into:
        return broken_into
    if (_reads(reads_as_bad_news, clean, repaired)
            and not _reads(reads_as_the_speakers_own_plan, clean, repaired)
            and not PLAN_IDIOM.search(clean)
            and not (_reads(reads_as_an_award_lost, clean, repaired)
                     and who_settles(clean, memory))):
        if _a_things_state(memory, clean):
            return _choose(A_THING_LOOKS_SAD, memory, clean)
        if _reads(reads_as_the_leaving, clean, repaired):
            return _choose(
                LEFT_POOL_GONE if reads_as_a_leaving_already_gone(clean) else LEFT_POOL,
                memory, clean)
        # "That's frustrating" is a word for a setback, and half of this list is a person: a dad
        # with parkinsons, a daughter taken into care, a roof that has to go. Those keep the pool
        # without that one line (NAMED_NEGATIVE); a court date and a wage stopped are the other
        # kind and keep the whole pool.
        # The third refusal is not the first one: "my dla got refused again" is a line whose one
        # concrete thing is the repeat, and the gentle pool answers it as if it were new
        # ("Sorry to hear that"), which loses the only part of it a friend would pick up. The
        # repeat pool is below this gate and would have answered it, so the gate stands aside for
        # that shape alone; read here so nothing else between the two can claim the line.
        if remark.reads_as_report(clean, words) == "again":
            again = remark.report_reply_for(clean, words, memory)
            if again:
                return again
        # A heart attack, a cancer, an operation, the hospital: news about someone close has no
        # next step to offer and no "it depends" to weigh, so the gentle pool's "that's
        # frustrating" is too small a word for it. Asked as a question ("my dad had a heart
        # attack, what do i do") it is not this pool's: that line wants the practical answer the
        # rest of the file gives, so the pool is only for the news as news.
        if not asking and _reads(reads_as_someone_close_is_ill, clean, repaired):
            return _choose(SOMEONE_SERIOUSLY_ILL, memory, clean)
        pool = NAMED_NEGATIVE if _reads(reads_as_news_with_a_name, clean, repaired) else NEGATIVE
        return _choose(pool, memory, clean)
    # Somebody they love is leaving: "my daughter is leaving home for uni", "my best friend is
    # moving away", "my neighbour is moving away and i will miss her". It sits here, above the
    # echo and above the gentle pool, because the two things the person can get here both say
    # nothing about the thing that is happening: "Noted: your daughter is leaving home for uni"
    # is the coldest line this file has, and "that sounds rough" is sympathy for a change that
    # may be half proud. It is below the bad-news and separation pools, so a death, an ending or
    # an emergency is still theirs.
    if (not asking
            and not _in_a_loss_thread(memory)
            and _reads(LEAVING_A_PERSON.search, clean, repaired)
            and _reads(LEFT_BEHIND.search, clean, repaired)
            and not _reads(NOT_LEAVING_ANYONE.search, clean, repaired)):
        is_a_child = _reads(A_CHILD.search, clean, repaired)
        has_happened = _reads(THE_LEAVE_HAS_HAPPENED.search, clean, repaired)
        if has_happened:
            pool = A_CHILD_LEFT if is_a_child else SOMEONE_GONE
        else:
            pool = _only_what_the_line_gives(
                A_CHILD_LEAVING if is_a_child else SOMEONE_LEAVING, clean)
        return _choose(pool, memory, clean)
    # A complaint about someone else, or a penalty that landed on them ("my boss had a go at me",
    # "i got a parking ticket") is not small talk: the stock nod answers it with nothing. The
    # gentle pool is the word for it, and it is never said back (ack.COMPLAINT).
    if _reads(ack.COMPLAINT.search, clean, repaired):
        if _a_things_state(memory, clean):
            return _choose(A_THING_LOOKS_SAD, memory, clean)
        return _choose(NEGATIVE, memory, clean)

    # "what am i even doing with my life" is not a question for the bot: it is the person
    # saying they are lost, and the honest hedge ("a quick search will get you a solid answer")
    # is nonsense for it. So it is answered with the direction pool before the hedge, which is
    # the one place it can be, because the line is read as a question.
    # Somebody asking the bot for something that nothing could answer must not get a neutral
    # nod ("got it, is there anything you'd like a hand with?"): it ignores what was asked. Say
    # plainly that this one is beyond what the bot knows, and stay useful.
    # A correction is not an ask to the bot, though the words inside it can look like one: "no it
    # was my idea not the kids" is a statement, and the reading of it as an ask sent it to the
    # search hedge - "I don't know enough to answer that honestly" - for somebody putting the bot
    # right. It is answered at the end of the chain, with the other corrections.
    if (_asks_the_bot(understood) and not _takes_something_back(clean, memory)
            and not _reads_value(_a_good_time, clean, repaired, memory)
            and not _reads(reads_as_a_win_nobody_noticed, clean.lower(), repaired.lower())
            and not _a_good_time(clean, memory)
            # A doubt about what to do is read as a question for the bot, and nothing in the
            # knowledge could answer it, so it took the search hedge - "a quick search online
            # will get you a solid answer" for "no idea what to do next" and "i have no idea what
            # to do". It is not a fact to look up: the open doubt pool below asks the one question
            # that gets at it, and it is reached from here now instead of after the hedge.
            and not (_reads_as_dither(clean, repaired) and _weighs_a_choice(clean))
            and not _a_dead_end(clean) and not _the_person_they_are_stuck_on(clean)
            # "good to know" reads as an ask to `_asks_the_bot` ("good" is an imperative verb by
            # grammar) and there is nothing in it to look up, so it took this door: "I'd rather
            # not guess. A quick search online will get you a solid answer" for somebody saying
            # the answer was useful. It is acknowledged by the thanks pools below, like any other
            # "thanks" - the line asks for nothing and the one thing it must not get is a search.
            and not _acknowledges_alone(clean)):
        # A good time said plainly ("best day ever", "great day today") is not a request, and
        # "I'd rather not guess, do a search" answers it by sending them to Google. Neither is a
        # win with a silence round it: "i got the job and nobody said anything good" has the words
        # of an ask for tips and is a letdown, so the search hedge is the last thing it needs.
        tips = _tips(memory, clean, repaired)
        if tips:
            return tips
        # A request the bot cannot answer still wants the reply its shape asks for: "help me
        # write an email to the council" is a wording request, not a fact question, so it gets
        # the same offer to draft as "can you help me write a text to my boss". One place works
        # out which pool that is (`unknown_pool`), so both doors open on the same lines.
        #
        # "i have no idea what to do" is this block's line said from the other end: it names
        # nothing to look up, and a search engine is the worst reply to somebody asking for a
        # hand. The offer the bare "what should i do" already gets is the reply, so the lost ask
        # is read at the same door - only the shape, because everything with a subject of its own
        # has already answered above. A thread already working through advice keeps it: "the
        # boiler is broken" then "i dont know what to do" is the next step of that advice, and
        # asking what has gone on reads as a bot that was not listening.
        free_time = _the_stretch_of_time(clean, memory)
        if free_time:
            return free_time
        lost = the_lost_ask_reply(memory, clean, repaired)
        if lost:
            return lost
        pool = unknown_pool(clean, words)
        if pool is UNKNOWN_WORD:
            # The same drafting chooser as the pool reader's own door, imported on the call the
            # way `fallback.py` reaches that module: asking who it is for after the person has
            # just said who it is for is the failure this stands down from.
            from .fallback_pools import _drafting_pool
            return _choose(_drafting_pool(clean), memory, clean)
        # A request the bot cannot answer often names the thing that can: "find me a plumber near
        # me" wants somebody local and no list of them is here, so the search hedge, which says a
        # search will sort it out without saying where, is the weakest of the honest replies.
        # The route pool names the one place and the one question, and it stands down on its own
        # for everything it cannot route better than the hedge.
        routed = finding_out.for_the_ask(clean, repaired, understood)
        if routed:
            said = _choose(routed, memory, clean)
            if said:
                return said
        # A question about clothes that no clothes row answered - the occasion is one the tables
        # do not have, or the ask was said the long way round - still has the rule that decides it
        # and one question to narrow it ("a layer you can take off, and shoes you can spend the
        # day in", then whether it is indoors or out). The hedge sends the person to a search
        # engine with the question they just asked, which for clothes is never the best reply
        # here: what decides it is the weather and how long they will be on their feet, and that
        # is true of every occasion, including the one the bot has never heard of.
        if _a_wear_ask_about_a_day(clean, repaired, text):
            return _choose(_the_wear_pool_for_the_line(clean, repaired, text), memory, clean)
        return _choose(UNKNOWN, memory, clean)
    # "Any tricks" is the same plea as "any tips" and the same shape: a statement by grammar
    # ("any tips" has no ? and no wh-word either, and it is answered here through `_asks_the_bot`).
    # The word "tricks" is the one the reading does not treat as asking, so it used to fall through
    # to the flat nod. It sits here, below the safety and bad-news reads, so a plea for tricks in a
    # line about bleeding or a death still gets the emergency rather than "what have you tried".
    if _reads(_is_a_tips_ask, clean, repaired):
        tips = _tips(memory, clean, repaired)
        if tips:
            return tips
        return _choose(TIPS_LINES, memory, clean)
    # A statement of trouble ("my landlord wont fix the damp") is not a question, but the same
    # person can settle it, so name them rather than nodding.
    told = _trouble(memory, repaired, words)
    if told:
        return told

    # "anything else" on two words is a request for more of the answer just given, not a nod:
    # the flat pool here asks "is there anything you'd like a hand with", one line after the
    # bot has just answered the same subject.
    if (asks_for_more(clean, memory) and not _hedged_recently(memory)
            and _answered_recently(memory)):
        return _choose(HELP_ALREADY, memory, clean)
    if _in_sudden_loss_thread(memory):
        # The next line of that chat ("my partner wont talk about it") is still the same loss, so
        # it is answered with room to say more, not with a stock line that fits any message. It
        return _choose(loss.AFTER_REPLIES, memory, clean)
    if len(words) <= 2 and set(words) & ACKS:
        if _a_loss_recently(memory):
            # "mm" and "ok" are how a person answers a condolence, and ACK's first line is
            # "Great — shout if you need anything else": after "the funeral was yesterday" the
            # bot told them great and offered a hand with anything. Answer the nod with room to
            # say more instead.
            return _choose(loss.AFTER_REPLIES, memory, clean)
        if _the_last_line_was_bad_news(memory):
            # "Great — shout if you want anything else" is the nod pool's first line, and after
            # "my mum has cancer" it congratulates the person on the news. A nod to heavy news is
            # them taking it in, so it gets the same room to say more a condolence gets - the
            # pool main already uses for "i lost my job" / "mm".
            return _choose(loss.AFTER_REPLIES, memory, clean)
        if _the_last_line_was_a_fault(memory):
            # "my knee is sore when i run" is everyday trouble, not heavy news: no congratulation,
            # no laugh, and no question, which asks them to start again on a subject still open.
            return _choose(ACK_AFTER_TROUBLE, memory, clean)
        if _the_last_line_was_heavy(memory):
            # One step away from a fault: the bot's own line was a condolence or a sorry ("im
            # really sad" / "mm" was told "Great — shout if you need anything else"). The nod
            # there is the person staying in the room, so it gets room and no cheer.
            return _choose(ACK_WARM, memory, clean)
        return _choose(ACK, memory, clean)
    # A kept-forgetting habit is a task to sort out before it is a loop ("i keep forgetting to
    # water the plants" has a plant in it), so it is read first.
    if not _in_a_loss_thread(memory):
        if FORGETS_A_CLASH.search(plain):
            return _choose(DOUBLE_BOOKED, memory, clean)
        if FORGET_A_DATE.search(plain):
            return _choose(DATES_KEEP_SLIPPING, memory, clean)
        if FORGET_A_SECRET.search(plain):
            return _choose(SECRETS_KEEP_SLIPPING, memory, clean)
    if FORGETS_AGAIN.search(plain) and not _in_a_loss_thread(memory):
        return _choose(KEEPS_FORGETTING, memory, clean)
    if _is_rumination(clean):
        # A line that says the same thing is going round again ("i keep going over it in my head
        # at 2am", "its been on my mind all week") is not a fact to file away: saying it back
        # returns their own sentence with nothing added, and "noted" is an intake form. The loop
        # itself is worth a word, then the one thing it keeps returning to.
        return _choose(RUMINATION_REPLIES, memory, clean)
    mood = _mood(words, clean)
    # A detail added to the complaint we are already on ("its sore when i sit down" after "how
    # long has it been like that?") is the next line of the same complaint, not a new subject.
    # Nothing in the composer could hold that thread, so it was answered with a stock line that
    # could have come before any message at all. It only fires on one of this module's own
    # questions as the last reply, and only for a line that is a detail about it.
    carried = trouble.carried_on(clean, words, memory)
    if carried:
        return _choose(carried, memory, clean)
    # A result they did not get is not a win and it is not a day that went alright, and every
    # pool reads the result without the "almost" in front of it: "i almost got the job" was
    # answered "Good to hear. What was the best bit?", "i almost won" "Nice one. How did the rest
    # of it go?", and "i nearly broke my pb yesterday" "Right. What have you tried so far?" - a
    # repair question about a personal best. The mood reading already refuses a cue behind
    # "nearly" (`nearly` in bot/compose/__init__.py), and the record reading does too, which is
    # why nothing above answers these lines; what was missing was a reply for the near miss
    # itself. It comes before the trouble question, which read "broke my pb" as a fault.
    if _a_near_miss(clean):
        return _choose(NEAR_MISS_REPLY, memory, clean)
    if mood == "neutral" and repaired and repaired != clean:
        # The reading put the line right ("me n my gf r arguin a lot" -> "me and my gf are
        # arguing a lot") but `_mood` reads the words as they were typed. A cue in the repaired
        # line is a cue in what the person said, so the typed line is read first and this is the
        # second try - the same deal the pools below make with `understood["plain"]`. Without it
        # the quick way of typing the same line gets "Got it. Is there anything you'd like a
        # hand with?" where the spelled-out line gets "Sorry to hear that."
        mood = _mood(_words(repaired), repaired)
    # The warm line is for an illness the person names ("i've got a sore throat", "i think ive
    # got the flu"), not for a body part that hurts: "my knee has been aching for a week" is the
    # trouble module's question, and "rest, warm drinks and an early night" is the wrong advice
    # for a knee anyway. trouble.reads_as_trouble tells the two apart, so it decides this one.
    # The cold's own line ("rest, warm drinks") is kept for an illness it fits; a headache at a
    # desk gets the two lines that suit any symptom.
    # A bug the person caught keeps its advice: reads_as_trouble answers "sore" for a cough as
    # well as for a knee, but "i've had a cough for three weeks now" wants "see someone if it is
    # not shifting", and the trouble question would ignore how long they have had it. So it is
    # only a body part that hurts that hands the line over, and a caught bug is not a body part.
    # Before the person's own symptom, because a cat and a horse are looked after in the same
    # words: "my cat has a bad back" is not "take it slow today".
    if mood != "positive" and _reads(reads_for_a_pet, clean.lower(), repaired.lower()):
        if _reads(reads_as_a_pet_low, clean.lower(), repaired.lower()):
            return _choose(PET_LOW_REPLY, memory, clean)
        condition = _reads(reads_as_a_pet_condition, clean.lower(), repaired.lower())
        return _choose(PET_CONDITION_TROUBLE if condition else PET_TROUBLE, memory, clean)
    if mood != "positive" and _reads(reads_as_a_carer_body, clean.lower(), repaired.lower(),
                                     memory=memory):
        return _choose(CARING_FOR_A_BODY, memory, clean)
    if mood != "positive" and _reads(reads_for_a_carer, clean.lower(), repaired.lower(),
                                     memory=memory):
        return _choose(CARING, memory, clean)
    if (mood == "neutral" and _reads(reads_like_a_symptom, clean.lower(),
                                     repaired.lower())
            and not (trouble.reads_as_trouble(clean, words, repaired) == "sore"
                     and not _CAUGHT.search(clean))):
        return _choose(SYMPTOM_COLD if _ILL.search(repaired) else SYMPTOM, memory, clean)
    if _a_relationship_ending(clean):
        # "i'm finally leaving him" is read as good news by the cue and as a next step by the
        # plan, and both cheer: "Lovely to hear. Enjoy it!" and "Nice one. Let me know how it
        # goes." The decision is the line, so it is answered as one.
        return _choose(RELATIONSHIP_DECISION, memory, clean)
    # A good time had by a group or by an event is a chat nobody can add a fact to, so it gets the
    # warm pool rather than the nod. Before the congratulations, which reads oddly for a party
    # they went to ("Good for you! That sounds like it was worth the wait").
    # Something funny is the good half of a chat, so it is answered with a laugh and a question
    # about it. It sits above the echo and the neutral pool, which between them either said the
    # line back without the smile or treated a laugh as something to sympathise with.
    if a_comparison_of_standing(clean) and not _in_a_loss_thread(memory):
        # Somebody holding their own life up against a crowd's gets the comparison answered, not
        # a cheer for the crowd and not the stock nod. In a loss thread it stands aside: "everyone
        # my age has their mum still" is grief, and the condolence is the right reply to it.
        return _choose(A_COMPARISON_OF_STANDING, memory, clean)
    if (mood != "negative" and not a_limit_on_the_answer(clean)
            and _something_funny(clean, memory)):
        return _choose(A_LAUGH, memory, clean)
    # The person measured against other people: "everyone else seems to have it sorted", "all my
    # mates have bought houses", "im 41 and everyone my age seems busy with kids". Every reader
    # above wants something to answer - a plan, a report, a thing that went wrong - and these
    # carry none of it, so on main they reach the pools that answer nothing: the account of the
    # day ("How was it, overall?"), the cheer the word "sorted" alone earns ("Good to hear. What
    # was the best bit?"), the intake form, or the line said back. What a friend answers is the
    # comparison, not the milestone: nobody's week looks like their update, and the scoreboard is
    # not the person's own. It sits above the good-time and day pools because those are what it
    # was falling into, and below every reading with something of its own.
    if not _in_a_care_thread(memory) and _the_crowd_is_ahead(clean):
        return _choose(A_CROWD_AHEAD, memory, clean)
    if mood != "negative" and _reads_value(_a_good_time, clean, repaired, memory):
        if _in_a_care_thread(memory):
            return _choose(A_GOOD_TIME_IN_A_CARE_THREAD, memory, clean)
        return _choose(A_GOOD_TIME, memory, clean)
    if mood != "negative" and _reads(reads_as_a_win_nobody_noticed, clean.lower(),
                                     repaired.lower()):
        # Two things in one line - the win and the silence around it - and congratulating alone
        # answers half of it. Before the congratulations, which it would otherwise get.
        return _choose(WIN_IN_A_SILENCE, memory, clean)
    if mood != "negative" and _reads(reads_as_a_win_a_cost_came_with, clean.lower(),
                                     repaired.lower()):
        # The same two halves the other way round - the win and what it costs ("we finally got the
        # keys and the place is a state", "we came into some money and now everyone wants it").
        # The cheer ("Lovely to hear. Enjoy it!") answers the first half and is deaf to the second,
        # and the good-news reader cannot be the one to stop it, because this file asks it later
        # and the new-thing reader reads a set of keys as a win on its own.
        return _choose(WIN_AND_A_COST, memory, clean)
    occasion = (reads_as_an_occasion(clean.lower())
                or (reads_as_an_occasion(repaired.lower()) if repaired != clean else None))
    if mood != "negative" and occasion:
        # "its my birthday on friday" is good news with a date on it, and the congratulations line
        # ("Brilliant. Really pleased for you.") reads oddly for it - you wish somebody a happy
        # birthday. Before the good-news branch, which is what a birth or an exam result wants,
        # and before the news-to-come line, which welcomes a wedding or a baby as a thing ahead.
        return _choose(_occasion_pool(occasion, clean), memory, clean)
    ahead_pool = _reads_value(_a_day_ahead, clean, repaired)
    if mood != "negative" and ahead_pool is not None:
        # "my holiday is next week" and "my exam is on monday" were nodded back ("Noted: your
        # holiday is next week"), which is the restatement STYLE.md rules out, and a dated
        # appointment was worse than nodded: "im due at the dentist on friday" wears the due-date
        # pattern in bot/compose/goodnews.py, which is there for a baby, and was congratulated -
        # "That's lovely news - and something to look forward to" - as was "im due in court on
        # friday" and "im due for my jab on monday". A line with a date on it and a tense thing in
        # it is a diary entry, so this sits above the news-to-come branch, and it needs one of its
        # own tone words, so a baby due in june is still good news.
        return _choose(ahead_pool, memory, clean)
    if mood != "negative" and _reads(reads_as_news_to_come, clean.lower(), repaired.lower()):
        # Still to come, so the reply looks forward and never asks how it went. A birthday said
        # with a figure ("my mum is 72 and she is 73 next month") is answered with the figure:
        # the pool above looks forward without saying which birthday, which hands the person
        # their own news back with the number taken out.
        birthday = _a_birthday_still_to_come(clean, memory)
        if birthday:
            return _choose(_the_birthday_said_back(birthday), memory, clean)
        return _choose(NEWS_TO_COME, memory, clean)
    if ack.a_limit_on_the_plan(clean):
        # A limit on the plan is answered with what the bot will do with it, whatever mood the
        # rest of the line is in: "she is 8 months pregnant and cant walk far" is not "Brilliant.
        # Thanks for telling me", which hears the pregnancy and drops the walk. Only a line that
        # is nothing but a limit gets this, so a month they have planned keeps its own reply.
        said_back = ack.a_limit_reply(text, memory)
        if said_back:
            return said_back
    if mood == "neutral" and _dreading(clean):
        # "im dreading monday", "not looking forward to the scan", "i cant face the phone call":
        # mild, and the two pools that could answer them are both wrong - the negative pool is for
        # a bad week and the floor says nothing.
        return _choose(A_DREAD, memory, clean)
    if mood == "neutral" and _wants_it_over(clean):
        return _choose(A_WANT_IT_OVER, memory, clean)
    if mood != "negative" and _reads_value(_looking_forward, clean, repaired):
        # A thing still to come said as a want rather than as news - "i cant wait for the
        # weekend", "roll on friday", "counting down to my holiday", "really looking forward to
        # it", "only 3 days till my holiday" - was at the composer's floor ("I'm listening - say
        # more if it helps"), which answers nothing at all, while the news-to-come pool is the
        # pool for a thing ahead and never asks how it went. Placed after the named events, so a
        # wedding, a baby and a holiday still get their own reading, and before the
        # congratulations, which would cheer a weekend as if it had happened.
        return _choose(NEWS_TO_COME, memory, clean)
    if mood == "neutral" and _reads(reads_as_good_news, clean.lower(), repaired.lower()):
        return _choose(_says_only_what_they_said(CONGRATS, clean),
                       memory, clean)  # a baby is not a fact to file away
    # A thing that has arrived - a rescue greyhound, a kitchen going in, a move - is news the
    # congrats pool cannot say anything about ("Good for you!" congratulates a sofa) and the nod
    # says nothing at all. It keeps its own question, about the thing that arrived. After the
    # congratulations, so a new job or a set of keys is still a win.
    arrived = goodnews.new_thing(clean.lower())
    if arrived and mood != "negative":
        return _choose(goodnews.new_thing_replies(arrived), memory, clean)

    # A regret ("we booked the holiday but now i regret it", "i wish i hadnt booked it") is not a
    # doubt to weigh and not a plan reported: the whole message is the regret, and every reading
    # below answers it with something that is not about it - the nod says nothing about it, and
    # the plan offers a first step for a thing they wish they had not started. It goes above them
    # and below the good news and the news of a thing that arrived, which are not regrets.
    # The repaired line is the second try, which is what carries the same regret typed with a
    # dropped apostrophe ("i shudnt have said anything") to the pool the standard spelling reaches.
    regretted = remark.regret_reply_for(clean, words, memory,
                                        understood.get("plain") or "")
    if regretted:
        return regretted
    idiom = PLAN_IDIOM.search(clean)
    if idiom:
        # "im going to die of embarrassment" is a feeling, and the plan ack answers the wrong
        # thing. A light line back, then the person says what happened.
        return _choose(IDIOM_SHY if "excit" not in idiom.group(0) else IDIOM_GLAD, memory, clean)
    if _plan_reported(clean, mood) and not ack.reads_as_a_trip(clean):
        if reads_as_a_change_of_medicine(clean):
            # "im going to skip my medication for a week" is a decision about a prescription, so
            # it is the one plan that is not blessed: the dose waits for the person who wrote it.
            # Above the done-things pool, because a medicine stopped last week is the same advice
            # and the same 111 line.
            whole = (PLAN_MEDICINE_SLOW_REPLY if PLAN_MEDICINE_SLOW.search(clean)
                     else PLAN_MEDICINE_REPLY)
            return _choose(whole, memory, clean)
        if any(phrase in clean for phrase in PLAN_DONE) and not PLAN_NOT_YET.search(clean):
            # The plan has already happened, so there is nothing to be told how it goes.
            return _choose(PLAN_DONE_ACK, memory, clean)
        # "ok ill book her in tomorrow" is a plan, not a fact. A trip or an occasion is not a
        # next step being reported ("i'm going to a wedding in september" has nothing to be told
        # how it goes yet), so it falls through to the store, which answers with the trip itself.
        return _choose(PLAN, memory, clean)
    promise = _a_promise_that_keeps_moving(clean)
    if promise is not None and mood != "positive":
        # A promise that keeps not happening has no impact word and nothing of theirs in the
        # way, so the grievance reader below could not see it and the line got "I'm listening".
        # It is read first: a promise with a word for the wear in it ("he keeps saying he will
        # sort it and it never happens") is still a promise.
        return _choose(promise, memory, clean)
    if mood != "positive" and _someone_else_minding(clean, words, _grievance_thread(memory)):
        if _grief_thread(memory):
            # "my partner wont talk about it" after a death is part of the grief, not a row about
            # somebody's manners: the last thing they need is "annoying".
            return _choose(GRIEF_AFTER, memory, clean)
        return _choose(GRIEVANCE, memory, clean)
    if mood == "neutral" and _sorry_for_asking(clean):
        # "Sorry to bother you" is manners, not a report: the stock line asks them to say more
        # when they have not said anything yet.
        return _choose(SORRY_FOR_ASKING, memory, clean)
    said = _thanks_then_said(clean)
    if _thanks_news_went_badly(clean):
        # Bad news behind a thanks. It used to fall through to the pools below, which read the
        # line as something new and answered the thanks instead: "thanks, its worse today" got
        # the echo and "thanks, still hurting" got "Got it". The outcome is the line, so the
        # pool that owns bad news answers it, and the person is asked the detail a card needs.
        return _choose(THANKS_NO_BETTER, memory, clean)
    if said:
        # A thanks and the outcome after it. The mood is read on the outcome, not on the whole line:
        # "thanks" in front of it hides the words that say which way it went, and "thanks, it's worse
        # today" was answered "Good. Thanks for letting me know."
        said_words = re.findall(r"[a-z']+", said)
        if THANKS_GOOD_AGAIN.search(said) or (
                not THANKS_WENT_BADLY.search(said) and _mood(said_words, said) != "negative"):
            return _choose(THANKS_THEN_SAID, memory, clean)
    if mood == "neutral" and (_thanks_with_more(clean) or _acknowledges_alone(clean)):
        # "That's good to know, thanks" is thanks with extra words, not a statement to file.
        return _choose(THANKS, memory, clean)
    if mood == "neutral" and (DITHER.search(clean) or DITHER.search(repaired or "")) \
            and HELP_SERVICE.search(clean):
        # A doubt pointed at a service you go to for help asks what to do about a body, so it is
        # the advisor's line, not a weighing: "im not sure whether to take him to the vets
        # tonight" wants the vet's number, and "not sure whether to go to a and e" is a person
        # deciding whether a body needs looking at (warm-feather on #1467). A pet's is the vet.
        if "vet" in clean or "vets" in clean or any(
                word in ANIMALS or word.rstrip("s") in ANIMALS for word in words):
            return VET_WHO
        return _choose(UNKNOWN_HEALTH, memory, clean)
    if mood == "neutral":
        # "i dont know what to do about my mum" names the person the doubt is about and nothing
        # else, so the open pool's "the part of it that won't move" points at a thing nobody
        # said. A friend asks about the person, which is the one question the line has already
        # made possible.
        about_a_person = _a_question_about_the_person(clean, memory)
        if about_a_person:
            return about_a_person
    free_time = _the_stretch_of_time(clean, memory)
    if free_time:
        return free_time
    if mood == "neutral" and _reads_as_dither(clean, repaired) and _weighs_a_choice(clean):
        # "im not sure whether to move in with her" is a decision the person has already put
        # down, so the echo ("I'll remember that") and the nod both answer it with nothing a
        # friend would say. It comes after the symptom, good-news and plan readings, which are
        # different kinds of line, and before the echo, which would otherwise file the decision
        # away as a fact. A doubt about health is the one that keeps the advisor: whether to
        # ring the doctor is not a question the bot weighs.
        if ((set(words) & HEALTH_WORDS and not HEALTH_MODIFIER.search(clean))
                or any(phrase in clean for phrase in CHECK_PHRASES)):
            return _choose(UNKNOWN_HEALTH, memory, clean)
        if DITHER_YES_NO.search(clean):
            return _choose(DITHER_DECIDE, memory, clean)
        if DITHER_OPEN.search(clean):
            return _choose(DITHER_OPEN_LINES, memory, clean)
        return _choose(DITHER_TWO_WAY_LINES, memory, clean)
    # A line with no way in - "i dont know what to do", "im stuck", "where do i start", "no idea
    # what to do first" - names nothing at all, so no reading above can use it and none of them
    # should: it reached the echo ("I'm listening - say more if it helps"), the nod ("Got it. Is
    # there anything you'd like a hand with?") or the search hedge, and there is nothing to look
    # up in a line that has not named anything. It sits here, after every reading that can find
    # a subject, so it only ever replaces a reply that answers nothing, and it asks the one
    # question that gets somewhere: about the trouble when the line above named one, and about
    # what is in the way when it named nothing.
    if mood == "neutral" and _run_out(clean) and not _in_a_care_thread(memory):
        return _choose(RUN_OUT_LINES, memory, clean)
    if mood == "neutral" and _only_the_stuck_phrase(clean) and not _in_a_care_thread(memory):
        # Never in a thread that safety, urgent, loss or grief answered: "i keep thinking about
        # ending it" then "i dont know where to start" is a person saying where the start is, and
        # "what have you tried so far" is the last question to ask them. The gentle pool the
        # fallback already had is the right answer there.
        if A_HELP_WORD.search(clean):
            # "i need help but i dont know what with" is an ask for a hand with the with taken
            # out, and the offer is the answer a friend gives: "of course - what are you stuck
            # on". A question about the part that will not move answers a person who has said
            # what they need least.
            return _choose(HAND, memory, clean)
        if _news_above(memory) or _a_subject_above(memory) or _a_bad_line_above(memory):
            return _choose(STUCK_AFTER_TROUBLE, memory, clean)
        # A bare stuck line is `bot/memory/stuck.py`'s: it carries the news above over, and where
        # it can it answers better than a question ("Tell me what has gone on, even roughly, and
        # I will help you work out the first step"). Read with its own regex, this file keeps its
        # answer by falling through, and keeps the forms it does not read - "i dont know how to
        # start" was the search hedge - and the run-out lines above.
        if not (stuck_line.STUCK.match(clean) or _a_start_ask(clean)):
            return _choose(DITHER_OPEN_LINES, memory, clean)
    # A line that is nothing but a number ("20 mins", "45 a month", "its about 5 miles", "forty
    # minutes each way") is half of a sum, and the sum is the reply: 45 a month is 540 a year, 40
    # minutes each way is 6 hours 40 a week. Today such a line is either filed away ("Got it - you
    # have 40 pounds left for food this week") or dropped in a stock line, and both say nothing
    # about the number the person just gave. It comes after every reading above, because a line
    # with a subject of its own ("i have 2000 saved and no idea what to do with it") is not a bare
    # number and keeps its own reply.
    #
    # A problem stated and left there ("i have a problem", "i got a problem", "problem",
    # "something is wrong", "something happened") is the same kind of line: it names nothing the
    # readings above can use, and it reaches the pools below as a thing done with the day or as a
    # fact to file away. Both say nothing about what the person just said - the intake form ("Got
    # it. Is there anything you'd like a hand with?"), the nod, the echo, and "Good to hear. What
    # was the best bit?" for "i have a problem i need help with" because "need" read as a past
    # tense. The offer is the answer a friend gives, and the question in it is the one that moves
    # the conversation on.
    if _a_problem_stated(clean, repaired):
        return _choose(HAND, memory, clean)
    amount = quantity.reply_for(clean, memory)
    if amount:
        return amount
    # A name that came from somebody ("my son is called after me", "hes named after his grandad"):
    # no pool above reads it, and the store's read-back was all these lines got. It is a whole-line
    # shape of its own, so it costs nothing to read here.
    named_after = _named_after_reply(clean, memory)
    if named_after:
        return named_after
    if mood == "neutral":
        # Before the echo and the nod: something hard said about themselves ("i feel like im not
        # doing enough", "i still dont know what i want to do") is not a fact to file away, and
        # saying it back ("noted: you feel like you're not doing enough as a mum") is not an
        # answer to it either. The pool names the thing and asks one question back.
        own = _own_feeling(clean)
        if own:
            return _choose(own, memory, clean)
        # A knock the person gave themselves ("i hit my thumb with a hammer"). It comes before
        # every pool below, because a sore thumb is not a plan, an arrangement or a small thing
        # done, and the receipt it used to get ("Got it. Is there anything you'd like a hand
        # with?") could have come before any message at all.
        if _a_knock_on_oneself(clean):
            return _choose(KNOCKED, memory, clean)
        if _a_knock_into_a_thing(clean):
            return _choose(WALKED_INTO_POOL, memory, clean)
        # A fall or something sharp underfoot, with no card on it ("my baby rolled off the bed",
        # "i stepped on a nail in the garden", "i got glass in my foot"). It sits with the knocks
        # because it is the same thing - something landing on a person - and, like them, it has
        # to come before the echo and the pleasantry, which filed "i got glass in my foot" back
        # as "Noted: you got glass in your foot." and cheered the rest ("Nice one. How did the
        # rest of it go?"). The question is about how bad it is, because what to do next depends
        # on that and the bot cannot see it.
        if _a_mishap(clean, words):
            return _choose(MISHAP_BACK, memory, clean)
        # Someone who can call them in wants a word (understood["summons"]). It comes before the
        # echo: "Noted: your sons teacher wants a word" gives the person nothing to do, and
        # every one of these lines was answered that way.
        summons = understood.get("summons")
        if summons:
            return _choose(_summons_pool(summons, clean), memory, clean)
        # Something they mean to do ("im thinking of going back to college", "i want to start
        # saving") - a plan, not a fault. The reply is about the first step, which is the part
        # people get stuck on (bot/compose/remark.py). It comes before the echo: a plan said
        # back ("Noted: you want to sort out the loft this weekend") names the thing and still
        # leaves them nowhere to start, and gray-cypress measured the echo claiming these
        # lines. It stays after trouble, because a plan that is also a fault is the fault.
        # An activity the person is into ("im into climbing", "ive got into yoga") is a
        # statement about themselves and nothing else, and every one of these lines got the
        # stocking pool. It comes before the plan reader because "im getting into gardening" is
        # both shapes and the reading names the activity, which is the part a friend answers
        # (bot/compose/remark.py). Whose interest it is, and whether the word "into" means an
        # activity rather than a person or a fight, is already decided there.
        taken = remark.interest_reply_for(understood.get("taking_up"), memory)
        if taken:
            return taken
        planned = remark.reply_for(clean, words, memory, understood.get("topics") or ())
        if planned:
            return planned
        # Something the person has arranged ("i booked flights to spain", "i booked a smear
        # test"). It is not a plan - it is done - so it fell through to the nod or to the echo,
        # and neither says anything about it. It comes before _thing_done_scan and the echo,
        # because the arrangement is the news here.
        arranged = remark.arranged_reply_for(clean, words, memory)
        if arranged:
            return arranged
        # A small thing done with the day, with nothing to add to it. It comes after the plan and
        # the arrangement, which say more than the pool can, and before the echo, which would only
        # say the line back.
        pool = _thing_done_pool(clean)
        if mood != "negative" and pool:
            return _choose(pool, memory, clean)
        # A detail about the thing we are on ("we live in a flat on the third floor", "i can put
        # away about 200 a month") is answered with the thing itself, and it comes before the
        # neutral pool, which would only nod: the stock line could have come before any message
        # at all. A report of a next step is a plan, so it keeps its own reply above.
        # A report of something that has happened ("the shop was shut", "the bus was late
        # again", "i started a new job") is not a question and not a plan, so it fell through to
        # the stock line. A friend answers a small setback with the nuisance it is, the same
        # setback again with "again", and something that has started with one question about how
        # it is going. It comes before the echo, because news is not a fact to file away:
        # "Noted: you started a new job on monday." says the line back and says nothing about it.
        reported = remark.report_reply_for(clean, words, memory)
        if reported:
            return reported
        # A habit said flatly ("i always leave things to the last minute", "i never finish
        # anything i start", "i keep interrupting my sister") is how somebody asks for help with
        # it: nobody tells you a pattern about themselves unless they want it to change. It
        # comes before the echo, because the line back - "Noted: you keep interrupting your
        # sister" - is the reply this file itself calls the coldest one, and `chat` stands down
        # on the same test, so the claim and the reply have to be in the same place.
        if not asking and reads_as_a_flat_habit(text, understood):
            return _choose(HABIT_REPLY, memory, clean)
        # A relationship said to be in trouble ("my marriage is on the rocks", "me and my
        # husband barely talk", "my mum and i dont get on") is not a plain fact to take an
        # interest in and not a fault to troubleshoot. It comes before the echo and before the
        # facts about their people, because both of those answer it as if the person had read
        # out a bus timetable: "Noted: things are bad with your wife."
        together = remark.the_two_of_them(clean, memory)
        if together:
            return together
        # A plain fact about one of their people ("my parents live in derby", "my daughter is
        # 4", "my sister is called meg") is what the store files, and the filing said back -
        # "Noted: your parents live in derby." - is the coldest reply in this file. A friend
        # takes an interest in the person in the fact. It comes before the echo for that
        # reason, and the shapes are whole lines, so a worry about the same person ("my mum is
        # 82 and keeps forgetting things") never reaches it.
        of_theirs = remark.their_people_reply_for(clean, words, memory)
        if of_theirs:
            return of_theirs
        # A place secured in something still to come ("i got an audition", "i got tickets for the
        # match"), read above the receipt: the store files the line and says it back ("Noted: you
        # got tickets for the match"), which answers a thing that has not happened yet with the
        # person's own words. It is above the echo and below the people, and the day question
        # below it stands down for the same shape.
        got_ahead = _a_thing_got_ahead(clean)
        if got_ahead:
            return _choose(got_ahead, memory, clean)
        # How one of their people was *with them* is not a fact about that person: "my mum was
        # funny with me" was filed as a trait ("Noted: your mum was funny with you") and "he
        # snapped at me this morning" got a receipt. A friend asks what set them off
        # (bot/compose/remark.py).
        going_on = remark.their_mood_going_on_reply_for(clean, memory)
        if going_on:
            return going_on
        mooded = remark.their_mood_with_you_reply_for(clean, words, memory)
        if mooded:
            return mooded
        # A thing, or a pile of them, wearing them down ("this spreadsheet is killing me", "i
        # have so much marking to do"). Nothing is broken and nobody else is in the line, so it
        # fell all the way to a stock line that could have answered any message at all. It comes
        # before the echo, which for these says the complaint back and adds nothing.
        wear = worn.reads_as_worn(clean, words, repaired)
        if wear:
            return _choose(worn.pool(wear), memory, clean)
        # A stated dislike with nothing under it to object to ("i hate presenting", "i cant stand
        # cats"). It comes before the echo, which for these is the coldest line in the file.
        disliked = the_dislike_ask(clean, memory)
        if disliked:
            return disliked
        said_back = ack.reply(text, memory)
        # A want somebody the person looks after has ("my son wants a tattoo", "my dad wants a
        # scooter at 78"). Whose the wanting is decides the reply: the person is asking on their
        # behalf, so it gets the first step of that want. It stands immediately above the filing
        # because the filing is the whole fault - "Noted: your son wants a tattoo." says the want
        # back and leaves them nowhere to start - and the filing is all it takes: the store's own
        # shaped answers ("So you are thinking about a horse. Who would look after it in the
        # day?") are better than anything this pool can say and keep their turn. A filing with a
        # guessed feeling on it ("Your son is 16 and wants a motorbike. That is a lot to carry on
        # top of how you feel.") counts as a filing - the mood is invented for a line that never
        # said one, and `remark.a_want_said_back` is what decides which of the two it is.
        if remark.a_want_said_back(said_back, clean):
            theirs = remark.dependant_want_reply_for(clean, words, memory)
            if theirs:
                return theirs
        told = _a_day_told_instead_of_the_receipt(said_back, clean, memory)
        if told:
            return told
        if said_back:
            return said_back
    if mood == "neutral":
        # A plain statement that gave the memory store something is answered with the thing
        # itself ("My sister is called Meg" -> "Your sister is called Meg — noted."), which
        # beats a stock line. News and bad news keep their own replies, so a rescue dog is still
        # "That's great news" and an argument about money is still "That sounds rough".
        of_theirs = remark.their_people_reply_for(clean, words, memory)
        if of_theirs:
            return of_theirs
        # A clock time somebody has to be somewhere by ("i need to be at work for 8", "i have a
        # train at 7", "my shift starts at 7"). It comes before the echo, because the store files
        # the time and says it back - "Noted: you have a train at 7." - which is the coldest
        # version of the one thing in the line worth working back from.
        if _the_morning_has_a_clock(clean):
            said = _the_time_said(clean)
            return _choose(_the_clock_pool(said.group(1) if said else ""), memory, clean)
        said_back = ack.reply(text, memory)
        if remark.a_want_said_back(said_back, clean):
            theirs = remark.dependant_want_reply_for(clean, words, memory)
            if theirs:
                return theirs
        told = _a_day_told_instead_of_the_receipt(said_back, clean, memory)
        if told:
            return told
        if said_back:
            return said_back
        # Something of theirs has gone wrong ("my washing machine is leaking", "my knee has been
        # aching for a week"). The trouble itself is the reply: what it is doing, when it
        # started, what they have tried (bot/compose/trouble.py). It comes after the echo,
        # because a line the memory store can say back is more specific still, and it never
        # fires on a question, a plea for tips, or anything about another person - an emergency
        # about a husband or a baby is not a fault to troubleshoot.
        shape = trouble.reads_as_trouble(clean, words, repaired)
        if shape:
            said = _choose(trouble.pool(shape, clean, memory), memory, clean)
            if said:
                return said
    if mood == "negative":
        # The word that made the mood negative is usually the pain word itself ("my back hurts",
        # "my shoulder is killing me"), so an ache was answered with the gentle pool: "That
        # sounds rough. If you want, I can help you think through what to do next" reads as if
        # the bot had misheard a person saying where it hurts. A body part that hurts is the
        # trouble module's question whatever the mood of the line, on the same terms the symptom
        # branch above uses, so a caught bug ("ive had a cough for three weeks now") keeps its
        # advice: the trouble question would ignore how long they have had it. A line that also
        # says the person is crying or frightened is a feeling line, not a fault to troubleshoot
        # ("my eyes are sore from crying all afternoon"): FRIGHTENED is the reading the file
        # already uses for that, so the gentle pool keeps it.
        shape = trouble.reads_as_trouble(clean, words, repaired)
        if shape == "sore" and not _CAUGHT.search(clean) and not FRIGHTENED.search(clean):
            said = _choose(trouble.pool(shape, clean, memory), memory, clean)
            if said:
                return said
    # A result still in the post ("i dont think i passed", "im waiting to hear about the job",
    # "i havent heard back yet") is not a thing to nod at, and the flat "Got it" is what is left
    # otherwise. The one useful thing a friend says is when, because that is the part the person
    # cannot move and can tell you. Placed after the echo and the trouble question and before
    # the neutral pool, so it can only ever replace a nod, and a line that already says when
    # gets the waiting itself instead of being asked again.
    landed = None
    if not (_in_a_loss_thread(memory) or _grief_thread(memory)):
        landed = _the_news_landed(clean)
    if landed == "bad":
        return _choose(LANDED_BAD, memory, clean)
    if landed == "good":
        return _choose(_says_only_what_they_said(CONGRATS, clean), memory, clean)
    if landed == "landed":
        return _choose(PENDING_LANDED, memory, clean)
    # "Anything I should know about the job" carries the same four words as "i should know by
    # friday", and the wait reading below took them: a person about to accept an offer was asked
    # when they would hear back. The ask is read in `toknow.py`, which also hands it to a card the
    # knowledge base holds when there is one. None is "not this ask", "" is this ask with nothing
    # to add - and then the line goes on past the wait, because a question about a thing is not
    # news in the post either way.
    from .toknow import ask_about_what_to_look_out_for as _ask_about

    answered = _ask_about(clean, memory)
    if answered:
        return answered
    if answered is None and _an_open_result(clean):
        if _a_time_in_it(clean):
            pool = PENDING_WAITING
        elif _a_guessed_result(clean):
            pool = PENDING_DOUBT
        else:
            pool = PENDING_WHEN
        return _choose(pool, memory, clean)
    if opens_with_hello and mood == "neutral":
        # Nothing in this file could answer the line, but it still opened with a hello
        # ("hi sorry, my phone was updating", "hey so im thinking of getting a dog"): saying
        # hello back is warmer than the neutral "got it", which is all that is left.
        # Only when the line carries no news of its own, though: a hello in front of bad news
        # ("hi, i think my waters broke", "hi, my waters broke an hour ago") was losing the news
        # to "Hi! What's up?", and the pool below already has the answer for it. The hello adds
        # nothing to a line that says something; it only decides the reply when it is all there
        # is, which `greeting_only` above has already had its turn at.
        return _choose(GREETING, memory, clean)
    if _reads_as_a_bad_stretch(clean):
        return _choose(BAD_STRETCH_REPLIES, memory, clean)
    # The same clothes question said as a statement rather than an ask - "im going to a do at the
    # golf club and i have no idea what to wear" is not read as asking, so it never reached the
    # arm above and the pools below only have a hedge for it, while the rule that decides clothes
    # is the same rule. It sits here, under every reading that could have something to say about
    # what the line is about, because all that is left below is the hedge and the neutral nod.
    if _says_there_is_nothing_to_wear(clean, repaired, text):
        return _choose(NOTHING_TO_WEAR_REPLIES, memory, clean)
    if _a_wear_ask_about_a_day(clean, repaired, text):
        return _choose(_the_wear_pool_for_the_line(clean, repaired, text), memory, clean)
    # A follow-up that names a new thing for the question before it ("and in the freezer too",
    # "what about the shed") is a question about that thing, even when it is said without one: it
    # has an answer somewhere or it has none. When answers has refused it - there is no entry for
    # the freezer - the honest hedge is what fits, because "Thanks for telling me - I'm here if
    # you want to dig into any of that" hears the line as something said about the person and
    # leaves the freezer where it was. Only a neutral line gets here: a follow-up that carries
    # trouble of its own ("and my neck hurts too") is answered above.
    # A correction is not that question: "sorry, i meant next august" takes something back, and
    # the search hedge would answer it as if they had asked about next august (see facts'
    # correction openers, which is where a correction is read).
    if mood == "neutral" and not _A_CORRECTION.match(clean) and swap.rewritten(clean, memory):
        return _choose(UNKNOWN, memory, clean)
    # "my landlord is a joke", "my job is a nightmare", "the buses are a joke round here": a
    # verdict on a thing of theirs is a complaint. The one thing it must not get is the punchline
    # pool ("joke" is in the line) or the note-back that files the verdict as a fact ("Noted: your
    # job is a nightmare."). It sits low, above only the last pools, because a verdict says how
    # the person feels about a thing they named, and a thing with an answer of its own keeps it:
    # "my boiler is a nightmare" is still the plumber's, "my rota is a nightmare" still the rota's.
    if verdicts_a_thing(clean):
        return _choose(NEGATIVE, memory, clean)
    # A body state and nothing else - "im cold", "im starving", "my hands are freezing" - is a
    # line no module has anything to say about, so it reached the neutral nod. It comes last,
    # after every reading above that might have something better: a line that names a fault or
    # a result is not this, and a cold room with the heating broken is still the trouble one.
    state = _body_state(clean)
    if not state:
        # A state typed with a syllable dropped is repaired by the reading ("im starvin",
        # "im nakerd", "im sare"), and the pools only know the word it repairs to. The typed
        # line is asked first, so nothing whose own spelling is a state moves; only a line
        # whose repair is the whole state reaches the pools.
        repaired = understood.get("plain") or ""
        if repaired and repaired != clean:
            state = _body_state(repaired)
    if state:
        return _choose(BODY_POOLS[state], memory, clean)
    # The same thing done, for a line whose mood is not neutral: "hired" and "sorted" are
    # good-news cues, so "hired a van" was read as a win and cheered with "Lovely to hear. Enjoy
    # it!" - a van is borrowed for the afternoon, not a thing to enjoy. Only the cheer is
    # replaced here; a neutral line has already had its turn above, after the plan and the
    # arrangement. A mood word on a thing of theirs is still the thing's, so it keeps the pool
    # below.
    pool = _thing_done_pool(clean)
    if mood != "negative" and pool and not _a_things_state(memory, clean):
        return _choose(pool, memory, clean)
    if mood == "negative" and _a_things_state(memory, clean):
        # The last pool of all: a mood word on a thing is still the thing's, not the person's.
        return _choose(A_THING_LOOKS_SAD, memory, clean)
    # The same doubt as "am i too old", said as a fact about themselves: "i want to start
    # running" / "im 44 and quite unfit" reached the neutral nod, and "Got it. Is there anything
    # you'd like a hand with?" answers the fact instead of the doubt - it is the line that fits
    # any message. The age and the fitness are what people offer as the reason not to start, so
    # they get the doubt answered and the plan kept small. It sits here, above nothing but the
    # neutral pool, so every reading with something of its own has already had its turn - and it
    # keeps out of a body thread, where "im 34 and my knee gives way when i run" is a knee
    # question.
    if (A_BIT_PAST_IT.search(clean) and _a_thing_they_started(memory)
            and not _hedged_recently(memory) and not _thread_is_about_the_body(memory)):
        return _choose(NOT_TOO_OLD if _names_their_age(clean) else NOT_FIT_ENOUGH, memory, clean)
    # (The flat habit is answered above the echo - see `reads_as_a_flat_habit`.)
    # A goodbye with the person's own trouble set against it ("im off but i feel rough", "got to
    # go but i keep waking up") is not a goodbye while something answers the trouble, and this
    # file is the last place that could. Where nothing above had a word for it, all that is left
    # is the intake form ("Got it. Is there anything you'd like a hand with?"), which files a
    # goodbye back as a fact and gives the person nothing; letting them go warmly is the smaller
    # thing to say, and the trouble is asked about on the next line if they come back.
    if leaving.reads_as_a_leave_with_a_trouble_in_it(clean, words):
        bye = leaving.pool(clean, words, trouble_blocks=False, memory=memory)
        if bye:
            return _choose(bye, memory, clean)
    # The last thing before the intake form. A cost somebody else has put on the person - "ive
    # been asked to be a bridesmaid but its 800 quid", "my mate wants 500 quid for the holiday",
    # "my sister wants me to spend 1000 on her wedding" - was answered "Got it. Is there anything
    # you'd like a hand with?" or with the line said back, which is the one thing a person
    # weighing up a bill does not need. The pool is here rather than higher up because every
    # reading with something of its own has already had its turn: it can only replace a reply
    # that answers nothing.
    if _a_cost_somebody_asks(clean):
        return _choose(A_COST_SOMEBODY_ASKS, memory, clean)
    # The last placeholder of all, and the commonest way a person asks for a hand: "i dont know
    # what to do", "i dont know what to do anymore", "i dont know what to do about it". The
    # three lines this file used to answer it with - "Thanks for telling me - I'm here if you
    # want to dig into any of that", "Got it. Is there anything you'd like a hand with?" and
    # "I'm listening - say more if it helps" - fit any message, and each one answers a person
    # asking for direction by handing the turn back. It sits here, above nothing but the mood
    # pool, because a line with a subject has already had its own answer; what is left is the
    # bare ask, and the bare ask has a pool already (BARE_PICK_DO). A thread with advice in it is
    # the exception: "the boiler is broken" then "i dont know what to do" is the next step of
    # that advice, and the reply that carries on with it is already proposed.
    lost = the_lost_ask_reply(memory, clean, repaired)
    if lost:
        return lost
    # A thing that came out wrong, without the thing being named ("it came out grey in the
    # middle"): every card that answers a bake or a roast needs the word for what it was, so a
    # line that only reports the result has nothing to look up, and it fell to the question about
    # the day or to being said back. The one thing a friend asks is what happened.
    if RESULT_WENT_WRONG.search(clean):
        return _choose(A_THING_CAME_OUT_WRONG, memory, clean)
    # What is true of them, said as a fact ("im self employed", "i was on a diet last year"): the
    # cheer above asks about a day nobody described and the intake form offers help with a task
    # nobody mentioned, so the question is about the thing they have just said about themselves.
    if PLAN_THAT_FELL_THROUGH.search(clean):
        return _choose(A_PLAN_THAT_FELL_THROUGH, memory, clean)
    # A state said with good news in it is the news ("im engaged", "im pregnant", "i feel like im
    # pregnant"): "Does that suit you, or would you change it?" is a question for a state somebody
    # might want to shift, and it took the congratulations off all three. The mood the line is
    # already read with is the test, so no word is listed here and a state that is only a state
    # ("im self employed") still gets its question.
    state = None if RESULT_WENT_WRONG.search(clean) or mood == "positive" else _a_state_of_theirs(clean)
    if state:
        return _choose(A_STATE_PAST if state == "then" else A_STATE_NOW, memory, clean)
    # A day the person has just said went badly ("we had a row last night", "were gutted when it
    # happened"): the day pool below is a cheer, and with the cheer taken away these reached the
    # floor. One question about the day is what a friend says, and nothing above wants the line.
    if _a_bad_time_told(clean, memory):
        return _choose(A_BAD_TIME_TOLD, memory, clean)
    # The same shape where the word for the trouble is a loose one ("we had a strange day at
    # work", "it was a grim afternoon"): the cheer is wrong and the floor answers nothing, so the
    # question is asked without a presumption in it.
    if _a_day_asked_without_a_cheer(clean, memory):
        return _choose(A_DAY_ASKED_PLAIN, memory, clean)
    # A line that is only a name ("my kids are called jack and emma", "my mother-in-law is called
    # june"): the cheer below asks about a day nobody described, and the intake form offers help
    # with a task nobody mentioned. The names are said back with one question about the people.
    named = _a_name_told_reply(clean, memory)
    if named:
        return named
    # A small account of the day, said with nothing on the end of it ("work was ok today", "i got
    # my hair cut", "we had a takeaway last night"): every reading above is for a thing with a
    # shape of its own, so these reached the intake form ("Got it. Is there anything you'd like a
    # hand with?"), which offers help with a task nobody mentioned and could have come before any
    # message at all. A friend asks about the day. It is the last reading before that pool, so it
    # can only ever replace a reply that answers nothing.
    # Advice somebody else gave the person is a plan with a name on it, and nothing in it has
    # happened yet: "my mate said i should try that new pizza place" was answered "How was it,
    # overall?" and "i was told to rest" got "Good to hear. What was the best bit?" - day pools
    # asking about a thing still to come. It sits beside the small day, as the last reading
    # before the intake form, so a line with a card of its own keeps it: "my wife wants me to
    # stop drinking" is the relationship answer's and "ive been told to lose weight" is the
    # weight card's. The reading is the understanding engine's own (`suggestion`).
    suggestion = understood.get("suggestion") if isinstance(understood, dict) else None
    if suggestion and not asking:
        who = str(suggestion.get("who") or "")
        if who:
            return _choose(tuple(line.format(who=who) for line in A_SUGGESTED_BY_SOMEONE),
                           memory, clean)
        return _choose(A_SUGGESTED, memory, clean)
    # A thing they did and are judging themselves for. Nothing above has a shape for it - it is
    # not a question, a plan, a symptom or a thing done about the house - so it reached the day
    # pool or the shrug, and "i did something stupid yesterday" was answered "Good to hear. What
    # was the best bit?", "i lied to my friend" "Sounds alright. Anything good in it?" and "i made
    # a mistake at work" "I'm listening - say more if it helps". A cheer at a confession is the
    # one reply a person does not forgive, and the shrug hands back the turn they were already
    # finding hard. The pool asks the only question worth asking.
    if _a_thing_they_regret(clean):
        return _choose(A_THING_THEY_REGRET, memory, clean)
    # The other half of the same reading: a line about what somebody close did to them is not a
    # day of their own that went fine.
    if _a_betrayal(clean):
        return _choose(A_BETRAYAL, memory, clean)
    # Somebody living in a care home ("my mum moved into a home last month", "my nan is in a home
    # too", "i feel guilty about not visiting my dad in the home"). It comes before the small day
    # and the echo, both of which answered these lines with something that could have been said to
    # anyone, and before the neutral pool for the same reason.
    care = _a_care_home_line(understood, memory)
    if care:
        return care
    # A form or a page that threw the person's work away ("my online application didnt save") is a
    # statement about a loss, and every pool below reads a line like that as a small account of the
    # day: a cleared checkout was answered "Sounds alright. Anything good in it?" and a lost
    # application "I'm listening - say more if it helps". The order that gets the work back is
    # known, so it is answered before the day pools - and nothing else takes its place, because
    # this can only answer a line that names a form and says the work went.
    wrecked = finding_out.the_wrecked_form_reply(clean)
    if wrecked:
        said = _choose(wrecked, memory, clean)
        if said:
            return said
    # The day is told over two lines, and every pool above reads one of them. "i had a lovely
    # day" then "we went to the beach" reached the flat pool ("Sounds alright. Anything good in
    # it?"), asking for the good bit of a good day the person was in the middle of describing, and
    # "work was mad today" then "i ended up staying till eight" was congratulated ("Good to hear.
    # What was the best bit?"). Where the turn before already said how the day was, the rest of it
    # is part of that day, so the pool is chosen from the day and not from the line alone.
    # A price the person stated is not a day they had. "my quote was 300", "my new sofa was 800"
    # and "i paid 60 for a haircut" were all read as a flat account of a day and cheered -
    # "Sounds alright. Anything good in it?", "Good to hear. What was the best bit?" - which
    # invents a feeling about a sum of money and asks what was good about a bill. A sum with no
    # second figure beside it is the one thing the bot cannot judge and can honestly say so, so the
    # answer is the one it already gives when somebody asks "is that a lot": the figure said back,
    # and the one other number that would settle it. The knowledge cards have all had their turn
    # above this line - "my boiler service cost 90" still gets the £60 to £120 card - so what is
    # left here is the sum of money with nothing behind it.
    sum_said = _a_sum_with_nothing_beside_it(clean, memory)
    if sum_said:
        return _choose([line.format(said=sum_said) for line in A_SUM_STATED], memory, clean)
    rest = _the_rest_of_the_day(clean, memory, mood)
    if rest is not None:
        return _choose(rest, memory, clean)
    # Something they have only been told about is not a day of theirs, and the day pool below
    # answered every one of these as an afternoon that went fine. It sits immediately before
    # that pool so it can only ever replace a line that would otherwise be congratulated.
    reported = _a_report_from_elsewhere(clean)
    if reported is not None:
        return _choose(reported, memory, clean)
    if mood == "neutral" and _a_small_day(clean, memory) and not _just_asked_about_the_day(memory):
        return _choose(A_SMALL_DAY, memory, clean)
    # The last thing before the neutral pool, and here for the same reason as the pool above: only
    # a reply that answers nothing can be replaced. An apology or a "never mind" names nothing, so
    # every reading with something of its own has already had its turn by now.
    if A_SORRY_ON_ITS_OWN.match((clean or "").strip()):
        return _choose(SORRY_ON_ITS_OWN, memory, clean)
    if A_DISMISSAL.match((clean or "").strip()):
        return _choose(NEVER_MIND, memory, clean)
    # A warm line that carries a detail the person never gave is a guess about their week, so the
    # positive pool is read through the line: "worth the wait" only where they said they waited.
    # A correction nobody here could file: "no it was my idea not the kids" after the bot asked
    # which of the party games the children had picked, "no the quiet is the best bit of it" after
    # an answer about the noise. The store files the corrections it can key ("no he is 7" is
    # "Got it - he is 7") and the echo says the rest back; what is left is a correction of
    # something neither could hold, and it reached the search hedge. The pool takes it and hands
    # the thread back. It sits with the other last readings, so the echo, the small day and every
    # pool with something of its own has already had its turn.
    if _takes_something_back(clean, memory):
        return _choose(A_CORRECTION_TAKEN, memory, clean)
    positive = _says_only_what_they_said(POSITIVE, clean)
    # A plain account of a thing with nothing on the end of it ("the tap has been running all
    # morning", "i think theyre underpaying me", "my shift starts at half 5") reached the intake
    # form, which offers help with a task nobody mentioned. The family of thing it names decides
    # one true thing to say instead. Last, so it can only replace a reply that answers nothing.
    if mood == "neutral":
        one_thing = onething.pool(clean, understood, memory)
        if one_thing:
            return _choose(one_thing, memory, clean)
        # A limit said in words the reading does not file ("nothing with a laugh track though")
        # arrived at the neutral receipt - the filler this shape least deserves, because the person
        # has just narrowed a list and is waiting for the next one. Here, last, so every reading
        # with something of its own keeps its turn.
        from . import limit as limit_line  # noqa: PLC0415 - no cycle at load
        narrowed = limit_line.a_limit_the_reading_missed(clean, memory)
        if narrowed:
            return narrowed
    # A pleasure gone out of everything is a low line and not a dull afternoon, so it does not
    # get the pool that offers a film and a book to cheer the day up: it gets the pool about the
    # flatness itself. Read here, last, so every reading with something of its own keeps its turn
    # ("my medication makes me sleepy" stays the medicine's), and read on the reading rather than
    # on the mood, because the mood is what the line says it is not.
    if reads_as_no_pleasure(clean):
        return _choose(PLEASURE_GONE_LINES, memory, clean)
    return _choose({"positive": positive, "negative": NEGATIVE, "neutral": NEUTRAL}[mood],
                   memory, clean)


# A thing the person did that they are judging themselves for: a confession, or the first half of
# one. The cues are a verdict the person passes on themselves ("i did something stupid", "i was
# horrible", "i feel awful about it") and the deeds that carry the blame with them ("i lied", "i
# lost my temper", "i let her down"), which are the sentences a person says when they are about to
# tell you the rest. Both are first person on purpose: "he lied to me" and "my husband cheated"
# are somebody else's doing and have their own readings above.
A_REGRET_DOING = re.compile(
    r"\bi\s+(?:have\s+|had\s+)?(?:did|done|said|been|was|am|feel|felt)\s+(?:something\s+)?"
    r"(?:really\s+|so\s+|very\s+|quite\s+|a bit\s+|pretty\s+|such\s+)?"
    r"(?:stupid|dumb|thick|silly|bad|awful|terrible|horrible|horrid|wrong|mean|nasty|rude|"
    r"selfish|unfair|pathetic|useless|worthless|guilty|ashamed|judged|daft|idiotic|moronic|"
    r"embarrassing|cringe|a cow|a bitch|a jerk)\b"
    # "i did something embarrassing" is the same confession as "i did something stupid" and was
    # answered "Good to hear. What was the best bit?" - the cheer pool took it for an afternoon
    # worth asking about. "silly" stays where it was, next to a noun, because "i did a silly
    # dance" and "i made a silly joke" are things to be pleased with.
    r"|\bsomething\s+(?:a\s+bit\s+|really\s+|so\s+|very\s+|quite\s+|pretty\s+|such\s+)?"
    r"(?:daft|idiotic|moronic|cringe|awkward)\b"
    # The same thing with the adjective in front of the noun instead of behind the "something":
    # "i did a stupid thing" and "i made a daft thing of it". Only a word for a deed counts
    # there, so "i made a silly joke" and "i did a silly dance" keep their cheer.
    r"|\b(?:did|done|made|make|said)\s+a\s+(?:really\s+|so\s+|very\s+|quite\s+|right\s+|"
    r"real\s+|proper\s+|bit\s+of\s+a\s+)?(?:stupid|daft|dumb|thick|silly|idiotic|moronic|"
    r"embarrassing|cringe|awful|terrible|bad)\s+(?:thing|things|stuff|job)\b"
    r"|\bi\s+(?:have\s+|had\s+)?(?:lied|cheated|stole|shouted|lost\s+my\s+temper|"
    r"wasted|ruined|messed\s+up|screwed\s+up|cocked\s+up|botched|betrayed|snapped)\b"
    # "i cocked up at work", "i put my foot in it", "i made a pig's ear of it": the same
    # confession said with a word nothing had read, so a person who had just told the bot they
    # had made a mess of something at work was answered "Nice one. How did the rest of it go?"
    # - a cheer at a confession, which is the one reply a person does not forgive.
    r"|\b(?:cocked|balls(?:ed)?|buggered|botched)\s+(?:it|things?|that)?\s*up\b"
    r"|\bput\s+my\s+(?:foot|feet)\s+in\s+it\b"
    r"|\bmade\s+a\s+(?:pig'?s?\s+ear|hash)\s+of\b"
    r"|\bi\s+(?:have\s+|had\s+)?(?:made|make)\s+(?:a\s+|one\s+)?(?:huge\s+|big\s+|silly\s+|"
    r"stupid\s+|terrible\s+|awful\s+|bad\s+|daft\s+|dumb\s+|thick\s+)?(?:mistake|error)\b"
    # Chat-speak drops the pronoun, the way "booked the hotel last night" does: "made a stupid
    # mistake today" has the shape of an evening worth asking about and got "Nice - how did it
    # go?". Every word in this arm is a past tense, so a line that opens on one is a report of
    # something done and not an instruction.
    r"|^\s*(?:i\s+)?(?:made|did)\s+(?:a\s+|an\s+|some\s+|the\s+)?(?:\w+\s+){0,2}?"
    r"(?:mistake|error|howler|blunder)\b"
    r"|\bi\s+(?:have\s+|had\s+)?let\s+(?:him|her|them|everyone|everybody|my\s+\w+|"
    r"someone|somebody)\s+down\b"
    r"|\bi\s+(?:really\s+)?(?:regret)\b"
    # "i shouldnt have said that" is the confession; "i shouldnt have another biscuit" is the
    # next thing on the plate and nothing to do with what happened, so this arm reads the deed
    # rather than the phrase.
    r"|\bi\s+shouldnt\s+have\s+(?:said|done|told|lied|shouted|yelled|snapped|eaten|drunk|"
    r"bought|spent|sent|texted|signed|answered|opened|posted|shared|taken|stayed|called|"
    r"let|been|gone)\b"
    r"|\bi\s+should\s+not\s+have\s+(?:said|done|told|lied|shouted|yelled|snapped|eaten|drunk|"
    r"bought|spent|sent|texted|signed|answered|opened|posted|shared|taken|stayed|called|"
    r"let|been|gone)\b")
# What turns the same words into something else: a question about what to do (the advice pools
# answer it), a plan ("i shouldnt have another biscuit" is about to come, not a confession), and
# a line about what happens now rather than what happened.
NOT_A_REGRET = re.compile(
    r"\?|^(?:can|could|should|would|will|do|does|did|is|are|was|were|what|how|why|when|where|"
    r"who|which|any)\b|"
    r"\b(?:how\s+(?:do|can|should)|what\s+should|should\s+i|shall\s+i|do\s+i|can\s+i|"
    r"tomorrow|next\s+(?:time|week)|from\s+now\s+on|in\s+future|"
    r"want\s+to|wanna|gonna|going\s+to|i\s+will|i'?ll|plan(?:ning)?\s+to|"
    # "can my employer stop my pay if i make a mistake" is a rule about the world with the
    # person's mistake in a subordinate clause, and "if i" is the shape that hypothetical takes.
    r"(?:if|unless|whether)\s+i)\b")
# "i snapped a photo at the wedding" is the camera and "i let my hair down at the party" is the
# good time: both carry a word from the list above and neither is a thing to be sorry for.
SNAPPED_A_PHOTO = re.compile(
    r"\bsnapped\s+(?:a|another|some|two|three)\s+"
    r"(?:photo|photos|pic|pics|picture|pictures|selfie|shot|shots)\b"
    r"|\blet\s+(?:my|his|her|their|our)\s+(?:hair|guard)\s+down\b"
    r"|\blet\s+off\s+steam\b")


# A mistake with a job named after it is a problem to fix, not a confession: "i made a mistake on
# my tax return", "i messed up the booking", "i made a mistake in the recipe" want the form filled
# in again, and "you don't have to dress it up for me" is sympathy they did not ask for. The
# mistake with nobody and no job after it ("i made a mistake", "i made a mistake at work") is
# still the confession the pool is for, and so is one with a person after it ("i made a mistake
# with my mate"), because that is somebody they think they have hurt.
A_MISTAKE = re.compile(r"\b(?:mistake|error|messed\s+(?:it\s+)?up|screwed\s+(?:it\s+)?up)\b")
THE_JOB_NAMED = re.compile(
    r"\b(?:mistake|error|messed\s+(?:it\s+)?up|screwed\s+(?:it\s+)?up)\b[^.]{0,24}?"
    r"\b(?:on|in|with|at|to)?\s*(?:my|the|our|a|an)\s+([a-z]+)")
NOT_A_JOB_BUT_A_PERSON = frozenset("""
    mum mom mummy dad daddy mate mates friend friends son daughter wife husband partner fiance
    boss team kid kids child colleague workmate sister brother nana gran granny nan neighbour
    neighbor someone somebody him her them everyone everybody people lass lad girl boy man woman
""".split())


# Who did it, when the line says: the person who lied, cheated or hid money, read on its own
# because "my husband has been lying to me" never says "found out" and "turns out he cheated"
# names nobody at all.
WHO_DID_IT = re.compile(
    r"\b(?:s?he|they|my (?:partner|husband|wife|boyfriend|girlfriend|fianc\w*|ex|mate|friend|"
    r"brother|sister|son|daughter|mum|dad|mother|father|boss|landlord|flatmate|housemate))\b")
# The wrong itself, as people say it. Every one is a thing done to the person by somebody close,
# so none of them belongs to a good day out and none is another person's bad luck. A lie, a cheat
# or a theft on its own says nothing about who it was done to: "he cheated at cards", "she cheated
# in the exam", "he lied about the film times", "he cheated death" are all things people say with
# nobody wronged, and the pool would be consoling somebody for a harm nobody did. So the words
# that can be about a thing are in A_WRONG_SAID and have to be aimed, and the ones that cannot
# ("an affair", "texting his ex") are read on their own.
A_WRONG_PLAIN = re.compile(
    r"\b(?:gambl\w*|affair|seeing someone|texting (?:his|her|their) ex|"
    r"back with (?:his|her|their) ex|drinking again|on the (?:booze|drugs) again|using again|"
    r"owed? (?:me|us) money|gone behind my back|kept it from me|been unfaithful|"
    r"cheat(?:ing|ed) on (?:me|us)|slept with (?:someone|somebody|my)|sent pictures)\b")
A_WRONG_SAID = re.compile(
    r"\b(?:ly(?:ing|ed)|lied|lies|cheat\w*|hiding|hidden|hides|stole|stolen|stealing)\b")
# What makes a lie or a cheat aimed at the person rather than at a thing: it is said to them
# ("lied to me", "cheated on me"), it is about their own ("about my cooking"), or it is about
# money, which in a household is the person's own.
A_WRONG_AIMED = re.compile(
    r"\s+(?:to|at|with|on)\s+(?:me|us)\b|\babout\s+(?:\w+\s+){0,2}(?:me|my|us|our|mine|ours)\b"
    r"|\s+(?:money|his wages|her wages|the savings|the rent|the bills)\b"
    r"|\s+(?:it\s+)?from\s+(?:me|us)\b")
# A complement that names a thing the wrong was about: a score, a time, a test, an exam, a game,
# a price. Nothing here is a harm done to the person.
A_WRONG_ABOUT_A_THING = re.compile(
    r"\s+(?:to|at|in|on|over|about|with|for)\s+\S"
    r"|\s+(?:the|a|an|his|her|their|its)\s+\S")
# The news that it was found out. A lie with nothing said about what it was about is the shape
# this pool answers only when the line also says it came to light: "i found out hes been lying",
# "turns out he cheated". Without that, "hes been lying" alone has no wrong named.
FOUND_IT_OUT = re.compile(
    r"\b(?:found|find|turned|turn)\s+(?:it\s+)?out\b|\b(?:turns|turned)\s+out\b"
    r"|\b(?:just\s+)?(?:heard|learned|learnt|discovered|found)\b")
FOUND_OUT = re.compile(
    r"\b(?:found|find|turned|turn) (?:it )?out\b|\b(?:turns|turned) out\b|"
    r"\b(?:just )?(?:heard|learned|learnt|discovered|found)\b")


def _a_betrayal(clean):
    """True when the line reports that somebody close lied, cheated or hid something from them.

    "i found out hes been lying" and "turns out hes been texting his ex" are the same news, and so
    is "my husband has been lying to me", which says nothing about finding out: the reading is the
    wrong done by a person of theirs, and everything else here - the day pool, the cheer, the
    receipt that says it back - is a reply to another kind of line.
    """
    text = " ".join(str(clean or "").lower().split())
    if not text or len(text.split()) > 22:
        return False
    wrong = A_WRONG_PLAIN.search(text)
    if not wrong:
        wrong = A_WRONG_SAID.search(text)
        if not wrong:
            return False
        # A lie or a cheat about a thing is not a wrong done to the person: "he lied about the film
        # times", "she cheated in the exam", "he cheated at cards", "my son lied about his
        # homework". It is one when it is aimed at them, or when nothing says what it was about
        # and the line has just found it out.
        if not A_WRONG_AIMED.search(text):
            if A_WRONG_ABOUT_A_THING.match(text[wrong.end():]):
                return False
            if not FOUND_IT_OUT.search(text):
                return False
    if not WHO_DID_IT.search(text[:wrong.start()]) and not FOUND_OUT.search(text[:wrong.start()]):
        return False
    # A wrong aimed at somebody else is their story, not this one: "my mate lied to his boss" and
    # "she stole money from her mum" are news about other people, and the pool would be consoling
    # the person for a thing that was not done to them. The wrong has to be said of them - "to
    # me", "on me" - or said of nobody at all, which is how a lie or an affair is told.
    after = text[wrong.end():]
    if re.search(r"\b(?:to|with|from|on|at)\s+(?!me\b|us\b)"
                 r"(?:his|her|their|my|the|a|an|some)\b", after):
        return False
    if HARM_ON_ME.search(text) and not WHO_DID_IT.search(text):
        return False
    return True


def _a_thing_they_regret(clean):
    """True when the line tells the bot about something the person did and is sorry for."""
    text = " ".join(str(clean or "").lower().split())
    if not text or len(text.split()) > 20:
        return False
    if not A_REGRET_DOING.search(text):
        return False
    if NOT_A_REGRET.search(text) or SNAPPED_A_PHOTO.search(text):
        return False
    job = THE_JOB_NAMED.search(text) if A_MISTAKE.search(text) else None
    if job and job.group(1) not in NOT_A_JOB_BUT_A_PERSON:
        return False
    if HARM_NAMED.search(text) or HARM_ON_ME.search(text):
        return False
    return True


# The day it happened on: a marker of a time already gone.
DAY_PAST = re.compile(
    r"\b(?:today|tonight|last night|yesterday|this morning|this afternoon|this evening|"
    r"at the weekend|over the weekend|this weekend|last weekend|all day|all morning|"
    r"the other day|earlier)\b")
# Whose day it was: the person's own, or the plain "it" of "work was ok today".
A_DAY_SUBJECT = re.compile(
    r"\b(?:i|i'm|im|ive|i've|we|we're|weve|we've|my|our|it|work|school|the weather|the day)\b")
# A past tense, read off the form of the word rather than off a list of what a person might
# mention: every one of these is a thing that has already happened, and a line that reaches this
# far has already been read for trouble, a fault, a plan and a body.
PAST_DOING = re.compile(
    r"\b(?:had|got|saw|was|were|went|did|made|took|met|ate|drank|bought|brought|read|played|"
    r"watched|walked|cooked|cleaned|painted|cut|sorted|finished|started|spent|sat|ran|came|left|"
    r"gave|found|booked|visited|helped|learned|learnt|worked|slept|drove|caught|wore|won|felt|"
    r"heard|told|said|sold|paid|sent|kept|put|let|set|fell|held|stood|thought|knew|began|broke|"
    r"spoke|rang|sang|wrote|built|swam|saw|ran)"
    # A word ending in "ed" is a doing, unless it is a thing or a colour: "the skin around it is
    # hot and red" is a symptom, and "red" read as a past doing made the small-day pool answer an
    # infected cut with "Sounds alright. Anything good in it?". The three words excluded here are
    # nouns, so the past doings of three letters - fed, led, wed, bled - are still readings of a
    # day, which cutting the word down to `\w{2,}ed` also dropped.
    r"\b|\b(?:(?!red\b|bed\b|shed\b|"
    # The words that end in "ed" and are not a thing that happened. "i need help with my
    # daughters birthday" was read as an account of a day - "need" is the only verb in it and it
    # ends in "ed" - and answered "Nice one. How did the rest of it go?"; a need is a thing they
    # want now, not a day behind them, and neither is a feed, a bleed or a speed.
    r"need\b|feed\b|bleed\b|speed\b|weed\b|seed\b|breed\b|proceed\b|succeed\b|exceed\b|"
    r"indeed\b|hundred\b|greed\b|creed\b)\w+ed)\b")
# A symptom said as a state rather than as an ache: skin hot or red, a wound weeping, a joint
# swollen. The symptom words the body reader knows are aches and pains, so these lines reached a
# reading of the day instead.
A_SYMPTOM_PHRASE = re.compile(
    r"\b(?:hot|warm)\s+(?:and\s+)?(?:red|redder|swollen|tender|puffy|angry)\b"
    r"|\bred(?:ness)?\s+(?:and\s+)?(?:hot|warm|spreading|swollen|tender|angry|streaky)\b"
    r"|\bhot to (?:the )?touch\b|\bweeping\b|\boozing\b|\boozed\b|\bpus\b"
    r"|\bswollen (?:and|or) (?:red|hot|tender)\b", re.I)


# Not a day that happened: a plan, a want, or a day still to come.
NOT_A_DAY_DONE = re.compile(
    r"\b(?:tomorrow|next (?:week|weekend|month|year|monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday)|gonna|going to|i will|i'll|ill|want to|wanna|plan to|planning to|"
    r"should i|shall i|can i|could i|do i|did i|have i|am i|are we|named|renamed)\b")


def _a_care_home_line(understood, memory):
    """The reply to somebody living in a care home, or None."""
    care = (understood or {}).get("care_home") if isinstance(understood, dict) else None
    if not isinstance(care, dict):
        return None
    pronoun = str(care.get("pronoun") or "they")
    several = pronoun == "they"
    words = {"they": pronoun, "them": "them", "their": "their",
             "is": "are" if several else "is"}
    shape = str(care.get("shape") or "")
    if shape == "bring":
        pool = A_CARE_HOME_BRING
    elif shape == "guilt":
        pool = A_CARE_HOME_GUILT
    elif shape == "visiting":
        pool = A_CARE_HOME_VISITING
    elif shape == "moved":
        pool = A_CARE_HOME_MOVED
    else:
        pool = A_CARE_HOME
    return _choose(tuple(line.format(**words) for line in pool), memory,
                   str(care.get("who") or ""))


# A thing they have is not a day they had. "ive got a mortgage" is the store's filing - "Noted:
# you've got a mortgage." - and "got" is a past doing, so the receipt was swapped for the day
# pool's question: "ive got a car" was answered "How was it, overall?", "ive got a boiler" "Nice
# one. How did the rest of it go?" and "ive got a dishwasher" "Sounds alright. Anything good in
# it?", while the same line with "i have" got "Noted: you have a car." Nobody asks how a thing
# they own went. Only the auxiliary form counts: "i got a haircut" and "we got burgled" are days,
# and "ive got to go" is a leave, which is answered above.
HAVE_GOT_A_THING = re.compile(
    r"\b(?:i|we)(?:['\u2019]?ve|['\u2019]?d|\s+have)\s+"
    r"(?:only\s+|just\s+|still\s+|already\s+|now\s+)?(?:got|gotten)\b(?!\s+to\b)", re.I)


def _a_day_told_instead_of_the_receipt(said_back, clean, memory):
    """The question about the day, where the echo is only a receipt of it.

    "i saw my sister at the weekend" is the store filing the visit, and the filing said back -
    "Noted: you saw your sister at the weekend." - is the coldest reply in this file and says
    nothing about the visit. A pool's own line ("Your sister is called Meg - noted.") is not a
    receipt and keeps its turn, and neither does a hire, a win or a thing bought reach here.
    """
    if not said_back or not ack.reads_as_a_receipt(said_back):
        return None
    # The receipt this file gets for a line that is only a name is the coldest of them ("Noted:
    # your kids are called jack and emma."), and a line the name reader has a pool for is not a
    # receipt and never reaches here. The names are said back and asked about instead.
    named = _a_name_told_reply(clean, memory)
    if named:
        return named
    # The detail of a day the person has already said went badly ("sorry, bad day" then "sorry,
    # it was the meeting"): the receipt is colder than the cheer it replaced, and the question
    # about the day is the reply a friend gives. The words for a bad day are not in this line,
    # so the line before it is the test.
    if _a_small_day_shape(clean) and _a_detail_of_a_bad_day(memory, clean):
        return _choose(A_BAD_TIME_TOLD, memory, clean)
    # A confession filed by the store is the coldest of the receipts: "i lied to my friend" came
    # back as "Noted: you lied to your friend." The pool asks what happened instead.
    if _a_thing_they_regret(clean):
        return _choose(A_THING_THEY_REGRET, memory, clean)
    if _a_betrayal(clean):
        return _choose(A_BETRAYAL, memory, clean)
    # "my nan is in a home too shes 88" was filed as a fact and said back, and the store is the one
    # claiming that turn: the pool answers it instead, as it does above.
    care = _a_care_home_line((memory or {}).get("understood"), memory)
    if care:
        return care
    if HAVE_GOT_A_THING.search(clean or ""):
        return None
    if _just_asked_about_the_day(memory):
        return None
    # The same three readings, in the order the day pools above are asked, because the echo this
    # replaces is also the reply a day that went wrong somewhere gets: "the mums got together on
    # sunday and it kicked off" is a row, and the cheer that stood here congratulated them on it.
    # A cheer is the wrong reply to a day like that whether it comes from the chain or from this
    # hook, so the hook asks the same questions the chain does and not only the flat one.
    if _a_bad_time_told(clean, memory):
        return _choose(A_BAD_TIME_TOLD, memory, clean)
    if _a_day_asked_without_a_cheer(clean, memory):
        return _choose(A_DAY_ASKED_PLAIN, memory, clean)
    if not _a_small_day(clean, memory):
        return None
    # A form that ate the work is a loss and not a day, and it reaches this hook as well as the
    # chain: the store's receipt is what the composer would otherwise stand behind. The order that
    # gets the work back is known, so it takes the receipt's place.
    wrecked = finding_out.the_wrecked_form_reply(clean)
    if wrecked:
        said = _choose(wrecked, memory, clean)
        if said:
            return said
    # The receipt is only a receipt: where the turn before already said how the day went, the
    # question about the day is the wrong read of the second half of it (see
    # `_the_rest_of_the_day`).
    rest = _the_rest_of_the_day(clean, memory)
    if rest:
        return _choose(rest, memory, clean)
    return _choose(A_SMALL_DAY, memory, clean)


# The person measured against other people. The cue is a crowd - "everyone else", "all my
# mates", "the only one", "people my age" - and the thing being measured is a milestone or a
# place in the order: a house, kids, a wedding, a career, "sorted", "settled", "behind", "ahead".
# Both halves are needed: a crowd on its own is "everyone is coming round tonight" and a
# milestone on its own is "i finally bought a flat".
A_CROWD = re.compile(
    r"\b(?:everyone|everybody|everyone'?s|everybody'?s|other people|others|the only one|only one|"
    r"nobody else|no one else|no-one else|"
    r"(?:everyone|everybody|people|friends|mates)\s+(?:i know|around me|my age|else|at work|"
    r"from school|from uni|from work|these days)|"
    r"all (?:of )?my (?:mates|friends|family|cousins|brothers|sisters|colleagues|workmates)|"
    r"people my age|people of my age|my age)\b")
# A place in the order, or a milestone that is the thing people are placed by. "behind" and
# "ahead" are the words a person uses for the scoreboard, so they carry the reading with any
# crowd in front of them.
A_MILESTONE = re.compile(
    r"\b(?:behind|ahead of|sorted|sorted out|settled|milestone|milestones|"
    r"bought|buying|own(?:s|ed)? a|house|houses|flat|mortgage|babies|baby|kids|children|"
    r"married|wedding|engaged|pregnan\w*|career|promotion|their lives|getting on with it|"
    r"moved on|all sorted)\b")
# Not this reading: a line that asks something (its answer is not a reassurance), a line where
# the crowd is doing something to the person ("everyone at school hates me" is a care line and
# the harm readers above it own it), a crowd celebrating the person's own news ("everyone is
# happy for us", "my sister had a baby and everyone is delighted"), and a plan or an event the
# crowd is part of ("all my mates are coming round").
NOT_A_CROWD_AHEAD = re.compile(
    r"\b(?:hate|hates|hated|bully|bullied|bullying|picks? on|picked on|leaves? me out|"
    r"left me out|laughs? at|laughed at|ignores? me|ignored me|mean to me|rumours?|gossip|"
    r"happy for (?:us|me)|proud of me|delighted for|congratulat\w*|well done|"
    r"coming round|coming over|round tonight|tonight|tomorrow|next week|next month|next year|"
    r"this weekend|party|gonna|going to|we'?re all|we are all|shall we|should we|any tips|"
    r"how do i|what should|am i|"
    # "im the only one doing anything round the house" is the work the person does for a
    # household, not a place in the order against other people, and it is the grievance readers
    # above that own it.
    r"only one (?:who|doing|that|bothered))\b")
# The frame that makes a milestone a comparison rather than news: the person is behind it, the
# only one without it, or set against a whole set of people. Without one of these the line is
# somebody else's news ("my sister had a baby and everyone is delighted") or a plan.
CROWD_ORDER = re.compile(
    r"\b(?:behind|ahead of|sorted|settled|caught up|only one|but me|"
    r"all (?:of )?my (?:mates|friends|family|cousins|brothers|sisters|colleagues|workmates)|"
    r"around me|my age|people my age|"
    r"(?:and )?i(?:'?m| am)? (?:havent|haven't|have not|aint|ain't|am not|dont|do not)|"
    r"i'?m not|im not|and i'?m still|still not|without)\b")
# A scoreboard is not an answer: each line names the comparison and hands the person their own
# question back, without guessing at the milestone they are missing.
A_CROWD_AHEAD = (
    "That comparison lands on nearly everybody, and it is not a fair one: you are seeing their "
    "headline and your own whole week. What would you actually like for yourself?",
    "The people who look sorted are mostly just further into their own thing. What is the next "
    "bit you would choose for yourself, if nobody were watching?",
    "It is worth pulling those two apart: which of those things do you actually want, and which "
    "do you only want because they have it?",
    "Everyone's timetable is their own and yours is not late, it is just not the same one. What "
    "would a good year look like for you?",
    "Nobody posts the part where it is going badly. What is the bit of your own you would want "
    "to change first?",
    "That is the comparison that makes everybody feel behind, and it has never once had the "
    "full picture. What would you want to be true for yourself a year from now?",
)


def _the_crowd_is_ahead(clean):
    """True for a line that measures the person against other people.

    A short line, no question in it, a crowd in it, a milestone in it, and the frame that makes
    the milestone a comparison (see CROWD_ORDER). The exclusions are the crowds that are not a
    measuring stick: one doing something to the person, one cheering their news, and one that is
    a plan for the evening.
    """
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text or len(text.split()) > 16:
        return False
    if not A_CROWD.search(text) or not A_MILESTONE.search(text):
        return False
    if not CROWD_ORDER.search(text):
        return False
    return not NOT_A_CROWD_AHEAD.search(text)


# A line that means the day went badly, as the understanding reads it. "work was mad today" and
# "today was mad" are the mood words the engine already files as anger, and they are the commonest
# way a hard day is said without a word like "rough" in it.
A_HARD_DAY_MOOD = ("angry", "sad", "tired", "worried", "stressed", "upset")


def _the_rest_of_the_day(clean, memory, mood="neutral"):
    """The pool for the rest of a day the turn before was about, or None.

    The line has to be an account of the day on its own, which is the same reading the flat pool
    takes: a subject with something asked about it, a plan or a question has had its own reply
    higher up and never reaches here. Then the turn before decides which day it is part of - a
    good one, so the reply adds to it instead of asking for its best bit, or a hard one, so the
    reply carries it instead of congratulating the person on it.
    """
    if not isinstance(memory, dict) or mood == "negative":
        return None
    if not _a_small_day(clean, memory):
        return None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return None
    was = _matchable(str(turns[-1].get("user") or ""))
    if not was:
        return None
    if _a_good_time(was) or _in_a_pool(str(turns[-1].get("bot") or ""),
                                      (A_GOOD_TIME, A_GOOD_TIME_IN_A_CARE_THREAD)):
        return A_REST_OF_A_GOOD_DAY
    if _in_a_pool(str(turns[-1].get("bot") or ""), (LOW_DAY_REPLIES,)):
        return A_REST_OF_A_HARD_DAY
    if _an_emotion(was) in A_HARD_DAY_MOOD:
        return A_REST_OF_A_HARD_DAY
    return None


def _an_emotion(clean):
    """The emotion the understanding engine reads in a line, or None."""
    try:
        return understanding_kinds.emotion_of(clean) or None
    except Exception:  # noqa: BLE001 - a reading that fails claims no turn
        return None


def _just_asked_about_the_day(memory):
    """True when the bot's own last line was already the question about the day.

    "we had a takeaway last night" / "it was nice not cooking" was asked how it went twice, which
    reads as not listening to the answer. The bot's last line is the test, so the second turn is
    left to the rest of the chain.
    """
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    return _in_a_pool(str(turns[-1].get("bot") or ""), (A_SMALL_DAY,))


# A line with a "not" in it is a doubt or a complaint, not an account of the day: "my brother is
# not cut out for the army" was read as a day out and got "Nice one. How did the rest of it go?".
# A negative auxiliary, spelled with the apostrophe a phone or a quick typist leaves out: the
# optional character is what "isnt" and "isn't" and "isn’t" have in common, so neither spelling
# needs its own arm and a curly one from a phone keyboard is not a miss.
_A_NEGATIVE_AUXILIARY = ("not|never|no|isn['’]?t|aren['’]?t|don['’]?t|didn['’]?t|"
                         "wasn['’]?t|weren['’]?t|can['’]?t|couldn['’]?t|"
                         "won['’]?t|hardly|cannot|haven['’]?t|hasn['’]?t|"
                         "hadn['’]?t|wouldn['’]?t|shouldn['’]?t|mustn['’]?t|"
                         "needn['’]?t|ain['’]?t|daren['’]?t|shan['’]?t|"
                         "oughtn['’]?t")
# Every auxiliary says the same thing, so the list carries them all rather than the ones that
# happened to turn up: "i havent got any cheese" and "i havent got round to it" were read as an
# afternoon's work and got "How was it, overall?", because "havent" is not the word "not".
NOT_A_DAY_SAID = re.compile(r"\b(?:" + _A_NEGATIVE_AUXILIARY + r")\b")
# The news is that somebody close did something to them: lying, cheating, hiding money, an affair.
# Read on the finding-out as well as on the deed, because that is how people say it ("i found out
# hes been lying", "turns out he cheated", "i just heard shes been seeing someone else"), and the
# deed word has to be there for the finding-out to count: "i found out im pregnant" and "i found
# out hes been promoted" are news of another kind and keep their reading.
_A_TELLING_OF_WRONG = (
    r"ly(?:ing|ed)|lies|lie\b|cheat\w*|hiding|hidden|stole|stealing|steals|gambl\w*|"
    r"affair|seeing someone|texting (?:his|her|their) ex|back with (?:his|her|their) ex|"
    r"drinking again|on the (?:booze|drugs) again|using again|owed? (?:me|us) money|"
    r"borrowed money|spent (?:it|the|our|my) .{0,20}money|gone behind my back")
A_BETRAYAL_FOUND_OUT = re.compile(
    r"\b(?:i |we )?(?:just |only |now )?(?:found|find|findin[g]|turned|turn) (?:it )?out\b"
    r"[^.!?]{0,45}\b(?:" + _A_TELLING_OF_WRONG + r")\b"
    r"|\b(?:turns|turned) out\b[^.!?]{0,45}\b(?:" + _A_TELLING_OF_WRONG + r")\b"
    r"|\b(?:i )?(?:just )?(?:heard|learned|learnt|discovered)\b[^.!?]{0,40}"
    r"\b(?:s?he|they|my \w+) (?:has been|had been|was|were|is|cheated|lied|stole)\b")


# A report of an attempt at somebody is the follow-up to a trouble, not a small account of the
# day. "my neighbour keeps parking over my drive" / "i asked him nicely twice" was answered
# "Sounds alright. Anything good in it?" once #6500 added the account-of-the-day pool: "asked"
# matched the past tense, "i" is a day subject and the line is short, so a person whose complaint
# had just gone nowhere was congratulated. "i asked him nicely", "i told him twice" after a
# landlord and "i chased them again" went the same way. What separates the two is who the doing
# was aimed at: a named person with news ("i told my mum the news") is still a small day, so it
# is the pronoun object, or a count of how many times it was tried, that stands this down.
_AN_ASKING = (r"asked|told|texted|messaged|phoned|rang|called|emailed|chased|reminded|warned|"
              r"complained|spoke|talked|written|wrote")
_AN_ATTEMPT_COUNT = (r"twice|three times|four times|five times|repeatedly|again|once more|"
                     r"for the (?:second|third|fourth|fifth) time")
AN_ATTEMPT_AT_SOMEONE = re.compile(
    r"\b(?:" + _AN_ASKING + r")(?: to)?\s+(?:him|her|them|us)\b"
    r"|\b(?:" + _AN_ASKING + r")\b(?:\s+\w+){0,4}?\s+(?:" + _AN_ATTEMPT_COUNT + r")\b")


# Whose day it was decides whether the pools' question fits. The four lines ask how it went, which
# is the right question for the person's own day and the wrong one for a thing that happened to
# somebody else: "my dad left when i was 5" was answered "Good to hear. What was the best bit?",
# "my mate got killed on call of duty" "Sounds alright. Anything good in it?", and "my marriage
# ended last year" the same. A memory from childhood is not a day that has just happened either.
SOMEONE_ELSE_NAMED = re.compile(
    r"\b(?:my|our|his|her|their)\s+(?:mum|mam|mom|mother|dad|father|son|daughter|wife|husband|"
    r"partner|boyfriend|girlfriend|brother|sister|mate|friend|boss|marriage|relationship|"
    r"nan|nana|gran|granny|grandad|grandma|uncle|aunt|cousin|neighbour|neighbor|child|kid|baby|"
    r"mother-in-law|father-in-law|in-laws|"
    # An ex is somebody, and the day is theirs: "my ex moved out" was answered "Good to hear.
    # What was the best bit?" - a cheer for a person leaving - because the day pool read it as a
    # flat account of the person's own afternoon. The cards that own a separation name "wife",
    # "partner" and "flatmate", so this line had no reading above it at all.
    r"ex|ex-wife|ex-husband|ex-partner|ex-boyfriend|ex-girlfriend|"
    r"flatmate|housemate|roommate|landlord|stepson|stepdaughter|stepmum|stepdad)\b"
    r"|\b(?:someone|somebody|a man|a woman|a bloke|a lad)\b")
A_CHILDHOOD_MEMORY = re.compile(
    r"\bwhen i was (?:\d+|little|young|a kid|a child|at school|small)\b")
# The person as the doer, which is what makes the day theirs: "i told my mum the news" and "i saw
# my sister at the weekend" are days, and the pool is what keeps the second off a receipt.
THEIR_OWN_DOING = re.compile(r"\b(?:i|im|i'm|ive|i've|we|we're|weve|we've)\b")
# A visit is the person's own day even when the other person is the one who came: "my nan came
# round for tea" was answered "How was it, overall?", and the guard below must not turn that into
# a receipt ("Noted: your nan came round for tea.").
A_VISIT = re.compile(
    # "coming over" is the commonest way a visit is said, and it was missing: "my ex is coming
    # over tonight" was read as somebody else's day and stood the day question down.
    r"\b(?:came (?:round|over|by|in)|come (?:round|over)|coming (?:round|over|by)|"
    r"popped (?:round|in|over)|"
    r"stopped by|visiting|visited|rang|phoned|called|texted|facetimed|stayed over)\b")


def _a_day_of_someone_else(text):
    """True when the day belongs to somebody else, or to a childhood that is not this day.

    One predication is enough: whoever comes first in the line is the one the day is about, so
    "my husband cornered me" is his doing and "i told my mum" is hers, and a line that names no
    speaker at all ("my marriage ended", "someone drove into the back of my car") is not an
    account of the person's own day.
    """
    if A_CHILDHOOD_MEMORY.search(text):
        return True
    who = SOMEONE_ELSE_NAMED.search(text)
    if not who:
        return False
    if A_VISIT.search(text):
        return False
    mine = THEIR_OWN_DOING.search(text)
    return mine is None or who.start() < mine.start()


# Something has to have happened in the line for "how did it go" to be about it. "i asked again"
# is a follow-up about the line above, not a day, and once the complaint above it stopped taking
# the pool's line this one took it instead: "Good to hear. What was the best bit?". The subject
# and the past tense are taken out first, and what is left has to name a thing or a time.
A_BARE_MODIFIER = frozenset(
    "a an the again already too as well anyway now so just really instead back then still yet "
    "before either though even also all of it in on at to my me myself i we our for with".split())


def _a_thing_happened(text):
    """True when the line holds a thing or a time, not only a verb and a modifier."""
    doing = PAST_DOING.search(text)
    rest = text if doing is None else text[:doing.start()] + " " + text[doing.end():]
    return bool([word for word in rest.split()
                 if len(word) > 2 and word not in A_BARE_MODIFIER])


# "i got an audition", "i got tickets for the match", "i got a viewing for a flat": a thing secured
# for a day that has not happened yet. The past tense of "got" made it a small day done, so every
# one of them was asked how it went - "How did the rest of it go?", "Anything good in it?", "How was
# it, overall?" - about something still to come. Nobody knows how it went, and the question a friend
# asks is when it is.
#
# The list is the things a person secures a place in, and it stops short of the ones that come with
# a date already in the line (`DATE_AHEAD` reads those) and of a thing that is tense rather than
# good: a scan, a test or an appointment is somebody else's pool, and "i got the job" is done.
A_THING_GOT_AHEAD = re.compile(
    r"\b(?:i|we)(?:'?ve| have)?\s+(?:just\s+|finally\s+)?"
    r"(?:got|booked|secured|bagged|landed|sorted)\s+(?:myself\s+|us\s+)?"
    r"(?:a|an|the|my|our|two|three|four|some|another|front row|cheap)?\s*"
    r"(?:audition|tickets?|viewing|viewings|booking|slot|reservations?|table booked)\b")
# A day already gone takes the past tense where it belongs: "i got a viewing yesterday" happened,
# and the line says so. A parking ticket is not a place in anything, and a bus or a train ticket is
# a purchase rather than a date.
GOT_AHEAD_GONE = re.compile(
    r"\b(?:yesterday|last (?:night|week|month|year|saturday|sunday|monday|tuesday|wednesday|"
    r"thursday|friday)|this morning|earlier|the other day|on (?:mon|tues|wednes|thurs|fri|satur|"
    r"sun)day)\b", re.I)
A_MONTH = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|"
    r"december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec|weekend after next|"
    r"the \d+(?:st|nd|rd|th))\b", re.I)
GOT_AHEAD_NOT_A_DATE = re.compile(
    r"\b(?:parking|speeding|penalty|fine|fined|clamped|bus|train|plane|coach|tube|ferry|tram|"
    r"lottery|raffle|on the way)\b", re.I)


def _a_thing_got_ahead(clean):
    """The pool for a place secured in something still to come, or None."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return None
    if not A_THING_GOT_AHEAD.search(text):
        return None
    if GOT_AHEAD_GONE.search(text) or GOT_AHEAD_NOT_A_DATE.search(text):
        return None
    if A_MONTH.search(text) or DATE_AHEAD.search(text):
        # The date is on the line already ("i got tickets to see them in june"), so asking when it
        # is would ask for the thing just said.
        return A_BOOKING_AHEAD_DATED
    return A_BOOKING_AHEAD


# ------------------------------------------------ a problem stated and nothing else
#
# A person who says they have a problem has asked for a hand and said nothing else. Every one of
# these lines fell to a pool that could have answered any message at all: "i have a problem" and
# "ok i have a problem" got the intake form, "i have an issue" got "I'm listening - say more if it
# helps", "problem" on its own got "Thanks for telling me", and the shapes with a past tense in
# them ("i got a problem", "i have a problem i need help with") were read as a small day and asked
# about cheerfully. The offer is the one the other bare asks already get, and it is the honest
# reply: yes, and the bot needs the thing before it can help.
#
# The line has to be the whole line. "i have a problem at work" and "i have a problem with my
# neighbour" name the thing, and the reply that asks what it is would lose what they just said;
# those keep their own readings, as does anything with a verb after it ("i have trouble sleeping").
PROBLEM_STATED = re.compile(
    r"^(?:so |ok |okay |right |and |hi |hiya |hello |hey |um |er |honestly |well |but )*"
    r"(?:(?:i|we)(?:'?ve|'?m| have| am| got|'?ve got)\s+|there (?:is|'?s) |theres |its |"
    r"it'?s )?"
    r"(?:a |an |one )?"
    # "a bit of a problem", "a small problem", "quite a problem": the size is part of saying it,
    # not the thing itself, so it does not stop the offer.
    r"(?:(?:bit of a|small|big|massive|real|proper|slight|little|serious|tiny|huge|nasty|"
    r"right|bit of|wee|awkward) )?"
    r"(?:problem|issue|trouble)"
    r"(?: (?:here|really|actually|now|again|too|i (?:need|could do with) (?:some )?help(?: with)?|"
    r"that i (?:need|could do with) (?:some )?help(?: with)?|i (?:need|could do with) "
    r"(?:some )?advice))?$")

# The same offer for the other half of the same line: something is up and the person has not said
# what. "something is wrong" got the intake form, "theres something wrong" and "something is
# bothering me" got "I'm listening - say more if it helps", and "something happened" got "Thanks
# for telling me - I'm here if you want to dig into any of that".
SOMETHING_UP = re.compile(
    r"^(?:so |ok |okay |right |and |hi |hello |hey |um |er |honestly |well |but )*"
    r"(?:"
    # "something is wrong", "theres something up", "something really is not right"
    r"(?:there (?:is|'?s) |theres )?"
    r"(?:(?:something|somethings|sommat|summat)(?: really| bad| weird| odd| serious| not right)?"
    r"(?:'?s)? )?"
    r"(?:is |was |keeps )?"
    r"(?:wrong|up|not right|off|the matter)"
    # "something happened", "something's gone wrong", "something has come up"
    r"|(?:something|somethings|sommat|summat)\s+(?:has |had |just )?"
    r"(?:happened|gone wrong|come up)"
    # "something is bothering me"
    r"|(?:something|somethings|sommat|summat)\s+(?:is |was |keeps )?"
    r"(?:bothering|worrying|upsetting|bugging|nagging)\s+me"
    r")"
    # The line has to end there. "something is wrong with my car" names the thing, and the offer
    # would lose it; a time or a place after it ("something happened at work yesterday") still says
    # nothing about what it was, so those are allowed.
    r"(?: (?:here|today|yesterday|tonight|last night|this morning|this week|at work|at home|"
    r"again|right now|at the moment)){0,2}$")


def _a_problem_stated(clean, repaired=None):
    """True when the line is a statement of a problem and nothing else.

    Both the line as typed and the reading's repaired text are tried, for the same reason
    `_asks_for_help` tries both: the reader puts the words back ("i hav a problem" -> "i have a
    problem", "ive got a problm" -> "i've got a problem"), and the patterns are written for
    ordinary words.
    """
    for line in (clean, repaired):
        bare = " ".join(re.sub(r"[^a-z0-9 ]+", " ", str(line or "").lower()).split())
        if bare and (PROBLEM_STATED.match(bare) or SOMETHING_UP.match(bare)):
            return True
    return False


# A line can ask what to put on and still name the day: "office has gone casual but the clients are
# in suits, what do i wear", "climbing for the first time saturday, what should i wear". The wear
# pool is written for the ask on its own (`BARE_PICK` wants the whole line to be the ask), no
# clothes row answers those occasions, and nothing else reads a clothes question - so the person
# got the search hedge, "I'd rather not guess. A quick search online will get you a solid answer",
# for the one kind of question this file can still say something true about.
# "put on" is deliberately not here: "what should i put on" is a moss killer on the lawn and a cream
# on a cold sore far more often than it is clothes, and answering those with a layer you can take
# off is the confident wrong frame this pool exists to avoid. Only the words that can only be
# clothes are in it.
WEAR_ASK = re.compile(
    r"\b(?:what|which|how)\b[^.?!]{0,40}?\b(?:wear|wearing|dress code|outfits?)\b", re.I)

# The rule that decides it, then the one question that narrows it: not a fact to look up, and not
# a guess about the occasion either. Each line leads with what is true of any day (the weather,
# how long you are on your feet, how the room is dressed) before it asks.
WEAR_WHEN_NOTHING_ANSWERS = (
    "Clothes come down to the weather and how long you are standing about: a layer you can take "
    "off, and shoes you can spend the day in. Is it indoors or out?",
    "Go off the room rather than the label - one notch up from what most people there will have "
    "on, and a layer to shed if you are the only one dressed up. Cold where you are?",
    "Dress for the coldest hour of it and the longest you will be on your feet: shoes decide "
    "more of a day than people expect. Are you inside or out?",
)


# "i have nothing to wear" is the same kind of line one step further from an ask: nothing in the
# tables answers it - it names no occasion - and it reached the echo ("Thanks for telling me - I'm
# here if you want to dig into any of that"), which is the reply that would fit any message at
# all. It is a clothes line and it is nearly always about the choice rather than the wardrobe, so
# the rule and the one question are the honest reply here too.
NOTHING_TO_WEAR = re.compile(
    r"\b(?:nothin|nothing|nowt)\b\s+(?:at all\s+)?to\s+(?:wear|put on)\b|"
    r"\b(?:nothin|nothing|nowt)\s+fits\b", re.I)

NOTHING_TO_WEAR_REPLIES = (
    "Nothing to wear usually means nothing you fancy - pick the one thing you feel good in and "
    "build the rest round it. What is the day?",
    "Everyone has nothing to wear the night before. Is it work, a meal out, or a long walk?",
    "Then wear the one you always skip and keep everything else plain. What is it for?",
)


def _says_there_is_nothing_to_wear(clean, repaired=None, text=None):
    """True when the line says there is nothing to put on, with no occasion named in the tables."""
    for line in (clean, repaired, text):
        said = " ".join(str(line or "").lower().split())
        if said and NOTHING_TO_WEAR.search(said):
            return True
    return False


def _a_wear_ask_about_a_day(clean, repaired=None, text=None):
    """True when the line asks what to put on and has a day to put it on for.

    The ask has to be part of a longer line, because the ask on its own is `_bare_pick`'s and
    already has its pool; this is the line that says the occasion first and asks after.

    All three readings are tried: `clean` is the line with the filler taken out and the ask read
    off it, so "im going to a do at the golf club and i have no idea what to wear" arrives here
    as the occasion alone and the ask in `understood["ask"]`, and only `text` still has both.
    """
    for line in (clean, repaired, text):
        said = " ".join(str(line or "").lower().split())
        if not said or not WEAR_ASK.search(said):
            continue
        rest = WEAR_ASK.sub(" ", said, count=1)
        if re.findall(r"[a-z']{2,}", rest):
            return True
    return False


# The weather as a number: "40 degree heat", "35 degrees", "minus 5". The pools above read the
# weather by the word for it ("it is boiling"), which is how a person says it when they are
# standing in it, and a line that says the figure instead ("what to wear in 40 degree heat") has
# no word in it at all, so it took the general pool and heard "dress for the coldest part of the
# day" in a heatwave. A figure needs the word degrees or a unit beside it, because "40" alone is
# an age, a run, or a bill.
HOT_FIGURE = re.compile(
    r"\b(?:\d{2})\s*(?:degrees?|°|c\b)|\b(?:minus|below)\s+(?:\d{1,2}|zero)\b|"
    r"\b(?:heat|heatwave|warm spell)\b", re.I)
# The sun said as a consequence rather than a temperature: "i burn in ten minutes" is a clothes
# line about heat, and answering it with layers for the cold is a confident wrong guess. A beach is
# the same day said another way.
WEATHER_SUN = re.compile(
    r"\b(?:sunburn\w*|sunbathe?\w*|sunny|sun cream|sunscreen|factor\s*(?:15|20|30|50)|"
    r"beach|blazing|scorching sun)\b|\bburn(?:s|t)? in (?:\w+ )?minutes?\b", re.I)
COLD_FIGURE = re.compile(
    r"\b(?:freezing|frost|snow|sleet|chilly|bitter(?:ly)?)\b|"
    r"\b(?:minus|below)\s+(?:\d{1,2}|zero)\b", re.I)


def _the_wear_pool_for_the_line(clean, repaired=None, text=None):
    """The wear pool that fits the weather the line itself named, or the general one."""
    said = " ".join(" ".join(str(line or "").lower().split())
                    for line in (clean, repaired, text))
    if WEATHER_WET.search(said):
        return BARE_PICK_WEAR_WET
    if COLD_FIGURE.search(said) or WEATHER_COLD.search(said):
        return BARE_PICK_WEAR_COLD
    if HOT_FIGURE.search(said) or WEATHER_HOT.search(said) or WEATHER_SUN.search(said):
        return BARE_PICK_WEAR_HOT
    return WEAR_WHEN_NOTHING_ANSWERS


def _a_small_day(clean, memory=None):
    """True for a short, flat account of a day of the person's own that went neither way.

    The shape first, then what the line feels like: a day that went well has its own warm pool, and
    a day that went badly is met rather than congratulated. This can only replace the intake form,
    because everything with a reading of its own has already had its turn above.
    """
    if not _a_small_day_shape(clean):
        return False
    text = " ".join(str(clean or "").lower().split())
    # Advice somebody else gave them is not a day they have had: "my mate said i should try that
    # new pizza place" has no "how did it go" in it to ask about.
    read = memory.get("understood") if isinstance(memory, dict) else None
    if isinstance(read, dict) and read.get("suggestion"):
        return False
    # A day that went well is the good-time pool's, which says something warm about it: "i had a
    # really good sleep", "we had a lovely lunch". This reading is for the flat line, where
    # nothing in it is good or bad.
    if _a_good_time(clean, memory):
        return False
    # A line that opens on "it"/"that"/"this" and a form of "be" is a detail added to what the
    # person has already said, not an account of a day of their own: "i think i sprained my ankle"
    # then "it was yesterday" was answered "Good to hear. What was the best bit?", and "it was in
    # march" after a miscarriage, "it was lifting the shopping" after a back going and "it was on
    # monday" after a cat was put down went the same way. The pleasantry is a small-day reading -
    # something happened and it was fine - and a clause with no doing of its own in it is the
    # wrong thing to read that way.
    if _a_detail_about_what_was_said(text, memory):
        return False
    # ... and neither is a line that goes back over what the person already said.
    if A_LOOKING_BACK.match(text):
        return False
    # A bad feeling in the line is the whole of it: "were gutted when it happened" and "ngl ive
    # bin knackered all week" were both asked how the day went, and "Nice one. How did the rest
    # of it go?" is the one reply a person who has just said they are gutted cannot use. The
    # reading is the one the rest of the bot uses, so a word the mood pools know ("worst", "hate")
    # counts here without being listed again.
    if ((memory or {}).get("understood") or {}).get("polarity") == -1:
        return False
    # A place secured in something still to come, only where the pool above will answer it: a
    # viewing that has already happened keeps the day question rather than losing it to a receipt.
    if _a_thing_got_ahead(text):
        return False
    # A child's name and age is a fact about them, not a day that happened: "and my sons called
    # tom, hes 9" was read as a day of someone else's and answered with the pleasantry that fits
    # any message ("Nice one. How did the rest of it go?"), where the same two facts put as "my
    # daughters name is mia and shes 6" got "Mia, 6. What is she like just now?".
    if remark.THEIR_NAME_AGE.match(text) or remark.THEIR_NAME.match(text):
        return False
    if _a_day_of_someone_else(text):
        return False
    # "i have a problem", "something is wrong": a problem is not a day, and a cheerful question
    # about it is the last thing to say back to somebody who has just said they have one.
    if _a_problem_stated(text):
        return False
    if not DAY_PAST.search(text) and not _a_thing_happened(text):
        return False
    if not (A_DAY_SUBJECT.search(text) and PAST_DOING.search(text)):
        return False
    # A day marker, or a line short enough to be one thing ("i got my hair cut"). The long shape
    # without a marker is a story, and a story has a reading of its own above.
    if not DAY_PAST.search(text) and len(text.split()) > 10:
        return False
    if NOT_A_DAY_DONE.search(text) or NOT_A_DAY_SAID.search(text):
        return False
    # A confession is not a day that happened to someone: "i lied to my friend" is filed by the
    # store like any other line and came back as a receipt, which the hook above turns into the
    # day pool's "Sounds alright. Anything good in it?".
    if _a_thing_they_regret(text):
        return False
    # A colour or a swelling is a symptom, not an account of a day, and the pool below is a warm
    # question about a day that went fine: "i had a red patch on my arm yesterday" was answered
    # "Good to hear. What was the best bit?" because "had" is a past doing and "red" was the only
    # other thing read. Written as the shape a symptom takes - two words that belong together - so
    # "i got a red dress in the sale" is still the day it sounds like.
    if A_SYMPTOM_PHRASE.search(text):
        return False
    if (NEGATIVE_LINE.search(text) or HARM_NAMED.search(text)
            or A_HURT_MYSELF.search(text)):
        return False
    # A crash or a burglary said flat is the same shape as a haircut: "we got burgled last night"
    # is a subject, a past tense and a day marker. What tells them apart is the thing itself, so
    # it is read before the pool is reached rather than left to the mood, which reads a burglary
    # as neutral.
    if A_DAY_WENT_WRONG.search(text) or remark.done_to_me(text):
        return False
    # A mishap is the careful reading's line even though nothing in the sentence is a word for
    # harm: "i got glass in my foot" and "my husband rolled off the bed" were both asked how the
    # rest of it went, and a cheerful question about a day is the one reply nobody wants after one
    # of those. Read off the whole line, so a mishap in a longer account of the day still counts,
    # and by shape rather than by body word, because "i got my hair cut" names a cut and is a day.
    # A fall that is over ("last summer", "nearly", "but hes ok") keeps the day question - it is
    # the story of a day and asking its best bit is what a friend does.
    if _a_mishap_to_ask_about(text):
        return False
    # Somebody doing them wrong - being called names, teased, picked on, left out - is the same
    # shape and the same fault: a parent told "good to hear" after their child was called names
    # has been congratulated on it.
    if SOMEONE_DONE_WRONG.search(text):
        return False
    # "i was in hospital yesterday", "i had a fall": a day with something wrong in it is the
    # trouble and feeling pools' line, and they come before this one anyway.
    if A_BAD_THING_NAMED.search(text) or A_HAND_OUT.search(text):
        return False

    # The day already went badly on the turn before: the cheer is for a day the person has said
    # nothing about, and "sorry, it was the meeting" after the bot's own sympathy is the detail
    # of that bad day, not a new one to ask about. A line that says when it happened is a day of
    # its own - "i did get out for a walk yesterday" after a grim week is the walk, not more of
    # the week - so the cheer is the question about it.
    if _the_day_was_already_bad(memory) and not DAY_PAST.search(text):
        return False
    # "i was in hospital yesterday", "we had a strange day at work": the day went wrong somewhere,
    # and the cheer is for a day that went neither way. This list only ever subtracts - the reply
    # is whatever answers next, which is the question `_a_day_asked_without_a_cheer` asks.
    # A change of medicine has an answer of its own two hooks below, and it is not a day that went
    # fine: "my meds have changed" was asked "Nice one. How did the rest of it go?". Read with the
    # same three patterns that pool uses, and with its stand-down for a symptom in the line, so the
    # dose and symptom cards keep their turns.
    if (onething.A_MEDS.search(text) and onething.A_MEDS_CHANGE.search(text)
            and onething.A_MEDS_MINE.match(text)
            and not onething.A_MEDS_SYMPTOM.search(text)):
        return False
    return not BAD_DAY_ANYWAY.search(text)


# A thing named as bad is not a flat account of a day, whatever the rest of the line looks like.
# "i got some bad news" was answered "Nice one. How did the rest of it go?" and "i got some good
# news" is the only line of that pair the pool is for. The word in front of the noun is what
# decides, so the shape is the modifier and the thing; "not bad" never reaches here, and a thing
# that is bad in a way worth naming ("a bad back", "the bad knee") is not in this list because it
# is a body part and the pools above have their own reading of it.
A_BAD_THING_NAMED = re.compile(
    r"\b(?:bad|sad|awful|terrible|dreadful|grim|rotten|lousy|horrible|horrid|rubbish|tough)\s+"
    r"(?:news|tidings)\b")

# Somebody asking for help is asking for it now, not reporting a day: "i asked for help" got
# "Sounds alright. Anything good in it?". The pool is for what happened, so it stands aside and
# the pools below are free to answer the ask.
A_HAND_OUT = re.compile(
    r"\b(?:asked|ask|asking|looked|looking|reached|reaching)\s+(?:for|out for)\s+"
    r"(?:help|support|a hand|some help)\b")


# A day with a thing gone wrong in it is not a day to ask about cheerfully, and the words for
# the things that go wrong are their own list: a crash, a burglary, a theft. "we got burgled last
# night" was answered "Sounds alright. Anything good in it?", "someone nicked my bike last week"
# "Good to hear. What was the best bit?" and "my car got keyed at the weekend" "Nice one. How did
# the rest of it go?" - the pool for a flat account of a day cannot tell a good afternoon from a
# burglary by the shape of the line, so it is the nouns that have to stop it.
# Nothing here is a word that is also said of something good: "crashed out" is an early night,
# "smashed it" and "smashed my pb" are a job well done, and "flooded with" is orders coming in,
# so the phrases are written out rather than left as bare verbs.
# The nouns above only cover the mishaps somebody has already named for us, and the same day is
# told as the verb far more often ("i got pickpocketed on the bus", "my dog ran off yesterday",
# "i chipped a tooth eating a toffee", "my phone cracked yesterday", each congratulated). The
# reading of a thing done to the person or to a thing of theirs is the remark module's setback,
# so it is asked for there rather than written out twice.
A_DAY_WENT_WRONG = re.compile(
    r"\b(?:burgl\w*|broken into|broke into|break-in|break in|robbed|robbery|mugged|mugging|"
    r"stolen|stole|theft|shoplifted|nicked|pinched|keyed|vandalised|vandalized|scratched the car|"
    r"written off|wrote it off|wrote the car off|caught fire|went on fire|on fire|burst pipe|"
    r"water damage|smoke damage|gone missing|went missing|disappeared|vanished|"
    r"crash|car crash|had a prang|a prang|in a smash|was rear-ended|rear-ended|hit by a car|"
    r"fell off|come off my bike|came off my bike|fell down the stairs)"
    r"\b|\bcrash(?:ed)?\b(?!\s+out)\b|\bflood(?:ed)?\b(?!\s+with)\b")
# "it was yesterday", "that was in march", "it was lifting the shopping": the subject is a
# pronoun standing in for the line before, so the line says nothing about a day of its own. Only
# a pronoun that has something to point at counts - on its own, with nothing before it, there is
# no "it" to be a detail about, and the line is left to the reading it would have had.
# A reply that opened on sympathy is the bot's own reading that something bad was said, which is
# the reading a detail added to it must not be congratulated.
_A_SYMPATHY = re.compile(r"\b(?:sorry|condolences|sad news|real loss)\b")

# A body that was ill is a trouble the reading above does not name: "my son was ill all week" is
# not a wrong day or a harm, and "ill" is too common to add to the day list.
_A_BODY_UNWELL = re.compile(r"\b(?:ill|illness|unwell|poorly|sick|infection)\b")

_A_DETAIL_OPENING = re.compile(r"^(?:it|that|this|there)\s+(?:was|were|is|had|happened)\b")

# A line that points back at the person's own earlier words is a correction to what is already on
# the table, not a new account of a day: "and i said it only started since may" was congratulated
# ("Good to hear. What was the best bit?") on the turn after an answer that ended in a question.
# The pronoun in the clause is what makes it a back-reference - "i said no to the offer" is a day
# with a decision in it, and keeps the pool.
A_LOOKING_BACK = re.compile(
    r"^(?:and\s+|but\s+|so\s+|well\s+)?(?:like\s+|as\s+)?i\s+(?:already\s+|did\s+)?"
    r"(?:said|told\s+you|mention\w*)\b"
    r"[^.!?]{0,50}?\b(?:it|that|this)\s+(?:only\s+|just\s+|actually\s+|never\s+)?"
    r"(?:was|were|is|had|started|began)\b",
    re.I,
)
def _a_detail_about_what_was_said(text, memory):
    """True for a clause that only adds to the line before it: "it was yesterday".

    The pleasantry this stands down is the answer to a question about a day, so it is kept when
    the bot has just asked one: "how was it, overall?" then "it was ok" is the answer, not a
    detail. What makes the line a detail is that the answer before it was advice or sympathy -
    the bot was talking about the ankle, not asking about the day.
    """
    if not _A_DETAIL_OPENING.match(text):
        return False
    turns = [turn for turn in ((memory or {}).get("turns") or []) if isinstance(turn, dict)]
    if not turns:
        return False
    last_bot = str(turns[-1].get("bot") or "")
    if _in_a_pool(last_bot, (A_SMALL_DAY,)):
        return False
    # What went before has to be a trouble, because a detail about a good thing ("i finished a
    # book last week" / "it was a thriller, set in norway") is the pleasantry's own line and
    # "got it - it was a thriller, set in norway" is worse than asking how it went. The trouble is
    # read off the line before and off the bot's own answer to it: a body part or a harm word, a
    # failure, a day that went wrong, or a reply that opened on sympathy for a death.
    if _A_SYMPATHY.search(last_bot.lower()):
        return True
    before = " ".join(str(turns[-1].get("user") or "").lower().split())
    return any(reading.search(before)
               for reading in (HARM_ANYWHERE, NEGATIVE_LINE, BAD_DAY_ANYWAY,
                              A_DAY_WENT_WRONG, _A_BODY_UNWELL))


# Being treated badly by another person is not a small account of the day to ask about warmly.
# "my son is being called names" was answered "Good to hear. What was the best bit?" and "i got
# called names at work" "How was it, overall?": the line is a subject, a past tense and a day, so
# the shape fits the pool, and only the words say that something was done to the person rather
# than by them. Every phrase here names who it was done to, because the same verbs the other way
# round are ordinary ("they called me a taxi", "we laughed at the film", "i teased my brother
# about his hair").
SOMEONE_DONE_WRONG = re.compile(
    r"\b(?:called (?:me|him|her|them|us) names|"
    r"call (?:me|him|her|them|us) names|"
    r"called names|name[- ]calling|called (?:me|him|her|them|us) a \w+ name|"
    r"got called names|got called (?:a |an |the )?(?:\w+ )?names?\b|"
    r"(?:was|were|is|are|being) called (?:a |an |the )?(?:\w+ )?names?\b|"
    r"teased (?:me|him|her|them|us)|teasing (?:me|him|her|them|us)|"
    r"bullied|bullying|bullies|"
    r"picked on|picking on|picked last|picking (?:me|him|her|them) last|"
    r"left (?:me|him|her|them|us) out|leaving (?:me|him|her|them|us) out|"
    r"laughed at (?:me|him|her|them|us)|laughing at (?:me|him|her|them|us)|"
    r"made fun of (?:me|him|her|them|us)|making fun of (?:me|him|her|them|us)|"
    r"mean to (?:me|him|her|them|us)|nasty to (?:me|him|her|them|us)|"
    r"horrible to (?:me|him|her|them|us)|"
    r"(?:would|wouldnt|wouldn't|wont|won't|didnt|didn't) let (?:me|him|her|them) play|"
    r"nobody (?:will|would|wants to) play with|"
    r"snatched (?:it|the \w+) (?:off|from) (?:me|him|her|them))\b")


# What makes an account of the day something to ask about rather than to answer: the day went
# wrong in a way that has no reading of its own above.
BAD_DAY_ANYWAY = re.compile(
    r"\b(?:hospital|a&e|ambulance|fell over|a fall|funeral|died|death|test results|biopsy|"
    # A thing that fell on the person, said with the speaker as the subject: "i had a car crash
    # last year" and "we had a flood in the kitchen" are not a day to ask how the best bit was.
    r"crash|crashed|accident|collision|flood|flooded|burst pipe|fire|burgled|robbed|stolen|"
    r"wrote off|killed|killing|(?:massive|big|huge|proper|right|awful|terrible) row|"
    r"row (?:about|over|with)|"
    r"chemo|miscarriage|evicted|lost my job|sacked|fight|row with|panic|anxiety attack|ticket|"
    # The drug that starts when the treatment stops is not a day to ask about cheerfully either:
    # "they put my dad on morphine" was answered "Nice one. How did the rest of it go?" and
    # "they started my mum on morphine" "How was it, overall?". The reading is in the loss
    # composer (`says_the_last_drug`), and this list is the fence under it, for the shapes it
    # does not read.
    r"morphine|diamorphine|midazolam|syringe driver|palliative|end of life|hospice|terminal|"
    r"clamped|fined|argued|argument|shouted|cried|upset|worried|worries|sick|threw up|migraine|"
    r"rained|soaked|drenched|wet through|late for|missed my|missed the|clinic|dentist|surgery|"
    r"wrong|mistake|messed up|screwed up|"
    r"waited|waiting|queued|queue|on hold|hung around|hung about|two hours|three hours|"
    r"four hours|an hour|all night|"
    r"headache|aching|exhausted|shattered|knackered|gutted|a row|an argument|strange|grim|"
    r"full on|fell flat|meh|"
    # The ride they came off, the thing they smashed, the wing mirror someone took off: a mishap
    # is a day that went wrong even when the line has no word for harm in it.
    r"came\s+off|smashed|smash|flooded|flooding|"
    r"stacked\s+it\b|stacked\s+(?:my|the|his|her|their)\s+"
    r"(?:bike|motorbike|moped|scooter|motorcycle|car|van|horse)\b|"
    r"wrecked|dented|chipped|snapped\s+(?:at|my|the|his|her|their)\b|"
    # A thing of theirs that stopped working, burned, or came apart in front of them: no word
    # here is a word for harm, so the line has the shape of a day and nothing in the mood reads
    # it - "my toast went up in flames" was answered "Nice one. How did the rest of it go?" and
    # "the website collapsed when we launched" "How was it, overall?".
    r"went up in flames|caught fire|blew up|blew a fuse|went bang|collapsed|fell apart|"
    r"packed in|conked out|stopped working|wouldnt start|wouldn't start|broke down|leaking|"
    # Something that was meant to come back well and came back worse, and something of theirs
    # shut: "the mortgage valuation came back 5k under our offer" was congratulated, and the
    # park at the end of a road being closed is a nuisance rather than a day to ask the best bit
    # of. "i closed the shop" is a day's work and keeps the cheer, which is why the verb has to
    # be the one the thing itself carries.
    r"came back (?:short|lower|worse)|under (?:our|the) (?:offer|asking)|over budget|"
    r"went over budget|(?:is|are|was|were) (?:still )?closed|"
    # Somebody telling the person off rather than the person telling a story: the same shape as
    # the haircut, so only these words separate them. ("it kicked off" is the same news and is
    # read a step earlier, in `A_DAY_SAID_BADLY`, because it wants the sympathetic question and
    # not the neutral one.)
    r"told\s+[^,.;!?]{0,25}?\boff\b|had a go at me|had a right go|"
    # A penalty put on the thing they parked, and a body or an animal that came a cropper in a
    # way that names no harm: "they put a boot on my car", "my cat fell in the paddling pool",
    # "i was short of breath earlier". "fell in love" is the one phrase the middle one would
    # take by mistake, and it is excluded by name.
    r"boot on (?:my|the|our) (?:car|van|motor|bike)\b|fell in (?!love)|"
    r"choked(?!\s+up)|short of breath|"
    # A thing marked or spoiled rather than broken ("my kettle is blackened on the bottom"), and a
    # mistake they made at work ("i keep slipping up at work and im confused"): neither names any
    # harm, and both were congratulated.
    r"blackened|burnt|burned|scorched|stained|rusted|scratched|slipping up|slipped up|"
    r"messed up|mucking up|mucked up|"
    r"knocked\s+over|tipped\s+over)\b")


FOOD_TOPICS = frozenset(("cooking", "food-and-drink"))


def _a_dish_name(clean, words, memory):
    """Is this line the name of a dish rather than a report of something done?

    Asked of the understanding engine's own reading, not of a word list: a line it read as
    cooking or food-and-drink is a subject the knowledge base answers, and "packed lunch for a
    vegan" is a question about lunch however it opens.
    """
    if len(words) < 2 or words[0] not in DISH_PARTICIPLE:
        return False
    if words[1] in DISH_DETERMINER:
        return False
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(understood, dict):
        return False
    topics = set(understood.get("topics") or ())
    if isinstance(understood.get("topic"), str):
        topics.add(understood["topic"])
    return bool(topics & FOOD_TOPICS)


def _a_report_with_no_pronoun(clean, text, memory):
    """A thing done said without the "i": "booked the hotel last night", "paid the deposit".

    The dropped pronoun is what makes this the composer's line rather than the knowledge base's.
    A card cannot tell "booked the hotel last night" from "how do i book a hotel" - both hold the
    word "hotel" and the word "book" - but a past tense in the first word is a report, and the
    whole line is then a thing done with nothing to advise. A line with its subject ("i booked the
    hotel last night") is not this: the answers module can still tell it from the how-to, and the
    composer only takes what nothing else can read.
    """
    words = re.findall(r"[a-z']+", clean)
    if not words or words[0] not in DONE_VERB:
        return False
    if HARM_ANYWHERE.search(clean):
        return False
    if any(w in DONE_NOT_THIS for w in words[1:3]):
        return False
    if _a_dish_name(clean, words, memory):
        return False
    # The composer claims the line only when its own answer for it is the thing-done pool. A
    # report the gentle pools would answer keeps the knowledge base's answer: "signed the consent
    # form for the operation" is a thing done and an operation, and "That sounds rough" is worse
    # than the how-to it replaced. Asked of the composer's own reading rather than of a word list,
    # so a pool added here is covered without a second place to keep it.
    if _thing_done_scan(clean)[0] != "done":
        return False
    try:
        reply = reply_for(text, memory)
    except Exception:  # noqa: BLE001 - a composer that cannot answer claims nothing
        return False
    return reply in _THING_DONE_LINES


# The arbiter reads this before the never-repeat fallback (README.md, "Interface"). Three kinds
# of line have no words of their own to match, and only the composer reads them: a line that is
# nothing but a report on the advice just given ("its not helping", "no change yet", "i did what
# you said"), a bare "why" after a substantive answer (bot/compose/why.py), and a bare hand-off -
# "one more thing", "quick one" - which announces something and has not said it yet
# (bot/compose/handoff.py). A line that says it did what was said and got nowhere is the most
# useful thing a person can say in an advice thread, and the chat module otherwise answers it with
# the line back or a stock "Alright then - good luck with it."
def _repaired_of(text, memory):
    """The line with its chat-speak put right, as the reading made it, or "" for none.

    The reading is the arbiter's own (`memory["understood"]`) when it is this turn's, so the
    router asks for no second reading of the line; a reading that fails claims no repair.
    """
    try:
        read = memory.get("understood")
        if isinstance(read, dict) and read.get("plain"):
            return str(read["plain"])
        read = understand(text, memory)
        return str((read or {}).get("plain") or "")
    except Exception:  # noqa: BLE001 - no repair, and the typed line still reads
        return ""


def takes_as_it_comes(text, memory):
    """Does the composer read this whole line, whatever any topic entry matching it says?"""
    clean = " ".join(str(text or "").lower().split())
    try:
        if reads_as_a_report(text, memory):
            return True
        # A regret the composer can meet is its own turn: the entries match the nouns of a line
        # ("i regret buying this car" reached the returns card on "car" and "buy"), and no card is
        # an answer to "i regret it". Only where the composer really has the line, so the claim is
        # as narrow as the reply (bot/compose/remark.py, `regret_reply_for`).
        if remark.regret_reply_for(clean, clean.split(), memory,
                                   _repaired_of(text, memory)):
            return True
        # A thing done with the pronoun dropped is a report, and the answer cards that hold its
        # words are instructions: "booked the hotel last night" reached the choose-a-hotel card
        # because nothing said a past tense is not a request for advice.
        if _a_report_with_no_pronoun(clean, text, memory):
            return True
        if why.takes_as_it_comes(text, memory):
            return True
        if _a_verdict_line(clean, memory):
            # A line that is only a verdict on the thing before it ("what a nightmare", "nightmare")
            # names nothing to look up, so no topic entry may take it on a word of it: the sleep
            # card answered "nightmare" after a job loss with the advice for dreams.
            return True
        if safetyask.reply_for(clean, memory):
            # "is it safe to keep it on tonight" is this module's question whatever a card
            # matches on the words of it: the repeat frame and the search shrug both answered it
            # before, and neither is a reply to somebody standing next to a dripping boiler.
            return not _after_safety(memory, clean, memory.get("understood"))
        if _a_verdict_on_their_plan(clean, memory):
            # A verdict asked for on the plan already on the table: the stock nod and the search
            # shrug both offered for it, and it wants neither. See _a_verdict_on_their_plan.
            return True
        # The place on the table, asked about in three words: "is it nice" after "we are going to
        # Cornwall in August". The line holds nothing to look up - the pool is only the words of
        # judgement - and the two replies it was getting were a sign-off ("Alright then - good luck
        # with it", because a three-word line with "nice" in it read as agreement) and the search
        # hedge. See _a_place_asked_about.
        if _a_place_asked_about(clean, memory):
            return True
        # "did you see it" is a conversation, not a read of what the person just said: the store
        # answered it "Yes - you watched the final together" at PRIORITY 7000, which is a true
        # sentence and no reply at all to somebody who wants to tell you about the match.
        if reads_as_if_i_saw(text, memory):
            return True
        # A short line that answers a question this composer has just asked is the next turn of
        # the same thread, whatever a card matches on one of its words: "since the baby" after
        # "what's it like at the moment?" was answered by the new-baby card. The claim is only as
        # wide as the reply - a question, a sentence with its own verb, a fault to repair and a
        # shrug are all left to the rest of the bot (bot/compose/trouble.py,
        # `answers_a_strain_question`).
        if "?" not in str(text or "") and trouble.answers_a_strain_question(clean, memory):
            return True
        # A plan the person has had to drop is the composer's line whatever else matched the nouns
        # in it: "gonna have to cancel" reached a plan pool ("Sounds like a plan. Tell me how it
        # turns out"), which answers a cancellation as if the person were looking forward to it.
        # The reading is the same narrow one the reply is built from, so a line that only uses the
        # verb in its other sense is not claimed ("i have to cancel my gym membership" keeps its
        # entry, `DECLINE_OTHER` and the tail rule in `_a_declined_plan`).
        #
        # Not when the thing dropped is already named in the chat and the line does not say
        # "cancel": "im going to the party on saturday" / "i cant make it" wants the words to say
        # to them, which the entry about telling somebody you cannot come already writes, and
        # "we booked a table for friday" / "cant make it tonight" wants what the booking card
        # knows. The composer's "do you want to rearrange it, or let this one go?" is the nod
        # beside a real answer (`_a_plan_on_the_table`).
        if (_a_declined_plan(_plain(clean), without_a_thing=True)
                # A feeling before the decline keeps its own answer, and the claim is what stops
                # one being proposed: "i had a panic attack" / "i cant come" was "no trouble at
                # all", and holding the turn for the composer took the panic card off the table.
                # A death or bad news is the exception, because the composer answers that one
                # gently and no entry does ("my wife is in hospital" / "i cant come" would go
                # back to the visiting-times card).
                and (_a_hard_week(memory)
                     or not _the_turn_before_was_a_heavy_one(memory, _plain(clean)))
                and not (_a_plan_on_the_table(memory) and not _the_line_cancels(_plain(clean)))):
            # Not while the bot is still with somebody in an emergency: there a "i cant come" is
            # the next turn of that thread, and the careful continuation is the reply (the same
            # shape as the hand-off hook below).
            return not _after_safety(memory, clean, memory.get("understood"))
        if not handoff.takes_as_it_comes(text, memory):
            return False
        # A hand-off is this module's to answer, unless the bot has just answered an emergency:
        # there the line gets the careful continuation instead, so the arbiter must not be told
        # the composer read it as a hand-off (the same shape as the #2494 hook fix).
        return not _after_safety(memory, clean, memory.get("understood"))
    except Exception:  # noqa: BLE001 - a reading that fails claims no turn
        return False


TAKES_AS_IT_COMES = takes_as_it_comes


# A name is not an afternoon's work: "my kids are called jack and emma" and "my mother-in-law is
# called june" opened with a subject and a past tense and were asked how the day went ("Nice one.
# How did the rest of it go?").
A_NAME_IS_NOT_A_DAY = re.compile(r"\b(?:is|are|was|were)\s+(?:called|named)\b")
# The name reader in remark.py has a line for one of them - "my sister is called rose" -> "Rose —
# noted with care. What does she make of it?" - but the collective shapes (kids, parents, the
# in-laws) and a person word with an adjective in front ("my new boss") are not in its patterns.
# Standing the cheer down alone put those on the store's read-back ("Noted: your kids are called
# jack and emma."), which is the restatement STYLE.md opens with, so the names are said back the
# way a person would say them and one question about the people is asked: with nothing known
# about them, that is the whole of the warm reply available.
A_NAMES_TOLD = re.compile(
    r"\bmy\s+(?:(?:new|old|little|big|eldest|youngest|middle|first|second|step|ex|late)\s+)?"
    r"(?P<person>[a-z][a-z'-]{1,20})\s+(?:is|are|was|were)\s+(?:called|named)\s+"
    r"(?P<names>[a-z][a-z'-]{0,20}(?:\s*(?:,|and|\s)\s*[a-z][a-z'-]{0,20}){0,3})"
    # A name with something said after it ("my mum is called janet and shes 72", "my sister is
    # called rose and she lives in leeds"): the figure or the place is the name reader's own line
    # where it reads the shape, and where it does not the name is still the whole of what this
    # pool needs - the receipt that would otherwise be said back says less than the name does.
    r"(?:\s+(?:and|,)?\s*(?:she|he|they|it)s?\b[^.!?]{0,80})?\s*$")
# A name the whole household answers to ("we are called the smiths", "they were called the
# williams"): there is no person word to take a pronoun from, so the question is about the name.
A_NAME_A_HOUSEHOLD_TAKES = re.compile(
    r"\b(?:we|they)\s+(?:are|were)\s+(?:called|named)\s+"
    r"(?P<names>[a-z][a-z'-]{0,20}(?:\s*(?:,|and|\s)\s*[a-z][a-z'-]{0,20}){0,3})\s*$")
# A word after "called" that names nobody: "my son is called after me", "my car is called it".
NOT_A_NAME_WORD = frozenset((
    "the", "a", "an", "it", "its", "that", "this", "him", "her", "them", "me", "after",
    "something", "nothing", "whatever", "what", "which", "who", "but", "and",
    "she", "hes", "he", "they", "we", "us", "his", "hers", "theirs", "is", "was", "were",
))


def _a_name_told(clean):
    """The names and the person, when the line is only a name: ("Jack and Emma", "kids", True).

    The third part is whether the names are more than one, because "Jack and Emma" is they and
    "June" is she or he: the pronoun comes from the person word the same way the name reader
    does it, so nothing here guesses.
    """
    said = " ".join(str(clean or "").lower().split()).strip(" .!,")
    if not said or "?" in said:
        return None
    match = A_NAMES_TOLD.search(said)
    person = match.group("person") if match else ""
    if not match:
        match = A_NAME_A_HOUSEHOLD_TAKES.search(said)
        if not match:
            return None
    names = [word.strip() for word in re.split(r"\s*(?:,|and)\s*", match.group("names"))]
    # The list stops at the first word that names nobody, so a sentence after the names
    # ("janet and she lives in leeds") leaves the name and not the sentence: the reply is about
    # the people, and their address is theirs to tell. "my son is called after me" is no name at
    # all and leaves nothing, while "the smiths" is a name with "the" in it.
    kept = []
    for word in names:
        if not word or set(word.split()) <= NOT_A_NAME_WORD:
            break
        kept.append(word)
    names = kept
    if not names:
        return None
    if len(names) == 1:
        spoken = names[0].title()
    else:
        spoken = ", ".join(word.title() for word in names[:-1]) + " and " + names[-1].title()
    # A name on a thing is not a person to ask about: "my car is called betsy" says nothing about
    # anybody, and "What are they like?" is not a question about a car. So the person word has to
    # be one the bot already reads as a person (the list the rest of this file uses, which carries
    # a dog and a cat but not a car), or one of the hyphenated kin words the list does not carry
    # ("mother-in-law", "step-dad"); otherwise the reply is about the name itself.
    if person and person not in THE_PEOPLE and "-" not in person:
        person = ""
    return spoken, person, len(names) > 1


# A name that came from somebody is not a name at all: "my son is called after me", "hes named
# after his grandad", "i was named after my nan". The name reader rightly stands down ("after you"
# is not a name), so these reached the store's read-back - "Noted: your son is called after you."
# - which is the coldest reply in this file and says nothing about the person the name came from.
# The shape is the words themselves, so nothing else in the file has to know about it.
NAMED_AFTER = re.compile(
    r"\b(?:called|named)\s+(?:(?:him|her|them|it|me|us)\s+)?after\s+(?P<who>me|us|you|i|"
    r"(?:my|his|her|their|our)\s+[a-z-]+)\b")
A_POSSESSIVE_OF_MINE = frozenset(("my", "our"))


def _named_after_reply(clean, memory):
    """The reply to a name that came from somebody, or None."""
    said = " ".join(str(clean or "").lower().split())
    found = NAMED_AFTER.search(said)
    if not found:
        return None
    who = found.group("who")
    if who in ("me", "us", "you", "i"):
        return _choose(A_NAMED_AFTER_THEM, memory, clean) or None
    words = who.split()
    # "my nan" is the person being spoken to's nan, so the reply says "your nan"; "his grandad" is
    # already how they would say it and is left alone.
    if words[0] in A_POSSESSIVE_OF_MINE:
        who = "your " + words[1]
    lines = [remark.fill_person(line.replace("{who}", who), words[-1])
             for line in A_NAMED_AFTER]
    return _choose(lines, memory, clean) or None


def _a_name_told_reply(clean, memory):
    """The reply to a line that is only a name, said back and asked about, or None."""
    told = _a_name_told(clean)
    if not told:
        return None
    spoken, person, plural = told
    if not person:
        return _choose([line.replace("{names}", spoken) for line in A_NAME_STORY],
                       memory, clean) or None
    # "kids" is the plural stand-in for the pronoun: fill_person gives they/them/their for a word
    # that is not one person, which is what two names need.
    lines = [remark.fill_person(line.replace("{names}", spoken), "kids" if plural else person)
             for line in A_NAME_TOLD]
    return _choose(lines, memory, clean) or None
# A state is not a day either. "im self employed" and "i was on a diet last year" opened with
# the person as the subject and a past tense in them, and were asked how the rest of it went ("Good
# to hear. What was the best bit?"); there is no rest of it, they were saying what is true of them.
# An "-ed" word that describes rather than does ("employed", "married", "retired") is the same
# kind of word as "tired", and "was" on its own says what was the case.
STATE_NOT_A_DOING = re.compile(
    r"\b(?:self[- ]?employed|unemployed|retired|married|divorced|engaged|separated|pregnant|"
    r"based|interested|tired|exhausted|worried|bothered|pleased|delighted|annoyed|scared|"
    r"frightened|settled|sorted|done|on a diet|on benefits|in debt|in credit|on the dole|"
    r"a vegetarian|a vegan|on medication|on tablets)\b")
BARE_STATE = re.compile(r"\b(?:was|were|been|is|are|am|im|i'm|its|it's)\b")
# Which way to ask about it: "i was on a diet last year" is a thing to look back on, "im self
# employed" is a thing still going.
STATE_THEN = re.compile(
    r"\b(?:last (?:year|summer|winter|spring|autumn|month)|years ago|used to|back then|"
    r"when i was|in the past)\b")
# The copula a state that has ended is said with: "i was married for 20 years", "we were skint
# that winter". "been" is left out on purpose - "ive been self employed for 3 years" is a state
# still going.
STATE_IN_THE_PAST = re.compile(r"\b(?:was|were)\b")


# A plan that did not happen, said as a thing that was meant to be: "i was meant to be on holiday
# this week", "it was meant to be a loaf of bread". The cheer that followed it ("Sounds alright.
# Anything good in it?") asked about a day nobody had described, and a loaf that came out wrong is
# the same news as one that came out grey.
# The marker is "supposed to" and "meant to" themselves, so the verb after it is any verb:
# "i was supposed to call the bank", "we were supposed to go away", "i was supposed to finish it
# today" are the same shape as "i was supposed to be on holiday", and all four were cheered.
PLAN_THAT_FELL_THROUGH = re.compile(
    r"\b(?:was|were|is|are|had|have)\s+(?:meant|supposed)\s+to\s+[a-z]+")


def _a_state_of_theirs(text):
    """\"now\", \"then\" or None: what is true of the person rather than what they did.

    A line here has the person as its subject and a word of state in it (\"self employed\",
    \"on a diet\", \"married\") and no past doing of its own, so there is no day to ask about.
    The day marker is what makes a line an account again: \"work was ok today\" is a day had.
    """
    text = " ".join(str(text or "").lower().split())
    if not text or not A_DAY_SUBJECT.search(text):
        return None
    if not STATE_NOT_A_DOING.search(text):
        return None
    rest = BARE_STATE.sub(" ", STATE_NOT_A_DOING.sub(" ", text))
    if DAY_PAST.search(text) or PAST_DOING.search(rest):
        return None
    # "i was married for 20 years" is a state that has ended, and the marker list below only knows
    # the usual time words, so the copula itself says which way to ask: was/were is a state to look
    # back on, is/am/are one still going.
    if STATE_THEN.search(text) or STATE_IN_THE_PAST.search(text):
        return "then"
    return "now"


# A thing that came out wrong is the report of a day that went badly: "it came out grey in the
# middle" was told "How was it, overall?", which is the one thing a person who has just said the
# bake went wrong cannot use. The shape is the result rather than the doing, so it is read on its
# own and the pools for a thing gone wrong are above this one.
RESULT_WENT_WRONG = re.compile(
    r"\b(?:came out|comes out|turned out|turns out|came back|comes back|ended up|went|goes)\s+"
    r"(?:a bit\s+|a little\s+|all\s+|really\s+|quite\s+|so\s+)?\s*"
    r"(?:grey|gray|dry|soggy|burnt|burned|raw|tough|dense|rubbery|pale|lumpy|stodgy|stale|"
    r"bland|wrong|ruined|awful|horrible|terrible|overdone|undercooked|flat|sour|bitter|"
    r"curdled|split|seized)\b")


# The bot's own last line met the day with sympathy, name in front or not ("Hi Eve — sorry to
# hear that. A walk and someone to talk to usually help more than sitting with it.").
BOT_WAS_SORRY = re.compile(
    r"\b(?:sorry|that sounds (?:rough|awful|horrible|hard|heavy|tough)|that is (?:rough|awful|"
    r"hard|heavy|tough)|that's (?:rough|awful|horrible|hard|heavy|tough)|rough one|hard one)\b",
    re.I)


# The words for a day said badly when the day itself is the subject: "sorry, bad day", "rough one
# today", "a rubbish day", "strange day at work", "long day". BAD_DAY_ANYWAY below can afford
# words like "waited" and "late for" because it only ever takes a cheer away; this one decides
# whether the *next* short line belongs to a day already on the table, so it keeps to the words
# that are about the day rather than about one irritating thing in it.
A_DAY_SAID_BADLY = re.compile(
    r"\b(?:bad day|bad one|rough day|rough one|rubbish day|rubbish|awful day|horrible day|"
    r"terrible day|hard day|hard one|long day|tough day|tough one|strange day|grim|draining|"
    # A row that started: "the mums got together on sunday and it kicked off" has the shape of an
    # account of a day and no word in it that says what it was. "it kicked off" and not
    # "kicked off", because that is also how a match or a party starts.
    r"it kicked off|"
    r"wiped out|hectic|full on|knackered|exhausted|shattered|gutted|a row|an argument)\b")
# A day nobody called bad, said only by the way the person did something in it: "i ate badly all
# week", "i drank too much last night", "i skipped the gym all week". None of those names a bad
# day, so the cheer below answered a week they had just told you went wrong with "Good to hear.
# What was the best bit?" - the one reply that cannot be given - and the words that say it are the
# way the doing went, not a word for the day. Two shapes, kept apart because they are not the same
# risk: the excess words are never good news about a doing of the person's own, and "skipped" is
# only a slip where the line also says how long it went on ("i skipped breakfast" is a morning,
# "i gave up sugar yesterday" is an achievement and keeps its own reply above).
A_DOING_GONE_BADLY = re.compile(
    r"\b(?:badly|too\s+much|too\s+many|too\s+often|not\s+enough|nothing\s+but|binged|"
    r"overdid\s+it|junk|crap|rubbish)\b")
A_THING_SKIPPED = re.compile(
    r"\bskipped\b(?:\s+\w+){0,4}\s+(?:all\s+(?:week|month|weekend)|this\s+week|last\s+week|"
    r"lately|every\s+(?:day|morning|week)|again)\b")
# A meal skipped is a day with a hole in it rather than a slip, and the ones that answer it name
# the hole: "i skipped lunch again" is already met with "That's a day with a hole in the middle of
# it. Is it no time to stop, or nothing in?" - warmer and more specific than the pool this
# change reaches, so a skipped meal is left to it and the span above only reads a doing.
A_MEAL_SKIPPED = re.compile(
    r"\bskipped\b(?:\s+\w+){0,2}\s+(?:a\s+|any\s+|my\s+|the\s+)?"
    r"(?:breakfast|lunch|lunches|dinner|dinners|tea|supper|meals?|food)\b")


def _a_day_said_badly(text):
    """True when the person's own line reads as a day that went badly."""
    said = " ".join(str(text or "").lower().split()).strip(" .!,")
    if not said or "?" in said or len(said.split()) > 12:
        return False
    return bool(A_DAY_SAID_BADLY.search(said))


def _the_last_exchange(memory):
    """The last turn that has a reply on it, or None.

    The turn being composed is already on the record with an empty bot line by the time this file
    reads it, so `turns[-1]` is the line being answered and not the exchange before it. Every
    reading of "the line before this one" in this file has to look for the last turn that has a
    bot line, or it reads the wrong turn - which is how the bad-day guard came out false on the
    very row it was written for ("sorry, bad day" then "sorry, it was the meeting").
    """
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    for turn in reversed(turns):
        if str(turn.get("bot") or "").strip():
            return turn
    return None


def _the_day_was_already_bad(memory):
    """True when the bot's own last line already met a bad day.

    "sorry, bad day" / "sorry, it was the meeting": the second line names what went wrong in the
    day the bot has just answered with sympathy, and the cheer that follows it ("Good to hear.
    What was the best bit?") reads as not having heard the first line at all. The bot's own last
    reply is the test, so a day that has already gone badly is only read as one while it is still
    on the table; a chat the bot has moved on from is left to the rest of the chain.
    """
    seen = _the_last_exchange(memory)
    if seen is None:
        return False
    last = str(seen.get("bot") or "")
    # A plan that fell through and a flat day read with no presumption in it are the same thing:
    # the bot has just said something is a shame, so the line after it is the rest of that story and
    # not a new day to cheer. "it was supposed to be sunny" then "we had the picnic in the front
    # room" was told "Nice one. How did the rest of it go?" on top of the bot's own "Ah no. What
    # stopped it?", which is the cheer contradicting the line above it.
    if _in_a_pool(last, (LOW_DAY_REPLIES, NEGATIVE, A_BAD_TIME_TOLD, A_THING_CAME_OUT_WRONG,
                         A_PLAN_THAT_FELL_THROUGH, A_DAY_ASKED_PLAIN)):
        return True
    if BOT_WAS_SORRY.search(last[:80]):
        return True
    # The pools that answer a bad day live in other modules and bring prose of their own ("Rough
    # one. A shower, something warm to eat and an early night usually resets it."), so no list of
    # their openers kept here would cover them - the first reading of this guard missed exactly
    # that line, and the row it was written for still went to the cheer. What the bot heard is on
    # the record too, so the test is the person's own line before it: a day this file would read
    # as one gone badly, and the short line after it is the detail of that day, not a new day.
    return _a_day_said_badly(seen.get("user"))


def _a_detail_of_a_bad_day(memory, text=None):
    """True when this line is the detail of a day the person has already said went badly.

    Narrower than `_the_day_was_already_bad` on purpose: the bot says something sympathetic after
    a great many lines, and the cheer for a haircut after a boiler is a new day, not a detail of
    the old one. What makes it a detail is the person's own line before it - a day read as one
    gone badly - and the short shape of this one.
    """
    seen = _the_last_exchange(memory)
    if seen is None:
        return False
    # A line that says when it happened is a day of its own. "i did get out for a walk yesterday"
    # after a grim week was read as more of the grim week and answered "How are you doing with
    # it?", where the question about the walk is what a friend asks; the exception is the short
    # clause that adds the day to what was already said ("it was yesterday"), which is the detail
    # this reading is for in the first place.
    if text and DAY_PAST.search(str(text).lower()):
        return bool(_a_detail_about_what_was_said(text, memory))
    return _a_day_said_badly(seen.get("user"))


# A thing that is going on, a thing somebody else settled and a wish are all the same shape as an
# account of a day - a subject, a past doing, a word ending in -ed - and none of them is a day that
# is over. On main the pleasantry went to all three: "i am being followed by my shadow" and "my
# leave got approved" got "How was it, overall?", "i wish i was on that beach" and "i wish it was
# friday" got "Nice one. How did the rest of it go?", and "if only i was there" got "How was it,
# overall?".
#
# The present passive is the shape that says a thing is happening now ("i am being followed", "the
# kids are being horrible"); "i got followed home" is still a day. A decision is a thing somebody
# else settled ("the invoice was approved at work", "my shift was confirmed") is a report of a
# thing, not a day spent; the ones that are the person's own good news have already been answered by
# the news reader above. A wish is about what is not the case, and nothing after it is read.
A_BEING_DONE_NOW = re.compile(
    r"\b(?:i|we|he|she|they|it|you|the|my|our|his|her|their|\w+s)\s+"
    r"(?:am|is|are|was|were|been)\s+being\b|\b(?:i'm|im|we're|they're|he's|she's|it's)\s+being\b",
    re.I)
A_DECISION_NOT_A_DAY = re.compile(r"\b(?:approved|granted|confirmed)\b", re.I)
A_WISH = re.compile(r"\b(?:i|we)\s+(?:really\s+|just\s+|so\s+|do\s+)?wish\b|\bif only\b", re.I)
# What to say to a sum of money with no second figure beside it. A friend does not call a price
# good or bad on its own - they ask what the other quote was - and that is also the only thing the
# bot can honestly say from here.
A_SUM_STATED = (
    "{said} on its own tells me nothing about whether it is high or low. What were you paying "
    "before, or what has someone else been quoted for the same thing?",
    "Put {said} beside the other figure for the same job - what you were paying before, or what a "
    "friend was quoted - and then it means something. What have you got to compare it with?",
)
# The words that make a sum of money a price rather than an amount of something. Fenced on the
# nouns a price is said with, because the verb alone is too wide: "it was 60" is a price with a
# haircut in front of it and a measurement without one.
PRICE_NOUNS = frozenset((
    "paid", "pay", "pays", "paying", "cost", "costs", "costing", "charged", "charge",
    "charging", "quote", "quoted", "quoting", "price", "priced", "fee", "fees", "bill",
    "bills", "invoice", "deposit", "fare", "fares", "spent", "spend", "spending", "wants",
    "wanting", "asking",
))
# The words a line can be made of and still name nothing: "it was 60" is a figure with no thing in
# front of it, and a sum with no thing in front of it is a measurement or a number in the middle of
# some other story, not a price. "my new sofa was 800" names the thing, and it is a price.
NO_THING_SAID = frozenset((
    "i", "me", "my", "we", "us", "our", "it", "its", "it's", "that", "thats", "that's",
    "this", "they", "them", "their", "he", "she", "his", "her", "was", "were", "is",
    "are", "be", "been", "a", "an", "the", "and", "but", "so", "then", "now", "just",
    "only", "about", "around", "at", "for", "of", "to", "in", "on", "with", "from",
    "much", "many", "um", "err", "well", "really",
))
# Money that came to the person is not a price they are asking to have judged. "my bonus was 500",
# "my refund was 60", "my pay went up by 200", "they paid me 200" - a friend is glad about that or
# asks about it, and does not say the figure means nothing on its own. The fence is the direction,
# not the sum: the same verb with the money going out ("i paid 200 for it") is still a price.
MONEY_IN_NOUNS = frozenset((
    "bonus", "bonuses", "refund", "refunds", "rebate", "rebates", "payout", "payouts", "pay",
    "wages", "salary", "earnings", "income", "pension", "pensions", "winnings", "commission",
    "dividend", "dividends", "raise", "rise", "backpay", "arrears",
))
MONEY_IN_SHAPES = re.compile(
    r"\b(?:paid|pay|pays|paying|gave|give|gives|giving|refunded|reimbursed|repaid)\s+"
    r"(?:me|us)\b"
    r"|\b(?:i|we)\s+(?:was|were|am|are|got|get|have|had)\s+(?:paid|given|refunded|"
    r"reimbursed|awarded)\b"
    r"|\b(?:i|we)\s+(?:earned|earn|made|make|won|win|sold)\b[^.]{0,24}?\bfor\b"
    r"|\b(?:sold|selling)\b[^.]{0,24}?\bfor\b\s*[\u00a3$\u20ac]?\d"
    r"|\b(?:got|get|gets|getting)\s+[\u00a3$\u20ac]?\d+\s+(?:for|from|back)\b"
    r"|\b(?:pay|wages|salary|income|pension)\s+(?:went|goes|has gone|rose|increased|is up)\b",
    re.I,
)


def _money_came_to_them(text, words):
    """True for a sum the person was given, paid, earned or refunded rather than asked to judge."""
    if words & MONEY_IN_NOUNS:
        return True
    return bool(MONEY_IN_SHAPES.search(text))


def _a_sum_with_nothing_beside_it(clean, memory=None):
    """The figure, said back the way they wrote it, for a sum of money stated with no question.

    Three ways for a line to say the figure is money: a currency mark, a price word ("paid", "the
    quote came to", "the fee"), or a price verb with a thing in front of it ("my new sofa was
    800"). The third is the one that needs care, because the same verb says a measurement: "it was
    60" names nothing, so it is not a price and the reading stands down. An amount with none of the
    three is somebody else's money - "my nan left me 500" is a bequest, and asking what they were
    paying before would be the wrong question about it - so that stands down too.

    The direction is fenced first: money that came to the person ("my bonus was 500", "they paid me
    200", "my pay went up by 200") is not a price, and a friend answers a bonus or a refund as the
    good news it is. Only money going out is a sum with nothing to judge it by.

    The figure itself is read by the same code a doubt is read by (`reading._their_figure`), so a
    year, an age and a distance are passed over here for the same reasons they are passed over
    there. No range is looked for in the answer just given: everything with a card behind it has
    already answered the turn above, so a sum that reaches this line is one the bot knows nothing
    about.
    """
    from . import reading  # noqa: PLC0415 - the reader imports back into this module's band

    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return None
    words = set(re.findall(r"[a-z']+", text))
    if _money_came_to_them(text, words):
        return None
    marked = bool(re.search(r"[\u00a3$\u20ac]", text))
    named = bool(words - NO_THING_SAID)
    if not (marked or (words & PRICE_NOUNS) or (named and reading.A_PRICE_VERB.search(text))):
        return None
    found = reading._their_figure({"turns": [{"user": text}]})
    if not found:
        return None
    _value, _unit, said, money = found
    if not money or not said:
        return None
    return said
# A report of something the person has only heard, seen or read is a thing that has not happened
# to them: "i saw on the news theres a big storm coming", "i heard theres a storm on the way", "i
# read that the council is closing the library". The day pools asked all three how it went, and
# one of them cheered a storm warning. Two parts make the shape, and both are needed. The verb is
# one of the ways a claim reaches a person, and its object is a clause rather than a thing: what
# follows is "that", "theres", "there is" or a source ("on the news", "in the paper", "on the
# radio"). That is what keeps "i saw a film last night" and "i read the whole book" out - those
# are things done, with an object, and they are the day pool's own lines.
A_ASKING_WORD = re.compile(
    r"^(?:did|do|does|have|has|had|are|is|was|were|can|could|would|will|should|shall|"
    r"what|whats|how|why|when|where|who|which|any)\b", re.I)
A_REPORTED_NOT_LIVED = re.compile(
    r"\b(?:i|we)\s+(?:saw|seen|heard|read|watched)\s+"
    r"(?:that\b|there(?:'s|s| is| are)\b|on\s+the\s+\w+|in\s+the\s+\w+|"
    r"the\s+\w+|"
    r"somebody\b|someone\b|they\b)|"
    r"\b(?:on|in)\s+the\s+(?:news|paper|radio|telly|local news)\b|"
    r"\bthey\s+say\b|\bive\s+been\s+told\b|"
    # The same claim, passed on by one person: "my mate says theres a storm coming". A
    # suggestion ("my mum said i should go") is a different reading and has already been
    # answered above, so what is left here is the claim with a clause after it.
    r"\b(?:says|said|told\s+me)\s+(?:that\b|there(?:'s|s| is| are)\b)", re.I)
# The half of it that can be acted on here is the weather, because a wind is the one thing in a
# warning that finds what is already loose. The words are the outdoor ones: a "storm in a teacup"
# and a "flood of forms" are not weather, so the noun has to be a plain one.
# The everything-else pool is written for a change, a closure or a charge - the reports that come
# as "what it covers, from when" - so a line is only sent to it when it is about one of those. A
# report of something new ("my sister told me theres a new cafe") has no dates in it to look up,
# and it keeps whatever the reading above already gave it.
A_NEWS_IS_A_CHANGE = re.compile(
    r"\b(?:clos(?:e|es|ed|ing|ure)|cancel\w*|chang(?:e|es|ed|ing)|charg(?:e|es|ed|ing)|"
    r"rules?|ban(?:s|ned|ning)?|cuts?|ris(?:e|es|ing)|increas(?:e|es|ed|ing)|delay\w*|"
    r"roadworks?|strikes?|walkout|fees?|prices?|tax(?:es)?|fines?|shut|"
    r"new\s+(?:rules|charges|prices|fares)|from\s+(?:monday|next\s+week|january|april))\b",
    re.I)
A_NEWS_IS_WEATHER = re.compile(
    r"\b(?:storm|storms|gale|gales|wind|winds|windy|rain|snow|ice|sleet|flood|floods|"
    r"freeze|freezing|frost|heatwave|thunder|lightning|hurricane|tornado|weather)\b", re.I)


def _a_report_from_elsewhere(clean):
    """The pool for a thing the person has only been told about, or None.

    Read where the day pool would answer, so a line with a reading of its own never reaches it.
    The weather half and the everything-else half are different jobs - the local forecast and the
    loose things outside, against the body that said it and the dates one line down - so they are
    two pools and the weather words choose.
    """
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return None
    # The source words are enough to read a report by ("heard it on the news"), so a line that
    # opens on a question word is told apart first: "did you see the storm on the news" asks the
    # bot something and is answered by the reading for the bot itself, not by a pool about the
    # weather.
    if A_ASKING_WORD.match(text):
        return None
    if not A_REPORTED_NOT_LIVED.search(text):
        return None
    if A_NEWS_IS_WEATHER.search(text):
        return A_NEWS_OF_WEATHER
    if A_NEWS_IS_A_CHANGE.search(text):
        return A_NEWS_OF_SOMETHING_ELSE
    return None


def _a_small_day_shape(clean):
    """True for the shape of a short, flat account of a day of the person's own.

    The shape only: a subject, a past doing, short enough to be one thing, and none of the things
    that already have a reading above (a name, a state, a result that came out wrong, a plan that
    fell through, a confession, a symptom, a mishap, a thing that went wrong). What the line
    feels like is read by `_a_small_day`, so the same shape can be answered warmly when it went
    well and met when it went badly.
    """
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return False
    if len(text.split()) > 14:
        return False
    # Something going on now is not a day that is over; see `A_BEING_DONE_NOW`.
    if A_BEING_DONE_NOW.search(text):
        return False
    # A thing somebody else decided is not a day somebody spent; see `A_DECISION_NOT_A_DAY`.
    if A_DECISION_NOT_A_DAY.search(text):
        return False
    # A wish is not a day somebody had either; see `A_WISH`.
    if A_WISH.search(text):
        return False
    # A report of an attempt at somebody is the follow-up to a trouble ("i asked him nicely
    # twice"), not a day out, and it is read here so both readings of this shape leave it alone.
    if AN_ATTEMPT_AT_SOMEONE.search(text):
        return False
    # Finding out that somebody close has lied, cheated or hidden money is not a flat day of the
    # person's own: "i found out hes been lying" was answered "How was it, overall?" and "i found
    # out shes been hiding money" "Sounds alright. Anything good in it?" - the one reply nobody
    # forgives, and the same for "turns out hes been texting his ex". The news is the wrongdoing,
    # so it goes to the pools that meet bad news.
    if A_BETRAYAL_FOUND_OUT.search(text):
        return False
    if _a_day_of_someone_else(text):
        return False
    if not DAY_PAST.search(text) and not _a_thing_happened(text):
        return False
    if not (A_DAY_SUBJECT.search(text) and PAST_DOING.search(text)):
        return False
    # A day marker, or a line short enough to be one thing ("i got my hair cut"). The long shape
    # without a marker is a story, and a story has a reading of its own above.
    if not DAY_PAST.search(text) and len(text.split()) > 10:
        return False
    if NOT_A_DAY_DONE.search(text) or NOT_A_DAY_SAID.search(text):
        return False
    # A confession is not a day that happened to someone: "i lied to my friend" is filed by the
    # store like any other line and came back as a receipt, which the hook in `_reply_for` turns
    # into the day pool's "Sounds alright. Anything good in it?".
    if _a_thing_they_regret(text):
        return False
    # A colour or a swelling is a symptom, not an account of a day, and the pool below is a warm
    # question about a day that went fine: "i had a red patch on my arm yesterday" was answered
    # "Good to hear. What was the best bit?" because "had" was a past doing and "red" was the only
    # other thing read. Written as the shape a symptom takes - two words that belong together - so
    # "i got a red dress in the sale" is still the day it sounds like.
    if A_SYMPTOM_PHRASE.search(text):
        return False
    # "i was in hospital yesterday", "i had a fall": a day with something wrong in it is the
    # trouble and feeling pools' line, and they come before this one anyway.
    if NEGATIVE_LINE.search(text) or HARM_NAMED.search(text):
        return False
    # A crash or a burglary said flat is the same shape as a haircut: "we got burgled last night"
    # is a subject, a past tense and a day marker. What tells them apart is the thing itself, so
    # it is read before the pool is reached rather than left to the mood, which reads a burglary
    # as neutral.
    if A_DAY_WENT_WRONG.search(text):
        return False
    # A mishap is the careful reading's line even though nothing in the sentence is a word for
    # harm: "i got glass in my foot" and "my husband rolled off the bed" were both asked how the
    # rest of it went, and a cheerful question about a day is the one reply nobody wants after one
    # of those. Read off the whole line, so a mishap in a longer account of the day still counts,
    # and by shape rather than by body word, because "i got my hair cut" names a cut and is a day.
    # A fall that is over ("last summer", "nearly", "but hes ok") keeps the day question - it is
    # the story of a day and asking its best bit is what a friend does.
    if _a_mishap_to_ask_about(text):
        return False
    # "i was in hospital yesterday", "i had a fall": a day with something wrong in it is the
    # trouble and feeling pools' line, and they come before this one anyway.
    if A_BAD_THING_NAMED.search(text) or A_HAND_OUT.search(text):
        return False
    # A name is not an afternoon's work, a state is not a doing, and a result that came out wrong
    # or a plan that fell through is the same news as a thing gone wrong: each has a pool of its
    # own above, and the cheer is a question about a day.
    if A_NAME_IS_NOT_A_DAY.search(text):
        return False
    # A thing they have only been told about is not a day they had, and every day pool here -
    # the cheer, the flat question, the one that meets a bad day - asks about a day. "i saw on
    # the news theres a big storm coming" was answered "Good to hear. What was the best bit?"
    # because "saw" is a past doing and the storm is the only other thing read; the reading just
    # above `_a_small_day` has the reply for it, and this is what keeps the day pools off it when
    # the mood is not neutral.
    #
    # It has to be the whole reading, not the cue alone: `the \w+` is in A_REPORTED_NOT_LIVED to
    # carry "i saw the storm on the news" (the news as the body that said it), and on its own it
    # also reads "the final", "the match", "the kids" and "the doctor" as a source - so a real day
    # of theirs was stood down and fell to the receipt ("we watched the final together" ->
    # "Got it. Is there anything you'd like a hand with?"). The reading is the thing that decides,
    # because it is the thing that knows a change or the weather is on the other end of the line.
    if _a_report_from_elsewhere(text) is not None:
        return False
    if _a_state_of_theirs(text):
        return False
    if RESULT_WENT_WRONG.search(text) or PLAN_THAT_FELL_THROUGH.search(text):
        return False
    return True


def _a_bad_time_told(clean, memory=None):
    """The day pool's own shape, read as a day that went badly: "we had a row last night",
    "we had a strange day at work", "ngl ive bin knackered all week", "were gutted when it
    happened".

    With the cheer taken away from a bad feeling these were left to the floor ("I'm listening -
    say more if it helps"), which is the line a person gets when nothing in what they said was
    heard - and the floor is right under this one, so a small pool here is the whole of the help
    available: one question about the day they have just told you about. The test is the reading
    the rest of the bot already makes, in either of the two ways it makes it: the mood of the
    whole line, or the words this file already keeps for a day gone wrong.
    """
    if not _a_small_day_shape(clean):
        return False
    text = " ".join(str(clean or "").lower().split())
    # A harm, a crash or a burglary is the trouble pools' line, and they come before this one.
    if NEGATIVE_LINE.search(text) or HARM_NAMED.search(text) or A_DAY_WENT_WRONG.search(text):
        return False
    if ((memory or {}).get("understood") or {}).get("polarity") == -1:
        return True
    # The detail of a day the person has already said went badly: "sorry, bad day" then "sorry,
    # it was the meeting". The words below are for a day named in this line, and the meeting is
    # not one, so without this the detail of a bad day fell to the store's read-back or the floor
    # - a colder reply than the cheer it replaced.
    if _a_detail_of_a_bad_day(memory, text):
        return True
    # A doing of the person's own where only the way it went says so ("i ate badly all week",
    # "i drank too much last night", "i skipped the gym all week"): the line names no bad day, so
    # the words below miss it and the cheer asked what the best bit of it was. It is the same day
    # gone wrong, said through the doing, and the pool it reaches is the one that asks about it.
    if A_DOING_GONE_BADLY.search(text) or (A_THING_SKIPPED.search(text)
                                          and not A_MEAL_SKIPPED.search(text)):
        return True
    # The words are A_DAY_SAID_BADLY and not the wider BAD_DAY_ANYWAY list. That list is only
    # ever subtractive - it takes a cheer away and leaves the line to whatever answers next - so
    # it can afford "waited", "late for" and "two hours"; here the words decide what the bot
    # says, and "i watched a film for two hours" was told "That is a nuisance" for a film.
    return bool(A_DAY_SAID_BADLY.search(text))


def _a_day_asked_without_a_cheer(clean, memory=None):
    """True for the day pool's shape where a word in the line says the day went wrong somewhere.

    Two lists, two jobs. A_DAY_SAID_BADLY is narrow because its words choose the sympathetic pool
    (`_a_bad_time_told`). BAD_DAY_ANYWAY is deliberately wide, because it only ever took the cheer
    away and left the line to whatever answers next - and on today's main what answers next is the
    floor ("I'm listening - say more if it helps"), which is worse than the cheer it replaced:
    "we had a strange day at work" went from "Good to hear. What was the best bit?" to the floor.
    So the wide list gets a question with no presumption in it either way, which is true of a
    strange day at work and of a fish that got gutted ("gutted" is in the list for the row it
    usually appears in).
    """
    if not _a_small_day_shape(clean):
        return False
    text = " ".join(str(clean or "").lower().split())
    # A harm, a crash or a burglary is the trouble pools' line, and they come before this one.
    if NEGATIVE_LINE.search(text) or HARM_NAMED.search(text) or A_DAY_WENT_WRONG.search(text):
        return False
    # A bad day already has the sympathetic pool, and a day the bot has just asked about does not
    # want the same question twice.
    if _a_bad_time_told(clean, memory):
        return False
    if _just_asked_about_the_day(memory):
        return False
    return bool(BAD_DAY_ANYWAY.search(text))
