"""Answers everyday requests from the knowledge base (bot/knowledge).

This is the one module that turns a line into a knowledge answer. It reads the shared
reading in memory["understood"] rather than its own keywords, asks the maths domain for a
computed answer when the line is a calculation, then asks bot.knowledge.lookup for the
entry the line is really about. It stays out of the way (returns None) when nothing fits
well: a wrong answer is worse than letting another module, or an honest "I don't know",
take the turn.
"""
import copy
import difflib
import re
import string

from .. import memory as mem
from ..compose import NEGATORS, goodnews, lead, pick, with_name
from ..compose import fit as shapes
from ..compose.repair import amends_to
from ..compose import trouble as trouble_reading
from ..knowledge import (by_topic, cooking, dishes, entertainment, entries as all_entries,
                         freshness, home, meat_in_a_card, pets, shopping, topics, work)
from ..knowledge.lookup import (EXPLAIN_FILLER, EXPLAIN_LEADS, about_the_chat,
                                about_the_topic, find, leans_on_a_subject,
                                names_its_own_subject, names_nothing_of_its_own)
from ..knowledge.lookup import entry as lookup_entry
# `repeat` is read by `_answer` on every line, so it is imported with the rest: inside the hook
# that declares a request for less, the import is there for `TAKES_AS_IT_COMES` and missing for
# the turn, and a module that raises is skipped without a word (the whole lookup went quiet).
from ..memory import (ack, deadline, healing, named, narrow as length, onset, prefer, repeat,
                      taste, when)
# not `hope` or `matters` on their own: `_answer` and its helpers use those names for other things
from ..memory import hope as a_wish, matters
from ..memory import topics as memory_topics  # not `topics`: this module has a `topics()` of its own
from ..knowledge.maths import solve
from ..understanding.kinds import ANSWERING_A_QUOTED_ASK, SUMMONS_WHO
from ..memory import a_year_of_birth
from ..memory import baking, doing_it, trips
from ..memory import repeat
from ..memory import outfit
from ..memory import (followup_reading, keywords, recall, remember_answer, resize,
                     same_as_before, the_ask_about_the_thing_it_points_at)
from ..memory import stuck as stuck_line
from ..memory import again as same_again  # the short of an answer already on the screen
from ..memory.again import NOTHING_MORE  # said of an answer with nothing further in it
from ..memory.again import AGAIN_HELP, DETAIL_AGAIN, SAME_ADVICE  # the lead-ins on a repeat
# A request for less ("keep it brief", "shorter") is the answer they already have, cut down, and
# it is read before the lookup so the short form comes back rather than a new entry.
from ..memory import repeat
from ..memory import topics as said_topic
from ..memory.topics import AMOUNT, ASK_ONLY, already_said, pairing, stem
from ..understanding import kinds
from ..memory.ack import VAGUE
from ..memory.topics import current as the_topic, is_follow_up
# `repeat` is used in `_answer`, not only in the one place that imports it locally: a
# request for less is cut from the answer in memory, which every answered line goes
# through. With the import inside that one function only, `_answer` raised NameError
# on every line, the runtime swallowed it as it is meant to, and the whole knowledge
# base went silent behind a greeting.
from ..memory import repeat, tried, more, returned
from ..memory import returns as went_back
from ..memory import limit
from ..memory import whereabout
from ..memory import price as a_price
from ..memory import (a_detail_of_the_thing_we_hold, answers_about_another_creature,
                      followup_reading, keywords, remember_answer, resize, same_as_before, swap,
                      the_animal_the_subject_is, the_thing_a_detail_belongs_to)
# The ask-for-less path cuts the answer already given down (`repeat.shorter_for`). #3748 imported
# it inside `TAKES_AS_IT_COMES` only, so `_answer` raised NameError on every line and the whole
# knowledge base fell through to chat: "how do i cook rice" was answered with "That's beyond what
# I know well, sorry".
from ..memory import repeat
from ..memory.narrow import (CAUSE, RATE, SIGNALS, asks_a_part, flat, kind_of as asked_kind,
                             narrow, the_outcome_asked, the_part_asked, words_of)
from ..understanding import understand

PRIORITY = 0

# The keeping entries that state the fact for cooked food in general. They fit any food, so a
# question put to them says no more than the line already had, and reading one as *this* food's
# keeping fact is how a gardening question ("what size pot do i need for tomatoes" / "can i
# still use it") would get told about cooked food in the fridge.
GENERIC_KEEPING = ("fridge-life", "fridge-life-cooked")

# The topics this module is the specialist for: the union of what the knowledge domains answer,
# with the topic ids the understanding engine produces (bot/understanding/topics.py). The
# arbiter reads ANSWERS, so a knowledge answer beats small talk on a line read as being about a
# topic the knowledge base covers, and only there. It is derived from the domains on purpose: a
# new domain must not need someone to remember to edit this list.
ANSWERS = topics()


# Words that point back at what the last lines were about.
REFERRING = frozenset("it its that this them they one ones there these those".split())

# "do you cook much?", "can you reheat rice?" - a yes/no question put to the bot is not a
# follow-up about the dish just discussed, so the conversation's subject is not written into it.
ABOUT_YOU = re.compile(r"^\s*(?:do|does|did|are|is|can|could|would|will|have|has|were)\s+you\b",
                       re.IGNORECASE)


def _the_new_part(reply, memory, keep=3):
    """The part of the reply the last answer did not already say, when it stands on its own.

    "how long to boil chicken legs" then "does that change if theyre from frozen" reaches the
    same entry, and the entry has a sentence for the frozen case: the two answers open the same
    way and the second goes on. Declined as a repeat, the turn had no answer at all. Said whole,
    the person hears the paragraph they just read again. The sentence that was not in the last
    answer is the answer to this line, so that is what comes back.
    """
    said = str(reply or "").strip()
    mine = flat(said)
    if not mine:
        return None
    for turn in (memory.get("turns") or [])[-keep:]:
        if not isinstance(turn, dict):
            continue
        before = str(turn.get("bot") or "").strip()
        opening = flat(before)
        if not opening or not mine.startswith(opening) or len(mine) <= len(opening) + 15:
            continue
        if not said.startswith(before):
            continue
        added = said[len(before):].strip()
        if added[:1].isupper() and added.endswith((".", "!", "?")):
            return added
    return None


# A verdict said on its own in front of the answer - "Usually, yes." on a row that declares one
# (`bot/compose/lead.py`) - is not part of what the answer says. It is read off before two answers
# are compared, so a card that was said with its verdict in front is still the same card when a
# later line is given it again.
_BARE_VERDICT = re.compile(
    r"^[^.?!]{0,40}[.?!]\s+(?=.)", re.S)


def _without_the_verdict(text):
    """The reply without a sentence-long verdict in front of it."""
    said = " ".join(str(text or "").split())
    found = _BARE_VERDICT.match(said)
    if not found:
        return said
    head = found.group(0).strip().lower()
    if len(head.split()) > 6:
        return said
    if not re.search(r"\b(?:yes|no|not|never|always|usually|often|sometimes|normally|depends"
                     r"|mostly|generally|rarely|seldom)\b", head):
        return said
    return said[found.end():].lstrip()


_CARD_OPENINGS = None


def _card_openings():
    """The first few words of every card in the knowledge base, read once."""
    global _CARD_OPENINGS
    if _CARD_OPENINGS is None:
        heads = set()
        try:
            from ..knowledge import entries as _all_entries
            for item in _all_entries():
                said = getattr(item, "reply", None)
                if isinstance(said, str):
                    flat = " ".join(said.split())
                    if flat:
                        heads.add(flat[:40].lower())
        except Exception:  # noqa: BLE001 - a repeat is never worth a turn
            heads = set()
        _CARD_OPENINGS = heads
    return _CARD_OPENINGS


def _without_a_lead(text):
    """The reply without a sentence a row declared in front of one of its own cards.

    A row may declare the sentence a kind of line asks for (`entry(..., lead=("yesno", "Yes"))`,
    `bot/compose/lead.py`), and the reply the person heard is that sentence and then the card.
    The sentence answers the line it was read for: it is not part of the card, so a later turn
    that repeats the card does not repeat the sentence ("Same as before: No." answers a question
    nobody asked). Only a sentence in front of a known card is read off - a card of its own that
    opens "No - leave them whole." keeps its own words (`_without_the_verdict`).
    """
    said = " ".join(str(text or "").split())
    found = _BARE_VERDICT.match(said)
    if not found:
        return said
    rest = said[found.end():].lstrip()
    if not rest or rest[:40].lower() not in _card_openings():
        return said
    head = _without_the_verdict(said)
    return head if head and head != said else said


def _opening(text, words=8):
    """The first few words of a reply: two answers that open the same way are the same answer.

    A card read out to a why line has its cause sentence moved to the front
    (`bot/compose/lead.cause_first`), and it is still the card that opened on its fix a turn ago.
    So a leading sentence that names itself as the cause is stepped over before the opening is
    read: without that, "why is my drain slow" then "how do i fix it" handed the whole card back
    a second time, because the repeat reading no longer recognised the answer it had just given.
    """
    said = _without_the_verdict(text) or ""
    parts = re.split(r"(?<=[.!?])\s+", said.strip())
    while len(parts) > 1 and lead._CAUSE_SENTENCE.match(parts[0]):
        parts.pop(0)
    return " ".join(" ".join(parts).lower().split()[:words])


def _most_of_it_said(reply, memory, keep=3, least=40):
    """True when a whole sentence of this answer is a sentence the bot has already given.

    A card can answer a fact with the answer it gave a turn ago and a lead-in on the front
    ("Nothing separate for stone - it is the same advice: ..."), which is the same paragraph a
    second time. A lead-in is not new advice, so it does not save the sentence.
    """
    said = " ".join(str(turn.get("bot") or "") for turn in (memory or {}).get("turns", ())[-keep:]
                    if isinstance(turn, dict))
    if not said:
        return False
    said = _flat(said)
    for sentence in re.split(r"(?<=[.;!?])\s+", str(reply or "")):
        # a lead-in ("Nothing separate for stone - it is the same advice: ...") is not advice,
        # so what follows the last colon or dash is the part that has to be new
        for part in (sentence, re.split(r"[:;]\s+|\s+[-—]\s+", sentence)[-1]):
            if len(part) >= least and _flat(part) and _flat(part) in said:
                return True
    return False


def _said_before(reply, memory, keep=3):
    """True when the bot has already given this answer (or one that opens the same way)."""
    turns = memory.get("turns") or []
    mine = _opening(reply)
    if not mine:
        return False
    for turn in turns[-keep:]:
        if not isinstance(turn, dict):
            continue
        if _opening(turn.get("bot")) == mine:
            return True
    return False


# The same line asked again gets the same answer, and saying it word for word twice in a row
# is what a machine does (STYLE.md, "Never answer the same way twice in a row"). The answer is
# still right, so it is given again rather than replaced; what changes is that the bot says it
# is giving it again, which also leaves room for the person to say what did not work. The
# wordings are the shared pool's, in `bot/memory/again` and `bot/memory/topics`, so that every
# lead-in the bot can put in front of an answer is in one place and can be read back off it.
AGAIN = tuple(memory_topics.REPEAT) + same_again.LIKE_I_SAID
# Asked a third time, the answer is not landing, so the bot says so and asks what went wrong
# rather than handing over the same paragraph again.
# The lead-ins that name the detail a follow-up asked about ("what about the biting"), and what
# each says when the answer already covers it. They live with the other frames, in
# `bot/memory/again`, so a reply under any of them can be read back to its answer.
WORD = re.compile(r"[a-z0-9']+")
# A follow-up can carry a verb of thinking or asking rather than a part of the thing ("what should
# we think about" after the dog answer): the verb is the asking, not a detail the answer can cover,
# so the lead-in must not name it ("Nothing separate for think" was the reply).
NOT_A_DETAIL = frozenset("""
think thinks thinking thought know knows knowing say says saying tell tells telling ask asks
asking wonder wonders wondering guess guesses guessing consider considers considering decide
decides deciding choose chooses choosing
# "reckon" is what a lot of people say for "think", and it is an ordinary word, so the repeat
# lead-in named it: "why am i always tired do u reckon" after the tiredness card came back
# "Nothing separate for reckon - it is the same advice: ...", which is a sentence about a word
# nobody asked about, and it reads worse than the plain "same answer" because "reckon" is not a
# part of anything. The line still carries the word - it is how the opinion is asked for, and the
# readers that answer one key on it - so it is dropped here, where the lead-in is chosen, and not
# from the reading.
reckon reckons reckoned reckoning rekon rekons reckin
""".split()) | frozenset("""
# Nor is the word a negation hangs on: "i dont know why" after the low-mood card came back
# "There is nothing separate for dont - it is the same advice", and "i have no idea why" named
# "idea". A line that says where the person has got to is not naming a part of the answer, so
# the words of not-knowing name nothing here.
dont doesnt didnt cant cannot couldnt wouldnt wont shant sure idea explain explains explained clue
""".split()) | frozenset("""
# The same verb said the other ways people say it: how somebody regards the thing is the asking,
# whatever verb carries it. "i want to start running but i find it boring" reached this lead-in as
# "Nothing separate for find - it is the same advice", where the word named is the person's own
# verb and the answer says nothing about it. The line is a repeat ask and gets the plain lead-in.
find finds finding found reckon reckons reckoning suppose supposes supposing imagine imagines
imagining feel feels feeling felt hope hopes hoping wish wishes wishing
""".split()) | frozenset("""
# How somebody hopes it will go is not a part of the thing either: "i want to start running but i
# hope it gets easier" came back "Nothing separate for easier - it is the same advice", which names
# a comparison the answer was never about. A comparative is the shape of the wish, not a subject.
easier easy better worse harder faster slower quicker sooner longer cheaper dearer
""".split()) | frozenset("""
# Nor is the opinion itself a part of the thing, and it is the word people reach for: covering
# the verb of thinking left the adjective behind, so "i want to start running but i find it dull"
# still came back "Nothing separate for dull - it is the same advice" while its nearest synonym
# "boring" was answered. How they regard the thing is not a part of the answer, whichever word
# they regard it with.
boring dull tedious pointless rubbish repetitive monotonous uninteresting
""".split()) | frozenset("""
# A time is not a part of the thing either: "she had a fall a week ago" came back "Nothing
# separate for ago - it is the same advice", which names a word nobody was asking about. The
# lead-in that says the answer covers it is the honest one for a line that only adds when.
ago today yesterday tomorrow tonight recently lately
week weeks month months year years day days
""".split()) | frozenset("""
# And a person nobody named is not a part of the thing: "someone else got the promotion" after
# the promotion answer came back "Same answer for someone: ...", which reads as a mistake. The
# plain repeat lead-in says the same thing without pretending it has narrowed anything.
someone somebody anyone anybody everyone everybody nobody none else another others other
""".split()) | frozenset("""
# Nor is how often: "is it ok to run every day" after another answer came back "Nothing separate
# for every - it is the same advice: <the answer before>", which names a word nobody asked about
# and reads as a sentence about nothing. A frequency says when the answer applies, not a part of
# the thing the answer is about.
every each once twice daily weekly monthly hourly yearly always never often sometimes
usually regularly rarely seldom
""".split())
# The verb the ask carries its own question on. In "how do i stop that" the last keyword is `stop`
# and it is the asking, not a detail, so it never becomes the thing the lead-in names.
# The words that point back at what was just said instead of naming a thing of their own.
BACK_POINTS = frozenset("""there it its that those these them they this one ones him her""".split())
ASK_VERB = re.compile(
    r"\b(?:how\s+(?:do|can|should|would|could)\s+(?:i|we)|how\s+to|"
    r"what\s+(?:do|can|should|would|could|will)\s+(?:i|we)|what\s+to|"
    r"where\s+(?:do|can|should|would|could)\s+(?:i|we)|"
    r"can\s+i|should\s+i|do\s+i)\s+([a-z']+)", re.I)
# The word that makes an -ed or -ing word a thing rather than the verb of the ask ("the seating",
# "the wedding"), so the frame-tail reading does not throw away a part they really named.
DETERMINER_BEFORE_DETAIL = frozenset(
    """the my his her their your our a an some both""".split())
# The same words, for joining a plural back onto the words that name it ("the custard tarts").
DETERMINERS = DETERMINER_BEFORE_DETAIL
# A word that is not part of the name of a part, so the search for it stops there: "what about the
# food for the kids" names the kids and not "food for".
STOP_BEFORE_A_PART = frozenset("""
    for and of in on at with about to from or the a an my his her their your our some both
    """.split())
# A sentence break, for the short version of an answer given a second time.
SENTENCE = re.compile(r"(?<=[.!?])\s+")
# A word that says how the answer landed is not a detail of it. "thats helpful" after the egg
# times was read as an ask about "helpful" and got "Nothing separate for helpful - it is the same
# advice: A soft one is the 5 to 6 minute egg...", which is the bot talking about its own words to
# somebody who had just thanked it for them. The praise belongs to the small-talk pool that answers
# a thank-you and a compliment, so the detail reading stands down and the line goes on to it.
PRAISE_WORD = frozenset("""
    helpful useful handy helpful great brilliant brill perfect lovely nice good sound sorted works
    worked working spot on exactly right clearer clear helpful interesting amazing fab fabulous
    wonderful excellent super ace wicked grand neat tidy
""".split())


# A word that names no thing is not a detail of the answer either. "what else can i do with it"
# asks for more of the answer, and read as a detail it gave "Nothing different for else I'm
# afraid: the same answer covers it - Take it off the heat...", a sentence about nothing: there is
# no part of the answer called "else". The ask is for the rest of what the entry knows, which is
# the repeat machinery's question, so the detail reading stands down and lets it answer.
# `more`, `other` and `another` are not in the set: they point at a part of the answer that has
# not been said yet ("the other half of it" is a real continuation), and only a word with no
# position in the answer at all is excluded.
NOTHING_WORD = frozenset("""
    else anything something nothing everything different instead anyway anyhow otherwise
""".split())

# A part of an answer is named, never a whole sentence about the person. "i work nights" after the
# neighbour's-dog advice named "nights", which that answer uses about the dog barking, and the words
# in front of it were walked back over the verb to "i", so the "part" was the entire line and the
# turn came back as "Everything about i work nights is in what I said above" - a fact handed back to
# the person who had just given it. A name never holds a subject, so a plural with one in front of
# it is a sentence about them, not a part of the answer to ask about.
SUBJECT_WORD = frozenset("""
    i im we us you he she they them theres thats it its one people
""".split())

# A word that adds emphasis or hesitation is not a detail either. "and when could they actually
# vote" after the women's-vote answer named "actually" as the part of the answer it asked about,
# and came back "Nothing separate for actually - it is the same advice: The campaign for women's
# votes split...". There is no part of a card called "actually": the line is the same ask with a
# softer word in it, so it is answered, not framed.
FILLER_WORD = frozenset("""
    actually really honestly seriously literally basically obviously definitely absolutely
    certainly clearly surely probably perhaps maybe quite rather even only just still again
    though although anyway anyhow then ok okay right please sure well so yes yeah
    hmm hmmm hm mhm mm um umm uhm uh er erm ah ahh oh ohh eh
""".split())

# A word that says what the thing is *like* is not a part of the answer either, and neither is the
# determiner in front of it. "when is the best time to buy a laptop" answered the calendar, and the
# same question said the other way - "when should i buy a new laptop" - came back "Nothing separate
# for **a new** - it is the same advice: Laptops and tablets are cheapest on Black Friday ...". The
# walk back from the end of the line had skipped `laptop` (the chat had just used it, so it names
# nothing new) and then taken the quality word beside it as the name of a part of the answer. There
# is no part of an answer called "a new", and "Same for a new: ..." is not a sentence: a quality
# word describes the thing and never names a piece of what the answer says about it. The same fault
# put "Same for a new" on the tv, the car and the phone, and "No separate fix for cheapest" on a
# bed.
A_QUALITY_WORD = frozenset("""
    new newer newest old older oldest young younger youngest
    cheap cheaper cheapest expensive pricey costly dear
    best better worst worse decent proper secondhand latest
    big bigger biggest small smaller smallest large larger huge tiny
    long longer longest short shorter shortest tall heavy light
""".split())

# A word that only joins one clause to the next is not a part of the thing. After the rescue-dog
# answer, "how long until my rescue dog settles" came back "Nothing different for until I'm afraid:
# the same answer covers it - Three months.": a person asking how long was told the bot had nothing
# separate to say about the word "until". `until` is a keyword of the ask ("how long until"), which
# is why the walk could reach it at all, so the joining words are named here and never said.
# A word that says where in the thing itself something goes - the end of the letter, the top of the
# form - is a part of what is already in hand, not a thing of its own. "i have to email my landlord
# about the damp" then "what should i write at the end of it" read `the end` as a thing the letter
# card never named, and the card stood down for a search hedge: the end of a letter being written is
# the letter's own last paragraph.
A_PLACE_IN_IT = frozenset("""
    end start beginning top bottom middle rest side front back corner last first
""".split())
A_JOINING_WORD = frozenset("""
    until till before after then when whenever while whilst during since once
    about if unless because than and or but so
""".split())
# A line that is nothing but a plea for more advice: "any tips", "got any advice", "any tricks".
# It names no thing of its own, so no entry is the answer to it - the answer is the one in hand.
A_PLEA_FOR_TIPS = re.compile(
    r"^(?:and |so |ok |okay |well )?(?:(?:any|some|got any|got some|need some|need any|"
    r"want some|more|any more|another|a few|any other)\s+)?"
    r"(?:tips?|advice|pointers?|tricks?|hints?)"
    r"(?: (?:at all|then|please|too|now|really|anyway))*[.!?]*$", re.I)


# A word no name in English contains: an auxiliary, a question word, a joining word. Asked the
# calendar question a second way - "when are laptops cheapest" - the plural reader walked up to
# three words back from `laptops` and took the question with it, and the person was told "Everything
# about **when are laptops** is in what I said above". A name is the thing and its modifiers, so
# both walks back over a candidate stop at one of these.
NOT_IN_A_NAME = A_JOINING_WORD | frozenset("""
    am is are was were be been being do does did done have has had having should would could can
    will shall may might must not
""".split())


def _in_short(reply):
    """The first sentence of an answer, or the first two when the first is only a lead-in.

    Asked the same thing twice, a friend repeats the short form, not the whole paragraph; the
    long answer is still there on the next ask (AGAIN_HELP), so nothing is lost.

    A sentence a row declared for an earlier line ("No.", "Usually, yes.") is not part of the
    short form either: this line asks something else, and "Same as before: No." answers a
    question the person did not ask (see `_without_a_lead`)."""
    reply = _without_a_lead(reply)
    parts = same_again.quoted.sentences(reply, SENTENCE)
    if not parts:
        return str(reply or "")
    if len(parts[0]) >= 60 or len(parts) == 1:
        return parts[0].strip()
    return (parts[0] + " " + parts[1]).strip()



def _same_as_the_last_answer(text, memory):
    """True when this answer is the one the person has just been given, in any words.

    Word for word is the plain case. A list of picks is the same list when it names the same
    things, even where an entry words the ones it has picked differently ("*Groundhog Day*
    (funny)" and "*Groundhog Day* for comedy" are the same film), because what the person is
    owed for a taste they have just named is a pick they have not had.
    """
    last = mem.last_bot(memory) or ""
    if not last:
        return False
    if _flat(text) == _flat(last):
        return True
    named_now = set(PICKED.findall(text))
    return bool(named_now) and named_now == set(PICKED.findall(last))


# The things an answer picks out by name (*Arrival*, *Project Hail Mary*): two answers naming the
# same set are the same list of picks, however the sentence around them is put together.
PICKED = re.compile(r"\*([^*\n]{2,60})\*")


def _the_same_answer_in_other_words(text, memory):
    """True when this answer says what is already on the screen, close enough to notice.

    A carried ask ("what else", "and a pudding") has to buy the person something they have not
    just had. An entry that words its list differently and keeps two of its three dishes hands
    back the answer they have just read: "Quick: tuna pasta in 15, macaroni cheese in 25, or a
    chicken traybake if you have 40 minutes" after "Quick: tuna pasta in 15, a frittata in 20, or
    a chicken traybake if you have 40 minutes". On that pair the overlap is 0.92, while the film
    list's second evening is 0.03 and a card where a punt was is 0.25, so 0.7 tells them apart.
    """
    last = mem.last_bot(memory) or ""
    if not last:
        return False
    return difflib.SequenceMatcher(None, _flat(text), _flat(last)).ratio() >= 0.7


def _flat(text):
    """A line reduced to its words, so a repeated question matches whatever its punctuation."""
    return " ".join(WORD.findall(str(text or "").lower()))


# The turn where the answer the person has just read covers what the line names: the reply points
# at it in one sentence. Two wordings, because the answer either names the part or it does not -
# "the 28 tram" is on the Lisbon card, so the trams are in the answer rather than missing from it,
# while a card about a phone battery that never says "screen" cannot claim to have covered it.
A_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")
A_CLAUSE_FINE = re.compile(r"[,;:]\s+|\s+\u2014\s+")
A_CLAUSE_BREAK = re.compile(r";\s+|:\s+|\s+\u2014\s+|,\s+(?:and|plus|but|so|which|then|with)\s+")
A_OPENS_A_CLAUSE = re.compile(r"^(?:and|plus|but|so|which|then|with|also|also\s)\b", re.I)
A_SAYS_NOTHING = frozenset(("it", "this", "that", "they", "them", "one", "ones"))


# A clause says something when it has a figure in it or a verb: "Insurance 8 to 20 a month",
# "Ask the vet about the rest". "Pubs away from Temple Bar for music" names the part and says
# nothing - it is the card's list with the sentence taken off it, so the pointer is better.
A_SAYS_SOMETHING = re.compile(
    r"\b(?:is|are|was|were|be|been|has|have|had|does|did|do|can|could|will|would|should|must|"
    r"need|needs|cost|costs|keep|keeps|want|wants|get|gets|give|gives|use|uses|take|takes|book|"
    r"books|buy|buys|put|puts|try|tries|ask|asks|check|checks|avoid|avoids|work|works|help|"
    r"helps|last|lasts|make|makes|mean|means|come|comes|go|goes|say|says|pay|pays|save|saves|"
    r"hold|holds|fit|fits|wear|wears|eat|eats|drink|drinks|start|starts|set|sets|add|adds|mix|"
    r"stir|stirs|cook|cooks|freeze|freezes|leave|leaves|order|orders|ring|rings|call|calls|wait|"
    r"waits|run|runs|sit|sits|stand|stands|open|opens|close|closes|clean|cleans|wash|washes|"
    r"dry|dries|walk|walks|feed|feeds|soak|soaks|cover|covers|worth)\b", re.I)


def _says_something(clause):
    """Whether the clause reads as a sentence rather than a list with the sentence taken off."""
    return bool(A_SAYS_SOMETHING.search(clause) or re.search(r"\d", clause))


def _the_part_in_the_answer(answer, detail):
    """The clause of `answer` that names the detail, said as its own sentence, or "".

    A follow-up that names a part of the last answer is owed the part. The answer above is on the
    screen, so the clause is not read out again - but a sentence about the conversation instead of
    about the thing ("Everything about insurance is in what I said above - there is no more than
    that") is what a person gets when the turn cannot find the clause, and it withholds the only
    line that answers them. Here it is found by name and handed back on its own.

    Only a clause that stands up as a sentence is used: four words or more, not opening on a
    joining word, and not a bare pronoun. A fragment is worse than the pointer.
    """
    last = (detail.split() or [""])[-1].lower()
    if len(last) < 3:
        return ""
    words = WORD.findall(str(answer or "").lower())
    if len(words) < 5:
        return ""
    # The loose split first, so the clause handed back keeps as much of its own sentence as still
    # reads as one; a list inside a sentence ("jabs and a microchip 60 to 100, neutering 60 to
    # 120 ..., insurance 8 to 20 a month") is one piece at that level and drops to the commas
    # only when no piece at the loose level both names the part and stands up.
    for splitter in (A_CLAUSE_BREAK, A_CLAUSE_FINE):
        for sentence in A_SENTENCE_BREAK.split(str(answer or "")):
            for clause in splitter.split(sentence):
                clause = clause.strip(" ,;:-\u2014")
                if not clause:
                    continue
                body = WORD.findall(clause.lower())
                if not any(_names_it(word, last) for word in body):
                    continue
                if len(body) < 4 or len(body) > 18:
                    continue
                if A_OPENS_A_CLAUSE.match(clause):
                    continue
                if body[0] in A_SAYS_NOTHING:
                    continue
                if not _says_something(clause):
                    continue
                clause = clause[0].upper() + clause[1:]
                if clause[-1] not in ".!?":
                    clause += "."
                return clause
    return ""


def _names_it(word, last):
    """Whether a word of the answer is the detail by name, or the stem of it."""
    if word == last:
        return True
    if len(word) < 4 or len(last) < 4:
        return False
    return word.startswith(last) or last.startswith(word)


SAID_ABOVE = (
    "Everything about {detail} is in what I said above \u2014 there is no more than that.",
    "All there is on {detail} is in the answer above, and nothing beyond it.",
    "{detail} is covered by the answer above; I have nothing to add to it.",
)
NOTHING_SEPARATE = (
    "There is nothing separate on {detail} \u2014 what I said above is the whole of it.",
    "Nothing more on {detail} than what I said above: it all comes under the one answer.",
    "There is no separate answer for {detail}: what is above is the whole of it.",
)


# A line that asks about how the thing turned out is not the part named and nothing else. "will it
# come back if i just wipe it" names the wiping, which the answer above covers, and the answer
# given back was "Everything about wipe is in what I said above" - a sentence about the
# conversation instead of about the wall, because the turn read the line as a part being named
# again and never saw the question in it. The question is what the person asked, so a line with
# one of these in it keeps the ordinary answer: this is only for a follow-up that names a part and
# asks nothing else ("what about the food", "and the trams").
ASKS_ABOUT_HOW_IT_TURNED_OUT = re.compile(
    r"\b(?:will|would|does|do|did|can|could|should|is|are|was|were|might)\s+"
    r"(?:it|that|this|they|them|those|these|i|we|you|he|she)\b", re.I)


def _a_part_named_in_the_line(text, memory, answer):
    """The part a follow-up names in the plural ("the pubs", "the trams"), or "".

    `_the_detail_named` keeps the words of the line as they were typed and looks for each of them
    among the keywords, which are stems, so a part named in the plural is never found: "what about
    the pubs" is looked for as "pubs" against "pub", and the turn gets no lead-in at all. Only a
    plural is read here - a word ending in "s" whose stem is one of the keywords - and only when
    the answer names it, because then the lead-in can say the answer covers it ("Same for the
    pubs: ..."). Anything else is the job of `_the_detail_named`, whose verb tests a bare ending
    never gets: "how do i make it work" names no part, and "work" is not one.
    """
    raw = WORD.findall(str(text or "").lower())
    wanted = {word for word in keywords(text) if len(word) > 2 and word not in ASK_ONLY}
    already = _said_before_now(text, memory)
    for index in range(len(raw) - 1, -1, -1):
        word = raw[index]
        if word in already or word in PRAISE_WORD or word in NOTHING_WORD:
            continue
        if len(word) < 4 or not word.endswith("s"):
            continue
        stem = word[:-1]
        if stem not in wanted:
            continue
        if not _named_in(answer, word):
            continue
        # "the custard tarts" is the part, not "tarts": the word or two in front of the plural are
        # part of its name when they are not a determiner ("the" is put back on in front of them).
        words = [word]
        before = index - 1
        while (before >= 0 and len(words) < 3 and raw[before] not in DETERMINERS
               and raw[before] not in ASK_ONLY and raw[before] not in STOP_BEFORE_A_PART
               and raw[before] not in PRAISE_WORD and raw[before] not in NOT_IN_A_NAME
               and raw[before] not in A_QUALITY_WORD):
            words.insert(0, raw[before])
            before -= 1
        if any(word in SUBJECT_WORD for word in words):
            continue
        name = " ".join(words)
        if before >= 0 and raw[before] in DETERMINERS:
            return raw[before] + " " + name
        return name
    return ""


def _short_form_of_the_last(answer, memory):
    """The answer last turn, when this turn's answer is only its opening, else ""."""
    last = str(mem.last_bot(memory) or "").strip()
    mine = _flat(answer)
    if not last or not mine or mine == _flat(last):
        return ""
    if not _flat(last).startswith(mine):
        return ""
    return last


def _answer_said(plan, memory):
    """How many of the turns just before this one already gave the plan's sentence.

    A follow-up asks the property in different words each time ("what temperature?" after "what
    temperature for a cake"), so the line is not the same twice and the count of the same line
    is 0. What is the same is the sentence we answered with, framed or not."""
    mine = _flat(plan)
    if not mine:
        return 0
    count = 0
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict) or mine not in _flat(turn.get("bot")):
            break
        module = turn.get("module")
        if isinstance(module, str) and module and module != "answers":
            # The sentence was said, but not as this module's answer to a question: a plan
            # announcement is answered with the entry's own paragraph by the store ("im planning
            # a trip" gets the countdown), and the line after it is the first question about
            # that paragraph. Counting it as said would answer "how long will it take" with
            # "Same as before:" in front of what was just read, where the part asked is what the
            # person needs (fast-shelf, #1848).
            continue
        count += 1
    return count


# Words that carry no subject: a sentence of an answer is about the same thing as the question
# when they share a word that is not one of these.
BARE = set("the a an i me my mine we our you your it its is are was were be do does did can could "
           "should would will shall may might to for of and or but in on at with about from that "
           "this these those there here what how when which why who whom whose if then so not no "
           "have has had get got make made much many more most some any".split())


def _carries(text):
    """The words of a line that say what it is about."""
    return {word for word in WORD.findall(str(text or "").lower())
            if len(word) > 2 and word not in BARE}


def _the_sentence_asked(reply, text):
    """The sentence of an answer that answers a line asking for one part of it.

    A repeated question is answered again, and a friend gives the part asked rather than the
    whole of a two-part answer: "can i make the frosting the day before", asked again, is the
    plan's sentence about the day, not the keeps-sentence in front of it that the person has
    already read. The sentence that shares the most words with the line is that part, and the
    first sentence is the answer when no sentence shares anything with it.
    """
    sentences = [part for part in SENTENCE.split(str(reply or "")) if part.strip()]
    if len(sentences) < 2:
        return None
    wanted = _carries(text)
    best, best_score, best_length = None, 0, len(sentences[0])
    for sentence in sentences:
        score = len(wanted & _carries(sentence))
        # The tightest sentence wins a tie, as in a narrowed answer: "before you use it" is not
        # as good a match for "the day before" as the sentence that says the day.
        if score and (score > best_score or (score == best_score and len(sentence) < best_length)):
            best, best_score, best_length = sentence, score, len(sentence)
    if best is None:
        return None
    # A sentence said on its own does not open with the word that joined it to the one before. The
    # child-worry card reads "...being told it is nothing teaches them to hide it. Then take one
    # small step towards whatever they are avoiding...", and the second sentence said alone opens
    # on a "then" with no then in front of it. A step of an answer is already said without its
    # joining word (_first_step), and the same holds for any one sentence of it.
    joined = _JOINED_ON.match(best.strip())
    if joined:
        best = best.strip()[joined.end():]
        best = best[:1].upper() + best[1:]
    return best


def _the_sentence_naming(reply, text, memory=None):
    """The later sentence of the answer that carries the part the line names, or None.

    A follow-up that names a part of the thing ("it catches at the top" after the sticking door)
    reaches the same entry, and the entry has one paragraph for the whole subject: held to the
    opening, the second turn handed back the general cause - damp, or a screw pulled out - which
    the person had just read, and said nothing about the top. The card does speak to the top: a
    later sentence has the hinge to tighten. That sentence is what the person asked for, so it is
    the one said again.

    The part is read by `_the_detail_named`, so a word the person has used before in this chat is
    not a part ("how do i clean my boots" asked twice names the whole thing, not a piece of it),
    and neither is the verb of the ask or a word that names no thing. Those turns keep the
    opening, which is the answer they asked for the first time.
    """
    detail = _the_detail_named(text, memory)
    if not detail:
        return None
    sentences = [part.strip() for part in SENTENCE.split(str(reply or "")) if part.strip()]
    if len(sentences) < 2:
        return None
    word = detail.split()[-1]
    for sentence in sentences[1:]:
        # The part of the thing, so the opening is left out: said again it is already the short
        # form, and a sentence that carries the part is the one with something new in it.
        if any(similar(word, other) for other in WORD.findall(sentence.lower())):
            return sentence
    return None


def _repeat_short(reply, text, memory=None):
    """The short form of an answer given a second time: the part the line asks, or the opening.

    A sentence a row declared for the first turn's line ("No.", "Usually, yes.") belongs to that
    line, not to this one: repeated behind "Same as before:" it answers a question nobody asked
    again, and a line that wants a time would be told "No." So a declared sentence is read off
    before the answer is repeated (`_without_a_lead`).
    """
    reply = _without_a_lead(reply)
    part = _the_sentence_asked(reply, text) if asked_kind(text) else None
    return part or _the_sentence_naming(reply, text, memory) or _in_short(reply)


# Asked for a figure the answer does not hold, repeating the answer is not an answer: "how long
# will that take" after the boiler checks gave the whole list back behind "Same as before:". A
# friend says what they cannot give and then gives the first step, so the honest line comes
# before the repeat wording.
NO_FIGURE = {
    "time": "I can't put a time on that one, sorry - ",
    "clock": "I can't put a time on that one, sorry - ",
    "heat": "I can't put a temperature on that one, sorry - ",
    "money": "I can't put a price on that one, sorry - ",
    "amount": "I can't put a figure on that one, sorry - ",
    "pressure": "I can't put a pressure on that one, sorry - ",
    "distance": "I can't put a distance on that one, sorry - ",
}
# A step ends where the next one starts: the opening of an answer is often one long sentence
# with the steps run together, and only the first of them is short enough to say again.
STEP_END = re.compile(r";\s+|,\s+(?:and|then|but)\s+|\.\s+|\.$")
# A length of time written in words is a time too: an entry that says "a fortnight" has answered
# "how long", and claiming otherwise would be worse than repeating it.
SPOKEN = re.compile(r"\b(?:fortnight\w*|overnight|all day|an hour|half an hour|a day|a week"
                    r"|a month|a year|a minute|a couple of (?:minutes|hours|days|weeks))\b", re.I)
# Any figure with a unit of time in it, relative or not: "30 minutes earlier" is still a length
# of time in the answer, so the answer is not one with no time in it.
TIMEISH = re.compile(r"\b\d+\s*(?:seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?"
                     r"|months?|years?)\b", re.I)


# Nothing in an answer is a length of time, so the honest line says that rather than repeat it: the
# steps are the answer to a different question.
NO_STEP = "what I said there is the steps, not how long they take."


# A step said on its own does not open with the word that joined it to the one before: "then go
# for a plain chocolate sponge" started life as the second step of the answer.
_JOINED_ON = re.compile(r"^(?:and|then|so|but|also|now|next)(?:\s*,\s*|\s+)", re.I)


def _first_step(reply):
    """The first step of an answer, short enough to say on its own."""
    opening = SENTENCE.split(str(reply or "").strip())[0].strip()
    joined = _JOINED_ON.match(opening)
    if joined:
        opening = opening[joined.end():]
        opening = opening[:1].upper() + opening[1:]
    if not opening:
        return ""
    if len(opening.split()) <= 16:
        return opening if opening[-1:] in ".!?" else opening + "."
    # Only the clause the answer opens with: a later clause of a long sentence is a detail
    # ("all electric, put the immersion on a timer"), not the step to start with.
    first = next((one.strip(" ,;:") for one in STEP_END.split(opening) if one.strip(" ,;:")), "")
    for piece in (first, first.split(": ")[-1]):
        if 4 <= len(piece.split()) <= 20:
            return piece if piece[-1:] in ".!?" else piece + "."
    return ""


def _figure_missing(reply, text):
    """The honest short line for a figure the answer does not hold, or None.

    Only the property the line asks for counts: an answer with no time in it is no answer to
    "how long", but it is the right answer to "how do i", so this is used on the repeats and
    follow-ups that ask for one part of an answer, never on the first ask.
    """
    kind = asked_kind(text)
    if kind not in NO_FIGURE:
        return None
    if _answers_the_figure(text, reply):
        # The answer holds a figure of the kind asked ("about two hours", "£80 to £200"), so it
        # is answering the line and the short form of it is the right thing to give.
        return None
    if kind in ("time", "clock") and (SPOKEN.search(str(reply or ""))
                                       or TIMEISH.search(str(reply or ""))):
        return None
    step = _first_step(reply)
    if not step:
        return NO_FIGURE[kind] + NO_STEP
    return NO_FIGURE[kind] + step[:1].lower() + step[1:]


def _figures_changed(reply, said):
    """True when both carry figures and the answer has one the earlier line did not."""
    mine = set(NUMBER_IN_TEXT.findall(str(reply or "")))
    theirs = set(NUMBER_IN_TEXT.findall(str(said or "")))
    return bool(mine and theirs and mine - theirs)


def _same_answer(reply, said):
    """True when `said` is this answer, or the short form of it, with or without a lead-in.

    A repeated answer comes back in three shapes: the whole paragraph again, the paragraph behind
    a lead-in ("Same as before: <answer>"), or the one sentence of it a friend repeats. The
    opening alone does not cover the third: a two-part answer asked a third time is repeated as
    its second sentence first ("how much water should i drink" answers with the six-to-eight
    glasses sentence, then the tea-and-coffee one), so a count read from the opening alone saw a
    new question and started the lead-in over at the long answer."""
    mine = _flat(reply)
    theirs = _flat(said)
    if not mine or not theirs:
        return False
    if _opening(mine) in theirs:
        return not _figures_changed(reply, said)
    for sentence in SENTENCE.split(str(reply or "")):
        part = _flat(sentence)
        if len(part) > 20 and part in theirs:
            # The same sentence with a different figure in it is a different answer, not this one
            # said again: "make it 3 instead" after the timing for a 2kg bird comes back as the
            # same rule worked out for three kilos, and the sentence around the figure is word
            # for word. Counted as a repeat it was handed over behind "Nothing more on it I'm
            # afraid", which tells the person the answer has not changed when it just has.
            return not _figures_changed(reply, said)
    # A step handed out of this answer is the answer in part: "The first thing to do: Open the
    # bleed valve at the top with a radiator key." a turn after the paragraph is that answer
    # still on the screen, so the same ask again is the repeat and gets the lead-in rather than
    # starting the ladder over with the paragraph printed bare.
    for clause in str(said or "").split(":"):
        cut = _flat(clause)
        if len(cut.split()) >= 6 and cut in mine:
            return True
    return False


def _asks_of_another_subject(text, understood):
    """True when the line, read on its own, belongs to a different subject than the one it leans on.

    "what should i see there", after a city was described, is about that city: read alone it is
    still a travel question, and the answer on the screen is the answer. "what is there to eat"
    is about food: read alone it is a food question that only borrowed its "there" from the
    travel turn, and handing back the paragraph about the tram tells a person nothing they asked
    for (STYLE.md prefers the honest hedge to an answer that does not fit). What separates them
    is the subject the words carry by themselves, not the shape of the line.
    """
    if not isinstance(understood, dict) or not str(text or "").strip():
        return False
    alone = understand(text, {}) or {}
    own = alone.get("topic") or ""
    held = (understood.get("leans_on") or {}).get("topic") or ""
    return bool(own) and bool(held) and own != held
def _asked_again(text, reply, memory):
    """How many times this same line was asked before and given this same answer: 0 when it is
    a new question, 1 on the first repeat, 2 on the second. A count rather than a flag so the
    wording can move on with each repeat (STYLE.md, "Never answer the same way twice in a row")."""
    wanted = _flat(text)
    mine = _opening(_flat(reply))
    if not wanted or not mine:
        return 0
    count = 0
    # Only the run of turns just before this one counts. "As before" points at the last thing
    # said, so when the person asked something else in between, the question is coming back to
    # an answer two turns old and the plain answer is what they need (calm-turtle, #854).
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict):
            break
        if _flat(turn.get("user")) != wanted:
            break
        # The answer already given, framed or not: an earlier "Same as before: <answer>" is the
        # same answer, and so is the sentence of it the repeat was shortened to, so the count
        # goes on rising and the wording can move with it.
        if not _same_answer(reply, turn.get("bot")):
            break
        count += 1
    return count

def _ask_verb(text):
    """The verb the ask leans its question on ("stop" in "how do i stop that"), or ""."""
    match = ASK_VERB.search(str(text or ""))
    return str(match.group(1) or "").lower() if match else ""


def _the_outcome_owed(item, text):
    """The sentence this row owes a line that asks how its subject turns out, or None.

    "will it be alright" after the phone went in the sink asks about the subject the last answer
    was about, and every sentence that answers it is already on the screen. A row that declares
    one (`entry(..., outcomes=(("survives", "..."),))`) has written that answer as a line of its
    own, so the turn gives the person that instead of a paragraph they have read.
    """
    which = the_outcome_asked(text)
    if not which or item is None:
        return None
    for shape, sentence in getattr(item, "outcomes", ()) or ():
        if shape == which and str(sentence or "").strip():
            return sentence
    return None


def _said_before_now(text, memory):
    """The words the person has already used in this chat, before this line."""
    seen = set()
    for turn in (memory or {}).get("turns") or []:
        if isinstance(turn, dict):
            seen.update(WORD.findall(str(turn.get("user") or "").lower()))
    return seen


# A word that corrects or softens the line rather than naming a part of the thing: "make it 3
# instead" names a new figure, and "instead" is not a detail the answer could have a sentence
# about - it made the lead-in read "Nothing separate for instead". The same for the openers
# people put in front of a correction ("actually", "no", "sorry", "wait").
A_CORRECTION_WORD = frozenset("""
    instead actually only just make again now please sorry wait really exactly still anyway
""".split())


def _a_fact_about_the_person(memory):
    """True when the line states something about the person rather than asking about a part.

    The detail frame is for a follow-up that names a part of the answer being pointed at ("what
    about the trams"). A line that says something about the person - "i work nights", "i have a
    toddler", "we live in a flat" - names no part of any answer, and a fact about themselves is the
    one thing a friend never hands back. The reading says which it is, so no word list has to guess;
    the part-name reading still gets its turn first, so a real part is never lost to this.
    """
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(understood, dict):
        return False
    return (understood.get("kind") == "statement" and not understood.get("asks")
            and bool(understood.get("first_person")))


def _the_detail_named(text, memory=None, with_quality=False):
    """The part a follow-up names, or "" when it names nothing the answer has not already said.

    A follow-up that names a part of the answer worth its own sentence is framed as one ("Same for
    the trams: ..."). A follow-up that says the thing again in more words names no new part, and
    the frame announced the answer back at the person: after the banging card, "its a banging sound
    when the heating comes on" came back "Same for the heating: a knocking that comes at the end of
    a burn is limescale on the heat exchanger..." - a different fault, invented out of a word the
    answer had just used. If every word of the part is already in the answer above it, there is
    nothing separate being named, and the reply is found without the frame.
    """
    named = _the_part_named(text, memory, with_quality)
    if named and _a_restatement_of_the_answer(memory) and _all_of_it_in_the_answer(named, memory):
        return ""
    return named


def _a_restatement_of_the_answer(memory):
    """True when the line tells the bot something rather than asking about a part of the answer.

    A question about a part ("what about the crate") is the framing's whole use, so it is never
    taken from it. A statement is the person adding what they know to the same subject, and what it
    names is the subject, not a part - the same test `_a_fact_about_the_person` makes.
    """
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(understood, dict):
        return False
    return understood.get("kind") == "statement" and not understood.get("asks")


def _all_of_it_in_the_answer(named, memory):
    """True when the answer just given already says every word of the part named."""
    said = WORD.findall(str(mem.last_bot(memory if isinstance(memory, dict) else {}) or "").lower())
    words = [word for word in WORD.findall(str(named or "").lower())
             if len(word) > 2 and word not in A_JOINING_WORD]
    return bool(words) and all(word in said or stem(word) in said for word in words)


# A word straight after a clause's subject is that clause's verb, and the line says so without
# naming the verb: "he bites when i stroke him" named `stroke` and answered "Same for stroke: that
# is usually over-stimulation ...", where nobody was talking about a part of the answer called
# "stroke". `stroke` is not on any verb list, and a list can only ever cover the verbs on it, so the
# test is the position rather than the word.
CLAUSE_OPENER = frozenset("when whenever if once after before while until as".split())
CLAUSE_SUBJECT = frozenset("i you he she it we they u".split())
NUMBER_OR_OWNER = frozenset("the my your his her their our this that a an".split())


def _the_clause_s_verb(raw, index):
    """True when the word at `index` is the verb of a when-or-if clause, whatever the word is."""
    if index >= 2 and raw[index - 2] in CLAUSE_OPENER and raw[index - 1] in CLAUSE_SUBJECT:
        return True
    # "when the heating comes on", "when my boiler fires": an opener, then a determiner and the
    # thing itself, and the next word is what the thing does.
    return bool(index >= 3 and raw[index - 3] in CLAUSE_OPENER
                and raw[index - 2] in NUMBER_OR_OWNER)


def _the_part_named(text, memory=None, with_quality=False):
    """The word a follow-up names as the part of the thing it asks about ("the biting"), or "".

    `with_quality` reads the line the way it was read before a quality word was known to name no
    part, so the caller can see what the name would have been and answer the repeat rather than
    stand down (see `_only_a_quality_name`).

    The word is kept with the word in front of it when that is a determiner, so the lead-in reads
    "Same for the biting" rather than "Same for biting".

    Three words are not a detail, and each of them made a wrong reply:
    * the verb of the ask itself - `stop` in "how do i stop that" - because "Same for stop:" is
      not a sentence;
    * a word the person has already used in this chat - `sofa` in "what about the sofa" after "my
      cat keeps scratching the sofa" - because the answer is already about that, so there is
      nothing new to say about it and the lead-in would announce the thing itself;
    * a word that names no thing at all - `else` in "what else can i do with it" - because there is
      no part of the answer called "else" and the lead-in came out as "Nothing different for else".
    A line that only goes back to a thing ("back to lisbon", "about the boiler") names no part of
    an answer either - the word read as the part was the return itself ("Nothing separate for
    back"), which is why the guard on the shape is here rather than at each reader.
    """
    if went_back.a_bare_return(text, memory if isinstance(memory, dict) else None):
        return ""
    raw = WORD.findall(str(text or "").lower())
    if raw and all(word in ONLY_THE_ASK for word in raw):
        # A line made only of the ask to hear it again names no part of the answer. "pardon?" after
        # the red-wine answer came back "Nothing separate for pardon - it is the same advice: <the
        # paragraph>", which tells a person who missed a sentence that the bot has nothing separate
        # to say about the word "pardon". The line is the repeat ask, and the memory lane answers it
        # as one; here there is nothing to name.
        return ""
    wanted = {word for word in keywords(text)
              if len(word) > 2 and word not in ASK_ONLY and word not in NOT_A_DETAIL
              and word not in A_CORRECTION_WORD}
    if not wanted:
        return ""
    verb = _ask_verb(text)
    already = _said_before_now(text, memory)
    for index in range(len(raw) - 1, -1, -1):
        word = raw[index]
        if word in A_JOINING_WORD:
            continue
        # `keywords()` gives stems ("settle"), so the word as typed ("settles") was never found
        # and the walk went back past it to an earlier word - "until", on the line above. A plural
        # whose stem is a keyword is that keyword.
        if word not in wanted and stem(word) not in wanted:
            continue
        if (word in PRAISE_WORD or word in NOTHING_WORD or word in FILLER_WORD
                or (word in A_QUALITY_WORD and not with_quality)):
            continue
        if verb and (word == verb or word.startswith(verb) or verb.startswith(word)):
            continue
        # A verb form the person says *after* the thing is how the question about it is asked -
        # "whats the scheme thing called", "what is it used for" - so it is the asking and never
        # the part the follow-up names: the answer came back framed "Nothing different for called,
        # I'm afraid". The word in front of it decides, the way it does in `bot/memory/detail.py`:
        # behind "the" or "my" it is a noun ("the seating", "the wedding"), otherwise it is a verb.
        if raw[index - 1] not in DETERMINER_BEFORE_DETAIL and (
                word in kinds.VERBISH
                or word in kinds.VERB_THIRD
                or _the_clause_s_verb(raw, index)
                or (len(word) > 4 and word.endswith(("ed", "ing")))):
            continue
        if word in already:
            continue
        # A word with `to` after it is the verb of a habit, not a part of the answer: "he used to
        # eat them" after the refusing-veg card named `used` and told the person "There is nothing
        # separate on used - what I said above is the whole of it", which is a sentence about the
        # bot's own notes. The -ed test above misses it because `used` is four letters and the
        # test wants five, and it is not a detail beside `to` whatever its length ("went to",
        # "got to", "tried to"). The next word decides, and an earlier word still gets its turn.
        if index + 1 < len(raw) and raw[index + 1] == "to":
            continue
        behind = raw[index - 1] if index else ""
        if (word in A_PLACE_IN_IT and index + 2 < len(raw) and raw[index + 1] == "of"
                and raw[index + 2] in BACK_POINTS):
            # "the end of it", "the top of that": where in the thing already in hand, not a thing
            # of its own, so nothing new is named here. The line leans on the answer, and the
            # answer is the answer.
            return ""
        if behind in ("the", "my", "his", "her", "their", "your", "a", "this", "that"):
            return behind + " " + word
        # The determiner and the word beside it are one name even when a plain word sits between
        # them: "will she stop if i get a scratch post" is the scratch post, not "post".
        whole = _named_whole(raw, index)
        if whole:
            return whole
        # A word that is not in the keywords as it was typed is a form of one ("settles" for
        # "settle"), and on its own it is the asking, not a part of the answer: the lead-in read
        # "Nothing different for settles", which is not a sentence either. It is said back only
        # when the answer itself says it by name ("Same for the scratching: ...").
        if word not in wanted and not _named_in(mem.last_bot(memory or {}), word):
            return ""
        return word
    return ""


def _only_a_quality_name(text, memory=None):
    """Whether the part the line names is a quality word and nothing else ("a new"), or False.

    A quality word says what the thing is like and names no piece of what the answer says about
    it, so such a line names no part at all. The caller still has to know that a part *was* read
    there: a repeat of a question the answer already covers must be answered as a repeat, not
    stood down to a search hedge, and reading the line the old way says which lines those are.
    """
    named = _the_detail_named(text, memory, with_quality=True)
    if not named:
        return False
    words = [word for word in named.split() if word not in DETERMINERS]
    return bool(words) and all(word in A_QUALITY_WORD for word in words)


# A word in front of the part and the part are one name ("a scratch post", "my new bike"), and the
# bare head word is not a phrase anyone says: "will she stop if i get a scratch post" came back
# "Same answer for post: Put a tall scratching post..." - the part named as the one word the
# determiner had been stripped off.
MODIFIER_WORDS = 2


def _named_whole(raw, index):
    """The determiner and the words between it and `raw[index]`, when they name one part, or "".

    Only a determiner close in front of the word counts, and only when every word between them is
    a plain one: a preposition, a back-pointing word or a verb means the line has moved on, and the
    word on its own is what it is.
    """
    # A back-pointing word right after the head word means the name is over: in "what about the
    # second hand one" the part is "the second hand one" or nothing at all, and "the second hand"
    # is a clock hand. Walking back from that head word would name a part nobody said.
    if index + 1 < len(raw) and raw[index + 1] in BACK_POINTS:
        return ""
    # The head word itself has to be a part: where it is the verb, the words in front of it are a
    # clause, not a name, and "Same answer for my back hurts:" is not a sentence. `what about the
    # biting` and `what about the seating` keep their answers, because the determiner in front of
    # the word settles the name before this test runs.
    head = raw[index]
    if (head in kinds.VERBISH or head in NEGATORS
            or (len(head) > 4 and head.endswith(("ed", "ing", "s")))):
        return ""
    # A negated verb in front of the head word is the same tell: "my mate hasnt text" is a
    # sentence about a mate, and "Same answer for my mate hasnt text:" is not a sentence.
    if any(word in NEGATORS for word in raw[max(index - MODIFIER_WORDS - 1, 0):index]):
        return ""
    for back in range(index - 1, max(index - 1 - MODIFIER_WORDS, -1), -1):
        word = raw[back]
        before = raw[back - 1] if back else ""
        if before in DETERMINER_BEFORE_DETAIL:
            return " ".join(raw[back - 1:index + 1])
        if (word in STOP_BEFORE_A_PART or word in BACK_POINTS or word in NOT_A_DETAIL
                or word in FILLER_WORD or word in NOTHING_WORD or word in PRAISE_WORD
                or word in NOT_IN_A_NAME or word in A_QUALITY_WORD):
            return ""
        if word in kinds.VERBISH or (len(word) > 4 and word.endswith(("ed", "ing"))):
            return ""
    return ""


FIRST_PERSON = frozenset("""i im ive id ill i'm i've i'd""".split())


def _their_own_state(text):
    """True when the line is about the person themselves and asks nothing of the thing.

    A follow-up that names no part of the answer and says how the person is ("i dont know why",
    "im not sure why") has nothing to be told about: the card on the screen above is not a second
    answer, and reading part of it out again is the bot talking at somebody who has just said
    they do not know.
    """
    text = str(text or "")
    if ASKS_ABOUT_HOW_IT_TURNED_OUT.search(text) or _ask_verb(text):
        return False
    raw = WORD.findall(text.lower())
    return bool(raw) and raw[0] in FIRST_PERSON


def _named_in(part, detail):
    """True when `part` says the detail by name, so a lead-in may say the answer covers it.

    A word of three letters or more is the detail itself when it is the word, whole: the check
    used to need four letters, so "should i ring the vet" after the vet answer was told
    "Nothing separate for the vet" by an answer whose every other word is about the vet. The
    prefix reading is for the word that carries an ending ("bite" in "biting"), and it needs four
    letters on both sides, because three is where "cat", "gas" and "bin" start matching things
    that are not them.
    """
    last = (detail.split() or [""])[-1]
    if len(last) < 3:
        return False
    for word in WORD.findall(str(part or "").lower()):
        if word == last:
            return True
        if len(word) >= 4 and len(last) >= 4 and (
                word.startswith(last[:4]) or last.startswith(word[:4])):
            return True
    return False


def similar(word, other):
    """Two words that are the same thing for this purpose: equal, or one carrying the other.

    "snails" and "snail" are one thing; "slug" and "slugs" are; "clean" and "cleaner" are not
    compared here, because the caller only passes words long enough for the stem to matter.
    """
    if word == other:
        return True
    if len(word) < 4 or len(other) < 4:
        return False
    return word.startswith(other) or other.startswith(word)


def _entry_words(memory):
    """The words the entry that has just answered is keyed on, all of them.

    Kept on the answer itself (`bot/memory/topics.remember_answer`), so a line naming another of
    the things that entry answers can be recognised without looking the entry up again.
    """
    kept = []
    answer = (memory or {}).get("entry_answer")
    if isinstance(answer, dict):
        kept.append(answer)
    others = (memory or {}).get("entry_answers")
    if isinstance(others, list):
        kept.extend(record for record in others if isinstance(record, dict))
    words = set()
    for record in kept:
        for key in record.get("keys") or ():
            words.update(WORD.findall(str(key).lower()))
    return words


def _what_they_typed(text, memory):
    """The words the person typed, given a reading with an earlier turn in front of it.

    The turn's own line is widened for a follow-up by putting the conversation's topic in front
    ("im learning to drive" + "how many lessons will i need"), and the knowledge base is then
    handed a line nobody typed (see `chat._follow_up_reading`). Everything below reads the
    person's own words for what the line names, so under that reading the topic comes back off
    the front: "how much does a puppy cost how much does a tattoo cost" is the tattoo question,
    and the puppy's answer is not about it.
    """
    if not isinstance(memory, dict) or not memory.get("joined_read"):
        return text
    read = memory.get("understood") if isinstance(memory.get("understood"), dict) else {}
    topic = str(((read.get("leans_on") or {}).get("text")) or "").strip()
    line = str(text or "").strip()
    if topic and line.lower().startswith(topic.lower()):
        return line[len(topic):].strip()
    return text


def _covered(text, reply, memory=None, understood=None):
    """True when the answer on the screen is about everything the line names.

    A line can reach its entry only through the words of the last turn: "how do i clean my boots"
    after the fruit-fly answer finds that answer on the word "clean", and the words of the line's
    own - the boots - are in it nowhere. Then the paragraph is not the answer to this line, so it
    is not handed back framed as a repeat of it either; nothing is said and another module speaks.
    A detail the line names ("what about the biting") is the exception: the answer having nothing
    separate for it is exactly what the lead-in is allowed to say.

    The exception is for a part of the thing the answer is about, and not for a thing of its own.
    "how much does a puppy cost" then "how much does a tattoo cost" is a price question about a
    tattoo, and reading the tattoo as a detail let the puppy's answer pass as one that covers the
    line, so the person was told "There is nothing separate on a tattoo". A line whose own subject
    is not the subject the answer is about (`_asks_of_another_subject`) names a thing, not a part.
    """
    said = set(WORD.findall(str(reply or "").lower()))
    read = understood
    if not isinstance(read, dict):
        read = (memory or {}).get("understood") if isinstance(memory, dict) else None
    typed = _what_they_typed(text, memory)
    detail = "" if _asks_of_another_subject(typed, read) else _the_detail_named(typed, memory)
    words = WORD.findall(str(text or "").lower())
    if any(word in BACK_POINTS for word in words):
        # "what is there to see" names nothing of its own: it points back at the answer on the
        # screen, and what it asks is that answer, so there is nothing here to be uncovered.
        return True
    verb = _ask_verb(text)
    entry = _entry_words(memory)
    for word in keywords(text):
        if len(word) < 3 or word in ASK_ONLY or word in detail.split():
            continue
        if verb and (word == verb or word.startswith(verb) or verb.startswith(word)):
            continue  # the asking, not a thing: "how do i clean my boots" asks how to *clean*
        if word in ASKING_VERBS:
            # "what helps" names nothing but the ask, so there is nothing in it for the answer to
            # cover: the answer on the screen is the thing it is about, and the lead-in "same
            # answer, and it covers this" is exactly what the person asked for.
            continue
        if any(similar(word, other) for other in said):
            continue
        # A word the entry that answered is keyed on is one of the things it answers, even when
        # the answer never says it: the slug row is keyed on slugs and snails and gives one
        # method for both, so "what about snails" after the slug answer was read as a line about
        # nothing the answer covered and got the shrug. The answer is about it - it is the same
        # row - so it comes back as the same advice.
        if any(similar(word, other) for other in entry):
            continue
        return False
    return True


def _a_question_about_another_thing(text, reply, understood, memory, own=None, item=None):
    """True when the line asks its own question about a thing the answer on the screen never names.

    "how much does a puppy cost" then "how much does a tattoo cost" reached the puppy's price row
    through the conversation and handed the puppy paragraph back framed as the answer to a tattoo:
    "Nothing separate for a tattoo - it is the same advice: A puppy is about 800 to 3,000 pounds".
    The line has a subject of its own - a thing, not a part of the thing in hand - and the answer
    is about another thing altogether, so it is not this line's answer however it is framed. A
    friend says what they do not know (STYLE.md prefers the honest hedge to an answer that does
    not fit), so the module stands down and the composer's own line takes the turn.

    The thing has to be named by the line, as a thing (`_the_detail_named` gives "a tattoo",
    "the passport"), and it has to be unknown to both the answer and the row that gave it. Two
    questions lean on the answer without naming anything of their own and keep it:
    - "how much should i expect to pay" after the brakes failed an MOT is the brake price; every
      word of it is asking, so it names no thing at all;
    - "how much should i budget for a van" is the money-plan card's line on the word budget, and
      a row keyed on a word the line asks by name is answering it, whether or not it says the
      line's other word.

    Only a question, too: a line that names a thing and asks nothing ("its an old oak floor")
    leans on the answer without asking anything of it, and the acknowledgement is the right reply.
    """
    if own:
        return False  # the line reached an entry on its own words: that entry is its answer
    if not isinstance(understood, dict) or understood.get("kind") != "question":
        return False
    if not isinstance(reply, str) or not reply.strip():
        return False
    typed = _what_they_typed(text, memory)
    if not _asks_of_another_subject(typed, understood):
        return False
    thing = _the_detail_named(typed, memory)
    if len(thing.split()) != 2:
        # The thing has to be named as a thing, with the word that makes it one: "a tattoo",
        # "the passport". A bare word can be the asking ("pay" in "how much should i expect to
        # pay", which is the brake price the answer on the screen already gives) and the line
        # then leans on the answer instead of naming a thing of its own.
        return False
    word = thing.split()[-1]
    if any(similar(word, other) for other in WORD.findall(reply.lower())):
        return False  # the answer names the thing
    held = set(_entry_words(memory))
    if item is not None:
        held |= _key_words(item)
    if any(similar(word, other) for other in held):
        return False  # the row that answered is keyed on the thing, so it is its answer
    named = [one for one in keywords(typed) if len(one) > 2 and one not in ASK_ONLY]
    if any(similar(one, other) for one in named for other in held):
        # The row that answered is keyed on something this line asks by name, so it is part of the
        # line's answer even when it never says the line's other word: "how much should i budget
        # for a van" is the money-plan card's line on the word budget, and the card answers it by
        # saying how to work the figure out. Only a row keyed on nothing the line names is
        # answering a different question.
        return False
    return True


# The first word of an answer that can lose its capital behind a lead-in. Every frame above puts
# the answer after a colon ("Same for {detail}: {reply}"), so a sentence opener came out as
# "Same for cooker: They are the cut a slow cooker suits" - two sentences in one. The set is the
# closed class of openers that are never a name, so "Same for the pan: Cook it" keeps its capital
# and nothing that starts a reply with a proper noun is touched.
A_SMALL_OPENER = frozenset("""
    the a an this that these those they it there he she we you and but if so or then both most
    some many all any each other another not no
    # ...and the verb an answer opens with when it tells somebody what to do. "Same for
    # floorboards: Sand a wooden floor back to bare wood" and "The same goes for the bathroom:
    # Use a mid-sheen" both read as two sentences with the capital on, which is the fault
    # STYLE.md names; the verb is a common word, so it loses it.
    add allow apply ask avoid bake baste beat begin boil bring brush buy catch change check
    choose clean clear close cook cool cover cut defrost do drain drink dry empty fill find
    finish fit fix freeze get give go hang heat hold keep lay leave let lift line look make
    measure mix open paint peel pick place plug pour prepare press pull put rinse roll rub
    run sand scrape seal set shake shut simmer sit soak sort spray spread stand start stay
    steam stir stop store switch take talk tell test thaw think throw tidy tip try turn use
    wait wash watch wear wipe work wrap
""".split())


def _small_letter(body):
    """`body` with a sentence-opening pronoun, article or verb put in lower case after a lead-in."""
    first, _, rest = body.partition(" ")
    bare = first.rstrip(string.punctuation)
    if bare.lower() in A_SMALL_OPENER:
        return first[:1].lower() + body[1:]
    # A word the same answer says again later in lower case is a common word, not a name: "Sand
    # a wooden floor back to bare wood, vacuum the dust off" is one sentence, where "Paris is the
    # one, and paris in august is hot" is not what this is protecting. A name is said again with
    # its capital, so it keeps it.
    if bare[:1].isupper() and re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(bare.lower()),
                                       rest):
        return first[:1].lower() + body[1:]
    return body


def _times_the_answer_was_said(reply, memory):
    """How many turns in a row the chat has just had this answer, counted before this one."""
    times = 0
    for turn in reversed((memory.get("turns") or [])[-4:]):
        if not isinstance(turn, dict) or not _same_answer(reply, turn.get("bot")):
            break
        times += 1
    return times


def _with_detail(detail, part, times, text="", memory=None, card=""):
    """`part` with the detail in front of it, said as what it is: the subject, or the same advice."""
    body = str(part or "").strip()
    if not detail or not body:
        return ""
    # Two frames saying the answer has not changed have been said; a third one about the bot's own
    # stock reads as the bot reporting on itself, and "nothing different for empty I'm afraid" also
    # makes an adjective in the line into a part of the answer. The person's own word takes the
    # lead-in's place from here. See `again.the_same_thing_underneath`.
    underneath = same_again.the_same_thing_underneath(text, body, times, memory)
    if underneath:
        return underneath
    if detail.split()[-1] in NOT_A_DETAIL:
        # The line asked what to think or what to say, not about a part of the thing: the answer
        # has not changed, and saying "Nothing separate for think" made it read as one word doing
        # another's job. The plain repeat lead-in is the honest one.
        return same_again.AGAIN[min(times, len(same_again.AGAIN)) - 1].format(reply=body)
    # The lead-in may only name what the answer itself names: see
    # `again.the_name_the_answer_says`, the one rule both frames use. It fixes the ask's own verb
    # being glued into the name ("a scratching post help") and the fragment left when the line
    # says "a bigger" and the answer only ever says "bigger".
    # The dictionary is the whole answer the person has, not only the sentence handed back: the
    # amount sentence of the paint card says "emulsion" and never "paint", while the card's own
    # opening names the paint. Reading the sentence alone dropped the person's word from the
    # lead-in and fell back to the plain frame, when naming it back is what the lead-in is for.
    named = same_again.the_name_the_answer_says(body, detail, card=card)
    if not named and _a_yes_no_ask(memory):
        # Nothing the lead-in could name, and a yes/no ask has no other word to build one from.
        # "Nothing separate for a bigger" claims the answer covers a fragment; the plain repeat
        # lead-in says the answer has not changed and hands it over with nothing glued in.
        return same_again.AGAIN[min(times, len(same_again.AGAIN)) - 1].format(reply=body)
    pool = DETAIL_AGAIN if named else SAME_ADVICE
    return pool[min(times, len(pool)) - 1].format(detail=named or detail,
                                                  reply=_small_letter(body))


def _a_yes_no_ask(memory):
    """True when the line asks yes or no ("would a service help")."""
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(understood, dict):
        return False
    return "yesno" in (understood.get("asks") or ())


# The answer given again for a line that names no part of it ("what else can i do with it"): there
# is no detail to put in the lead-in, so the lead says the entry has nothing further and the short
# form of the answer follows, rather than the paragraph word for word. The wording lives with the
# other frames, in `bot/memory/again` (as `NOTHING_MORE`), because every lead-in has to be
# readable back to its answer in one place: a family written here was not, and the answer under
# it read as a new one.


# The words that ask for the rest of what the entry knows. A line with one of them is not asking
# about a part of the answer, it is asking whether there is more; a line with none of them ("and
# how long should i walk him") is asking to be answered, and the narrow reading or the repeat
# machinery answers it better than a claim that there is nothing further.
MORE_ASK = frozenset("""
    else more other others another anything something nothing everything different instead
    anyway anyhow otherwise
""".split())


def _asks_for_more(text):
    """True when the line asks for the rest of the answer rather than about a part of it."""
    return any(word in MORE_ASK for word in keywords(text))


def _nothing_more_said_again(reply, text, memory):
    """The same answer for a line that names no part of it, said as nothing further, or ""."""
    if not _asks_for_more(text):
        return ""
    times = 0
    for turn in reversed((memory.get("turns") or [])[-4:]):
        if not isinstance(turn, dict) or not _same_answer(reply, turn.get("bot")):
            break
        times += 1
    if not times:
        return ""
    short = _in_short(reply) or reply
    underneath = same_again.the_same_thing_underneath(text, short, times, memory)
    if underneath:
        return underneath
    return NOTHING_MORE[min(times, len(NOTHING_MORE)) - 1].format(reply=short)


def _the_detail_said_again(reply, text, memory):
    """The same answer given again for a detail named inside it, or None.

    The answer is on the screen and the entry has nothing new, so the paragraph is not printed
    twice word for word: the detail the line named is said in the lead-in, the way a friend
    answers "what about the biting" with "same for the biting - plenty of chew toys"."""
    detail = _the_detail_named(text, memory)
    if not detail:
        # No detail, but the line asks for a kind of thing the answer holds ("when could they
        # actually vote" holds the dates): the sentence that answers the ask is what a friend
        # says again, and the alternative - "That is everything I have on that one, so I would
        # only repeat myself" - shrugs at a question the card answers.
        picked = _the_sentence_asked(reply, text) if asked_kind(text) else None
        if isinstance(picked, str) and picked.strip() and flat(picked) != flat(reply):
            times = _times_the_answer_was_said(reply, memory)
            if times:
                underneath = same_again.the_same_thing_underneath(text, picked, times, memory)
                if underneath:
                    return underneath
                return same_again.AGAIN[min(times, len(same_again.AGAIN)) - 1].format(
                    reply=picked)
        return _nothing_more_said_again(reply, text, memory)
    times = _times_the_answer_was_said(reply, memory)
    if not times:
        return None
    # The detail may be said in the answer itself ("the biting" inside a paragraph about chewing):
    # then the sentence that names it is given back rather than the opening.
    short = narrow(reply, text) or ""
    if not isinstance(short, str) or not short.strip() or flat(short) == flat(reply):
        # The sentence the line asks for, not the opening: "and when could they actually vote"
        # after the women's-vote answer was handed "The campaign for women's votes split into..."
        # behind the lead-in, and the dates the person asked for were in the next sentence.
        short = _repeat_short(reply, text, memory) or reply
    return _with_detail(detail, short, times, text, memory, card=reply)


def _detail_lead_in(text, part, memory):
    """`part` with the detail the line named in front of it, when the part is already on screen."""
    detail = _the_detail_named(text, memory)
    if not detail or not isinstance(part, str) or not part.strip():
        return ""
    said = flat(part)
    times = 0
    for turn in reversed((memory.get("turns") or [])[-4:]):
        if not isinstance(turn, dict):
            break
        if said and said in flat(turn.get("bot")):
            times += 1
            continue
        break
    if not times:
        return ""
    return _with_detail(detail, part, times, text, memory, card=_the_answer_on_screen(memory))


def _the_answer_on_screen(memory):
    """The whole answer the person is looking at, which is the dictionary a lead-in may name from."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed(list(turns or ())[-2:]):
        if isinstance(turn, dict) and isinstance(turn.get("bot"), str) and turn["bot"].strip():
            return turn["bot"]
    return ""


def _the_part_said_again(part, text, understood, memory):
    """The part of the last answer, with the detail the line named in front of it when needed.

    The part asked for is usually a sentence of the answer just given, so said plainly it is the
    same sentence twice in a row - which STYLE.md says never to do. When the line named a detail
    of the animal they told us about ("what about the chewing" after the chewing answer), that
    detail is what the lead-in names."""
    if isinstance(part, str) and part.strip() and a_detail_of_the_thing_we_hold(understood, memory):
        lead = _detail_lead_in(text, part, memory)
        if lead:
            return lead
    return part


def _already_said(reply, memory, keep=3):
    """True when the bot has just given this answer, with only a lead-in in front of it.

    A composer may put a sentence of its own before an entry's body ("Nerves before an
    interview are normal. Prepare four stories..."), and then the same answer comes back word
    for word without the openings matching. A reply that a recent answer *ends* with is that
    case. A reply the earlier answer only starts with is a part of it, which is how a follow-up
    is answered ("How do I fix it?" gets the steps of the last answer).
    """
    mine = " ".join(str(reply or "").lower().split())
    if not mine:
        return False
    for turn in (memory.get("turns") or [])[-keep:]:
        if not isinstance(turn, dict):
            continue
        bot = " ".join(str(turn.get("bot") or "").lower().split())
        if bot and (bot == mine or bot.endswith(mine) or _the_same_sentences(bot, mine)):
            return True
    return False


def _the_same_sentences(said, mine):
    """True when two replies are the same sentences with one of them moved to the front.

    A row that declares the sentence it owes a whether-line (`lead=("yesno", sentence)`) answers
    with that sentence first and the rest of the card after it, so the card that is on the screen
    is the entry's own reply with its sentences in a different order. Read as a string that is not
    the answer already given, and a follow-up about the card reaches it again as if new: "can i
    compost cooked food" / "and bones?" lost "The same goes for the bones: no cooked food or meat"
    and got the whole paragraph back instead.
    """
    if not said or not mine or said == mine:
        return False
    # Compared in lower case here rather than trusted from the caller: a call site that forgets to
    # flatten the case would otherwise make two replies the same sentences on case alone.
    parts = [part.lower() for part in re.split(r"(?<=[.!?])\s+", said) if part]
    others = [part.lower() for part in re.split(r"(?<=[.!?])\s+", mine) if part]
    return len(parts) > 1 and len(parts) == len(others) and sorted(parts) == sorted(others)


# "who are you", "what can you do", "where are you": a question about the bot carries no subject
# word either, so every follow-up reader in here took it as a question about the last thing
# discussed, and after "how do i cook rice" the person got "Same as before: Rinse it until the
# water runs clear" (brave-canoe, main watch). Understanding calls most of these about_bot and
# leaves a line with a subject of its own alone ("can you reheat rice", "what are you cooking" are
# not about_bot); the shapes here are the ones it misses, and they end where the line ends, so
# "where are you going on holiday" stays a holiday question.
WHO_IS_THE_BOT = re.compile(
    r"^\s*(?:so\s+|and\s+|ok\s+|okay\s+|but\s+|sorry\s+)?"
    r"(?:who|what|where)\s+(?:are|r)\s+(?:you|u)\s*[?.!]*$"
    r"|^\s*(?:what\s+can\s+you\s+do|what\s+do\s+you\s+do|who\s+made\s+you"
    r"|tell\s+me\s+about\s+yourself)\s*[?.!]*$",
    re.IGNORECASE)


# A line that asks how to answer a question is not a question to the bot about itself, even when
# the question quoted in it is about the bot: "how do i answer what are your weaknesses" is an
# interview question the person expects in a room with somebody else in it, and understanding
# reads the quoted words as the bot's own. The frame itself lives in the reading
# (`understanding.kinds.ANSWERING_A_QUOTED_ASK`), which stood the same reading down, so there is
# one definition of it and this is the same answer given to the composer.
def _asks_who_the_bot_is(understood, text):
    """True when the line asks who or what the bot is, not what the last answer was about."""
    text = text or ""
    if ANSWERING_A_QUOTED_ASK.search(text) and not WHO_IS_THE_BOT.search(text):
        return False
    if isinstance(understood, dict) and understood.get("about_bot"):
        return True
    return bool(WHO_IS_THE_BOT.search(text))


# The words an entry's own key uses when it answers a length ask. An entry found through a noun
# the action shares with it is not an answer to "how long": "im moving house" then "how long will
# it take" reached the deposit entry (which asks "how much", not "how long") because both say
# "house", and answered a question about moving with a figure about a Lifetime ISA. An entry may
# take the written-out ask only when its own key already reads a length, which is the entry
# saying that a length is one of the questions it answers.
LENGTH_WORDS = frozenset((
    "long", "soon", "months", "month", "years", "year", "weeks", "week",
    "hours", "hour", "days", "day", "minutes", "minute"))

# A length stated in an answer: a number of days, weeks, months, years, hours or minutes. A sum of
# money followed by a period ("\u00a3333 a month for five years", "\u00a34,000 a year") is a rate of
# payment, not a length, and an answer full of them (how to save a deposit, what a loan costs) is
# not answering "how long will it take" however many periods it mentions.
_A_LENGTH = re.compile(
    r"(?<![\u00a3$\u20ac\d.,])\b(?:\d{1,4}|a|an|one|two|three|four|five|six|seven|eight|nine|ten"
    r"|eleven|twelve|fifteen|twenty|thirty|forty|fifty|sixty)\s+"
    r"(?:to\s+\w+\s+)?(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b", re.I)

# A length that is spent doing the thing, rather than a wait before it or a total to reach it:
# "20 minutes", "half an hour", "ten minutes a day". An answer that opens with one of these is
# answering "how long should i ..." in the form it was asked.
_A_DURATION = re.compile(r"\b(?:minutes?|mins?|hours?|hrs?)\b", re.I)


# An answer that defines the unit is not a length to spend doing the thing. "how long should i
# practise each day" reached the row that says what a day is ("A day is 24 hours - the time from
# one noon to the next") and that answer holds a figure of hours, so it looked like the length the
# person asked for. The unit's own definition answers "how long is a day", never "how long should
# i do this for".
_DEFINES_THE_UNIT = re.compile(
    r"^\W*(?:a|an|one|the)\s+(?:second|minute|hour|day|week|month|year|decade|century)s?\b"
    r"\W+(?:is|are|has|have|takes|lasts|means)\b", re.I)


def _answers_a_length(item, reply):
    """Whether this entry answers a length ask: its own key asks one and its answer gives one."""
    reply = str(reply or "")
    if not reply or any(mark in reply for mark in ("\u00a3", "$", "\u20ac")):
        return False
    if _DEFINES_THE_UNIT.match(reply):
        return False
    if not _A_LENGTH.search(reply):
        return False
    for part in getattr(item, "key", ()) or ():
        for phrase in part:
            if set(str(phrase).lower().split()) & LENGTH_WORDS:
                return True
    return False


def _written_ask_with_an_answer(text, memory):
    """The duration ask written out with the action the chat is on, when an entry answers it.

    "how long will it take" after "im learning to drive" is the driving entry's question, and
    neither the line nor the subject put back in ("how long will it take learning to drive")
    reaches it. The written-out ask is only worth taking the turn when it lands somewhere: after
    "i want to grow tomatoes" it asks "how long will it take to grow tomatoes?", no entry answers
    that, and the turn then fell to repeating the answer before it ("Same as before: Give them
    sun, a big pot...") where the person used to get an honest "that's beyond what I know well".
    None when the line is not a duration ask, or the action it names has no answer.
    """
    written = mem.written_out(text, memory)
    if not written:
        return None
    try:
        asked = understand(written, memory)
        found, found_reply = _offer(lambda reject: find(asked, reject=reject), memory, asked)
        if not _answers_a_length(found, found_reply):
            return None
    except Exception:  # noqa: BLE001 - a lookup that fails is not an answer
        return None
    return written


def _the_article(subject, memory):
    """The article a rewritten line puts in front of the thing: "the " or, for a name, nothing.

    "im going to rome in june" then "is it expensive" is written out as "is rome expensive",
    because a name takes no article. "is the rome expensive" is not only wrong English, it is
    read as a different question: the price word is all the reading is about, so the domain the
    answer is in (travel) is one the reading never touched, the day rate is passed over, and the
    person gets the search hedge. Only the head of the subject is asked about, and only names the
    store has met count as names - a place, a person, a pet, the person themselves.
    """
    head = (subject.split() or [""])[0].strip(".,!?;:'\"").lower()
    if not head:
        return "the "
    user = memory.get("user") if isinstance(memory, dict) else None
    if not isinstance(user, dict):
        return "the "
    names = set()
    for key in ("name", "city"):
        value = user.get(key)
        if isinstance(value, str) and value.strip():
            names.update(word.lower() for word in value.split())
    for key in ("places", "people", "pets"):
        found = user.get(key)
        if isinstance(found, (list, tuple)):
            for value in found:
                if isinstance(value, str) and value.strip():
                    names.update(word.lower() for word in value.split())
    return "the " if head not in names else ""


def _with_subject(text, memory, about=None):
    """The follow-up written out with the thing it refers to: "how long will it take?" ->
    "how long will the birthday cake take?". The line itself when it names its own subject."""
    # An ask about time is about an action before it is about a thing: "how long will it take"
    # after "i want to lose a stone" is the question the weight-loss entry answers.
    written = _written_ask_with_an_answer(text, memory)
    if written:
        return written
    words = text.split()
    if len(words) > 14:
        return text
    if ABOUT_YOU.search(text):
        return text  # "do you cook much?" is a question about the bot, not about the dish
    subject = mem.subject(memory) if about is None else about
    if not subject:
        return text
    wanted = [w.strip(".,!?;:").lower() for w in subject.split()]
    said = [w.strip(".,!?;:").lower() for w in words]
    if any(word in said for word in wanted):
        return text  # it already says what it is about
    for i, word in enumerate(said):
        if word in REFERRING:
            words[i] = _the_article(subject, memory) + subject
            return " ".join(words)
    return text


# A follow-up can ask about a property of the thing without naming it: "what temperature should
# the oven be?" after a cake. These are the words that ask about a property, not about a thing.
PROPERTY = re.compile(r"\b(?:temperature|oven|gas mark|degrees|how long|how much|how many|"
                      r"minutes?|hours?|cost|price|expensive|when|how early|how hot)\b",
                      re.IGNORECASE)


def _about_subject(text, memory, about=None):
    """"What temperature should the oven be?" -> "... for the birthday cake?"."""
    asks_which_one = mem.KIND_ASK.search(text)
    if len(text.split()) > 14 or not (PROPERTY.search(text) or asks_which_one):
        return text
    subject = mem.subject(memory) if about is None else about
    if not subject or not mem.current(memory):
        return text
    wanted = [word.strip(".,!?;:").lower() for word in subject.split()]
    if any(word in text.lower() for word in wanted):
        return text  # it already says what it is about
    return text.rstrip("?.! ") + " for " + _the_article(subject, memory) + subject + "?"


# "what was I planning?" asks for the plan itself, and the store has it: read with the topic on
# the end it lands on the move-house checklist, which answers "how do I plan a move" instead of
# "you're planning to move house in March". "what's my plan?" is not here - that one is followed
# up with advice on purpose, because the person asking it wants the next step.
# "i need something for a headache" names the problem and asks for the thing that helps, and
# no entry is keyed on "something": the entries are keyed on the problem and on the ask ("what do
# i do for a headache", "what helps a headache", "what can i take for a headache"), so the vague
# frame the person put in front of the problem kept all of them out and the line was answered as
# a request for a suggestion ("Something for a headache? Tell me what you've enjoyed before and
# I'll suggest something."). The frame is read away and the rest asked as the question it is.
#
# It runs only where the lookup found nothing, so every line that has an answer keeps it, and the
# rest must name a thing rather than a person: "something for my mum" and "something to do with
# the kids" are the gift and the plans questions, which have answers of their own.
SOMETHING_FOR = re.compile(
    r"\b(?:something|anything|somef?in\w*|anyf\w*|summat|sommat|stuff)\s+"
    r"(?:for|to\s+(?:take|help|ease|soothe|settle|stop|calm|clear|put\s+on|rub\s+on|"
    r"drink|eat|use))\b\s*(.+)", re.I)
SOMETHING_FOR_PEOPLE = frozenset("""
mum mom dad mother father husband wife partner boyfriend girlfriend son daughter kid kids child
children baby brother sister friend friends gran granny grandma grandad grandpa nan aunt uncle
cousin nephew niece boss colleague neighbour neighbor her him them they us we people someone
anybody somebody everyone my his their our
""".split())
# Words at the end of the thing that say when, not what: "something for a headache now" is the
# headache, and the time is the ask ("fast", "quickly") rather than part of the problem.
SOMETHING_FOR_FILLER = frozenset("""
do doing use using later now anything something nothing else other general
""".split())
SOMETHING_FOR_TAIL = frozenset("""
please pls fast quickly quick now asap soon
""".split())
# A problem that is qualified by a pregnancy is not the plain problem. "what helps a headache in
# pregnancy" lands on whichever pregnancy row matches the ask word (back pain, heartburn), and a
# headache remedy handed to a pregnant woman is the ibuprofen problem: the qualifier changes the
# answer, so the frame is left alone and the line keeps the hedged reply it had before.
# The words behind "something for" that name *when* rather than *what*: a birthday, an
# anniversary, a wedding, an age. "get my dad something for his 60th" was framed as "what helps
# 60th", and there is no ailment in that reading - the line asks what to buy someone, which the
# gift rows answer. Kept as its own set because the frame is the only thing wrong with these
# lines: the thing they name is a date, not a problem.
_OCCASION_WORDS = frozenset("""
birthday birthdays bday anniversary anniversaries wedding weddings christening retirement
graduation leaving housewarming
""".split())
SOMETHING_FOR_STATE = frozenset("""
breastfeeding breast-feeding breast feeding trimester expecting
""".split())


# The give, the dose and the feed are what make the person in the line the patient: whatever
# comes back from the tables has to be right for them and not for a grown-up.
SOMETHING_FOR_GIVEN_TO = re.compile(
    r"\b(?:give|gives|giving|gave|given|feed|feeds|feeding|dose|dosing|treat|treating|use|using"
    r"|used)\s+(?:it to\s+|them\s+|him\s+|her\s+)?"
    r"(?:my|the|your|his|her|their|our|this|that|a|an)?\s*"
    r"(baby|babies|newborn|toddler|child|children|kid|kids|son|daughter|boy|girl|child|"
    r"teenager|teen|patient|mum|mom|dad|father|mother|partner|husband|wife|friend)\b")


def _keyed_on_the_person(item, who):
    """Whether the entry answers for this kind of person, not just for the word in the line.

    "can i give my son anything for a cold" reached the cool-bag entry on the words "can" and
    "cold", and that entry says nothing about a son. Only an entry whose own key names the
    person (a child, a baby, a toddler) is that person's answer.
    """
    if not who:
        return False
    keys = _key_words(item)
    person = who.rstrip("s")
    if person in keys:
        return True
    child = {"baby", "toddler", "child", "kid", "son", "daughter", "newborn", "boy", "girl"}
    return bool(keys & child) and (person in child or person in ("teenager", "teen"))


def _something_for(text):
    """The problem from "i need something for a headache" as a question, or "".

    "something for a headache" -> "what helps headache": the entries are keyed on the problem and
    an ask word, and this is the same ask in the words the tables use.
    """
    match = SOMETHING_FOR.search(_flat(text))
    if not match:
        return ""
    rest = [word for word in re.split(r"\s+", match.group(1).strip(" ?.!")) if word]
    # The article stays: the entries key the phrase as people say it ("a cold sore", "a nettle
    # sting"), and "what helps cold sore" is not the same row as "what helps a cold sore". A
    # possessive does not stay: "something for my hay fever" is a question about hay fever.
    while rest and rest[-1] in SOMETHING_FOR_TAIL:
        rest = rest[:-1]
    while rest and rest[0] in ("my", "your", "his", "her", "their", "our"):
        rest = rest[1:]
    if not 1 <= len(rest) <= 6:
        return ""
    # A date is not a problem to ask the tables about. "something for his 60th", "something for
    # my mums birthday", "something for the wedding" all name when the thing is for, and the
    # only thing the frame can do with them is invent "what helps 60th". "something for a
    # headache", "something for his back" and "something for the kids party" name a thing and
    # are untouched, and a bare age is read the same way.
    if all(word in _OCCASION_WORDS or re.fullmatch(r"\d{1,3}(?:st|nd|rd|th)?", word)
           for word in rest):
        return ""
    if {word for word in rest} & SOMETHING_FOR_PEOPLE:
        return ""
    if [word for word in rest if "pregnan" in word or word in SOMETHING_FOR_STATE]:
        return ""
    # "something to do with the kids", "something for later": the thing behind the frame is the
    # frame's own filler, and there is no problem to ask the tables about.
    if not [word for word in rest if word not in SOMETHING_FOR_FILLER]:
        return ""
    return " ".join(rest)


PLAN_RECALL = re.compile(r"\bwhat (?:was|were|am|are) (?:i|we) (?:planning|up to)\b|"
                         r"\bwhat did i say i (?:was|am) (?:planning|up to)\b|"
                         # One part of the plan asked for on its own is the same fact: "which
                         # month are we going" after a trip was answered with the travel entry
                         # for the country, and "when am i moving" with the moving checklist.
                         r"\bwhere (?:are|were|was|am) (?:we|i) (?:going|off|headed|heading|away)\b|"
                         r"\bwhen (?:are|were|was|am) (?:we|i) (?:off|going|away|moving|flying|travelling)\b|"
                         r"\b(?:which|what) (?:month|day|week|date) (?:are|am|is) (?:we|i)\b|"
                         # Only "that": "what day is it" asks what today is, not what the
                         # plan says, so the entry keeps that line.
                         r"\b(?:which|what) (?:month|day|week|date) (?:is|was) that\b",
                         re.IGNORECASE)


def _keeps_a_plan(memory):
    """Whether the store holds a plan to say back. A recall line with nothing kept stays here,
    where the topic's advice is better than "you haven't told me a plan"."""
    known = (memory or {}).get("user") or {}
    return bool(known.get("plan") or known.get("plans"))


# A line that asks what was said before is a memory question, not a question about the topic:
# "what did I call my cats?" after a scratching question is not another scratching question.
RECALL = re.compile(r"\bremind me (?:what|when|where|which|who|how much|how many|that|again)\b|"
                    r"\bdo you remember\b|"
                    r"\bwhat did (?:i|you|we) (?:call|name|say|tell|mention|order|ask)\b|"
                    r"\bwhat (?:do|did) (?:i|you|we) (?:call|name)\b|"
                    # "what do i order" is not a recall: it is what to order, and the place it
                    # names is the question ("what do i order at a kebab shop" was sent here and
                    # came back as a shrug). Only the past tense asks what was ordered.
                    r"\bwhat did (?:i|you|we) order\b|"
                    r"\bwhat (?:was|were) (?:i|we) (?:saying|talking about)\b|"
                    # "how did we start?" asks about this conversation, not about starting a
                    # savings plan: read with the subject on the end it becomes "how did we
                    # start save 3000 pounds car", which the savings entry would answer.
                    # "what have i told you?" is the memory store's whole picture, and read
                    # with the topic written back in ("... money") the savings entry answered
                    # it with advice the person had already been given.
                    r"\bwhat have i (?:told|said|mentioned)(?: you)?(?: so far| again)?\b|"
                    r"\bwhat (?:do|would) you know about me\b|"
                    r"\bhow (?:did|do) (?:we|you and i) (?:start|begin|open)\b|"
                    r"\bhow did (?:this|it|the (?:chat|conversation|talk)) (?:start|begin|open)\b",
                    re.IGNORECASE)


# "what am I planning?" is a question about the conversation itself: the plans memory keeps are
# the answer, and putting the subject on the end turns it into "planning holiday", which the
# holiday checklist then wrongly takes.
# A question about the person themselves: "what am i planning?", "where do i live", "how old am
# i". The answer is in memory, so the subject of the last turn must not be put back on the end of
# it: "where do i live" plus "a trip to rome" is the holiday checklist. Only a question about
# where or who they *are* counts: "where do i start" and "what do i say when they ask why i
# left" are questions about the topic, and they need the subject.
# A "when" that puts the person in the sentence as its subject - "when am i going", "when are we
# back" - asks about their own plan, and the plans memory is where the answer is. The modal forms
# ("when should i go") keep the topic: those ask what to do about it.
WHEN_AM_I = re.compile(
    r"\bwhen\s+(?:(?:am|are|was|were)\s+(?:i|we)\b|"
    r"(?:do|does|did|will)\s+(?:i|we)\s+(?:go|goes|going|leave|leaves|leaving|fly|head off|"
    r"set off|get back|be back)\b)", re.IGNORECASE)


ASKS_MEMORY = re.compile(r"\b(?:what|where|who|when|which|how old|how much|how many)\s+"
                         r"(?:am|was|were|is)\s+(?:i|we)\b|"
                         r"\bwhere (?:do|did|does) (?:i|we) (?:live|work|come from|belong)\b|"
                         r"\bwhat (?:do|did) you know about (?:me|us|my)\b|"
                         r"\bwhat(?:'s| is| was) (?:on|coming up)\b", re.IGNORECASE)


def _with_subject_tail(text, memory, understood=None):
    """The follow-up with what the conversation is about put on the end: "where do i start"
    after "I'm trying to save money" becomes "where do i start save money", which the knowledge
    base can answer. Empty when there is nothing to add, so the line is left alone."""
    tails = _subject_tails(text, memory, understood)
    return tails[0] if tails else ""


def _subject_tails(text, memory, understood=None):
    """The line with the subject on the end, longest subject first, then shorter runs of it.

    "what do i wear" after "a job interview at a warehouse on friday" is about the interview,
    but the whole gist ("job interview warehouse friday") can land on an entry already
    answered, so the shorter runs ("interview warehouse friday", "warehouse friday") are tried
    too and the first one that finds a new entry is the one used.
    """
    subject = mem.subject(memory)
    if not isinstance(understood, dict):
        understood = memory.get("understood")
    if not isinstance(understood, dict):
        understood = {}
    if not subject or len(text.split()) > 10 or len(subject.split()) > 4:
        return []
    if understood.get("kind") == "statement" or not understood.get("asks"):
        return []  # only a follow-up question is written out with the subject
    if understood.get("about_bot") or ABOUT_YOU.search(text):
        return []  # "do you cook much?" is about the bot, not about the dish just discussed
    if re.match(r"\s*(?:what|which|how|who|when|where|why)\b", subject, re.IGNORECASE):
        return []  # "what favourite food" is the leftover of a question, not a thing to name
    if RECALL.search(text) or ASKS_MEMORY.search(text):
        return []  # "what did I call my cats?" is a question for memory, not the topic
    said = {word.strip(".,!?;:").lower() for word in text.split()}
    if said & {word.lower() for word in subject.split()}:
        return []  # the line already says what it is about
    words = subject.split()
    if len(words) == 1:
        # A subject of one word is still a thing: "im thinking of getting a cat" then "what about
        # holidays" reached the work's paid holiday because the tail loop below only builds runs
        # of two words or more, so there was nothing to try and the line's own "holidays" was
        # the whole question. The entry still has to be named by this word and be about the
        # thing (`_named_by` and `_is_about` above), so a line that has nothing to do with the
        # cat is not answered from the cat's rows.
        return [text.rstrip("?.,! ") + " " + words[0]]
    tails = []
    for start in range(0, max(len(words) - 1, 0)):
        tail = " ".join(words[start:])
        if len(tail.split()) < 2:
            break
        tails.append(text.rstrip("?.,! ") + " " + tail)
    return tails

# A question that picks between things and names nothing to pick for: "what should I see?"
# after a trip, "what should I wear?" after an interview, "what could I get her?" after a
# birthday. The thing was said last turn, so the question is answered about it, in the words the
# verb takes: what you see is *in* a place, what you wear is *to* an occasion, what you get is
# *for* a person. Only a line that ends on the verb is read this way, so "what should I wear to
# the wedding" stays its own question.
CHOOSING = re.compile(r"(?:what|which|where)\s+(?:should|could|can|would|do|shall)\s+(?:i|we)\s+"
                      r"(?:[a-z]+\s+){0,2}?(?P<verb>see|visit|watch|play|do|eat|drink|try|wear|"
                      r"take|bring|pack|get|buy|cook|make|give|order|book)\s*"
                      r"(?:her|him|them|there)?\s*\??$", re.I)
# "what could i get her" names the person with a pronoun, and "what should we see there" points at
# the place rather than naming it: the thing under discussion is still the subject, so the line is
# read without the pronoun or the "there".
CHOOSING_PRONOUN = re.compile(r"\s+(?:her|him|them|there)\s*\??$", re.I)
PREPOSITION_OF = {}
for _prep, _verbs in (("in", "see visit watch play do eat drink try"),
                      ("to", "wear take bring pack"),
                      ("for", "get buy cook make give order book")):
    for _verb in _verbs.split():
        PREPOSITION_OF[_verb] = _prep
# The day or the month says when, not what: "job interview thursday" is an interview, and an
# entry keyed "interview" is the one to answer it.
HOLDING_A_NUMBER = re.compile(r"^\d+(?:st|nd|rd|th)?$")
WHEN_WORDS = frozenset("""january february march april may june july august september october
november december jan feb mar apr jun jul aug sep sept oct nov dec monday tuesday wednesday
thursday friday saturday sunday next this last tonight today tomorrow weekend week month year
morning afternoon evening""".split())


def _bare_subject(subject):
    """The subject without the words that say when or how many: "rome july" -> "rome".

    "mum 80th" is a question about mum, and an entry about presents for a mum is the one to answer
    it, so the number goes with the date.
    """
    words = [word for word in (subject or "").split()
             if word.lower() not in WHEN_WORDS and not HOLDING_A_NUMBER.match(word)]
    return " ".join(words) or (subject or "")


# An entry is written for one way of asking and not for another: "what should i get for mum"
# reaches the present entry and "what could i get for mum" does not. The modal is not part of the
# question, so the line is tried with each of them.
MODAL = re.compile(r"\b(?:should|could|can|would|shall|do)\b", re.I)
MODALS = ("should", "can", "could")
# The month the conversation named, when the line itself names none: the packing entry answers by
# season ("For a warm week: light cotton tops..."), so "what should we pack" about a trip in may
# reaches nothing until the may is put back in with the place.
MONTH = re.compile(r"\b(january|february|march|april|may|june|july|august|september|october|"
                   r"november|december)\b", re.I)
# A time word on its own is not a thing to choose for. "i'm getting married in june" leaves june as
# the topic, and "what should i wear to june" is the warm-weather packing entry - a wedding outfit
# answered with shorts and sun cream. So the subject has to be a thing the person named.
TIME_WORD = re.compile(r"^(?:january|february|march|april|may|june|july|august|september|october|"
                       r"november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|"
                       r"spring|summer|autumn|fall|winter|"
                       r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
                       r"today|tonight|tomorrow|yesterday|week|weekend|month|year|"
                       r"(?:next|this|last) (?:week|weekend|month|year|christmas|summer|winter|"
                       r"spring|autumn|fall))$", re.I)


def _the_month(text):
    match = MONTH.search(text or "")
    return match.group(1).lower() if match else ""


# The month only refines a trip. "i'm getting married in june" / "what should i wear" is a
# wedding outfit, and read with the month on the end it became the warm-weather packing entry -
# shorts and sun cream for a wedding. The conversation's own topic says which of the two it is.
TRIP_TOPICS = ("geography-and-travel", "travel", "holidays-and-trips")


def _a_trip(memory):
    """Whether the conversation is about going somewhere, so a month means a season there.

    The last few user lines are read, not just the last one: "we're going to lisbon in may" is
    followed by "it's me and my wife" often enough, and the trip is still the conversation.
    """
    lines = [((mem.current(memory) or {}).get("text") or "")]
    recent = mem.last_user(memory, 5)
    lines.extend(recent if isinstance(recent, (list, tuple)) else [recent])
    for text in lines:
        if not text or not isinstance(text, str):
            continue
        if any(topic in TRIP_TOPICS for topic in understand(text, memory).get("topics") or ()):
            return True
    return False


# A subject with a verb in it is a clause, not a thing. "my kids wont listen to me" leaves the
# subject "kid wont listen", and the shapes below hang a preposition on the subject ("what can i
# do in kid wont listen"), which is not a line at all: the entry it reaches off the one word
# "listen" is a fact from another part of the knowledge base. A thing - "marquee", "nan", "our
# anniversary" - takes the preposition honestly, and the ask's own verb ("what should i wear to
# marquee", "what do i get her") is what names the field.
FINITE = frozenset("""is are was were am be been being do does did dont doesnt didnt wont cant
couldnt shouldnt wouldnt isnt arent wasnt aint not never always keep keeps kept will would
should can could may might must have has had""".split())


def _a_clause(subject):
    """True when the subject carries a verb, so a preposition cannot be hung on it."""
    return any(word.strip(string.punctuation).lower() in FINITE for word in str(subject or "").split())


def _choosing(text, memory):
    """The entry a bare choosing question is about, with the reading and the reply.

    "what should i see" after "i'm going to rome in july" is "what should i see in rome", which
    the entries answer. Only tried when the line on its own found nothing, and the entry has to be
    keyed by the thing itself, so nothing is answered about a neighbour. The reading comes back
    with it because the entry builds its answer from that reading: the city guide needs the city.
    """
    match = CHOOSING.search(text.strip())
    if not match:
        return None
    subject = _bare_subject(mem.subject(memory) or "")
    if not subject:
        return None
    if TIME_WORD.match(subject.strip()):
        return None  # a month or a weekend is not a thing to choose for
    a_clause = _a_clause(subject)
    prep = PREPOSITION_OF[match.group("verb").lower()]
    shapes = [prep + " {s}"]
    if prep == "to":
        shapes.append("to a {s}")
    recent_user = mem.last_user(memory, 3)
    recent_user = " ".join(recent_user) if isinstance(recent_user, list) else str(recent_user or "")
    month = _the_month(text) or _the_month(mem.topic_text(memory) or "") or _the_month(recent_user)
    if month and _a_trip(memory):
        # "what should we pack" about a trip in may is "what should we pack for lisbon in may":
        # the season is part of the question, and the entries answer by season.
        shapes = [shape + " in " + month for shape in shapes] + shapes
    stem = CHOOSING_PRONOUN.sub("", text.strip()).rstrip("?").strip()
    declined = set()
    said = None
    for modal in MODALS:
        asked = MODAL.sub(modal, stem)
        for fuller in (asked + " " + shape.format(s=subject) for shape in shapes):
            reading = understand(fuller, memory)
            item = find(reading)
            if item is None or item.id in declined:
                continue
            if not (_is_about(item, subject) or (month and _a_trip(memory) and _is_about(item, month))):
                continue  # the entry has to be about the thing we put in the line
            # A fact from a field the talk never touched is not this conversation's fact - but
            # only when the words that reached it are the borrowed subject's. A thing borrowed
            # into the ask ("wear to marquee", "get for nan") makes a line the ask itself words,
            # and the entry that answers it is the right one even when the talk is about
            # something else: a nan's birthday must still reach the gifts entry. A clause cannot
            # be borrowed that way, and there the veto stands.
            if a_clause and not about_the_topic(item, reading):
                continue
            reply = _payload(item, memory, reading)
            if not reply.strip():
                declined.add(item.id)  # nothing to say about it
                continue
            if _said_before(reply, memory):
                # The entry was answered earlier in this chat, so the same paragraph would come
                # round word for word: give the part of it this ask names ("what should i see"
                # after a city guide wants the places, not the weather). That is the answer the
                # ask is for even though the whole of it has been said.
                part = narrow(reply, text)
                if (isinstance(part, str) and part.strip() and flat(part) != flat(reply)
                        and not _said_before(part, memory)):
                    return reading, item, part
                if said is None:
                    said = (reading, item, reply)
                continue
            return reading, item, reply
    if said is not None and _asked_again(text, said[2], memory):
        # Nothing fresh and nothing narrower, and this is the same question again: say that is
        # what was said before rather than leave the person with a shrug. "what should i see"
        # after the city guide read "I'd rather not guess" while the sights had been named a turn
        # earlier; a friend says "same as I said: ..." and stops.
        #
        # A different ask ("my washing machine is leaking", then "what do I do?") is not that:
        # the follow-up module says "stop the cycle first, then work down the list I gave you",
        # which is better than handing back the paragraph, so it is left to answer.
        reading, item, reply = said
        if _asks_only_the_length(text):
            # The paragraph is all there is for "how long will that take", and reading it out
            # behind "Same as before" answers nothing: say the answer holds no time and give its
            # first step. The arbiter rightly prefers a search to the paragraph again, so this is
            # the line that has to be here for the person to get an answer at all.
            honest = _figure_missing(reply, text)
            if honest:
                return reading, item, honest
        return reading, item, AGAIN[0].format(reply=_in_short(reply))
    return None


def _only_a_size_of(item, text):
    """True when every word of the line is this entry's own, a size, or the ask itself.

    "how long for 250g" is the chicken question about another weight, so its rate answers it.
    "how long do i roast a 2kg leg of lamb" names a thing this entry is not about, so the
    chicken rate must not be worked out for it.
    """
    words = _key_words(item)
    for word in mem.topics.keywords(text):
        if mem.topics.AMOUNT.search(word) or word in words:
            continue
        return False
    return True


# A person narrowing the choice without naming it: "something funny but not silly" after a film
# question, "nothing scary", "something shorter". The line names no thing and carries no key word
# of its own, so the knowledge base cannot read it: "funny" alone is 2 points against a threshold
# of 4. But the chat has just said what is being chosen between, so the same line with that word
# added ("something funny but not silly film") is one it can read - and it reaches the narrowed
# entry (`film-family-funny`) rather than the general one the bot has just given.
QUALIFIER_OPEN = re.compile(r"^(?:something|anything|nothing|everything)\b")
QUALIFIER_MAX_WORDS = 9


def _choice_words(text, memory):
    """The domain the chat is in and the word naming what it is choosing between.

    The head of the first key part of the entry that answered the topic: "film" for a film
    question, "meal" for a question about dinner. Nothing comes from the line itself, so a
    qualifier that names no thing is only ever rewritten towards the thing already being chosen.
    The topic is the line before this one: the store has already noted this line as the current
    topic, so reading that back would only hand the qualifier its own words.
    """
    line = " ".join(str(text or "").split()).lower()
    earlier = [one for one in mem.context(memory, 3)
               if " ".join(str(one).split()).lower() != line]
    topic = earlier[-1] if earlier else ""
    if not topic:
        return None, []
    found = []
    item = find(understand(topic, memory))
    for part in getattr(item, "key", ()) or ():
        options = (part,) if isinstance(part, str) else part
        # Every word of the first part, because a two-letter head leaves the rewrite unreadable:
        # the entry that answers "nothing on tv tonight" is keyed ("tv", "series", "watch"), and
        # "something funny tv" reaches nothing while "something funny watch" reaches the film
        # table. The head still comes first, so the plainest rewrite is tried first.
        for option in options:
            if isinstance(option, str):
                for word in option.split()[:1]:
                    if word.lower() not in found:
                        found.append(word.lower())
        break  # only the first part: the thing itself, not the words that qualify it
    domain = item.domain if item is not None else None
    return domain, [word for word in found if len(word) > 2]


def _qualifier_rewrites(text, memory):
    """The qualifier line with one word of the choice added, one rewrite per candidate word."""
    clean = " ".join(text.split())
    if len(clean.split()) > QUALIFIER_MAX_WORDS or not QUALIFIER_OPEN.match(clean.lower()):
        return []
    if not mem.current(memory):
        return []
    domain, words = _choice_words(text, memory)
    # A line that leaves a thing out ("anything but a horror") is still a narrowing and is still
    # rewritten: the entry it reaches first is the thing refused, and the refusal guard in
    # `_in_context` and `_offer` passes over that one to the entry that answers around it
    # ("skip horror and gore: *Knives Out* ..."), which is the answer the line is asking for.
    said = {word.strip(".,!?;:").lower() for word in clean.split()}
    rewrites = []
    for word in words:
        if word not in said:
            rewrites.append((clean.rstrip("?.! ") + " " + word, word, domain))
    return rewrites


# A line can refuse a thing in two shapes: the refusal is the whole line ("nothing funny",
# "no horror"), or it is the thing left out of a choice ("anything but a horror", "something
# except horror"). In the second shape the quantifier stands in for a thing, so whatever follows
# "but" is the thing refused, and read only for its own words the line reaches the entry for
# that very thing ("anything but a horror" reached the horror films, because "horror" was the
# one word in it the entries know). Only the bare shape counts as a refusal: "something quick
# but healthy" asks for healthy, and "something funny but not silly" leaves out a way of being,
# which is still a narrowing of the same choice and not a thing the entries answer by name.
#
# The negation alone does not decide it either, because "nothing scary" is a line the horror
# entry answers around ("skip horror and gore"): what matters is whether the answer respects the
# refusal, so the refused thing is what the entries are searched past, not what the line means.
REFUSE_OPEN = re.compile(r"^(?:nothing|no|not)\b(?:\s+(?:a|an|too|very|really))*\s+([a-z']+)", re.I)
REFUSE_CHOICE = re.compile(
    r"^(?:anything|something|everything)\s+(?:but|except|apart from|other than|besides)\s+"
    r"(?:not\s+)?(?:a\s+|an\s+|the\s+|any\s+)?([a-z']+)", re.I)

# The refusal a person makes by saying what they would rather not have: "i dont want a scary
# film", "i hate horror", "i cant stand gore", "im not a fan of musicals". The negation is the
# same one REFUSE_OPEN reads, and what sits in front of it is only a softener ("i really", "i
# just") and the want ("wouldnt want", "dont feel like"), which say nothing about the thing
# refused - but they were enough to stop the line being read as a refusal at all. "i dont want a
# scary film" reached the entry for scary films, whose own choice words ("want", "tonight") are a
# want, and the chat module nodded the line back: "Noted: you don't want a scary film". A want
# with "to" after it is an activity rather than a thing to leave out ("i dont want to cook
# tonight" is a cooking question), so the verb after it stops the match. So does a verb of
# knowing: "i dont know what job i want" rules nothing out, and read as a refusal of "know" it
# stood every row keyed on "dont know" or "no idea" down - the career answer survived only
# because its wording happened to carry the word "nothing" (lime-weasel, #answers 94483).
REFUSE_WISH = re.compile(
    r"^(?:i|we)\s+(?:(?:just|really|actually|honestly)\s+)*"
    r"(?:don'?t|do\s+not|didn'?t|wouldn'?t|won'?t|hate|dislike|loathe|"
    r"can'?t\s+stand|don'?t\s+like|not\s+into|"
    r"(?:im|am|'m)\s+not\s+(?:keen\s+on|a\s+fan\s+of)|not\s+a\s+fan\s+of)"
    r"(?:\s+(?:want|wants|wanting|need|needs|fancy|feel\s+like|like))?"
    r"(?:\s+(?:a|an|the|any|anything|something|everything|nothing|too|very|really|more|"
    r"another|much|lots|of|as))*"
    r"\s+(?!(?:to|be|have|go|get|do|see|watch|read|eat|cook|make|talk|hear|listen|work|"
    r"know|understand|remember|recall|decide|think|believe|reckon|guess|say|tell|imagine|"
    r"it|this|that|one|ones|thing|things|stuff|me|us|them|him|her|my|your|our|their|"
    # A verb of state or feeling is the want, not the thing wanted: "i dont feel anything" was
    # read as a refusal of the word "feel", and an entry about the feeling was stood down as the
    # thing the person had just ruled out, so "i dont feel anything for my baby" got a shrug
    # instead of the post-natal card. The words after the negation here are the want, not the
    # thing, so there is no refusal in the line.
    r"feel|feels|felt|feeling|want|wants|need|needs|fancy|like|likes|care)\b)"
    r"([a-z']+)", re.I)

# What an answer says when it is answering around a refusal rather than ignoring it.
REFUSAL_ACK = re.compile(
    r"\b(?:skip|avoid|steer clear|stay away from|without|instead of|rather than|except|nothing)\b")
# The phrases above that are also how a cooking answer compares two ways of doing something.
# "Wipe rather than wash them" says nothing about leaving the mushrooms out, so "rather than" is
# a refusal only when it stands next to the thing the line refused.
WEAK_ACKS = frozenset(("rather than",))


# A bare refusal is the whole line ("no horror", "nothing too scary"), so the refused word is the
# last one that means anything; only the kind of thing being chosen can come after it ("no sad
# films"). A "no" that is followed by where the thing is, or what it is for, is not a refusal but
# a lack: "no internet on my laptop", "no hot water", "no ideas for dinner". Those lines are about
# the missing thing, and the entry for it - the laptop's wifi, the boiler's hot water - is the
# answer rather than the thing to search past. Reading them as refusals used to throw that entry
# away and leave a line like "no signal on my phone" with an empty acknowledgement.
CHOICE_NOUNS = frozenset(
    "film films movie movies show shows series programme programmes book books game games "
    "music song songs thing things one ones stuff food meal meals recipe recipes".split())
SAID_POLITELY = frozenset("please thanks ta though".split())


def _a_lack_not_a_refusal(flat, end):
    """True when the words after the negated word say what is missing, not what to leave out."""
    for word in flat[end:].strip(" .,!?;:'\"").split():
        word = word.strip(".,!?;:'\"").lower()
        if word and word not in CHOICE_NOUNS and word not in SAID_POLITELY:
            return True
    return False


def _refused(text):
    """The word a line like "nothing funny" or "anything but a horror" rules out, if any."""
    flat = " ".join(str(text or "").split())
    match = REFUSE_CHOICE.match(flat)
    if not match:
        match = REFUSE_OPEN.match(flat)
        if match:
            if _a_lack_not_a_refusal(flat, match.end()):
                return ""
        else:
            # a wish said politely reads the same refusal out of the line
            match = REFUSE_WISH.match(flat)
            if match and _a_lack_not_a_refusal(flat, match.end()) \
                    and not _ASKS_AFTER_A_TASTE.search(flat[match.end():]):
                # The words after a taste are read the way the words after a "no" are, so "i
                # dont like the smell in my fridge" keeps the fridge-smell answer and "i dont
                # like spiders in my house" the spider one. A line that then asks for something
                # is not describing a thing, it is leaving it out of what it asks for: "i dont
                # like mushrooms what can i cook" is a dislike and an ask, and the ask is not
                # the thing that is short.
                return ""
    if not match:
        return ""
    word = match.group(1).strip(".,!?;:").lower()
    return word if len(word) > 2 else ""


# The ask that makes a taste a constraint on it: "i dont like mushrooms what can i cook", "i dont
# want pasta, what should i have instead".
_ASKS_AFTER_A_TASTE = re.compile(
    r"\b(?:what|which|anything|something|suggest|suggestions?|recommend|ideas?|instead|else|"
    r"can i|could i|should i|shall i|do i)\b", re.IGNORECASE)


def _says_it_leaves_it_out(reply, refused):
    """Whether the answer says the refused thing is left out, not merely uses the same words.

    "i dont like mushrooms what can i cook" reached the mushrooms row and was told "Wipe rather
    than wash them", which is how the answer describes a pan: the refusal acknowledgement was
    found in a sentence about something else, and the person who said they did not like the food
    got a recipe for it. A real acknowledgement says it about the thing the line refused - "No
    mushrooms then", "skip horror and gore", "without the cream" - so the phrase has to stand
    next to the refused word to count.
    """
    text = " ".join(str(reply or "").lower().split())
    word = str(refused or "").strip().lower()
    if not text or not word:
        return False
    named = re.compile(r"\b%s\w*\b" % re.escape(word))
    for found in REFUSAL_ACK.finditer(text):
        if found.group(0) not in WEAK_ACKS:
            # "skip horror and gore" leaves the thing out by naming what to avoid, which is
            # not the refused word itself (the line said "scary"), so the strong phrases count
            # wherever they stand.
            return True
        if named.search(text[found.end():found.end() + 40]):
            return True
        if named.search(text[max(0, found.start() - 30):found.start()]):
            return True
    return False


def _hands_back_the_refusal(item, refused):
    """True when the entry is the thing the line ruled out and its answer does not skip it."""
    if not refused or not _is_about(item, refused):
        return False
    if _about_a_lack(item):
        # "no hot water" is not a person refusing hot water, it is a person with none: the entry
        # is keyed on the lack itself ("no hot water", "hot water gone"), so its reply is the
        # answer to the line. Without this the refusal reader stood `no-hot-water` down and a
        # three-word fault got "Got it. Is there anything you'd like a hand with?"
        return False
    reply = getattr(item, "reply", "")
    if callable(reply):
        # The entry worked its reply out for this line, so it has already taken the refusal
        # into account ("No onion then: a leek or a celery stick does the same job"), and
        # there is no fixed text here to read. Only an entry that stores a string can be
        # asked whether it says the thing was left out.
        return False
    return not _says_it_leaves_it_out(reply, refused)


# A key that names the lack itself: "no hot water", "not heating up", "without an oven".
LACK_OPEN = re.compile(r"^(?:no|not|nothing|without)\b", re.I)


def _about_a_lack(item):
    """True when the entry is keyed on a thing being missing, not on choosing one."""
    for part in getattr(item, "key", ()) or ():
        options = (part,) if isinstance(part, str) else part
        for option in options:
            if isinstance(option, str) and LACK_OPEN.match(option.strip()):
                return True
    return False


def _key_words(item):
    """Every word an entry says it is about."""
    found = set()
    for part in getattr(item, "key", ()) or ():
        options = (part,) if isinstance(part, str) else part
        for option in options:
            for word in str(option).lower().split():
                found.add(word.rstrip("s") or word)
    return found


# How far into the line the thing a line names for itself can sit and still be its own subject:
# "my knee keeps clicking, is that normal" opens with its knee, "how do I bring it up without
# ruining the friendship" only mentions a friend at the end.
OWN_THING_AT = 3

# How far into a longer line the same search goes: "i really do hate my job" puts the possessive
# four words in, and the thing after it is still what the line is about.
OWN_THING_SCAN = 12

# The words that make the next word a thing of the speaker's own: "my back hurts" opens with a
# back, whether or not the understanding engine calls it an entity.
POSSESSIVE = frozenset("my our his her their".split())

# A person in the line is usually the one doing something, not the thing being asked about: "my
# son spilt juice on it" is a question about the juice. These words are checked only when the
# understanding engine has not tagged the person itself.
PERSON_WORDS = frozenset("""son daughter husband wife mum mom dad father mother partner
    boyfriend girlfriend brother sister kid kids child children baby toddler friend mate
    neighbour neighbor colleague boss teacher nan grandma grandad granny grandchild flatmate
    housemate lodger guest visitor landlord tenant aunt auntie uncle cousin nephew niece
    grandparent parents folks family
dog cat puppy kitten pet""".split())


def _names_a_thing(understood):
    """True when the line names something other than a person: the juice in "my son spilt juice
    on it", the knee in "my knee keeps clicking"."""
    for ent in understood.get("entities") or []:
        if isinstance(ent, dict) and str(ent.get("type") or "") not in ("person", ""):
            return True
    return False


def _own_thing(understood):
    """The thing the line itself opens with, when it opens with one.

    A line can lean on the last topic and still start a subject of its own: after a friend who
    keeps cancelling, "my knee keeps clicking, is that normal" is a knee question, and after a
    bottle of wine it is still a knee question. Nothing is named here for a line that only asks
    about the old thing ("how long will it take?", "he's allergic to nuts").

    A person is not that subject when the line names a thing as well: "my son spilt juice on it"
    after a sofa-cleaning turn is still a question about the juice, and the cleaning answer is the
    right one. A person on their own ("my mum keeps forgetting things") is a subject, and it is
    not the last topic.
    """
    person = ""
    for ent in understood.get("entities") or []:
        if not isinstance(ent, dict):
            continue
        at = ent.get("at")
        if isinstance(at, int) and 0 <= at <= OWN_THING_AT:
            text = str(ent.get("text") or "")
            if str(ent.get("type") or "") == "person":
                person = person or text
                continue
            return text
    if person:
        return "" if _names_a_thing(understood) else person
    boilerplate = str(understood.get("clean") or understood.get("text") or "").split()
    # "i hate my job" opens with no subject of its own if only the first word is read, and the
    # line then leans on the last topic and is answered as if it were still about it: after
    # "i love dogs and cats" the words put back on the end reached the cats-and-dogs entry,
    # because "hate" is one of its key words. The thing a line calls its own is the thing after
    # "my", "our", "his", "her" or "their" wherever that falls in the line, not only when the
    # line starts with it: "i really do hate my job" is a job line in the same way "my job is
    # awful" is.
    for at, word in enumerate(boilerplate[:OWN_THING_SCAN]):
        if word.strip(".,!?;:").lower() not in POSSESSIVE:
            continue
        if at + 1 >= len(boilerplate):
            break
        span = [w.strip(".,!?;:").lower() for w in boilerplate[at + 1:at + 4]]
        if not span or span[0] in REFERRING:
            continue
        # "my new sofa" is a sofa: the engine has already named it, and its name is the last word
        # of the phrase rather than the word straight after the possessive.
        named = _thing_named_in(understood, span)
        if named:
            return named
        second = boilerplate[at + 1].strip(".,!?;:")
        if second.lower() in PERSON_WORDS and _names_a_thing(understood):
            continue
        if second:
            return second.lower()
    return ""


def _thing_named_in(understood, span):
    """The thing the understanding engine named among these words, if it named one."""
    for ent in understood.get("entities") or []:
        if not isinstance(ent, dict):
            continue
        text = [w.lower() for w in str(ent.get("text") or "").split()]
        if not text or len(text) > len(span):
            continue
        for i in range(len(span) - len(text) + 1):
            if span[i:i + len(text)] != text:
                continue
            if str(ent.get("type") or "") == "person" and _names_a_thing(understood):
                return ""
            return text[-1]
    return ""


def _new_thing(own, answer):
    """True when the line names a thing the answer never mentions: a knee is not leftovers.

    "my knee keeps clicking, is that normal" after a leftovers answer leaned on the last topic and
    came back with the sentence about how long they keep, because "keeps" was the only word the
    two lines had in common.
    """
    if not own:
        return False
    words = {word.strip(".,!?;:").lower() for word in str(answer).split()}
    return not any(word.rstrip("s") in words or word in words for word in own.lower().split())

def _the_run_said(memory, extra=""):
    """What this run of answers has said, read as one answer.

    A follow-up can follow a follow-up: "how do i make pancakes for four", "how many eggs is
    that", "and how much flour". The third line names a thing from the first answer, not from
    the short line just before it ("2 eggs." does not mention flour), so asking whether the
    line names something new has to read the whole run, or every second follow-up looks like a
    new question and drops to the fallback.
    """
    turns = memory.get("turns")
    said = [str(extra or "")]
    answered = 0
    if isinstance(turns, list):
        for turn in reversed(turns):
            if not isinstance(turn, dict):
                break
            if turn.get("module") != "answers":
                if answered:
                    break
                continue  # the line just typed carries no module yet
            said.append(str(turn.get("bot") or turn.get("reply") or ""))
            answered += 1
            if answered >= 4:
                break
    return " ".join(part for part in said if part)


def _head_thing(subject):
    """The thing a subject names, when it names one: "my sourdough keeps going flat" is the
    sourdough. A subject that names no thing ("im training for a marathon" is about the
    training) gives nothing back, and the subject's own words are all the reading there is."""
    return _own_thing(understand(subject)) if subject else ""


# A word that only describes the thing is not the thing: after "how do i keep herbs fresh" the
# subject is "keep herb fresh", and the entry that keeps herbs is about the herb, not the fresh.
DESCRIBING = frozenset("""
fresh frozen cooked raw uncooked leftover leftovers ripe open opened unopened whole sliced cut
peeled dried dried-out tinned canned stale
""".split())


def _the_same_kind_of_thing(item, memory, text=""):
    """True when the entry's domain answers the topic the chat is on.

    The thing in hand is read by the understanding engine ("my back hurts" is a health line) and
    every knowledge domain declares the topics it answers (bot/knowledge.by_topic), so an entry
    whose domain answers that topic is about the same kind of thing as the chat however few
    words the two happen to share.

    The thing in hand is the one the follow-up is about, and a turn that adds a detail moves the
    topic onto the detail: "my back hurts" then "i use a strap already" then "do i need to see a
    physio" is still a question about the back, but the topic the store is on by then is the
    strap, which no health entry answers. A detail is recorded with the thing it is a detail of
    (`of`, see bot/memory/topics), so the line is read back through that chain, which is what
    `topics.carried_topic` does for the rest of the reader.
    """
    try:
        domain = str(getattr(item, "domain", "") or "")
        if not domain:
            return False
        record = (mem.topics.carried_topic(memory, text) if text else None) or the_topic(memory)
        said = str((record or {}).get("text") or "")
        if not said:
            return False
        about = str((understand(said, {}) or {}).get("topic") or "")
        return bool(about) and about in by_topic().get(domain, ())
    except Exception:  # noqa: BLE001 - a reading that fails leaves the guard as it was
        return False


def _reaches_another_subject(text, item, memory):
    """True when the entry the line reaches is about something the conversation is not.

    A follow-up names no thing of its own, so it is answered on its bare words: "any other
    ideas" is the key word of the quick-dinners entry and of nothing else, so a chat about films
    got "Quick: tuna pasta in 15, macaroni cheese in 25". The check is on the words around the
    line - the current topic's own words and the subject's - against the entry's: when the entry
    shares none of them it is a different subject, and no wording makes that the answer.
    """
    try:
        if not is_follow_up(text, memory):
            return False
        # A line that carries a subject of its own is a new question, whatever the chat was
        # about: "what can i make with eggs" in the middle of a film chat is a cooking question
        # and the omelette is its answer. Only a line that names nothing of its own can be
        # answered from another subject, and this is the read that says which it is. Without it
        # every "what can i make with eggs/leeks/chicken/mince" was dropped as a follow-up on
        # another subject and fell through to the hedge, while the meal was in the table all along.
        if str((understand(text, {}) or {}).get("topic") or ""):
            return False
        # Nothing has been said before this line, so there is no subject it could be reaching
        # past: the store records the line as the current topic before the entry is looked up,
        # so on the first turn of a conversation "what can i make with mince" is a follow-up of
        # itself, shares no word with the dinners entry's keys ("cook" is in them and "make" is
        # not) and stood down - the person got the search hedge, while "what can i cook with
        # mince" got the recipe. A guard against answering the wrong subject has nothing to
        # protect on a first line.
        if not (memory.get("turns") if isinstance(memory, dict) else None):
            return False
        around = {str(word).lower() for word in ((the_topic(memory) or {}).get("words") or ())}
        around |= {str(word).lower() for word in keywords(mem.subject(memory) or "")}
        if not around:
            return False
        # The entry's keys carry the grammar too ("any", "something"), so both sides go
        # through keywords(): "any other ideas" shares the word "something" with the dinners
        # entry and nothing else, and that is not a subject in common.
        keys = set(keywords(" ".join(str(word) for word in _key_words(item))))
        # A placeholder is not a subject either: "something" is in the topic's words and in the
        # dinners entry's keys, and on its own it says nothing about the thing being discussed.
        around = {word for word in around if word not in VAGUE}
        keys = {word for word in keys if word not in VAGUE}
        # Two entries about the same kind of thing are not another subject. "do i need to see a
        # physio" after "my back hurts" is a question about the back, and the physio entry is a
        # body entry - but the two share no word, because the chat's words are "back" and "hurt"
        # and the entry's keys are "physio" and the ask, so the word test stood it down and the
        # person got the search shrug while the answer ("see a physio if the pain has lasted more
        # than a fortnight") was there all along. The domain is what both of them are about, so
        # the guard reads it as well as the words.
        if _the_same_kind_of_thing(item, memory, text):
            return False
        # A line asking what the entry's own word means is a new subject in so many words: "what
        # is inflation" after a back pain chat asks about inflation, and the trouble the talk was
        # on has nothing to do with it. Read as a follow-up on that, the money row was dropped for
        # a search hedge the table answers.
        if _a_definition_of_the_entry(text, item):
            return False
        return bool(keys) and not (keys & around)
    except Exception:  # noqa: BLE001 - a reading that fails just leaves the entry alone
        return False
# A line that adds a detail to what the chat is on - "i water them every day" after "my tomato
# plants have yellow leaves" - is a line about that thing and nothing else: the pronoun has no
# other thing to point at. Read in context it carries the topic's words along, but the detail's
# own words travel with it too, and on their own they reach an entry from somewhere else
# entirely: "water" and "every day" reached the daily figure for drinking water, "feed" and
# "every week" reached a meal plan. So the entry that answers such a line has to belong to the
# answer on the screen - its domain, or a word of the topic it is meant to be about. One that
# does neither is answering a different question.
DETAIL_OF = re.compile(
    r"^\s*(?:and\s+|so\s+|also\s+)?(?:i|we)\s+(?:also\s+|just\s+|still\s+)?(?:[a-z']+\s+)?"
    r"(?:it|them|they|him|her|these|those)\b", re.I)
# A question about the thing in hand - "how long will it take", "can i make it the day before" -
# names no thing of its own either: "it" and "that" are the thing the chat is on. Its own words
# are the leftover ones which reach an entry about the thing's neighbour: "how long will that
# take" after "im going to paint my kitchen" reached the kitchen-cleaning routine.
ASK_OF = re.compile(
    r"^\s*(?:and\s+|so\s+)?(?:how|what|when|where|which|who|should|shall|can|could|do|does|"
    r"did|will|would|is|are|was|were|if|any)\b", re.I)
OBJECT_PRONOUN = re.compile(r"\b(?:it|them|that|this|those|these|one)\b", re.I)
# What a line about doing something to the thing in hand is made of: the verb of the doing, and
# the words that make it a report of what they do rather than a question - an amount, a
# frequency, a time. A line naming a thing of its own ("i bleed the radiators every year") is a
# follow-up of its own kind and is left alone.
DO_VERBS = frozenset("""
water feed clean wash trim cut prune mow repot mist move cover drain bleed charge replace change
check add give take put turn leave run walk play use paint sand oil service tidy hoover dust
eat drink make cook bake freeze reheat serve store keep need want get buy pay sell work go come
""".split())
REPORT_WORDS = frozenset("""
day days week weeks month months year years morning evening night time times once twice daily
weekly monthly yearly every each a an all the at in on of and but to for with it them they him
her these those i we my our just still also really always never usually sometimes about
much many lot little bit twice three four five six two one few several
last next ago past
""".split())
# The asking words of a question that names no thing of its own, so a line made of these and an
# object pronoun is a question about the thing in hand: "how long will it take", "can i make it
# the day before", "should i freeze it".
ASK_WORDS = frozenset("""
how what when where which who why should shall can could would will do does did is are was were
if any ok okay please before after since until tonight tomorrow today again too soon often long
take need want have has keep use get put make cook freeze reheat serve store prepare
it that this these those them they him her one ones
""".split())

# A colour said of the thing in hand is that thing's property, not a thing of its own: "i painted
# it green last year" is a detail about the room, and "green" on its own reached the bag of salad
# in the fridge. The colour belongs to the line's own object, so it cannot make the line a
# follow-up in its own right.
SAID_OF_THE_THING = frozenset("""
red blue green yellow white black grey gray brown pink purple orange cream beige navy teal
turquoise lilac mauve magenta gold silver bronze ivory charcoal
""".split())


def _off_the_topic(understood, memory):
    """(the topic's key words, the domain of the entry that answers it, whether the line says what
    the thing is) when this line is a detail about that topic, else (empty, "", False).

    The third part is what tells a detail that names something of its own from a detail that only
    says what was done: "i painted it green last year" says what the room is, and the salad in the
    fridge was answering it; "i painted it last year" says what they did, and leaves the subject
    to the chat - so the fence below is only thrown around the line that says what the thing is.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return frozenset(), "", False
    text = understood.get("clean") or understood.get("text") or ""
    detail = "?" not in text and bool(DETAIL_OF.search(text))
    # A question with an object pronoun and nothing else of its own is about the thing too.
    asking = bool(ASK_OF.search(text) and OBJECT_PRONOUN.search(text))
    if not (detail or asking):
        return frozenset(), "", False
    allowed = (REPORT_WORDS | DO_VERBS | (ASK_WORDS if asking else frozenset())
               | (SAID_OF_THE_THING if detail else frozenset()))
    # Anything it names of its own makes it a follow-up in its own right: "i bleed the
    # radiators every year" says what it is about, so it is left to the entries as it is.
    # A word in the form a person puts a verb ending on is still the allowed word: "i painted it
    # green last year" said "painted" where the list holds "paint", so the line was read as one
    # naming a thing of its own and the salad in the fridge answered a question about a room.
    says_what_it_is = False
    for word in said_topic.words(text):
        if word.isdigit() or word in allowed or (said_topic.forms(word) - {word}) & allowed:
            if detail and word in SAID_OF_THE_THING:
                says_what_it_is = True
            continue
        return frozenset(), "", False
    leans_on = understood.get("leans_on")
    if not isinstance(leans_on, dict):
        return frozenset(), "", False
    said = str(leans_on.get("text") or "")
    if not said:
        return frozenset(), "", False
    # What the detail is about is the answer that is on the screen: the entry behind it, and the
    # topic's own words. An entry from another domain is answering a different question that
    # happens to have the detail's words in it.
    last = memory.get("last_answer") if isinstance(memory.get("last_answer"), dict) else {}
    domain = str(last.get("domain") or "")
    if not domain:
        home = find(understand(said, memory))
        domain = str(getattr(home, "domain", "") or "")
    # Only the topic's own nouns: the doing words are shared with every entry about doing
    # something, so "eat" in "she doesnt eat meat" does not make a workout answer about her.
    words = {word for word in said_topic.keywords(said)
             if word not in REPORT_WORDS and word not in DO_VERBS and word not in ASK_WORDS}
    return frozenset(words), domain, says_what_it_is


def _from_another_domain(item, off_topic):
    """True when the entry is about neither the topic's words nor the topic's own kind of thing."""
    words, domain = off_topic[0], off_topic[1]
    if domain and str(getattr(item, "domain", "") or "") == domain:
        return False
    return not _names_a_topic_word(item, words)


def _names_a_topic_word(item, wanted):
    """True when the entry is keyed on one of the words, in any of their forms.

    Only the word itself or its stem: a looser match makes "plant" and "plan" the same thing,
    and the meal plan came back as an answer about tomato plants that way.
    """
    keys = {str(key).lower() for key in _key_words(item)}
    for word in wanted:
        if word in keys or said_topic.stem(word) in keys:
            return True
    return False



# Words that say how the ask is meant, not what it is about: "what should I change first" is a
# question about whatever the conversation is on, and "first" is in the keys of half the world.
BARE_GENERIC = frozenset("""first next best else last thing things way ways part bit most least
    change changing start starting stop stopping more right now then again still only just""".split())


# The verbs of asking, which name nothing on their own: "what should I look for" is a question
# about whatever the conversation has been about, "what could I bake for a birthday" is not.
ASKING = frozenset("""look looking wear wearing do does get getting pick choose need buy
    prepare bring bring take taking use check expect know say tell ask want find worth""".split())


# Asking what to say, rather than what to do: an answer about clothes or a timetable does not
# answer it, however well the topic fits.
SPEECH = frozenset("""say saying tell telling ask asking talk talking phrase wording word
    mention explain explaining""".split())


# A time says when, not what: an entry keyed to "june" is a holiday in the sun, and a move in
# June is not one. So a word the topic and the entry only share as a when never carries an entry.
TIME_WORDS = frozenset("""january february march april may june july august september october
november december jan feb mar apr jun jul aug sep sept oct nov dec monday tuesday wednesday
thursday friday saturday sunday weekend weekday morning afternoon evening night tonight today
tomorrow yesterday week weeks month months year years next this last first soon""".split())


def _topic_words(line, memory):
    """The words of the topic this line carries on from, without the words the line already
    says and without the words that only say when: those name nothing the entry can be about."""
    said = set(mem.content(line))
    record = mem.topics.carried_topic(memory or {}, line) or {}
    return [word for word in mem.content(record.get("text") or "")
            if word not in said and word not in BARE_GENERIC and word not in TIME_WORDS]


def _lent_words(reading, memory):
    """The words the topic lent this line when it was read with it.

    The topic can be the last line, which says little ("something funny but not stupid"), or the
    question two turns back that it belongs to ("what should I watch tonight"): the reading that
    was widened is the one that knows which of them the ask is really on, so its added words are
    what the entry has to be about.
    """
    line = str(reading.get("clean") or reading.get("text") or "")
    said = set(mem.content(line))
    wider = mem.followup_reading(reading, memory or {})
    added = str(wider.get("clean") or wider.get("text") or "") if isinstance(wider, dict) else ""
    words = [word for word in mem.content(added) if word not in said]
    if not words:
        return _topic_words(line, memory)
    return [word for word in words if word not in BARE_GENERIC and word not in TIME_WORDS]


def _same_word(word, said):
    """True when two words are the same word, endings and all: "friend" is not "friendship" but
    "friend" and "friends" are, and "ruin" and "ruining" are."""
    if word == said:
        return True
    if len(word) < 4 or len(said) < 4:
        return False
    return word.startswith(said) or said.startswith(word)


def _writes_its_own_reply(item):
    """True when the entry writes its answer from the reading instead of storing one.

    The weather answers are a function of the place and the month ("May in Rome is usually about
    15 to 24C"), so the entry's own text has the topic's words nowhere in it: `hits` is empty
    for every one of them however well the entry fits, and the check that an entry is about the
    topic cannot be made against the reply. Such an entry is reached only by the place and the
    month in the reading, which is the topic's own word, so it is about the topic by
    construction - and without this, "whats the weather like there" after "im going to rome in
    may" stopped being the figures and became "No live weather here, sorry" (main, where the
    only match was the widening and the guard turned it down).
    """
    return callable(getattr(item, "reply", None))


# The verbs a bare ask is made of, which name nothing an entry can be about: "what helps", "what
# works", "how do i fix it" are all questions about the thing the chat is already on.
ASKING_VERBS = frozenset("""help helps helped helping work works worked working fix fixes fixing
                         sort sorts sorted deal deals coping cope handle handles try tries""".split())


def _leans_on(reading, item, memory=None):
    """True when an entry reached only with the last topic belongs to the line's own words too.

    A short question with no subject of its own is read with the topic, which is what makes
    "what should I wear" an outfit question after a wedding. A question that names something of
    its own ("what could I bake for a birthday") must not be carried off to whatever the last
    turn was about: the entry has to be about one of the line's own words, in its keys or in
    what it says. And a line asking what to *say* needs an entry about words, not about clothes.
    """
    line = reading.get("clean") or reading.get("text") or ""
    line_words = mem.content(line)
    # A month or a season says when, not what: "and in october" after the Rome figures in May is
    # the same question about another month, and the month is the entry's slot rather than a
    # word in its keys, so it is not a subject the entry has to name.
    # A verb that is the ask itself is not a thing the entry has to be about: "what helps" after
    # the shower-drain answer is the same question about the same drain, and the drain entry does
    # not have to say "help" anywhere for that to be true. Without this the line counted "help"
    # as a subject of its own, the entry was read as not about the line, and the turn went to the
    # search hedge - while the same word in the entry's own paragraph ("what helps most") would
    # have made it a follow-up.
    own = [word for word in line_words
           if word not in ASKING and word not in BARE_GENERIC and word not in ASKING_VERBS
           and word not in mem.topics.MONTH_NAMES and word not in mem.topics.SEASONS]
    # "what should I change first" is all ask: no subject of its own and nothing but first/next
    # in it, so one shared word ("security") must not decide which entry answers it.
    vague = not own and any(word in BARE_GENERIC for word in line_words)
    keyed = _key_words(item)
    says = set(keyed)
    reply = getattr(item, "reply", "")
    if isinstance(reply, str):
        says |= {word.strip(string.punctuation).rstrip("s") for word in reply.lower().split()}
    topic = _topic_words(line, memory)
    carried = (mem.topics.carried_topic(memory or {}, line) or {}).get("text") or ""
    topic_text = " ".join(str(carried).lower().split())
    subject_of_the_topic = ([str(word).lower() for word in mem.key_subject(carried, memory)]
                            if carried else [])
    about = subject_of_the_topic or topic
    about_text = " ".join(subject_of_the_topic) or topic_text
    lent = _lent_words(reading, memory)
    hits = {word for word in lent if any(_same_word(word, other) for other in says)}
    # An entry that names what the topic is *not* is not about the topic: a phone that dies by
    # lunchtime is not the car battery the entry is written for, and its "phone" is in that
    # entry's avoid list. Saying so with the topic's words is the same test the line gets, but
    # only when the topic is all the entry has: a line that names the entry itself is its own
    # subject, and an entry that keeps feelings out of a packing question is still the packing
    # answer for "the packing is the worst bit" after a line about being stressed.
    avoid = getattr(item, "avoid", ()) or ()
    # Only a word that names something counts as naming the entry: "first" is in half the keys in
    # the world ("what happens at security first"), so the property words are left out here.
    named = [word for word in own if word not in PROPERTY_WORDS] or own
    names_it = any(_same_word(word, said) for word in named for said in keyed)
    # An entry that names what the topic is *not* is not about the topic: a phone that dies by
    # lunchtime is not the car battery the entry is written for, and its "phone" is in that
    # entry's avoid list. This one is checked even when the line names the entry ("should i get
    # the battery replaced" is about the phone), because the topic decides what the thing is.
    # A feeling in the topic is not a thing, though: an entry that keeps feelings out of a
    # packing question is still the packing answer for "the packing is the worst bit" after a
    # line about being stressed.
    def _it_says_it_is_not(phrase):
        """True when the avoid list names what the topic is: a word of the topic, or a phrase
        said across the topic's own sentence ("learn to swim" is two words of the topic list).

        It is the thing the topic is about that is tested, not the ask it made about it: the
        topic "when did the romans leave britain" is about the Romans in Britain, and "leave"
        is only what was asked there, so it does not make the length of the stay a different
        subject. The whole of the topic is used when its subject words are not known, which is
        where the test was before.
        """
        phrase = phrase.strip().lower()
        if not phrase or phrase in FEELINGS:
            return False
        return phrase in about or (" " in phrase and phrase in about_text)
    if any(_it_says_it_is_not(word) for word in avoid if isinstance(word, str)):
        return False
    if not own:
        # The line names nothing at all ("what can I do", "what should I change first"), so the
        # entry has to be about the topic by more than one word: a single generic word is enough
        # to take "security codes by text" to the airport scanner, which is a wrong answer where
        # an honest shrug is not.
        return len(hits) >= (2 if vague else 1)
    ask_side = [word for word in own if word not in PROPERTY_WORDS]
    if not ask_side:
        # The line names a property of the topic and nothing of its own ("what can we do before
        # the first day" in a thread about starting school), so the entry has to be about the
        # topic, not about the property: the words before/first/day decide no entry by
        # themselves, and every entry has a "day" somewhere in it.
        return bool(hits)
    if not any(_same_word(word, said) for word in own for said in says):
        if not _a_money_question(own, keyed):
            return False
        # The two ways of asking what a thing costs are one question, and an entry is written
        # with whichever of them the person it was written for would use: the Rome budget row is
        # keyed on "expensive", so "is that cheap" after the same trip was dropped here and the
        # search hedge went out while "is it expensive" got the price. "cost" and "price" are in
        # the family too, because the price rows are keyed with those words as well.
    if (not hits and not _writes_its_own_reply(item)
            and mem.topics.next_slot_reading(reading, memory or {}) is None):
        # The line names its own thing and the entry is not about the topic at all: it is only
        # the words the ask put back in that reached it, so the answer would be about something
        # else ("what should I pack first" answered with a holiday when the move is the subject).
        # A line that only names the next thing of the same ask ("and for lunch") is the ask
        # carried on rather than the topic, so the topic is not what the entry has to match.
        return False
    if set(line.lower().split()) & SPEECH and not says & SPEECH:
        return False  # "what should I say on the first day" is not a question about clothes
    return True



def _is_about(item, subject):
    """True when the entry is about the thing, not about a neighbour: a stew is not a steak."""
    words = [word for word in subject.split() if word not in DESCRIBING] or subject.split()
    head = (words or [""])[-1]
    head = head.rstrip("s") or head
    if not head or head not in _key_words(item):
        return False
    if head in kinds.VERBISH or (len(head) > 4 and head.endswith(("ed", "ing"))):
        # A whole clause can stand where the thing should be, and a clause puts its verb last:
        # "my headphones stopped working" is about the headphones, and the pension entry answers
        # "how long does it last" only because "working" is one of its keys ("stop working").
        # When the head is the verb, the entry also has to name something else the clause says.
        named = [word for word in words if word not in kinds.VERBISH
                 and not (len(word) > 4 and word.endswith(("ed", "ing")))]
        keys = _key_words(item)
        return any(word.rstrip("s") in keys or word in keys for word in named)
    return True


# Where a thing is cooked or kept is not a new subject: "how long does it keep in the fridge" and
# "how long in the oven?" stay about the food the last answer was about.
PLACE_WORDS = frozenset("""
fridge freezer oven grill hob microwave pan pans pot pots tray tin tins dish dishes shelf
cupboard counter worktop sink kettle toaster air fryer barbecue bbq fridge-freezer larder
room kitchen outside indoors
""".split())


# A reply that works a goal out at several rates each month, e.g. "£100 a month is 50 months".
SUM_TABLE = re.compile(r"£[\d,]+ a month is \d")

# A state of mind, not a thing the entry could be about: an avoid list keeps these out of a
# question about the subject ("not while you're stressed"), and the topic saying one does not
# make the entry about something else.
FEELINGS = frozenset("""stressed stress stressed-out worried worry anxious anxiety nervous sad
    upset feeling feelings scared afraid frightened terrified angry cross annoyed frustrated
    happy glad excited relieved tired exhausted shattered overwhelmed guilty ashamed embarrassed
    lonely fed-up down low rubbish awful terrible horrible upset gutted excited keen fuming
    panicking panic crying upset""".split())


PROPERTY_WORDS = frozenset("""long time times minute minutes hour hours day days much many far often temperature temp temps
degrees centigrade fahrenheit heat
hot warm cold size price cost spend pressure bar psi
spending pay paying per kilo kilos kg gram grams start finish last first take takes need needs
one ones
rest resting hard soft runny jammy medium rare fan gas thick thin large small whole skimmed semi
cook cooking bake baking roast roasting boil boiling fry frying grill grilling leave leaving
sit sitting wait waiting cool cooling chill chilling set setting
causing caused cause causes why reason worth worths valued value
# A date is a property of the answer too: after a dated answer, "when did that happen" and
# "what year was that" name the part they want and no subject of their own.
year years date happen happened done
""".split())


def _only_a_property(words):
    """True when the line names no subject, only the property it asks about."""
    return bool(words) and not [word for word in words if word not in PROPERTY_WORDS]


# A property word can also be the thing itself: a cold is an illness, a light is a lamp, a price
# is what something costs, a date is when it happens. The words are in PROPERTY_WORDS because the
# same word asks about a property ("how cold is it", "what price is that"), so the article is what
# tells the two apart. Without this, "i have a cold" -> "how long does a cold last" read the
# second line as a bare length ask about the first answer, and the greeting said how long a job
# takes instead of answering the cold.
PROPERTY_WORD_THAT_NAMES_A_THING = re.compile(
    # A determiner before the word makes it a thing: "a cold", "my light", "the price".
    r"\b(?:a|an|the|my|your|his|her|their|our|this|that|these|those|any|no)\s+"
    r"(?:colds?|heats?|lights?|darks?|prices?|costs?|sizes?|times?|dates?|years?|days?"
    r"|starts?|finishes?)\b"
    # A plural of one of these words is a thing even with no determiner: "how long do colds
    # last" was still read as a bare length ask, while "how cold is it" keeps the adjective.
    r"|\b(?:colds|lights|prices|costs|sizes|dates|starts|finishes)\b",
    re.I,
)


def _a_property_word_names_a_thing(text):
    """True when a property word in the line is the thing the line is about, not the ask.

    "how long does a cold last" is the cold's question; "how cold is it" is the sky's. Only a
    line that is otherwise all property words needs this test, so it is cheap.
    """
    return bool(PROPERTY_WORD_THAT_NAMES_A_THING.search(str(text or "")))


# What a thing costs, said either way round. A person asks "is it expensive" as often as "is
# that cheap", and a knowledge entry keeps one of the two in its keys, so an entry about the
# price is about both questions.
MONEY_ASK = frozenset("""
cheap cheaper cheapest expensive pricey costly dear affordable cost costs costing price prices
priced charge charges fee fees
""".split())


def _a_money_question(own, keyed):
    """True when the line asks what a thing costs and the entry is keyed on what a thing costs.

    The keys, not the answer's words: a bike-buying entry says "worth" and "check" and talks about
    a price in its answer, and it is not the price row the pronoun question is asking for.
    """
    return bool(set(own) & MONEY_ASK) and bool(set(keyed) & MONEY_ASK)


def _remember_answer(memory, item, reply, keys=()):
    """Keep what a follow-up can ask about again: the answer, what it is about, its turn.

    `keys` is for an answer that came from no entry: the words the answer was chosen for, when
    there is no entry to take them from.
    """
    if not isinstance(reply, str) or not reply.strip():
        return
    turns = memory.get("turns")
    memory["last_answer"] = {
        "reply": reply,
        "keys": sorted(_key_words(item) | set(keys)),
        "id": getattr(item, "id", None),
        "domain": getattr(item, "domain", "") or "",
        "turn": len(turns) if isinstance(turns, list) else 0,
    }


def _last_answer(memory):
    """The answer just given, while the conversation is still about the same thing.

    The answer has to be recent and from this module. A new topic ends the run, so "how long
    should I rest it" after a knee statement cannot reach the potatoes from three turns back.
    A detail line that stays on the subject ("my oven is fan assisted") does not end it: the
    answer is still about what is being said when the entry and the line share a word.
    """
    record = memory.get("last_answer")
    if not isinstance(record, dict) or not record.get("reply"):
        return None
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return None
    turn = record.get("turn")
    if not isinstance(turn, int) or turn < 0 or turn >= len(turns):
        return None
    if len(turns) - 1 - turn > 4:
        return None
    said = turns[turn] if isinstance(turns[turn], dict) else {}
    if said.get("module") != "answers":
        return None
    topic = mem.current(memory)
    if not isinstance(topic, dict) or not isinstance(topic.get("turn"), int):
        return None
    if topic["turn"] > turn:
        here = set(keywords(topic.get("text") or ""))
        if not here & set(record.get("keys") or ()):
            return None  # a new subject started after the answer
    return record


def _asks_part(text):
    """True when the line asks for one part of the answer and names no subject of its own."""
    if asked_kind(text) == "cause" and not keywords(text):
        return True  # "why?" is the ask on its own
    if asked_kind(text) is not None:
        return _only_a_property(keywords(text))
    # A step or a property question names the part in its own words ("parboil", "crisp");
    # narrow() matches those against the answer and returns None when it cannot.
    return asks_a_part(text)


# A yes/no about a thing the last answer named: "will salt work", "does vinegar help", "can i use
# a hairdryer". The line names no subject of its own, so it is a question about the answer just
# given, and the sentence of that answer which names the thing is the part that answers it.
YES_NO_ABOUT_A_THING = re.compile(
    r"^\s*(?:will|would|does|do|did|can|could|should|shall|is|are|was|were|has|have|must|might)\b",
    re.I)

# Words a line uses about an answer rather than about a thing in it: "will salt work" asks about
# salt, and "work" is there because it is a yes/no, not because the answer has to say it.
# The words a line uses to ask a question of its own rather than to name a thing in the answer:
# a short line holding one of these is asking afresh ("what should i do", "how long?").
ASKING_FRESH = frozenset("""
what which how why when where who whose should would could can will shall do does did is are
was were need needs must if
""".split())

# An option offered with its own time ("tuna pasta in 15", "a frittata in 20"): two of them in
# one sentence make it a menu rather than an answer.
OPTION_TIMING = re.compile(r"\bin\s+\d+\b", re.I)

# A figure or a length of time in the line ("an hour", "2 days", "45 minutes").
DIGIT_OR_SPAN = re.compile(
    r"\d|\b(?:an?|one|two|three|four|five|six|seven|eight|nine|ten|twelve|fifteen|twenty|thirty|"
    r"forty|fifty|sixty|ninety|hundred)\s+(?:seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|"
    r"weeks?|months?|years?)\b", re.I)

# A sentence that opens by pointing back is a continuation of the sentence before it, not an
# answer on its own: "There is chilli as well.", "It keeps for three days.", "That is the one."
DEPENDENT_SENTENCE = re.compile(
    r"^\s*(?:there|it|this|that|these|those|also|and|so|then|plus|but)\b", re.I)

ABOUT_THE_ANSWER = frozenset("""
work works working help helps helped use using used try trying need needs needed
better best good good idea worth right wrong okay ok actually really still just also
instead thing things way ways method enough any more much option
""".split())


def _the_sentence_about(text, memory):
    """The sentence of the last answer that answers a yes/no about a thing it named, or None.

    "will salt work" after the red-wine carpet answer is answered by the sentence that names
    salt; the whole paragraph again is not, and a shrug is worse than both. The guards keep it
    to a follow-up: a short line, a yes/no shape, and every word of the line but the ones about
    the answer itself already in the answer, so a line naming a new thing ("will a dehumidifier
    help") is left for the entries.
    """
    earlier = _last_answer(memory)
    if not earlier:
        return None
    reply = earlier.get("reply") or ""
    if not reply.strip() or len(text.split()) > 7:
        return None
    # A line that names a figure or a span ("its been there an hour", "for 2 days?") asks about
    # that figure, not about a thing in the answer, however few words it has: the amount readers
    # in this module work the figure out from the answer's own rule.
    if DIGIT_OR_SPAN.search(text):
        return None
    # A yes/no ("will salt work") or the bare name of the thing ("salt?", "white wine?"): both
    # ask about the answer rather than bringing a question of their own. A short question that
    # asks for the doing or the figure ("what should i do", "how long?") is asking afresh, so it
    # is not read here however few words it has.
    said_so_far = words_of(text)
    # The ask words are read off the line as typed, not off its content words: "what should i
    # say" is one content word ("say") and would pass for the bare name of a thing, and the
    # thing it would name is the advice the answer already gave - said again word for word.
    asked_fresh = ASKING_FRESH.intersection(re.findall(r"[a-z']+", flat(text)))
    if not (YES_NO_ABOUT_A_THING.search(flat(text))
            or (len(said_so_far) <= 3 and not asked_fresh)):
        return None
    said = set(words_of(reply)) | set(earlier.get("keys") or ())
    named, other = [], False
    for word in words_of(text):
        if word in ABOUT_THE_ANSWER or len(word) < 3:
            continue
        if word in said:
            named.append(word)
        else:
            other = True
    if not named or other:
        return None
    sentences = same_again.quoted.sentences(reply, SENTENCE)
    holding = [one for one in sentences if all(word in set(words_of(one)) for word in named)]
    if len(holding) != 1 or len(sentences) < 2:
        return None
    part = holding[0]
    if flat(part) == flat(reply):
        return None
    # A sentence that offers the same dish in several times over ("tuna pasta in 15, macaroni
    # cheese in 25, or a sausage traybake in 45") is a menu of options, not the answer to a line
    # that picks one of them: the thing the line names is one of the choices, and handing the
    # menu back is repeating the answer the person just chose from.
    if len(OPTION_TIMING.findall(part)) >= 2:
        return None
    # A sentence that leans on the one before it is not a reply on its own: "there is chilli as
    # well" answers "chilli?" after a spaghetti bolognese answer with a clause about somebody
    # else's dinner, and a shrug reads better than a fragment.
    if DEPENDENT_SENTENCE.match(part) or len(part) < 40:
        return None
    return _part_not_repeated(part, reply, memory)


# A "who should I call" about the thing in hand is answered by whoever the answer on the screen
# already names: "...that is a Gas Safe engineer", "get a roofer out". The ask carries the words
# of the asking ("who", "call") and none of the answer's, so every sentence reader above passes
# the answer by and the person was sent to a search engine about their own broken boiler. The
# trades are the ones the knowledge base sends people to; a sentence that says who to get is
# preferred over one that merely mentions somebody, so a leak answer gives "get a roofer out"
# rather than the line about the landlord.
WHO_TO_CALL = re.compile(
    r"^\s*(?:(?:so|and|but|ok|okay|then|also|right|now|sorry|hmm)[\s,]+)*"
    r"(?:who|which)\b(?:(?!\?).){0,40}?"
    r"\b(?:call|ring|phone|contact|get\s+(?:in|out|somebody|someone|a\\s)|ask|speak\s+to|"
    r"talk\s+to|come\s+out|do\s+i\s+get)\b", re.I)
A_TRADE = frozenset("""
engineer plumber electrician roofer locksmith glazier builder surveyor landlord
landlady letting agent council insurer insurance vet doctor gp dentist nurse optician
pharmacist mechanic garage sweep decorator plasterer joiner drain drains
""".split())
# A sentence that opens on a condition is advice for whoever the condition fits ("If you rent,
# tell the landlord"), not the answer to "who should I call".
CONDITIONS_THE_LINE = re.compile(r"^\s*(?:if|when|unless|where|in\s+case)\b", re.I)
OPENING_CONNECTIVE = re.compile(r"^(?:then|and|so|but|now|next|first|also)[\s,]+", re.I)
SAYS_TO_GET_SOMEBODY = re.compile(
    r"^\s*(?:then|so|and|now|next|first)?[\s,]*"
    r"(?:get|call|ring|phone|contact|ask|book|hire|find|use|see|tell|speak\s+to|talk\s+to)\b",
    re.I)
SOMEONE_TO_GET = re.compile(
    r"\b(?:call|ring|phone|get|ask|tell|book|find|hire|contact|use)\b", re.I)
# A detail added to the answer ("its a worcester bosch") is met with the store saying it back
# ("Got it - it's a worcester bosch"), and that stock line then sits between the answer and the
# ask. Only a stock line is stepped over: a turn that answered a question of its own is the
# answer this ask belongs to, and reading an older one would answer the last question but one.
STOCK_ACKNOWLEDGEMENT = re.compile(
    r"^\s*(?:got\s+it|noted|right|ok|okay|thanks|thank\s+you|of\s+course|sure|understood|"
    r"no\s+problem|fair\s+enough)\b", re.I)
ACK_MODULES = frozenset({"greeting", "memory_store"})
MOST_ACKS = 2
MOST_WORDS_OF_AN_ACK = 24


def _a_stock_acknowledgement(turns, back):
    """Whether the turn `back` from the end only handed part of the chat back, and nothing more.

    Two shapes: the store saying the person's own detail back ("Got it - it's a worcester
    bosch"), and the bot repeating a sentence of the answer before it ("A whistling boiler is
    usually the same pump or a flow problem"). Neither is a new answer, so the ask behind it is
    still about the answer before them.
    """
    turn = turns[-1 - back]
    if not isinstance(turn, dict):
        return False
    reply = str(turn.get("bot") or "").strip()
    if not reply:
        return False
    if turn.get("module") in ACK_MODULES and len(reply.split()) <= MOST_WORDS_OF_AN_ACK:
        if STOCK_ACKNOWLEDGEMENT.match(reply):
            return True
    before = turns[-2 - back] if len(turns) > 1 + back else None
    if isinstance(before, dict):
        earlier = flat(str(before.get("bot") or ""))
        said = flat(reply)
        if earlier and said and len(said.split()) >= 4 and said in earlier:
            return True
    return False


def _the_person_to_call(text, memory):
    """The sentence of the last answer that says who to get, for a "who should I call", or None.

    Only a line that is the asking and nothing else: a word of its own ("who should i call about
    my car") names a thing the entries answer, and the sentence of an unrelated answer is a
    worse reply than leaving the turn alone.
    """
    if not WHO_TO_CALL.search(flat(text)):
        return None
    spare = [word for word in words_of(text) if word not in WHO_ASK_WORDS and len(word) > 2]
    if spare:
        return None
    # The answer on the screen is the turn before this one, read off the chat rather than off
    # `_last_answer`: that record ends with the topic, and the ask here is a new topic with none
    # of the answer's words in it, so it is exactly the case the record drops.
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return None
    last = turns[-1]
    if last.get("module") != "answers":
        skipped = 0
        while (skipped < MOST_ACKS and len(turns) - 1 - skipped >= 0
               and _a_stock_acknowledgement(turns, skipped)):
            skipped += 1
        if not skipped or len(turns) - 1 - skipped < 0:
            return None
        last = turns[-1 - skipped]
        if last.get("module") != "answers":
            return None
    reply = str(last.get("bot") or "").strip()
    if not reply:
        return None
    sentences = [one.strip() for one in SENTENCE.split(reply) if one.strip()]
    if len(sentences) < 2:
        return None
    holding = [one for one in sentences
               if A_TRADE.intersection(re.findall(r"[a-z']+", one.lower()))]
    if not holding:
        return None
    # The sentence that both names somebody and says to get them answers the ask; a sentence
    # that only mentions a trade ("gas work is theirs by law") is the answer to another question.
    # Of those, the one that says to get somebody first ("Then get a roofer out") beats one that
    # names a person inside a condition ("If you rent, tell the landlord"), which is advice for
    # a renter rather than the answer to the ask.
    getting = [one for one in holding if SOMEONE_TO_GET.search(one)]
    pool = getting or holding
    stating = [one for one in pool if not CONDITIONS_THE_LINE.match(one)]
    pool = stating or pool
    up_front = [one for one in pool if SAYS_TO_GET_SOMEBODY.match(one)]
    # The reply has to name who to get. A sentence that mentions a trade in passing ("a brush
    # strip on the door, a chimney balloon") is not the answer to the ask, and handing back the
    # condition half of a sentence ("If it has been more than six weeks ...") answers nothing at
    # all: the clause that says to see the GP is the one that was cut off in front of it.
    ordered = up_front + [one for one in pool if one not in up_front]
    named = [one for one in ordered
             if A_TRADE.intersection(re.findall(r"[a-z']+", one.lower()))]
    if not named:
        return None
    part = named[0]
    # A sentence of a paragraph leans on the one before it ("Then get a roofer out"): said on its
    # own, the connecting word goes with the sentence it connected to.
    stripped = OPENING_CONNECTIVE.sub("", part).strip()
    if stripped != part and stripped:
        part = stripped[:1].upper() + stripped[1:]
    if len(part) < 25 or not part[:1].isupper() or DEPENDENT_SENTENCE.match(part):
        return None
    part = _the_clause_that_says_who(part)
    return _part_not_repeated(part, reply, memory)


# A long sentence of an answer often does everything at once - the cause, the three jobs to do,
# and then who to get: "Banging or rumbling ... is usually air ...: bleed the radiators, check
# the pressure ..., and if it carries on get a heating engineer to look at the pump." Handing
# that whole sentence back is repeating the answer for an ask that only wants the last clause.
CLAUSE_BREAK = re.compile(r"\s*[,;:]\s*|\s+(?:and|but|then|so)\s+", re.I)
LONG_SENTENCE_WORDS = 24


def _the_clause_that_says_who(part):
    """The clause of a long sentence that names who to get, or the sentence as it stands.

    Only a clause that both names a trade and says to get them will do, and only when the
    sentence is long enough that handing it all back is repeating the answer. A short sentence
    is already the one thing the ask wants.
    """
    if len(part.split()) <= LONG_SENTENCE_WORDS:
        return part
    pieces = [one.strip() for one in CLAUSE_BREAK.split(part) if one.strip()]
    for piece in reversed(pieces):
        named = A_TRADE.intersection(re.findall(r"[a-z']+", piece.lower()))
        if named and SOMEONE_TO_GET.search(piece):
            piece = OPENING_CONNECTIVE.sub("", piece).strip() or piece
            return piece[:1].upper() + piece[1:]
    return part


# The words a "who should I call" is made of. A line with anything else in it names a thing of
# its own and is left to the entries.
WHO_ASK_WORDS = frozenset("""
who which what should shall do does can could would will might i we you they me my our
call ring phone contact get ask speak talk to about now then also just really
somebody someone anybody anyone person people trade tradesman professional expert
kind sort type best good right one out in come
""".split())

# A "which one" after a recommendation is the recommendation asked for again, and the answer
# is already in the reply the person has just read: "get 16GB of RAM and a 512GB SSD" is what
# decides it. Handing back the search shrug refuses a question the bot itself answered a
# moment ago, and handing the whole paragraph back is the machine thing STYLE names. Only a
# short line that names nothing of its own qualifies; a comparison ("which one is better, the
# iphone or the samsung") names the two things and has an answer of its own.
CHOICE_ASK = re.compile(
    r"^\s*(?:so |ok |okay |right |and |then )*(?:"
    r"which (?:one|ones|of those|of them|of these)"
    r"|which should i (?:get|buy|pick|choose|go for)"
    r"|which would you|which do you"
    r"|what (?:should|would) (?:i|you) (?:get|buy|pick|choose|go for)"
    r"|what do you recommend|what would you recommend"
    r"|any recommendations?|any suggestions?)\s*[?.!]*\s*$")
# ... and it is only about a choice when the answer it follows was about buying one. "which one"
# after a dripping tap, or after a list of dinners, is a line with nothing to pick from.
CHOICE_CONTEXT = re.compile(
    r"\b(?:buy|buying|bought|get|getting|purchase|recommend|recommendation|best|worth|"
    r"choose|choosing|pick|picking|upgrade|look for|looking for|which|new)\b")
# A word that is a size, a number or a spec: the sentence that decides between two things has
# one of these in it, and a sentence that only says why the thing is worth having does not.
A_SPEC = re.compile(
    r"\d|\b(?:gb|tb|mb|ghz|mah|kg|litres?|litre|ml|cm|mm|inch|inches|watt|watts|hours?|"
    r"minutes?|percent|pounds?|quid|years?|months?|weeks?|degrees?|spin|speed|drum|size|"
    r"tog|thread|bar|btu)\b")
# The sentence that decides is the answer, in the words the bot has already used, so all the
# reply adds is which part of the last answer this is. It goes after the sentence, not before:
# the answer comes first (STYLE), and a lead-in with a colon in it would be read as a list of
# options by the memory store.
CHOICE_TAIL = (
    "That is the bit that decides it.",
    "That is the one I would go for.",
    "That is what to go by.",
)


# A sentence that carries the spec is often a long one, with the rest of the answer after it:
# the pick is the clause that names the size, so a second clause is dropped when there is
# enough of the sentence left without it.
CHOICE_CUT = re.compile(r",?\s+(?:and |but |so |which |because )|;\s+")
CHOICE_SHORTEST = 60


def _the_clause_that_picks(sentence):
    """The first clause of a long sentence, when the rest of it is a second thought."""
    if len(sentence) <= 150:
        return sentence
    for found in CHOICE_CUT.finditer(sentence):
        start = found.start()
        if start >= CHOICE_SHORTEST:
            return sentence[:start].strip(" ,;")
    return sentence


# The thing to take is named inside the deciding sentence, not by it: the concrete one usually
# comes after the colon ("...: a 10 to 12 litre one"), and a list of things to choose between
# starts at its first item. Handing the whole sentence back is the last turn said again, which
# is the one thing a "which one?" reply must not be.
# A figure or a size in the thing itself is what a "which one?" is asking for: it is the part of
# the recommendation a person can act on, and an answer with none of it in it ("an air fryer is a
# small oven that blows hot air fast: chips, roast veg") has nothing to pick between.
CHOICE_FIGURE = re.compile(
    r"\d|\b(?:gb|tb|mb|ghz|mah|kg|litres?|ml|cm|mm|inch|inches|watt|watts|tog)\b", re.I)
CHOICE_LIST_HEAD = re.compile(r"\b(?:get|buy|make|go|choose|take|pick|spend|aim|look for|opt for)"
                              r"\b", re.I)
CHOICE_ITEM = re.compile(r",\s+")
CHOICE_LEAD_VERB = re.compile(r"^(?:get|buy|choose|take|go for|pick|look for|aim for|spend|opt for"
                              r"|go with)\s+", re.I)
CHOICE_CONDITION = re.compile(r"\s+(?:if|unless|when)\s+")
# A price is a figure too, and a sentence whose deciding figure is what a thing costs answers a
# "which one" with a number rather than a thing: "About 100 pounds is the usual gift" is not a
# choice to make, and neither is "a 10 to 12 litre one" once the figure has been cut off it.
CHOICE_COST = re.compile(r"[£$€]\s*\d[\d,.]*|\b\d[\d,.]*\s*(?:pounds?|quid|dollars?|euros?)\b", re.I)
# A price that opens a span and is then explained is a statement about money, not a thing.
CHOICE_PRICE_OPENS = re.compile(
    r"^(?:about|around|roughly|approx(?:imately)?|maybe|somewhere|up to|over|under)?\s*"
    r"(?:[£$€]\s*\d[\d,.]*|\d[\d,.]*\s*(?:pounds?|quid|dollars?|euros?))\b"
    r"(?=\s*(?:[a-z]+\s+){0,4}?(?:is|are|was|were)\b)", re.I)
# What is left of a price once it has been read as a price: the number, the currency and the
# words people put around a price ("about", "the usual", "going rate"). A span with nothing
# but those in it sized the thing without naming it.
CHOICE_PRICE_ONLY = re.compile(
    r"(?:about|around|roughly|approx(?:imately)?|maybe|somewhere|up to|over|under|less than|more"
    r" than|between)?\s*(?:[£$€]\s*\d[\d,.]*|\d[\d,.]*\s*(?:pounds?|quid|dollars?|euros?))"
    r"(?:\s*(?:to|-|and)\s*(?:[£$€]\s*)?\d[\d,.]*)?", re.I)


def _a_list_of_things(tail):
    """True when a clause lists three or more things, each a phrase of its own.

    A list of things to get is a run of short noun phrases ("a proper thermos, a voucher for the
    place she likes, a photo book of the family"). A sentence explaining why the advice is right
    splits on the same commas ("a 30 pound supermarket one sits too high off the neck, hurts your
    fingers and is why people stop after a fortnight") and every item in it is a whole clause, so
    an item longer than a phrase rules the list out.
    """
    items = [one.strip(" .!?") for one in re.split(r",\s*|\s+and\s+", tail)]
    items = [re.sub(r"^(?:or|and)\s+", "", one) for one in items if one]
    return (len(items) >= 3
            and all(2 <= len(one.split()) <= 11 for one in items))


def _the_thing_that_picks(sentence):
    """The shortest span of a deciding sentence that names the thing to take, or None.

    A recommendation has two halves when it has a colon at all: the things to get, and either the
    reason for them ("the running cost over ten years beats the purchase price difference") or
    the list itself ("a proper thermos, a voucher, a photo book"). Which half decides is read off
    the sentence: a list of things after an instruction is the list, otherwise the half with the
    figures in it wins. What comes back is one thing to take - never the whole sentence, because
    the whole sentence is the last turn said again - and None when the sentence names nothing a
    person could choose on.
    """
    span = sentence.strip()
    listed = sized = False
    if ": " in span:
        head, tail = span.split(": ", 1)
        head, tail = head.strip(), tail.strip()
        if len(tail.split()) >= 3:
            if (CHOICE_LIST_HEAD.search(head) and not CHOICE_FIGURE.search(head)
                    and _a_list_of_things(tail)):
                # "Make something she uses every week a bit nicer: a proper thermos, a voucher,
                # ..." - the instruction names no thing and says no figure, so the list is the
                # answer. When the head already sizes the thing ("Buy a used acoustic ..., 80 to
                # 150 pounds") the figures in it decide instead.
                span, listed = tail, True
            elif len(CHOICE_FIGURE.findall(head)) > len(CHOICE_FIGURE.findall(tail)):
                span, sized = head, True
            elif len(CHOICE_FIGURE.findall(tail)) > len(CHOICE_FIGURE.findall(head)):
                span, sized = tail, True
            else:
                span = head
    first = CHOICE_ITEM.split(span, 1)
    takes_the_figure = (len(first) == 2 and CHOICE_FIGURE.search(span)
                        and not CHOICE_FIGURE.search(first[0]))
    if len(first) == 2:
        if len(first[0].split()) < 2:
            return None  # "chips, roast veg and salmon" is a list of dishes, not of things to get
        if takes_the_figure:
            # The comma takes the only figure with it, and that figure is why this sentence decides
            # the choice: cut there and what is left is the why of the answer, not the thing the
            # why is about ("a proper pair makes a real difference to your knees"). The sentence
            # stays whole then, so the pick still carries what makes it a size to go by.
            pass
        else:
            span = first[0]
    span = CHOICE_LEAD_VERB.sub("", span)
    conditional = CHOICE_CONDITION.search(span)
    if conditional and conditional.start() >= 8:
        span = span[:conditional.start()]
    span = _the_clause_that_picks(span).strip(" ,;:.!?")
    if len(span.split()) < 2:
        return None  # one word is a noun to look up, not a thing to go and get
    if _a_price_and_nothing_else(span):
        return None  # a figure on its own answers "how much", not "which one"
    if listed:
        return span  # a list of things to get, and every item in it is a thing to get
    if sized or CHOICE_FIGURE.search(span):
        return span  # the part of the answer with the figure that decides
    return None


CHOICE_NOT_A_THING = frozenset("""
    about around roughly approx approximately maybe perhaps somewhere between up over under less
    more than to and or the a an it its that this these those is are was were be being been of
    for per at in on with without plus altogether total totals overall usually usual typical
    typically average norm normally going rate price prices cost costs cheap cheaper cheapest
    expensive budget spend spending paying pay paid altogether cheaper worth pounds quid dollars
    euros notes coins roughly
""".split())


def _a_price_and_nothing_else(span):
    """True when the span is a price rather than a thing, so it answers "how much", not "which".

    Three shapes of it: nothing but the figure and the words people put around a price ("About 100
    pounds", "90 to 130 pounds" - a figure beside a noun is a thing sized by that figure, so
    "16GB of RAM" passes); a price that opens the span and is then explained ("About 50 pounds is
    the usual gift"); and a price at the very end ("A good one is about 100 pounds"), where the
    span is only a way of getting to the number.
    """
    rest = CHOICE_PRICE_ONLY.sub(" ", span)
    if not any(word not in CHOICE_NOT_A_THING for word in re.findall(r"[a-z]{2,}", rest.lower())):
        return True
    bare = span.rstrip(" .!?")
    if CHOICE_PRICE_OPENS.match(bare):
        return True  # "About 50 pounds is the usual gift": the thing is the gift, not the figure
    ends = CHOICE_COST.search(bare)
    if ends and bare[ends.end():].strip(" .,!?"):
        ends = None
    return bool(ends)  # "... and fit you for 90 to 130 pounds": the span only leads to the number


def _the_composer_has_options(memory):
    """True when the bot's last answer offered named options the composer can pick between."""
    try:
        from ..compose import fallback as composer
        return bool(composer._offered(memory))
    except Exception:  # noqa: BLE001 - a composer that cannot be asked adds no reason to decline
        return False


# A question can put two things up without any word of buying in it: "should we go to spain or
# italy", "the train or the coach". `CHOICE_CONTEXT` reads the buying verbs, so a choice like
# that was invisible to the choice reader, and the answer was a shrug or a request that the
# person pick the thing the bot had already picked. The two things are the question's own words,
# and the answer's first word is one of them.
_AN_ALTERNATIVE = re.compile(r"\b(?:or|vs\.?)\b", re.I)
_NOT_AN_OPTION = frozenset("""a an the i we you it that this these those and but so if for to of
in on at by is are was were be been do does did would could should can will go get got one
both either neither""".split())


def _the_option_that_decides(said, reply):
    """The option of theirs the answer opened with, or '' when it opened with something else."""
    head = re.split(r"[.!?\u2014:;]", str(reply or "").strip(), 1)[0]
    in_the_question = set(re.findall(r"[a-z][a-z'\u2019-]*", said.lower()))
    for word in re.findall(r"[A-Za-z][A-Za-z'\u2019-]*", head)[:5]:
        low = word.lower()
        if low in in_the_question and low not in _NOT_AN_OPTION:
            return word
    return ""


def _the_answer_to_a_choice_behind(memory):
    """The answer that decided between two things the person put up, or None.

    A choice is not always asked again on the next turn. "should we go to spain or italy" is
    answered "Italy", then a detail about the kids, then "so which one" - and the answer on the
    screen is about the kids. Reading only that answer refused a choice the bot had already
    made. A line that offered two things is the one to read, and its answer's first word is the
    pick when it is one of those two.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for row in reversed(turns if isinstance(turns, list) else ()):
        if not isinstance(row, dict):
            continue
        said = " ".join(str(row.get("user") or "").lower().split())
        reply = str(row.get("bot") or "").strip()
        if not said or not reply or len(said.split()) > 16:
            continue
        if not _AN_ALTERNATIVE.search(said):
            continue
        option = _the_option_that_decides(said, reply)
        if not option:
            continue
        return f"{option[:1].upper()}{option[1:]}. That is the one I would go for."
    return None


def _the_one_to_pick(text, memory):
    """The sentence of the last answer that decides which one of the things to take."""
    clean = " ".join(str(text or "").lower().split())
    if not CHOICE_ASK.match(clean):
        return None
    if " or " in f" {clean} " or " vs " in f" {clean} " or "better" in clean:
        return None  # a comparison names the two things, and has an answer of its own
    earlier = _last_answer(memory)
    if not earlier:
        return _the_answer_to_a_choice_behind(memory)
    turns = memory.get("turns") or []
    turn = earlier.get("turn")
    before = ""
    if isinstance(turn, int) and 0 <= turn < len(turns) and isinstance(turns[turn], dict):
        before = str(turns[turn].get("user") or turns[turn].get("text") or "").lower()
    if not CHOICE_CONTEXT.search(before):
        return None  # nothing was being chosen before this line, so there is nothing to pick
    # The composer already picks out of a list it offered ("*Groundhog Day* for comedy,
    # *Knives Out* ..."), in the bot's own voice and with the note that goes with it. That pick
    # is better than handing a sentence of the last answer back, so this reader stands down.
    if _the_composer_has_options(memory):
        return None
    reply = str(earlier.get("reply") or "").strip()
    if not reply:
        return None
    sentences = [one.strip() for one in SENTENCE.split(reply) if one.strip()]
    if not sentences:
        return None
    choose_from = [one for one in sentences if not one.rstrip().endswith("?")]
    if not choose_from:
        return None
    # The answer's own first sentence is the recommendation (STYLE puts the answer there); a
    # later sentence only wins when the first one names no size, figure or spec at all and the
    # later one does, which is the answer that keeps its number in the second sentence.
    best = choose_from[0]
    if not A_SPEC.search(best):
        for sentence in choose_from[1:]:
            if A_SPEC.search(sentence):
                best = sentence
                break
    said = _flat(best)
    if not said or said == _flat(mem.last_bot(memory) or ""):
        return None
    pick = _the_thing_that_picks(best)
    if not pick or len(pick.split()) < 2 or _flat(pick) == _flat(mem.last_bot(memory) or ""):
        return None  # nothing shorter to say than the last answer: not a pick
    tail = CHOICE_TAIL[len(said) % len(CHOICE_TAIL)]
    pick = pick.rstrip('. ') or pick.rstrip()
    return f"{pick[:1].upper()}{pick[1:]}. {tail}"
# A meal idea states the whole dish's time in brackets ("I'd do dhal (30 minutes): ..."), and the
# step inside it keeps a count of its own ("simmer for 25 minutes"). "how long does that take"
# after that answer is asking about the answer we gave, so the bracket is the reply. Left to the
# part reader, the step's 25 minutes came back as the dhal's time when we had said 30, and on a
# diet answer whose closing sentence carries no number the line was not read at all: after "I'd
# do tomato pasta (20 minutes): ..." the bot asked "You haven't said - how long does that take?".
_DISH_TIME = re.compile(r"\(\s*(\d+)\s*(minutes?|mins?|hours?|hrs?)\s*\)")
# The same whole-dish time is written as a sentence of its own when the method comes first ("I'd
# do spaghetti bolognese: Brown the mince ... while the spaghetti cooks. 30 minutes, give or
# take."). A sentence that *starts* with the duration is the dish's; a sentence with the count
# inside it ("simmer it 20 minutes while the spaghetti cooks") is that step's.
_WORD_NUMBER = (r"\d+|an?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen"
                r"|twenty|thirty|forty|fifty|sixty|ninety|twenty[-\s]five|twenty[-\s]ten"
                r"|thirty[-\s]five|forty[-\s]five")
_A_WHOLE_TIME = re.compile(r"(__N__)(?:\s*(?:to|or|-|and a half)\s*(__N__))?\s*"
                           r"(minutes?|mins?|hours?|hrs?)\b".replace("__N__", _WORD_NUMBER), re.I)
_A_BARE_TIME = re.compile(r"^\s*(?:about\s+|roughly\s+|around\s+)?(?:%s)"
                          % _A_WHOLE_TIME.pattern, re.I)
# Only a line that asks the one thing points back at our answer. "how long should i rest it"
# after a meal has a verb of its own, and the dish's time is no answer to it.
# A dish named and then its time: "Curry: 35 to 45 minutes from scratch: 10 minutes of frying the
# onions ... then 25 to 30 minutes simmering." The whole time is the figure in front of the first
# colon, and the ones after it are the steps.
_A_LABELLED_TIME = re.compile(r"^\s*[A-Z][\w' -]{0,40}:\s*([^:.;\n]{0,90})")
# A figure is the dish's time only when it is the whole of what its sentence says: a rate ("20
# minutes per 500g plus 20 minutes at 190C, so a 2kg bird takes 1 hour 40") opens with a time and
# is not one, and a range written in two halves ("6 minutes for a soft egg, 10 for a hard one")
# opens with the lower end of a range that is the answer. What may follow the figure is only
# words that say the same time again another way.
_RATE = re.compile(r"\b(?:per|each)\b|\ba\s+\d+(?:\.\d+)?\s*(?:g|kg|lb|oz)\b", re.I)
# A sentence that states the time and nothing else may say it again in one of these ways and no
# other: "35 minutes, give or take", "Roughly 35 minutes in all", "Twenty minutes, no packet
# needed". A sentence that opens with a time and then explains something ("Two hours before
# departure is the safe rule") is not a sentence of its own about the time.
_TIME_TAIL = re.compile(r"^(?:give or take|in all|altogether|from scratch|start to finish|or so"
                        r"|no packet needed|flat|to make|total)?$", re.I)

_HOW_LONG_ONLY = frozenset((
    "how", "long", "many", "much", "does", "do", "did", "will", "would", "that", "it", "this",
    "them", "take", "takes", "then", "so", "roughly", "about", "and", "to", "cook", "make",
    "minute", "minutes", "mins", "hour", "hours", "time", "the", "a", "is", "are", "s", "for",
    "of", "altogether", "total", "start", "finish", "from", "scratch"))


def _one_total(rest, whole_sentence=False):
    """Whether what follows a figure in its sentence leaves that figure as the one total.

    Three ways the rest of a sentence takes the figure back: the time carries on with a number of
    its own ("1 hour 40"), a rate follows it ("per 500g", "for each kilo"), or the same clause
    gives another figure of its own ("6 minutes for a runny yolk, 7 for jammy, 9 to 10 for hard
    boiled" is a range written out, not one total). A second clause after a semicolon is a
    different way of doing the same dish and leaves the first figure where it is ("20 to 25
    minutes at 200C from frozen, turning once; an air fryer does them in 12 to 15"), and a
    temperature is not a time, so "25 minutes at 200C" is still 25 minutes.
    """
    rest = " ".join(str(rest or "").strip(" .,;:!?-").split())
    if rest[:1].isdigit() or _RATE.search(rest):
        return False
    # A number glued to a unit or a degree ("200C", "170C") is a heat, not another time.
    if re.search(r"\b\d+(?:\.\d+)?(?![\w\u00b0])", rest.split(";")[0]):
        return False
    if whole_sentence:
        # The sentence shape is the least certain of the three, so it asks the most: what follows
        # the figure has to be one of the ways of saying the same time again.
        return bool(_TIME_TAIL.match(rest))
    return True


def _the_dish_time(understood, memory):
    """The whole-dish time in the answer just given, when the line asks for it.

    A meal answer gives its total in one of three shapes, and each is read in turn because each
    is more certain than the next:

    * the bracket: "I'd do tuna pasta (15 minutes): stir a tin of tuna through hot pasta".
    * a sentence that states nothing but the time: "About 30 minutes.", "35 minutes, give or
      take.", "Twenty minutes, no packet needed."
    * a name and then the time in the very next words: "Curry: 35 to 45 minutes from scratch:
      10 minutes of frying the onions and spices, then 25 to 30 minutes simmering." A label in
      front of a list of three ("Quick: tuna pasta in 15, a frittata in 20, or ...") is not this
      one: the time has to be the first thing the label says.

    A count inside a step is a step, which is why the shapes are read in that order, and a figure
    only counts when the rest of its sentence leaves it as the one total: "About 20 minutes per
    500g plus 20 minutes at 190C, so a 2kg bird takes 1 hour 40" opens with a rate and "6 minutes
    for a runny yolk, 7 for jammy" opens with half of a range, so neither is a whole-dish time.
    Unless one of them names a single total, the answer does not give the dish's time and the
    turn is left to the reader it had.
    """
    text = str((understood or {}).get("clean") or "")
    if asked_kind(text) != "time":
        return None
    # The reading's words keep the pronouns `words_of` drops: a line with a verb or a food of its
    # own ("how long should i rest it", "how long do i boil an egg") names something else.
    words = [str(word).lower() for word in (understood or {}).get("words") or ()]
    if not words or [word for word in words if word not in _HOW_LONG_ONLY]:
        return None
    earlier = _last_answer(memory)
    if not earlier:
        return None
    reply = str(earlier.get("reply") or "")
    whole = None
    bracketed = {"%s %s" % (one.group(1), one.group(2).lower())
                 for one in _DISH_TIME.finditer(reply)}
    if len(bracketed) == 1:
        whole = bracketed.pop()
    if whole is None:
        sentences = set()
        for part in re.split(r"(?<=[.!?])\s+", reply.strip()):
            bare = _A_BARE_TIME.match(part)
            if bare and _one_total(part[bare.end():], whole_sentence=True):
                sentences.add(" ".join(bare.group(0).lower().split())
                              .replace("about ", "").replace("roughly ", "").replace("around ", ""))
        if len(sentences) == 1:
            whole = sentences.pop()
    if whole is None:
        labelled = _A_LABELLED_TIME.match(reply.strip())
        if labelled:
            # The time has to be the first thing the label says: "Curry: 35 to 45 minutes from
            # scratch: ..." is the dish, and "Quick: tuna pasta in 15, a frittata in 20" is a
            # list of three dishes that happens to open with a label.
            first = _A_BARE_TIME.match(labelled.group(1))
            if first and _one_total(labelled.group(1)[first.end():]):
                whole = (" ".join(first.group(0).lower().split())
                         .replace("about ", "").replace("roughly ", "").replace("around ", ""))
    if whole is None:
        return None
    # A food of its own that our answer never mentioned is a new question, not this one.
    for food in cooking.ingredients(understood):
        if str(food).lower() not in reply.lower():
            return None
    return "About %s for that one, start to finish." % whole


# A correction of a figure: "sorry i meant 1.5", "no, 1.5", "make that 4". What follows the
# frame is the figure itself, and a figure with no unit names no amount on its own.
CORRECTION_FRAME = re.compile(
    r"^\s*(?:(?:no|nope|sorry|actually|wait|hold\s+on|oops|oh|and|so|right|ok|okay)\b[\s,]*)*"
    r"(?:i\s+(?:mean|meant)(?:\s+to\s+say)?|make\s+that|sorry|no|nope|actually|wait)\b[\s,]*",
    re.I)
A_BARE_FIGURE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([a-z]{0,6})?\s*[.!]?\s*$", re.I)
# The unit a bare figure is missing, as the amount was last said: "2 kilos" makes "1.5" a weight.
A_UNIT = re.compile(
    r"\b\d+(?:\.\d+)?\s*(kg|kgs|kilos?|kilograms?|g|grams?|lb|lbs|pounds?|litres?|liters?"
    r"|l|ml|pints?)\b", re.I)
UNIT_WORDS = {"kilo": "kg", "kilos": "kg", "kilogram": "kg", "kilograms": "kg",
              "kgs": "kg", "gram": "g", "grams": "g", "pound": "lb", "pounds": "lb", "lbs": "lb",
              "litre": "litres", "liter": "litres", "liters": "litres", "pint": "pints"}


def _the_unit_last_said(memory, reply):
    """The unit of the last amount the conversation said, or None.

    The person's own "its 2 kilos" is the amount a "sorry i meant 1.5" corrects, so their words
    decide what the figure measures. A rate is not an amount to copy: the first figure in the
    chicken answer is the "500g" of "20 minutes per 500g".
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for said_turn in reversed(turns or []):
        said = A_UNIT.search(str(said_turn.get("user") or ""))
        if said:
            return said.group(1).lower()
    for said in A_UNIT.finditer(reply or ""):
        before = (reply or "")[:said.start()].rstrip().lower()
        if before.endswith("per"):
            continue  # the rate, not the size this answer was written for
        return said.group(1).lower()
    return None


def _the_figure_they_meant(text, memory, reply):
    """The correction as the amount it corrects to ("and for 1.5 kilos"), or None.

    Only a line that is a correction frame and then a figure, so "sorry i meant the other one"
    is untouched, and only when the figure comes without a unit of its own and the conversation
    has one to give it.
    """
    said_line = str(text or "")
    body = CORRECTION_FRAME.sub("", said_line)
    if body.strip() == said_line.strip():
        return None  # no correction frame in the line
    found = A_BARE_FIGURE.match(body)
    if not found:
        return None
    figure, unit = found.group(1), (found.group(2) or "").lower()
    if unit not in ("kg", "g", "lb", "l", "ml", "cm", "mm"):
        unit = _the_unit_last_said(memory, reply)
        if not unit:
            return None
    # The amount reader knows a short list of units: "1.5 kilos" is the same amount as "1.5kg",
    # and the long word is how people say it.
    return "and for {} {}".format(figure, UNIT_WORDS.get(unit, unit))


def _amount_asked(text, memory):
    """The figure for a new amount the line names, or None.

    "how long for a 1.5kg one" after the 2kg bird names an amount the last answer does not
    state: the sentence that carries the 2kg time is the wrong figure, and the rate in it ("20
    minutes per 500g plus 20") is only useful worked out. Put the subject back in and let the
    entry answer the new amount, then keep the part that answers this line ("1 hour 20"), never
    the whole paragraph again.
    """
    earlier = _last_answer(memory)
    if not earlier:
        return None
    reply = earlier.get("reply") or ""
    # A correction says the figure again and nothing else, so it names no unit: "sorry i meant
    # 1.5" after the 2kg bird, "no 1.5" after "for six". Nothing read those lines - the amount
    # reader wants a unit, and the store can only say "Thanks for telling me". The unit is the one
    # the conversation last said, so the correction becomes the same "and for <amount>" this
    # function already works out.
    corrected = _the_figure_they_meant(text, memory, reply)
    if corrected:
        # A correction is an ask in its own right: "and for 3 kilos" is a question the entry can
        # answer whether or not the last reply gave a rate to work it out from.
        text = corrected
    elif asked_kind(text) != "time" and not RATE.search(reply):
        return None  # an amount is owed a new figure only when the last answer gave a rate
    clean = lambda found: {re.sub(r"\s+", "", one.group(0).lower()) for one in found}
    amounts = [one.group(0) for one in AMOUNT.finditer(text)]
    wanted = clean(AMOUNT.finditer(text))
    if not wanted or wanted <= clean(AMOUNT.finditer(reply)):
        return None
    subject = mem.subject(memory)
    if not subject:
        return None
    # A line that replaces the size the last answer worked from ("make it 3kg instead", "do it at
    # 2kg this time") is the same ask made at a new size: the words of the replacement are a frame
    # and not a subject. Read as a subject they reach the table's stand-in row ("instead" -> the
    # mince swap) and come back with the rate it happens to carry - "make it 3kg instead" after a
    # roast chicken time was answered "20 minutes", the per-500g figure, when the total for the
    # bird is what was asked. So the ask is put back as the question, with the new size on it.
    replaced = bool(SIZE_REPLACED.search(text)) and asked_kind(text) != "time" and RATE.search(reply)
    if replaced:
        fuller = "how long for {} {}?".format(amounts[0], subject)
    else:
        fuller = _with_subject(text, memory)
        if fuller.strip() == str(text).strip():
            fuller = _about_subject(text, memory)
        if fuller.strip() == str(text).strip():
            # "and for 3kg" points back with no word of its own, so the subject is put on the end.
            fuller = str(text).rstrip("?.! ") + " for the " + subject + "?"
    reading = understand(fuller, memory)
    item = find(reading)
    if item is None or not _is_about(item, subject):
        return None
    # The subject put back can turn the line into a question about something else: after "how do
    # i keep chicken breast moist" the subject is "moist chicken breast", and a whole-bird line
    # then reads as a breast line, so "how long does a 2kg chicken take to roast" was answered
    # with the breast's 18 to 20 minutes. If the line names its own subject and that subject has
    # its own answer, this is not a follow-up about the amount at all: let the entry answer it.
    own = None if replaced else find(understand(text, memory))
    if own is not None and own is not item:
        return None
    fresh = _payload(item, memory, reading)
    # The entry answers the new amount with the rate worked out for the size it was written
    # about ("so a 2kg bird takes roughly 1 hour 40"), and narrowing picks that figure out
    # because it is the only time in the answer: "how long for 250g chicken" was answered with
    # the 2kg figure. Work the entry's own rate out for the amount they named instead.
    sized = mem.sized_reply(fresh, text, memory, _key_words(item))
    if sized:
        return sized
    part = narrow(fresh, fuller) or narrow(fresh, "how long for " + amounts[0])
    if isinstance(part, str) and part.strip() and flat(part) != flat(fresh):
        # The same size asked again gets the same figure, word for word, from a narrowed answer
        # that is one short sentence: say the sentence it was cut from instead, which carries the
        # size and the rate, and the whole answer after that.
        return _part_not_repeated(part, fresh, memory)
    return None


# A line that replaces the size the answer worked from with one of its own: "make it 2kg instead",
# "do it now instead" - the ask is made again at a new size, and no thing is being substituted.
SIZE_REPLACED = re.compile(r"\b(?:instead|now|this\s+time)\b", re.I)


def _the_amount_they_named_again(text, memory):
    """The sentence of the last answer that gives the amount this line names, or None.

    "make it 2kg instead" after the timing for a 2kg bird names the size the answer has already
    worked out: there is no new figure to work out, and it is not a substitution - "instead" here
    means "instead of the size you assumed". Nothing read it that way. The size was the only
    content word left, so `_amount_asked` declined it (the answer already states 2kg) and the turn
    fell through to the context reader, which writes the line out with the last subject on it
    ("make the chicken oven 2kg instead"). The table's stand-in row is keyed on the word
    "instead", so that reading answered "Swap in pulses: red lentils for mince". The figure the
    person asked for is on the screen, so say the sentence of the answer that carries it.
    """
    earlier = _last_answer(memory)
    reply = str((earlier or {}).get("reply") or "").strip()
    if not reply:
        return None
    amounts = [one.group(0) for one in AMOUNT.finditer(text)]
    if len(amounts) != 1:
        return None  # one size or none: two is a comparison, and no size is not this line
    if not SIZE_REPLACED.search(text):
        return None  # nothing says a size is being replaced
    if not re.search(r"(?:^|[^\w])" + re.escape(amounts[0]) + r"(?:[^\w]|$)", reply, re.I):
        return None  # the answer gives another size, so the figure has to be worked out
    if swap.thing(text):
        return None  # the line names the thing to stand in for: that is a substitution
    if _own_thing(understand(text, memory)):
        return None  # the line names a thing of its own, so it is not a follow-up about a size
    sentences = [one for one in SENTENCE.split(reply) if one.strip()]
    carrying = [one for one in sentences if re.search(re.escape(amounts[0]), one, re.I)]
    if not carrying:
        return None
    # The shortest sentence that carries the size is the one written for it: the rate sentence
    # ("20 minutes per 500g plus 20") says nothing about the size asked.
    best = min(carrying, key=lambda one: len(one)).strip()
    # The size usually sits in the second half of a rate sentence - "20 minutes per 500g plus 20,
    # so a 2kg bird takes 1 hour 40" - and the opening half is the rate the person has just read.
    # A sentence said back from the front of the answer is the paragraph on the screen again as
    # far as the turn is concerned (`_short_form_of_the_last`), so the size's own clause is what
    # is said, and only when it carries the amount by itself.
    # The size is often the second half of a sentence whose first half is the rate the person has
    # just read ("a leg of lamb is 25 minutes per 500g ..., then 15 minutes resting: about 1 hour
    # 5 in total for a 2kg leg"), so the half after the last break that still carries the size is
    # what is said. A sentence said back from its own front is the paragraph on the screen again
    # as far as the turn is concerned (`_short_form_of_the_last`).
    for lead in (": ", ", so ", " so ", ", which means ", " \u2014 ", ", then ", "; "):
        cut = best.rfind(lead)
        if cut < 0:
            continue
        tail = best[cut + len(lead):].strip()
        if re.search(re.escape(amounts[0]), tail, re.I):
            best = tail
            break
    return best[:1].upper() + best[1:] if best else None

# The shapes a question about the machine takes: worth it, repair or replace, who to ring, and a
# plain yes/no ("should i get someone in"). Without one of these the line is not asking about the
# machine at all, whatever trigger words it happens to carry.
MACHINE_ASKING = re.compile(
    r"\b(?:worth|should|shall|is it|is that|would|could|can i|do i|who|whom|what|how|where|when|"
    r"why|or new|or replace|fix|fixing|repair|repairing|replace|replacing|salvage|scrap)\b")


def _the_machine_follow_up(text, reading, memory):
    """The decision about the machine the last line named, when this line names none of its own.

    "the washing machine smells of damp" then "is it worth getting someone in" is a money question
    about that washing machine, and the second line has neither the machine nor the fault in it,
    so nothing in the knowledge base could reach the repair rule and the person got "not mine to
    decide" straight after a good answer (sky-tuna, #answers). The machine and the fault are in
    the line before, so the rule reads both lines. The same goes for "is it worth fixing" and
    "shall i just replace it", which point back with a pronoun. A line that names a machine of its
    own is left alone: that is its own entry's question.
    """
    line = _flat(text)
    if home.machine_named(line):
        return None  # its own machine, so its own entry's question
    # It has to be a question. The trigger words are ordinary words, so a statement about the
    # person carrying them was read as a question about the machine: "the boiler is broken" then
    # "i work as an engineer" got the Gas Safe rule off the bare word "engineer", "the washing
    # machine is broken" then "i got a quote for a new kitchen" got the repair rule off "quote",
    # and "... then my dad looked at it and gave up" got it off "looked at" and "it" (friendly-
    # cobra, #1933). A confident answer to a question nobody asked is worse than a weak one.
    if not MACHINE_ASKING.search(line):
        return None
    asks = home.CALLING_SOMEONE.search(line) or (
        home.FOLLOWING_IT.search(line) and home.DECIDING_NOW.search(line))
    if not asks:
        return None
    earlier = home.machine_before(memory)
    if not earlier:
        return None
    # The decision is about the machine, so it is the answer to a question about the machine. A
    # line that names a part of it ("is it worth cleaning the filter") is a question about the
    # answer just given, and the sentence of that answer which speaks of the part is the answer:
    # the repair rule, which talks of quotes and new machines, says nothing about the filter.
    part = narrow(mem.last_bot(memory) or "", text)
    if part:
        return part
    reply = home.the_machine_decision(memory, earlier, line)
    return reply if isinstance(reply, str) and reply.strip() else None


# "when do i take it" after a tablet's card asks what time of day, and understanding reads the
# bare "when" as asking for a date. The date reader then cut the one date out of the card that
# answered before - "Three months.", the interval to the blood test - where the timing question
# wants the entry's own answer ("same time each day, and for most statins that is the evening").
# "What time of day should i take them" is read as `clock` already and answered by the entry, so
# this only catches the ones the reading misses: a "when"/"what time" and then a routine verb with
# the thing it is done to.
WHEN_OF_THE_DAY = re.compile(
    r"\b(?:when|what\s+time)\b[^.?!]*\b(?:take|taking|use|using|eat|eating|have|having|do|doing|"
    r"put|apply|give)\s+(?:it|them|this|these|those|one|mine|the\s+\w+)\b", re.I)


def _part_asked(text, memory):
    """The part of the last answer the line asks for, or None when it asks about something else."""
    if _a_property_word_names_a_thing(text):
        # "how long does the cold last" names the cold, so it is not a part of the answer on the
        # screen even though every word in it is a property word. The entry for the cold answers
        # it; narrowing the last answer gave "Rest, fluids... I can't say how long it will take".
        return None
    if WHEN_OF_THE_DAY.search(str(text or "")) and asked_kind(text) == "date":
        return None
    earlier = _last_answer(memory)
    if not _asks_part(text):
        # "how long should the opening be?" names a part of the answer, not a property on its
        # own. It is still about the last answer when the word it names is in that answer (or
        # in what the entry is about); a new thing ("how long does a chicken take?") is not.
        if earlier is None or asked_kind(text) is None:
            return None
        said = set(words_of(earlier.get("reply") or "")) | set(earlier.get("keys") or ())
        named = set(words_of(text)) - PROPERTY_WORDS - NOT_NEW
        if named and not named & said:
            return None
    if mem.left_for_a_blank(memory, text):
        # A turn in between named a thing of its own and got no answer ("what about a leg of
        # lamb?" after the roast chicken): this line is a question about that thing, so a part of
        # the older answer (the chicken times) is a wrong answer rather than a helpful one.
        return None
    if RATE.search(text):
        # A rate ("per kilo") is better answered by the entry that states it with its
        # qualifier than read out of a neighbouring sentence; let the lookup try.
        return None
    if not earlier:
        return None
    reply = earlier.get("reply") or ""
    if (COOK_VERB.search(text) and not KEEPS_ASK.search(text)
            and KEEPS_ANSWER.search(reply) and not COOK_VERB.search(reply)):
        # "how long do i cook it for" after "how long does cooked chicken last": the keeping
        # answer holds no cooking time, so there is no part of it to hand back, and trimming it
        # gave "3 days" as if that were how long the pan takes. The method entry for the same
        # food answers the line instead.
        return None
    if len(SUM_TABLE.findall(reply)) > 1 and asked_kind(text) == "time":
        # A table of sums ("£100 a month is 50 months, £250 a month is 20 months") is one answer:
        # trimmed to its last figure it reads "10 months" with nothing saying what for. The entry
        # that wrote the table answers the follow-up itself, with the next sums up.
        return None
    # One entry can hold a whole table of the things it answers one at a time, and then its key
    # words say nothing about which row was given: `appliance-life` keys on every appliance name,
    # so "how long does a toaster last" straight after "how long should white goods last" was read
    # as a part of that answer and cut to the sentence the table gave. When the line reaches the
    # same entry that answered, names a row of it, and that row would answer in its own words, the
    # line is a question of its own. A follow-up that names a thing of its own (`and how much
    # flour` after "2 eggs") reaches a different entry, so it is still the answer's detail.
    own_named = set(words_of(text)) - PROPERTY_WORDS - NOT_NEW
    earlier_keys = set(earlier.get("keys") or ())
    if own_named and earlier_keys:
        reading = understand(text, memory)
        same_item = [one for one in all_entries() if _key_words(one) == earlier_keys]
        if same_item and own_named & _key_words(same_item[0]):
            fresh = _payload(same_item[0], memory, reading)
            # The whole of what the entry says, not only its opening sentence: the thing the line
            # names can be in its second sentence ("and how long in the oven" after the frosting
            # answer reaches the cake's plan, whose oven time is not the sentence the follow-up
            # entry opens with). An entry that has something to say about the word the line names
            # is answering this line, and reading the last answer's part instead gives a sentence
            # about the other thing.
            if not (fresh or "").strip() or (
                    flat(fresh) != flat(reply) and own_named & set(words_of(fresh))):
                return None

    # A follow-up can name a different thing than the answer just given: "how long to bake a
    # sweet potato" after a plain one, or "how long to roast a chicken breast" after a whole
    # bird. Narrowing the last answer to its figure then gives "An hour." and "1 hour 40." for
    # a thing that takes neither, which is worse than no answer at all. When the line names a
    # thing the last answer never mentioned and reaches an entry of its own, that entry speaks.
    # Only a different *thing* counts: "in the fridge", "in the oven" and "on the hob" are where it
    # happens, not what is being cooked, and narrowing still answers those.
    named = (set(words_of(text)) - PROPERTY_WORDS - PLACE_WORDS - set(words_of(reply))
             - set(earlier.get("keys") or ()))
    reading = understand(text, memory)
    own = find(reading)
    # The line can also name what it is about in a word the last answer happened to say, and then
    # `named` is empty and nothing below looks new: "my cake cracked on top" then "why did my cake
    # sink in the middle" shares "cake" and "middle" with the crack answer and with the entry that
    # gave it, so the crack sentence was read out again for a cake that sank. What counts is not a
    # word the answer said but a word of the entry this line reaches that the earlier entry knows
    # nothing about: `cake-sink` keys on "sink" and `cake-fault` does not, so the sinking speaks.
    if own is not None and getattr(own, "id", None) != earlier.get("id"):
        theirs = _key_words(own) - set(earlier.get("keys") or ())
        hit = (set(words_of(text)) - PROPERTY_WORDS) & theirs
        # A place word is a place here too ("in the fridge", "in the oven"), so it is not a thing
        # of its own - but "sink" is a place word and a verb, and a sinking cake is the cake's.
        # The fresh entry has to be about the word and the last answer not to be: `cake-sink`
        # answers "a cake sinks when...", and no sentence of the crack answer says sink.
        if hit and not (hit & set(words_of(reply))):
            fresh = _payload(own, memory, reading)
            if (isinstance(fresh, str) and fresh.strip()
                    and hit & set(words_of(fresh))):
                return None  # the entry for what this line names answers it, not the last answer
        # The last answer can mention a thing in passing and still not be about it, and then the
        # line naming that thing is the other question: "is a cat ok with a baby" then "what
        # about the pram" was narrowed to the one sentence of the house-rules answer that says
        # pram, when the pram has an entry of its own in another part of the knowledge base
        # (plans.baby-gear). A line that asks nothing by name of a property, about a thing the
        # last answer's entry knows nothing about, and picked up by an entry from another part of
        # the knowledge base, is a change of subject rather than a part of that answer.
        if (hit and asked_kind(text) is None
                and getattr(own, "domain", "") != str(earlier.get("domain") or "")):
            fresh = _payload(own, memory, reading)
            if (isinstance(fresh, str) and fresh.strip() and flat(fresh) != flat(reply)
                    and hit & set(words_of(fresh))):
                return None
    if named:
        if own is not None and named & _key_words(own):
            if getattr(own, "id", None) != earlier.get("id"):
                return None  # a thing of its own, and the entry that answers it is about that thing
            # One entry can answer many things: a table with a row per food answers every food
            # from the same id, so "how much protein in greek yoghurt" after an egg is the same
            # entry and a different thing. When that entry has something to say about this line
            # that is not the answer on the table, the line is about its own thing: the egg's 6g
            # is a wrong fact about yoghurt. An entry with the same answer as before leaves the
            # narrowing alone, because then it really is the same subject.
            fresh = _payload(own, memory, reading)
            if isinstance(fresh, str) and fresh.strip() and flat(fresh) != flat(reply):
                return None
        elif (own is not None and getattr(own, "id", None) != earlier.get("id")
                and _keyed_on_the_line(own, text)):
            # The line reaches an entry of its own, and it is not the entry the last answer came
            # from: "how long does chicken keep in the fridge" then "how long do roast potatoes
            # keep in the fridge" narrowed the chicken answer to its opening sentence, which is a
            # confident wrong keep-time for potatoes. What the line names is not in the last
            # answer, and an entry answers the line itself, so that entry speaks. Only when it
            # has something to say that is not the answer already on the screen.
            fresh = _payload(own, memory, reading)
            if isinstance(fresh, str) and fresh.strip() and flat(fresh) != flat(reply):
                return None
        if (own is not None and getattr(own, "id", None) != earlier.get("id")
                and AMOUNT.search(text) and not AMOUNT.search(reply)
                and _keyed_on_the_line(own, text)):
            # "how long does a 2kg chicken take to roast" after an answer about breasts: the only
            # word the last answer never said is the size, and a size the answer does not state
            # is a question of its own, not a part of that answer. The entry that answers it
            # says one hour forty for a whole bird.
            return None

        # ...and the same when the line reaches an entry of its own from another part of the
        # knowledge base: "how much salt do i put in bread dough" then "how much salt should i
        # eat a day" is a person's daily limit, not the loaf's 10g, and the two questions sharing
        # the word "salt" is what used to hand back the loaf's figure. A part of an answer is
        # asked in the same subject the answer was about (a recipe's flour, a cake's temperature),
        # so a neighbour from another subject with a word of its own in the line answers instead.
        if own is not None and _keyed_on_the_line(own, text):
            mine = getattr(own, "domain", "") or ""
            theirs = str(earlier.get("domain") or "")
            if mine and theirs and mine != theirs:
                return None

    # ...and the same hand-off when the line names nothing new at all. A part is a part of the
    # answer only when it is asked in the same subject: "how do i descale my kettle" then "how
    # long does a kettle take to boil" names only the kettle, which the answer said, and "boil",
    # which is a property word, so nothing looked new and the half-hour soak time was read out
    # as the time to boil. The line reaches the kettle's boiling-time entry, and that entry is
    # about what the line says, so it answers.
    shared = (_key_words(own) & set(earlier.get("keys") or ()) & set(words_of(text))
              if own is not None else set())
    if (shared and getattr(own, "id", None) != earlier.get("id")
            and _keyed_on_the_line(own, text)):
        mine = getattr(own, "domain", "") or ""
        theirs = str(earlier.get("domain") or "")
        if mine and theirs and mine != theirs:
            fresh = _payload(own, memory, reading)
            if (isinstance(fresh, str) and fresh.strip()
                    and flat(fresh) != flat(reply)):
                return None

    # The same table entry also has to be spotted when the earlier answer's *keys* are the whole
    # table: `nutrients-in-food` keeps every food name as a key word, so "greek yoghurt" was
    # treated as a word of the last answer and the egg's figure was narrowed out of it. Only the
    # answer's own words can say whether this line names something new.
    same = own if own is not None else find(reading)
    if same is not None and getattr(same, "id", None) == earlier.get("id"):
        named = set(words_of(text)) - PROPERTY_WORDS - PLACE_WORDS - set(words_of(reply))
        # A figure the last answer never stated is the same entry asked a different question,
        # not a part of the answer: "how much lbtt on a 400000 first home" after the 200000 one
        # was answered by narrowing, which read the old price out of the old answer. An entry
        # that works a figure out from the line (a tax bill, a deposit, a rate for a size) has
        # the new figure; one that replies the same thing again leaves the narrowing alone.
        if named & _key_words(same) or _figures(text) - _figures(reply):
            fresh = _payload(same, memory, reading)
            if isinstance(fresh, str) and fresh.strip() and flat(fresh) != flat(reply):
                return None
    # The same is true of a *different* entry when the last answer's keys are a whole table:
    # `nutrients-in-food` keeps every food it can measure as a key word, so "how much protein in
    # milk" after the yoghurt figure was read as asking about yoghurt and the yoghurt sentence
    # came back instead of the milk one. The words the last answer never said are what decide
    # it: when an entry of its own has something to say about them that is not the answer on the
    # table, that entry speaks.
    other = find(understand(text, memory))
    if other is not None and getattr(other, "id", None) != earlier.get("id"):
        newly = set(words_of(text)) - PROPERTY_WORDS - PLACE_WORDS - set(words_of(reply))
        if newly & _key_words(other):
            fresh = _payload(other, memory, understand(text, memory))
            if isinstance(fresh, str) and fresh.strip() and flat(fresh) != flat(reply):
                return None
    # A conditional answer ("If nothing happens at all, try a different charger and leave it an
    # hour") is all one piece of advice: trimming it to "An hour." drops what to do first.
    if asked_kind(text) == "time" and re.search(r"\bleav(?:e|ing)\b", text):
        for sentence in re.split(r"(?<=[.!?])\s+", reply.strip()):
            if re.match(r"\s*(?:if|unless)\b", sentence, re.I) and re.search(r"\d|\ban?\b", sentence):
                return sentence.strip()
    # A line that names an amount and an answer that states a rate: the rate worked out for
    # their amount is the answer. Narrowing would hand back the figure the answer happens to
    # carry, which is for the size it was written about ("how long for a 1.5kg one" after "20
    # minutes per 500g plus 20 minutes, so a 2kg bird takes about 1 hour 40").
    sized = mem.sized_reply(reply, text, memory, set(earlier.get("keys") or ()))
    if sized:
        return sized
    # A bare figure is the whole of what narrowing can cut when the last answer stated a price:
    # "how much does it cost to charge an electric car" after the cost of a home charger came
    # back as "£800 to £1,200", which is the price of the wrong thing. If the line has an entry
    # of its own, that entry is asking about something the last answer did not price, so it
    # speaks and the figure is left alone.
    own_price = find(understand(text, memory))
    if (own_price is not None and getattr(own_price, "id", None) != earlier.get("id")
            and _only_a_figure(narrow(reply, text))):
        return None
    # A length of time is the same fault as a price, and a worse one on food. "and my oven only
    # fits one tray" answers with a traybake at 200C for 40 minutes; the next line, "how long do
    # i roast a whole chicken", was answered "40 minutes." - a raw bird, where the entry for the
    # bird states one hour forty. The sentence before only gives its figure for the thing it was
    # about, so when the entry this line reaches of its own states a different length of time,
    # that entry answers instead.
    if own_price is not None and getattr(own_price, "id", None) != earlier.get("id"):
        theirs = _key_words(own_price) - set(earlier.get("keys") or ())
        hit = set(words_of(text)) & theirs
        fresh = _payload(own_price, memory, understand(text, memory))
        if (hit and isinstance(fresh, str)
                and _a_figure_apart(narrow(reply, text), fresh)):
            return None
    # "when does it expire" after a keep answer is the same question as "how long does it keep",
    # and the subject is in the earlier answer rather than in the line: `narrow` is told what
    # that answer was about, so it looks for a document there and not in the five words of the
    # line.
    about = " ".join(str(key) for key in (earlier.get("keys") or ()))
    # A follow-up that names its unit ("how many weeks") is answered by the figure written in
    # that unit: the plain narrowing hands back the first length in the answer, and a plan names
    # several, so "how many weeks" after a training plan was answered "20 minutes." - the length
    # of the first session (see narrow.the_part_asked).
    part = the_part_asked(reply, text, about)
    if not (isinstance(part, str) and part.strip()):
        part = _sentence_naming_the_part(reply, text)
    if isinstance(part, str) and part.strip():
        # The part handed back is the whole answer to this line, so it has to state the kind of
        # quantity the line asked for. "and how long before i can play a song" after the guitar
        # cost answer was answered with "Which is most of the songs you already like." - a
        # proportion cut out of that answer for a line that asked how long, and the answer on
        # screen says no length of time about playing a song, so another turn is owed the entry.
        said = KIND_SAID.get(asked_kind(text))
        if said is not None and not said.search(part):
            part = None
        elif (asked_kind(text) == "time" and not re.search(r"\bbefore\b", text, re.I)
              and A_LEAD_TIME.search(_sentence_with(reply, part) or "")):
            # A lead time is not the length of the thing they asked about. `narrow` cuts the
            # figure out and with it the "before the flight" clause it sits in, so the sentence
            # the part came from is what says whether it is a lead time.
            part = None
    if asked_kind(text) == "cause" and isinstance(part, str) and part.strip():
        # The reason was just given: answer with the reason on its own, not the whole answer
        # again. A cause sentence can put the reason first ("A sore knee is usually...: ease
        # off") or after the step it explains ("Restart it: a full phone slows down, so...").
        return _reason_again(_cause_part(part), mem.last_bot(memory) or "")
    return _part_not_repeated(part, mem.entry_answer(memory, text) or reply, memory)


# An answer that gives a quantity by proportion rather than in figures: "use the same weight of
# butter", "half as much sugar", "twice the rice to the water".
PROPORTION = re.compile(r"\b(?:same weight|same amount|equal|half as much|twice|double\b|"
                        r"three times|two parts|one part)\b|\d", re.I)
# A clause that gives a quantity in units ("one mug of rice to one and a half mugs of water"),
# whether the number is written as a digit or as a word.
MEASURE = re.compile(r"\d|\b(?:mug|mugs|cup|cups|spoon|spoons|teaspoons?|tablespoons?"
                     r"|grams?|kilograms?|kilos?|ml|litres?|liters?|pints?|ounces?|oz"
                     r"|pounds?|handfuls?|pinch(?:es)?)\b", re.I)


# The words that can put a quantity in front of the thing it is a quantity of: "100g plain
# flour", "one and a half mugs of water", "three eggs".
_AMOUNT_BEFORE = (r"\d+(?:\.\d+)?\s*(?:g|kg|ml|cl|l|oz|lb|cm)?|one|two|three|four|five|six|"
                  r"seven|eight|nine|ten|eleven|twelve|half|quarter|dozen|mugs?|cups?|spoons?|"
                  r"teaspoons?|tablespoons?|grams?|kilograms?|kilos?|litres?|liters?|pints?|"
                  r"ounces?|pounds?|handfuls?|pinch(?:es)?")
# A quantity given by proportion rather than in figures: "use the same weight of butter".
_PROPORTION_PHRASE = (r"same weight|same amount|equal weight|equal amount|half as much|twice|"
                      r"double|three times")


def _amount_for_the_name(clause, named):
    """True when the clause ties a quantity to that very thing, not to a neighbour.

    "Weigh the eggs and use the same weight of soft butter" gives an amount for the butter, so
    "how many eggs" must not be answered with it; "three eggs fills two tins" does answer it.
    The number or unit has to sit right before the word that was asked about, or a proportion
    phrase has to lead to it a few words later.

    The words are read with their joining words in ("the same weight of soft butter"), because
    "of" and "same" are exactly what says the amount belongs to the thing after them.
    """
    text = " " + re.sub(r"[^a-z0-9. ]+", " ", str(clause).lower()) + " "
    for name in {str(one).lower() for one in named}:
        thing = re.escape(name.rstrip("s")) + r"s?"
        if re.search(r"\b(?:" + _AMOUNT_BEFORE + r")\s+(?:[a-z]+\s+){0,2}" + thing + r"\b",
                     text):
            return True
        if re.search(r"\b(?:" + _PROPORTION_PHRASE + r")\s+(?:[a-z]+\s+){0,3}" + thing
                     + r"\b", text):
            return True
    return False


# Where one clause of an answer ends and the next begins.
#
# A comma inside a number is part of the number: "About 7,000 to 8,000 steps a day" cut at its
# comma leaves "000 steps a day is where most of the benefit is", which was said back as the
# answer to "how many steps in a 5k"; "£400,000" left "000 first home in Scotland" for the
# same reason, and a boiler price cut at its comma was "800 to £3.". So a comma is a seam only
# when it is not between two digits - and it has to be written so that no wider alternative can
# match it first: a plain [:,;] character class in front of the guard swallows every comma and
# the guard never runs, which is how "000 steps a day" got through.
CLAUSE_SEAM = re.compile(r"(?:(?<=\D)[:,;]|[:,;](?=\D))|\bthen\b")

# The kind of quantity a line asks for, said in a part of an answer. Only the kinds that cannot be
# said without their own words are checked; an amount ("how much sugar") can be given by
# proportion ("the same weight of sugar"), which is the case the part reader exists for.
KIND_SAID = {
    "time": re.compile(r"\d|\b(?:an?|one|two|three|four|five|six|seven|eight|nine|ten|twelve|"
                       r"fifteen|twenty|thirty|forty|fifty|sixty|ninety|hundred)\s+"
                       r"(?:seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?)\b"
                       r"|\bovernight\b|\ba few (?:hours?|days?|weeks?|months?)\b", re.I),
    "money": re.compile(r"£\s*\d|\b\d[\d,.]*\s*(?:pounds?|quid|dollars?|euros?)\b", re.I),
    "heat": re.compile(r"\d\s*(?:°|degrees?|gas mark|C\b|F\b)", re.I),
    "distance": re.compile(r"\d\s*(?:miles?|km|kilometres?|kilometers?|metres?|meters?|yards?|"
                           r"feet|foot)\b", re.I),
    "clock": re.compile(r"\b\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm|o'clock)\b|\b\d{1,2}[:.]\d{2}\b",
                        re.I),
}
# The words a clause cannot start with, because they tie it to the clause before it. A clause
# cut at a comma that begins with one of these is half a sentence, not an answer.
JOINING_WORD = re.compile(r"^\s*(?:which|that|who|whom|whose|where|because|though|although"
                          r"|whereas|while|yet|however|instead|plus|as well)\b", re.I)


def _sentence_naming_the_part(reply, text):
    """The clause of the answer that gives a quantity for the thing a follow-up asks about.

    Some answers give a quantity by proportion instead of in figures: "how do i make a cake"
    says to weigh four eggs and use the same weight of butter, sugar and flour, so "how much
    sugar" has no number to read out and the figure reader returned nothing, and the question
    got a shrug. The clause that gives it is the answer, and it is part of the answer just
    given, not a new one.

    The amount has to be for the thing that was named: a sentence that only mentions the word
    ("Caster sugar and self-raising flour.") is not an amount, and a sentence whose amount
    belongs to something else ("the same weight of soft butter" for "how many eggs") is a
    wrong answer where a shrug was right.
    """
    kind = asked_kind(text)
    if kind is None or kind in ("cause", "order"):
        return None
    # The same words the part reader counts as a thing: "how long do they go in for?" names
    # nothing ("go" is a verb), so it cannot pick a clause out of an answer by its words.
    named = set(words_of(text)) - PROPERTY_WORDS - NOT_NEW - WHERE_WORDS
    if not named:
        return None
    sentences = [one.strip() for one in SENTENCE.split(str(reply or "").strip()) if one.strip()]
    if not sentences:
        return None
    flat_reply = _flat(reply)
    for sentence in sentences:
        for clause in CLAUSE_SEAM.split(sentence):
            clause = clause.strip(" .,")
            if not clause or not named & set(words_of(clause)):
                continue
            if not _amount_for_the_name(clause, named):
                continue
            # A list split by its commas leaves fragments that say "half white vinegar": the
            # amount is there and the thing is there, but it is a piece of a list rather than a
            # sentence, and "Half white vinegar." is no answer at all. A real clause carries a
            # ratio or enough words to read as one.
            if len(clause.split()) < 4 and not re.search(r"\b(?:of|to|per)\b", clause):
                continue
            if JOINING_WORD.match(clause):
                # "..., which is about four cups of instant coffee" is the second half of a
                # sentence: said on its own it read as "Which is about four cups of instant
                # coffee." - a relative clause with no subject in it, handed over as the answer
                # to "how much coffee is too much". The sentence the clause was cut from holds
                # the figure and the thing both, so that is the part that answers.
                clause = sentence.strip().rstrip(",;: ")
                if len(clause.split()) > 40:
                    continue  # a long sentence is not a narrowing of a long answer
            elif clause[0].islower():
                clause = clause[0].upper() + clause[1:]
            part = clause + ("" if clause.endswith((".", "!", "?")) else ".")
            if _flat(part) == flat_reply:
                return None  # the whole answer, which would be the same answer twice
            return part
    return None


# A head that counts the causes instead of naming one, and a head that only says a cause exists:
# both are labels for the half after the colon. "One heavy thing is the usual cause: a duvet or a
# bath mat balls up on one side" is one sentence in the washing-machine card, and cut at its colon
# it answered "why does it do that" with "One heavy thing is the usual cause." - a label with the
# cause, which was in the half that was dropped, gone.
COUNTS_THE_CAUSES = re.compile(
    r"^\s*(?:(?:it|that|this|there)\s+(?:is|are|s)\s+)?"
    r"(?:(?:usually|often|mostly|nearly always|probably)\s+)?"
    r"(?:one|ones|a few|a couple|several|a number|a combination|a mix|many|most|some|two|three|"
    r"a lot|a range|nothing|everything)\b", re.I)
# The words a head uses to say that a cause exists, or to count one, without naming it. What is
# left when these are taken out is the subject: "Overwatering is the usual cause" keeps
# overwatering, "the usual cause" keeps nothing and names nothing.
NAMES_NO_CAUSE = frozenset("""cause causes reason reasons usual usually common commonest main
mostly often likely probably real whole only most thing things something anything everything
one ones part parts bit couple few number several combination mix lot lots many some""".split())


def _names_no_cause(head):
    """True for the head of a colon sentence that labels a cause without naming one."""
    head = str(head or "")
    if COUNTS_THE_CAUSES.match(head):
        return True
    return not (set(keywords(head)) - NAMES_NO_CAUSE)


def _cause_part(part):
    """The side of a colon sentence that gives the reason, or the whole sentence when neither
    side names a cause. A colon can open a list of causes, a step, or the advice that follows
    the reason, so the side is chosen by what it says, not by its position."""
    part = str(part or "").strip()
    if ":" not in part:
        return part
    head, tail = part.split(":", 1)
    for candidate in (head, tail):
        if candidate is head and _names_no_cause(head):
            # A head that only points at the cause is not the cause: the sentence is kept whole,
            # because the half after the colon is where the reason actually is.
            continue
        if CAUSE.search(candidate):
            candidate = candidate.strip().rstrip(",;")
            if candidate and candidate[0].islower():
                candidate = candidate[0].upper() + candidate[1:]
            return candidate + ("" if candidate.endswith((".", "!", "?")) else ".")
    return part


def _reason_again(reason, last):
    """The same reason said another way when it was just given.

    A cause answer says its subject and then the reason ("A sore knee is usually a strain...").
    Asked again, the reason on its own reads better than the whole answer, and the short form
    ("Usually a strain...") is not the same line again. The two forms alternate.
    """
    reason = str(reason or "").strip()
    match = re.match(r"^(.*?)\b(?:is|are|was|were)\s+(usually|commonly|often)\s+(.+)$",
                     reason, re.IGNORECASE)
    if match:
        short = "{} {}".format(match.group(2).capitalize(), match.group(3))
        if _flat(short) != _flat(reason):
            if _flat(reason) == _flat(last):
                return short
            if _flat(short) == _flat(last):
                return reason
    if _flat(reason) == _flat(last) and re.search(r",\s*so\b", reason, re.I):
        short = re.split(r",\s*so\b", reason, 1, flags=re.I)[0].strip().rstrip(",;")
        short += "" if short.endswith((".", "!", "?")) else "."
        if _flat(short) != _flat(reason):
            return short
    return reason


# A line asking for a measure, and a sentence that carries one. Used to keep the entry that
# answers a price or a time, instead of handing the turn to an entry that says how to fit it.
ASKS_A_MEASURE = re.compile(
    r"\b(?:how\s+(?:much|many|long|often|far|big|old)|when|what\s+time|price|cost|cheapest)\b",
    re.I)
A_MEASURE = re.compile(r"[\d\u00a3$\u20ac]|\b(?:one|two|three|four|five|six|seven|eight|nine|"
                       r"ten|twenty|thirty|forty|fifty|hundred|thousand)\b", re.I)


# A "when" that puts a condition on the time rather than asking for a span: "its sore when i sit
# down", "it clicks when i climb the stairs". The sentence of the last answer that carries a
# figure can then be its warning - "or if it is still there after eight weeks" - and handing that
# back on its own gives somebody who described a twinge the red flag instead of the advice it came
# with.
# A figure that only says how long *before* something to arrive or act is a lead time, not the
# length or the amount the line asked for: with the airport card in hand, "how long is the flight"
# was answered "45 to 60 minutes", which is when the bag drop shuts, and the flight itself is an
# hour and a quarter. The line has to be asking for a span for this to apply - "how long before i
# need to be there" is the lead time, and the same sentence answers it.
A_LEAD_TIME = re.compile(
    r"\d[\d.,]*\s*(?:to\s*\d[\d.,]*\s*)?(?:minutes?|mins?|hours?|hrs?)\s+"
    r"(?:before|ahead of)\b", re.I)
ASKS_A_SPAN = re.compile(r"\bhow\s+(?:long|many\s+(?:minutes|hours|days|weeks))\b", re.I)
WHEN_IS_A_CONDITION = re.compile(
    r"\bwhen\s+(?!'s|s\b|\?|should\b|shall\b|do\b|does\b|did\b|will\b|would\b|can\b|could\b|"
    r"is\b|are\b|was\b|were\b|am\b|must\b|to\b)\w+", re.I)
# A sentence that only sends the person to somebody else. It is part of an answer, not an answer
# on its own: the figure it carries is when to go, not the length or the amount that was asked for.
A_WARNING = re.compile(
    r"\b(?:see|speak to|talk to|ring|call|contact|visit|go to)\s+"
    r"(?:a|an|your|the|nhs|111|999)?\s*"
    r"(?:gp|doctor|dentist|midwife|health visitor|pharmacist|a&e|ae|casualty|hospital|"
    r"111|999|out of hours)\b"
    r"|\bget (?:it|them|that) (?:checked|looked at|seen)\b"
    r"|\b(?:urgent|urgently|straight away|same day|a&e|casualty)\b", re.I)


def _asked_figure(text, reply, other_reply):
    """The sentence of `reply` that carries the figure this line asks for, or "".

    Only when the entry just read has one and the other entry does not: "how much is a new one"
    is the price they have already been told, and a fitting note is not the answer to it.

    A conditional "when" asks for no figure at all: "it aches when i walk" does not want the
    warning at the end of the last answer, it wants the advice that answer opened with, and the
    warning is where the only number in it tends to sit. Skipping a sentence that only sends
    them to a doctor leaves the rest of the answer to say its piece.
    """
    if not ASKS_A_MEASURE.search(str(text or "")):
        return ""
    condition = bool(WHEN_IS_A_CONDITION.search(str(text or "")))
    if A_MEASURE.search(str(other_reply or "")):
        return ""
    for sentence in SENTENCE.split(str(reply or "").strip()):
        if not A_MEASURE.search(sentence):
            continue
        if condition and A_WARNING.search(sentence):
            continue
        return sentence.strip()
    return ""


def _the_figure(text, reply):
    """The sentence of `reply` carrying the figure this line asks for, or ""."""
    return _asked_figure(text, reply, "")


def _sentence_with(reply, part):
    """The sentence of `reply` that `part` was cut from.

    A sentence here is one a person would read as one, so a quotation is never split: the words
    an answer hands over to say carry full stops of their own, and the sentence holding them ends
    where the quote does (`same_again.quoted.sentences`)."""
    wanted = _flat(part)
    for sentence in same_again.quoted.sentences(reply, SENTENCE):
        if wanted and wanted in _flat(sentence):
            return sentence.strip()
    return ""


def _part_not_repeated(part, whole, memory):
    """The part of an answer that answers this line, said another way if it was just said.

    The same follow-up twice ("what temperature for roast potatoes", "what pressure should it
    be?") gets the same figure twice, and a reply that repeats its own last words reads as
    broken. The sentence the figure was cut from says it with its context, and the answer it
    came from says it whole: either is the same answer without the same words.
    """
    if not isinstance(part, str) or not part.strip():
        return None
    if _flat(part) != _flat(mem.last_bot(memory) or ""):
        return part.strip()
    whole = whole if isinstance(whole, str) and whole.strip() else part
    if _flat(whole) == _flat(mem.last_bot(memory) or ""):
        # The whole of it is what is already on the screen, so handing it back is the repeat this
        # guards against: no part of this answer is new to the conversation.
        return None
    sentence = _sentence_with(whole, part)
    if sentence and _flat(sentence) != _flat(part):
        return sentence
    if _flat(whole) != _flat(part):
        return whole.strip()
    return None


# A property that the line names itself, rather than the general shape of the ask. "How long will
# it take?" only asks for the total; "how long should I rest it?" names resting, and if the answer
# just given never mentions resting, another entry's time is not an answer to this line.
GENERIC_ASK = frozenset("""
long time times minute minutes hour hours day days take takes will start finish
cook cooking bake baking roast roasting boil boiling fry frying grill grilling
""".split())


# Words about *when* a job is done, not about what the job is: "how long should i cook it for
# next time" names no thing of its own, so it is a question about the answer just given however
# little of its wording it shares with it.
# "in", "into", "on" and "at" say where a thing is, not what it is: "how long do they go in
# for?" names no thing of its own.
WHERE_WORDS = frozenset("""
go goes going went gone put puts putting get gets getting set sets use uses using
in into on at for to of with it them they that this there here
""".split())


NOT_NEW = frozenset("""
next again tonight today tomorrow yesterday now soon later still just once twice another other
bit lot lots week weeks month months year years time times future onwards onward
""".split())


def _names_a_property(text):
    """True when the line names a property of its own, not just a length or a price."""
    return bool(set(keywords(text)) & (PROPERTY_WORDS - GENERIC_ASK))


# A short ask that names no thing of its own: "what should i see", "what should i do", "where
# should i eat". The words are an ask and a verb, and what it is about is only in the chat.
BARE_ASK = re.compile(r"^\s*(?:so\s+|and\s+|ok\s+|okay\s+)?"
                      r"(?:what|which|where|who|when|how)\b[^?]{0,40}"
                      r"\b(?:see|do|eat|visit|book|buy|pack|take|wear|cook|make|get|try|"
                      r"recommend|suggest|start)\b\s*[?.!]*\s*$", re.IGNORECASE)


def _with_bare_subject(text, memory):
    """A bare ask with the thing it is about on the end: "what should i see" -> "what should
    i see rome". The words the entry matches on are in the subject, so the ask carries it."""
    if not BARE_ASK.match(text):
        return text
    subject = mem.subject(memory)
    if not subject or TIME_WORD.match(subject.strip()):
        return text  # a month or a weekend is not a thing the person named
    wanted = [word.strip(".,!?;:").lower() for word in subject.split()]
    if any(word in text.lower() for word in wanted):
        return text
    return text.rstrip("?.! ") + " " + subject


def _the_things_to_try(understood, memory):
    """The things a "that" in the line could mean, newest first.

    The subject is not always the newest thing: "we are going to rome" then "we are going to
    lisbon" leaves the subject on Rome, and answering the second trip with the first trip's
    figure is a wrong answer where a hedge is not. So the thing the last turn named is tried
    first, then the thing the store resolved the pronoun to, then the subject. Each candidate
    still has to reach an entry that is about it, so a word that is nobody's subject ("going")
    finds nothing and the next one is tried.
    """
    things = []
    leans = understood.get("leans_on") if isinstance(understood, dict) else None
    if isinstance(leans, dict):
        for word in leans.get("words") or []:
            if isinstance(word, str) and len(word.strip()) > 2:
                things.append(word.strip().lower())
    ref = understood.get("ref") if isinstance(understood, dict) else None
    if isinstance(ref, dict):
        for word in ("that", "it", "this"):
            value = ref.get(word)
            if isinstance(value, str) and value.strip():
                things.append(value.strip())
                break
    if mem.subject(memory):
        things.append(mem.subject(memory))
    seen, out = set(), []
    for thing in things:
        if thing and thing not in seen:
            seen.add(thing)
            out.append(thing)
    return out


def _the_answer_from_thing(text, thing, memory):
    """The entry for `thing` and its reply to the line, or (None, None) when no entry answers it
    as that thing. The line is written out with the thing in place of its "that"."""
    if not thing:
        return None, None
    fuller = (_with_subject(text, memory) if thing == mem.subject(memory)
              else _with_the_thing(text, thing))
    if fuller.strip() == str(text).strip():
        return None, None
    wider = understand(fuller, memory)
    found, said = _offer(lambda reject: find(wider, reject=reject), memory, wider)
    if found is None or not _is_about(found, thing) or _said_before(said, memory):
        return None, None
    return found, said


def _with_the_thing(text, thing):
    """The line with its "that"/"it" written out as the thing: "...that cost" -> "...the rome
    cost". The line itself when it has no such word."""
    words = str(text).split()
    said = [word.strip(".,!?;:").lower() for word in words]
    if not thing:
        return text
    for i, word in enumerate(said):
        if word in REFERRING:
            words[i] = "the " + thing
            return " ".join(words)
    return text


def _care_holds(text, memory):
    """True when the composer is already holding this line inside a safety thread.

    A follow-up in a first-aid chat ("should i put butter on it" after a burn) is the composer's
    turn: it has the careful continuation, and the knowledge base would have to widen the line
    with the conversation's subject to reach an entry at all ("...on the oven"), which answers a
    question nobody asked. One door, so the wording and the judgement of what still counts as the
    same thread stay in bot/compose/.
    """
    try:
        from ..compose import fallback as composer
        return bool(composer.careful(text, memory))
    except Exception:  # noqa: BLE001 - a composer that cannot answer only adds no guard
        return False


def _named_by(item, subject):
    """True when the subject names the entry, not just brushes one of its words.

    The subject put on the end of a follow-up is a gist, and a gist holds words that belong to
    other things: "keep getting security code" shares "security" with the airport scanner entry,
    which is not what the conversation is about. So the entry has to match a phrase of the
    subject, or at least two of its words.
    """
    keys = _key_words(item)
    low = " " + subject.lower() + " "
    phrases = set()
    for part in getattr(item, "key", ()) or ():
        options = (part,) if isinstance(part, str) else part
        for option in options:
            option = str(option).lower().strip()
            if " " in option and option in low:
                phrases.add(option)
    if phrases:
        return True
    # A single short key word is enough: the second key group of an entry is the ask
    # ("nervous", "what to", "bring"), and those words say how the line is put, not what it is
    # about. Two subjects words have to be there, and both of them from the subject side of the
    # entry, or "what can we do before the first day" reaches the first day at a new job.
    subject_keys = set()
    for part in (getattr(item, "key", ()) or ())[:1]:
        options = (part,) if isinstance(part, str) else part
        for option in options:
            for word in str(option).lower().split():
                subject_keys.add(word.rstrip("s") or word)
    if len(low.split()) == 1:
        # A subject of one word ("cat") can never reach the two-word rule below, and it is the
        # whole thing the chat is about: "im thinking of getting a cat" then "what about
        # holidays". One word from the entry's first key group is the most it can offer, so that
        # is the test, and the entry still has to be about the thing as well.
        return bool(subject_keys)
    found = 0
    for word in low.split():
        word = word.strip(".,!?;:").rstrip("s")
        if len(word) > 2 and word in subject_keys:
            found += 1
    return found >= 2


def _the_answer_was_about_the_subject(memory):
    """True when the thing the chat is on is also what the last answer was about.

    "and what about holidays" adds a dimension to the thing on screen, so the thing is read with
    it - but only while the answer just given was about that thing. The chat on a dog went on to
    "im going to italy in may", which the Italy entry answered, and the next line ("what about
    money") was hung on the dog and got the price of a puppy. A stored subject can lag a topic
    change by a turn; the answer that was just given does not.
    """
    subject = str(mem.subject(memory) or "").lower()
    if not subject:
        return False
    last = memory.get("entry_answer")
    keys = getattr(last, "get", lambda *_: None)("keys") if isinstance(last, dict) else None
    if not keys:
        return True
    words = {word.strip(".,!?;:").rstrip("s") for word in subject.split()}
    return bool(words & {str(key).lower().rstrip("s") for key in keys})


# A line that adds a dimension to the thing on screen instead of naming a new subject:
# "and what about holidays", "how about at night", "what if it rains". The thing said last is
# still what it is about, so the subject may be put on the end of it.
ADDING_TO_THE_SUBJECT = re.compile(
    r"^\s*(?:and\s+)?(?:what|how)\s+about\b|^\s*(?:and\s+)?what\s+if\b|"
    r"^\s*and\s+(?:for|at|on|with|in)\b", re.IGNORECASE)
# A measure of the thing in hand is not a new subject: "what about a bowl" after the protein in
# porridge is the same protein question about a bowl, and read as a new subject it reached the
# cereal-portion card instead of the figure. The earlier question's shape answers a measure;
# an actual new subject ("what about holidays") still goes the new way.
A_MEASURE_OF_THE_SUBJECT = re.compile(
    r"^\s*(?:and\s+)?(?:what|how)\s+about\s+(?:a|an|one|two|three|four|\d+)?\s*"
    r"(?:bowl(?:ful)?|cup(?:ful)?|plate(?:ful)?|mug(?:ful)?|glass(?:ful)?|servings?|portions?|"
    r"slices?|pieces?|handfuls?|spoons?|spoonfuls?|tablespoons?|teaspoons?)\b", re.IGNORECASE)

# Words that carry no subject, so a line that is only these says nothing about itself.
GENERIC = {"should", "would", "could", "how", "what", "when", "where", "which", "about", "tomorrow",
           "today", "tonight", "them", "they", "have", "need", "want", "much", "many", "does",
           "did", "will", "this", "that", "there", "then", "with", "your", "mine", "some",
           "thing", "things", "please", "thanks", "maybe", "really", "also", "just", "like"}


# "1 hour 40 minutes" is one figure, not an hour plus forty minutes: it is read as 100 minutes
# before the spans are taken, so two answers can be compared figure for figure.
_HOURS_AND_MINUTES = re.compile(
    r"\b(\d+)\s*(?:hours?|hrs?)\s*(\d+)\s*(?:minutes?|mins?)", re.I)


def _minutes_in(text):
    """Every length of time a piece of text states, in minutes, as (low, high) pairs."""
    if not isinstance(text, str) or not text:
        return []
    stated = _HOURS_AND_MINUTES.sub(
        lambda m: "%d minutes" % (int(m.group(1)) * 60 + int(m.group(2))), text)
    found = []
    for match in re.finditer(
            r"\b(\d+)(?:\s*(?:to|-|\u2013)\s*(\d+))?\s*(minutes?|mins?|hours?|hrs?)\b",
            stated, re.I):
        unit = 60 if match.group(3).lower().startswith(("h",)) else 1
        low = int(match.group(1)) * unit
        high = int(match.group(2) or match.group(1)) * unit
        found.append((low, high))
    return found


def _a_figure_apart(mine, theirs):
    """True when two answers give lengths of time that cannot both be about the same thing.

    "40 minutes" and "1 hour 40 minutes" are two answers to "how long does this take", and a
    bird cannot be both. Two answers are apart when one states a span the other's spans leave
    out: a rate and a total ("20 minutes per 500g plus 20 minutes, so a 2kg bird takes about 1
    hour 40") is apart from a short figure that is neither of them.
    """
    mine_spans = _minutes_in(mine)
    their_spans = _minutes_in(theirs)
    if not mine_spans or not their_spans:
        return False
    return any(high_other < low or high < low_other
               for low, high in mine_spans for low_other, high_other in their_spans)


def _only_a_figure(part):
    """True when the part is a sum of money and nothing else ("£800 to £1,200.")."""
    if not isinstance(part, str) or not part.strip():
        return False
    words = words_of(part)
    return bool(re.search(r"[\u00a3$\u20ac]|\bpounds?\b|\bquid\b", part)) and len(words) <= 6


FIGURE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _figures(text):
    """The numbers a line states, comma or not: "£400,000" and "400000" are one figure."""
    return {one.replace(",", "") for one in FIGURE.findall(str(text or ""))}


# The words the knowledge base keys *few* entries on: the things it knows about, as opposed to
# the words that say how a line is put ("spend", "afford", "fix") and the common words that end
# up in a key because they are part of some entry's name ("put", "one", "before", "never").
# Built once.
_NAME_WORDS = None
_NAME_DOMAINS = {}
FEW_ENTRIES = 12


# A time word says when, not what: "how long until he is house trained" names the puppy, not
# "until". `trained` and `frozen` are a state of the thing in hand, not another thing, so neither
# may stand in as the thing the line names.
WHEN_NOT_A_THING = frozenset("""
until till since while during before after within ago
""".split())


def _name_words():
    """The words that name a thing: keyed on by a handful of entries, not by the whole base.

    Asking every word any entry is keyed on is too wide to be useful - "ive never done one
    before" is four such words, and a guard that refuses a follow-up for any of them turns
    ordinary chats into a punt ("how do i give a talk at work" then "ive never done one
    before" lost its answer). A thing the base knows has a name, and a name keys a few entries:
    "fluent" keys one, "pension" five, "presentation" nine. "put" keys 74 entries and "one" 99,
    so neither is a name.
    """
    global _NAME_WORDS
    if _NAME_WORDS is None:
        counted = {}
        domains = {}
        try:
            for one in all_entries():
                field = getattr(one, "domain", None)
                for word in _key_words(one):
                    counted[word] = counted.get(word, 0) + 1
                    if field:
                        domains.setdefault(word, set()).add(field)
        except Exception:  # noqa: BLE001 - the guard is an extra, it must not stop a turn
            counted = {}
            domains = {}
        _NAME_WORDS = {word for word, seen in counted.items() if seen <= FEW_ENTRIES}
        _NAME_DOMAINS.clear()
        _NAME_DOMAINS.update({word: domains.get(word, set()) for word in _NAME_WORDS})
    return _NAME_WORDS


def _filler(word):
    """A word that says how a line is put, not what it is about: "until", "theyre", "should"."""
    if word in GENERIC or word in mem.topics.STOPWORDS or word in NOT_NEW:
        return True
    if word in PROPERTY_WORDS or word in WHEN_NOT_A_THING:
        return True
    for tail in ("re", "ve", "ll", "d", "m"):
        if word.endswith(tail) and word[:-len(tail)] in mem.topics.STOPWORDS:
            return True
    return False


def _left_out(item, text):
    """True when the line names a thing this entry never mentions.

    A follow-up is written out with the subject on the end and the entry is read from that
    rewrite, so nothing looked at the words the person actually typed: "how long until i'm
    fluent" after "i practice on the bus" became "how long until i'm fluent for the practice
    bus?" and the coach price (bus, how long) answered it. "fluent" is a word the knowledge base
    keys an entry on - the language one - and the coach entry never says it, so the widening put
    the wrong thing back. A name the base knows, that this entry does not say, is that case; the
    words that only say how a line is put, and the common words that ride along in a key, are not
    names and never block.
    """
    keys = _key_words(item)
    names = _name_words()
    for word in re.findall(r"[a-z']+", str(text or "").lower()):
        word = word.rstrip("'")
        if len(word) < 4 or _filler(word):
            continue
        bare = word.rstrip("s") or word
        if bare in keys or word in keys:
            continue
        if bare in names or word in names:
            # A name the entry's own field answers for is an aspect of the thing in hand, not
            # another thing: "house trained" after a puppy is a pets question, and a pets entry
            # is keyed on "trained", so the puppy's answer stands. "fluent" is a study word and
            # the coach entry is travel, so that one is the wrong thing being put back.
            field = getattr(item, "domain", None)
            if not any(field in _NAME_DOMAINS.get(form, ()) for form in (word, bare)):
                return True
    return False


def _keyed_on_the_line(item, text):
    """True when the entry is keyed on a word the line itself says: "wear" in "what do i wear".

    A word that only gives the shape of the ask names nothing of its own: "how long should i cook
    it for next time" was keyed on "long" and on "next" - the words of the plan entry, whose keys
    hold the length of a job and "next week" - so the line was read as a plan question from
    another subject, and the rice answer came back whole instead of its twelve minutes."""
    keys = _key_words(item)
    for word in re.findall(r"[a-z']+", str(text).lower()):
        if len(word) < 3 or word in GENERIC or word in NOT_NEW or word in PROPERTY_WORDS:
            continue
        if (word.rstrip("s") or word) in keys:
            return True
    return False


def _shares_a_word(item, subject):
    """True when the entry is keyed on a word of the subject: "save money" is about saving."""
    keys = _key_words(item)
    for word in subject.lower().split():
        word = word.strip(".,!?;:")
        if len(word) > 2 and (word.rstrip("s") or word) in keys:
            return True
    return False


# A line that asks for a figure is answered by a figure, and an entry that holds none answers a
# different question: "how much roughly to fix" after a brake that clicks reached the entry about
# the noise itself, whose answer says what to listen for and no price at all.
FIGURE_ASKS = ("money", "amount", "time", "clock", "heat", "distance", "pressure")


def _answers_the_figure(text, reply):
    """False when the line asks for a figure and the entry's answer names none of that kind.

    Only an answer that holds no figure is turned away: one that states a figure in any of the
    shapes a person writes it (£80 to £200, "20 to 30 minutes", "a couple of minutes")
    is answering the line. An entry that answers a step or a reason is asked for one, so it
    never comes here. A reply chosen later from a callable cannot be read, and is left alone.
    """
    if not isinstance(reply, str) or not reply.strip():
        return True
    kind = asked_kind(text)
    if kind not in FIGURE_ASKS:
        return True
    wanted = {kind}
    if kind in ("amount", "money"):
        # A sum of money answers "how much" whether the line asks a price or a quantity, and
        # it is written in the money shape ("£80 to £200") rather than the amount one.
        wanted.add("money")
    for one in wanted:
        pattern = SIGNALS.get(one)
        if pattern is not None and pattern.search(reply):
            return True
    return False


# A line that asks how to say something to someone is about the person and the moment, not
# about the topic: "how do i raise it without sounding like i'm keeping score" after a friend
# who keeps cancelling plans is not a question about cancelling, and reading the referring word
# as the topic ("how do i raise the cancelling plans ...") handed it the how-to-cancel wording,
# which is the message the other person would send. The referring word in these shapes is what
# is said or who hears it, so the topic is not put back in for them.
#
# "how do i tell if the egg is off" is a diagnosis and not this shape, so the tell-words carry
# a guard for what follows them.
#
# The verb needs its object, the same way the fallback's wording pattern does, and the verbs are
# only the ones that mean saying something: raise, broach, word, phrase, put. "Approach" and
# "tackle" are left out on purpose - "my bike is squeaking" then "how do i approach it" is a fix
# question about the bike, and blocking the bike for it lost the chain answer. A bare "how do i
# approach my boss about a pay rise" is left to the entry that owns it.
#
# A machine "sounding like" something is the commonest way people say it is making a noise, and
# that is not a tone ask either: the tone is named by "without sounding like" and "not sounding
# like", never by the bare words.
SAY_IT = re.compile(
    r"\bhow (?:do|should|can|could|would) i (?:raise|broach|word|phrase|put)"
    r"\s+(?:it|this|that|the subject|the issue)\b"
    r"|\bhow (?:do|should|can|could|would) i (?:say|tell)\b(?!\s+(?:if|whether|the difference"
    r"|when|what))"
    r"|\bbring (?:it|this|that) up\b|\bbroach (?:it|this|that)\b"
    r"|\bwithout sounding\b|\bnot sounding\b|\bnot wanting to sound\b"
    r"|\bwithout (?:being|coming across|upsetting|offending|hurting)\b"
    r"|\bwhat (?:should|do) i say to\b",
    re.IGNORECASE)


def _asks_how_to_say_it(text):
    """Whether the line asks how to say something rather than what the thing is."""
    return bool(SAY_IT.search(text or ""))


def _in_the_subjects_field(item, subject):
    """Whether the entry is in the same field as the thing the subject names, or has no field."""
    field = (understand(subject) if subject else {}).get("topic")
    if not field:
        return True  # nothing to go on, so nothing to rule out
    return getattr(item, "domain", None) == field

# The words of an ask rather than of a thing: how/do/want, the articles and pronouns, laughter,
# periods of time, and the little words people hang a question on.
_ASKING_ONLY = frozenset("""how much many long far often soon old big large small hot cold warm
fast slow quick heavy light high deep thick thin wide tall low early late few more less most least
time times cost costs price worth take takes last lasts
do does did can could would should shall will may might must need needs want wants
get gets got make makes made use uses using put
i me my we our you your a an the it its that this they them there
and or but for of to in on at with from about than then too also just really very
good nice best better worse right wrong new
one ones thing things kind type sort way part bit
lol lmao haha hahaha hmm hm mmm ah oh yeah yep ok okay
today tomorrow tonight week weekend month year day night morning evening
away around back down up out over any some all
""".split())


def _own_thing_words(text, memory):
    """The words in the line that name a thing of its own, not the ask or the subject on screen.

    A question is not a follow-up just because it is a question: "how much is a tv licence" after
    "what is a credit score" was read as one that had left its subject out, the credit score was
    hung on the end of it, and "how much" is a property the credit entry knows - so the licence
    question came back as the credit report, and so did a driving licence and a tip. The words
    that make it a question (how, much, should) are not the thing asked about; "tv" and "licence"
    are. A line that brings no such word ("and how much is that", "how long does it take") really
    has left its subject out and keeps the follow-up.
    """
    understood = understand(text, memory)
    subject = str(mem.subject(memory) or "").lower()
    out = []
    for word in understood.get("keywords") or []:
        low = str(word).lower()
        if low in _ASKING_ONLY or low in subject or low.isdigit() or len(low) < 3:
            continue
        out.append(low)
    return tuple(out)


def _about_the_talk(item, text, memory, reading):
    """False when the entry is from a part of the knowledge base this talk never touched.

    A follow-up names no thing of its own, so its bare words can look like a thing they are not:
    "we got a puppy" and then "how long until he is house trained" reached the first-home entry
    off "house" and answered with a deposit plan the puppy conversation had nothing to do with.
    The entry has to be about the thing the conversation is on, or about a topic the line itself
    names; when it is neither, this module steps aside and the one with the real answer gets it.

    A line that says it is changing the subject is not a follow-up at all: "ok changing the
    subject, im planning a curry tonight" after a dripping tap is about the curry, and reading
    its words against the tap threw away the recipe that answers it. The person has told us the
    old thing is done with, so nothing below treats them as still leaning on it.
    """
    read = (memory or {}).get("understood") if isinstance(memory, dict) else None
    if isinstance(read, dict) and read.get("change_of_subject"):
        return True
    subject = mem.subject(memory)
    record = mem.current(memory)
    if not isinstance(record, dict) or record.get("turn") == len(memory.get("turns") or []):
        # The record the subject would be read from is the line being answered, so there is no
        # other subject this talk is on yet: the first line of a conversation, or one that
        # started a new one, is the whole of it so far. Read back as a thing the answer has to
        # be about, that line's own noun throws away every answer that speaks to the situation
        # without saying the noun again - "how do i deal with a friend who always cancels" is
        # about the friend, the advice is about the pattern, and the person got the search hedge
        # instead of "Say it once, about the pattern rather than the last time". It is the same
        # mistake the store itself avoids in `bot/memory/topics.py::is_follow_up`, which does
        # not read a record written for this very line as the thing before it.
        return True
    thing = _head_thing(subject)
    if not thing:
        return True  # nothing the talk is on: the bare words are all the line has
    if _is_about(item, thing):
        return True
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not turns:
        # The first line of a talk is not a follow-up: it contradicts nothing, because there is no
        # earlier turn to contradict. Whatever the head of that line reads as, the subject the
        # memory holds is the line's own words, so an entry about them is the answer it has and
        # there is nothing this talk has "never touched" yet. Read as a follow-up the line loses
        # it: the head reading takes the verb ("what should i eat before a football match" is
        # about "eat"), and "should i take vitamin d in winter" reads as "take", so the person got
        # a hedge for two things the knowledge base answers well. A later line keeps the whole
        # guard: "we got a puppy" / "how long until he is house trained" steps aside for "house".
        return True
    if _names_the_entry(text, item):
        return True  # the line names the thing the entry is about, in so many words
    if _a_definition_of_the_entry(text, item):
        return True  # the line asks what the thing the entry is about means
    if _names_the_thing_apart_from_the_talk(item, text, subject, reading):
        return True  # the line names the entry's own subject and none of the talk's
    # A why-line says what it is about, so the entry that knows that thing is its
    # answer whatever this talk is on: the domain test above is for a follow-up that
    # names nothing of its own, and applied to a why-line it stood the allergy answer
    # down after a chat about cats.
    if _a_why_line_that_names(item, reading):
        return True
    if _the_field_on_the_screen(item, text, reading, memory):
        return True
    if _says_the_ask_whole(text, item):
        # A hand-over names nothing but the ask itself: "quiz me", "test me", "hit me with a
        # question". There is no subject in it to read against the thing this talk is on, so the
        # guard above threw the quiz away a turn after a chat about somebody's son ("my son loves
        # quizzes" / "quiz me" got "Thanks for telling me - I'm here if you want to dig into any
        # of that"). A whole line that is one of the entry's own key phrases, two words or more,
        # is about that entry whatever else the conversation holds - and a single key word is not
        # enough (`_names_the_entry`'s determiner test is what keeps a puppy chat's "house
        # trained" off the first-home entry).
        return True
    if _names_its_own_thing(text, memory) and _agrees_with_its_own_field(item, reading):
        # The line names a thing of its own, so it is judged by its own field and not by the field
        # of the answer before it: "my boiler is making a clunking noise" and then "is it worth
        # getting a smart meter" was turned down as a boiler talk, and the boiler's meter row took
        # the turn. The line still has to agree with its own field, so "should i tip a hotel
        # cleaner" is not handed the money table.
        return True
    return about_the_topic(item, reading)


def _agrees_with_its_own_field(item, reading):
    """True when the entry is in the field the line itself is read as, or in no field at all.

    An entry that carries no topic cannot disagree with the line, and the entry the line's own
    words reach is the entry for it.
    """
    if getattr(item, "topic", None) is None:
        return True
    return about_the_topic(item, reading)


def _the_field_on_the_screen(item, text, reading, memory):
    """True when the line says the entry's own subject and the entry is from the field on screen.

    The field of the answer is a fact about the talk; the topic the line is read as is a guess
    from its words, and one word can carry it into another field: "im skint this month" / "i get
    paid on friday" / "what should i cut first" was read as a question about a body because
    "cut" is a body word, so the money row that answers it was stood down as a field this talk
    never touched and the person got a shrug for the step their own conversation had set up.

    The line has to say one of the entry's own subject phrases, which is what keeps this from
    lifting an entry in over the answer the line really asks for: after "my son is being
    bullied", "how do i help with homework without fighting" says "cut first" to no card and
    keeps the homework answer, while a family card that only shares the single word "fight" with
    it is not the thing the line names.
    """
    if not isinstance(reading, dict) or reading.get("kind") != "question":
        # A statement is not a request for a card: it says where the person stands, and the
        # readers that answer a report are the ones that should take it.
        return False
    last = memory.get("last_answer") if isinstance(memory, dict) else None
    domain = str(last.get("domain") or "") if isinstance(last, dict) else ""
    if not domain or domain != str(getattr(item, "domain", "") or ""):
        return False
    if _last_turn_answered_from_the_field(memory):
        # The turn before this one already gave the field's answer, so the field is on the screen
        # and a question about it is a question about the answer they have: "is 2 hours enough
        # between connecting flights at heathrow" / "no checked bag" is answered by the connection
        # rule with the bag folded in, and the baggage card is a different question.
        return False
    return _says_a_subject_phrase(item, text)


def _last_turn_answered_from_the_field(memory):
    """True when the turn before this one was the field's answer rather than an acknowledgement.

    "im skint this month" / "i get paid on friday" / "what should i cut first" is a chat where the
    middle line only said a detail ("Got it - you get paid on friday"), and the follow-up is the
    field's own question. The connection chat is the other shape: the middle turn *was* the
    answer, so the person is adding to what they were told.
    """
    if not isinstance(memory, dict):
        return False
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return False
    last = memory.get("last_answer")
    reply = last.get("reply") if isinstance(last, dict) else last
    said = turns[-1].get("bot") if isinstance(turns[-1], dict) else None
    if not isinstance(reply, str) or not isinstance(said, str):
        return False
    return _same_answer(reply, said)


def _says_a_subject_phrase(item, text):
    """True when the line says a subject of the entry in so many words, two words or more.

    The first key part of an entry is its subject, and a phrase of it that the person wrote
    ("cut first", "where can i save") is not a pairing two unrelated lines share by accident. A
    single word is, which is why one is not enough here.
    """
    key = getattr(item, "key", ()) or ()
    if not key:
        return False
    first = key[0]
    said = " " + " ".join(re.findall(r"[a-z0-9']+", str(text or "").lower())) + " "
    for option in (first if not isinstance(first, str) else (first,)):
        phrase = " ".join(str(option).lower().split())
        if " " in phrase and (" " + phrase + " ") in said:
            return True
    return False


# What makes a word in a line a thing the line is about, rather than a word that happens to be
# in it: a determiner in front of it. "is it worth getting a smart meter" says "a smart meter",
# and "how long until he is house trained" says no house at all - the house there is the front of
# "trained". One describing word is allowed in between, so "a bigger oven" and "the new boiler"
# count as named.
# The subject of a line does not need a determiner in front of it when the word is the first
# thing the line says: "is brie safe when pregnant" names brie as plainly as "is a brie safe".
# Without this the line answered in one conversation and punted in the next, because after any
# other turn the talk's subject is read against the entry and a bare name was not a name: after
# "is risotto safe to eat when pregnant" the same brie question got the search hedge, and after
# "my back hurts" it was answered. A line that opens with a word the entry is about *is* about
# it. Only one or two auxiliaries are allowed in front of it, which keeps a question that opens
# with an ask ("how long until he is house trained" names no house) out of this.
OPENS_WITH_AN_AUXILIARY = frozenset(
    "is are was were can could should do does did will would".split())

NAMING = re.compile(
    r"\b(?:a|an|the|another|my|our|your|his|her|their|this|that|these|those|one|two|three)\s+"
    # The thing named is any of the next three words, not only the last one the pattern could
    # reach: "can a gerbil have a carrot" was read as naming "a", so the gerbil's own food card
    # stood down as the answer to a talk about a horse's apples and the soup recipe took the
    # carrot. Each word in the window is tested against the entry's own subjects below.
    # A thing named at the end of the line has nothing after it to reach: "what can i do for a
    # cold" said "a cold" and the pattern wanted a word after it, so the entry that answers a
    # cold was not "named" by a line that names nothing else, and after a chat about cold rice
    # the whole turn was a shrug. The last word counts on its own.
    r"((?:[a-z-]+[\s,]+){1,3}|[a-z-]+)")


def _names_the_entry(text, item):
    """True when the line names the thing this entry is about, with a determiner in front of it.

    The entry's own subject words are the test, not the asks in the rest of its key
    ("worth", "get", "buy"): a person saying "a smart meter" has named the meter, and the
    entry is about the meter. This is what tells a real new subject from a word that only sits
    inside another one: the puppy talk's "house trained" names no house, so the first-home
    entry still stands down, and the washing machine talk's "a smart meter" does name one, so
    the meter's entry answers instead of "that's your call, not mine".
    """
    first = getattr(item, "key", ()) or ()
    things = first[0] if first and not isinstance(first[0], str) else ()
    heads = set()
    for option in things:
        words = str(option).lower().split()
        if words:
            heads.add(words[-1].rstrip("s") or words[-1])
    if not heads:
        return False
    for found in NAMING.finditer(" ".join(str(text or "").lower().split())):
        for word in re.findall(r"[a-z-]+", found.group(1)):
            if word.rstrip("s") in heads:
                return True
    said = " ".join(str(text or "").lower().split())
    mine = said.split()
    for _ in range(2):
        if mine and mine[0] in OPENS_WITH_AN_AUXILIARY:
            mine = mine[1:]
    for word in re.findall(r"[a-z-]+", " ".join(mine[:2])):
        if word.rstrip("s") in heads:
            return True
    return False


# How far into a line the word being explained can sit. "what is inflation" and "explain a
# dividend" put it first or second, and the far end is an ask with the longer lead-in ("what does
# a tracker mortgage actually mean"); a word deep in a line about something else is a mention.
DEFINITION_WORD_AT = 6


def _a_definition_of_the_entry(text, item):
    """True when the line asks what one of the entry's own words means ("what is inflation").

    A request to explain a word names that word as plainly as "a smart meter" names the meter,
    but it carries no determiner in front of it, so `_names_the_entry` does not see it and the
    line was read as a follow-up that names nothing of its own. After any other turn the talk's
    subject then stood the entry down - "my back hurts after sitting all day" then "what is
    inflation" got the search hedge, "who invented the telephone" then "what is apr" too - and
    the same line answered in one conversation and punted in another, which is the shape of
    mistake STYLE.md calls out. The question is a new subject, so it is that entry's question
    whatever the talk before it was on.

    The words in front of the subject have to be the ask itself ("what", "whats", "explain",
    "the meaning of"), which keeps "what is the best way to clean a sofa" off the sofa row:
    "best", "way" and "clean" are not words of a request to explain a sofa.
    """
    words = [word.strip(".,!?;:") for word in
             (" ".join(str(text or "").lower().split())).split()]
    if not words or len(words) > DEFINITION_WORD_AT + 1:
        return False
    first = getattr(item, "key", ()) or ()
    things = first[0] if first and not isinstance(first[0], str) else ()
    subject = set()
    for option in things:
        for word in str(option).lower().split():
            subject.add(word.rstrip("s") or word)
    if not subject:
        return False
    for at, word in enumerate(words):
        if (word.rstrip("s") or word) not in subject:
            continue
        before = words[:at]
        if not before or not any(one in EXPLAIN_LEADS for one in before):
            continue
        if all(one in EXPLAIN_FILLER for one in before):
            return True
    return False


# The words a line can carry without naming anything of its own: the hand-over's courtesy and
# its pronouns. "please quiz me then" is the same ask as "quiz me".
HANDOVER_FILLER = frozenset("""
a an the some any another one more then now again please pls just
so ok okay and but also even really
""".split())


def _says_the_ask_whole(text, item):
    """True when the line is nothing but one of the entry's own key phrases.

    The phrases are the entry's own wording, so a line that is exactly one of them is asking for
    this thing and cannot be a detail of whatever the chat was on before. Only phrases of two
    words or more count: a single key word is the loose match `_about_the_talk` is there to
    distrust (a puppy's "house trained" holds "house").
    """
    said = [word for word in WORD.findall(str(text or "").lower())
            if word not in HANDOVER_FILLER]
    if len(said) < 2:
        return False
    for part in getattr(item, "key", ()) or ():
        options = (part,) if isinstance(part, str) else part
        for option in options:
            phrase = [word for word in WORD.findall(str(option).lower())
                      if word not in HANDOVER_FILLER]
            if len(phrase) >= 2 and phrase == said:
                return True
    return False


def _a_why_line_that_names(item, reading):
    """True when a why-line names the subject of the entry it reached."""
    if not isinstance(reading, dict) or "why" not in (reading.get("asks") or ()):
        return False
    return names_its_own_subject(item, reading)


def _names_the_thing_apart_from_the_talk(item, text, subject, reading):
    """True when the line ends on this entry's own subject and says nothing of the talk's.

    A subject the store carries forward is only evidence about the line when the line still
    speaks to it. "i went to the shop today" and then "how do i build endurance" is a new
    question with its own word in it ("endurance", the fitness row's own subject), and the shop
    has no part in it; read against the shop's topic the row stood down and the person got a
    hedge. The word the line ends on is the test, so a loose row still stands down: "how do i
    bake brownies" ends on the brownies, not on "bake", and the row that answers how to start
    baking does not take the turn from the brownie recipe. So does the loud case: "my kids wont
    listen to me" and then "what can i do" names nothing of the music row's at all.
    """
    if not isinstance(reading, dict) or reading.get("kind") != "question":
        return False  # a statement that names a thing loosely is a follow-up about a feeling
    if not names_its_own_subject(item, reading):
        return False
    said = said_topic.words(text)
    if not said:
        return False
    if not _is_about(item, said[-1]):
        return False
    if PRONOUN_OBJECTS.intersection(WORD.findall(str(text or "").lower())):
        return False  # a pronoun is the line pointing back at the talk
    thing = _head_thing(subject)
    if not thing:
        return False
    words = {word.rstrip("s") or word for word in WORD.findall(str(text or "").lower())}
    return (thing.rstrip("s") or thing) not in words


# What a person is choosing between when a taste narrows the choice: a film night, a book, a
# meal, a game. A taste about one of these is a request, because the answer is another thing of
# the same kind; a taste about a cat or a neighbour is a fact about them and nobody is choosing.
CHOICE_KINDS = frozenset("""film films movie movies series show shows programme programmes
    book books novel novels game games music song songs album albums meal meals dinner food
    recipe recipes takeaway takeaway""".split())


def _a_choice_with_one_thing_left_out(text):
    """True when the line narrows a choice ("i dont want a scary film", "i hate horror books")."""
    flat_words = set(re.findall(r"[a-z']+", " ".join(str(text or "").split()).lower()))
    if not flat_words & CHOICE_KINDS:
        return False
    return bool(_refused(text))


# A follow-up leaves its subject out, and that is what makes the rewrite safe: the thing on screen
# is put back where the "it" was. A line that names a thing of its own is not that line. "is a
# burnt toast bad for a dog" and then "is it worth getting a heat pump" became "is the burnt toast
# bad worth getting a heat pump", and the toast card answered a question about a heat pump.
#
# The word that marks the thing is the determiner in front of it: "getting a heat pump" names one,
# "fixing my old laptop" names one, and "is it worth fixing", "how long should i prove it" and
# "and if i get a new one, what should i look for" name none - they say only what to do with the
# thing already on screen, which is exactly what the rewrite is for. So a word after "a", "my" or
# "the" is a thing unless it is one of the words that only describes or counts one ("a new one",
# "the best one", "a bit").
# "its" is left out on purpose: in a chat line it is nearly always "it is" ("its 8 years old"),
# so nothing after it names a thing.
THING_AFTER = frozenset("""a an the my your our their his her this that these those another
    any some every each""".split())
# A determiner behind one of these is where the subject goes, not a thing of its own: "can i take
# it in the pool" is a question about the phone and the pool is the water it might go in, so the
# swimming kit is not the answer and the phone's own card is. "for" and "about" are left out on
# purpose: "a lot for a new one" and "what about the potatoes" both name the thing asked about.
AFTER_A_PLACE = frozenset("""in on at into inside onto unto under underneath near by through
    across behind beside below above outside around round aboard throughout within past
    toward towards via along off upon""".split())
# Words that name no thing even with a determiner in front of them: the ask itself ("no idea
# where to hold it"), a quality ("is that dangerous"), a quantity ("is 300 quid a lot"), and the
# person asking ("what do i wear as a man in his 50s"). A determiner in front of one of these says
# nothing about a new thing in the talk, so the last subject is still what the line means. Without
# the person words, the line named "a man" as its own thing, `_in_context` stepped aside, and the
# outfit question lost the occasion from the line before.
NO_THING_NAMED = frozenset("""idea ideas point points sense question questions matter deal
    problem problems chance chances clue guess guesses example examples option options choice
    choices answer answers lot lots bit bits time times while moment minute second hour day days
    week weeks month months year years difference change reason reasons dangerous risky noisy
    pricey dodgy faulty broken safe spare fortune mint bomb packet ton
    man men woman women person people guy guys lady ladies bloke child kid adult teenager""".split())
# The little verbs a determiner can sit in front of: "any ideas that wont cost a fortune", "the
# one that will last". What follows one of these is not a thing the line names.
_AUXILIARY = frozenset("""wont cant doesnt dont didnt isnt wasnt arent shouldnt wouldnt couldnt
    mustnt will would can could should may might must shall do does did have has had be been
    being is are was were am""".split())
# The endings an adjective has and a thing does not: "is that dangerous", "is it fixable", "is
# that expensive". A word that ends this way describes the thing in the talk rather than naming
# another one, so it is no reason to drop the last subject.
_ADJECTIVE_ENDINGS = ("ous", "ful", "less", "able", "ible", "ive", "ish", "ary")
# A line that asks how much or how many is asking about the thing already in the talk, whatever
# it says: "my boiler needs replacing" then "is 300 quid a lot for a new one" is the price of
# that boiler, and "a new one" is not a thing of its own.
ASKS_A_QUANTITY = re.compile(r"\bhow (?:much|many)\b|\bhow (?:long|far|often)\b", re.I)


def _describes_the_thing(word):
    """True when the word describes a thing rather than naming one."""
    if word in NO_THING_NAMED:
        return True
    return any(word.endswith(ending) and len(word) > len(ending) + 2
               for ending in _ADJECTIVE_ENDINGS)


DESCRIBES_ONE = frozenset("""new old another different same other else more less much many few
    lot lots best better worse easiest hardest first second last next right wrong kind sort type
    way ways thing things stuff one ones bit bits worth safe ok okay normal bad legal possible
    fine allowed hard easy too still someone something anything everything nothing everyone
    everybody nobody anybody""".split())


def _said_in_the_talk(memory):
    """The words of the last few turns, the bot's own included."""
    said = set()
    for turn in (memory or {}).get("turns") or []:
        if not isinstance(turn, dict):
            continue
        for side in ("user", "bot"):
            said.update(WORD.findall(str(turn.get(side) or "").lower()))
    return said


def _already_in_the_talk(word, said):
    """True when the word, its plural or a longer form of it has been said in the talk."""
    if not said:
        return False
    if word in said or word + "s" in said:
        return True
    if word.endswith("s") and word[:-1] in said:
        return True
    return any(one.startswith(word) for one in said)


def _names_its_own_thing(text, memory=None):
    """True when the line names a thing for itself rather than only what to do with the subject.

    "is it worth fixing" is the subject's own question and the rewrite answers it; "is it worth
    fixing my old laptop" names the laptop, so the last subject is not put back into it. A thing
    the talk has already named is not a new subject: after "the washing machine smells" the
    drawer it was answered about is part of the same machine, so "i think its the drawer" is
    still answered about the machine and not as a question about drawers in general.
    """
    said = _said_in_the_talk(memory) if memory is not None else set()
    if ASKS_A_QUANTITY.search(str(text or "")):
        return False
    words = re.findall(r"[a-z0-9']+", str(text or "").lower())
    for index, word in enumerate(words):
        if re.fullmatch(r"\d+(?:s|st|nd|rd|th)?", word):
            continue  # an age or a count is a quality, not a new thing
        if word in DESCRIBES_ONE or word in kinds.VERB_FORMS or word in _AUXILIARY:
            continue
        if word.endswith("e") and word[:-1] + "ing" in DESCRIBES_ONE:
            continue
        if _describes_the_thing(word):
            continue  # a quality or an amount in front of a determiner names no new thing
        if any(word in ("one", "ones") for word in words[index + 1:index + 3]):
            # "a decent one", "a really big one": the word stands in for the thing already in
            # the talk rather than naming a new one, so the last subject is still what it means.
            continue
        if _already_in_the_talk(word, said):
            continue  # a thing this talk has named is not a new subject
        before = words[max(0, index - 2):index]
        if before[-1:] and before[-1] in THING_AFTER:
            if len(before) == 2 and before[0] in AFTER_A_PLACE:
                continue  # "in the pool", "on the plane": where the subject goes, not a new thing
            return True
        # The determiner is the word before the thing ("a heat pump"), or the one before an
        # adjective ("my old laptop", "a proper coat"). The word in the middle has to be an
        # adjective: in "a lot for a new one" the middle is "lot", and "for" is not a thing.
        if (len(before) == 2 and before[0] in THING_AFTER
                and before[1] not in THING_AFTER
                and before[1] not in _AUXILIARY
                and not _describes_the_thing(before[1])):
            return True
    return False


def _the_topic_rules_it_out(item, memory):
    """True when the topic's own words are on the entry's avoid list.

    The knowledge base says which lines an entry is not about, and the topic is a line the
    person said. An entry that stands down for it cannot be the answer to a follow-up that has
    no subject of its own: nothing but the topic could have named it.
    """
    topic = mem.topics.topic_text(memory) if isinstance(memory, dict) else ""
    if not topic:
        return False
    return bool(mem.topics.keeps_away(topic, topic, item))


def _in_context(text, memory, reject=None):
    """The knowledge entry a follow-up is about, by naming the thing it refers to.

    "How long will it take, start to finish?" after a birthday cake is the question "how long
    will the birthday cake take?", which the knowledge base answers. Only tried when the line
    on its own found nothing, so a full question is never rewritten, and a follow-up never
    gets the answer the bot has just given.
    """
    subject = mem.subject(memory)
    # The head of the subject is the thing it names, not its last word: "my sourdough keeps going
    # flat" is about the sourdough, and "flat" is the house word there, so reading the last word
    # alone let the first-home entry take "how long should i prove it". A subject that names no
    # thing at all keeps the old reading, because its last word is all there is.
    thing = _head_thing(subject)
    refused = _refused(text)
    if refused:
        # The line rules a thing out ("anything but a horror"). No entry about that thing is an
        # answer to it whichever rewrite reached it, unless its own reply answers around the
        # refusal ("skip horror and gore"), so the entries are searched past it.
        inner = reject
        reject = (lambda one: _hands_back_the_refusal(one, refused)
                  or (inner is not None and inner(one)))
    understood = memory.get("understood")
    if not isinstance(understood, dict):
        understood = understand(text, memory)
    if understood.get("intent") == "ack":
        return None  # "nice one, thx" is a thank-you, not a question about the dinner
    if _asks_how_to_say_it(text):
        return None  # see SAY_IT: the referring word here is the person or the news
    if not leans_on_a_subject(understood):
        # A statement that names its own subject is not a follow-up: "i have a dog" then "i walk
        # twice a day" was answered with the 10,000-steps entry, "im redecorating the bedroom"
        # then "i have a small budget" got a list of cheap dinners, and "my knee hurts" then "i
        # work on my feet all day" got the foot-ache one. None of those is about the thing they
        # said before; each is news about themselves, and the entry that answered was reached
        # only by putting the earlier subject back in.
        return None
    if _names_its_own_thing(text, memory):
        return None
    fuller = _with_subject(text, memory)
    if fuller.strip() == text.strip() and not _own_thing_words(text, memory):
        # The rewrite hangs the subject on the line as a property of it ("how much is a tv
        # licence for the credit score"), which is only a follow-up when the line brings no
        # thing of its own: see _own_thing_words.
        fuller = _about_subject(text, memory)
    if fuller.strip() == text.strip():
        # A bare ask ("what should I see?") points at the thing with no word at all, so the
        # thing is tried on the end of it and the entry has to be about that thing.
        fuller = _with_bare_subject(text, memory)
        # A line that only narrows the choice ("something funny but not silly", "nothing scary")
        # names no thing of its own; with the thing already being chosen put back on the end it
        # is a line the entries can read, and it reaches the narrowed entry rather than a shrug.
        for rewrite, added, domain in _qualifier_rewrites(text, memory):
            item = _from_rewrite(rewrite, text, memory, reject, added, domain)
            if item is not None:
                if _hands_back_the_refusal(item, _refused(text)):
                    continue  # the line ruled this out: an answer that ignores it is worse than none
                return item
    if (fuller.strip() == text.strip()
            and _the_answer_was_about_the_subject(memory)
            and (not _own_thing_words(text, memory) or ADDING_TO_THE_SUBJECT.match(text))):
        # Nothing to put in front of the subject, so it goes on the end, longest run first.
        # "and what about holidays" names a word of its own, but it is a word added to the thing
        # on screen rather than a new subject: "im thinking of getting a cat" then "what about
        # holidays" is the cat's holiday, and without the tail it was answered with the paid
        # holiday from work.
        skip = set()
        after_used = False
        for fuller in _subject_tails(text, memory, understand(text, memory)):
            reading = understand(fuller, memory)
            after_used = False
            while True:
                item = find(reading, reject=lambda one: one.id in skip
                            or (reject is not None and reject(one)))
                if item is None:
                    break
                skip.add(item.id)
                # The subject was put on the end, so the entry has to be keyed on one of its
                # words, be about the thing the subject names, and its answer has to be one we
                # have not just given.
                if not _named_by(item, subject):
                    continue
                if thing and not _is_about(item, thing):
                    continue
                reply = _payload(item, memory, reading)
                if not reply.strip():
                    continue
                if _said_before(reply, memory):
                    after_used = True
                    continue
                if not _answers_the_figure(text, reply):
                    # The line asks for a figure this entry never states, so the subject put on
                    # the end of it landed on an entry about something else: the next reading
                    # down is no better, and the honest hedge is what the person gets.
                    return None
                if after_used and not _keyed_on_the_line(item, text):
                    # One entry down from the best reading is only worth taking when the line
                    # itself says what it is about: "what do i wear" does, and the outfit entry
                    # is next. Without that the subject's words land on something that is not
                    # the question — "what should i feed him" after a sick dog reached the
                    # car-sickness advice that way.
                    return None
                if _left_out(item, text):
                    return None  # the line names a thing this entry never mentions
                if _the_topic_rules_it_out(item, memory):
                    # The words put on the end came from the topic, so an entry the topic itself
                    # rules out is not this chat's: "what do i need" after "im making a thai
                    # green curry tonight" was read as "what do i need thai green curry" and
                    # handed the what-to-order card, which rules itself out for "making" - the
                    # person cooking tonight was told what to order in. Same test as the one
                    # that guards the widened reading (`topics.keeps_away`), made here because
                    # this is the other way a subject gets put back into the line.
                    return None
                return item
        return None
    if not fuller or fuller.strip() == text.strip():
        return None
    # An entry about something else is passed over rather than taken, so the search goes on to
    # the entry that is about the thing - and to nothing at all if there is none.
    # "Something else" includes another part of the knowledge base: a bare ask leans on the
    # words of the line before it, and one of those words sits in other domains too, so "my
    # kids wont listen to me" and then "what can i do" reached the music entry off the word
    # "listen". A fact this talk never touched is passed over like an entry about something else.
    #
    # A subject read off the person's description also ends in the word they used for the fault
    # ("laptop keep freezing", "freezer frosting"), and the last word of that is the fault, not
    # the thing: "is it worth fixing" after a laptop was answered by the entry about how long
    # food keeps in the freezer, which is about "freezing". The thing a subject names is only a
    # guess, though (a "bathroom tap" is read as the bathroom, and the cleaning entry answers for
    # the bathroom), so both readings are tried and the subject's own words decide between them.
    reading_here = understand(fuller, memory)
    inner = reject
    want = thing or subject
    fits = lambda one: _is_about(one, want) and about_the_topic(one, reading_here)
    about = lambda one: _is_about(one, subject) and about_the_topic(one, reading_here)
    strict = (lambda one: not fits(one) or (inner is not None and inner(one)))
    loose = (lambda one: not about(one) or (inner is not None and inner(one)))
    item = find(reading_here, reject=loose)
    if item is None or not _in_the_subjects_field(item, subject):
        # The line's own reading reached an entry about another field ("a laptop that keeps
        # freezing" is not a question about the freezer), so the entry about the thing the
        # subject names is tried before that one is given.
        better = find(reading_here, reject=strict)
        if better is not None and (item is None or _in_the_subjects_field(better, subject)):
            item = better
    if item is None:
        return None
    # "what kind should I get?", "which brand?" name no thing of their own: the word that looks
    # like one is the ask itself, and the thing they ask about is the last subject.
    own = None if mem.KIND_ASK.search(text) else _own_thing(understand(text, memory))
    if own and not _is_about(item, own):
        return None  # the line names its own thing: it is not about the last subject
    if _left_out(item, text):
        return None  # the line names a thing this entry never mentions
    reply = item.reply
    if isinstance(reply, (list, tuple)) or callable(reply):
        # Handed back with the reading of the written-out line, so an entry that words itself
        # from the line names the thing: "is it worth repairing" after a freezer that has iced
        # up said "A machine is worth repairing" when the entry had the freezer in front of it.
        # When that answer is one the person has already heard, the line's own words get the
        # choice instead: "is that enough" after the child-and-veg advice came back as the same
        # advice, where the five-a-day figures were the answer to what was asked.
        held = reading_here
        if _said_before(_payload(item, memory, reading_here), memory):
            here = understand(text, memory)
            own_words = _payload(item, memory, here)
            if own_words.strip() and not _said_before(own_words, memory):
                held = here
        return item, held
    if _said_before(reply, memory):
        return None  # the same answer again is no answer
    if not _answers_the_figure(text, reply):
        return None  # the answer names no figure and the line asks for one
    return item, reading_here


def _from_rewrite(fuller, text, memory, reject, added="", domain=None):
    """The entry a rewritten line reaches, when it is about the last subject and is not a repeat.

    `added` is the word the rewrite put in ("film"): an entry can be about the thing the chat is
    choosing between without carrying the subject's own word, so either one makes it the entry.
    """
    item = find(understand(fuller, memory), reject=reject)
    if item is None:
        return None
    if domain is not None and item.domain != domain:
        return None  # the word reached an entry in another field: not the thing being chosen
    if not (_is_about(item, mem.subject(memory)) or (added and _is_about(item, added))):
        return None
    own = _own_thing(understand(text, memory))
    if own and not _is_about(item, own):
        return None  # the line names its own thing: it is not about the last subject
    reply = item.reply
    if isinstance(reply, (list, tuple)) or callable(reply):
        return item  # the phrasing is chosen later; a repeated answer is caught below
    if _said_before(reply, memory):
        return None  # the same answer again is no answer
    return item

KEEPS = re.compile(r"\b(?:keep|keeps|keeping|fridge|freezer|freeze|lasts?)\b", re.I)
# A figure is what "how long does that keep" asks for: a number with a unit of time on it.
FIGURE = re.compile(r"\b(?:\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|a couple of|a few)"
                    r"(?:\.\d+)?\s*(?:-|to\s+\d+\s*)?(?:hour|hours|day|days|week|weeks|month|"
                    r"months|year|years)\b", re.I)
# Advice to keep something out of the fridge is for a raw food in a cupboard, never for a dish
# that has just been cooked.
_NOT_THE_FRIDGE = re.compile(
    r"\b(?:never\s+(?:in\s+)?the\s+fridge|not\s+(?:in\s+)?the\s+fridge|out\s+of\s+the\s+fridge"
    r"|room\s+temperature|dry,\s+dark|in\s+a\s+cupboard|in\s+the\s+cupboard)\b", re.I)


# A line that asks how to store or keep a food is a keeping answer in itself, so the follow-up
# "how long does that keep" asks for that same fact again, not for the general fridge table.
# Only the doing word the subject came from can say so: "how do i store bread" leaves "store
# bread", where "how long do i boil an egg" leaves no storing word at all.
STORING = frozenset("""
store stores stored storing keep keeps kept keeping
""".split())


def _asks_storing(memory):
    """True when the line before was a how-to-store (or how-to-keep-fresh) question."""
    words = (mem.subject(memory) or "").split()
    return bool(words) and words[0] in STORING


# The storing word a how-to line leaves in the subject is not part of the thing: "how do i keep
# herbs fresh" leaves the subject "keep herb fresh", so the keeping rewording read "how long does
# that keep" as already naming its subject and the follow-up got nothing. The herb is the thing.
# Only a storing word comes off: "how do i cook rice" has to keep its "cook", because cooked rice
# keeps a day and dry rice keeps months, and the cooking is what tells them apart.
def _keeping_thing(memory):
    """The thing a keeping follow-up is about, without the storing word the how-to line asked with."""
    words = (mem.subject(memory) or "").split()
    while words and (words[0] in STORING or words[0].rstrip("s") in STORING):
        words.pop(0)
    return " ".join(words)


def _the_plan_keeps(understood, memory):
    """The keeping fact a dish the conversation planned says for itself: "it keeps 3 days".

    "im making a beef stew" then "how long will it keep" is a question about that stew, and the
    plan has its own answer for it. The general cooked-food line is the answer for a dish nobody
    named, and a worse one for a dish we can name.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    words = {str(word).lower() for word in (understood.get("words") or ())}
    if dishes.ask_kind(understood) != "keep" or not words & {"it", "that", "this", "them", "they"}:
        return None
    if _own_thing(understood):
        return None  # the line names a food of its own, and that food has its own answer
    return dishes.follow_up(memory, understood)


def _keeping_entry(text, memory, thing=None, storing=False):
    """The entry that says how long the topic keeps, when the knowledge base has one.

    "how long does that keep" after a boiled egg is about the eggs, and the eggs have their own
    answer (a week in the fridge). Only an answer that really talks about keeping counts, so a
    recipe or a cupboard line cannot answer it.
    """
    fuller = _with_subject(text, memory, thing)
    if fuller.strip() == text.strip():
        fuller = _about_subject(text, memory)
    if fuller.strip() == text.strip():
        return None
    reading = understand(fuller, memory)
    item = find(reading)
    if item is None or not _is_about(item, mem.subject(memory)):
        return None
    reply = _reply_of(item, reading, memory)
    if not isinstance(reply, str) or not reply.strip():
        return None
    # An answer counts when it talks about keeping, or when it is the answer just given to a
    # storage question: "how do i keep herbs fresh" answers with the jar and the damp paper and
    # no figure at all, and it is still what the person asked to hear again. A recipe or a
    # cupboard line that was not the last answer never gets in this way.
    # The answer just given counts only after a how-to-store line, where it *is* the keeping
    # answer to say again. Anywhere else the previous answer may be a cooking time: after "how do
    # i roast a chicken" the roast timetable is about the chicken and was just said, and it is
    # still the wrong answer to "and how long does that last".
    said_already = bool(storing and _said_before(reply, memory))
    if not KEEPS.search(reply) and not said_already:
        return None
    # The answer has to be about keeping the thing that was cooked. After "what can i make with
    # mince and onions" the subject names both foods, and the onion entry is about raw onions in
    # a cupboard ("never the fridge") - the opposite advice to a cooked dish. A dish of two or
    # more foods is kept by the cooked-food rule, not by one ingredient's cupboard rule.
    subject = mem.subject(memory)
    if subject and len(cooking.ingredients(understand(subject, memory))) > 1:
        # A dish of two or more foods is kept by the cooked-food rule, whatever one ingredient's
        # own answer says. After "what can i make with chickpeas and spinach" the subject names
        # both foods, and the spinach entry answers for leaves in a salad drawer ("About 5 days"),
        # which is the raw ones, not the pan that just came off the hob.
        return None
    # The answer just given was this one, and it is still the answer: "how do i store potatoes"
    # then "how long does that keep" asks for the figure that is in it. Standing aside here hands
    # the line to the general fridge table, which answers a raw loaf with "keep it covered in the
    # fridge" - the opposite of the bread answer just given. So the keeping answer is said once
    # more rather than a different one being said instead - but only the part of it that answers
    # the question: "how do i store eggs" then "how long does that keep" wants "three weeks", not
    # the shelf in the door and the temperature of the fridge as well.
    if said_already:
        figures = [part.strip() for part in SENTENCE.split(reply) if FIGURE.search(part)]
        if figures:
            return " ".join(figures)
    return reply


def _in_this_conversation(reject, reading):
    """The caller's veto, and one of its own: a fact from another part of the knowledge base.

    A bare ask leans on the words of the line before it, and one of those words sits in other
    domains too: "my kids wont listen to me" and then "what can i do" reached the music entry
    off the word "listen", and the parent was offered an album. A fact the conversation never
    touched is passed over, so the search goes on to the domain it is actually about.
    """
    def veto(item):
        if not about_the_topic(item, reading):
            return True
        return bool(reject is not None and reject(item))
    return veto


def _in_bare_context(text, memory, reject=None):
    """The entry a bare ask reaches once the thing it is about is put on the end of it.

    Kept apart from `_in_context` because it hands back the reading of the written-out line:
    the entry phrases itself from that reading ("In Rome: the Colosseum ..." needs the city in
    the line), where the pronoun and property rewrites are read from the line as it came in.
    """
    if _names_its_own_thing(text, memory):
        return None
    fuller = _with_bare_subject(text, memory)
    if fuller.strip() == text.strip():
        return None
    reading = understand(fuller, memory)
    item = find(reading, reject=_in_this_conversation(reject, reading))
    if item is None or not _is_about(item, mem.subject(memory)):
        return None
    reply = getattr(item, "reply", None)
    if not (isinstance(reply, (list, tuple)) or callable(reply)):
        if _said_before(reply, memory):
            return None  # the same answer again is no answer
    return item, reading


def _reply_of(item, reading, memory):
    """What this entry would say, without keeping it, so a reply can be read before it is given."""
    reply = getattr(item, "reply", None)
    if callable(reply):
        try:
            reply = reply(memory, reading)
        except Exception:
            return ""
    elif isinstance(reply, (list, tuple)):
        reply = " ".join(one for one in reply if isinstance(one, str))
    return reply if isinstance(reply, str) else ""


A_FIGURE = re.compile(r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b",
                      re.I)


NUMBER_IN_TEXT = re.compile(r"\d+(?:\.\d+)?")


def _figures_of(said):
    """The numbers a sentence carries, as words a set can hold."""
    return set(NUMBER_IN_TEXT.findall(flat(said or "")))


def _new_figure(fresh, before):
    """Whether the answer has a figure the one before it did not.

    A line that adds a figure to the answer just given is worth a second answer only when the
    figure changes it: the figure they gave that was already the one used ("its 2 kilos" after
    the timing for a 2kg bird) leaves the paragraph saying what it already said.
    """
    return bool(_figures_of(fresh) - _figures_of(before))


def _adds_a_figure(text):
    """Whether the line brings a number for the thing under discussion, and asks nothing.

    A number on its own is not a line: "it says 1.8 kilos", "the gauge says 0.5", "we are six".
    An ask with a number in it ("how long for 2 kilos") is read for an entry as usual.
    """
    said = flat(text)
    if not said or "?" in said:
        return False
    return bool(A_FIGURE.search(said))


# A line that changes a figure the chat already has, rather than one that adds a figure to it: the
# sum on it replaces the sum before it, so the two are never the same question ("what if i can only
# do 100" adds a rate, "make it 150 instead" moves one).
A_PUT_RIGHT = re.compile(r"\b(?:make\s+(?:it|that|them)|instead|rather\s+than|i\s+meant|no\s+wait|"
                         r"change\s+(?:it|that|them)|put\s+(?:it|that)\s+(?:to|up|down)|"
                         r"bump\s+(?:it|that)|let'?s\s+say)\b", re.I)


def _a_figure_put_right(text):
    """True when the line moves a figure the chat already gave ("make it 150 instead")."""
    text = str(text or "")
    return bool(A_PUT_RIGHT.search(text) and re.search(r"\d", text))


def _without_the_figures(line):
    """The earlier line with its sums taken out, so only its words are handed on."""
    return " ".join(re.sub(r"[£$]?\b\d[\d,.]*\b", "", str(line or "")).split())


def _the_entry_asked_again(text, memory):
    """The entry that answered last, asked this line with its own subject still in it.

    A line that only asks for a property ("how long will that take", "what temperature?") names
    nothing of its own, so the entry is the one the last answer came from - but the entry cannot
    see the ask when the subject is missing from the line ("how long will that take" carries no
    word of a credit card). Read with the line it leans on in front, the entry answers the ask
    it has an answer for, and when it has nothing to add it says the same answer again: that is
    not a new reply, so this returns None and the rest of the module goes on as before.
    """
    record = _last_answer(memory)
    if not record:
        return None
    entry_id = record.get("id")
    if not entry_id:
        return None
    item = None
    for candidate in all_entries():
        if getattr(candidate, "id", None) == entry_id:
            item = candidate
            break
    if item is None:
        return None
    turns = memory.get("turns")
    turn = record.get("turn")
    if not isinstance(turns, list) or not isinstance(turn, int) or not 0 <= turn < len(turns):
        return None
    said = turns[turn] if isinstance(turns[turn], dict) else {}
    line = str(said.get("user") or "").strip()
    if not line:
        return None
    # The earlier line is put in front so the entry can see what the ask is about ("how long will
    # that take" carries no word of a credit card). A figure the line puts right is the one thing
    # that must not come with it: read with the rate from two turns back in front of it the entry
    # answered with both - "£2,500 at £200 a month" / "make it 150 instead" -> "£150 at £200 a
    # month is a single month at that rate", a pot nobody named made out of the rate they were
    # changing. The words still go in front, so "the car is" is still what the sum is for.
    earlier = _without_the_figures(line) if _a_figure_put_right(text) else line
    reading = understand(earlier + " " + text, memory)
    fresh = _payload(item, memory, reading)
    if not isinstance(fresh, str) or not fresh.strip():
        return None
    if flat(fresh) == flat(record.get("reply") or ""):
        return None  # the same answer again is not an answer to this line
    new_part = _the_part_a_longer_variant_adds(fresh, record.get("reply"))
    if new_part is not None:
        return new_part
    return fresh


def _the_part_a_longer_variant_adds(fresh, said):
    """What a longer variant of the answer on the screen adds to it, or None.

    The entry asked again with the line it answered still in front of it can pick a longer
    variant, and the paragraph the person has just read goes out again with a sentence stuck on
    the end: "how far should i go first" then "and how often" in a running chat came back as the
    whole training-order paragraph plus "The best order is the one you will keep doing twice a
    week." The answer is on the screen, so only the added sentences are owed here - STYLE.md
    rules out the same words twice in a row, and a friend asked a second question about the same
    answer says the part that answers it.
    """
    said = flat(said)
    mine = flat(fresh)
    if not said or not mine.startswith(said):
        return None
    rest = mine[len(said):]
    if not rest.startswith(" "):
        return None  # a word the flat form cuts in half is not the answer said again
    words = len(said.split())
    added = " ".join(str(fresh).split()[words:]).strip()
    if len(added.split()) < 3:
        return None  # a word or two on the end is the same answer, not a new part of it
    return added


def _payload(item, memory, reading):
    """The entry's reply, chosen the way the composer will choose it, or "" if it declines."""
    reply = getattr(item, "reply", None)
    if callable(reply):
        reply = reply(memory, reading)
    elif isinstance(reply, (list, tuple)):
        reply = pick(reply, memory)
    return reply if isinstance(reply, str) else ""


def _the_sentence_owed(text, reply, memory):
    """The sentence the entry behind this reply owes the line, or None when it owes none.

    The entry is the one the line's own reading reaches, and the reply has to open on that
    entry's own words: a card narrowed to one of its sentences ("Do not stop suddenly on your
    own: ..."), a card wrapped as the answer already given ("Same answer, and it covers this:
    ..."), and a reply from another row are all left as they are, because the sentence the row
    owes belongs in front of the card it belongs to.
    """
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(understood, dict):
        return None
    try:
        item = find(understood)
    except Exception:  # noqa: BLE001 - a sentence is never worth a turn
        return None
    if item is None or not getattr(item, "lead", None):
        return None
    said = getattr(item, "reply", None)
    if not isinstance(said, str):
        try:
            said = _payload(item, memory, understood)
        except Exception:  # noqa: BLE001
            return None
    plain = " ".join(str(said or "").split())
    here = " ".join(str(reply or "").split())
    if not plain or not here:
        return None
    at = here.find(plain[:50])
    if at != 0:
        # the card is not what this reply says: it has been narrowed to one of its sentences, or
        # wrapped as the answer already given ("Same as before: ...", "As I said: ..."), or the
        # reply is another row's altogether. Only a reply that opens on the card gets its verdict,
        # because the sentence a row owes belongs in front of the card and not in front of a frame
        # around it: "It is not an emergency. As I said: A suddenly louder exhaust ..." answers a
        # line the person asked before with a verdict they have already been given.
        return None
    return item.lead


# A line that asks for a stand-in wants the missing thing named back: "no double cream, what can
# i use" is answered in cream's own terms ("milk with a knob of butter ... thickens much like
# cream"), and an answer that says cream is the answer, not a confident recipe about the thing
# that is not in the house. The refusal check below is for a preference ("anything but a
# horror"), so a swap line is never asked to leave the word out - and a swap line that says "no
# double cream" is read as refusing "double", the modifier, which no answer is about at all.
STAND_IN_WORDS = frozenset("""
substitute substitutes substitution swap swaps swapping replace replaces replacing replacement
""".split())
# Only the shapes that ask for a stand-in in those words: "i ran out of butter" and "i havent
# got any milk" already read as a swap and never reach the refusal check at all, so a "no double
# cream" line is the only one that needs this gate to open.
STAND_IN_PHRASES = ("what can i use", "what do i use", "what should i use", "what else can i use",
                    "what can i substitute", "in place of",
                    # The short way of asking, after a taste rather than a shortage: "i hate
                    # broccoli what can i have instead" was neither a stand-in nor a refusal the
                    # code knew, so the swap row for broccoli was handed back and the line got a
                    # search hedge.
                    "instead", "what can i have", "what could i have", "what else can i have",
                    # The other way of asking it, which needs no stand-in at all: "i dont like
                    # garlic can i leave it out" is the same swap question, and the swap row's
                    # "leave it out - nothing collapses" was handed back as a refusal answer.
                    "leave it out", "leave them out", "leave out", "skip it")


# A line that names what it wants a stand-in for is answered by that name and nothing else:
# "anything but cream, what can i use instead of milk" rules cream out and asks about milk, so
# the cream entry must keep out of it. Only the bare "no <thing>" opening, asking what to use in
# its place, is the shape where the missing thing is the subject of the line.
STAND_IN_TARGET = re.compile(r"\b(?:instead of|in place of|substitute for|swap (?:it )?for)\b",
                             re.I)


def _wants_a_stand_in(reading):
    """True when the line asks what to use in place of the thing it says it has none of."""
    if not isinstance(reading, dict):
        return False
    clean = " ".join(str(reading.get("clean") or "").split()).lower()
    if not clean or STAND_IN_TARGET.search(clean):
        return False
    asked = any(phrase in clean for phrase in STAND_IN_PHRASES)
    if not asked:
        words = reading.get("words")
        if not isinstance(words, (list, tuple)):
            words = clean.split()
        asked = any(str(word).lower() in STAND_IN_WORDS for word in words)
    if not asked:
        return False
    # "no double cream, what can i use" - the refusal is the line's own subject, so the entry
    # that says the thing back is the answer. "anything but cream" still goes through the check.
    #
    # A taste opens the line the same way a lack does: "i hate broccoli what can i have instead"
    # is the swap question put by someone who will not eat the food rather than by someone who
    # has run out of it, and the swap row that answers it was being handed back because the
    # refusal check only knew the shape a missing ingredient has.
    return bool(REFUSE_OPEN.match(clean) or REFUSE_WISH.match(clean)) \
        and not REFUSE_CHOICE.match(clean)


def _a_swap_row(item):
    """True for the table's stand-in rows, whose answer is the swapped ingredient by design.

    The gate above belongs to them and to nothing else: "no alcohol what can i drink instead"
    has the shape of a swap and is a question about alcohol, so the row that says alcohol back
    - the sleep one - has to keep its refusal. A row without the prefix simply keeps the check,
    which costs a stand-in at worst and never a confident answer about something else.
    """
    return str(getattr(item, "id", "") or "").startswith("swap-")

# --- a present with a price on it ----------------------------------------------------
# A gift question that names an amount and the same question without one are two questions: "what
# should i get my dad for his 60th, under 40 quid" has to come back with things that cost that
# much. So does the limit given as a follow-up ("what about under 40 quid", "anything cheaper"),
# which names no present word at all and used to reach the shrug. The picks themselves are data in
# shopping.py (INTEREST_GIFTS, PRESENT_BANDS), so this only reads the limit and the person.
PRICE_LIMIT = re.compile(
    r"\b(?:under|below|less than|no more than|not more than|up to|max(?:imum)?(?: of)?|"
    r"budget(?: of| is| around| about)?|spend(?: up to)?)\s*\u00a3?\s*(\d{1,4})(?:\.\d\d?)?\b",
    re.IGNORECASE)
# "nothing over 20 quid", "not over a tenner", "no more than 15 pounds": the ceiling said as a
# thing the present must not go above. Without it the amount is read ("20 quid") and the rest of the
# line is left over, so the limit is never applied and the person gets the whole price range again.
PRICE_NOT_OVER = re.compile(
    r"\b(?:nothing|not|no|nowt)\s+(?:more\s+than|over|above|past)\s*\u00a3?\s*(\d{1,4})(?:\.\d\d?)?\b",
    re.IGNORECASE)
PRICE_BARE = re.compile(r"\b(\d{1,4})(?:\.\d\d?)?\s*(?:pounds?|quid|\u00a3)\b",
                        re.IGNORECASE)
# "over 20 quid then" is the floor side of the same words, and it is not a ceiling: with `over` in
# `LIMIT_ONLY` the line reads as a limit of its own, and `PRICE_BARE` then turns "over 20 quid"
# into a ceiling of 20. The words only say a limit when nothing else in the line says which way
# the limit goes, so a floor with no negation in front of it and no "under"/"up to" beside it
# stands the reading down.
PRICE_OVER = re.compile(r"\b(?:over|above|more\s+than|past)\s*\u00a3?\s*(\d{1,4})(?:\.\d\d?)?\b",
                        re.IGNORECASE)
PRICE_WORDS = (("a tenner", 10), ("tenner", 10), ("a fiver", 5), ("fiver", 5))
CHEAPER = re.compile(r"\b(?:cheaper|more affordable|less expensive)\b", re.IGNORECASE)
# The cheapest test for "this line may hold a limit": a digit, a tenner or a fiver, or a word for
# cheaper. Every line that reaches the reader above has to pass it, so it stays a plain search.
LIMIT_SHAPE = re.compile(r"\d|\btenner\b|\bfiver\b|\bcheaper\b|affordable", re.IGNORECASE)
# What a line that *only* sets a limit is made of: the ask and the limit, nothing else. Anything
# the line names for itself (a dad, a wedding, a book) takes it out of this shape.
LIMIT_ONLY = frozenset("""
    nothing not no over above more than nowt
    what about anything something cheaper cheap please then so ok okay could we go bit a an the is
    my budget max maximum under below less than more no not up to spend pounds pound quid tenner
    fiver that this it for on do i can you any if but else maybe just around roughly sort kind of
    thing things price prices cost costs money how much will would should get buy gets go for
    """.split())
# The same interest said two ways: "garden" and "gardening" are one row of the table, and a line
# that says both does not ask for two presents.
INTEREST_ALIASES = {"garden": "gardening", "plants": "gardening", "allotment": "gardening",
                    "tackle": "fishing", "angling": "fishing", "fish": "fishing",
                    "books": "reading", "book": "reading"}


def _price_limit(text):
    """(the amount in pounds or None, whether the line asked for something cheaper)."""
    if not isinstance(text, str) or not text.strip():
        return None, False
    flat = " ".join(text.lower().split())
    cheaper = bool(CHEAPER.search(flat))
    if (PRICE_OVER.search(flat) and not PRICE_NOT_OVER.search(flat)
            and not PRICE_LIMIT.search(flat)):
        # The line says a floor and nothing that makes it a ceiling: "over 20 quid then" is a
        # present above 20 pounds, not a budget of 20.
        return None, cheaper
    match = PRICE_NOT_OVER.search(flat) or PRICE_LIMIT.search(flat) or PRICE_BARE.search(flat)
    if match:
        try:
            return int(float(match.group(1))), cheaper
        except (TypeError, ValueError):
            return None, cheaper
    for phrase, amount in PRICE_WORDS:
        if phrase in flat:
            return amount, cheaper
    return None, cheaper


# A line with a price on it is a present question when it says so, or when it is a limit on a
# present already being discussed. "my budget is 30 pounds" on its own says neither and is money.
GIFT_WORD = re.compile(r"\b(?:present|presents|gift|gifts)\b")


def _only_a_limit(text):
    """True when the line is the limit and nothing else: "what about under 40 quid"."""
    words = [word for word in WORD.findall(" ".join(str(text or "").lower().split()))
             if not word.isdigit()]
    return bool(words) and all(word in LIMIT_ONLY for word in words)


def _a_gift_entry(reading):
    """The present entry this line is about, if it is about one."""
    item = find(reading)
    return item if str(getattr(item, "id", "")).startswith("gift-") else None


def _a_gift_just_answered(memory):
    """The present entry one of the last few lines reached, while the chat is still on it."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return None
    for turn in reversed(turns[-3:]):
        said = str((turn or {}).get("user") or "") if isinstance(turn, dict) else ""
        if not said:
            continue
        item = _a_gift_entry(understand(said, memory))
        if item is not None:
            return item
    return None


def _asks_what_to_give(reading):
    """True when the line is asking what to give somebody, with a person to give it to.

    The same reading the gift rows ask before they answer (topics.gift_ask), so one rule decides
    for the rows and for the band: "get her" and "what should i buy my husband" are presents,
    "cheap running shoes under 40 pounds" and "get him tested" are not.
    """
    from ..understanding import topics as present_reading
    return present_reading.gift_ask(reading)


def _the_interests(text, memory, item):
    """The hobbies this present is for, as the table names them: said in the chat, or in the key.

    "he likes fishing and gardening" a turn before the limit is what makes "what about under 40
    quid" a question about a fisherman, so the words are read off the last few lines as well as
    off this one, and off the entry's own key when the line named the hobby in the first place.
    """
    from ..knowledge import shopping  # a local import: the module's own import line is shared
    said = []
    lines = []
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if isinstance(turns, list):
        lines = [str((turn or {}).get("user") or "") for turn in turns[-3:]
                 if isinstance(turn, dict)]
    for line in lines + [str(text or "")]:
        for word in WORD.findall(line.lower()):
            name = INTEREST_ALIASES.get(word, word)
            if name in shopping.INTEREST_GIFTS and name not in said:
                said.append(name)
    if said:
        return said
    for part in getattr(item, "key", ()) or ():
        for word in (part if isinstance(part, (list, tuple, set)) else (part,)):
            name = INTEREST_ALIASES.get(str(word).lower(), str(word).lower())
            if name in shopping.INTEREST_GIFTS and name not in said:
                said.append(name)
    return said


def _the_entry_reply(item, memory, reading):
    """What the entry says, without being said: the price it already names, or an empty string."""
    reply = getattr(item, "reply", None)
    try:
        said = reply(memory, reading) if callable(reply) else reply
    except Exception:  # noqa: BLE001 - an entry that cannot answer says nothing
        return ""
    return said if isinstance(said, str) else ""


def _the_present_with_a_price(text, reading, memory):
    """A present at the price the line gives, or the limit on the present just suggested.

    Only a line that is a present question with a limit on it, or a limit on a present question a
    line or two back, reads here; everything else passes, because an amount is in half the lines
    ever typed ("my budget is 30 pounds" on its own is the money answer).
    """
    money, cheaper = _price_limit(text)
    if money is None and not cheaper:
        return None
    item = _a_gift_entry(reading)
    if item is not None and "\u00a3" in _the_entry_reply(item, memory, reading):
        # An entry that already prices itself answers better than a band does: "what present for
        # a wedding, budget 60" wants the "about 50 pounds is usual" sentence, not an experience.
        return None
    only_a_limit = _only_a_limit(text)
    interests = _the_interests(text, memory, item)
    if item is None:
        if only_a_limit:
            item = _a_gift_just_answered(memory)
            if item is None:
                return None
        elif not GIFT_WORD.search(str(text or "").lower()) \
                and not (interests and _asks_what_to_give(reading)):
            # The words "gift" and "present" are how the order is usually put, and the rows that
            # price a present are reached through them: "what should i get my wife who likes
            # reading for under 100 pounds" names the person, the hobby and the limit and not
            # the noun, so the band was refused and the line fell to the love-language card,
            # which says a book and never mentions the hundred. A line the reading calls a gift
            # ask with a hobby in it is the band's question however it says it.
            return None
    if item is not None and not only_a_limit and not interests \
            and str(getattr(item, "id", "")) != "gift-generic":
        # A present for a named person, with no hobby named, is that person's row: the age picks
        # for a 7 year old, the "buy into it - secateurs for a gardener" answer for a sister. A
        # band fixes the money and forgets the person, so it says a thermos and a book to a
        # question about a child. The band answers where it is better: the limit on its own, a
        # limit as a follow-up to the present just discussed, a hobby it can price, and a line
        # that names no recipient at all.
        return None
    from ..knowledge import shopping
    if money is None:
        return shopping.present_less(interests)
    return shopping.present_within(money, interests)

# A line that asks what something costs wants a figure. It shares words with the entry about
# the thing, which answers the thing instead: "how much roughly to fix" after a noise in the
# brakes reached the entry that says when the noise happens, and a confident diagnosis is not a
# price. The entry states money when it is the answer to this line.
# A line that asks how to do something is a request, not a recall of a fact the store keeps.
_HOW_TO_SHAPES = (r"\bhow\s+(?:do|can|should|would|could|to)\b|\bhow to\b"
                # "what do i do about my budget" is the same request as "how do i budget",
                # and the recall gate above would otherwise hand it to the store. Only the
                # "about my/the" form: "what do i do for a living" is still the store's.
                r"|\bwhat\s+(?:do|can|should|shall)\s+i\s+do\s+about\s+(?:my|our|the|this|that)\b")
HOW_TO = re.compile(_HOW_TO_SHAPES)

MONEY_SAID = re.compile(
    r"£|\$|€|\bquid\b|\bpounds?\b|\bcosts?\b|\bcosting\b|\bprice[ds]?\b|\bpric(?:ey|ier)\b"
    r"|\bexpensive\b|\bcheap(?:er|est)?\b|\bfree\b|\bcharges?\b|\bfees?\b|\bpay\b"
    r"|\b\d+\s?(?:p|quid|pence)\b", re.I)
# The words that make "how much" a price rather than a quantity: an adverb, an auxiliary, a
# preposition or a pronoun, then the verb the price is for ("how much to fix it"), or nothing at
# all ("how much roughly?"). "how much rice" and "how much water" name what is measured, and an
# entry about the food is right to answer those.
PRICE_FILLER = frozenset("""
roughly approximately approx about around maybe usually normally possibly just exactly to for it
that this them those be is are was were do does did would will should can could i you we they he
she my our me us a an the
""".split())
PRICE_VERBS = frozenset("""
fix repair replace get buy hire rent install book cost costs charge pay spend make do take put
sort service deliver fit mend
""".split())


def _asks_a_price(text):
    """Whether the line asks what something costs, rather than how much of a thing there is.

    "how much roughly to fix", "how much for a service", "how much would that be" want a
    figure; "how much rice" and "how much water" want a quantity, and a recipe answers those.
    """
    low = flat(text)
    if re.search(r"\bhow much (?:does|do|is|are|will|would|should|can|could)\b.*"
                 r"\b(?:cost|pay|price|spend|budget)\b|\bwhat(?:'s| is) the price\b"
                 r"|\bhow much for\b", low):
        return True
    found = re.search(r"\bhow much\b(.*)$", low)
    if not found:
        return False
    for word in re.findall(r"[a-z']+", found.group(1)):
        if word in PRICE_FILLER:
            continue
        return word in PRICE_VERBS
    return True


def _names_what_it_wants_priced(text):
    """Whether the price question says what it is for, rather than leaving it to the chat.

    "how much does it cost to fix a dripping tap" names the tap, so the entry about the tap is
    still an answer when nothing states money. "how much roughly to fix", "how much for it" and
    "how much would that be" name nothing but the thing already said, and the entry that fits
    those words is about the thing, not about the price of it: a diagnosis of a noise in the
    brakes is not a price for repairing it.
    """
    found = re.search(r"\bhow much\b(.*)$", flat(text))
    if not found:
        return False
    for word in re.findall(r"[a-z']+", found.group(1)):
        if word in PRICE_FILLER:
            continue
        if word in PRICE_VERBS:
            continue
        return True
    return False


# The line given when the entry a follow-up reaches is the answer already on the screen. The
# answer is about the subject and not the place it was asked about - the ants advice never says
# either room - so it holds where they asked about as well: a person who asks "what about the
# bathroom" gets something useful instead of a search hedge. But the paragraph again word for word
# is the bot repeating itself, so the part of it they have not read is what comes back, under a
# lead-in that names where they asked about.
SAME_WHERE = "The same goes for {thing}: {said}"
# "in the bathroom", "at home", "on the shelf" would read "the same goes for in the bathroom": the
# place is named by the phrase, and the lead-in already has its own preposition. The same is true
# of every other preposition a detail can open on, and they are not only places: "and for cooking"
# after the camping list came back as "The same goes for the for cooking: ...", and "what about
# with kids" as "the with kids". A detail is the noun the person named, and the preposition in
# front of it is theirs, not part of its name.
LEAD_PREPOSITION = frozenset("""in at on inside into for with about to of from by without after
                                before like using around near over under between""".split())
# The most a line handed back this way can be: one line of the answer, not another paragraph.
MOST_SAME = 220


# "bathroom" on its own reads "the same goes for bathroom": the thing is named with the word
# that says which one, and a line that already has one keeps it ("my freezer", "the oven door").
DETERMINER = frozenset("the a an my our your his her its their this that these those".split())


# An elided follow-up reads a bare "again" as the thing it names - "what about again" - and
# "The same goes for the again: iron it while it is still damp" is a sentence nobody wrote. The
# line that asks for the answer a second time names no thing for the answer to be handed to.
NOT_A_THING = frozenset("again pardon sorry eh huh".split())
# Everything a line can be made of and still be only the ask to hear the answer again. The line
# reaches the detail reading folded - "pardon?" arrives as "what about pardon" - so the wrapper
# words are here beside the ask itself, and a line made of nothing else names no part of the
# answer to say it again for.
ONLY_THE_ASK = NOT_A_THING | frozenset("""
    what about again say said come then please it that this you was just now one more time
    """.split())

# The lead-in above puts the new thing in a noun slot ("the same goes for the bathroom", "the same
# goes for the snails"), which is right for a thing and wrong for a sentence. A line that opens on
# a pronoun is a sentence about the subject in hand, not the name of a new one: "hes a spaniel"
# after the lead question came back as "The same goes for the hes a spaniel: Train the lead as a
# stop-and-go game", and the same shape waits behind "its a big dog", "we have two kids" and
# "nothing too heavy". Those keep the answer and lose the frame.
CLAUSE_START = frozenset("""
he hes she shes it its i im ive ill id you youre youve we weve were they theyre theyve
that thats this these those there nothing something anything everything nobody somebody
anybody everybody
""".split())
# The answer, said again for what they told you, with no thing for the frame to name.
SAME_PLAIN = "Then the same holds: {said}"


def _same_where_they_asked(text, said):
    """The part of that answer the new thing has not been given yet, or "" for none left."""
    thing = swap.thing(text)
    if not thing:
        return ""
    # Only the words that ask for the answer again: there is no thing here to hand it to.
    if all(word in NOT_A_THING for word in re.findall(r"[a-z']+", thing.lower())):
        return ""
    # A line judging the answer as doable names no thing to hand it to either: "sounds doable"
    # came back as "The same goes for the sounds doable: ...", which is the judgement said back
    # as if the person had named a part of the job. Asked of the composer's own reading, so the
    # two cannot disagree about whether the line is about the answer or about a thing.
    from ..compose import fallback
    if fallback.reads_as_a_judgement(text):
        return ""
    # A sentence about the thing in hand is not the name of a new one, so it keeps the answer and
    # loses the "the same goes for the ..." frame: a pronoun is never how a thing is named.
    clause = bool(re.findall(r"[a-z']+", thing.lower())[:1]
                  and re.findall(r"[a-z']+", thing.lower())[0] in CLAUSE_START)
    words = thing.split()
    if len(words) > 1 and words[0].lower() in LEAD_PREPOSITION:
        words = words[1:]
    if (not clause and words[0].lower() not in DETERMINER
            and not (len(words) == 1 and words[0].endswith("ing"))):
        # "the same goes for the cooking" is one determiner too many: an activity named by its
        # gerund is the name of the thing, not a countable one of them.
        words = ["the"] + words
    thing = " ".join(words)
    # The room named in the thing, which is what a sentence about another room is read as.
    room = next((word for word in re.findall(r"[a-z']+", thing.lower())
                 if word.rstrip("s") in ROOMS), "")
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", str(said or "")) if part.strip()]
    asked = {word.rstrip("s") or word for word in re.findall(r"[a-z']+", thing.lower())}
    # The first sentence is usually the thing to do, so it is tried first: the method is what a
    # person asking about the new thing needs, and handing over only the aside is worse than a
    # hedge. "how do i get rid of slugs / what about snails" gave "Encourage birds and frogs, and
    # water in the morning" while "go out after dark with a torch" - still true of snails - went
    # unsaid.
    for part in parts:
        for piece in _the_method_in(part):
            if len(piece.split()) < 5 or len(piece) < 30 or len(piece) > MOST_SAME:
                continue
            if not _holds_where_they_asked(piece, asked):
                continue
            line = _mid_sentence(piece.rstrip(" ."))
            line = _room_they_asked_about(line, asked, room)
            if not line.endswith((".", "!", "?")):
                line += "."
            # The answer follows a colon, so its opening capital is the only thing making it a
            # sentence of its own: "The same goes for the bathroom: use a mid-sheen..." is the
            # one sentence STYLE.md asks for.
            if clause:
                return SAME_PLAIN.format(said=_small_letter(line))
            return SAME_WHERE.format(thing=thing, said=_small_letter(line))
    return ""


def _mid_sentence(part):
    """The line with its opening capital taken off, when it is only a capital because it began.

    A sentence that starts "The usual hiding places are the door seal" carries the same words in
    lower case later on, which is how this knows the first word is not a name: "Paris is the one"
    keeps its capital, because nothing later in the line says "paris".
    """
    tokens = re.findall(r"[A-Za-z']+", part)
    if len(tokens) < 2 or not part[0].isupper():
        return part
    if tokens[0].lower() in [word.lower() for word in tokens[1:]]:
        return part[0].lower() + part[1:]
    return part


# The rooms and outside places an answer can be handed to another of. A part of a house is the
# same kind of place as another part of a house: advice about a bedroom's damp holds in a bathroom,
# and advice about a fridge's door seal holds nowhere but a fridge. It is not a topic list - it is
# what tells "somewhere else in the house" from "some other thing".
ROOMS = frozenset("""room kitchen bathroom bedroom loo toilet ensuite hall hallway landing lounge
living dining garage shed garden conservatory study nursery attic loft cellar basement porch patio
balcony utility laundry cloakroom downstairs upstairs flat house home""".split())


# The places a sentence can name, for telling a line that holds anywhere from one written about
# somewhere else. Wider than ROOMS: a lawn, a path and a flowerbed are different places although
# none of them is a room.
NAMED_PLACES = ROOMS | frozenset("""lawn grass flowerbed patio path gravel drive yard plot
allotment greenhouse""".split())


def _holds_where_they_asked(part, asked):
    """Whether a sentence of the earlier answer is about the place asked about, or about none.

    "on a lawn, feed and mow it properly ... on a patio, path or gravel, hoe or flame them young"
    was handed to a flowerbed under "The same goes for the flowerbed:", which says the opposite of
    what the sentence says. A sentence that names another place is only handed over when that
    place is another of the same kind - a bedroom's advice in a bathroom.
    """
    named = {word.rstrip("s") or word
             for word in re.findall(r"[a-z']+", str(part or "").lower())} & NAMED_PLACES
    if not named or named & asked:
        return True
    return bool(named & ROOMS) and bool(asked & ROOMS)


def _the_method_in(part):
    """The sentence, and the part of it after a colon when it has one.

    A long opening sentence of an advice paragraph often carries the reason first and the thing
    to do after a colon ("Condensation comes from warm wet air hitting cold surfaces ...: use the
    extractor fan, open a window for 10 minutes a day"). The whole sentence is too long to hand
    over, and the clause after the colon is the part a person can act on.
    """
    pieces = [part]
    if ": " in part:
        pieces.append(part.split(": ", 1)[1])
    return pieces


def _room_they_asked_about(line, asked, room):
    """The line with another room in it read as the one they asked about.

    A sentence that holds anywhere in a house can still name where it was first written: the
    dehumidifier line of the condensation answer says "in a bedroom that gets it badly", and
    handed to a bathroom under "The same goes for the bathroom:" it says the opposite of what
    the lead-in claims. The room they asked about is the room in the sentence when it is the
    same kind of place, so the sentence is about the room they asked about.
    """
    if not room or not asked:
        return line
    found = {word.rstrip("s") or word
             for word in re.findall(r"[a-z']+", str(line or "").lower())} & ROOMS
    others = found - asked
    if len(others) != 1:
        return line
    other = others.pop()
    name = room.rstrip("s") or room
    return re.sub(r"\b%s(s?)\b" % re.escape(other), lambda m: name + (m.group(1) or ""),
                  line, flags=re.I)


def _a_place_of_the_same_kind(earlier, text):
    """True when the place they now ask about is another of the kind the answer was about.

    The condensation advice is about a bedroom, so it is about a bathroom too and can be handed
    over with the bathroom named. The fridge answer is about a fridge, which is not a room, so
    "what about in the garage" is a different thing and gets the honest hedge rather than a
    paragraph about door seals.
    """
    if not isinstance(earlier, dict):
        return False
    asked = {word.rstrip("s") or word
             for word in re.findall(r"[a-z']+", (swap.thing(text) or "").lower())}
    keys = {str(word).lower() for word in (earlier.get("keys") or ())}
    return bool(asked & ROOMS) and bool(keys & ROOMS)


def _a_place_they_asked(text):
    """True when the follow-up names a place with a place's own preposition.

    "and in the bathroom", "what about under the sink". A bare thing ("what about the cake",
    "and what about a turkey") is not one: the answer about a table is not the answer about a
    cake, and saying it again with the cake's name in front would be worse than a hedge.
    """
    words = (swap.thing(text) or "").split()
    return bool(words) and words[0].strip("?.!,;:").lower() in swap.PREPOSITION


def _key_terms(item):
    """Every phrase the entry is keyed on, however deeply its key is nested.

    An entry's `key` is a tuple of groups, but some entries are written with the phrases in the
    tuple itself (`('slugs', 'snails', ('keep', 'stop', ...))`), so iterating it once gives the
    letters of a phrase rather than the phrase. Walking it to the strings is what both readers
    below need.
    """
    def walk(node):
        if isinstance(node, str):
            return [node]
        try:
            children = list(node)
        except TypeError:
            return []
        out = []
        for child in children:
            out.extend(walk(child))
        return out
    return walk(getattr(item, "key", None) or ())


def _written_for(item, thing):
    """True when one of the entry's own key words is the thing, or covers it.

    The ants entry is keyed "ants" against "kitchen, bait, cupboard, sugar", and the fridge entry
    is keyed "fridge, freezer" against "smell, stink". A follow-up that changes one of those
    words ("what about the bathroom", "what about the freezer") reaches the same entry, and the
    entry was written with both of them in mind.
    """
    if item is None:
        return False
    words = set(re.findall(r"[a-z']+", str(thing or "").lower()))
    if not words:
        return False
    for term in _key_terms(item):
        own = set(re.findall(r"[a-z']+", term.lower()))
        if own and (words <= own or own <= words):
            return True
    return False


def _more_than_the_thing(item, rest):
    """True when a key of the entry also names something in the rest of the question.

    "The smell in the shed" finds the entry for shedding weight, which is keyed "shed" - one word
    shared by chance, and its answer is about eating. The sink entry reached by "and under the
    sink" after the shower is keyed "sink" and "clean", and the question was a how-do-i-clean
    one. One shared word is enough when it is the thing being asked about; a key word that the
    rest of the question also says is what tells the two apart.
    """
    if item is None:
        return False
    rest_words = set(re.findall(r"[a-z']+", str(rest or "").lower()))
    if not rest_words:
        return False
    for term in _key_terms(item):
        own = set(re.findall(r"[a-z']+", term.lower()))
        # A key term made only of question words ("how") says nothing about the subject.
        if own and own <= rest_words and not own <= swap.STOP:
            return True
    return False


def _about_the_rest_of_the_question(item, question, new):
    """True when the entry's own subject words are in the question besides the new thing.

    An entry is reached by a question about the thing the follow-up named, and its reply names
    the subject, not the room the subject is in: the ants entry answers "ants in the bathroom"
    with "wipe the trail away ... do not spray the line they are following", which never says
    either room. Reading the reply for the words of the question turned that answer down and
    left the person with a search hedge, when the answer they already have is the answer.

    The entry's own subject words say what it is about, and the rest of the question (the words
    that are not the new thing) is what the follow-up kept asking about.
    """
    key = getattr(item, "key", None) or ()
    subject = key[0] if key else ()
    if not subject:
        return False
    new_words = re.findall(r"[a-z']+", str(new or "").lower())
    if not new_words or new_words[0] not in swap.PREPOSITION:
        # Only a place is read this way. A thing swapped into a question that named none asks a
        # different question - "what should i make thats not too fiddly" / "and what about the
        # cake" reached the party-food entry that answered the turn before - and an entry about
        # the old subject is not an entry about the cake.
        return False
    asked = set(re.findall(r"[a-z']+", str(question or "").lower()))
    left = asked - set(new_words)
    for term in subject:
        words = re.findall(r"[a-z']+", str(term or "").lower())
        if words and all(word in left for word in words):
            return True
    return False


def _offer(reader, memory, reading):
    """The first entry the reader offers whose reply stands, and that reply.

    An entry can fit the words and still turn the line down, because the conversation says the
    line is about something else: "how long do i cook it for", after a packet of mince, is a
    question about the mince. A lower entry that can answer should still get its turn rather
    than the whole turn shrugging.
    """
    text_here = reading.get("text") if isinstance(reading, dict) else ""
    names_it = _names_what_it_wants_priced(text_here)

    def price_asked(held):
        return _asks_a_price((held or {}).get("text") if isinstance(held, dict) else text_here)

    declined = set()
    refused = _refused(text_here)
    # The first entry the price filter turned down, kept in case nothing below it states money.
    fallback = None
    # The same for a line that asks for the words: the first entry whose reply says nothing to
    # say is kept for the end, so a line with no "what to say" card still gets the answer its own
    # words reached rather than a shrug.
    # Only for the line the person just sent: a reader that puts the last turn's subject back
    # into a follow-up hands back a reading whose plain words are that earlier line, and a card
    # declined there is a card declined for a question nobody has asked yet ("what can i say to
    # her" after a nervous-daughter turn stepped from the school answer to the weaning one).
    here = str((reading or {}).get("plain") or "").strip().lower()
    now = str((memory or {}).get("understood", {}).get("plain") or "").strip().lower() \
        if isinstance(memory, dict) else ""
    words_wanted = (_the_ask_is_for_words(reading)
                    if not here or not now or here == now else False)
    words_fallback = None
    # How many cards the wording rule may turn down before the answer its own words reached is
    # given after all. A line asks for the words, not for a walk through the card index: with no
    # limit, "what can i say to her" (read on the whole chat, so the subject is "my daughter")
    # stepped from the school answer past three cards to how to start a baby on solids.
    words_declines = 0
    while True:
        got = reader(lambda one: one.id in declined)
        if got is None:
            kept = fallback or words_fallback
            if kept is None:
                return None, None
            item, held = kept
            reply = _payload(item, memory, held)
            return (item, reply) if reply.strip() else (None, None)
        # A reader that wrote the line out to reach the entry hands back the reading it used,
        # because an entry can phrase itself from it ("In Rome: ..." needs "rome" in the line).
        item, held = got if isinstance(got, tuple) else (got, reading)
        if price_asked(held):
            reply = _payload(item, memory, held)
            if reply.strip() and not MONEY_SAID.search(reply):
                # The line asks for a price and this entry states none: it is answering the
                # thing, not the question. The entry below may price it. If none does, an answer
                # that is still new is better than a shrug - "how much does it cost to fix a
                # dripping tap" is answered by naming the washer, and that entry states no
                # money - but an answer the bot has already given is not, which is the noise in
                # the brakes said back a second time.
                if names_it and fallback is None and not _said_before(reply, memory):
                    fallback = (item, held)
                declined.add(item.id)
                continue
        if not (_wants_a_stand_in(reading) and _a_swap_row(item)) \
                and _hands_back_the_refusal(item, refused):
            # The line rules this thing out ("anything but a horror"), and the answer says
            # nothing about leaving it out: a confident answer about the very thing the person
            # refused is worse than a shrug, so the next entry gets the turn.
            declined.add(item.id)
            continue
        reply = _payload(item, memory, held)
        if (reply.strip() and refused
                and not (_wants_a_stand_in(reading) and _a_swap_row(item))
                and _is_about(item, refused)
                and not _says_it_leaves_it_out(reply, refused)):
            # An entry that phrases itself from the line cannot be asked about the refusal before
            # it is written, so it is asked afterwards: "i dont like sad films" reached the sad
            # films and was told "For a good cry: Manchester by the Sea...", which is the one
            # answer the line had ruled out. Only a reply that says nothing about leaving the
            # thing out is handed back, and the entry below may still answer.
            declined.add(item.id)
            continue
        if (reply.strip() and words_wanted and words_declines < 3 and held is reading
                and not _said_before(reply, memory)
                and not SAID_OUT_LOUD.search(reply)
                and not _puts_it_to_someone(reply)):
            # The line asks for the words and this card answers the thing they are about: "how do
            # i tell my flatmate to do the dishes" was answered with how to wash up, and "ordered
            # a pizza and it came freezing cold, what can i say" with how long a pizza freezes.
            # The card below it may be the one that says it; when none does, the answer here is
            # still better than a shrug, so the first of them is kept for the end. A reply that
            # already says how to put it to somebody is left alone: see `_puts_it_to_someone`.
            if words_fallback is None:
                words_fallback = (item, held)
            declined.add(item.id)
            words_declines += 1
            continue
        if reply.strip():
            return item, reply
        declined.add(item.id)


KEEPING_FROM_THE_ANSWER = "keeping-from-the-answer"


def _keeping_in_the_answer_before(memory):
    """The sentence of the answer just given that says how long the thing in hand keeps, or "".

    "i want to make stock from the chicken carcass" ends "it keeps 4 days in the fridge or 3
    months frozen". Two steps of the same job later ("how long do i simmer it", "and how long do
    i cool it for" - the second one answered with that whole sentence again) the person's "how
    long does it keep" was answered from the general cooked-food table: a card about cooked food,
    raw meat and rice, with neither the stock in it nor the 3 months. The table is the answer for
    a thing we cannot name; here the answer just given already carries the figure, and a wide card
    must not be handed over in place of it.
    """
    said = str(mem.last_bot(memory) or "").strip()
    if not said:
        return ""
    for sentence in SENTENCE.split(said):
        sentence = sentence.strip()
        if not (cooking.speaks_of_keeping(sentence) and KEEPS_A_FIGURE.search(sentence)):
            continue
        # The lead-in says what to do with it ("Strain it, cool it fast and"), not how long it
        # keeps, and the whole sentence just said reads as the bot repeating itself: the person
        # gets the keeping clause, which is what they asked for.
        keep_at = KEEPING_CLAUSE.search(sentence)
        if keep_at and keep_at.start() > 0:
            lead = sentence[:keep_at.start()].rstrip(" ,;:-")
            if lead and ("," in lead or " and" in lead.lower()):
                sentence = sentence[keep_at.start():]
                sentence = sentence[:1].upper() + sentence[1:]
        if sentence.strip() == said.strip():
            continue  # the same words again are no answer: leave it to the entry below
        return sentence.strip()
    return ""


# Where the keeping clause starts in a sentence: "Strain it, cool it fast and it keeps 4 days".
KEEPING_CLAUSE = re.compile(r"\b(?:it|they|that|this|these|those)\s+(?:keeps?|lasts?|freez(?:e|es))\b",
                            re.I)
# A keeping sentence with a length of time in it. The keeping table's own phrase ("the label's
# once-opened line beats any general rule") says nothing about how long anything keeps.
KEEPS_A_FIGURE = re.compile(
    r"\b\d+\s*(?:-|to)?\s*\d*\s*(?:day|days|week|weeks|month|months|year|years)\b"
    r"|\ba (?:day|week|month|year)\b|\bcouple of (?:days|weeks|months)\b", re.I)


def _keeping_reader(reading, memory):
    """The reader for a line that asks how long something keeps rather than how long it cooks.

    "how long does a cooked chicken last" reached the roast timetable, and "how long does a cooked
    ham last" a shrug, though the knowledge base has an answer that says how long it keeps. The
    keeping answer is the one the line asked for, so it is looked for first; when there is none,
    the line is answered as it was before.
    """
    if not cooking.keeping_ask(reading):
        return lambda reject: find(reading, reject=reject)

    own = _own_thing(reading)

    def keeps(of, reject):
        def not_about_keeping(one):
            if reject(one):
                return True
            return not cooking.speaks_of_keeping(_payload(one, memory, of))
        return find(of, reject=not_about_keeping)

    def in_the_fridge(of):
        # "how long does a roast keep" names the keeping but not where, and the answer that holds
        # the figure is keyed on the fridge. This is the same line with the obvious place on it.
        cold = dict(of)
        cold["clean"] = (str(of.get("clean") or of.get("text") or "") + " in the fridge")
        cold["words"] = list(of.get("words") or ()) + ["in", "the", "fridge"]
        return cold

    def with_the_thing(of):
        # The thing the conversation is on goes into the line before the fridge does. "what can i
        # make with eggs" then "how long do they keep" is a question about the eggs, and the eggs
        # have their own keeping answer (three weeks on the box); the general fridge table is the
        # answer for a thing we cannot name, and a worse one for a thing we can. Only an entry
        # that speaks of keeping counts, so a recipe or a cupboard line cannot get in this way.
        said = str(of.get("text") or of.get("clean") or "")
        fuller = _with_subject(said, memory)
        if not fuller.strip() or fuller.strip() == said.strip():
            return None
        return understand(fuller, memory)

    def reader(reject):
        found = keeps(reading, reject)
        if found is None:
            thing = with_the_thing(reading)
            if thing is not None:
                found = keeps(thing, reject)
        if found is None and not own and mem.last_module(memory) == "answers":
            # The thing in hand said how long it keeps in the answer just given, and this line
            # names no food of its own: that figure is the answer, and the wide table is not.
            kept = _keeping_in_the_answer_before(memory)
            if kept:
                return lookup_entry(KEEPING_FROM_THE_ANSWER, ("keep", "keeps", "last", "lasts"),
                                    kept)
        if found is None and mem.last_module(memory) == "answers":
            # The general table answers a thing we cannot name, so there has to be a thing:
            # "that" points at the answer before, and when the turn before was not an answer
            # about anything ("hey" then "how long does that keep") there is nothing to keep.
            # The subject is no use as the test - the words of the line are the gist of it, so
            # a bare "how long does that keep" makes its own subject "keep".
            cold = keeps(in_the_fridge(reading), reject)
            # The general table is the answer for a thing we cannot name, never for a food the
            # line names: "how long does vinegar last" is not "cooked food keeps 3 to 4 days".
            # A food with an answer of its own was found above, so this is the last resort.
            if cold is not None and own and not _is_about(cold, own):
                cold = None
            found = cold
        return found or find(reading, reject=reject)

    return reader


# A temperature in an answer, and the number in it: "190C", "180 degrees".
DEGREES = re.compile(r"\b(\d{2,3})\s*(?:c\b|degrees)", re.I)


# A thing that has been cooked, and the words a line uses for what is left of it. The plan's
# keep fact is about leftovers, so it is only the answer when there is something cooked to have
# left over: "half a roast chicken left over" yes, "raw chicken in the fridge" no.
COOKED_THING = frozenset("""
cooked cook roast roasted bake baked fry fried grill grilled boil boiled poach poached steam
steamed leftover leftovers made reheat reheated rest rested
""".split())


def _cooked_thing(memory):
    """True when the thing the conversation is on has been cooked already."""
    return bool(set((mem.subject(memory) or "").split()) & COOKED_THING)


def _the_plan_for(text, memory, understood):
    """The dish plan's answer to a part question the last answer did not state, or None.

    "what temperature should the oven be?" after a cake's baking time names no subject: the
    time answer has no heat in it, and no other entry is about the cake. The dish the
    conversation is on says the heat itself, so the plan answers for it.
    """
    if not _the_plan_answers_this(memory):
        return None
    answer = dishes.follow_up(memory, understood)
    if isinstance(answer, str) and answer.strip():
        return answer
    return None


# A keeping answer says how long the food lasts in the fridge; it is not how long the pan
# takes. Both halves are needed before the guard fires, and neither alone is rare: "keeps" and
# "days" are in half the kitchen's answers, and "cook" is in half its questions.
COOK_VERB = re.compile(r"\b(?:cook|boil|bake|roast|fry|grill|simmer|steam|reheat|air-?fry|"
                       r"poach|braise|pressure cook)\b", re.I)
KEEPS_ANSWER = re.compile(r"\b(?:keeps?|lasts?|freezes?|fridge|freezer|cooler)\b", re.I)
KEEPS_ASK = re.compile(r"\b(?:keep|keeps|keeping|last|lasts|lasting|fridge|freezer|freeze|"
                       r"frozen|leftover|leftovers|left over|store|stored)\b", re.I)
# Heating up leftovers is the third clock: not the pan's time, not the fridge life, and the
# keeping answer has no reheat time in it. "how long do i reheat it for" after a keeping answer
# was handed the storage figure ("2 days."), which is the one number that must not be used.
PRONOUN_OBJECTS = frozenset(("it", "them", "that", "this", "one", "these", "those", "him",
                             "her", "his", "hers", "the rest", "some"))
REHEAT_ASK = re.compile(r"\b(?:re-?heat|re-?heating|heat (?:it|them|that|this) up|heat up|"
                        r"warm (?:it|them|that|this) up|warm up|microwave)\b", re.I)
# What is true of every leftover, and the only thing that is: the test is piping hot right
# through, not a number of minutes, because the time is the portion's size and the shape of the
# food. Said as a range so it is useful, and with the once-only rule because that part is food
# safety rather than preference.
REHEAT_REPLY = ("No fixed time: reheat it until it is piping hot right through, not just warm. "
                "A portion takes 2 to 4 minutes in the microwave with a splash of water, "
                "stirring halfway; a whole joint or a big tub needs 15 to 25 minutes covered in "
                "the oven at 180C. Piping hot means steaming all the way through, and reheat it "
                "once only.")


def _names_another_food(understood, subject):
    """True when the line names a thing of its own that is not the food we are on.

    The pronoun line ("how long do i reheat it for") names nothing, and the food named again
    ("how long do i cook pasta for") names the same thing the keeping answer did - both are
    follow-ups about this food. "how long do i reheat a pizza" is not: pizza is a new question,
    and the entry that knows pizza is where it belongs.
    """
    if not subject:
        return False
    words = set(subject.split())
    for ent in understood.get("entities") or []:
        if not isinstance(ent, dict) or str(ent.get("type") or "") == "person":
            continue
        text = str(ent.get("text") or "").lower().strip()
        if not text:
            continue
        # The understanding names the action as a thing: "how long do i reheat it for" comes
        # back with "reheat" among its entities, and reading that as a second food stood this
        # guard down on the one line it exists for, leaving the keeping figure ("2 days.") as
        # the answer. An action is not a food of its own, and neither is a pronoun.
        if text in PRONOUN_OBJECTS or COOK_VERB.search(text):
            continue
        if words & set(text.split()):
            return False
        return True
    return False


# The subject the store keeps after a keeping question carries the ask's own verb ("cooked rice
# keep", "cooked chicken keep"), which is not part of the food. Written into the follow-up it made
# "how long does the cooked rice keep take to cook", which reaches nothing, so the keeping figure
# stayed as the answer to a question about the pan. The food is what is left without it.
KEEPING_WORD = re.compile(r"^(?:keep|keeps|keeping|kept|last|lasts|lasting|store|stored|"
                          r"storage|freeze|freezes|frozen|fridge|freezer|long)$", re.I)


def _the_food_named(subject):
    """The subject without the keeping words in it: "cooked rice keep" -> "cooked rice"."""
    return " ".join(word for word in str(subject or "").split()
                    if not KEEPING_WORD.match(word))


def _a_cooking_ask_after_a_keeping_answer(understood, memory):
    """The method entry's answer to a "how long do i cook it for" after a keeping answer.

    "how long does cooked chicken last" then "how long do i cook it for" said "3 days": the
    keeping sentence was handed back as if it were a cooking time, because the follow-up names
    no food and the last answer is what the conversation is on. The keeping question and the
    cooking question are about the same food, so the line read with the food put back in ("how
    long do i cook the chicken for") reaches the entry that knows the method, and that entry
    answers. The food may have no method entry (mince, gammon), and then this says nothing.
    """
    line = str(understood.get("clean") or understood.get("text") or "")
    if not line or not COOK_VERB.search(line) or KEEPS_ASK.search(line):
        return None  # a keeping question of its own: "how long do i cook it for the fridge"
    # The keeping answer is still the one on the table after a "thanks": an acknowledgement says
    # nothing about the food, so "thanks" / "how long does it take to cook" was reading the
    # bot's "Glad that helped." and missing the keeping answer it has to stand down for.
    said = str((mem.answer_in_hand(memory) or {}).get("bot") or "")
    if not said or not KEEPS_ANSWER.search(said):
        return None  # nothing about keeping in the last answer, so not this
    # A follow-up that names a different food is a new question even when a keeping answer is on
    # the table: "how long do i reheat a pizza" after "how long does cooked chicken last" is
    # about pizza, and the entry that knows pizza answers it. Only a follow-up on the same food
    # (the pronoun, or the food named again) is this guard's business.
    subject = str(mem.subject(memory) or "").lower()
    if _names_another_food(understood, subject):
        return None
    if REHEAT_ASK.search(line):
        # Heating is a third clock, and it is the same question whatever the food is: what
        # matters is piping hot right through, not a time taken from the fridge life. The
        # keeping answers each say their own version of it in a sentence that also carries
        # keeping facts ("and eat it cold within 3 days"), so the reply is written once here
        # rather than cut out of them.
        return REHEAT_REPLY
    # The food may be named again in the follow-up ("how long do i cook pasta for", "how long do
    # i fry bacon"), and then the line itself is the reading: adding the subject would only make
    # a sentence nobody typed. When it is the pronoun that stands for the food, the line is
    # written out with the food put back in.
    food = _the_food_named(mem.subject(memory)) or None
    fuller = _with_subject(line, memory, about=food)
    if fuller.strip() == line.strip():
        fuller = _about_subject(line, memory, about=food)
    readings = [fuller, line] if fuller.strip() != line.strip() else [line]
    # The subject the memory keeps is the food as the keeping answer named it ("cooked rice"),
    # and "how long do i cook the cooked rice for" reads the keeping word as a dish of its own.
    # The method question is about the food, so the keeping adjective comes out of it.
    readings = [re.sub(r"\b(cooked|leftover|left over|roast|roasted)\s+(?=[\w' ]+\bfor\b)", "",
                       reading, count=1) for reading in readings]
    # What the line asks for is the pan's time, and a keeping entry can be reached by the same
    # words ("how long do i cook it for" landing on the rule about cooked food). A keeping answer
    # states days, not minutes, so one that states no length of time is only the fallback: the
    # answer with a time in it is the one this line wants.
    fallback = None
    for written in readings:
        reading = understand(written, memory)
        item, answer = _offer(lambda reject: find(reading, reject=reject), memory, reading)
        if item is None or not isinstance(answer, str) or not answer.strip():
            continue
        if answer.strip() == said.strip():
            continue  # the same keeping paragraph: nothing better to say about the pan
        if _minutes_in(answer):
            return answer
        fallback = fallback or answer
    return fallback


def _the_plan_answers_this(memory):
    """True when the last answer was about cooking the dish, so its plan is the answer here.

    "how long?" after "what temperature for a cake" wants the plan's time. "how long?" after
    "how long does chicken last in the fridge" does not: that conversation is about keeping
    food, and the plan would say how long to roast it - a wrong answer, and worse than the
    search hedge it replaced. The plan is about one oven at one heat, so it only answers while
    the answer we are on was about that oven: a fridge-life answer has no heat in it, and an
    air fryer answer has a different one.
    """
    said = str(mem.last_bot(memory) or "")
    if "air fryer" in said.lower() or "airfryer" in said.lower():
        return False
    return bool(DEGREES.search(said) or mem.has_time(said))


def _the_plan_said_again(understood, text, memory):
    """The same property asked again about the plan we just gave, said as a repeat.

    A bare ask ("what temperature?" after "what temperature for a cake") repeats the answer it is
    about without repeating the line, so it is counted by the sentence we gave and not by the
    line that asked for it. The answer comes whole, with the lead-in a repeated answer gets, and
    this runs before the guard that sends a figure we do not have to a search: the plan is not
    another entry guessing, it is the answer we already gave."""
    if not (mem.asks_only(understood) and mem.last_module(memory) == "answers"):
        return None
    if not _the_plan_answers_this(memory):
        return None
    plan = dishes.follow_up(memory, understood)
    if not isinstance(plan, str) or not plan.strip():
        return None
    said = 0 if pairing(text) else _answer_said(plan, memory)
    if said >= 3:
        return AGAIN_HELP.format(reply=plan)
    if said:
        # The same ask again gets the sentence of the plan that answers it, not the whole plan
        # twice: "can i make the frosting the day before" is answered by the plan's sentence
        # about the day, and the keeps-sentence in front of it is the same paragraph again.
        return AGAIN[said - 1].format(reply=_repeat_short(plan, text, memory))
    return None



# While an emergency is open, a bare statement is the person filling in what happened, and the
# nouns in it are not the subject of the turn: after "i can't breathe properly", "it started this
# morning when i was in the garden" is when it began, not a garden to plan, and it was answered
# with "take one bed, not the garden: strim or mow the lot". A question is still a question
# ("should i use my inhaler"), and the guard lapses with the case, so it only covers the turn
# right after the safety reply.
def _filling_in_an_emergency(understood, memory):
    """True when the line only adds detail to a safety reply the bot has just given."""
    if not isinstance(memory, dict):
        return False
    said = [turn for turn in mem.recent(memory, 1) if isinstance(turn, dict)]
    if not said or said[-1].get("module") != "safety":
        return False
    if not isinstance(understood, dict):
        return True
    # "when i was in the garden" is read as an ask for a time, so the asks are no sign of a
    # question: what the person said, not what the line contains, is what the guard goes on.
    signals = understood.get("signals") or {}
    return not (understood.get("kind") == "question" or signals.get("question_mark"))


def _usable(item, reading, memory):
    """False when the answer needs something the line says the kitchen has not got."""
    # An answer about the appliance itself is not a cooking instruction: "my oven wont heat up"
    # says the oven is not working, and the element diagnosis is the answer to it, not a recipe
    # that needs an oven. Only a dish is held out by what the kitchen has not got.
    if getattr(item, "fault", False):
        return True
    return not cooking.unusable(_reply_of(item, reading, memory), reading)


def _next_usable(item, reading, memory):
    """The best entry that answers the same line without what the line has not got."""
    kept = [one for one in all_entries() if one is not item and _usable(one, reading, memory)]
    return find(reading, entries=kept) if kept else None


def _without_names(reading):
    """The same reading with a place word the line uses as a name taken out.

    "my mate paris is visiting for the weekend" is a friend coming over, and "my nan is called
    florence" is a name: the city guide and the city weather are answers to a different question.
    The understanding engine says which words those are, so every domain gets the same answer.
    """
    names = [name for name in (reading.get("person_names") or ()) if isinstance(name, str)]
    if not names:
        return reading
    drop = set(names)
    narrowed = dict(reading)
    words = reading.get("words")
    if isinstance(words, list):
        narrowed["words"] = [word for word in words
                             if not (isinstance(word, str) and word.lower() in drop)]
    clean = reading.get("clean")
    if isinstance(clean, str) and clean:
        narrowed["clean"] = " ".join(word for word in clean.split()
                                     if word.lower().strip(".,!?;:") not in drop)
    return narrowed
# A line that hands over text and asks for a tone wants that text rewritten: "make this sound
# less angry: i want my deposit back now" is a writing job, not a question about deposits, and
# the entry that answers deposits used to claim it and answer the wrong thing - the tenancy
# rules instead of a softer sentence. So these lines are recognised first, the rewrite is built
# from the text itself (so it works on anything someone pastes in), and no entry gets the turn.
REWORD_ASKS = (
    "make this sound", "make that sound", "make it sound", "make mine sound",
    "make this a bit", "make this more", "make this less", "make that more", "make that less",
    "make it more", "make it less", "can you make this", "could you make this",
    "can you make it", "could you make it", "rewrite this", "rewrite that", "rewrite it",
    "can you rewrite", "could you rewrite", "reword this", "reword that", "reword it",
    "can you reword", "rephrase this", "rephrase that", "can you rephrase",
    "how do i word this", "how would you word", "how should i word", "how do i phrase this",
    "word this better", "say this more", "say it more", "say that more", "say this less",
    "say it less", "put this more", "put it more", "so it sounds", "so it doesnt sound",
    "so it doesn't sound", "so it sounds", "so that it sounds", "make this shorter",
    "make it shorter", "shorter please", "cut this down", "make this briefer",
    "make it a bit", "make this a little", "make it a little", "make this sound a bit",
    # A message pasted in to be checked is the same job as a rewrite: "can you check this sounds
    # all right: Hi Sarah, ..." used to be shrugged at, and then the follow-ups about it had
    # nothing to work on either.
    "check this sounds", "check that sounds", "check how this sounds", "check this reads",
    "does this sound", "does this read", "check this email", "check this message",
    "check this text", "check this note", "check this letter", "look over this",
    "check over this", "read this over", "read it over", "does this come across",
)

# A line that hands text over to be checked rather than told to change its tone. The answer says
# what is right about the sentence instead of pretending it was an angry one.
CHECK_ASKS = (
    "check this", "check that", "check how this", "does this sound", "does this read",
    "look over this", "check over this", "read this over", "read it over",
    "does this come across", "sounds all right", "sounds alright", "sound all right",
)

# The tone the line asks for, as the words a person uses for it.
TONE_WORDS = {
    "warm": ("friendl", "nice", "nicer", "warm", "polite", "politer", "kind", "gentler",
             "gentle", "softer", "soft", "tactful", "diplomatic", "angry", "harsh", "rude",
             "aggressive", "blunt", "cross", "snappy"),
    "formal": ("formal", "professional", "businesslike", "official"),
    "casual": ("casual", "informal", "less stiff"),
    "short": ("short", "shorter", "brief", "concise", "punchy"),
}

# The words a follow-up tones the sentence with, and the joining words between them, are not the
# sentence: "make it shorter and less angry" and "can you make it a bit warmer and less jokey"
# hand over nothing, and quoting "and less jokey" back at the person is nonsense. Flattened
# stems, because TONE_WORDS holds them ("friendl", "politer").
TONING_WORDS = frozenset(word for words in TONE_WORDS.values() for word in words)
JOINING_WORDS = frozenset("""
and but or also plus then so just please bit little really very quite rather still too as well
less more much slightly now thanks thank you for me mate ok okay
to be sound sounds read reads look looks come comes across
""".split())
# How the message sounds, as a person names it, when the word is not one the rewriter acts on:
# "less jokey" is a tone whether or not there is a rule for making a joke quieter.
TONE_DESCRIPTORS = frozenset("""
joke jokes jokey jokingly jokier funny funnier fun silly serious light lighter cheery cheerful
breezier breezy flowery salesy pushy needy desperate posh chatty direct firm sweary swearing
angry cross snappy blunt harsh rude
""".split())


def _only_the_tone(rest):
    """True when what follows the instruction is the tone again, not text to rewrite."""
    words = [word.strip(".,!?;:'\"") for word in str(rest or "").lower().split()]
    words = [word for word in words if word and word not in JOINING_WORDS]
    if not words:
        return True
    for word in words:
        if word in TONE_DESCRIPTORS or CONTINUED.search(word):
            continue
        if any(stem in word for stem in TONING_WORDS):
            continue
        return False
    return True

# The wording that makes a demand, and the wording that asks. Only these swap, because a rewrite
# that changes the meaning of what someone wants to say is worse than no rewrite at all.
DEMANDS = (
    (re.compile(r"\bi want\b", re.I), "I'd like"),
    (re.compile(r"\bi need you to\b", re.I), "Could you"),
    (re.compile(r"\bi demand\b", re.I), "I'd ask for"),
    (re.compile(r"\bgive me\b", re.I), "could I have"),
    (re.compile(r"\byou need to\b", re.I), "could you"),
    (re.compile(r"\byou must\b", re.I), "would you be able to"),
    (re.compile(r"\byou never\b", re.I), "it sometimes feels like you don't"),
    (re.compile(r"\byou always\b", re.I), "it sometimes feels like you always"),
    (re.compile(r"\bi'm sick of\b", re.I), "I'm fed up with"),
    (re.compile(r"\bi am sick of\b", re.I), "I'm fed up with"),
    (re.compile(r"\bi'm fed up of\b", re.I), "I'm fed up with"),
    (re.compile(r"\bsort it out\b", re.I), "look into it"),
    (re.compile(r"\bright now\b", re.I), ""),
    (re.compile(r"\bimmediately\b", re.I), "as soon as you can"),
)


def _reword_ask(text):
    """The text the line wants rewritten, or None when the line is not a rewrite request.

    An empty string means the line asks for a rewrite but hands over nothing to rewrite.
    """
    flat = _flat(text)
    lowered = " ".join(str(text or "").lower().split())
    asked = any(phrase in flat for phrase in REWORD_ASKS)
    tone = any(word in flat for group in TONE_WORDS.values() for word in group)
    if not (asked and (tone or ":" in lowered)):
        return None
    head, sep, tail = lowered.rpartition(":")
    if sep and len(tail.split()) >= 2 and any(phrase in _flat(head) for phrase in REWORD_ASKS):
        return tail.strip(" .\"'")
    # The instruction is what comes before the text: take the earliest one, so "rewrite this
    # email so it sounds professional" hands over the email, not the word "professional".
    at, found = len(flat) + 1, ""
    for phrase in REWORD_ASKS:
        where = flat.find(phrase)
        if where >= 0 and (where < at or (where == at and len(phrase) > len(found))):
            at, found = where, phrase
    rest = flat[at + len(found):] if found else flat
    # "so it sounds professional" and "so it doesn't sound rude" are the tone again, said after
    # the text rather than before it.
    rest = re.sub(r"\bso (it|that) (sounds?|reads?) (more |less )?.*$", "", rest)
    rest = re.sub(r"\bso (it|that) does ?n[o']?t sound .*$", "", rest)
    # What follows the instruction is the tone, not the text: "make this sound less angry please
    # i need to tell my boss i quit" hands over the sentence after the tone words.
    rest = re.sub(r"^\s*(a bit |abit |a little |alittle )?(sound|sounds|read|look)?\s*"
                  r"(less|more|softer|warmer|friendlier|nicer|politer|politelier|formal|"
                  r"professional|casual|shorter|briefer|blunt|harsh|rude|angry|aggressive|"
                  r"gentle|tactful|diplomatic|kind)\b\s*(angry|harsh|blunt|rude|aggressive|"
                  r"formal|polite)?",
                  "", rest)
    for _ in range(3):
        rest = re.sub(r"^\s*(a bit|a little|please|thanks|thank you|for me|mate)\b[ ,]*",
                      "", rest)
    rest = rest.strip(" .,:;\"'")
    if len(rest.split()) < 3 or _only_the_tone(rest):
        return ""
    return rest


def _tone_of(text):
    flat = _flat(text)
    tones = set()
    for tone, words in TONE_WORDS.items():
        if any(word in flat for word in words):
            tones.add(tone)
    if "less formal" in flat:
        tones.add("casual")
    if any(phrase in flat for phrase in CHECK_ASKS) and not tones:
        tones.add("check")
    return tones


def _softened(sentence, tones):
    """The sentence with its demands asked instead, no shout in it, and the tone asked for."""
    out = sentence.strip()
    for pattern, better in DEMANDS:
        out = pattern.sub(better, out)
    out = out.replace("!", ".")
    # "now" is what makes a request read as a demand; "as soon as you can" keeps the urgency.
    out = re.sub(r"\bnow\b(?=\s*(?:[.,;!?]|$|or\b|and\b))", "", out)
    out = re.sub(r"\s+", " ", out).strip(" ,;")
    out = re.sub(r"\bi\b", "I", out)
    # A typist who leaves the apostrophe out still wants the apostrophe in the sentence they send.
    for bare, proper in (("cant", "can't"), ("dont", "don't"), ("wont", "won't"),
                         ("doesnt", "doesn't"), ("didnt", "didn't"), ("couldnt", "couldn't"),
                         ("wouldnt", "wouldn't"), ("isnt", "isn't"), ("im", "I'm"),
                         ("ive", "I've"), ("ill", "I'll")):
        out = re.sub(r"\b%s\b" % bare, proper, out)
    if out and out[0].islower():
        out = out[0].upper() + out[1:]
    if "formal" in tones:
        for short, long in (("I'm", "I am"), ("I've", "I have"), ("I'd", "I would"),
                            ("I'll", "I will"), ("don't", "do not"), ("doesn't", "does not"),
                            ("can't", "cannot"), ("won't", "will not"), ("it's", "it is"),
                            ("couldn't", "could not"), ("wouldn't", "would not")):
            # the sentence may open on the contraction, so the swap has to survive a capital
            out = re.sub(re.escape(short), long, out)
            cap_short, cap_long = short[0].upper() + short[1:], long[0].upper() + long[1:]
            out = out.replace(cap_short, cap_long)
    if "casual" in tones:
        for long, short in (("I would", "I'd"), ("I am", "I'm"), ("do not", "don't"),
                            ("cannot", "can't"), ("will not", "won't")):
            out = out.replace(long, short)
    # Days and months are names, and a sentence someone is about to send should not have them
    # in lower case.
    for name in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
                 "January", "February", "March", "April", "May", "June", "July", "August",
                 "September", "October", "November", "December"):
        out = re.sub(r"\b%s\b" % name.lower(), name, out)
    # A person's name is a name too: "Hi sarah, just checking in" is how it was typed, and
    # nobody sends that. Only after a greeting, where a lower-case word is certainly a name.
    out = re.sub(r"\b(Hi|Hello|Dear|Hey|Thanks|Thank you|Morning|Afternoon)\s+([a-z])",
                 lambda m: m.group(1) + " " + m.group(2).upper(), out)
    if out and out[-1] not in ".?!":
        out += "."
    return out


# A rewrite is a conversation: "make this less angry: ..." then "shorter" then "and friendlier".
# The text is in the last line that handed one over, so a follow-up returns that same sentence
# with the tone it asks for now added rather than asking the person to paste it again.
CONTINUED = re.compile(r"\b(more|less|softer|friendlier|friendly|nicer|polite|politer|shorter|"
                       r"briefer|formal|casual|tone|warmer|pushy|rude|blunt|harsh|strong|needy|"
                       r"desperate|unprofessional)\b")


def _last_rewrite(memory):
    """The text and tones of the rewrite before this turn, or None.

    Only lines that handed text over count, so a follow-up after an ordinary answer is not read
    as one about a sentence that was never there.
    """
    turns = memory.get("turns") or []
    for turn in reversed(turns[-4:]):
        if not isinstance(turn, dict):
            continue
        said = turn.get("user")
        asked = _reword_ask(said) if isinstance(said, str) else None
        if asked:
            return asked, _tone_of(said)
    return None


# The sentences people hand over most often are the ones they find hardest to say, and a
# mechanical softening of "i need to tell my boss i quit" is no use to anyone: it needs the
# words, not the punctuation tidied. These are the meanings, keyed by what the line is about,
# so the reply says the thing in a way the person can actually send.
HARD_TO_SAY = (
    (re.compile(r"\b(quit|quits|resign|resigning|resigned|hand in my notice|leave my job)\b"),
     "I've decided to move on, and I'd like to agree a leaving date.",
     "Say it out loud first and keep to that one line: the date and a thank you are the parts "
     "they remember, and the reasons are for the exit interview."),
    (re.compile(r"\b(pay me|owe me|my money|the money back|refund|invoice)\b"),
     "I'd like to sort out what I'm owed, please.",
     "Put the amount and the date in the message, and say what you will do next if it is not "
     "settled, once, without heat."),
)


def _hard_to_say(asked):
    """A known hard sentence, said properly, or None."""
    flat = " ".join(asked.lower().split())
    for pattern, sentence, tail in HARD_TO_SAY:
        if pattern.search(flat):
            return sentence, tail
    return None


def _rewritten(asked, tones, from_followup=False):
    """The rewrite, phrased as the answer: the sentence, then what to leave in or out."""
    body = _softened(asked, tones)
    known = _hard_to_say(asked)
    # The canned words for the hardest sentences are for a request made in full ("make this
    # sound less angry: i need to tell my boss i quit"), not for "make it shorter" three turns
    # later: shortening a message about an invoice must not replace it with a sentence about a
    # resignation or a refund.
    if from_followup:
        known = None
    if known is not None and ("warm" in tones or "short" in tones):
        body, tail = known
        return 'Softer, same point: "%s" %s' % (body, tail)
    if tones == {"check"}:
        # Handed over to be checked, not told off: say what is right about it and what is missing.
        return 'Reads all right: "%s" Nothing needs fixing: it is short, it says what you want, and ' \
               'it leaves them an easy way to say yes. Add the date you need an answer by if there ' \
               'is one.' % body
    polite = any(t in tones for t in ("warm", "formal"))
    # "please" belongs on a request. A sentence that only tells someone something ("I need to
    # tell my boss I quit") is not rude for leaving it out, and "please" on it reads as a mistake.
    asking = bool(re.search(r"\b(want|need|give|send|pay|refund|back|fix|sort|complain|explain|"
                            r"ask|book|change|cancel|return|replace|stop|reply|respond|"
                            r"could|would|can)\b", body.lower()))
    if re.search(r"\bneed to (tell|say|let)\b", body.lower()):
        asking = False
    if polite and asking and "please" not in body.lower() and not body.endswith("?"):
        body = body[:-1] + ", please." if body.endswith(".") else body + "?"
    if "short" in tones:
        body = re.sub(r"\b(just|really|actually|basically|obviously|literally)\b ?", "", body)
        body = re.sub(r"\s+", " ", body).strip()
    tail = ("Ask for what you want and a date, and leave out the anger: a short, specific message "
            "gets answered more often than a hot one.")
    if not asking:
        tail = ("Say it plainly, name the date, and stop there: the calmer and shorter it is, the "
                "better it lands.")
    if "formal" in tones:
        tail = ("Formal but human works best: the request, the date, and one line of reason, with no "
                "apology for asking.")
    elif "casual" in tones:
        tail = ("Keep it short and say it as you would out loud; the subject still has to be clear.")
    elif "short" in tones:
        tail = ("Cut everything that is not the request: the ask and the date are the whole message.")
    return 'Softer, same point: "%s" %s' % (body, tail)


# A line about what *someone else* eats is the memory store's, not a dinner idea. "she doesnt
# eat meat" is a fact about the mum that wants saying back, and "what did i say she doesnt eat"
# asks what is already known; the vegetarian-dish entry answers both with cooking advice, and
# the person is left without knowing their line was taken in.
THEIR_EAT = re.compile(r"\b(?:eat|eats|eating|diet|diets|vegetarian|vegan|pescatarian|meat"
                       r"|gluten|dairy|halal|kosher)\b", re.I)
# Words that make the line a request for a meal rather than a fact about the person: "what can
# i cook for my mum" is a cooking question even though it names her diet.
COOK_WORD = re.compile(r"\b(?:cook|cooks|cooking|cooked|make|makes|making|recipe|recipes|meal"
                       r"|meals|dinner|lunch|tea|supper|dish|dishes|serve|serving|menu|feed"
                       r"|buy|shop"
                       # The oven verbs and the meals people name on their own. "my son cant
                       # have dairy, what can i bake" was a fact kept and said back ("Your son
                       # is dairy-free.") with the ask left unanswered, because "bake" was not
                       # in this list while "cook" and "make" were: the same line in those words
                       # got the swaps. A line that names what to bake is a request for food,
                       # exactly as one that names what to cook is.
                       r"|bake|bakes|baking|baked|roast|roasts|roasting|grill|grills|grilling"
                       r"|fry|fries|frying|breakfast|breakfasts|snack|snacks|pudding|puddings"
                       r"|dessert|desserts|cake|cakes|biscuit|biscuits|bread|packed lunch)\b",
                       re.I)
# A line that asks what was already said ("what did i say she doesnt eat").
SAID_WORD = re.compile(r"\b(?:say|said|saying|tell|told|ask|asked|mention|mentioned|remember"
                       r"|remind)\b", re.I)

# "can he eat cake", "can she eat pesto": the question is about the *food*, and the knowledge
# base has an answer for it (the allergy entry, the meat-free dishes). Read as a question about
# the guest it only gets the store's shrug - "You haven't told me what your son eats" - which is
# wrong when the line before said what he cannot have. A question whose object is the diet
# itself ("does she eat meat", "what does she eat") is still a question about the person.
EAT_VERB = re.compile(r"\b(?:eat|eats|eating|have|has|having|drink|drinks|drinking|try|trying"
                      r"|tuck)\b")
DIET_WORDS = frozenset("""
meat dairy gluten nut nuts egg eggs fish pork wheat soya soy lactose halal kosher vegetarian
vegan pescatarian cheese milk sugar carbs alcohol shellfish peanut peanuts seafood chicken beef
lamb bacon ham butter cream yoghurt yogurt bread pasta rice potato chips
""".split())
NOT_THE_THING = frozenset("""
a an the some any this that it my your his her their our at on in for with too as well again
today tonight now though really then there here and but or so
""".split())


def _asks_about_a_food(low):
    """Whether a question about someone puts a thing to eat after the verb ("can he eat cake")."""
    found = EAT_VERB.search(low)
    if not found:
        return False
    words = [word.strip(".,!?;:'\"") for word in low[found.end():].split()]
    words = [word for word in words if word and word not in NOT_THE_THING]
    if not words:
        return False
    return words[0] not in DIET_WORDS


def _someones_else_diet(text, memory, understood):
    """True when the line is about what someone other than the person eats.

    The memory store keeps a visitor's diet against the visitor and says it back with their name
    ("Your mum doesn't eat meat."); the knowledge base has one answer for meat-free eating and it
    is a request for dish ideas, so it reads both the fact and the question about it as a cooking
    question. A statement about them, or a question about what is already known, is theirs.
    """
    low = " ".join(str(text or "").lower().split())
    if not low or COOK_WORD.search(low):
        return False
    if not THEIR_EAT.search(low) or not isinstance(understood, dict):
        return False
    if not _names_someone_else(low):
        return False
    if not memory.get("others"):
        return False  # nobody else has been talked about: there is nothing to be right about
    if understood.get("kind") != "question" and _a_guest_restriction(text, memory, understood):
        # "my friend doesnt eat dairy" is a constraint on the dinner, and the kitchen has the
        # swaps for it: the store's "Your friend doesn't eat dairy." says the line back and
        # answers nothing. The swaps are the better reply, so the knowledge base keeps the line.
        # A question about them is still the store's: "is my mum vegetarian or what" is asking
        # what was said, and a dinner idea is no answer to it.
        return False
    if understood.get("kind") == "question":
        if SAID_WORD.search(low):
            return True
        if _asks_about_a_food(low):
            return False  # "can he eat cake" is the knowledge base's, allergy and all
        return not _about_them_alone(low)
    if MEAT_FREE.search(low):
        # A meat-free diet is always the kitchen's: over a dish being cooked it changes the dish,
        # and over a question that was not about cooking it gets the swap and the portion. The
        # store's "Your daughter doesn't eat meat." says the line back either way.
        return False
    return True


def _a_guest_restriction(text, memory, understood):
    """Whether the kitchen has a cooking answer for the diet this line names for someone else.

    One question, asked of the dish table: a diet the table has swaps for, or the meat-free
    dinner, is a constraint on what to cook rather than a fact to keep. A line the table does
    not answer is still the store's ("my mum ate dairy and was ill").
    """
    try:
        from bot.knowledge import dishes
    except Exception:
        return False
    return bool(dishes.has_a_diet_reply(memory, understood)
                or dishes.has_a_veggie_reply(memory, understood))

# The diets the dish tables have an answer for. A meat-free request has a dinner idea
# (dishes.VEGGIE_IDEA, dishes.VEGAN_IDEA); dairy, fish and the rest do not, so a line naming one
# of those over a dish keeps the store's echo, which is true, instead of being handed to whatever
# entry is about that food ("my husband doesnt eat dairy" used to be answered with the cheese
# calorie line, "she doesnt eat fish" with how to tell fish is done).
MEAT_FREE = re.compile(
    r"\b(?:vegetarian|vegetarians|veggie|veggies|vegan|vegans|meat\s?free|flexitarian)\b|"
    r"\b(?:doesn'?t|doesnt|don'?t|dont|won'?t|wont|can'?t|cant|never|refuses to|hates)\s+"
    r"(?:eat|eats|eating|touch|touches)\s+(?:any\s+)?meat\b|"
    r"\b(?:no|without|off)\s+meat\b", re.I)


def _names_someone_else(low):
    """Whether the line names or points at a person other than the speaker."""
    for relation in mem.facts.RELATIONS:
        if re.search(r"\b" + relation + r"\b", low):
            return True
    return bool(re.search(r"\b(?:he|she|they|him|her|them|his|their)\b", low))


# A thank-you line can still be a writing job: "thank you letter for a present" and "thank you
# card for a wedding present" name the thing to write straight after the thanks, and the note to
# send is what the person wants help with - "Happy to help." answers nothing. The thanks are the
# member of the pair that came first; what follows the "you" decides.
WRITE_OBJECT = frozenset("""
letter letters card cards note notes message messages text texts email emails wording words
verse poem speech toast
""".split())


def _a_writing_job(understood):
    """True when the line asks for the words by naming the thing to write itself."""
    norm = list((understood or {}).get("norm") or ())
    for at, word in enumerate(norm):
        if word not in ("thank", "thanks", "thankyou", "thank you", "thx", "ta"):
            continue
        rest = [w for w in norm[at + 1:] if w != "you"]
        if rest and rest[0] in WRITE_OBJECT:
            return True
    return False


# A question about what somebody else likes is a fact the memory store keeps against that person
# ("she's vegetarian and cant stand museums" -> "and what does she not like"), and the kitchen has
# an answer that is a dinner idea instead: the meat-free dish, because the vegetarian line was said
# a turn before. The store says the fact back with the person's name; a card about a dish answers a
# question nobody asked. Only the open ask is read here - "what does my mum hate" - because a yes/no
# about a named thing ("does she like museums") can be a real question about the thing.
A_TASTE_OF_THEIRS = re.compile(
    r"\b(?:what|which)\s+(?:does|do|did)\s+"
    r"(?:(?:my|our)\s+[a-z][a-z'\u2019-]*|he|she|they)\s+(?:not\s+)?"
    r"(?:like|love|enjoy|hate|dislike|mind|prefer|fancy)\b", re.I)


def _asks_about_their_taste(text):
    """Whether the line asks what somebody else likes or hates."""
    return bool(A_TASTE_OF_THEIRS.search(" ".join(str(text or "").lower().split())))


def _about_them_alone(low):
    """"what can she eat" asks for the person; "my mum" is the guest, not the speaker."""
    theirs = "|".join(mem.facts.RELATIONS)
    if re.search(r"\b(?:my|our)\s+(?:" + theirs + r")\b", low):
        return False
    return bool(re.search(r"\b(?:i|im|i'm|me|my|we|us|our)\b", low))


COMPLAINT = re.compile(r"\b(?:i (?:get|have|had|keep getting|keep|suffer from|live with)|"
                       r"i(?:'ve|ve) (?:got|had|been having))\b", re.I)
HEALTH_DOMAINS = frozenset(("body", "science", "fitness"))
_HEALTH = []


def _health_entries():
    """The answers about a person's own body, read once."""
    if not _HEALTH:
        _HEALTH.extend(one for one in all_entries()
                       if (getattr(one, "domain", "") or "") in HEALTH_DOMAINS)
    return _HEALTH


def _names_a_typed_word(item, text):
    """True when the entry is about a word the person actually typed."""
    said = {word.strip(".,!?;:").lower() for word in _flat(text).split()}
    return bool(said & _key_words(item))


# A detail that narrows a trouble is still about the answer on the screen: "it's worse when I lie
# down" after the heartburn answer is the line that answer already carries ("leave three hours
# between dinner and bed"). Read on its own words it asks for nothing, and the reply it used to
# get was "I'm listening - say more if it helps", which is what a person says when they have not
# heard you. The circumstance words are the join: the detail names when it is at its worst and the
# answer names the same time of day in its own words, so a family of them is how the two meet.
DETAIL_LINE = re.compile(r"\b(?:worse|better|only|mostly|mainly|usually|always|hurts|aches|sore)\b"
                         r"[^.!?]{0,30}?\b(?:when|if|at|after|before|in the|during|while)\b|"
                         r"\b(?:when|if|whenever) (?:i|we)\b", re.I)
CIRCUMSTANCE = (
    ("bed", "lie", "lying", "lay", "sleep", "sleeping", "night", "nights", "overnight",
     "pillow", "reclining", "wake", "waking", "morning", "mornings"),
    ("sit", "sitting", "sat", "chair", "desk", "seated", "screens", "screen", "computer", "work"),
    ("stand", "standing", "stood", "feet", "upright"),
    ("eat", "eating", "meal", "meals", "food", "dinner", "lunch", "breakfast", "swallow"),
    ("walk", "walking", "run", "running", "stairs", "steps", "climb", "climbing", "kneel"),
    ("bend", "bending", "stoop", "lift", "lifting", "carry", "carrying"),
    ("cold", "chilly", "damp", "winter", "weather", "rain"),
    ("stress", "stressed", "anxious", "worry", "worried", "tension", "busy"),
)


def _circumstances(text):
    """The circumstance family of every circumstance word in a line, and nothing else.

    Only the words in `CIRCUMSTANCE` count. Starting from every word of the line made the join
    between a detail and a sentence a shared pronoun: "it gets worse when its cold" and "It is
    ready when a fork twists easily in the middle" met on "it" and "when", and the doneness line
    of a slow roast was handed over as "the part for that" for a detail about the weather.
    """
    words = {word.strip("'") for word in re.findall(r"[a-z']+", str(text).lower())}
    found = set()
    for family in CIRCUMSTANCE:
        if words & set(family):
            found |= set(family)
    return found


# How the part of the answer that speaks to the detail is handed over. One frame is a little
# different from the next so that two details in a row do not come back in the same words.
DETAIL_FRAMES = ("Then this is the part that helps: {part}",
                 "That's the bit to work on: {part}",
                 "This is the part for that: {part}")


def _detail_frame(part):
    return DETAIL_FRAMES[len(part) % len(DETAIL_FRAMES)].format(part=part)


def _a_figure_the_answer_has(text, memory):
    """The sentence of the last answer that carries a figure this line names, or None."""
    from ..memory import detail as detail_reading  # noqa: PLC0415 - its own reader
    try:
        return detail_reading.the_fact_the_answer_has(text, memory)
    except Exception:  # noqa: BLE001 - a reader that cannot read is no answer here
        return None


def _a_detail_answered(text, memory):
    """The sentence of the last answer that speaks to this detail, or None."""
    line = str(text or "")
    if not DETAIL_LINE.search(line):
        return None
    reply = str(mem.last_bot(memory) or "")
    if not reply:
        return None
    want = _circumstances(line)
    known_first = None
    said = {stem(word) for word in keywords(line) if len(word) > 2}
    best, best_score, known = "", 0, False
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", reply) if part.strip()]
    for index, sentence in enumerate(sentences):
        if len(sentence.split()) < 6:
            continue
        if index == 0 and known_first is None and already_said(memory, sentence):
            known_first = sentence
        # A circumstance the two share is the join ("worse lying down" is "between dinner and
        # bed"), and a word the two share is the subject. A sentence that does not name the same
        # circumstance is not about this detail, however many words it shares.
        shared = want & _circumstances(sentence)
        if not shared:
            continue
        there = {stem(word) for word in keywords(sentence) if len(word) > 2}
        score = 2 * len(shared) + len(said & there)
        if score > best_score:
            best, best_score = sentence, score
            known = already_said(memory, sentence)
    if best and best == known_first:
        # The sentence that speaks to the detail is the opening of the answer they are reading:
        # handing it back, framed or not, is the paragraph they have just been given.
        return None
    if not best:
        return None
    if len(best.split()) * 2 >= len(str(reply).split()):
        # The part is most of the answer on the screen ("keep the room cool and dark, and don't
        # lie there fighting it - get up, then go back when you feel heavy again" is all but the
        # first nine words of it), so framing it as the part for the detail says the paragraph
        # again in other words. A part is only worth handing over when it is a part.
        return None
    # The line is a detail of the answer they are looking at, so the part of it for that detail
    # is named as such: the whole paragraph again, or the bare sentence with no lead-in, reads as
    # if the bot had not heard the detail at all.
    part = best[0].lower() + best[1:] if best[:1].isupper() else best
    return _detail_frame(part)


def _a_complaint_answered(text, understood, memory):
    """The help a report of a sore or a trouble did not spell out, or None.

    "i get heartburn after meals" reached nothing and got "I'm listening - say more if it
    helps", which is what a person says when they have not heard you. The line is read as the
    question a friend hears ("what can I do about heartburn"), against the health answers only.
    """
    if not COMPLAINT.search(_flat(text)):
        return None
    if trouble_reading.reads_as_trouble(_flat(text), (understood or {}).get("words")):
        # A bodily trouble the chat module already talks them through ("i get migraines" gets the
        # dark room and something for it early) is that module's turn: this reading is only for a
        # report that nothing else has a word for, so nothing it answers today moves.
        return None
    if find(understood) is not None:
        return None  # the line found its own answer: nothing to add
    again = dict(understood)
    again["clean"] = "what can i do about " + str(understood.get("clean") or _flat(text))
    # a reading of its own is words of its own: a guard that asks whether a word is in `words`
    # raises on None, and this reading would lose the answer it exists to give
    again["words"] = [word for word in re.findall(r"[a-z']+", again["clean"].lower()) if word]
    item, reply = _offer(lambda reject: find(again, entries=_health_entries(), reject=reject),
                         memory, again)
    if item is None or not isinstance(reply, str) or not reply.strip():
        return None
    if not _names_a_typed_word(item, text):
        return None
    remember_answer(memory, reply, _key_words(item))
    _remember_answer(memory, item, reply)
    return reply


def _a_dish_was_offered(memory):
    """Whether the meal being planned has already been answered with food.

    The line before a diet said of a guest is the difference between the two: straight after
    "my mum is coming over on sunday for dinner" the diet is news about her, while after "what
    should i cook" it is telling the bot what the dish has to be.
    """
    if not isinstance(memory.get("meal"), dict):
        return False
    turns = memory.get("turns") or ()
    return bool(turns) and (turns[-1] or {}).get("module") == "answers"


def observe(text, memory):
    """Keep what the line says about the meal it is planning, for the next short line to narrow."""
    understood = memory.get("understood")
    if not isinstance(understood, dict):
        understood = understand(text, memory)
    try:
        a_year_of_birth.observe(text, memory)
    except Exception:  # noqa: BLE001 - a year of birth must never cost a turn
        pass
    try:
        plan = cooking.remembered(understood, memory)
    except Exception:  # noqa: BLE001 - a plan hint must never cost a turn
        return
    if plan:
        memory["meal"] = plan


# A line that asks only for a length of the thing just answered: "how long does it last",
# "how long does that take", "how many days then". Every word is the ask or a word pointing
# back at the answer, so the line names no thing of its own and the length is the answer's own.
# A line that names one - "how long until he is house trained", "how long should i rest it" -
# is another entry's question, and the length of the answer before it is no fact about it.
LENGTH_SAID = frozenset("""
    how long much many it that this these those them they he she you i
    do does did is are was were be been will would should can could
    a an the of to for in on at about more time day days week weeks month months
    hour hours minute minutes last lasts lasted going gone left
    take takes taking me us mine
""".split())


def _asks_only_the_length(text):
    """Is every word of this line the length ask or a word pointing back at the answer?"""
    words = [re.sub(r"[^a-z']", "", word.lower()) for word in str(text or "").split()]
    words = [word for word in words if word]
    if not words or not set(words) & {"long", "many", "much"}:
        return False
    return set(words) <= LENGTH_SAID


def TAKES_AS_IT_COMES(text, memory=None):
    """A request for less is answered with the answer they already have, cut down.

    The arbiter passes over a reply that is the last answer said again (the never-repeat rule),
    because a bare follow-up read as a fresh line comes back as "Same as before: <the opening>".
    A request for less is the one line where that shape is the whole answer, so the module says
    so on the line in front of it. Only where the hand-back is really there: on a request for
    less with nothing to cut down, this module has no claim and the lookup's reply is its own.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return False
    return bool(repeat.asks_for_less(text) and repeat.shorter_for(text, memory))


def claims_instead(text, memory=None):
    """The arbiter's `CLAIMS_INSTEAD`: a line asking how to answer somebody else's question.

    "how do i answer what are your weaknesses" is the interview question said out loud, and the
    composer reads the words in it as a question to the bot about itself, so the identity card
    takes the turn as it comes and the person is told the bot has no news and no clock. The
    knowledge base has the interview answer, so the module says the line is its own answer - only
    where it really is: the frame is narrow, the bare identity ask is left alone, and a line the
    knowledge base cannot answer keeps its turn.
    """
    if not isinstance(text, str) or not ANSWERING_A_QUOTED_ASK.search(text):
        return False
    if WHO_IS_THE_BOT.search(text) or not isinstance(memory, dict):
        return False
    try:
        return respond(text, memory) is not None
    except Exception:  # noqa: BLE001 - no claim is better than a broken turn
        return False


CLAIMS_INSTEAD = claims_instead


def _a_limit_on_the_plan(text, memory):
    """True when the line is only a limit on the plan, which the composer answers itself.

    Read through `bot/memory/ack.py`, which owns the frames and the "is it only a limit" test, so
    the two answers for a limit cannot drift apart. A line that gives the store something of its
    own (a person, a detail, a plan) is a fact of its own and keeps the knowledge base's answer.
    """
    try:
        from ..memory import ack as _ack
    except Exception:
        return False
    try:
        return bool(_ack.a_limit_on_the_plan(text) and _ack.a_limit_reply(text, memory))
    except Exception:
        return False


# "what day did i say it was due", "what did i say the excess was": the person asks for a detail
# from one of their own earlier lines, and the word the ask turns on is not what the line is
# about - a school project "due friday" read as a late period, which is the card that answered
# "what day did i say it was due". The memory store quotes their line, so an entry that takes the
# ask on one of its words answers a question nobody asked.
THEIR_OWN_ASK = re.compile(
    r"\b(?:did|have|had)\s+i\s+(?:just\s+)?(?:say|said|tell|told|mention|mentioned)\b", re.I)


def _a_bare_thanks(understood):
    """True when the line is a thank you and nothing else.

    Read here rather than only where the lookup stands down, because the readers that draw on the
    answer just given run in front of the lookup and answer a thank you as a follow-up to it: after
    a recipe, "thats really kind thanks" was handed a second recipe. A thank you with a question
    after it is still a question, and a writing job only opens with a thank you, so both are left
    to the readers below. The kind is the reading that decides: a thanks line can still carry an
    ask word it does not ask with ("thanks, that explains the boiler" carries "explains"), and a
    thank you that really asks something is read as a question.
    """
    return (isinstance(understood, dict) and understood.get("kind") == "thanks"
            and not _a_writing_job(understood))


def _a_judgement_of_the_figure_on_the_table(text, memory):
    """True when the line is only a doubt about a figure, and the reading can answer it.

    The reading is imported here rather than at the top because it is the composer's and this
    module must keep working if it raises: a doubt this cannot read is left to the card.
    """
    try:
        from ..compose import reading as _reading
        return _reading.judges_the_figure_on_the_table(text, memory)
    except Exception:  # noqa: BLE001 - an unreadable doubt is not a reason to lose the answer
        return False


# The modules whose reply is an answer about the subject, rather than a nod at the person's line.
_AN_ANSWER = frozenset(("answers", "memory_store"))


def _the_bot_has_something_to_go_over(memory):
    """True when one of the bot's last lines explains something the ask could be pointing at.

    A line that asks what the bot meant points at the answer just given, so there has to be one.
    Very often there is not: "i got a payslip" is answered "Good to hear. What was the best bit?",
    which is the bot asking rather than answering, and standing the knowledge base down for that
    turn took away the card that answered well - "what does that mean for my pay" got "I haven't
    put anything about it into words yet" instead of the gross/net card. So the reading is asked
    only after the bot has said something to explain: the same test the store uses to decide a
    line is thick enough to hand back (`bot/memory/meant.py`), read here so the two cannot
    disagree about whether there was an answer.
    """
    from ..memory import meant as _meant
    from ..memory import repeat as _repeat
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed((turns or [])[-_meant.LOOK_BACK_FAR:]):
        if not isinstance(turn, dict):
            break
        said = str(turn.get("bot") or "").strip()
        if not said:
            continue
        if str(turn.get("module") or "") in _meant.NOT_TO_REPEAT:
            # An emergency or a condolence is not an explanation to point back at.
            break
        asked = str(turn.get("user") or "").strip()
        if (_repeat.HEDGE.search(said) or _meant.CONDOLENCE.match(said)
                or _meant.RECEIPT.search(said)):
            continue
        if str(turn.get("module") or "") in _AN_ANSWER or _meant._thick_enough(said, asked):
            return True
    return False


def _the_line_asks_what_this_one_meant(memory):
    """True when this turn asks what the bot's own last answer meant.

    "what do you mean", "whats that supposed to mean", "wot u mean", "wdym": the line names
    nothing of its own, so the answer is the last answer said again, which the store gives. The
    reading settles it in every spelling (`understood["asks_what_was_meant"]`, see
    `bot/understanding/kinds.py::_asks_what_was_meant`) so no list of spellings is kept here.
    """
    if not isinstance(memory, dict):
        return False
    understood = memory.get("understood")
    if not (isinstance(understood, dict) and understood.get("asks_what_was_meant")):
        return False
    return _the_bot_has_something_to_go_over(memory)


def respond(text, memory):
    """The knowledge base's reply, with the name the person just gave in front of it.

    A line that is only the thing again with "still" on it is not a new subject for whatever
    card its one word opens - "still cold" after "my shower is cold" is the shower, not the
    common cold - so the store's reading of it keeps the turn (`bot/memory/tried.py`).

    A line that greets the bot and says what they are doing ("hi im jess, im saving for a car")
    is answered by the entry - the substance - and the greeting is the part an entry cannot see,
    so the composer puts the name in front of the answer rather than letting a welcome take the
    turn (`bot/compose/__init__.py::with_name`).
    """
    from ..memory import not_this as _ruled_out
    from ..memory import portions as _portions
    from ..memory import size as another_size
    from ..memory import trips as _trips
    from ..memory.thread import only_the_arrival as _only_the_arrival
    from ..compose import said_about_me
    if isinstance(memory, dict):
        # The line as the person typed it, for the rows that have to tell the words of this line
        # from the earlier subject written into it: a follow-up is read with the thing the talk
        # is on put into it, so "can i freeze it" reads as "im making a chilli tonight can i
        # freeze it", and a card keyed on the added word then answers a line that never said it.
        # See `bot/knowledge/lookup.py::said_in_this_line`.
        memory["asked_now"] = text
    if _only_the_arrival(text):
        # "im back", "back from work", "we are back home": nothing in it but the arrival. A chat
        # with a bad knee in it answered the word "back" as the part, and the arbiter prefers an
        # answer to the composer's "Welcome back. Where were we?", so the person who came back
        # from the shop was told about a back that gives trouble on and off. The return is the
        # composer's line, not the knowledge base's, so this module stands down for it.
        return None
    # A remark that comes back with a frequency on it - "she says it every time i visit" after "my
    # mum says im not trying hard enough" - was answered out of the card the bot's own reply put in
    # the thread ("Agree the length before you go... two nights is plenty for most trips"), because
    # that reply said "mum" and this line says "visit". It is still about the remark, so the
    # sentence that answers a pattern takes the turn and this module stands down
    # (bot/compose/said_about_me.py, `answer_followup`).
    if said_about_me.answer_followup(text, memory):
        return None
        return None
    if _trips.THE_JOURNEY_ASK.search(text or "") and _trips.reply_for(text, memory):
        # A journey asked as a question while a trip is live is the trip's line. "how long will it
        # take to drive" after "we're going to cornwall in july" was answered here by the driving
        # entry - 45 hours of lessons, a test in six months - which is about learning to drive and
        # not about the trip. The trip reader has the reply, and the store leads the turn with it.
        # Only this shape is given up: the rest of the trip's detail questions (what to pack, what
        # to book first) are what the knowledge base is best at.
        return None
    if _the_line_asks_what_this_one_meant(memory):
        # "what do you mean" names nothing of its own: it points at the answer just given, and
        # the store says that answer again ("Just this: Top the pressure up to between 1 and 1.5
        # bar"). Read as a follow-up, the knowledge base reached the subject of the last answer
        # instead and took the word "mean" for the thing named: after "my tomato plants have
        # blight", "wot u mean" was answered "The same goes for the wot u mean: cut off and bin
        # the affected leaves" - the person's own slip said back at them as the subject - and
        # the arbiter prefers a card to the composer's line, so that is the reply they got. The
        # reading knows the shape in every spelling (`understood["asks_what_was_meant"]`), so
        # this module stands down for it rather than keeping a list of its own.
        return None
    if _a_judgement_of_the_figure_on_the_table(text, memory):
        # The line only holds a figure up ("is 2000 too much" after the price of a bike, "is that
        # expensive" after a kitchen quote): what it asks for is the comparison, which the reading
        # has already made, and this module's card says the price range over again instead of
        # answering. See `bot/compose/reading.py` (the reading) and `_doubt_and_answer`.
        return None
    if THEIR_OWN_ASK.search(text or ""):
        # A line that asks for their own words is the conversation's, not the knowledge base's.
        return None
    if repeat.A_PAY_WORD.search(" ".join(str(text or "").lower().split())) \
            and repeat.the_figure_they_gave(text, memory if isinstance(memory, dict) else {}):
        # An ask for their own pay is the store's, and the card it reached was about the shape of
        # a weekly wage rather than about this person's: "i get paid 2000 a month" then "how much
        # is my wage" was answered with the budgeting-a-weekly-wage lesson while the wage was in
        # the chat. The store says the figure, so no card is the answer to the ask.
        return None
    if (_portions.an_ask(text or "", memory) or _portions.a_count_to_fill(text or "", memory)
            or _portions.a_bare_count_to_fill(text or "", memory)):
        # "how much potato salad for a party" / "how many does that feed" is a question about the
        # answer in hand, and the store answers it from that answer. An entry that matches the
        # word "party" answers a different question (cheap party food, not how much of this one to
        # make), so the knowledge base stands down on the line rather than taking the turn.
        # The same holds for a count they change after it ("so how much for 8", "actually 6 of
        # us"): the figure is worked out from the answer's own per-head rule (bot/memory/portions.py).
        return None
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if isinstance(understood, dict) and understood.get("subject_unclear"):
        # The reading could not settle which thing the word means ("the bank was closed", "the
        # seal is broken"). Any entry that matches the bare word is a guess, and a confident card
        # for the other life is worse than saying which one is meant, so the knowledge base stands
        # down and the composer asks. A line with a cue is not flagged.
        return None
    if _a_bare_thanks(understood) and not (isinstance(text, str)
                                          and repeat.after_an_ack(text)):
        # A thank you and nothing else is not a follow-up to the answer it thanks. The readers
        # below answer a line that names the thing in the answer again ("thats kind thanks" after
        # a recipe was handed the recipe a second time, in other words), and a thanks that only
        # closes the turn has nothing of its own for them to answer, so the knowledge base stands
        # down and the small-talk reply takes it. A line after the ack is a line of its own and is
        # left to the readers as before ("cheers. also im skint till friday" is the money line).
        return None
    from ..compose import fallback as _the_composer
    if _the_composer.the_day_remarked(text):
        # The whole line says what the day is like ("windy as anything", "cold next week"). Nothing
        # is being asked and nothing is being looked up, and an entry is reached by a word: "wind"
        # found the bloating card, and "cold next week" found the one about a virus. The composer's
        # own reading decides, so the two cannot disagree about what the day is, and the knowledge
        # base stands down on a line the day's answer owns. A report on the day in the past is not
        # this case and stays with the entry that knows the thing.
        return None
    if _ruled_out.the_place_ruled_out(text, memory):
        # The place this module has a card for is the one they just ruled out: "we want to go to
        # italy" / "not rome" was answered with the Rome card. The line is a rejection, not a
        # mention, so the entry is no answer at all and the store's own reply takes the turn.
        return None
    try:
        if repeat.asks_what_that_costs(text, memory):
            # A line that asks what the thing on the screen costs names nothing of its own, so
            # the entry about the word in it prices its own subject: after "should i get it
            # serviced" ("a gas boiler service is usually 60 to 120 pounds"), "how much is that
            # usually" was answered with the price of a new boiler. The figure they are asking
            # about is the one in that answer, and the composer hands it back
            # (`bot/memory/repeat.py::asks_what_that_costs`), so this module stands down.
            return None
    except Exception:  # noqa: BLE001 - a reading that raises is a line this module keeps
        pass
    if mem.facts.a_name_picked(text, memory):
        # "we got a kitten" / "what should we name her" / "pepper": the word is the name they
        # chose, not a thing to look up. The store keeps it and says it back, and an entry about
        # peppers answers the word while missing the question - which is the one the bot asked.
        return None
    dog_feed = pets.the_dog_feed_follow_up(text, memory)
    if dog_feed:
        # A feeding question asked with a pronoun ("what should i feed him tomorrow") has no
        # animal word of its own, so the dog row cannot reach it; the last few turns still say
        # which animal the chat is on. It is kept as the dog row's answer, because the next line
        # ("how much of that a day") reads what this one was about from that row.
        _remember_answer(memory, pets.DOG_FEED_AMOUNT_ENTRY, dog_feed)
        return dog_feed
    # A limit that reaches an entry for the plan in hand keeps that entry. "keep it cheap" after
    # "im booking flights" is the cheap-flights answer, and an ack in its place ("I'll keep what I
    # suggest to what costs nothing") threw away the booking advice the person was asking for.
    limit = _a_limit_on_the_plan(text, memory)
    # "the cheapest quote i got is 2400" / "is that a lot": the range is in the answer this module
    # gave a turn ago, so the figure the person gave is read against it and the verdict goes in
    # place of the card said again. A price entry can be asked "is 400 too much for a roof
    # repair" - that line names its subject and is answered below - but "is that a lot" names
    # nothing, and no entry can price "that".
    judged = a_price.judged(text, memory)
    if judged:
        _keep_the_answer(text, judged, memory)
        return judged
    resized = another_size.answer_for(text, memory)
    if resized:
        # "what about a bigger one" straight after a time answer is that answer's rule asked for
        # the size they have, and the lookup reaches the entry its bare words fit: the chicken
        # rule came back as "Nothing separate for a bigger - it is the same advice: ...", which is
        # the bot quoting itself at somebody who asked a sum. Read here, before the lookup and
        # before the repeat framing, so the size line is answered by the module that knows how
        # (`bot/memory/size.py`), and a line any other reader can answer is untouched because the
        # reader passes on everything that is not a size ask about the thing above.
        _keep_the_answer(text, resized, memory)
        return resized
    if tried.a_card_is_not_the_answer(text, memory):
        # "still cold" after "my shower is cold" is the shower, and the card its one word belongs
        # to is the common cold: the thing keeps the turn, in the module that answers reports.
        return None
    reply = with_name(_the_dish_by_name(a_year_of_birth.reply(text, memory)
                                       or _answer(text, memory), memory), memory)
    # The same judgement when the figure and the thing are in one line: "is 6000 too much for a
    # new boiler" is answered with the card for a new boiler, which says what one usually costs
    # and never puts their own figure beside it. The card for the thing priced is the answer, so
    # it is the range read here, and the verdict stands in its place.
    judged = a_price.judged_with_the_card(text, reply, memory)
    if judged:
        _keep_the_answer(text, judged, memory)
        return judged
    placed = _the_question_with_the_place_on_it(text, memory, reply)
    if placed:
        _keep_the_answer(text, placed, memory)
        return placed
    if reply:
        # The rows are written for everyone, and the store knows what this person eats: a reply
        # that still names a food they said no to is handed back as no answer, so the row below
        # it - or another module - can answer with something they can eat.
        reply = _fitted_to_what_they_eat(reply, text, memory)
    if reply:
        # A paragraph read out earlier in this chat is not read out again when the line names a
        # sentence of it: "what paint do i need", "how many coats", "do i need a primer" reaches
        # the paint entry three times, and the third turn gave the same paragraph back word for
        # word two turns after the first. The sentence that names what this line names is the
        # part of it that answers, and it is new to the conversation.
        reply = _the_sentence_it_names(reply, text, memory)
    if reply:
        # A row holds one answer for every way its subject is asked about, and it is written the
        # way a screen reads it: a signpost first ("Three tests, in this order.") or the clock
        # first ("About 40 minutes start to finish. Fry 500g mince hard ..."). Neither is the
        # answer to the line read out: the sentence after the signpost is, and "how do i make
        # chilli" wants the method in its first sentence - see `bot/compose/lead.py`.
        reply = lead.answer_first(
            reply, memory.get("understood") if isinstance(memory, dict) else None, text)
    if reply:
        # The same reading for the other shapes of answer: a row holds one answer for every way
        # its subject is asked about, so the sentence that gives the time, the amount or the place
        # the line asked for is moved to the front when the card does not open on it. A declared
        # `lead` still wins, because it goes in after this - see `bot/compose/lead.py`'s `shape`.
        reply = lead.shape(reply, memory.get("understood")
                           if isinstance(memory, dict) else None, text)
    if reply:
        # The sentence the line asked for, in front, when the entry that answered declares one:
        # `entry(..., lead=("yesno", "Usually, yes"))` is the whole of that row's work, in any
        # domain, because every card is said from here - see `bot/compose/lead.py` and
        # `_the_sentence_owed`. It goes in at the last moment, after the repeat and narrowing
        # readings above, so a card the bot has already said is still read as the same card.
        reply = lead.the_sentence_owed(reply, memory.get("understood")
                                       if isinstance(memory, dict) else None,
                                       _the_sentence_owed(text, reply, memory))
    if not reply and limit:
        # "nothing too tiring" after "we are going to york next weekend" is a limit on the trip,
        # not a report of constant tiredness: the knowledge base has a fatigue entry, and it was
        # answering the trip's constraint with two weeks of sleep hygiene. Where the knowledge
        # base has nothing for the plan the limit is on, the composer answers the limit itself.
        return None
    if not reply:
        # The turn after a present list is often about the card, and a card is not a present: "my
        # nephew is 5 in june" / "what can i get them" / "and what about a card" reached the
        # present row again and had the whole list handed back behind a "Same as before" lead -
        # which the arbiter passes over as the answer already on the screen - so the turn ended on
        # a search punt. The card has an answer of its own, and it is the same answer whoever the
        # present was for, so it is said rather than the list.
        card = shopping.the_card_after_a_present(None, memory, line=text)
        if card and shopping.a_present_was_answered(memory):
            reply = card
    if not reply:
        # A line that only picks between things the bot itself just offered is answered from
        # that answer; the knowledge base has no entry for it, and the composer's search shrug is
        # a refusal of a question that was already answered one turn ago.
        reply = _the_one_to_pick(text, memory)
    # The answer is kept before the healing reader looks at it, so the care card stays the answer
    # the next line is read against: "my knee hurts" / "how long does it take to get better" /
    # "and what should i do" asked its "what should i do" of the healing line when that line was
    # the one on record, and got "Nothing to do for now."
    _keep_the_answer(text, reply, memory)
    # "how long will it take to heal" after a card about a body is answered from that card, not
    # from the entry its bare words reach: the entries keyed on healing are bones and sprains, and
    # a cut finger was told six weeks for a bone and a knee was told the two days its icing takes.
    return healing.vetted(text, memory, reply, step_of=_first_step)


def _the_question_with_the_place_on_it(text, memory, reply):
    """The last question asked again with the place this line says, answered; or "".

    "any ideas for a cheap day out with kids" is answered with the free ones, and "near leeds" is
    then the same question with a place on it: the knowledge base holds the day trips from Leeds,
    and main answered the place with "I'm listening - say more if it helps", or with the free ones
    again ("Near leeds - same answer: ..."). So the question is put back together and answered, and
    kept only when that answer is new: a hedge, the answer already on screen, or the very line the
    person's place was answered with, is nothing to hand the turn to.
    """
    question = whereabout.the_question_with_the_place(text, memory)
    if not question:
        return ""
    from ..compose import fallback as composer
    said = str((memory.get("last_answer") or {}).get("reply") or "")
    placed = with_name(_the_dish_by_name(_answer(question, _of_its_own(memory)), memory), memory)
    if not placed or placed in composer.UNKNOWN:
        return ""
    for other in (said, reply):
        if other and placed.strip() == str(other).strip():
            return ""
    # The answer is about the place and not about the answer already given, so a repeat of the
    # last answer with a place on the front of it loses: "Near leeds - same answer: ..." and
    # "Same answer, and it covers this: <the answer above>" are both the line said twice.
    flat_placed = _flat(placed)
    for other in (said, reply):
        flat_other = _flat(str(other or ""))
        if flat_other and flat_other in flat_placed:
            return ""
        if flat_other and flat_other[:60] in flat_placed:
            return ""
    return placed


# What the answer to a question of its own is read against: the person's own facts, and nothing
# about the turn before this one. "any ideas for a cheap day out with kids near leeds" carries
# everything the entry needs, and the reading of the previous line points at the previous entry -
# with that still in the store the combined question was answered by the day-out row again.
_TURN_ONLY = ("understood", "entry_answer", "entry_answers", "frequency_answer",
              "frequency_reply", "last_answer", "topics", "topic", "return_to", "correction",
              "denial", "replies")


def _of_its_own(memory):
    """The store with the last turn's reading taken out, so a question is answered on its words."""
    own = copy.deepcopy(memory) if isinstance(memory, dict) else {}
    for key in _TURN_ONLY:
        own.pop(key, None)
    return own


def _keep_the_answer(text, reply, memory):
    """Keep the answer this module gives, so the next line can be about it.

    Every reader inside this module that answers from an entry records the turn itself, because
    it knows the words the entry was keyed on. The readers that answer from something else - the
    pantry table naming a dish from two foods in the line, a pick between the things the bot
    offered - gave no record at all, so "how long does that take" a turn later had nothing to
    read: "what can i do with mince and a tin of tomatoes" then "ok thanks" then "how long does
    that take" got the search hedge, while the same ask straight after the answer got "Simmer
    for at least 30 minutes". An answer is an answer whichever reader gave it, so the line's own
    words are kept with it, and a record an entry already made this turn is left as it is: it
    knows more about what the answer is about than the line does.
    """
    if not isinstance(memory, dict) or not isinstance(reply, str) or not reply.strip():
        return
    turns = memory.get("turns")
    here = len(turns) if isinstance(turns, list) else 0
    kept = memory.get("last_answer")
    if isinstance(kept, dict) and kept.get("turn") == here and kept.get("reply"):
        return
    _remember_answer(memory, None, reply, keys=keywords(text))



def _the_sentence_it_names(reply, text, memory):
    """`reply` cut to the sentence naming this line's own word, when the paragraph was said before.

    Only a paragraph the bot has already given word for word in this chat is cut: everywhere else
    the entry's own wording is the answer, and the readers above have already narrowed it where
    the line asked for a part. The word has to be one the person has not used before this turn
    ("primer" in "do i need a primer", not "paint" again), so a line that only says the subject
    once more keeps the whole paragraph.
    """
    mine = _flat(reply)
    if not mine or not isinstance(memory, dict):
        return reply
    said_before = any(isinstance(turn, dict) and _flat(turn.get("bot")) == mine
                      for turn in memory.get("turns") or [])
    if not said_before:
        return reply
    named = set(keywords(text)) - _said_before_now(text, memory)
    named &= set(words_of(reply))
    if not named:
        return reply
    parts = [sentence.strip() for sentence in SENTENCE.split(str(reply).strip())
             if sentence.strip() and named & set(words_of(sentence))]
    if not parts:
        return reply
    cut = " ".join(parts[:2])
    if len(cut.split()) < 4 or len(cut) >= len(str(reply).strip()):
        return reply
    return cut


def _fitted_to_what_they_eat(reply, text, memory):
    """The answer with the food they do not eat taken out of it, or "" when it cannot be.

    Every row in the knowledge base is written for everyone, and a row that fits the words can
    still name the food the person has just ruled out: "im vegetarian" then "what can i do with a
    swede" was "mashed with butter, alongside sausages", and "im vegan" then "what can i do with
    spinach" was "a hot pan, a knob of butter". The choosing inside the kitchen reads the diet,
    and the rows themselves do not, so the reply is read here against what the store knows the
    person eats. A word with an everyday swap is swapped ("softened in butter" is "softened in
    oil"), a row with a meat-free version of itself is served as that version, and a reply that
    still names the food they said no to is handed back as no answer at all: the row below it, or
    another module, may have one they can eat, and a shrug is a bad answer but the food they
    refused is a worse one.
    """
    if not isinstance(reply, str) or not reply.strip():
        return reply
    avoided = cooking.avoids(memory)
    # The meat a card uses as an ingredient, where the vegetarian version is one word: the gravy
    # card opens on "whisk the flour into the meat juices", and a vegetarian ten turns into a
    # chat about a roast was handed nothing rather than the gravy. See meat_in_a_card.
    reply = meat_in_a_card.swapped_out(reply, text, avoided)
    fitted = cooking.fits_the_diet(reply, avoided, text)
    if fitted is None:
        return ""
    # The person the chat is about, when that is somebody else in the store (memory["person"]
    # and memory["others"]): a long chat about packing a daughter's lunch is about her, and her
    # allergy is not the person's own (avoids() keeps those apart on purpose) but it does bind
    # the answer about her. Only ever a veto - see cooking.fitted_for_the_one_talked_about.
    fitted = cooking.fitted_for_the_one_talked_about(
        fitted, cooking.avoids_for_the_one_talked_about(memory), text)
    if fitted is None:
        return ""
    return fitted


# A dish names itself at the start of its own text ("A frittata: whisk 6 eggs", "A potato hash:
# fry diced potatoes"), and a qualifier in front of the name is not part of it.
_DISH_NAME_IN_TEXT = re.compile(r"^\s*(?:(?:one|two)[- ]pan\s+|a\s+|an\s+|the\s+)?"
                                r"([^:.,]{3,40}?)\s*:", re.I)


def _the_dish_by_name(answer, memory):
    """A reply that points at the dish ("that one") says the dish's name instead.

    "and i dont have any cheese" after a frittata was answered "Leave the cheese out of that one
    and it still works.", where "that one" names nothing a person can see: the dish was the
    subject of the answer before, and it is the one thing the sentence they now have to act on
    has to say. The plan on the table knows which dish it was, so the name goes in where the
    pointing word was.
    """
    if not isinstance(answer, str) or " that one" not in answer.lower():
        return answer
    plan = cooking.plan_recent(memory) or {}
    offered = [name for name in (plan.get("offered") or ()) if name]
    if not offered:
        return answer
    dishes = {dish["id"]: dish for dish in cooking.DISHES}
    said = _DISH_NAME_IN_TEXT.match(str((dishes.get(offered[-1]) or {}).get("text") or ""))
    name = ""
    if said and len(said.group(1).split()) <= 5:
        name = said.group(1).lower()
    if not name:
        # The plan's id for a dish is built from the foods in it, not from a name anybody has
        # read: "i have chicken and spinach" is answered "Chicken and spinach in one pan: ..."
        # while the id is chicken-spinach-cream, and naming that id gave "Leave the cheese out of
        # the chicken spinach cream and it still works." - a dish on no screen, with no cheese or
        # cream in it. A name comes off the screen, or the sentence keeps "that one".
        shown = _last_answer(memory)
        shown = shown.get("reply") if isinstance(shown, dict) else shown
        screen = _DISH_NAME_IN_TEXT.match(str(shown or ""))
        if screen and len(screen.group(1).split()) <= 5:
            name = screen.group(1).lower()
    if not name:
        return answer                    # "that one" beats a name that is nowhere on the screen
    return re.sub(r"\bthat one\b", "the " + name, answer, count=1, flags=re.I)


def _the_same_answer_again(answer, memory):
    """True when this answer says what the answer just given said, lead-in aside.

    The lead-ins are stripped first ("Same answer, and it covers this: ..."), and the two are
    compared by their openings, because the second telling is the first telling shortened rather
    than repeated word for word.
    """
    was = _flat(mem.last_bot(memory) or "")
    now = _flat(_without_lead_in(answer))
    if not was or not now:
        return False
    return now.startswith(was[:60]) or was.startswith(now[:60])
def _the_figure_the_thing_we_are_on_holds(text, memory):
    """The answer the thing we are on gives this length ask, when it holds the time asked for.

    "how long will it take, start to finish?" after "im making a birthday cake" and "he is
    allergic to nuts": the answer just given is the cake's allergy variant and holds no time, so
    the honest line said the steps are not a length - but the cake the chat is on has its
    timings, and the ask read against it ("... cake") reaches them. The honest line is for a
    length ask that no entry answers, not for one whose subject is a turn back.
    """
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(understood, dict):
        return ""
    wider = followup_reading(understood, memory)
    if not isinstance(wider, dict) or wider is understood:
        return ""
    if _flat(str(wider.get("clean") or "")) == _flat(str(understood.get("clean") or "")):
        return ""
    item, reply = _offer(lambda reject: find(wider, reject=reject), memory, wider)
    reply = str(reply or "").strip()
    if item is None or not reply:
        return ""
    # The entry has to hold the figure the line asks for, or the honest line is the right one.
    return "" if _figure_missing(reply, text) else reply


def _a_length_ask_with_no_figure(text, memory, answer=""):
    """The honest line for a length ask about an answer that holds no time.

    "How long will that take" after the steps for a blocked sink shares no word with the steps, so
    there is no sentence of the answer to quote: the lookup reaches nothing, and the whole
    paragraph came back behind "Same as before". The arbiter passes an echo over as soon as
    another module has anything fresh to say, and a search is fresher, so the person was told
    "I'd rather not guess" about the job in front of them. A friend says the answer holds no time
    and names the first step, so that line is built here, before the repeat is framed.
    """
    if not _asks_only_the_length(text) or mem.last_module(memory) != "answers":
        return None
    earlier = _last_answer(memory)
    last = str((earlier or {}).get("reply") or "")
    if not last.strip():
        return None
    if answer:
        opening = _flat(last)[:60]
        if not opening or opening not in _flat(answer):
            return None  # this reply is not the last answer again, so it is a different answer
    honest = _figure_missing(last, text)
    if not honest or _flat(honest) == _flat(answer):
        return None
    # The answer just given holds no time - but the thing the chat is on may: after a cake and a
    # line about the nuts, the allergy variant is the answer in front and the cake has the
    # timings. That answer beats the honest line, and it is only looked for here, where the
    # honest line would otherwise be said.
    return _the_figure_the_thing_we_are_on_holds(text, memory) or honest

def _a_city_card_asks_which_first(text, memory):
    """True when the line asks which of a city card's places comes first.

    The city rows know their own list of places, so the card they wrote answers it; imported here
    rather than at the top because this is the only place in this module that reads them.
    """
    from ..knowledge import travel as travel_cards
    return (travel_cards.asks_which_one_first(text)
            and travel_cards.a_city_card_is_in_front(_the_answer_in_front(memory)))


def _the_answer_in_front(memory):
    """The reply just given by the knowledge base, for a line asking which part of it to do.

    Only a knowledge answer of the turn just before: a greeting, a hedge or a line of another
    module has no steps in it, and reaching further back would hand over the wrong answer.
    """
    if not isinstance(memory, dict):
        return ""
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return ""
    said = turns[-1] if isinstance(turns[-1], dict) else {}
    if said.get("module") != "answers":
        return ""
    return str(said.get("bot") or "")
# A line that opens by withdrawing something is a take-back, not a question: "forget the dog",
# "scratch that", "never mind the dog", "ignore that". The memory store answers it, so no entry
# of the knowledge base should read the take-back word as the subject of the line.
TAKEN_BACK_OPENER = re.compile(
    r"^\s*(?:(?:please|ok|okay|right)\s+)?(?:forget|forgot|ignore|scratch|disregard|drop|"
    r"never\s+mind|no)\s+(?:that|this|it|the|my|our|your|a|an|about|all)\b", re.I)


# --- how long before the day ----------------------------------------------------------------
# "how long before the day should we order the cake" was answered with how long a cake keeps.
# The ask has a length in it and a thing in it, so the length card for that thing wins the
# lookup, and nothing reads the event the length hangs off: a fixed date with a job to do
# before it. That is what people ask when the date is set - a cake, the invitations, the
# airport parking, a passport - and every one of them has an answer, so the shape is read
# before the lookup rather than left to the thing's own entry.
LEAD_ASK = re.compile(
    r"\bhow\s+(?:long|far|soon)\s+(?:before|ahead\s+of)\s+(?P<event>[^.?!]{1,60}?)\s*"
    r"\b(?:should|shall|ought\s+to|do)\s+(?:i|we|you|one)\s+(?P<act>[^.?!]{0,60})"
    r"|\bhow\s+(?:long|far|soon|early)\s+in\s+advance\s+(?P<act2>[^.?!]{0,60})"
    r"|\bhow\s+early\s+(?:should|shall|do)\s+(?:i|we|you)\s+(?P<act3>[^.?!]{0,60})")
# The job the date hangs off has to be a booking or an ordering one. "how long before the flight
# do i need to be at the airport" and "how early should i get to the airport" are the length of a
# wait on the day, not a lead time, and the general answer below would be wrong for both.
# The words that say what is being booked. A row matches on any one of its words, and the earlier
# row wins, so "wedding cake" is the cake row before anything general.
LEAD_ROWS = (
    (("cake",), "Order a decorated one four to six weeks ahead: the bakery wants the number of "
                "people and the design about a month out, and the week itself it can turn round. "
                "A fruit cake is the exception: it is baked well before and fed brandy as it "
                "sits, and it only gets better."),
    (("turkey", "goose", "bird"), "Order it by the middle of December, and collect it on the 22nd "
                                  "or 23rd so it has two days in the fridge. Free-range and big "
                                  "birds go first, so the middle of the month is the real deadline."),
    (("invitation", "invite", "save"), "Six to eight weeks before the day, with the reply-by four "
                "weeks out - eight to twelve if people have to travel or fly. The venue and any "
                "rooms are the things that go a year ahead, not the cards."),
    (("passport",), "Ten weeks is the honest allowance for a standard renewal, and quicker costs "
                    "extra. Check the country you are going to as well: many want six months left "
                    "on it at the date you arrive, not the date you leave."),
    (("parking",), "Two to four weeks ahead is plenty and the price is the reason: the on-the-day "
                   "rate at an airport is several times the booked one, and the cheap car parks go "
                   "first. The date and the flight time are all they need."),
    (("hotel", "accommodation", "cottage", "campsite", "room"), "As soon as the dates are fixed. A "
                "hotel needs nothing from you but a card, and the cheap rooms are the ones that "
                "sell out first - a refundable rate booked early beats a dearer one late."),
    (("table", "restaurant"), "Two to four weeks ahead for a Friday or Saturday, and a week or two "
                              "for a weeknight. Somewhere small or famous you book when you think "
                              "of it, and a set menu also wants the numbers a few days before."),
    (("flight", "ferry", "train", "ticket", "travel"), "Six to twelve weeks ahead is the cheapest "
                "window: a flight is dearest in the last fortnight and a train is best booked the "
                "day the tickets release, about twelve weeks out. After that the price only climbs."),
    (("venue", "hall", "church", "marquee"), "A year or more for a Saturday in summer, and two "
                "years for the popular ones. The venue sets the date, so it is the first thing "
                "booked and everything else fits round it."),
    (("flower", "delivery", "bouquet", "gift", "present"), "Three to five days ahead for a delivery "
                "on a set day, and a fortnight for anything made to order or for Valentine's and "
                "Mother's Day. Same-day is a different, dearer price."),
)
LEAD_VERB = re.compile(r"\b(?:order|orders|ordering|book|books|booking|reserve|reserving|hire|"
                       r"hiring|send|sends|sending|renew|renews|renewing|apply|applying|"
                       r"arrange|arranging|sort|sorting|pay|paying|buy|buying|collect|"
                       r"collecting|pick|picking)\b")
LEAD_ANY = "Sooner than you would think: the price only goes up and the good slots go first, so " \
           "book it as soon as the date is fixed. Tell me which booking and I will be exact."


def _a_lead_time(text):
    """The answer to "how long before the day should we order it", or None.

    Read before the lookup: the thing named in the line has a length entry of its own (a cake
    keeps four days, parking is a price), and that entry answers a question about the thing
    rather than about the job to do before the date.
    """
    if not isinstance(text, str):
        return None
    found = LEAD_ASK.search(text.lower())
    if not found:
        return None
    act = " ".join(part for part in found.groups() if part)
    if not LEAD_VERB.search(act):
        return None
    words = {word.rstrip("s") for word in WORD.findall(text.lower())}
    for needles, answer in LEAD_ROWS:
        if any(needle.rstrip("s") in words for needle in needles):
            return answer
    return LEAD_ANY




# A thing that has got better is news, and the knowledge base is the advice for the thing still
# being there. "i have a rash on my arm" then "the rash has cleared up" reached the rash entry
# again and came back as *"Same answer, and it covers this: Most rashes are contact or heat..."* -
# the paragraph for a rash that has gone. The readers are the composer's own, because the news
# pools that answer it live there (`bot/compose/goodnews.RELIEF`), and a line is only news when
# nothing in it asks: a question mark keeps the whole module.
def _the_thing_has_got_better(text, memory):
    """Whether the line reports that the trouble has passed, so the advice would be stale.

    "the pain has gone", "my knee has healed", "im over the flu now" and "its stopped now" are
    reports on the answer above, not a second ask for it. `reads_as_recovery` reads the ones said
    about the speaker, and `reads_as_settled` the ones said about a thing or a body - that one
    needs a worry on the table, so "its stopped now" about a noise the car was making keeps its
    own answer and does not become a medical relief.
    """
    clean = " ".join(str(text or "").lower().split())
    if not clean or "?" in clean:
        return False
    got_better = goodnews.reads_as_recovery(clean) or (
        goodnews.reads_as_settled(clean) and goodnews.worry_on_the_table(memory or {}))
    # The phrase has to be the end of it: "my cough has gone green" is a cough that has changed
    # colour, and standing the chesty-cough card down for it would answer a symptom with relief.
    return bool(got_better) and goodnews.the_news_is_the_whole_of_it(clean)


# A follow-up that points at one of the cases inside the answer in hand instead of asking its own
# question: "and for a hard one", "what about the soft ones", "how about the big one". It names no
# thing the knowledge base can look up, and the case it points at is written in an answer already on
# the screen, so the words that answer it are there to be read rather than looked up again.
A_CASE_ASK = re.compile(
    r"^(?:and|or|what|how|which|then)\b[^?.]{0,40}\b(?:one|ones|other|another|"
    r"hard|soft|big|small|large|little|medium|old|young|dark|light|cheap|quick|slow)\b", re.I)
# The words that say where the ask points rather than what it points at: a part found by one of
# these is a part of the sentence, not the case the person named.
A_CASE_STOP = frozenset("""about and another any are can could for from have how i if is it
    its just like long many much my of one ones or other the then to what when which who why
    will with would you your""".split())


def _a_case_of_the_answer_in_hand(text, memory):
    """The words of an answer on the screen that cover the case this line names, or "".

    "how long do i boil an egg" gives 6 minutes for a runny yolk, 7 for jammy and 9 to 10 for hard
    boiled, and "i want it soft" gives the soft one alone - so "and for a hard one" names a case
    that is no longer in the last answer, and the bot answered it with a nod. A friend reads back
    to the answer that covered it. `bot/memory/narrow.py` cuts the clause a line asks for out of a
    paragraph, and it cuts "9 to 10 for hard boiled" out of that answer, so the case is read from
    the answers still on the screen, newest first, and only from an answer of the knowledge base.

    The part has to name what the line names - the word of the case itself - so that a figure out
    of another answer cannot be handed over for a case nobody covered. Nothing is read when the
    line is longer than a pointer ("and what about the soft boiled ones in the morning"), which is
    a line with a question of its own.
    """
    line = " ".join(str(text or "").split())
    if not line or len(line.split()) > 8:
        return ""
    if not A_CASE_ASK.match(line.lower()):
        return ""
    wanted = {word for word in WORD.findall(line.lower())
              if len(word) > 2 and word not in A_CASE_STOP}
    if not wanted:
        return ""
    answers = [str(turn.get("bot")) for turn in reversed(memory.get("turns") or ())
               if isinstance(turn, dict) and turn.get("bot") and turn.get("module") == "answers"]
    # The wider read below is for the turn after a case and no other. When the answer in hand is a
    # fragment ("9 to 10 for hard boiled."), the paragraph it came from has gone off the screen and
    # the card that answers the next case is two turns up. Straight after a whole answer the case
    # is cut out of the newest answer's own clause, and reading further back is how the list of
    # three dinners came back for "and quick" when the chat had moved on to vegetarian dishes.
    after_a_case = bool(answers) and len(answers[0].split()) <= 12
    for answer in answers[:3]:
        try:
            part = length.narrow(answer, text)
        except Exception:  # noqa: BLE001 - a part that cannot be cut is no part at all
            part = ""
        if not isinstance(part, str) or not part.strip():
            part = ""
        # Nothing was cut out of this answer: either narrow found no clause for the line, or the
        # answer is already just that clause. The second is the answer in hand after a case was
        # read - "and for a hard one" leaves the one line "9 to 10 for hard boiled." - and the card
        # before it, "A soft one is the 5 to 6 minute egg...", is the answer to "and the soft one".
        # The whole-answer rule below is there so a paragraph is never handed back; a card that is
        # one sentence with a figure in it is the case itself, and the person asked for it again.
        uncut = not part or (" ".join(part.lower().split())
                             == " ".join(answer.strip().lower().split()))
        if uncut:
            part = answer.strip() if len(answer.split()) <= 30 else ""
        if not part:
            continue
        if not re.search(r"\d", part):
            continue
        # The part is the clause around the figure ("9 to 10 for hard boiled"), never a whole
        # paragraph: "and quick" after a list of three dinners cut the whole list out of the first
        # answer, and read back a dinner they had already turned down (they are vegetarian, so the
        # whole answer was dropped as uneatable and the turn went to the small talk).
        if len(part.split()) > (30 if after_a_case else 14):
            continue
        if after_a_case and len([s for s in re.split(r"(?<=[.!?])\s+", part.strip())
                                 if s.strip()]) > 1:
            # The card two turns up can be two sentences, and the first of them is the case ("A
            # soft one is the 5 to 6 minute egg: 5 for a yolk that still runs, 6 for a set white
            # with a soft middle."). Four sentences cut out is the paragraph coming back.
            continue
        said = {word.rstrip("s") for word in WORD.findall(part.lower())}
        if not any(word.rstrip("s") in said for word in wanted):
            continue
        part = part.strip()
        if part[-1:] not in ".!?":
            # A clause cut out of the middle of a sentence comes back without its stop ("2 to 3
            # minutes a side for medium rare"), and every other reply this bot gives ends on one.
            part += "."
        return part[:1].upper() + part[1:]
    return ""


def _answer(text, memory):
    """The knowledge base's reply, or the answer last given when the line is that line again."""

    if isinstance(memory, dict) and memory:
        from ..memory.when import asks_what_today_is

        if asks_what_today_is(text):
            # "what day is it" asks the calendar, and the chat around it is not part of the
            # question. Read with the thread in hand, the ask lent itself the trip on it: after
            # "we're off to portugal in august", "what day is it" got "Portugal: Lisbon three
            # full days, Porto two". The calendar row answers it with nothing else in hand, and
            # that is what it is answered with here.
            return _answer(text, {})
    if isinstance(memory, dict) and stuck_line.pool(text, memory) \
            and not repeat.answer_for(text, memory):
        # "i dont know what to do" after hard news is a request for the next step, and the stuck
        # reader has the one that fits that kind of news. It is read first, before every reader
        # below, because each of them reads a word of the line on its own: carried into the
        # knowledge base the only reachable word is the hard line's own ("i lost my job yesterday"
        # reads "lost", which is the memory-science row), and read as a plan it reached the
        # cheapest-week list. Standing aside leaves the turn to bot/memory/stuck.py, which reads
        # the class (job, money, a death, an ending) before any single word of it.
        #
        # One reader is excepted, and it is the one that answers the line already: when the reply
        # on the screen was a card with steps in it ("my boyfriend dumped me" -> "Tell two people
        # today..."), the answer to "i dont know what to do" is that reply's own first step, and a
        # neutral pool in its place throws away the specific advice for the generic one. The pool
        # is for the line after a nod, and `repeat.answer_for` says which of the two this is.
        return None
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if A_PLEA_FOR_TIPS.match(str(text or "").strip().lower()) \
            and mem.last_module(memory) == "answers":
        # "Any tips" names nothing at all, and it comes after a card of advice: it asks for more of
        # the answer in hand, and that answer is the composer's to read (the next thing in it, or
        # the plain line that the step stands). Looked up in the knowledge base the line leans on
        # the one before it and can land on a card about something else entirely - "Green
        # vegetables: broccoli or beans steamed for 4 to 5 minutes" for a child who will not eat
        # veg - because the words "any tips" are the only thing the lookup has to go on. A last
        # turn that was a note rather than a card ("Noted: you're moving flat next month.") is
        # the one case where the lookup is what answers the plea, and it is left alone.
        return None
    if isinstance(understood, dict) and understood.get("intent") == "farewell":
        # A goodbye is not a question about the words in it: after an answer about sleep, "night
        # night" reached the sleep entry through the word "night" and read the goodnight as a
        # second ask about sleep, at the moment the person was going to bed. The farewell is the
        # composer's line. The reading only calls a line a farewell when the goodbye is the whole
        # of it, so a line that says something of its own ("night feeds are killing me", "good
        # night routine for a baby") is still answered.
        return None
    if isinstance(understood, dict):
        written = named.the_best_time_to_do_it(text, understood, memory)
        if written:
            # "When is the best time to do it" after the mould on the courgette leaves points at
            # the plants, and the question about the plants is the one the knowledge base has a
            # row for. Written out, it answers; on its own the line only reaches the answer the
            # person has just had, which comes back as the mould card said again.
            said = _ask_a_rewritten_line(written, memory)
            if said and not _said_before(_without_lead_in(said), memory):
                return said
    if isinstance(memory, dict) and _the_thing_has_got_better(text, memory):
        # The same stand-down as the farewell, for a line whose words are not a new ask: the news
        # is answered by the relief pools, and this module's entry is the advice for a trouble
        # that is still there.
        return None
    if isinstance(memory, dict):
        the_moan = _the_ask_behind_a_moan(text, memory)
        if the_moan:
            # "i always get rice wrong" names the thing that comes out badly and nothing else, so
            # every reader below passes it on and the line was answered with the intake form
            # ("Got it. Is there anything you'd like a hand with?") while the card for the thing
            # was in the knowledge base all along - "how do i get rice right" gets it. The moan is
            # written out as that ask and read again; only an answer about the thing they named is
            # taken, so a loose rewrite cannot hand back a card about something else.
            return the_moan
    led = _a_lead_time(text)
    if led:
        # "how long before the day should we order the cake" is a lead time, and the cake's own
        # entry answers how long it keeps. It is read here, before the lookup, because the ask
        # names a length and a thing and every reader below would answer the length of the thing.
        return led
    if isinstance(memory, dict):
        # "i started learning guitar last month" / "my fingers hurt" / "how long should i
        # practise" was the bone-healing card, because the line was read against the complaint
        # about fingers and that card keys both "fingers" and "how long". The practicing is what
        # the ask is about and the guitar is what the chat has been on, so the ask is written out
        # with the guitar and read again. Only a rewrite that reaches an entry giving a length is
        # taken, and only when its answer is not the one already on the screen, so a line whose
        # own answer is the right one keeps the turn it had.
        #
        # The rewrite is only worth taking when it reaches a *different* entry from the one the
        # line reaches on its own. "i started running last month" / "how long should i run for"
        # reached how-often-to-run on its own, which narrows to "20 minutes." - the length asked
        # for - and the rewrite ("how long should i run for running?") reached the same entry and
        # handed back the whole training card instead. When both readings land on the same entry
        # the person has already been answered about the thing they asked about, and there is
        # nothing for this reader to add.
        own = find(understand(text))
        own_answers_the_length = False
        if own is not None:
            own_said = _payload(own, memory, understand(text))
            own_answers_the_length = bool(_answers_a_length(own, own_said)
                                          and _A_DURATION.search(str(own_said or "")))
            # The line's own answer is already a length to spend doing it - "a mile is 20 minutes
            # at a brisk walk ... half an hour a day is the number that earns most of the
            # benefit" for "i started walking every day" / "how long should i walk". A rewrite
            # reaches a card on the same practice with a figure of another kind (steps a day) or
            # the whole training plan, and neither is the length the person asked for, so the
            # line keeps the answer it had.
        for written in doing_it.written_out(text, memory):
            if own_answers_the_length:
                break
            reading = understand(written)
            reached = find(reading)
            if reached is None:
                continue
            if own is not None and reached is own:
                continue
            written_reply = _payload(reached, memory, reading)
            if not _answers_a_length(reached, written_reply):
                continue
            if _said_before(_without_lead_in(written_reply), memory):
                # The chat has had this answer already, and the ask is the same question about
                # the same practice: the part asked is what the person wants back, not the whole
                # paragraph a second time.
                short = length.narrow(written_reply, text)
                if short and not _said_before(short, memory):
                    return short
                continue
            return written_reply
    if a_wish.reading(text):
        # A hopeful aside ("fingers crossed", "with luck", "hope it works") names nothing to look
        # up, and its own words reach whatever they fit: "fingers crossed" after the condensation
        # answer got the entry on fingers going white in the cold, and "with luck" was read as a
        # detail of the answer ("The same goes for the luck: ..."). The wish is the small talk's
        # turn (`bot/memory/hope.py`, answered by `chat`), so the lookup stands aside.
        return None
    if isinstance(memory, dict) and prefer.served_already(text, memory):
        # The same taste a turn after it was answered with picks for it. Every reader below
        # would reach the same entry and hand the same list back, framed as a repeat ("Same as
        # before: *Arrival* is the smartest one ..."), because the taste is the only thing in
        # the line - and the answer last given is the last of those readers. Nothing new can
        # be said about it, so the turn goes to the small talk ("You like sci fi - noted."),
        # which is what the person got before this reader existed.
        return ""
    agreed = repeat.agreement_with_the_answer(text, memory)
    if agreed:
        # The line says the answer back ("low heat, got it" a turn after "Low heat it is."). Read
        # as a fresh question it is answered with the whole paragraph again - the paragraph the
        # person has just agreed with - so the confirmation comes first, the way the repeat
        # below does.
        return agreed
    if isinstance(text, str) and BARE_SAY_NO.search(text):
        # Nothing in the knowledge base names a situation for this ask, but the answer to
        # saying no does not need one. This is the first reader, so the answer does not depend
        # on a lookup that has nothing to match, and it still lets _the_line_again take a
        # repeat, so the line asked twice gets "Same as before" rather than the paragraph
        # again. The regex names only the bare asks - "how do i say no", "how do i refuse" -
        # so "to my boss", "to my mum" and "turn down a request" keep their own entries, and
        # "without sounding lazy" keeps the wording offer.
        return _the_line_again(text, memory) or work.SAY_NO_POLITELY
    # "make it short", "shorter", "in one line", "tldr": the person wants the answer they already
    # have with the detail taken out, and the lead of it is in memory. It comes before the lookup
    # on purpose - a line that names nothing still matches entries on its own words ("keep it
    # brief" reaches the cheese that keeps, "shorter" reaches the one that got shorter) and the
    # reply to a request for less is the answer itself, never a new entry.
    # `repeat` is imported at the top of this file: a local import here would make the name local
    # to the whole function and the agreement check above would raise before it is bound.
    shorter = repeat.shorter_for(text, memory) if isinstance(memory, dict) else None
    if shorter:
        return shorter
    dated = deadline.follow_up(text, memory) if isinstance(memory, dict) else ""
    if dated:
        # A line that is only a date is the plan said a turn ago with the date on it: "we want to
        # save 3000 pounds" / "by december" asks how the plan goes against December, and the goal
        # alone only gets the general advice. It is read that way here, before the lookup, because
        # the topic path answers a bare date with the answer already on the screen.
        answer = _ask_a_rewritten_line(dated, memory)
        if answer and _the_same_answer_again(answer, memory):
            # The date bought nothing - the entry says the same thing with it as without it - so
            # the person would hear "Same answer, and it covers this" at a line that added
            # something. The turn is then read exactly the way it was before this module.
            answer = None
        if answer:
            return answer
    # A line whose subject is a bare "he" or "she", in a chat that is on an animal, is about that
    # animal: "we got a puppy last week" then "he keeps biting the kids" was answered from the
    # entry for a child who bites at nursery, and the one after "we got a dog in the summer" came
    # back as the nod, because the pronoun is the subject of the question and nothing had put the
    # animal in its place. The store says which animal only when the reading points the pronoun at
    # one it holds and the filled line lands on an entry keyed on that animal
    # (`topics.the_animal_the_subject_is`). It is asked below, after the line itself, so a line
    # that already has an answer keeps it: "he cries when i leave the room" straight after the
    # puppy and a sleepless night is the separation answer, not the one on leaving a dog alone.
    animal = the_animal_the_subject_is(understood, memory) if isinstance(memory, dict) else None

    back_to = said_topic.the_thing_asked_again(memory, text) if isinstance(memory, dict) else ""
    if back_to:
        # "back to lisbon, what should i see" goes back to a thing and asks about it in one
        # breath. Read as it is typed the line is answered for its own words - "back" is a body
        # part - so the back-pain card answered a question about Lisbon. The store has just put
        # the thing back on the table, so the line is read with it in front of the ask.
        thing = said_topic.the_thing_went_back_to(memory)
        reached = find(understand(back_to, memory))
        if reached is not None and any(_the_entry_names(reached, word)
                                       for word in thing.split() if len(word) > 3):
            # The card the rewritten line reaches has to be the one about the thing they went
            # back to: written with the thing in front, a line about pricing a carboot reaches
            # the card on raising your freelance rate, which shares the asking and nothing else.
            answer = _ask_a_rewritten_line(back_to, memory)
            if answer:
                # The same question asked again a few turns later is worth the answer again,
                # framed as the repeat: they asked what to see in Lisbon, went on to something
                # else, and came back to it. `_said_before` would stand the reader down and hand
                # the line to the card its own words fit, which is the fault this reader is for.
                return same_again.instead(answer, text, memory) or answer
    # A line asking which part of the answer to do first is answered out of the answer in hand,
    # before the lookup. It names nothing of its own, so the lookup can reach a neighbour of that
    # answer instead: "where do i start" after "im trying to save money" reached the card on where
    # to borrow, and the person asking which step of the plan to do first got a loan. `_last_answer`
    # is no help here - a bare ask shares no word with the answer, so the run is read as ended -
    # and the line in front is all the step reader needs.
    if repeat.asks_which_part(text) and not _a_city_card_asks_which_first(text, memory):
        # A city card is a list of places to go, not a list of steps, and the card's second
        # sentence is a local habit rather than one of them: "what should we do first" after the
        # Barcelona guide came back "The thing to do first: Eat lunch at 2pm like locals." The
        # city's own row answers which of the places comes first (`city-next`), so this reader
        # stands down and the lookup has the turn.
        step = repeat.the_move(text, _the_answer_in_front(memory), memory)
        if step:
            return step
    case = _a_case_of_the_answer_in_hand(text, memory) if isinstance(memory, dict) else ""
    if case:
        # "and for a hard one" after the answer gave one of the cases: the case is written in an
        # answer above, so it is read from there rather than looked up as a question of its own.
        # Before the lookup, because the words of the line reach nothing on their own and the
        # greeting pool answered it with a nod ("For a hard one - noted.").
        return case
    if limit.reads_the_answer(text, memory):
        # The line limits the answer just given, whichever reader below would take it: this one
        # answers from that answer's steps, and the carry below would ask the knowledge base again
        # with the limit on the end of the question ("oven cleaner" reached a food answer here).
        return None
    if TAKEN_BACK_OPENER.match(str(text or "")) and "?" not in str(text or "") \
            and len(str(text or "").split()) <= 5:
        # A line that opens by withdrawing something is a take-back, not a question. The store
        # answers it ("Right - no dog, then") and the word "forget" must not reach the entry on
        # forgetting, which read "forget the dog" as a question about memory. A real ask about
        # forgetting says its question - "how do i stop forgetting things" - and is untouched.
        return None
    back_to = went_back.a_return_to_the_topic(text, memory) if isinstance(memory, dict) else ""
    if back_to:
        # "back to lisbon, what should i see" takes the chat back to a thing it has already
        # named and then asks about it. Read whole, the line reached the entry on a bad back:
        # "back" is the return, not the body part, and the thing they named never got to the
        # question. With the thing written into the ask ("what lisbon should i see") it reaches
        # the entry filed for it, which is `bot/memory/returns.py`.
        answer = _ask_a_rewritten_line(back_to, memory)
        if answer:
            if _said_before(_without_lead_in(answer), memory):
                # The return lands on the answer already on the screen: it is still the answer,
                # and it is said as the same one rather than word for word a second time.
                return went_back.as_the_same_answer(
                    answer, text, short=_repeat_short(answer, back_to))
            return answer
    again = named.a_measure_asked_again(text, memory) if isinstance(memory, dict) else ""
    if again:
        # "how long does it take to fit a new one" after the chat has been about a boiler: the
        # line names no thing, so on its own it reaches the entry that answers how long a boiler
        # is built for. Written as the question it is, it reaches the row that knows how long a
        # fitting takes. Read before the lookup, because that wrong entry does answer the line
        # as it stands and would take the turn.
        answer = _ask_a_line_of_its_own(again, memory)
        if answer and not _the_same_answer_again(answer, memory):
            return answer
    trip = named.a_part_of_the_trip(text, memory) if isinstance(memory, dict) else ""
    if trip:
        # "and where should i stay" after a trip to Rome is the question with the place written
        # in, and the card filed for that question is the one that knows: asked bare, the line
        # reached whatever the chat's newest words fit, and the day trips out of Rome answered
        # where to stay.
        answer = _ask_a_rewritten_line(trip, memory)
        if answer:
            # The same card twice in a row is not a second answer, but it is the right card:
            # "whats the food like" asked after the city card reached nothing at all and got the
            # search hedge, and said again with a lead-in it at least names Trastevere for dinner.
            # A yes/no ask about the part is not the card said again. "is three days enough" after
            # the days card asks for a verdict on the three days, and the card on the screen
            # cannot give one: saying "That was the whole of my answer on it" answers their
            # question with a remark about the bot. Where the card has already been read, the line
            # is left to the modules that hedge - the same honest reply the chat got before the
            # card - rather than handed a claim that it already had everything.
            if not _A_YES_NO_ASK.match(str(text or "").strip()):
                again_told = same_again.instead(answer, text, memory)
                if again_told:
                    return again_told
            if not _said_before(_without_lead_in(answer), memory):
                return answer
    # A plan moved to a day, rather than to a time: "im cooking chilli for 6" / "can i make it
    # friday night instead". The line names a day and a move and nothing to answer with, so the
    # turn came back as the search hedge, or as the ingredient-swap card because "instead" is how
    # a swap is asked for. Whether it can be made on Friday is whether it can be made ahead, which
    # the kitchen already answers for "can i make it the day before": the day goes out of the line
    # and "ahead of time" goes in, and the reply says the day out loud so the move is read back.
    # Only where the rewritten line answers and the answer is not the one already on the screen, so
    # a line whose subject has nothing to say about being made ahead keeps the turn it had.
    moved = when.a_plan_moved_to_a_day(text) if isinstance(memory, dict) else None
    if moved:
        answer = _ask_a_rewritten_line(moved["line"], memory)
        if answer and not _said_before(_without_lead_in(answer), memory):
            day = moved["day"]
            return day[:1].upper() + day[1:] + " works. " + answer
    if tried.reads_as_a_step_done(text, memory):
        # A step of the answer just given, said as done ("ive cleaned the filter" after "my
        # washing machine smells"): the memory lane walks the answer from there, and every reader
        # below asks the knowledge base about the words of the line instead - "filter" reached
        # the vacuum cleaner's filter, so a person with a smelly washing machine was told how to
        # clean a vacuum. The step is the answer's own, and the store has it.
        return None

    # A follow-up that names a part of the thing the person named is about that thing, even when
    # the turn before it was about a different part. "my washing machine smells" / "i clean the
    # filter" / "and the drawer every month": the drawer's owner is still the machine, and the
    # newest turn's words have lost it, so the part joined to those words reaches no entry and the
    # line fell to the pantry card that is keyed on the bare word "drawer" - a cupboard clear-out
    # as the answer to a washing machine's detergent drawer. Read before the lookup, because the
    # pantry card does answer the words of the line as it stands, and the part of the machine is
    # the thing the person asked about.
    part_owned = _the_part_of_the_thing_they_named(text, memory)
    if part_owned:
        return part_owned
    # A food or drink question whose only subject is "he" or "she" is about the animal the
    # chat is on: "my dog is 8 and a bit overweight" / "can he have cheese" reached the cooking
    # rows and came back as an omelette, and a rabbit's carrot as vegetable soup. With the
    # animal written into the line the pet rows reach it, exactly as they do when the person
    # names it themselves. A person's pronoun is left alone by `_pet_in_the_talk`.
    animal_line = pets.the_animal_follow_up_line(text, memory)
    if animal_line:
        animal_answer = _ask_a_rewritten_line(animal_line, memory)
        if animal_answer:
            return animal_answer
    answer = _respond(text, memory)
    if animal is not None and (
            not answer or answers_about_another_creature(answer, animal.get("clean") or "")):
        filled = _ask_a_rewritten_line(animal.get("clean") or "", memory)
        if filled and not _the_same_answer_again(filled, memory):
            answer = filled
    if _asks_only_the_length(text):
        # Both when the answer came back as the last paragraph again and when the lookup found
        # nothing at all: a length ask about an answer that holds no time gets the honest line.
        honest = _a_length_ask_with_no_figure(text, memory, answer or "")
        if honest:
            return honest
    measure = named.about_the_subject(text, memory) if isinstance(memory, dict) else ""
    if measure:
        # A line that only points back - "how long should it be", "how much would that cost" -
        # names nothing, so what it reaches is whatever the topic's newest words fit: after
        # "im thinking of getting a dog" / "it would be for the kids" the child bus fares, and
        # where nothing fits it, the search hedge. Written about the subject of the chat the same
        # line reaches the entry that knows it ("how much would the dog cost"), and that entry
        # takes the turn when it names the subject and the line on its own does not.
        said_about_it = _a_measure_about_the_subject(measure, text, memory, answer)
        if said_about_it:
            return said_about_it
    if answer:
        # An answer that is word for word the one the person has just had is not a second answer:
        # it happens when the line reaches the entry through the thing under discussion rather
        # than on its own ("my kitchen tap is dripping" gets the washer answer, then "i tried
        # turning it really hard and now its worse" reaches the same washer answer through the
        # tap). Said twice running, the bot is talking at the person; the short form behind a
        # lead-in is the same answer, said the way a friend says it a second time.
        if (isinstance(text, str) and _A_BARE_MEASURE.fullmatch(text)
                and re.search(r"\d", str(answer))
                and (SIGNALS["amount"].search(answer) or SIGNALS["money"].search(answer))):
            # The bare ask got the figure on the screen back. It is the same words as the answer
            # above, but the repeat frame ("Same as before: A banana is about 105 calories") is
            # a pointer at the card rather than the figure, and a how-much line is owed the
            # figure. Said plainly, it is the answer.
            return answer
        said = _answer_said(answer, memory) if _flat(answer) == _flat(mem.last_bot(memory)) else 0
        if said:
            if said >= 3:
                return AGAIN_HELP.format(reply=_repeat_short(_without_lead_in(answer), text, memory))
            return AGAIN[said - 1].format(reply=_repeat_short(_without_lead_in(answer), text, memory))
        # The short form of the answer just given, on a line that names something else, is not a
        # second answer either. "im going to lisbon in may" gives the city card, and "what about
        # the food" reaches the same card and comes back as its first sentence, so the person who
        # asked about food reads the sights again with nothing saying why. The paragraph is on the
        # screen directly above, so the turn says in one sentence where the answer is rather than
        # reading it out again behind four words of lead-in - `bot/memory/again.py` has those
        # lead-ins for the turn where the answer has not been read yet, and this is not that turn.
        short_of_it = _short_form_of_the_last(answer, memory)
        fact = bool(short_of_it) and _a_fact_about_the_person(memory)
        detail = ""
        if short_of_it and not ASKS_ABOUT_HOW_IT_TURNED_OUT.search(text):
            # A part the answer names is a part, even in a sentence ("i looked at the trams").
            # A bare word the person's own sentence happens to share with the paragraph is not:
            # `_the_detail_named` walks back over the line to the newest keyword and holds it up
            # as the part, so "i work nights" named "nights" after an answer that says "late
            # night" about a dog. So the fact test comes before that guess and after the name.
            detail = (_a_part_named_in_the_line(text, memory, short_of_it)
                      or ("" if fact else _the_detail_named(text, memory)))
        if detail:
            if _named_in(short_of_it, detail):
                # The answer names the part, so it has something to say about it, and a sentence
                # about the conversation ("Everything about insurance is in what I said above")
                # withholds the one clause that answers the line. "how much does a cat cost to
                # keep" prices insurance in passing (8 to 20 a month) and the follow-up "what
                # about insurance" was told there is no more than that - which is not true, the
                # figure is in the paragraph. The clause that names the part is the answer.
                part = _the_part_in_the_answer(short_of_it, detail)
                if part:
                    return part
            return NOTHING_SEPARATE[0].format(detail=detail)
        if fact and _only_a_quality_name(text, memory):
            # The only name in the line is a word that says what the thing is like ("a new"), and
            # that names no part of the answer: there is nothing for a lead-in to say about it and
            # the answer is already on the screen, so the repeat is answered as a repeat. Standing
            # down said "I'm not sure about that one, sorry" to a question the card answers.
            return AGAIN[0].format(reply=_repeat_short(short_of_it, text, memory))
        if fact:
            # A part the answer above does not name is not a part of it, and no paragraph is the
            # whole of a fact about themselves, so the turn goes to the parts of the bot that
            # answer a person saying something about themselves.
            return None
        if short_of_it and _their_own_state(text):
            # The same goes for a line that says where the person has got to without asking
            # anything of the thing: "i dont know why" after the low-mood card was read as the
            # part of the answer named "dont" and given a sentence of the card again, and after
            # "my 3 year old wont eat vegetables" it reached the question about why the sky is
            # blue. A line that is the person's own state is theirs.
            return None
        return answer
    carried_on = more.reply_for(text, memory) if isinstance(memory, dict) else None
    if carried_on:
        # "tell me more", "go on" - the whole line is a request to carry on, and the answer it
        # asks about is the one just given: nothing can look it up, so the reply says plainly
        # how much there is and hands the turn back with a question that can be answered.
        return carried_on
    # A report of a sore or a trouble ("i get heartburn after meals") is not a question, but a
    # friend hears one: what can I do about it. Read that way against the health answers only, so
    # "i have two kids" keeps the warmer pool, and only where the line reached nothing at all.
    if tried.might_be_a_report(text) and tried.pool_for(text, memory):
        # The line reports on the answer it followed, and the state word in it is the thing's, not
        # a new subject: "my shower is cold" then "still cold" was read as a fresh complaint and
        # answered with the common cold ("two or three days and gone in about a week"). Every
        # reader below looks the words of the line up, so the report stands the module down and
        # `chat` says the next step (`bot/memory/tried.py`).
        return None
    understood = memory.get("understood")
    if not isinstance(understood, dict):
        understood = understand(text, memory)
    if (understood or {}).get("kind") == "statement":
        told = _a_complaint_answered(text, understood, memory)
        if told is not None:
            return told
    carried = named.follow_up(text, memory) if isinstance(memory, dict) else ""
    from_a_taste = False
    if not carried:
        # "i like sci fi" after the film list is a request for the science fiction one, and the
        # medium it omits is in the answer just given (`bot/memory/prefer.py`).
        carried = prefer.follow_up(text, memory) if isinstance(memory, dict) else ""
        from_a_taste = bool(carried)
    if carried:
        # The line names a thing and asks nothing, and the line before it asked for
        # suggestions: "my mum is coming to stay" / "what should i cook" / "and a pudding" is
        # still that request, about a pudding. Read the ask the line carries and answer that.
        # Only when the line itself has no answer (above), so nothing that answers today moves.
        answer = _ask_a_rewritten_line(carried, memory)
        if answer and (_same_as_the_last_answer(answer, memory)
                      or _the_same_answer_in_other_words(answer, memory)):
            # A carried ask has to buy the person something they have not just had. "what else"
            # after the film list is a request for a second pick, and an entry that hands the same
            # three titles back over again has read nothing: the turn is better spent on the
            # composer's answer to the line than on the list already on the screen.
            answer = None
        if answer and from_a_taste and not prefer.about_the_medium(answer, memory):
            # "i like crime" after the film list reaches an entry with no crime films and hands
            # the same three films over again: the person hears the list they have just heard,
            # with no sign it was read. A taste that buys nothing new stands down and the small
            # talk takes the turn. So does a taste that buys something from another domain: the
            # ask is written with the medium on the end of it ("any good light books"), and an
            # entry that shares only the taste word with it (a soup for "light", a walk for
            # "walk") answers a question the person did not ask.
            answer = None
        if answer:
            return answer
    # A line that reports where the thing in hand stands ("its on 4%", "it still smells") names no
    # subject of its own, so the knowledge base cannot reach it and the turn came back as the
    # report said back at the person ("Got it — it's on 4%."). Read with the thing written in
    # ("my phone is on 4%") the same line reaches the entry that knows it. Only where the line
    # answered nothing at all and the answer is not the one already on the screen, so no turn that
    # answers today moves; the first read that answers takes the turn.
    if isinstance(memory, dict):
        for in_hand in named.reported_states(text, memory):
            reached = find(understand(in_hand, memory))
            if not _the_report_is_answered(text, reached):
                continue
            answer = _ask_a_rewritten_line(in_hand, memory)
            if answer and not _said_before(_without_lead_in(answer), memory):
                return same_again.instead(answer, text, memory) or answer
    # A fact about the person, said with no subject of its own, is the subject on the table asked
    # about with the fact on it: "pension" then "im 34 and self employed" reached nothing and the
    # turn came back as "Got it. Is there anything you'd like a hand with?". Written with the
    # subject in front ("pension im 34 and self employed") the same line reaches the entry that
    # needs both halves - the pension one for the self employed. Only an entry keyed on the fact
    # the person stated takes the turn, so a read that reaches a neighbour of the subject by a
    # word-mate ("party for a 7 year old" reaching a party card that says nothing about age) is
    # no answer and the small talk keeps the turn.
    if isinstance(memory, dict):
        for stated in named.stated_about_the_person(text, memory):
            reached = find(understand(stated, memory))
            if not _the_fact_is_what_is_answered(text, stated, reached, memory):
                continue
            answer = _ask_a_rewritten_line(stated, memory)
            if answer and _most_of_it_said(answer, memory):
                # the fact moved nothing: the same card answered, with a lead-in in front
                continue
            if answer and not _said_before(_without_lead_in(answer), memory):
                return same_again.instead(answer, text, memory) or answer
    # A practice the person keeps with the thing in hand ("i feed them every week" after tomato
    # plants) has the same shape as a report: no subject of its own, so no entry is reached and the
    # turn came back as the practice said back at the person. Written with the thing in front
    # ("tomatoes feed every week") the same line reaches the entry that knows when and how often.
    if isinstance(memory, dict):
        for practice in named.care_reports(text, memory):
            reached = find(understand(practice, memory))
            if not _the_practice_is_answered(practice, reached):
                continue
            answer = _ask_a_rewritten_line(practice, memory)
            if answer and not _said_before(_without_lead_in(answer), memory):
                return same_again.instead(answer, text, memory) or answer
    bare = named.about_it(text, memory) if isinstance(memory, dict) else ""
    if bare:
        # A bare thing after a turn about something is that thing asked about ("frosting" after
        # "im making a cake"), and the entry for it is what the person wants. The sentence of the
        # last answer that names the thing comes first: it is the same answer's own words about it.
        answer = _ask_a_rewritten_line(bare, memory)
        if answer:
            short = _the_sentence_about(text, memory) or _the_sentence_about(bare, memory)
            if short and _flat(short) != _flat(answer):
                return short
            if not _said_before(_without_lead_in(answer), memory):
                return same_again.instead(answer, text, memory) or answer
    part = named.about_the_thing(text, memory) if isinstance(memory, dict) else ""
    if part and _the_part_is_what_answers(part, memory):
        # The line names a part of the subject and asks nothing: "im going to spain" / "and its
        # population" is a question about Spain, and the knowledge base has the entry under
        # "population of spain". Only when the line on its own found nothing (above) and it does
        # not carry the ask before it, so nothing that answers today moves: the part has to
        # reach an entry of its own to take the turn.
        answer = _ask_a_rewritten_line(part, memory)
        # A part the entry answers by reading its paragraph out again is the answer they were
        # given a turn ago: "im visiting lisbon" / "and the food" reached the Lisbon card a
        # second time. The part has to be new to take the turn, so the answer on screen stands
        # and the line falls back to the follow-up paths.
        if answer and not _said_before(answer, memory):
            return answer
    person = matters.about_them(text, memory) if isinstance(memory, dict) else ""
    if person:
        # "my mum is 78 and keeps falling" / "she lives alone" is a fact about the person the
        # answer was about, and written out with her in it ("my mum lives alone") the knowledge
        # base answers it: the free care needs assessment, the pendant alarm, the key safe. The
        # store's reply to the line as typed is the receipt STYLE.md rules out ("Got it - she
        # lives alone"), with the one fact that matters left unused. Only an answer that is not
        # the one already on the screen takes the turn.
        answer = _ask_a_rewritten_line(person, memory)
        if answer and not _said_before(answer, memory):
            return answer
    # Every reader above is done and there is no answer: the line would be a search hedge, and the
    # answer already on the screen speaks to the trouble in it ("i burnt the rice" / "can i still
    # eat it"). Last, so an entry that answers the line as it stands always beats a repeat of the
    # turn above it: see _the_answer_on_the_table.
    said_on_the_table = _the_answer_on_the_table(understood, memory)
    if said_on_the_table:
        return said_on_the_table
    return _the_line_again(text, memory)


# A reply cut out of the answer on the screen is not a reply when it is only a clause of it: the
# figure a price ask pulls out of a paragraph ("£100 to £200" out of "pads are 100 to 200 and a
# front set with discs is 200 to 350"). Any longer and the part stands on its own.
_A_CLAUSE_OF_THE_ANSWER = 14


def _a_measure_about_the_subject(measure, text, memory, alone=""):
    """The answer to a measure ask that points back, asked about the subject of the chat.

    "how much would that cost" after "im thinking of getting a dog" is a question about the dog,
    and the entry that answers it ("pet-cost") is only reached when the subject is in the line. The
    line on its own, with nothing of its own to match, reaches the entry the topic's newest words
    fit ("it would be for the kids" gave the child bus fares) or nothing at all, which is the
    search hedge. Three things have to hold before it takes the turn:

    - the entry the written-in line reaches names the subject, not only the asking;
    - the entry the line on its own reaches does not name the subject (so nothing that answers
      today moves);
    - where the subject alone is not enough, the plan the chat is on goes in as well: "how long
      should the speech be" names no occasion, and "my sister is getting married in june" does.
    """
    # A bare "how much" whose answer already carries a figure is answered: the rewritten line
    # ("how much drink") reaches a clause without one ("Drink a few mouthfuls every 15-20 minutes")
    # and the repeat reader framed that as the answer. The figure on the screen is the answer, and
    # only a figure the line did not get sends the ask through the rewrite.
    if (alone and re.fullmatch(r"\s*how (?:much|many)\s*[?.!]*", str(text or ""), re.I)
            and asked_kind(text) == "amount"
            and SIGNALS["amount"].search(str(alone))):
        return ""
    word = named.subject_word(memory)
    if not word:
        return ""
    if named.a_newer_thing(memory, word):
        # The line before the ask named something they need, so the ask is about that and the
        # subject the chat opened with is stale: "it needs a new spring" / "how much would that
        # cost" is the price of the spring, not the price of the MOT test.
        return ""
    # The thing on the table has stopped working, so the measure asked about it is the repair's:
    # "my boiler is broken" / "how long will it take" wants the visit, not the boiler's ten to
    # fifteen years, and the entry that knows it is filed under the boiler and the repair. Asked
    # first, and only where an entry about getting the thing mended names the thing, so a fault the
    # knowledge base has nothing for falls through to the paths that were there before.
    reached = None
    faulty = named.a_faulty_thing(memory)
    if faulty and not _A_HOW_LONG.search(measure):
        # Only a length ask moves. "how much will that cost" about a broken thing is answered well
        # by the rows that were already answering it (a repair is £60 to £120, a phone screen £60 to
        # £120), and the repair's *time* row is no answer to a price: the price of a cooker's repair
        # reached the car repair row, said how long a garage keeps a car, and the figure they asked
        # for never came.
        faulty = False
    if faulty:
        # The phrase naming the thing, not the one word of it: "the washing machine" reaches the
        # washing machine's repair row where "the machine" reaches the row about how long a wash
        # cycle runs. `named.the_thing` is the subject with the words for how it is taken out.
        thing = named.the_thing(memory)
        phrased = measure
        if thing and word and ("the " + word) in measure and thing != word:
            phrased = measure.replace("the " + word, "the " + thing, 1)
        asked_lines = [phrased.replace("the " + thing, "the " + thing + " repair", 1)
                       if thing and ("the " + thing) in phrased else phrased + " repair",
                       phrased + " repair"]
        if thing:
            # The row about a repair is only reached by a line that says how long a repair takes
            # and not how long a cycle runs: "how many days for a washing machine repair" is that
            # line, where "how long will the washing machine repair take" is the cycle's.
            asked_lines.append("how many days for a " + thing + " repair")
        for said in asked_lines:
            asked = find(understand(said, memory))
            if not (asked is not None and _the_entry_names(asked, word)
                    and _names_a_repair(asked)):
                continue
            told = _ask_a_rewritten_line(said, memory)
            if not told or _flat(told) == _flat(alone):
                # The row that answers the written line is the thing's own row again ("Six years."
                # for a cooker whatever the wording), so this candidate buys nothing: the ask has
                # to bring the repair's answer, not the same one under a different sentence.
                continue
            measure, reached = said, asked
            break
    if reached is None:
        reached = find(understand(measure, memory))
    if faulty and _A_HOW_LONG.search(measure) and not _names_a_repair(reached):
        # A broken thing asked how long is not asking how long the thing lasts: without an entry
        # that names the repair, the life of it ("Six years.") would be handed over as the answer
        # to getting it mended, and the paths below were giving nothing better. Stand down instead.
        return ""
    if reached is None or not _the_entry_names(reached, word):
        if named.is_a_progress_ask(text) and named.a_figure_on_the_doing(memory, word):
            # A progress ask about a doing the plan put a figure on is already the whole question:
            # "how long until im good at running" answers how long it takes to be able to run one,
            # and putting the plan on the end adds its figure, which reaches the row for how long a
            # 5k takes to *run*. A plan with no figure in it ("i started running") is a different
            # case, and there the plan's words are what find the timeline.
            told = _ask_a_rewritten_line(measure, memory)
            if told:
                return told
        plan = _the_plan_said(memory)
        if not plan:
            return ""
        measure = measure + " " + plan
        reached = find(understand(measure, memory))
    if reached is None or not _the_entry_names(reached, word):
        return ""
    if _the_entry_names(find(understand(text, memory)), word) and not (
            faulty and _names_a_repair(reached)):
        # The line on its own reached an entry that names the thing, which is the case this keeps
        # safe - except on a fault, where the entry it reaches is the life of the thing ("Six
        # years." for a fridge that has stopped) and the repair row is the answer that was asked
        # for.
        return ""
    if alone and word in _flat(alone):
        # The answer the line gets on its own already talks about the subject: it is about the
        # right thing and only the wording differs. "im learning spanish" / "how long until im
        # good at it" is answered with the Spanish hours, and the written-in line reached the
        # language row that says "Spanish, French or Italian" instead, which is the same answer
        # with less of the person in it.
        return ""
    answer = _ask_a_rewritten_line(measure, memory)
    if not answer:
        return ""
    if _the_line_already_has_its_answer(alone, text) and not (
            faulty and _names_a_repair(reached)):
        # A fault is the exception: "my washing machine has stopped" / "how long will it take" got
        # the life of the machine ("Six years."), and that short figure is the answer to a question
        # nobody asked. Where an entry about the repair names the thing, the repair's clock is the
        # answer and it takes the turn.
        # In a chat about reheating rice, "how long in the microwave" is answered with the rice's
        # own time by the cooking path, which is not an entry the line reaches: the figure they
        # asked for is already on the way. The rewrite is for a line that got the appliance's
        # lifespan or the search hedge, so a short answer with a figure in it is kept as it is.
        return ""
    if same_again.unframed(answer):
        # The written-in line reached an answer that is already on the screen: the rewrite found
        # nothing the line on its own did not have, and a repeat lead-in in front of the same
        # paragraph ("Nothing separate for the oven - it is the same advice: 30 to 40 minutes")
        # reads worse than the figure the line gets on its own. Only a rewrite that brings a new
        # answer takes the turn.
        return ""
    # An ask the answer already covers pulls a clause out of the paragraph on the screen, and a
    # clause on its own is not a reply: "the price" after the price of a brake job gave
    # "£100 to £200.", which is the pads alone out of a sentence that went on to say the job with
    # discs is 200 to 350. The whole of that sentence, framed as the answer already given, is
    # what a friend says.
    last_said = _flat((mem.last_bot(memory) or ""))
    whole_amount = (asked_kind(text) == "amount"
                    and SIGNALS["amount"].search(str(answer or "")) is not None)
    if (last_said and _flat(answer) in last_said
            and len(_flat(answer).split()) < _A_CLAUSE_OF_THE_ANSWER and not whole_amount):
        return same_again.instead(str(mem.last_bot(memory) or ""), text, memory) or ""
    # The same answer twice in a row is not a second answer: "how many words is that" after the
    # length of the speech gets the length again, framed as the repeat it is.
    again_said = same_again.instead(answer, text, memory)
    if again_said and not whole_amount:
        return again_said
    if _said_before(_without_lead_in(answer), memory):
        return ""
    return answer


# The words a short answer can be and still be the whole of what was asked: "2 to 4 minutes.",
# "about 20 minutes", "an hour and a half".
_A_SHORT_ANSWER = 12


def _the_line_already_has_its_answer(alone, text):
    """Whether a bare length ask already got a short answer with a figure in it.

    Only a line that asks for nothing but the length, because that is the case this keeps safe: a
    microwave asked how long takes the microwave's own time out of the answer above it, and that
    figure is the answer. A measure ask about the subject - "how much would that cost" - is a
    different case: the short figure the line gets on its own is a clause cut out of an older
    answer ("£1,500 to £2,000." out of what a dog costs a year), and the written-in line reaches
    the entry that answers the cost properly. A clause on its own is not a reply, so the rewrite
    takes that turn.
    """
    if not _asks_only_the_length(text):
        return False
    said = _flat(alone or "")
    if not said or not A_FIGURE.search(said):
        return False
    return len(said.split()) <= _A_SHORT_ANSWER


# A line asking for a length of time, in any of the ways people ask it.
_A_HOW_LONG = re.compile(r"\bhow\s+long\b", re.I)
# The words an entry about getting a thing mended is keyed on: "repair-time" and the cost rows for
# a boiler, a washing machine, a phone screen. A row about the thing itself ("How long does a
# washing machine last") names none of these, which is how the two are told apart.
_A_REPAIR = re.compile(
    r"\b(?:repair|repairs|repaired|fix|fixes|fixed|fixing|install|installs|installed|"
    r"installation|engineer|plumber|electrician|callout|call-out|call out|swap|swapping|job|"
    r"visit)\b", re.I)


def _names_a_repair(entry):
    """Whether the entry is about getting the thing mended rather than about the thing itself."""
    if entry is None:
        return False
    flat = " ".join(str(group) for group in (getattr(entry, "key", ()) or ()))
    return bool(_A_REPAIR.search(flat))


def _the_entry_names(entry, word):
    """Whether the entry is keyed on the thing itself ("dog"), not only on the asking ("cost")."""
    if entry is None or not word:
        return False
    flat = " ".join(str(group) for group in (getattr(entry, "key", ()) or ())).lower()
    return bool(re.search(r"\b" + re.escape(word) + r"\w*", flat))


def _the_plan_said(memory):
    """The plan the chat is on, in the person's own words ("my sister is getting married in june")."""
    known = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    return " ".join(str(known.get("plan") or "").split())


# The words of the part in a "part of <subject>" question, as the person said them: "cost" out
# of "cost of boiler".
_PART_OF = re.compile(r"^\s*(?P<part>[a-z][a-z -]{1,24}?)\s+of\s+", re.I)


def _the_part_is_what_answers(part, memory):
    """The entry a part ask reaches has to be keyed on the part, not only on the subject.

    "and the cost" after "my car is making a noise" is a price, and the entry the subject reaches
    is the diagnosis: it says nothing about a price, so the part is not answered and the turn
    falls back to the follow-up paths that were there before. "and the capital" after a trip to
    Spain reaches the entry filed for "capital of spain", which is the part's own entry, and that
    one takes the turn. A part with no entry of its own is left alone exactly as it was.
    """
    named_part = _PART_OF.match(part or "")
    if not named_part:
        return True
    wanted = {word for word in _PART_OF_WORDS.findall(named_part.group("part"))}
    if not wanted:
        return True
    item = find(understand(part, memory))
    if item is None:
        return True  # nothing is filed for it: the paths below are the only chance it has
    said = _key_words(item)
    return bool(wanted & said)


_PART_OF_WORDS = re.compile(r"[a-z]{3,}")

# A part is attached to the turn before it by a word: "and the drawer", "what about the drum",
# "the belt too", "and its population". A bare noun phrase ("the drum") and a report ("the drawer
# every month") are lines about the part in their own right, and the lookup answers those.
_ATTACHED_TO_THE_LAST_TURN = re.compile(
    r"\b(?:and|also|plus|too|what about|how about|its|it's|their|his|her)\b", re.I)


def _the_part_of_the_thing_they_named(text, memory):
    """The answer about a part of the thing the person named, or "".

    A part follows the chat's subject for as long as the chat is about it, and the newest turn's
    words are not always that subject: after "my washing machine smells" / "i clean the filter"
    the reading joins "and the drawer every month" to "clean filter", which is no entry at all,
    and the line falls to whatever is keyed on "drawer" alone. The machine is what the person
    named, so the part is joined to that, and only an entry that is keyed on the part (the drawer
    card, not the machine's smell card read out again) and an answer the person has not already
    had takes the turn.
    """
    if not isinstance(memory, dict):
        return ""
    owner = named.the_thing_named(memory)
    if not owner:
        return ""
    part = named.about_the_thing(text, memory, owner=owner)
    on_its_own = named.about_the_thing(text, memory)
    if not part or not on_its_own or part == on_its_own:
        # No part at all, or the line is not a part follow-up. A bare "the drum" after "my
        # washing machine is noisy" is a line about the drum on its own, and the lookup already
        # answers it; "the drawer every month" is a report, and the line's own subject. Only a
        # part attached to the turn before it ("and the drawer", "what about the drum", "the
        # belt too") is asked about the thing the person named.
        return ""
    if not _ATTACHED_TO_THE_LAST_TURN.search(text):
        return ""
    if _the_part_is_what_answers(on_its_own, memory):
        # The reading from the newest turn's words does reach an entry of the part's own, so the
        # answer already on the table is that entry's and this reader has nothing to add. Only a
        # part the newest turn's words lose is written under the thing the person named.
        return ""
    if not _the_part_is_what_answers(part, memory):
        return ""
    filled = _ask_a_rewritten_line(part, memory)
    if not filled or _said_before(filled, memory):
        return ""
    return filled


def _the_report_is_answered(text, entry):
    """The entry the report reaches has to be about the state, not only about the thing.

    A report written with its thing in ("my phone is on 4%") reaches whatever the thing and one
    other word fit, and that is not necessarily an answer: "my phone is fine now" reached a line
    about skipping breakfast, and "my battery is on 4%" reached how a battery works. The state is
    what the person said something about, so the entry has to be keyed on it too - the shape a
    figure is read as ("4%" as a charge level), or the word the person used for it ("still",
    "warm", "smells"). Where nothing is keyed on the state, the line keeps whatever answer it had.
    """
    if entry is None:
        return False
    said = " ".join(str(text or "").lower().split())
    keys = []
    for part in getattr(entry, "key", ()) or ():
        for alternative in (part if isinstance(part, (tuple, list, frozenset, set)) else (part,)):
            if isinstance(alternative, str):
                keys.extend(alternative.lower().split())
    if not keys:
        return False
    figures = re.findall(r"\d+(?:\.\d+)?\s*(?:%|percent|hours?|minutes?|days?|weeks?|litres?|"
                         r"liters?|kilos?|kg|metres?|miles?|pounds?)", said)
    if figures:
        for shape in getattr(entry, "shape", ()) or ():
            try:
                if shape(said):
                    return True
            except Exception:  # noqa: BLE001 - a shape that cannot read the line is no signal
                continue
        units = {word for figure in figures for word in re.findall(r"[a-z%]+", figure)}
        if units & set(keys):
            return True
    said_words = {word.strip(".,;:!?()") for word in said.split()}
    states = said_words & named.STATE_WORDS
    return any(any(key[:4] == state[:4] for key in keys) for state in states)


# The words that say how much of a thing there is, and nothing about which thing it is. A stated
# fact built only of these is not a fact about the thing on the table: "the hours are too much" is
# about hours, and no row keyed on "too much" is answering it.
A_DEGREE = frozenset("""too very really quite rather so such more most less least much many
                        enough plenty lots lot bit little slightly far""".split())


def _the_fact_is_what_is_answered(text, stated, entry, memory=None):
    """The entry a stated fact reaches has to be keyed on the fact, and on the subject too.

    Written with the subject in front, the line can reach any row that shares a single word with
    it, and that is not an answer: "lawn i work shifts" reached the stop-smoking card, "phone i
    work shifts" the stain one and "bike we rent" the rent-or-buy-a-house one. The entry that
    holds both halves of what the person said is the one that needs them - the pension card for
    the self employed, the bike card for a child - so the fact has to be in the key and so does
    the subject. A word is compared by its first four letters, because a key holds one form of a
    word ("years") and the line another ("year").
    """
    if entry is None:
        return False
    # The rewrite must not slip past the row's own standing-down words: the child-weight card
    # says "i want to lose" is not about a child, and the fact on its own ("i have two kids")
    # no longer holds that phrase, so writing the subject in front of it read a parent's own
    # wish as a question about their children.
    # What the whole exchange said, not only this line: the card that stands down on "i want to
    # lose" is held down by the first turn, and the fact said on its own no longer holds it.
    low = " ".join(str(text or "").lower().split())
    try:
        said = [str(turn.get("user") or "").lower() for turn in (memory or {}).get("turns", ())[-3:]]
    except (AttributeError, TypeError):
        said = []
    low = " ".join(said + [low])
    for hold in getattr(entry, "avoid", ()) or ():
        if isinstance(hold, str) and hold and hold.lower() in low:
            return False
    keys = []
    for part in getattr(entry, "key", ()) or ():
        for alternative in (part if isinstance(part, (tuple, list, frozenset, set)) else (part,)):
            if isinstance(alternative, str):
                keys.append(" ".join(alternative.lower().split()))
    if not keys:
        return False

    def tells(word):
        # The whole word, in the key's own phrase: comparing by opening letters was how "patchy"
        # met the nicotine patch in the stop-smoking card, and "shifts" the word "shift".
        return any(re.search(r"\b" + re.escape(word) + r"(?:s|es)?\b", key) for key in keys)

    said = [word for word in re.findall(r"[a-z0-9']+", str(text or "").lower())
            if len(word) > 2 and word not in named.FACT_FILLER
            and word not in named.JOINING]
    # A degree says how much of a thing, not which thing: "my sister says i should quit my job"
    # then "yeah she thinks the hours are too much" wrote the sister in front of the line, the
    # gift-budget row took "sister" as its subject and "too much" as the fact, and a person
    # talking about their shifts was asked what a present should cost. The fact has to name
    # something the row is about, so a fact made only of degrees is no fact to put in front.
    told = [word for word in said if tells(word)]
    if not told or all(word in A_DEGREE for word in told):
        return False
    subject = str(stated or "").lower().split()
    subject = subject[0] if subject else ""
    return bool(said) and tells(subject)


def _ask_a_line_of_its_own(line, memory):
    """The answer to a line asked with nothing on the table, as if it were the first thing said.

    The line here is one the person did not type - it is their own line written out ("how long
    does it take to fit a new one" asked as "how long does it take to fit a new boiler"). Read
    with the chat's topic still in memory it reaches the entry the topic is on (how long a boiler
    is built for) rather than the one its own words fit (how long a fitting takes), so the topic
    the bot remembers is left out and the entry that answers the words is asked.
    """
    spoke = {key: value for key, value in memory.items()
             if key not in ("topic", "topics", "entry_answer", "entry_answers", "last_answer")}
    return _ask_a_rewritten_line(line, spoke)


def _the_entry_key_words(entry):
    """Every word an entry is keyed on, in one flat list."""
    keys = []
    for part in getattr(entry, "key", ()) or ():
        for alternative in (part if isinstance(part, (tuple, list, frozenset, set)) else (part,)):
            if isinstance(alternative, str):
                keys.extend(alternative.lower().split())
    return keys


def _the_practice_is_answered(practice, entry):
    """The entry the practice reaches has to be about the practice and about the thing.

    A line written with its thing in front ("tomatoes feed every week") reaches whatever the thing
    and one other word fit, and an entry that only says what the thing is is no answer to what the
    person does to it: "tomatoes feed every week" reaching the sowing answer would tell them when
    to sow a plant they already have. The practice is what they said something about, so the entry
    has to be keyed on the care verb too ("feed", "water").

    It has to be keyed on the thing as well, and that is the half that is easy to lose. The person
    said the practice about *their* plant or *their* dog, and an entry that shares only the verb is
    some other question about the same word: "chillies feed every two weeks" met the meal plan,
    because chillies are a dinner, and "dog walk twice a day" met the step count, because walking
    is how the steps are counted. Both are fluent answers about something else, so both are worse
    than the plain "Got it" they replace. The thing is the words in front of the verb in the
    rewrite, which is the shape `named.care_reports` writes.
    """
    if entry is None:
        return False
    words = re.split(r"[^a-z]+", " ".join(str(practice or "").lower().split()))
    verbs = [word for word in words if word in named.CARE_VERBS]
    if not verbs:
        return False
    at = words.index(verbs[0])
    thing = [word for word in words[:at] if len(word) > 2]
    keys = _the_entry_key_words(entry)
    if not keys or not thing:
        return False
    same = any(_same_word(key, word) for key in keys for word in thing)
    if not same:
        return False
    return any(_same_word(key, verb) for key in keys for verb in verbs)


_A_YES_NO_ASK = re.compile(
    r"^(?:is|are|was|were|would|will|do|does|did|can|could|should|shall|have|has)\b", re.I)


# The words a thing named in a moan is made of, as the stems the answer is searched with.
MOAN_STOP = frozenset("""a an the my our your his her their its me i we you it that this these
those and or of to for in on at with from by up down out about right wrong""".split())


def _the_ask_behind_a_moan(text, memory):
    """The answer to the how-to ask behind "i always get rice wrong", or "".

    The frame says the thing they do comes out badly, and the thing named is what they want to do
    properly, so the ask behind it is the how-to about that thing. It is only taken when its
    answer is about the thing the person named: read loosely, "how do i get the kids to bed
    right" reaches the frost card, and a card about the wrong thing is worse than the line that
    asked for help.
    """
    written = doing_it.the_ask_behind_a_moan(text)
    if not written:
        return ""
    said = _ask_a_rewritten_line(written, memory)
    if not said:
        return ""
    thing = written[len("how do i "):].rsplit(" right?", 1)[0]
    # The thing's own name is the last word of it that is not grammar ("the rice", "my hours",
    # "the timing"), and that is the word the answer has to have in it. A share of any words is
    # not enough: "how do i get the tax return right" reaches the trading-allowance card, which
    # says "tax" and is not about a return at all.
    named = [word for word in WORD.findall(thing.lower())
             if len(word) > 2 and word not in MOAN_STOP and word not in MOAN_VERB_WORDS]
    if not named:
        return ""
    head = said_topic.stem(named[-1])
    answered = {said_topic.stem(word) for word in WORD.findall(said.lower())}
    if head not in answered:
        return ""
    if _said_before(_without_lead_in(said), memory):
        return ""
    return said


MOAN_VERB_WORDS = frozenset("get do make cook pick find manage".split())


def _ask_a_rewritten_line(line, memory):
    """The answer to a line the person did not type, read with their own reading replaced.

    The shape of answer the turn asked for is carried onto the fresh reading: the reading of the
    rewrite never passes through `bot/modules/intent.py`, which is what writes `wants`, so a module
    underneath saw a line that asked for nothing. "and for 3kg" after a chicken time lost its
    time, and the second "what should i cook tonight" in a chat lost its pick.
    """
    was = memory.get("understood")
    want = was.get("wants") if isinstance(was, dict) else None
    try:
        fresh = understand(line, memory)
        if want and isinstance(fresh, dict):
            fresh["wants"] = want
        memory["understood"] = fresh
        return _respond(line, memory)
    finally:
        if was is None:
            memory.pop("understood", None)
        else:
            memory["understood"] = was


# A period the line asks about: a day, a week, a month. "how much sugar should i have a day"
# is a question about the day, so a figure cut out of the previous answer is not its answer.
_A_PERIOD = re.compile(
    r"\b(?:a|per|each|every|one)\s+(?:day|week|month)\b|\b(?:daily|weekly|monthly)\b", re.I)

# The bare ask for the words to refuse: "how do i say no", "how can i say no without feeling
# awful". The refusal entries are keyed on the situation (a boss, a client, a mum, a request),
# so the ask that names no situation reached the search hedge even though the same answer fits.
# This is the last reader in _answer, after every entry and every follow-up, so an answer that
# knows the situation keeps the turn. It is deliberately narrow: only the ask itself, or the ask
# with a feeling to avoid, because "how do i say no without sounding lazy" is the wording module's
# offer to draft it, and a language question ("how do i say no in sign language") is not advice.
BARE_SAY_NO = re.compile(
    r"^(?:how\s+(?:do|can|could|should)\s+i\s+"
    r"(?:say\s+no|refuse|turn\s+(?:something|it|that)\s+down)"
    r"|what\s+do\s+i\s+say\s+when\s+i\s+say\s+no)"
    r"(?:\s+without\s+feeling\b[^.!?,;:]*)?\s*[.!?]*\s*$", re.I)


def _turns_on_this_line(text, memory):
    """How many turns in a row, just before this one, asked the same line."""
    wanted = _flat(text)
    if not wanted:
        return 0
    count = 0
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict):
            break
        if _flat(turn.get("user")) != wanted:
            break
        count += 1
    return count


def _without_lead_in(answer):
    """The answer with a repeat lead-in taken off, so a third repeat does not stack them."""
    for frame in AGAIN + (AGAIN_HELP,):
        head = frame.split("{reply}")[0]
        if answer.startswith(head):
            return answer[len(head):].strip()
    # Every other repeat frame in the codebase is a lead-in too, and they live in
    # `bot/memory/again` ("Same answer, and it covers this: ...", "Nothing separate for the biting
    # - it is the same advice: ..."). Not knowing them stacked a second lead-in in front of the
    # first: "Same as before: Same answer, and it covers this: Wash the bin with hot soapy water".
    return same_again.unframed(answer) or answer


# A line that asks whether to make a call is not answered by saying the trouble's steps again:
# "should i see someone" after a cough is the composer's referral to give, and it has the answer
# in hand. The words are the call itself, not the ask around it ("what should i do" is a step).
A_CALL_ASK = frozenset("""see seeing ring call contact phone gp doctor surgery nurse hospital
    dentist vet 111 999""".split())


def _the_line_again(text, memory):
    """The answer just given, said again with the lead-in a repeat gets, or None.

    This is the last thing the knowledge base does: when nothing in it answers the line the
    second time, the answer the person has already been given is still the answer, and a shrug
    is the one reply a repeated question must not get - "im making a cake" then "frosting" twice
    gave the frosting recipe and then "Thanks for telling me - I'm here if you want to dig into
    any of that". Only an answer of ours is repeated, so a repeated "no" or "thanks" is left to
    the small talk, and a line asking about a step already taken ("i tried that") keeps its
    next step from `chat`.
    """
    if not isinstance(memory, dict):
        return None
    if memory.get("frequency_reply"):
        # The turn before the frequency reply is the trouble answer, and a line that leans on the
        # trouble without naming anything of its own ("can i take anything for it") can reach the
        # search hedge because the frequency line, not an answer, is now the last thing said. The
        # answer behind it is still the answer, so the part the line asks is said again. A line
        # with something of its own keeps the normal lookup, and a referral ask is left to the
        # composer, which outranks this module.
        behind = str(memory.get("frequency_answer") or "").strip()
        read = memory.get("understood")
        if (behind and isinstance(read, dict) and read.get("followup")
                and not read.get("change_of_subject") and not read.get("subject")
                and "recommend" not in (read.get("asks") or ())
                and not (A_CALL_ASK & set(read.get("words") or ()))):
            # A line asking for a judgement ("is it worth seeing someone") is left to the
            # composer, which has the answer's referral and is the better reply; only a line
            # asking for a step or a thing gets the part of the answer it asks for.
            return AGAIN[0].format(reply=_repeat_short(behind, text, memory))
    if mem.last_module(memory) != "answers":
        return None
    said = _turns_on_this_line(text, memory)
    answer = _without_lead_in(str(mem.last_bot(memory) or "").strip())
    if not said or not answer:
        return None
    if said >= 3:
        return AGAIN_HELP.format(reply=answer)
    return AGAIN[said - 1].format(reply=_repeat_short(answer, text, memory))


# The words a line says around a topic without naming anything: "my budget", "the budget",
# "our spending". Only these are stripped when asking whether a line is nothing but the store's
# own slot, and only "my"/"our"/"i" make it the person's rather than the topic's.
# The lead-ins and joining words people put in front of the slot, so "and my budget?" and
# "so my budget then" are the same line as "my budget".
_FRAME = frozenset("my our i the a an is was be been it its of on about and but so also then "
                   "now ok okay right well again too".split())
_MINE = frozenset("my our i me mine ours".split())
# The store's own fact keys ("budget", "name", "pet", ...): a line that is nothing but one of
# these is a mention of the slot, not a question about the topic.
_SLOT_KEYS = frozenset(key for key, _ in recall.SUBJECTS)
# The slots whose store reply is a limit the bot then works inside ("Your budget is 400 pounds,
# then - I'll stick to that"), and the entries that would otherwise take the line. A job or a
# city is not a limit at all: "i work in a warehouse on the night shift" keeps the night-shift
# answer, which says more than "Noted: you work in a warehouse on the night shift". Of the
# money entries, only the general ones stand down, because a figure the store has read back is
# still the figure the split entry splits. An entry with a purpose of its own keeps the line -
# "my food budget is 60 a week" is food-bill's, "my wedding budget is 5000" is wedding-budget's,
# and both say something about the figure that a receipt cannot.
_STORED_VALUE = {"budget": frozenset(("budget-how", "budget-split", "budget-rule"))}
# A how-to is not a request for a stored value: "how do i budget" and "what do i do about my
# budget" ask what to do, and the entry is the answer to that.
_HOW_TO = re.compile(r"\b(?:how|help|make|sort|fix|plan|start|do)\b")
# A value is stated rather than planned: "my budget is 400 pounds" hands over a figure, while
# "i set myself a budget of 200" and "my budget of 200" keep the worksheet on main and still do.
_COPULA = frozenset("is are was were s".split())


def _stated_with_copula(text, value):
    """Whether the value is given with "is"/"was" in front of it, not with "of" or a verb.

    "my budget is 400 pounds" and "my food budget is 60 a week" hand over a figure; "i set
    myself a budget of 200" and "my budget of 200" are plans, and on main they keep the
    worksheet, which is what a person asking how to budget wants.
    """
    words = _flat(text).split()
    value_words = _flat(str(value)).split()
    if not words or not value_words:
        return False
    for start in range(len(words) - len(value_words) + 1):
        if words[start:start + len(value_words)] == value_words:
            return start > 0 and words[start - 1] in _COPULA
    return False


def _nothing_but_the_slot(said, value_words, about):
    """Whether the line, with the value taken out, is no more than the slot's own word.

    "my budget of 200" is the same line as "my budget is 200" and main reads it back, while
    "i set myself a budget of 200" has words of its own ("set", "myself") and keeps the
    worksheet there. So the copula is not the whole test; this is the other half of it.
    """
    rest = list(said)
    for word in value_words:
        if word in rest:
            rest.remove(word)
    left = [word for word in rest if word not in _FRAME]
    return bool(left) and all(word in about for word in left)


# The knowledge that answers with food: a line saying what someone does not eat is a diet, and
# the useful reply is a dinner they can eat or the swap for the thing they cannot. Every other
# domain reads a food named after "doesnt eat" as the thing that has stopped being eaten - a pet
# off its food, a child refusing meals - which is a different line about a different subject.
_COOKING_DOMAIN = frozenset(("cooking", "dishes", "meals", "food", "drink", "drinks"))


def _the_food_they_do_not_eat(text, understood):
    """Whether the line only states a food somebody does not eat, and the entry is not about food.

    "my son doesnt eat fish" is the son's diet: the store says it back, and the pet answer - test
    the water, it is nearly always ammonia - is about a fish that has stopped feeding. The same
    line worded as a limit on the person - "my son cant eat fish", "my wife cannot eat gluten" -
    is the same fact, and the store keeps it as their allergy. A line that asks something as well
    keeps its answer ("my son doesnt eat fish, what can i cook"), and so does any domain that
    answers with food, because a dinner round a diet is the better reply than the fact said back:
    "my son doesnt eat meat" still gets the vegetarian dinner and "my son doesnt eat eggs" the
    egg-free swap.
    """
    if not isinstance(text, str) or _HOW_TO.search(_flat(text)):
        return False
    reading = understood if isinstance(understood, dict) else {}
    if reading.get("asks") or reading.get("kind") == "question":
        return False
    stated = mem.facts.extract(text, question=False)
    if not mem.facts.foods_ruled_out(stated):
        return False
    item = find(understood)
    return item is not None and item.domain not in _COOKING_DOMAIN


def _store_keeps_the_line(text, understood):
    """True when the line hands the store a value the entry is about, or asks for one back.

    A person who says "my budget is 400 pounds" is telling the bot something, and a person who
    says "whats my budget" is asking the bot what it kept. Both are the store's turns, and an
    entry about budgeting that answers either one is a how-to for a question they did not ask.
    The entry still answers every line that is a question about budgeting itself ("my budget is
    a mess", "help me with my budget", "how do i make a budget"), because those state no value
    and ask for none.

    The comparison is against the entry's own key words, so a statement about something else
    keeps its answer: "im 34 and thinking of going back to uni" states an age, no entry about
    university is about age, and the answer is unchanged. A value has to be a part of the line
    rather than the line itself, because "i want to plan meals for the week" is filed as a plan
    and the plan is what the meal-plan entry is there to answer.
    """
    if not isinstance(text, str):
        return False
    item = find(understood)
    if item is None:
        return False
    about = _key_words(item)
    if not about:
        return False
    reading = understood if isinstance(understood, dict) else {}
    if reading.get("kind") == "statement":
        stated = mem.facts.extract(text, question=False)
        said = _flat(text).split()
        if isinstance(stated, dict):
            for slot, value in stated.items():
                words = _flat(str(value)).split()
                if item.id not in _STORED_VALUE.get(slot, ()):
                    continue
                if words and words != said and len(words) < len(said) \
                        and (_stated_with_copula(text, value)
                             or _nothing_but_the_slot(said, words, about)):
                    return True
    asked = recall.ask(text)
    if asked and not _HOW_TO.search(_flat(text)):
        return asked in about
    # "my budget", and its like: nothing but the person's own topic, with no ask and no value.
    # That is still the store's, not the entry's: it answered it before this change ("You haven't
    # told me a budget."), and now that "my" is an ask word the entry would take it. The line has
    # to name the slot in the store's own words and say nothing else that the entry is about, so
    # "my budget is a mess" and "i want to sort my budget out" keep the how-to.
    said = [word for word in _flat(text).split() if word not in _FRAME]
    if not said or not all(word in about for word in said):
        return False
    if not any(word in _MINE for word in _flat(text).split()):
        return False
    # ... and the words left have to be the slot's own name, so "my budget plan" still wants the
    # plan: only "budget", "name", "pet" and the rest of the store's keys stand down here.
    return all(word in _SLOT_KEYS for word in said)


# A line that asks what the oven should be set to is asking for a figure, and the oven-runs-hot
# card is about an oven that is wrong. These words keep that card for the question it answers.
_OVEN_CHECK_WORDS = ("check", "checking", "thermometer", "accurate", "runs hot", "running hot",
                     "too hot", "overheat", "overheats", "gone wrong", "be wrong",
                     # an oven with a fault is a fault question, whatever setting is asked for
                     "not heating", "not heat", "wont heat", "won't heat", "cold", "not working",
                     "broken", "fault", "smell", "smoke", "stays on", "stay on", "won't turn off",
                     "wont turn off", "keeps running", "noisy", "noise", "loud", "rattl",
                     "grinding", "squeak", "bulb", "element", "door", "seal", "hinge", "light")


# Only the oven and the fan oven: the figure in a plan is the *oven* figure, and an air fryer,
# a grill or a slow cooker is a different appliance with its own answer.
_OVEN_WORDS = ("oven", "fan oven")


_PROPERTY_WORDS = ("temperature", "temp", "heat", "degrees", "gas", "gas mark", "how hot")


def _says_line(text, words):
    """True when any phrase in `words` is in the line."""
    return any(phrase in text for phrase in words)
# A taste in a line that also asks what to watch, read or listen to is a constraint on the pick,
# not a preference to file away: "what film should i watch if i like sci fi" says what they like
# and asks for the next thing, and read as a bare taste it went to the store, which said it back
# (or to the search hedge), while the film card sat one row away. The frame is narrow on purpose:
# only the three tables that really do pick by taste have one, because the bare "recommend" and
# "what should i do" frames let a card answer a line that named its taste for a reason, and a
# card that is about the wrong thing is worse than the honest "I don't know that one".
PICK_FRAME = re.compile(
    r"\b(?:what|which)\b[^?.!]{0,30}?\b(?:should|could|can|shall|would|do|might)\s+"
    r"(?:i|we|you)\s+(?:watch|read|listen\b|stream|binge)\b"
    r"|\b(?:recommend|suggest)\b[^?.!]{0,40}?\b(?:to watch|to read|to listen|podcast|podcasts|"
    r"film|films|movie|movies|book|books|album|albums|show|shows|series)\b",
    re.I)


def _a_pick_is_asked(text):
    """Whether the line asks what to watch, read or listen to, so a taste is a constraint."""
    return bool(PICK_FRAME.search(str(text or "")))


def _the_line_as_said(text):
    """The line with a filler it opens with taken off, as the understanding engine read it.

    People open a line with "like" the way they open it with "so" or "well", and the word is a
    real one, so a reader that matches it as typed takes "like my back hurts" for a taste of
    theirs ("i like...") and hands the turn to the store. The engine drops the filler and keeps
    the rest, so the readers that go by a phrase ask the line as it was said.
    """
    if not isinstance(text, str):
        return text
    from ..understanding.normalize import _a_leading_like_is_a_filler
    return _a_leading_like_is_a_filler(" ".join(text.lower().split()))


# Someone who can call the person in wants a word with them: "my sons teacher wants to see me"
# is not a question about teaching, and "the doctor wants to see me" is not one about booking
# an appointment - yet the entries that know those subjects answered them, because the only
# word they shared with the line was the office itself. The chat has a pool for each shape of
# summons (a word, a letter, a phone call), so the knowledge base steps aside for a line that
# says nothing but the office and the asking. A line that says what the word is about keeps its
# answer: "... wants to see me about his reading" is the reading entry's, and "a letter from
# the council saying i owe council tax" is the council tax letter's.
OFFICE_WHO = frozenset(SUMMONS_WHO) | frozenset("""
    social services health visitor home tax job centre jobcentre letting agent the
""".split())
# The words a summons is made of - what they asked for, and the asking itself - so a line whose
# only shared words are these has been read for the office and nothing else.
OFFICE_ASKING = frozenset("""
    word words meeting meetings appointment appointments letter letters written wrote write
    writing rang ring ringing phoned phone called call calls message messages email emailed
    note notes see saw talk talks speak speaking discuss discussing chat meet come came coming
    quick asked ask asks asking want wants wanted need needs needed like would got receive
    received had saying told
""".split())


def _only_the_office(memory):
    """True when the entry this line reaches answers on the summons' office and nothing else."""
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(understood, dict) or not isinstance(understood.get("summons"), dict):
        return False
    if understood.get("asks") or understood.get("kind") == "question":
        return False
    item = find(understood)
    if item is None:
        return False
    said = {str(word).lower().rstrip("s") for word in _key_words(item)}
    typed = {str(word).lower().rstrip("s") for word in (understood.get("keywords") or ())}
    shared = said & typed
    return bool(shared) and not (shared - OFFICE_WHO - OFFICE_ASKING)

def _a_food_named_of_its_own(understood, food):
    """True when the line names a food of its own that is not the food in hand.

    A keeping question is only a follow-up when the food in it is the one the store is holding.
    "how long can i keep cooked chicken in the fridge" a turn after the rice was answered is a
    question about the chicken: it names its own food, so nothing has to be put back in, and the
    chicken's own entry is the answer. Read as a bare "how long does that keep" it was put back
    together with the food the store held - "how long does cooked rice keep in the fridge" - and
    the chicken question came back with the rice paragraph behind "Same as before", which is
    the one answer nobody can use. Only a line that brings no other food leans on the one in hand.
    """
    held = set(str(food or "").lower().split())
    if not held:
        return False
    for name in cooking.ingredients(understood) or ():
        if not set(str(name).lower().split()) & held:
            return True
    return False


def _keeping_about_the_food_there(memory, understood):
    """The keeping fact for the food the chat has moved to, when a bare line asks about "it".

    "im making a cake" / "frosting" / "i burnt the rice" then "can i still eat it" is a keeping
    question about the rice, and the rice's own entry says 24 hours in the fridge. The line names
    nothing, though, so the entries never reach it: the dish follow-up answers instead from the
    last *dish* the store heard of, which here is the cake two turns back, and "3 days in a tin"
    is a keeping fact about the wrong food. Where the chat has moved to a food with no plan of its
    own, the question is put with that food in it and the entries answer - they are where the
    keeping facts live.

    Only when there is a dish for the store to answer from. With no dish in the chat, nothing
    hands out a fact about another food: "i burnt the rice" / "can i still eat it" is about the
    rice in front of them, and the answer already on the table - take it off the heat, lift the
    burnt bits out - covers it. A freshness figure is a different question about a different
    thing, and the repeat says more than the figure does - main's own "Same answer" path already
    hands that answer back, so this stands aside and lets it.
    """
    if not isinstance(memory, dict) or not isinstance(understood, dict):
        return None
    if dishes.ask_kind(understood) != "keep":
        return None
    if not dishes.dish_for(memory, understood):
        return None  # no dish to answer from: the answer on the table is the answer
    if cooking.ingredients(understood):
        # The line names a food of its own, so it is not the bare "can i still eat it" this is
        # for: the entries read it as it stands. "how do i cook rice" then "how long does chicken
        # last in the fridge" names the chicken and no "it" at all, and the food the chat is on
        # put the rice's 24 hours in place of the chicken's two days.
        return None
    food = named.the_food_it_is_about(understood, memory)
    if not food or dishes.dish_in(food):
        return None  # a food with a plan of its own is the plan's to answer
    if _a_food_named_of_its_own(understood, food):
        return None  # the line brought a food of its own: its own entry is the answer
    if not cooking.ingredients(understand(food, memory)):
        return None  # not a thing anyone keeps: a pot, a plant, a word we do not know
    asked = understand("how long does cooked " + food + " keep in the fridge", memory)
    item, reply = _offer(lambda reject: find(asked, reject=reject), memory, asked)
    if getattr(item, "id", "") in GENERIC_KEEPING:
        return None  # a fact about cooked food in general says nothing about this food
    return reply if isinstance(reply, str) and reply.strip() else None


def _the_answer_on_the_table(understood, memory):
    """The answer already on the screen, when the keeping question is about the food in it.

    "i burnt the rice" / "can i still eat it" names no food, so no entry reaches it, there is no
    dish for the store to answer from, and the turn fell through to a search hedge with a
    paragraph about the rice sitting right above it. The food the chat is on is the food the last
    answer was about, so that answer is said again - but only when it answers the *trouble* the
    person named ("burnt" is in it), never when it is how to cook the thing: after "i cooked too
    much pasta" the answer on the table is the pan and the timing, and saying it again does not
    say whether the pasta can still be eaten, so a hedge is the honest reply and a confident
    repeat is not.

    This is the last resort of `_respond`: an entry that can answer the line as it stands always
    beats a repeat of the turn above it ("i burnt the toast" / "can i still eat it" is a direct
    yes, and it must stay one).
    """
    if not isinstance(memory, dict) or not isinstance(understood, dict):
        return None
    if dishes.ask_kind(understood) != "keep":
        return None
    food = named.the_food_it_is_about(understood, memory)
    if not food or food.lower() not in str(mem.last_user(memory) or "").lower():
        return None  # the food is not the one the last answer was given about
    if _a_food_named_of_its_own(understood, food):
        return None  # the line brought a food of its own: its own entry is the answer
    turns = memory.get("turns")
    last = turns[-1] if isinstance(turns, list) and turns and isinstance(turns[-1], dict) else None
    if not last or last.get("module") != "answers":
        return None  # the line on the screen is not an answer from the knowledge base
    said_back = str(last.get("bot") or "")
    if not said_back.strip():
        return None
    trouble = (_carries(mem.last_user(memory)) - {word.lower() for word in food.split()}
               - _carries(food)) & _carries(said_back)
    if not trouble:
        return None  # the answer is not about the trouble in the line: do not say it again
    return AGAIN[0].format(reply=_in_short(said_back))


def _already_on_the_screen(reply, memory, turns=4):
    """Whether this reply is an answer the person already has, word for word."""
    mine = " ".join(str(reply or "").split()).lower()
    if not mine:
        return True
    seen = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(seen, list):
        return False
    for turn in seen[-turns:]:
        if isinstance(turn, dict):
            said = " ".join(str(turn.get("bot") or "").split()).lower()
            if said and said == mine:
                return True
    return False


# "read it again" after a verse is the verse asked for, not a lapsed reading habit: "read" and
# "again" are the lapsed-reader row's key words, so somebody who had just been given a poem was
# told to start with *Of Mice and Men*. The verse is written as a lead with lines under it, which
# is what tells it apart from every other reply here.
_READ_AGAIN = re.compile(
    r"\b(?:read|say|tell|sing)(?: it| that| this)?(?: again| once more)\b"
    r"|\bread it (?:back|to me again)\b"
    r"|\b(?:again|once more) please\b", re.I)
_VERSE_FORM_WORD = re.compile(
    r"\b(story|stories|tale|tales|poem|poems|rhyme|rhymes|rap|song|verse|limerick|haiku|"
    r"couplet|ode|sonnet)\b", re.I)


def _the_verse_said_again(text, memory):
    """The verse the last turn gave, said once more, or None when the last turn was not one.

    Only a verse counts: a lead with lines under it. A hedge, an idea or a piece of advice about
    a poem is not something to read out again, and a verse from three turns back is not what
    "read it again" points at.
    """
    if not isinstance(text, str) or not _READ_AGAIN.search(text):
        return None
    turns = [turn for turn in ((memory or {}).get("turns") or []) if isinstance(turn, dict)]
    for turn in reversed(turns):
        said = str(turn.get("bot") or "")
        if not said:
            continue
        asked = str(turn.get("user") or "")
        if not (_VERSE_FORM_WORD.search(asked) or said.startswith("Once more")) or "\n" not in said:
            return None
        said = said[said.index("\n") + 1:] if said.startswith("Once more") else said
        lead, lines = said.split("\n", 1)
        # A form that announces itself ("A limerick, then:") is not given a second lead, or the
        # person gets "Once more, then: A limerick, then: ...".
        if lead.rstrip().endswith(":"):
            return "Once more.\n" + lines
        return "Once more, then:\n" + said
    return None


# The frame a repeat reader puts in front of an answer already on the screen. A how-much line
# wants the figure, and a frame that points back at the card is not the figure said again.
_REPEAT_OPENS = re.compile(r"^(?:same as before|same answer|as i said|you've got it|you have it|"
                           r"i said|still)\b", re.I)

# The bare ways of asking for the figure again, with nothing of the subject in them. A line
# like this cannot be matched by the shared-word reader, and the answer it gets is the figure
# already on the screen; the repeat reader would frame that answer as a pointer at the card.
_A_BARE_MEASURE = re.compile(
    r"^\s*(?:(?:and|so|then|ok|okay)\s+)?how (?:much|many)"
    r"(?:\s+(?:is it|is that|does it cost|does that cost|again))?\s*[?.!]*$", re.I)


def _the_sentence_around(fragment, text):
    """The whole sentence of `text` that holds `fragment`, or "" when it does not hold it.

    "The limit for an adult is 6g of salt a day." is a cut of the card's first sentence, and the
    rest of that sentence ("about a level teaspoon, and most people eat 8g") is what a friend
    says. A figure sentence inside a longer answer is widened the same way, so the warning that
    happens to share the word "take" is not handed back as the dose.
    """
    fragment = str(fragment or "").strip()
    text = str(text or "")
    if not fragment or not text:
        return ""
    flat_fragment = " ".join(fragment.split()).rstrip(".")
    lowered = " ".join(text.split())
    where = lowered.lower().find(flat_fragment.lower())
    if where < 0:
        return ""
    start = 0
    for match in re.finditer(r"(?<=[.!?])\s+", lowered[:where]):
        start = match.end()
    end = len(lowered)
    match = re.search(r"[.!?](?=\s|$)", lowered[where + len(flat_fragment):])
    if match:
        end = where + len(flat_fragment) + match.end()
    return lowered[start:end].strip()


def _the_sentence_with_a_figure(text):
    """The first sentence of `text` that carries a figure and says what the figure is of.

    A bare "how much" after "A banana is about 105 calories (a medium one)." is the figure
    already on the screen. The shared-word reader has nothing to match and the repeat reader
    framed that sentence as "Same as before: ...", which points at the answer instead of giving
    it. The sentence itself is the answer, and it is the sentence a how-much line gets.
    """
    for sentence in SENTENCE.split(str(text or "")):
        said = sentence.strip()
        if (said and re.search(r"\d", said)
                and (SIGNALS["amount"].search(said) or SIGNALS["money"].search(said))):
            return said
    return ""

# The words themselves, as a card says them: a sentence to say, given in quotes, or a reply that
# opens on telling the person what to say. That is what the line asked for when `shapes.
# asks_for_words` is true, and a card that answers the thing instead - "Fill the sink with the
# hottest water" for how to tell a flatmate about the dishes - has neither.
SAID_OUT_LOUD = re.compile(
    r"[\"“][^\"”]{6,}[\"”]|'[^']{8,}'"
    r"|^\s*(?:say|tell|ask|put it|word it|lead with|start with|open with|write)\b"
    # A card that says which question to put is giving the person something to say, even when it
    # writes it out without quotes: "ask each trader the same question: what would bring that
    # down?" is the words to use.
    r"|\b(?:ask|say|tell|raise)\b[^.?!]{0,40}\b(?:question|questions|sentence|words|wording)\b",
    re.I)


# A reply that is about taking the matter to somebody *is* the answer to "how do i tell them":
# "how do i tell my dad to stop driving" was answered with the DVLA, his GP and a driving
# assessment - advice about this very conversation, which is what the person was asking for - and
# the wording card that took its place was a script for criticising somebody's pastry. It has to
# be said to somebody, though, or be *their* person ("your instructor"): a dentist in the last
# sentence of a card about bad breath, or the registrar in the second sentence of a card about
# wedding costs, is not what that card is about.
A_PERSON = (r"(?:gp|doctor|doctors|dentist|school|college|university|instructor|examiner|teacher"
            r"|tutor|head of year|manager|boss|employer|hr|personnel|union|careers|adviser"
            r"|advisor|consultant|council|citizens advice|solicitor|landlord|letting agent|vet"
            r"|pharmacist|midwife|health visitor|social worker|ombudsman|registrar|therapist)")
SAYING_IT_TO = re.compile(
    r"\b(?:ask|asked|asking|tell|telling|speak|speaking|talk|talking|ring|phone|call|email|write"
    r"|raise it|mention|sit down|take it|bring it up|have a word|report|complain)"
    r"\b[^.!?]{0,60}?\b" + A_PERSON
    + r"\b(?!['\u2019]s)",
    re.I)
YOUR_PERSON = re.compile(r"\byour\s+" + A_PERSON + r"\b(?!['\u2019]s)", re.I)
_TWO_SENTENCES = re.compile(r"\s*(?:[^.!?]*[.!?]){1,2}")


def _puts_it_to_someone(reply):
    """True when the reply already says how to put this to a person rather than what the thing is."""
    words = " ".join(str(reply or "").split())
    if not words:
        return False
    found = _TWO_SENTENCES.match(words)
    opening = found.group(0) if found else words
    return bool(SAYING_IT_TO.search(opening) or YOUR_PERSON.search(opening))


def _the_ask_is_for_words(reading):
    """True when this line asks what to say rather than what to do (see `compose.fit`)."""
    try:
        return shapes.asks_for_words(reading)
    except Exception:  # noqa: BLE001 - a reading this shape cannot use answers nothing here
        return False


def _respond(text, memory):
    if isinstance(text, str):
        verse = _the_verse_said_again(text, memory)
        if verse:
            return verse
    if isinstance(text, str):
        # A kind of cake, asked about after a bake was named: "im thinking of baking a cake" then
        # "what about a carrot cake" reached the carrot entry, which is a side dish, and "what
        # about lemon drizzle" reached the entry about drizzling a sauce over a joint. Written
        # out as the how-to the cake entries answer, the line keeps the bake the person is in.
        baked = baking.written_out(text, memory)
        if baked and baked != text:
            asked = understand(baked, memory)
            item, reply = _offer(lambda reject: find(asked, reject=reject), memory, asked)
            # Only a reply that answers the cake: "what about a coffee cake" right after the
            # sponge method earns "Same as before: ..." - the answer already given with a lead-in
            # on it - where the entry the line reached on its own was better.
            if item is not None and reply and not _already_on_the_screen(reply, memory):
                return reply
        # What to wear, asked after the occasion has been said: "im not sure what to wear" and
        # "and what about shoes" carry no occasion of their own, so on their own they were a
        # feeling read back and a search hedge. Written out with the thing on the table - "what
        # should i wear to a wedding" - they reach the outfit answer the entries hold.
        # The card is already on the screen and the line asks about one thing in it: "will black
        # be alright" after an answer that said black or dark colours are the thing. The sentence
        # that names it is the answer, and it is handed over as it was said.
        covered = outfit.the_sentence_answered(text, memory)
        if covered:
            return covered
        outfitted = outfit.written_out(text, memory)
        if outfitted and outfitted != text:
            asked = understand(outfitted, memory)
            item, reply = _offer(lambda reject: find(asked, reject=reject), memory, asked)
            if item is not None and reply and not _already_on_the_screen(reply, memory):
                return reply
        # One attribute of the thing on the table, asked on a line of its own: after "im making
        # bread" the person's next line is "and the oven temperature", which names no thing and
        # reached the oven repair card ("the heating element is almost always the fault"); after
        # "she wants a bike" the line "which size" reached the women's clothes chart. Written out
        # with the thing on the table, "oven temperature for bread" and "what size bike do i need"
        # are the questions the entries answer.
        attributed = said_topic.attribute_of_the_thing(text, memory)
        if attributed and attributed != text:
            asked = understand(attributed, memory)
            item, reply = _offer(lambda reject: find(asked, reject=reject), memory, asked)
            if item is not None and reply:
                if _already_on_the_screen(reply, memory):
                    # The attribute is one the answer already gave: "im roasting a chicken" was
                    # answered with the timing, and "and the timing" asks for it again. It is
                    # given again and framed as the repeat it is, rather than leaving the turn to
                    # the quantity reader, which answered a length of time with how much meat.
                    return repeat.pick(same_again.SHORT_AGAIN, memory,
                                       text).format(reply=reply)
                # An entry's sentence can open on a lower-case word ("about 1 hour 40 at 190C for
                # a 2kg joint or bird."), which is a fragment on a line of its own.
                return reply[:1].upper() + reply[1:]
    if isinstance(text, str) and trips.the_bag_beats_the_list(text, memory):
        # "what should we pack" about a trip in October is the trip's line: the store knows the
        # place and the month ("Pack light for the Lakes in October - a waterproof, something
        # warm..."), and this module's warm-week list answered a cold place with cotton tops and
        # swimwear. Every other month keeps this module's answer: high summer and the cold months
        # its lists do know, and where a place has no entry of its own the store's bag is reached
        # anyway, so standing down there only cost the answer a turn ("were going to cornwall in
        # july" lost its bag to a search hedge).
        return None
    if _only_the_office(memory):
        # The answer the entry would give is about the office rather than about the word the
        # person is waiting for, so the turn goes to the summons pool (`greeting`).
        return None
    if isinstance(text, str):
        # A verdict on the present the chat already listed is answered here, before any entry
        # reads the words of the line: "my nephew is 5 in june" / "what can i get them" / "would a
        # scooter be too much" reached the repeat reader, which said "Everything about a scooter
        # is in what I said above" - the list again, in a sentence about the chat instead of the
        # present. The row stands down unless the age is held and the thing named is a pick that
        # age's answer already offered, so every other verdict ask keeps the answer it had.
        verdict = shopping.the_verdict_on_a_present(memory, understand(text, memory))
        if verdict:
            return verdict
        # "make it longer" after a story or a poem is the verse just given with another part on
        # the end. Every reader below treats it as the verse said again ("Nothing separate for a
        # longer - it is the same advice"), as the hair-growth card, or as the search hedge, so it
        # is answered here first, on the typed line, the way the verdict on a present is.
        longer = entertainment.the_verse_longer(text, memory)
        if longer:
            return longer
        # "one more about the moon" after a poem about the moon is another poem about the moon, in
        # the form just given: the phrase names a subject and no form, so no row reads it as a
        # request and main said "Got it - one more about the moon."
        another = entertainment.the_next_verse(text, memory)
        if another:
            return another
    # A limit on a present is settled first, before anything reads the amount as something else:
    # "my budget is 30 pounds" after "a present for my sister" is the price of that present, and
    # the store reads a figure back, which is the right answer to the same line in a chat that is
    # not buying anyone a present. The gate is the cheap shape of a limit, so this costs nothing
    # on the lines that are not one.
    if isinstance(text, str) and LIMIT_SHAPE.search(text):
        priced = _the_present_with_a_price(text, understand(text, memory), memory)
        if priced:
            return priced
    if (isinstance(memory, dict) and mem.last_module(memory) == "answers"
            and isinstance(memory.get("understood"), dict)
            and mem.asks_only(memory["understood"])
            and not memory["understood"].get("change_of_subject")
            and asked_kind(text) in ("amount", "money")
            and re.search(r"\bhow much\b", str(text or ""), re.I)
            # A line that names the cost is asking about a thing, and the subject written into it
            # ("how much would the dog cost") reaches the price row. The answer last given can be
            # a sentence with the yearly cost in it, and handing that back would answer a
            # different question - the running cost of the dog for the price of getting one.
            and not re.search(r"\b(?:cost|costs|costing|price|prices|charge|charges)\b",
                              str(text or ""), re.I)):
        stated = same_as_before(memory["understood"], memory)
        # Only a sentence with a figure in it answers a how-much line. The shared-word reader
        # can hand back the steps instead ("divide the total by the weeks left" shares "week"
        # with the line), and that sentence was already read: the money readers below have the
        # figure this line wants, so leave the turn to them.
        if (stated and re.search(r"\d", str(stated))
                and flat(stated) != flat(mem.last_bot(memory) or "")
                and (SIGNALS["money"].search(stated) or SIGNALS["amount"].search(stated))):
            # The reader can hand the answer back behind a repeat lead-in ("Same answer, and it
            # covers this: ..."). A how-much line is owed the figure, not a pointer to where it is
            # on the screen, so the frame comes off before the sentence is read.
            if _REPEAT_OPENS.match(str(stated)):
                stated = _REPEAT_OPENS.sub("", str(stated)).lstrip(" :,-")
            # `same_as_before` cuts the answer to the clause that matched. When that clause is
            # inside the answer the person just read, the whole sentence around it says more and
            # is still the same answer: "The limit ... 6g of salt a day." lost the level teaspoon
            # and the 8g most people eat. The sentence is preferred to the cut, and to a repeat
            # frame, which is never the answer to a how-much line.
            whole = _the_sentence_around(stated, mem.last_bot(memory) or "")
            # Only widen when the rest of that sentence says something with a figure of its own:
            # the salt clause lost "most people eat 8g", while the water and melatonin clauses
            # already carry the figure asked for and reading more of the paragraph is the repeat
            # the arbiter passes over.
            if (whole and re.search(r"\d", whole[len(stated):])
                    and not _REPEAT_OPENS.match(whole)):
                return whole
            return stated
        # The bare ask has no words for the shared-word reader to match, so nothing came back.
        # The figure on the screen is still the answer to it: "A banana is about 105 calories"
        # after "how many calories in a banana" / "how much" is what the person is asking for,
        # and it is said plainly rather than behind a "Same as before" pointer at the card.
        same = (_the_sentence_with_a_figure(mem.last_bot(memory))
                if _A_BARE_MEASURE.fullmatch(str(text or "").strip()) else "")
        if same and not _REPEAT_OPENS.match(same):
            return same
    if _asks_who_the_bot_is(memory.get("understood"), text):
        # The bot's own identity is not a fact about the world: `greeting` answers it (who it is,
        # what it can do, where it lives). Nothing in the knowledge base is about it, and the
        # readers below that draw on the last answer - the bare ask, the dish plan, the part cut
        # out of it - all read a subjectless question as being about what was just discussed.
        return None
    if isinstance(text, str) and PLAN_RECALL.search(text) and _keeps_a_plan(memory):
        # "what was I planning?" is the plan said back, not the plan advice.
        return None
    if limit.reads_the_answer(text, memory):
        # The line limits the answer just given: the memory lane answers it from that answer's
        # steps, and re-asking the knowledge base with the limit appended is how "ants with a cat
        # in the house" reached the entry about rehoming a pet.
        return None
    if tried.might_be_a_report(text) and tried.pool_for(text, memory):
        # "i tried that and it didn't work", "still blocked": the person is reporting on the
        # answer just given, not asking for it again. Handing the same instructions over is the
        # one thing a friend never does, so the follow-up goes to `chat`, which says the next
        # step (`bot/memory/tried.py`).
        return None
    if returned.pool_for(text, memory):
        # "the smell came back after a week": the answer has not held and it already names the
        # step for that point, so re-answering the words is wrong twice over - it either repeats
        # the answer or swaps to an entry about one word of it ("i scrubbed it with bleach and it
        # came back" reached the bleach-or-vinegar comparison). `chat` says the step
        # (`bot/memory/returned.py`).
        return None
    if length.only_a_length(text) and ack.reply(text, memory):
        # "its been like that for about a week" after the answer: how long it has been going is
        # news about that answer, not a new ask and not a part of the answer to cut out. The
        # repeat machinery here reaches the same entry and says the paragraph again, which is
        # what the person has just read; the store replies with the question a length asks.
        # Passed only when the store has that reply, so a length this module does answer keeps
        # its answer.
        return None
    if mem.facts.a_name_picked(text, memory):
        # "we got a kitten" / "what should we name her" / "pepper": the word is the name they
        # chose, not a thing to look up. The store keeps it and says it back, and an entry about
        # peppers answers the word while missing the question - which is the one the bot asked.
        return None
        return None
    if about_the_chat(text):
        # "how did we start?" is a question about this chat, not about the dish on the table.
        # The memory store answers it from the turns; a fact entry answering it ("the chicken
        # takes an hour forty") is the knowledge base talking about the wrong thing.
        return None
    if taste.asks_about_a_taste(_the_line_as_said(text)):
        # "do i like curry and rice?" is a question about them, and the store keeps the answer.
        # An entry about rice answers the word, not the question: the person asked what they
        # like, and a recipe is about the food.
        return None
    if recall.ask(text) and not HOW_TO.search(_flat(text)):
        # "and where do i work", "what was my name", "what do i do for a living": the line asks
        # for one of their own facts, and the store has it. An entry answers the words it shares
        # with the question instead: "and where do i work" after a night shift reached the rota
        # and answered "the law gives you 11 hours off between shifts", which is not where they
        # work. The recall is the store's, and no fact entry is about them.
        # A how-to is a request even when it names one of their own things: "how do i live on a
        # budget" reads as a recall to ask() because live and budget are both subject words, and
        # the store has nothing to hand back for it.
        return None
    if taste.only_a_taste(_the_line_as_said(text)) and not _a_pick_is_asked(text):
        # "i like dogs but i hate cats" is a preference, not a household: an entry about
        # introducing a dog to a cat answers the two animals and the word "hate" in the line, and
        # told the person to keep their (nonexistent) pets behind a baby gate. The store says the
        # taste back, which is what the line is.
        # A diet is the one taste that is also a constraint on what to cook: "im vegetarian and i
        # dont eat dairy" was said back as "good to know", when the useful answer is a dinner
        # that is both and the labels that break it. The diet table is asked first, and a line it
        # really answers goes on to the entries.
        read = memory.get("understood") if isinstance(memory, dict) else None
        if not isinstance(read, dict):
            read = understand(text, memory)
        if not (dishes.has_a_diet_reply(memory, read)
                or dishes.has_a_dislike_reply(memory, read)
                or _a_choice_with_one_thing_left_out(text)):
            # A taste about a thing the entries answer by *choosing* is a constraint on the
            # choice, not a taste to file away: "i dont want a scary film" is asking for a film
            # without the scares, and standing down handed it to the store, which said it back
            # ("Noted: you don't want a scary film") while the gentle list sat one entry away.
            # A taste about a thing they own or meet ("i hate cats") is still the store's, which
            # is why the line has to name what is being chosen as well as what is left out.
            return None
    understood = memory.get("understood")
    if not isinstance(understood, dict):
        understood = understand(text, memory)
    # "will they get on?" after a new kitten and an older cat names neither animal. The
    # store knows both, so it can turn the line back into the question it is about before a
    # last-answer reader treats it as more talk about the older cat's health checks.
    introduction = mem.introduction_question(text, memory)
    if introduction:
        intro = understand(introduction, memory)
        item, reply = _offer(lambda reject: find(intro, reject=reject), memory, intro)
        if item is not None:
            return reply
    if _the_food_they_do_not_eat(text, understood):
        return None
    if _store_keeps_the_line(text, understood):
        # "my budget is 400 pounds" hands the store a value and "whats my budget" asks it for
        # one, so an entry about budgeting is answering the wrong question. The store says the
        # value back ("Your budget is 400 pounds") and the recall ("Your budget is £500"), which
        # is the reply the person wanted. Only when the slot the store reads is one of the
        # entry's own words: "im 34 and thinking of going back to uni" states an age, and the
        # answer about university is still the right one.
        return None
    if isinstance(text, str) and RECALL.search(text) and not recall.asks_for_a_word(text):
        # "What did I say my budget was again?" is a question about the conversation, and the
        # memory store answers it better than any entry: read with the topic written back in
        # ("... used car"), the knowledge base would answer the topic instead of the question.
        #
        # "What do you call a baby goat" is not that question: it wants the word the world uses
        # for a thing, and the entry that holds the word was stood down here on "what do you
        # call". The article is what tells the two apart - a recall points at what was said
        # ("what did i call my cats", "what do you call them") and a thing is named with "a" or
        # "an" - so that shape is read as the entry's ask.
        return None
    # "thanks, that helps" in the middle of a thread is a thank you, and the chat module has the
    # reply for it. Read as a follow-up it picks up the topic's words instead and answers the
    # question it was thanking us for a second time ("my cat died last night" then "thanks, that
    # helps" got the cat-sleep fact). Nothing in the knowledge base is about a bare thank you.
    #
    # A thank you with a question after it is still a question: "thanks, one more thing - how do
    # i clean the oven" reads as a question because it is shaped like one, and the oven question
    # after it is not thrown away with the thank you. A thanks line that only carries an ask word
    # it does not ask with ("thanks, that explains the boiler" carries "explains") is still a bare
    # thank you, which is the reading `_a_bare_thanks` asks for.
    if _a_bare_thanks(understood):
        # A thank-you in front of a line of its own is that line, not a thank you: "cheers. also im
        # skint till friday and theres nothing in the fridge" is the money line, "thanks. my back
        # has gone" the back one. Read whole, the thank you came first and the knowledge base
        # stood aside for it, so the turn went to the chat module's "Happy to help." and what the
        # person asked after the ack was dropped - which is how a "cheers." turns a question into
        # a shrug. The ack is cut off and the rest read as the line it is; a line that only closes
        # the turn ("thanks, that helps") has nothing after the ack, and one that agrees to try
        # something ("thanks, ill try that tonight") belongs to the chat module.
        rest = repeat.after_an_ack(text) if isinstance(text, str) else ""
        reread = understand(rest) if rest else None
        if (not isinstance(reread, dict) or reread.get("agrees_to_try")
                or reread.get("kind") in (None, "thanks", "greeting", "empty")):
            return None
        text, understood = rest, reread
    # A diet named in the middle of a meal being planned is about the dish, not a fact to say
    # back: "what should i cook" then "she doesnt eat meat" wants the vegetarian dinner. The
    # same words in a line of their own are the memory store's ("Your mum doesn't eat meat."),
    # so the plan only steps in front of it once it has answered with food.
    # "is it done" while something is in the oven asks when it is cooked, and the plan's own
    # `done` sentence says exactly that ("the juices from the thigh run clear"). The dish
    # follow-up just below answers a planned dish with the whole plan instead - "20 minutes per
    # 500g plus 20 minutes" - which is the timing said a second time: "how do i roast a chicken"
    # then "is it done" got "Same as before: About 20 minutes per 500g..." on main, while the
    # foods with no plan of their own already got their doneness sentence. The doneness ask is
    # answered from the food's own sentence first, and the plan answers the rest.
    # A line that says a food was left out on the side is a food-safety line, whatever the talk
    # before it was about: "i left the chicken out for a few hours", "can i still cook it" and
    # then "i left the mince out all night" was answered with a recipe for the mince - the dish
    # follow-up read the third line as being about the meal the talk had been on. The leaving
    # rule's own answer is the one that belongs on that line.
    left_out = freshness.says_a_food_was_left_out(text)
    if not left_out:
        # "can i still cook it" after "i left the chicken out for a few hours" is the leaving
        # question again, with the food and the hours left in the line before: the verdict is the
        # answer, and it is given before the dish follow-ups below, which read the line as being
        # about the meal and hand back a recipe for the food the bot just said to bin.
        verdict = freshness.the_still_ok_follow_up(text, memory)
        if verdict:
            return verdict
    if not left_out and dishes.ask_kind(understood or {}) == "done":
        readied = dishes.follow_up(memory, understood)
        if isinstance(readied, str) and readied.strip():
            return readied
    if not left_out and _a_dish_was_offered(memory):
        planned = cooking.follow_up(understood, memory)
        if isinstance(planned, str) and planned.strip():
            return planned
    if _someones_else_diet(text, memory, understood):
        return None  # the memory store says it back with the person's name
    if _asks_about_their_taste(text):
        # What a visitor likes or hates is kept against that person, and a dish is no answer to
        # it: "and what does she not like" after "she's vegetarian and cant stand museums" came
        # back as the meat-free dinner.
        return None
    calculated = solve(text, understood, memory)
    if isinstance(calculated, str) and calculated.strip():
        return calculated
    if _filling_in_an_emergency(understood, memory):
        # The person is talking, not asking: the modules for the person take the turn.
        return None
    # "it started when i moved house" says when the thing the bot has just answered began, and the
    # clause is the cause, not a new subject: without this, `house` is a kind of music and the
    # person is told about Daft Punk instead of about their sleep. The reading passes on every
    # line that is not an onset statement, and on a body complaint (a move that hurt their back
    # is a lifting injury).
    began = onset.reply(text, memory)
    if began:
        return began
    # "something quick please", "and no cheese either", "she doesnt eat meat": the next line
    # often only narrows the dish already on the table, which no entry and no single line of
    # the pantry can see. The plan kept in memory answers it, and passes when it cannot.
    # "i need something for a headache" asks for what helps the headache, and "something" is the
    # one word no entry is keyed on, so the pain, the burn and the cough all missed and the line
    # was read as a request for a suggestion ("Something for a headache? Tell me what you've
    # enjoyed before and I'll suggest something."). Asked as the question the tables know, the
    # problem is answered. It runs before the meal ideas because "i need something for a headache
    # fast" was a dinner: the "fast" is how soon they want help, not what they want to eat. On a
    # line with no answer of its own this changes nothing.
    helped = _something_for(text)
    if helped:
        again = understand("what helps " + helped, memory)
        other, said = _offer(lambda reject: find(again, reject=reject), memory, again)
        if other is not None and isinstance(said, str) and said.strip():
            # "can i give my baby anything for a cold" captures only "a cold", so the baby never
            # reaches the check in _something_for and the re-asked line ("what helps a cold")
            # answered the grown-up question - honey in warm water, which a baby must not have.
            # The give is what makes the person the patient, so the line's own reading is asked
            # first and kept when an entry answers it: the child-cold, the child-fever and the
            # child-cough rows own those lines, and a line the tables only know as a grown-up
            # problem ("can i give my son something for a sore throat") still gets the problem's
            # answer from the re-ask, as it did.
            given_to = SOMETHING_FOR_GIVEN_TO.search(_flat(text).lower())
            if given_to:
                own, own_said = _offer(lambda reject: find(understood, reject=reject), memory,
                                       understood)
                if (own is not None and own is not other and isinstance(own_said, str)
                        and own_said.strip() and _keyed_on_the_person(own, given_to.group(1))):
                    return own_said
            return said
    planned = (None if left_out else
               cooking.follow_up(understood, memory) or cooking.first_plan(understood, memory))
    if isinstance(planned, str) and planned.strip():
        return planned
    # A place word the line uses as a name is a name, not the city: the narrowed reading is the
    # one the rest of the turn uses, and nothing below may put the place back.
    reading = _without_names(understood)
    asked = _reword_ask(text)
    if asked is not None:
        if not asked:
            # "make it shorter" with nothing after it: the sentence is the one just handed over.
            before = _last_rewrite(memory)
            if before is None:
                return ("Paste the words you want to send and I'll soften them: who it is going "
                        "to helps too.")
            asked, tones = before
            return _rewritten(asked, tones | _tone_of(text), from_followup=True)
        return _rewritten(asked, _tone_of(text))
    # "shorter", "and friendlier" after a rewrite are about the sentence just given back.
    short_line = len(_flat(text).split()) <= 4
    if short_line and CONTINUED.search(_flat(text)):
        before = _last_rewrite(memory)
        if before is not None:
            asked, tones = before
            return _rewritten(asked, tones | _tone_of(text), from_followup=True)
    # The thing this line names for itself, if it names one: a line that opens its own subject is
    # not a follow-up about the last one.
    own = _own_thing(understood)
    # "how long do i cook it for" after "how long does cooked chicken last" is the method
    # question about the same food, not the keeping one again: the keeping answer has no
    # cooking time in it, and the part-taker below was trimming it to "3 days". The food is
    # what the conversation is on, so the line read with the food put back in reaches the
    # entry that knows the pan.
    cooked_ask = _a_cooking_ask_after_a_keeping_answer(understood, memory)
    if cooked_ask:
        return cooked_ask
    # A line that points back at the food instead of naming it ("what can i make with them",
    # "what should i do with it") has no food of its own for the pantry to work from, so it got a
    # list of quick dinners or a shrug. Read it as the earlier food plus these words, answer for
    # that food, and leave out what was just said so the follow-up is not the same words twice.
    pointed = cooking.pointed(memory, understood)
    # A side question pointed back at the dish ("what should i have with it") is that dish's own
    # side, not another dinner: the pantry read "pasta" out of a pasta bake and answered aglio e
    # olio, which is the bake over again. The plan already has the side, so hand it over here.
    if (pointed is not None and pairing(text)
            and cooking.SIDE_ASKS.search(_flat(text).lower())):
        side = cooking.side_for(memory, _flat(text))
        if side:
            return side
    if pointed is not None:
        said = tuple(text for text in (cooking.recent_replies(memory) or (mem.last_bot(memory) or "",))
                     if text)
        # A fresh dish first, then any other idea; a second way of saying the same dish beats a
        # shrug, so the food is never dropped just because everything was said once.
        picked = (cooking.dish(pointed, avoid=said)
                  or cooking.meal(pointed, avoid=said, pointed_back=True))
        if not (isinstance(picked, str) and picked.strip()) and not pointed.get("new_dish_only"):
            # Everything the table has for this food has been said already. The same dish again
            # is still better than "I'm not sure about that one" - "i have leeks" then "what can
            # i do with them" has nothing else to offer - but said flat it reads canned, so the
            # one we are going back to says so. A line that asked for a *second* idea is the one
            # case where the same dish is not an answer.
            picked = cooking.dish(pointed)
            if not (isinstance(picked, str) and picked.strip()):
                again = cooking.meal(pointed)
                if isinstance(again, str) and again.strip():
                    picked = (("The one I'd go back to: " + again[0].lower() + again[1:])
                              if again in said else again)
        if (isinstance(picked, str) and picked.strip()
                and not cooking.unusable(picked, pointed)):
            return picked
    # "Can I eat satay?" a turn after a peanut allergy is a yes or a no about peanuts, and that is
    # what they told us, not a new subject: the store answers it before any entry does, because an
    # entry about satay says how to cook it and no entry is about their allergy at all.
    suits = cooking.suits_them(understood, memory)
    if isinstance(suits, str) and suits.strip():
        return suits
    # A food somebody at the table will not eat is a limit on the dinner in the same words as an
    # allergy, and a line that names one and asks what to cook is the pantry's, before the food's
    # own card: "she wont eat cheese what can i cook" got cheese's calorie figure, and "my wife
    # wont eat bread what can i cook" the loaf's method, which is the one thing they cannot use.
    # Only where the pantry has a dinner to give: a bare "my daughter hates cheese" keeps its
    # substitute answer, because the kitchen has no dinner to suggest from it.
    without = cooking.a_dinner_without(understood, memory)
    if isinstance(without, str) and without.strip():
        return without
    # A line naming two or more things from the kitchen asks about the combination, and the
    # pantry table knows the dishes that use those things together: no entry does, because an
    # entry is keyed by one dish or one problem. One ingredient on its own is left to the
    # entries, which say more about it than a single dish can.
    named_foods = cooking.ingredients(reading)
    # Two foods are a "what can I make" question only when the line is asking for a meal: "is
    # oat milk gluten free" names oat milk and milk, and the dinner built from them answered a
    # yes or no with a bowl of porridge. A fact about the food is the entries' question.
    if len(named_foods) > 1 and not cooking.asks_a_food_fact(understood):
        # Two foods named in one line is a "what can I make" question, and it wants a meal: the
        # storage and safety entries answer a different question, so they wait until the dish and
        # the ideas have both passed ("ive got chicken and spinach in the fridge").
        cooked = (cooking.dish(understood, memory)
                  or cooking.meal(understood, memory=memory))
        # The kitchen the line describes is part of the line: a dish that needs the oven is no
        # dish at all to someone whose oven has broken ("chicken and rice and no oven").
        if isinstance(cooked, str) and cooked.strip() and not cooking.unusable(cooked, understood):
            return cooked
    # A meal idea we gave last turn states its own time, so "how long does that take" is a
    # question about our answer and the time in it is the reply. It runs before the entries,
    # because a word from the first line can win one of those instead: "i have chickpeas and
    # spinach in the cupboard" then "how long does that take" reads the cupboard, and the
    # cupboard-cleaning entry answers a question about a dinner.
    # A bare keeping question ("can i still eat it") after a line about a food of its own is
    # about that food, not about the last dish the store heard of: see the docstring.
    about_the_food = _keeping_about_the_food_there(memory, understood)
    if about_the_food:
        return about_the_food
    amount = _amount_asked(text, memory)
    if amount:
        return amount  # the figure for the amount this line names, not the one already given
    again = _the_amount_they_named_again(text, memory)
    if again:
        return again  # the size the answer already worked out, said in its own sentence
    # The same follow-up with "keep" in it wants the keeping fact, not the cooking time: twenty
    # minutes is how long the dish takes, and "how long does that keep" is a different question.
    # A food with its own keeping answer keeps it ("how long does that keep" after a boiled egg
    # wants the week an egg keeps, not the days any cooked dish does). This is tried before the
    # dish rule below, because that rule stands aside when the answer just given already carries
    # a keeping word: after "how do i store bread" the loaf's own answer is the answer, and the
    # general fridge table that would otherwise win tells people to keep a loaf in the fridge.
    if cooking.keeping_ask(understood) and _asks_storing(memory):
        specific = _keeping_entry(text, memory, _keeping_thing(memory), storing=True)
        if isinstance(specific, str) and specific.strip():
            # The storing answer is given out again when the food has no figure anywhere else,
            # and that is no use for the question asked: "how do i store bread" then "how long
            # does that keep" said the same paragraph twice, with no "3 days" in it. So when the
            # dish table knows the thing and keeps a figure for it, that figure is the answer.
            planned = _the_plan_keeps(understood, memory)
            if planned and _opening(planned) != _opening(specific):
                return planned
            return specific
    kept = cooking.keeping_followup(understood, memory)
    if isinstance(kept, str) and kept.strip():
        specific = _keeping_entry(text, memory)
        if isinstance(specific, str) and specific.strip():
            return specific
        planned = _the_plan_keeps(understood, memory)
        if planned:
            return planned
        return kept
    ours = _the_dish_time(understood, memory)
    if ours:
        return ours
    timed = cooking.timing_followup(understood, memory)
    if isinstance(timed, str) and timed.strip():
        return timed
    # A repair question about the machine the line before was about ("washing machine smells of
    # damp") is answered by that machine's own rule, before the part reader can cut a sentence
    # out of the answer just given.
    repaired = _the_machine_follow_up(text, reading, memory)
    if repaired:
        return repaired
    # An announcement that asks about cooking the dish in the same line ("im making a big
    # lasagne tonight, how long in the oven") is both things at once, and the plan is the
    # answer to both: the entry that fits the words is a category one (the pasta-bake method
    # bakes it 20 to 25 minutes at 200C, where this lasagne takes 35 to 40 at 180C). It runs
    # before the part reader, because that one reads the part out of the *previous* answer: a
    # pasta bake's 200C cut down to "200C." is not the lasagne's heat.
    if not _care_holds(text, memory):
        announced = dishes.announced_part(memory, understood)
        if announced:
            return announced
    # The part of the last answer is the answer only when the line asks about that answer. A
    # line that names a thing of its own is a new question: "can i freeze lasagne" after "can i
    # freeze cream" came back with the sentence about cream, because "freeze" was the one word
    # the two lines had in common. A line that only asks for a property ("what temperature?")
    # names no thing of its own however its words are read, so it is still about the answer.
    # A line that asks about a whole day or week asks about the period, not about the figure in
    # the answer before it: "how much sugar should i have a day" straight after a can of cola
    # came back as "A 330ml can of regular Coke has 35g of sugar." - the can's figure cut out of
    # the last answer, where the question is the daily limit and its own entry has it.
    # A follow-up that names another meal ("and for lunch") is the same question about the meal it
    # names, not a part of the answer just given: after a dairy-free breakfast it came back with
    # the breakfast list again. It is read with its own meal in it and answered as itself.
    meal = mem.meal_follow_up(understood, memory)
    if meal is not None:
        _meal_entry, _meal_reply = _offer(lambda reject: find(meal, reject=reject), memory, meal)
        if _meal_reply:
            return _meal_reply
    if _A_PERIOD.search(str(text or "")):
        asks_a_part = False
    else:
        asks_a_part = not (own and _new_thing(own, _the_run_said(memory, mem.last_bot(memory) or ""))
                           and not mem.asks_only(understood))
    if asks_a_part and named.asks_a_part_of_the_trip(text, memory):
        # A line that asks a part of the trip about the place in the chat asks its own question,
        # not for a slice of the card on the screen: after the card for a city, "how many days do
        # i need" was answered "The beach at Barceloneta for half a day." - the sentence of the
        # card that happens to hold the words "half a day", where the trip reader has the days
        # question for that place and the entry `city-stay` answers it.
        asks_a_part = False
    if asks_a_part and mem.answer_about(text, memory):
        # The line's words belong to an answer from earlier in the chat than the last one ("and
        # how long in the oven" after the cake, with a turn about the frosting in between). The
        # part it asks for is in that answer and the one just given is about the other thing, so
        # the entries answer the line rather than a part of the frosting.
        asks_a_part = False
    # A line the knowledge base answers on its own words is a question of its own, not a part of
    # the paragraph above it. "why do you want this job" after "how do i find a job" names no
    # thing with a possessive in it, so every gate above said "a follow-up", and the only word it
    # shared with the answer was "job": it was handed that answer's own sentence about jobs
    # ("Most jobs come through a person rather than a portal") where the interview row has the
    # answer to the line. The entries are asked before the part reader can cut a sentence out.
    # The line has to name a thing of its own for that: "how long does it keep" also has an entry
    # (the keeping row), and it is still a part of the answer just given - the lasagne card says
    # three months frozen where the line wants the three days the cooling answer gave.
    if asks_a_part and find(understood) is not None and understood.get("entities"):
        asks_a_part = False
    part = _part_asked(text, memory) if asks_a_part else None
    if part and cooking.keeping_ask(understood) and not FIGURE.search(part):
        # A keeping question is not a part of the answer just given when the figure in it is a
        # cooking time: "what can i make with eggs" then "how long do they last" cut the "2
        # minutes" out of the omelette recipe, which is how long it takes to cook, not how long
        # the eggs keep. The keeping answers have all been tried by now and had nothing, and a
        # sentence about days or weeks is the keeping figure the line asked for: "what can i do
        # with leftover chicken" then "how long will it last" was a shrug without it.
        part = None
    if part:
        # One part of the answer just given, not the whole answer again - with the detail the
        # line named in front of it when that part is already on the screen.
        return _the_part_said_again(part, text, understood, memory)
    again = _the_plan_said_again(understood, text, memory)
    if again:
        return again  # the same property asked again is answered again, not hedged
    earlier = _last_answer(memory)
    if (earlier and asked_kind(text) and _names_a_property(text)
            and _only_a_property(keywords(text))
            and not _a_property_word_names_a_thing(text)
            and not RATE.search(text)):
        # The line names a figure the answer just given does not have. Do not let a
        # different entry answer it with its own ("rest it" is not "roast 40 minutes").
        # A line that names a subject of its own ("what temperature for roast potatoes")
        # is a question for that entry, not this guard.
        plan = _the_plan_for(text, memory, understood)
        if plan:
            return plan  # the dish in the conversation states this part itself ("180C")
        # The figure the last answer lacks can still be the thing's own, and the line names the
        # thing only with its "that": "how much will that cost" after "we are going to rome" is
        # a question about the trip, and the trip's entry knows the cost. The words of the line
        # share nothing with the answer before it, so the key check below cannot see this; the
        # subject put back in is what reaches the entry, and the answer is the thing's own only
        # when that entry is about what the conversation is on.
        subject = mem.subject(memory)
        found, said = _the_answer_from_thing(text, subject, memory) if earlier else (None, None)
        if found is not None:
            # A thing the chat named after the subject answers instead of it: the second trip
            # is not priced with the first one's figure. A newer thing can only take the
            # answer away from the subject, never give one where the subject's entry has none
            # ("my boiler is making a noise" is not a price list).
            for thing in _the_things_to_try(understood, memory):
                if thing == subject:
                    break
                newer, newer_said = _the_answer_from_thing(text, thing, memory)
                if newer is not None:
                    return newer_said
            return said
        # It is still the same thing's question when the subject put back in reaches the entry
        # that answered last ("what temperature should the oven be?" after the cake timing), so
        # that entry may answer with the figure this line asks for.
        words = set(keywords(text))
        keys = set(earlier.get("keys") or ())
        if not words or not words <= keys:
            # The last answer's entry is not about what this line asks, but the line is still a
            # figure question about the answer just given: give the part of that answer that
            # carries the figure rather than a hedge. "i have an upset stomach" then "how long
            # does it last" reached nothing at all and was answered with a search, while the
            # answer on the screen says "it usually settles in two to three days". Only a line
            # that asks for nothing but the length takes it: one that names a thing comes back
            # here with no figure of its own, and the length before it is no fact about it.
            if not _asks_only_the_length(text):
                return None
            part = same_as_before(understood, memory)
            if part:
                return part
            # No sentence of the answer shares a word with "how long will that take" (a list of
            # steps for a blocked sink shares none), so there is nothing to quote: say that the
            # answer holds no time and give its first step, rather than hand the turn to a search.
            honest = _figure_missing(earlier.get("reply") or "", text)
            if honest:
                return honest
            return None
        fuller = _with_subject(text, memory)
        if fuller.strip() == text.strip():
            # The subject put back in ("how long will it take for the save for a house?") is not
            # this line's question when the line is a bare length ask about an action: the
            # string reaches an entry that shares a noun with it and answers something else.
            # Only an entry that answers a length may take the ask (_answers_a_length), and
            # _with_subject hands the written-out ask back only when there is one.
            fuller = text if mem.written_out(text, memory) else _about_subject(text, memory)
        same = find(understand(fuller, memory)) if fuller.strip() != text.strip() else None
        if same is None or not _is_about(same, mem.subject(memory)):
            # The ask written out with the action the chat is on takes the turn next, whatever
            # the answer before it was about: "im learning to drive" then "how long will it
            # take" is the driving entry's question, and the answer to the line before it was a
            # nudge. Only an entry that answers a length may take it (_answers_a_length).
            written = _written_ask_with_an_answer(text, memory)
            if written:
                fuller = written
            else:
                if not _asks_only_the_length(text):
                    return None
                part = same_as_before(understood, memory)
                if part:
                    return part
                honest = _figure_missing(earlier.get("reply") or "", text)
                if honest:
                    return honest
                return None
        reading = understand(fuller, memory)
    # A plan the conversation is cooking answers a follow-up about one of its parts, before the
    # entries do: "can I make it ahead" after "I'm cooking a pasta bake for eight people" is about
    # that bake, and the eight fits the party-hosting entry, which advises on a menu instead.
    # "keep" is here only when the line points back at the dish ("can i keep it in the fridge",
    # "how long will it keep"). One that names the food - "how long can i keep cooked chicken in
    # the fridge" - is a keeping fact, and the entry that knows it says more (raw 1 to 2 days,
    # cooked 3, go by the date on the pack) than the plan's one sentence does.
    PLAN_FIRST = ("ahead", "fill", "sides")
    kind = dishes.ask_kind(understood)
    words = {str(word).lower() for word in (understood.get("words") or ())}
    if kind == "keep" and words & {"it", "that", "this", "them", "they"}:
        # The plan's keep fact is what is left of a cooked dish, so it answers only when the
        # answer we are on was about cooking, or the thing the conversation is on has been
        # cooked. "raw chicken in the fridge" then "how long will it keep" was told the
        # leftovers keep 3 days, a day too long for raw meat, when the raw chicken answer
        # (1 to 2 days) is the one that belongs.
        if _the_plan_answers_this(memory) or _cooked_thing(memory):
            PLAN_FIRST += ("keep",)
    if (kind == "temp" and _the_plan_answers_this(memory) and _says_line(text, _OVEN_WORDS)
            and not _says_line(text, _OVEN_CHECK_WORDS)):
        # "what temperature should the oven be" in a cake chat asks for the cake's own figure
        # ("180C, or 160C in a fan oven"), and the oven-runs-hot card was taking it: setting the
        # oven is not a question about the oven being wrong. The line has to name the oven, so
        # "what temperature should the chicken be" keeps the internal 75C it asks for, and a
        # line about checking the heat keeps the card.
        PLAN_FIRST += ("temp",)
        # `own` here is the property the line asks for, not an entry, and it being set sent the
        # line to the card while the dish's figure was waiting.
        if own and str(own).lower() in _PROPERTY_WORDS:
            own = None
    if not own and kind in PLAN_FIRST and not _care_holds(text, memory):
        plan = dishes.follow_up(memory, understood)
        if plan:
            return plan
    # A detail about the thing in hand is answered about that thing or not at all, on every
    # reading of it below: the line alone, the line with its figure changed, the line read with
    # the topic beside it. One entry from another domain means the answer is to a different
    # question that happens to share the detail's words.
    off_topic = _off_the_topic(understood, memory)

    def _guard(reject):
        # The fence goes up when the chat's answer has a domain to be off, or when the line says
        # what the thing IS (a colour): both mean the line is about the thing in hand and an entry
        # from elsewhere is answering a question that shares its words. A detail that only says
        # what was done to it ("i painted it last year") names no subject of its own, so the entry
        # reached through the chat's own domain is the answer to it, which is what the bot gave
        # before the colour work and still does.
        if not off_topic[1] and not off_topic[2]:
            return reject
        return lambda one: reject(one) or _from_another_domain(one, off_topic)

    keeping = _keeping_reader(reading, memory)
    item, reply = _offer(lambda reject: keeping(_guard(reject)), memory, reading)
    if item is not None and item.id == KEEPING_FROM_THE_ANSWER:
        # The figure the answer just gave, handed back as it stands: the subject has drifted to
        # the last thing asked about ("cool", after "and how long do i cool it for"), so the
        # guards below would read the line against that word instead of against the answer.
        return reply
    if not own and (understood or {}).get("kind") == "statement":
        # A detail that narrows the trouble ("it's worse when I lie down", "it's sore when I
        # kneel") is still about the answer on the screen, and that answer usually holds the part
        # of it that speaks to the detail. Read as words it reaches the same entry again, whose
        # answer has just been given, so it is answered here before the repeat is dropped and the
        # turn goes to the chat.
        detail = _a_detail_answered(text, memory)
        if detail is not None:
            return detail
        # A figure the answer already speaks of is that answer's own sentence, not a shrug: "im
        # 34 and i want to run a 10k" then "i can do 5k now" was answered "I'm listening — say
        # more if it helps" while the answer on the screen said "If you can run 5k comfortably
        # now, eight to ten weeks is a realistic build."
        figure = _a_figure_the_answer_has(text, memory)
        if figure is not None:
            return figure
    if not own:
        # An ask that names only a detail of the thing the store holds is about that thing: after
        # "we got a puppy called Biscuit", "how do I stop the chewing" reaches the answer about
        # chewing a pen at a desk on its own words, and the puppy's own entry only when the kind
        # the store holds is read beside it. The memory decides that reading, and it is kept only
        # when it reaches an entry of its own - never the one the line alone already had.
        beside = the_thing_a_detail_belongs_to(understood, memory)
        if beside is not None:
            # The entry the stored kind and the detail were read together for is the only one
            # those words vouch for. When that entry is turned down, the next best card from the
            # same words is one the line itself never named, and it must not take the turn:
            # "my rabbit bites me when i pick him up" then "how long should i boil an egg" read
            # the egg line with the rabbit beside it, the cooking entry was refused, and the
            # rabbit's heat card answered a question about boiling an egg.
            vouched = find(beside)
            other, said = _offer(_keeping_reader(beside, memory), memory, beside)
            if (other is not None and vouched is not None
                    and getattr(other, "key", None) != getattr(vouched, "key", None)):
                other, said = None, ""
            if other is not None:
                if _said_before(said, memory) or _already_said(said, memory):
                    # The entry the detail belongs to has already answered - reaching it with the
                    # thing's kind read beside the line, or on the line's own words - and one
                    # detail of it is all this line names ("what about the chewing" after the
                    # chewing answer). The paragraph would come back word for word, so the detail
                    # is named in the lead-in and the part of it that answers is given instead.
                    again = _the_detail_said_again(said, text, memory)
                    if again:
                        remember_answer(memory, said, _key_words(other))
                        _remember_answer(memory, other, said)
                        return again
                if getattr(other, "id", None) != getattr(item, "id", None):
                    item, reply, reading = other, said, beside
    if item is not None and not own:
        # A follow-up names no thing of its own, so an entry about something else can take it on
        # its bare words: "and how long should i rest it" after a sore knee reaches the rest day
        # advice, and the knee never gets the line. The thing the conversation is on is what the
        # line is about, so the entry about that thing is taken instead - and only when it is
        # about that thing, so a line the other entry answers better is left alone.
        head = _head_thing(mem.subject(memory))
        # A line that names a food of its own is about that food, not the one on the table: "how
        # long do i reheat a pizza" after a chicken keeping answer was read with chicken put back
        # in and got the roast chicken's 20 minutes per 500g, where its own words reach the pizza
        # entry. The context entry only takes a line that names nothing but a property.
        other_food = _names_another_food(understood, str(mem.subject(memory) or "").lower())
        # A line asking what a word means is about that word, not about the talk: read with the
        # back pain of the turn before it, "what is an overdraft" took the lifting advice, and
        # "what is a recession" after a leap year took the leap year. The definition stands.
        defined = _a_definition_of_the_entry(text, item)
        if head and not other_food and not defined and not _is_about(item, head):
            other, said = _offer(lambda reject: _in_context(text, memory, reject=_guard(reject)),
                                 memory, reading)
            if other is not None:
                item, reply = other, said
    if item is not None and not own and not _about_the_talk(item, text, memory, reading):
        item, reply = None, None
    follow_up = False
    if item is None:
        # A follow-up that only changes a figure ("what about a 3kg one" after "how long do i
        # cook a 2kg chicken for") is the same question with the new figure in it. Read with the
        # earlier line's figure swapped out it reaches the entry the first line did, and the
        # entry works the new figure out from its own rule ("20 minutes per 500g plus 20").
        resized = resize.rewritten(text, memory)
        if resized:
            again = understand(resized, memory)
            # A headcount is worked out rather than looked up: "how much rice for 4 people" is
            # answered by the portion table ("75 g each, so 300 g for four") with no entry
            # behind it, so the corrected line has to be worked out the same way before an
            # entry is asked for it - the rice entry says 75 g a head and nothing about the
            # table of three, which is the number the person just changed.
            calculated = solve(resized, again, memory)
            if (isinstance(calculated, str) and calculated.strip()
                    and flat(calculated) != flat(mem.last_bot(memory) or "")):
                return calculated
            item, reply = _offer(lambda reject: find(again, reject=_guard(reject)), memory, again)
            if item is not None:
                # Not a follow-up in the repeat sense: the figure is new, so the answer is a new
                # one even though the entry and its rule are the same.
                reading, own = again, _own_thing(again)
        if item is None:
            if (ADDING_TO_THE_SUBJECT.match(text)
                    and not A_MEASURE_OF_THE_SUBJECT.match(text)
                    and _the_answer_was_about_the_subject(memory)):
                # "and what about holidays" adds a dimension to the thing on screen rather than
                # naming a new subject, so the thing is read with it before the earlier
                # question's shape is put back round it. Without this the long cat chat - "what
                # do i need", "how much does it cost", "what about holidays" - read the line as
                # "how much holidays", which is the paid holiday from work.
                other, said = _offer(
                    lambda reject: _in_context(text, memory, reject=_guard(reject)),
                    memory, reading)
                if other is not None:
                    item, reply = other, said
        if item is None:
            # A follow-up that only names a new thing ("what about a dessert") has no ask in it,
            # so no entry fits it on its own. Read as the earlier question with that thing in
            # place of the old one it reaches the entry the first line did - but only when the answer that
            # comes back is about the new thing, so a crumble answers a dessert question and the
            # dinner answer is never handed over as if it were.
            # The reading this has always used - the earlier question's word that its answer took
            # up - comes last, so an ordinary follow-up is read exactly as it always was. A repair
            # gets the other readings too: it says the earlier line had the wrong thing in it, and
            # that thing is not always the word the earlier answer took up. "how long does a
            # chicken take to roast" is answered with "20 minutes per 500g plus 20", which takes up
            # "take" and never says chicken, so "i meant a turkey" was read as "how long does a
            # chicken turkey to roast", reached nothing, and the person got "I'm listening - say
            # more if it helps" where the question in full gets the turkey's time. Worse, "how
            # long does chicken last in the fridge" takes up "fridge", so "i meant beef" swapped
            # the fridge and kept the chicken.
            older = swap.rewritten(text, memory)
            readings = swap.candidates(text, memory) if swap.is_repair(text) else []
            if older and all(read[0] != older[0] for read in readings):
                readings.append(older)
            if not readings and older:
                readings = [older]
            handed = None
            for swapped in readings:
                again = understand(swapped[0], memory)
                other, said = _offer(lambda reject: find(again, reject=_guard(reject)), memory, again)
                # An answer that is the paragraph already on the screen is turned down by
                # `names` (saying it again is not an answer about the new thing). It is the
                # answer, though, when the entry it came from is keyed for the word the follow-up
                # replaced: "what about the freezer" after the smell in the fridge reaches the
                # fridge entry, which is keyed for freezers too, and "what about the bathroom"
                # after ants in the kitchen reaches the ants entry, keyed on the kitchen.
                same_answer = (_already_said(said, memory)
                               and _written_for(other, swapped[1]))
                # An entry is about its subject and its answers do not always name it: the sink
                # entry says "rinse it after every wash-up" and never the word sink, so "and
                # under the sink" after the shower was turned down and the person got their own
                # words back ("Got it - under the sink"). An entry keyed for the new thing is
                # about it, whatever words its answer happens to use.
                thing = swap.thing(text)
                thing_words = set(re.findall(r"[a-z']+", str(thing or "").lower()))
                rest = " ".join(word for word in swapped[0].split()
                                if set(re.findall(r"[a-z']+", word.lower())) - thing_words)
                kept = _written_for(other, thing) and _more_than_the_thing(other, rest)
                if other is not None and (same_answer or kept
                                          or swap.names(swapped[1], said, text, memory,
                                                        question=swapped[0])
                                          or _about_the_rest_of_the_question(
                                              other, swapped[0], swap.thing(text))):
                    # That answer may be the one already on the screen, word for word: the entry
                    # is about the subject, so the same lines answer both rooms. Handing the
                    # paragraph back again is the bot repeating itself, so the rest of it comes.
                    if same_answer or _already_said(said, memory):
                        # Handing the paragraph back again is the bot repeating itself, so the
                        # part of it they have not read is what comes.
                        said = _same_where_they_asked(text, said) or said
                    item, reply, reading = other, said, again
                    handed = (other, said, again)
                    break
            if handed is None and _a_place_they_asked(text) and _a_place_of_the_same_kind(
                    earlier, text):
                # A place that no entry answers is still the place the answer they have was
                # asked about: "how do i stop condensation / and in the bathroom" reached the
                # bathroom's cleaning routine, whose answer is about a different job, and the
                # person was left with a search hedge while the advice about air and warmth
                # was one line above. What holds where they asked about is handed back, once,
                # under a lead-in that names it - and only the part they have not read.
                parting = _same_where_they_asked(text, mem.last_bot(memory) or "")
                if parting:
                    return parting

        if item is None:
            # A follow-up that only names a person ("what about my dad", "and something for my
            # brother") is the same question about somebody else: asked in full - "what should i
            # get my dad for his birthday" - it reaches an entry, while on its own it is a bare
            # ask and the person got the search hedge. The answer has to be about the new person,
            # which is checked by the old one not being in it and it not being the answer just
            # given said again.
            about_someone = swap.rewritten_person(text, memory)
            if about_someone:
                again = understand(about_someone[0], memory)
                other, said = _offer(lambda reject: find(again, reject=reject), memory, again)
                if other is not None and swap.names_person(about_someone[1], said, text,
                                                           mem.last_bot(memory)):
                    item, reply, reading = other, said, again
    # A follow-up about a part of a dinner plan is the plan's to answer, not the entry the line
    # reaches when it is read back with the dish put in: "how long should it be in the oven"
    # after "I'm cooking a pasta bake" reached the announcement and said the time again.
    PLAN_KINDS = ("fill", "sides", "done", "keep", "fix")
    care = item is None and _care_holds(text, memory)
    if item is None and not care:
        if dishes.ask_kind(understood) in PLAN_KINDS:
            # "And what should I put in it?" asks about a part of the plan, and the line as it
            # came in names no dish: read back with the dish put in ("I'm making a beef stew")
            # it reaches the announcement entry, which says the time it already said. The plan
            # answers the part, so it goes first.
            plan = dishes.follow_up(memory, understood)
            if plan:
                return plan
        if mem.asks_only(understood) and mem.last_module(memory) == "answers":
            # A line that only asks for a property ("how long?", "what temperature?") is a
            # question about what we are already talking about, not about a neighbour entry the
            # ask happens to fit: read with a subject put back in, "how long do I need?" also
            # reaches the boiled-potatoes entry after a tray of roast ones.
            # "how long do i cook it for" after "how long does cooked chicken last" is the
            # method question about the same food, not the keeping one again, and the keeping
            # answer has no cooking time to take out of it.
            cooked = _a_cooking_ask_after_a_keeping_answer(understood, memory)
            if cooked:
                return cooked
            # A line that names a food of its own is not asking about the one in the answer we
            # just gave: "how long do i reheat a pizza" after a chicken answer was handed the
            # chicken's figure out of that answer ("2 hours"), where the entry that knows pizza
            # has the 12 to 15 minutes. The bare asks ("how long?", "how long does it take")
            # name nothing, so they still take the figure out of the last answer.
            other_food = _names_another_food(understood, str(mem.subject(memory) or "").lower())
            if mem.has_time(mem.last_bot(memory)) and not other_food:
                said = same_as_before(understood, memory)
                if said and said != mem.last_bot(memory):
                    return said  # take the figure out of the answer we just gave
            # The answer just given has no figure for the property asked, and the entry that
            # gave it often has one: the same entry, asked with the line it leans on in front,
            # is the ask in its own words ("how long will that take" after the credit-card
            # answer is the payoff-length answer). Without this the line is read for an entry
            # of its own and a neighbour answers it - the travel-money entry, off the word
            # "take", told them what to carry abroad instead of what the debt takes.
            again = _the_entry_asked_again(text, memory)
            if again:
                return again
        if not care and mem.last_module(memory) == "answers" and _adds_a_figure(text):
            # The lines that add a figure to the answer just given - "it says 1.8 kilos" after the
            # per-kilo time, "we are 6" after the table for four - carry no ask and name no entry,
            # so the greeting echoed them back ("Got it - it says 1.8 kilos.") and the figure did
            # nothing. The entry that answered last is the one that knows what the figure means,
            # asked again with the line it leans on in front. Only when the figure is new to the
            # answer: "its 2 kilos" after the timing for a 2kg bird repeats the figure they were
            # just given, and a paragraph read out again is not an answer.
            again = _the_entry_asked_again(text, memory)
            if again and _new_figure(again, mem.last_bot(memory)):
                return again
            # The last answer had no figure in it ("180C, or 160C in a fan oven"), so the dish
            # plan is where the answer is: the plan says the whole thing in one sentence.
            if _the_plan_answers_this(memory) and not pairing(text):
                plan = dishes.follow_up(memory, understood)
                if plan:
                    # "what temperature?" asked twice is the same line in different words, so
                    # the count is of turns that already carried this sentence, not of turns
                    # that typed it: the answer comes whole with the same lead-in a repeated
                    # answer gets.
                    said = 0 if pairing(text) else _answer_said(plan, memory)
                    if said >= 3:
                        return AGAIN_HELP.format(reply=plan)
                    if said:
                        return AGAIN[said - 1].format(reply=_repeat_short(plan, text, memory))
                    return plan
        follow_up = True
        if WHEN_AM_I.search(text):
            # "when am i going" is a question about what they told us, not about the topic: read
            # with the topic put back in ("when am i going lisbon may") it reaches the trip entry
            # again and hands back the paragraph they just read. The plans memory answers it.
            return None
        # Nothing for the line on its own: a follow-up is about the last thing said, so the
        # earlier line it leans on is searched too (memory["understood"]["leans_on"]), with the
        # guards in lookup keeping a neighbour's entry out. Only after the line alone found
        # nothing, so an answer that fits stands.
        # A follow-up that names a food of its own is about that food: "how long do i reheat a
        # pizza" after a chicken answer was read with chicken added to it and got the roast
        # chicken's 20 minutes per 500g, where the line on its own reaches the pizza entry.
        # A follow-up that names another meal ("and for lunch") is the same question about the
        # meal it names, so it is read with its own meal in it before the earlier line is
        # searched: searched as it stands, the dairy-free breakfast and then "and for lunch" was
        # answered with the breakfast list again.
        meal = mem.meal_follow_up(understood, memory)
        if meal is not None:
            reading = meal
        other_food = _names_another_food(understood, str(mem.subject(memory) or "").lower())
        own_thing = _names_its_own_thing(text, memory)
        item, reply = _offer(
            lambda reject: find(reading, reject=_guard(reject),
                                use_context=not other_food and not own_thing),
            memory, reading)
        if item is not None:
            # A follow-up that asks how the subject turns out is answered by the row that
            # answered the line before it: "will it be alright" after the phone went in the sink,
            # "will it survive" after the laptop got coffee in it. The row has an answer of its
            # own for the ask when it declares one, and giving that is the whole turn - the card
            # itself has already been read out, and saying it again is the paragraph the person
            # is looking at. Without this the turn gave up and pointed at a search, over a
            # subject the bot had answered a turn before.
            owed = _the_outcome_owed(item, text)
            if owed and (_said_before(reply, memory)
                         or names_nothing_of_its_own(reading)):
                return owed
        if item is not None and _said_before(reply, memory):
            # The entry the line reaches with the topic behind it is the one that gave the answer
            # already on the screen: what the line asks is a part of it the store can ask for, out
            # loud, in the words the row is kept in. "i have a cough" then "will it go away on its
            # own" is the cough's own row about how long it lasts, and the store holds that
            # reading - the cheap answer here read out the cough answer a second time, and the
            # turn after it was a search hedge.
            wider = mem.followup_reading(understood, memory)
            if isinstance(wider, dict) and wider is not understood:
                wider_item, wider_reply = _offer(
                    lambda reject: find(wider, reject=_guard(reject)), memory, wider)
                if wider_item is not None and wider_item.key != item.key:
                    reading, item, reply = wider, wider_item, wider_reply
        if item is not None and not _about_the_talk(item, text, memory, reading):
            # The best entry is from a field this line is not about, and the field is against it
            # rather than the words: "should i tip a hotel cleaner" reaches the money table, and
            # the line is read as a travel one, so the money row is turned down and the turn went
            # to a shrug while the travel row for the same question sat one place below it. Ask
            # again with the domain as part of the refusal, so the next best entry gets the turn
            # a wrong-field entry took from it.
            item, reply = _offer(
                lambda reject: find(reading,
                                    reject=_in_this_conversation(_guard(reject), reading),
                                    use_context=not other_food and not own_thing),
                memory, reading)
        if item is None:
            item, reply = _offer(lambda reject: _in_context(text, memory, reject=_guard(reject)),
                                 memory, reading)

            # A question that picks between things and names nothing to pick for ("what should i
            # see?", "what could i get her?") is answered about the thing under discussion.
            chosen = _choosing(text, memory)
            if chosen is not None:
                reading, item, reply = chosen
    if item is None:
        # A short ask naming no thing of its own ("what should I see?", after a city) is about
        # the thing the conversation is on, so the thing is tried on the end of it.
        item, reply = _offer(lambda reject: _in_bare_context(text, memory, reject=_guard(reject)),
                             memory, reading)
        follow_up = item is not None
    # Whether the line is a bare ask of the thing the chat is on ("how much is a new one"), which
    # wants the figure even when the entry's whole answer has been read already. Bound here
    # because the repeat check further down reads it on the path where `care` is set and the
    # block below never runs; read unbound, the raise is swallowed by the runtime and the turn
    # goes to another module with nothing red to show for it.
    bare = False
    if item is None and not care:
        # A follow-up names no subject of its own ("and if I stuff it?", "he's allergic to
        # nuts") and a correction names the wrong one; read it with the topic's subject put
        # back in, but only when the line alone reaches no entry, so a fit answer stands.
        wider = followup_reading(understood, memory)
        if wider is not understood:
            reading = wider
            item, reply = _offer(lambda reject: find(reading, reject=_guard(reject)), memory, reading)
            bare = mem.bare_question(understood, memory)
            if item is not None and bare:
                # A line that asks for a price or a time wants the figure even when the entry's
                # whole answer has been read already: "how much is a new one" after the battery
                # answer is the seventy to a hundred and fifty pounds.
                #
                # What this does NOT do, and an earlier head of this PR did, is hand the turn to
                # the next entry that fits when the topic's own entry has nothing new. It read
                # "my daughter is nervous about starting secondary school" / "what can we do
                # before the first day" as the school-admissions entry, whose advice is to apply
                # by 31 October - a different question, months too late for a child about to
                # start, where the entry the chat was already on answers it. Stepping off an
                # entry by subject is not something the keys can be trusted with; the sentence
                # the line asks for, when the entry has one, is picked out below.
                figure = _asked_figure(text, reply, None)
                if figure:
                    reply = figure
            # A line that names its own subject is not a follow-up, however much it leans on the
            # last topic: putting the subject back in may add the thing the topic was about, it
            # may not replace the thing this line is about.
            if item is not None and own and not _is_about(item, own):
                item, reply, reading = None, None, understood
            # The entry has to be about what the line is about. One ask is already known to be:
            # the store writes a line that says nothing but a pronoun out loud with the thing in
            # it ("will it go away" after "i have a cough" becomes "how long does a cough take to
            # go away"), and it only does that when the row it lands on is about that thing, so
            # there is nothing here for the line to be checked against - its own words are "will
            # it go away", which name nothing. Judged on those words alone, every such turn was
            # turned down here and went to a search hedge with the right row found. Everything
            # else is judged on its own words, as before: a line that names something ("and no
            # oven") must not be carried off to another subject by the topic.
            written_out = (understood is not reading
                           and mem.topics.the_prognosis_the_line_asks(understood, memory) is not None)
            if (item is not None and not written_out and not _leans_on(understood, item, memory)
                    and understood.get("kind") == "question"):
                # The topic fits the shape of the ask but not what the line is about: "what
                # should I say on the first day" is not a question about clothes. Leave the turn
                # to another module rather than read the last answer back a sentence at a time.
                # Only a question can be carried off this way: a statement that carries the same
                # thing on ("its been like that for a week" after the fridge-noise answer) is
                # read with the topic exactly as before, and repeating the answer is right.
                # A "who should i call" is that case and the answer on the screen settles it:
                # the topic fits the shape of the ask, and the entry it reaches is the wrong one.
                someone = _the_person_to_call(text, memory)
                if someone:
                    return someone
                return None
            follow_up = item is not None
    if item is None and not care:
        # A bare duration ask written out with the action the chat is on: "im learning to drive"
        # then "how long will it take" is the driving entry's question, and neither the line nor
        # the subject put back in ("how long will it take learning to drive") reaches it. Only
        # the ask about time, and only when the chat is on something you do, so a line that names
        # its own thing is untouched.
        written = _written_ask_with_an_answer(text, memory)
        if written:
            asked = understand(written, memory)
            item, reply = _offer(lambda reject: find(asked, reject=reject), memory, asked)
            if item is not None and not _is_about(item, mem.subject(memory)):
                item, reply = None, None
            if item is not None and not _answers_a_length(item, reply):
                # The entry found shares a noun with the action but answers another question
                # ("moving house" reaching "how much deposit"): a hedge beats a figure about a
                # different thing, and what is on the screen can still answer the length.
                item, reply = None, None
            if item is not None:
                reading, follow_up = asked, True
    if item is None and not care and mem.written_out(text, memory) \
            and not same_as_before(understood, memory):
        # The line asks how long something the person does takes, and no entry answers that
        # ("i want to grow tomatoes" then "how long will it take"). Nothing here knows the
        # length, and the answer on the screen is how to grow them: the turn is left to say it
        # does not know, rather than repeat the answer with "Same as before" in front of it.
        # The answer on the screen does settle it when it carries the length itself ("i want to
        # lose a stone" then "how long will it take" is answered by its own "losing about 0.5
        # to 1kg a week is the rate that stays off"), so only an answer with no such part is
        # left alone here.
        return None
    if item is None:
        # The sentence of the last answer about the thing this line names: "will salt work" after
        # the carpet answer reaches no entry however it is read, and the sentence holding salt
        # answers it. A yes/no whose thing has an entry of its own ("should i take ibuprofen"
        # after "my back hurts") is answered by that entry above and never arrives here.
        about = _the_sentence_about(text, memory)
        if about:
            return about
        # "who should i call" after the answer about the thing that broke names nobody itself:
        # the person the answer already names is the reply.
        someone = _the_person_to_call(text, memory)
        if someone:
            return someone
        # The line is about the very thing the last answer was about, and the knowledge base has
        # one entry per thing: give the part of that answer this line asks for.
        # A use-it-up question is about the food it names, not about the dish on the hob: the
        # slice of the last answer the words point at ("medium heat on the hob") is not what
        # was asked, and it stops the pantry table building the ragu the mince is for. A question
        # read with the topic is the other exception: every sentence of that answer has been
        # said, so the part it would give is a repeat.
        use_up = any(phrase in text.lower() for phrase in dishes.USE_UP_PHRASES)
        followed = None if (use_up or bare) else same_as_before(understood, memory)
        if isinstance(followed, str) and followed.strip() and not _new_thing(own, followed):
            # The part comes back from the answer just given, and the line named a detail of the
            # animal they told us about: said plainly it is the same sentence twice in a row
            # ("what about the chewing" after the chewing answer), so the detail is named.
            return _the_part_said_again(followed, text, understood, memory)
        # A dish they are only thinking of ("i was thinking of a satay") is a yes or no about
        # their allergy, and no entry is about that: it is about the dish. Last, though, because
        # an entry that already answers them with a dish they can have ("i fancy a chicken
        # curry" -> chickpea curry) is the better answer, and a check would take its turn.
        thinking = cooking.considered(understood, memory)
        if thinking:
            return thinking
        # No entry is about this line by name, but a line naming what is in the kitchen ("eggs
        # and spinach, what can I make?") is still answerable: the pantry table builds a meal
        # from the ingredients named rather than from a keyword. It passes on anything that is
        # a timing, a safety question or a why, and on a follow-up that names no food itself.
        # "how do i make it up to my mum" is a table to the kitchen's words alone - "make", "up
        # to", and a person after it - and the tray bake for a crowd is no answer to a person
        # asking how to put something right. The composer's repair is that turn, so the pantry
        # is not shown this line (bot/compose/repair.py, amends_to).
        meal = None if amends_to(text) else cooking.meal(understood, text=text, memory=memory)
        if isinstance(meal, str) and meal.strip() and not cooking.unusable(meal, understood):
            return meal
        # Every reader above has passed, and the line points back at a thing the store holds:
        # "where should i keep it" after "im trying to save money" asks about the money, and
        # "where should i keep my money" is the entry. It is asked here rather than earlier so a
        # turn a sentence of the answer above can answer keeps that answer.
        pointed = the_ask_about_the_thing_it_points_at(understood, memory)
        if pointed is not None:
            item, reply = _offer(lambda reject: find(pointed, reject=reject), memory, pointed)
            if item is not None and isinstance(reply, str) and reply.strip():
                return reply
        # Nothing the knowledge base has fits this kitchen: say what can be cooked in the one it
        # has ("my oven is broken, what can i make for dinner" had no answer at all).
        return cooking.without(understood)
    if getattr(item, "fault", False):
        # A fault card is about the appliance; the line may still be asking what to eat without
        # it. "my oven is broken what can i cook" fits the plug-check card on the words, and the
        # dinner is the question, so the kitchen plan answers before the card does.
        kitchen = cooking.without(reading)
        if isinstance(kitchen, str) and kitchen.strip():
            return kitchen
    if not _usable(item, reading, memory):
        # The entry answers the words but not the kitchen: take the best entry that needs
        # nothing the line has not got ("no oven" once reached the roast-chicken timings).
        kitchen = cooking.without(reading)
        # "my oven is broken what can i cook" is a cooking question with a repair answer in the
        # table: the kitchen plan answers the part of the line that is a question, and it is
        # better than the plug-check card, which is for the appliance and not for dinner.
        if isinstance(kitchen, str) and kitchen.strip():
            return kitchen
        item = _next_usable(item, reading, memory)
        if item is None:
            return kitchen
        reply = _payload(item, memory, reading)
        # The entry that needs nothing the line has not got can still have no reply at all for
        # this line ("can i bake a cake with no oven" landed on the planning entry, which only
        # answers an announcement). The kitchen answer is better than a shrug, and it is the
        # answer to the part of the line that is a question.
        if not (isinstance(reply, str) and reply.strip()) and isinstance(kitchen, str):
            if kitchen.strip():
                return kitchen
    if isinstance(reply, str) and reply.strip():
        if not own and _reaches_another_subject(text, item, memory):
            # The entry the line reaches is about something the conversation is not. "any other
            # ideas" after a chat about what to watch asked for another film and got the
            # fifteen-minute dinners ("Quick: tuna pasta in 15, macaroni cheese in 25") because
            # "ideas" is in that entry's keys and the line names nothing of its own. A wrong
            # subject is worse than a shrug, so the entry stands down here, after every reader
            # has had its chance: a topic-anchored read of the same line shares the topic's words
            # and is never dropped.
            return None
        said = (_answer_said(reply, memory)
                if mem.asks_only(understood) and not pairing(text) else 0)
        # A line that names only a size ("how long for 250g") reaches the entry by name, so the
        # whole paragraph comes back before any follow-up is looked at - and the figure they
        # asked for is workable from the rate inside it. Only for a line about this entry and
        # nothing else, so "how long do i roast a 2kg leg of lamb" is not given the bird's rate.
        if (not own or _is_about(item, own)) and _only_a_size_of(item, text):
            sized = mem.sized_reply(reply, text, memory, _key_words(item))
            if sized:
                remember_answer(memory, reply, _key_words(item))
                return sized
        # A bare ask repeats the answer it is about ("what temperature?" after "what temperature
        # for a cake") without repeating the line, so it is counted by the sentence we gave and
        # not only by the line that asked for it. A question that says its own subject again
        # ("how long do I boil eggs for") is asking afresh and gets the plain answer.
        if not said and not follow_up and _said_before(reply, memory):
            # The line reaches the same entry on its own words, so the whole paragraph would be
            # said again word for word: give the part of it this line asks for instead.
            part = narrow(reply, text)
            if isinstance(part, str) and part.strip() and flat(part) != flat(reply):
                part = _part_not_repeated(part, reply, memory)
                if part:
                    # The sentence was said on the last turn as part of the same paragraph, so it
                    # comes back with the detail the line named in front of it: a sentence word
                    # for word twice in a row is the repeat STYLE.md says never to give.
                    again = _the_detail_said_again(reply, text, memory)
                    if again:
                        return again
                    return part
        # "which one?" is not the same line asked again: the answer they want is the one part of
        # the last answer that decides between the things, not the whole paragraph back with a
        # "Same as before" in front of it. Read it before the repeat framing takes the turn, and
        # only for a line that is one of the bare choice asks (`_the_one_to_pick` declines on
        # everything else: a comparison, a line with nothing being chosen before it, an answer
        # with nothing shorter to give).
        if CHOICE_ASK.match(" ".join(str(text or "").lower().split())):
            picked = _the_one_to_pick(text, memory)
            if picked:
                return picked
        same_line = _asked_again(text, reply, memory)
        # A line that names a food of its own is not asking for a part of the last answer: "how
        # long do i reheat a pizza" after a chicken keeping answer was cut down to that answer's
        # "2 hours", where the pizza entry had just found the 12 to 15 minutes.
        # A timing ask about an action the chat is on ("i want to grow tomatoes" then "how long
        # will it take") is not a part of the last answer: the answer on the screen is how to
        # grow them, and framing it "Same as before" is the bot's worst habit, not a length. When
        # the ask written out reaches no entry, the turn has nothing to say about the length and
        # is left to say so.
        if (not own and not same_line and _said_before(reply, memory)
                and not _names_another_food(understood, str(mem.subject(memory) or "").lower())
                and (not mem.written_out(text, memory) or same_as_before(understood, memory))):
            # The answer is on the screen but this line is not the same line: it leans on the
            # last answer for its subject ("what can we do before the first day", "anything to
            # do before it starts"). That is a follow-up asking for a part of the answer, and
            # framing it "Same as before" and cutting it to its opening sentence drops the very
            # sentence it asks about - the classmate line was right there in the answer. Whether
            # `follow_up` was read for the line does not matter here: the line names no thing of
            # its own, so what it is about is what we just said.
            part = same_as_before(understood, memory)
            if (isinstance(part, str) and part.strip()
                    and flat(part) != flat(mem.last_bot(memory) or "")):
                return part
        if said and mem.written_out(text, memory) and not same_as_before(understood, memory):
            # A timing ask about an action the chat is on ("i want to grow tomatoes", then "how
            # long will it take") read as a bare ask for a figure. No entry knows how long that
            # takes, and the answer on the screen is how to grow them: it is not that answer
            # said again, so it is neither framed as a repeat nor cut to its opening sentence.
            # The turn is left to say it does not know.
            return None
        asked = max(same_line, said)
        if asked and _said_before(reply, memory):
            # "Where do i start", "what should i do first" a turn after this answer: they are not
            # asking for the paragraph again, they are asking which part of it to do. The step is
            # already in the answer, so it is handed over in the answer's own words.
            move = repeat.the_move(text, reply, memory)
            if move:
                return move
            # The same line again, reaching the same answer: say it again with the lead-in a
            # repeat gets, rather than hand the turn over. The entry has nothing new, but the
            # person asked the same thing, and a shrug is the one answer a repeated question
            # must not get.
            if asked >= 3:
                return AGAIN_HELP.format(reply=reply)
            honest = _figure_missing(reply, text)
            if honest:
                return honest
            return AGAIN[asked - 1].format(reply=_repeat_short(reply, text, memory))
        # A bare ask names nothing of its own ("what am i doing this week", "how do i do it"), so
        # the answer coming round again is that same answer asked for again and is framed as the
        # repeat it is - even with an acknowledgement between. A line that names its own thing is
        # a question of its own and is left to the module that has something new about it.
        framed = mem.said_again(reply, memory, line=None if said_topic.names_nothing(text) else text)
        if framed:
            # Nothing smaller to give and the paragraph is already on the screen, so it comes
            # back as the repeat it is rather than printed twice word for word.
            return framed
        added = _the_new_part(reply, memory) if follow_up and _said_before(reply, memory) else None
        if added:
            # The entry says what it said before and then the sentence this line asks for: that
            # sentence is the answer, and the rest is a paragraph already on the screen.
            remember_answer(memory, reply, _key_words(item))
            _remember_answer(memory, item, reply)
            return added
        if follow_up and _said_before(reply, memory):
            # The entry has nothing new for this follow-up: give the part of the last answer
            # that fits, or let another module speak rather than say it twice. A line asking
            # for a price or a time gets the sentence that carries one: "how much is a new one"
            # is the figure they were told a turn ago, not a note on how to fit it. A choosing
            # question is worth one more try first: what the context reached is often the entry
            # that answered the line before ("interview-prep" for "what should i wear"), and the
            # outfit the line is really asking about is a different entry nothing has said yet.
            if _a_question_about_another_thing(text, reply, understood, memory, own, item):
                # A figure cut out of the answer on the screen is not this line's figure when the
                # line asks about a thing of its own that the answer never mentions: "how much
                # does a puppy cost" then "how much does a tattoo cost" was handed the puppy's
                # price as the price of a tattoo. A friend says what they do not know instead.
                return None
            figure = _the_figure(text, reply)
            if figure:
                return figure
            chosen = _choosing(text, memory)
            if chosen is not None and not _said_before(chosen[2], memory):
                return chosen[2]
            same = same_as_before(understood, memory)
            if same:
                return same
            # The entry the line reaches has nothing new, but the person asked a yes/no about a
            # thing it named ("does a plunger help" after the sink answer): the sentence of that
            # answer holding the thing is exactly what they asked for, and a shrug is not.
            sentence = _the_sentence_about(text, memory)
            if sentence:
                return sentence
            # The follow-up points back at the answer itself and the words it brings name no
            # thing to cut a sentence by: "what should i see there", after the city was already
            # described. The reply is on the screen, so it comes back framed as the repeat it is
            # rather than as a search hedge - a person who asks again gets their answer again.
            # Only a question: a detail they add ("its an old oak floor") leans on the last answer
            # without asking anything of it, and the acknowledgement it gets is the right reply.
            # And only for a line the answer is about: "how do i clean my boots" after "how do i
            # get rid of fruit flies" reached the fruit-fly answer on the word "clean" and came
            # back as "Same as before: Put a little cider vinegar..." for a line about boots. The
            # sentence about the thing, above, is the one thing worth handing back to a line that
            # names a thing the answer never mentions.
            # A line that names nothing of its own but the ask ("what helps" after the
            # shower-drain answer) is asking the same question about the same thing, and the
            # answer says how: nothing in it has to say the word "help" for the framing to be
            # right. Cut to the sentence with the move in it, so the person gets the step rather
            # than the paragraph they have already read.
            if (isinstance(understood, dict) and understood.get("kind") == "question"
                    and _covered(text, reply, memory, understood)
                    and not _asks_of_another_subject(text, understood)):
                # A yes/no ask is not the same ask again: "my back is sore" then "will it stop"
                # wants a yes or a no, and "Same answer, and it covers this" in front of the
                # paragraph is not one. Only an ask that names nothing and asks nothing to be
                # decided - "what helps", "what should i do" - is the question the answer on the
                # screen already answers.
                bare_ask = (not mem.topics.YES_NO.search(str(understood.get("clean") or ""))
                            and not [word for word in mem.content(str(understood.get("clean") or ""))
                                     if word not in ASKING and word not in BARE_GENERIC
                                     and word not in ASKING_VERBS and word not in PROPERTY_WORDS])
                if (bare_ask and isinstance(understood, dict)
                        and understood.get("kind") == "question"
                        and not _asks_of_another_subject(text, understood)):
                    return (same_again.instead(reply, text, memory)
                            or mem.said_again(reply, memory, line=text))
                return mem.said_again(reply, memory, line=text)
            # Nothing in the last answer matched this line's words, and a turn before it got no
            # answer at all, so the usual part-picking has nothing to hand over: "how do i clean
            # it off" after a burnt pan came back as "I'm not sure about that one - a quick
            # search". The answer still says how, so the step in it is given in its own words
            # rather than a hedge about a subject we have already answered.
            return repeat.the_move(text, reply, memory)
        if not asked and follow_up and _already_said(reply, memory):
            # The same answer, word for word, is still on the screen: say the part of it this
            # line asks for, or let another module speak rather than repeat it. Only a line that
            # had to lean on the last answer counts: a question asked again by name reaches its
            # entry on its own, and answering it twice is right. A bare ask is counted above,
            # so it is answered again with the lead-in a repeat gets rather than declined.
            figure = _the_figure(text, reply)
            if figure:
                return figure
            same = same_as_before(understood, memory)
            if same:
                return same
            if (isinstance(understood, dict) and understood.get("kind") == "question"
                    and not _asks_of_another_subject(text, understood)):
                return mem.said_again(reply, memory, line=text)
            return repeat.the_move(text, reply, memory)
        if asked >= 3:
            return AGAIN_HELP.format(reply=reply)
        if asked:
            honest = _figure_missing(reply, text)
            if honest:
                return honest
            return AGAIN[asked - 1].format(reply=_repeat_short(reply, text, memory))
        if not own and _said_before(reply, memory) and _covered(text, reply, memory, understood):
            # Nothing else narrowed it and the paragraph is word for word what the last turn said:
            # the line is a follow-up on the answer already given ("what about the chewing" after
            # the chewing answer), so the part it asks about comes back with the detail named
            # rather than the same paragraph twice. STYLE.md, "Never answer the same way twice in
            # a row", and a repeat printed twice reads as a machine.
            again = _the_detail_said_again(reply, text, memory)
            if again:
                return again
            framed = mem.said_again(reply, memory)
            if framed:
                return framed
        if _a_question_about_another_thing(text, reply, understood, memory, own, item):
            # The answer on the screen is about the thing the chat was on, and this line asks its
            # own question about a thing of its own that the answer never mentions: it is not this
            # line's answer, neither framed as a repeat nor said plainly.
            return None
        # Keep the answer whole: a later follow-up may need a sentence of it that this turn is
        # about to be trimmed to, or that a trimmed answer no longer carries.
        remember_answer(memory, reply, _key_words(item))
        _remember_answer(memory, item, reply)
        # The paragraph is already on the screen word for word, and this line named something of
        # its own, so no lead-in applies to it above and the entry has nothing new: say the short
        # of it rather than print it twice (bot/memory/again).
        return same_again.instead(reply, text, memory) or reply
    return None

from ..memory import again as _never_twice  # noqa: E402 - applied once the module is defined

# Whatever this module answers, the last thing that happens to it is the earlier-turn
# check (bot/memory/again.replied): `answers` alone served a card again on 59 deck turns.
respond = _never_twice.replied(respond)

from ..memory import paragraph  # noqa: E402 - the floor is applied once the module is defined

# And the floor under all of it: a paragraph the chat has *had* is not printed again in the same
# words. `again.replied` above frames a repeat of the answer just given; this one frames a card
# that comes back several turns later, after a turn about something else, which no reader sees.
respond = paragraph.then_framed(respond)
