"""Moved out of bot/modules/memory_store.py whole, to keep that file small.

Nothing here is new: the same readers and pools, imported back by the module that
used to hold them. See bot/memory/store_lines.py for the same move made earlier.
"""
import re
from ..memory import facts as extract
from ..memory import current, keywords, last_user, log, name, note, others, plan_line, plan_sentence, remember, remember_other, stem, user
from ..memory.store_lines import AMOUNT_WORD, AT_TIME_VALUE, CORRECTION_BACK, COUNT_WORDS, FACT_FAMILY, NOT_A_UNIT, OTHER_KIND_SAY, OTHER_SAID, PLURAL_PETS, SPELLING_APART, UNIT_FAMILY
from ..memory import plans
from ..memory.named import carries_a_name
from ..memory.relations import _animal_family, _tidy_name


OTHER_BARE_NUMBER = re.compile(r"\d{1,3}")

def _number_belongs_to_that_age(memory):
    """Whether a bare number can only be the age of the person named before it.

    A number said on its own belongs to the fact the line before it stated. When that line stated
    that person's age ("my son is 7" then "no, 8") or asked something they want kept ("what should
    I get her" then "no, 6"), the age is what moves. When it stated something else about the user
    ("i weigh 80 kilos", "my budget is 30"), the number is that fact's correction, and reading it
    as the child's age files a weight against the child: "my son is 7", "i weigh 80 kilos", "no,
    75" used to keep the son at 75 years old.
    """
    last = str(last_user(memory) or "").strip()
    if not last:
        return True
    stated = [entry for entry in memory.get("facts_log") or []
              if isinstance(entry, dict) and entry.get("key") == "other"]
    if stated and str(stated[-1].get("text") or "").strip() == last:
        return True
    # A correction is the same statement in fewer words, so "my son is 7", "no, 8", "no, 9" is
    # the age moving twice: the line before "no, 9" said his age, it just said it as a fix.
    fixed = memory.get("correction") or {}
    if isinstance(fixed, dict) and str(fixed.get("said") or "").strip() == last:
        said = str(fixed.get("line") or "")
        if said and (extract.extract(said).get("others") or []):
            return True
    return bool(_asks(last))

def _a_name_for_a_person(value):
    """Whether a corrected value can be somebody's name at all.

    A rename is only read when what follows is a name: `_not_a_name` turns down the words people
    use about somebody ("fine", "complicated") and a month or a weekday is never one, so the
    answer to "what is my sister called" is never "Sunday".
    """
    word = " ".join(str(value or "").split())
    low = word.lower()
    if not word or low in extract.MONTHS or low in extract.DAYS:
        return False
    if extract._not_a_name(word, strict_ly=False):
        return False
    # A word that ends the way a doing or a way of being does is one: nobody is called
    # Complicated, and a name that really does end that way is on the reader's own short list
    # (Ted, Fred, Lily, Molly). The capital does not settle it here: the reader hands a corrected
    # value back capitalised ("Complicated"), so the capital says nothing about how it was typed.
    if low in extract.NAMES_THAT_END_LIKE_A_VERB:
        return True
    return not low.endswith(extract.NOT_NAME_ENDING)

def _a_new_name_was_said(target, text):
    """Whether the correction gives somebody a name at all, in one of the three shapes.

    The naming word says it in as many words ("no hes called dave"), and so does a denial that
    gives the name back ("no he isn't, it's Dave") - the pronoun and the negation are the frame
    there, and the name is what follows them. Away from those, people put a name right with the
    name and nothing else: "no its dave", "i meant dave", "sorry, dave".

    So the word itself is what has to hold up, and `facts.a_name_could_be` is the test: one word
    of a name's shape, not a word the bot reads as language ("its fine", "its complicated", "its
    the plumber"), and not a month or a day ("its sunday" is what day it is).

    A name that runs to two words is a name too, and it is the commonest one people have:
    "no its mrs jones", "no its elsa bell". Both words have to be a name or the title in front
    of one, so "no its mrs" is still not a name and "no it was very" still is not.
    """
    word = " ".join(str(target or "").split())
    if not word:
        return False
    if carries_a_name(text) or _denies_and_names(text):
        return True
    parts = word.split()
    if len(parts) == 2 and _a_word_of_a_name(parts[0]) and extract.a_name_could_be(parts[1]):
        return True
    return extract.a_name_could_be(word)

def _a_word_of_a_name(word):
    """Whether a word can lead a name: a title ("mr", "dr") or a name itself.

    Only the first half of a two-word name is checked with this, because the second half is
    checked as a name, and "no its mr" is a title with nothing behind it.
    """
    low = str(word or "").strip(".").strip().lower()
    if low in extract.TITLE_WORDS:
        return True
    return extract.a_name_could_be(low)

def _denies_and_names(text):
    """Whether the line denies the old name and gives the new one: "no he isn't, it's Dave".

    The pronoun and the negation are the frame here, where the other routes look for "called".
    Only the shape that gives a name back counts: "no he isn't Dave" denies one and names none, and
    neither does "no he isn't called Dave" - the naming word there belongs to the clause being
    denied, so the store keeps the name it had rather than the one the person ruled out.
    """
    if extract.a_name_is_taken_back(text):
        return False
    denial = extract.DENIAL_OF_A_VALUE.match(str(text or "").strip())
    return bool(denial and denial.group("says") and denial.group("value"))

def _correct_other(memory, target, text=""):
    """The correction of a fact kept against someone else, as the line it lands on plus a note.

    "My mum is allergic to nuts" then "no, peanuts": the fact is the mum's, so the user's own
    allergies are not what is being corrected, and the correction has to be re-said in her shape
    to reach it. Returns {"line", "note"}, or None when nothing is kept against anyone that fits.

    `text` is the line the person said, because a name is only corrected by a line that says it
    is the name ("no shes called dana"), not by the bare word the correction was read from.
    """
    known = [entry for entry in others(memory)
             if isinstance(entry, dict) and entry.get("who")]
    if not known:
        return None
    # A bare number is the one kind of fact about someone else that can be said on its own: "my
    # son is 7" then "no, 8". The other kinds are said in words, so a number cannot be a
    # correction of them, and the age of the last person named is what it moves.
    number = OTHER_BARE_NUMBER.match(str(target or "").strip())
    if number and not _number_belongs_to_that_age(memory):
        return None
    if number:
        for entry in reversed(known):
            if not isinstance(entry.get("age"), int):
                continue
            who = str(entry.get("who") or "").strip()
            age = int(number.group(0))
            if not who or not 0 <= age <= 120:
                return None
            remember_other(memory, {"who": who, "age": age})
            return {"line": "my %s is %d" % (who, age),
                    "note": "%d \u2014 got it, your %s is %d from now on." % (age, who, age)}
        return None
    for entry in reversed(known):
        who = str(entry.get("who") or "").strip()
        if not who:
            continue
        kept = [kind for kind, _ in OTHER_SAID if entry.get(kind)]
        for kind, saying in OTHER_SAID:
            if kept and kind not in kept:
                continue
            if kind == "name" and (not _a_name_for_a_person(target)
                                   or not _a_new_name_was_said(target, text)):
                # Two rules, and a name has to pass both. The word has to be one a person could
                # be called at all - "actually its fine" and "its sunday" are remarks about the
                # sister, not her new name - and the line has to say it is the name ("no shes
                # called dana"), the same rule _correct_a_persons_name follows.
                continue
            line = "my %s %s %s" % (who, saying, target)
            found = extract.extract(line)
            mine = [item for item in (found.get("others") or [])
                    if isinstance(item, dict)
                    and str(item.get("who") or "").lower() == who.lower()]
            if not any(item.get(kind) for item in mine):
                continue
            # The value the person means now replaces the one they corrected: "she is allergic
            # to nuts" then "no, peanuts" is peanuts now, the same way a corrected place is the
            # place they live in now.
            entry.pop(kind, None)
            for item in mine:
                remember_other(memory, item, line)
            shown = str(target)[:1].upper() + str(target)[1:]
            shape = OTHER_KIND_SAY.get(kind, "{v} it is, then.")
            return {"line": line, "note": shape.format(v=shown, who=who)}

MADE_OF_A_VALUE = re.compile(
    r"^(?:[\u00a3$\u20ac]?\s?\d"                       # 900, 800, 2, 1,000
    r"|the\s+\d{1,2}(?:st|nd|rd|th)"                  # the 12th
    r"|\d{1,2}(?::\d{2})?\s*(?:am|pm)"                # 7pm
    r"|(?:next\s+|this\s+|on\s+|until\s+|till\s+)?(?:mon|tues|wednes|thurs|fri|satur|sun)day"
    r"|(?:next\s+|this\s+|in\s+)?(?:january|february|march|april|may|june|july|august"
    r"|september|october|november|december))", re.I)

def _make_corrects(target, memory):
    """Whether "make it ..." puts a value where a value was.

    "make it 900" after "my budget is 500" and "make it 3 cats" after "we have 2 cats" are
    corrections, and a number, a date, a day or a time is one on its own. A word is one only when
    the line it puts right holds a fact to put it in ("we're going to lisbon" / "make it porto").
    "my boiler is broken" / "make it stop" and "a new sofa" / "make it bigger" are the rest of a
    sentence, and folding "Stop" into the topic would colour every turn after it.
    """
    if MADE_OF_A_VALUE.match(str(target or "").strip()):
        return True
    return bool(extract.extract(last_user(memory) or ""))

A_UNIT_SAID = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?\s*([a-z]+)", re.I)

def _the_unit(text):
    """The family of the unit a value is said in, or "" when it names no unit."""
    match = A_UNIT_SAID.search(str(text or "").lower())
    if not match:
        return ""
    return UNIT_FAMILY.get(match.group(1), "")

def _stated_families(before):
    """The families of unit a line is said in: the unit it names, and the facts it states."""
    families = set()
    unit = _the_unit(before)
    if unit:
        families.add(unit)
    try:
        found = extract.extract(before or "")
    except Exception:
        found = {}
    for key in found if isinstance(found, dict) else ():
        family = FACT_FAMILY.get(key)
        if family:
            families.add(family)
    return families

def _measured_the_same(value, before):
    """True when the line before is measured in the unit the new value is said in.

    Only values that name a unit are checked: a bare number ("make that 800") takes its meaning
    from the fact it corrects, which is what the readers below decide. The line before answers
    for it either by naming the same unit ("lose 5 kilos" / "8 kilos") or by stating a fact that
    is measured in that family at all ("my budget is 400" / "no, 600 pounds").
    """
    family = _the_unit(value)
    if not family:
        return True
    if any(_date_said(str(value or "").lower())):
        # A day is not measured in a unit, even though "21st" ends in the letters of "stone".
        # The unit reader took the ordinal suffix for a unit and dropped the correction before
        # the date reader could move the plan: "the party is on the 14th" / "sorry i meant the
        # 21st" kept the 14th. A date is the date reader's business, so it is not stopped here.
        return True
    return family in _stated_families(before)

NAMING_VERB = re.compile(r"^(?:(?:called|named)\s+"
                         r"|(?:he|she|it|they)(?:'s|s|\s+is|\s+was|\s+are)\s+"
                         r"(?:(?:called|named)\s+)?)(?=\S)", re.I)

def _without_the_naming_verb(value):
    """"no its called max": the value read off that line is the verb and the name both.

    The correction reader takes up to two words for a value, so a name given with its verb
    ("called max") arrived with the verb in it - and the store then kept a dog called "Called
    max", which is what the bot said back. The name is the word after the verb.

    The pronoun in front is the same fault in another shape: "no hes max" was kept as a cat
    called "Hes max", and "no shes called milly" as "Shes called milly". The pronoun names the
    pet the correction is about, so it is never part of the name either.
    """
    said = str(value or "").strip()
    fixed = NAMING_VERB.sub("", said)
    if fixed == said:
        return said
    return fixed[:1].upper() + fixed[1:]

def _the_plan_on_the_table(memory):
    """The plan as the chat holds it right now, in the words the store keeps it in.

    A second correction has no line in `facts_log` to lean on: the log holds the plan as it was
    first said ("sons birthday on 3 may"), while the chat has already moved it to "on 4 may", so
    "no the 5th" would find nothing to stand in place of. The plan on the table is the one the
    correction is about to rewrite, and it is read here before that happens.
    """
    if not isinstance(memory, dict):
        return None
    for key in ("plan",):
        value = (memory.get("user") or {}).get(key)
        if isinstance(value, str) and value.strip():
            return value
    for value in (memory.get("user") or {}).get("plans") or ():
        if isinstance(value, str) and value.strip():
            return value
    return None

def _the_plan_before(memory, plan_after):
    """The plan a correction came from: the newest one in the log that is not the new one.

    A plan keeps no key of its own that can be read back, so the plan the person put right is
    found where it was written down: the log holds every plan in the words it arrived in, and
    the one the correction replaced is the newest that is not the value they now mean.
    """
    after = " ".join(str(plan_after or "").lower().split())
    for entry in reversed([e for e in (memory.get("facts_log") or ()) if isinstance(e, dict)]):
        if entry.get("key") not in ("plan", "plans"):
            continue
        value = entry.get("value")
        if not isinstance(value, str) or not value.strip():
            continue
        if " ".join(value.lower().split()) != after:
            return value
    return None

def _what_took_its_place(before, after, value):
    """The words of `after` that stand where `value` stood in `before`, or None.

    "sons birthday on 3 may" corrected to "sons birthday on 4 may" says the fact "3 may" is now
    "4 may": the plan changed inside that fact, so the part of the new plan between the common
    start and the common end is what the fact now says, with the words the change left alone
    kept on either side of it. A plan that changed somewhere else returns None, so a value the
    correction did not touch is never rewritten.
    """
    before = " ".join(str(before or "").lower().split())
    after = " ".join(str(after or "").lower().split())
    value = " ".join(str(value or "").lower().split())
    if not value or not before or not after or value not in before:
        return None
    start = before.index(value)
    end = start + len(value)
    head = 0
    while head < min(len(before), len(after)) and before[head] == after[head]:
        head += 1
    tail = 0
    while (tail < min(len(before), len(after)) - head
           and before[len(before) - 1 - tail] == after[len(after) - 1 - tail]):
        tail += 1
    change_start, change_end = head, len(before) - tail
    if change_end <= start or change_start >= end:
        return None
    kept_head = before[start:min(change_start, end)]
    kept_tail = before[max(change_end, start):end] if change_end < end else ""
    new_middle = after[change_start:max(change_start, len(after) - tail)]
    fixed = (kept_head + new_middle + kept_tail).strip()
    return fixed or None

NOT_A_FACT_OF_THEIRS = frozenset("""who pronoun names name""".split())

A_DAY_SAID_LONG = re.compile(r"^(?:the\s+)?(\d{1,2}(?:st|nd|rd|th)?)\s+(?:of\s+)?([a-z]+)$",
                             re.I)

def _a_day_written_the_way_the_store_writes_it(fact):
    """The day without the little words it was said with, when the fact is a day."""
    text = " ".join(str(fact or "").split())
    found = A_DAY_SAID_LONG.match(text)
    if not found:
        return text
    return "%s %s" % (found.group(1), found.group(2))

def _the_person_the_plan_is_about(memory, correction, before=None):
    """A fact kept against a person moves with the plan the person put right.

    "my sons birthday is 3 may" then "actually its on 4 may" corrects the plan to "sons birthday
    on 4 may" and leaves the son's birthday at 3 May, so "when is my sons birthday" reads back
    the date they took back. The plan is the same fact the person carries, so a value the plan
    held and no longer holds is written on the person with what took its place. Nothing is moved
    on a plan that mentions nobody, so a trip keeps to itself.
    """
    plan_after = correction.get("value") if isinstance(correction, dict) else None
    if not before:
        before = _the_plan_before(memory, plan_after)
    if not before:
        return 0
    sentence = str(correction.get("sentence") or "").strip()
    moved = 0
    for entry in others(memory) or ():
        if not isinstance(entry, dict):
            continue
        who = str(entry.get("who") or entry.get("pronoun") or entry.get("name") or "").strip()
        if not who or not re.search(r"\b" + re.escape(who.lower()) + r"\w*\b", before):
            # The plan has to be about this person. "my trip is on 3 may" beside a son whose
            # birthday is also 3 May is a trip they are putting right, not the birthday.
            continue
        if plan_after and not re.search(r"\b" + re.escape(who.lower()) + r"\w*\b",
                                       str(plan_after).lower()):
            # The plan that took its place is about something else, so this person's fact is not
            # what moved: "my sons birthday is in august" / "sorry, july not june" corrects the
            # trip, and the birthday was left saying "in Portugal in July".
            continue
        for key, value in list(entry.items()):
            if key in NOT_A_FACT_OF_THEIRS:
                continue
            said = value if isinstance(value, str) else ""
            taken = _what_took_its_place(before, plan_after, said)
            if not taken or taken == " ".join(said.lower().split()):
                continue
            taken = _a_day_written_the_way_the_store_writes_it(taken)
            entry[key] = taken
            # The fact is kept again in the words the correction was said in, so the reader that
            # says what the chat holds about somebody ("what do you know about my son") has the
            # date they mean: it quotes the newest line about the person, and the old line is
            # then a value a later line gave again, which the store leaves out.
            kept = {("who" if entry.get("who") else "pronoun"):
                    entry.get("who") or entry.get("pronoun"), key: taken}
            log(memory).append({"key": "other", "value": kept,
                                "turn": len(memory.get("turns") or []),
                                "text": sentence or " ".join(str(plan_after or "").split())})
            moved += 1
    return moved

def _a_correction_is_not_a_plan(memory, text):
    """A line that put a value right is not also a plan of its own.

    "im going to spain in june" then "actually we fly in july now": the line says which month the
    trip moved to, and the trip it moved is the one already in the store. Read as a plan of its
    own as well, the list held "Spain in July" and "we fly in july now", and the reply said the
    second one back - "Got it - July." where the person had named the trip, not a month on its
    own. The words the line corrects with are not part of what it says, so the plan to drop is
    the line without them.
    """
    said = " ".join(str(text or "").lower().split())
    if not said:
        return
    body = " ".join(extract.CORRECTION_LEAD_RE.sub("", said).split())
    known = user(memory)
    plans = known.get("plans")
    if not isinstance(plans, list):
        return
    kept = [one for one in plans
            if " ".join(str(one).lower().split()) not in (said, body)]
    if len(kept) != len(plans):
        known["plans"] = kept


def _a_value_already_the_plans(memory, target, text=""):
    """Whether the value a line corrects to is already what the person's own plan says.

    A correction is applied once per turn but the store is written two or three times, and each
    later pass found the old month still in a twin of the plan: "im booking a trip to croatia in
    july" / "my mums birthday is 2 april" / "actually we fly out in october" moved "Croatia in
    july" to October and then moved "A trip to croatia in july" as well, and the value the answer
    reads the place from became the twin - so "whats the food like" lost Croatia and answered the
    birthday as a party. The line's own words do not count: the store files the correction as a
    plan on the way in ("we fly out in october"), and that is not a second thing to move.
    """
    said = str(target or "").strip().lower()
    if not said:
        return False
    line = " ".join(str(text or "").lower().split())
    known = user(memory)
    plans = [p for p in (known.get("plans") or []) if isinstance(p, str) and p.strip()]
    latest = known.get("plan")
    if isinstance(latest, str) and latest.strip():
        plans.append(latest)
    for one in plans:
        held = " ".join(one.lower().split())
        if line and (held in line or line in held):
            continue
        if re.search(r"\b" + re.escape(said) + r"\b", held):
            return True
    return False


def _apply_correction(memory, correction, text=""):
    """'Sorry, I meant Florence, not Rome' replaces Rome in the topic it corrects."""
    target = correction.get("to") if isinstance(correction, dict) else None
    if target:
        target = _without_the_naming_verb(target)
        correction["to"] = target
    wrong = correction.get("from") if isinstance(correction, dict) else None
    if not target:
        return
    if isinstance(correction, dict) and correction.get("applied"):
        return
    if _a_value_already_the_plans(memory, target, text):
        # A correction is one event, however many times the line is read in the turn: once the
        # value is in a plan, there is nothing left of it to move.
        return
    if not wrong and not _measured_the_same(target, last_user(memory) or ""):
        # "no 2 weeks" after "my budget is 400" is not a budget: a unit the fact on the table does
        # not use says the line is about something else, so nothing is corrected.
        return
    if isinstance(correction, dict) and correction.get("make") and not _make_corrects(target, memory):
        return
    # A number corrected inside a plan is the plan's own business, and it has to be asked first:
    # the fact path keeps a plan as the sentence it arrived in and swaps the value in whole, so
    # "5 kilos" corrected to "8 kilos" becomes "Lose 8 kilos kilos" there. When the line before
    # stated a plan and both values are numbers, the plan is the only thing that can be corrected:
    # a number the plan does not say ("i meant 8 not 2" after "lose 12 kilos") is a correction of
    # something else, and the fact path must not go guessing at it.
    both_numbers = bool(not extract.a_clock_time(target)
                        and NUMBER_VALUE.match(str(target or "").strip() or "-")
                        and NUMBER_VALUE.match(str(wrong or "").strip() or "-"))
    plan_on_the_table = _the_plan_on_the_table(memory)
    fixed = _correct_plan(memory, target, wrong, text)
    if not fixed and not (both_numbers and _stated_plan(memory)):
        # A date is read before the numbers are: "the 13th of june" states two values, and the
        # 13 in it is not a number that took the place of the plan's 12 - it is the same date
        # saying a different day, so the date reader moves the day and keeps the rest.
        fixed = (_correct_date(memory, target, text, wrong or "")
                 or _correct_clock(memory, target, text, wrong or "")
                 or _correct_number(memory, target, text)
                 or _correct_count(memory, target, text)
                 or _correct_fact(memory, target, wrong, text)
                 or _correct_a_persons_name(memory, target, text, wrong or "")
                 or _correct_when(memory, target, text)
                 or _correct_the_count_on_the_table(memory, target, text))
    if fixed and fixed.get("from") and not wrong:
        # A month or a day corrected without naming the old one: the line it corrects had it,
        # so the topic line is fixed the same way as the fact.
        wrong = fixed["from"]
        correction["from"] = wrong
    said = " ".join(str(text or "").lower().split())
    # A fact kept against someone else is nobody's plan and nothing in the user's own facts, so
    # it is asked for only when neither of those took the correction.
    other = None if fixed else _correct_other(memory, target, text)
    if other:
        other["said"] = said
        other["applied"] = True
        memory["correction"] = other
    if fixed:
        if fixed.get("key") == "plan":
            # The plan a person's own fact was stated in carries the fact with it: a date put
            # right moved the plan and left the person's entry at the date they took back.
            _the_person_the_plan_is_about(memory, fixed, plan_on_the_table)
            _a_correction_is_not_a_plan(memory, text)
        # The correction is the news of this turn: the old value is already replaced, so say
        # which one the bot is going with instead of leaving the user to wonder. The line is
        # kept so a later turn does not repeat the same note.
        fixed["said"] = said
        fixed["applied"] = True
        memory["correction"] = fixed
    if not fixed and not wrong:
        # Nothing was corrected, so nothing is rewritten. "make that" is an ordinary phrase
        # ("i make that mistake", "we make that recipe a lot"), and a line that fixes no fact
        # used to leave the topic it was on tagged "(mean Mistake)" - a store changed by a line
        # that changed nothing.
        return
    record = current(memory)
    if not record:
        return
    text = record["text"]
    moved_off_the_topic = bool(
        fixed and fixed.get("key") == "plan" and fixed.get("from")
        and not re.search(r"\b" + re.escape(str(fixed["from"])) + r"\b", text, flags=re.I))
    if moved_off_the_topic:
        # The date moved a plan the person is not speaking of: "my mums birthday is 2 april" was
        # the subject on the table and "actually we fly out in october" moves the trip. Rewritten,
        # the birthday read "(mean October)" and the next turn ("whats the food like") was
        # answered against the birthday, with Croatia gone from the topics the answer reads a
        # place from - so the older record is left whole and the line is this turn's own subject,
        # filed here because the store stops once a correction is applied.
        line = " ".join(str(said or text).split())
        if line:
            fresh = {"turn": len(memory.get("turns") or []), "text": line,
                     "words": keywords(line)}
            memory["topic"] = fresh
            topics = memory.get("topics")
            if not isinstance(topics, list):
                topics = memory["topics"] = []
            if not topics or topics[-1].get("text") != line:
                topics.append(fresh)
        return
    elif other:
        # The sentence the correction was said in is the one to hold, so a later "what did I
        # say?" answers with the value they meant.
        text = other.get("line") or text
    elif fixed and fixed.get("line"):
        # A plan put right by naming a new amount keeps the line it was said in, with the amount
        # they mean in it, so the next turn is read against one line and not against two amounts.
        text = fixed["line"]
    elif wrong and re.search(r"\b" + re.escape(wrong) + r"\b", text, flags=re.I):
        # The topic is kept as the line they corrected, with the value they mean now beside it:
        # a topic rewritten to read as a fresh statement ("my budget is 800") is claimed by the
        # module for that subject on the very turn of the correction, and the person who said
        # "make that 800" gets the savings lecture instead of "800 — got it".
        text = text + " (mean " + target + ")"
    elif fixed and fixed.get("key") == "plan" and _the_topic_with_the_new_clock(
            text, str(user(memory).get("plan") or "")):
        # A clock put right in a plan ("im flying at 6am" / "actually 7") left the topic as
        # "im flying at 6am (mean 7)", and the next turn asking what time to leave read the hour
        # that had been taken back. The topic keeps the person's own words with the time they
        # mean in them, which is the same move a plan's amount already gets.
        text = _the_topic_with_the_new_clock(text, str(user(memory).get("plan") or ""))
    elif target.lower() not in text.lower():
        text = text + " (mean " + target + ")"
    record["text"] = text
    record["words"] = keywords(text)
    # The corrected sentence without the note the topic carries: "my sons birthday is in
    # September" is what the correction says, and "my sons birthday is in August (mean
    # september)" is what the chat reads back. Facts are filed from the first, never the second.
    before = re.sub(r"\s*\(mean [^)]*\)\s*$", "", text, flags=re.I)
    stated = (_swap_in(before, target, wrong) if wrong else None) or before
    # The corrected sentence is a line that states something, so what it says about other people
    # is filed again from it. A birthday for somebody else is kept on the person, not in the plan:
    # "my sons birthday is in august" / "no its september" said "your son's birthday is in
    # September" and then answered "when is my sons birthday" with August, because the plan moved
    # and the person's own record did not. Only entries that say something about them are filed -
    # a person named in passing in a corrected plan is not a fact about them.
    for entry in extract.extract(stated or text).get("others") or []:
        if not set(entry) - {"who", "pronoun"}:
            continue
        fresh = entry.get("birthday")
        theirs = next((one for one in others(memory)
                       if one.get("who") == entry.get("who")), None)
        kept = " ".join(str((theirs or {}).get("birthday") or "").lower().split())
        if fresh and wrong and kept:
            # What they took back has to be in this person's birthday for the birthday to be the
            # fact being corrected: "im going to portugal in june" / "my sons birthday is in
            # august" / "sorry, july not june" moves the trip, and the birthday the line after it
            # gave is a different fact.
            hated = [part for part in re.split(r"[^a-z0-9]+", str(wrong).lower())
                     if part and part not in ("the", "of", "on", "in")]
            if hated and not any(part in kept for part in hated):
                continue
        if fresh:
            # A birthday moved by its day ("no the 4th") still belongs to the month the chat has,
            # the way a corrected figure keeps the word it was counted in: keeping only the new
            # day answered "your son's birthday is the 4th" and dropped May.
            held = next((one for one in others(memory)
                         if one.get("who") == entry.get("who")), None)
            before = str((held or {}).get("birthday") or "").lower()
            month = next((name for name in extract.MONTHS if name in before), None)
            if month and not any(name in str(fresh).lower() for name in extract.MONTHS):
                entry["birthday"] = "%s %s" % (fresh, month)
        remember_other(memory, dict(entry), stated or text)
    places = user(memory).get("places")
    if isinstance(places, list) and wrong and extract.place_value(target):
        # Keep the wrong one too: "which did I say first?" still has an answer, while the
        # latest place (the one they mean now) is the corrected one. A value that is not a
        # place is not put among them: "no in july" moved the date of the trip, and July was
        # filed as a third place they are going to.
        if not any(str(place).lower() == target.lower() for place in places):
            places.append(target)
    topics = memory.get("topics")
    if isinstance(topics, list) and topics and topics[-1] is not record \
            and topics[-1].get("text", "").startswith(record["text"][:10]):
        topics[-1] = record
    note(memory, text)

NUMBER_VALUE = re.compile(r"^(\d+(?:\.\d+)?)\s*([a-z]+)?$", re.I)

def _stated_plan(memory):
    """The plan the line before this one stated, or None.

    A plan has no fact key of its own ("plan", "plans"), so the correction path cannot read it
    the way it reads a name or an age; the value it replaces is a number inside the plan.
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
        if entry.get("key") in ("plan", "plans"):
            value = entry.get("value")
            return value if isinstance(value, str) and value.strip() else None
        return None
    return None

def _an_amount_on_the_measure(plan, target):
    """The plan with the amount they named now in it: "Lose a stone" / "i meant half a stone".

    The correction of a plan was read only when both values were figures ("lose 5 kilos" / "i
    meant 8 kilos"), so an amount said in words was dropped without a word: "i want to lose a
    stone" then "i meant half a stone" kept "Lose a stone" and answered "Thanks for telling me -
    I'm here if you want to dig into any of that", which says the correction did not land.

    What makes the two amounts the same fact is the measure after them, so the measure is what is
    matched: the word the new amount counts ("stone" in "half a stone", "minutes" in "30 minutes")
    has to be a measure the plan already says, and the amount in front of it is what moves. A plan
    that does not say that measure is a different fact and is left alone ("lose a stone" with
    "i meant a week" corrects nothing), and so is a measure with no amount in front of it.
    """
    words = re.findall(r"[a-z0-9']+", str(target or "").lower())
    if len(words) < 2:
        return None
    measure = words[-1]
    stem = measure[:-1] if measure.endswith("s") and len(measure) > 3 else measure
    if len(stem) < 3:
        return None
    found = re.search(r"(?<![\w])(" + AMOUNT_WORD + r"\s+)(" + re.escape(stem)
                      + r"(?:s|es)?)(?![\w])", str(plan or ""), re.I)
    if found is None:
        return None
    before = plan[:found.start()]
    said = str(target or "").strip()
    if before.strip():
        # The amount sits inside the sentence the plan was said in ("Lose ..."), so it is not
        # the first word and is not capitalised: "Lose half a stone", not "Lose Half a stone".
        said = said[:1].lower() + said[1:]
    return {"plan": before + said + plan[found.end():], "value": str(target).strip(),
            "in_the_sentence": said, "was": found.group(0)}

def _correct_plan(memory, target, wrong, text=""):
    """A number corrected inside a plan: "lose 5 kilos" / "i meant 8 kilos not 5".

    Both values have to be numbers, and the plan has to say the wrong one, or nothing is
    touched: "no, sesame" is a list fact and "no, thursday not tuesday" is a day. The unit is
    the plan's own, so "i meant 8" after "lose 5 kilos" gives "lose 8 kilos".
    """
    plan = _stated_plan(memory)
    if plan and not wrong:
        # An amount in words is corrected by naming the new one: "i meant half a stone" says no
        # old value, and the measure is the only thing that says the two are the same fact.
        amount = _an_amount_on_the_measure(plan, target)
        if amount:
            fixed, shown = amount["plan"], amount["value"]
            known = user(memory)
            known["plan"] = fixed
            plans = known.get("plans")
            if isinstance(plans, list):
                known["plans"] = [fixed if p == plan else p for p in plans]
            note(memory, fixed)
            # The note is the plan in the sentence they said it in, the same way a corrected
            # number inside a plan is said back: "Got it - you want to lose half a stone", not
            # the bare "Got it - half a stone", which does not say what it is half of. The old
            # amount is what moves in that sentence, or it would say the amount being taken back.
            origin = plan_line(memory, plan)
            if origin:
                was = amount["was"]
                origin = re.sub(r"(?<![\w])" + re.escape(was) + r"(?![\w])",
                                amount["in_the_sentence"], origin, count=1, flags=re.I)
            sentence = plan_sentence(fixed, origin)
            # The line the plan was said in, with the amount they meant in it, is the line the
            # topic keeps: "i want to lose half a stone". Left to the note below it would keep
            # both amounts side by side ("... (mean Half a stone)"), and the words of that line
            # are what the follow-up on the next turn is read against.
            # The answer about the new thing is not added for this one: it is read off lines
            # with a phrase swapped into them ("i want to save a couple of A few hundred a
            # month"), and a line like that says nothing - one of them was answered with a card
            # about getting a repair done, which has nothing to do with how much is saved. The
            # sentence the plan was said in is already the answer.
            return {"key": "plan", "value": shown, "sentence": sentence or fixed,
                    "line": origin or None, "quiet": True}
    right = NUMBER_VALUE.match(str(target or "").strip())
    if not plan or not right or not wrong:
        return None
    if extract.a_clock_time(target) or extract.a_clock_time(wrong):
        return None  # a clock is not a figure in a plan: `_correct_clock` reads that
    if not NUMBER_VALUE.match(str(wrong).strip()):
        return None
    number, unit = right.group(1), (right.group(2) or "").lower()
    # The unit the new value is said in is taken with the old number, so "3 days not 2 weeks"
    # leaves the words around it alone: "for 2 weeks in june" -> "for 3 days in june". When the
    # old value is a bare number the word after it is the plan's own unit and goes too, or the
    # plan ends up saying both ("for 2 weeks" + "not 2" -> "3 days weeks in june"); a word that
    # carries the rest of the plan (in, on, for, before ...) is never taken.
    pattern = r"(?<![\d.])" + re.escape(str(wrong).strip())
    if unit:
        pattern += r"(\s+" + re.escape(unit) + r"\b|\s+(?!" + NOT_A_UNIT + r"\b)[a-z]+\b)?"
    shown = []

    def swap(match):
        found = number + " " + unit if unit else number
        shown.append(found)
        return found

    fixed, count = re.subn(pattern, swap, plan, count=1, flags=re.I)
    if not count:
        return None
    # The line says the value the way the plan says it, unit and all: "i meant 8 not 5" after
    # "lose 5 kilos" answers "8 kilos, not 5".
    if not unit:
        there = re.search(r"(?<![\d.])" + re.escape(number) + r"(\s+[a-z]+)?", fixed, re.I)
        if there and there.group(1):
            shown[0] = number + there.group(1)
    known = user(memory)
    known["plan"] = fixed
    plans = known.get("plans")
    if isinstance(plans, list):
        known["plans"] = [fixed if p == plan else p for p in plans]
    note(memory, fixed)
    return {"key": "plan", "value": shown[0], "wrong": str(wrong).strip()}

NUMBER_DIGITS = re.compile(r"[£$€]?\d+(?:[.,]\d+)?")

def _number_in(value):
    """The digits of a value, so "£500" and "500" are the same number."""
    match = NUMBER_DIGITS.search(str(value or ""))
    return match.group(0).lstrip("£$€").strip() if match else ""

def _correct_a_persons_name(memory, target, text="", wrong=""):
    """A name given for somebody else is put right when the right name is said.

    "my sister is called ana" and then "actually its anna" is the same sister spelled right, not
    a second person: the name is filed against the person, and "what is my sister called" answers
    from it, so it is the filed name that moves. Only a line that gave one person a name and
    nothing else is corrected, and only with a single word that reads as a name, so "my sister is
    called ana" then "i meant the plumber" corrects nothing, and no pet or the person typing is
    touched here - those have their own paths and are answered before this one.
    """
    new = " ".join(str(target or "").split())
    if not new or not extract.NAME_WORD.match(new) or new.lower() in extract.NOT_A_NAME:
        return None
    taken_back = " ".join(str(wrong or "").strip().lower().split())
    # The line names both halves ("its hannah not anna"), so the person it is about is the one the
    # store keeps under the name taken back, not the one named last. In a chat with two people
    # ("my sister is called anna and my brother is called tom") the last person named is the
    # brother, and the new name belongs to the sister - so the name on record decides it, and the
    # store never gives one person's new name to another.
    if taken_back and taken_back != new.lower():
        moved = _a_name_the_store_keeps(memory, taken_back, new)
        if moved is not None:
            return moved
    said = str(last_user(memory) or "")
    named = [entry for entry in (extract.extract(said).get("others") or [])
             if isinstance(entry, dict) and entry.get("who") and entry.get("name")]
    if len(named) != 1:
        return None
    who = str(named[0]["who"])
    old = str(named[0]["name"])
    was = [str(one) for one in (named[0].get("was") or [])]
    if old.lower() == new.lower():
        return None
    # The right name is a spelling of the old one, not another word in its place: people put
    # right a name they said wrong (ana/anna, lily/lilly, sam/sammy, jo/josephine), and a line
    # that says "its fine" or "its sunday" after a name is saying something else about the
    # sister, not renaming her. So the new word has to look like the one it replaces - unless
    # the line named the old one too ("its hannah not anna"), because then the person has said
    # themselves that the two names are the same sister and a whole new name is not a guess -
    # and the line says, in as many words, that this is the name: "my son is called jack", then
    # "no hes called dave", is a name given, and the letter test alone refused it and let the
    # turn be answered by a small-talk line that said the new name back as if it had not been
    # heard. "no he isn't, it's Dave" names the person again with no "called" in it, and it is
    # the same licence - "no its dave", "i meant dave", "sorry, dave" too.
    taken_back = str(wrong or "").strip().lower()
    if (not _a_spelling_of(new, old) and taken_back != old.lower()
            and taken_back not in [one.lower() for one in was]
            and not (_a_new_name_was_said(new, text) and _a_name_for_a_person(new))):
        return None
    for entry in others(memory):
        if isinstance(entry, dict) and entry.get("who") == who and entry.get("name"):
            entry["name"] = new
            entry["was"] = [one for one in ([str(o) for o in (entry.get("was") or [])] + [old])
                            if one.lower() != new.lower()]
            said_back = old[:1].upper() + old[1:]
            return {"key": "person_name", "value": new, "wrong": said_back, "from": old}
    return None

def _a_spelling_of(new, old):
    """Whether a word reads as another go at the same name: the same first letter, and close.

    A month or a weekday is never a name, so a word the date readers already take is refused
    even when it is a letter or two from the name.
    """
    one = str(new or "").strip().lower()
    other = str(old or "").strip().lower()
    if not one or not other or one[0] != other[0]:
        return False
    if one in extract.MONTHS or one in extract.DAYS:
        return False
    if one.startswith(other) or other.startswith(one):
        return True
    return _letters_apart(one, other) <= SPELLING_APART

def _letters_apart(one, other):
    """How many single letters have to be added, dropped or changed to turn one into other."""
    if len(one) < len(other):
        one, other = other, one
    before = list(range(len(other) + 1))
    for i, letter in enumerate(one, 1):
        after = [i]
        for j, other_letter in enumerate(other, 1):
            after.append(min(before[j] + 1, after[j - 1] + 1,
                             before[j - 1] + (letter != other_letter)))
        before = after
    return before[-1]

def _correct_clock(memory, target, text="", wrong=""):
    """A clock inside a plan is put right: "the meeting is at 10am" then "make it 2pm".

    The plan keeps everything else it says and takes the new time, so "what time is the
    meeting" answers with the hour they corrected it to. It could not be done by putting the
    figure right: a figure in a plan was swapped on a word boundary, and `\b10\b` does not find
    the 10 in "10am", so the store said "Meeting at 10am - got it" over a plan it had left as
    it was. A bare figure is a clock only where the plan's own clock names no half of the day
    ("dinner at 8" then "make it 9"): beside "at 10am", "make it 2" could be either.
    """
    new = extract.a_clock_time(target)
    bare = "" if new else _a_bare_hour(target)
    if not new and not bare:
        return None
    known = user(memory)
    plans = [p for p in (known.get("plans") or []) if isinstance(p, str) and p.strip()]
    latest = known.get("plan")
    if isinstance(latest, str) and latest.strip() and latest not in plans:
        plans.append(latest)
    if wrong:
        # A correction that names the old clock ("2pm not 10am") moves the plan that says it.
        named = [p for p in plans if _clock_key(extract.the_clock_in(p)) == _clock_key(wrong)]
        plans = named or plans
    for plan in reversed(plans):
        found = extract.the_clock_in(plan)
        if not found:
            continue
        old = " ".join(found.group(0).split())
        if not new:
            if _names_a_half_of_the_day(old):
                continue  # "at 10am" needs a new time that says am or pm
            new = bare
        if _clock_key(old) == _clock_key(new):
            return None  # the plan already says it, so nothing was taken back
        fixed = (plan[:found.start()] + new + plan[found.end():]).strip()
        remember(memory, "plan", fixed, text)
        held = known.get("plans")
        if isinstance(held, list):
            known["plans"] = [fixed if str(p) == plan else p for p in held]
        return {"key": "plan", "value": fixed, "from": old}
    return None

def _the_topic_with_the_new_clock(text, plan_now):
    """The topic's own line with the plan's new clock in it, or None when the two are not the
    same line.

    "im flying at 6am" beside a plan that now reads "im flying at 7am" is the same sentence with
    the hour they meant: the topic takes the new hour and keeps the words the person used, so the
    next turn is read against one line and not against the hour that was taken back. A plan about
    something else ("Meeting at 2pm" beside "the meeting is at 10am") is not the topic's line, and
    nothing is moved: the answer to that one comes from the plan itself ("At 2pm.").
    """
    said = " ".join(str(text or "").lower().split())
    plan = " ".join(str(plan_now or "").lower().split())
    if not said or not plan:
        return None
    was, now = extract.the_clock_in(said), extract.the_clock_in(plan)
    if not was or not now or _clock_key(was.group(0)) == _clock_key(now.group(0)):
        return None
    # The store holds a plan in the second person ("your flight is at 9.15am") and the person said
    # it in the first ("my flight is at 8.30am"), so the two sides are compared with the small
    # words and the person taken off: "flight" is what says it is the same line.
    def words(line, found):
        rest = " ".join((line[:found.start()] + line[found.end():]).split())
        return [word for word in rest.split()
                if word not in ("my", "your", "our", "the", "a", "an", "im", "i", "you",
                                "is", "are", "its", "at")]
    if words(said, was) != words(plan, now):
        return None
    fixed = (text[:was.start()] + now.group(0) + text[was.end():]).strip()
    return fixed

BARE_HOUR = re.compile(r"^(\d{1,2})$")

def _a_bare_hour(value):
    """The hour a bare figure could be, or "" when it is not one."""
    match = BARE_HOUR.match(str(value or "").strip())
    if not match or not 1 <= int(match.group(1)) <= 24:
        return ""
    return match.group(1)

def _names_a_half_of_the_day(clock):
    """True when a clock says which half of the day it is in ("10am", "noon")."""
    return bool(re.search(r"am|pm|o'?clock|noon|midday|midnight", str(clock or ""), re.I))

def _clock_key(clock):
    """A clock with everything but its figures and letters taken out, so 10am is 10am."""
    return re.sub(r"[^0-9a-z]", "", str(clock or "").lower())

def _correct_number(memory, target, text=""):
    """A number is not a fact of its own either: it belongs to whatever the line before it
    was about, so "my budget is 500" then "make that 800" moves the budget, and the user does
    not have to name the thing again. Only a field that really holds the old number is moved,
    so a stray digit somewhere in the line corrects nothing.
    """
    new = " ".join(str(target or "").split())
    digits = _number_in(new)
    if not digits:
        return None
    if _names_a_date(new):
        # A value that states a date is a date, and the date reader has already had it: the 5 in
        # "the 5th of june" is not a figure that took the place of another one. Read as one it
        # moved the hour of "the dentist is on tuesday at 9" to 5, and the recall said "your
        # dentist is at 5 on Tuesday" over a line that said nine.
        return None
    said = " ".join(str(last_user(memory) or "").split())
    if not said or _a_birthday_on_the_last_line(memory):
        # A birthday is the one fact kept as a date, and the number in it is a day of the month,
        # so it is the date reader's to move and not a plan's number to swap: "my birthday is
        # on 3 may" / "sorry its the 4th" moved the 3 in the line it was said in and left the
        # birthday on the 3rd. Answering None here lets `_correct_fact` read it as the date.
        return None
    olds = [n for n in re.findall(r"\d+(?:[.,]\d+)?", said) if n != digits]
    if not olds:
        return None
    known = user(memory)
    for old in olds:
        for key in ("budget", "age", "height", "weight"):
            value = known.get(key)
            if value is not None and _number_in(value) == old:
                # The new value is kept the way the old one was: an age is a number the recall
                # reads as one, so "34" corrected to "43" is 43, not the word "43", and a
                # weight keeps its unit ("90 kilos" corrected to "88 kilos", not a bare "88").
                if isinstance(value, str) and re.search(r"\d", value):
                    same = re.sub(r"\d+(?:[.,]\d+)?", digits, value, count=1)
                else:
                    same = int(digits) if isinstance(value, int) else digits
                remember(memory, key, same, text)
                kept = known.get(key)
                shown = kept if kept not in (None, "") else same
                return {"key": key, "value": shown, "from": old}
        for key in ("plan", "job"):
            value = known.get(key)
            if isinstance(value, str) and old in value and digits not in value:
                fixed = re.sub(r"\b" + old + r"\b", digits, value, count=1)
                if fixed == value:
                    # The old number is only part of a longer word, so this line is not the
                    # number's: "my birthday is the 3rd of may" / "sorry, the 4th" found the
                    # 3 inside "3rd", put nothing in its place and still claimed the
                    # correction - so the birthday kept the day it was just taken back from
                    # and the note read the old line out again. The date it holds is put
                    # right by the date reader, as the fact it is. A figure written against a
                    # word ("10am") is the same case from the other side: nothing moved, and a
                    # change that changes nothing is not a correction - reported as one it said
                    # "Meeting at 10am - got it" over a plan still holding the old clock, and the
                    # next reader never ran.
                    continue
                # The line the plan was said in is what says it back. Keeping the correction
                # instead ("sorry, i meant 5") leaves the plan with no sentence of its own, and
                # the phrase alone answers "what am i up to?" with "Your leave for the airport
                # is at 5": the number moves inside that line, the way a date does.
                told = text
                if key == "plan":
                    origin = plan_line(memory, value)
                    told = (_swap_in(origin, digits, old) if origin else "") or text
                remember(memory, key, fixed, told)
                plans = known.get("plans")
                if key == "plan" and isinstance(plans, list):
                    known["plans"] = [fixed if str(p).lower() == value.lower() else p
                                      for p in plans]
                if key == "plan":
                    # A number moved inside a plan corrects the plan, and the note says the
                    # sentence the plan now reads in their own words ("Got it - you have to
                    # leave for the airport at 5"), so the store's own reply is about the plan
                    # as it stands rather than the line the number was said in.
                    return {"key": "plan", "value": fixed, "sentence": told, "from": old}
                return {"key": "line", "value": fixed[:1].lower() + fixed[1:], "from": old}
    return None

COUNT_SAID = re.compile(r"\b(" + "|".join(sorted(extract.PET_COUNT_WORDS, key=len, reverse=True))
                         + r"|\d{1,2})\b", re.I)

def _count_said(text):
    """The number a line says, as a number: "3", "three cats", "a couple of dogs"."""
    match = COUNT_SAID.search(" ".join(str(text or "").lower().split()))
    if not match:
        return 0
    word = match.group(1).lower()
    if word.isdigit():
        return int(word)
    return int(extract.PET_COUNT_WORDS.get(word) or 0)

def _a_count(count, animal):
    """A count of an animal said back as a person says it: "three cats", "two fish"."""
    animal = str(animal or "pet").strip().lower()
    if animal.endswith(("fish", "sheep", "deer")) or count == 1:
        many = animal          # one cat, one child, two fish - "1 cats" is not said
    else:
        many = animal + "s"
    return "{} {}".format(count, many)

def _correct_count(memory, target, text=""):
    """A count of an animal already on the store is put right by saying the new count.

    "we have two cats" then "sorry, 3 cats" is the same house with one more cat, not a second
    animal: the store keeps one record per animal, so the number in that record is what moves.
    A bare "no, 3" moves the count of the animal the line before it named, the way "make that
    800" moves a budget, and only when that line gave a count for the same animal to replace -
    "i have a cat" then "no, 3" says nothing about how many, so nothing is guessed at.
    """
    new = _count_said(target)
    if new < 1 or new > 30:
        return None
    held = [pet for pet in (user(memory).get("pets") or []) if isinstance(pet, dict)]
    if not held:
        return None
    said = " ".join(str(last_user(memory) or "").lower().split())
    named = [str(pet.get("animal") or "") for pet in (extract.extract(str(target or ""))
                                                      .get("pets") or [])]
    if not named:
        named = [str(pet.get("animal") or "") for pet in (extract.extract(said).get("pets") or [])]
    named = [animal for animal in named if animal]
    if not named:
        return None
    # The count being replaced has to be one the line before it gave for that animal: "my cat is
    # 3" is an age, and "no, 5" after it says nothing about how many cats there are.
    told = [pet for pet in (extract.extract(said).get("pets") or []) if pet.get("count")]
    old = int(told[0]["count"]) if told else 0
    if not old or old == new:
        return None
    for pet in reversed(held):
        if _animal_family(pet.get("animal")) != _animal_family(named[0]):
            continue
        pet["count"] = new
        return {"key": "pets_count", "value": _a_count(new, pet.get("animal")),
                "from": _a_count(old, pet.get("animal"))}
    return None

ANY_NUMBER = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"\w+teen|twenty|thirty|forty|fifty|hundred)\b", re.I)

BARE_NEW_COUNT = re.compile(
    r"^\W*(?:(?:ok|okay|ah|oh|right)\b[,.]?\s*)*"
    r"(?:(?:no|nope|sorry|actually|oops|wait|hold\s+on|hold\s+up|hang\s+on)\b[,.]?\s*"
    r"|i\s+mean(?:t)?\s+|make\s+(?:that|it)\s+)+"
    # A count on its way back is usually hedged - "actually just one", "no, only 2" - and the
    # hedge sits where the number should start, so the shape stopped and the store kept the old
    # count: "i have two kids" then "actually just one" still said two children. Only a number
    # may follow the hedge, so "no just checking" stays the shrug it was.
    r"(?:(?:just|only|about|around|roughly|nearly|exactly)\s+(?:the\s+)?)?"
    r"(?:(?:it'?s|its|that'?s|thats)\s+)?"
    r"(?P<count>\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\w+teen)\b"
    r"\s*(?:now\b)?\s*[.!]?$", re.I)

def _correct_the_count_on_the_table(memory, target, text=""):
    """Put a corrected count on what the line before it counted.

    "i have two kids" then "actually three" is the same household with one more child: the store
    already keeps the count under the thing counted, so a line that only says the new number
    moves that number and the person does not have to name the thing again. Only a line that is
    nothing but the new number counts, and only when the line before it gave one number - "i have
    two kids and 3 dogs" then "no, 4" says nothing about which of them is 4. A count of an animal
    never gets here: `_correct_count` reads it first and knows the animal the line named.
    """
    line = BARE_NEW_COUNT.match(" ".join(str(text or "").split()))
    if not line:
        return None
    new = _count_said(line.group("count"))
    if not 0 < new <= 30:
        return None
    said = " ".join(str(last_user(memory) or "").split())
    if not said or len(ANY_NUMBER.findall(said)) > 1:
        return None
    known = user(memory)
    counted = extract.extract(said).get("kids")
    if not isinstance(counted, int) or not isinstance(known.get("kids"), int):
        return None
    if counted == new:
        return None
    old = known["kids"]
    remember(memory, "kids", new, text)
    return {"key": "kids", "value": _a_count(new, "kid"), "from": _a_count(old, "kid")}

# The going a line says with the date names what kind of thing moved, so it is also what the move
# must land on. "im booking a trip to croatia in july" / "my mums birthday is 2 april" / "actually
# we fly out in october" moved the birthday to 2 October, because the birthday was the newest date
# in the store and every date held looked the same to the reader: the person's fact came back
# wrong ("when is my mums birthday" -> "2 October"), and once a fact is put wrong a later turn
# hands it back with a confident frame. A going of flying or travelling is about a journey, and a
# date kept for somebody else is never the journey on the table.
A_JOURNEY_GOING = re.compile(
    r"\b(?:fly|flies|flying|flight|flights|travel|travels|travelling|traveling|trip|trips"
    r"|holiday|holidays|booking|booked|visit|visiting|journey|outing)\b", re.I)


def _a_fact_of_somebody_else(memory, plan):
    """Whether a plan is a date kept for another person ("mums birthday on 2 april"), not a plan.

    The store says whose it is in `others`, so the person's own word for them ("mum", "son") in
    the plan is what marks it: their birthday is a fact about them, and a trip of the person's own
    is not.
    """
    said = " ".join(str(plan or "").lower().split())
    if not said:
        return False
    for entry in (memory or {}).get("others") or []:
        who = str((entry or {}).get("who") or "").strip().lower()
        if not who:
            continue
        word = who.split()[0]
        if re.search(r"\b" + re.escape(word) + r"(?:'?s)?\b", said):
            return True
    return False


def _the_plans_a_journey_moves(memory, plans, text):
    """The plans a line about a journey can move, or None when the line names no journey.

    None means the line names no going of that kind, so every date held is a candidate the way it
    always was ("make it july", "no, in august").
    """
    if not A_JOURNEY_GOING.search(str(text or "")):
        return None
    return [one for one in plans if not _a_fact_of_somebody_else(memory, one)]


def _correct_when(memory, target, text=""):
    """A month or a day is not a fact of its own: it lives inside the plan the line before it
    stated, so "my holiday is in june" then "make that july" moves the holiday to July. The
    old month is the one that plan holds, which is why the user does not have to name it.
    """
    low = str(target or "").lower()
    if low not in extract.MONTHS and low not in extract.DAYS:
        return None
    known = user(memory)
    plans = [p for p in (known.get("plans") or []) if isinstance(p, str) and p.strip()]
    latest = known.get("plan")
    if isinstance(latest, str) and latest.strip() and latest not in plans:
        plans.append(latest)
    group = extract.MONTHS if low in extract.MONTHS else extract.DAYS
    journeys = _the_plans_a_journey_moves(memory, plans, text)
    if journeys is not None:
        # A journey was named, so a person's fact is not one of the things it can move. With no
        # journey in the store the move is left alone rather than landing on the nearest date
        # held: a fact put wrong cannot be taken back by a later turn.
        if not journeys:
            return None
        plans = journeys
    for plan in reversed(plans):
        for word in re.findall(r"[a-z]+", plan.lower()):
            if word in group and word != low:
                fixed = re.sub(r"\b" + word + r"\b", target, plan, count=1, flags=re.I)
                # The line the plan came from is the line they stated it in, not the correction:
                # "we're going to spain in july" then "make it august" is said back as "You're
                # going to spain in August", and never as the change ("You moved it to august").
                told = _plan_told_line(memory, plan, fixed, text)
                remember(memory, "plan", fixed, told)
                plans_list = known.get("plans")
                if isinstance(plans_list, list):
                    # The corrected plan replaces the old one, so "when do I start?" has one
                    # answer, the new one.
                    known["plans"] = [fixed if str(p).lower() == plan.lower() else p
                                      for p in plans_list]
                # The move is said as the plan it now stands, never as the month on its own: "im
                # going to spain in june" then "actually we fly in july now" was answered "Got it
                # - July.", which is the same month with the trip taken out of it.
                read_back = plan_sentence(fixed, told)
                if read_back.lower().startswith("you're planning "):
                    read_back = ""
                return {"key": "plan", "value": fixed.rstrip(" ."),
                        "from": word[:1].upper() + word[1:], "sentence": read_back}
    return None

DATE_DAY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b", re.I)

A_DAY_BEFORE_A_MONTH = re.compile(
    r"\b(?:the\s+)?(\d{1,2})\s+(?:of\s+)?(?:%s)\b" % "|".join(
        sorted((re.escape(name) for name in extract.MONTHS), key=len, reverse=True)), re.I)

def _date_said(low):
    """The day and the month a value states, either of them None."""
    day = DATE_DAY.search(low)
    month = None
    for name in sorted(extract.MONTHS, key=len, reverse=True):
        if re.search(r"\b" + name + r"\b", low):
            month = name
            break
    if day is None and month:
        # "no, 4 june" is the fourth of June, and it was read as June alone: the day they said
        # was dropped and the old day kept, so "3 may" then "4 june" gave "3 June".
        bare = A_DAY_BEFORE_A_MONTH.search(low)
        if bare:
            return bare.group(1), month
    return day.group(0) if day else None, month

def _a_day_in_the_kind(old_day, day):
    """A day written the way the plan already writes its days: "3 may" put right stays a number.

    "my sons birthday is 3 may" then "sorry, its the 4th of may" kept the plan's day as "4th",
    which reads fine but is a different kind of day from the one the plan had, so the store's
    own value changed shape for no reason. An ordinal plan keeps the ordinal, a plain one the
    number.
    """
    number = re.match(r"(\d{1,2})", str(day or ""))
    if not number:
        return _date_word_case(day)
    if re.match(r"\d{1,2}(?:st|nd|rd|th)$", str(old_day or ""), re.I):
        count = int(number.group(1))
        suffix = "th" if 11 <= count % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(
            count % 10, "th")
        return number.group(1) + suffix
    return number.group(1)

def _date_word_case(value):
    """"july" is written "July", and a day said as "13th" is left as it is said."""
    text = str(value or "")
    return text[:1].upper() + text[1:] if text[:1].isalpha() else text

def _date_in_plan(plan):
    """The day and the month the plan already says, either of them None."""
    return _date_said(str(plan or "").lower())

WEEKDAY_IN_PLAN = re.compile(
    r"\b(?:(?:this|next|last|coming|the)\s+)?(?:" +
    "|".join(sorted(extract.DAYS - {"weekend"}, key=len, reverse=True)) + r")\b", re.I)

def _the_weekday_in(plan):
    """The weekday a plan says its day as, or None ("the dentist is on tuesday at 9")."""
    return WEEKDAY_IN_PLAN.search(str(plan or ""))

def _names_a_date(value):
    """True when a value states a date: a month, or a day of the month ("5 june", "the 5th")."""
    day, month = _date_said(str(value or "").lower())
    return bool(day or month)

RELATIVE_MONTH = re.compile(r"\b(?:next|this|that|the\s+following|the\s+coming|the\s+next)\s+month\b",
                            re.I)

def _a_relative_month(plan, day, month):
    """The plan with a relative month replaced by the month they named, and what moved.

    "Rome next month" and "no in july" gives "Rome in July": the preposition is added with
    the month, because the plan said when with no preposition of its own. A day with it
    ("no, the 12th of july") writes both, and the relative words go.
    """
    if not month or not isinstance(plan, str):
        return None
    found = RELATIVE_MONTH.search(plan)
    if found is None:
        return None
    said = _date_word_case(month)
    if day:
        # A day and a month are said the way people say them: "on the 12th of July".
        said = "on the {day} of {month}".format(day=day, month=said)
    else:
        said = "in " + said
    fixed = (plan[:found.start()] + said + plan[found.end():]).strip()
    fixed = " ".join(fixed.replace(" ,", ",").split())
    return fixed, found.group(0).lower(), said

def _a_relative_line(memory, plan, was, said):
    """The line the plan was stated in, with the relative date said as the date they mean.

    "im going to rome next month" and "no in july" gives "im going to rome in July", which
    plan_sentence says back as "You're going to rome in July".
    """
    told = plan_line(memory, plan)
    if not told or not was or not said:
        return None
    return re.sub(r"\b" + re.escape(was) + r"\b", said, told, count=1, flags=re.I)

def _plan_saying(memory, day, month):
    """The plan in the store that says the date being taken back, or None.

    "im going to portugal in june" / "my sons birthday is in august" / "sorry, july not
    june" is the trip that is wrong, not the birthday: the value they name as wrong says
    which plan the correction is about. The newest plan that says it wins.
    """
    if not day and not month:
        return None
    plans = [p for p in ((memory.get("user") or {}).get("plans") or []) if isinstance(p, str)]
    for plan in reversed(plans):
        found_day, found_month = _date_in_plan(plan)
        if month and found_month != month:
            continue
        if day and found_day and found_day != day:
            continue
        return plan
    return None

def _correct_date(memory, target, text="", wrong=""):
    """A date said again moves the date in the plan it belongs to, part by part.

    "im going to portugal on the 12th of june" / "sorry i meant the 13th of june" moves the day;
    "sorry i meant the 13th" moves the day and keeps June, because a month nobody took back is
    still the month. Nothing is moved on a value that names no day and no month, and a plan that
    says neither is not a plan this reader can fix.
    """
    low = str(target or "").lower()
    day, month = _date_said(low)
    if not day and not month:
        return None
    if _a_birthday_on_the_last_line(memory):
        # A plan is not the only thing a date can be moved in: "the 4th may" after "the 3rd may"
        # is the birthday they just told us, and the store keeps it as a date of its own.
        return None
    plan = _stated_plan(memory) or user(memory).get("plan")
    # The date they took back says which plan is meant: "sorry, july not june" after the trip
    # and then a birthday moves the trip, because the trip is the plan that says June.
    gone_day, gone_month = _date_said(str(wrong or "").lower())
    saying = _plan_saying(memory, gone_day, gone_month)
    if saying:
        plan = saying
    if not isinstance(plan, str) or not plan.strip():
        return None
    old_day, old_month = _date_in_plan(plan)
    fixed, moved = plan, []
    told = None
    if not old_day and not old_month:
        # A plan can say when in relative words, and a month named later is that date said
        # again: "im going to rome next month" / "no in july" is Rome in July, and the month
        # was going into the plan's place instead ("you're going to In july next month").
        # Only a whole month moves this way: a day on its own ("no, the 12th") has no month
        # to sit in, so it is left to the readers that know what it belongs to.
        weekday = _the_weekday_in(plan)
        if day and month and weekday:
            # A plan that says its day as a weekday is moved to the date they name: "the dentist
            # is on tuesday at 9" put right by "the 5th of june" is the dentist on the 5th of
            # June at 9. Nothing was moved here before - no reader thought a weekday was a date
            # a date could replace - so the weekday stood, the number reader moved the hour
            # instead, and the recall said "at 5 on Tuesday".
            said = "the {day} of {month}".format(day=_date_word_case(day),
                                                 month=_date_word_case(month))
            fixed = " ".join((plan[:weekday.start()] + said + plan[weekday.end():]).split())
            was = weekday.group(0).lower()
            moved.append(was)
        else:
            relative = _a_relative_month(plan, day, month)
            if relative is None:
                return None
            fixed, was, said = relative
            moved.append(was)
        # The line they said it in is the one the plan is said back with, and it still carries
        # the relative words, so the date moves in that line too: "You're going to rome in
        # July". Without it the correction had no sentence to say, and the when answer went
        # back to the line that said "next month".
        told = _a_relative_line(memory, plan, was, said)
    if day and not old_day and old_month:
        # The plan said the month and no day, and the date they put right names a day: the day
        # goes into the month the plan already holds - "my exam is in june" / "sorry, it's the
        # 4th" is the 4th of June, because the month nobody took back is still the month. The
        # preposition the plan was said with is kept, so "save 500 by june" becomes "by the 4th
        # of june" and never "by on the 4th of june".
        with_a_day = re.compile(r"\b(in|on|for|by|until|till|from|around|before|after)\s+"
                                r"(?:the\s+)?" + re.escape(old_month) + r"\b", re.I)
        found = with_a_day.search(fixed)
        if found:
            join = "on" if found.group(1).lower() == "in" else found.group(1).lower()
            fixed = (fixed[:found.start()] + join + " the " + _date_word_case(day) + " of "
                     + _date_word_case(old_month) + fixed[found.end():])
            moved.append(old_month)
    if day and old_day and day.lower() != old_day.lower():
        # A day or a month is written as a word, not as the person's chat-speak: "we moved it
        # to july" gives "Portugal in July", and the sentence it was said in reads in kind. A
        # day keeps the kind the plan writes it in, so "3 may" put right by "the 4th" is "4 may"
        # and not "4th may" - the store's own value should not change shape on a correction.
        fixed = re.sub(r"\b" + old_day + r"\b", _a_day_in_the_kind(old_day, day), fixed,
                       count=1, flags=re.I)
        moved.append(old_day)
    if month and old_month and month != old_month:
        fixed = re.sub(r"\b" + old_month + r"\b", _date_word_case(month), fixed, count=1, flags=re.I)
        moved.append(old_month)
    if fixed == plan:
        return None
    # A move of the whole month ("we moved it to july") carries the line the plan was stated
    # in, with the date put right in it: "You're going to portugal in July", never "You moved
    # it to july" - the change is not a plan of its own and says nothing about the trip.
    if told is None:
        told = _plan_told_line(memory, plan, fixed, text)
    remember(memory, "plan", fixed, told)
    known = user(memory)
    plans_list = known.get("plans")
    if isinstance(plans_list, list):
        # One plan, one answer: the corrected one replaces the plan it came from.
        known["plans"] = [fixed if str(p).lower() == plan.lower() else p for p in plans_list]
    # The plan is kept as the sentence it was said in, so it may end with a full stop of its
    # own ("I'm going to Portugal in June.") - the note adds one, so the value says it without.
    # The note says the plan as it now stands, in the words they used for it, so "Got it -
    # you're seeing the solicitor on Tuesday." and never their own chat-speak read back.
    # Only a line that already reads as something they are doing is said back in the second
    # person; a plan the bot can only say as "You're planning the 13th of June" is said as the
    # plan itself.
    read_back = plan_sentence(fixed, told)
    if read_back.lower().startswith("you're planning "):
        read_back = ""
    return {"key": "plan", "value": fixed.rstrip(" ."), "from": " ".join(moved),
            "sentence": read_back}

CORRECTABLE = frozenset(("name", "age", "city", "places", "job", "diet", "allergies", "height",
                         "weight", "budget", "pet", "pets", "plan", "birthday"))

def _a_name_the_store_keeps(memory, taken_back, new):
    """The correction that moves the name of the one person the store keeps under it.

    "my sister is called anna and my brother is called tom" then "its hannah not anna": the name
    taken back is on record for the sister, so it is her name that moves - the person named last
    in the chat is not the one being put right.
    """
    for entry in others(memory):
        if not isinstance(entry, dict) or not entry.get("name"):
            continue
        if str(entry["name"]).strip().lower() != taken_back:
            continue
        if not _a_name_for_a_person(new):
            return None
        before = str(entry.get("name") or "")
        entry["name"] = new
        if before and before.lower() != new.lower():
            was = [str(old) for old in (entry.get("was") or []) if str(old).lower() != new.lower()]
            entry["was"] = was + [before]
        entry.pop("turns", None)
        log(memory).append({"key": "other", "value": dict(entry),
                            "turn": len(memory.get("turns") or []),
                            "text": "my %s is called %s" % (entry.get("who"), new)})
        return {"key": "person_name", "value": new,
                "wrong": taken_back[:1].upper() + taken_back[1:], "from": taken_back}
    return None

def _stated_last(memory):
    """The key of the fact the correction fixes, or None.

    A correction fixes the thing just said, and that is usually the previous line. It is not
    always: people ask about a fact first and correct it once they hear it back ("im a nurse",
    "whats my job?", "no i mean a teacher"). So the lines are walked back over the questions
    between, and the search stops at the first line that said something of its own - a fact that
    cannot be corrected, or a deed - because the person has moved on and an older age is not what
    "no I mean 43" is about.
    """
    entries = memory.get("facts_log")
    if not isinstance(entries, list):
        return None
    by_line = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        said = " ".join(str(entry.get("text") or "").lower().split())
        by_line.setdefault(said, []).append(entry.get("key"))
    for line in reversed(last_user(memory, CORRECTION_BACK) or []):
        said = " ".join(str(line or "").lower().split())
        if not said:
            continue
        keys = by_line.get(said)
        if keys:
            # One line can state more than one thing (a job and the frame it was said in), and
            # only some kinds can be corrected: the value a "no i mean" fixes is the last one of
            # those the line stated, not whichever came last in the log.
            for key in reversed(keys):
                if key in CORRECTABLE:
                    return key
            if not _asks(said):
                return None  # it did state a fact, just not one a correction can replace
            # A question that happened to name someone ("what should i get my sister" keeps the
            # sister, "where shall we go in june" keeps the month) has not moved the person on:
            # "my budget is 30 quid" then that question still leaves the budget what "no, 45"
            # is about, so the walk goes on past it.
            continue
        if not _asks(said):
            return None  # a deed or a statement of its own: that is what we are on now
    return None

AMOUNT = re.compile(r"(?:[£$\u20ac]\s?)?\d[\d,]*(?:\.\d+)?"
                     r"(?:\s*(?:(?:hundred|thousand|million|grand)(?![a-z])|k(?![a-z])))?",
                     re.I)

NUMBER_WORD = re.compile(r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                         r"noon|midday|midnight)", re.I)

MONTHS = frozenset("january february march april may june july august september october november "
                   "december jan feb mar apr jun jul aug sep sept oct nov dec".split())

MONTH_WORD = re.compile(r"\b(?:" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b",
                        re.I)

MONTH_ALT = "|".join(sorted(MONTHS, key=len, reverse=True))

DATE_PHRASE = re.compile(
    r"\b(?:the\s+)?\d{1,2}(?:st|nd|rd|th)\b(?:\s+of\s+(?:" + MONTH_ALT + r"))?"
    r"|\b(?:the\s+)?\d{1,2}\s+(?:" + MONTH_ALT + r")\b"
    r"|\b(?:" + MONTH_ALT + r")\s+(?:the\s+)?\d{1,2}(?:st|nd|rd|th)?\b", re.I)

AT_TIME = re.compile(r"\bat\s+" + AT_TIME_VALUE, re.I)

DAY_WORD = re.compile(r"\b(?:" + "|".join(sorted(extract.DAYS, key=len, reverse=True))
                      + r")\b", re.I)

CURRENCY = re.compile(r"[£$\u20ac]\s?")

def _plan_told_line(memory, old, new, text=""):
    """The line to keep with a plan whose date was changed.

    A plan is said back in the words it was stated in ("You're going to portugal in July", not
    "You're planning portugal in July"), and the line they stated it in still holds the date
    they said first, so the date moves in the line too. Only a change of the date carries the
    original line: correcting the thing itself ("sorry, i meant porto") is a new line, and the
    old one would name the place they have just corrected.
    """
    told = plan_line(memory, old)
    was, now = _date_word(old), _date_word(new)
    if not told or not was or not now or was.lower() == now.lower():
        return text
    return re.sub(r"\b" + re.escape(was) + r"\b", now, told, count=1, flags=re.I)

def _date_word(phrase):
    """The month or day a phrase names, as it was written there, or "" - the value a change moves."""
    match = MONTH_WORD.search(str(phrase or "")) or DAY_WORD.search(str(phrase or ""))
    return match.group(0) if match else ""

def _kind_of_value(target, told):
    """What part of the fact's sentence a corrected value is a value of.

    "August" after "we're going to Lisbon in May" is the month, so the month moves and Lisbon
    stays. "500" after "400 pounds" is the amount, so the pounds stay. A bare number after
    "leave for the airport at 4" is the time. Anything else names the thing the line was
    about, and the place it replaces is the one the sentence carries.
    """
    low = target.lower()
    if low in MONTHS:
        return "month"
    if low in extract.DAYS:
        # A weekday is as much a value of when as a month is: "we're flying to rome on monday"
        # and "actually make that tuesday" moves the day, and Rome is still where they go.
        return "day"
    if AMOUNT.fullmatch(target) and not AT_TIME.search(told):
        return "amount"
    if AT_TIME.search(told) and (AMOUNT.fullmatch(target) or NUMBER_WORD.fullmatch(target)):
        return "time"
    if DATE_PHRASE.search(target):
        return "date"
    return None

def _swap_in(told, target, wrong=None):
    """The fact's own sentence with the corrected value in place of the one it corrects.

    "A trip to Lisbon in May" and "sorry, I meant Porto" (or "no, Porto") tells the whole
    sentence: only the place moved. "400 pounds" and "I meant 500" is 500 pounds, because the
    pounds are still how the budget is counted. A value only moves the part of the sentence it
    is a value of: "I meant August" moves the month, not the city. Nothing is swapped when the
    sentence does not carry the thing being corrected, so a correction about something else
    leaves the fact be.
    """
    if not isinstance(told, str) or not told.strip() or not target:
        return None
    target = str(target).strip()
    kind = _kind_of_value(target, told)
    if kind in ("month", "day"):
        wanted = MONTH_WORD if kind == "month" else DAY_WORD
        found = list(wanted.finditer(told))
        if not found:
            return None
        last = found[-1]
        return told[:last.start()] + target + told[last.end():]
    if kind == "amount":
        found = list(AMOUNT.finditer(told))
        if not found:
            return None
        last = found[-1]
        # A budget said in pounds is still in pounds when only the number is corrected: "400
        # pounds" and "I meant 500" is 500 pounds, not 500.
        unit = CURRENCY.match(told[last.start():])
        tail = told[last.end():]
        if unit and not CURRENCY.match(target):
            target = unit.group(0).strip() + (" " if unit.group(0).endswith(" ") else "") + target
        elif CURRENCY.match(target):
            # "£500" already says the money, so the "pounds" after the old number would be a
            # second unit: "£500 pounds" is not how anyone says it.
            tail = re.sub(r"^\s*(?:pounds?|dollars?|euros?|quid|bucks?)\b", "", tail, count=1,
                          flags=re.I)
        return told[:last.start()] + target + tail
    if kind == "date":
        found = list(DATE_PHRASE.finditer(told))
        if not found:
            return None
        last = found[-1]
        # The day (and the month, when the correction names one) moves into the plan it belongs
        # to, and the article in front of it stays lower case: "Portugal on the 12th of june" and
        # "sorry, i meant the 13th of june" is "Portugal on the 13th of june".
        said = target.lower() if target.lower().startswith(("the ", "a ", "an ")) else target
        return told[:last.start()] + said + told[last.end():]
    if kind == "time":
        found = list(AT_TIME.finditer(told))
        if not found:
            return None
        last = found[-1]
        said = last.group(0)
        half = re.search(r"(am|pm|o'?clock)\b", said, re.I)
        if half and not re.search(r"am|pm|o'?clock|noon|midday|midnight", target, re.I):
            # "my flight is at 6am" then "no, 8" is eight in the morning: the correction names
            # the figure alone, and the plan already says which half of the day it is in, so the
            # plan keeps it rather than losing the am and leaving "at 8" to mean either.
            target = target + ("" if target[-1:].isdigit() else " ") + half.group(1)
        rest = re.sub(r"^at\s+" + AT_TIME_VALUE, "at " + target, said, count=1, flags=re.I)
        return told[:last.start()] + rest + told[last.end():]
    if wrong:
        named = re.compile(r"\b" + re.escape(str(wrong).strip()) + r"\b", re.I)
        if not named.search(told):
            return None
        return named.sub(target, told, count=1)
    if not AMOUNT.fullmatch(target):
        return None
    found = list(AMOUNT.finditer(told))
    if not found:
        return None
    last = found[-1]
    return told[:last.start()] + target + told[last.end():]

def _plan_the_line_named(plans, told):
    """The plan in the list that the corrected sentence was kept as, or None.

    The plan is stored as the phrase the person used ("Portugal in june"), while the line in the
    log is the whole sentence ("im going to portugal in june"), so the one that came from this
    sentence is the entry one holds the other. Left in the list, it is a plan they have already
    corrected, and "what am I up to?" reads both.
    """
    low = " ".join(str(told or "").lower().split())
    if not low:
        return None
    for plan in plans:
        said = " ".join(str(plan).lower().split())
        if said and (said == low or said in low or low in said):
            return plan
    return None

def _carries(value, word):
    """Whether a kept value's own wording carries `word` as a word."""
    said = " ".join(str(value or "").lower().split())
    word = " ".join(str(word or "").lower().split())
    return bool(said and word and re.search(r"\b" + re.escape(word) + r"\b", said))

def _fact_naming(memory, wrong):
    """(key, sentence) of the fact whose own wording carries the value being corrected.

    "im going to portugal in june" / "my sons birthday is in august" / "sorry, july not june":
    the month they named as wrong is in the trip, so the trip is what moves. The newest stated
    fact is the birthday, and correcting the newest one moves a plan the line never mentioned.
    Only a value the person actually names gets this reading; "make that july" names nothing and
    the fact to correct is the one just said.
    """
    value = " ".join(str(wrong or "").lower().split())
    entries = memory.get("facts_log")
    if not value or not isinstance(entries, list):
        return None
    pattern = re.compile(r"\b" + re.escape(value) + r"\b", re.I)
    for entry in reversed(entries):
        if not isinstance(entry, dict) or entry.get("key") not in CORRECTABLE:
            continue
        said = str(entry.get("text") or "")
        if pattern.search(said):
            return entry.get("key"), said
    return None

def _a_birthday_on_the_last_line(memory):
    """Whether the line before this one stated a birthday, whichever entry it was logged as.

    "my birthday is in may" is read as their birthday and as the date it names, so the log holds
    both. A correction of the date is a correction of the birthday, and the plan the same line was
    kept as is not what moves.
    """
    said = " ".join(str(last_user(memory) or "").lower().split())
    if not said:
        return False
    for entry in reversed(memory.get("facts_log") or []):
        if not isinstance(entry, dict):
            continue
        if " ".join(str(entry.get("text") or "").lower().split()) != said:
            continue
        if entry.get("key") == "birthday":
            return True
    return False

def _correct_birthday(memory, target, text=""):
    """The birthday a person gives again is the one the store keeps.

    "my birthday is 3rd may" / "sorry, its the 4th may" left the day as it first said it, so
    "when is my birthday" answered with the date they had just taken back. The date said now
    replaces the one said before, and a line that names only the month or only the day moves that
    part of it and keeps the rest - "sorry, the 4th" keeps May, because a month nobody took back
    is still the month. A line that names no date at all leaves the birthday alone.
    """
    known = user(memory)
    held = " ".join(str(known.get("birthday") or "").split())
    day, month = _date_said(" ".join(str(target or "").lower().split()))
    if not day and not month:
        return None
    old_day, old_month = _date_said(held.lower())
    day = day or old_day
    month = month or old_month
    if not day and not month:
        return None
    # A day and a month are kept together the way a date reads in a sentence, so the ask says
    # "the 4th of May" and never "4 may" back at them.
    value = day + " of " + month if day and month else (month or day)
    if value.lower() == held.lower():
        return None
    # The line the birthday was first said in is the line it is kept by, so a later correction
    # still finds the fact it belongs to.
    told = text
    for entry in reversed(memory.get("facts_log") or []):
        if isinstance(entry, dict) and entry.get("key") == "birthday":
            told = entry.get("text") or text
            break
    remember(memory, "birthday", value, told)
    return {"key": "birthday", "value": value, "sentence": _birthday_words(value)}

def _a_birthday_for_somebody(memory):
    """The person the line before this one gave a birthday to, as the store keeps them, or None.

    "my daughters birthday is the 3 may" is filed on the daughter rather than as a plan, so a
    date said again after it has to be moved on the person - the person's own birthday goes
    through `_correct_birthday`, and this is that same seam one person along.
    """
    said = " ".join(str(last_user(memory) or "").lower().split())
    if not said or "birthday" not in said and "born" not in said:
        return None
    for entry in reversed(others(memory)):
        if not isinstance(entry, dict) or not entry.get("birthday"):
            continue
        who = str(entry.get("who") or "").strip().lower()
        if not who or not re.search(r"\b" + re.escape(who) + r"s?\b", said):
            continue
        return entry
    return None

NO_SUBJECT_OF_ITS_OWN = frozenset("""
a about actually ah all also am an and anyway as at be been but by can could did do does doing
for from get gets got had has have i i'd i'll i'm i've if in into is it it's its just like made
make makes me meant meanto maybe might my no nope not of oh ok okay on or own please probably
put puts rather right said say says so sorry than that that's thats the then there these think
this those to too um us was we well were what when where which who will with would yeah yeh yes
you your
""".split())

STILL_THE_SAME_PERSON = frozenset("""
birthday bday dob born her hers he him his she their them they
""".split())

def _the_line_is_about_that_birthday(text, held, target):
    """Whether a line naming a date is about the birthday the line before it gave.

    "no the 4th" and "sorry, september" say nothing but the value, so the birthday on the table
    is what they move. A line with a subject and a verb of its own is about that thing instead:
    "my sons birthday is 3 may" then "actually we fly in september" moved the birthday to 3
    September and the flight stayed in June, because a month said again was read as a correction
    of the last date in the chat whatever the line was about. Naming the person or the birthday
    again keeps the birthday the subject.
    """
    value = set(re.findall(r"[a-z']+", str(target or "").lower()))
    left = [word for word in re.findall(r"[a-z']+", str(text or "").lower())
            if word not in NO_SUBJECT_OF_ITS_OWN and word not in value]
    if not left:
        return True
    who = str((held or {}).get("who") or "").strip().lower()
    theirs = {who, who + "s"} if who else set()
    return all(word in STILL_THE_SAME_PERSON or word in theirs for word in left)

def _correct_their_birthday(memory, target, wrong, text=""):
    """A date said again after somebody else's birthday is that person's birthday, moved.

    "my daughters birthday is the 3 may" / "no the 4th" kept the 3rd and answered "Got it. Is
    there anything you'd like a hand with?", because a bare day names no fact of its own: the
    birthday is kept on the daughter, and the reader for it only knew the person using the bot.
    The day said here moves the day and keeps the month nobody took back - the same rule the
    person's own birthday follows - and the line is said back about them, not about the user.

    Nothing moves when the value they take back is not part of that birthday: "im going to
    portugal in june" / "my sons birthday is in august" / "sorry, july not june" is the trip
    that is wrong, and the birthday the line after it gave is not the thing being corrected.
    """
    held = _a_birthday_for_somebody(memory)
    if not held:
        return None
    low = " ".join(str(target or "").lower().split())
    day, month = _date_said(low)
    if not day and not month:
        return None
    known = " ".join(str(held.get("birthday") or "").lower().split())
    old_day, old_month = _date_said(known)
    if not old_day:
        # "3 may" keeps its day as a bare number, and `_date_said` reads an ordinal ("3rd") only:
        # a month said again would otherwise drop the day the chat already had.
        bare = re.search(r"\b(\d{1,2})\b", known)
        old_day = bare.group(1) if bare else None
    gone_day, gone_month = _date_said(" ".join(str(wrong or "").lower().split()))
    if (gone_day or gone_month) and not ((gone_day and gone_day == old_day)
                                        or (gone_month and gone_month == old_month)):
        return None  # what they took back is not in this birthday: not the birthday being moved
    if not _the_line_is_about_that_birthday(text, held, target):
        # The line brought a subject of its own, so the date in it belongs to that instead: a
        # trip put right does not move the birthday the line before it gave.
        return None
    day = day or old_day
    month = month or old_month
    value = (day + (" of " if " of " in known else " ") + month) if day and month else (month or day)
    if value.lower() == known.lower():
        return None
    who = str(held.get("who") or "").strip()
    entry = {"who": who, "birthday": value}
    if held.get("name"):
        entry["name"] = held.get("name")
    remember_other(memory, entry, last_user(memory) or text)
    # The correction is the line the store keeps from now on, said about the person whose birthday
    # it is: a bare "no the 4th" is not a sentence about anybody, and the turn after it is read
    # against this one.
    line = "my " + who + "s birthday is " + ("on " if day else "in ") + value
    link = "on " if day else ""
    said_back = "your " + who + "s birthday is " + link + _birthday_words(value)
    return {"key": "birthday", "value": value, "from": known, "line": line,
            "note": "Got it — " + said_back + "."}

def _correct_fact(memory, target, wrong, text=""):
    """Replace the fact the previous line stated with the value the user corrected it to.

    The value is read in the shape its fact arrives in ("i live in Bristol", "i am 43", "my
    name is Jen"), and kept only when it reads as that same kind of fact. A wrong first value
    stays in the list of places, because "which did I say first?" still has an answer.
    """
    theirs = _correct_their_birthday(memory, target, wrong, text)
    if theirs:
        return theirs
    known = user(memory)
    # "i have 2 cats" / "sorry, 3 cats": the number is part of the fact, so a correction moves
    # it on the animal they already told us about instead of leaving the old count behind. A
    # count is no fact of its own, so this runs before the fact the last line stated is read.
    counted = extract.pet_counts(target)
    pets = [p for p in (known.get("pets") or []) if isinstance(p, dict)]
    if counted and pets:
        moved = ""
        for said in counted:
            for pet in pets:
                if _animal_family(pet.get("animal")) != _animal_family(said["animal"]):
                    continue
                if pet.get("count") == said["count"]:
                    continue
                pet["count"] = said["count"]
                moved = _many(said["count"], pet.get("animal") or "pet")
        if moved:
            known["pets"] = pets
            return {"key": "pets", "value": moved}
    named = _fact_naming(memory, wrong)
    key = named[0] if named else _stated_last(memory)
    if not key:
        return None
    if key in ("city", "places") and not extract.place_value(target):
        # A correction replaces a fact of the same kind: after "i live in bristol" the value still
        # has to be a place, so "actually, tree nuts" leaves the city alone instead of keeping a
        # food as where the person lives.
        return None
    if key != "birthday" and _a_birthday_on_the_last_line(memory):
        # The line that said the birthday also states it as a date of its own, and one line can
        # log both: a date said again after it is the birthday, whichever entry came last.
        key = "birthday"
    if key == "birthday":
        # A birthday is the one fact kept as a date, so a date said again is the correction:
        # "the 4th may" after "the 3rd may" is the same birthday, moved.
        return _correct_birthday(memory, target, text)
    known = user(memory)
    if key in ("pet", "pets"):
        # A pet's name is corrected by naming it, not by naming the animal again: "sorry, i meant
        # Rufus" renames the pet the line before introduced (or the one named "Rex" in it).
        pets = known.get("pets")
        if not isinstance(pets, list):
            return None
        for pet in reversed(pets):
            if not isinstance(pet, dict) or not pet.get("name"):
                continue
            if wrong and str(pet.get("name")).lower() != wrong.lower():
                continue
            pet["name"] = _tidy_name(target)
            return {"key": "pet", "value": pet["name"], "animal": pet.get("animal") or "pet"}
        return None
    # The fact as it is kept is the sentence to move, in its own shape ("Lisbon in May" stays
    # title case) - but only when it is the one carrying the value they named. When it is not
    # (the newest plan is a birthday in August, and the month named is June) the fact to correct
    # is the older line that named it.
    told = None
    held = known.get(key)
    if named and not _carries(held, wrong):
        told = named[1]
    if key in ("budget", "plan"):
        # A budget and a plan are kept as the sentence they arrived in, so the corrected value
        # goes into that sentence: "A trip to Lisbon in May" and "sorry, I meant Porto" is the
        # same trip to Porto, and "400 pounds" with "I meant 500" is 500 pounds, not 500.
        # Reading the value alone in a shape would lose the month, or the pounds it is counted in.
        replaced = wrong
        if not replaced and key == "plan":
            # "no, porto" names only the new place, so the one the plan was built on is what
            # moves: "Lisbon in May" became "Porto in May", and the month is still the month.
            places = [p for p in (known.get("places") or []) if isinstance(p, str)]
            replaced = places[-1] if places else None
        if key == "plan" and replaced and not extract.place_value(str(target)):
            # A correction replaces a value of the same kind. After "im going to rome in may" the
            # value is a place, so "actually its fine" leaves the trip alone instead of making the
            # trip one to "Fine" and "where am i going" answer "Fine."
            return None
        old = told if told is not None else known.get(key)
        swapped = _swap_in(old, target, replaced)
        if swapped:
            # The line the plan was said in is what says it back ("we are going to spain in
            # july" is "You're going to spain in july"), and the phrase alone has no verb to
            # say. A correction is not that line, so the value moves inside the sentence the
            # plan came from: "we are going to lisbon in may" with "sorry, i meant porto" is
            # kept as the clause "we are going to porto in may", not as "Porto in may", which
            # reads back as "You're planning to porto in may". A change of the date names no
            # old value to swap ("we moved it to august"), so the date moves in the line the
            # plan was stated in: "You're going to spain in August", never "You moved it to
            # august" - the correction is a change of the date, not a plan of its own.
            said = text
            if key == "plan":
                origin = plan_line(memory, old)
                said = (_swap_in(origin, target, replaced)
                        or _plan_told_line(memory, old, swapped, text))
            remember(memory, key, swapped, said)
            if key == "plan":
                # The list of plans is what "what am I up to?" reads, so the corrected plan takes
                # the place of the one it corrects: two plans naming two cities is the reply
                # contradicting itself. The old wording is still in the log.
                plans = [p for p in (known.get("plans") or []) if isinstance(p, str)]
                holder = _plan_the_line_named(plans, old)
                if holder is not None:
                    known["plans"] = [swapped if p == holder else p for p in plans]
                elif swapped not in plans:
                    known["plans"] = (plans + [swapped])[-6:]
                places = [p for p in (known.get("places") or []) if isinstance(p, str)]
                if replaced and _kind_of_value(target, old) is None \
                        and any(p.lower() == str(replaced).lower() for p in places) \
                        and not any(p.lower() == target.lower() for p in places):
                    # "where am I going?" is about the place they mean now, so the corrected one
                    # joins the list; the wrong one stays for "which did I say first?".
                    known["places"] = places + [target]
            note = swapped
            if key == "plan":
                # The note says the plan in the words they used for it, the same way a moved
                # date does: "we moved it to tuesday" after "im seeing the solicitor on monday"
                # is "Got it — You're seeing the solicitor on Tuesday", not their own typing
                # read back at them ("im seeing the solicitor on Tuesday").
                note = plan_sentence(swapped, said) or swapped
                if note.lower().startswith("you're planning "):
                    note = swapped
            return {"key": key, "value": target, "sentence": note}
    if isinstance(held, str) and _kind_of_value(target, held) is not None:
        # A month, a time or an amount only moves the part of the fact it is a value of, and no
        # fact here carries one: "my name is sam" and "make that july" is not a rename, and the
        # bot inventing "you're July" is worse than saying it did not follow. The same guard
        # keeps a job, a city or a diet from being renamed to a month.
        return None
    found = extract.reread(target, key)
    if not found:
        return None
    if key in ("city", "places"):
        place = found.get("city") or (found.get("places") or [None])[0]
        if not place:
            return None
        # The wrong value stays in the list: "which did I say first?" still has an answer,
        # while the one they mean now is the corrected one, and the recall says both.
        known["places"] = [p for p in (known.get("places") or []) if isinstance(p, str)]
        remember(memory, "places", [place], text)
        remember(memory, "city", place, text)
        return {"key": "city", "value": place}
    value = found.get(key)
    if isinstance(value, list):
        value = value[0] if value else None
    if value in (None, "", [], {}):
        return None
    if key == "budget":
        value = _keep_unit(value, known.get("budget"))
    if key in ("allergies", "people", "conditions"):
        _drop_wrong(known, key, wrong, target)
    remember(memory, key, value, text)
    return {"key": key, "value": value, "from": wrong}

ASK_START = re.compile(r"^\W*(?:does|did|do|is|are|was|were|can|could|would|will|has|have)\b",
                       re.I)

def _keep_unit(value, was):
    """"no, i mean 500" after "my budget is 300 pounds" is still pounds: a bare number takes the
    unit the fact it replaces was said in."""
    value = str(value or "").strip()
    if not value or re.search(r"[a-z]", value):
        return value
    unit = re.search(r"([a-z]+)\s*$", str(was or "").strip(), re.I)
    return value + " " + unit.group(1).lower() if unit else value

def _drop_wrong(known, key, wrong, target):
    """A correction said which value was wrong ("tree nuts, not peanuts"): that one goes.

    It is the difference between replacing a fact and adding to it, and it only ever touches a
    list of things the person named, never the history of where they have lived.
    """
    kept = [v for v in (known.get(key) or []) if isinstance(v, str)]
    if not kept:
        return
    doomed = {str(w).lower() for w in (wrong, target) if w}
    left = [v for v in kept if v.lower() not in doomed]
    # The wrong value can be named in words the list does not hold ("tree nuts, not peanuts"
    # after "allergic to nuts"): the value being corrected is the last one said, so a single
    # one on the list goes anyway.
    if left == kept and len(kept) == 1:
        left = []
    known[key] = left

MONTH_WORDS = frozenset("""january february march april may june july august september october
november december""".split())

def _birthday_words(date):
    """The date the way it reads in a sentence: "3rd of may" -> "the 3rd of May"."""
    said = " ".join(str(date).split())
    parts = []
    for word in said.split():
        parts.append(word.capitalize() if word in MONTH_WORDS else word)
    said = " ".join(parts)
    if not re.search(r"\d", said):
        return "in " + said  # "my birthday is in august" names no day, and "in August" says so
    # "the 3rd of May" takes the article; "4 July 1980" is the date in the order it was said and
    # putting "the" in front of it would be putting words in their mouth.
    if not re.match(r"\d{1,2}(?:st|nd|rd|th)\b", said):
        return said
    # "the 3rd May" is not how a date is said in a sentence: an ordinal with only a month after
    # it takes the "of" ("the 3rd of May"), and a date that already has one is left alone.
    if re.match(r"\d{1,2}(?:st|nd|rd|th)\s+[A-Z][a-z]+$", said):
        day, month = said.split()
        return "the %s of %s" % (day, month)
    return "the " + said

def _many(count, animal):
    """"two cats": how many animals, said the way a person says it."""
    noun = PLURAL_PETS.get(str(animal).lower(), str(animal) + "s")
    return COUNT_WORDS.get(count, str(count)) + " " + noun

ASK_START = re.compile(r"^\W*(?:(?:anyway|and|but|so|oh|right|ok|okay|sorry|just|also|well|then|"
                       r"actually|anyhow|plus)[\s,]+)*"
                       r"(?:what|whats|why|whys|how|hows|when|whens|where|wheres|who|whos|which|"
                       # "were redoing our bathroom" and "was going to be a problem" start with a
                       # past form that only asks when it is followed by a subject, not by the -ing
                       # word that makes it a verb in a statement: read as a question, a line that
                       # said what they were doing was handed back as one they asked.
                       r"whose|can|could|should|would|do|does|did|is|are|(?:was|were)(?!\s+\w+ing\b)|"
                       r"will|shall|have|has|any\b|anyone|anything)\b",
                       re.I)

def _asks(line):
    """True when the user's line is a question rather than something they told us."""
    return bool(ASK_START.match(line or ""))

