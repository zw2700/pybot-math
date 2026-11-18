"""A fact that belongs to the person's address, which only a postcode can answer.

The fallback cannot see where the person lives, but every such fact has one official lookup
that needs nothing else: theyworkforyou for the MP, the MSP, the MS and the MLA, the council
for the ward and the polling station, the bill for the supplier, gov.uk for the flood map, the
council tax band and the EPC, Ofcom for the line, the council for the road, the catchment and
the smoke control area, the heritage list for a listed building, the water company for the
hardness, UKradon for the radon chance, and 105 for a power cut. This module reads the ask and
hands back the honest limit plus that lookup; it never guesses a fact.
"""

import re


# A fact that belongs to the place the person lives: who their MP is, which council area they
# are in, where the polling station is, who supplies the water and the gas, when the road is
# being resurfaced, which school's catchment they are in. The bot cannot see a postcode, so it
# cannot answer any of them - but every one has an official lookup that needs nothing else, and
# "put your postcode in there" is the one concrete thing a friend says. They used to reach the
# search hedge ("that's beyond what I know well... searching for it will turn up better
# sources"), which names neither the limit nor the place to look.
#
# Every pattern needs "my"/"our" or an ask shape that is about the person's own address, so
# "who is the mp for leeds" and "which council runs the bins in manchester" keep their own
# answers. It runs only inside the fallback, so a knowledge entry that answers the line keeps
# the turn.
POSTCODE_LOOKUPS = (
    ("representative", re.compile(
        r"\bwho(?:'s|s| is)?\s+(?:my|our)\s+(?:msp|ms|mla|member\s+of\s+the\s+senedd|"
        r"member\s+of\s+the\s+scottish\s+parliament|member\s+of\s+the\s+northern\s+"
        r"ireland\s+assembly)\b"
        r"|\bwhich\s+(?:msp|ms|mla)\s+(?:represents|covers)\s+"
        r"(?:me|my\s+(?:area|constituency|town|city|street)|our\s+(?:area|constituency|"
        r"town|city|street))\b"
        r"|\bwho\s+represents\s+me\s+in\s+the\s+(?:scottish\s+parliament|senedd|"
        r"northern\s+ireland\s+assembly)\b"),
     ("I can't see your postcode, so I can't name your MSP, MS or MLA. theyworkforyou.com "
      "takes a postcode and names the member for your area, with their office email.",
      "Nothing here that knows your address, so I can't name the member. Put the postcode into "
      "theyworkforyou.com and it gives your MSP, MS or MLA and their office.")),
    ("assembly", re.compile(
        r"\bwho(?:'s|s| is)?\s+(?:my|our)\s+(?:london\s+)?assembly\s+member\b"
        r"|\bwhich\s+(?:london\s+)?assembly\s+member\s+(?:represents|covers)\s+"
        r"(?:me|my\s+(?:area|constituency|town|city|street)|our\s+(?:area|constituency|"
        r"town|city|street))\b"),
     ("I can't see your postcode, so I can't name your assembly member. In London the London "
      "Assembly site lists the member for your constituency; in Scotland, Wales and Northern "
      "Ireland, theyworkforyou.com takes the postcode.",
      "Nothing here that knows your address, so I can't name the member. The London Assembly site "
      "lists London's members by constituency, and theyworkforyou.com covers Scotland, Wales and "
      "Northern Ireland.")),
    ("water hardness", re.compile(
        r"^(?:(?:and|but|so|then|ok|okay|please)\s+)*(?:is|how)\s+(?:my|our)\s+water\s+"
        r"(?:hard|soft)\b"
        r"|\bwhat(?:'s|s| is)?\s+(?:my|our)\s+water\s+(?:hardness|like)\b"
        r"|\bhow\s+hard\s+is\s+(?:my|our)\s+water\b"),
     ("I can't test your water from here. Your water company's site takes the postcode and gives "
      "the hardness for your supply; a test strip settles it if you want the number.",
      "Nothing here that has tested your water. Put the postcode into your water company's site "
      "and it gives the hardness for your supply, or a test strip gives the figure.")),
    ("radon", re.compile(
        r"\b(?:what(?:'s|s| is)?|how\s+(?:high|much)(?:\s+is)?)\s+(?:my|our)\s+radon"
        r"(?:\s+(?:level|risk|reading))?\b"
        r"|\bhow\s+much\s+radon\s+(?:is\s+)?(?:in|at)\s+(?:my|our)\s+"
        r"(?:house|home|area|street|property)\b"
        r"|\bis\s+(?:my|our)\s+(?:house|home|area|street|property)\s+(?:in\s+)?(?:a\s+)?"
        r"radon\s+(?:area|zone)\b"
        r"|\bam\s+i\s+in\s+a\s+radon\s+(?:area|zone)\b"),
     ("I can't see your address, so I can't tell you the radon level. UKradon's map takes the "
      "postcode and gives the chance for your area; a home test kit is the only way to know the "
      "level inside.",
      "Nothing here that knows your address. Put the postcode into UKradon's map for the chance "
      "in your area, and use a home test kit for the level inside.")),
    ("smoke control", re.compile(
        r"\bam\s+i\s+in\s+a\s+smoke\s+control\s+area\b"
        r"|\bis\s+(?:my|our)\s+(?:house|home|area|street|property)\s+in\s+a\s+"
        r"smoke\s+control\s+area\b"
        r"|\bwhat\s+smoke\s+control\s+area\s+am\s+i\s+in\b"),
     ("I can't see your address, so I can't say. Your council's smoke control page lists the "
      "areas, and it decides whether a wood burner or an open fire may emit smoke; its "
      "environmental health team confirms your street.",
      "Nothing here that knows your street. The council's smoke control page lists the areas and "
      "says whether a wood burner or open fire may emit smoke; environmental health confirms it.")),
    ("power cut", re.compile(
        r"\bwho\s+(?:do|should|can)\s+i\s+(?:call|ring|phone|contact)\s+"
        r"(?:about|during|in)\s+a\s+power\s+(?:cut|outage)\b"
        r"|\bwho\s+(?:do|should|can)\s+i\s+(?:call|ring|phone)\s+(?:when|if)\s+"
        r"(?:the\s+)?(?:power|electricity)\s+(?:goes|is)\s+(?:out|off)\b"
        r"|\b(?:who|which\s+number)\s+(?:do\s+i\s+)?(?:call|ring)\s+for\s+a\s+"
        r"power\s+cut\b"
        r"|\bhow\s+(?:do|can|should)\s+i\s+(?:report|log|tell\s+(?:someone|them)\s+about)\s+"
        r"(?:a\s+)?power\s+(?:cut|outage)\b"
        r"|\bwho\s+(?:do|should|can)\s+i\s+(?:tell|report\s+(?:it\s+)?to)\s+"
        r"(?:about\s+)?(?:a\s+)?power\s+(?:cut|outage)\b"),
     ("I can't see your address, so I can't name your network operator. Ring 105 - it is free and "
      "puts you through to the one that covers your postcode - or use its postcode map. If a line "
      "has come down, stay well clear and call 105.",
      "Nothing here that knows your postcode. Ring 105 free and it connects you to the network "
      "operator for your area, or use its postcode map; a fallen line needs staying clear and "
      "that call.")),
    ("mp", re.compile(
        r"\b(?:who(?:'s|s| is)?|what(?:'s|s| is)?|which)\s+(?:my|our)\s+(?:local\s+)?"
        r"(?:mp|member\s+of\s+parliament|constituency)\b"
        r"|\bwho(?:'s|s| is)?\s+(?:the\s+)?mp\s+for\s+(?:my|our)\s+"
        r"(?:area|constituency|town|city|street|road|ward|postcode|address)\b"
        r"|\b(?:which|what)\s+constituency\s+(?:am\s+i|do\s+i\s+live)\b"
        r"|\b(?:which|what)\s+constituency\s+(?:is|are)\s+(?:my|our)\b"
        r"|\b(?:which|what)\s+mp\s+(?:represents|covers)\s+(?:me|my\s+(?:area|constituency|"
        r"ward|town|city|street)|our\s+(?:area|constituency|ward|town|city|street))\b"
        r"|\bwho\s+represents\s+(?:me|my\s+(?:area|constituency|ward|town|city|street)|"
        r"our\s+(?:area|constituency|ward|town|city|street))\b"),
     ("I can't see your postcode from here. Put it into theyworkforyou.com and it names your MP "
      "and constituency, with their office email.",
      "Nothing here that knows your address, so I can't name the MP. theyworkforyou.com takes a "
      "postcode and gives the MP and the constituency office.")),
    ("councillor", re.compile(
        r"\b(?:who(?:'s|s| is)?|which)\s+(?:my|our)\s+(?:local\s+)?councill?or\b"
        r"|\b(?:which|what)\s+ward\s+(?:am|do)\s+i\b"
        r"|\bhow\s+(?:do|can)\s+i\s+(?:find|contact)\s+(?:my|our|the)\s+(?:local\s+)?councill?or\b"
        r"|\b(?:which|what)\s+councill?or\s+(?:represents|covers)\s+(?:me|this|my\s+(?:area|"
        r"ward|street|road|town|city)|our\s+(?:area|ward|street|road|town|city))\b"
        r"|\bwho\s+is\s+the\s+councill?or\s+for\s+(?:my\s+(?:area|ward|street|road|town|"
        r"city)|our\s+(?:area|ward|street|road|town|city)|this\s+(?:area|ward|street|road))\b"),
     ("I can't see which ward you are in. Your council's site takes a postcode and names your "
      "councillors, and writetothem.com does the same in one step.",
      "Nothing here that knows your ward, sorry. The council's own site, or writetothem.com, "
      "takes a postcode and gives the councillors for it.")),
    ("poll card", re.compile(
        r"\bwhere(?:'s|s| is)?\s+(?:my|our)\s+poll(?:ing)?\s+card\b"
        r"|\bmy\s+poll(?:ing)?\s+card\b[^.!?]{0,24}"
        r"\b(?:hasn'?t|hasnt|has\s+not|didn'?t|didnt|never)\b"
        r"|\b(?:i|we)\s+(?:have\s?n'?t|havent|haven'?t|did\s?n'?t|didnt)\s+"
        r"(?:had|got|received)\b[^.!?]{0,24}\bpoll(?:ing)?\s+card\b"
        r"|\bwhen\s+(?:will|does|is)\s+(?:my|our)\s+poll(?:ing)?\s+card\b"),
     ("The poll card is posted a few weeks before the vote, and you can vote without it. If it "
      "has not come, your council's elections team can confirm you are on the register and tell "
      "you where to go.",
      "Nothing here that can look at your post. The card is not needed at the station, so ring "
      "the council's elections line to check your registration and the polling place.")),
    ("polling", re.compile(
        r"\bwhere\s+(?:do|can|should|will)\s+i\s+(?:go\s+to\s+)?vote\b"
        r"|\bwhere(?:'s|s| is)?\s+(?:my|our)\s+polling\s+(?:station|place)\b"
        r"|\b(?:which|what)\s+polling\s+(?:station|place)\s+"
        r"(?:is\s+mine|do\s+i\s+(?:use|go\s+to))\b"
        r"|\b(?:which|what)\s+polling\s+district\s+(?:am|do)\s+i\b"
        r"|\b(?:which|what)(?:'s|s| is)?\s+(?:my|our)\s+polling\s+district\b"
        r"|\bhow\s+(?:do|can)\s+i\s+find\s+(?:out\s+)?(?:my|our)\s+polling\s+(?:station|place)\b"
        r"|\bhow\s+(?:do|can)\s+i\s+find\s+(?:out\s+)?where\s+(?:to|i)\s+vote\b"),
     ("I can't look up your polling station from here. Your council's elections page takes a "
      "postcode and gives the station and its hours, and the poll card through your door names "
      "it too.",
      "Nothing here that knows your address. The council's \"where to vote\" page takes a "
      "postcode; the poll card they send also has the station on it.")),
    ("council area", re.compile(
        r"\b(?:which|what)\s+(?:council|local\s+authority)\s+(?:am|do)\s+i\b"
        r"|\b(?:which|what)\s+council\s+area\s+(?:am|do)\s+i\b"
        r"|\bwhich\s+local\s+authority\s+(?:covers|is)\s+(?:my|our|this)\b"
        r"|\b(?:what(?:'s|s| is)?|who(?:'s|s| is))\s+(?:my|our)\s+(?:local\s+)?"
        r"(?:council|local\s+authority)\s*$"
        r"|\bwhich\s+(?:council|local\s+authority)\s+(?:is|does)\s+(?:mine|my|our)\b"),
     ("I can't tell which council area you are in from here. Gov.uk's \"find your local "
      "council\" takes a postcode and gives the council with its phone number and website.",
      "Nothing here that knows where you live. On gov.uk, \"find your local council\" takes a "
      "postcode and names it.")),
    ("water", re.compile(
        r"\bwho\s+(?:is|provides|supplies|are)\s+(?:my|our)\s+(?:water|water\s+company|water\s+supplier)\b"
        r"|\bwho(?:'s|s)\s+(?:my|our)\s+water\b"
        r"|\b(?:which|what)\s+water\s+(?:company|supplier|provider)\s+(?:am|do)\s+i\b"
        r"|\bwhat(?:'s|s| is)?\s+(?:my|our)\s+water\s+(?:supplier|company|provider)\b"
        r"|\b(?:which|what)\s+water\s+(?:company|supplier|provider)\s+"
        r"(?:supplies|serves|covers)\s+(?:my|our)\b"
        # "how do i find out my water supplier" names no who and no which, so nothing read it.
        r"|\bhow\s+(?:do|can)\s+i\s+(?:find|check|know)\s+(?:out\s+)?(?:my|our)\s+"
        r"water\s+(?:supplier|company|provider)\b"),
     ("I can't see your postcode, so I can't name your water company. A recent water bill names "
      "it at the top; if you have just moved in, the letting agent or the previous owner will "
      "know.",
      "Nothing here to look at, sorry. The water bill, or any letter from them, has the company "
      "name on it.")),
    ("energy", re.compile(
        r"\bwho\s+(?:is|provides|supplies|are)\s+(?:my|our)\s+(?:energy|gas|electric|electricity)"
        r"(?:\s+(?:supplier|company|provider))?\b"
        r"|\bwho(?:'s|s)\s+(?:my|our)\s+(?:energy|gas|electric|electricity)\b"
        r"|\b(?:which|what)\s+(?:energy|gas|electricity)\s+(?:supplier|company|provider)\s+"
        r"(?:am|do)\s+i\b"
        r"|\bwhat(?:'s|s| is)?\s+(?:my|our)\s+(?:energy|gas|electricity)\s+"
        r"(?:supplier|company|provider)\b"
        r"|\b(?:which|what)\s+(?:energy|gas|electricity)\s+(?:company|supplier|provider)\s+"
        r"(?:supplies|serves|covers)\s+(?:my|our)\b"
        # The finding form, as with water: "how do i find out my energy supplier".
        r"|\bhow\s+(?:do|can)\s+i\s+(?:find|check|know)\s+(?:out\s+)?(?:my|our)\s+"
        r"(?:energy|gas|electricity)\s+(?:supplier|company|provider)\b"),
     ("I can't see your meter or your bills. A recent bill names the supplier, and so does the "
      "supplier's app; if you have just moved in, the letting agent or the previous occupier's "
      "final bill will say.",
      "Nothing of yours to look at here, so I can't tell who supplies you. The name is on a "
      "recent bill or in the supplier's app.")),
    ("flood risk", re.compile(
        r"\b(?:is|are|does|do|am|will|would)\b[^.!?]{0,50}\bflood(?:ing|s)?\b"
        r"[^.!?]{0,30}\b(?:my|our)\s+(?:house|home|area|street|road|property|postcode|"
        r"address|neighbourhood|neighborhood|garden|flat|village|town|business)\b"
        r"|\b(?:my|our)\s+(?:house|home|area|street|road|property|postcode|address|"
        r"neighbourhood|neighborhood)\b[^.!?]{0,40}\bflood(?:ing|s)?\b"
        r"|\bam\s+i\s+in\s+a\s+flood\s+(?:zone|area|risk)\b"),
     ("I can't see your address, so I can't read the flood map. Gov.uk's flood-risk page takes "
      "a postcode and shows river, sea and surface-water risk for the area, with any warnings "
      "for it.",
      "Nothing here that knows where you live. Put the postcode into the flood-risk check on "
      "gov.uk and it gives the risk for the area; the Environment Agency's warnings show what "
      "is current.")),
    ("broadband", re.compile(
        r"\b(?:what|which)\s+broadband\s+(?:can\s+i\s+get|is\s+available|"
        r"(?:packages?|providers?)\s+(?:are\s+)?available)\b"
        r"|\bbroadband\s+(?:at|on|in)\s+(?:my|our)\s+"
        r"(?:address|street|road|area|house|home|flat)\b"
        r"|\bhow\s+fast\s+is\s+(?:the\s+)?broadband\s+(?:at|on|in)\s+(?:my|our)\b"
        r"|\b(?:is|are)\s+(?:there\s+)?(?:fast\s+|fibre\s+|full\s+fibre\s+)?broadband\s+"
        r"(?:at|on|in)\s+(?:my|our)\b"),
     ("I can't see your line from here. Ofcom's broadband checker takes a postcode and shows "
      "the speeds and providers available at that address.",
      "Nothing here that knows your address. Ofcom's coverage checker takes a postcode and "
      "lists the broadband there, and the provider's own line checker confirms it.")),
    ("mobile coverage", re.compile(
        r"\b(?:which|what)\s+(?:mobile\s+)?network\s+(?:has|gives|gets)\s+(?:the\s+)?"
        r"(?:best|good|strongest|better)\s+(?:signal|coverage|reception)\b"
        r"|\b(?:which|what)\s+(?:mobile\s+)?network\s+(?:is|works)\s+best\s+"
        r"(?:where\s+i\s+live|(?:at|in|around|near)\s+(?:my|our|here))\b"
        r"|\b(?:what|which)\s+(?:mobile\s+)?(?:signal|coverage|reception)\s+"
        r"(?:do|can|will)\s+i\s+get\s+(?:at|in|on|around|near)\s+(?:my|our)\b"
        r"|\bcan\s+i\s+get\s+(?:a\s+)?(?:mobile\s+)?(?:signal|coverage|reception)\s+"
        r"(?:at|in|on|around|near)\s+(?:my|our)\b"
        r"|\b(?:is|are)\s+there\s+(?:good\s+|any\s+|decent\s+|strong\s+)?(?:mobile\s+)?"
        r"(?:signal|coverage|reception)\s+(?:at|in|on|around|near)\s+(?:my|our)\b"
        r"|\bhow\s+(?:good|strong)\s+is\s+(?:the\s+)?(?:mobile\s+)?"
        r"(?:signal|coverage|reception)\s+(?:at|in|on|around|near)\s+(?:my|our)\b"),
     ("I can't see your street, so I can't say which network is best there. Ofcom's mobile "
      "coverage checker takes a postcode and compares the networks indoors and out; each "
      "network's own map does the same for its signal.",
      "Nothing here that knows your address. Ofcom's coverage checker takes a postcode and "
      "shows the signal each network gives indoors and out, and the networks' own maps do the "
      "same.")),
    ("bin day", re.compile(
        r"\b(?:when|what\s+day|which\s+day)\s+(?:is|are|will|do|does)\s+(?:my|our)\s+"
        r"(?:bins?|rubbish|recycling|waste|refuse|garden\s+waste)\b[^.!?]{0,24}"
        r"\b(?:collected|collection|emptied|out|due|picked\s+up)\b"
        r"|\b(?:when|what\s+day|which\s+day)\s+(?:do|does|will)\s+"
        r"(?:they|the\s+council|my\s+council)\s+(?:collect|empty|pick\s+up)\s+"
        r"(?:my|our)\s+(?:bins?|rubbish|recycling|waste|refuse)\b"
        r"|\b(?:what|which)\s+(?:is|are)\s+(?:my|our)\s+"
        r"(?:bin|rubbish|recycling|waste|refuse)\s+(?:collection\s+)?(?:day|days|schedule)\b"
        r"|\bwhen(?:'s|s| is)\s+(?:my|our)\s+bin\s+day\b"
        r"|\b(?:what|which)\s+day\s+(?:are|do)\s+(?:my|our)\s+bins?\s+"
        r"(?:go\s+out|get\s+collected|get\s+emptied|get\s+picked\s+up)\b"
        r"|\b(?:what|which)\s+bin\s+day\s+is\s+it\b"
        # The how-to form people type: "how do i find my bin day". The card above reads the
        # day words but not the finding, so the line reached the search hedge.
        r"|\bhow\s+(?:do|can)\s+i\s+(?:find|check|see)\s+(?:out\s+)?(?:my|our)\s+"
        r"(?:bin|rubbish|recycling|waste)\s+(?:day|collection\s+day|schedule)\b"),
     ("I can't see your street, so I can't give your bin day. Your council's bin page takes a "
      "postcode and shows the day for your address, with any change for a bank holiday.",
      "Nothing here that knows your address. The council's bin-day page takes a postcode and "
      "gives the day and the bank-holiday changes; the bin itself often has a sticker with it "
      "too.")),
    ("epc", re.compile(
        r"\bwhat(?:'s|s| is)?\s+(?:my|our)\s+(?:epc|energy\s+performance\s+certificate)"
        r"(?:\s+(?:rating|score|band))?\b"
        r"|\bwhat\s+epc\s+(?:rating\s+|band\s+)?(?:does|has|is)\s+(?:my|our)\s+"
        r"(?:house|home|flat|property|building)\b"
        r"|\b(?:which|what)\s+epc\s+(?:rating|band)\s+(?:is|does)\s+(?:my|our)\b"
        r"|\b(?:what|which)\s+is\s+the\s+epc\s+(?:rating|band)\s+of\s+(?:my|our)\s+"
        r"(?:house|home|flat|property|building)\b"),
     ("I can't see your address, so I can't read your EPC. Gov.uk's energy performance "
      "certificate register takes a postcode and address and shows the rating and the "
      "certificate; the seller or letting agent should have it too.",
      "Nothing here that knows your address. The EPC register on gov.uk takes the postcode and "
      "address and gives the rating, and a copy is usually in the seller's or agent's pack.")),
    ("listed", re.compile(
        r"\bis\s+(?:my|our)\s+(?:house|home|building|flat|property|cottage|pub|shop|church)"
        r"\b[^.!?]{0,30}\b(?:a\s+)?listed\s+building\b"
        r"|\bis\s+(?:my|our)\s+(?:house|home|building|flat|property|cottage|pub|shop|church)"
        r"\b[^.!?]{0,30}\bgrade\s+(?:i|ii|2)\s+listed\b"
        r"|\bam\s+i\s+in\s+a\s+conservation\s+area\b"
        r"|\bis\s+(?:my|our)\s+(?:house|home|building|flat|property|street|road|area)"
        r"\b[^.!?]{0,30}\bin\s+a\s+conservation\s+area\b"),
     ("I can't see your address, so I can't say whether it is listed. The national heritage "
      "list takes the address, and your council's conservation-area map shows whether the "
      "street is protected.",
      "Nothing here that knows your building. The national heritage list is searched by address, "
      "and the council's conservation map covers the streets around it.")),
    ("roads", re.compile(
        r"\b(?:is|are|will|when\s+(?:is|are|will))\s+(?:my|our)\s+(?:road|street)\b"
        r"[^.!?]{0,30}\b(?:resurfac\w*|roadworks|closed|closure|dug\s+up|tarmac\w*)\b"
        r"|\b(?:my|our|the)\s+(?:road|street)\b[^.!?]{0,30}"
        r"\b(?:resurfac\w*|roadworks|dug\s+up|tarmac\w*)\b"
        r"|\bwhen\s+(?:is|are|will)\s+(?:my|our)\s+(?:road|street)\s+(?:being\s+)?"
        r"(?:resurfaced|closed|done|fixed)\b"
        # Told, not asked: "theres roadworks at the end of our street", "resurfacing on our
        # street this week". The works word comes before the road, which the patterns above
        # only had the other way round, so the line reached the stock nod.
        r"|\b(?:roadworks|road\s+works|resurfac\w*|dug\s+up|tarmac\w*|closed\s+off)\b"
        r"[^.!?]{0,40}\b(?:my|our|the)\s+(?:road|street)\b"
        # "my road is closed" was read as a small thing done in a day ("Good to hear. What was
        # the best bit?"), which is the wrong way round for a complaint about a closed road.
        r"|(?:^|[.!,;:]|\b(?:and|but|so|now)\b)\s*(?:my|our|the)\s+(?:road|street)\s+"
        r"(?:is|was|will\s+be)\s+(?:closed|shut)\b"),
     ("I can't see your street from here. Your council's roadworks map takes a postcode, and "
      "one.network shows planned resurfacing and closures by road name.",
      "Nothing here on your road's schedule. The council's roadworks or highways page, searched "
      "by postcode or street, says what is planned, and one.network shows the current works.")),
    ("clean air zone", re.compile(
        r"\b(?:is|are)\s+(?:my|our)\s+(?:car|van|vehicle|truck|lorry|motorbike|bike)\b"
        r"[^.!?]{0,40}\b(?:ulez|lez|caz|clean\s+air\s+zone|low\s+emission\s+zone)\b"
        r"|\b(?:is|are)\s+(?:my|our)\s+(?:area|street|road|postcode|address|house|home|flat)\s+"
        r"(?:(?:in|inside)\s+)?(?:a|an|the)\s*"
        r"(?:ulez|lez|caz|clean\s+air\s+zone|low\s+emission\s+zone)\b"
        r"|\b(?:do|will)\s+i\s+(?:have\s+to\s+|need\s+to\s+)?(?:pay|get\s+charged|"
        r"be\s+charged)\s+(?:for\s+)?(?:the\s+)?"
        r"(?:ulez|lez|caz|clean\s+air\s+zone|low\s+emission\s+zone)\b"
        r"|\b(?:am|are)\s+(?:i|we)\s+(?:in|inside)\s+(?:a|the)\s+"
        r"(?:ulez|lez|caz|clean\s+air\s+zone|low\s+emission\s+zone)\b"
        r"|\b(?:which|what)\s+(?:ulez|lez|caz|clean\s+air\s+zone|low\s+emission\s+zone)\s+"
        r"(?:am\s+i|is\s+my|are\s+we|do\s+i)\b"),
     ("I can't see your car or your address, so I can't say whether a charge applies. Gov.uk's "
      "clean air zone checker takes the number plate and postcode and says whether a charge is "
      "due; London's ULEZ checker does the same for London.",
      "Nothing here that knows your vehicle or your street. On gov.uk, the clean air zone "
      "checker takes the plate and postcode and says whether a charge is due; TfL's ULEZ "
      "checker covers London.")),
    ("council tax band", re.compile(
        r"\bwhat(?:'s|s| is)?\s+(?:my|our)\s+council\s+tax\s+band\b"
        r"|\bwhich\s+council\s+tax\s+band\s+(?:am\s+i|is\s+my|are\s+we|do\s+i)\b"
        r"|\bwhat\s+band\s+(?:is|are)\s+(?:my|our)\s+council\s+tax\b"
        r"|\bhow\s+(?:do|can)\s+i\s+(?:find\s+out|check|look\s+up)\s+(?:my|our)\s+"
        r"council\s+tax\s+band\b"),
     ("I can't look up your band from here. The Valuation Office Agency's checker takes your "
      "postcode and address and gives the band; your council's bill shows it too.",
      "Nothing here that knows your address. On gov.uk, the council tax band checker takes the "
      "postcode and address, and the band is printed on the bill.")),
    ("school catchment", re.compile(
        r"\b(?:which|what)\s+school\s+(?:am\s+i|is\s+my\s+(?:child|son|daughter|kid)|will\s+my\s+"
        r"(?:child|son|daughter|kid))\b[^.!?]*\bcatchment\b"
        r"|\b(?:which|what)\s+school\s+catchment\b"
        r"|\b(?:my|our)\s+catchment\s+school\b"
        r"|\bwhat\s+catchment\s+(?:school|area)\b"
        r"|\b(?:which|what)\s+catchment\s+area\b"),
     ("I can't see your postcode, so I can't say which catchment you are in. Your council's "
      "school admissions page takes it and shows the catchment school and the last distance "
      "that got a place.",
      "Nothing here that knows your address. The council's admissions site has a postcode "
      "checker with each school's catchment and the last distance offered.")),
    ("school term dates", re.compile(
        r"\b(?:when|what\s+date)\s+(?:does|do|is|are|will)\s+(?:my|our)\s+"
        r"(?:child|son|daughter|kid|children|kids)(?:'s|s')?\s+school\s+"
        r"(?:break\s+up|finish|go\s+back|return|close|be\s+off)\b"
        r"|\b(?:when|what\s+date)\s+(?:does|do|is|are|will)\s+(?:my|our)\s+school\s+"
        r"(?:break\s+up|finish|go\s+back|return|close|be\s+off)\b"
        r"|\b(?:when|what)\s+(?:are|is)\s+(?:my|our)\s+(?:school\s+)?"
        r"(?:term\s+dates|half[\s-]?term|summer\s+holidays|christmas\s+holidays|"
        r"easter\s+holidays|school\s+holidays)\b"
        r"|\b(?:when|what)\s+(?:are|is)\s+the\s+(?:school\s+)?"
        r"(?:term\s+dates|school\s+holidays)\s+for\s+(?:my|our)\b"
        r"|\b(?:when|what\s+date)\s+(?:does|do|is|are|will)\s+(?:my|our)\s+"
        r"(?:child|son|daughter|kid|children|kids)\s+(?:school\s+)?"
        r"(?:break\s+up|finish|go\s+back|return|be\s+off)\s+(?:school\s+)?"
        r"(?:for|from|to)\s+(?:school|summer|christmas|easter|half[\s-]?term)\b"
        r"|\b(?:where|how)\s+(?:can|do)\s+i\s+find\s+(?:my|our)\s+"
        r"(?:\w+(?:'s|s')?\s+){0,3}(?:term\s+dates|school\s+holidays)\b"),
     ("I can't see your school's calendar. Your council's school-term-dates page covers its "
      "schools, and the school's own site or newsletter has the inset days, which differ from "
      "school to school.",
      "Nothing here with your school's calendar. The council lists term dates for its schools, "
      "and the school office has the inset days that are not in the council list.")),
)


# A how-to about the same noun asks for action, not identity: "how do i switch my energy
# supplier" and "how do i change my water company" want the switching steps, and the line about
# a bill names the wrong thing. "where do i vote" and "who is my mp" are identity asks and keep
# the lookup.
POSTCODE_NOT = re.compile(
    r"\b(?:help\s+me|advice|any\s+tips|switch(?:ing)?|chang(?:e|ing)|compar(?:e|ing)|"
    r"save\s+on|cut\s+(?:down|back|costs|bills|use|my|our|the|your)|reduce)\b")


def a_postcode_lookup(clean):
    """The honest line for a fact that only the person's postcode can answer, or None."""
    if POSTCODE_NOT.search(clean):
        return None
    for _name, pattern, options in POSTCODE_LOOKUPS:
        if pattern.search(clean):
            return options
    return None
