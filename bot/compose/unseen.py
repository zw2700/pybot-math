"""Being around people and not being seen by them.

"i feel like nobody cares", "nobody ever asks how i am", "i feel invisible at work" - the person
is not saying how they feel about a thing, a plan or a fact, so none of the modules that answer
those lines wants it, and what was left was the stock nod ("Got it. Is there anything you'd like
a hand with?", "I'm listening - say more if it helps"), which answers nothing at all to somebody
saying they are lonely in a room full of people.

One reading, one pool: what a friend says to that is that it is a lonely way to feel, and then
one question. No advice - a weekly club is not the answer to "nobody at home asks how i am" -
and never the line said back.

The shapes are the verb people use for the thing they are missing, with the person as its
object: nobody *listens to me*, no one *asks how i am*, nobody *is on my side*. A verb with a
thing after it is not this ("nobody cares about the bins", "nobody asked for a receipt"), which
is why the object is part of every shape rather than a word list alone.
"""
import re

# The verbs of being seen, heard, asked after and stood up for.
_SEEN = (r"(?:cares?|cared|listens?|listened|understands?|understood|notices?|noticed|"
         r"checks? (?:in|on me)|invites?|invited|includes?|included|sees? me|"
         r"wants? me|likes? me|loves? me|stands? up for me|is (?:there|around) for me|"
         r"are (?:there|around) for me|is on my side|are on my side|has time for me|"
         r"knows? (?:my name|me|i exist)|"
         r"have time for me|talks? to me|spoke to me|speaks to me|texts? me|rings? me|calls? me)")
# The same complaint with the person first: "i feel invisible", "i feel like a spare part".
_NOT_SEEN = (r"(?:invisible|unseen|unheard|overlooked|ignored|left out|an afterthought|"
             r"a spare part|like furniture|like a ghost|like a nobody|like i am not there|"
             r"like i'?m not there|like i do not exist|like i don'?t exist)")
# A line about somebody else's loneliness ("my mum says nobody cares about her") is not the
# speaker's own. It is turned away below rather than inside ME, because another person is often
# only the setting ("nobody in my family listens to me").
OTHER = re.compile(r"\b(?:he|she|they|him|her|them|his|their|my (?:mum|mom|mam|dad|boss|son|"
                   r"daughter|partner|husband|wife|friend|sister|brother|colleague|manager|"
                   r"neighbour|neighbor|carer))\b")
# The world, not the person: "nobody cares about the planet" is a view, not a loneliness.
NOT_ME = re.compile(r"\b(?:the (?:planet|climate|environment|government|club|team|company|"
                    r"shop|bins|bin|road|park|beach|library|bus|train)|them|it all|"
                    r"about (?:the|this|that)\s+(?:company|job|place|team|club))\b")
# A professional who owes them an answer is not the loneliness this pool is for: "i feel ignored
# by my doctor" is a complaint about being put off by a person whose job it is to reply, and the
# fallback's own "I'm sorry - that's frustrating" is closer than "where does it bite most".
PROFESSIONAL = re.compile(
    r"\b(?:doctor|gp|surgery|consultant|nurse|midwife|health visitor|dentist|optician|"
    r"teacher|head ?teacher|tutor|lecturer|social worker|council|landlord|letting agent|"
    r"housing officer|jobcentre|dwp|bank|insurer)\b")
# Lines this reading stands aside for, and why. A hypothetical about the person being gone
# ("nobody would notice if i left early") is not being overlooked, it is the line the safety
# modules answer, and "that is a lonely place to be" is the wrong reply to hand back. The deck
# has that line in the safety area, so the pool must not take it.
RISK = re.compile(
    r"\b(?:nobody|no ?one)\s+would\b"
    r"|\bif i (?:wasn'?t|was not|weren'?t|were not|am not|was |were )?(?:here|gone)\b"
    r"|\bif i died\b|\bbetter off (?:dead|without me)\b|\bkill myself\b"
    r"|\bend (?:it all|my life)\b|\bno reason to (?:live|go on)\b|\bnot be here any ?more\b")
# A denial of the state, not the state: "im not invisible", "im never ignored", "nobody does not
# care". The negator has to stand directly between the person and the state word, which is what
# makes "never" safe here: "im never ignored" and "im never overlooked" deny the state, while
# "im never noticed" and "im never invited" - the complaint, said as a frequency - have no state
# word after the "never" to deny, so they are still read. And the "no" of "no one" is its
# subject, not a denial.
DENIED = re.compile(
    r"\b(?:im|i['\u2019]?m|i\s+(?:feel|felt|am|get|end up))\s+(?:not|never|hardly|barely)\s+"
    r"(?:like\s+)?" + _NOT_SEEN + r"\b"
    r"|\b(?:nobody|no ?one|no-one|none of (?:my|them|the lot))\b(?:\s+\w+){0,3}\s+"
    r"(?:not|never|does?nt|do not|didnt|isnt|is not|wont|will not)\b")
# The verbs of being seen split in two. `_SEEN` above carries the shapes whose object is written
# in them ("listens to me", "texts me"), and four of them are the ones people say with nothing
# after them at all ("nobody cares", "nobody listens"), where the object left out is the person.
# Said with a thing after it they are not this reading - "nobody cares about my plants", "nobody
# listens to voicemails now", "nobody understands cricket" - so what follows the verb is read:
# the person, their feelings, their words, or nothing at all.
BARE_VERB = re.compile(
    r"\b(?:nobody|no ?one|no-one|not one person|none of (?:my|them|the lot))"
    r"(?:\s+\w+){0,4}\s+"
    r"(?:(?:cares?|cared|listens?|listened|understands?|understood|notices?|noticed)"
    r"|(?:checks?|checked) (?:in|up))\b"
    r"(?P<tail>[^.!?,]{0,40})")
# What may follow one of those verbs and still be the person: nothing, the person, or the person's
# own feelings and words. Anything else is a thing ("about my plants", "to voicemails now",
# "cricket", "the typo"), and the line is about that thing.
THE_PERSON = re.compile(
    r"^\s*(?:$"
    r"|(?:me|us)\b"
    r"|(?:in|up|on|with)\s+(?:me|us)\b"
    r"|(?:about|to|for|of|at|with)\s+(?:me|us)\b"
    r"|(?:about|to|for|of)\s+(?:how|what|whether|if|anything|nothing|whatever|any\s+of\s+it)"
    r"\s+(?:i|we)\b"
    r"|(?:how|whether|if)\s+(?:i|we)\b"
    r"|(?:in|up)\s+(?:on|with)\s+(?:me|us)\b"
    r"|(?:anymore|any ?more|at all|either|ever)\b"
    r"|(?:in|up)?\s*$)")
# "i felt ignored by the satnav": a machine that ignored them is not a person who did, and the
# people who could be the loneliness are the ones a line names as people.
IGNORED_BY = re.compile(
    r"\b(?:ignored|overlooked|left out|unseen|unheard|not noticed)\s+by\s+"
    r"(?:the|a|an|my|our|his|her|their)\s+(\w+)")
PEOPLE = frozenset((
    "mum", "mom", "mam", "mother", "dad", "father", "parents", "family", "friends", "friend",
    "mates", "mate", "people", "everyone", "everybody", "anyone", "anybody", "someone",
    "somebody", "colleagues", "colleague", "coworkers", "neighbours", "neighbors", "kids",
    "children", "son", "daughter", "partner", "husband", "wife", "boyfriend", "girlfriend",
    "brother", "sister", "siblings", "group", "others", "crowd", "team", "class", "work",
    "housemates", "flatmates", "school", "them", "him", "her",
))
ME = re.compile(
    # nobody cares / no one listens to me / nobody asks how i am / none of my friends text me
    r"\b(?:nobody|no ?one|no-one|not one person|none of (?:my|them|the lot))"
    r"(?:\s+\w+){0,4}\s+" + _SEEN + r"\b"
    r"|\b(?:nobody|no ?one|no-one)\s+(?:cares?|cared)\b(?=\s*(?:[.!?,]|$))"
    r"|\b(?:nobody|no ?one|no-one)(?:\s+\w+){0,2}\s+(?:asks?|asked|notices?|noticed)\s+"
    # "nobody asks me how i am" is the commonest way to say it: the person is in the middle.
    # The "how" has to be about them - "nobody asked how my sourdough turned out" is about the
    # loaf, and "that is a lonely place to be" answered it.
    r"(?:me\s+|us\s+)?(?:how|whether|if)\s+(?:i|we)\b"
    r"|\b(?:nobody|no ?one|no-one)(?:\s+\w+){0,4}\s+(?:asks?|asked)\s+(?:about|after)\s+me\b"
    # "nobody bothers with me" needs its object: a bare "nobody bothers" is a shrug about the
    # street, the club or the shop, not a line about being unseen.
    r"|\b(?:nobody|no ?one|no-one)(?:\s+\w+){0,4}\s+bothers?\s+(?:with|about)\s+me\b"
    # i feel invisible / i feel like a spare part / im ignored at work
    # "im invisible", "i'm overlooked at work": people write "im" far more than "i am", and
    # "im unheard" was read as an introduction ("Nice to meet you, Unheard").
    r"|\b(?:i\s+(?:feel|felt|am|get|end up)|im|i['\u2019]m)\b(?:\s+\w+){0,2}\s+(?:like\s+)?"
    + _NOT_SEEN + r"\b"
    r"|\b(?:feel|feels|felt|feeling)\s+(?:like\s+)?" + _NOT_SEEN + r"\b")
# The same loneliness with the people named instead of "nobody": "my friends dont like me",
# "my dad doesnt care about me", "the girls at work dont like me", "my friends never invite
# me". Every one of these was the grievance pool ("Annoying. Tell me how it has gone so far
# and we'll work out what to say", "What have you tried saying so far?") or the bare nod, and
# there is nothing to work out saying to your own father about not caring - it is the person
# being left out, which is what this reading is for. The subject is the people, the verb is
# one of being seen or wanted, and the object has to be the person themselves.
# A qualifier in front of the noun is the same person: "my best mate doesnt text me back" was
# not read while "my mates dont text me back" was, because the people list wanted `my` and
# `mate` side by side. The list is the qualifiers people actually put there, not any word -
# "my job mate" and "my old school friend" are not what this is for, and `(?:\w+\s+){0,1}`
# would have taken both.
NAMED_PEOPLE = (
    r"(?:my|our)\s+(?:best\s+|old\s+|oldest\s+|closest\s+|closer\s+|own\s+|new\s+|"
    r"eldest\s+|older\s+|younger\s+|little\s+|big\s+)?(?:friends?|mates?|family|mum|mom|"
    r"mam|mother|dad|father|parents|"
    r"sister|brother|siblings|husband|wife|partner|boyfriend|girlfriend|kids|children|"
    r"son|daughter|flatmates?|housemates?|colleagues?|coworkers?|workmates?|neighbours?|"
    r"neighbors?|relatives|cousins?|in-?laws)"
    r"|the\s+(?:girls|boys|lads|lasses|others|kids|team|group|people|family|mums|parents)"
    r"|everyone|everybody")
NAMED_REGARD = (
    r"(?:likes?|loves?|wants?|cares?(?:\s+about)?|notices?|needs?|listens?\s+to|"
    r"bothers?\s+with|invites?|includes?|misses?|respects?|trusts?|fancies|talks?\s+to|"
    r"texts?|rings?|calls?)")
# "my ex doesnt want me back" and "my husband doesnt fancy me any more" are the end of a
# relationship, not being left out of one, and the pools that answer those lines are better.
NAMED_OVER = re.compile(r"\b(?:want|love|need|miss|fancy)\s+me\s+(?:back|any\s?more)\b")
# "she doesnt want me to come" and "he doesnt like me to drive" are somebody's rules or plans,
# and the person is in them as the one being told rather than the one being left out. "she
# doesnt invite me to lunch" is the other way round, so only the telling verbs are turned away.
NAMED_TOLD = re.compile(r"\b(?:likes?|loves?|wants?|needs?|asks?)\s+(?:me|us)\s+to\s+\w+")
NAMED = re.compile(
    r"\b(?:{people})\b(?:\s+\w+){{0,2}}\s+"
    r"(?:dont|don'?t|doesnt|doesn'?t|didnt|didn'?t|never|wont|won'?t|do not|does not|"
    r"did not|will not)\s+(?:\w+\s+){{0,2}}{regard}\s+(?:me|us)\b".format(
        people=NAMED_PEOPLE, regard=NAMED_REGARD))
LINES = (
    "That is a lonely place to be, and being surrounded by people does not fix it. Who is one "
    "person who does see you?",
    "I hear you. Talking and getting nothing back wears a person down. How long has it felt "
    "like this?",
    "Not being noticed by the people near you is its own kind of hard. Where does it bite most "
    "- home, work, or with friends?",
    "That would get to anyone, and it is not about being easy to overlook. Is there one person "
    "you could say this to?",
)


def reads(clean):
    """True when the line is about not being seen by the people around them."""
    text = " ".join(str(clean or "").lower().split())
    if not text or RISK.search(text):
        return False
    named = (bool(NAMED.search(text)) and not NAMED_OVER.search(text)
             and not NAMED_TOLD.search(text))
    if not named and not ME.search(text):
        return False
    if DENIED.search(text):
        # "i'm not invisible", "im never ignored at home", "nobody does not care": a denial is
        # not the complaint, and "that is a lonely place to be" answers a line nobody said. The
        # negator has to sit between the person and the state - the "no" of "no one" is the
        # subject, not a denial - so the two shapes are spelled out.
        return False
    if named:
        # The people who are leaving them out are named, so `OTHER` - which is there to stop a
        # line about somebody else's loneliness ("my mum says nobody cares about her") - does
        # not apply, and neither does the bare-verb tail: the object is already the person.
        return not PROFESSIONAL.search(text)
    if NOT_ME.search(text) or OTHER.search(text) or PROFESSIONAL.search(text):
        return False
    bare = BARE_VERB.search(text)
    if bare and not THE_PERSON.match(bare.group("tail")):
        # "nobody cares about my plants" is about the plants, and "nobody listens to voicemails
        # now" is about the voicemails: the verb alone is not the complaint, the object says
        # whether the person is in the sentence.
        return False
    by = IGNORED_BY.search(text)
    if by and by.group(1) not in PEOPLE:
        # "i felt ignored by the satnav" is an ordinary line about a machine.
        return False
    return True
