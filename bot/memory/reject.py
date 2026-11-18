"""They turned down the answer the bot just gave, and it owes them another one.

"whats a good film tonight" / "nah not that one" is a conversation still going somewhere. Main
answers it by saying the line back - "Got it — nah not that one." - which is the coldest reply
there is: the three films the bot named a turn ago are still on the screen, one of them has been
ruled out, and the person is asking, in four words, for the next one. The same shape arrives as
"dont fancy it", "ive seen it", "already read that one", "not for me" and "nah not those".

So this reads the refusal and the answer it refuses. Two rules keep it to the lines it is good
at:

* the whole line has to be the refusal. Every word, once the chat-speak is taken off, has to be
  a word for turning something down or one of the pronouns that point at it ("that", "it",
  "those"). "nah just eggs and some rice" is a person saying what they have, not a refusal, and
  one word this module does not know sends the turn back to the rest of the bot.
* the answer has to have offered things to choose between, read out of the bot's own last reply
  the way "you pick" is (bot/memory/choice.py). A refusal of advice with no choice in it ("do i
  need a coat" / "not today") is not a choice to make again, and the ordinary pools answer it.

What comes back is one of the things the bot itself offered, never a new fact: a title, a dish
or a price it can read off its own last reply. When the line rules the whole list out ("ive seen
all those") there is nothing left to hand over from it, so the reply asks the one thing that
lets the bot pick again - what they did like - rather than offering the same list a second time.
"""
import re

from ..compose import pick
from . import choice, recent

# The module whose replies hand over another option: a search back for the offer walks over its
# own lines and over nothing else.
MEMORY_STORE = "memory_store"

# Taken off before the line is read: the courtesies and pauses a refusal arrives wrapped in.
FILLER = frozenset("""
    ok okay oh ah well right so then but and just really sorry ta thanks thank you thx cheers
    hmm erm uh um like actually honestly tbh though tho anyway ha haha lol x xx please pls
    i im ive id ill we youre you u us for of about at in too either also still yet neither
""".split())

# The words that turn something down.
NEGATION = frozenset("""
    nah no nope none not dont do not doesnt didnt didnt never aint already meh rather
""".split())

# The words that point at the thing being turned down.
OBJECT = frozenset("""
    that this it those these them one ones both either neither any all every everything
    thing things one either list two three
""".split())

# The words that say what was done with it: seen, read, tried, eaten, or simply not fancied.
JUDGED = frozenset("""
    seen saw watch watched read tried had have ate eaten got get fancy fancied like liked keen
    bother bothered feel feeling want wanted sound sounds sounded appeal appeals my me kind
    cup tea sort thing things type sort my mine thanks ta taste tastes
""".split())

# Done with it: "seen it", "already read that one", "we tried that". These turn a thing down
# without a "no" anywhere in the line.
DONE = frozenset("seen saw watched read tried had ate eaten got heard done".split())

# "got it, thanks" is the commonest way of saying "I follow you" in a chat, and "got it" is also
# how a person says they already have the thing. The possession verbs are the only judged words
# in it, so a line that turns down nothing ("no", "not", "dont"), names no other judgement
# ("seen", "read", "tried") and does not say they have it already is the first meaning: an
# acknowledgement, which is the chat module's turn and not a request for another option.
POSSESSION = frozenset(("got", "get"))
A_HAVE_ALREADY = re.compile(
    r"\b(?:already|before|once|one|ones|last|year|years|since|when|ever|yet|ages?)\b", re.I)
# "I've got it" is the opposite of "got it": the subject in front of the verb says they hold one
# already, where a bare "got it" is a person following along.
_I_HAVE = re.compile(r"^\s*(?:i\s+have|ive|i\s+got|we\s+have|weve|we\s+got)\b", re.I)

KNOWN = FILLER | NEGATION | OBJECT | JUDGED | DONE

# A line that opens by asking the bot something ("have you seen it", "do you fancy it") is a
# question about the bot, not a refusal of its answer, with or without the question mark.
_ASKS_THE_BOT = frozenset("""
    have has do does did can could would will shall is are was were am any anything
""".split())

# "those", "them", "all of it": the refusal covers the whole list rather than its lead pick, and
# then there is nothing in that reply left to hand over.
_WHOLE_LIST = re.compile(
    r"\b(?:all|those|them|these|both|every|everything|any|list|three|two)\b", re.I)

# The offers this module must not answer: a reply that is itself a question puts the choice to
# the person ("Saturday or Sunday?"), and a refusal of it is a refusal to decide, not a request
# for another suggestion.
_OFFER_NOT_A_LIST = re.compile(r"\?\s*$")

# How another of the bot's own options is handed over. It has to read as a second suggestion,
# with whatever note the bot put on the option ("for comedy", "if you'd rather think") still
# attached, so the reason the bot gave for it comes with it.
ANOTHER = (
    "Fair enough \u2014 then how about {option}?",
    "Then {option} instead.",
    "Right, {option} is the other one worth a go.",
    "Not that one, then \u2014 {option}?",
)

# The whole list is out, so what the reply needs is the one thing that lets the bot choose again.
# It asks, and it stays short: a paragraph about how choice works is no better than the echo.
PICK_AGAIN = (
    "Fair enough, none of those then. What did you enjoy last? I'll pick something in that vein.",
    "Right, that list is out. Tell me one you did like and I'll go from there.",
    "Fair enough. What have you enjoyed lately? I'll keep clear of these three.",
)

# "them all" is not a turn-down: the person wants every one of them ("them all please", "all of
# them", "all three"). Handing back "that list is out" contradicts what they asked for, so all of
# the options come back by name. The had-it reading ("ive read them all") is a turn-down and gets
# the pool above.
ALL_OF_THEM = (
    "{which} then: {names}.",
    "All of them: {names}.",
    "Then take {which}: {names}.",
    "Good \u2014 {which}: {names}.",
)
# Two of the offer have already been spoken for, so there is no lot left to count: the honest
# answer names the one still on the table. "All 1 then: The Thursday Murder Club." was what the
# count came out as, and it named a title the person had turned down two turns before.
ONE_LEFT = (
    "That leaves one: {option}.",
    "Two of those are out, so it comes down to {option}.",
    "Then there is just {option} left.",
)
# "them all please" with one still on the table is a person taking it, not counting it: the
# count of what is left reads as the bot offering the same title twice when the one that is left
# is the one it handed over last turn ("Then The Midnight Library instead." and then "That leaves
# one: The Midnight Library."). They asked for the lot, so the answer hands it over.
ONE_TAKEN = (
    "Then take {option}.",
    "Then it is {option}.",
    "Go with {option}, then.",
)

# The words that mean the whole lot, rather than pointing at it: "them all", "all of them",
# "both". "none of those" and "not that one" point, and are the turn-down the pool below is for.
_THE_LOT = re.compile(r"\b(?:all|every|everything|both)\b", re.I)
# How many things can be handed back by name and still read as a list. A menu of three films or
# three books is a handful and naming all three answers "them all"; a paragraph answer - "free
# ones that work: a walk with a purpose (a park, a canal, the woods...), a museum or gallery, the
# library and a Saturday market" - offers seven pieces and is not a list anybody counts, so "done
# them all" there is the turn-down the pool below already has a line for, not a list read back.
THE_MOST_A_LIST = 5


def _words(text):
    """The line as words, chat-speak and courtesies stripped, or None when it is not a refusal."""
    low = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not low or "?" in low:
        return None
    low = low.strip(".,;:!-\u2026 ")
    # "don't" and "do not" are one word to the reader.
    low = re.sub(r"\b(?:do not|did not|does not)\b", "dont", low)
    low = re.sub(r"n['\u2019]t\b", " not", low)
    words = [w.strip(".,;:!-") for w in low.split()]
    words = [w for w in words if w]
    # "no thanks at all" and "not that one at all" carry the word "all" without counting
    # anything: the phrase is how firmly the no was said, and reading it as the lot handed five
    # films back under "All five then: Groundhog Day, ..." to somebody who had just turned them
    # down. So the pair goes before anything reads the line for the word "all" - and before the
    # courtesies are dropped, because "no thanks at all" loses "thanks" first and would leave
    # "no ... at all" reading as the lot.
    kept = []
    for word in words:
        if word == "all" and kept and kept[-1] == "at":
            kept.pop()
            continue
        kept.append(word)
    return [w for w in kept if w not in FILLER]


# "he has everything already" is about the person who is hard to buy for, not about the bot's
# list: the "already" is their possessions, not something the speaker has had off the list. Only
# a subject other than the speaker takes it out of the refusal reading - "i have everything
# already" and "we have everything" are still a turn-down of the whole offer. The line is read
# before filler is dropped, so the "i" and "we" that make it the speaker's own are still there.
_SOMEONE_ELSE_HAS_IT = re.compile(
    r"(?<!\bi )(?<!\bwe )(?<!\byou )(?<!\bive )(?<!\bweve )(?<!\byouve )"
    r"(?<!\balready )\b(?:has|have|got)\s+(?:everything|it all|the lot)\b", re.I)


def refusal(text, offer=""):
    """True when the whole line turns something down and says nothing else.

    `offer` is the bot's own last reply. It is the only place a word the module does not know can
    come from, because the thing turned down is often named rather than pointed at: "already had
    the frittata" and "seen the others" after the bot put a frittata and a ghost story on the
    screen. A name the offer does not contain is a line about something else - "nah just eggs and
    some rice" is a person saying what they have - and it goes back to the rest of the bot.
    """
    words = _words(text)
    if not words or len(words) > 7 or len(words) < 2:
        return False
    if _SOMEONE_ELSE_HAS_IT.search(text):
        return False
    unknown = [w for w in words if w not in KNOWN]
    if unknown:
        named = set(re.findall(r"[a-z']+", str(offer or "").lower()))
        if not named or len(unknown) > 3 or not all(w in named for w in unknown):
            return False
    if words[0] in _ASKS_THE_BOT:
        return False
    judged = {w for w in words if w in DONE}
    if (judged and judged <= POSSESSION and not any(w in NEGATION for w in words)
            and not A_HAVE_ALREADY.search(" ".join(words)) and not _I_HAVE.match(str(text or ""))):
        return False
    # One of the words has to be the turning-down itself, and one has to point at what it turns
    # down: a bare "nah" is a person done with the subject, not a request for another option.
    # "them all please" has no verb in it at all, and it is the plainest turn-down of a whole
    # list there is, so a line made only of words that point, one of which is the whole list,
    # counts too.
    if not any(w in NEGATION or w in DONE for w in words):
        points_at_the_whole = (_WHOLE_LIST.search(" ".join(words))
                               and all(w in OBJECT for w in words))
        if not points_at_the_whole:
            return False
    return any(w in OBJECT or w in JUDGED for w in words)


# A name that stops on the full stop of an initial: "*Wonder* by R. J. Palacio" is cut to
# "Wonder by R" by the italics reader, whose tail ends at a full stop. The surname is one word
# past the initial in the bot's own reply, so the name is finished off from there: the answer to
# "already read it" was "Not that one, then - Wonder by R?".
STOPS_ON_AN_INITIAL = re.compile(r"(?:^|\s)[A-Z]\.?$")
# What follows the initial in a name: another initial, then a surname.
NAME_GOES_ON = re.compile(r"\.?\s+((?:[A-Z]\.\s*)*(?:[A-Z][a-z'\u2019-]+)(?:\s+[A-Z][a-z'\u2019-]+)?)")


def _the_whole_name(option, reply):
    """The option, finished off when the reader cut it short on the full stop of an initial."""
    option = str(option or "").strip()
    if not STOPS_ON_AN_INITIAL.search(option):
        return option
    # The reply stars the title ("*Wonder* by R. J. Palacio"), so the name as it was read
    # ("Wonder by R") is not in it word for word: the last word of it is the initial, and the
    # rest of the name follows that anywhere in the reply.
    core = option.split()[-1].rstrip(".")
    found = re.search(r"\b" + re.escape(core) + NAME_GOES_ON.pattern, reply)
    if not found:
        return option
    rest = found.group(1).strip().rstrip(".")
    return (option if option.endswith(".") else option + ".") + " " + rest


def _tidy(option):
    """One option as it can be said back: the name, without a note the reader cut in half.

    The italics reader takes a short tail after a title as the bot's note on it ("*Knives Out*
    for a clever whodunnit") and keeps it, which reads well. A bracketed note arrives cut off at
    the comma inside it ("The Thursday Murder Club (funny"), and half a bracket is worse than no
    note at all.

    A figure is not a thing to choose: "6 minutes for a runny yolk, 7 for jammy, 9 to 10 for
    hard boiled" is one answer with times in it, and the answer to "not that" after a boiled
    egg was never "7 for jammy".
    """
    option = re.sub(r"\s*\([^)]*$", "", str(option or "")).strip()
    if re.match(r"^(?:\d|[£$€]\s*\d)", option):
        return ""
    # "A sandwich" is a thing on a list; in the middle of a sentence it is "a sandwich".
    option = re.sub(r"^(A|An|The) (?=[a-z])", lambda m: m.group(1).lower(), option)
    if not (2 < len(option) and len(option.split()) <= 10):
        return ""
    words = option.lower().split()
    if words[0] in _STEP_START or any(w in _CLAUSE_VERB for w in words[1:3]):
        return ""  # a step or a clause, not one of the things on offer
    return option


# A piece of a reply that cannot be the name of a thing: half a bracket, or a clause with a
# semicolon or a colon in it ("salted first; the skin crisps" was handed over as an option).
_NOT_A_NAME = re.compile(r"[()\[\];:!?]")

# The first word of a step rather than the name of a thing. A how-to answer reads as a list to
# bot/memory/choice.py the moment it has an "or" or a semicolon in it, and "roast chicken thighs
# at 200C" was handed back to a person who asked for another dinner.
_STEP_START = frozenset("""
    take put use add cook roast boil fry bake grill heat mix stir cut chop peel wash rinse spray
    wipe clean soak leave cover simmer drain season salt rest cool freeze store keep serve pour
    toss brush line preheat check test break slice grate whisk knead roll spread fill top drizzle
    sprinkle reduce blend mash layer wrap seal tie trim dry hang iron vacuum dust scrub hoover
""".split())

# A clause rather than a name, read off the verb that comes straight after its subject: "the
# juices run clear", "the skin crisps". Only inside the first three words, so a name that
# happens to hold a verb further in ("a voucher for something he already does") still stands.
_CLAUSE_VERB = frozenset("""
    is are was were has have had does do did will would can could make makes keep keeps help
    helps work works come comes go goes run runs give gives take takes last lasts win wins beat
    beats fit fits hold holds protect protects save saves cost costs sound sounds look looks
    taste tastes feel feels crisp crisps promise promises mean means sit sits stand stands need
    needs seem seems turn turns stay stays
""".split())


# A title the reply marks out with stars: "*Groundhog Day* for comedy".
_TITLE = re.compile(r"\*([^*\n]{2,40})\*")


def _by_title(titles, options):
    """The reply's titles, in the order it gave them, each with its note when that survived.

    bot/memory/choice.py drops an option whose note is a clause of its own: "*Arrival* if you'd
    rather think" is not a way of saying "Arrival", so the third film of three never reaches the
    list, and two refusals then run the offer out instead of naming it. The title is the thing to
    choose whatever the note after it says, so a title the reader dropped comes back as itself -
    a bare "Arrival" is what a friend would say.
    """
    if len(titles) < 2:
        return options
    ordered, seen = [], set()
    for title in titles:
        # The whole title is what tells two of them apart: matching on its first word makes
        # "*The Thursday Murder Club*" and "*The Midnight Library*" the same book, and the third
        # option of three then never reaches the list.
        low = title.lower()
        said = next((o for o in options if o.lower().startswith(low)), "")
        if said and said.lower() != low:
            # An option can run on past the title into the next thing ("The Mitchells vs the
            # Machines or *Matilda*"): the title is the thing to name, where a note after it
            # ("*Knives Out* for a clever whodunnit") stays attached.
            rest = said[len(title):].strip()
            if re.match(r"^(?:,|or\b|and\b|\*)", rest, re.I):
                said = said[:len(title)].strip()
        if not said:
            said = next((o for o in options if low in o.lower()), "")
        said = said or title
        if said.lower() in seen:
            continue
        seen.add(said.lower())
        ordered.append(said)
    return ordered if len(ordered) >= 2 else options


def _a_choice_of_things(reply):
    """True when the reply put things up to choose between, not advice with a list in it.

    A reply can read as a list to `choice.options_in` without offering a choice: the nail-biting
    answer ends "give that hand something else to do: a ring to twist, a pen, a stress ball",
    and a person who says "ive tried everything" after it was told "Fair enough, none of those
    then. What did you enjoy last? I'll pick something in that vein." - the wording for a
    shortlist of films. Those three are steps of the advice, not things to pick one of. A real
    shortlist says "or" ("... a frittata in 20, or a salmon traybake") or stars its titles.
    """
    reply = " ".join(str(reply or "").split())
    return len({title.lower() for title in _TITLE.findall(reply)}) >= 2 \
        or bool(_OR_CHOICE.search(reply))


# The line that says the whole of the advice was tried: "ive tried everything", "ive tried them
# all", "tried all of it". Only the trying words count. "done them all" after a list of free days
# out is a person who has been to them, and the offer still answers that; "tried everything" is
# the person reporting back on advice, which the composer has pools for (`fallback`, the tried-it
# and no-change lines).
TRIED_THE_LOT = re.compile(
    r"\btried\b[^.!?]{0,24}?"
    r"\b(?:everything|all of it|all of them|them all|it all|every one|the lot)\b", re.I)


def _the_offer_reply(memory):
    """The bot's own reply that put things up to choose between, or "".

    The refusal can be two turns after the offer ("nah not that one" / "nah not that either"),
    so the reply that counts as the offer is found the same way `_offered` finds it, not taken
    from the last turn alone.
    """
    for turn in reversed(recent(memory, 4)):
        reply = str((turn or {}).get("bot") or "")
        if reply and len(_options(reply)) >= 2:
            return reply
    return ""


def _options(reply):
    """The things one reply offered to choose between, or [] when it offered no choice."""
    reply = " ".join(str(reply or "").split())
    if not reply or _OFFER_NOT_A_LIST.search(reply):
        return []
    titles = [_tidy(t) for t in _TITLE.findall(reply)]
    titles = [t for t in titles if t and not _NOT_A_NAME.search(t)]
    options = [_tidy(_the_whole_name(o, reply)) for o in choice.options_in(reply)]
    options = [o for o in options if o and not _NOT_A_NAME.search(o)]
    options = _by_title(titles, options)
    # A single word is a title ("*Arrival*") or the tail of a list of fillings ("cheese, tuna,
    # ham, hummus"): only the title is a thing the bot offered to choose between, so a one-word
    # option that is not one of the reply's titles is a fragment and goes.
    known = {t.lower() for t in titles}
    options = [o for o in options if len(o.split()) > 1 or o.lower() in known]
    short = [o for o in options if len(o.split()) <= 8]
    options = short or options
    if len(options) < 2:
        return []
    # A choice says "or". "Cut the distance and the speed for a week or two: most running knee,
    # shin and ankle pain is too much, too soon, and hip and glute strength work fixes it" has a
    # comma list of nouns in it and choice.py reads three of them as things on offer, so "ive
    # tried that" was answered "Right, too soon is the other one worth a go." The last thing of
    # a real offer is introduced by "or" ("or *Arrival*", "or a salmon traybake"); a paragraph
    # joins its nouns with "and". A reply that stars two or more titles is a choice whatever
    # joins them ("*Get Out* ... and *Hereditary* ..."), so it is let through.
    if len(titles) < 2 and not _OR_CHOICE.search(reply):
        # An offer does not always say "or". The gift answer names what to buy after a colon -
        # "Pick something they'd use every week and wouldn't buy themselves: good coffee and a
        # proper mug, woolly socks, nice soap" - and a person who says "no not that" is asking
        # for another of those, not for "Fair enough." Prose is what the "or" gate keeps out, so
        # a list with no "or" counts only when the reply introduces it with a colon and every
        # piece of it is the name of a thing.
        if not (":" in reply and len(options) >= 3 and all(_a_noun_phrase(o) for o in options)):
            return []
    if _a_list_of_causes(reply, options):
        # A list of the possible causes of the fault is not a list of things to pick one of.
        return []
    return options


# The words that open a piece of prose rather than name a thing. "most running knee, shin and
# ankle pain is too much, too soon, and hip and glute strength work fixes it" has a comma list in
# it, and neither "most running knee" nor "too soon" is something a person could be handed
# instead of what they turned down.
_NOT_A_THING_START = frozenset("""
    most more less least too very so quite much many few little enough only even also still yet
    just then now and or but if when while as because than that this these those it they we you
    he she i is are was were be been being do does did done have has had will would can could
    should may might must not no never always usually often sometimes there here
""".split())


# The words that make the list after them the answer to why rather than a set of things to pick
# one of. "the boiler pressure keeps dropping" was answered "The pressure falls because water is
# escaping somewhere: a radiator valve, a joint, or the pressure relief pipe outside", and a person
# who said "ive tried topping it up" was handed "Right, a joint is the other one worth a go." - a
# cause of the fault offered as the next thing to try. A list of the possible causes is not an
# offer, whatever joins its pieces, so the "or" gate alone does not catch it.
_A_REASON = re.compile(
    r"(?:\bbecause\b|\bthe reason\b|\bwhich is why\b|\bthat'?s why\b|\bwhy\b|"
    r"\bsomewhere\b|\bcauses?\b|\bcaused by\b|\bis down to\b|\bcomes down to\b)"
    r"[^.;!?]{0,70}$", re.I)


def _a_list_of_causes(reply, options):
    """True when the "or" list the options came from is a reason rather than an offer.

    Only the sentence the option sits in is read, and only the words in front of it: a genuine
    offer explains itself afterwards ("Saturday market, or the library if it rains"), which is the
    opposite order and stays an offer.
    """
    flat = " ".join(str(reply or "").split())
    for option in options:
        at = flat.lower().find(str(option).lower())
        if at < 0:
            continue
        before = flat[:at]
        for stop in (". ", "! ", "? ", "; "):
            cut = before.rfind(stop)
            if cut > 0:
                before = before[cut + len(stop):]
        if _A_REASON.search(before):
            return True
    return False


def _a_noun_phrase(option):
    """True when an option reads as the name of a thing rather than a piece of a sentence."""
    words = str(option or "").lower().split()
    return bool(words) and words[0] not in _NOT_A_THING_START


# The join of a real offer: "... a frittata in 20, or a salmon traybake", "... the library, or a
# Saturday market". A paragraph joins its nouns with "and" and its clauses with a comma and a
# person ("see a physio if ... every run, or it is still there in two weeks"), and "a week or two"
# is a range rather than two things to pick from.
_OR_CHOICE = re.compile(
    r",\s*or\s+(?!(?:it|they|i|you|we|he|she|that|this|there|those)\b)", re.I)


def _said_by_them(option, text):
    """True when the person's own line says every word of `option`.

    A time after a dish is how long it takes, not part of its name: the offer says "Quick: tuna
    pasta in 15, a frittata in 20", and a person who says "already had the frittata" has named
    the frittata. The time stays in the line the module writes, because "how about a frittata in
    20?" is the useful form and "how about a frittata?" loses how long it takes.
    """
    option = re.sub(r"\s+in\s+\d+\s*(?:minutes?|mins?|min)?\s*$", "", str(option or ""))
    said = set(re.findall(r"[a-z']+", str(text or "").lower()))

    def every_word(name):
        words = [w for w in re.findall(r"[a-z']+", name.lower()) if w not in ("a", "an", "the")]
        return bool(words) and all(w in said for w in words)

    if every_word(option):
        return True
    # The bot's note on an option is not part of its name: the offer says "Knives Out for a
    # clever whodunnit", and a person who has seen it says "already seen knives out". Matching
    # every word of the whole option missed that, so the one film they had named was handed
    # straight back: "Fair enough - then how about Knives Out for a clever whodunnit?"
    name = re.split(r"\s+(?:for|if|which|when|that|to|in|about)\s+", option, maxsplit=1)[0]
    # A one-word name ("Up") would match any line with the word in it, so the name has to be a
    # name of more than one word before it is matched on its own.
    return len(name.split()) > 1 and every_word(name)


def _offered(memory):
    """The offer the refusal is about, as the options of it the bot has not named again.

    A second refusal ("then *Knives Out*" / "nah not that one either") is about the same offer
    as the first, so the search walks back over the replies this module itself wrote - the ones
    that hand over another option and name no list - and stops at any other reply. Options the
    bot has already handed over are taken out, so the third refusal gets the third film and a
    fourth gets the question that lets the bot pick again. None when no reply in reach offered
    a choice, which is the whole of the difference between "not my answer" and "not my line".
    """
    turns = [turn if isinstance(turn, dict) else {} for turn in recent(memory, 4)]
    start = None
    for index in range(len(turns) - 1, -1, -1):
        if len(_options(turns[index].get("bot") or "")) >= 2:
            start = index
            break
    if start is None:
        return None
    # A reply after the offer that this module did not write means the chat has moved on: a list
    # three answers ago is not what "not that one" is about.
    if any(str(turn.get("module") or "") != MEMORY_STORE for turn in turns[start + 1:]):
        return None
    # Replayed forwards from the offer, because what is left depends on what was refused and not
    # only on what was handed over. "already read that" names no title and takes the book the bot
    # led with, and the reply after it names the one it handed over - so walking back over the
    # bot's replies alone left the book they had already read at the head of the list, and "them
    # all please" then said it back ("That leaves one: The Thursday Murder Club.").
    left = list(_options(turns[start].get("bot") or ""))
    for turn in turns[start + 1:]:
        line = str(turn.get("user") or "")
        named = [option for option in left if _said_by_them(option, line)]
        left = [option for option in left if option not in named] if named else left[1:]
    return left


# The fence in a request: "not a scary one", "no horror", "anything but a romcom". The words
# after the refusal are what the person ruled out, before any list was put up.
_FENCE = re.compile(
    r"\b(?:not|no|never|without|except|anything but)\s+(?:a|an|the|any|too much|more)?\s*"
    r"([a-z][a-z'\-]{3,})", re.I)
# The word on the offer's own lead-in that says the fence was honoured ("For a film without a
# scare:") - so an offer that already left the thing out is not the thing ruled out.
_HELD_THE_FENCE = re.compile(r"\b(?:without|no|not|nothing|non)\b", re.I)

# The list the bot put up is the thing the person ruled out, so no title on it is an answer and
# every later hand-over from it would be another scary film. What helps is a different direction,
# asked for once per turn-down rather than the same sentence twice.
FENCED_OUT = (
    "Fair enough, nothing {kind} then. What do you fancy instead?",
    "Right, no {kind} ones. Tell me what you do want and I'll aim at that.",
    "Fair enough - {kind} is out. What sort of thing would you go for?",
)


def _the_fence(memory):
    """The thing the person ruled out in the request, when the offer that came back ignored it.

    `i fancy a film but not a scary one` is a request with a fence in it, and the film entry
    answered with the list of scares ("For a proper scare: Get Out, A Quiet Place, Hereditary").
    Every later turn-down then walked that same list - "then Get Out?", "how about Hereditary?" -
    so the fence cannot be read one title at a time: the offer's own lead-in is matched against
    the word the person ruled out, and the whole list stands down.
    """
    turns = [turn if isinstance(turn, dict) else {} for turn in recent(memory, 3)]
    offer, options, request = "", [], ""
    for index in range(len(turns) - 1, -1, -1):
        offer = str(turns[index].get("bot") or "")
        options = _options(offer)
        if len(options) >= 2:
            request = str(turns[index].get("user") or "")
            break
    else:
        return None
    ruled_out = [word for word in _FENCE.findall(request) if word not in KNOWN]
    if not ruled_out:
        return None
    # The lead-in is the offer's own words before the first thing it names: "For a proper
    # scare:". What comes after it is the note on each option ("not gory"), which is not the
    # offer saying what it is.
    started = [offer.find(option) for option in options if offer.find(option) > 0]
    lead = offer[:min(started)] if started else offer[:80]
    if _HELD_THE_FENCE.search(lead):
        return None
    words = [word for word in re.findall(r"[a-z']+", lead.lower()) if len(word) > 3]
    for fence in ruled_out:
        for word in words:
            if word[:4] == fence[:4]:
                return fence
    return None


def _the_whole_lot(options):
    """"both" or "all three", for however many of them are still on the table."""
    count = len(options or [])
    if count == 2:
        return "both"
    # Never a numeral: "All 1 then: ..." is what "all " + str(1) reads as, and a count of one is
    # not a lot. Below two the caller has already stopped counting.
    return "all " + {3: "three", 4: "four", 5: "five"}.get(count, "of them")


def offers_a_choice(memory):
    """True when the bot's last reply put two or more things up to choose between.

    A line that says the whole lot means something different either side of this: after three
    films "ive tried them all" says the list is out, and after a paragraph of advice it is a
    report that they have done what the advice said. The reader of the report asks this before
    it reads the line. A reply whose list is not a choice at all (`_a_choice_of_things`) is a
    paragraph of advice: the nail-biting answer's "give that hand something else to do: a ring
    to twist, a pen, a stress ball" was read as a shortlist, so "ive tried everything" after it
    was answered as a list refused rather than as a report on the advice.
    """
    if len(_offered(memory) or []) < 2:
        return False
    reply = _the_offer_reply(memory)
    return _a_choice_of_things(reply) if reply else False


def _the_names(options):
    """The options as one list read aloud: "a, b and c"."""
    said = [str(o) for o in options if o]
    if len(said) < 2:
        return said[0] if said else ""
    return ", ".join(said[:-1]) + " and " + said[-1]


def _the_lot_and_the_verb(lines):
    """(had the lot, wants the lot) for one line, read off the word that means all of it.

    "them all please" and "all of them" carry no word for having had them, so they are a person
    taking the lot. "ive read them all" and "seen them all" carry the had-it verb and are a
    refusal of the whole list. A line with neither ("none of those", "not that one") points at
    the list rather than covering it, and is the turn-down the pool below is for.
    """
    the_lot = bool(_THE_LOT.search(" ".join(lines)))
    return the_lot and any(w in DONE for w in lines), the_lot


def reply_for(text, memory):
    """Another of the options the bot just offered, or a question that lets it pick again."""
    if not isinstance(memory, dict):
        return None
    answer = ""
    for turn in reversed(recent(memory, 2)):
        answer = str((turn or {}).get("bot") or "")
        if answer:
            break
    if not refusal(text, answer):
        return None
    offered = _offered(memory)
    if offered is None:
        return None
    # The whole of the advice tried is a report on it, not a shortlist turned down: the
    # nail-biting answer's "give that hand something else to do: a ring to twist, a pen, a stress
    # ball" is not three things to pick one of, and "ive tried everything" after it was answered
    # "Fair enough, none of those then. What did you enjoy last? I'll pick something in that
    # vein." The tried-it and no-change pools of the composer answer it instead.
    if TRIED_THE_LOT.search(str(text)) and not _a_choice_of_things(_the_offer_reply(memory)):
        return None
    # The offer is the thing they ruled out, so it has no answer in it at all.
    fence = _the_fence(memory)
    if fence:
        said = pick(FENCED_OUT, memory, str(text)).format(kind=fence)
        return said[:1].upper() + said[1:]
    left = list(offered)
    # Which of them the line is about. A person who names the one they had ("already had the
    # frittata") has ruled that one out and nothing else, so the first alternative the bot put
    # up is still an answer and must not be thrown away with it. When the line points instead
    # ("not that one", "ive seen it"), it means the pick the bot led with, and the lead goes.
    named_by_them = [o for o in left if _said_by_them(o, text)]
    left = [o for o in left if o not in named_by_them] if named_by_them else left[1:]
    lines = _words(text)
    had_them_all, wants_them_all = _the_lot_and_the_verb(lines or [])
    if len(offered) > THE_MOST_A_LIST:
        # Nothing to count ("them all" against seven pieces of a paragraph): the turn-down pool
        # hands back the one question that lets the bot choose again.
        had_them_all = wants_them_all = False
    # The list read back is the one the bot put up, and the count with it: "both" against three
    # names is the same mistake as the menu again with a wrong number on it.
    if len(offered) < 2:
        # One option left of the three the bot opened with: "them all" has no lot to count, and
        # naming the single survivor back reads as the count "All 1 then". "Seen them all" has
        # nothing left to hand over at all, so it gets the question that lets the bot choose
        # again rather than the one title they have not had named at them.
        # "them all please" still wants the one that is left, so the count of what is left is
        # asked for only when the line is not asking for the lot.
        if had_them_all or not (left or wants_them_all):
            return pick(PICK_AGAIN, memory, str(text))
        pool = ONE_TAKEN if wants_them_all else ONE_LEFT
        said = pick(pool, memory, str(text)).format(option=(left or offered)[0])
        return said[:1].upper() + said[1:]
    which, names = _the_whole_lot(offered), _the_names(offered)
    if had_them_all:
        # They have had all of it already, so nothing in that reply is left to hand over - and
        # naming the lot back is the one thing this turn must not do: a person who has seen all
        # three is telling the bot the list is finished, not asking to hear it again. Main
        # answered this with the out-of-list line and it was right.
        return pick(PICK_AGAIN, memory, str(text))
    if wants_them_all:
        # "them all please" is a person taking the lot, not turning it down.
        said = pick(ALL_OF_THEM, memory, str(text)).format(which=which, names=names)
        return said[:1].upper() + said[1:]
    if not left or (lines and _WHOLE_LIST.search(" ".join(lines))):
        # Nothing of that offer is left to hand over: it has all been named, or the line rules
        # the whole list out in one go. What helps then is the one thing that lets the bot
        # choose again, not the same three films a second time.
        return pick(PICK_AGAIN, memory, str(text))
    # The order the bot gave them is the order they are handed over in, from the lead down: a
    # person working through a list of three gets the second, then the third, and never one it
    # has already named. Anything else repeats an option or jumps over one for no reason.
    option = left[0]
    said = pick(ANOTHER, memory, str(text)).format(option=option)
    return said[:1].upper() + said[1:]
