"""A question about how a thing of theirs went is theirs to answer, not a search.

On main "how was the wedding", "how did the scan go", "how are the kids" and "how is work" all
reach the composer's search hedge: "A quick search online will get you a solid answer". Nothing a
search turns up about the wedding is the wedding the person went to. The bot was not there and
cannot see the person's week; the one who knows is the person, and what a friend does with the
question is ask it back and let them tell it.

The reading is whose the thing is, which is the possessive in the line:

    how was the wedding        a thing of theirs     -> "How did it go?"
    how did the scan go        a thing of theirs     -> "I hope it went as well as it could"
    how are the kids           people of theirs     -> "How are they doing?"
    how is work                theirs              -> "How is it going?"
    how was your day           the bot's own day  -> not this file (the manners pools)
    how was the roman empire   a thing in the world -> not this file
    how long do i boil an egg  a how-to           -> not this file

"my/our/his/her/their <anything>" is a thing of the person's that the bot has no way to know, so
any noun after it is read as theirs. "the <thing>" is theirs only when the thing is the kind that
sits in a person's own life - an event, a person, a pet, work, the house, a meal, a journey - so
that list is what keeps "how was the war" and "how was the empire" out. A line with the bot in it
("how was your day", "how are you") is the manners question and stands down here.

Every reply says only what is true - the bot was not there and only has the person's words - and
gives the question back in the same words for any noun, so nothing is invented to fill the gap.
The medical ones are careful: a cheerful "how was it?" is the wrong tone for a scan, so those
say they hope it went as well as it could.

This is a last resort and it is written to be one: `bot/modules/greeting.py` asks it in the same
place as the other readers of a hedge, and the composer is asked first, so a line any entry, any
module or the composer can answer never reaches this file. Only a hedge is replaced.
"""
import re

from . import pick

# The things a "how was the ..." is about when the line says "the": the person's own life, in
# the words people type it. A head noun that is not here stands down, which is what keeps the
# history and the general-knowledge questions out ("how was the battle", "how was the empire").
THEIRS = frozenset("""
wedding funeral wake christening baptism party celebration anniversary birthday
scan appointment interview exam test operation surgery treatment chemo chemotherapy
radiotherapy biopsy results procedure checkup consultation diagnosis meeting
presentation review appraisal shift holiday honeymoon trip flight journey drive
move date match game concert gig show play film meal dinner lunch breakfast roast
takeaway restaurant hotel kids children child family mum mom dad mother father parent wife
husband partner son daughter sister brother baby toddler grandparents gran grandma
grandad nana dog cat puppy kitten pet rabbit hamster work job business shop team
house home flat garden
allotment course term lesson class school nursery weekend week day night morning
evening church ceremony service birth viewing rehearsal training practice football
rugby
""".split())

# Words that are not a thing that happened or is going on: "how was my fault" is not a question
# about anybody's week, and the shrug is a better answer to it than a friendly question.
NOT_AN_EVENT = frozenset(("fault", "idea", "point", "question", "turn", "problem", "favour"))

# A thing that has been through something difficult: "how was it?" with a bright edge is the
# wrong reply, so these get the pool that says it hopes it went as well as it could.
HEAVY = frozenset("""
funeral wake scan operation surgery treatment chemo chemotherapy radiotherapy biopsy
results procedure checkup diagnosis
""".split())

# The ask. The possessive is optional because "how was work" has none; the thing is read first
# and then checked against what kind of thing it is.
HOW = re.compile(
    r"^(?:(?:so|and|ok|okay|well|oh|but|right)[,\s]+)?"
    r"how(?:\s+(?:was|were|is|are|did|does)|'s|s)\s+"
    r"(?:(?P<whose>my|our|his|her|their|the)\s+)?"
    r"(?P<thing>[a-z][a-z' -]{0,30}?)"
    r"(?:\s+(?:go|went|going|doing|then|today|yesterday|tonight|last night|this week))*"
    r"\s*\??$", re.I)
# The same question said with the pronoun and the feeling: "was it scary", "was it hard", "was
# it rough". Nothing names the thing, so no reader in the composer has anything to go on and the
# line reaches the search hedge - and a search cannot say how their own morning went. The past
# tense is part of the shape ("is it scary" is about a film, not a day), the feeling has to be one
# of these words, and nothing else may be in the line, so "was it hard to park" (a how-to) and
# "was it good for families" (a question about a place) stand down.
FELT = re.compile(
    r"^(?:(?:so|and|ok|okay|well|oh|but|right)[,\s]+)?"
    r"(?:was|were)\s+(?:it|that|this)\s+"
    r"(?:(?:really|actually|very|too|that|so|pretty)\s+)?"
    r"(?P<word>bad|good|nice|hard|tough|rough|scary|easy|awful|ok|okay|alright|fine|fun|"
    r"horrible|dreadful|painful|tiring|stressful|busy|long|slow|worrying|grim|lovely|great|sunny|warm|cold|wet|windy|hot)"
    r"\s*(?:for\s+(?:you|her|him|them))?\s*[?!.]*$", re.I)

# The bot's own question, and the bot itself: the manners pools answer those, and this file must
# not take them ("how was your day" was the bot's day long before it was anybody's wedding).
THE_BOT = re.compile(r"(?<![a-z])(?:you|your|yours|yourself|u|ur)(?![a-z])", re.I)
# A question about a thing that has already happened is answered with the one question a friend
# asks, and the one thing the bot can honestly say: it only has the person's words.
PAST = (
    "You'll have to tell me - I only get what you type. How did it go?",
    "I wasn't there, so you're the one who knows. How did it go?",
    "Nothing of it reached me here, so tell me: how did it go?",
    "You tell me - how did it go? I only get what you type.",
)
# The same for a thing that is still going on ("how are the kids", "how is work"), where the
# answer is how they are, not how they went.
STILL_PLURAL = (
    "You'll have to tell me - I only get what you type. How are they doing?",
    "I'm not there for any of it, so you're the one who knows. How are they?",
    "Nothing of that reaches me here. So how are they?",
)
STILL_SINGLE = (
    "You'll have to tell me - I only get what you type. How is it going?",
    "I'm not there for any of it, so you're the one who knows. How is it going?",
    "Nothing of that reaches me here. So how is it going?",
)
# A thing that has been through something difficult: a bright "how did it go?" is the wrong
# tone, so these say they hope it went as well as it could.
CAREFUL = (
    "I only know what you tell me. I hope it went as well as it could - how are you doing now?",
    "Nothing of that reaches me, so I only have what you say. How did it go?",
    "I hope it went as well as it could. Tell me how you are doing with it.",
)
# More than one. Said as a list plus the words that really do end in "s", because the reverse -
# "it ends in s, so it is plural" - is one word away from "how is the business" -> "How are they?",
# and a business, a class and a shop are the commonest things a person asks about after work.
MORE_THAN_ONE = frozenset("""
children kids twins people parents grandparents mumanddad results tests scans appointments
""".split())
# A singular that ends in "s" anyway. Nothing else in THEIRS does today, so this fence is what
# keeps the rule honest when the next such word is added.
SINGULAR_ENDS_IN_S = frozenset("""
business class christmas maths news series gas address boss
""".split())


def a_kind_of_theirs(head):
    """Is the bare "the X" a kind of thing that sits in a person's own life?

    The plural of a word that is in THEIRS is the same kind of thing, so the list holds the word
    once ("the tests", "the appointments", "the scans" all read through "test", "appointment",
    "scan"). That is a rule rather than a second list, so a word added above comes with its
    plural already.
    """
    if head in THEIRS:
        return True
    for suffix in ("s", "es"):
        if head.endswith(suffix) and head[:-len(suffix)] in THEIRS:
            return True
    return False


def more_than_one(head):
    """Is the thing the person asks about more than one of something?"""
    if head in MORE_THAN_ONE:
        return True
    return head.endswith("s") and head not in SINGULAR_ENDS_IN_S


def _head(thing):
    """The last word is what the thing is: "school play" is a play, "first day" is a day."""
    return thing.split()[-1].strip("'") if thing.split() else ""


def answer_for(text, memory=None):
    line = " ".join((text or "").lower().split()).rstrip(" .!,;:")
    if not line or THE_BOT.search(line):
        return None
    match = HOW.match(line)
    if not match:
        felt = FELT.match(line)
        if felt:
            return pick(list(PAST), memory or {}, line)
        return None
    thing = (match.group("thing") or "").strip()
    whose = (match.group("whose") or "").lower()
    head = _head(thing)
    if not head or head in NOT_AN_EVENT:
        return None
    # "my exam", "their wedding": theirs whatever the noun is, because only the person has the
    # thing the possessive points at. A bare "the ..." has to be a kind of thing that belongs to
    # somebody's own life, or "how was the war" would be read as their war.
    if whose not in ("my", "our", "his", "her", "their") and not a_kind_of_theirs(head):
        return None
    if head in HEAVY:
        pool = CAREFUL
    elif re.match(r"^(?:(?:so|and|ok|okay|well|oh|but|right)[,\s]+)?"
                  r"how(?:'s|s| is| are)\b", line):
        pool = STILL_PLURAL if more_than_one(head) else STILL_SINGLE
    else:
        pool = PAST
    return pick(list(pool), memory or {}, line)

# --- the other half of the same exchange: the person's answer -------------------------------
#
# The question above asks how it went. The answer often comes back as a comparison rather than a
# fact: "better than i expected", "not as good as i hoped", "quiet, which is what we wanted". On
# main every one of those reached the composer's search hedge - "A quick search online will get
# you a solid answer" - which is the worst reply there is to somebody telling you how their
# interview went. A search cannot be told how a week went, and the person is not asking a
# question at all: they are answering the one the bot asked.
#
# The line has to be only the comparison. A comparison with a subject of its own is about that
# subject, and the module that knows the subject reads it: "my back is worse than yesterday" is
# a symptom (bot/compose/harm.py), not a verdict on a day. So the line must open on the
# comparison, on "it/that/this", or on "not", and nothing but the comparison may follow it.
LEAD = (r"(?:(?:oh|ah|well|actually|honestly|yeah|yep|no|ha|hmm|so|and|but|ok|okay|"
        r"thankfully|happily)[,\s]+)*")
COMPARE = (r"(?:better|worse|easier|harder|nicer|quicker|slower|cheaper|quieter|rougher|"
           r"smoother|calmer|lighter|heavier|longer|shorter|funnier|duller)")
SOFT = r"(?:much|far|a lot|loads|a bit|bit|slightly|definitely|way|even|so much)?\s*"
COPULA = r"(?:(?:it|that|this)(?:'s|s| is| was| went| turned out| feels)?\s+)?"
MINE = r"(?:i|we)"
HOPED = (r"(?:expected|thought|hoped|feared|imagined|dreaded|anticipated|planned|"
         r"was expecting|were expecting|was hoping|were hoping)")
THAN = (r"than\s+(?:" + MINE + r"\s+(?:" + HOPED + r")|last\s+time|yesterday|before|"
        r"the\s+last\s+one|the\s+other\s+one|the\s+first\s+(?:one|time)|the\s+usual|usual|"
        r"(?:the\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|weekend|"
        r"christmas|last\s+year|last\s+week|last\s+month))\b")
COMPARED = re.compile("^" + LEAD + COPULA + SOFT + r"(?P<word>" + COMPARE + r")\s*" + THAN,
                      re.I)
# "not as good as i hoped", "not as bad as i feared": the same comparison turned round.
NOT_AS = re.compile("^" + LEAD + COPULA + r"not\s+(?:as|so)\s+"
                    r"(?P<word>good|bad|nice|easy|hard|busy|expensive|cheap|scary|painful)\s+"
                    r"as\s+" + MINE + r"\s+(?:" + HOPED + r")", re.I)
# "as expected", "about what i expected": no surprise either way.
AS_EXPECTED = re.compile("^" + LEAD + r"(?:(?:about|roughly|pretty|more\s+or\s+less)\s+)?"
                         r"(?:as|what)\s+" + MINE + r"\s+expected\b", re.I)
EXPECTED_BARE = re.compile(
    "^" + LEAD + r"(?:(?:pretty|much|about|roughly|more\s+or\s+less)\s+|pretty\s+much\s+)*"
    r"as\s+expected\b", re.I)
# "quiet, which is what we wanted": they name what they got and say it was the aim. A bad thing
# said the same way is a complaint ("the boiler broke, which is what we feared"), so only the
# wanting words count and the thing named has to be a plain description.
WHICH_WAS_THE_AIM = re.compile(
    r"^(?P<what>[a-z][a-z' -]{1,24}?),?\s+which\s+(?:is|was)\s+(?:just\s+)?"
    r"what\s+" + MINE + r"\s+(?:wanted|needed|hoped\s+for|(?:was|were)\s+after)\b", re.I)
NOTHING_WENT_WRONG = re.compile(
    r"\b(?:broke|broken|failed|died|stopped|leaked|flooded|crashed|caught\s+fire|went\s+wrong|"
    r"lost|cancelled|ruined)\b", re.I)
# The words a comparison can open on. Anything else in front of "better" or "worse" is a subject,
# and a subject means the line is about that thing, not about how the day went.
STANDS_ALONE = frozenset("""
it that this not much far way so even still definitely bit slightly honestly actually
well oh ah yeah yep no about roughly pretty as what
""".split())
# The comparison word itself can open the line: "better than i expected" has no subject in front
# of it, which is what makes it a verdict on the last turn rather than a fact about a thing.
COMPARE_WORD = re.compile("^(?:" + COMPARE + ")$", re.I)
LEAD_STRIP = re.compile("^" + LEAD)

# A comparison is good news or bad news, and the reply has to be on the right side of it:
# "better than i feared" and "not as bad as i expected" are reliefs, where "sorry" is the wrong
# way round, and "worse than i hoped" is not the place for a cheer.
BETTER = (
    "Good - better than you expected is the best way round for it to go.",
    "That's a nice surprise. What made the difference?",
    "Pleased to hear it. What was better about it than you thought?",
)
WORSE = (
    "Sorry - that's a let-down when you had hoped for more.",
    "Ah, I'm sorry. What was off about it?",
    "That's a shame. Do you know what changed?",
)
RELIEF = (
    "That's a relief, then. What was it actually like?",
    "Good - the dread is usually worse than the thing itself.",
    "Pleased it was not the ordeal you had braced for.",
)
NO_SURPRISES = (
    "No surprises then. Is there anything you would do differently next time?",
    "Fair enough - it did what you expected of it.",
    "So it went the way you thought it would. Nothing to fix.",
)
WANTED_IT = (
    "Good - {0} is exactly what you were after.",
    "That's the good kind of {0}. Pleased it landed that way.",
    "{0} was the point of it, so that counts as a good one.",
)
# Words that carry the feeling on their own.
LOW = frozenset("worse harder rougher busier heavier longer slower duller".split())
# "not as bad as i hoped" is still a let-down; the rest of these are reliefs.
NOT_SO_BAD = frozenset("bad hard busy expensive scary painful".split())


def _opens_on_the_comparison(line):
    """True when nothing but the comparison is in front of it.

    "better than i expected" opens on the comparison; "my back is worse than yesterday" opens on
    a body part, and the reading below is not about bodies.
    """
    rest = LEAD_STRIP.sub("", line)
    first = rest.split()[0] if rest.split() else ""
    return first in STANDS_ALONE or bool(COMPARE_WORD.match(first))


def the_answer_they_gave(text, memory=None):
    """The reply to a person's verdict on how a thing of theirs went, or None.

    Only a line that is nothing but the comparison is read. A line with a subject, a question
    mark or the bot in it keeps whatever answer it already had.
    """
    line = " ".join((text or "").lower().split()).rstrip(" .!,;:")
    if not line or "?" in line or THE_BOT.search(line):
        return None
    if len(line.split()) > 9:
        return None
    aim = WHICH_WAS_THE_AIM.match(line)
    if aim:
        what = aim.group("what").strip()
        for lead in ("it was ", "it is ", "that was ", "this was "):
            if what.startswith(lead):
                what = what[len(lead):]
        if not what or NOTHING_WENT_WRONG.search(what) or len(what.split()) > 3:
            return None
        return pick([line.format(what) for line in WANTED_IT], memory or {}, line)
    if not _opens_on_the_comparison(line):
        return None
    match = COMPARED.search(line)
    not_as = NOT_AS.search(line)
    if match:
        pool = WORSE if match.group("word").lower() in LOW else BETTER
    elif not_as:
        pool = RELIEF if not_as.group("word").lower() in NOT_SO_BAD else WORSE
    elif AS_EXPECTED.search(line) or EXPECTED_BARE.search(line):
        pool = NO_SURPRISES
    else:
        return None
    return pick(list(pool), memory or {}, line)
