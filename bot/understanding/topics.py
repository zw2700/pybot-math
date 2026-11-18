"""What the line is about: the topic, the things it names, and the numbers in it.

Data first: every topic is a small vocabulary of distinctive words ("strong"), ordinary words
("weak") and short phrases. A match scores 2 for a strong word, 3 for a phrase and 1 for a
weak word, so a distinctive word beats a generic one, and a line only gets a topic when
something in it really points that way. Ties go to the topic mentioned last, because people
end a line with what they actually want.

Entities come from what the line names: capitalised names ("Lisbon", "Gone Girl"), the people
it mentions ("my daughter"), quoted titles, and the everyday things in the vocabulary above.
Numbers come with their unit when the line gives one ("2kg", "20 minutes", "15%").

The understanding lane owns this file; extend a vocabulary rather than special-casing a line.
"""
import re

from . import lexicon
from .body import A_GUT_ONLY
from .kinds import ADDRESS_WORDS, VERDICT_NOUNS, _asks_back, a_bad_verdict, small_talk_only
from .normalize import LEXICON as COMMON_WORDS
from .normalize import background_positions, reason_positions
from . import normalize

# Distinctive words: seeing one is strong evidence for the topic.
STRONG = {
    # The dishes and kit the deck asks about that had no word here: muffins, custard,
    # flapjacks, popcorn, brownies, tzatziki and a wok are all cooking questions, and
    # each of those lines read as no topic at all.
    "cooking": """cook cooking recipe recipes bake baking boiled boil fry frying roast roasted
        pudding puddings bbq
        grill simmer oven hob pan pot saucepan whisk knead dough batter marinade seasoning
        chop chopped chopped stir fry leftover leftovers sourdough pastry cake cupcakes
        biscuits bread pizza pasta curry soup stew rice risotto noodles sauce gravy stuffing
        roast scrambled poached omelette pancake pancakes lasagne lasagna meatballs
        undercooked overcooked sticky mushy crispy seasoning vegan vegetarian cheese
        dairy gluten lactose nut soya soy wheat
        cheeses chicken beef pork lamb mince bacon sausages ham fish salmon tuna prawns
        potato potatoes tomato tomatoes onion onions garlic ginger carrot carrots
        cabbage leeks cauliflowers swede peas celery cucumber lettuce beetroot sprouts pepper
        peppers mushroom mushrooms spinach courgette courgettes broccoli beans lentils
        chickpeas pasta spaghetti noodles rice flour sugar butter egg eggs milk cream
        lemon lemons lime limes orange herbs basil thyme rosemary parsley coriander cumin
        paprika cinnamon vanilla honey mustard mayonnaise yoghurt oil vinegar stock
        casserole tray tin whisk blender frying baking grill saucepan saucepan dish
        defrost thaw preheat simmering frying boiling recipes portions portion serving
        brine brining deseed deseeded meringue meringues pavlova guacamole milkshake
        milkshakes melon melons burrito burritos
        refreeze cabbage cauliflower kale lettuce sprouts peas veggie veggies pie quiche
        shortbread sponge scones icing frosting buttercream jam pesto hummus couscous halloumi
        buttermilk pudding puddings bolognese bol spag chilli chips mash loaf yeast
        parboil thicken reheat bland soggy rubbery watery steak chops breast thighs burgers meat
 tablespoon dessertspoon rinse tinned muffins muffin custard flapjacks flapjack popcorn cheesecake brownies brownie
        caramel tzatziki wok jelly aioli clams crumble meringue sorbet coleslaw
        burgers pineapple oats
 turkey knives cheddar quinoa scales sweetcorn mussels burger chinese indian grainy""",
    "food-and-drink": """eat eating food meal breakfast lunch dinner snack snacks drink drinking
        supper brunch dessert pud afters nibbles elevenses brekkie brekky sarnie
        butty cuppa takeout nosh chow kebab chippy munchies bap sanger
        coffee tea water juice wine beer sugar salt pepper cheese butter milk yogurt cream
        vegan vegetarian gluten allergy allergic caffeine decaf fizzy chocolate crisps
        takeaway restaurant menu hungry thirsty tasty delicious bread toast sandwiches
        sandwich cereal porridge yoghurt smoothie chocolate crisps nuts fruit apple apples
        banana bananas orange strawberries berries salad salad dressing mouldy moldy
 leftovers reheating leftovers portions
        ripe granola""",
    # A cold is named by the part that is blocked or runny, but only where a symptom word says
    # so: "runny" is a yolk and a honey, "stuffy" is a room, and an "ear" is an ear of corn, so
    # those three words are in the phrases below instead of here.
    # The body words the deck's health lines use and this list did not have, each about a
    # person's health and nothing else: "should i get my mole checked", "my hayfever is
    # bad", "the inhaler is empty", "my toenails have gone yellow", "is it colic".
    "health": """doctor gp hospital nurse pharmacy medicine tablet tablets pill pills symptom
        symptoms pain ache ill illness sick unwell fever temperature cold flu cough sneeze
        headache headaches migraine throat sore throat bleeding bleed cut burn burnt bruise
        infection antibiotics vaccine vaccination allergy allergic dizziness dizzy nausea
        blood pressure appointment clinic injury prescription eyes eye vision headache
        migraines dentist dental toothache teeth stroke numb numbness slurred
        seizure fainted fainting sprain sprained swelling swollen blister blisters
        sliced rash itchy itch vomiting vomit puking puke puked barf barfing diarrhoea constipation
        heartburn indigestion reflux
        cramps cramp bloated congestion earache ankle wrist elbow shoulder knee hip
        thumb finger fingers toe toes spine joint tendon ligament stomach calpol nurofen
        ibuprofen
        paracetamol painkiller painkillers cyst infected hangover hangovers
        nostrils nostril sinus sinuses sniffles sniffly stinging stings stung hoarse
        shivery chills queasy laryngitis tonsils wheezy croaky phlegmy smoking braces
        cholesterol heal healing snacking aching aches hurting nails toothbrush fibre
        fasting rundown mole moles acne hayfever inhaler inhalers colic palpitations antidepressants
        antidepressant dandruff floss plaque smear nits verruca verrucas wart warts
 cystitis menopause measles mumps chickenpox tonsillitis earache toenail
        toenails adhd autism dyslexia ocd ptsd sunscreen aftersun blistering
        pregnancy vitamin limping""",
    "fitness": """run running jog jogging gym workout exercise exercises stretch stretching
        training train fitness muscle muscles cardio weights lifting squat squats push-ups
 plank cycling swim swimming yoga pilates marathon 10k 5k steps calories toned
        insoles reps pace sets""",
    "sleep": """sleep sleeping slept insomnia bedtime nap naps wake waking woke tired exhausted
 mattress pillow duvet toddler wakes snore snoring dreams nightmare melatonin""",
    # The money words the deck uses that were missing: a pension question says "isa" or
    # "retire", a phone contract asks about "apr", a fine about "bailiffs", and those
    # lines read as no topic at all.
    "money": """money bank savings save saving budget budgeting salary wage wages pay paid
        loan loans mortgage rent debt debts credit debit card overdraft pension
        invest investing insurance tax taxes bills bill invoice receipt refund expensive
        cheap afford spending spent pound pounds euro euros dollar dollars cash atm council
        owes owed supplier payday payment payments doubled income lease vat switching
 deposit skint overcharging overcharged isa retire retired retirement subscriptions allowance overdrawn bailiff bailiffs
        dividend dividends apr payslip payslips annuity
benefit declare hmrc""",
    "work": """job jobs work working boss manager colleague colleagues office interview cv
        resume salary promotion review meeting meetings deadline project team hire hiring
        fired quit resign resignation contract shift shifts overtime coworker workplace
        conference presentation badge rota roster timesheet timesheets appraisal
 payslip warehouse supervisor defensive
        employer reference probation earlies sacked staff published""",
    "school-and-study": """school exam exams revise revising revision study studying homework
        teacher class lesson lessons term semester university college student grades grade
        test tests essays essay coursework dissertation notebook learn learning
        spelling vocabulary subject tutor a-level a-levels alevel alevels gcse
        gcses apprenticeship apprenticeships lecture lectures seminar
 seminars memorise memorising memorised cram cramming timetable
        uni squared levels phd ucas factorise accountant thesis courses maintenance equations lab""",
    "science": """science scientific physics chemistry biology atoms molecules gravity energy
        evolution photosynthesis oxygen carbon climate vaccines virus bacteria cells species
        experiment theory hypothesis dna planets jupiter saturn mars venus mercury
 orbit orbits seasons solar astronomy telescope moon moons
        tan planet thunder lava reflect blink shiver freckles digestion conductor insulator galaxy skyscrapers berry""",
    # The people and battles history questions are about - "who was genghis khan", "what
    # did darwin discover", "the battle of waterloo" - read as no topic at all.
    "history": """history historical century ancient empire revolution war wars king queen
        pharaoh pyramids roman romans greeks medieval victorian industrial
 archaeology civilisation civilization darwin einstein freud waterloo tsar lenin bismarck attila napoleon
        boleyn tudor tudors victorians aztec aztecs inca vikings
        invented britain blitz hitler marx antoinette curie crusades""",
    "geography-and-travel": """travel travelling traveling trip holiday holidays flight fly
        flying airport boarding plane train station passport luggage packing pack suitcase hotel
        booking itinerary visa abroad city countries country capital jet lag jetlag map
 tour tourist sightseeing beach mountains island abroad drive driving
        spain rome cornwall lisbon ferry edinburgh paris portugal london croatia coast naples amalfi airline cabin metro mexico heathrow prague pompeii benidorm""",
    "technology": """phone laptop computer tablet screen keyboard battery charger wifi wi-fi
        internet email app apps website software password passwords download upload update
        install printer router bluetooth notification notifications file files folder backup
        virus hacking privacy screenshot log login account data iphone android mac macbook
        photos delete uninstall restart spam scam texting pointer icloud zoom
        broadband headphones earphones robocall robocalls landline
        
        ipad signal earbuds pdf blurry monitor sim print facebook ssd speaker usb spreadsheet vlookup teams google cloud youtube photograph""",
    # The house words the deck uses that were missing: a wardrobe, a patio, a toaster, a
    # ladder, a tenancy agreement and something chipped or rusty are house questions.
    "home-and-diy": """house flat apartment kitchen bathroom bedroom ceiling wall walls floor
        carpet paint painting diy drill hammer screw screws shelf cupboard radiator boiler
        sink tap drain drains mould mold damp leak leaking plumber electrician fuse
        furniture sofa bed washing machine dishwasher hoover dyson vacuum suction filter
        ironing ironed curtain curtains
        moving move removal landlord toilet flush flushing grout tile tiles shower smoke alarm
        carbon monoxide draught draughts door doors window windows lock locks thermostat
        heating freezer fridge kettle draft loft gutter guttering locksmith doorbell
        burner burners stove stoves fireplace chimney flue hearth worktop worktops dryer tumble
        jeans shirt shirts jumper towels stain stains condensation limescale kettling extractor
 radiators gutters fence plasterboard drum loader wooden spilt pipes
 wallpaper wallpapering decking wardrobe wardrobes patio toaster cistern ladder ladders tenancy chipped varnish
        blinds cutlery crockery doormat skirting tiling umbrellas knit knitted scarf
        recycling rug bins bedding softener stool""",
    # The plants people keep in the house, and the jobs that are only ever done to a plant. A
    # plant is not dinner: "how often do i water my monstera" is not a drink, and "when do i
    # harvest potatoes" is not a recipe, so the plant and the job it needs are named here rather
    # than left to the words they share with food (water, potatoes, onions).
    "garden-and-plants": """garden gardening plant plants planting grow growing seed seeds
        seedling seedlings soil compost weed weeds weeding watering pruning prune lawn grass
        flower flowers bulbs tulip tulips basil tomato tomatoes balcony allotment greenhouse
        pots shrubs shrub hedge hedges turf mower rake hoe mulch repot repotting
        deadhead deadheading cuttings propagate houseplant houseplants monstera orchid orchids
        cactus cacti succulent succulents fern ferns lily lilies aloe lavender hydrangea
        daffodil daffodils sunflower sunflowers composted harvest harvesting harvested
        sow sows sowing sowed slug slugs snail snails
        roses moss lawnmower vase bonsai bamboo baskets basket chit""",
    "pets": """pet pets dog dogs puppy cat cats kitten kittens vet vet rabbit rabbits hamster
        goldfish fish tank lead leash walkies dog lead kitten litter kennel rescue adopted
 adopt purring barking bark treats barks fleas collar paw poisonous
        labrador greyhound guinea whippet spaniel pug pig neutering""",
    "family-and-parenting": """child children kid kids baby toddler toddler son daughter
        parent parents mum mom mother dad father husband wife partner family babies nappy nappies
        pram nursery babysit twins birthday party school run parenting newborn
        toddler toddlers potty weaning teething playgroup playschool childminder
        gran grans sister sisters brother brothers sibling siblings grandma grandmas granny grandad
        grandpa grandparents grandmother grandfather grandson granddaughter grandchild
        grandchildren nan nana nanna nephew nephews niece nieces cousin cousins aunt aunty
        auntie uncle uncles stepmother stepfather stepmum stepdad stepson stepdaughter
        stepchild stepchildren stepsister stepbrother half-brother half-sister in-laws
 relatives ex exes
        teen invitations godparent babysitting hymns boys""",
    "friends-and-relationships": """friend friends friendship partner boyfriend girlfriend
        wife husband marry married wedding dating date anniversary argument argued row
        apology apologise apologize forgive trust relationship relationships breakup
        neighbour neighbours colleague flatmate housemate ex exes
 divorce divorced separation separated cheat cheated cheating affair affairs""",
    "shopping": """buy buying bought shop shopping store price prices cheap expensive
        sale discount refund warranty returns second-hand reviews review order
 delivery parcel stock size sizes brand
 moisturiser housewarming bleaching""",
    "cars": """car cars tyre tyres tire tires mot brakes brake braking engine engines clutch
        gearbox windscreen windshield wipers wiper headlights headlight bonnet coolant
        dipstick tread puncture petrol diesel mpg speedometer dashboard mechanic garage
 servicing motoring motorway alloy alloys demist
        ebike pcn bumper pedal penalty motor""",
    "entertainment": """film films movie movies watch watching series tv television show
        shows netflix book books novel novels read reading podcast podcasts music song songs
        album band concert theatre theatre game games play console chess draughts
        backgammon scrabble monopoly jigsaw jigsaws
        documentary comedy comedy episode episodes season author writer actor actress
 streaming
 chords amp iplayer succession western jazz""",
    "sport": """sport sports football footy footie soccer rugby cricket tennis golf match
        matches team
        league cup goal goals offside wicket wickets innings coach coaching training
        bowling yorker googly bouncer crease stumps batsman batsmen wicketkeeper keeper
        olympics tennis badminton swimming race racing formula tennis wimbledon
 player players referee darts snooker hockey netball volleyball athletics
        basketball baseball softball handball squash boxing marathon marathons triathlon
        skiing surfing rowing bowls
        hamstrings""",
    # The writing questions the deck asks that had no word here: a plural, a semicolon, a
    # colon, a voicemail greeting, a thesaurus and a dictionary.
    "language-and-writing": """grammar spelling word words writing wrote write sentence
        sentences essay paragraph punctuation apostrophe comma vocabulary phrase
        wording translate translation english language meaning affect effect fewer less
 email draft letter poem speech bio caption congratulations plural plurals semicolon semicolons colon voicemail thesaurus dictionary mumbling
        monotone
        spell fluent exclamation bullet rewrite""",
    "feelings": """feel feeling felt emotional lonely alone sad unhappy upset anxious worried
        nervous stressed stress overwhelmed depressed crying tears heartbroken gutted angry
        annoyed frustrated guilty ashamed jealous embarrassed happy excited relieved proud
 grateful mood feelings grief grieving funeral devastated
        coping knots churning""",
    # "coffee", "tea", "weekend" and "plans" are not here: a drink is food and drink, and a
    # weekend is the thing a line plans, so they led food and travel lines into small talk
    # ("whats a good tea for a cold", "planning a weekend away").
    "small-talk": """jigsaw chatty catch chat catch-up catchup rain raining sunny freezing
 chilly warm cold weather bye lovely
 easter""",
    "opinions": """opinion favourite favorite prefer rather
 worth overrated underrated agree disagree""",
    "creative": """poem poetry story stories joke jokes nickname creative
 write writing speech rhyme character plot lyrics slogan tagline design
        limerick haiku rap""",
    # The words maths questions name: a numerator and a denominator, a perimeter, a
    # theorem, a protractor, a diameter, and the shapes people ask about.
    "maths-and-numbers": """percent percentage maths math numbers calculate sum total average
        divide multiply minus plus equation fraction fractions decimals half double triple
 algebra geometry numerator denominator perimeter theorem pythagoras protractor diameter radius
        isosceles quadrilateral quadrilaterals parallelogram rhombus trapezium cuboid
        triangles triangle probability median""",
    "nature-and-weather": """weather rain raining snow snowing storm thunderstorm lightning
        wind windy sunny sunshine clouds cloudy fog foggy freezing frost heatwave forecast
        autumn spring winter summer birds heron robin sparrow wildlife trees nature
 river sea ocean beach stars moon
        animal whale cheetah penguins penguin""",
    "about-the-bot": """chatbot bot robot artificial intelligence human person alive feelings
 remember yourself yourself
        version chatgpt soul""",
}

# The parts of a home and the things kept in it that these lists did not carry, so a line that
# named only one of them named no thing at all and the line after it had nothing to lean on:
# "my mum is hanging pictures" / "she wants them level" got the echo "Got it - she wants them
# level" instead of the fixing advice, and "i want to hang a picture" / "how high" carried nothing
# but the ask. Named as things, these words reach the cards already keyed on them.
# Kept to what people ask about as a thing and out of the words with a life of their own: "chest"
# is part of the body, "landing" is what a plane does, "bath" is a city - and "shed" is what
# hair does, so that one is left out: naming it pulled a shed-delivery chat onto the hair-loss
# card, because "shedding" is a key of that card. Note that words in these vocabularies are also
# the everyday things a line can name (`THINGS` below), so prose written inside a string here is
# read as vocabulary. The list is added in a statement of its own so that an edit here cannot
# collide with the words other lanes add to the literal above.
STRONG["home-and-diy"] += """
        attic cellar mirror mirrors picture pictures frame frames lamp lamps
        socket sockets plug plugs wiring hook hooks armchair armchairs"""


# Ordinary words that only point at a topic together with something else.
WEAK = {
    "cooking": "make made time minutes hours temperature heat hot plate bowl spoon knife "
               "cookies "
               "dinner tonight lunch breakfast tastes frozen handful freeze",
    "food-and-drink": "like dislike sweet sour spicy fresh cold hot bottle cup glass",
    "health": "feel better worse days week rest sleep tired checked",
    "fitness": "minute minutes week day morning evening body",
    "sleep": "night morning bed room",
    "money": "much cost worth pay month year percent save owe minimum",
    "work": "day week hours people ask",
    "school-and-study": "help practice remember book week day",
    "science": "why works explain",
    "history": "time people built",
    "geography-and-travel": "go going place days week month",
    "technology": "work working broken fix new old connect storage charging broadband",
    "home-and-diy": "room house fix clean door doors window windows repairing replace serviced "
                    "bleach smells smelling dripping banging rattling humming stinks stinking "
                    "squeaking leather patch",
    "garden-and-plants": "water green yellow leaves grow",
    "pets": "feed cat dog walk scratching",
    "family-and-parenting": "home help age",
    "friends-and-relationships": "talk said told mate mates pal pals buddy bloke fella",
    "shopping": "need new look",
    "cars": "start starting noise noisy sound light warning fix cost worth check insurance",
    "entertainment": "good funny watch read listen",
    "sport": "play watch season",
    "language-and-writing": "say write help mean",
    "feelings": "really very today week",
    "small-talk": "today hello hi tomorrow day week morning evening busy tired",
    "opinions": "think really",
    "creative": "help idea",
    "maths-and-numbers": "how many long",
    "nature-and-weather": "today season year",
    "about-the-bot": "you your help",
}

# Every word the topics name a thing by, in one place: the reading repairs a thing typed a
# letter short against this list ("my fidge is broken", "how do i check my raiator"). It is the
# strongest vocabulary the engine has for things people ask about, and a word that is not a real
# word of the language cannot be confused with much once this list is the other side.
THING_WORDS = frozenset(
    word for words in list(STRONG.values()) + list(WEAK.values()) for word in words.split())
normalize.learn_thing_words(THING_WORDS)

# "work out" is two different things: the exercise, and the sums a line does ("work out my
# hourly rate", "work out 15% of 80", "work out how many tiles"). Only the exercise is the
# fitness phrase, so a sums-shaped phrase is not evidence for fitness.
# What a line that is working something out goes on to name: a sum, an amount, or a choice.
# The asking words and amounts come first, then a determiner: "work out the area of a room",
# "work out my notice period", "work out which contract is cheaper" are all sums or a choice,
# and the thing they name is what the topic comes from.
SUMS_AFTER = frozenset("""how what which if whether when where why much many long cost costs
    budget rate rates salary pay bill bills price prices percentage percent total average
    amount area size volume length distance mpg miles tax taxes loan loans owe owes
    spend spending split share calories tiles paint dose timer timers worth number numbers
    cheaper cheapest
    the my our your his her their its this that these those""".split())
# The normaliser spells numbers out, so "work out 3 divided by 4" arrives as "three divided by
# four" and a digit test never fires: the number words are what says it is a sum.
NUMBER_WORDS = frozenset("""one two three four five six seven eight nine ten eleven twelve
    thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty
    sixty seventy eighty ninety hundred thousand million billion half quarter""".split())
# ... and what says it is the exercise: a place, a frequency, a body it is done to, or how
# hard. These are read first, so "work out at the gym" and "work out my arms" stay the gym.
# The amounts a working-out is about, so the topic is what the sum is for.
SUM_MONEY = frozenset("""pay paid salary wage wages tax taxes bill bills budget price prices
    cost costs rate hourly income rent loan loans mortgage overtime notice pension fee fees
    profit loss interest entitlement entitlements cheaper cheapest owe owes
    debt debts refund refunds save savings total""".split())
EXERCISE_AFTER = frozenset("""gym home more often regularly times sets reps cardio weights
    running fit fitness training body muscles arms arm legs leg abs back chest shoulders
    glutes core biceps triceps thighs butt hard lightly daily weekly workout session
    day days week weeks once twice
    morning mornings evening evenings night afternoon today tomorrow""".split())
# ... and the thing a working-out is measured in, which can sit anywhere in the line: "work out
# my one rep max", "how do i work out my target heart rate", "work out how much protein i
# need". The exercise words above are read close to the phrase; these are read across the
# whole line, because the training noun is often the last thing named. They are the measures
# and the scaled things, not the everyday body words ("back", "core"), which would make
# "work out when i get my money back" the gym.
EXERCISE_NOUNS = frozenset("""heart pulse zone calorie calories macro macros protein
    rep reps weight weights pace treadmill lifting lift sets bodyfat bmi 1rm
    km kilometre kilometres mile miles""".split())


def _work_out_sums(norm):
    """Where "work out" is arithmetic or deciding, not the job and not the exercise.

    "work out a percentage", "work out my hourly rate", "work out how much i owe" and
    "work out if the loan is worth it" are sums, and there the word "work" is no evidence for
    the work topic either. "work out at home", "work out three times a week" and "work out
    more" are the exercise, and those keep both the word and the fitness phrase.
    """
    hits = set()
    training = any(word in EXERCISE_NOUNS for word in norm)
    for index, word in enumerate(norm):
        if word not in ("work", "works", "working", "worked") or index + 1 >= len(norm):
            continue
        if norm[index + 1] != "out":
            continue
        after = norm[index + 2:index + 8]
        # "work out twelve times seven" is a sum, and the exercise "three times a week" is
        # not, so a number on both sides of "times" is what separates them.
        if len(after) >= 3 and after[0] in NUMBER_WORDS and after[1] == "times" \
                and after[2] in NUMBER_WORDS:
            hits.add(index)
            continue
        if training or any(word in EXERCISE_AFTER for word in after[:3]):
            continue
        if any(word in SUMS_AFTER or word in NUMBER_WORDS for word in after) \
                or any(word.isdigit() for word in after):
            hits.add(index)
    return hits


# A topic word used in another sense, so that phrase is not evidence for this topic: "how does
# darts scoring work" is a how-it-works question, not the work topic. People end a line with
# what they want, so this only takes back the word, never the whole topic.
CANCELS = (
    (re.compile(r"\bhow (?:do|does|did|would|will|should) (?:[a-z]+ ){0,3}?work\b"), "work"),
    (re.compile(r"\bhow (?:it|they|this|that|these|those) works?\b"), "work"),
    (re.compile(r"\b(?:does|do|will|would|can|could) (?:it|that|this|they) work\b"), "work"),
    (re.compile(r"\bwhat makes (?:[a-z]+ ){0,3}?work\b"), "work"),
)
# What may follow the cancelled word and still leave the whole phrase: the end of the clause, a
# particle or preposition ("work like that", "work for us", "work out"), or a word that opens
# the next clause. Anything else is the word used as a noun in front of another noun, which is
# the job: "the work rota", "the work laptop", "the work appraisal".
CANCEL_AFTER = frozenset("""
    for with in on at to out up like if when as that this it than from about
    and or but so then though because
""".split())

# Phrases carry a topic on their own.
PHRASES = {
    "cooking": ("packed lunch", "packed lunches", "party food", "lunch box", "lunchbox",
                "how long should i cook", "how do i cook", "what can i make", "what can i cook",
                "main course", "cooking for", "i am cooking", "cook for", "easy dinner",
                "quick dinner", "quick meal", "use up",
                "birthday cake", "something to cook", "cook tonight", "meal for",
                # A meal named by name keeps the line on cooking even when the ask is about
                # buying: "what do i need to buy for a sunday roast" is a cooking question, and
                # the shopping entries have nothing for a roast.
                "sunday roast", "roast dinner for", "christmas dinner",
                # yorkshire on its own is the county, so the pudding is the two words
                "yorkshire pudding", "yorkshire puddings",
                # the pressure of the weather or blood pressure is not the cooker
                "pressure cooker", "slow cooker", "air fryer",
                "leftover", "meal idea", "meal ideas", "dinner idea", "dinner ideas",
                "something quick", "under cooked", "ice cream",
                # A board in a kitchen is a chopping board, not a box of games: "my chopping
                # board has gone black" was reading entertainment from the bare word, and the
                # topic it gave then held the kitchen out of the follow-up's search.
                "chopping board", "chopping boards", "cutting board", "cutting boards"),
    "food-and-drink": ("book a table", "a table for", "table for two", "table for four",
                       # "iron" as a bare word read home-and-diy (the appliance) and took every
                       # question about the nutrient with it: "what foods are high in iron" was a
                       # search suggestion and "how do i get more iron in my diet" was the
                       # weight-loss answer. The phrases that are really about the food keep the
                       # topic; the appliance and the creases keep the words ironing/ironed.
                       "high in iron", "iron rich", "rich in iron", "low in iron", "low iron",
                       "iron levels", "iron level", "iron deficiency", "deficient in iron",
                       "more iron", "iron in", "sources of iron", "getting enough iron",
                       "enough iron", "need iron", "anaemic", "anaemia", "anemia", "anemic",
                       "eat out", "go out for dinner", "too much coffee", "less coffee",
                       "ice cream",
                       "is it safe to eat", "out of date", "goes well with", "cheese board",
                       "graze board", "graze boards", "picky bits", "picky tea",
                       "main course", "use by date", "sell by date", "best before",
                       "past its date", "in season"),
    "health": ("see a doctor", "go to the doctor", "should i see a doctor", "sore throat",
               "root canal", "mole checked",
               # Being sick is said as a phrase more often than as a word: "i keep throwing up",
               # "she threw up twice" name no symptom on their own, because "throwing" and "up"
               # are ordinary words.
               # The pair is the sickness whatever comes after it, so "throwing up the window"
               # - how people say they opened it - reads health too. Nothing in the deck says
               # it and the same answer comes back either way; a list of the things a person
               # can open is not worth carrying in the reading for it.
               "throwing up", "throws up", "threw up", "thrown up", "want to throw up",
               "going to throw up", "gonna throw up",
               "high temperature", "blood pressure", "cut my finger", "feeling ill",
               "feel unwell", "get headaches", "have a headache", "my head hurts",
               "making me cry", "stopped bleeding", "wont stop bleeding",
               "signs of a stroke", "burnt my hand", "burnt myself", "burnt my arm",
               "burnt my finger",
               # a cold is said as a phrase more often than with a symptom word, and the
               # words that carry it ("runny", "stuffy", "ear") mean something else alone
               "coming down with", "going down with", "runny nose", "stuffy nose",
               "blocked nose", "bunged up", "bunged nose", "blocked ear", "blocked ears",
               "ear is blocked", "ears are blocked", "ear infection", "sore ears",
               "ringing in my ears", "ears are ringing", "stuffy head", "scratchy throat",
               "sinus infection",
               # "nose" and "bunged" alone are something else - the nose of a car, the plane's
               # nose, "i bunged the washing in" - so a nose is health only as a phrase
               "my nose is blocked", "my nose is running", "my nose is bunged",
               "my nose is stuffy", "nose bleed", "nose bleeds", "nosebleed",
               # "congested" describes a road as readily as a chest, so the chest is said
               "chest congestion", "my chest is congested", "congested chest",
               "nasal congestion", "sinus congestion", "congested nose",
               "im congested", "i am congested", "feel congested", "feeling congested",
               "really congested",
               # a mouth ulcer is health even said without a symptom word, and "ulcer" on
               # its own is a stomach or a leg, so the mouth is said as a phrase
               "mouth ulcer", "mouth ulcers", "ulcer in my mouth", "ulcers in my mouth",
               "ulcer on my tongue", "ulcer on my gum", "canker sore", "canker sores",
               # water is a drink and a pipe leak, so water in an ear is health only as a
               # phrase: "water trapped in my ear" was answered as a trap under the sink
               "water in my ear", "water in my ears", "water trapped in my ear",
               "water trapped in my ears", "water stuck in my ear", "water stuck in my ears",
               "water in my ear after swimming", "swimmers ear", "swimmer's ear",
               # A stomach that is upset is said as a phrase far more often than with a symptom
               # word, and every word in the phrase means something else alone: "the runs" is
               # running, "upset" is a mood, "dicky" is a bird and "trots" are steps. So
               # "i have an upset stomach" was read as a feeling ("what would make today a bit
               # easier") and "i keep running to the loo" as exercise. Each phrase is the two
               # or three words together, so running for the bus and an upset friend are left
               # exactly as they were.
               "upset stomach", "upset tummy", "upset belly", "upset guts",
               "bad guts", "bad belly", "dicky tummy", "dicky stomach",
               "dodgy tummy", "dodgy stomach", "tummy bug", "stomach bug", "sick bug",
               "the runs", "the trots", "the squits", "got the runs", "have the runs",
               "loose stools", "runny tummy", "runny bottom",
               "running to the loo", "running to the toilet", "runs to the loo",
               "runs to the toilet", "back and forth to the loo",
               "stomach is off", "tummy is off", "belly is off", "stomach is queasy",
               "tummy is queasy",
               "diarrhoea", "diarrhea", "sick with diarrhoea", "sick with diarrhea",
               # The complaint named as a whole, not by a body part and a word of pain: a
               # filling, a wisdom tooth, an ingrown nail, a sting off a plant, a bite off an
               # insect, hair coming out, a panic attack, acid coming up. Each is a phrase
               # because one half of it means something else alone - "filling" is a sandwich,
               # "insect" is in the garden, "hair" is the hairdresser's.
               "wisdom tooth", "wisdom teeth", "ingrown toenail", "ingrown nail",
               "ingrowing toenail", "ingrowing nail", "nail is ingrown",
               "nettle sting", "nettle stings", "stung by nettles", "insect bite",
               "insect bites", "insect sting", "bug bite", "bug bites", "hair loss",
               "losing my hair", "going bald", "panic attack", "panic attacks",
               "acid reflux", "acid indigestion", "athletes foot", "athlete's foot",
               "sweating too much", "excessive sweating", "night sweats",
               "heavy period", "period pain", "period pains", "period cramps",
               "on my period", "missed period", "late period", "irregular periods",
               "stop sweating", "sweat so much", "sweating a lot", "sweat a lot",
               "lump in my breast", "lump in my armpit", "lump in my neck",
               "lump under my skin", "swollen glands", "glands are up"),
    "fitness": ("out of breath", "get fit", "lose weight", "work out", "start running",
                "training for", "train for", "train hard", "lower back"),
    "sleep": ("get to sleep", "back to sleep", "wake up", "wakes up", "can not sleep",
              "cant sleep", "sleep through"),
    "money": ("save for", "how much should i save", "pay off", "stamp duty", "worth paying",
              "interest rate", "interest rates", "savings account", "the interest",
              "compound interest",
              "cut my bills", "energy bills", "energy bill", "electricity bill",
              "gas bill", "water bill", "small salary", "how should i budget"),
    "work": ("my boss", "my manager", "job interview", "my colleague", "teaching assistant",
             "performance review", "my team", "too much on my plate",
             # speaking to a room is the work of a talk, not a mood on its own
             "public speaking", "speaking in front of people", "speaking in front of an audience",
             "in front of an audience", "speaking to a room", "before a talk", "at a talk",
             "giving a talk", "give a talk", "nervous about my presentation"),
    "school-and-study": ("revise for", "exam in", "how do i revise", "learn vocabulary",
                         "struggling with", "get started on", "science project",
                         "school project", "for an exam", "a degree worth",
                         "degree still worth", "do a degree",
                         "a-level results", "do my a-levels", "my mocks",
                         "mock exam", "mock exams", "mocks in", "mocks next"),
    "science": ("how does it work", "why does", "why is the sky", "what is the difference between",
                "how do plants", "in a nutshell", "speed of light", "how many moons",
                "why is it hotter",
                # the body a question is about, so "how many bones in the human body" is
                # science and not a question about the bot
                "human body", "bones in the", "bones are in", "how many bones",
                # the seismic words are science only as an ask about the phenomenon: "i am
                # scared of earthquakes" is a fear, and "the volcano ash cancelled my flight"
                # is a travel line, so they are phrases rather than words
                "what causes an earthquake", "what causes earthquakes", "how do earthquakes",
                "why do earthquakes", "earthquake happen", "earthquakes happen",
                "how do tsunamis", "what causes a tsunami", "tsunami warning",
                "what causes a volcano", "how do volcanoes", "volcano erupt", "volcano erupts",
                "volcano erupted", "volcanoes erupt", "volcano erupting",
                "volcanoes work", "volcano work", "volcano project", "volcanoes project", "project on volcanoes",
                "project on volcano", "volcanic eruption"),
    "history": ("who built", "when did", "in a nutshell", "roman empire", "industrial revolution",
                # The names that are two words, and the term made of two ordinary ones: a
                # phrase in a STRONG block is only words, so "genghis" and "khan" would each
                # be history on their own, and so would "slave" and "trade".
                "slave trade", "genghis khan",
                # "china" is the crockery and the country: the wall is the country's, and the
                # word alone is left to the sentence (see COUNTRY_HOMOGRAPHS).
                "great wall of china", "ancient china",
                # "wall" and "sink" are ordinary nouns, so a line about a wall coming down or a
                # ship sinking read home-and-diy: the wall, the ship and the war are history only
                # as names. A phrase outranks the word, so these keep the subject. The name has to
                # be in the line: "the wall came down" is a garden wall as often as the Berlin one.
                "berlin wall", "the berlin wall", "cold war",
                "moon landing",
                # "titanic" and "tudor" name a film and a kind of house as well as the ship and
                # the dynasty, so they are history in the shapes that say which one: "i watched
                # titanic" is entertainment and "i live in a tudor cottage" is home-and-diy.
                "titanic sank", "titanic sink", "titanic sinking", "titanic wreck",
                "titanic iceberg", "the titanic hit", "when did the titanic",
                "how did the titanic", "why did the titanic",
                "the tudors", "tudor period", "tudor times", "tudor england"),
    "geography-and-travel": ("day trip", "jet lag", "shouldn miss", "don t miss",
                             "what should i see", "long flight", "car journey",
                             "capital of", "book a flight", "book a hotel",
                             "book a train", "book a room", "by coach", "a coach to",
                             "coach from", "coach station", "coach trip", "coach leaves",
                             # "train" is both the railway and the exercise, and the railway
                             # is the one people write about with a delay, a ticket or a
                             # platform in the line. Without these the exercise word decides
                             # it: "the train is cancelled" read as fitness.
                             "by train", "train ticket", "train tickets", "train station",
                             "train times", "train fare", "train fares", "catch the train",
                             "the next train", "the last train", "missed the train", "missed my train",
                             "the train to", "train to london", "train to leeds"),
    "technology": ("battery drains", "wont turn on", "wont start", "keeps dropping",
                   "improve the signal", "take a screenshot", "password manager", "group chat"),
    "home-and-diy": ("get rid of", "unblock", "bleed the radiator", "front door", "back door",
                     # the appliance and its creases, now that a bare "iron" is not home-and-diy
                     "clothes iron", "steam iron", "iron a shirt", "iron the shirt",
                     "iron my shirt", "iron a few shirts", "ironing board", "iron board",
                     # the appliance itself, in the shapes that name it rather than the mineral
                     "my iron", "the iron", "our iron", "iron is broken", "iron broke",
                     "iron has broken", "iron stopped", "iron wont heat", "iron is not heating",
                     "iron is leaking", "iron spits", "iron spitting", "never iron",
                     "never ironing", "hate ironing", "creases out of", "crease out of",
                     "get creases", "stop creases", "trousers creased", "iron the creases",
                     "heat pump", "heat pumps", "cold at the top",
                     # a fan on a desk is an appliance with dust in it, not an admirer
                     "desk fan", "desk fans", "ceiling fan", "ceiling fans",
                     "hot at the bottom", "get red wine out", "paint my", "second hand",
                     "do the dishes", "wash the dishes", "the dishes", "dishes are",
                     "the spring on", "spring broke", "spring has gone", "a new spring",
                     "the spring needs",
                     "smoke alarm", "wont flush", "won t flush", "cold air coming",
                     # A household pressure is the water's, not the blood's: the words that
                     # say which pressure it is sit next to it.
                     "water pressure", "low pressure", "pressure gauge",
                     "wood burner", "woodburner", "log burner", "log fire", "wood fire",
                     "burning stove", "wood stove", "fire place"),
    "garden-and-plants": ("turning yellow", "easy to grow", "when should i plant",

                          "plant bulbs", "on the balcony",
                          # A crop is not a recipe: the question is when to lift, sow or pick
                          # it, and the vegetable's own name is a cooking word.
                          "when do i harvest", "when should i harvest", "when can i harvest",
                          "when do i sow", "when should i sow", "when can i sow",
                          "when do i lift", "when should i lift", "ready to harvest",
                          "ready to lift"),
    "pets": ("pulls on the lead", "dangerous for dogs", "clean the tank", "getting a puppy",
             "getting a kitten", "rescue dog", "stopped eating", "has not eaten"),
    "family-and-parenting": ("starting school", "with kids", "for my son", "for my daughter",
                             # a small child is a person, not a piece of exercise kit: "is my 2
                             # year old ready for potty training" read fitness and sport off
                             # "training", so the phrase says what the line is about.
                             "potty training",
                             # the person a parent takes a baby to, named in full: people
                             # write "the hv", which the normaliser spells out for this
                             "health visitor", "health visitors", "my health visitor",
                             "my parents are visiting", "birthday party",
                             "watch the kids", "watching the kids", "watch my kids",
                             "to watch my kids", "to watch the kids", "to watch the children",
                             "someone to watch"),
    "friends-and-relationships": ("forgot my birthday", "make friends", "anniversary gift",
                                  "had an argument", "bring it up", "best friend",
                                  "on a date", "date night", "blind date", "first date",
                                  "going on a date", "a date with",
                                  # Only a phrase that is about the relationship itself carries
                                  # the subject. "my mate" names a person, not a question about
                                  # one: "my mate is coming for dinner, what should i cook" is a
                                  # cooking line that mentions a friend, and the weak words above
                                  # already say a friend is there when nothing else is named.
                                  "fell out with", "avoiding me", "stopped asking me out",
                                  "stopped speaking to me", "not speaking to me"),
    "shopping": ("worth it", "worth the money", "should i look for", "before buying",
                 "second-hand", "which one should i buy", "buying a car", "used car",
                 "worth paying", "good deal", "bad deal", "better deal", "a deal",
                 "the store", "at the store", "to the store", "in the store", "store was",
                 "store is", "which store", "store sells", "store open", "store closed",
                 "any store", "the shops",
                 "what specs", "how much should a decent"),
    "cars": ("jump start", "warning light", "engine light", "tyre pressure", "oil change",
             "break down", "broken down", "hard shoulder", "won t start", "wont start",
             "won t turn over", "new tyres", "car insurance", "road tax", "mot due",
             "mot fail", "failed its mot", "car tax"),
    "entertainment": ("harry potter", "what should i read", "what should i watch", "anything good",
                      "watch tv", "watch a film", "watch a movie", "watch a series",
                      "watching tv", "watch the match", "watching the match",
                      "something to watch", "anything to watch", "what can i watch",
                      "can i watch", "this book", "a book about", "book club", "which book",
                      "a book for", "what book", "good book", "need a book", "book to read",
                      "book recommendations", "recommend a book", "books for", "favourite book",
                      "favorite book", "to watch", "worth watching", "what to read",
                      "family night", "board game", "play station", "playstation",
                      "for my commute", "season ticket",
                      "season finale", "new season of", "next season of", "series finale"),
    "sport": ("offside rule", "world cup", "how does the game work", "my coach", "coached",
              "coaching", "the match", "match is on", "match tonight", "match day",
              "cricket match", "football match", "rugby match", "tennis match",
              "darts match", "boxing match",
              "this season",
              "next season", "pre-season"),
    "language-and-writing": ("difference between", "is it bad to say", "how do i word",
                             "without sounding rude", "can you help me word"),
    "feelings": ("i feel", "i am feeling", "been feeling", "feel like", "so stressed",
                 "so done", "done with today", "done with this week", "done with today",
                 "fed up", "had enough", "long day", "what a day", "tough day", "rough day",
                 "really lonely", "i am nervous", "nervous about", "i am worried",
                 "i am gutted", "i am upset", "let off steam", "miss my old",
                 # The judgement said as an absolute about their own record: "i get everything
                 # wrong", "i cant do anything right", "i always mess everything up". It names no
                 # feeling word, so the topic was left empty and every reader had to guess. Only
                 # the shapes with the person's own record in them: "everything went wrong with
                 # the cake" is about a cake, and "what is wrong with my boiler" is not this.
                 # The verb has to be in the phrase: "i listed everything wrong with the flat"
                 # and "how do i fix everything wrong in the kitchen" are about a flat and a
                 # kitchen, and they keep home-and-diy.
                 "get everything wrong", "gets everything wrong", "do everything wrong",
                 "did everything wrong", "doing everything wrong", "doing it all wrong",
                 "did it all wrong", "everything i do goes wrong", "everything i do is wrong",
                 "mess everything up", "messed everything up", "messing everything up",
                 "mess it all up", "messed it all up", "cant do anything right",
                 "can not do anything right", "never get anything right",
                 "never do anything right"),
    # "weekend" and "plans" are ordinary words ("planning a weekend away", "plans for the
    # extension"), so the weekend chat is a phrase, not either word on its own.
    # How-are-you said with a day or a week in it is the same small talk: "how was your day",
    # "hows your day been", "how have you been". None of these names a subject of its own, so
    # without them the carried subject decided the topic - "how long do i boil an egg" then
    # "how was your day" was read as a cooking line and answered with the keeping card for
    # boiled eggs. Only the *your* forms are here: "how was the day" and "how has your week
    # been at work" are about the world.
    "small-talk": ("how s your day", "how is your day", "how are you", "how is it going",
                   "nice to meet you", "what s up", "any plans", "plans for the weekend",
                   "up to this weekend", "this weekend", "weekend plans"),
    "opinions": ("what do you think", "do you think", "your favourite", "which do you prefer"),
    "creative": ("write a poem", "tell me a joke", "name for", "opening line"),
    # "an hour" on its own is a length of time, not a figure: "the shop is an hour away", "he
    # had calpol an hour ago", "people coming round in an hour" are not sums, and reading them
    # as one took the line off whatever it was about. Only a speed ("miles an hour", "km an
    # hour") or a rate ("per hour") makes the hour part of a figure.
    "maths-and-numbers": ("how many weeks", "how much is", "percent of", "what is the average",
                          "miles an hour", "miles per hour", "km an hour",
                          "per hour", "per day", "per week", "how many miles"),
    "nature-and-weather": ("change colour", "change color", "leaves change", "leaves fall",
                           "leaves turn", "in a thunderstorm", "in the spring", "this spring",
                           "next spring", "spring is", "spring flowers", "early spring",
                           "going to rain", "will it rain", "is it going to be sunny",
                           "birds might i see", "leaves are"),
    # A how-are-you said with a day or a week in it is a question about the bot, the same as the
    # shapes already here: "how was your day", "hows your day been", "how have you been". None of
    # them names a subject, so without them the carried subject decided the topic - "how long do
    # i boil an egg" then "hows your day been" was read as a cooking line and answered with the
    # keeping card for boiled eggs. Only the *your* forms are here: "how was your day at work" and
    # "how has your week been at work" name work and keep the answer they had.
    "about-the-bot": ("are you a bot", "are you real", "are you human", "what are you",
                      "who are you", "do you remember", "what can you do",
                      "what kind of things can you help", "how can you help",
                      "how was your day", "how has your day been", "hows your day been",
                      "how s your day been", "hows your day going", "how was your week",
                      "how has your week been", "hows your week been", "how s your week been",
                      "how have you been", "how you been"),
}

# Verb and adjective forms that appear in the vocabularies above but do not name a thing;
# they are kept out of the entities so a module can trust the "thing" entries.
NOT_THINGS = frozenset("""
cook cooking bake baking boil boiled frying fry roast roasted grill simmer chop chopped stir
eat eating drink drinking feed fed save saving pay paid spend spent buy buying bought sell
sold work working revise revising study studying learn learning teach taught travel travelling
traveling fly flying drive driving pack packing book booking plan planning move moving rent
watch watching read reading write writing wrote felt feel feeling sleep sleeping slept wake
waking run running jog jogging train training exercise stretching stretch grow growing plant
planting water watering clean cleaning fix fixing paint painting repair repairing adopt adopted
rescue buy fix bleed bleeding cut chopped knocked dropped broke broken spill spilled leak
leaking drain drains turned turning turned stuck stop stopped start started finish finished
scrambled poached undercooked overcooked sticky mushy crispy hungry thirsty tasty delicious
expensive cheap worth tired exhausted lonely sad unhappy upset anxious worried nervous stressed
overwhelmed depressed crying angry annoyed frustrated guilty ashamed jealous happy excited
relieved proud grateful dizzy sore ill sick unwell allergic vegan vegetarian second-hand
best better worst good bad great nice lovely favourite favorite perfect brilliant amazing
fine okay first second third last next more less most least many few several some
percent percentage maths math number numbers average total half double
log lag row sow hoe
""".split())

# Everyday things a line can name, taken from the strong vocabularies above.
THINGS = frozenset(
    word
    for words in STRONG.values()
    for word in words.split()
    if len(word) > 2 and word.isalpha() and word not in NOT_THINGS
)

PLACES = frozenset("""
london paris rome florence lisbon madrid barcelona berlin amsterdam brussels dublin edinburgh
glasgow manchester birmingham leeds liverpool bristol cardiff belfast newcastle oxford
cambridge brighton york bath bristol glasgow tokyo kyoto osaka beijing shanghai hong kong
singapore bangkok sydney melbourne auckland delhi mumbai goa istanbul athens cairo dubai
new york chicago boston seattle toronto vancouver mexico brazil argentina spain france
italy germany portugal greece turkey egypt india china japan korea thailand vietnam canada
australia america england scotland wales ireland europe africa asia
eiffel
""".split())

UNIT_WORDS = {
    "g": "g", "gram": "g", "grams": "g", "gramme": "g", "grammes": "g",
    "kg": "kg", "kilo": "kg", "kilos": "kg", "kilogram": "kg", "kilograms": "kg",
    "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb",
    "oz": "oz", "ounce": "oz", "ounces": "oz",
    "ml": "ml", "millilitre": "ml", "millilitres": "ml", "milliliter": "ml",
    "l": "litre", "litre": "litre", "litres": "litre", "liter": "litre", "liters": "litre",
    "tsp": "tsp", "teaspoon": "tsp", "teaspoons": "tsp",
    "tbsp": "tbsp", "tablespoon": "tbsp", "tablespoons": "tbsp",
    "cup": "cup", "cups": "cup",
    "c": "celsius", "°c": "celsius", "celsius": "celsius", "centigrade": "celsius",
    "f": "fahrenheit", "°f": "fahrenheit", "fahrenheit": "fahrenheit",
    "sec": "seconds", "secs": "seconds", "second": "seconds", "seconds": "seconds",
    "min": "minutes", "mins": "minutes", "minute": "minutes", "minutes": "minutes",
    "hr": "hours", "hrs": "hours", "hour": "hours", "hours": "hours",
    "day": "days", "days": "days", "week": "weeks", "weeks": "weeks",
    "month": "months", "months": "months", "year": "years", "years": "years",
    "mile": "miles", "miles": "miles", "km": "km", "kilometre": "km",
    "kilometres": "km", "kilometer": "km", "kilometers": "km",
    "metre": "metres", "metres": "metres", "meter": "metres", "meters": "metres",
    "foot": "feet", "feet": "feet", "ft": "feet", "inch": "inches", "inches": "inches",
    "mph": "mph", "percent": "percent", "%": "percent",
    "quid": "gbp", "£": "gbp", "euro": "eur", "euros": "eur", "€": "eur",
    "dollar": "usd", "dollars": "usd", "$": "usd",
    "people": "people", "person": "people", "kid": "people", "kids": "people",
    "adult": "people", "adults": "people", "guest": "people", "guests": "people",
}
WORD_NUMBERS = {
    "half": 0.5, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000, "couple": 2, "dozen": 12,
}
# The words after a figure that are how big it is rather than a word it is joined to: "70k on the
# clock", "20 grand", "2 million". They measure the figure the way a unit does, so a figure said
# back keeps them; every other word after it is the rest of the sentence.
FIGURE_SIZE_WORDS = frozenset("""k ks grand thousand million millionaire billion bn mil mths""".split())

NUMBER_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(%|[a-z]+)?")

# A unit clipped to its first letters, which is only the unit right after a figure: "a 60 yr
# old", "6 mths old", "2 wks off". Only the forms a figure can be followed by are here, and
# every one of them is a length of time, so nothing that counts something else is touched: "m"
# is not, because a metre, a minute and a month are all "m", "mo" is not, because "mo" is
# also a moment ("wait a mo"), and "mon" is not, because it is also Monday. "yo" and "y/o" are
# how people write the years of a person:
# "a 60 yo", "60 y/o".
CLIPPED_UNIT_WORDS = {
    "yr": "years", "yrs": "years", "y": "years", "yo": "years", "yos": "years",
    "mth": "months", "mths": "months", "mnt": "months", "mnts": "months",
    "wk": "weeks", "wks": "weeks",
}
# "a 60 y/o" is spelled with a slash, so the figure's own match stops at the "y".
CLIPPED_AFTER_A_SLASH = re.compile(r"\s*(?:y/o|y\.o\.?|yo)\b")

# What can sit between a figure and the half of it: "2 and a half", "2 n half", "2 and half".
# The article is optional and the "n" is "and", so the fraction is part of the same count. Read
# on its own it was a number of its own - two, and then a half - and a recipe told "2 and half
# kilos" was answered for two.
MIXED_FRACTION = re.compile(r"\s+(?:(?:and|n)\s+)?(?:(?:a|an)\s+)?(?:half|quarter)s?\b")
# A unit word here is the joiner itself, not something being counted.
MIXED_JOINERS = frozenset(("", "n", "and", "a", "an"))

_BREAKS = re.compile(r"[^a-z0-9' ]+")


# How much the conversation's current topic counts when the line is a follow-up.
CARRY = 2
# A body part on its own is not a topic; a body part that hurts is.
# The list is lexicon.BODY_PARTS because the reading repairs a misspelt part before this rule
# sees it (`normalize._parts_that_hurt`), and both halves of the repair have to agree.
BODY = lexicon.BODY_PARTS
HURTS = lexicon.PAIN_WORDS
# A body part with a word for the state of the skin is health, the way a part with a word of
# pain is: "my hands are dry and cracked", "my skin is really dry in winter", "my heels are
# cracked". The two words are enough together, and either alone is not ("a dry winter", "the
# cracked tile", "my back"): the state has no topic of its own.
SKIN_STATES = frozenset("""dry drier dryness flaky flakes flaking cracked cracking chapped
    itchy itching peeling""".split())
SKIN_REACH = 3
SKIN_BOOST = 4
# The parts whose dry or cracked state is the skin: the body parts, plus the ones people name
# for dryness without ever saying "skin" ("my lips are chapped", "my cheeks are flaky").
SKIN_PARTS = BODY | frozenset("""face cheeks cheek knuckles knuckle lips lip mouth heels""".split())
# The head said as the seat of thinking, for the fog words above. A tongue or a throat that feels
# thick is a different line and often an emergency, so neither is here.
HEAD_WORDS = frozenset("""head brain mind thoughts thinking concentration memory""".split())


# A head that will not clear is said with the weather's own words: "my head is cloudy", "my
# head feels foggy", "i have brain fog", "my head feels thick". The sky is cloudy for a different
# reason, and a soup or a jam is thick, so the fog word only counts when the speaker's head, brain
# or mind is the thing it is said of. The reply for it is the mind-that-will-not-settle pool, so
# it is read as the body state it is - a foggy head is what the person has, not a mood they are in.
HEAD_FOG = frozenset("fog foggy cloudy misty muzzy woolly wooly fuzzy thick".split())
HEAD_FOG_REACH = 4
HEAD_FOG_BOOST = 6


def _head_fog(norm):
    """True when the line says the speaker's own head, brain or mind is foggy or thick."""
    foggy = [at for at, word in enumerate(norm) if word in HEAD_FOG]
    if not foggy:
        return False
    for at, word in enumerate(norm):
        if word in HEAD_FOG or word not in HEAD_WORDS:
            continue
        # a head word just before the fog word: "my head feels thick", "my head is cloudy"
        if any(0 < other - at <= HEAD_FOG_REACH for other in foggy):
            return True
    return False


def _skin_state(norm, skip):
    """The position of a body part within `SKIN_REACH` of the state of its skin, or None.

    The reach keeps a state said of something else off the body: "the cracked tile under my
    feet" is the tile, and only a part next to the state is the skin ("my heels are cracked").
    """
    states = [at for at, word in enumerate(norm)
              if word in SKIN_STATES and at not in skip]
    if not states:
        return None
    for at, word in enumerate(norm):
        if word not in SKIN_PARTS or at in skip:
            continue
        if any(abs(state - at) <= SKIN_REACH for state in states):
            return at
    return None


# A body part that is "playing up" is a health line: "my knees are playing up", "my tummy is
# playing up since breakfast", "my back plays up in the cold". The two words say something is
# wrong with the subject and nothing about what, so what the line is about is the part. Without
# this the verb "play" won it the entertainment topic, and a bad knee was read as television.
PLAYS_UP_BEFORE = frozenset("""playing playin plays play played acting acts acted
    """.split())
PLAY_UP_REACH = 3
PART_UP_BOOST = 4


def _a_part_plays_up(norm, skip):
    """The position of a body part that is playing up, or None.

    The part has to be next to the words, so "the kids are playing up" (no part) and "the
    boiler is playing up" (a part of the house, not of a person) are not health lines.
    """
    ups = [at for at, word in enumerate(norm)
           if word == "up" and at and at not in skip
           and (norm[at - 1] in PLAYS_UP_BEFORE
                # "my eyes are playing me up"
                or (at >= 2 and norm[at - 1] in ("me", "my")
                    and norm[at - 2] in PLAYS_UP_BEFORE))]
    if not ups:
        return None
    for at, word in enumerate(norm):
        if word not in BODY or at in skip:
            continue
        if any(0 < up - at <= PLAY_UP_REACH for up in ups):
            return at
    return None


# A body part with a word of pain is the subject of the line, whatever else the line names. Five
# is above the three a phrase scores and the two a vocabulary word scores, so the part the person
# is complaining about wins: "my back has been killing me since i moved the sofa" is the back and
# the sofa is the reason, and "my chest hurts and its going down my left arm" is the chest, not
# how the person feels about it.
HURT_BOOST = 5
# A condition named by its own name is a health line, with no part and no word of pain in it:
# "ive got piles", "my eczema is flaring up", "i think i have sciatica". These read no topic at
# all, because the reader only knew the parts of the body and the words for pain, and a
# named illness is neither. Four is above the two an ordinary vocabulary word scores, so the
# complaint wins over an incidental word in the same line ("my gout is playing up" was
# entertainment from "playing"), and below the five a part with a word of pain scores.
CONDITION_BOOST = 4
# The conditions people name by name. A word here is never bent into another one and is never
# the subject of its own line; it is only evidence that the line is about the body.
CONDITIONS = frozenset("""cystitis uti thrush dandruff eczema asthma verruca verrucas piles
    haemorrhoids sciatica gout stye styes shingles tonsillitis arthritis coeliac anaemic anaemia
    psoriasis rosacea conjunctivitis bronchitis pneumonia appendicitis vertigo tinnitus
    endometriosis ibs crohns colitis prolapse bunion bunions whitlow ringworm scabies nits
    headlice hypo hypos coldsore coldsores abscess quinsy phlebitis dvt cataract cataracts
    glaucoma gingivitis hiccup hiccups thyroid constipated
    boil boils lump lumps spot spots cyst cysts filling fillings
    pcos copd lupus fibromyalgia hashimotos hypothyroid hyperthyroid epilepsy diabetes
    anorexia bulimia cfs ibd""".split())
# A few of those have a second life so ordinary that the word alone is not the condition: a
# kettle boils, a lump of coal, a spot on the wall, a filling in a sandwich, and a thrush that
# sings in the garden. One table says the word counts only beside the part it is on; the other
# says it never counts when one of its other-life words is in the same line.
CONDITION_NEEDS_PART = frozenset("""boil boils lump lumps spot spots cyst cysts""".split())
# A word whose other life is not a thing but another part of life altogether: a filling is in a
# tooth or in a sandwich, and "after filling the car" is a petrol station with a gas smell. The
# part that says so is named, because any part of the body will not do.
CONDITION_NEEDS_WORD = {
    "filling": frozenset("""tooth teeth molar molars cavity cavities dentist dental gum gums
        filled""".split()),
    "fillings": frozenset("""tooth teeth molar molars cavity cavities dentist dental gum gums
        filled""".split()),
}
CONDITION_OTHER_LIFE = {
    "thrush": frozenset("garden lawn bird birds nest hedge tree trees feeder".split()),
    # the shingles on a roof, not the shingles a person gets
    "shingles": frozenset("roof roofs tile tiles tiled shed sheds wall walls house chimney slate".split()),
}
# A condition word that is also the head of an ordinary phrase is not the condition where that
# phrase follows it: "piles of washing", "piles of leaves", "piles of paperwork" are piles of
# something, and the complaint is "piles" on its own. The word straight after decides, which is
# the one thing a set of words anywhere in the line cannot say.
CONDITION_NOT_NEXT = {
    "piles": frozenset("of".split()),
}
CONDITION_REACH = 3


def _named_condition(norm, words, skip):
    """True when the line names a condition that is not, here, its other life.

    The part the word is on has to be within `CONDITION_REACH` for a word in
    `CONDITION_NEEDS_PART` ("i have a boil on my back" is health, "boil the kettle" is not),
    and one of the other-life words has to be absent for a word in `CONDITION_OTHER_LIFE`. An
    animal that has the condition is the animal's: "the dog is constipated" is a pet question
    with an answer about warm beds and short walks, so the condition counts only where no
    animal is named, unless a person is named as well ("my son has nits and so does the cat").
    """
    if words & PETS and not words & (_person_words() - PETS):
        return False
    for at, word in enumerate(norm):
        if word not in CONDITIONS or at in skip:
            continue
        nexts = CONDITION_NOT_NEXT.get(word)
        if nexts and at + 1 < len(norm) and norm[at + 1] in nexts:
            continue
        other = CONDITION_OTHER_LIFE.get(word)
        if other and words & other:
            continue
        if word in CONDITION_NEEDS_PART and not any(
                abs(other_at - at) <= CONDITION_REACH and other_word in BODY
                for other_at, other_word in enumerate(norm) if other_at not in skip):
            continue
        wanted = CONDITION_NEEDS_WORD.get(word)
        if wanted and not any(
                abs(other_at - at) <= CONDITION_REACH and other_word in wanted
                for other_at, other_word in enumerate(norm) if other_at not in skip):
            continue
        return True
    return False
# A person and something wrong with them is a health line: "my baby has a temperature", "my son
# has a fever", "the dog is being sick". The person is who it happens to; what the line is about
# is what is wrong with them, so the person being named does not make it a family line.
UNWELL_BOOST = 3
# The topics a person the line names belongs to. A symptom said of one of them is health.
PEOPLE_TOPICS = ("family-and-parenting", "friends-and-relationships", "pets")
# Signs that a person is not themselves. They name no subject on their own ("i am confused about
# my tax" is not a health line), so they only count when the line says who it is about.
# "throwing" is not one of them on its own: "we are throwing a party" says who it is about, so a
# bare "throwing" is a health line. The phrase carries the sickness ("throwing up", "threw up"),
# and the other spoken verbs (puking, puke, puked, barf) do not live a second life.
UNWELL_SIGNS = frozenset("""unresponsive unconscious drowsy confused floppy limp listless
    dehydrated collapsed fitting seizure seizures temperature fever sepsis bleeding puking
    puke puked barf
    breathless rash cold cough flu dizzy vomiting vomit diarrhoea diarrhea constipated
    wheeze wheezing swollen infection itchy ill unwell allergy allergic diabetic diabetes
    overdose pills operation surgery chemo chemotherapy fell fall fallen broken broke
    fracture fractured stroke injured injury""".split())
# "not feeding" is a sign in a way that "feeding" is not, so it needs the word before it.
UNWELL_NOT = frozenset("""feeding drinking eating responding waking weeing""".split())
# Some signs also name an ordinary thing ("a temperature", "a cold", "a cough", "pills"), so they
# are a sign where they are said of the person and not where they modify the next word: "her
# temperature homework" and "a cold shoulder" are not complaints about anybody.
NOUNY_SIGNS = frozenset("""temperature cold cough flu pills pill operation surgery infection
    rash seizure seizures allergy overdose chemo chemotherapy diabetes dose medicine""".split())
# What may follow a sign word for it to still be the state of the person rather than a modifier
# of the next noun.
# The people a line can name: the kinship words, the pet words, and the small words for a person
# that carry no topic of their own ("my newborn", "someone").
EXTRA_PEOPLE = frozenset("""newborn newborns toddler toddlers baby babies person people someone
    somebody anyone anybody child children kid kids""".split())


def _person_words():
    """Every word that can name a person a symptom could be said of."""
    words = set(RELATIONS) | EXTRA_PEOPLE | PETS
    for topic in ("family-and-parenting", "friends-and-relationships"):
        words |= set(STRONG[topic].split())
    return frozenset(words)


# What may follow a sign word for it to still be the state of the person rather than a modifier
# of the next noun.
SIGN_FOLLOWS = frozenset("""a an the his her my your our their its is was are were am has have
    had got get gets of and or but so to for in on at with from since last this that these those
    today tonight yesterday morning night now still again too very really all just should shall
    will would can could do does did not no time times day days week weeks month months about
    up down out over""".split())
# "not responding" needs a hearer: "my sister is not responding to my texts" is about the texts.
HEARERS = frozenset("""me us name names pain voice voices anything anyone nothing stimulus
    sounds noise light lights it them him her breakfast medicine""".split())
COMMS = frozenset("""text texts message messages phone phones mobile mobiles email emails
    call calls whatsapp dm dms letter letters post emailing texting""".split())
# A sign straight before one of these is a behaviour, not a body: "my son is unresponsive when he
# is told off".
BEHAVIOUR = frozenset("""when whenever if unless because after before till until once while""".split())
# "fell asleep", "fell out with", "a fall out": the word is part of another figure of speech, so
# it is not the injury it looks like.
SIGN_NOT_AFTER = frozenset("""asleep out over apart behind short through pregnant ill about
    for""".split())
# Saying "bleeding me dry" is a complaint about somebody's requests.
UNWELL_IDIOMS = ("bleeding me dry", "bleed me dry", "bleeding us dry", "bleed us dry",
                 "drove me mad", "driving me mad", "worried sick", "bored stiff")
PETS = frozenset("""dog dogs puppy puppies cat cats kitten kittens rabbit hamster parrot goldfish
pet pets""".split())
# An animal someone owns is not the world working: "why are my fish dying" is about the fish in
# the tank, while "why do fish breathe underwater" is still a science question, so only the
# possessive is the cue, and only for a word that names the animal itself ("my rabbit", "our
# guinea pig"). A bare "fish" is dinner as often as it is a pet.
OWNERS = frozenset("""my our his her their""".split())
ANIMALS = frozenset("""dog dogs puppy puppies cat cats kitten kittens rabbit rabbits hamster
hamsters guinea parrot parrots budgie budgies goldfish fish tortoise tortoises turtle turtles
snake snakes lizard lizards gecko geckos horse horses pony""".split())
# A chicken, a duck and a pig are dinner as often as they are pets ("my chicken is still frozen
# in the middle"), so they are not here, and "guinea" is here rather than "pig" for the same
# reason.
PET_BOOST = 3
# A word that is both a country and an everyday thing ("turkey", "china", "brazil") means the
# thing in most lines and the country in some, so the sentence has to decide: once it has said
# the word is the place (a capital letter, a place word in front, "turkey in europe", or a word
# only a country takes), the country is what the line is about, and the ordinary sense of the
# word does not take the line off it. Without this one word in a cooking vocabulary sends "is
# turkey in europe" to the kitchen.
COUNTRY_BOOST = 6
# A gift is the most common shopping question, and it is asked with the plainest verb there
# is: "what should i get my sister for christmas", "what could i get her". "Get" on its own
# is every verb at once, so it only counts with a person to give to and a line that asks.
GIFT_WORDS = frozenset("gift gifts present presents".split())
GIFT_ALWAYS = frozenset("gifts presents".split())
# "Got" and "gotten" are the same errand said in the past - "i still havent got her anything",
# "have you gotten your mum a present yet" - and a present owed is said that way more often
# than any other, usually with no question word at all.
GIVE_VERB = frozenset("get gets got gotten getting buy buys buying bought pick wrap".split())
# A present is not always asked for: "i still havent got her anything", "still need to get my
# mum something", "nothing for her yet". The person and the thing are named the same way as
# in a question, so what is missing is only the word that makes it one - and a line that says
# the present is still to come is about the present.
GIFT_WANTING = frozenset("""need needs needed needing still yet havent havnt haventgot
    must should ought havent got gotta later tomorrow soon""".split())
GIVE_TO = frozenset("""her him them mum mom mother dad father sister brother nan gran
    granny grandma grandad grandpa friend friends teacher husband wife partner son daughter
    nephew niece colleague boss kids child children inlaws flatmate flatmates housemate
    roommate mate mates cousin cousins aunt aunty uncle neighbour neighbor girlfriend
    boyfriend""".split())
GIFT_OCCASION = frozenset("""christmas xmas birthday anniversary wedding graduation
    leaving retiring retirement""".split())
GIFT_ASKING = frozenset("""should could would shall what which worth best any idea ideas""".split())
# The words that stand for the thing given when no person is named: "get something",
# "get a present", "get ideas". They follow the giving verb closely, like a person does.
GIVE_THING = frozenset("""something anything ideas idea nothing""".split())
GIFT_BOOST = 5
# What the words after a person have to name, for "get <person> ..." to be a gift: the
# thing given ("get her something", "get her a present") or the reason ("for christmas").
GIFTS_OR_OCCASIONS = GIVE_THING | GIFT_WORDS | GIFT_OCCASION
GIVE_THINGS = GIVE_THING | GIFT_WORDS
GIVE_DETERMINERS = frozenset("my your his their our the a an some".split())
# After "get my mate", a clause that describes the person rather than the errand.
GIVE_RELATIVE = frozenset("who whos that".split())

# A crop that is not doing well where it grows is a growing question, not a cooking one: "my
# tomatoes are going blue", "my tomatoes are not ripening", "my courgettes are rotting". The
# crop words are the same either way, so what the line says is happening to it is what tells the
# two apart - and a kitchen word or a place the food is kept says the crop is dinner, which is
# why the same state in a fridge or a pan changes nothing.
CROP_STATES = ("not ripening", "going blue", "gone blue", "going yellow", "turning yellow",
               "gone to seed", "blossom end rot", "not flowering", "no flowers", "not fruiting",
               "no fruit", "ripening", "bolting", "leggy", "wilting", "drooping", "rotting",
               "rotten", "stunted", "flowering", "splitting", "dying")
CROP_KITCHEN = frozenset("""fridge freezer cupboard pantry shelf shop shops supermarket market
bag box tub jar tin pan pans oven hob pot pots bowl plate dinner lunch tea recipe cook cooked
cooking eat eating mash roast boil boiled fry fried bake baked salad sandwich soup sauce""".split())
# The crops people grow, said by the person who grows them. A crop is dinner in plenty of lines
# and a plant in plenty of others, which is why only the state it is in decides.
CROPS = frozenset("""tomato tomatoes tom toms potato potatoes courgette courgettes zucchini
cucumber cucumbers pepper peppers chilli chillies chili chillis carrot carrots onion onions
leek leeks garlic lettuce spinach kale cabbage cabbages bean beans pea peas strawberry
strawberries raspberry raspberries blackberry blackberries blueberry blueberries apple apples
pear pears plum plums cherry cherries grape grapes rhubarb beetroot beetroot parsnip parsnips
squash pumpkin marrows marrow broccoli cauliflower sweetcorn corn aubergine aubergines
basil mint parsley rosemary thyme coriander chives sage oregano dill herbs herb""".split())
# Where a crop grows: said of the person's crop, one of these makes the line about the plant.
GROWING_PLACES = frozenset("""plant plants vine vines tree trees greenhouse greenhouse allotment
allotments garden plot pots bed beds border seedling seedlings bush bushes""".split())
CROP_BOOST = 3
TRAVEL_CUES = frozenset("""trip holiday flight fly flying visit visiting travel travelling
traveling abroad hotel booking itinerary sightseeing tourist stay staying going go get
plan plans planned planning break weekend week days""".split())

# How the world works: the ground under us, the sky, the animals and the body. A why/how
# question about one of these asks science, whatever else its words point at: "why do fish
# breathe underwater" is not dinner and "why do my ears pop on a plane" is not a trip.
WORLD = frozenset("""sun sky moon stars earth planets planet ocean sea river mountain
mountains snow ice rain wind thunder lightning clouds tides gravity rainbow seasons
winter summer spring autumn frost temperature fish fishes bird
birds animal animals insects bees brain bones lungs cells atoms veins""".split())
# "back", "hand", "arm", "leg", "foot" and "chest" are the body and also an adverb, a clock, a
# verb, a table and a guard ("how fast should i push on the chest"), so only a body part that
# cannot be mistaken for another word counts. "world" and "blood" are everywhere ("how many
# countries are there in the world", "why do my eggs have blood spots"), so neither is here.
WORLD |= BODY - frozenset("back hand hands arm arms leg legs foot feet chest".split())
# An ice-maker answers a why-question by being broken, not by being ice.
WORLD_NOT = frozenset("maker machine tray cube bin bucket box cream lolly lollies".split())
# The sky, the sea and the animals already have a topic of their own: "why do birds sing so
# early" is a nature question and stays one, so the boost only helps a line with no such word.
NATURE_WORDS = frozenset(STRONG["nature-and-weather"].split())
MECHANISM = ("why", "how")
# "how" only asks how the world works when it is asking for an amount of it ("how old is the
# earth"); "how do i unblock the sink" is a job for another topic.
MECHANISM_HOW = frozenset("old many long far hot cold big deep fast wide".split())
SCIENCE_BOOST = 2
# A cue word that is also an ordinary verb says nothing about the topic when the line puts an
# object after it: "revise my cv" is work and money, "revise for my exam" is school, and
# "how do i revise so it stays in my head" is study too, because nothing is acted on.
VERB_CUES = {
    "school-and-study": frozenset("""revise revising revision""".split()),
}
# The things that make "revise" mean study even when something follows it.
STUDY_OBJECTS = frozenset("""exam exams test tests mock mocks gcse a-level alevel biology
chemistry physics maths math history geography french spanish german notes revision
coursework subject term paper spelling vocabulary homework school college university
class lesson a2 as-level sat sats""".split())
# Words that open the thing a verb acts on: "revise **my** cv".
DETERMINERS = frozenset("""my your his her their our the a an this that these those some any""".split())
# A health word that is also an ordinary verb says nothing about health when the thing it acts
# on is not the body: "i burnt the pan" is a kitchen job, "cut the grass" is the garden,
# "how do i cut my energy bill" is money, and "how do i bleed a radiator" is the heating. It
# speaks for health when the body is what it acts on ("i burnt my finger", "cut myself shaving")
# or when nothing is named ("how do i treat a burn", "what do i do for a burn on a child",
# "my nose is bleeding").
BODY_CUES = frozenset("""burn burnt burned burning scald scalded scalds cut cuts cutting
    bleed bleeding""".split())
# The body words the burn or the cut is on. `BODY` is the list the pain rule uses; these are the
# parts people name without it ("i cut my tongue", "i burnt my palm").
PARTS = frozenset("""me myself yourself himself herself themselves ourselves itself tongue lip
lips gum gums cheek cheeks chin forehead scalp brow eyebrow eyelash eyelid palm palms nail
nails knuckle knuckles thigh thighs calf calves shin shins shing toe toes sole soles mouth
mouths face faces nose noses bottom bottoms bum waist sides upper lower""".split())
BODY_OR_SELF = BODY | PARTS
# What may follow a burn or a cut without saying what it acted on: the sentence carrying on
# ("burnt and sore", "cut it out"), a time word, or a word of degree. Anything else after the
# cue with no determiner in front of it is the thing the cue describes ("a burning smell",
# "the wood burning stove", "burnt toast"), so the cue is not about the body.
CUE_CARRIERS = frozenset("""and or but so now again today yesterday tomorrow still then than
    it into in on at when if because very really badly slightly a bit
    down back up out off away through over around first next""".split())

# The judgement said as an absolute about their own record, in whatever form of the verb: "im
# getting everything wrong" and "i keep getting everything wrong" are the same line as "i get
# everything wrong", and the phrase list has one form of each verb, so the -ing and the "keep"
# forms were left with no topic at all. The speaker has to be the one it is about, so "the printer
# does everything wrong" and "how do i fix everything wrong in the kitchen" stay about the printer
# and the kitchen. Only the verbs that mean doing or getting here: "i made it all up" is inventing
# something, not this.
JUDGEMENT_OF_RECORD = re.compile(
    r"\b(?:i|i'm)\s+(?:am |was |have |had |been |being |always |still |just |really |"
    r"keep |keeps |kept |constantly |probably )*"
    r"(?:get|gets|getting|got|do|does|did|doing|mess|messes|messed|messing)\s+"
    r"(?:everything|it all)\s+(?:wrong|up)\b")

# The judgement said as their own unfitness: "im not cut out for this job", "i dont think im cut
# out for nursing", "im not cut out to be a teacher". It is how they see themselves, not a fact
# about the job, and it is the shape people reach for when they cannot name a feeling. "cut" is
# also a health word, so "im not cut out for this job" was read as a body and got health and "Got
# it. Is there anything you'd like a hand with?".
NOT_CUT_OUT = re.compile(r"\b(?:cut out|made) (?:for|to be)\b")
# The words that make it a judgement rather than a boast: "im cut out for this" is the good news
# it sounds like, and "i never cut out sugar" says nothing about being cut out for anything.
NOT_WORDS = frozenset("not never dont don't didnt didn't isnt isn't wasnt wasn't aint ain't".split())
# Who the judgement is about. "my brother is not cut out for the army" is a line about him, and
# the nearest one of these to the phrase is the one it belongs to.
OWN_SELF = frozenset("i im i'm me myself".split())
OTHER_PERSON = frozenset("""he she they hes shes theyre him her them his her their you your
    we we're us our my brother sister son daughter mum mom dad father mother husband wife
    partner friend boss colleague""".split())

def reads_as_unfit(text):
    """Where the words say they are not cut out for something, or None.

    Shared with the composer (`bot/modules/chat.py`), which answers it with the pool for a
    judgement about themselves: the engine decides the line is about how they see themselves, and
    the composer must not then treat it as a fact about a job.

    The negative and the person are what make it a judgement: "im cut out for this" is a boast,
    "i never cut out sugar" is a diet, and "my brother is not cut out for the army" is about him.
    """
    for match in NOT_CUT_OUT.finditer(text):
        before = text[:match.start()].split()[-6:]
        if not any(word in NOT_WORDS for word in before):
            continue
        person = [word for word in before if word in OWN_SELF or word in OTHER_PERSON]
        if not person or person[-1] not in OWN_SELF:
            continue
        return match.start()
    return None




# A person who gives something up is changing what they eat or drink, not asking about a recipe.
# "i gave up sugar", "i gave up bread last year" and "i packed in the chocolate" are diets, and
# the cooking card answered them with how long bread keeps, because the food's own name is a
# cooking word and nothing in the line was a reading of a recipe. The verb is what makes the line
# a diet, and what is given up has to be something eaten or drunk, so "i gave up my gym" and "i
# gave up the bus" keep the reading their own words give them.
GIVING_UP = ("gave up", "give up", "given up", "gives up", "giving up", "packed in",
             "packing in", "cut out", "cutting out", "cut down on", "cutting down on",
             "stopped eating", "stopped drinking", "gone off")
# What a person gives up: anything the two food tables name, which is the food, the drink and the
# ingredients, and not the pan it is cooked in.
GIVEN_UP_FOOD = frozenset(STRONG["food-and-drink"].split()) | frozenset(
    word for word in STRONG["cooking"].split()
    if word in ("meat", "dairy", "gluten", "lactose", "nut", "soya", "soy", "wheat"))
GIVING_UP_BOOST = 3


def _a_habit_given_up(norm):
    """True when the line gives up something they eat or drink, read off the whole line."""
    text = " ".join(norm)
    if not any(word in GIVEN_UP_FOOD for word in norm):
        return False
    return any(phrase in text for phrase in GIVING_UP)


GENERIC = frozenset("""a an the to of in on at for with my your i you it is and or something
someone thing things any some this that these those be have do does""".split())

# Words that name two everyday things, so they back an area but cannot decide it on their own: a
# line whose only evidence for an area is one of these is usually about the other sense. "the milk
# smells off but the date says tomorrow" is food, not a date; "it is the season for strawberries"
# is food, not a season of a series. When people mean one of the two senses they usually say so
# in a phrase, and the phrase carries the area instead: "on a date", "use by date", "season
# ticket". "store" is a shop and a verb: "how do i store basil" is cooking, "the store was shut"
# is shopping, and "at the store" says which one is meant. The same holds for a book people read
# and a table people book, a coach that drives and a coach who trains, a dish on a plate and the
# dishes in the sink, a match of rugby and socks that do not match, the spring of the year and the
# spring of a bike, a thing to watch and watching the kids. "Cream" is the dairy and the
# moisturiser, and only the line says which: "cream the butter", "dry hands want cream".
# "pressure" is the doctor's only when it is blood pressure, which the phrase says: a boiler, a
# tap, a tyre and a shower all have one, and "under pressure" at work has nothing to do with the
# body.
POLYSEMOUS = frozenset("""date season store book coach dish match spring watch cream
    pressure""".split())

# "half a cabbage", "half the batter", "double the recipe": a quantity cut from a thing, so it
# is said at one point like a polysemous word and cannot carry an area alone. "half of 80" is a
# sum, and "its a 10k, not a half" names a race, so those keep their full weight.
PORTION_WORDS = frozenset("""half double triple""".split())
# "half a cup in ml", "half a stone", "half a pint of milk": the word after the article is a
# unit of measure, so the figure is a figure again and keeps its full weight. A dish or a thing
# ("half a cabbage", "half the batter") is a piece of what the line already names.
PORTION_UNITS = frozenset("""cup cups stone stones pint pints litre litres ml gram grams kilo
kilos kg ounce ounces oz tablespoon tablespoons tbsp teaspoon teaspoons inch inches foot feet
mile miles metre metres metre hour hours minute minutes""".split())

POLY_FORMS = POLYSEMOUS | frozenset(word + "s" for word in POLYSEMOUS)

# A season says *when* something happens, or which jumper it is: "we are moving house in the
# spring" is the move, "i need a new winter coat" is something to buy, "i broke my arm last
# winter" is the arm, and "how much should i spend on a winter coat" is the money. The season is
# the subject only when the weather is: the rest of the line is the weather's own words ("what
# should i feed the birds in winter", "does it get worse in winter"). So a line that names
# another subject takes the season back to the one point that says "maybe", the same point a word
# with two everyday senses keeps.
SEASONS = frozenset("spring summer autumn winter".split())
# A season with one of these in front of it is what the weather was like, not when something
# happened: "a dry winter is hard on the garden", "a mild winter", "the wettest summer".
WEATHER_BEFORE = frozenset("""dry wet cold warm mild harsh hard bad good long short late early
    frosty freezing sunny rainy""".split())
# A temperature or a sky word says what the weather is like, so the line is about the weather
# even when a season is only saying when: "is it warm in the summer in spain".
WEATHER_ITSELF = frozenset("""warm cold hot sunny cloudy raining snowing windy icy freezing
    icy humid muggy showers drizzle""".split())

# Two lives, decided by the words that only fit one of them. "train" is the railway and the
# exercise, and "the train is cancelled", "my train leaves at seven" and "the train to leeds"
# cannot be the exercise; the exercise is said with "train for", "train hard" or a number of
# times, and none of those words appears in a line about the railway. The cue does not have to
# sit next to the word: people write "the train to leeds is cancelled". A line with no cue at
# all keeps the plain word ("i train three times a week"), so nothing is taken from the
# exercise; a cue only ever adds the other area, it never takes the plain one away.
# A cue word that only fits one life of the word is strong evidence - strong enough to beat the
# plain word plus any phrase that contains it (`the match` is 3 + 2 for sport), so it is scored
# above both rather than beside them.
SENSE_WEIGHT = 6
# A cue is a word that only fits one life of a word with two. Some cues are so much that life's
# own that being near the word is enough ("the train to leeds is cancelled"). Others are ordinary
# English - "light", "missed", "catch" - and they turn up in lines about the other life all the
# time ("the floodlights lit the pitch", "i train and then catch a cold"), so they have to sit
# right beside the word to count. Anything looser makes the fix worse than the miss.
SENSE_REACH = 3
SENSE_NEAR = 2
# What a line uses to say its bin is the one on a computer. Nothing here fits the bin under the
# sink, so the words settle the sentence rather than tipping one reading.
MACHINE_BIN_WORDS = frozenset("""recycle trash windows mac macbook laptop desktop disk disks
    file files folder folders downloads download storage usb restore permanently""".split())
SENSE_PAIRS = {
    "train": (("train", "trains"), "geography-and-travel", (
        # No other kind of train has a ticket, a platform or a timetable.
        (SENSE_REACH, frozenset("""ticket tickets station platform timetable fare fares rail
            railcard carriage intercity""".split())),
        # A training week is not cancelled and a session is not delayed, so these may stand a
        # little away: "the trains are all cancelled today".
        (SENSE_REACH, frozenset("cancelled cancel delayed delay".split())),
        # A trainer misses a session and catches a cold, so these must touch the word:
        # "i missed my train", "catch the train".
        (SENSE_NEAR, frozenset("""missed miss catch catching missed leaves leaving departs
            departing arrives arrival""".split())),
    )),
    # "run" is the exercise and the service: a bus runs, a train runs, and "how often does the
    # bus run" and "does the tram run late" are a timetable question that read as fitness and
    # got "Three sessions a week is the number to aim for." The service noun has to sit right
    # beside the word, because "running for the bus" and "i run to catch the train" are the
    # exercise with a bus in them, and there the noun is three or more words away.
    "run": (("run", "runs", "running", "ran"), "geography-and-travel", (
        (SENSE_NEAR, frozenset("""bus buses train trains tram trams coach coaches tube
            ferry ferries flight flights timetable""".split())),
    )),
    # "match" is a game and a thing struck to make fire. Only a fire has a flame, kindling or
    # firelighters. "Light", "lit" and "strike" are ordinary words, but a football line does not
    # put one within three words of the match ("the floodlights lit the pitch", "a candle lit
    # dinner" are further off), and "the match wont light" is three once "wont" is two words.
    # "chippy" is the chip shop and the carpenter. A chippy who hangs a door is not dinner, and
    # the joinery words are the ones a food line never has.
    "chippy": (("chippy", "chippies"), "home-and-diy", (
        (SENSE_NEAR, frozenset("""door doors hinge hinges hang hanging shelf shelves skirting
            timber joiner joiners fitter fitted""".split())),
    )),
    # A mole is a shape on the skin and a pest in a lawn, and each of the two has its own
    # words: "should i get my mole checked" is the doctor's and "the mole in the garden" is
    # not. Nothing is taken from the doctor's reading, which keeps the word.
    "mole": (("mole", "moles"), "garden-and-plants", (
        (SENSE_REACH, frozenset("""garden gardens lawn lawns grass hedge hedges border borders
            soil flowerbed flowerbed lawnmower molehill molehills tunnel tunnels""".split())),
    )),
    # A root is a plant's, a number's, a tooth's and a phone's. "whats the root of a plant" is
    # the garden, a root canal is the dentist's, and root access is the phone's.
    "root": (("root", "roots"), "garden-and-plants", (
        (SENSE_REACH, frozenset("""plant plants tree trees soil pot pots potted repot repotting
            cutting cuttings seedling seedlings""".split())),
    )),
    "root-canal": (("root", "roots"), "health", (
        (SENSE_NEAR, frozenset("""canal tooth teeth dentist dental filling abscess gum
            gums""".split())),
    )),
    "root-maths": (("root", "roots"), "maths-and-numbers", (
        (SENSE_NEAR, frozenset("""square squares squared cube cubed equation equations
            number numbers solve solved divided prime""".split())),
    )),
    "root-access": (("root", "roots"), "technology", (
        (SENSE_NEAR, frozenset("""phone android device access enable enabled boot bootloader
            samsung pixel tablet""".split())),
    )),
    # Stock is what a shop keeps, what a pan is made from and what the market trades. Only the
    # market and the pan have their own words.
    "stock": (("stock", "stocks"), "money", (
        (SENSE_NEAR, frozenset("""market markets share shares trading trader exchange portfolio
            dividend dividends isa""".split())),
    )),
    "stock-pot": (("stock", "stocks"), "cooking", (
        (SENSE_NEAR, frozenset("""cube cubes pot pan soup gravy vegetable chicken beef ham
            simmer simmering broth""".split())),
    )),
    "match": (("match", "matches"), "home-and-diy", (
        (SENSE_REACH, frozenset("""box damp flame flames firelighter firelighters kindling bbq
            barbecue burner smoulder smolder""".split())),
        (SENSE_REACH, frozenset("light lights lit strike struck".split())),
    )),
    # A bin is the one under the sink and the one on a computer, and only a machine has a
    # recycle bin, a desktop or a disk. A cue of that kind says the line is about the machine, so
    # it names the technology topic. The cue is always a word about the machine and never the verb
    # the two bins share: "empty" belongs to both, so "the bin needs emptying" names no
    # technology and keeps the bin under the sink.
    "bin": (("bin", "bins"), "technology", (
        (SENSE_REACH, MACHINE_BIN_WORDS),
    )),
}


def the_bin_is_on_a_machine(understood):
    """True when the sentence's bin is the one on a computer ("how do i empty the recycle bin on
    my laptop"), False when it says nothing about a machine ("the bin needs emptying").

    The machine words above are what settles it, and the technology topic is the same reading
    from the other side: a line that names a laptop or a disk is about a machine whether or not
    it uses one of these words. A line that names neither keeps the everyday bin, which is what
    "my bin is full" and "how do i empty my bin" are.
    """
    words = set((understood or {}).get("words") or ())
    if words & MACHINE_BIN_WORDS:
        return True
    return "technology" in ((understood or {}).get("topics") or ())


# Some words have two ordinary lives and the rest of the sentence is what says which. A bank is
# a place that keeps money and the ground beside a river; a seal is an animal and the rubber edge
# of a lid. With a cue in the line the word is read; with none, the word is the only subject and
# guessing gives a confident card for the wrong thing ("the bank was closed" was answered with
# how to close an account). The cue sets are deliberately small and only hold words that fit one
# life: "closed", "broken" and "looks" are not cues, because both lives have them.
TWO_LIVES = {
    "bank": (("bank", "banks"), (
        (frozenset("""account accounts money cash card cards overdraft loan loans mortgage
            mortgages payment payments paid pay savings branch branches switch switches
            statement statements balance balances deposit deposits withdraw withdrawal
            transfer transfers debit credit cheque cheques interest debt debts atm cashpoint
            salary salaries wages building society current holiday holidays food blood
            england sperm said says told rang ring called phoned robbed robbery robber cashier teller
            vault charge charges charged charging fee fees refund refunds claim claims useless
            overdrawn locked blocked phone app online free pending shut shuts empty sunday
            sundays saturday saturdays weekday weekdays hours opening opens""".split()),
         frozenset(("money", "shopping", "life-admin", "work-and-money"))),
        (frozenset("""river rivers water fish swim swimming path paths walk walked walking boat
            boats flood flooded muddy grass trees reeds ducks swans fishing current currents
            flow steep bridge bridges canal canals lake lakes stream streams shore bankside""".split()),
         frozenset(("nature-and-weather", "geography-and-travel", "fitness", "home-and-diy"))),
    )),
    "seal": (("seal", "seals"), (
        (frozenset("""zoo sea beach ocean shore rocks ice swimming fish pup pups rescue wildlife
            aquarium flipper flippers colony warden vet injured entangled plastic cute cuddly
            adorable""".split()),
         frozenset(("pets", "nature-and-weather", "geography-and-travel"))),
        (frozenset("""jar jars lid lids door doors window windows freezer fridge container
            containers bottle bottles cap caps rubber gasket airtight vacuum preserve jam
            pickle filter filters oven washing machine drum black mould mold leak leaks
            leaking leaked dripping split torn worn perished hardened stiff sticky crumpled
            shut shuts""".split()),
         frozenset(("home-and-diy", "cooking", "cleaning", "food-and-drink"))),
    )),
}
TWO_LIVES_FORMS = {form: tiers for _forms, tiers in TWO_LIVES.values() for form in _forms}
# The cue may come well after the thing it explains ("the bank was full of fish", "the seal is
# fine, i mean the little round filter"), so it gets the whole sentence rather than the few words
# beside the word that SENSE_PAIRS uses. A cue anywhere in the line is part of what the line is
# about, which is what the person meant by reading the whole sentence.
TWO_LIVES_REACH = 99
# What has to follow the word for it to be the subject of the line: "the bank was closed" and
# "the seal is broken" are states of that thing. A word that is only somewhere the person went
# past ("we walked past the bank") is not the subject of anything, and is left alone. The money
# verbs a bank does are in the money cues, so "the bank said no" still reads as the bank.
_A_STATE_VERB = frozenset("""is are was were has have had looks seems seemed becomes became
    sounds feels closed shut broke broken breaks split splits tore torn worn wears""".split())
# A possessive settles the one word whose two lives cannot be owned: "my bank" is the money
# bank, because nobody says "my bank" about the ground beside a river. The word still has its
# two lives with an article ("the bank was closed"), so this is not a cue for the line; it is a
# rule about what the owner says. "my seal is broken" is left alone: a person can own a seal.
_THE_OWNER_SETTLES = frozenset(("bank",))
_POSSESSIVE = frozenset("my our your his her their".split())
# What a first word can be without being the subject: the articles and the speaker.
_NOT_THE_SUBJECT = frozenset("""a an the my our your his her their this that these those i we
    you he she they it there old new local main high street current former usual regular
    well so but and oh hmm actually honestly anyway right now then also just only even
    hi hello hey good morning afternoon evening please thanks thank perhaps maybe""".split())


def unclear_subject(norm, inherited=None, previous=None):
    """The two-life word the line leaves unsettled, or None.

    Only the first thing the line names, only when it is the subject of a state ("the bank was
    closed", "the seal is broken"), and only when no word in the line fits one of its lives and
    the conversation has not already settled on a subject. A line with a cue ("my bank account",
    "the seal on the fridge door") is not unclear, and neither is a line that only passes the
    word by ("we walked past the bank").
    """
    content = [at for at, word in enumerate(norm) if word not in _NOT_THE_SUBJECT]
    if not content:
        return None
    first = content[0]
    word = norm[first]
    tiers = TWO_LIVES_FORMS.get(word)
    if not tiers:
        return None
    if word in _THE_OWNER_SETTLES and first and norm[first - 1] in _POSSESSIVE:
        # "my bank is closed" is the money bank; the owner settled it without a cue word.
        return None
    if inherited and any(inherited in sense_topics for _cues, sense_topics in tiers):
        # The chat is already on one of this word's lives: "my mortgage..." then "the bank said
        # no" is the money bank, and asking which one now would be asking them to repeat what the
        # conversation is about. A chat that is on some other topic does not settle this word,
        # so "my bank account is closed" then "the seal is broken" still says it is not sure.
        return None
    if previous:
        # The line before it can settle the word without naming it again: "how do i set up apple
        # pay" then "my bank isnt in the list" is the money bank, and the cue "pay" is what says
        # so. Only the last line is used, because an older cue can be a different subject.
        before = set(previous.get("norm") or ())
        if any(before & cues for cues, _sense_topics in tiers):
            return None
    after = [norm[at] for at in content[1:9]]
    if not any(other in _A_STATE_VERB for other in after):
        return None
    if any(_sense_cue(norm, [first], ((TWO_LIVES_REACH, cues),))
           for cues, _sense_topics in tiers):
        return None
    return word


# A word can name a dish and a thing of another kind, and then the words around it say which:
# "a pie chart", "the traffic jam", "the chips are down", "a yeast infection", "nails for the
# shelf". Each word below keeps the weight it has unless one of its own cues sits near it, so
# "how do i make a pie" is still the kitchen and "a pie chart in the report" is not. The cue sets
# are small on purpose: a word that fits both readings is not a cue.
SENSE_ELSEWHERE = {
    # A pie is a dish and a chart, and only a chart is measured in a percentage.
    "pie": (("pie", "pies"), (
        (SENSE_NEAR, frozenset("chart charts graph graphs diagram diagrams".split())),
    )),
    # Jam is a set jam, and the other ones are the queue on the road and being in a jam at
    # work, which is neither of them.
    "jam": (("jam", "jams"), (
        (SENSE_NEAR, frozenset("traffic queued stuck pickle spot trouble bind work".split())),
    )),
    # "The chips are down" is not dinner, and a chip can be the thing you bet with.
    "chips": (("chip", "chips"), (
        (SENSE_NEAR, frozenset("down poker casino betting stack stacks".split())),
    )),
    # Yeast is for bread, except where it is an infection.
    "yeast": (("yeast",), (
        (SENSE_NEAR, frozenset("infection infections thrush".split())),
    )),
    # A nail is on a finger and it is also what you knock into a wall.
    "nails": (("nail", "nails"), (
        (SENSE_REACH, frozenset("""shelf hammer wooden wood wall walls box boxes diy rawlplug
            plasterboard studwork picture pictures hang hanging screws screw""".split())),
    )),
    # A breast of chicken is the butcher's, and the body's been said to have a lump. The words
    # below are the ones only a body has: "how do i check my breasts for lumps" is a person
    # asking about themselves, and "are chicken breasts in milk ok" keeps the milk, because a
    # cut of chicken is not sore, aching or checked.
    "breast": (("breast", "breasts"), (
        (SENSE_REACH, frozenset("""lump lumps cancer nipple nipples areola sore hurting hurt
            hurts painful ache aches aching swelling discharge mastitis checked checking scan
            mammogram""".split())),
        # "breast milk" and "breast feeding" are the body's only when the two words touch: a
        # cut of chicken goes in a milk marinade all the time, so "chicken breasts in milk" is
        # still dinner.
        (SENSE_NEAR, frozenset("milk feeding breastfeeding fed".split())),
    )),
    # Spam is a junk email, and the post at the door is junk mail: "so much spam in the post"
    # names no screen at all.
    "spam": (("spam",), (
        (SENSE_REACH, frozenset("post letter letters envelope envelopes doormat junk pile".split())),
    )),
    # Thighs are the body when they are tight, sore or aching, and the pan when they are not.
    "thighs": (("thigh", "thighs"), (
        (SENSE_NEAR, frozenset("""tight sore ache aches aching hurt hurts hurting cramp cramps
            chafing""".split())),
    )),
    # Icing is for a cake, and icing a knee is the bag of frozen peas.
    "icing": (("icing",), (
        (SENSE_REACH, frozenset("""knee knees ankle ankles shoulder elbow muscle muscles
            injury injured swelling sprain bruise bruising hurt hurts""".split())),
    )),
    # Fibre is the roughage in a meal and it is the cable to the house.
    "fibre": (("fibre", "fiber"), (
        (SENSE_REACH, frozenset("""broadband internet router connection cable provider
            install installed""".split())),
    )),
}


# "Teething problems with the new boiler" is a new thing's early faults, not a baby's gums, and
# the word is the family's only where the child is: "my baby is teething", "she is teething". A
# fault phrase with no child in the line is about the thing that is new, so `teething` stops
# naming the family there and the machine it is next to takes the line.
TEETHING_IS_A_FAULT = frozenset("""problem problems trouble troubles fault faults
    niggles issues""".split())
TEETHING_AND_A_CHILD = frozenset("""baby babies child children kid kids toddler toddlers
    son daughter newborn girl boy he she his her their ours""".split())


def _teething_is_a_fault(norm):
    """True when "teething" is a new thing finding its feet, not a child cutting teeth."""
    return bool(set(norm) & TEETHING_IS_A_FAULT) and not set(norm) & TEETHING_AND_A_CHILD


# Every form of every two-life word, so the plural is found as well as the singular: the table
# is keyed on one form, and `_means_something_else` looked the word in it directly, so "a pie
# chart" stood down and "two pie charts" did not, and "how do i check my breasts for lumps"
# kept "breasts" as dinner while "a lump in my breast" did not keep it.
SENSE_ELSEWHERE_FORMS = {form: tiers for _forms, tiers in SENSE_ELSEWHERE.values()
                         for form in _forms}


# The two-life words that are body parts. "how do i check my breasts" carries no cue word at
# all - "check" is the commonest word in a cooking line too ("how do i check chicken breasts are
# cooked") - but "my", "her", "his" in front of one is the body every time: nobody says "my
# breasts" about a cut of chicken.
BODY_TWO_LIFE = frozenset("breast breasts thigh thighs".split())
OWNING_WORDS = frozenset("my her his their your our".split())


# How warm somebody is, said as how they are, is not the illness the same word also names. The
# word cannot decide it - "cold" is both - so the whole sentence does: an illness is something
# somebody HAS ("my mum has a cold", "caught a cold", "full of cold"), and a person BEING cold
# is the warmth. Reading it off the word alone had a mum who needed a jumper answered with "For
# a cold, the things that genuinely help are rest, plenty of fluids, honey in warm water for a
# cough", and "the kids are cold" answered with the child-with-a-cold card.
# The words that say how warm somebody is, when the word is used of a person: "cold" is the one
# that also names the illness, and the rest are the same state said harder.
COLD_WORDS = frozenset("cold freezing frozen chilled".split())
# The other side of the same question: a person who is hot, boiling or shivery is a temperature.
# "shivering" and "shivery" are here rather than with the cold on purpose - they are a symptom,
# and a shivering child is a fever question rather than a blanket one.
HOT_WORDS = frozenset("""hot boiling roasting sweltering sweaty sweating shivery shivering
    feverish""".split())
WARMTH_WORDS = COLD_WORDS | HOT_WORDS
# The words that stand between the person and the warmth, and the ones that say how they are
# rather than what they have.
WARMTH_ARE = frozenset("is are was were am feeling getting being".split()) | frozenset(
    "feel feels felt".split())
WARMTH_DEGREE = frozenset("""a bit lot little tad wee touch really so very too proper bloody
    freezing stone quite that dead still always absolutely proper""".split())
# The words that make it a habit rather than today, on either side. A mum who is always cold is
# how she runs - the same answer "cold all the time" gets - and a dad who is always hot is the
# same question from the other end, not a fever, which is never "always". So a warmth with one of
# these between the person and the word is not this turn's question.
WARMTH_HABITUAL = frozenset("always still".split())
# What may follow the warmth and leave it the warmth: nothing, or when it was. "all the time",
# "since tuesday" and "and shivery" each say something more, and each of those is the other
# reading - a pattern for the doctor, or a second symptom.
WARMTH_THEN = frozenset("""now today tonight again too still here outside lately""".split())
# Who can be cold: a person, never a thing (a radiator, a room and a fridge are a heating
# question) and never a part of the body, which is circulation ("my hands are cold").
COLD_PEOPLE = frozenset("""i im i'm iam me she he they we you u everyone everybody someone
    somebody people""".split())


def the_warmth_said(norm):
    """The word for how warm somebody is, when that is what the line says: "cold", "hot", else None.

    Read over the whole sentence rather than the word: a person, then is/are/feels, then the
    warmth with no more than a degree word or two in between, then nothing but when it was. So
    "my mum is cold" and "the kids are cold" are the warmth, and "my mum has a cold", "my mum
    is full of cold", "my mum is cold all the time" and "my hands are cold" are all something
    else and keep the reading they had. A habit is not this turn's question either: "my mum is
    always cold" runs like "cold all the time" and "my dad is always hot" runs like it too. The
    hot side answers the same question from the other end: "my nan is boiling" and "my son is
    shivery" are a temperature to take, not a shrug.
    """
    for at, word in enumerate(norm):
        if word not in WARMTH_WORDS:
            continue
        back = at - 1
        habit = False
        while back >= 0 and norm[back] in WARMTH_DEGREE:
            if norm[back] in WARMTH_HABITUAL:
                habit = True
            back -= 1
        if back < 1 or norm[back] not in WARMTH_ARE:
            continue
        if habit:
            # "my mum is always cold" and "my dad is always hot" are how they run, not this
            # turn's question: the cold row leaves a habit to the thyroid answer, and a fever
            # is never "always".
            continue
        who = norm[back - 1]
        if who in COLD_PEOPLE:
            person = True
        elif who in PERSON_WORDS:
            person = True
        elif who.endswith("s") and who[:-1] in PERSON_WORDS:
            person = True
        else:
            person = False
        if not person:
            continue
        rest = [word for word in norm[at + 1:] if word not in WARMTH_THEN]
        if rest and rest[0] not in (".", "!", "?", ","):
            continue
        return word
    return None


def _means_something_else(norm, position):
    """True when the word at `position` names another thing in this line (SENSE_ELSEWHERE)."""
    if norm[position] == "teething" and _teething_is_a_fault(norm):
        return True
    tiers = SENSE_ELSEWHERE_FORMS.get(norm[position])
    if not tiers:
        return False
    if (norm[position] in BODY_TWO_LIFE and position and norm[position - 1] in OWNING_WORDS):
        return True
    return _sense_cue(norm, [position], tiers)


def says_another_thing(text):
    """The two-life words in a line that a cue has taken to their other life, as a set.

    `text` is a normalised line, so the words are split on anything that is not one.
    """
    norm = [word for word in re.split(r"[^a-z0-9]+", str(text or "").lower()) if word]
    return {norm[at] for at in names_another_thing(norm)}


def names_another_thing(norm):
    """The positions in `norm` of two-life words a cue has taken to their other life.

    The topics read drops these words; a table that looks for a dish by name has its own match
    and needs the same answer, or "how do i check my breasts for lumps" keeps the chicken and
    "a lump in my breast" does not.
    """
    return frozenset(at for at, word in enumerate(norm)
                     if word in SENSE_ELSEWHERE_FORMS
                     and _means_something_else(norm, at))


# A word can name an animal and a machine at once, and then the line, not the word, says which.
# "mouse" is the one people meet every day: "my mouse isnt working" was sent to a pest
# controller, "i lost my mouse" was answered with sympathy for a bereavement and "my mouse
# battery is dead" got the car battery. Every reader that treats the word as an animal asks
# `is_a_machine_word` first, so the pest line, the vet line, the grief line and the car line all
# stand aside for the same reason, once.
# The plural is the household: people write "we have mice in the kitchen" and nobody types
# "mice" about a computer part, so "mice" alone settles it, and the words that only fit a pest
# or a pet outrank the singular. Anything else is the device, because that is what the word means
# nine times in ten.
MACHINE_WORD_CUES = {
    "mouse": frozenset("""mice kitchen loft attic shed garage garden cupboard bedroom house home
        flat wall walls nest trap traps mousetrap droppings infestation pest pests rodent
        rodents chewing chewed scurrying poison wild tame pet pets caught catch cat cats dog
        dogs cage hutch tank vet alive ran running escape escaped squeak squeaking bait cheese
        bins bin cavity floorboards floorboard living saw seen""".split()),
}
# Two words that only fit the animal together: "we have a mouse problem" is a household, while
# "i have a problem with my mouse" is the device, so "problem" on its own cannot be the cue.
MACHINE_WORD_PHRASES = ("mouse problem", "mouse problems", "mice problem", "mice problems",
                        "mouse infestation", "mouse in the", "mouse in my", "mice in the",
                        "mice in my", "rid of mice", "rid of the mouse", "mouse trap")


def is_a_machine_word(text):
    """True when the line's "mouse" is the computer part, not the animal.

    "my mouse isnt working", "i lost my mouse" and "my mouse battery is dead" are the device;
    "we have mice in the kitchen", "my cat caught a mouse" and "my pet mouse died" are not.
    A line with no cue at all ("my mouse") is read as the device, which is the everyday meaning.
    """
    said = str(text or "").lower().replace("'", "")
    words = set(re.split(r"[^a-z]+", said))
    if "mouse" not in words and "mice" not in words and "mousepad" not in words:
        return False
    if "mice" in words:
        return False
    if any(phrase in said for phrase in MACHINE_WORD_PHRASES):
        return False
    return not (words & MACHINE_WORD_CUES["mouse"])


# A phrase that only asks who is being asked says nothing about the subject, so it is worth no
# more than one ordinary word: "do you think it is the filter" is about the filter.
ASK_PHRASES = frozenset(["any ideas", "do you think"])
# A phrase made only of everyday verbs names no subject of its own either: "keeps dropping" was
# the phone line's, but prices, temperatures, moods and boiler pressure all keep dropping, and
# the thing that keeps dropping is what the line is about. Such a phrase is still evidence, but
# only as much as one ordinary word, so a subject the line does name outranks it.
ORDINARY_VERBS = frozenset("""keep keeps kept drop drops dropped dropping fall falls falling
    cut cuts cutting stop stops stopped start starts started go goes going get gets getting
    turn turns turned work works worked show shows showed""".split())


_SENSE_TIERS = {}
for _forms, _sense_topic, _tiers in SENSE_PAIRS.values():
    for _form in _forms:
        _SENSE_TIERS.setdefault(_form, []).append((_sense_topic, _tiers))


def _the_sense_the_cues_name(norm, position, word):
    """True when a cue word beside this one names the other sense of a two-life word.

    "a mole in the garden" is the lawn's, though "mole" on its own is the doctor's, and "the
    stock market" is money though "stock" alone is the shop's. The word keeps its own weight
    only where nothing beside it says which thing is meant.
    """
    for _topic, tiers in _SENSE_TIERS.get(word, ()):
        if _sense_cue(norm, [position], tiers):
            return True
    return False


def _sense_cue(norm, positions, tiers):
    """True when a cue word sits near one of the two-life words (see SENSE_PAIRS)."""
    for cue_at, word in enumerate(norm):
        for reach, cues in tiers:
            if word not in cues:
                continue
            for spot in positions:
                if spot - reach <= cue_at <= spot + reach:
                    return True
    return False


def _index():
    """word/phrase -> [(topic, weight)], built once from the data above."""
    table = {}

    def add(key, topic, weight):
        # One entry per word and topic, at its strongest weight: a word listed in both
        # STRONG and WEAK of a topic says the same thing twice, and a sum nobody chose is
        # a weight the data does not explain.
        entries = table.setdefault(key, [])
        for index, (seen, points) in enumerate(entries):
            if seen == topic:
                if weight > points:
                    entries[index] = (topic, weight)
                return
        entries.append((topic, weight))

    for topic, words in STRONG.items():
        for word in words.split():
            if word not in GENERIC:
                add(word, topic, 2)
    for topic, words in WEAK.items():
        for word in words.split():
            if word not in GENERIC:
                add(word, topic, 1)
    for name in CAR_NAMES:
        add(name, "cars", 2)
    for topic, phrases in PHRASES.items():
        for phrase in phrases:
            key = " ".join(_BREAKS.sub(" ", phrase).split())
            if key and key not in GENERIC:
                ordinary = all(word in ORDINARY_VERBS for word in key.split())
                add(key, topic, 1 if key in ASK_PHRASES or ordinary else 3)
    return table


# The make and the model a car is called by. "my punto makes a clicking noise when i turn" named
# a car as plainly as "my car" does, but the word is not in the list above and the line read as
# naming nothing at all: the topic came out None, the follow-up "is it safe to drive" then took
# `drive` for travel, and "what will it cost roughly" answered with the cost of driving lessons
# rather than a garage bill. `my audi needs a service`, `my corsa wont start` and `i drive a
# punto` all read the same way. A make is the car in every sentence it appears in, so it points
# at the topic the way `car` does.
#
# Only the names that mean nothing else are here. A model that is also an ordinary word or an
# animal is left out and read by the words round it: golf, polo, beetle, mustang, jaguar, mini,
# seat, rover, smart, focus, fiesta, escort, transit, discovery, defender, galaxy, yeti, superb,
# note, leaf, rio. `mg` is left out as too short to tell from a typo of "me".
CAR_NAMES = frozenset("""audi fords ford vauxhall toyota honda nissan renault peugeot citroen
    skoda hyundai kia mazda volvo suzuki bmw mercedes volkswagen vw fiat tesla dacia chevrolet
    chrysler dodge subaru mitsubishi lexus saab alfa jeep bentley porsche ferrari lamborghini
    aston lada daewoo infiniti acura punto corsa clio astra mondeo passat micra yaris fabia
    octavia ibiza qashqai juke captur kadjar sandero duster sprinter picanto zafira insignia
    vectra laguna megane berlingo picasso cupra leon toledo kamiq karoq kodiaq tucson sportage
    camaro impreza forester hilux auris avensis prius celica supra aygo navara""".split())


TABLE = _index()


def _takes_an_object(norm, position):
    """True when a word at `position` is followed by a determiner and the thing it names."""
    return position + 1 < len(norm) and norm[position + 1] in DETERMINERS


def _acts_on_a_thing(topic, words, norm, start):
    """True when a verb cue in these words is followed by the thing it acts on: "revise my cv".
    The test runs after the cue itself, not after the whole phrase."""
    for offset, word in enumerate(words):
        if word in VERB_CUES.get(topic, ()):
            return _takes_an_object(norm, start + offset)
    return False


# A determiner phrase can say how much rather than what: "bleeding a lot", "bleed a bit",
# "burnt a little". Those are not the thing the cue acts on, so they leave the cue about the
# body, while "a lot of the carpet" names the carpet after the quantity.
DEGREE_NOUNS = frozenset("lot lots bit little much few couple plenty".split())


def _thing_a_cue_acts_on(norm, position):
    """The head noun of the thing after a cue, or "" when it names nothing: "the pan",
    "the bottom of the pan" -> pan."""
    if not _takes_an_object(norm, position):
        return ""
    index = position + 2
    noun = norm[index] if index < len(norm) else ""
    if noun in DEGREE_NOUNS and not (index + 1 < len(norm) and norm[index + 1] == "of"):
        return ""
    while index + 1 < len(norm) and norm[index + 1] == "of":
        index += 2
        if index < len(norm) and norm[index] in DETERMINERS:
            index += 1
        noun = norm[index] if index < len(norm) else noun
    return noun


def _acts_on_the_body(norm, position):
    """True when a burn or a cut at `position` is on the body, or names nothing at all."""
    thing = _thing_a_cue_acts_on(norm, position)
    if thing:
        return thing in BODY_OR_SELF
    # No determiner after the cue, so the word there is not an object but the thing the cue
    # describes: "the wood burning stove", "a burning smell", "burnt toast". A body word is the
    # body ("burnt hands"), and a word that carries on the thought ("burnt and sore") says
    # nothing about what is burnt, so it keeps the reading.
    after = norm[position + 1:position + 2]
    if after and after[0] not in BODY_OR_SELF and after[0] not in CUE_CARRIERS:
        # The cue describes that noun, so health is not what this word says - but only when the
        # line names something else to be about: "a cut avocado" names nothing the reader knows,
        # and losing the only reading there is worse than keeping a weak one.
        others = {topic for index, word in enumerate(norm)
                  if index != position and word not in POLY_FORMS
                  for topic, weight in _lookup(word)
                  if weight >= 2 and topic not in ("health", "small-talk")}
        return not others
    return True


# "run out of" is not exercise. The fitness vocabulary carries `run`, so "i have run out of
# washing powder", "we ran out of milk" and "im running out of time" were all read as being about
# running, and the topic decides which knowledge domains are allowed to answer the line: the
# household question went to the running answers. The word is dropped only when `out` comes
# straight after it, which is the phrasal verb every time; "how far should i run" and "i run three
# times a week" keep their fitness reading.
RUN_OUT_BEFORE = frozenset("run runs running ran".split())


def _is_run_out(norm, position):
    """True when the word at `position` is the `run` of "run out of" rather than a run."""
    return (norm[position] in RUN_OUT_BEFORE and position + 1 < len(norm)
            and norm[position + 1] == "out")


# "watch for" is not watching something. "what should i watch for" after "my dad had a stroke"
# was read as a request for something to watch - the entertainment phrase "what should i watch"
# matched, the line named a topic of its own, and the signs to look out for after a stroke became
# a shrug about telly. The phrase is the same words either way; what comes after the verb is what
# says which verb it is, and only a `for` or an `out` can turn watching something into watching
# out for something.
WATCH_OUT_AFTER = frozenset("for out".split())
WATCHING = frozenset("watch watches watching watched".split())


def _watches_out_for(words, norm, end):
    """True when the watching in this phrase is followed by the for or out of "watch for"."""
    return (words[-1:] and words[-1] in WATCHING
            and end < len(norm) and norm[end] in WATCH_OUT_AFTER)



def _says_nothing_here(topic, words, norm, start, study):
    """True when this word or phrase cannot name `topic` in this line: the same words are an
    ordinary verb here, and the line does not say what they act on."""
    if _watches_out_for(words, norm, start + len(words)):
        # The verb is "watch for", so the line is about what to look out for, not about a
        # programme: "what should i watch for" is the signs after a stroke or a medicine.
        return True
    if topic == "family-and-parenting" and "health visitor" in " ".join(words):
        # The health visitor is who a parent rings about the baby, and she is also the person
        # a line about a rash, a weight or a medicine names. A line that names something wrong
        # with the child is a health line, not a line about the family, so the phrase never
        # takes the subject from a sign or a medicine.
        # The "health" of "health visitor" is her name, not something wrong with the child,
        # so it is taken out before the line is read for a sign or a medicine.
        rest = " ".join(norm).replace("health visitor", " ").replace("health visitors", " ")
        for word in rest.split():
            if any(topic_ == "health" and weight >= 2 for topic_, weight in _lookup(word)):
                return True
    if len(words) == 1 and words[0] in BODY_CUES:
        return not _acts_on_the_body(norm, start)
    if any(word in VERB_CUES.get(topic, ()) for word in words):
        return _acts_on_a_thing(topic, words, norm, start) and not study
    return False


# A travel verb that takes a person and then a mad-word is the idiom, not a journey: "its
# driving me mad", "the kids are driving us up the wall", "that noise is driving him potty".
# The travel vocabulary cannot help it, because the word on its own is a journey
# ("driving to scotland"), so the person-and-mood shape is what rules the journey out.
DRIVEN_PERSON = frozenset("me us him her them you u everyone everybody".split())
DRIVEN_MOOD = frozenset("""mad insane crazy nuts bonkers barmy potty daft distracted wild
    spare""".split())
DRIVEN_TAIL = frozenset("wall walls bend".split())
DRIVEN_JOINERS = frozenset("up round around over".split())
DRIVES = frozenset("drive drives driving drove driven".split())
# An age is a child's when the number sits directly after a determiner or possessive ("a 7 year
# old", "my 3 year old"), and a thing's when it is predicative ("its about five years old",
# "the boiler is 12 years old"). Only the first is about a person, so only the first is family:
# a machine's age must not make the conversation about children.
AGE_NOUNS = frozenset("year years yr yrs month months mth mths week weeks wk wks".split())
# How many of each unit there are in a year, so an age is read in years however it is said:
# "my 4 month old" and "my 3 week old" are babies, and a 200 year old house is still a house.
AGE_IN_A_YEAR = {"year": 1, "years": 1, "yr": 1, "yrs": 1,
                 "month": 12, "months": 12, "mth": 12, "mths": 12,
                 "week": 52, "weeks": 52, "wk": 52, "wks": 52}
A_CHILD_TILL = 19      # in years: past this the person is a grown-up of their own
# The words that say the age is the child's own: "a 6 week old baby routine" names a baby the
# age belongs to. Any other thing after "old" is what the age is of - "a 10 week old kitten"
# is a kitten and "my 6 month old dog" is a dog - and the line is about it, not about a child.
AGE_OF_A_CHILD_WORDS = frozenset("""baby babies child children kid kids toddler toddlers
    infant infants newborn boy girl son daughter grandchild lad lass""".split())
# The words that make the age one of the speaker's own people: "my 4 month old" names the child,
# "a 3 year old" says what the week away or the class is for.
THE_PERSONS_OWN = frozenset("my our his her their".split())
AGE_AFTER = frozenset("is are was were be been about turned turns nearly almost just only".split())


def _age_value(word):
    """The number a child's age is said with, or a large value when it is not a small count."""
    value = WORD_NUMBERS.get(word)
    if value is None:
        digits = WORD_DIGITS.match(word)
        value = float(digits.group(0).replace(",", ".")) if digits else 99
    return value


def _ages_of_a_child(norm):
    """The positions of a "a 7 year old" in this line: a child, not a machine's age."""
    ages = []
    for position, word in enumerate(norm):
        if word not in AGE_NOUNS or position == 0 or position + 1 >= len(norm):
            continue
        if norm[position + 1] != "old":
            continue
        number_at = position - 1
        if norm[number_at] in AGE_AFTER:
            continue
        if number_at == 0 or norm[number_at - 1] not in DETERMINERS:
            continue
        if _age_value(norm[number_at]) / AGE_IN_A_YEAR[word] > A_CHILD_TILL:
            continue          # "a 200 year old house" is the house, not a child
        ages.append(number_at)
    return ages


# "book for a 10 year old" is the same question as "books for a 10 year old": the thing wanted
# is a book, and the child is who it is for. The plural phrase was in the list and the singular
# was not, so the line named no topic and the memory store counted the child back at them ("One
# kid, ten"). The book has to sit directly before "for", which keeps the verb out: "can you book
# a table for 4" and "book a flight for a 10 year old" are bookings, not reading.
BOOK_WORDS = frozenset("book books novel novels".split())
A_CHILD_TO_READ_FOR = frozenset("""child children kid kids baby toddler boy girl son
    daughter niece nephew grandson granddaughter grandchild teenager teen""".split())


def _a_book_for_a_child(norm, child_ages):
    """The position of "book for a 10 year old" in this line, or None."""
    for position, word in enumerate(norm):
        if word not in BOOK_WORDS or norm[position + 1:position + 2] != ["for"]:
            continue
        after = position + 2
        tail = norm[after:after + 5]
        if set(tail) & A_CHILD_TO_READ_FOR:
            return position
        if any(after <= age <= after + 3 for age in child_ages):
            return position
        if "year" in tail and ("old" in tail or "olds" in tail):
            return position
    return None


def _drives_a_person(norm, position):
    """True for "driving me mad": a person object and then a mood, not a destination."""
    if norm[position] not in DRIVES:
        return False
    if norm[position + 1:position + 2] != [] and norm[position + 1] not in DRIVEN_PERSON:
        return False
    if not norm[position + 1:position + 2]:
        return False
    tail = norm[position + 2:position + 7]
    return bool(set(tail) & DRIVEN_MOOD
                or (set(tail) & DRIVEN_TAIL and set(tail) & DRIVEN_JOINERS))


# A phrase whose words are not about the things they usually name. "run off my feet" is a busy
# week, not a foot and not a run; "over the moon" is pleased, not the sky; "a piece of cake" is
# an easy exam, not a bake. The words inside the phrase are taken out before the topic is scored,
# and what the line names outside it decides, the same way `_drive_idiom` handles "driving me up
# the wall".
IDIOM_PHRASES = (
    # being rushed is not exercise, and the feet in it are not feet
    ("run", "off", "my", "feet"), ("run", "off", "our", "feet"),
    ("run", "off", "your", "feet"), ("running", "off", "my", "feet"),
    ("rushed", "off", "my", "feet"), ("rushed", "off", "our", "feet"),
    ("pushed", "off", "my", "feet"), ("ran", "off", "my", "feet"),
    ("on", "my", "feet", "all", "day"), ("on", "our", "feet", "all", "day"),
    ("on", "my", "feet", "all", "week"), ("up", "on", "my", "feet"),
    ("run", "ragged"), ("running", "ragged"), ("ran", "ragged"),
    # the feet in these are the whole person, standing, recovering or nervous
    ("dead", "on", "my", "feet"), ("dead", "on", "her", "feet"),
    ("dead", "on", "his", "feet"), ("dead", "on", "their", "feet"),
    ("back", "on", "my", "feet"), ("back", "on", "his", "feet"),
    ("back", "on", "her", "feet"), ("back", "on", "its", "feet"),
    ("back", "on", "their", "feet"), ("back", "on", "our", "feet"),
    ("find", "my", "feet"), ("finding", "my", "feet"), ("found", "my", "feet"),
    ("two", "left", "feet"), ("swept", "off", "my", "feet"),
    ("swept", "me", "off", "my", "feet"),
    ("cold", "feet"), ("cold", "turkey"),
    # too much of a thing is not the thing
    ("snowed", "under"), ("snowed", "under", "with"), ("under", "the", "weather"),
    ("under", "my", "belt"), ("out", "of", "my", "depth"), ("out", "of", "our", "depth"),
    ("at", "my", "wits", "end"), ("at", "our", "wits", "end"), ("at", "wits", "end"),
    ("on", "the", "fence"), ("in", "two", "minds"), ("on", "the", "same", "page"),
    ("over", "the", "moon"), ("in", "the", "same", "boat"),
    ("doing", "my", "head", "in"), ("doing", "my", "nut", "in"),
    ("does", "my", "head", "in"), ("doing", "his", "head", "in"),
    ("doing", "her", "head", "in"), ("doing", "our", "head", "in"),
    # a food word that is not food
    ("a", "piece", "of", "cake"), ("piece", "of", "cake"), ("easy", "as", "pie"),
    ("spill", "the", "beans"), ("spilling", "the", "beans"), ("spilled", "the", "beans"),
    ("not", "my", "cup", "of", "tea"), ("my", "cup", "of", "tea"),
    ("the", "icing", "on", "the", "cake"), ("icing", "on", "the", "cake"),
    ("cherry", "on", "the", "cake"), ("half", "baked", "idea"),
    ("the", "last", "straw"), ("a", "storm", "in", "a", "teacup"),
    # a body word that is not a body
    ("a", "pain", "in", "the", "neck"), ("a", "pain", "in", "the", "backside"),
    ("music", "to", "my", "ears"), ("a", "shot", "in", "the", "arm"),
    ("the", "tip", "of", "the", "iceberg"), ("a", "drop", "in", "the", "ocean"),
    ("a", "grey", "area"), ("off", "the", "rails"), ("off", "the", "boil"),
    # a body word that belongs to a thing. "my washing machine is noisy" / "its on its last legs"
    # / "is it worth fixing" rang 111: the composer's thread reader takes any word in `BODY_PARTS`
    # as a body, and "legs" is one, so the machine on the table became a person who needs a
    # doctor. The possessive is what tells the two apart, so only the thing's form is here:
    # "the boiler is on its last legs" is a machine wearing out, and "im on my last legs" is the
    # speaker, which stays a body thread and keeps the health answer.
    ("on", "its", "last", "legs"), ("on", "their", "last", "legs"),
)


def _idiom_positions(norm):
    """The positions taken by a phrase in `IDIOM_PHRASES`, or an empty set.

    Only a whole phrase counts, so `moon` on its own is still the sky, `cake` on its own is
    still to eat, and `my feet are killing me` is still about feet.
    """
    spots = set()
    joined = " " + " ".join(norm) + " "
    for phrase in IDIOM_PHRASES:
        needle = " " + " ".join(phrase) + " "
        start = 0
        while True:
            at = joined.find(needle, start)
            if at < 0:
                break
            spots.update(range(len(joined[:at].split()), len(joined[:at].split()) + len(phrase)))
            start = at + 1
    return spots


def _bad_verdict_positions(norm):
    """The positions of a verdict on a thing: "my landlord is a joke", "the nhs is a shambles".

    The noun is what the person thinks of the thing they named, and it is not the subject of the
    line: "the nhs is a joke" is about the nhs, and read as a line about a joke it went to the
    punchline pool. Nothing inside the verdict scores a topic or names an entity, which is what
    makes "is a joke" a comment on the thing in front of it.
    """
    return {position for position in range(len(norm)) if a_bad_verdict(norm, position)}


def _drive_idiom(norm):
    """The positions of a "driving me up the wall" idiom: its verb, its person and its mood.

    Inside the idiom no word names a thing: `wall` is not the wall of a house and `bend` is not
    a road, so a line made of the idiom alone (`driving me up the wall`, `shes driving me round
    the bend`) must not be read as home-and-diy or a journey. The idiom says how the speaker
    feels, and the topic comes from whatever the line names outside it (`the kids are driving me
    up the wall` is still family-and-parenting).
    """
    idiom = set()
    for position in range(len(norm)):
        if not _drives_a_person(norm, position):
            continue
        idiom.update((position, position + 1))
        for offset in range(position + 2, min(position + 7, len(norm))):
            if norm[offset] in DRIVEN_MOOD or norm[offset] in DRIVEN_TAIL \
                    or norm[offset] in DRIVEN_JOINERS:
                idiom.add(offset)
    return idiom



# "sick of" and "tired of" name the thing the person has had enough of, not what is wrong with
# them: "im sick of it" is not a health line and "im tired of waiting" is not a sleep line. Only
# the word in front of one of these says so ("sick with worry" is its own idiom, and a bare "im
# tired" is still the long day), and the thing named after it keeps its own topic, which is what
# the line is really about: "im sick of my job" is work.
COMPLAINT_OF = frozenset("sick tired bored weary".split())
COMPLAINT_OF_NEXT = frozenset("of with about".split())


# What comes out of a person is the gut's line, and the words for it are the words for what
# comes out of an animal too. "my poo has been green for a week" named no part of the body at
# all, so the only words left to match were "green" and "a week" and the line was answered with
# the salad-drawer advice; "the smell of dog poo in the garden" is the garden, and an animal
# takes the word. A person named as well ("my son hasnt pooed for two days") keeps it.
BODILY_OUTPUT = frozenset("""poo poos pooed pooing poop poops pooped pooping stool stools
    faeces feces turd turds bowels bowel""".split())
BODILY_OUTPUT_NOUN = BODILY_OUTPUT - frozenset("pooed pooped pooing pooping".split())
# A sample, a test or a pot is a thing being handed in, not a symptom: "my stool sample" is a
# line about the appointment and none of the gut words are the subject of it.
SAMPLE_WORDS = frozenset("""sample samples test tests tested testing kit pot container jar
    form forms""".split())


# A stool is a chair that has gone wobbly as often as it is anything else: "my stool is wobbly"
# is a leg to tighten, so the word beside the furniture words is not the person's own. Only the
# words that are a piece of furniture as well ("stool", "stools") are held off - "my poo is loose
# and my seat is sore" is still the gut - and only when the line says nothing else about the body.
STOOL_AS_FURNITURE = frozenset("""wobbly wobble wobbles wobbliest rickety leg legs joint joints
    seat seats wood wooden screw screws screwdriver tighten tight creak creaks squeak squeaks
    bracket glue chair chairs table tables bench furniture dresser sideboard carpenter flatpack
    kitchen""".split())
ONLY_A_STOOL = frozenset("stool stools".split())


def _is_a_complaint(norm, position):
    """True when the word at `position` is "sick of"/"tired of": a complaint, not a symptom."""
    if norm[position] not in COMPLAINT_OF:
        return False
    return position + 1 < len(norm) and norm[position + 1] in COMPLAINT_OF_NEXT


# The vocabulary is written once, by hand, and a line says the same word in another form: the
# list has "pregnancy" and the line says "pregnant", the list has "tired" and the line says
# "tiredness", the list has "cheap" and the line says "cheaper". One word family is one word, and
# a member of the family the list happens not to hold was read as no word at all: "im pregnant and
# my back aches" was read by the back ache alone, and "i think im pregnant" reached no topic, so
# the reply was a note of congratulation instead of the test. These are the endings a word takes
# on, read both ways: taken off the line's word ("tiredness" is "tired") and added to it to reach
# the form the list holds ("wash" is "washing").
DERIVED_ENDINGS = ("ness", "ment", "tion", "sion", "ity", "ance", "ence", "ancy", "ency",
                   "ism", "ist", "ful", "less", "ing", "ers", "ant", "ent", "er", "ed",
                   "cy", "ic", "al", "ly", "th", "y", "s")
# Two members of a family change more than the ending: "pregnant" and "pregnancy" share "pregn",
# "patient" and "patience" share "pati". These are the pairs a list may hold either end of.
FAMILY_PAIRS = (("ant", "ancy"), ("ent", "ency"), ("ate", "ation"), ("ate", "acy"),
                ("ive", "ion"), ("ible", "ibility"), ("able", "ability"))
# A stem shorter than this is not a family, it is a coincidence: "car" is not "care" and "art" is
# not "artist". Five letters is where a stem means something on its own.
FAMILY_STEM = 5
# The same bar for the line's word before an ending is added to it. Four letters was measured and
# refused: "part" became "party" and "meet" became "meeting", and every "part of the uk" line and
# "nice to meet you" line moved topic on the strength of it.
FAMILY_WORD = 5

_FUNCTION_WORDS = None


def _function_words():
    """The words that are only grammar: they are never another word with an ending on."""
    global _FUNCTION_WORDS
    if _FUNCTION_WORDS is None:
        try:
            from . import STOPWORDS     # a local import: the package holds it and imports this
            _FUNCTION_WORDS = frozenset(STOPWORDS)
        except Exception:
            _FUNCTION_WORDS = frozenset()
    return _FUNCTION_WORDS


def _family(word):
    """The table entries for another form of this word, if the list holds that form."""
    for ending in DERIVED_ENDINGS:
        if word.endswith(ending):
            stem = word[:-len(ending)]
            if len(stem) >= FAMILY_STEM:
                hit = TABLE.get(stem) or TABLE.get(stem + "e")
                if hit:
                    return hit
        # The line's word may be the shorter member: "cheap" is "cheaper". Never a word that is
        # only grammar: "should" is not "shoulder", and every "should i ..." line in the deck was
        # being handed to the health topic by that one ending.
        if len(word) >= FAMILY_WORD and word not in _function_words():
            hit = TABLE.get(word + ending)
            if hit:
                return hit
    for here, there in FAMILY_PAIRS:
        if word.endswith(here):
            hit = TABLE.get(word[:-len(here)] + there)
            if hit:
                return hit
        if word.endswith(there):
            hit = TABLE.get(word[:-len(there)] + here)
            if hit:
                return hit
    return ()


def _lookup(word):
    """The table entries for a word, also trying its singular and verb stem."""
    hit = TABLE.get(word)
    if hit:
        return hit
    for suffix, replacement in (("ies", "y"), ("es", ""), ("s", ""), ("ing", ""),
                                ("ing", "e"), ("ed", ""), ("ed", "e")):
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            hit = TABLE.get(word[:-len(suffix)] + replacement)
            if hit:
                return hit
    family = _family(word)
    if family:
        # The bot's own topic is what a line claims about the bot, not a word's other form:
        # "personal" is "person" with an ending on, and "personal alarm" is an alarm.
        return tuple((topic, weight) for topic, weight in family if topic != "about-the-bot")
    return ()


def _is_a_portion(norm, position):
    """True for "half a cabbage", "half the batter", "double the recipe".

    A quantity word in front of an article is a piece of a thing the line already names, which
    is not a sum: "ive got half a cabbage left, what can i do with it" is a cooking line. A
    figure after it ("half of 80") is arithmetic and keeps its full weight.
    """
    if norm[position] not in PORTION_WORDS:
        return False
    after = norm[position + 1:position + 3]
    if not after:
        return False
    if after[0] in ("a", "an", "the"):
        if len(after) > 1 and after[1] in PORTION_UNITS:
            return False        # "half a cup in ml" is a figure again, not a piece
        return True
    return after[0] == "of" and len(after) > 1 and after[1] in ("a", "an", "the")


def _the_weather_is_just_a_season(norm, text):
    """True when the only weather in the line is a season word.

    A season phrase ("in the spring", "next winter") counts as the season, not as weather of its
    own. A temperature or a sky word does not: "is it warm in the summer in spain" is still the
    weather.
    """
    spots = [at for at, word in enumerate(norm) if word in SEASONS]
    if not spots:
        return False
    if min(spots) <= 2:
        # A season that opens the line is the frame the rest of it happens in, and often its
        # subject: "in the spring the garden comes alive", "a dry winter is hard on the garden".
        return False
    if any(norm[at - 1] in WEATHER_BEFORE for at in spots if at):
        return False
    if any(word in WEATHER_ITSELF for word in norm):
        return False
    if any(word not in SEASONS and topic == "nature-and-weather" and weight >= 2
           for word in norm for topic, weight in _lookup(word)):
        return False
    return not any(
        key in text and not set(key.split()) & SEASONS
        for key, entries in TABLE.items() if " " in key
        and any(topic == "nature-and-weather" for topic, _weight in entries))


def score_topics(line, inherited=None):
    """[(topic, score, best weight)] for this line, best first.

    The best weight is the strongest single thing that pointed at the topic: 2 or more means a
    distinctive word or a phrase, 1 means only ordinary words (see `subject_topic`).
    """
    norm = line["norm"]
    text = " " + line["norm_text"] + " "
    sums = _work_out_sums(norm)
    study = bool(set(norm) & STUDY_OBJECTS)
    background = background_positions(norm)
    found, own = {}, {}

    def note(topic, weight, position, polysemous):
        score, top, first = found.get(topic, (0, 0, position))
        found[topic] = (score + weight, max(top, weight), first)
        if not polysemous:
            own[topic] = True

    forms_of = {form for forms, _topic, _tiers in SENSE_PAIRS.values() for form in forms}
    idiom = _drive_idiom(norm) | _idiom_positions(norm) | _bad_verdict_positions(norm)
    child_ages = _ages_of_a_child(norm)
    for position, word in enumerate(norm):
        if position in sums or position in background or position in idiom:
            continue
        if _is_run_out(norm, position):
            continue            # "run out of milk" is not a run (see RUN_OUT_BEFORE)
        if _is_a_complaint(norm, position):
            continue            # "sick of it" is fed up, not ill
        if word in PLACES and _names_a_person(norm, position):
            continue            # "my mate paris is visiting" is a friend, not the city
        elsewhere = _means_something_else(norm, position)
        if word in WARMTH_WORDS and the_warmth_said(norm):
            # how warm somebody is, not the illness the word also names (see below)
            elsewhere = True
        if word in forms_of and _the_sense_the_cues_name(norm, position, word):
            continue        # the cues beside the word say which sense it is (see SENSE_PAIRS)
        for topic, weight in _lookup(word):
            if elsewhere:
                continue  # "a pie chart", "the traffic jam": the word names something else here
            if _says_nothing_here(topic, [word], norm, position, study):
                continue  # a verb whose object the line does not name
            note(topic, weight, position,
                 word in POLY_FORMS or _is_a_portion(norm, position))
    for forms, sense_topic, tiers in SENSE_PAIRS.values():
        spots = [at for at, word in enumerate(norm) if word in forms_of and word in forms]
        if spots and _sense_cue(norm, spots, tiers):
            note(sense_topic, SENSE_WEIGHT, spots[0], False)
    family_score = found.get("family-and-parenting", (0, 0, 0))[0]
    if child_ages and (family_score >= 2 or not any(
            score >= 2 for topic, (score, _top, _first) in found.items()
            if topic not in ("family-and-parenting", "feelings"))):
        # A child's age names the person the line is about, but only when nothing stronger does:
        # "our 3 year old has a fever" is health, and "my 9 year old wont do homework" is school.
        note("family-and-parenting", 2, child_ages[0], False)
    book_at = _a_book_for_a_child(norm, child_ages)
    if book_at is not None:
        # A book for a child is a reading question, and the age in it is who it is for, not the
        # subject: the child is named by the age and the book row is the one that answers it.
        note("entertainment", 3, book_at, False)
    if sums and not any(score >= 2 for score, _top, _first in found.values()):
        # Nothing strong was named: the line is a sum ("work out the area of a room").
        note("maths-and-numbers", 2, min(sums), False)
    output_at = _the_persons_own_output(norm)
    if output_at is not None:
        note("health", 2, output_at, False)
    stone_at = stone_weight_at(norm)
    if stone_at is not None:
        # "wanna lose a stone by summer" is a fitness goal, and `summer` alone read it as the
        # weather; the verb beside the stone is what the line is about.
        note("fitness", 3, stone_at, False)
    tight_at = tight_money_at(norm, line.get("text") or "")
    if tight_at is not None and not any(
            score >= 2 for topic, (score, _top, _first) in found.items() if topic != "money"):
        # "im skint till friday" names no account and no bill, only the tight week: money is
        # the subject of the line, and the reply reads `tight_on_money`.
        note("money", 3, tight_at, False)
    if sums and set(norm) & SUM_MONEY:
        # An amount anything is worked out for is the subject, whatever else the line says:
        # "work out my holiday pay" is money, and `holiday` is not the travel topic there.
        note("money", 3, min(sums), False)
    # What the line names with a distinctive word. A greeting phrase is the whole line when the
    # line names nothing else ("how are you doing then"), and only an opener when it does ("how
    # are you supposed to poach an egg", "how is it going with the new job"), so a line that
    # names something keeps that subject.
    named = {topic for word in norm if word not in ADDRESS_WORDS
             for topic, weight in _lookup(word)
             if weight >= 2 and topic != "small-talk"}
    # A greeting or a weather word says the whole line is small talk only when the line is
    # nothing else, so `its freezing in here` is small talk and `the pipes are freezing` is
    # about the pipes: the phrase is no topic at all there.
    for key, entries in TABLE.items():
        if " " not in key or key not in text:
            continue
        words = key.split()
        for start in range(len(norm) - len(words) + 1):
            if norm[start:start + len(words)] != words:
                continue           # "percent of" is not inside "percent off"
            if start in background:
                continue           # a phrase in the background clause is not the subject
            if sums and key == "work out":
                continue
            if named and all(topic == "small-talk" for topic, _weight in entries):
                continue           # "how are you supposed to poach an egg" is about an egg
            for topic, weight in entries:
                if _says_nothing_here(topic, words, norm, start, study):
                    continue
                note(topic, weight, start, False)
            break
    text_norm = " " + " ".join(norm) + " "
    match = JUDGEMENT_OF_RECORD.search(text_norm)
    if match and not any(score >= 3 for score, _top, _first in found.values()):
        # Nothing stronger was named, so the judgement is the subject. A line that names a place
        # keeps it as a co-topic the way the phrase list's entries do ("i mess everything up at
        # work" is feelings and work), so the phrase is only the subject here.
        note("feelings", 3, text_norm[:match.start()].count(" "), False)
    unfit = reads_as_unfit(text_norm)
    if unfit is not None and not any(score >= 3 for score, _top, _first in found.values()):
        # "im not cut out for this job" is how they see themselves; the job is where it happens,
        # so the phrase is only the subject here and the place keeps its own co-topic.
        note("feelings", 3, text_norm[:unfit].count(" "), False)
    if _the_weather_is_just_a_season(norm, text) and any(
            other != "nature-and-weather" and score >= 2
            for other, (score, _top, _first) in found.items()):
        own.pop("nature-and-weather", None)
    for pattern, topic in CANCELS:
        if topic not in found:
            continue
        # The word is only taken back when the line has another topic to be about: "how does
        # darts scoring work" has sport, while "how does my notice period work" and "how does
        # the appraisal work" name nothing but the job, and there the question is about the
        # job. A line that names only the word itself keeps it.
        if not any(other != topic and score >= 2 for other, (score, _top, _first)
                   in found.items()):
            continue
        match = pattern.search(text_norm)
        if not match:
            continue
        after = text_norm[match.end():].strip().split()
        if after and after[0] not in CANCEL_AFTER and after[0] not in (".", ",", ";", ":",):
            continue
        score, top, first = found[topic]
        found[topic] = (max(0, score - 2), top, first)
    ranked = sorted(found.items(),
                    key=lambda item: (item[1][0], item[1][1], -item[1][2]), reverse=True)
    # A word with a second everyday sense stays evidence, but it cannot carry an area alone: it
    # keeps the one point that says "maybe", and the ranking wants two.
    return [(topic, score if own.get(topic) else min(score, 1),
             top if own.get(topic) else min(top, 1))
            for topic, (score, top, _first) in ranked]


# A word that names a thing in two parts of life, where the two are different things and not two
# corners of one: a `tablet` is a pill and a screen, `stock` is what is in the freezer and what is
# in an ISA, a `fish` is a dinner and a pet, `draughts` are a game and the cold air under a door,
# a `tomato` is the seed packet and the dinner, a `virus` is the one going round the office and
# the one on the laptop, a `team` is the one you play for and the one you work in. Cooking and
# food-and-drink are one kitchen, so `milk`, `bread` and `cheese` are not here: a card from either
# is about the thing the person named.
#
# A word like this says nothing about the line on its own - only the rest of the sentence can say
# which of the two it is - so when the line gives nothing else to go on, the reading names it in
# `memory["understood"]["unsure"]` instead of letting the one word stand as the subject.
TWO_HOMES = frozenset("""
    tablet stock fish draughts tomato tomatoes basil virus team
""".split())


# The words that belong to each of the two lives, so the line can say which one it means without
# naming the thing twice: "the freezer is full" settles `stock` (the freezer is the kitchen's),
# "the screen is cracked" settles `tablet` (a pill has no screen). Only words of one life count,
# and a word that is in both lists settles nothing: "cream" is in the cook's kitchen and the
# chemist's, so it leaves a `tablet` in doubt.
#
# This is the whole of the settling test, and it is deliberately the two lives rather than "some
# other word of the area". The area a line is read as is picked from the doubtful word itself, so
# counting other words of that area settles the doubt with words that are no cue at all: the carer
# line "i need to tell my team im applying elsewhere" was called settled by `applying`, and
# "it was a woman from another team" by `woman`, while "how do i stock the freezer" stayed in
# doubt although "freezer" says the kitchen plainly, because the cue tables file a freezer under
# home-and-diy and the line had been read as cooking.
LIVES = {
    "tablet": (
        frozenset("""pill pills dose dosage swallow swallowed blister pack pharmacy
            prescription headache headachey painkiller painkillers ibuprofen paracetamol
            antibiotic antibiotics chemist gp food meal meals stomach empty water milk
            coffee breakfast with""".split()),
        frozenset("""screen screens battery charge charging charger charged app apps keypad
            keyboard wifi update downloading cracked ipad android""".split()),
    ),
    "stock": (
        frozenset("""cube cubes gravy soup broth pot saucepan freezer shelf cupboard kitchen
            chicken vegetable vegetables veg boil simmer bone bones""".split()),
        frozenset("""shares share market markets invest investing investment portfolio dividend
            dividends trading trader isa pension ftse broker buy sell buying selling worth
            price prices""".split()),
    ),
    "fish": (
        frozenset("""dinner tea supper lunch cook cooked frying fried grill grilled baked
            fillet fillets bones chips salmon tuna cod haddock mackerel monger fingers rice
            lemon batter""".split()),
        frozenset("""tank tanks pond pond bowl aquarium goldfish swim swimming died dying filter
            feeder feeding feed water""".split()),
    ),
    "draughts": (
        frozenset("""board pieces checkers play playing game games opponent win won lose""".split()),
        frozenset("""door doors window windows draught gap gaps under cold blow blowing seal""".split()),
    ),
    "tomato": (
        frozenset("""sauce sauces salad ketchup slice sliced soup tinned canned ripe puree
            passata sandwich make making cook cooking dinner meal""".split()),
        frozenset("""plant plants grow growing grew seed seeds seedling seedlings garden
            greenhouse blight water watering stake""".split()),
    ),
    "basil": (
        frozenset("""pesto pasta sauce leaves leaf fresh cook cooked make making recipe salad
            sprinkle dish dinner meal pizza""".split()),
        frozenset("""plant plants grow growing grew died dying wilted wilt pot soil water
            watering repot seed seeds""".split()),
    ),
    "virus": (
        frozenset("""laptop computer pc file files email software antivirus malware download
            downloaded popup popups password browser update""".split()),
        frozenset("""cold flu round caught fever cough symptoms sick ill bug bugs tummy
            throwing headache""".split()),
    ),
    "team": (
        frozenset("""rota shift shifts manager boss job work project colleagues colleague
            meeting employer office""".split()),
        frozenset("""match game win won lost lose score scored goal goals player players coach
            league season fans football rugby cricket kit""".split()),
    ),
}
LIVES["tomatoes"] = LIVES["tomato"]


def unsure_words(norm, topic):
    """The words whose second life is still in play, when the line said nothing to settle it.

    "my tablet has gone missing" names a thing that is a pill and a screen, and the rest of the
    line does not say which, so the area the reader picked from it is a guess. "should i take a
    tablet with food" says which in another word (`food` is the pill's life), and "the freezer is
    full, how do i stock it" (`freezer` is the kitchen's). Those lines have said what they are
    about, and nothing is in doubt.

    The line is asked which of the two lives it named (LIVES), and only that. A word of neither
    life, however well it scores for the area the line was read as, leaves the doubt standing:
    the area came from the doubtful word in the first place.
    """
    if not topic:
        return []
    words = set(norm)
    in_doubt = []
    for word in words:
        if word not in TWO_HOMES:
            continue
        if any(words & home for home in LIVES.get(word, ())):
            continue                     # the line said which life it means
        in_doubt.append(word)
    return sorted(in_doubt)


# A topic the line itself scores this strongly is what the line is about; a place in it is
# only where it happens.
PLACE_OVER = 2


def _place_points(line, entities, scores, asks=None):
    """How much a place the line names says about what the line is about.

    A place is what a line is about when the person is going there or planning something
    there ("a weekend in Lisbon", "we are going to Rome next month"), and when they ask what
    to do there ("museums in Rome", "restaurants in Edinburgh"). It is only the background of
    a line about something else: "how do i get a mortgage in Birmingham" is a money question,
    "i am a bus driver in Leeds" is a self-introduction, "my sister lives in Paris" is news
    about a sister. So the place scores 4 with a travel word, 3 when the line asks something
    and nothing else in it scores, and nothing otherwise.
    """
    words = set(line["norm"])
    if words & TRAVEL_STRONG:
        return 4
    if any(item["type"] == "person" for item in entities):
        return 0
    others = [score for topic, score in scores.items()
              if topic not in ("geography-and-travel", "small-talk")]
    if others and max(others) >= PLACE_OVER:
        return 0
    asked = _looks_like_an_ask(line) if asks is None else asks
    return 3 if asked else 0


# Words that say a person is going somewhere. Deliberately not "get" or "go": "how do i get a
# mortgage in Birmingham" is a money question with a town in it.
TRAVEL_STRONG = frozenset("""trip trips holiday holidays flight flights fly flying flew
    visit visiting visited travel travelling traveling travelled traveled abroad hotel hotels
    booking itinerary sightseeing tourist tourists weekend weekends break honeymoon
    going drove driving ride staying""".split())

# The words that open a question, so a line can be read as an ask without the whole of kinds.
ASK_WORDS = frozenset("""what how where when why which who whom whose can could should would
    will shall do does did is are was were am any anyone something tell give suggest
    recommend show me""".split())


# A person a line is about does not decide what the line is about when the line goes on to say
# what that person wants: "my wife wants a takeaway" is a food line, "my wife wants a new sofa" is
# a home line, "the mrs is learning to drive" is a study line. The person is the subject of the
# sentence, and the thing they want is what the person typing it wants a hand with. Without this
# every one of those lines read as family-and-parenting, because "wife" alone is a strong family
# word. A want of something that has no area of its own ("my wife wants a break") is left alone.
WANT_VERBS = frozenset("""want wants wanted wanting need needs needed fancies fancy
    fancied fancies""".split())
A_THING_WANTED = frozenset("a an the some another new more".split())
WANTED_BEFORE_A_STOP = frozenset("""for to of at with and but so because when if
    about by from in on""".split())
A_PERSON_WHO_WANTS = frozenset("""wife husband mrs missus partner son daughter kid kids
    child children baby teenager mum mom mother dad father brother sister mate mates friend
    friends boyfriend girlfriend fella bloke lad lass nan nana granny grandad""".split())


def _what_someone_else_wants(norm):
    """(topic, position) for the thing a person in the line wants, or None.

    "my wife wants a takeaway" -> ("cooking-and-food", 4), "my son wants a dog" -> pets. The
    person has to be the one wanting - the person word sits just before the verb - so "i need
    some breathing room from my husband" is not read as something the husband wants, and the
    thing wanted has to be written as a thing ("a takeaway", "some new bedding"), not abstractly
    or after a preposition: "school wants 20 pounds for a trip" is a money line about a trip.
    """
    for at, word in enumerate(norm):
        if word not in WANT_VERBS:
            continue
        if not A_PERSON_WHO_WANTS & set(norm[max(0, at - 3):at]):
            continue
        for spot in range(at + 1, min(len(norm), at + 5)):
            if norm[spot] in WANTED_BEFORE_A_STOP:
                break             # "wants 20 pounds for a trip": the trip is not what is wanted
            if norm[spot] not in A_THING_WANTED:
                continue
            for candidate in norm[spot + 1:min(len(norm), spot + 5)]:
                if candidate in A_THING_WANTED:
                    continue      # "a new sofa" is a sofa, not the word "new"
                topics = [topic for topic, weight in _lookup(candidate)
                          if topic not in PEOPLE_TOPICS and topic != "small-talk" and weight >= 2]
                if topics:
                    return topics[0], spot + 1
            break
    return None


def _looks_like_an_ask(line):
    """Does the line ask for something? A question mark, a question word, or an imperative."""
    text = line.get("text") or ""
    norm = line["norm"]
    if "?" in text or not norm:
        return True
    return norm[0] in ASK_WORDS


# The familiar words for a friend are ordinary ones: "mate", "pal", "bloke", "fella". The
# person a line claims as their own ("my mate", "our mates", "your bloke") is a subject, so one
# of those words after a possessive counts as much as a distinctive word - "my mate keeps
# flaking on me" and "its my mates 40th on saturday" named nothing at all. A line that only
# addresses somebody ("u alright mate") names nobody, so it takes no boost, and an area that
# already has a distinctive word of its own keeps the line ("my mate owes me 300" is money).
# "my lad", "our lass" and "my missus" are a son, a daughter and a wife, so they are not here.
FRIEND_WORDS = frozenset("""mate mates pal pals buddy buddies bloke fella
    flatmate flatmates housemate housemates""".split())
OWNED_BY = frozenset("my your his her our their me".split())
FRIEND_BOOST = 1


def _names_a_friend_of_their_own(norm):
    """True when the line says "my mate", "our mates", "your bloke": a friend they claim."""
    return any(word in FRIEND_WORDS and before in OWNED_BY
               for before, word in zip(norm, norm[1:]))


def _the_persons_own_output(norm):
    """Where the line talks about what comes out of the person, or None.

    "my poo has been green for a week" named no part of the body, so the only words left were
    "green" and "a week" and it was answered with the salad-drawer advice. The words for it are
    also the words for what an animal does and for a job to be done - "how do i get bird poo off
    my car" is the car - so the line has to make it the person's own: said of them ("i have not
    pooed in 3 days", "my son hasnt pooed for two days") or owned by them ("my poo", "her
    stools"). A sample or a test is a thing being handed in, not a symptom.
    """
    if not set(norm) & BODILY_OUTPUT or set(norm) & SAMPLE_WORDS:
        return None
    words = set(norm)
    if words & ONLY_A_STOOL and not words & (BODILY_OUTPUT - ONLY_A_STOOL):
        if words & STOOL_AS_FURNITURE:
            # "my stool is wobbly", "one leg of my stool is loose": the only word for the gut
            # here is the one that is a chair too, and the line names a leg and a joint.
            return None
        if not A_GUT_ONLY.search(" ".join(norm)):
            # "my stool is loose" is a loose leg as much as a loose gut, so the shared words
            # alone do not make it the person's: the line needs one word no chair can have.
            return None
    if set(norm) & ANIMALS:
        return None                      # the bird's, the cat's, the dog's
    if set(norm) & PETS:
        return None
    words = set(norm)
    person = bool(words & (_person_words() - PETS - ANIMALS))
    for at, word in enumerate(norm):
        if word not in BODILY_OUTPUT:
            continue
        if word in BODILY_OUTPUT_NOUN:
            if at and norm[at - 1] in OWNERS:
                return at               # "my poo", "her stools"
            continue
        if person or words & frozenset("i im ive we weve".split()):
            return at                   # "i have not pooed", "my son hasnt pooed"
    return None


def own_output_word(norm):
    """The word for what comes out of the person, when the line makes it theirs, or None.

    The reading carries it as `own_output` so a knowledge row that shares the word with a thing
    - a stool is a chair, green leaves keep a week in the drawer - can stand aside for the body.
    """
    return _the_persons_own_output(norm)


def _owns_an_animal(norm):
    """True when the line names an animal somebody owns ("my fish", "our rabbit")."""
    return any(word in OWNERS and norm[at + 1] in ANIMALS
               for at, word in enumerate(norm[:-1]))


def _a_crop_is_failing(norm):
    """True when the line says a crop of the person's own is not doing well where it grows.

    The state has to be one a plant is in rather than a dish: "my tomatoes are not ripening" is
    the plant, "my tomatoes are in the salad" is dinner. A crop kept in a kitchen, or one the
    line cooks, is dinner whatever else it says, so the kitchen words hold the fence off.
    """
    words = set(norm)
    if words & CROP_KITCHEN:
        return False
    text = " ".join(norm)
    if not any(state in text for state in CROP_STATES):
        return False
    # Something has to be growing: the person's own crop, the plant, the tree, the greenhouse.
    if words & GROWING_PLACES:
        return True
    for at, word in enumerate(norm[:-1]):
        if word in OWNERS and norm[at + 1] in CROPS:
            return True
    return False


def _asks_mechanism(norm):
    """True when the line asks how the world works ("why do...", "how old is...")."""
    if not norm or norm[0] not in MECHANISM:
        return False
    if norm[0] == "how":
        return len(norm) > 1 and norm[1] in MECHANISM_HOW
    return True


def _sign_said_of_a_person(norm, words):
    """True when a sign word in the line is the state of the person it is said of.

    A sign only counts with a person in the line to have it, and then only in the shapes that
    make it the person's state rather than a modifier, a behaviour or an idiom.
    """
    text = " ".join(norm)
    if any(phrase in text for phrase in UNWELL_IDIOMS):
        return False
    for at, word in enumerate(norm):
        after = norm[at + 1] if at + 1 < len(norm) else ""
        before = norm[at - 1] if at else ""
        if word in UNWELL_SIGNS:
            if after in BEHAVIOUR or after in SIGN_NOT_AFTER:
                continue                  # "confused about her homework", "unresponsive when..."
            if word in NOUNY_SIGNS and after and after not in SIGN_FOLLOWS and not after.isdigit():
                continue                  # "her temperature homework", "a cold shoulder"
            if word == "broke" and not words & BODY:
                continue                  # "my son broke his toy" is not an injury
            return True
        if before == "not" and word in UNWELL_NOT:
            if word != "responding":
                return True
            # "not responding" is a sign when there is somebody or something to respond to
            for ahead in norm[at + 1:at + 4]:
                if ahead in COMMS:
                    return False
                if ahead in HEARERS:
                    return True
            return True                   # "she is not responding" on its own
    return False


# A blocked nose is said without the nose: "im stuffy", "im all bunged up", "im congested",
# "my head is blocked up". Each of those words describes something that is not a person too - a
# stuffy office, a blocked sink, a congested road - and "im stuffed" is a full stomach rather than
# a cold. So the word only counts as a cold when it is said of the person: straight after "im",
# "i am" or "i feel" with no more than a few fillers in between ("all", "really", "a bit"), or
# after a head, nose or sinus that is the speaker's own. Read on the line only: the answer for
# these lines is the cold's, and a room that is stuffy is a different answer entirely.
NOSE_BLOCKED = re.compile(
    r"\b(?:im|i am|i feel|im feeling|i am feeling|i feel like i am)\b"
    r"(?:\s+(?:all|really|so|very|a\s+bit|a\s+little|totally|properly|quite|that|bit|"
    r"still|now|again|bit)){0,3}\s+"
    r"(?:stuffy|stuffed\s+up|bunged\s+up|blocked\s+up|congested|congestion|clogged\s+up)\b"
    # "im sniffly", "ive been sniffling all week": nothing else is sniffly, and the answer for it
    # is the cold's. The line still has to be about the person ("the dog is sniffing" is not).
    r"|\b(?:im|ive|i've|i\s+have|i\s+keep)\b"
    r"(?:(?!\b(?:dog|cat|puppy|kitten|baby|kid|boy|girl)\b)[^.!?]){0,18}?"
    r"\b(?:sniffly|sniffles|sniffling|sniffing|snotty)\b"
    r"|\bmy\s+(?:head|nose|sinuses?|nose\s+passages?|face)\b"
    r"(?:\s+(?:is|are|feels?|feeling|gets?|keeps?|has\s+been)){0,2}"
    r"(?:\s+(?:all|really|so|very|a\s+bit|a\s+little|totally|quite|still|now|again|bit)){0,3}"
    r"\s+(?:stuffy|stuffed\s+up|bunged\s+up|blocked\s+up|blocked|congested|congestion)\b")
# "i feel stuffy" is the mood reading at 5 ("feel" plus "stuffy"), and this is the same words
# said of the person by the person, so the cold has to outrank the mood it sounds like.
NOSE_BLOCKED_BOOST = 6


def _a_person_is_unwell(norm, words):
    """A line that names a person and says something is wrong with them ("my baby has a fever")."""
    if not words & UNWELL_SIGNS and not ("not" in words and words & UNWELL_NOT):
        return False
    if not any(word in THE_PEOPLE for word in norm):
        return False                      # "the shed collapsed last year" names nobody
    return _sign_said_of_a_person(norm, words)

# The phrases that say the money has run out rather than name a money subject: "im skint till
# friday" names no account and no bill, and the reply that fits is about the tight week and not
# about saving. Read on the line only, and only when the line is not asking for something else,
# so "what can i cook till payday" stays the cooking question it is.
MONEY_TIGHT = ("skint", "brassic", "till payday", "until payday", "money is tight",
               "tight month", "on the breadline", "no money till", "no money until",
               # "no money" is the plainest way of saying it and it says it on its own:
               # "i have no money", "there is no money", "no money this week"
               "no money left", "no money", "running out of money", "a bit short this month",
               "short this month", "short till payday",
               # and the week is named: "im short till friday", "im short this week"
               "short till", "short this week",
               # an empty purse said as what is left rather than as no money: "i have nothing till
               # friday", "there is nowt until payday"
               "nothing till", "nothing until", "nowt till", "nowt until",
               "cleaned out", "not got a penny", "penny to my name")
MONEY_TIGHT_MAX = 10

# `broke` is the word people use most for this, and it is also the verb: "i broke my phone",
# "she broke up with me", "the car broke down", and a thing's own state ("my laptop is broke").
# So it says the money has gone only where the person is the subject and nothing but a time
# follows: "im broke", "we are broke", "im so broke", "im completely broke", "im broke till
# friday", "broke till payday", "im broke this week", "im broke again". Every word in front has
# to be the person or an intensifier, so "the car broke" and "i broke my phone" never match, and
# every word after has to be a time or a turn of phrase, so "i broke a glass" never matches.
# A copula stays: "he is broke" and "she was broke" are the money, not a machine of its own. The
# one word that has to go is "it", because "it" is the only word here that stands for a thing
# rather than a person, and "its broke" / "it was broke" are the thing.
BROKE_AS_SUBJECT = frozenset("""i im am we are he she hes shes they theyre you youre u is
    was were been be being totally completely so officially proper flat dead stone absolutely
    very pretty quite really just still honestly yeah ok okay and but now""".split())
BROKE_AS_TIME = frozenset("""till until by for this week month payday weekend end today
    tomorrow again now already friday monday tuesday wednesday thursday saturday sunday and but
    so or time yet though honestly lol ha thanks anyway right now""".split())


def broke_at(norm):
    """Where the line says the speaker has no money with `broke`, or None."""
    for at, word in enumerate(norm):
        if word != "broke":
            continue
        if any(before not in BROKE_AS_SUBJECT for before in norm[:at]):
            continue
        if any(after not in BROKE_AS_TIME for after in norm[at + 1:]):
            continue
        return at
    return None


# The other way people say it is to name what is left and how long it has to last: "i have 20
# quid till friday", "a tenner till payday", "30 pounds until the end of the week". The amount is
# what carries it, so a money word has to sit next to a number, and a wait has to follow it: "i
# have 20 quid" on its own is not a complaint. Where the wait runs to is what makes it a week
# rather than a fact about a bill - "my rent is 900 quid until march" names a date, not payday.
A_MONEY_WORD = frozenset("quid pound pounds tenner tenners fiver fivers bucks".split())
# "a tenner till friday" and "a fiver till monday" name the amount in the noun itself, so there is
# no number word in front of it to find. The noun is the sum, and it is a small one.
A_AMOUNT_NOUN = {"tenner": 10, "tenners": 10, "fiver": 5, "fivers": 5}
# The way most people type an amount is a symbol, and `normalise` drops it before any reader sees
# the line: "i have £30 till friday" arrives as `["i", "have", "30", "till", "friday"]`, so no
# money word is next to the figure and the shape missed its commonest spelling. The typed line
# still has the `£`, so it is read here, beside the normalised words.
A_AMOUNT_SYMBOL = re.compile(r"£\s*(\d+(?:[.,]\d+)?)|(?<![\w.])(\d{1,4})\s*p\b")
A_WAIT = frozenset("till until til".split())
A_WAIT_TO = frozenset("""payday friday saturday sunday monday tuesday wednesday thursday week
    weekend month end tomorrow today next""".split())
# A purse with plenty in it is savings, not a shortfall. "i have 2000 quid till next month" and
# "i have 500 pounds till payday" are people saying what they have, not what has run out, and the
# money entry answered both plainly ("Noted: you have 2000 quid till next month") before this
# reading existed. What makes a week tight is the money being nearly gone, so the reading stands
# only while the amount is small: five hundred or more with time to go is a cushion, and those
# lines go back to the entry that answers a sum of money.
BIG_PURSE = 500


def _purse_amount(norm, at):
    """How much the line says is left, in pounds, or None when it does not say."""
    amount = norm[at - 1]
    if amount.replace(".", "").isdigit():
        return float(amount)
    value = WORD_NUMBERS.get(amount)
    if value is None:
        return None
    if amount in ("hundred", "thousand") and at >= 2:
        # "two thousand pounds", "three hundred quid": the word in front is how many of them.
        before = WORD_NUMBERS.get(norm[at - 2])
        if before is not None:
            return before * value
    return value


def _a_wait_follows(words):
    """True when the words after an amount say when the money comes."""
    for spot, word in enumerate(words[:3]):
        if word not in A_WAIT:
            continue
        # "till payday", "until friday", "till the end of the week": the wait has to run to
        # something that gives the week an end.
        rest = [one for one in words[spot + 1:spot + 3] if one not in ("the", "a", "i")]
        if rest and rest[0] in A_WAIT_TO:
            return True
    return False


def purse_till_at(norm, text=""):
    """Where the line says what is left and when the money comes, or None."""
    for at, word in enumerate(norm):
        if at == 0:
            continue
        if word in A_AMOUNT_NOUN:
            # "a tenner till friday" is the same week as "ten quid till friday": the noun is the
            # amount, so the wait alone decides it.
            if _a_wait_follows(norm[at + 1:]):
                return at - 1
            continue
        if word not in A_MONEY_WORD:
            continue
        amount = norm[at - 1]
        if amount not in NUMBER_WORDS and not amount.replace(".", "").isdigit():
            continue
        if (_purse_amount(norm, at) or 0) >= BIG_PURSE:
            continue
        if _a_wait_follows(norm[at + 1:]):
            return at - 1
    if text:
        for match in A_AMOUNT_SYMBOL.finditer(text.lower()):
            pounds, pence = match.group(1), match.group(2)
            value = float(pounds.replace(",", "")) if pounds else float(pence) / 100.0
            if value >= BIG_PURSE:
                continue
            after = re.findall(r"[a-z']+", text[match.end():].lower())
            if _a_wait_follows(after):
                return 0
    return None


def tight_money_at(norm, text=""):
    """Where the line says the money has run out, or None: "im skint till friday", "a bit short".

    The phrase has to be the whole of what the line names. "im vegetarian and im skint, cheap
    dinners" asks for dinners and is answered as the cooking ask it is, so naming another
    subject at all leaves the tight week unsaid.
    """
    joined = " " + " ".join(norm) + " "
    at = broke_at(norm)
    purse = purse_till_at(norm, text)
    if purse is not None:
        at = purse if at is None else min(at, purse)
    for phrase in MONEY_TIGHT:
        spot = joined.find(" " + phrase + " ")
        if spot < 0:
            continue
        index = len(joined[:spot].split())
        at = index if at is None else min(at, index)
    if at is None:
        return None
    for word in norm:
        for topic, weight in _lookup(word):
            if weight >= 2 and topic not in ("money", "small-talk"):
                return None
    return at


# A weight in stones is the fitness area, and "stone" alone is building stone, a fruit stone or
# a paving slab. The verb is what makes it a weight: people say "i want to lose a stone", "shed
# half a stone", "ive put on a stone", "i weigh 13 stone". `put` is only ever "put on" here -
# "i put a stone on the path" is a path - and `dropped` and `shifted` are left out on purpose:
# "i dropped a stone on my foot" is a foot and "we shifted a ton of stone" is a delivery.
STONE_VERBS = frozenset("""lose loses losing lost loss shed sheds shedding gained gain
    gains gaining weighed weigh weighs weigh-in diet dieting slimming slimmer""".split())
STONE_COMPOUNDS = ("put on", "piling on", "piled on")


def stone_weight_at(norm):
    """Where the line weighs something in stones, or None.

    Only the verb makes it a weight, and it has to be near the stone ("i want to lose a stone",
    "half a stone to shift before the wedding"), so a line about a wall or a fruit stone keeps
    its own area.
    """
    spots = [at for at, word in enumerate(norm) if word in ("stone", "stones")]
    if not spots:
        return None
    joined = " ".join(norm)
    cues = {at for at, word in enumerate(norm) if word in STONE_VERBS}
    for phrase in STONE_COMPOUNDS:
        start = 0
        while True:
            spot = joined.find(phrase, start)
            if spot < 0:
                break
            cues.add(len(joined[:spot].split()))
            start = spot + 1
    for at in spots:
        if any(abs(at - cue) <= 4 for cue in cues):
            return at
    return None


def tight_on_money(norm, kind=None, text=""):
    """True when the line says the money has run out and is about nothing else.

    A question is left alone - "what can i cook till payday" is a cooking ask that happens to
    mention payday - and so is a line long enough to be about something else.
    """
    if kind == "question" or not norm or len(norm) > MONEY_TIGHT_MAX:
        return False
    return tight_money_at(norm, text) is not None



# The words a person uses for worn out, which name other things on their own: a shattered
# window, a drained radiator, a wiped table, a wrecked car. They are the tiredness when they
# are said of the person, so they only count within a few words of "im", "am" or "feel".
WORN_OUT = frozenset("shattered whacked zonked pooped bushed fagged drained wrecked frazzled".split())
WORN_OUT_SAID = ("wiped out", "done in", "worn out", "cream crackered", "wiped")
WORN_OUT_CUE = frozenset("im am feel feeling".split())
WORN_OUT_LOOKBACK = 3
WORN_OUT_BOOST = 4


def _worn_out(norm):
    """True when the line says the person is worn out, in the words people use for it.

    The cue is the person: "im shattered" is the tiredness and "the shed window is shattered"
    is not, so the word has to come within three words of "im", "am" or "feel". "Wiped", "done"
    and "worn" only count inside their phrase, because "im done with that" is not tiredness.
    """
    if not norm:
        return False
    for at, word in enumerate(norm):
        if word in WORN_OUT and any(item in WORN_OUT_CUE
                                     for item in norm[max(0, at - WORN_OUT_LOOKBACK):at]):
            return True
    joined = " " + " ".join(norm) + " "
    for phrase in WORN_OUT_SAID:
        spot = joined.find(" " + phrase + " ")
        if spot < 0:
            continue
        back = joined[:spot].split()[-WORN_OUT_LOOKBACK:]
        if any(item in WORN_OUT_CUE for item in back):
            return True
    return False


def rank_topics(line, inherited=None, entities=None, asks=None):
    """[(topic, score)] for this line, best first, with what the line names taken into
    account: a place plus a travel cue, a pet that is the subject, a percentage."""
    found = {topic: [score, top] for topic, score, top in score_topics(line)}

    def boost(topic, points):
        entry = found.setdefault(topic, [0, 0])
        entry[0] += points
        entry[1] = max(entry[1], points)

    words = set(line["norm"])
    if entities and any(item["type"] == "place" for item in entities):
        points = _place_points(line, entities,
                               {topic: score for topic, (score, _top) in found.items()},
                               asks)
        if points:
            boost("geography-and-travel", points)
    if entities and any(_a_country_named(item) for item in entities):
        # The sentence has said the word is the place: "is turkey in europe", "a weekend in
        # turkey", "how safe is turkey". The word is in a cooking vocabulary too, and one word
        # in common must not send a country question to the kitchen.
        boost("geography-and-travel", COUNTRY_BOOST)
    if entities and any(item["text"].lower().split()[-1] in PETS for item in entities):
        # a named pet is the subject of its line, whatever else the line mentions
        boost("pets", PET_BOOST)
    words = set(line["norm"])
    reason = reason_positions(line["norm"])
    if set(word for position, word in enumerate(line["norm"]) if position not in reason) & BODY \
            and set(word for position, word in enumerate(line["norm"]) if position not in reason) & HURTS:
        boost("health", HURT_BOOST)
    if _head_fog(line["norm"]):
        # a head that will not clear is the person's own state, and the weather words in it are
        # not the weather
        boost("health", HEAD_FOG_BOOST)
    if _skin_state(line["norm"], reason) is not None and not any(
            found.get(topic, [0])[0] >= 2 for topic in PEOPLE_TOPICS):
        # Someone else's dry skin is about them, not a health line for the speaker, and the
        # knowledge has the family answer: "my husband has dry skin" is not "my hands are dry".
        boost("health", SKIN_BOOST)
    if _named_condition(line["norm"], words, reason):
        # A condition named by its own name is a health line, with no part of the body and no
        # word of pain in it: "ive got piles", "my eczema is flaring up", "i think i have
        # sciatica", "how do i stop getting cystitis". The named illness is the subject, so an
        # ordinary word in the same line does not take the line off it.
        boost("health", CONDITION_BOOST)
    if _a_part_plays_up(line["norm"], reason) is not None:
        boost("health", PART_UP_BOOST)
    warmth = the_warmth_said(line["norm"])
    # A person who is cold has no sign of illness in that word, so the word is left out of the
    # unwell reading: "my mum is cold" is a jumper, not a cold.
    sign_words = ([word for word in line["norm"] if word != warmth] if warmth else line["norm"])
    if _a_person_is_unwell(sign_words, set(sign_words)):
        # A person plus something wrong with them is a health line: "my baby has a fever", "my
        # dad is confused and drowsy". The person is who it is happening to; what the line is
        # about is what is wrong with them, so naming the person does not make it a family line.
        boost("health", UNWELL_BOOST)
    if NOSE_BLOCKED.search(" " + " ".join(line["norm"]) + " "):
        # a cold said without the nose: "im stuffy", "im all bunged up" read as nothing at all,
        # and the person got "I'm listening" back
        boost("health", NOSE_BLOCKED_BOOST)
    animals = _owns_an_animal(line["norm"])
    if animals:
        boost("pets", PET_BOOST)          # "why are my fish dying" is a fish-keeper's question
    if _names_a_friend_of_their_own(line["norm"]):
        boost("friends-and-relationships", FRIEND_BOOST)
    wanted = _what_someone_else_wants(line["norm"])
    if wanted is not None and any(found.get(topic, [0])[0] >= 2 for topic in PEOPLE_TOPICS):
        # "...wants a takeaway" is the line's subject, and the person it is about is not:
        # the want is what the person typing it wants a hand with. It only outranks a line the
        # person word has already made a family line, so a want in an ordinary sentence is
        # left to the ordinary reading.
        topic, at = wanted
        boost(topic, max(found.get(topic, [0])[0], 2) + 1)
    if _a_crop_is_failing(line["norm"]):
        # "my tomatoes are going blue" is about the plant, not the dinner: the crop is named the
        # same way either way, so what is happening to it is what says which.
        boost("garden-and-plants", CROP_BOOST)
    if _a_habit_given_up(line["norm"]):
        # A food given up is a diet, not a recipe: the cooking card answered "i gave up sugar"
        # and "i gave up bread last year" with how to store them.
        boost("food-and-drink", GIVING_UP_BOOST)

    if _worn_out(line["norm"]) and not _asks_back(line["norm"]):
        # "im shattered", "im wiped out", "im done in": the everyday words for worn out are
        # other things on their own - a shattered window, a drained radiator, a wiped table -
        # so the word only counts with the person in front of it. A line that hands the
        # question back is answering "how are you", though: "im shattered thanks, you?" wants
        # the bot's own day and the question returned, not a page about sleep, so the tiredness
        # there is the social answer and not a subject of its own.
        boost("sleep", WORN_OUT_BOOST)
    if (words & WORLD and not words & WORLD_NOT and not words & NATURE_WORDS
            and not words & HURTS and not animals and _asks_mechanism(line["norm"])):
        # "why do we have seasons" is not a TV series, "why do fish breathe underwater" is not
        # dinner and "why do my ears pop on a plane" is not a trip: the line asks how something
        # works, so the subject of the line is what it is about, not what it is part of.
        boost("science", SCIENCE_BOOST)
    for number in detect_numbers(line):
        if number["unit"] == "percent":
            boost("maths-and-numbers", 3)
    if _gift_ask(words, line["norm"]):
        boost("shopping", GIFT_BOOST)
    if (found.get("health", [0])[0] >= 3
            and {topic for topic, entry in found.items()
                 if entry[0] >= 2} <= {"health", "small-talk"}):
        # A line whose strongest reading is a symptom and whose only other reading is small talk
        # is a health line: "i have a cold sore" carries "cold", which is small talk on its own,
        # but nobody saying it is chatting about the weather. A weak health word is left alone,
        # so "it's cold today" and "im cold" keep their small-talk reading.
        found.pop("small-talk", None)
    if inherited:
        # staying on the conversation's topic is evidence: a follow-up rarely changes subject.
        # A topic the line only holds up with ordinary words ("we have a 3 year old" is
        # "year" and "old") is not a new subject, so it gives way to the conversation's own.
        for topic, entry in found.items():
            if topic != inherited and entry[1] < 2:
                entry[0] -= 1
        boost(inherited, CARRY)
    scores = {topic: score for topic, (score, _top) in found.items()}
    if _the_weather_is_just_a_season(line["norm"], " " + line["norm_text"] + " "):
        # The boosts above are the rest of the sentence speaking: a part of the body that hurts,
        # a place, a pet, a sum. A season that only says when cannot outrank any of them, so it
        # drops to the one point that says "maybe" - "i broke my arm last winter" is the arm.
        entry = scores.get("nature-and-weather")
        if entry is not None and any(
                other != "nature-and-weather" and score >= 2
                for other, score in scores.items()):
            scores["nature-and-weather"] = min(entry, 1)
    ranked = [(topic, score) for topic, score in scores.items() if score >= 2]
    ranked.sort(key=lambda item: (item[1], item[0] == inherited), reverse=True)
    return ranked


def gift_ask(understood):
    """True when this reading asks what to give someone. Public: the answer entry asks too."""
    if not isinstance(understood, dict):
        return False
    norm = understood.get("norm")
    if not isinstance(norm, (list, tuple)) or not norm:
        return False
    return _gift_ask(set(norm), list(norm))


def _gift_ask(words, norm):
    """True when the line asks what to give someone.

    A gift word needs one other sign of a gift ("a present for", "an anniversary gift"), and
    a plain "get" needs a person to give to and then nothing that turns it into another
    errand: "get her" is a present, "get her to eat", "get her a taxi", "get him tested" and
    "get him for his cough" are not. What follows the person decides - the end of the line, or
    "something", a present word, or an occasion ("for christmas", "for her birthday").
    """
    if words & GIFT_ALWAYS:
        return True
    if words & GIFT_WORDS and (words & GIFT_ASKING or words & GIVE_VERB
                               or words & GIFT_OCCASION or "for" in words):
        return True
    if words & GIFT_WANTING and _gift_still_to_get(words, norm):
        return True
    if not (words & GIFT_ASKING or words & GIFT_OCCASION):
        return False
    if words & GIFT_OCCASION:
        # An occasion with a thing given to someone is a gift ask whatever verb carries it:
        # "my mums birthday is on saturday and i havent got her anything" is not asking what
        # to buy in general, and "got" is not one of the giving verbs above. The thing has to
        # be named - "i miss him at christmas" is an occasion and nothing given.
        for position, word in enumerate(norm[:-1]):
            if word in GIVE_TO and set(norm[position + 1:position + 3]) & GIVE_THINGS:
                return True
    for position, word in enumerate(norm):
        if word not in GIVE_VERB:
            continue
        rest = norm[position + 1:]
        if not rest:
            continue
        head = rest[0]
        if head in GIVE_THING or head in GIFT_WORDS or head in GIFT_OCCASION:
            # "get something", "get ideas", "get a present": the thing is the whole ask.
            return True
        tail = rest
        for index, one in enumerate(rest[:2]):
            if one in GIVE_TO or (one in GIVE_DETERMINERS and rest[index + 1:index + 2]
                                  and rest[index + 1] in GIVE_TO):
                tail = rest[index + 1:] if one in GIVE_TO else rest[index + 2:]
                break
        else:
            continue
        # "what could i get her" is the whole ask, and "get her something", "get her a present"
        # and "get her for christmas" name the thing given. "get her a taxi", "get him to the
        # doctor" and "get her to eat" name another errand, so they are not shopping lines. A
        # relative clause after the person describes them, not the errand ("what could i get my
        # mate who just moved in" asks what to get, not what to do about the move).
        if not tail or tail[0] in GIVE_RELATIVE:
            return True
        if [one for one in tail[:3] if one in GIFTS_OR_OCCASIONS]:
            return True
        if tail[0] == "for" and any(ch.isdigit() for one in tail[1:4] for ch in one):
            # "what should i get my mum for her 60th" names its occasion as a number.
            return True
    return False


def _gift_still_to_get(words, norm):
    """True when the line says a present is still not got: the person and the thing, no question.

    "i still havent got her anything", "still need to get my mum something", "i havent bought
    my sister her present yet", "nothing for him yet". The giving verb is the same one a gift
    question uses, so the shape is the same - a person to give to and then the thing given -
    and what makes it a gift line rather than an errand is that the thing is still owed: a
    want word somewhere in the line, and "anything" or "nothing" as the thing.
    "get her a taxi", "get him tested" and "get the kids to bed" name no thing given.
    """
    if words & GIVE_TO and "for" in words and words & {"nothing", "anything"}:
        return True
    for position, word in enumerate(norm):
        if word not in GIVE_VERB:
            continue
        rest = norm[position + 1:]
        for index, one in enumerate(rest[:2]):
            if one in GIVE_TO:
                tail = rest[index + 1:]
                break
            if (one in GIVE_DETERMINERS and rest[index + 1:index + 2]
                    and rest[index + 1] in GIVE_TO):
                tail = rest[index + 2:]
                break
        else:
            continue
        if not tail:
            continue
        # "havent got her anything", "need to get my mum something": the thing given is a word
        # for a thing, so it can only be a present. "havent got her a taxi" names an errand.
        if tail[0] in GIVE_THING or tail[0] in GIFT_WORDS:
            return True
        if "for" in tail and words & {"nothing", "anything"}:
            return True
        if [one for one in tail[:3] if one in GIFT_OCCASION]:
            return True
    return False


def subject_topic(line, entities=None):
    """The topic this line names with a distinctive word or a phrase, or None.

    Ordinary words alone ("year", "old", "think") do not make a subject: a line built from
    them is a follow-up on whatever the conversation is already about, so this is what a
    caller asks before treating the line as a new subject.
    """
    for topic, _score, top in score_topics(line):
        if top >= 2:
            return topic
    return None


def the_words_that_said(line, topic, entities=None):
    """[(word, weight)] for what in the line points at `topic`, strongest first.

    A phrase counts as the phrase (`hot dog`, `work out`) and not as its words, because the
    phrase is what says which sense a word is being used in: "hot dog" is a food, while `dog`
    on its own is the animal. Understanding publishes this so a reader can see how much of the
    sentence backs a topic before it answers from it (`understood["topic_from"]`).
    """
    if not isinstance(topic, str) or not topic:
        return []
    # The reading publishes this, and a caller may ask about a topic the table has no entry
    # for (`small-talk`, `about-the-bot`): those said nothing, so there is nothing to show.
    norm = list(line.get("norm") or ())
    found, covered = [], set()
    for size in range(2, 5):
        for start in range(len(norm) - size + 1):
            key = " ".join(norm[start:start + size])
            for name, weight in TABLE.get(key, ()):      # `percent of` is not `percent off`
                if name == topic:
                    found.append((key, weight))
                    covered.update(norm[start:start + size])
    for position, word in enumerate(norm):
        if word in covered:
            continue
        for name, weight in _lookup(word):
            if name == topic:
                found.append((word, weight))
    found.sort(key=lambda item: (-item[1], item[0]))
    return found


def detect_topic(line, inherited=None, entities=None, asks=None):
    """The topic the line is about (or inherited when it adds nothing), plus its score."""
    ranked = rank_topics(line, inherited, entities, asks)
    if ranked:
        return ranked[0]
    return (inherited, 0) if inherited else (None, 0)


def _is_name(word):
    """A capitalised word is a name when it is not just an ordinary word in capitals.

    "She's 12." and "It's about the booking system" only start with a capital because they
    start the sentence: an ordinary word that happens to be written short ("she's", "don't",
    "it's") is no more a name than "the" is.
    """
    lower = word.lower()
    if lower in COMMON_WORDS and lower != "i":
        return False
    stem = lower.split("'")[0]
    if stem != lower and (stem in lexicon.CORE_WORDS
                          or (stem.endswith("n") and stem[:-1] in lexicon.CORE_WORDS)):
        return False
    return lower not in lexicon.CHAT or lower == "i"


# Words that break a name in two: a capitalised ordinary word after a name is often part of
# it ("Eiffel Tower", "Niagara Falls"), but a verb or a grammar word starts a new clause
# ("Eiffel Tower Is Tall"). A pronoun at the start of a run belongs to the sentence, not the
# name, so "I Love New York" still names New York.
NAME_BREAKS = frozenset("""a an the and or but if then than that this these those there here
    i me my we our us you your he him his she her they them their it its am is are was were be
    been being do does did have has had will would shall should can could may might must not no
    so too very just really quite only also as at by for from in into of off on onto out over
    under up with within without about after again against all any both each few more most other
    some such own same what which who whom whose when where why how""".split())
LEADING = frozenset("""i i'm im i've ive i'll ill i'd id we we're we've you you're
    he he's she she's it it's they they're""".split())


def _capitalised(text):
    """Runs of capitalised words that read as names: the people and things a line mentions.

    A name can carry an ordinary word written with a capital: "Eiffel Tower" and "Niagara
    Falls" are one name, and the knowledge base knows the whole phrase. Only the run that
    starts with the name is kept, so an article in front of it ("the Eiffel Tower") and a
    sentence after it ("the Eiffel Tower is tall") do not become part of the name.
    """
    runs, current = [], []
    for token in text.split():
        bare = token.strip(".,!?;:\"'()[]")
        if bare[:1].isupper() and bare.replace("-", "").replace("'", "").isalpha():
            current.append(bare)
        else:
            if current:
                runs.append(current)
                current = []
    if current:
        runs.append(current)
    names = []
    for run in runs:
        if len(run) == 1:
            # A one-word run is left to the vocabulary, which adds a known place in its own
            # lowercase form: the name form here would change the case every reader gets.
            if _is_name(run[0]):
                names.append(run[0])
            continue
        if run[0].lower() in ARTICLES or run[0].lower() in LEADING:
            run = run[1:]
        if not run:
            continue
        start = next((at for at, word in enumerate(run)
                      if _is_name(word) or word.lower() in PLACES), None)
        if start is None:
            continue
        part = []
        for word in run[start:]:
            if word.lower() in NAME_BREAKS:
                break
            part.append(word)
        if part:
            names.append(" ".join(part))
    return names


def detect_entities(line, text=None):
    """The things the line names: people, places, titles and everyday objects."""
    text = line["text"] if text is None else text
    if small_talk_only(line["norm"]):
        return []       # "hiya pet how are you" greets someone, it does not name a pet
    entities, seen = [], set()

    def add(name, kind, at=None):
        key = name.lower()
        if key and key not in seen and len(key) > 1:
            seen.add(key)
            entities.append({"text": name.strip(), "type": kind,
                             "at": _position(line, key) if at is None else at})

    for match in re.finditer(r"\*([^*]{2,60})\*|\"([^\"]{2,60})\"", text):
        add(match.group(1) or match.group(2), "title")
    for person in re.finditer(r"\bmy ([a-z]+(?:\s+[a-z]+)?)", line["clean"]):
        word = person.group(1).split()[0]
        if word in RELATIONS:
            add("my " + word, "person")
            seen.add(word)                     # "my sister" already names the person
    for at in _ages_of_a_child(line["norm"]):
        # An age after a possessive is how a parent names the child the line is about: "my 4
        # month old has a rash" is "my son has a rash" with the person named by their age, and
        # until now no word in the line stood for the child, so the symptom was read as the
        # subject and the kind of line to answer was the wrong one. It has to be the person's
        # own ("my", "our"): "a 3 year old" is how people say what a holiday or a class is for
        # ("a cheap week in spain in may with a 3 year old"), so it is not the one the line is
        # about. The word after "old" is the other half: "a 10 week old kitten" and "my 6
        # month old dog" name an animal, and a machine's age is said the other way round ("my
        # boiler is 6 weeks old"), which `AGE_AFTER` has already left out.
        after = line["norm"][at + 3] if at + 3 < len(line["norm"]) else ""
        if line["norm"][at - 1] not in THE_PERSONS_OWN:
            continue
        if after and after not in AGE_OF_A_CHILD_WORDS and (after in PETS or _thing(after)):
            continue
        add(" ".join(line["norm"][at - 1:at + 3]), "person", at=at - 1)
    for run in _capitalised(text):
        if run.lower() in {"i", "i'm", "im"}:
            continue
        first_word = run.lower().split()[0]
        kind = "place" if run.lower() in PLACES or first_word in PLACES else "name"
        if kind == "name" and _said_as_a_place(run, line["norm"]):
            kind = "place"
        add(run, kind)
    verdicts = _bad_verdict_positions(line["norm"])
    for index, word in enumerate(line["norm"]):
        if index in verdicts:
            continue                           # "is a joke" is a verdict on the thing, not a thing
        asked = _asked_as_a_country(line["norm"], index)
        if word in PLACES and _names_a_person(line["norm"], index):
            continue                           # "my mate paris" is a person, not the city
        if word in PLACES and (_names_a_place(word, text, asked)
                               or _placed_by_a_word(line["norm"], index)):
            add(word, "place")
            continue
        if word in RELATIONS:
            # A relation the line did not type is one the reading spelled out ("my dd" is read
            # as "my daughter"), and the person has to read back the way the word does: the
            # possessive is part of the name, so "my dd fell off the slide" names the same
            # person as "my daughter fell off the slide" and gets the same answer. Only a word
            # the line did not type is joined to its possessive, so "his sister" is unchanged.
            if (index and word not in line["clean"].split()
                    and line["norm"][index - 1] in OWNERS):
                add(line["norm"][index - 1] + " " + word, "person", at=index - 1)
                seen.add(word)
                continue
            add(word, "person")
            continue
        thing = _thing(word)
        if thing:
            add(thing, "thing")
    entities.sort(key=lambda entity: entity["at"])
    return entities


# A name after one of these words is a place even when the vocabulary has never seen it:
# "a weekend in Ljubljana", "flying to Osaka".
PLACE_WORDS = frozenset("""in at from near around across through visit visiting visited
    outside inside via""".split())
# "to" points at a person as often as at a place: "i said to Sarah that i was tired" is not
# travel, so a name after these words needs a travel word in the line to be read as a place.
PLACE_WORDS_WITH_CUE = frozenset("""to towards toward""".split())

# Written like a name, but not a place: "a budget in Excel", "a draft in Word", "she works at
# Google". A product or a company is where a job happens or where a file lives.
NOT_PLACES = frozenset("""excel word powerpoint outlook onenote slack zoom teams skype discord
    facebook instagram twitter whatsapp tiktok youtube netflix spotify amazon ebay etsy google
    gmail github gitlab python javascript chrome safari windows android iphone ipad mac
    photoshop canva notion trello jira dropbox onedrive icloud uber airbnb booking expedia
    linkedin paypal ebay tinder
drive docs sheets slides mail calendar
tesco sainsbury asda aldi lidl waitrose morrisons coop boots argos ikea currys""".split())
WORK_WORDS = frozenset("""work works working worked workplace office job jobs shift shifts
    employer company meeting meetings boss manager team interview roster rota colleagues""".split())


def _said_as_a_place(run, norm):
    """True when the line puts the name where a place goes ("in Ljubljana", "to Osaka")."""
    first = run.split()[0].lower().strip(".,!?;:\"'()[]")
    if first in NOT_PLACES:
        return False
    for index, word in enumerate(norm):
        if word != first:
            continue
        if _places_a_name(norm, index):
            return True
        # An article between the place word and the name keeps the name in the place: "a
        # weekend in the Eiffel Tower" is still a place, and "at the Shard" is one too.
        if index >= 2 and norm[index - 1] in PLACE_THING and norm[index - 2] in PLACE_WORDS:
            if norm[index - 2] == "at" and set(norm) & WORK_WORDS:
                return False
            return True
        return False
    return False


# A place word right before a name places it, even in lower case: "museums in rome",
# "hotels in bath", "flights to nice". An article or a possessive in between keeps the word an
# ordinary thing: "in the bath", "to my reading group".
PLACE_THING = frozenset("the a an my your his her our their this that some any another".split())


def _placed_by_a_word(norm, index):
    """True when the word sits right after a place word ("in rome"), not after an article."""
    return _places_a_name(norm, index)


def _has_travel_word(norm):
    """Does the line carry a word that is about going somewhere ("flights", "visit", "trip")?"""
    words = set(norm)
    if words & TRAVEL_CUES:
        return True
    return any(word[:-1] in TRAVEL_CUES for word in words if word.endswith("s"))


def _places_a_name(norm, index):
    """Does the word at index sit where a place goes, so the word before it places the line?

    "in rome", "at the airport in Lisbon" place a line on their own. "to" does not: it points
    at a person just as often ("i said to Sarah"), so it needs a travel word in the line.
    "at" with a work word around it names a workplace ("she works at Google"), not a place.
    """
    if index < 1 or index >= len(norm):
        return False
    before = norm[index - 1]
    if before in PLACE_WORDS_WITH_CUE:
        return _has_travel_word(norm)
    if before not in PLACE_WORDS:
        return False
    if before == "at" and set(norm) & WORK_WORDS:
        return False
    return True


# Place names that are also the word a kitchen or a shop uses every day: "is it too late to
# put the turkey in" is a bird, "a weekend in Turkey" is the country. The vocabulary does not
# know every one of them ("turkey" was not in it), so they are listed here and need a capital
# letter, or a place word in front of them ("in turkey"), before they count as a place.
#
# The list is of words that really are ordinary words, not of places the reader's word list
# happens to hold. It held "leeds", "france", "spain", "lisbon", "rome", "tokyo", "sydney",
# "kyoto" and "australia" as names, and asking the word list whether a place name is also a
# word meant that "we are moving to leeds", "is leeds a good place to live" and "how far is it
# to rome" named no place at all, so nothing in the chat could be about it.
#
# "new" is the same case the other way round: it is a word the deck uses every day ("a new
# sofa"), and it is also the first half of "new york" and "new zealand", so it still needs
# the capital.
PLACE_HOMOGRAPHS = frozenset("""turkey china brazil bath reading new""".split())
# The ones that are also countries, where the other reading is the bird or the cup.
COUNTRY_HOMOGRAPHS = frozenset("""turkey china brazil""".split())

# Nobody types the capital letter on a phone, so a country name that is also an ordinary word
# needs a second way to say it is the country: a word only a country is asked about ("is
# turkey hot in june", "how safe is turkey", "whats the currency in turkey"), or another
# place in the same comparison ("turkey or greece for a family").
COUNTRY_CUES = frozenset("""hot warm cold sunny rainy weather temperature safe dangerous
    expensive cheap currency capital visa language speak driving flights flight hotel hotels
    resort beaches beach coast airport north south east west trip holiday visit visiting
    travel travelling traveling season best part parts city cities region regions
    january february march april may june july august september october november
    december""".split())
COMPARE_WORDS = frozenset("or and vs versus compared than".split())
ARTICLES = frozenset("the a an my our your his her their this that these those some any".split())


def _a_country_named(entity):
    """Is this a place the sentence has said is the country, though the word is also a thing?

    The entity is typed by the place rules - a capital letter, a place word in front, a word only
    a country takes, "in europe" after it - so a place whose last word is also an everyday thing
    is the country here, and the everyday thing is not what the line is about.
    """
    if not isinstance(entity, dict) or entity.get("type") != "place":
        return False
    text = entity.get("text") or ""
    words = text.lower().split()
    return bool(words) and words[-1] in PLACE_HOMOGRAPHS


def _set_in_a_place(norm, index):
    """Is the word at index said to be somewhere, the way a country is? "is turkey in europe",
    "is china in asia", "china is bigger than india". A place named after it with "in" between
    ("turkey in europe") or a comparison with another place says the word is the country, not
    the bird or the cup: nothing is said to be "in europe" except a place.
    """
    if index + 2 < len(norm) and norm[index + 1] == "in" and norm[index + 2] in PLACES \
            and norm[index + 2] not in PLACE_HOMOGRAPHS:
        return True
    for near in range(max(0, index - 3), min(len(norm), index + 4)):
        if near != index and norm[near] in PLACES and norm[near] not in PLACE_HOMOGRAPHS:
            between = norm[min(index, near):max(index, near)]
            if any(word in COMPARE_WORDS for word in between):
                return True
    return False


def _asked_as_a_country(norm, index):
    """Is the line about the country, not about the thing the country is also called?

    "is turkey hot in june" and "how safe is turkey" ask about the country; "the turkey is
    still frozen" does not, and the words only a country takes ("weather", "visa", "currency")
    are how it is asked without a capital letter.
    """
    if index and norm[index - 1] in ARTICLES:
        return False                       # "the turkey", "my china": the thing, not the country
    if set(norm) & COUNTRY_CUES:
        return True
    if _set_in_a_place(norm, index):
        return True
    for near in range(max(0, index - 2), min(len(norm), index + 3)):
        if near != index and norm[near] in PLACES and norm[near] not in PLACE_HOMOGRAPHS:
            between = norm[min(index, near):max(index, near)]
            if any(word in COMPARE_WORDS for word in between):
                return True
    return False


# A place name that is also somebody's name: a person word in front of it ("my mate paris", "my
# aunt savannah"), "called"/"named" before it ("my nan is called florence"), or "<name> is my
# <relation>" after it ("georgia is my daughter") makes the word a person, not the place. The
# word still reads as a place where the line puts it where a place goes: "my friend is in paris",
# "we went to paris with my mate".
NAME_FRAMES = frozenset("called named call calls".split())


def _names_a_person(norm, index):
    """Is the word at index somebody's name in this line, though the vocabulary knows it as a
    place?"""
    before = norm[index - 1] if index else ""
    if before in PERSON_WORDS or before in NAME_FRAMES:
        return True
    return (index + 3 < len(norm) and norm[index + 1] == "is" and norm[index + 2] == "my"
            and norm[index + 3] in PERSON_WORDS)


def person_names(line):
    """The place words this line uses as somebody's name, in the order said.

    "my mate paris is visiting" is a friend, not the city: the knowledge base must not read the
    word as the place the line is about. Kept as its own list so the memory lane can still see
    the name, and every domain gets the same answer to "is this a place here".
    """
    norm = line["norm"]
    seen, names = set(), []
    for index, word in enumerate(norm):
        if word in PLACES and word not in seen and _names_a_person(norm, index):
            seen.add(word)
            names.append(word)
    return names


def _names_a_place(word, text, asked=False):
    """Some place names are also ordinary words ("bath", "reading", "turkey"): those only name
    a place when the line writes them as one, or asks about the country."""
    if word not in PLACE_HOMOGRAPHS:
        return True
    if asked and word in COUNTRY_HOMOGRAPHS:
        return True
    return re.search(r"\b%s\b" % word.capitalize(), text) is not None


def _position(line, name):
    """Where in the line the first mention appears, so entities read in the order said."""
    first = name.split()[0]
    for index, word in enumerate(line["norm"]):
        if word == first or word.startswith(first):
            return index
    return len(line["norm"])


def _thing(word):
    """The everyday thing a word names, singular, or None.

    A short word is looked up before it is turned away. The length check below is there for the
    plural endings - "as" is not "a" and "is" is not "i" - but it was also throwing away every
    three-letter thing `THINGS` holds, so "egg", "pot", "pan", "tap", "cup", "car", "job" and
    fifty-odd more named nothing at all. A line with no thing of its own ("how long do i boil an
    egg") is then read as a follow-up on whatever came before it, and the mince from the turn
    ago answered the question about eggs.
    """
    if word in THINGS:
        return word
    if len(word) <= 3:
        return None
    for candidate in (word.rstrip("s"), word[:-2] if word.endswith("es") else None,
                      word[:-3] if word.endswith("ies") else None):
        if candidate and candidate in THINGS:
            return word
    return None


WORD_DIGITS = re.compile(r"[0-9]+(?:[.,][0-9]+)?")

# A word in front of a relation makes a different relation, and people say these far more often
# than the plain list suggests: a stepson is not the son, and a grandson is not the son either.
# Built from the relations below rather than listed again, so "my stepson is 21 and my daughter
# is 7" names two people the way "my son is 21 and my daughter is 7" does, instead of reading the
# step-word as a thing the line mentioned and losing the fact.
# Only the relations that name one person: a stepchildren or a grandparents is a group, and those
# words stay out so a group is never read as one person.
_STEPPED_RELATIONS = ("mum", "mom", "mother", "dad", "father", "son", "daughter", "brother",
                      "sister")
_GRAND_RELATIONS = ("mum", "mom", "mother", "dad", "father", "son", "daughter", "child")
_KIN_BUILT = tuple(["step" + word for word in _STEPPED_RELATIONS]
                   + ["grand" + word for word in _GRAND_RELATIONS])

RELATIONS = frozenset("""
son daughter kid kids child children baby toddler mum mom mother dad father husband wife
partner boyfriend girlfriend friend friends boss manager colleague brother sister aunt
uncle cousin gran grandma grandad grandpa grandmother grandfather neighbour neighbour
landlord flatmate housemate boss team pet dog cat puppy kitten
ex exes
""".split()) | frozenset(_KIN_BUILT) | frozenset(("gran", "granddad", "granny"))
# Somebody's former partner, said on its own: "my ex keeps texting me" was read as the texting
# rather than the person, so the line reached the phone and the marketing-calls entries and said
# "Got it. Is there anything you'd like a hand with?".

# The words people put in front of a person's name ("my mate paris", "my nan florence"): the
# relations, plus the familiar words that name a person without naming a relation.
PERSON_WORDS = RELATIONS | frozenset("""mate mates nan nana granny auntie pal lad lass fella
    bloke guy missus fiance fiancee stepson stepdaughter""".split())
# Every word that can name a person a symptom could be said of, built once.
THE_PEOPLE = _person_words()


def _spoken_numbers(norm):
    """The values the normalised line still says, so a digit read as a word can be dropped.

    "4 the kids" reads as "for the kids": the line has no four in it any more, so listing one
    would have a module do arithmetic on a number the person never said.
    """
    values = set()
    for word in norm:
        value = WORD_NUMBERS.get(word)
        if value is not None:
            values.add(value)
            continue
        digits = WORD_DIGITS.match(word)
        if digits:
            try:
                value = float(digits.group(0).replace(",", "."))
            except ValueError:
                continue
            values.add(int(value) if value.is_integer() else value)
    return values


# Words that can sit between a count word and its unit without changing what is counted: "half
# a kilo", "half of a lemon", "a couple of kilos". Nothing else may come between them: "two big
# cups" is not a measure, and "two and a half cups" is two numbers, not one.
NUMBER_FILLER = frozenset("a an of".split())

# "a" and "an" before one of these is one of it: "a kilo of pork" is a kilo the same way
# "1kg of pork" is. Only measures of an amount or a length are here. A length of time is not:
# "a week" in "a week ago" or "twice a week" is when or how often, and reading it as the
# count one would hand the modules a figure for a line that has none. Money is not either:
# "a pound" on its own is a pound in the pocket, and a unit only follows it in "a pound of".
A_PORTION_UNITS = frozenset("""g gram grams gramme grammes kg kilo kilos kilogram kilograms
lb lbs pound pounds oz ounce ounces ml millilitre millilitres milliliter milliliters
l litre litres liter liters tsp teaspoon teaspoons tbsp tablespoon tablespoons cup cups
mile miles km kilometre kilometres kilometer kilometers metre metres meter meters
foot feet ft inch inches""".split())
# A fraction or a count in front of the article owns the unit: "half a kilo" is half of one,
# not one, and "two and a half cups" is one and a half.
OWNS_THE_UNIT = frozenset(WORD_NUMBERS) | {"quarter", "quarters", "third", "thirds"}
# A pound is money as well as weight, so "a pound" alone is a pound in the pocket and only
# "a pound of" names a measure: "it costs a pound" is not a pound of anything.
A_PORTION_NEEDS_OF = frozenset({"pound", "pounds", "lb", "lbs"})


def _mixed_number(norm, position, value):
    """A count with a half after it: "one and a half kilos" is 1.5, not a half.

    Read as two numbers it is worse than as none at all - a recipe told "half a kilo" of
    potatoes it was told one and a half kilos of. So the "and a half" is folded into the count in
    front of it, and the words it used are returned so the half is not counted twice.
    """
    words = tuple(norm[position + 1:position + 4])
    # The article is optional: "two and a half" and "two and half" are the same count, and the
    # article is dropped far more often than it is kept when people type ("2 n half hours",
    # "two and half kilos"). Without it the count was read as two and the half as a number of
    # its own, so a recipe or a cooking time was given for half the amount. The quarter is the
    # same word with the same article in front of it: "an hour and a quarter".
    if not words or words[0] != "and":
        return value, ()
    step = 2 if words[1:2] in (("a",), ("an",)) else 1
    fraction = words[step] if len(words) > step else None
    if fraction not in ("half", "quarter"):
        return value, ()
    return (value + (0.5 if fraction == "half" else 0.25),
            tuple(range(position + 1, position + 1 + step + 1)))


def _the_figure_and_its_unit(digits, unit, raw=""):
    """The figure as it is said back, with the unit only when the word is a unit.

    The unit group of NUMBER_RE takes any word at all, which the unit table then reads: most
    words are not units and are dropped there, but the text kept them, so a figure said with a
    reason or a preposition was stored as "75 because", "34 and", "2000 on", "5 for". The text is
    what a reply says back ("You said 75 because."), and it is also what a later value is read
    out of, so the word that follows belongs in it only when it is a measure of the figure.
    """
    if not unit:
        return digits
    if unit == "%":
        return digits + "%"
    if unit in UNIT_WORDS or unit in CLIPPED_UNIT_WORDS or unit in FIGURE_SIZE_WORDS:
        # "70k" is written with its size word and "70 k" is not, so the gap is the one they typed.
        gap = " " if str(raw)[len(digits):len(digits) + 1].isspace() else ""
        return digits + gap + unit
    return digits


def detect_numbers(line):
    """Numbers in the line with their unit, so a module can use "2kg" or "20 minutes"."""
    out, seen, typed, merged = [], set(), [], set()
    norm = line["norm"]
    spoken = _spoken_numbers(norm)
    for match in NUMBER_RE.finditer(line["clean"]):
        raw = match.group(0).strip()
        digits, unit = match.group(1), (match.group(2) or "").lower()
        try:
            value = float(digits.replace(",", "."))
        except ValueError:
            continue
        if value.is_integer():
            value = int(value)
        if value not in spoken:
            continue                       # the digit was read as a word ("4 the kids")
        if unit in MIXED_JOINERS and MIXED_FRACTION.match(line["clean"], match.end()):
            continue                       # "2 n half hours" is one count and a half: the
            # word pass reads the figure and its fraction together, so it owns this one
        canonical = UNIT_WORDS.get(unit) or UNIT_WORDS.get(unit.rstrip("s"))
        if canonical is None:
            canonical = CLIPPED_UNIT_WORDS.get(unit)
        if canonical is None and not unit:
            clipped = CLIPPED_AFTER_A_SLASH.match(line["clean"], match.end())
            if clipped:
                canonical = CLIPPED_UNIT_WORDS.get(clipped.group(0).strip().lower(),
                                                   "years")
        typed.append((line["clean"][:match.start()].count(" "), value))
        key = (value, canonical)
        if key not in seen:
            seen.add(key)
            out.append({"value": value, "unit": canonical,
                        "text": _the_figure_and_its_unit(digits, unit, raw)})
    for position, word in enumerate(norm):
        if word in ("a", "an"):
            # "a kilo of pork", "a pint of milk", "a mile from here": the article is the count.
            if position + 1 < len(norm) and norm[position + 1] in A_PORTION_UNITS:
                before = norm[position - 1] if position else ""
                after = norm[position + 2] if position + 2 < len(norm) else ""
                unit = UNIT_WORDS.get(norm[position + 1])
                if norm[position + 1] in A_PORTION_NEEDS_OF and after != "of":
                    continue
                key = (1, unit)
                if before not in OWNS_THE_UNIT and unit and key not in seen:
                    seen.add(key)
                    out.append({"value": 1, "unit": unit,
                                "text": "%s %s" % (word, norm[position + 1])})
            continue
        value = WORD_NUMBERS.get(word)
        if value is None or _counts_as_number(norm, position):
            continue
        if position in merged:
            continue                           # the "half" of "one and a half": already counted
        if any(got == value and abs(at - position) <= 1 for at, got in typed):
            continue                           # "15%" is not also "fifteen"
        value, folded = _mixed_number(norm, position, value)
        merged.update(folded)
        unit = None
        step = 1 + len(folded)
        while position + step < len(norm) and step <= 5:
            after_word = norm[position + step]
            if after_word in UNIT_WORDS:
                unit = UNIT_WORDS[after_word]
                break
            if after_word not in NUMBER_FILLER:
                break
            step += 1
        key = (value, unit, word)
        if key not in seen:
            seen.add(key)
            out.append({"value": value, "unit": unit, "text": word})
    return out


# "one" is usually not a count: "nice one, thx", "the one with the blue cover", "which one".
ONE_IS_A_THING = frozenset("""the this that these those which no any each every another
    nice good great big small little wrong right other same next last first""".split())


def _counts_as_number(norm, position):
    """True when the word there is not being used as a count ("one" mostly is not)."""
    word = norm[position]
    if word != "one":
        return False
    following = tuple(norm[position + 1:position + 4])
    if following[:3] in (("and", "a", "half"), ("and", "an", "half")) \
            or following[:2] in (("and", "half"), ("and", "quarter")):
        return False                           # "one and a half kilos" is a count
    before = norm[position - 1] if position else None
    after = norm[position + 1] if position + 1 < len(norm) else None
    if after and after in UNIT_WORDS:
        return False                           # "one hour" is a count
    return before is None or before in ONE_IS_A_THING or after is None
