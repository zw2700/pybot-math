"""Phrase tables for `safety.py`, kept in their own file.

`bot/modules/safety.py` was 56 KB over the world's 1 MiB per-file cap on main `64514606`, and
`open_pr` refuses every PR that touches a file over it - so the safety lane could not open a
change at all. These are the same tables, moved whole and imported back at the same point in
the same order, so the replies people get are identical. Nothing was deleted or rewritten.
"""

import re  # noqa: F401  - the tables below are compiled here and used through this name
from .safety_cards import PURSUIT_PLACE_HOME  # noqa: F401

__all__ = [
    "ABUSE",
    "ABUSER",
    "BY_NOT_A_THING",
    "ABUSE_DISCLOSURE",
    "ABUSE_DISCLOSURE_FINE",
    "ABUSE_FINE",
    "ABUSE_HEAD_INTO",
    "ABUSE_HIT_ME",
    "ABUSE_MEMORY",
    "ABUSE_NOW",
    "ABUSE_PURSUIT_HARD",
    "ABUSE_VERB",
    "ABUSE_VERBAL",
    "ABUSE_VERBAL_FINE",
    "ABUSE_VERBAL_LABEL",
    "ABUSE_VERBAL_MAD",
    "ABUSE_VERBAL_PERSON",
    "ABUSE_VERBAL_SUBJECT",
    "ABUSE_VERB_PART",
    "ASK_AFTER_ME",
    "BLOW_THINGS",
    "CHILD_AGGRESSOR",
    "CHILD_HIT_NOW",
    "CLOSE",
    "DYING_OTHER",
    "GAME_AFTER_ME",
    "GAME_PLAYED",
    "GAME_WORD_STOP",
    "GRIP_GAME",
    "GRIP_GAME_FENCE",
    "GRIP_NOT_AN_ASSAULT",
    "GRIP_NOT_AN_ASSAULT_STR",
    "HAS_ME_SUBJECT",
    "HIT_AS_A_CHILD",
    "HIT_BY_A_VEHICLE",
    "HIT_THING_NOT_PERSON",
    "I_DID_NOT_HIT",
    "I_HIT_SOMEONE",
    "MONEY_NAMED",
    "NOT_A_FEAR",
    "OTHERS",
    "PARTNER_CLOSE",
    "PEOPLE",
    "PERSON",
    "PLAY_FACE_REPLIES",
    "PURSUIT",
    "PURSUIT_FEAR",
    "PURSUIT_LOUD",
    "PURSUIT_OUTSIDE",
    "PURSUIT_PLACE_WORK",
    "PURSUIT_SUBJECT",
    "PURSUIT_SUBJECT_EX",
    "REMORSE_FOR_THE_ACT",
    "SELF_HARM_NEEDS_PERSON",
    "SELF_OWN_DYING",
    "SOFT_FACE_PUSH",
    "SOFT_FACE_STOP",
    "SOMEONE_HOLDS_THE_MONEY",
    "THREAT_COERCIVE",
    "THREAT_SUBJECT",
    "_NOT_A_THREAT",
    "_REFUSED_EXIT",
    "_THE_BLOW",
    "_THE_HAND",
    "_THE_ONE_HIT",
    "_both_here",
]

MONEY_NAMED = re.compile(
    r"\b(?:pay\s?day|paid|pay|wages?|salary|pension|benefits?|universal\s+credit|money|cash|"
    r"quid|pounds?|dollars?|euros?|fiver|tenner|skint|paycheck|overdraft|rent|bills?|"
    r"\d+\s*(?:pounds?|quid|dollars?|euros?|bucks?))\b")
# Where another person took, emptied, hid or holds the money, a short week is not the question:
# "my partner took the money and i have nothing left" sent back "Pay in by what each of you earns,
# not by halves", which takes the side of whoever took it (@noble-walrus). The money stand-down
# does not apply to those lines, so the card stays while the money answer is still built for the
# short week it belongs to. An abuse answer of its own is a separate change.
SOMEONE_HOLDS_THE_MONEY = re.compile(
    r"\b(?:he|she|they|him|her|them|someone|somebody|my\s+(?:partner|husband|wife|boyfriend|"
    r"girlfriend|ex|mum|mom|dad|father|mother|son|daughter|brother|sister|flatmate|roommate|"
    r"housemate|landlord))\b[^.?!]{0,40}?\b(?:took|takes|taking|emptied|empties|cleared\s+out|"
    r"clears\s+out|controls?|controlled|keeps?|kept|hides?|hid|hidden|spends?|spent|gambled|"
    r"stole|steals?)\b[^.?!]{0,30}\b(?:money|wages?|salary|pay|paycheck|account|benefits?|"
    r"universal\s+credit|pension|savings?|card)\b",
    re.I)
SELF_HARM_NEEDS_PERSON = True
# "my nan is going to die" and "my wife is going to die" are grief said in advance. The crisis line
# belongs to the speaker's own wish to die, so the dying person has to be someone else for the loss
# answer to have it, and SELF_OWN_DYING is what says the line is about the speaker.
DYING_OTHER = (
    r"\b(?:my|our|his|her|their|the)\s+(?:nan|gran|nanny|nana|granny|grandma|grandmother|grandad|"
    r"granddad|grandpa|grandfather|mum|mom|mother|dad|father|wife|husband|partner|son|daughter|"
    r"child|kid|baby|brother|sister|aunt|uncle|cousin|friend|mate|dog|cat|puppy|kitten|pet|horse)\b"
    r"[^.?!]{0,20}\b(?:is|are|'s|s)\s+(?:going\s+to|gonna|about\s+to)\s+die\b",
)
SELF_OWN_DYING = (
    r"\b(?:im|i'm|i\s+am|i\s+think\s+im|i\s+think\s+i'm|i\s+feel|i\s+keep\s+thinking)\b"
    r"[^.?!]{0,20}\b(?:going\s+to|gonna|want\s+to|wanna|ready\s+to)\s+die\b",
    r"\bwant\s+to\s+die\b", r"\bkill\s+my\s*self\b", r"\bbetter\s+off\s+dead\b",
    r"\bsuicid\w*\b",
)

# The people a line can name. The carers are the ones people live with as much as their family, and
# they were in none of the lists: "my support worker has collapsed", "the care worker is on the
# floor and not responding", "my personal assistant collapsed" all got small talk. The
# grandchildren are the same hole at the other end of the family: "my grandson collapsed" got
# nothing, while "my granddaughter is unresponsive" only reached a card because "unresponsive" is a
# word of its own.
PERSON = (r"(?:mum|mom|mother|dad|father|son|daughter|husband|wife|partner|boyfriend|girlfriend|"
          # Plural as well as singular: "my grandsons collapsed" and "my doctors are" are the same
          # line said about more than one person, and the list is followed by \b in most patterns, so
          # a bare "grandson" missed the plural whole (lilac-apple, #12389).
          r"brother|sister|friend|flatmate|roommate|baby|child|kid|kids|children|"
          r"grand(?:child|children|son|daughter|kid)s?|step(?:child|children|son|daughter)s?|"
          r"boy|girl|man|woman|"
          r"lady|guy|bloke|neighbou?r|colleague|boss|gran|granny|nan|grandad|grandma|grandpa|mate|"
          r"carers?|care\s+workers?|support\s+workers?|social\s+workers?|personal\s+assistants?|"
          r"nurses?|midwives?|midwife|doctors?|gps?|physios?|therapists?|"
          r"patient|pupil|student|teacher|driver|passenger|singer|player|runner|swimmer)")

PEOPLE = (r"(?:i|i'm|i've|he|he's|she|she's|they|they're|we|you|someone|somebody|anyone|everyone|"
          r"my\s+" + PERSON + r"|the\s+" + PERSON + r"|" + PERSON + r")")

OTHERS = (r"(?:he|he's|she|she's|they|they're|him|her|them|someone|somebody|anyone|everyone|"
          r"my\s+" + PERSON + r"|his\s+" + PERSON + r"|her\s+" + PERSON + r"|their\s+" + PERSON + r"|"
          + PERSON + r")")

# A person the user can name: family, the people they live with, and the ones with power over
# them. "my sister hit me" and "my landlord pushed me" got nothing at all, because the abuse list
# only knew the partner-and-parent words.
ABUSER = (r"(?:" + PERSON + r"|step(?:mum|mom|dad|mother|father|brother|sister|son|daughter|parent|"
          r"child|children)|ex|landlord|landlady|housemate|lodger|aunt|auntie|uncle|cousin|nan|nana|"
          r"grandparent|in-?laws?|father-?in-?law|mother-?in-?law|son-?in-?law|daughter-?in-?law|"
          r"guardian|foster\s+parent|boy|friend|manager|supervisor|"
          # A niece, a nephew and a grandmother are people you can be hurt by, and the list held
          # only the family a household is made of. Since the strangle arm was fenced to a named
          # person (merged), "im strangling my niece" was answered "Noted: you're strangling your
          # niece." - a person being strangled, with the person not on the list.
          r"nieces?|nephews?|grandmothers?|grandfathers?|grandparents?)")
# The person saying *they* did it, in the first person: "i hit my wife last night", "i lost my
# temper and hit my son", "i grabbed her by the throat". Every arm in this file is written for the
# person it is done *to*, so these were answered with the row-repair script or "I'm listening" -
# the two answers somebody admitting to it must not get, with the person they hit in the house
# tonight. The `(?!'s)` is what keeps a car and a birthday cake out of it: "i hit my wife's car".
_THE_ONE_HIT = (r"(?:my\s+(?:partner|husband|wife|boyfriend|girlfriend|ex|fianc(?:e|ée)|mum|mom|"
                r"mother|dad|father|son|daughter|child|kid|kids|children|baby|stepson|stepdaughter|"
                r"stepdad|stepmum|brother|sister|nan|gran|grandma|grandad|carer)(?!'s)|"
                r"(?:my|the)\s+(?:kids|children|child|baby|son|daughter)s?(?!'s)|her|him|them)\b")
# The verbs with no other meaning in a family. A push, a shove or a grab is left out: those are
# how a family hurries itself out of the house ("i pushed my daughter to practise"), so they take
# the second arm, which wants the throat, the wall or the row.
_THE_BLOW = (r"(?:hit|hitting|slap(?:ped|ping)?|punch(?:ed|ing)?|kick(?:ed|ing)?|beat|beating|"
             r"chok(?:ed|ing)?|strangl(?:ed|ing)?|drag(?:ged|ging)?|threw|thrown|throwing|"
             r"scratch(?:ed|ing)|claw(?:ed|ing))")
_THE_HAND = (r"(?:push(?:ed|ing)?|shov(?:e|ed|es|ing)|grab(?:bed|bing)?|pin(?:ned|ning)?|held|"
             r"hold|pulled|yank(?:ed|ing)?|twist(?:ed|ing)?)")
I_HIT_SOMEONE = (
    r"\bi\s+(?:keep\s+|kept\s+|just\s+|nearly\s+|almost\s+|have\s+|had\s+)?" + _THE_BLOW +
    r"\s+" + _THE_ONE_HIT,
    r"\bi\s+(?:keep\s+|kept\s+)?" + _THE_HAND + r"\s+" + _THE_ONE_HIT +
    r"(?:[^.?!]{0,30}\b(?:throat|neck|wall|floor|stairs|ground|door|hard|down|against|"
    r"into\s+the\s+(?:road|traffic|kitchen|hall|bathroom|fire|car|bushes))\b"
    r"|[^.?!]{0,40}\b(?:during|in|after|before)\s+(?:an?\s+)?(?:argument|row|fight|"
    r"disagreement|falling\s+out)\b)",
    # The mood in front of it, which is how a lot of people write it down: "i lost my temper and
    # hit my son", "i was drunk and i hit my wife". The state is the reason they give, not a
    # different event, so it is the link rather than a way out.
    r"\b(?:i\s+)?(?:lost|lose|be\s+losing)\s+my\s+temper\b[^.?!]{0,30}\b" + _THE_BLOW +
    r"\s+" + _THE_ONE_HIT,
    r"\bi\s+(?:was\s+|got\s+|get\s+|am\s+|'m\s+|im\s+)?(?:so\s+)?(?:angry|mad|raging|"
    r"drunk|pissed|upset|frustrated|stressed|exhausted|wound\s+up|beside\s+myself)\b"
    r"[^.?!]{0,25}\b" + _THE_BLOW + r"\s+" + _THE_ONE_HIT,
)
# The typo repair folds "wife's" into "wife", so a possessive cannot be read off the repaired
# line: "i hit my wife's car" came through as "i hit my wife car" and the reply accused a man of
# hitting his wife over a dent. The line as typed is where the apostrophe still is.
HIT_THING_NOT_PERSON = (
    r"\b(?:partner|husband|wife|boyfriend|girlfriend|ex|fiance|fiancee|son|daughter|child|kid|"
    r"kids|children|baby|mum|mom|mother|dad|father|brother|sister|nan|gran|grandma|grandad|"
    r"carer|parents)'s\b",
    # ...and the same thing with the apostrophe left out, which is how it is often typed: "i hit my
    # sons birthday cake". A thing after the person is a thing, not a blow.
    r"\b(?:partner|husband|wife|boyfriend|girlfriend|ex|son|daughter|child|kid|kids|children|"
    r"baby|mum|mom|mother|dad|father|brother|sister|carer)(?:s)?\s+(?:\w+\s+){0,2}(?:cake|car|bike|toys?|ball|"
    r"phone|laptop|window|door|plate|glass|cup|mug|tv|telly|scooter|bike|present|cards?|"
    r"homework|drawing|picture)\b",
)
# A blow that is not a blow: a denial ("i never hit my wife", "i wouldnt hit her"), a game or a
# sport ("we were messing about", "sparring", "play fighting", "boxing"), a fight between children,
# and the defence ("i hit him back") - all of those must stay out of it, or the reply accuses
# someone of hitting their family when they said the opposite.
# A blow that was a game. The person is the object of a hit or a beating in a match, a board game
# or a playfight, and reading it as violence is the card accusing a family of a night the house
# never saw: "i beat my partner at chess", "i hit my wife in the tennis final" (peach-hammer,
# #5014), "my dad used to beat me at chess". One table, because three readers need the same list:
# the line that says who it hit, and the two arms of HIT_AS_A_CHILD below.
GAME_NOT_A_BLOW = (
    r"\b(?:mess(?:ing)?\s+about|mucking\s+about|play(?:ing)?\s*(?:fighting|fight)|sparring|"
    r"boxing|wrestl(?:ing|e)|judo|karate|rugby|football|practice|training|drill|"
    r"a\s+game|snowball|water\s+fight|paintball|nerf|tickl(?:e|ing)|play)\b",
    r"\b(?:at|in|during|on)\s+(?:the\s+)?(?:chess|cards?|scrabble|monopoly|backgammon|draughts|"
    r"checkers|dominoes|poker|darts|snooker|billiards|pool|bowling|tennis|badminton|squash|"
    r"golf|cricket|football|rugby|rounders|netball|basketball|hockey|table\s+tennis|"
    r"video\s+games?|playstation|xbox|wii|board\s+game)\b",
    r"\b(?:in|at|during)\s+(?:[\w-]+\s+)?(?:final|match|game|tournament|league|race|marathon|"
    r"competition|championship|quiz)\b(?!\s+(?:argument|row|fight|bust-?up|falling\s+out))",
)
I_DID_NOT_HIT = (
    r"\b(?:never|didn'?t|didnt|don'?t|dont|wouldn'?t|wouldnt|not|have\s+never)\s+"
    r"(?:ever\s+)?(?:hit|hitting|hurt|hurting|touch|touched|lay\s+a\s+hand|laid\s+a\s+hand)\b",
    r"\bhit\s+(?:her|him|them|my\s+" + ABUSER + r")\s+back\b",
    r"\b(?:lose|losing|lost)\s+my\s+temper\s+(?:with|at)\s+(?:her|him|them|the\s+kids|"
    r"my\s+" + ABUSER + r")\b[^.?!]{0,30}\b(?:shout|shouted|shouting|yell|yelled|swore|swear|"
    r"snapped|said|slam|slammed|walked|rowing|row|argue|argued|arguing)\b",
    r"\bwhen\s+we\s+were\s+(?:kids|children|little|lads|girls|boys)\b",
    r"\bwe\s+used\s+to\s+(?:fight|hit|scrap|wrestle)\b",
    # ...and the same said from one side of it. "i hit my brother when i was a kid" was the
    # Respect card for people who are violent at home, which is a programme for tonight's
    # household, not for a scrap at ten (purple-camel, #5014). The time in the line is the fence;
    # the same line with no time in it keeps the card.
    r"\bwhen\s+i\s+was\s+(?:\d+|a\s+kid|a\s+child|a\s+lad|a\s+boy|a\s+girl|young|"
    r"little|small|tiny|at\s+school|in\s+school)\b",
    r"\b(?:as|like)\s+(?:a\s+)?(?:kid|child|kids|children|lads|boys|girls)\b",
    r"\bgrowing\s+up\b",
    r"\b(?:at|in)\s+(?:primary|secondary|junior|middle|comprehensive)\s+school\b",
    r"\bi\s+used\s+to\s+(?:\w+\s+){0,3}(?:hit|fight|scrap|wrestle)\b[^.?!]{0,25}"
    r"\b(?:brother|sister|cousin|mate|friend|kids|kids|boy|girl)s?\b",
    r"\b(?:accident|accidentally|by\s+mistake|didn'?t\s+mean|didnt\s+mean|"
    r"in\s+my\s+sleep|sleepwalking|fidgeting)\b",
    # A kick to wake somebody up is the morning, not the bedroom door: "i kicked my partner awake
    # this morning".
    r"\b(?:awake|out\s+of\s+bed|to\s+wake\s+(?:me|him|her|them|the\s+kids))\b",
    # A dream names itself, so it is not a night in the house. The scene words only: "i hit my
    # wife and now i keep dreaming about it" is a disclosure, not a dream.
    r"\b(?:in\s+a\s+dream|dream(?:t|ed)\b|had\s+a\s+dream|nightmare)\b",
) + GAME_NOT_A_BLOW
# A grown-up telling you what was done to them as a child. "my dad hit me when i was a kid" is not
# a discipline question and it is not a live emergency either: the blow is years old, and what is
# left of it is an injury that a GP can refer on. The time words are what make it that, and they
# are also what made it a shrug or a toddler-advice answer.
# The grown-ups of a childhood, named as the person who did it: "my dad", "my mum", "my parents".
# One list, read by both arms of HIT_AS_A_CHILD below, because the second arm was written with a
# copy of it and a word added to one copy is a hole in the other.
MY_GROWN_UP = (r"(?:dad|father|stepdad|mum|mom|mother|stepmum|parents|uncle|aunt|auntie|brother|"
               r"sister|cousin|carer|nan|nana|gran|grandma|grandad|grandpa|grandparents|"
               r"foster\s+\w+)")
# The verbs a blow is done to a child with, in one place because both arms of HIT_AS_A_CHILD below
# read it: an arm written with its own copy of the list is a hole in the others, which is how "my
# stepdad used to belt me" got the cheer for a day that went well.
THE_BLOW_ON_A_CHILD = (
    _THE_BLOW + r"|beat|belt(?:ed)?|strap(?:ped)?|cane(?:d)?|smack(?:s|ed|ing)?|lock(?:ed)?|"
    r"starve(?:d)?|smother(?:ed)?|throttle(?:d)?|abuse(?:d|s)?|molest(?:ed|s)?|touch(?:ed|es)?"
)
# A missile is a blow, and a ball is not: the verb counts when what it moves is aimed at the person
# ("throw things at me", "threw a plate at me") or is the surface they land on ("threw me against
# the wall"). "my dad used to throw me a ball" is the ball going the other way and stays out.
THROWN_AT_ME = (
    r"(?:(?:throw|threw|thrown|throwing|hurl(?:ed|ing)?|chuck(?:ed|ing)?)[^.?!]{0,20}"
    r"\bat\s+(?:me|us)\b"
    r"|(?:threw|thrown|throwing|throw|hurled)[^.?!]{0,15}\b(?:against|into|down)\s+(?:the\s+)?"
    r"(?:wall|door|floor|stairs|ground)\b)"
)


HIT_AS_A_CHILD = (
    r"\bmy\s+" + MY_GROWN_UP + r"\b"
    r"[^.?!]{0,40}\b(?:" + _THE_BLOW + r"|burn(?:ed|t)|scalded|"
    r"whipped|belt(?:ed)?|strap(?:ped)?|cane(?:d)?|smack(?:s|ed|ing)?|abused|molested|touched\s+me|"
    r"locked\s+me|starved|smothered|throttled)\b"
    r"[^.?!]{0,40}"
    r"\b(?:when\s+i\s+was\s+(?:a\s+)?(?:kid|child|little|young|small|teenager|teen|"
    r"at\s+school|in\s+school|\d{1,2})|as\s+a\s+(?:kid|child|little\s+\w+|teenager)|"
    r"growing\s+up|back\s+then|years\s+ago|decades\s+ago|my\s+whole\s+childhood|"
    r"all\s+my\s+childhood|(?:used|would)\s+to\s+\w+\s+me)\b",
    r"\bi\s+(?:was|got)\s+(?:hit|beaten|abused|molested|whipped|slapped|kicked|punched)\s+"
    r"(?:as\s+a\s+(?:kid|child|little\s+\w+|teenager)|when\s+i\s+was\s+(?:a\s+)?"
    r"(?:kid|child|little|young|small|teenager|at\s+school)|growing\s+up|my\s+whole\s+"
    r"childhood)\b",
    # The same disclosure written as the habit it was, with the time in "used to" or "would" rather
    # than in a "when i was a kid": "my parents used to beat me", "my mum used to lock me in the
    # shed", "my dad would hit me when he drank". Without this arm the first got the cheer for a
    # day that went well ("Good to hear. What was the best bit?"), the second a shrug, and the
    # third the card for a blow happening now. The blow is the grown-up's and the object is the
    # person writing, and the verbs are the ones with no other meaning in a family (_THE_BLOW) -
    # "my dad used to push me on the swings" is the swings.
    r"\bmy\s+" + MY_GROWN_UP + r"\b[^.?!]{0,25}\b(?:used\s+to|would)\s+[^.?!]{0,20}\b(?:"
    + THE_BLOW_ON_A_CHILD + r")\b[^.?!]{0,15}\b(?:me|us)\b",
    # ...and when the thing that hit was thrown: "my dad used to throw things at me", "he would
    # throw the remote at me". The missile arm is separate because the object is the point: what a
    # grown-up throws at you is a blow, and what he throws you is a ball.
    r"\bmy\s+" + MY_GROWN_UP + r"\b[^.?!]{0,25}\b(?:used\s+to|would)\s+[^.?!]{0,20}"
    + THROWN_AT_ME,
    # The same again with the household in the place of the person: "i used to get beaten at home",
    # "i was hit at home as a kid". This is the shape that got the cheer for a day that went well
    # ("How was it, overall?"), because nothing in it names a person for the arms above to hold.
    r"\bi\s+(?:used|would)\s+to\s+(?:get|be)\s+(?:hit|beaten|beat|slapped|punched|kicked|"
    r"whipped|belted|abused|smacked)\b[^.?!]{0,25}\b(?:at\s+home|by\s+my\s+" + MY_GROWN_UP +
    r"|as\s+a\s+(?:kid|child)|when\s+i\s+was)\b",
)
# The childhood line is still going on when it says so, and then it is the present case, not the
# old one: "my dad hits me when i was a kid" is a typo, but "my dad hits me and i am 30" is a
# disclosure of now, and it must not be sent to the GP-referral reply.
CHILD_HIT_NOW = (
    r"\b(?:still|now|again|these\s+days|nowadays|every\s+(?:day|night|week|time))\s+"
    r"(?:\w+\s+){0,2}(?:hits?|beats?|does|doing|comes?|turns?\s+up)\b",
)
# The remorse that comes straight after the act, said in the first person about themselves: "i hit
# my wife once and i hate myself". The words are the reason the person is writing, not a different
# event, so the line is still the act and the answer is still what to do tonight. Kept tight on
# purpose: every arm is a self-directed revulsion, and none of them can be read as a wish to die.
REMORSE_FOR_THE_ACT = (
    r"\b(?:hate|hating|disgusted\s+(?:with|by)|ashamed\s+of|sickened\s+by|disappointed\s+in|"
    r"furious\s+(?:with|at)|angry\s+at)\s+my\s*self\b",
    r"\bi\s*(?:'?m|am|feel|felt)\s+(?:like\s+)?(?:such\s+)?(?:an?\s+)?(?:monster|beast|"
    r"awful\s+person|terrible\s+person|horrible\s+person|bad\s+person)\b",
    r"\bwhat\s+have\s+i\s+done\b",
    r"\bcan'?t\s+believe\s+i\s+(?:did|done)\s+(?:that|it)\b",
)
# The verbs people use for it, including the ones that never made the list: a shoved shoulder, a
# hand round the wrist, a plate thrown across the room.
ABUSE_VERB = (r"(?:hits?|hitting|beat(?:s|ing)?|punch(?:es|ed|ing)?|kick(?:s|ed|ing)?|chok(?:es|ed|ing)|"
              r"slapp?(?:s|ed|ing)?|grab(?:s|bed|bing)?|drag(?:s|ged|ging)?|burn(?:s|ed|ing)?|"
              r"strangl(?:e|es|ed|ing)|push(?:es|ed|ing)?|shov(?:e|es|ed|ing)|"
              r"bit\b|bite|bites|biting|spat\s+at|spit\s+at|throw(?:s|ing)?|threw|hurl(?:s|ed|ing)?|"
              r"yank(?:s|ed|ing)?|twist(?:s|ed|ing)?|wrench(?:es|ed|ing)?|swung\s+at|swing\s+at|"
              r"attack(?:s|ed|ing)?|savaged|mauled|lash(?:es|ed|ing)?\s+out\s+at|"
              r"lunged\s+at|held\s+me\s+down|pinned\s+me|scratch(?:es|ed|ing)?|"
              r"claw(?:s|ed|ing)?)")
# A threat *with* something is this case when the something can hurt; a threat about a written
# warning, a fine, an eviction or a letter is a bad job, a tenancy or a bill, and the abuse reply
# names a person who is not doing anything violent ("my boss is threatening me with a written
# warning", "my landlord is threatening me with eviction" both got the abuse card). Only the
# object decides it, and "about" is never a weapon, so it always stands the case down.
# "a man hit me with his car" is an accident, not a partner: the relative-clause arm reads the
# verb and the person, and a vehicle after it says the car did the hitting. A car, a van, a bike, a
# bus and a door are the things that hit people in that sentence; a fist, a belt, a shoe, a bottle
# and a plate are left in, because those are the same sentence as abuse.
HIT_BY_A_VEHICLE = (r"(?!\s+(?:with|by)\s+(?:a\s+|an\s+|the\s+|his\s+|her\s+|their\s+|"
                    r"our\s+|my\s+)?(?:car|cars|van|bike|bikes|bicycle|motorbike|motorcycle|"
                    r"scooter|lorry|truck|bus|train|tram|taxi|car\s+door|door|doors|vehicle|"
                    r"wheelchair|buggy|pram|cart|trolley|skateboard|scooter)\b)")
_NOT_A_THREAT = (r"(?!\s+(?:with|over|about)\s+(?:a\s+|the\s+|his\s+|her\s+|their\s+|"
                 r"my\s+|our\s+)?(?:written|warning|fine|fines|eviction|legal|lawsuit|court|"
                 r"police|report|complaint|solicitor|letter|bill|bill?s|charge|charges|"
                 r"prosecution|dismissal|sack|sacking|redundancy|redundant|fired|disciplinary|"
                 r"hearing|notice|tenancy|deposit)\b)")

# The passive voice says who did it with "by", and that is the one word that can make the sentence
# ordinary: "i am being followed by my ex" is the case, and "i am being followed by bad luck", "by
# a cold", "by my shadow", "by google maps", "by a black cat" have nothing to fear in them. A list
# of harmless things cannot cover them all - a toddler, a satnav and a shadow were each a false
# card - so the guard asks for a person rather than reading off a list of things that are not one.
# "i was strangled by the seatbelt" is a thing, and it is not a hand at a throat.
BY_NOT_A_THING = (
    r"(?!\s+by\s+(?!(?:(?:him|her|them|his|their|someone|somebody|some\s+men|men|guys|blokes|"
    r"lads|youths|people|strangers)\b|(?:a|an|the|two|three|four|five|several|some|another|"
    r"that|this|one)\s+(?:\w+\s+){0,2}(?:men|women|man|bloke|blokes|stranger|strangers|guy|guys|"
    r"woman|lady|ladies|person|people|group|youth|youths|teenager|teenagers|teen|teens|kid|kids|"
    r"boy|boys|girl|girls|fella|fellas|lad|lads|neighbour|neighbours|driver|carer|partner|"
    r"husband|wife|boyfriend|girlfriend|ex|dad|mum|father|mother|stepdad|stepmum|brother|"
    r"sister|uncle|aunt|cousin|son|daughter|landlord|landlady|housemate|colleague|boss|"
    r"manager)\b)"
    r"|my\s+" + ABUSER + r"\b))")

# The people who threaten someone they live with or are close to. A threat from one of them is
# the abuse case whatever the object, because "i will call the police" and "i will get a solicitor"
# are how coercive control is said: the authority is not the weapon, the person holding it over you
# is. This list is only for the two patterns below - a landlord, boss or bank keeps the stand-down.
CLOSE = (r"(?:ex|husband|wife|partner|boyfriend|girlfriend|fiance|fiancee|stepdad|stepmum|stepmom|"
         r"stepfather|stepmother|dad|mum|mom|father|mother|son|daughter|brother|sister|carer|"
         r"uncle|aunt|auntie|nan|grandad|grandpa|grandma)")
# A threat of the authorities made by someone close is the abuse case, and the object stand-down
# in _NOT_A_THREAT must not reach it: "my ex is threatening me with the police", "my husband is
# threatening to report me", "my ex is threatening me with a solicitor". The same words from a
# boss or a landlord are a bad job, which is what the stand-down is for, so the counterparty is
# the whole rule here as well.
# Whoever the threatening is coming from. It spans the written form and the contracted one,
# because "hes threatening me with the police" and "he is threatening me with the police" are the
# same sentence typed by different people, and only the first was reaching this case.
THREAT_SUBJECT = r"(?:he'?s|she'?s|they'?re|he|she|they|my\s+" + CLOSE + r")"
THREAT_COERCIVE = (
    r"\b" + THREAT_SUBJECT + r"\b[^.?!]{0,40}\bthreaten(?:s|ed|ing)?\b[^.?!]{0,25}\b"
    r"(?:police|cops?|solicitor|lawyer|court|custody|social\s+services)\b",
    r"\b" + THREAT_SUBJECT + r"\b[^.?!]{0,40}\bthreaten(?:s|ed|ing)?\s+to\s+"
    r"(?:call|ring|report|tell|contact|go\s+to)\b[^.?!]{0,20}\b(?:police|cops?|solicitor|"
    r"lawyer|court|custody|social\s+services)\b",
    # The person threatened is not always the one typing: "my stepdad is threatening my mum" got
    # "Noted: your stepdad is threatening your mum." Both ends of it are close, so it is this case.
    r"\bmy\s+" + CLOSE + r"(?:'?s|\s+is|\s+keeps?|\s+has\s+been)\s+threatening\s+my\s+"
    + CLOSE + r"\b",
)

# What a refusal takes away is the exit *and* the life behind it: a home, the people in it, the
# money to run it and the work that pays for it. The three refusal arms below all ended at the way
# out of the house, so "my husband refused to let me see my friends", "he refused to let me have my
# own money" and "my partner refused to let me work" - the same control said about a person rather
# than a door - were a shrug. Naming the life here rather than in one arm keeps the three of them
# saying the same thing, and the objects are specific so a refusal of a biscuit or a night out is
# not part of it.
_REFUSED_EXIT = (
    r"(?:past|through|out|out\s+of\s+the\s+(?:house|flat|room|car)|leave|go|go\s+out|"
    r"go\s+anywhere|see\s+(?:(?:my|her|his|the|any|our)\s+)?(?:own\s+)?(?:friends|family|mum|mom|"
    r"dad|mother|father|parents|sister|brother|kids|children|mates|pals|buddies|colleagues|"
    r"coworkers|anyone|people)|speak\s+(?:to|with)\s+"
    r"(?:(?:my|her|his|the|any)\s+)?(?:friends|family|mum|mom|dad|mother|father|parents|"
    r"sister|brother|kids|children|anyone|people)|have\s+(?:any\s+|my\s+own\s+|the\s+)?"
    r"(?:money|wages|bank\s+card|bank\s+account|debit\s+card|keys|a\s+job|my\s+own\s+money|"
    r"friends|a\s+life|people\s+over|visitors|company|a\s+social\s+life)|"
    # "wont let me work from home" is a rota, not a door locked: the work only counts as the exit
    # when it is the job itself, not the place or the hours it is done in.
    r"work(?!\s+(?:from|at|in|late|early|nights?|weekends?|evenings?|overtime|flexibly|"
    r"remotely|hybrid|part[\s-]?time|full[\s-]?time|with|on|for))|"
    r"study|sleep|get\s+a\s+job|look\s+for\s+work|"
    # `drive` on its own is the car key, not the way out of the house: "my husband wont let me
    # drive" is a tiff about the car, and it was the card. The car and the journey to somewhere
    # are what a person who will not let you out takes away.
    r"drive\s+(?:the\s+car|my\s+car|his\s+car|her\s+car|our\s+car|to\s+work|to\s+the\s+shops|"
    r"anywhere|myself)|visit\s+"
    r"(?:(?:my|her|his|any)\s+)?(?:friends|family|mum|mom|dad|mother|father))"
)

# The one arm a bereavement can look like, because "the death of my wife has hit me hard" has a
# person and a "hit me" in it. It is named here and left out of ABUSE_NOT_HIT by name, not by
# position: a positional slice silently took in the next arm whenever a new one went in front of it.
# The verbs that take a body part as their object without becoming something else. "he twisted my
# arm" and "he threw my back out" are idioms about persuasion and a bad lift, so the twisting and
# the throwing verbs are not here even though they are in ABUSE_VERB.
ABUSE_VERB_PART = (
    r"(?:hits?|hitting|beat(?:s|ing)?|punch(?:es|ed|ing)?|kick(?:es|ed|ing)?|chok(?:es|ed|ing)|"
    r"slapp?(?:s|ed|ing)?|smack(?:s|ed|ing)?|drag(?:s|ged|ging)?|"
    # A burn is not a blow: `he burned my arm cooking` was the abuse card, and the burn answer is
    # the one with the water in it. Every burn verb stays out of this list.
    r"strangl(?:e|es|ed|ing)|shov(?:e|es|ed|ing)|"
    r"spat\s+at|spit\s+at|hurl(?:s|ed|ing)?|attack(?:s|ed|ing)?|savaged|mauled|thump(?:s|ed|ing)?|"
    r"push(?:es|ed|ing)?|whack(?:s|ed|ing)?|head-?butt(?:s|ed|ing)?)")
    # ...and not "grabbed": `he grabbed my shoulder` was an ordinary hand on main and the card
    # here, while `he grabbed my arm hard` and `he grabbed my throat` are read by the arms above.
    # A grip is not a blow, so a part after it is the crowd on the tube, not the card (zippy).
    # ...but not "held" and not "pinned": a body part is what those two take in ordinary hands -
    # "he held my arm as we crossed the road", "my son held my arm", "he held my face in his
    # hands" - and eleven lines of that family became the 999 card for it (peach-hammer's read).
ABUSE_HIT_ME = (
    r"\b(?:he|she|they|hubby|my\s+" + ABUSER + r")\b.{0,30}\b" + ABUSE_VERB + r"\s+me\b",
    # A hit is not always said as "me": people name the place it landed. "my husband hit my
    # face", "he punched my arm", "she slapped my face" and "he hit my back" were a shrug on
    # main, while "my husband hit me" was the card, so the sentence people actually type about
    # it was the one answered with "Thanks for telling me". The body part is the object the verb
    # takes, and the surface after it is what makes it an accident instead ("he hit my head on
    # the door"), which is the one shape kept out.
    # The speaker's own body being hit is the card whatever comes after it: "he pushed my face
    # into the pillow" is not an accident because a surface is named.
    # ...except a surface a face is pushed into for a laugh. A birthday cake, a bowl of cream, a
    # snowdrift and a pile of leaves are what a head lands in at a party, a wedding or a first
    # snow, and "he pushed my face into the cake" is that face being mashed at a birthday, not a
    # hand held down. `tests/test_safety_head_into.py` had already turned this line away before
    # the body-part arm above reached it, so the arm now leaves the soft, silly things out: the
    # hard surfaces ("the door frame", "the wall", "the wardrobe") and the bedding are still the
    # card, because a pillow over a face is not a game.
    r"\b(?:he|she|they|hubby|my\s+" + ABUSER + r")\b[^.?!]{0,30}\b" + ABUSE_VERB_PART + r"\s+"
    r"(?:my|me\s+in\s+my)\s+(?:face|head|back|arm|arms|leg|legs|ribs?|stomach|"
    r"belly|jaw|eye|eyes|ear|ears|neck|throat|shoulders?|chest|side|hip|hips|thigh|mouth|nose|"
    r"teeth|wrist|knee)\b"
    r"(?![^.?!]{0,40}\b(?:cake|cakes|cream|icing|jelly|bun|buns|pudding|pie|pies|flour|"
    r"bunting|snow|snowdrift|leaves|foam|bubbles|mud|sand|dough|pillow\s+fight)\b"
    # ...unless a blow is named in the same breath: "he pushed my face into the cake and then hit
    # me" is two things, and the second is the card. The surface excuses the shove, not what comes
    # after it.
    # ...but a room that slaps a person on the back is pleased with them: "pushed my face into the
    # cake and everyone slapped me on the back" is a party, and the back of the head is still a
    # blow.
    r"(?![^.?!]{0,60}\b(?:hit|hits|punch(?:ed|es)?|kick(?:ed|es)?|slap(?:ped|s)?|beat(?:s)?|"
    r"chok(?:ed|es)?|shov(?:ed|es)?|push(?:ed|es)?)\s+me\b"
    r"(?!\s+(?:on|round|in)\s+the\s+back\b))"
    # ...and a line that says they could not breathe is not a snowball, however it is typed.
    r"(?![^.?!]{0,60}\b(?:breath|breathe|breathing|breathless|blacked\s+out|passed\s+out|"
    r"unconscious|choking|couldnt\s+breathe|could\s+not\s+breathe|no\s+air)\b))",
    # A scratch is a blow when it lands on the face, the arms or the throat, and a kindness when it
    # lands on the back: "he scratched my back" is an itch being dealt with. The two arms that read
    # a blow landing on a place did not take the scratching verbs, so `he scratched my face` was a
    # shrug and `my husband scratched my arms` was a cat-scratch card. This arm is last in the
    # tuple because the arm before it closes a group it opened: an arm put between them leaves that
    # group unclosed, and the whole case then fails to compile and is skipped without a word.
    r"\b(?:he|she|they|hubby|my\s+" + ABUSER + r")\b[^.?!]{0,30}\b(?:scratch(?:es|ed|ing)?|"
    r"claw(?:s|ed|ing)?)\s+(?:my|me\s+in\s+my)\s+(?:face|head|arm|arms|leg|legs|ribs?|"
    r"stomach|belly|jaw|eye|eyes|ear|ears|neck|throat|shoulders?|chest|side|hip|hips|thigh|"
    r"mouth|nose|teeth|wrist|knee)\b"
    # ...and a scratch that names where it happened is the roses: "he scratched my arm on the
    # bushes" is a walk through a garden, not a hand. A place after the part takes it out of this
    # arm, unless the same line also says it bled, bruised, happened again or frightened them.
    r"(?![^.?!]{0,30}\b(?:on|against|through|by)\s+(?:the|a|an|some|my|his|her|their|our)?\s*\w+)"
    r"(?![^.?!]{0,40}\b(?:bleed|bleeds|bled|bleeding|blood|bruise|bruises|bruised|marks|"
    r"scarred|again|police|scared|afraid|frightened|threaten\w*|strangl\w*|choke\w*|hit|hits|"
    r"punch\w*|kick\w*|beat\w*)\b)",
)
# The subject of "has me pinned", including the way it is typed without the apostrophe: "hes got me
# pinned to the wall" reached the worktop-cleaning answer because every arm wanted a bare "he".
HAS_ME_SUBJECT = r"\b(?:he|she|they|he'?s|she'?s|they'?re|hubby|my\s+" + ABUSER + r")\b"
# The words that say the grip was a game, a sport, a haircut or a figure of speech: "he had me
# against the wall at squash", "he pinned me on the floor laughing", "he held me by the hair while
# he cut it", "my boss has me by the throat over this deadline". They fence only the grip arms
# written beside them, not the whole case, so a blow, a fear or a threat in the same line is still
# the card.
# The sports a grip belongs to. It is its own piece because the arm that names the place a body is
# held against ("he held me against the wall at squash") is older and must keep the laughter as the
# card: a man holding someone against a wall and laughing is not a game.
GRIP_GAME = (r"\b(?:squash|tennis|judo|karate|mma|taekwondo|rugby|football|netball|wrestl\w*|"
             r"sparring|dojo|scrum|scrums|matches?)\b")
GRIP_GAME_FENCE = r"(?![^.?!]{0,30}" + GRIP_GAME + r")"
GRIP_NOT_AN_ASSAULT = (
    GRIP_GAME_FENCE,
    r"(?![^.?!]{0,30}\b(?:play\w*|tickl\w*|laugh\w*|giggl\w*|joking|for\s+fun)\b)"
    r"(?![^.?!]{0,30}\b(?:deadline|deadlines|budget|bills?|rent|mortgage|money|hours|rota|shift|"
    r"shifts|clock|targets?|emails?|paperwork)\b)"
    r"(?![^.?!]{0,30}\b(?:haircut|while\s+(?:he|she|they|it)\s+cut)\b)"
)
# The same fence for an arm that is one string rather than a tuple.
GRIP_NOT_AN_ASSAULT_STR = "".join(GRIP_NOT_AN_ASSAULT)

# A blow is a blow, but the same words over a game are a loss and the same words over a request
# are a favour: "hes beating me at fifa" is a console, and "hes been hitting me up for a tenner"
# is asking. Both arms below read a verb and a person, so these two tails keep the game and the
# ask out of the card. The word after at/in decides the game - a game is a thing beaten at, while
# a place, a time or a part of the body is not one, and those keep the card ("he beats me at
# home", "at night", "in the kitchen", "in the back", "in front of the kids").
GAME_WORD_STOP = (
    r"(?!the\b|a\b|an\b|home\b|house\b|work\b|school\b|night\b|nights\b|bed\b|morning\b|"
    r"afternoon\b|evening\b|weekend\b|weekends\b|front\b|public\b|private\b|kitchen\b|"
    r"bathroom\b|bedroom\b|hall\b|stairs\b|car\b|street\b|garden\b|pub\b|court\b|"
    r"office\b|hospital\b|head\b|face\b|ribs\b|back\b|stomach\b|chest\b|arm\b|arms\b|"
    r"leg\b|legs\b|neck\b|throat\b|gut\b|kidney\b|kidneys\b|hands?\b|fists?\b|feet\b|"
    r"foot\b|shoulders?\b|knees?\b|elbows?\b)[\w'-]+"
)
# The same game as a stand-down of its own, for the arms that another pattern in ABUSE reaches:
# what ABUSE_FINE holds is what the game is, so the game is written out here as it is played.
GAME_PLAYED = (
    r"\bbeat(?:s|en|ing)?\s+(?:me|us)\s+(?:at|in)\s+(?:the\s+|a\s+)?" + GAME_WORD_STOP
)
GAME_AFTER_ME = (
    r"(?!\s+(?:at|in)\s+(?:the\s+|a\s+)?"
    + GAME_WORD_STOP + r")")
# "Hitting me up for" something is asking me for it.
ASK_AFTER_ME = r"(?!\s+up\s+(?:for|to)\b)"

ABUSE = THREAT_COERCIVE + (
    # Said in the present tense it is a habit, and still the card: "he holds me against the wall
    # every time we argue". Only the grip words that need a place afterwards are here, so a hand
    # on you to steady you is not caught.
    r"\b(?:he|she|they|hubby|my\s+" + ABUSER + r")\b[^.?!]{0,20}\b(?:holds?|keeps?|pins?|"
    r"grips?|presses?)\s+(?:me|us)\s+(?:up\s+)?(?:against|into|onto)\s+(?:the\s+|a\s+|my\s+)?"
    r"(?:wall|floor|door|bed|ground|fridge|cooker|cupboard|sofa|table)\b",
    *ABUSE_HIT_ME,
    # "he threw a glass at me", "she threw a plate at my head": the thing is in between, so the
    # verb and the "at me" are what matter. "my husband threw me a surprise party" has no "at".
    r"\b(?:he|she|they|my\s+" + ABUSER + r")\b.{0,30}\b(?:thr(?:ew|ows|owing)|hurl(?:ed|s)|"
    r"lobbed|shov(?:e|es|ed)|push(?:es|ed)|swung|swing|lunged)\b.{0,25}\b(?:at|against)\s+"
    r"(?:me|my\s+(?:head|face|arm|back|leg|son|daughter|kids?|child|mum|dad))\b",
    # A hand round the throat is the most dangerous assault there is, and it was nobody's
    # pattern: `my husband put his hands round my throat` got a shrug.
    r"\b(?:he|she|they|my\s+" + ABUSER + r")\b.{0,25}\b(?:hands?|fingers?|arm)\s+(?:round|around|on|"
    r"across)\s+(?:my\s+)?(?:throat|neck)\b",
    r"\bput\s+(?:his|her|their)\s+hands?\s+(?:round|around|on)\s+(?:my\s+)?(?:throat|neck)\b",
    r"\b(?:held|pinned|pressed)\s+me\s+(?:down|against\s+the\s+(?:wall|floor|door|bed)|"
    r"on\s+the\s+(?:floor|ground|bed)|in\s+the\s+(?:kitchen|bathroom|bedroom|hall|hallway))\b"
    + GRIP_NOT_AN_ASSAULT_STR,
    # The same assault with the places people actually say, and with the hand on you as a verb: "my
    # husband held me against the wall", "he shoved me up against the fridge", "she pushed me onto
    # the bed". The arm above only knew one place and two verbs.
    r"\b(?:he|she|they|my\s+" + ABUSER + r")\b.{0,25}\b(?:held|pinned|pressed|pushed|shoved|"
    r"backed|slammed|threw)\s+me\s+(?:up\s+)?(?:against|onto|into|to)\s+the\s+(?:wall|floor|door|"
    r"bed|fridge|cooker|counter|cupboard|sofa|ground)\b" + GRIP_GAME_FENCE,
    # "my husband has me pinned to the wall" - the restraint is a participle *after* "me", so
    # every arm above, which wants the verb and then "me", walked past it. "has me worried", "has
    # me on a diet" and "has me doing the washing up" stay ordinary because the participle has to
    # be one of restraint.
    # ...but a participle with an object is only restraint when the object is a place a body can be
    # held against. "my partner has me pinned to the rota" is a shift pattern, and the card on a
    # work line is the false alarm this lane must not have, so the words a job hands you stand the
    # arm down wherever the participle would otherwise take them.
    HAS_ME_SUBJECT + r".{0,20}\b(?:has|had|have|got|gets|keeps?|kept|"
    r"holds?|held|leaves?|left|pins?|pinned)\s+me\s+(?:pinned|trapped|cornered|locked\s+in|"
    r"pressed|held|shoved|pushed|backed|slammed)\b"
    r"(?!\s+(?:to|on|onto|against|into|in|by)\s+(?:the\s+|a\s+|my\s+|his\s+|her\s+|their\s+|our\s+)?"
    r"(?:rota|rotas|shift|shifts|roster|rosters|list|lists|board|boards|schedule|schedules|"
    r"duty|duties|plan|plans|app|apps|"
    # and the desk you are chained to: "she keeps me pinned to my desk all day" is a working day,
    # not a hand on you. The office words are here so a boss doing the talking is not a partner,
    # and the bed and the wall are not in the list, so the restraint that matters keeps its arm.
    r"desk|desks|office|meeting\s+room|conference\s+room|trolley|till|screen|monitor|keyboard|"
    r"in-?tray|inbox|deadline|deadlines|shop\s+floor|checkout|call\s+list)\b)",
    # A person cornered in a room is an exit being blocked, and people name the rooms of the
    # house: "my ex cornered me in the hall and would not let me past" was a shrug. The person has
    # to be in front of it, so a cornered pet or a shelf is not this.
    r"\b(?:he|she|they|my\s+" + ABUSER + r")\b[^.?!]{0,25}\b(?:corner(?:ed|s)?|trapped|backed|"
    r"blocked|pinned)\s+me\s+(?:in|into)\s+(?:the\s+|my\s+|a\s+)?(?:kitchen|bedroom|bathroom|"
    r"bath|hall|hallway|corridor|lift|stairwell|stairs|garage|flat|house|room|doorway|balcony|"
    r"landing|porch|study|shed)\b",
    # The exit itself refused: "he wont let me leave the house", "my husband will not let me go
    # out". A refusal to let someone go is the control the card is for, and the person is in
    # front of it so a rota or a roped-off road is not.
    r"\b(?:he|she|they|my\s+" + ABUSER + r")\b[^.?!]{0,25}\b(?:wouldn?'?t|won'?t|"
    r"would|will|refused?|refuses?)\s*(?:not\s+)?(?:to\s+)?(?:let|allow)\s+me\s+"
    + _REFUSED_EXIT + r"\b",
    # The same refusal with "does not" instead of "will not", and the person in front of it for the
    # same reason: an anxiety, a back, a rota, a shift or a bus does not let somebody leave either,
    # and a thing that keeps you in the house is not a person keeping you there.
    r"\b(?:he|she|they|my\s+" + ABUSER + r")\b[^.?!]{0,25}\b(?:doesn'?t|don'?t|didn'?t|"
    r"(?:does|do|did)\s*not)\s*let\s+me\s+" + _REFUSED_EXIT + r"\b",
    # Locked in with somebody on the other side of the door: "i am locked in the bathroom, he is
    # banging on the door" was answered with the door-that-slams-in-the-wind. The room and the
    # person and the noise all have to be there, so "i locked myself in the bathroom" and a line
    # with nobody in it stay ordinary. A child doing the banging is stood down below.
    r"\b(?:locked|shut|trapped|stuck)\s+(?:in|inside)\s+(?:the\s+|my\s+|a\s+|this\s+)?"
    r"(?:bathroom|bedroom|toilet|kitchen|room|flat|house|hall|hallway|car|cellar|basement|loft|"
    r"attic)\b[^.?!]{0,40}\b(?:he|she|they|my\s+" + ABUSER + r")\b[^.?!]{0,30}"
    r"\b(?:bang(?:ing|s)?|pound(?:ing|s)?|hammer(?:ing|s)?|kick(?:ing|s)?|smash(?:ing|es)?|"
    r"breaking|shout(?:ing|s)?|scream(?:ing|s)?|rattl(?:ing|es))\b",
    # The same line said the other way round: "he is banging on the door and i am locked in".
    r"\b(?:he|she|they|my\s+" + ABUSER + r")\b[^.?!]{0,30}\b(?:bang(?:ing|s)?|pound(?:ing|s)?|"
    r"hammer(?:ing|s)?|kick(?:ing|s)?|shout(?:ing|s)?|scream(?:ing|s)?)\b[^.?!]{0,40}"
    r"\b(?:locked|shut|trapped|stuck)\s+(?:in|inside)\b",
    # A grip named by the part it has hold of, which no arm had at all: "my ex has me by the
    # throat", "she has me by my hair", "he held me by the scruff of my neck" were all a shrug.
    # The parts are the ones a hand closes on and a handshake never does, so being taken or held by
    # the hand or the arm, to be steered, stays ordinary.
    HAS_ME_SUBJECT + r"[^.?!]{0,15}\b(?:has|have|had|got|keeps?|kept|holds?|held|grabs?|grabbed|"
    r"drags?|dragged|pulls?|pulled|takes?|took)\s+me\s+by\s+(?:the|my|his|her|their)\s+"
    r"(?:throat|neck|hair|scalp|collar|scruff|jaw)s?\b" + GRIP_NOT_AN_ASSAULT_STR,
    # "my husband has me up against the fridge": the place is what he has me against, with no
    # participle in between, and every arm above wanted one. The places are the ones a body is
    # held against, so a rota, a shift and a list keep their own answers.
    HAS_ME_SUBJECT + r"[^.?!]{0,15}\b(?:has|have|had|got|keeps?|kept|holds?|held|pins?|pinned|"
    r"presses?|pressed|shoves?|shoved|pushes?|pushed)\s+me\s+(?:up\s+)?(?:against|onto|into|to)\s+"
    r"(?:the\s+|a\s+|my\s+)?(?:wall|floor|door|bed|ground|fridge|cooker|cupboard|sofa|counter|"
    r"table|car)\b" + GRIP_NOT_AN_ASSAULT_STR,
    # Shaken hard is an assault; shaken awake is how you wake a heavy sleeper.
    r"\b(?:shook|shak(?:es|ing))\s+me\s+(?:hard|violently|roughly|until|so\s+hard)\b",
    # A hand round the wrist, a fist in the hair: the body part is being held, not just bumped.
    r"\b(?:grab(?:s|bed|bing)?|yank(?:s|ed|ing)?|twist(?:s|ed|ing)?|wrench(?:es|ed|ing)?|"
    r"pull(?:s|ed|ing)?)\s+(?:me\s+)?by\s+the\s+(?:hair|throat|neck|arm|wrist|collar|scruff)\b",
    r"\b(?:grab(?:s|bed|bing)?|yank(?:s|ed|ing)?)\s+my\s+(?:arm|wrist|hair|throat|neck|collar)\b",
    # A blow that lands on a named part is the same blow: "my husband hit my face", "my dad hit
    # my arm", "my partner slapped my face". Every arm above wanted "me" straight after the
    # verb, so the commonest way of saying it was the listening line (keen-book, #safety 40291).
    # The one doing it has to be a person, or "the door hit my arm" and "the ball hit my face"
    # would be violence, and the part is what makes it a blow rather than a shove.
    r"\b(?:he|she|they|my\s+" + ABUSER + r")\b[^.?!]{0,30}\b(?:hits?|hitting|beat|beats|beating|"
    r"slapp?(?:s|ed)?|punch(?:es|ed)?|kick(?:s|ed)?|struck|thump(?:s|ed)?|whack(?:s|ed)?|"
    r"smack(?:s|ed)?|belt(?:s|ed)?|cuff(?:s|ed)?)\b\s+"
    r"(?:me\s+(?:in|on|across|round|about)\s+)?(?:the|my)\s+"
    r"(?:face|head|arm|ribs|stomach|back|throat|neck|jaw|cheek|nose|eye|eyes|leg|hip|shoulder|"
    r"wrist|chest|side|belly|ear|mouth|thigh|knee)s?\b",
    r"\b(?:he|she|my\s+" + ABUSER + r")\b.{0,30}\bthreaten(?:s|ed|ing)?\s+me\b" + _NOT_A_THREAT,
    # "they" is a lender, a landlord, a debt collector, a company: a threat from them is money or
    # housing and the abuse helpline is the wrong number for it - "i owe money to a loan shark and
    # they are threatening me" was getting the domestic abuse card. What they say they will do is
    # still an assault, so "they threatened to kill me" keeps the abuse card.
    r"\b(?:he|she|they|my\s+" + ABUSER + r")\b.{0,30}\bthreaten(?:s|ed|ing)?\s+"
    r"(?:me\b|us\b|to\s+(?:kill|hurt|hit|stab)\s+me)" + _NOT_A_THREAT,
    # A stated intention, not the verb "threaten": "my boss said he would stab me".
    r"\b(?:he|she|they|my\s+" + ABUSER + r")\b.{0,30}\b(?:said|says|told\s+me)?\s*"
    r"(?:he|she|they)?\s*(?:would|will|is\s+going\s+to|was\s+going\s+to)\s+"
    r"(?:kill|hurt|stab|rape|strangle|shoot)\s+me\b",
    r"\b(?:he|she|they)\s+(?:(?:won'?t|wont|wouldn'?t|wouldnt|didn'?t|doesn'?t|refus(?:es?|ed)\s+to)"
    r"\s+(?:let|allow)|never\s+lets?)\s+me\s+" + _REFUSED_EXIT + r"\b",
    r"\b(?:abusing|abused|abuses)\s+me\b", r"\b(?:sexual(?:ly)?\s+assault(?:ed)?|raped|raping)\b",
    r"\bhits?\s+me\s+(?:when|if|again)\b",
    r"\bafraid\s+(?:of|to\s+go)\s+(?:him|her|them|home|back\s+home)\b",
    r"\bscared\s+(?:of|to\s+go)\s+(?:him|her|home|back\s+home|my\s+(?:husband|partner|dad|mum|boyfriend|girlfriend|carer))\b",
    r"\b(?:locks?|locked)\s+me\s+(?:in|out)\b",
    # A person who shuts somebody into a car or a room is confining them, and "he trapped me in
    # the car" was the crash card with its "keep talking to them" - which cannot be said to the
    # person it is happening to. The subject is a person, so "the car trapped me" is still the
    # crash; and "kept" and "held" are left out, because "kept me in the loop" and "held me in
    # his arms" are the two idioms that would come with them.
    r"\b(?:" + THREAT_SUBJECT + r"|the\s+(?:man|woman|lady|guy|bloke))\b[^.?!]{0,20}\b"
    r"(?:trapped|pinned|wedged|locked|shut)\s+(?:me|us)\s+(?:in|inside|under|into)\b",
    # The same refusal with the person in front of it, because without one a rota is keeping you
    # in: "my rota wont let me go out on friday", "my shift wont let me leave early", "my job wont
    # let me go out on friday", "money wont let me go out this month", "my anxiety wont let me go
    # out", "my kids wont let me leave the house" and "my toddler wont let me leave the room" were
    # all the domestic abuse card. The words here are the people you cannot get away from, not a
    # manager or a landlord, who each have their own answer.
    r"\b(?:he|she|they|my\s+(?:partner|husband|wife|boyfriend|girlfriend|ex|dad|mum|mom|father|"
    r"mother|son|daughter|brother|sister|step(?:dad|mum|mom|father|mother|son|daughter|brother|"
    r"sister)|carer|boy|girl|nan|nana|gran|granny|uncle|aunt|auntie|cousin|in-?laws?))\s+"
    r"(?:won'?t|wont|wouldn'?t|wouldnt|refus(?:es?|ed)\s+to|refuse\s+to|never\s+lets?\s+me|"
    r"didn'?t\s+let|doesn'?t\s+let|did\s+not\s+let)\s+let\s+me\s+" + _REFUSED_EXIT + r"\b",
    r"\bthreatened?\s+(?:to\s+kill|me\s+with)\b",
    # The same threat with no person named in front of it, or with "us" rather than "me": "is
    # threatening me", "he keeps threatening us". See _NOT_A_THREAT for the tail that stands a
    # warning or a tenancy down.
    # The contracted present tense is how most people type it - "hes threatening me", "shes
    # threatening me", "theyre threatening me" - and a person typing those is in the same
    # position as one typing "he is threatening me", so it must not be the difference between
    # the card and a shrug. "someone's" too: a stranger threatening you is still a threat.
    r"\b(?:(?:he|she|they|someone|somebody|my\s+" + CLOSE + r")'?s|they'?re|"
    r"is|are|keeps?|has\s+been|have\s+been)\s+threatening\s+(?:me|us)\b" + _NOT_A_THREAT,
    r"\b(?:i'm|i\s+am)\s+(?:being\s+)?(?:controlled|coerced)\b",
    # The passive is how a frightened person types it. Every arm above names the person doing it
    # ("my ex is threatening me"), so the same sentence with the speaker as the object of the verb
    # was a shrug: "i am being abused", "i am being threatened by my ex", "i was stalked". The
    # harm word after it is the whole rule, and _NOT_A_THREAT still stands a threat over a written
    # warning, a fine or an eviction down. "beaten" is only the "beaten up" form, because "i was
    # beaten in the final" is a match, and the sports stand-down below is not reachable from here.
    # "by" is the one thing that can make the line ordinary, and it is a person or nothing: "i am
    # being followed by my ex" is the case, and "i am being followed by bad luck", "by a cold",
    # "by my shadow", "by google maps", "by a black cat" are the same sentence with nothing to
    # fear in it. A list of harmless things cannot cover them all - a toddler, a satnav and a
    # shadow were each a false card - so the guard asks for a person rather than reading off a
    # list of things that are not one.
    r"\b(?:i'm|i\s+am|im|i\s+was|i\s+have\s+been|i've\s+been|ive\s+been|i\s+keep\s+being|"
    r"i\s+keep\s+getting)\s+(?:being\s+|getting\s+)?(?:abused|threatened|stalked|followed|"
    r"watched|harassed|hit|attacked|assaulted|raped|molested|groomed|"
    r"beaten\s+up)\b" + BY_NOT_A_THING + _NOT_A_THREAT,
    # A choke in the present tense has to be in progress to be an assault. "im choked" on its own
    # is how a person in Britain and Ireland says they are gutted - it was reaching the domestic
    # abuse card with a 999 line, which is not what being passed over for a job is - and the
    # airway is answered by the choking first aid. A choke with a person in it ("i was choked",
    # "hes been choking me", "im being choked") keeps the card, because that is a report of a hand
    # at a throat and not a feeling.
    r"\b(?:i'm|i\s+am|im)\s+(?:being|getting)\s+(?:choked|strangled)\b"
    + BY_NOT_A_THING + _NOT_A_THREAT,
    # ...and the same for the past tense, which is the other way the feeling is said: "i was
    # choked about it" is a person's day, not a hand at a throat. A choke about a thing is not a
    # report of a person, so `about`/`over` after it stands this arm down too.
    r"\b(?:i\s+was|i\s+have\s+been|i've\s+been|ive\s+been|i\s+keep\s+(?:being|getting))\s+"
    r"(?:being\s+|getting\s+)?(?:choked|strangled)\b(?!\s+(?:about|over)\b)"
    + BY_NOT_A_THING + _NOT_A_THREAT,
    # The present perfect is how most people say it: "hes been hitting me", "shes been hitting me",
    # "hes been hitting me again". The arm read the simple present only, so the joined spelling of
    # "he has been hitting me" - which the card already answered - came back a shrug, and "hes been
    # hitting me again" came back praise for a good day.
    r"\b(?:he|she|they|my\s+\w+)'?(?:s|ve)?\s+(?:been\s+)?(?:hurting|hitting|strangling)"
    r"\s+me\b" + ASK_AFTER_ME,
    # "Beating" is a game as often as it is a blow - "hes beating me at fifa" is a console - so it
    # keeps its own arm with the game fence on the end of it.
    r"\b(?:he|she|they|my\s+\w+)'?(?:s|ve)?\s+(?:been\s+)?beating\s+me\b"
    + GAME_AFTER_ME + ASK_AFTER_ME,
    # "my husband is being abusive" is the same sentence as "my husband is abusive", and it was a
    # shrug. Only the two words that have no other meaning take the "being", because "my mum is
    # being controlling about the wedding" is an argument about seating.
    r"\bmy\s+(?:partner|husband|wife|boyfriend|girlfriend|dad|mum|father|mother|ex|carer)\s+is\s+"
    r"(?:being\s+)?(?:abusive|violent)\b|\bmy\s+(?:partner|husband|wife|boyfriend|girlfriend|dad|"
    r"mum|father|mother|ex|carer)\s+is\s+(?:controlling|coercive)\b",
    r"\b(?:he|she|they)'?s?\s+(?:being|is|keeps?\s+being)\s+(?:abusive|violent)\b",
    r"\b(?:he|she|they)\s+is\s+being\s+(?:abusive|violent)\b",
    # The adjective often comes first, and then nothing above rings: "how do i leave my violent
    # boyfriend" and "how do i leave my abusive husband" were both a shrug, while "my boyfriend
    # is violent" already had the card.
    r"\bmy\s+(?:violent|abusive|controlling|coercive|dangerous|aggressive|threatening)\s+"
    r"(?:partner|husband|wife|boyfriend|girlfriend|dad|mum|father|mother|ex|carer|"
    r"son|daughter|brother|sister|stepdad|stepdad|stepmum|stepfather|stepmother)\b",
    # And the person is sometimes only a relative clause - "how do i break up with someone who
    # hits me", "how do i get away from someone who hurts me" - which none of the patterns above
    # reach, because they all want he, she, they or a relationship word.
    r"\b(?:someone|somebody|a\s+(?:man|bloke|guy|woman|lad|person)|the\s+(?:man|woman|person))\b"
    r"[^.?!]{0,25}\b" + ABUSE_VERB + r"\s+me\b" + HIT_BY_A_VEHICLE,
    r"\b(?:someone|somebody)\b[^.?!]{0,25}\bhurt(?:s|ing)?\s+me\b" + HIT_BY_A_VEHICLE,
    # The same arm with the adjective instead of the verb: "how do i end a relationship with
    # someone abusive" and "i live with a man who is violent" name no violence the verbs above
    # can see, and the first was being sent an essay-writing card.
    r"\b(?:someone|somebody|a\s+(?:man|bloke|guy|woman|lad|person|partner)|"
    r"the\s+(?:man|woman|person|partner))\b[^.?!]{0,25}\b"
    r"(?:is\s+|was\s+|being\s+|been\s+)?(?:abusive|violent|controlling|coercive|dangerous|"
    r"aggressive)\b",
    # And the arm with being frightened instead of being hit: "how do i leave someone who scares
    # me", "i live with someone who frightens me". Both were a punt on main's hedge.
    r"\b(?:someone|somebody|a\s+(?:man|bloke|guy|woman|lad|person)|the\s+(?:man|woman|person))\b"
    r"[^.?!]{0,25}\b(?:scares|frightens|terrifies|intimidates)\s+me\b",
    r"\b(?:i|we|he|she|they)\s+(?:was|were|got|just\s+got)\s+(?:attacked|assaulted|mugged|beaten\s+up)\b",
    r"\b(?:i'm|i\s+am)\s+(?:scared|terrified)\s+of\s+(?:going\s+home|him|her)\b",
    # A threat does not always come from somebody you can name. "someone is threatening me" and
    # "a bloke down the road is threatening me" were a shrug and the motorway answer, because
    # every threat pattern above needs he, she, they or a partner. The next tuple keeps the
    # threats that are not this: a boss, a school, a bank, a landlord.
    r"\b(?:someone|somebody|a\s+(?:man|bloke|guy|woman|lad)|(?:the|our|my)\s+neighbours?|"
    r"next\s+door)\b[^.?!]{0,30}\bthreaten(?:s|ed|ing)?\s+(?:me\b|to\s+(?:kill|hurt|harm|"
    r"hit|stab|beat)\s+me)",
)
# A partner who is *there* again - outside the door, in front of the house, waiting where you
# work, behind you on the walk home - says nothing a violence verb can catch, so `my ex is
# outside and i am scared` was answered with the breathing exercise for nerves before a big day
# and `my ex is banging on the door` with a door closer. The subject is the partner word only:
# this list leaves out the rest of the family, because "my son is outside playing" and "my mum is
# waiting in the car" are the same shape and nothing is happening in them.
PARTNER_CLOSE = (r"(?:ex|exes|husband|wife|partner|boyfriend|girlfriend|fiance|fiancee|"
                 r"baby\s*daddy|baby\s*dad|baby\s*mother|baby\s*mum)")
PURSUIT_SUBJECT = (r"\b(?:my\s+" + PARTNER_CLOSE + r"|my\s+ex'?s?)\b",)
# The fear, said by the person typing: "and i am scared", "im terrified", "i'm shaking".
# "scared hes going to be late" is not the fear: the word is doing the same work as "worried the
# bus wont come", so anything about a time after it takes the fear back out.
NOT_A_FEAR = (r"(?!\s+(?:that\s+)?(?:hes|shes|theyre|its|it'?s|im|i'?m|ill|i'?ll|hell|well|"
              r"going\s+to\s+be|we\s+will|we'?ll)\s*(?:going\s+to\s+be\s+)?(?:late|"
              r"late\s+home|in\s+trouble|on\s+time))")
PURSUIT_FEAR = (
    r"\b(?:i'?m|i\s+am|im)\s+(?:(?:really|so|very|that|proper|properly|absolutely|dead|"
    r"scared\s+witless)\s+)*(?:scared|frightened|terrified|afraid|panicking|shaking|worried)\b"
    + NOT_A_FEAR,
    r"\b(?:scared|frightened|terrified|afraid)\s+(?:of|to\s+go|to\s+leave|to\s+open)\b",
)
# Where a person stands when they are waiting for you rather than passing: the possessive place
# ("outside my house", "in front of my flat", "at my work") or the door itself.
# `my ex` is not `my husband` where the place is the one you are expected at: a husband outside
# your work is a lift, a wife outside the school is the pick-up, and an ex outside either is not.
PURSUIT_SUBJECT_EX = (r"\b(?:my\s+(?:ex|exes|baby\s*daddy|baby\s*dad|baby\s*mother|baby\s*mum)|"
                      r"my\s+ex'?s?)\b",)
# The forms that name no place at all: "my ex is waiting outside", "my ex is waiting for me". They
# are the card for an ex and the lift for a partner, which is the same split as the school gate.
PURSUIT_OUTSIDE = (
    r"\b(?:waiting|waits|sat|sitting|stood|standing|parked|lurking|hiding|hovering|"
    r"hanging\s+around)\s+(?:right\s+|still\s+|now\s+)?(?:outside|out\s+front|in\s+the\s+car\s+"
    r"outside|round\s+the\s+back)\b",
    r"\bwait(?:ing|s|ed)?\s+for\s+(?:me|us)\b",
)
PURSUIT_PLACE_WORK = (
    r"\b(?:outside|in\s+front\s+of|at\s+the\s+end\s+of|round\s+the\s+back\s+of)\s+"
    r"(?:my|our|the)\s+(?:work|workplace|office|school|nursery|college|uni|university|gates)\b",
    r"\b(?:waiting|waits|sat|sitting|stood|standing|parked|lurking|hiding|hovering|hanging\s+around)"
    r"\s+(?:right\s+|still\s+|now\s+)?(?:outside|near)\s+(?:my|our|the)\s+(?:work|workplace|"
    r"office|school|nursery|college|uni|university|gates)\b",
)
# Shouting at the door, drunk on the step, not going away: the fear is in the line without the word.
PURSUIT_LOUD = (
    r"\b(?:shouting|yelling|screaming)\s+at\s+(?:the\s+)?(?:football|telly|tv|match|game|"
    r"radio|news|kids|dog|cat|ref|referee)\b(?!.*\b(?:i'?m|i\s+am|im)\s+(?:scared|terrified))",
    r"\b(?:shouting|yelling|screaming|drunk|hammering|banging|pounding)\b",
    r"\b(?:won'?t|wont|refuses?\s+to)\s+(?:leave|go|move)\b",
)
# Both halves have to be in the line, in whichever order: the partner word and the place, or the
# partner word outside the house and the fear. `_both` lives a long way below with the fever and
# pet pairs, so the lookahead pair is written out here.
def _both_here(*groups):
    """One thing from each group, all in the line, in whichever order."""
    parts = ["(?=.*(?:" + "|".join(group) + "))" for group in groups]
    return "".join(parts)


PURSUIT = (
    # The partner and the place: "my ex is outside my house", "my ex is banging on the door".
    _both_here(PURSUIT_SUBJECT, PURSUIT_PLACE_HOME),
    # The fear is the place's stand-in: "my ex is outside and i am scared", "my ex is outside
    # shouting". Nothing else in the line needs to say what is wrong.
    _both_here(PURSUIT_SUBJECT, (r"\b(?:is|was|keeps?|still)\s+(?:right\s+)?(?:outside|here|back)\b",),
               PURSUIT_FEAR + PURSUIT_LOUD),
    # The same at the place you are expected at, but only for an ex: "my ex is waiting outside my
    # work" is not "my husband is outside my work, waiting to pick me up".
    _both_here(PURSUIT_SUBJECT_EX, PURSUIT_PLACE_WORK),
    # An ex waiting outside with no place named, or waiting for them at all.
    _both_here(PURSUIT_SUBJECT_EX, PURSUIT_OUTSIDE),
    # "he is following me" and "hes stalking me" name nobody, and there is nothing else they mean.
    r"\b(?:he|she|they|hes|shes|theyre)'?s?\b[^.?!]{0,12}\b"
    r"(?:follow(?:s|ing|ed)?|stalk(?:s|ing|ed)?)\s+(?:me|us)\b",
)
# Being called names is said without a verb of threat, so the abuse case never saw it: "my husband
# keeps calling me names", "my mum keeps calling me stupid, useless" and "he calls me stupid every
# day" all fell to "Thanks for telling me - I'm here if you want to dig into any of that", and
# "my husband calls me useless" to "That is worth mentioning to a GP". The person at home is the
# whole test, so a boss, a landlord and the children at school keep their own answers, and the aim
# is at the speaker ("me"), not at anything else in the line.
ABUSE_VERBAL_PERSON = (r"(?:he|she|they|hubby|husband|wife|partner|boyfriend|girlfriend|fiance|"
                       r"fiancee|ex|mum|mom|mam|mother|dad|father|stepdad|stepmum|stepmom|"
                       r"stepfather|stepmother|nan|nana|gran|granny|grandma|grandad|grandpa|"
                       r"carer)")
# The word they are called by: a plain "names" covers the rest of the sentence, and the labels are
# the ones people type. Nothing here is a word said in passing - every label is a verdict on the
# person, which is what makes it this case rather than an argument.
# "my wife says im crazy about the dog" and "he says im mental about my car" are affection, and
# "crazy in a good way" is a compliment: the word alone is the name, the word with a thing it loves
# is not. What follows it has to be a thing, not a reason: "about the dog" and "mad at her" are a
# thing loved or a thing someone is cross with, while "for crying", "for seeing my mum" and "about
# everything i do" are reasons handed to the person being called it, and a partner who calls you
# mental for seeing your mum is doing the thing this case is for.
ABUSE_VERBAL_MAD = (r"(?:mental|crazy|mad)(?!\s+(?:(?:about|over)\s+"
                    r"(?!everything|anything|every\s+thing|all\s+(?:of|the)|whatever|"
                    r"how\s+i|everyone|every\s+time|being|doing|saying|wanting)"
                    r"|at\s+(?!the\s+time|first|least)"
                    r"|in\s+(?:love|bed|a\s+good\s+way|the\s+good\s+way|a\s+kind\s+way)))")
ABUSE_VERBAL_LABEL = (r"(?:names|stupid|thick|dumb|useless|worthless|lazy|fat|ugly|pathetic|"
                      r"hopeless|a\s+failure|a\s+loser|a\s+waste\s+of\s+space|a\s+waste|"
                      r"nothing|" + ABUSE_VERBAL_MAD + r"|psycho|disgusting|a\s+slag|a\s+slut|a\s+bitch|"
                      r"a\s+cow|rubbish|a\s+disappointment|a\s+mistake|an\s+idiot|an\s+imbecile|"
                      r"stupid\s+cow|fat\s+cow|silly\s+cow|cretin|a\s+joke|unloveable|"
                      r"unlovable|a\s+burden|a\s+drain|a\s+piece\s+of\s+shit|"
                      r"a\s+piece\s+of\s+crap|shit)")
# The subject, glued or not: people type "hes always calling me names" and "shes always calling me
# useless" without the apostrophe and without the space, and a bare "\bhe\b" never matches "hes" -
# every one of these arms failed on the lines with the pronoun written that way, which is how most
# people type in a hurry.
# A child doing the same things is not the card: "my son pushes me and calls me names" is what a
# small person does when they are cross, and the answer for it is the parenting one. The subject
# has to be the child and the verb has to be theirs, so "my son was there when he pushed me" keeps
# the card.
CHILD_AGGRESSOR = (
    r"\b(?:(?:my|our|his|her|their|the)\s+(?:son|sons|daughter|daughters|child|children|kid|kids|"
    r"toddler|baby|teen|teenager|teenagers|boy|girl|boys|girls|little\s+one)|"
    r"my\s+(?:eldest|oldest|youngest))\b"
    # the child has to be the one doing it, so a "when he" between them is somebody else
    r"(?!\s+[^.?!]{0,12}\b(?:when|while|as)\s+(?:he|she|they)\b)[^.?!]{0,12}"
    r"\b(?:pushes?|pushed|pushing|hits?|hit|"
    r"hitting|kicks?|kicked|kicking|slaps?|slapped|slapping|bites?|bit|biting|punches?|punched|"
    r"punching|calls?\s+me|calling\s+me|called\s+me|swears?\s+at\s+me|shouts?\s+at\s+me|"
    r"yells?\s+at\s+me)\b",
)[:1]
ABUSE_VERBAL_SUBJECT = (r"\b(?:he|she|they|he'?s|she'?s|they'?re|my\s+" + ABUSE_VERBAL_PERSON +
                        r")\b")
ABUSE_VERBAL = (
    # "my husband keeps calling me names", "he calls me stupid every day", "shes always calling me
    # a fat cow".
    ABUSE_VERBAL_SUBJECT + r"[^.?!]{0,25}\b(?:calls?|calling|"
    r"called|keeps\s+calling)\s+me\s+(?:(?:a|an)\s+)?" + ABUSE_VERBAL_LABEL + r"\b",
    # "my partner tells me im worthless", "my mum says im thick".
    ABUSE_VERBAL_SUBJECT + r"[^.?!]{0,25}\b(?:tells?|telling|"
    r"told|says?|saying|said)\s+(?:me\s+)?i(?:'?m|\s+am)\s+(?:(?:a|an)\s+)?"     + ABUSE_VERBAL_LABEL + r"\b",
    # The habit said as a habit: "my wife keeps putting me down", "he is always running me down".
    ABUSE_VERBAL_SUBJECT + r"[^.?!]{0,30}\b(?:keeps?|kept|"
    r"always|constantly|regularly|never\s+stops|every\s+(?:day|night|week))\b[^.?!]{0,20}"
    r"\b(?:putting\s+me\s+down|put\s+me\s+down|running\s+me\s+down|having\s+a\s+go\s+at\s+me)\b",
    # ...and the habit said afterwards, which is how most people say it: "he puts me down all the
    # time", "hes always putting me down", "my husband runs me down constantly". The habit is the
    # point, so the marker is required here: one occasion has a place or a time in it - "my
    # partner puts me down in front of my friends", "he had a go at me at dinner" - and main
    # already answers those with what to say about one thing that happened. Replacing a usable
    # reply with a helpline card is a loss, so those lines are left alone.
    ABUSE_VERBAL_SUBJECT + r"[^.?!]{0,30}"
    r"\b(?:puts?\s+me\s+down|putting\s+me\s+down|runs?\s+me\s+down|running\s+me\s+down|"
    r"has\s+a\s+go\s+at\s+me|having\s+a\s+go\s+at\s+me)\b[^.?!]{0,25}"
    r"\b(?:all\s+the\s+time|all\s+day|constantly|always|every\s+(?:day|night|week|time)|"
    r"non[\s-]?stop)\b",
)
# ...and the same words when they are not aimed at a person: a nickname, a family who tease each
# other, a word in a game. The reciprocity is the tell, so "me and my sister call each other names"
# and "the lads call me names at five-a-side" keep their own answer.
ABUSE_VERBAL_FINE = (
    r"\b(?:call|calls|calling|called)\s+each\s+other\b",
    r"\b(?:we|we'?re|were)\s+(?:both\s+)?(?:call|calls|calling|tease|teasing|wind)\b",
    r"\b(?:me\s+and|between\s+me\s+and|my\s+(?:mates?|friends?|lads|colleagues?|team|"
    r"classmates?|schoolmates?|flatmates?|housemates?))\b[^.?!]{0,20}\b(?:call|calls|calling|"
    r"tease|teasing|rip\s+into)\b",
    r"\b(?:nickname|nicknames|term\s+of\s+endearment|pet\s+name|affectionately|"
    r"fondly)\b",
    r"\b(?:in\s+fun|for\s+a\s+laugh|in\s+good\s+fun|in\s+jest|in\s+play|at\s+five-a-side|"
    r"on\s+the\s+pitch|at\s+rugby|at\s+football|in\s+training)\b",
)
# The pursuit arms join the abuse case here, after the stand-down tuples, so nothing above them
# changes and ABUSE_NOT_HIT below still slices off the "hit me" arm by its position.
# A head or a face put into a hard thing is an assault, and the person names the object rather
# than "me": `he pushed my head into the door frame`, `he shoved my face into the wall`,
# `he banged my head against the door`. All three were a shrug or a bumped-head card. The person
# has to be in front of it, so `i banged my head on the door frame` (an accident) and
# `my son banged his head on the table` (a child, his own head) keep the bumped-head card, and
# nothing soft is in the list, so `he pushed my face into the cake` stays ordinary.
ABUSE_HEAD_INTO = (
    r"\b(?:he|she|they|hubby|my\s+" + ABUSER + r")\b[^.?!]{0,20}"
    r"\b(?:push(?:ed|es|ing)?|shov(?:ed|es|ing)|slam(?:med|s)?|bang(?:ed|s|ing)?|"
    r"smash(?:ed|es|ing)?|knock(?:ed|s|ing)?|ram(?:med|s|ming)?|thr(?:ew|ows|owing)|"
    r"yank(?:ed|s|ing)?|drag(?:ged|s|ging)?|smack(?:ed|s|ing)?|press(?:ed|es|ing)?)\b"
    r"[^.?!]{0,15}\bmy\s+(?:head|face)\b[^.?!]{0,15}"
    r"\b(?:into|onto|against|off|through)\b\s*(?:the\s+|a\s+|his\s+|her\s+)?"
    r"(?:wall|walls|door|doors|door\s?frame|doorframe|frame|floor|ground|table|table\s?top|"
    r"desk|worktop|counter|cupboard|cabinet|fridge|freezer|radiator|banister|stairs|"
    r"stair\s?gate|step|kerb|curb|pavement|window|windowsill|sill|sink|bath|bathroom|toilet|"
    r"headboard|bed\s?frame|wardrobe|shelf|shelves|cooker|oven|dashboard|car|van|"
    r"kitchen\s?unit|brick\s?wall|concrete)\b"
)

# A face put into something soft is a mess before it is a blow, and it needs an answer of its
# own rather than the fall-through. The card is wrong, but so is the baking card that took four
# "birthday cake" lines when the card simply stood down, and a shrug is the echo STYLE.md rejects.
# So this shape gets a short, warm reply that asks whether it was a laugh - which is the one thing
# that decides whether it wants a friend or something more.
SOFT_FACE_PUSH = (
    r"\b(?:he|she|they|hubby|my\s+" + ABUSER + r")\b[^.?!]{0,20}"
    r"\b(?:push(?:ed|es|ing)?|shov(?:ed|es|ing)|slam(?:med|s)?|bang(?:ed|s|ing)?|"
    r"smash(?:ed|es|ing)?|ram(?:med|s|ming)?|thr(?:ew|ows|owing)|dunk(?:ed|s|ing)?)\b"
    r"[^.?!]{0,15}\bmy\s+(?:face|head)\b[^.?!]{0,15}"
    r"\b(?:into|onto|in|through)\b\s*"
    r"(?:(?:the|a|his|her|my|their)\s+)?(?:\w+\s+){0,2}"
    r"(?:cake|cakes|snow|mud|sand|dough|flour|icing|bubbles|foam|paint|slime)\b"
)
SOFT_FACE_STOP = (
    # a blow, a hold, or trouble breathing in the same line is not play
    r"\b(?:hit|hits|hitting|punch(?:ed|es|ing)?|kick(?:ed|es|ing)?|slap(?:ped|s|ping)?|"
    r"beat(?:s|en)?|chok(?:ed|es|ing)?|shov(?:ed|es)?\s+me|push(?:ed|es)?\s+me|"
    r"held\s+me|hold(?:ing)?\s+me|kept\s+me|held\s+it|pinned)\b",
    r"\b(?:can'?t|couldn'?t|could\s+not|cannot|unable\s+to|struggl\w*\s+to)\s+breath\w*\b",
    r"\b(?:gasping|choking|unconscious|blue\s+in\s+the\s+face)\b",
)
PLAY_FACE_REPLIES = (
    "A proper mess. Were you both laughing, or did it land badly?",
    "Ha - somebody got you. Was it a laugh, or did that land badly?",
    "That's the classic. Were you both laughing, or did it not feel funny to you?",
)

ABUSE = ABUSE + PURSUIT + ABUSE_VERBAL + (ABUSE_HEAD_INTO,)
# A violent thing said in the same line outranks the handover.
ABUSE_PURSUIT_HARD = (
    r"\b" + ABUSE_VERB + r"\s+(?:me|us)\b",
) + PURSUIT_FEAR + (
    r"\b(?:drunk|threatening|hit|hitting|kicked|pushed|grabbed)\b",
    r"\b(?:won'?t|wont|refuses?)\s+(?:leave|go|let)\b",
)
# The speaker as the object of the harm, said in the past: the sentence a person types when they
# are telling you about something that was done to them. The abuse arm below reacts to it as it
# would to the present tense, which is right for "i was abused" on its own, but "i was abused when
# i was little" and "i was raped years ago" never reached it at all: the time words stopped them at
# the old-story guard, which is what turns away "i had a bleed when i was pregnant last year", and
# the line came back a shrug. Both of those need a different reply and neither needs an ambulance.
ABUSE_DISCLOSURE = (
    r"\b(?:i|we)\s+(?:was|were|have\s+been|'ve\s+been|had\s+been)\s+(?:being\s+|getting\s+)?"
    r"(?:abused|assaulted|raped|molested|groomed|stalked|harassed|threatened|beaten|hit|"
    r"attacked|choked|strangled)\b",
    r"\b(?:i|we)\s+(?:was|were)\s+in\s+an?\s+(?:abusive|violent)\s+(?:relationship|marriage|home)\b",
    r"\b(?:i|we)\s+used\s+to\s+be\s+(?:beaten|hit|abused|assaulted)\b",
)
# ...unless the harm word is really a job or a tenancy: "i was threatened with the sack", "i was
# threatened with redundancy", "i was threatened with eviction" are a bad week, and the tenancy
# one has its own answer. The object decides it, as it does in _NOT_A_THREAT.
ABUSE_DISCLOSURE_FINE = (
    r"\bthreatened\s+(?:with|over|about)\s+(?:a\s+|the\s+|his\s+|her\s+|their\s+|my\s+|"
    r"our\s+)?(?:being\s+)?(?:written\s+)?(?:warning|fine|fines|eviction|legal|lawsuit|court|"
    r"police|report|complaint|solicitor|letter|bills?|charges?|prosecution|dismissal|sack|"
    r"sack(?:ing|ed)|redundancy|redundant|fired|firing|disciplinary|hearing|notice|tenancy|"
    r"deposit)\b",
)
# A memory of being hurt is not a live threat, and the emergency line is for the thing happening
# now: "i was abused as a child", "i was harassed at my old job", "i was abused growing up" were
# all getting "get a real person involved: 999 or 911". The time words below say the harm is over,
# and ABUSE_NOW takes the card back when the same line says it is still going on.
ABUSE_MEMORY = (
    r"\bas\s+a\s+(?:child|kid|baby|boy|girl|teenager|teen|little\s+(?:boy|girl|kid|one))\b",
    r"\bgrowing\s+up\b", r"\bin\s+my\s+(?:childhood|teens|twenties|thirties)\b",
    r"\bwhen\s+i\s+was\s+(?:a\s+(?:child|kid|baby|teenager|little\s+\w+)|young|little|small|"
    r"at\s+school|in\s+school|at\s+college|at\s+university)\b",
    r"\bat\s+(?:school|primary|secondary|college|university)\b",
    r"\bat\s+my\s+(?:old|previous|last|former)\s+(?:job|work|school|house|flat)\b",
    r"\byears\s+and\s+years\s+ago\b", r"\byears\s+ago\b", r"\bages\s+ago\b",
    r"\bdecades?\s+ago\b", r"\ba\s+long\s+(?:time|while)\s+ago\b",
    r"\bback\s+(?:then|in\s+(?:the\s+)?(?:\d0s|\d{4}))\b", r"\bin\s+the\s+\d0s\b",
    r"\bused\s+to\b", r"\bmy\s+(?:childhood|past)\b",
)
# Only the words that say the harm is happening again, and a verb has to follow them: a bare
# "still" is the memory talking ("i was abused as a child and i still have nightmares", "but hes
# dead now"), and a memory with a nightmare in it is still the past.
ABUSE_NOW = (
    r"\b(?:still|now|again)\s+(?:\w+\s+){0,2}(?:does|doing|hits?|hurts?\s+me|beats?|"
    r"threatens?|follows?|watches?|comes?|turns?\s+up|shows?\s+up|calls?|texts?|happens?|"
    r"happening|at\s+it)\b",
    r"\b(?:keeps?\s+(?:doing|on|at)|hasn'?t\s+stopped|never\s+stopped|carries\s+on)\b",
    r"\b(?:it|this|he|she)\s*(?:'s|s|\s+is)?\s*(?:happening|going\s+on|happened)\s+again\b",
    r"\bat\s+it\s+again\b",
    r"\b(?:every|each)\s+(?:day|night|morning|week|evening)\b",
    r"\b(?:nowadays|these\s+days)\b",
    r"\b(?:tonight|yesterday|last\s+night|this\s+(?:morning|week))\b",
)
# The same words, said about something harmless: a game of rugby, a party, a shoulder rub, a
# pushchair. These keep the ordinary reply.
# The solid things a person is hit with, for the one check that has no verb to notice: a figure of
# speech and then a second object with nothing between them but "and" ("he hit me with a joke and
# a bottle", "she hit me with a joke and then with her hand"). It is a list of things that hurt
# rather than "anything not on the harmless list", so a joke and a smile stays a joke.
BLOW_THINGS = (r"(?:bottles?|glasses?|pans?|frying\s+pans?|saucepans?|bats?|baseball\s+bats?|"
               r"belts?|belt\s+buckles?|chairs?|stools?|cups?|mugs?|plates?|bowls?|knife|knives|"
               r"sticks?|canes?|hammers?|bricks?|stones?|rocks?|remotes?|remote\s+controls?|"
               r"shoes?|boots?|slippers?|trainers?|books?|newspapers?|candlesticks?|spanners?|"
               r"wrenches?|wires?|cables?|cords?|pipes?|rods?|bars?|iron\s+bars?|"
               r"rolling\s+pins?|ladles?|spoons?|wooden\s+spoons?|forks?|pokers?|torches?|"
               r"phones?|lamps?|vases?|ashtrays?|tools?|hands?|fists?|feet|foot|elbows?|knees?|"
               r"shoulders?)")

# What a blow can be struck with and still be a joke. It is the *thing* being soft that makes the
# head card wrong ("he hit my head with a pillow"), and it is the thing being named in a game that
# makes the whole disclosure wrong ("we were mucking about and he threw a sponge at me"). Both of
# those read this one list, so a new soft thing is added in one place.
SOFT_HIT_THING = (
    r"(?:pillow|cushion|duvet|blanket|quilt|snowball(?:s)?|ball(?:s)?|beach\s+ball|"
    r"plastic\s+ball|tennis\s+ball|frisbee|sponge|flannel|tea\s+towel|towel|"
    r"newspaper|magazine|paper|roll?ed[\s-]?up\s+(?:paper|newspaper|magazine|towel)|"
    r"water\s?bomb|water\s?balloon|water\s+pistol|sock|slipper|plush\s+toy|teddy|toy|"
    r"stickle\s?brick|lego|balloon|cushion\s+case)"
)
# A game that is named as a game: the activity itself, or a subject that includes the speaker
# ("we were playing", "we both laughed"). It is deliberately NOT a feeling word. A bare "joke",
# "laugh", "kids" or "mates" anywhere in the line is how a blow gets minimised or watched, and
# standing the card down on those answers "he hit me with a cushion and then said he was only
# joking" with a comfort line (steward-garnet-axe, #steward 88199).
PLAY_NAMED = (
    r"(?:pillow\s+fight|snowball\s+fight|water\s+fight|food\s+fight|play\s?fight\w*|"
    r"nerf\s+(?:gun|war|fight)|paintball|tickl\w+|"
    r"muck(?:ing)?\s+(?:about|around)|mess(?:ing)?\s+(?:about|around)|"
    r"fool(?:ing)?\s+(?:about|around)|lark(?:ing)?\s+(?:about|around)|"
    r"jok(?:ing|e)\s+(?:about|around)|banter|"
    r"we\s+(?:were|was|are)\s+(?:only\s+|just\s+)?"
    r"(?:playing|mucking|messing|fooling|larking|joking|having\s+a\s+laugh)|"
    r"we\s+both\s+(?:laughed|were\s+laughing|laugh)|we\s+were\s+laughing|"
    r"playing\s+(?:catch|football|rounders|netball|basketball|tag|a\s+game|games|together))"
)
# The verb a soft thing comes at you with, in either order: "he hit me with a pillow",
# "he threw a cushion at me".
SOFT_HIT_VERB = (
    r"(?:hit|hits|hitting|slapped|slaps|smacked|whacked|pelted|threw|throws|thrown|"
    r"sprayed|squirted|flicked|dunked|dumped|doused)"
)

ABUSE_FINE = (
    # Losing is not being hit: "my dad beats me at chess" and "he beats me at pool every friday"
    # are a game, and the board, the cards and the console are the whole of it. The game has to be
    # named in the same line, so "he beats me every time he comes round" still keeps the card.
    r"\bbeat(?:s|en|ing)?\s+(?:me|us)\s+(?:at|in)\s+(?:chess|cards|poker|pool|snooker|billiards|"
    r"darts|tennis|badminton|table\s+tennis|ping\s?pong|squash|golf|football|rugby|cricket|"
    r"basketball|netball|scrabble|monopoly|cluedo|checkers|draughts|dominoes|mario\s?kart|"
    r"video\s+games?|the\s+quiz|the\s+game|the\s+final|the\s+match|the\s+league|"
    r"arm\s?wrestl\w*)\b",
    # The games that are not in that list - fifa, fortnite, the pool table, the bowling - and
    # the ask that is not a blow at all.
    GAME_PLAYED,
    r"\bhit(?:s|ting)?\s+(?:me|us)\s+up\s+(?:for|to)\b",
    # A corner at a party is a conversation, not an exit being blocked: "my friend had me
    # cornered at the party to talk about work", "my mate had me cornered at the pub all
    # evening". The social place and the talk are both in the pattern, so a hallway or a
    # kitchen keeps the card.
    r"\b(?:had|has|have|got|gets|kept|keeps)\s+me\s+cornered\s+(?:at|during|after)\s+(?:the\s+|"
    r"a\s+|his\s+|her\s+)?(?:party|pub|wedding|conference|meeting|office|work|do|dinner|"
    r"reception|barbecue|bbq|gig|match|networking\s+event)\b",
    r"\bcornered?\s+me\s+(?:to\s+(?:talk|ask|discuss|pitch|sell|persuade|convince|apologise|"
    r"apologize)|at\s+(?:the\s+|a\s+)?(?:party|pub|wedding|conference|meeting|office|work|do))\b",
    # A parent refusing a night out is parenting, and a landlord refusing an early exit from a
    # tenancy is a contract: "my mum wont let me go to the party", "my landlord wont let me leave
    # my tenancy early". A partner doing it keeps the card, which is why the subject is what
    # stands these down.
    r"\bmy\s+(?:mum|mom|mam|dad|mother|father|parents?|nan|nana|grandad|grandma)\b[^.?!]{0,25}"
    r"\b(?:let|allow)\s+me\s+(?:go|out|stay|leave)\b",
    r"\b(?:landlord|landlady|letting\s+agent|agent|council|employer|boss|manager|company|firm|"
    r"university|college|school|gym)\b[^.?!]{0,30}\b(?:let|allow)\s+me\s+"
    r"(?:leave|go|out|past)\b",
    # A threat over money, a rota or the rent is a dispute, so who is making it decides it:
    # "my boss is threatening me over my hours" and "the landlord is threatening me over the
    # rent" are letters and rotas, while a partner or an ex threatening over money is the case
    # the pool below is for. Only the counterparties below stand the case down, so the money
    # words stay in the pattern instead of in _NOT_A_THREAT.
    # A company chasing a bill says "we will take this further" and calls it a threat; the
    # emergency line is not where a debt letter belongs, whatever object the threat takes.
    r"\b(?:debt\s+collector|debt\s+collectors|bailiffs?|bank|mortgage|lender|utility|"
    r"utilities|energy|water\s+company|broadband|phone\s+company|insurer|insurance|"
    r"hmrc|tax\s+office|dvla)\b[^.?!]{0,40}\bthreaten(?:s|ed|ing)?\s+(?:me|us)\b",
    r"\b(?:landlord|letting\s+agent|agent|council|housing|bank|mortgage|utility|utilities|"
    r"energy|water\s+company|broadband|phone\s+company|mobile\s+network|insurer|insurance|"
    r"employer|boss|manager|company|firm|agency|payroll|hr\b|hmrc|tax\s+office|dvla|"
    r"university|college|school|gym|debt\s+collector|solicitor)\b[^.?!]{0,40}"
    r"\bthreaten(?:s|ed|ing)?\b[^.?!]{0,25}\b(?:over|about|with)\s+"
    r"(?:a\s+|the\s+|his\s+|her\s+|their\s+|my\s+|our\s+)?(?:money|pay|wages|salary|rent|"
    r"hours|shifts?|rota|arrears|fees?|charges?|debt|bills?)\b",
    # "i am being hit on by a guy at work" is flirting and "i was hit with a huge bill" is a bill;
    # neither has a `by` for the person guard to look at, so they stand down by their own words.
    r"\bhit\s+(?:on|with)\b",
    # "i feel like im being watched" is the anxiety shape as often as the stalking one.
    r"\bfeel(?:s|ing)?\s+like\s+(?:i\s*(?:'m|am)|im)\s+being\s+watched\b",
    # Harassment at work has its own answer on main and it is the right one: write it down while
    # it is fresh, then who to take it to. "get somewhere safe, 999" is not the reply to that.
    r"\bharass(?:ed|es|ing|ment)\b[^.?!]{0,30}\b(?:at|from)\s+(?:work|the\s+office|my\s+job)\b",
    # "...hit me with a snowball" was the 999 card: the body-part guard stopped at "me" as well as
    # at "my". Only a body part in front of the playful thing is a hit; "me with" is the thing.
    r"\b(?:thr(?:ew|ows)|push(?:ed|es)|shov(?:ed|es)|kick(?:ed|s)?|hit|hits|slapped)\b"
    r"(?!\s+(?:my|his|her|their)\b)(?!\s+me\s+(?:in|on|round|across)\b)[^.?!]{0,20}\b(?:ball|snowball|"
    r"frisbee|water\s+balloon|pillow|toy|party|surprise|birthday|early\s+night|hint|look)\b",
    r"\b(?:push(?:ed|es)|shov(?:ed|es)|thr(?:ew|ows))\s+me\s+(?:into|in)\s+the\s+"
    r"(?:pool|water|sea|lake|river|snow|leaves)\b",
    r"\b(?:push(?:ed|es)|shov(?:ed|es))\s+me\s+(?:in|on)\s+the\s+(?:buggy|pushchair|wheelchair|"
    r"swing|sledge|sled|trolley|bike|boat)\b",
    r"\b(?:my|his|her)\s+(?:sister|brother|friend|mate|son|daughter|kids?)\s+(?:hit|hits|punched|"
    r"pushed|kicked|slapped)\s+me\s+(?:at|during|in)\s+(?:rugby|football|the\s+match|training|"
    r"practice|a\s+game|the\s+game|playtime|the\s+pool)\b",
    # A child on the other side of a bathroom door is a child, not somebody holding you in it:
    # "i am locked in the bathroom and my toddler is banging on the door".
    r"\bmy\s+(?:son|daughter|child|children|kid|kids|baby|babies|toddler|nephew|niece|"
    r"grandson|granddaughter)\b[^.?!]{0,40}\b(?:bang(?:ing|s)?|pound(?:ing|s)?|kick(?:ing|s)?|"
    r"hammer(?:ing|s)?|shout(?:ing|s)?)\b",
    # A small child who climbs on you has you pinned, and that is a game, not an assault: the
    # child is the subject and "pinned" is the wrestling word. A grown-up son or daughter doing it
    # still counts, so for those two words only "pinned" is stood down, and "trapped" or
    # "cornered" stays whatever it is.
    r"\bmy\s+(?:son|daughter|niece|nephew|godson|goddaughter)\b[^.?!]{0,25}\b"
    r"(?:(?:has|have|had|got|keeps?|kept)\s+me\s+pinned|pinned\s+me|wrestl(?:ed|es|ing)\s+me)\b",
    # "my toddler has me trapped in the kitchen" is how parents describe a morning, so the young
    # words stand the whole restraint down.
    r"\bmy\s+(?:kid|kids|child|children|toddler|baby|babies|newborn)\b[^.?!]{0,25}\b"
    r"(?:(?:has|have|had|got|keeps?|kept)\s+me\s+(?:pinned|trapped|stuck)|"
    r"(?:pinned|trapped|wrestl(?:ed|es|ing))\s+me)\b",
    # A hand on your arm to stop you falling, to hug you, to shake it hello: the grip is help.
    r"\b(?:grab(?:bed|s)?|held|took)\b[^.?!]{0,25}\bto\s+(?:hug|kiss|say|shake|stop|help|save|"
    r"pull\s+me\s+up|hold|steady|catch|guide|lead|thank|greet|calm)\b",
    r"\b(?:as\s+(?:i|he|she)\s+(?:fell|slipped))\b",
    # "hit me with the next deadline" is a figure of speech, not a blow, and so is "he hit me
    # with a joke". What says which it is, is the thing after "with": a person is hit with a solid
    # thing, and the classes below are the things nobody is hit with - something said, a piece of
    # information, an idea, a demand for money or a date in the diary. A bat, a glass, a bottle, a
    # belt or a fist is in none of them, so a real blow keeps the card. One adjective is allowed,
    # so "a good line" and "a rubbish joke" are in it too.
    # ...and a line you are hit with can be a rope: "he hit me with the washing line", "the
    # clothes line", "a fishing line", "a clothesline". The figure of speech is the line somebody
    # says, so the rope compounds stand the rule down before the article is allowed to be read as
    # the start of the phrase.
    r"\bhit(?:s|ting)?\s+me\s+with\s+"
    r"(?!(?:(?:the|a|an|my|his|her|their|this|that)\s+)?(?:washing|clothes|clothesline|fishing|"
    r"tow|washing-up|party|garden|climbing)\s*-?\s*line\b)"
    r"(?:(?:the|a|an|this|that|his|her|their)\s+)?"
    r"(?:[\w'-]+\s+){0,2}(?:next\s+)?(?:deadline|deadlines|bill|bills|news|invoice|invoices|fine|tax|taxes|work|"
    r"project|projects|question|questions|idea|ideas|surprise|party|joke|jokes|pun|punchline|"
    r"line|lines|quote|quotes|fact|facts|truth|hint|warning|newsflash|update|updates|headline|"
    r"headlines|statistic|statistics|stats|figure|figures|number|numbers|story|stories|riddle|"
    r"suggestion|suggestions|advice|compliment|compliments|argument|excuse|excuses|ultimatum|"
    r"guilt\s+trip|lecture|earful|mouthful|reality\s+check|curveball|revelation|rumour|rumor|"
    r"gossip|opinion|promise|invite|invitation|letter|email|text|phone\s+call)\b"
    # "a number of punches" is not arithmetic: a counting word in front of the blows is a beating,
    # and the noun list must not stand it down as a "number".
    r"(?!\s+of\s+(?:punches|blows|kicks|hits|slaps|thumps|digs|jabs|beatings|whacks|wallops|"
    r"shots|smacks|strikes|knocks)\b)"
    # ...but only the word itself: "letter" begins "letter opener", "story" begins "story book",
    # "number" begins "number plate", and those are the solid things people really are hit with.
    # So the matched word may not be followed by the word that turns it into an object.
    r"(?!\s+(?:opener|book|books|plate|plates|sheet|sheets|skate|skates|prop|props|"
    r"board|boards|rack|stand|clip|gun|punch|hole|weight|pin|block|cutter|knife|bat|pad|bag|"
    r"cover|holder|rest|frame|case|box|bag|handle|head|piece|booklet|boards?)\b)"
    # ...and the figure of speech stands down only when nothing else in the line is a blow: "he hit
    # me with a joke and then he hit me" is a joke and a beating, and the beating is the half to
    # answer. Two ways a blow comes after the figure: the same object in a second clause, which
    # reaches back through the whole phrase, and a blow that keeps happening.
    r"(?!(?:[^.?!]{0,40})\b(?:and|then|but|so)\b[^.?!]{0,30}"
    r"(?:hit|hits|hitting|punched|punching|slapped|slapping|kicked|kicking|shoved|shoving|"
    r"pushed|pushing|grabbed|grabbing|choked|choking|strangled|beat|beating|thumped|whacked|"
    r"headbutted|pinned|dragged|smashed)\s+(?:me|my|us)\b(?!\s+(?:with|by)\b))"
    r"(?![^.?!]{0,40}\b(?:keeps?|kept)\s+(?:on\s+)?(?:hitting|punching|slapping|kicking|"
    r"shoving|pushing|grabbing|choking|beating|thumping|whacking)\s+(?:me|my|us)\b)"
    # ...and the third way, which has no verb to notice: a second thing after the figure of
    # speech, with nothing between them but "and" - "he hit me with a joke and a bottle",
    # "she hit me with a joke and then with her hand". The harmless word still has to name
    # something harmless after it, so the check is the solid things people are hit with and
    # not "anything that is not on the harmless list": a joke and a smile stays a joke, and
    # a cup of tea, or a hand on your shoulder, is comfort rather than a blow.
    r"(?![^.?!]{0,30}\b(?:and|then|or|but)\b[\s,]+(?:(?:then|also|with|by)\s+)?"
    r"(?:(?:a|an|the|his|her|their|my|our)\s+)?" + BLOW_THINGS +
    r"\b(?!\s+(?:of|on|round|around|to)\b))",
    # A bailiff or a debt collector who is threatening you is a money problem with a helpline of
    # its own, not the domestic abuse card: `money.bailiff` answers those lines and this card
    # must not take them. Only the two agents that entry answers are named here - a creditor or
    # "the council tax people" has no answer behind them, and standing the card down there left
    # `the council tax people are threatening me` with `Thanks for telling me`. Loan sharks and
    # money threats over a debt are stood down below.
    r"\b(?:bailiffs?|debt\s+collectors?)\b[^.?!]{0,40}"
    r"\bthreaten(?:s|ed|ing)?\b",
    # Said out loud as play, it is play: "my mum hit me on the arm playfully".
    r"\b(?:playfully|jokingly|in\s+play|for\s+fun|messing\s+about|playfight\w*|larking\s+about|"
    r"tickl\w+)\b",
    # ...and the same said with another spelling of it. "mucking about", "fooling about" and
    # "larking about" are the same claim as "messing about", and only the last one was listed, so
    # "we were mucking about and he threw a sponge at me" kept the 999 card.
    r"\b(?:muck(?:ing)?\s+(?:about|around)|mess(?:ing)?\s+(?:about|around)|"
    r"fool(?:ing)?\s+(?:about|around)|lark(?:ing)?\s+(?:about|around)|"
    r"jok(?:ing|e)\s+(?:about|around)|muck(?:ing)?\s+around)\b",
    # A head or a face hit with a soft thing is a bumped head, not a disclosure. "he hit my head
    # with a pillow", "he hit my head with a frisbee", "he hit my head with a ball" and "he hit my
    # face with a snowball" all took the 999 card, and the bumped-head card answers every one of
    # them. It is the two of them together that is the rule - a part of the body and a soft thing -
    # so a hard thing keeps the card ("with a brick", "with a bottle"), and so does a part that is
    # not the head ("he hit my nose with a ball" is a nosebleed, "he hit my arm with a ball" is a
    # bruise), because the answers behind the card are better than a card nobody meant.
    r"\b" + SOFT_HIT_VERB + r"\b[^.?!]{0,24}\b(?:my|the|his|her|your)\s+(?:head|face)\b"
    r"[^.?!]{0,24}\bwith\s+(?:a\s+|an\s+|the\s+|some\s+)?" + SOFT_HIT_THING + r"\b",
    # The game named in the line is the game, whatever was in the air during it: a pillow fight is
    # not in the list above, so "we had a pillow fight and he hit me with a cushion" and "he hit me
    # with a cushion, the kids were having a pillow fight" kept the card. Named either side of the
    # blow, and the thing named before the person it hit.
    r"\b" + SOFT_HIT_VERB + r"\b[^.?!]{0,40}\bwith\s+(?:a\s+|an\s+|the\s+|some\s+)?"
    + SOFT_HIT_THING + r"\b[^.?!]{0,60}" + PLAY_NAMED + r"\b",
    r"\b" + PLAY_NAMED + r"\b[^.?!]{0,60}\b" + SOFT_HIT_VERB + r"\b[^.?!]{0,40}\bwith\s+"
    r"(?:a\s+|an\s+|the\s+|some\s+)?" + SOFT_HIT_THING + r"\b",
    r"\b" + PLAY_NAMED + r"\b[^.?!]{0,60}\b(?:threw|throw|thrown|throws|pelted|sprayed|"
    r"squirted)\b[^.?!]{0,20}\b" + SOFT_HIT_THING + r"\s+at\s+(?:me|us)\b",
    # An illegal lender threatening someone is intimidation over money, not domestic abuse: the
    # loan-shark answer owns that line, and it names 999 as well, so nothing is lost. The lender
    # arm is LENDER_FINE below and not one of these, because a line can name a partner as well
    # ("my partner hit me over the money i owe a loan shark") and that person keeps the card.
    # A small child who bites or lashes out is a toddler with no words yet, not an abuser: the
    # biting and hitting answers belong to that, and `my daughter bit me today` was landing on the
    # abuse card. A grown-up son or a grandmother doing it still counts.
    r"\bmy\s+(?:son|daughter|child|kid|baby|toddler|boy|girl|children|stepson|stepdaughter|"
    r"grandson|granddaughter|nephew|niece|little\s+one)\b[^.?!]{0,30}"
    r"\b(?:bit|bite|bites|biting)\s+me\b",
    r"\bmy\s+(?:baby|toddler|child|kid|little\s+one|newborn|infant|two\s+year\s+old|"
    r"three\s+year\s+old)\b[^.?!]{0,30}"
    r"\b(?:hit|hits|hitting|kicked|kicks|kicking|slapped|slaps|slapping|pinched|pinches|pinching|"
    r"scratched|scratches|scratching|pushed|pushes|shoved|shoves|headbutted|headbutts)\s+me\b",
    # A threat over money is a debt problem, not domestic abuse. The loan-shark answer carries
    # the 999 line; a workplace threat belongs to the bullying answer. A partner threatening
    # someone over money still gets the abuse card, so only these outside subjects stand down.
    r"\b(?:they|someone)\s+(?:are|is|was|were)?\s*(?:threatening|threatened)\s+me\b"
    r"[^.?!]{0,30}\b(?:debt|debts|money|loan|loans|repayment|repayments|bill|bills)\b",
    # A threat to hurt or kill is an emergency whoever says it, so the workplace stand-down
    # applies only while the threat stays non-violent.
    r"\b(?:boss|manager|colleague|coworker|co-worker|supervisor)\b[^.?!]{0,30}\bthreaten"
    r"(?![^.?!]{0,60}\b(?:kill|kills|killing|murder|hurt|hurts|harm|attack|stab|shoot|"
    r"strangle|choke|rape|beat|punch|hit|slap|grab|shove|push|throat|weapon|knife|gun)\b)",
    r"\bthreaten(?![^.?!]{0,60}\b(?:kill|kills|killing|murder|hurt|hurts|harm|attack|stab|"
    r"shoot|strangle|choke|rape|beat|punch|hit|slap|grab|shove|push|throat|weapon|knife|gun)\b)"
    r"[^.?!]{0,30}\b(?:boss|manager|colleague|coworker|co-worker|supervisor)\b",
    # Horseplay with the family lands on the sofa: "my kids pushed me onto the sofa", "my sister
    # A crowd, not a hand on you: "my friend held me against the wall to let the ambulance past".
    r"\b(?:held|pulled|pushed|shoved)\s+(?:me|us)\s+(?:against|to|back\s+against)\s+(?:the\s+)?"
    r"(?:wall|fence|barrier|side|back)\b[^.?!]{0,25}\b(?:to\s+let|so\s+they|so\s+the|"
    r"to\s+make\s+room|to\s+get\s+out\s+of\s+the\s+way)\b",
    # An owner's animal is the one that bit, not the owner, and a person who attacked the speaker
    # as well keeps the card: the two arms for that are in ABUSE_FINE_ANIMAL below.
)
