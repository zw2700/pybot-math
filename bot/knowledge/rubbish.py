"""Getting rid of things: the bin, the tip, the shop, and the council collection.

The answers lane owns this domain. Every house holds things that cannot simply go out with the
rubbish - a battery, a bulb, half a tin of medicine, a mattress, a fridge - and the question is
always the same shape: this thing, where does it go? Nobody else in the tree answers it: the one
entry that did, `home.paint-tins`, exists because liquid paint is legally not household waste, and
it is the pattern these entries follow.

So the fact here is the *route*, one per item, keyed by the item and one of the words that asks
what to do with it ("get rid of", "throw away", "in the bin", "recycle", "the tip"). The route
words are shared by every entry on purpose: they say what is being asked, and the item says what
about, so one row answers "can i put batteries in the bin", "how do i get rid of old batteries"
and "where do i recycle batteries" without three keys. Each entry carries an `avoid` list for the
neighbouring question about the same item - a mattress to *buy* or *clean*, a fridge that is not
*cold*, a phone *contract* - because those are other entries' lines and this one is only for the
thing on its way out.

What to do with an item nobody here knows is its own entry: rather than a shrug, it says the
three routes a thing usually takes and asks which item it is.
"""
import re

from .dishes import cook_ask
from .lookup import A_HOURS_ASK, entry

# The topics this domain answers (bot/understanding/topics.py). Both are ids other domains
# already declare, so the union answers.py publishes does not change: this file answers the lines
# those domains pass on and takes no subject over from them. Rubbish is read as `technology` when
# the line names a battery or a bulb and as `home-and-diy` when it asks how to get rid of
# something ("how do i get rid of an old mattress"), and it is the same answer either way.
ANSWERS = ("home-and-diy", "technology")

# The words that say "I want this gone". They name the ask, never the thing, so the same tuple
# belongs on every item below and the item's own word decides which route is meant.
# Passing a thing on is the commonest ask of all and it is the same shape as the bin: the
# item, and a word that says it is leaving the house. "how do i donate clothes", "how do i
# donate a bike" and "where can i donate toys" were all a shrug or a search hedge, because the
# ask words only ever said throw away. "charity" is here rather than in one row because it is
# an ask and never an item: a line with no thing in it ("how do i raise money for charity")
# still matches nothing below.
RID = ("get rid", "rid of", "dispose", "disposal", "throw away", "throw out", "throwing away",
       "donate", "donated", "donating", "donation", "donations", "give away", "giving away",
       "gave away", "charity", "charity shop", "charity shops", "free ad", "free ads",
       "freecycle", "pass on",
       "where do i take", "where can i take", "where do i put", "where can i put",
       "drop off", "get shot of", "throw", "throwing", "toss",
       "chuck", "chuck out", "chucking out", "bin", "bins", "the tip", "to the tip", "tip it",
       "recycling centre", "recycle", "recycling", "kerbside", "waste", "dump", "scrap",
       "skip", "get shot", "household waste", "council collection", "collection",
       "do with")

# A line that asks which bin a thing goes in names the bin and asks where, and nothing else.
BIN_WORDS = ("bin", "bins", "the tip", "to the tip", "recycling", "recycle", "kerbside",
             "household waste")
BIN_ASK = ("put", "throw", "chuck", "dump", "dispose", "get rid", "go in", "goes in", "go",
           "goes", "belong", "belongs", "which", "where")

# A line that says "without" a medicine is asking how to cure something, not where the medicine
# goes. "how do i get rid of a toothache without tablets" was the electricals card, because a tablet
# is also a computer, and "get rid of hay fever without tablets" and "get rid of heartburn without
# tablets" were the same card. The phrase is what tells the two apart, never the bare word: a device
# that comes without a cable is still a device on its way out.
CURING_ASIDE = ("without pills", "without tablets", "without medicine", "without medicines",
                "without medication", "without antibiotics", "without painkillers",
                "without any pills", "without any tablets", "without any medicine",
                "without drugs", "without meds")

# A medicine is the one item here whose words are also what a person reaches for when they want a
# symptom gone, so "how do i get rid of a headache without pills" was answered "Take them back to a
# pharmacy" - and so were a cough without medicine, heartburn without pills and a blocked nose
# without medicine. A disposal question says the thing being got rid of is the medicine itself: it
# is old or unused or out of date, or it goes in the bin, to the tip or back to the chemist. The row
# therefore asks for one of those, which a curing question never says.
MEDICINE_DISPOSAL = (
    "old", "unused", "unwanted", "leftover", "left over", "expired", "out of date", "past it",
    "no longer", "stopped taking", "dont need", "don't need", "not taking", "off them",
    "bin", "bins", "tip", "recycling", "recycle", "dispose", "throw", "throwing", "chuck",
    "pharmacy", "chemist", "where do i", "where can i", "where should i", "what do i do with",
    "get rid of the tablets", "get rid of the pills", "get rid of the medicine",
    "get rid of the medicines", "get rid of my tablets", "get rid of my pills",
    "get rid of my medicine", "get rid of my medicines", "get rid of these tablets",
    "get rid of these pills", "get rid of all the tablets", "get rid of all these pills",
    # The bare phrase too: "how do i get rid of pills" is a person holding a packet, and it
    # was losing main's pharmacy card because only the "the"/"my"/"these" forms were listed.
    # A curing line never says "get rid of pills" - it says "without pills" - so this does
    # not reopen the hole CURING_ASIDE closes.
    "get rid of pills", "get rid of tablets", "get rid of medicine", "get rid of medicines",
    "rid of old pills", "rid of leftover tablets",
)

# A verdict on a buy is not a thing on its way out. "would a standing desk be a waste of money"
# was the bulky-furniture row on the bare word "waste", and a person asking whether to spend is
# answered by the worth-it card, not with a trip to the tip. The bare word is what RID reads as
# rubbish, so the phrases that only ever mean a judgement about money stand every item row down.
NOT_RUBBISH = ("waste of money", "waste of time", "wasted money", "wasting money",
               "worth the money", "worth it", "any point in", "money well spent",
               "a good buy", "a bad buy")

# One fact per item: (id, the item's own words, the route, what the entry must not take).
ITEMS = (
    # A takeaway box is the one cardboard question with a catch in it, and on main `85d8420` all
    # three ways of asking it were answered "Cold pizza is fine if it went into the fridge within
    # a couple of hours of arriving" - the leftover-pizza row keys on the bare word "box".
    ("pizza-box",
     ("pizza box", "pizza boxes", "greasy cardboard", "oily cardboard", "dirty cardboard",
      "takeaway box", "takeaway boxes", "chip box", "food box", "food boxes", "cardboard box",
      "cardboard boxes", "greasy box"),
     "Tear off the clean lid and put that in the recycling; the greasy base goes in the general "
     "waste, or in the food waste if your council takes that. Cheese and oil soaked into card "
     "spoil the load at the sorting plant, so a soaked box is the one thing worth separating.",
     ("leftover pizza", "cold pizza", "reheat", "reheating", "eat", "freeze", "freezing",
      "how long", "order", "delivery", "delivered", "arrived", "takeaway pizza", "slice")),
    # A move leaves a mountain of cardboard, and a plain box is the pizza row's word: on main
    # `2a03352e` "how do i get rid of boxes" was answered "Cold pizza is fine..." at the pizza
    # row's own wording, and "where do i take cardboard boxes" with the greasy-lid card. The
    # pizza row keeps the messy box (it is in this row's avoid); everything dry and clean goes
    # out flat with the kerbside card.
    ("cardboard-boxes",
     ("cardboard", "cardboard box", "cardboard boxes", "moving boxes", "moving box",
      "packing boxes", "delivery boxes", "delivery box", "packaging", "boxes", "box",
      "cartons", "carton", "empty boxes", "pile of boxes"),
     "Flatten them and keep them dry: clean cardboard goes out with the kerbside recycling, cut "
     "down to the size your council takes, and tape, polystyrene and any food grease keep a box "
     "out of it. More than the bin will take is a bulky collection or a trip to the recycling "
     "centre, and removal boxes in good nick go fast on a local free-and-wanted group.",
     ("pizza", "greasy", "oily", "dirty", "takeaway", "chip box", "food box", "leftover",
      "gift", "present", "cereal", "hamper", "batteries", "cat", "litter", "pack", "packing",
      "packed", "label", "tape", "flat pack", "flatpack", "shadow", "cardboard cutout"),
     2),
    # Ordinary batteries are `home.batteries-in-the-bin`, which was merged before this domain and
    # answers every "can i put batteries in the bin" line, so this is only the car battery: the
    # one battery the household bin question is not about, and the one worth money.
    ("car-battery",
     ("car battery", "car batteries", "van battery", "leisure battery", "motorcycle battery"),
     "A garage will take the old one when it fits a new one, and a scrap dealer or a metal "
     "merchant buys it by weight, so it is worth a few pounds rather than a trip to the tip - "
     "which takes them too. Never put it in the bin or leave it in the garage for years: it holds "
     "acid and lead.",
     ("flat", "flat battery", "wont start", "won't start", "jump", "jump start", "charging",
      "charge", "charger", "dies", "dying", "last", "lasts", "life", "how long", "replace",
      "replacement", "test", "cold weather", "warning light")),
    ("medicines",
     ("medicine", "medicines", "tablets", "pills", "capsules", "old medicine", "unused medicine",
      "medical waste", "syringe", "inhaler", "antibiotics", "painkillers", "antidepressants",
      "old tablets", "leftover tablets", "unused tablets", "expired tablets", "old pills",
      "leftover medicine", "insulin pen", "epipen"),
     "Take them back to a pharmacy: every pharmacy takes unwanted medicines for safe disposal, and "
     "you do not need to explain. Don't flush them and don't bin them - they reach the water "
     "supply, and a child or a pet can find them. Leave them in their packet with the label on, "
     "and put a used inhaler in with them rather than in the bin.",
     # A plan to stop, skip or change a dose is not a bag of unwanted tablets: "im going to skip
     # my tablets tonight" was told to take them back to a pharmacy for safe disposal. The row is
     # for medicines nobody wants any more, so the words that say the person still takes them
     # stand it down.
     ("im going to", "going to", "gonna", "plan to", "skip", "skips", "skipping", "stopped",
      "stopping", "stop taking", "come off", "coming off", "cut down", "cutting down", "halve",
      "halving", "half", "reduce", "reducing", "increase", "increasing", "double", "doubling",
      "extra dose", "change my dose", "my dose", "taper", "wean", "instead of",
      "can i take", "should i take", "safe to take", "ok to take", "take one", "take two",
      "take them", "take it", "take with", "take for", "still taking", "dose", "dosage",
      "side effect", "side effects", "how many", "overdose", "missed", "forgot", "forget",
      # "how do i get rid of a headache without pills" is a line about the headache, and "get rid
      # of" plus "pills" won it this row: the person was told to take their medicines back to a
      # pharmacy. A named pain or illness is the subject, so the disposal row stands down.
      "headache", "headaches", "head ache", "migraine", "migraines", "ache", "aches", "aching",
      "pain", "pains", "painful", "sore", "toothache", "tooth ache", "stomach ache", "earache",
      "back pain", "period pain", "cramp", "cramps", "hurt", "hurts", "ill", "unwell",
      "symptom", "symptoms", "cure", "relief", "relieve", "ease", "calm down",
      "cold", "flu", "cough", "colds", "infection", "sick", "sickness", "fever", "temperature",
      "hangover", "allergy", "allergies", "hayfever", "hay fever", "insect bite", "sting")),
    ("mattress",
     ("mattress", "mattresses", "old bed", "bed frame", "divan", "headboard"),
     "Book a bulky waste collection with your council - most charge twenty to forty pounds and "
     "collect from the doorstep - or take it to the recycling centre, where it is stripped for its "
     "springs. Charity shops rarely take one for hygiene reasons, so a free-ad site is the other "
     "realistic route if it is clean and you say collection only.",
     ("cost", "costs", "price", "prices", "buy", "buying", "best", "which", "decent", "clean",
      "cleaning", "stain", "stains", "wash", "smell", "smells", "size", "firm", "soft")),
    ("fridge",
     ("fridge", "freezer", "fridge freezer", "chest freezer"),
     "A fridge or freezer holds refrigerant gas that has to be taken out by someone equipped for "
     "it, so it can never go out with the rubbish. The shop selling you the new one has to take the "
     "old one away on a like-for-like basis, often free or for a small fee, and the recycling "
     "centre takes it. Take the doors off before it leaves the kitchen if children or pets will be "
     "near it.",
     ("cold", "not cold", "freezing", "repair", "fix", "fixing", "smells", "smell",
      "noisy", "noise", "frost", "temperature", "ice", "not working", "wont", "won't", "leaking",
      "installing", "install", "second hand",
      # A fridge the person is putting food into is not a fridge on its way to the tip: "where do
      # i put cheese in the fridge" was answered with the refrigerant gas. A named food is the
      # keeping question, and the keeping table has the answer.
      # Only foods the keeping table answers are named here. "Milk" and "salad" were in this
      # list and both fell past the keeping table to a white sauce and a chicken salad, which is
      # its own kind of wrong, so they are left to the fridge row's wrong answer until the
      # keeping side has a card of its own for them.
      "cheese", "butter", "yoghurt", "yogurt", "leftovers", "bacon", "ham",
      "eggs", "raw meat")),
    # White goods hold no refrigerant, so they are not the fridge row: the shop takes the old one
    # when it delivers, the tip has a skip for them, and a scrap dealer pays by weight for metal.
    ("white-goods",
     ("washing machine", "washer", "tumble dryer", "dryer", "dishwasher", "oven", "cooker",
      "microwave", "hob", "fridge unit"),
     "The shop delivering a new one has to take the old one away on a like-for-like basis, and "
     "some charge a small fee for it, so ask when you buy. Otherwise the tip has a skip for white "
     "goods, or a scrap dealer collects for the metal - and a machine that still works will go on "
     "a free-ad site in a day. Unplug it, drain the water out of the filter, and tape the door "
     "shut before it leaves the kitchen.",
     ("clean", "cleaning", "descale", "limescale", "smell", "smells", "smelly", "musty", "filter",
      # "how do i get rid of mould in my washing machine" is the mould, not the machine on its
      # way out to the tip: the mould words stand this row down
      "mould", "mold", "mouldy", "moldy", "mildew", "black mould", "black mold",
      "not draining", "wont drain", "won't drain", "not spinning", "wont spin", "won't spin",
      "repair", "fix", "faulty", "not working", "broken", "error", "install", "installing",
      "plumb", "plumbing", "leaking", "leak", "noisy", "banging",
      # the rest of the sounds a machine makes: a machine that grinds, squeals or rattles is a
      # fault question, and this row was answering "my washing machine is scraping" with the
      # like-for-like collection at the tip
      "grind", "grinds", "grinding", "scrap", "scrapes", "scraping", "rattle", "rattles",
      "rattling", "squeak", "squeaks", "squeaking", "squeal", "squeals", "squealing",
      "thump", "thumping", "knock", "knocking", "vibrate", "vibrating", "shaking",
      "how often", "which", "best",
      "buy", "buying", "bake", "baking", "roast", "cook", "cooking", "preheat", "temperature",
      "fan oven", "self clean"),
     2),
    ("bulbs",
     ("light bulb", "light bulbs", "bulb", "bulbs", "halogen", "fluorescent", "cfl", "led bulb",
      "led bulbs", "strip light", "tube light"),
     "Old-style filament and halogen bulbs are just glass and wire, so they go in the bin. The "
     "coiled low-energy ones hold a little mercury: take those to the tip or to a shop that sells "
     "them. If one breaks, air the room for fifteen minutes, don't vacuum, and wipe it up with a "
     "damp paper towel. LEDs are electronics, so they belong with the small appliances at the tip.",
     ("change", "changing", "replace", "replacement", "fitting", "watt", "watts", "bright",
      "brighter", "dimmable", "flicker", "flickering", "not working", "blown", "which", "best",
      "warm white", "energy")),
    ("electricals",
     ("tv", "television", "telly", "laptop", "computer", "pc", "monitor", "printer", "kettle",
      "toaster", "hoover", "vacuum cleaner", "phone", "mobile", "mobile phone", "old phone",
      "iphone", "tablet", "ipad", "charger", "cable", "electricals", "electronics", "appliance",
      "appliances", "game console", "xbox", "playstation"),
     "Anything with a plug, a battery or a cable is electrical waste and can't go in the bin. A "
     "shop that sells you a new one has to take the old one back, like for like, and the tip has a "
     "small-appliance skip. Wipe a phone or laptop and take the SIM and memory card out first; a "
     "charity shop or a repair cafe can make use of one that still works.",
     ("limescale", "scale", "descale", "furred", "virus", "viruses", "pop up", "popup", "malware",
      "spyware", "adware", "software", "app", "apps", "update", "browser", "email", "wifi",
      # a program is software, not the laptop it runs on: "how do i get rid of a program on my
      # laptop" was told a shop has to take the old one back. The thing being got rid of is the
      # program, so the uninstall answer owns the line - and "how do i get rid of an old laptop"
      # still names the machine, which is what this row is for.
      "program", "programs", "uninstall", "uninstalling", "uninstalled", "reinstall",
      "wi-fi", "speed", "slow", "taking ages", "taking so long", "taking long", "is taking",
      "takes ages", "takes forever", "took a", "took one", "took it", "took my",
      "swallow", "swallowed", "pill", "pills",
      # A complaint said beside the word "tablets" is a person asking what to do about the
      # complaint, not a computer on its way out: "i cant take tablets, how do i get rid of a
      # headache" was this card. CURING_ASIDE only catches the "without tablets" spelling, so the
      # words that name the trouble are named here too. No line that asks where an old device goes
      # says any of them.
      "headache", "headaches", "migraine", "migraines", "toothache", "earache", "sore throat",
      "stomach ache", "cramp", "cramps", "nausea", "rash", "itching", "pain", "pains", "aching",
      "hurts", "hurting", "fever",
      "medicine", "dose", "dies", "dying", "lunchtime", "battery life", "cushion", "cushions",
      # a tablet is also a pill: "how do i get rid of a headache without tablets" was answered
      # with the small-appliance skip, so the medicine words stand this card down
      "tablets", "painkillers", "paracetamol", "ibuprofen", "prescription", "headache",
      "migraine", "symptom", "symptoms", "without tablets", "without pills",
      "contract", "contracts", "bill", "bills", "tariff", "upgrade", "unlock", "network", "sim",
      "number", "account", "cracked", "screen", "not working", "repair", "fix", "warranty",
      "no signal", "slow", "storage", "battery life", "charge", "charging", "watch", "channel",
      "channels", "remote", "print", "printing", "cartridge", "boil", "boiling", "toast",
      "vacuum", "hoovering",
      # a recycle bin on a desktop is software, not a machine on its way out: "the recycle bin is
      # full on my laptop" was told a shop has to take the old one back
      "recycle bin", "recycling bin", "trash can", "trash", "empty the trash", "deleted",
      "delete", "folder", "folders", "files", "desktop",
      # dust on the telly is a question about the room, not about where the telly goes at the
      # end of its life: "how do i get rid of dust settling on my tv" was the small-appliance
      # skip, because "get rid of" and "tv" are both this row's words and nothing in the line
      # says the machine is finished. A person asking where an old one goes says "old",
      # "broken" or "not working", and this row reads a thing being cleaned or landed on
      # instead.
      "dust", "dusty", "dusted", "cobweb", "cobwebs", "settling", "smear", "smears",
      "smudges", "fingerprints", "polish", "polishing", "wipe", "wiping", "cleaning",
      "clean the")),
    ("clothes",
     ("clothes", "clothing", "old clothes", "shoes", "trainers", "coats", "jumpers", "textiles",
      "rags", "bedding", "duvet", "pillows", "towels",
      # the list stopped at jumpers and a person's old socks went to a card about tiredness:
      # "what can i do with worn out socks" and "what do i do with old underwear" are the same
      # ask as the shoe one, and the textile bank takes them all
      "socks", "sock", "pants", "underwear", "knickers", "bras", "gloves", "scarves", "hats",
      "sheets", "curtains", "fabric", "linen", "blankets", "slippers", "boots", "sandals"),
     "Charity shops, the clothes banks in car parks and the textile skip at the tip take anything "
     "wearable. Worn-out fabric still earns its place in a textile bank, where it becomes rags or "
     "stuffing, so a bag of split trousers is not waste. Wash it first, put shoes in pairs, and a "
     "duvet or pillow that is past it goes to the textile bank rather than the bin.",
     ("dog", "dogs", "cat", "cats", "pet", "pets", "died", "dies", "passed away", "gone",
      "kid", "kids", "child", "children", "baby", "hospital", "his", "her bed",
      "wash", "washing", "shrink", "shrank", "stain", "stains", "iron", "ironing", "fit", "size",
      # "wear" on its own is the word in "clothes i dont wear", which is the commonest way to
      # ask this row's question, and it stood the row down on five phrasings of it ("how do i
      # get rid of clothes i dont wear", "what to do with clothes i dont wear", "clothes i never
      # wear"). The wearing words are the phrases instead, so a line about putting clothes on
      # still keeps its own card.
      # "wearing" cannot be listed here: an avoid word is matched loosely, so its stem "wear"
      # is the word in "clothes i dont wear" and it took the row down again. The phrases below
      # are the ones that mean putting clothes on.
      # "worn out" cannot be here either: a worn-out shoe is this row's own subject - the reply
      # says worn-out fabric goes to a textile bank - and two readers found "what do i do with
      # worn out shoes" going to a card about being tired. "wear it", "wear them" and "to wear"
      # are the phrases that mean putting clothes on, which is the other question.
      "wear it", "wear them", "to wear",
      "smell", "smells", "dry", "drying", "hole", "holes", "repair", "refashion",
      "style", "outfit", "what to wear",
      # the garments are what they are made of, not what to do with them: static and moths both
      # reached this row ("how do i get rid of static in clothes", "how do i get rid of clothes
      # moths") and each has an answer of its own
      "static", "static electricity", "clinging", "cling", "moth", "moths", "mothball",
      "mothballs", "lint", "bobbles", "bobbling", "pilling", "pills",
      # "get rid of" is the disposal verb and the stain verb both: "how do i get rid of chewing
      # gum from clothes" was answered with the clothes bank, so the things people want off a
      # garment rather than out of the house stand this row down
      "chewing gum", "gum", "oil", "grease", "paint", "ink", "blood", "wine", "coffee", "tea",
      "chocolate", "mud", "grass", "marker", "pen", "sick", "vomit", "wee", "urine",
      "out of my", "off my", "off the", "out of the",
      # A flower bed is a bed: "how do i get rid of weeds in my flower bed" was sent to the
      # clothes bank, because "bed" is read as "bedding". Anything growing stands this row down.
      "flower bed", "flower beds", "flowerbed", "garden", "gardens", "lawn", "lawns", "border",
      "borders", "allotment", "allotments", "weed", "weeds", "weeding", "plant", "plants",
      "shrub", "shrubs", "rose", "roses", "tomato", "tomatoes", "greenhouse", "compost")),
    ("furniture",
     ("sofa", "couch", "settee", "armchair", "wardrobe", "table", "chairs", "bookcase",
      "furniture", "sideboard", "dresser", "desk", "cabinet"),
     "Three routes: a council bulky waste collection (usually charged), the tip if you can drive it "
     "there, or a charity that collects - the British Heart Foundation takes sofas and wardrobes "
     "free if they have their fire labels and can come down the stairs. A free-ad site clears most "
     "furniture within a week if you say collection only.",
     ("cushion", "cushions", "new", "replacement", "cover", "covers", "which", "start",
      "not comfortable", "uncomfortable", "wobbly", "squeaks", "squeaking",
      "moths", "moth", "mice", "mouse", "rats", "ant", "ants", "flies", "bedbugs", "woodworm",
      "mould", "mold", "damp", "silverfish", "cockroach", "spiders",
      # a mark on a table is a repair, not a trip to the tip: "how do i get rid of a water mark
      # on my table" went out with the sofas
      "mark", "marks", "water mark", "water marks", "ring", "rings", "heat mark", "scratch",
      "scratches", "dent", "dents", "gouge", "chipped", "polish", "polishing",
      "clean", "cleaning", "stain", "stains", "smell", "smells", "upstairs", "delivery",
      "assemble", "assembling", "flat pack", "cover", "repair", "buy", "buying", "best",
      "which", "arrange", "layout", "small room")),
    # Books and toys came out of the same ask as the clothes: a house being thinned out has a
    # shelf of each, and "how do i get rid of books" was answered with the card for a stain on
    # paper while "how do i get rid of toys" was a hedge. A charity shop takes both, but not a
    # car load at once, so the route names the people who do want them.
    ("books",
     ("book", "books", "old books", "paperback", "paperbacks", "novels", "textbooks",
      "magazines", "comics", "encyclopaedias", "encyclopedias", "cookbooks", "book shelf",
      "bookshelf", "bookcase full of books"),
     "Ring the charity shop before you load the car: most take a bag or two of books and say no "
     "to a bootful, and a book bank at the tip or a supermarket car park takes as many as you "
     "have. Paperbacks go down well at a hospital, a care home or a phone box library, and a "
     "school fair clears children's books. Anything mouldy, damp or water-damaged goes in the "
     "paper recycling, not to a shop.",
     # "booking" and "booked" cannot be listed: an avoid word is matched loosely, so their stem
     # "book" is the word in "books" and the row stood down on every phrasing of its own question.
     # A line that books something reaches nothing here anyway, because a route word has to be in
     # it too.
     ("book a", "book the", "reserve", "reservation", "table", "hotel",
      "flight", "flights", "train", "tickets", "appointment", "read", "reading", "reads",
      "recommend", "recommendation", "recommendations", "what book", "which book", "good book",
      "best book", "books for", "book for", "kindle", "e reader", "e-reader", "audiobook",
      "library", "borrow", "store", "storage", "shelf", "shelves", "display")),
    ("toys",
     ("toy", "toys", "old toys", "lego", "duplo", "playmobil", "teddy", "teddies",
      "cuddly toys", "soft toys", "dolls", "action figures", "train set", "board games",
      "jigsaws", "puzzles", "childrens toys", "kids toys"),
     "Charity shops take toys only if they are complete and clean, so a nursery, a sure start "
     "centre or a refuge will take what a shop will not, and a free-ad site clears a box of lego "
     "in a day. Wash what you have and put the pieces back in their boxes first. A car seat or a "
     "cot is the exception: charity shops cannot take them, so it goes to the tip unless a "
     "friend wants it, and broken plastic is general waste.",
     ("buy", "buying", "best", "which", "for a 3", "for a 2", "for a 4", "for a 5",
      "year old", "years old", "gift", "present", "birthday", "christmas", "play with",
      "clean", "cleaning", "sterilise", "wash", "smell", "recall", "safety", "choking",
      "store", "storage", "tidy", "organise", "floor")),
    # A bike is the one item here that is worth money in any state, and the word is also a verb
    # and a sport, so its own avoid keeps riding, buying and mending out of it.
    ("bikes",
     ("bike", "bikes", "bicycle", "bicycles", "old bike", "kids bike", "childs bike",
      "mountain bike", "push bike"),
     "A bike project or a charity that refurbishes them takes one that does not ride: Re-Cycle "
     "and most city bike workshops want frames and parts, and a free-ad listing marked "
     "collection only clears one in a day. A scrap dealer buys the frame by weight, and the tip "
     "takes it with the metal. Charity shops rarely take bikes, so ring the project first.",
     ("ride", "riding", "rider", "buy", "buying", "which", "best", "cheap", "repair",
      "fix", "mend", "puncture", "tyre", "tyres", "chain", "brakes", "gears", "saddle",
      "lock", "helmet", "lights", "electric", "e-bike", "how far", "how long", "train",
      "lose weight", "fitness", "commute", "storage", "store", "shed", "carrier")),
    ("polystyrene",
     ("polystyrene", "styrofoam", "packaging", "packing peanuts", "bubble wrap"),
     "The white beaded stuff (expanded polystyrene) is not collected at the kerbside in most "
     "places, so it goes in the general waste - break it up so it takes less room, and put the "
     "pieces in a bag so they don't blow about. A few tips take it if you check your council's A "
     "to Z page, and the hard plastic trays often go in with the plastics.",
     ("cook", "cooking", "food", "insulate", "insulation", "sound", "noise", "craft", "paint",
      "glue", "fix", "filler")),
    ("oil",
     ("cooking oil", "used oil", "frying oil", "old oil", "chip pan", "deep fryer", "fat",
      "grease", "lard", "turkey fat", "bacon fat"),
     "Let it cool, pour it into a bottle or a tub, and put that in the general waste - never down "
     "the sink, where it sets with wipes into a blockage. A little fat can go in the food waste "
     "caddy if your council collects one, and a recycling centre takes larger amounts of used "
     "cooking oil.",
     ("belly", "lose", "losing", "burn", "burning", "diet", "weight", "body", "stomach", "abs",
      # the fat on a person is not the fat in a pan, and "how do i get rid of fat around my
      # waist" was answered with this bottle and a tub
      "waist", "tummy", "thigh", "thighs", "hips", "flabby", "fat around", "fat round",
      "bingo wings", "muffin top", "spot reduce", "calories",
      "reduce", "cut down", "best", "healthy", "healthiest", "which oil", "olive", "rapeseed",
      "smoke point", "temperature", "how hot", "calories", "reuse", "reusing", "use again",
      "sink", "blocked", "drain", "smell",
      # "get rid of grease from clothes" is the stain row's line, not the pan's: the fat that
      # goes in a bottle is the fat in a pan, so a garment or a surface named in the line stands
      # this row down
      "clothes", "clothing", "shirt", "shirts", "trousers", "jeans", "dress", "dresses",
      "jumper", "jumpers", "top", "tops", "t shirt", "tshirt", "hoodie", "cardigan", "coat",
      "jacket", "fabric", "carpet", "rug", "sofa", "settee", "couch", "upholstery", "floor",
      "tiles", "wall", "walls", "worktop", "drive", "driveway", "patio", "shoes", "trainers")),
    ("garden-waste",
     ("garden waste", "grass cuttings", "prunings", "hedge cuttings", "branches",
      # "leaves" on its own is a word half of the garden uses, and it was taking "why are the
      # tips of my plant's leaves brown" to the green bin: a leaf on the plant is the plant's
      # question, and a leaf in the barrow is this row's, so the phrases name the barrow.
      "fallen leaves", "dead leaves", "autumn leaves", "leaves in the garden",
      "leaves in my garden", "leaves from the garden", "leaves from my garden",
      "leaves on the lawn", "leaves on my lawn", "rake the leaves", "raked leaves",
      "leaf litter", "bag of leaves", "bags of leaves", "get rid of leaves",
      "lawn clippings", "green waste", "compost",
      # the bin itself, because "can i put leaves in the green bin" names no pile and no barrow:
      # without this the line lost its row when bare "leaves" left the key
      "green bin", "green bins", "in the green bin", "brown bin", "brown bins",
      "in the brown bin", "green wheely bin", "garden waste bin"),
     "The council's green bin is the cheapest route if you have one - many charge for the "
     "subscription and collect fortnightly - and the tip has a green waste skip. Grass, leaves and "
     "prunings can go in a compost bin at home too, but leave out cooked food, weeds in seed and "
     "anything diseased.",
     ("compost bin", "how to compost", "composting", "bin smells", "smell", "rats", "flies",
      # what belongs in a bin is the recycling list's question, not what to do with a barrow
      "what goes in", "what can go in", "what can i put in", "recycling", "card and paper",
      "when to cut", "cut back", "prune", "pruning", "mow", "mowing", "lawn",
      # a leaf that is going brown on the plant is not garden waste: the garden table's
      # plant-brown-tips row answers that, and "leaves" here was taking it
      "brown tips", "brown at the tips", "tips of the leaves", "leaf edges", "houseplant",
      "houseplants", "indoor plant", "pot plant", "yellow leaves", "yellowing")),
    ("christmas-tree",
     ("christmas tree", "real tree", "xmas tree", "old christmas tree"),
     "Councils collect real trees in the first couple of January weeks and shred them for mulch - "
     "check the day on the council's site, and strip the decorations and the stand first. Garden "
     "centres often take them back, and one that still has its roots in a pot can be planted out "
     "instead.",
     ("decorate", "decorating", "lights", "when should i put up", "take down", "artificial",
      "which tree", "buy", "best", "price", "cost", "needle", "needles", "drop", "dropping")),
    ("chemicals",
     ("chemicals", "weedkiller", "bleach", "white spirit", "thinners", "paint thinner",
      "pesticide", "antifreeze", "drain cleaner", "caustic soda", "ammonia", "old petrol",
      "paraffin", "gas bottle", "gas canister", "camping gas"),
     "Anything with a hazard symbol on it is household chemicals, and the tip's hazardous waste "
     "skip is where it goes - most sites take it from householders, and a few councils run set "
     "days, so ring before you drive over. Keep it in its own labelled container, never mix two "
     "together, and never pour it down the drain or into the bin. A gas bottle goes back to the "
     "shop that sells them.",
     ("mix", "mixing", "how much", "dose", "use", "using", "safe", "dangerous", "fumes", "smell",
      "kill", "weeds", "mould", "mold", "clean", "cleaning", "drain", "blocked", "unblock",
      "stain", "stains", "toilet", "sink", "shower", "grout")),
    ("mirror",
     ("mirror", "mirrors", "pyrex", "glass dish", "drinking glass", "window glass", "broken glass",
      "vase", "ceramic", "crockery", "plate"),
     "Mirrors, Pyrex and drinking glasses are not bottle-bank glass: they are made to take heat, so "
     "they melt at a different temperature and spoil the batch. Wrap it so nobody cuts themselves "
     "and put it in the general waste, or take it to the tip.",
     ("clean", "hang", "hanging", "mount", "steam", "streak", "smear", "smears", "crack", "chipped",
      "replace", "which glass", "wine glass", "bake", "baking", "ovenproof", "cut", "cutting")),
    ("aerosols",
     ("aerosol", "aerosols", "spray can", "spray cans", "deodorant can", "hairspray", "paint spray",
      "wd40", "wd-40"),
     "An empty aerosol can go in the kerbside recycling with the tins in most areas - check the "
     "council's list, and don't pierce or crush it. One that still has something in it is not "
     "rubbish: it goes to the tip, and a spray paint or a solvent goes to the hazardous waste.",
     ("use", "using", "safe", "dangerous", "explode", "heat", "hot", "cold", "spray",
      "spraying", "paint", "paint the", "squeak", "squeaky", "hinge", "rust", "lock")),
)

# The collection day is the one question in this domain with nothing to get rid of: it is a date
# the council keeps, not an item on its way out, so every item row and the which-bin shrug pass on
# it - and the shrug's own avoid list already named "bin day" and "bins out", which is how long it
# has been a hole. A person asking it has one bin full and no idea which morning it goes, so the
# answer is where the day is written down and the hour it has to be out by.
BIN_DAY = (
    "Your council's bin-day page will say: put your postcode in and it gives the day for your "
    "street, and that is the only place that is right, because bank holidays and ice move a round "
    "by a day or two and the paper calendar on the fridge goes stale. If it says tomorrow, put it "
    "out tonight; either way it has to be out by about 6.30 in the morning, so the night before is "
    "safest, and it comes back in the same day. If it is missed, report it on the council's "
    "missed-bin form that day rather than ringing - it is free and the round usually comes back "
    "within two working days."
)

# The line names the collection rather than an item: "when is bin day", "when should i put the
# bins out", "when do the bins go out", "how do i find out when my recycling is collected". The
# second tuple is the ask - a day, an hour or the way to find one - so "i put the bins out" as a
# statement and "the bins are full" stay other lines.
BIN_DAY_KEY = (
    ("bin day", "bins out", "bin out", "the bins out", "put my bin out", "put the bin out",
     "put the bins out", "put my bins out", "put the rubbish out", "put my rubbish out",
     "put the recycling out", "put the green bin out", "bins go out", "bin goes out",
     "collection day", "collection days", "bin collection", "bins collected",
     "bin collected", "bins are collected", "bin is collected", "bins emptied",
     "bin emptied", "bins are emptied", "bin men", "bin lorry", "bin round", "bin crew",
     "wheelie bin day", "recycling collected", "recycling is collected", "recycling emptied",
     "recycling collection", "rubbish collected", "rubbish is collected", "rubbish collection",
     "refuse collection", "garden waste collection", "my recycling", "my rubbish"),
    ("when", "what time", "what day", "which day", "what days", "how often", "find out",
     "check", "due", "should i put", "do i put", "am i supposed to put", "is it",
     "are they", "know",
     # a day that has moved is the same question, and it is the one people notice: "my bin
     # collection day has changed" was "I'm listening", because a statement about the day names
     # no question word at all and the new day is exactly what the council's page is for
     "changed", "changes", "has changed", "have changed", "change of",
     # phrases, not the bare verb: "the bin men moved my bin" is where the bin stands, and only a
     # collection that has moved is this question
     "has moved", "moved to", "moved day", "collection moved", "bin day moved",
     "swapped", "rescheduled", "new day", "different day", "which morning", "what morning"),
)

BIN_DAY_AVOID = (
    # the bin as a thing to clean, a smell, a pest, or a collection that has already failed: each
    # of those is another row's line, and none of them is asking which morning it goes
    "smell", "smells", "smelly", "stink", "stinks", "maggots", "wash", "clean", "cleaning",
    "rats", "rat", "mice", "mouse", "fox", "foxes", "seagull", "seagulls", "cat", "cats",
    "missed", "wasnt collected", "wasn't collected", "not collected", "didnt collect",
    "didn't collect", "havent collected", "haven't collected", "still there", "overflowing",
    "where do i put", "where can i put", "which bin", "what goes in", "what can i put in",
    "can i put", "how do i get rid", "get rid of", "tip", "recycling centre", "lid", "bags",
    "bin bags", "bin bag", "lock", "key", "replace", "buy", "size", "how big",
)

# A line that names the bin and asks what to do, with no item this domain knows. A shrug is the
# wrong reply to "can i put this in the bin": the routes are few and one of them is right.
WHICH_BIN = (
    "That depends on the item: anything with a plug or a battery goes back to a shop or the tip, "
    "chemicals go to the tip's hazardous skip, and bulky things are a council collection. Which "
    "item is it?"
)

# The line names the item and the domain has no row for it, so "That depends on the item... which
# item is it?" answers a question that was already answered in the asking: "which bin do tins go
# in", "what bin does foil go in" and "which bin do glass jars go in" all got the depends-on-the-
# item sentence with the item in the line. The kerbside box takes nearly all of it, and one item
# is one sentence, so the route is said and the "which item is it" is kept for the lines that name
# nothing ("can i put this in the bin").
#
# Each row is the words people use for the thing, and what the box does with it. The order is
# specific before general: a tin can is not the general "can", and a glass jar is not the glass
# row, which is about drinking glasses and ovenware.
ITEM_ROUTES = (
    # "can" alone is the modal ("can i put this in the bin") and took a line with no item in it,
    # so only the can that is a tin is spelled here
    ("tins", ("tin", "tins", "tin can", "tin cans", "cans", "drink can", "drink cans",
              "food tin", "food tins", "baked bean tin", "soup tin", "pet food tin", "aluminium"),
     "Tins and cans go in the kerbside recycling: rinse them, leave them whole and push the lid "
     "inside, and do not flatten them - the plant sorts steel from aluminium, and a flattened tin "
     "can be read as the wrong metal. An aerosol is the one can that goes back to a shop or the "
     "tip if it still has something in it."),
    ("foil", ("foil", "tin foil", "kitchen foil", "foil tray", "foil trays", "foil container",
              "bacofoil"),
     "Clean foil goes in the kerbside recycling, scrunched into a ball about the size of a fist so "
     "the machine can pick it out - loose foil and a foil tray with food stuck to it do not get "
     "sorted, and a greasy one goes in the general waste."),
    # a bare "bottle" is plastic in most households, so it is the plastic row's word and the
    # glass row keeps the bottle that says glass
    ("jars and bottles", ("jar", "jars", "glass jar", "glass jars",
                          "glass bottle", "glass bottles", "wine bottle", "beer bottle",
                          "jam jar", "sauce jar"),
     "Glass jars and bottles go in the kerbside recycling: empty and rinsed, lids off, and the "
     "lids go in with the metal if they are metal. Drinking glasses, Pyrex and ovenware are a "
     "different glass and go in the general waste, because they melt at the wrong temperature."),
    ("paper and card", ("paper", "newspaper", "newspapers", "card", "cardboard", "carton",
                        "cartons", "junk mail", "envelope", "envelopes", "magazine",
                        "magazines", "cereal box", "cereal boxes"),
     "Paper and card go in the kerbside recycling, flattened and dry: envelopes with a window, "
     "cereal boxes and junk mail all go in. A food carton or a tetra pak is only collected where "
     "the council says so, and a greasy pizza box goes in the general waste apart from its clean "
     "lid."),
    ("plastic bottles and tubs", ("plastic bottle", "plastic bottles", "bottle", "bottles",
                                  "tub", "tubs", "yoghurt pot", "yoghurt pots", "margarine tub",
                                  "plastic tub", "plastic tubs", "milk bottle", "shampoo bottle"),
     "Plastic bottles and tubs go in the kerbside recycling: rinse them, squash the bottles, and "
     "leave the lids on or off as your council says, because both are collected in most places "
     "now. A black plastic tray is the one that is often not sorted, and your council's A to Z "
     "page will say."),
    ("soft plastic", ("crisp packet", "crisp packets", "carrier bag", "carrier bags",
                      "plastic bag", "plastic bags", "bread bag", "film lid", "cling film",
                      "bubble wrap", "soft plastic", "padded envelope"),
     "Soft plastic - carrier bags, crisp packets, bread bags, film lids, bubble wrap - is not "
     "collected at the kerbside in most places. The big supermarkets take it in a bin by the door, "
     "and the collected plastic is turned into bin bags and pellets. A padded envelope is the "
     "same, and it is worth keeping a bag by the door for it."),
    ("polystyrene", ("polystyrene", "styrofoam", "packing peanuts", "meat tray", "meat trays",
                     "takeaway box", "takeaway boxes"),
     "Polystyrene goes in the general waste, not the recycling: expanded foam is mostly air, and "
     "no kerbside service takes it. A clean meat tray is the exception in some areas because some "
     "trays are the recyclable kind - squeeze it, and if it springs back it is foam and goes in "
     "the bin."),
    ("nappies", ("nappy", "nappies", "diaper", "diapers", "baby wipes", "wet wipes",
                 "sanitary", "sanitary pad", "sanitary pads", "tampon", "tampons", "incontinence"),
     "Nappies, wipes, pads and tampons all go in the general waste - nothing absorbent is "
     "recycled, and a wet wipe is not flushable however the packet reads, because it does not "
     "break down and it is most of what blocks a sewer. Bag it and bin it; a nappy bin with a lid "
     "keeps the room livable."),
    ("clothes and textiles", ("clothes", "clothing", "old clothes", "textiles", "textile",
                              "shoes", "old shoes", "curtains", "bedding", "duvet", "duvets",
                              "towels", "rags"),
     "Clothes, shoes, bedding and curtains do not go in the kerbside bin: the charity bank or the "
     "textile bank at the supermarket car park takes them, even worn ones, and they are sorted into "
     "resale, rags and fibre. A duvet and a pillow are the awkward ones - most banks will not take "
     "them, so ring the council for a bulky collection or take them to the tip's textile container."),
)


def _the_item_named(line):
    """The route for the item this line names, or None when it names none of them."""
    words = " %s " % str(line or "").lower().replace("\u2019", "'")
    for name, spellings, said in ITEM_ROUTES:
        if any((" %s " % spelling) in words for spelling in spellings):
            return said
    return None


def _a_bin_for_the_item(memory, understood):
    """The route for the item in the line, or the depends-on-the-item question when there is none."""
    if isinstance(understood, dict):
        said = _the_item_named(understood.get("text") or understood.get("clean") or "")
        if said:
            return said
    return WHICH_BIN


WHICH_BIN_AVOID = (
    # the bin itself, as a service rather than a thing to go in it: the collection day, the lid,
    # the smell, the seagulls
    "collection", "collected", "collection day", "missed", "empty", "emptied", "smell", "smells",
    "rats", "mice", "fox", "foxes", "seagull", "seagulls", "bags", "lid", "wheelie",
    "what goes in", "how often", "bins out", "bin out", "put the bins", "the bins out",
    "bin day", "what time", "tonight", "tomorrow", "this morning", "last night",
    "recycling bin",
    # "the tip" is matched inside "the tips of my hair", and that is not a place a thing goes:
    # "why do the tips of my hair go dry" was asked which item it was (polite-cord, #answers)
    # "at the tips" is NOT here: an avoid phrase is read loosely and by prefix, so "the tips"
    # in it matched "at the tip" and "do i need an appointment at the tip" lost its own answer.
    "tips of", "brown tips", "white tips", "split ends", "dry tips",
    "fingertips", "finger tips", "nails", "hair", "plant", "plants", "leaves",
)

# Sorting the recycling is the one rubbish question whose answer needs no item: people want the
# short version of what goes in which box, and what the council will not take.
RECYCLE = (
    "Roughly: flattened card and paper, glass jars and bottles, tins and cans, plastic bottles and "
    "tubs, and clean foil - rinsed, loose rather than bagged, because a bag of the right things "
    "still goes to waste. Soft plastic (carrier bags, crisp packets, film lids) is not collected "
    "at the kerbside in most places: the big supermarkets take it in a bin by the door. For "
    "anything odd, the council's A to Z page has a line for it."
)

RECYCLE_AVOID = (
    "first aid", "kit", "sandwich", "lunch", "lunchbox", "picnic", "stocking", "stockings",
    "hamper", "hospital bag", "empty", "emptied", "computer", "laptop", "windows", "mac",
    "file", "files", "desktop", "disk", "drive", "deleted", "delete", "restore", "email",
    "folder", "folders", "phone",
    "hard drive", "bin day", "bins out", "put the bins", "collection day", "what time",
    "bin smells", "smell", "smells", "limescale", "phone contract",
    # an hours ask names the site and the clock, and what goes in the box is not the answer to
    # any of them: "what are the opening hours of the recycling centre" was the whole-box list
) + A_HOURS_ASK

# A trip to the tip is a job of its own: what to bring, what they will not take, and where the
# awkward things go once you are there.
TIP = (
    "Load it so it can be tipped in one go, and put the awkward things on top: a car load usually "
    "drives straight in, but many sites ask for proof of address, and a van or a trailer is often "
    "booked. Paint, chemicals, gas bottles, batteries and anything with a screen go to a staffed "
    "container or to a steward rather than into a skip, so ask at the gate. Soil, rubble and "
    "plasterboard are usually limited to a few bags a visit."
    # "Tip or collection?" is the choice most people are actually weighing, and the row only "
    # said how to do the tip run: the other route is the council's, booked rather than driven. "
    # It is the same page the site's own details are on, which is why it is here and not a row "
    # about a service nobody can name without their council.
    " If you cannot drive it there, the council's bulky waste collection is the other route: "
    "usually charged, booked online or by phone, and they take it from the doorstep."
)

TIP_AVOID = (
    # "any tips", a tip in a restaurant and a tip at the pub are not the household waste site
    "any tips", "tips for", "tip in", "tip on", "the waiter", "waitress", "restaurant", "pub",
    "percent", "gratuity", "tidy", "garden tip",
    # the other tip is the arithmetic at the table: "how do i work out a tip" was a question
    # about how much to leave and got the household waste site's hours
    "work out a tip", "work out the tip", "work out a service", "work out the service",
    "how do i tip", "how to tip", "how should i tip",
    # a story that ends in a tip is not a tip run: "i buried the old fence posts in the garden
    # instead of taking them to the tip" was read as a question about the visit
    "buried", "bury", "burying", "instead of", "ended up",
    "how much", "cost", "charge", "price", "open", "closing", "opening", "what time", "close",
    # the other tip is the arithmetic at the table, and it is asked with "calculate" as
    # often as "work out": "how do i calculate a tip" was a question about how much to
    # leave and got the household waste site's hours
    "calculate a tip", "calculate the tip", "calculate a service", "calculate the service",
    "how much should i tip", "how much do i tip",
    "nearest", "where is", "council tax", "holiday", "bank holiday",
    # "the tip" is matched inside "the tips of my hair", and that is not a place a thing goes:
    # "why do the tips of my hair go dry" was asked which item it was, and then, once the visit
    # rows grew, which of them the trip was. The thing that has tips is the fence.
    # "at the tips" is NOT here: an avoid phrase is read loosely and by prefix, so "the tips"
    # in it matched "at the tip" and "do i need an appointment at the tip" lost its own answer.
    "tips of", "brown tips", "white tips", "split ends", "dry tips",
    "fingertips", "finger tips", "nails", "hair", "plant", "plants", "leaves",
)

# "what can i do with the mince in the fridge" and "half a bag of spinach in the fridge" were
# both answered with the fridge-disposal card, because the removal words include the bare "do
# with" and a container is the one item here whose name also appears in a cooking question. The
# dish table's own reading decides it: a line that asks what to make with a food it names is the
# kitchen's question, and this domain is only for the thing on its way out.
def _not_a_cook_ask(understood):
    """False when the line is asking what to cook, so no item row answers."""
    return not cook_ask(understood)



# Main read "where do i put the salt in the dishwasher" as a disposal line, because the removal
# words include the bare phrase "where do i put" and a person says it just as often about a thing
# on its way out as about a place for a thing that stays. The preposition after the verb is what
# tells the two apart: a line that puts something *into* an item this domain knows is placing it,
# and the item named is where it goes, not the waste. "where do i put the old fridge" keeps its
# route, and so does every line without a place in it.
_CONTAINERS = sorted({name for item in ITEMS for name in item[1]}, key=len, reverse=True)
PUT_INTO = re.compile(
    r"\b(?:put|puts|putting|place|places|placing|keep|keeps|keeping|store|stores|storing|add|"
    r"adding|load|loading|pour|pouring|stick|sticking|poke|poking|stand|standing)\b"
    r"[^.;?!]{0,40}?\b(?:in|into|inside|on|onto|under|behind|beside|near)\s+"
    r"(?:the\s+|my\s+|our\s+|a\s+|an\s+|your\s+|its\s+)?(?:%s)\b"
    % "|".join(re.escape(name) for name in _CONTAINERS))


def _said(understood):
    """The line as typed, then the reading's own text - what a word match here looks at."""
    if not isinstance(understood, dict):
        return ""
    return str(understood.get("plain") or understood.get("clean")
               or understood.get("norm_text") or "")


def _not_a_container(understood):
    """False when the item named holds what the line is putting into it."""
    return not PUT_INTO.search(_said(understood).lower())


# "Where do i put the salt" is a placement question, and the removal words include "where do i
# put" and "where can i put" because that is also how a person asks where something goes on its
# way out of the house. What tells the two apart is the thing: a consumable that goes *in* a
# machine - salt, tablets, powder, rinse aid - is being placed, and "where do i put dishwasher
# tablets" was answered with which shop takes the old machine. An item of furniture or an
# appliance still reads as disposal, which is its usual question ("where do i put a mattress").
PLACEMENT = re.compile(
    r"\bwhere\s+(?:do|does|can|could|should|shall|would)\s+(?:i|we|you|it)\s+put\b"
    r"|\bwhere\s+to\s+put\b|\bwhere\s+i\s+put\b")
# Two kinds of consumable word. "Rinse aid", "fabric softener" and "descaler" are only ever put
# into a machine, so the ask alone is enough. "Tablets", "salt" and "powder" are just as often
# medicine, food or water-softening salt: "where do i put the tablets" is the pharmacy's question
# and the disposal rows must keep it, so those need a machine named in the line as well. Azure-spoon
# found this on the review: with the bare word enough, the pharmacy route lost the line.
ONLY_A_MACHINE = ("rinse aid", "rinse-aid", "fabric softener", "descaler")
A_MACHINE = re.compile(r"\b(?:dishwasher|dish washer|washing machine|washer|washer dryer|"
                       r"washer-dryer|dishdrawer|dish drawer|tumble dryer|tumble drier|dryer)\b")
CONSUMABLE = ("salt", "tablet", "tablets", "powder", "detergent", "rinse aid", "rinse-aid",
              "pod", "pods", "capsule", "capsules", "softener", "descaler")


def _a_consumable_is_placed(understood):
    """True only when the line asks where to put something that goes in a machine."""
    said = _said(understood).lower()
    if not PLACEMENT.search(said):
        return False
    if any(word in said for word in ONLY_A_MACHINE):
        return True
    return bool(A_MACHINE.search(said)) and any(word in said for word in CONSUMABLE)


def _disposal_guard(understood):
    """False when this line is another row's question: a cook ask, a container or a placement."""
    return (_not_a_cook_ask(understood) and _not_a_container(understood)
            and not _a_consumable_is_placed(understood))


# `bias` leans an entry over a neighbour of the same rank. A white good is the one item here whose
# rival ("is a tumble dryer worth it") scores as high on the same line, and the item on its way out
# is the question when the line says "get rid of".
ENTRIES = [
    entry("dispose-" + item[0], (item[1], RID), item[2],
          avoid=item[3] + CURING_ASIDE + NOT_RUBBISH,
          bias=item[4] if len(item) > 4 else 1, guard=_disposal_guard,
          # a sixth element is the item's own ask, for a row that would otherwise answer the
          # question a person asks about a symptom rather than about the thing
          ask=item[5] if len(item) > 5 else ())
    for item in ITEMS
] + [
    # the shrug is the answer when nothing more specific fits, so it sits just under every item row
    entry("dispose-which-bin", (BIN_WORDS, BIN_ASK), _a_bin_for_the_item,
          avoid=WHICH_BIN_AVOID, bias=-1),
    entry("recycle-what-goes-where",
          (("recycle", "recycling", "recycled", "what goes in", "landfill"),
           ("what", "which", "how", "sort", "sorting", "goes", "go in", "in the", "can i",
            "do i")),
          # the whole-box list is the answer when nothing more specific fits, so any item row
          # beats it: "where do i recycle batteries" is the battery answer, not the list
          RECYCLE, avoid=RECYCLE_AVOID, bias=-1),
    entry("bin-day", BIN_DAY_KEY, BIN_DAY, avoid=BIN_DAY_AVOID, bias=2),
    entry("dispose-tip-visit",
          (("the tip", "a tip", "to the tip", "tip run", "recycling centre", "household waste site",
            "the dump",
            # the council runs the place, so people name it that way: "what about the council tip"
            # was answered "it is fine not to tip in the UK", by the money table's tipping row
            "council tip", "council dump", "council recycling centre", "council recycling center"),
           # "Should i go to the tip or is there a collection" asks whether to make the trip at
           # all, and the ask words were all about what to bring once there: on "the tip" plus
           # "go" or "collection" the row scored nothing, the money table's tipping row took the
           # line ("it is fine not to tip in the UK") and the question was never answered.
           ("what", "take", "bring", "need", "allowed", "can i", "how", "load", "van",
            "go", "goes", "going", "collection", "bulky", "worth")),
          TIP, avoid=TIP_AVOID, bias=2),
    # "Where is my local tip" was a punt and "how do i find my nearest recycling centre" was the
    # maths card, because "nearest" is a rounding word there and `TIP_AVOID` keeps "where is" and
    # "nearest" off the visit row. The location is a different question from the trip: the trip
    # asks what to bring, this one asks which site and how to find it.
    entry("find-your-tip",
          # the council is who runs it, so "where is the council tip" is the same lookup: the
          # place is named as a place, which keeps the bare follow-up ("what about the council
          # tip") on the visit row, where what to bring is what they want
          (("local tip", "my local tip", "nearest tip", "closest tip", "tip near me",
            "council tip near me", "where is the council tip", "wheres the council tip",
            "where is my council tip", "the council tip near me",
            "the tip near me", "tip local to me", "where is the tip", "where is my tip",
            "where is the dump", "the dump near me", "local dump", "nearest dump",
            "local recycling centre", "local recycling center", "nearest recycling centre",
            "nearest recycling center", "recycling centre near me", "recycling center near me",
            "closest recycling centre", "household waste site near me", "household waste near me",
            "find a tip", "find the tip", "find a recycling centre", "find the recycling centre",
            "find the dump", "which tip", "which recycling centre", "my nearest tip",
            "dump near me"),
           ("where", "how", "find", "nearest", "closest", "local", "near me", "near",
            "look up", "search", "which", "is my", "the")),
          ("Put your postcode into your council's recycling centre page - searching your "
           "postcode and \"recycling centre\" lands on it, and gov.uk links every council's site "
           "finder - and that page has the opening hours, what the site takes and whether you "
           "have to book. Take something that proves you live in the area, because most sites "
           "check it at the gate, and book a slot first if your council runs a booking system, "
           "which the busiest ones do at weekends."), bias=3,
          # not `TIP_AVOID`: that tuple exists to keep the *other* tipping questions off the tip
          # rows and it holds "where is" and "nearest", which are this row's whole question.
          avoid=("any tips", "tips for", "tip in", "tip on", "the waiter", "waitress",
                 "restaurant", "pub", "percent", "gratuity", "work out a tip", "how do i tip",
                 "how to tip", "how should i tip", "how much", "cost", "charge", "price",
                 "open", "closing", "opening", "what time", "close", "council tax", "holiday",
                 "bank holiday", "service charge", "tattoo", "barber", "hairdresser",
                 # a statement that the site is shut is not a lookup: "my local tip is closed"
                 "closed", "is closed", "is shut", "shut",
                 # a report of what the site told them is not a lookup: "the tip near me says no
                 # paint tins if theyre not empty" is a question about the paint, not the site.
                 "says", "said", "told me", "they say", "they said", "reckons", "apparently")),
    # What the visit costs is the other half of the same trip, and it was an honest pass with a
    # wrong tip card behind it: "how much does the tip cost" is not a question about a waiter.
    # `TIP_AVOID` keeps the amount-to-leave lines out of the visit row, so this row takes them.
    entry("tip-charges",
          (("the tip", "a tip", "to the tip", "tip run", "recycling centre", "household waste",
            "the dump", "council tip"),
           ("cost", "costs", "charge", "charges", "charged", "free", "pay", "how much", "price",
            "fees", "fee", "rubble", "tyres", "tyre", "plasterboard", "soil", "hardcore",
            "diy", "van", "trailer", "permit")),
          ("Household rubbish is free at a council tip; what they charge for is the DIY waste - "
           "rubble, soil, plasterboard, old tyres and sometimes garden waste - and the price is "
           "set by your council, so check its page for your site before you load the car. Vans "
           "and trailers usually need a permit booked in advance, and a few sites want proof you "
           "live in the area."), bias=3,
          # the trip's own questions (hours, what is allowed) are the visit row's
          avoid=("any tips", "tips for", "how much to tip", "should i tip", "the waiter",
                 "restaurant", "percent", "gratuity",
                 # a service charge on a bill is the bill's "charge" and the money table's
                 # tipping answer: "what is the difference between a tip and a service charge"
                 # was the household waste site, because "a tip" met "charge"
                 "service charge", "discretionary", "difference between", "same as a tip",
                 "is a tip", "the bill", "on the bill", "tattoo", "hairdresser", "barber",
                 # a sofa or a mattress is a bulky collection, not the site's price list:
                 # "how much does it cost to take a sofa to the tip" was told what DIY waste
                 # costs when the three routes were the answer
                 "sofa", "settee", "couch", "armchair", "furniture", "wardrobe", "mattress",
                 "bed", "table", "chairs", "bulky", "charity", "fridge", "freezer",
                 "washing machine", "cooker", "tumble dryer", "dishwasher",
                 # "can i take rubble to the tip" is what the site accepts, not what it costs
                 "can i take", "can i bring", "can i put", "what can i take", "what can i bring",
                 "allowed", "am i allowed", "what goes", "what do you take", "will they take",
                 "do they take", "accept")),
]
