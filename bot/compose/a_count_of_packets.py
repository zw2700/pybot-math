"""A count of packets is a dose, not a shopping list.

`i swallowed two packets of pills` was answered with how to take one tablet - "Take a mouthful of
water first, put the tablet further back on your tongue than feels natural and swallow with a
drink" - which is the worst reply there is to somebody who has just taken two packets. The poisons
case in `bot/modules/safety.py` reads an amount (`PILLS_OVERDOSE`, `DOSE_WHOLE_PACK`), and every
arm of it wants the word whole, full or entire before the packet, or a number the size of a
handful of tablets. A number and a plural packet is how people word it when they are frightened,
so the shape was answered by whoever else had a card for the words: the tablet-taking card for
`swallowed`, and a nod for the rest.

This reader is the container count only, and it says nothing else: it does not read a drug, an
intent or a time, and it never fires on a packet that is being bought, carried or kept. The card
itself is safety's (`REPLIES["poison"]`), so the wording stays in one place.

Three readings keep the emergency where it belongs:

* **An animal is not a person.** `my dog swallowed two packets of pills` is the vet's card, and
  999 for a dog is worse than the shrug it replaced, so a line whose subject is an animal is
  stood down here and left to the pet reader.
* **Stock has to be said on the packet, not somewhere in the sentence.** `we are away this week
  and i took two packets of pills` is somebody telling you what they did, and `i took two packets
  of pills and left the house` is the same; only a frame that sits on the packet ("for the trip",
  "on holiday with me", "in my bag", "from the pharmacy") makes a count stock.
* **A hand-over is a dose.** `i gave my child two packets of pills` is the count as much as
  `i swallowed` is.
"""
import re

COUNT = (r"(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,3}|"
         r"a\s+couple\s+of|a\s+few|several|a\s+handful\s+of)")
CONTAINER = (r"(?:packets?|packs?|boxes|box|bottles?|blisters?|strips?|sleeves?|sachets?|"
             r"handfuls?)")
DRUG = (r"(?:pills|tablets|paracetamol|ibuprofen|painkillers|analgesics|meds|medicines?|"
        r"sleeping\s+pills|antidepressants|tranquill?i[sz]ers?|insulin|codeine|co[\s-]?codamol|"
        r"codamol|tramadol|morphine|diazepam|cough\s+medicine|painkillers?)")
VERB = (r"(?:swallowed|swallowing|drank|drunk|eaten|ate|took|taken|downed|inhaled|popped|necked|"
        r"finished|used|washed\s+down|swilled|gulped|gave|given|handed)")

# The count of containers itself: "two packets of pills". Both readings below are built on it, and
# so are the two stock frames, which is the point of having it in one place.
PACKETS = (COUNT + r"\s+" + CONTAINER + r"\s+of\s+[^.?!]{0,15}\b" + DRUG + r"\b")

# Taken, and the amount is a count of containers: "i swallowed two packets of pills".
TAKEN = re.compile(r"\b" + VERB + r"\b[^.?!]{0,25}\b" + PACKETS)

# The same with no verb at all, which is how people write it in a panic: "two packets of pills and
# i feel sick". A count of packets on its own is also a shopping list, so this one wants a sign
# that something has already gone wrong as well as the count.
NO_VERB = re.compile(r"\b" + PACKETS +
                     r"[^.?!]{0,25}\b(?:feel|felt|feeling|sick|ill|dizzy|drowsy|sleepy|vomit\w*|"
                     r"throwing\s+up|shak\w*|blurry|off\s+my\s+face|can'?t\s+stay\s+awake|"
                     r"sleeping\s+all\s+day|swallow\w*|and\s+then\s+i|and\s+now\s+i)\b")

# An animal that took something is the vet's patient, not the ambulance's: `my dog swallowed two
# packets of pills` is answered by the pet-poisoning card, and 999 for a dog is worse than the nod
# it replaced. The animal has to be the one doing the taking, so "i took two packets of pills and
# the dog is asleep" stays a dose.
AN_ANIMAL = (r"(?:dogs?|pupp(?:y|ies)|cats?|kittens?|rabbits?|bunn(?:y|ies)|hamsters?|budgies?|"
             r"birds?|parrots?|horses?|pon(?:y|ies)|guinea\s+pigs?|gerbils?|ferrets?|tortoises?|"
             r"animals?|pets?)")
AN_ANIMAL_TOOK = re.compile(r"\b" + AN_ANIMAL + r"\b[^.?!]{0,25}\b" + VERB + r"\b")

# A packet that is bought, carried, kept or packed is stock, not a dose. "i bought two packets of
# paracetamol" and "my bag has two packets of pills in it" are the same words about shopping, and
# the poisons card on them is the bot crying wolf on a line where the person did nothing.
#
# The frame has to sit on the packet. "we are away this week and i took two packets of pills" is
# somebody telling you what they did, and a bare "away" or "left" anywhere in the line used to
# stand the card down on it - the one outcome this reader exists to prevent. So a buying word
# counts when it is before the count, and a trip, a bag or a shelf counts when it is on it.
PACKET_WORDS_BEFORE = re.compile(r"\b(?:buy|buys|buying|bought|shop|shopping|order|ordered|"
                                 r"prescription|prescribed|pharmacy|chemist|doctor|gp|nurse|"
                                 r"getting|pick\s+up|picked\s+up|stock|stocked\s+up|spare|"
                                 r"first\s+aid)\b[^.?!]{0,30}" + PACKETS)
PACKET_WORDS_ON = re.compile(r"\b" + PACKETS +
                             r"[^.?!]{0,25}\b(?:for\s+(?:the|a|my)\s+(?:trip|holiday|weekend|"
                             r"flight|journey|kids)|on\s+holiday|on\s+business|to\s+take\s+away|"
                             r"away\s+with\s+me|in\s+my\s+(?:bag|pocket|suitcase|handbag|purse)|"
                             r"in\s+the\s+(?:cupboard|drawer|cabinet|glovebox)|at\s+home|"
                             r"left\s+over|spare|abroad)\b")
# ... and the place a packet is kept, which is stock only when the line frames it as keeping: "my
# bag has two packets of pills in it" is a bag, while "i took two packets of pills from the
# cupboard" is somebody saying where they got them, and the cupboard there is not the answer.
STOCK_PLACE = re.compile(r"\b(?:in|inside|kept\s+in|keep\s+in|keeps\s+in|have|has|got|carry|"
                         r"carrying|stash)\b[^.?!]{0,20}\b(?:cupboard|drawer|cabinet|shelf|"
                         r"shelves|bag|pocket|purse|glovebox)\b")


def is_a_dose(text):
    """True when the line says an amount of medicine as a count of packets somebody has taken."""
    line = " ".join((text or "").lower().split())
    if not line:
        return False
    if AN_ANIMAL_TOOK.search(line):
        return False
    if (PACKET_WORDS_BEFORE.search(line) or PACKET_WORDS_ON.search(line)
            or STOCK_PLACE.search(line)):
        return False
    return bool(TAKEN.search(line) or NO_VERB.search(line))
