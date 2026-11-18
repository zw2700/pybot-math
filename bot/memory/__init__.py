"""The memory store: what the user and the bot have said. The conversation lane owns it.

Shared keys of the conversation's memory dict (list new ones in README.md):
- memory["turns"]: every earlier turn as {"user", "bot", "module"}; the runtime writes it.
- memory["understood"]: this turn's reading of the user's line (bot/understanding).
- memory["user"]: facts about the user, e.g. {"name": "Sam", "city": "Leeds", "allergies":
  ["nuts"], "pets": [{"animal": "dog", "name": "Biscuit"}], "budget": "6,000 pounds",
  "diet": "vegetarian" or "no dairy", "condition": ["coeliac"], "age": 34,
  "birthday": "3rd of may", "weight": "90 kilos", "plans": ["..."]}.
  Write it through remember().
- memory["asked"]: the fact the last recall question was about, {"slot", "turn"}, so an
  elided ask ("what did I say it was again?", "and what did I call him?") is answered about
  the same fact.
- memory["facts_log"]: every fact the user stated, in order: {"key", "value", "turn", "text"}.
- memory["others"]: facts about other people the user mentioned, [{"who": "son", "allergies":
  ["nuts"]}], with who "" for "he's" when no noun is named. A fact belongs to the person it is
  about, so "my son is allergic to nuts" goes here and never into memory["user"].
- memory["topic"]: what the conversation is about now, {"turn", "text", "words"}; see
  bot/memory/topics.py.
- memory["night_out"]: the place they said they went ("we went to the pub last night"),
  {"place", "turn"}, so the next line can be answered about it ("it was lovely"). It only
  counts for the turn right after the one that asked.
- memory["topics"]: every topic so far, oldest first.
- memory["return_to"], memory["returned"]: set when the user goes back to an earlier topic ("ok
  back to the boiler", "anyway, the laptop"); returned is {"text", "asked", "asks", "turn"} for
  the turn it happened, so an answer module can greet the return or answer on that topic.

Helpers every lane can use:
- user(memory) -> the user's facts (a dict), created on first use
- others(memory) -> facts about other people they mentioned (a list, created on first use)
- remember(memory, key, value, text="") -> keep a fact and log when it was said
- current(memory), expand(text, memory), is_follow_up(text, memory), keywords(text)
- resumed(memory) -> the earlier topic the user went back to on this turn, or None
- return_target(text) -> the thing a return line names ("the boiler"), or ""
- subject(memory) -> the noun phrase the conversation is about now ("birthday cake"), for
  modules that answer a follow-up; gist(text) -> that phrase for one line
- followup_reading(understood, memory): the reading with the current topic's subject put back in,
  for a follow-up ('and if I stuff it?') or a correction ('sorry, I meant Florence')
- the_thing_a_detail_belongs_to(understood, memory): an ask that names only a detail of the animal
  the store holds, read with that animal's kind beside it ('how do I stop the chewing' after a
  puppy is the puppy's chewing, not a pen at a desk); None when it lands on no entry
- a_detail_of_the_thing_we_hold(understood, memory): the same reading without the entry, True when
  the line names a detail of the animal and leaves the animal itself out
- key_subject(text, memory), same_as_before(understood, memory), already_said(memory, text)
- forms(word), content(text): a word with its verb endings on or off, and the words a line is
  about, so "saving" finds "save" and a grammar word with an ending is still grammar
- when_answer(text, memory): the date of the thing a "when ..." line asks about, from the line
  that stated it (bot/memory/when.py); None when no earlier line dates it
- remember_answer(memory, reply, keys), entry_answer(memory, topic_text): the whole answer an
  entry gave, kept so a later follow-up can still reach a sentence a trimmed answer left out
- recent(memory, n), last_user(memory), last_bot(memory),
  answer_in_hand(memory): the bot turn that answered the subject the chat is on, read back over
  an acknowledgement or two ("ok thanks" does not end what was being talked about, so the
  follow-up after it is still about the answer before the thanks)
- choice.reply_for(text, memory): when they hand the choice back ("you pick", "your call"),
  one of the options the bot offered a turn ago, read out of its own last reply
  (bot/memory/choice.py)
- reject.reply_for(text, memory): the other side of that - they turn the offer down ("nah not
  that one", "ive seen it"), and get another of the options the bot itself named
  (bot/memory/reject.py)
"""
import re

from ..understanding.kinds import VERB_FORMS, VERBISH
from ..understanding.normalize import TIME_WORDS, possessive_me
from . import facts, resize, topics
from .filler import without_filler
from .facts import COUNTRIES, DETERMINERS, NOT_PLACES, MONTHS, PREPOSITIONS
from .topics import (PERSON_TROUBLE, trouble)
from .topics import (KIND_ASK, WHO_SAID, a_detail_of_the_thing_we_hold, about, action,
                     already_said, answer_in_hand,
                     asks_only, bare_question, content, context, current,
                     entry_answer, expand, forms, followup_reading, gist, has_time,
                     introduction_question, is_follow_up, key_subject, keywords, left_for_a_blank,
                     meal_follow_up, note, person, person_named, remember_answer, resumed,
                     return_target, said_again, answer_about, answers_about_another_creature,
                     same_as_before, sized_reply, stem, subject, the_animal_the_subject_is,
                     the_ask_about_the_thing_it_points_at, the_thing_a_detail_belongs_to,
                     the_step_back_takes_its_words_back, the_thing_it_is, topic_text,
                     written_out)

LIST_FACTS = ("places", "allergies", "people", "plans", "condition")

# How many pets the store keeps. A line can name more than this in one go, and those are always
# kept: see the cap in `remember()`.
PETS_KEPT = 12


def user(memory):
    """The user's facts (a dict), created on first use."""
    facts_ = memory.get("user")
    if not isinstance(facts_, dict):
        facts_ = memory["user"] = {}
    return facts_


def log(memory):
    """Every fact the user stated, in the order they said it."""
    entries = memory.get("facts_log")
    if not isinstance(entries, list):
        entries = memory["facts_log"] = []
    return entries


def others(memory):
    """Facts about other people the user mentioned: [{"who": "son", "allergies": ["nuts"]}].

    A fact belongs to the person it is about: "my son is allergic to nuts" is the son's, and
    only what the user says about themselves can be recalled as their own (bot/memory/facts.py
    decides with facts.subject()).
    """
    seen = memory.get("others")
    if not isinstance(seen, list):
        seen = memory["others"] = []
    return seen


# The words that say a line is about somebody else of the same kind: "my other daughter is 2",
# "my second son is 5", "the youngest is 3 months". They come just before the word for the person.
#
# Not every word that describes a person tells a second one from the first: "my big sister is 40"
# after "my sister is 38" is the same sister, described, and reading it as another one turned one
# person into two ("Your sisters are 38 and 40"). So the words of size and of age are out: only
# the words that count, and the ones that pick the youngest or the oldest of a group, count.
ANOTHER_ONE = frozenset("""other another second third fourth youngest eldest oldest first middle
last""".split())


def _said_another(text, who):
    """Whether the line put one of those words in front of this person's word.

    The window is two words, so "my other little girl" and "the second of my sons" are read and a
    word from earlier in the sentence is not: "he turns 8 the second week of june" is one boy.
    """
    word = str(who or "").strip().lower()
    words = re.findall(r"[a-z']+", str(text or "").lower())
    if not word or not words:
        return False
    for index, one in enumerate(words):
        if one != word and one.rstrip("s") != word.rstrip("s"):
            continue
        if any(earlier in ANOTHER_ONE for earlier in words[max(0, index - 2):index]):
            return True
    return False


def _another_of_them(entry, known, text):
    """Whether this fact is about a second person of the same kind, not the one already held.

    Two people with the same word for them are told apart by a name when the chat gives one, and
    by nothing else there is: the age is all a person gives ("my daughter is 4" / "my other
    daughter is 2"), so a different age is what a second one looks like. Two ages for one word
    with no telling-apart word is the ordinary correction - "my son is 7" / "my son is 8" is one
    son of 8 - which is why the word in front of the person is what the reading turns on.
    """
    if entry.get("name") or known.get("name"):
        return False
    age, held = entry.get("age"), known.get("age")
    if not isinstance(age, int) or not isinstance(held, int) or age == held:
        return False
    return _said_another(text, known.get("who") or entry.get("who"))


def remember_other(memory, entry, text=""):
    """Keep a fact about someone else the user mentioned, merged into that person."""
    if not isinstance(entry, dict) or not any(entry.values()):
        return
    who = entry.get("who") or ""
    # Two children said under the same word are two people: "my kids are ada 7 and sam 4" is not
    # one child called Sam aged 4. A name on the entry is what tells them apart, so a named entry
    # only joins a person with the same name - or one that has no name yet.
    named = str(entry.get("name") or "").strip().lower()
    if not who and named:
        # A line that names the person and nothing else ("ada is 8", "no, sam is 5") is about the
        # person the chat already knows by that name: the name is the whole of what it says about
        # who. Two of them with that name is nobody in particular, and a name the chat has never
        # been given is nobody at all - a line about a stranger is not a fact to file.
        same = [one for one in others(memory)
                if str(one.get("name") or "").strip().lower() == named]
        if len(same) != 1:
            return
        return _fold_into(memory, same[0], entry, text)
    for known in others(memory):
        if known.get("who") != who:
            continue
        if (entry.get("name") and known.get("name")
                and str(entry["name"]).lower() != str(known["name"]).lower()):
            # Two people with the same word for them are two people: "my kids are ada 7 and sam
            # 4" is not one child whose name and age keep changing. A fact with no name of its
            # own still goes on the person the chat named.
            continue
        if _another_of_them(entry, known, text):
            # A second one of the same kind keeps its own age beside the first (see above).
            continue
        return _fold_into(memory, known, entry, text)
    kept = {key: list(value) if isinstance(value, (list, tuple)) else value
            for key, value in entry.items()}
    others(memory).append(kept)
    log(memory).append({"key": "other", "value": kept, "turn": len(memory.get("turns") or []),
                        "text": text})


def _fold_into(memory, known, entry, text=""):
    """Put one fact the line stated about a person onto the person the store already holds."""
    for key, value in entry.items():
        if key in ("who", "pronoun"):
            continue
        if key == "ages":
            # A group of ages said again is the same group said again: "my kids are 4 and 7" and
            # then "my kids are 5 and 8" is two children, not four, so the new list stands in
            # place of the old one. Extending it would answer "how old are my kids" with every
            # age the chat ever heard for them. A birthday still to come belongs to the number it
            # was said with, so it goes with a list that replaces it.
            known["ages"] = list(value)
            known.pop("age", None)
            known.pop("to_come", None)
            known.pop("turns", None)
            continue
        if key == "age" and known.get("ages"):
            # The other way round: one age said for the same word is that group said again, so
            # the list it replaces goes with it.
            known.pop("ages", None)
            known["age"] = value
            known.pop("months", None)
            known.pop("to_come", None)
            known.pop("turns", None)
            continue
        if key == "age" and isinstance(value, int) and isinstance(known.get("age"), int):
            # One of the two numbers can be a birthday still to come and the other the age they
            # are now: "my son is 7" and then "he turns 8 in june" is a seven-year-old whose
            # birthday is in june, and the store keeps both, in the order they mean. Kept as one
            # number either way, the chat answered "how old is he" a year out.
            ahead = entry.get("turns") or ""
            knew = known.get("turns") or ""
            if ahead and not knew:
                known["to_come"], known["turns"] = value, ahead
                continue
            if knew and not ahead:
                if not isinstance(known.get("to_come"), int) and known.get("age") != value:
                    known["to_come"] = known["age"]
                known["age"] = value
                if isinstance(known.get("to_come"), int) and known["to_come"] <= value:
                    known.pop("to_come", None)
                    known.pop("turns", None)
                continue
            if ahead and knew and value != known["age"]:
                known["to_come"], known["turns"] = value, ahead
                continue
        if not isinstance(value, (list, tuple)):
            known[key] = value  # a diet or a name is one thing, not a list of things
            continue
        have = known.setdefault(key, [])
        if isinstance(have, list):
            have.extend(item for item in value if item not in have)
    return known


COUNT_HEAD = re.compile(
    r"^\W*(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a few|several|"
    r"lots of|\d+)\b", re.I)


# A line that asks something does not tell us a plan, whatever the extractor made of it: "what
# do i need to know about saving" leaves "Know about saving" in the slot, and the summary then
# reads it back at them as if they had said it.
QUESTION_OPEN = re.compile(
    r"^\W*(?:what|how|why|when|where|who|which|whose|should|shall|do|does|did|can|could|is|are|"
    r"was|were|will|would|any)\b", re.I)


def reads_as_a_plan(value, text=""):
    """Whether a plan kept from a line reads well back in the summary of the chat.

    "We are going to spain in july" is a plan. "i've got two kids" comes out of the same slot as
    "Two kids", which is a count of what they have and not something they are going to do, and
    "what do i need to know" leaves the verb of the ask ("Know") behind, which is not a plan
    either - and neither is the rest of that ask, so a line that asks a question keeps nothing.
    """
    value = " ".join(str(value).split())
    if len(value.split()) < 2:
        return False
    if COUNT_HEAD.match(value):
        return False
    said = " ".join(str(text or "").split())
    if said and (said.endswith("?") or QUESTION_OPEN.match(said)):
        return False
    return True


# The words a plan carries about when it happens. Two plans that agree on everything else are the
# same thing coming up, said again - and the newer date is the one the person means.
WHEN_WORDS = frozenset("""january february march april may june july august september october
november december jan feb mar apr jun jul aug sep sept oct nov dec
monday tuesday wednesday thursday friday saturday sunday weekend
next this coming tomorrow tonight morning afternoon evening week month year the of on in at
for and on""".split())


def _the_thing_the_plan_is(plan):
    """The plan without the words that say when it happens: "my brother is coming" for both
    "my brother is coming in june" and "my brother is coming in july"."""
    words = [word for word in re.findall(r"[a-z']+", str(plan or "").lower())
             if word not in WHEN_WORDS]
    return " ".join(words) if len(words) > 1 else ""


def remember(memory, key, value, text=""):
    """Keep a fact about the user, logging when they said it."""
    if value in (None, "", [], {}):
        return
    known = user(memory)
    if isinstance(value, list):
        value = [without_filler(one) if isinstance(one, str) else one for one in value]
    if key in ("plan", "plans"):
        # The chat-speak people hang off the end of a line is not part of the plan: kept, it comes
        # back in the plan itself ("your sisters due date is in june lol") every time the store
        # says what they told you.
        if not isinstance(value, list):
            value = without_filler(value)
    if key == "plans":
        # One line can carry more than one thing coming up ("my sister is coming in may and my
        # brother in june"), so the reader hands over every plan it found, in the order said.
        for one in (value if isinstance(value, list) else [value]):
            if not reads_as_a_plan(one, text):
                continue
            plans = known.get("plans")
            if not isinstance(plans, list):
                plans = []
            if one in plans:
                continue
            # The same thing coming up, said again with another date, is the plan they mean now:
            # "my sister is coming in may and my brother in june" then "actually my brother is
            # coming in july" leaves one brother's plan, not two that disagree.
            thing = _the_thing_the_plan_is(one)
            if thing:
                plans = [kept for kept in plans if _the_thing_the_plan_is(kept) != thing]
            plans.append(one)
            known["plans"] = plans[-6:]
        log(memory).append({"key": key, "value": value, "turn": len(memory.get("turns") or []),
                            "text": text})
        return
    if key == "pets":
        pets = known.get("pets")
        if not isinstance(pets, list):
            pets = []
        # An animal they want, dislike or had once is named so the line can be said back, but it
        # is not kept: the store is what answers "what pets do i have", and a dog they do not
        # want there answers "You've got a dog". An animal on its way is kept, marked "coming",
        # because the follow-ups need it ("what do i need to buy first", "will they get on"), and
        # the sentence the store says back says it is coming instead of claiming it is here.
        value = [pet for pet in value if not (isinstance(pet, dict) and pet.get("not_theirs"))]
        if not value:
            return
        # A line that names more than one animal is a list of animals, not one animal named
        # twice: "my cats are called tom and jerry" is two cats, and the second name must not
        # rename the first.
        one_animal = len(value) == 1
        for pet in value:
            if not isinstance(pet, dict):
                continue
            # "my cat is called Milo" and then "my cat is called Max" is one cat named twice, not
            # two cats: "my cat" is the cat they have, and a line that names no second animal
            # (no "another", no "a second", no count of two) is about that one. Read as a second
            # animal it left the store answering "you've got two cats called Milo and Max", which
            # is a fact they can see is wrong. A line that does say "another" adds the animal, and
            # the number a line gives is still the number of animals.
            # A name they already have an animal under is that animal, not a rename of its
            # brother: "i have two dogs called rex and sam" and then "rex died in january" renamed
            # Sam to Rex, and the death then took both records and left the store with no dogs at
            # all. The name being new is what makes a line a rename.
            already_named = [p for p in pets if p.get("animal") == pet.get("animal")
                             and p.get("name") == pet.get("name")]
            rename = (one_animal and pet.get("name") and not pet.get("another")
                      and not already_named
                      and (pet.get("count") or 0) <= 1
                      and [p for p in pets if p.get("animal") == pet.get("animal")
                           and p.get("name") and p.get("name") != pet.get("name")
                           and not (p.get("count") or 0) > 1])
            if rename and len(rename) == 1:
                renamed = rename[0]
                log(memory).append({"key": "pet", "value": pet,
                                    "turn": len(memory.get("turns") or []), "text": text})
                renamed["name"] = pet["name"]
                if pet.get("age") and pet.get("age") != renamed.get("age"):
                    renamed["age"] = pet["age"]
                    renamed.pop("unit", None)
                    if pet.get("unit"):
                        renamed["unit"] = pet["unit"]
                continue
            # A line that says "my other cat" is a second cat, so it is only the same animal as
            # one already kept when it gives the same name: "i have a cat" files a cat with no
            # name, and the cat they name next is the other one, not that one named at last.
            # Read as the same, the unnamed first cat was swallowed and "what are my cats called"
            # answered "you've got a cat called Max" about two cats.
            # The count is the exception. "i have two cats" and then "my other cat is called
            # max" names one of the two they said, so the name goes on that record instead of
            # adding a third: the listing said "two cats and a cat called Max" to a person who
            # had said they have two, and a number in the line is not a new animal.
            counted = next((p for p in pets if p.get("animal") == pet.get("animal")
                            and (p.get("count") or 0) > 1 and not p.get("name")), None)
            same = next((p for p in pets if p.get("animal") == pet.get("animal") and
                         (p.get("name") == pet.get("name")
                          or not pet.get("another") and (not p.get("name")
                                                         or not pet.get("name"))
                          or counted is not None and p is counted)), None)
            if same is None and not pet.get("another") and (pet.get("count") or 0) <= 1:
                # "we're getting a puppy next month" and then "its a labrador" is one animal
                # said twice, and the store filed a puppy and a labrador: the store then had
                # two animals they do not have, and the reply about the labrador asked how long
                # it had been with them. A puppy is a dog and a breed is the animal it is, so an
                # animal still on its way takes the breed the next line gives it, and stays on
                # its way. Only an animal marked `coming` is matched this way: two animals the
                # person has are compared by their own word, as before, because a dog and a
                # puppy in the same house are two animals. And only a line that says no more
                # than the breed is a second word for the same animal: an animal with a name of
                # its own is a different animal, whatever kind it is, so "we're getting a puppy
                # next month" then "my dog is called rex" keeps both rather than turning the dog
                # they have into the puppy they are waiting for.
                kind = facts.ANIMAL_KINDS.get(str(pet.get("animal") or "").lower(), "")
                if pet.get("breed") and not pet.get("name"):
                    same = next((p for p in pets if p.get("coming") and kind
                                 and facts.ANIMAL_KINDS.get(
                                     str(p.get("animal") or "").lower(), "") == kind), None)
            if same is not None:
                # "your cat" and then "my cat is Biscuit" is one cat, not two: a name fills in
                # the animal we already knew about.
                if pet.get("name") and not same.get("name"):
                    same["name"] = pet["name"]
                    log(memory).append({"key": "pet", "value": pet,
                                        "turn": len(memory.get("turns") or []), "text": text})
                # The breed the next line names belongs to the animal already on record, so the
                # reply can say the word the person used instead of the one the store first
                # filed: "we're getting a puppy next month" then "its a labrador" is a labrador
                # on its way, not a puppy and a labrador.
                if pet.get("breed") and not same.get("breed"):
                    same["breed"] = pet["breed"]
                    log(memory).append({"key": "pet", "value": pet,
                                        "turn": len(memory.get("turns") or []), "text": text})
                # "i have 2 cats" and then "sorry, 3 cats" is the same fact put right: the
                # number is part of what they told us, so a later one takes the place of the
                # old one instead of being dropped on the floor.
                elif pet.get("count") and pet.get("count") != same.get("count"):
                    same["count"] = pet["count"]
                    log(memory).append({"key": "pet", "value": pet,
                                        "turn": len(memory.get("turns") or []), "text": text})
                # "my dog is 5" then "my dog is 6" is the same dog with a new age, and "my dog
                # is called fred" then "fred is 5" fills the age in on the dog we know.
                if pet.get("age") and pet.get("age") != same.get("age"):
                    same["age"] = pet["age"]
                    same.pop("unit", None)
                    if pet.get("unit"):
                        same["unit"] = pet["unit"]
                    log(memory).append({"key": "pet", "value": pet,
                                        "turn": len(memory.get("turns") or []), "text": text})
                # "i got a dog" and then "hes a lurcher" is what the dog is, not a second dog:
                # the breed the later line gave belongs on the animal the store already knows,
                # or the fact was dropped on the floor and "what breed was he" was answered with
                # "you haven't said" about a breed it had just been told. A later breed takes the
                # place of the old one, as a later age does.
                if pet.get("breed") and pet.get("breed") != same.get("breed"):
                    same["breed"] = pet["breed"]
                    log(memory).append({"key": "pet", "value": pet,
                                        "turn": len(memory.get("turns") or []), "text": text})
                continue
            pets.append(pet)
            log(memory).append({"key": "pet", "value": pet, "turn": len(memory.get("turns") or []),
                                "text": text})
        # Keeping only the newest four drops names the person has just given: a line that says
        # "my cats are called tom, jerry, spike, bub, milly and polly" names six, and the store
        # then answered "what are my cats called" with four of them - a fact they can see is
        # wrong. Everything this line named is kept, and so are the newest of the rest.
        known["pets"] = pets[-max(PETS_KEPT, len(value)):]
        return
    if key == "tastes":
        # A taste is a fact with a thing and a way ("dogs", "yes"): two tastes are two entries,
        # and the same thing said again is the same entry with what they now say about it. Before
        # this, "i like cats" then "i dont like fish" kept only the fish.
        tastes = known.get("tastes")
        if not isinstance(tastes, list):
            tastes = []
        for taste in value if isinstance(value, (list, tuple)) else [value]:
            if not isinstance(taste, dict) or not taste.get("thing"):
                continue
            thing = " ".join(str(taste.get("thing") or "").lower().split())
            same = next((t for t in tastes
                         if " ".join(str(t.get("thing") or "").lower().split()) == thing), None)
            if same is not None:
                if same.get("how") != taste.get("how"):
                    same["how"] = taste.get("how")
                    log(memory).append({"key": "taste", "value": taste,
                                        "turn": len(memory.get("turns") or []), "text": text})
                continue
            tastes.append(taste)
            log(memory).append({"key": "taste", "value": taste,
                                "turn": len(memory.get("turns") or []), "text": text})
        known["tastes"] = tastes[-6:]
        return
    if key == "owns":
        # A thing they own is kept by the name of the thing, so a second one adds to the first
        # rather than replacing it: "my car is a fiesta" then "my phone is a pixel" is two
        # things, and the store answers either without the other going missing.
        held = known.get("owns")
        if not isinstance(held, dict):
            held = {}
        for thing, name in (value or {}).items() if isinstance(value, dict) else []:
            if not thing or not name:
                continue
            if held.get(thing) == name:
                continue
            held[thing] = name
            log(memory).append({"key": "owns", "value": {thing: name},
                                "turn": len(memory.get("turns") or []), "text": text})
        known["owns"] = held
        return
    if key in LIST_FACTS:
        seen = known.get(key)
        if not isinstance(seen, list):
            seen = []
        for item in value if isinstance(value, (list, tuple)) else [value]:
            if item and item not in seen:
                seen.append(item)
                log(memory).append({"key": key, "value": item, "turn": len(memory.get("turns") or []),
                                    "text": text})
        known[key] = seen[-8:]
        return
    if known.get(key) == value:
        return
    known[key] = value
    log(memory).append({"key": key, "value": value, "turn": len(memory.get("turns") or []),
                        "text": text})


def forget(memory, key, values, why=None):
    """Take values back out of a fact: "im not coeliac" after "im coeliac".

    Returns the values that actually went, so the caller can say it out loud instead of leaving
    the person to wonder whether the store heard them. The log keeps what was said earlier: a
    fact that was true ten turns ago is still part of the conversation.
    """
    known = user(memory)
    wanted = values if isinstance(values, (list, tuple, set)) else [values]
    doomed = {str(value).strip().lower() for value in wanted if str(value).strip()}
    had = known.get(key)
    if key == "pets":
        # A pet is kept as a small record, not a word, so it goes back by the animal or the name
        # they called it: "i dont have a dog any more" while a cat called Milly stays on record.
        if not isinstance(had, list) or not doomed:
            return []
        everything = "*" in doomed
        # A record may also be handed back one at a time: "my cat died" from someone with two cats
        # takes one of them, and only the caller knows which record that is.
        records = [value for value in wanted if isinstance(value, dict)]
        kept, gone = [], []
        for pet in had:
            if not isinstance(pet, dict):
                continue
            worded = (str(pet.get("animal") or "").strip().lower() in doomed
                      or str(pet.get("name") or "").strip().lower() in doomed)
            named = pet in records
            if not (everything or worded or named):
                kept.append(pet)
                continue
            if named and not everything and not worded and (pet.get("count") or 1) > 1:
                # "i have two cats" then one of them dies: one animal goes, not the species.
                pet["count"] = int(pet["count"]) - 1
                if pet["count"] <= 1:
                    pet.pop("count", None)
                kept.append(pet)
                continue
            gone.append(pet)
        known[key] = kept
        if not kept:
            known.pop(key, None)
        # A pet that is gone is not a pet never mentioned: the person said it twice, so the store
        # keeps the record with the reason in `pets_gone`. Without it the next ask answers "you
        # haven't told me about a pet yet", which denies what they just said.
        if gone:
            past = [pet for pet in (known.get("pets_gone") or []) if isinstance(pet, dict)]
            for pet in gone:
                if not isinstance(pet, dict):
                    continue
                if pet not in past:
                    past.append(dict(pet, gone=why or "gone"))
            known["pets_gone"] = past
        return gone
    if key in LIST_FACTS:
        if not isinstance(had, list) or not doomed:
            return []
        left = [value for value in had if str(value).strip().lower() not in doomed]
        known[key] = left
        return [value for value in had if str(value).strip().lower() in doomed]
    if had is None or not doomed:
        return []
    if str(had).strip().lower() in doomed:
        del known[key]
        return [had]
    return []


def there_is_a_chat(memory):
    """Whether the person said anything before this line.

    A reply that leans on what was said earlier needs something said earlier, and on a first
    message there is nothing. Every reader that leans on the chat asks this one question, so a
    new one does not have to remember which key holds the turns or how the memory is shaped.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in turns or ():
        if isinstance(turn, dict) and str(turn.get("user") or "").strip():
            return True
    return False


def recent(memory, n=6):
    """The last n turns, oldest first.

    A reader asking about a past line with no memory to hand has no turns to look at. That
    happens in `_about_this_chat` (`_recall_reply` and the summary readers call it with the line
    alone, only to tell whether the line is itself a question about the chat), and the which-ask
    rule inside it read the thing back out of the memory: `recent(None, 8)` raised
    `AttributeError: 'NoneType' object has no attribute 'get'`, so from the first which-ask
    onwards every recall proposed nothing and the person got the search hedge about a line they
    had said three turns earlier. No turns is the honest answer here, not a crash.
    """
    if not memory:
        return []
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return []
    return turns[-n:]


def last_user(memory, n=1):
    """The last n things the user said (before this turn), oldest first."""
    lines = [turn.get("user", "") for turn in recent(memory, n)]
    return lines if n > 1 else (lines[-1] if lines else "")


def last_bot(memory):
    """The bot's last reply."""
    turns = recent(memory, 1)
    return turns[-1].get("bot", "") if turns else ""


def last_module(memory):
    turns = recent(memory, 1)
    return turns[-1].get("module") if turns else None


def name(memory):
    """The user's name, or ''."""
    facts_ = user(memory)
    value = facts_.get("name")
    return value if isinstance(value, str) else ""


# The words a plan opens with when the person said the whole thing, rather than naming what they
# are up to: "i start my new job on monday" is a sentence, "the gym tomorrow" is a phrase.
PLAN_OPENS = frozenset("""i i'm im i've i'll ill we we're were we've weve we'll well my our me""".split())
# A plan whose subject is two people opens with one of them and brings the speaker in with "and":
# "me and my wife are going to spain", "the kids and i are going to spain". Whether the first word
# is a pronoun or not, the subject is still theirs, and the phrase alone ("You're planning the
# kids and you are going to spain") says it wrong, so it is said back as their own sentence.
JOINED_SUBJECT = re.compile(r"^(?:[a-z'\u2019]+\s+){0,3}and\s+(?:i|me)\b", re.I)
# Plans that already carry the verb that says what kind of plan they are, so "planning" is not
# put in front of them a second time.
PLAN_VERBS = frozenset("""planning going trying aiming hoping intending looking""".split())


# A plan that is an appointment: a thing, its clock and its day, with no verb of its own
# ("dentist at 3 on tuesday", "lunch with sam at 1 on friday"). The store keeps those the way
# they read back, and "You're planning the dentist at 3 on tuesday" says the person is
# organising one; the appointment itself is "your dentist is at 3 on tuesday".
# The thing may hold a figure: "party for 8 on saturday" and "tea for 6 on sunday" are a thing of
# theirs with a count in it, and read as a doing they came back "You're planning to party for 8 on
# Saturday" - a person setting out to party. A count belongs to the thing.
APPOINTMENT_PLAN = re.compile(
    r"^(?:the\s+)?(?P<thing>[a-z][a-z0-9' \-]{1,28}?)\s+(?P<when>at\s+[\w:.]+(?:\s*(?:am|pm))?"
    r"(?:\s+on\s+[a-z0-9 \-]+)?|on\s+[a-z0-9 \-]+)$", re.I)


# A plan can name a thing of theirs on a day ("dentist at 3 on tuesday") or something they are
# doing on a day ("call the plumber on monday"). Both were said back as the first, so the doing
# one read "Your call the plumber is on Monday" - a thing called a call-the-plumber - and "pick
# up the kids at 3", "meet sam at 3 on tuesday", "book the hotel on monday" and "bake bread on
# sunday" were the same. The plan reader already has the frame for a doing ("You're planning to
# ..."), so what is decided here is only which side of the line a phrase is on.
#
# Two tests, and the shape of the phrase carries most of it. A determiner cannot come after the
# head of a noun phrase ("dentist the plumber" is not a phrase), so a determiner after the first
# word means the first word is a verb: "call the plumber", "wash the car", "test the smoke alarm".
# That leaves the verb-and-a-bare-noun shape, which needs the word itself: "bake bread", "meet
# sam", "book flights". The list holds only words that are not also the name of an event, so a
# noun a day hangs on (dentist, lunch, haircut, train, viewing, meeting, checkup) is never in it.
APPOINTMENT_DOING = frozenset("""
arrange bake book bring buy call clean collect cook deliver do drop email fetch finish fix get
go have hire make meet message order pay phone pick post put renew rent ring see send set sort
start submit take text tidy visit write
""".split())
# The words that cannot sit inside a noun phrase after its head, so their presence after the
# first word is what says the phrase is a verb and its object.
APPOINTMENT_A_DETERMINER = frozenset("""
a an the my your our their his her its this that these those some any
""".split())


# The verbs whose object is a person. "meet sam" and "call mum" are a doing whatever follows the
# verb, and the object of one of these is never the second half of a compound name.
APPOINTMENT_A_PERSON_VERB = frozenset("""
meet call ring text phone message email see visit collect fetch
""".split())
# What a doing takes as one bare word: the things you buy, spend or make in a quantity, and any
# plural ("book flights", "buy flowers"). A word outside both is as likely to be the second half
# of a name as the object of a verb - "book club", "post office", "pay day", "take away" - and a
# day hangs on those exactly as it does on "dentist", so the shape the store already had is kept.
APPOINTMENT_A_QUANTITY = frozenset("""
bread money rent cash milk water petrol diesel fuel shopping washing ironing laundry food
""".split())
# A plural the doing takes: "book flights", "pay bills", "buy flowers".
APPOINTMENT_A_PLURAL = re.compile(r"^[a-z]{3,}(?:s|es)$")
APPOINTMENT_NOT_A_PLURAL = ("ss", "us", "is", "ous")


def _takes_a_thing(word):
    """True when the word after the verb marks what follows as a thing, not a compound's half."""
    if word in APPOINTMENT_A_QUANTITY:
        return True
    return bool(APPOINTMENT_A_PLURAL.match(word)
                and not word.endswith(APPOINTMENT_NOT_A_PLURAL))


def _a_doing(thing):
    """True when the plan's thing is something they are doing, not something they have on."""
    words = [word.strip(",.;:") for word in thing.lower().split()]
    if not words:
        return False
    # A gerund is a doing read as a thing: "viewing the flat at 3" is the viewing, and
    # "You're planning to viewing the flat" is not a sentence.
    if words[0].endswith("ing") and len(words[0]) > 4:
        return False
    if words[0] in APPOINTMENT_A_PERSON_VERB:
        return True
    # A determiner cannot come after the head of a noun phrase, so its presence after the first
    # word is what says the phrase is a verb and its object: "call the plumber", "wash the car".
    if any(word in APPOINTMENT_A_DETERMINER for word in words[1:]):
        return True
    # The same shape with no determiner is only a doing when the object is a thing a verb takes
    # one of. "bake bread" is a doing; "book club" is a club.
    return (len(words) > 1 and words[0] in APPOINTMENT_DOING
            and _takes_a_thing(words[1]))


# A day or a month said back is a name: "on Tuesday", "in June". The store said both lower case
# because it keeps the person's own spelling of a plan, so "my interview is in june" was read back
# as "Your interview is in june." A month is also an ordinary word - "we may go to york", "march
# to the shop" - so it only takes the capital where a date stands: after "in", "of", "by", "from",
# "until" or one of the "early"/"late"/"mid" words. A weekday is nobody else's word, so it always
# does.
_WEEKDAY_NAMES = frozenset(("monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
                            "sunday", "christmas", "easter"))
_DATE_LEADS = frozenset(("in", "of", "by", "from", "until", "till", "til", "early", "late", "mid",
                         "towards", "before", "after"))
# A day of the month is also what makes the word beside it a month: "14 march" and "december 3"
# are dates, and "may 3" is the one that matters - "may" is a verb everywhere else.
_A_DAY_NUMBER = re.compile(r"^\d{1,2}(?:st|nd|rd|th)?$")


def named_days(said):
    """"on tuesday in june" -> "on Tuesday in June"; "we may go to york" is left alone."""
    words = str(said or "").split()
    out = []
    for index, word in enumerate(words):
        bare = word.lower().strip(",.;:!?")
        before = words[index - 1].lower().strip(",.;:!?") if index else ""
        after = words[index + 1].lower().strip(",.;:!?") if index + 1 < len(words) else ""
        if (bare in _WEEKDAY_NAMES
                or (bare in MONTHS and (before in _DATE_LEADS or _A_DAY_NUMBER.match(before)
                                        or _A_DAY_NUMBER.match(after)))):
            word = word.replace(bare, bare[:1].upper() + bare[1:], 1)
        out.append(word)
    return " ".join(out)


def _a_name_at_the_front(text):
    """Whether a kept plan opens with a capital that is not the article of a thing.

    "Portugal on the 12th of june" and "Moving to leeds on 3 june" open on a capital the store
    did not write for a thing: the first is a place it recognised, the second is the person's own
    sentence. "A cake on friday" opens on a capital too, and that one is a thing they have.
    """
    words = str(text or "").split()
    if not words or not words[0][:1].isupper():
        return False
    return words[0].lower().strip(",.!?") not in ("a", "an", "the")


# The words a thing already carries to say whose it is. A plan kept from "her appointment is on
# 3 june" is "her appointment on 3 june", and the sentence that gives a thing an owner must not
# give it a second one - "Your her appointment is on 3 June" says whose it is twice.
WHOSE_IT_IS = frozenset(("his", "her", "hers", "their", "theirs", "your", "yours"))

# A thing that carries its own verb is a sentence, and the "is" an appointment needs breaks it:
# "the clocks go back on 27 october" was read back as "Your clocks go back is on 27 October", and
# "the school holidays start on 21 july" as "Your school holidays start is on 21 July". The verb is
# never the first word - that is the noun the sentence starts with - and the word after it has to
# agree with that noun, because a bare verb after a singular noun is the other half of a compound:
# "the tip run on saturday" is a run, and "the school holidays start" is what the holidays do.
A_THING_DOES_BARE = frozenset("""go come start end begin finish close open reopen run happen
arrive leave return fly land depart move switch change rise set turn shut take last break
break up go back come round""".split())
A_THING_DOES_S = frozenset("""is are was were due goes comes starts ends begins finishes closes
opens reopens runs happens arrives leaves returns flies lands departs moves switches changes
rises sets turns shuts takes lasts breaks""".split())


def _a_plural(word):
    """True for the subject of a sentence said in the plural: "clocks", "school holidays"."""
    word = str(word or "").lower()
    return word.endswith("s") and not word.endswith(("ss", "us", "is"))


def _has_its_own_verb(thing):
    """True when the thing kept for a day already says what it does: "clocks go back"."""
    words = [word.strip(",.;:!?") for word in str(thing or "").lower().split()]
    if len(words) < 2:
        return False
    for index, word in enumerate(words[1:], 1):
        if word in A_THING_DOES_S:
            return True
        # The word in front of the verb is the head of the subject, so that is the one that says
        # whether the sentence is said in the plural: "school holidays start", "the kids break up".
        if _a_plural(words[index - 1]) and word in A_THING_DOES_BARE:
            return True
    return False


def appointment_sentence(text):
    """"dentist at 3 on tuesday" -> "Your dentist is at 3 on tuesday", or "" when it is not one."""
    found = APPOINTMENT_PLAN.match(" ".join(str(text or "").split()).strip(" .!?,"))
    if not found:
        return ""
    # "sons parents evening" is "son's parents evening": the plan kept the relation without the
    # "my" that said whose it is, and the "s" on it is still the possessive.
    thing = _the_possessive_a_relation_means(found.group("thing").strip())
    when = found.group("when").strip()
    if not thing or thing.split()[0].lower() in (
            "i", "im", "i'm", "we", "were", "we're", "my", "our", "to", "it", "its", "he", "she",
            "they", "you"):
        return ""
    # The day is a name: "on tuesday" is said back as "on Tuesday", the way every other reply in
    # the store says a weekday.
    when = named_days(when)
    if _a_doing(thing):
        # Something they are doing keeps its own words and takes the doing frame: a verb is never
        # a proper noun, so the store's capital on the first word goes back to lower case.
        said = "You're planning to " + thing[:1].lower() + thing[1:] + " " + when
        return said[:1].upper() + said[1:]
    if thing.split()[0].lower() in ("a", "an"):
        # The plan kept only the object, because the doing was the line's own verb: "im making a
        # cake on friday" left "A cake on friday", and "Your a cake is on Friday" is not
        # English. What the store has is a thing of theirs on a day.
        said = "You've got " + thing[:1].lower() + thing[1:] + " " + when
        return said[:1].upper() + said[1:]
    if thing.split()[0].lower() in WHOSE_IT_IS:
        # The thing already says whose it is: "her appointment is on 3 june" keeps "her
        # appointment on 3 june", and "Your her appointment is on 3 June" is not English. The
        # owner is the one the sentence needs, so it is not added twice.
        said = thing + ("" if _has_its_own_verb(thing) else " is") + " " + when
        return said[:1].upper() + said[1:]
    # A thing that brings its own verb keeps the day after it, with no "is" in between.
    said = "Your " + thing + ("" if _has_its_own_verb(thing) else " is") + " " + when
    return said[:1].upper() + said[1:]


# A line about getting somewhere: a trip, a move or a drive. The thing it names is a place they
# are going to, not a thing they have on a day, so it is said back with the person as the subject
# ("You're going to spain on 3 June") rather than as an appointment ("Your Spain is on 3 June").
JOURNEY_LINE = re.compile(
    r"\b(?:i|im|i'm|ive|i've|we|were|we're|weve|we've|they|hes|he's|shes|she's)\s+"
    r"(?:am\s+|are\s+|is\s+)?(?:going|off|flying|fly|moving|driving|heading|travell?ing|"
    r"cycling|walking|jetting|sailing|back)\b", re.I)


def _a_journey_line(said_line):
    """True when the line the plan came from puts the person on their way somewhere.

    The journey word has to be what they are doing ("im going to spain on 3 june", "we fly to rome
    on 3 june"), not the name of the thing ("my driving test is on 14 march"), so it has to come
    straight after the person.
    """
    return bool(JOURNEY_LINE.search(str(said_line or "")))


def plan_sentence(plan, said_line=None):
    """A plan said back, with the day a name: "in june" -> "in June"."""
    return named_days(_the_plan_said_back(plan, said_line))


def _the_plan_said_back(plan, said_line=None):
    """A plan said back to the person.

    A plan they said as a sentence comes back as one: "i start my new job on monday" -> "You
    start your new job on monday". A plan that is only the thing itself keeps the phrase after
    "you're planning": "The gym tomorrow" -> "You're planning the gym tomorrow".

    A plan kept as the bare phrase is often only half of what they said - "we're going to spain
    in july" keeps "Spain in july", and "You're planning spain in july" is a machine saying it
    back. So when the phrase alone needs the "planning" lead-in and the line it came from is a
    sentence of their own ("said_line"), that sentence is what is said back: "You're going to
    spain in july"."""
    text = without_filler(" ".join(str(plan or "").split())).strip(" .!?,")
    # The words that only lead in to the thing ("also my mums birthday is saturday", "by the way
    # the dentist is tuesday") are not part of the plan, and saying them back reads broken.
    text = re.sub(r"^(?:and\s+)?(?:also|oh|plus|by the way|btw|anyway|anyways|so|well|right|ok|"
                  r"okay|hey|and)\b[\s,]*", "", text, flags=re.I).strip(" .!?,")
    # "to repaint the hallway" is how the plan was said after "i'm planning", and the sentence
    # below adds its own "to": keeping it says "you're planning to to repaint the hallway".
    text = re.sub(r"^to\s+", "", text, flags=re.I)
    if not text:
        return ""
    # The line it came from, when it is a sentence of their own: a plan kept as half of one
    # ("we need to leave for the airport at 4" keeps "Leave for the airport at 4") has lost its
    # subject, and said back as an appointment the half has none to stand on: "Your leave for
    # the airport is at 4". The sentence that was really said answers instead.
    said_sentence = facts.no_tone(
        without_filler(" ".join(str(said_line or "").split()))).strip(" .!?,")
    theirs = bool(said_sentence) and (said_sentence.split()[0].lower() in PLAN_OPENS
                                      or bool(JOINED_SUBJECT.match(said_sentence)))
    # A journey is not an appointment ("your Spain is on 3 June"), and the person is the subject.
    # The plan itself says so when there is no journey line to read: a correction that moves the
    # day of a trip ("sorry i meant the 13th of june") has no journey in it, and the plan it is
    # moved in is kept with a capital - a place the store recognised ("Portugal on the 12th of
    # june") or a sentence of their own ("Moving to leeds on 3 june"). A thing they have on a day
    # is written in lower case ("scan on 3 june"), or opens with the article it was said with
    # ("A cake on friday"), so the capital that is not an article is what says "not a thing".
    appointment = ("" if (_a_journey_line(said_line) or _a_name_at_the_front(text))
                   else appointment_sentence(text))
    if appointment:
        if theirs and text.lower() in said_sentence.lower():
            out = _mid(you(said_sentence)).rstrip(" .")
            return out[:1].upper() + out[1:]
        return appointment
    # "to run 3 times a week" is already the phrase "planning to" wants, so the "to" is not said
    # twice: "You're planning to run 3 times a week".
    text = re.sub(r"^to\s+", "", text, flags=re.I)
    # "plan to visit my mum" names the plan in the same words "planning to visit" does.
    text = re.sub(r"^plans?\s+to\s+", "planning to ", text, flags=re.I)
    first = text.split()[0].lower().strip(",.;:")
    if first in PLAN_VERBS:
        # A plan that already says what they are doing with it keeps its own verb: "planning a
        # picnic for my daughter" is "You're planning a picnic", not "You're planning planning".
        phrase = _mid(you(text))
        return ("You're " + phrase[:1].lower() + phrase[1:]).rstrip(" .")
    if first in PLAN_OPENS or JOINED_SUBJECT.match(text):
        said = re.sub(r"\b(?:im|ive|ill)\b", lambda m: "i'" + m.group(0)[1:], text, flags=re.I)
        said = re.sub(r"\bwere\b", "we're", said, flags=re.I)
        said = re.sub(r"\bweve\b", "we've", said, flags=re.I)
        out = _mid(you(said)).rstrip(" .")
        return out[:1].upper() + out[1:]
    # The line it came from is the person's own sentence, and the tone at the end of it is still
    # theirs to keep: "im going to york in may haha" is said back as "You're going to york in may",
    # not with the "haha" the fact never had. The filler goes first: "xx" and "innit" are in the
    # composer's TAIL_OFF, not in the fact store's TONE_TAIL, so each reader keeps its own words.
    if said_sentence and theirs:
        # The line it came from says what they are doing with the thing ("we're going to spain
        # in july"), which the bare phrase cannot.
        return plan_sentence(said_sentence)
    phrase = you(text)
    phrase = phrase[:1].lower() + phrase[1:]
    if first.endswith("ing") and len(first) > 4:
        # a plan that keeps its verb is said back as the person's own doing: "Saving up for a
        # bike" -> "You're saving up for a bike", never "You're planning to saving up for a bike".
        return ("You're " + phrase).rstrip(" .")
    # "we are going to portugal in june" is a place they are off to, not an activity; a place
    # word used as a thing ("a bath and an early night") is not a place.
    if first in DETERMINERS or first in COUNTRIES or first in NOT_PLACES \
            or (first in _places() and first not in _not_places()):
        return ("You're planning " + phrase).rstrip(" .")
    # a bare verb phrase reads as a plan only with "to": "Visit my mum next weekend" ->
    # "You're planning to visit your mum next weekend". A plan the store kept with its own "to"
    # keeps one: "To paint the fence" is "You're planning to paint the fence", not "to to".
    if phrase.lower().startswith("to "):
        return ("You're planning " + phrase).rstrip(" .")
    return ("You're planning to " + phrase).rstrip(" .")


def _mid(text):
    """A "You" that ends up in the middle of a sentence goes back to lower case: the only reason
    it was capitalised is that it replaced an "I" ("how much should I put away")."""
    return re.sub(r"(?<=[\s,])You\b", "you", text)


# The person talks to the bot, so a "you" in a line about the person's own doing is the bot,
# and the bot says "me". "i told you about my mum" was said back as "you told you about your
# mum", and "sorry i snapped at you" as "you snapped at you": the swap moved the subject and
# left the addressee where it was, so the line was said back to the wrong person.
#
# Two things have to hold before the "you" is the bot. The line's own subject has to be the
# person ("i called you yesterday"), which is read off the first pronoun of the line: "talk to
# me whenever you like" opens on an object "me", so its "you" is the person being talked to, not
# the bot. And the "you" has to be the thing the doing is done to, which is what the word in
# front of it says: told, called, thanked, woke, or one of the prepositions a person is talked at
# through ("at you", "with you", "to you"). An opinion about what the person would do is not
# something done to the bot, so "i think you should rest" and "i hope you feel better" keep
# their "you".
#
# "thank" is not one of them: a thank you is a thing (a card, a note, a letter) or a courtesy
# that names who it went to after it, so "i sent my mum a thank you card" said back as "you sent
# your mum a thank me card" is wrong. The past tense "thanked" is the one that names the bot.
SAYS_TO_A_PERSON = frozenset("""
told tell telling tellin says said asks asked ask asking calls called call calling rang ring
ringing texted texting texts text emailed emailing emails email phoned phoning phones phone
messaged messaging message thanked thanking thanks thank blamed blaming blame ignored ignoring
ignore hurt hurting hurts missed missing miss loved loving love needed needing need trusted
trusting trust woke woken woke saw seeing seen heard hearing hear helped helping help sent
sending send showed showing show shown gave giving give given paid paying pay owed owing owe met
meeting meet noticed noticing notice picked picking pick chose chosen choose chose kissed
kissing kiss hugged hugging hug
""".split())
DONE_TO_A_PERSON = frozenset("""
to at with for about on from of around near towards toward into over behind beside against
across
""".split())
# The line's first word that can be a subject, and the ones that make it the person's own doing.
SUBJECT_HEADS = frozenset(("i", "i'm", "i've", "i'll", "i'd", "im", "ive", "ill", "we", "we're",
                           "we've", "we'll", "we'd", "were", "me", "my", "mine", "us", "our",
                           "ours", "you", "your", "yours", "yourself", "he", "she", "it", "they",
                           "him", "her", "them", "his", "their", "theirs"))
FIRST_PERSON_HEADS = frozenset(("i", "i'm", "i've", "i'll", "i'd", "im", "ive", "ill", "we",
                                "we're", "we've", "we'll", "we'd", "were"))
# A marker the ordinary swap below cannot touch, so the "me" it becomes is not turned back into
# a "you" by the same pass.
_BOT_ME, _BOT_MY = "\x00m", "\x00M"


def _to_the_bot(text):
    """Mark the "you" that is the bot in a line about the person's own doing."""
    words = re.findall(r"[a-z']+", text.lower())
    head = next((word for word in words if word in SUBJECT_HEADS), "")
    if head not in FIRST_PERSON_HEADS:
        return text
    def mark(match):
        word = match.group(2)
        if match.group(1).lower() not in SAYS_TO_A_PERSON | DONE_TO_A_PERSON:
            return match.group(0)
        # "thank you" is the courtesy, and a thank you card or note is a thing: the "you" in
        # them belongs to nobody, so "i sent my mum a thank you card" comes back as it went in.
        # Only "thank you for" and "thank you again" name who it goes to, and that is the bot.
        if match.group(1).lower() in ("thank", "thanks"):
            after = re.match(r"[\s,]*([a-z']+)", match.string[match.end():])
            if not after or after.group(1).lower() not in ("for", "again", "so", "too"):
                return match.group(0)
        new = "my" if word.lower() == "your" else "me"
        marker = _BOT_MY if new == "my" else _BOT_ME
        return match.group(1) + " " + (marker.upper() if word[:1].isupper() else marker)
    return re.sub(r"\b([a-z']+) +\b(you|your)\b", mark, text, flags=re.I)


def _from_the_bot(text):
    """The marked words go back to the bot's own person: "you will always be" -> "me"."""
    return text.replace(_BOT_ME, "me").replace(_BOT_MY, "my")

def _places():
    try:
        from ..understanding.topics import PLACES
    except ImportError:  # pragma: no cover - the module is always there in the bot
        return frozenset()
    return PLACES


def _not_places():
    try:
        from ..understanding.topics import NOT_PLACES
    except ImportError:  # pragma: no cover - the module is always there in the bot
        return frozenset()
    return NOT_PLACES


# The words people type with the apostrophe left out. Said back in the store's own sentence they
# read as somebody else's shorthand - "You told me your mum is called Janet and shes 72" - so the
# store puts the apostrophe in, the way it would write them itself. Only words with one reading
# are here: "ill", "id", "were", "well", "its" and "wont" are words of their own and stay as
# they were typed.
APOSTROPHE = {
    "im": "I'm", "ive": "I've", "dont": "don't", "cant": "can't",
    "doesnt": "doesn't", "didnt": "didn't", "isnt": "isn't", "wasnt": "wasn't",
    "arent": "aren't", "werent": "weren't", "havent": "haven't", "hasnt": "hasn't",
    "hadnt": "hadn't", "wouldnt": "wouldn't", "couldnt": "couldn't", "shouldnt": "shouldn't",
    "mustnt": "mustn't", "neednt": "needn't", "aint": "ain't", "shes": "she's",
    "hes": "he's", "thats": "that's", "whats": "what's", "theres": "there's",
    "heres": "here's", "theyre": "they're", "youre": "you're", "youve": "you've",
    "youll": "you'll", "youd": "you'd",
}
# "lets" is the verb as well as "let us", and so are "ill", "id", "its", "were", "well" and
# "wont": "my neighbour lets me park in his drive" said back as "your neighbour let's you park"
# is a word the person did not write. Those are left as typed; every other entry here has one
# reading.
APOSTROPHE_WORD = re.compile(r"\b(" + "|".join(sorted(APOSTROPHE, key=len, reverse=True)) +
                             r")\b", re.I)


# The span of a line the person is quoting rather than saying: their dad's words, a parcel, the
# label on a form. Inside it the words are not the person's own, so neither the flip to the second
# person nor the apostrophe repair reaches them - "my dad said "im not coming"" said back as
# "your dad said "you're not coming"" puts the words on the wrong person altogether.
QUOTED = re.compile(r'"[^"]*"|\u201c[^\u201d]*\u201d|(?<!\w)' + "'" + r"[^']*" + "'" + r'(?!\w)')


def _outside_quotes(text, repair):
    """`repair` over the parts of the line that are the person's own words, quotes left alone."""
    if not text or not QUOTED.search(text):
        return repair(text)
    out, last = [], 0
    for found in QUOTED.finditer(text):
        out.append(repair(text[last:found.start()]))
        out.append(found.group(0))
        last = found.end()
    out.append(repair(text[last:]))
    return "".join(out)


def without_the_apostrophe(text):
    """The person's words with the apostrophes they left out put back: "shes 72" -> "she's 72".

    Only the store's own sentence is written this way; a line handed back in quotation marks is
    their words as they typed them, and is left alone.
    """
    if not text:
        return text
    def put_back(match):
        word = match.group(0)
        other = APOSTROPHE.get(word.lower(), word)
        return other[:1].upper() + other[1:] if word[:1].isupper() else other
    return _outside_quotes(text, lambda part: APOSTROPHE_WORD.sub(put_back, part))
# A relation typed without its apostrophe is still a possessive, and it owns the thing after it:
# "your mums in hospital" reads like a form read back, and the quote marks the store used to put
# round the line were the only thing hiding it. The words that take the "s" themselves are not
# things it could own, so "my sisters are coming" keeps its plural.
# "my sisters are coming" is two people and keeps its plural; "my mums in hospital" is one person
# whose "s" is the "is", and the apostrophe belongs there too. A verb after the word is what says
# it is a plural subject - "my brothers play football", "my sisters work at the hospital" - so the
# words the reading already knows as verbs count as things the "s" cannot own.
NOT_OWNED = (frozenset("""are were is was am and or but nor too either""".split())
             | VERB_FORMS | VERBISH)
# A relation talked about as people they are with stays in the plural: "im seeing my sisters
# tomorrow" is two people and a day, and reading the "s" as a possessive gives "your sister's
# tomorrow", a sentence about one sister who is not there. It is only the verb that settles it -
# the same word with nothing in front of it really is the possessive ("its my mums tomorrow",
# "my daughters in year 6"), so the word of being with somebody has to be there.
WITH_SOMEBODY = frozenset("""see saw seen seeing visit visited visiting meet met meeting missed
    missing miss call called calling ring rang ringing text texted texting phone phoned phoning
    email emailed emailing thank thanked thanking hug hugged hugging kiss kissed kissing help helped
    helping bother bothered bothering visit stay stayed staying""".split()) | {"with"}
# "going to my dads for christmas" and "off to my brothers tonight" keep the possessive: a
# relation with "to" in front of it names the place they are going to, which is their dad's, and
# putting a plural there ("your dads for christmas") is the wrong sentence. So only the verb
# itself, standing next to the relation, makes it the people they are with.
# A relation they are with carries a time after it in the plural too: "text my sisters later" is
# two people and a time, not one sister's later.
WHEN_OR_WHERE = TIME_WORDS | PREPOSITIONS | DETERMINERS | frozenset("""next last later soon
    earlier afterwards afterward today tomorrow tonight week weekend morning evening night day
    month year couple few""".split())


def _the_relation_possessive(text):
    """The "s" of a relation with something after it becomes the possessive it means: "my
    mums birthday" -> "my mum's birthday", and "my daughters school" -> "my daughter's school".

    Only a relation the store knows, and only when the word after it is a thing it could own:
    "my sisters are coming" is two people, not a possessive, and neither is "seeing my sisters
    tomorrow".
    """
    def own(match):
        whole, relation, thing = match.group(0), match.group(2), match.group(3)
        if relation[:-1].lower() not in facts.RELATIONS or thing.lower() in NOT_OWNED:
            return whole
        if thing.lower() in WHEN_OR_WHERE and _with_somebody(text, match.start()):
            return whole
        return match.group(1) + " " + relation[:-1] + "'s " + thing
    return re.sub(r"\b((?:[Mm]y|[Oo]ur)) ([a-z]+s) ([A-Za-z0-9']+)", own, text)


def _the_possessive_a_relation_means(phrase):
    """The possessive a relation means when its determiner is not in the phrase: "sons parents
    evening" -> "son's parents evening".

    The store keeps a plan as the thing itself, and the "my" that said whose it is stays with
    the line: "my sons parents evening is on thursday" is kept as "sons parents evening on
    thursday". Said back whole it is the line that says it ("your son's parents evening is on
    Thursday"), but a plan said back as a thing of theirs has only its own words to stand on,
    and "your sons parents evening" reads as a typo.

    The same guards as the determiner's version: a relation the store knows, a thing it could
    own after it, so "sons are coming" and "sons tonight" keep their plural.
    """
    match = re.match(r"([A-Za-z]+s)\s+([A-Za-z0-9']+)", str(phrase or "").strip())
    if not match:
        return phrase
    relation, owned = match.group(1), match.group(2)
    if relation[:-1].lower() not in facts.RELATIONS or owned.lower() in NOT_OWNED:
        return phrase
    if owned.lower() in WHEN_OR_WHERE:
        return phrase
    return relation[:-1] + "'s " + phrase.strip()[len(relation):].lstrip()


def _with_somebody(text, start):
    """True when the relation is somebody the line says they are with or going to see.

    The verb of being with somebody has to stand next to the relation: "seeing my sisters
    tomorrow", "text my sisters later". A "to" in between names the place they are going to, and
    a place is somebody's ("off to my brother's tonight"), so the possessive is right there.
    """
    before = text[:start].rstrip().split()
    return bool(before) and before[-1].lower() in WITH_SOMEBODY


def you(text):
    """A fact in the user's own words, reworded to say it back to them: "my daughter's
    birthday" -> "your daughter's birthday". A quotation in the line is somebody else's words
    and is left as it was said; outside one, the "s" a relation was typed with becomes the
    possessive it means ("your mums birthday" -> "your mum's birthday")."""
    return _outside_quotes(
        text, lambda part: _flip_to_the_second_person(_the_relation_possessive(part)))


def _flip_to_the_second_person(text):
    """`you`'s reading, over one stretch of the line: the first person becomes the second."""
    swaps = {"i'm": "you're", "i am": "you are", "i've": "you've", "i have": "you have",
             "i'll": "you'll", "we'll": "you'll",
             # Most people type it without the apostrophe: "im planning a picnic for my
             # daughter" said back was "You told me im planning a picnic for your daughter",
             # which reads as if a stranger were being quoted. "ive" is the same word and the
             # same fix; "ill" and "id" are left alone because each is a word of its own.
             "im": "you're", "ive": "you've",
             # The verb has to agree with the new subject: "i was awake all night" is "you
             # were awake all night", never "you was".
             "i was not": "you were not", "i wasn't": "you weren't", "i wasnt": "you weren't",
             "i was": "you were", "i were": "you were", "we was": "you were",
             "we wasnt": "you weren't",
             "my": "your", "mine": "yours", "myself": "yourself", "me": "you", "we": "you",
             "our": "your", "ourselves": "yourselves", "us": "you", "i": "you"}
    def swap(match):
        word = match.group(0)
        other = swaps.get(word.lower(), word)
        return other[:1].upper() + other[1:] if word[:1].isupper() else other
    # "me" written for "my" is "your", not "you": "i dont get on with me sister" has to come
    # back as "your sister". The reading repairs the same words, so the echo and the reading
    # cannot drift apart; only "me" in front of a thing it could own is taken.
    text = _the_relation_possessive(text)
    text = _to_the_bot(text)
    words = re.findall(r"[a-z']+", text.lower())
    mine = possessive_me(words)
    said_me = [index for index, word in enumerate(words) if word == "me"]
    owns = {place for place, index in enumerate(said_me)
            if index < len(mine) and mine[index] == "my"}
    # A comma after it is a list of people, not a thing owned: "me, mum and dad went to spain"
    # has to come back as "you, mum and dad", and the reading of the line agrees.
    owns -= {place for place, found in enumerate(re.finditer(r"\bme\b", text, re.I))
             if re.match(r"\s*,", text[found.end():])}
    if owns:
        seen = [-1]
        def yours(match):
            seen[0] += 1
            word = match.group(0)
            if seen[0] in owns:
                return "Your" if word[:1].isupper() else "your"
            return word
        text = re.sub(r"\bme\b", yours, text, flags=re.I)
    text = re.sub(r"\b(i'm|i am|i've|i have|i was not|i wasn't|i wasnt|i was|i were|we wasnt|"
                  r"we was|im|ive|my|mine|myself|me|we|our|ourselves|us|i)\b", swap, text, flags=re.I)
    return without_the_apostrophe(_from_the_bot(text))


# The words a line asks with. A plan is kept from the statement half of a line, and the question
# half ("i want to save 480 pounds in 6 months, how much should i put away") is not part of it.
ASK_WORDS = frozenset("""how what when where who why which whose should shall can could do does did
is are was were will would am""".split())
ASK_TAIL = re.compile(r",\s*(?:and\s+)?(?:" + "|".join(sorted(ASK_WORDS)) + r")\b", re.I)


# "were moving house in march" is "we're moving house in march" typed without the apostrophe,
# not a question about the past: the past tense has a "we" in front of it ("we were moving"), so a
# line that opens on "were" and a doing word is the person's own statement and keeps its verb.
WERE_DOING = re.compile(r"we[r']?e?\s+\w+ing\b|were\s+\w+ing\b", re.I)


def _statement(text):
    """The statement half of a line, or "" when the line is a question."""
    line = " ".join(str(text or "").split()).strip(" .!?,")
    words = line.split()
    if (words and words[0].lower().strip(",.;:") in ASK_WORDS
            and not WERE_DOING.match(line)):
        return ""
    cut = ASK_TAIL.search(line)
    if cut:
        line = line[:cut.start()]
    return line.strip(" .,!?")


def plan_line(memory, plan):
    """The line the person said that a plan came from, if it names that plan.

    "we're going to spain in july" keeps the plan "Spain in july", and the phrase alone cannot
    say who is going or that anybody is: the sentence it came from can. Only the statement part
    of that line is a plan said back, so a question hanging off it is cut away."""
    wanted = " ".join(str(plan or "").lower().split())
    if not wanted:
        return None
    for entry in reversed(log(memory)):
        if entry.get("key") not in ("plan", "plans"):
            continue
        if " ".join(str(entry.get("value") or "").lower().split()) != wanted:
            continue
        said_line = _statement(entry.get("text"))
        if said_line:
            return said_line
    return None


def said(memory, key):
    """The first value the user gave for a fact key, as (value, turn) or (None, None)."""
    for entry in log(memory):
        if entry.get("key") == key:
            return entry.get("value"), entry.get("turn")
    return None, None


__all__ = [
    "action", "already_said", "asks_only", "context", "you", "current", "entry_answer", "expand", "facts",
    "followup_reading", "gist", "has_time", "introduction_question", "is_follow_up",
    "answer_in_hand",
    "key_subject", "keywords", "last_bot", "last_module", "last_user", "left_for_a_blank", "log",
    "meal_follow_up", "name", "note", "plan_line", "plan_sentence", "recent", "remember",
    "remember_answer", "resumed", "return_target", "said", "said_again", "same_as_before",
    "answer_about", "answers_about_another_creature", "the_animal_the_subject_is",
    "sized_reply", "stem", "subject", "the_ask_about_the_thing_it_points_at", "topic_text",
    "the_step_back_takes_its_words_back", "topics", "user", "bare_question", "written_out",
]
