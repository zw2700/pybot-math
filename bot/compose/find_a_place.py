"""Where to get a thing, or somebody to do a job, when the bot has no map and no branch list.

People ask this constantly - "where do i get seed from", "is there a launderette near me", "where
can i get my bike fixed", "is there a pharmacy open near me on sunday" - and every one of them
reached either the search hedge ("A quick search online will get you a solid answer") or, worse,
the composer's flat nod:

    where do i get seed from                    -> I'm not sure about that one... A quick search
    is there a launderette near me              -> I don't know enough to answer that honestly
    any decent chippy near me                   -> Thanks for telling me - I'm here if you want
                                                   to dig into any of that
    where do i get the part                     (after "its a mixer tap") -> I don't know enough

A search is not wrong here, but it is thin: it does not say *what* the bot cannot see, and it does
not name the one move that does work. What is true on this side is small and worth saying: there
is no map, no list of what is near them, no live opening times and no recommendations - and the
move that works is a map app with their own town in it, or two neighbours, and a phone call before
they go out of their way.

So this reader says the true part, names the move, and keeps it short. It is a fallback and it is
written to be one: it only replaces a hedge or the composer's nod (`NEUTRAL`, `A_SMALL_DAY`), and
any entry, any card, or the composer's own line keeps the turn.

Three kinds, because the answer is different for each:

    a thing to buy        - "where do i get seed from", "is there a launderette near me"
                            a map app with the thing and their town; the branch page for stock
    a person for a job    - "where can i get my bike fixed", "where do i find someone to service
                            it" - neighbours and a local group, then a trade body's register
                            (Gas Safe for gas) and the price in writing
    one with hours        - "is there a pharmacy open near me on sunday" - a map app's "open now",
                            and the NHS pharmacy finder for a pharmacy

What it never does is invent a shop, a name, a price or a time. It reads the thing out of the
person's own line ("a christmas tree", "seed", "dry cleaning") so the reply names what they asked
about instead of "it".
"""
import re

from . import fallback_data, finding_out, pick

# Where to get a thing. The asks people type, in their own words: "where can i get", "where do i
# buy", "where do i find someone", "wheres the best place for".
WHERE_TO_GET = re.compile(
    r"\bwhere (?:can|could|do|would|should|might) (?:i|we) (?:get|buy|find|hire|pick up|source)\b"
    r"|\bwhere(?:'s| is| are)? (?:the )?(?:best|nearest|closest)\b"
    r"|\bwhere (?:can|could) (?:i|we) (?:get|find) (?:somebody|someone)\b"
    r"|\bwho (?:does|sells|fixes|repairs|makes|can) (?:this|that|it|them)?\b")
# "is there a launderette near me", "any good pubs near york station", "anywhere round here that
# does dry cleaning". The near-word is what makes it a place ask, so it is required.
THERE_IS = re.compile(
    r"\b(?:is|are) there (?:a|an|any|anywhere|somewhere|any good|any decent|a good|a decent)\b"
    r"|\bany (?:good|decent|half decent|nice)\b"
    r"|\banywhere (?:i can|that|round here|near|to get|to buy)\b")
NEARBY = re.compile(
    r"\b(?:near me|near here|near us|nearby|round here|around here|round the corner|close by|"
    r"locally|in the area|in town|near york|near my|nearest)\b")
# A recommendation ask: "can you recommend a plumber", "do you know anyone who fixes bikes",
# "anyone know a good hairdresser round here". It is the same question as where-to-get-it with the
# politeness of a name in it, and the true answer is the same: nobody here can vouch for anybody.
A_RECOMMEND = re.compile(
    r"\b(?:can|could|would) (?:you|anybody|anyone) (?:recommend|suggest)\b"
    r"|\b(?:do|did) you know (?:a|an|any|anyone|anybody|someone|somebody|of a|of any)\b"
    r"|\bknow (?:a|an|any) (?:good|decent|reliable|half decent|trustworthy)\b"
    r"|\banyone know (?:a|an|any)\b"
    r"|\bwho (?:would|could) you (?:recommend|suggest)\b"
    r"|\b(?:recommend|recommendation|recommendations) (?:for|of) (?:a|an|someone|somebody)\b")
# Who the name would be for. A recommendation ask with none of these is a film, a book or a
# podcast - a card the knowledge already answers - so the reader stands down rather than offer a
# trade register for a box set.
# ...and a line that asks what the bot thinks they should do is not a request for a name:
# "would you recommend i see a physio" wants a yes or no, and the health cards have that.
A_ASKING_MY_OPINION = re.compile(
    r"\b(?:recommend|suggest) (?:i|we|me|that i|that we)\b"
    r"|\bwould you (?:recommend|suggest) (?:seeing|going|trying|taking|using|booking|getting)\b")
A_NAME_FOR_SOMEBODY = re.compile(
    r"\b(?:plumber|electrician|builder|joiner|carpenter|roofer|roofing|gardener|landscaper|"
    r"decorator|painter|mechanic|garage|locksmith|glazier|chimney sweep|pest control|removals|"
    r"handyman|odd job|surveyor|architect|cleaner|window cleaner|solicitor|lawyer|conveyancer|"
    r"accountant|bookkeeper|dentist|orthodontist|hygienist|hairdresser|barber|vet|optician|"
    r"physio|physiotherapist|osteopath|chiropractor|chiropodist|podiatrist|tutor|childminder|"
    r"dog walker|dog groomer|nanny|carer|interpreter|translator|tailor|seamstress|upholsterer|"
    r"tiler|plasterer|drainage|gas engineer|boiler engineer|heating engineer)\b")
# A place that has hours is a different question from one that doesn't: "is there a pharmacy open
# near me on sunday" is about today's times, not about who sells things.
HOURS = re.compile(
    r"\bopen\b|\bopening\b|\bclosed\b|\bshut\b|\blate\b|\bsunday\b|\bsaturday\b|\btonight\b|"
    r"\bnow\b|\btoday\b|\bbank holiday\b|\bweekend\b|24 hour|24-hour")
# A person to do a job: either the line says somebody, or it names a trade, or it says what is to
# be done to a thing of theirs ("get my bike fixed", "service the boiler").
SOMEBODY = re.compile(r"\b(?:someone|somebody|a man|a person|anyone|who can|who could)\b")
A_TRADE = re.compile(
    r"\b(?:plumber|electrician|builder|joiner|carpenter|roofer|roofing|gardener|landscaper|"
    r"decorator|painter|mechanic|garage|locksmith|glazier|chimney sweep|pest control|"
    r"removals|man with a van|gas engineer|boiler engineer|heating engineer|tiler|plasterer|"
    r"drainage|drain man|odd job|handyman|surveyor|architect|cleaner|window cleaner)\b")
A_JOB_ON_A_THING = re.compile(
    r"\b(?:fix|fixes|fixed|repair|repairs|repaired|mend|mends|mended|service|services|serviced|"
    r"install|installs|installed|fit|fits|fitted|replace|replaces|replaced|unblock|unblocks|"
    r"unblocked|bleed|bleeds|bleeding|rewire|plaster|tile|decorate|assemble|"
    r"put up|take down|cut back|trim|fell|haul|clear out|check over|mot|valet)\b")
# The thing, as the person said it, without the ask or the place around it.
A_LEAD = re.compile(r"^(?:a|an|the|some|any|my|our|his|her|their)\s+")
A_TAIL = re.compile(
    r"\s+(?:from|from a|near me|near here|nearby|round here|around here|round the corner|"
    r"close by|locally|in the area|in town|please|then|today|now|cheaply|cheap|asap|"
    r"at all|if possible)$")
# A part of a sentence that names no thing of its own: the read-back would be "the part near me",
# which is worse than saying nothing about it.
NO_THING = frozenset((
    "it", "its", "it's", "one", "ones", "them", "that", "this", "those", "these", "the part",
    "the bit", "the thing", "the other one", "the right one", "the same one", "a new one",
    "the rest", "some", "more", "the stuff", "stuff", "something", "anything", "part", "bit",
    "piece", "number", "spare", "the spare", "new one", "the new one", "a replacement",
))
# The words that make it a question about the bot, the screen, a form or a figure rather than
# about a place: "where do i find the setting", "where do i get the form", "where do i get the
# money". The composer has an answer for those, and a map app has none.
NOT_A_PLACE = re.compile(
    r"\b(?:setting|settings|option|menu|button|box|tick|toggle|app|website|web ?site|site|"
    r"internet|online|account|profile|password|page|link|file|folder|form|email|e-mail|"
    r"number|answer|word|phrase|name of|symbol|icon|tab|code|pin|receipt|invoice|statement|"
    r"advice|help|support|information|info|idea|ideas|inspiration|motivation|energy|time|"
    r"money|cash|courage|willpower|confidence|strength|protein|fibre|fiber|iron|calcium|"
    r"vitamin|vitamins|carbs|calories|fat|nutrient|nutrients|hydration|sleep|"
    r"results|result|prescription|referral|appointment|test|tests|tested|screening|screened|"
    r"vaccinated|jab|jabbed|vaccine|vaccination|voucher|gift card|"
    r"refund|compensation|complaint|report|permission|licence|license|visa|change|connection|"
    r"platform|route|directions|ticket|bus|buses|train|trains|tube|taxi|tram|coach|get off|"
    r"get on|get out|stop)\b")
# The same ask with the question dropped off the front: "any chemist in the area", "any petrol
# station near here", "any pharmacy open now". Every one of those reached the composer's nod or
# the listening line while its twin with "is there a" in front of it got a map line.
BARE_ANY = re.compile(r"^(?:any|anywhere|somewhere)\b")
# With the question missing, an abstract word reads like a thing: "any news in the area", "any
# problems round here", "any advice nearby". Those are not places, and a map app has nothing for
# them, so the bare-any shape stands down on them and the rest of the bot answers as before.
ANY_ABSTRACT = re.compile(
    r"\b(?:advice|help|news|luck|update|updates|chance|word|ideas?|points?|sign|signs|"
    r"problems?|trouble|issues?|questions?|objection|preference|reasons?|differences?|"
    r"changes?|time|space|room|evidence|proof|complaints?|feedback|progress|"
    r"better|worse|easier|harder|nicer|cheaper|different|new|same|"
    r"news|warning|warnings)\b")
# "cash machine", "cash point" and "atm" are places with a door, and the money arm of
# NOT_A_PLACE used to stand them down: "is there a cash machine near here" got the search hedge.
# The phrase is swapped for a token the money arm does not read, so the shop ask survives.
CASH_MACHINE = re.compile(
    r"\b(?:cash machine|cash point|cashpoint|cashline|cash dispenser|atm|hole in the wall)\b")
# A line that already says where they are going has its own plan, and does not need a map from me.
ALREADY_A_PLAN = re.compile(
    r"\b(?:i'll|i will|im going|i'm going|we're going|were going|the council already)\b")


# The composer's flat pools: the nod that files the line away and says nothing about it. Only a
# reply from one of these (or a hedge, which `bot/modules/greeting.py` tests) is replaced, so a
# card or the composer's own line keeps the turn.
A_NOD = frozenset(fallback_data.NEUTRAL + fallback_data.A_SMALL_DAY)


# A reply that already names the route - the profession's own finder, a register, the body that
# keeps the list - is the better answer, and this reader used to replace it because it is filed
# with the hedges: "can you recommend a good solicitor" got "two neighbours ... Gas Safe for
# anything gas", and "is there a good physio near me" was told the branch's own page would say
# whether they keep it. The route is what a fallback should be handing over to, not overwriting.
ALREADY_A_ROUTE = re.compile(
    r"\b(?:own finder|own register|official (?:finder|register|list)|profession'?s own|"
    r"professional body|trade body|lists? them by area|find a (?:solicitor|lawyer|vet|dentist|"
    r"physio|accountant|plumber|electrician)|taking new (?:people|patients|clients))\b",
    re.I)
# "do you know anyone who has had this" is a person asking for somebody's experience, not for
# somebody to hire: the hand pool answered it with a trade register and "I won't guess with
# somebody's livelihood", which is a reply to a question nobody asked.
A_HAD_IT = re.compile(r"\b(?:has|have|had|who'?s|whos|that'?s|whose)\s+(?:also\s+)?had\b")
# What somebody might be fetched to help with when no trade is named: "do you know anyone with a
# van". They are a job for a person, which is what separates them from "do you know anyone who has
# had this".
A_THING_TO_HELP_WITH = re.compile(
    r"\b(?:van|trailer|ladder|ladders|generator|marquee|tables? and chairs|chairs|"
    r"skip|pressure washer|trolley)\b")


# `bot/compose/finding_out.py` already answers the same asks - the shop that has the thing, the
# trade who quotes, the professional who takes new patients, the planner for a journey - and its
# lines are as good as or better than this reader's. It is filed with the hedges, so this reader
# used to replace them: "where do i get seed from" lost "A map app search for seed shows what's
# nearest, and ring before you set off" for a line saying the same thing in more words, and "can
# you recommend a good plumber" lost the trade pool's two quotes for a register this bot cannot
# check. A route is what a fallback hands over to, so its heads are read and the turn is left.
ROUTE_POOLS = tuple(getattr(finding_out, name) for name in
                    ("BUY_POOL", "TRADE_POOL", "PROFESSIONAL_POOL", "PLACE_ROUTE_POOL")
                    if hasattr(finding_out, name))
_ROUTE_HEADS = frozenset(line.split("{")[0].strip()[:34] for pool in ROUTE_POOLS
                         for line in pool)


def already_a_route(reply):
    """True when a reply already names the finder, the register or the body that keeps it.

    That covers `finding_out`'s own routes as well as the finder lines other readers add, because
    the point of this reader is to answer where nothing does, not to reword a route already given.
    """
    said = str(reply or "")
    if ALREADY_A_ROUTE.search(said):
        return True
    return any(head and said.startswith(head) for head in _ROUTE_HEADS)


def _clean(text):
    return " ".join(str(text or "").lower().replace("\u2019", "'").split()).strip(" ?.!,")


def _a_thing(thing):
    """The thing trimmed of the ask and the place around it, or None when it names nothing."""
    thing = str(thing or "").strip()
    while True:
        trimmed = A_TAIL.sub("", thing).strip()
        if trimmed == thing:
            break
        thing = trimmed
    if not thing or thing in NO_THING or len(thing.split()) > 4:
        return None
    return thing


def _the_thing(clean):
    """The thing the line asks for, in the person's own words, or None when it names none.

    Three read-backs, because people ask three ways: "where do i get a christmas tree", "is there
    a launderette near me", "anywhere round here that does dry cleaning". The thing is taken as
    they said it so the reply can hand them a search they can type.
    """
    # "anywhere round here that does dry cleaning": the thing is what the place does, not the
    # place-word in front of it.
    found = re.search(r"\b(?:that|which|who) (?:does|sells|fixes|repairs|makes|keeps|stocks)\s+"
                      r"([a-z][a-z' ]{1,28})$", clean)
    if found:
        return _a_thing(found.group(1))
    found = re.search(
        r"\b(?:get|buy|find|hire|pick up|source)\s+(?:hold of\s+)?(?:a|an|the|some|any|my|our)?\s*"
        r"([a-z][a-z' ]{1,28}?)(?:\s+(?:from|near|round|around|close|locally|in|please|then|"
        r"today|now|cheaply|cheap|asap)$|\s*$)", clean)
    if found:
        return _a_thing(A_LEAD.sub("", found.group(1).strip()))
    found = re.match(r"(?:any|some)\s+([a-z][a-z' ]{1,28}?)(?:\s+(?:near|round|around|open|"
                     r"in|that|to|please|today|now|locally)\b|$)", clean)
    if found:
        return _a_thing(A_LEAD.sub("", found.group(1).strip()))
    # "where is the nearest atm": the thing is what the near-word is about, and it used to be read
    # back as nothing, so the reply talked about "the name of the thing" instead of the atm.
    found = re.search(r"\b(?:nearest|closest)\s+([a-z][a-z' ]{1,28}?)(?:\s+(?:near|to|for|in|"
                      r"that|please|today|now|open)\b|$)", clean)
    if found:
        thing = _a_thing(A_LEAD.sub("", found.group(1).strip()))
        if thing and thing not in ("place", "one", "spot"):
            return thing
    found = re.search(r"\b(?:is|are) there (?:a|an|any|somewhere|anywhere|any good|a decent)"
                      r"\s+([a-z][a-z' ]{1,28}?)(?:\s+(?:near|round|around|close|open|"
                      r"locally|in|that|to)\b|$)", clean)
    if found:
        return _a_thing(A_LEAD.sub("", found.group(1).strip()))
    return None


# A thing to buy, said back to the person so the map search is one they can type.
NO_MAP = (
    "No map on this side, so I can't see what's near you. \"{thing} near me\" in a map app lists "
    "the closest with their hours, and the branch's own page says whether they keep it.",
    "I can't see what's near you, so a pick from me would be a guess. Put \"{thing}\" into "
    "a map app with your town in the search, then ring before you go if it's a bus ride away.",
    "There's no list of places here. A map app search for \"{thing}\" and your town shows "
    "the nearest ones and what time they shut, which is the part I can't tell you.",
)
# The same, for a line that names no thing of its own ("where do i get the part", after a tap).
NO_MAP_UNNAMED = (
    "No map on this side, so I can't point you at anywhere near you. A map app with the name of "
    "the thing and your town is the quickest way, and a phone call settles whether they keep it.",
    "I can't see what's near you, so any shop I named would be a guess. Search it in a map app "
    "with your town added, and ring first: that saves the trip if they haven't got it.",
)
# Somebody to do the job: the bot has no way to know who is near, still trading, or any good.
A_HAND = (
    "I can't recommend anyone - I've no way to see who's near you or how their work turns out. "
    "Two neighbours who've had the same job done is the best source for a name, then check it on "
    "the trade's register (Gas Safe for anything gas) before you book.",
    "Nobody I can name for that, and I won't guess with somebody's livelihood. Ask on a local "
    "group or two neighbours, check the name on the trade body's list, and get the price in "
    "writing before they start.",
)
# A place that is open now or on a day: the hours are the thing that changes, so they have to look.
THE_HOURS = (
    "No live opening times here. A map app will show today's hours for the ones near you, and for "
    "a pharmacy the NHS pharmacy finder lists which are open.",
    "I can't see what's open near you today. A map app with \"open now\" in the search is the "
    "quick way, and the branch's own page is the one that's kept right.",
)


def _a_person_for_the_job(clean):
    """True when the person is asking for somebody to do the work rather than a shop."""
    if SOMEBODY.search(clean) or A_TRADE.search(clean):
        return True
    return bool(A_JOB_ON_A_THING.search(clean) and re.search(r"\b(?:my|our|the)\b", clean))


def answer_for(text, memory):
    """A reply for a where-to-get-it ask, or None.

    Only a place ask reaches here: a shape ("where can i get", "is there a ... near me") and,
    for the yes/no shapes, a near-word. Everything the bot does know - a card, a name, the
    composer's own line - keeps its turn before this is asked.
    """
    clean = _clean(text)
    if not clean:
        return None
    words = clean.split()
    if len(words) < 3 or len(words) > 16:
        return None
    bare_any = bool(BARE_ANY.match(clean))
    for_the_place_test = CASH_MACHINE.sub("cash_machine", clean)
    if bare_any and not THERE_IS.search(clean) and ANY_ABSTRACT.search(for_the_place_test):
        return None
    if NOT_A_PLACE.search(for_the_place_test) or ALREADY_A_PLAN.search(clean):
        return None
    asking_where = bool(WHERE_TO_GET.search(clean))
    asking_if_there_is = bool((THERE_IS.search(clean) or bare_any) and NEARBY.search(clean))
    if bare_any and not asking_if_there_is:
        # "any chemist open now" names no place word but is the same question: open, near them.
        asking_if_there_is = bool(HOURS.search(clean))
    asking_for_a_name = (bool(A_RECOMMEND.search(clean))
                         and not A_ASKING_MY_OPINION.search(clean)
                         and not A_HAD_IT.search(clean)
                         and (bool(A_NAME_FOR_SOMEBODY.search(clean))
                              or bool(A_TRADE.search(clean))
                              or bool(A_THING_TO_HELP_WITH.search(clean))
                              or (bool(SOMEBODY.search(clean))
                                  and bool(A_JOB_ON_A_THING.search(clean)))))
    if not asking_where and not asking_if_there_is and not asking_for_a_name:
        return None
    if asking_for_a_name:
        return pick(list(A_HAND), memory, clean)
    who_does = re.search(r"\bwho (?:does|sells|fixes|repairs|makes)\b", clean) and NEARBY.search(clean)
    if asking_where and not who_does and not re.search(
            r"\b(?:get|buy|find|hire|pick up|source)\b", clean) and not NEARBY.search(clean):
        return None
    if HOURS.search(clean):
        return pick(list(THE_HOURS), memory, clean)
    if _a_person_for_the_job(clean):
        return pick(list(A_HAND), memory, clean)
    thing = _the_thing(clean)
    if thing:
        return pick(list(NO_MAP), memory, clean).format(thing=thing)
    return pick(list(NO_MAP_UNNAMED), memory, clean)
