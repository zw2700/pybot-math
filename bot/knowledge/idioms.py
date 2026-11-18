"""Idioms: the everyday figures of speech, kept as one table and answered as language.

The answers lane owns this domain, and it exists because an idiom is the one kind of line the
rest of the knowledge base reads word by word and gets wrong in the same shape every time:

    i have my hands full this week   -> "A hand that has been sore for a week or more is usually
                                         a tendon or a strained muscle"   (sore-wrist-weeks)
    im pulling your leg              -> "A pulled thigh or calf muscle ..."  (sore-leg)
    its raining cats and dogs        -> "A cat and a dog - how long have they been with you?"
    im in the dark about it          -> "Leave a small warm light on ..."  (child-light-at-night)
    let me sleep on it               -> "An extra hour or two is usually the good call ..."
    its a piece of cake              -> a shrug

None of those is a question about a hand, a leg, a cat, a light or a cake. The fix is the
ordinary one for this lane: the meaning is data, keyed by the phrase and not by the wording
around it, and one row per idiom answers every way of saying it - "what does X mean", "he said
X", "X", "why do people say X".

The phrase is in both key groups on purpose. A row needs two covered positions to answer
(MIN_SCORE in lookup.py), and a phrase scores three: with the same phrase in both groups the row
scores six and wins over a body row that caught one of its words, without any avoid lists in the
modules that were answering these by accident.
"""
from .lookup import entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("language-and-writing",)

# phrase, the other ways people write the phrase, the reply.
#
# The reply says what it means in the first clause - that is the whole question - and then turns
# back to the person, because an idiom used in a chat is usually the opening of something.
_IDIOMS = (
    ("raining cats and dogs", ("raining cats dogs", "rain cats and dogs", "cat and dog weather"),
     "It just means raining very hard - nothing to do with animals. Are you stuck in it, or "
     "looking for something to do on a wet day?"),
    ("piece of cake", ("piece of cake", "a piece of cake"),
     "It means very easy: \"that was a piece of cake\" is \"that was no trouble at all\". What is "
     "the thing you are hoping will be easy?"),
    ("pulling your leg", ("pulling my leg", "pull your leg", "pulled my leg", "on the pull"),
     "Pulling someone's leg is teasing them - saying something untrue as a joke, not actually "
     "touching their leg. Was someone having you on?"),
    ("a lot on my plate", ("lot on my plate", "too much on my plate", "a lot on your plate"),
     "It means you have more to deal with than you can comfortably hold at once - from a dinner "
     "plate piled high. What is on yours at the moment?"),
    ("my hands are tied", ("hands are tied", "hands tied", "my hands tied"),
     "It means you cannot act, even if you want to - someone else has the say. What is the thing "
     "you are stuck on?"),
    ("in the dark about", ("in the dark", "kept in the dark", "left in the dark"),
     "Being in the dark about something means nobody has told you what is going on. What is it "
     "you have not been told?"),
    ("snowed under", ("snowed under", "snowed under with work"),
     "Snowed under just means buried in work or messages - nothing to do with weather. What is "
     "the pile in front of you?"),
    ("an arm and a leg", ("arm and a leg", "cost an arm and a leg", "costs an arm and a leg"),
     "It means very expensive: \"it cost an arm and a leg\" is \"it cost far too much\". What "
     "are you pricing up?"),
    ("under the weather", ("under the weather", "feeling under the weather"),
     "Feeling under the weather means a bit unwell - off colour, not seriously ill. What is "
     "wrong - sore throat, tired, sick?"),
    ("tip of my tongue", ("tip of my tongue", "on the tip of my tongue"),
     "That is the feeling of knowing a word or name that will not come. It usually arrives a "
     "minute later, or when you stop trying. What are you trying to remember?"),
    ("ball is in your court", ("ball in your court", "ball is in their court"),
     "It means the next move is yours to make - the other person has done their part. What are "
     "you deciding whether to do?"),
    ("break the ice", ("break the ice", "breaking the ice", "icebreaker"),
     "Breaking the ice just means getting a first conversation going with someone you do not know "
     "well. Is this a new job, a date, or a room full of strangers?"),
    ("beating around the bush", ("beating around the bush", "beat around the bush"),
     "It means avoiding the point instead of saying it. Do you want help working out how to say "
     "the thing plainly?"),
    ("let the cat out of the bag", ("cat out of the bag", "let the cat out"),
     "It means telling a secret by accident. Whose secret was it?"),
    ("once in a blue moon", ("once in a blue moon", "blue moon"),
     "It means very rarely - now and then rather than often. What is it that only happens "
     "occasionally?"),
    ("on the same page", ("on the same page", "not on the same page"),
     "Being on the same page means agreeing about what you are doing. Are you trying to get "
     "someone to agree with you?"),
    ("going round in circles", ("round in circles", "going in circles", "go round in circles"),
     "It means talking or thinking without getting anywhere. What is the decision you keep "
     "circling?"),
    ("head above water", ("head above water", "keep my head above water"),
     "It means just about coping - keeping up with money, work or everything at once. Which one "
     "is it for you?"),
    ("bite off more than you can chew", ("more than i can chew", "more than you can chew"),
     "It means taking on more than you can manage. What did you say yes to?"),
    ("get something off my chest", ("off my chest", "get it off my chest", "off your chest"),
     "It means saying something that has been weighing on you, so you feel lighter. Go on - what "
     "is it?"),
    ("the cold shoulder", ("cold shoulder", "giving me the cold shoulder"),
     "Giving someone the cold shoulder means being deliberately distant with them. Has someone "
     "gone quiet on you?"),
    ("hands full", ("hands full", "my hands are full", "hands are full"),
     "Having your hands full means you are as busy as you can be. What is taking all of it?"),
    ("sleep on it", ("sleep on it", "i will sleep on it", "lets sleep on it"),
     "Sleeping on it means waiting until tomorrow before deciding, so it looks different in the "
     "morning. That is usually a good call for a big one. What are you deciding?"),
    ("clear my head", ("clear my head", "clear your head", "clearing my head"),
     "Clearing your head means stepping away for a bit - a walk, fresh air, no screens - so the "
     "thinking gets easier. What is crowding it?"),
    ("put my finger on it", ("put my finger on it", "put your finger on it"),
     "It means naming the thing you can sense but not yet describe. What is the feeling?"),
    ("back to square one", ("back to square one", "back at square one"),
     "It means starting again from the beginning after a plan fell through. What are you "
     "restarting?"),
    ("the last straw", ("last straw", "the final straw"),
     "The last straw is the small thing that finally makes you react, after a lot of bigger ones. "
     "What happened?"),
    ("cut corners", ("cut corners", "cutting corners"),
     "It means doing something quickly and cheaply by skipping the careful parts. Are you being "
     "asked to, or did someone do it to you?"),
    ("best of both worlds", ("best of both worlds", "both worlds"),
     "The best of both worlds means getting the good parts of two options at once. What are the "
     "two you are choosing between?"),
    ("speak too soon", ("spoke too soon", "speak too soon", "spoken too soon"),
     "Saying you spoke too soon means the thing you just said has already been proved wrong. "
     "What happened?"),
    # --- the second wave, found by chatting through the commonest expressions ----------------
    # Each of these was answered by a card about one of its words, or by a shrug: "it came out of
    # the blue" got the laundry colour-run card, "its not my cup of tea" the caffeine limit,
    # "im ready to throw in the towel" the charity-shop card, and "it was a shot in the dark"
    # rang 999 for a gunshot (that fence is in bot/modules/safety.py).
    ("out of the blue", ("came out of the blue", "come out of the blue", "comes out of the blue"),
     "It means it happened suddenly, with no warning. What came out of the blue?",
     ("wash", "washed", "washing", "whites", "clothes", "stain", "dye", "dyed", "laundry",
      "shirt", "shirts", "socks", "drum", "bleach")),
    # The negator is the idiom. "cup of tea" on its own is a drink somebody wants made, and it
    # was answering "can i have a cup of tea" and "how do u make a proper cup of tea" with what
    # the expression means, so every key here holds the "not".
    # People ask it as a question with the negator left out - "is that your cup of tea", "is
    # she your cup of tea" - and the drink card took all of those. The question is the same
    # expression, so its own words are keys here too.
    ("not my cup of tea", ("not her cup of tea", "not his cup of tea", "not a cup of tea",
                           "isnt my cup of tea", "is not my cup of tea",
                           "not really my cup of tea", "isnt really my cup of tea",
                           "not quite my cup of tea", "not their cup of tea",
                           "your cup of tea"),
     "It means you don't like it much, said politely. What is it that isn't for you?",
     ("caffeine", "coffee", "espresso", "cups a day", "brew", "tea bag", "decaf", "sugar",
      "milk", "mg",
      # The drink itself, and not the opinion of it: "how many cups of tea will a full kettle
      # make" is the fill answer and "how many cups of tea is too many" the caffeine limit, and
      # the second one was the expression too, because "cups a day" alone did not catch "cups of
      # tea". A count or a measure of tea is a question about tea.
      "kettle", "kettles", "how many cups", "how many mugs", "how many teas", "how much tea",
      "too many cups", "too many mugs", "too much", "cups of tea a day",
      # A measure of water for a count of cups is the fill answer, and the count on its own is the
      # follow-up it invites: "how much water should i boil for four cups of tea" and "and for two
      # cups of tea" were both read as the expression.
      "how much water", "water for", "for one cup", "for two cups", "for three cups",
      "for four cups", "for five cups", "for six cups", "for two mugs", "for three mugs",
      "for four mugs",
      # The drink is real and something happened to it: a cup over a laptop is the spill answer,
      # which is the opposite of an opinion of it.
      "laptop", "keyboard", "spilled", "spilt", "knocked over", "knocked it over",
      # What is made, brewed, poured or counted is a cup, not an opinion, and a cup that is in
      # the room is the drink somebody made: "how do you like your cup of tea" is milk and sugar,
      # and "your cup of tea is on the table" is the cup on the table.
      "make", "making", "made", "brewing", "boiling", "hot water", "drink", "drinking",
      "too much tea", "fill", "teapot", "how long to brew", "strong", "weak", "milk in",
      "stewed", "how do you like", "on the table", "in front of you", "here is", "heres",
      "i made", "made you", "brewed you", "i poured", "poured you")),
    ("throw in the towel", ("throwing in the towel", "threw in the towel"),
     "It means giving up on something you have been trying hard at. What are you thinking of "
     "stopping?",
     ("clothes", "charity", "textile", "donate", "recycling", "fabric", "wash", "laundry",
      "dry", "bin", "skip")),
    ("shot in the dark", ("a shot in the dark", "just a shot in the dark"),
     "It means a guess with very little to go on. What are you trying to work out?",
     ("gun", "guns", "pistol", "police", "ambulance", "999", "911", "wound", "blood", "bleeding",
      "neighbour", "neighbor", "shotgun")),
    ("break a leg", ("break a leg", "broke a leg", "breaking a leg"),
     "It is what people say to someone before a show or a match: it means good luck, because "
     "wishing it out loud is thought to jinx it. What are you going on for?"),
    ("see eye to eye", ("dont see eye to eye", "doesnt see eye to eye", "see eye to eye"),
     "It means you agree about something - and this line says you don't. What is the "
     "disagreement about?",
     ("glasses", "specs", "eyesight", "optician", "screen", "dry eye", "sight", "blurry",
      "contact lens", "lenses")),
    ("long story short", ("to cut a long story short",),
     "That is the short-version opener - go on, then. What happened?",
     ("bedtime story", "read me a story", "tell me a story", "story about")),
    ("in hot water", ("im in hot water", "in hot water at work", "got in hot water"),
     "It means you are in trouble over something. What happened?",
     ("kettle", "boiler", "immersion", "shower", "bath", "water bill", "heating", "tap",
      "cylinder", "radiator", "hot water bottle")),
    ("dead set on", ("dead set against", "im dead set on it"),
     "It means you have decided and won't be talked out of it. What is it?",
     ("died", "dead body", "passed away", "funeral", "grief", "grieving", "buried", "death")),
    ("in the same boat", ("we are in the same boat", "were in the same boat"),
     "It means you are both stuck in the same difficult position. What is the situation?"),
    ("off the top of my head", ("off the top of your head",),
     "It means from memory, without looking anything up. What do you need to remember?"),
    ("scratched the surface", ("only scratched the surface", "scratch the surface"),
     "It means you have only made a start on something much bigger. What is the bigger thing?"),
    ("call it a day", ("lets call it a day", "call it a night", "time to call it a day"),
     "It means stopping for today and picking it up later. What are you leaving until tomorrow?"),
    ("hit the nail on the head", ("you hit the nail on the head",),
     "It means you got it exactly right. What was it about?"),
    ("jump the gun", ("jumping the gun", "jumped the gun", "dont jump the gun"),
     "It means starting before the right moment. What are you about to do early?"),
    ("burning the candle at both ends", ("burn the candle at both ends", "burning the candle"),
     "It means doing too much on too little sleep, usually for weeks. What is the week like - "
     "work in the day and something else at night?"),
    ("bite the bullet", ("biting the bullet", "bit the bullet"),
     "It means getting on with the thing you have been putting off. What is it?"),
    ("sitting on the fence", ("sit on the fence", "hes sitting on the fence",
                              "shes sitting on the fence"),
     "It means not deciding yet. What are the two options?"),
    ("on the ball", ("shes on the ball", "hes on the ball", "really on the ball"),
     "It means quick and on top of things. What is it they are on top of?"),
    ("ring a bell", ("does that ring a bell", "ring any bells", "rings a bell"),
     "It means it sounds familiar without being certain. What name or thing are you trying to "
     "place?"),
    ("barking up the wrong tree", ("youre barking up the wrong tree",),
     "It means looking in the wrong place for the answer. What are you trying to find?"),
    ("that ship has sailed", ("ship has sailed",),
     "It means the chance has gone. What was it?"),
    ("water under the bridge", ("thats water under the bridge", "its water under the bridge"),
     "It means it is in the past and not worth arguing about now. What happened?"),
    ("pulling my hair out", ("pull my hair out", "tearing my hair out"),
     "It means you are frustrated with something that will not work. What is it?",
     ("hair loss", "losing my hair", "thinning", "shampoo", "scalp", "grey hair", "hair dye",
      "hairdresser", "cut my hair", "hair falling")),
    ("up in the air", ("still up in the air", "its up in the air"),
     "It means it is not decided yet. What are you waiting to hear?",
     ("flight", "flights", "plane", "airport", "travel", "luggage")),
    ("grey area", ("its a grey area", "it is a grey area", "gray area"),
     "It means it is not clearly right or wrong. What is the situation?",
     ("grey hair", "gray hair", "paint", "painting", "dye", "walls", "whitewash")),
    ("play it by ear", ("playing it by ear", "played it by ear"),
     "It means deciding as you go instead of planning now. What is the day?"),
    ("cutting it fine", ("cut it fine", "cutting it close"),
     "It means leaving almost no time to spare. What is the deadline?",
     ("cut my", "cutting my", "knife", "scissors", "finger", "thumb", "bleeding")),
    ("keep me in the loop", ("keep you in the loop", "keep in the loop", "in the loop"),
     "It means keep me updated. What are you waiting to hear about?"),
    ("the bigger picture", ("look at the bigger picture", "bigger picture", "the big picture"),
     "It means the wider view rather than this one detail. What decision is it for?"),
    ("run of the mill", ("nothing special about it",),
     "It means ordinary, nothing unusual. What is the thing?"),
    ("the ball is rolling", ("ball is rolling", "get the ball rolling", "got the ball rolling"),
     "It means the thing has started moving at last. What did you set going?"),
    ("cant get my head round it", ("get my head round it", "get my head around it",
                                   "cant get my head around it"),
     "It means getting to understand something that is not clicking yet. What is the thing?"),
    ("pinch of salt", ("take it with a pinch of salt", "grain of salt"),
     "It means don't take it too literally. Whose claim was it?",
     # The words are the salt question's, and never "salt" itself: the expression says that word,
     # so a fence on it stood this row down on its own phrase (the lesson from the hot/cold card).
     ("sodium", "blood pressure", "grams", "mg", "limit", "recommended", "seasoning",
      "stock cube")),
    ("blow off steam", ("blowing off steam", "blew off steam", "let off steam"),
     "It means letting the frustration out so it stops building up. What has got you wound up?"),
    ("back on track", ("got back on track", "keep on track"),
     "It means going the right way again after a slip. What did you get back to?"),
    ("on the mend", ("shes on the mend", "hes on the mend"),
     "It means getting better after being ill. How long has it been going on?"),
)


# An expression is only the expression when the line is not about the thing itself. "should i
# freeze the piece of cake", "i dropped my piece of cake on the floor" and "the room is in the
# dark" were all read as figures of speech once this table could win them, and each of them lost
# an answer that was right (the cake's keeping card, the five-second rule, the night light).
#
# The fence is the object the rest of the line is about - the food, the light, the nail, the
# piano - and it is written once per expression here rather than as a rule, because what makes a
# line literal is different for every expression. One rule holds throughout: the fence never
# names a word of the expression itself, so it can never stand the row down on its own phrase.
# The words are the object's own card, which is what should answer the line instead.
_LITERAL_NEIGHBOURS = {
    # A cup of tea is a drink people ask about all day, and the expression is the refusal of one,
    # so the row answers the refusal: without these words it answered "how do you make a good cup
    # of tea" and "how many cups of tea is too many" with what the phrase means, which is the
    # fault the row was added to fix.
    "not my cup of tea": ("make", "making", "made", "kettle", "water", "how long",
                          "how many", "how much", "brew", "brewing", "teabag", "taste",
                          "tastes", "tasting", "bitter", "strong", "strength", "green tea",
                          "black tea", "good for", "bad for", "healthy", "unhealthy",
                          "before bed", "at night", "sleep", "wake me", "too late",
                          # a number of them is a quantity of drink, not a way of saying no:
                          # "is 4 cups of tea too much" was told what the expression means
                          "cup a day", "cups a day", "too much", "drink it"),
    "piece of cake": ("freeze", "frozen", "freezing", "defrost", "freezer", "leftover",
                      "leftovers", "dropped", "drop", "floor", "slice", "slices", "crumb",
                      "crumbs", "eaten", "ate", "bakery", "tier", "frosting", "ganache",
                      "sprinkles", "tins", "traybake", "fresh", "keeps", "keeping", "kept",
                      "tin", "fridge", "fridged", "buttercream", "fondant", "cutting"),
    "a lot on my plate": ("dinner", "lunch", "supper", "portion", "portions", "food", "eat",
                          "eating", "meal", "meals", "vegetables", "gravy"),
    "my hands are tied": ("rope", "ropes", "knot", "knots", "string", "tape", "tied up with",
                          "cable", "cables", "bungee", "restraint"),
    "in the dark about": ("room", "rooms", "bedroom", "bed", "beds", "under the bed",
                          "under the sofa", "hall", "hallway", "landing", "stairs",
                          "cupboard", "cellar", "loft", "light", "lights", "lighting", "lamp",
                          "lamps", "torch", "candle", "candles", "bulb", "bulbs", "fuse", "fuses",
                          # and reading a page with too little light on it is the eye's own
                          # question: "does reading in the dark damage your eyes" was told what
                          # the expression means instead of what a dim page does to the eye
                          "read", "reading", "book", "books", "page", "pages", "print", "eyes",
                          "eye", "sight", "vision", "strain", "glasses", "specs", "booklight",
                          "kindle",
                          "electric", "electricity", "power cut", "wiring", "night light",
                          "darkroom", "outside",
                          # and the one darkness that is not a room: "how do i drive in the dark"
                          # was explained as an expression, while cars.py has the headlights
                          # answer. A road at night is the literal dark.
                          "a car", "my car", "the car", "cars", "driving", "drive", "driver",
                          "headlights", "headlight",
                          "dipped beam", "full beam", "main beam", "road", "roads", "motorway",
                          "windscreen", "behind the wheel", "oncoming", "kerb",
                          # and a frightened child is a literal dark too: "he says he sees things
                          # in the dark" was explained as an expression instead of answered
                          "sees things", "he sees", "she sees", "scared", "afraid", "frightened",
                          "terrified", "my son", "my daughter", "child", "children", "kid",
                          "kids", "toddler", "bedtime", "nightmare", "nightmares"),
    "snowed under": ("roads", "gritter", "forecast", "slippery", "ice", "school closed",
                     "driveway", "pavement", "planes", "flights"),
    "an arm and a leg": ("broken", "break", "fracture", "fractured", "injury", "injured", "cast",
                         "sling", "sore", "ache", "aching", "numb", "physio", "x ray", "crutches"),
    "under the weather": ("forecast", "rain", "raining", "storm", "wind", "met office", "sunny",
                          "weekend weather", "tomorrow weather"),
    "tip of my tongue": ("ulcer", "ulcers", "mouth", "taste", "tasting", "bitten", "bite", "sore",
                         "throat", "dentist"),
    "ball is in your court": ("tennis", "badminton", "squash", "netball", "racket", "racquet",
                              "net", "court hire", "coach"),
    "break the ice": ("windscreen", "windscreens", "drive", "driveway", "pavement", "grit",
                      "de icer", "deicer", "freezer", "frost", "roads", "car", "scraper",
                      "puddles", "slippery"),
    "beating around the bush": ("garden", "hedge", "hedges", "trim", "trimming",
                                "prune", "pruning", "lawn", "mower"),
    "let the cat out of the bag": ("vet", "vets", "litter", "kitten", "kittens", "puss", "pet",
                                   "carrier", "scratching", "purring"),
    "once in a blue moon": ("sky", "astronomy", "telescope", "eclipse", "planet", "stargazing",
                            "full moon", "lunar"),
    "on the same page": ("book", "books", "notebook", "printer", "printing", "binder", "printer",
                         "kindle", "novel"),
    "going round in circles": ("roundabout", "roundabouts", "satnav", "driving", "round trip",
                               "washing machine", "spin", "tumble dryer"),
    "head above water": ("swim", "swimming", "swimmer", "pool", "bath", "drowning", "lifeguard",
                         "wetsuit"),
    "bite off more than you can chew": ("swallow", "swallowing", "choking", "dentist", "tooth",
                                        "teeth", "denture", "puree", "soft diet"),
    "get something off my chest": ("cough", "coughing", "breathing", "breathless", "wheeze",
                                   "palpitations", "tightness", "rib", "ribs"),
    "the cold shoulder": ("frozen", "frozen shoulder", "stiff", "stiffness", "painful", "ache",
                          "achey", "achy", "physio", "sling", "rotator"),
    "hands full": ("bags", "shopping", "carrying", "lugging", "arms full", "basket", "trolley",
                   "pushchair", "pram"),
    "sleep on it": ("mattress", "mattresses", "sofa", "sofa bed", "floor", "pillow", "pillows",
                    "topper", "bed", "beds", "bedding", "cot", "camping", "sleeping bag",
                    "sprung", "firm", "back pain"),
    "clear my head": ("headache", "headaches", "migraine", "migraines", "painkiller",
                      "painkillers", "paracetamol", "ibuprofen", "sore head", "concussion",
                      "splitting"),
    "put my finger on it": ("splinter", "cut", "cuts", "thumb", "nail", "bruise", "burn", "sore",
                            "swollen", "blister"),
    "back to square one": ("monopoly", "dice", "board game", "snakes and ladders", "chess"),
    "the last straw": ("drink", "drinks", "cocktail", "milkshake", "smoothie", "reusable",
                       "paper", "plastic", "sip"),
    "cut corners": ("wall", "walls", "saw", "sawing", "skirting", "tile", "tiles", "tiling",
                    "carpet", "laminate", "worktop", "jigsaw"),
    "speak too soon": (),
    "best of both worlds": (),
    "hit the nail on the head": ("hammer", "hammers", "plaster", "drill", "stud", "studs", "wall",
                                 "walls", "shelf", "shelves", "panel", "panels", "rawplug",
                                 "rawlplug", "bracket", "joist"),
    "jump the gun": ("pistol", "starter", "starting pistol", "race", "athletics", "racestart",
                     "cannon", "sprint"),
    "burning the candle at both ends": ("wick", "wax", "flame", "scented", "scent", "tealight",
                                        "snuffer", "tallow"),
    "bite the bullet": ("ammunition", "shooting", "rifle", "revolver", "magazine", "firing",
                        "army", "range"),
    "sitting on the fence": ("garden fence", "fence panel", "fence panels", "paint", "stain",
                             "creosote", "panel", "panels", "post", "posts", "trellis"),
    "on the ball": ("football", "tennis", "cricket", "rugby", "netball", "basketball", "bounce",
                    "bouncing", "catch", "throw", "keeper", "goalkeeper", "pitch", "match"),
    "ring a bell": ("doorbell", "doorbells", "church", "bike", "bicycle", "chime",
                    "handbell", "bell tower", "wireless doorbell"),
    "barking up the wrong tree": ("dog", "dogs", "neighbour", "neighbours", "vet",
                                  "howling", "puppy", "kennel"),
    "that ship has sailed": ("ferry", "ferries", "cruise", "cruises", "harbour", "port",
                             "boarding", "departure", "itinerary"),
    "water under the bridge": ("river", "rivers", "flood", "flooded", "flooding", "canal",
                               "damp", "leak", "leaking", "water level"),
    "pulling my hair out": ("thinning", "bald", "balding", "scalp", "hairdresser", "conditioner",
                            "haircut", "hayley", "shampoo", "frizz", "dandruff"),
    "up in the air": ("flight", "flights", "plane", "planes", "airport", "airline", "luggage",
                      "boarding", "takeoff", "runway"),
    "grey area": ("paint", "painting", "painted", "decorating", "patio", "grout", "shade",
                  "colour scheme", "colour scheme"),
    "play it by ear": ("earache", "infection", "ear infection",
                       "hearing", "wax", "buds", "earphones", "earplugs", "tinnitus",
                       "perforated"),
    "cutting it fine": ("hair", "haircut", "hedge", "lawn", "cheese", "slicing", "chop", "chops",
                        "knife", "chopping"),
    "keep me in the loop": ("knitting", "yarn", "knit", "crochet", "belt loop", "stitch",
                            "stitches", "needles"),
    "the bigger picture": ("frame", "frames", "picture frame", "wall", "print", "prints",
                           "poster", "hang", "mount", "canvas"),
    "run of the mill": ("flour", "grain", "watermill", "windmill", "grind", "bread"),
    "the ball is rolling": ("bowling", "football", "tennis", "cricket", "netball", "basketball",
                            "pitch", "match", "kickabout"),
    "cant get my head round it": ("scalp", "headache", "helmet", "hat", "haircut", "dizzy",
                                  "sore head"),
    "back on track": ("train", "trains", "railway", "rail", "platform", "timetable", "tram",
                      "bus times", "train times", "season ticket"),
    "blow off steam": ("iron", "ironing", "steamer", "kettle", "pressure cooker", "boiler",
                       "radiator", "valve"),
    "on the mend": ("stitch", "stitches", "sew", "sewing", "darning", "tailor", "cobbler",
                    "hem", "seam"),
    "pinch of salt": ("teaspoon", "teaspoons", "tablespoon", "recipe", "seasoning", "stock cube",
                      "bake", "baking"),
    "see eye to eye": ("glasses", "specs", "eyesight", "optician", "screen", "dry eye", "sight",
                       "blurry"),
}


def _slug(phrase):
    return "-".join("".join(ch if ch.isalnum() else " " for ch in phrase).split())


# An idiom is language, and a line that is actually a request for the thing keeps the thing:
# "a piece of cake recipe" was answered with what the expression means, and the sponge cake row
# beside it had the recipe. The words here are a request for the thing itself.
_NOT_THE_EXPRESSION = (
    "recipe", "recipes", "bake", "baking", "baked", "cook", "cooking", "oven", "flour",
    "sponge", "cake tin", "icing", "buttercream", "how long in the", "how do i make",
    "how do i cook", "how do i bake", "make a cake", "make one", "calories", "ingredients",
    # The same request in the other wordings people type, because "how do you make a cup of tea"
    # and "how to make one" were both answered with what the expression means: the first never
    # named a way of making anything the list knew, and the second only said "one".
    "how do you make", "how do u make", "how can i make", "how to make", "how to cook",
    "how to bake", "how would i make", "how do i get one made", "recipe for",
    # A line asking for the thing is asking for the thing, whatever noun the expression is made
    # of: "can i have a piece of cake" was told what the expression means, and so was "can i get
    # a cup of tea". The idiom is a statement about something, so it never opens with an ask.
    "can i have", "can i get", "could i have", "may i have", "i want a", "i want some",
    "id like a", "i'd like a", "one please", "a slice of", "slices of", "how much is",
    "how much are", "how much does", "where can i buy", "buy a", "buy some", "order a",
    # A line that says a body hurts is about the body, whatever expression it also uses: "my ear
    # hurts when i play it by ear" is an earache, not a figure of speech.
    "hurts", "hurting", "sore", "soreness", "painful", "aches", "aching", "achy", "swollen",
    "itching", "itchy", "bleeding", "rash",
)


def _idiom(row):
    """One idiom: the phrase in both key groups, so it scores six and beats a body row."""
    phrase, also, said = row[0], row[1], row[2]
    words = (phrase,) + tuple(one for one in also if one != phrase)
    # A row may name its own keep-out words as well: the house of each expression ("cups a day"
    # for a cup of tea, "kettle" for hot water) is what took the line before this row existed.
    avoid = (_NOT_THE_EXPRESSION + _LITERAL_NEIGHBOURS.get(phrase, ())
             + (row[3] if len(row) > 3 else ()))
    # The phrase in three groups, so it counts three times: two groups tie with the row that
    # caught two of the expression's words ("came out" and "blue" for the laundry card) and the
    # earlier module wins a tie, which is how "it came out of the blue" stayed a colour run.
    return entry("idiom-" + _slug(phrase), (words, words, words), said, avoid=avoid, bias=1)


ENTRIES = [_idiom(row) for row in _IDIOMS]
