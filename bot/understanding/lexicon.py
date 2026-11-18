"""Word data for the understanding engine: common words, chat-speak, misspellings.

The understanding lane owns this file. Data lives here, mechanisms live in the sibling
modules (`normalize.py`, `kinds.py`, `topics.py`, `references.py`). Keep it plain data so other
lanes can extend a vocabulary without touching logic.

Nothing here is keyed by a whole sentence: these are words and short phrases, so the same
entry helps every line that uses it.
"""

import re

# The most common English words, roughly in order of frequency: the normaliser ranks typo
# candidates by position, so earlier words win a tie. Everyday vocabulary people use when
# they ask for help is mixed in (food, body, house, money, ...) so a typo anywhere in an
# ordinary sentence has a neighbour to match.
COMMON = """
the be to of and a in that have i it for not on with he as you do at this but his by from
# The words a person judges themselves with. The answers in bot/modules/chat.py key on them
# ("im a faliure", "i feel usless"), so the reading has to be able to hear a typo of one:
# a word the vocabulary does not hold cannot be repaired, and "i feel like a faliure" came
# back as "Got it. Is there anything you'd like a hand with?" while "i feel like a failure"
# was answered. Nothing here is new to the bot: it is the vocabulary the answers are written in.
failure failures useless worthless hopeless ashamed pathetic burden fraud disappointment
disappointment disgrace waste selfish jealousy uselessness failure
they we say her she or an will my one all would there their what so up out if about who get
which go me when make can like time no just him know take people into year your good some
could them see other than then now look only come its over think also back after use two how
our work first well way even new want because any these give day most us is are was were been
being am does did done doing has had having

hello hi hey morning evening night goodbye bye thanks thank please sorry yes yeah no nah nope
yep ok okay right sure fine cool great nice lovely good bad better best worse worst really
very super too much many more less little bit lot quite rather pretty enough almost just still
again once always never sometimes often usually maybe perhaps probably definitely actually
basically honestly literally obviously obviously anyway anyways somehow somewhere anywhere
everywhere nowhere here there where when why how what who whom whose which while until since
before after during between among through across along around behind beside beyond near off
onto over under above below inside outside toward towards without within upon about against

i you he she it we they me him her us them my your his its our their mine yours hers ours
theirs myself yourself himself herself itself ourselves themselves this that these those
someone somebody something anyone anybody anything everyone everybody everything nobody
nothing none all both each either neither other another such same different

is are was were am be been being do does did done have has had having can could will would
shall should may might must ought need dare let make made get got gotten go went gone going
come came come coming take took taken taking give gave given giving see saw seen seeing say
said saying tell told telling ask asked asking answer know knew known knowing think thought
thinking feel felt feeling want wanted wanting need needed needing like liked liking love
loved loving hate hated hating try tried trying start started starting stop stopped stopping
keep kept keeping put putting set setting run ran running walk walked walking drive drove
driving fly flew flying travel travelled traveled plan planned planning buy bought buying
pay paid paying sell sold selling find found finding look looked looking watch watched
watching read reading write wrote written writing learn learned learnt learning teach taught
teach teaching study studied studying work worked working cook cooked cooking bake baked
baking boil boiled boiling fry fried frying roast roasted roasting chop chopped chopping
wash washed washing clean cleaned cleaning fix fixed fixing build built building grow grew
grown growing plant planted planting water watered watering feed fed feeding walk walked

good bad great awful terrible fine okay nice lovely wonderful brilliant perfect horrible
happy sad angry tired hungry thirsty cold hot warm cool freezing boiling busy stressed
worried nervous scared afraid anxious excited bored lonely upset disappointed pleased glad
proud grateful thankful sorry guilty embarrassed confused lost stuck fed up

morning afternoon evening night today tomorrow tonight yesterday week weekend month year
hour minute second time day date monday tuesday wednesday thursday friday saturday sunday
january february march april may june july august september october november december
spring summer autumn fall winter christmas easter holiday holidays birthday anniversary

home house flat apartment room kitchen bedroom bathroom living room garden garage door
window wall floor ceiling roof table chair bed sofa carpet shelf cupboard fridge oven hob
microwave kettle sink toilet bath shower radiator boiler heating washing machine dishwasher
light lamp plug socket key lock bag box car bike bicycle bus train plane flight airport
station ticket road street city town village country place park river sea beach mountain
hill forest lake garden shop store market supermarket bank post office hospital doctor
dentist pharmacy school university office work job boss colleague meeting money price cost
cheap expensive card cash salary bill budget loan debt savings account

food drink meal breakfast lunch dinner snack water tea coffee milk juice wine beer bread
rice pasta potato potatoes tomato onion garlic carrot chicken beef pork lamb fish egg eggs
cheese butter milk yogurt cream sugar salt pepper oil sauce soup salad sandwich pizza cake
biscuit bread fruit apple banana orange lemon strawberry chocolate vegetable vegetables
beans lentils nuts vegetarian vegan recipe cook oven bake boil grill roast fry

head face eye eyes blink blinks blinking ear ears nose mouth tooth teeth neck throat shoulder arm hand hands hiss
finger fingers chest back stomach leg legs knee foot feet toe toes skin hair blood body
tired sleep asleep wake woke waking rest night bed dream pain hurt ache ache sore sick ill
illness cold flu fever cough headache doctor medicine tablet hospital ambulance diarrhea
hangover hungover jetlag crackered

cat cats dog dogs puppy kitten pet pets bird birds fish goldfish hamster rabbit horse
chocolate dangerous vet lead walk train feed tank

child children kid kids baby toddler son daughter boy girl mother mum mom father dad
parent parents husband wife partner family sister brother friend friends grandmother
grandfather grandma grandpa uncle aunt cousin neighbour colleague

book books read reading novel story film films movie movies watch series show tv
television music song songs podcast game games board game play theatre concert
recommend recommendation best favourite favorite character author writer episode season
boring funny interesting exciting scary sad happy mardy crabbit

computer laptop phone mobile tablet screen keyboard mouse internet wifi email password
software app website online download upload battery charger cable printer photo camera
video call message text imessage imessages

# The cake: "parkin" is "parking" with the g left off, which is the one repair of its kind that
# a real word loses, and "what is parkin" wants the cake and its follow-up.
parkin

fast slow heavy light big small large little long short tall wide narrow new old young
younger older easy hard simple difficult quick quickly slowly careful safely safe
open closed full empty free cheap clean dirty strong weak loud quiet

pounds euros dollars pence cents money cost price cheap expensive worth

jeans trousers pants shoes trainers boots socks shirt tshirt sweatshirt jumper hoodie jacket
coat skirt dress suit hat cap gloves scarf belt wallet purse bag backpack umbrella
wool wood cotton linen silk denim leather velvet metal plastic
ring watch jewellery makeup razor toothbrush toothpaste towel soap shampoo brush comb
pillow blanket duvet curtain rug mat cushion mirror picture poster bin basket
bottle glass cup mug plate bowl knife fork spoon pan pot tray jug tin jar tin foil
washing dryer iron hoover vacuum broom mop sponge cloth detergent bleach
sour cream sauce spice herb herbs pepper sugar flour yeast dough batter
scifi sciencefiction poem poetry joke jokes riddle quiz crossword puzzle
battery charger headphones speaker router printer scanner screen keyboard mouse
vitamins protein fibre fibre carbs calories diet weight muscle
stretch stretching workout gym run running walk cycling swim swimming yoga
budget savings insurance mortgage rent landlord tenant deposit invoice receipt
interview cv resume application deadline meeting email colleague manager
homework exam revision grades term lesson class teacher student
volcano earthquake storm thunder lightning rainbow clouds rain snow wind fog ice
leaves leaf tree trees plant plants soil compost weed weeds seed seeds bulb
dog cat rabbit hamster guinea pig budgie parrot goldfish kitten puppy
shrank shrunk stretched stretch colour color favourite favorite
wrote written built bought brought caught chose chosen drank drunk ate eaten fell fallen
flew flown forgot forgotten gave given grew grown hid hidden knew known lay lain lent
lost made meant met paid put rode ridden rang rung rose risen said saw seen sold sent
sang sung sat slept spoke spoken spent stood stole stolen swam swum taught thought threw
thrown understood woke worn won

add adopted adult adults advice already allergic allotment antibiotics appointment architecture
argument australia bacteria badge balcony ball basil begin bio bleed bleeding blossom blue bot
bottom breath bring broken cancelling capital causing change chasing chat cheapest check cherry
climate coach coached commute completely conference course credit cricket cut debit defensive
didn difference dinosaurs disease difference drains dried driver dropping duty easiest east eat
eating empire end energy erupts essay ever every exactly explain failed fair fan feedback fewer
fight finally finish finished firefighter five float florence football footie footy
four fractions france
french fresh friendship front fun gift giza gory group handle happens hasn haven help helpful
helps heron hides history idea ideas idiot improve industrial inspection instead instrument japan
jet jigsaw joint journey knocked kyoto lag land last lately later leeds left leftover line
lisbon lower main mainly martian match meat men mentioned miles miss mix moon mould move moved
moving musical name next nine noise nurse nutshell offside overgrown overnight own oxygen pack
paint part party pass performance person photosynthesis piano pick plumber politely powder
prepare project proper pulls pyramids questions race rail rainy recline red repairing replace
rescue review revising revolution rid role rolled roman rome rosemary roughly rubbery rude
ruining rule rules runny sam sandwiches sane save science scrambled screenshot seat secondary
security sentence session settle shift shouldn signal simply sitting six sky slipped soda
sounding sounds sourdough space spain spanish speaking speech spend spinach split sticky stiff
struggling suggest sunlight sydney system talk talked team temperature test theme thighs things
thirty thoughtful three thunderstorm tips titles tokyo tom top tricks trip true trust tulip
turn turning twins unblock university unwind usual vaccines virus visiting vocabulary volcanoes
wedding wee west wimbledon word wrong yellow yet yolk
hell
baker bridge bumpy fitter ounce packet plaster poison power primer shout sleepy stroke sweaty
tower

# Found the same way: a scan of every word the knowledge base and the deck use, run through the
# one-edit fixer. Each of these is a word of its own that was being "corrected" into another one
# (bee->be, thin->thing, wee->we, satin->sating, area->are, died->did, wars/wasp->was).
area bee died wars wasp wee satin thin thick war
# A pudding, not a small animal: "chocolate mousse" was read as "chocolate mouse".
mousse
# One edit from a feeling and a word of its own in a line people write often: "i think my email
# has been hacked" was being read as "whacked", and a rabbit that "hasnt pooed" as "pooped".
hack hacked hacking hacker poo pooed pooing
"""
# The same word, spelt the American way. Nothing was mistyped: a great many people spell
# "colour", "mouldy", "favourite" and "neighbour" the way they were taught, and the knowledge
# base, the deck and the replies are all written in the British spelling, so an otherwise
# perfect line matched nothing ("why does my bread go moldy so fast" got a search hedge).
# Only spellings that differ by a letter and nothing else are here: a word that is a different
# word across the Atlantic ("eggplant", "faucet", "diaper") is a fact about the world, not a
# spelling, and stays out.
US_SPELLINGS = {
    "mold": "mould", "molds": "moulds", "molded": "moulded", "moldy": "mouldy",
    "moldier": "mouldier", "moldiest": "mouldiest",
    "color": "colour", "colors": "colours", "colored": "coloured",
    "coloring": "colouring", "colorful": "colourful",
    "flavor": "flavour", "flavors": "flavours", "flavored": "flavoured",
    "flavoring": "flavouring", "flavorful": "flavourful",
    "favorite": "favourite", "favorites": "favourites",
    "favor": "favour", "favors": "favours", "favored": "favoured",
    "neighbor": "neighbour", "neighbors": "neighbours",
    "neighborhood": "neighbourhood", "neighborhoods": "neighbourhoods",
    "behavior": "behaviour", "behaviors": "behaviours",
    "humor": "humour", "labor": "labour", "labors": "labours",
    "rumor": "rumour", "rumors": "rumours", "odor": "odour", "odors": "odours",
    "vapor": "vapour", "savior": "saviour",
    "center": "centre", "centers": "centres", "centered": "centred",
    "theater": "theatre", "theaters": "theatres",
    "liter": "litre", "liters": "litres",
    "fiber": "fibre", "fibers": "fibres",
    "gray": "grey", "grays": "greys",
    "pajamas": "pyjamas", "pajama": "pyjama",
    "catalog": "catalogue", "catalogs": "catalogues",
    "dialog": "dialogue", "dialogs": "dialogues",
    "defense": "defence", "offense": "offence", "pretense": "pretence",
    "traveler": "traveller", "travelers": "travellers",
    "traveling": "travelling", "traveled": "travelled",
    "canceled": "cancelled", "canceling": "cancelling",
    "labeled": "labelled", "labeling": "labelling",
    "modeled": "modelled", "modeling": "modelling",
    "fueled": "fuelled", "fueling": "fuelling",
    "jewelry": "jewellery", "license": "licence",
    "aluminum": "aluminium", "mom": "mum", "mommy": "mummy",
    "apologize": "apologise", "organize": "organise", "organized": "organised",
    "realize": "realise", "realized": "realised", "recognize": "recognise",
    "recognized": "recognised", "memorize": "memorise", "memorized": "memorised",
}


# Everyday doing words: the ones people use when they say what went wrong ("me back is killin
# me", "me n my sister keep arguin"). The normaliser restores a left-off final g on its own (a
# word ending in -in whose -ing form it knows), and a lemma here brings its -ing, -ed, -s, -er
# and -ly forms with it, so the mechanism has something to restore.
COMMON += """
kill argue complain nag moan yell cry panic procrastinate gamble overspend vape smoke bite itch
sneeze vomit spill shrink thaw defrost sharpen descale repaint tidy declutter sweep prune repot
scour scrub soak rinse hang fold unclog worry stress ruin snore drool twitch limp shiver sweat
burn choke gasp bang churn pound sting swell tingle chat nod rub stab throb
dance cramp hurry kneel crouch jog hobble stagger retch unpack chuck wound juggle whinge
scribble trim dust polish sprinkle knead whisk stir simmer mash peel dice slice grate squeeze
# Ordinary words that begin with the sound the f-repair reads as a swapped "th": "fought",
# "frown", "fins" and "fats" are their own words, so the repair must not bend them into
# "thought", "thrown", "thins" and "thats". Kept here because the repair trusts this list to
# say what is already a word.
fought frown frowns frowning fins fats fens finer fated funder
"""

# Everyday words the one-edit repair bent into another word, because the vocabulary did not
# hold them: "how do i pray" was read as "how do i pay", "is fury any good" as "is furry any
# good", "everyone just stared" as "starred", "the sleeper to fort william" as "thort william",
# a London borough as "healing", and a garden of "0.15 acres" as "0.15 cares". A word the reader
# knows is left as it was typed, so the words a person says plainly belong here.
COMMON += """
pray prayed praying prayer prayers fury stare stared staring stare fort acre acres cute
"""

# How a body is, said of yourself: "im clamy", "im queezy", "im akey". These are ordinary words,
# and the reading and the memory store already use most of them for the way somebody is, but the
# repair only lands on a word the lexicon holds, so a letter short of one was read as a name:
# "im clamy" was answered "Nice to meet you, Clamy" and the clammy answer line was never reached.
COMMON += """
clammy woozy jittery queasy bleary puffy giddy edgy antsy twitchy drowsy mopey quivery fidgety
wobbly phlegmy wheezy croaky sniffly snotty achy shaky crampy bloated shivery husky sneezy
rattly itchy lightheaded nauseous
"""

# Words that matter most when a typo has several neighbours: the normaliser prefers these.
CORE = """
the a an and or but not no yes is are was were be been have has had do does did
i you he she we they it me my your his her our their this that these those
what why how when where who which can could would should will just now then
today tonight tomorrow thanks thank please hello hi hey ok okay sorry good great
make get take go come see know think want need like try use find give tell say
"""

# The feeling words the reading and the replies know. A typo of one of these is that feeling
# ("knackerd", "exausted", "worrid"), which is worth its own list because it is a closed one:
# the shortest edit for an ordinary word is nearly always another ordinary word, so a general
# spell-fixer has to refuse, while next to a feeling word there is nothing to confuse it with.
def _words(text):
    """The words in one of the lists below, and not the notes written beside them.

    Each list sits next to the reason for its words - "the plain words for a low day", "the words
    the vocabulary held only as near-synonyms" - and the note is inside the same string so that a
    word and its reason stay together. Read as vocabulary, the notes are words too: the feeling
    list held "the", "reply" and "plain" because a comment said them, and when this round's note
    used the word "letter" the one-edit repair turned every "litter tray" in the deck into a
    letter. A note is what follows a "#", so it stops there, and only a word is kept.
    """
    words = []
    for line in str(text or "").splitlines():
        line = line.split("#", 1)[0]
        for word in line.split():
            bare = word.replace("-", "").replace("'", "")
            if bare.isalpha():
                words.append(word.lower())
    return frozenset(words)


# The temper a person is in and the end of their steam: "im fuming", "im seething", "im frazzled",
# "im incandescent". A typo of one of these is that feeling too.
FEELINGS = _words("""sad unhappy miserable down low gutted heartbroken crying tears
disappointed devastated depressed upset lonely alone isolated angry annoyed furious cross
irritated frustrated mad livid raging anxious worried worry nervous scared afraid
frightened stressed overwhelmed panic panicking dreading tired exhausted knackered
# The doing form of a worry: "im worrying", "im stressing", "im overthinking", "im obsessing".
# A word the reading calls a feeling has to be in this list, or "im worrying" is a name.
worrying stressing overthinking obsessing spiralling spiraling
shattered wiped sleepy bushed drained happy glad delighted thrilled pleased excited proud
relieved chuffed grateful thankful appreciate guilty ashamed embarrassed bored boring
stress cry terrified petrified panicky butterflies
weepy tearful homesick shy hungry starving thirsty peckish ravenous
rotten lousy meh rough crap rubbish grumpy restless numb
# "im worse", "im no better": a comparison of two states is how a bad day is told in a second
# turn, and a cue the reading calls a feeling has to be in this list or the line reads as a name.
worse
cheesed empty flat hollow blank
# The plain words for a low day: "i feel awful", "i feel hopeless", "im still grieving",
# "my anxiety is bad". The reading and the reply must agree on what a feeling word is.
awful hopeless worthless grieving mourning despair despairing anxiety
# The plain words for being unsure or worried about something: "im confused", "im concerned",
# and the moods that name themselves: glum, mardy, zonked.
confused confusing confusion puzzled baffled bewildered muddled
interested concerned glum mopey teary downhearted despondent blah bleh cranky
snappy tetchy ratty mardy jittery antsy edgy tense pooped whacked zonked
hungover hangover jet-lagged run-down crackered
# "im fried" is the same tiredness as "im wiped", and it is in the reading's tiredness list, so
# it has to be a feeling word here too: the two lists are read as one (MisspeltFeelingTest).
fried
fuming seething frazzled incandescent narked miffed
# "im awesome", "im hopeful", "im emotional" were answered "Hi Awesome - fair enough" and "Nice
# to meet you, Emotional": the lexicon held the near-synonyms ("excited", "glad") but not the
# words themselves, so neither the reading nor the name reader knew them.
awesome hopeful emotional
# The same gap, one letter out: "im irritble" and "im aprehensive" are answered "Nice to meet
# you, ..." because the one-edit repair has nothing to repair them to - "irritable" and
# "apprehensive" were not in the vocabulary at all, and the lists above held only their
# near-synonyms ("irritated", "anxious"). "im cheerful" was answered "I'm listening" for the
# same reason.
irritable apprehensive cheerful
# The ending a state is said with, which a reply already answers and the reading did not know:
# the pools read "im wrecked", "im spent", "im swamped" and "im jetlagged" as the tired and
# stressed days they are, but none of those words was in the vocabulary, so the one-edit repair
# had nothing to repair a slip toward and the line fell out of its pool altogether - "im wrcked"
# got "Got it. Is there anything you'd like a hand with?", and "im spnt", "im bet" and "im ded"
# were answered "Nice to meet you, Spnt" / "Bet" / "Ded" - a word the reading does not know,
# standing where a state stands after "im", is a name. A state typed correctly was read as an
# introduction for the same reason ("im cheery" was "Hi Cheery").
# Every word here is one a reply in bot/modules/ already answers in a line of its own ("worn"
# and "wearing" only in "worn out" and "wearing thin"), and a word the lexicon knows keeps its
# own meaning in the repair: "boat" is not bent to "beat" and "deaf" is not "dead".
beat dead draining exhausting fagged knackering spent tiring wearing worn wrecked
overwhelming stressful swamped jetlagged cheery buzzing brilliant
# The colour as the mood: "im blue", "feeling a bit blue". It was not a feeling word at all, so
# "im blue" was read as a name and answered "Nice to meet you, Blue". The state has to be said of
# the person (see SELF_ONLY_STATE), because a door and a sea are blue too.
blue
# A condition somebody says they have is how they are, not who they are. "im bipolar" was
# answered "Nice to meet you, Bipolar", and the store filed the word as a name, so every later
# line knew the person by it. The seven below were found by probing the class; the rest are the
# conditions a person names about themselves in the same position. A word here is a state the
# reading knows, which is what stops a name.
bipolar schizophrenic anorexic bulimic narcoleptic psychotic infertile sterile paranoid
transgender nonbinary hiv""")

# How the body looks and feels when something is wrong with it, said as a bare word after "im".
# None of these was a state the reading knew, so the name reader took the word for what the person
# is called: "im spotty", "im pale", "im tender" and "im grey" were answered "Nice to meet you,
# Spotty. What can I help with?", the store kept the word as their name, and every later line knew
# them by it. A word that says how the body is, said in the place where the person says how they
# are, is never a name - so they are in this list, which is what the name reader asks, and the
# pools that answer them are BODY_STATES in bot/compose/fallback_data.py (bot/memory/ack.py keeps
# its own copy of the words, because the echo has to decline the line and must not import the
# composer).
A_BODY_STATE = frozenset("""pale pallid ashen grey gray greyish grayish mottled blotchy spotty
puffy bloated clammy flushed feverish shivery shaky tender husky snotty sniffly""".split())
# A state is not a name. "im hurt", "im desperate", "im content", "im broken", "im hungover"
# were all introductions - "Nice to meet you, Hurt. What can I help with?" - because the only
# thing between a bare word and a welcome was whether the engine knew it as a feeling. These say
# how the person is, not what they are called. They are kept apart from FEELINGS because that
# list also drives the one-edit repair, and a repair is not always wanted: "hangover" is one
# letter from "hungover", and the health topic for `what helps a hangover` went out with it.
# How the body and the mood are, said with an "-ing" and nothing else: "im starvin", "im fumin",
# "im freezin", "im shakin". The reading knows the verb ("starve", "fume") but not this form, so
# the g people leave off had nothing to be put back onto it.
# The dialect words for how somebody is that have no plainer word to stand in for them:
# "im chocka" (full up), "im chocker", "im manky", "im wonky", "im tickety" (tickety-boo),
# "im wabbit" (rabbit, done in) were read as introductions - "Nice to meet you, Manky. What can
# I help with?" - and the word was kept as the person's name. The ones that do have a plainer
# word are read as that word instead, in `DIALECT_STATES` below.
A_STATE = frozenset("""hurt hurting desperate content confused confusing broken drunk torn
hungover sober skint shattered wiped gutted
starving fuming freezing boiling raging aching itching shaking shivering sweating
chocka chocker manky wonky tickety wabbit""".split()) | A_BODY_STATE

# The same states and feelings with the g left off. The reader puts the g back from this list,
# so the word is not a guess and the mended spelling is the one the knowledge base is handed:
# "how long can i go without eating, im starvin" is about starving, and an echo says the word
# they meant.
# How a person can be, said in one word onto the "im": phones drop the space and people type
# "imsad", "imlonely", "imexhausted", "imsuicidal" in a hurry. None of those is a word, so the
# whole line was no line at all - "Got it. Is there anything you'd like a hand with?" where "im
# sad" gets the sad answer - while the tokens around them ("image", "impact", "import",
# "improve", "imagine", "immune") are words of their own and keep their meaning.
# Every feeling and state above is here, plus the everyday ones the pools already answer and the
# vocabulary does not carry: a person says "im fine", "im ok", "im done", "im fed up".
STATES_SAID_ONTO_IM = FEELINGS | A_STATE | frozenset("""
sick suicidal fine ok okay good better great done stuck lost back home here busy free fed
""".split())

STATES_WITHOUT_G = frozenset(word[:-1] for word in FEELINGS | A_STATE if word.endswith("g"))

# People give their name in the second sentence of a chat - "hi im lisa" - so a name has to keep
# its own reading. Only the commonest first names are here, and the list earns its place where a
# name sounds like a feeling: "im lisa" shares "lose"'s consonants and "im alan" shares
# "lonely"'s, so a rule that reads a feeling from a sound turned both introductions into a
# sympathy line. Nothing in the reading treats these words as anything else: it only says "this
# word is a name I know", so no feeling, topic or repair rule claims it first.
COMMON_NAMES = frozenset("""
abbie abigail adam adrian aiden aisha alan albert alex alexa alexander alfred ali alice alicia
allison amanda amber amelia amy ana anastasia andre andrea andrew andy angela angie anita ann
anna anne annette annie anthony antonio april archie arlene arnold arthur ashley audrey austin
ava ayesha barbara barry beatrice becky belinda ben benjamin bernard beth bethany betty beverly
bianca bill billy blake bob bobby bonnie boris brad bradley brandon brenda brendan brian bridget
brittany brooke bruce bryan caitlin callum calvin cameron camila carl carla carlos carmen carol
caroline carrie cary casey cassie catherine cathy chad charlene charles charlie charlotte chelsea
cheryl chloe chris christian christina christine christopher cindy claire clara clarence claudia
clifford clint cody colin connie connor craig crystal curtis cynthia daisy dale damian damon dan
dana daniel danielle danny darcy daren darlene darren darryl dave david dawn dean debbie deborah
debra denise dennis derek diana diane dianne dina dominic don donald donna dora doris dorothy
doug douglas duncan dustin dylan earl eddie edgar edith eduardo edward eileen elaine eleanor
elena eli elias elijah elizabeth ella ellen ellie elliot eloise elsie emily emma emmanuel enid
eric erica erik erin ernest esther ethan eva evan eve evelyn fiona florence floyd frances
francis frank fred freda freddie gabriel gabrielle gail gareth gary gavin gemma gene geoff
geoffrey george georgia gerald geraldine gilbert gina glen glenda glenn gloria gordon grace
graham grant greg gregory gwen gwendolyn hannah harold harriet harry harvey hazel heather
hector heidi helen henry herbert holly hugh hugo ian ida ike imogen irene iris isaac isabel
isabella isla ivan jack jackie jacob jade jaime jake james jamie jan jane janet janice jared
jasmine jason jay jayne jean jeff jeffrey jemma jenny jeremy jerome jerry jess jessica jill
jim jimmy jo joan joanna joanne jodie joe joel joey john johnny jon jonathan jordan jose
joseph josephine josh joshua joyce juan judith judy julia julian julie june justin kara karen
karl kate katherine kathleen kathryn kathy katie katrina kay kayla keith kelly kelsey ken
kenneth kerry kevin kieran kim kimberly kirk kirsty kit kurt kyle lana lance lara larry laura
lauren laurie lawrence leah lee leila lena leo leon leonard lesley leslie lester lewis li liam
lilian lily linda lindsay lindsey lionel lisa lloyd lois lola loren lorenzo lorraine louis
louisa louise lucas lucia lucy lucy luis luke lydia lynn lynne mabel maddie madeleine madison
mae maggie malcolm mandy manuel marc marcus margaret maria marian marie marilyn marina mario
marion marjorie mark marlene marsha marshall martha martin marvin mary mason matt matthew
maureen maurice max maxine may megan mel melanie melissa mia micah michael michele michelle
mickey mike mildred miles millie milton miranda miriam molly monica morgan muhammad myra
nadia nancy naomi natalie natasha nathan neil nelson nicholas nick nico nicola nicolas nicole
nigel nina noah noel nora norma norman olga oliver olivia omar oscar owen pablo paige pamela
patricia patrick patsy paul paula pauline pearl pedro peggy penny percy pete peter phil philip
phillip phoebe phyllis polly peter priya rachel ralph ramon randall randy raul ray raymond
rebecca reggie regina renee rex rhonda ricardo richard rick ricky rita rob robbie robert
roberta roberto robin robyn rodney roger roland ron ronald ronnie rosa rosalie rose rosemary
ross roy ruben ruby russell ruth ryan sally sam samantha samuel sandra sara sarah scott sean
sebastian selina seth shane shannon sharon shawn sheila shelby shelley sherry shirley sid
sidney simon sofia sonia sonya sophia sophie stacey stacy stanley stella stephanie stephen
steve steven stuart sue susan susie suzanne sylvia tamara tammy tanya tara ted teresa terry
tessa thelma theodore theresa thomas tiffany tim timothy tina toby todd tom tommy toni tony
tracey tracy travis trevor tricia trish tristan troy tyler val valerie vanessa vera veronica
vernon vicki vicky victor victoria vince vincent violet vivian vivien wade walter wanda warren
wayne wendy wesley whitney wilbur wilfred will william willie wilson winifred yasmin yolanda
zach zachary zoe zoe
""".split())

# A word that is the sound of a feeling and is spelled as another word. "im board" is how
# people type "i'm bored" and "im tried" is "i'm tired"; both are ordinary words, so no
# spell-fixer may touch them anywhere else - "the board is warped", "i tried the gym" keep
# their words. Only the position a feeling goes in reads them as one (normalize.FIRST_PERSON_BE).
SOUNDS_LIKE_A_FEELING = {
    "board": "bored",
    "tried": "tired",
}

# CORE are single words, but people write them joined up: "she's", "it's", "don't".
CORE_WORDS = frozenset(CORE.split())

# Chat-speak and shorthand, as whole tokens or short phrases. Keys are what people type,
# values are what they meant, in ordinary words.
CHAT = {
    "u": "you", "ur": "your", "ure": "you are", "urs": "yours", "r": "are", "y": "why",
    "ya": "you", "yah": "yes", "yeh": "yes", "yea": "yes", "yep": "yes", "nope": "no",
    "k": "ok", "kk": "ok", "okey": "ok", "okey dokey": "ok", "cn": "can", "cud": "could",
    "ar": "are", "wuz": "was", "duz": "does", "hav": "have",
    "thx": "thanks", "thnx": "thanks", "thanx": "thanks", "ty": "thanks", "tysm": "thanks",
    "cheers": "thanks", "ta": "thanks", "tyvm": "thanks so much",
    "pls": "please", "plz": "please", "pleas": "please", "plss": "please",
    "bc": "because", "bcoz": "because", "becos": "because", "cuz": "because",
    "coz": "because", "cos": "because", "cause": "because", "caus": "because",
    "thru": "through", "tho": "though", "tho'": "though", "altho": "although",
    "nite": "night", "tonite": "tonight", "2nite": "tonight", "tmrw": "tomorrow",
    "tomoz": "tomorrow", "tomoro": "tomorrow", "tommorow": "tomorrow", "2moro": "tomorrow",
    # The shortest way people type tomorrow: "speak tmoro", "see u tmoro". The table held
    # "tmrw", "tomoz", "tomo" and "tmorro" but not this one, so a sign-off at the end of it
    # ("speak tmoro") was not a goodbye and got "Got it. Is there anything you'd like a hand
    # with?". "n8" is the same night as "nite" and "2nite", and "seeya" the same see-you as
    # "cya", which the goodbye already reads.
    "tmoro": "tomorrow", "n8": "night", "seeya": "see you", "speek": "speak",
    "gr8": "great", "b4": "before", "w8": "wait", "2day": "today", "2morrow": "tomorrow",
    # The moment a remark is about, typed short: "rn its baltic" opened on a word no reader knows
    # and the day outside was answered with "What are you up to there?" - the passing-the-time
    # reader taking the opener for something the person did. "atm" is not here: it is as often the
    # cash machine as "at the moment", and "the atm ate my card" is a bank line.
    "rn": "now", "tn": "tonight",
    # The 8 spellings are the letters the digit says, and the table held every one but the one
    # people type most: "gr8", "n8", "w8" and "m8" were all here, so "i h8 my job" was the only
    # line of that family the reader did not know, and it got "Got it. Is there anything you'd
    # like a hand with?" where "i hate my job" gets "Ugh, that's a lot to carry."
    "h8s": "hates", "l8": "late",
    "msg": "message", "msgs": "messages", "asap": "as soon as possible",
    "idk": "i do not know", "dont know": "do not know",
    # "cba"/"cbf" are read further down, where the word they make is spelled out in full.
    "stomakaike": "stomach ache", "stomach ake": "stomach ache",
    "wanna": "want to",
    "gimme": "give me", "outta": "out of",
    "hafta": "have to", "coulda": "could have", "shoulda": "should have",
    "woulda": "would have", "musta": "must have", "nuthin": "nothing",
    "imo": "in my opinion", "imho": "in my opinion",
    "btw": "by the way", "nvm": "never mind", "np": "no problem", "yw": "you are welcome",
    "rn": "right now", "atm": "at the moment", "abt": "about", "abt.": "about",
    "prob": "probably", "probs": "probably", "def": "definitely",
    "w/": "with", "w/o": "without", "b/c": "because", "&": "and", "n": "and",
    "cya": "see you", "gtg": "got to go", "brb": "be right back",
    "afaik": "as far as i know", "iirc": "if i remember correctly",
    "wtf": "what", "smh": "shaking my head", "fwiw": "for what it is worth",
    "irl": "in real life", "dm": "message", "tmi": "too much information",
    "wat": "what", "wats": "what is", "wut": "what", "wot": "what", "whut": "what",
    "kno": "know", "knos": "knows",
    "hows": "how is", "howd": "how did", "whats": "what is", "wots": "what is",
    "wheres": "where is",
    # The "have" people write as its last two letters, the same shortening as "coulda" and
    # "shoulda" just above. Without them "i shouldve said no" keeps a word that is not English,
    # so the line names no past and no advice; "whatre" is the same shortening of "what are",
    # and it was not a question at all - "whatre you doing" got "I'm well, thanks".
    "whatre": "what are", "shouldve": "should have",
    "whos": "who is", "whys": "why is", "whens": "when is", "howsit": "how is it",
    "ne1": "anyone", "sum1": "someone", "any1": "anyone", "every1": "everyone",
    "evry1": "everyone", "no1": "no one", "some1": "someone", "thruout": "throughout",
    "lol": "lol", "lmao": "lol", "haha": "haha", "hehe": "hehe", "omg": "oh my god",
    "hbu": "how about you", "wyd": "what are you doing", "idc": "i do not care",
    # The ask for the bot's view typed as its initials: "wdyt" is "what do you think", and
    # without the expansion the line names nothing and no pattern can see the ask in it.
    "wdyt": "what do you think", "wdy think": "what do you think",
    "jk": "just kidding", "rofl": "lol", "yolo": "you only live once",
    "nm": "not much", "nmu": "not much you", "wbu": "what about you", "ikr": "i know right",
    "tbh": "to be honest", "dunno": "i do not know",
    # The shortest ways of typing "I don't know" and "don't": no vowel, no apostrophe, no
    # space. Each is a run of letters that is not a word, so it can be read straight, and
    # without it the line names nothing and gets the shrug - "dno" and "i dno" were both
    # answered "Got it. Is there anything you'd like a hand with?" while "dunno" and "idk"
    # were answered as the "I don't know" they are.
    "dno": "i do not know", "dnno": "i do not know", "iunno": "i do not know",
    "donno": "i do not know", "dnt": "do not",
    "gonna": "going to", "gotta": "got to", "lemme": "let me",
    "kinda": "kind of", "sorta": "sort of", "cmon": "come on", "aint": "is not",
    # The spellings people actually type for the words a line turns on. None of these is a
    # real word, so a spelling here cannot bend one. `wana` matters beyond tidiness: without
    # it `i wana make pasta tnight` has no `want` in the normalised line, so the line reads as
    # a report and the bot answers with a mirror instead of a recipe.
    "wana": "want to", "wanne": "want to", "wannna": "want to", "wanta": "want to",
    "hasta": "have to", "shood": "should", "shuld": "should", "coud": "could",
    "spose": "suppose", "becoz": "because", "plis": "please",
    "tnight": "tonight", "tonyt": "tonight", "tonit": "tonight", "2nit": "tonight",
    "tday": "today", "todai": "today", "tmoz": "tomorrow", "2moz": "tomorrow",
    "wid": "with", "weerd": "weird", "styff": "stuff", "stuf": "stuff",
    "knw": "know", "knwo": "know", "defo": "definitely", "rlly": "really",
    "lik": "like", "lyk": "like", "gd": "good", "qwik": "quick", "quik": "quick",
    "chek": "check", "chekcing": "checking", "shoppin": "shopping", "recive": "receive",
    # The numeral-for-a-syllable spellings are all here but the commonest: "gr8", "w8", "l8r",
    # "m8" and "b4" were read and "h8" was not, so "i h8 my job" named nothing and got a nod
    # back while "i hate my job" was answered. `wna` is the same shortening as `wana` and
    # `wanta`, and `nething`/`nethin` are the "ne" of `ne1` with "thing" on the end.
    "h8": "hate", "h8d": "hated", "h8ing": "hating",
    "wna": "want to", "nething": "anything", "nethin": "anything",
}

# The day words are the ones people write shortest, because they settle plans with them: the
# vowel run in the middle of "tomorrow" is the part that goes, so the same person writes
# "tmrow", "tmrw", "tmw", "tomo" and "2moro" across one conversation, and "yday" for
# yesterday. A line that keeps one of these as typed is a line about no particular day, so it
# reads as news and gets an echo back.
# "Thanks" is the word people shorten the most, and the shortenings are not slips of it: "tks"
# and "tkx" are two letters of it with the middle dropped, and "fanks" is the same word with the
# th said as an f. None of them is a slip the opener repair can reach (that fixes one letter),
# so they are spelled out here and the line is read as the thanks it is.
CHAT.update({
    "tkx": "thanks", "tks": "thanks", "thxs": "thanks", "thnks": "thanks", "thks": "thanks",
    "fanks": "thanks", "thanxs": "thanks",
})

CHAT.update({
    "tmrow": "tomorrow", "tmorro": "tomorrow", "tomo": "tomorrow", "tomoz": "tomorrow",
    "tmw": "tomorrow", "2mora": "tomorrow", "2morra": "tomorrow",
    "yday": "yesterday", "ystday": "yesterday", "yestday": "yesterday", "2day": "today",
})

# Words people spell short rather than wrong: a birthday is a "bday", Christmas is "xmas",
# and a partner is "the missus". Kept apart from the misspellings because nothing was mistyped.
CHAT.update({
    "bday": "birthday", "b'day": "birthday", "b-day": "birthday", "bdays": "birthdays",
    "xmas": "christmas", "x-mas": "christmas", "crimbo": "christmas",
    "summat": "something", "sommat": "something", "sumfink": "something",
    "missus": "wife", "hubby": "husband", "bubba": "baby",
    # The oldest texting line there is: "wuu2" is "what you up to", and "what you up to" is the
    # manners question the pool already answers ("Can't complain. Better question: how are you
    # doing?"). The word is a letter run and a digit, so it is one token no dictionary has and the
    # reading could not reach the phrase: "wuu2" got "Got it. Is there anything you'd like a hand
    # with?" and "wuu2 mate" got the listening line.
    "wuu2": "what you up to", "wu2": "what you up to", "wuu": "what you up to",
})

# Shortenings people type that the tables above never had, found by reading real typed lines
# rather than by guessing: "my fone is broken", "i av no idea", "my bf", "got a appt",
# "need meds", "hes sed", "im not bova", "giv us a min", "dats fine",
# "i cnt do it", "gona b late". None of these spellings is an English word, so they can be
# mapped straight to the word behind them without touching a line that says the real thing.
# The chat spelling of a contraction, and the spelling the rest of the code matches: no
# apostrophe, because that is how the same person types it in full ("cudnt" -> "couldnt").
# The reading itself does not change - `norm` still gives "could not" - this only puts the word
# right in the plain line, which is the line modules read for the spelling the writer meant.
# "i cudnt face work today" was answering as an echo because nothing matched "cudnt".
TYPED_CONTRACTIONS = {
    "cnt": "cant", "cudnt": "couldnt", "coudnt": "couldnt", "shudnt": "shouldnt",
    "wudnt": "wouldnt", "dnt": "dont", "wnt": "wont", "didnt": "didnt", "wasnt": "wasnt",
    "isnt": "isnt", "arent": "arent", "werent": "werent", "hasnt": "hasnt",
    "havnt": "havent", "avnt": "havent", "aint": "aint", "doesnt": "doesnt",
}

# A contraction typed without its apostrophe, and the chat spelling of it, in one place: any
# module that has to read a contraction reads it the same way, and "i cnt breathe" is read as
# "i can't breathe" exactly as "i cant breathe" is. The long form keeps the apostrophe because
# that is the spelling a pattern matches without knowing which way it was typed.
CONTRACTIONS = {
    "dont": "don't", "cant": "can't", "wont": "won't", "isnt": "isn't",
    "doesnt": "doesn't", "im": "i'm", "ive": "i've", "i'll": "i'll",
    # A missing apostrophe is the same typo, and the possessive of a child word is what the
    # floppy and sleepy arms read: "my babys lips have gone blue".
    "babys": "baby's", "childs": "child's", "toddlers": "toddler's",
    # The chat spellings of the same words: "i cnt breathe", "i cudnt sleep", "i dnt know".
    "cnt": "can't", "cudnt": "couldn't", "coudnt": "couldn't", "shudnt": "shouldn't",
    "wudnt": "wouldn't", "dnt": "don't", "wnt": "won't", "didnt": "didn't",
    "hasnt": "hasn't", "havnt": "haven't", "avnt": "haven't", "aint": "ain't",
}

CHAT.update({
    "fone": "phone", "fones": "phones", "fonecall": "phone call", "phne": "phone",
    "av": "have", "bv": "have", "hve": "have",
    "avnt": "have not", "propa": "proper",
    "gf": "girlfriend", "gfs": "girlfriends", "bf": "boyfriend", "bfs": "boyfriends",
    "sed": "said", "syas": "says",
    "bova": "bothered", "bovad": "bothered", "bovered": "bothered", "botherd": "bothered",
    # "i cba to cook" and "cbf" are how people say "i can't be bothered", and the word has to
    # be there: it is the cue for the tiredness and low-mood replies, so a line that keeps
    # "cba" reads as an echo of what was typed and gets one back.
    "cba": "can not be bothered", "cbf": "can not be bothered",
    "giv": "give", "givin": "giving", "gimme a": "give me a",
    "gona": "going to", "gonig": "going", "goina": "going to",
    "nt": "not", "cnt": "can not",
    # The "not" of a modal with its o dropped and the apostrophe gone: "i cudnt sleep",
    # "we shudnt bother", "they wudnt say". "havnt" and "avnt" are the same for "have".
    "havnt": "have not", "avent": "have not",
    "shudnt": "should not", "cudnt": "could not", "wudnt": "would not",
    "dats": "that is", "das": "that is", "dere": "there",
    "tryna": "trying to", "trynna": "trying to",
    # The forms the tables above still missed, every one of them a spelling that is not an
    # English word, so none of them can bend a line that says the real thing. `tnx` keeps a
    # thanks a thanks, which is the difference between "any time" and a stock line.
    "tnx": "thanks", "tnks": "thanks", "thnkx": "thanks", "thnxs": "thanks",
    "sumin": "something", "sumink": "something", "anyfin": "anything",
    "anyfink": "anything", "eveything": "everything", "evrythin": "everything",
    "nuffink": "nothing", "nuffin": "nothing",
    "meds": "medicines",
    "abt": "about", "bout time": "about time",
    # "fell owt wiv me sister", "owt else": the Northern "owt" is "out" in what people type.
    "owt": "out", "owtside": "outside", "owta": "out of",
    "owt else": "anything else", "owt wrong": "anything wrong",
})

# The same shape again, one step further from the words they stand for: a gift is a "prezzy" or
# a "pressie", and "avnt"/"ment" are how a whole sentence gets typed in a hurry. None of them is
# an English word, so a line that says the real thing is never touched.
CHAT.update({
    "avnt": "have not", "havnt": "have not",
    "ment": "meant",
    "normaly": "normally", "usualy": "usually",
    "cupple": "couple", "cupples": "couples",
    # "prezzie" is the spelling most people use for a gift and it was not in the table while
    # "prezzy", "pressie" and both plurals were, so a question about one never reached the
    # present answers: "what prezzie should i get my mum" got the search hedge where
    # "what present should i get my mum" gets the gift line.
    "prezzie": "present",
    "prezzy": "present", "prezzies": "presents", "pressie": "present", "pressies": "presents",
    "presant": "present",
})

# The short form of a noun that is longer than the word it is short for, cut off before the ending
# people leave off: the decorations are the "decs", a licence is a "lic" and a hospital is a
# "hosp". Each one is a run of letters no English word has on its own, so a line that says the
# whole word is never touched - and without them the reading searched for a thing called "decs"
# and came back with a search hedge. Found by reading typed lines rather than by guessing
# (#understanding 80669): "when do the decs come down" was a hedge where the decorations answer
# is written, and "my mum is in hosp" was read back to the person as "Noted: your mum is in hosp."
#
# Measured and deliberately NOT in the table, so nobody adds them back thinking they were missed:
# `pres` -> prescription and `serv` -> service. `pres` reaches no answer ("i need a pres for my
# mum" is an echo either way) and turns "whats a good pres for a 5 yr old" from a hedge into the
# medicine-expiry card, which is the wrong question about a child's medicine - a hedge is the
# better of the two. `serv` changed no reply in 16 typed lines.
CHAT.update({
    "decs": "decorations", "decs.": "decorations",
    "lic": "licence",
    "hosp": "hospital",
})

CHAT.update({
    "brekkie": "breakfast", "brekky": "breakfast",
    "biccy": "biscuit", "biccies": "biscuits", "bikkie": "biscuit", "bikkies": "biscuits",
    "choccy": "chocolate", "choccies": "chocolates",
    "sarnie": "sandwich", "sarnies": "sandwiches", "butty": "sandwich", "butties": "sandwiches",
    # "veggies" is not here: "3 are veggies" is three vegetarians ("theres 14 of us, 3 are
    # veggies" read as "3 are vegetables"), so the plural is only the plate when a cooking word
    # is in front of it - `VEGGIES_AFTER` in normalize.py.
    # An idiom rather than a short form, and the same mechanism serves it: "the boiler is on the
    # blink" is the boiler not working, and every answer about one is the right one. "broken"
    # says the same thing but reads as a broken bone as well, so the health topic came to a
    # washing machine; "not working" keeps the answers and no injury.
    "on the blink": "not working",
})

# Common misspellings that the edit-distance corrector cannot settle on its own: two real
# words are one edit away, or the fix is two edits from what was typed.
MISSPELLINGS = {
    # "tight" typed by ear or with the gh left out, which is how half of it is said. The
    # one-edit reader refuses both ("tite" is not one edit from anything it trusts), so the line
    # read as nothing at all: "my chest feels tite" answered "I'm listening" while "my chest
    # feels tight" gets the 999 card, and "my jeans are tite" the fit advice. Neither word is a
    # word, so there is nothing to fence them against.
    "tite": "tight", "thight": "tight",
    # The same sound again, in the two places it decides whether the line is an ambulance:
    # `my chest pane is bad` answered "Ugh, that's rotten" and `i think im having a hart attack`
    # answered "Got it." while `my chest pain` and `a heart attack` both get the 999 card,
    # and `my speech is slurd` got "Got it." while `slurred` gets the stroke ambulance.
    # "pane" and "hart" are words of their own (a window pane, a hart is a stag), so the two
    # that are words are held to the phrase that carries the body, never the word alone.
    "slurd": "slurred", "slurrd": "slurred", "slured": "slurred",
    # "pane in my chest" is not in this map: `_a_slip_that_is_a_word` already reads it, and it
    # refuses the line when any word for glass or a pan is in it. Written here it is a blind
    # string repair, so "the pane in my chest freezer cracked" became a chest pain and got
    # the 999 card on a broken piece of glass.
    "chest pane": "chest pain",
    "hart attack": "heart attack", "hart rate": "heart rate", "hart beat": "heartbeat",
    "my hart": "my heart", "his hart": "his heart", "her hart": "her heart",
    # "crack" typed with the letters run together. "crak" is not a word, so it needs no fence,
    # and the same slip turns up in every line about a thing that has split: `my phone screen has
    # a crak` answered "I'm listening" while `my phone screen has a crack` gets the screen card,
    # and a crack in a cup, a ceiling or a bone reads the same way once the word is put back.
    "crak": "crack", "craks": "cracks", "craked": "cracked", "craking": "cracking",
    # "numb" with its last letter dropped, which is one of the stroke signs: `my face feels num`
    # answered "I'm listening" while `my face feels numb` gets the face-numbness answer. "num" is
    # also chat-speak for a phone number ("whats ur num"), so the repair is held to the verbs
    # that take "numb" and never made on the word alone.
    "feels num": "feels numb", "feel num": "feel numb", "is num": "is numb",
    "are num": "are numb", "gone num": "gone numb", "went num": "went numb",
    "goes num": "goes numb", "going num": "going numb",
    # "gasping for air" with a letter dropped or doubled: the line was not read as anything and
    # came back as an echo of itself - "Noted: your dad is gaspng for air." - while the word
    # spelled right is the ambulance. "gaspin" is the same word with its g left off, which the
    # table already does for "havin", "chokin" and "bleedin".
    "gaspng": "gasping", "gaspping": "gasping", "gaspin": "gasping",
    "gaspign": "gasping", "gaspeing": "gasping",

    # "i got layed off 2day": two slips from "laid", and the wrong word ("layed" reads as
    # "lay") is what the edit-distance corrector settles on, so the fix is written here.
    "layed": "laid", "layed off": "laid off",
    # "failure" with its i and l typed the wrong way round: the one-edit readers leave a
    # vowel-consonant swap alone, because that is how a real word becomes another real word.
    "faliure": "failure", "faluire": "failure", "failiure": "failure",
    "dissapointment": "disappointment",
    "dissapointing": "disappointing", "dissapoint": "disappoint",
    # The judgement words again, with a vowel or a letter the wrong way round. "fix_typo" leaves
    # a letter swapped for another one alone on purpose, so the table is the only way these land
    # - and a judgement noun that does not land is read as a thing being named: "im wortles" was
    # answered "Nice to meet you, Wortles. What can I help with?" and "im a faliur" was read as
    # a role to chat about ("Faliur - good to know. What do you like most about it?").
    "faliur": "failure", "falure": "failure", "fialure": "failure",
    "failur": "failure", "wortles": "worthless", "wothles": "worthless",
    "useles": "useless", "uselss": "useless", "hopeles": "hopeless",
    "nuiscance": "nuisance", "letdow": "letdown",
    "usless": "useless",
    # Two letters typed round the wrong way, in the words people write most: a swapped pair is
    # two edits, so the one-edit corrector refuses it and the word stayed as typed. "whcih one
    # should i get" then read "one" as a count and the ask never reached the answer, and "whaat
    # can i do about damp" missed the words the damp answer matches on. "tounge" is the spelling
    # of tongue people write by ear, and the sore-tongue answer never came.
    "whcih": "which", "whihc": "which", "whaat": "what", "tounge": "tongue", "toung": "tongue",
    "recipie": "recipe", "reciepe": "recipe", "resipee": "recipe",
    "qinuoa": "quinoa", "qunioa": "quinoa", "quinoia": "quinoa", "quinnoa": "quinoa",
    "sandwhich": "sandwich", "sandwitch": "sandwich",
    "potatos": "potatoes", "tomatos": "tomatoes", "avacado": "avocado", "eg": "egg",
    "definately": "definitely", "definatly": "definitely",
    "sence": "sense",
    "tempreture": "temperature",
    "wierd": "weird",
    "beleive": "believe", "aswell": "as well",
    "apreciate": "appreciate", "appriciate": "appreciate", "apprechiate": "appreciate",
    "alot": "a lot", "thier": "their", "wich": "which",
    "wheather": "weather", "tomorow": "tomorrow", "exercize": "exercise",
    "excercise": "exercise",
    "acheive": "achieve", "adress": "address",
    "goverment": "government", "enviroment": "environment",
    "necesary": "necessary",
    "restaraunt": "restaurant",
    "vegtable": "vegetable", "chocalate": "chocolate", "choclate": "chocolate",
    "spagetti": "spaghetti", "lasagne": "lasagne", "yoghurt": "yogurt",
    "teh": "the", "hte": "the", "adn": "and", "nad": "and", "taht": "that",
    "waht": "what", "whta": "what", "yuo": "you", "fo": "of", "ot": "to",
    "becuase": "because", "becasue": "because", "beacuse": "because",
    "wether": "weather", "wether or not": "whether or not",
    "weather or not": "whether or not",
    "seperate": "separate", "definetly": "definitely",
    "recieve": "receive", "recieved": "received",
    "belive": "believe", "occured": "occurred", "begining": "beginning",
    "calender": "calendar", "recomend": "recommend", "reccomend": "recommend",
    "recomendations": "recommendations", "diffrent": "different", "differnt": "different",
    "excersize": "exercise",
    "tommorow": "tomorrow", "untill": "until", "freind": "friend",
    "freinds": "friends", "garantee": "guarantee", "gratefull": "grateful",
    "immediatly": "immediately", "independant": "independent", "intresting": "interesting",
    "knowlege": "knowledge", "libary": "library", "maintainance": "maintenance",
    "neccessary": "necessary", "occassion": "occasion", "posible": "possible",
    "prefered": "preferred", "recomended": "recommended", "resturant": "restaurant",
    "rythm": "rhythm", "suprise": "surprise",
    "truely": "truly", "useing": "using", "usefull": "useful", "vegeterian": "vegetarian",
    "verry": "very", "writting": "writing",
    # Slips that cost a real answer: each of these made the bot hedge or hand back a stock line on a
    # line it answers well when the word is spelled, and none of them is an English word, so no line
    # about anything else can move.
    "remoov": "remove", "brokn": "broken", "dropin": "dropping", "lern": "learn",
    "gettin": "getting", "goin": "going", "doin": "doing", "nothin": "nothing",
    "somethin": "something", "anythin": "anything", "everythin": "everything",
    "lil": "little", "smth": "something", "sth": "something", "ppl": "people",
    "bcos": "because", "gud": "good",
    # Said the way it is typed: a dropped h, a dropped final sound, and the words people spell
    # by their sound. Each one is a word the engine read as no word at all, so the line got a
    # stock reply where the spelled-out word gets the answer for what was meant.
    # "arsed" only ever appears in one idiom ("i cant be arsed"), where it means bothered - the
    # same word the `bova`/`bovered` group above already maps, and the line read as nothing at
    # all without it. `tnx`/`thnx`/`thankz` are already in CHAT, so they are not repeated here.
    "bovvered": "bothered", "bovverd": "bothered", "arsed": "bothered",
    "fink": "think", "mebbe": "maybe", "luvly": "lovely",
    "sista": "sister", "sistah": "sister", "bruv": "brother",
    "bruvva": "brother", "bruvver": "brother", "muvva": "mother", "muva": "mother",
    "muvver": "mother", "fatha": "father",
    "feelin": "feeling", "talkin": "talking", "waitin": "waiting", "makin": "making",
    "tryin": "trying", "lookin": "looking", "comin": "coming", "knowin": "knowing",
    "thinkin": "thinking", "wonderin": "wondering", "l8r": "later", "g2g": "got to go", "m8": "mate",
    # the -ing forms the lexicon itself does not list, so the left-off g is repaired here
    "complainin": "complaining", "quittin": "quitting", "shoppin": "shopping",
    "workin": "working", "runnin": "running", "eatin": "eating", "sleepin": "sleeping",
    "drivin": "driving", "sittin": "sitting", "studyin": "studying", "listenin": "listening",
    "holdin": "holding", "livin": "living", "lovin": "loving", "writin": "writing",
    "readin": "reading", "helpin": "helping", "openin": "opening", "closin": "closing",
    "cud": "could", "shoud": "should", "shud": "should", "wud": "would", "wold": "would",
    "hungrey": "hungry", "hungray": "hungry", "thristy": "thirsty",
    "rekon": "reckon", "rekons": "reckons", "rekoning": "reckoning",
    # The feelings typed with a letter missing or swapped: each one was read as a name and
    # answered "Nice to meet you, Awsome", while a curated spelling reads it as the state it
    # is. None of them is an English word, so no line about anything else can move.
    "awsome": "awesome", "awfl": "awful", "awfull": "awful", "hopefull": "hopeful",
    "ankshus": "anxious", "anxios": "anxious", "anxty": "anxious",
    "emosh": "emotional",
    # The same class with the vowels taken out, which the one-edit fixer cannot see because the
    # word is two or three letters short of the feeling: "im anxty", "im deprsd" and "im woryd"
    # were all answered "Nice to meet you, Anxty." None of them is an English word.
    "deprsd": "depressed", "depresd": "depressed", "depresed": "depressed",
    "stresd": "stressed", "woryd": "worried", "angryy": "angry", "irratable": "irritable",
    "chiken": "chicken", "chikcen": "chicken",
    # "th" typed as "t", which is how a lot of the country speaks and types: "i tink so" got
    # "I'm listening - say more if it helps." It is a list and not a rule on the first letter,
    # because short real words sit one letter from a "th" word - "ten"/"tan"/"tick"/"tough" are
    # all one swap away, and bending those would cost more lines than the swap wins ("tough"
    # alone is on fourteen deck lines). The "f" side needs no list: `_said_with_an_f` already
    # reads "fanks", "fink", "fing" and "frew" from the rule.
    "tink": "think", "tinks": "thinks", "tinking": "thinking", "tinkin": "thinking",
    "tinked": "thought", "tought": "thought",
    "kichen": "kitchen", "kitched": "kitchen", "wach": "watch", "wathc": "watch",
    "bord": "bored", "boared": "bored", "blak": "black", "stomack": "stomach",
    "ankel": "ankle", "plummer": "plumber", "shoer": "shower", "curtins": "curtains",
    "cusion": "cushion", "cupbord": "cupboard", "tabl": "table", "hous": "house",
    "brocolli": "broccoli", "omlette": "omelette", "porrige": "porridge",
    "recepie": "recipe", "recpie": "recipe",
    "tirred": "tired", "tierd": "tired", "headach": "headache", "headace": "headache",
    "docor": "doctor", "reciept": "receipt", "radiater": "radiator", "boilar": "boiler",
    "boilier": "boiler",
    # the letters people leave out of the words they say most when something is wrong
    "docer": "doctor", "doctur": "doctor", "dockter": "doctor",
    "ambulnce": "ambulance", "ambulence": "ambulance", "ambulanc": "ambulance",
    "hostpital": "hospital", "hospitl": "hospital",
    "paracetomal": "paracetamol", "paracetemol": "paracetamol", "paracetmol": "paracetamol",
    "ibuprofin": "ibuprofen", "ibruprofen": "ibuprofen", "ibroprofen": "ibuprofen",
    "matress": "mattress", "allergey": "allergy", "allergies": "allergies",
    "appoinment": "appointment", "appointmnt": "appointment", "sanwhich": "sandwich",
    "dishwosher": "dishwasher", "battry": "battery", "washign": "washing",
    "accomodation": "accommodation", "agian": "again", "agianst": "against",
    "arguement": "argument", "bacause": "because", "beleif": "belief",
    "buisness": "business", "catagory": "category", "collegue": "colleague",
    "comittee": "committee", "completly": "completely", "concensus": "consensus",
    "concious": "conscious", "curiousity": "curiosity", "dilemna": "dilemma",
    "dissapointed": "disappointed", "embarassed": "embarrassed", "embarassing": "embarrassing",
    "freindly": "friendly", "frist": "first", "grammer": "grammar", "happend": "happened",
    "harrass": "harass", "intrest": "interest", "jist": "just", "jsut": "just",
    "jstu": "just", "knowlage": "knowledge", "lenght": "length", "lisence": "licence",
    "medecine": "medicine", "millenium": "millennium", "noticable": "noticeable",
    "occuring": "occurring", "paralel": "parallel", "perfomance": "performance",
    "personel": "personnel", "persue": "pursue", "posession": "possession",
    "priviledge": "privilege", "probaly": "probably",
    "pronounciation": "pronunciation", "publically": "publicly", "questionaire": "questionnaire",
    "recommened": "recommended", "refered": "referred", "relevent": "relevant",
    "religous": "religious", "rember": "remember", "remeber": "remember",
    "responsable": "responsible", "scedule": "schedule", "shedule": "schedule",
    "seperated": "separated", "shoudl": "should", "coudl": "could", "woudl": "would",
    "succesful": "successful", "sucessful": "successful", "suprize": "surprise",
    "supercede": "supersede", "temperture": "temperature", "tempriture": "temperature",
    "tendancy": "tendency", "threshhold": "threshold", "tommorrow": "tomorrow",
    "transfered": "transferred", "unecessary": "unnecessary", "usualy": "usually",
    "vaccum": "vacuum", "vegtables": "vegetables", "vehical": "vehicle", "wehn": "when",
    "wiht": "with", "wonderfull": "wonderful", "yuor": "your", "hwat": "what",
    "brill": "brilliant", "seige": "siege", "sieze": "seize", "mediteranean": "mediterranean",
    # A letter left out of a word typed at speed. None of these is a word as it stands, and each
    # one stops a line reaching what it is about: "my back is kiling me" got a nod where
    # "killing" asks how it comes and goes, "my nabours music is loud till 2am" got a shrug where
    # "neighbours" gets the knock-once answer, and "my dauter is 3 and wont sleep" missed the
    # sleep answer it gets with the whole word. The repair is only the word: the line keeps its
    # order, so the writer's own words still start it.
    "nabour": "neighbour", "nabours": "neighbours",
    "nabor": "neighbour", "nabors": "neighbours",
    "neigbour": "neighbour", "neigbours": "neighbours",
    "daugther": "daughter", "daugthers": "daughters",
    "dauter": "daughter", "dauters": "daughters",
    "tird": "tired", "geting": "getting",
    # A body that hurts, and the words for it: the reply code tells "my back is killing me" (a
    # body, so it asks about it) from a fact to say back by reading the word, so the slip has to
    # reach it put right. A slip is never a word of its own - "kiling", "headeche", "leeking" are
    # not English - so nothing that is really a word is bent into one of these.
    "kiling": "killing", "kilin": "killing", "headeche": "headache", "headche": "headache",
    "headake": "headache", "stomache": "stomach", "kidnees": "kidneys", "kidnies": "kidneys",
    "ancious": "anxious", "anxous": "anxious", "misrable": "miserable",
    # A feeling typed with an extra letter left out and a letter changed: two edits, which the
    # one-edit repair in front of the feeling list will not guess at, but people write them this
    # way over and over ("im strest", "im deprest"). None is a word as it stands.
    "strest": "stressed", "deprest": "depressed", "annoied": "annoyed",
    "embarased": "embarrassed", "overwelmd": "overwhelmed", "greatful": "grateful",
    "sufering": "suffering", "caugh": "cough", "coughin": "coughing", "docter": "doctor",
    "hospitle": "hospital", "medcine": "medicine", "symtoms": "symptoms", "dizy": "dizzy",
    "vometing": "vomiting", "swolen": "swollen", "throte": "throat", "brething": "breathing",
    "bleading": "bleeding",
    # A thing in the house that has gone wrong.
    "leeking": "leaking", "driping": "dripping", "radiaters": "radiators",
    "freezar": "freezer", "fridg": "fridge", "ovan": "oven", "microwve": "microwave",
    "plumer": "plumber",
    # Everyday spelling, heard rather than read: the same letters, in the order people say them.
    "yesturday": "yesterday", "saterday": "saturday", "wensday": "wednesday",
    "defintely": "definitely", "proberly": "probably", "allways": "always",
    "allready": "already", "intrested": "interested", "restarant": "restaurant",
    "woried": "worried", "worring": "worrying", "cheeper": "cheaper",
    "exersize": "exercise", "vitimens": "vitamins", "proteen": "protein",
    "protien": "protein",
    # Two edits from "protein" - a letter short, or a letter short and two swapped - and not a
    # word as they stand. `fix_typo` leaves both alone on purpose: it repairs a word that is one
    # edit away, and "how much proten in chicken" is one letter from a real word nobody asked for.
    "proten": "protein", "protine": "protein",
    "recomends": "recommends",
    # The everyday words people misspell the same way, over and over, when they are worried or
    # typing one-handed. None of these is a word as it stands either, so no real word is at risk:
    # "my sun has a temprature of 39" reached nothing at all, while "temperature" gets the call
    # the doctor answer, and "ive got a migrane" was said straight back as "your migrane" where
    # "migraine" gets the health answer. The list stays short and only holds slips seen in the
    # wild, because a table of guesses is worse than none.
    "temprature": "temperature",
    "tempreature": "temperature", "tempratue": "temperature",
    "migrane": "migraine", "migranes": "migraines", "migrain": "migraine",
    "stomaches": "stomachs",
    "coughting": "coughing",
    "dizey": "dizzy",
    "alergic": "allergic", "allerjic": "allergic",
    "pennicillin": "penicillin", "penicilin": "penicillin", "penicillian": "penicillin",
    "diarhea": "diarrhoea", "diarhoea": "diarrhoea", "dioreah": "diarrhoea",
    # The three people type most often, and each one cost the whole answer: "i have dihorrea" was
    # "Noted: you have dihorrea" where the right spelling gets the salt-and-sugar glass.
    "dihorrea": "diarrhoea", "diahorrea": "diarrhoea", "diarrea": "diarrhoea",
    "colestrol": "cholesterol", "cholesteral": "cholesterol", "colesterol": "cholesterol",
    "vomitting": "vomiting", "vommiting": "vomiting",
    "infektion": "infection", "infekshun": "infection", "infecton": "infection",
    "bloked": "blocked", "realy": "really",
    "feaver": "fever", "feaverish": "feverish",
    # `cought` is the usual slip of *caught* - "it was cought on camera" - and a slip of two
    # words has to be given the frame that says which one was meant. So instead of the bare word
    # the entry is only the shapes with a cough in them, and the reader keeps "caught" out of
    # the health vocabulary. `coughting` is nobody's word for catching anything.
    "a cought": "a cough", "the cought": "the cough", "my cought": "my cough",
    "bad cought": "bad cough",
    # The same hand, a few words later: a misspelling nobody would call a typo, and a night that
    # is spelled the way it is said. "iv" alone is left alone on purpose - a line about an IV
    # drip, or a line typed "iv got" - so it is only repaired where the word after it says which
    # the person meant.
    # "gorra" is "got a" said aloud, the same way "iv" is "i have": "iv gorra headache" came
    # back "I'm listening - say more if it helps" while "iv got a headache" and "i have got a
    # headache" both reached the headache answer, and "iv gorra toothache" lost the toothache
    # one. A bare "gorra" cannot be written down: the word after it is what says which helper
    # it was, so the entry is the pair ("hes gorra dog" is "he has got a dog", not "is got").
    "iv gorra": "i have got a", "ive gorra": "i have got a",
    "hes gorra": "he has got a", "shes gorra": "she has got a",
    "we gorra": "we have got a", "they gorra": "they have got a",
    "iv got": "i have got", "iv had": "i have had", "iv been": "i have been",
    "iv just": "i have just", "iv never": "i have never", "iv not": "i have not",
    "iv only": "i have only", "iv always": "i have always", "iv already": "i have already",
    "iv still": "i have still", "iv also": "i have also", "iv lost": "i have lost",
    "iv taken": "i have taken", "iv stopped": "i have stopped", "iv tried": "i have tried",
    "probly": "probably", "probally": "probably",
    # The words a person judges themselves with, typed at speed. chat.py has an answer written
    # for each of them, and every one of these slips is a letter out of place or a doubled letter
    # the one-edit readers leave alone - so the line missed the answer and the echo said the slip
    # back ("Dissapointment - good to know."). "im a burden" reaches "you're being harder on
    # yourself than you'd be on a friend"; "im a burdon" reached the job pool that tells a person
    # who calls themselves a burden "A burdon - nice one."
    "disapointment": "disappointment",
    "disappoinment": "disappointment",
    "burdon": "burden", "burdons": "burdens",
    "worthles": "worthless", "worthlesly": "worthlessly",
}

# The everyday words people misspell most when they write about a body or a house, kept apart
# from the tables above so this one does not grow into a general one. Each is a letter run that
# is nobody's word and that the one-edit fixer cannot settle: a doubled letter dropped or a
# sound written as it is said ("paracetemol", "kettel"), the vowels in the wrong order
# ("bruse", "medicaton"), or a letter run two edits from the word it stands for ("heatng").
MISSPELLINGS.update({
    # a body, a symptom
    "stomac": "stomach", "swallen": "swollen", "bruse": "bruise", "brusie": "bruise",
    "simptoms": "symptoms", "consentrate": "concentrate",
    "daugher": "daughter", "medicaton": "medication", "presure": "pressure",
    # the medicine cabinet and the GP
    "paracetemol": "paracetamol", "paracetmol": "paracetamol", "ibuprofin": "ibuprofen",
    "ibuprophen": "ibuprofen", "presciption": "prescription", "perscripton": "prescription",
    "apointment": "appointment", "apointmnet": "appointment",
    # the house and the paperwork
    "heatng": "heating", "triping": "tripping", "kettel": "kettle", "passward": "password",
    "pasword": "password", "tennants": "tenants", "substatute": "substitute",
    "substitue": "substitute", "properley": "properly", "properlly": "properly",
    # the day, the week
    "yesterdy": "yesterday", "goign": "going", "depresed": "depressed",
    # A state typed with a syllable dropped: "im nakerd", "im starvin", "im fumin", "im sare".
    # Each one was read as a person and answered "Nice to meet you, Nakerd", while the spelling
    # the module knows gets the tired, hungry, angry or sore answer. None of them is an English
    # word, so no line about anything else can move. "sic" is deliberately not here: it is the
    # Latin adverb a quotation carries, and "the quote says sic" became a comfort line.
    "nakerd": "knackered", "nakered": "knackered", "knackerd": "knackered",
    "starvin": "starving", "starveing": "starving",
    "fumin": "fuming", "fummin": "fuming", "sare": "sore",
    # A letter heard wrong, on the words a body, a kitchen and a house are described with. The
    # one-edit fixer refuses a substitution on purpose (with this lexicon "three" becomes
    # "there"), so the everyday word it gets wrong is written here instead: "heachache" for a
    # headache, "beff" for beef, "mashine" for the washing machine, "teatching" for a baby's
    # teeth. Each is a letter run nobody's word spells, and every one of them leaves the line
    # unanswered ("Noted: you have a bad heachache", "Got it. Is there anything you'd like a
    # hand with?") where the word itself gets the answer. "sic" stays out for the reason above;
    # "bitting" is the horseman's word, not a slip; and "stane" is left out because it is the
    # Scots word for a stone, so "a nice stane wall" became a stain-removal answer.
    "heachache": "headache", "heachaches": "headaches",
    "sik": "sick", "tyred": "tired",
    "mashine": "machine", "mashines": "machines",
    "beff": "beef", "chese": "cheese", "teatching": "teething",
})


# The words that turn a line into an emergency, as people misspell them when they are frightened
# and typing fast. A letter left out is the one typo this engine will not guess at, and that is
# the right rule everywhere else: a word one letter short of another is usually the other word
# ("till" for "still", "past" for "pasta", "fire" for "fibre"), and a confident wrong correction
# is worse than none. Here it is not: "swalowed", "collapsd" and "sezure" are nobody's words, and
# costing one of them the 999 answer is the worst failure the bot can have. So the emergency
# vocabulary carries a short curated table, the same way the kitchen words do, and every entry
# maps into the emergency vocabulary and nothing else (a test holds that).
# The short slips the reader cannot take on its own. A swap of two letters that are both vowels
# ("baout", "htere", "monye") is how one real word becomes another - "stain" is "satin", "order"
# is "roder", "matters" is "mattres" - so the general reader leaves every vowel pair alone and the
# curated map holds the ones people type. Each key is a slip, each value the word meant, and a key
# can only ever be read as the word written beside it.
#
# Found by swapping a letter pair in one word of every deck line and keeping the pairs where the
# word meant is a common word (top 1,500 by COMMON_RANK), the word typed is one no reader holds,
# and exactly one swap fits. Written out as pairs because the same slip is typed several ways
# ("abotu", "abuot", "aobut") and each way is its own key.
MISSPELLINGS.update({
    "abotu": "about",
    "abuot": "about",
    "aftre": "after",
    "anrgy": "angry",
    "anxoius": "anxious",
    "aobut": "about",
    "aplpes": "apples",
    "appel": "apple",
    "apsta": "pasta",
    "arzor": "razor",
    "asuce": "sauce",
    "atfer": "after",
    "audlt": "adult",
    "awflu": "awful",
    "baout": "about",
    "bioling": "boiling",
    "biuld": "build",
    "blodo": "blood",
    "bolod": "blood",
    "borad": "board",
    "borde": "bored",
    "braed": "bread",
    "brsuh": "brush",
    "bulid": "build",
    "cehst": "chest",
    "chets": "chest",
    # "cheast" is the chest with an "a" in it, the way people type it after "breast". It is
    # not a transposition, and without this row the corrector reaches for a real word one
    # letter away instead: "my cheast hurts" was read as "my cheats hurts", so the part
    # repair below never saw it and a chest pain opened as nothing at all.
    "cheast": "chest",
    "chlid": "child",
    "cihld": "child",
    "claen": "clean",
    "clena": "clean",
    "coluor": "colour",
    "craem": "cream",
    "dirnk": "drink",
    "dreyr": "dryer",
    "drnik": "drink",
    "drvie": "drive",
    "dryre": "dryer",
    "duaghter": "daughter",
    "ebans": "beans",
    "ejans": "jeans",
    "elmon": "lemon",
    "enver": "never",
    "eyast": "yeast",
    "fater": "after",
    "fbire": "fibre",
    "feevr": "fever",
    "fimls": "films",
    "firts": "first",
    "fisrt": "first",
    "folor": "floor",
    "folur": "flour",
    "funyn": "funny",
    "fxied": "fixed",
    "giong": "going",
    "goign": "going",
    "hadns": "hands",
    "hosue": "house",
    "hpone": "phone",
    "hsort": "short",
    "htere": "there",
    "hwich": "which",
    "hwile": "while",
    "inght": "night",
    "jenas": "jeans",
    "kinfe": "knife",
    "laern": "learn",
    "lbood": "blood",
    "lcean": "clean",
    "lfoor": "floor",
    "lgass": "glass",
    "lgiht": "light",
    "lovde": "loved",
    "lpace": "place",
    "lpane": "plane",
    "lseep": "sleep",
    "maent": "meant",
    "mnoth": "month",
    "moeny": "money",
    "monht": "month",
    "monye": "money",
    "motuh": "mouth",
    "muontain": "mountain",
    "muoth": "mouth",
    "nevre": "never",
    "ngiht": "night",
    "nigth": "night",
    "nihgt": "night",
    "ocugh": "cough",
    "oculd": "could",
    "odugh": "dough",
    "ofetn": "often",
    "oging": "going",
    "omney": "money",
    "owrth": "worth",
    "palnt": "plant",
    "pasat": "pasta",
    "patsa": "pasta",
    "phnoe": "phone",
    "phoen": "phone",
    "pizaz": "pizza",
    "platn": "plant",
    "puonds": "pounds",
    "raelly": "really",
    "raozr": "razor",
    "rbead": "bread",
    "rceam": "cream",
    "rdink": "drink",
    "rdive": "drive",
    "rievr": "river",
    "rihgt": "right",
    "rtain": "train",
    "salda": "salad",
    "sehlf": "shelf",
    "shuold": "should",
    "sicne": "since",
    "sitll": "still",
    "slepe": "sleep",
    "snakc": "snack",
    "stlil": "still",
    "sugra": "sugar",
    "tarin": "train",
    "tdoay": "today",
    "tehre": "there",
    "tierd": "tired",
    "tinlging": "tingling",
    "toady": "today",
    "tooht": "tooth",
    "totoh": "tooth",
    "tsill": "still",
    "udner": "under",
    "ufnny": "funny",
    "ujice": "juice",
    "umsic": "music",
    "unedr": "under",
    "unitl": "until",
    "upppy": "puppy",
    "usgar": "sugar",
    "veagn": "vegan",
    "wacth": "watch",
    "waetr": "water",
    "wehre": "where",
    "whcih": "which",
    "whiel": "while",
    "whihc": "which",
    "wolud": "would",
    "wotrh": "worth",
    "wroth": "worth",
    "wtaer": "water",
})

URGENT_MISSPELLINGS = {
    # A first-aid pattern of its own keys on these: "swollen" is what tells a sprained joint from
    # a knock, and a person who types "swolen" must not lose the ice and the "get it checked".
    "swolen": "swollen", "swollan": "swollen",
    # swallow - a child, a dog or an adult who has taken something they should not have
    "swalow": "swallow", "swallo": "swallow", "swollow": "swallow",
    "swaloed": "swallowed", "swalowed": "swallowed", "swalloed": "swallowed",
    "swollowed": "swallowed", "swalowing": "swallowing", "swalloing": "swallowing",
    "swollowing": "swallowing",
    # collapse - a person going down
    "colapse": "collapse", "collpase": "collapse", "collaps": "collapse",
    "colapsed": "collapsed", "collapsd": "collapsed", "collapsesd": "collapsed",
    "colapsing": "collapsing",
    # choke
    "chok": "choke", "chokng": "choking", "chocking": "choking",
    "chokeing": "choking", "chokking": "choking",
    # unconscious, unresponsive
    "unconcious": "unconscious", "unconsious": "unconscious", "unconcius": "unconscious",
    "unconciuos": "unconscious", "unconscience": "unconscious", "unconcsious": "unconscious",
    "unresponsve": "unresponsive",
    # seizure
    "sezure": "seizure", "sezuire": "seizure", "seziure": "seizure", "sezire": "seizure",
    "siezure": "seizure", "seisures": "seizures", "sezures": "seizures",
    # overdose
    "overdos": "overdose", "overdosse": "overdose", "overdosd": "overdosed",
    "overdowsed": "overdosed", "overdosng": "overdosing",
    # bleeding
    "bleding": "bleeding", "bleading": "bleeding", "bledding": "bleeding",
    "bleednig": "bleeding",
    # drowning
    "drownd": "drowned", "drownded": "drowned", "drowing": "drowning",
    "drownng": "drowning",
    # breathing
    "brething": "breathing", "breatheing": "breathing", "breathng": "breathing",
    "breahting": "breathing",
    # a stroke, vomiting, a burn
    "strok": "stroke", "stroks": "strokes", "vomitting": "vomiting",
    "vometing": "vomiting", "vomitng": "vomiting", "burnng": "burning",
    "bruning": "burning",
    # the last letter left off, which people type faster than anything else
    "havin": "having", "chokin": "choking", "bleedin": "bleeding", "bledin": "bleeding",
    "swallowin": "swallowing", "breathin": "breathing", "drownin": "drowning",
    "overdosin": "overdosing", "collapsin": "collapsing", "vomitin": "vomiting",
    "burnin": "burning", "seizurin": "seizing",
    # The other spellings of the same first-aid words. "burn", "breath", "throat" and
    # "temperature" each key a pattern of their own in safety, and a person who types "burnet" or
    # "throt" was losing the answer: "i burnet my hand" and "my throt is closing" got a shrug
    # (fancy-broom). "swallen" is deliberately not respelled: the answers card for a swollen joint
    # is the better one, and putting the word back would hand the line to the ice-and-raise-it card.
    "breaht": "breath", "breth": "breath", "breathh": "breath",
    "burnet": "burnt", "burent": "burnt", "burntt": "burnt", "burnd": "burnt",
    "throt": "throat", "troath": "throat", "thraot": "throat",
    "tempreture": "temperature", "temperture": "temperature", "tempriture": "temperature",
    "temparature": "temperature", "tempurature": "temperature",
    # and the joints people type in a hurry: "my ancle is swollen" reached nothing at all.
    "ancle": "ankle", "ankel": "ankle", "ankkle": "ankle",
    # "my nan fel over" - a fall is one of the things an older person does not get up from
    # ("felin" is left out: far more often it is "feeling")
    "fel": "fell", "faling": "falling",
}


# More of the way people shorten words when they type quickly.
CHAT.update({
    "yall": "you all", "kay": "ok", "okie": "ok", "thankyou": "thanks",
    "thanku": "thanks", "iono": "i do not know", "pic": "picture",
    "pics": "pictures", "rite": "right", "gunna": "going to", "gna": "going to",
    "gona": "going to", "cu": "see you",
    # "i gota go" was "I'm listening - say more if it helps" until the t it is missing.
    "gota": "got to",
    "tmr": "tomorrow", "l8r": "later", "rly": "really", "srsly": "seriously",
    "cnt": "can not", "hve": "have", "luv": "love", "lv": "love", "luvs": "loves",
    "wht": "what", "hw": "how", "hwo": "how", "wen": "when", "wens": "when",
    "wher": "where", "yr": "your", "urself": "yourself", "prolly": "probably",
    "mayb": "maybe", "sry": "sorry", "srry": "sorry", "nd": "and",
    "dat": "that", "dis": "this", "dem": "them", "dey": "they",
    # The small words a sentence is built from, typed the way the person says them. A slip in
    # one of these does not just look untidy: the words carry no topic and no mood of their own,
    # so a line that keeps one has nothing for a module to hold on to and comes back as an echo
    # of what was typed ("Noted: you're going wif your mum to town", "Noted: you don't want eny
    # of it"). The letters that go are the ones a person does not hear ("haz", "woz"), and
    # "summin", "somet", "eny", "ppls" and "txt" are the same word with its middle eaten.
    #
    # "ny" and "ne" are not on the list, though they look like short "any": "ny" is how people
    # write New York and "ne" is what a hurried "me"/"my" looks like on a keyboard where n and m
    # are beside each other. Mapped to "any", "ny mum said no" came back as "any mum said no"
    # and "i live in ny" as "i live in any" - a misquote of the line, which is worse than the
    # echo it replaces. "der" for "there" goes the same way ("der man said no"), and "dere" is
    # already in CHAT. "innit" is the tag on the end of a statement, which the tag reader owns.
    "wif": "with", "widout": "without", "wiff": "with",
    "summin": "something", "sumthing": "something", "somet": "something",
    "summink": "something", "eny": "any", "enything": "anything",
    "woz": "was", "haz": "has", "ppls": "people's",
    "txt": "text", "txts": "texts",
    # "where's" with the e and the apostrophe gone is a question about a place, and keeping it
    # as typed lost the answer: "wers my keys" got "I'm listening - say more if it helps" while
    # "wheres my keys" gets the lost-keys answer. It is read in `normalize._wers_word`, not here,
    # because after a person it is the verb "wears" ("she wers a red coat"). "presnt" is
    # "present" with the e gone.
    "presnt": "present",
    "wiv": "with", "abit": "a bit", "incase": "in case", "atleast": "at least",
    "eachother": "each other", "infront": "in front",
})

# The everyday word people misspell by leaving a letter out of the middle or by putting a letter
# run in the order they say it. None of these is a word, and none is one edit from the word it
# stands for, so no reader in `normalize` reaches them: "evry" is two edits from "every", and the
# line kept it, so a line about a boiler at nine `evry` morning was not read as one. The words here
# are the ones a person writes a hundred times a week - when, before, again, school, sorry, money -
# because that is where a hurried hand goes wrong, and a reading that loses one of them loses what
# the line is about.
MISSPELLINGS.update({
    "evry": "every", "evrey": "every", "evryone": "everyone", "evrything": "everything",
    "agin": "again", "befor": "before", "agen": "again",
    "sory": "sorry", "skool": "school", "finaly": "finally", "famly": "family",
    "frends": "friends", "frend": "friend", "frendly": "friendly",
    "deposite": "deposit", "holliday": "holiday", "hollidays": "holidays",
    "muney": "money", "managment": "management", "bolognase": "bolognese",
    "similer": "similar", "genuinly": "genuinely", "basicly": "basically",
    "foriegn": "foreign", "quater": "quarter", "secound": "second",
    "surprized": "surprised", "toghether": "together", "yestarday": "yesterday",
    "vegtarian": "vegetarian", "brnded": "branded",
    # The words a follow-up asking what the last answer means is made of, typed by ear. The
    # corrector reads the same sound with the vowel the wrong way round as a slip of a different
    # word ("meen" is "mean", but it is one letter from "been" too, and "dos" is a word already -
    # the plural of "do" - so a real word is never bent towards another one). So the table is the
    # only place they land. Without them `what does that meen`, `what dos that mean` and
    # `whats that suposed to mean` reached the search hedge while the same line spelt correctly
    # got the answer said again in plainer words (crisp-goose, #understanding).
    "meens": "means",
    "meen": "mean", "meening": "meaning", "meent": "meant",
    "deos": "does", "suposed": "supposed", "supose": "suppose",
    "suposedly": "supposedly",
    # "dos" is a word already ("the dos and donts", "ms dos"), so it is bent only where the words
    # after it make it the auxiliary: "what dos that mean", "how dos it work".
    "dos that": "does that", "dos it": "does it", "dos this": "does this",
    "dus that": "does that", "dus it mean": "does it mean",
    "dos the": "does the", "dos he": "does he", "dos she": "does she", "dos your": "does your",
})

# Words people write as one and say as two. These are not words in any language, so they are set
# down as the two words in `clean` itself (see JOINED_WORDS in normalize.py): "im fedup with my job"
# was "Thanks for telling me" while "im fed up with my job" gets the fed-up reply, and they are the
# same line.
JOINED_WORDS = {
    "fedup": "fed up", "sickof": "sick of", "tiredof": "tired of", "boredof": "bored of",
    "pissedoff": "pissed off", "cheesedoff": "cheesed off", "hadenough": "had enough",
    "shutup": "shut up", "growup": "grow up", "comeon": "come on", "goaway": "go away",
}

# Typed quickly, heard once and written down the way it sounded: greetings, thanks and the
# small words around them. These are the lines a person sends on their own, so a miss here
# costs a whole turn.
CHAT.update({
    "morngin": "morning", "mornging": "morning", "mornign": "morning",
    "mornin": "morning", "gud": "good", "gewd": "good",
    "alrite": "alright", "awrite": "alright", "awright": "alright", "aight": "alright",
    "thnaks": "thanks", "tahnks": "thanks", "thankz": "thanks", "cheerz": "thanks",
    "cheeers": "thanks", "wassup": "what is up", "sup": "what is up",
    # The letters a thank you is cut down to: the sound for the whole word, or the initials of
    # the whole phrase. A line that is only one of these is the whole turn, so a miss costs it.
    "thks": "thanks", "thnx": "thanks", "thanx": "thanks", "thankx": "thanks",
    "tnx": "thanks", "tyty": "thanks", "tysm": "thanks", "10q": "thank you",
    "fankyou": "thank you", "fanku": "thank you", "fank you": "thank you",
    "howz": "how is", "hru": "how are you", "yoo": "hi",
    "yo": "hi", "hai": "hi", "hihi": "hi", "heyoo": "hey",
    "ideeas": "ideas", "ideea": "idea", "wt": "what", "wnt": "want",
    # A name for something written with the fewest letters that still read the same.
    "m8": "mate", "m8s": "mates", "drs": "doctors", "bday": "birthday",
    "appt": "appointment", "appts": "appointments",
})

# The sound of a word written the way it comes out, where the spelling is not a word in any
# sense: "urt" for hurt, "bort" for bought, "hu" for who. Nothing has to be guarded here - no
# English word is spelled like this - so the whole word is read for the word it means. It is
# read in `plain` only: `clean` keeps what the person typed, because a reply must not put a
# word in their mouth. "my chest urts" was answered "I'm listening", while "my chest hurts"
# gets the 999 reply, so this is a turn that is lost rather than a turn that is worded oddly.
CHAT.update({
    # The ache, said with the h dropped. Every part of the body a person names takes it.
    "urt": "hurt", "urts": "hurts", "urting": "hurting", "urted": "hurt",
    # The -ought words, said with a flat o.
    "bort": "bought", "thort": "thought", "brort": "brought",
    # The one question word that is not spelt the way it sounds.
    "hu": "who",
})

# A common verb written the way it sounds. "werk" is "work" typed in a hurry, and the letter
# is not the point: the word is the subject of the line, and every card about a thing that has
# stopped is keyed on it. "my tv dont werk" got "Thanks for telling me", "my laptop dont werk"
# got "I'm listening", and "me fone dont werk" got "Got it" while the same three lines spelt
# right get the television, the laptop and the phone repair. No other word in the language is
# read the same way, so the whole family is set down: the -s, the -ed and the -ing.
CHAT.update({
    "werk": "work", "werks": "works", "werked": "worked", "werking": "working",
    # "elp" is "help" with its first letter gone - the line a person types when they are asking
    # for it. "i need elp wiv me cv" was answered "Elp wiv you cv - fair enough. What's stopped it
    # happening so far?", which is the echo frame for a noun nobody named, and "can u elp me
    # sleep" got "I'm not sure about that one" where "can you help me sleep" gets the sleep card.
    "elp": "help", "elps": "helps", "elped": "helped", "elping": "helping",
    # "reckn" is "reckon" with the o gone, and the phrase it sits in - "what do you reckon" - is
    # the whole of an opinion ask. "what do u reckn" got "I'm not sure about that one, sorry - I'd
    # rather not guess" where "what do you reckon" gets "Ask away, I'm listening." "rekon" is
    # already set down; this is the same word with the vowel gone rather than swapped.
    "reckn": "reckon", "reckns": "reckons", "recknd": "reckoned", "reckning": "reckoning",
})

# A dialect word for how somebody is, read as the plain word it means, so the answers keyed on
# the plain word reach the line: "im ropey" was answered "Nice to meet you, Ropey", and the name
# stayed for the rest of the chat ("You're Ropey" when they asked). The word the person typed is
# kept in `clean` and `text`, so no reply says a word they did not write.
DIALECT_STATES = {
    "ropey": "unwell", "ropy": "unwell", "hackit": "rough", "gubbed": "shattered",
    "scunnered": "fed up", "crabbit": "grumpy",
}
CHAT.update(DIALECT_STATES)

# The words people clip to the fewest letters that still read the same: a week is a "wk" and
# tonight is "tnite". Settling them here means every module that reads the normalised line sees
# the word the person meant, not the one they had room to type.
CHAT.update({
    "nxt": "next", "wk": "week", "wks": "weeks", "wknd": "weekend", "wknds": "weekends",
    "mth": "month", "mths": "months", "mnth": "month", "mnths": "months",
    "2moz": "tomorrow", "2mz": "tomorrow", "tmoz": "tomorrow", "2morro": "tomorrow",
    "yrs": "years", "hrs": "hours", "mins": "minutes", "secs": "seconds",
    "defo": "definitely", "shd": "should", "culd": "could", "spk": "speak",
    "tnite": "tonight", "tnight": "tonight", "tonyt": "tonight", "gna": "going to",
    "jst": "just", "ovr": "over", "abwt": "about", "bwt": "about",
    "skl": "school", "hol": "holiday", "hols": "holidays", "agen": "again",
    "forgetin": "forgetting", "forgettin": "forgetting",
})

# The shorthand of a quick message: initials for a whole phrase, a digit for a sound, and
# the northern short forms. None of these is a word on its own, so nothing ordinary is bent.
CHAT.update({
    "ngl": "not going to lie", "wdym": "what do you mean", "wym": "what do you mean",
    "tbf": "to be fair",
    # "ages" is a long time, not the verb "age". The knowledge matcher stems a word to meet its
    # key, so the "ages" in "i havent cooked in ages" met the ageing row's "we age" and the person
    # who has not cooked for months was told what ageing does to cells. The saying is read as the
    # words it stands for, which is the meaning every reader wants: "i havent slept properly in
    # ages" is a long time, not a stage of life.
    "in ages": "in a long time", "ages ago": "a long time ago",
    "been ages": "been a long time", "takes ages": "takes a long time",
    "took ages": "took a long time", "taking ages": "taking a long time",
    "ttyl": "talk to you later", "omw": "on my way", "fyi": "for your information",
    # The sign-off, typed as the letters or the sound of it: "gn" is the end of a chat, and
    # read as nothing at all it got "Got it. Is there anything you'd like a hand with?" at the
    # moment the person was leaving. The repair is the goodbye itself, so the sign-off is read
    # off the words, and the plain line keeps what they typed.
    "gn": "good night", "gnite": "good night", "gnight": "good night", "gnyt": "good night",
    "buhbye": "bye", "buhbye now": "bye now", "nighto": "night",
    # "ciao" is a greeting as often as a sign-off ("ciao", then "how are you doing today?"), and
    # the chat table is read wherever the word stands, so it is left to the greeting it already
    # is. The words below are only ever said on the way out.
    "peace out": "bye", "toodles": "bye",
    "nowt": "nothing", "aye": "yes", "l8ly": "lately", "slee": "sleep",
    # The northern child word: "bairn" is the noun, not a slip, so the family words reach it the
    # way they reach "kids" (`the bairns are driving me up the wall`). "wean" is left alone
    # because the verb is common ("how do i wean my baby onto solids").
    "bairn": "child", "bairns": "children",
    "hv": "health visitor", "hvs": "health visitors",
    "wev": "we have", "av": "have",
    "shud": "should", "shld": "should", "wud": "would", "wuld": "would",
    "guna": "going to", "gona": "going to", "goina": "going to",
    # "meself" is how the reflexive is said and typed in most of the north of England, and
    # "mesen" is the same word further north again: "im cacking meself", "im shittin mesen".
    "meself": "myself", "mesen": "myself", "me self": "myself",
})

# Contractions without an apostrophe, and the positive forms people leave alone.
EXPAND = {
    "dont": "do not", "doesnt": "does not", "didnt": "did not", "isnt": "is not",
    "arent": "are not", "wasnt": "was not", "werent": "were not", "cant": "can not",
    "couldnt": "could not", "shouldnt": "should not", "wouldnt": "would not",
    "wont": "will not", "havent": "have not", "hasnt": "has not", "hadnt": "had not",
    "mustnt": "must not", "neednt": "need not", "aint": "is not",
    "im": "i am", "ive": "i have",
    "youre": "you are", "youve": "you have", "youll": "you will", "youd": "you would",
    "theyre": "they are", "theyve": "they have", "theyll": "they will",
    "weve": "we have",
    "shes": "she is", "hes": "he is", "thats": "that is", "theres": "there is",
    "heres": "here is", "lets": "let us",
}

# Negative markers, for "no"/"not" scoping.
NEGATIONS = frozenset("not no never none nothing nobody neither nor cannot".split())

# The words that open a clause saying WHEN or WHERE something happened. That clause is
# background: "it started this morning when i was in the garden" is about whatever started,
# not about the garden. Only a time or a place is background this way; "because" and "if"
# carry the reason and the condition, which are the line's subject as often as not ("i cant
# sleep because my back hurts" is a back).
BACKGROUND_STARTS = frozenset("""when whenever while whilst after before since during until
    where wherever""".split())
# The verbs a line uses to report when something began. With only "it" in front, the line
# has no subject of its own: it is about the last thing talked about, and the time or place
# after it is where that thing happened ("it started at work in the garden centre").
START_VERBS = frozenset("""started starts began begins happening happened happens kicked
    comes came""".split())
# Where a line says something happened. In a line that only reports when it began, the words
# after one of these are the place, not the subject.
PLACE_PREPS = frozenset("in at on near inside outside around from".split())
# The words that end a place phrase: after one of these the line has moved on to the next
# thing it says ("it started at work and now my chest hurts").
CLAUSE_BREAKS = frozenset("""and but so then now because cos if when while after before
    which that who whose""".split())

# The words that open a line and decide how the whole line is read: a question word makes it a
# question, a greeting makes it a hello. People misspell them the same way at speed ("whts",
# "whn", "hw", "hii", "thnks"), and one slip in the opening word changes the reading of
# everything after it, so `normalize.fix_opener` repairs that word against this list.
OPENERS = """
    what why when where who which whose how
    whats whys whens wheres whos hows
    hi hello hey hiya heya howdy morning evening
    thanks thankyou cheers
    bye goodbye cya
    can could should would will shall is are was were am do does did have has may might
"""

# Found by `python tools/typo_scan.py`, which lists every repair the typo readers make on the
# deck's own lines. Each word here was read as a slip of a key word (depth->death, appeal->appear,
# chance->change, closer->close, crisp->crispy, polite->police, pushy->push, unfair->unpair,
# wrinkly->wrinkle): one wrong match today, and a wrong answer as soon as a domain keys on the
# word it invented.
COMMON += """
appeal chance closer crisp depth polite pushy unfair wrinkly
"""

# Found by the same scan in `--words` mode, which runs the line fixer over every word the
# knowledge base and the deck use. The left-off-g reader turns a word ending in "in" back into
# the -ing form the lexicon knows through an inflection, and these are words of their own:
# basin->basing, shin->shing ("shing" came from "she" + "ing").
COMMON += """
basin shin
"""

# Meals by the names people give them. Each was one slip from a key word of the knowledge base
# ("brunch" -> "bunch", the herbs; "chow" -> "chop"), so the reader bent the word into another
# one and "what brunch should i make" was answered with how big a bunch of parsley is. A word
# here is a word the engine reads, so it is never a slip of anything.
COMMON += """
supper brunch pudding dessert pud afters nibbles elevenses brekkie brekky sarnie butty cuppa
takeout nosh grub chow kebab chippy munchies bap sanger bbq barbecue
"""

# "desert" is the meal word's twin and a word of its own. Without it here the meal words above
# made it the nearest neighbour of "dessert", so the line fixer "repaired" a desert that was
# spelled right: "the sahara desert" came back as "the sahara dessert" and read as food.
COMMON += """
desert deserts deserted deserting
"""

# Found by `python tools/typo_scan.py` on the deck's own lines. Each is a word or a name the
# engine did not read, so the knowledge matcher bent it into a key word: hiya -> hoya (the
# plant), wots -> wet, satay -> stay, jerry -> jerky, kate -> kale, preston -> presto,
# unfit -> unit, manic -> magic, silly -> sill. A word here is read as typed, so none of those
# answers is reached by a slip.
COMMON += """
hiya satay jerry kate preston unfit manic silly
"""

# The spoken verbs that the reading's own feeling words are built from. "im brickin it", "im
# shittin myself", "im freakin out", "im hopin to", "im pukin" are how these lines are typed,
# and the left-off-g repair can only put the g back on a word the lexicon has, so a nerves line
# the tables know perfectly well lost its feeling word and came back "I'm listening".
COMMON += """
hope sting freak shit crap cack brick puke barf throw
"""

# The same for the two verbs whose -ing form doubles the last letter, which the inflection
# rules do not do: "shittin myself" and "crappin myself" are the nerves idiom too.
COMMON += """
shitting crapping cacking
"""

# Laughter and filler: signals, not content.

# Ordinary words that end in "in" and are not a verb missing its g: "satin" is a cloth, not
# "sating", and "a satin dress" should not read as one. A left-off g is repaired anyway only
# for a word nothing else knows, so this list is just the words that would be damaged.
# Everyday verbs the base list above never carried. Without them the whole family is unknown,
# so "leavin", "wearin" and "hopin" had no form to be repaired to and were left as themselves,
# and any module asking about the doing saw nothing: "im leavin me job", "im wearin a splint",
# "im hopin to move". The forms are written out because `_inflections` runs off these words.
COMMON += """
beat beats beating beaten blow blows blowing blown break breaks breaking broke broken
carry carries carried carrying catch catches catching caught choose chooses choosing chose
chosen climb climbs climbing climbed close closes closing closed decide decides deciding
decided die dies dying died dig digs digging dug draw draws drawing drew drawn drop drops
dropping dropped dry dries drying dried fit fits fitting fitted forget forgets forgetting
forgot forgotten forgive forgives forgiving forgave forgiven happen happens happening
happened hear hears hearing heard hide hides hiding hid hidden hit hits hitting hit hold
holds holding held hope hopes hoping hoped jump jumps jumping jumped kick kicks kicking
kicked laugh laughs laughing laughed leave leaves leaving left lend lends lending lent
listen listens listening listened lose loses losing lost
meet meets meeting met melt melts melting melted mend mends mending mended pull pulls
pulling pulled push pushes pushing pushed ride rides riding rode ridden rise rises rising
rose risen send sends sending sent shake shakes shaking shook shaken share shares sharing
shared shine shines shining shone shoot shoots shooting shot shut shuts shutting sit sits sitting sat slide slides sliding slid smell smells
smelling smelled smile smiles smiling smiled spin spins spinning spun stand stands standing
stood stay stays staying stayed steal steals stealing stole stolen stick sticks sticking
stuck taste tastes tasting tasted tear tears tearing tore torn throw throws throwing threw
thrown understand understands understanding understood visit visits visiting visited wear
wears wearing wore worn win wins winning won wipe wipes wiping wiped wish wishes wishing
wished wonder wonders wondering wondered
"""

# The -ing forms the left-off-g reader had nothing to put its g back on. It can only repair a
# word whose -ing form the lexicon holds, and the lists above are stems, so a person who typed
# "frostin", "rattlin", "christenin", "orderin" or "chewin" kept the word they typed: the topic
# and the entry that would have answered them never saw the word ("how do i make frostin that
# isnt runny" was answered with a tomato sauce, and "my mouse isnt connectin" with "Thanks for
# telling me"). Found by running the line fixer over every -ing word the deck and the knowledge
# base use, and written out as the -ing form because most of these verbs are not in the lists
# above at all (chew, frost, fill, crack, scratch) and some double a letter the inflection
# rules do not guess ("panicking", "upsetting", "sliding").
COMMON += """
acting adopting affecting amazing annoying apologising applying attacking autocorrecting
avoiding barging barking basting bearing beeping begging blaming bloating blocking bookkeeping
borrowing breastfeeding breeding bubbling buffering bulging bullying bumping bunching bursting
buzzing camping challenging charging cheating chewing chirping chocking christening clanking
clawing clearing clicking clinging clunking clutching coding collapsing commenting comparing
conditioning connecting considering contesting coping covering cracking crackling cramming
crashing craving creaking creasing criticising crumbling crushing crystallising curling
decorating dehydrating depressing dimming dining dipping disappearing disconnecting distracting
dodging dragging draining dreading dribbling drifting drooping drowning dumping dumpling
escalating exhausting expecting fading failing fainting fattening filling firing flaking flaring
flickering flooding flowering flushing foaming fouling frosting funding gaining
gaslighting glazing grabbing grinding grovelling grunting gurgling handwriting hiking hiring
hopping hosting humming ignoring including interfering interrupting investing inviting juddering
knitting knocking leaning leasing licking lifting mentioning meowing merging messing mounting
mourning neutering nipping nitpicking offering ordering outgrowing overcharging overflowing
overhanging overheating overreacting overthinking panicking panting paving peeling piling
pinging pooling popping pouring pricking proofing proving punching queuing raging raising
rattling reassuring recycling redoing refusing renewing replaying replying rereading
rescheduling responding restructuring retaining returning ripening rolling rotting rounding
safeguarding sagging sanding scaffolding scarifying scoring scrambling scratching screaming
scrolling seething servicing serving sewing shaving signing simmering singing siting skiing
skipping slamming slipping slurring snapping sniffling snoozing sobbing sowing sparking spelling
spiralling spitting spreading sprouting squeaking squealing stalking stalling steaming steering
stifling stinking stocking strangling streaming submitting subtracting sucking swearing
switching syncing tangling tempting thickening threatening thumping tipping touching tracking
travelling twirling typing undermining updating upgrading uplifting upsetting wandering warning
wasting waterproofing weeping wetting wheezing wobbling wrapping wrecking wuthering yowling
"""


# Words that are their own word and look like a shorter word plus an ending: "career" is not
# "care" with -er on it, and the lexicon carried it only by that accident. Naming it here keeps
# it a word now that the shorter word's real form is the one written ("carer").
# The other four are the words that keep the e before -ing, and they are named here rather than
# in the reader alone because a word the lexicon knows is a word no repair has to undo: the
# extra-vowel reader turned "singeing" into "singing" and "singeing my hair" was read as a line
# about singing. "dyeing", "tingeing" and "swingeing" sit in exactly the same place.
# A word people type is a word, even when it is one letter short of another one's doubled
# spelling: the reader that puts back a letter a word doubles is a general one, so it looks at
# "bled", "wed", "lager" and "telly" as words that lost a letter. Each of the words below is in
# the deck or in the bot's own prose as it stands, and each of them is a doubled letter away
# from a different word the lexicon holds ("bled" is one letter from "bleed", "moped" from
# "mopped", "latter" from "later"). They are named here so that the word a person wrote stays
# the word they wrote. The list is mined from what the bot has already been said and has
# already said; a real word outside it can still be bent, which is the price of reading "slep",
# "kiling" and "anyfing" as the words they are.
_DOUBLED_NOT_A_SLIP = """
bled butt cal canceling caper carers casein committed crispin desserts ding fibrin filing
latte
filings filling fillings finnish freeing hover hovering hovers lager latter leds ling losses
mealy moped moping mopped mopping munches noted noting notted notting oily painting paned
pilling planed planing pulsing putin putt queueing saladin sed stalin sumer teether tether
thee traveling travelling wed weds weeing
"""
# Everyday words that sit one letter from a feeling word, and are never that feeling typed with a
# slip. A feeling is a closed list, so one letter out is still that feeling - but only when the
# word is nobody's word to begin with. These are: "my baby has a nappy rash" was read as "a
# snappy rash", "i scored a goal" was answered "I'm sorry - that's frustrating" (scared), "she
# gave me an earful" was sad (tearful), "a tankful of petrol" was grateful (thankful), "the
# mattress sagged" was shagged, "this place is sacred" was scared, "cress in a sandwich" was
# cross, "the seat is leased" was pleased, "aging" was raging, "staring"/"etched" were
# starving/itching. The lexicon does not hold these words, so they are named here instead.
NOT_A_FEELING = frozenset("""
aging bashed bused cress criss earful etched etching leased naked nappy sacred sagged sappy
scored staring tankful""".split())
# "tiered" is not here on purpose: "the cake is tiered" is a cake, and "im tiered or just bored"
# is somebody saying how they are, so only where the word stands tells the two apart - that is
# the frame in `normalize._near_a_feeling`, not this list.

# Words that are real and that the lexicon does not otherwise hold, so that no reader bends
# them towards the word it thinks they nearly are. "nappy" was bent to "snappy" by the feeling
# repair once a time word let a state stand after a be-form: "he was nappy last night" came back
# as a short temper, and "he was nappy" and "he was nappy all day" with it. The word a person
# wrote stays the word they wrote, and the repair keeps the words it was built for ("nackered",
# "exausted", "worrid": none of those is a word, which is why they are not here).
# "fired" is a word of its own, and the feeling list holds "fried": the two are one swap apart,
# so the feeling repair read "i got fired today" as "i got fried today" and the reply lost the
# job. It bends into a feeling, which is what this list is for.
REAL_WORDS = frozenset("""career careers dyeing singeing tingeing swingeing
nappy nappies fired""".split())

# The words above, and the words the deck and the bot's prose use as they stand, as one set: a
# word here is a word, so no reader bends it. It is kept out of REAL_WORDS on purpose - a word a
# candidate list holds is a candidate for another word's slip ("thee" in the lexicon read "fee"
# as "thee"), so these ride beside the lexicon, not in it.
TYPED_WORDS = frozenset(_DOUBLED_NOT_A_SLIP.split())

REAL_IN = frozenset("""satin raisin basin cabin robin napkin muffin violin margin origin
protein pumpkin cousin resin ruin twin grin shin skin spin chin pin bin din fin gin kin sin
tin win within begin origin vitamin insulin aspirin gelatin tarragon gratin crispin saladin""".split())
# Laughter as people type it: one "ha" is a laugh the way "haha" is, "hahahaha" is the same
# laugh held longer, and the "heh"/"hehehe" family is the quiet version of it. The signal is
# what tells a laugh from a line about something, so a spelling missing here is a laugh that
# reads as a statement and gets answered with "Got it." instead of a laugh back.
LAUGHTER = frozenset("""lol lols lolz lul lulz lolol lololol lmao lmfao lmfaoo rofl roflmao
ha hah haha hahaa hahah hahaha hahahah hahahaha heh hehe heheh hehehe heheheh""".split())

# What a person says they are like. A trait is not how they are today ("im hungry") and it is
# not who they are called: "im lazy", "i am lazy" and "im lazy lol" were answered "Nice to meet
# you, Lazy. What can I help with?", and "im so shy", "im a bit shy", "im really awkward" and
# "im quite shy" were answered four different ways, none of them a reply to what was said. The
# words are the ones people reach for when they are being hard on themselves, so the same set
# is read as a judgement in bot/modules/chat.py and refused as a name in bot/memory/facts.py.
# Only words that are a trait and nothing else: "quiet", "slow", "odd" and "loud" describe a
# Wednesday as easily as a person, so they are left out.
TRAITS = frozenset("""lazy shy awkward clumsy forgetful impatient selfish greedy mean nasty
boring thick stupid dumb daft clueless useless worthless rubbish crap weak cowardly spineless
jealous moody annoying irritating ugly fat""".split())

# The words `TRAITS` leaves out, because they describe a Wednesday as easily as a person, and
# that is exactly why nothing asked the list when the word came straight after "im": "im quiet",
# "im messy", "im noisy", "im bossy" and "im a bit stubborn" were answered "Nice to meet you,
# Quiet" and the name stuck for the rest of the chat. They are kept in one place here, read as
# how the person is by the understanding engine, refused as a name by bot/memory/facts.py, and
# kept for another person ("my dad is stubborn") by the same list there.
A_DESCRIBING = frozenset("""quiet messy noisy picky fussy bossy stubborn rude spoilt chatty
negative positive tidy untidy nosy weird odd loud hard""".split())


def is_a_laugh(word):
    """True when the word is a laugh as people type it, not only one of the table's forms.

    "hahahahaha", "heheheh" and "lololol" are the same laugh with the letters held down, and no
    table can hold every run length. The reading uses this for the laugh signal and the chat
    module for a line that is a laugh and nothing else, so both hear the same laugh.

    The syllables are whole ones, so no ordinary word is bent into a laugh: a bare "h" syllable
    also builds "huh", "halo", "helo" and "hilo", and a "lo" syllable builds "lolo", which is a
    name. A run of h's is still a laugh, and that is matched on its own.
    """
    if word in NOT_A_LAUGH:
        return False
    if word in LAUGHTER:
        return True
    # One syllable on its own is a word ("he", "hi", "ha"), so a run has to be longer than that.
    return bool((len(word) > 2 and _LAUGH_RUN.fullmatch(word)) or _H_RUN.fullmatch(word))


# The words a run of laugh syllables would otherwise spell: "huh" asks the bot to say that again,
# "halo"/"helo"/"hilo" are other things, and "lolo" is a name.
NOT_A_LAUGH = frozenset("huh halo helo hilo hola lolo lulu".split())

# The syllables people repeat: ha, he, hi, ho, hu and "lol", held down to any length ("lolol",
# "lololol", "lolololol"). A word has to be made only of them.
_LAUGH_RUN = re.compile(r"(?:ha|he|hi|ho|hu|l(?:ol)+)+")
# A run of h's on its own is a laugh too ("hh", "hhhh").
_H_RUN = re.compile(r"h{2,}")

# Chat words that are not words at all, whose repair is two words or more. `plain` is the line the
# readers that match English words see, and a repair reaches it only when it is one word, so these
# are named here and the plain line carries them too. A contraction is not one of these: "don't" ->
# "do not" is the same words read out, and plain keeps the spelling the writer used.
PLAIN_EXPANDS = frozenset("""cba cbf stomakaike wuu2 wu2 wuu wdyt wdym wym idk dunno seeya
    wanna wana wanne wannna wanta gona gonna gunna guna goina gna gotta gota
    lemme gimme kinda sorta outta owta hafta hasta tryna trynna
    coulda shoulda woulda musta
    shouldve whatre""".split())

# The day a line is about, typed short, when the repair is one word rather than two. `clean` is
# the line as it was typed, and a reader that matches on it met "tmoz" and did not know what day
# that was: "is it gna rain tmoz" was read as a line about no particular day and got the search
# hedge, while the same line spelled out gets the honest note about the forecast. The reading had
# both right (`plain` says "tomorrow"); only what a `clean` reader matches was missing it.
#
# This does not reach everything that spells the day out. `going to the coast tmrw` still says
# "The Coast Tmrw - nice. When are you going?", because the place name is cut from the line as
# typed rather than from `clean` (bot/memory/trips.py), and that reader is a change of its own.
#
# A day word is worth spelling out because it decides whether a line is about a day at all: the
# shortenings drop the whole vowel run, so "tmrw" and "2moro" carry nothing of "tomorrow" for a
# pattern to find. Measured with tools/compare.py over every deck chat that carries one: 1 chat
# better, 0 worse, the rest unchanged, and 0 of 184 replies changed in a blind sample either side.
#
# "tomo" is not here either, and that is measured: it is also a short name ("i met tomo at
# work" got "How was it, overall?" and, spelled out as a day, fell to the pool that says nothing).
# It is the one form in the set with no "r" and no "2" to tell it apart from a person.
#
# The words for yesterday are not here: `i saw her yday and she looked rough` changed the nod it
# got ("Sounds alright" -> "Nice one") with no gain, so the day a line is about pays here only when
# the line is about a day still to come. Today's words are here and measured inert (25 chats,
# nothing changed), kept because they are the same shortening of the same idea.
#
# The night words ("tnite", "2nite", "tonite") are not here yet, and that is measured too:
# spelling them out makes the free-evening plan answer "im gonna make a spag bol tnite any
# tips", because "tonight" is one of the words that plan is keyed on and it outranks the dish.
# It also costs a follow-up ("wat shud i cook 2nite" / "is it ok?") the answer it links to. Add
# them once the plan row stands down for a line that names something to cook.
PLAIN_ONE_WORD = frozenset("""tmrw tmw tmr tmoz 2moz 2mz 2moro 2mora 2morra 2morro 2morrow
    tmrow tmorro tomoz tomoro tommorow
    tday 2day todai""".split())

# A chat form that is not a word at all, whose meaning is one word: "u" is "you", "ur" is "your",
# "ya" is "you" and "r" is "are". These are the four a reader that matches English words has to be
# given the meaning of, because there is nothing in "u" for it to match. The words of the line
# carry the meaning ("what are you reading", "how do i write a thank you letter"), and the line
# itself keeps what was typed, so a reply quoting the person still reads as they wrote it. A "u"
# that is the letter - "the letter u", "u turn", "u's" - is the letter and keeps it: see
# normalize._a_short_word_named.
SAID_SHORT = {"u": "you", "ur": "your", "ya": "you", "r": "are"}

# A line that opens with a hand-off announces what comes next ("one more thing", "quick
# question") and then says it; the announcement is not what the line is about. "one more thing
# about the boiler" reached the study entry, because "one" and "thing" are words a key there
# happens to match, and got a paragraph about rereading for an exam. These are the phrases a
# knowledge key is matched without, longest first, and only when the line carries something
# after them (bot/knowledge/lookup.py, `_past_a_handoff`).
HANDOFF_LEADS = (
    "one more thing", "one more question", "one more q", "one more ask",
    "one last thing", "one last question", "one final thing",
    "another thing", "another question", "another one", "another ask",
    "the other thing", "one other thing", "the last thing", "the last question",
    "last thing", "last question", "the next thing", "next thing", "next question",
    "quick question", "quick one", "quick q", "a quick question", "a quick one",
    "a different question", "a different one", "a separate question", "an unrelated question",
    "one thing more", "a couple more things", "couple more questions", "two more things",
    "before i forget", "while im here", "while i am here",
)

# The words that carry a line from the hand-off to what it is about, and go with it: "one more
# thing about the boiler" is a line about the boiler.
HANDOFF_BRIDGES = ("about", "on", "re", "regarding", "concerning", "as for", "to do with")

# The parts of the body people say are hurting, and the words that say a part is hurting. Both
# are closed lists, which is what lets the reading repair a misspelt one: a word a letter out of
# exactly one of these, in a line that already says a part hurts, is that part - "my cheast
# hurts", "my tomach is sore", "my hed is banging". Put here rather than in topics.py because
# the repair happens once, in `normalize`, and the topic rule that reads it lives in topics.py.
#
# Every part a person is likely to say is hurting belongs here, not only the ones the answer
# pools were written around: a part left out of the list can never be mended, so "my troat hurts"
# stayed a shrug ("Does it come and go, or is it there all the time?") while the sore-throat
# answer sat there waiting for a throat spelt right. The parts people name most and the
# misspelling fixer missed - throat, gums, calf, shin, armpit, groin - were the gap.
BODY_PARTS = frozenset("""back neck head shoulder shoulders arm arms elbow wrist wrist hand hands
finger fingers thumb thumb chest rib ribs stomach tummy belly knee knees leg legs ankle foot feet
heel hip hips jaw tooth teeth ear ears eye eyes muscle muscles skin
throat nose gut waist spine lung lungs
shin shins thigh thighs calf calves toe toes
mouth tongue gum gums lip lips cheek cheeks chin forehead temple temples armpit groin
palm palms bum
""".split())
# The beating words are pain words too, and only beside a part of the body: "my head is
# pounding", "my head is thumping", "my head is splitting". A heart pounds and music thumps, so
# the word on its own says nothing - the part of the body next to it is what makes it a
# headache, and that is the rule that reads this list (`topics.HURT_BOOST`).
PAIN_WORDS = frozenset("""hurt hurts hurting ache aches aching sore painful pain agony killing
throbbing stinging stiff swollen swelling numb cramp cramped burning pins needle
pounding thumping splitting""".split())
# A real word typed for another real word that sounds the same. MISSPELLINGS cannot hold these:
# a slip is never a word of its own, and every one of these is ("loose" and "lose" are both
# English), so bending one into the other would break the lines that mean what they typed ("a
# loose screw", "the desert is hot"). They are a second chance instead, tried only when the line
# as typed reads as nothing at all (bot/understanding/__init__.py, `_confused_text`):
# "whats the best way to loose weight" reads no topic, and "lose weight" reads the fitness one.
#
# Where both words are said in the same sort of line, the place the word stands settles it: "a
# loose screw" is a screw and "i want to loose weight" is weight, "bad breath" is breath and "i
# cant breath" is breathing. The three tables below are the unambiguous word, the word that
# needs the word before it, and the word that needs the word after it.
CONFUSIONS = {
    "looser": "loser", "loosing": "losing",
}
# word: (the word they meant, the words it may follow). "loose" and "breath" in front of a thing
# they do are the verbs; before a noun that is a thing they are the words themselves.
CONFUSIONS_AFTER = {
    "loose": ("lose", frozenset("""to dont didnt doesnt wont wouldnt cant cannot couldnt
shouldnt gonna gotta want wants wanted try trying tried need needs needed plan planning
help helps helped""".split())),
    "breath": ("breathe", frozenset("""to cant cannot couldnt can hard struggling struggle
need needs needed try trying tried forget forgets forgot remember remembers learn learnt""".split())),
    # "dos" is a word already - the plural of "do" - so a table that bent every one of them would
    # turn "the dos and donts of a new job" and "ms dos" into "does". It is the question word in
    # front that makes it the auxiliary: "what dos that mean", "how dos it work". Without it the
    # meaning follow-up reached the search hedge while the same line spelt correctly had its
    # answer said again (crisp-goose, #understanding).
    "dos": ("does", frozenset("what how why when where who which".split())),
}
# word: (the word they meant, the words it may come before). "its quite in here" is a quiet room.
CONFUSIONS_BEFORE = {
    "quite": ("quiet", frozenset("in at on for tonight today now please here there inside".split())),
}
# word: (the word they meant, the words that may follow it). This one is how the person says they
# are, so it needs both the first-person frame in front of it and the end of the clause after it:
# "im board", "im so board all the time". "im board certified", "im board exams" and "the
# chairman of the board" are a board, and the frame is what tells them apart.
CONFUSIONS_IN_A_FEELING = {
    "board": ("bored", frozenset("""all of with at because cause cuz so and but when that today
tonight lately atm rn tbh now again too already most there bit""".split())),
}
# The words between a first-person frame and the way they say they are: "im so board", "i feel
# really board", "im a bit board".
FEELING_FILLER = frozenset("""so really very proper quite well bit kinda kind of that too
pretty much totally absolutely well""".split())
FEELING_LEAD = frozenset("""im i'm iam am feel feels feeling felt getting being""".split())
# "no" is "know" only in front of the word that makes it a question: "how do i no when the
# chicken is cooked". Everywhere else it is the word itself ("no, i havent", "no longer").
CONFUSIONS_BEFORE_A_QUESTION = {"no": "know"}
QUESTION_WORDS = frozenset("when how why what if whether where who which".split())


_ENGINE_WORDS = None


def every_word():
    """Every word this package has a meaning for, as one set: the closing fence on a typo.

    The reading is built from tables - the base words, the chat forms, the personal names, the
    topic and kind words, the parts of the body - and any word in any of them is a word a person
    typed. The knowledge base asks this before it bends a line word into a key word, because a
    real word bent into another real word is a confident answer to a question nobody asked: it
    read "my fella keeps taking credit for my ideas" as "my fell ..." and answered with the
    falls card for an elderly parent, "my friend enid" as "my friend end" and answered a
    friendship with what to do after a breakup.

    The tables are gathered by name rather than listed again, so a word added to any of them is
    fenced in the same turn it is added: the list of real words this replaces was rebuilt by
    hand each time one was found bending a line ("kate" was "kale", "preston" was "presto").
    """
    global _ENGINE_WORDS
    if _ENGINE_WORDS is not None:
        return _ENGINE_WORDS
    from . import body, kinds, topics
    tables = (globals(), vars(topics), vars(kinds), vars(body))
    words = set()
    for table in tables:
        for name, value in table.items():
            if name.startswith("_") or "MISSPELLING" in name:
                # A misspelling table is the opposite of a fence: its keys are the words that
                # are not words, and the reader is meant to bend them.
                continue
            if isinstance(value, (frozenset, set, tuple, list)):
                items = value
            elif isinstance(value, dict):
                # The keys: a table maps the word people type to the word it means, and the
                # typed word is the one this fence is about. A correction is a word of the
                # bot's own writing and needs no fence here.
                items = list(value)
            else:
                continue
            for item in items:
                if not isinstance(item, str):
                    continue
                for word in item.lower().replace(",", " ").split():
                    if word.isalpha():
                        words.add(word)
    _ENGINE_WORDS = frozenset(words)
    return _ENGINE_WORDS
