"""Real emergencies get a plain, short reply that points to real help.

The rule of this module: answer only when the line describes something that is happening now
and can kill or seriously harm someone. Everything else passes (returns None), so ordinary
lines that merely sound alarming ("this deadline is killing me", "I cut my finger chopping
onions", "I'm dying to see that film") are answered by whichever module fits them.

Recognition is data, not a list of exact sentences: each case has phrase patterns over a
normalised line (lower case, chat-speak folded, apostrophes standardised), plus guards for the
ways the same words are *not* an emergency:

- figurative use ("killing me", "dying to", "dead tired", "starving"),
- hypotheticals and fiction ("what if someone", "for a story", "in a novel"),
- questions about the world ("what causes chest pain", "suicide rate"),
- mild variants ("can't breathe through my nose", "food poisoning", "fire alarm beeping").

A minor injury (a cut finger, a small scald, a nosebleed) is not an emergency either, but it
does want a useful answer, so it gets a short first-aid reply instead of an alarm.
"""
import re

from ..compose import pick
from ..compose.fallback import BLACKED_OUT_SIGHT
try:  # the reading of a dream, so a dream of the thing is not the thing
    from ..memory import dream as _dream
except Exception:  # noqa: BLE001 - a reading that cannot be imported just adds no rule
    _dream = None
from ..understanding import respell_urgent
from ..understanding import lexicon
# The words the reader already repairs are these; a word of them is never replaced by the
# splice below, or safety would repair a different word than the rest of the bot reads.
from ..understanding.normalize import LEXICON, glued_words, said_apart
from ..understanding.lexicon import MISSPELLINGS
# Tables that only this module reads, moved out because one file may not pass 1 MiB.
from .safety_cards import (
    ALLERGY_AIRWAY,
    ALLERGY_FACE,
    ALLERGY_FOOD,
    ALLERGY_OFF,
    BLEEDING_SMALL,
    BODY,
    BREATH_BARE,
    BURNT_BODY_VERB,
    BURN_ON_BODY,
    BURN_VERB,
    CRUSH,
    CRUSH_HARD,
    CRUSH_OFF,
    CUT_BODY_PART,
    CUT_ON_BODY,
    CUT_ON_THROAT_BODY,
    FOOD_WORDS,
    HEAT_BREATH_RED,
    HEAT_CAUSE,
    HEAT_NOT_WEATHER,
    HOT_COMFORT,
    HOT_SURFACE,
    HOT_WAX_ON_BODY,
    LAUGH_BREATH_RED,
    LAUGH_OTHER_PERSON,
    LAUGH_TAKES_BREATH,
    LAUGH_WORD,
    MINOR,
    NOT_A_PET_LINE,
    NOT_BURN_ON_BODY,
    PET_APPOSITIVE,
    PET_APPOSITIVE_SUB,
    PET_BREATH,
    PET_BREATH_NOW,
    PET_CANT_SETTLE,
    PET_EFFORT,
    PET_NAIL,
    PET_OWNS_THE_WOUND,
    PET_WOUND,
    PET_PASSES_BLOOD,
    PET_ANIMAL_HURT,
    PET_OWNS_A_THING,
    HUMAN_OWN_INJURY,
    RING_STUCK,
    SCORCHED_A_PERSON,
    SIGHT_EVER,
    SIGHT_LIFE_REPLIES,
    STING_WORDS,
    TOOTH_CHIPPED,
    TOOTH_OUT,
    WAX_BODY,
    WEIGHT_JOINT,
    _PET_APPOSITIVE,
    _PET_DAMAGE_THING,
    MY_OWN_PART,
    PET_WEAK,
)
# The tables for the arms below. `safety.py` has to stay under the publisher's 1 MiB, so the
# patterns live in safety_tables.py with the rest of them and are imported by name.
from .safety_tables import (SELF_HARM_OWN_PART, POISON_SAID, A_HURT_OF_A_BODY_PART,
                            A_WORKOUT_CUE, A_PLAN_SAID, A_PLAN_ORDINARY)
from .safety_cards import (BITE_DONE, BAT_BITE, WILD_BITE, ALLERGY_NOW, ALLERGY_SIGN_NAMED,
                            COUNTERFACTUAL_WISH, COUNTERFACTUAL_IDIOM, STRUCK_BY_A_VEHICLE,
                            STRUCK_MY_BIKE, NEAR_HIT_ON_A_ROAD,
                            NEAR_HIT_ON_A_ROAD_PLACE,
                            STRUCK_BY_A_VEHICLE_NOT, EFFORT_BEFORE,
                            EFFORT_DIED, COME_OFF_IT, EFFORT_DOING, EFFORT_NOT_AN_ACCIDENT,
                            INSECT_BITE, INSECT_BITE_NEEDS_A_LOOK, TICK_BITE, TICK_ALREADY, GRATER_CUT, PERSON_HANGING, HEAD_OUT_COLD, STRUCK_NOT_NOW, SELF_HARM_HABIT, HEAL_TIME, HEAD_REPLIES, HUMAN_BITTEN, HIT_IN_FUN_HARD, WATER_DANGER, MILD, SCALD, HYPERBOLE_WISH, PURSUIT_PLACE_HOME, INJURY_HOW, LIPS_SWELL_BARE, DOG_ATTACK, HYPO_SIGN, SUGAR_READING_LOW, SELF_HARM_REPEAT_CAUSE, FOLLOW_UP, LIMP_ONGOING, SHOULD_I_CALL, NOT_JUST_A_NEAR_THING, LIMP_PERSON, PURSUIT_FINE, LIMB_IS_A_THING)

# The four effort patterns are compiled here, not in the table file, so the cards stay plain data
# with no `re` of their own - one import, one place, nothing for a rebase to double.
_EFFORT_BEFORE = re.compile(EFFORT_BEFORE)
_EFFORT_DIED = re.compile(EFFORT_DIED)
_COME_OFF_IT = re.compile(COME_OFF_IT)
_EFFORT_DOING = re.compile(EFFORT_DOING)

PRIORITY = 9000  # above the answer modules: an emergency is never outvoted

EMERGENCY_NUMBERS = "999 or 911"


def _one(verb, who):
    """'they stop breathing' for one person: 'she stops breathing'."""
    if verb in ("are", "were", "have", "do"):
        verb = {"are": "is", "were": "was", "have": "has", "do": "does"}[verb]
    else:
        verb += "es" if verb.endswith(("sh", "ch", "s", "x", "o")) else "s"
    return who + " " + verb


from .safety_tables import (
    ABOUT_THE_SPEAKER,
    ABUSE_BENIGN_REASON,
    ABUSE_BLOW,
    ABUSE_BUTTONHOLED,
    ABUSE_CHILD_REFUSAL,
    ABUSE_EMPLOYER_REFUSAL,
    ABUSE_FINE_ANIMAL,
    ABUSE_FINE_PLACE,
    ABUSE_HANDS_ON,
    ABUSE_KIDS_AT_HOME,
    ABUSE_KIDS_CARD,
    ABUSE_PARENT_REFUSAL,
    ABUSE_PARENT_REFUSAL_HARD,
    ANY_REFUSAL_TO_GO,
    A_HAND_ON_THE_PERSON,
    ABUSE_PLAY,
    ABUSE_PLAY_HARD,
    ABUSE_QUARREL,
    ABUSE_ROOM_CARD,
    ABUSE_ROOM_FAMILY,
    ABUSE_SCARED,
    ABUSE_SCARED_REPLY,
    ACCIDENT,
    ADULT_HIT,
    AFTER_EXERCISE,
    AGE_PERSON,
    ALARM_NUISANCE,
    AMBULANCE_CASES,
    ANIMAL_KICK,
    APPLIANCE_SMOKE,
    ASKS_ABOUT_THE_INJURY,
    ASKS_GO_BARE,
    ASKS_IF_CALL,
    ASKS_IF_GOING,
    ASK_CALL_REPLIES,
    ASK_GO_REPLIES,
    ASPIRIN_REPLY,
    A_BREATHER,
    A_FOLLOW_UP_ABOUT_THE_INJURY,
    A_GROWN_AGE,
    A_PERSON,
    A_REAL_DANGER,
    A_WISH_OR_TALK_OF_IT,
    BABY_FELL,
    BABY_FELL_OFF,
    BABY_FELL_RED,
    BABY_FELL_SURFACE,
    BATTERY_BULGE,
    BATTERY_FIRE,
    BITE_ON_ANIMAL,
    BLACKOUT_A_THING,
    BLACKOUT_BREATH,
    BLACKOUT_EFFORT,
    BLACKOUT_FLOOR,
    BLACKOUT_OFF,
    BLACKOUT_REPEAT,
    BLACKOUT_SOMEONE_DOWN,
    BLEACH_MIX,
    BLEACH_MIX_Q,
    BLEEDING,
    BLIND_CORD,
    BLISTER_CAUSE_BURN,
    BLISTER_STATE,
    BLISTER_STATE_REPLIES,
    BLOW_ON_ME,
    BLUE,
    BLUE_CLOTH,
    BLUE_COLD_CAUSE,
    BLUE_FINE,
    BLUE_FOOD,
    BLUE_OTHER_PERSON,
    BLUE_PERSON_SUBJECT,
    BLUE_STRONG,
    BLUE_TINGE,
    BODY_PART,
    BONE_ORDINARY,
    BONE_PAST,
    BONE_THROAT,
    BREATH_CAUSE,
    BREATH_CAUSE_RED,
    BREATH_EFFORT,
    BREATH_EFFORT_RED,
    BREATH_LAUGH,
    BREATH_LAUGH_REPLY,
    BREATH_PAST_OVER,
    BREATH_RED,
    BREATH_REST,
    BREATH_SHORT,
    BURNT_FOOD,
    BURNT_SELF,
    BURN_MARK_ON_A_BODY,
    CALL_HAS_A_SIGN,
    CALL_HELP_REPLY,
    CASE_WORDS,
    CHEM_WORD,
    CHEST_ASKED,
    CHEST_EFFORT,
    CHEST_IN_A_HAND,
    CHEST_IN_A_HAND_TAIL,
    CHEST_SLOW,
    CHEST_SPREADING,
    CHEST_URGENT,
    CHEST_WORK,
    CHILDHOOD_FIT,
    CHILD_FEVER_NOT_EATING,
    CHILD_FEVER_RED,
    CHILD_GROWN,
    CHILD_SCHOOL_AGE,
    CHILD_YOUNG,
    CHOKE_AIR_OK,
    CHOKE_NOT_PERSON,
    CHOKE_OVER,
    CHOKE_PERSON,
    CHOKE_PREVENT,
    CHOKE_RED,
    CHOKE_SETTLED,
    CHOKE_STILL_RED,
    CHRONIC_BREATH,
    CLEANABLE_SURFACE,
    COLD_ILLNESS,
    COLLAPSE_HINT,
    CONFUSED_THING,
    COUGH_BLOOD,
    CO_GOING_OFF,
    CO_LEAK,
    CO_SIGNS,
    CO_TEST,
    CPR_BABY_SCENE,
    CPR_CHILD,
    CPR_CHILD_SCENE,
    CPR_HOW,
    CPR_HOWTO,
    CPR_HOW_BABY,
    CPR_HOW_CHILD,
    CPR_NOT_EFFORT,
    CPR_NO_PULSE_NOW,
    CPR_ROOM_EMPTY,
    CPR_ROUGH,
    CPR_START,
    CPR_STOP,
    CPR_STOP_REPLY,
    CPR_WHEN_ALIVE,
    CRISIS_PLAN_CARRY,
    CRISIS_PLAN_ORDINARY,
    CRISIS_PLAN_REPLY,
    CRISIS_PLAN_SAID,
    CRISIS_WORD,
    CUT_NOT_STOPPING,
    DAY_TOTAL_SIGN,
    DAY_TOTAL_WORD,
    DENTAL_WORDS,
    DETAIL_AFTER_ESCALATION,
    DEVICE_BURNING,
    DEVICE_OLD,
    DIE_OF_THE_FEELING,
    DISTRESS_BESIDE_IT,
    DOG_HABIT,
    DOG_MOUTHING,
    DOG_SELF_BITE,
    DOSE_AMOUNT,
    DOSE_ASKED,
    DOSE_COURSE,
    DOSE_COURSE_KEEP,
    DOSE_WORDS,
    DRINK_WORDS,
    DROWNED_THING,
    DROWNING_HYPERBOLE,
    DRUG_NAME,
    EDGE_OF_A_DROP,
    EFFORT_AFTER,
    EFFORT_ANYWHERE,
    EFFORT_BENIGN,
    EFFORT_HEART_CLUSTER,
    EFFORT_PATTERN,
    EFFORT_RED_HEART,
    EFFORT_TOO_LONG,
    ELECTRIC_BURN,
    ELECTRIC_FINE,
    ELECTRIC_SHOCK_DEFINITION,
    ELECTRIC_SHOCK_DOWN,
    END_IT_MEANS,
    END_IT_WITH_A_THING,
    END_IT_WITH_NOUN,
    END_MEANS_OTHER,
    END_THING,
    EXERTION,
    EXERTION_CLASS,
    EXERTION_SMALL,
    EYE_CHEM,
    EYE_FINE,
    FAINT_STORY,
    FALL_ANSWERED,
    FALL_CHECK_OFF,
    FALL_CORE,
    FALL_FINE,
    FALL_HIP,
    FALL_NOW,
    FALL_PAST,
    FALL_RED,
    FALL_REPEAT,
    FALL_WORD_IDIOM,
    FEMALE_WORDS,
    FEVER_ASK,
    FEVER_RASH_FINE,
    FEVER_REPORT,
    FICTION_NOW,
    FIRE,
    FIRE_DRILL,
    NEAR_FIRE,
    NEAR_FIRE_OVER,
    NEAR_THING_OVER,
    FIRE_ELSEWHERE,
    FIRE_NOW,
    FIRE_OUT,
    FIRE_SCALE,
    FITTING_IN,
    FITTING_MANNER_TAIL,
    FIT_ALL_BETTER,
    FIT_CASES,
    FIT_ROUTINE,
    FIT_STILL_RINGS,
    FIT_THIS_WEEK,
    FLAMES,
    FLOPPY_RED_FLAG,
    FLOPPY_SLEEPY,
    FLOPPY_THING,
    FOLLOW_UP_ANCHOR,
    FOLLOW_UP_MORE,
    FOOD_CUT,
    FORAGED_EATEN,
    FORAGED_FINE,
    FRICTION_WORD,
    FRIGHTENED,
    FRIGHTENED_REPLY,
    GARMENT,
    GASPING_THIRST,
    GASP_FINE,
    GASP_RED,
    GAS_LEFT_ON,
    GAS_ON_NOT_RUNNING,
    GAS_ON_YOU,
    GAS_PAST,
    GAS_SMELL,
    GIVING_UP_GROUP,
    GIVING_UP_HELD_ON,
    GO_IN_NOT_ABOUT_IT,
    GO_IS_A_CALL,
    GRUNTING_FINE,
    HAIR_SCORCH,
    HAIR_SCORCH_ANSWER,
    HANGED_LONG_AGO,
    HANGING,
    HARD_TO_WAKE,
    HEADACHE_BAD,
    HEADACHE_STORY,
    HEADACHE_SUDDEN,
    HEAD_BANG,
    HEAD_KNOCKOUT,
    HEAD_RED,
    HEAL_WORDS,
    HEARD_ASSAULT,
    HEAT,
    HELD_CRISIS_DETAIL,
    HELD_CRISIS_OFF,
    HELP_ARRIVED,
    HELP_SOMEONE,
    HIT_IN_FUN,
    HIT_THE_LAUGH_IS_HIS,
    HOW_LONG,
    HOW_TO_TREAT,
    HUMAN_TOO,
    HYPERBOLE_BLOCK,
    HYPO_HOW_KNOW,
    HYPO_QUESTION,
    HYPO_STRONG,
    HYPO_STRONG_OTHER,
    INJURY_WORDS,
    INTRUDER,
    KICKED_PERSON,
    LIMP_LONG,
    LIMP_MECHANISM,
    LIMP_OTHER_LIMB,
    LIMP_SOMEBODY_ELSE,
    LIPS_COLD,
    LIPS_SWELL,
    LIPS_SWELL_BARE_OFF,
    LIPS_TINGLE,
    LIPS_TINGLE_FOOD,
    LIPS_TINGLE_OFF,
    LIPS_TINGLE_RED,
    LOCKED_IN_RISK,
    LOOKS_REAL,
    LOSS_SAID,
    LOSS_SUBJECT,
    MACHINE,
    MEAL_BREATH,
    MEDICINE,
    MENINGITIS_OTHER,
    MILD_BODY_SIGN,
    MILD_CHOKE,
    MILD_PRODUCT_SMALL,
    MILD_SWALLOWED,
    MORNING_ROUTINE,
    MOUTH_BLEED_NOW,
    NAMED_SICK_FINE,
    NEWBORN,
    NIGHT_BREATH_OTHER,
    NIGHT_BREATH_PAST,
    NIGHT_BREATH_RED,
    NOSE_RED,
    NOT_A_WOUND_OFF,
    NOT_NOW,
    NOT_NOW_FICTION,
    NOT_STOPPING,
    OBJECT_IN_HEAD_THING,
    OLDER_CHILD_NAMED,
    OLD_FALL_FINE,
    OLD_FALL_NOT,
    OLD_PERSON,
    OLD_TIME,
    OTHER_RISK,
    OTHER_SELF_HARM,
    OUT_COLD_ASLEEP,
    OUT_COLD_PERSON,
    OUT_COLD_REPLY,
    OVERDOSE_DRUG,
    OVERDOSE_FOOD,
    OVERDOSE_OF_A_TREAT,
    OWN_CRY,
    OWN_INJURY,
    OWN_INJURY_IN_MY_CARE,
    OWN_INJURY_QUESTION,
    OWN_LIMB_AT_AN_ANGLE,
    PALE_EFFORT_RED,
    PALE_EXERTION,
    PALE_HEAT,
    PALE_SECOND,
    PAN_FIRE,
    PARENT_REFUSAL_BLOW,
    PAST_ATTEMPT_NOT,
    PAST_WISH,
    PAST_WISH_NOT,
    PERSON,
    PERSON_AS_ATTACKER,
    PERSON_BURNT,
    PET_ALL_RIGHT,
    PET_ANY,
    PET_GASP_EXPLAINED,
    PET_GASP_FINE,
    PET_GASP_RED,
    PET_NAMES,
    PET_PAST,
    PET_RESPOND_AT,
    PET_TOOTH,
    PLAYFUL_HIT,
    POO_BLACK,
    POO_BLOOD,
    POO_FINE,
    PREGNANCY_WORDS,
    PUNCTURE,
    PUSHED_AWAY,
    PUSHED_AWAY_BUT_SOMETHING_ELSE,
    PUSHED_AWAY_REPLY,
    PUSHED_AWAY_THEN_RESTRAINT,
    RASH_FADE,
    RASH_HEADACHE_FINE,
    RASH_PRESSED,
    RAZOR_BURN,
    RECENT_FIT_FINE,
    RECENT_TIME,
    RESPOND_SENSE,
    RESTRAINT_BESIDE,
    RING_DANGER,
    RING_NOT_WORN,
    ROUTINE_REASON,
    ROUTINE_WAKE,
    SAFE_NOW,
    SAID_AS_IT_HAPPENS,
    SEIZURE,
    SEIZURE_FIGURATIVE,
    SEIZURE_STORY_GUARD,
    SELF_CUT,
    SELF_HARM_AGAIN,
    SELF_HARM_CUT_NO_OBJECT,
    SELF_HARM_DELIBERATE_ACT,
    SELF_HARM_DESERVE,
    SELF_HARM_LOOKALIKE,
    AN_ITCH_LOOKALIKE,
    SELF_HARM_NOT_EATING,
    SELF_HARM_REASON,
    SELF_HARM_SCARS,
    SELF_HARM_SCARS_NOT,
    SELF_HARM_TOPIC_OFF,
    SELF_RUMINATION,
    SELF_TALK,
    SEPSIS_SIGN,
    SHAKEN,
    SHAKEN_REPLY,
    SHOCK_ANY,
    SHORT_OF_BREATH,
    SHOT,
    SHOT_FINE,
    SIGHT_A_WHILE,
    SLUR_RED_BESIDE,
    SLUR_THICK,
    SMALL_CHILD,
    SMALL_CHILD_LASH_REPLIES,
    SMOKE_IS_A_SMELL,
    SNAKE_LOOKALIKE,
    SOCKET_OBJECT,
    SOCKET_THING_FINE,
    SOFT_BLEED_OFF,
    SOMEONE_ELSES_DESPAIR,
    SOMEONE_ELSE_OWN,
    SOME_OF_IT,
    SPELL_RED,
    SPIKED,
    SPINE_BACK_WORK,
    SPINE_BREAK,
    SPOKEN_ATTEMPT_UNDATED,
    STIFF_FINE,
    STIFF_NECK,
    STILL_GOING,
    STING_SETTLED,
    STOOL_LONG,
    STRANGLED_SELF,
    STRANGLE_THING_SUBJECT,
    STROKE_HAND,
    STROKE_HAND_BESIDE,
    STROKE_HAND_CHRONIC,
    STROKE_HAND_HARD,
    STROKE_WEAK,
    STROKE_WEAK_OFF,
    STUCK_MACHINE,
    SUICIDE_ABOUT_A_THING,
    SUICIDE_TOPIC,
    SWALLOWED_BAD_REPLY,
    SWALLOWED_BAD_SELF,
    SWALLOWED_ORDINARY,
    SWALLOWED_SELF,
    SWALLOW_GONE_OFF,
    SWALLOW_GONE_RED,
    TALK_HABIT,
    TESTIS_LUMP,
    THING_BURNT,
    THING_BURNT_WORDS,
    THING_THAT_IS_SUICIDE,
    THIRD_PERSON_ACTOR,
    THROAT_TIGHT_CAUSE,
    THROAT_TIGHT_EFFORT,
    THROAT_TIGHT_RED,
    TINY_AGE,
    TINY_AGE_FINE,
    TOOK_OUT_OF,
    TOOTH_OUT_FINE,
    TORSION,
    TORSION_FINE,
    TORSION_ONSET,
    TRAPPED_HELD_BY_A_PERSON,
    TRAPPED_VEHICLE_NOT_NOW,
    TYPED_TYPOS,
    VEHICLE_BURNING_SMELL,
    VEHICLE_BURNING_SMELL_HARD,
    VEHICLE_EXHAUST,
    VEHICLE_FIRE,
    VEHICLE_FIRE_OVER,
    VIOLENT_THREAT,
    VISIT_OR_TIME,
    WAKE_RED,
    WAKE_UP_SOMEONE,
    WATER_DROWNING_FINE,
    WATER_DROWNING_NOW,
    WATER_FINE,
    WATER_HEAD_FEAR,
    WATER_HUMAN,
    WATER_IN_NOW,
    WATER_NOT_A_PERSON,
    WATER_PERSON_TOO,
    WATER_SELF,
    WATER_THING_DROPPED,
    WATER_URGENT,
    WEIGHT_HIP,
    WEIGHT_LONG,
    WEIGHT_OFF_FEET,
    WENT_BLUE_FINE,
    WENT_BLUE_IDIOM,
    WHEN_HELP_COMES,
    WHEN_HELP_REPLY,
    WHOLE_BODY_RED_FLAG,
    WISH_BY_MODAL,
    WISH_DEAD_HYPERBOLE,
    WISH_DEAD_PLACE,
    WISH_DEAD_WHEN,
    WISH_NAMED,
    WITHDRAWAL_ALONE_AT_HOME,
    WITHDRAWAL_ASK_DANGER,
    WITHDRAWAL_DANGER,
    WITHDRAWAL_HAIR_OF_THE_DOG,
    WITHDRAWAL_HALLUCINATION,
    WITHDRAWAL_NAMED,
    WITHDRAWAL_NOT_ALCOHOL,
    WITHDRAWAL_ROUTINE,
    WITHDRAWAL_SENSES_FINE,
    WITHDRAWAL_STOP,
    WITHDRAWAL_STRONG,
    WITHDRAWAL_SYMPTOM,
    WONT_COME_ROUND,
    WORDS_OUT_OCCASION,
    WOUND_STREAK,
    WOUND_STREAK_FEVER,
    WORLD_QUESTION,
    _AGREEMENT,
    _AWAY_TAIL,
    _DENIED,
    _FLAT_WISH_HOW,
    _PERSON,
    _SMELLY_THING,
    _SMOKE_THING,
    _STRUCK_RELATIVE,
    _THIRD,

)
MALE_WORDS = (r"\bdad\b", r"\bfather\b", r"\bhusband\b", r"\bboyfriend\b", r"\bbrother\b",
              r"\bson\b", r"\blittle\s+boy\b", r"\bboy\b", r"\buncle\b", r"\bgrandad\b",
              r"\bgrandpa\b", r"\bgrandfather\b", r"\bnephew\b", r"\bhe\b", r"\bhim\b")
# The chest reply talks to the patient; when the patient is someone else it has to point at them.
_TO_PATIENT = ((r"\bdon't\s+drive\s+yourself\b", "don't let {obj} drive"),
               (r"\bSit\s+and\s+stay\s+still\b", "Keep {obj} sitting and still"),
               (r"\bSit\s+upright,\s+stay\s+calm,", "Keep {obj} sitting upright and calm,"))
SHE = ([(p, v.format(obj="her")) for p, v in _TO_PATIENT]
       + [(r"\bthey're\b", "she's")] + [(p, _one(v, "she")) for p, v in _AGREEMENT]
       + [(r"\bthey\b", "she"), (r"\bthem\b", "her"), (r"\btheir\b", "her"),
          (r"\btheirs\b", "hers"), (r"\bthemselves\b", "herself")])
HE = ([(p, v.format(obj="him")) for p, v in _TO_PATIENT]
      + [(r"\bthey're\b", "he's")] + [(p, _one(v, "he")) for p, v in _AGREEMENT]
      + [(r"\bthey\b", "he"), (r"\bthem\b", "him"), (r"\btheir\b", "his"),
         (r"\btheirs\b", "his"), (r"\bthemselves\b", "himself")])


# "my baby has blood in his poo" is about the baby, and nothing in the baby words says which
# pronoun it is. The possessive on the same line is the only thing that does.
CHILD_ANON = (
    r"\b(?:my|our|her|his|their|the)\s+(?:baby|babies|toddler|newborn|infant|child|kid|"
    r"little\s+one|little\s+lad|little\s+girl|little\s+boy|\d+\s*(?:year|month)s?\s*old)\b",
)


def _person(line):
    """'she', 'he' or None when the line names no single other person."""
    # A baby, a toddler or "my 3 year old" is another person, and the only word that says which
    # is the possessive: "my baby has blood in her poo" is about her, not about the parent.
    if _matches(CHILD_ANON, line):
        her = _matches((r"\bher\b", r"\bshe\b"), line)
        if her and not _matches((r"\bhis\b", r"\bi\b", r"\bmy\b", r"\bme\b"), line):
            return "she"
        if _matches((r"\bhis\b",), line) and not her:
            return "he"
    woman = _matches(FEMALE_WORDS, line)
    man = _matches(MALE_WORDS, line)
    if woman and not man:
        return "she"
    if man and not woman:
        return "he"
    return None


 # A line about the user themselves is answered in the second person: "i swallowed a bee" gets
# "don't make yourself sick", not "don't make them sick".
SPEAKER_IS_PATIENT = (
    r"\bi\s+(?:have\s+|just\s+|think\s+i\s+|might\s+have\s+)?(?:swallowed|gulped|ate|eaten)\b",
    r"\bi\s+(?:just\s+)?choked\s+on\b", r"\bgot\s+stuck\s+in\s+my\s+throat\b",
)

DOSE_COUNT = (r"(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
              r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
              r"a\s+couple|half\s+a\s+dozen|a\s+dozen)")
DOSE_DRUG = (r"(co[\s-]?codamol|codamol|paracetamol|acetaminophen|panadol|calpol|"
             r"ibuprofen|nurofen|brufen)")
DOSE_STATED = (
    # The verb, then the count, then the drug: "i took 6 paracetamol today", "i swallowed eight
    # tablets of paracetamol", "take 4 paracetamol".
    r"\b(?:took|taken|swallowed|downed|popped|had|ate|eaten|been\s+taking|taking|take)\b"
    r"[^.!?]{0,18}?\b" + DOSE_COUNT + r"\b[^.!?]{0,20}?\b" + DOSE_DRUG + r"\b",
    # The count with its unit: "i took 8 tablets of paracetamol today".
    r"\b" + DOSE_COUNT + r"\b\s*(?:x\s*)?(?:tablets?|pills?|capsules?|caplets?|doses?)\b"
    r"[^.!?]{0,18}?\b" + DOSE_DRUG + r"\b",
)

# The count is not there, but the amount is: a pack, a handful, a bottle.
# The count is not there either, but the mix-up is: "i took my paracetamol twice by mistake".
DOSE_DOUBLE = (
    r"\b(?:took|taken|had|swallowed)\b[^.!?]{0,25}\b" + DOSE_DRUG + r"\b[^.!?]{0,25}"
    r"\b(?:twice|two\s+times|a\s+double\s+dose|double\s+dose|again\s+by\s+mistake)\b",
    r"\b(?:twice|two\s+times|double\s+dose)\b[^.!?]{0,25}\b" + DOSE_DRUG + r"\b",
    r"\b" + DOSE_DRUG + r"\b[^.!?]{0,25}\b(?:twice|two\s+times|a\s+double\s+dose|"
    r"double\s+dose)\b",
)

# A dose just taken, with the time it was taken: the question is when the next one is.
DOSE_RECENT = (
    r"\b(?:took|taken|had|swallowed)\b[^.!?]{0,20}\b" + DOSE_DRUG + r"\b[^.!?]{0,20}"
    r"\b(?:an?\s+hour\s+ago|half\s+an\s+hour\s+ago|just\s+now|a\s+minute\s+ago|"
    r"at\s+\d|this\s+(?:morning|afternoon|evening|lunchtime|dinner))\b",
    r"\b" + DOSE_DRUG + r"\b[^.!?]{0,20}\b(?:an?\s+hour\s+ago|half\s+an\s+hour\s+ago|"
    r"just\s+now|this\s+(?:morning|afternoon|evening|lunchtime|dinner))\b",
)

DOSE_WHOLE_PACK = (
    r"\b(?:whole|full|entire)\s+(?:pack|packet|box|bottle|blister|strip)\b[^.!?]{0,25}\b"
    + DOSE_DRUG + r"\b",
    r"\b(?:handful|loads?|load\s+of|bunch)\s+(?:of\s+)?" + DOSE_DRUG + r"\b",
    r"\b" + DOSE_DRUG + r"\b[^.!?]{0,20}\b(?:all\s+at\s+once|in\s+one\s+go|"
    r"(?:whole|full)\s+(?:pack|packet|box|bottle))\b",
)

# What the packet says a day holds, in the strength the packet sells.
DOSE_LIMITS = {"paracetamol": 8, "acetaminophen": 8, "panadol": 8, "calpol": 8,
               "co codamol": 8, "co-codamol": 8, "cocodamol": 8, "codamol": 8,
               "ibuprofen": 6, "nurofen": 6, "brufen": 6}


def _dose_count(word):
    word = " ".join(word.lower().split())
    if word.isdigit():
        return int(word)
    if "couple" in word:
        return 2
    if "dozen" in word:
        return 6 if "half" in word else 12
    return DOSE_WORDS.get(word.replace("-", " "))


def _day_dose_reply(text):
    """The packet's own limit, said plainly, for a count the poisons case stood down."""
    number, drug = None, ""
    for count, word in _DAY_TOTAL_COUNT.findall(text):
        n = _DAY_TOTAL_WORDS.get(count)
        if n is None:
            try:
                n = int(count)
            except ValueError:
                continue
        number, drug = n, word
    limit, spelling = (6, "six of the 200mg tablets a day") \
        if drug in ("ibuprofen", "nurofen", "brufen") else \
        (8, "eight 500mg paracetamol tablets a day")
    if drug in ("ibuprofen", "nurofen", "brufen"):
        tail = ("Take it with food rather than on an empty stomach, and nothing else that contains "
                "it. Needing that many for more than a few days is the back to get looked at.")
    else:
        tail = ("Four hours between doses, and count anything from a cold remedy as paracetamol "
                "too. Running at the full eight for more than a few days means the pain needs "
                "looking at rather than more tablets.")
    if number is not None and number < limit:
        return "%d is inside the day's limit of %s. %s" % (number, spelling, tail)
    return "The day's limit is %s, so there is nothing more to take. %s" % (spelling, tail)


def _stated_dose(line):
    """The written answer for a dose line the poisons case has already stood down, or None.

    Main reads the count and stands the card down when it is a day's total at or under the
    packet's maximum ("i had 8 paracetamol today"), which is right - but then nothing answers the
    line, so it got the hold ("i took 6 paracetamol today") or "I'm listening". A count that is
    the packet's own limit needs saying out loud: eight 500mg tablets a day, four hours apart,
    and the cold remedy counts too.

    Nothing above the limit comes here, because the poisons case answers that with the card, and
    a child or a pet is left to it as well.
    """
    text = " ".join(line.lower().split())
    # Taken to do harm is not a dose question: it stays with the harm answer.
    if re.search(r"\bon\s+purpose\b|\b(?:to|trying\s+to)\s+(?:hurt|harm|kill)\s+myself\b|"
                 r"\bsuicid|\bwanted\s+to\s+die\b|\bkill\s+myself\b|\bend\s+it\b", text):
        return None
    if _matches((CHILD_TAKER, CHILD_WORD), line) or _matches(PET_OWN + PET_SUBJECT, line):
        return None
    # A count above the packet's maximum is the poisons card, whatever else the line says: "i had
    # 12 ibuprofen an hour ago" is an overdose, not a timing question.
    for pattern in DOSE_STATED:
        found = re.search(pattern, text)
        if not found:
            continue
        n = _dose_count(found.group(1))
        drug = " ".join(found.group(2).lower().replace("-", " ").split())
        limit = DOSE_LIMITS.get(drug)
        if n and limit and n > limit:
            return None
        break
    if _a_days_dose(line):
        return _day_dose_reply(text)
    for pattern in DOSE_DOUBLE:
        if re.search(pattern, text):
            return ("One extra dose is usually nothing to worry about: don't take any more for four "
                    "hours, and skip that one if it lands in the night. If it was more than one "
                    "extra, or you have liver trouble or drink heavily, ring 111 rather than "
                    "guessing - and never make up a missed dose by doubling the next one.")
    for pattern in DOSE_RECENT:
        if re.search(pattern, text):
            return ("That is done and inside the limit, so the only thing to keep is the gap: four "
                    "hours before the next dose, and eight tablets of 500mg in a day at most. If "
                    "you are still in pain at four hours, that is worth getting looked at rather "
                    "than topping up early.")
    return None


SWALLOWED_BAD = (
    r"\b(?:batter(?:y|ies)|button\s+battery|magnet|magnets|razor|blade|blades|glass|"
    r"pins?|needles?|screws?|nails?|toothpick|fork|wire|beads?)\b",
)


SWALLOWED_CHILD = (r"\bmy\s+(?:child|son|daughter|baby|toddler|kid|boy|girl)\b",)

# A pet on its way out is grief, and the loss module answers it better than the crisis card. It is
# only the pet that is dying: "my dog is going to die and i want to die too" is still the user.
PET_DYING = (
    r"\b(?:dog|dogs|puppy|pup|cat|cats|kitten|horse|pony|rabbit|hamster|guinea\s+pig|bird|parrot|"
    r"budgie|pet|pets)\b[^.?!]{0,30}\b(?:is\s+dying|are\s+dying|dying|going\s+to\s+die|"
    r"will\s+die|going\s+to\s+be\s+put\s+(?:down|to\s+sleep)|being\s+put\s+down)\b",
)


def _fit(reply, line, case=None):
    """The reply with its they/them/their pointing at the person the user named, when there is one."""
    if not reply:
        return reply
    if case is not None and case not in FIT_CASES:
        return reply
    who = _person(line)
    pairs = SHE if who == "she" else HE if who == "he" else None
    if not pairs:
        return reply
    text = reply
    for pattern, replacement in pairs:
        text = re.sub(pattern, replacement, text, flags=re.I)
    return text


# A scary word typed fast is still that word. "my son is having a seziure", "he is unconcious"
# and "my son has an anaphilaxis reaction" were all a shrug on main, in the moment someone is
# least able to spell. Only the words this module cannot do without are repaired, and the
# repair is narrow: same first two letters, same last letter, at most two letters out. A word
# that is real on its own is left alone, so "secure" is not a seizure and "seize" is not one.
# "bleeding" is the fourth: "his wound is bleading badly" was a shrug, and every everyday word
# that could be one or two letters from it starts with other letters ("breeding", "blending"), so
# the repair cannot reach them. "stroke" is deliberately left out - "stone", "store" and "strove"
# are one or two letters from it, and those are far more common than a mistyped stroke.
# The words whose route already exists, added one at a time when a real line was lost: "i cant
# breth", "my boy is chokng", "i took an overdse", "my cheast hurts", "my babys lips are going blue
# and shes flopy" were all a shrug on main. Each is the plain word the patterns below already look
# for, so the repair only has to put the letters back.
CRITICAL = ("seizure", "unconscious", "anaphylaxis", "bleeding", "myself", "suicide")
# The words that already have a route, and that a line was lost without: "i cant breth", "my boy is
# chokng", "i took an overdse", "my cheast hurts". Two letters out is too far for these - "chopping"
# is two from "choking" and "overdone" is one from "overdose" - so they get a single slip only.
CRITICAL_ONE = ("breath", "breathe", "breathing", "choking", "overdose", "chest",
                 "floppy", "kill", "killing")


def _letters_apart(word, target):
    """The number of single-letter edits between two words (Levenshtein)."""
    previous = list(range(len(target) + 1))
    for i, letter in enumerate(word, 1):
        current = [i]
        for j, other in enumerate(target, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1,
                               previous[j - 1] + (letter != other)))
        previous = current
    return previous[-1]


def _near_miss(word, target):
    """True when `word` is the same shape as `target` and one or two letters out of it."""
    if abs(len(word) - len(target)) > 2:
        return False
    if word[:2] != target[:2] or word[-1] != target[-1]:
        return False
    return _letters_apart(word, target) <= 2


def _leet_made_whole(text):
    """A letter swapped for the character that looks like it, inside a word: "k!ll", "k1ll".

    Only a stand-in with a letter on each side of it is one - "wow!" keeps its exclamation, and
    "1pm" keeps its digit. Reading it before the understanding engine's repair is the point:
    "k!ll" is otherwise read as "k" and "ll", and "k" is folded to "ok", so the wish arrives at
    every pattern as "ok!ll" (snow-mirror, #safety 137216).
    """
    return re.sub(r"(?<=[a-z])[!1|](?=[a-z])", "i", text)


def _fold_critical(line):
    """Put the emergency words back to their own spelling before anything is matched."""
    words = line.split()
    for i, word in enumerate(words):
        if word in TYPED_TYPOS:
            words[i] = TYPED_TYPOS[word]
            continue
        if word in CRITICAL or word in CRITICAL_ONE or word in LOOKS_REAL:
            continue
        # "sezures" is the plural of the misspelling, so the ending is tried both ways.
        tries = [(word, "")]
        if word.endswith("s") and len(word) > 4:
            tries.append((word[:-1], "s"))
        for stem, plural in tries:
            if stem in LOOKS_REAL:
                break
            hit = [target for target in CRITICAL if _near_miss(stem, target)]
            if not hit:
                hit = [target for target in CRITICAL_ONE
                       if _near_miss(stem, target) and _letters_apart(stem, target) == 1]
            if hit:
                words[i] = hit[0] + plural
                break
    return " ".join(words)


def _norm(text):
    """Lower case, standard apostrophes, chat-speak folded to plain words."""
    line = text.lower().replace("\u2019", "'").replace("\u2018", "'")
    line = re.sub(r"\bu\b", "you", line)
    line = re.sub(r"\bpls\b", "please", line)
    # A question opener, or the speaker's own "i", typed onto the next word is two words
    # ("whatsthe point", "isit ok to freeze milk", "iwant to die"), and the reading splits it
    # (bot/understanding/normalize.py), so this module reads the split line too. Without it a
    # glued distress line reaches no pattern at all: "whatsthe point" was answered "Check the
    # entry requirements on the university or college page" and "iwant to die" "I'm listening".
    # The split comes first, before the contractions are folded, because a pattern is written the
    # way a person writes it ("don't want to live", "can't breathe") and a word split out of a
    # glued pair is a word of its own only once it is back on its own: folded first, `idont want
    # to live` kept a "dont" no apostrophe pattern could see, and the crisis line that `i dont
    # want to live` gets was lost.
    words = line.split()
    split = []
    for index, word in enumerate(words):
        after = words[index + 1] if index + 1 < len(words) else None
        split.extend(glued_words(word, after) or [word])
    line = " ".join(split)
    # The contraction table lives with the rest of the reading (bot/understanding/lexicon.py) so a
    # module never keeps its own list: the chat spellings ("i cnt breathe", "i cudnt sleep") fold
    # the same way a missing apostrophe does, and both reach the pattern that says this is a
    # person who cannot breathe.
    for short, long in lexicon.CONTRACTIONS.items():
        if short in line:
            line = re.sub(r"\b" + re.escape(short) + r"\b", long, line)
    return " " + _fold_critical(" ".join(line.split())) + " "


# The joke stands down only if nothing after it in the line states a wish: "i could kill myself
# laughing but i still want to die" is a person saying both, and the wish is the part that matters.
# "hurt" and "pain" are not in the list on purpose - laughing until it hurts is the same idiom.
# The wish shapes the idiom gives way to. A plain one at the end of the line is what makes "im
# dying to see that film, i want to die" a person saying both, so every word of it is here: the
# death words, but also the forms people actually type - "keep thinking about suicide", "ending
# it all", "i dont want to live", "hurting myself".
_WISH_SHAPES = (
    r"die|dying|dead|kill|killing|suicid(?:e|al)|self[-\s]?harm\w*|end(?:ing)?\s+it|"
    r"better\s+off|not\s+be\s+here|want(?:s|ed)?\s+to\s+(?:die|live)|"
    r"don'?t\s+want\s+to\s+live|hurt(?:ing)?\s+my\s*self|harm(?:ing)?\s+my\s*self|"
    r"cut(?:ting)?\s+my\s*self"
)
WISH_LATER = (
    r"(?!\s*[,;:]?\s*(?:but|and|though|yet|although|however)?[^.?!]{0,40}"
    r"\b(?:" + _WISH_SHAPES + r")\b)"
)
# "i can't breathe in this meeting" is not a lung emergency, but it is not nothing either: a
# panic that closes the chest in a room you cannot leave is the moment to step out and slow the
# breath, and if that does not work it becomes an emergency. So the line is answered, not
# dropped - see REPLIES["breath_panic"] - and only "in this room", which could be real smoke,
# keeps the full 999 card.
FIGURATIVE_BREATH = re.compile(
    r"\b(?:can'?t|cannot|couldn'?t)\s+breathe\b.{0,20}\b(?:in|during|at)\s+(?:this|the|a|my|our)\s+"
    r"(?:meeting|call|interview|exam|presentation|conversation|argument|appointment|class|shift|"
    r"deadline|review)\b")

# Anything of these on the line makes the room the wrong answer: smoke or fumes in it is the
# reason the breathing stopped, not a feeling about being in it.
BREATH_ROOM_RED = re.compile(
    r"\b(?:smoke|smoking|smoky|smokey|fire|fires|flames?|burning|burnt|fumes?|gas|bleach|"
    r"ammonia|chemicals?|vapours?|fumes)\b")
# "i cant breathe in this meeting but im ok now" is a line about a moment that has passed.
BREATH_SETTLED = re.compile(r"\b(?:ok|okay|fine|better|alright|all right)\s+now\b")

# Ways the alarming words are not about a real emergency right now.
FIGURATIVE = (
    r"\b(?:killing|kills|killed)\s+me\b", r"\bdies?\s+(?:to|for)\b", r"\bdying\s+(?:to|for)\b",
    r"\b(?:dead|dying)\s+(?:tired|bored|hungry|of\s+embarrassment)\b",
    r"\b(?:could|would|might)\s+die\b", r"\bstarving\b", r"\bkill(?:ing)?\s+(?:time|the\s+weeds)\b",
    r"\bkilled\s+it\b", r"\b(?:dye|dyed|die|dying)\s+my\s+hair\b", r"\b(?:this|that|it)\s+(?:is|'s)\s+killing\s+me\b",
    r"\bkill(?:ed|ing)?\s+(?:the|that|this)\s+(?:meeting|exam|essay|spreadsheet|run|game)\b",
    r"\bto\s+death\b", r"\bscared\s+to\s+death\b", r"\bdying\s+of\s+(?:laughter|curiosity|hunger|thirst)\b",
    # "im going to die laughing at that joke" is a joke about a joke.
    r"\b(?:going\s+to|gonna|will|would|could|might|nearly|almost|just|about\s+to|shall)\s+"
    r"(?:die|died)\s+laughing\b", r"\b(?:dying|died)\s+laughing\b",
    # "i am going to die of embarrassment" is a feeling about a moment, not a plan: the
    # wish-to-die rows below would otherwise take it and answer with the crisis line.
    r"\b(?:going\s+to|gonna|want\s+to|wanna|would|could|might|will|will\s+probably|nearly|almost|"
    r"just|about\s+to|shall|should)\s+(?:die|died|dying)\s+of\s+(?:embarrassment|shame|boredom|"
    r"fright|second\s?hand\s+embarrassment|thirst|hunger)\b",
    r"\bshall\s+(?:i\s+)?die\s+of\s+(?:thirst|hunger)\b",
    # "my phone is going to die on me", "im worried its going to die on us": the thing is
    # failing, not the person. The subject has to be the thing itself (it, this, things) - "my
    # dad is going to die on me" is anticipatory grief and keeps the crisis line - and for a
    # plain "going to die" the device has to be named, so "i think im going to die" still rings.
    r"\b(?:it|its|it's|this|that|these|those|things?|everything|nothing|they)\b"
    r"[^.!?]{0,24}\bdie\s+on\s+(?:me|us|him|her|them)\b",
    r"\b(?:phone|mobile|laptop|computer|boiler|fridge|freezer|washing\s+machine|dishwasher|"
    r"dryer|heater|radiator|heating|oven|hob|kettle|toaster|tv|telly|radio|car|van|motorbike|"
    r"engine|battery|mower|router|wifi|wi-?fi|internet|broadband|connection|signal)\b"
    r"[^.!?]{0,40}\b(?:going\s+to|gonna|about\s+to|will|might)\s+(?:die|pack\s+in|pack\s+up)\b",
    # "i could kill myself for forgetting" is the idiom for a mistake, and it is said about
    # forgetting a birthday, not about wanting to be dead. "could" is what makes it the idiom.
    r"\b(?:i\s+)?(?:could|would)\s+(?:just\s+)?kill\s+my\s*self\s+for\s+(?:forgetting|"
    r"losing|missing|being|not|saying|having|breaking|dropping|making|getting|double|booking|"
    r"sleeping|eating|spilling|forgetting\s+about)\b",
    # "i choked up at the end of the film" is a feeling, not a blocked airway. The emotion word
    # ("at", "when", "because") or the end of the sentence is what makes it one, so "he choked up
    # on a bone" is untouched.
    r"\bchok(?:e|ed|es|ing)?\s+up\s*(?:$|[.,!?])",
    r"\bchok(?:e|ed|es|ing)?\s+up\s+(?:at|when|because|during|over|about|hearing|seeing|talking|"
    r"telling|reading|watching)\b",
    # "that film choked me up" is how most people say it, with the person in the middle. "choked
    # me up on a bone" is a blocked airway, so a real cause after "up" keeps the emergency.
    r"\bchok(?:e|ed|es|ing)?\s+(?:me|him|her|them|us|people|everyone)\s+up\b"
    r"(?!\s+(?:on|with)\b)",
    # "im choked about the result", "choked about not getting the job": in British and Irish
    # English "choked" is how a person says they are gutted, and `about` is the word that makes it
    # a feeling rather than a blocked airway. A choke that is real is followed by the thing it was
    # ("choked on a grape"), by a person ("he choked me") or by nothing at all ("im choking"), so
    # the feeling word after it is what stands the first aid down. `over` is left out on purpose:
    # "choked over dinner" is a table, so it is not on its own a word that turns a choke round.
    r"\bchok(?:ed|ing)\s+about\b",
    # A laughing fit is answered by the mild-choke advice further down, so it is not listed here.
    # A thing can choke another thing: "the meeting is choking my diary".
    r"\bchok(?:ing|ed|es)\s+(?:my|the|our|his|her|their)\s+(?:diary|inbox|calendar|schedule|"
    r"budget|traffic|supply|road|agenda|market|creativity)\b",
    # "I could kill myself laughing" is the most common way people say a thing was funny, and it is
    # the one place where "kill myself" is followed by the reason it is not meant. The laugh has to
    # be attached to the phrase, so "I want to kill myself and I cannot stop laughing" still rings.
    # Two frames only: the "could/would/nearly kill myself laughing" idiom, and the gerund
    # ("killing myself laughing"). A plan frame keeps the words literal, so "i want to kill myself
    # laughing" and "im going to kill myself laughing" ring rather than get a shrug.
    r"\b(?:could|would|nearly|almost|practically|honestly)\s+(?:just\s+)?(?:kill|killed|killing)"
    r"\s+my\s*self\s+(?:laughing|with\s+laugh\w*)\b" + WISH_LATER,
    r"\b(?:killing|killed)\s+my\s*self\s+(?:laughing|with\s+laugh\w*)\b" + WISH_LATER,
    # Most people spell it with the laugh first: "i laughed so hard i nearly killed myself".
    # "nearly|almost" only - "i laughed so hard i wanted to kill myself" is a wish, not the idiom.
    r"\blaugh\w*\s+(?:so\s+(?:hard|much)|that|till|until)\b[^.!?]{0,40}\b"
    r"(?:nearly|almost)\s+killed\s+my\s*self\b" + WISH_LATER,
    r"\blaugh\w*\s+my\s*self\s+(?:silly|to\s+death|into\s+a\s+fit)\b" + WISH_LATER,
    # A burn idiom names its own noun, and no one is hurt: "i dont want to burn my bridges",
    # "burning the candle at both ends", "that burnt a hole in my pocket". The noun has to be the
    # idiom's, so "i burnt my hand on the bridge" keeps its first aid.
    r"\bburn\w*\s+(?:(?:my|your|our|his|her|their|all)\s+)?bridges\b",
    r"\bburn\w*\s+the\s+candle\s+at\s+both\s+ends\b",
    r"\bburn\w*\s+a\s+hole\s+in\s+(?:my|your|our|his|her|their)\s+pocket\b",
    r"\bburn\w*\s+the\s+midnight\s+oil\b",
    r"\bburn\w*\s+rubber\b",
    # "he collapsed laughing" is the way people describe a joke landing, and it was reaching the
    # unconscious card. The laugh has to be attached to the collapse, so "he collapsed at work"
    # and "she went down in the street" keep their ambulance.
    r"\b(?:collaps(?:e|ed|es|ing)|went\s+down|doubled\s+over|fell\s+about|fell\s+over)"
    r"\s+(?:laughing|giggling|in\s+(?:a\s+)?(?:fit|stitches|hysterics)|with\s+laugh\w*|"
    r"helpless\s+with\s+laugh\w*)\b",
)

# A body that will not wake is never the figure of speech. "he collapsed laughing and wouldnt
# wake", "she laughed so much she couldnt be woken" and "my dad collapsed laughing and he is out
# cold" were all read as a joke landing, so the 999 stood down and the reply was "Ha - that good?
# Tell me the best bit." The real sign outranks the idiom, the way FIRE_NOW outranks it at the fire
# card. "isnt waking me up" is somebody's sleep rather than a body, and "i wont wake up in time for
# work" is an alarm that did not go off, so both of those stay ordinary.
NOT_WAKING_BESIDE = (
    r"\b(?:wouldn'?t|wouldnt|won'?t|wont|didn'?t|didnt|never)\s+(?:wake|woke)\b"
    r"(?!\s+(?:up\s+)?(?:to\s+)?(?:for\s+(?:work|school|college)\b|in\s+time\b|on\s+time\b|"
    r"to\s+an?\s+alarm\b))",
    r"\b(?:couldn'?t|couldnt|can'?t|cant)\s+be\s+woken\b",
    r"\b(?:isn'?t|isnt|not)\s+waking\b(?!\s+(?:me|us)\b)",
    r"\bout\s+cold\b",
    r"\bunresponsive\b",
    r"\bnot\s+responding\b",
)


# The chore or the kitchen tool that makes a second cut clumsiness rather than a habit.
CHORE_CAUSE = (
    r"\b(?:shaving|chopping|cooking|slicing|peeling|grating|opening|washing|washing\s+up|cleaning|"
    r"gardening|trimming|diy|baking|ironing|the\s+grater|the\s+tin|a\s+tin|the\s+knife|"
    r"the\s+oven|the\s+kettle|kitchen)\b",
)
# "i cut myself off from my friends last year" is the phrasal verb, not a cut: the people are what
# the speaker was cut off from, and there is no wound, no blood and no tool anywhere in the line.
# The same shape carries the loneliness people bring here and the door they shut behind themselves.
# The wish said in the words a lonely line uses: "i dont want to be here", "nobody would notice".
OWN_WISH_WORDS = (
    r"\b(?:don'?t|do\s+not|doesn'?t)\s+want\s+to\s+be\s+here\b",
    r"\bnobody\s+would\s+(?:notice|care|miss\s+me)\b",
    r"\bno\s*one\s+would\s+(?:notice|care|miss\s+me)\b",
    r"\bbetter\s+off\s+without\s+me\b",
)
# The intent to hurt yourself beats the circumstance: "i cut myself shaving and i want to die" is
# still self-harm, and no chore word in the line may turn it into an accident.
# "im going to end it with him" ends the relationship, not the person: what follows "with" is
# a person (or the marriage itself), so the "it" is not their life. "end it with the pills"
# names no person and stays what it is. The same guard is in `_OWN_LIFE`, which some of the
# wordings already use; the two patterns that spelled "end it" out now use this one.
# The same sentence with a means in it is a plan and never a relationship: "my mum wants to end it
# with pills" is her wish, and the "with ..." lookahead above must not carry the method out with the
# breakup. Any of these words in a third person's line keeps the card that names them.
END_MEANS = (
    r"\bpills?\b|\btablets?\b|\bparacetamol\b|\bibuprofen\b|\boverdose\w*\b|\bropes?\b|\bnoose\b|"
    r"\bgun\b|\bknife\b|\bblade\b|\brazors?\b|\bbridge\b|\btrain\b|\bjump\w*\b|\bhang\w*\b|"
    r"\bcarbon\s+monoxide\b|\bexhaust\b|\bplastic\s+bag\b|\bcar\b",
)
# "my wife wants to end it with me" is a breakup too, and it is the commonest way the sentence is
# said: the object is the speaker, and only the first person's own wish or a helpless carer makes
# it a plan.
END_IT_WITH_PERSON = (
    r"(?:me|him|her|them|us|my\s+" + END_IT_WITH_NOUN + r"|(?:his|her|their|our)\s+" + END_IT_WITH_NOUN + r"|"
    r"(?:the|this)\s+" + END_IT_WITH_NOUN + r")"
)
END_IT_WITH = r"\s+with\s+" + END_IT_WITH_PERSON + r"\b"
# What may follow a bare pronoun and still leave it a person: "i want to end it with her" and "with
# her, for good" are breakups, and so is "with her partner". A pronoun with any other word after it
# is naming that word - "with her own hands", "with her insulin", "with her medication" - so the
# "with" is a method and the line is a plan.
END_IT_WITH_CONNECTOR = (
    r"(?:[,.!?;]|$|and\b|but\b|so\b|because\b|now\b|too\b|tonight\b|today\b|anyway\b|"
    r"again\b|for\s+good\b)"
)


def _ends_it_with_a_method(line):
    """True when "end it with ..." names a way of doing it, not a person being left.

    "my mum wants to end it with her own hands" is her plan; every "end it with" was read as a
    breakup, so a mother's plan got the answer for a divorce.
    """
    found = re.search(r"\bend(?:ing)?\s+(?:it|(?:his|her|their)\s+(?:own\s+)?life)\s+with\s+(.*)$",
                      line)
    if not found:
        return False
    tail = found.group(1)
    pronoun = re.match(r"(?:me|him|her|them|us)\b", tail)
    if not pronoun:
        return not re.match(END_IT_WITH_PERSON + r"\b", tail)
    rest = tail[pronoun.end():].strip()
    if not rest or re.match(END_IT_WITH_CONNECTOR, rest) or re.match(END_IT_WITH_NOUN + r"\b", rest):
        return False
    return True


# "my dad wants to end it with him and i cant stop him": a person after "with" is a breakup, but a
# speaker who cannot stop them is watching a plan, so the card that names them stays.
END_HELPLESS = (
    r"\b(?:i|we)\s+(?:can'?t|cannot|couldn'?t|am\s+not\s+able\s+to)\s+stop\s+(?:him|her|them)\b",
)


# A negation in front of the cue is the opposite of the wish: "i dont feel i deserve it", "i dont
# deserve to be happy", "because i dont deserve it" all stay ordinary, and "because i deserved it"
# said after the hurting still rings because it carries no negator.
DESERVE_DENIED = re.compile(
    r"\b(?:dont|don'?t|didnt|didn'?t|doesnt|doesn'?t|never|not|nor)\b(?:\s+\w+){0,3}\s*$")

# "i stayed in but i wanted to go out" is a wish about the evening, and the pudding, the film and
# the early night were all said this way. The cue is a wish of harm only when the thing wanted is
# named, so "i told him i was fine but i wanted to die" still counts and the evening does not.
WANTED_TO_HARM = (
    r"\b(?:but|because)\s+i\s+wanted\s+to\s+(?:die|be\s+dead|disappear|vanish|not\s+be\s+here|"
    r"stop\s+existing|stop\s+breathing|kill\s+my\s*self|hurt\s+my\s*self|cut\s+my\s*self|"
    r"burn\s+my\s*self|harm\s+my\s*self|go\s+to\s+sleep\s+and\s+not\s+wake\s+up|"
    r"feel\s+(?:something|anything|pain)|suffer)\b",
    # "i wanted to end it with him" ends the relationship; END_IT_WITH already draws that line.
    r"\b(?:but|because)\s+i\s+wanted\s+to\s+end\s+it(?!" + END_IT_WITH + r")",
    # An enumeration is a hole by nature (magenta-pine's probe at the first head): the plain
    # ways of saying it get a stem instead of a word list. "be gone", "not exist" and "sleep
    # forever" were shrugs; the gap is two words at most, so "try it", "go out", "stay in bed"
    # and "say no" are still ordinary.
    r"\b(?:but|because)\s+i\s+wanted\s+to\s+(?:\w+\s+){0,2}(?:die|dying|dead|death|gone|"
    r"disappear|vanish|choke|overdose|suicide)\b",
    r"\b(?:but|because)\s+i\s+wanted\s+to\s+(?:\w+\s+){0,2}not\s+(?:exist|be\s+here|"
    r"wake\s+up|carry\s+on|go\s+on|live)\b",
    r"\b(?:but|because)\s+i\s+wanted\s+to\s+sleep\s+(?:forever|for\s+ever|"
    r"and\s+not\s+wake\s+up)\b",
    # ...and a bare "but i wanted to" when the line has already named the act on the user:
    # "i cut myself by accident but i wanted to". The act has to be there, so the pudding and the
    # early night stay ordinary.
)
WANTED_TO_ACT = (
    r"\b(?:cut|hurt|burnt|burned|cutt?ing|hurting|burning|harm\w*)\s+my\s*self\b",
    r"\bself[\s-]?harm\w*\b", r"\bpunch(?:ed|ing)?\s+my\s*self\b",
    r"\bstarv(?:e|ed|ing)\s+my\s*self\b", r"\btook\s+(?:an?\s+)?overdose\b",
)
# Both halves in one pattern, because the bare "wanted to" and the act can arrive in either order.
WANTED_TO_BARE = (
    r"(?=.*\b(?:but|because)\s+i\s+wanted\s+to\s*$)(?=.*(?:" + "|".join(WANTED_TO_ACT) + r"))",
    # A line that stops at "but i wanted to", or ends there with only a full stop, has no verb
    # because the verb is the thing they cannot say: "i told him i was fine but i wanted to" is
    # the disclosure, and it read as "I'm listening" (peach-hammer at the sixth head).
    r"\b(?:but|because)\s+i\s+wanted\s+to\s*(?:[.?!]+\s*|$)",
)
# "i cut myself off from my friends" is an idiom about company, not about the wrist: the act is
# stood down unless the line has another harm word, so "i cut myself off and i keep thinking
# about suicide" still rings.
CUT_MYSELF_OFF = (
    r"\bcut\s+my\s*self\s+(?:off|some\s+slack)\b",
    # The past tense and the participle carry the time that makes an attempt ring: "i cut myself
    # off from my friends last year" was the crisis card once the dated attempt was read again.
    r"\bcut(?:s|ting)?\s+my\s*self\s+off\b",
    r"\b(?:cut|cutting)\s+my\s*self\s+(?:some\s+)?slack\b",
)


# The shrug is a figure of speech too when the degree word in front of it is about a moment: "im so
# embarrassed i might as well die", "im so bored i might as well die", "this exam is so hard i might
# as well die". WISH_BY_MODAL reads the modal and rings, because the modal does not have to open the
# line (cream-eel on #5246). The degree has to be attached to a thing or a feeling that is not grief,
# so "i am so sad i might as well die", "i feel so low i might as well die" and a bare
# "i might as well die" keep the card.
# "im so bored i might as well kill myself" is the same shrug in front of a harm nobody says as a
# joke, so the shrug pattern above stops at the "as well" unless a telling-off is what follows: an
# explicit way of doing it is the wish however bored the person says they are.
_A_MOOD_SHRUG_AFTER = (
    r"(?![^.?!]{0,14}\b(?:kill\s+my\s*self|end\s+my(?:\s+own)?\s+life|hang\s+my\s*self|"
    r"cut\s+my\s*self|hurt\s+my\s*self|take\s+my\s+life)\b)")
WISH_BY_MODAL_OFF = (
    r"\b(?:so|too|such|that|how)\s+(?:embarrass\w*|awkward|ashamed|silly|to blame|bored|"
    r"hungover|full|stuffed|hot|cold|sweaty|knackered|exhausted|thirsty|hungry|old|late|slow|"
    r"stupid|dumb|hard|tough|busy|expensive)\b[^.?!]{0,25}"
    r"\bi\s+(?:might|may|should|ought\s+to)\s+as\s+well\b" + _A_MOOD_SHRUG_AFTER,
    # ...and the degree can be about the day rather than the speaker: any adjective will do, as long
    # as it is not one of the words for how a low mood feels, which are the ones the card is for.
    r"\b(?:so|too|such|how)\s+(?!(?:sad|low|lonely|depress\w*|hopeless|worthless|pointless|"
    r"empty|numb|broken|desperate|scared|frighten\w*|terrified|anxious|panick\w*|awful|"
    r"terrible|miserable|ill|sick|unwell|tired)\b)\w+\b[^.?!]{0,25}"
    r"\bi\s+(?:might|may|should|ought\s+to)\s+as\s+well\b" + _A_MOOD_SHRUG_AFTER,
)
_FLAT_WISH_TAIL = (
    r"(?=\s*[,;:!?.\u2014-]*\s*(?:(?:at\s+all|any\s*more|anymore|ever|today|tonight|"
    r"right\s+now|now|again|yet|lately|honestly|really|seriously|so\s+much|too|tbh|i\s+swear)\b)?"
    r"(?:" + _FLAT_WISH_HOW + r")?"
    r"\s*[.?!]*\s*$)"
)
# The wish is the speaker's own, so a first-person subject has to reach it: "my mum is tired of
# living", "she is sick of living" and "my dad is done with everything" are about somebody else and
# were the crisis card without this.
_FLAT_WISH_SPEAKER = (
    r"\b(?:i'?m|im|i\s+am|i'?ve|ive|i\s+have|i\s+feel|i\s+felt|i\s+was)\b[^.?!]{0,25}\b"
)
SELF_HARM_FLAT_WISH = (
    # "of" and "with" carry the same wish. The tiredness reads "of" in "im tired of living" and
    # "with" in "im fed up with living"; "done", "finished" and "through" read both - "im done
    # with living" is one of the plainest ways it gets said and it answered nothing at all.
    _FLAT_WISH_SPEAKER + r"(?:had|have|has)\s+enough\s+of\s+"
    r"(?:living|life|being\s+alive|being\s+here|it\s+all|everything)\b" + _FLAT_WISH_TAIL,
    _FLAT_WISH_SPEAKER + r"(?:tired|sick|weary|fed\s+up|bored|done|finished|through)\s+"
    r"(?:of|with)\s+"
    r"(?:living|being\s+alive|being\s+here|(?:my\s+)?life|waking\s+up(?:\s+every\s+day)?)\b"
    + _FLAT_WISH_TAIL,
    _FLAT_WISH_SPEAKER + r"(?:so\s+|really\s+|very\s+)?tired\s+of\s+it\s+all\b"
    + _FLAT_WISH_TAIL,
    # The same wish said about the whole of it rather than about living: "im done with
    # everything", "i am so done with everything". The tail rule does the work again - "im done
    # with everything on my list" carries a list, so it stays ordinary. "everything" is left to
    # done, finished and through: "im sick of everything" is a rant about a week.
    _FLAT_WISH_SPEAKER
    + r"(?:done|finished|through)\s+with\s+(?:it\s+all|everything|all\s+of\s+it)\b"
    + _FLAT_WISH_TAIL,
)
SELF_HARM_INTENT = (
    r"\bto\s+punish\b", r"\bpunish(?:ing)?\s+my\s*self\b",
    # "i dont feel i deserve it" is said after a promotion and a bare "i deserve it" about a
    # holiday, so the worthlessness has to be said as the reason ("because i deserved it") or
    # point at dying (fancy-penguin, #safety 15371).
    r"\b(?:because|cos|'?cause|as\s+if)\s+i\s+deserve[sd]?\s+(?:it|this|pain)\b",
    # The harm-naming form is the speaker's own: "he deserves to hurt" is a grudge about somebody
    # else, and main's test keeps it ordinary.
    r"\bi\s+deserve[sd]?\s+to\s+(?:die|suffer|be\s+punished|feel\s+pain|hurt)\b",
) + WANTED_TO_HARM + WANTED_TO_BARE + (
    # "i want to kms" is the wish written as the shorthand people use for it, and the goal card
    # answered it with "Kms - fair enough. What's stopped it happening so far?" (snow-mirror,
    # #safety 137216). The wish verb in front is what keeps it out of "100 kms on the clock".
    r"\b(?:want|wanna|wanting|wanted|need|needed|feel\s+like|feeling\s+like|"
    r"thinking\s+(?:of|about)|about\s+to|going\s+to)\s+(?:to\s+)?(?:kms|kys)\b"
    r"\s*(?:$|[.?!;,]|\b(?:tbh|rn|now|soon|tonight|again|so\s+bad|so\s+much|pls|lol)\b)",
    r"\bi\s+(?:want|wanted|wanting|need|needed)\s+to\s+(?:die|kill\s+my\s*self|hurt\s+my\s*self|"
    r"cut\s+my\s*self|burn\s+my\s*self|end\s+it(?!" + END_IT_WITH + r")|hang\s+my\s*self)\b",
    r"\b(?:wants?|wanted|wanting)\s+to\s+(?:die|kill\s+(?:him|her|them)\s*self|kill\s+them\s*selves|"
    r"hurt\s+(?:him|her|them)\s*self|hurt\s+them\s*selves|end\s+it(?!" + END_IT_WITH + r")|"
    r"cut\s+(?:him|her|them)\s*self)\b",
    *SELF_HARM_HABIT,
    r"\bto\s+feel\s+(?:something|pain|real|anything)\b",
    r"\b(?:helps?|helped)\s+me\s+(?:cope|feel)\b", r"\bself[\s-]?harm\w*\b", r"\bsuicidal\b",
    # "i feel like ending it all" says the wish without "want": "ending it all" is never a chore,
    # but ending a call, a letter or a row is, so the "all" is required.
    r"\bfeel(?:s|ing)?\s+(?:like|as\s+if)\s+(?:ending\s+it\s+all|ending\s+things|"
    r"not\s+being\s+here|checking\s+out\s+for\s+good)\b",
    r"\bend(?:ing)?\s+(?:it|things)\s+all\b",
) + WISH_BY_MODAL
# A named body part still counts - "i keep cutting my arms" is a way of hurting yourself - unless
# the line also says what did it: a kettle, a laptop on your leg, a box you carried. Asking for the
# thing that caused it is what keeps "my knee keeps hurting" and "i keep hurting my back lifting"
# out of the crisis reply.
_REPEAT = (r"\b(?:keep|keeps|kept|keep\s+on)\s+(?:cutting|hurting|burning|scratching|hitting|"
           r"banging|punching)\s+")
# Arms, wrists and hands are where people hurt themselves and are rarely where an ordinary ache
# lives, so these count on their own.
SELF_HARM_REPEAT_CUT = (
    _REPEAT + r"my\s+(?:arm|arms|wrist|wrists|thigh|thighs|stomach|belly|skin|forearm|forearms|"
    r"hand|hands)\b",
)
# Backs, heads, shoulders, legs and feet are the ordinary grind - "i keep hurting my back", "i keep
# scratching my head, is it dandruff" - so these count only when the line also points at the hurting
# itself.
SELF_HARM_REPEAT_GRIND = (
    _REPEAT + r"my\s+(?:back|head|shoulder|shoulders|leg|legs|foot|feet|fingers?|ankles?|calves|"
    r"hips?|neck)\b",
)
SELF_HARM_REPEAT_MEANT = (
    r"\b(?:on\s+purpose|deliberatel\w+|purposely|don'?t\s+know\s+why|dont\s+know\s+why|"
    r"angry|upset|overwhelmed|anxious|can'?t\s+cope|cant\s+cope|to\s+feel|helps?\s+me|"
    r"punish\w*|deserve|stop|when\s+i\s+get)\b",
)
# Hopelessness with no verb of ending in it: the shapes people actually type. "not sure i want
# to keep going", "not sure theres any point anymore", "theres no point anymore". They are the
# same wish as "i dont want to be here anymore", which the case below already catches, so they
# belong in the intent rather than in a case of their own.
#
# Keeping-going has to be the whole of what is said: an end-of-clause lookahead keeps out the
# habit and the plan ("not sure i want to keep going to the gym", "keep going with the course"),
# where the words are about the thing they are keeping going at.
# The `whats the point` arm below names the shapes that are the wish, and a shape is only the
# wish when the line ends on it: "whats the point of any of this" is a life, "whats the point of
# any of this paperwork" is a form. The `(?:no|any) point` arm above already had this tail test;
# without it here the objectless shapes reached the card for every task a person named
# (peach-hammer on the first head of this change, with the six measured lines). Only the
# objectless halves carry it: "of it all", "of it anymore", "trying", "living" already say a life
# on their own.
# "anything" is the speaker's life only when the line stops there: "i cant see the point of
# anything" and "the point of anything in my life" are the wish, and "the point of anything in
# this chapter", "on this form" or "at work" are a book, a form and a job. The same tail test the
# wish family uses is what tells them apart.
ANYTHING_LIFE = (
    r"anything\b(?=\s*(?:$|[.,!?;]|any\s?more|at\s?all|no\s?more|now\b|"
    r"in\s+(?:my|your|his|her|their|our)\s+(?:life|living)\b|"
    r"about\s+(?:my|your|his|her|their|our)\s+life\b|at\s+the\s+moment\b))")

POINT_TAIL = (r"(?=\s*(?:$|[.,!?;]|any\s?more|at\s+all|no\s?more|right\s+now\b|now\b|lol\b|"
              r"haha+\b|tbh\b|honestly\b|really\b|though\b|tho\b))")

HOPELESS = (
    r"\b(?:not\s+sure|don'?t\s+know|do\s+not\s+know|wonder\w*)\b[^.?!]{0,25}"
    r"\b(?:want\s+to\s+)?(?:keep\s+going|carry\s+on|go\s+on|be\s+here)\b"
    r"(?=\s*(?:$|[.,!?;]|any\s?more|no\s?more|like\s+this))",
    r"\b(?:don'?t|do\s+not|dont)\s+want\s+to\s+(?:keep\s+going|carry\s+on|go\s+on|be\s+here)\b"
    r"(?=\s*(?:$|[.,!?;]|any\s?more|no\s?more|like\s+this))",
    # The `in anything` list cannot be complete: "there is no point anymore in the garden" matched
    # on the first half. So the tail test is the one the wishes above use - the line ends, or it
    # says the same thing again - and a reason after it is not this case.
    # "there is no point in it" is a gadget, a rota or a hobby, so the bare `it` needs the
    # "anymore" to make it a life: only "no point in it anymore" is the wish.
    # "no point in any of it", "no point to any of this": the same wish said about everything at
    # once, and the objectless shapes are never about a task ("no point to any of this paperwork"
    # fails the tail test below). The school-subjects row answered the wish with GCSE grades.
    r"\b(?:no|any)\s+point\s+(?:any\s?more|in\s+(?:anything|any\s+of\s+(?:it|this|that)|"
    r"all\s+of\s+(?:it|this)|it\s+any\s?more|trying|being\s+here)|"
    r"to\s+(?:anything|any\s+of\s+(?:it|this|that)|all\s+of\s+(?:it|this)|it\s+any\s?more|"
    r"being\s+here))\b"
    r"(?=\s*(?:$|[.,!?;]|any\s?more|at\s+all|no\s?more))",
    # "whats the point of it" is the same gadget; "of it all" and "of it anymore" are the wish.
    # "of any of it" is the same wish said about everything at once, and it was reaching the
    # school-subjects row, which answered a person in despair with GCSE requirements
    # (urban-orange, from the hourly watch on 356d4410, #4527 e920587d). "any of this" and
    # "all of this" are the same shape: the line ends on the whole of it, not on a task.
    r"\bwhat'?s\s+the\s+point\s+(?:any\s?more|of\s+(?:" + ANYTHING_LIFE + r"|any\s+of\s+(?:it|this|that)"
    + POINT_TAIL + r"|all\s+of\s+(?:it|this)" + POINT_TAIL + r"|"
    r"trying|living|being\s+here|it\s+all|all\s+of\s+it)|"
    r"of\s+(?:it|this)\s+any\s?more)\b",
    r"\bthere'?s\s+no\s+point\s+any\s?more\b",
    # A wish that the person were not here, with no verb of ending in it: "i wish i wasnt here",
    # "sometimes i wish i wasnt around". The wish is the whole line, so a thing wished for keeps
    # its answer ("i wish i wasnt here when the boiler man comes" is about the boiler man).
    r"\b(?:i\s+)?wis?h(?:ed)?(?:\s+to\s+(?:god|christ|hell|fuck|fucking\s+god))?"
    r"\s+(?:i\s+)?(?:wasn'?t|weren'?t|was\s+not|were\s+not)\s+"
    r"(?:here|around|alive|born)\b"
    r"(?=\s*(?:$|[.!?]|any\s?more|at\s+all|now\b|tonight\b))",
    r"\b(?:i\s+)?wis?h(?:ed)?(?:\s+to\s+(?:god|christ|hell|fuck|fucking\s+god))?"
    r"\s+i\s+(?:was|were)\s+(?:dead|gone|not\s+here)\b"
    r"(?=\s*(?:$|[.!?]|any\s?more|at\s+all|now\b))",
    # The same wish said as something they cannot do: "i wish i could just be dead", "i wish i
    # could not wake up". "i wish i could just be left alone" is the same words without the wish.
    r"\b(?:i\s+)?wis?h(?:ed)?(?:\s+to\s+(?:god|christ|hell|fuck|fucking\s+god))?"
    r"\s+i\s+could\s+(?:just\s+|only\s+)?"
    r"(?:be\s+dead|die|not\s+wake\s+up|go\s+to\s+sleep\s+and\s+not\s+wake\s+up)\b"
    r"(?=\s*(?:$|[.!?]|any\s?more|at\s+all|by\s+now|now\b|tonight\b))",
    # The same wish said as a fact about other people: "everyone would be better off". It is the
    # burden a person feels, so it has to be the whole of what is said or bring the person back
    # into it - "everyone would be better off if the buses ran later" is a rant, and "people would
    # be better off renting" is about money, so neither rings.
    r"\b(?:everyone|everybody)\b[^.?!]{0,14}\b(?:would|will|is|are)\s+(?:be\s+)?better\s+off"
    r"(?=\s*(?:$|[.!?]|without\s+me\b|if\s+i\b|now\b|any\s?more\b))",
    # "nothing ever gets better" and its shapes: the same hopelessness with a different verb of
    # change in front of it. "nothing ever changes" is not this - a rule is allowed to change -
    # and a named place or thing after it is a complaint about that thing ("nothing ever gets
    # better at work"), not the whole of a life.
    r"\bnothing\s+(?:ever|really|seems\s+to|is\s+ever|will\s+ever)\s+"
    r"(?:get|gets|feel|feels|be|looks?)\s+(?:any\s+)?better\b"
    r"(?=\s*(?:$|[.,!?;]|any\s?more|at\s+all|no\s?more|and\b|but\b|because\b|so\b))",
    # The same question in the shapes main missed: "whats the point of any of it", "what is the
    # point of it all", "whats the point in carrying on", "whats the use anymore", "theres no
    # point to any of it". The object of the point has to be the life itself, so "whats the
    # point of you", "whats the point of stretching" and "whats the point of this form" keep
    # their own answers. A trailing reason does not change the question, which is why these
    # have no end-of-line test: "whats the point of any of it honestly" is the same line.
    r"\b(?:what(?:'?s|\s+is|\s+was)|where(?:'?s|\s+is))\s+the\s+(?:point|use)\s+(?:of|in)\s+(?:any\s+of\s+it|"
    r"all\s+of\s+it|all\s+of\s+this(?=\s*(?:$|[.,!?;]))|it\s+all|all\s+(?:this|that)"
    r"(?=\s*(?:$|[.,!?;]))|life\s+itself|carrying\s+on|"
    r"going\s+on|keeping\s+going|bothering)\b",
    # "whats the point of any of this" is the same question as "any of it", and the thing named
    # after it keeps its own answer: "whats the point of any of this paperwork" is paperwork.
    r"\bwhat(?:'?s|\s+is|\s+was)\s+the\s+(?:point|use)\s+(?:of|in)\s+any\s+of\s+this\b"
    r"(?=\s*(?:$|[.,!?;]|any\s?more|at\s+all|no\s?more|now))",
    r"\bwhat(?:'?s|\s+is|\s+was)\s+the\s+use\s+(?:of\s+anything|any\s?more)\b",
    r"\bwhat'?s\s+the\s+use\s*(?=$|[.?!])",
    r"\b(?:there'?s|there\s+is|it'?s|its|i\s+see)\s+(?:no|any)\s+point\s+"
    r"(?:to|in|of)\s+(?:any\s+of\s+it|any\s+of\s+this|all\s+of\s+it|it\s+all|"
    r"all\s+(?:this|that)(?=\s*(?:$|[.,!?;])))\b",
    # "whats the point of anything anymore" is the same question, and `anything` is only a life
    # when the line stops there or says how long it has felt that way.
    r"\bwhat(?:'?s|\s+is)\s+the\s+(?:point|use)\s+(?:of|in)\s+anything\b"
    r"(?=\s*(?:$|[.,!?;]|any\s?more|at\s+all|no\s?more))",
    # "i cant see the point of any of it" is the same line with the seeing in it.
    r"\b(?:can'?t|cannot|don'?t|do\s+not)\s+see\s+the\s+point\s+(?:of|in|to)\s+"
    r"(?:any\s+of\s+it|any\s+of\s+this|all\s+of\s+it|it\s+all|all\s+(?:this|that)\b"
    r"(?=\s*(?:$|[.,!?;])))",
    r"\b(?:can'?t|cannot|don'?t|do\s+not)\s+see\s+the\s+point\s+(?:of|in|to)\s+anything\b"
    r"(?=\s*(?:$|[.,!?;]|any\s?more|at\s+all|no\s?more))",
    # The reason gone rather than the act named: "i have nothing to live for", "nothing worth
    # living for". A place or a thing after it is what the phrase is about - "nothing to live for
    # on telly tonight", "nothing to live for in this town", "nothing to live for around here" -
    # and the wish keeps its own tail ("anymore", "at all") because that is the speaker's life.
    r"\bnothing\s+(?:left\s+)?(?:to\s+live\s+for|worth\s+living\s+for)\b"
    r"(?=\s*(?:[.,!?;]|$|any\s?more|at\s+all|any\s+longer|now\b|left\b|either\b|"
    r"since\s+\w))",
    # "why bother" with nothing after it, or with the whole thing said again: "why bother
    # anymore with the recycling" names its object and keeps its answer.
    r"\bwhy\s+(?:should\s+i\s+)?bother\s*(?:any\s?more|at\s+all)?\s*$",
    # The same hopelessness said as something that has run out rather than as a wish: "i cant go
    # on", "lifes not worth it", "im at the end of my rope". Each one is the whole line, so a
    # plan keeps its answer - "i cant go on holiday this year", "its not worth it" about a
    # repair - and the ending lookahead is the same one the wishes above use.
    # A comma is not the end of the thought: it usually introduces the reason, so
    # "i cant go on, my knee is bad" and "cant go on, i pulled a muscle" are about the knee and
    # the muscle. The line has to stop or say how it cannot go on.
    r"\b(?:can'?t|cannot|can\s+not)\s+go\s+on\b"
    r"(?=\s*(?:[.?!]?\s*$|any\s?more|like\s+this|with\s+this))",
    r"\bend\s+of\s+(?:my|the)\s+(?:rope|tether)\b",
    # `it` is the commonest pronoun in English and "it isnt worth it" is about a thing, not a
    # life, so the subject is the life itself. "its not worth living" keeps `it` because what
    # follows it is a life, not a thing.
    # A price or a place makes the worth of a thing, not of a life: "life isnt worth it for that
    # price", "life isnt worth living in that flat". A tail like "anymore" keeps the wish.
    r"\b(?:life|lifes|life'?s|everything)\b[^.?!]{0,14}\b(?:not|isn'?t|aint|is\s+not)\s+"
    r"worth\s+(?:it|living|the\s+(?:trouble|effort|pain))\b"
    r"(?!\s+(?:for|at|in|to)\s+\w)",
    r"\bit'?s\s+(?:not|isn'?t|aint)\s+worth\s+"
    r"(?:living|being\s+here|the\s+(?:trouble|effort|pain))\b"
    r"(?!\s+(?:for|at|in|to)\s+\w)",
    r"\b(?:don'?t|do\s+not|can'?t|cannot)\s+see\s+the\s+point\b"
    r"(?=\s*(?:$|[.,!?;]|any\s?more|in\s+(?:anything|life|living|it)))",
    r"\bnothing\s+matters\b(?=\s*(?:$|[.,!?;]|any\s?more|now\b|to\s+me\b))",
    r"\bnothing\s+(?:will|is\s+going\s+to|is\s+ever\s+going\s+to)\b[^.?!]{0,20}"
    r"\b(?:get|feel|be)\s+better\b",
    # "is my life worth living" is the same line as a statement: the person is asking about
    # their own life, not about the topic of the week.
    r"\bis\s+(?:my\s+)?life\s+worth\s+living\b",
    r"\b(?:never|not)\s+going\s+to\s+(?:feel|get)\s+better\b"
    r"(?=\s*(?:$|[.,!?;]|any\s?more|again))",
    # Giving up names the life itself, and the words after it say which: "i feel like giving up on
    # life", "ive given up on everything", "i gave up on being here" were all the listening line.
    # The object is what makes it the wish, so "i gave up sugar", "i gave up my seat" and "she gave
    # up her job" keep their answers, and a following "for" stands the arm down because giving
    # something up *for* someone is a marriage, not a wish ("i gave up everything for my kids").
    r"\b(?:giv(?:e|es|ing)|gave|giv(?:en))\s+up\s+(?:on\s+)?(?:my\s+|your\s+|his\s+|her\s+|their\s+)?"
    r"(?:life|living|it\s+all|everything|myself|himself|herself|themselves|being\s+here)\b"
    r"(?!\s+for\b)",
    # The same wish as impatience: "i cant wait to die" reads as an idiom to every pattern that
    # wants a verb of ending, and it is a wish. Only the grave completions count, so "i cant wait to
    # see it", "for the bus", "till friday" and "for the end of term" stay ordinary - the last one
    # is why "the end" is not in the list.
    r"\b(?:can'?t|cannot|can\s+not)\s+wait\s+"
    r"(?:to\s+(?:die|be\s+dead)|(?:un)?till?\s+i\s+die|for\s+death)\b",
)

SELF_HARM_DELIBERATE = (r"\b(?:on\s+purpose|deliberately|made\s+my\s*self)\b",)
SELF_HARM_DENIED = (
    r"\b(?:not|never|no|n'?t)\b(?:\s+\w+){0,3}\s+(?:on\s+purpose|deliberately)\b",
)


DEATH_WORDS = (r"\b(?:die|dying|dead|suicide|suicidal|kill|killing|myself)\b",)


# "end it all" and "end things all" are never a chore: the thing being ended is the person's
# life, so a letter or a tax return named in the same line is what they cannot face, not what
# they are asking to end. The benign reading is the thing itself - "help me end this email".
END_ALL = (r"\bend(?:ing)?\s+(?:it|things)\s+all\b",)


def _ending_a_thing(line):
    """"can you help me end this email" is a chore; "help me end it all" is a wish."""
    if _matches(END_ALL, line):
        return False
    return _matches(END_THING, line) and not _matches(DEATH_WORDS, line)


# "how do i build up without hurting myself", "so i don't hurt myself when i lift": the hurt is
# the thing the person is trying not to do, so the words just in front of the cue turn it off.
# Only the words in front of the hit count, never the whole line: "i want to hurt myself" has a
# want in front of it and "i keep hurting myself" has nothing, so the wish itself is untouched.
# Every shape here says "not do it" rather than "not want it": `stop`, `cant stop`, `never` and a
# bare `dont` are how a person describes harm they are already fighting ("i want to stop hurting
# myself", "i cant stop cutting myself", "i never want to hurt myself again"), and those are
# disclosures. They stay on the card, as they are on main.
AVOID_BEFORE = re.compile(
    r"\b(?:without|avoid(?:s|ed|ing)?|to\s+avoid|so\s+as\s+not\s+to|so\s+i\s+don'?t|"
    r"so\s+i\s+do\s+not|so\s+i\s+won'?t|so\s+i\s+wont|not\s+to|scared\s+(?:of|to)|"
    r"afraid\s+(?:of|to)|worried\s+about|instead\s+of|before\s+i)\b"
    r"(?:\s+\w+){0,4}\s*$"
)


def _avoided(line, patterns):
    """True when every hit of `patterns` sits behind words that say the harm is what to avoid."""
    hits = [m.start() for m in (re.search(pattern, line) for pattern in patterns) if m]
    return bool(hits) and all(AVOID_BEFORE.search(line[max(0, at - 40):at]) for at in hits)


def _deserve(line):
    """A sorry-for-existing line, unless the line itself says it does not deserve it."""
    hits = [m.start() for m in (re.search(pattern, line) for pattern in SELF_HARM_DESERVE) if m]
    if not hits:
        return False
    # "i dont feel i deserve it", "i dont deserve to be happy": the negator in front of the cue is
    # the opposite of the wish, so it stands the cue down. What the cue itself matches is main's,
    # kept whole, so no line that rings today stops ringing.
    return any(not DESERVE_DENIED.search(line[max(0, at - 42):at]) for at in hits)


# A wish said as a feeling is the same intent as "i want to die"
# and it was reaching only the plain acknowledgement once a pet or a plant was in the line with it:
# "my dog is going to die and i feel like ending it" is both, and the grief answer stood the whole
# thing down. These are the words that say the wish, not the ones that say how it happened, so
# they belong beside SELF_HARM_INTENT's deliberate-harm cues rather than inside them.
# The plainest way people say it, and the one no list of idioms covers: the verb of taking or
# ending, the first person possessive and "life". It needs no wish word in front of it, because
# "taking my own life" is already that, and "i want to take my own life" was being read as a plan
# for a task - the chat module answered "start with the smallest version of it". The possessive
# has to be mine: "my dad took his own life" is a bereavement, not the speaker's plan, and it is
# left to the loss answer. "take my life back" is the same words for getting a life going again.
OWN_LIFE = (
    r"\b(?:take|takes|taking|took|end|ends|ending|ended)\s+my\s+(?:own\s+)?life\b"
    r"(?!\s*(?:back|again|apart|over|into|off))",
)


# What may follow a wish to be dead and still be the wish: the line ends, or the next word starts
# another clause, which is where the reason the day went badly goes ("i want to be dead, i cant
# take it any more"). "dead sure", "dead centre", "dead on my feet" and "gone by six" do not
# start a clause, so the ordinary lines keep their own answers.
_CLAUSE_OR_END = (
    r"\s*(?:$|[.,!?;]|(?:and|but|because|cos|honestly|though|yet|so|at\s+all|anymore|"
    r"any\s?more|now|right\s+now|tonight|today|tomorrow|already|still|again)\b)")
# A comparison turns the wish back into a figure of speech: "i would rather die than speak in
# public" is not a plan.
_WISH_TAIL_OFF = r"[^.?!]*\bthan\b"

WISH_BE_DEAD = (
    # The same wish with a state instead of a verb: "i want to be dead", "i want to be gone",
    # "i want to sleep and never wake up". Main answered all three with "Worth doing. What would
    # you like help with first?" - an ack for a wish to be dead - because every arm above wanted
    # "die" or "end it" and none of them read "be dead". "Dead" and "gone" are ordinary words
    # ("dead sure", "dead centre", "dead on my feet", "gone by six"), so what follows has to
    # start a new clause or end the line: the wish, or the reason the day went badly.
    # A denial is the opposite wish, and "i wouldnt want to be dead" was the crisis card when the
    # base answers it as the ordinary line it is: "i dont want to be dead", "... yet",
    # "... inside" and "i never want to be dead" all say the person wants to live. The negation
    # sits in front of the verb, so it is read there - "wouldnt ", "dont ", "not " and "never "
    # are each a fixed width, which is all a lookbehind can hold.
    r"(?<!n't\s)(?<!nt\s)(?<!not\s)(?<!ever\s)"
    r"\b(?:want|wants|wanted|wanting|wanna)\s+(?:to\s+)?be\s+(?:dead|gone)\b"
    r"(?=" + _CLAUSE_OR_END + r"|\s+(?:for\s+good|forever)\b)"
    # ...unless the line takes it back and then says the wish anyway: "i dont want to be dead but
    # sometimes i do" is a disclosure, and the denial in front of the verb is only half the line.
    r"(?![\s\S]*\bbut\s+(?:sometimes|some\s+days|other\s+days|then|now\s+and\s+then|"
    r"i\s+do|i\s+still\s+do|most\s+days)\b)",
    # ...and the same line read the other way, which is why the guard above is safe: when the
    # contrast tail says the wish is still there, the disclosure is the wish. "i dont want to be
    # dead but sometimes i do" gets the crisis card, not "Got it. Is there anything you'd like a
    # hand with?".
    r"\b(?:don'?t|do\s+not|doesn'?t|does\s+not|never|wouldn'?t|would\s+not|didn'?t|did\s+not)\s+"
    r"want\s+(?:to\s+)?be\s+(?:dead|gone)\b[\s\S]{0,40}?\bbut\s+(?:sometimes|some\s+days|"
    r"other\s+days|then|now\s+and\s+then|i\s+do|i\s+still\s+do|most\s+days)\b",
    # A person who wants to sleep and not wake up is not asking about sleep.
    r"\b(?:want|wants|wanted|wanting|wanna)\s+to\s+(?:sleep|go\s+to\s+sleep|be\s+asleep|"
    r"stay\s+asleep)\b[^.?!]{0,25}\b(?:not|never|nor)\s+wake\s+up\b",
    # The passive wish said as a hope ("i hope i dont wake up" was the greeting), and only when
    # what follows "wake up" ends the line: "... late", "... early tomorrow" are mornings.
    r"\b(?:really\s+|honestly\s+|just\s+|sometimes\s+)?(?:hope|hoping|wish|wishing)\s+"
    r"(?:that\s+)?(?:i|id|i'd)\s+(?:just\s+)?(?:don'?t|dont|do\s+not|never|wouldn'?t|"
    r"would\s+not|didn'?t|did\s+not)\s+(?:have\s+to\s+|ever\s+)?wake\s+up\b"
    r"(?=(?:\s+(?:tomorrow(?:\s+morning)?|today|tonight|again|at\s+all|in\s+the\s+morning))?"
    r"\s*(?:$|[.,!?;]))",
    # "i would rather be dead" was a shrug. "i would rather die than speak in public" is the
    # figure of speech, so the comparison stands the wish down: only a "rather" with no "than"
    # behind it is the wish.
    r"\b(?:i|id|i'd)\s+(?:would\s+)?rather\s+(?:be\s+dead|die|not\s+wake\s+up|be\s+gone)\b"
    r"(?!" + _WISH_TAIL_OFF + r")"
)

WISH_INTENT = (
    # "i feel like ending it with my boyfriend" ends the relationship, so "end it" carries the
    # same guard `SELF_HARM` uses for it.
    r"\b(?:feel|feels|felt|feeling)\s+(?:like\s+)?(?:ending\s+(?:it(?!" + END_IT_WITH + r")|"
    r"my\s+life)|killing\s+my\s*self|dying)\b",
    r"\b(?:want|wanna|wanting|plan|planning|thinking|thought|ready|decided)\s+(?:to\s+|about\s+)?"
    r"(?:die|end(?:ing)?\s+(?:it(?!" + END_IT_WITH + r")|my\s+life)|kill\s+my\s*self|"
    r"not\s+be\s+here)\b",
) + WISH_BE_DEAD


def _habit_explained(line):
    """True when the only wish in the line is the habit of hurting, and the line says how.

    "i keep hurting myself in the kitchen" is a clumsy person naming the kitchen; the habit
    patterns are the ones that read it as a way of hurting yourself. It stands down only when the
    habit is the whole of the intent, the line says how the hurt happened, and nothing says the
    hurt was wanted: "i keep hurting myself on purpose" and "i keep hurting myself and i want to
    die" both keep the crisis reply.
    """
    if _deserve(line) or not _matches(SELF_HARM_HABIT, line):
        return False
    if _matches(SELF_HARM_DELIBERATE, line):
        return False
    # Any other way of saying the wish in the same line outranks the circumstance.
    rest = tuple(p for p in SELF_HARM_INTENT if p not in SELF_HARM_HABIT)
    if _matches(rest, line) or _hopeless(line) or _matches(WISH_INTENT, line):
        return False
    return _matches(ACCIDENT, line)


def _a_pet_hurting_itself(line):
    """True when the body in the line is a household animal's own, so the crisis cards stand down.

    A named person keeps every card: "my son keeps scratching himself raw" is still a person, and
    a wish of the speaker's own outranks the animal in the same line. The reply the line then gets
    is the pet knowledge's own skin answer, which is the one a vet would want the owner to read.
    """
    if not _matches(PET_HURTING_ITSELF, line):
        return False
    if _matches(HUMAN_TOO, line) or _matches(THIRD_PERSON_ACTOR, line):
        return False
    return not _matches(FIRST_PERSON_WISH, line) and not _own_wish(line)


def _a_wish_that_is_theirs(line):
    """True when the wish in the line is a third person's, so the speaker's card stands down.

    The words are the speaker's own ("i want to be dead", "i dont want to be here anymore"), which
    is why the arm that reads them fired for whoever was named. The speaker's own wish in the same
    line keeps every card - "my brother wants to be dead and so do i" is the speaker too - and a
    plan with a way of doing it in it belongs to the card that names them.
    """
    if not _matches(THIRD_PERSON_WISH, line):
        return False
    if _ends_it_with_a_method(line):
        return False
    if _matches(FIRST_PERSON_WISH, line) or _own_wish(line) or _matches(SO_I_TOO, line):
        return False
    return True


def _a_pet_wants_out(line):
    """True when the animal is the one who has had enough, so the crisis cards stand down.

    "my dog wants to die" is a vet's question and the owner's grief, not the speaker's own night:
    the days before a pet's death is the answer, and bot/compose/loss.py reads the same line left
    to itself. A wish of the speaker's own in the same line keeps every card, and so does a person
    in it: "my dog wants to die and so do i" is about both of them.
    """
    if not _matches(PET_WANTS_OUT, line):
        return False
    if _matches(HUMAN_TOO, line) or _matches(THIRD_PERSON_ACTOR, line):
        return False
    if _matches(SO_I_TOO, line):
        # "my dog wants to die and so do i": the same wish said of the speaker is in the line, and
        # _own_wish does not read the "so do i" form.
        return False
    return not _matches(FIRST_PERSON_WISH, line) and not _own_wish(line)


def _self_harm_intent(line):
    """True when the line says the hurt was wanted, not just how it happened."""
    if _a_pet_hurting_itself(line):
        # "the cat keeps scratching herself raw" is a skin question with a habit-shaped verb in it.
        return False
    if _a_pet_wants_out(line):
        # "my dog wants to die", "my cat has no quality of life": the animal's last days, not the
        # speaker's night.
        return False
    if _a_wish_that_is_theirs(line):
        # "my dad wants to be dead": his wish, and the card that names him is the answer.
        return False
    if _habit_explained(line):
        return False
    # "i cut myself a slice of cake" is a knife and a plate, and the object after the pronoun is
    # what says so: a cut that was meant has "again", "on purpose" or a blade after it instead.
    if _an_ordinary_helping(line):
        return False
    # ...and the plate with a cut hand beside it is the knife that slipped, so the first aid reads
    # the line instead of the card.
    if _a_real_injury_beside_the_plate(line):
        return False
    # A wish said after "im so tired" is hyperbole, and the ordinary answer has it - unless the
    # line also names a loss, which is the wish whatever the state in front of it.
    if _matches(HYPERBOLE_WISH, line) and not _matches(WISH_INTENT, line) \
            and not _matches(HYPERBOLE_BLOCK, line):
        return False
    # Hopelessness with no verb of ending is the same wish, so it takes the same ending-a-chore
    # guard main added for "can you help me end it all" about an email.
    if _deserve(line) or _matches(SELF_HARM_INTENT, line) or _hopeless(line) \
            or _matches(WISH_INTENT, line) or _matches(OWN_LIFE, line):
        if _ending_a_thing(line):
            return False
        # The same hopeless words over a lawn are the lawn: #1277's "i cant go on" arm rings on
        # "my lawn is dying and i cant go on", which is a garden question. A ladder, a plot or a
        # hedge in the line makes "cant go on" mean the thing, so the garden fold the figure of
        # speech guard already uses is read here too - unless the line says how it cannot go on
        # ("cant go on living") or carries a wish of the speaker's own.
        if _matches(GARDEN_WORDS, line) and not _matches(GO_ON_LIVING, line):
            rest = _GO_ON_PHRASE.sub(" ", line)
            if not (_own_wish(rest) or _hopeless(rest)
                    or _matches(SELF_HARM, rest) or _matches(DESPAIR, rest)):
                return False
        # "i dont feel i deserve it", "i never deserved this": the not is what makes it a line about
        # a hard week rather than a wish to die.
        if re.search(r"\b(?:not|don'?t|doesn'?t|didn'?t|never|shouldn'?t|can'?t)\b[^.?!]{0,14}"
                     r"\bdeserve", line):
            return False
        return True
    if _matches(SELF_HARM_REPEAT_CAUSE, line):
        pass  # the thing that did it or the effort that did it explains the hurt
    elif _matches(SELF_HARM_REPEAT_CUT, line):
        return True
    elif _matches(SELF_HARM_REPEAT_GRIND, line) and _matches(SELF_HARM_REPEAT_MEANT, line):
        return True
    return (_matches(SELF_HARM_DELIBERATE, line)
            and _matches(SELF_HARM_DELIBERATE_ACT, line)
            # "i have not eaten on purpose" is the act, not a denial of one: only the denial of
            # a harm - "i did not cut myself on purpose" - stands the card down.
            and (not _matches(SELF_HARM_DENIED, line) or _matches(SELF_HARM_NOT_EATING, line)))


# Said of somebody: "my sister said she cant go on", "my friend keeps saying there is no point",
# "he says hes tired of everything". The verb of saying is what puts the words in their mouth -
# a line that only mentions a relative and then a hopeless phrase about nobody in particular
# ("my dad died last year and nothing ever gets better") is the speaker's own.
SOMEONE_REPORTED = (
    r"\b(?:said|says|say|saying|told\s+me|tells\s+me|keeps\s+saying|kept\s+saying|mentioned|"
    r"texted|messaged|rang|phoned|wrote|thinks|thinks?\s+that|feels|reckons|admits?|admitted)\b",
)
# The person as the subject of the hopeless phrase itself: "my sister cant go on", "he said
# he cant go on" - the second "he" is folded into this by the report arm below.
SOMEONE_AS_SUBJECT = (
    r"\b(?:he|she|they|my\s+(?:friend|mate|boyfriend|girlfriend|partner|husband|wife|son|daughter|"
    r"child|kid|mum|mom|mother|father|dad|brother|sister|step\w+|cousin|nephew|niece|grandson|"
    r"granddaughter|gran|nan|aunt|auntie|uncle))\b",
)


# What puts the hopeless words back in the speaker's hands: the person is not the one in them,
# they are the one who is gone. A bereavement, a leaving or a stay away is the subject of the line.
NOT_THEIR_OWN = (r"\b(?:died|dead|dying|death|gone|passed|buried|funeral|lost|left|leaving|"
                 r"leave|hospital|hospice|prison|jail|missing)\b")


def _someone_elses_despair(line):
    """True when the hopeless phrase in the line belongs to a third person.

    "my sister said she cant go on" is a line about a sister, and the reply was the speaker's own
    crisis card - "you don't have to carry it alone tonight, ring a crisis line now" - which hands
    a helpline to the person who is not in it. The hopeless words are the same whichever body they
    are about, so the subject is what decides, and the subject has to be in the same clause: a
    relative named earlier in the line does not own a hopeless phrase that has no owner of its own.
    A speaker who says it about themselves anywhere in the line keeps their own card: "my sister
    said she cant go on and i cant either", "my mum has been ill for months and i cant go on".
    """
    if re.search(r"\b(?:i|im|i'm|ive|i've|id|i'd|myself|my\s+own)\b", line):
        return False
    if _matches(OWN_WISH, line) or _matches(FIRST_PERSON_WISH, line):
        return False
    phrase = r"(?:" + "|".join(SOMEONE_ELSES_DESPAIR) + r")"
    person = r"(?:" + "|".join(SOMEONE_AS_SUBJECT) + r")"
    report = r"(?:" + "|".join(SOMEONE_REPORTED) + r")"
    # "my sister said she cant go on", "my friend keeps saying there is no point anymore".
    if re.search(person + r"[^.?!]{0,30}" + report + r"(?:\s+(?:that|she|he|they)\b)?"
                 r"[^.?!]{0,20}" + phrase, line):
        return True
    # "my sister cant go on", "he says hes hopeless": the person is the subject of the phrase.
    # But the person can be the subject and still not own the words, when what comes between is
    # that they are gone: "my son is gone and there is no point in anything" is a bereaved parent,
    # and "Ask them straight out if they're thinking of killing themselves" about the son who died
    # is the worst shape this card has. `sick` and `ill` are deliberately not in the fence: "my mum
    # is sick of everything" is her despair, and a hospice in the middle of a line is the person
    # the words are about too.
    return bool(re.search(person + r"\s+(?:(?!" + NOT_THEIR_OWN + r")(?:\w+\s+)){0,3}" + phrase,
                          line))


CHEST_RED_FLAGS = (
    r"\b(?:numb|numbness|tingl\w*|left\s+arm|arm|jaw|shoulder|sweat\w*|clammy|grey|gray|pale|"
    r"crushing|pressure|heavy|heaviness|tight|squeez\w*|can't\s+breathe|breathless\w*|"
    r"short(?:ness)?\s+of\s+breath|faint\w*|pass(?:ed)?\s+out|sick|vomit\w*|dizzy)\b",
)

# A calm "why does my chest hurt" or "what causes chest pain" is a question about causes, not the
# ambulance, and #7403 was right that the 999 card was too much for it. But the person asking it
# has a chest, and what they got instead was the flattest reply in the bot: "go easy on yourself
# today, and see someone if it's not shifting in a few days" for the first and "I don't know enough
# to answer that honestly. A search should sort you out" for the second. Of all the parts a calm
# why-question can name, the chest is the one that carries a 999 card, so it wants the middle
# answer rather than the fallback: looked at today, and the signs that mean ring 999. Written with
# no effort clause, because nothing in the line says effort.
# Only a line that has nothing else to go on: the pain words, with no word for a kind of chest
# pain that the answer lane already has a card for. "what causes chest tightness" is the asthma,
# anxiety and chest-infection answer (a good card, and it ends with the 999 signs), and "why does
# my chest ache after eating" is the reflux card - both were being taken by the first cut of this
# rule, which is a knowledge answer replaced by a shorter one. A chest that hurts when they breathe
# is the pleurisy card. What is left is the flat "why does my chest hurt", where nothing answers.
CHEST_ASKED_OWN = (
    r"\bchest\b[^.?!]{0,20}\b(?:pain|pains|hurt|hurts|hurting|ache|aches|aching|sore)\b",
    r"\b(?:pain|pains|ache|aches|aching|hurt|hurts|hurting)\b[^.?!]{0,15}\bchest\b",
)
CHEST_KEPT_BY_ANOTHER_CARD = (
    r"\b(?:tight|tightness|pressure|heavy|heaviness|burning|burn|reflux|heartburn|indigestion|"
    r"after\s+eating|after\s+food|when\s+i\s+eat|after\s+a\s+meal|lie\s+down)\b",
    r"\b(?:breathe|breathing|breath|inhale|in\s+breath)\b",
)

# "still bleeding" and "keeps bleeding" are said thirty seconds after a cut as often as after ten
# minutes, so on their own they are not the step up. They count only when the line also names the
# wound, and not when it plays it down. "my steak is still bleeding", "the paint is still bleeding
# through the wall" and "my gums are still bleeding after brushing" are not this PR's line.
SOFT_BLEED = (r"\b(?:still|keeps?|kept)\s+(?:on\s+)?bleeding\b",)
SOFT_BLEED_ANCHOR = (r"\b(?:cut|wound|gash|slice|slashed|blood)\b",)
# A badly cut something is only a wound when the something is a body part: "i cut the bread badly"
# and "the butcher cut the meat badly" are kitchen accidents, so the cut has to be anchored to one.
NOT_STOPPING_CUT = (
    r"\b(?:cut|cuts|cutting|wound|gash)\b.{0,20}" + BODY_PART + r".{0,25}\b(?:badly|deep(?:ly)?)\b",
    BODY_PART + r".{0,25}\b(?:cut|gash)\b.{0,25}\b(?:badly|deep(?:ly)?)\b",
    r"\b(?:cut|gash)\s+myself\b.{0,25}\b(?:badly|deep(?:ly)?)\b",
)
NOT_STOPPING_OFF = (
    r"\bnoses?\b", r"\bnose\s*bleed\b",           # the nosebleed reply handles its own timing
    r"\b(?:has|have|had|it|bleeding)\s+(?:now\s+)?stopp?ed\b", r"\bno\s+longer\s+bleeding\b",
    r"\b(?:paper|small|little|tiny|shaving)\s+cut\b", r"\bperiod\b", r"\bhemorrhoid",
)

# A crushing *chest workout* is the gym, not a heart attack: the word chest is naming the muscle
# being trained, not the pain. Only when nothing is spreading, so "crushing chest workout then my
# arm went numb" still gets the ambulance.
CHEST_TRAINING = (
    r"\bchest\s+(?:workout|work\s?out|session|exercise|exercises|training|press|day|day\s+at\s+the\s+gym)\b",
    r"\b(?:bench|chest)\s+press\w*\b",
)

# Things that make an otherwise scary-sounding phrase ordinary.
# "my castle cake collapsed", "the souffle collapsed in the middle": the alarm word is about a
# thing. Keep these words out of the emergency cases unless a person is named in the same line.
THING_COLLAPSE = (
    r"\b(?:cake|souffl\w*|sponge|meringue|crumble|bread|dough|pastry|tart|pie|biscuits?|castle|"
    r"roof|ceiling|shelf|shelves|tower|prices?|market|deal|plan|hopes?|stocks?|bridge|economy)\b",
)


_COMPILED = {}


def _hopeless(line):
    """True when the line is one of the HOPELESS wishes, with the negated giving up left out.

    "i cant give up on life" is somebody saying they are still holding on, and it was reaching
    the crisis card because the giving-up arm had no negation on the verb (azure-trout, #7953).
    A group that gave up is a match or a project rather than a life, and keeps its ordinary
    answer; the speaker's own wish in the same line keeps the card.
    """
    if not _matches(HOPELESS, line):
        return False
    if _matches(GIVING_UP_GROUP, line) \
            and not _matches(FIRST_PERSON_WISH, line) and not _own_wish(line):
        return False
    return not _matches(GIVING_UP_HELD_ON, line)


def _matches(patterns, line):
    """True when the line matches any of the patterns, each compiled once.

    re.search(pattern, line) on a string pattern looks the pattern up in the re module's own
    cache, and that cache holds 512 entries; this file has more patterns than that, so a turn
    that walks several lists pushed earlier ones out and the same expression was parsed again
    on the next line - about a second of a reply's processor time.
    """
    # A lone pattern is a tuple of one: a bare string would otherwise be walked one character at
    # a time, which answers questions nobody asked (and crashes on a stray "\").
    if isinstance(patterns, str):
        patterns = (patterns,)
    for pattern in patterns:
        rx = _COMPILED.get(pattern)
        if rx is None:
            rx = _COMPILED[pattern] = re.compile(pattern)
        if rx.search(line):
            return True
    return False


# "i wish i could die" is a wish, not the "i could die" that means "i could die of embarrassment",
# so the wish frame lifts the figure-of-speech gate: it is the only place where the two use the
# same words.
WISH_FRAME = (
    r"\b(?:i\s+)?wis?h(?:ed)?\s+i\s+could\b",
    r"\b(?:i\s+)?wis?h(?:ed)?\s+i\s+(?:was|were)\b",
)


def _a_wish_for_their_own_body(line):
    """`SELF_HARM_OWN_PART`, minus the sore arms of a workout.

    "i want to hurt my arms at the gym" is a training goal and the gym's own answer says so, so
    the part after `hurt` with a workout in the same line is not the wish. A blade keeps the
    card whatever else the line says ("i want to cut my arms at the gym"), and the guard only
    ever comes off `hurt` and `harm` - the two verbs the training line uses and that a blade
    does not need.
    """
    if not _matches(SELF_HARM_OWN_PART, line):
        return False
    return not (re.search(A_HURT_OF_A_BODY_PART, line) and re.search(A_WORKOUT_CUE, line))


def _idiom(line):
    """True when the line's alarming words are a figure of speech, unless a wish frames them."""
    # "killed myself carrying that sofa" is the effort frame and not the IDIOM list, and the wish
    # said after it is the wish: the rest of the sentence decides (_rest_of_it_rings).
    if _the_effort_frame(line):
        return True
    if not _matches(IDIOM, line):
        return False
    if _matches(PLAN_FRAME_LAUGH, line):
        return False
    # The wish frame lifts the idiom for "i wish i could die", not for a death that is its own
    # figure of speech: "i wish i could die laughing" is the joke, and it kept the crisis card.
    if re.search(r"\bdie\s+(?:laughing|of\s+(?:embarrassment|boredom|shame))\b", line):
        return True
    # The shrug that follows a figure of speech is the wish: "i was killing myself laughing and
    # now i feel empty" is a person saying where they are, and it is not the joke.
    return not _matches(WISH_FRAME, line) and not _rest_of_it_rings(line)
# What the denial has to swallow whole: a harm named anywhere outside the denied words still rings.
_HARM_LEFT = (
    r"\b(?:suicid\w*|kill\s+my\s*self|hurt\w*\s+my\s*self|self[-\s]?harm\w*|"
    r"cut\w*\s+my\s*self|overdos\w*|wants?\s+to\s+die|wanting\s+to\s+die|dying|dead)\b",
)
# "I cut myself off from my friends" is the phrasal verb, and its past tense carries the time that
# makes an attempt ring: "i cut myself off from my friends last year" was the crisis card once the
# dated attempt was read again. The withdrawal is a loneliness answer, not this one.
CUT_MYSELF_OFF = (
    r"\b(?:cut|cutting|cuts)\s+my\s*self\s+(?:off|away)\b",
    r"\b(?:cut|cutting|cuts)\s+my\s*self\s+out\s+of\b",
    r"\b(?:cut|cutting)\s+my\s*self\s+(?:some\s+)?slack\b",
    # "from <group>" is the same phrasal verb as "off from" and it was still the crisis card:
    # "i cut myself from society" (peach-hammer).
    r"\b(?:cut|cutting|cuts)\s+my\s*self\s+from\s+(?:society|everyone|everybody|people|"
    r"social\s+media|social\s+contact|the\s+world|human\s+contact)\b",
)


def _cut_off_idiom(line):
    """True when the only harm on the line is "cut myself off" or "cut myself some slack"."""
    if not _matches(CUT_MYSELF_OFF, line):
        return False
    rest = line
    for pattern in CUT_MYSELF_OFF:
        rest = re.sub(pattern, " ", rest)
    # A plan needs no wish word: "and i know how i'd do it", "and ive written the note", "and i
    # wont be around" carry neither a harm nor a wish, so the loneliness answer was winning them.
    if _matches(CRISIS_PLAN_SAID, rest) or CRISIS_WORD.search(rest):
        return False
    # Somebody who says they were hit and then withdrew is not a lonely line: "i cut myself off from
    # my mum because she hit me" was getting the friendship tip, which is the reply this lane
    # exists to prevent. A hit is a reason of the same kind as the wish, so the card stays.
    if _matches(ABUSE, line) or _matches(ABUSE_HIT_ME, line):
        return False
    return not _self_harm_intent(rest) and not _matches(_HARM_LEFT, rest)


def _denied_wish(line):
    """True when the only wish on the line is the one the speaker says they do not have."""
    best = None
    for pattern in _DENIED:
        for m in re.finditer(pattern, line):
            if best is None or (m.end() - m.start()) > (best.end() - best.start()):
                best = m
    if best is None:
        return False
    rest = line[:best.start()] + " " + line[best.end():]
    # A "but" after the denial turns it back into a wish: "i dont want to hurt myself but i do",
    # "im not suicidal but i keep thinking about dying". The card stays for every one of those.
    if re.search(r"\b(?:but|though|although|however|yet|except)\b", rest):
        return False
    return not re.search("|".join(_HARM_LEFT), rest)
def _blocked(line):
    """True when the alarming words are figurative, hypothetical or clearly mild."""
    if _matches(WISH_FRAME, line):
        return False
    return _matches(FIGURATIVE, line) or _matches(NOT_NOW, line) or _matches(MILD, line)


# The daily maximum printed on the packet. A count at or under it, with a day word and no sign,
# is the day's dose; anything else is left to the poisons case.
DAY_TOTAL_MAX = {"paracetamol": 8, "ibuprofen": 6}
_DAY_TOTAL_COUNT = re.compile(
    r"\b(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|"
    r"twenty|thirty|forty|fifty)\s+(?:of\s+)?(?:(?:the|my|his|her|their)\s+)?"
    r"(pills|tablets|paracetamol|ibuprofen|painkillers|analgesics|meds|medicines?)\b",
)
_DAY_TOTAL_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15,
                    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}


def _a_days_dose(line):
    """True when the count in the line is a day's total at or under the packet's own maximum."""
    if not _matches(DAY_TOTAL_WORD, line) or _matches(DAY_TOTAL_SIGN, line):
        return False
    # The maximum is for an adult who weighed up the box for themselves. A child who took a dozen
    # of anything, and a dog or a cat that did, is the poisons line or the vet whatever the count.
    if _matches((CHILD_TAKER, CHILD_WORD), line) or _matches(PET_OWN + PET_SUBJECT, line):
        return False
    for count, drug in _DAY_TOTAL_COUNT.findall(line):
        number = _DAY_TOTAL_WORDS.get(count)
        if number is None:
            try:
                number = int(count)
            except ValueError:
                continue
        # A count next to no drug name is the vaguest of the lot: treat it as the higher limit.
        if number <= DAY_TOTAL_MAX.get(drug, 8):
            return True
    return False


# Where the question starts. Most people type the mark or none at all: "what causes chest pain" and
# "why does my chest hurt" are the same question as the versions with a "?" at the end, and they
# were reaching the instructions for someone having it because the guard below wanted the mark.
# A softener in front ("ok so why does...", "and why...") is how a person carries on a chat.
QUESTION_OPENER = (
    r"^\W*(?:(?:ok|okay|so|and|but|well|oh|ah|hmm|actually|please|sorry|hi|hey)\b[ ,-]*)*"
    r"(?:what|whats|what's|why|how|when|where|which|who|whose)\b",
)


# "What is causing my chest pain" is the same question as "what causes chest pain", and the
# world-question patterns have no shape for it: a wh-opener, a word for causing, and the
# speaker's own part. It has to be the speaker's own ("my"), so "what makes him hit me" is not
# this shape and keeps its card.
ASKING_WHY_IT_HURTS = (
    r"^\W*(?:(?:ok|okay|so|and|but|well|oh|ah|hmm|actually|please|sorry|hi|hey)\b[ ,-]*)*"
    r"(?:what|whats|what's|why|how|which)\b[^.?!]{0,40}"
    r"\b(?:cause|causes|causing|caused|makes?|making|mean|means|behind)\b[^.?!]{0,20}"
    r"\b(?:my|mine)\b",
)


def _the_person_is_in_it(line):
    """True when the line is the person the thing is happening to, not a question about it."""
    if _matches(SAID_AS_IT_HAPPENS, line) or _matches(OWN_CRY, line):
        return True
    # A red flag said out loud is the person it is happening to, whatever the line opens with:
    # "why do i have a crushing pain in my chest" is not a question about causes. (CHEST_URGENT
    # is read here, not above, because it is defined further down the file with the chest cases.)
    return _matches(CHEST_URGENT, line)


def _asking_about_the_world(line):
    if line.rstrip().endswith("?") and _matches(WORLD_QUESTION, line):
        return True
    if _the_person_is_in_it(line):
        return False
    return ((_matches(WORLD_QUESTION, line) and _matches(QUESTION_OPENER, line))
            or _matches(ASKING_WHY_IT_HURTS, line))


# --- the cases -----------------------------------------------------------------------------

_SELF_WISH = r"(?:my\s*self|himself|herself|themselves|them\s*selves)"
# The speaker's own life, or a relative's: "ending it", "ending my life", "ending her own life".
_OWN_LIFE = r"(?:it(?!\s+with)\b|my\s+(?:own\s+)?life|(?:his|her|their)\s+(?:own\s+)?life)"
# The same thought with no verb of wanting in it: the shapes that can only be about a life,
# never about a lawn or a film. Kept beside _OWN_LIFE above, which the feeling and the habit of
# thought already use.
DESPAIR = (
    # The phrase has to end the thought: "nothing to live for on telly tonight" is a listings
    # line, and only "nothing left to live for" / "nothing to live for anymore" is the wish.
    r"\b(?:nothing|nowt)\s+(?:left\s+)?to\s+live\s+for\b"
    r"(?!\s+(?:on|in|at|for|around|round|here|there|about)\b)",
    # "life isnt worth living in that flat" is a complaint about the flat, not about living.
    r"\blife\s+(?:isn'?t|isnt|is\s+not)\s+worth\s+(?:it|living)\b"
    r"(?!\s+(?:in|for|at)\s+\w)",
    # "nobody would notice" is the same thought from the other side, but only when what follows
    # is a version of being gone: "nobody would notice if i changed the curtains" is a joke.
    r"\b(?:nobody|no\s?one)\s+would\s+(?:notice|care|miss\s+me)\b"
    r"(?=\s*(?:\?|$|[.,!]|\bany\s?more\b|\bat\s+all\b|\bif\s+i\s+(?:was|were|am)\s+(?:gone|"
    r"dead|not\s+here|no\s+longer\s+here)|\bif\s+i\s+(?:died|disappeared|wasnt\s+here|"
    r"werent\s+here|didnt\s+exist|wasnt\s+around|werent\s+around)\b))",
    # "i dont see the point anymore", "whats the point": only the shapes a person says about a
    # life, so "i dont see the point in watering it" stays a gardening line.
    r"\b(?:dont|don'?t|doesnt|doesn'?t|can'?t|cant)\s+see\s+the\s+point\s+"
    r"(?:in\s+)?(?:" + ANYTHING_LIFE + r"|any\s?more|any\s+of\s+(?:this|it)|of\s+"
    + ANYTHING_LIFE + r"|in\s+(?:" + ANYTHING_LIFE + r"|life|going\s+on|carrying\s+on)"
    r"|of\s+(?:it|this|that)\s+any\s?more)\b",
    # "there is no point anymore", "what is the point in anything": the same thought with the
    # verb spelled out and nothing after it, so a bare "whats the point" counts and
    # "whats the point of a wedding" does not.
    r"\bthere(?:'s|s|\s+is)\s+no\s+point\s*(?:\?|$|\bany\s?more\b|\bin\s+(?:anything|"
    r"any\s+of\s+(?:this|it)|life|going\s+on|carrying\s+on)\b|\bto\s+(?:anything|life)\b)",
    r"\bwhat(?:'?s|\s+is)\s+the\s+point\s*(?:\?|$|\bany\s?more\b|\bin\s+(?:"
    + ANYTHING_LIFE + r"|life|any\s+of\s+this|going\s+on)\b|\bof\s+(?:"
    + ANYTHING_LIFE + r"|life|going\s+on)\b)",
    # "i cant go on", and the version people send after a death, "i cant go on without her". The
    # verb has to end the phrase, so "i cant go on holiday", "i cant go on monday" and
    # "i cant go on living with my flatmate" stay ordinary, and "i cant go on like this" already
    # has its own arm above.
    # Any -ing after it is the activity that cannot go on: "i cant go on paying this rent" is a
    # money question, "eating like this" a diet one, "spending like this" a budget. Living and
    # existing are the exceptions, because those say the life, not the chore.
    r"\bi\s+(?:just\s+)?(?:cant|can'?t|couldnt|couldn'?t)\s+go\s+on\b"
    r"(?!\s+(?:(?:(?!living\b|existing\b)\w+ing\b)|living\s+(?:with|at|in)\b|"
    r"holiday|holidays|about\b|the|a\b|an\b|monday|tuesday|wednesday|thursday|"
    r"friday|saturday|sunday|\d|with\s+(?:my|his|her|"
    r"their|the|this)\b|in\s+(?:that|this|my|our)\b|stage\b|benefits\b|tour\b|shift\b|"
    r"train\b|bus\b|tub|tube|plane\b|flight\b|course\b|placement\b))",
    # "i cant see a way out", "i feel hopeless", "im so tired of everything": the bare
    # hopelessness people type without naming a wish, which reached only the flat acknowledgement.
    # Each one has to end the phrase, so the same words about a thing stay ordinary:
    # "i cant see a way out of this contract", "im hopeless at maths", "nothing left in the fridge".
    r"\b(?:i\s+)?(?:just\s+)?(?:cant|can'?t|couldnt|couldn'?t|don'?t|dont)\s+see\s+"
    # The way out is the situation, whatever length it is: "a way out of debt" and "a way out
    # of this contract" are both a money or a work question, and one word after "of" was
    # enough to let "of debt" reach the card.
    r"(?:a|any)\s+way\s+out\b"
    r"(?!\s+(?:of|from)\s+\w)",
    # "there is no way out" said with nothing after it is the same sentence as "i cant see a way
    # out", and it reached only "I'm listening". The situation is what follows "of"/"from"
    # ("no way out of this contract", "no way out of here"), so that stays ordinary.
    r"\b(?:there\s+is\s+|there'?s\s+|theres\s+)?no\s+way\s+out\b"
    r"(?!\s+(?:of|from)\s+\w)",
    # "i feel hopeless" is the speaker; "im hopeless at maths" is a skill.
    r"\b(?:i\s+)?(?:feel|feeling|felt|am|im|i'm)\s+"
    r"(?:so\s+|really\s+|totally\s+|completely\s+|pretty\s+|a\s+bit\s+)?hopeless\b"
    r"(?!\s+(?:at|with|in|about|of|for)\b)",
    # Tired of everything is the world, not a Tuesday: "tired of this show" stays ordinary, and
    # "tired of everything at work" is a job (burnout is not the card).
    r"\b(?:so\s+|really\s+|just\s+|sick\s+and\s+)?tired\s+of\s+"
    # Everything has to be the end of the thought: "im so tired of everything my boss does" is a
    # job, and "tired of everything at work" one too, while a comma or full stop keeps the wish
    # ("im so tired of everything, i could cry").
    r"(?:everything|it\s+all|all\s+this|all\s+of\s+this|life|being\s+here|existing)\b"
    r"(?=\s*(?:$|[.,!?;]|\band\b))",
    # "nothing left" on its own, after the bills are paid and after everything else has gone.
    r"\b(?:i\s+have\s+|i'?ve\s+got\s+|i\s+got\s+|there\s+is\s+|there'?s\s+)?"
    r"nothing\s+left\s*(?:\?|$|[.!]*$)",
    # "im done with living", "im fed up of living", "im sick of living", "im tired of living",
    # "ive had enough of living". The object is the life, not a room or a town, and every one of
    # them was reaching the annoyed pool: "Annoying. Walk it off for ten minutes before you reply
    # to anyone." "Living" has to end the thought, so "im done with the living room", "im sick of
    # living at home" and "im tired of living in this flat" stay ordinary (soft-ocelot, #safety
    # 41685, found on main `bc571218`).
    r"\b(?:i'?m|im|i\s+am|i'?ve|ive|i\s+have|i\s+feel|i\s+felt|i\s+was)\b[^.?!]{0,25}\b"
    r"(?:done|fed\s+up|sick|tired|had\s+enough)\s+(?:of|with)\s+(?:living|existing)\b"
    # The same rule as the flat wish above, and for the same reason: a word list of rooms and
    # towns only catches the ones somebody thought of, so "im tired of living alone", "im sick of
    # living a lie", "im tired of living by myself" and "im tired of living like this" were all
    # the crisis card on main. What follows "living" is either nothing, a tail that adds nothing,
    # or the living itself - and only the first two are the wish.
    + _FLAT_WISH_TAIL,
)

# The verbs that hurt a body, in one list because the same gap showed up in three places on the
# same day. The person's own wish: "i want to shoot myself" was answered "Shoot yourself — fair
# enough. What's stopped it happening so far?" (and "i want to strangle myself" the same). A
# relative's wish: "my sister wants to poison herself" was filed as a fact - "Noted: your sister
# wants to poison herself." An act a relative reports: "my friend shoots herself" and "my brother
# has been stabbing himself", both "Noted:". Every pattern in this file writes its own verbs out,
# and kill, hurt, cut, hang and overdose were the ones written down. Shooting, stabbing, poisoning
# and strangling were in no list at all, so the bot read the line as a choice somebody was
# describing rather than as a body somebody was in danger of.
A_BODY_HURTING = (
    r"(?:kill|kills|killing|killed|murder|murders|murdering|murdered|hurt|hurts|hurting|harm|"
    r"harms|harming|harmed|cut|cuts|cutting|starve|starves|starving|starved|shoot|shoots|"
    r"shooting|shot|stab|stabs|stabbing|stabbed|hang|hangs|hanging|hung|hanged|strangle|"
    r"strangles|strangling|strangled|choke|chokes|choking|choked|poison|poisons|poisoning|"
    r"poisoned|burn|burns|burning|burnt|burned|drown|drowns|drowning|drowned|overdose|overdoses|"
    r"overdosing|overdosed|slit|slits|slitting|smother|smothers|smothering|smothered)")
# The verb alone is not the thing: "shoot hoops", "a film to shoot", "strangle a yawn" and "i
# could murder a curry" carry it and no reflexive, and the myself/himself is what makes the line
# about a body. A verb with no reflexive keeps the answer it has today.
# Poisoning keeps the card it already has, which is about the container and the medics: "i want to
# poison myself" was answered well on main, and a wish frame must not take that away.
_HURTING_MYSELF = (r"\b(?!poison)" + A_BODY_HURTING + r"\s+my\s*self\b")
# "shot himself" and "hung himself" are left to the cards that already answer the act: the gunshot
# wound and the hanging both have an ambulance on them, and this arm is the one that explains how
# to help somebody who is still standing. "shoots herself" stays here, because the habit is not
# the wound.
_HURTING_THEMSELVES = (r"\b(?!(?:shot|hung|hanged)\b)" + A_BODY_HURTING
                       + r"\s+(?:him|her|them)sel(?:f|ves)\b"
                       # The idiom is in what follows the reflexive: "my son kills himself
                       # laughing" is a joke and "he kills himself at work" or "at the gym" is an
                       # effort. The effort and laugh guards in this file are written for the first
                       # person ("killed myself carrying the sofa"), so the third person had none,
                       # and a wider verb list would have handed a helpline to a joke.
                       + r"(?!\s+laughing\b)(?!\s+out\b)(?!\s+(?:at|in|on)\s+(?:the\s+)?"
                         r"(?:work|gym|office|job|building\s+site|training)\b)"
                       # The effort said with the doing after it: "kills himself trying to be
                       # everything to everyone", "she kills herself to keep everyone happy".
                       # The doing that follows is a purpose, so the verb is about effort.
                       + r"(?!\s+(?:trying|keeping|making|pleasing|doing|working|getting|"
                         r"being|to\s+(?:keep|make|please|get|be|help|prove|show))\b)"
                       # Something went down the wrong way: "my son choked himself on a sweet"
                       # is the choking first aid, not a wish. "on purpose" is still an act.
                       + r"(?!\s+on\s+(?!purpose\b))"
                       # The medicine given with a device: "he stabs himself with the epi pen".
                       + r"(?!\s+with\s+(?:the|his|her|their|my|an?)\s+(?:epi\s?pen|epipen|"
                         r"insulin\s?pen|inhaler|syringe|auto[-\s]?injector|needle))")

# The wish said about the medicine rather than about a verb: "i want to take all my pills". The
# act itself was read ("i took all my pills" is the poisons card), but the wish for it was answered
# as a plan worth doing. The quantity is what makes it a container and not a dose: "i want to take
# my pills", "i want to take all my pills to the pharmacy" - a line that says why - keep what they
# have, and "i take my pills at night" has no quantity and never reaches here.
_SOME_OF_A_MEDICINE = (
    r"\b(?:take|taken|taking|took|swallow|swallowed|swallowing|down|downing|downed|neck|necking|"
    r"necked|pop|popping|popped)\s+(?:all\s+(?:of\s+)?|the\s+rest\s+of\s+|"
    r"a\s+(?:whole|bunch|load|handful)\s+of\s+)(?:my|these|those|the)?\s*"
    r"(?:pills?|tablets?|capsules?|caplets?|meds|medication|painkillers?|paracetamol|ibuprofen|"
    r"antidepressants?|sleeping\s+pills?|tranquill?i[sz]ers?)\b")

SELF_HARM = (
    r"\b(?:kill|killing|killed|hurt|hurting|harm|harming|cut|cutting|starve|starving)\s+my\s*self\b",
    # The same wish with a verb nobody had written down, in a wish frame so that "i could shoot
    # myself" (which people say about being embarrassed) and "we shot some hoops" keep what they
    # have. "im thinking of shooting myself" is the same wish said as a thought.
    r"\b(?:want|wanna|wanting|going|gonna|plan|planning|planned|ready|decided|thinking\s+of|"
    r"thinking\s+about|thought\s+of|thought\s+about)\s+(?:to\s+)?" + _HURTING_MYSELF,
    r"\b(?:want|wanna|wanting|going|gonna|plan|planning|planned|ready|decided|thinking\s+of|"
    r"thinking\s+about|thought\s+of|thought\s+about)\s+(?:to\s+)?" + _SOME_OF_A_MEDICINE,
    *SELF_HARM_CUT_NO_OBJECT,
    # The same wish said with a body part after the verb instead of "myself", or with the
    # means ("under a train", "shoot myself"); both live in `safety_more.py` under the cap.
    *SELF_HARM_OWN_PART,
    *SELF_HARM_FLAT_WISH,
    # "im going to end it with him" ends the relationship, not the person: the thing after
    # "with" is a person, so the "it" is the marriage and not their life. `_OWN_LIFE` has the
    # same guard for the other wordings; this pattern spelled "end it" out, so it missed it.
    r"\b(?:want|wanna|wanting|going|plan|planning|ready|decided)\s+to\s+(?:die|kill\s+my\s*self|"
    r"end\s+(?:it(?!" + END_IT_WITH + r")|my\s+life))\b",
    # The wish said as a thought rather than a plan: "i keep thinking about suicide" needed the
    # suicide word, and "i think about dying every night" had nothing at all. The thought has to
    # be the speaker's own, and "dying my hair" is the dye.
    r"\bi\s+(?:keep\s+|often\s+|sometimes\s+|constantly\s+|still\s+|just\s+|really\s+|"
    r"cant\s+stop\s+|can'?t\s+stop\s+)?(?:think|thinking|thought)\s+(?:about|of)\s+"
    r"(?:dying(?!\s+(?:my|her|his|their|our)\s+hair)|killing\s+my\s*self|"
    r"ending\s+it(?!" + END_IT_WITH + r")|suicide|self[-\s]?harm)\b",
    # "alive" is the same state as "live": "i dont want to be alive", "i just dont want to be
    # alive", "i dont want to be alive anymore" were the greeting and a shrug on main, because
    # every arm spelled the state as live, here or exist. A wish with "any more people" after
    # "around" is a quantity, so that arm now wants the end of the thought (zippy-kangaroo, #5601).
    # The wish is the bare verb, so each arm says what makes the words the thing instead: "i dont
    # want to live in a flat", "i dont want to go on holiday", "i dont want to carry on with the
    # course" and "i dont want to wake up early" are a plan and a morning, and the card answered
    # every one of them (slate-fan, #safety 144082). What follows has to be a reason ("without
    # him", "anymore", "like this") rather than the object the verb is about.
    r"\bdon't\s+want\s+to\s+(?:"
    r"live\b(?!\s+(?:in|at|on|near|next\s+to|off|abroad|with)\b)"
    r"|be\s+alive(?!\s+(?:in|on)\s+(?:that|this|the)\s+(?:photo|picture|pic|video|footage|"
    r"stream|recording|thumbnail)\b)"
    r"|be\s+here|exist"
    # "early" and a time are the morning; "tomorrow" is not. sleek-sparrow (#safety 144082)
    # measured the fence down to a shrug on "i dont want to wake up tomorrow": the one word that
    # ends the day is also the one word that line is made of.
    r"|wake\s+up\b(?!\s+(?:early|at\s+(?:\d|one\b|two\b|three\b|four\b|five\b|six\b|seven\b|"
    r"eight\b|nine\b|ten\b|eleven\b|twelve\b|noon\b|midnight\b|dawn\b|sunrise\b)|before\b|"
    r"by\b|so\b))"
    # "with" has no word end, so `\s+with` was also reading "without": "i dont want to carry on
    # without him" was the plan, and "without" is the reason the line is a wish.
    r"|(?:carry|go)\s+on\b(?!\s+(?:with\b|the\b|a\b|an\b|to\b|about\b|in\b|on\b|holiday|"
    r"holidays|course|(?:(?!living\b|existing\b)\w+ing\b))))",
    # An object is what the verb is about; a reason is the end of the thought, and it says the
    # wish whatever object came before it: "i dont want to live with myself anymore", "... at home
    # anymore", "... in this world anymore", "i dont want to go on without her". The exclusions
    # above are for the object, so this arm reads past them (sleek-sparrow, #safety 144082).
    r"\bdon't\s+want\s+to\s+(?:live|be\s+alive|be\s+here|exist|wake\s+up|(?:carry|go)\s+on)\b"
    r"[a-z']{0,20}(?:[\s'][a-z']{1,15}){0,4}\s+(?:any\s?more|no\s?more|at\s+all|altogether|"
    r"for\s+good|without\s+(?:him|her|them|you|it|anyone|anybody|myself|my\s+\w+))\b",
    # The same wish said as the state stopping rather than the living ending: "i want to stop
    # existing", "i want to not be alive". The end-of-clause lookahead keeps out "i want to stop
    # existing on social media", where the words are about an account.
    r"\b(?:want|wants|wanted|wanting|wanna)\s+to\s+(?:not\s+(?:be\s+alive|exist)|"
    r"stop\s+(?:existing|being\s+alive))\b"
    r"(?=\s*(?:$|[.,!?;]|\b(?:any\s?more|no\s?more|at\s+all|now|tonight|altogether|for\s+good)\b))",
    # "i dont want to be around anymore" is about being alive; "i dont want to be around people"
    # is the party, so the words that follow have to be the ones that end the thought.
    r"\bdon't\s+want\s+to\s+be\s+around\s+(?:any\s?more|no\s?more)\b"
    r"(?=\s*(?:$|[.,!?;]|\b(?:at\s+all|now|tonight|today|altogether|ever|for\s+good)\b))",
    r"\bno\s+(?:reason|point)\s+(?:to|in)\s+(?:live|living|going\s+on|carrying\s+on)\b",
    r"\bbetter\s+off\s+(?:dead|without\s+me|if\s+i\s+was\s+gone|if\s+i\s+weren't\s+here)\b",
    r"\bsuicid(?:e|al)\b", r"\bself[-\s]?harm(?:ing|ed)?\b",
    r"\boverdos(?:e|ed|ing)\b",
    r"\b(?:took|taken|swallowed|had)\s+(?:too\s+many|a\s+(?:whole|bunch|load|handful)\s+of)\s+(?:pills|tablets|paracetamol|ibuprofen|meds)\b",
    r"\b(?:thinking|thought|thinking\s+about)\s+(?:about\s+)?(?:killing\s+my\s*self|suicide|ending\s+(?:it|my\s+life)|not\s+being\s+here)\b",
    # The wish said as a feeling: "i feel like ending it", "i feel like ending my life". Main
    # answered those two with "Got it. Is there anything you would like a hand with?", which is
    # the one reply this file exists to keep away from them. A feeling of embarrassment or of
    # laughing is not the wish: "i feel like dying of embarrassment", "i feel like dying laughing".
    r"\b(?:feel|feels|felt|feeling)\s+(?:like|as\s+if)\s+(?:ending\s+" + _OWN_LIFE + r"|dying"
    r"|kill(?:ing)?\s+" + _SELF_WISH + r"|not\s+being\s+here)\b"
    r"(?!\s*(?:,|:)?\s*(?:of\s+(?:embarrass\w*|shame|laughter|boredom)|laughing|embarrass\w*|mortified"
    r"|cringe\w*|my\s+hair))",
    # The same wish as a habit of thought rather than a plan: "i keep thinking about ending it",
    # "she keeps thinking of killing herself", "i think about ending my life every day".
    r"\b(?:keep|keeps|kept)\s+(?:thinking|having\s+thoughts)\s+(?:about|of)\s+"
    r"(?:ending\s+" + _OWN_LIFE + r"|killing\s+" + _SELF_WISH + r"|suicide|dying|not\s+being\s+here)\b",
    # The same habit with "have" instead of "keep", said by the person themselves: "im having
    # thoughts of ending it", "i have thoughts about suicide", "i had thoughts of ending it last
    # night", "ive been having thoughts of suicide". The habit above is the only place "having
    # thoughts" was read, so it needed the "keep" in front of it, and main answered "im having
    # thoughts of ending it" with "Got it. Is there anything you would like a hand with?" - the
    # reply this file exists to keep away from it. Two things are left out on purpose:
    #   * "thoughts of dying", which is the shape of health anxiety as much as of the wish
    #     ("i have thoughts of dying of embarrassment" is about a work presentation);
    #   * somebody else's habit ("my son has thoughts of killing himself"). That is the other
    #     person's card, and the turn after it is the helper asking what to say, which this file
    #     answers with its own generic line instead of the answer the greeting has for it.
    r"\b(?:i|im|i'?m|ive|i'?ve|id|i'?d)\b[^.?!]{0,12}?\b(?:have|had|having)\s+thoughts?\s+"
    r"(?:about|of)\s+(?:ending\s+" + _OWN_LIFE + r"|killing\s+" + _SELF_WISH + r"|suicide|"
    r"not\s+being\s+here)\b",
    # The same with no subject at all, which is still the speaker: "having thoughts of ending it
    # again", "been having thoughts of suicide".
    r"^\s*(?:just\s+|been\s+|still\s+|and\s+)?(?:having|had)\s+thoughts?\s+(?:about|of)\s+"
    r"(?:ending\s+" + _OWN_LIFE + r"|killing\s+" + _SELF_WISH + r"|suicide|not\s+being\s+here)\b",
    r"\bthink(?:s|ing)?\s+(?:about|of)\s+(?:ending\s+" + _OWN_LIFE + r"|killing\s+" + _SELF_WISH + r"|suicide)\b",
    r"\bend\s+(?:it\s+all|my\s+(?:own\s+)?life)\b",
    # "I feel like ending it all" is the same line as "I want to end it all": the gerund hides it
    # from the infinitive, and it is the phrase a person types when they are least able to spell.
    r"\bend(?:ing)?\s+(?:it\s+all|my\s+(?:own\s+)?life)\b",
    r"\bcan't\s+(?:go\s+on|carry\s+on)\s+(?:any\s?more|like\s+this)\b",
    r"\b(?:hang|hanged|hung|hanging)\s+my\s*self\b",
    # Wanting to do it is a thought, not an act: "i want to hang myself", "thinking of hanging
    # myself", "my brother wants to hang himself". The hanging reply is for what already happened.
    r"\b(?:wants?|want|wanna|wanting|going|plan|plans?|planning|thinking|thought|thoughts|"
    r"considering|tempted|ready|decided|feels?\s+like)\b[^.?!]{0,18}\b(?:to\s+)?(?:hang|hanging|"
    r"jump|jumping|drown|drowning)\s+(?:my\s*self|himself|herself|themselves|off\s+(?:a|the|this)\s+"
    r"(?:bridge|roof|building|cliff|balcony|ledge|car\s*park))\b"
    r"(?!\s+in\s+(?:work|emails?|paperwork|admin|debt|chores|housework))",
    # ...and the same thought with the traffic as the method: "i thought about stepping in front
    # of a bus", "i keep thinking about walking in front of a train". The act arm below takes the
    # step itself, and nothing took the thinking about it, so these were a shrug.
    r"\b(?:thought|thoughts?|thinking|kept\s+thinking|keep\s+thinking|keeps\s+thinking|dreamt|dreaming)"
    r"\s+(?:about|of)\s+(?:step|stepping|walk|walking|stand|standing|lie|lying|lay|jump|jumping|throw|throwing)"
    r"\s+(?:my\s*self\s+)?(?:"
    # Standing in front of it or under it only ever means one thing, so those two take the vehicles.
    r"(?:in\s+front\s+of|under)\s+(?:traffic|(?:a\s+|the\s+)?bus|(?:a\s+|the\s+)?train|"
    r"(?:a\s+|the\s+)?car|(?:a\s+|the\s+)?lorry|(?:a\s+|the\s+)?truck)"
    # Going into or onto one is mostly getting on it: "i thought about jumping into the car to get
    # out of the rain" is a person getting out of the rain, and "jumping onto the bus" is catching
    # it. So `into|onto|on` only take the traffic itself and the track, never the vehicle.
    r"|(?:into|onto|on)\s+(?:traffic|the\s+tracks|the\s+track|the\s+railway\s+line)"
    r")\b"
    r"(?!\s+(?:queue|stop|station|doors?|board|platform|screen|ticket\s+machine|shelters?|awning|"
    r"canopy|umbrella))"
    # ...and the definite article is why "i thought about walking in front of the train" rang
    # nothing (lively-notebook): the arm wanted "a train" and people say "the train".
    # A photo is not a method, so a line that gives its own reason stands the card down: "i
    # thought about standing on the railway line to take a photo" was the crisis card.
    r"(?![^.?!]*\b(?:photo|photos|picture|pictures|pic|pics|selfie|selfies|photograph|"
    r"photographs)\b)",
    # "i could jump off a bridge": the first person and the place make it a risk, not a swim.
    r"\bi\b[^.?!]{0,20}\b(?:could|would|might|should|want\s+to|going\s+to)\s+(?:jump|jumping)\s+"
    r"(?:off|from)\s+(?:a|the|this)\s+(?:bridge|roof|building|cliff|balcony|ledge|car\s*park)\b"
    r"(?!\s+into\s+the\s+(?:pool|water|sea|lake|river|hay|snow))",
    # "i feel like drowning myself in work" is about the workload, not the wish.
    r"\b(?:drown|drowning)\s+my\s*self\b(?!\s+in\s+(?:work|emails?|paperwork|admin|debt|chores|"
    r"housework|the\s+washing))",
    # Shut in a room with the means: "my wife has locked herself in the bathroom with pills".
    r"\blocked\s+(?:him|her|them)sel(?:f|ves)\s+in\b.{0,40}\b(?:pills|tablets|razor|blades?|knife)\b",
) + DESPAIR + WISH_BY_MODAL
# "nothing left" is the last clause of `DESPAIR`, and it is the one a money line reaches by
# accident: "i get paid on friday and i have nothing left" ends on the same three words as
# "i have nothing left", and what came back was a crisis line to someone whose week was short
# (@sure-umbrella, #safety). The clause is read on its own here so the self_harm case can stand
# down for it without touching `DESPAIR`, `SELF_HARM` or the band.
_NOTHING_LEFT_PROBE = "i have nothing left"


def _nothing_left_clause():
    """The `nothing left` arm of `DESPAIR`, found by what it matches, not by where it sits.

    It was read as `DESPAIR[-1:]`, and `DESPAIR` is a tuple other changes append arms to: put one
    after this clause and the stand-down below starts reading the new arm instead, which is how
    the next arm was silently swallowed on #3036. The probe is the sentence the clause is for, so
    the last arm that still matches it is the clause, whatever is added after it.
    """
    for clause in reversed(DESPAIR):
        try:
            if re.search(clause, _NOTHING_LEFT_PROBE, re.I):
                return (clause,)
        except re.error:
            continue
    return DESPAIR[-1:]


NOTHING_LEFT = _nothing_left_clause()
# ... and the arms *other* than that clause are the ones that keep a money line on the card.
# `DESPAIR[:-1]` said the same thing while the clause sat last, and it stopped being true the
# day an arm was appended after it: the clause came back into the "something else rang" list, the
# stand-down below could never be reached again, and "i get paid on friday and i have nothing
# left" went back to a crisis line while `tests/test_nothing_left_money.py` went red on main.
DESPAIR_WITHOUT_NOTHING_LEFT = tuple(clause for clause in DESPAIR if clause not in NOTHING_LEFT)
# The phrase tables that stood here live in `bot/modules/safety_phrases.py`: this module was
# 56 KB over the world's 1 MiB per-file cap, and `open_pr` refuses every PR that touches a file
# over it, so the whole safety lane was frozen. The tables are imported back at the same point,
# in the same order, so nothing below this line changes.
from .safety_phrases import (  # noqa: F401 - named so the undefined-name guard can see them
    ABUSE, ABUSER, ABUSE_DISCLOSURE,
    ABUSE_DISCLOSURE_FINE, ABUSE_FINE, ABUSE_HEAD_INTO,
    ABUSE_HIT_ME, ABUSE_MEMORY, ABUSE_NOW,
    ABUSE_PURSUIT_HARD, ABUSE_VERB, ABUSE_VERBAL,
    ABUSE_VERBAL_FINE, ABUSE_VERBAL_LABEL, ABUSE_VERBAL_MAD,
    ABUSE_VERBAL_PERSON, ABUSE_VERBAL_SUBJECT, ABUSE_VERB_PART,
    ASK_AFTER_ME, BLOW_THINGS, CHILD_AGGRESSOR,
    CHILD_HIT_NOW, CLOSE, DYING_OTHER,
    GAME_AFTER_ME, GAME_PLAYED, GAME_WORD_STOP,
    GRIP_GAME, GRIP_GAME_FENCE, GRIP_NOT_AN_ASSAULT,
    GAME_NOT_A_BLOW, GRIP_NOT_AN_ASSAULT_STR, HAS_ME_SUBJECT, HIT_AS_A_CHILD,
    HIT_BY_A_VEHICLE, HIT_THING_NOT_PERSON, I_DID_NOT_HIT,
    I_HIT_SOMEONE, MONEY_NAMED, NOT_A_FEAR,
    OTHERS, PARTNER_CLOSE, PEOPLE,
    PERSON, PLAY_FACE_REPLIES, PURSUIT,
    PURSUIT_FEAR, PURSUIT_LOUD, PURSUIT_OUTSIDE,
    PURSUIT_PLACE_WORK, PURSUIT_SUBJECT, PURSUIT_SUBJECT_EX,
    REMORSE_FOR_THE_ACT, SELF_HARM_NEEDS_PERSON, SELF_OWN_DYING,
    SOFT_FACE_PUSH, SOFT_FACE_STOP, SOMEONE_HOLDS_THE_MONEY,
    THREAT_COERCIVE, THREAT_SUBJECT, _NOT_A_THREAT,
    _REFUSED_EXIT, _THE_BLOW, _THE_HAND,
    _THE_ONE_HIT, _both_here,
)


# A parent saying no is parenting, not coercive control: "my mum wont let me go out", "my parents
# wont let me see my friends", "my mum wont let me have my phone" and "my dad wont let me speak to
# my friends" are the ordinary life of a teenager, and the refusal arms above (which are right for
# a partner or an ex) were reading them as domestic abuse. The parent has to be the subject and a
# blow, a hand on the body or a lock keeps the card: "my dad wont let me leave and he hits me" is
# not a rule about going out.
# A child who will not let you sleep or leave the room is a Tuesday, not a hand: "my son wont let
# me sleep", "my toddler wont let me leave the room", "my kids wont let me sit down" are the life
# of a parent, and the refusal arms above reach them because a son and a daughter are in the list
# of people who can hurt you. The card is for the adult who will not let you out, so a child as
# the subject stands these arms down - and a blow, a threat or a hand in the line puts it back.
# The money is the exception: a grown son who will not let a parent have their own money is taking
# the pension, which is abuse of an older person, so the exit words only cover the days.
ABUSE_CHILD_TAKES_MONEY = (
    r"\b(?:money|wages|pay|pension|pensions|benefits|bank\s+card|debit\s+card|bank\s+account|"
    r"keys|savings|my\s+own\s+money)\b",
)


# The harmless reason is for the family and the friends. A partner or an ex who backs you into a
# room "for a hug" is still the card, whatever the reason says.
ABUSE_PARTNER_DID_IT = (
    r"\bmy\s+(?:husband|wife|partner|boyfriend|girlfriend|ex|fiance|fiancee|stepdad|stepmum|"
    r"stepmom|carer)\b[^.?!]{0,25}\b(?:corner(?:ed|s)?|pinned|trapped|backed|blocked|pushed|"
    r"shoved|held)\b",
)


# `hit me with a joke` is a figure of speech, not a hit in fun: the thing after `with` is the
# instrument, and the blow-beside-it machinery owns those lines.
HIT_WITH_A_THING = (
    r"\bh(?:it|its|itting|urt)\s+(?:me|us|him|her|them)\s+with\s+"
    r"(?:a|an|the|his|her|their|my|your)\b",
)
# ...unless somebody grown-up hit the speaker in the same line: "my son hit me while playing but
# my husband hit my face" is still the card, and the child's game must not stand it down.
# A two year old who bites or hits their parent is a stage, not a violent partner. "he bites me
# when i pick him up", said straight after "my son is 2 and keeps hitting", got the abuse card:
# 999 and a domestic abuse helpline, to a parent asking how to stop a toddler biting. The child is
# named the ways parents name one, and usually named in the turn that starts the thread rather
# than in the answer, so the last few of their lines are read as well as this one. A teenager, a
# partner or any other adult is not this: ADULT_HIT and the other stand-downs are untouched.
# A grandchild is a small child only when an age comes with the word: "i look after my grandson"
# then "he hits me" is a fifteen year old as easily as a two year old, and the age text went to a
# grandmother who may have been hit by a grown one (azure-trout, #7433).
_GRANDCHILD_OF_AN_AGE = (
    r"(?:little|small|young|baby|toddler)\s+(?:grandson|granddaughter)|"
    r"(?:grandson|granddaughter)\s+(?:is\s+)?(?:one|two|three|four|1|2|3|4)\b|"
    r"(?:one|two|three|four|1|2|3|4)\s*(?:year|yr)[\s-]*old\s+(?:grandson|granddaughter)")
A_SMALL_CHILD_SAID = re.compile(
    r"\b(?:toddlers?|nursery|pre-?school|playgroup|bab(?:y|ies)|small\s+child|"
    r"(?:one|two|three|four|1|2|3|4|eighteen|18)\s*(?:year|yr)[\s-]*old|"
    r"(?:eighteen|18)\s*months?|little\s+(?:boy|girl|one|lad|fella)|"
    r"" + _GRANDCHILD_OF_AN_AGE + r"|"
    r"my\s+(?:son|daughter|boy|girl)\s+is\s+(?:one|two|three|four|1|2|3|4)\b)\b",
    re.IGNORECASE)
A_GRANDCHILD_OF_AN_AGE = re.compile(_GRANDCHILD_OF_AN_AGE, re.IGNORECASE)
# A blow only a grown body lands. A punch to the stomach, the ribs or the groin is not a two year
# old's, whatever the pronoun says, and the child text is the wrong answer to it (azure-trout).
A_GROWN_BLOW = re.compile(
    r"\b(?:punch(?:es|ed|ing)?|knee(?:s|d)?|head[-\s]?butt(?:ed|s|ing)?)\b[^.?!]{0,24}"
    r"\b(?:stomach|belly|ribs?|groin|kidneys?|back|jaw|nose)\b",
    re.IGNORECASE)
# The blows a small child lands: biting, hitting, kicking, scratching, slapping, hair pulling. A
# threat, a hand round the throat or a weapon is not on this list, so those keep the card.
A_LASH_VERB = (r"bit(?:es|ing)?|hits?|hitting|kick(?:s|ed|ing)?|scratch(?:es|ed|ing)|"
               r"slap(?:s|ped|ping)?|thump(?:s|ed|ing)?|punch(?:es|ed|ing)?|"
               r"pull(?:s|ed)?\s+my\s+hair|spit(?:s|ting)?")
A_SMALL_CHILD_LASHES_OUT = re.compile(
    r"\b(?:" + A_LASH_VERB + r")\s+(?:at\s+)?me\b",
    re.IGNORECASE)
# The same blow with nobody named before it: "he bites me", "hes biting me", "she hit me". A line
# whose actor is a bare pronoun is the only one the child named three lines ago can answer for
# (see `_a_small_child_did_it`).
A_BARE_ACTOR_LASH = re.compile(
    r"\b(?:he|she|it|hes|shes|they|theyre)\b(?:\s+\w+){0,2}?\s+(?:" + A_LASH_VERB + r")"
    r"\s+(?:at\s+)?me\b",
    re.IGNORECASE)


# The replies above name the child in their own words, so the turn after one of them has"
# something to read: "he hit me in the face" is a lash line and the child is in the answer before"
# it (kind-mug, #7433). Matched by phrase because `_fit` rewrites the line's pronouns."
SMALL_CHILD_REPLY_GIVEN = re.compile(
    r"that is what a small child does|last things a small child drops|"
    r"a small child has no other way to say", re.IGNORECASE)


def _a_small_child_did_it(line, memory):
    """True when the bite or the blow came from a small child, on this line or a recent one."""
    if not A_SMALL_CHILD_LASHES_OUT.search(line):
        return False
    # The line's own age wins over the memory's: "hes 15 and he hits me" after a turn about a two
    # year old is a teenager (kind-mug, #7433).
    if A_GROWN_AGE.search(line):
        return False
    if A_SMALL_CHILD_SAID.search(line):
        return True
    if A_GROWN_BLOW.search(line):
        return False
    # A child named three lines ago is not the one who did it unless this line leaves the actor
    # unnamed. "my son is 2 and keeps hitting" then "my grandad hits me" is an adult hitting the
    # speaker, and reading the earlier child there handed the toddler text to a grown man's blow -
    # the one mistake in this module that can cost somebody (brown-magpie, #7433). So the memory
    # answers only for a line whose actor is a bare "he", "she" or "it".
    if not A_BARE_ACTOR_LASH.search(line):
        return False
    said = ""
    for turn in reversed((memory.get("turns") or [])[-3:] if isinstance(memory, dict) else []):
        if isinstance(turn, dict) and turn.get("user"):
            said += " " + _norm(str(turn["user"]))
        # The bot's own answer counts too, because it names the child when the person did not:
        # after the age reply the chat says "he hit me in the face" with no child in the line, and
        # the turn after that is the one a parent really sends next (kind-mug, #7433).
        if isinstance(turn, dict) and turn.get("bot") \
                and SMALL_CHILD_REPLY_GIVEN.search(_norm(str(turn["bot"]))):
            said += " " + _norm(str(turn["bot"]))
    return bool(A_SMALL_CHILD_SAID.search(said))


# A lender demanding money threatens, and "they" in that line is the lender, not the person they
# live with: `i owe money to a loan shark and they are threatening me` was taking the abuse card,
# which sends someone in real danger to the wrong phone number. The loan-shark answer has Stop
# Loan Sharks on it, so the card stands back for a lender - but only while no person is named.
# `my husband threatens me when i ask for money and the loan shark keeps ringing me` and
# `my partner hit me over the money i owe a loan shark` are one person in danger who also owes a
# lender, and they keep the card. A named person is what decides it, not a pronoun: "they" in the
# loan-shark line is the shark.
# The lenders a person can name. A bailiff or a debt collector is left out on purpose: neither
# has an answer of its own on the other side, so the card is still the best reply for those, and
# "my landlord pushed me" keeps it (tests/test_safety.py WhoHitYouTest).
LENDER_FINE = (
    r"\b(?:loan\s*-?\s*sharks?|loan\s+sharking|illegal\s+lender|unlicensed\s+lender|"
    r"money\s*lenders?|payday\s+lenders?|payday\s+loans?)\b",
)
NAMED_PERSON = (
    r"\b(?:my|his|her|their|our)\s+(?:" + ABUSER + r")\b",
)

# A loss can hit you hard: "the death of my wife has hit me hard", "my wife's death has hit me
# hard", "losing my wife has hit me hard", "when my mum died it hit me hard". The person is in the
# line and the verb says "hit me", so the alarm above rings for a bereavement. The subject of the
# verb is what decides it - a death, a loss, a funeral is not the one who hit anybody - so the
# abuse case stands down for those, and only when no other arm of it rings ("... and he won't let
# me leave" is still abuse). The words that can stand between the subject and the verb:
_HIT_ME = re.compile(r"\b(?:hits?|hitting|knocked|knocks?|beats?|punched)\s+(?:me|us)\b")
_SUBJECT_TAIL = re.compile(
    r"(?:\s+(?:has|had|have|really|just|nearly|almost|so|properly|completely|truly|still|also|"
    r"it|its|it's|that|this|which|and|then))*\s*$")
LOSS_SUBJECT_AT_END = tuple(pattern + r"\s*$" for pattern in LOSS_SUBJECT)
# Every arm of the abuse case except the "hit me" one: a loss can be the subject of a hit and the
# case still stands down, but only when nothing else in the line rings.
ABUSE_NOT_HIT = THREAT_COERCIVE + tuple(
    arm for arm in ABUSE[len(THREAT_COERCIVE):] if arm not in ABUSE_HIT_ME)


def _hit_by_a_loss(line):
    """True when every "hit me" in the line has a loss, not a person, as its subject."""
    clauses = list(_HIT_ME.finditer(line))
    if not clauses:
        return False
    for match in clauses:
        window = _SUBJECT_TAIL.sub("", line[max(0, match.start() - 80):match.start()])[-60:]
        # It is the subject of the verb, so the loss has to be what the window ends on: "at my
        # dad's funeral my husband hit me hard" has a funeral in it, and the husband is the one
        # doing the hitting.
        if not _matches(LOSS_SUBJECT_AT_END, window):
            return False
    return True


# The ways a line that has already said "not safe" carries on being this case: it stops there,
# or it says where, or it names the person.
STOP_TAIL = (r"\s*(?:$|[.,!?;]|(?:because|since|when|whenever|if|now|at\s+all|anymore|"
             r"any\s?more|tonight|today|again|at\s+the\s+moment|at\s+night|right\s+now|"
             r"in\s+the\s+end)\b)")
WHERE_TAIL = (r"\s+(?:at\s+home|at\s+work|at\s+night|where\s+i\s+live|here|on\s+my\s+own|"
              r"in\s+(?:my|the|this|our)\s+(?:own\s+)?(?:home|house|flat|place|bed)|"
              r"where\s+i\s+(?:live|am)|where\s+we\s+live)\b")
PERSON_TAIL = r"\s+(?:with|around|near|by|on)\s+(?:\w+\s+){0,3}" + _PERSON + r"\b"
# `where` and `on my own` are a state of a person, so they keep the reply; a thing does not.
_SAFE_TAIL = "(?=" + STOP_TAIL + "|" + WHERE_TAIL + "|" + PERSON_TAIL + ")"
UNSAFE = (
    r"\b(?:i'?m|im|i\s+am)\s+not\s+safe\b" + _SAFE_TAIL,
    r"\b(?:i\s+)?(?:don'?t|do\s+not|dont)\s+feel\s+safe\b" + _SAFE_TAIL,
    r"\bnot\s+safe\s+(?:at\s+home|in\s+my\s+own\s+(?:home|house|flat)|where\s+i\s+live|here|"
    r"in\s+my\s+house|in\s+the\s+house)\b",
    # A road, a climb, a journey, a gym, a dog or a body part that will not hold is a worry
    # about a thing, and the abuse reply would name a person who is not in the line: "i feel
    # unsafe on the motorway", "on the stairs", "on this ladder", "walking home", "at the gym",
    # "lifting heavy", "in the dark", "in danger on my bike". This tail is the negative list,
    # and only for this case: where they live, who they live with, a relationship and a time of
    # day are the shape the case exists for ("i feel unsafe in my bedroom", "at his flat", "in
    # my marriage", "in the evenings", "about going back"), and a positive list of tails that
    # *keep* the reply dropped all five into the honest shrug. A list of things cannot be
    # complete either way, so it names the ones people write.
    r"\b(?:i\s+)?feel\s+(?:unsafe|in\s+danger)\b(?!\s+(?:" + _AWAY_TAIL + r"))",
)

# Flames are the fire whatever they are coming out of: "flames coming out of the toaster" was a
# shrug, and a toaster with flames in it is not a toaster with crumbs in it. The idioms that only
# borrow the word - an old flame, flame grilled, flame retardant, a flame effect heater - are stood
# down here, and each arm below needs the flame to be doing something (coming, pouring, spreading)
# or to be seen, so the borrowed ones never reach the fire card.
# A place that is built to hold a flame is not a fire: a barbecue, a grill, a lit fireplace, a
# wood burner, a candle and a fire on a screen all have flames in them by design, and telling
# someone to leave the building for the fat on their barbecue makes the card noise. The toaster,
# the socket and the sofa are the ones that should not have flames, so the arms below name the
# things that should rather than widening the stand-down.
# The things a flame belongs in, kept as a name so the stand-down can ask for it in the same
# breath as the flame word.
_FLAME_THING = (
    r"\b(?:fireplace|fire\s*place|wood\s*burner|woodburner|log\s*burner|multi\s*fuel\s*burner|"
    r"grill|grille|barbecue|barbeque|bbq|barbie|fire\s*pit|brazier|candle|candles|"
    r"wood\s*stove|log\s*fire|coal\s*fire|open\s*fire|stove|hob|rings?)\b"
)
FLAMES_NOT_FIRE = (
    r"\b(?:old|twin|former|new)\s+flames?\b",
    r"\bflames?\s+(?:grilled|grill|retardant|proof|effect|test|war|thrower|pit|bait)\b",
    r"\bflame\s*proof\w*\b",
    # "flames coming out of the barbecue", "flames coming off the grill", "there are flames in
    # the fireplace", "i can see flames in the wood burner". The source and the flame have to be
    # in the same breath, so "the grill caught fire and the kitchen is burning" keeps the card.
    _FLAME_THING + r"[^.?!]{0,30}\bflames?\b",
    r"\bflames?\b[^.?!]{0,30}" + _FLAME_THING,
    # A fire somebody has just lit has flames: "i lit the fire and now there are flames".
    r"\b(?:lit|light|lighting|lighted|made|make|making|started|starting|built|build|put)\s+"
    r"(?:the|a|my|our|this)\s+(?:fire|burner|stove|barbecue|bbq|grill)\b[^.?!]{0,30}\bflames?\b",
    # Flames on a screen are a picture of a fire, and so are the flames in a photo, a film or a
    # dream: "i saw flames in my dream" was the get-everyone-out card.
    r"\bflames?\s+(?:on|in)\s+(?:the\s+)?(?:tv|telly|television|screen|monitor)\b",
    r"\b(?:on|in|from)\s+(?:the\s+|a\s+|my\s+|our\s+)?(?:tv|telly|television|screen|monitor|"
    r"photo|picture|film|movie|video|game|painting|drawing|dream|dreams|nightmare)\b"
    r"[^.?!]{0,20}\bflames?\b",
    r"\bflames?\b[^.?!]{0,20}\b(?:on\s+)?(?:the\s+|a\s+|my\s+|our\s+)?(?:tv|telly|television|"
    r"screen|monitor|photo|picture|film|movie|video|game|painting|drawing|dream|dreams|nightmare)\b",
    # The idiom with nothing burning: the plans, the diet, the project and the career go up in
    # flames when they fail. A house, a shed, a car or a kitchen going up in flames is the fire.
    r"\b(?:plans?|hopes?|dreams?|dreamt|diets?|careers?|projects?|budgets?|savings|marriage|"
    r"relationship|business|chances?|grades?|reputation|weekend|strateg\w*|team|faith|trust|"
    r"confidence|nerves|nervousness|arguments?|negotiations?|deal|interview|holiday|wedding|"
    r"prospects?|retirement|pension|investments?|shares?|portfolio|"
    # A dinner goes up in flames in a pan and the answer is the burnt food, not the building:
    # "my toast went up in flames" was the leave-the-building card. The food is the subject and
    # the line has to be about that subject only, so "the kitchen went up in flames" keeps the
    # card, and so does a food line with smoke or spreading fire in it (FIRE_ELSEWHERE).
    r"toast|toastie|toasties|dinner|teas|supper|lunch|breakfast|roast|chicken|sausages?|bacon|"
    r"bread|rice|pasta|pizza|pie|pies|curry|stew|casserole|lasagne|lasagna|soup|sauce|chips|"
    r"potatoes|pancakes?|porridge|biscuits?|muffins?|crumpets?|cakes?|meat|fish|veg|vegetables|garlic|"
    r"onions?|beans|food|pudding|turkey|stuffing|yorkshire\s+puddings?)\b[^.?!]{0,25}"
    r"\b(?:went|gone|go|goes|going|is|was|are|were|been|up)\s+(?:up\s+)?in\s+flames\b",
)
# Whose clothes they are, when they are somebody else's: "my daughter's sleeve went up",
# "my little girl's dress caught fire", "my sons pyjamas went up", "his coat caught fire". Every
# arm below read the garment from the bare "my" outwards, so a parent describing a child alight
# was answered by the laundry module - "Air it before you wash it" (brisk-torch, #10769).
# The owner is one or two words ending in an s, with or without the apostrophe, which is how
# people type it.
SOMEONES = (r"(?:(?:my|his|her|their|our|your|the)\s+(?:[\w-]+\s+){0,1}[\w-]+'?s\s+)?")
CLOTHES_FIRE = (
    SOMEONES + GARMENT + r"[^.?!]{0,20}"
    r"\b(?:is\s+|was\s+|'s\s+|are\s+|were\s+|got\s+|has\s+gone\s+|had\s+gone\s+)?"
    r"(?:on\s+fire|alight|ablaze)\b",
    SOMEONES + GARMENT + r"[^.?!]{0,20}\bcaught\s+(?:on\s+)?fire\b",
    r"\b(?:i|he|she|they)\s+(?:am|is|are|was|were)\s+(?:on\s+fire|alight|ablaze)\b",
    r"\bset\s+(?:my|his|her|their)\s+(?:coat|shirt|top|sleeve|trousers|clothes)\s+alight\b",
    # The flame named instead of the fire. In a kitchen the thing that catches a sleeve is "the
    # flame" - "my sleeve caught the flame", "the flame caught my sleeve" - and every arm above
    # wanted the words "on fire", "alight" or "caught fire", so the commonest way it is said read
    # as nothing at all and the bot answered cheerily. "caught light" is the same event in British
    # English, and "went up in flames" is a garment as often as a building: `my apron went up in
    # flames` was the *leave the building* card, which tells a person who is alight to walk out.
    # The garment and the flame have to be in the same clause either way round, so "the candle
    # flame" or "free the flame of the gas ring" names no clothes and stays ordinary.
    SOMEONES + GARMENT + r"(?=[^.?!]{0,20}\b(?:caught|catches|took|takes|touched|touches|"
    r"grabbed|grabs|lapped|laps|licked|licks|caught\s+light)\s+(?:the\s+|a\s+)?flames?\b)",
    SOMEONES + GARMENT + r"(?=[^.?!]{0,25}\bwent\s+up\s+in\s+flames\b)",
    # "my daughter's sleeve went up", "my sons pyjamas went up": a garment that has gone up in a
    # kitchen is alight. A price and a size go up too, and neither is burning.
    SOMEONES + GARMENT + r"(?=[^.?!]{0,12}\b(?:went|goes|had\s+gone|has\s+gone|gone)\s+up\b"
    r"(?!\s+(?:in\s+)?(?:price|prices|by|to|from|again|a\s+size|two\s+sizes|\d|"
    r"a\b|an\b|the\b|some\b|one\b|two\b)))",
    SOMEONES + GARMENT + r"(?=[^.?!]{0,25}\b(?:is|was|were|are|'s)\s+(?:in|among)\s+the\s+flames\b)",
    r"\b(?:the\s+|a\s+)?flames?\b[^.?!]{0,20}\b(?:caught|catches|took|takes|touched|"
    r"touches|grabbed|lapped|licked|reached)\b(?=[^.?!]{0,8}" + GARMENT + r")",
    SOMEONES + GARMENT + r"(?=[^.?!]{0,20}\bcaught\s+light\b)",
    # A person catching fire, in the tense people use: "he caught fire off the gas ring" is the
    # same event as "he is on fire", and only the present tense was read.
    r"\b(?:i|he|she|they|we)\s+caught\s+(?:on\s+)?fire\b",
    r"\b(?:my|his|her|their)\s+(?:son|daughter|husband|wife|partner|dad|mum|father|mother|"
    r"brother|sister|friend|baby|child|kid|boy|girl)\s+(?:has\s+|had\s+)?caught\s+"
    r"(?:on\s+)?fire\b",
)
# ...and the ten seconds are over once the fire is out of the pan: the hood, the ceiling, the
# smoke or the alarm means the kitchen is the question and the building card is the answer.
PAN_FIRE_SPREAD = (
    r"\b(?:hood|extractor|ceiling|wall|walls|curtains?|cupboards?|shelf|shelves|worktop|"
    r"kitchen|everywhere|spreading|spread|out\s+of\s+control)\b",
    r"\bsmok\w*\b",
    r"\b(?:alarm|trapped|can'?t\s+get\s+out|cannot\s+get\s+out)\b",
)

# An engine that uses or burns oil is the engine question, and "the engine is burning" is how
# drivers say it. Only a fire word on the line overrides this.
VEHICLE_STILL_FIRE = (
    r"\b(?:on\s+fire|caught\s+fire|alight|ablaze|in\s+flames|flames|smok\w*)\b",
)
# ...unless the fire is named as well.
VEHICLE_EXHAUST_HARD = (
    r"\b(?:on\s+fire|caught\s+fire|alight|ablaze|in\s+flames|flames?|bonnet|engine\s+bay|"
    r"dashboard|inside\s+the\s+car|coming\s+into\s+the\s+car)\b",
)
# A person's hand on a hot exhaust is a burn, not a vehicle fire: "the bonnet is burning my hand"
# and "the exhaust is burning my leg" were handed the 999 car-fire card while "the engine is
# burning my fingers" kept the burn card. When the thing that burns has a body part as its
# object, the verb belongs to the burn case, and a fire word in the line puts it back.
VEHICLE_BURNING_A_PERSON = (
    r"\bburn\w*\b[^.?!]{0,20}\b(?:my|his|her|their|your|our)\s+(?:hand|hands|arm|arms|"
    r"leg|legs|finger|fingers|thumb|thumbs|wrist|wrists|foot|feet|toe|toes|face|cheek|"
    r"shoulder|knee|eye|eyes|skin|back|neck|thigh)\b",
)
VEHICLE_BURNING_A_PERSON_HARD = (
    r"\b(?:on\s+fire|caught\s+fire|alight|ablaze|in\s+flames|flames?|smok\w*|"
    r"everyone\s+out|get\s+out)\b",
)
VEHICLE_FIRE_OVER_HARD = (
    r"\b(?:on\s+fire|alight|ablaze|in\s+flames|flames?|still\s+(?:burning|smoking|smoking)|"
    r"still\s+smok\w*|burning\s+now|right\s+now|everyone\s+out)\b",
)
VEHICLE_NOT_FIRE = (
    r"\b(?:burning|burns|burnt|using|uses|used|losing|loses)\s+(?:a\s+bit\s+of\s+|some\s+|"
    r"too\s+much\s+)?(?:oil|fuel|petrol|diesel|coolant|calories|money)\b",
    r"\b(?:oil|fuel)\s+(?:burning|consumption|use)\b",
)


# The smell is on something a person can wash or air. Without a thing, "i can smell smoke" is a
# warning sign and the card stays.
SMELL_ON_A_THING = re.compile(r"\b(?:" + _SMELLY_THING + r")\b", re.I)

# A lithium battery on fire is its own kind of fire: it is small, it is in the room, and water
# and a cloth make it worse, so it gets its own answer. "Burning up" is a hot phone, not a fire.
# A place that is full of smoke, whatever is in it. Used to keep the building card off a phone
# that is alight on the desk in a kitchen that is not.
ROOM_OR_HOUSE = (
    r"\b(?:house|flat|apartment|kitchen|room|living\s+room|bedroom|hall|hallway|landing|"
    r"building|stairwell|stairs|ceiling|floor\s?boards?)\b",
)

# Tablets in a quantity are poisoning whoever took them, even when the line is about the user.
# "my whole packet of paracetamol" is the same amount as "a whole packet of": the possessive in
# front of "whole" is the way most people say it, and it rang nothing.
WHOLE_OF = (r"(?:my|his|her|their|your|mums?|mum'?s|dads?|dad'?s)\s+whole\s+(?:packet|pack|box|"
            r"bottle|strip|blister|tub)\s+of")
CHILD_TAKER = (
    r"(?:(?:my|our|his|her|their)\s+(?:son|daughter|child|kid|baby|toddler|boy|girl|grandson|"
    r"granddaughter|grandchild|niece|nephew|little\s+one)|\d+\s*(?:year|yr)s?[\s-]?old|"
    r"the\s+(?:baby|toddler|child|kid))\b"
)
# The child the dose went to, written after it rather than before: "for my baby", "to my son".
CHILD_DOSE_AFTER = (
    r"\b(?:for|to)\s+(?:my|our|his|her|their|the|a|an)\s+(?:son|daughter|child|kid|baby|toddler|"
    r"boy|girl|little\s+one|grandson|granddaughter|grandchild|niece|nephew|newborn|\d+\s*"
    r"(?:year|yr)s?[\s-]?old)\b"
)
DOSE_ALREADY_GIVEN = (
    r"\b(?:gave|given|dosed|took|taken|swallowed|fed)\b",
)

CHILD_MEDICINE = (
    # "my child swallowed the whole bottle of calpol", "my son finished the bottle of nurofen"
    CHILD_TAKER + r"[^.?!]{0,25}\b(?:swallowed|swallowing|drank|drunk|drinking|ate|eaten|took|"
    r"taken|had|finished|downed|necked|gulped|sucked|sipped|given|gave)\b[^.?!]{0,25}"
    r"\b(?:the|a|his|her|my|another)\s+(?:whole\s+)?(?:bottle|packet|pack|box|strip|blister|tub)\b"
    r"[^.?!]{0,20}\b" + MEDICINE + r"\b",
    # "my baby had too many doses of calpol", "my toddler had a double dose"
    CHILD_TAKER + r"[^.?!]{0,25}\b(?:had|given|gave|took|taken|swallowed|drank)\b[^.?!]{0,25}"
    r"\b(?:too\s+many|extra|double|another|two|three|four|several)\s+(?:doses?|spoonfuls?|"
    r"mouthfuls?|syringes?)\b[^.?!]{0,20}\b" + MEDICINE + r"\b",
    # "i gave my son too much calpol": the parent poured it, so the child is the object and not the
    # one doing the verb.
    r"\b(?:gave|give|giving|dosed|fed|measured)\s+(?:my|our|his|her|their)\s+(?:son|daughter|"
    r"child|kid|baby|toddler|boy|girl|little\s+one)\b[^.?!]{0,25}"
    r"\b(?:too\s+much|too\s+many|double|extra|twice|another\s+dose|two\s+doses)\b"
    r"[^.?!]{0,20}\b" + MEDICINE + r"\b",
    # "my son drank too much calpol": no dose word, just the amount people actually say for a
    # liquid, which is uncountable - so "too much" needs its own arm here.
    CHILD_TAKER + r"[^.?!]{0,25}\b(?:swallowed|swallowing|drank|drunk|drinking|took|taken|had|"
    r"downed|gulped|sucked|sipped)\b[^.?!]{0,20}\btoo\s+much\b[^.?!]{0,20}\b" + MEDICINE + r"\b",
    # "the baby got into the calpol": no swallowing named, and the reach is the whole story.
    CHILD_TAKER + r"[^.?!]{0,40}\b(?:got|get|gets|getting)\s+into\s+(?:the|my|his|her|their|a)\s+"
    r"(?:bottle\s+of\s+|packet\s+of\s+|box\s+of\s+)?" + MEDICINE + r"\b",
    # "my son has taken my sleeping tablets": the possessive is what says whose medicine it is, so a
    # child and a grown-up's tablets is the poisons line with no bottle and no count said. "my son
    # took his calpol" is the child's own medicine, so "his" and "her" are deliberately not here.
    CHILD_TAKER + r"[^.?!]{0,25}\b(?:took|taken|swallowed|ate|eaten|had|nicked|downed|found)\b"
    r"[^.?!]{0,20}\b(?:my|your|mums?|mum'?s|dads?|dad'?s|nans?|nana'?s|grans?|gran'?s|"
    r"nanny'?s|grandad'?s|grandma'?s|the|these|those)\s+(?:\w+\s+)?(?:pills|tablets|"
    r"sleeping\s+(?:pills|tablets)|antidepressants|painkillers|medicines?|meds|vitamins?|"
    r"paracetamol|ibuprofen|tranquill?i[sz]ers?)\b",
    # "too many doses of calpol for my baby", "too much calpol for my baby": the amount first and
    # the child after it, which is the order a parent writes in as often as the other, and nothing
    # above reaches it.
    r"\b(?:too\s+many|too\s+much)[^.?!]{0,25}?\b" + MEDICINE +
    r"\b[^.?!]{0,20}?" + CHILD_DOSE_AFTER,
    # "i gave her twice the dose of calpol", "i gave him too much calpol": the child is a pronoun,
    # so no child word is in the line and every child-first arm above is blind to her. The dose
    # words are what say the medicine has gone in, so they are what the arm reads - with the
    # medicine named, because "too much" on its own is dinner and homework.
    r"\b(?:gave|give|giving|given|dosed|dosing|fed|measuring|measured|squirted)\s+"
    r"(?:her|him|them)\b[^.?!]{0,25}\b(?:(?:" + DOSE_AMOUNT +
    r")|\b(?:too\s+many|too\s+much)\b|an?\s+(?:extra|double)\s+dose)[^.?!]{0,20}\b" +
    MEDICINE + r"\b",
    # ...and the same with no brand named, where the amount is itself a dose: "i gave her two
    # doses of calpol in an hour". "a double dose" is not here, because with nothing named it is
    # as often the pasta as the calpol.
    r"\b(?:gave|give|giving|given|dosed|dosing|fed|measuring|measured|squirted)\s+"
    r"(?:her|him|them)\b[^.?!]{0,25}\b(?:\b(?:too\s+many|too\s+much)\s+(?:doses?|"
    r"spoonfuls?|mouthfuls?|syringes?)\b|\b(?:two|three|four|several)\s+(?:doses?|spoonfuls?)\b"
    r"[^.?!]{0,15}\b(?:at\s+once|together|at\s+the\s+same\s+time|in\s+(?:an|one|1)\s+hour|"
    r"within\s+an\s+hour|in\s+\d+\s+minutes|back\s+to\s+back)\b)",
    # "too many doses for a baby", with no medicine named at all: a dose is a medicine, and the
    # parent saying how many went in does not put the brand in the sentence. It has to be the dose
    # word, so "too much for a baby" about anything at all is not this.
    r"\b(?:too\s+many|too\s+much)\s+(?:doses?|spoonfuls?|mouthfuls?|syringes?)\b"
    r"[^.?!]{0,15}?" + CHILD_DOSE_AFTER,
)

PILLS_OVERDOSE = (
    r"\b(?:took|taken|swallowed|had|downed|ate|eaten|popped|necked)\b[^.?!]{0,25}"
    # "too much" as well as "too many": the amount people say for paracetamol, ibuprofen or
    # medicine is uncountable - "i think i took too much paracetamol" - and only "too many" was
    # read, so the hedged version of the same sentence fell through to an acknowledgement.
    r"\b(?:too\s+(?:many|much)|a\s+lot\s+of|loads\s+of|lots\s+of|a\s+(?:whole|bunch|load|handful|pile|packet|"
    r"box|strip|blister)\s+of|a\s+whole\s+(?:packet|pack|box|bottle|strip|blister)\s+of|"
    r"the\s+whole\s+(?:packet|pack|box|strip|blister)|" + WHOLE_OF + r"|"
    r"all\s+(?:of\s+)?(?:my|his|her|their|mums?|mum's|dads?|dad's|the|these|those)|"
    r"[6-9]\s+(?:of\s+)?|[1-9]\d{1,}\s+(?:of\s+)?|"
    r"(?:six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|forty|fifty))"
    r"\b[^.?!]{0,20}"
    r"\b(?:pills|tablets|paracetamol|ibuprofen|painkillers|meds|medicines?|sleeping\s+pills|"
    r"antidepressants)\b",
    r"\boverdos(?:e|ed|ing)\b",
)
# Six tablets a day is a prescription, not an overdose: a count only says "overdose" when the line
# is not describing how they are taken.
DOSE_REGULAR = (
    r"\b(?:a|per|each)\s+(?:day|week|dose)\b",
    r"\b(?:daily|every\s+day|once\s+a|twice\s+a|three\s+times\s+a)\b",
    r"\bat\s+a\s+time\b",
    r"\b(?:as|when)\s+(?:needed|required)\b",
    r"\bprescri(?:bed|ption)\b",
)
# A packet that is still sealed, out of date or in the bin is not an overdose.
PACK_FINE = (
    r"\b(?:out\s+of\s+date|expired|in\s+the\s+bin|threw|thrown|unopened|sealed|still\s+full|"
    r"left\s+(?:in|on)|in\s+the\s+cupboard|to\s+buy|bought|pharmacy|prescription\s+ready)\b",
)
# The things that make it a treat rather than a packet: a pill or a poison named in the line beats
# the treat words, so "i overdosed on my heart tablets after coffee" keeps the card.
OVERDOSE_REAL_THING = (
    r"\bpills?\b", r"\btablets?\b", r"\bparacetamol\b", r"\bibuprofen\b", r"\binsulin\b",
    r"\bmeds\b", r"\bmedicines?\b", r"\bbleach\b", r"\bantifreeze\b", r"\bheroin\b",
    r"\bopioids?\b", r"\btramadol\b", r"\bantidepressants?\b", r"\bchemotherapy\b",
)


def _overdose_of_a_treat(line):
    """"i overdosed on coffee" is too much of a good thing, not a packet to keep."""
    return (_matches(OVERDOSE_OF_A_TREAT, line) or _matches(OVERDOSE_WORK, line)) \
        and not _matches(OVERDOSE_REAL_THING, line)


# ...and the work words only with "an overdose of": "i overdosed on work" is rare next to the box
# set, and "overdosed on insulin" or "on my pills" must keep the card.
OVERDOSE_WORK = (
    r"\boverdosed?\s+on\s+(?:work|meetings?|emails?|paperwork|spreadsheets?)\b",
)
# How much of it was taken, said the way people say it. "i swallowed a bit of bleach" and "i drank
# a little bleach" were answered "I'm listening - say more if it helps": the amount in front of the
# substance was a short fixed list ("a bottle of", "a mouthful of"), so every other way of saying
# a little - a bit, a drop, a splash, a little - hid the bleach behind it. One list now, and the
# substance after it is what makes the line.
POISON_SWALLOW_VERB = (
    r"\b(?:swallowed|swallowing|drank|drunk|drinking|eaten|eating|gulped|sucked|licked|tasted)\b",
)
# The words that say it was a little of it. Without one there is no amount at all, and "my son
# drank shampoo" stays the poisons line.
A_SMALL_AMOUNT = (
    r"\b(?:a\s+bit|a\s+little|a\s+small\s+amount|a\s+mouthful|a\s+sip|one\s+sip|"
    r"one\s+mouthful|a\s+taste|a\s+drop|a\s+dab|a\s+smear|a\s+swig|a\s+lick|some)\b",
)
MILD_PRODUCT_BIG = (
    r"\b(?:whole|full|tubes?|packets?|packs?|bottles?|litres?|pint|glass\s+full|handful|boxes?|"
    r"box|bar)\b",
)
# A child is the poisons line whatever the amount: a mouthful of shampoo to a toddler is the card,
# and the mild bathroom answer is written for the person who took it, so it cannot take the third
# person ("my son drank a mouthful of shampoo" was answered with how much water a toddler drinks -
# friendly-kangaroo, #8776).
# Soap and toothpaste are the two a child can have in any amount without a call, and the milder
# answer takes the third person for those; everything else in the cabinet is the card for a child.
MILD_HARMLESS = (
    r"\b(?:soap|toothpaste|sun\s?cream|moisturiser|moisturizer)\b",
)
MILD_TAKEN_BY_A_CHILD = (
    r"\b(?:my|our|her|his|their|the)\s+(?:son|daughter|child|kid|baby|toddler|boy|girl|niece|"
    r"nephew|grandson|granddaughter|stepson|stepdaughter)\b",
    r"\b(?:little\s+(?:boy|girl|one)|a\s+child|a\s+toddler|my\s+little\s+\w+)\b",
)
# The fluids that are the poisons line whatever the amount: petrol and the rest of the shed are
# the line to 999 and to "don't make them sick", and "i swallowed petrol" was answered "Good to
# hear. What was the best bit?".
FUEL_AND_SOLVENT = (
    r"petrol|petroleum|diesel|paraffin|kero?scene|lighter\s+fluid|turpentine|white\s+spirit|"
    r"paint\s?thinner|thinners?|meths|methylated\s+spirits?|lamp\s+oil|engine\s+oil|"
    r"screen\s?wash|de-?icer|antifreeze|coolant"
)
# A count of packs is a dose, the way "a whole packet" is. The medicine arm below counts tablets
# (six or more) and it counts one pack ("a packet of", "a whole box of"); a number of packs was the
# one amount nobody counted, and two packets of paracetamol is thirty-two tablets. "i took two
# packets of pills" was answered "Got it. Is there anything you'd like a hand with?" (close-pipe,
# #safety 139534), and the same hole ran the other way up: "i took the rest of my tablets" was a
# greeting too. The pack word and the drug word both have to be in the line, so "i took two boxes
# down from the shelf", "i took the bottles to the recycling" and "i bought two packets of pills"
# stay the shopping and the errand.
PACK_COUNT = (r"(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|\d{1,3}|"
              r"a\s+couple|a\s+few|a\s+handful|couple|few|several|both|all)")
PACK_WORD = (r"(?:packs?|packets?|boxes?|box|strips?|blisters?|blister\s+packs?|bottles?|tubes?|"
             r"tubs?|sachets?)")
PACK_DRUG = (r"(?:pills|tablets|capsules|caplets|paracetamol|acetaminophen|ibuprofen|nurofen|"
             r"brufen|panadol|calpol|co[\s-]?codamol|codamol|painkillers|analgesics|meds|"
             r"medicines?|sleeping\s+(?:pills|tablets)|antidepressants|tranquill?i[sz]ers?|insulin)\b")
TOOK_MANY_PACKS = (
    # "i took two packets of pills", "i swallowed three strips of tablets"
    r"\b(?:took|taken|swallowed|downed|necked|popped|had|ate|eaten|emptied|finished)\b"
    r"[^.?!]{0,20}\b" + PACK_COUNT
    + r"\s+(?:more\s+)?(?:of\s+)?(?:the\s+|my\s+|these\s+|those\s+)?(?:other\s+)?"
    + PACK_WORD
    + r"\b(?:\s+of)?[^.?!]{0,25}\b" + PACK_DRUG,
    # The pack counted after the drug: "i took 20 pills, two packets".
    r"\b(?:took|taken|swallowed|downed|necked|popped|had|emptied|finished)\b"
    r"[^.?!]{0,25}\b" + PACK_DRUG + r"[^.?!]{0,12}\b" + PACK_COUNT + r"\s+" + PACK_WORD +
    r"\b",
    # "i took the rest of my tablets", "i took what was left of the packet of paracetamol".
    # Not "finished": "i finished the rest of my sleeping tablets" is as often the packet being
    # empty as the tablets being swallowed, and that line has an answer of its own.
    r"\b(?:took|taken|swallowed|downed|necked|popped|had|emptied|eaten|ate)\s+(?:the\s+rest\s+of|"
    r"the\s+last\s+of|the\s+remainder\s+of|whats\s+left\s+of|what'?s\s+left\s+of|"
    r"what\s+was\s+left\s+of|what\s+is\s+left\s+of|"
    r"whatever\s+was\s+left\s+of|all\s+that\s+was\s+left\s+of)\s+(?:the\s+|my\s+|a\s+|his\s+|"
    r"her\s+|their\s+)?(?:" + PACK_WORD + r"\s+of\s+)?" + PACK_DRUG,
    # "i swallowed a whole strip": a strip is the medicine packed, and not a strip of anything
    # else, so the drug does not have to be named a second time.
    r"\b(?:took|taken|swallowed|downed|necked|popped|had|emptied|finished)\s+(?:the\s+|a\s+)?"
    r"(?:whole|full|entire)\s+(?:strip|blister\s+pack|blister|sheet\s+of\s+tablets)\b"
    r"(?!\s+of\s+(?:paper|wallpaper|cloth|fabric|tape|vinyl|wood|card|cardboard|metal|lead|land))",
)

POISON = (
    *CHILD_MEDICINE,
    r"\b(?:swallowed|drank|eaten|ate|took|downed|inhaled|gulped|licked)\s+" + SOME_OF_IT +
    r"(?:bleach|detergent|disinfectant|antifreeze|weed\s?killer|hand\s+saniti[sz]er|"
    r"drain\s+cleaner|soap|shampoo|mouthwash|shower\s+gel)\b",
    # The same mouthful said in the perfect tense, and an overdose said as a doubled dose. `drunk`
    # was missing from the verbs above, so "i have drunk some bleach" was answered "Noted: you
    # have drunk some bleach." while "i drank some bleach" got the 999 line.
    *POISON_SAID,
    # Mushrooms are the one substance the word "the" has to be kept away from: "i ate the mushrooms"
    # is dinner, and a foraged or a wild one is `FORAGED_EATEN` below.
    r"\b(?:swallowed|drank|eaten|ate|took|downed|gulped)\s+"
    r"(?:some\s+|a\s+few\s+|any\s+|a\s+)?mushrooms?\b",
    # The shed and the garage: petrol, diesel, paraffin, lighter fluid, turpentine, meths. These do
    # not need a word for how much, because a mouthful of any of them is the poisons line.
    r"\b(?:swallowed|drank|eaten|ate|took|downed|inhaled|gulped|licked)\s+" +
    SOME_OF_IT + r"(?:" + FUEL_AND_SOLVENT + r")\b",
    # A medicine is the poisons line when the amount is said, because the amount is the whole
    # question: "i took 20 paracetamol", "i took a whole packet of paracetamol", "my son swallowed
    # a bottle of paracetamol". The drug name on its own is not one: "i took paracetamol" a while
    # into a headache, and "i took some paracetamol", were both answered with this line.
    r"\b(?:swallowed|swallowing|drank|drunk|eaten|ate|took|taken|downed|inhaled|popped|necked)\b"
    r"[^.?!]{0,30}(?:too\s+(?:many|much)|a\s+lot\s+of|loads\s+of|lots\s+of|a\s+(?:whole|bunch|load|handful|"
    r"pile)\s+of|a\s+whole\s+(?:packet|pack|box|bottle|strip|blister|tub)\s+of|"
    r"the\s+whole\s+(?:packet|pack|box|bottle|strip|blister)\s+of|" + WHOLE_OF + r"|"
    r"a\s+(?:packet|pack|box|bottle|strip|blister)\s+of|[6-9]\s+(?:of\s+)?|[1-9]\d{1,}\s+(?:of\s+)?|"
    r"(?:six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|forty|fifty|a\s+hundred)\s+)"
    r"[^.?!]{0,20}\b(?:pills|tablets|paracetamol|ibuprofen|painkillers|analgesics|meds|medicines?|"
    r"sleeping\s+pills|antidepressants|tranquill?i[sz]ers?|insulin)\b",
    # "i had 10 paracetamol" says the dose without the word overdose, and "had" was the one verb
    # people use that the arm above did not carry: main answered it "Got it - you had 10
    # paracetamol". A packet that is left, in the cupboard or still to be taken is the shopping
    # line, so the amount has to be the dose and not the stock.
    r"\b(?:had|have\s+had|'?ve\s+had|got\s+down|knocked\s+back|managed)\s+"
    r"(?:[6-9]|[1-9]\d{1,}|(?:six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|"
    r"forty|fifty|a\s+hundred))\s+(?:of\s+)?(?:pills|tablets|paracetamol|ibuprofen|painkillers|"
    r"analgesics|meds|medicines?|sleeping\s+pills|antidepressants|tranquill?i[sz]ers?|insulin)\b"
    r"(?!\s+(?:left|in\s+the|in\s+my|at\s+home|with\s+me|to\s+take|in\s+stock|spare|over))",
    # The amount said on its own, with no verb: "my whole packet of paracetamol". Nobody describes
    # a packet that size unless they have taken it, but a packet that is still sealed is not.
    r"\b" + WHOLE_OF + r"\s*\b(?:pills|tablets|paracetamol|ibuprofen|painkillers|analgesics|meds|"
    r"medicines?|sleeping\s+pills|antidepressants|tranquill?i[sz]ers?|insulin)\b",
    *TOOK_MANY_PACKS,
    r"\b(?:chemical|fumes?)\s+(?:leak|leaking|leaked)\b",
    r"\bpoison(?:ed|ing)?\b.{0,20}\b(?:child|kid|son|daughter|baby|toddler|myself|me|dog|cat|puppy)\b",
    # The object after the verb is never the topic: a dishwasher tablet, a washing pod and a
    # bottle of bleach are all the poison line, and the next one nobody has thought of joins them.
    r"\b(?:swallowed|drank|eaten|ate|took|downed|inhaled|gulped|choked\s+on)\s+"
    r"(?:(?:some|a|an|the|his|her|their|my|one|two|three)\s+)?" + SOME_OF_IT +
    r"(?:dishwasher\s+(?:tablet|cube|pod|powder)s?|washing\s+(?:capsule|tablet|pod|liquid|"
    r"powder)s?|laundry\s+(?:capsule|tablet|pod)s?|soap\s+powder|fabric\s+softener|"
    r"bleach\s+tablet|drain\s+unblocker|oven\s+cleaner|limescale\s+remover|"
    r"antifreeze|screen\s?wash|de-?icer|weed\s?killer|slug\s+pellets?)\b"
    # "i took the washing powder out of the cupboard" is fetching, not swallowing: taking a
    # product out of, from or off something is the sentence about where it lives.
    r"(?!\s+(?:out\s+of|from|off|down\s+from|out\s+the)\b)",
    # A cigarette eaten by a small child is nicotine poisoning - one butt can be enough for a
    # toddler - and the smoking answers own the word "cigarette", so "my child ate a cigarette"
    # came back as a shrug and the line with the amount in it never reached the poison card. The
    # nicotine list joins the other things a child does not eat; the child has to be named, so
    # somebody asking how to give up is still the smoking answer's.
    r"\b(?:child|kid|son|daughter|baby|toddler|boy|girl|little\s+one|he|she|grandson|"
    r"granddaughter)\b[^.?!]{0,20}\b(?:swallowed|drank|ate|eaten|eating|chewed|sucked|"
    r"licked|bitten|bit)\s+(?:(?:my|his|her|their|the|some|a|an|half\s+a)\s+)?"
    r"(?:cigarettes?|cigarette\s+(?:butt|end|stub)s?|fag\s?ends?|fags?|nicotine\s+"
    r"(?:pouch|pouches|gum|lozenge|lozenges|spray|inhaler|shot|shots)s?|snus|chewing\s+tobacco|"
    r"vape\s+(?:liquid|juice)|e-?liquid|nic\s?shot|nicotine)\b",
    r"\b(?:child|kid|son|daughter|baby|toddler|he|she)\b.{0,20}\b(?:swallowed|drank|ate)\s+(?:(?:my|his|her|their|the|some|a)\s+)?(?:bleach|detergent|pills|tablets|medicine|meds|antifreeze|disinfectant|paracetamol|ibuprofen|painkillers|antidepressants|insulin)\b",
    r"\b(?:overdose|overdosed)\b",
    # A small hard thing in a child is a poisons-line question whichever verb is used: "ate a coin"
    # and "swallowed a coin" are the same afternoon.
    r"\b(?:swallowed|swallowing|ate|eaten|eating|chewed|chewing)\s+(?:a|an|some)\s+(?:coin|coins|"
    r"battery|batteries|magnet|magnets|marble|marbles|button|toy|piece\s+of\s+(?:glass|plastic|metal)|"
    r"drawing\s+pin|pen\s+lid|(?:blu|blue)\s?tack?|play\s?dough)\b",
    # A named household product that went into somebody's mouth is a poisons-line call, whatever
    # the brand calls it: "my daughter licked the toilet cleaner", "my child ate rat poison",
    # "i drank nail varnish remover". The names are the long ones on purpose - "battery", "pods"
    # and "softener" on their own are everyday sentences ("i took the batteries out of the
    # remote", "i took the coffee pods out of the machine"), so they stay out of this list.
    # ...and it is a person's mouth: `my dog licked the toilet cleaner` is the vet's answer, which
    # pet_harm gives once the product is in PET_CRISIS, so the pet words keep the hot card away.
    r"(?![^?]{0,40}\b(?:dog|dogs|cat|cats|puppy|puppies|kitten|kittens|pup|pups|pet|pets|"
    r"parrot|budgie|hamster|rabbit|bunny|horse|pony|guinea\s+pig|tortoise|ferret|gerbil)\b)"
    r"\b(?:swallowed|swallowing|drank|drunk|eaten|ate|eating|licked|sucked|chewed)\b[^.?!]{0,25}"
    r"\b(?:toilet\s+cleaner|oven\s+cleaner|washing\s+powder|nail\s+varnish|"
    r"nail\s+varnish\s+remover|rat\s+poison|rodent\s+poison|slug\s+pellets?|de-?icer|"
    r"screen\s?wash|fabric\s+softener|dishwasher\s+salt|drain\s+cleaner)\b",
    # A whole tube of toothpaste is a fluoride dose worth the hot card, in a way a smear of it is
    # not: "my daughter ate a whole tube of toothpaste" stays here, the rest of the crayon-and-chalk
    # lines go to the milder `swallowed_ordinary` answer below.
    r"\b(?:swallowed|swallowing|drank|drunk|eaten|ate|eating)\b[^.?!]{0,25}"
    r"\b(?:whole|full|half\s+a|tube\s+of|tubes?\s+of|packet\s+of|pack\s+of)\b[^.?!]{0,15}"
    r"\btoothpaste\b",
    # A washing or dishwasher tablet is not a medical one, and a screen tablet is not swallowed:
    # the household word in front of it settles what was eaten. Without this, "my daughter ate a
    # washing tablet" was read as a question about screen time, because `tablet` is one of that
    # entry's key words.
    r"\b(?:swallowed|drank|drunk|eaten|ate|chewed|sucked|licked)\b[^.?!]{0,25}"
    r"\b(?:washing\s?up|dishwasher|laundry|soap|shower\s+gel|fabric\s+softener)\s+(?:tablet|tablets|capsule|capsules|pod|pods|liquid|gel|powder|sachet|sachets)\b",
    # Nobody eats a computer. "ate" and "chewed" are the verbs that say it was not a medicine;
    # "took a tablet" stays ordinary, because that is how people describe their own pills. Someone
    # else has to be the one doing it: "i swallowed my tablet with water" is a normal breakfast.
    r"\b(?:child|kid|kids|son|daughter|baby|toddler|newborn|grandson|granddaughter|niece|nephew|"
    r"boy|girl|he|she|they|dog|cat|puppy|kitten|pup)\b[^.?!]{0,25}"
    r"\b(?:ate|eaten|eat|chewed|sucked|swallowed)\b[^.?!]{0,15}"
    r"\b(?:tablet|tablets|capsule|capsules|pod|pods)\b",
    # A quantity is what makes tablets an overdose: "i've taken a lot of pills", "my son took all
    # my pills". "i took my pills this morning" has no quantity and stays ordinary.
    r"\b(?:took|taken|swallowed|had|downed|ate|eaten|popped|necked)\b[^.?!]{0,25}"
    r"\b(?:too\s+(?:many|much)|a\s+lot\s+of|loads\s+of|lots\s+of|a\s+(?:whole|bunch|load|handful|pile|packet|"
    r"box|strip|blister)\s+of|the\s+whole\s+(?:packet|pack|bottle|box|strip|blister)|"
    + WHOLE_OF + r"|"
    r"all\s+(?:of\s+)?(?:my|his|her|their|mums?|mum's|dads?|dad's|the|these|those))\b[^.?!]{0,20}"
    r"\b(?:pills|tablets|paracetamol|ibuprofen|painkillers|meds|medicines?|sleeping\s+pills|"
    r"antidepressants)\b",
    # A tablet nobody counted, said with doubt in it: "i think my son took some tablets" was
    # answered with the screen-time limit for a `tablet`, and "i think my little boy has taken some
    # paracetamol" with "I'm listening", because `took` is left out of the arm above (it is how an
    # adult describes their own pills, "i took my tablets this morning") and "some" is not an
    # amount that arm counts. The doubt is the thing that makes this a poisoning question: a parent
    # who watched the dose go in says "i gave him some", and one who has just found the strip open
    # says "i think". So the hedge is required, and the child's own prescription is left out with
    # its possessive - "i think my son took his tablets this morning" is a double-dose question for
    # a pharmacist, not this card.
    r"\b(?:i\s+(?:think|reckon|believe|suspect)|(?:i'?m|i\s+am)\s+not\s+sure|"
    r"not\s+sure\s+(?:if|whether)|might\s+have|may\s+have|did\s+(?:he|she|they)|"
    r"has\s+(?:he|she|they)|have\s+(?:they|we))\b[^.?!]{0,45}"
    r"\b(?:took|taken|taking|had|has\s+had|got\s+into|helped\s+(?:him|her|them)sel(?:f|ves)\s+to)\b"
    r"[^.?!]{0,25}(?<!his )(?<!her )(?<!their )"
    r"\b(?:(?:some|a\s+few|a\s+couple\s+of|any|another|more)\s+(?:of\s+(?:my|the)\s+)?|"
    r"(?:my|mums?|mum'?s|dads?|dad'?s|nans?|nan'?s)\s+)?" + MEDICINE + r"\b",
    # A red flag in the same line as an ordinary mouthful is still an emergency. The mild answer
    # below ends "999 if they get drowsy, limp, or struggle to breathe", so the matcher has to agree:
    # "my son ate a crayon and now hes drowsy" was getting the calm water-and-watch card.
    r"\b(?:crayons?|chalk(?!\s*paint)|toothpaste|soap|play\s?dough|(?:blu|blue)\s?tack?)\b[^.?!]{0,60}"
    r"\b(?:drowsy|sleepy|limp|floppy|cough\w*|chok\w*|struggling\s+to\s+breathe|"
    r"can'?t\s+breathe|vomit\w*|being\s+sick|throwing\s+up|fitting|seizure|blue|"
    r"unresponsive|passing\s+out|hard\s+to\s+wake)\b",
    r"\b(?:drowsy|sleepy|limp|floppy|cough\w*|chok\w*|struggling\s+to\s+breathe|"
    r"can'?t\s+breathe|vomit\w*|fitting|seizure)\b[^.?!]{0,60}"
    r"\b(?:crayons?|chalk(?!\s*paint)|toothpaste|soap|play\s?dough|(?:blu|blue)\s?tack?)\b",
    # Chalk paint is paint: the ordinary crayon arm used to take "my son ate a bowl of chalk paint"
    # off the poison card. The decorating lines have no swallowed verb in front, so they stay
    # ordinary ("how do i clean chalk paint off a wall", "which chalk paint is best for furniture").
    r"\b(?:swallowed|swallowing|drank|drunk|eaten|ate|eating|licked|chewed)\b[^.?!]{0,25}"
    r"\b(?:chalk|emulsion|gloss|matt|satin)\s+paint\b",
    # The name on the bottle is the bottle. "Fairy liquid" is what washing-up liquid is called in
    # most of the UK, and the same liquid said by its everyday name reached a shrug while "i drank
    # some washing up liquid" reached this card: the list of substances was the chemical name only,
    # so the words people actually use for the thing in the cupboard under the sink were missing.
    # The verbs people use for a mouthful are shapes too - a sip of white spirit was answered
    # "Nice one. How did the rest of it go?" - so they are read beside the verb in the past tense.
    r"(?![^?]{0,40}\b(?:dog|dogs|cat|cats|puppy|puppies|kitten|kittens|pup|pups|pet|pets|"
    r"parrot|budgie|hamster|rabbit|bunny|horse|pony|guinea\s+pig|tortoise|ferret|gerbil)\b)"
    r"\b(?:swallowed|swallowing|drank|drunk|drinking|gulped|gulping|sucked|sucking|licked|"
    r"licking|sipped|sipping|swigged|swigging|necked|glugged|glugging)\b[^.?!]{0,25}"
    r"\b(?:fairy\s+liquid|washing[\s-]?up\s+liquid|dish\s+soap|bubble\s+bath|"
    r"laundry\s+liquid|fabric\s+conditioner|dishwasher\s+(?:liquid|gel|powder|salt)|"
    r"bleach|detergent|disinfectant|drain\s+cleaner|weed\s?killer|hand\s+saniti[sz]er|"
    + FUEL_AND_SOLVENT + r")\b"
    # "i took the washing powder out of the cupboard" is fetching, not swallowing.
    r"(?!\s+(?:out\s+of|from|off|down\s+from|out\s+the)\b)",
)


# Anything left that names the gas or the alarm - "carbon monoxide", "how often should I replace a
# carbon monoxide alarm", "should I buy a detector" - is someone worried about it, so it gets the
# device-and-danger answer rather than a stock "Got it". This is the last case for a reason.
CO_MENTION = (
    r"\bcarbon\s+monoxide\b",
    r"\bco\s+(?:alarm|detector|monitor)\b",
)


# A thing swallowed is not a poison: a sim card, a coin and a bee are the same line, and what
# matters is whether it can block an airway or burn, not what it was for. Kept separate from the
# poison line so the reply does not send someone to poison control about a memory card.
# The verb, said every way people say it. Main had only the past tense, so the same emergency in
# the present was left to whatever its nouns happened to match: "what do i do if my child swallows
# a battery" got the sore-throat gargle, "my son keeps swallowing glass" got a children's sight
# test, and "if a toddler swallows a magnet" got nothing at all. A thing going down is not a tense.
SWALLOW_TAKING = (
    r"(?:swallow\w*|gulp\w*|got\s+stuck\s+in\s+(?:his|her|their|my)\s+throat)"
)
# A battery that was bitten through leaks, so it is the same call as one swallowed: "my toddler bit
# a button battery" was answered with the teething-and-biting card, and "my child bit through a
# battery" with a row about being hit. Only the battery and the magnet are here: a chewed bead is
# not.
SWALLOW_BITTEN = (
    r"\b(?:bit|bites?|biting|chewed|chewing|sucked|sucking|pierced|pierces)\b[^.?!]{0,20}"
    r"\b(?:button\s+battery|battery|batteries|magnet|magnets)\b"
)
SWALLOWED_THING = (
    # A thing that was choked on keeps the choking reply: it is the one with "stay on the line".
    r"\b" + SWALLOW_TAKING + r"\s+"
    r"(?:(?:some|a|an|the|his|her|their|my|one|two|three)\s+)?"
    r"(?:(?:bit|piece)\s+of\s+)?"
    r"(?:sim\s?card|memory\s+card|sd\s+card|credit\s+card|button\s+battery|watch\s+battery|"
    r"fish\s+bone|chicken\s+bone|"
    r"battery|coin|magnet|marble|bead|pin|screw|nail|blade|razor\s+blade|glass|toy\s+part|"
    r"lego|bee|wasp|insect|stone|plastic\s+bag|balloon)\b",
    r"\b(?:child|kid|son|daughter|baby|toddler|he|she)\b.{0,20}\b(?:ate|eaten|eats|eating)\s+"
    r"(?:a\s+|the\s+|his\s+|her\s+)?(?:sim\s?card|memory\s+card|sd\s+card|button\s+battery|"
    r"watch\s+battery|coin|magnet|marble|bead|pin|screw|nail|blade|glass|toy\s+part|lego|"
    r"bee|wasp|insect|stone|balloon)\b",
    SWALLOW_BITTEN,
)


# and two questions that are about the kit and the gas rather than about right now: a person
# asking how to test the alarm, or whether carbon monoxide rises, wants the fact, not 999.
CO_PLACE = (
    r"\bwhere\s+(?:should|do|can)\s+(?:i|we|you)\s+(?:put|place|fit|mount|install|site)\b.{0,30}"
    r"\b(?:carbon\s+monoxide|co)\s+(?:alarm|detector|monitor)\b",
    r"\b(?:carbon\s+monoxide|co)\s+(?:alarm|detector|monitor)\b.{0,30}\bwhere\b.{0,20}\b(?:put|go|place|fit)\b",
)
CO_FACT = (
    r"\bcarbon\s+monoxide\b.{0,40}\b(?:heavier|lighter|than\s+air|rise|rises|sink|sinks)\b",
    r"\b(?:heavier|lighter)\s+than\s+air\b.{0,40}\bcarbon\s+monoxide\b",
    r"\bwhat\s+(?:is|does)\s+carbon\s+monoxide\b",
)

# "breath" without its e is the spelling people reach for when they are the ones short of it, and
# the typo reader cannot help here: a real word is left alone, so "write" does not become "white".
# An emergency pattern therefore spells out the forms it accepts instead of trusting one.
BREATH = r"breath(?:e|es|ing)?"


BREATHING = (
    # "i can't breath through my nose with this cold" is a blocked nose, not an airway closing
    r"\b(?:can't|cannot|can\s+not|struggling\s+to|hard\s+to|unable\s+to)\s+" + BREATH + r"\b"
    r"(?!\s+through\b)",
    # "can't catch my breath", "can't get my breath", "fighting for breath"
    r"\b(?:can't|cannot|can\s+not)\s+(?:catch|get|find)\s+(?:my|his|her|their|a)\s+"
    r"breath\b",
    r"\b(?:not|stopped|stop|isn't|is\s+not|hasn't|has\s+not)\s+" + BREATH + r"\b",
    # The same emergency said as a thing rather than an action: "having trouble breathing",
    # "difficulty breathing", "shortness of breath". Main answered all three with small talk.
    r"\b(?:trouble|difficulty|difficult(?:y)?|problems?)\s+(?:to\s+)?breath(?:e|ing)\b",
    # "shortness of breath" on its own is a subject, not a person, and main already treats the
    # bare phrase as ordinary: the emergency is someone who has it, or has it at a bad moment.
    # The verb matters as much as the subject. "my husband is short of breath" and "i have been
    # short of breath all day" are the same emergency as "i have shortness of breath", and a
    # copula was the one word that kept them out: main answered both with a greeting.
    r"\b(?:i|we|he|she|they|my\s+\w+|i'?m|im|i'?ve|ive|he'?s|hes|she'?s|shes|they'?re|theyre|"
    r"they'?ve|theyve|we'?re|we'?ve)\s+(?:have|has|had|having|got|get|getting|been\s+having|"
    r"have\s+been|has\s+been|been|am|is|are|keeps?|kept|feels?|looks?)\s+"
    r"(?:some\s+|a\s+bit\s+of\s+)?short(?:ness)?\s+of\s+breath\b",
    # "im short of breath" has no word boundary before the contraction, so the list above walked
    # past the commonest spelling of all: main answered `im short of breath` with "Noted!" and
    # `hes short of breath` with "Thanks for telling me".
    r"\b(?:im|i'?m|hes|he'?s|shes|she'?s|they'?re|theyre|we'?re)\s+"
    r"(?:a\s+bit\s+(?:of\s+)?|a\s+little\s+)?short(?:ness)?\s+of\s+breath\b",
    # "i am still short of breath" and "im still out of breath" put one word between the copula and
    # the phrase, so the list above cannot see the present tense at all.
    r"\b(?:still|now)\s+(?:a\s+bit\s+|a\s+little\s+)?(?:out\s+of|short(?:ness)?\s+of)\s+breath\b",
    # The bare phrase with a "now" on it is the person reporting it, not a subject: main answered
    # "shortness of breath right now" with "Got it. Is there anything you'd like a hand with?".
    r"\b(?:short(?:ness)?\s+of\s+breath|breathless)\s+(?:right\s+)?now\b",
    r"\bshort(?:ness)?\s+of\s+breath\s+(?:when|whenever|while|at|on|lying|walking|that|since|and|"
    r"if|after|before|going|doing)\b",
    # The bare phrase with a duration on it: "short of breath for 2 weeks and my ankles are swollen".
    r"\bshort(?:ness)?\s+of\s+breath\s+for\s+(?:\d+|a|an|two|three|a\s+few|a\s+couple\s+of|"
    r"several|many|the\s+last)\s+(?:hour|hours|day|days|week|weeks|month|months|year|years)\b",
    # "out of breath" on its own is not this: `i was out of breath earlier`, `i get out of breath
    # singing`, `i ran for the bus` are people describing their own day, and main treats bare
    # breathlessness as ordinary. Out of breath while doing nothing is the shape that is not.
    # An attack said in its own name, and the shape that always escalates: the reliever is not
    # working. Main answered "i am having an asthma attack" with "Got it. Is there anything you'd
    # like a hand with?" and "my inhaler is not working" with "Annoying."
    r"\basthma\s+attack\b",
    # "my inhaler is not working" mid-attack is an ambulance; an inhaler that is out of date,
    # empty or due a repeat is a chemist today, so "out of" is gone and "empty" needs the breath
    # beside it (wide-pineapple, #safety 15328).
    r"\binhaler\b[^.!?]{0,25}\b(?:not\s+working|isn'?t\s+working|won'?t\s+work|"
    r"didn'?t\s+work|isn'?t\s+helping|not\s+helping)\b",
    r"\binhaler\b[^.!?]{0,25}\b(?:empty|running\s+out)\b(?=[^.!?]{0,40}\b(?:breath|breathing|"
    r"breathe|wheez\w*|attack|tight|shaky|shake)\b)",
    r"\bout\s+of\s+breath\s+(?:at\s+rest|in\s+bed|sitting\s+still|sitting\s+down|"
    r"doing\s+nothing|watching\s+tv|lying\s+down)\b",
    # British English "gasping for a brew" is a thirst and "gasping after that run" is the effort,
    # so gasping is the emergency only for air, when a person is named doing it, or with a body sign.
    r"\bgasping\s+for\s+(?:breath|air)\b",
    r"\bgasping\s+for\s+(?:his|her|their|my)\s+breath\b",
    r"\b(?:he|she|they|my\s+" + PERSON + r"|the\s+" + PERSON + r")\b[^.?!]{0,15}\bgasping\b",
    # A bare "im gasping" is the breath and nothing else - main's own test keeps it an emergency -
    # and GASP_FINE still takes "im gasping for a brew" and "im gasping after that run" away first.
    r"\b(?:i'?m|im|i\s+am)\s+gasping\b",
    r"\bgasping\b[^.!?]{0,25}\b(?:blue|lips?|pale|sweat\w*|collapsed|unconscious|"
    r"not\s+breathing|stopped|wheez\w*|struggling)\b",
    r"\bturning\s+blue\b",
    # "chocking" for "choking" is common enough to answer, and "chock full" is the only other use
    # - and neither is "im choked about the result", which is disappointed, so `about` is the one
    # word that takes the choke out of the airway. "choked about" is not how a choke is described:
    # a real one is "choked on a grape", "choked at dinner", or nothing after it at all.
    r"\bchok(?:ing|ed|es)\b(?!\s+(?:under\s+pressure|about\b))", r"\bchocking\b", r"\b(?:throat|tongue|airway)\s+(?:is\s+|'s\s+)?(?:closing|closing\s+up|swelling|swollen)\b",
    r"\banaphyla\w*\b", r"\b(?:severe|serious|bad|really\s+bad)\s+allergic\s+reaction\b", r"\bepipen\b",
    r"\b(?:he|she|they|my\s+(?:son|daughter|husband|wife|dad|mum|friend|partner|baby))\s+"
    r"(?:isn't|is\s+not|stopped|hasn't|has\s+not)\s+" + BREATH + r"\b",
    # A breathlessness the person puts a duration on is a symptom to have looked at, not an
    # ambulance: "i have been short of breath for a week", "ive had it for 3 days and im
    # breathless". It has to reach the case at all, which is why it is here and not only below.
    r"\b(?:for|since|going\s+on\s+for|these\s+last)\s+(?:about\s+|nearly\s+|almost\s+)?"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a|a\s+few|a\s+couple\s+of|"
    r"several|many|last)\s+(?:day|days|week|weeks|month|months|year|years|christmas|friday)\b"
    r"[^.!?]{0,40}?\b(?:breathless|short(?:ness)?\s+of\s+breath|out\s+of\s+breath)\b",
    # Bare "out of breath" is ordinary, so it needs its own duration to reach the case: "ive been
    # out of breath for weeks" is a symptom to have looked at, and the guard below gives it the
    # same-day line rather than a shrug or an ambulance.
    r"\bout\s+of\s+breath\b[^.!?]{0,30}\bfor\s+(?:days|weeks|months|years|a\s+week|"
    r"a\s+month|a\s+few\s+days|a\s+few\s+weeks|a\s+couple\s+of\s+weeks|the\s+last\s+\w+)\b",
    # Hours are not weeks: "short of breath for an hour" is new, so it keeps the careful line and
    # not the appointment one. "when i talk for a long time" is a habit and must not reach either.
    r"\b(?:short(?:ness)?\s+of\s+breath|out\s+of\s+breath|breathless)\b[^.!?]{0,20}\bfor\s+"
    r"(?:an?\s+hour|hours|an?\s+hour\s+or\s+two|half\s+an\s+hour)\b",
)

# "couldn't breathe" is said about a lot of things: a bill, a laugh, a sprint. It is a safety line
# only when the breathing really failed, so the words that made it fail have to be in the line too.
BREATH_PAST_CUE = (
    r"\bcough\w*", r"\bchok\w*", r"\bswallow\w*", r"\bblue\b", r"\bwheez\w*", r"\bgasp\w*",
    r"\bthroat\b", r"\basthma\b", r"\bswell\w*", r"\bcroup\b", r"\bpneumonia\b",
    r"\bfits?\b", r"\bstopped\b", r"\bhospital\b", r"\bambulance\b", r"\binhaler\b",
)
BREATH_PAST = (
    r"\b(?:couldn'?t|could\s+not|wasn'?t\s+able\s+to|was\s+unable\s+to|struggled\s+to)\s+"
    r"(?:" + BREATH + r"|(?:catch|get|find)\s+(?:my|his|her|their|a|any)\s+breath)\b"
    # "couldn't breathe through my nose with this cold" is a blocked nose, not this case.
    r"(?!\s+through\b)",
)

# A jaw or a left arm on its own is a dentist or a strain, not a heart attack: main answered
# "my jaw hurts when i chew" with "Ring 999 or 911 straight away: chest pain ..." said to
# someone who never mentioned a chest (gentle-chair, #safety 18903). The limb word counts only
# with a chest word in the line, or with a symptom that travels with a heart attack.
CHEST_LIMB = r"(?:left\s+arm|jaw)s?"
CHEST_LIMB_SIGN = r"(?:numb(?:ness|ed|ing|s)?|tingl\w*|pains?|painful|ache\w*|hurts?|sore)"
CHEST_COMPANY = (
    r"(?:chest|heart|sweat\w*|clammy|breathless|short\s+of\s+breath|faint\w*|grey|gray|"
    r"nause\w*|vomit\w*|crush\w*|spread\w*|radiat\w*|down\s+(?:my\s+|the\s+)?left\s+arm)"
)
CHEST_LIMB_PAIR = r"(?:left\s+arm|arm|jaw|shoulder)s?"
# The chest word, or a word that means the pain is already travelling, keeps the chest wording.
CHEST_MENTIONED = (
    r"\bchest\b", r"\bheart\b", r"\bcrush\w*", r"\bspread\w*", r"\bradiat\w*",
    r"\bdown\s+(?:my\s+|the\s+)?left\s+arm\b",
)
# Two of the four FAST signs in one line, or one of them said on its own: "my face is numb and my
# arm is weak" was answered "Ugh, that's a lot to carry", "my face and arm are numb" got "That
# sounds rough" and "my left arm is weak" got "Nice one. How did the rest of it go?" on main.
# FAST is Face, Arms, Speech, Time, and the arms half was the one nobody had.
# The sign has to belong to the face. A line can carry a face word, a limb word and a weakness word
# and still be two complaints - "my face is dry and my hands are numb in the cold" is Raynaud's and
# "my mouth is dry and my arm is weak" is a dry mouth - so the face and its sign are read as one
# phrase, and the limb only has to be somewhere else in the line (merry-wheel, #9679).
_FACE_WORD = (r"\b(?:face|faces|mouth|smile|cheek|eyelid|lip|tongue|"
              r"side\s+of\s+(?:my|his|her|their)\s+face)\b")
_FAST_SIGN = (r"\b(?:numb\w*|weak\w*|dead|heavy|droop\w*|dropped|floppy|useless|slack|twisted|"
              r"not\s+working|won'?t\s+(?:lift|move|raise|work|close)|"
              r"can'?t\s+(?:lift|raise|move|feel|hold|close))\b")
# FAST is Face, Arms, Speech, Time, so the limb half is an arm or a hand. A numb face beside
# weak legs is the cauda equina card, and it keeps it: `my face is numb and my legs are weak`
# was the stroke card with `legs?` in this list (merry-wheel, #9679).
_LIMB_WORD = r"\b(?:arms?|hands?|side|one\s+side|fingers?|fingertips?)\b"
# The face said as odd rather than numb: "my face feels funny and my arm is heavy". This one needs
# the limb's sign as well, so a face that feels funny beside cold hands is still the cold.
_FACE_ODD = (r"\b(?:droop\w*|dropped|twisted|slack|funny|odd|weird|strange|not\s+right|"
             r"numb\w*|tingl\w*|pins\s+and\s+needles)\b")
# The face that is odd rather than numb. A numb cheek beside a numb hand is the filling or the
# position slept in and a named cause explains it; a face that has "gone funny" or "drooped" is not
# explained by any cause, so the cause door reads this one, not _FACE_ODD.
_FACE_GOING_ODD = (r"\b(?:droop\w*|dropped|twisted|slack|funny|odd|weird|strange|not\s+right)\b")
STROKE_FAST = (
    # The pair, with a sign on each half: "my face is numb and my arm is weak". A face that is numb
    # beside cold hands is Raynaud's and a dry mouth beside a weak arm is a dry mouth, so the limb
    # has to be affected too. Every lookahead starts at the same place, so either half can come
    # first.
    r"(?=[^.?!]*" + _LIMB_WORD + r"[^.;!?]{0,18}" + _FAST_SIGN + r")"
    r"(?=[^.?!]*" + _FACE_WORD + r"[^.;!?]{0,18}" + _FAST_SIGN + r")",
    # The sign on the limb, with the face odd rather than numb: "my face feels funny and my arm is
    # heavy", "my face is drooping and my arm has gone heavy".
    r"(?=[^.?!]*" + _LIMB_WORD + r"[^.;!?]{0,18}" + _FAST_SIGN + r")"
    r"(?=[^.?!]*" + _FACE_WORD + r"[^.;!?]{0,18}" + _FACE_ODD + r")",
    # The two said as one list, sharing the sign: "my face and my arm are both numb".
    _FACE_WORD + r"\s*(?:,|and)\s+(?:my\s+|his\s+|her\s+|their\s+|the\s+)?"
    r"(?:arms?|hands?|side)\s+(?:are|is|both|have|has|went|gone|feel)?\s*"
    r"(?:both\s+)?" + _FAST_SIGN,
    # One side named: "my left arm is weak", "my right arm has gone numb". This is the sign on its
    # own, and it is the one where the hour matters most.
    r"\b(?:my|his|her|their|the)\s+(?:left|right)\s+arms?\b[^.!?]{0,25}"
    r"\b(?:weak\w*|numb\w*|dead|heavy|useless|floppy|not\s+working|won'?t\s+(?:lift|move|"
    r"raise|work))\b",
    # A limb that will not lift, when it is the person's own and the side is named.
    r"\b(?:can'?t|cannot|couldn'?t)\s+(?:lift|raise|move|hold\s+up|feel)\s+(?:my|his|her|their)\s+"
    r"(?:left|right)\s+(?:arm|hand|leg)\b",
)
# The arm that has been like that for months, the one slept on, and the one that is sore after the
# gym are all a nerve or a muscle: a stroke sign is new, so the old ones keep their ordinary
# answer. Nothing here can stand down a line that another STROKE pattern also read.
STROKE_FAST_OFF = (
    r"\b(?:for|in)\s+(?:the\s+)?(?:last\s+)?(?:months|years|weeks|ages)\b",
    r"\bsince\s+(?:my|his|her|their|the)?\s*(?:accident|injury|operation|op|fall|surgery|stroke|"
    r"birth|diagnosis)\b",
    r"\b(?:trapped\s+nerve|pins\s+and\s+needles|carpal|tennis\s+elbow|frozen\s+shoulder|"
    r"rsi|repetitive\s+strain)\b",
    r"\b(?:slept\s+(?:on|funny)|went\s+to\s+sleep\s+on|gym|work\s?out|weights?|"
    r"after\s+(?:the\s+)?(?:gym|run|exercise|swim))\b",
    r"\balways\b",
    # "since i was a kid", "all my life": a weakness somebody has always had is not this hour.
    r"\bsince\s+(?:i|he|she|they|we)\s+(?:was|were)\b",
    r"\b(?:all\s+my\s+life|since\s+(?:a\s+)?(?:kid|child|childhood|birth|teenager|teen))\b",
    # Reaching is a shoulder, not a stroke: "i cant lift my right arm over my head" is the frozen
    # shoulder question, and it is the one arm-weakness line people ask about most.
    r"\b(?:over|above|behind|past)\s+(?:my|his|her|their)\s+(?:head|back)\b",
    # The cold gives both halves a sign at once: "my face is tingly and my hands feel numb in the
    # cold" is Raynaud's, and the comment above the pair has always said so. The causes themselves
    # are one group below, because a cause explains a numbness and nothing benign explains a face
    # that has fallen on one side.
)

# The benign causes that name one half of the pair: the cold, a wrist from the keyboard, a shoulder
# that hurts when it is lifted, the ache after a jab, and the half-face a filling numbs. Each has a
# card of its own, and each was ringing the ambulance beside a numb half - "my left arm is weak from
# typing all day", "i cant lift my right arm and my shoulder hurts", "my left arm is weak from the
# vaccine", "my face is numb from the dentist and my arm is weak" (mint-brick and merry-wheel, #9679).
STROKE_FAST_CAUSE = (
    r"\b(?:in|out\s+in|from|with|out\s+of)\s+the\s+(?:cold|freezing|cold\s+weather|snow)\b",
    r"\b(?:cold\s+(?:hands?|fingers?|feet|toes|weather)|frostnip|frostbite)\b",
    r"\b(?:typing|typed|type|keyboard|keyboards|mouse|desk|laptop|computer|sewing|knitting|"
    r"cello|guitar|piano|drumming|gardening|painting|chopping)\b",
    r"\b(?:vaccin\w+|jabs?|injections?|booster|booster\s+jab|covid|flu\s+jab|anaesthetic|"
    r"anesthetic|novocaine)\b",
    r"\b(?:dentist|dental|filling|fillings|tooth|teeth|gums|root\s+canal|wisdom\s+tooth)\b",
)
# A shoulder that hurts and an arm that will not lift is the frozen-shoulder question, and it is how
# people ask it ("i cant lift my right arm and my shoulder hurts" was the stroke card on the pair).
# This one wins over the hard signs below, because the shoulder is what explains the lift.
STROKE_FAST_SHOULDER = (
    r"\bshoulders?\b[^.!?]{0,24}\b(?:hurts?|hurt|sore|aches?|aching|pain\w*|stiff\w*|"
    r"clicking|frozen)\b",
    r"\b(?:hurts?|hurt|sore|aches?|aching|pain\w*|stiff\w*|frozen)\b[^.!?]{0,18}\bshoulders?\b",
)
# What no benign cause can explain: a face that has fallen on one side, and a limb that has gone
# heavy or dead. A numb face after a filling is the filling; "i was at the dentist and now my face is
# drooping and my arm feels dead" is not, and it keeps the card.
STROKE_FAST_HARD = (
    r"\b(?:droop\w*|dropped|twisted|slack|floppy|dead|useless|heavy|hangs?\s+down|"
    r"won'?t\s+(?:lift|move|raise|work|close)|can'?t\s+(?:lift|raise|move|hold))\b",
)
# A numb cheek beside a numb hand, with no hard sign anywhere in the line, is the dentist or a hand
# slept on rather than the pair: `cheek`, `lip`, `tongue` and `mouth` are the parts half a filling
# numbs. A whole face beside an arm keeps the card - "my face and my arm are both numb" is one side
# of a body (merry-wheel, #9679).
STROKE_FAST_SENSORY = (
    r"\b(?:cheeks?|lips?|tongue|mouth|teeth|gums?)\b[^.?!]{0,40}"
    r"\b(?:hands?|fingers?|fingertips?|thumb)\b",
    r"\b(?:hands?|fingers?|fingertips?|thumb)\b[^.?!]{0,40}\b(?:cheeks?|lips?|tongue|mouth)\b",
)
# Weakness that comes and goes is the classic TIA description, not a reason to stand down: on main
# `my face droops sometimes and my arm is weak` was 999 and the stand-down above took it away, and
# `my left arm is weak and it comes and goes` was answered "Good to hear. What was the best bit?"
# (ivory-orange, #9679). These words stand down a sign only when the line carries ONE half of the
# pair - a face on its own, or an arm on its own - because a face that droops and an arm that is
# weak in the same line is the pair, whatever the person says about how often.
# Two ordinary reasons an arm will not lift, both of which the hard sign would otherwise outrank:
# the arm that was injected ("i cant lift my left arm since my flu jab") and the shoulder that stops
# at shoulder height ("i cant lift my left arm above my head"). Neither is a stroke, and neither
# word was in the file; teal-spruce's #13187 fences the same pair. A face word anywhere in the line
# puts the card back, so "my arm is weak since the jab and my face is drooping" still rings.
STROKE_FAST_JAB = (
    r"\b(?:flu|covid|tetanus|booster|vaccine|vaccination|jab|jabs|injection|injections|shot|shots)\b"
    r"[^.!?]{0,30}\b(?:arm|arms|shoulder|shoulders|deltoid)\b",
    r"\b(?:arm|arms|shoulder|shoulders|deltoid)\b[^.!?]{0,30}\b(?:flu|covid|tetanus|booster|"
    r"vaccine|vaccination|jab|jabs|injection|injections|shot|shots)\b",
)
STROKE_FAST_LIFT_CEILING = (
    r"\b(?:above|over)\s+(?:my|his|her|their|your)\s+head\b",
    r"\b(?:to|at)\s+shoulder\s+height\b",
)
STROKE_FAST_PATTERN = (
    r"\b(?:usually|sometimes|comes\s+and\s+goes|on\s+and\s+off)\b",
)
# The three shapes that are a face and a limb in one line.
STROKE_PAIR_BOTH = STROKE_FAST[:3]
# A weakness that comes and goes is the TIA and never stands down; a numbness that comes and goes is
# a trapped nerve and does.
STROKE_FAST_WEAK = (
    r"\b(?:weak\w*|heavy|dead|useless|floppy|not\s+working|won'?t\s+(?:lift|move|raise|work)|"
    r"can'?t\s+(?:lift|raise|move|hold))\b",
)
# A chest that aches *with the cough* is the muscle between the ribs, not the heart: "chest pain
# after coughing" and "my chest hurts when i cough" were both the 999 card on main, and what a
# person with an ordinary chest infection needs is the cough answer. The cough has to be the
# stated cause - said as when/after/from coughing or as a coughing fit - so a chest that is tight
# with a cough beside it (which can be an infection) keeps the ambulance, and so does a cough
# with any heart sign or blood in it (the guard below).
CHEST_STRAIN = (
    r"\b(?:when|whenever|every\s+time|each\s+time|after|from|since|while)\b[^.!?]{0,25}"
    r"\bcough\w*\b",
    r"\bcough\w*\b[^.!?]{0,20}\b(?:makes?|made|leaves?|left)\b[^.!?]{0,15}\bchest\b",
    # The same cause said the other way round, which is how most people type it: "i cough and my
    # chest hurts", "i cough then my chest is sore". The cough is the stated cause either side of
    # the verb, and the spread-and-red-flag fences below still stand the strain answer down.
    r"\bcough\w*\b[^.!?]{0,15}\b(?:and|but|then|so)\b[^.!?]{0,20}\bchest\b"
    r"[^.!?]{0,15}\b(?:hurt|sore|ache)\w*\b",
    r"\bcoughing\s+fit\b",
)
# Sneeze and laugh are the other two movements that strain the muscle between the ribs, and main
# rang the ambulance for both ("my chest hurts when i sneeze", "chest pain when i laugh"). They
# get their own list because the cough has a knowledge entry to hand the line to and these two do
# not: passing them on leaves a punt ("Sorry to hear that"), which is no answer to a chest.
CHEST_STRAIN_MOVE = (
    r"\b(?:when|whenever|every\s+time|each\s+time|after|from|since|while)\b[^.!?]{0,25}"
    r"\b(?:sneeze\w*|sneezed|laugh\w*)\b",
    r"\b(?:sneez\w*|laugh\w*)\b[^.!?]{0,20}"
    r"\b(?:makes?|made|leaves?|left)\b[^.!?]{0,15}\bchest\b[^.!?]{0,15}\b(?:hurt|sore|ache)\w*\b",
    # The movement said as the thing that cannot be done without the chest hurting: "i cant laugh
    # without my chest hurting" is the same strained muscle as "laughing makes my chest hurt", and
    # on main it was the 999 card (teal-spruce, #10407).
    r"\b(?:sneez\w*|laugh\w*|cough\w*)\b[^.!?]{0,25}\bchest\b[^.!?]{0,15}\b(?:hurt|sore|ache)\w*\b",
)
# ...and the row itself, because a row that never matches never reaches the arms: the chest row
# reads hurts/tight/aching but not "aches", so these lines were answered by the laugh cheer before
# safety was ever asked. The movement has to be in the line for this row to fire, so a bare "my
# chest aches" keeps the answer it had.
CHEST_SORE_MOVE = (
    r"\b(?:my|his|her|their|the|a)\s+chest\b[^.?!]{0,30}"
    r"\b(?:ache\w*|sore|hurts?|hurting|pain\w*)\b[^.?!]{0,45}"
    r"\b(?:sneeze\w*|sneezed|laugh\w*|cough\w*)\b",
    r"\b(?:sneeze\w*|sneezed|laugh\w*|cough\w*)\b[^.?!]{0,45}"
    r"\b(?:my|his|her|their|the)\s+chest\b[^.?!]{0,30}\b(?:ache\w*|sore|hurts?|hurting|pain\w*)\b",
)
# A cough or a sneeze is a muscular cause only while the pain stays where it is. Pain that spreads,
# radiates, or turns up in the back or between the shoulder blades is the shape that makes chest pain
# an emergency, and the world rings the ambulance for every one of these:
# "my chest hurts when i cough and it spreads to my back" must not become the coughy-cold answer.
CHEST_SPREAD = (
    r"\b(?:spread\w*|radiat\w*|moves?\b|moving\b|travel\w*|shoot\w*)\b",
    r"\b(?:goes|going|went|comes|coming|came)\s+(?:into|to|down|up|across)\b",
    r"\b(?:back|shoulders?|shoulder\s+blades?|between\s+the\s+shoulders|neck)\b",
)
# Two things a strain does not explain, so the muscle answer stands down for them (ivory-orange,
# #10407). Pain that arrives with the breath is the pleura, not the muscle between the ribs - "my
# cough is worse and now my chest hurts when i breathe" is the same-day call. A chest pain with a
# fever behind it is an infection, and the fever is in the line before the cough is.
CHEST_STRAIN_STOP = (
    r"\bwhen\s+(?:i|ya)\s+breathe?\b", r"\bhurts?\s+to\s+breathe\b",
    r"\bbreath(?:ing|e)\s+(?:in|deeply)\b", r"\btakes?\s+a\s+deep\s+breath\b",
    r"\bdeeper\s+breath\b",
    r"\bfever\w*\b", r"\bburning\s+up\b", r"\btemperature\b", r"\bchills?\b",
    r"\bshiver\w*\b", r"\bhot\s+and\s+cold\b",
    # ...and neither does the heart, a pain that is there when the person is still, or the history
    # that makes a chest pain a different question (grand-iris, #10407): a racing heart, a pain at
    # rest and a sixty-year-old smoker all rang 999 on main and the strain answer took them over.
    r"\b(?:heart|racing|pounding|palpitations?|fluttering|irregular|pulse)\b",
    r"\b(?:at\s+rest|sitting\s+still|sit\s+still|lying\s+still|not\s+moving|"
    r"when\s+i\s+am\s+still|when\s+i'm\s+still)\b",
    r"\b(?:smokers?|ex-?smoker|smoked|angina|heart\s+attack|stent|bypass|diabetes|diabetic|"
    r"high\s+blood\s+pressure|hypertension|cholesterol|blood\s+thinners?)\b",
    r"\b(?:5\d|6\d|7\d|8\d|9\d)\s*(?:years?\s+old|yrs?\s+old|yo)\b",
    r"\b(?:i\s+am|i'?m|im)\s+(?:5\d|6\d|7\d|8\d|9\d)\b",
    # breathlessness said plainly, and the history that makes a clot or a strained heart likely
    r"\b(?:out\s+of\s+breath|short\s+of\s+breath|breathless|puffed\s+out|"
    r"can'?t\s+(?:get\s+my\s+)?breath)\b",
    # Not every breathlessness is one of those phrases, and a list of the ways to say it is a list
    # that will always be short (close-falcon, #10407): "i cant catch my breath", "it is hard to
    # breathe", "i have trouble breathing" and "i keep gasping" were all muscle, and the card's own
    # words are "ring 999 if you are breathless with it", so the verb does the work now. The same
    # goes for the colour of a face and for going under: "my lips are blue", "i keep passing out".
    r"\b(?:catch|get|find)\w*\s+(?:my\s+|your\s+)?breath\b",
    r"\b(?:barely|hardly|scarcely)\s+(?:able\s+to\s+)?breath\w*",
    r"\bfigh(?:t|ting)\s+for\s+(?:my\s+|his\s+|her\s+)?breath\b",
    r"\bbreath\w*\s+properly\b",
    r"\b(?:hard|trouble|difficult\w*|struggl\w*)\s+(?:to\s+|with\s+)?breath\w*",
    r"\bbreath\w*\s+(?:hard|difficult)\b",
    r"\bgasp\w*\s+for\s+(?:air|breath|it)\b",
    r"\b(?:blue|grey|gray)\b",
    r"\b(?:pass(?:ed|es|ing)?\s+out|black(?:ed|ing)?\s+out|faint\w*|keel\w*\s+over)\b",
    r"\b(?:pregnan\w*|on\s+the\s+pill|contraceptives?|chemo\w*|cancer|clots?|dvt)\b",
    # A muscle does not wheeze (steward-urban-rake, #10407). A chest that aches with the cough and
    # then wheezes, rattles, is a known asthma with an inhaler that is not helping, brings up green
    # phlegm, or has been going a month is a chest that needs looking at today, not "the ache fades
    # over a week or two". The list is the shape "there is something else wrong with the chest"
    # rather than a list of diagnoses, which is why the noun and the verb both earn a place.
    r"\bwheez\w*", r"\basthma\w*", r"\binhalers?\b", r"\brattl\w*",
    r"\b(?:chest\s+infection|bronchitis|pneumonia|phlegm)\b",
    r"\bcoughing\s+up\s+(?:green|yellow|brown)\b",
    r"\b(?:lost|losing)\s+weight\b", r"\bfor\s+(?:a|one|\d+)\s+months?\b",
)
# The cough version says what to do for the cough as well, since that is the thing the person
# has to live with for a week, and it names the red flags for the same reason as the one below.
CHEST_COUGH_STRAIN_REPLY = (
    "A chest that aches when you cough is usually the muscle between the ribs, strained by the "
    "coughing itself, and it eases off as the cough settles. Honey in warm water, warm drinks and "
    "rest help the cough; see a GP if you are hot and shivery, coughing up green or blood, or no "
    "better after three weeks, and ring 999 if the pain spreads to your back, arm or jaw or you "
    "are breathless with it.",
    "The coughing is what strains the muscle between the ribs, and that ache fades over a week or "
    "two as the cough goes. Warm drinks, honey and an early night; a GP if you are feverish or no "
    "better in three weeks, and 999 if it spreads to your back, arm or jaw or you are short of "
    "breath with it.",
)
# The reply names the red flags, because the next line is often "and it spreads to my back" and a
# person who has just been told it is a muscle needs to know what would change that.
CHEST_STRAIN_REPLY = (
    "A chest that hurts only when you sneeze or laugh is usually a muscle between the ribs, and it "
    "settles by itself in a week or two. See a GP if it hurts when you sit still or is no better "
    "after three weeks, and ring 999 if it spreads to your back, arm or jaw.",
    "The muscle between the ribs is what a sneeze or a hard laugh pulls, and it eases off in a "
    "week or two. A GP if the pain turns up when you are resting or is still there after three "
    "weeks, and 999 if it spreads to your back, arm or jaw.",
)
# A left arm that has gone numb rings on its own, but it gets the stroke wording rather than a
# chest the person never mentioned. A tingle is out on purpose: pins and needles in an arm is a
# trapped nerve, and it was ringing the ambulance when it went in.
LEFT_ARM_NUMB = (
    r"\bleft\s+arms?\b[^.!?]{0,25}\b(?:numb(?:ness|ed|ing|s)?|gone\s+dead|dead)\b",
    r"\b(?:numb(?:ness|ed|ing|s)?|gone\s+dead)\b[^.!?]{0,20}\bleft\s+arms?\b",
)
# The adjective first and often no "my" in front of the chest: "i keep getting a tight chest when i
# walk up the stairs", "a heavy chest", "tightness in the chest". Every shape in CHEST wants
# "chest" and then the pain, so the commonest way people say it read as nothing at all - and a
# chest that comes on with the stairs is the one line that must not be.
# The chest that comes with a feeling names its cause in the same breath, and the ambulance card is
# the wrong answer to it: "my chest feels tight when im anxious", "i get chest tightness when i
# panic", "tight chest from anxiety", "my chest hurts when i have a panic attack" all rang 999 on
# main, which teaches a frightened person that the one card they get for a panic is the one that
# frightens them. Anxiety is the commonest cause of a tight chest in a healthy adult, so those lines
# want the anxiety answer with the 999 signs written after it, not instead of it. Every other red
# flag in _CHEST_OTHER_RED wins: an arm, a jaw, sweat, sickness, breathlessness, fainting.
CHEST_FEELING = (
    r"\b(?:when|whenever|with|from|because\s+of|after|during|amid|in)\b[^.?!]{0,30}"
    r"\b(?:anxi\w*|panic\w*|stress(?:ed|ful)?|nervous\w*|worry\w*|worried|overwhelm\w*|"
    r"sad\w*|upset|grief|grieving|exam|exams|test|presentation|interview|deadline)\b",
    # The feeling said first: "anxiety chest tightness", "panic attack and my chest hurts".
    r"\b(?:anxi\w*|panic\s+attack|anxiety\s+attack|stress|my\s+nerves)\b[^.?!]{0,30}\bchest\b",
    # The cause said as a belief, which is how a person who has had it before puts it: "my chest is
    # tight but i know its anxiety", "its probably just a panic attack". Nothing here overrides a
    # red flag - the arms below and _CHEST_OTHER_RED are read first.
    r"\b(?:know|knows|knew|think|thinks|thought|sure|probably|likely|reckon|guess)\b"
    r"[^.?!]{0,20}\b(?:anxi\w*|panic\w*)\b",
)
# A chest that is new, sudden, at rest or hours long is not explained by a feeling, whatever the
# line says beside it, and neither is a chest that is crushing or travelling (_CHEST_OTHER_RED).
CHEST_FEELING_RED = (
    # Travelling pain is the heart whatever the feeling beside it, so "chest pain that spreads to my
    # back when im anxious" keeps the ambulance.
    r"\b(?:spread\w*|radiat\w*|travel\w*|(?:in)?to\s+(?:my\s+|the\s+)?(?:back|shoulders?|neck|arms?|"
    r"jaw)\b)",
    r"\b(?:sudden\w*|out\s+of\s+(?:nowhere|the\s+blue)|never\s+had|first\s+time|"
    r"new\s+(?:pain|tightness|ache)|worse\s+than|wont\s+go\s+away|won'?t\s+go\s+away|"
    r"all\s+day|all\s+night|for\s+(?:hours|an\s+hour|days)|at\s+rest|"
    r"wok(?:e|en)\s+me|wakes\s+me|started\s+(?:today|yesterday|last\s+night)|"
    r"this\s+morning|this\s+week)\b",
)
CHEST_ADJ = (
    r"\b(?:a\s+|my\s+|his\s+|her\s+|their\s+)?(?:tight\w*|heavy|pressured?)\s+"
    r"(?:feeling\s+)?(?:in\s+)?(?:(?:my|his|her|their|the)\s+)?chest\b(?!\s+of\b)"
    r"(?!\s+(?:drawers?|freezer|freezers))",
)
# A hand on the chest says where the trouble is, not how far it has gone. The two shapes above
# are how people say "it is my heart" without a pain word, which is why they are worth having;
# but the words that set them off are also the words that say the person has gone down, and there
# a different card is the right one: the recovery position for someone who has collapsed, staying
# on the line for someone who cannot breathe, CPR once the breathing has stopped. "he grabbed his
# chest and collapsed" was answered "Keep him sitting and still until the ambulance arrives", and
# sitting someone up who is on the floor is the wrong thing to tell a frightened person to do
# (#4785 brought the gesture and this with it; wide-pineapple's gain is kept).
#
# Only the shapes that really do have a card of their own go on this list, so the chest row can
# step aside for them and nothing else: "my dad passed out" and "my husband is unresponsive" have
# no card anywhere, so a hand on the chest keeps the chest card rather than trading an ambulance
# for nothing. The collapse shape is written the way the card's own is (a person, then at most
# four words, then "collapsed"), so "my dad is clutching his chest and has collapsed" - which no
# card answers - keeps the chest card too. A fall of your own stays with the chest card: "i
# clutched my chest and fell" is still a hand on a chest that hurts.
CHEST_ANSWERED_ELSEWHERE = (
    r"\b" + PEOPLE + r"\b(?:\s+\w+){0,4}\s+collapsed\b"
    r"|\b(?:can'?t|cannot|couldn'?t|struggling\s+to|unable\s+to)\s+breathe\b"
    r"|\b(?:not|stopped|stop|isn'?t|is\s+not)\s+breathing\b"
    r"|\bcpr\b|\bgasping\b"
    r"|\b(?:he|she|they)\s+(?:is|'s)\s+out\s+cold\b"
    r"|\b(?:he|she|they|my\s+" + PERSON + r")\s+(?:is|'s|are)\s+not\s+responding\b"
)

CHEST = (
    r"\bcrushing\s+(?:chest|pains?)\b",
    # "chest pains" is how most people say it. "my chest pains me after gardening" is the
    # verb: the pain is the subject, not a symptom, so a chest word followed by me/you/him/
    # her/us/them is not this case.
    # "the chest freezer is tight on space" is the freezer, not the heart, so the words in
    # between may not be furniture.
    r"\b(?:chest|heart)\s+(?!of\b)(?!drawers?\b)(?!freezers?\b)"
    r"(?:\w+\s+){0,2}(?:pains?|tightness|tight|hurts?|hurting|aching)\b"
    r"(?!\s+(?:me|you|him|her|us|them)\b)",
    # The same thing said the other way round: "my chest is crushing", "my chest feels like it is
    # being squeezed", "a crushing feeling in my chest". Here the word is the pain, not a thing in
    # front of it - so "crushing chest pain" matched and "my chest is crushing" did not.
    r"\b(?:my\s+)?chest\s+(?:is|'s|feels|felt)\s+(?:like\s*(?:it'?s|it\s+is)\s+)?(?:being\s+)?"
    r"(?:crush\w*|squeez\w*|in\s+a\s+vice|heav\w*)\b",
    r"\bcrush\w*\s+(?:feeling|tightness|weight|pressure|pain)\s+(?:in|across|round)\s+(?:my|the)\s+chest\b",
    # "my chest is fine when i rest but hurts when i climb the stairs": the words in between
    # carry the meaning, so the chest must not have to sit next to the pain.
    r"\b(?:my|his|her|their|the)\s+chest\b(?!\s+of\s+drawers)(?!\s+drawers?\b)"
    r"(?!\s+freezers?\b).{0,25}"
    r"\b(?:hurts?|hurting|aching|ache|pain|painful|tight\w*|pressure)\b",
    r"\bpains?\s+in\s+my\s+chest\b", r"\b(?:pains?|pressure|tightness)\s+(?:in|across)\s+(?:my|the)\s+chest\b",
    r"\bchest\s+(?:pains?|hurts?|tight\w*)\b.{0,45}\b(?:arm|jaw|shoulder|sweat\w*|nausea|back)\b",
    # Same in either word order, and the company has to be somewhere in the line.
    r"\b" + CHEST_LIMB + r"\b[^.!?]{0,30}\b" + CHEST_LIMB_SIGN + r"\b[^.!?]{0,40}\b"
    + CHEST_COMPANY + r"\b",
    r"\b" + CHEST_COMPANY + r"\b[^.!?]{0,40}\b" + CHEST_LIMB + r"\b[^.!?]{0,30}\b"
    + CHEST_LIMB_SIGN + r"\b",
    # A jaw and an arm hurting together is the spreading shape whatever the other words are:
    # "my jaw hurts and my left arm is numb" has no chest in it and still needs the ambulance.
    r"\b" + CHEST_LIMB + r"\b[^.!?]{0,45}\b" + CHEST_LIMB_PAIR + r"\b[^.!?]{0,25}\b"
    + CHEST_LIMB_SIGN + r"\b",
    r"\b(?:going|spreading|radiating)\s+(?:down|into|to|up)\s+(?:my\s+)?(?:left\s+)?(?:arm|jaw|shoulder|neck)\b",
    r"\b(?:having|is\s+having|just\s+had|i'?m\s+having|he'?s\s+having|she'?s\s+having|having\s+another|think|suspect\w*)\b.{0,20}\bheart\s+attack\b",
    r"\bheart\s+attack\s+(?:right\s+)?now\b",
    *CHEST_IN_A_HAND,
)

SLUR_NOT_DENTAL = r"\A(?!.*\b(?:" + DENTAL_WORDS + r")\b)"
TIRED_WORDS = (r"tired|exhausted|knackered|sleepy|shattered|weary|worn\s+out|jet\s?lag|"
               r"no\s+sleep|not\s+slept|havent\s+slept|hasnt\s+slept|up\s+all\s+night|"
               r"long\s+day|early\s+start|night\s+shift|first\s+night\s+shift|"
               r"been\s+up\s+since")
SLUR_CAUSE_WORDS = DENTAL_WORDS + "|" + DRINK_WORDS + "|" + TIRED_WORDS
# The third reading of a slurred word that is not the speaker's own mouth: a gig review is a
# performance, and nobody rings 999 for one. The word has to be a performance one, so a family
# slurring in the front room with the telly on is still the card.
SLUR_NOT_A_PERFORMANCE = (r"\A(?!.*\b(?:singers?|lead\s+singer|frontman|presenter|comedian|"
                          r"band|choir|gig|gigs|concert|on\s+stage|on\s+tv|on\s+the\s+radio|"
                          r"interview)\b)")
SLUR_NOT_A_STROKE = r"\A(?!.*\b(?:" + SLUR_CAUSE_WORDS + r")\b)"
# The dentist's injection numbs the mouth and slurs the words for a few hours. That is not a
# stroke - the slurring patterns above stand it down for exactly this reason - but "Noted: your
# son is slurring his words after the dentist" is not an answer either, so the numbing gets its
# own line. Only the speech symptoms count: a numb lip or a numb arm after a filling is not this
# card. Weakness, a drooping face or confusion with it is a stroke whatever the dentist did, so
# those keep the ambulance below.
DENTAL = r"(?:" + DENTAL_WORDS + r")"
DENTAL_NUMB = (
    r"\b(?:slurr\w*|speech|words?)\b[^.!?]{0,60}\b" + DENTAL + r"\b",
    r"\b" + DENTAL + r"\b[^.!?]{0,60}\b(?:slurr\w*|speech|words?)\b",
)
DENTAL_NUMB_ASK = (
    r"\bhow\s+long\b", r"\bhow\s+many\s+hours\b", r"\bwears?\s+off\b",
    r"\bwhen\s+will\s+(?:it|the\s+numb(?:ness|ed|ing|s)?\s+feeling)\s+(?:go|wear|be\s+back|be\s+normal)\b",
    r"\bhow\s+long\s+does\s+it\s+(?:last|take)\b",
)
# The numbing has an end to it, and "how long does it last" is the question the card invites.
# Not in WAITING with the ambulance cases: that table is the scenes where help is on the way, and
# every emergency follow-up ("will he be ok for school tomorrow") is answered from it.
DENTAL_NUMB_FOLLOW = (
    "A few hours, usually two to four: the feeling comes back from the edge of the lip inwards, "
    "and soft food and nothing hot until it does. If it is still the same tomorrow, ring the "
    "dentist.",
)
# The two answers to that question, which the follow-up settles: a word that went thick today is
# the ambulance, one that has always been like that is the health visitor.
SLUR_SUDDEN = (r"\b(?:today|this morning|this afternoon|tonight|last night|yesterday|suddenly|"
               r"all of a sudden|came on|started|just now|an hour ago|this week)\b",
               r"\A(?:yes|yeah|yep|it did|it has|he did|she did)\b")
SLUR_NOT_SUDDEN = (r"\balways\b", r"\bsince\s+(?:he|she|they)\s+was\s+(?:born|a\s+baby|little|small)\b",
                   r"\bmonths\b", r"\bforever\b", r"\bgradually\b", r"\bslowly\b",
                   r"\bnever\s+(?:said|spoken|talked)\b", r"\bno\s+change\b", r"\bstill\s+the\s+same\b")
SLUR_SMALL_CHILD_URGENT = (
    r"\bfever\b", r"\btemperature\b", r"\brash\b", r"\bfits?\b", r"\bseizure\w*\b",
    r"\bfloppy\b", r"\bdrowsy\b", r"\bhard\s+to\s+wake\b", r"\bwont\s+wake\b",
    r"\bnot\s+himself\b", r"\bnot\s+herself\b", r"\bbreathing\b", r"\bblue\b",
)
SLUR_SMALL_CHILD_URGENT_REPLY = (
    "That needs seeing today rather than waiting: ring 111 or your GP now, and 999 or 911 if he "
    "is drowsy, floppy or hard to wake.",
)
SLUR_SMALL_CHILD_CALM = (
    "Then it is a health visitor or a GP who can watch it: ask for the words that are not coming "
    "out to be checked, and his hearing at the same time.",
)
# A slurring line that names the drink is the drink: it wears off, and "Noted: your dad is
# slurring his words he has had a few" is the coldest reply there is to it.
SLUR_DRINK = (
    r"\b(?:" + DRINK_WORDS + r")\b[^.!?]{0,40}\b(?:slurr\w*|slurred|speech|words?)\b",
    r"\b(?:slurr\w*|slurred|speech|words?)\b[^.!?]{0,40}\b(?:" + DRINK_WORDS + r")\b",
)
SLUR_SMALL_CHILD = (
    r"\b(?:" + SMALL_CHILD + r")\b[^.!?]{0,40}\b" + SLUR_THICK + r"\b",
    r"\b" + SLUR_THICK + r"\b[^.!?]{0,40}\b(?:" + SMALL_CHILD + r")\b",
)
DENTAL_NUMB_RED = (
    r"\bdroop\w*", r"\bweak\w*", r"\bone\s+side\b", r"\bconfus\w*",
    r"\bcan'?t\s+move\b", r"\bcan\s+not\s+move\b",
    r"\bnumb\s+(?:down\s+)?(?:my\s+)?(?:arm|leg|side|hand|foot)\b",
    r"\b(?:arm|leg|side|hand|foot)\s+(?:is\s+|feels\s+)?(?:numb|weak|dead)\b",
)
# The stroke sign said from the other side: the words will not come out. "my mum cant get her
# words out" is losing the words, the same sign as slurred speech, and it was answered with a
# gift idea, because "speak" was the only verb the patterns knew for it.
# Three shapes read the same and are nobody's stroke. A song does not stop at the mouth, so "of"
# and "to" after the words stand the sign down ("i cant get the words out of my head"), and a
# stutter is how someone has always talked ("i cant get my words out when i stutter"), so the
# word for it anywhere in the line stands it down.
NOT_A_STUTTER = (r"\A(?!.*\bstutter\w*\b)(?!.*\bstammer\w*\b)")
NOT_AN_OCCASION = (r"\A(?!.*(?:" + WORDS_OUT_OCCASION + r"))")
# "i keep dropping my cup and i feel confused" is a tired or anxious person about themselves: the
# confusion has to be someone else's, or another sign has to be in the line with it.
STROKE_HAND_SELF = (
    r"\bi\s+(?:feel|felt|am|get|getting|got|keep\s+getting|have\s+been\s+feeling)\s+"
    r"(?:a\s+bit\s+|really\s+|very\s+|so\s+|kind\s+of\s+)?(?:confus\w*|muddled|scatty|"
    r"forgetful)\b",
)
# What the self guard reads as another sign in the line: the hard ones only, so "i keep dropping my
# cup and my hands are weak" is still a tired person about themselves.
STROKE_HAND_OTHER = STROKE_HAND_HARD

STROKE = (
    NOT_A_STUTTER + NOT_AN_OCCASION
    + r".*?\b(?:can'?t|cannot|couldn'?t|couldnt|could\s+not|can\s+not)\s+"
    r"(?:get|get\s+out)\s+(?:my|his|her|their|our|your|the|any|a)\s+words?\s+out\b"
    r"(?!\s+(?:to\b|of\s+(?:my|his|her|their|our)\s+(?:head|mind)\b|of\s+the\s+way\b))",
    # The same thing in the other order, and only with the person's own words: "the words wont
    # come out" is a writer's block as often as it is a stroke.
    NOT_A_STUTTER + NOT_AN_OCCASION
    + r".*?\b(?:my|his|her|their|our)(?:\s+\w+){0,2}\s+words?\s+won'?t\s+"
    r"come\s+out\b",
    # The speech described rather than named. Nobody says "slurred": they say the speech has gone
    # funny, odd, weird, strange or wrong, and "his speech has gone funny" was answered "I'm
    # listening - say more if it helps" (super-pomelo, msg 82334). The subject has to be a person's
    # speech, words or talking, so "the sound has gone funny on the telly" is not this, and the
    # voice is left out because a voice that has gone funny is a cold.
    r"\b(?:his|her|my|their|our|your|dad'?s?|mum'?s?|mom'?s?|husband'?s?|wife'?s?|"
    r"partner'?s?|son'?s?|daughter'?s?)\s+(?:speech|words?)\s+"
    r"(?:(?:are|is|were|was|keeps?)\s+coming\s+out|has|have|had|is|are|was|were|'s|'ve|"
    r"sounds?|came\s+out|comes?\s+out|went|goes)\s+"
    r"(?:gone\s+|all\s+|a\s+bit\s+|a\s+little\s+|really\s+|very\s+|so\s+)?"
    r"(?:funny|odd|weird|strange|wrong|blurred|muddled|mushy|thick|slurred)\b",
    r"\b(?:face|mouth)\s+(?:is\s+|'s\s+)?(?:drooping|dropped|slurred)\b", r"\bdrooping\s+(?:face|mouth|on\s+one\s+side)\b",
    r"\bslurred\s+(?:speech|words)\b",
    # The doing, with the thing it slurrs: "my dad is slurring his words" and "he is slurring his
    # speech" were answered "Noted:", the worst reply there is to a stroke sign. The person has
    # to be named in front of the bare doing - "the singer was slurring the words" is a gig
    # review - and the drink or the dentist that explains a slur keeps it out of the ambulance.
    # A weakness, a drooping face or confusion beside the words is the ambulance whatever the
    # cause: a drink or a long day explains the mouth, not the arm. "my dad is slurring his words
    # and his arm feels weak, he is exhausted" was lost to the stand-down above. The red sign has
    # to be the stroke one (a limb, a side, a face), so "my voice is weak" and "dead tired" stay
    # ordinary, and the dental stand-down holds for a numb jaw after a filling.
    SLUR_NOT_DENTAL + r".*?\b(?:slurr\w*|slurred|speech|words?|talking)\b[^.!?]{0,40}\b(?:"
    + SLUR_RED_BESIDE + r")\b",
    SLUR_NOT_DENTAL + r".*?\b(?:" + SLUR_RED_BESIDE + r")\b[^.!?]{0,40}"
    r"\b(?:slurr\w*|slurred|speech|words?|talking)\b",
    # The same red sign further down the line. "my words wont come out when i talk to people and
    # my side is numb" puts 50 characters between the words and the side, so the window above
    # misses it and the occasion would stand the words-out sign down. A red sign anywhere in the
    # sentence beside lost words keeps the ambulance, whatever room the person was in.
    NOT_A_STUTTER + r".*?\b(?:words?|speech)\b[^.!?]{0,90}\b(?:" + SLUR_RED_BESIDE + r")\b",
    # A performance slurrs its words too, and a performer has a voice to lose: "the lead singer
    # was slurring his words" and "the presenter was slurring his words on tv" are reviews.
    # The stand-down needs a performance word, so a person slurring in front of the tv keeps the
    # card, and the weakness or the drooping face beside it is not stood down at all.
    SLUR_NOT_A_PERFORMANCE + SLUR_NOT_A_STROKE
    + r".*?\bslurring\s+(?:my|his|her|their|your|our)\s+(?:speech|words|voice|sounds)\b",
    SLUR_NOT_A_STROKE + r".*?\b(?:(?:my|his|her|their|our)(?:\s+\w+){1,2}|he|she|they|i)"
    r"\s+(?:is|am|was|were|are|keeps?|kept|started)\s+slurring\b",
    r"\b(?:talking|speaking)\s+(?:all\s+|a\s+bit\s+|really\s+)?(?:slurred|slurry)\b",
    # The way people actually say it: the thing belongs to them and the slurring comes after.
    # "my dads speech is slurred" and "his words are slurred" both got a shrug, which is the
    # worst thing to miss, so the possessive order counts as well as "slurred speech". A dentist,
    # a drink and being tired all slur the words and none of them is a stroke.
    r"\b(?:speech|words|voice|talking)\s+(?:is|are|was|were|'s|sounds?|seems?)\s+(?:a\s+bit\s+|all\s+)?"
    r"(?:slurred|slurry|slushy|thick)\b"
    r"(?!.{0,30}\b(?:" + SLUR_CAUSE_WORDS + r")\b)",
    # Losing speech, not a language or a person: "i cant speak french" and "i cant speak to my
    # mum" are ordinary lines and were getting the ambulance. The sign needs the end of the
    # sentence or the word about the difficulty after it.
    r"\b(?:can't|cannot)\s+speak\b(?=\s*(?:$|[,.!?;]|at\s+all\b|properly\b|clearly\b|"
    r"any\s?more\b|any\s+longer\b|well\b))",
    # Speech plus another sign in the same line is a stroke whatever the words after "speak":
    # "my dad cant speak and his arm feels weak".
    r"\b(?:can't|cannot)\s+speak\b(?=[^.!?]{0,60}\b(?:arm|leg|side|weak\w*|numb|"
    r"droop\w*|slurr\w*|confus\w*|face|mouth)\b)",
    r"\b(?:can't|cannot)\s+move\s+(?:my\s+)?(?:arm|leg|side|left|right)\b",
    r"\bnumb\s+(?:down\s+)?(?:on\s+)?(?:one\s+side|my\s+left|my\s+right|one\s+arm|half\s+of\s+my\s+face)\b",
    # A side that cannot be felt is a side that cannot be moved: "i cant feel my left side" and
    # "my grandad cant feel his left side" were answered with the kidney card, which is worse than
    # no answer at all. The side or the whole limb has to be named - "i cant feel my fingers" and
    # "my hand has gone numb" are a trapped nerve, and they keep the answer they have.
    r"\b(?:can'?t|cannot|couldn'?t|could\s+not|can\s+not)\s+feel\s+(?:my|his|her|their|our)\s+"
    r"(?:whole\s+|entire\s+)?(?:left|right)\s+(?:side|arm|body|face)\b",
    r"\b(?:can'?t|cannot)\s+feel\s+(?:anything\s+)?(?:at\s+all\s+)?(?:down\s+|on\s+)?"
    r"(?:one\s+side|half\s+of\s+my\s+body|half\s+of\s+my\s+face)\b",
    r"\bno\s+feeling\s+(?:at\s+all\s+)?(?:in|down|on)\s+(?:my|his|her|their|the)\s+"
    r"(?:left|right)\s+(?:side|arm|body|face)\b",
    r"\b(?:lost|gone)\s+(?:the\s+)?(?:feeling|sensation)\s+in\s+(?:my|his|her|their)\s+"
    r"(?:left|right)\s+(?:side|arm|body|face)\b",
    r"\bworst\s+headache\s+of\s+my\s+life\b", r"\bsudden(?:ly)?\s+(?:can't\s+see|lost\s+my\s+vision|numb)\b",
    # The line names it: "my dad is having a stroke", "I'm having another stroke". Naming the
    # condition is enough - a person who says this needs the ambulance, not a symptom list.
    r"\b(?:having|'s\s+having|is\s+having|think\w*|suspect\w*|probably|might\s+be)\b"
    r"(?:\s+\w+){0,3}\s+(?:a\s+|another\s+)?stroke\b",
    r"\bstroke\s+(?:right\s+)?now\b",
    r"\bjust\s+had\s+(?:a\s+)?stroke\b",
    r"\bhad\s+(?:a\s+)?stroke\s+(?:this\s+(?:morning|afternoon|evening)|today|yesterday|"
    r"an?\s+hour\s+ago)\b",
    # The F in FAST said with a hand: the thing it will not hold, or keeps dropping, plus another
    # sign of the same stroke in the line.
    _both_here(STROKE_HAND, STROKE_HAND_BESIDE),
)

SLUR_NOT_DENTAL = r"\A(?!.*\b(?:" + DENTAL_WORDS + r")\b)"
SIGHT_WORD = (
    r"\b(?:blind|sight|vision|eyes?)\b",
    r"\b(?:can'?t|cannot|can\s+not)\s+see\b",
    r"\b(?:lost|loss)\s+(?:the\s+)?(?:sight|vision)\b",
)


PEOPLE = (r"(?:i|i'm|i've|he|he's|she|she's|they|they're|we|you|someone|somebody|anyone|everyone|"
          r"my\s+" + PERSON + r"|the\s+" + PERSON + r"|" + PERSON + r")")

# A collapse the line itself says is a habit or a hypothetical is not someone going down now.
# Reading the present tense of the verb put "i collapse when i get up" and "i feel like i might
# collapse" on "Ring 999 or 911 straight away": dizziness on standing is one of the commonest
# things people bring, and the GP card it had before is the right envelope for it (brisk-turkey,
# #14526). What makes it a habit or a hypothetical sits on the collapse itself ("might collapse",
# "nearly collapse", "feel like ... collapsing") or on the moment it happens ("when i stand up",
# "every time", "too fast"), so only those shapes stand down - a line saying a person has gone down
# now, "my mum collapsed", "hes on the floor", keeps the ambulance.
A_HABITUAL_COLLAPSE = (
    r"\b(?:might|may|could|would)\s+(?:collapse|collapsed|collapsing|pass\s+out|passed\s+out|passing\s+out|"
    r"faint|fainted|fainting|go\s+down|went\s+down|going\s+down)\b",
    r"\b(?:nearly|almost|about\s+to)\s+(?:collapse|collapsed|collapsing|pass\s+out|passed\s+out|"
    r"passing\s+out|faint|fainted|fainting|go\s+down|went\s+down|going\s+down)\b",
    r"\bfeel(?:s|ing|t)?\s+like\s+(?:\w+\s+){0,4}(?:collapse|collapsing|passing\s+out|fainting|going\s+down)\b",
    r"\bwhen(?:ever)?\s+(?:i|we|you|he|she|they|my\s+" + PERSON + r"|the\s+" + PERSON + r")\b"
    r"(?:\s+\w+){0,4}\s+(?:stand|stands|standing|stood|get|gets|getting|got|sit|sits|sitting|sat)\b",
    r"\b(?:on|after|from|when)\s+standing\b",
    r"\b(?:every|each)\s+time\b", r"\bwhenever\b", r"\b(?:sometimes|often|always)\b",
    r"\btoo\s+fast\b",
    r"\bin\s+the\s+(?:heat|hot\s+weather)\b",
    r"\bif\s+(?:i|we|he|she|they)\s+(?:don'?t|dont|didn'?t|didnt|miss|misses|skip|skips)\b",
)
# Written once, because the collapse rows below both read the same fence.
NOT_A_COLLAPSE_NOW = r"(?![\s\S]*(?:" + "|".join(A_HABITUAL_COLLAPSE) + r"))"


# Someone else is the one at risk - "my wife wants to kill herself", "my friend has taken an
# overdose" - which needs a different reply (how to help them) from the user's own crisis.
OTHERS = (r"(?:he|he's|she|she's|they|they're|him|her|them|someone|somebody|anyone|everyone|"
          r"my\s+" + PERSON + r"|his\s+" + PERSON + r"|her\s+" + PERSON + r"|their\s+" + PERSON + r"|"
          + PERSON + r")")
# Somebody else talking about it, rather than doing it: "my dad keeps talking about ending it all
# when hes angry", "my son keeps talking about wanting to die". Named on its own because it has to
# stand the reader's own crisis card down as well - SELF_HARM_INTENT knows "wanting to die" and
# cannot tell whose wish it is.
TALKS_ABOUT_IT = (
    r"\b" + OTHERS + r"\b[^.?!]{0,40}\b(?:keeps?|kept|keeps\s+on)\s+(?:talking|mentioning|"
    r"saying|joking|going\s+on)\s+(?:about\s+)?(?:ending\s+(?:it|things)\s+all|suicid(?:e|"
    r"al)(?!\s*(?:rates?|statistics?|figures?|numbers))|killing\s+(?:him|her|them)sel(?:f|ves)|"
    r"not\s+being\s+here|want(?:s|ing|ed)?\s+to\s+die|dying)\b",
)
SOMEONE_ELSE_RISK = (
    r"\b" + OTHERS + r"\b.{0,40}\b(?:wants?\s+to\s+(?:die|kill\s+(?:him|her|them)sel(?:f|ves)|"
    r"end\s+(?:it|his\s+life|her\s+life))|(?:is|are)\s+going\s+to\s+kill\s+(?:him|her|them)sel(?:f|ves)|"
    r"suicidal|overdos\w*|(?:took|taken|swallowed)\s+(?:an?\s+overdose|pills|tablets|too\s+many)|"
    r"locked\s+(?:him|her)self\s+in\b.{0,40}\bpills\b)\b",
    r"\b(?:kill|hang)\s+(?:him|her|them)self\b(?!\s+(?:upside|on\s+the\s+(?:bars|swing)|from\s+the\s+bars))",
    r"\b(?:he|she|they)'?s?\s+been\s+(?:self[-\s]?harming|cutting)\b",
    # Any verb that hurts a body, with the relative as its object: "my sister wants to poison
    # herself", "my friend shoots herself", "my brother has been stabbing himself". A relative's
    # cut and burn already answered this way; the verb list is what was missing, not the shape.
    _HURTING_THEMSELVES,
    # The wish as a habit of thought or a feeling belongs to a relative too: "my son keeps
    # thinking of killing himself", "my mum feels like ending it".
    r"\b" + OTHERS + r"\b.{0,40}\b(?:(?:keeps?|kept)\s+thinking\s+(?:about|of)\s+"
    r"(?:ending\s+(?:it|his\s+life|her\s+life|their\s+life)|killing\s+(?:him|her|them)sel(?:f|ves)|"
    r"dying)|feels?\s+(?:like|as\s+if)\s+(?:ending\s+(?:it|his\s+life|her\s+life|their\s+life)|"
    r"killing\s+(?:him|her|them)sel(?:f|ves)|dying))\b",
    # The reader asking how to help somebody else: "how do i help a friend who self harms".
# A relative who keeps talking about it: "my dad keeps talking about ending it all when hes
    # angry", "my friend keeps talking about killing herself". The reader is the one asking for
    # help with somebody else, so the card that explains how to ask them is the answer; the
    # reader's own crisis line told them to ring a helpline about their father's mood.
    *TALKS_ABOUT_IT,
)
SOMEONE_ELSE_RISK = (*SOMEONE_ELSE_RISK, *HELP_SOMEONE)
# "Wants to be dead", and the euphemism people use instead of the word, are the two ways somebody
# reports a relative's wish, and both were read without asking whose wish it was. "my dad wants to
# be dead" and "my son keeps saying he wants to be dead" handed the *speaker* their own crisis card,
# with the person at risk sitting in the same room, and "my sister doesnt want to be here anymore"
# got the greeting and a shrug - the one reply somebody reporting that must not get. Only a person
# is a subject here, and "going to die" is deliberately not in it: "my dad is going to die" is a
# terminal illness and the waiting for it, not a wish.
THIRD_PERSON_WISH = (
    r"\b" + OTHERS + r"\b[^.?!]{0,30}\b(?:wants?\s+to|keeps?\s+saying\s+(?:he|she|they)\s+wants?\s+to|"
    r"says?\s+(?:he|she|they)\s+wants?\s+to|told\s+me\s+(?:he|she|they)\s+wants?\s+to)"
    r"\s+be\s+dead\b",
    # The euphemism rather than the word, which is how most people say it out loud. A place after
    # "here" is the party, the school or the office, so that arm stands this one down: it is somebody
    # who does not want to go somewhere, not somebody at risk.
    r"\b" + OTHERS + r"\b[^.?!]{0,30}\b(?:doesnt|doesn'?t|does\s+not|didnt|didn'?t|did\s+not|"
    r"dont|don'?t|do\s+not)\s+want\s+to\s+(?:"
    # "live" is the risky one: "my mum doesnt want to live here any more" is a house.
    r"live(?!\s+(?:here|there|with|in|at|on|near|abroad|alone|anywhere|somewhere|off)\b)|"
    r"be\s+here|be\s+alive|exist|be\s+around\s+(?:any\s?more|no\s?more)|"
    # "go on" is a trip unless it is the end of the sentence or "any more".
    r"(?:carry|go)\s+on(?=\s*(?:[.?!]|$)|\s+(?:any\s?more|no\s?more)\b))"
    r"(?!\s+(?:at|on|for|in|with|to)\b)",
)


# The same two arms answer it: a relative's wish said in either of the ways people report it is the
# person at risk, and the card that names them is the reply. One pattern raises that card and stands
# the speaker's own down, so the two can never drift apart.
SOMEONE_ELSE_RISK = (*SOMEONE_ELSE_RISK, *THIRD_PERSON_WISH)
# The suicide words with somebody else as their subject: "my dad keeps talking about ending it
# all", "my neighbour keeps mentioning suicide". They were all getting the reader's own crisis
# card, which asks the wrong person to ring a helpline. Where the line also says how to help
# ("keeps talking about", "said she wants to") SOMEONE_ELSE_RISK answers it first; the rest, a
# bereavement said plainly ("my dad died by suicide"), is the loss module's to answer.
SUICIDE_OTHER = (
    r"\b(?:he|she|they|someone|somebody|anyone|a\s+(?:person|friend|man|woman|boy|girl)|"
    r"my\s+(?!own\b)" + PERSON + r")\b[^.?!]{0,40}\b(?:suicid\w*|"
    # "ending it" without "all" is how most people say it, and the speaker's own crisis card was
    # the reply to somebody reporting it: "my friend told me she wants to end it". A person after
    # "with" is a breakup ("my wife wants to end it with me") and stays out, the same fence every
    # other "end it" arm uses.
    r"end(?:ing)?\s+(?:it(?!\s+with\s+" + END_IT_WITH_PERSON + r"\b)|things\s+all\b)|"
    r"kill(?:ed|ing)?\s+(?:him|her|them)sel(?:f|ves))\b",
)
# A death reported as a death is the loss module's to answer, so it is left exactly as main had
# it: this guard is for the word used as a topic, and for a relative who keeps talking about it.
DEATH_REPORT = (
    r"\b(?:died|dies|dead|passed\s+away|killed\s+(?:him|her|them)sel(?:f|ves)|took\s+(?:his|her|"
    r"their)\s+own\s+life|committed\s+suicide)\b",
)
# ...unless the speaker is saying it about themselves in the same line: "my mum died by suicide and
# i keep thinking about it myself" is the reader's crisis.
OWN_DISTRESS = (
    r"\bi\s+(?:want|wanna|feel|felt|keep|kept|am|im|i'm|was|have|had|think|thought|plan|planned)"
    r"\b[^.?!]{0,25}\b(?:suicid\w*|die|dying|dead|end(?:ing)?\s+(?:it|things)\s+all|"
    r"kill\s+my\s*self|hurt\s+my\s*self)\b",
    r"\bmyself\b",
)
SHAKEN_FINE = (
    r"\b(?:awake|to\s+wake|gently|playfully|to\s+wake\s+(?:him|her|them)|rattle|toy|bottle|"
    r"blanket|milk)\b",
)
HUMAN_ANCHOR = ((r"\b(?:i|i'm|i've|he|she|someone|somebody|anyone|everyone)\b|"
                 r"\b(?:my|the)\s+" + PERSON + r"\b|\b" + PERSON + r"\b|" + AGE_PERSON[0]),)
PERSON_WORD = ((r"\b(?:my|the)\s+" + PERSON + r"\b|\b" + PERSON + r"\b"),)

# The mouth is where a pet's colour shows, and the pet table answers that one in its own words.
PET_MOUTH = (r"\b(?:gums?|gum\s?colou?r)\b",)
# "went blue" is how most people say a pet's colour changed, and BLUE_CHANGE has only "gone".
PET_BLUE_WENT = (r"\bwent\s+(?:blue|grey|gray)\b", r"\b(?:is|was|looks?)\s+(?:blue|grey|gray)\b")
# A part of a pet that can show a colour: a blue collar, a blue bowl or a blue bed is a thing.
PET_BLUE_PART = (
    r"\b(?:lips?|tongue|mouth|gums?|face|nose|paws?|tummy|belly|skin|ears?|eyes?|nails?)\b",
)
# The lips and the face are where cyanosis shows, so a cold cause does not explain them away;
# a blue tongue from a slushie, cold hands or dye on the skin is the colour of a thing. A person
# who "is blue and cold" is not a limb, though, and that one still rings.
BLUE_LIPS_FACE = (
    r"\b(?:lips?|face|around\s+the\s+(?:lips?|mouth)|round\s+the\s+(?:lips?|mouth))\b",
)
BLUE_LIMB = (
    r"\b(?:fingertips?|fingers?|hands?|toes?|feet|legs?|arms?|tongue|mouth|skin|cheeks?|knees?|"
    r"nails?|nail\s?beds?|gums)\b",
)
# A bruise, a vein or a mark going blue is the colour of a thing that is not the person's oxygen.
BLUE_MARK = (
    r"\b(?:bruise|bruises|bruised|bruising|vein|veins|mark|marks|spot|spots|patch|patches|"
    r"tattoo|scar|scars|nail\s?varnish|plaster|bandage|dressing|nappy|nappies|ring|rings)\b",
)
# The cold explains a hand, a foot or a tongue, even when the line says the colour changed.
BLUE_COLD = (
    r"\b(?:cold|freezing|frozen|chilly|perishing|slushie|slush|ice|iced|lolly|popsicle|"
    r"snowball|snow)\b",
)
LIPS_RED_FLAG = (
    r"\b(?:breath\w*|gasping|struggling|chest|collapsed|unresponsive|not\s+responding|floppy|"
    r"limp|sleepy|grunting|shivering\s+badly|shaking)\b",
    r"\b(?:baby|babies|newborn|child|children|kid|kids|son|daughter|toddler|infant|boy|girl)\b",
)

# "i went blue in the cold" is hands and feet, not oxygen: a cold cause on the speaker's own limbs
# stands the arm down unless the lips, a breath or a child are named.
BLUE_COLD_SELF = (r"\b(?:in|from|out\s+in)\s+the\s+cold\b",)
# ...and the limbs the cold gets to, or the speaker talking about themselves.
BLUE_SELF = (
    r"\b(?:i|i'?m|im|me|myself)\b",
    r"\bmy\s+(?:hands?|fingers?|fingertips?|toes?|feet|legs?|arms?|skin|knees?|nails?)\b",
)

# The colour of a limb is a change when the line says it changed: "my fingers have gone blue".
BLUE_CHANGE = (
    r"\b(?:turned|turning|goes|going|gone|get|gets|getting|is\s+turning|looks?|looking|looked|"
    r"appears?|seems?|become|becomes|becoming|suddenly|started?)\b",
)


# A tan, a sunburn or a scar that never fades is not the glass test: those words sit next to
# "doesnt fade" often, and none of them is a spot that stays under a glass.
FADE_EVERYDAY = (
    r"\b(?:tan|tans|tanning|sunburn\w*|scar|scars|scarring|scab|scabs|eczema|psoriasis|"
    r"birthmark\w*|bruise|bruises|stain|stains|freckl\w*|hickey|fake\s+tan|marker|biro|pen\s+mark)\b",
)


def _glass_test_line(line, before):
    """True when this line and the turn before it together say "a rash that does not fade".

    "my son has a temperature and a rash" then "it doesnt fade when pressed": neither line says
    it alone, and the pair is the meningitis case.
    """
    if _matches(FADE_EVERYDAY, line):
        return False
    if not (_matches(RASH_FADE, line) and _matches((RASH,), before)):
        return False
    return _matches(RASH_COMPANY, line) or _matches(RASH_COMPANY, before)


def _said_before(memory, turns=2):
    """The last things the user said, for a sign that was named a turn earlier.

    A parent says "my son has a temperature and a rash" and gets the glass test back, then
    answers it: "the rash doesnt fade when i press it". The fever and the child are in the turn
    before, so the line is the meningitis case, not a mark on an arm that faded.
    """
    said = []
    for turn in reversed((memory.get("turns") or [])[-turns:]):
        if isinstance(turn, dict) and turn.get("user"):
            said.append(_norm(str(turn["user"])))
    return " ".join(said)


def _person_before(memory):
    """The last thing the user said, for deciding whether a bare "they" means people."""
    turns = memory.get("turns") or []
    for turn in reversed(turns[-3:]):
        if isinstance(turn, dict) and turn.get("user"):
            return _norm(turn["user"])
    return ""


# The user speaking for themselves: "i want to die" is their own crisis however the rest reads.
_FIRST_PERSON_ME = (r"\b(?:i\s+want|i\s+don't\s+want|i'?ve\s+(?:taken|took)|killing\s+my\s*self|"
                    r"kill\s+my\s*self|hurt\s+my\s*self|end\s+it\s+all)\b",)

# The speaker's own wish, said in the same line as a dying pet or plant: "my dog is going to die
# and i feel like ending it" is both, and the crisis is the half that matters.
OWN_WISH = (
    r"\bi\s+(?:want|wanted|wanna|dont|don'?t|feel\s+like|feel|felt|plan|planning|can'?t|cant|won'?t|"
    r"would\s+rather|rather)\b[^.?!]{0,30}\b(?:die|dying|dead|end(?:ing)?\s+it|end\s+my(?:\s+own)?\s+"
    r"life|kill\s+my\s*self|live|here|go\s+on|carry\s+on|not\s+being\s+here)\b",
    r"\bmyself\b", r"\bnothing\s+(?:left\s+)?to\s+live\s+for\b",
    r"\b(?:nobody|no\s?one)\s+would\s+(?:notice|care|miss\s+me)\b",
    r"\bbetter\s+off\s+(?:dead|without\s+me|if\s+i\s+was\s+gone)\b",
    r"\bnot\s+worth\s+(?:it|living)\b",
    # "i keep thinking about ending it" is the speaker's own wish said as a habit of thought, so it
    # has to keep the crisis line when the same line also has a pet or a relative dying.
    r"\bi\b[^.?!]{0,20}\b(?:keep|keeps|kept)\s+(?:thinking|having\s+thoughts)\s+(?:about|of)\s+"
    r"(?:ending|killing|dying|suicide|not\s+being\s+here)\b",
    r"\bi\s+(?:think|thinks|thought|dream)\s+(?:about|of)\s+(?:ending|killing|suicide|dying|dead)\b",
)

# The bare word "myself" was read as a wish of the speaker's, and it is in the sentences where they
# talk to themselves: "my nan is going to die and i keep telling myself it will be ok" got the
# crisis card over a line that is grief, and so did "i told myself not to cry" beside a dying pet.
# The bare word is a wish only when the speaker is not just talking to themselves, which is what
# SELF_TALK names; every other cue in OWN_WISH counts as it did.
WISH_OWN_BARE = tuple(p for p in OWN_WISH if p != r"\bmyself\b")


def _own_wish(line):
    """The speaker's own wish to be dead or gone, said in any of OWN_WISH's ways.

    A wish that names the harm still counts with "myself" in the line, and so does the bare word
    anywhere the speaker is not talking to themselves.
    """
    return _matches(WISH_OWN_BARE, line) or (_matches((r"\bmyself\b",), line)
                                             and not _matches(SELF_TALK, line))


# The ways somebody is said not to wake. Every negative modal, including the past ones, because
# "she laughed so much she couldnt be woken" and "he collapsed laughing and wouldnt wake" are the
# same fact as "wont wake" - and they were reaching the small-talk pool ("Ha - that good?").
NOT_WAKE_MODAL = (r"(?:won'?t|wont|wouldn'?t|wouldnt|couldn'?t|couldnt|didn'?t|didnt|"
                  r"can'?t|cant|cannot|isn'?t|isnt|is\s+not|not|never)")
# A professional who has not answered is a message, not a body. "my carer is not responding" is the
# commonest way of saying the carer has not replied to a text, and it rang the ambulance; the same
# line about a friend or a husband is a collapse. So the not-responding arms stand down when the
# only person named is a professional, and anything that puts the body in the room - the floor, the
# bed, breathing, a colour - brings the call back (teal-spruce, #12389).
PRO_NOT_ANSWERING = (
    r"\b(?:my|his|her|their|our|the)\s+(?:carers?|care\s+workers?|support\s+workers?|"
    r"social\s+workers?|personal\s+assistants?|nurses?|midwives?|midwife|doctors?|gps?|"
    r"physios?|therapists?)\b[^.?!]{0,30}\b(?:isn'?t|is\s+not|not|hasn'?t|has\s+not|never|"
    r"no)\s+respond(?:ing|ed|e)?\b",
    r"\bno\s+response\s+from\s+(?:my|the|our)\s+(?:carer|care\s+worker|support\s+worker|"
    r"social\s+worker|personal\s+assistant|nurse|doctor|gp|physio|therapist)s?\b",
)
# "Unresponsive" is also how people describe somebody's manner, not their body: "my boss was
# unresponsive to my emails", "my son is unresponsive when hes told off". The adjective alone is not
# the sign then, so the state stands down - unless something in the line puts the body in the room,
# which is what BODY_IN_THE_ROOM is for below.
UNRESPONSIVE_MANNER = (
    r"\b(?:to|about|on|in)\s+(?:my|his|her|their|the|our|a|an)?\s*\w*\s*"
    r"(?:texts?|emails?|e-?mails?|messages?|msgs?|calls?|letters?|questions?|requests?|"
    r"complaints?|invites?|applications?|interviews?|thread|group\s+chat|whatsapp|facebook|"
    r"social\s+media|feedback|criticism|suggestions?)\b",
    r"\bwhen(?:ever)?\s+(?:he|she|they|i|we)(?:'s|s|'re|re)?\b[^.?!]{0,25}"
    r"\b(?:told\s+off|told\s+no|told|ignored|shouted\s+at|ticking\s+off|naughty|"
    r"in\s+trouble|sulking|sulky|pulling\s+a\s+face)\b",
    r"\b(?:at\s+(?:work|school|college|uni|university)|in\s+meetings?|on\s+the\s+group)\b",
)
# The body in front of the reader: any of these turns the message back into a collapse.
BODY_IN_THE_ROOM = (
    r"\b(?:floor|ground|bed|sofa|settee|couch|bath|pavement|street|doorstep)\b",
    r"\b(?:collapsed|collapsing|fell|fallen|fainted|pass(?:ed)?\s+out|seizure|fitting)\b",
    r"\b(?:breathing|breath|breathe|pulse|blue|lips|cold|clammy|sweating|eyes|pale|grey|gray)\b",
    # "unresponsive" is deliberately not here: it is the state being tested, so it would match every
    # line this fence is meant to read. "out cold" and "on the floor" are body signs, not states.
    r"\b(?:unconscious|out\s+cold|in\s+front\s+of\s+me|with\s+me|next\s+to\s+me)\b",
    # A body that does not answer to pain or to its own name is the collapse; a carer who does not
    # answer a text is the message. "to my texts" is deliberately not here.
    r"\b(?:to\s+(?:pain|touch|voices?|noise|light|stimulus)|(?:his|her|their)\s+name)\b",
)
UNCONSCIOUS = (
    # "unconscious" about a person, not "unconscious bias" or "unconscious mind".
    r"\bunconscious\b(?!\s+(?:bias|biases|mind|thought|thoughts|desire|wish|belief|prejudice|"
    r"process|choice|decision|level))",
    r"\b" + NOT_WAKE_MODAL + r"\s+waking\s+up\b",
    # "my husband won't wake up", "my grandad can't wake up". The first person is left out: "i
    # can't wake up in the mornings" is an insomnia complaint, not a collapse.
    r"\b(?:he|she|they|my\s+" + PERSON + r"|the\s+" + PERSON + r")\b(?:\s+\w+){0,3}\s+"
    + NOT_WAKE_MODAL + r"\s+wak(?:e|ing)\b",
    r"\b" + NOT_WAKE_MODAL + r"\s+wake\s+(?:him|her|them)\b",
    # "my husband is on the floor and wont wake up": the floor says it is happening now, so the
    # words between the person and the verb do not matter.
    r"\bon\s+the\s+(?:floor|ground)\b.{0,30}\b" + NOT_WAKE_MODAL + r"\s+wak(?:e|ing)\b",
    r"\b" + NOT_WAKE_MODAL + r"\s+(?:be\s+)?woken\b", r"\bpassed\s+out\b.{0,20}\b(?:and|not)\b",
    # "he was out cold and wouldnt wake up" is the same collapse told in the past tense, and the
    # past-tense negative is in none of the patterns above: the line was a comfort line. "wouldn't
    # wake up" on its own stays out, because a teenager who would not get up is a grumble - it is
    # the out-cold that makes this the recovery-position call.
    r"\bout\s+cold\b[^.?!]{0,40}\b(?:won'?t|wont|wouldn'?t|wouldnt|couldn'?t|couldnt|"
    r"can'?t|cant|not|didn'?t|didnt)\s+wak(?:e|ing|en)\b",
    r"\b(?:won'?t|wont|wouldn'?t|wouldnt|couldn'?t|couldnt|can'?t|cant|not)\s+wak(?:e|ing|en)\b"
    r"[^.?!]{0,30}\bout\s+cold\b",
    r"\bno\s+pulse\b",
    # "my mum passed out on the floor" is an emergency; "I passed out at the gym last week" is not.
    r"\bpassed\s+out\b(?:\s+\w+){0,3}\s+on\s+(?:the\s+)?(?:floor|ground|pavement|street)\b",
    r"\b" + PEOPLE + r"\b\s+(?:just|suddenly|then)\s+passed\s+out\b(?!\s+(?:laughing|crying))",
    # "not responding" about a person or an animal, not a laptop, a website or an app.
    r"\b" + PEOPLE + r"\b(?:\s+\w+){0,3}\s+(?:is\s+|isn't\s+|is\s+not\s+)?not\s+responding\b"
    r"(?!\s+(?:well\b|" + RESPOND_SENSE + r"))",
    r"\b(?:he|she|they|my\s+" + PERSON + r")\s+(?:is|'s)\s+not\s+responsive\b",
    # "my mum is unresponsive" is the shortest way to say it about somebody else, and the file had
    # the joined pronoun ("hes unresponsive") and "not responsive", but not the plain adjective
    # after a person: "my mum is unresponsive", "my dad is unresponsive" and "my wife is
    # unresponsive but breathing" were all a chat nod.
    r"\b\s?(?:(?:he|she|they)\b|(?:my|his|her|their|our|the)\s+" + PERSON + r"\b)"
    r"(?:\s+\w+){0,3}\s+(?:is|are|was|were|'s|'re|seems?|looks?|has\s+gone|have\s+gone|now)\s+"
    r"(?:now\s+)?unresponsive\b"
    r"(?!\s+(?:to\s+(?:[\w']+))?\s*(?:food|dinner|tea|treats?|name|his|her|their|my)\b)",
    # A body on the floor that is not responding. The posture is the sign, so no person word is
    # needed: "the care worker is on the floor and not responding" was answered "Right. What have
    # you tried so far?" because every arm above wanted "my <person>" or a pronoun in front of the
    # verb (teal-spruce, #12389).
    r"\bon\s+the\s+(?:floor|ground)\b[^.?!]{0,40}\b(?:not\s+responding|unresponsive)\b",
    r"\b(?:he|she|they|my\s+" + PERSON + r"|the\s+" + PERSON + r")\b(?:\s+\w+){0,3}\s+"
    r"(?:won't|wont|isn'?t|is\s+not|not)\s+respond(?:ing)?\b(?!\s+(?:well\b|" + RESPOND_SENSE + r"))",
    # The two reports above with the verb joined to the pronoun - "shes unresponsive", "hes not
    # responding", "theyre unresponsive" - which is how people type a collapse. Every pattern above
    # spells the verb out, so without this the shortest form of the most urgent line gets small
    # talk. The guard is an allow-list of the ordinary readings, not a blocklist of the tail: after
    # "to", only a message, a treatment or a food can be a thing that has not worked ("to emails",
    # "to the antibiotics", "to her new milk"), and a condition or a usual way ("when i text her",
    # "as usual") is not a collapse. Everything else after "to" - "to pain", "to touch", "to
    # voices", "to his name", "after the fall" - keeps the ambulance. "well" is the file's own
    # guard and carries over: "hes not responding well" and "shes not responding well to the
    # antibiotics" are how a treatment is going, not a collapse.
    r"\b(?:he|she|they)(?:'s|s|'re|re)\s+(?:not\s+responding|unresponsive)\b"
    r"(?![\s-]*(?:well\b|to\s+(?!(?:pain|painful|touch|stimulus|stimuli|light|voices?|noise|sound|"
    r"anything|anyone|me|us|a\s+word|(?:the|a)\s+light|"
    r"(?:a\s+)?painful\s+stimulus|my\s+voice|his\s+voice|her\s+voice|their\s+voice|"
    r"(?:his|her|their|my|the)\s+name)\b)"
    r"|when|whenever|if|because|as\s+(?:usual|always|normal|ever)|as\s+he|as\s+she|as\s+they|"
    # A colleague, a group chat or a sulk, not a body: "hes unresponsive at work lately" and
    # "hes not responding because hes sulking" are how people describe someone who will not
    # answer. "at the scene" and "since the fall" are not in this list on purpose.
    r"lately|recently|these\s+days|at\s+(?:work|school|college|uni|university))\b)"
    # A collapse with a fever or an infection is the sepsis case, which has its own answer
    # ("say you're worried about sepsis, that is the word that gets them there fast"), so leave
    # that line to it rather than taking it with the generic first-aid reply.
    r"(?![\s\S]*\b(?:fever|temperature|sepsis|rigors|shivering|infection)\b)",
    # A person collapses. A cake, a shelf or a market collapses too, so the subject has to be one.
    # Every form of the verb counts, not only the past tense: "my mum collapsing on the floor just
    # now" was answered "Ring 111 or your surgery this week rather than waiting it out", because
    # only `collapsed` was in the pattern - the present tense of the same thing, which is the more
    # urgent of the two, reached the GP card while "my dad has collapsed" reached the ambulance.
    # ...and a collapse the line says is a habit or a hypothetical stands down, which is the fence
    # above: "i collapse when i get up" is the GP card, "my mum is collapsing" is the ambulance.
    NOT_A_COLLAPSE_NOW + r"\b" + PEOPLE + r"\b(?:\s+\w+){0,4}\s+collaps(?:e|es|ed|ing)\b",
    NOT_A_COLLAPSE_NOW + r"\bcollaps(?:e|es|ed|ing)\b.{0,30}\b(?:and\s+(?:isn't|is\s+not|won't|wont|stopped|not)\s+(?:breathing|waking|responding|conscious)|"
    r"on\s+(?:the\s+)?(?:floor|ground|pavement|street|kitchen\s+floor|bathroom\s+floor))\b",
    r"\b(?:he|she|they|my\s+" + PERSON + r")\s+(?:is|'s)\s+out\s+cold\b",
    # Something fell on someone: "the roof collapsed on the kids", "the shelf came down on me".
    r"\b(?:collapsed|came\s+down|fell)\b.{0,30}\b(?:on|onto|over|on\s+top\s+of)\s+(?:the\s+|my\s+|his\s+|"
    r"her\s+|our\s+|a\s+)?" + PEOPLE + r"\b",
)


# A machine has a fit when it breaks down, so "my laptop had a fit" is not a body on the floor.
THING_FIT_SUBJECT = (
    r"\b(?:my|the|our|his|her|their|your)\s+(?:laptop|computer|pc|phone|printer|car|van|engine|"
    r"boiler|washing\s+machine|dishwasher|fridge|freezer|telly|tv|wifi|internet|heating|"
    r"shower|oven|kettle|hoover|vacuum|mower|motorbike|bike|scooter|website|site)\b",
)
# ...but a pet that has one is a pet case, and the pet answer names the vet rather than 999.
ANIMAL = (
    r"\b(?:dog|puppy|pup|cat|kitten|horse|pony|rabbit|hamster|guinea\s+pig|parrot|budgie|bird|"
    r"ferret|tortoise|snake|pet)\b",
)

# A choke whose object is speech is a stutter, not an airway: "im choking on my words", "i choked
# on a word in my speech". The thing was never in the throat, so the back-blows card is the wrong
# instruction; a real choke said after it keeps the card through the red lists below.
CHOKE_WORDS = (
    r"\bchok(?:e|ed|es|ing)?\s+on\s+(?:(?:my|his|her|their|your|our|the|a|an)\s+)?(?:own\s+)?"
    r"(?:words?|sentences?|speech|lines?|names?|syllables?|pronunciation)\b",
)


# The lips and the face are where the oxygen shows, so the cold and the laundry stand-downs are for
# the limbs only: "ive got blue lips from the cold" is not an echo and not a warm drink.
BLUE_FACE_PART = (r"\blips?\b", r"\bface\b", r"\bmouth\b", r"\btongue\b")
# "i went blue in the face laughing" is the idiom for holding your breath, not a colour change.
# Blue lips that a lipstick or a photograph explains are not a colour change at all: "my lips are
# blue with lipstick" and "my lips look blue on zoom" are a question about make-up, a filter or the
# light. The breathing red flags still win, so "my lips are blue and i cant breathe" keeps the card.
BLUE_COSMETIC = (
    r"\b(?:make-?up|lipstick|lip\s+gloss|lip\s+stain|lip\s+balm|gloss|tint|blusher|bronzer|"
    r"eyeshadow|eye\s+shadow|foundation|contour|filter|photo\w*|zoom|selfie|camera|webcam|"
    r"screen|monitor|lighting|light\s+is|bad\s+light|the\s+light|in\s+this\s+light)\b",
)
# Whose body part it is: "my hand in the blender" is the user, "my son went blue" and "his lips
# are blue" are somebody else, and the card has to say the right one.
OTHER_BODY = (
    r"\b(?:he|she|they|him|her|them)\b",
    r"\b(?:my|our|his|her|their|the)\s+" + PERSON + r"\b",
    r"\b(?:his|her|their)\s+(?:lips?|face|mouth|tongue|hands?|fingers?|fingertips|toes?|feet|"
    r"foot|arms?|legs?|throat|head)\b",
)
# Hands and feet that go white, then blue, then red and sore in the cold are Raynaud's: common,
# worth a GP word, and nothing like an ambulance.
RAYNAUD = (
    r"\b(?:fingers?|fingertips|hands?|toes?|feet|foot)\b[^.?!]{0,40}\b(?:white|blue|purple|grey|"
    r"gray|numb|dead|burning)\b",
    r"\braynaud\w*\b",
)
# The limb itself says nothing: "my hands have gone blue" with no cause in the line is a colour
# change on a person, which is the 999 card main gave before this PR. Only a cause on the line
# makes a limb a surgery question.
LIMB_PART = (
    r"\b(?:fingers?|fingertips|hands?|toes?|feet|foot|arms?|legs?|fingernails?|nails?)\b",
)
WENT_BLUE_BREATH_RED = (
    r"\b(?:can'?t|cannot|not|struggling\s+to|stopped)\s+breath\w*\b", r"\bgasping\b",
    r"\bunconscious\b", r"\blimp\b", r"\bfloppy\b", r"\bunresponsive\b",
    r"\bnot\s+waking\b", r"\bchoking\b", r"\bfaint\w*\b",
)
WENT_BLUE_RED = (
    r"\b(?:can'?t|cannot|not|struggling\s+to|stopped)\s+breath\w*\b", r"\bgasping\b",
    r"\blips?\b", r"\bface\b", r"\bunconscious\b", r"\blimp\b", r"\bfloppy\b",
    r"\bunresponsive\b", r"\bnot\s+waking\b", r"\bchoking\b",
)
STUCK_FINE = (
    r"\b(?:jar|bottle|lid|zip|zipper|box|tin|can|bucket|tube|boot|shoe|lock|tap|plug|key|hole)\b",
)


DROWNING = (
    r"\b(?:he|she|they|my\s+\w+|someone)\s+(?:is\s+|'s\s+)?drowning\b", r"\b(?:pulled|dragged|got)\s+(?:him|her|them|someone)\s+out\s+of\s+the\s+(?:water|pool|sea)\b",
    r"\bnearly\s+drowned\b", r"\b(?:stopped|not)\s+breathing\s+after\s+(?:the\s+)?water\b",
)
# Somebody has to be in the water: a road, a cellar and a car are flooded, not drowning.
WATER_DANGER_PERSON = (
    r"\b(?:baby|babies|newborn|infant|son|daughter|child|children|kid|kids|boy|girl|toddler|"
    r"little\s+one|niece|nephew|grandson|granddaughter|he|she|him|her|them|they|someone|"
    r"somebody|anyone|i|me|my|we|us|our)\b",
)
# ...unless it is a push into a pool with nothing wrong in the line, which is a summer afternoon and
# not a rescue: "my mate pushed me in the pool".
WATER_SELF_PUSH_FINE = (
    r"\b(?:mate|mates|friend|friends|brother|sister|cousin|husband|wife|partner|kids?|lads?|"
    r"guys?|son|daughter|he|she|they)\b[^.?!]{0,15}\b(?:pushed|shoved|threw|tipped|knocked)\s+me"
    r"\s+(?:in|into)\b",
)
# A pet that went in is the pet's own answer: `my` counted as the person, so `my dog fell in the
# pond` and `my cat fell in the water` were the 999 card (@white-ruler). A person in the same line
# keeps the card - "my dog fell in the pond and i went in after him" is about the person.
WATER_PET = (
    r"\b(?:dogs?|doggy|pupp(?:y|ies)|cats?|kittens?|horses?|pon(?:y|ies)|rabbits?|bunny|"
    r"guinea\s+pig|hamsters?|ferrets?|parrots?|chickens?|hens?|cows?|sheep|lambs?|goats?|"
    r"pigs?|piglets?|tortoises?|lizards?|snakes?|budgies?|gerbils?|mice|mouse|rats?|pets?)\b",
)
# A past trip into the water is a story unless something is still going on, and a swimming lesson,
# a splash about or a child who came up laughing is not a drowning.
WATER_STORY = (
    r"\b(?:yesterday|last\s+(?:night|week|month|year|summer|winter|spring)|years?\s+ago|"
    r"when\s+i\s+was\s+(?:a\s+)?(?:child|kid|boy|girl|little|younger|small)|used\s+to)\b",
)
# The speaker's own dip in the water, said as an ordinary thing: "i went under the water at the
# pool" is how a swim is described, and it is not a drowning unless the line says it still is.
WATER_SELF_DIP = (
    r"\bi\s+(?:went|go|goes|gone|sank|sunk|dived?|dove|swam)\s+(?:under|below)\b",
)
# ...and the breath after it is what makes it an accident: "i went under the water and swallowed
# half the pool" is a story, "i went under and couldnt breathe" is not.
WATER_BREATH_RED = (
    r"\b(?:couldn'?t|could\s+not|can'?t|cant|not|stopped|struggl\w+|fought)\b[^.?!]{0,15}"
    r"\b(?:breath\w*|breathing)\b",
)
# A child who can now swim under is the opposite of a drowning, and the bare `underwater` arm made
# "my son can swim underwater now" and "the kids love going underwater" the 999 card
# (@steward-bold-arrow). `now` is in the urgent list, so these have their own list and their own
# fence: a swim line that also says what is wrong in the water is still the card.
WATER_SWIM = (
    r"\b(?:swims?|swam|swum|swimming|dives?|dived|dove|going|goes|gone|can\s+swim|"
    r"learning\s+to\s+swim|learnt)\s+underwater\b",
    r"\bunderwater\s+(?:now|too|as\s+well)\b",
    r"\bunderwater\s+for\s+the\s+first\s+time\b",
)
# What is still wrong in the water keeps the 999 card even when the head is the thing that went
# under: the breath, the colour, the stillness, and the not coming up. `WATER_URGENT` cannot be
# reused for that fence, because "cant get my head under water" and "i struggle to put my head
# under water" are exactly the lines this stands down, and both carry "cant get" / "struggle"
# as the swimmer's own words rather than as a sign.
WATER_STILL_BAD = (
    r"\b(?:not\s+breathing|didn'?t\s+come|hasn'?t\s+come|limp|unresponsive|not\s+moving|"
    r"blue|still\s+under|under\s+for|couldn'?t\s+get\s+(?:him|her|them|me)\s+(?:out|up)|"
    r"(?:can'?t|cant|couldn'?t)\s+see)\b",
)


# A snake bite is venom, not a wound: the advice is stillness, a calm 999 call and no cutting,
# sucking or tight band. Main answered `my son has been stung by a snake` with "Noted: your son has
# been stung by a snake." The UK's only venomous snake is the adder, and grass snakes are harmless.
SNAKE_BITE = (
    r"\b(?:snake|adder|adders|viper|cobra|rattlesnake|mamba|krait)\b[^.?!]{0,30}"
    r"\b(?:bit|bite|bitten|bit\s+me|struck|sting|stung)\b",
    r"\b(?:bit|bitten|stung|sting)\s+(?:by|on\s+the\s+\w+\s+by)\s+(?:a|an|the|my|his|her|this)\s*"
    r"(?:snake|adder|viper|cobra)\b",
)
ANIMAL_KICK_LOOKALIKE = (
    r"\b(?:fence|gate|stable|door|barn|bucket|ball|trolley|car|trailer|wall|post)\b",
    r"\b(?:kicks?\s+off|kick\s+off|kicked\s+off)\b",
)
# ...and the speaker's own hands: "i put my hands round my neck to keep warm", "i wrapped my hands
# around my neck". The neck card is for someone else's hand, and the cold answer is the right one.
STRANGLE_OWN_HANDS = (
    r"\bi\s+(?:put|place[ds]?|putting|wrap(?:ped|ping|s)?|wound|kept|have|had|got|held|cups?|"
    r"cupped|rest(?:ed|ing)?|tucked)\b[^.?!]{0,20}\bmy\s+(?:own\s+)?hands?\b",
)

# ...and the lines where the word is doing something else: a collar, a game, or a business that is
# being strangled. A hand on the throat is not on any of these.
STRANGLE_LOOKALIKE = (
    r"\b(?:jokingly|playfully|for\s+a\s+laugh|mucking\s+about|messing\s+about|in\s+judo|"
    r"at\s+judo|wrestling|in\s+training|during\s+training|at\s+rugby|in\s+the\s+scrum|"
    r"in\s+fun|as\s+a\s+joke)\b",
    r"\b(?:collar|tie|scarf|seatbelt|seat\s+belt|strap|helmet|necklace|hoover|vaccum|"
    r"vacuum|lettuce|pipe|hose|noose\s+of)\b",
    r"\b(?:business|company|economy|budget|deadline|bills?|rent|workload|club|team|crop|"
    r"market|industry|startup|shop|sales|paperwork|red\s+tape|admin|forms?|tax|taxes|"
    r"regulations?|rules|bureaucracy|traffic|inbox|emails?)\b",
    *STRANGLE_THING_SUBJECT,
    *STRANGLE_OWN_HANDS,
)


GAS_IN_ROOM = (
    r"\b(?:kitchen|boiler|oven|cooker|hob|flat|house|home|room|garage|meter|pipe|pipes|heater|"
    r"fire|cooker|cylinder|hall|hallway|bathroom|cellar|basement|camper|caravan|shop|workshop)\b",
)

GAS_NOW = (
    r"\b(?:still|now|right\s+now|just\s+now|this\s+(?:morning|afternoon|evening)|tonight|today|"
    r"again|earlier\s+today)\b",
    r"\b(?:can|could)\s+(?:i|you|we|she|he|they)\s+smell\b",
)


# Breathless lying down or sitting still is the urgent answer however it is phrased.
BREATH_AT_REST = (
    r"\b(?:at\s+rest|sit(?:ting)?\s+still|sat\s+still|in\s+bed|lying\s+down|lie\s+down|"
    r"laying\s+down|doing\s+nothing|resting)\b",
)
# Singing, talking and laughing leave a person out of breath and are not exercise: they excuse
# "out of breath" and nothing else. "shortness of breath when talking" is a red flag, not a hobby.
EFFORT_WEAK = (r"\b(?:singing|sing|laughing|talking|chatting)\b",)
OUT_OF_BREATH = (r"\bout\s+of\s+breath\b",)
# A thing does not breathe. "the app has trouble breathing" and "my car is having trouble
# breathing" are the two shapes where the words are right and the subject is not a person, and
# an ambulance for either is the bot not reading the line at all.
NOT_A_BREATHER = (
    r"\b(?:app|apps|website|server|network|wifi|router|phone|laptop|computer|pc|telly|tv|car|"
    r"cars|van|bike|motorbike|engine|boiler|radiator|pump|machine|washer|hoover|vacuum|pipe|"
    r"fan|heater|fridge|freezer|oven|projector|console)\b",
)
# A pet choking, eating something poisonous or being hurt is the vet's job, not a human ambulance.
# A pet is "not responding" to its recall, a treat, its dinner: those are not a collapse.
PET_RESPOND_SENSE = (r"(?:(?:his|her|its|their|the|my|our)\s+)?(?:name|treats?|food|dinner|tea|"
                     r"recall|call|toys?|lead|whistle|clicker|catnip|nip|commands?|laser|ball|"
                     r"kibble|chews?)\b")
# "unresponsive to her new food" is how a cat treats a bowl, and "not responding to her name" is a
# recall problem; "unresponsive after the walk" and "unresponsive and cold" are the vet's job tonight.
PET_UNRESPONSIVE = (r"\bunresponsive\b(?!\s*(?:to\s+(?:(?:his|her|its|their|my|our|the|a|an)\b|"
                    + PET_RESPOND_SENSE + r")|when\s+(?:i|we|you)\b))")
# A pet that cannot be woken is tonight's call, whether the pet is named before or after the verb.
PET_PET_NAMES = (r"dogs?|cats?|pupp(?:y|ies)|kittens?|pups?|pets?|parrots?|hamsters?|rabbits?|"
                 r"bunn(?:y|ies)|horses?|pon(?:y|ies)|budgies?|guinea\s+pigs?|tortoises?|ferrets?|"
                 r"gerbils?")
PET_WAKE = (r"\b(?:won'?t|wont|can'?t|cannot|unable\s+to|isn'?t|is\s+not|not)\s+wak(?:e|ing)\s+"
            r"(?:up\s+)?(?:my|our|the|his|her)\s+(?:" + PET_PET_NAMES + r")\b"
            # "the cat is not waking me up" is a bedtime complaint, not a pet that will not wake.
            r"(?!\s*(?:me|us|you|him|her|them)\b)")
PET_HARM = (
    r"\b(?:" + PET_PET_NAMES + r")\b"
    r".{0,60}\b(?:chok\w*|swallow\w*|ate|eaten|eats|lick\w*|chew\w*|bit|bitten|gasp\w*|"
    r"drank|drunk|poison\w*|bleeding|hurt|fell|sick|breathing|breath\w*|limp\w*|paws?|hit\s+by|"
    r"ran\s+over|"
    r"collapse\w*|unconscious|" + PET_UNRESPONSIVE + r"|(?:stopped|not|isn'?t)\s+eating|trouble\s+breathing|"
    r"(?:won'?t|wont|can'?t|cannot|unable\s+to|isn'?t|is\s+not|not)\s+wak\w*"
    r"(?!\s+(?:me|us|you|him|them)\b)|\b(?:be\s+)?woken\b|"
    r"(?:not|isn'?t|stopped|won'?t|wont)\s+respond\w*(?!\s+(?:to|for)\s+(?:"
    + PET_RESPOND_SENSE + r"))|breathing\s+(?:funny|oddly|strangely|weirdly|noisily|"
    r"with\s+a\s+(?:rasp|rattle))|(?:hasn'?t|has\s+not|not|isn'?t)\s+mov\w*|fitting(?!\s+in)|"
    r"(?:having|had|has|in)\s+(?:a\s+)?fits?|went\s+floppy|flopp\w*|"
    r"won'?t\s+wake|wont\s+wake|"
    r"seizure\w*|not\s+moving)\b",
)
# The pet is the one with the symptom: "my dog has chest pains", "the dog has chest pains and is
# panting". A human named in the same line still counts ("my dog knocked my son over"), so this only
# quiets a line where the animal owns the trouble.
PET_OWN = (
    r"\b(?:my|our|the|his|her|their|a|this)\s+(?:dog|dogs|cat|cats|puppy|puppies|kitten|kittens|"
    r"pup|pet|parrot|budgie|hamster|rabbit|bunny|horse|pony|guinea\s+pig|tortoise|ferret|gerbil|"
    r"rat|lizard|snake|hen|chicken)\b",
)
# A person of the speaker's who is going to die: "my nan is going to die" is anticipatory grief.
# The future tense is the point - "my dad is dying" already reaches the loss lines by its own route.
OTHER_DYING = (
    r"\b(?:my|our|her|his|their)\s+" + PERSON + r"\b[^.?!]{0,20}\b(?:going\s+to|gonna|will|"
    r"about\s+to|soon\s+to)\s+(?:die|pass\s+away)\b",
)
# A body verb with the animal as its own subject is the vet's question. "my cat is scratching
# himself raw" and "my dog is scratching himself raw" were answered "Don't leave them alone, and ask
# them directly whether they are thinking about suicide" - the self-harm arms read "my <any noun>"
# as a person, and the habit arm names nobody at all. Only the animals with a skin entry in
# `bot/knowledge/pets.py` are here, because standing the card down for a goldfish only buys a shrug.
PET_SKIN_PET = (
    r"\b(?:my|our|the|his|her|their)\s+(?:dog|dogs|cat|cats|puppy|puppies|kitten|kittens|rabbit|"
    r"rabbits|bunny|bunnies|hamster|hamsters|guinea\s+pig|guinea\s+pigs)\b",
)
PET_HURTING_ITSELF = (
    PET_SKIN_PET[0] + r"[^.?!]{0,30}?\b(?:scratch\w*|itch\w*|bit(?:e|es|ing|ten)?|chew\w*|"
    r"lick\w*|gnaw\w*|rub(?:s|bed|bing)?|nip(?:s|ped|ping)?)\b[^.?!]{0,26}"
    r"\b(?:him|her|it)sel(?:f|ves|vesd)?\b",
)
# A past line that says it is still going is an emergency now.
PET_NOW = (
    r"\bstill\b", r"\bright\s+now\b", r"\bcan'?t\s+breathe\b", r"\bnot\s+breathing\b",
    r"\bchoking\b",
)
# A pet that landed on its feet is fine, whatever it fell off.
PET_FINE = (
    r"\b(?:seems?|is|was|looks?)\s+(?:fine|ok|okay|alright)\b", r"\blanded\s+on\s+(?:his|her|its)\b",
    r"\bjumped\s+back\s+up\b", r"\bnothing\s+(?:wrong|broken)\b",
)
# A nicked paw is a vet appointment, not a night call.
PET_MILD = (
    r"\b(?:a\s+bit|a\s+little|slightly|small|tiny|little)\b.{0,25}\b(?:bleed\w*|blood|cut|"
    r"scratch\w*|sore|nick\w*)\b",
    r"\b(?:bleed\w*|cut|scratch\w*|nick\w*)\b.{0,15}\b(?:a\s+bit|a\s+little|slightly)\b",
)
# A pet that gasps for air is the vet's, the same as the person gasping is the ambulance's. One
# family answers both ends of it: `my cat woke up gasping` was "Noted: your cat woke up gasping"
# and `my puppy keeps gasping` a shrug, while `my dog is gasping for air` got the human 999 card.
# The gasp alone is not enough - a dog puffing after a run or gasping for its water is a dog doing
# dog things - so PET_GASP_FINE names what explains it, and nothing red may be in the line.
PET_GASP = (r"\bgasp\w*",)
# "My dog is a gasper" is what a noisy breather is called, not a night at the vet.
PET_GASP_NOUN = (r"\bgasp(?:er|ers|y)\b",)
# A gasp that goes on, or comes back, is not explained by the thing it was beside: "the dog keeps
# gasping when it lies down" is a dog in trouble, whatever the clause says.
PET_GASP_ONGOING = (
    r"\bkeep\w*\b", r"\bstill\b", r"\bagain\b", r"\bfor\s+(?:air|breath)\b",
)
# A dog that snores, snorts or runs in its sleep is fine, and a dog that gasps in its sleep is not:
# a gasp is a struggle for air however still the animal is, so the sleep word only stands the card
# down when the line also names the noise the sleep makes. "let him sleep it off" was the answer to
# `my dog is gasping in his sleep`, which is the one line of the set that must not get it.
PET_GASP_SLEEP = (
    r"\b(?:sleeps?|sleeping|asleep|naps?|napping|dozes?|dozing|dreams?|dreaming|dreamt)\b",
)
PET_GASP_SLEEP_FINE = (
    r"\b(?:snor\w*|snort\w*|snuffl\w*|pant\w*|dream\w*|twitch\w*|whin\w*|"
    r"sleep[\s-]?talk\w*|sleep[\s-]?walk\w*)\b",
)
# A pet whose gums have changed colour has an answer of its own, and it is the better one: press
# the gum and count the seconds. The pet table writes it, so the gasp does not take the line over.
PET_GUMS_TOLD = (r"\b(?:blue|pale|white|grey|gray|bright\s+red)\b",)
# The same report without the word gasp: "my dog is breathing funny" is a vet's question.
PET_BREATH_ODD = (
    r"\bbreath\w*\s+(?:funny|odd|oddly|strange|strangely|weird|weirdly|noisily|loudly|"
    r"differently)\b",
)
# Something eaten or caught in the throat has its own answer, so the gasp does not take it over.
PET_EATEN_THING = (
    r"\bchok\w*", r"\b(?:ate|eaten|eats|swallow\w*|poison\w*|drank|drunk|lick\w*|chew\w*)\b",
)
TOOTH_CHIPPED_FINE = (
    r"\bmilk\s+tooth\b", r"\bbaby\s+tooth\b", r"\bloose\s+tooth\b", r"\btoothache\b",
    r"\b(?:last|this)\s+(?:year|month|week)\b", r"\byears?\s+ago\b", r"\bwobbly\b",
)
TOOTH_CHILD = (r"\b(?:son|daughter|kid|child|children|baby|toddler|girl|boy|she|he|his|her)\b",)
TOOTH_KNOCK = (r"\b(?:knocked|broke|busted|smashed|snapped)\b",)

# A bang that is over, on purpose, or somebody else's: "i hit my head on the door frame last week".
# A fall and then confusion, with no head mentioned, is still the same call: in an older person a
# knock is often not remembered, and "confused about the recipe" is not what this means.
HEAD_FALL = (
    r"\b(?:fell|fallen|fall|falls|collapsed|went\s+down|slipped|tripped)\b",
)
# The confusion that is a sign is the disorientation, not the question: "hes confused about his
# pills" is the pills and "i was confused why the umpire gave it" is being puzzled, while
# "confused about where he is" and "confused about who i am" are the head injury (azure-trout).
CONFUSED_SIGN = (
    r"confus(?:ed|ion)\b(?!\s+(?:why|what|whether|if)\b)"
    r"(?!\s+(?:about|by|at|as\s+to)\s+(?!where\b|who\b|whereabouts\b))"
)
HEAD_FALL_SIGN = (
    # "my dad fell and he isnt making sense": the person, the fall, then the sign, in the words
    # people use for it ("isnt making sense" is as common as "not making sense").
    # "hes" and "shes" are how most people type it, and they are not \bhe\b, so they are named
    # here: "my dad fell and hes not making sense" was reaching the bruising question.
    r"\b(?:he|she|they|hes|shes|theyre|dad|mum|grandad|grandma|nan|gran|husband|wife|father|mother)\b.{0,40}"
    # "not making any sense" is as common as "not making sense", and "he doesnt know where he is"
    # is the same sign said plainly.
    r"\b(?:" + CONFUSED_SIGN + r"|drowsy|sleepy|"
    r"(?:isn'?t|isnt|not|wasn'?t|ain'?t)\s+making\s+(?:any\s+)?sense|"
    r"(?:doesn'?t|doesnt|didn'?t|didnt)\s+know\s+(?:where\s+(?:he|she|they)\s+(?:is|are|was|were)|"
    r"who\s+(?:i|we|he|she|they)\s+(?:am|are|is|was))\b|acting\s+(?:strange|odd|weird|differently)|"
    # "my dad had a fall and isnt himself" is the same sign: a person who is not themselves after
    # a fall is the confusion card, not the bruising question.
    r"(?:isn'?t|isnt|not|wasn'?t|ain'?t|hasn'?t|hadn'?t)\s+(?:been\s+)?(?:him|her|them)sel(?:f|ves)|"
    r"talking\s+(?:rubbish|nonsense|gibberish)|"
    r"can'?t\s+wake|knocked\s+out|unconscious)\b",
    r"\bconfused\b(?!\s+about)\b.{0,20}\b(?:after|since)\b.{0,20}\b(?:fell|fall|bang|knock)\b",
    # ...and the same about yourself: "ive had a few falls and i feel confused" is the same call as
    # "my dad fell and hes confused", and it was reaching the paragraph about balance and eyesight.
    r"\b(?:i|im|i'?m|ive|i'?ve)\b.{0,45}\b" + CONFUSED_SIGN + r"",
)
# A leg that keeps falling asleep is not a fall, and "fell asleep" was never one. The pattern arms
# below borrow the same verb, so the sleep is fenced off once and every arm reads it.
FALL_ASLEEP = (
    r"\bf(?:ell|alls?|alling)\s+asleep\b",
)
# A price or a temperature falls too, and the thing itself has to be in front of the verb for that
# reading: "the price keeps falling and i feel confused" is a money line, while "my dad fell and he
# has a temperature and is confused" is the bang card the fever makes worse.
# The confusion has to be what is happening now: "my dad keeps tripping over the rug and he was
# confused after his stroke" is his baseline, named with the thing that caused it, and the falls
# review is the better answer for that line.
CONFUSION_NAMED_CAUSE = (
    r"\b(?:was|were|is|been)\s+confused\s+(?:after|since|following)\s+"
    r"(?:his|her|their|the)\s+(?:stroke|surgery|operation|anaesthetic|chemo|accident)\b",
)
FALL_THING = (
    r"\b(?:prices?|markets?|shares?|stocks?|temperature|rain|snow|sales|rates?|figures?|numbers?|"
    r"pounds?|euros?|dollars?|hair|wigs?|leaves)\s+(?:keeps?\s+|kept\s+|is\s+|are\s+|was\s+|were\s+|"
    r"had\s+|has\s+|have\s+)?(?:falling|fell|falls?|dropping|dropped)\b",
)
# Already being looked after: a head injury in hospital, or one a doctor has seen, is not a call to
# make, and the advice that fits is about the visit, not the first minutes.
HEAD_SEEN = (
    r"\b(?:in|at)\s+(?:the\s+)?(?:hospital|a&e|ae|er|casualty)\b", r"\bbeen\s+checked\b",
    r"\b(?:doctor|nurse|paramedic|ambulance)\s+(?:has\s+)?(?:seen|checked|said|looked)\b",
    r"\bwalk-in\s+(?:centre|clinic)\b", r"\bthey\s+(?:kept|are\s+keeping)\b.{0,15}\bin\b",
)
HEAD_PAST = (r"\b(?:last|this)\s+(?:year|month|week|night)\b", r"\byears?\s+ago\b",
             r"\bages\s+ago\b", r"\bused\s+to\b", r"\bwhen\s+i\s+was\s+(?:a\s+)?(?:kid|child|little)\b")
# `respond(?:s|ing|ed)?` rather than `respond\w*`: a `\w*` can stop one letter short, and then
# the stand-down is asked about the wrong place in the line, so "stopped responding to sit" still
# came out as the vet card (copper-string's second blocker on #795).
PET_RESPOND = r"\b(?:not|isn'?t|stopped|won'?t|wont)\s+respond(?:s|ing|ed)?(?![a-z])" + PET_RESPOND_AT
PET_COLLAPSE = (
    PET_UNRESPONSIVE,
    PET_RESPOND,
    r"\b(?:not|isn'?t|hasn'?t|has\s+not)\s+mov\w*|\bnot\s+moving\b",
    # A pet that *is* limp has gone floppy and is tonight's call; that is not the same answer as
    # something it swallowed, because there is no wrapper to bring.
    r"\b(?:is|are|was|were|went|gone|being|looks?|seems?)\s+(?:a\s+bit\s+|really\s+|very\s+|"
    r"totally\s+|completely\s+)?limp\b",
)
# The behaviour patterns above are the ones a fine word cancels; a swallowed battery is not.
PET_BEHAVIOUR = (
    PET_UNRESPONSIVE,
    PET_RESPOND,
    r"\b(?:not|isn'?t|hasn'?t|has\s+not|not\s+moving)\b\s*\w*\bmov\w*|\bnot\s+moving\b",
)
# The fit forms people type, and the bare state: "is having a fit", "went floppy".
PET_FIT = (
    r"\b(?:having|had|has|in)\s+(?:a\s+)?fits?\b", r"\bfitting(?!\s+in)\b", r"\bseizure\b",
    r"\bflopp\w*\b", r"\bnot\s+moving\b",
)
PET_CRISIS = (
    r"\bchok\w*\b", r"\b(?:can'?t|cannot|unable\s+to|struggling\s+to|not)\s+breathe?\b",
    r"\b(?:isn'?t|is\s+not|not|stopped)\s+breathing\b", r"\btrouble\s+breathing\b",
    r"\bshort(?:ness)?\s+of\s+breath\b",
    # "my dog is gasping for breath" was reaching the tooth-brushing answer: a pet fighting for
    # air is the same vet-now case as one that cannot breathe.
    r"\bgasp\w*\s+for\s+(?:air|breath|it)\b",
    # "My dog is breathing funny" is the same report in the words people use, and it was a shrug
    # while "breathing oddly" got the toothbrushing answer.
    r"\bbreath\w*\s+(?:funny|odd|oddly|strange|strangely|weird|weirdly|noisily|loudly|"
    r"differently)\b",
    r"\bbleeding\b", r"\bhit\s+by\s+(?:a\s+)?(?:car|bike|van|bus|train|lorry|truck)\b",
    r"\brun\s+over\b", r"\b(?:car|van|bus|bike|lorry|truck)\s+(?:clipped|knocked|caught|hit|struck)\b",
    r"\bseizure\b", r"\bfitting\b", r"\b(?:having|had|has|in)\s+(?:a\s+)?fits?\b",
    r"\b(?:went|gone|is|was|being)\s+floppy\b", r"\bunconscious\b", r"\b(?:has\s+)?collapsed\b",
    # A pet that *is* limp is the vet's tonight; "has a limp" and "is limping" are a leg to rest.
    r"\b(?:is|are|was|were|went|gone|being|looks?|seems?)\s+(?:a\s+bit\s+|really\s+|very\s+|"
    r"totally\s+|completely\s+)?limp\b",
    r"\b(?:not|isn'?t)\s+moving\b", PET_UNRESPONSIVE,
    r"\b(?:won'?t|wont|can'?t|cannot|unable\s+to|isn'?t|not)\s+wak\w*(?!\s+(?:me|us|you|him|them)\b)",
    r"\b(?:be\s+)?woken\b",
    PET_RESPOND,
    r"\b(?:hasn'?t|has\s+not|not)\s+mov\w*\b",
    # ...and a pet that fell from a height or cannot be woken is not a "keep an eye on it" either.
    r"\b(?:fell|fallen|jumped)\s+(?:off|from|down)\b", r"\bwon'?t\s+wake\b", r"\bwont\s+wake\b",
    # Eating is only an emergency when the thing eaten is the dangerous part. Chocolate, grapes,
    # raisins, onions and garlic have their own answers in the knowledge base, which name the
    # dose and say what to look for, so they are not in this list: "my dog ate grapes" got the
    # generic script about a pet that cannot breathe while "my dog ate a mince pie" - the same
    # raisins - got the kidney answer, and the two lines were the same accident.
    r"\b(?:ate|eaten|eats|drank|drunk|swallow\w*|licked|lick\w*|chew\w*|bit|bitten)\b"
    r".{0,35}\b(?:antifreeze|poison\w*|"
    r"xylitol|lil(?:y|ies)|ibuprofen|paracetamol|"
    r"painkillers?|rat\s+bait|slug\s+pellets?|bleach|a\s+bone|a\s+sock|a\s+stick|"
    r"toilet\s+cleaner|oven\s+cleaner|washing\s+powder|nail\s+varnish|de-?icer|screen\s?wash|"
    r"drain\s+cleaner|fabric\s+softener|dishwasher\s+salt|"
    r"something\s+(?:bad|poisonous|sharp)|batter(?:y|ies)|coins?|magnet\w*|string|tinsel|"
    r"a\s+toy|plastic|a\s+stone|a\s+pebble)\b",
    # A rabbit or a guinea pig that stops eating is an emergency in a way a fussy dog is not.
    r"\b(?:rabbits?|bunn(?:y|ies)|guinea\s+pigs?)\b.{0,30}\b(?:stopped|not|isn'?t|hasn'?t)\s+"
    r"(?:eating|eaten)\b",
)
# A choking that happens again and again is the weaning question or the speech one, not an
# incident: "my baby used to choke on lumps" wants the lumps, not the cough.
CHOKE_HABIT = (
    r"\b(?:used\s+to|always|never|often|keeps?|kept|every\s+time|when\s+(?:he|she|they)\s+"
    r"(?:was|were)\s+(?:a\s+)?(?:baby|little|small|young|kid|child))\s+chok",
)
# The person has told you it is over: "hes short of breath but hes fine now", "my mum is short of
# breath and it passed". The present tense is what a copula adds, so it needs this to stay honest
# when the same line also says the symptom has gone. A red flag anywhere still wins.
BREATH_OVER = (
    r"\b(?:fine|ok|okay|alright|better)\s+(?:now|again)\b",
    r"\b(?:it|that)\s+(?:has\s+)?passed\b", r"\bpassed\s+now\b", r"\bwent\s+away\b",
    r"\b(?:it|that)\s+(?:is\s+|has\s+)?(?:over|gone)\b",
)
NIGHT_OCCASION = (r"(?:last\s+night|overnight|in\s+the\s+night|at\s+night|during\s+the\s+night|"
                  r"middle\s+of\s+the\s+night|in\s+bed|in\s+my\s+sleep|in\s+his\s+sleep|"
                  r"in\s+her\s+sleep)")
NIGHT_BREATH = (
    r"\b" + NIGHT_OCCASION + r"\b[^.?!]{0,60}\b(?:breath\w*|gasp\w*)\b",
    r"\b(?:breath\w*|gasp\w*)\b[^.?!]{0,60}\b" + NIGHT_OCCASION + r"\b",
    # The habitual present: "i wake up short of breath", "i keep waking up gasping". This one keeps
    # any subject, because a child who keeps doing it is the sleep apnoea question too.
    r"\b(?:wake|wakes|waking)\s+up\b[^.?!]{0,40}\b(?:breath\w*|gasp\w*)\b",
    # The past tense is the same illness reported in the words people actually use - `i woke up
    # gasping` was a shrug ("I'm here if you want to dig into any of that") for months. It is the
    # speaker's own night, though: a child or a parent who woke up gasping is the 999, and a gasp
    # "for breath" is heart failure as much as apnoea, so both stand this arm down.
    NIGHT_BREATH_PAST[0],
    r"\b(?:breath\w*|gasp\w*)\b[^.?!]{0,30}\b(?:when|whenever)\s+i\s+(?:wake|wakes)\b",
    # Lying flat and having to be propped up are the same question about the heart.
    r"\b(?:lying|lie|lies|lay|laid)\s+(?:flat|down)\b[^.?!]{0,40}\b(?:breath\w*|gasp\w*)\b",
    r"\b(?:breath\w*|gasp\w*)\b[^.?!]{0,40}\b(?:lying|lie|lies)\s+(?:flat|down)\b",
    r"\bpropped\s+up\b[^.?!]{0,40}\b(?:breath\w*|gasp\w*)\b",
    r"\b(?:breath\w*|gasp\w*)\b[^.?!]{0,40}\bpropped\s+up\b",
    r"\bsleep(?:ing)?\s+(?:sitting\s+up|upright|propped)\b",
)
# A gasp that comes with a nightmare is the nightmare: "i woke up gasping after a bad dream" is
# not a heart to have checked, and the night question below would give it the same-day card.
NIGHT_BREATH_DREAM = (
    r"\b(?:nightmare|nightmares|bad\s+dream|bad\s+dreams|dream|dreams|dreaming|dreamt|dreamed)\b",
)
# A small child who stops breathing in the night is not the adult apnoea question: the parent is
# awake and the risk is the child's, so the answer has to be about the child.
NIGHT_BREATH_CHILD = (
    r"\b(?:my|our|his|her|their|the)\s+(?:baby|babies|son|sons|daughter|daughters|child|"
    r"children|kid|kids|toddler|toddlers|infant|infants|boy|girl|newborn|little\s+one)s?\b",
)
BREATH_STILL_RED = (
    r"\b(?:can'?t|cannot|can\s+not|unable\s+to)\s+(?:breathe|breath)\b",
    r"\b(?:stopped\s+breathing|isn'?t\s+breathing|not\s+breathing|gasping)\b",
)
CHOKE_NOW = (
    r"\b(?:still|right\s+now|now|can'?t\s+breathe|cannot\s+breathe|struggling|gasping|coughing|"
    r"went\s+blue|turned\s+blue|in\s+a\s+lot\s+of\s+pain|hurts)\b",
)
# A person who is choking right now needs the hand movements, not a phone number: five sharp back
# blows between the shoulder blades, then five sharp abdominal thrusts, and the five-and-five again
# until it clears or the ambulance takes over. "choking me" is the abuse case and "choked up" is
# the feeling, so neither is the airway.
CHOKE_HELP = (
    r"\bchok(?:ing|ed|es)\b(?!\s+(?:me|up)\b)", r"\bchocking\b",
)
# A baby under one is the two-finger job: back blows face down, then chest thrusts, never
# abdominal thrusts. Months old, or the word for a baby, is what makes it one.
CHOKE_BABY = (
    r"\b(?:baby|babies|infant|newborn|new\s?born|babe\s+in\s+arms)\b",
    r"\b(?:under\s+(?:one|1|a\s+year)|(?:\d|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven)\s+months?\s+old)\b",
)
# A small child who has gone floppy or limp, or who is too sleepy to feed, is the classic
# sepsis/meningitis scene and people say it as a description, not as an emergency: "my toddler is
# very sleepy and floppy". It is said of hats and teddy rabbits too, hence FLOPPY_THING.
# A limp is a walk as well as a state, so the child word only counts with a limp that happened to
# them: "my son has a limp after falling off his bike" is how he walks.
LIMP_STATE = r"(?:gone|is|was|went|being|felt|feels?|all)\s+limp\b"
FLOPPY_CHILD = (
    r"\b(?:baby|babies|toddler|newborn|infant|child|kid|son|daughter|boy|girl|she|he|they|"
    r"shes|hes|theyre|my\s+" + PERSON + r")\b"
    r".{0,40}\b(?:flopp\w*|life-?less)\b",
    r"\b(?:baby|babies|toddler|newborn|infant|child|kid|son|daughter|boy|girl|she|he|they|"
    r"shes|hes|theyre|my\s+" + PERSON + r")\b"
    r".{0,40}" + LIMP_STATE,
    # "unresponsive" is a grown-up's word too, so it needs a child in the line (#305 owns the
    # grown-up lines), and "unresponsive to her new milk" or "unresponsive when hes told off" is
    # not a collapse.
    r"\b(?:baby|babies|toddler|newborn|infant|child|kid|son|daughter|boy|girl)\b"
    r".{0,40}\bunresponsive\b(?!\s*(?:to|when|whenever|if|because|as|after|with)\b)",
    # Except a feed: "my baby is unresponsive to her milk" is a parent saying the baby will not
    # wake after a bottle, which is the same red flag as "my baby is unresponsive" and the same
    # one as "not responding to her feed". A message after `to` stays out ("unresponsive to my
    # texts" is a phone), and a feed is never something a person is texting about.
    r"\b(?:baby|babies|toddler|newborn|infant|child|kid|son|daughter|boy|girl)\b"
    r".{0,40}\bunresponsive\b\s*(?:to|after|during|at|following)\s+(?:the|a|an|her|his|my|"
    r"their|this|that|some)?\s*(?:(?:new|old)\s+)?(?:milk|formula|feeds?|feeding|bottle|breast|"
    r"solids|weaning)\b",
    r"\b(?:flopp\w*|life-?less)\b.{0,40}\b(?:baby|babies|toddler|newborn|infant|child|kid|"
    r"son|daughter|boy|girl)\b",
    # Too sleepy to feed, or you cannot rouse them for a feed, is the same red flag said another way.
    r"\b(?:baby|babies|toddler|newborn|infant)\b.{0,40}\b(?:too\s+sleepy|very\s+sleepy|won'?t\s+wake|"
    r"wont\s+wake|hard\s+to\s+wake|not\s+waking|can'?t\s+wake|drowsy|sleepy)\b.{0,40}"
    r"\b(?:feed\w*|eating|eaten|drink\w*|napp(?:y|ies)|wet\s+nappy|wake\s+for\s+a\s+feed)\b",
)
# Tightness by itself is not a heart-attack sign: it is what makes chest pain on effort the
# "get it checked this week" reply rather than the ambulance. The other red flags still are.
EXERTION_CHEST = (r"\b(?:tight\w*|pressure|heavy|heaviness|ache|aching)\b",)
_CHEST_OTHER_RED = (
    r"\b(?:arm|jaw|shoulder|neck|sweat\w*|clammy|grey|gray|pale|numb|numbness|tingl\w*|crushing|"
    r"squeez\w*|can't\s+breathe|breathless\w*|short(?:ness)?\s+of\s+breath|faint\w*|"
    r"pass(?:ed)?\s+out|sick|vomit\w*|dizzy)\b",
)


# A third person cutting or burning himself is a parent or friend saying self-harm, and it is not
# something to wash and cover: "my son is cutting himself" was getting the first-aid line for a
# cut, and "my son cuts himself" a shrug. A cause or an activity on the line - "on a tin", "at
# netball", "shaving" - keeps the accident the accident it is.
YOUNG_PERSON = (r"(?:teen|teenager|adolescent|child|kid|toddler|baby|pre-?schooler|schoolkid|"
                r"schoolboy|schoolgirl|boy|girl|lad|lass|youngster|nephew|niece|"
                r"cousin|grandson|granda?ughter|stepson|stepdaughter|" + PERSON + r")")
# "hes"/"shes" are how most people type the third person, and `\bhe\b` cannot see them:
# "hes been cutting himself on purpose" was answered with the cut first aid, while "he has been
# cutting himself on purpose" got the crisis card. The spelling is added to the actor rather
# than folded into the line, because the rest of the module reads the joined pronoun on its
# own terms (JoinedPronounCollapseTest) and a blanket fold moves those lines underneath it.
OTHER_SUBJECT = (r"(?:he|hes|she|shes|they|(?:my|our|the)\s+(?:\d{1,2}[\s-]?year[\s-]?old|" + YOUNG_PERSON + r"))")
SELF_HARM_BY_OTHER = (
    r"\b" + OTHER_SUBJECT + r"\b.{0,25}"
    r"\b(?:cuts?|cutting|burns?|burning|hurts?|hurting|harms?|harming|scratches?|scratching|"
    r"starves?|starving)\s+(?:him|her|them)sel(?:f|ves)\b",
    r"\b" + OTHER_SUBJECT + r"\b.{0,25}"
    r"\b(?:is|are|was|were|keeps?|kept|been)\s+(?:cutting|burning|hurting|harming|scratching)\b"
    r".{0,15}\b(?:again|himself|herself|themselves|at\s+night|every\s+day)\b",
    r"\b(?:my|our|the)\s+(?:\d{1,2}[\s-]?year[\s-]?old|" + YOUNG_PERSON + r")\b.{0,20}"
    r"\b(?:cuts?|cutting|burns?|burning|scratches?|scratching)\b.{0,10}\b(?:again|a\s+lot)\b",
    # The act talked about rather than done: "my friend keeps talking about killing herself",
    # "my mate keeps saying he wants to top himself". A friend saying it is the same worry as a
    # friend doing it, and main answered these with "Thanks for telling me".
    r"\b" + OTHER_SUBJECT + r"\b.{0,30}"
    r"\b(?:talks?|talking|talked|says?|saying|said|mentions?|mentioning|mentioned|jokes?|joking|"
    r"threatens?|threatening|keeps?|kept|sent|texted|messaged|wrote|posted|shared)\b"
    r".{0,20}\b(?:about|of|that)\b.{0,20}"
    r"\b(?:killing|hurting|cutting|harming|topping|ending|taking)\b.{0,15}"
    # "it" is how people say the wish without naming it: "he keeps talking about ending it",
    # "my husband is talking about ending it". Main gave the first "I'm listening" and the second
    # the *how to close a conversation* line. The gate below already keeps "ending it with his
    # girlfriend" - the marriage - out of the card, and the own-life spelling is here too.
    r"\b(?:(?:him|her|them)sel(?:f|ves)|(?:his|her|their)\s+(?:own\s+)?life|"
    r"it(?:\s+all)?(?!\s+with\s+(?:him|her|them|us|my|his|their|the)))\b",
    # The wish said as a feeling or a want, in the third person: "my mum feels like ending it" is
    # her wish, not the speaker's, and main answered it with the user's own crisis card. A friend
    # saying it is the same worry as a friend doing it.
    r"\b" + OTHER_SUBJECT + r"\b[^.?!]{0,25}"
    r"\b(?:feels?|felt|feeling)\s+(?:like\s+)?(?:ending\s+(?:it(?!\s+with\s+(?:him|her|them|us|my|"
    r"his|their|the))|(?:his|her|their)\s+life)|killing\s+(?:him|her|them)sel(?:f|ves)|"
    r"dying(?!\s+(?:of|laughing|with\s+laughter|(?:my|his|her|their)\s+hair)))\b",
    r"\b" + OTHER_SUBJECT + r"\b[^.?!]{0,25}"
    r"\b(?:wants?|wanted|wanting|plans?|planning)\s+to\s+(?:die(?!\s+(?:of|laughing|with\s+"
    r"laughter|(?:my|his|her|their)\s+hair))|end\s+(?:it(?!\s+with\s+(?:him|her|them|us|my|his|their|the))|"
    r"(?:his|her|their)\s+life)|kill\s+(?:him|her|them)sel(?:f|ves))\b",
    # ...and the same said with the noun: "my sister keeps talking about suicide" was answered
    # with the *user's* crisis card, which is the wrong person's name on the help.
    r"\b" + OTHER_SUBJECT + r"\b.{0,30}"
    r"\b(?:talks?|talking|talked|says?|saying|said|mentions?|mentioning|mentioned|jokes?|joking|"
    r"threatens?|threatening|keeps?|kept|sent|texted|messaged|wrote|posted|shared)\b"
    r".{0,20}(?:(?:about|of|that)\b.{0,20})?(?:suicide|suicidal)\b",
    # The report with no "about" in it: "he said he was ending it all", "she told me she was
    # going to end it", "my son keeps saying he is taking his own life". Main answered these with
    # "Thanks for telling me" while `he's been cutting himself` got the card, so the shape was a
    # third person *saying* the wish (steward-wide-shield, 81137).
    r"\b" + OTHER_SUBJECT + r"\b.{0,30}"
    r"\b(?:said|says|saying|told\s+me|tells\s+me|keeps\s+saying|kept\s+saying|texted|"
    r"messaged|wrote|mention(?:s|ed|ing)?|posted)\b.{0,25}"
    r"\b(?:end(?:ing)?\s+it(?:\s+all)?(?!\s+with\s+(?:him|her|them|us|my|his|their|the))|"
    r"tak(?:e|es|ing|en)\s+(?:his|her|their)\s+(?:own\s+)?life|"
    r"kill(?:ing)?\s+(?:him|her|them)sel(?:f|ves)|"
    # "topping himself" is how a lot of people say it, and the shout noun is here too.
    r"top(?:s|ping|ped)?\s+(?:him|her|them)sel(?:f|ves)|off(?:s|ed|ing)?\s+(?:him|her|them)sel(?:f|ves)|"
    r"suicid\w+)\b",
)
SELF_HARM_BY_OTHER = (*SELF_HARM_BY_OTHER,
    r"\b" + OTHER_SUBJECT + r"\b[^.?!]{0,25}\bself[-\s]?harm(?:s|ing|ed)?\b",
    # A relative's wish said as a wish: "my son says he wishes he was dead" was answered with the
    # loss reply ("That's such sad news"), which is the wrong grief for somebody still here.
    r"\b" + OTHER_SUBJECT + r"\b[^.?!]{0,25}\bwish(?:es)?\s+(?:he|she|they)\s+"
    r"(?:was|were|is|are)\s+(?:dead|gone)\b",
    # A relative's plan with a means, or with a verb a blade does not have. `SELF_HARM_BY_OTHER`
    # above reads cutting, burning, hurting and starving, so "my brother wants to shoot himself"
    # was filed as news ("Noted: your brother wants to shoot himself.") and "my son wants to
    # throw himself under a train" the same, both said as plainly as the cutting lines the arm
    # does read. The person words are the ones the arm already knows.
    r"\b" + OTHER_SUBJECT + r"\b[^.?!]{0,30}\b(?:shoot|shooting|hang|hanging|stab|stabbing|"
    r"poison|poisoning|drown|drowning|strangle|strangling|overdose|overdosing)\s+"
    r"(?:him|her|them)sel(?:f|ves)\b",
    r"\b" + OTHER_SUBJECT + r"\b[^.?!]{0,30}\b(?:throw|throwing|jump|jumping|step|stepping|"
    r"walk|walking)\s+(?:him|her|them)sel(?:f|ves)\s+"
    r"(?:in\s+front\s+of|under|onto|off)\s+(?:a|an|the)?\s*(?:train|trains|bus|buses|lorry|"
    r"truck|coach|traffic|platform|tracks?|rails?|bridge|roof|building|cliff|balcony|ledge)\b",
)
# A bare "hurt himself" is not the same sentence as "cut himself": it is a playground fall and it
# is a boy who means it, and the line does not say which. It is asked rather than answered with the
# crisis card, which is the wrong answer to the accidents and the wrong reassurance to the rest.
HURT_HIMSELF_BARE = (
    r"\b" + OTHER_SUBJECT + r"\b.{0,25}\b(?:hurt|hurts|hurting)\s+(?:him|her|them)sel(?:f|ves)\b",
)
# The framing that turns the same three words into a crisis: on purpose, again, when they are upset.
HURT_HIMSELF_MEANT = (
    r"\b(?:on\s+purpose|again|keeps?|kept|every\s+day|every\s+night|at\s+night|"
    r"when\s+(?:he|she|they)\b|because\b|upset|anxious|depressed|angry|wants?\s+to\s+die|"
    r"wish\w*\s+(?:he|she|they)|suicid\w*|kill|ended?\s+up\s+in|hospital|a\s+and\s+e|"
    r"a&e)\b",
)
# The thing that makes a reflexive harm verb a helping is the object being a portion: "a slice of",
# "a big slice", "a piece of cake", "a bit of bread", "some bread" are a plate. "a cross on her arm",
# "a word on her leg", "a smiley on her wrist", "a heart on my arm" are the act carved into skin, and
# a body part named in the same line is the act whatever the object follows it - which is the false
# negative this tuple had (friendly-kangaroo, review of #7418).
A_PORTION = (
    r"(?:slice|slices|piece|pieces|bit|bits|portion|portions|helping|helpings|serving|servings|"
    r"wedge|wedges|chunk|chunks|plate|plateful|bowl|bowlful|glass|cup|mug|half|hunk|knob|spoon|"
    r"spoonful|handful|bite)\b")
A_HARM_VERB_CUT = (
    r"\b(?:cuts?|cutting|cut|slices?|slicing|sliced|burns?|burning|burned|burnt|scratches?|"
    r"scratching|scratched|carves?|carving|carved|engraves?)\b")
ORDINARY_REFLEXIVE = (
    # The reflexive verb with an ordinary thing after it is the verb, not the act. "she cuts
    # herself a slice of cake", "he cuts himself a big slice", "she cuts herself some bread",
    # "he helps himself to the biscuits", "he pours himself a whisky", "she served herself a
    # large portion" were all answered with the card that asks whether someone is thinking of
    # suicide. What tells the two apart is the determiner and the object after it: a cut meant or
    # a cut done often has "again", "on purpose" or an instrument there, never a portion - while
    # "a lot", "a bit" and "a little" on their own are a small injury, not a helping.
    # The harm verbs, and only a portion after the determiner, one adjective allowed, so "a big
    # slice" is a plate and "a cross" or "a word" is not.
    r"\b(?:cuts?|cutting|slices?|slicing|burns?|burning|burned|burnt|starves?|starving|starved)\s+"
    r"(?:my\s*self|himself|herself|themselves)\s+"
    r"(?![^.?!]{0,24}\b(?:gash|wound|scar|cut|blade|razor|burn\s*mark|bruise)\b)"
    # ...and a cut that was meant says so after the plate: "he cuts himself a slice of cake on
    # purpose" is the act with a cake word in front of it (cream-eel, review of #7418).
    r"(?![^.?!]{0,40}\b(?:on\s+purpose|deliberately|on\s+purposely)\b)"
    # ...and the portion has to have something after it: "i cut myself a slice" on its own is
    # as likely the act as a cake, and base answered it with the card.
    r"(?:a|an|the|another|one|two|three|half)\s+(?:\w+\s+){0,1}" + A_PORTION
    + r"(?!\s*(?:[.?!,;]|$))",
    # ...and "she cuts herself some bread", where "some" carries the food itself.
    r"\b(?:cuts?|cutting|slices?|slicing|burns?|burning|starves?|starving)\s+"
    r"(?:my\s*self|himself|herself|themselves)\s+some\s+\w+",
    # Taking something is never a harm, whatever the object: "he helps himself to the biscuits",
    # "she treated herself to a new coat", "he poured himself a whisky", "he grabbed himself a
    # coffee". These verbs are in the tuple so a line with one of them and a wish still reads as
    # the wish through `_a_reason_it_was_not_meant`.
    r"\b(?:helps?|helped|helping|pours?|poured|pouring|serves?|served|serving|grabs?|grabbed|"
    r"grabbing|treats?|treated|treating|makes?|made|making)\s+"
    r"(?:my\s*self|himself|herself|themselves)\s+"
    r"(?:(?:a|an|the|some|another)\s+\w+|to\b)",
    # "he burns himself out at work" is the job, not a scald, but the stand-down does not fire on
    # it: with the card taken away the line reached a chat nod, and a woman run into the ground
    # should reach the work-and-stress card or nothing (clear-weasel, review of #7418). It stays
    # with the card it had until something in the deck answers the burnout.
    # "he starves himself all day then eats at night": the day after the pronoun is a diet. The
    # event is not: "shes starving herself for a wedding" then reached the wedding-and-hotel card,
    # which is worse than the card it left, so that line keeps its card until something answers
    # the diet (clear-weasel, review of #7418).
    # ...and the day is only a diet when the line comes back to eating: "he starves himself all day
    # then eats at night" is one meal a day, while "i starve myself until i faint" and "i starve
    # myself all week and then binge" are what it did to him, and both keep the card
    # (close-falcon, review of #7418). "shes starving herself for a wedding" keeps it too.
    r"\b(?:starves?|starving|starved)\s+(?:my\s*self|himself|herself|themselves)\s+"
    r"(?:all\s+day|all\s+week|for\s+days|until\b|then\b)[^.?!]{0,30}"
    r"\b(?:eats?|eating|ate|dinner|lunch|breakfast|meal)\b",
)


# The itch explains a line about scratching, and nothing else: "my son picks at his spots and cuts
# himself", "my son scratches at night and has a blade", "my son scratches at night and swallowed a
# packet of pills" are about the other thing in them, and an itch word must not stand the card down.
# The blade is read here and not in the lookalike table because a razor beside a lookalike is
# ordinary - "he cut himself shaving with a razor" - and that line is not one of these.
AN_ACT_BESIDE_THE_ITCH = (
    r"\b(?:cut|cuts|cutting|cut\s+himself|cut\s+herself|slit\w*|slashed|blade|razor|knife|"
    r"scalpel|stanley\s+knife|glass|broken\s+glass|burn\w*|scald\w*|burnt)\b",
    r"\b(?:pills?|tablets?|paracetamol|ibuprofen|overdose[ds]?|od|poison\w*|bleach|"
    r"kill\w*|die|dying|suicide|end\s+it|end\s+my\s+life|hang\w*|noose|rope)\b",
    r"\b(?:self[\s-]?harm\w*|hurting\s+himself|hurting\s+herself|hurting\s+themselves|"
    r"on\s+purpose)\b",
)


def _a_reason_it_was_not_meant(text):
    # ...and the plate, through the helper that reads the tears as well as the wish: the arms are
    # not in SELF_HARM_LOOKALIKE on their own, or "my daughter cuts herself a slice of cake but
    # she is depressed" would be stood down before anybody read the depression.
    # The itch is read on its own line of reasoning: it explains the scratching and not a blade
    # beside it, and the same wish fence applies to it.
    return ((_matches(SELF_HARM_LOOKALIKE, text) and not _matches(A_WISH_OR_TALK_OF_IT, text))
            or (_matches(AN_ITCH_LOOKALIKE, text)
                and not _matches(A_WISH_OR_TALK_OF_IT, text)
                and not _matches(AN_ACT_BESIDE_THE_ITCH, text))
            or _an_ordinary_helping(text))


# ...and the plate is not the whole line: "my daughter cut herself a slice of cake and cut her
# finger" is a knife that slipped while somebody was being helped, and the card that asks whether
# she is thinking about suicide is the wrong question about it (azure-trout, review of #7418). The
# injury has to be where a knife slips - a hand, a finger, blood - and not an arm or a wrist, which
# is where a cut is the act, so the carve lines keep their card.
A_REAL_INJURY = (
    r"\b(?:bleed\w*|blood|bloody|stitches?|gash\w*|deep\s+cut)\b",
    r"\b(?:cut|cuts|cutting|sliced|slices|slicing|nicked|nicks|grazed|caught)\b[^.?!]{0,20}?"
    r"\b(?:thumb|finger|fingers|hand|hands|palm|knuckle|knuckles|nail|fingertips?)\b",
)


# The plate as a shape of its own, without the arm's injury lookahead: a line that names the cut
# finger is exactly the one the arms above turn away, and it is still a plate of cake.
A_PLATE_SHAPE = (
    r"\b(?:cuts?|cutting|slices?|slicing|burns?|burning|burned|burnt)\s+"
    r"(?:my\s*self|himself|herself|themselves)\s+"
    r"(?:a|an|the|another|one|two|three|half)\s+(?:\w+\s+){0,1}" + A_PORTION,
    r"\b(?:cuts?|cutting|slices?|slicing|burns?|burning)\s+"
    r"(?:my\s*self|himself|herself|themselves)\s+some\s+\w+",
)


def _a_real_injury_beside_the_plate(text):
    """True when a helping and a cut hand are in the same line, so the first aid answers it."""
    return (_matches(A_REAL_INJURY, text)
            and _matches(A_PLATE_SHAPE, text)
            and not _matches(A_WISH_OR_TALK_OF_IT, text)
            and not _matches(DISTRESS_BESIDE_IT, text)
            # ...and only while the injury is a small one: a knife that slipped badly is the
            # ambulance answer, and the plaster row must not take "its bleeding a lot" off it.
            and not _matches(BLEEDING + CUT_NOT_STOPPING, text))


# A plate with the sign of a person being unwell after it is still the person: "i cut myself a slice
# of cake and i feel faint" is a faint, and main answered it with the crisis card. Standing the plate
# down without this left the line to the cake entry, so the sign is read before the plate is.
UNWELL_BESIDE_THE_PLATE = (
    r"\b(?:feel|feels|felt|feeling)\s+(?:faint|dizzy|light.?headed|sick|ill|weak|shaky|unwell|"
    r"nauseous|queasy)\b",
    r"\b(?:fainted|passed\s+out|blacked\s+out|light.?headed|seeing\s+stars|blurred\s+vision|"
    r"went\s+white|shaking|can'?t\s+stand\s+up)\b",
)


def _an_ordinary_helping(text):
    """True when a reflexive harm verb has its ordinary object after it.

    "she cuts herself a slice of cake", "he helps himself to the biscuits", "she served herself a
    large portion", "he burns himself out at work", "shes starving herself for a wedding". The
    verb is the same word the self-harm arms read, and the thing after it is what says which one
    it is - unless the line also states a wish, which is the wish whatever the plate.
    """
    return (_matches(ORDINARY_REFLEXIVE, text)
            and not _matches(A_WISH_OR_TALK_OF_IT, text)
            and not _matches(DISTRESS_BESIDE_IT, text)
            # ...and a body part beside a cut verb is a carving, not a plate: "she cuts herself a
            # cross on her arm" keeps the card even though "a cross" has a determiner in front.
            # A_BODY_PART is the module's own reader of a named body part, further down the file.
            and not (_matches(A_BODY_PART, text) and _matches(A_HARM_VERB_CUT, text))
            # ...and a line that says blood or a cut hand is not a plate of cake either: the first
            # aid is the answer to it, whether it was the knife or the act. A heavy bleed is the
            # exception - the ambulance is the answer there and the plate reading leaves it alone.
            and not (_matches(A_REAL_INJURY, text)
                     and not _matches(BLEEDING + CUT_NOT_STOPPING, text))
            # ...and the plate is not the reading when the line says the person is unwell after it:
            # "i cut myself a slice of cake and i feel faint" is a faint, and the cake is not the answer.
            and not _matches(UNWELL_BESIDE_THE_PLATE, text)
            # ...and a cut that will not stop bleeding is not a plate either: the card it had named
            # the ambulance and the crisis line, and the plate reading must not reach past it.
            and not _matches(BLEEDING + CUT_NOT_STOPPING, text))


SELF_REASSURED = (
    r"\b(?:i'?m|it'?s|im|its|he'?s|she'?s|they'?re|we'?re)\s+(?:all\s+)?(?:fine|ok|okay|grand)\b",
    r"\b(?:nothing|not)\s+(?:too\s+)?(?:serious|bad|major)\b",
)
# The user's own wish stays the user's: "i want to die and my son cuts himself" is one person
# saying two things, and the line that matters is theirs.
# "i wish i was dead" and its family were a shrug on main ("I'm here if you want to dig into any of
# that"): the wish was said as a wish about the speaker, and no arm knew the shape. `dead` in a
# comparison ("i wish i was dead tired", "dead lucky") is not the wish, so it is written out.
# The tail of the line is what decides a wish: a comma introduces the reason a day went badly
# ("i wish i was dead, that exam was brutal"), so these arms stop at a full stop, a question, an
# exclamation, or one of the softenings that say the same thing again. It is the lookahead
# `HOPELESS` uses above, and without it any complaint after the phrase rang the crisis card.
WISH_DEAD_TAIL = (r"(?=\s*(?:$|[.!?]|any\s?more|any\s+longer|at\s+all|no\s?more|now\b|"
                  r"tonight\b|today\b))")
# ...and for the "dead"/"gone" arms the test is only that a comma does not introduce the reason.
# "i wish i was dead i cant do this anymore" is the wish with the next thought run onto it and no
# punctuation at all, so it has to keep the card; the comma, not the tail, is what names a day.
# A comma followed by the same thing said again is still the wish: "i wish i was dead, honestly"
# and ", tbh" were the nod on main. Each word counts only where the line ends, so ", honestly, my
# exam went badly" is still an exam.
_SOFTENING = (r"(?:honestly|tbh|for\s+real|seriously|genuinely|no\s+joke|i\s+mean\s+it|"
              r"really|truthfully|lol)\b(?=\s*(?:$|[.!?]))")
WISH_DEAD_NO_REASON = (r"(?!\s*+,\s*+(?!any\s?more|any\s+longer|at\s+all|no\s?more|now\b|"
                       r"tonight\b|today\b|" + _SOFTENING + r"))")
WISH_DEAD = (
    r"\bi\s+wish\w*\s+i\s+(?:was|were|am)\s+(?:dead|gone|never\s+born)\b"
    # "dead" and "gone" are ordinary words as often as they are the wish, and every phrase below
    # names the day rather than a life: "i wish i was dead set on finishing it", "i wish i was
    # dead last in the race", "i wish i was gone fishing". Each of those was the crisis card on
    # main, which is the frightening reply to somebody talking about a race or a hobby, so the
    # phrase after the word keeps its own answer. "by six" is a time, and it is spelled out
    # because a bare "by" would also swallow the day of a real wish.
    r"(?!\s*(?:tired|exhausted|beat|knackered|on\s+my\s+feet|serious|funny|lucky|happy|"
    r"to\s+the\s+world|as\s+\w+|set\b|sure\b|honest\b|certain\b|"
    r"centre|center|to\s+rights|weight\b|fishing\b|in\s+the\s+water|"
    # "dead last in the race" is the race and "dead first place" is the medal; "dead last night"
    # and "dead first thing every morning" are times, which are the wish. So the two words are
    # kept only where a time word does not follow them.
    r"last\b(?!\s*(?:night|nights|week|weeks|month|months|year|years|time|times|summer|winter|"
    r"spring|autumn|christmas|new\s+year|monday|tuesday|wednesday|thursday|friday|saturday|"
    r"sunday))|"
    r"first\b(?=\s*(?:place|in\s+the\s+race|past\s+the\s+post|over\s+the\s+line))|"
    r"by\s+(?:\d|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|noon|midday|"
    r"half)\b))" + WISH_DEAD_NO_REASON,
    r"\bi\s+wish\w*\s+i\s+(?:wasnt|wasn'?t|was\s+not|didnt|didn'?t|did\s+not|never|"
    r"could(?:nt|n'?t|\s+not)?|would(?:nt|n'?t|\s+not)?)\b[^.?!]{0,20}"
    r"\b(?:dead|die|dying|gone|disappear|vanish|not\s+here|exist|born|wake\s+up)\b"
    + WISH_DEAD_NO_REASON,
    # "i wish i wasnt here" with nothing after it is the wish; what follows the "here" is where
    # they would rather not be, so a room or an occasion keeps its own answer: "i wish i wasnt
    # here when the boiler man comes" and "... for this meeting" are about the boiler man and the
    # meeting. Only the words that end the sentence, or say how long, keep the reading.
    r"\bi\s+wish\w*\s+i\s+(?:wasnt|wasn'?t|was\s+not)\s+(?:here|around|alive)\b"
    + WISH_DEAD_TAIL,
    r"\bi\s+wish\w*\s+(?:i\s+)?(?:to\s+die|to\s+be\s+dead|i\s+could\s+just\s+die)\b",
    # The wish in the past perfect: "i wish i had never been born", "i wish id never been born",
    # "i wished i had never been born". The past tense of "wish" and the "had" hid it from both
    # arms above, and the birth words left it to the new-baby answer - a congratulations card to
    # somebody saying they wish they had never existed.
    r"\bi\s+wish\w*\s+(?:i'?d\s+|i\s+had\s+|id\s+|had\s+)?never\s+(?:been\s+)?born\b"
    + WISH_DEAD_NO_REASON,
    # ...and the same wish without the "never": "i wish i hadnt been born", "i wish i wasn't
    # born". A denial is still the wish.
    r"\bi\s+wish\w*\s+(?:i\s+)?(?:hadnt|hadn'?t|had\s+not|wasnt|wasn'?t|was\s+not|aint)"
    r"\s+(?:ever\s+)?(?:been\s+)?born\b"
    + WISH_DEAD_NO_REASON,
    # The wish said as a habit: "i keep wishing i was dead", "i kept wishing i was never born".
    # The subject between "keep" and "wish" was what the arms above wanted, and these lines were
    # a shrug.
    r"\b(?:i\s+(?:keep|keeps|kept|was\s+always|am\s+always)|i'?ve\s+been|ive\s+been)\s+wish\w*\b"
    r"[^.?!]{0,20}\b(?:dead|die|dying|gone|not\s+here|never\s+(?:been\s+)?born|disappear)\b"
    # ...and what follows the word decides it, by the same rule the arms above use: "i keep
    # wishing i was dead" is the wish, and "i keep wishing i was dead on my feet" is a long day
    # (steward-fleet-blanket's read). A word list of tirednesses here was the wrong test, because
    # it only caught "dead tired" and not the "dead on my feet" that people actually say.
    + _CLAUSE_OR_END + WISH_DEAD_NO_REASON,
)
SELF_HARM_INTENT = (*SELF_HARM_INTENT, *WISH_DEAD, *SELF_HARM_CUT_NO_OBJECT)
WISH_DEAD_OFF = (*WISH_DEAD_HYPERBOLE, *WISH_DEAD_PLACE)
# A wish said as a state ("i want to be dead", "i would rather be dead") is the speaker's own
# wish too, or DEATH_REPORT reads "be dead" as somebody else's death and stands the card down.
OWN_WISH = (*OWN_WISH, *WISH_DEAD, *WISH_BE_DEAD)
FIRST_PERSON_WISH = (
    r"\bi\b.{0,20}\b(?:want|wanna|wish|might|rather|going|plan|feel\s+like|thinking\s+of)\b"
    r".{0,12}\b(?:to\s+)?(?:die|dying|kill\s+my\s*self|end\s+it|not\s+be\s+here|be\s+dead)\b",
    *WISH_DEAD,
)
# A suicide in a lesson, a film or the news is a subject, not a plan: "we talked about suicide in
# class today" and "the film we watched was about suicide" were answered with the user's own crisis
# card, which is a frightening reply to somebody describing their homework. Every arm needs the
# word itself, so "my son cant wake up for school" and "my chest hurts during training" are
# untouched.
_LEARN_PLACE = (r"(?:class|classes|lesson|lessons|assembly|school|college|uni|university|lecture|"
                r"seminar|workshop|training|course|pshe|homework|essay|exam)")
_MEDIA_WORD = (r"(?:film|films|movie|documentary|programme|program|show|series|episode|book|novel|"
               r"article|paper|podcast|news|telly|radio|play|song|headline|headlines|chapter|"
               r"thriller|true\s+crime|tv|netflix|tiktok|reddit|forum|subreddit|thread)")
_WORD_ITSELF = r"(?:suicide|suicidal|self[-\s]?harm)"
SUICIDE_MENTION_CONTEXT = (
    # the place, before or after the word: "we talked about suicide in class today"
    r"\b" + _WORD_ITSELF + r"\b.{0,40}\b(?:in|during|at|for)\s+(?:a|an|the|our|my|his|her)?\s*"
    + _LEARN_PLACE + r"\b",
    r"\b(?:in|during|at|for)\s+(?:a|an|the|our|my|his|her)?\s*" + _LEARN_PLACE + r"\b"
    r".{0,40}\b" + _WORD_ITSELF + r"\b",
    # the thing it was about, either way round: "the film we watched was about suicide"
    r"\b" + _MEDIA_WORD + r"\b.{0,40}\b" + _WORD_ITSELF + r"\b",
    r"\b" + _WORD_ITSELF + r"\b.{0,40}\b" + _MEDIA_WORD + r"\b",
    # and the bare homework sentence
    r"\b(?:we|they|the\s+class)\s+(?:talked|talk|discussed|covered|learned|learnt|studied|"
    r"read|watched)\s+(?:about\s+)?" + _WORD_ITSELF + r"\b",
)
# The lesson is often given by whoever taught it, and the word can come before the place:
# "our teacher talked about suicide today", "the tutor covered self harm in the seminar", "suicide
# came up at assembly". The person who taught it is not the one at risk, so this is a subject too.
SUICIDE_LESSON = (
    r"\b(?:teacher|tutors?|lecturers?|professors?|head\s*teacher|class|lesson|assembly|course|"
    r"workshop|training|pshe|seminars?|lectures?)\b[^.?!]{0,30}\b(?:talked|talk|talks|"
    r"discussed|discusses|taught|teaches|covering|covered|read|reads|watched|watches|mentioned|"
    r"mentions|went\s+over)\b[^.?!]{0,20}\b" + _WORD_ITSELF + r"\b",
    # The subject is named by the session rather than by a verb: "we did a lesson on self harm",
    # "an assembly about self harm", "a session on suicide". The setting is what makes it a
    # lesson, so the word names it and nothing has to be taught in the same sentence.
    r"\b(?:lesson|class|assembly|seminar|lecture|workshop|pshe|session|course|module|unit|"
    r"training|talk|chat)\b[^.?!]{0,20}\b(?:on|about)\s+" + _WORD_ITSELF + r"\b",
    # ...and coming up is how a subject arrives without a lesson: "suicide came up at work today",
    # "self harm came up in the meeting". A person's own plan says `i want to` instead.
    r"\b" + _WORD_ITSELF + r"\b\s+came\s+up\b",
    r"\b" + _WORD_ITSELF + r"\b[^.?!]{0,30}\b(?:in|at|during)\s+(?:the\s+|our\s+|her\s+|his\s+)?"
    r"(?:lesson|class|assembly|lecture|seminar|course|workshop|pshe|training)\b",
)
# "let's end it all and go home" is making a night of it, not a wish. The "and go" is what makes
# it a plan for the evening rather than a plan for the person.
END_IT_ALL_JOKE = (
    r"\b(?:let'?s|let\s+us)\s+end\s+it\s+all\s+and\s+go\b",
    r"\bend\s+it\s+all\s+and\s+go\b",
)


def _rest_of_it(line):
    """The line with the idioms cut out of it.

    The idiom goes first ("killed myself carrying that sofa", "killing myself laughing"), and then
    the phrases that are a wish only by look - "dying laughing", "dying of boredom" - because
    "i feel like dying laughing" is the joke and its remainder reads as a wish without them.
    """
    rest = re.sub(_LAUGH_KILL, " ", line)
    rest = EFFORT_AFTER.sub(" ", rest)
    for pattern in DIE_OF_THE_FEELING:
        rest = re.sub(pattern, " ", rest)
    for pattern in PAST_WISH_NOT:
        rest = re.sub(pattern, " ", rest)
    # "i felt like dying of embarrassment" leaves "i felt like" behind, and that is the start of
    # "i feel like ending it". Cut the frame too: "i feel like ending it" still reads as the wish
    # once only "ending it" is left, and "i felt like dying of embarrassment" reads as nothing.
    return re.sub(r"\b(?:feel|feels|feeling|felt)\s+like\b", " ", rest)


def _rings(text):
    """The module's own crisis vocabulary, read on a piece of a line."""
    return _matches(WISH_NAMED + WISH_INTENT + SELF_HARM_INTENT + FIRST_PERSON_WISH + DESPAIR
                    + NOT_JUST_A_NEAR_THING, text)


def _rest_of_it_rings(line):
    """True when the line says a wish outside the idiom itself."""
    rest = _rest_of_it(line)
    # Nothing was cut, so there is no "outside": reading the whole line back would make every
    # figure of speech its own wish. "i could kill myself for forgetting her birthday" is the one
    # this protects - the idiom is the whole line and the card is the wrong answer to it.
    if " ".join(rest.split()) == " ".join(line.split()):
        return False
    return _rings(rest)

# A line that names a death is not a joke to take up and not a heavy object: "i killed myself
# laughing at the funeral" wants the word for the loss, not "Ha, good. What set you off?".
DEATH_IN_THE_LINE = (
    r"\b(?:died|dying|death|funeral|burial|cremation|buried|passed\s+away|widow\w*|"
    r"widower|miscarriage|stillborn|cemetery|graveside|mourning|the\s+wake)\b",
)

_LAUGH_KILL = (r"(?:\b(?:was|were|am|is|are|been|kept|got)\s+killing"
               r"|\b(?:nearly|almost)\s+killed"
               r"|\b(?:kill|killing|killed))"
               r"\s+my\s*self\s+(?:laughing|with\s+laughter)\b")
IDIOM = (
    # A figure of speech stands down the death words it is made of, and nothing else: "work is
    # killing me and i keep thinking about suicide" and "this job is killing me, i want to die"
    # are a person saying both, and main answered them as small talk. So every arm here gives way
    # to a wish said in the same breath, the same guard the laugh and the "die of boredom" arms
    # already carry.
    r"\b(?:killing|kills|killed)\s+me\b" + WISH_LATER,
    r"\bdies?\s+(?:to|for)\b" + WISH_LATER,
    r"\bdying\s+(?:to|for)\b" + WISH_LATER,
    r"\b(?:dead|dying)\s+(?:tired|bored|hungry|of\s+embarrassment)\b" + WISH_LATER,
    r"\b(?:could|would|might)\s+die\b" + WISH_LATER,
    # The laugh stands down when the same line also says the wish: "i could kill myself
    # laughing but i still want to die" is a person saying both, and the wish is what matters.
    r"\bcould\s+kill\s+my\s*self\s+(?:laughing|with\s+laughter|try\w*)\b" + WISH_LATER,
    # The laugh without the "could": a laugh at the front of the sentence ("killing myself
    # laughing at this video", "i was killing myself laughing") rang the crisis line.
    r"\bkilling\s+my\s*self\s+(?:laughing|with\s+laughter)\b" + WISH_LATER,
    # "i could kill myself for forgetting that" is the same figure of speech said about a slip, and
    # it was the crisis card, question about suicide and all. The cause has to *be* a slip - a small
    # thing dropped, lost, forgotten, sent, said - and everything else keeps the card, because a
    # reason for the wish is still the wish: "for what he did to me", "for the way i look", "for
    # being so stupid", "for what i did to her", "for letting it happen again" and "for no reason at
    # all" are all disclosures, and only a listed slip stands the reply down.
    r"\b(?:i'?d|i\s+would|could|would|might)(?:\s+(?:just|honestly|literally|easily|quite|"
    r"really|so|totally|actually|probably|almost|nearly|bloody|still))?\s*kill\s+my\s*self\s+"
    r"(?:for|over|about)\s+(?!real\b|good\b|sure\b|definite\b|keeps?\b|ever\b)"
    r"(?=[^.!?]{0,24}\b(?:forgetting|forgot|losing|lost|missing|missed|dropping|dropped|"
    r"breaking|broke|spilling|spilt|spilled|deleting|deleted|sending|sent|booking|booked|"
    r"clicking|clicked|typing|typed|mixing|saying|said|"
    r"being\s+(?:so\s+|really\s+|a\s+bit\s+|very\s+|that\s+)?(?:late|lazy|slow|silly|"
    r"forgetful|clumsy|early|on\s+time)|that\b|this\b))"
    r"(?![^.!?]{0,24}\b(?:job|baby|pregnan\w*|mum|mom|dad|wife|husband|partner|marriage|"
    r"son|daughter|child|house|home|fiance\w*|said\s+to\s+(?:her|him|them|you|someone|"
    r"everyone|anyone|everybody))\b)" + WISH_LATER,
    # "i was killing myself laughing yesterday" is the same laugh in the past tense, which the
    # `could` form above could not see, so the crisis card was the answer to a joke.
    _LAUGH_KILL + WISH_LATER,
    r"\b(?:dye|dyed|die|dying)\s+(?:my|his|her|their|its)\s+hair\b" + WISH_LATER,
    r"\b(?:this|that|it)\s+(?:is|'s)\s+killing\s+me\b" + WISH_LATER,
    r"\bdying\s+of\s+(?:laughter|curiosity|hunger|thirst)\b" + WISH_LATER,
    # "i feel like dying laughing" says the feeling in the -ing form the wish is said in, so the
    # "dying of laughter" arm above did not reach it and the line got the crisis card.
    r"\b(?:dying|died|die)\s+(?:laughing|with\s+laughter)\b" + WISH_LATER,
    # "im going to die laughing", "we're going to die of boredom", "i could die of
    # embarrassment": the death word is the feeling, and the feeling is the whole line.
    # The feeling stands down, unless the same line also says the wish: "im going to die
    # laughing and honestly i want to die" is a person saying both.
    r"\b(?:going\s+to|gonna|will|would|could|might|about\s+to)\s+die\s+"
    r"(?:laughing|of\s+(?:laughter|boredom|embarrassment|shame|curiosity|hunger|thirst|"
    r"tiredness|excitement|joy))\b" + WISH_LATER,
    r"\b(?:die|dying|died)\s+of\s+(?:boredom|embarrassment|shame|excitement)\b" + WISH_LATER,
    r"\b(?:kill|killing)\s+time\b", r"\bstarving\s+(?:for|of)\b",
)
FIRST_PERSON = (r"\bi\b", r"\bi'?m\b", r"\bi'?ve\b", r"\bme\b", r"\bmyself\b", r"\bmy\s+own\b")
PAST_HARM = (
    r"\b(?:broke|broken|fractured|dislocated|sprained)\b.{0,30}\b(?:when\s+i\s+was|years?\s+ago|"
    r"as\s+a\s+(?:kid|child|boy|girl)|last\s+(?:year|summer|winter|month|week)|ages\s+ago)\b",
)
URGENT_NOW = (
    r"\b(?:now|right\s+now|today|tonight|just|suddenly|this\s+(?:morning|evening|afternoon|"
    r"moment))\b",
)


# "i jumped off a bridge last week" is a leap; the same words are a dare with a crowd in it and a
# swim with a river under it. So the leaper is the speaker alone, and no water is below.
LEAP_OFF_A_DROP = (
    r"(?:\bi\b[^.?!]{0,15}\bjumped\b(?![^.?!]*\binto\s+(?:the\s+|a\s+)?(?:river|water|sea|"
    r"lake|canal|reservoir|pool)\b)|\bthrew\s+my\s*self\b)[^.?!]{0,12}\b(?:off|from)\s+"
    r"(?:a\s+|the\s+)?(?:bridge|roof|building|cliff|car\s*park|balcony)\b"
)
# The attempts that stand on their own with no time on them. A dose is not one of these: "i took a
# whole packet of paracetamol" is happening now and wants the poisons line, and "i cut my wrist" is a
# wound that needs pressure, so only the plainest spoken attempt is read this way.
# "i cut my wrists when i was a teenager" rang the 999 bleed card: the teenager shapes were not in
# OLD_TIME, so the memory never reached the gate that reads an old telling. They are kept out of
# OLD_TIME on purpose, because that gate stands a whole line down ("i have had blood in my poo since
# i was a teenager" is a long-standing symptom that still wants the GP) - only the telling reads them.
TEEN_AGE = (
    r"\b(?:when|since)\s+i\s+was\s+(?:a\s+)?(?:teenager|teen|in\s+my\s+teens)\b",
    r"\b(?:as|like)\s+a\s+teenager\b", r"\bin\s+my\s+teens\b", r"\bgrowing\s+up\b",
    r"\bwhen\s+i\s+was\s+(?:in\s+my\s+)?(?:twenties|thirties|forties|fifties)\b",
)

PAST_ATTEMPT = (
    # "i nearly ended it" is the same disclosure short of the act, and it was a shrug: the verb list
    # was all tries. Only "ended it" and "took my own life" take "nearly" - "nearly killed myself"
    # is the laugh idiom and has its own guard.
    r"\b(?:nearly|almost)\s+(?:ended|did)\s+it\b",
    r"\b(?:nearly|almost)\s+(?:took|ended)\s+my\s+(?:own\s+)?life\b",
    r"\b(?:tried|try|tries|attempted|attempt|attempts|went\s+to)\b[^.?!]{0,25}"
    r"\b(?:kill(?:ing)?\s+(?:my|him|her|them)\s*self|end(?:ed|ing)?\s+it|end\s+my\s+life|"
    r"take\s+my\s+own\s+life|suicide|overdos\w*|hang(?:ing)?\s+(?:my|him|her|them)\s*self|"
    r"cut\s+(?:my|his|her|their)\s*wrists?|jump\s+off)\b",
    r"\b(?:took|taken|swallowed|downed|popped|necked|ate)\b[^.?!]{0,25}"
    r"\b(?:an?\s+overdose|too\s+many\s+(?:pills|tablets|paracetamol|ibuprofen|painkillers|"
    r"sleeping\s+pills|antidepressants))\b",
    # The container is the dose only when a drug is named after it, and "a whole packet of
    # paracetamol" is that dose: the word "whole" sat between the article and the container and
    # the old arm needed them side by side, so the plainest way of saying it rang nothing.
    r"\b(?:took|taken|swallowed|downed|popped|necked|ate)\b[^.?!]{0,25}"
    r"\b(?:a|the|what\s+was\s+left\s+of\s+(?:a|the))\s+(?:whole\s+|entire\s+|full\s+)?"
    r"(?:bunch|load|handful|packet|pack|box|strip|blister|bottle)\s+of\s+(?:(?:the|my|his|her|"
    r"their|our|some)\s+)?(?:\w+'?s\s+)?" + DRUG_NAME + r"\b",
    r"\boverdos(?:e|ed)\b",
    r"\b(?:cut|cutting|sliced|slashed|carved)\b[^.?!]{0,12}\b(?:my\s*self|(?:my|his|her|their)\s+"
    r"(?:wrists?|arms?|forearms?|upper\s+arms?|thighs?|legs?|tummy|stomach|belly|chest|shins?))\b",
    *SELF_HARM_SCARS,
    r"\b(?:hung|hanging|hanged|tied|put|got)\b[^.?!]{0,20}\b(?:rope|noose|belt|cord)\b"
    r"[^.?!]{0,20}\b(?:my\s+neck|round\s+my\s+neck|around\s+my\s+neck)\b",
    r"\b(?:held|put|pressed|pushed)\b[^.?!]{0,20}\b(?:a\s+)?(?:knife|blade|razor)\b"
    r"[^.?!]{0,20}\b(?:to|against)\s+my\s+(?:throat|neck|wrist|arm)\b",
    LEAP_OFF_A_DROP,
    # The body is what is on the track: "i laid the slabs on the track last week" is a garden, so
    # nothing may come between the verb and the "on".
    r"\b(?:laid|lay|lying|sat|sitting|standing|stood|walked|stepped)\s+(?:down\s+)?(?:on|onto|"
    r"in\s+front\s+of)\s+(?:the\s+)?(?:train\s+tracks?|rail\s+tracks?|tracks?|railway|"
    r"live\s+rail)\b",
    *EDGE_OF_A_DROP,
    r"\bself[-\s]?harmed\b",
)
# The acts that no craft word explains: nobody cuts both wrists gardening, and no knife-to-the-throat
# is a chopping board. These keep the card whatever else the line says.
PAST_ATTEMPT_STRONG = (
    r"\b(?:tried|try|tries|attempted|attempt|attempts)\b[^.?!]{0,25}"
    r"\b(?:kill\s+my\s*self|end(?:ing)?\s+it|end\s+my\s+life|take\s+my\s+own\s+life|suicide)\b",
    r"\b(?:cut|cutting|sliced|slashed|carved)\b[^.?!]{0,10}\bmy\s+wrists?\b",
    r"\boverdos(?:e|ed)\b",
    r"\b(?:hung|hanging|hanged|tied|put|got)\b[^.?!]{0,20}\b(?:rope|noose|cord)\b",
    r"\b(?:knife|blade|razor)\b[^.?!]{0,20}\b(?:to|against)\s+my\s+(?:throat|neck)\b",
    LEAP_OFF_A_DROP,
    r"\b(?:laid|lay|lying|sat|sitting|standing|stood)\s+(?:down\s+)?(?:on|in\s+front\s+of)\s+"
    r"(?:the\s+)?(?:train\s+tracks?|rail\s+tracks?|tracks?|railway)\b",
    *EDGE_OF_A_DROP,
    r"\bself[-\s]?harmed\b",
    # A cut that says it was meant is meant, whatever the kitchen was doing.
    r"\b(?:cut|cutting|sliced|slashed|carved|burned|burnt|scratched)\b[^.?!]{0,25}"
    r"\b(?:on\s+purpose|deliberately|to\s+(?:hurt|punish|feel|see\s+blood|calm|cope))\b",
)
# "i nearly killed myself last week" is a near miss, and most lines said that way are accidents -
# the stairs, the bike, laughing - so this arm carries the craft words as well as the idioms.
PAST_NEAR_ACT = (
    r"\bi\b[^.?!]{0,12}\b(?:nearly|almost|come\s+close\s+to|came\s+close\s+to)\b"
    r"[^.?!]{0,14}\b(?:kill(?:ed)?\s+my\s*self|hurt\s+my\s*self|cut\s+my\s*self|"
    r"did\s+something\s+stupid|end\s+it)\b",
)
# The means `END_MEANS` does not name, because the sentence is about a person who walked into
# traffic rather than about pills.
EFFORT_MEANS = END_MEANS + (
    r"\btraffic\b", r"\bcliff\w*\b", r"\bplatform\b", r"\bledge\b", r"\bkerb\b",
    # "off the bridge" is where a person goes to end it, not a thing they ride: the fall arm must
    # not take it, the same way it steps back for the cliff and the platform.
    r"\bbridge\w*\b",
)
# The -ing words that are the act rather than the job: "nearly killed myself cutting" is a person
# who cut themselves, so the effort reading must not take it.
HARM_DOING = re.compile(
    r"^(?:cutting|burning|harming|hurting|starving|drowning|hanging|overdosing|poisoning|"
    r"slashing|scratching|swallowing|taking|drinking|suffocating|choking|strangling|hitting|"
    r"punching|banging|throwing|jumping|bleeding|punishing|self)$",
)


# Plan language in front of the laugh keeps it literal: "i want to kill myself laughing", "im going
# to kill myself laughing" and "i might kill myself laughing" are the wish with a joke on the end.
# Main's three failing tests are right about that, so the laugh reply steps back for these.
PLAN_FRAME_LAUGH = (
    r"\b(?:want|wanna|wanted|intend|intending|plan|planning|plan\s+to|going\s+to|gonna|might|"
    r"may|will|would|should|considering|thinking\s+about|thought\s+about)\b[^.?!]{0,18}"
    r"\b(?:kill|killing|killed)\s+my\s*self\b",
)
# The bare exclamation keeps main's stand-down: "i nearly killed myself laughing" and "i almost
# killed myself laughing" are answered by the conversation, and a test of the safety module's own
# contract says so. Once there is something to ask about - "at that", "at this video", "yesterday" -
# the laugh reply has an anchor and takes the turn.
BARE_LAUGH = re.compile(
    r"^\W*(?:i\s+)?(?:nearly|almost|very\s+nearly)\s+(?:kill|killing|killed)\s+my\s*self\s+"
    r"(?:laughing|with\s+laughter)\W*$")


def _the_laugh(line):
    """True when the line is the laughing figure of speech, not a wish.

    It rides on `_idiom`, so the same guard applies: "i could kill myself laughing but i still
    want to die" keeps the crisis card - and so does the wish said as a shrug after it, "i was
    killing myself laughing and now i feel empty", which is what NOT_JUST_A_NEAR_THING reads.
    """
    if _matches(PLAN_FRAME_LAUGH, line) or _rest_of_it_rings(line):
        return False
    if BARE_LAUGH.match(line.strip()):
        return False
    return _idiom(line) and re.search(_LAUGH_KILL, line) is not None


def _an_accident_near_thing(line):
    """True when "nearly died" is a scare on a bike or a ladder, not a wish.

    The accident is the thing they came off, said before the phrase or after it; a wish, a means
    or a deliberate act on the same line takes the accident back.
    """
    doing = _EFFORT_DOING.search(line)
    if not (_EFFORT_BEFORE.search(line)
            or (doing and doing.group("doing") != "laughing"
                and not HARM_DOING.match(doing.group("doing")))):
        if not _EFFORT_DIED.search(line) or not _COME_OFF_IT.search(line):
            return False
    return (not _matches(EFFORT_NOT_AN_ACCIDENT, line) and not _matches(EFFORT_MEANS, line)
            and not _rings(line) and not _rest_of_it_rings(line))


def _near_thing_key(line):
    """The near thing's own reply, or the one for the person who watched it happen."""
    return "near_thing_other" if _person(line) and not _matches((r"\bi\b", r"\bwe\b"),
                                                                line) else "near_thing"


def _the_effort_frame(line):
    """True when "killed myself" is a job they were doing, not a wish.

    "i nearly killed myself carrying that sofa", "moving house", "at the gym" and "on my bike"
    are the idiom for a near thing; main answered every one of them with a crisis line and a
    crisis number. The key is what comes straight after the phrase, so a wish said anywhere in
    the line - "i nearly killed myself and i want to die" - keeps the card.
    """
    if _an_accident_near_thing(line):
        return True
    found = EFFORT_AFTER.search(line)
    if not found:
        return False
    doing = found.group("doing")
    if doing and HARM_DOING.match(doing):
        return False
    # The laugh has its own arm and its own reply: "i nearly killed myself laughing at that" is
    # not a job with a heavy thing.
    if doing == "laughing":
        return False
    # A means on the line is a plan, not a job: "i nearly killed myself walking into traffic" is
    # not the sofa, and the effort reading must not take it.
    if _matches(EFFORT_MEANS, line):
        return False
    return not _rings(line) and not _rest_of_it_rings(line)


# An act and a death in the same line is a loss, not a live crisis: "my dad overdosed when i was 10
# and died" is a bereavement, and the loss reply is the one for it. "i feel dead inside" is not that
# death, so the feeling is read out of it.
PAST_DEATH = (
    r"\b(?:died|dead|death|passed\s+away|passed\s+on|funeral|burial|cremated|cremation|"
    r"inquest|autopsy|post\s*mortem|buried)\b",
)
SELF_DEAD_FEELING = (
    r"\b(?:i\s*(?:'?m|am|feel|felt|was)\s+(?:dead|like\s+death)|dead\s+inside|"
    r"feel(?:s|ing)?\s+dead|wish\s+(?:that\s+)?i\s+(?:was|were)\s+dead)\b",
)
# A memory of a decade ago is history: "my nan overdosed on her tablets years ago" is a grandchild
# remembering, so the reply for somebody in trouble now is not the one for it.
LONG_AGO = (
    r"\b(?:\d+\s+years?\s+ago|years?\s+ago|decades?\s+ago|when\s+i\s+was\s+\w+|"
    r"in\s+(?:19|20)\d\d)\b",
)
GAS_BURNER = r"(?:gas(?:\s+(?:cooker|oven|fire|heater|ring|hob|grill|stove))?|hob|burner|gas\s+ring|grill|stove)"
# A bite that has drawn blood is a bite that happened, whatever the habit word in front of it.
DOG_BLEED = (
    r"\b(?:bleeding|bled|blood\w*|broke\s+the\s+skin|broken\s+the\s+skin|skin\s+is\s+broken|"
    r"punctur\w*|stitches|wound|a&e|hospital|infected)\b",
)
DOG_ITCH = (
    r"\b(?:itch\w*|scratch\w*|fleas?|skin|raw\s+(?:patch|skin)|chew\w*|groom\w*|bald\s+patch|"
    r"hot\s+spot|sore\s+spot|lump)\b",
)
# ... and the stand-down above is cancelled by a person in the line, whoever the dog is also biting.
DOG_BIT_A_PERSON = (
    r"\b(?:me|us|someone|somebody|anybody|anyone)\b",
    r"\b(?:my|his|her|their|our)\s+(?:hand|hands|arm|arms|leg|legs|foot|feet|face|finger|"
    r"fingers|head|shoulder|shoulders|wrist|ankle|neck|cheek|nose|toe|toes|chin|back|skin)\b",
)
DOG_ATTACK_NOW = (
    r"\b(?:right\s+now|at\s+the\s+moment|this\s+minute|attacking|mauling|savaging|"
    r"has\s+hold\s+of|wont\s+let\s+go|won'?t\s+let\s+go|just\s+bit|just\s+bitten|"
    r"dragging\s+(?:me|him|her|them))\b",
)
# A bite from years back is a retelling; one from last week that has not been seen still needs the
# vet today, so only the long-ago and the habit arms stand the answer down.
PET_LONG_AGO = (
    r"\byears\s+ago\b", r"\bages\s+ago\b", r"\bused\s+to\b", r"\blast\s+year\b",
    r"\bwhen\s+(?:he|she|it|they)\b.{0,20}\b(?:puppy|kitten|young)\b",
    r"\bevery\s+(?:few\s+)?(?:days?|weeks?|months?|years?)\b",
    r"\bis\s+that\s+(?:normal|usual|common)\b",
)
from bot.knowledge.crisis_replies import AFTER  # noqa: F401  (what to say once help is coming)
from bot.knowledge.crisis_replies import WAITING  # noqa: F401  (what to do while help comes)

# ...but a back with numbness below it is the cauda equina card in the health module, which names the
# legs, the saddle and the bladder, and says same-day rather than ambulance. That card was answering
# `my back is broken and my legs are numb` before this row existed, so the row stands down and lets it
# answer, rather than taking the worst lines in the set down to a fracture card.
SPINE_NUMB_LOWER = (
    r"\b(?:legs?|feet|foot|toes?|thighs?|calves?|saddle|between\s+my\s+legs|bladder|bowels?)\b",
    r"\b(?:can'?t|cant|cannot)\s+(?:pee|wee|urinate)\b",
    r"\bno\s+urine\b",
)
SPINE_BACK_FALL = (
    r"\b(?:fell|fall|fallen|falling|crash|accident|collision|landed|dropped|horse|bike|"
    r"bicycle|stairs|staircase|ladder|roof|scaffold|dive|dived|diving|trampoline|sledging|sking|"
    r"skiing|hit\s+by|knocked\s+over|thrown|rode\s+off)\b",
)
# The speaker is the one who has to not move, so this card is written in the second person and the
# row only matches the speaker's own back or neck.
SPINE_BREAK_ANSWER = (
    "Ring 999 or 911 and don't move: don't sit up and don't let anyone move you. A break in the back "
    "or the neck can injure the spinal cord, and it is the moving that does the damage, so stay "
    "exactly where you are, warm and still, until the crew arrive.",
)
# Cases where the follow-up can be about the user themselves ("my chest", "i fell"): the wording
# is neutral, and these are the words that turn it to the second person when the user is the patient.
FIRST_FIT = ("chest", "breathing", "head_injury", "heat", "stroke", "bleeding", "poison")
ME = ((r"\bthey\b", "you"), (r"\bthem\b", "you"), (r"\btheir\b", "your"),
      (r"\btheirs\b", "yours"), (r"\bthemselves\b", "yourself"), (r"\bthey're\b", "you're"),
      (r"\bthey are\b", "you are"))


# Help arriving is good news, and the greeting module says that better than another instruction
# does: "the ambulance is on the way" is not a request for more first aid. A question about when
# they will get here is a different line and is answered before this one.
HELP_ASK_MORE = (
    r"\?", r"\b(?:what|how|should|can|could|when|else|while|wait|waiting|now|do|anything)\b",
    r"\b(?:outside|stairs|smoke|breath\w*|bleeding|burn\w*|door)\b",
)


NEXT_STEP = (
    r"\b(?:check\w*|hospital|a\s*&\s*e|a\s+and\s+e|doctor|gp|worry\w*|normal|fine|okay|serious|dangerous)\b",
)


NOT_BREATHING_NOW = (
    r"\b(?:not|isn'?t|aren'?t|wasn'?t|stopped?)\s+breathing\b", r"\bno\s+pulse\b",
    r"\b(?:stopped|stopping)\s+breathing\b",
)


BURNT_MARKS = (
    r"\b(?:clean|cleaning|scrub(?:bing)?|remove|removing|wipe|wiping|get\s+off)\b.{0,40}\b(?:worktop|worktop|hob|oven|pan|toaster|toast|carpet|grill|barbecue|bbq|saucepan|plate)\b",
    r"\b(?:burn|burned|burnt|scorch|scorched|scorch\s+marks?)\b.{0,20}\bmarks?\b",
)


# An older person who has gone down and cannot take weight is the hip answer whatever joint they
# name: "my dad is 85 and he fell and he cant put weight on it" is an ambulance, not an X-ray.
WEIGHT_OLD = (
    r"\b(?:nan|nana|granny|gran|grandma|grandmother|grandad|grandpa|grandfather|elderly|"
    r"pensioner|oop|old\s+(?:man|woman|lady|boy|girl))\b",
    r"\b(?:6[5-9]|[7-9]\d|1[0-1]\d)\b",
)
WEIGHT_OLD_FALL = (r"\b(?:fell|fallen|fall|falling|slipped|tripped|collapsed|down)\b",)

# A limb at a funny angle is a fracture, not a bruise - but only when the limb is someone's. The arm
# of a pair of glasses and the leg of a chair are bent all the time, and "the arm of my glasses is
# bent" was told to stay where it was and ring 999. The rule is held apart from the list above so
# the loop can ask what the limb belongs to.
LIMB_AT_AN_ANGLE = (
    r"\b(?:arm|leg|wrist|ankle|shoulder|elbow|knee)\b[^.?!]{0,25}"
    r"\b(?:bent|deformed|at\s+a\s+funny\s+angle|sticking\s+out|back\s+to\s+front)\b",
)


def _without_object_limbs(line):
    """The line with every "leg of my jeans" / "trouser leg" phrase taken out.

    What is left is the question the loop actually has to ask: does the person's own limb appear
    at an angle? A garment's leg goes, a knee does not.

    The one arm that names "bent" in the pattern itself is the stand-down question said as a whole
    sentence ("my jeans are bent"), not the name of an object's limb. Taken out like the others it
    swallowed the person as well - "my jeans and my knee is bent" went whole, and
    "i fell in my jeans and my knee is bent the wrong way" lost the ambulance. So it stays in.
    """
    for pattern in LIMB_IS_A_THING:
        if "bent" in pattern:
            continue
        line = re.sub(pattern, " ", line, flags=re.I)
    return line


FALL = FALL_CORE + LIMB_AT_AN_ANGLE
# "i nearly fell off the ladder" is a fright, not a fall - unless the line says what it cost.
NEAR_MISS = (
    r"\b(?:nearly|almost|near)\s+(?:fell|fallen|tripped|slipped|tumbled|went\s+over|came\s+off)\b",
    r"\bthought\s+i\s+(?:was\s+going\s+to|would)\s+fall\b",
)
NEAR_MISS_HARM = (
    r"\b(?:broke|broken|fractured|hurt|hospital|ambulance|a\s+and\s+e|a&e|stitches|"
    r"can'?t\s+(?:get|stand|move)|knocked\s+out|unconscious)\b",
)
# A pattern that also names an injury is that injury's card, not the pattern's: "i keep falling
# down the stairs and now my ankle is bent" is a break to be seen now.
FALL_PATTERN_HURT = (
    r"\b(?:broke|broken|fractured|bent|deformed|sticking\s+out|back\s+to\s+front|bleeding|"
    r"blood|gash|swollen|stitches|hospital|ambulance|a\s+and\s+e|a&e|unconscious|knocked\s+out)\b",
)

# "my dad fell in the garden" is a fall with nothing else said, and main answered it with "Noted:
# your dad fell in the garden." The two questions are the answer: can they get up, did they hit
# their head. Anything that already says how it went is a different arm.
FALL_CHECK = (
    r"\b(?:i|we)\s+(?:just\s+)?(?:fell|fallen|slipped|tripped|went\s+over)\b",
    r"\b(?:he|she|they)\s+(?:just\s+)?(?:fell|fallen|slipped|tripped|went\s+over)\b",
    r"\b(?:my|our|the)\s+" + PERSON + r"\b[^.?!]{0,20}\b(?:fell|fallen|slipped|tripped|"
    r"went\s+over)\b",
)
# Of those, the ones where the breathing itself has stopped: the CPR card, not the recovery position.
FALL_NOT_BREATHING = (
    r"\b(?:not|isn'?t|isnt|aren'?t|arent|stopped|stop|stopt)\s+breathing\b",
    r"\bcan'?t\s+breathe\b", r"\bcant\s+breathe\b",
)
# The pet has to be the one that fell: "i tripped over the cat and broke my hip" is the user's.
PET_FELL = (
    r"\b(?:dog|cat|pupp\w*|kitten|pup|pet|parrot|hamster|rabbit|bunny|horse|pony|budgie|"
    r"guinea\s+pig|tortoise|ferret|gerbil|snake|lizard|animal)\b[^.?!]{0,20}\b(?:fell|fallen|"
    r"jumped|slipped|tumbled)\b",
)

PET_SUBJECT = (
    r"\b(?:my|our|the|a)\s+(?:dog|cat|puppy|kitten|pup|pet|parrot|hamster|rabbit|bunny|horse|"
    r"pony|budgie|guinea\s+pig|tortoise|ferret|gerbil|snake|lizard)\b",
)
# People type the possessive without the apostrophe, and "my dogs face has drooped" is the same
# animal as "my dog's face has drooped": the standdown below would have read the plural as no
# animal at all and left the person's stroke card on the pet.
PET_SUBJECT_PLURAL = (
    r"\b(?:my|our|the)\s+(?:dogs|cats|puppies|kittens|rabbits|horses|ponies|pets)\b",
)
# Moved to safety_cards.py: PET_APPOSITIVE, PET_APPOSITIVE_SUB, PET_BREATH, PET_BREATH_NOW, PET_CANT_SETTLE, PET_EFFORT, _PET_APPOSITIVE
# "and so do i", "me too" after the animal's wish: the speaker's own wish in the short form, which
# FIRST_PERSON_WISH (it wants a verb like want or wish) and _own_wish do not read.
SO_I_TOO = (
    r"\b(?:so\s+(?:do|will|would|can|does)\s+i|same\s+here|me\s+too|and\s+i\s+do)\b",
)
# The wish said about the animal rather than by the speaker: the same pet subject, and one of the
# ways people say the animal has had enough close behind it in the same sentence.
PET_WANTS_OUT = (
    r"\b(?:my|our|the|a)\s+(?:dog|cat|puppy|kitten|pup|pet|parrot|hamster|rabbit|bunny|horse|"
    r"pony|budgie|guinea\s+pig|tortoise|ferret|gerbil|snake|lizard)\b[^.?!]{0,40}\b(?:"
    r"wants?\s+to\s+die|no\s+will\s+to\s+live|doesn'?t\s+want\s+to\s+live|"
    r"does\s+not\s+want\s+to\s+live|no\s+quality\s+of\s+life|has\s+had\s+enough(?!\s+(?:food|water|to\s+eat|dinner)))\b",
)
def _any_of(*groups):
    """One alternation from several pattern groups, for the lookahead pairs below."""
    parts = [r"(?:" + part + r")" for group in groups for part in group]
    return r"(?:" + "|".join(parts) + r")" if len(parts) > 1 else parts[0]


def _both(first, *rest):
    """One thing from `first` and one from `rest`, both in the line, in whichever order."""
    return ("(?=.*" + _any_of(first) + r")(?=.*" + _any_of(*rest) + r")",)


# A fever with a rash, a stiff neck or confusion is sepsis or meningitis, and it is the line that
# looks most ordinary and kills quickest. Nothing here fires on the fever alone: "my son has a
# temperature" is a doctor-today question, so each row wants the thing that makes it an ambulance.
RASH = (r"(?:rash|rashes|spots|marks|blotches|dots|purpura|petechiae)")
# The names of the sign, as opposed to a description of a mark. Nobody says "non blanching" about
# a tan or a bruise, so a line that names it is the glass test already done and does not need a
# fever or a child beside it to be the ambulance: "non blanching rash" and "the rash does not
# blanch" were reaching the conversational nod, and "i have a rash that doesnt blanch" was told
# that most rashes are contact or heat.
RASH_NAMED = (r"\bnon[\s-]?blanch\w*", r"\bpetechiae\b", r"\bpurpura\b")
# A definition ask is a question about the term, not a rash in front of the person: "what is a non
# blanching rash" is somebody reading a leaflet, and the ambulance card for it is an alarm nobody
# reported. Same reading as ELECTRIC_SHOCK_DEFINITION.
RASH_DEFINITION = (
    r"\b(?:what|whats|what'?s|which)\s+(?:is|are|does|do)\b[^.?!]{0,30}"
    r"\b(?:non[\s-]?blanch\w*|blanching)\b",
    r"\b(?:explain|definition\s+of|meaning\s+of|what\s+does)\b[^.?!]{0,25}"
    r"\b(?:non[\s-]?blanch\w*|blanching|blanch)\b",
)
# The fade test by itself is a mark on an arm; with a fever, on a child, or said as petechiae it
# is the meningitis rash. So the flat-rash row is kept apart and asks for company in respond().
RASH_FLAT = _both((RASH,), RASH_FADE)
RASH_RED = (
    r"\bnon[\s-]?blanch\w*",
    r"\b(?:petechiae|petechial|purpura|purpuric)\b",
    r"\bpurple\s+(?:rash|spots|marks|dots|blotches)\b",
    r"\b(?:bruise|bruises|bruising)\b[^.?!]{0,25}\b(?:for\s+no\s+reason|out\s+of\s+nowhere|"
    r"spreading|everywhere)\b",
) + RASH_FLAT
# A stiff neck is meningitis when something else in the line is red; a stiff neck from sleeping is
# the answer people get most often, so the cause stands the case down.
# Losing consciousness had no card in this module: "i passed out" and "my husband passed out in the
# garden" were the composer's faint line - well written for a faint with an obvious cause, and it says
# to be seen this week, which is the wrong week for the three ways a blackout is the heart. Going down
# during exercise, going down with chest pain or a racing heart, or coming round on the floor with no
# idea how you got there is a same-day assessment at the least and 999 when anything is off.
# Only the three ways people say a blackout. "Out cold", "collapsed", "keeled over" and "went limp"
# are deliberately not here: the unconscious case and the head injury case already answer them well
# ("keep him on his side, check he's breathing"), and taking those lines was a regression.
BLACKOUT_ANY = (
    r"\b(?:pass(?:ed|ing)?\s+out|black(?:ed|ing)?\s+out|faint(?:ed|ing)?)\b",
)
BLACKOUT_HEART = (
    r"\b(?:chest\s+(?:pain|tight\w*|pressure|heavy)|palpitation\w*|racing\s+heart|"
    r"heart\s+(?:racing|pounding|fluttered|fluttering|went)|fluttering|irregular\s+heartbeat|"
    r"pounding\s+heart)\b",
)
# Somebody who has not come round, or is not right afterwards, is the 999 that the faint line is not.
BLACKOUT_STILL_DOWN = (
    r"\b(?:not|hasn'?t|haven'?t|isn'?t|wasn'?t)\s+(?:come\s+round|came\s+round|woken?|"
    r"woke|with\s+it|responding)\b",
    r"\b(?:out\s+cold|in\s+and\s+out|still\s+(?:out|down))\b",
)
# The three ways a blackout is the heart, which is the 999 card, kept apart from the two ways it is a
# same-day question: a run of them, and somebody else on the floor.
BLACKOUT_URGENT = (BLACKOUT_EFFORT + BLACKOUT_HEART + BLACKOUT_FLOOR + BLACKOUT_STILL_DOWN
                   + BLACKOUT_BREATH)
BLACKOUT_RED = BLACKOUT_URGENT + BLACKOUT_REPEAT + BLACKOUT_SOMEONE_DOWN
BLACKOUT_RED_LINE = _both(BLACKOUT_ANY, BLACKOUT_RED)
FEVER_SIGN = (
    r"\bfever\w*", r"\btemperature\b", r"\btemp\b", r"\bfeverish\b", r"\bburning\s+up\b",
    r"\bhot\s+to\s+touch\b", r"\b\d{2}(?:\.\d)?\s*(?:c\b|degrees)", r"\bhigh\s+temperature\b",
)
# What makes a fading-test line the emergency: a fever, a child, or the rash being everywhere.
RASH_COMPANY = FEVER_SIGN + (
    r"\b(?:baby|babies|newborn|infant|toddler|child|children|kid|kids|son|daughter|boy|girl|"
    r"nursery|school)\b",
    r"\b(?:everywhere|all\s+over|spreading)\b", r"\bpetechiae\b", r"\bpurpura\b",
)
# "his temp is 39 and hes drowsy": the person can be named by a possessive or a contraction.
RED_ANCHOR = HUMAN_ANCHOR + (
    r"\b(?:his|her|their|hes|shes|theyre|our|your|newborn|new\s?born|infant|toddler|baby)\b",
    # The age is the anchor when it is said next to a temperature: "my 6 week old has a fever".
    r"\b\d+\s*(?:days?|weeks?)\s+old\b", r"\b(?:1|2|one|two)[-\s]*months?[-\s]*old\b",
    r"\b(?:is|only|just|nearly)\s+(?:1|2|one|two)\s+months?\b",
    # A child given in years is a person too. "my 2 year old has a temperature and is floppy" was
    # read as no one at all, because only days and weeks were an anchor, and it fell past the
    # sepsis card to the 111 one whose own text calls a floppy child a 999.
    r"\b\d+\s*(?:year|yr|month)s?[-\s]*old\b",
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten)(?:\s+and\s+a\s+half)?\s+years?\s+old\b",
    r"\b(?:my|his|her|their|our)\s+(?:son|daughter|boy|girl|child|kid|little\s+one)\b",
)
# An oven, a boiler and a room have a temperature too, and none of them can be drowsy.
DEVICE_TEMP = (
    r"\b(?:oven|boiler|room|water|thermostat|fridge|freezer|shower|bath|heating|radiator|"
    r"washing\s+machine|tumble\s+dryer|air|weather|engine|car)\b[^.?!]{0,20}\btemperatures?\b",
    r"\btemperatures?\s+(?:setting|gauge|dial|control|knob)\b",
)
NEWBORN_FINE = (
    r"\bover\s+(?:3|three|6|six)\s+months\b",
    r"\b(?:3|4|5|6|7|8|9|1\d|[2-9]\d)\s+months?\s+old\b",
    r"\b(?:three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+months?\s+old\b",
    r"\b\d+\s*(?:years?|yrs?)\s+old\b",
)
# The words that make a fever line the baby's: "my baby has a temperature", "our daughter is hot".
TINY_SAID = (
    r"\b(?:my|our|the)\s+(?:baby|babies|newborn|infant|little\s+one)\b",
    r"\b(?:my|our)\s+(?:son|daughter|boy|girl|child)\b",
)


# A named serious illness said plainly is the thing itself, not small talk: "my son has
# meningitis" got "Noted: your son has meningitis." A child already being treated ("she is on
# antibiotics for it", "he had it years ago") is a story, so it stays ordinary.
# A child named by their place in the family names no son or daughter: "my youngest has a
# temperature" and "the eldest drank it" are the same child as "my son has a temperature", and
# without the place words the safety rules that key on a child passed both over and the line got
# a general answer. Only a possessive makes them a child - a bare "the youngest" can be a dog.
# ...and the everyday word for a child is the same child: "my lad has a temperature" was
# answered "I'm listening" while "my son has a temperature" got the 111 line.
CHILD_BY_PLACE = (r"(?:my|our|his|her|their)\s+(?:youngest|eldest|oldest|little\s+one|"
                  r"middle\s+one|lad|lass|kiddo|laddie)")
CHILD_WORD = (r"\b(?:" + CHILD_BY_PLACE + r"|kid|kids|baby|babies|toddler|newborn|infant|child|"
              r"children|boy|girl|sons?|"
              r"daughters?|school\s?child|\d+\s*(?:year|month|yr)s?[\s-]*old|(?:one|two|three|four|"
              r"five|six|seven|eight|nine|ten)\s+years?[\s-]*old)\b")

# The colour of a child going downhill, and the second thing that turns the colour into a call.
PALE_SIGN = (
    r"\bpale\b", r"\bpallid\b", r"\bwhite\s+as\s+a\s+sheet\b", r"\bgrey\b", r"\bgray\b",
    r"\bmottled\b", r"\bblue\s+(?:round|around)\s+the\s+(?:lips|mouth)\b",
)
# `_both` pairs two groups and this one wants three, so the lookaheads are written out:
# the child, the colour, and the second thing, in whichever order.
PALE_CHILD = ("(?=.*" + _any_of((CHILD_WORD,)) + ")(?=.*" + _any_of(PALE_SIGN) +
              ")(?=.*" + _any_of(PALE_SECOND) + ") ",)
# The same colour in a grown-up is a different thing, and the advice is not the child's. A child
# goes downhill over hours and is kept warm while the doctor comes; an adult who is pale, grey or
# clammy has lost blood pressure - a bleed, a shock or a heart attack - and is sat down and given
# to the ambulance. Both were answered by nothing: `my husband is pale and clammy` was "Noted:
# your husband is pale and clammy" and `i am pale and clammy` was told to open a window and have
# a cold drink, which is the heat answer and the opposite of what a cold sweat means.
ADULT_PERSON = (
    r"\b(?:husband|wife|partner|boyfriend|girlfriend|fianc\w+|mum|mom|mummy|mother|dad|daddy|"
    r"father|nan|nana|gran|grannie|granny|grandma|grandmother|grandad|grandpa|grandfather|"
    r"sister|brother|aunt|auntie|uncle|cousin|friend|mate|neighbour|neighbor|colleague|"
    r"coworker|flatmate|housemate|lodger|carer|he|she|him|her)\b",
)
ADULT_ME = (
    r"\b(?:i|i'm|im|ive|i've|i\s+am|i\s+feel|i\s+look|i\s+went|i\s+have|me|myself|my\s+own)\b",
)
# Someone, the colour, and the second thing, in whichever order - and a child is not this row.
PALE_ADULT = ("(?=.*" + _any_of(ADULT_PERSON + ADULT_ME) + ")(?=.*" + _any_of(PALE_SIGN) +
              ")(?=.*" + _any_of(PALE_SECOND) + ") ",)
# Pale and sweaty straight after football is a child who has been running about - the colour is
# the effort, not the circulation. A hot day is deliberately not in this list: pale and clammy
# in the sun is heat exhaustion. "my daughter is pale and sweaty after football"
# was a child going downhill. The red signs below still win: a child who is floppy, wont wake,
# going blue or grey is the card whatever they were doing.
# Real exertion: a match, training, a run, the gym, swimming, a bike ride, PE. Sweaty and clammy
# straight after one of these is sweat, and the cooling answer is the right one. The shape is
# generic rather than a longer list of nouns, so "after cross country", "after a 3k race", "after
# the school run" and "after a swimming lesson" are all in it (@magenta-pine's read).
PALE_EXERTION = (
    r"\b(?:after|during|at|from|in)\s+(?:(?:a\s+|the\s+)?(?:\w+\s+){0,2}"
    r"(?:race|run|match|game|session|training|lesson|class|practice|workout|circuit|"
    r"walk|hike|ride)|"
    r"cross\s?country|school\s+run|football|rugby|netball|hockey|the\s+gym|sports?\s+day|"
    r"swimming|a\s+swim|cycling|a\s+bike\s+ride|pe)\b",
    # A named sport after the cue is the same thing - "after gymnastics", "after tennis" - and so
    # is "after his lesson".
    r"\b(?:after|during|at|from|in)\s+(?:his|her|my|their|our|the|a|an)?\s*"
    r"(?:tennis|badminton|squash|cricket|athletics|gymnastics|dance|dancing|ballet|judo|karate|"
    r"martial\s+arts|taekwondo|boxing|climbing|rowing|trampolining|skating|skateboarding|"
    r"snowboarding|skiing|riding|horse\s+riding|sports?|games?|practice|training|workout|walk|"
    r"walking|hike|hiking|ramble)\b",
)
PALE_EFFORT = PALE_EXERTION + PALE_HEAT + (
    r"\b(?:after|during|at|from|in)\s+(?:the\s+)?(?:park|playtime|playground|playing\s+out|"
    r"the\s+beach|nursery|soft\s+play)\b",
    r"\b(?:just|only)\s+been\s+(?:running|playing|out)\b",
)
PALE_EFFORT_REAL = PALE_EXERTION + (
    r"\b(?:just|only)\s+been\s+running\b",
)
# The other half of that fence: the second sign that is never effort. After a match clammy is
# sweat; after the park, playtime or the beach it is the circulation, so those loose places need
# the second sign to be sweat and not one of these.
PALE_EFFORT_NO = (
    r"\bclammy\b", r"\bcold\b", r"\bfloppy\b", r"\blimp\b", r"\bdrows\w*",
    r"\bsleepy\b", r"\bunresponsive\b", r"\bconfus\w*",
)
# The red signs that already have an ambulance answer of their own, so the colour card leaves
# them alone: floppy, hard to wake, not breathing properly. What is left of PALE_EFFORT_RED is
# the colour itself - grey, mottled, blue round the lips - which nothing else answers.
PALE_OTHER_RED = (
    r"\bfloppy\b", r"\blimp\b", r"\b(?:wont|won't|not|can't|cant|unable\s+to)\s+wake\b",
    r"\bunresponsive\b", r"\bunconscious\b", r"\bcollapsed\b",
    # "blue" on its own is the colour this card is for; the lips are the breathing sign that has
    # its own answer above.
    r"\bblue\s+(?:round|around)\s+the\s+(?:lips|mouth)\b",
    r"\bbreathing\s+(?:fast|quickly|hard)\b", r"\bgrunting\b", r"\bnot\s+breathing\b",
)
PALE_EFFORT_RED = (
    r"\bfloppy\b", r"\blimp\b", r"\b(?:wont|won't|not|can't|cant|unable\s+to)\s+wake\b",
    r"\bunresponsive\b", r"\bunconscious\b", r"\bcollapsed\b", r"\bblue\b",
    r"\bgrey\b", r"\bgray\b", r"\bmottled\b", r"\bbreathing\s+(?:fast|quickly|hard)\b",
    r"\bgrunting\b", r"\bnot\s+breathing\b",
)
# Pale and clammy hands are nerves, and a line that never says whose hands they are is asked by
# somebody holding them out: the whole-body version is a person, and this is the fence.
PALE_ADULT_ITSELF = (
    r"\b(?:(?:my|his|her|their|your|our|the|both)\s+)?(?:hands?|feet|fingers|toes|palms?)\s+"
    r"(?:(?:are|is|were|was|feel|feels|felt|go|goes|went|get|gets|got|look|looks)\s+)?"
    r"(?:\w+\s+){0,2}?(?:pale|grey|gray|white|clammy|cold)\b",
)
# ...but only when the hands are the whole of it. "i am pale and clammy and clammy hands" is a
# person describing themselves and then their hands, and it was stood down by the word "hands".
PALE_ADULT_WHOLE = (
    r"\b(?:i|he|she|they|we|you)\s+(?:am|is|are|was|were|look|looks|looked|feel|feels|felt|"
    r"have\s+gone|has\s+gone|went|got)\s+(?:\w+\s+){0,2}(?:pale|grey|gray|clammy|ashen|"
    r"white\s+as)\b",
)
# What makes a grown-up pale and clammy without being an emergency: the heat, the effort, a night
# of drinking, a needle, and a fever that has its own answer.
# The heat and the effort are not in this list: they have their own answer above, and it is a
# better one than leaving the line to whatever else catches it.
PALE_ADULT_FINE = (
    r"\bhangover\w*\b", r"\b(?:been|out)\s+drinking\b", r"\bhung\s?over\b",
    r"\b(?:after|from|at)\s+(?:my|a|the|his|her)\s+(?:blood\s+test|bloods|jab|injection|"
    r"vaccine|vaccination|needle|donation|giving\s+blood|blood\s+donation)\b",
    r"\b(?:with|from|got|has|have|had)\s+(?:an?\s+)?(?:cold|flu|virus|hangover)\b",
    # Pale and clammy with nerves is a body that is frightened, and it passes: the trembling
    # hands answer is the one that helps, not an ambulance.
    r"\b(?:nervous|nerves|anxious|anxiety|panick\w*|panic\s+attack|scared|frightened|"
    r"terrified|stage\s+fright|worried|exam|interview|dentist|needle\s+phobia)\b",
    r"\bgave\s+blood\b", r"\bblood\s+donor\b",
)
NAMED_SICK = (r"\b(?:meningitis|meningococcal|sepsis|blood\s+poisoning|pneumonia|encephalitis|"
              r"necrotis\w+\s+fasciitis|kawasaki\s+disease)\b")
NAMED_SAID = (r"\b(?:has|have|got|caught|diagnosed\s+with|being\s+treated\s+for|"
              r"think\s+(?:its|it's)|think\s+(?:he|she)\s+(?:has|might\s+have)|might\s+have|"
              r"probably\s+has|suspect\w*|getting|coming\s+down\s+with|gone\s+septic|"
              r"going\s+septic)\b")
# Someone, the illness, and the words that say it is going on now, all in one line.
NAMED_ILLNESS_CHILD = ("(?=.*" + PEOPLE + ")(?=.*" + NAMED_SAID + ")(?=.*" + NAMED_SICK + ")",)
# A child's temperature is a number a parent reads out, and 40 is the number they ring about.
HIGH_TEMP = (r"\b(?:39\.[5-9]|4[0-3](?:\.\d)?)\s*(?:c\b|degrees)?",)
# "her temperature is 40.2" is the same sentence without a person word the other rows know.
TEMP_ANCHOR = HUMAN_ANCHOR + (
    r"\b(?:my|his|her|their|the)\s+(?:temperature|temp)\b",
    r"\b(?:my|his|her|their)\s+(?:fever|high\s+temperature)\b",
    # "my 2 year old has a temperature of 40" is the same sentence with the age for a name.
    r"\b(?:my|his|her|their|our)\s+\d+\s*(?:year|month|yr)s?[-\s]*old\b",
)
HIGH_TEMP_CHILD = ("(?=.*" + HIGH_TEMP[0] + r")(?=.*\b(?:temperature|temp|fever)\b)(?=.*"
                   + _any_of(TEMP_ANCHOR) + ")",)
# A child with a temperature is a same-day call even at 38: the number matters less than the age
# next to it, and "my baby has a fever" deserves better than "Got it."
CHILD_FEVER = ("(?=.*" + CHILD_WORD + r")(?=.*\b(?:temperature|temperatures|temp|fever|feverish|"
               r"fevered|hot\s+to\s+(?:the\s+)?touch|hot\s+to\s+touch|boiling\s+hot|"
               r"burning\s+up|hot\s+and\s+(?:shivery|clammy|sweaty|floppy|miserable|grumpy|"
               r"sleepy)|(?:really|very|so|properly|absolutely)\s+hot|feels?\s+(?:hot|warm|"
               r"feverish))\b)",)
# A toddler who drank the gin is the poison call, and "drank" is how the family puts it.
CHILD_DRANK = ("(?=.*" + CHILD_WORD + r")(?=.*\b(?:drank|drunk|swallowed|got\s+into|glugged|"
               r"sipped|downed|sucked|licked)\b)(?=.*\b(?:gin|vodka|whisk(?:y|ey)|beer|wine|"
               r"alcohol|lager|rum|brandy|prosecco|cider|spirits|liqueur|moonshine|schnapps|"
               r"mouthwash|hand\s+saniti[sz]er|aftershave|perfume)\b)",)
# A small child who got at the beer is the poison line; a fifteen-year-old with a can of lager is
# not, so the weak drinks need a young child in the line and the spirits do not.
CHILD_DRANK_WEAK = (r"\b(?:beer|beers|lager|cider|shandy|ale|stout|pint|a\s+sip|a\s+taste|"
                    r"a\s+swig|swig)\b",)
# A fit that has already happened a moment ago is still today's emergency; a fit every few months
# is the condition the family already manages, and "a fit of coughing" is neither.
RECENT_FIT = _both(
    (CHILD_WORD + r"|\b" + PEOPLE + r"\b",),
    (r"\b(?:just\s+had|has\s+had|had)\s+(?:a|another|his\s+first|her\s+first)\s+"
     r"(?:fit|seizure|convulsion)\b",),
)
# Grunting is the sound a small chest makes when it is working too hard, and it is easy to miss.
GRUNTING_BABY = _both(
    (r"\b(?:baby|babies|newborn|infant|toddler)\b",),
    (r"\bgrunting\b|\bgrunts\b",),
)
GRUNTING_NOW = (
    r"\bgrunt\w*\b[^.?!]{0,30}\b(?:breath\w*|every\s+breath|when\s+(?:he|she|they)\s+breathes)\b",
    r"\b(?:blue|floppy|limp|not\s+feeding|wont\s+feed|unresponsive|fever|temperature|"
    r"struggling\s+to\s+breathe|working\s+hard)\b",
)
# "Too sleepy to feed" is how a parent describes a baby who is going downhill.
SLEEPY_FEED = (r"\btoo\s+(?:sleepy|drowsy|tired|floppy|weak)\s+to\s+(?:feed|eat|drink|wake|"
               r"suck|take\s+(?:a\s+)?feed|be\s+woken)\b",
               r"\b(?:wont|won'?t|refus\w+\s+to)\s+(?:feed|take\s+(?:a|his|her)\s+feed|"
               r"wake\s+for\s+(?:a\s+)?feed)\b")

# A fever and a rash together is the pair a parent rings about, whatever the rash looks like.
# A heat rash, a nappy rash, chickenpox and teething are the everyday reasons, and they pass.
FEVER_RASH = ("(?=.*" + _any_of(FEVER_SIGN) + r")(?=.*" + _any_of((RASH,)) + r")(?=.*"
              + _any_of(HUMAN_ANCHOR) + ")",)

STIFF_NECK_RED = _both(STIFF_NECK, MENINGITIS_OTHER + FEVER_SIGN)
SEPSIS = _both(FEVER_SIGN, SEPSIS_SIGN)
# A temperature outside falls: "the temperature keeps falling and im confused about what to wear"
# was the sepsis card on main. The weather is only ever "the temperature", never "his temperature",
# so a possessive keeps the card it always had: a fever that is dropping next to confusion is still
# the person who needs the ambulance.
TEMP_FALLING_WEATHER = (
    r"\b(?:the|outside)\s+temperature\s+(?:is|are|was|were|keeps?|kept|has|had|have)\s+"
    r"(?:been\s+)?(?:falling|dropping|dropped|fell|down|low|going\s+down|below)\b",
    r"\bthe\s+temperature\b[^.?!]{0,25}\b(?:outside|today|forecast|weather|tomorrow)\b",
)
# The fever said as something that is not the thermometer word: a number, "running a temp", the
# fever itself. Any of these and the line is about a body however the temperature is going.
FEVER_NOT_THE_WEATHER = (
    r"\bfever\w*\b", r"\btemps?\b", r"\b\d{2}(?:\.\d)?\s*(?:c\b|degrees)\b",
    r"\bburning\s+up\b", r"\bhot\s+to\s+touch\b", r"\bhigh\s+temperature\b",
    r"\b(?:spiked|went\s+up\s+to|running\s+a\s+temp)\b",
)
FEVER_CASES = frozenset(("red_flags", "stiff_neck", "sepsis_signs", "newborn_fever",
                         "named_illness", "high_temp", "rash_headache", "fever_rash",
                         "child_fever"))
# The two cards that tell a parent how to look after a temperature at home. A disease's name only
# ever takes these away: a stiff neck, a rash that does not fade and a child who is floppy are
# red flags whatever the illness is called, so those cards keep the line.
FEVER_HOME_CARE = frozenset(("child_fever", "high_temp"))
# Some illnesses are called a fever and nobody in the house has a thermometer out: glandular
# fever, scarlet fever, yellow fever, dengue. The word is in the name of the disease, so the
# fever cards read "my daughter has glandular fever" as a child with a temperature and answer
# a how-many-degrees question nobody asked - a same-day 111 call for a child who wants to know
# whether she can play netball. What makes a line a temperature is a fever word that is not
# inside a name: a reading, "hot", "temperature", "burning up".
_A_DISEASE_CALLED_A_FEVER = (
    r"\b(?:glandular|scarlet|yellow|dengue|rheumatic|typhoid|paratyphoid|q|lassa|ebola|marburg|"
    r"crimean-congo|rocky\s+mountain\s+spotted|mediterranean\s+spotted|swine|haemorrhagic|hemorrhagic)"
    r"\s+fever\b",
)
_THE_TEMPERATURE_WORDS = (
    r"\bfever\w*", r"\bfeverish\b", r"\btemps?\b", r"\btemperatures?\b",
    r"\bhot\b", r"\bhot\s+to\s+(?:the\s+)?touch\b", r"\bburning\s+up\b",
    r"\bhigh\s+temperature\b", r"\b\d{2}(?:\.\d)?\s*(?:c\b|degrees)",
)


def _the_only_fever_is_a_disease_name(line):
    """True when every fever word in the line is inside the name of a disease."""
    if not _matches(_A_DISEASE_CALLED_A_FEVER, line):
        return False
    stripped = line
    for pattern in _A_DISEASE_CALLED_A_FEVER:
        stripped = re.sub(pattern, " ", stripped)
    return not _matches(_THE_TEMPERATURE_WORDS, stripped)
# The words that put a fever in the present, even when the line also names a time: "a temp of 39
# since last night", "still burning up", "has had a fever since friday". The story guards use them
# so a child who is ill now is not read as a child who was ill once.
FEVER_STILL_NOW = SEPSIS_SIGN + (
    r"\bsince\s+(?:last\s+)?(?:night|yesterday|friday|saturday|sunday|monday|tuesday|wednesday|"
    r"thursday|this\s+morning|teatime)\b",
    r"\bstill\b", r"\bright\s+now\b", r"\bhas\s+had\b", r"\bstarted\b",
)
# The fever said the way a parent says it, with no word for temperature in it: "my baby is 2 months
# old and feels hot" was the child-fever card (111 and watch for floppiness) when a baby that small
# is seen straight away. The baby has to be the one that is hot, so the hot word comes within a word
# or two of a baby word or of the age said in the line: "my 6 week old feels hot" yes, "the kettle
# is boiling" and "the bath is hot" no.
BABY_HOT_SUBJECT = _any_of((
    r"\b(?:baby|newborn|new\s?born|infant|little\s+one|son|daughter|boy|girl|she|he|they|"
    # the age with or without the "old", since "baby is 7 weeks and feels very hot" is the same
    # baby as "my 7 week old feels hot"; NEWBORN still has to match the line as well, so a thing
    # aged in weeks is not read here.
    r"\d+\s*(?:days?|weeks?|months?)(?:\s+old)?|under\s+(?:3|three)\s+months?)\b",
))
# How small the baby has to be for a hand on the forehead to be the hospital call: under five
# weeks. A parent's hand is not a thermometer, and "feels hot" at seven or ten weeks is the
# same-day 111 card this bot already gives it - three readers of #11074 said the same
# (steward-fleet-blanket, zippy-kangaroo, cream-eel). A stated temperature and a stated strong
# heat are the hospital call at any age under three months, and that is what stays below.
TRUE_NEWBORN = _any_of((
    r"\bnew\s?born\b", r"\bjust\s+born\b", r"\b\d+\s*days?\s*(?:old)?\b",
    r"\b(?:1|2|3|4|one|two|three|four)\s*weeks?\s*(?:old)?\b",
    r"\bunder\s+(?:1|one)\s+month\b",
    r"\b(?:is|only|just|nearly)\s+(?:1|2|3|4|one|two|three|four)\s+weeks?\b",
))
# The ages in TINY_AGE that are five weeks and over, so a later line settling the age the other way
# wins: "my baby is 3 weeks old" then "shes 7 weeks now" is not the newborn's card any more.
TRUE_NEWBORN_FINE = (
    r"\b(?:5|6|7|8|9|10|11|12|five|six|seven|eight|nine|ten|eleven|twelve)\s*weeks?\s*(?:old)?\b",
    r"\b(?:is|only|just|nearly)\s+(?:5|6|7|8|9|10|11|12|five|six|seven|eight|nine|ten|eleven|"
    r"twelve)\s+weeks?\b",
    r"\b(?:1|2|one|two)\s*months?\s*(?:old)?\b",
    r"\b(?:is|only|just|nearly)\s+(?:1|2|one|two)\s+months?\b",
    r"\b(?:under|less\s+than)\s+(?:3|three)\s+months?\b",
)
# A baby named as a baby, or an age used as a noun ("my 3 week old"). A thing is aged with the
# verb: "my laptop is 3 weeks old and feels hot" is a machine that has been running, and the age
# there is a description, not a person. So the plain "feels hot" arm wants one of these as well,
# and the age-as-a-noun arm is only the possessive shape a parent uses.
BABY_NAMED = _any_of((
    r"\b(?:baby|newborn|new\s?born|infant|little\s+one|son|daughter|boy|girl|she|he|they)\b",
    r"\b(?:my|our|his|her|their)\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve)\s*(?:days?|weeks?|months?)\s*old\b",
))
# The heat words that carry a strong fever in themselves, without a number on a thermometer.
BABY_BURNING = (r"\bboiling\b", r"\bburning\s+hot\b")
BABY_IS_HOT = (
    # A stated strong heat is the hospital call at any age under three months: "my baby is 8 weeks
    # old and is burning hot" puts the age and the heat a few words apart, so the copula is what
    # the window is measured from.
    BABY_HOT_SUBJECT + r"[^.?!]{0,7}\b(?:boiling|burning\s+hot)\b",
    BABY_HOT_SUBJECT + r"[^.?!]{0,12}\b(?:is|was|got|has\s+gone)\s+"
    r"(?:really\s+|very\s+|so\s+)?(?:boiling|burning\s+hot)\b",
    # No hedge here: a parent who says "a bit hot" about a two month old is playing it down, and
    # that line is already the same-day 111 call. A plain "feels hot" with no number is the
    # newborn's card only, and the age is taken from the same line.
    r"(?=.*" + TRUE_NEWBORN + r")(?=.*" + BABY_NAMED + r")(?=.*" + BABY_HOT_SUBJECT +
    r"[^.?!]{0,7}\b(?:feels?|is|was)\s+(?:really\s+|very\s+|so\s+)?(?:hot|very\s+hot)\b)",
)
# The age on its own is not a person: `BABY_HOT_SUBJECT` takes a bare "2 months", so
# "my laptop is 2 months old and is boiling" and "my boiler is 2 months old and is boiling" were
# read as a baby with the 999 - the one fence this table exists to hold. Naming the baby as well
# (`BABY_NAMED`) is the same fence the plain "feels hot" arm already carries, and it is asked
# here rather than in the arms so that a real baby's age keeps every window below.
NEWBORN_TEMP = (
    r"(?=.*" + _any_of(NEWBORN) + r")(?=.*" + BABY_NAMED + r")(?=.*"
    + _any_of(FEVER_SIGN + BABY_IS_HOT) + r")",
)
# A fever said about the baby, with the age coming from the line before it (see TINY_AGE): the
# arm keeps its own words here and the memory decides whether it is a baby's line at all.
NEWBORN_NEXT = FEVER_SIGN + (r"\bboiling\b", r"\bburning\s+hot\b", r"\bvery\s+warm\b",
                # "she feels hot", "he is hot", and fast breathing are how a parent says the same
                # thing without the word temperature; the age is already in memory, so these are
                # the tiny baby's lines and nobody else's.
                r"\bfeels?\s+(?:really\s+|very\s+|so\s+)?hot\b",
                r"\bis\s+(?:really\s+|very\s+|so\s+)?hot\b",
                r"\bbreathing\s+(?:fast|quickly|hard)\b")

# A hypo is the diabetic emergency people actually send, and the sign they describe is a person
# who is not themselves - confused, sweating, shaking, slurred, or aggressive out of nowhere.
# Sugar is the first thing, not an ambulance, so the reply says sugar and then the one thing that
# makes it an ambulance (cannot swallow, fitting, unconscious).
DIABETIC = (
    r"\bdiabet\w*\b", r"\btype\s*(?:1|2|one|two)\b", r"\bblood\s+sugar\b", r"\bglucose\b",
    r"\bhypo(?:s|glyc\w*)?\b",
    r"\b(?:blood\s+)?sugar\s+(?:is\s+|was\s+|levels?\s+(?:is\s+|are\s+)?)?"
    r"(?:low|dropped|dropping|dipped|crashing|bottomed\s+out|too\s+low)\b",
    r"\b(?:blood\s+)?sugar\s+level\w*\s+(?:is\s+|are\s+)?(?:low|dropping|dropped)\b",
)
# The meter reading is the sign as well as the subject ("my blood sugar is 1.9"), and it is one
# rule for both tables: SUGAR_READING_LOW lives beside HYPO_SIGN, where a change to the range is
# read by everything that answers a low reading.
DIABETIC = DIABETIC + SUGAR_READING_LOW
HYPO = _both(DIABETIC, HYPO_SIGN)
# A hypo that happened and is over is a story, unless the line says it is still going on.
HYPO_PAST = (
    r"\b(?:yesterday|last\s+night|last\s+week|last\s+month|years?\s+ago|used\s+to|"
    r"when\s+i\s+was|ages\s+ago|this\s+morning|earlier|the\s+other\s+day)\b",
)
HYPO_NOW = (
    r"\b(?:now|right\s+now|at\s+the\s+moment|currently|still|getting|has\s+gone|gone)\b",
)
# A sugar that is low right now is the hypo itself, whatever else the line asks.
# Sugar by mouth is the wrong first move for a person who is fitting or will not wake: they need
# the ambulance, and the glucagon kit if the house has one. Answering "give them juice" to someone
# who cannot swallow is the one way this reply can hurt.
HYPO_NO_MOUTH = (
    r"\b(?:a|another)\s+fit\b", r"\bfitting\b", r"\bseizure\w*", r"\bconvuls\w*",
    r"\bcoma\b", r"\bunconscious\b", r"\bunresponsive\b", r"\bcan'?t\s+stay\s+awake\b",
    r"\b(?:won'?t|wont|not|isn'?t)\s+wak\w*", r"\bout\s+cold\b", r"\bpassed\s+out\b",
    r"\bfainted\b",
)
# A wake-up with a clock time in it is a lie-in, not a person who will not rouse: the same guard
# the ordinary wake-up reply uses. It only stands down a line where the time is the whole sign.
HYPO_LIE_IN = (
    r"\b(?:won'?t|wont|not|never)\s+wak\w*\b[^.?!]{0,20}\b(?:before|until|till|by|at)\s*"
    r"(?:\d{1,2}(?!\d)|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"noon|lunch|midday)\b",
    r"\bwak\w*\s+up\s+at\s+\d{1,2}(?!\d)",
)
LOW_SUGAR_NOW = (
    r"\bhypo(?:s|glyc\w*)?\b",
    # "my sugar was low last night" is a story, so the past tense is not the now arm.
    r"\b(?:sugar|glucose)\b(?!\s+was\b)[^.?!]{0,15}\b(?:low|dropped|dropping|dipped|"
    r"crashing|too\s+low)\b",
)

OBJECT_IN_HEAD_PLACE = r"(?:nose|nostril|ear)(?:s)?"
OBJECT_IN_HEAD = (
    r"\b" + OBJECT_IN_HEAD_THING + r"\b[^.!?]{0,30}\b(?:up|in|inside|into|"
    r"stuck\s+(?:up|in|inside|into)|wedged|lodged)\b[^.!?]{0,25}\b"
    r"(?:my|his|her|their|the|your)?\s*" + OBJECT_IN_HEAD_PLACE + r"\b",
    # "my ear has a bug in it", "my nose had a bead in it": the place first, then what is in it.
    # Blood, wax and snot are not objects, and none of them is in the list above, so a blocked or
    # bleeding nose keeps the answer it has.
    r"\b" + OBJECT_IN_HEAD_PLACE + r"\b[^.!?]{0,25}\b(?:has|have|had|got|with|holding)\b"
    r"[^.!?]{0,25}\b" + OBJECT_IN_HEAD_THING + r"\b",
    r"\bsomething\s+(?:is\s+|'s\s+)?(?:stuck|wedged|lodged)\s+(?:up|in|inside)\s+"
    r"(?:my|his|her|their)\s+" + OBJECT_IN_HEAD_PLACE + r"\b",
    r"\b(?:can'?t|cannot)\s+get\s+(?:it|something|the\s+\w+)\s+out\s+of\s+"
    r"(?:my|his|her|their)\s+" + OBJECT_IN_HEAD_PLACE + r"\b",
)

# The battery is the one that must not wait for urgent care.
OBJECT_IN_HEAD_BATTERY = (
    r"\bbutton\s+batter(?:y|ies)\b",
    r"\b(?:batter(?:y|ies)|magnets?)\b[^.!?]{0,30}\b" + OBJECT_IN_HEAD_PLACE + r"\b",
    r"\b" + OBJECT_IN_HEAD_PLACE + r"\b[^.!?]{0,30}\b(?:batter(?:y|ies)|magnets?)\b",
)

# A blow that lands on a nose or an ear is not an object up it: once "something up a nose" had an
# answer, "my son hit my nose with a toy" was given "leave it alone and get it looked at today" for
# a bruise. Only the struck verbs: bumping a nose on a door is the accident the nose answer suits.
OBJECT_IN_HEAD_BLOW = (
    r"\b(?:hit|hits|hitting|slapp?(?:ed|s|ing)?|punch(?:ed|es|ing)?|head-?butt(?:ed|s)?|kicked?)\b"
    r"[^.!?]{0,30}\b(?:my|his|her|their|the|your)\s+(?:nose|ear|earhole)\b",
)

# The one thing a bone in the throat can do that is an ambulance: it is stopping the swallow.
BONE_RED = (
    r"\b(?:can'?t|cannot|can\s+not|unable\s+to|couldn'?t|not\s+able\s+to)\s+swallow\b",
    r"\bdrool\w*\b", r"\b(?:can'?t|cannot|struggling\s+to|hard\s+to)\s+breathe\b",
    r"\bturning\s+blue\b", r"\b(?:a\s+lot\s+of|lots\s+of|coughing\s+up)\s+blood\b",
)

BONE_STILL = (
    r"\bstill\b", r"\bhasn'?t\s+(?:come|came)\s+out\b", r"\bnever\s+came\s+out\b",
    r"\bsince\s+then\b", r"\bit'?s\s+been\s+(?:stuck|there|in)\b", r"\bleft\s+in\b",
)

OLD_DOWN = (
    r"\b(?:fell|fallen|fall|tripped|slipped|went\s+over|went\s+down|toppled|tumbled|"
    r"collapsed|had\s+a\s+fall|took\s+a\s+tumble)\b",
)

# --- the lines that name a hard emergency and nothing else ------------------------------------
# Someone has been shot: it is a bleeding wound, but the danger is the injury under it, so the
# answer is the ambulance rather than the first aid. A jab, a paintball and a photo are not this.
SHOT_SELF = (
    r"\bi\s+(?:got|gets|was|were|have|had|am|'m|been)\b[^.?!]{0,15}\bshot\b",
    r"\bshot\s+me\b", r"\bthey\s+shot\s+me\b", r"\bi\s+(?:have\s+)?been\s+shot\b",
    # "i shot myself" is the speaker's own wound, and it had no card at all: the line was answered
    # "I'm listening — say more if it helps." "my son shot himself" was worse, a fact filed as one -
    # "Noted: your son shot himself." The verb with a reflexive is the same wound whether it is
    # first person or third, so SHOT reads it and this says whose it is.
    r"\bi\s+(?:have\s+|had\s+)?shot\s+my\s*self\b",
)
# A bone through the skin is an ambulance and a wound to cover, not a support and a lift.
BODY_LIMB = (r"(?:arms?|legs?|wrist|ankle|fingers?|thumb|shin|knee|elbow|shoulder|collarbone|"
             r"jaw|foot|toes?|ribs?|hip|thigh|heel|hands?|forearm)")
BONE_OUT = (
    BODY_LIMB + r"\b[^.?!]{0,25}\bbones?\b[^.?!]{0,25}\b(?:sticking|poking|coming\s+through|"
    r"through|out|show(?:ing|s)?)\b",
    r"\bbones?\b[^.?!]{0,20}\b(?:sticking\s+out|poking\s+out|through\s+the\s+skin|"
    r"out\s+of\s+my\s+" + BODY_LIMB + r")\b",
    r"\b(?:open|compound)\s+fracture\b",
)
# "the chicken bone is sticking out of the bin bag" wears the words of an open fracture; only a
# line with a body part in it, or without the food word, is one.
BONE_OUT_LOOSE = (r"\b(?:bone|wrist|arm|leg)\b[^.?!]{0,25}\b(?:sticking|poking|piercing)\s+out\b",)
FOOD_BONE = (
    r"\b(?:chicken|turkey|lamb|beef|pork|ham|steak|meat|fish|broth|carcass|bin\s*bag|soup|stock|"
    r"skeleton|doll|toy|dog|cat|puppy|kitten)\b",
)
# "how long does a cut avocado last" is the keeping question, and a healing clock answered it:
# the food is what got cut, not a person. Same shape as FOOD_BONE: a food word with no body part
# in the line is not an injury.
# ...but people do cut themselves on a chopping board, so a person in the line still makes it an
# injury: "i cut myself chopping onions" is the first aid, "a cut avocado" is the keeping answer.
# A possessive is not a person: "how long does my cut avocado last" is still the keeping answer,
# and every real cut in the first person names the body part it is on ("i cut my finger"), which
# A_BODY_PART has already spoken for. So only the reflexives make a cut somebody's own.
CUT_SELF = r"\b(?:myself|himself|herself|yourself|ourselves|themselves)\b"
# "how long do cut flowers last" was answered with how long a cut takes to heal: the cut in the
# line is the thing being cut, not a wound. A body part in the line still wins ("i cut my hand"),
# so this only stands the row down when nothing in the line is the person.
NOT_A_BODY_CUT = (
    r"\bcut\s+(?:flowers?|grass|lawn|hedge|hair|bread|costs?|the\s+flowers)\b|"
    r"\b(?:flowers?|vase|bouquet|stems?|tulips?|daffodils?|lilies|carnations?)\b|"
    r"\b(?:haircut|paper\s*cut\s+cost|budget|spending)\b|"
    # A power cut is an outage, not a wound: "how long is food ok in a power cut" and "how long
    # does food last in a power cut" were answered "a small cut closes over in a few days", which
    # is the worst kind of wrong - the person had a fridge full of warm food. A body part in the
    # line still wins ("i cut my finger when the power went off"), because the caller asks for
    # this pattern to stand down only when nothing in the line is the person.
    r"\bpower\s*cut\b|\b(?:power|electricity)\s+(?:cut|outage|failures?|failure|went|goes|gone|"
    r"is|was|back|came)\b|\b(?:lost|losing|lose)\s+(?:the\s+)?(?:power|electricity)\b",
)
BONE_FINE = (
    r"\b(?:chicken|turkey|lamb|beef|pork|ham|steak|meat|fish|broth|dog|cat|puppy|kitten|"
    r"pet|toy|doll|skeleton|bone\s+density|bone\s+scan|x-?ray)\b",
)
# The one headache that is an ambulance: bad *and* out of nowhere, in the same line.
HEADACHE = (r"\bhead(?:ache)?\b",)
HEADACHE_WORST_EVER = (
    r"\bworst\s+head(?:ache)?\s+of\s+my\s+life\b", r"\bworst\s+head(?:ache)?\s+ever\b",
    r"\bnever\s+had\s+a\s+headache\s+like\s+(?:this|it)\b",
)
# A headache with a rash is the meningitis pair, and it is the pair on its own: no fever, no
# stiff neck and none of the words in RASH_RED, which is why "my son has a headache and a rash"
# was a shrug on main. The bare word "head" is deliberately not here - "a rash on my head" is a
# scalp, and "my head is a bit sore" is the ordinary headache module's.
HEADACHE_ANY = (
    r"\bheadaches?\b", r"\bhead\s+hurts?\b",
    r"\bhead\s+(?:is\s+|really\s+|just\s+|has\s+been\s+)?(?:killing|banging|thumping|pounding|"
    r"splitting|sore)\b",
    r"\b(?:killing|banging|thumping|pounding|splitting)\s+headache\b",
)
# A rash with a headache is asked about the whole family, and "my toddler" and "my newborn" are not
# in PERSON: without these words the commonest way a parent writes the line missed the row.
HUMAN_KID = HUMAN_ANCHOR + (
    r"\b(?:baby|babies|toddler|newborn|new\s?born|infant|little\s+one|teenager|teen|lad|"
    r"lass|schoolboy|schoolgirl)\b",
)
RASH_HEADACHE = ("(?=.*" + _any_of((RASH,)) + r")(?=.*" + _any_of(HEADACHE_ANY) + r")(?=.*"
                 + _any_of(HUMAN_KID) + ")",)
# Blood in vomit is an ambulance: it is a bleed inside that nobody can see to press on.
VOMIT_BLOOD = (
    r"\b(?:vomit\w*|throw\w*|threw|thrown|sick|puke\w*|puked)\b[^.?!]{0,20}\b(?:up\s+)?blood\b",
    r"\bblood\s+in\s+(?:my|his|her|their|the)\s+(?:vomit|sick|puke)\b",
    r"\b(?:coffee\s+grounds?)\b[^.?!]{0,20}\b(?:vomit|sick)\b",
)
# The gas-on script is about a ring left burning, and every one of those patterns says
# "cooker". An electric one is named with a word in front of it, and it is not a gas leak:
# "is it safe to leave a slow cooker on overnight" was told to turn it off and open the
# windows. The guard stands down only when nothing in the line says gas, smell or hissing.
ELECTRIC_COOKER = (
    r"\b(?:slow|rice|pressure|multi|electric)\s*-?\s*cooker\b",
    r"\belectric\s+(?:hob|ring|cooker|oven)\b",
    r"\bair\s*fryer\b",
)
GAS_WORD = (
    r"\bgas\b",
    r"\bsmell\w*\b",
    r"\bhissing\b",
    r"\bleak\w*\b",
)


COUGH_FINE = (
    r"\b(?:film|movie|tv|telly|show|series|game|book|novel|story|dream|dreamt|song)\b",
    r"\b(?:last\s+(?:year|month)|years?\s+ago|when\s+i\s+was\s+(?:a\s+)?(?:kid|child|little)|"
    r"used\s+to|had\s+it\s+before)\b",
)

# A line that names a sport keeps the exercise answer, even when the breathing is in it.
BREATH_SPORT = (
    r"\b(?:run|runs|running|jog\w*|gym|swim\w*|cycl\w*|bike|football|rugby|squash|tennis|"
    r"rowing|hiit|zumba|boxing|netball|hockey|marathon|parkrun|spin\s+class|workout)\b",
)
# "my friend was spiked with too much chilli sauce" is a plate of food, and an evening that happened
# years ago is a memory rather than a night out to look after.
SPIKED_STAND_DOWN = (
    r"\b(?:sauce|chilli|chili|curry|salsa|seasoning|food|pizza|joke|prank|meme|coffee\s+order)\b",
    r"\b(?:last\s+(?:year|month)|years?\s+ago|months?\s+ago|when\s+i\s+was\s+(?:a\s+)?"
    r"(?:kid|young|little|at\s+uni))\b",
)

# A film, a game or a party is noise rather than an assault, and the telly is the usual answer.
HEARD_ASSAULT_OFF = (
    r"\b(?:tv|telly|television|film|movie|netflix|episode|boxset|box\s+set|game|game\s+show|"
    r"playstation|xbox|console|radio|podcast|song|music|match|football|party|karaoke)\b",
    r"\b(?:last\s+(?:year|week|month)|years?\s+ago|months?\s+ago|used\s+to)\b",
)

# Faintness, sweating and numbness are how a person describes a heart that is struggling, so an
# effort line that says one of them is not the settling answer.
# Sweat is its own list, because it is not the same kind of red flag as a faint feeling: a hot
# building or a spin class explains it, so it stands the settling answer down but must not stop a
# person being sent to the GP for breathlessness that is new. A faint feeling, a cold clammy skin or
# pain down an arm is the heart's side of the list, and that side is a call rather than a question.
EFFORT_SWEAT = (
    r"\b(?:sweat\w*|clammy)\b",
)
EFFORT_MORE_RED = EFFORT_SWEAT + EFFORT_RED_HEART
# Getting dizzy on the way up out of a chair is a drop in blood pressure: it is the GP's question
# and the water and the sitting down, not the ambulance. "i get breathless on the stairs and dizzy
# when i stand up" was ringing 999 on the previous head.
EFFORT_POSTURAL = (
    r"\b(?:when|as|after|if)\s+i\s+(?:stand|stand\s+up|standing|standing\s+up|get\s+up|getting\s+up|"
    r"stood|stood\s+up|rise|rising)\b",
    r"\bon\s+standing\b|\bstanding\s+up\s+too\s+fast\b",
)
# Pain that travels is the clearest heart line there is, and it is a call whether or not another
# cluster word is there with it: "i cant catch my breath on the stairs and i am sweating and my arm
# hurts" got a vague chat reply on the previous head, which is the one thing it must not get.
EFFORT_TRAVEL_PAIN = (
    r"\b(?:arm|arms|jaw|shoulder|shoulders|neck)\b[^.?!]{0,20}"
    r"\b(?:hurt\w*|pain\w*|ache\w*|tight\w*|heavy|sore|numb)\b",
    r"\b(?:hurt\w*|pain\w*|ache\w*|tight\w*|heavy|sore)\b[^.?!]{0,15}"
    r"\b(?:arm|arms|jaw|shoulder|shoulders|neck)\b",
)
EFFORT_SICK = (
    r"\b(?:feel|feels|feeling|felt)\s+(?:sick|ill|queasy|sickly)\b",
    r"\b(?:queasy|nauseous)\b",
)
# A single "i feel sick" on the stairs is morning sickness, a bug, nerves or the heat. It is the
# cluster only with a second word beside it ("sick and sweaty", "clammy and sick"), so a pregnancy
# line is not read as a heart.
EFFORT_SICK_PAIR = (
    r"\bsick\b[^.?!]{0,24}\b(?:sweat\w*|clammy|faint\w*|dizzy|light-?headed|woozy|pale|grey|gray|"
    r"cold)\b",
    r"\b(?:sweat\w*|clammy|faint\w*|dizzy|light-?headed|woozy|pale|grey|gray)\b[^.?!]{0,24}\bsick\b",
)
# The person who cannot catch their breath is not always the person typing: "my dad cant catch his
# breath after his workout" got the settling answer for the speaker instead of the sitting-upright
# card. Someone else in the line means someone else's emergency.
EFFORT_SOMEONE_ELSE = (
    r"\b(?:my|our|his|her|their)\s+" + PERSON + r"\b",
    r"\b(?:he|she|they)\b\s*(?:'?s|is|was|were|keeps?|kept|can'?t|cant|couldn'?t|couldnt|"
    r"has|had|started)\b",
)
EFFORT_RECOVERY = (
    r"\b(?:catch|caught|get|getting|got|find|finding)\s+(?:my|her|his|their)?\s*breath\b",
    r"\bbreath\s+back\b",
    r"\b(?:out\s+of|short(?:ness)?\s+of)\s+(?:puff|breath)\b",
    r"\b(?:puffed|puffing|winded|blown|breathless)\b",
)


# A nettle, a gnat or a mosquito never swells an airway: a dizzy spell after one is the sting card
# and a lie down. A wasp, a bee or a hornet on the same line is the real stinger.
STING_MILD = (
    r"\b(?:nettles?|mosquito(?:es)?|midges?|gnats?|horse\s?fly|ants?|fleas?|bramble\w*|"
    r"thorns?|thistles?|stingers?\s+weed)\b",
)
STING_WINGED = (r"\b(?:wasps?|bees?|hornets?|bumble\s?bee\w*)\b",)
# The swelling itself, which no settled word stands down.
SWELLING_NOW = LIPS_SWELL_BARE[:3]
# The throat and the tongue are the airway, so neither a settled word nor a nettle stands them
# down: "a wasp stung me and my throat feels funny but im fine now" is the person hoping.
AIRWAY_CHANGED = (r"\b(?:throat|tongue|uvula|lips?)\b",)

LIPS_TINGLE_TRIGGER = (
    r"\b(?:peanuts?|nuts?|tree\s+nuts?|shellfish|prawns?|crabs?|lobster|fish|sesame|egg|eggs|"
    r"milk|soy|wheat|kiwi|strawberr\w*|bee|bees|wasp|sting\w*|stung|allerg\w*|reaction|"
    r"epipen|antihistamine)\b",
)
# A chilli is a tingle in the mouth that no ambulance helps: the burn of the spice is the same
# feeling and it passes.
SPICY_MOUTH = (
    r"\b(?:spicy|spice|chilli|chili|chillies|chilies|hot\s+sauce|wasabi|horseradish|szechuan|"
    r"sichuan|peppercorns?|jalape\w+|naga|scotch\s+bonnet|vindaloo|hot\s+curry)\b",
)
# A throat that has gone thick is the same second sign, but a throat that only feels thick is the
# cold and the drip, so this one is only the airway next to a tingle in the lips or the tongue.
THROAT_THICK = (
    r"\bthroat\b[^.?!]{0,20}\b(?:feels?|is|has\s+gone|has\s+got|going)\s+"
    r"(?:a\s+bit\s+|a\s+little\s+|really\s+|very\s+|so\s+)?thick\b",
)
MOUTH_TINGLE = (
    r"\b(?:tingl\w*|numb(?:ness|ed|ing|s)?|pins\s+and\s+needles|prickl\w*)\b",
)
# The tingle card is about the lips, the tongue and the mouth. A face that has gone numb on one
# side is the stroke answer, and "my face is numb" and "one side of my face is numb" both had it
# before this arm existed, so the face alone does not get the watch-it card.
LIPS_TINGLE_MOUTH = (
    r"\b(?:lips?|tongue|mouth)\b",
)
# A lip that has gone *numb* is a nerve sign and not a tingle: Bell's palsy, a stroke and an
# allergy all start that way, and the cold sore and the toothpaste have nothing to do with a lip
# that cannot feel. The watch-it card needs a tingle in the word - "my lips are numb" keeps
# whatever it had (eager-pineapple, #safety 134176).
LIPS_NUMB = (
    r"\b(?:numb|numbness|dead|gone\s+dead)\b",
)
LIPS_TINGLE_SAID = (
    r"\b(?:tingl\w*|pins\s+and\s+needles|prickl\w*|fizz\w*|buzz\w*|tingly)\b",
)
# ...and when a hand, an arm or a foot is in the line too, the limbs are the story: "my hands and
# lips are tingling" is Raynaud's, which is a thing to be seen about, not a lip tingle with
# nothing behind it. The lip card is for the mouth on its own.
LIPS_LIMB_TOO = (
    r"\b(?:hands?|fingers?|fingertips?|feet|foot|toes?|arms?|legs?|chest|shoulders?)\b",
)
# A mouth that tingles when somebody eats an apple, when they drink a glass of wine or when they
# come in from the cold has its cause in the line, and the cause gets its own answer (the oral
# allergy card, the units card) or the listening line it had before. This card is for the tingle
# with nothing behind it, which is the shape that needs what to watch for.
LIPS_TINGLE_ELSEWHERE = (
    r"\b(?:eat|eats|eating|ate|eaten|food|foods|fruit|fruits|raw|drink|drinks|drinking|drank|"
    r"glass|cup|wine|beer|lager|cider|coffee|tea|fizzy|juice|pineapple|apples?|kiwi|mango|"
    r"avocado|tomatoes?|strawberr\w*|berries|melon|peach\w*|cherr\w*|bananas?|citrus|oranges?|"
    r"lemons?|limes?|nuts?|peanuts?|shellfish|prawns?|sushi|curry|spices?|spicy|chilli|chili)\b",
    r"\b(?:cold|heat|hot|wind|sun|sunburn|freezing|frozen|weather)\b",
    r"\b(?:sting|stings|stung|bee|bees|wasp|wasp\s+sting|bite|bites|bitten)\b",
)
# What a tingle never talks down: a swelling, a swallow that is going, or a breath that is wrong.
LIPS_TINGLE_BREATH = (
    r"\b(?:can'?t\s+breathe|cant\s+breathe|cannot\s+breathe|breath\w*|wheez\w*|stridor|"
    r"can'?t\s+swallow|cant\s+swallow|struggling\s+to\s+swallow|hard\s+to\s+swallow|voice|"
    r"throat\s+(?:is\s+)?(?:tight|tightening|closing|closing\s+up)|airway)\b",
)
# A swallow that has gone is not a sore throat: nothing can be got down, and a quinsy or a bad
# tonsillitis behind it is treatable today and miserable to wait on. "i cant swallow" was
# "Got it. Is there anything you'd like a hand with?" and "i can barely swallow" was
# "Thanks for telling me" (flower-heron, msg 86511). The drooling, the muffled voice and the breath
# are the airway and belong to the 999 cards, so they are the fence rather than the trigger.
SWALLOW_GONE = (
    r"\b(?:can'?t|cannot|can\s+barely|barely\s+can|couldn'?t|unable\s+to|not\s+able\s+to|"
    r"struggling\s+to|struggle\s+to)\s+(?:even\s+)?swallow\b",
    r"\bswallow(?:ing)?\s+(?:is\s+)?(?:impossible|gone|stopped)\b",
)
# The breathing is not the swelling card's to answer: those arms sit above this one and say the
# right thing, so a breath in the line lets them have it.
SWALLOW_GONE_BREATH = (
    r"\b(?:can'?t|cannot|hard\s+to|difficult\s+to|struggling\s+to|unable\s+to)\s+"
    r"(?:breathe|breath)\b",
    r"\b(?:breath\w*|wheez\w*|stridor)\b",
)
# A throat that feels tight with nothing else in the line is nerves, a cold, a long day of talking
# or hayfever far more often than it is the airway. It is not a shrug either: it is the same-day
# call, with the escalation said out loud.
THROAT_TIGHT = (
    r"\bthroat\b[^.?!]{0,14}\b(?:feels?|feeling|is|'s)\s+(?:really\s+|very\s+|a\s+bit\s+)?"
    r"(?:tight|tightening|tightened|closed\s+up)\b",
    r"\b(?:tight|tightening)\s+throat\b",
)
THROAT_TIGHT_MILD = THROAT_TIGHT_CAUSE + (
    r"\b(?:a\s+bit|a\s+little|slightly)\b",
    # a hedged swelling anywhere on the body is not the airway on its own
    r"\b(?:lips?|face|eyelids?|cheeks?)\b[^.?!]{0,20}\b(?:a\s+bit|slightly|a\s+little)\b",
)
LIPS_SWELL_OFF = (
    r"\b(?:cold\s+sore|chapped|chaps|dry\s+lips|chap\s?stick|lip\s+balm|piercing|"
    r"filler\w*|collagen|cosmetic|sunburn|sun\s+burn|gloss|lipstick|blister)\b",
    r"\b(?:last\s+(?:year|summer|month)|years?\s+ago|as\s+a\s+(?:kid|child))\b",
)

# "the bleeding wont stop" with no site and no volume is a person staring at a wound: pressure
# first, and the step up only if it soaks through or they go pale.
NOT_STOPPING_BARE = (
    r"\b(?:won'?t|wont|doesn'?t|doesnt|isn'?t|isnt|not|never|keeps?)\s+(?:on\s+)?stopp?(?:ed|ing)?\b",
    r"\b(?:still|keeps?)\s+(?:on\s+)?bleeding\b",
)
WOUND_NAMED = (
    r"\b(?:cut|wound|gash|slice|scratch|arm|leg|hand|finger|thumb|head|scalp|foot|toe|knee|elbow|"
    r"face|mouth|tongue|lip|gum|nose|ear|tattoo|pierc\w*|wrist|thigh|neck|eye|chest|belly|"
    r"stomach|back|bottom)\b",
)
# A nose is the one site where the amount of blood says nothing: a nosebleed runs hard and stops
# with ten minutes of pinching, so "my nose is bleeding a lot" was the ambulance because the volume
# was all the bleeding case read. The nose keeps its own card unless something on the line makes it
# the exception: blood that will not stop, ten minutes or more already gone, a blood thinner, going
# pale or faint, or a knock to the head, which is the head injury's question anyway.
NOSE_SITE = (r"\bnoses?\b", r"\bnostrils?\b", r"\bnose\s*bleed\w*\b")
BLEED_VOLUME = (
    r"\b(?:heavily|a\s+lot|pouring|dripping|soaking|soaked|everywhere|loads|badly|gushing|"
    r"spurting|pulsing)\b",
)
# A bitten tongue, a cut lip or a gum can bleed impressively and still stop with pressure: that is
# the soak-through answer and a same-day look, not an ambulance.
MOUTH_BLEED = (r"\b(?:tongue|lip|lips|gums?|mouth|cheek\s+inside|tooth\s+socket|palate)\b",)
# Blood in the mouth looks worse than it is, so the volume alone does not make it an ambulance: only
# going pale, dizzy or faint, or a cut that is deep, does.
MOUTH_BLEED_RED = (r"\b(?:pale|grey|gray|dizzy|faint|clammy|unconscious|shaking|deep\s+cut|gaping)\b",)
# A gum that bleeds when you brush it is a dentist-and-floss question, and an ulcer is not a wound.
MOUTH_BLEED_OFF = (
    r"\bbrush\w*\b", r"\bfloss\w*\b", r"\b(?:my|the)\s+gums?\b[^.?!]{0,20}\bbleed\w*\b",
    r"\bdentist\b", r"\b(?:ulcer|sore)\b",
)

# A pregnancy line is often about someone else - "my wife is 8 weeks pregnant and can't keep
# anything down" - and the reply is written to the user, so it has to say whose midwife to ring.
EXPECTING_OTHER = (
    r"\bmy\s+(?:wife|girlfriend|partner|friend|mate|sister|daughter|cousin|colleague|neighbour|"
    r"neighbor|flatmate|housemate|mum|mom|dad|husband|boyfriend|niece|aunt)\b",
    r"\bshe\s+is\s+(?:pregnan\w*|expecting)\b",
)
def _for_the_person(reply, line, case):
    """A pregnancy reply about someone else, told to the user as what to do for them."""
    if not reply or not case or not case.startswith("pregnancy_"):
        return reply
    if not _matches(EXPECTING_OTHER, line):
        return reply
    she = _person(line) != "he"
    obj, subject = ("her", "she") if she else ("him", "he")
    text = re.sub(r"\byou're\b", subject + "'s", reply, flags=re.I)
    text = re.sub(r"\byou've\b", subject + "'s", text, flags=re.I)
    text = re.sub(r"\byour\b", obj, text, flags=re.I)
    # Object before subject: "stops you keeping" is "stops her keeping", not "stops she keeping".
    for verb in ("stops", "stop", "leave", "leaves", "get", "gets", "keep", "keeps", "make",
                 "makes", "take", "takes", "tell", "tells", "with", "for", "to"):
        text = re.sub(r"\b" + verb + r"\s+you\b", verb + " " + obj, text, flags=re.I)
    text = re.sub(r"\bthat\s+needs\b", subject + " needs", text, flags=re.I)
    text = re.sub(r"\byou\b", subject, text, flags=re.I)
    # "if she also feel faint" is not English: the verb has to agree with the one person.
    text = re.sub(r"\b(she|he)\s+((?:also|still|just|only)\s+)?(" + "|".join(map(re.escape, _THIRD)) +
                  r")\b",
                  lambda m: m.group(1) + " " + (m.group(2) or "") + _THIRD[m.group(3).lower()],
                  text, flags=re.I)
    # "Ring her midwife today" said to the user is an order they cannot carry out themselves.
    if re.match(r"(?i)^ring\b", text):
        text = "Tell " + obj + " to ring " + text[4:].lstrip()
    return text[:1].upper() + text[1:]
# Sickness in pregnancy that stops you keeping food or drink down is the hyperemesis picture: it
# needs the midwife or GP the same day and can mean dehydration. Both halves have to be in the
# same line, in either order - "i'm pregnant and craving pickles" is not this.
# "im not pregnant but i cant keep anything down" is a sick person, not a pregnant one, so a
# denied pregnancy never opens any of the pregnancy cases.
# \A anchors the guard to the whole line: a bare (?!...) lookahead lets re.search slide one
# character forward and match the rest of the line past the "not".
NOT_PREG = (r"\A(?!.*\b(?:not|isn'?t|aren'?t|never|no\s+longer|stopped\s+being)\s+"
            r"(?:be\s+|been\s+)?(?:pregnant|pregnancy|expecting)\b)")
SICK_WORDS = (r"(?:can't|cannot|can\s+not|unable\s+to|struggling\s+to)\s+keep\b")
PREGNANCY_SICK = (
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)(?=.*\b" + SICK_WORDS + r")"
    r"(?=.*\b(?:food|water|drink|drinks|fluids?|meals?|anything|down)\b)",
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"(?=.*\b(?:throwing\s+up|being\s+sick|vomit\w*|puking)\b)"
    r"(?=.*\b(?:always|all\s+day|all\s+the\s+time|constantly|everything|non.?stop|every\s+day|"
    r"for\s+(?:weeks|days))\b)",
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)(?=.*\bsick\b)"
    r"(?=.*\b(?:all\s+day|all\s+the\s+time|constantly|every\s+day|everything)\b)",
    # "i cant stop vomiting" is the same picture said as a sentence about stopping.
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"(?=.*\b(?:can'?t|cannot|can\s+not)\s+stop\s+"
    r"(?:vomiting|puking|being\s+sick|throwing\s+up|sick)\b)",
)
# A question about normal sickness gets an answer, not an ambulance: what helps, and the line
# where it stops being normal.
PREGNANCY_SICK_Q = (
    r"\bmorning\s+sickness\b",
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"(?=.*\b(?:is\s+it\s+normal|normal|usual)\b)"
    r"(?=.*\b(?:sick|nauseous|nausea|queasy|vomit\w*|throwing\s+up)\b)",
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"(?=.*\b(?:how\s+long|what\s+helps|any\s+advice|tips)\b)"
    r"(?=.*\b(?:sick|nauseous|nausea|queasy|vomit\w*|morning)\b)",
    # Feeling sick in the morning, with nothing said about keeping food down, is the ordinary
    # picture: an answer that helps and names the line where it stops being ordinary.
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"(?=.*\b(?:i\s+feel|feeling|i\s+am|i'?m|being|so)\s+(?:sick|nauseous|queasy)\b)",
)
# The other pregnancy red flags: a bleed, a baby that has gone quiet, and waters breaking early.
# All three are "ring the maternity unit now", never "wait and see", and each needs the pregnancy
# word in the line so an ordinary bleed or a kicking baby stays ordinary.
PREGNANCY_BLEED = (
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"\A(?!.*\b(?:no|not|isn'?t|never|stopped)\b.{0,12}\b(?:bleed\w*|blood|spotting)\b)"
    r"(?=.*\b(?:bleed\w*|bled|blood|spotting)\b)",
)
PREGNANCY_QUIET = (
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"(?=.*\b(?:no\s+movement|not\s+moving|isn'?t\s+moving|stopped\s+moving|"
    r"less\s+movement|fewer\s+kicks|not\s+kicking|hasn'?t\s+moved|hasn'?t\s+kicked|"
    r"stopped\s+kicking|no\s+kicks)\b)",
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"(?=.*\b(?:hasn'?t|haven'?t|not|isn'?t|didn'?t)\s+(?:felt|feel|been\s+feeling)\b"
    r".{0,25}\b(?:move|moves|moving|kick|kicks|kicking)\b)",
)
# The waters are always the person's own: "the water broke on my bike" and "my car is leaking
# fluid" are not a labour, so the bare word is not enough without a "my" in front of it.
PREGNANCY_WATERS = (
    r"\bmy\s+waters?\s+(?:have\s+|has\s+)?(?:broke|broken|gone|went|leak\w*)\b",
    r"\bmy\s+waters?\s+(?:are\s+|is\s+)?leak\w*\b",
    r"\b(?:i'?m|im|i\s+am)\s+leaking\s+(?:fluid|waters)\b",
    r"\bi\s+think\s+my\s+waters?\b",
)
SOCKET_SHOCK = _both(
    (r"\b(?:got|get|gets|getting|had|has|have|took)\s+(?:a\s+|an\s+|the\s+)?"
     r"(?:electric(?:al)?\s+|nasty\s+|bad\s+|real\s+|proper\s+|little\s+)?shock\b",),
    (r"\b(?:socket|sockets|plug\s+socket|wall\s+socket|outlet|power\s+point|mains|"
     r"live\s+wire)\b",),
)
# "Electrocuted" is the word people reach for when the shock was survived, and on main
# `my husband was electrocuted` was answered with a condolence - "I'm sorry, that's a real loss" -
# because the loss module reads "was electrocuted" as a death, and `i got electrocuted at work` was
# a shrug. Both are the same live question: is the supply off, and does this need a check. A line
# that says the person died keeps its condolence, and a shock from years ago is a story.
ELECTRIC_SHOCK = (
    r"\belectrocut\w*\b",
    r"\b(?:got|get|gets|getting|had|has|have|took|suffered)\s+(?:a\s+|an\s+|the\s+)?"
    r"(?:electric(?:al)?\s+shock|shock\s+(?:from|off|of))\b",
    r"\b(?:shock(?:ed)?|zapped)\s+(?:from|off|by)\s+(?:a|the|my|an|our)\s+"
    r"(?:socket|plug|wire|cable|lead|mains|fuse\s?box|switch|kettle|charger)\b",
    r"\b(?:touched|grabbed|held|caught)\s+(?:a\s+|the\s+)?live\s+(?:wire|cable|rail|terminal)\b",
    r"\blive\s+wire\b[^.?!]{0,20}\b(?:shock\w*|burn\w*|spark\w*)\b",
    SOCKET_SHOCK[0],
)
# "my son put a fork in the socket" had nothing at all: not the shock card, because no shock was
# said, and not anything else, because a socket is not a thing the other modules know. A thing in
# the socket is the shock waiting to happen, and a shock that names what it came off is the shock.
SOCKET_WORD = (r"\b(?:socket|sockets|plug\s+socket|wall\s+socket|outlet|power\s+point|"
               r"mains|plug\s+hole|the\s+plug)\b",)
SOCKET_POKE = (r"\b(?:put|puts|putting|stuck|sticking|stick|poked|poking|poke|shoves?|shoving|"
               r"shoved|pushes|pushing|pushed|jams?|jam(?:med|ming)?|forced|forcing|inserted|"
               r"inserting|plays?|playing|chews?|chewed|chewing|licks?|licked|bit|licks)\b",)
# A thing in a socket is not the plug: the verb, the thing and the socket all have to be there, so
# "the plug is stuck in the socket" and "i put the plug in and nothing happened" stay ordinary.
SOCKET_THING = (
    r"(?=.*" + _any_of(SOCKET_POKE) + r")(?=.*" + _any_of(SOCKET_OBJECT) + r")"
    r"(?=.*" + _any_of(SOCKET_WORD) + r")",
)
# The same question asked as how to stop it: the answer is the card, because it names the blanking
# plugs and the RCD.
SOCKET_COVER = _both(
    (r"\b(?:child\s?proof\w*|child\s?safe\w*|baby\s?proof\w*|blanking\s+plugs?|"
     r"socket\s+covers?|covers?\s+(?:for|on)\s+(?:the\s+)?sockets?)\b",),
    SOCKET_WORD,
)
# The wires that make a shock real, whatever else the line says.
ELECTRIC_SHOCK_WIRED = (
    r"\b(?:socket|plug|wire|cable|lead|mains|fuse\s?box|kettle|charger|voltage|live\s+wire)\b",
)
# The death said after the shock: "electrocuted and passed away" is a condolence, and "passed
# away" is how most people say it, next to "didnt make it" which they type without the apostrophe.
ELECTRIC_SHOCK_DEATH = (
    r"\b(?:died|killed|dead|fatal|didn'?t\s+make\s+it|did\s+not\s+make\s+it|pronounced|"
    r"passed\s+(?:away|on)|lost\s+(?:him|her|them))\b",
)
# A shock off a car door in a car park, a trolley or a blanket is static, and it is not a 999
# question: it is the same everyday spark everyone gets.
ELECTRIC_SHOCK_STATIC = (
    r"\b(?:static|car\s+door|door\s?handle|door\s?knob|trolley|handrail|blanket|jumper|"
    r"fleece|carpet|metal\s+pole|the\s+dog|the\s+cat|shelf)\b",
)
# The floor, said every way people type it. "felt faint" is deliberately not here: feeling faint is
# the sit-down card, and it is the losing of the few seconds that makes this the ambulance.
ELECTRIC_SHOCK_FLOOR = (
    r"\b(?:passed\s+out|passing\s+out|out\s+cold|knocked\s+out|collaps\w*|fainted|fainting|"
    r"unconscious|unresponsive|blacked\s+out|keeled\s+over|in\s+a\s+heap|went\s+limp)\b",
)
ELECTRIC_SHOCK_FLOOR_LINE = _both(SHOCK_ANY, ELECTRIC_SHOCK_FLOOR)
# A shock that is not electricity. The card's first instruction is to turn the supply off, so on
# bad news it sends somebody looking for a fuse box that has nothing to do with it: "i was in
# shock after the crash and i passed out" is the collapse, and "the news gave me such a shock i
# blacked out" is a faint - the words "shock" and "passed out" are the same words, and the cause
# in the line is what decides which card answers.
ELECTRIC_SHOCK_NOT_ELECTRIC = (
    r"\b(?:crash|collision|accident|news|phone\s*call|grief|bereave\w*|funeral|diagnosis|"
    r"test\s+results|results|letter|bill|price|quote|scare|scared|fright|surprise|"
    r"jump\s*scare)\b",
)
# ...unless the line says the electricity in it anywhere, which makes the cause a detail of the
# accident: "the power line came down in the crash and i got a shock" is still the supply.
ELECTRIC_SHOCK_SUPPLY = (
    r"\b(?:electric\w*|electrocut\w*|socket|plug|wire|cable|lead|mains|voltage|volt\w*|fuse|"
    r"power|pylon|substation|zapped|battery|charger|live|shorted?|shorts)\b",
)
# A shock that nearly put someone on the floor is the shock card's business, not this one: "i got a
# shock and nearly passed out" is a same-day check, and so is the figure of speech.
ELECTRIC_SHOCK_NEARLY = (
    r"\b(?:nearly|almost|close\s+to|thought\s+(?:i|he|she|they)\s+(?:was|were)\s+(?:going\s+to|"
    r"about\s+to)|felt\s+like\s+(?:i|he|she|they)\s+(?:was|were)\s+(?:going\s+to|about\s+to)|"
    r"could\s+have)\b",
)
# A person who is not breathing after a shock is a resuscitation, and the recovery position is the
# wrong answer for them: the CPR card is the one to give.
ELECTRIC_SHOCK_CPR = (
    r"\b(?:not|isn'?t|isnt|wasn'?t|wasnt|stopped|won'?t|wont)\s+breath\w*\b",
    r"\bno\s+(?:pulse|heartbeat)\b",
    r"\b(?:cpr|resuscitat\w*)\b",
)
ELECTRIC_SHOCK_STORY = (
    r"\b(?:years?\s+ago|last\s+year|when\s+(?:he|she|they|i)\s+was\s+(?:a\s+)?(?:kid|child|"
    r"young|little|small)|as\s+a\s+(?:kid|child)|back\s+in\s+\d{4}|decades?\s+ago)\b",
)
# Pre-eclampsia is said as a headache and funny vision rather than as a disease name: a bad
# headache, blurring or flashing lights, or swelling of the face and hands in a pregnancy is a
# call to the maternity unit the same day, and 999 if she feels very unwell. Each arm needs both
# the pregnancy word and the sign, so an ordinary headache stays ordinary. Swelling of the face,
# of the hands or of the fingers is the sign itself in a pregnancy, so it does not have to arrive
# overnight; the feet and ankles are the ones that swell anyway and are not in these lists.
PREGNANCY_BP = (
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"(?=.*\b(?:bad|really\s+bad|severe|worst|pounding|splitting|banging)\s+headache\b)",
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)(?=.*\bheadache\b)"
    r"(?=.*\b(?:blurr\w*|vision|double\s+vision|flashing\s+lights|seeing\s+(?:spots|stars)|"
    r"lights?\s+in\s+front\s+of\s+my\s+eyes)\b)",
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"(?=.*\b(?:blurr\w*\s+vision|double\s+vision|flashing\s+lights|seeing\s+spots|"
    r"vision\s+(?:is\s+)?(?:blurr\w*|funny|odd|going))\b)",
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"(?=.*\b(?:swell\w*|swoll\w*|puffy|puffiness|puff\w*\s+up)\b.{0,25}"
    r"\b(?:face|hands|hand|fingers|arm|arms)\b)",
    NOT_PREG + r"(?=.*\b" + PREGNANCY_WORDS + r"\b)"
    r"(?=.*\b(?:face|hands|hand|fingers|arm|arms)\b.{0,25}"
    r"\b(?:swell\w*|swoll\w*|puffy|puffiness|puff\w*\s+up)\b)",
)
# "there is blood in my pants" is a period or a surprise rather than a poo, and main answered it
# with the period talk. It is only the stool card when the line also names a poo.
POO_PANTS = (
    r"\b(?:pants|underwear|knickers|boxers|boxer\s+shorts|briefs|drawers|undies|pyjamas?)\b",
)
POO_WORD = (
    r"\b(?:poo|poos|pooed|poop|pooped|stool|stools|shit|shitted|bowel\s+movement|number\s+two|"
    r"faeces|feces|diarrhoea|diarrhea)\b",
)
# A hot meal, a takeaway or a lot of chilli is a reason to give it a day before ringing anybody.
POO_MEAL = (
    r"\b(?:after|from|because\s+of)\s+(?:a\s+|the\s+|some\s+)?(?:curry|spicy\s+\w+|takeaway|"
    r"take-?out|kebab|chilli|chili|indian|mexican|thai|hot\s+sauce|tabasco|jalape\w+|"
    r"peri\s+peri|piri\s+piri|nando'?s|pizza|beetroot|beet\s+juice)\b",
)
# ...unless the same line says they are pale, faint, weak or bleeding heavily, which is the body
# talking rather than the meal.
POO_RED = (
    r"\b(?:faint|fainted|dizzy|light-?headed|pale|grey|gray|clammy|weak|shaking|sweating|"
    r"heavy|heavier|a\s+lot|lots\s+of|pouring|clots?|clotted|gushing|soaked|soaking|can'?t\s+stand|"
    r"passed\s+out)\b",
)

# A torsion is sudden; a dull ache that has been there for weeks is not one, and telling somebody
# their pain "came on suddenly" when their own line says otherwise is wrong. So the ache words only
# count with an onset or a sign that is not an ache, and a long-standing line gets the seen-today
# reply rather than the hours-one.
TORSION_HARD = (
    r"\b(?:swollen|swelling|swoll|hard|firm|twisted|torsion|high\s+up|retracted)\b",
)
# Being sick beside a sore testicle is one of the signs the card itself names, so it opens the same
# case as a swelling does - unless the line plays it down.
TORSION_SICK = (
    r"\b(?:feel|feeling|be|being|been|am|im|is|was)\s+(?:really\s+|very\s+|so\s+)?sick\b",
    r"\bvomit\w*|throwing\s+up|thrown\s+up|nausea\w*",
)
TORSION_MILD = (
    r"\b(?:a\s+bit|a\s+little|slightly|mild|bit\s+of|sort\s+of|kind\s+of)\b",
)
TORSION_LONG = (
    r"\b(?:for\s+(?:a\s+|the\s+last\s+|about\s+a\s+|over\s+a\s+)?(?:\d+\s+)?(?:days?|weeks?|"
    r"months?|years?)|since\s+(?:last\s+year|christmas|the\s+summer)|weeks\s+now|months\s+now|"
    r"years\s+now|a\s+while\s+now|ages)\b",
)
# The signs that make it an ambulance whatever the calendar says.
TORSION_RED = (
    r"\b(?:severe|unbearable|agony|excruciating|worse|getting\s+worse|vomit\w*|being\s+sick|"
    r"throwing\s+up|fever|temperature|hard|firm|discolou?red|purple|black|blue\s+and|twisted)\b",
)
PUNCTURE_OFF = (
    r"\b(?:tyre|tire|wall|hammer|picture|shelf|fence|hanging|lego|block|bike|car|laptop|"
    r"shoe\s+rack|nail\s+varnish|fingernail|toenail|carpet)\b",
    r"\bhit\s+the\s+nail\b",
)
# A burst appendix is an ambulance: the pain is in the belly, so nobody at home can tell it from
# the colic, and waiting is the one thing that makes it worse.
APPENDIX = (
    r"\bappendix\b[^.?!]{0,30}\b(?:burst|bursting|ruptured|rupturing|has\s+gone|gone)\b",
    r"\b(?:burst|bursting|ruptured|rupturing)\s+(?:my\s+|his\s+|her\s+|their\s+)?appendix\b",
    r"\bappendicitis\b[^.?!]{0,25}\b(?:burst|ruptured)\b",
)
# A toddler falls over on the rug every day of the week, and the same-day check for it teaches a
# parent to ignore the card. This one is read after the red flags, so "she fell over and is sleepy"
# is still the ambulance and only the fall with nothing after it is a tumble.
BABY_FELL_OVER = (
    r"\bfell\s+over\b(?!\s+(?:and|then|onto|off|from|down|hitting|banging|cutting))",
)

# "my grandad hung himself" is a death that already happened, so the rescue script is the wrong
# reply: there is nobody to get down. The scene - "i found my dad hanging" - is still the call.
HANGED_DONE = (
    r"\b(?:hung|hanged)\s+(?:him|her|them)sel(?:f|ves)\b",
)
# ...and only when the person it happened to is a grandparent. "my grandad hung himself" is a man
# who died years ago, and the rescue script has nobody to get down; but "he hung himself" and
# "my brother hanged himself" are somebody who may be in the next room, so the neck answer is the
# only safe one there. Urgency words still win either way.
ELDER_KIN = (
    r"\b(?:nan|nana|gran|granny|grandma|grandmother|grandad|granddad|grandpa|grandfather)\b",
)
# ...and the other way people say it is already over: they name the death. "my aunt hanged
# herself, she died" is a funeral, not a rescue, and the death word is stronger evidence of the
# past than the person being a grandparent is.
DEATH_SAID = (
    r"\b(?:died|dead|death|funeral|buried|burial|passed\s+away|cremat\w*|inquest|grave|"
    r"anniversary|memorial|headstone)\b",
)
# "she hung herself at university" is somebody's student years, but "my son hung himself at
# school" is a parent typing today, so the place is only the past when the person is not a young
# one of the speaker's.
SCHOOL_PLACE = (
    r"\bat\s+(?:school|uni|university|college|sixth\s+form)\b",
)
YOUNG_KIN = (
    r"\b(?:son|daughter|child|kid|boy|girl|baby|toddler|teen|teenager|stepson|stepdaughter|"
    r"grandson|granddaughter|nephew|niece)\b",
)
# ---------------------------------------------------------------------------
# A person struck by a vehicle is a 999 call.
#
# Nothing on main read this as an emergency: "my son got hit by a car" was "I'm listening - say
# more if it helps.", "my child got hit by a car" was the road-trip packing list, and the worst
# phrasing - "my son was knocked down by a car and is bleeding" - reached the car-*buying* row
# ("talk to the salesperson, not whoever greets you"), because "knocked down" and "car" were the
# only two words anything looked for. A person of any age who has been hit by something on the
# road is a 999 call, and the two halves of that are what this reads: the person and the strike
# with the vehicle after "by", or the vehicle first with the person after the verb.
#
# Every rule below is a guard against taking a turn that is not that:
#
# * a near miss is a fright, not an injury: "i nearly got hit by a car" wants the fear answer.
# * "what if" and "imagine" are a worry about a road, not a call now, and a collision years ago -
#   "when i was a kid", "in 1998", "last summer" - is history rather than an ambulance.
# * a shunt is one car into another: "a van hit us from behind this morning" is the passenger
#   talking to their insurer, and "do not move them" is not the answer to that.
# * a pet under a car is the vet's call, not this one ("my puppy got out and a car clipped him").
# * a car hit by a car, a fence hit by a car and a door swung into somebody are all somebody
#   else's case: the vehicle has to strike a *person*, and "hit by a car door" is a bruise.
_STRUCK_VEHICLE = (r"(?:car|cars|van|vans|lorry|lorries|truck|trucks|bus|buses|coach|taxi|cab|"
                   r"bike|bikes|bicycle|motorbike|motorcycle|scooter|moped|tram|train|tractor|"
                   r"digger|forklift|police\s+car|fire\s+engine)")


# Somebody a vehicle can strike. The bare person word has to be there, so "my car got hit by a
# van" and "my fence got hit by a car" are not this.
# A person after "a" is still a person: "a car hit a man outside my house" and "a bike hit a
# pedestrian" are the call the rest of this row is for, and the article was the only thing
# missing, so both fell to the greeting (deft-bear's sweep, #safety 84106). A vehicle has to be
# doing the striking for the row to be read at all, so "the bus hit a wall" is untouched.
_STRUCK_PERSON = (r"(?:i|me|he|him|she|her|they|them|us|we|someone|somebody"
                  r"|(?:my|his|her|their|our|the|your|a|an|some)\s+" + _STRUCK_RELATIVE +
                  r"|" + _STRUCK_RELATIVE + r")")

_STRUCK_VERB = (r"(?:hit|hits|hitting|struck|strikes|knocked\s+(?:down|over)"
                r"|knocks\s+(?:down|over)|ran\s+over|run\s+over|runs\s+over|clipped|clips"
                r"|mowed\s+down|collided\s+with)")

# The people a blow in the house is about: "my husband nearly hit me in the street" keeps the abuse
# card, and the road place in the line does not take it away.
NEAR_HIT_ON_A_ROAD_NOT = (r"\b(?:my|his|her|our|their|your)\s+" + _STRUCK_RELATIVE + r"\b",)

# The part of a person a wheel goes over. "a van ran over my foot" is a foot under a van, and no
# row read it: the hazard-lights script answered instead, which is for the driver who hit somebody.
_STRUCK_BODY = (r"(?:my|his|her|their|our|your)\s+"
                r"(?:foot|feet|leg|legs|hand|hands|arm|arms|toe|toes|ankle|ankles|knee|knees)")

# Run over needs no vehicle named: "my son got run over" and "someone got run over outside my
# house" are the same call, and both were read as a death because nothing else looked at them.
# The verb has to be about the person, so "run over the plan" is not this (see STRUCK_NOT_NOW).
_STRUCK_RUN_OVER = (r"\b" + _STRUCK_PERSON + r"\b[^.?!]{0,20}\b"
                    r"(?:got|get|gets|was|were|is|are|been|had\s+been|has\s+been|just|suddenly)?\s*"
                    r"(?:run|ran|runs)\s+over\b"
                    # ...but what follows "over" has to be a person or nothing: "they ran over my
                    # fence" and "run over the plan" are objects, and a particle cannot take them.
                    r"(?!\s+(?:the|a|an|my|our|his|her|their|your|some|any|it|this|that|to)\b)")

# A pet under a wheel is the vet's call, and this row is the one that reads the wheel, so it is
# the one that has to hand the line over rather than let it fall to the bereavement card.
_STRUCK_PET = (r"\b(?:my|our|the|his|her|their)\s+(?:dog|dogs|puppy|cat|cats|kitten|rabbit|horse|"
               r"pony|hamster|parrot|budgie|guinea\s+pig)\b")

STRUCK_BY_VEHICLE = (
    # "my son got hit by a car", "i was knocked down by a bus", "he was run over by a van".
    r"\b" + _STRUCK_PERSON + r"\b[^.?!]{0,25}\b" + _STRUCK_VERB + r"\s+by\s+(?:a\s+|an\s+|"
    r"the\s+|his\s+|her\s+|their\s+|my\s+|our\s+|your\s+)?" + _STRUCK_VEHICLE +
    r"\b(?!\s+door)",
    # "a car hit me", "the bus hit my son", "a lorry struck him".
    r"\b(?:a|an|the|some|one|his|her|their|my|our)\s+" + _STRUCK_VEHICLE + r"\b[^.?!]{0,20}\b"
    r"(?:hit|hits|struck|strikes|clipped|clips)\s+" + _STRUCK_PERSON + r"\b",
    # "a car knocked my son down" - the person sits inside the verb.
    r"\b(?:a|an|the|some|one|his|her|their|my|our)\s+" + _STRUCK_VEHICLE + r"\b[^.?!]{0,20}\b"
    r"(?:knocked|knocks|ran|run|runs|mowed)\s+" + _STRUCK_PERSON + r"\s+(?:down|over)\b",
    # "a car ran over my son" and "a van ran over my foot" - the vehicle first, "over" in the
    # middle. Only the two run-over phrasings put "over" before the person, which is why they
    # reached the hazard-lights answer.
    r"\b(?:a|an|the|some|one|his|her|their|my|our)\s+" + _STRUCK_VEHICLE + r"\b[^.?!]{0,20}\b"
    r"(?:ran|run|runs)\s+over\s+(?:" + _STRUCK_PERSON + r"|" + _STRUCK_BODY + r")\b",
    # "my son got run over", "i got run over", "someone got run over outside my house" - no
    # vehicle has to be named, because the person is the subject and "run over" is not something
    # a plan does to them.
    _STRUCK_RUN_OVER,
    # "my cat got run over": the pet answer is the vet today, and the row passes it on below. A
    # cat crossing the road is not under a wheel, so the same "over + object" fence applies.
    r"\b" + _STRUCK_PET + r"\b[^.?!]{0,25}\b(?:got|get|gets|was|were|is|are|been)?\s*"
    r"(?:run|ran|runs)\s+over\b"
    r"(?!\s+(?:the|a|an|my|our|his|her|their|your|some|any|it|this|that|to)\b)",
    r"\b(?:a|an|the|some|one)\s+" + _STRUCK_VEHICLE + r"\b[^.?!]{0,20}\b"
    r"(?:ran|run|runs)\s+over\s+" + _STRUCK_PET + r"\b",
    # "i almost went under a bus", "he fell under a lorry": a person under a vehicle is the row
    # even with no verb of its own, and the line was reaching the drowning card on "under".
    r"\b" + _STRUCK_PERSON + r"\b[^.?!]{0,14}\b(?:went|go|goes|going|gone|fell|falls|falling|"
    r"ended\s+up|slid)\b[^.?!]{0,12}\bunder\s+(?:a|an|the)\s+" + _STRUCK_VEHICLE + r"\b",
    # "someone ran me over", "a fella ran my nan down": the doer need not be a vehicle word, and
    # "ran over" with a person on the end of it is not something a person does on foot. The near
    # thing reads the same shape with "nearly" in front of it, which is why this is here.
    r"\b(?:someone|somebody|he|she|they|(?:a|an|the|some|one)\s+(?:driver|man|woman|lad|lass|"
    r"boy|girl|fella|feller|chap|guy|bloke|person|van|car|lorry|truck|bus|coach|taxi|cab|"
    r"motorbike|motorcycle|scooter|bike|bicycle))\b"
    r"[^.?!]{0,10}\b(?:ran|run|runs)\s+" + _STRUCK_PERSON + r"\s+(?:over|down)\b",
    # "i nearly got mown down on the pavement" - the one verb that says the wheel did it, said
    # without "down" or "over" after it.
    r"\b" + _STRUCK_PERSON + r"\b[^.?!]{0,20}\b(?:got|get|gets|was|were|been)?\s*"
    r"(?:mowed|mown|mow)\b[^.?!]{0,10}\bdown\b",
    # "i nearly got knocked off my bike this morning": whoever did it need not be named, and a
    # rider off their bike on a road is the row's person whatever knocked them.
    r"\b" + _STRUCK_PERSON + r"\b[^.?!]{0,14}\b(?:got|get|gets|was|were|been)?\s*"
    r"(?:knocked|knocks)\s+off\s+(?:my|his|her|their|our|your)\s+"
    r"(?:bike|bicycle|motorbike|motorcycle|scooter|moped)\b",
    # "my foot was run over by a van", "he got run over by a lorry".
    r"\b" + _STRUCK_BODY + r"\b[^.?!]{0,20}\b(?:was|were|got|get|gets|been|is|are)\s*"
    r"(?:run|ran|runs)\s+over\s+by\s+(?:a\s+|an\s+|the\s+)?" + _STRUCK_VEHICLE + r"\b",
    # "my son was knocked off his bike by a car", "i got knocked off my bike by a car": the
    # bike is what the car knocked them off, so the rider is the person struck. Nothing read the
    # verb with "off" in it, and the line went to the greeting ("Your son was knocked off his
    # bike by a car - I'll remember that") or to the stain row when the person said "i".
    r"\b" + _STRUCK_PERSON + r"\b[^.?!]{0,20}\b(?:knocked|knocks|shoved|shunt(?:ed|s)?|"
    r"sent|sends)\s+off\s+(?:\w+\s+)?(?:bike|bicycle|motorbike|motorcycle|scooter|moped)\b"
    r"[^.?!]{0,12}\bby\s+(?:a\s+|an\s+|the\s+|his\s+|her\s+|their\s+|my\s+|our\s+|your\s+)?"
    + _STRUCK_VEHICLE + r"\b",
    # "a car knocked my son off his bike", "a van shunted him off his motorbike".
    r"\b(?:a|an|the|some|one|his|her|their|my|our)\s+" + _STRUCK_VEHICLE + r"\b[^.?!]{0,20}\b"
    r"(?:knocked|knocks|shoved|shunt(?:ed|s)?|sent|sends)\s+" + _STRUCK_PERSON + r"\s+off\s+"
    r"(?:\w+\s+)?(?:bike|bicycle|motorbike|motorcycle|scooter|moped)\b",
    # "a car drove into my son", "the van drove into me": driving into a person is the same
    # call as hitting them, and "drove into town" has no person after it.
    # "a lorry went into a woman at the lights" is the same call as driving into her, and "went
    # into" was not one of the verbs the row read.
    r"\b(?:a|an|the|some|one|another|his|her|their|my|our)\s+" + _STRUCK_VEHICLE +
    r"\b[^.?!]{0,20}\b(?:drove|drives|drive|rammed|rams|crashed|went|goes|go|ploughed|ploughs|"
    r"plowed|plows|smashed|smashes)\s+into\s+" + _STRUCK_PERSON + r"\b",
    # "someone drove into me", "a driver drove into my son".
    r"\b(?:someone|somebody|a\s+driver|the\s+driver)\s+(?:drove|drives|drive|rammed|rams|"
    r"crashed)\s+into\s+" + _STRUCK_PERSON + r"\b",
)


# A hypothetical is somebody asking about the road, not a call for it: "what should i do if a car
# hit my son". A line that says it has happened ("my son got hit by a car, what do i do") is not
# one of these and never leaves here.
STRUCK_HYPOTHETICAL = (
    r"\bwhat\s+(?:should|do|can|would)\s+(?:i|we|you)\s+do\s+if\b",
    r"\bwhat\s+(?:happens|would\s+happen|will\s+happen)\s+if\b",
    r"\bwhat\s+if\b",
)

# Somebody trapped in or under a vehicle is its own call, not the struck-by-a-vehicle one: that
# card says "say someone has been hit by a vehicle", and nobody was hit in "my wife is trapped in
# the car". On main the line is answered "Noted: your wife is trapped in the car", and "my leg is
# trapped under the car" with "I'll remember that", which is the worst line of a bad day met with
# a receipt.
_TRAPPED_VEHICLE_NOUN = (r"(?:car|van|lorry|truck|vehicle|wreck|taxi|cab|bus|coach|tractor|"
                         r"digger|forklift|train|tram)")
# The car door, the car seat and the car park hold people without trapping them in a crash:
# "my hand is trapped in the car door" is a finger in a hinge, and it has its own answer.
_TRAPPED_VEHICLE_NOT = (r"(?!\s+(?:door|doors|seat|seats|park|wash|boot|lot|key|keys|lock|"
                        r"mirror|radio))")
# "hes", "shes" and "theyre" are how people type a person, and only the last of them is in
# `_STRUCK_PERSON`.
_TRAPPED_PERSON = (r"(?:" + _STRUCK_PERSON + r"|hes|shes|theyre|he['\u2019]s|she['\u2019]s|"
                   r"they['\u2019]re|kids|children|(?:the|my|our)\s+(?:kids|children|little\s+"
                   r"(?:one|boy|girl)))")
# Locked and shut are said of a person only when the preposition comes straight after them, so
# "i locked my keys in the car" is the lockout answer and not a person in a wreck.
# The parts of a person a vehicle can be on top of, with the owner in front and an optional
# possessive relative between: "my leg", "my son's legs", "my sons legs".
_TRAPPED_BODY = (r"(?:leg|legs|arm|arms|foot|feet|hand|hands|body|torso|chest|hip|hips|waist|head|"
                 r"neck|ankle|ankles|wrist|wrists|shoulder|shoulders|ribs|pelvis|back)")
_TRAPPED_BODY_OWNER = (r"(?:my|his|her|their|our|your)\s+(?:\w+['\u2019]?s\s+)?" + _TRAPPED_BODY)
_TRAPPED_STATE = (r"(?:trapped|pinned|wedged|crushed|stuck)")
_TRAPPED_LOCKED = (r"(?:locked|shut)\s+(?:in|inside)")
TRAPPED_VEHICLE = (
    # "my wife is trapped in the car", "hes pinned under the van", "my son is stuck inside the
    # wreck". The person, then the state, then the vehicle.
    r"\b" + _TRAPPED_PERSON + r"\b[^.?!]{0,15}\b(?:\w+\s+){0,2}?"
    r"(?:" + _TRAPPED_STATE + r"\b[^.?!]{0,12}\b(?:in|inside|under|beneath)|"
    r"" + _TRAPPED_LOCKED + r")\b[^.?!]{0,10}\b(?:the\s+|a\s+|an\s+|his\s+|her\s+|"
    r"their\s+|our\s+|my\s+)?" + _TRAPPED_VEHICLE_NOUN + r"\b" + _TRAPPED_VEHICLE_NOT,
    # The body part is the person: "my leg is trapped under the car", "his arm is caught in the
    # wreck". "under the car door" is the fence above. The possessive is optional before the part,
    # because "my sons legs" and "his sister's arm" are typed without the apostrophe or with it.
    r"\b" + _TRAPPED_BODY_OWNER + r"[^.?!]{0,15}\b(?:trapped|pinned|wedged|crushed|"
    r"stuck|caught)\b"
    r"[^.?!]{0,12}\b(?:in|inside|under|beneath)\b[^.?!]{0,10}\b(?:the\s+|a\s+|an\s+)?"
    + _TRAPPED_VEHICLE_NOUN + r"\b" + _TRAPPED_VEHICLE_NOT,
    # The vehicle said first: "the car has pinned my son's legs", "a van trapped him", "the lorry
    # trapped his leg".
    r"\b(?:the|a|an|his|her|their|our|my)\s+" + _TRAPPED_VEHICLE_NOUN +
    r"\b[^.?!]{0,20}\b" + _TRAPPED_STATE + r"\b[^.?!]{0,12}\b(?:"
    + _TRAPPED_PERSON + r"|" + _TRAPPED_BODY_OWNER + r")\b",
    # The state at the end of the line, with the crash named: "the car went into a ditch and my
    # wife is trapped" is a wreck with a person in it, and main answered it with a receipt. The
    # crash word has to be there, so "my wife is trapped" on its own is still somebody else's row.
    r"(?=[^.?!]*\b(?:crash(?:ed|es|ing)?|ditch|wreck(?:ed)?|rolled|overturn(?:ed)?|flipped|"
    r"skidded|collision|hit\s+(?:a|the)\s+(?:tree|wall|lamp\s*post|post|barrier|railing|"
    r"bridge))\b)"
    r"[^.?!]*\b" + _TRAPPED_PERSON + r"\b[^.?!]{0,25}\b(?:" + _TRAPPED_STATE + r"|"
    + _TRAPPED_LOCKED + r")\b",
)
# "im stuck in the car" is a jam, a car park or a wait, and the card is written for the person
# watching; "i am trapped in the car" is the emergency and stays. A wreck, heat, fire or the engine
# running makes being stuck one too: "im stuck in the car and its hot".
TRAPPED_SELF_STUCK = re.compile(
    r"\b(?:im|i\s+am|i['\u2019]m|we['\u2019]re|we\s+are)\b[^.?!]{0,20}\bstuck\b")
TRAPPED_NOT_A_WAIT = re.compile(
    r"\b(?:wreck|wrecked|upside\s+down|on\s+its\s+(?:side|roof)|rolled|overturned|flipped|"
    r"ditch|hot|heat|sun|stifling|no\s+air|fire|smoke|flames|engine\s+(?:is\s+)?running|"
    r"can'?t\s+get\s+out|locked\s+in)\b")


# A parent at the end of their rope: "the baby has been crying for six hours and i feel like
# shaking him" was answered with a film about crying. The wish to shake is the one thing that must
# never be carried out, and the person saying it needs a way out now, not a card about crying. The
# object has to be a child, so "i feel like shaking my head" and "i could shake him" stay ordinary.
SHAKE_WISH = (
    r"\b(?:feel\s+like|felt\s+like|want\s+to|wanted\s+to|going\s+to|about\s+to|nearly|"
    r"close\s+to|tempted\s+to|might|i\s+could|afraid|scared|"
    # "i keep thinking about shaking her" and "i have thought about it" are the same wish said as
    # a thought, and they were reaching the tremor card. A bare "him" does not say it is a child,
    # so the thought still needs the child named or the coping said (SHAKE_CHILD_CONTEXT and
    # SHAKE_COPING below) before it is this arm's line.
    r"(?:keep\s+)?think(?:ing)?\s+about|thought\s+about|have\s+thought\s+about|"
    r"keep\s+wanting)\b[^.?!]{0,30}"
    r"\b(?:shak(?:e|es|ing)|shook|hurt|hurting|hit|hitting|thump(?:ing)?|smack(?:ing)?)\b"
    r"[^.?!]{0,26}\b(?:him|her|them|the\s+baby|my\s+(?:son|daughter)|the\s+little\s+one)\b",
)
# ...and the child is the one it is about, said either before the wish or after it.
SHAKE_CHILD_CONTEXT = (
    r"\b(?:baby|babies|newborn|toddler|the\s+little\s+one|my\s+(?:son|daughter|baby|girl|boy)|"
    # The child is often carried by the care rather than the word: "i had to put her down",
    # "the nappies", "the night feeds". Without this the wish read as a tremor or, worse, as
    # putting a pet down.
    r"put\s+(?:her|him|them)\s+down|napp(?:y|ies)|night\s+feeds?|feeding|"
    r"bottle|pram|cot|moses\s+basket|first\s+tooth|sleep\s+(?:regression|training))\b",
    r"\b(?:cr(?:y|ies|ied|ying)|scream\w*|wont\s+sleep|won'?t\s+sleep|up\s+all\s+night|"
    r"will\s+not\s+sleep|teething|colic|colicky)\b",
)
# The child is often not named at all: "i dont know how much longer i can do this, i want to shake
# her" is the same line as the one above with the baby left implied, and it reached the weaning
# card. A coping word on the end of a wish to shake somebody is enough, unless the somebody is a
# grown-up the line has already named.
SHAKE_COPING = (
    r"\b(?:can'?t\s+do\s+this|cant\s+do\s+this|can'?t\s+cope|not\s+coping|no\s+sleep|"
    r"havent\s+slept|haven'?t\s+slept|not\s+slept|exhausted|so\s+tired|knackered|"
    r"breaking\s+point|at\s+the\s+end\s+of\s+(?:it|my\s+tether)|desperate|nothing\s+works|"
    r"nothing\s+helps|"
    r"(?:dont|don'?t)\s+know\s+how\s+much\s+longer)\b",
)
SHAKE_ADULT = (
    r"\bmy\s+(?:husband|wife|partner|boyfriend|girlfriend|ex|boss|manager|mum|dad|mother|"
    r"father|sister|brother|nan|grandad|grandma|friend|mate|neighbour|colleague)\b",
)
SHAKE_CHILD = SHAKE_WISH
# The same wish said about the person themselves, or as a joke about a band and a milkshake.
SHAKE_IDIOM = (
    r"\b(?:shake|shaking|shook)\s+(?:my|your|his|her)\s+head\b",
    r"\b(?:shake|shaking)\s+hands?\b",
    r"\b(?:shake\s+it\s+off|shake\s+things\s+up|shake\s+up)\b",
    r"\bmilk\s*shake\b",
    r"\bshak(?:e|ing)\s+with\s+(?:cold|laughter|laughing|fear|nerves)\b",
    r"\bshak(?:e|ing)\s+some\s+sense\b",
)
SHAKE_REPLY = (
    "Put the baby down somewhere safe - on their back in the cot, even if they are crying - and "
    "step out of the room for a minute. Never shake a baby, however long it has gone on: put them "
    "down and ring someone who can take over, Cry-sis on 0800 448 0737, or 111 if you are scared "
    "of how you feel.",
    "That is the moment to put the baby down and walk away, not to carry it through: on their back "
    "in the cot, door shut, two minutes in another room. Shaking a baby hurts them for life. Ring "
    "Cry-sis on 0800 448 0737, or 111 tonight, and say out loud that you are at the end of it.",
)
# "Put the baby down in the cot" is only the right wording when the line says there is a baby in
# it. A tired parent saying "i want to hit him" about an older child gets the same help without
# being told to do something that makes no sense for a seven-year-old.
SHAKE_BABY_WORD = (
    r"\b(?:baby|babies|newborn|new\s*born|cot|crib|napp(?:y|ies)|feeding|feeds?|bottle|pram|"
    r"teething|colic|colicky)\b",
    r"\bput\s+(?:her|him|them)\s+down\b",
)
SHAKE_CHILD_REPLY = (
    "Put them down somewhere safe and step out of the room for a minute - they can cry for two "
    "minutes and come to no harm. Never shake or hit a child, however long it has gone on: put "
    "them down and ring someone who can take over. Cry-sis on 0800 448 0737 is for exactly this, "
    "and 111 if you are scared of how you feel.",
    "That is the moment to put them down and walk away, not to carry it through: somewhere safe, "
    "the door shut, two minutes in another room. Shaking or hitting a child hurts them for life. "
    "Ring someone who can take over tonight - Cry-sis on 0800 448 0737 - and say out loud that you "
    "are at the end of it.",
)
# Being out cold for a night, or until a time, or until somebody found them, is not a nap: "my dad
# was out cold all night" and "she was out cold until 3am" were answered with a shrug, because the
# sleep words in OUT_COLD_ASLEEP ("all night", "until", "the whole") stand the knockout arm down.
OUT_COLD_LONG = (
    # "until 3am" has no word boundary after the figure, so the clock is matched on its own.
    r"\bout\s+cold\b[^.?!]{0,24}(?:\b(?:all\s+night|the\s+(?:whole|entire)\s+night|"
    r"for\s+(?:hours|ages))\b|until\s+\d|later\s+that\s+(?:morning|afternoon|evening)|"
    r"until\s+(?:the\s+|that\s+)?(?:morning|afternoon|evening|lunchtime|midday|dawn|"
    r"dusk|nightfall))",
)
OUT_COLD_FOUND = (
    r"\bfound\s+(?:me|him|her|them)\b",
    r"\b(?:couldn'?t|couldnt|could\s+not)\s+wake\b",
    r"\bno\s+idea\s+(?:how\s+long|what\s+happened)\b",
    r"\bcouldn'?t\s+get\s+(?:him|her|them)\s+up\b",
    r"\bwoke\s+up\s+(?:on\s+the|in\s+the)\b",
)
# Somebody who cannot be woken now is the recovery-position card's, and that card already answers
# it: this one is for the history, not for a person still out.
OUT_COLD_LEFT_TO_OTHERS = (
    r"\b(?:can'?t|cant|couldn'?t|couldnt)\s+wake\b",
    r"\bnot\s+breathing\b",
    r"\bno\s+pulse\b",
    r"\bstill\s+(?:not\s+woken|out|unconscious|asleep)\b",
)
# The name carries "night" because OUT_COLD_REPLY is already the tables' faint answer, and
# `from .safety_tables import *` would otherwise have this shadow it for every blackout line.
# A night out, a night shift, a bottle and a long walk all end in being out cold, and none of them
# wants an ambulance.
OUT_COLD_SLEEPY = (
    r"\b(?:party|night\s+shift|night\s+out|long\s+day|shift|walk|run|hike|gig|flight|"
    r"jet\s?lag|dinner|meal|feed|bottle|nap|bed|bedtime|asleep|sleep\w*|exhaust\w*|tired|"
    r"knackered|drunk|pints|beers?|wine)\b",
)
OUT_COLD_NIGHT_REPLY = (
    "That is not a sleep - being out cold that long needs 999 or 911 now, or straight to A&E if "
    "they are awake and you can get them there. Say how long it went on and whether they came "
    "round by themselves, and do not leave them alone until someone has seen them.",
    "Ring 999 or 911 now: nobody is out cold for a night and fine. Tell them how long it lasted and "
    "anything before it - a bang on the head, a drink, a medicine - and stay with them until help "
    "comes.",
)
# Violence that lands on the room instead of a person: "he is throwing things", "my husband is
# smashing things up", "my partner punched the wall". Nothing has hit anybody yet, and that is
# exactly the turn to say it: the person in the next room is already being told what would happen.
ABUSE_OBJECTS = (
    r"\b(?:throw(?:s|ing)?|threw|thrown|smash(?:es|ing|ed)?|break(?:s|ing)?|broke|"
    r"punch(?:es|ing|ed)?|kick(?:s|ing|ed)?|trash(?:es|ing|ed)?|wreck(?:s|ing|ed)?)\b"
    r"[^.?!]{0,30}\b(?:things|stuff|plates|glasses|crockery|furniture|chairs?|doors?|walls?|"
    r"windows?|the\s+(?:house|flat|place)|"
    r"my\s+(?:things|stuff|house|flat|home|place|room|kitchen|bedroom|living\s+room|car))\b",
)
# A person has to be doing it: "ive had enough of life throwing things at me" is a figure of
# speech about a bad year, and the abuse card read that as a home with things being thrown in it.
ABUSE_OBJECTS_PERSON = (
    # "hes" and "shes" are how most people type it, and they are not \bhe\b.
    r"\b(?:he|she|they|hes|shes|theyre|husband|wife|partner|boyfriend|girlfriend|ex|dad|mum|"
    r"father|mother|stepdad|stepmum|grandma|grandpa|nan|grandad|flatmate|housemate|brother|"
    r"sister|carer)\b",
)
# The same words for a job, a game, a clear-out or a toddler, and for a person nobody lives with.
ABUSE_OBJECTS_OFF = (
    r"\bthrowing\s+(?:things|stuff)\s+(?:away|out|in\s+the\s+bin)\b",
    r"\bthrew\s+my\s+back\s+out\b",
    r"\bbreak(?:ing)?\s+things\s+off\b",
    r"\b(?:baby|babies|toddler|toddlers|kids?|children|child)\b[^.?!]{0,24}"
    r"\b(?:throw|throws|throwing|smash|smashing|broke|breaking)\b",
    r"\b(?:throwing|smashing|punching)\s+(?:things|stuff|plates)\s+(?:at|in)\s+"
    r"(?:the\s+)?(?:park|garden|playground|soft\s+play|bouncy\s+castle)\b",
    r"\b(?:in\s+a\s+(?:film|movie|game|show)|on\s+telly|in\s+the\s+film)\b",
)
CASES = (
    # A pregnancy red flag before the words it shares with everything else: "im pregnant and
    # bleeding" is the maternity unit, not the cut-and-press reply.
    ("pregnancy_bleed", PREGNANCY_BLEED, False),
    ("pregnancy_quiet", PREGNANCY_QUIET, False),
    ("pregnancy_bp", PREGNANCY_BP, False),
    ("pregnancy_waters", PREGNANCY_WATERS, False),
    ("electric_shock_floor", ELECTRIC_SHOCK_FLOOR_LINE, False),
    ("electric_shock", ELECTRIC_SHOCK, False),
    ("socket_thing", SOCKET_THING + SOCKET_COVER, False),
    ("pregnancy_sick", PREGNANCY_SICK, False),
    ("pregnancy_sick_q", PREGNANCY_SICK_Q, False),
    ("self_harm", SELF_HARM, True),
    ("hanging", HANGING, True),
    ("abuse", ABUSE, False),
    ("shot", SHOT, False),
    ("eye_chem", EYE_CHEM, False),
    ("heard_assault", HEARD_ASSAULT, False),
    # No sign named: ask what you can see, and carry the rule both ways.
    ("allergy_now", ALLERGY_NOW, False),
    ("lips_swell", LIPS_SWELL, False),
    ("lips_swell_bare", LIPS_SWELL_BARE, False),
    ("lips_tingle", LIPS_TINGLE, False),
    ("allergy_food", ALLERGY_FOOD, False),
    ("throat_tight", THROAT_TIGHT, False),
    ("swallow_gone", SWALLOW_GONE, False),
    ("bone_out", BONE_OUT, False),
    ("headache", HEADACHE, False),
    ("cough_blood", COUGH_BLOOD, False),
    ("vomit_blood", VOMIT_BLOOD, False),
    ("poo_black", POO_BLACK, False),
    ("poo_blood", POO_BLOOD, False),
    ("torsion", TORSION, False),
    ("unsafe", UNSAFE, False),
    ("intruder", INTRUDER, False),
    # An insect bite is an itch, a tick a removal and a watch: both reached the wide bite arms.
    ("insect_bite", INSECT_BITE, False),
    ("tick_bite", TICK_BITE, False),
    # A bat is the bite where a mark that barely shows still needs a same-day call.
    ("bat_bite", BAT_BITE, False),
    # A fox, a badger or a rat is the small wound the dog's arm alone was answering.
    ("wild_bite", WILD_BITE, False),
    ("dog_bite", BITE_DONE, False),
    ("dog_attack", DOG_ATTACK, False),
    # A garment alight and a pan alight each have their own answer, and both are the fire's
    # family: they come first so the building card does not answer over them.
    ("clothes_fire", CLOTHES_FIRE, False),
    ("pan_fire", PAN_FIRE, False),
    ("vehicle_fire", VEHICLE_FIRE, False),
    ("fire", FIRE, False),
    # A burning battery is in the same family as the fire, but the advice against water is not.
    ("battery_fire", BATTERY_FIRE, False),
    ("battery_bulge", BATTERY_BULGE, False),
    ("electric_burn", ELECTRIC_BURN, False),
    ("gas_left", GAS_LEFT_ON, False),
    ("gas_smell", GAS_SMELL, False),
    # Bleach plus an acid is chlorine gas, before the poison and cleaning rows that share its words.
    ("bleach_mix_q", BLEACH_MIX_Q, False),
    ("bleach_mix", BLEACH_MIX, False),
    ("co_signs", CO_SIGNS, False),
    ("co_going_off", CO_GOING_OFF, False),
    ("co_leak", CO_LEAK, False),
    ("co_place", CO_PLACE, False),
    ("co_test", CO_TEST, False),
    ("co_fact", CO_FACT, False),
    ("bone_throat", BONE_THROAT, False),
    ("object_in_head", OBJECT_IN_HEAD, False),
    ("dose_stated", DOSE_STATED + DOSE_DOUBLE + DOSE_RECENT + DOSE_WHOLE_PACK, False),
    ("swallowed_thing", SWALLOWED_THING, False),
    ("mild_swallowed", MILD_SWALLOWED, False),
    ("foraged", FORAGED_EATEN, False),
    ("poison", POISON, False),
    ("swallowed_ordinary", SWALLOWED_ORDINARY, False),
    ("spiked", SPIKED, False),
    ("co_mention", CO_MENTION, False),
    ("fall_hip", FALL_HIP, False),
    ("crush", CRUSH, False),
    ("fall", FALL, False),
    ("puncture", PUNCTURE, False),
    ("appendix", APPENDIX, False),
    ("old_fall", OLD_DOWN, False),
    ("fall_check", FALL_CHECK, False),
    ("bleeding", BLEEDING, False),
    # A person struck by a vehicle, before the injury rows it shares words with: "my son was
    # knocked down by a car and is bleeding" is the 999 call, not the cut-and-press card.
    ("struck_by_vehicle", STRUCK_BY_VEHICLE, False),
    ("trapped_vehicle", TRAPPED_VEHICLE, False),
    ("stuck_machine", STUCK_MACHINE, False),
    ("dental_numb", DENTAL_NUMB, False),
    ("slur_small_child", SLUR_SMALL_CHILD, False),
    ("slur_drink", SLUR_DRINK, False),
    # A wound with a red line running from it, or redness spreading from it, is lymphangitis: the
    # infection is in the channels that drain the wound, so it is a same-day call, and the 999 call
    # once a fever is with it. Read before the limb rows rather than with the first aid ones: "my
    # cut has a red line going up my arm" and "redness spreading up my arm from a cut" both lost
    # to a chest-and-arm card, and the answers row calls an infection "two or three days after the
    # injury". A stroke or a heart attack said in the same line keeps its own card.
    ("stroke", STROKE + STROKE_WEAK, False),
    ("wound_streak_fever", WOUND_STREAK_FEVER, False),
    ("wound_streak", WOUND_STREAK, False),
    ("arm_numb", LEFT_ARM_NUMB, False),
    ("chest", CHEST + CHEST_ADJ + CHEST_SORE_MOVE, False),
    # The FAST arm answers after the chest and after the numb left arm, on purpose: both of those
    # are specific cards for the lines they own ("my chest is tight and my left arm is numb" stays
    # the chest call, and a numb left arm keeps its stroke wording), and this one is here for what
    # nothing else read at all.
    ("stroke", STROKE_FAST, False),
    ("breath_rest", BREATH_REST, False),
    ("breathing", BREATHING, False),
    # Breathless in the night or lying flat: an appointment today, unless it is still happening.
    ("night_breath", NIGHT_BREATH, False),
    ("breath_past", BREATH_PAST, False),
    ("blue", BLUE, False),
    ("floppy_child", FLOPPY_CHILD, False),
    # A blackout is its own case and it is not the "unconscious" one: that case is somebody who is
    # not responding now, and this is a person who went down and came back.
    ("blackout", BLACKOUT_RED_LINE, False),
    ("unconscious", UNCONSCIOUS + WAKE_UP_SOMEONE + WONT_COME_ROUND + HARD_TO_WAKE, False),
    ("seizure", SEIZURE, False),
    ("drowning", DROWNING, False),
    ("heat", HEAT, False),
    ("scald", SCALD, False),
    # A rash that does not fade goes before everything else: it is the one sign a parent can see.
    ("red_flags", RASH_RED, False),
    ("stiff_neck", STIFF_NECK_RED, False),
    ("sepsis_signs", SEPSIS, False),
    # A pale, grey or mottled child with cold, clammy or sweaty skin is a child with too little
    # blood going round, and it is said without a fever word in the line, so the sepsis pair
    # (which needs both) passed it: "my son is pale and clammy" and "my baby is pale and sweaty"
    # were "Noted:", and "my son is very pale and sleepy" was told he was tired. One sign is not
    # enough on its own - a child can look pale after a long day - so this wants a sign and a
    # second thing in the same line.
    ("pale_child", PALE_CHILD, False),
    # The grown-up version of the row below, and the advice is the opposite one: sit them down and
    # ring the ambulance rather than keep them warm and wait for a doctor.
    ("pale_adult", PALE_ADULT, False),
    ("newborn_fever", NEWBORN_TEMP, False),
    ("newborn_fever_next", NEWBORN_NEXT, False),
    # A named illness, a number that is too high, a drink the child found, a fit that just
    # happened, a grunt, a baby too sleepy to feed: each is stated plainly and each is an
    # ambulance or a same-day doctor, and none of them was answered by the bot at all.
    ("named_illness", NAMED_ILLNESS_CHILD, False),
    ("high_temp", HIGH_TEMP_CHILD, False),
    ("child_drank", CHILD_DRANK, False),
    ("recent_fit", RECENT_FIT, False),
    ("grunting_baby", GRUNTING_BABY, False),
    ("sleepy_feed", SLEEPY_FEED, False),
    # A headache and a rash said together is the meningitis pair without the fever, and it is the
    # commonest way a parent describes it: it goes before the fever rows, above the plain-fever one.
    ("rash_headache", RASH_HEADACHE, False),
    ("fever_rash", FEVER_RASH, False),
    # Last, so that a rash, a stiff neck, a named illness or a child who is playing happily all
    # keep their own answer: this one is for the plain "my baby has a fever".
    ("child_fever", CHILD_FEVER, False),
    # Last, because a fall with a red flag already taken by the head or breathing answer is an
    # ambulance, and this only says the same-day check for a baby who seems well.
    ("baby_fell", BABY_FELL, False),
)

# A bang on the head that came with a faint is not the mild bump: being out for a moment and hitting
# the head is the head-injury card whatever the lump looks like afterwards, and the watch reply
# ("an ice pack for ten minutes is plenty") is the wrong advice for it. The words are the faint
# readers' own, plus "came over funny", which is how people say the same thing.
FAINT_WITH_A_BANG = FAINT_STORY + (
    r"\bcame\s+(?:over|round)\b[^.?!]{0,20}\b(?:funny|queer|faint|on\s+the\s+floor)\b",
)


def _fainted_with_the_bang(line):
    """True when the line says a faint as well as the bang: the sight going, or the verb itself."""
    if _matches(FAINT_WITH_A_BANG, line):
        return True
    # "everything went black and i banged my head": a person's head is in the line already, because
    # HEAD_BANG will not match without one, so only the shape is asked about here.
    return any(re.search(shape, line) for shape, _needs_person in BLACKED_OUT_SIGHT)
PAST_BLACKOUT_REPLY = (
    "Worth mentioning to your GP: passing out is looked into even when it was a one-off, and they "
    "can check blood pressure, the heart and bloods. If it happens again, or they are hard to wake "
    "or fitting, that is an ambulance and not a wait."
)
# "Is out cold" is not this: a person out cold now is the recovery-position call, and that card is
# written further down. This one is the faint that has already happened and ended.
OUT_COLD_NOW = (
    r"\b(?:is|'s|are|'re|still)\s+(?:\w+\s+){0,2}out\s+cold\b",
    r"\bout\s+cold\b[^.?!]{0,12}\b(?:right\s+now|now|at\s+the\s+moment)\b",
)
# Somebody who will not wake is not a faint that has ended, whatever else the line says: the
# recovery-position call is the right one, and it is written further down.
OUT_COLD_WONT_WAKE = (
    r"\b(?:won'?t|wont|wouldn'?t|wouldnt|didn'?t|didnt|can'?t|cant|cannot|isn'?t|isnt|not)\s+"
    r"(?:wake|waking|rouse|come\s+round|coming\s+round|respond|responding)\b",
    r"\bunresponsive\b", r"\bnot\s+responding\b", r"\bout\s+of\s+it\b",
)
# Said to whoever had the fit, so the actions in it are ones the reader can take either way:
# "ring 111 and say what *they* did" was being said to people who had the fit themselves.
PAST_FIT_WEEK_REPLY = (
    "A fit a week ago still needs looking at today rather than waiting: ring 111 or the GP surgery "
    "and say when it happened and what it looked like. If another one starts and does not stop, "
    "that is an ambulance: on the floor on one side, nothing in the mouth."
)
PAST_FIT_REPLY = (
    "Mention that to your GP: a fit is looked into even when it only happened once, and they can "
    "say whether it needs any tests. If one happens again and does not stop, that is an ambulance: "
    "on the floor on one side, nothing in the mouth."
)
def _effort_recovery(line):
    """Hard exercise plus a phrase of recovery is a person who has just worked hard.

    "i cant catch my breath after spin class" rang the ambulance because BREATH_EFFORT only knows
    running for a bus; "i was out of breath after spinning" got a shrug because no case matches it.
    A red flag, a faintness or a thing that does not breathe puts the line back where it was.
    """
    return (_matches(EXERTION_CLASS + BREATH_EFFORT + EXERTION, line)
            and _matches(EFFORT_RECOVERY, line)
            and not _matches(BREATH_RED + EFFORT_MORE_RED, line)
            and not _matches(NOT_A_BREATHER + PET_WORDS, line)
            and not _matches(EFFORT_TOO_LONG, line)
            and not _matches(EFFORT_SOMEONE_ELSE, line)
            # "i get shortness of breath right now when i run" is a present symptom, not an
            # afternoon that has gone; those lines keep whatever reading they had.
            and not _matches((r"\bstill\b", r"\bright\s+now\b"), line))


# ---------------------------------------------------------------------------
# Alcohol withdrawal.
# "i stopped drinking" is the stop, and the drink after it is what was stopped: coffee, tea, coke
# and squash are the same sentence and are not this, which is what WITHDRAWAL_NOT_ALCOHOL keeps
# out. The second arm is the other order - "booze withdrawal", "detox from alcohol".
# A stop that is not recent is not the withdrawal: the risk is the first hours and days.
WITHDRAWAL_LONG_AGO = (
    r"\b(?:\d+|two|three|four|five|six|seven|eight|nine|ten|tin|twenty|thirty|many|several|"
    r"a\s+few)\s+years?\s+ago\b",
    r"\byears\s+ago\b", r"\bmonths\s+ago\b", r"\blast\s+year\b", r"\bdecades?\b",
)
# The state said as a count is the stop: "im 2 days sober and my heart is racing" was a greeting on
# main. It needs a sign with it, so "im 3 months sober and i feel great" stays a win.
WITHDRAWAL_SOBER = (
    r"\b(?:\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|a\s+few|several|couple\s+of)"
    r"\s+(?:hours?|days?|weeks?|months?)\s+(?:sober|dry|off\s+it|alcohol[-\s]?free|"
    r"without\s+a\s+drink|with\s+no\s+booze)\b",
)
# "i stopped cold turkey and now im shaking" has no drink word, and "cold turkey" is the stop said
# the way people say it. The fags and the cigarettes are still stood down by WITHDRAWAL_NOT_ALCOHOL.
WITHDRAWAL_COLD_TURKEY = (
    r"\b(?:stop(?:ped|ping)?|quit(?:ting)?|come|coming|came|get|getting|got|went|going|go|"
    r"gave\s+up|giving\s+up)\b[^.?!]{0,20}\bcold\s+turkey\b",
)
# A stop that is going well and has been going on for weeks is not the risky stretch: "im off the
# booze for a month and i feel great" is the news, not a symptom. Weeks in and still feeling awful
# keeps the card, which is why the good news has to be in the line too.
WITHDRAWAL_WEEKS = (
    r"\b(?:\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|twelve|couple\s+of|"
    r"few)\s+(?:weeks?|months?)\b",
)
WITHDRAWAL_FINE = (
    r"\b(?:feel|feeling|felt)\s+(?:great|better|amazing|brilliant|fantastic|good|"
    r"so\s+much\s+better|loads\s+better)\b",
    r"\bnever\s+(?:felt|feel)\s+better\b", r"\bbest\s+(?:i'?ve|i\s+have)\s+felt\b",
)
PREGNANT_LINE = (
    r"\bpregnan\w*", r"\bexpecting\s+a\s+(?:baby|child)\b", r"\b\d+\s+weeks?\s+gone\b",
)
# "how long does it last" and "is that dangerous" are the two questions the card invites, and both
# were being answered with something else a turn later.
WITHDRAWAL_DURATION = (
    r"\bhow\s+long\b", r"\bhow\s+many\s+(?:days|hours|weeks)\b",
    r"\bwhen\s+(?:will|does|do|should)\b[^.?!]{0,30}\b(?:stop|end|ease|better|over|go\s+away)\b",
)
# Getting worse is the 111 line, not the ambulance: "will it get worse" and "im scared" after the
# card were getting the delirium tremens 999 card. `help` is not in here - "should i have a beer to
# help me sleep" is a question about the beer, and it was reaching the same 999.
WITHDRAWAL_WORSE = (
    r"\bworse\b", r"\bgetting\s+worse\b", r"\bnot\s+stopping\b", r"\bcant\s+stop\b",
    r"\ball\s+night\b", r"\ball\s+day\b", r"\bunbearable\b",
    r"\bscared\b", r"\bterrified\b", r"\bfrightened\b",
)
# "my partner is detoxing at home and shaking" names the state without the drink, and the symptom
# is what carries it. The sugar and phone detoxes are kept out by WITHDRAWAL_NOT_ALCOHOL above.
WITHDRAWAL_BARE = (
    r"\bdetox\w*", r"\bwithdrawal\b", r"\b(?:went|going|go|gone)\s+cold\s+turkey\b",
)
# The state named and said to be bad is the state, even with no symptom word: "the withdrawal is
# bad tonight" is somebody in it, not somebody asking about it.
WITHDRAWAL_BARE_BAD = (
    r"\b(?:bad|worse|awful|terrible|rough|hell|horrible|dreadful)\b",
    r"\b(?:cant|cannot|can'?t)\s+(?:sleep|eat|stop\s+shaking)\b",
)
# The severe end: confusion, hallucinations and fits are the ambulance, not the surgery.
WITHDRAWAL_SEVERE = (
    r"\bconfus\w*", r"\bhallucinat\w*",
    r"\bdelirium\b", r"\bfits?\b", r"\bseizures?\b", r"\bnot\s+making\s+sense\b",
    r"\bdon'?t\s+know\s+where\s+i\s+am\b", r"\bshaking\s+all\s+over\b", r"\bcan'?t\s+stand\b",
)


def _hallucinating(line):
    """True when the line reports a hallucination rather than a sense that came back."""
    if not _matches(WITHDRAWAL_HALLUCINATION, line):
        return False
    return not _matches(WITHDRAWAL_SENSES_FINE, line)


def _severe(line):
    """True for the delirium tremens signs, hallucination included."""
    return _matches(WITHDRAWAL_SEVERE, line) or _hallucinating(line)
# A stop that is a plan rather than a thing that happened. A date in the future keeps the ordinary
# answer: nothing is withdrawing yet.
WITHDRAWAL_NOT_NOW = (
    r"\b(?:next\s+week|next\s+month|on\s+monday|on\s+tuesday|on\s+wednesday|on\s+thursday|"
    r"on\s+friday|on\s+saturday|on\s+sunday|in\s+the\s+new\s+year|for\s+dry\s+january|"
    r"dry\s+january|sober\s+october)\b",
)

from bot.knowledge.crisis_replies import REPLIES  # noqa: F401  (the cards)


# ...and a scorched fringe over skin that is red or blistered is a burn on the face, so it gets the
# burn card rather than the haircut answer.
HAIR_SCORCH_SKIN = (
    r"\b(?:red|raw|sore|blister\w*|peeled|peeling|swollen|swelling|weeping|white\s+patch|"
    r"burnt\s+skin|burned\s+skin)\b",
)


# The rash, the stiff neck, the fever that has gone wrong and the newborn's temperature are one
# emergency with one reply: the glass test and "say you are worried about sepsis or meningitis".
for _alias in ("stiff_neck", "sepsis_signs", "newborn_fever"):
    REPLIES[_alias] = REPLIES["red_flags"]

# Lines that are alarming but clearly a general question get the same help, said as guidance.
# The texts live in bot/knowledge/crisis_replies.py with the cards, so this module stays under the
# publisher's 1 MiB file limit; nothing below reads a different word for it.
from bot.knowledge.crisis_replies import GENERAL  # noqa: F401  (the general answers)


# --- minor injuries: not an emergency, but still worth a useful answer -----------------------

# ...and never the animals' or the vegetables': both have their own answer further down the
# ladder, and this module is above everything.
LIMP_NOT = ANIMAL + (
    r"\b(?:celery|lettuce|greens?|salad|spinach|cabbage|herbs?|leaves?|asparagus|spring\s+onions?|"
    r"hair|market|car|engine|economy)\b",
    # A thing that has a limp part is not a person: "my bike has a limp wheel", "the door has a
    # limp hinge", "the shed has a bad limp in the fence", "my washing machine has a limp". The
    # noun arms above read the plainest way people say it, and they read a thing saying it too
    # (alert-cat, on this PR), so the thing has to be at the front of the line to be the subject -
    # a person who caught their foot "in the door" keeps the card.
    r"\A\W*(?:(?:the|my|our|this|that|his|her|their|your)\s+)?(?:shed|fence|gates?|doors?|"
    r"hinges?|bikes?|wheels?|machines?|washing\s+machine|dishwasher|hoover|vacuum|laptops?|"
    r"phones?|screen|boards?|chairs?|tables?|sofas?|bench|pram|pushchair|buggy|trolley)\b",
    # A prosthesis is a leg only when the line is about the walking. The prosthesis word alone is
    # on the ongoing-limp table, so "i have a prosthetic eye and it itches", "my prosthetic eye is
    # sore", "my prosthetic hand is cold" and "my prosthetic leg hurts" were all told that a
    # weeks-old limp is a GP job. An eye, a socket, a hand, a denture or a limb that rubs is a fit
    # question with its own answer, so the limp rows stand down - unless the line also says the
    # gait, because a prosthesis and a limp together is the appointment.
    r"\b(?:prosthe\w*|artificial\s+(?:arm|arms|leg|legs|limb|limbs|hand|hands|foot|feet))"
    r"(?![^.]*\b(?:limp(?:s|ing|ed)?|gait|walk\s+with)\b)",
)


# A limp with a named cause is not a fresh knock, and the two needs are different. A gait that
# comes after a stroke or a hip replacement is the joint or the brain's answer, which this module
# sits above: "i walk with a limp after my stroke" was the stroke card before the noun patterns
# above read it, and ice and a day or two off it is the wrong thing to say to a stroke. Those rows
# are named here so the limp stands down and the answer that knew the cause takes the line back.
LIMP_CAUSE = (
    r"\bstroke\b", r"\bhip\s+replacement\b", r"\bknee\s+replacement\b",
    r"\b(?:hip|knee|joint)\s+(?:op|operation)\b",
    r"\breplacement\s+(?:hip|knee|joint)\b",
)
# The replacement is the one cause here whose own answer reads only the first person: "i have a
# limp since my hip replacement" is the hip entry's line, but "my dad limps since his hip
# replacement" is not, so standing this row down left the third-person lines with nothing at all
# (modern-cap and tawny-octopus, both as request-changes). A gait that has an operation of its own
# behind it is not a fresh knock either, so those lines get this row's own weeks-and-a-GP card.
LIMP_REPLACED = (
    r"\b(?:hip|knee|joint)\s+replacement\b",
    r"\b(?:hip|knee|joint)\s+(?:op|operation)\b",
    r"\breplacement\s+(?:hip|knee|joint)\b",
)

# A band on a finger is jewellery until the finger swells: then the ring is what is stopping the
# blood, and the fix is taking it off rather than the sprain routine. The finger or hand word has
# to be there, because "ring" is a phone, a doorbell, a bathtub and a bird.
# "ring finger" is the name of a finger with no ring on it, so the bare word is not the band:
# "my ring finger is throbbing" was told to get off a ring it never mentioned. The negatives still
# find the band in "my ring finger is swollen under my ring", on its second word.
RING_WORD = (r"\bring\b(?!\s*fingers?\b)", r"\brings\b(?!\s*fingers?\b)",
             r"\bwedding\s+ring\b", r"\bengagement\s+ring\b", r"\beternity\s+ring\b")
FINGER_SIDE = (r"\bfinger\b", r"\bfingers\b", r"\bknuckle\b", r"\bhand\b", r"\bhands\b")


# Sight that has always been like that is a lifelong thing, not a stroke and not a limp: it wants
# an eye test and a GP, and the same-day call only if it has changed. The words that say "always"
# are the limp table's own (`LIMP_ONGOING`), because the same phrases name the same history.
# A limp is walked on: the leg words are what say the long-standing thing is a leg, so
# "my legs have been bad all my life" keeps the appointment and "my son has a droopy shoulder on
# one side since he was little" does not get the leg card.
# A pet's eyes are not a person's stroke sign.
PET_SIGHT = (
    r"\b(?:blind|going\s+blind|eyes?|sight|can'?t\s+see|cant\s+see|squint\w*|cataracts?)\b",
)
# The sugar in a recipe is not the sugar in a person.
SUGAR_IN_A_RECIPE = (
    r"\b(?:biscuits?|cakes?|scones?|bread|loaves|loaf|pastry|batter|dough|mixture|icing|"
    r"frosting|jam|sauce|pudding|dessert|crumble|cereal|yogurt|yoghurt|porridge|muffins?|"
    r"cookies?|brownies?|flapjacks?|granola|smoothie|milk|squash|lemonade)\b",
)
LEG_WORDS = (
    r"\b(?:legs?|knees?|ankles?|feet|foot|hips?|thighs?|calves|calf|shins?|heels?|toes?)\b"
)


# Somebody else's accident is not the speaker's, and a story is not happening at all.
OWN_INJURY_SOMEONE_OR_A_STORY = (
    r"\b(?:someone|somebody|a\s+person|people|anyone|everyone|your\s+friend)\b",
    r"\bfor\s+(?:a|my|the)\s+(?:story|novel|book|film|script|screenplay|essay|assignment)\b",
    r"\bin\s+(?:a|my|the)\s+(?:story|novel|book|film|game|dream)\b",
)
# "what do you do if your child has a nosebleed" is the same question as "my child": the bare
# "you" is how a person puts it to a friend, and it was answered with "I can talk through everyday
# health - what's going on?".
OWN_INJURY_YOU = (r"\byou\b", r"\byour\b")
OWN_INJURY_OTHER_PERSON = (
    r"\b(?:my|our)\s+(?:son|daughter|child|kid|kids|children|husband|wife|partner|boyfriend|"
    r"girlfriend|mum|mom|mother|dad|father|friend|neighbour|neighbor|colleague|boss|dog|cat)\b",
)
OWN_INJURY_NOT_ME = OWN_INJURY_SOMEONE_OR_A_STORY + OWN_INJURY_YOU + OWN_INJURY_OTHER_PERSON
A_BODY_PART = (
    r"\b(?:hands?|fingers?|fingertips?|thumbs?|arms?|wrists?|elbows?|tongue|mouth|throat|lips?|"
    r"faces?|cheeks?|nose|ears?|eyes?|feet|foot|toes?|legs?|knees?|shins?|chest|backs?|skin|palms?|"
    r"knuckles?|head|scalp|neck|stomach|belly)\b",
)
# A hair colour changing is the hair row's answer, not a person short of oxygen: "my beard has
# gone grey", "the greying at my temples" and "should i dye my grey roots" are all the same
# colour as cyanosis and none of them is about breathing.
GREY_HAIR = (
    r"\b(?:hair|hairs|beard|beards|moustache|mustache|eyebrows?|eyelashes?|roots|greying|graying|"
    r"greyed|grayed|bald|balding|receding|thinning|wig|dye|dyed|sideburns?)\b",
)
GREY_COLOUR = (r"\b(?:grey|gray)\b",)
# A grey that is arriving is a hair colour; a grey somebody *looked* or *was* is a shut-down. The
# bare-grey default used to take any grey with no body part in it, and that caught a person as
# well as a hair: "she looked grey", "my daughter looked grey" and "he looked grey and ill" all got
# 999 on main and got a shrug once the default was added. Only the progressive and the possessive
# are hair, so "im going grey", "why am i going grey", "my husband is going grey" and "grey roots"
# still stand the card down while "looked grey", "seemed grey" and "was grey" keep it.
GREY_ARRIVING = (
    # Only a grey that is still arriving is hair: "going grey", "turning grey", "getting grey".
    # A grey that has finished - "has gone grey", "went grey", "turned grey" - is a change that
    # happened, and a person who changed colour needs the card: "my son has gone grey", "my dad
    # has gone grey" and "ive gone grey all over" all rang on main. Where the hair is named, the
    # GREY_HAIR branch above settles it ("my hair has gone grey", "my beard has gone grey"), and
    # where a garment is named the science row declines it to the laundry card.
    r"\b(?:going|goes|go|turning|turns?|getting|gets)\s+(?:\w+\s+){0,2}(?:grey|gray)\b",
    r"\b(?:grey|gray)\s+(?:hair|hairs|roots|streaks?|patch|patches|temples?)\b",
)
# The speaker is a person too: "ive gone grey all over" is not a hair colour.
GREY_SELF = (r"\b(?:i|im|i'm|ive|i've|me|myself|my\s+own)\b",)
# The parts a grey shows on when it is not hair.
GREY_BODY = (*A_BODY_PART, r"\b(?:gums?|gum\s?colou?r|nail\s?beds?|fingertips?)\b")
# The signs that make a grey a shut-down rather than a hair colour. Anything in here keeps the
# 999 card, and "blue" and "purple" are in it so a line that says the colour plainly is untouched.
GREY_ALARM = (
    r"\b(?:clammy|sweating|sweaty|collapsed?|collapsing|faint(?:ed|ing|s)?|unconscious|"
    r"passed\s+out|passing\s+out|black(?:ed)?\s+out|breathless|struggling\s+to\s+breathe|"
    r"can'?t\s+breathe|cannot\s+breathe|blue|purple|mottled|rash|fitting|seizure|"
    r"unresponsive|limp|floppy|shock|bleeding|blood|vomiting|pulse|911|999)\b",
)
# Who can go blue: a body part, a person, or the speaker as the subject of the change. A possessive
# ("my phone went blue") is not enough, so the phone, the garlic and the screwdriver stand down
# while "my lips are blue", "her face went blue" and "i went blue" keep the card.
BLUE_HUMAN = (
    *A_BODY_PART,
    r"\b(?:he|she|they|we|him|them|he'?s|she'?s|they'?re|we'?re|myself|himself|herself|themselves|"
    r"everyone|anybody|somebody|someone|anyone)\b",
    r"\b(?:man|woman|boy|girl|child|children|baby|babies|toddler|infant|patient|kid|kids|son|"
    r"daughter|mum|mom|mother|dad|father|husband|wife|partner|boyfriend|girlfriend|brother|"
    r"sister|friend|gran|granny|grandma|grandad|grandpa|nan|nana|uncle|aunt|niece|nephew|"
    r"colleague|neighbour|neighbor|people|men|women|newborn|pupil|student)\b",
    # "i've gone blue all over" and "ive gone blue" are the same sentence as "i have gone blue":
    # the contraction was the only thing missing, and the colour spread over the whole of them
    # fell through to a shrug with it.
    r"\b(?:i|im|i'?m|i'?ve|ive)\s+(?:have\s+|had\s+|was\s+|were\s+|is\s+|am\s+)?"
    r"(?:gone|going|went|turned|turning|been)\b",
    r"\bi\s+(?:am|look|feel)\s+(?:blue|grey|gray|purple)\b",
    # The widest way of saying it is the whole body, and "my body" is a person where "my phone" is
    # not: dropping it from this list was how "my whole body went blue" lost the card to a laundry
    # answer. "all over" is the same sentence the other way round.
    r"\b(?:my|his|her|their|our|your)\s+(?:(?:whole|entire)\s+)?bod(?:y|ies)\b",
    r"\bbod(?:y|ies)\b[^.?!]{0,12}\b(?:went|gone|going|turned|turning|is|has|was)\s+"
    r"(?:blue|grey|gray|purple)\b",
    r"\b(?:i'?m|im|i\s+am)\s+(?:blue|grey|gray|purple)\s+all\s+over\b",
)

# A wood burner is a stove, not a burn. "how do i clean a wood burner" was reaching the first-aid
# reply because `burn` matched inside `burner`; a line that actually hurt someone still wins.
BURNER_THING = (r"\b(?:wood|log|gas|oil|pellet)\s*burner\b",)
# The food that is burnt is dinner, not a patient: "i burnt my sausages, can i still eat them"
# reached the cool-water card, because a burn verb and a possessive noun are all the burn row asks
# for, while the question the person asked - can i still eat it - is answered one module over.
# BURNT_FOOD is the list the fire case already keeps for "burnt toast is smoke, not a fire", and a
# second list here would be the same words twice and would shadow it; the burn row reads the same
# list. The stand-down needs no body part in the line, so "i burnt my hand on the sausages" and
# "i burnt my mouth on the tea" keep the first aid.
# A burn you are trying not to get and a burnout are both lines with the word burn in them and no
# injury in them: "how do i avoid burning my hand when cooking", "what if i burn myself out".
# Whoever answers prevention questions and burnout is a better answer than twenty minutes of water.
PREVENTION_OR_BURNOUT = (
    r"\b(?:avoid|avoiding|prevent|preventing|stop\s+myself|watch\s+out|be\s+careful)\b"
    r"[^.?!]{0,30}\b(?:burn\w*|scal\w*)",
    r"\bburn\w*\s+(?:myself|yourself|himself|herself|themselves|people|everyone)\s+out\b",
    r"\bburn(?:t|ed)?\s+out\b|\bburnout\b",
)
# A blister is not always a burn. New boots, a long walk and a rake handle rub blisters too, and
# those want a plaster and a better shoe, not twenty minutes under the cold tap. The burn answer
# keeps every blister that comes with heat, or with no cause named at all ("my hand is blistered").
BLISTER_WORD = (r"\bblister",)
# A burn said as a verb and then a body part is a heat burn, whatever else is in the line: "hot wax
# burnt my hand" and "waxing burnt my lip" are twenty minutes under the tap, and the razor stand-down
# below used to take them because "wax" is a hair-removal word. The past tense is what makes it a
# verb - "razor burn on my neck" names the complaint and keeps the shaving answer.
FRICTION_BURN = (
    r"\b(?:rope|carpet|mat|rug|friction|treadmill|tow\s+rope|road\s+rash|chaf\w+|sandpaper|"
    r"grip\s+tape)\b[^.?!]{0,20}\bburn\w*\b",
    r"\bburn\w*\b[^.?!]{0,20}\b(?:from|by|off)\s+(?:the\s+)?(?:rope|carpet|mat|rug|friction|"
    r"treadmill|grip\s+tape|sandpaper)\b",
)
# The friction word and the burn word together as a noun ("a rope burn", "carpet burn"), which is the
# complaint itself rather than a thing that is burning somewhere in the line.
FRICTION_BURN_NOUN = (
    r"\b(?:rope|carpet|mat|rug|friction|treadmill|road\s+rash|chaf\w+|grip\s+tape|sandpaper)"
    r"\s+burn\w*\b",
)
# The heat that turns a friction word into a real burn: "i burnt my hand on the iron while shaving"
# and "the rope was on fire" are the burn row's lines, not these.
FRICTION_BURN_HEAT = (
    r"\b(?:boiling|boiled|kettle|steam\w*|oven|hob|grill|toaster|hot\s+(?:water|oil|fat|pan|"
    r"plate|metal|iron)|scald\w*|fire|flame\w*|flames|alight|barbecue|bbq|fryer|sun\s?burn\w*|"
    r"curling\s+tongs|straighteners?|hair\s+dryer|blow\s+dry)\b",
)

BURN_WORD = (
    r"\b(?:burn\w*|scald\w*|scorch\w*|singe\w*|boiling|boiled|kettle|steam\w*|oven|hob|grill|"
    r"toaster|iron|fire|"
    r"flame\w*|barbecue|bbq|fryer|sun\s?burn\w*|hot\s+(?:water|oil|fat|pan|plate|metal)|"
    r"heat\s+rash)\b",
)


# "how do i treat a blister" names no cause and no heat: it is a plaster question, and twenty
# minutes under the cold tap answers nothing. A how-to about a blister is never the burn card
# while no burn word is in the line.
BLISTER_HOWTO = (
    r"\bhow\s+(?:do|should|can)\s+i\b",
    r"\bwhat\s+(?:do|should)\s+i\s+do\b",
    r"\b(?:treat|pop|burst|drain|cover|dress|protect|deal\s+with|get\s+rid\s+of)\b",
    r"\bshould\s+i\s+(?:pop|burst|drain|cover)\b",
)


def _ring_stuck(line):
    """True for a ring on a finger that is swelling or tightening round it."""
    return (_matches(RING_WORD, line) and _matches(FINGER_SIDE, line)
            and _matches(RING_DANGER, line) and not _matches(RING_NOT_WORN, line))


def _friction_blister(line):
    """True for a blister that rubbing made, which is a plaster question and not a burn."""
    if not _matches(BLISTER_WORD, line) or _matches(BURN_WORD, line):
        return False
    return (_matches(FRICTION_WORD, line)
            or (_matches(BLISTER_HOWTO, line) and not _matches(BURNT_SELF, line)))


def _tooth_out(line):
    """True when the line is a tooth that has been knocked or broken out, which is the dentist's."""
    if not _matches(TOOTH_OUT, line) or _matches(TOOTH_OUT_FINE, line):
        return False
    # "my son's tooth fell out" is the tooth fairy; the same words about a knock are not.
    if _matches(TOOTH_CHILD, line) and not _matches(TOOTH_KNOCK, line):
        return False
    return True


# What a stroke looks like in a line, said the ordinary way: the mouth, the words, one side gone.
FALL_STROKE_SIGN = (
    r"\b(?:slurr\w*|slurs?)\b",
    r"\bspeech\s+(?:is|was|sounds?|comes\s+out)\b[^.?!]{0,20}\b(?:slurr\w*|thick|strange|odd)\b",
    # "his words came out strange" is the same sign said about the words rather than the speech.
    r"\bwords?\s+(?:came|come|comes|coming)\s+out\b[^.?!]{0,14}"
    r"\b(?:strange|odd|wrong|thick|slurr\w*)\b",
    r"\b(?:face|mouth)\s+(?:is\s+|has\s+)?(?:droop\w*|dropping|gone\s+on\s+one\s+side|twisted)\b",
    r"\bone\s+side\s+(?:of\s+)?(?:his|her|their|the)\s+(?:body|face|arm)\b[^.?!]{0,24}"
    r"\b(?:gone|weak|numb|heavy|wont|won'?t|not\s+working)\b",
    r"\bcant\s+lift\s+(?:his|her|their)\s+arm\b",
    r"\bcan'?t\s+lift\s+(?:his|her|their)\s+arm\b",
)
# The dentist's injection, the pints, a gig review: the words a slurred phrase shares with a stroke.
SLUR_NOT_A_STROKE_WORDS = (
    r"\b(?:dentist|filling|injection|anaesthetic|numb\s+lip|pints?|drunk|drinking|beers?|"
    r"pub|gig|singer|song|lyric|wine)\b",
)


def _fall_with_sign(line):
    """A fall, or a pattern of them, with the person confused or not themselves after it.

    "my dad keeps falling over and hes confused" is the same bang-on-the-head call as "my dad fell
    and hes confused", and the count of falls is not what makes it one: the confusion is. The
    falls-review answer (strength, sight, medicines) is the right reply to a repeated fall on its
    own, which is why this has to be read before it.
    """
    if _matches(FALL_ASLEEP, line):
        return False  # a leg falling asleep is not a fall
    if _matches(FALL_WORD_IDIOM, line):
        return False  # slipping up is a mistake and tripping over your words is nerves
    if _matches(FALL_THING, line):
        return False  # the price falling is not a person falling
    if _matches(FALL_CHECK_OFF, line):
        return False  # "fell for a scam", "fell in love", "fallen behind with the rent"
    if _matches(CONFUSION_NAMED_CAUSE, line) and not _matches(
            (r"\b(?:now|worse|still|again|getting\s+worse)\b",), line):
        return False  # the confusion is their baseline, and the reply says what caused it
    return ((_matches(HEAD_FALL, line) or _matches(FALL_REPEAT, line))
            and _matches(HEAD_FALL_SIGN, line))


def _out_cold_knockout(line):
    """True when "out cold" is being knocked out, not a faint and not a night's sleep."""
    if _matches(OUT_COLD_ASLEEP, line) or _matches(OUT_COLD_NOW, line):
        return False
    return _matches(HEAD_OUT_COLD, line)


def _head_bang(line):
    """"red" for a bang on the head with a dangerous sign, "watch" for one without, None otherwise."""
    if not _matches(HEAD_BANG, line):
        if not _fall_with_sign(line):
            # A knock-out needs no head word, but it is history once a doctor has seen it or it
            # happened last year, which is the same guard a bang gets.
            if not (_matches(HEAD_KNOCKOUT, line) or _out_cold_knockout(line)) \
                    or _matches(HEAD_SEEN, line):
                return None
            if _matches(HEAD_PAST, line) and not _matches((r"\bstill\b", r"\bright\s+now\b"), line):
                return None
            if _tooth_out(line):
                return None  # a knocked-out tooth is not a knock-out, and it is the dentist's
            return "red"
        return "red"
    if _matches(HEAD_SEEN, line):
        return None
    if _matches(HEAD_PAST, line) and not _matches((r"\bstill\b", r"\bright\s+now\b"), line):
        return None
    if _matches(HEAD_RED, line):
        return "red"
    if _fainted_with_the_bang(line):
        return "red"
    return "watch"


PET_WORDS = (r"\b(?:dog|dogs|puppy|pup|cat|cats|kitten|horse|pony|rabbit|hamster|parrot|budgie|"
             r"bird|guinea\s+pig|gerbil)\b",)

# A plant or a garden that is dying is a plant: "my tomatoes are dying" is not a wish to die.
# A fish, a tank or a pond keeps a chore a chore: "our fish are going to die if we dont clean the
# tank" is the tank answer, and it was ringing the crisis line because nothing in PET_WORDS
# matched a fish. Kept apart from PET_WORDS so a hurt fish never reaches the pet-emergency rows.
AQUARIUM_WORDS = (r"\b(?:fish|fishes|goldfish|aquarium|fish\s?tank|pond|koi)\b",)

PLANT_WORDS = (r"\b(?:plant|plants|house\s?plants?|tomato|tomatoes|flower|flowers|shrub|tree|trees|"
               r"lawn|grass|garden|seedlings?|cuttings?)\b",)


_GO_ON_PHRASE = re.compile(r"\b(?:i\s+)?(?:just\s+)?(?:can'?t|cant|couldn'?t|couldnt)\s+go\s+on\b", re.I)

# "i cant go on living" is the wish even with a lawn in the line, so the phrase that says how it
# cannot go on is read before the garden fold stands anything down.
GO_ON_LIVING = (r"\b(?:go|going)\s+on\s+(?:living|existing)\b",)

# A garden, a lawn or a grass verge going over is maintenance, not a loss.
GARDEN_WORDS = (r"\b(?:lawn|lawns|grass|garden|gardens|plot|allotment|hedge|hedges|borders?)\b",)


def _head_person(line):
    """The injured person's pronouns: the one named, else the possessive in the line, else the user."""
    # "i banged my head and my wife is worried" is about the user, whatever else the line names.
    if re.search(r"\bi\s+(?:'ve\s+|had\s+|got\s+)?(?:bang|hit|knock|fell|fall|slip|trip|smack|crack|"
                 r"bash|smash)\w*", line):
        return None
    who = _person(line)
    if who:
        return who
    if re.search(r"\b(?:his|him|he)\b", line):
        return "he"
    if re.search(r"\b(?:her|she)\b", line):
        return "she"
    return None


def _weight_on_a_joint(line, today=False):
    """True when a named joint will not take weight, with no hip or fall behind it.

    "i cant put weight on my ankle" is a sprain or a small break that needs an X-ray today, and
    it was getting the spine answer - "stay where you are, don't try to stand" - because the
    weight bearing is also the test a hip fracture has to pass. The hip, the floor, a fall from a
    height and an older person who has gone down keep the ambulance. `today` asks for the reply
    too, and a foot that has been like this for weeks is the GP's rather than A&E's.
    """
    if not (_matches(WEIGHT_OFF_FEET, line) and _matches(WEIGHT_JOINT, line)):
        return False
    if _matches(WEIGHT_HIP, line):
        return False
    if _matches(WEIGHT_OLD, line) and _matches(WEIGHT_OLD_FALL, line):
        return False
    if today and _matches(WEIGHT_LONG, line):
        return False
    return True


# Taking burnt-on grime off a pan, a tray or an oven is a cleaning job with no person in it, and
# it came back as twenty minutes under running water. Three things together make it that job: a
# cleaning verb, something burnt, and a surface that can be cleaned. Any one of them alone is not
# enough - "how do i clean a burn on my hand" is about the injury - so all three have to be there,
# and a line that says a person was burnt keeps its first aid even when it also says "clean".
GRIME_CLEANING = (r"\b(?:clean|cleaning|cleaned|scrub\w*|scour\w*|soak\w*|remove|removing|"
                   r"wash\w*|lift|lifting|shift|shifting|get|getting)\b",)
BURNT_GRIME = (r"\b(?:burnt|burned|burning|scorched|charred|blackened)\b",)


# "how do i get burnt off the bottom of my oven": the burn sits right before an "off", which
# makes it something to get off a surface and not something that happened to a person - yet "i get
# burnt" inside the same line read as the person and the answer was twenty minutes under the tap.
GRIME_OFF = (r"\b(?:burnt|burned|scorched|charred|blackened)\s+"
             r"(?:bits?|stuff|food|grime|marks?|patches?|\w+)?\s*(?:off|out\s+of)\b",)


def _grime_on_a_surface(line):
    """True when the line is about cleaning burnt stuff off a pan, a tray or an oven."""
    if (_matches(GRIME_OFF, line) and _matches(CLEANABLE_SURFACE, line)
            and not _matches(BURNT_SELF, line)):
        return True
    return (_matches(GRIME_CLEANING, line) and _matches(BURNT_GRIME, line)
            and _matches(CLEANABLE_SURFACE, line)
            and not _matches(PERSON_BURNT, line) and not _matches(BURNT_SELF, line))


MILD_BODY_ESCALATION = (
    " An injury on top of feeling unwell is a 111 call today, and 999 if waking gets harder, "
    "breathing goes fast, or lips go grey or blue."
)


# The rows by name, for the two cases that borrow another row's answer further down.
_MINOR_REPLIES = {name: replies for name, _patterns, replies in MINOR}


# The MINOR rows that hand out a person's first aid. An animal that owns the injury must not get one
# of these, whatever the injury is - see the fence in the MINOR loop - so they are named once here.
PET_FIRST_AID_ROWS = frozenset((
    "bleeding", "cut", "burn", "sunburn", "mouth_burn", "splinter", "nosebleed", "part_off",
    "broken",
))


def _pet_first_aid(line):
    """The animal's own card for an injury the animal owns: a burn, a wound, or the vet-day card.

    The reply pools are returned unpicked, like every other row in `_first_aid`, so the caller that
    knows the chat can pick the one that fits.
    """
    if _matches(BURN_OR_SCALD_WORD, line):
        return REPLIES["pet_burn"]
    if _matches(PET_WOUND, line):
        return _MINOR_REPLIES["pet_wound"]
    return REPLIES["pet_hurt"]


# The injury a chat is already on, for the follow-up that names none: "i have a burn on my hand"
# then "how long will it take to heal" - the second line has no injury word in it, so the first-aid
# card that says the burn settles in a week to ten days was never reached and the turn went to a
# search hedge, or (after a cut) to the bone-healing row, which is a different injury. What a
# follow-up is about is the injury the chat is on, so the chat's own subject is lent to the line
# for this one reading. It is only a subject, and only when the line asks about the injury: the
# figure the card gives is what a person means by "how long will it take to heal" a turn later.
BURN_OR_SCALD_WORD = (r"\bburn(?:s|t|ed|ing)?\b", r"\bscald\w*\b")

THE_INJURY_NAMED_BEYOND_A_QUESTION = frozenset((
    "burn", "burns", "burnt", "burned", "scald", "scalds", "scalded", "cut", "cuts",
    "gash", "graze", "sprain", "sprains", "sprained", "blister", "blisters", "sunburn",
    "bruise", "bruises", "bruised", "wound", "wounds",
))


def _the_injury_the_chat_is_on(line, memory):
    """The injury the last first-aid card was about, when this line is a follow-up about it."""
    if not isinstance(memory, dict) or not _matches(ASKS_ABOUT_THE_INJURY, line):
        return ""
    # The card has to be the thing the chat is on: the injury was answered in the last few turns,
    # a bit of small talk may sit between it and the ask ("anyway we were meant to be going out").
    turns = memory.get("turns") or []
    last_card = ""
    for turn in reversed(turns[-3:]):
        if isinstance(turn, dict) and turn.get("module") == "safety":
            last_card = " ".join(str(turn.get("user") or "").lower().split())
            break
    if not last_card:
        return ""
    # Every other word of the line has to be the ask itself or a word the injury was said with:
    # "how long will it take to heal my hand" is still the burn when the burn was on the hand, and
    # "how long will the oven take to cool" is a question about the oven even in the same chat.
    earlier = set(last_card.split())
    if [word for word in line.split()
            if word not in A_FOLLOW_UP_ABOUT_THE_INJURY and word not in earlier]:
        return ""
    for name, words in HEAL_WORDS:
        if re.search(words, last_card):
            return name
    for word in THE_INJURY_NAMED_BEYOND_A_QUESTION:
        if re.search(r"\b" + word + r"\b", last_card):
            return word
    return ""


def _minor(line, memory=None):
    """The first-aid reply for a small injury, or None."""
    if memory is not None:
        injury = _the_injury_the_chat_is_on(line, memory)
        if injury and _first_aid(line) is None:
            # "how long will it take to heal" after the burn card is the burn's clock: read with the
            # injury the chat is on, which is the only way the card that knows it can be reached.
            line = line + " " + injury
    if _matches(WHOLE_BODY_RED_FLAG, line):
        return None  # a body that cannot be woken is not a small injury, whatever else is in the line
    reply = _first_aid(line)
    if reply is not None and _matches(MILD_BODY_SIGN, line):
        if isinstance(reply, tuple):
            return tuple(one + MILD_BODY_ESCALATION for one in reply)
        return reply + MILD_BODY_ESCALATION
    return reply


def _minor_replies(name):
    """The reply pool of the small-injury row called `name`, so a second route can give its card."""
    for row in MINOR:
        if row[0] == name:
            return row[2]
    return ()


def _first_aid(line):
    """The small-injury row the line matches, or None."""
    if _self_harm_intent(line):
        return None  # hurting yourself on purpose is not a small injury
    # A break in the back or the neck is not a small injury, whatever else is in the line.
    if _matches(SPINE_BREAK, line):
        # The one exception: a back that has gone numb below it is the cauda equina card, which was
        # answering these lines before this row existed and names the legs and the bladder.
        if _matches(SPINE_BACK_WORK, line) and not _matches(SPINE_BACK_FALL, line):
            return None  # a back that went at work is the strain card
        if _matches(SPINE_NUMB_LOWER, line) and not _matches(
                (r"\b(?:neck|spine|spinal)\b", r"\b(?:paralysed|paralyzed)\b",
                 r"\b(?:can'?t|cant|cannot)\s+move\b"), line):
            return None
        return SPINE_BREAK_ANSWER
    if _an_ordinary_helping(line):
        return None  # "she cuts herself a slice of cake" is not a cut to dress
    # "how do i avoid burning my hand when cooking" asks how not to get hurt, and "what if i burn
    # myself out" is not a burn at all; both are somebody else's answer. A line that says the burn
    # already happened still gets the first aid.
    if _matches(PREVENTION_OR_BURNOUT, line) and not _matches(BURNT_SELF, line):
        return None
    # "i got a burn from the oven" names the oven, but the oven is not what burnt: a line that
    # says the person was burnt is theirs, and the thing that does the burning is not a bake
    # thing_burnt = a thing was burnt, including burnt-on grime on a pan or an oven door
    thing_burnt = ((_matches(THING_BURNT, line) or _grime_on_a_surface(line))
                   and not _matches(A_BODY_PART, line)
                   and not _matches(BURNT_SELF, line))
    burner_thing = (_matches(BURNER_THING, line) and not _matches(A_BODY_PART, line)
                    and not _matches(BURNT_SELF, line))
    friction = _friction_blister(line)
    # See BURNT_FOOD: the food is what is burnt, and the person is asking whether to eat it.
    food_burnt = (_matches(BURNT_FOOD, line) and not _matches(A_BODY_PART, line)
                  and not _matches(BURNT_SELF, line))
    # A razor burn is friction and irritation, and the shaving answer already exists one module
    # over and answers the bare line well: "razor burn" and "how do i stop razor burn" both get it
    # on main. Only the body part broke it - "razor burn on my neck" got the scalded-hand card,
    # twenty minutes under cool running water - so the burn rows pass on the shaving words and the
    # line falls through to that answer. Rope, carpet and mat burns have no answer anywhere and
    # want a first-aid card of their own.
    razor = (_matches(RAZOR_BURN, line) and not _matches(FRICTION_BURN_HEAT, line)
             and not _matches(BURNT_BODY_VERB, line))
    # The card is for skin, so the line has to have some: "carpet burn on my knee" and "a rope burn
    # on my hands" do, while "the carpet smells of burning" and "my treadmill belt is burning" are
    # about the carpet and the belt. The noun is enough on its own for the question - "how do i
    # treat a rope burn" - because there the burn is the thing being asked about.
    if (_matches(FRICTION_BURN, line) and not _matches(FRICTION_BURN_HEAT, line) and not razor
            and (_matches(A_BODY_PART, line) or _matches(FRICTION_BURN_NOUN, line))):
        return REPLIES["friction_burn"]
    # A blister on a hand, an arm or a shoulder is a plaster question, and nothing below this
    # answers it: the shoe rows only know feet and heels.
    if _matches(BLISTER_STATE, line) and not _matches(BURN_WORD, line) \
            and not _matches(BLISTER_CAUSE_BURN, line):
        return BLISTER_STATE_REPLIES
    # "how long does it take to heal" is a different question from "what do i do about it", and
    # people ask it about the injury itself ("a sprained ankle"), not only their own.
    if _matches(HOW_LONG, line):
        if re.search(r"\bsun\s?burn", line):
            return HEAL_TIME["sunburn"]
        for name, words in HEAL_WORDS:
            if (name == "cut" and _matches(FOOD_CUT, line) and not _matches(A_BODY_PART, line)
                    and not re.search(CUT_SELF, line)):
                continue
            if (name == "cut" and _matches(NOT_A_BODY_CUT, line)
                    and not _matches(A_BODY_PART, line) and not re.search(CUT_SELF, line)):
                continue
            if re.search(words, line):
                return HEAL_TIME[name]
    # A grater takes a knuckle as often as a knife takes a finger, and main had no verb for it:
    # "i grated my knuckle on the cheese grater" got "How was it, overall?". The cut card is this
    # line's answer, and a recipe - "how do i grate cheese" - names no body part, so it stays out.
    if _matches(GRATER_CUT, line):
        return _MINOR_REPLIES["cut"]
    for name, patterns, replies in MINOR:
        if name == "burn" and (thing_burnt or burner_thing or friction or razor
                               or food_burnt):
            continue
        # "i cut myself off from my friends" is company, not a cut - see _cut_off_idiom.
        if name == "cut" and _cut_off_idiom(line):
            continue
        if (name == "broken" and _matches(BONE_OUT_LOOSE, line) and _matches(FOOD_BONE, line)
                and not re.search(BODY_LIMB, line)):
            continue
        if (name == "cut" and _matches(FOOD_CUT, line) and not _matches(A_BODY_PART, line)
                and not re.search(CUT_SELF, line)):
            continue
        # A limp named on a hand, an arm or a shoulder is that limb's small injury, not the leg's:
        # the card below is the one a wrist already gets for a knock.
        if name == "limp" and _matches(LIMP_OTHER_LIMB, line):
            return _MINOR_REPLIES["sprain"]
        if name in ("limp", "limp_long") and _matches(LIMP_NOT, line):
            continue
        # The limp follows the unstable joint rather than being the problem: that line is the
        # knee or the ankle entry's, and ice is not the answer to a joint that gives way.
        if name in ("limp", "limp_long") and _matches(LIMP_MECHANISM, line):
            continue
        if name == "limp_long" and not _matches(LIMP_LONG, line):
            continue
        if name == "limp" and _matches(LIMP_LONG, line):
            continue
        # A named cause is that answer's line, not this first aid; a long-standing one is the
        # weeks-to-the-GP card rather than rest and ice.
        if name == "limp" and _matches(LIMP_CAUSE, line):
            # ...but only when there is a limp in the line: "my mum's got a hip replacement booked
            # for june" is a plan, and answered with "a limp that has been going on for weeks" it
            # was advice for a symptom nobody mentioned.
            if _matches(LIMP_REPLACED, line) and _matches(LIMP_SOMEBODY_ELSE, line) \
                    and re.search(r"\b(?:limp\w*|hobbl\w*|gait|walk\w*)\b", line):
                return _MINOR_REPLIES["limp_long"]
            continue
        # ...and the long-standing cause is about a limp, so it needs a limp or a limb in the
        # line. Without the door every line with `all my life` or `since birth` in it came back
        # as "A limp that has been going on for weeks", and a sight line answered with a leg is
        # worse than the shrug it should have had (azure-trout's read of #2292).
        if name == "sight_long" and not _matches(LIMP_ONGOING, line):
            continue
        if name == "limp" and _matches(LIMP_ONGOING, line) \
                and (_matches(LIMP_PERSON, line)
                     or re.search(r"\b(?:limp\w*|hobbl\w*|gait)\b", line)
                     or re.search(LEG_WORDS, line)):
            return _MINOR_REPLIES["limp_long"]
        if name == "weight_limb_long" and not (_weight_on_a_joint(line)
                                             and _matches(WEIGHT_LONG, line)):
            continue
        if name == "weight_limb" and not _weight_on_a_joint(line, today=True):
            continue
        if name == "ring_stuck" and not _ring_stuck(line):
            continue
        # ...and only for a tooth that has actually gone, so "my dog has bad teeth" keeps the
        # vet-visit answer it already had.
        if name in ("tooth_out", "tooth_chipped") and _matches(PET_TOOTH, line) \
                and _matches(patterns, line):
            return REPLIES["pet_tooth"]
        # An animal's wound is the animal's, but only when the animal is the one hurt: "my dog bit
        # my hand and it is bleeding" and "my cat scratched me and it is bleeding" have the animal
        # and a bleeding in them and belong to the person's first aid, so a person in the line keeps
        # the human card. This row now reads "bleeding" as well as "cut", so it needs that fence.
        if name == "pet_wound" and (_matches(HUMAN_TOO, line)
                                    or _matches(HUMAN_BITTEN, line)):
            continue
        # An animal that owns an injury is the vet's, and the person's first-aid rows are the wrong
        # card for it however the injury is worded: "my dog cut his paw and it is bleeding a bit" and
        # "my dog has a bit of bleeding from his paw" got a card ending "if it's still going after
        # twenty minutes or they go pale or dizzy, that's 999"; "my dog burnt his paw" got the burn
        # card about a person's face, hands and joints; "my cat has a splinter in her paw" got warm
        # water and tweezers for a hand; and "my dog grazed his knee" got a card that ends "a nurse
        # or A&E". The animal's own cards are the ones to reach. A person hurt in the same line keeps
        # the person's card: "my dog bit my hand and it is bleeding" names the person's hand.
        if name in PET_FIRST_AID_ROWS and _matches(PET_ANIMAL_HURT, line) \
                and not _matches(HUMAN_TOO, line) and not _matches(HUMAN_BITTEN, line) \
                and not _matches(HUMAN_OWN_INJURY, line) \
                and not _matches(PET_PASSES_BLOOD, line) \
                and not _matches(PET_OWNS_A_THING, line):
            return _pet_first_aid(line)
        if name == "tooth_out" and not _tooth_out(line):
            continue
        if name == "tooth_chipped" and (_matches(TOOTH_CHIPPED_FINE, line) or _tooth_out(line)):
            continue
        if _matches(patterns, line):
            return replies
    if _matches(HOW_TO_TREAT, line) and not thing_burnt and not burner_thing:
        for name, words in INJURY_WORDS:
            if name == "burn" and (friction or razor or food_burnt):
                continue
            if _matches(words, line):
                for case, _, replies in MINOR:
                    if case == name:
                        return replies
    return None


def _last_case(memory):
    """The case of the most recent safety reply, if it was one of the last two turns."""
    if not isinstance(memory, dict):
        return None
    recent = (memory.get("turns") or [])[-2:]
    if not any(isinstance(turn, dict) and turn.get("module") == "safety" for turn in recent):
        return None
    case = memory.get("safety_case")
    if case in WAITING:
        return case
    for turn in reversed(recent):
        if not isinstance(turn, dict) or turn.get("module") != "safety":
            continue
        said = turn.get("bot") or ""
        for name, options in REPLIES.items():
            if said in options:
                return name
        return None
    return None

CPR_ASK = (
    r"\bcpr\b", r"\bcompressions?\b", r"\brescue\s+breaths?\b", r"\bbreaths?\s+(?:to|and)\s+",
    r"\bhow\s+(?:hard|fast|deep|many)\b", r"\btoo\s+(?:hard|fast|deep|soft|slow|gentle)\b",
)
CPR_SCENE = (
    r"\bnot\s+breathing\b", r"\bstopped\s+breathing\b", r"\b(?:start|do|doing)\s+cpr\b",
    r"\bcpr\b", r"\bnot\s+waking\b", r"\bunconscious\b", r"\bcollapsed\b",
    r"\brecovery\s+position\b", r"\bno\s+pulse\b",
)
# A thing being pushed is not a chest being pushed: the brake pedal, the pram, the drill and the
# weights keep their own answers.
CPR_NOT_A_BODY = (
    r"\b(?:brakes?|pedal|clutch|throttle|pram|pushchair|wheelchair|trolley|barrow|mower|hoover|"
    r"vacuum|door|doors|drill|screw|nail|brush|paint\w*|button|buttons|lever|handle|swing|"
    r"snooze|send|reply|publish|commit|merge|updates?)\b",
)
# A scene that is still running keeps the floor: a question in the middle of one is the follow-up
# handler's, which answers it in the scene's own words. Anything else - a GP-visit case, a story,
# nothing at all - is a person learning the numbers, and that is this arm.
CPR_SCENE_CASES = (
    "breathing", "not_breathing", "unconscious", "choking", "drowning", "hanging", "bleeding",
    "chest", "stroke", "seizure", "overdose", "anaphylaxis", "fire", "gas", "self_harm",
)
# A pulse or a breath named in the question changes the action, and the numbers alone never say
# so: "can i do cpr if they have a pulse" was getting "push hard and fast" and nothing else.
CPR_STILL_ALIVE = (
    r"\b(?:a\s+)?(?:pulse|heartbeat|heart\s+beat)\b", r"\bstill\s+breathing\b",
    r"\bbreathing\s+(?:normally|on\s+(?:his|her|their)\s+own|by\s+(?:him|her|them)sel(?:f|ves))\b",
    r"\b(?:is|are|was|were)\s+breathing\b",
)
CPR_NOT_ALIVE = (
    r"\bno\s+(?:pulse|heartbeat)\b", r"\bnot\s+breathing\b", r"\bstopped\s+breathing\b",
    r"\b(?:isn'?t|aren'?t|isnt|arent)\s+breathing\b",
)
# No pulse is the other side of the same question, and it is the start signal rather than a reason
# to wait: "can i do cpr if they have no pulse" was answered with the recovery position.
CPR_NO_PULSE = (r"\bno\s+(?:pulse|heartbeat)\b",)
# 30:2 at 5-6 cm is the adult sequence. A baby gets five rescue breaths first, then 15
# compressions with two fingers to about a third of the depth; a child the same 15:2 with the heel
# of one hand. Somebody reading this at 3am is holding the person, so the age on the line chooses
# the sequence.
CPR_BABY = (
    r"\b(?:baby|babies|newborn|new\s?born|infant|infants)\b",
    r"\b\d+\s*(?:day|week|month)s?\s*old\b", r"\bunder\s+(?:one|1|a)\b",
    r"\b(?:six|seven|eight|nine|ten|eleven|two|three|four|five)\s+(?:weeks?|months?)\s+old\b",
)


CALL_HELP = (
    r"\bshould\s+i\s+(?:call|ring|phone|dial)\b.{0,25}\b(?:ambulance|999|911|112|help|doctor)\b",
    r"\bdo\s+(?:i|we)\s+need\s+(?:an\s+)?ambulance\b",
    r"\bshall\s+i\s+(?:call|ring|phone)\b",
    r"\bis\s+it\s+(?:bad\s+enough\s+)?(?:for\s+)?an\s+ambulance\b",
)
# Aspirin is part of the first minutes of a heart attack, so "should i take an aspirin" in a chest
# thread gets an answer rather than the scene's general advice. Only for the chest: after a stroke
# aspirin is the one thing that can make a bleed worse.
ASPIRIN = (
    r"\b(?:should|can|shall|do|could)\s+(?:i|we|he|she|they)\s+(?:take|have|give|chew)\b"
    r"[^.?!]{0,25}\baspirin\b",
    r"\baspirin\b[^.?!]{0,25}\b(?:ok|okay|safe|help|good|wise)\b",
    r"\b(?:give|take|chew)\b[^.?!]{0,20}\baspirin\b",
)
# The manner a child settles in by, and what may follow it and leave it a manner: nothing, a
# calendar word, or the place being settled into. The list is the composer's SETTLING exactly
# (bot/compose/urgent.py), so one word decides both layers. "better", "great", "ok" and "okay" are
# not in it: `he is fitting better now but he had 3 today` is three fits and a seizure line, and
# `my son is fitting ok now` is a fit the composer already rings.
FITTING_MANNER = re.compile(
    r"\bfitting\s+(?:in\s+)?(?:nicely|well|perfectly|fine|easily|beautifully|smoothly|"
    r"brilliantly)\b")


def _a_settling_fit(line):
    """True when the manner word after "fitting" is all there is, or a calendar or a place.

    `my son is fitting nicely` and `fitting well today` are a child settling in, and so is
    `fitting in nicely at nursery`. `fitting nicely but still having them`, `fitting well and then
    sleeping for hours` and `fitting nicely in the car` are a fit that is still going: the tail is
    the red flag, so the card stays and the manner word in front of it settles nothing.
    """
    found = FITTING_MANNER.search(line)
    if not found:
        return False
    return bool(FITTING_MANNER_TAIL.match(line[found.end():].strip(" .,!?;:")))


# The other half of the same idiom: a person can be fitting something on - shoes, a helmet, a new
# blind. "is fitting" is a fit only when nothing comes after it that the person is fitting.
FITTING_THING = (
    r"\bfitting\s+(?:his|her|their|my|your|our|its|him|them|me|a|an|the|new|another|some|"
    r"these|those|this)\b",
)


# "sorry i mean my mum" is a correction of who is in trouble, said about a case that is still
# open. It used to fall through to the memory module and come back "Got it - you mean your mum",
# which leaves a chest pain with nobody telling anyone to ring 999. The advice does not change
# with the person, so the escalation is said again, to the right person, with no hedging.
CORRECTION_OF_PERSON = (
    r"\b(?:sorry|no|actually|wait)?,?\s*i\s+mean\s+(?:my|his|her|the|its)\b",
    r"\bnot\s+(?:my|the)\s+\w+\s*,?\s*(?:it'?s|its|but)\b",
    r"\b(?:i\s+meant|i\s+said)\s+(?:my|the)\b",
    r"\bwrong\s+person\b",
)


def _last_said_as_written(memory):
    """The last safety reply as it was typed: _last_said lowercases, and this one is said again."""
    if not isinstance(memory, dict):
        return ""
    for turn in reversed((memory.get("turns") or [])[-3:]):
        if isinstance(turn, dict) and turn.get("module") == "safety":
            return turn.get("bot") or ""
    return ""


def _resay(raw, line, memory):
    """The escalation said again about the person the correction names."""
    who = _person(line)
    if who:
        if isinstance(memory, dict):
            memory["safety_person"] = who
        pairs = (("him", "her"), ("his", "her"), ("he", "she"), ("he's", "she's"),
                 ("himself", "herself"), ("them", "her"), ("their", "her")) \
            if who == "she" else (
                ("her", "him"), ("hers", "his"), ("she", "he"), ("she's", "he's"),
                ("herself", "himself"), ("them", "him"), ("their", "his"))
        for word, swap in pairs:
            raw = re.sub(r"\b" + word + r"\b", swap, raw)
    return raw


# ...but not when the same line also asks what to do next: that is a follow-up with its own
# answer, and the tables above have already had their turn.
ESCALATED_ALREADY = (
    r"\bshould\s+i\b", r"\bwhat\s+(?:do|should)\s+i\b", r"\bshall\s+i\b",
    r"\bcan\s+i\b", r"\bhow\s+(?:do|long|much)\b",
)
DETAIL_REPLY = (
    "Got that - tell the 999 or 911 handler it as well, and stay with them until the ambulance "
    "comes.",
    "Tell the 999 or 911 handler that too. Stay with them and keep them talking until the "
    "ambulance arrives.",
)


def _name_the_person(reply, line, memory):
    """A follow-up that says "stay with them" says "stay with him" when the first turn named him."""
    # The line's own "he" wins over the first turn's, so "is he going to be ok" after "my dad
    # collapsed" says "him" and not "them".
    named = _person(line) or (memory.get("safety_person") if isinstance(memory, dict) else None)
    if named is None:
        return reply
    pairs = (("them", "her"), ("their", "her"), ("they're", "she's")) if named == "she" else (
        ("them", "him"), ("their", "his"), ("they're", "he's"))
    for word, swap in pairs:
        reply = re.sub(r"\b" + word + r"\b", swap, reply)
    return reply


def _true_newborn(memory):
    """A baby under five weeks, from what was typed before: the age a "feels hot" alone is for.

    Same walk as _tiny_baby, with the ages that have grown past the newborn's own card settling it
    the other way: "my baby is 3 weeks old" then "shes 7 weeks now" then "she feels hot" is the
    same-day call.
    """
    if not isinstance(memory, dict):
        return False
    for turn in reversed((memory.get("turns") or [])[-4:]):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if not said:
            continue
        if _matches(TRUE_NEWBORN_FINE, said):
            return False
        if _matches(TRUE_NEWBORN, said):
            return True
    return False


def _tiny_baby(memory):
    """An earlier line said a baby under three months, so a fever now is that baby's fever.

    The age is read from the last few things the person typed, newest first, and an age that is
    old enough settles it: "my baby is 3 weeks old" then "shes 14 weeks now" then a temperature is
    not the hospital call any more.
    """
    if not isinstance(memory, dict):
        return False
    for turn in reversed((memory.get("turns") or [])[-4:]):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if not said:
            continue
        if _matches(TINY_AGE_FINE, said):
            return False
        if _matches(TINY_AGE, said):
            return True
    return False


def _last_said(memory):
    """What the bot last said as a safety reply, so a follow-up knows which scene it is in."""
    if not isinstance(memory, dict):
        return ""
    for turn in reversed((memory.get("turns") or [])[-3:]):
        if isinstance(turn, dict) and turn.get("module") == "safety":
            return (turn.get("bot") or "").lower()
    return ""


# "Should I turn it off" after "the plug socket is sparking" is not a personal decision to weigh
# up: it is the one thing every fire service says, and handing it back ("That's your call, not
# mine") or answering about a phone that shuts itself down leaves someone standing next to a
# sparking socket. The hazard is in the person's own words a turn earlier, so the act question is
# read against what they already said, not against the line on its own - which carries no hazard
# word at all and so reached nothing above.
# The verb is what the act is done to the thing with, and "use" is deliberately not one: "should i
# use cream" on a sunburn is the same shape as "should i unplug it" and wants a pharmacist, not a
# plug. "Keep" and "go on" only count with "using" after them, which is the act again.
_AN_ACT_OR_NOT = (
    r"(?:\b(?:should|shall|do|can|could|ought|may)\s+(?:i|we)\b|"
    r"\b(?:is|would)\s+it\s+(?:be\s+)?(?:ok(?:ay)?|alright|all\s+right|safe|fine)\s+to)\b"
    r"[^.?!]{0,40}?"
    r"(?:\b(?:turn|switch|shut|plug|unplug|disconnect|stop|leave|touch|kill|put|pour|throw|run|stay|"
    r"move|carry|open|cover|smother|fan)\b|"
    r"\b(?:keep|go\s+on|carry\s+on)\s+using\b|\buse\s+it\s+again\b)")
_A_LIVE_HAZARD = (
    r"\b(?:spark(?:s|ing|ed)?|fizz(?:ing|ed)?|smok(?:e|ing|y)|smoulder(?:ing)?|smolder(?:ing)?|"
    r"burn(?:ing|t)?|scorch(?:ed|ing)?|melt(?:ing|ed)?|buzz(?:ing)?|on\s+fire|caught\s+fire|"
    r"too\s+hot\s+to\s+touch|red\s+hot)\b")

# The other half of the same question, and the one that follows the first answer: "can i turn it
# back on" is not a decision either, and a thing that has sparked once does it again.
BACK_ON = (
    "Not yet - leave it off and unplugged until someone has looked at it. Whatever sparked or "
    "smoked once will do it again, and the next time nobody may be in the room.",
    "I would not. Keep it out of use until it has been checked: the fault that sparked it has not "
    "gone away by itself, and a fire is a lot harder to put out than a plug is to leave alone.",
)
# The hazard word alone does not make the thing in hand a socket. "i burnt my hand on the oven"
# names a burn on a person, and the act question after it ("should i cover it", "should i put
# anything on it") is a burn question: it was answered with the switch-it-off-at-the-wall card,
# which is an electric instruction for a hand. A line that hurt somebody is not the thing that
# sparked, so it is read out of the hazard the act question is about. "the wire burnt me" is that
# line too - what a burn on skin wants is cool water, not an unplugged appliance.
_A_BURNT_PERSON = (
    r"\b(?:hand|hands|arm|arms|finger|fingers|thumb|thumbs|skin|wrist|wrists|foot|feet|leg|legs|"
    r"knee|knees|shoulder|shoulders|chest|face|eyes?|head|hair|lip|lips|tongue|mouth|neck|ears?|"
    r"blister(?:s|ed|ing)?|myself|himself|herself|themselves|me)\b")
_A_WANTS_IT_ON = (
    r"\b(?:back\s+on|on\s+again|switch\s+it\s+on|turn\s+it\s+on|plug\s+it\s+(?:back\s+)?in|"
    r"use\s+it\s+again|start\s+it\s+(?:up\s+)?again)\b")

# The first sentence is the answer, because "should I?" wants a yes before it wants reasoning.
SWITCH_OFF = (
    "Yes - switch it off at the wall, and unplug it if you can reach the plug without touching "
    "anything hot or wet. Leave it out of use until someone has looked at it.",
    "Off, and unplugged if you can do that safely. Whatever sparked or smoked is not safe to use "
    "again until it has been checked - and if it is burning or smoking now, get out and ring 999 "
    "rather than stay with it.",
    "Switch it off at the wall and unplug it, without touching the metal or anything wet, then "
    "keep it out of use. A thing that has sparked once does it again, and this one wants looking "
    "at before it goes back on.",
)


def _follow_up(line, memory):
    """A reply to a follow-up asked while an emergency reply is still the last thing said."""
    # The act question after a live hazard. Read first, because it is the one where a wrong answer
    # costs somebody: the pool that answered it ("That's your call, not mine") is for a choice with
    # two sides, and there is only one side to a socket that is sparking.
    hazard = _said_before(memory, 2) if isinstance(memory, dict) else ""
    if isinstance(memory, dict) and _matches(_AN_ACT_OR_NOT, line) \
            and _matches(_A_LIVE_HAZARD, hazard) \
            and not _matches(_A_BURNT_PERSON, hazard) \
            and not _matches(_A_LIVE_HAZARD, line):
        # A pan of oil and a person alight have their own ten seconds, and neither answer is "a
        # socket": the card that was just given already carries the one thing not to do (water on
        # fat, running, carrying it), so it is the answer to the act question as well as to the
        # fire, and it is served again rather than replaced with a narrower rule.
        case = str(_last_case(memory) or "")
        if case in ("pan_fire", "clothes_fire"):
            _note(memory, "fire" if case == "pan_fire" else case)
            return _fit(pick(REPLIES[case], memory), line, case)
        _note(memory, "fire")
        if _matches(_A_WANTS_IT_ON, line):
            return _fit(pick(BACK_ON, memory), line, "fire")
        return _fit(pick(SWITCH_OFF, memory), line, "fire")
    # The crisis card holds the thread while the person is still saying how it would happen. A
    # plan, a note, the means, a date - "i have a plan", "i wrote a note", "how long till that" -
    # carry no harm word of their own, so nothing above read them and the fallback answered a
    # suicide disclosure with "Nice - how did it go?" or "That's coming up. What do you want to
    # get right?". The shapes that turn towards help keep their own answers (the AFTER pool, "i
    # rang the line", "im ok now"), which is what the OFF list is for.
    # The turn after a near miss with fire: "no it didnt catch, i caught it in time" was answered
    # "I'm listening - say more if it helps", which leaves someone still watching a pan.
    if isinstance(memory, dict) and memory.get("safety_case") == "near_fire" \
            and any(isinstance(t, dict) and t.get("module") == "safety"
                    for t in (memory.get("turns") or [])[-2:]) \
            and _matches(NEAR_FIRE_OVER, line) \
            and not _says_something_is_burning(line):
        return _fit(pick(REPLIES["near_fire_over"], memory), line)
    # The turn after a road scare is still that scare: "it was a white van" after "someone nearly
    # hit me at the crossing" was answered "Good to hear. What was the best bit?".
    if isinstance(memory, dict) and memory.get("safety_case") in ("near_thing", "struck_my_bike") \
            and any(isinstance(t, dict) and t.get("module") == "safety"
                    for t in (memory.get("turns") or [])[-2:]) \
            and _matches(NEAR_THING_OVER, line):
        return _fit(pick(REPLIES["near_thing_over"], memory), line)
    if str(_last_case(memory) or "") in WISH_FRAMES + ("self_harm_other", "poison") \
            and _matches(HELD_CRISIS_DETAIL, line) and not _matches(HELD_CRISIS_OFF, line) \
            and not _matches(CRISIS_PLAN_ORDINARY, line):
        _note(memory, "self_harm")
        return _fit(pick(REPLIES["self_harm"], memory), line, "self_harm")
    # A plan said on its own, in the first turn as much as the third: "my plan is to jump", "the
    # plan is to take all of them", "i know how id do it", "im going to do it" with nothing after
    # it. No wish word, so nothing below reads it and the person gets "Worth doing. What would you
    # like help with first?". The plan card is the right card: a person in the room, means away.
    if _matches(A_PLAN_SAID, line) and not _matches(A_PLAN_ORDINARY, line):
        _note(memory, "self_harm")
        return pick(CRISIS_PLAN_REPLY, memory)
    # The numbing is the one card whose follow-up is a duration, and it is settled here rather
    # than in the waiting table, so an ordinary line after it ("will he be ok for school") is not
    # answered as if an ambulance were coming.
    # The toddler card asks whether the words went thick suddenly. The answer to that is either
    # the ambulance or the health visitor, and it is never the emergency hold's "do what the line
    # says" - "no hes always been like that" got that, which is the opposite of the truth.
    said_child = any(isinstance(t, dict) and t.get("module") == "safety"
                     and (t.get("bot") or "") in REPLIES["slur_small_child"]
                     for t in ((memory.get("turns") or [])[-2:] if isinstance(memory, dict) else []))
    if said_child:
        # A fever, a rash, a fit or a child who is floppy with it is not the wait-and-see answer
        # however slowly the words came: that is seen today.
        if _matches(SLUR_SMALL_CHILD_URGENT, line):
            return _fit(pick(SLUR_SMALL_CHILD_URGENT_REPLY, memory), line)
        if _matches(SLUR_SUDDEN, line):
            _note(memory, "stroke")
            return _fit(pick(REPLIES["stroke"], memory), line, "stroke")
        if _matches(SLUR_NOT_SUDDEN, line):
            return _fit(pick(SLUR_SMALL_CHILD_CALM, memory), line)
        return None
    if _matches(DENTAL_NUMB_ASK, line) and isinstance(memory, dict) \
            and memory.get("safety_case") == "dental_numb" \
            and any(isinstance(t, dict) and t.get("module") == "safety"
                    for t in (memory.get("turns") or [])[-2:]):
        return _fit(pick(DENTAL_NUMB_FOLLOW, memory), line)
    # The withdrawal card is a caution, not a scene: there is no ambulance coming, so a symptom
    # said a turn later gets the next step and anything else gets its ordinary answer.
    if str(_last_case(memory) or "").startswith("alcohol_withdrawal") \
            and any(isinstance(t, dict) and t.get("module") == "safety"
                    for t in (memory.get("turns") or [])[-2:]):
        if _severe(line):
            _note(memory, "alcohol_withdrawal_severe")
            return _fit(pick(REPLIES["alcohol_withdrawal_severe"], memory), line)
        if _matches(WITHDRAWAL_WORSE, line):
            _note(memory, "alcohol_withdrawal_more")
            return _fit(pick(REPLIES["alcohol_withdrawal_worse"], memory), line)
        if _matches(WITHDRAWAL_SYMPTOM, line):
            _note(memory, "alcohol_withdrawal_more")
            return _fit(pick(REPLIES["alcohol_withdrawal_more"], memory), line)
        if _matches(WITHDRAWAL_DURATION, line):
            _note(memory, "alcohol_withdrawal_more")
            return _fit(pick(REPLIES["alcohol_withdrawal_when"], memory), line)
        # "should i have a beer to help me sleep" is the hair of the dog, and it is the one question
        # where the honest answer is no - the units card is the reply to a different question.
        if _matches(WITHDRAWAL_HAIR_OF_THE_DOG, line):
            _note(memory, "alcohol_withdrawal_more")
            return _fit(pick(REPLIES["alcohol_withdrawal_hair"], memory), line)
        if _matches(WITHDRAWAL_DANGER, line):
            _note(memory, "alcohol_withdrawal_more")
            return _fit(pick(REPLIES["alcohol_withdrawal_danger"], memory), line)
        return None
    # A calm card is not a scene with an ambulance in it. "will he be ok for work tomorrow" after
    # the drink card got "keep the 999 or 911 call handler", which is about a person who is not
    # in an emergency at all.
    calm = (REPLIES["dental_numb"] + REPLIES["slur_drink"] + REPLIES["alcohol_withdrawal"]
            + REPLIES["alcohol_withdrawal_more"] + REPLIES["alcohol_withdrawal_when"]
            + REPLIES["alcohol_withdrawal_danger"] + REPLIES["alcohol_withdrawal_worse"])
    if any(isinstance(t, dict) and t.get("module") == "safety" and (t.get("bot") or "") in calm
           for t in ((memory.get("turns") or [])[-2:] if isinstance(memory, dict) else [])):
        return None
    case = _last_case(memory)
    if case is None:
        return None
    # Someone asking how to do CPR, or whether they are doing it right, is never asking anything
    # else: it gets the numbers rather than the scene's general advice.
    said = _last_said(memory)
    # Choking is left out on purpose: "when should i stop back blows" wants the choking cycle, not
    # the CPR answer, and a choking case that has reached CPR has been re-cased as not breathing.
    if case in ("breathing", "not_breathing", "unconscious", "drowning", "hanging") \
            and _matches(CPR_STOP, line):
        return pick(CPR_STOP_REPLY, memory)
    if _matches(CPR_ASK, line) and (_matches(CPR_SCENE, said) or case in (
            "breathing", "not_breathing", "unconscious", "choking", "drowning", "hanging",
            "general", "chest")):
        baby = _matches(CPR_BABY, line) or _matches(CPR_BABY, said)
        child = _matches(CPR_CHILD, line) or _matches(CPR_CHILD, said)
        if _matches((r"\btoo\s+(?:hard|fast|deep|soft|slow|gentle)\b", r"\bdoing\s+it\s+"
                     r"(?:right|wrong)\b", r"\bam\s+i\s+doing\b"), line):
            return pick(CPR_ROUGH, memory)
        if baby:
            return pick(CPR_BABY_SCENE, memory)
        if child:
            return pick(CPR_CHILD_SCENE, memory)
        if _matches((r"\bshould\s+i\b", r"\bdo\s+i\b", r"\bshall\s+i\b", r"\bstart\b"),
                    line):
            return pick(CPR_START, memory)
        return pick(CPR_HOW, memory)
    # "how long till the ambulance gets here", "can you hear me", "im scared": what someone says
    # while they wait, which is the same in every scene.
    if case == "chest" and _matches(ASPIRIN, line):
        return _name_the_person(pick(ASPIRIN_REPLY, memory), line, memory)
    if case != "self_harm" and _matches(WHEN_HELP_COMES, line):
        return _name_the_person(pick(WHEN_HELP_REPLY, memory), line, memory)
    # A card about a person who hurt you is not a scene with an ambulance on its way: "im scared"
    # after "he hit me last night" got "you're doing the right thing by staying with him ... until
    # the ambulance comes", which tells someone to stay put with the person who hit them.
    if case == "abuse" and _matches(ABUSE_SCARED, line):
        return _name_the_person(pick(ABUSE_SCARED_REPLY, memory), line, memory)
    if case != "self_harm" and _matches(FRIGHTENED, line):
        return _name_the_person(pick(FRIGHTENED_REPLY, memory), line, memory)
    if _matches(CALL_HELP, line):
        return _name_the_person(pick(CALL_HELP_REPLY, memory), line, memory)
    # A correction of who is hurt, while the case is still open: the same card, said again.
    if _matches(CORRECTION_OF_PERSON, line) and case not in ("self_harm",):
        raw = _last_said_as_written(memory)
        if raw and _matches((r"\b999\b", r"\b911\b", r"\bemergency\b"), raw.lower()):
            return _resay(raw, line, memory)
    # A detail added while the case is open ("it started this morning", "he is 62") used to
    # get a shrug - "Noted!" - in the middle of an emergency. It is not a new question and
    # there is nothing to look up: it is one more thing for the 999 handler to hear.
    if _matches(DETAIL_AFTER_ESCALATION, line) and not _matches(ESCALATED_ALREADY, line):
        return _name_the_person(pick(DETAIL_REPLY, memory), line, memory)
    if not _matches(FOLLOW_UP, line):
        return None
    # A follow-up keeps the floor words of the scene it belongs to: "should i open the windows"
    # after a gas reply, "should i grab his collar" after a dog attack. A question about something
    # else entirely still passes to the other modules.
    # Help arriving is good news, but only when the line is the news and not a request on top of
    # it: "the ambulance is on its way" passes, "the ambulance is on its way, what do i do while we
    # wait?" is still about this emergency, and so is "im outside, the fire brigade is coming".
    if _matches(HELP_ARRIVED, line) and not _matches(HELP_ASK_MORE, line):
        return None
    case_words = CASE_WORDS.get(case) or CASE_WORDS["general"]
    if not (_matches(FOLLOW_UP_ANCHOR, line) or _matches((case_words,), line)):
        return None
    safe = _matches(SAFE_NOW, line)
    if isinstance(memory, dict) and memory.get("safety_safe"):
        safe = True
    table = AFTER if safe else WAITING
    if isinstance(memory, dict):
        memory["safety_safe"] = safe
    options = table.get(case)
    if options is None:
        # A small cut or a burn has its own advice, not an emergency follow-up: let it pass.
        return None
    named = memory.get("safety_person") if isinstance(memory, dict) else None
    who = line if _person(line) else (named or _person_before(memory))
    reply = _fit(pick(options if isinstance(options, tuple) else (options,), memory), who, case)
    # The same advice is asked for by the person who is hurt and by someone looking after another
    # person, so the few cases that can speak to the user directly swap the third person for "you".
    if case in FIRST_FIT and not _person(line) and _matches(FIRST_PERSON, line):
        for pattern, replacement in ME:
            reply = re.sub(pattern, replacement, reply, flags=re.I)
    return reply


# --- minor injuries: not an emergency, but still worth a useful answer -----------------------


CASE_ALIAS = {
    "gas_left": "gas", "gas_smell": "gas", "dog_bite": "dog_bite", "dog_attack": "dog_attack",
    "head_injury": "head_injury", "other": "general",
}


def _note(memory, case):
    if isinstance(memory, dict):
        memory["safety_case"] = CASE_ALIAS.get(case, case)
        memory["safety_safe"] = False


# A hypo is checked before the mild guard: "my blood sugar is low" is blood without a wound, so
# the guard that keeps "blood sugar" out of the bleeding reply would pass the emergency itself.
# The sugar that moved in price or in weight is the bag in the cupboard, not the meter: "my sugar
# dropped in price" and "my sugar has gone up 20p a bag" were getting the hypo card, because the
# words that say a reading dropped are the same words that say a price did. A price, a weight or
# a container right after the sugar phrase stands the card down - unless the line also describes
# a person who is unwell, which is the thing this card exists for.
SUGAR_SHOP = (
    r"\b(?:in\s+price|prices?|priced|cost|costs|costing|\d+\s*p\b|pence|quid|"
    r"pounds?|kilos?|bags?|packets?|tins?|grams?|teaspoons?|spoons?)\b",
)
SUGAR_MENTION = re.compile(r"\b(?:blood\s+)?sugar\b|\bglucose\b", re.I)


def _sugar_is_the_shopping(line):
    """True when every sugar named in the line is followed by a price or an amount of it."""
    found = False
    for match in SUGAR_MENTION.finditer(line):
        found = True
        # The end of the clause: "my sugar dropped in price and im shaking" is two things, and
        # only the first of them is the shopping.
        rest = re.split(r"\band\b|\bbut\b|[,.?!;]", line[match.end():match.end() + 60], 1)[0]
        before = re.split(r"\band\b|\bbut\b|[,.?!;]", line[max(0, match.start() - 30):match.start()], 1)[-1]
        # "the price of sugar dropped" puts the shop word in front of the sugar.
        if not _matches(SUGAR_SHOP, rest) and not _matches(SUGAR_SHOP, before):
            return False
    return found


def _hypo_reply(line, memory):
    """The low-blood-sugar reply, or None when the line is a diet question, a story or a name."""
    if not _matches(HYPO, line):
        return None
    # A price is not a reading: "my sugar dropped in price" is the shopping, and the whole card
    # went to a person whose sugar was fine. A person who is also unwell keeps it.
    if _sugar_is_the_shopping(line) and not _matches(HYPO_STRONG, line):
        return None
    # The sugar in a recipe is not the sugar in a person: "the sugar is too low in these biscuits
    # for me" got the low-blood-sugar card. A food word is the tell, and a sign in the same line
    # keeps the card for the person who is shaking while baking it.
    if _matches(SUGAR_IN_A_RECIPE, line) and not _matches(HYPO_STRONG, line):
        return None
    if _matches(HYPO_HOW_KNOW, line) and not _matches(HYPO_STRONG, line):
        return None
    if not _matches(LOW_SUGAR_NOW, line) and (
            _matches(HYPO_QUESTION, line)
            or (_matches(HYPO_PAST, line) and not _matches(HYPO_NOW, line))):
        return None
    # "confused about his tablets" is a question about a dose, not a confused person.
    if _matches(CONFUSED_THING, line) and not _matches(HYPO_STRONG, line):
        return None
    if _matches(HYPO_LIE_IN, line) and not _matches(HYPO_STRONG_OTHER, line):
        return None
    mine = _matches((r"\bi\b", r"\bmy\b"), line) and not _person(line)
    if not mine and _matches(HYPO_NO_MOUTH, line):
        return _fit(pick(REPLIES["hypo_no_mouth"], memory), line, "hypo")
    key = "hypo_self" if mine else "hypo"
    return _fit(pick(REPLIES[key], memory), line, "hypo")


def _words(text):
    """The words of a line, in order, with the punctuation and hyphens left out."""
    return re.findall(r"[a-z]+(?:'[a-z]+)*", text.lower())


def _a_repair_the_reader_made(memory):
    """The words the understanding engine repaired on purpose in this line, lower case.

    `plain` alone cannot say which of its words the reader put right, because a word that is
    already a word is usually left as typed; `fixes` is the record of the repairs it made.
    """
    if not isinstance(memory, dict):
        return frozenset()
    understood = memory.get("understood")
    if not isinstance(understood, dict):
        return frozenset()
    fixes = understood.get("fixes")
    if not isinstance(fixes, dict):
        return frozenset()
    return frozenset(str(word).lower() for word in fixes)


def _repaired(text, memory):
    """The line as typed, with the words the understanding engine repaired put back in place.

    `respell_urgent` only knows the emergency table, so a first-aid case that turns on an
    ordinary word loses its answer when that word is misspelt: "my knee is swallen" was
    "A swollen knee is usually fluid ... have it looked at this week" instead of the ice and
    the check, because only the emergency words were put right. The reading the engine keeps
    in `memory["understood"]["plain"]` repairs every word it is sure of, so this takes a word
    from it - but only that word. Everything else in the line is exactly as the person typed
    it, because a case is matched on the whole line: "my daughter licked the de-icer" keeps its
    hyphen, and the wish in the same line keeps its punctuation.
    """
    typed = respell_urgent(text)
    # A contraction typed with a space where its apostrophe belongs is one word, and the reading
    # in the engine has it as one word: "she s drowsy" is "she's drowsy". Joined here as well,
    # the line lines up with the reading again - and a line that turns on it is read whole, which
    # is what "i can t breathe" needs: main answered it with "I'm listening".
    typed = said_apart(typed)
    typed_text = said_apart(text)
    plain = ""
    if isinstance(memory, dict):
        understood = memory.get("understood")
        if isinstance(understood, dict):
            plain = understood.get("plain") or ""
    if not isinstance(plain, str) or not plain.strip():
        return typed
    mine, read, said = _words(typed_text), _words(typed), _words(plain)
    if len(mine) != len(read) or len(read) != len(said):
        return typed
    pieces, last = [], 0
    for at, found in enumerate(re.finditer(r"[A-Za-z]+(?:'[A-Za-z]+)*", typed)):
        # A word the reader put right, and only one it moved away from what was typed: a word
        # this module already repairs itself is left alone, so no fix here is ever undone. A word
        # that is already a word stays as typed, because the reader's change is then a reading and
        # not a repair - it turns "is it going to die on me lol" into "die on my lol", which is
        # not a sentence anyone wrote.
        # A word in the table of misspellings is not a word that stands on its own: it is a
        # repair the reader has already made, and one a crisis line needs. "hopeless" is a word
        # the wish patterns ring on, and "im hopeles" - one letter short - was answered "It
        # sounds like you're running on empty", because the table entry put the typed word in
        # LEXICON and the guard below then kept the repair to itself. A slip the reader does not
        # know ("im hopless", which happens to be an ending off the word) was handed over, so the
        # word people type most often got the less careful answer. Same line, same card now.
        if (said[at] != read[at] and said[at] != mine[at]
                # A word the reader put right on purpose is a repair even when it is a word of
                # its own: "pan" for "pain" ("i have a pan in my chest") is in the lexicon, so
                # the guard below kept the repair to itself and the chest card never saw it. The
                # reader records those in `fixes`, and a word on that list is the reader saying
                # which word was meant.
                and (mine[at] not in LEXICON or mine[at] in MISSPELLINGS
                     or mine[at].lower() in _a_repair_the_reader_made(memory))):
            pieces.append(typed[last:found.start()])
            pieces.append(said[at])
            last = found.end()
    if not pieces:
        return typed
    pieces.append(typed[last:])
    return "".join(pieces)


# A fit is the one withdrawal sign with a first aid of its own, and that first aid is the answer:
# how to lie the person down, what to move out of the way and when to start timing it.
WITHDRAWAL_FIT_ITS_OWN_ANSWER = (
    r"\b(?:fits?|seizures?|seizure|seized|convuls\w*|fitting)\b",
)


def _withdrawal(line):
    """"mild" or "severe" for a line about stopping the drink, or None.

    Shared by the old-story guard, which would otherwise turn "i quit the drink last week and i
    can't sleep" away as history, and by the reply at the end of respond.
    """
    if _matches(WITHDRAWAL_NOT_ALCOHOL, line) or _matches(WITHDRAWAL_LONG_AGO, line) \
            or _matches(WITHDRAWAL_NOT_NOW, line):
        return None
    if _matches(WITHDRAWAL_WEEKS, line) and _matches(WITHDRAWAL_FINE, line):
        return None
    # A stop the person says is going well is a win, not a come-down, and it does not need a count
    # in the line to say so: "im off the booze for good and i feel amazing" was the card. A sign in
    # the same line still wins - "i stopped drinking and i feel great but i keep shaking".
    if _matches(WITHDRAWAL_FINE, line) and not (
            _matches(WITHDRAWAL_SYMPTOM, line) or _severe(line)
            or _matches(WITHDRAWAL_BARE_BAD, line)):
        return None
    # A sign is what turns a stop into the withdrawal; the state named as detox or withdrawal is the
    # only thing that carries a line on its own.
    sign = _matches(WITHDRAWAL_SYMPTOM, line) or _severe(line) \
        or _matches(WITHDRAWAL_BARE_BAD, line)
    carried = (
        # the stop said plainly, with a sign or with the state named beside it
        (_matches(WITHDRAWAL_STOP + WITHDRAWAL_COLD_TURKEY, line)
         and (sign or _matches(WITHDRAWAL_NAMED, line)))
        # the state named without the drink: "my partner is detoxing at home and shaking"
        or (_matches(WITHDRAWAL_BARE, line) and sign)
        # the count: "im 2 days sober and my heart is racing"
        or (_matches(WITHDRAWAL_SOBER, line) and sign)
        # the routine: the morning shake a drink fixes, the drink taken to stop the shaking
        or _matches(WITHDRAWAL_ROUTINE, line)
        # alone at home, before any sign is said
        or _matches(WITHDRAWAL_ALONE_AT_HOME, line))
    if not carried:
        return None
    if _matches(PREGNANT_LINE, line) and not _matches(WITHDRAWAL_STRONG, line):
        return None
    return "severe" if _severe(line) else "mild"


# The cases the crisis card stands for, so a plan that arrives afterwards is still the same chat.
WISH_FRAMES = ("self_harm", "overdose", "crisis", "despair")

# A fire that nearly started is not a fire, and the rule is the near word rather than the wording:
# every fire word in the line has to sit inside a "nearly/almost/close to" clause for the fire's
# cards to stand down. One fire word outside a clause keeps them, the way round that costs least.
# "i nearly set the kitchen on fire" was the building card, "leave straight away and call 999",
# and "i nearly set my sleeve on fire" was stop, drop and roll with nothing alight, while "i
# nearly set the kitchen on fire and it's still burning" has to stay a fire.
_FIRE_WORD = re.compile(
    r"\b(?:fire|fires|flames?|flaming|alight|ablaze|blazing|burning|burn|burnt|burned|"
    r"catch|caught|catchin(?:g)?|smoke|smoking|smouldering|smoldering|torched?|torching|"
    r"caught\s+light|took\s+light)\b")
# "The curtains almost went up" says a fire in the one way that has no fire word in it, and "went
# up" on its own is also the rent and the price of a pint. So it only counts as a fire word when a
# thing that burns is what went up, and the position that matters is the "went up".
_BURNS_UP = re.compile(
    r"\b(?:curtains?|carpets?|rugs?|sofas?|settee|armchair|chairs?|bed|bedding|mattress|pillow|"
    r"shed|garage|house|flat|kitchen|room|pan|pans|oil|chip\s+pan|grill|oven|hob|toaster|toast|"
    r"towels?|tea\s?towel|dish\s?towel|cloth|sleeve|shirt|coat|dressing\s+gown|dressing\s+robe|"
    r"apron|hair|beard|bins?|wheelie\s+bin|tree|wreath|paper|newspaper|cardboard|wood|logs?|"
    r"firewood|car|van|tent|rubbish|hay|straw|leaves)\b[^.?!]{0,30}?"
    r"\b(went|go|goes|going|gone)\s+up\b")
_NEAR_WORD = re.compile(r"\b(?:nearly|almost|close\s+to|about\s+to)\b")
# Something that is alight right now, in any word for it, for the turn after a near miss: "no it
# didnt catch and now the curtains are alight" says both "didnt catch" and a fire, so it does not
# get the after-a-near-miss answer; "it was just smoke, no flames" says the opposite, so a burning
# word behind no/just/only does not count.
_BURNING_NOW = re.compile(
    r"\b(?:alight|ablaze|on\s+fire|caught\s+fire|flames?|smoking|smoke|smoulders?|burning|"
    r"burnt|smell\s+of\s+burning)\b")
_NEGATED_BEFORE = re.compile(r"\b(?:no|not|just|only|without|none|never)\b[^.]{0,14}$")


def _says_something_is_burning(line):
    """True when a burning word in the line is not one the line is talking down."""
    for match in _BURNING_NOW.finditer(line):
        if not _NEGATED_BEFORE.search(line[max(0, match.start() - 18):match.start()]):
            return True
    return False


# A near word and a fire word have to be in the same clause, or "i nearly died and then the house was
# on fire" reads as a near miss because the two words sit forty characters apart.
_CLAUSE_BREAK = re.compile(
    r"[.?!,;:]|\b(?:and|but|then|so|because|when|while|before|after|until|till|if)\b")


def _fire_words_in(line):
    """Every place in the line that names a fire, including "the curtains went up"."""
    words = list(_FIRE_WORD.finditer(line))
    words += [_Where(m.start(1)) for m in _BURNS_UP.finditer(line)]
    return words


class _Where:
    """A position in the line, so a place and a match can be read the same way."""

    def __init__(self, start):
        self._start = start

    def start(self):
        return self._start


def _a_fire_that_did_not_happen(line):
    """True when the only fire in the line is one the near word says was avoided.

    A near word has to sit in front of every fire word, in the same clause and within forty
    characters: forty covers "set the kitchen on fire" and "so close to the curtains going up",
    and the clause covers "i nearly died and then the house was on fire". A fire word with no near
    word in front of it - the same line going on to say it is still burning, a smoke alarm, a
    second fire - is a fire.
    """
    near = [m.start() for m in _NEAR_WORD.finditer(line)]
    fire_words = _fire_words_in(line)
    if not near or not fire_words:
        return False
    breaks = [m.start() for m in _CLAUSE_BREAK.finditer(line)]

    def close(start, fire_start):
        if not 0 < fire_start - start <= 40:
            return False
        return not any(start < b < fire_start for b in breaks)

    return all(any(close(start, m.start()) for start in near) for m in fire_words)


def respond(text, memory):
    """An emergency reply, a first-aid reply for a small injury, or None to pass."""
    # A character standing in for a letter inside a word is that letter, read before the engine
    # below takes the line apart: `k!ll` arrives as three words, one of which the engine folds to
    # `ok`, so the wish was handed on as "ok!ll" and no pattern could see it.
    text = _leet_made_whole(text) or text
    # The emergency words are the one place a misspelt word costs the person the right answer:
    # "my son swalowed a coin" folded to "Noted: your son swalowed a coin". The understanding
    # engine repairs those words in place, so this reads the line with them put right; every
    # other word, and the punctuation, is exactly what the person typed.
    line = _norm(_repaired(text, memory))
    # A dream is not happening now. "i dreamt my baby stopped breathing" was the infant CPR card,
    # "i dreamt i was being attacked" the assault card, "i dreamt my teeth fell out" the knocked-
    # out-tooth card and "i had a nightmare that i swallowed a bottle of pills" the overdose card -
    # four emergencies nobody in the line is having. The words of a dream are the words of the
    # thing, so the frame is what separates them, and anything that says it is happening now
    # ("still bleeding", "woke up", "right now", "i can smell smoke") keeps its card.
    if _dream is not None and _dream.a_dream_is_not_happening(text):
        return None
    # A face pushed into cake, snow or mud is a mess, not an assault: answer it lightly and let
    # the rest of the bot alone. A blow, a hold or a breath word in the line keeps the card.
    if _matches(SOFT_FACE_PUSH, line) and not _matches(SOFT_FACE_STOP, line):
        _note(memory, "general")
        return pick(PLAY_FACE_REPLIES, memory)
    # Remember who the emergency is about, so the third turn can still say "him".
    if isinstance(memory, dict) and _person(line):
        memory["safety_person"] = _person(line)
    # A parent who says out loud that they might shake the baby is the one line that cannot wait
    # for the next arm: it is read here, before everything, and it is answered with a way out.
    if _matches(SHAKE_CHILD, line) and not _matches(SHAKE_IDIOM, line) \
            and (_matches(SHAKE_CHILD_CONTEXT, line)
                 or (_matches(SHAKE_COPING, line) and not _matches(SHAKE_ADULT, line))):
        _note(memory, "abuse")
        return pick(SHAKE_REPLY if _matches(SHAKE_BABY_WORD, line) else SHAKE_CHILD_REPLY, memory)
    # A long time out cold, or one somebody found them in, before the rows that read "all night"
    # and "until three" as sleep.
    if _matches(OUT_COLD_LONG, line) and not _matches(OUT_COLD_SLEEPY, line) \
            and not _matches(OUT_COLD_LEFT_TO_OTHERS, line) \
            and (_matches(OUT_COLD_FOUND, line) or not _matches(FIRST_PERSON, line)):
        _note(memory, "general")
        return pick(OUT_COLD_NIGHT_REPLY, memory)
    # Things thrown, smashed or punched in the room a person lives in, before the cards that read
    # the same words as a hobby or a clear-out.
    if _matches(ABUSE_OBJECTS, line) and _matches(ABUSE_OBJECTS_PERSON, line) \
            and not _matches(ABUSE_OBJECTS_OFF, line):
        _note(memory, "abuse")
        return pick(REPLIES["abuse"], memory)
    # The plan that arrives a turn later is the same emergency: the crisis card has been given,
    # and "i wrote a note" or "i have the pills" has no wish word of its own to be read. Only
    # inside that frame, and only when the note, the date or the tablets are not an errand.
    if isinstance(memory, dict) and memory.get("safety_case") in WISH_FRAMES \
            and (_matches(CRISIS_PLAN_SAID, line) or _matches(CRISIS_PLAN_CARRY, line)) \
            and not _matches(CRISIS_PLAN_ORDINARY, line):
        _note(memory, "self_harm")
        return pick(CRISIS_PLAN_REPLY, memory)
    minor = _minor(line, memory)
    # ...and the plate with a cut hand beside it is a knife that slipped while somebody was being
    # helped: "my daughter cut herself a slice of cake and cut her finger" was answered, by the card
    # that asks whether she is thinking about suicide, a question nobody in the line is asking
    # (azure-trout, review of #7418). The minor row answers it, and only when the injury is where a
    # knife slips - a hand, a finger, blood - so a cut on an arm or a wrist keeps its card.
    if minor is not None and _a_real_injury_beside_the_plate(line):
        _note(memory, "minor")
        return _fit(pick(minor, memory), line, "minor")
    # A question about cleaning burnt marks off a worktop is a kitchen job, not a person with a burn.
    if _matches(BURNT_MARKS, line) and not _matches(PERSON_WORD, line) \
            and not _matches(BURN_MARK_ON_A_BODY, line):
        return None
    # "i overdosed on cake" is a joke about eating, not a drug: the 999 card is for the drug. A
    # drug word on the same line keeps the card, so "i overdosed on painkillers" is untouched.
    if _matches(OVERDOSE_FOOD, line) and not _matches(OVERDOSE_DRUG, line):
        return None
    # A story about something that happened long ago is not happening now: "i had a bleed when i
    # was pregnant last year" is not this minute, unless the line says when.
    # A fit in childhood is the one old fit that nobody needs to be sent anywhere for: it is
    # already-known history, so it passes rather than raising the GP.
    if _matches(SEIZURE, line) and _matches(CHILDHOOD_FIT, line) and not _matches(
            URGENT_NOW, line) and not _matches(STILL_GOING, line) and not _matches(
            ANIMAL, line) and not _matches(FIT_STILL_RINGS, line):
        return None
    # A fit a day or a week ago is still not a wait, but the ambulance has no job by now either:
    # it is seen today. "just had a fit" is not this - that one is happening now.
    if _matches(SEIZURE, line) and _matches(FIT_THIS_WEEK, line) and (
            _matches(FIT_ALL_BETTER, line) or not _matches(URGENT_NOW, line)) and not _matches(
            STILL_GOING, line) and not _matches(FIT_STILL_RINGS, line) and not _matches(
            ANIMAL, line) and not _matches(CHILDHOOD_FIT, line) and not _matches(
            SEIZURE_STORY_GUARD, line):
        _note(memory, "general")
        return PAST_FIT_WEEK_REPLY
    # "i cut myself off from my friends last year" is the phrasal verb, not a cut: the people are
    # what the speaker was cut off from, and there is no wound, no blood and no tool in the line.
    # A wish, a reason or an emergency anywhere in it keeps the card, so "i cut myself off from
    # everyone and i want to die" is still the crisis reply - this only covers being alone.
    if (_matches(CUT_MYSELF_OFF, line) and not _matches(
            DESPAIR + WISH_INTENT + SELF_HARM_INTENT + SELF_HARM_REASON + URGENT_NOW
            + OWN_WISH_WORDS + CRISIS_PLAN_SAID, line)
            and not CRISIS_WORD.search(line)):
        # A hit with the withdrawal is not a loneliness line and not a wish either: "i cut myself off
        # from my mum because she hit me" was getting the friendship tip, and the abuse reply is the
        # one for it (zippy-kangaroo, #4643).
        if _matches(ABUSE, line) or _matches(ABUSE_HIT_ME, line):
            _note(memory, "abuse")
            return _fit(pick(REPLIES["abuse"], memory), line, "abuse")
        return None
    # A near thing on a bike outranks the arm the same line wants, unless somebody is hurt now.
    if _an_accident_near_thing(line) and not _matches(
            FALL_RED + STILL_GOING + DESPAIR + WISH_INTENT + SELF_HARM_INTENT
            + CRISIS_PLAN_SAID, line) and not _matches(COUNTERFACTUAL_WISH, line):
        _note(memory, "near_thing")
        return _fit(pick(REPLIES[_near_thing_key(line)], memory), line, "near_thing")
    # A near thing with a heavy object, and a joke about laughing, are the two ways "killed
    # myself" is ordinary. Neither is a crisis and neither deserves a shrug, so they get their own
    # line here - above the old-story return, which was eating "i was killing myself laughing
    # yesterday" - and only when no other case on the line wants it: a chest that hurts after the
    # sofa is still the chest's answer, and a line that names a death is somebody else's turn.
    # "i killed myself laughing at the funeral" was getting "Ha, good. Killed yourself laughing,
    # not the other thing" over an open grave, and "carrying the coffin at my dad's funeral" the
    # lifting advice; the loss module answers both.
    if not _matches(DEATH_IN_THE_LINE, line) \
            and not any(_matches(patterns, line) for name, patterns, _ in CASES
                        if name != "self_harm"):
        if _the_effort_frame(line):
            _note(memory, "near_thing")
            return _fit(pick(REPLIES[_near_thing_key(line)], memory), line, "near_thing")
        if _the_laugh(line):
            _note(memory, "laughing_kill")
            return _fit(pick(REPLIES["laughing_kill"], memory), line, "laughing_kill")
    # An attempt that already happened is still the attempt: the week on the line is about what to
    # do now, not about whether it is worth talking about. Somebody else's attempt is their crisis,
    # and the reply for them is how to help.
    # "End it with" something that is not a means is a break-up or a cancellation, not the attempt.
    _end_it_is_something_else = _matches(END_IT_WITH_A_THING, line) \
        and not _matches(END_IT_MEANS, line)
    _said_an_attempt = _matches(PAST_ATTEMPT, line) \
        and not _end_it_is_something_else and (
            _matches(PAST_ATTEMPT_STRONG, line) or not _matches(PAST_ATTEMPT_NOT, line))
    _said_a_past_wish = _matches(PAST_WISH, line) and not _matches(PAST_WISH_NOT, line)
    if not _said_a_past_wish and _matches(PAST_NEAR_ACT, line) \
            and not _matches(PAST_WISH_NOT, line) and not _matches(PAST_ATTEMPT_NOT, line):
        _said_a_past_wish = True
    # The plainest way of saying it carries no date at all: "i tried to end it", "i have tried to
    # end it" are the attempt, and waiting for a "last week" before answering is how the person who
    # says it shortest gets a shrug. The date changes the reply, not whether there is one.
    _mine_and_undated = _matches(FIRST_PERSON, line) \
        and _matches(SPOKEN_ATTEMPT_UNDATED, line) \
        and not _end_it_is_something_else
    # Scars say nothing about when, and somebody asking about their daughter's arms has no date
    # either, so this one shape carries its own gate.
    _scars_seen = _matches(SELF_HARM_SCARS, line) \
        and not _matches(SELF_HARM_SCARS_NOT, line)
    # A wish said as a thing that nearly happened carries no date and needs none.
    if _matches(COUNTERFACTUAL_WISH, line) and not _matches(ANIMAL, line) \
            and not _matches(PAST_WISH_NOT, line) \
            and not _matches(COUNTERFACTUAL_IDIOM, line):
        _note(memory, "self_harm")
        return _fit(pick(REPLIES["self_harm"], memory), line, "self_harm")
    if (_said_an_attempt or _said_a_past_wish or _scars_seen) and (
            _matches(OLD_TIME, line) or _matches(RECENT_TIME, line) or _mine_and_undated
            or _scars_seen or _matches(TEEN_AGE, line)) \
            and (not _matches(URGENT_NOW, line) or _said_an_attempt) \
            and not _matches(ANIMAL, line) \
            and not _idiom(line) \
            and not _matches(CUT_MYSELF_OFF, line) \
            and not (_matches(PAST_DEATH, line)
                     and not _matches(SELF_DEAD_FEELING, line)) \
            and not (not _matches(FIRST_PERSON, line) and _matches(LONG_AGO, line)
                     and not _matches(FIRST_PERSON_WISH, line)):
        _note(memory, "self_harm")
        # Somebody else's attempt is their crisis, and the reply for them is how to help.
        if not _matches(FIRST_PERSON, line) and _matches(THIRD_PERSON_ACTOR, line) \
                and not _matches(FIRST_PERSON_WISH, line) \
                and not _matches(LONG_AGO, line):
            return pick(REPLIES["self_harm_other"], memory)
        return _fit(pick(REPLIES["self_harm"], memory), line, "self_harm")
    # A blow the speaker says they gave, or a childhood they are telling you about, is not one of
    # the cases below and it is not the old-story guard either: every case here is written for the
    # person it was done to, and "when i was a kid" is the guard's own time words. The wish wins a
    # tie, because "i hit my wife and i want to die" is the crisis first.
    # ...and the remorse after it is not the crisis. "i hit my wife once and i hate myself" got
    # the soft empathy line, and somebody who has just said they hit their wife needs what to do
    # tonight, not "what would make today a bit easier". The stand-down is as narrow as the shape:
    # it needs an act, a word that is only remorse about it, and no word that can only be about
    # dying - so "i hit my wife and i want to die", "...and i feel like a burden" and "...and i
    # keep thinking about ending it" all keep the crisis card.
    _remorse_after_hit = (_matches(I_HIT_SOMEONE, line)
                          and _matches(REMORSE_FOR_THE_ACT, line)
                          and not CRISIS_WORD.search(line)
                          and not _matches(WISH_OWN_BARE, line)
                          and not _self_harm_intent(line))
    # The dying words win a tie in every shape, not only the two pattern sets: "i hit my wife and i
    # feel like a burden" is the crisis first, and its own word for it is enough to say so.
    _crisis_first = (_self_harm_intent(line) or _own_wish(line) or _matches(DESPAIR, line)
                     or bool(CRISIS_WORD.search(line)))
    if not (_crisis_first and not _remorse_after_hit):
        if _matches(I_HIT_SOMEONE, line) and not _matches(I_DID_NOT_HIT, line) \
                and not _matches(HIT_THING_NOT_PERSON, _norm(text)):
            _note(memory, "abuse")
            return _fit(pick(REPLIES["abuse_own"], memory), line, "abuse_own")
        if (_matches(HIT_AS_A_CHILD, line) and not _matches(CHILD_HIT_NOW, line)
                and not _matches(GAME_NOT_A_BLOW, line)):
            _note(memory, "abuse")
            return _fit(pick(REPLIES["abuse_past"], memory), line, "abuse_past")
    # A hanging that already happened is a death, not a rescue: "my grandad hung himself" got
    # "Get them down and start CPR" for a man who died years ago, and "my dad hanged himself last
    # year" fell through to a shrug. The scene - "i found my dad hanging", "he is hanging now" -
    # still keeps the card, and so does the reader asking for help with it.
    if (_matches(HANGED_DONE, line)
            and (_matches(DEATH_SAID, line) or _matches(ELDER_KIN, line)
                 or _matches(HANGED_LONG_AGO, line)
                 or (_matches(SCHOOL_PLACE, line) and not _matches(YOUNG_KIN, line))
                 or _matches(OLD_TIME, line) or _matches(RECENT_TIME, line))
            and not _matches(URGENT_NOW, line)
            and not _matches(OWN_WISH, line)
            and not _matches((r"\bfound\b", r"\bis\s+hanging\b", r"\bstill\b", r"\bnow\b",
                              r"\bhelp\b"), line)):
        _note(memory, "loss")
        return _fit(pick(REPLIES["death_already"], memory), line, "loss")
    # "out cold" is a faint in the words people use, and it used to be read as a knock-out: the
    # line got the head-injury card about "confusion, drowsiness or sickness after a bang on the
    # head" when no bang was ever said, and once that was fixed the words "at school" were enough
    # for the cold-and-school answer. A faint that has already happened keeps the faint advice.
    if (_matches(FAINT_STORY, line) and _matches((r"\bout\s+cold\b",), line)
            and not _matches(OUT_COLD_NOW, line)
            and not _matches(OUT_COLD_WONT_WAKE, line)
            and not _matches(OUT_COLD_ASLEEP, line)
            and not _out_cold_knockout(line)
            and not _matches(ANIMAL, line)
            and not _matches(URGENT_NOW, line)
            and not _matches(OLD_TIME, line)):
        _note(memory, "general")
        return _fit(OUT_COLD_REPLY, line, "general")
    if _matches(OLD_TIME, line) and not _matches(URGENT_NOW, line) and not _matches(
            STILL_GOING, line) and not _hopeless(line) and not _matches(
            OWN_WISH, line) and not _withdrawal(line):
        # A fit is the one old story that still needs someone: a first one is looked into even
        # years later, so it is the GP's rather than nobody's. The family's known epilepsy, a fit
        # of coughing and a laptop that had a fit are not that story, and a pet's fit is the vet's.
        if _matches(SEIZURE, line) and not _matches(FIT_ROUTINE, line) and not _matches(
                SEIZURE_STORY_GUARD, line) and not _matches(ANIMAL, line):
            _note(memory, "general")
            return PAST_FIT_REPLY
        if _matches(FAINT_STORY, line) and not _matches(ANIMAL, line):
            _note(memory, "general")
            return PAST_BLACKOUT_REPLY
        # A disclosure of something done to the speaker is not the old story this guard turns
        # away. "i was abused when i was little", "i was raped years ago", "i was assaulted last
        # year" all stopped here and came back a shrug: the time words are the reason the guard is
        # here at all, and they are also how an old disclosure is said. The ambulance has no job
        # years later, so it is the abuse arm's own reply rather than the card - and a line that
        # says it is still going on never reaches this block.
        if _matches(ABUSE_DISCLOSURE, line) and not _matches(ABUSE_NOW, line) \
                and not _matches(ABUSE_DISCLOSURE_FINE, line) \
                and not _matches(ABUSE_FINE, line):
            _note(memory, "abuse")
            return _fit(pick(REPLIES["abuse_past"], memory), line, "abuse")
        # ...and the reverse: a disclosure that goes on to say it is still happening is not an old
        # story at all, so it must not be turned away here - it is the abuse arm's card.
        if not (_matches(ABUSE_DISCLOSURE, line) and _matches(ABUSE_NOW, line)):
            return None
    # How to do CPR, asked by somebody who is learning rather than somebody in the room with a
    # person who has stopped breathing. The numbers are two sentences and nobody should have to go
    # and search for them; the scene itself is untouched because the room has to be empty.
    if _matches(CPR_HOWTO, line) and _last_case(memory) not in CPR_SCENE_CASES and (
            not _matches(CPR_ROOM_EMPTY, line)
            or _matches(CPR_NO_PULSE, line)) and not _matches(CPR_NOT_EFFORT, line) and not _matches(
            CPR_NOT_A_BODY, line) and not _matches(CHEST, line) and not _matches(ANIMAL, line):
        _note(memory, "general")
        if _matches((r"\blearn|learning|course\b|class\b|training|qualification|certificate",
                     r"\bwhere\s+can\s+i\s+(?:do|take)\b"), line):
            # "is cpr hard to learn" is a question about a course, not a person on a floor.
            _note(memory, "general")
            return None
        start = _matches((r"\bshould\s+i\s+(?:start|do|begin)\b", r"\bshall\s+i\s+start\b",
                          r"\bam\s+i\s+supposed\s+to\s+start\b"), line)
        # A pulse or a breath in the question changes what to do, so it is answered before the
        # numbers are handed over.
        if _matches(CPR_STILL_ALIVE, line) and not _matches(CPR_NOT_ALIVE, line):
            return pick(CPR_WHEN_ALIVE, memory)
        if _matches(CPR_NO_PULSE, line):
            return pick(CPR_NO_PULSE_NOW, memory)
        if _matches(CPR_BABY, line):
            return pick(CPR_BABY_SCENE if start else CPR_HOW_BABY, memory)
        if _matches(CPR_CHILD, line):
            return pick(CPR_CHILD_SCENE if start else CPR_HOW_CHILD, memory)
        if start:
            return pick(CPR_START, memory)
        return pick(CPR_HOW, memory)
    # Someone shut in a room with the pills or a blade and not answering: the door is what costs
    # the time, so this comes before the "did they say why" gate.
    if _matches(LOCKED_IN_RISK, line):
        # The user shut in with the pills needs the crisis line for themselves, not the 999 call.
        if re.search(r"\bm[y\s]*self\b", line):
            _note(memory, "self_harm")
            return pick(REPLIES["self_harm"], memory)
        _note(memory, "general")
        return pick(REPLIES["locked_in"], memory)
    # Someone else hurting their own body is their crisis, not a cut to dress: answer how to help
    # them. It runs before the cut and burn first aid, which "my son is cutting himself" was
    # otherwise getting, with a clean cloth and a plaster.
    # A cut that is bleeding heavily is first aid before anything else: "my brother cut himself
    # and there is blood everywhere" needs the ten minutes of pressure, not the crisis line.
    if (_matches(OTHER_SELF_HARM, line) and not _matches(BLEEDING, line)
            and not _a_pet_hurting_itself(line)
            # A cause on the line is an accident in the third person: "my son cut himself
            # badly on glass" is a boy and a pane, not a boy who means it.
            and not _a_reason_it_was_not_meant(line)
            # The speaker's own wish in the same line is the crisis that matters: "i want to die
            # and my son cuts himself" is one person saying two things about themselves.
            and not _matches(FIRST_PERSON_WISH, line)):
        # An overdose is the ambulance whoever took it, and the amount is what decides it: the
        # crisis line is for afterwards. `my friend overdosed` was getting only the crisis card.
        if _matches(PILLS_OVERDOSE, line):
            _note(memory, "poison")
            return _fit(pick(REPLIES["poison_other"], memory), line, "poison")
        _note(memory, "self_harm")
        return _fit(pick(REPLIES["someone_else"], memory), line, "someone_else")
    # ...unless the suicide is the subject of a lesson, a film or the news, or the thing that is
    # suicide is a job, a drive or a fixture, rather than the person's own plan. The user's own
    # wish in the same line still wins.
    # ...and a subject stays a subject only while the speaker is outside it: a lesson that they
    # keep turning over, or a wish they name in the same breath, is the person themselves.
    self_in_it = _matches(SELF_RUMINATION, line) and _matches(DEATH_WORDS, line)
    if ((_matches(SUICIDE_MENTION_CONTEXT, line) or _matches(SUICIDE_ABOUT_A_THING, line)
         or _matches(SUICIDE_LESSON, line))
            and not _matches(IDIOM, line)
            and not self_in_it
            and not _matches(FIRST_PERSON_WISH, line) and not _own_wish(line)):
        # A lesson gets an answer of its own rather than falling through to whatever the line
        # happens to look like next (a teacher, a film, a homework question): the subject is heavy
        # and the reply should be about it, without the crisis card for somebody who is fine. A
        # place of learning is enough, because the setting is what makes it a lesson: "the tutor
        # covered self harm in the seminar", "suicide came up at assembly", "we watched a film
        # about suicide in pshe" were falling through to "Got it. Is there anything you'd like a
        # hand with?".
        if (_matches(SUICIDE_LESSON, line) or (
                _matches(SUICIDE_MENTION_CONTEXT, line) and _matches((_LEARN_PLACE,), line))) \
                and not _matches(LOSS_SAID, line):
            _note(memory, "suicide_lesson")
            return _fit(pick(REPLIES["suicide_lesson"], memory), line, "suicide_lesson")
        return None
    if self_in_it:
        _note(memory, "self_harm")
        return _fit(pick(REPLIES["self_harm"], memory), line, "self_harm")
    # "suicide" said as a topic, or with somebody else as its subject, is not the reader's own
    # state: the article they read, their father's angry talk and a question about helping a
    # friend have their own answers, and the crisis card asked the wrong person to ring a
    # helpline. Where the line names somebody else at risk, SOMEONE_ELSE_RISK above answers it.
    # Hopelessness is the speaker's own too: "my dad died last year and nothing ever gets better"
    # is a bereavement and a life that has stopped, and the grief in the first half must not stand
    # the card down for the second. Without HOPELESS here the loss answered for both halves.
    # ...and a hopeless phrase that is somebody else's is their crisis, not the speaker's, so it
    # does not count as the speaker's own distress here.
    own_distress = (_matches(OWN_WISH, line)
                    or (_hopeless(line) and not _someone_elses_despair(line))
                    # The wish said as a shrug is the speaker's own, and the bare "dead" arm of
                    # DEATH_REPORT would otherwise read "i should be dead" as somebody else's
                    # death already happened and hand it the bereavement answer.
                    or _matches(WISH_BY_MODAL, line)
                    or (_matches(OWN_DISTRESS, line) and not _matches(SUICIDE_TOPIC, line)))
    # A death already happened: "my dad died by suicide" is a bereavement, and the loss answer is
    # the one for it. Main rang the reader's own crisis line, which told them to ring a helpline
    # about their father's death.
    other_death = _matches(DEATH_REPORT, line) and not own_distress
    # Somebody else keeps bringing it up is not a topic for the reader to chew over and not the
    # reader's own state either: the reply for it is how to help that person, which is the same
    # answer the person-at-risk arms give. Without this, "my neighbour keeps mentioning suicide
    # rates" fell to a shrug once the topic stand-down read the word as a subject.
    # "my neighbour keeps mentioning suicide rates" is the rate and not a neighbour to ask straight
    # out, so the word as a subject stays a topic here; the replies for a person who keeps saying
    # it are the talking-about-it arms above, and the topic stand-downs must not swallow them:
    # "my daughter is doing a talk on self harm" is still those lessons, not a shrug.
    suicide_elsewhere = not own_distress and (
        other_death or _matches(SUICIDE_TOPIC, line) or _matches(SUICIDE_OTHER, line))
    # ...and a wish the person has just said they do not have is not a wish either.
    denied_wish = (_denied_wish(line) or _matches(WISH_DEAD_OFF, line)
                   or _cut_off_idiom(line))
    # A talk, a course, a documentary or a self-harm worker is the subject of the line: somebody is
    # talking about the thing, not doing it, and the reader is not in crisis either.
    topic_talk = (not _matches(OWN_WISH, line)
                  and _matches(SELF_HARM_TOPIC_OFF, line))
    # The figure of speech stands this down, but only when the rest of the sentence is not a wish:
    # "i was killing myself laughing and now i feel empty" counts as intent, and "i feel like dying
    # laughing" stays the joke it is.
    intent = (_self_harm_intent(line)
              and not (_idiom(line) and not _rest_of_it_rings(line))
              and not suicide_elsewhere
              and not denied_wish
              and not topic_talk
              and not _matches(TALKS_ABOUT_IT + HELP_SOMEONE, line)
              and not _avoided(line, SELF_HARM_INTENT + SELF_HARM + SELF_HARM_DESERVE))
    # A relative dying is grief said in advance, not the speaker's own wish to die: the loss answer
    # is the one for it, so the crisis reply stands down unless the speaker says it about themselves.
    # The speaker's own wish in the same line wins over the relative's, which is what OWN_WISH is
    # for: "my nan is going to die and i keep thinking about ending it" is two things, and the
    # crisis is the half that matters. Without that clause the stand-down swallowed the wish too,
    # and the person got the grief answer.
    if (intent and _matches(DYING_OTHER, line) and not _matches(SELF_OWN_DYING, line)
            and not _own_wish(line)):
        intent = False
    # A chest closed by a room you cannot leave is answered rather than dropped: the advice is to
    # get out and slow the breath, with the 999 card kept for when that does not work. Anything
    # else on the line that is a real red flag (chest pain, a crush, smoke) still wins below.
    if FIGURATIVE_BREATH.search(line) and not intent:
        if BREATH_SETTLED.search(line):
            return None
        if not (_matches(CHEST, line) or _matches(BREATH_RED, line)
                or _matches(FIRE, line) or _matches(GAS_SMELL, line)
                or BREATH_ROOM_RED.search(line)):
            return _fit(pick(REPLIES["breath_panic"], memory), line, "panic")
    intent = (_self_harm_intent(line) and not _idiom(line)
              and not _matches(END_IT_ALL_JOKE, line)
              # the same ownership stand-downs as above: a topic, a relative's talk or a death
              # already happened is not this reader's crisis whichever assignment ran last
              and not suicide_elsewhere
              and not denied_wish
              and not topic_talk
              and not _matches(TALKS_ABOUT_IT + HELP_SOMEONE, line)
              and not _matches(WISH_BY_MODAL_OFF, line))
    # A third person's plan with a means in it keeps the card that names them, whether or not the
    # speaker's own wish fires: "my dad is going to end it with pills" is his plan, and main
    # answered the speaker as if it were theirs. The speaker's own stated wish still wins.
    # ...and a wish said with *any* way of doing it is that person's plan, not only one of the
    # words END_MEANS knows: "my mum wants to end it with her own hands", "my friend wants to end it
    # with her insulin", "my mum wants to end it with her medication" were all read as a breakup,
    # because what follows "with" is not a person. A person after "with" is a breakup again, unless
    # the line says the speaker cannot stop them: "my dad wants to end it with him and i cant stop
    # him". The lookalike guard does not stand this down: "my dad wants to end it with a knife" is
    # a plan, even though a knife is also in the kitchen.
    means_other = (_matches(END_MEANS_OTHER, line)
                   and (_matches(END_MEANS, line)
                        or _ends_it_with_a_method(line)
                        or _matches(END_HELPLESS, line))
                   and not _matches(FIRST_PERSON_WISH, line))
    accident = (_matches(ACCIDENT, line) and not intent
                and not _matches(SELF_HARM_REASON, line)
                # The chore named in the line is what "again" belongs to: "i cut myself again
                # shaving" is a second clumsy shave, not a habit with a blade.
                and (not _matches(SELF_HARM_AGAIN, line) or _matches(CHORE_CAUSE, line)))
    # A stated wish to be hurt or dead is the support reply, whatever the line also mentions.
    if intent:
        # A third person's plan with a means in it is their plan, and it keeps the card that names
        # them on every arm below: the lookalike guard would read "my dad wants to end it with a
        # knife" as a knife in a kitchen, and the person list below has already stood the carer
        # card down for any "end it with".
        if means_other:
            _note(memory, "self_harm")
            return pick(REPLIES["self_harm_other"], memory)
        # ...but a habit that a sport, a sleep or a thing explains is an accident said often:
        # "he hurts himself every time he plays rugby" and "she scratches herself in her sleep"
        # are a boy on a pitch and a girl with dry skin, not the act. It goes before every other
        # arm of this branch, or "my son cut himself on glass" is still answered as a crisis.
        if (_matches(SELF_HARM_BY_OTHER, line) and _a_reason_it_was_not_meant(line)
                and not _matches(FIRST_PERSON_WISH, line)
                # "self harming" said straight out is not a knock at netball: "my son is self
                # harming at school" is the worry, not a boy at sport.
                and not re.search(r"\bself[-\s]?harm", line)):
            return None
        # `my friend overdosed on purpose` is not the user's own crisis: somebody else did it, so
        # the ambulance comes first and the crisis line comes after.
        if (not _matches(FIRST_PERSON, line) and _matches(THIRD_PERSON_ACTOR, line)
                and _matches(PILLS_OVERDOSE, line)):
            _note(memory, "poison")
            return _fit(pick(REPLIES["poison_other"], memory), line, "poison")
        # the user is safe and someone with them is at risk, so speak to the helper.
        # A figure of speech about someone else is the figure of speech: "my mum wants to die of
        # embarrassment" and "my son wants to die of boredom" are not a person to be watched over
        # tonight. The same for ending a relationship rather than a life: "he wants to end it with
        # his girlfriend" is not the sentence this card is for.
        if ((_matches(OTHER_RISK, line) or _matches(SELF_HARM_BY_OTHER, line))
                and not _matches(FIRST_PERSON, line)
                and not _matches(IDIOM, line)
                # A talk, a course or a counsellor is the subject of the line, not a person at risk.
                and not _matches(SELF_HARM_TOPIC_OFF, line)
                and not re.search(r"\bend(?:ing)?\s+it" + END_IT_WITH, line)):
            # `my friend overdosed on purpose` is still an overdose first: the pills are the
            # emergency, and the help for the person with them comes after.
            if _matches(PILLS_OVERDOSE, line):
                _note(memory, "poison")
                return _fit(pick(REPLIES["poison_other"], memory), line, "poison")
            _note(memory, "self_harm")
            return pick(REPLIES["self_harm_other"], memory)
        # A cut of your own that is still bleeding wants the cloth first: "i cut myself and the
        # blood wont stop" was answered with the crisis line alone on main - no pressure on the
        # wound, no 999 - which is the wrong way round when the bleeding is what hurts them in the
        # next ten minutes. The crisis line is still in this reply, because a cut like this is
        # often self-inflicted, and the bare "i cut myself" keeps the support reply it has.
        if _matches(SELF_CUT, line) and (_matches(BLEEDING, line)
                                         or _matches(CUT_NOT_STOPPING, line)):
            _note(memory, "bleeding")
            return _fit(pick(REPLIES["self_cut_bleeding"], memory), line, "bleeding")
        # Hopelessness somebody else has is answered with how to help them, by the same arms that
        # already do it for their plan or their cutting: "my sister said she cant go on" was the
        # speaker's own crisis card, which told them to ring a helpline about themselves.
        if _someone_elses_despair(line):
            _note(memory, "self_harm")
            return pick(REPLIES["self_harm_other"], memory)
        _note(memory, "self_harm")
        return _fit(pick(REPLIES["self_harm"], memory), line, "self_harm")
    # A third person is the one cutting, burning or scratching himself. It goes before the mild
    # guard, or "my son is cutting himself" is a cut to wash, and before the world-question guard,
    # because a parent asking what to do about it still needs the help for the child.
    # "my son hurt himself" with nothing else in the line is asked, not answered: the bare verb is
    # an accident as often as it is self-harm, and the crisis card answers only one of those.
    if (_matches(HURT_HIMSELF_BARE, line) and not _matches(HURT_HIMSELF_MEANT, line)
            and not _matches(BLEEDING, line) and not _a_reason_it_was_not_meant(line)
            and not _matches(FIRST_PERSON_WISH, line)
            and not re.search(r"\bm[y\s]*self\b", line)):
        _note(memory, "general")
        return pick(REPLIES["hurt_himself_asked"], memory)
    if means_other:
        _note(memory, "self_harm")
        return pick(REPLIES["self_harm_other"], memory)
    if (_matches(SELF_HARM_BY_OTHER, line) and not re.search(r"\bm[y\s]*self\b", line)
            # The word as a subject is not somebody at risk: `my neighbour keeps mentioning
            # suicide rates` is a chat about the news, not a neighbour to ask straight out.
            and not _matches(SUICIDE_TOPIC, line)
            # A talk, a course or a counsellor is the subject, not a person at risk.
            and not _matches(SELF_HARM_TOPIC_OFF, line)
            # Blood everywhere is a wound to press on first: the crisis answer follows the cut.
            and not _matches(BLEEDING, line)
            and not _matches(FIRST_PERSON_WISH, line)
            and not _a_reason_it_was_not_meant(line)
            and not _matches(SELF_REASSURED, line) and not _matches(NOT_NOW, line)
            and not re.search(r"\bend(?:ing)?\s+it" + END_IT_WITH, line)):
        _note(memory, "self_harm")
        return pick(REPLIES["self_harm_other"], memory)
    # A hypo is asked before the mild guard does its work: "my blood sugar is low" is blood
    # without a wound, so the guard that keeps "blood sugar" out of the bleeding reply would pass
    # the emergency itself.
    reply = _hypo_reply(line, memory)
    if reply:
        return reply
    # A pet that is out of puff is the vet's question, not the person's. "my dog gets breathless on
    # the stairs" was getting the human GP card about having a chest listened to, which is the bot
    # answering as if the dog were the user. A red flag or a pet in real trouble keeps its own
    # card, and so does a line with a person's own breathlessness in it.
    if _matches(PET_BREATH, line) and not _matches(HUMAN_TOO, line) \
            and not _matches(PET_EFFORT, line) \
            and _matches(BREATH_AT_REST + PET_CANT_SETTLE + PET_BREATH_NOW, line) \
            and not _matches(PET_CRISIS, line):
        return _fit(pick(REPLIES["pet_emergency"], memory), line, "pet_emergency")
    if _matches(PET_BREATH, line) and not _matches(HUMAN_TOO, line) \
            and not _matches(BREATH_RED + BREATH_AT_REST + PET_CRISIS + PET_EFFORT
                             + PET_CANT_SETTLE + (r"\bgums?\b",), line):
        _note(memory, "pet_breath_mild")
        return _fit(pick(REPLIES["pet_breath_mild"], memory), line, "pet_breath_mild")
    # ...but the same small effort with sweat, clamminess or a faint feeling is not the GP's
    # question, it is today's: that cluster is how a heart short of blood announces itself, and the
    # everyday answers were reassuring those lines with "usually just fitness".
    if (_matches(BREATH_SHORT + EFFORT_RECOVERY, line) and _matches(EXERTION_SMALL, line)
            and _matches(EFFORT_HEART_CLUSTER + EFFORT_SICK_PAIR + EFFORT_TRAVEL_PAIN, line)
            and not _matches(BREATH_RED, line) and not _matches(BREATH_AT_REST, line)
            and not _matches(CHEST, line) and not _matches(PAST_HARM, line)
            and not _matches(NOT_A_BREATHER + PET_WORDS, line)
            and not _matches(EFFORT_TOO_LONG, line)
            and not _matches(EFFORT_PATTERN, line) and not _matches(EFFORT_BENIGN, line)
            and not intent):
        # A parent describing a child, or a person describing their mum, is not the patient: the
        # card for a heart attack is the wrong card for "my son gets out of breath on the stairs
        # and feels dizzy", and the GP visit is the right one.
        if _matches(EFFORT_SOMEONE_ELSE, line):
            return _fit(pick(REPLIES["breath_exertion"], memory), line)
        # A dizzy spell on getting up is a blood-pressure drop, not a heart.
        if _matches(EFFORT_POSTURAL, line) and not _matches(EFFORT_TRAVEL_PAIN, line):
            return _fit(pick(REPLIES["breath_exertion"], memory), line)
        return _fit(pick(REPLIES["breath_effort_heart"], memory), line, "breath_effort_heart")
    # "Feel sick" on its own is not the heart's cluster, but it is not the fitness answer either: a
    # person who is breathless and sick on the stairs is a GP visit even when the sick is morning
    # sickness or a bug.
    if (_matches(BREATH_SHORT + EFFORT_RECOVERY, line) and _matches(EXERTION_SMALL, line)
            and _matches(EFFORT_SICK, line)
            and not _matches(BREATH_RED, line) and not _matches(BREATH_AT_REST, line)
            and not _matches(CHEST, line) and not _matches(PAST_HARM, line)
            and not _matches(NOT_A_BREATHER + PET_WORDS, line)
            and not _matches(EFFORT_BENIGN, line) and not _matches(EFFORT_PATTERN, line) \
            and not intent):
        return _fit(pick(REPLIES["breath_exertion"], memory), line)
    # Months of the same thing on the same stairs is not a body pushed today, it is a body that has
    # changed, and the everyday answer ("being puffed after stairs is usually just fitness") is the
    # wrong reassurance for it. The faint side of the cluster does not overrule this: a person who is
    # dizzy on the stairs every time needs the GP either way.
    if (_matches(BREATH_SHORT + EFFORT_RECOVERY, line) and _matches(EXERTION_SMALL, line)
            and _matches(EFFORT_PATTERN, line)
            and not _matches(BREATH_AT_REST, line) and not _matches(CHEST, line)
            and not _matches(PAST_HARM, line) and not intent):
        return _fit(pick(REPLIES["breath_exertion"], memory), line)
    # Out of puff on the stairs or a hill, said plainly, is a GP question: it is new breathlessness
    # and nobody has looked at it. Everything that makes it urgent still rings below and above.
    # A sweat on the stairs stands the fitness answer down but not the doctor: every hot stairwell
    # produces one, and "i get sweaty and out of breath climbing the stairs at the office" is a
    # person asking whether something has changed. So only the heart's side of the red flags keeps
    # the GP out of this one, and a pattern of months is what the GP is for.
    #
    # EFFORT_BENIGN is not consulted here. It is what keeps the ambulance away from a hot day or a
    # cold, and that is the cluster rule's business; the GP arm is the floor under it. Standing it
    # down as well took the doctor away from a pregnant person breathless on the stairs and from
    # anyone with a stinking cold, because the settling answer ("that is what hard effort does")
    # answers a question they did not ask. Seven ordinary lines went from the GP to that.
    if _matches(BREATH_SHORT + EFFORT_RECOVERY, line) and _matches(EXERTION_SMALL, line) and             not _matches(BREATH_RED + EFFORT_RED_HEART, line) and not _matches(
            BREATH_AT_REST, line) and not _matches(
            CHEST, line) and not _matches(PAST_HARM, line) and not intent:
        return _fit(pick(REPLIES["breath_exertion"], memory), line)
    # The same reading for a meal: new breathlessness at the table is the GP's, unless something
    # on the red-flag list says otherwise.
    if _matches(BREATH_SHORT, line) and _matches(MEAL_BREATH, line) and not _matches(
            BREATH_RED, line) and not _matches(BREATH_AT_REST, line) and not _matches(
            CHEST, line) and not _matches(PAST_HARM, line) and not intent:
        return _fit(pick(REPLIES["breath_meal"], memory), line)
    # A choke that is over is the cough that clears itself, but only while the airway is working:
    # "i choked on my coffee and i cant breathe" was getting the sip of water, so the red flags
    # take the line back to the breathing case.
    # A shaken baby is an injury that may not show for hours, so it is checked the same day.
    if _matches(SHAKEN, line) and not _matches(SHAKEN_FINE, line):
        _note(memory, "shaken")
        return pick(SHAKEN_REPLY, memory)
    # A choke on a word is a stutter, so it gets the ordinary reply rather than advice for a
    # blocked airway - unless one of the red signs is in the line too. It is checked before the
    # mild-choke answer because "i nearly choked on my words" carries "nearly choked".
    if _matches(CHOKE_WORDS, line) and not _matches(CHOKE_RED, line) \
            and not _matches(CHOKE_STILL_RED, line):
        return None
    if _matches(MILD_CHOKE, line) and not _matches(CHOKE_RED, line) \
            and not _matches(CHOKE_STILL_RED, line):
        return _fit(pick(REPLIES["mild_choke"], memory), line, "minor")
    # Somebody in the water: the fracture card and the toddler's fluids were answering these,
    # because `_minor` and the plain answers both get to the line before the drowning case does.
    # The person is the whole test, so a flooded road, a flooded cellar and a child splashing about
    # in a lesson all keep their own answer.
    if (_matches(WATER_DANGER, line)
            or (_matches(WATER_DROWNING_NOW, line) and not _matches(WATER_DROWNING_FINE, line))) \
            and (_matches(WATER_DANGER_PERSON, line) or _matches(WATER_DROWNING_NOW, line)) \
            and not (_matches(WATER_THING_DROPPED, line)
                     and not _matches(WATER_PERSON_TOO, line)) \
            and not _matches(WATER_NOT_A_PERSON, line) \
            and not (_matches(WATER_PET, line) and not _matches(WATER_HUMAN, line)) \
            and not (_matches(WATER_SELF_PUSH_FINE, line) and not _matches(URGENT_NOW, line)
                     and not _matches(WATER_BREATH_RED, line)
                     and not _matches(WATER_URGENT, line)) \
            and not (_matches(WATER_FINE, line) and not _matches(URGENT_NOW, line)) \
            and not (_matches(WATER_SWIM, line) and not _matches(WATER_URGENT, line)) \
            and not (_matches(WATER_HEAD_FEAR, line)
                     and not _matches(WATER_STILL_BAD, line)
                     and not _matches(WATER_IN_NOW, line)
                     and not _matches(WATER_BREATH_RED, line)) \
            and not (_matches(WATER_SELF_DIP, line) and not _matches(URGENT_NOW, line)
                     and not _matches(WATER_BREATH_RED, line)
                     and not _matches(WATER_URGENT, line)) \
            and not (_matches(WATER_STORY, line) and not _matches(URGENT_NOW, line)
                     and not _matches(WATER_URGENT, line)):
        _note(memory, "drowning")
        if _matches(WATER_SELF_DIP, line) or _matches(WATER_SELF, line):
            return _fit(pick(REPLIES["drowning_self"], memory), line, "drowning")
        return _fit(pick(REPLIES["drowning"], memory), line, "drowning")
    # "there's smoke in the hallway and the fire alarm is going off" is a fire, not an alarm
    # mention: the benign readings of "fire alarm" and "on fire" only hold without the smoke.
    # ...but a line that also says they want to be dead is not a figure of speech: "my dog is going
    # to die and i feel like ending it" is the crisis, whatever else is in it.
    # Alcohol withdrawal, which nothing here answered at all: "i stopped drinking 2 days ago and im
    # shaking" got "Most shaking like this is caffeine, a missed meal, anxiety or a fever", "im 2
    # days off the booze and sweating" got the asking-for-time-off card, and "i stopped drinking 5
    # days ago and i saw things" - the delirium tremens - got "write down what you really drink for
    # a fortnight". Someone stopping after heavy drinking is in the one stretch where the ordinary
    # drinking answers are wrong and the caffeine answer can hurt: the shakes and sweats of the
    # first days are withdrawal, the surgery can make it safe, and confusion, hallucinations or a
    # fit a day or two after the last drink is an ambulance.
    #
    # The stop has to be a stop of the drink: "i stopped drinking coffee" and "i stopped smoking"
    # are the same sentence about something else. A symptom is what makes it a withdrawal rather
    # than a change of habit, and the words withdrawal and detox say it on their own.
    # ...but a fit said in that same line belongs to the fit answer, which the bot already had and
    # which is the first aid: "i had a seizure after stopping drinking" was the delirium tremens
    # card, and it tells the person lying beside them nothing about lying them on their side, moving
    # the hard things away and timing it. The fit case answers every one of those lines with 999 and
    # the recovery position, and the withdrawal card is what the next turn gets.
    withdrawal = None if _matches(WITHDRAWAL_FIT_ITS_OWN_ANSWER, line) else _withdrawal(line)
    if withdrawal and _matches(WITHDRAWAL_ASK_DANGER, line):
        # "should i call 999 for alcohol withdrawal" is the call itself being asked about, and the
        # answer is what the ambulance is for rather than the ambulance.
        _note(memory, "alcohol_withdrawal")
        return pick(REPLIES["alcohol_withdrawal_danger"], memory)
    if withdrawal == "severe":
        _note(memory, "alcohol_withdrawal_severe")
        return pick(REPLIES["alcohol_withdrawal_severe"], memory)
    if withdrawal:
        _note(memory, "alcohol_withdrawal")
        return pick(REPLIES["alcohol_withdrawal"], memory)
    if (_matches(MILD, line) or _matches(FIGURATIVE, line)) and not _matches(FIRE_NOW, line) \
            and not _matches(NOT_WAKING_BESIDE, line) \
            and not _matches(DESPAIR + WISH_INTENT, line):
        # What clears the idiom here is the break still going on, not the word "today": in
        # "this heat is killing me today, i broke my leg years ago" the today belongs to the heat,
        # and the fall and history checks below read a break that is still going on the same way.
        if _matches(PAST_HARM, line) and not _matches(STILL_GOING, line):
            return None
        if _matches(SELF_REASSURED, line):
            return None
        # ...but the idiom only clears the words it is made of: a plain wish in the same line goes
        # on to the self-harm case below, where it is answered.
        wish_named = _matches(WISH_NAMED, line) and not _matches(SUICIDE_MENTION_CONTEXT, line) \
            and not _idiom(line)
        if not wish_named:
            return pick(minor, memory) if minor else None
    # Someone else is the one at risk: answer how to help them, not with the user's own crisis
    # reply. A bare "they" needs a person in the line, or in the turn before it.
    # The speaker's own wish wins over a relative's in the same line: "my nan is going to die and i
    # keep thinking about ending it" is two things, and the crisis is the half that matters.
    if (_matches(SOMEONE_ELSE_RISK, line)
            # "how do i help a friend who self harms" opens with "i" and is still about them.
            and (not _matches(_FIRST_PERSON_ME, line) or _matches(HELP_SOMEONE, line))
            and not _own_wish(line)
            # A figure of speech about someone else is not a person to be watched tonight ("my mum
            # wants to die of embarrassment"), and ending a relationship is not ending a life.
            and not _matches(IDIOM, line)
            and not re.search(r"\bend(?:ing)?\s+it\s+with\b", line)
            # ...and a cause on the line is an accident said in the third person: "my son cut
            # himself badly on glass" is a boy and a pane, not a boy who means it.
            and not _a_reason_it_was_not_meant(line)
            # ...and the animal hurting itself is the vet's, not a person to be watched tonight.
            and not _a_pet_hurting_itself(line)
            # ...and a reflexive verb with its ordinary object after it is the plate, the biscuits
            # or the workload: "my daughter cuts herself a slice of cake", "my son burns himself out
            # at work". The same guard the first-aid row uses, because the wider verb list reads
            # those words too.
            and not _an_ordinary_helping(line)):
        if _matches(HUMAN_ANCHOR, line) or _matches(PERSON_WORD, _person_before(memory)):
            _note(memory, "self_harm")
            return _fit(pick(REPLIES["someone_else"], memory), line, "someone_else")
    # "my souffle collapsed" is about a cake, so the collapse case is not for it - but a fire, a
    # gas smell or chest pain further along the same line still needs its answer.
    # "the bleeding wont stop" with no site and no volume is a person staring at a wound: pressure
    # first, and the step up only if it soaks through or they go pale. A steak, a pen or a ceiling
    # keeps its own answer, and a nosebleed has its own card.
    if (_matches(NOT_STOPPING_BARE, line) and _matches((r"\b(?:bleed\w*|blood)\b",), line)
            # "thanks, still bleeding" is the person carrying on the conversation: the bleeding has to
            # be named as a thing ("the bleeding", "my cut is bleeding") for this to be a fresh turn.
            and re.search(r"\b(?:the|his|her|their|my|your)\s+(?:\w+\s+){0,2}bleed\w*\b", line)
            and not _matches(NOT_A_WOUND_OFF, line)
            and not _matches(WOUND_NAMED, line) and not _matches(BLEED_VOLUME, line)
            and not _matches((r"\bnoses?\b", r"\bnose\s*bleed\b", r"\bperiod\b"), line)
            and not _matches(MOUTH_BLEED_OFF, line)):
        return _fit(pick(REPLIES["bleeding_wont_stop"], memory), line, "minor")
    # A mouth that will not stop bleeding gets pressure and a same-day look, said before any of the
    # bleeding arms can call it an ambulance.
    if _matches(MOUTH_BLEED, line) and _matches(MOUTH_BLEED_NOW, line) and not _matches(
            MOUTH_BLEED_RED, line) and not _matches(MOUTH_BLEED_OFF, line):
        return _fit(pick(REPLIES["mouth_bleed"], memory), line, "minor")
    thing_collapsed = _matches(THING_COLLAPSE, line) and not _matches(A_PERSON, line)
    # "what do i do if i burn my hand" is the way people ask for the first aid for a burn they
    # are about to risk, so the user's own body being the injured thing makes it a real case
    # again. Fiction, someone else and the sign-and-symptom questions stay hypothetical:
    # "what if my son burns his hand" is about the son, not about the person typing.
    own_injury = _matches(OWN_INJURY, line) and not _matches(SOMEONE_ELSE_OWN, line)
    # "what do i do when i feel hopeless" is the person typing about their own night, and the
    # "what do i do when..." frame was reading it as a question about the world: it got the
    # GENERAL["self_harm"] text, which is written for whoever is helping someone else. Despair
    # in the first person is never hypothetical, the same way the user's own burn is not.
    own_despair = (_matches(DESPAIR, line) and _matches(FIRST_PERSON, line)
                   and not _matches(SOMEONE_ELSE_OWN, line))
    hypothetical = (_matches(NOT_NOW_FICTION, line) or _asking_about_the_world(line)
                    or (_matches(NOT_NOW, line) and not own_injury and not own_despair))
    # A dog choking on a bone or a cat that ate something needs the vet, not a human ambulance.
    # A person with a bite or a scratch on them is not the pet: "my dog bit my hand and it is
    # bleeding" was reaching the vet's card, which tells someone with a bleeding hand to ring the
    # vet about their dog. The wound is on the person, so the human answer below has it.
    pet_harm = (_matches(PET_HARM, line) or _matches((PET_WAKE,), line)) and not _matches(
        HUMAN_TOO, line) and not _matches(HUMAN_BITTEN, line)
    # And it still needs an answer: dropping the case left a choking dog with "Noted!".
    pet_past = _matches(PET_PAST, line) and not _matches(PET_NOW, line)
    pet_mild = _matches(PET_MILD, line) and not _matches(
        (r"\bcan'?t\s+breathe\b", r"\bnot\s+breathing\b", r"\bunconscious\b", r"\bseizure\b",
         r"\bchok\w*\b"), line)
    # "my cat is not responding to her treats", "hes 14 and stiff" and "he landed on his feet" are
    # not tonight's call, but a fine word never talks a dog out of not breathing or bleeding.
    pet_all_right = (_matches(PET_FINE, line) or _matches(PET_ALL_RIGHT, line)) and not _matches(
        (r"\bcan'?t\s+breathe\b", r"\bnot\s+breathing\b", r"\bunconscious\b", r"\bseizure\b",
         r"\bchok\w*\b", r"\bbleeding\b", r"\bhit\s+by\b", r"\bran\s+over\b"), line)
    # A pet puffing after a run, gasping for its water or panting in the heat is not a vet call.
    pet_gasp_explained = (_matches(PET_GASP_EXPLAINED, line)
                          and not _matches(PET_GASP_RED, line)
                          and not _matches(PET_GASP_ONGOING, line))
    pet_gasp_fine = (_matches(PET_GASP, line) and not _matches(PET_GASP_RED, line)
                     and (_matches(PET_GASP_FINE, line) or _matches(PET_GASP_NOUN, line)
                          or pet_gasp_explained
                          or (_matches(PET_GASP_SLEEP, line)
                              and _matches(PET_GASP_SLEEP_FINE, line))))
    # A gasp is the same vet-now case as "cannot breathe", whenever the gasp is not one of the ways
    # a healthy animal gets its breath back: "my cat woke up gasping" and "my rabbit is gasping"
    # were answered "Noted: your cat woke up gasping" and a shrug.
    pet_gasp = _matches(PET_GASP, line) and not pet_gasp_fine
    # "my dog has blue gums and is gasping" wants the press-the-gum test, which says what to do with
    # your hands now and is already in the pet table: the vet's night is the weaker half of it.
    pet_gums_told = (_matches(PET_ANY, line) and not _matches(HUMAN_TOO, line)
                     and _matches(PET_MOUTH, line) and _matches(PET_GUMS_TOLD, line)
                     and not _matches(PET_EATEN_THING, line))
    # The pet named twice over is still the pet: "my dog, he cant breathe" was the human 999 card.
    if _matches(PET_APPOSITIVE, line) and (_matches(PET_CRISIS, line)
                                           or _matches(PET_BREATH, line)) \
            and not _matches(HUMAN_TOO, PET_APPOSITIVE_SUB.sub(" ", line)) \
            and not pet_past and not pet_all_right:
        kind = "pet_breath" if (_matches(PET_GASP, line)
                               or _matches(PET_BREATH_ODD, line)) else "pet_emergency"
        if _matches(PET_FIT, line):
            kind = "pet_fit"
        return _fit(pick(REPLIES[kind], memory), line, kind)
    if pet_harm and (_matches(PET_CRISIS, line) or pet_gasp) and not pet_all_right \
            and not pet_gums_told and not pet_past \
            and not pet_mild and not pet_gasp_fine and not (
            pet_all_right and _matches(PET_BEHAVIOUR, line)) and not (
            hypothetical and not _matches(CHOKE_NOW, line)):
        # A fit or a pet that has gone floppy has its own first minutes, not "it ate something".
        if _matches(PET_FIT, line):
            kind = "pet_fit"
        # A pet that will not wake has gone quiet in the same way, and the choking-and-poisoning
        # script is the wrong script for it: nobody brings a wrapper to a dog who won't get up.
        elif (_matches(PET_COLLAPSE, line) or _matches(PET_WAKE, line)
              or _matches((r"\bwak(?:e|ing)\s+up\b",
                           r"\b(?:won'?t|wont|can'?t|cannot|isn'?t|is\s+not|not)\s+wak\w*"),
                          line)) and not _matches(
                (r"\bcan'?t\s+breathe\b", r"\bnot\s+breathing\b", r"\bbleeding\b"), line):
            kind = "pet_collapse"
        # A pet that cannot get its air gets the sentence about the air, not the one about poison.
        elif (_matches(PET_GASP, line) or _matches(PET_BREATH_ODD, line)) \
                and not _matches(PET_EATEN_THING, line):
            kind = "pet_breath"
        else:
            kind = "pet_emergency"
        return _fit(pick(REPLIES[kind], memory), line, kind)
    # A pet that owns the symptom is the vet's: "my dog has chest pains" is not an ambulance, and
    # it is not a shrug either. Only the chest case needs this wider guard, because PET_CRISIS
    # already names the rest of the pet trouble.
    # The animal owns the wound: "a dog bit my cat" is the vet's, and the dog warden's after that,
    # not a person's bite card. A bite on a person keeps the human answer below.
    if _matches(BITE_ON_ANIMAL, line) and not _matches(HUMAN_BITTEN, line) \
            and not _matches(FICTION_NOW, line) and not _matches(PET_LONG_AGO, line):
        kind = "pet_bitten_cat" if _matches((r"\b(?:cat|cats|kitten|kittens)\b",), line) \
            else "pet_bitten"
        return _fit(pick(REPLIES[kind], memory), line, kind)
    pet_own = _matches(PET_OWN, line) and not _matches(HUMAN_TOO, line)
    if pet_own and _matches(CHEST, line):
        return _fit(pick(REPLIES["pet_emergency"], memory), line, "pet_emergency")
    # A pet or a plant that is dying is a loss or a vet bill, not the user's own crisis:
    # "my dog is going to die" was getting the helpline script. It only stands down when the
    # line carries no wish of the speaker's own, so "my dog is going to die and i feel like
    # ending it" keeps the crisis.
    # A garden or a lawn dying is a chore, not a loss: "my lawn is dying and i cant go on" is about
    # the lawn.  So on a line with a garden in it, "i cant go on" is read as "with the lawn" and only
    # an explicit wish (which cannot be about a lawn) stands the guard down.
    if _matches(GARDEN_WORDS, line):
        # "i cant go on living" is the wish with a lawn in front of it: the phrase is read before
        # "cant go on" is folded away as "with the lawn", so the card is not lost to a garden.
        own_wish = _own_wish(_GO_ON_PHRASE.sub(" ", line)) \
            or _matches(GO_ON_LIVING, line)
    else:
        # The speaker's own wish keeps the card: "my dog is going to die and i feel like ending
        # it" is both, and the pet guard stood the whole line down for the grief. The intent the
        # self_harm case is about is the same question, so it is asked here too.
        own_wish = _own_wish(line) or _matches(DESPAIR, line) \
            or _self_harm_intent(line)
    thing_dying = _matches(PET_WORDS + PLANT_WORDS + GARDEN_WORDS + AQUARIUM_WORDS, line) \
        and not _matches(HUMAN_TOO, line) and not own_wish
    # Someone else who is going to die is grief, not the speaker's crisis: "my nan is going to
    # die" and "my mum is going to die soon" were both getting the helpline script, which tells
    # a person watching a relative die to ring a crisis line. The speaker's own wish still wins.
    other_dying = _matches(OTHER_DYING, line) and not own_wish
    # A class, a match or a run that leaves a person puffed is effort, not a symptom. None of the
    # cases match "i was out of breath after spinning" or "i was puffed out after my run", so those
    # lines fell through to a shrug; the words of recovery are what make them ordinary, and a bare
    # "i cant breathe after boxing" has none and keeps its card.
    if _effort_recovery(line) and not any(_matches(p, line) for _, p, _ in CASES):
        return _fit(pick(REPLIES["breath_effort"], memory), line, "breath_effort")
    # The two halves of the glass test can come in two turns, so the rash row gets a
    # second look at the pair of them before it is passed over.
    before = _said_before(memory)
    # The person who was strangled is the reader, and the neck case would answer them as if they
    # were watching: the reply below is the one said to them. A game, a collar or a business keeps
    # its own answer.
    if _matches(STRANGLED_SELF, line) and not _matches(STRANGLE_LOOKALIKE, line):
        _note(memory, "abuse")
        return _fit(pick(REPLIES["strangled_self"], memory), line, "strangled_self")
    # Harm that is not a bite, a burn or a fall of the usual kind, and that main answered with a
    # script about something else: venom, a hoof, and a loop of cord.
    # ...but a dog kicked by a horse, or a cat in the blind cord, is the pet's: the vet today is the
    # answer, not A&E for a person. "my horse kicked me" is the person's, so the verb's object counts.
    # The verb's object decides, and so does the subject: "my horse kicked me" and "i was kicked by
    # a horse" are the person's ribs, and only "my dog got kicked by a horse" is the vet's.
    hurt_is_a_pet = (_matches(PET_OWN + PET_WORDS, line) and not (
        _matches(HUMAN_TOO, line) or _matches(KICKED_PERSON, line)))
    for name, patterns, lookalike in (
            ("snake_bite", SNAKE_BITE, SNAKE_LOOKALIKE),
            ("animal_kick", ANIMAL_KICK, ANIMAL_KICK_LOOKALIKE),
            ("blind_cord", BLIND_CORD, ())):
        if _matches(patterns, line) and not (lookalike and _matches(lookalike, line)):
            if hurt_is_a_pet and name != "snake_bite":
                _note(memory, "pet_hurt")
                return _fit(pick(REPLIES["pet_hurt"], memory), line, "pet_hurt")
            _note(memory, name)
            return _fit(pick(REPLIES[name], memory), line, name)
    # A road scare is not a shove: "someone nearly hit me at the crossing" reached the abuse card,
    # which sends the person to 999 for a blow that never landed. The road place or the vehicle is
    # what makes it the road's, and a person the speaker lives with keeps it the abuse card's.
    if _matches(NEAR_HIT_ON_A_ROAD, line) \
            and (_matches(NEAR_HIT_ON_A_ROAD_PLACE, line)
                 or _matches((_STRUCK_VEHICLE + r"\b",), line)) \
            and not _matches(NEAR_HIT_ON_A_ROAD_NOT, line):
        _note(memory, "near_thing")
        return _fit(pick(REPLIES[_near_thing_key(line)], memory), line, "near_thing")
    # A bike a vehicle struck is the rider's accident, not a bike to carry: "a car hit my bike this
    # morning" reached the answer about strapping a bike to roof bars. A person struck as well
    # keeps the 999 card, and a near miss keeps the near thing's, so those are read first.
    if _matches(STRUCK_MY_BIKE, line) and not _matches(STRUCK_BY_VEHICLE, line) \
            and not _matches(STRUCK_HYPOTHETICAL, line):
        # "my bike nearly got hit by a van" is the same scare as the rider's, not a bike to carry.
        if _matches(STRUCK_NOT_NOW, line):
            _note(memory, "near_thing")
            return _fit(pick(REPLIES[_near_thing_key(line)], memory), line, "near_thing")
        _note(memory, "struck_my_bike")
        return _fit(pick(REPLIES["struck_my_bike"], memory), line, "struck_my_bike")
    for name, patterns, needs_person in CASES:
        if not _matches(patterns, line):
            if not (name == "red_flags" and _glass_test_line(line, before)):
                continue
        # "i cut myself a slice of cake" is the knife and the plate, not the act: the thing after
        # the pronoun stands the self-harm row down here, the same way it does for the first aid.
        if name == "self_harm" and _an_ordinary_helping(line):
            continue
        # A heart attack said in the same breath as a red line is still the heart attack: the
        # spreading redness is a doctor today, and the chest is the ambulance.
        if name in ("wound_streak", "wound_streak_fever") \
                and _matches((r"\bchest\b", r"\bheart\b", r"\bbreastbone\b"), line) \
                and _matches(CHEST + CHEST_ADJ, line):
            continue
        # Not this call: a near miss, a what-if, a collision years ago, a shunt between two cars,
        # a car or a fence that was hit rather than a person, and a pet under a wheel.
        # Something heavy coming down on a person: the line names the collapse, the person under
        # it and nothing else, so the injury word the other rows want is not there.
        if name == "crush":
            if _matches(CRUSH_OFF, line) and not _matches(CRUSH_HARD, line):
                continue
        # Somebody described as unresponsive in manner is not a body on the floor either, and the
        # words after the adjective are what say which it is.
        if (name == "unconscious" and _matches(UNRESPONSIVE_MANNER, line)
                and not _matches(BODY_IN_THE_ROOM, line)):
            continue
        # A professional who has not replied to a message is not a body on the floor.
        if (name == "unconscious" and _matches(PRO_NOT_ANSWERING, line)
                and not _matches(BODY_IN_THE_ROOM, line)):
            continue
            _note(memory, "crush")
            return _fit(pick(REPLIES["crush"], memory), line, "crush")
        if name == "struck_by_vehicle" and (
                _matches(STRUCK_NOT_NOW, line) or _matches(STRUCK_HYPOTHETICAL, line)):
            # A near miss with a vehicle is a scare with its own answer, and standing down left
            # "i nearly got run over on my bike" to "Sounds alright. Anything good in it?" and
            # "i almost went under a bus" to the drowning card. The question, the story and the
            # shunt still stand down: only the near word and the vehicle's own verb are answered.
            if _matches(STRUCK_BY_A_VEHICLE, line) \
                    and not _matches(STRUCK_BY_A_VEHICLE_NOT, line) \
                    and not _matches(STRUCK_HYPOTHETICAL, line) \
                    and not _matches(STILL_GOING + DESPAIR + WISH_INTENT + SELF_HARM_INTENT
                                     + CRISIS_PLAN_SAID, line):
                _note(memory, "near_thing")
                return _fit(pick(REPLIES[_near_thing_key(line)], memory), line, "near_thing")
            continue
        # A fire that nearly started is not a fire, for every card in the fire's family: the
        # building's card, stop-drop-roll and the car's card all stand down together, and the
        # near thing is answered as itself rather than left to whatever else reads the line.
        if (name in ("fire", "clothes_fire", "vehicle_fire")
                and _a_fire_that_did_not_happen(line)
                and not _matches(FIRE_DRILL, line) and not _minor(line, memory)):
            _note(memory, "near_fire")
            return _fit(pick(REPLIES["near_fire"], memory), line, "near_fire")
        # A jam, a child seat and being kept in a car by a person are not a crash: see
        # TRAPPED_VEHICLE_NOT_NOW.
        # A bite on a hand, a face or over a joint is the wide bite card's, which says to get it
        # seen today: the itch card is a downgrade there ("the spider bit my hand").
        if name == "insect_bite" and _matches(INSECT_BITE_NEEDS_A_LOOK, line):
            continue
        if name == "trapped_vehicle" and _matches(TRAPPED_VEHICLE_NOT_NOW, line):
            continue
        if name == "trapped_vehicle" and TRAPPED_HELD_BY_A_PERSON.search(line):
            continue
        if (name == "trapped_vehicle" and TRAPPED_SELF_STUCK.search(line)
                and not TRAPPED_NOT_A_WAIT.search(line)):
            continue
        # A pet under a wheel is the vet's call, not the ambulance's - but standing the row down
        # sent "my cat got run over" to the bereavement card, which tells someone whose cat may be
        # alive that it has died. The pet answer is the one to give.
        if (name == "struck_by_vehicle" and _matches(PET_WORDS, line)
                and not _matches(HUMAN_TOO, line)):
            _note(memory, "pet_hurt")
            return _fit(pick(REPLIES["pet_hurt"], memory), line, "pet_hurt")
        # The weather falling is not a fever however confused the person is ("the temperature
        # keeps falling and im confused about what to wear" was the sepsis card).
        if (name in FEVER_CASES and _matches(TEMP_FALLING_WEATHER, line)
                and not _matches(FEVER_NOT_THE_WEATHER, line)):
            continue
        # The chest row is the heart-call card. When the line also says the person has gone down
        # or is not breathing, that card - recovery position, stay on the line, CPR - is the one
        # to give, so the chest row steps aside and lets it through.
        if name == "chest" and _matches(CHEST_ANSWERED_ELSEWHERE, line):
            continue
        # A laugh is what took the breath: "i cant catch my breath when i laugh" and "i laugh so
        # hard i cant breathe" were both the 999 card on main, and the breath is back in a few
        # seconds after a laugh. The laugh has to be the thing the breath belongs to, and a red
        # flag beside it (blue lips, a chest that hurts, a wheeze) still rings the ambulance.
        if name in ("breathing", "breath_weeks", "breath_past") \
                and _matches(LAUGH_WORD, line) and _matches(LAUGH_TAKES_BREATH, line) \
                and not _matches(BREATH_RED + BREATH_AT_REST + LAUGH_BREATH_RED
                                 + LAUGH_OTHER_PERSON, line):
            _note(memory, "breath_laugh")
            return _fit(pick(REPLIES["breath_laugh"], memory), line, "breath_laugh")
        # The weather is a cause the line names too: "i cant breathe in this heat" was the 999
        # card, telling someone in a heatwave to start CPR on themselves. Heat sends the blood to
        # the skin, so the breath comes back once the person is cool; a chest, a faint or a breath
        # that has not settled keeps the emergency.
        if name in ("breathing", "breath_weeks", "breath_past") \
                and _matches(HEAT_CAUSE, line) and _matches(BREATH_BARE, line) \
                and not _matches(HEAT_NOT_WEATHER, line) \
                and not _matches(BREATH_RED + BREATH_AT_REST + HEAT_BREATH_RED, line):
            _note(memory, "breath_heat")
            return _fit(pick(REPLIES["breath_heat"], memory), line, "breath_heat")
        # A pet that could not breathe is the vet's line, not the human ambulance.
        if name == "breath_past" and _matches(PET_OWN, line) and not _matches(HUMAN_TOO, line):
            return _fit(pick(REPLIES["pet_emergency"], memory), line, "pet_emergency")
        if name == "breath_past" and not _matches(BREATH_PAST_CUE, line) and not _matches(
                (CHILD_WORD,), line):
            continue
        # A birth story or a bout years ago is a memory, not this week's accident.
        if name == "breath_past" and _matches(BREATH_PAST_OVER, line) and not _matches(
                BREATH_RED, line):
            continue
        # A blue face or blue lips outranks a breath that came back: that is the 999 call now.
        if name == "breath_past" and (_matches(BLUE_LIPS_FACE, line) or (
                _matches(BLUE, line) and _matches(PERSON_WORD, line)
                and not _matches(BLUE_FOOD, line) and not _matches(BLUE_COLD_SELF, line))):
            continue
        # A plant, a phone or a plate of chips is not in the water: "i nearly drowned my plant" was
        # the drowning card with "say they were in the water" in it.
        if name in ("drowning", "water_danger") and _matches(DROWNED_THING, line):
            continue
        # "i cut myself off from my friends" is company, not a cut: the first-aid card is the wrong
        # script for a lonely year, and the crisis card was wrong before it.
        if name == "cut" and _cut_off_idiom(line):
            continue
        # A pet that is dying is grief, unless the line says the user wants to follow it.
        # ...and a wish said as a feeling or as being gone is the speaker following it: "my dog is
        # going to die and nobody would notice" is the crisis half, not the vet half.
        # The speaker following the animal is the half that matters, however it is said: "my cat is
        # dying and i dont want to live" is not a vet question, and OWN_WISH is what reads the wish
        # without the words this guard used to look for ("i dont", "i cant", "i cant go on").
        if (name == "self_harm" and _matches(PET_DYING, line)
                and not _matches((r"\bi\s+(?:want|wanna|need|might|will|could|should|do)\b",
                                  r"\bmy\s*self\b", r"\bme\s+too\b", r"\bwith\s+him\b",
                                  r"\bwith\s+her\b"), line)
                and not _matches(DESPAIR + WISH_INTENT, line) and not _own_wish(line)):
            return _fit(pick(REPLIES["pet_loss"], memory), line, "pet_loss")
        # ...and a wish the speaker has just denied: "im not suicidal", "i would never kill myself".
        # "i feel like cutting my arms" was read as a garden line: `cuttings?` in PLANT_WORDS
        # matches "cutting", so the plant word alone made thing_dying true and stood the card
        # down. A wish to cut the speaker's own body part is not about a plant.
        if name == "self_harm" and ((thing_dying and not _a_wish_for_their_own_body(line))
                                   or other_dying or suicide_elsewhere
                                   or denied_wish or topic_talk):
            continue
        # Flames out of a phone or a laptop are the battery answer, not the building card: water
        # and a cloth make a lithium fire worse, and "leave the building straight away" is not what
        # helps with a phone on the desk. A room named in the line keeps the card, because then the
        # fire is the room's and not the device's.
        # A pan alight is answered by the pan's own ten seconds, but only while the fire is still
        # in the pan: smoke, the hood, the ceiling or the alarm is the building's card.
        if name == "pan_fire" and _matches(PAN_FIRE_SPREAD, line):
            continue
        if (name == "fire" and (_matches(BATTERY_FIRE, line) or _matches(DEVICE_BURNING, line))
                and not _matches(ROOM_OR_HOUSE, line)):
            continue
        # Burnt food is smoke, not a fire: the toast line is air the room and open a window.
        if (name == "fire" and _matches(BURNT_FOOD, line) and not _matches(FIRE_OUT, line)
                and not _matches(BATTERY_FIRE, line)):
            continue
        # A flame in the thing that is built to hold one - a barbecue, a grill, a lit fireplace, a
        # wood burner, a candle, a fire on a screen - belongs to that thing, not to the building,
        # unless the line also says the fire got out: smoke, the ceiling, "caught fire".
        if (name == "fire" and _matches(FLAMES_NOT_FIRE, line)
                and not _matches(FIRE_ELSEWHERE, line)):
            continue
        # A dog that keeps biting is a habit, not an attack: see DOG_HABIT.
        if name in ("dog_attack", "dog_bite") and _matches(DOG_HABIT, line) \
                and not _matches(DOG_ATTACK_NOW, line) and not _matches(DOG_BLEED, line) \
                and not _matches(BITE_DONE, line):
            continue
        # A thing bitten first and a hand caught second is mouthing, not an attack: see
        # DOG_MOUTHING. The habit words above do not cover it, because nobody calls it a habit.
        if name in ("dog_attack", "dog_bite") and _matches(DOG_MOUTHING, line) \
                and not _matches(DOG_ATTACK_NOW, line) and not _matches(DOG_BLEED, line):
            continue
        # An engine that burns oil is the engine question, not a fire.
        if (name == "vehicle_fire" and _matches(VEHICLE_NOT_FIRE, line)
                and not _matches(VEHICLE_STILL_FIRE, line)):
            continue
        # A smell of burning in a car is the brakes or the clutch unless a fire word, smoke or a
        # part is in the line with it.
        if name in ("vehicle_fire", "fire") and _matches(VEHICLE_BURNING_SMELL, line) \
                and not _matches(VEHICLE_BURNING_SMELL_HARD, line):
            continue
        # A report of a fire that has already been put out is a story, not an emergency.
        if name in ("vehicle_fire", "fire") and _matches(VEHICLE_FIRE_OVER, line) \
                and not _matches(VEHICLE_FIRE_OVER_HARD, line):
            continue
        if name in ("vehicle_fire", "fire") and _matches(VEHICLE_BURNING_A_PERSON, line) \
                and not _matches(VEHICLE_BURNING_A_PERSON_HARD, line):
            continue
        # A car that burns oil is the oil question, not a fire: the fire case has "car" in front of
        # "burning" and told a driver to leave the building. A smoke word does not make it a fire -
        # "my car is burning oil and there is smoke" is the worn engine - so only a named flame,
        # the bonnet or the dashboard keeps the card here.
        if (name == "fire" and _matches(VEHICLE_NOT_FIRE, line)
                and not _matches(VEHICLE_EXHAUST_HARD, line)):
            continue
        # Smoke out of the exhaust is a car that runs badly, not a building on fire.
        if (name == "fire" and _matches(VEHICLE_EXHAUST, line)
                and not _matches(VEHICLE_EXHAUST_HARD, line)):
            continue
        # One appliance that smokes, or an alarm set off by the cooking, is not a house fire: the
        # answer is off at the wall, the door shut and a window open, which the home entries give.
        # Flames, a room filling, smoke in the hall or a way out you cannot take keep the card.
        if name == "fire" and not _matches(FIRE_SCALE, line) and (
                _matches(APPLIANCE_SMOKE, line) or _matches(ALARM_NUISANCE, line)):
            continue
        # A smell of smoke on a coat, a jumper, hair or a car seat is a laundry question, and the
        # fire card for it is the bot mistaking a smell for an emergency. The card keeps the lines
        # where there is smoke in a place, where the alarm is going off, or where the fire scale
        # says the fire is more than a smell - and a line with no thing in it at all, because "i
        # can smell smoke" on its own is a warning sign and not a washing question.
        if (name == "fire" and _matches(SMOKE_IS_A_SMELL, line)
                and SMELL_ON_A_THING.search(line) and not _matches(ROOM_OR_HOUSE, line)
                and not _matches(FIRE_SCALE, line) and not _matches(ALARM_NUISANCE, line)):
            continue
        # "the death of my wife has hit me hard" is a bereavement, not an assault: the alarm rings
        # on the person phrase inside it, so the case stands down when the loss is what hit them.
        if name == "abuse" and _hit_by_a_loss(line) and not _matches(ABUSE_NOT_HIT, line):
            continue
        # A dog biting itself, or a scratching, itchy, balding pet, is a skin question for the
        # vet, not a dog attack on a person.
        if name in ("dog_bite", "dog_attack") and not _matches(HUMAN_TOO, line) \
                and not _matches(DOG_BIT_A_PERSON, line) \
                and (_matches(DOG_SELF_BITE, line)
                     or (_matches(PET_OWN, line) and _matches(DOG_ITCH, line))):
            continue
        # A collar, a scarf in a door, a game or a business being strangled is not a hand on a
        # throat: the neck case stands down with the victim reply it would otherwise answer.
        if name == "hanging" and _matches(STRANGLE_LOOKALIKE, line):
            continue
        # "how do i build up without hurting myself": the harm is what they mean to avoid.
        if name == "self_harm" and _avoided(line, SELF_HARM):
            continue
        # Sore arms after a session is the training answer: "i want to hurt my arms at the gym" was
        # the crisis card on a head that read `hurt my arms` as the wish. A blade keeps the card
        # whatever the rest of the line says, so this only ever takes the line that has the verb
        # `hurt` or `harm` and a workout in it.
        if name == "self_harm" and re.search(A_HURT_OF_A_BODY_PART, line) \
                and re.search(A_WORKOUT_CUE, line):
            continue
        # A short week is not the end of one: where the line has named the money, the `nothing
        # left` clause is the money, so this case stands down - unless something else in the list
        # rings, so a real wish said next to money keeps the card.
        if (name == "self_harm" and MONEY_NAMED.search(line) and _matches(NOTHING_LEFT, line)
                and not SOMEONE_HOLDS_THE_MONEY.search(line)
                and not _matches(DESPAIR_WITHOUT_NOTHING_LEFT + WISH_INTENT + SELF_HARM_INTENT,
                                 line)):
            continue
        # The weak-side arms this lane added stand down for the ordinary numb lines - a cold hand,
        # a limb slept on, a trapped nerve - unless one of the older stroke arms is in the line.
        # Sight that went days or weeks ago is the eye clinic today, not the ambulance: the weak
        # sight arms are written for what has just happened, and "i cant see out of my left eye for
        # 2 days" came back as 999. The sight that went this morning still rings.
        if name == "stroke" and not _matches(STROKE, line) \
                and _matches(SIGHT_WORD, line) and _matches(SIGHT_A_WHILE, line):
            _note(memory, "sight_days")
            return _fit(pick(REPLIES["sight_days"], memory), line, "sight_days")
        # A hand that keeps dropping and a head that feels confused is a tired or anxious person
        # about themselves, not a stroke: it needs the confusion to be someone else's, or another
        # sign of the same stroke in the line.
        if (name == "stroke" and _matches(STROKE_HAND, line)
                and _matches(STROKE_HAND_SELF, line)
                and not _matches(STROKE_HAND_OTHER, line)):
            continue
        # A hand and a weak or confused head with a known cause in the line is that cause: the flu,
        # the cold, Raynaud's, arthritis, a dementia already named, a child of two. The hard signs
        # - the face dropped, the words gone, one side gone - are new and keep the card.
        if (name == "stroke" and _matches(STROKE_HAND, line)
                and _matches(STROKE_HAND_CHRONIC, line)
                and not _matches(STROKE_HAND_HARD, line)):
            continue
        # A pet's eye is the vet's question: "my cat is going blind" and "my cat has gone blind in
        # one eye" rang 999 for a stroke in a person (breezy-ruler, #safety). The weak sight and
        # weak-side arms read the animal as the patient, and the pet sight answer already exists.
        # The word stroke itself, or a person in the same line, keeps the card.
        if name == "stroke" and not _matches(STROKE, line) \
                and _matches(PET_SUBJECT + PET_SUBJECT_PLURAL, line) \
                and not _matches(HUMAN_TOO + MY_OWN_PART, line):
            # Standing the person's card down is half the answer. With the person's stroke card out
            # of the way, a pet whose side has gone weak fell through to "Got it. Is there anything
            # you'd like a hand with?" - there was no pet weak-side answer to land on, which is the
            # other half of the same bug (steward-teal-donkey, #safety). A side that has gone, a
            # droop, a drag or a tilted head in the animal is the vet now; the pet sight answer
            # above keeps "my cat is going blind". The reply text is ivory-orange's from #10804.
            if _matches(PET_WEAK, line):
                _note(memory, "pet_weak")
                return _fit(pick(REPLIES["pet_weak"], memory), line, "pet_weak")
            continue
        # The FAST pair outranks the wide stand-down: `dentist`, `cold` and `slept on` are in it,
        # so "my face is numb from the dentist and my arm is weak" was stood down here and never
        # reached the pair below. A pair is the pair whatever else is in the line.
        if name == "stroke" and not _matches(STROKE, line) and _matches(STROKE_WEAK_OFF, line) \
                and not _matches(STROKE_FAST, line):
            continue
        # An old pet going blind is not a person having a stroke: "my dog is 12 and going blind"
        # rang 999 because "going blind" is one of the stroke signs. The pet has to be the subject,
        # and a first person or a human sign in the same line keeps the card.
        if name == "stroke" and not _matches(STROKE, line) \
                and _matches(PET_SUBJECT, line) and _matches(PET_SIGHT, line) \
                and not _matches(FIRST_PERSON, line) and not _matches(HUMAN_ANCHOR, line):
            continue
        # A nail that went into the shoe is a puncture; a tyre, a wall and a picture hook are not.
        if name == "puncture" and _matches(PUNCTURE_OFF, line):
            continue
        # A baby who fell and is now sick, sleepy or floppy is the head answer's ambulance, not
        # this same-day check.
        # A bang on the head already has its own watch-or-999 answer further down, and it was
        # right for "my toddler fell off the sofa and hit his head": this card is only for a fall
        # that says nothing else.
        if name == "baby_fell" and _head_bang(line):
            continue
        # A baby who went to sleep did not fall: bedtime, a nap in the car and a dropped dummy are
        # what babies do, and the red-flag list has "asleep" in it, so this guard has to come
        # first or "my baby fell asleep" is the ambulance.
        if name == "baby_fell" and _matches(BABY_FELL_OFF, line) \
                and not _matches(BABY_FELL_SURFACE, line):
            continue
        if name == "baby_fell" and _matches(BABY_FELL_RED, line):
            _note(memory, "baby_fell_red")
            return _fit(pick(REPLIES["baby_fell_red"], memory), line, "baby_fell_red")
        # A short fall with nothing after it is learning to walk, and the red flags have already
        # had their turn above.
        if name == "baby_fell" and _matches(BABY_FELL_OVER, line):
            continue
        # An electric cooker is not the gas ring (see ELECTRIC_COOKER): the cooking answer for
        # "can I leave the slow cooker on while I'm at work" is a better reply than the leak script.
        if name == "gas_left" and _matches(ELECTRIC_COOKER, line) and not _matches(GAS_WORD, line):
            continue
        if pet_harm and name in ("breathing", "bleeding", "poison", "swallowed_thing", "seizure",
                                 "unconscious", "broken", "hypo", "chest", "stroke", "heat",
                                 "hanging", "fall", "bone_throat"):
            continue
        # The amount of blood does not decide a nose: "my nose is bleeding a lot" is a nosebleed,
        # which has its own card further down, not an ambulance. Anything that makes it the
        # exception (blood that will not stop, a blood thinner, going faint, a knock on the head)
        # keeps the ambulance, and so does a nose that is not the only place bleeding.
        if name == "bleeding" and _matches(NOSE_SITE, line) and not _matches(NOSE_RED, line) \
                and not _matches((r"\b(?:cut|gash|gashes|wound|wounds|sliced|stabbed|graze[ds]?)\b",),
                                 line):
            continue
        # A nose that is blocked explains the breathing, and lying down or sitting still takes
        # the urgent answer instead: "i cant breathe because my nose is blocked" was ring-999.
        # A blocked nose or a chesty cold does explain the breathing, so it is not the ambulance -
        # but it is not nothing either. It gets the same-day line, because "I'm listening" is no
        # answer to "i cant breathe".
        if name == "breathing" and not _matches(BREATH_AT_REST, line) and _matches(
                BREATH_CAUSE, line) and not _matches(BREATH_CAUSE_RED, line):
            _note(memory, "breath_cause")
            if not (_matches(NIGHT_BREATH, line) and _matches(BREATH_CAUSE, line)):
                return _fit(pick(REPLIES["breath_cause"], memory), line, "breath_cause")
            continue
        # Breathless in the night, or when lying flat, is the same-day appointment the night case
        # below gives; a red flag or a night still going on keeps the ambulance here.
        if name == "breathing" and _matches(NIGHT_BREATH, line) \
                and not _matches(NIGHT_BREATH_RED, line):
            continue
        # Someone who has stopped breathing needs CPR, not the chest pain or the inhaler reply.
        if name == "chest" and _matches(NOT_BREATHING_NOW, line):
            continue
        # A cuppa is not an airway: "im gasping for a brew" was ringing 999, which in Britain is
        # how you say you are thirsty.
        # The bare word is also a red flag, so take the gasp out of the line first and let the
        # other red flags decide.
        # The red-flag re-check runs on the line with the gasp word taken out, because
        # "gasping" is itself one of the BREATH_RED patterns: without the strip the guard can
        # never fire. A line that says it cannot breathe is a red flag on its own.
        _gasp_stripped = re.sub(r"\bgasp\w*", "", line, flags=re.I)
        if name == "breathing" and _matches(GASPING_THIRST, line) \
                and not _matches(BREATH_RED + BREATH_STILL_RED, _gasp_stripped):
            continue
        if name == "breathing" and _matches(NOT_BREATHING_NOW, line):
            _note(memory, "not_breathing")
            # 30:2 at 5-6 cm is the adult sequence; a baby or a child gets its own.
            if _matches(CPR_BABY, line):
                return _fit(pick(CPR_BABY_SCENE, memory), line, "not_breathing")
            if _matches(CPR_CHILD, line):
                return _fit(pick(CPR_CHILD_SCENE, memory), line, "not_breathing")
            return _fit(pick(REPLIES["not_breathing"], memory), line, "not_breathing")
        # A class or a sport named with the words of recovery is effort, not the lungs: "i cant catch
        # my breath after spin class" rang the ambulance for a person who had just done some
        # exercise, and "i was out of breath after spinning" got a shrug. The recovery phrase is what
        # makes it ordinary; a bare "i cant breathe after boxing" has none and keeps its card.
        if name in ("breathing", "breath_weeks", "breath_past") and _effort_recovery(line):
            return _fit(pick(REPLIES["breath_effort"], memory), line, "breath_effort")
        # Laughing hard leaves anyone gasping, and the ambulance for it is a false alarm: the laugh
        # has to be the stated cause ("when i laugh", "laughing makes me"), and at rest, a wheeze,
        # chest pain, blue lips or blood still keep the breath card above.
        if (name in ("breathing", "breath_weeks", "breath_past")
                and _matches(BREATH_LAUGH, line)
                # ...and the same two fences the newer laugh card carries, because this card was
                # answering a laugh that never gave the breath back ("for ages") and a child's
                # laugh as if it were the speaker's own.
                and not _matches(BREATH_RED + BREATH_STILL_RED + LAUGH_BREATH_RED
                                 + LAUGH_OTHER_PERSON, line)
                and not _matches(BREATH_AT_REST, line)
                and not _matches((r"\bstill\b", r"\bright\s+now\b"), line)):
            return _fit(pick(BREATH_LAUGH_REPLY, memory), line)
        # Breathlessness that comes on with effort, and nothing else, is ordinary.
        if name == "breathing" and _matches(EXERTION, line) and not _matches(BREATH_RED, line):
            continue
        if (name == "breathing" and _matches(SHORT_OF_BREATH, line)
                and _matches(EFFORT_ANYWHERE, line) and not _matches(BREATH_RED, line)
                and (_matches(OUT_OF_BREATH, line) or not _matches(EFFORT_WEAK, line))):
            continue
        # "the app has trouble breathing", "my car is having trouble breathing": a person or pet
        # in the line always wins, a gadget on its own never does.
        if (name == "breathing" and _matches(NOT_A_BREATHER, line)
                and not _matches(A_BREATHER, line) and not _matches(BREATH_RED, line)):
            continue
        # Said to be over: "my mum is short of breath and it passed", "hes short of breath but hes
        # fine now". An ambulance for a symptom the person has just told you has gone is the bot not
        # listening, and the cheerful ack it would otherwise get ("Lovely to hear. Enjoy it!") is not
        # honest either, so this gets its own line: good that it passed, and still worth a same-day
        # check. `still` and `right now` keep the ambulance, because those are the present tense.
        # A choke that is over is the cough advice below, not this: "he choked on a grape but hes
        # fine now" wants the cough and the 999 test, not a same-day breathlessness check.
        if (name == "breathing" and _matches(BREATH_OVER, line)
                and not _matches(BREATH_RED + BREATH_STILL_RED, line)
                and not _matches((r"\bstill\b", r"\bright\s+now\b"), line)
                and not _matches(CHOKE_HELP, line)):
            return _fit(pick(REPLIES["breath_past"], memory), line, "breath_past")
        # A habit of breathlessness while talking or singing for a long stretch is not the red flag
        # that "short of breath while talking" is, and main answered it with a shrug.
        if (name == "breathing" and _matches(TALK_HABIT, line)
                and not _matches(BREATH_RED + BREATH_STILL_RED, line)):
            continue
        # A duration makes it a symptom rather than an emergency: weeks of breathlessness is a
        # same-day appointment, and an ambulance for it frightens someone who was only saying how
        # long it had been going on. A red flag or "can't breathe" anywhere in the line still wins.
        if (name == "breathing" and _matches(CHRONIC_BREATH, line)
                and not _matches(BREATH_RED + BREATH_STILL_RED, line)):
            return _fit(pick(REPLIES["breath_weeks"], memory), line, "breath_weeks")
        # Something that went down the wrong way an hour ago and is over is not an emergency.
        # A choking that is over - last year, at lunch, as a kid - is a memory for every arm that
        # answers choking, not only the breathing one.
        if name in ("breathing", "breath_past", "bone_throat", "bone_throat_red") and _matches(
                CHOKE_OVER, line) and not _matches(CHOKE_NOW, line):
            # A choke that is over is still worth the cough advice and the 999 test when a person
            # is the one who did it: "my gran choked at lunch" is somebody asking whether that
            # was handled right, and it was getting a shrug instead of any answer at all.
            # The thing that chokes (a sink, a drain, an engine), a habit ("my baby used to choke
            # on lumps", which is the weaning question) and a first-person choke, which
            # `MILD_CHOKE` answers on its own, all stand down exactly as before.
            if (_matches(CHOKE_PERSON, line) and not _matches(CHOKE_NOT_PERSON, line)
                    and not _matches(CHOKE_HABIT, line)):
                _note(memory, "choking")
                return _fit(pick(REPLIES["mild_choke"], memory), line, "minor")
            continue
        # A sink, a drain, an engine or a lawn chokes too, and "how do i stop my baby choking" is a
        # question about a baby who is not choking: neither is this minute, so the breathing case
        # stands down and the module that owns the line answers it.
        if name == "breathing" and _matches(CHOKE_NOT_PERSON, line) \
                and not _matches(CHOKE_PERSON, line) and not _matches(CHOKE_NOW, line):
            continue
        # Someone choking now gets the back blows and the thrusts while the ambulance comes. The
        # cough that still works, a thing in the line and a choking that is over all stay ordinary.
        # A person choking with no air gets the hands, not a phone number: five back blows, five
        # abdominal thrusts, and the baby or the self version of the same thing. A thing that
        # chokes (sink, drains, engine), the prevention question, a laugh and a choke that is
        # already over are all somebody else's line, so they pass.
        if (name in ("breathing", "stroke") and _matches(CHOKE_HELP, line)
                and not _matches(PET_HARM, line)
                and not (_matches(CHOKE_NOT_PERSON, line)
                         and not _matches(CHOKE_PERSON, line))):
            if _matches(CHOKE_PREVENT, line):
                # How do i stop my baby choking on grapes: the shape of the food, for a baby who
                # is not choking. It is the same question the parent asks a health visitor.
                return _fit(pick(REPLIES["choke_prevent"], memory), line, "minor")
            if _matches(CHOKE_AIR_OK, line) or _matches(CHOKE_SETTLED, line):
                # The cough that still works is the airway clearing itself: the cough advice, not
                # the five and five, and not a bare ambulance card.
                _note(memory, "choking")
                return _fit(pick(REPLIES["mild_choke"], memory), line, "minor")
            if _matches(CHOKE_BABY, line):
                _note(memory, "choking")
                return _fit(pick(REPLIES["choking_baby"], memory), line, "breathing")
            kind = "choking_self" if _matches(FIRST_PERSON, line) \
                and not _matches(CHOKE_PERSON, line) else "choking_help"
            _note(memory, "choking")
            return _fit(pick(REPLIES[kind], memory), line, "breathing")
        if _matches(BONE_PAST, line) and not _matches(BONE_STILL, line) and _matches(
                BONE_THROAT, line) and not _matches(BONE_RED, line):
            continue
        # A bone in the throat: the swallow and the breath decide whether it is the ambulance or
        # the same-day check; a bone in the stock pot, the leg or a dog's mouth is none of this.
        if name == "bone_throat":
            if _matches(BONE_ORDINARY, line) and not _matches(BONE_RED, line):
                continue
            if _matches(BONE_RED, line):
                return _fit(pick(REPLIES["bone_throat_red"], memory), line, "bone_throat")
        if name == "self_harm" and _matches(WORLD_QUESTION, line) and not _matches(
                (r"\bi\b", r"\bmy\b", r"\bmyself\b"), line):
            continue
        if name == "child_drank" and _matches(CHILD_DRANK_WEAK, line) and not _matches(
                CHILD_YOUNG, line):
            continue
        # The numbing after a filling explains the slurring; a drooping face, a weak limb or
        # confusion with it does not, and those keep walking down to the stroke card.
        # A child that young is usually just learning the sounds; a weak side or a fit beside it
        # is not that, and keeps the ambulance.
        # A weak side or a drooping face with the drink is the ambulance: the drink explains the
        # mouth, not the arm.
        if name == "slur_drink" and _matches(SLUR_RED_BESIDE, line):
            _note(memory, "stroke")
            return _fit(pick(REPLIES["stroke"], memory), line, "stroke")
        if name == "slur_small_child":
            if _matches(SLUR_RED_BESIDE, line) or _matches((r"\bfit\b", r"\bfever\b", r"\brash\b"), line):
                _note(memory, "stroke")
                return _fit(pick(REPLIES["stroke"], memory), line, "stroke")
            # No case is noted: the child card is a question, not an emergency under way, and a
            # noted case made every later line sound like an ambulance was coming ("will he be ok
            # for school tomorrow" got "do what the emergency line says").
            return _fit(pick(REPLIES["slur_small_child"], memory), line)
        if name == "dental_numb":
            if _matches(DENTAL_NUMB_RED, line):
                # The dentist explains the words, not the weakness: a drooping face, a weak or
                # numb limb or confusion beside it is the ambulance, dentist or no dentist.
                _note(memory, "stroke")
                return _fit(pick(REPLIES["stroke"], memory), line, "stroke")
            _note(memory, "dental_numb")
            return _fit(pick(REPLIES["dental_numb"], memory), line)
        # `i choked on my drink and now i cant speak` is a blocked airway, not a stroke:
        # "can't speak" and "slurred" are stroke words but a choke is the thing to answer.
        if name == "stroke" and _matches((r"\bchok(?:ed|ing|es)\b",), line):
            continue
        # Thirsty, or out of puff after a run, is not breathlessness.
        if name in ("breathing", "breath_weeks", "breath_past") and _matches(GASP_FINE, line) and not _matches(GASP_RED, line):
            continue
        # A ball thrown at you in a game, a push into the pool, a hand grabbed to stop you
        # falling: the abuse words are there but nothing is being done to you.
        # An ex on the doorstep with the kids is a handover, and "my ex is outside my house
        # dropping them off" is the same event said the long way round.
        if name == "abuse" and _matches(PURSUIT_FINE, line) and not _matches(ABUSE_PURSUIT_HARD, line):
            continue
        # ... but the parent's-no stand-down inside ABUSE_FINE is the one piece of that list that
        # swallows a blow with it: "my dad wont let me out and he hit me", "my dad hit me and he
        # wont let me leave the house" and "my dad wont let me out and he punched me" are a rule
        # and a hand on the body in the same breath, and a parent's no is not an answer to those.
        # ...and the same is true whoever is saying no. This was the parent's exemption alone, so
        # "my boss wont let me go home and he grabbed my arm" lost the card to a rule about a rota
        # while the same sentence about a husband kept it: the refusal is who it is, the hand is
        # what is happening (deck row saf-pc-ref-22).
        if name == "abuse" and _matches(ABUSE_FINE, line) \
                and not (_matches(ABUSE_PARENT_REFUSAL, line)
                         and _matches(PARENT_REFUSAL_BLOW, line)) \
                and not (_matches(ANY_REFUSAL_TO_GO, line)
                         and _matches(A_HAND_ON_THE_PERSON, line)):
            continue
        # A nickname and a family who tease each other are the same words without the habit: only
        # the put-down aimed at the speaker in the lines above keeps the card.
        # ...and the same words with a hand in the line are not teasing: "he pushes me and calls
        # me names" was stood down by the "names" in it and answered with "I'm listening". The one
        # exception is the child doing it: "my son pushes me and calls me names" is a Tuesday with
        # a small person, and the parenting answer it already has is better than the card.
        if name == "abuse" and _matches(ABUSE_VERBAL_FINE, line) \
                and not _matches(ABUSE_BLOW, line) \
                and not (_matches(ABUSE_HIT_ME, line)
                         and not _matches(CHILD_AGGRESSOR, line)):
            continue
        # A face put into a soft thing is a mess, not a blow: the reply it wants is the one
        # SOFT_FACE_PUSH answers above. A blow, a hold or a breath word in the line keeps the
        # card, so "he pushed my face into the snow and i couldnt breathe" is still an emergency.
        if name == "abuse" and _matches(SOFT_FACE_PUSH, line) \
                and not _matches(SOFT_FACE_STOP, line):
            continue
        # A small child lashing out in play is not abuse, and a hand brushed away is not a blow:
        # "my son hit my face while playing" is a Tuesday, and the card's 999 is not for it.
        if (name == "abuse" and _matches(PLAYFUL_HIT, line)
                and not _matches(ADULT_HIT, line)):
            continue
        # A hand pushed off a person is a gesture, not a blow - unless the line says a blow landed
        # too, or an adult did it.
        if (name == "abuse" and _matches(PUSHED_AWAY, line)
                and not _matches(BLOW_ON_ME, line) and not _matches(ADULT_HIT, line)
                and not _matches(RESTRAINT_BESIDE, line)):
            # The card stands down, but the person is still talking about a hand that was moved
            # off them: it gets an answer that fits that, rather than the cheer of the greeting
            # pools ("Sounds alright. Anything good in it?"). The answer is not a shrug either -
            # the one question that separates a gesture from a blow, and the offer to hear the
            # rest (peach-hammer, steward-frank-chicken, #safety 87919, 88092).
            if _matches(PUSHED_AWAY_THEN_RESTRAINT, line):
                # Stopped from leaving, thrown into a door, hurt on the way down: the gesture is
                # the smallest thing in the line and the card is right (cyan-trumpet, #safety
                # 88437: "he pushed my arm away so i couldnt leave", "...and i hit the wall").
                pass
            elif _matches(PUSHED_AWAY_BUT_SOMETHING_ELSE, line):
                # Something else is the subject - a pan, the dinner, a child - and it keeps the
                # answer that subject has.
                continue
            else:
                return _fit(pick(PUSHED_AWAY_REPLY, memory), line)
        # A boss refusing hours is a job, not the card: see ABUSE_EMPLOYER_REFUSAL. A hand, a blow,
        # a threat or a lock beside it keeps the card.
        if name == "abuse" and _matches(ABUSE_EMPLOYER_REFUSAL, line) \
                and not _matches(ABUSE_PARENT_REFUSAL_HARD, line) \
                and not _matches(PARENT_REFUSAL_BLOW, line) \
                and not _matches(ABUSE_HANDS_ON, line) \
                and not _matches(ABUSE_PARTNER_DID_IT, line):
            continue
        # ...and a child who will not let you sleep is a Tuesday. See ABUSE_CHILD_REFUSAL.
        if name == "abuse" and _matches(ABUSE_CHILD_REFUSAL, line) \
                and not _matches(ABUSE_CHILD_TAKES_MONEY, line) \
                and not _matches(PARENT_REFUSAL_BLOW, line) \
                and not _matches(ABUSE_HANDS_ON, line):
            continue
        # A parent's no is parenting: see ABUSE_PARENT_REFUSAL. A blow, a hand on the body, a lock
        # or a partner in the line keeps the card.
        if name == "abuse" and _matches(ABUSE_PARENT_REFUSAL, line) \
                and not _matches(ABUSE_PARENT_REFUSAL_HARD, line) \
                and not _matches(ABUSE_HANDS_ON, line) \
                and not _matches(ABUSE_PARTNER_DID_IT, line):
            continue
        # The line says it was play, and nothing in it says more than play: see HIT_IN_FUN. It gets
        # an ordinary answer rather than the card, and not a shrug either - leaving it to the next
        # module put a bull joke on "my boyfriend hit me on the arm as a joke".
        if name == "abuse" and _matches(HIT_IN_FUN, line) \
                and not _matches(HIT_IN_FUN_HARD, line) \
                and not _matches(HIT_THE_LAUGH_IS_HIS, line) \
                and not _matches(HIT_WITH_A_THING, line):
            _note(memory, name)
            return _fit(pick(REPLIES["hit_in_fun"], memory), line, name)
        # The workplace answer has the notebook, and an emergency has the card: a threat at work
        # that names a weapon, a killing or being afraid keeps the card.
        if name == "abuse" and _matches(ABUSE_FINE_PLACE, line) \
                and not _matches(VIOLENT_THREAT, line):
            continue
        # A memory of being hurt is not a live threat: "i was abused as a child" and "i was
        # harassed at my old job" are the past, and 999 is not the number for the past. A line
        # that says it is still going on ("and he still does", "it happens every day") keeps it.
        # An old disclosure is not a live emergency, and it is not a shrug either: the abuse card's
        # 999 is wrong for a childhood, and "Got it." is worse than either.
        if name == "abuse" and _matches(ABUSE_MEMORY, line) and not _matches(ABUSE_NOW, line):
            _note(memory, name)
            return _fit(pick(REPLIES["abuse_past"], memory), line, name)
        # The push onto the sofa is play until a hard word is in the line with it.
        if name == "abuse" and _matches(ABUSE_PLAY, line) \
                and not _matches(ABUSE_PLAY_HARD, line):
            continue
        # A son in the kitchen is a family sharing a kitchen, not a person held in one: see
        # ABUSE_ROOM_FAMILY. A fear, a blow, a name called or a way out refused puts the card back,
        # and a partner or an ex was never stood down here in the first place.
        if name == "abuse" and _matches(ABUSE_ROOM_FAMILY, line) \
                and not _matches(ABUSE_ROOM_CARD, line) \
                and not _matches(ABUSE_HANDS_ON, line):
            continue
        # See ABUSE_QUARREL: a row about an ordinary thing, in a room, is a row. A blow word, a
        # fear or a refusal in the same line puts the card back, and "about the knife" is not in
        # the list in the first place.
        if name == "abuse" and _matches(ABUSE_QUARREL, line) \
                and not _matches(ABUSE_BLOW, line) \
                and not _matches(ABUSE_HANDS_ON, line):
            continue
        # A hand on you to hand over a cake, a hug at a family do, a doorway blocked by the
        # hoover: the reason is in the line, so the room and the hand are ordinary.
        # A conversation with a complaint in it is a conversation: see ABUSE_BUTTONHOLED. A blow,
        # a fear or a way out refused keeps the card.
        if name == "abuse" and _matches(ABUSE_BUTTONHOLED, line) \
                and not _matches(ABUSE_BLOW, line) \
                and not _matches(ABUSE_ROOM_CARD, line) \
                and not _matches(ABUSE_HANDS_ON, line):
            continue
        # Small children at home are the reason the door is shut: see ABUSE_KIDS_AT_HOME.
        # A child who will not be put down is the reason you are in the house, so the fear and the
        # blow keep the card and the refusal on its own does not: the refusal is exactly what a
        # toddler is doing. The partner and the ex were never stood down here.
        if name == "abuse" and _matches(ABUSE_KIDS_AT_HOME, line) \
                and not _matches(ABUSE_KIDS_CARD, line) \
                and not _matches(ABUSE_HANDS_ON, line) \
                and not _matches(ABUSE_PARTNER_DID_IT, line):
            continue
        if name == "abuse" and _matches(ABUSE_BENIGN_REASON, line) \
                and not _matches(ABUSE_BLOW, line) \
                and not _matches(ABUSE_PARTNER_DID_IT, line):
            continue
        # An animal did it, and no person in the line also did: the bite readers answer it. A
        # person who attacked the speaker as well keeps the card.
        if name == "abuse" and _matches(ABUSE_FINE_ANIMAL, line) \
                and not PERSON_AS_ATTACKER.search(line):
            continue
        # The lender doing the threatening is not the partner, but a partner in the same line is:
        # a line that names a person keeps the card, whatever else it mentions.
        if (name == "abuse" and _matches(LENDER_FINE, line)
                and not _matches(NAMED_PERSON, line)):
            continue
        # ...and a small child lashing out at all is not a partner doing it: "he bites me" and
        # "he hits me in the face" after a turn about a two year old were the card. A threat, a
        # weapon, a hand round the throat or an adult in the line keeps it, and so does a blow
        # made with a thing or an errand only a grown person has: `he hits me with a belt` and
        # `he hit me because i wouldnt give him money` are not a two year old's (golden-newt,
        # #7433). Both of those arms already exist on main, so this reuses them. A hit in play is
        # stood down before this block, and a line the play answer declines (because it says it
        # was hard) is better off with the child's answer than with the card.
        if (name == "abuse" and _a_small_child_did_it(line, memory)
                and not _matches(ADULT_HIT, line)
                and not _matches(A_REAL_DANGER, line)
                and not _matches(HIT_WITH_A_THING, line)
                and not _matches(ABUSE_CHILD_TAKES_MONEY, line)):
            # Standing the card down is only half an answer: "she bites me" after a turn about a
            # four year old came back as "Thanks for telling me", which is the shrug the card was
            # better than. When the line names no child, the age is in the earlier turn and the
            # arbiter has nothing, so answer the blow itself. A line that names the child is left
            # to the knowledge card, which already says what to do.
            if (A_SMALL_CHILD_LASHES_OUT.search(line)
                    and (not A_SMALL_CHILD_SAID.search(line)
                         # ...and a grandchild always gets it: the knowledge has nothing for the
                         # word, so standing down left "Ugh, that's a lot to carry." where the card
                         # had been, and a shrug is not better than either answer.
                         or A_GRANDCHILD_OF_AN_AGE.search(line))):
                return _fit(pick(SMALL_CHILD_LASH_REPLIES, memory, line), line,
                            "small_child")
            continue
        if name == "self_harm" and accident:
            continue
        # "i could kill myself laughing" is a figure of speech, not a crisis, and neither is
        # "let's end it all and go home". The effort frame - "i nearly killed myself carrying that
        # sofa" - is one of these, and a shrug is no answer to a near thing, so it gets its own
        # line: how are they now, and what to do with a sore back.
        if name == "self_harm" and _idiom(line):
            continue
        # "my nan is going to die" is anticipatory grief: the loss answer has it, not the crisis line.
        # A wish of the speaker's own in the same line is the half that matters, which is what
        # SELF_OWN_DYING says for "so will i", WISH_INTENT for "i feel like ending it", and OWN_WISH
        # for the wish said without those words ("i cant see the point in anything").
        if (name == "self_harm" and _matches(DYING_OTHER, line)
                and not _matches(SELF_OWN_DYING, line)
                and not _matches(DESPAIR + WISH_INTENT, line)
                and not _own_wish(line)):
            continue
        if name == "self_harm" and _matches(END_IT_ALL_JOKE, line):
            continue
        # The shrug after a degree word: "im so embarrassed i might as well die" is a figure of
        # speech, and the same line without the degree ("i might as well die") is not.
        if name == "self_harm" and _matches(WISH_BY_MODAL_OFF, line):
            continue
        if name == "self_harm" and _ending_a_thing(line):
            continue
        # "i overdosed on coffee" is too much of a good thing: neither a packet to keep nor a
        # crisis, so the drink and the box set are left to the ordinary reply.
        if name == "self_harm" and _overdose_of_a_treat(line):
            continue
        # A count of tablets only says "overdose" when the line is not describing the course they
        # are on: "i take 6 tablets a day" is a prescription, "i took 20 paracetamol" is not.
        if name == "poison" and _matches(DOSE_REGULAR, line) and not _matches(
                (r"\btoo\s+many\b", r"\ball\s+(?:of\s+)?(?:my|his|her|their)\b", r"\boverdos\w*",
                 r"\bhandful\b", r"\bwhole\s+(?:packet|pack|box|bottle)\b"), line):
            continue
        # A day's total is the packet's own limit, not an overdose: "i had 8 paracetamol today" and
        # "i had 6 ibuprofen today because of my back" are the most the box allows, spread over a
        # day. Above the maximum, or with a sign in the line, the poisons card keeps the line.
        if name == "poison" and _a_days_dose(line):
            continue
        # An "overdose" of coffee, cake or a box set is how people say too much of a good thing:
        # nothing was taken that anyone can be poisoned by.
        if name == "poison" and _overdose_of_a_treat(line):
            continue
        # A packet that is sealed, out of date or already in the bin is not an overdose.
        if name == "poison" and _matches(PACK_FINE, line) and not _matches(
                (r"\boverdos\w*", r"\btoo\s+many\b", r"\bsweat", r"\bunconscious\b"), line):
            continue
        # A bit of soap or toothpaste is washed away, not a poisoning: the mild answer is the one
        # for it, and only a whole tube or a bottle brings the card back.
        if name == "poison" and _matches(MILD_PRODUCT_SMALL, line) \
                and not (_matches(MILD_TAKEN_BY_A_CHILD, line)
                         and not _matches(MILD_HARMLESS, line)) \
                and (_matches(A_SMALL_AMOUNT, line) or _matches(MILD_HARMLESS, line)) \
                and not _matches(MILD_PRODUCT_BIG, line) \
                and not _matches(FUEL_AND_SOLVENT, line):
            continue
        if name == "self_harm" and _matches(PILLS_OVERDOSE, line) \
                and not _overdose_of_a_treat(line):
            _note(memory, "poison")
            return _fit(pick(REPLIES["poison"], memory), line, "poison")
        # "a seizure of laughter", "a fit of coughing", "i nearly had a fit": the fit is a figure
        # of speech, and a sign that the fit is still going keeps the card.
        if name in ("seizure", "recent_fit") and _matches(SEIZURE_STORY_GUARD, line) \
                and not _matches(FIT_STILL_RINGS, line) and not _matches(ANIMAL, line):
            continue
                # A film, a party or a game with screaming in it is noise, not a neighbour being hurt.
        if name == "heard_assault" and _matches(HEARD_ASSAULT_OFF, line):
            continue
        # "i took the bleach out of the car" is fetching; a swallow verb in the line still counts.
        if name == "poison" and _matches(TOOK_OUT_OF, line) \
                and not _matches(POISON_SWALLOW_VERB, line):
            continue
        # A risotto, a punnet from the shop or the wild garlic in a pesto is food that was chosen,
        # and mushrooms somebody is still growing or naming are not in anybody's mouth.
        if name == "foraged" and _matches(FORAGED_FINE, line):
            continue
        # A cold sore, chapped lips or a new piercing swells too, and a line about last summer is a
        # story; neither is anaphylaxis.
        # A sign named, or a reaction already over, is another card's: this one is only for the
        # line that says "a reaction" and stops there.
        if name == "allergy_now" and (hypothetical or _matches(ALLERGY_SIGN_NAMED, line)):
            continue
        # A tick the person has already found and taken off has its own answer; this card is for
        # the bite and the one still attached.
        if name == "tick_bite" and _matches(TICK_ALREADY, line):
            continue
        if name == "lips_swell" and _matches(LIPS_SWELL_OFF, line):
            continue
        # A cold sore, a bitten lip, a piercing and "what if my lips swell" are not a swelling that
        # is happening now.
        if name == "lips_swell_bare" and _matches(LIPS_SWELL_BARE_OFF, line):
            continue
        # A sting the person says has settled, or one from a nettle or a gnat, is not an airway
        # closing: the swelling and the breath still are, so those keep the ambulance.
        if (name in ("lips_swell_bare", "lips_tingle") and not _matches(SWELLING_NOW, line)
                and not _matches(AIRWAY_CHANGED, line)
                and (_matches(STING_SETTLED, line)
                     or (_matches(STING_MILD, line) and not _matches(STING_WINGED, line)))):
            continue
        # The tingle in the mouth needs the food, the sting or a reaction in the line; with a
        # swelling, a faint or a wheeze it is the ambulance card instead.
        if name == "lips_tingle":
            # The dentist, the cold, a panic attack and pins and needles that are in the hands as
            # well as the mouth explain a tingle on their own. A swelling, a swallow that is going
            # or a breath that is wrong keeps the card whatever else is in the line.
            if (_matches(LIPS_TINGLE_OFF, line) and not _matches(LIPS_TINGLE_BREATH, line)
                    and not _matches(SWELLING_NOW, line)):
                continue
            # A tongue or a throat that has gone thick next to the tingle is the airway even when
            # nothing in the line names a cause.
            if (_matches(THROAT_THICK, line) and _matches(MOUTH_TINGLE, line)
                    and not _matches(LIPS_TINGLE_OFF, line)):
                return _fit(pick(REPLIES["lips_swell_bare"], memory), line, "lips_swell")
            # The food, the sting or a reaction names the cause; a faint or a swelling is the
            # sign on its own, with no cause needed.
            if (_matches(SPICY_MOUTH, line) and not _matches(LIPS_TINGLE_BREATH, line)
                    and not _matches(SWELLING_NOW, line)):
                continue
            # A tingle with no cause at all is the commonest shape of all ("my lips are
            # tingling", "my tongue is tingling", "my lips are numb") and it was the listening
            # line. It is not the food card, which has nothing to stop eating here, and it is not
            # nothing: the answer says what it usually is and what change means 999.
            # ...and a lip that has gone numb, or a tingle that is in the hands as well, is a
            # nerve sign or a limb: neither is this card.
            if (_matches(LIPS_NUMB, line) and not _matches(LIPS_TINGLE_SAID, line)
                    and not _matches(SWELLING_NOW, line)):
                continue
            # ...but a sting, a nut or a reaction in the line is the cause, and a lips tingle
            # after a bee sting is the airway being watched whatever the hand is doing.
            if (_matches(LIPS_LIMB_TOO, line) and not _matches(LIPS_TINGLE_BREATH, line)
                    and not _matches(LIPS_TINGLE_TRIGGER, line)):
                continue
            if (not (_matches(LIPS_TINGLE_TRIGGER, line) or _matches(LIPS_TINGLE_RED, line)
                     or _matches(LIPS_TINGLE_FOOD, line))
                    and _matches(LIPS_TINGLE_MOUTH, line)
                    and not _matches(LIPS_TINGLE_ELSEWHERE, line)):
                _note(memory, "general")
                return _fit(pick(REPLIES["lips_tingle_alone"], memory), line, "lips_swell")
            if not (_matches(LIPS_TINGLE_TRIGGER, line) or _matches(LIPS_TINGLE_RED, line)
                    or _matches(LIPS_TINGLE_FOOD, line)):
                continue
            if _matches(LIPS_TINGLE_RED, line):
                return _fit(pick(REPLIES["lips_swell_bare"], memory), line, "lips_swell")
            _note(memory, "general")
            return _fit(pick(REPLIES["lips_tingle"], memory), line, "lips_swell")
        # A swelling or a rash after something eaten names its food, and the food can be any food:
        # "my baby has a swollen lip after eating egg" was the omelette recipe. A cold, chapped
        # lips or a bitten lip are swellings too, so those stand down; an airway sign, or a lip
        # that swelled after a sting, is the ambulance card.
        if name == "allergy_food":
            if _matches(ALLERGY_OFF, line) and not _matches(ALLERGY_AIRWAY, line):
                continue
            sting = _matches(STING_WORDS, line) and not _matches(FOOD_WORDS, line)
            if _matches(ALLERGY_AIRWAY, line) or (sting and _matches(ALLERGY_FACE, line)):
                _note(memory, "lips_swell")
                return _fit(pick(REPLIES["lips_swell_bare"], memory), line, "lips_swell")
            kind = "sting_watch" if sting else "allergy_watch"
            _note(memory, kind)
            return _fit(pick(REPLIES[kind], memory), line, kind)
        # A throat that only feels tight is the same-day arm below, not the ambulance: the swelling
        # arms were taking "my throat feels tight" as anaphylaxis with nothing else in the line.
        if name in ("lips_swell", "lips_swell_bare") and _matches(
                THROAT_TIGHT, line) and not _matches(THROAT_TIGHT_RED, line):
            continue
        # A sore throat with a swollen gland, a throat that feels tight when you are nervous, and
        # "a bit puffy": the swelling arm was taking all three as anaphylaxis.
        if name in ("lips_swell", "lips_swell_bare") and _matches(
                THROAT_TIGHT_MILD, line) and not _matches(THROAT_TIGHT_RED, line):
            continue
        # A tight throat with no swelling, no trigger and no other sign is a same-day call, not the
        # ambulance: the mild reasons and anything red have already had their turn above.
        if name == "throat_tight":
            if _matches(THROAT_TIGHT_CAUSE, line) and not _matches(THROAT_TIGHT_RED, line):
                # Effort has its own answer: a throat that tightens on a run is the cold air and
                # the breathing, not a same-day appointment for nothing.
                if _matches(THROAT_TIGHT_EFFORT, line):
                    _note(memory, "general")
                    return _fit(pick(REPLIES["throat_exertion"], memory), line, "throat_tight")
                continue
            _note(memory, "general")
            return _fit(pick(REPLIES["throat_tight"], memory), line, "throat_tight")
        # A swallow that has gone is urgent the same day, and the airway signs beside it are the
        # 999 card: drooling, a muffled voice, a lip or a tongue that is swelling, the breath.
        if name == "swallow_gone":
            if _matches(SWALLOW_GONE_OFF, line) or _matches(SWALLOW_GONE_BREATH, line):
                continue
            if _matches(SWALLOW_GONE_RED, line):
                _note(memory, "general")
                return _fit(pick(REPLIES["lips_swell_bare"], memory), line, "lips_swell")
            _note(memory, "general")
            return _fit(pick(REPLIES["swallow_gone"], memory), line, "swallow_gone")
        # "i ran for the bus and im gasping for air" is the effort rather than the lungs.
        if name in ("breathing", "breath_weeks", "breath_past") and _matches(BREATH_EFFORT, line) \
                and not _matches(BREATH_EFFORT_RED, line):
            continue
        # "my friend was spiked with too much chilli sauce" is dinner, and an evening years ago is a
        # memory rather than a night out to look after.
        if name == "spiked" and _matches(SPIKED_STAND_DOWN, line):
            continue
        # A fall that ended fine is a story, and "he fell asleep" was never a fall: the hip arm obeys
        # the same two guards the older-fall arm does.
        # A fall and then confusion or a knock-out is the bang-on-the-head card, not this one: that
        # card is asked after this loop, so "my dad fell and he isnt making sense" got the bruising
        # question here and never reached it. The older-fall arm stands down the same way.
        if name == "fall_check" and _matches(HEAD_BANG, line):
            continue
        # A fall and then a stroke sign is the 999 stroke call, not the bruising question: "my dad
        # fell and now his speech is slurred" was asked "is it just bruising?" on main. The stroke
        # row is read further down the list, so this stands the fall row down and lets it.
        if name == "fall_check" and _matches(FALL_STROKE_SIGN, line) \
                and not _matches(SLUR_NOT_A_STROKE_WORDS, line):
            continue
        if name == "fall_check" and _fall_with_sign(line):
            continue
        if name == "fall_check" and (_matches(HEAD_KNOCKOUT, line)
                                     or _out_cold_knockout(line)):
            continue
        # The questions this card asks have already been answered: a person not breathing, not
        # responding or unresponsive after a fall is a 999 call, whatever else the line says, and
        # "can they get up?" is the wrong thing to read out to them.
        if name == "fall_check" and _matches(FALL_ANSWERED, line):
            if _matches(FALL_NOT_BREATHING, line):
                return _fit(pick(REPLIES["not_breathing"], memory), line, "not_breathing")
            _note(memory, "general")
            return _fit(pick(REPLIES["unconscious"], memory), line, "unconscious")
        # A fall that already says how it went (an injury, a red sign, a story, a joke) belongs to
        # another arm, so the two-questions card only takes the bare ones.
        # A baby off a bed or a sofa is the same-day check whatever else is on the line, so the
        # two-questions card stands down for it: "the baby fell off the bed" is not a bruise. A
        # baby who fell over on the rug, went to sleep or dropped a dummy did not fall off anything,
        # so the bruise question is still the answer for that one.
        if name == "fall_check" and _matches(BABY_FELL, line) \
                and not (_matches(BABY_FELL_OFF, line) or _matches(BABY_FELL_OVER, line)):
            continue
        if name == "fall_check" and (_matches(FALL_CHECK_OFF, line) or _matches(FALL_RED, line)
                                     or _matches(FALL_PAST, line) or _matches(FALL_FINE, line)
                                     or re.search(r"\b(?:hurt|broke|broken|fractur\w*|hip|head|"
                                                  r"back|neck|blood|bleed\w*|cut|hospital|"
                                                  r"ambulance|get\s+up|weight|dizzy|sick|"
                                                  # "i fell and im confused about what to cook" is
                                                  # the recipe, not a bang on the head.
                                                  r"confus\w*|"
                                                  # "my dad fell and he isnt making sense" is
                                                  # the head-injury call, not a bruise question.
                                                  # "i cant lift her" is the helper saying the
                                                  # person cannot get up.
                                                  r"making\s+sense|lift|talking\s+(?:rubbish|"
                                                  r"nonsense|gibberish)|not\s+(?:him|her|them)s"
                                                  r"elf|not\s+(?:him|her|them)selves|"
                                                  r"swell\w*|swollen|sore|bruise\w*|stiff|"
                                                  r"sprain\w*|twisted|turned\s+over|"
                                                  r"grazed|scraped|ache\w*|teeth|tooth|dentist)\b",
                                                  line)):
            continue
        if name == "fall_hip" and _matches(OLD_FALL_FINE, line):
            continue
        if name == "fall_hip" and _matches(OLD_FALL_NOT, line):
            continue
        # A hip that is said to be broken is an ambulance, not an X-ray today: the older arm already
        # says so, and "my gran fell and broke her hip" must not come down to 111.
        if name == "fall_hip" and re.search(r"\b(?:broke|broken|fractur\w*|snapped)\b", line):
            continue
        # A line naming a sport keeps the exercise answer, even with the breathlessness in it.
        if name == "breath_rest" and _matches(BREATH_SPORT, line):
            continue
        # Lying flat or waking breathless is the night card's same-day 111, unless a red flag is in
        # the line: the rest-at-once answer was taking "i get breathless lying flat" as 999.
        if name == "breath_rest" and _matches(NIGHT_BREATH, line) \
                and not _matches(NIGHT_BREATH_RED, line):
            continue
        # A jab, a paintball, a photo and a shot of whisky are not gunshots.
        if name == "shot" and _matches(SHOT_FINE, line):
            continue
        # Fumes that make the eyes water, a bottle on a shelf and a cleaning day are not a splash.
        if name == "eye_chem" and _matches(EYE_FINE, line):
            continue
        # A chicken bone, a dog and an x-ray are not a limb with the bone out through the skin.
        if name == "bone_out" and _matches(BONE_FINE, line):
            continue
        # The sudden headache is bad *and* out of nowhere; "the worst of my life" says both.
        if name == "headache" and not (_matches(HEADACHE_SUDDEN, line)
                                       or _matches(HEADACHE_WORST_EVER, line)):
            continue
        if name == "headache" and not _matches(HEADACHE_BAD, line):
            continue
        if name == "headache" and _matches(HEADACHE_STORY, line):
            continue
        # Blood in a film, or in a story from last year, is not blood now.
        if name in ("cough_blood", "vomit_blood") and _matches(COUGH_FINE, line):
            continue
        # A cat coughing up blood is the vet's, and it is answered just above.
        if name in ("cough_blood", "vomit_blood") and _matches(ANIMAL, line) and not _matches(
                HUMAN_TOO, line):
            continue
        if name in ("cough_blood", "vomit_blood"):
            key = name if _person(line) else name + "_self"
            return _fit(pick(REPLIES[key], memory), line, name)
        # Iron tablets, black pudding and a poo from years ago are not a bleed happening now.
        if name in ("poo_blood", "poo_black") and _matches(POO_FINE, line):
            continue
        # "there is blood in my pants" is a period, not a poo: only a line that names a poo gets
        # the stool card.
        if name in ("poo_blood", "poo_black") and _matches(POO_PANTS, line) and not _matches(
                POO_WORD, line):
            continue
        # A curry, a takeaway or a hot sauce explains a red poo for a day, as long as the line says
        # nothing about being faint, weak or heavy with it.
        if name in ("poo_blood", "poo_black") and _matches(POO_MEAL, line) and not _matches(
                POO_RED, line):
            continue
        # Blood that has been there for weeks or months is the GP's, not the ambulance's: the reply
        # has to agree with the line it is answering.
        if name in ("poo_blood", "poo_black") and _matches(STOOL_LONG, line) and not _matches(
                POO_RED, line):
            key = name + "_long" if _person(line) else name + "_long_self"
            return _fit(pick(REPLIES[key], memory), line, name)
        # Itching, chafing and the ache after a long ride are the ordinary testicle lines.
        if name == "torsion" and _matches(TORSION_FINE, line):
            continue
        # A dog with a swollen testicle needs the vet, not a person's A&E: the line has to name a
        # person for the human answer to be right.
        if name == "torsion" and _matches(ANIMAL, line) and not _matches(HUMAN_TOO, line):
            continue
        # A lump, or one side bigger, is the two-week GP referral: it is not the twist, so it does
        # not get the reply that tells the person their pain came on suddenly.
        if (name == "torsion" and _matches(TESTIS_LUMP, line)
                and not _matches(TORSION_ONSET, line)
                and not _matches(TORSION_RED, line)):
            key = "torsion_lump" if _person(line) else "torsion_lump_self"
            return _fit(pick(REPLIES[key], memory), line, name)
        # A torsion is sudden, so an ache with no onset and no swelling, lump or twist is the
        # ordinary one: "my balls ache a bit" is not a reason to send somebody to A&E.
        if (name == "torsion" and not _matches(TORSION_HARD, line)
                and not _matches(TORSION_ONSET, line)
                and not (_matches(TORSION_SICK, line) and not _matches(TORSION_MILD, line))):
            continue
        # The same line said with a duration: a swelling of a week is seen today, and the reply must
        # not tell them their pain came on suddenly when their own line says otherwise.
        if name == "torsion" and _matches(TORSION_LONG, line) and not _matches(TORSION_RED, line):
            key = "torsion_long" if _person(line) else "torsion_long_self"
            return _fit(pick(REPLIES[key], memory), line, name)
        if name in ("poo_blood", "poo_black", "torsion"):
            # The words have to match the line: "say the pain came on suddenly" is wrong on a line
            # that only says swollen, so that wording is kept for the lines that said it.
            if name == "torsion" and not _matches(TORSION_ONSET, line):
                key = "torsion_hard" if _person(line) else "torsion_hard_self"
            else:
                key = name if _person(line) else name + "_self"
            return _fit(pick(REPLIES[key], memory), line, name)
        # Gas you can only smell on your hands or your clothes is not a leak in the building.
        if name == "gas_smell" and _matches(GAS_ON_YOU, line) and not _matches(GAS_IN_ROOM, line):
            continue
        # A gas smell from last year, or at somebody else's flat, is a story rather than a leak.
        if name == "gas_smell" and _matches(GAS_PAST, line) and not _matches(GAS_NOW, line):
            continue
        # The child-tuned arms are about a person: a dog with sepsis or a cat with a temperature is
        # the vet's, and the line has to name a person for the human answer to be right.
        # "i think my dog has sepsis" is still the dog: the bare "i" in HUMAN_ANCHOR is why this
        # asks HUMAN_TOO, which wants a person to be the one who is ill.
        if name in ("named_illness", "high_temp", "child_drank", "recent_fit", "grunting_baby",
                    "sleepy_feed", "fever_rash") and _matches(PET_WORDS, line) and not _matches(
                HUMAN_TOO, line):
            continue
        # A fit that has just happened has its own answer, which says what to tell the handler and
        # to lie them on their side: it is a better first minute than the generic fit reply.
        # The faint with a cause in the line keeps the composer's faint card; the blackout that
        # came from effort, from the heart or from the floor is this card, and it is the person's
        # own card only when the line is about the person typing.
        if name == "blackout":
            if _matches(BLACKOUT_A_THING, line):
                continue
            urgent = _matches(BLACKOUT_URGENT, line) or _matches(BLACKOUT_STILL_DOWN, line)
            # The composer's faint card and its child-faint card are good answers and they own the
            # lines with a cause in them, and a child who has come round is the same-day check it
            # already gives. This card is only for the blackout that is a collapse.
            if _matches(BLACKOUT_OFF, line) and not _matches(BLACKOUT_HEART, line):
                continue
            if _matches(CHILD_ANON, line) and not urgent:
                continue
            if _person(line) or _matches(OTHER_BODY, line):
                # Somebody who has not come round belongs to the unconscious case below, which says
                # "keep him on his side" in the right words; this card is for the person who went
                # down and came back, where "check they're breathing" is the only advice left.
                if not urgent or _matches(UNCONSCIOUS, line):
                    continue
                key = "blackout_other"
            elif urgent:
                key = "blackout_self"
            elif _matches(BLACKOUT_REPEAT, line):
                key = "blackout_today"
            else:
                continue
            _note(memory, name)
            return _fit(pick(REPLIES[key], memory), line, name)
        if name == "seizure" and _matches(RECENT_FIT, line) and not _matches(RECENT_FIT_FINE, line):
            continue
        # "i nearly drowned laughing" and "i was drowning in paperwork" are figures of speech: the
        # water is not water, so the drowning case stands down and the line keeps its own answer.
        if name == "drowning" and _matches(DROWNING_HYPERBOLE, line) \
                and not _matches(WATER_DANGER, line):
            continue
        # A dog having a fit of sneezing is the vet's, and it is picked up by the pet case.
        if name == "seizure" and _matches(SEIZURE_FIGURATIVE, line) and not _matches(ANIMAL, line):
            continue
        # The fits a child has every few months are epilepsy the GP already knows about, and a
        # laptop that had a fit is a laptop: neither is a body on the floor tonight.
        if name == "seizure" and not _matches(FIT_STILL_RINGS, line) and (
                _matches(FIT_ROUTINE, line) or _matches(THING_FIT_SUBJECT, line)):
            continue
        # The arm of a pair of glasses and the leg of a chair are bent all the time, and nothing in
        # that line is a person: only the limb-at-an-angle rule can be about a thing, so the line is
        # let go when that is the only fall rule it trips and the limb belongs to an object.
        if (name == "fall" and _matches(LIMB_AT_AN_ANGLE, line)
                and not _matches(FALL_CORE, line) and _matches(LIMB_IS_A_THING, line)
                # ...and only while the person's own limb is not at an angle in the same line:
                # a trouser leg and a knee are bent in the same sentence more often than not.
                and not _matches(OWN_LIMB_AT_AN_ANGLE, _without_object_limbs(line))):
            continue
        # A fall that ended fine is a story: "my dad fell off a ladder but hes ok".
        if name == "fall" and _matches(FALL_FINE, line) and not _matches(FALL_RED, line):
            continue
        if name == "fall" and _matches(FALL_PAST, line) and not _matches(FALL_NOW, line):
            continue
        # The second, third or fourth fall is a pattern question with an answer of its own: the
        # GP's falls review, the medicines, the house. It is not "stay where you are and ring
        # 999", which is what the stairs arm said to "i keep falling down the stairs". A line
        # that puts somebody on the floor now, or that names an injury, keeps the card.
        if (name == "fall" and _matches(FALL_REPEAT, line)
                and not _fall_with_sign(line)
                and not _matches(FALL_NOW, line) and not _matches(FALL_RED, line)
                and not _matches(FALL_PATTERN_HURT, line)):
            key = "fall_pattern_self" if _matches((r"\bi\b", r"\bwe\b"), line) and not _person(
                line) else "fall_pattern"
            return _fit(pick(REPLIES[key], memory), line, "fall_pattern")
        if name == "fall" and _matches(NEAR_MISS, line) and not _matches(NEAR_MISS_HARM, line):
            continue
        # The cat fell off the balcony is the vet's, and it is being answered just above.
        if name == "fall" and _matches(PET_FELL, line) and not _matches(HUMAN_TOO, line):
            continue
        # "confused about the homework" is not a confused person: sepsis is about the patient.
        if name == "sepsis_signs" and _matches(CONFUSED_THING, line) and not _matches(
                (r"\bdrows\w*", r"\bfloppy\b", r"\blimp\b", r"\bunrespons\w*",
                 r"\bwon'?t\s+wake\b", r"\bvery\s+sleepy\b"), line):
            continue
        if name == "red_flags":
            # A mark on an arm that does not fade is a doctor-today question; the meningitis rash
            # has a fever or a child or "everywhere" in the line with it, or in the turn before.
            flat = _matches(RASH_FLAT, line) or _glass_test_line(line, before)
            company = _matches(RASH_COMPANY, line) or _matches(RASH_COMPANY, before)
            if _matches(RASH_DEFINITION, line):
                continue
            if flat and not company and not _matches(RASH_NAMED, line) \
                    and not _matches(RASH_NAMED, before) \
                    and not _matches(RASH_PRESSED, line):
                continue
        # A stiff neck from sleeping on it, or from the gym, is the answer people get most often.
        if name == "stiff_neck" and _matches(STIFF_FINE, line) and not _matches(RASH_RED, line):
            continue
        # An oven, a boiler and a hot tap have a temperature too, and they are never drowsy.
        if name in ("sepsis_signs", "newborn_fever", "newborn_fever_next") and not _matches(
                RED_ANCHOR, line):
            continue
        if name == "newborn_fever" and _matches(DEVICE_OLD, line):
            continue
        if name in ("sepsis_signs", "newborn_fever", "newborn_fever_next") and _matches(DEVICE_TEMP, line) and not _matches(
                (r"\bfever\w*", r"\bfeverish\b", r"\bburning\s+up\b", r"\bhot\s+to\s+touch\b",
                 r"\b\d{2}(?:\.\d)?\s*(?:c\b|degrees)"), line):
            continue
        # A pale child with a red sign is the ambulance, and the red list is the fence on the whole
        # arm, not just on the effort branch: `my son is pale and limp` and `...clammy and wont
        # wake up` are 999 on main and were "going downhill, ring 111" with the pale-child row.
        # A red sign on a pale child is an ambulance, not the 111 card and not nothing: the row
        # used to skip the child entirely, and "my son is mottled and cold" fell through to the
        # cold-in-a-child answer. The rows above catch most of these; this is the belt.
        if name == "pale_child" and _matches(PALE_EFFORT_RED, line):
            # The signs that are a whole 999 answer of their own - floppy, wont wake, not
            # breathing fast and blue - keep the row above; the colour words are the ones that
            # had nothing behind them, and they are what this card is for.
            if _matches(PALE_OTHER_RED, line):
                continue
            _note(memory, "pale_child")
            return _fit(pick(REPLIES["pale_child_now"], memory), line, "pale_child")
        # A child who is pale and sweaty because they have been playing football is hot, not
        # shocked: the effort words take the heat answer instead of the downhill one, unless a
        # red sign is in the line too.
        if name == "pale_child" and _matches(PALE_EFFORT, line) and not _matches(
                PALE_EFFORT_RED, line) and (
                _matches(PALE_EFFORT_REAL, line) or not _matches(PALE_EFFORT_NO, line)):
            _note(memory, "pale_child")
            said = "pale_child_heat" if _matches(PALE_HEAT, line) else "pale_child_effort"
            return _fit(pick(REPLIES[said], memory), line, "pale_child")
        # The grown-up colour row. A child in the line is the child's row above; hands and feet on
        # their own are nerves; the heat, the effort, a hangover, a needle or a fever that already
        # has an answer all explain the colour, so this row passes and they keep their own reply.
        if name == "pale_adult" and (
                _matches(CHILD_WORD, line) or _matches(PALE_ADULT_FINE, line)
                or (_matches(PALE_ADULT_ITSELF, line)
                    and not _matches(PALE_ADULT_WHOLE, line))):
            continue
        # At the gym, in the sun, straight after a run: the colour is the effort, and this is the
        # cooling answer rather than the ambulance.
        if name == "pale_adult" and _matches(PALE_EFFORT, line) and not _matches(
                PALE_EFFORT_RED, line):
            _note(memory, "pale_adult")
            return _fit(pick(REPLIES["pale_adult_effort"], memory), line, "pale_adult")
        # Whose colour it is decides whose advice it is: the speaker gets "sit down", somebody
        # else gets "sit them down".
        if name == "pale_adult":
            said = "pale_adult" if _matches(ADULT_PERSON, line) else "pale_adult_self"
            _note(memory, said)
            return _fit(pick(REPLIES[said], memory), line, "pale_adult")
        # Three months old and over is a doctor-today question, not this call.
        if name == "newborn_fever" and _matches(NEWBORN_FINE, line) and not _matches(
                SEPSIS_SIGN, line):
            continue
        # A rash, a confused homework question and a child who is eating and playing all have a
        # better answer than this one.
        if name == "child_fever" and _matches(
                (r"\bhad\s+(?:a\s+|an\s+|the\s+)?(?:temperature|temp|fever|high\s+temperature)\b",
                 r"\bwas\s+(?:ill|poorly|unwell|sick)\s+(?:with|from)\s+(?:a\s+)?(?:temperature|"
                 r"temp|fever)\b"), line) and not _matches((r"\bhas\s+had\b", r"\bfor\s+(?:\d+|"
                 r"two|three|four|five|six|seven)\s+days?\b"), line):
            continue
        # A child who is burning up is the fever call, unless the sun or the heat is the cause -
        # and a fever word brings it back even then.
        if (name == "heat" and _matches((CHILD_WORD,), line)
                and _matches((r"\bburning\s+up\b", r"\bfeels?\s+(?:hot|feverish)\b",
                              r"\bboiling\s+hot\b", r"\bhot\s+to\s+(?:the\s+)?touch\b",
                              r"\bhot\s+and\s+(?:shivery|clammy|sweaty|floppy|miserable)\b",
                              r"\b(?:really|very|so)\s+hot\b"), line)
                and (not _matches((r"\bsun\b", r"\bheat\b", r"\bheatwave\b", r"\bcar\b",
                                   r"\bhot\s+(?:car|room|day|weather)\b", r"\boutdoors?\b",
                                   r"\bpark\b", r"\bbeach\b", r"\bafternoon\b", r"\bweather\b",
                                   r"\bafter\s+(?:football|rugby|sport|training|a\s+run|pe)\b"),
                                  line)
                     or _matches((r"\b(?:temperature|temp|fever|feverish)\b",), line))):
            continue
        # A disease with the word in its name is not a temperature reading. "my daughter has
        # glandular fever" and "scarlet fever" are named infections with their own cards, and a
        # line with no reading, no "hot" and no "temperature" besides the name is not a child to
        # ring 111 about today. A real temperature beside the name keeps the card, because the
        # fever word then survives the name being taken out.
        if name in FEVER_HOME_CARE and _the_only_fever_is_a_disease_name(line) and not _matches(
                SEPSIS_SIGN, line):
            continue
        if name == "child_fever" and _matches(FEVER_ASK, line) and not _matches(
                FEVER_REPORT, line):
            continue
        # A twelve-year-old with a temperature is not the small child this card is written about.
        if name == "child_fever" and _matches(CHILD_GROWN, line) and not _matches(SEPSIS_SIGN, line):
            continue
        # Neither is a school-age child with a fever and nothing else wrong: "my 6 year old has a
        # temperature of 38 and a cough" was "Ring 111 or your GP today", which is not what anyone
        # is told to do for a child who is otherwise well (honey-bat and urban-orange, 87725/87789).
        if (name == "child_fever" and _matches(CHILD_SCHOOL_AGE, line)
                and not _matches(CHILD_FEVER_RED, line) and not _matches(SEPSIS_SIGN, line)):
            continue
        if name == "child_fever" and _matches(CONFUSED_THING, line):
            continue
        if name == "child_fever" and _matches((RASH,), line) and not _matches(SEPSIS_SIGN, line):
            continue
        if name == "child_fever" and _matches(
                (r"\b(?:eating|drinking|playing|chatty|cheerful|happy|himself|herself|themselves|"
                 r"running\s+about|full\s+of\s+beans|fine|better|improving)\b",
                 r"\bno\s+other\s+symptoms\b"), line) and not _matches(SEPSIS_SIGN, line) \
                and not _matches(CHILD_FEVER_NOT_EATING, line):
            continue
        # A young baby's temperature on its own is urgent because of the age, and the answer is
        # undress-and-feed rather than the sepsis glass test.
        if name == "newborn_fever" and not _matches(
                RASH_RED + STIFF_NECK + SEPSIS_SIGN + (r"\bblue\b", r"\bbreathing\s+fast\b"), line):
            return _fit(pick(REPLIES["newborn_temp"], memory), line, "newborn_temp")
        # A child on the way back up, or one whose temperature was last week, is a story - unless
        # the line says the fever is running now: "my sons got a temp of 39 since last nite" names
        # last night, and once the misspelling is repaired that read as history and lost the call.
        if name == "child_fever" and _matches(
                (r"\blast\s+(?:week|month|year|night|time)\b", r"\bweeks?\s+ago\b",
                 r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+days?\s+ago\b",
                 r"\bused\s+to\b", r"\bback\s+to\s+(?:normal|"
                 r"himself|herself|school|nursery)\b", r"\bover\s+it\b", r"\bfully\s+better\b"),
                line) and not _matches(FEVER_STILL_NOW, line):
            continue
        if name == "child_fever" and _matches(PET_WORDS, line) and not _matches(HUMAN_TOO, line):
            continue
        # The tiny baby's fever said in the line after the age. The memory carries the age, and
        # this line only has to be about the baby: an age here that is old enough settles it, the
        # speaker's own temperature is an adult's line, and a line that names somebody else (a
        # grandmother, a neighbour) is not the three-week-old.
        if name == "newborn_fever_next" and not _tiny_baby(memory):
            continue
        # The age came in an earlier line and it is five weeks or more: a plain "she feels hot"
        # with no number is the same-day card for that baby, as it is when the age is in the line,
        # and only a stated strong heat is the hospital call. (see TRUE_NEWBORN)
        if name == "newborn_fever_next" and not (
                _matches(BABY_BURNING, line) or _matches(FEVER_SIGN, line)) and not (
                _true_newborn(memory)):
            continue
        if name == "newborn_fever_next" and (_matches(NEWBORN, line) or _matches(
                TINY_AGE_FINE, line)):
            continue
        # A brother or sister named with years is not the baby in the window. (lively-notebook)
        if name == "newborn_fever_next" and _matches(OLDER_CHILD_NAMED, line):
            continue
        if name == "newborn_fever_next" and _matches(ABOUT_THE_SPEAKER, line) and not _matches(
                PERSON_WORD, line):
            continue
        if name == "newborn_fever_next" and _matches(PERSON_WORD, line) and not _matches(
                TINY_SAID, line):
            continue
        if name == "newborn_fever_next" and _matches(PET_WORDS, line) and not _matches(
                HUMAN_TOO, line):
            continue
        # The age in memory belongs to one child and the fever in this line can belong to another:
        # "my baby is 3 weeks old" then "my toddler has a fever" is the toddler's card.
        if name == "newborn_fever_next" and _matches(
                (r"\btoddlers?\b", r"\bkids?\b", r"\bchildren\b", r"\bchild\b"), line):
            continue
        # The age is in memory and this line only says the baby is hot: the answer is the newborn
        # card, not the sepsis glass test. Without this the reply dispatch aliases the line to the
        # red flags, and "don't let her drive" lands on a three-week-old.
        if name == "newborn_fever_next" and not _matches(
                RASH_RED + STIFF_NECK + SEPSIS_SIGN + (r"\bblue\b", r"\bbreathing\s+fast\b"), line):
            return _fit(pick(REPLIES["newborn_temp"], memory), line, "newborn_temp")
        # A child already being treated for it, or one who had it years ago, is a story.
        if name == "named_illness" and _matches(NAMED_SICK_FINE, line) and not _matches(
                SEPSIS_SIGN + (r"\bfever\w*", r"\brash\w*", r"\bstiff\s+neck\b"), line):
            continue
        # A fit every few months is the condition the family already manages; a fit of coughing
        # is not a fit. A temperature of 40 is a number, not a how-to.
        if name == "recent_fit" and _matches(RECENT_FIT_FINE, line):
            continue
        # A grunt in the cot is a noise; a grunt with a working chest or a floppy baby is not.
        if name == "grunting_baby" and _matches(GRUNTING_FINE, line) and not _matches(
                GRUNTING_NOW, line):
            continue
        # A heat rash, a nappy rash or chickenpox is the everyday reason for a spot with a fever.
        if name == "fever_rash" and _matches(FEVER_RASH_FINE, line):
            continue
        # ...and the same everyday rashes stand the headache pair down. A cat with a rash is the
        # vet's, and it was being answered by the meningitis card.
        if name == "rash_headache" and (_matches(FEVER_RASH_FINE, line)
                                        or _matches(RASH_HEADACHE_FINE, line)):
            continue
        if name == "rash_headache" and _matches(PET_WORDS, line) and not _matches(HUMAN_TOO, line):
            continue
        # A phone that is warm while charging, a flat battery and a frayed lead are questions
        # about a thing; a blue mood and a blue dress are not a person short of oxygen.
        # A swollen battery that is smoking or hot is the fire card, not the tip about the bin.
        if name == "battery_bulge" and _matches(
                (r"\bsmok", r"\bspark", r"\bflames?\b", r"\bon\s+fire\b", r"\bcaught\s+fire\b",
                 r"\bsmell", r"\bhot\s+to\s+touch\b", r"\bmelt"), line):
            continue
        if name == "electric_burn" and _matches(ELECTRIC_FINE, line) and not _matches(
                (r"\bsmell", r"\bsmoke", r"\bmelt", r"\bspark", r"\bbulging", r"\bflames?\b"), line):
            continue
        # A pet whose gums have gone grey or blue is the vet's case, and the pet table answers
        # that one in the pet's own words: "my puppies gums look grey" was getting the 999 card.
        if (name == "blue" and _matches(PET_ANY, line) and not _matches(HUMAN_TOO, line)
                and _matches(PET_MOUTH, line)):
            continue
        # Any other pet whose colour changes is a vet now, not a person short of oxygen - and it
        # must not fall through to "Noted: your dog is going blue." or to the laundry answer. The
        # change has to be said or shown on a body part, so a blue collar or a blue bowl stays a
        # question about a thing.
        if (name == "blue" and _matches(PET_ANY, line) and not _matches(HUMAN_TOO, line)
                and (_matches(BLUE_CHANGE + PET_BLUE_WENT, line) or _matches(PET_BLUE_PART, line))):
            return _fit(pick(REPLIES["pet_emergency"], memory), line, "pet_emergency")
        # The colour card is about a body short of oxygen. A phone, a pan, a pickle or a laptop that
        # went blue is a screen, a kitchen or an electrical question, and main sent every one of
        # them to 999. Only a body part, a person, or a person as the subject of the change keeps it.
        if name == "blue" and not _matches(BLUE_HUMAN, line):
            continue
        # "Grey" is a hair colour before it is cyanosis. The person-side alternative in BLUE only
        # needs a subject and a colour change, so "im going grey", "why am i going grey" and "my
        # husband is going grey" were all told that a colour change is a 999 call - and every one
        # of them was the grey-hair answer's line. A hair word settles it; without one, a bare
        # grey with no body part, no blue and none of the signs of a real shut-down is hair by
        # default. A grey that names a body part - grey lips, a grey face, grey fingertips, grey
        # gums - is still the card, and so is "he went grey and clammy" or "she went grey and
        # passed out", because those are the signs the card exists for.
        if (name == "blue" and not _matches(GREY_ALARM, line)
                and not _matches(BLUE_LIPS_FACE, line)
                and not _matches(BLUE_TINGE, line)
                and (_matches(GREY_HAIR, line)
                     or (_matches(GREY_ARRIVING, line)
                         and not _matches(GREY_BODY, line))
                     or (_matches(GREY_COLOUR, line)
                         and not _matches(GREY_BODY, line)
                         and not _matches(BLUE_HUMAN, line)
                         and not _matches(GREY_SELF, line)))):
            continue
        # Cold hands, a blue tongue from a slushie, dye on the skin: the colour of a thing, or of a
        # limb that has not changed, is not a person short of oxygen.
        if (name == "blue" and _matches(BLUE_LIMB, line)
                and not _matches(BLUE_LIPS_FACE, line)
                and not _matches(BLUE_TINGE, line)
                and not _matches(BLUE_CHANGE, line)):
            continue
        # Cold hands that have gone blue are still cold hands, and a bruise going blue is a bruise.
        if (name == "blue" and _matches(BLUE_LIMB, line) and _matches(BLUE_COLD, line)
                and not _matches(BLUE_LIPS_FACE, line) and not _matches(BLUE_TINGE, line)):
            continue
        # "turning blue" on its own is the breath arm's case for a person, and a pet's colour is
        # the vet's, so the breath arm stands down and the blue arm below answers it.
        if (name == "breathing" and _matches(PET_ANY, line) and not _matches(HUMAN_TOO, line)
                and _matches(BLUE_CHANGE, line) and not _matches(PET_CRISIS, line)):
            continue
        # A garment in the wash going blue is the fabric, not a person short of oxygen.
        if (name == "blue" and _matches(BLUE_CLOTH, line) and not _matches(BLUE_LIPS_FACE, line)
                and not _matches(A_BODY_PART, line)):
            continue
        # Food in the fridge going blue is mould, not a person short of oxygen. A person has to be
        # the one who changed colour: "my garlic went blue when i pickled it" is the garlic, and
        # the bare "i" in the clause after it is not someone short of oxygen.
        if (name == "blue" and _matches(BLUE_FOOD, line)
                and not _matches(BLUE_PERSON_SUBJECT, line)
                and not _matches(BLUE_OTHER_PERSON, line)
                and not _matches(BLUE_LIPS_FACE, line)):
            continue
        # The additions below are the person-side ones: a laugh is not a colour change, make-up is
        # not a colour change, and blue lips that the cold explains want warming up rather than an
        # ambulance. All of it passes when the breathing or the waking is wrong, because then the
        # colour is the least of it and the 999 card is right.
        # A laugh or a held breath that turns a face blue comes back in seconds, so it gets its own
        # light line: standing down was leaving the colour to the laundry ("wash the ruined
        # whites"), which is the wrong answer rather than no answer.
        if name == "blue" and _matches(WENT_BLUE_IDIOM, line) \
                and not _matches(WENT_BLUE_BREATH_RED, line):
            _note(memory, "general")
            return _fit(pick(REPLIES["blue_idiom"], memory), line, name)

        if name == "blue" and _matches(BLUE_COSMETIC, line) \
                and not _matches(WENT_BLUE_BREATH_RED, line):
            return None
        # A baby is the exception to "the cold explains blue lips": the threshold for a small baby
        # is lower, so a blue baby is a 999 call whatever the room is like.
        if name == "blue" and _matches(BLUE_FACE_PART, line) and _matches(BLUE_COLD_CAUSE, line) \
                and not _matches(WENT_BLUE_BREATH_RED, line) \
                and not _matches(COLD_ILLNESS, line) \
                and not _matches(NEWBORN + (r"\b(?:baby|babies|infant)\b",), line):
            mine = not _matches(OTHER_BODY, line)
            _note(memory, "blue")
            return _fit(pick(REPLIES["blue_cold" if mine else "blue_cold_other"], memory),
                        line, "blue")
        if name == "blue" and not _matches(BLUE_FACE_PART, line) and _matches(LIMB_PART, line) \
                and _matches(WENT_BLUE_FINE, line) and not _matches(WENT_BLUE_RED, line):
            continue
        if name == "blue" and _matches((r"\bchok\w*",), line):
            continue
        if (name == "blue" and _matches(BLUE_COLD_SELF, line) and _matches(BLUE_SELF, line)
                and not _matches(BLUE_LIPS_FACE, line) and not _matches(LIPS_RED_FLAG, line)):
            continue
        if (name == "blue" and _matches(BLUE_MARK, line)
                and not _matches(BLUE_LIPS_FACE, line)):
            continue
        if (name == "blue" and _matches(BLUE_LIPS_FACE, line) and _matches(LIPS_COLD, line)
                and not _matches(COLD_ILLNESS, line)
                and not _matches(LIPS_RED_FLAG, line)):
            continue
        if (name == "blue" and _matches(BLUE_FINE, line)
                and not _matches(BLUE_STRONG, line)):
            continue
        # Whose lips they are decides the wording: "my lips are blue" is the reader's own, and
        # "keep them sitting up" is a reply about somebody else.
        if name == "blue":
            key = "blue" if _matches(OTHER_BODY, line) else "blue_self"
            _note(memory, name)
            return _for_the_person(_fit(pick(REPLIES[key], memory), line, name), line, name)
        # A floppy hat, a limp lettuce or a floppy-eared rabbit is not a sick child.
        if name == "floppy_child" and _matches(FLOPPY_THING, line):
            continue

        # Floppy on the way to sleep, asked about as a normal thing: answer the question.
        if (name == "floppy_child" and _matches(FLOPPY_SLEEPY, line)
                and not _matches(FLOPPY_RED_FLAG, line)):
            return _fit(pick(REPLIES["floppy_soft"], memory), line, "floppy_child")

        # A joint that will not take weight is an X-ray today, not a spine: "i cant put weight on
        # my ankle" was getting "stay where you are and ring 999". The hip, the floor, a fall
        # from a height and an older person who has gone down keep the ambulance.
        if name == "fall" and _weight_on_a_joint(line):
            continue
        if name == "fall":
            key = "fall_self" if _matches((r"\bi\b", r"\bmy\b"), line) and not _person(
                line) else "fall"
            return _fit(pick(REPLIES[key], memory), line, "fall")
        # A fall in someone older gets checked the same day even when they are up and talking, so
        # this one asks two questions: is this a person old enough for it to matter, and is there
        # anything in the line that says the fall was harmless or never happened.
        # A bang on the head has its own reply, with the signs to watch for, and it is the better
        # answer for "my nan fell and banged her head": this arm only says to get it looked at.
        # A quarrel is not a fall: "i fell owt wiv me sister", typed the way people type it, was
        # the bruising card, and so was "we fell owt over money". The idiom guard lived inside the
        # confusion check only, which these lines do not reach.
        if name in ("old_fall", "fall", "fall_check") and _matches(FALL_WORD_IDIOM, line):
            continue
        if name == "old_fall" and _matches(HEAD_BANG, line):
            continue
        if name == "old_fall" and _matches(FALL_STROKE_SIGN, line) \
                and not _matches(SLUR_NOT_A_STROKE_WORDS, line):
            continue
        if name == "old_fall" and _fall_with_sign(line):
            continue
        if name == "old_fall" and (_matches(HEAD_KNOCKOUT, line)
                                   or _out_cold_knockout(line)):
            continue
        if name == "old_fall" and not _matches(OLD_PERSON, line):
            continue
        if name == "old_fall" and _matches(OLD_FALL_FINE, line):
            continue
        if name == "old_fall" and _matches(OLD_FALL_NOT, line):
            continue
        if name == "old_fall" and _matches(FALL_PAST, line) and not _matches(FALL_NOW, line):
            continue
        if name == "old_fall" and _matches(NEAR_MISS, line) and not _matches(NEAR_MISS_HARM, line):
            continue
        if name == "old_fall" and _matches(PET_FELL, line) and not _matches(HUMAN_TOO, line):
            continue
        if name == "old_fall":
            key = "old_fall_self" if _matches(FIRST_PERSON, line) and not _person(
                line) else "old_fall"
            return _fit(pick(REPLIES[key], memory), line, "old_fall")
        # Floppy on the way to sleep, asked about as a normal thing: answer the question (#670).
        if (name == "floppy_child" and _matches(FLOPPY_SLEEPY, line)
                and not _matches(FLOPPY_RED_FLAG, line)):
            return _fit(pick(REPLIES["floppy_soft"], memory), line, "floppy_child")
        # "is fitting" is only a fit when a person is doing it: a shelf fitting is a DIY job.
        # "my cat is fitting in with the new baby" is a new pet, not a seizure: a fit needs a
        # person as its subject, and "fitting in" is the idiom.
        if name == "seizure" and _matches((r"\b(?:is|are|keeps?)\s+fitting\b",), line) and (
                not _matches(A_PERSON, line)
                or _matches(FITTING_IN + FITTING_THING, line) or _a_settling_fit(line)):
            continue
        if name == "hypo":
            key = "hypo_self" if _matches((r"\bi\b", r"\bmy\b"), line) and not _person(
                line) else "hypo"
            return _fit(pick(REPLIES[key], memory), line, "hypo")
        if name == "heat":
            key = "heat_self" if _matches((r"\bi\b", r"\bmy\b"), line) and not _person(
                line) else "heat"
            return _fit(pick(REPLIES[key], memory), line, "heat")
        if name in ("red_flags", "stiff_neck", "sepsis_signs", "newborn_fever",
                    "newborn_fever_next"):
            # The user is the patient unless the line names someone else, and "my baby" is someone
            # else: the reply has to tell them how to help, not how to be helped.
            key = "red_flags_self" if _matches(
                (r"\bi\b", r"\bi'm\b", r"\bim\b", r"\bmy\b"), line) and not _matches(
                PERSON_WORD + (r"\b(?:newborn|infant|toddler|little\s+one|baby|babies)\b",),
                line) else "red_flags"
            return _fit(pick(REPLIES[key], memory), line, "red_flags")
        if (name == "chest" and _matches(CHEST_FEELING, line)
                and not _matches(_CHEST_OTHER_RED, line)
                and not _matches(CHEST_FEELING_RED, line)
                and not _matches(AFTER_EXERCISE, line)):
            # The feeling is the cause the person already has, so the answer is the anxiety one and
            # the 999 signs come after it rather than in place of it.
            return _fit(pick(REPLIES["chest_anxiety"], memory), line, "chest")
        if (name == "chest" and _matches(CHEST_ADJ, line)
                and not _matches(CHEST, line)
                and not _matches(AFTER_EXERCISE, line)):
            # "i have a tight chest with a cold", "a tight chest when i cough": tightness said
            # before the word chest is only this entry's line when effort is in it, or when a
            # shape that already matched would have said so anyway.
            continue
        if name == "chest" and _matches(AFTER_EXERCISE, line) and (
                not _matches(CHEST_RED_FLAGS, line) or (
                    _matches(EXERTION_CHEST, line)
                    and not _matches(_CHEST_OTHER_RED, line))):
            return _fit(pick(CHEST_EFFORT, memory), line, "chest")
        if (name == "chest" and _matches(CHEST_TRAINING, line)
                and not _matches(CHEST_SPREADING, line)):
            continue
        if thing_collapsed and name in ("unconscious", "medical"):
            continue
        if name == "stuck_machine" and _matches(STUCK_FINE, line) \
                and not _matches(MACHINE, line):
            continue
        # "cant wake up for school/work" is a routine grumble unless something red follows.
        if name == "unconscious" and _matches(ROUTINE_WAKE, line) and not _matches(WAKE_RED, line):
            continue
        # "my friend isnt coming round after all" is a visit and "he hasnt come round yet" is a person
        # still out. The visit words are only believed when nothing in the line says what happened.
        if name == "unconscious" and _matches(WONT_COME_ROUND, line) \
                and not _matches(UNCONSCIOUS, line) and not _matches(WAKE_UP_SOMEONE, line) \
                and _matches(VISIT_OR_TIME, line) and not _matches(COLLAPSE_HINT, line):
            continue
        # A person who is hard to wake in the mornings is a grumble, unless the line says more.
        if name == "unconscious" and _matches(HARD_TO_WAKE, line) \
                and not _matches(UNCONSCIOUS, line) and not _matches(WAKE_UP_SOMEONE, line) \
                and _matches(MORNING_ROUTINE, line) and not _matches(COLLAPSE_HINT, line):
            continue
        # A reason to be up early is the whole story of "i cant wake my mum up for work". The routine
        # words are open-ended, so this is a list of reasons rather than a fence on each shape.
        if name == "unconscious" and _matches(ROUTINE_REASON, line) \
                and not _matches(WAKE_RED + COLLAPSE_HINT + SPELL_RED, line):
            continue
        if name in ("chest",) and _asking_about_the_world(line) and not _matches(
                (r"\bright\s+now\b", r"\bnow\b", r"\bsudden(?:ly)?\b"), line):
            # ... and the calm version still has the chest in it: a question about causes is not an
            # ambulance, and it is not "go easy on yourself" either (CHEST_ASKED says why). Only
            # where the answer lane has nothing for the line, so the tightness, the reflux and the
            # breathing cards keep theirs.
            if _matches(CHEST_ASKED_OWN, line) and not _matches(
                    CHEST_KEPT_BY_ANOTHER_CARD, line):
                return _fit(pick(CHEST_ASKED, memory), line, "chest")
            continue
        # A headache and a gunshot are the patient's own line as often as someone else's, and a
        # neighbour or a passer-by has no he or she in the line to read the person from.
        if name == "stuck_machine":
            mine = not _matches(OTHER_BODY, line)
            key = name + "_self" if mine else name
            return _fit(pick(REPLIES[key], memory), line, name)
        if name in ("headache", "shot"):
            if name == "shot":
                mine = _matches(SHOT_SELF, line) and not _person(line)
            else:
                mine = _person(line) is None and _matches((r"\bi\b", r"\bmy\b"), line)
            key = name + "_self" if mine else name
            return _fit(pick(REPLIES[key], memory), line, name)
        # The night that is already over is an appointment today; anything still happening, or
        # with a red flag in it, stays with the cases above.
        # A shock that killed is a loss, and a shock from childhood is a story.
        # A tool in a socket is the shock waiting to happen; an adapter, a socket being replaced
        # and a socket from years ago are not.
        if name == "socket_thing" and _matches(SOCKET_THING_FINE, line):
            continue
        # A person who is not breathing or is unconscious beside a shock is a resuscitation,
        # and the shock card's "111 the same day" must never reach them.
        if name == "electric_shock_floor":
            if (_matches(ELECTRIC_SHOCK_NEARLY, line) or _matches(ELECTRIC_SHOCK_DEATH, line)
                    or (_matches(ELECTRIC_SHOCK_NOT_ELECTRIC, line)
                        and not _matches(ELECTRIC_SHOCK_SUPPLY, line))
                    or _matches(ELECTRIC_SHOCK_CPR, line) or _matches(ELECTRIC_SHOCK_STORY, line)
                    or _matches(ELECTRIC_SHOCK_DEFINITION, line)
                    or (_matches(ELECTRIC_SHOCK_STATIC, line)
                        and not _matches(ELECTRIC_SHOCK_WIRED, line))):
                continue
            # Whose body went down decides the wording: "put them on their side" is no use to the
            # person who was knocked out themselves.
            key = "electric_shock_floor" if (_person(line) or _matches(OTHER_BODY, line)) else (
                "electric_shock_floor_self")
            _note(memory, name)
            return _fit(pick(REPLIES[key], memory), line, name)
        if name == "electric_shock" and _matches(ELECTRIC_SHOCK_DOWN, line):
            continue
        # ...and a question about what a shock does is the knowledge card, not the card above.
        if name == "electric_shock" and _matches(ELECTRIC_SHOCK_DEFINITION, line):
            continue
        if name == "electric_shock" and _matches(ELECTRIC_SHOCK_DEATH, line):
            continue
        if name == "electric_shock" and _matches(ELECTRIC_SHOCK_STORY, line):
            continue
        if name == "electric_shock" and _matches(ELECTRIC_SHOCK_STATIC, line) \
                and not _matches(ELECTRIC_SHOCK_WIRED, line):
            continue
        if name == "night_breath" and _matches(NIGHT_BREATH_RED, line):
            continue
        # A nose that is blocked explains the night gasp the same way it explains the daytime one:
        # "i woke up with a blocked nose and couldnt breathe" is the cold, not the heart.
        if name == "night_breath" and _matches(BREATH_CAUSE, line) and not _matches(
                NIGHT_BREATH_RED, line):
            continue
        # A nightmare is not the heart: the gasp it leaves behind is the dream coming back.
        if name == "night_breath" and _matches(NIGHT_BREATH_DREAM, line):
            continue
        # A child's night is the same-day call for the parent, but the words have to be about the
        # child: `my baby was gasping in his sleep` was told to ring 111 and "say it happened in
        # your sleep", which is advice for a grown-up about themselves.
        if name == "night_breath" and _matches(NIGHT_BREATH_CHILD, line) \
                and not _matches(NIGHT_BREATH_RED, line):
            _note(memory, name)
            return _fit(pick(REPLIES["night_breath_child"], memory), line, name)
        # A cat that wakes up gasping is the vet's, the same as a cat that chokes.
        if name == "night_breath" and _matches(ANIMAL, line) and not _matches(
                HUMAN_TOO, line):
            continue
        if hypothetical:
            general = GENERAL.get(name)
            if general:
                _note(memory, name)
                return _for_the_person(general, line, name)
            continue
        # Numbness in one arm is a chest when the chest is named in the same line, and a stroke
        # question when it is not.
        # The FAST pair is the one thing in this file that must not be reasoned away, so the
        # stand-down is narrow on purpose: it only reaches a line the FAST arm alone caught, and
        # only with an old cause, an over-use cause or a settled pattern in it.
        if name == "stroke" and _matches(STROKE_FAST, line) and not _matches(STROKE, line):
            # The injected arm and the shoulder that stops at shoulder height keep their own
            # answers: `cant lift` is a hard sign, so a cause alone does not stand them down. No
            # face word in the line is what makes it the arm rather than the stroke.
            if not _matches(_FACE_WORD, line) and (
                    _matches(STROKE_FAST_JAB, line) or _matches(STROKE_FAST_LIFT_CEILING, line)):
                continue
            if _matches(STROKE_FAST_OFF, line) or _matches(STROKE_FAST_SHOULDER, line) or (
                    _matches(STROKE_FAST_PATTERN, line)
                    and not _matches(STROKE_PAIR_BOTH, line)
                    and not _matches(STROKE_FAST_WEAK, line)) or (
                    not _matches(STROKE_FAST_HARD, line)
                    # ...except that a jab explains the arm and never the face that went with it:
                    # "my left arm is weak since my covid jab and my face feels funny" is a pair
                    # with a cause on one half. Numb is left out of _FACE_GOING_ODD on purpose, so
                    # "hands numb from the cold and my face is numb" keeps the cause it had.
                    and not (_matches(STROKE_FAST_JAB, line)
                             and _matches(_FACE_GOING_ODD, line))
                    and (_matches(STROKE_FAST_CAUSE, line)
                         or _matches(STROKE_FAST_SENSORY, line))):
                continue
        if name == "arm_numb" and _matches(CHEST_MENTIONED, line):
            continue
        if name == "chest" and _matches(CHEST_WORK, line) and not _matches(CHEST_URGENT, line):
            _note(memory, "chest_slow")
            return _fit(pick(REPLIES["chest_work"], memory), line, name)
        if name == "chest" and _matches(CHEST_SLOW, line) and not _matches(CHEST_URGENT, line):
            _note(memory, "chest_slow")
            return _fit(pick(REPLIES["chest_slow"], memory), line, name)
        # A chest that hurts with the cough is a strained muscle, not a heart attack. Any heart
        # sign, blood, or a line that says it is happening now keeps the ambulance above.
        if (name == "chest" and _matches(CHEST_SORE_MOVE, line)
                and not _matches(CHEST_URGENT, line)
                and not _matches(CHEST_RED_FLAGS, line)
                and not _matches(CHEST_SPREAD, line)
                and not _matches(CHEST_STRAIN_STOP, line)
                and not _matches((r"\bblood\b", r"\bbleed\w*", r"\bright\s+now\b"), line)):
            if _matches((r"\bcough\w*",), line):
                return _fit(pick(CHEST_COUGH_STRAIN_REPLY, memory), line)
            return _fit(pick(CHEST_STRAIN_REPLY, memory), line)
        if (name == "chest" and _matches(CHEST_STRAIN_MOVE, line)
                and not _matches(CHEST_URGENT, line)
                and not _matches(CHEST_RED_FLAGS, line)
                and not _matches(CHEST_SPREAD, line)
                and not _matches(CHEST_STRAIN_STOP, line)
                and not _matches((r"\bblood\b", r"\bbleed\w*", r"\bright\s+now\b"), line)):
            return _fit(pick(CHEST_STRAIN_REPLY, memory), line)
        if (name == "chest" and _matches(CHEST_STRAIN, line)
                and not _matches(CHEST_URGENT, line)
                and not _matches(CHEST_RED_FLAGS, line)
                and not _matches(CHEST_SPREAD, line)
                and not _matches(CHEST_STRAIN_STOP, line)
                and not _matches((r"\bblood\b", r"\bbleed\w*", r"\bright\s+now\b"), line)):
            return _fit(pick(CHEST_COUGH_STRAIN_REPLY, memory), line)
        # A jaw or an arm that aches with no chest in the line is still the ambulance, but the
        # reply must not describe a chest the person never mentioned.
        if name == "chest" and not _matches(CHEST_MENTIONED, line):
            _note(memory, "chest")
            return _for_the_person(_fit(pick(REPLIES["chest_limb"], memory), line, "chest"),
                                   line, "chest")
        # A blow that landed on the nose is not an object up it, and the bruise answer is not
        # "get it looked at today" for a toy: the abuse gate and the parenting answer take it.
        if name == "object_in_head" and _matches(OBJECT_IN_HEAD_BLOW, line) \
                and not _matches(OBJECT_IN_HEAD_BATTERY, line):
            continue
        if name == "object_in_head" and _matches(OBJECT_IN_HEAD_BATTERY, line):
            _note(memory, "object_in_head_battery")
            return _fit(pick(REPLIES["object_in_head_battery"], memory), line, name)
        # A course of doses spaced hours apart, and the packet's own daily maximum, are what the
        # label says: the poisons card on those teaches a parent that the bot cries wolf on the
        # line where they told the truth.
        if name == "poison" and _matches(DOSE_COURSE, line) and not _matches(
                DOSE_COURSE_KEEP, line):
            continue
        # Asking whether a bigger dose may be given is not a report that it was given.
        if name == "poison" and _matches(DOSE_ASKED, line) and not _matches(
                DOSE_ALREADY_GIVEN, line):
            continue
        if name == "dose_stated":
            counted = _stated_dose(line)
            if counted is None:
                continue
            _note(memory, "dose_stated")
            return counted
        if name == "swallowed_thing" and _matches(SWALLOWED_BAD, line):
            _note(memory, name)
            if _matches(SPEAKER_IS_PATIENT, line) and not _matches(SWALLOWED_CHILD, line):
                return pick(SWALLOWED_BAD_SELF, memory)
            return pick(SWALLOWED_BAD_REPLY, memory)
        if name == "swallowed_thing" and _matches(SPEAKER_IS_PATIENT, line) and not _matches(
                (r"\bmy\s+(?:child|son|daughter|baby|toddler|kid|boy|girl)\b",), line):
            _note(memory, name)
            return pick(SWALLOWED_SELF, memory)
        # A cut of your own that is still bleeding wants the cloth first, and the crisis line in
        # the same breath: "i cut myself and the blood wont stop" was answered with the crisis line
        # alone on main - no pressure on the wound, no 999 - which is the wrong way round when the
        # bleeding is what hurts them in the next ten minutes. The self_harm case comes before the
        # first aid cases, which is why the crisis reply owned this line, and a bare "i cut myself"
        # keeps the support reply it has.
        # ...unless the line is the wish and not the act: `cut my thighs` is a method phrase the
        # bleeding row reads, and "press on it for ten minutes" is the wrong reply to somebody
        # who has not cut anything yet.
        if name == "self_harm" and not _a_wish_for_their_own_body(line) \
                and _matches(SELF_CUT, line) and (
                _matches(BLEEDING, line) or _matches(CUT_NOT_STOPPING, line)):
            _note(memory, "bleeding")
            return _fit(pick(REPLIES["self_cut_bleeding"], memory), line, "self_cut_bleeding")
        # The fit said by the person who had it: "i had a fit" was told to lie *themselves* on
        # their side and to time it on their phone, which the reader cannot do to themselves. Same
        # rule as the electric shock above - whose body it was decides the wording - and a fit
        # somebody else had keeps the card it has.
        if name == "recent_fit" and not (_person(line) or _matches(OTHER_BODY, line)):
            _note(memory, "recent_fit_self")
            return _fit(pick(REPLIES["recent_fit_self"], memory), line, "recent_fit_self")
        _note(memory, name)
        return _for_the_person(_fit(pick(REPLIES[name], memory), line, name), line, name)
    # Cold hands and feet that go white, then blue, then red and sore are Raynaud's: common, a GP
    # word, and an answer people were not getting at all - "my toes turn blue when its cold" was
    # answered by the laundry module. The cold has to be in the line: a limb that is simply blue
    # is the went_blue card above, because nothing else explains the colour.
    # A limb the cold explains, said the way people say it, is already answered well ("blue in the
    # cold", "blue with cold" is the Raynaud's card from the health module), so safety keeps out of
    # it: this arm is for the shapes that were getting the laundry card, like "my toes turn blue
    # when its cold" and "my toes went white with the cold".
    if (not hypothetical and _matches(RAYNAUD, line)
            and _matches((r"\bcold\b", r"\bwinter\b", r"\braynaud\w*\b", r"\bswim\w*",
                          r"\bsea\b", r"\bsnow\b", r"\bfreez\w*", r"\bice\b",
                          r"\bshower\b", r"\bwater\b", r"\bwashing\s+up\b"), line)
            and not _matches((r"\b(?:blue|white|purple|grey|gray)\s+(?:in|with|from|out\s+in|and)\s+"
                              r"(?:the\s+|a\s+)?(?:cold|freezing)",), line)
            # A swim or the sea is the same cold, and the health module's Raynaud's card for it is
            # the more complete one (it names the one-sided numbness that would be 999).
            and not _matches((r"\b(?:swim\w*|swam|the\s+sea|sea\s+water|pool|lido|"
                              r"cold\s+water)\b",), line)
            and not _matches((r"\b(?:can'?t|cannot|struggling\s+to|stopped)\s+breath\w*",
                              r"\bgasping\b", r"\bchest\b", r"\bunconscious\b",
                              r"\bchoking\b"), line)):
        return _fit(pick(REPLIES["raynaud"], memory), line, "minor")
    # A cut that soaks through the cloth or will not stop is past the ten-minute first aid, but it is
    # not automatically an ambulance: it needs seeing the same day. The red-flag cuts (deep, spurting,
    # a wrist or a thigh) were already taken by the bleeding case above.
    soft_bleed = (_matches(SOFT_BLEED, line) and _matches(SOFT_BLEED_ANCHOR, line)
                  and not _matches(SOFT_BLEED_OFF, line))
    if (soft_bleed or _matches(NOT_STOPPING, line)) and not _matches(NOT_STOPPING_OFF, line):
        return _fit(pick(REPLIES["bleeding_wont_stop"], memory), line, "minor")
    # A bang on the head: what to do now, and the one question that sorts a knock-out from a bump.
    head = None if hypothetical else _head_bang(line)
    if head and _matches(PET_WORDS, line) and not _matches(HUMAN_ANCHOR, line):
        head = None  # a dog with a bumped head is a vet question, not an ambulance
    if head:
        who = _head_person(line)
        keys = {"watch": ("head_bang", "head_bang_other"),
                "red": ("head_bang_red", "head_bang_red_other")}[head]
        text = pick(HEAD_REPLIES[keys[1] if who else keys[0]], memory)
        if who:
            subj, obj = ("she", "her") if who == "she" else ("he", "him")
            text = text.format(s=subj, o=obj)
        return text
    # "what if i burn my hand" is the first-aid question, so a hypothetical about the user's own
    # body keeps the minor reply; one about somebody else, or a story, does not.
    # A child, a partner or an elderly parent on the line is somebody in the speaker's care, not
    # somebody else: the card for that injury is still the answer, spoken of the person named.
    care = _matches(OWN_INJURY_IN_MY_CARE, line)
    own_question = (hypothetical and _matches(OWN_INJURY_QUESTION, line)
                    and _matches((r"\bi\b", r"\bmy\b", r"\byour\b"), line)
                    and not _matches(OWN_INJURY_SOMEONE_OR_A_STORY, line)
                    and (care or not _matches(OWN_INJURY_YOU + OWN_INJURY_OTHER_PERSON, line)))
    # "how many days will it take to heal" is read as a question about the world - the person is
    # not named in it - but a turn after the burn card it is a question about that burn, and the
    # chat is where its subject is. Only a follow-up that borrows its injury this way counts.
    if not own_question and hypothetical and _the_injury_the_chat_is_on(line, memory):
        own_question = True
    minor = _minor(line, memory)
    if minor and (not hypothetical or own_question):
        if care and isinstance(minor, tuple) and len(minor) > 1:
            # The card has a phrasing for the person hurt and one that speaks of the injury, and
            # "pinch the soft part of your nose" is the wrong one for a child on the line.
            spoken = tuple(one for one in minor if not re.search(r"\byou\b|\byour\b", one, re.I))
            minor = spoken or minor
        return _fit(pick(minor, memory), line, "minor")
    # ...and a singed fringe is not a burn, but it is not "Noted" either: it gets an answer. The skin
    # under it decides which one, so a red or blistered forehead still gets the water.
    if _matches(HAIR_SCORCH, line):
        if _matches(HAIR_SCORCH_SKIN, line) or _matches(MILD_BODY_SIGN, line):
            burn_card = _minor_replies("burn")
            if burn_card:
                return _fit(pick(burn_card, memory), line, "minor")
        return pick(HAIR_SCORCH_ANSWER, memory)
    # The call itself, asked about with nothing to judge: the rule for ringing is the answer.
    if _matches(ASKS_IF_CALL, line) and not _matches(CALL_HAS_A_SIGN, line):
        _note(memory, "general")
        return pick(ASK_CALL_REPLIES, memory)
    # A card that ordered an ambulance has already answered "should i go to hospital", and the
    # answer is the call. The A&E rule of thumb below is for a person deciding about a morning's
    # appointment; after a chest-pain card it was a downgrade inside a live emergency.
    if not _matches(CALL_HAS_A_SIGN, line) and (
            _matches(ASKS_IF_GOING, line) or _matches(ASKS_GO_BARE, line)):
        was_case = _last_case(memory)
        live = not (isinstance(memory, dict) and memory.get("safety_safe"))
        if was_case in AMBULANCE_CASES and live and not _matches(GO_IN_NOT_ABOUT_IT, line):
            _note(memory, was_case)
            wait = WAITING.get(was_case) or WAITING["general"]
            return _fit(pick(GO_IS_A_CALL, memory)
                        + pick(wait if isinstance(wait, tuple) else (wait,), memory), line, was_case)
    if _matches(ASKS_IF_GOING, line) and not _matches(CALL_HAS_A_SIGN, line):
        _note(memory, "general")
        return pick(ASK_GO_REPLIES, memory)
    # A near miss the fire's own cards never saw - "i nearly burnt the house down", "i nearly had a
    # fire but it was fine" - is still a fright, and this is the last place to say so: it comes
    # after every card and after the small injuries, so a burn or a toaster that is smoking is
    # answered by what it is, and only a bare near miss lands here. A fire drill is not a fire.
    if _matches(NEAR_FIRE, line) and not _matches(FIRE_DRILL, line) \
            and not _minor(line, memory):
        if _a_fire_that_did_not_happen(line):
            _note(memory, "near_fire")
            return _fit(pick(REPLIES["near_fire"], memory), line, "near_fire")
        # A fire word outside the near clause is a fire: "i nearly died and then the house was on
        # fire" was reaching the general fallback, because FIRE does not read "the house was on
        # fire" at all - it wants "is on fire". Here the near word has already said a fire is worth
        # a card, so the fire's card is the answer rather than an accident of wording. A line with
        # no fire word in it at all is neither - "prices almost went up" is not a fire - and is
        # left where it was.
        if _fire_words_in(line):
            _note(memory, "fire")
            return _fit(pick(REPLIES["fire"], memory), line, "fire")
    return _follow_up(line, memory)

from ..memory import again as _never_twice  # noqa: E402 - applied once the module is defined

# Whatever this module answers, the last thing that happens to it is the earlier-turn
# check (bot/memory/again.replied): `answers` alone served a card again on 59 deck turns.
respond = _never_twice.replied(respond)
