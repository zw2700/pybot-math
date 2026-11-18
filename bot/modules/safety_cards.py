"""Text and pattern tables that only `safety.py` reads.

`bot/modules/safety.py` is at the 1 MiB file limit the Hub puts on one file, and this is
the cheapest room to make: these are literal tables with no reference to anything else
in the module, so they move without changing a single reply. `safety.py` imports them
back, and every name is still reachable as `safety.<NAME>`.
"""

BITE_DONE = (
    r"\b(?:dog|dogs|puppy)\b\s+(?:has\s+|had\s+|'s\s+|just\s+)?(?:bit|bitten|nipped)\s+"
    r"(?:me|him|her|them|my|his|their)\b",
    r"\b(?:dogs?|puppy)\b.{0,25}\b(?:bit\s+(?:me|him|her|them|my|his|their|a|the)|bitten|nipped|"
    r"snapped\s+at|went\s+for)\b.{0,30}"
    r"\b(?:me|my|his|her|their|the\s+(?:child|kid|baby)|a\s+(?:child|kid|baby))\b",
    r"\b(?:bitten|nipped|bit\s+(?:me|my|him|her|them))\b.{0,25}\b(?:by\s+a\s+dog|dog|puppy)\b",
    r"\b(?:bitten|bit\s+(?:me|my|him|her|them))\b.{0,20}\b(?:face|cheek|lip|hand|finger|arm|leg|ankle)\b",
    # ...and the bite that broke the skin, with no body part named: "my son bit me and it bled",
    # "my daughter bit me and left marks". The wound is the question there and the answer for it is
    # the first aid. A small child's teeth break a parent's skin all the time, and without this arm
    # those lines reached no bite card at all, so the only thing left to answer them was the abuse
    # card's 999 - while "my toddler bit my arm and it bled" got the first aid, because "my arm" is
    # in the arm above. It is not only a child who does it, so this arm reads the teeth and the
    # wound and leaves whose they are to the words around them.
    r"\b(?:bit|bites?|bitten|nipped)\s+"
    r"(?:me|my\s+(?:hand|hands|finger|fingers|thumb|wrist|arm|arms|leg|legs|foot|feet|toe|toes|"
    r"face|cheek|nose|ear|lip|shoulder|chest|belly|back|head|neck|skin))\b[^.?!]{0,30}"
    r"\b(?:bled|bleeds?|bleeding|blood|bloody|broke\s+(?:the|my)\s+skin|broke\s+skin|"
    r"marks?|drew\s+blood|draw\s+blood|drawn\s+blood|infected|needs?\s+stitches|"
    r"wont\s+stop\s+bleeding|won't\s+stop\s+bleeding)\b",
    # The passive turn of the same bite: "i was bitten by my cat", "my hand was bitten by a cat".
    # A cat bite on a hand is one of the few everyday lines that wants a same-day answer, and the
    # arms above are all written from the dog's side of the sentence. The subject has to be the
    # speaker or a body part, so "my cat was bitten by a dog" stays the vet's (BITE_ON_ANIMAL).
    # A dog that went for the person: "the neighbours dog attacked me", "a dog savaged my hand".
    # The subject is the person again, so the same rule holds - the vet's answer is for the pet
    # that was attacked, and this one is for the body that was.
    r"\b(?:dog|dogs|puppy|puppies|cat|cats|kitten|kittens|pet|pets|horse|pony|rabbit|hamster|"
    r"parrot|budgie|ferret|gerbil)\b[^.?!]{0,30}\b(?:attacked|savaged|mauled|set\s+about|"
    r"went\s+for|went\s+at|lurched\s+at|turned\s+on)\s+"
    r"(?:me|him|her|them|us)\b",
    # ... and the body part version, where "my slippers" must not count as a person:
    r"\b(?:dog|dogs|puppy|puppies|cat|cats|kitten|kittens|pet|pets|horse|pony|rabbit)\b"
    r"[^.?!]{0,20}\b(?:attacked|savaged|mauled|went\s+for|went\s+at|turned\s+on)\s+"
    r"(?:my|his|her|their|our)\s+(?:hand|hands|finger|fingers|thumb|arm|arms|leg|legs|foot|"
    r"feet|face|cheek|lip|ankle|head|neck|shoulder|ear|ears|nose|eye|wrist|toe|toes|thigh|"
    r"shin|knee|stomach|back)\b",
    r"\b(?:i|we)\b[^.?!]{0,15}\b(?:was|were|got|have\s+been|has\s+been|had\s+been)\s+"
    r"(?:attacked|savaged|mauled)\s+by\b.{0,20}\b(?:dog|dogs|puppy|puppies|cat|cats|kitten|"
    r"kittens|pet|pets|horse|pony|rabbit|hamster|parrot|budgie|ferret|gerbil)\b",
    r"\b(?:i|we)\b[^.?!]{0,15}\b(?:was|were|got|have\s+been|has\s+been|had\s+been)\s+"
    r"(?:bit|bitten|nipped)\s+by\b.{0,20}"
    r"\b(?:dog|dogs|puppy|puppies|cat|cats|kitten|kittens|pet|pets|horse|pony|rabbit|hamster|"
    r"parrot|budgie|ferret)\b",
    r"\b(?:my|his|her|their|our)\s+(?:hand|hands|finger|fingers|thumb|arm|arms|leg|legs|foot|"
    r"feet|face|cheek|lip|ankle|head|neck|shoulder|ear|ears|nose|eye|wrist|toe|toes)\b"
    r"[^.?!]{0,15}\b(?:was|were|got|has\s+been|had\s+been)\s+(?:bit|bitten|nipped)\s+by\b"
    r".{0,20}\b(?:dog|dogs|puppy|puppies|cat|cats|kitten|kittens|pet|pets|horse|pony|rabbit|"
    r"hamster|parrot|budgie|ferret)\b",
    # The bite is over and the wound is the question: "my dog bite got infected", "my dog bite
    # needs stitches", "do i need a tetanus after a dog bite". Every arm above is written around
    # the verb ("bit me", "was bitten"), so the bite as a thing - the noun - missed them all, and
    # the training advice answered a wound: "Stop the biting by changing what happens before it".
    # The pet is named on purpose: a bare "my bite is infected" stays where it was.
    r"\b(?:dog|dogs|cat|cats|puppy|puppies|kitten|kittens|pet|pets|horse)\b[^.?!]{0,15}"
    r"\bbites?\b[^.?!]{0,30}\b(?:infected|infection|septic|pus|ooz\w*|weep\w*|swollen|"
    r"swelling|red|hot|stitches?|tetanus|an?\s*(?:and|&)\s*e|hospital|antibiotics?)\b",
    # ... and the same wound said the other way round, where the bite comes last.
    r"\b(?:infected|septic|oozing|swollen|stitches?|tetanus|antibiotics?)\b[^.?!]{0,25}"
    r"\b(?:dog|cat|puppy|kitten)\s?bites?\b",
    # A tetanus question is about the wound whatever order it comes in.
    r"\btetanus\b[^.?!]{0,30}\b(?:bite|bitten|bit|dog|cat|puppy|kitten|scratch)\b",
)


# The near-miss, bite and reaction cards that came with the a-near-thing and small-hurt work.

ALLERGY_NOW = (
    r"\b(?:i|im|i'?m|we|we'?re|he|she|they|my\s+\w+)\b[^.?!]{0,14}"
    r"\b(?:having|getting|developing|going\s+into)\b[^.?!]{0,20}"
    r"\b(?:allergic\s+reaction|reaction|anaphyla\w*)\b",
    r"\b(?:allergic\s+reaction|reaction)\b[^.?!]{0,14}"
    r"\b(?:right\s+now|now|starting|coming\s+on|just\s+happened)\b",
)


ALLERGY_SIGN_NAMED = (
    r"\b(?:swell\w*|swollen|puff(?:ed|y)?|bloat\w*|lips?|tongue|throat|mouth|face)\b",
    r"\b(?:breath\w*|wheez\w*|stridor|hoarse|croak\w*|voice)\b",
    r"\b(?:dizzy|faint\w*|light\s?headed|collapse\w*|passing\s+out|vomit\w*|throwing\s+up|sick)\b",
    r"\b(?:sting|stung|epipen|injector)\b",
    r"\b(?:hives?|rash\w*|itch\w*|blotch\w*|red\s+spots?|nettle\s+rash)\b",
    # The reaction that has already been and gone is a note, not a call.
    r"\b(?:fine\s+now|was\s+fine|settled|went\s+away|calmed\s+down|last\s+(?:year|week|month)|"
    r"years\s+ago|as\s+a\s+kid|used\s+to|once|back\s+then)\b",
)


# A grater takes a knuckle as often as a knife takes a finger. Main had no verb for it, so "i
# grated my knuckle on the cheese grater" got the listening line.
GRATER_CUT = (
    r"\bgrat(?:e|es|ed|ing)\b[^.?!]{0,24}\b(?:my|his|her|their|the)\s+"
    r"(?:finger|thumb|hand|knuckle|nail|fingertip|palm)",
)


# The near thing that is never said with "killed myself": a bike, a road and a vehicle that did not
# quite hit you. "i nearly got run over on my bike" reached "Sounds alright. Anything good in it?"
# and "i almost went under a bus" reached the drowning card, so the scare needs reading as a scare.
# Only the side being struck is here - "i nearly hit him with my car" is the driver's line - and the
# verb has to be one that says what the vehicle did.
STRUCK_BY_A_VEHICLE = (
    # "nearly got hit by a car", "was almost struck by a van", "nearly run over by a taxi".
    r"\b(?:nearly|almost|close\s+to|came\s+close\s+to|just\s+about)\b[^.?!]{0,20}"
    r"\b(?:(?:got|get|gets|getting|been|be|being|was|were|had)\s+)?"
    r"(?:run\s+over|hit|struck|clipped|swiped|knocked\s+(?:off|down|over))\b[^.?!]{0,16}\b(?:by|"
    r"by\s+a|by\s+the)\b",
    # The verbs that are only ever the vehicle's: nobody is "nearly run over" by a door.
    r"\b(?:nearly|almost|close\s+to|came\s+close\s+to|just\s+about)\b[^.?!]{0,20}"
    r"\b(?:got|get|gets|getting|been|be|being|was|were|had)?\s*"
    r"(?:run\s+over|knocked\s+off|knocked\s+down|knocked\s+over|clipped|swiped|"
    r"rammed|mow(?:ed|n)\b[^.?!]{0,10}\bdown)\b",
    # The vehicle as the subject, with a person on the receiving end: "the bus nearly hit me" is
    # the same scare from the other side, and "the car nearly hit the tree" has nobody on the end
    # of it, so it keeps whatever answer it had.
    r"\b(?:bus|car|lorry|truck|van|tram|train|taxi|cab|motorbike|motorcycle|moped|scooter|bike|"
    r"bicycle|cyclist|driver)\b[^.?!]{0,12}\b(?:nearly|almost)\s+"
    r"(?:hit|missed|struck|clipped|knocked)\s+(?:me|us|him|her|them|my\s+\w+)\b",
    # "almost went under a bus" - under a vehicle, not under water.
    r"\b(?:nearly|almost)\b[^.?!]{0,16}\b(?:went|go|going|gone|fell|ended\s+up)\b[^.?!]{0,14}"
    r"\bunder\s+(?:a|the|an)\s+(?:bus|car|lorry|truck|van|tram|train)\b",
    # The vehicle first and the person as the verb's object - "a lorry almost ran me over",
    # "someone nearly ran me over", "the bus nearly ran us down" - which is how a road scare is
    # usually told, and the one order the patterns above miss ("a bus nearly hit me" was read and
    # "a lorry almost ran me over" was not). Only me and us, so the driver's own line - "i nearly
    # ran him over" - is not read as a scare for the person typing.
    r"\b(?:nearly|almost|close\s+to|just\s+about)\b[^.?!]{0,10}\b(?:ran|run|runs)\s+"
    r"(?:me|us)\s+(?:over|down)\b",
)


# A bike struck by a vehicle is the rider's accident, not a bike to carry: "a car hit my bike this
# morning" and "my bike got clipped by a van" both reached the answer about strapping a bike to
# roof bars, and "a van clipped my bike on the way home" reached "How was it, overall?". The bike
# is the object of the verb in both orders, so the row is the bike and the vehicle. The rider may
# not have been touched, which is why the reply asks that before it says anything else; a person
# struck as well keeps the struck-by-a-vehicle card, which is read before this one.
STRUCK_MY_BIKE = (
    r"\b(?:my|our|his|her|their|the)\s+(?:bike|bicycle|motorbike|motorcycle|scooter|moped)\b"
    r"[^.?!]{0,24}\b(?:got|get|gets|was|were|is|are|been|had\s+been)\s*"
    r"(?:clipped|hit|struck|swiped|knocked|nudged|shunted|rammed|sideswiped)\b"
    r"[^.?!]{0,18}\b(?:van|car|lorry|truck|bus|coach|taxi|cab|tractor|driver)\b",
    r"\b(?:a|an|the|some|one|another)\s+(?:van|car|lorry|truck|bus|coach|taxi|cab|tractor|"
    r"driver)\b[^.?!]{0,16}\b(?:clipped|hit|struck|swiped|knocked|nudged|shunted|rammed|"
    r"sideswiped)\b[^.?!]{0,12}\b(?:my|our|his|her|their|the)\s+(?:bike|bicycle|motorbike|"
    r"motorcycle|scooter|moped)\b",
)


# A road scare is not a shove. "someone nearly hit me at the crossing" and "a man nearly hit me at
# the crossing" came back with the abuse card, which tells the person to get a real person
# involved and ring 999 - for a blow that never landed, on a crossing. The near word and the
# person are not enough on their own, because "he nearly hit me" IS the abuse card's; the road
# place or the vehicle is what makes it the road's, and a person the speaker lives with keeps it
# the abuse card's.
NEAR_HIT_ON_A_ROAD = (
    r"\b(?:nearly|almost|close\s+to|just\s+about)\b[^.?!]{0,12}\b(?:hit|hits|struck|"
    r"ran\s+over|run\s+over|knocked|clipped|caught)\s+(?:me|us)\b",
)
NEAR_HIT_ON_A_ROAD_PLACE = (
    r"\b(?:crossing|zebra|pelican|crossroads|pavement|kerb|curb|road|street|junction|"
    r"roundabout|bollard|cycle\s*lane|bike\s*lane|lay-?by|motorway|dual\s+carriageway|"
    r"bus\s+stop|car\s+park|driveway|level\s+crossing|lights)\b",
)


# Putting yourself in the road is not an accident: "i nearly stepped in front of a train" is a
# person telling you about a wish, and it keeps the answer that line already gets.
STRUCK_BY_A_VEHICLE_NOT = (
    r"\b(?:step(?:ped|ping)?|walk(?:ed|ing)?|jump(?:ed|ing)?|stand(?:ing)?|stood|lay|laid|sat|"
    r"sitting|straddl\w*|leant|leaned)\b",
)


INSECT_BITE_BODY = (
    r"(?:arms?|hands?|fingers?|thumb|legs?|feet|foot|ankles?|wrists?|neck|face|cheek|head|back|"
    r"shoulders?|knees?|elbow|shin|toes?|hip|stomach|belly|ears?|eyes?|chest|forehead|scalp)"
)


# A bite on a hand, a face or over a joint is the wide bite card's: it says to get it seen today,
# and the itch card is a downgrade where a mosquito on the ankle is not ("the spider bit my hand").
INSECT_BITE_NEEDS_A_LOOK = (
    r"\b(?:hands?|wrists?|fingers?|thumb|face|cheek|eyes?|knees?|elbows?|joints?)\b",
)


INSECT_BITE = (
    r"\b(?:mosquito(?:es)?|midges?|gnats?|fleas?|horse\s?fly|horseflies|cleg|spiders?|bed\s?bugs?|"
    r"sand\s?fly|ants?)\b[^.?!]{0,24}\b(?:bit|bitten|bite|nipped|stung?)\b[^.?!]{0,10}"
    r"\b(?:me|him|her|them|us)\b[^.?!]{0,8}\b(?:on|in|under|between)\b[^.?!]{0,8}"
    r"\b(?:the|my|his|her|their|both)\b\s*" + INSECT_BITE_BODY + r"\b",
    r"\b(?:mosquito(?:es)?|midges?|gnats?|fleas?|horse\s?fly|horseflies|cleg|spiders?|bed\s?bugs?|"
    r"ants?)\b[^.?!]{0,24}\b(?:bit|bitten|bite|nipped|stung?)\b\s+"
    r"(?:my|his|her|their)\s+" + INSECT_BITE_BODY + r"\b",
    r"\b(?:i|we)\b[^.?!]{0,15}\b(?:was|were|got|have\s+been|has\s+been|had\s+been)\b[^.?!]{0,10}"
    r"\b(?:bit|bitten|stung)\s+by\s+(?:a|an|the)?\s*(?:mosquito|midge|gnat|flea|ant|spider|"
    r"horse\s?fly)\b[^.?!]{0,10}\b(?:on|in)\b",
)


TICK_BITE = (
    r"\bticks?\b[^.?!]{0,24}\b(?:bit|bitten|bite|on\s+me|on\s+my|attached|dug\s+in|"
    r"burrow\w*|stuck\s+in|in\s+my)\b",
    # The fetching-and-removing lines ("i found a tick on my arm", "i pulled one off the dog")
    # already have an answer that says the same thing, so they are left alone - see TICK_ALREADY.

    r"\b(?:a\s+|the\s+)?tick\s+(?:bite|bites)\b",
    # "i got bitten by a tick", "i was bitten by a tick on saturday" - the shape most people use,
    # and it was reaching the animal-bite card ("Rinse it under the tap for a good five minutes"),
    # which is the wrong advice for a tick: the tweezers and the flat rash are what matter.
    r"\b(?:i|we)\b[^.?!]{0,15}\b(?:was|were|got|have\s+been|has\s+been|had\s+been|might\s+have\s+been)\s+"
    r"(?:bit|bitten)\s+by\s+(?:a|an|the|some)?\s*tick\b",
)


TICK_ALREADY = (r"\b(?:found|pulled|removed|took|got\s+(?:it|one))\b",)


BAT_BITE = (
    r"\b(?:bat|bats)\b[^.?!]{0,24}\b(?:bit|bitten|bite|scratch(?:ed|es)?|claw(?:ed)?|nipped)\b"
    r"[^.?!]{0,24}\b(?:me|him|her|them|us|my|his|her|their)\b",
    r"\b(?:i|we)\b[^.?!]{0,15}\b(?:was|were|got|have\s+been|has\s+been|had\s+been|might\s+have\s+been)\s+"
    r"(?:bit|bitten|nipped|scratched|clawed)\s+by\s+(?:a|an|the)?\s*bat\b",
    # The noun needs a determiner in front, or "i saw a bat bite a man on telly" is a sentence
    # about the bat doing the biting.
    r"\b(?:a|an|the|that|this|my|his|her|their)\s+bat\s+(?:bite|bites|scratch|scratches)\b"
    r"(?!\s+(?:a|an|the|it)\b)",
    # "a bat was in the bedroom and i woke up with marks" is the same question to the helpline.
    r"\bbat\b[^.?!]{0,40}\b(?:woke\s+up\s+with|marks?|a\s+mark|scratch\w*)\b",
)


WILD_BITE = (
    r"\b(?:fox|foxes|badger|badgers|squirrel|squirrels|rat|rats|hedgehog|hedgehogs|mouse|mice|"
    r"deer|otter|weasel|stoat|mole|vole|seagull|gull|swan|goose|geese|crow|magpie|pigeon|"
    r"kestrel|buzzard|owl|tick|ticks|wild\s+animal)\b[^.?!]{0,24}"
    r"\b(?:bit|bitten|bite|nipped|scratched|clawed|went\s+for|attacked)\b[^.?!]{0,20}"
    r"\b(?:me|him|her|them|us|my|his|her|their)\b",
    r"\b(?:i|we)\b[^.?!]{0,15}\b(?:was|were|got|have\s+been|has\s+been|had\s+been)\s+"
    r"(?:bit|bitten|nipped|scratched|clawed)\s+by\s+(?:a|an|the|some)?\s*"
    r"(?:fox|badger|squirrel|rat|hedgehog|mouse|deer|otter|seagull|gull|swan|goose|"
    r"wild\s+animal)\b",
    # The noun, with a determiner in front: "a fox bite", "that rat bite". Without one, "i saw a
    # rat bite a man on telly" is a sentence about the rat doing the biting, not a wound to treat.
    r"\b(?:a|an|the|that|this|my|his|her|their)\s+(?:fox|badger|squirrel|rat|hedgehog)\s+"
    r"(?:bite|bites|scratch)\b(?!\s+(?:a|an|the|it)\b)",
)


COUNTERFACTUAL_WISH = (
    r"\bwis?h\b[^.?!]{0,24}\b(?:i|he|she|they|it|the\s+\w+|that\s+\w+)\b[^.?!]{0,16}"
    r"\b(?:had|have|would\s+have|'d)\b[^.?!]{0,12}"
    r"\b(?:died|been\s+killed|killed\s+me|not\s+survived|never\s+woke\s+up|ended\s+it|"
    r"gone\s+ahead|done\s+it|finished\s+it|not\s+woken\s+up)\b",
    r"\bwis?h\b[^.?!]{0,16}\b(?:i|he|she|they)\b[^.?!]{0,10}"
    r"\b(?:hadn'?t|had\s+not|never)\b[^.?!]{0,10}"
    r"\b(?:survived|woken\s+up|made\s+it|come\s+round|pulled\s+through)\b",
    # ...and the same wish said about the accident rather than about dying: "i nearly died off my
    # bike and i wish it had worked" is somebody saying they wanted the fall to kill them.
    r"\b(?:nearly|almost)\b[^.?!]{0,30}\b(?:died|killed\s+(?:my|him|her)self|got\s+hit|"
    r"been\s+hit|run\s+over|knocked\s+(?:me\s+)?(?:off|down|over)|gone\s+under)\b"
    r"[^.?!]{0,40}\bwis?h\b[^.?!]{0,30}\b(?:it|that|i|they)\b[^.?!]{0,12}"
    r"\b(?:had|would\s+have|'d)\b[^.?!]{0,16}"
    r"\b(?:worked|happened|gone\s+through|succeeded|done\s+it|killed\s+me|finished\s+(?:it|"
    r"the\s+job|me\s+off)|taken\s+me|done\s+for\s+me)\b",
)


EFFORT_BEFORE = (
    r"\b(?:came|come|fell|fallen|slipped|tripped|tumbled|crashed|went\s+over|got\s+knocked)\b"
    r"[^.?!]{0,24}\b(?:nearly|almost)\b[^.?!]{0,20}\b(?:killed|kill)\s+my\s*self\b"
)


EFFORT_DIED = (
    r"\b(?:nearly|almost|came\s+close\s+to|so\s+close\s+to)\b[^.?!]{0,20}"
    r"\b(?:died|killed\s+(?:my|him|her|them)self)\b"
)


COME_OFF_IT = (
    r"\b(?:off|on|from)\s+(?:(?:my|his|her|their|our|a|the)\s+)?"
    r"(?:bike|bicycle|motorbike|motorcycle|scooter|moped|horse|pony|quad|skateboard|"
    r"ladder|roof|scaffold|balcony|wall|fence|trampoline|stairs|steps|staircase|"
    r"road|motorway|kerb|car|van|truck|lorry|tractor|boat)\b"
)


EFFORT_DOING = (
    r"\b(?:nearly|almost)\b[^.?!]{0,24}\b(?:killed|kill)\s+(?:my|him|her|them)self\s+"
    r"(?P<doing>[a-z']+ing)\b"
)


EFFORT_NOT_AN_ACCIDENT = (
    r"\b(?:on\s+purpose|deliberately|by\s+choice|meant\s+to|tried\s+to|wanted\s+to)\b",
    r"\b(?:wish|wished|hope|hoped)\b",
    r"\b(?:so\s+i\s+(?:would|could)\s+die|to\s+die)\b",
)


COUNTERFACTUAL_IDIOM = (
    r"\b(?:died|killed\s+(?:my|him|her)self|killed\s+me)\s+"
    r"(?:laughing|of\s+(?:embarrassment|boredom|shame|thirst|curiosity))\b",
)

# Someone has been found hanging or strangled: the weight comes off the neck first, then CPR.
# The person who is hanging, said with no object and no date: "my brother is hanging", "hes
# hanging in the garage", "she was hanging when i got home". The words after the verb decide it: a
# thing being put up, dried or carried is not a person.
PERSON_HANGING = (
    r"\b(?:he|she|they|hes|shes|theyre|someone|somebody|(?:my|his|her|their|our)\s+(?:brother|"
    r"sister|mum|mom|mam|dad|father|mother|son|daughter|child|kid|boy|girl|baby|husband|wife|"
    r"partner|boyfriend|girlfriend|ex|uncle|aunt|nan|nana|gran|granny|grandad|grandpa|grandma|"
    r"grandmother|grandfather|cousin|friend|mate|flatmate|housemate|neighbour|neighbor|carer|"
    r"stepdad|stepson|stepdaughter|nephew|niece)s?)\b[^.?!]{0,20}?'?s?\s+"
    r"(?:is\s+|was\s+)?(?:hanging|hung)\b"
    r"(?!\s+(?:the|a|an|his|her|their|my|our|your|some|those|these|up|out|around|about|"
    # "my dad is hung over after his birthday" is a hangover and "my brother was hanging
    # back at the party" is holding off; both are the commonest ordinary "hung" about a
    # person and both wore the neck card (clear-octopus, #5930).
    r"over|back|"
    r"christmas|fairy|lights|decorations|baubles|garland|wreath|washing|laundry|clothes|out\s+with|"
    r"wallpaper|tinsel|foil|lining|bunting|paper|"
    # The reflexive is left to the arm below, which has the chore fence: "he hung himself out to
    # dry" and "she hung herself the washing" are a figure of speech and a washday.
    r"himself|herself|themselves|my\s*self|myself|"
    r"on\s+the\s+(?:phone|line|doorstep|door|bell|internet|web|sofa|fence|gate|wall))\b)"
    # Coping, playing and still-with-us: "hes hanging by a thread", "hes hanging on", "hes
    # hanging in there", "my daughter is hanging off the sofa", "my son is hanging on the monkey
    # bars", "my nan is hanging on at the hospital". A bare "on" at the end of the line and "on
    # at ..." are the coping sense; the furniture a child climbs on is play. "hes hanging on the
    # rail" is a person, so "on the" is only fenced for the play things. "by the neck" and "by a
    # rope" are the act and are deliberately not excluded.
    r"(?!\s+(?:by\s+a\s+thread|by\s+(?:his|her|their|my)\s+fingertips?|in\s+there)\b)"
    r"(?!\s+on\b\s*(?:$|[.,!?;]|\bin\s+there\b|at\b))"
    # The same play things take any of the three prepositions a child holds on by: "hanging on the
    # monkey bars", "hanging from the monkey bars", "hanging off the sofa" (magenta-pine, #5930 -
    # "from the" was the one the fence did not have, so a child on the climbing frame got the
    # rescue card). "upside down" is the same game said without an object. "from the rafters" and
    # "from a rope" are still the act: neither is in this list.
    r"(?!\s+(?:on|from|off)\s+(?:the\s+)?(?:monkey\s+bars|wall\s+bars|climbing\s+frame|"
    r"trampoline|slide|swing|bars|sofa|couch|settee|bed|bunk|bunk\s+bed|chair|table|bike|"
    r"swing\s+set)\b)"
    r"(?!\s+upside\s+down\b)"
    # Holding on hard is the coping sense too: "my nan is hanging on for dear life".
    r"(?!\s+(?:on\s+)?for\s+dear\s+life\b)"
    # A bare plural straight after the verb is the thing being put up, not a person: "my dad is
    # hanging curtains", "my dad is hanging shelves in the kitchen", "my mum is hanging
    # pictures", "hes hanging stockings". A person is never a plural, so this covers the whole
    # shelf without listing it (steward-frank-chicken's list, #5930).
    r"(?!\s+[a-z]+s\b)"
    # Loitering and the pub: "my ex is hanging round here", "hes hanging with his mates", "my
    # friend is hanging by the bar". "by the neck" and "by a rope" are the act and are not
    # excluded.
    r"(?!\s+round\b)"
    r"(?!\s+with\s+(?:(?:his|her|their|my|our)\s+|the\s+)?(?:mates?|friends?|family|kids|lads|"
    r"girls|boys|crowd)\b)"
    r"(?!\s+(?:by|at)\s+the\s+(?:bar|counter|pub)\b)",
)

# "Out cold" is the same words for more than one thing. With a knock behind it - a tackle, a fall,
# a wall, a car - it is being knocked out, and it is the head-injury call. On its own it is the
# faint: "i was out cold for a minute" is what people say for a blackout, and the head-injury card
# told them about "confusion, drowsiness or sickness after a bang on the head" when no bang was
# ever mentioned. So the knock is what earns the card here, and a bare faint falls through to the
# faint answer every other faint gets.
HEAD_OUT_COLD = (
    r"\bout\s+cold\b[^.?!]{0,30}\b(?:tackle[ds]?|rugby|football|boxing|match|game|scrum|"
    r"fell|fall|fallen|collided|collision|crashed?|crash|"
    r"car|van|bike|motorbike|lorry|stairs|steps|ladder|wall|door|branch|tree|"
    r"goalpost|post|railing|kerb|curb|round|rounds|canvas|ring|ring\s+rope)\b",
    # The head only counts with the blow that landed on it: "i was out cold as soon as my head hit
    # the pillow" is going to sleep, and the bare word was reading it as a bang on the head.
    r"\bout\s+cold\b[^.?!]{0,30}\b(?:hit|banged?|struck|smacked|cracked|knocked)\b"
    r"[^.?!]{0,12}\bheads?\b",
    r"\bheads?\b[^.?!]{0,20}\b(?:injur\w+|wound|trauma)\b[^.?!]{0,20}\bout\s+cold\b",
    # The bang said *after* the phrase is still the bang, and it is how most people say it: "my
    # son was out cold after a bang on the head", "i was out cold for five minutes after hitting
    # my head". The faint arm claimed those, and a knock-out is a brain injury whichever end of
    # the sentence the blow is in.
    r"\bout\s+cold\b[^.?!]{0,60}\b(?:after|from|when|because)\b[^.?!]{0,30}"
    r"\b(?:a\s+bang|bang(?:ed)?|hitting|hit|blew|blow|knocked|knock|fall|fell|falling|"
    r"blow\s+to|kick|punch|crash|accident|smack)\b",
    # The signs that make even a brief faint a 999: blood or fluid from the ear, a fit, a stop in
    # the breathing. Those are the red flags on the head card, and they read after the phrase.
    r"\bout\s+cold\b[^.?!]{0,40}\b(?:bleeding|bled|blood|fitting|"
    r"had\s+a\s+fit(?!\s+of\s+(?:giggles|the\s+giggles|laughing))|seizure|"
    r"convuls\w*|stopped\s+breathing|not\s+breathing|vomit\w*|threw\s+up|being\s+sick)\b",
    # The other way round: "he was hit by a car and was out cold".
    r"\b(?:hit|banged?|knocked|struck|clipped|collided|fell|fallen|crashed|tackled)\b"
    r"[^.?!]{0,30}\bout\s+cold\b",
    # Somebody still down is not a blackout that has ended: "i found him out cold on the floor",
    # "my mum was out cold on the kitchen floor when i got home". A blackout you watched and one
    # you walked in on are the same person on the same floor, and the recovery position is the
    # answer whatever put them there.
    r"\bout\s+cold\b[^.?!]{0,20}\b(?:floor|ground|street|pavement|road|sofa|couch)\b",
    r"\bfound\s+(?:him|her|them|my\s+\w+|\w+)\b[^.?!]{0,25}\bout\s+cold\b",
    r"\bout\s+cold\b[^.?!]{0,30}\bwhen\s+i\s+(?:found|got\s+home|got\s+in|got\s+back|"
    r"came\s+in|came\s+home|arrived)\b",
    # A long blackout is not the faint that came round by itself, and this arm's own advice says
    # so ("if they were out for more than a minute ... that is 999"). "for a minute" and "for a few
    # seconds" stay the faint.
    r"\bout\s+cold\s+for\s+(?:more\s+than\s+a\s+minute|(?:two|three|four|five|six|seven|"
    r"eight|nine|ten|fifteen|twenty|thirty|forty|fifty|sixty|\d{2,})\s*(?:mins?|minutes?|"
    r"hours?|hrs?)|ages|hours)\b",
    # A colour change with it is the ambulance, not the "looked into today".
    r"\bout\s+cold\b[^.?!]{0,20}\b(?:blue|grey|gray|clammy|mottled|ashen)\b",
    # Wetting yourself is a fit sign, the same class as the fitting and the seizure above.
    r"\bout\s+cold\b[^.?!]{0,40}\b(?:wet\s+my\s*self|wet\s+the\s+bed|wet\s+(?:him|her)\s*self|"
    r"soaked\s+my\s*self|peed\s+my\s*self|peed\s+(?:him|her)\s*self|incontinent)\b",
)

# Not this call now. A near miss, a hypothesis, a memory or a shunt between two cars.
STRUCK_NOT_NOW = (
    # A rider who came off their own bike and hit their own head was not struck by it: "my
    # daughter fell off her bike and hit her head" reached this card through "her bike ... hit
    # her", and it is a fall off her own bike, not a blow from one (the son spelling never did,
    # because "his" is not a person word here). The coming-off and the body part have to be in
    # the line together, so "the car hit me and i fell off my bike" keeps the call.
    r"\b(?:fell|fallen|falling|came|come|comes|slipped|toppled|tipped)\s+off\s+(?:\w+\s+)?"
    r"(?:bike|bicycle|motorbike|motorcycle|scooter|moped|skateboard|horse)\b[^.?!]{0,40}\b"
    r"(?:hit|hits|banged|bangs|struck|strikes)\s+(?:my|his|her|their|our|your)\s+"
    r"(?:head|face|chin|nose|knee|elbow|arm|leg|hip|shoulder|hand|wrist|ankle|back|chest)\b",
    r"\bnearly\b", r"\balmost\b", r"\bjust\s+about\b", r"\bnarrowly\b", r"\bclose\s+call\b",
    r"\bwhat\s+if\b", r"\bif\s+(?:i|he|she|they|we|my\s+\w+)\b", r"\bimagine\b",
    r"\bsuppose\b",
    r"\b(?:years?|decades?)\s+(?:ago|back)\b", r"\bin\s+(?:19|20)\d\d\b",
    r"\bwhen\s+(?:i|he|she|they)\s+(?:was|were)\s+(?:a\s+|an\s+)?"
    r"(?:kid|child|little|small|young|boy|girl|teenager|teen)\b",
    r"\blast\s+(?:year|summer|winter|christmas|xmas|term|month|week)\b",
    r"\bmissed\s+(?:me|him|her|them|us|my\s+\w+)\b",
    # One car into another, which is the insurer's call: "a van hit us from behind this morning".
    r"\bfrom\s+behind\b", r"\bin\s+the\s+back\b", r"\brear-?end\w*\b", r"\bwhiplash\b",
    r"\bshunt\w*\b", r"\bwrote\s+(?:it|the\s+car)\s+off\b",
    # "run over" is also how a meeting, a plan and a shopping list are read out, and how a dog
    # goes to greet somebody: none of those is a person under a wheel.
    r"\bover\s+to\b",
    r"\bover\s+(?:the\s+|a\s+|our\s+|my\s+|your\s+)?(?:plan|plans|details|budget|figures|numbers|"
    r"points|list|lists|options|wording|email|emails|costs|cost|rules|schedule|story|recipe|"
    r"contract|draft|accounts|it|them|this|that)\b",
    r"\bran\s+over\s+time\b", r"\bover\s+time\b",
    r"\b(?:you|we|i|they)\s+(?:can|could|should|must)\s+run\s+over\b",
    # What went under the wheel was a wild animal, and that is a sighting, not a casualty: "i saw a
    # fox run over on the way in" was the 999 card with "say it was a vehicle" (deft-bear, #84106).
    # The animal is the thing the verb is about, and so is the noun that follows it. Pets are kept
    # out of the list on purpose, because "my cat got run over" is the vet's line, handed over below.
    r"\b(?:foxe?s?|badgers?|hedgehogs?|deer|squirrels?|owls?|swans?|pigeons?|hares?)\b"
    r"\s+(?:\w+\s+){0,3}(?:run|ran|runs|got|get|was|were|is)?\s*"
    r"(?:over|hit|hits|struck|clipped|knocked)\b",
    # Knocked over in a shop is a bruise and a complaint, not a road: a trolley is not a vehicle.
    r"\bby\s+(?:a\s+|the\s+)?(?:trolley|shopping\s+trolley|pram|pushchair|buggy|wheelchair|"
    r"mobility\s+scooter|crowd|queue)\b",
    # The door is the thing that hit them, or the thing that swung out: "the bus door hit me in
    # the face" is a bruise, not a call, and it is the door that goes in front of the person, so
    # the (?!\s+door) after the vehicle word never saw it.
    r"\b(?:a|an|the|its|his|her|their|my|our)\s+(?:\w+\s+)?doors?\b",
    # A vehicle that hits somebody *with* something hits them with an instrument, or with a bill:
    # "a bus hit me with its door" and "the car has hit me with a big repair bill".
    r"\b(?:hit|hits|struck|strikes|clipped|clips)\s+(?:me|him|her|them|us)\s+with\b",
    # The person's thing was hit, not the person: "a car hit my neighbour's fence", "a car hit my
    # dad's car", "my son's bike". A possessive alone is not enough to stand down - "my son's leg
    # is bleeding after a car hit him" is still this card - so the fence keys on the thing.
    # The understanding engine hands this row a line with the possessive squeezed out of it
    # ("my neighbour's fence" arrives as "my neighbour fence"), so the fence reads both.
    r"\b(?:mum|mom|mother|dad|father|son|daughter|husband|wife|partner|boyfriend|girlfriend|"
    r"brother|sister|friend|child|kid|baby|boy|girl|man|woman|lady|neighbou?r|colleague|mate|"
    r"gran|granny|nan|grandad|grandma|grandpa|passenger|cyclist|pedestrian|toddler|teenager|"
    r"nephew|niece|cousin|aunt|uncle|stepson|stepdaughter|stepdad|stepmum|driver|owner)"
    r"\s*['\u2019]?s?\s+(?:car|cars|bike|bikes|van|vans|lorry|lorries|truck|trucks|bus|buses|"
    r"wall|walls|fence|fences|gate|gates|hedge|hedges|house|window|windows|bins?|garden|"
    r"garage|drive|driveway|shed|roof|bumper|wing|mirror|gatepost|door|school|schools|"
    r"nursery|playground|office|work|workplace|shop|shops|church|building|home|flat|room)\b",
)

# The habit of hurting is intent on its own ("i keep hurting myself"), and it is the shape that
# also catches a clumsy person with a kitchen: "i keep hurting myself in the kitchen" was the
# crisis line. Kept as its own tuple so `_habit_explained` can stand it down when the line says how
# the hurt happened, without touching any other way of saying the wish.
SELF_HARM_HABIT = (
    # "my back keeps hurting", "my boiler keeps cutting out": the verb has to point at the person
    # before a kept hurting counts as intent, or the boiler and the knee get a crisis line.
    r"\bi\s+(?:keep|keeps|kept|keep\s+on)\s+(?:cutting|hurting|burning)\b"
    r"(?=\s*(?:$|[.,!?]|and\b|again\b|so\b|all\b|every\b))",
    # ...and any verb of hurting repeated on yourself, not just the three commonest: "i keep
    # punching myself in the head", "i keep scratching myself", "i keep hitting myself".
    r"\b(?:keep|keeps|kept|keep\s+on)\s+(?:cutting|hurting|burning|scratching|hitting|banging|"
    r"punching|choking|starving)\s+(?:(?:my|him|her|your)\s*self|them\s*selves|them\s*self)\b",
    # The same habit in the present perfect, which is how people most often say it: "i have been
    # cutting", "ive been cutting", "i have been hurting". Without "myself" nothing else here
    # reads it, and main answered "i have been cutting" with a shrug. The tail is required so the
    # same words over a lawn or a cake stay the thing: "i have been cutting the grass", "i have
    # been burning the toast" and "i have been scratching my head over it" name their object and
    # are ordinary, while "i have been cutting for weeks" and "i have been cutting again" count.
    # Only "cutting" is a habit word on its own. "hurting", "burning" and "scratching" are what
    # people type about a bad back, an itch and sunburn, so a bare present perfect of them is
    # ordinary (teal-emu's read at the first head: "i have been hurting because of my back" went
    # to the crisis line) and the "myself" arm above still reads them when they are the habit.
    # The tail is a clause that ends, a repeat, or a length of time - never a clause that explains
    # itself, which is what "because of my back", "for the family budget" and "for hours in the
    # sun" are.
    r"\b(?:we'?ve|i'?ve|we|i)\s+(?:have|has|had|'?ve)?\s*been\s+(?:on\s+)?"
    r"cutting\b(?=\s*(?:$|[.,!?]|a\s+lot\b|recently\b|lately\b|too\b|most\b|badly\b|"
    r"every\s+day\b|now\b|on\s+and\s+off\b|again\b|"
    r"for\s+(?:weeks|months|years|ages|days|a\s+while|a\s+bit|a\s+long\s+time)\b|"
    r"since\s+(?:i\s+was|then|last\s+year|christmas|primary|school|my\s+teens|"
    r"forever)\b|and\s+(?:i|it)\b|so\s+(?:much|badly|many|hard)\b))",
    # A cut said as a repeat with no object at all: "i cut again", "i cut again last night". The
    # object is what makes it an accident ("i cut my finger again", "i cut the bread again"), so
    # the verb has to be followed by "again" itself, and what comes after "again" must not say how
    # it happened: "i cut again on the bread knife" and "i hurt again at the gym" are ordinary.
    # "i cut again" carries its own shape and needs no object; `hurt` does not, and "i hurt again"
    # straight after a named bad back is the back (purple-camel's read at the sixth head), so the
    # repeat is the cut alone. `i have been hurting myself` still reads the habit above.
    r"\bi\s+cut\s+again\b(?!\s+(?:on|with|at|in|while|after|during|doing|from|"
    r"using|because|the\s+(?:knife|bread|glass|gym|run))\b)",
)

HEAL_TIME = {
    "sprain": (
        "It depends how bad it is. A mild sprain is usually much better in one to two weeks and "
        "normal again in four to six; a bad one with a lot of bruising can take eight to twelve "
        "weeks, and the first 48 hours of rest, ice and keeping it raised are what set that up. "
        "Start gentle movement and walking on it as the pain allows rather than staying off it, "
        "and get it seen if you cannot put weight on it at all, it is very swollen, or it is no "
        "better after a week.",
        "Most sprains are much better in one to two weeks and properly right in four to six; a bad "
        "one can take a couple of months. Ice and rest for the first two days, then gentle walking "
        "and moving it as far as it lets you. A joint you cannot put weight on, or one that is no "
        "better after a week, is worth having looked at."),
    "burn": (
        "A small burn usually settles in a week to ten days, and a blistering one takes about two "
        "to three weeks to heal from underneath. Keep it clean and covered and leave blisters "
        "alone; anything bigger than your palm, on the face or hands, or slow to heal after two "
        "weeks should be seen.",
        "A small burn is mostly fine in seven to ten days, and a blistered one in about two to "
        "three weeks. Leave the blisters alone and keep it covered; a burn that is not healing "
        "after a fortnight, or is on the face or hands, needs a nurse."),
    "blister": (
        "A rubbed blister drains and dries up in about three to five days and the skin under it "
        "is new in a week or two; leave the roof on, cover it with a padded plaster and keep it "
        "dry. One that is hot, spreading or weeping pus is the doctor's rather than time.",
        "Most blisters settle in three to five days and are properly new skin in a week or two. "
        "Cover it, don't pop it, and keep it dry; hot, spreading or pus needs a doctor."),
    "cut": (
        "A small cut closes over in a few days and is usually fully healed in a week or two, with "
        "the edges kept together and the dressing changed. Redness spreading, pus, or a cut that "
        "gapes needs to be seen the same day rather than waited on.",
        "Small cuts close in a few days and are properly healed in a week or two. Keep it clean and "
        "covered, and get it looked at if it goes red and hot, weeps pus, or will not close."),
    "sunburn": (
        "The redness of sunburn usually settles in three to five days and the peeling in about a "
        "week. Cool showers, plenty of water and leaving the peeling skin alone are what help; "
        "shivering, dizziness or bad blisters need a doctor.",
        "Sunburn redness mostly fades in three to five days and the peeling takes about a week. "
        "Cool showers and water help, and leave the skin alone; shivery, dizzy or badly blistered "
        "is a doctor."),
}

HEAD_REPLIES = {
    "head_bang": (
        "A bang on the head is usually fine, but the next 24 hours are the ones to watch: being sick, "
        "being knocked out, or feeling confused or unusually sleepy means an ambulance or A&E rather "
        "than wait, and 111 will advise you on anything milder. Are you up and talking normally now, "
        "or has anything changed since it happened?",
        "A bumped head hurts for a day or two and an ice pack on it for ten minutes is plenty, but "
        "a knock-out, being sick, or feeling confused or sleepier than usual means an ambulance or A&E "
        "rather than wait - 111 for anything milder. Are you up and talking normally now, or has "
        "anything changed since it happened?",
    ),
    "head_bang_other": (
        "A bang on the head is usually fine, but the next 24 hours are the ones to watch: being sick, "
        "being knocked out, or {s} seeming confused or unusually sleepy means an ambulance or A&E "
        "rather than wait, and 111 will advise you on anything milder. Is {s} up and talking normally "
        "now, or has anything changed since it happened?",
        "A bumped head hurts for a day or two, but a knock-out, being sick, or {s} seeming confused or "
        "sleepier than usual means an ambulance or A&E rather than wait - 111 for anything milder. Is "
        "{s} up and talking normally now, or has anything changed since it happened?",
    ),
    "head_bang_red": (
        "That is a 999 call rather than wait and see: being knocked out, confused, drowsy or sick after "
        "a bang on the head is a head injury until a doctor says otherwise. Keep still and awake, stay "
        "with someone, and don't drive yourself.",
        "Ring 999 or 911 now rather than waiting to see: confusion, drowsiness or sickness after a bang "
        "on the head is a head injury until a doctor says otherwise. Keep awake and still while you "
        "wait, and don't take anything for the headache until someone has seen you.",
    ),
    "head_bang_red_other": (
        "That is a 999 call rather than wait and see: being knocked out, confused, drowsy or sick after "
        "a bang on the head is a head injury until a doctor says otherwise. Stay with {o}, keep {o} "
        "awake and still, and don't let {o} drive.",
        "Ring 999 or 911 now rather than waiting to see: confusion, drowsiness or sickness after a bang "
        "on the head is a head injury until a doctor says otherwise. Keep {o} awake and still, and stay "
        "with {o} until help comes.",
    ),
}

# The person is the one bitten, so the human card stays: "my neighbours dog bit my hand", "it bit
# me", "my cat bit my son". Only a body part or a person makes this true, never a possessive alone.
HUMAN_BITTEN = (
    r"\b(?:bit|bitten|nipped|snapped\s+at|went\s+for|attacked)\s+(?:me|him|her|us|them)\b",
    r"\b(?:bit|bitten|nipped)\s+(?:my|his|her|their|our)\s+(?:hand|hands|finger|fingers|thumb|"
    r"arm|arms|leg|legs|foot|feet|face|cheek|lip|ankle|head|neck|shoulder|ear|ears|nose|eye|wrist|"
    r"toe|toes)\b",
    r"\b(?:bit|bitten|nipped)\s+(?:the|a)\s+(?:child|kid|baby|boy|girl|man|woman|postman|postie|"
    r"vet)\b",
    r"\b(?:my|our|her|his|their)\s+(?:son|daughter|child|kid|baby|husband|wife|partner|mum|mom|"
    r"dad|father|mother|friend|neighbour|neighbor|postman|postie)\b[^.?!]{0,20}"
    r"\b(?:was|were|got|has\s+been|had\s+been)\s+(?:bit|bitten)\b",
    # The speaker is the one bitten, written the other way round: "i was bitten by my cat", "my
    # hand was bitten by my cat". The verb sits in the passive, so the pet name comes after it and
    # the animal arm read the cat as the wounded one. A speaker or a body part keeps the human card.
    r"\b(?:i|we)\b[^.?!]{0,12}\b(?:was|were|got|have\s+been|has\s+been|had\s+been)\s+"
    r"(?:bit|bitten)\b",
    # ... and the same turn for an animal that went for the speaker: "i was attacked by my
    # neighbours dog" was read as the pet being attacked, because the animal comes after the verb.
    r"\b(?:i|we)\b[^.?!]{0,15}\b(?:was|were|got|have\s+been|has\s+been|had\s+been)\s+"
    r"(?:attacked|savaged|mauled|scratched|clawed)\b",
    r"\b(?:my|his|her|their|our)\s+(?:hand|hands|finger|fingers|thumb|arm|arms|leg|legs|foot|"
    r"feet|face|cheek|lip|ankle|head|neck|shoulder|ear|ears|nose|eye|wrist|toe|toes)\b"
    r"[^.?!]{0,15}\b(?:was|were|got|has\s+been|had\s+been)\s+(?:bit|bitten)\b",
    # A scratch is the same wound as a bite, and the pet name in front of it did not make it the
    # pet's: "my cat scratched me and it is bleeding" was reaching the vet's card, which is about
    # the cat. A person or a body part has to be on the other end, so a scratched door or sofa
    # stays a thing.
    r"\b(?:scratch(?:ed|es|ing)?|claw(?:ed|s|ing)?)\s+(?:me|him|her|us|them)\b",
    r"\b(?:scratch(?:ed|es|ing)?|claw(?:ed|s|ing)?)\s+(?:my|his|her|their|our)\s+(?:hand|hands|"
    r"finger|fingers|thumb|arm|arms|leg|legs|foot|feet|face|cheek|lip|ankle|head|neck|shoulder|"
    r"ear|ears|nose|eye|wrist|toe|toes|skin)\b",
)



MILD = (
    r"\bthrough\s+my\s+nose\b", r"\bfood\s+poisoning\b", r"\bpoison\s+ivy\b", r"\bpoisonous\s+(?:plant|mushroom|snake|spider)\b",
    r"\bfire\s+(?:alarm|drill|station|escape|pit|place|works|extinguisher|guard|fighter)s?\b",
    r"\b(?:camp|bon)fire\b", r"\bfireworks?\b", r"\bfired?\s+(?:from|up)\b", r"\bon\s+fire\b.*\b(?:team|player|form|streak)\b",
    r"\b(?:bleed|bled|bleeding)\s+(?:the|my|a)\s+(?:radiator|pipe|boiler|brakes?)\b",
    r"\bbleed(?:ing)?\s+the\s+(?:heating|radiators?)\b",
    r"\bblood\s+(?:test|pressure|donor|donation|type|sugar|group)\b", r"\bbloody\b",
    r"\bkill(?:ing)?\s+(?:time|the\s+weeds)\b", r"\bdead\s+(?:battery|phone|line|end|weight)\b",
    r"\bdie\s+cast\b", r"\bcut\s+(?:my|the)\s+(?:hair|nails|lawn|grass)\b", r"\bcut\s+it\s+out\b",
    # (a school morning is handled by ROUTINE_WAKE, so the benign reading lives there and the
    # red flags after "for school" still ring)
    r"\bwak(?:e|ing)\s+up\s+(?:in|before)\s+(?:the\s+morning|noon|\d)",
    r"\bchest\s+of\s+drawers\b", r"\bfire\s+me\b", r"\brained\s+off\b", r"\bstabbed\s+in\s+the\s+back\b",
    # The head is also where the figures of speech live: a nail, a wall, a drum, a headline.
    r"\bhit\s+the\s+nail\s+on\s+the\s+head\b", r"\bhead\s*-?\s*bang(?:ing|er|ers)\b",
    # "i keep banging my head against a wall" is the idiom, and the banger has to be the speaker:
    # the same words with somebody else on the front are the assault the head arm already reads -
    # "he banged my head against the door" and "my husband banged my head against the wall" were
    # both the bumped-head card because this arm wrote "my", not "i" (@purple-camel, #6264).
    r"\b(?:i|im|i'?m|i'?ve)\b[^.?!]{0,20}\bbang(?:ing|ed)?\s+my\s+head\s+against\s+"
    r"(?:a\s+|the\s+)?(?:wall|brick|desk|door|table)\b",
    r"\bbang(?:ing|ed)?\s+(?:your|his|her)\s+head\s+against\s+(?:a\s+|the\s+)?(?:wall|brick|"
    r"desk|door|table)\b",
    r"\bhead\s+(?:over\s+heels|start|of\s+(?:the\s+)?(?:department|house|school|state)|count)\b",
    r"\bknock(?:ed|s)?\s+out\s+of\s+(?:the\s+)?(?:cup|competition|tournament|playoffs?|championship|league|competition|semis?|final|series|race)\b",
    r"\bknock(?:ed|s)?\s+(?:it|this|that|things)\s+out\s+of\s+the\s+park\b",
    # a frightened pet is a training question, not a person in danger
    r"\b(?:dog|puppy|pup|cat|kitten|horse|pony|rabbit|hamster|parrot|bird)\s+(?:is|was|seems|gets|looks|has\s+got)\s+(?:really\s+|very\s+|so\s+|a\s+bit\s+)?(?:scared|afraid|terrified|frightened|nervous|anxious)\b",
)

# A scald that is past first aid: the skin is peeling, white, waxy or charred, or a small child
# has been scalded. A plain red burn keeps the first-aid reply, so the burn word has to be there.
SCALD = (
    r"\b(?:burn\w*|scald\w*|boiling\s+water|hot\s+oil|steam|pan\s+of\s+"
    r"(?:water|oil|fat))\b[^.?!]{0,40}"
    r"\b(?:skin\s+)?(?:is\s+|gone\s+)?(?:peeling|peeled|peeling\s+off|waxy|charred|"
    r"blackened)\b",
    # A kettle or a saucepan can be blackened by limescale or soot, so the body has to be named.
    r"\b(?:kettle|saucepan|pan)\b[^.?!]{0,40}\b(?:skin|hand|arm|foot|feet|leg|face|wrist|"
    r"fingers?|chest|shoulder|thigh|thumb|toes?)\b[^.?!]{0,30}\b(?:peeling|peeled|waxy|charred|"
    r"blackened)\b",
    r"\b(?:skin|hand|arm|foot|feet|leg|face|wrist|fingers?|chest|shoulder|thigh|thumb|toes?)\b"
    r"[^.?!]{0,30}\b(?:peeling|peeled|waxy|charred|blackened)\b[^.?!]{0,30}\b(?:kettle|"
    r"saucepan|pan)\b",
    # "gone white", "turned white": the skin itself, not a limescale mark on the kettle, and the
    # burn word can come before or after it: "my hand went white after the burn". White paint, a
    # white face from shock and white skin are not burns, so the burn word has to be in the line.
    r"\b(?:went|gone|turned|turning|going|is|was)\s+white\b[^.?!]{0,40}"
    r"\b(?:burn\w*|scald\w*|boiling|hot\s+oil|steam|kettle|water\s+(?:hit|landed|went))\b",
    r"\b(?:burn\w*|scald\w*|boiling|hot\s+oil|steam|kettle)\b[^.?!]{0,40}"
    r"\b(?:went|gone|turned|turning|going|is|was)\s+white\b",
    # A small child, a kettle and a pull or a tip over is the scald this reply is written for.
    r"\b(?:baby|toddler|child|son|daughter|kid|little\s+one)\b[^.?!]{0,40}"
    r"\b(?:kettle|saucepan|pan)\b[^.?!]{0,40}\b(?:over|on\s+(?:him|her|them)sel(?:f|ves)|"
    r"on\s+him|on\s+her)\b",
    r"\b(?:boiling|scalding)\s+(?:water|oil|fat|soup|tea|coffee)\b[^.?!]{0,30}"
    r"\b(?:over|on|onto)\s+(?:my|his|her|their|the)\s+(?:baby|toddler|child|son|daughter|kid)\b",
    r"\b(?:baby|toddler|child|son|daughter|kid|little\s+one)\b[^.?!]{0,40}"
    r"\b(?:boiling|scalding)\s+(?:water|oil|fat|soup|tea|coffee|kettle|pan)\b",
    r"\b(?:boiling|scalding)\s+(?:water|oil|fat|soup|tea|coffee|kettle|pan)\b[^.?!]{0,40}"
    r"\b(?:him|her|them)sel(?:f|ves)\b",
    r"\b(?:baby|toddler|child|kid|little\s+one|boy|girl)\b[^.?!]{0,30}"
    r"\b(?:scalded|burnt|burned)\s+(?:him|her|them)sel(?:f|ves)\b",
    # A bigger child is only an emergency when the burn is bad enough to show it.
    r"\b(?:son|daughter|boy|girl|child|kid|niece|nephew)\b[^.?!]{0,40}"
    r"\b(?:scalded|burnt|burned)\b[^.?!]{0,50}"
    r"\b(?:screaming|screamed|crying|badly|all\s+over|blister\w*|peeling)\b",
)

# "im so tired i wish i was dead" is the same figure of speech as "im dying for a cup of tea", and
# main answers it as the day it is. The tell is a degree word and a state before the wish: a wish
# said plainly ("i wish i was dead") has nothing in front of it, and a state that is not on this
# list ("i feel so low i wish i was dead") is not something to shrug at, so it still rings.
HYPERBOLE_WISH = (
    r"\b(?:i'?m|im|i\s+am|i\s+feel|feeling)\s+"
    r"(?:(?:so|too|that|this|really|proper|bloody|absolutely|utterly|completely|dead)\s+)?"
    r"(?:tired|exhausted|bored|knackered|shattered|worn\s+out|sleepy|hungry|thirsty|hot|cold|"
    r"sore|aching|full|stuffed|busy|fed\s+up|embarrassed|mortified|old|poor|skint|stressed|"
    r"nervous|scared|itchy|sweaty|dirty|covered\s+in\s+\w+|hungover|hung\s?over|ill|poorly|"
    r"unwell|headachy|aching|achy|cream\s+crackered|croaky|snotty|sniffly)"
    r"\b[^.?!]{0,24}\b(?:wish|wished|wishing)\b",
    # The same complaint said about a thing rather than about themselves: "work is so boring i
    # wish i was dead", "the job is that dull i wish i was dead".
    r"\b\w+(?:\s+\w+)?\s+(?:is|are|was|were)\s+(?:(?:so|too|that|this|really|proper|bloody)\s+)?"
    r"(?:boring|dull|slow|tiring|tedious|repetitive|long|hot|cold|loud|noisy|busy|quiet|"
    r"rubbish|crap|annoying|fiddly|heavy|stiff|itchy|sweaty|grim|depressing|pointless|"
    # How the day itself is said: "the traffic is so bad", "this weather is that awful",
    # "the match was so rubbish", "the shift is so exhausting". These rang the crisis card
    # while `so long` did not.
    r"bad|worse|awful|terrible|horrible|dreadful|miserable|sore|painful|aching|achy|hungover|"
    r"hung\s?over|exhausting|stressful|tough|hard|chaotic|mental|hectic|shocking|useless)\b"
    r"[^.?!]{0,24}\b(?:wish|wished|wishing)\b",
    # ...and said about a part that hurts: "my feet are killing me i wish i was dead".
    r"\b(?:my\s+)?\w+\s+(?:is|are|have\s+been)\s+killing\s+me\b[^.?!]{0,24}"
    r"\b(?:wish|wished|wishing)\b",
    # The same part with the hurt as a plain verb: "my feet hurt and i wish i was dead", "my
    # head hurts i wish i was dead", "my back is agony i wish i was dead". A part has to be
    # named, so "i hurt and i wish i was dead" stays the wish.
    r"\b(?:my|his|her|their)\s+(?:head|heads|feet|foot|knees?|back|legs?|arms?|shoulders?|hips?|"
    r"teeth|tooth|neck|stomach|belly|ankles?|wrists?|hands?|thighs?|calves|calf|elbows?|joints?|"
    r"shoulder\s+blade|lower\s+back|sciatica)\b[^.?!]{0,28}"
    r"\b(?:hurt|hurts|hurting|aching|aches?|sore|agony|killing\s+me|throbbing|stiff|bad)\b"
    r"[^.?!]{0,20}\b(?:wish|wished|wishing)\b",
)

PURSUIT_PLACE_HOME = (
    r"\b(?:outside|in\s+front\s+of|at\s+the\s+end\s+of|round\s+the\s+back\s+of)\s+"
    r"(?:my|our)\s+(?:house|home|flat|door|doorstep|front\s+door|window|gate|drive|driveway|"
    r"garden)\b",
    r"\b(?:banging|hammering|pounding|knocking|ringing)\s+(?:on|at)\s+(?:my|our|the)\s+"
    r"(?:door|doorbell|window|buzzer)\b",
    # "waiting outside" on its own needs the place it is outside of, because a partner waiting
    # outside the pub, the takeaway or the church is the evening, not this: curious-zebra's read at
    # `eab419f3`. The bare form and "waiting for me" are in PURSUIT_OUTSIDE below, for an ex only.
    r"\b(?:waiting|waits|sat|sitting|stood|standing|parked|lurking|hiding|hovering|hanging\s+around)\s+"
    r"(?:right\s+|still\s+|now\s+)?(?:outside|in\s+front\s+of|at\s+the\s+end\s+of|"
    r"round\s+the\s+back\s+of)\s+(?:my|our)\s+(?:house|home|flat|door|doorstep|front\s+door|"
    r"window|gate|drive|driveway|garden)\b",
    # Turning up is only a pursuit at the user's own door or where they are: "my ex turned up at
    # the party" is an awkward evening, not this.
    r"\b(?:turned|turns|turning|showed|shows|showing)\s+up\s+(?:at|outside|in|on)\s+"
    r"(?:my|our)\s+(?:house|home|flat|door|doorstep|work|office|workplace|mum'?s|mum|mother'?s|"
    r"parents'?|school|gate)\b",
    r"\b(?:turned|turns|turning|showed|shows|showing)\s+up\s+(?:outside|unannounced|uninvited)\b",
    # Somebody who is at the door is at the door whether or not they said where they are waiting.
    r"\b(?:at|on)\s+(?:my|our)\s+(?:front\s+)?(?:door|doorstep|buzzer)\b",
    # A social follow is a follow: "he is following me on instagram" is not somebody behind you.
    r"\b(?:following|followed|follows)\s+(?:me|us)\b"
    r"(?!\s+(?:back\s+)?(?:on|at|in)\s+(?:instagram|insta|facebook|fb|twitter|x|tiktok|"
    r"socials?|social\s+media|linkedin|youtube|reddit|snapchat|strava|whatsapp|threads|"
    r"the\s+app|here))",
    r"\bstalk(?:s|ing|ed)\s+(?:me|us)\b"
    r"(?!\s+(?:back\s+)?(?:on|at|in)\s+(?:instagram|insta|facebook|fb|twitter|x|tiktok|"
    r"socials?|social\s+media|linkedin|youtube|reddit|snapchat|strava|whatsapp|threads))",
    r"\b(?:watching|watched|watches)\s+(?:my|our)\s+(?:house|home|flat)\b",
)

# "i hurt myself lifting weights", "i keep hurting myself in the kitchen", "i hurt myself at work":
# the line says how it happened, so the hurt is a knock to answer rather than a wish to answer with
# a crisis line. The cue is the effort, the place or the thing, and it has to sit with the hurting
# on the speaker: "i want to hurt myself at work" keeps the crisis reply, because a stated wish
# beats a circumstance (see `_habit_explained`).
INJURY_HOW = (
    # the gerund names the effort: "i hurt myself lifting weights", "i hurt myself running"
    r"\b(?:hurt|hurting|injured|injuring|tweaked|strained|pulled|sprained|wrenched)\s+my\s*self\s+"
    r"(?:while\s+|when\s+)?(?:lifting|carrying|moving|shifting|digging|running|jogging|walking|"
    r"hiking|cycling|swimming|training|exercising|boxing|climbing|dancing|skating|skiing|rowing|"
    r"playing|gardening|cooking|chopping|cleaning|hoovering|decorating|painting|diy|stretching|"
    r"working\s+out|squatting|deadlifting|shopping|ice\s+skating)\b",
    # the place says how: "i hurt myself in the kitchen", "i keep hurting myself at work"
    r"\b(?:hurt|hurting|injured|injuring)\s+my\s*self\b[^.?!]{0,24}\b(?:in|at|on)\s+(?:the|my|a)\s+"
    r"(?:kitchen|garden|garage|gym|office|stairs|bathroom|shower|shed|workshop|pitch|field|"
    r"court|track|pool|sea|road|street|bus|train|ladder|roof|site|building\s+site|work)\b",
    r"\b(?:hurt|hurting|injured|injuring)\s+my\s*self\s+at\s+work\b",
    # the thing did it: "i hurt myself on the door", "i hurt myself with the drill"
    r"\b(?:hurt|hurting|injured|injuring)\s+my\s*self\s+(?:on|with)\s+(?:a|an|the|some)\s+"
    r"(?:\w+\s+){0,2}(?:door|shelf|drawer|car|bike|ladder|knife|drill|saw|pan|oven|hob|kettle|"
    r"weight|weights|barbell|dumbbell|box|bag|suitcase|pram|wheelchair|step|stair|curb|kerb)\b",
    # the aftermath says it is a knock: "i hurt myself yesterday and it still hurts"
    r"\b(?:hurt|hurting|injured|injuring)\s+my\s*self\b[^.?!]{0,30}\band\s+(?:it|my\s+\w+)\s+"
    r"(?:still\s+)?(?:hurts|aches|is\s+sore|swelled|swollen|is\s+bruised)\b",
    # the fall did it: "i fell down the stairs and hurt myself", "i hurt myself falling". A slip
    # with a knife cuts as easily as it bruises: "i slipped with the knife and cut myself" was the
    # crisis card while "i cut myself shaving" was the first aid, and the circumstance is what
    # makes either of them an accident.
    r"\b(?:fell|fallen|falling|tripped|slipped)\b[^.?!]{0,32}\b(?:hurt|injured|cut|cutting|"
    r"nicked|sliced|grazed|scraped)\s+my\s*self\b",
    r"\b(?:hurt|hurting|injured|injuring|cut|cutting|nicked|sliced)\s+my\s*self\s+"
    r"(?:falling|tripping|slipping)\b",
)

# Anaphylaxis does not always name what set it off: "my lips are swelling" on its own is the same
# ambulance, because the airway is the thing being lost. A cold sore, a bitten lip, a new piercing
# and a story in the past tense are not this.
LIPS_SWELL_BARE = (
    r"\b(?:my|his|her|their)\s+(?:lips?|tongue|throat|face)\s+(?:are\s+|is\s+|'s\s+)?"
    r"(?:swelling|swollen|swelled|puff\w*\s+up|puffed\s+up|puffing\s+up|blowing\s+up)\b",
    r"\b(?:my|his|her|their)\s+(?:throat|tongue|uvula)\b[^.?!]{0,15}\b(?:is|'s|feels?)\s+"
    r"(?:closing|tight|swelling|swollen)\b",
    r"\b(?:my|his|her|their)\s+(?:uvula)\s+(?:is\s+|'s\s+)?(?:swelling|swollen)\b",
    # A sting with a faint, a dizzy spell or clamminess is the same reaction with the blood
    # pressure gone, and the sting card's "scrape it out sideways" is the wrong answer for it.
    #
    # It has to be a sting that happened: "there is a wasp in my kitchen and i feel dizzy from the
    # heat" is the heat, and "i feel dizzy and there is a bee in the garden" is not a sting at all,
    # so an insect word on its own cannot carry the arm - only "stung", or the sting itself.
    r"\b(?:stung|stings?)\b[^.?!]{0,40}\b(?:dizzy|dizziness|faint\w*|"
    r"light\s?headed|clammy)\b",
    r"\b(?:dizzy|dizziness|faint\w*|light\s?headed|clammy)\b[^.?!]{0,40}\b(?:stung|stings?)\b",
    # The throat's own way of saying the airway is going, which is not "tight": after a sting a
    # throat or a tongue that "feels funny" or "feels thick" is the ambulance, not the itch to
    # watch.
    r"\b(?:stung|stings?)\b[^.?!]{0,40}\b(?:throat|tongue)\b[^.?!]{0,12}"
    r"\b(?:feels?|is|going|getting)\s+(?:a\s+bit\s+|a\s+little\s+|really\s+|very\s+|so\s+)?"
    r"(?:funny|odd|weird|strange|thick|tickl\w*|itch\w*)\b",
    r"\b(?:throat|tongue)\b[^.?!]{0,12}\b(?:feels?|is)\s+(?:a\s+bit\s+|a\s+little\s+|"
    r"really\s+|very\s+|so\s+)?(?:funny|odd|weird|strange|thick|tickl\w*|itch\w*)\b"
    r"[^.?!]{0,40}\b(?:stung|stings?)\b",
    # The same in the verb's own shape: "my throat tickles after a bee sting" is not a lump in the
    # throat with nothing there.
    r"\b(?:throat|tongue)\b[^.?!]{0,15}\b(?:tickl\w*|itches|itching)\b[^.?!]{0,40}"
    r"\b(?:stung|stings?)\b",
    r"\b(?:stung|stings?)\b[^.?!]{0,40}\b(?:throat|tongue)\b[^.?!]{0,15}"
    r"\b(?:tickl\w*|itches|itching)\b",
)

DOG_ATTACK = (
    # ... but not when the thing being bitten is the dog's own body, or a fence, a toy or a lead:
    # "my dog is biting his paw" is the skin answer and "my dog is biting the fence" is the
    # chewing one, and the verb alone has no object to tell them apart (great-fork's lookahead).
    r"\bdogs?\b.{0,30}\b(?:attacking|mauling|savaging|biting|went\s+for)\b"
    r"(?!\s+(?:his|her|its|their|the|a)\s+(?:paw|paws|tail|leg|legs|foot|feet|ear|ears|fur|"
    r"skin|lead|fence|toy|bed|nappy|blanket|cushion))\b",
    r"\bdogs?\s+(?:has\s+|have\s+)?bit\s+(?:me|my|his|her|him|them|a\s+(?:child|kid|baby))\b",
    r"\b(?:bit|bitten)\s+by\s+a\s+dog\b",
    r"\b(?:attacking|mauling)\s+(?:him|her|them|me|my\s+\w+)\b.{0,20}\bdogs?\b",
    r"\b(?:being\s+)?attacked\s+by\s+(?:a\s+)?dogs?\b",
    r"\bdogs?\b.{0,25}\b(?:is|are|was|were)?\s*(?:going\s+for|after|lunging\s+at|snapping\s+at|growling\s+at)\s+(?:me|my|him|her|them)\b",
    # ... and a bite with a person in it, even when an object is in the line too: the lookahead
    # above stands the first pattern down for "my dog is biting the lead", so this arm is what
    # rings for a person's hand in the line with an object. DOG_MOUTHING then stands this arm
    # down again for the mouthing shape ("biting the lead and my hand", "the toy and my fingers"),
    # which is the yelp-and-redirect question and not an attack - a gate, a fence or a door is not
    # on that list, so "biting the door and my fingers" keeps this arm.
    #
    # A bare "bite" or "bites" is left out on purpose: "my dog bites me" and "my dog bites my hand"
    # are how a habit is described, not a dog with hold of someone, and both were answered with
    # the training card on main. The past and the progressive are the shapes of a bite that
    # happened or is happening now.
    r"\bdogs?\b[^.?!]{0,30}\b(?:bit|bitten|biting|nipped|nipping|snapped\s+at)\b[^.?!]{0,25}"
    r"\b(?:me|us|my\s+(?:hand|hands|arm|arms|leg|legs|foot|feet|face|finger|fingers|head|"
    r"shoulder|wrist|ankle|neck|cheek|nose|toe|toes|chin))\b",
)

# The figure on the meter that is a low: under 4, whichever digits, so 1.9 and 3.9 both count.
_A_LOW_FIGURE = r"(?:0\.[1-9]|[1-3](?:\.\d)?)(?:\s*mmol)?\b"

# A reading on the meter below 4. This is the level the low-sugar card is for, whichever way the
# line is put: "my blood sugar is 1.9", "sugar level was 3", "glucose reading of 0.9",
# "blood sugar: 2.4". Anything at 4 or above is a different question - the target range - and a
# number on its own with no verb ("sugar 3 tbsp") is a recipe, so the verb stays required.
# Glucose is the same reading as blood sugar, in the same units, and it is the word half the
# people with a meter use. A noun the patterns below share, so a fix to one is a fix to all:
# "my glucose is 2.9" was answered "Thanks for telling me - I'm here if you want to dig into any
# of that" while "my blood sugar is 2.9" got the sugar-now card, and "blood glucose is 2.9" got
# the target range - the noun, not the question, was the difference.
_A_READING_NOUN = r"(?:(?:blood\s+)?sugars?|(?:blood\s+)?glucose)"

SUGAR_READING_LOW = (
    # the figure with its verb: "my blood sugar is 1.9", "sugar level was 3", "sugars are 3.8",
    # "my glucose is 2.9", "blood glucose was 3.1"
    r"\b" + _A_READING_NOUN + r"\s+(?:levels?\s+|readings?\s+)?"
    r"(?:is|was|are|at|reads?|reading|of|:)\s*" + _A_LOW_FIGURE,
    # the figure alone, which is how a reading is usually sent: "blood sugar 1.9". The word
    # "blood" is what makes it safe to read without a verb, so a recipe's "sugar 3 tbsp" is out.
    r"\bblood\s+sugars?\s+(?:levels?\s+|readings?\s+)?(?:of\s+|:\s*)?" + _A_LOW_FIGURE,
    # and the same for glucose, which a meter is read off by whoever owns it: "glucose reading
    # 2.4", "blood glucose 2.9", "my glucose 2.9". The possessive or "blood" keeps a recipe's
    # "glucose 3 tbsp" out, and the figure itself still has to be under 4.
    # the possessive or "blood" is required here: a verb-free "glucose 3 tbsp" is a recipe, and
    # the first cut of this line read it as a hypo.
    r"\b(?:blood|my|his|her|their|the)\s+glucose\s+(?:levels?\s+|readings?\s+)?"
    r"(?:of\s+|:\s*)?" + _A_LOW_FIGURE,
    # and the measurement noun on its own, with no possessive in front of it: "glucose level
    # 3.2", "glucose reading 2.4". The word "level" or "reading" is the fence that keeps a
    # recipe's "glucose 3 tbsp" out, so this arm may read the figure without a verb or a
    # determiner - it was the third pattern's own shape, and folding it into the arm above
    # dropped "glucose level 3.2" to "I'm listening". Found in review by @zippy-kangaroo.
    r"\bglucose\s+(?:levels?|readings?)\s+(?:is\s+|was\s+|of\s+|:\s*)?" + _A_LOW_FIGURE,
)

HYPO_SIGN = (
    # "im having a hypo" carries no sign word at all, and it is the plainest way to say it.
    # The subject is what makes it now: "im having a hypo" and "my dad is having a hypo" are the
    # hypo itself, while "how do i avoid having a hypo" is a question about prevention, and it was
    # getting this card.
    r"\b(?:im|i'?m|am|is|are|'s|'re|hes|he'?s|shes|she'?s|theyre|they'?re|youre|you'?re|"
    r"was|were)\s+(?:having|getting|going\s+into)\s+(?:a\s+|another\s+)?hypo\b",
    r"\b(?:and|then|now)\s+(?:(?:hes|he'?s|shes|she'?s|theyre|they'?re|im)\s+)?"
    r"(?:having|getting|going\s+into)\s+(?:a\s+|another\s+)?hypo\b",
    r"\bthink\s+(?:i'?m|im|i\s+am)\s+(?:having|getting)\s+(?:a\s+|another\s+)?hypo\b",
    r"\bconfus\w*", r"\bdisorient\w*", r"\bsweat\w*", r"\bclammy\b", r"\bshak\w*",
    r"\btrembl\w*", r"\bjitter\w*", r"\bdrows\w*", r"\b(?:very\s+)?sleepy\b",
    r"\bslurr\w*", r"\bacting\s+(?:drunk|odd|strange|weird|pissed|funny)\b",
    r"\bnot\s+(?:him|her|them|himself|herself|themselves)\b", r"\bwobbly\b",
    r"\b(?:pale|grey|gray|white)\s+as\s+a\s+sheet\b", r"\b(?:won'?t|wont)\s+wake\b",
    r"\bfeels?\s+(?:faint|funny|wobbly|drunk)\b", r"\bcan'?t\s+stay\s+awake\b",
    # A hypoglycaemia that has gone further: a faint, a fit, or a person who will not rouse.
    r"\b(?:passed|passing)\s+out\b", r"\b(?:blacked|blacking)\s+out\b", r"\bout\s+cold\b",
    r"\bfaint\w*", r"\bcollaps\w*", r"\bkeel\w*\s+over\b", r"\ba\s+fit\b",
    r"\bseizure\w*", r"\bconvuls\w*", r"\bcoma\b", r"\bunconscious\b", r"\bunresponsive\b",
    r"\bnot\s+making\s+(?:any\s+)?sense\b", r"\bgibberish\b",
    r"\b(?:talking|talked|saying)\s+(?:nonsense|rubbish)\b",
    # The meter is the sign, and a reading under 4 is a hypo whatever the person says about it.
    # This was written as "2 or 3", so it caught 2.4 and 3.9 - the leading digit was the rule -
    # and missed every reading that starts with 1, which is exactly the reading that cannot wait:
    # "my blood sugar is 1.9" was answered with the target range. The figure is matched by its
    # shape rather than by the digits people usually send, and the verb is still required so a
    # recipe's "sugar 3 tbsp" is not a hypo.
    *SUGAR_READING_LOW,
    r"\b(?:blood\s+)?(?:sugars?|glucose)\s+(?:is\s+|was\s+|has\s+|have\s+|had\s+|levels?\s+(?:is\s+|are\s+)?)?"
    r"(?:low|dropped|dropping|dipped|crashing|too\s+low)\b",
    r"\b(?:blood\s+)?(?:sugars?|glucose)\s+level\w*\s+(?:is\s+|are\s+)?(?:low|dropping|dropped)\b",
    r"\b(?:blood\s+)?glucose\s+(?:is\s+|was\s+)?(?:falling|fallen|plummet\w*)\b",
)

SELF_HARM_REPEAT_CAUSE = (
    # the thing that did it: a device, a hot surface, a tool, a chemical
    r"\b(?:boiler|wifi|wi-?fi|internet|router|broadband|signal|connection|car|van|engine|motorbike|"
    r"bike|mower|lawnmower|laptop|phone|computer|screen|tv|telly|radio|fridge|freezer|fan|"
    r"washing\s+machine|dishwasher|dryer|heater|radiator|heating|oven|hob|cooker|grill|kettle|"
    r"toaster|iron|straighteners|hairdryer|hair\s+dryer|light|lights|bulb|plug|socket|charger|"
    r"cable|battery|drill|saw|knife|blade|glass|bleach|acid|pan|pot|plate|shower|tap|mattress|"
    r"brakes?|clutch|gears?|fuse|power|electricity|sun|sunburn|candle|lighter|fire|barbecue|"
    r"barbeque|stove|radiator|ice|snow|shelf|shelves|cupboard|ceiling|door|desk|chair|sofa|"
    r"table|worktop|counter|bed|floor|stairs|nails?)\b",
    # or a skin condition, which explains the scratching: "i keep scratching my arms with eczema"
    r"\b(?:eczema|psoriasis|dandruff|rash|itch\w*|dry\s+skin|allergy|allergic|hives|heating|"
    r"in\s+the\s+night|at\s+night|in\s+my\s+sleep)\b",
    # or the effort that did it, said as a cause rather than as a wish
    r"\b(?:lifting|carrying|moving|shifting|digging|painting|gardening|running|jogging|walking|"
    r" cycling|swimming|exercising|training|playing|football|rugby|netball|gym|workout|squats?|"
    r"deadlifts?|weights|boxes?|furniture|bags?|shopping|hoovering|cleaning|scrubbing|typing|"
    r"at\s+work|in\s+the\s+garden)\b",
    # A time alone explains nothing: "i keep cutting my arms after my mum shouts at me" and
    # "i keep banging my head on the wall when i get upset" are still ways of hurting yourself.
    # Only the effort that did it counts, so the time word has to carry one.
    r"\b(?:after\s+(?:work|the\s+gym|a\s+run|a\s+walk|lifting|football|netball|rugby|a\s+shift|"
    r"the\s+shopping)|when\s+i\s+(?:lift|run|cycle|walk|play|train|work\s+out|carry|exercise|"
    r"climb|swim|dig|garden))\b",
)

FOLLOW_UP = (
    r"\bwhile\s+(?:we|i|they|you)\s+wait\b", r"\bwhat\s+(?:do|should)\s+(?:i|we)\s+do\b",
    r"\bwhat\s+now\b", r"\banything\s+else\b", r"\bis\s+(?:that|it|this)\s+(?:ok|okay|right|normal|safe|dangerous)\b",
    r"\bis\s+it\s+safe\s+to\b", r"\bthe\s+ambulance\b", r"\bthey'?re\s+(?:coming|on\s+their\s+way)\b",
    r"\bhelp\s+is\s+(?:coming|on\s+the\s+way)\b", r"\bstill\s+waiting\b",
    r"\bshould\s+i\s+(?:use|give|move|leave|go|call|keep|do|put|take|wash|clean|rinse|cover|wrap|bandage)\b",
    r"\bcan\s+i\s+(?:give|move|leave|go|use|do|put|take|wash|clean|rinse|cover|wrap|bandage|walk|stand|sit|lie|help|carry)\b",
    r"\bwhat\s+(?:else\s+)?can\s+i\s+do\b", r"\bkeep\s+(?:them|him|her)\s+(?:warm|still|awake)\b",
    r"\b(?:cpr|dispatcher|call\s+handler)\b", r"\b(?:breathing|feels?|looks?|seems?)\s+(?:better|easier|worse|normally|again)\b",
    r"\bthey\s+(?:seem|look|are)\s+(?:better|worse|okay|ok)\b",
    r"\b(?:i'm|im|we're|we\s+are|i\s+am)\s+(?:outside|out|safe|clear)\b",
    r"\b(?:fire\s+(?:brigade|service|fighters?)|paramedics?|ambulance)\b",
    r"\b(?:he|she|they|it)(?:'s|'re|\s+is|\s+are)\s+(?:awake|breathing|okay|ok)\b",
    r"\b(?:it|the\s+bleeding)\s+(?:has\s+)?stopped\b",
    r"\b(?:called|rang|phoned)\s+(?:999|911|112)\b", r"\bon\s+(?:the\s+phone|hold)\b",
    r"\b(?:still|really)\s+(?:scared|frightened|terrified|afraid|shaky|panicking|panicky)\b",
    r"\bstill\s+(?:soaking|bleeding|coming|pouring)\b", r"\bsoaking\s+through\b",
    r"\bit'?s\s+still\s+\w+ing\b",
    r"\bshould\s+i\s+(?:try|open|shut|close|turn|grab|hold|press|cover|warm|sit|lie|stand|walk|drive|eat|drink|wake|ring|phone|tell|say|text|message|put|take|wash|clean|rinse|wrap|bandage)\b",
    r"\bcan\s+i\s+(?:open|shut|close|turn|give|move|go|drive|eat|drink|wake|ring|phone|put|take|wash|clean|rinse|cover|wrap|bandage|walk|stand|sit|lie|help|leave|try|carry|hold|press)\b",
    r"\bis\s+it\s+(?:ok|okay|safe|alright|fine)\s+to\b",
)

# A limp that has been there for years is the same appointment as one that has been there for a
# month: the six-week card above is the answer, not ice. Nobody has a knock last since childhood,
# so the limbs list and the "since he was little" shapes are read as what they are.
LIMP_ONGOING = (
    # "my ms" and never "ms jenkins": the two letters are a name and a title as often as they are
    # the illness, so the possessive is what makes them the cause.
    r"\b(?:my|his|her|their|the|your)\s+ms\b", r"\bmultiple\s+sclerosis\b",
    r"\bparkinsons?\b", r"\bparkinson'?s\b", r"\b(?:brain|head|spinal)\s+injur\w+",
    r"\bcerebral\s+palsy\b", r"\bspina\s+bifida\b", r"\bmuscular\s+dystrophy\b",
    # A prosthetic is only a limp's cause when it is a leg: a prosthetic eye, a glass eye or a
    # false tooth is not why walking hurts, and "my prosthetic eye is sore" was answered with the
    # weeks-to-the-GP limp card. "prosthesis" without a limb after it is left to the part's own
    # entry.
    r"\bamputat\w+\b",
    # The limb can be either side of the prosthesis word: "my prosthetic leg" and "my leg
    # prosthesis" are the same question, and reading only the word after the prosthesis turned
    # a sore leg prosthesis into a pulled muscle.
    r"\bprosthe\w+\s+(?:leg|legs|limb|limbs|knee|knees|ankle|ankles|foot|feet|hip|hips|"
    r"thigh|thighs|calf|calves)\b",
    r"\b(?:leg|legs|limb|limbs|knee|knees|ankle|ankles|foot|feet|hip|hips|thigh|thighs|"
    r"calf|calves)\s+prosthe\w+",
    # A prosthesis with no part named is still the long-standing cause a limp is asked about.
    # A named eye is not - it is the eye's own question - whichever side of the word it sits
    # on, so the bare reading stands down for that one part only.
    r"(?<!eye )(?<!ocular )\bprosthe\w+\b(?!\s+(?:eye|eyes|eyeball|socket))",
    r"\bpolio\b", r"\bdrop\s+foot\b",
    r"\bsince\s+(?:he|she|they|i)\s+(?:was|were)\s+(?:little|born|a\s+baby|small)\b",
    r"\bsince\s+(?:birth|childhood|i\s+was\s+born|he\s+was\s+born|she\s+was\s+born)\b",
    r"\b(?:all|all\s+of)\s+(?:my|his|her|their)\s+life\b",
    # "i was born with a limp": lifelong, so the appointment and not the ice (alert-cat).
    # "born blind" is the same history and the eye's own row reads it too: "i was born blind in one
    # eye" stood the stroke card down and then had nothing left to answer it (patient-lychee).
    r"\bborn\s+(?:blind|with)\b",
)

# A bare "should i call an ambulance" is a person wondering whether this is an emergency, not a
# decision to weigh. The composer read it as a big decision - "Can't call that one for you, sorry.
# Say what you'd lose either way" - and "should i call 999" got "Not one I can call for you".
# Wondering is the whole line here: a question with a symptom in it ("when should i call an
# ambulance for a fever") or a subject ("should i call 999 about my neighbour's music") keeps its
# own answer, because those are first-aid and noise questions, not this one.
SHOULD_I_CALL = (
    r"^[\s,]*(?:so|ok|okay|right|well|then)?[\s,]*"
    r"(?:do\s+you\s+think|i\s+think|honestly|really)?[\s,]*"
    r"(?:i|we)?\s*(?:should|shall|do)\s*(?:i|we)?\s*(?:call|ring|phone|dial)\s+(?:an?\s+)?"
    r"(?:ambulance|999|911|112|emergency\s+services)\b"
    r"[\s?!.]*(?:please|thanks|thank\s+you|or\s+not|yes\s+or\s+no)?[\s?!.]*$",
    # The same question with the other option in it: "should i call an ambulance or drive him",
    # "should i ring 999 or go to a and e". The choice is the reason they are asking, and the
    # answer to the choice is the same one.
    r"^[\s,]*(?:should|shall|do)\s+(?:i|we)\s+(?:call|ring|phone|dial)\s+(?:an?\s+)?"
    r"(?:ambulance|999|911|112|emergency\s+services)\b[^?.!]*"
    r"\b(?:or|otherwise)\b[^?.!]*[?!.]*$",
    # "is that a 999 job" is the same question from the other end.
    r"^[\s,]*(?:is|isnt|isn'?t)\s+(?:that|this|it)\s+(?:really\s+)?(?:a\s+)?"
    r"(?:999|911|112)\s+job\b[\s?!.]*$",
    # "do i need to call an ambulance" and the shorter "do i need an ambulance" are the same
    # question said the other way round, and a "do you think" lead can come before them too.
    r"^[\s,]*(?:so|ok|okay|right|well|then)?[\s,]*"
    r"(?:do\s+you\s+think|i\s+think|honestly|really)?[\s,]*"
    r"(?:should|shall|do)?\s*(?:i|we)?\s*(?:need\s+to|have\s+to|bother(?:\s+\w+)?)\s*"
    r"(?:calling|ringing|phoning|dialing|dialling|call|ring|phone|dial)?[\s,]*\s*(?:an?\s+)?"
    r"(?:ambulance|999|911|112|emergency\s+services)\b"
    r"[\s?!.]*(?:please|thanks|or\s+not|yes\s+or\s+no)?[\s?!.]*$",
    # ...and with no verb at all: "do i need an ambulance".
    r"^[\s,]*(?:so|ok|okay|right|well|then)?[\s,]*"
    r"(?:do\s+you\s+think|i\s+think|honestly|really)?[\s,]*"
    r"(?:do\s+i\s+|do\s+we\s+|i\s+)?(?:need|needs|want|wants)\s+(?:an?\s+)?"
    r"(?:ambulance|999|911|112|emergency\s+services)\b"
    r"[\s?!.]*(?:please|thanks|or\s+not|yes\s+or\s+no)?[\s?!.]*$",
)

# The laugh in every tense and with no tense at all: "i was killing myself laughing yesterday",
# "i nearly killed myself laughing", and the bare "killing myself laughing at this video", which
# was getting the crisis card too. Spelled once so the stand-down can ask for this arm by name.
# The wish said as a shrug, which is how a person writes it after a near thing: "i nearly killed
# myself at the pool and honestly i dont care if i live", "i almost killed myself driving home and i
# wish i had crashed", "i nearly killed myself moving house, i cant do this anymore". None of these
# name a wish in the shape WISH_NAMED and DESPAIR look for, so they were reaching the near-thing
# reply, which offers ice for a back. Whatever the near thing was, the sentence after it is the one
# that decides the turn.
NOT_JUST_A_NEAR_THING = (
    r"\b(?:i\s+)?(?:just\s+)?(?:cant|can'?t|couldnt|couldn'?t)\s+"
    r"(?:do\s+(?:this|it)|take\s+(?:it|this)|go\s+on|carry\s+on|keep\s+going|keep\s+on)\s*"
    r"(?:any\s?more|anymore)\b",
    r"\b(?:i\s+)?(?:just\s+)?(?:don'?t|dont|do\s+not)\s+care\s+"
    r"(?:if\s+i\s+(?:live|die|wake|make\s+it|survive)\b|any\s?more\b|anymore\b|"
    r"about\s+(?:anything|myself|it)\b|whether\s+i\s+(?:live|die)\b)",
    r"\b(?:i\s+)?(?:just\s+)?(?:feel|feeling|felt|am|im)\s+(?:so\s+|really\s+|totally\s+)?"
    r"(?:empty|numb|hollow|dead\s+inside)\b",
    r"\bwish\s+(?:i|it|that\s+i|the\s+car|that\s+car)\b[^.?!]{0,24}"
    r"\b(?:crashed|died|gone\s+through|not\s+woken|killed\s+me|hit\s+me|"
    r"finished\s+it|done\s+it|succeeded|worked)\b",
    r"\b(?:would|would'?ve|would\s+have)\s+(?:be\s+)?(?:better|easier)\s+if\s+i\b",
    r"\b(?:i\s+)?(?:honestly\s+)?(?:don'?t|dont)\s+want\s+to\s+be\s+here\b",
    r"\bnot\s+worth\s+(?:being\s+here|carrying\s+on|going\s+on)\b",
    r"\b(?:havent|have\s+not)\s+(?:got\s+)?(?:anything|much)\s+left\b",
    # The same shrug in the words a person reaches for when the near thing was not a joke and not a
    # job: "i was killing myself laughing and i hate myself", "and i wish i wasnt here", "i nearly
    # killed myself running for the bus and i want to disappear". These are read out of the line
    # once the idiom itself is cut away, which is what _rest_of_it_rings does.
    r"\b(?:i\s+)?(?:really\s+|just\s+|honestly\s+|so\s+)?hate\s+my\s*self\b",
    r"\bwish\s+(?:i|that\s+i)\s+(?:wasnt|wasn'?t|werent|weren'?t|was\s+not|were\s+not)\b",
    r"\b(?:want|wanted|wanna|wishing|wish)\s+(?:to\s+)?(?:disappear|vanish|"
    r"stop\s+existing|cease\s+to\s+exist|not\s+exist|be\s+gone|be\s+dead|be\s+here\s+any\s?more)\b",
    r"\b(?:cant|can'?t|couldnt|couldn'?t)\s+(?:take|stand)\s+(?:it|this|much\s+more)\b",
    r"\bnot\s+(?:wake|waking)\s+up\b",
)

# A person's limp, never a vegetable's: "the celery has gone limp" and "my dog is limping" are the
# cooking and the pets rows' lines, and this module is above both of them.
LIMP_PERSON = (
    r"\b(?:i|he|she|they|we)\s+(?:am|is|are|was|were|have\s+been|has\s+been)\s+"
    r"(?:still\s+|now\s+|really\s+|badly\s+|left\s+)?limp(?:ing)?\b",
    r"\bmy\s+(?:son|daughter|child|boy|girl|kid|toddler|baby|husband|wife|partner|mum|mom|dad|"
    r"mother|father|nan|grandad|grandma|grandson|granddaughter|niece|nephew|friend|sister|brother)"
    r"\s+(?:is|was|keeps?|has\s+been|had\s+been)\s+(?:still\s+)?limp(?:ing)?\b",
    # a named person who limps: "my son limps when he is tired" is the same leg as "is limping"
    r"\b(?:son|daughter|child|boy|girl|kid|toddler|baby|husband|wife|partner|mum|mom|dad|mother|"
    r"father|nan|nana|grandad|grandma|grandson|granddaughter|niece|nephew|friend|sister|brother)"
    r"\s+limp(?:s|ed)\b",
    r"\b(?:i|he|she)\s+limp(?:s|ed)\b",
    r"\b(?:keeps?\s+limping|started\s+limping|stop\s+limping|stopped\s+limping|been\s+limping|"
    r"still\s+limping|stop\s+(?:\w+\s+){0,2}limping)\b",
    # "my son limping when he runs", "her leg limping": a body part or a person, then the gait
    r"\b(?:my|his|her|their|our)\s+(?:\w+\s+){0,2}limp(?:ing)\b",
    # The noun rather than the gait: "my son has a limp", "she has got a limp", "my dad walks with
    # a limp". Every pattern above wants the -ing or the -s, so the plainest way people say it was
    # the one that got "Noted: your son has a limp." back.
    r"\b(?:has|have|had|has\s+got|have\s+got|had\s+got|developed|developing|been\s+left\s+with)"
    r"\s+(?:a\s+|an\s+|this\s+|that\s+)?(?:bad\s+|slight\s+|really\s+|sore\s+)?limp\b",
    r"\b(?:walks|walking|walked|hobbles|hobbling)\s+with\s+(?:a\s+|this\s+)?limp\b",
    # "hes got a limp", "ive got a limp": the apostrophe-less form the matcher sees.
    r"\bgot\s+(?:a\s+|this\s+)?(?:bad\s+|slight\s+)?limp\b",
    r"\bwith\s+(?:a\s+)?(?:bad\s+|slight\s+)?limp\b",
    r"\b(?:leg|knee|ankle|foot|hip|back)\s+(?:is\s+)?limp(?:ing)?\b",
)

# A handover is why an ex is outside the house, and the doorstep is where it happens.
PURSUIT_FINE = (
    r"\b(?:to|with|for)\s+(?:the\s+)?(?:kids|children|child|dog|stuff|things|bags)\b",
    r"\b(?:dropping|dropped|drop)\s+(?:off|the|it|them)\b",
    r"\b(?:picking|picked|pick)\s+(?:up|the|them)\b",
    r"\b(?:handover|hand\s*over|collecting|collected|collect)\b",
    r"\b(?:comes|coming|came)\s+(?:to|for|round)\b",
    # A partner outside your work is usually the lift home, and one banging on the door is usually
    # locked out of it. Both are named, so both stand the card down while the fear takes it back.
    r"\b(?:pick(?:ing|ed|s)?\s+(?:me|us|him|her|them)\s+up|pick\s*-?\s*up|"
    r"lift\s+(?:home|to\s+work|back)|give\s+(?:me|us|him|her|them)\s+a\s+lift|"
    r"for\s+a\s+lift|to\s+be\s+let\s+in|let\s+(?:me|us|him|her)\s+in|"
    r"locked\s+(?:out|himself\s+out|herself\s+out))\b",
    # A follow on an app is a follow: "he is following me on instagram", "shes stalking me on
    # facebook". The word carries the place the person is not in.
    r"\b(?:follow\w*|stalk\w*)\s+(?:me|us)\b[^.?!]{0,12}\b(?:instagram|insta|facebook|fb|"
    r"twitter|tiktok|socials?|social\s+media|linkedin|youtube|reddit|snapchat|strava|whatsapp|"
    r"threads)\b",
    # A husband outside the school at three o'clock is the pick-up, and a wife outside the office
    # is waiting for the lift home: the place you are expected at only counts for an ex.
    r"\b(?:husband|wife|partner|boyfriend|girlfriend|fiance|fiancee)\b[^.?!]{0,30}"
    r"\b(?:outside|at|near|by)\s+(?:the|her|his|their)\s+(?:school|work|office|nursery|"
    r"college|uni|university|gates?)\b",
    # The fear about a time is not the fear about a person.
    r"\b(?:scared|frightened|worried|afraid|panicking|nervous)\b[^.?!]{0,30}\b(?:late|"
    r"on\s+time|in\s+trouble)\b",
    r"\b(?:shouting|yelling|screaming)\s+at\s+(?:the\s+)?(?:football|telly|tv|match|game|"
    r"radio|news|ref|referee)\b",
)  # end PURSUIT_FINE

# The things that have an arm or a leg of their own: spectacles, furniture, a screen on a stand.
LIMB_IS_A_THING = (
    r"\b(?:arm|leg)\s+(?:of|on)\s+(?:my|the|our|his|her|their|your)\s+"
    # "the leg of my new sofa is bent" puts an adjective in the way, and the word after it is
    # still the thing the leg belongs to.
    r"(?:[\w-]+\s+){0,2}"
    r"(?:glasses|specs|spectacles|sunglasses|monitor|screen|telly|tv|lamp|light|tripod|mirror|"
    r"chair|table|desk|sofa|settee|stool|bed|shelf|shelves|gate|door|bike|scooter|guitar|"
    r"violin|rack|stand|pram|pushchair|buggy|"
    # clothes have arms and legs of their own, and a garment's leg is a seam: "the leg of my
    # jeans is bent" was told to stay where it was and ring 999.
    r"jeans|trousers|pants|joggers|jogging bottoms|leggings|shorts|chinos|cords|combats|"
    r"pyjamas|pyjama bottoms|pjamas|pjs|tights|skirt|dress|dresses|shirt|shirts|coat|coats|"
    r"jacket|jackets|sock|socks|boot|boots|shoe|shoes|slipper|slippers)\b",
    r"\b(?:glasses|specs|spectacles|sunglasses|monitor|screen|chair|table|desk|sofa|settee|"
    r"stool|lamp|tripod|mirror|pram|pushchair|buggy|guitar|violin|bike|scooter|"
    r"jeans|trousers|leggings|shorts|pyjamas|jacket|coat|shirt|dress)\b"
    r"(?:'s)?\s+(?:arm|leg)\b",
    r"\b(?:the|a|my|our|his|her|their|your)\s+(?:glasses|specs|spectacles|sunglasses|chair|"
    r"table|desk|sofa|settee|stool|lamp|monitor|screen|tripod|mirror|pram|pushchair|buggy|"
    r"jeans|trousers|leggings|shorts|pyjamas|jacket|coat|shirt|dress)\b"
    r"[^.?!]{0,20}\b(?:bent|deformed)\b",
    # ...and the same thing said the other way round, which is how most people write it: "my
    # trouser leg is bent", "my jacket arm is bent". The thing comes first and owns the limb.
    r"\b(?:trouser|trousers|jeans|jean|pyjama|pyjamas|pajama|pajamas|jacket|shirt|coat|sleeve|"
    r"chair|table|sofa|settee|desk|stool|lamp|monitor|screen|glasses|door|gate)\s+"
    r"(?:leg|legs|arm|arms)\b",
)

# ...unless the line says more than play: where it landed, what it felt like, what it left, or that
# it keeps happening.
HIT_IN_FUN_HARD = (
    # The laugh has to be the two of them. A laugh in the speaker's own clause is what a victim's
    # line says too - "i was laughing and he hit me", "he hit me while i was laughing", "i was
    # laughing at his joke and he slapped me" - so the speaker's own laugh rings the card again
    # (cream-eel's one-liner, measured over 2,339 deck first turns: 0 changed).
    r"\bi\s+(?:just\s+|was\s+|were\s+|am\s+)?laugh(?:ing|ed|s)?\b",
    # Same clause, same reason: a blow that lands because the speaker was joking is about
    # something, not play between two people. "he hit me while i was joking with him" and "he hit
    # me and i was kidding around" were the play reply. A shared laugh still stands the card
    # down - "we were laughing" is the two of them - so the lookahead keeps those lines out.
    r"\bi\s+(?:just\s+|was\s+|were\s+|am\s+)?(?:only\s+|just\s+)?(?:joking|kidding|kiddin)\b"
    r"(?![^.?!]*\bwe\s+(?:both\s+)?(?:laughed|were\s+laughing|laughing)\b)",
    r"\bwhile\s+(?:i\s+was\s+)?(?:joking|kidding)\b"
    r"(?![^.?!]*\bwe\s+(?:both\s+)?(?:laughed|were\s+laughing|laughing)\b)",
    # What it felt like is already in the list for "it really hurt"; a sting is the same evidence
    # and "he slapped my leg while we were playing, it stung" was the play reply (zippy).
    r"\bit\s+(?:stung|stings?|hurt|hurts|smarts?|throbs?|burn(?:s|ed)?)\b",
    # "my husband hit me during play" is not the game either: play named as a period, not as what
    # the two of them were doing together.
    r"\bduring\s+(?:the\s+)?play\b",
    r"\b(?:face|head|throat|neck|nose|eyes?|jaw|ribs?|stomach|belly|genitals?|chest)\b",
    r"\b(?:hard|harder|really\s+hurt|properly|painful|bruis\w*|blood|bled|bleeding|mark)\b",
    r"\b(?:afraid|scared|frightened|terrified)\b",
    r"\b(?:wouldn'?t\s+stop|didn'?t\s+stop|kept\s+(?:on|going)|not\s+the\s+first\s+time|"
    r"every\s+day|all\s+the\s+time)\b",
    # A blow that keeps happening is not one joke gone wrong. The list had "every day" and "all
    # the time" and nothing else, so "he hits me every time we play fight", "he always hits me
    # when we play", "he hit me whenever we joke around" were all the play reply: the recurrence
    # is the shape people are told to watch for, and the game is the setting, not the reason
    # (pink-lime, 81228).
    r"\b(?:every\s+(?:single\s+)?(?:time|week|night|month|birthday)|each\s+time|"
    r"whenever|constantly|regularly|"
    r"always\s+(?:hits?|hit|slapp?(?:s|ped)?|punch(?:es|ed)?|kick(?:s|ed)?|shov(?:es|ed)|"
    r"push(?:es|ed)|beats?|hurts?))\b",
    r"\b(?:knife|belt|bottle|weapon|stick|pan|chair|bat)\b",
    # "and then said it was a joke" is the other person's claim, not the speaker's framing: the
    # words people are told to accept are not the words that make a hit play. See PLAY_CLAIMED.
    r"\b(?:said|says|saying|say|called|calls|calling|claimed|claims|claiming|told|tells|telling)"
    r"\b[^.?!]{0,25}\b(?:joke|joking|laugh|laughing|fun|banter|mess(?:ing)?\s+about)\b",
    r"\b(?:it\s+was|it\s+were)\s+(?:only\s+|just\s+|all\s+)?(?:a\s+)?"
    r"(?:joke|joking|banter|laugh)\b",
    r"\b(?:only|just)\s+joking\b",
    # Play is a hand, not a fall: stairs, a road, a dropped body. A shove that put somebody on the
    # floor is the card whatever the line calls it.
    r"\b(?:down\s+the\s+stairs|downstairs|fell|fallen|falling|fell\s+over|tripped\s+me|"
    r"knocked\s+me\s+(?:over|down)|off\s+the\s+(?:ladder|chair|bike)|into\s+the\s+road)\b",
)

# The way into the water, which is what people type. DROWNING knew the word "drowning" and the
# pronoun pulled out of the water, so the entry itself was read as something else entirely:
# "my baby slipped under the water" and "he slipped under the water" were the fracture card
# ("is it just bruising, or is something not right"), "my son went under the water" and
# "my daughter was pulled out of the water" were the toddler's daily fluids, and "the baby is face
# down in the bath" was how to run a bath. A person under the surface is a drowning however the
# verb put them there, and the water is what makes it the water.
WATER_DANGER = (
    # under the surface
    r"\b(?:under|below)\s+(?:the\s+|his\s+|her\s+|their\s+)?(?:water|surface)\b",
    # in, or into, a body of water that is not a bath: a slip in the bath is a fall
    r"\b(?:fell|fallen|falls?|went|goes|gone|slipped|slips?|dropped|drops?|jumped|jumps?|pushed|"
    r"pushed\s+in|tipped|tumbled|sank|sunk|wa(s|s)\s+in|were\s+in|is\s+in|went\s+in)\b"
    r"[^.?!]{0,20}\b(?:in|into)\s+(?:the\s+)?(?:water|pond|river|lake|sea|canal|pool|stream|"
    r"reservoir|loch|harbour|harbor|lagoon|deep\s+end|shallow\s+end)\b",
    # gone under on its own
    r"\b(?:went\s+under|goes\s+under|gone\s+under|disappeared\s+under|underwater)\b",
    # A sinking is not the water by itself: "my heart sank when i saw the letter" and "i sank into
    # the sofa" are how people say a bad morning, and the bare `sank` arm rang 999 on both. The
    # sinking has to name the water or the depth.
    r"\b(?:sank|sunk|sinking)\s+(?:under|below|to\s+the\s+bottom)\b",
    r"\b(?:sank|sunk|sinking)\s+(?:in|into)\s+the\s+(?:water|pond|river|lake|sea|canal|pool|"
    r"stream|reservoir|loch|harbour|harbor|lagoon)\b",
    # ...and a small child under the water in the bath is the one a bath-safety sentence must keep:
    # a slip in the bath is a fall, but "the baby slipped under in the bath" is not.
    r"\b(?:slipped|slips?|fell|fallen|sank|sunk|tipped|tumbled|rolled)\s+under\b"
    r"[^.?!]{0,25}\b(?:bath|tub)\b",
    r"\b(?:bath|tub)\b[^.?!]{0,20}\b(?:went|goes|gone|sank|sunk|slips?|slipped|fell|fallen)"
    r"\s+under\b",
    # and how long is the thing that matters: "he was under for two minutes"
    r"\bunder\s+for\s+(?:\d+|a\s+few|several|two|three|four|five|ten|twenty|thirty)\s*"
    r"(?:seconds?|secs?|minutes?|mins?)\b",
    # face down in it
    r"\bface\s+down\b[^.?!]{0,20}\b(?:water|bath|tub|pool|pond)\b",
    # in the water and lost to sight, in either order: "i cant see him in the water" puts the
    # asking first, which is how a frightened person types it
    r"\bin\s+the\s+water\b[^.?!]{0,30}\bcan'?t\s+see\b",
    r"\b(?:can'?t|cant|couldn'?t|could\s+not)\s+see\b[^.?!]{0,25}\b(?:in|under)\s+"
    r"(?:the\s+)?(?:water|pool|sea|pond|river|lake|canal)\b",
    # pulled or lifted out of it
    r"\b(?:pulled|drags?|dragged|lifted|hauled|got|gets|getting|fished)\s+(?:[\w']+\s+){0,3}"
    r"out\s+of\s+the\s+(?:water|pool|sea|pond|river|lake|canal)\b",
    # "i nearly drowned in the sea" went to the old drowning card, which is written to somebody
    # standing over the person: the water word makes it this case, and the speaker gets their own.
    r"\bnearly\s+drowned\b[^.?!]{0,20}\b(?:water|pond|river|lake|sea|pool|canal|reservoir|"
    r"loch|deep\s+end|bath|tub)\b",
)

# The things a pet damages: a scratched sofa, a chewed slipper, a pulled-down curtain. Everything
# else the teeth or claws land on is read as a person, because the two mistakes are not equal - a
# clean cloth on a scratched cushion wastes ten seconds, and a scratching-post tip for a scratched
# nephew is the bot failing at the one thing it exists for. So this is the list that stands the
# wound arm down, not a list of the people who need it.
_PET_DAMAGE_THING = (
    r"(?:sofas?|couches?|settees?|armchairs?|chairs?|stools?|seats?|curtains?|blinds?|carpets?|"
    r"rugs?|mats?|bedding|duvet|pillows?|cushions?|blankets?|throws?|towels?|linen|"
    r"clothes|jumpers?|cardigans?|shirts?|dress(?:es)?|trousers|jeans|skirts?|coats?|jackets?|"
    r"sleeves?|socks?|tights|shoes?|slippers?|trainers?|boots?|laces?|shoelaces?|hats?|scarves?|"
    r"bags?|rucksacks?|backpacks?|handbags?|wallets?|purses?|phones?|mobiles?|cables?|chargers?|"
    r"wires?|leads?|laptops?|keyboards?|mice|remotes?|tvs?|televisions?|screens?|monitors?|"
    r"headphones|speakers?|wallpaper|walls?|doors?|doorways?|doorframes?|skirtings?|paint|floors?|"
    r"floorboards?|tables?|desks?|shelves|shelf|bookcases?|cupboards?|wardrobes?|cabinets?|"
    r"worktops?|counters?|sideboards?|garden|lawn|grass|fences?|gates?|sheds?|decking|patios?|"
    r"plants?|flowers?|houseplants?|trees?|bark|scratch\s*posts?|posts?|toys?|tunnels?|carpet|"
    r"furniture|woodwork|paintwork|bannister|banister|radiator|switch|light\s*switch)"
)

# A bleed that is not the ambulance-sized one, but still wants first aid: your own cut, or anyone
# else's - "my dad is bleeding and it won't stop".
BLEEDING_SMALL = (
    r"\b(?:he|she|they|his|her|their|my\s+(?:dad|mum|mom|father|mother|son|daughter|child|kid|baby|"
    r"husband|wife|partner|brother|sister|nan|gran|grandma|grandad|friend|neighbour|neighbor|boy|"
    r"girl|man|woman|lad|mate|colleague))\b.{0,25}"
    r"\b(?:is|are|'s|was|keeps?|has\s+been)\s+bleeding\b(?!\s+(?:me\s+)?(?:dry|white))",
    # The whole body, not only the parts somebody thought of: "my ear is bleeding", "my cheek is
    # bleeding" and "my mouth is bleeding" were a shrug each. Three parts are left out on purpose
    # because a cloth is the wrong answer to them: the nose has its own pinch-and-lean-forward
    # card, a bleeding gum is gum disease and wants a dentist ("my gum is bleeding" was the cloth
    # here, and main's own gum answer is right), and an eye that bleeds wants A&E today - pressing
    # on it is the one thing not to do.
    r"\b(?:my|his|her|their|your)\s+(?:hand|arm|leg|foot|head|finger|thumb|wrist|knee|elbow|face|"
    r"lip|scalp|shin|shoulder|ear|cheek|mouth|brow|eyebrow|chin|jaw|forearm|upper\s+arm|"
    r"thigh|calf|palm|heel|toe|knuckle|knuckles|belly|chest|neck|back)\s+"
    r"(?:is\s+|are\s+|keeps?\s+|started\s+|won'?t\s+stop\s+)?(?:bleeding|bled)\b",
    r"\b(?:cut|sliced|nicked|gashed|slashed)\b.{0,25}"
    r"\b(?:won'?t|wont|doesn'?t|didn'?t|keeps?)\s+stop\s+bleeding\b",
    # A pet that has bitten or scratched a person is the person's cut, not the vet's night.
    # An animal that is bleeding itself is the vet's, and it is not this arm: "my dog is bleeding a
    # bit from his paw" has the "bit" of "a bit" where the verb goes and "his paw" where the person
    # goes, so it read as a dog that had bitten somebody and a cut on a paw got the person's
    # press-the-cloth-and-999 card.
    r"\b(?:dogs?|cats?|pupp(?:y|ies)|kittens?|pets?)\b"
    r".{0,25}"
    r"\b(?:bit|bitten|scratched|clawed|claw|nicked)\b.{0,20}"
    # What the teeth or claws landed on decides it, the way the hot thing's landing place decides a
    # scald. "my cat scratched my sofa", "her armchair" and "my son's sofa" are damage to a thing,
    # and the answer they want is the scratching post; "my cat scratched my niece", "my toddler" and
    # "my flatmate" are a person's cut. The thing list is read off first, with room for a possessive
    # and a describing word in front of the noun ("my son's sofa", "my best curtains"), and anything
    # else after "my"/"her" is a person: the list that can leave somebody out is the furniture, not
    # the family. A lead-in like "the postman" is left to the bite report, which has its own arm.
    r"\b(?:(?:me|us)\b|(?:him|her|them)\b(?!\s+\w)|"
    r"(?:my|his|her|their|your|our)\s+"
    r"(?!(?:\w+['’]s\s+)?(?:[a-z]+\s+){0,2}(?:" + _PET_DAMAGE_THING + r")\b)\w)",
)

# Who the tooth belongs to: a possessive, or the "a"/"an" a hypothetical is asked with ("what do
# i do if i knock a tooth out").
A_TOOTH_OWNER = (r"(?:my|his|her|their|the|your|our|a|an|son'?s|daughter'?s|kid'?s|child'?s|"
                 r"husband'?s|wife'?s|partner'?s|friend'?s|mum'?s|dad'?s)")

# A tooth that comes out is the dentist's, not the ambulance's. "my tooth got knocked out" matched
# the knock-out arm and got the head-injury 999 reply, which is the wrong number for the one dental
# emergency where the hour matters: a tooth put back inside the hour has the best chance of taking.
# The verbs are written with their endings for the same reason the chipped row is: a person asks
# this as a hypothetical ("what do i do if i knock a tooth out") far more often than in the past
# tense, and the row only knew "knocked", so the bare form was not read at all.
TOOTH_OUT = (
    r"\b" + A_TOOTH_OWNER + r"\s+(?:front\s+|back\s+|adult\s+|baby\s+|milk\s+)?"
    r"(?:tooth|teeth)\b[^.?!]{0,20}"
    r"\b(?:knock(?:ed|s|ing)?\s+out|came\s+out|comes?\s+out|fell\s+out|falls?\s+out|"
    r"is\s+hanging)\b",
    # A tooth that is broken is the chipped row's, not this one: "broke" is deliberately absent
    # from this list, so "he broke a tooth" is never told to put it back in the socket.
    r"\b(?:knock|knocks|knocked|knocking|kick|kicks|kicked|kicking|punch|punches|punched|"
    r"punching|smash|smashes|smashed|smashing)\s+"
    r"(?:my|his|her|their|our|your|a|an|out\s+)\s*(?:front\s+|back\s+)?tooth\b",
    # The verb first and the teeth plural, which is how a parent or an adult child says it:
    # "my son knocked his teeth out on his bike", "i knocked three of my teeth out".
    r"\b(?:knock|knocks|knocked|knocking|kicking|kicked|punch|punched|punching|smash|smashed|"
    r"smashing)\s+(?:my|his|her|their|the|our|your|out\s+)\b[^.?!]{0,18}\bteeth\b",
    r"\b(?:knocked|came|fell)\s+(?:out\s+)?(?:\w+\s+){0,4}(?:teeth|tooth)\b",
    r"\b(?:teeth|tooth)\s+(?:got\s+|were\s+|was\s+|both\s+)?(?:knocked|came|fell)\s+out\b",
)

# A chipped or cracked tooth is not one to put back: it wants a dentist soon, not an ambulance.
#
# Every tense of the four verbs, and the article as well as the possessive. The pattern used to
# list only the past forms ("chipped", "cracked", "broke", "busted", "snapped") and only "my/his/
# her/their", so "what do i do if i break a tooth" - the way most people ask it, in the bare form
# with "a" - reached no card at all and got a shrug, while "i broke my tooth" was answered. The
# bone row was taught the same lesson ("i cracked a rib" was a nod while "i broke a rib" was
# answered) and lists its verbs twice over, cracked|crack|snapped|snap|broke|broken; this is that
# rule for the teeth, so every way of saying one broken tooth meets the same card.
A_TOOTH_DAMAGED = (r"(?:chips?|chipped|chipping|cracks?|cracked|cracking|breaks?|breaking|broke|"
                   r"broken|busts?|busted|busting|snaps?|snapped|snapping)")

TOOTH_CHIPPED = (
    r"\b" + A_TOOTH_OWNER + r"\s+(?:front\s+|back\s+|baby\s+|adult\s+)?"
    r"(?:tooth|teeth)\b[^.?!]{0,20}\b" + A_TOOTH_DAMAGED + r"\b(?!\s*out)",
    r"\b" + A_TOOTH_DAMAGED + r"\s+" + A_TOOTH_OWNER +
    r"\s+(?:front\s+|back\s+|baby\s+|adult\s+)?tooth\b(?!\s*out)",
)

# The joint itself: the ankle, the knee, the foot, the wrist. Not the hip - that one is the femur.
WEIGHT_JOINT = (
    r"\b(?:ankle|ankles|knee|knees|foot|feet|heel|heels|toe|toes|leg|legs|wrist|wrists|hand|"
    r"hands|elbow|elbows|shoulder|shoulders|finger|fingers|thumb|thumbs)\b",
)

# The words people use for a burn on their own skin: a scorch and a singe are burns with another word
# for them, and `i scorched my hand on the iron` was answered with how to press a scorch out of a
# shirt, `i scorched my arm on the hob` with a shrug and `i singed my arm on the gas ring` with the
# price of gas. A scorched shirt, a scorched pan and a scorched tea towel keep their own answers, so a
# body part has to be the word after the verb.
BODY = (
    r"(?:hands?|fingers?|fingertips?|thumbs?|arms?|wrists?|elbows?|tongue|mouth|throat|lips?|"
    r"faces?|cheeks?|nose|ears?|eyes?|feet|foot|toes?|legs?|knees?|shins?|chest|backs?|skin|palms?|"
    r"knuckles?|head|scalp|neck|stomach|belly)\b"
)

SCORCHED_A_PERSON = (
    r"\b(?:scorch(?:ed|es|ing)?|singe(?:d|s|ing)?|scold(?:ed|ing))\s+" r"(?:my|his|her|their|your|our|the|a)\s+" r"(?:(?:left|right|own|whole|poor|other|inner|top)\s+)?" + BODY,
    r"\b(?:a|an|the|this|that)\s+" r"(?:bad|nasty|small|minor|little|sore|red|fresh|ugly)?\s*" r"(?:scorch|singe)(?:\s+marks?)?\s+(?:on|to)\s+(?:my|his|her|their|your|the)\s+" + BODY,
    r"\bmy\s+" + BODY + r"\s+(?:is|are|was|were|got)\s+(?:scorched|singed)\b",
    r"\b(?:scorch(?:ed|es|ing)?|singe(?:d|s|ing)?|scold(?:ed|ing))\s+" r"(?:the\s+)?(?:side|back|top|front|inside|outside|roof|tip)\s+of\s+" r"(?:my|his|her|their|your|our)\s+" + BODY,
    r"\b(?:got|get|gets)\s+(?:scorched|singed)\b[^.?!]{0,25}" r"\b(?:by|on|from|with)\s+(?:the\s+|a\s+|an\s+|my\s+|his\s+|her\s+|some\s+)?" r"(?:steam|sun|iron|hob|grill|oven|fire|flames?|heat|barbecue|bbq|pan|kettle|" r"hot\s+water|oil|saucepan|toaster|sand)\b",
    # ...and a kettle is left out of it: "the kettle fell on my foot" already gets the health
    # module's long burn card, which names a foot and sends a burned foot to a walk-in, and that
    # says more than this one.
    r"(?!(?:.*?)\bkettle\b)" r"\b(?:iron|pan|saucepans?|frying\s+pan|chip\s+pan|grill|oven|tray|baking\s+" r"tray|pot|fryer|toaster|jug|hotplate|cooker)\b[^.?!]{0,25}" r"\b(?:fell|fall|falls|dropped|tipped|tips|slipped|slid|touched|touching|" r"came\s+down|knocked\s+over)\b[^.?!]{0,25}\b(?:on|onto|over|into|across)\s+" r"(?:my|his|her|their|our|your)\s+" + BODY,
    r"(?!(?:.*?)\bkettle\b)" r"\b(?:iron|pan|saucepan|hob|grill|oven|pot|fryer|toaster|tray)\b" r"[^.?!]{0,15}\b(?:touched|touching|brushed|grazed|nicked|caught)\b\s+" r"(?:my|his|her|their|our|your)\s+" + BODY,
    r"\b(?:oil|fat|grease)\b[^.?!]{0,15}\b(?:splash(?:ed|es)?|spat|spits?|popped|" r"sprayed|jumped)\b[^.?!]{0,20}\b(?:on|onto|over)\s+" r"(?:my|his|her|their|our|your)\s+" + BODY,
    r"\b(?:scorch(?:ed|es|ing)?|singe(?:d|s|ing)?|scold(?:ed|ing))\s+" r"(?:me|my\s*self|your\s*self|him\s*self|her\s*self|them\s*selves)\b" r"[^.?!]{0,20}\b(?:on|with)\b",
)

# The body-part list without a leading word boundary, for "a burn on my hand": the possessive in
# front of it already closes the word, and "a burn on my wooden table" is furniture.
BURN_ON_BODY = (
    r"(?:hands?|fingers?|fingertips?|thumbs?|arms?|wrists?|elbows?|tongue|mouth|throat|lips?|"
    r"faces?|cheeks?|nose|ears?|eyes?|feet|foot|toes?|legs?|knees?|shins?|chest|backs?|skin|palms?|"
    r"knuckles?|head|scalp|neck|stomach|belly)\b"
)

# "a burn on my shirt", "a burn on my table", "a burn on it": the burn is a mark on a thing, and
# the burn first aid is the wrong answer to it. The noun arms read a burn "on" or "to" something
# as a person's burn only when what follows is a body part.
NOT_BURN_ON_BODY = (
    r"(?:on|to|in|across)\s+(?:(?:my|his|her|their|your|our|the|a|this|that)\s+)?"
    r"(?!" + BURN_ON_BODY + r"|me\b|him\b|her\b|them\b|us\b|myself\b|yourself\b)\w"
)

# The things that burn a hand without needing the word "hot", and the ones that need it. `hot
# plate` is not here on purpose: that is a plate of hot food and the food answer owns it.
HOT_SURFACE = (
    # `cooker` on its own is the slow cooker: "something I can put in the slow cooker" and "can i
    # put my slow cooker pot in the dishwasher" were both the burn card for it.
    r"\b(?:(?:hot\s+)?(?:hob|grill|oven\s+door|oven\s+shelf|hotplate|cooker\s+ring)|"
    r"(?:hot|boiling|scalding|burning)\s+(?:iron|pan|kettle|saucepan|dish|tray|oil|fat|spoon|"
    r"tin|water))\b"
)

# Warm on purpose, and not an injury: a hot water bottle, a heat pack and a hot drink.
HOT_COMFORT = (
    r"\b(?:hot\s+water\s+bottl\w*|ice\s+pack|heat\s+pack|wheat\s+bag|hot\s+towel|"
    r"hot\s+drink|hot\s+chocolate|hot\s+bath|hot\s+shower|hot\s+water\s+tap)\b"
)

# "a cut on my hand", "a graze on my knee", "a scratch on my arm": the injury as a thing the
# person has, rather than as something they did, which is the shape the cut arms above read. The
# body part is what says a person is hurt, so a cut on a wooden table or a scratch on a phone
# screen is not this answer.
# The body parts a cut is named on. Kept apart from A_BODY_PART, which is the reader's, because
# the mouth is out here: a cut tongue wants an ice cube, not a cloth pressed on it.
CUT_BODY_PART = (
    r"(?:hands?|fingers?|fingertips?|thumbs?|arms?|wrists?|elbows?|lips?|faces?|cheeks?|nose|"
    r"ears?|eyes?|forehead|feet|foot|toes?|legs?|knees?|shins?|chest|palms?|knuckles?|head|scalp|"
    r"neck|stomach|belly|thighs?|calves|calf|heels?|shins?|ankles?|shoulders?|forearms?|skin)s?\b"
)

# An animal named as the one who has the wound: "the dog has a small cut on its paw" is the
# vet's, and the size word is the only thing here that could reach the person's first aid.
# The animal that owns the wound, which is not the same as a line that mentions one: a cut on a
# cat's ear is the animal's, and "i have a cut on my ear from the dog" is still mine.
PET_OWNS_THE_WOUND = (
    r"(?:my|our|the|his|her|their)\s+(?:dog|dogs|cat|cats|puppy|puppies|kitten|kittens|pup|pet|"
    r"parrot|budgie|hamster|rabbit|bunny|horse|pony|guinea\s+pig|tortoise|ferret|gerbil|rat|lizard|"
    r"snake|hen|chicken)\b[^.?!]{0,25}\b(?:has|have|had|got|with|cut|is|was)\b"
)

NOT_A_PET_LINE = (
    r"\A(?!.*\b(?:dog|dogs|puppy|pup|pups|cat|cats|kitten|kittens|rabbit|hamster|guinea|horse|"
    r"pony|bird|parrot|pet|pets|vet|paw|paws|hoof|fur|tail|beak|snake|lizard)\b).*?"
)

CUT_ON_BODY = (
    # An animal is not a person: "my cat has a little cut on her ear" is the pets card, and the
    # "her" in it is the cat. A pet word anywhere in the line keeps the human first aid off it.
    r"^(?!.*\b(?:dog|dogs|puppy|pup|pups|cat|cats|kitten|kittens|rabbit|hamster|guinea|"
    r"horse|pony|bird|parrot|pet|pets|vet|paw|paws|hoof|fur|tail|beak|snake|lizard)\b).*?"
    r"\b(?:have|has|had|got|get|gets|getting|gave|gives?|with|from)\b[^.?!]{0,25}"
    r"\b(?:cut|gash|graze|scrape|scratch|nick)\s+"
    r"(?:on|to|in|above|below)\s+(?:my|his|her|their|your|the)\s+"
    # The mouth is out: a cut tongue or a torn bit inside the mouth wants an ice cube, not a cloth
    # pressed on it, and those lines have their own card.
    r"(?:hands?|fingers?|fingertips?|thumbs?|arms?|elbows?|lips?|"
    r"faces?|cheeks?|nose|ears?|eyes?|eyebrows?|forehead|feet|foot|toes?|legs?|knees?|shins?|"
    r"chest|backs?|palms?|knuckles?|head|scalp|stomach|belly|thighs?|calves|calf|heels?|"
    r"ankles?|shoulders?|hips?)\b"
)

# The same cut said as a thing, but on the three places where it is more often done than fallen on.
# Kept out of `CUT_ON_BODY` above so the cloth-and-ten-minutes answer does not land on it alone.
CUT_ON_THROAT_BODY = (
    r"\b(?:cut|gash|scratch|graze|scrape|nick|slice)\b"
    r"(?:\s+(?:on|in|to|across)\s+(?:my|his|her|their|the|your)\s+|\s+(?:my|his|her|their|your)\s+|\s+)"
    r"(?:wrists?|neck|throat)\b"
)

RING_STUCK = (r"\bring\b", r"\bwedding\s+ring\b", r"\bengagement\s+ring\b")

# A nail cut too short is an injury with a first aid of its own: the quick is the blood supply
# inside the nail, so it bleeds far more than the nick looks and it is answered at home rather than
# at the vet. The lines got a grooming-refund answer ("Photograph it straight away and ask for a
# refund") because the thing cut was the animal's nail and nobody read the nail, and "i nicked the
# quick" got a listening line. The injury word has to be said, so the how-to lines ("how do i cut my
# dogs nails", "my dogs nails are too long") keep their own answer, and a nail simply described as
# bleeding stays with the vet card above.
# An animal's wound is the vet's, and it needs an answer of its own rather than the human first
# aid: "my cat has a cut on her ear" got "wash it under the tap, press a clean cloth down", and a
# stand-down into whatever answers the pet shape elsewhere sent "my dog has a gash on his leg" to a
# listening line. The animal has to own the wound, so "i have a cut on my ear from the dog" is still
# the person's.
# Blood an animal passes is not a wound on it: "my cat is weeing blood" is cystitis and the vet
# tomorrow, and neither a wash-and-don't-lick card nor a vet-tonight card is the right first aid for
# it. Named once here, read by both the wound row and the fence that stands the person's rows down.
PET_PASSES_BLOOD = (r"[^.?!]*\b(?:wee\w*|urine|urinating|pee\w*|piss\w*|stool|poo\w*|vomit\w*|"
                    r"sick|diarrh\w*|tummy|gut)\b")

PET_WOUND = (
    # A pet that is bleeding is a pet wound in the words people actually use: "my dog is bleeding a
    # bit from his paw", "my cat is bleeding a bit" and "my dog's paw is bleeding" were all read as
    # the person's own cut, because "bleeding" was not in this list.
    # Blood the animal passes is not a wound on it: "my cat is weeing blood" is cystitis and the vet
    # tomorrow, and a wash-and-don't-lick card is the wrong first aid for it.
    r"\A(?=.*" + PET_OWNS_THE_WOUND + r")(?!" + PET_PASSES_BLOOD + r")"
    r".*?\b(?:cut|gash|graze|scrape|scratch|nick|wound|sore|blister|bleed\w*|bled|blood)\b",
)

# An animal that owns an injury is the vet's, whatever the injury is: the animal, or something of its
# own ("my dog's paw"), is the subject of the injury word. "my dog burnt his paw" was getting the
# person's burn card, "my cat has a splinter in her paw" warm water and tweezers for a hand, and
# "my dog grazed his knee" a card that ends "a nurse or A&E". A person's own injury keeps its card:
# "my dog knocked me over and my wrist is sprained" names the person's wrist, not the dog's.
PET_ANIMAL_HURT = (
    r"\b(?:my|our|the|his|her|their)\s+(?:dogs?|cats?|pupp(?:y|ies)|kittens?|pup|pets?|parrot|"
    r"budgie|hamster|rabbit|bunny|horse|pony|guinea\s+pig|tortoise|ferret|gerbil|rats?|lizard|"
    r"snake|hen|chicken)\b[^.?!]{0,32}?\b(?:burnt|burned|scalded|grazed|cut|nicked|"
    r"splinter|blister\w*|broke|broken|bleed\w*|bled|blood|wound|gash\w*|scraped|scrapes)\b",
)
# An animal does not break its own flap or its lead, and a nail trimmed too short is the nail's own
# row rather than a break: "the cat flap is broken", "my dog's lead is broken what should i buy" and
# "my dog broke a nail" are answered better where they already were.
PET_OWNS_A_THING = (
    r"\b(?:dogs?|cats?|pupp(?:y|ies)|kittens?|pup|pets?|parrot|budgie|hamster|rabbit|bunny|horse|"
    r"pony|guinea\s+pig|tortoise|ferret|gerbil|rats?|lizard|snake|hen|chicken)(?:'s)?\s+"
    r"(?:flap|lead|leash|harness|collar|tag|bowl|bed|basket|blanket|toy|toys|coat|jacket|gate|"
    r"door|hutch|kennel|cage|tank|claw|claws|nail|nails)\b",
    # ...and a nail torn or trimmed is the nail row's, wherever the verb sits in the sentence.
    r"\b(?:broke|broken|split|torn|lost|caught|trimmed|clipped)\s+(?:a|his|her|its|the)\s+"
    r"(?:nail|nails|claw|claws)\b",
)
# The person's own part taking the injury in the same line, which is the person's card.
HUMAN_OWN_INJURY = (
    # The person's part taking the injury, either way round: "my wrist is sprained" and
    # "my dog nicked my finger" are both the person's card.
    r"\b(?:my|our|his|her|their)\s+(?:hand|hands|finger|fingers|thumb|thumbs|wrist|wrists|arm|"
    r"arms|elbow|shoulder|knee|shin|calf|ankle|foot|feet|toe|toes|face|cheek|lip|nose|head|back|"
    r"chest|stomach|leg|legs)\b[^.?!]{0,25}?\b(?:burnt|burned|scalded|sprained|grazed|cut|nicked|"
    r"blister\w*|broke|broken|bleed\w*|bled|blood)\b",
    # "his" and "her" are left out of this one on purpose: in "my dog burnt his nose" the nose is the
    # dog's, and a person named with his or her is already caught by HUMAN_TOO above.
    r"\b(?:burnt|burned|scalded|sprained|grazed|cut|nicked|scratched|bit|bitten|nipped|broke|broken)"
    r"\b[^.?!]{0,20}?\b(?:my|our|their)\s+(?:hand|hands|finger|fingers|thumb|thumbs|wrist|"
    r"wrists|arm|arms|elbow|shoulder|knee|shin|calf|ankle|foot|feet|toe|toes|face|cheek|lip|nose|"
    r"head|back|chest|stomach|leg|legs)\b",
)

PET_NAIL = (
    r"\b(?:my|our|the|his|her|their)\s+(?:dogs?|cats?|puppy|puppies|kitten|kittens|pup|pet|parrot|"
    r"budgie|rabbit|bunny|hamster|horse|pony|guinea\s+pig|ferret|gerbil|lizard)\b[^.?!]{0,30}?\b"
    r"(?:cut|clipped|trimmed|nicked|caught|tore|torn|snapped)\b[^.?!]{0,20}?\b(?:nail|nails|claw|"
    r"claws|quick)\b",
    r"\b(?:my|our|the|his|her|their)\s+(?:dogs?|cats?|puppy|puppies|kitten|kittens|pup|pet)'?s?\s+"
    r"(?:nail|nails|claw|claws|quick)\b[^.?!]{0,30}?\b(?:too\s+short|cut\s+too|clipped\s+too|"
    r"trimmed\s+too|nicked|torn|snapped|split)\b",
    r"\bi\s+(?:cut|clipped|trimmed|nicked)\s+(?:the\s+|his\s+|her\s+|its\s+)?quick\b",
)

# A cut wrist, neck or throat is never the small-cut reply: that is the bleeding emergency,
# so those body words stay out of this list.
# The verbs people use for a burn are four, not two. "i scorched my hand on the iron" was answered
# with a laundry tip about flattened scorched fibre and "i singed my arm on the gas ring" with the
# cost of gas, because the burn rows only knew burnt and scalded (sound-gate, msg 82391). One list,
# so the next word for a burn is one line rather than four.
BURN_VERB = r"(?:burnt|burned|burn|scald(?:ed|s)?|scorch(?:ed|es|ing)?|singe(?:d|s|ing)?)"

SIGHT_EVER = (
    r"\b(?:sight|eyesight|vision|eye|eyes)\b",
)

SIGHT_LIFE_REPLIES = (
    "Sight that has always been like that is not an emergency, but it is worth a proper eye test: "
    "an optician can test it and your GP can refer you, and there is practical help too - a "
    "certificate for sight loss and the support that comes with it. If it has changed even a "
    "little this week, that is a same-day call instead.",
)

BURNT_BODY_VERB = (
    # a body part and then the state, which is how most people say it: "my face is burnt",
    # "my skin is blistering", "her arm was all scalded". None of the verb-first arms in the burn
    # row reach these, so "my face is burnt" was a shrug while "my hand is burnt" got the card.
    r"\b(?:my|his|her|their|your|our)\s+(?:faces?|skin|hands?|arms?|legs?|neck|chest|shoulders?|"
    r"backs?|tummy|belly|feet|foot|fingers?|fingertips?|thumbs?|thighs?|palms?|wrists?|lips?|ears?|"
    r"cheeks?|chin|forehead|scalp|eyebrows?|knees?|elbows?|calves|calf|shins?|toes?)\b"
    r"[^.?!]{0,15}\b(?:is|are|was|were|got|gets|has\s+got|have\s+got|looks?)\s+(?:all\s+)?"
    r"(?:burnt|burned|scalded|blister\w*)\b"
    # A face burnt from crying is the salt and the rubbing, not a heat injury, and twenty minutes
    # under cool running water is the wrong comfort for it. The arm wanted no reason at all, so a
    # reason that is not heat stands it down; the sun, the oven and the kettle are heat and keep it.
    r"(?![^.?!]{0,20}\b(?:from|because\s+of|due\s+to|off)\s+(?:the\s+|all\s+the\s+)?"
    r"(?:cry\w*|tears?|weep\w*|sob\w*)\b)",
    # Red raw is heat only when the line says what heated it: "my hands are red raw from washing up"
    # and "my lips are red raw" are chapping and a cold, and twenty minutes under cool running water
    # is the wrong shape for them. The sun, the oven and the kettle are heat words; washing up is not.
    r"\b(?:my|his|her|their|your|our)\s+(?:faces?|skin|hands?|arms?|legs?|neck|chest|shoulders?|"
    r"backs?|tummy|belly|feet|foot|fingers?|fingertips?|thumbs?|thighs?|palms?|wrists?|lips?|ears?|"
    r"cheeks?|chin|forehead|scalp|knees?|elbows?|shins?|toes?)\b[^.?!]{0,15}"
    r"\b(?:is|are|was|were|got|gets|looks?)\s+(?:all\s+)?red\s+raw\b"
    r"(?=[^.?!]{0,30}\b(?:sun|sunburn\w*|sunburnt|hot|boil\w*|oven|kettle|pan|steam|steam\w*|"
    r"iron|wax|scald\w*|fire|flame\w*|barbecue|bbq|cooker|hob|radiator|heat\w*|heated|"
    r"straightener\w*|blow\s+dry\w*|hot\s+water)\b|\Z)",
    r"\bburn(?:t|ed)\b[^.?!]{0,10}\b(?:my|his|her|their|your|our)\s+"
    r"(?:hands?|fingers?|fingertips?|thumbs?|arms?|wrists?|lips?|faces?|cheeks?|nose|ears?|legs?|"
    r"knees?|chest|skin|neck|chin|forehead|eyebrows?|scalp|back|thighs?|feet|foot|toes?|stomach|"
    r"belly|shoulders?)\b",
)

# The wax is the heat and the body part is where it landed: "hot wax on my hand", "i got hot wax on
# my arm", "i spilt hot wax on my fingers". No burn verb is said, so the burn row never saw them, and
# a home wax kit is a heat injury said as a spill - main answered the first two with a chat line
# ("Good to hear. What was the best bit?") and the third with the nail-infection card, because a red
# throbbing finger is what it read. The word that says heat has to be there: "wax on my hand" alone
# is a candle, a polish or a spill that has cooled, and the salon questions ("how do i get wax off my
# hands") keep their own answer because they ask to get it off, not to be seen for it.
WAX_BODY = (
    r"(?:hands?|fingers?|fingertips?|thumbs?|arms?|wrists?|legs?|thighs?|knees?|feet|foot|toes?|"
    r"lips?|faces?|cheeks?|chin|skin|stomach|belly|chest|neck|back|shoulders?|ears?)\b"
)

HOT_WAX_ON_BODY = (
    r"\b(?:hot|melted|molten|warm|boiling)\s+wax\b[^.?!]{0,25}\b(?:on|onto|over|down|across)\b"
    r"[^.?!]{0,15}\b(?:my|his|her|their|your|our)\s+" + WAX_BODY,
    r"\b(?:wax|waxing\s+wax|wax\s+pot|wax\s+burner)\b[^.?!]{0,25}"
    r"\b(?:spilt|spilled|dripped|dribbled|poured|splashed|leaked|came\s+off)\b"
    r"[^.?!]{0,25}\b(?:my|his|her|their|your|our)\s+" + WAX_BODY,
)

# A part of the body that is off, or hanging on by a thread, is not a cut to press and dress. There
# was no amputation arm anywhere in the module: `amputat` appeared only inside LIMP_ONGOING, the
# long-standing-cause card. So "my finger is hanging off" was answered with a chat line ("Thanks for
# telling me - I'm here if you want to dig into any of that"), "my finger has been cut off" with
# "Good to hear. What was the best bit?", "i sliced the top of my thumb off" with "Sounds alright.
# Anything good in it?" and "i got my hand in the machine at work" with "Nice one. How did the rest
# of it go?" - the worst replies measured in this lane. The nearest routes, BLEEDING and
# STUCK_MACHINE, want a blood or machine word and are not reached by the shape people type.
# A nail, a tooth, hair, a denture, a false or prosthetic part, a ring and a plaster all come off a
# person without anybody being hurt, so every arm stands down when one of them is in the line.
PART_OFF_PART = (
    r"(?:fingers?|fingertips?|thumbs?|toes?|hands?|feet|foot|arms?|legs?|ears?|noses?|lips?|tongues?)"
)

PART_OFF_NOT = (
    r"\A(?!.*\b(?:prosthe\w+|false|glass|denture|dentures|nails?|toenails?|fingernails?|hair|tooth|"
    r"teeth|wig|hairpiece|rings?|earrings?|bracelet|watch|plaster|cast|bandages?|dressings?|brace|"
    r"retainer|contacts?|tags?|labels?|buttons?|sticker|stuck\s+on)\b).*?"
)

PART_OFF = (
    # "my finger is hanging off", "his thumb is hanging by a thread", "my hand is half off"
    PART_OFF_NOT
    + r"\b(?:my|his|her|their|your|our)\s+" + PART_OFF_PART + r"\b[^.?!]{0,12}\b"
    r"(?:hanging\s+off|hanging\s+by|hanging\s+on\s+by|half\s+off|hanging\s+loose|"
    r"hangs?\s+off)\b",
    # "my finger has been cut off", "her toe was chopped off", "his thumb got taken off"
    PART_OFF_NOT
    + r"\b(?:my|his|her|their|your|our)\s+" + PART_OFF_PART + r"\b[^.?!]{0,15}\b"
    r"(?:has|have|had|was|were|is|are|got|been)?\s*(?:been\s+)?"
    r"(?:cut|chopped|sliced|severed|taken|took|bitten|ripped|torn|broke|snapped)\s+off\b",
    # "i cut the top of my finger off", "he sliced the tip of his thumb off"
    PART_OFF_NOT
    + r"\b(?:cut|sliced|chopped|severed|took|nipped|bit|ripped|tore)\s+(?:the\s+)?"
    r"(?:top|tip|end|part)\s+of\s+(?:my|his|her|their|your)\s+" + PART_OFF_PART + r"\s+off\b",
    # "i cut my finger off", "he severed his thumb"
    PART_OFF_NOT
    + r"\b(?:cut|sliced|chopped|severed|amputated)\s+(?:my|his|her|their|your)\s+"
    + PART_OFF_PART + r"\s+off\b",
    PART_OFF_NOT
    + r"\b(?:severed|amputated)\s+(?:my|his|her|their|your)\s+" + PART_OFF_PART + r"\b",
    # "the tip of my finger came off"
    PART_OFF_NOT
    + r"\b(?:the\s+)?(?:top|tip|end)\s+of\s+(?:my|his|her|their|your)\s+"
    r"(?:fingers?|thumbs?|toes?|noses?|ears?)\s+(?:came|come|has\s+come|had\s+come|is|was)\s+off\b",
    # a hand or an arm in a running machine
    PART_OFF_NOT
    + r"\b(?:my|his|her|their|your)\s+(?:hands?|arms?|fingers?)\s+"
    r"(?:got|was|is|were|has\s+been|had\s+been)?\s*"
    r"(?:caught|trapped|stuck|pulled|dragged|crushed)\s+(?:in|into|under)\s+(?:the|a)\s+"
    r"(?:machine|machinery|press|lathe|blender|mincer|saw|chipper|shredder|mower|drill|mixer|"
    r"guillotine|baler|combine)\b",
    # the same machine said the other way round: "i got my hand in the machine at work", "he put his
    # hand in the blender", "i had my fingers under the press"
    PART_OFF_NOT
    + r"\b(?:got|get|put|puts|had|has|have|stuck|shoved|pushed|caught)\s+"
    r"(?:my|his|her|their|your)\s+(?:hands?|arms?|fingers?)\s+(?:in|into|under)\s+(?:the|a)\s+"
    r"(?:machine|machinery|press|lathe|blender|mincer|saw|chipper|shredder|mower|drill|mixer|"
    r"guillotine|baler|combine)\b",
    # a hand or a part that has been crushed rather than cut: "my hand is mashed", "my fingers were
    # crushed under the pallet"
    PART_OFF_NOT
    + r"\b(?:my|his|her|their|your)\s+" + PART_OFF_PART + r"\b[^.?!]{0,12}\b"
    r"(?:mashed|mangled|crushed|pulped|squashed\s+flat|flattened)\b",
    # and said with the verb first: "i crushed my finger with a hammer", "he smashed his thumb"
    PART_OFF_NOT
    + r"\b(?:crushed|smashed|squashed)\s+(?:my|his|her|their|your)\s+"
    r"(?:fingers?|thumbs?|hands?|toes?|feet|foot)\b",
)


MINOR = (
    ("mouth_burn", (r"\b(?:burnt|burned|scalded)\s+(?:the\s+roof\s+of\s+my|inside\s+of\s+my|my\s+(?:tongue|mouth|throat))\b",),
     ("Sip cold water or suck an ice cube, and skip hot, salty or citrus food for a couple of days; "
      "the roof of your mouth usually settles within a week. Get it looked at if it's a big white "
      "patch or still sore after a week.",
      "Cold water or an ice cube is the fix, and give hot, salty and citrus food a miss for a few "
      "days. It normally heals in about a week; anything large or still painful after that should be "
      "checked.")),
    ("tooth_chipped", TOOTH_CHIPPED,
     ("A chipped tooth is a dentist's, not an ambulance: if a piece came off, keep it in milk, and "
      "ring 111 for an urgent dental appointment. Go today if it is bleeding, hurts a lot, or you "
      "can see a pink or red centre in it.",
      "Ring 111 and ask for an urgent dentist, usually within a day or two; keep any piece that "
      "came off in milk and eat on the other side. Bleeding that will not stop, or a bad knock "
      "with it, wants to be seen today.")),
    ("tooth_out", TOOTH_OUT,
     ("Pick the tooth up by the crown and never the root, put it straight back in the socket if you "
      "can, or keep it in milk or saline: a dentist within the hour gives it the best chance, so "
      "ring 111 for the emergency dentist now. A bang on the head as well, or bleeding you cannot "
      "stop, is 999 or A&E.",
      "Hold it by the crown, put it back in the socket if you can and bite gently on a cloth, or "
      "keep it in milk or saline, and ring 111 for an emergency dentist now - the first hour is what "
      "matters. If there was a bang on the head or the bleeding will not stop, ring 999.")),
    # Anyone's bad cut, not only your own: "my dad cut his hand and it won't stop bleeding".
    # Before the small-injury replies: a person asking whether to ring is asking about a person,
    # and the answer is to ring, not to weigh it.
    ("should_i_call", SHOULD_I_CALL,
     ("That is a 999 or 911 call, not a judgement call: if the question is in your head at all, "
      "ring and say what you can see - they would far rather have the call than not, and being "
      "wrong about it costs you nothing.",
      "Ring 999 or 911 and say what you can see; the call taker decides what to send, and they "
      "would rather hear from you than not. If it turns out to be nothing much, nobody will mind.")),
    # A part that is off is the hospital now, not the cloth and ten minutes: the small-cut reply
    # ("press a clean cloth on the cut... most cuts stop by then") is the wrong register for a finger
    # that is not attached any more.
    ("part_off", PART_OFF,
     ("A part that is off, or hanging on by a thread, is a hospital job now rather than a plaster: "
      "press a clean cloth on the wound and keep pressing, and if a piece has come away, wrap it in "
      "a clean cloth, seal it in a bag and keep the bag cool - never the piece straight on ice. Ring "
      "999 or 911 if the bleeding will not slow or they go pale or dizzy; if it has slowed, go "
      "straight to A&E.",
      "Do not wait on that one: press a clean cloth on it and hold it without lifting it to look, "
      "and if a piece has come away, wrap it in a clean cloth, seal it in a bag and keep the bag "
      "cool. Ring 999 or 911 if the bleeding will not stop or they look pale or clammy - otherwise "
      "A&E now, not tomorrow.")),
    ("bleeding", BLEEDING_SMALL,
     ("Press a clean cloth on the cut and hold it there without lifting it to look for ten minutes; "
      "most cuts stop by then. If it soaks through, the edges gape, or they go pale or dizzy, that's "
      "999 or 911.",
      "Press a clean cloth on it and keep pressing for ten minutes without lifting it to look; add "
      "another cloth on top if it soaks through. If it's still going after twenty minutes or they go "
      "pale or dizzy, that's 999 or 911.")),
    # A cut named on the wrist, neck or throat is neither the small-cut reply nor a shrug. Most
    # people mean an accident and want the cloth; some mean the other thing and this is the only
    # line they will write today, so the answer does both in one breath and gives the number.
    ("cut_wrist", CUT_ON_THROAT_BODY,
     ("Press a clean cloth on it and hold for ten minutes, and get it looked at if it gapes or keeps "
      "bleeding. If you did that to yourself, please tell someone today - Samaritans is 116 123, free "
      "and open any hour, and one cut on a wrist is not a fuss.",
      "Hold a clean cloth on it for ten minutes; if it needs a stitch or will not stop, that is A&E. "
      "And if that was on purpose, tell someone today - 116 123 is Samaritans, free and open any "
      "hour.")),
    ("pet_nail", PET_NAIL,
     ("Press a pinch of flour, cornflour or a styptic pencil on the end of the nail and hold it there "
      "for five minutes without lifting it to look - a cut quick bleeds much more than the nick "
      "deserves, and it stops with pressure. Keep them off the pavement and the stairs for the rest "
      "of the day, and ring the vet if it is still going after ten minutes, if the nail is torn or "
      "hanging, or if a cat has caught a claw.",
      "Flour or cornflour pressed on the tip for five minutes is the first thing, and most stop "
      "there; a torn nail or one that keeps bleeding needs the vet today, and so does a cat's caught "
      "claw, which snags again until it is trimmed back. Soft ground and no jumping for the rest of "
      "the day.")),
    ("pet_wound", PET_WOUND,
     ("Bathe it with cool water or salt water and pat it dry, then keep the animal off it - a buster "
      "collar or a sock over a paw - because licking keeps a wound wet and slow to heal. Ring the "
      "vet today if it gapes open, keeps bleeding, or is on a paw, an ear or near an eye, and put "
      "nothing from the bathroom cabinet on it.",
      "Cool water or salt water, pat it dry, and keep the animal from licking it - a cone or a sock "
      "over a paw does that better than telling it off. Anything that gapes, keeps bleeding, or is "
      "on a paw, an ear or an eye is a vet visit today rather than a wait-and-see, and nothing from "
      "the bathroom cabinet goes on it: a pet licks a plaster off and the cream is not made for "
      "animals.")),
    # A cut wrist, neck or throat is never the small-cut reply: that is the bleeding emergency,
    # so those body words stay out of this list.
    # The verb is said in the present as often as the past - "my husband cuts his finger", "my son
    # cuts his hand" - and the singular forms were missing, so a cut that is happening was answered
    # with a lump on the wrist.
    ("cut", (r"\b(?:cut|cuts|sliced|slices|nicked|nicks|grazed|grazes|scraped|scrapes)\s+"
              r"(?:my|his|her|their|the)\s+(?:finger|thumb|hand|"
              r"arm|leg|foot|toe|knee|head|face|lip|eye|ear|tongue|palm|heel|knuckle|shin|"
              r"elbow|fingertip)s?\b",
              # Scratch is the one cut verb people use about themselves most often - "i scratched
              # my hand on a thorn", "i scratched my arms until they bled", "i scratched my arms
              # in my sleep" - and the cut row did not read it at all, so the skin was open while
              # the reply was a pleasantry or a cat's claw. It gets its own arm rather than joining
              # the verbs above, because the eye is on that list and a scratched eye is not a cut
              # that wants a cloth: it has its own first aid (do not rub, rinse for ten to fifteen
              # minutes, eye casualty if it does not settle), and the deck's `i scratched my eye`
              # answered with the cloth the moment scratch was read by the shared arm.
              r"\b(?:scratched|scratches)\s+(?:my|his|her|their|the)\s+(?:finger|thumb|hand|"
              r"arm|leg|foot|toe|knee|head|face|lip|ear|tongue|palm|heel|knuckle|shin|"
              r"elbow|fingertip|forearm|forehead|chin)s?\b",
              # The noun, which the verb arms above miss: "i have a cut on my hand", "i have a
              # cut finger", "a gash on my arm", "i have a scratch on my arm" were all a listening
              # line (soft-ocelot, #safety 40287). The body part has to be in the pattern, so
              # "a cut on the price" and "a gash in the budget" are not it.
              r"\A(?!.*" + PET_OWNS_THE_WOUND + r").*?"
              r"\b(?:cut|gash|scratch|graze|scrape|nick|slice)\b"
              r"(?:\s+(?:on|in|to|across)\s+(?:my|his|her|their|the|your)\s+"
              r"|\s+(?:my|his|her|their|your)\s+|\s+)"
              r"(?:finger|thumb|hand|arm|leg|foot|toe|knee|head|face|lip|eye|ear|tongue|palm|"
              r"heel|knuckle|shin|elbow|fingertip|forearm|forehead|chin)s?\b",
              r"\bpaper\s+cut\b", r"\bcut\s+my\s*self\b",
              r"\b(?:cut|cutting|nicked|sliced|grazed|scraped)\s+(?:him|her|them)sel(?:f|ves)\b",
              # A cut named as a thing on a body part is the same injury as "i cut my finger",
              # and the verb arms above cannot see it. "i have a cut on my hand" was answered
              # with "Most shaky hands are caffeine", because the shaky-hands key holds a bare
              # "hand" and a bare "have". Same shape as the burn arm's "a burn on my hand", and
              # the graze, scrape and scratch that had no answer at all ride with it.
              CUT_ON_BODY,
              # "my cut is bleeding": the injury named, then the bleeding, with no verb arm to
              # match either ("cut my finger" is not in the line).
              r"\b(?:my|his|her|their|your|the)\s+(?:cut|gash|graze|scrape|scratch)\b"
              r"[^.?!]{0,20}\bbleeding\b",
              # CUT_ON_BODY needs a verb and the word "on". The same wound is said without
              # either: "i have a cut finger", "a cut on my hand", "i have a small cut", "i have
              # a graze". Every one of those was acknowledged back at the person ("Noted: you
              # have a small cut") while "i cut my finger" got the first aid. A size word, a body
              # part or a named graze is what makes it the wound: "i have a cut of beef", "a cut
              # in my pay" and "a cut and blow dry" stay with their own rows.
              NOT_A_PET_LINE
              + r"\b(?:a|an|this|that|my|his|her|their)\s+"
              r"(?:nasty|deep|bad|sore|bleeding|weeping)?\s*"
              r"(?:cut|gash|graze|scrape|scratch|nick|slice)\s+(?:on|in|to|across|near)\s+"
              r"(?:my|his|her|their|your)\s+" + CUT_BODY_PART,
              NOT_A_PET_LINE
              + r"\b(?:have|has|got|get|had)\s+(?:a|an|this|that)\s+"
              r"(?:small|little|nasty|deep|bad|tiny|sore|long|clean|weeping)\s+"
              r"(?:cut|gash|graze|scrape|scratch|nick)\b",
              NOT_A_PET_LINE
              + r"\b(?:have|has|had|got|get)\s+(?:a|an)\s+"
              r"(?:cut|gashed|grazed|scraped|scratched)\s+" + CUT_BODY_PART,
              # A graze or a scrape is nothing but skin off, so on its own it is the injury. A car
              # door or an alloy wheel is the one other thing people graze, and those lines keep
              # their own answers.
              r"(?!(?:.*?)\b(?:car|cars|van|bike|motorbike|wheel|wheels|bumper|alloy|paint|door|"
              r"doors|wall|table|worktop)\b)"
              r"\b(?:have|had|got)\s+(?:a|an)\s+(?:graze|scrape|gash)\b",
              # "i nicked myself shaving" and "i caught myself on a nail" are the same sentence as
              # "i cut myself", and only the one verb was read, so the shaving had no answer.
              r"\b(?:nicked|sliced|grazed|scratched|scraped|caught)\s+my\s*self\b",
              r"\b(?:nicked|sliced|grazed|scratched|scraped|caught)\s+"
              r"(?:him|her|them)sel(?:f|ves)\b"),
     ("Press a clean cloth on it and keep pressing for ten minutes without lifting it to look; most "
      "small cuts stop by then. If the edges gape, it's deep, or it's still bleeding after twenty "
      "minutes of steady pressure, get it looked at.",
      "Wash it under the tap, press a clean cloth down and hold for ten minutes; that's what stops "
      "most cuts. A cut that gapes open, is deep, or keeps bleeding through the cloth needs a nurse "
      "or A&E.")),
    # The idiom "burn my bridges" says the same words as an injury, so the idiom's noun is read
    # off first and the burn case leaves the line alone.
    ("burn", (r"\b" + BURN_VERB + r"\s+(?:my|his|her|their|me|myself|yourself|himself|herself|themselves)\b"
              # ...and the hair is not skin: "i singed my fringe on the candle" was the burn card,
              # and what a singed fringe needs is a hairdresser. An eyebrow stays with the card: it
              # sits on skin, where the flash that singed it can have burnt the face too.
              r"(?!\s+(?:bridges|candle\s+at|holes?|midnight|hair|fringe|bangs|ponytail|plait|"
              r"braid)\b)",
              # "my face is burnt", "my skin is blistering": the body part leads and the state
              # follows. See BURNT_BODY_VERB, which spells out the list once. Every arm of it is
              # read here, so a later arm added to that list is not silently dead.
              *BURNT_BODY_VERB,
              r"\b(?:small|minor|little)\s+(?:burn|scald)s?\b",
              # A blister and the heat that made it: "blister from a kettle", "blistered from
              # boiling water", "a blister off the oven door". Without a heat word the same words
              # are a rubbed heel, and those keep the plaster answer.
              r"\bblister\w*\s+(?:from|off|after)\s+(?:the\s+|a\s+|my\s+|his\s+|her\s+|"
              r"their\s+)?(?:kettle|oven|hob|grill|toaster|iron|pan|fryer|barbecue|bbq|fire|"
              r"flames?|steam|boiling\s+water|hot\s+water|hot\s+oil|hot\s+fat|hot\s+pan)\b",
              r"\b(?:burn|burnt|burned|burning|scalds?|scalded|scalding)\b[^.?!]{0,25}"
              r"\bblister\w*\b",
              # The wax that is the heat, spilled on skin: "hot wax on my hand". See HOT_WAX_ON_BODY.
              HOT_WAX_ON_BODY[0], HOT_WAX_ON_BODY[1],
              # The noun, which the verb arms above miss: "i got a burn from the oven what should i
              # do" was read as a burnt bake, because the oven is one of the things this bot knows
              # can burn. Naming the burn is naming the injury, and the water is the answer either
              # way, so the wording "a burn" counts wherever the person is in the line.
              r"(?!(?:.*?)\b" + NOT_BURN_ON_BODY + r")"
              r"\b(?:got|get|have|has|had)\s+(?:a|an|this|that|some)\s+"
              r"(?:bad|nasty|nasty|small|minor|little|sore|red|nasty)*\s*(?:burn|scald)s?\b",
              # "a burn from the oven" is a person burnt by a heat thing, and "a burn on my hand"
              # is a person burnt on a body part. Without those two qualifiers the arm also took
              # "a burn on my wooden table", "the iron left a burn on my shirt" and "a burn on it".
              r"\b(?:a|the|this|that)\s+(?:bad|nasty|small|minor|little|sore|red)?\s*burn\s+"
              r"(?:from|off)\b",
              r"\b(?:a|the|this|that)\s+(?:bad|nasty|small|minor|little|sore|red)?\s*burn\s+"
              r"(?:on|to)\s+(?:my|his|her|their|your|the)\s+" + BURN_ON_BODY,
              r"\b(?:burnt|burned|scalded|scald|burn)\s+(?:the\s+roof\s+of\s+my|inside\s+of\s+my)\b",
              r"\b" + BURN_VERB + r"\s+(?:my|his|her|their|me|on\s+my)\s+"
              r"(?:hand|finger|arm|wrist|thumb|tongue|mouth|foot|leg)s?\b",
              # The hand that went onto the hot thing, with no burn word in the line at all: "i
              # put my hand on a hot hob", "i put my hand on a hot iron", "i grabbed the oven
              # shelf". Main answered these with "Thanks for telling me". A hob, a grill, an oven
              # door or a hotplate is hot by nature, so it needs no "hot" in front of it; a
              # kettle, a pan or a plate does need it, because "i put my hand on the kettle" is
              # somebody making a cup of tea and "i put my hand on the hot plate" is a plate of
              # hot food, which the food-safety answer already owns.
              r"\b(?:put|putting|puts|placed?|placing|rest(?:ed|ing)?|touch(?:ed|ing)?|touches|"
              r"grab(?:bed|bing)?|grabs|picked?\s+up|lean(?:ed|t|ing)?\s+on|sat\s+on|slipped)\s+"
              r"(?:my|his|her|their)\s+(?:hand|hands|finger|fingers|thumb|palm|forearms?|arm|wrist|"
              r"bottom|bum|leg|legs|back)\b[^.?!]{0,25}\b"
              r"(?:hob|grill|oven\s+door|oven\s+shelf|hotplate|cooker\s+ring|cooker)\b",
              # A hand put into the fire itself: "i put my hand in the fire" and "i stuck my
              # hand in the flames" were a shrug, because every arm here wants an appliance or a
              # pan and a fire is neither. The hand is the thing in the fire, so the verb has to
              # take a hand and the fire has to be a fire.
              r"\b(?:put|puts|putting|stuck|stick|sticks|sticking|thrust|shoved|shove|dipped|"
              r"dip|place[ds]?|placing)\s+(?:my|his|her|their|our|your)\s+"
              r"(?:hand|hands|finger|fingers|thumb|thumb|arm|arms|foot|feet|fist)\b"
              r"[^.?!]{0,15}\b(?:in|into|through|over)\s+(?:the|a|an)\s+"
              r"(?:fire|flames|flame|campfire|bonfire|barbecue|barbeque|bbq|coals|embers|"
              r"burning\s+coals)\b",
              # ... and the same said as a state rather than an act: "my hand is in the fire".
              r"\b(?:my|his|her|their|our|your)\s+(?:hand|hands|fingers?|arm|arms|foot|feet)\b"
              r"[^.?!]{0,12}\b(?:is|was|were|got|went|had\s+gone)\b[^.?!]{0,6}"
              r"\b(?:in|into|through)\s+(?:the|a|an)\s+(?:fire|flames|campfire|bonfire|coals|"
              r"embers)\b",
              # A hand that brushed a hot thing rather than taking hold of it, which is how most
              # people describe it: "i brushed against the hot grill" and "i grazed the hot oven
              # shelf" were the shrug. The surface is the named hot one, so a hand brushing past
              # a cold oven is not this.
              r"\b(?:brushed|brushing|brushes|graze[ds]?|grazing|scraped|rubbed|caught)\s+"
              r"(?:against|past|up\s+against|on)?\s*"
              r"(?:(?:the|a|an|my|his|her|their|our)\s+)?"
              r"(?:hot|boiling|scalding|red\s?hot|searing|sizzling)\s+"
              r"(?:grill|hob|ring|oven|oven\s+door|oven\s+shelf|iron|pan|pot|kettle|cooker|"
              r"hotplate|radiator|heater|burner|stove|saucepan|element|plate|tray|shelf)\b"
              # A thing that was off is not a burn: "i brushed against the hot iron and it was
              # cold" is somebody working on the appliance.
              r"(?![^.!?]{0,25}\b(?:was|were|is|are|had\s+been|has\s+been)\s+"
              r"(?:already\s+|still\s+|stone\s+|completely\s+)?(?:cold|off|not\s+hot|"
              r"not\s+warm|switched\s+off|turned\s+off|unplugged|cooled)\b)",
              # A hot liquid on the skin with no verb at all: "hot oil on my hand" was answered
              # with frying temperatures, because every arm here asks how the liquid arrived.
              # The liquid, the preposition and the body are the whole line.
              r"\b(?:hot|boiling|scalding|searing|sizzling)\s+"
              r"(?:oil|fat|water|stock|soup|gravy|syrup|sugar)\b[^.?!]{0,10}"
              r"\b(?:on|over|onto|down|across)\s+"
              r"(?:my|his|her|their|our|your)\s+"
              r"(?:hand|hands|arm|arms|wrist|wrists|leg|legs|foot|feet|lap|chest|tummy|belly|"
              r"neck|face|skin|shoulder|shoulders|back|thigh|thighs|knee|knees|fingers?|thumb|"
              r"toes?|ankle|body|mouth|chin)\b",
              # The same thing with nobody's hand named: "i touched the hot hob",
              # "my son touched the hot hob" and "i grabbed the hot pan" were a shrug, and
              # "Noted: your son touched the hot hob" is no answer to a burned hand. A comfort
              # item is warm on purpose, so the hot water bottle, the heat pack and the hot drink
              # stand it down.
              # ...and only the verbs that take a body: "put", "place" and "rest" take whatever is
              # being cooked or stood down. "do i put the oil in a hot pan", "i put the chicken in
              # a hot pan", "put the pasta in boiling water" and "i rested the hot pan on the
              # worktop" were all the burn card, because the thing going into or onto the hot
              # thing matched it. A hand put or rested somewhere is the arm above.
              r"(?!(?:.*?)\b" + HOT_COMFORT + r")"
              r"\b(?:touch(?:ed|ing)?|touches|"
              r"grab(?:bed|bing)?|grabs|held|holding|lean(?:ed|t|ing)?\s+on|"
              r"rest(?:ed|ing)?\s+(?:on|onto|against|over)|"
              r"sat\s+on|slipped)\b[^.?!]{0,25}(?:(?:the|a|an|my|his|her|their|our)\s+)?"
              + HOT_SURFACE,
              # A hot thing rested **on a body** is the same injury in the other order, and that
              # order is the common one: "i rested the hot iron on my arm" and "i rested the hot
              # pan on my lap" were the burn card and must stay it. The verb alone cannot settle
              # it - "i rested the hot pan on the worktop" has the same verb and the same hot
              # thing - so the noun after the preposition decides: a body is a burn, a worktop,
              # a table or a side is not, and "i rested the hot kettle down" has no preposition
              # at all and stays out.
              r"(?!(?:.*?)\b" + HOT_COMFORT + r")"
              r"\brest(?:ed|ing)?\b[^.?!]{0,20}(?:(?:the|a|an|my|his|her|their|our)\s+)?"
              + HOT_SURFACE +
              r"\b[^.?!]{0,12}\b(?:on|onto|against|over|across)\s+"
              r"(?:my|his|her|their|our|your)\s+"
              r"(?:hand|hands|arm|arms|finger|fingers|thumb|wrist|leg|legs|knee|knees|lap|foot|feet|"
              r"chest|face|skin|shoulder|shoulders|thigh|back|belly|tummy)\b",
              r"(?!(?:.*?)\b" + HOT_COMFORT + r")"
              r"\b(?:put|putting|puts|placed?|placing|rest(?:ed|ing)?|touch(?:ed|ing)?|touches|"
              r"grab(?:bed|bing)?|grabs|picked?\s+up|lean(?:ed|t|ing)?\s+on|sat\s+on|slipped)\s+"
              r"(?:my|his|her|their)\s+(?:hand|hands|finger|fingers|thumb|palm|forearms?|arm|wrist|"
              r"bottom|bum|leg|legs|back)\b[^.?!]{0,25}\b"
              r"(?:hot|boiling|scalding|burning)\s+(?:iron|water|pan|kettle|saucepan|dish|tray|"
              r"oil|fat|spoon|tin)\b",
              r"\b(?:spill\w*|spilt|pour\w*|tip\w*|knock\w*|get\w*|got|drop\w*|dropped|"
              r"splash\w*|throw\w*|threw|chuck\w*)\s+(?:boiling|hot|scalding)\s+"
              r"(?:water|oil|fat|soup|tea|coffee)\s+(?:on|over|onto)\s+"
              r"(?:(?:my|his|her|your|their|our)\s+(?:hand|hands|arm|arms|wrist|wrists|leg|legs|"
              r"foot|feet|lap|chest|tummy|belly|neck|face|skin|shoulder|shoulders|back|thigh|thighs|"
              r"knee|knees|fingers?|thumb|toes?|ankle|body|mouth|chin)"
              r"|me|him|her|them|us|my\s*self|your\s*self|him\s*self|her\s*self|them\s*selves|"
              r"our\s*selves)\b",
              r"\bmy\s+(?:hand|finger|arm|wrist|thumb|tongue|mouth|foot|leg|skin)\b.{0,15}"
              r"\b(?:is|got|keeps?\s+getting)\s+(?:burnt|burned|scalded|blistered|scorched|"
              r"singed)\b",
              *SCORCHED_A_PERSON,

              # "should i put butter on a burn": the myth question names the burn as a thing, so
              # none of the arms above reach it, and a decision pool answered it as one of life's
              # trade-offs. The answer is a fact, and it is the one the case already gives.
              #
              # What goes on the burn is not always named: "what do i put on a burn" and "what
              # should i put on a burn" were shrugs, and "can i put cold water on a burn" was one
              # too, because the object had to be one of the words below. Anything put on a burn
              # is this question, and the reply already says what to use and what not to.
              r"\b(?:put|rub|apply|use|spread)\b[^.?!]{0,30}\b(?:on|onto)\s+(?:a|the|my|this|that)\s+"
              r"(?:bad\s+|red\s+|small\s+|nasty\s+|serious\s+|little\s+|sore\s+|fresh\s+)*"
              r"(?:burn|scald)s?\b",

              # The burn has not happened yet and the person still wants the first aid:
              # "what do i do if i burn my hand", "what if i burn myself", "what if i get burnt".
              # The burn idioms take the possessive too - "burn my bridges", "burn my fingers on
              # the deal" - so the idiom's noun has to be read off before this arm claims it.
              r"\b(?:burn|burns|burning|scald|scalds|scalding)\s+(?:my|your|his|her|their|me|"
              r"myself|yourself|himself|herself|themselves)\b"
              r"(?!\s+(?:bridges|candle\s+at|holes?|midnight)\b)",
              r"\b(?:get|got|gets)\s+(?:burnt|burned|scalded)\b(?!\s*(?:out\b|by\b|on\s+(?:that|the\s+deal|a\s+deal)\b))",
              r"\b(?:burn|burns|burning|scald|scalds|scalding)\b[^.?!]{0,20}"
              r"\b(?:my|your|his|her|their)\s+(?:hand|hands|finger|fingers|thumb|arm|wrist|"
              r"tongue|mouth|foot|feet|leg|skin|face|neck)\b",
              # "whats the first aid for a burn", "how do i treat a burn", "whats good for a burn"
              r"\b(?:first\s+aid\s+for|treat|treating|soothe|helps?|do\s+for|good\s+for|"
              r"best\s+(?:thing\s+)?for)\b[^.?!]{0,20}"
              r"\b(?:a|the|this)\s+(?:bad\s+|red\s+|small\s+|nasty\s+|serious\s+)?(?:burn|scald)\b"),
     ("Cool it under cool running water for twenty minutes, then cover it loosely with cling film "
      "or a clean non-fluffy cloth. Don't use ice, butter or cream, and get it checked if it's bigger "
      "than your palm, on the face or hands, or blistered.",
      "Twenty minutes under cool running water is the thing that helps, starting straight away. "
      "Cover it loosely and skip ice and butter; a burn that blisters or is on the face, hands or "
      "joints should be seen.")),
    ("nosebleed", (r"\bnose\s*bleed\b", r"\bnose\s+(?:is\s+|keeps\s+|started\s+)?bleeding\b",
                   r"\bnose\b.{0,20}\bbleed\w*\b"),
     ("Sit up, lean forward and pinch the soft part of your nose for ten minutes without checking. "
      "Spit out any blood rather than swallowing it; if it's still going after twenty minutes, get "
      "help.",
      "Lean forward, pinch the soft part of the nose and hold for ten minutes; leaning back just "
      "sends blood down your throat. If it keeps coming back or lasts over twenty minutes, see "
      "someone.")),
    # A foot or a knee that has been giving way for weeks is the GP's rather than A&E's: the
    # X-ray that fixes a break is the one taken in the first day or two, so a long-standing case
    # wants an appointment and an exam. Without this the line falls through to the weight-loss
    # answers, because "weight" in it is not about standing up at all.
    ("weight_limb_long", WEIGHT_JOINT,
     ("Weeks or months of it is a GP job rather than A&E: book an appointment, say how long it has "
      "been going on and what sets it off, and keep off it as much as you can meanwhile. Anything "
      "sudden, or clearly worse than usual, is the exception - that is A&E the same day.",)),
    # A joint that will not take weight is where the X-ray is: the sprain entry below says what
    # to do about the swelling, and this one says where to go about the standing.
    # A ring on a finger that is swelling is a deadline, not a sprain: "my finger is swollen
    # under my ring" was answered with "Ice for 15 minutes, raise it, and take it easy for a day
    # or two", which does nothing about the band doing the harm. Ice does not help a finger that
    # is swelling round a ring; getting it off before the swelling closes over it does.
    ("ring_stuck", RING_STUCK,
     ("Get the ring off now, before the finger swells any further: hold your hand above your head "
      "for a few minutes, then work it round with soap and water or a little cooking oil, twisting "
      "rather than pulling. If it will not move, wind dental floss or thin thread under the band "
      "and unwrap it towards the fingertip; a jeweller can cut it off, and so can A&E. If the "
      "finger has gone numb, cold or blue, go today rather than waiting - a ring left on a "
      "swelling finger can cut the blood off within hours.",
      "Get it off today if you can: hand up above your head for a few minutes, then soap and "
      "water or a little oil, twisting rather than pulling, and do not keep at it. Floss wound "
      "under the ring and unwrapped towards the tip will walk it off. If it will not move, or the "
      "finger is numb, cold or blue, that is A&E or 111 today; a jeweller can cut it off too.")),
    ("weight_limb", WEIGHT_JOINT,
     ("A joint that won't take weight is an X-ray today rather than a wait-and-see: go to A&E or a "
      "minor injuries unit, and keep it still on the way. Ice it and keep it raised until it has "
      "been seen.",
      "Don't wait to see whether it eases: a joint that won't take weight wants an X-ray today, at "
      "A&E or a minor injuries unit. Keep it still and raised on the way there.")),
    ("sprain", (r"\bsprain(?:ed)?\s+(?:my|his|her|their)\b",
                # "a sprained ankle", "sprained ankles": the injury named, not owned
                r"\bsprain(?:ed)?\s+(?:a|an|the|both|your)?\s*(?:ankle|ankles|knee|knees|wrist|"
                r"wrists|thumb|elbow)s?\b",
                r"\btwisted\s+my\s+(?:ankle|knee|wrist)\b",
               r"\brolled\s+my\s+ankle\b", r"\b(?:went\s+)?over\s+on\s+my\s+ankle\b",
               # a swollen joint after a fall is a sprain until a nurse says otherwise
               # "i hurt my knee at football": a joint knocked in a game is a sprain until seen
               r"\bhurt\s+(?:my|his|her|their)\s+(?:knee|ankle|wrist|shoulder|elbow)\b",
               r"\b(?:ankle|knee|wrist|elbow|foot|finger|thumb|shoulder)\b.{0,40}"
               r"\b(?:swollen|swelling|puffy|bruised|bruising)\b",
               r"\b(?:swollen|swelling|puffy|bruised|bruising)\b.{0,40}"
               r"\b(?:ankle|knee|wrist|elbow|foot|finger|thumb|shoulder)\b"),
     ("Rest it, put an ice pack on for 15 minutes at a time, and wrap it snugly but not tight; keep "
      "it up when you sit down. If you can't put weight on it or it swells badly, get it checked.",
      "Ice for 15 minutes, raise it, and take it easy for a day or two. If you can't bear weight or "
      "it's very swollen and bruising fast, have it looked at.")),
    # A limp is a leg, not a collapse: `urgent.py` found `limp` inside `limping` and a sprained
    # ankle got the ambulance script. The cure has to live above it, because a small injury is
    # this module's answer and the urgent module sits below. The food is the trap: limp celery,
    # limp lettuce and limp greens are the cooking rows' lines, and so is a limping pet the vet's.
    # A sight line with `all my life`, `since birth` or `born with` in it used to come back as the
    # weeks-to-the-GP limp card, because the ongoing-limp table is read for every line. The eye
    # has its own answer, and the alarm is the change, not the history (azure-trout's read of
    # #2292 found the family; a review of the limb table found the card).
    ("sight_long", SIGHT_EVER,
     SIGHT_LIFE_REPLIES),
    ("limp_long", LIMP_PERSON,
     ("A limp that has been going on for weeks is a GP job rather than A&E: book an appointment, "
      "say how long it has been there and what makes it worse, and keep up what you can do without "
      "pain meanwhile. Get it seen sooner if it is getting worse, if the joint gives way, or if "
      "there is swelling or heat in it.",)),
    ("limp", LIMP_PERSON,
     ("Check it while they are sitting: look for swelling and bruising, run a hand down the shin "
      "and press gently round the ankle and the knee, and see which way it hurts. Ice it for 15 "
      "minutes, rest it and give children's paracetamol if the age allows; if they will not put "
      "weight on it, the joint is swollen or hot, or a small child will not walk at all, that is "
      "the same day at a minor injuries unit.",
      "A limp that comes after a knock is rest, ice for 15 minutes and a day or two off it. Get it "
      "looked at the same day if you cannot put weight on it, if it is swollen or hot, or if a "
      "small child has stopped walking on it altogether.")),
    ("sunburn", (r"\bsun\s?burnt\b", r"\bsun\s?burn(?:ed)?\b", r"\bsunburn\b"),
     ("Get out of the sun, cool the skin with a shower or a damp cloth, and drink plenty of water; "
      "calamine or after-sun takes the sting out. Blisters, shivering or feeling faint need a doctor, "
      "and keep it covered for a few days.",
      "Cool showers, plenty of water and a loose cotton shirt are what help; leave blisters alone. "
      "If someone is shivery, dizzy or badly blistered, that needs a doctor.")),
    ("splinter", (r"\bsplinter\b",),
     ("Soak it in warm water for ten minutes and pull it out with tweezers in the direction it went "
      "in. If it's deep, under a nail, or the area gets red and hot, get it looked at.",
      "Warm water first, then tweezers along the line it went in. Anything deep or going red and hot "
      "should be checked.")),
    ("broken", (r"\b(?:broken|broke|fractured)\s+(?:my|his|her|their|a)\b.{0,25}\b(?:arm|leg|wrist|"
                r"ankle|hip|finger|thumb|toe|ribs?|collarbone|shoulder|foot|hand|nose|knee|elbow)\b",
                # The bone first and the verb after it, which is how half of these are typed: "my
                # ribs are broken", "my ribs are cracked" were "Thanks for telling me" (honey-bat,
                # msg 82387). Only the ribs: every other limb already has a better answer - the
                # wrist, the ankle and the finger get the four-steps test and the "how do i know if
                # it is broken" question, which says more than this card and is not the same line.
                r"\bmy\s+(?:ribs?)\s+(?:is|are|'s|'re|feels?|looks?)\s+"
                r"(?:broken|cracked|fractured|snapped)\b",
                # ...and "cracked" and "snapped" were not verbs this row knew at all: "i cracked a
                # rib" was a shrug. A neck and a back are left out because cracking your own neck
                # or back is a habit rather than an injury.
                r"\b(?:cracked|crack|snapped|snap|broke|broken|fractured)\s+"
                r"(?:a|my|his|her|their|two|three)\s+(?:ribs?|rib\s?cage)\b",
                r"\bthink\s+(?:i'?ve\s+)?(?:broken|fractured)\b", r"\b(?:bone|wrist|arm|leg)\b.{0,25}"
                r"\b(?:sticking|poking|piercing)\s+out\b",
                # The same injury said the other way round, and the way a rib is usually said:
                # "my ribs are broken" and "i think i cracked a rib" were a chat nod and a punt,
                # while "i broke a rib" was answered. The verb and the part swap places, and a
                # crack is a break. A rack of ribs is the butcher's, so the meat is read off.
                r"\b(?:my|his|her|their)\s+ribs?\b[^.?!]{0,15}"
                r"\b(?:is|are|was|were|got|might\s+be|may\s+be|feels?)\b[^.?!]{0,10}"
                r"\b(?:broken|cracked|fractured)\b",
                r"\b(?:cracked|crack|broke|broken|fractured)\s+(?:a|my|his|her|their)\s+ribs?\b"
                r"(?!\s+(?:of\s+beef|of\s+pork|joint|roast|recipe|rub|rack))",
                r"\bthink\s+(?:i'?ve\s+|i\s+)?(?:cracked|broken|fractured)\s+"
                r"(?:a\s+|my\s+)?ribs?\b",
                # and the injury with no owner at all: "cracked rib" and "broken rib what do i
                # do" were a chat nod and a punt. The butcher's ribs are named next to the word
                # when they are the subject, so the meat is read off.
                r"\b(?:broken|cracked|fractured)\s+ribs?\b"
                r"(?!\s*(?:of\s+(?:beef|pork|lamb)|joint|roast|recipe|rub|rack|in\s+the))",
                # The bone first is the same injury said the other way round, and only the bones
                # the rest of the bot has no answer for are here: a wrist, an ankle, a hand, a foot,
                # a collarbone that is fractured and a jaw that clicks all get a card from the
                # health module that says more than this one, so this row leaves them alone and
                # fills the gaps instead - a jaw or a nose said as broken or fractured, a nose that
                # is snapped, a collarbone that is snapped.
                r"(?:^|[,.!?;]|\band\b|\bbut\b|\bso\b|\bi\s+think\b|\bi\s+reckon\b)\s*"
                r"(?:my|his|her|their)\s+jaw\b[^.?!]{0,15}"
                r"\b(?:is|are|'?s|'?re|was|were)\s+(?:broken|fractured)\b(?!\s+out\b)",
                r"(?:^|[,.!?;]|\band\b|\bbut\b|\bso\b|\bi\s+think\b|\bi\s+reckon\b)\s*"
                r"(?:my|his|her|their)\s+nose\b[^.?!]{0,15}"
                r"\b(?:is|are|'?s|'?re|was|were)\s+"
                r"(?:broken|cracked|fractured|snapped)\b(?!\s+out\b)",
                # ...and a collarbone only when it is snapped: "my collarbone is broken" and
                # "...fractured" already get the health module's card, which says more.
                r"(?:^|[,.!?;]|\band\b|\bbut\b|\bso\b|\bi\s+think\b|\bi\s+reckon\b)\s*"
                r"(?:my|his|her|their)\s+collarbone\b[^.?!]{0,15}"
                r"\b(?:is|are|'?s|'?re|was|were)\s+snapped\b",
                r"\b(?:broken|broke|fractured)\s+(?:my|his|her|their)\s+jaw\b",
                r"\b(?:broken|broke|fractured|cracked|snapped)\s+(?:my|his|her|their)\s+nose\b",
                r"\b(?:snapped)\s+(?:my|his|her|their)\s+collarbone\b",
                # A finger or a toe at a funny angle is a fracture that gets seen today, not the
                # "stay where you are and ring 999" card the arm gets: "my finger is bent" and
                # "my toe looks bent" were both a shrug.
                r"\b(?:my|his|her|their|your)\s+(?:fingers?|thumb|toes?)\b[^.?!]{0,20}"
                r"\b(?:is|are|looks?|went|gone|got)\s+(?:all\s+)?(?:bent|bent\s+back|twisted|"
                r"out\s+of\s+shape|at\s+a\s+funny\s+angle)\b"),
     ("Keep it still and supported, ice it for twenty minutes and take paracetamol; don't try to "
      "straighten it yourself. Go to A&E or a minor injuries unit, and ring 999 if the bone is "
      "through the skin, it looks bent, or the fingers or toes go numb or white.",
      "Support it where it is, ice it and take painkillers; a bent limb, bone through the skin or "
      "numb fingers is 999, otherwise get it checked at A&E or a minor injuries unit today.")),
)

import re

# ---------------- what a breath, a heat, a pet, a swelling, a sting and a weight do
# A closed family: it reads nothing outside itself, so it moves without changing a reply.
# The laugh that took the breath, the pet out of puff, the heat a person cannot breathe in,
# the reaction to something eaten or a sting, and the weight that came down. `safety.py`
# imports them back by name.
# A laugh takes the breath in bursts, and people say so in three shapes: the breath and then the
# laugh that does it ("i cant catch my breath when i laugh"), the laugh and then what it did ("i
# laugh so hard i cant breathe"), and the breath the laugh took ("laughing makes me lose my
# breath"). All three were the 999 card on main, which is the bot reading a good time as an
# emergency. Only the laugh is allowed to explain the breath here, so a laugh beside a breath it
# did not cause ("i cant breathe and the kids were laughing") keeps its card.
LAUGH_WORD = (
    r"\blaugh\w*\b", r"\bgiggl\w*\b", r"\bchuckl\w*\b", r"\blol\b",
)
LAUGH_TAKES_BREATH = (
    r"\bbreath\w*\b[^.!?]{0,30}\b(?:when|whenever|if|while|after)\b[^.!?]{0,20}"
    r"\blaugh\w*\b",
    r"\b(?:when|whenever|while|if|after)\b[^.!?]{0,15}\blaugh\w*\b[^.!?]{0,40}"
    r"\bbreath\w*\b",
    r"\blaugh\w*\b[^.!?]{0,40}\b(?:can'?t|cannot|couldn'?t|makes?\s+me|lose|lost|losing)\b"
    r"[^.!?]{0,20}\bbreath\w*\b",
    r"\blaugh\w*\b[^.!?]{0,40}\b(?:out\s+of\s+(?:breath|puff)|breathless|puffed|winded)\b",
    r"\b(?:lose|lost|losing)\s+(?:my|his|her|their|our)\s+breath\b[^.!?]{0,25}\blaugh\w*\b",
    # "i cant get my breath laughing", "cant catch my breath laughing": the laugh comes after the
    # breath in the sentence, and the arms above all want it before (steward-frank-lamp, #7432).
    r"\bbreath\b[^.!?]{0,25}\blaugh\w*\b",
)
# A laugh that ends in a breath that did not come back is not the laugh: those lines keep the
# ambulance, and so does a chest, a wheeze or a faint beside it (see BREATH_RED).
LAUGH_BREATH_RED = (
    r"\b(?:stopped\s+breathing|isn'?t\s+breathing|not\s+breathing|gasping|turned\s+blue|"
    r"went\s+blue|blue\s+lips|pass(?:ed)?\s+out|blacked\s+out|fainted|faint|collapsed|"
    r"hurts?|wheez\w*|"
    # A breath that goes while laughing is the laugh's; a breath that goes in the night is the
    # heart's, and "i cant catch my breath when i laugh at night" was the night card on main.
    r"at\s+night|in\s+the\s+(?:night|evening)|during\s+the\s+night|night[\s-]?time|"
    r"wok(?:e|en)(?:\s+up)?|wakes?\s+(?:me|up)|waking\s+(?:up|me)|"
    r"coughing\s+up|blood|dizz\w*|light[\s-]?headed|see\s+stars|blurr\w*|"
    # A laugh explains a breath that came back. "i was laughing and now i cant breathe", "i laughed
    # and now i cant breathe at all" and "i was laughing and i still cant breathe" are a breath that
    # has not come back, and they keep the ambulance the laugh arm was taking from them
    # (mint-brick, #safety 92703). "for a minute" is left out on purpose: "i laughed so hard i
    # couldnt breathe for a minute" is the laugh, and a minute is how long the breath took.
    r"\bnow\b|\bat\s+all\b|\bstill\b|\bnot\s+(?:coming|getting|back|stopping)\b|"
    r"\b(?:hasn'?t|havent|haven'?t|didnt|didn'?t|won'?t|wont)\s+(?:come|got|get|stop)\b|"
    r"\b(?:been\s+going|going|gone)\s+on\s+for\b|\bfor\s+\d+\s+(?:minutes?|hours?)\s+now\b|"
    # A length of time that is not a few seconds: "i laugh and then i cant get my breath back for
    # ages" was "comes back within a few seconds, so there is nothing to worry about"
    # (close-falcon, #7432). "for a minute" stays out, because that is how long the laugh takes.
    r"(?:\bfor|\btakes?)\s+(?:ages|a\s+(?:long\s+)?(?:while|time)|minutes)\b)\b",
)
# The laugh arm reads a laugh and a breath as one person's. A child or a partner whose breath did
# not come back is not the speaker's good laugh: "my son was laughing and then he couldnt breathe"
# was "that one is normal" with a pattern that only saw a laugh and a breath. Present-tense
# "my son laughs so hard he cant breathe" is the ordinary laugh, so "cant" alone is not enough.
LAUGH_OTHER_PERSON = (
    r"\b(?:he|she|they)\b[^.?!]{0,25}"
    r"\b(?:couldn'?t|couldnt|stopped|wasnt|was\s+not|isnt|is\s+not)\b[^.?!]{0,15}\bbreath\w*",
    r"\b(?:my|our|her|his|their)\s+(?:son|daughter|child|kid|baby|boy|girl|husband|wife|partner|"
    r"mum|mom|dad|father|mother|brother|sister|nan|grandma|grandad|grandmother|grandfather|"
    r"friend|mate|neighbour|neighbor)\b[^.?!]{0,25}\b(?:was|were)\s+laugh\w*",
    r"\b(?:someone|somebody)\b[^.?!]{0,20}\b(?:couldn'?t|couldnt|stopped)\b[^.?!]{0,12}"
    r"\bbreath\w*",
)

# The animal is the one out of puff, so it has to be the animal that is out of puff: the pet comes
# first and its breath after it, or "i get breathless walking the dog" - a person's own line - is
# read as the dog's. "my dog gets breathless on the stairs" was getting the human GP card about
# having a chest listened to.
PET_BREATH = (
    r"\b(?:dog|dogs|pupp\w*|cat|cats|kitten|kittens|pet|parrot|budgie|hamster|rabbit|bunny|"
    r"horse|pony|guinea\s+pig|tortoise|ferret|gerbil|rat|lizard|snake|animal)\b\s*"
    # "my dog, he gets breathless on the stairs" names the animal and then the symptom, the way
    # people talk about a pet, and the comma stood the animal away from the verb so the line got
    # the human GP card.
    r"(?:,\s*(?:he|she|it)\s+)?"
    r"(?:is|are|was|were|gets?|got|keeps?|seems?|looks?|sounds?|'s|has\s+been|have\s+been)\s+"
    r"(?:\w+\s+){0,2}"
    r"(?:breathless|out\s+of\s+(?:puff|breath)|puffed|winded)\b",
    # "my dog cant catch his breath" (rose-wasp, #7432): the same out-of-puff line in the words
    # people use for a pet, and with the animal first so "i cant catch my breath" stays the person's.
    r"\b(?:dog|dogs|pupp\w*|cat|cats|kitten|kittens|pet|parrot|budgie|hamster|rabbit|bunny|"
    r"horse|pony|guinea\s+pig|tortoise|ferret|gerbil|rat|lizard|snake|animal)\b\s*"
    r"(?:,\s*(?:he|she|it)\s+)?"
    r"(?:(?:is|was|are|were|keeps?|'s)\s+)?"
    r"(?:can'?t|cannot|couldn'?t|could\s+not|is\s+not|isn'?t|struggl\w*)\s+"
    r"(?:to\s+)?(?:catch|get|find)\s+(?:his|her|its|their)\s+breath\b",
)
# "my dog cant catch his breath" is past being puffed: it is the same pet as one struggling to
# breathe, so it is the vet tonight rather than this week. It has to be the pet's breath, because
# "i cant catch my breath" is the person's card.
PET_BREATH_NOW = (
    r"\b(?:can'?t|cannot|couldn'?t|could\s+not|struggl\w*|struggled)\s+(?:to\s+)?"
    r"(?:catch|get|find)\s+(?:his|her|its|their)\s+breath\b",
)
# The effort is the answer for a pet as much as for a person: a cat breathless after playing, a dog
# puffed after its walk or out of breath running in the park, is a question about play and heat, and
# the everyday answer was right. Only a pet out of puff with no effort to explain it is the vet's.
PET_EFFORT = (
    r"\b(?:play\w*|running|ran(?:\s+about)?|runs?\b|fetch\w*|walk\w*|park|chase\w*|ball|"
    r"exercise\w*|training|agility|swim\w*|"
    # A ridden horse is a working animal, so its own gaits are the effort that explains the puff:
    # "my horse is out of breath after a trot" was the vet-this-week card about a dog or a cat.
    r"trot\w*|canter\w*|gallop\w*|ride|rides|riding|ridden|lunge\w*|hack\w*|jump\w*|"
    r"lesson|schooling)\b",
)
# A pet named and then repeated - "my dog, he cant breathe" - is the same animal as the one beside
# the verb, and the comma was enough to send the line to the human breath card, which told someone
# to start CPR on their dog.
_PET_APPOSITIVE = (
    r"\b(?:dog|dogs|pupp\w*|cat|cats|kitten|kittens|pet|parrot|budgie|hamster|rabbit|bunny|"
    r"horse|pony|guinea\s+pig|tortoise|ferret|gerbil|rat|lizard|snake|animal)\b\s*,\s*"
    r"(?:he|she|it)\b"
)
PET_APPOSITIVE = (_PET_APPOSITIVE,)
# The "he" in "my dog, he cant breathe" is the dog, so the pet is taken out of the line before the
# question "is a person the patient here?" is asked of it.
PET_APPOSITIVE_SUB = re.compile(_PET_APPOSITIVE, re.I)
# ...and "my cat is breathless and her gums are pale" was the gums card, which is the emergency
# version of the same visit, so any line that names the gums keeps the card it had.
# A pet that cannot settle is working to breathe, which is tonight rather than this week: both
# week cards say "ring today if it cannot settle", so the line that says it cannot settle gets the
# vet-now card the rest of the pet trouble gets.
PET_CANT_SETTLE = (
    r"\b(?:can'?t|cannot|won'?t|wont|not)\s+(?:get\s+)?(?:comfortable|comfy|settle[ds]?)\b",
)

# The heat is a cause of a short breath that a line can name: "i cant breathe in this heat" got the
# 999 card on main. Only the words that put the weather in the line, not a bare "hot".
HEAT_CAUSE = (
    r"\b(?:this|the|all\s+this)\s+heat\b|\bheat\s?wave\b|\bhumidi(?:d|ty)\b|\bhumidity\b|"
    r"\b(?:hot|boiling|muggy|stifling|sweltering)\s+(?:weather|day|room|office|night|bus|tube)\b|"
    r"\b(?:so|too|really|very)\s+(?:hot|humid|muggy|stuffy)\b|"
    r"\bheat\s+of\s+the\s+day\b|\b\d{2,3}\s*degrees\b",
)
# The heat that takes the breath is the weather or the room. "so hot" is also how a chilli is
# described, and "the chilli was so hot i couldnt breathe" was the heatwave card telling a person
# to open windows, so food heat stands the card down.
HEAT_NOT_WEATHER = (
    r"\b(?:chilli?|chili|curry|pepper\w*|spic(?:y|e|ier|iest)|wasabi|horseradish|mustard|"
    r"salsa|sauce|wings|broth|soup|kebab|taco\w*|jalape\w*|paprika|ginger|"
    r"oven|grill|barbecue|bbq|bonfire|sauna|steam(?:er|y)?|toaster?)\b",
)
# A breath the line itself is about: "i cant breathe in this heat". A room that is too hot to
# breathe in is not the person's breathing.
BREATH_BARE = (
    r"\b(?:can'?t|cannot|couldn'?t|hard\s+to|difficult\s+to)\s*"
    r"(?:breathe|breath\b|get\s+my\s+breath|catch\s+my\s+breath)\b|"
    r"\bstruggl\w*\s+(?:to\s+)?breathe\b",
)
# The heat explains a breath that comes back once the person is cool. These are the signs that it
# is not the heat, and they keep the ambulance.
HEAT_BREATH_RED = (
    r"\b(?:faint\w*|dizz\w*|light[\s-]?headed|confus\w*|sick|vomit\w*|"
    r"one\s+side|slurr\w*|for\s+hours?|all\s+day|since\s+(?:yesterday|this\s+morning)|"
    # A person who tells you they have asthma is not helped by being told it is the heat.
    r"asthma|inhaler|COPD\b|"
    # A person who tells you they have asthma is not helped by being told it is the heat.
    r"not\s+settl\w*|wont\s+settle|won'?t\s+settle|no\s+better|getting\s+worse)\b",
)

# A swelling or a rash that arrives after something eaten is an allergic reaction, and the trigger
# can be any food: "my baby has a swollen lip after eating egg" was the omelette recipe on main,
# and "my daughter has hives after eating strawberries" the kids' tea. The first shape needs the
# reaction and the "after" in the line; the last one is the "had X and now her face is puffy"
# order, which has no "after" in it at all.
ALLERGY_FOOD = (
    r"\b(?:swelling|swollen|swelled|puff\w*\s+up|puffed\s+up|puffing\s+up|puffy|hives?|urticaria|"
    r"welts?|blotch\w*|rash)\b[^.!?]{0,45}\b(?:after|from|since|because\s+of)\b[^.!?]{0,25}"
    r"\b(?:eat\w*|ate|eaten|having|had|drank|drink\w*|tried|tast\w*|bit\s+into|food|meal|"
    r"breakfast|lunch|dinner|snack|formula|milk|sting\w*|stung|bee|wasp|antibiotic\w*|medicine|"
    r"tablet\w*)\b",
    r"\b(?:after|from)\b[^.!?]{0,15}\b(?:eating|having|drinking|trying|tasting|taking)\b"
    r"[^.!?]{0,30}\b(?:swelling|swollen|swelled|puff\w*|puffy|hives?|urticaria|welts?|rash|"
    r"itch\w*|tingl\w*|blotch\w*)\b",
    # "my son got stung by a bee and now his hand is swollen": the sting first, the swelling after.
    r"\b(?:stung|stings?)\b[^.!?]{0,30}\b(?:and|,)\b[^.!?]{0,20}\b(?:now\s+)?"
    r"\b(?:her|his|their|my|our|the)\b[^.!?]{0,18}"
    r"\b(?:hand|arm|foot|leg|face|lips?|tongue|throat|finger|ankle|wrist|cheeks?)\b"
    r"[^.!?]{0,20}\b(?:swell\w*|swollen|puff\w*|itch\w*|hives?|rash)\b",
    # "my baby had egg and now her face is puffy": the food first, the reaction after the "and".
    r"\b(?:ate|eaten|eating|had|tried|drank|drinking)\b[^.!?]{0,30}\b(?:and|,)\b[^.!?]{0,20}"
    r"\b(?:her|his|their|my|our|the)\b[^.!?]{0,18}\b(?:lips?|tongue|throat|face|mouth|cheeks?)\b"
    r"[^.!?]{0,20}\b(?:puff\w*|puffy|swell\w*|swollen|itch\w*|tingl\w*|hives?|rash)\b",
)
# The signs that say this is the ambulance and not the watch-it-hour card: an airway or a swallow
# that has changed, a voice, a faint or a person who has gone quiet.
ALLERGY_AIRWAY = (
    r"\b(?:tongue|throat|voice|swallow\w*|breath\w*|can'?t\s+breathe|wheez\w*|faint\w*|"
    r"dizz\w*|limp|floppy|collapse\w*|unconscious|shock)\b",
)
# A cold, chapped lips or the lip a person bit are swellings too, and none of them is a reaction.
ALLERGY_OFF = (
    r"\b(?:chapped|cold\s+sore|piercing|teething|dummy|chewed|bit\s+my\s+lip|bitten\s+lip|"
    r"sunburn\w*|in\s+the\s+cold|from\s+the\s+cold|dehydrat\w*|mouth\s+ulcer|bump\w*\s+it)\b",
)

# Where the swelling is matters more than what caused it: a lip, tongue, throat or face after a
# sting is the airway card, and a hand or an arm is the sting's own watch-it card.
ALLERGY_FACE = (
    r"\b(?:lips?|tongue|throat|face|mouth|cheeks?)\b",
)
STING_WORDS = (
    r"\b(?:bee|bees|wasp|wasps|hornet\w*|stung|stings?|bumble\s?bee\w*)\b",
)
FOOD_WORDS = (
    r"\b(?:eat\w*|ate|eaten|food|meal|breakfast|lunch|dinner|snack|formula|milk|drank|drink\w*)\b",
)

# Something heavy coming down on a person is an injury, and the line often has no injury word in
# it: "the scaffolding has collapsed and someone is under it" got "Got it. Is there anything you'd
# like a hand with?" on main, "a wall has fallen on someone" got nothing, and "he got crushed by a
# machine" got nothing (free-carpet, #safety 97225). "came down on my neighbour" and "the shed fell
# on my dad" were already the ambulance, so this is the same event written with the person under it
# instead of after "on".
# What a thing came down on decides whether it is an ambulance: "the fence fell on my shed", "a
# tree fell on my car" and "the ceiling came down on my bed" are property, while "the shed fell on
# my dad" and "the branch came down on my leg" are not. The first draft of this table read `my \w+`
# after "on", so every "X fell on my <anything>" rang 999 (@sound-wolf, #safety 140296). So the
# word after the possessive has to be a person or a part of one, and a bare thing stands down.
CRUSH_ON_A_PERSON = (
    r"\b(?:someone|somebody|a\s+(?:man|woman|child|kid|bloke|lady|person)|him|her|them|people|"
    r"anyone|everyone)\b",
    r"\b(?:my|his|her|their|our|your)\s+(?:husband|wife|partner|fianc|boyfriend|girlfriend|son|"
    r"daughter|child|kid|kids|baby|boy|girl|mum|mom|mother|dad|father|brother|sister|friend|"
    r"mate|neighbour|neighbor|gran|granny|grandma|grandad|grandpa|uncle|aunt|cousin|nan|nana|"
    r"colleague|boss|carer|lodger|housemate|flatmate|dog|cat|puppy|kitten|pet|"
    r"hands?|fingers?|thumbs?|arms?|wrists?|elbows?|legs?|feet|foot|toes?|knees?|ankles?|shins?|"
    r"chest|back|head|neck|face|shoulders?|hips?|ribs|pelvis|thighs?|calf|calves|torso|spine|"
    r"belly|stomach|lap)\b",
)
# The same rule read the other way round: "the ceiling came down on me", "a tree fell on us" and
# "the wall collapsed on top of me" name the person with a pronoun instead of a possessive, and on
# main every one of them was a shrug ("That's a rotten one. How bad is it?") while a roof that came
# down on a shed rang 999. The pronoun is only a person if something heavy is what came down, so
# the thing comes first in the pattern: a book that fell on a person in bed, rain that came down on
# a walk and a cat that fell on a lap all stay out of it.
CRUSH_HEAVY_ON_A_PRONOUN = (
    r"\b(?:roof|roofs|roofing|chimney|ceiling|ceilings|wall|walls|beam|beams|joist|joists|"
    r"scaffold\w*|slab|slabs|brick|bricks|masonry|rubble|debris|wardrobe|cupboard|shelves|shelf|"
    r"bookcase|cabinet|fridge|freezer|door|ladder|television|tv|mirror|glass|window|tiles?|"
    r"slates?|gutter\w*|fence|fencing|panel|panels|gate|garage\s+door|car|van|lorry|truck|"
    r"container|pallet|machinery|machine|tree|trees|branch|branches|trunk|limb)\b"
    r"[^.!?]{0,30}"
    r"\b(?:fallen|fell|come\s+down|came\s+down|collapsed|toppled|tumbled|gave\s+way)\b"
    r"[^.!?]{0,20}\b(?:on|onto)\b[^.!?]{0,15}"
    r"\b(?:me|us|myself|yourself|himself|herself|themselves|everybody|everyone|someone|"
    r"somebody|anyone|anybody)\b"
)
CRUSH = (
    CRUSH_HEAVY_ON_A_PRONOUN,
    r"\b(?:collapsed|fallen|fell|come\s+down|came\s+down|tumbled|toppled|gave\s+way|give\s+way)\b"
    r"[^.!?]{0,30}\b(?:and|,|with)\b[^.!?]{0,25}"
    r"(?:" + "|".join(CRUSH_ON_A_PERSON) + r")"
    r"[^.!?]{0,25}\b(?:under|underneath|trapped|stuck|pinned|buried)\b",
    r"\b(?:fallen|fell|came\s+down|come\s+down|collapsed|toppled|toppled\s+over)\b[^.!?]{0,20}"
    r"\b(?:on|onto)\b[^.!?]{0,15}"
    r"(?:" + "|".join(CRUSH_ON_A_PERSON) + r")",
    # A person crushed or pinned by something heavy, whoever writes it.
    r"\b(?:someone|somebody|a\s+(?:man|woman|child|kid|person)|my\s+\w+|he|she|they|i)\b"
    r"[^.!?]{0,25}\b(?:crushed|pinned|buried|trapped)\b[^.!?]{0,15}\b(?:by|under|underneath)\b",
    r"\b(?:crushed|pinned)\s+(?:by|under)\b[^.!?]{0,25}"
    r"\b(?:machine|machinery|truck|van|car|lorry|wall|ceiling|roof|beam|scaffold\w*|slab|"
    r"container|pallet|forklift|tractor|rubble|debris)\b",
)
# A duvet, a pillow or a pet on top of a person is not somebody pinned under a wall.
CRUSH_OFF = (
    r"\b(?:duvet|blanket|quilt|covers|pillow|cushions?|bed|toddler|cat|dog|puppy|kitten)\b",
)
# ... unless the line also names the thing that did it, because "the wall came down with the cat
# under it" is about the wall.
CRUSH_HARD = (
    r"\b(?:machine\w*|truck|van|car|lorry|wall|walls|ceiling|roof|beam|scaffold\w*|slab|"
    r"container|pallet|forklift|tractor|rubble|debris|tree|branch|gate|lift|door)\b",
)

# A stroke sign in the person's own body belongs to the person, whatever animal is named in the
# same line. On main `3dd9e92d` "the dog is fine but my arm has gone weak" rang 999; once a pet in
# the line stood the stroke card down, that line became a shrug while the animal was fine and the
# arm was not. So the standdown needs the animal to be the one with the symptom.
MY_OWN_PART = (
    r"\bmy\s+(?:arm|arms|leg|legs|hand|hands|face|side|foot|feet|mouth|eye|eyes|lip|lips|cheek|"
    r"shoulder|hip|knee|grip|voice|speech|vision|tongue|fingers|toes)\b",
    r"\b(?:i|im|i'm)\b[^.?!]{0,14}\b(?:can'?t|cannot|couldn'?t|struggling\s+to|unable\s+to)\s+"
    r"(?:see|walk|feel|talk|speak|hold|move|smile|swallow)\b",
    r"\b(?:i|im|i'm)\b[^.?!]{0,8}\b(?:have|ve|'ve)\s+(?:gone|become)\s+(?:weak|numb|blind)\b",
)

# The shapes of a weakness rather than a sight problem, so that a pet whose side has gone gets the
# vet card below while "my cat is going blind" keeps the pet sight answer it already had.
PET_WEAK = (
    r"\b(?:on\s+)?(?:one|his|her|its|their|the|left|right)\s+side\b",
    r"\b(?:gone|gone\s+all|has\s+gone|have\s+gone)\s+weak\b",
    r"\b(?:is|are|seems|looks|been)\s+weak\s+(?:on|in|down)\b",
    r"\b(?:half|one\s+half)\s+of\s+(?:his|her|its|their)\s+(?:body|face)\b",
    r"\bdroop\w*|\bdropping\b",
    r"\bdragging\b|\bdragged\b",
    r"\btilt(?:ed|ing)\b",
    r"\b(?:back|front|hind)\s+legs?\b",
)
