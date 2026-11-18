"""Animals and wildlife: the questions people ask about the creatures around them.

The answers lane owns this domain. People ask these while watching something, reading to a
child, or answering homework: how long an animal lives, how big or fast it is, which one is the
fastest, and why an animal does the strange thing it does. The facts are school level, the
answer names the number first, and a fact stays out of the reply when the animal has no row for
that question, so a line this table cannot answer passes to another domain instead of guessing.

Kept as data: one row per animal (the words people call it, and the facts it has), and one row
per curiosity (the animal, the words that ask it, the answer). The entries are built from those
tables, so adding a row is all it takes to answer another animal, and no entry holds a phrasing.
"""
import re

from .lookup import entry

ANSWERS = ("nature-and-weather", "science")

# One row per animal. "names" is every word people use for it, singular and plural, because a
# key word matches a line word by its forms and the plural is what most lines carry ("how long
# do elephants live"). A fact that is not in the row is not answered: a question about an
# animal's eyes gets nothing from a row that only knows how long it lives.
ANIMALS = (
    {"names": ("elephant", "elephants", "african elephant", "african elephants"),
     "life": "Elephants live 60 to 70 years in the wild, and a big bull can reach 70.",
     "gestation": "An elephant carries her calf for about 22 months, the longest of any land "
                  "animal - one calf, about 100 kg at birth, and the herd stands round her while "
                  "she gives birth.",
     "size": "An African elephant is the biggest land animal: a big bull is about 3 metres at "
             "the shoulder and 6 tonnes, and a newborn calf is around 100 kg.",
     "speed": "An elephant can charge at about 40 km/h, which is faster than a person can run."},
    {"names": ("lion", "lions"),
     "life": "Lions live about 10 to 14 years in the wild; in a zoo they can reach 20.",
     "size": "A male lion is about 190 kg and 1.2 metres at the shoulder, and the mane grows "
             "darker as he gets older.",
     "speed": "A lion runs at up to 80 km/h, but only for a few seconds: it hunts by stalking "
             "close first."},
    {"names": ("tiger", "tigers"),
     "life": "Tigers live about 10 to 15 years in the wild.",
     "size": "A male Siberian tiger is the biggest cat, at up to 300 kg and 3 metres nose to "
             "tail; a Bengal tiger is about 220 kg.",
     "speed": "A tiger can sprint at about 60 km/h, but only over a short distance."},
    {"names": ("cheetah", "cheetahs"),
     "life": "Cheetahs live about 10 to 12 years in the wild.",
     "speed": "The cheetah is the fastest land animal: about 110 km/h, and 0 to 100 km/h in "
             "about three seconds. It can only keep that up for 20 to 30 seconds, so it hunts "
             "by creeping close first."},
    {"names": ("giraffe", "giraffes"),
     "life": "Giraffes live about 25 years in the wild.",
     "gestation": "A giraffe carries her calf for about 15 months, and the calf drops nearly two "
                  "metres to the ground when it is born, then stands within the hour.",
     "size": "The giraffe is the tallest animal: males reach about 5.5 metres, and more than a "
             "third of that is neck. The neck has seven bones, the same number as yours.",
     "speed": "A giraffe can run at about 50 km/h, and its legs are long enough that a kick can "
             "kill a lion."},
    {"names": ("zebra", "zebras"),
     "life": "Zebras live about 20 to 25 years in the wild.",
     "speed": "A zebra runs at up to 65 km/h and zigzags as it goes, which is harder for a lion "
             "to follow than a straight sprint."},
    {"names": ("rhino", "rhinos", "rhinoceros"),
     "life": "Rhinos live 40 to 50 years.",
     "gestation": "A rhino carries her calf for about 16 months, so well over a year, and a "
                  "single calf every two to four years is normal.",
     "size": "A white rhino is the second biggest land animal, at about 2,300 kg; a black rhino "
             "is smaller, around 1,000 kg, and has the longer horn.",
     "speed": "A rhino can run at about 50 km/h, and it turns faster than you would expect for "
             "something that size."},
    {"names": ("hippo", "hippos", "hippopotamus"),
     "life": "Hippos live about 40 to 50 years.",
     "size": "A hippo is about 1,500 kg and 1.5 metres at the shoulder, with teeth that can be "
             "half a metre long.",
     "speed": "A hippo can run at about 30 km/h on land, and it is the animal that kills most "
             "people in Africa."},
    {"names": ("gorilla", "gorillas"),
     "life": "Gorillas live 35 to 40 years in the wild.",
     "size": "An adult male gorilla is about 1.7 metres tall and 160 to 200 kg, and twice as "
             "strong in the arms as the average person."},
    {"names": ("chimpanzee", "chimpanzees", "chimp", "chimps"),
     "life": "Chimpanzees live 40 to 50 years in the wild.",
     "size": "A chimpanzee is about 1.2 metres tall standing and 40 to 60 kg, and around four "
             "times stronger than a person of the same size."},
    {"names": ("panda", "pandas", "giant panda", "giant pandas"),
     "life": "Giant pandas live about 20 years in the wild, and nearer 30 in a zoo.",
     "size": "A giant panda is about 100 to 115 kg, and it eats up to 12 kg of bamboo a day "
             "because bamboo gives it so little energy."},
    {"names": ("koala", "koalas"),
     "life": "Koalas live 10 to 15 years in the wild.",
     "size": "A koala is about 60 to 85 cm and 4 to 15 kg, and it sleeps around 18 hours a day "
             "because eucalyptus leaves give it so little energy."},
    {"names": ("kangaroo", "kangaroos"),
     "life": "Red kangaroos live about 20 to 25 years.",
     "size": "A male red kangaroo stands about 1.6 metres and weighs up to 85 kg, and it can "
             "cover 8 metres in one hop.",
     "speed": "A red kangaroo can reach about 70 km/h in a burst, and it is faster over distance "
             "than a horse."},
    {"names": ("whale", "whales"),
     "life": "Whales are long-lived: a blue whale lives 80 to 90 years, a humpback about 45 to 50.",
     "gestation": "A whale carries for 10 to 12 months, and the calf is born tail first and "
                  "swims up for its first breath within seconds."},
    {"names": ("blue whale", "blue whales"),
     "life": "Blue whales live 80 to 90 years, and some live past 100.",
     "gestation": "A blue whale carries her calf for 10 to 12 months, and it is about 7 metres "
                  "long and 2.5 tonnes when it is born.",
     "size": "The blue whale is the biggest animal alive, and the biggest that has ever lived: "
             "up to 30 metres and around 150 tonnes, with a heart the size of a small car.",
     "speed": "A blue whale cruises at about 8 km/h and can burst to around 30 km/h when it is "
             "frightened."},
    {"names": ("dolphin", "dolphins", "bottlenose dolphin", "bottlenose dolphins"),
     "life": "Bottlenose dolphins live 40 to 50 years.",
     "gestation": "A bottlenose dolphin carries her calf for about 12 months, and she feeds it "
                  "milk for a year and a half to two years after that.",
     "size": "A bottlenose dolphin is about 2.5 to 3 metres and 200 to 300 kg."},
    {"names": ("shark", "sharks"),
     "life": "Most sharks live 20 to 30 years, and the Greenland shark can live about 400, "
             "which makes it the longest-lived animal with a backbone.",
     "size": "A great white is 4.5 to 6 metres and up to 1,100 kg; the whale shark, at 12 "
             "metres and 20 tonnes, is the biggest fish and eats only plankton."},
    {"names": ("octopus", "octopuses", "octopi"),
     "life": "Most octopuses live only one or two years, and die soon after they breed.",
     "size": "The common octopus is around a metre across and 3 kg; the giant Pacific octopus "
             "can reach 5 metres arm tip to arm tip."},
    {"names": ("penguin", "penguins", "emperor penguin", "emperor penguins"),
     "life": "Penguins live 15 to 20 years in the wild.",
     "size": "The emperor penguin is the biggest, at about 1.1 metres and 40 kg; the little "
             "blue penguin is around 40 cm and 1 kg."},
    {"names": ("parrot", "parrots", "african grey", "macaw", "macaws"),
     "life": "Parrots are long-lived: an African grey often reaches 50 to 60, and a macaw can "
             "pass 80."},
    {"names": ("tortoise", "tortoises", "galapagos tortoise", "giant tortoise"),
     "life": "Tortoises are the longest-lived land animals: a giant tortoise often reaches 100, "
             "and some have lived past 150."},
    {"names": ("crocodile", "crocodiles", "alligator", "alligators"),
     "life": "Crocodiles live 70 to 100 years, and they keep growing slowly all that time.",
     "size": "A Nile crocodile reaches about 5 metres and 500 kg; the saltwater crocodile can go "
             "past 6 metres, the biggest of any reptile."},
    {"names": ("snake", "snakes"),
     "life": "Most snakes live 10 to 20 years in the wild, and a pet corn snake can pass 20."},
    {"names": ("swan", "swans"),
     "life": "Swans live 10 to 15 years in the wild.",
     "size": "A mute swan is about 1.5 metres long with a wingspan of 2.2 metres, and weighs 10 "
             "to 12 kg."},
    {"names": ("fox", "foxes"),
     "life": "A fox usually lives only 3 to 5 years in the wild, though one in captivity can "
             "reach 12."},
    {"names": ("hedgehog", "hedgehogs"),
     "life": "Hedgehogs usually live only 3 to 5 years in the wild; the road is the main danger."},
    {"names": ("squirrel", "squirrels", "grey squirrel", "grey squirrels"),
     "life": "Grey squirrels live about 3 to 5 years in the wild."},
    {"names": ("badger", "badgers"),
     "life": "Badgers usually live 3 to 5 years in the wild, and can reach 10 in captivity."},
    {"names": ("deer", "red deer", "roe deer"),
     "life": "A red deer lives about 15 years and a roe deer about 7."},
    {"names": ("eagle", "eagles", "golden eagle", "golden eagles", "bald eagle", "bald eagles"),
     "life": "A golden eagle lives about 20 to 25 years in the wild.",
     "size": "A golden eagle has a wingspan of about 2.2 metres; a bald eagle's is about 2.3 "
             "metres and it weighs 3 to 6 kg."},
    {"names": ("owl", "owls", "barn owl", "barn owls"),
     "life": "A barn owl usually lives only about four years in the wild, though in a barn or a "
             "sanctuary it can reach 15."},
    {"names": ("bee", "bees", "honey bee", "honey bees", "honeybee", "honeybees"),
     "life": "A worker bee lives about six weeks in summer, when it is flying all day; a queen "
             "lives three to five years."},
    {"names": ("ant", "ants"),
     "life": "A worker ant lives a year or two; a queen can live for decades.",
     "speed": "An ant runs about 5 cm a second, which for something 5 mm long is the same as a "
             "person jogging."},
    {"names": ("butterfly", "butterflies"),
     "life": "An adult butterfly usually lives only a few weeks, though a butterfly that "
             "overwinters as an adult can live many months."},
    {"names": ("mouse", "mice"),
     "life": "A wild mouse usually lives under a year, and a pet one two to three years."},
    {"names": ("rat", "rats"),
     "life": "A wild rat usually lives about a year, and a pet rat two to three years."},
    # Farm animals, for the food question and the due date: "what does a cow eat" is a child's
    # question, and a row with names and no food fact answers it from the EATS table below. The
    # `gestation` line is the answer to "how long is a cow pregnant", which reached the human
    # fertility card on main - a year of trying and folic acid, for a cow.
    {"names": ("cow", "cows", "cattle", "dairy cow", "dairy cows"),
     "gestation": "A cow carries her calf for about 283 days, so nine months and a week - the "
                  "vet can narrow it down, and a heifer with a first calf often goes a few days "
                  "over. Signs she is close: a bagged-up udder, a slack tail end and restlessness "
                  "the day before."},
    {"names": ("sheep", "sheeps", "ewe", "ewes", "lamb", "lambs"),
     "gestation": "A sheep carries her lambs for about 147 days, so five months, and a ewe with "
                  "twins or triplets often goes a few days early. The last week she wants "
                  "watching twice a day, because a ewe in trouble at lambing goes downhill fast."},
    {"names": ("pig", "pigs", "piglet", "piglets", "sow", "sows", "boar", "boars"),
     "gestation": "A pig carries her litter for 115 days - three months, three weeks and three "
                  "days, which is the rule pig keepers use - and a litter is 8 to 12 piglets."},
    # A hen does not carry at all, so the due-date question is really the hatching one: 21 days
    # under a broody hen, and the same in an incubator.
    {"names": ("chicken", "chickens", "hen", "hens", "cockerel", "cockerels"),
     "gestation": "A hen is never pregnant: she lays an egg a day or so and the chick grows "
                  "outside her. An egg takes 21 days to hatch, under a broody hen or in an "
                  "incubator at 37.5C, turned an odd number of times a day."},
    {"names": ("goat", "goats", "billy goat", "nanny goat", "doe goat"),
     "gestation": "A goat carries her kids for about 150 days, so five months, and twins are the "
                  "common litter. Her udder fills in the last two weeks and she will look for a "
                  "corner to be alone in - that is the day to leave her quiet."},
    # A pony first, because the row is read for its names in order and "what do horses eat"
    # has to reach the horse's own food line: a row whose names begin with "pony" answers it
    # with a pony's ration instead.
    {"names": ("pony", "ponies"),
     "gestation": "A horse or pony carries her foal for about 340 days, so eleven months, and "
                  "anything from 320 to 370 is normal - which is why the vet dates it from the "
                  "covering rather than guessing. A mare foals fast, usually at night, and the "
                  "foal should be up and feeding within two hours."},
    {"names": ("horse", "horses", "mare", "mares", "foal", "foals"),
     "gestation": "A horse carries her foal for about 340 days, so eleven months, and anything "
                  "from 320 to 370 is normal - which is why the vet dates it from the covering "
                  "rather than guessing. A mare foals fast, usually at night, and the foal "
                  "should be up and feeding within two hours."},
    # Animals with a due date and no other row of their own. A dog was going to the human
    # fertility card on main, and so was a rabbit.
    {"names": ("dog", "dogs", "bitch", "bitches", "puppy", "puppies", "labrador", "spaniel"),
     "gestation": "A dog is pregnant for about 63 days, so nine weeks, and anything from 58 to 68 "
                  "is normal - the date is a window, not a day. She is usually scanned or x-rayed "
                  "around 55 days to count the pups, and she will want a quiet box a week before."},
    # no bare "doe" or "does" among the names: `_work_out_forms` stems "does" to "doe", so
    # "how long does pregnancy last" was read as a rabbit
    {"names": ("rabbit", "rabbits", "bunny", "bunnies"),
     "gestation": "A rabbit kindles about 31 days after mating, so a month - which is why a "
                  "rabbit you thought was alone can produce a litter before you have noticed she "
                  "was pregnant. Leave her alone with a nest box and do not tidy it for a few "
                  "days after the kits arrive."},
    {"names": ("guinea pig", "guinea pigs", "cavy", "cavies"),
     "gestation": "A guinea pig carries her pups for 63 to 70 days, so about nine to ten weeks, "
                  "and the litter is usually two to four - born furred, eyes open and eating "
                  "within hours."},
    {"names": ("hamster", "hamsters"),
     "gestation": "A hamster is pregnant for only 16 days, so barely over two weeks, and litters "
                  "are five to nine. The father has to come out before she gives birth, because "
                  "he will be chased and bitten once the pups are there."},
    {"names": ("ferret", "ferrets"),
     "gestation": "A ferret is pregnant for about 42 days, so six weeks, and a jill can be "
                  "delayed: if she was mated late in the year the litter waits until the spring."},
    # The zoo questions came to the human fertility card, because these animals had rows about
    # how long they live and what they eat but no due date at all. An orca had no row.
    {"names": ("orca", "orcas", "killer whale", "killer whales"),
     "gestation": "An orca carries her calf for 15 to 18 months, the longest of the dolphins, "
                  "and a calf stays with its mother for years."},
    {"names": ("donkey", "donkeys")},
    # a lizard in a tank and a polar bear on the telly are the same question: what does it eat
    {"names": ("lizard", "lizards", "bearded dragon", "leopard gecko")},
    {"names": ("polar bear", "polar bears")},
    {"names": ("greyhound", "greyhounds"),
     "speed": "A greyhound is the fastest dog, at about 70 km/h, and it reaches that in six "
             "strides from a standing start."},
    {"names": ("horse", "horses"),
     "speed": "A racehorse can reach about 70 km/h, and it can keep up a gallop for a couple of "
             "minutes rather than a few seconds."},
    {"names": ("ostrich", "ostriches"),
     "size": "The ostrich is the biggest bird: up to 2.7 metres tall and 150 kg. It cannot fly, "
             "but it runs at about 70 km/h, the fastest of any bird on land.",
     "speed": "An ostrich runs at about 70 km/h over a short distance, and 40 to 50 km/h for "
             "longer, which is the fastest of any bird on land."},
)

# The record questions, by what is asked and where: the plain one, on land, in water, or a bird.
# A line that names no place gets "any".
RECORDS = {
    ("speed", "any"): ("The peregrine falcon is the fastest animal: it reaches over 240 km/h in a "
                       "hunting dive, though a cheetah is the fastest on land at about 110 km/h."),
    ("speed", "land"): ("The cheetah is the fastest land animal: about 110 km/h, from 0 to 100 in "
                        "about three seconds, but only for 20 to 30 seconds at a time."),
    ("speed", "sea"): ("The sailfish is usually called the fastest fish, at around 100 km/h in "
                       "short bursts, though that is hard to measure and often argued about."),
    ("speed", "bird"): ("The peregrine falcon, at over 240 km/h in a dive; in level flight a swift "
                        "is the fastest, at around 110 km/h."),
    ("big", "any"): ("The blue whale is the biggest animal alive, and the biggest that has ever "
                     "lived: up to 30 metres and around 150 tonnes."),
    ("big", "sea"): ("The blue whale: up to 30 metres and around 150 tonnes, with a heart the size "
                     "of a small car and a tongue that weighs as much as an elephant."),
    ("big", "land"): ("The African elephant is the biggest land animal: a big bull is about 3 "
                      "metres at the shoulder and 6 tonnes."),
    ("big", "bird"): ("The ostrich is the biggest bird, at up to 2.7 metres and 150 kg, and it "
                      "cannot fly. The wandering albatross has the widest wingspan, about 3.5 "
                      "metres."),
    ("tall", "any"): ("The giraffe: a male reaches about 5.5 metres, and more than a third of that "
                      "is neck."),
    ("tall", "bird"): ("The ostrich, at up to 2.7 metres; the tallest flying bird is the crane, at "
                       "about 1.8 metres."),
    ("life", "any"): ("The Greenland shark, at about 400 years, lives longest of any animal with a "
                      "backbone. A giant tortoise can pass 150, and a blue whale 80 to 90."),
    ("life", "land"): ("The giant tortoise: often over 100 years, and the oldest known reached 190."),
    ("strong", "any"): ("An ant can carry 10 to 50 times its own weight, and a dung beetle can pull "
                        "over 1,000 times its own, which is the strongest for its size."),
    ("weak", "any"): ("Weight for weight, an ant carries the most: 10 to 50 times its own body "
                      "weight. A dung beetle can pull over 1,000 times its own."),
    ("danger", "any"): ("The mosquito, by a wide margin: it spreads malaria, dengue and yellow "
                        "fever, which between them kill hundreds of thousands of people a year. "
                        "It is not the bite that kills, so nets and repellent are the answer."),
}

# What a wild animal eats, which is the other half of "what do badgers eat": the garden questions
# about the animal (its bins, its setts, its holes in the lawn) are other rows, so every row here
# stands down for the words that make it a nuisance question. The hedgehog is not in the table
# because nature.py keeps its own feeding row, and a rabbit is a pet, not a wild animal.
# No "what do"/"what does" here: the reading empties the question frame before the key is
# matched, so a group that matched on the phrase scored nothing and "what do deer eat" reached no
# row at all while "what do deers eat" (a typo) did.
DIET_CUES = ("eat", "eats", "eating", "ate", "eaten", "diet", "feed", "feeds", "feeding", "fed",
             "food", "foods", "menu")
# The line has to be asking: "badgers eat the bird food" is a remark about the garden, and the
# diet table is the wrong reply to it. Every diet row also needs this to win the tie against the
# travel row keyed on the bare verb "eat" ("what do i eat in rome"), which is why the ask words are
# here and not left to the default.
# What each animal eats, by the row it belongs to. Diet is a question people ask about nearly
# every animal - "what does a lion eat" is a child's homework and a grown-up's curiosity - and the
# table above had the life span and the speed of each one but no food, so the question went to a
# search hedge. One fact per row, in the same shape as the others, and nothing is answered for an
# animal that has no line. "parrot" and "hedgehog" are left out on purpose: their food questions
# already have a feeding card with more in it than a diet list, and a second row would take it.
EATS = {
    "elephant": "Grass, leaves, bark and fruit: a big bull eats up to 150 kg of plants a day and "
                "drinks around 100 litres of water.",
    "lion": "Meat, and only meat - zebra, wildebeest, antelope and buffalo, taken by the females "
            "in a group hunt. A lion eats around 5 to 7 kg a day and can go a week without.",
    "tiger": "Meat: deer, wild pig and wild cattle, hunted alone and mostly at night. A tiger can "
             "eat up to 40 kg in one sitting and then go several days without.",
    "cheetah": "Meat, and it has to be fresh: hares, young antelope and birds, caught in a sprint "
               "and eaten quickly before a lion or a hyena takes it. A cheetah eats around 3 kg "
               "a day.",
    "giraffe": "Leaves, mostly acacia: the tongue and lips are tough enough to strip thorny twigs "
               "without harm. A giraffe eats around 34 kg of leaves a day and drinks only every "
               "few days.",
    "zebra": "Grass, almost all of it: a zebra grazes up to 16 hours a day and needs water every "
             "day or two.",
    "rhino": "Grass for the white rhino, which grazes with its head down; the black rhino browses "
             "bushes and leaves with its lip hooked round a twig. Both eat around 50 kg a day.",
    "hippo": "Grass, and almost all of it at night on land: a hippo can eat 40 kg in a night and "
             "spends the day in the water.",
    "gorilla": "Plants - leaves, shoots, stems and fruit - around 20 kg a day for a big male, "
               "with the odd insect. A mountain gorilla eats very little meat.",
    "chimpanzee": "Mostly fruit, plus leaves, seeds and insects, and now and then meat from a "
                  "monkey it has hunted, which is a group affair with a lot of noise.",
    "panda": "Bamboo, almost nothing else: 12 to 38 kg a day, because bamboo gives so little "
             "energy that a panda eats for up to 14 hours of it.",
    "koala": "Eucalyptus leaves only, and only a few species of them: a koala eats about half a "
             "kilo a day and sleeps 18 to 20 hours.",
    "kangaroo": "Grass and leaves, grazed at dawn and dusk; a kangaroo needs little water and "
                "gets most of it from the plants.",
    "whale": "Krill and small fish for a baleen whale, strained through the plates in its mouth; "
             "a toothed whale takes fish and squid.",
    "blue whale": "Krill, and up to 4 tonnes of it a day in the feeding season, strained through "
                  "the baleen plates; a blue whale eats little or nothing while it migrates.",
    "dolphin": "Fish and squid, swallowed whole or shaken apart first: a dolphin eats around 10 "
               "to 20 kg of fish a day.",
    "shark": "Fish, squid, seals and carrion, by species: a great white hunts seals, a basking "
             "shark strains plankton through its gills, and a nurse shark sucks shellfish off "
             "the seabed.",
    "octopus": "Crabs, shellfish and small fish, cracked open with its beak and pulled apart; an "
               "octopus hunts at night and can taste with its arms.",
    "penguin": "Fish, squid and krill, caught by diving: an emperor penguin can dive to 500 "
               "metres and stay under for 20 minutes.",
    "tortoise": "Leaves, weeds and flowers - dandelion, plantain, clover, bindweed - for a "
                "Mediterranean tortoise, with no fruit and no dog food. A pet tortoise gets a "
                "pile about the size of its shell, once a day.",
    "crocodile": "Meat: fish, birds, turtles and anything that comes to drink, taken in one "
                 "lunge and swallowed in pieces. A crocodile can go months between meals.",
    "eagle": "Meat: rabbits, fish, birds or carrion, by species, taken with the talons and torn "
             "up at a perch.",
    "ostrich": "Mostly plants - grass, seeds, leaves and flowers - with the odd insect or "
               "lizard; an ostrich has no teeth and swallows small stones to grind its food.",
    "horse": "Grass or hay, most of the day: a horse eats about 2% of its body weight a day, so "
             "10 kg of hay for a 500 kg horse, in small amounts through the day, with water "
             "always available.",
    "greyhound": "A complete dog food, and less than its size suggests: a retired racer of about "
                 "30 kg eats 400 to 500 g a day, split into two meals.",
    "bee": "Nectar and pollen: the adults live on nectar, and the larvae on pollen and honey. A "
           "colony can bring in 20 to 30 kg of pollen in a year.",
    "ant": "Almost anything - other insects, seeds, nectar and the honeydew off aphids. Some "
           "ants farm aphids for it, and some grow fungus on leaves instead.",
    "cow": "Grass and hay, and a lot of it: a dairy cow eats around 20 kg of dry matter a day, "
           "which is most of a bale of hay, and drinks 60 to 100 litres of water.",
    "sheep": "Grass, mostly, plus the clover and weeds in it: a sheep eats around 2 kg of dry "
             "matter a day and spends 8 to 10 hours of it grazing.",
    "pig": "Almost anything, which is what an omnivore means: a pig eats 2 to 3 kg of feed a day "
           "and roots for grubs, roots and fallen fruit with a nose built to dig. It cannot "
           "sweat, so it wallows to cool down. Kitchen scraps and any meat are illegal to feed a "
           "pig in the UK, and that rule is what keeps swine fever out. A wild boar, the same "
           "animal, lives on roots, acorns, grubs and carrion over a much bigger range.",
    "chicken": "Layers pellets or mash as the base, about 120 g a day per hen, plus grass, weeds, "
               "insects and vegetable scraps; grit and crushed oyster shell keep the eggshells "
               "hard. Bread and corn are treats rather than feed, and avocado, citrus peel, salt "
               "and anything mouldy are not for them at all.",
    "goat": "Browse first, not grass: brambles, hedge, leaves, bark, weeds and thistles, then hay "
            "- about 2 kg of hay a day plus a mineral lick and water. A goat has a stomach for "
            "roughage, so rich grass or a lot of grain makes it ill, and it will strip a garden "
            "to the fence line given the chance.",
    "pony": "Grass and hay, and less of it than people think: a 300 kg pony needs about 6 kg of "
            "hay a day in dry matter, plus water and a salt lick, and a native pony on good grass "
            "needs nothing else - which is why a fat pony is the one that gets laminitis in "
            "spring. Hard feed is for a pony in work, not for one standing in a field.",
    "donkey": "Straw and hay, and less than a pony of the same size: a donkey has a slower "
              "digestive system and gets fat on good grass, so the work is keeping it thin with "
              "coarse hay and a bare paddock rather than feeding it up.",
    "lizard": "Insects for nearly all of them - crickets, locusts and mealworms, dusted with a "
              "calcium powder - and the green ones take leaves and veg instead. It needs the "
              "right heat to digest at all, so the lamp matters as much as the food.",
    "polar bear": "Seals, and mostly the ringed seal: a polar bear waits at a breathing hole and "
                  "takes the seal as it surfaces, then eats the blubber first. It can go days "
                  "between meals and swims long distances between patches of ice.",
}

# Four of these animals are also dinner, and one shared avoid list cannot hold both questions:
# "what do chickens eat" has to answer and "is it ok to eat pink chicken" must not, and the words
# that tell them apart are the eating of the bird rather than the feeding of it. So the fence is
# per animal, and it stands the row down rather than reaching for a second row that would tie.
EATS_ITSELF = {
    "chicken": ("ok to eat", "safe to eat", "still ok", "eat it", "to eat", "can i eat", "pink",
                "raw", "cooked", "undercooked", "dry", "left out", "out of date", "use by",
                "in the fridge", "in the freezer", "in the oven", "how long", "how many people",
                "whole", "roast", "recipe", "cook", "cooking", "thigh", "thighs", "breast",
                "breasts", "wing", "wings", "nugget", "nuggets", "stock", "soup", "bone", "bones",
                "gravy", "sandwich", "curry", "pie", "calories", "protein", "thaw", "dinner",
                "for tea", "for sunday", "feed my", "my dog", "my cat"),
    "hen": ("ok to eat", "safe to eat", "still ok", "to eat", "pink", "raw", "cooked", "roast",
            "how many people", "whole", "in the oven", "how long", "how many eggs", "laying",
            "stop laying", "not laying", "broody", "sick", "ill", "unwell", "not eating"),
    "pig": ("pork", "bacon", "ham", "gammon", "sausage", "sausages", "chop", "chops", "belly",
            "crackling", "roast", "in the oven", "how long", "ok to eat", "safe to eat", "pink"),
    "goat": ("milk", "cheese", "curry", "in the oven", "how long", "ok to eat", "safe to eat",
             "get my goat", "got my goat", "scapegoat", "goatee"),
    "pony": ("riding", "ride", "livery", "tack", "saddle", "how tall", "height", "shoes",
             "race", "racing", "bet", "betting"),
}

# The words that make a line a question about food rather than about the animal itself. "what do"
# and "what does" are not here: "what do ants do in winter" is about winter, and the animal plus
# the asking word was already two parts of a key.
EAT_CUES = ("eat", "eats", "eaten", "eating", "food", "diet", "fed", "feed", "feeding",
            "hunt", "hunts", "hunting", "prey")

# The asking words, so an animal plus a food word is a question and not a statement ("the cat ate
# the mouse").
EAT_ASK = ("what", "whats", "what's", "do", "does", "did", "should", "which", "how", "is",
           "are", "want to know", "tell me", "wondering")

DIET_ASK = ("what", "whats", "what's", "should", "do", "does", "did", "which", "how", "any",
            "is", "are", "best", "good", "feed", "never", "not")
DIET_AVOID = ("bin", "bins", "bin bag", "bin bags", "rubbish", "wheelie", "tip over", "knock over",
              # not "deter": "deer" is one slip from it, and the slip reader then stood every
              # diet row down for the commonest way anybody asks about a deer
              "get rid", "keep away", "keep off", "keep out", "stop them", "repel",
              "traps", "trap", "poison", "shoot", "shooting", "licence", "protected",
              "lawn", "holes in the lawn", "holes in my lawn", "digging", "dig up", "dug up",
              "setts", "sett", "nest", "nests", "in my loft", "in the loft", "in the attic",
              "in my roof", "in the shed", "in my house", "in the kitchen", "droppings", "mice in",
              "rats in", "we have mice", "we have rats", "how do i", "how to get")

# An animal that lives with somebody is the pet rows' question, how much to feed one is a portion
# question this table has no numbers for, and a food-safety line is the keeping rows' question:
# "is it safe to eat chicken that was left out" carries the word eat and a food, not a diet.
EAT_AVOID = DIET_AVOID + ("my dog", "my cat", "my puppy", "my kitten", "my rabbit", "my guinea",
                          "my hamster", "my horse", "my pony", "my tortoise", "my snake",
                          "my beardie", "puppy", "kitten", "how much", "how often",
                          "how many times", "portion", "portion size", "grams", "per day food",
                          "safe to eat", "left out", "leftover", "leftovers", "reheat",
                          "use by", "gone off", "out of date", "still ok")


DIETS = (
    (("fox", "foxes"), DIET_CUES,
     "Almost anything, and mostly things we leave out: worms, beetles, slugs and grubs out of a "
     "lawn, small rodents, birds and their eggs, fruit and berries, and every kind of food waste - "
     "which is why a bin bag left out is the same meal, easier to reach. A cat is not on that list: "
     "an adult cat can look after itself and a fox backs off."),
    (("badger", "badgers"), DIET_CUES,
     "Earthworms are most of it: a badger can eat well over a hundred in a night, which is why a "
     "lawn full of small conical holes is badger work rather than a pest. The rest is beetles and "
     "grubs, slugs, roots, windfall fruit, and now and then eggs or a chick, plus anything a bin "
     "bag offers."),
    (("squirrel", "squirrels", "grey squirrel", "grey squirrels"), DIET_CUES,
     "Seeds and nuts first - acorns, hazelnuts, beech mast, sunflower seeds - then fungi, buds, "
     "shoots and fruit, and a bird feeder is the same food in an easier place. In autumn a grey "
     "squirrel buries thousands of nuts one at a time and remembers where most of them are."),
    (("owl", "owls", "tawny owl", "barn owl", "barn owls", "tawny owls"), DIET_CUES,
     "Small mammals: a tawny owl lives on mice, voles and shrews, with the odd small bird, frog or "
     "beetle, and a barn owl is almost all voles. It swallows the prey whole and coughs up the fur "
     "and bones as a pellet, which is what you find under a roost."),
    (("deer", "deers", "roe deer", "muntjac", "fallow deer"), DIET_CUES,
     "Grass, leaves, shoots, buds, ivy and brambles, and fruit in autumn - a deer browses at the "
     "height of a hedge rather than grazing it, which is why the roses are stripped to a line and "
     "the buds on your apple tree go first. A muntjac also eats bluebells and birds' eggs."),
    (("mouse", "mice", "house mouse", "house mice", "field mouse", "field mice"), DIET_CUES,
     "Seeds and grain mostly, so a kitchen is a windfall: cereals, crumbs, nuts, chocolate, pet "
     "food, and the odd insect. A house mouse eats only about 3g a day and drinks very little, "
     "which is why a small spill keeps a family going."),
    (("rat", "rats", "brown rat", "brown rats"), DIET_CUES,
     "Almost anything, about 25 to 30g a day, plus water: grain, fruit, scraps, pet food, eggs, "
     "even soap and candles. That range is why rat baiting works with something they already "
     "like, and why the bin and the bird feeder are the two places they go first."),
    (("frog", "frogs", "toad", "toads"), DIET_CUES,
     "Moving prey it can fit in its mouth: slugs, snails, worms, beetles, flies, spiders and "
     "caterpillars, caught with a sticky tongue in about a tenth of a second. Tadpoles eat algae "
     "and plant matter instead, so a pond with a few leaves in it feeds them."),
    (("bat", "bats", "pipistrelle", "pipistrelles"), DIET_CUES,
     "Insects, caught on the wing by echolocation: a single pipistrelle eats around 3,000 midges "
     "and mosquitoes in a night, which is why bats over a garden mean fewer bites. Fruit bats in "
     "the tropics eat fruit and nectar instead."),
    (("snake", "snakes", "grass snake", "grass snakes", "adder", "adders"), DIET_CUES,
     "Whole prey, swallowed in one: a grass snake takes frogs, toads, newts, small fish, mice and "
     "the odd bird's egg, and an adder takes voles, mice, lizards and young birds. It can go days "
     "or weeks between meals, then sit still somewhere warm to digest."),
    (("seagull", "seagulls", "gull", "gulls", "herring gull", "herring gulls"), DIET_CUES,
     "Anything it can win: fish and shellfish, worms and insects off a ploughed field, other "
     "birds' eggs and chicks, chips, and whatever the bin has. A herring gull will drop a shell "
     "on a car park to break it, which is the same trick, not a taste for cars."),
    (("pidgeon", "pidgeons", "pigeon", "pigeons", "wood pigeon", "wood pigeons"),
     DIET_CUES,
     "Seeds and grain, then leaves, buds, berries and brassicas - a wood pigeon will strip a "
     "cabbage row - and the feral pigeons in town live on scraps and bread. Bread is not good for "
     "any of them: peas, oats or bird seed are the better thing to put down."),
    (("duck", "ducks", "mallard", "mallards"), DIET_CUES,
     "Water plants and their seeds, grain, grass, insects, snails and the odd small fish. Bread is "
     "the thing to stop giving them: it fills a duck up without feeding it, and it fouls the water. "
     "Oats, peas, sweetcorn or bird seed do the job and float while they eat."),
    (("heron", "herons", "grey heron", "grey herons"), DIET_CUES,
     "Fish and frogs first, then eels, water voles, insects, and in spring ducklings and moorhen "
     "chicks. A heron hunts by standing still in the shallows and striking, so a pond with a "
     "planted edge and deeper water gives the fish somewhere to hide."),
    (("swan", "swans", "mute swan", "mute swans"), DIET_CUES,
     "Water plants pulled up from the bottom, plus grass, grain and the odd insect or snail. Bread "
     "is the wrong food: it is empty of much they need and it fouls the water, so grain, oats or "
     "shredded greens are the better offering."),
    (("butterfly", "butterflies", "caterpillar", "caterpillars"), DIET_CUES,
     "Two different diets in one life: a caterpillar eats leaves, and each kind wants its own "
     "plant - stinging nettles for peacock and small tortoiseshell, holly for holly blue, "
     "buckthorn for brimstone - while the butterfly drinks nectar from flowers such as lavender, "
     "buddleia and sedum."),
    (("starling", "starlings"), DIET_CUES,
     "Insects and worms from lawns and dung, then fruit, seeds and scraps; in autumn they switch "
     "to berries and orchards, which is when the murmurations gather before roosting. A starling "
     "will also take fat balls and kitchen scraps from a feeder."),
    (("robin", "robins"), DIET_CUES,
     "Insects, worms, spiders and caterpillars for most of the year, then berries and fruit in "
     "winter when the ground is hard. That is the moment to put out mealworms, suet and a few "
     "sultanas, and a robin will take them from a hand within a couple of weeks."),
    (("magpie", "magpies"), DIET_CUES,
     "Insects, carrion, seeds and fruit, plus eggs and nestlings in spring, which is why small "
     "birds mob one and why a garden with a magpie nesting goes quiet for a few weeks. It also "
     "takes scraps and pet food left outside."),
)

# The animals on a farm and at the zoo: the same diet question, and the same cues, but each with
# a life of its own outside the answer. A guinea pig is not a pig, counting sheep is how people get
# to sleep, chicken pox is a childhood illness and a chicken dinner is dinner, so every row here
# carries its own fence on top of `DIET_AVOID` rather than sharing one list.
FARM_DIETS = (
    (("horse", "horses", "pony", "ponies"), DIET_CUES,
     "Grass and hay, roughly 2 per cent of its body weight a day in dry matter: a 500 kg horse "
     "gets through about 10 kg of hay plus water and a salt lick, and hard feed such as oats or "
     "barley is for work rather than the diet. Lush spring grass holds enough sugar to bring on "
     "laminitis, so a fat pony is the one to ration.",
     ("race", "racing", "racehorse", "bet", "betting", "each way", "riding", "livery", "tack",
      "shoe", "shoes", "height", "how tall")),
    (("cow", "cows", "cattle", "heifer", "heifers", "bull", "bulls"), DIET_CUES,
     "Grass and silage, in bulk: a dairy cow eats 50 to 60 kg of fresh grass or silage a day and "
     "drinks 60 to 100 litres of water. The rumen and its bugs are what break the grass down, "
     "which is why a little grain is a supplement and not a diet. Kitchen scraps are illegal to "
     "feed to farm animals in the UK, and have been since 2001.",
     ("mad cow", "cow pat", "cow pats", "cow poo", "milk", "milking", "dairy", "cowbell",
      "beef", "steak", "steaks", "mince", "brisket", "roast", "in the oven", "how long",
      "ok to eat", "safe to eat", "pink", "protein", "calories")),
    (("pig", "pigs", "piglet", "piglets", "sow", "boar"), DIET_CUES,
     "Almost anything, which is what an omnivore means: a pig eats 2 to 3 kg of feed a day, and "
     "roots for grubs, roots and fallen fruit with a nose built to dig. It cannot sweat, so it "
     "wallows to cool down. Kitchen scraps and any meat are illegal to feed to a pig in the UK, "
     "and that rule is what keeps swine fever out.",
     ("guinea", "guinea pig", "guinea pigs", "piggy bank", "pig out", "pig out on", "guinea-pig",
      "pork", "bacon", "ham", "gammon", "sausage", "sausages", "chop", "chops", "belly",
      "crackling", "roast", "in the oven", "how long", "ok to eat", "safe to eat", "pink")),
    (("sheep", "ewe", "ewes", "lamb", "lambs"), DIET_CUES,
     "Grass, and mostly grass: a ewe eats about 2 per cent of her body weight in dry matter a "
     "day, so 1.5 to 2 kg, plus a mineral lick and clean water. Late pregnancy wants more, and "
     "very rich spring grass or a sudden feed change is what brings on twin lamb disease and "
     "bloat, so any change is made over a week.",
     ("count", "counting", "counted", "sheepskin", "wool", "sheepdog", "sheep dog", "bollard",
      "black sheep", "lamb", "lamb chop", "lamb chops", "roast", "ok to eat", "safe to eat",
      "pink", "in the oven", "how long", "shoulder", "leg of")),
    (("chicken", "chickens", "hen", "hens", "cockerel", "cockerels"), DIET_CUES,
     "Layers pellets or mash as the base, about 120 g a day per hen, plus grass, weeds, insects "
     "and vegetable scraps; grit and crushed oyster shell keep the eggshells hard. Bread, pasta "
     "and corn are treats rather than feed, and avocado, citrus peel, salt and anything mouldy "
     "are not for them at all.",
     ("pox", "chicken pox", "chickenpox", "cook", "cooked", "cooking", "raw", "recipe", "roast",
      "dinner", "thigh", "thighs", "breast", "breasts", "wing", "wings", "nugget", "nuggets",
      "stock", "soup", "bone", "bones", "gravy", "sandwich", "curry", "pie",
      # the bird is dinner far more often than it is a hen in a run: a line about eating it,
      # cooking it, keeping it or serving it is another row's
      "ok to eat", "safe to eat", "still ok", "eat it", "to eat", "can i eat", "pink", "dry",
      "left out", "out of date", "use by", "in the fridge", "in the freezer", "in the oven",
      "how long", "how many people", "whole", "for tea", "for dinner", "for sunday", "feed my",
      "dog", "cat", "puppy", "kitten", "calories", "protein", "thaw")),
    # "kid" is a young goat and also every person's word for their children, and the bare word
    # took the people: "what should i feed my kids for lunch", "what do kids like to eat" and
    # "how much should i feed my kids" were all answered with brambles and hay. The goat's kid
    # is only read when the line says goat.
    (("goat", "goats", "kid goat", "kid goats", "baby goat", "baby goats", "young goat",
      "young goats", "billy goat", "nanny goat"), DIET_CUES,
     "Browse first, not grass: brambles, hedge, leaves, bark, weeds and thistles, then hay - "
     "about 2 kg of hay a day plus a mineral lick and water. A goat is a browser with a stomach "
     "for roughage, so rich grass or a lot of grain makes it ill, and it will strip a garden to "
     "the fence line given the chance.",
     ("get my goat", "got my goat", "goatee", "scapegoat", "kids party", "goat curry",
      "goat cheese", "goats cheese", "milk", "in the oven", "how long", "ok to eat")),
    (("lion", "lions", "lioness", "lionesses"), DIET_CUES,
     "Meat, and plenty of it: a lion averages 5 to 7 kg a day, taken from zebra, wildebeest, "
     "buffalo and smaller prey, and it can go several days between kills and then eat 30 kg at "
     "one sitting. The lionesses do most of the hunting, and the pride shares the carcass.",
     ("lion bar", "lions club", "mane", "roar", "roaring", "tattoo")),
    (("elephant", "elephants"), DIET_CUES,
     "Plants, in enormous quantity: an adult elephant eats 100 to 150 kg of grass, leaves, bark "
     "and fruit a day and drinks 100 to 200 litres of water, so it spends 16 hours a day feeding "
     "and travels to find it. Its dung is a seed bank, and a forest grows along the paths it "
     "makes.",
     ("white elephant", "elephant in the room", "ivory", "tusk", "tusks", "pregnant", "pregnancy")),
    (("giraffe", "giraffes"), DIET_CUES,
     "Acacia leaves, browsed four to five metres up: a giraffe eats up to 45 kg of leaves a day "
     "with a 45 cm tongue and lips tough enough for the thorns, and it drinks only every few days "
     "because the leaves hold so much water. It spreads its front legs to reach a waterhole.",
     ("neck", "how tall", "height", "tall")),
)

# The curiosity questions: the animal, the words that ask it, and the answer. One Entry per row,
# so each answer is only reached by a line that names the animal and asks this about it.
CURIOSITIES = (
    (("bat", "bats"), ("blind", "blindness", "see", "seeing", "sight"),
     "Bats are not blind: they see about as well as a cat in dim light. What makes them special "
     "is echolocation, squeaks too high to hear that bounce back and tell them where things are "
     "in the dark."),
    (("zebra", "zebras"), ("stripe", "stripes", "striped"),
     "Nobody knows for certain, and the best evidence points at flies and heat rather than "
     "camouflage: the stripes seem to confuse biting flies and help the animal lose heat, and "
     "the pattern on each zebra is as individual as a fingerprint."),
    (("penguin", "penguins"), ("north pole", "arctic", "south pole", "antarctic", "where",
                               "where do penguins live", "which pole"),
     "Penguins live in the southern half of the world: Antarctica, and the coasts of South "
     "America, Africa, Australia and New Zealand. There are none at the North Pole; the birds "
     "there are puffins, which are not penguins."),
    (("penguin", "penguins"), ("hold their breath", "hold its breath", "breath", "dive", "diving",
                              "deep", "swim", "swimming"),
     "An emperor penguin can hold its breath for around 20 minutes and dive past 500 metres; "
     "most dives are one to five minutes and less than 100 metres."),
    (("penguin", "penguins"), ("warm", "cold", "freeze", "survive", "huddle", "huddles"),
     "Four things: a layer of blubber, feathers packed so tightly that water never reaches the "
     "skin, feet and flippers with a heat-exchange that keeps the blood warm, and huddling. In a "
     "huddle each bird takes a turn on the freezing outside."),
    (("ant", "ants"), ("winter", "cold", "survive", "survives", "hibernate", "hibernation"),
     "They slow down and go deep: a colony moves to the lowest, frost-free part of the nest, "
     "clusters together, and eats stored food, with the queen in the middle. They do not truly "
     "hibernate, they just keep still until it warms up."),
    (("ant", "ants"), ("strong", "stronger", "strength", "carry", "lift", "how much can"),
     "An ant carries 10 to 50 times its own body weight, and holds on with feet that grip "
     "smooth surfaces, which is why one can walk off with a whole crisp."),
    (("octopus", "octopuses", "octopi"), ("heart", "hearts", "how many"),
     "Three: two pump blood through the gills and one pumps it round the rest of the body. "
     "Their blood is blue, because it uses copper rather than iron to carry oxygen."),
    (("octopus", "octopuses", "octopi"), ("arm", "arms", "leg", "legs", "how many"),
     "Eight arms, and two rows of suckers on each, about 2,000 suckers in all. Each one can "
     "taste what it touches."),
    # "why do fish need oxygen" is the same question as "how do fish breathe underwater", and it
    # was answered with the rod licence, because "fish" plus "need" is that entry's whole key.
    (("fish", "fishes", "goldfish"), ("breathe", "breathing", "gills", "underwater", "under water",
                                      "oxygen", "need oxygen", "oxygen in the water", "air"),
     "They take oxygen out of the water instead of the air: water goes in at the mouth, passes "
     "over the gills, and the gills pull the oxygen out and pass the carbon dioxide back. A few "
     "fish, like bettas and gouramis, can also gulp air from the surface."),
    (("fish", "fishes"), ("feel pain", "pain", "suffer", "suffering"),
     "The evidence says probably yes: fish have nerves and opioid receptors, and they learn to "
     "avoid a place where they were hurt. Scientists argued about it for years, and it is why "
     "handling rules for angling have tightened."),
    (("dog", "dogs", "puppy", "puppies"), ("wag", "wagging", "wags", "tail", "tails"),
     "It is a signal, and the tail is not always saying the same thing: a loose, wide wag with a "
     "loose body means happy, a fast low wag can mean nerves, and a stiff high wag is usually a "
     "warning. Studies find a wag that swings more to the dog's right goes with a friendly "
     "meeting."),
    (("spider", "spiders"), ("how many legs", "legs", "eyes", "how many eyes"),
     "Spiders have eight legs and usually eight eyes, in rows across the front of the head. They "
     "have silk glands in the abdomen and spin the web out with their back legs."),
    (("bat", "bats"), ("sleep", "sleeps", "hibernate", "hibernation", "upside down"),
     "Bats sleep upside down, hanging by their feet, and many hibernate through the winter that "
     "way. Hanging upside down means a fall is a drop of a few centimetres, and taking off is "
     "just letting go."),
    (("beaver", "beavers"), ("dam", "dams", "why", "build"),
     "A beaver builds a dam to hold the water deep enough that the entrance to its lodge is under "
     "the surface, which keeps out foxes, wolves and bears. The pond also means it can swim to "
     "food in winter instead of walking over land."),
    (("swallow", "swallows", "swift", "swifts"), ("sleep", "sleeps", "fly", "flying", "land"),
     "Swifts sleep on the wing, climbing to where they can glide slowly for hours at a time. "
     "Some stay airborne for months, and they only land to nest."),
    (("chameleon", "chameleons"), ("change colour", "colour", "color", "why"),
     "They stretch or squeeze layers of pigment cells in the skin. It is mostly mood and "
     "temperature rather than camouflage: a calm chameleon is often green, and a cross one goes "
     "bright or dark."),
    (("elephant", "elephants"), ("trunk", "why", "how many bones"),
     "An elephant's trunk has no bones at all and around 40,000 muscles, which is why it can pick "
     "up a single peanut or lift a tree. Elephants greet by touching trunks."),
    (("hibernate", "hibernates", "hibernating", "hibernation"),
     ("why", "how", "animals", "bear", "bears", "hedgehog", "survive", "winter"),
     "Hibernation is a way of getting through a season with no food: the animal's temperature, "
     "heart rate and breathing drop, and it lives off the fat it laid down in autumn. A bear's "
     "heart can slow from 40 beats a minute to 8, and a hedgehog turns almost cold to the touch. "
     "A bat or a hedgehog woken in winter has spent a lot of energy for nothing, so leave one be."),
)


# What people call an animal, as data: the word for its young, for its crowd, and for each
# parent. "what is a baby goat called" and "what is a group of crows called" had nothing in the
# knowledge base at all - both were a search hedge - while the words themselves (kid, murder,
# vixen) are the everyday facts people ask about while reading to a child or answering homework.
# One row per animal, and the reply is built from the row rather than written out, so adding a
# word is adding a value here: the sentence a line gets is always "A young <animal> is a <word>",
# which is the name first and nothing else claimed about it.
WORD_ROWS = (
    {"names": ("goat", "goats"), "young": "kid", "female": "doe", "male": "buck",
     "group": "herd"},
    {"names": ("cow", "cows", "cattle"), "young": "calf", "female": "cow", "male": "bull",
     "group": "herd"},
    {"names": ("sheep", "ewe", "ewes"), "young": "lamb", "female": "ewe", "male": "ram",
     "group": "flock"},
    {"names": ("pig", "pigs"), "young": "piglet", "female": "sow", "male": "boar",
     "group": "herd"},
    {"names": ("horse", "horses"), "young": "foal", "female": "mare", "male": "stallion",
     "group": "herd"},
    {"names": ("donkey", "donkeys"), "young": "foal", "group": "herd"},
    {"names": ("dog", "dogs"), "young": "puppy", "female": "bitch", "male": "stud",
     "group": "pack"},
    {"names": ("cat", "cats"), "young": "kitten", "female": "queen", "male": "tom",
     "group": "clowder"},
    {"names": ("chicken", "chickens", "hen", "hens"), "young": "chick", "female": "hen",
     "male": "cockerel", "group": "flock"},
    {"names": ("duck", "ducks"), "young": "duckling", "female": "duck", "male": "drake",
     "group": "raft"},
    {"names": ("goose", "geese"), "young": "gosling", "group": "gaggle"},
    {"names": ("swan", "swans"), "young": "cygnet", "female": "pen", "male": "cob",
     "group": "bevy"},
    {"names": ("turkey", "turkeys"), "young": "poult", "group": "rafter"},
    {"names": ("pigeon", "pigeons"), "young": "squab", "group": "flock"},
    {"names": ("crow", "crows"), "group": "murder"},
    {"names": ("raven", "ravens"), "group": "unkindness"},
    {"names": ("owl", "owls"), "young": "owlet", "group": "parliament"},
    {"names": ("eagle", "eagles"), "young": "eaglet", "group": "convocation"},
    {"names": ("fox", "foxes"), "young": "cub", "female": "vixen", "male": "dog",
     "group": "skulk"},
    {"names": ("wolf", "wolves"), "young": "cub", "group": "pack"},
    {"names": ("deer",), "young": "fawn", "female": "doe", "male": "stag", "group": "herd"},
    {"names": ("rabbit", "rabbits"), "young": "kit", "group": "colony"},
    {"names": ("hare", "hares"), "young": "leveret", "group": "husk"},
    {"names": ("mouse", "mice"), "young": "pup", "group": "mischief"},
    {"names": ("rat", "rats"), "young": "pup", "group": "mischief"},
    {"names": ("squirrel", "squirrels"), "young": "kitten", "group": "scurry"},
    {"names": ("hedgehog", "hedgehogs"), "young": "hoglet"},
    {"names": ("lion", "lions"), "young": "cub", "group": "pride"},
    {"names": ("tiger", "tigers"), "young": "cub", "group": "streak"},
    {"names": ("bear", "bears"), "young": "cub", "group": "sleuth"},
    {"names": ("elephant", "elephants"), "young": "calf", "group": "herd"},
    {"names": ("kangaroo", "kangaroos"), "young": "joey", "group": "mob"},
    {"names": ("camel", "camels"), "young": "calf", "group": "caravan"},
    {"names": ("seal", "seals"), "young": "pup", "group": "colony"},
    {"names": ("penguin", "penguins"), "young": "chick", "group": "waddle"},
    {"names": ("ostrich", "ostriches"), "young": "chick", "group": "flock"},
    {"names": ("bat", "bats"), "young": "pup", "group": "colony"},
    {"names": ("frog", "frogs"), "young": "tadpole", "group": "army"},
    {"names": ("snake", "snakes"), "young": "hatchling", "group": "nest"},
    {"names": ("turtle", "turtles", "tortoise", "tortoises"), "young": "hatchling",
     "group": "bale"},
    {"names": ("spider", "spiders"), "young": "spiderling", "group": "cluster"},
    {"names": ("bee", "bees"), "young": "larva", "group": "colony"},
    {"names": ("ant", "ants"), "young": "larva", "group": "colony"},
    {"names": ("butterfly", "butterflies"), "young": "caterpillar",
     "group": "kaleidoscope"},
    {"names": ("fish", "fishes"), "young": "fry", "group": "shoal"},
    {"names": ("whale", "whales"), "young": "calf", "group": "pod"},
    {"names": ("dolphin", "dolphins"), "young": "calf", "group": "pod"},
)

# The words that ask which of those it is. The animal is the key's other half, and the ask below
# is what makes a line a question about a word: "how do i look after a baby goat" names a baby and
# a goat and wants care, not vocabulary, so the name question has to be there too.
_WORD_CUES = {
    "young": ("baby", "young", "newborn"),
    "group": ("group", "collective noun", "bunch", "gathering"),
    "female": ("female", "girl", "lady", "mother", "mum"),
    "male": ("male", "boy", "man", "father", "dad"),
}
_WORD_ASK = ("called", "call", "word for", "name for", "what is", "whats", "what's",
             "what do you", "which word", "term for", "collective noun")
# Anything asking how to keep, feed, buy or look after the animal is another row's question, and a
# line about a sick or a pregnant one is nobody's here.
# What the line is about instead of the word, when it names an animal the same way the word
# questions do ("baby rabbits", "young rabbits"). Every one of these is a question the diet, the
# care or the lifespan entry answers, and the word entry has nothing to say to it: "what do baby
# rabbits eat" was answered "A young rabbit is a kit" where the hay card had it right (just-heron,
# PR #9005). The animal is still read, so the diet card is found through it as before.
_WORD_AVOID = ("look after", "care for", "care of", "feed", "fed", "feeding", "eat", "eats",
               "eating", "ate", "diet", "food", "what to feed", "how much",
               "cost", "price", "buy", "adopt", "keep", "keeping", "train", "vet", "pregnant",
               "sick", "ill", "how long", "how many babies", "live", "lives", "lifespan",
               "how do i", "should i")
_WORD_SENTENCE = {
    "young": "A young {one} is {article} {word}.",
    "group": "A group of {many} is {article} {word}.",
    "female": "A female {one} is {article} {word}.",
    "male": "A male {one} is {article} {word}.",
}


def _article(word):
    """A or an, from the letter the word starts with: "an unkindness", "a murder"."""
    return "an" if str(word)[:1].lower() in "aeiou" else "a"


def _line(understood):
    """The repaired line, lower case, with a space at each end, for a whole-word search."""
    text = understood.get("plain") or understood.get("clean") or ""
    return " " + str(text).lower() + " "


def _named(understood, rows=ANIMALS):
    """The animal row the line names, or None.

    The longest matching name wins, so "blue whale" is read as the blue whale and not as the
    whale row, and "african elephant" as the elephant.
    """
    text = _line(understood)
    found, best = None, ""
    for row in rows:
        for name in row["names"]:
            if len(name) > len(best) and re.search(r"\b" + re.escape(name) + r"\b", text):
                found, best = row, name
    return found


def _names_with(fact, rows=ANIMALS):
    """Every animal name whose row has this fact, for an entry's key."""
    return tuple(name for row in rows if row.get(fact) for name in row["names"])


def _the_word(kind):
    """The word for this kind of name, from the row the line names, or None.

    The reply is the row's value in one sentence, so no phrasing is written twice and a row that
    lacks the fact ("a hare has no word for a male here") passes the line on rather than guessing.
    """
    def reply(memory, understood):
        row = _named(understood, WORD_ROWS)
        word = row.get(kind) if row else None
        if not word:
            return None
        names = row["names"]
        many = names[1] if len(names) > 1 else names[0] + "s"
        return _WORD_SENTENCE[kind].format(one=names[0], many=many, word=word,
                                           article=_article(word))
    return reply


def _fact(fact):
    """A reply from the animal row the line names, or None when the row does not have it."""
    def reply(memory, understood):
        row = _named(understood)
        return row.get(fact) if row else None
    return reply


def _eats(memory, understood):
    """The food for the animal the line names, or None when its row has no line about food."""
    row = _named(understood)
    if not row:
        return None
    text = _line(understood)
    for name in row["names"]:
        fence = EATS_ITSELF.get(name)
        if fence and any(word in text for word in fence):
            # the line is about eating the animal, keeping it, or riding it, which is another
            # row's question or nobody's: the diet card would be a confident wrong answer
            return None
        if name in EATS:
            return EATS[name]
    return None


def _record(memory, understood):
    """The record the line asks about: what it is the most of, and where."""
    text = _line(understood)
    where = "any"
    if re.search(r"\bbird|birds\b", text):
        where = "bird"
    elif re.search(r"\b(fish|sea|ocean|water)\b", text):
        where = "sea"
    elif re.search(r"\b(land|on land)\b", text):
        where = "land"
    if re.search(r"\b(longest lived|longest living|longest-lived|oldest|longest|lives the longest"
                 r"|live the longest)\b", text):
        what = "life"
    elif re.search(r"\b(fastest|quickest|speed)\b", text):
        what = "speed"
    elif re.search(r"\btall\b|\btallest\b", text):
        what = "tall"
    elif re.search(r"\b(strongest|weakest)\b", text):
        what = "strong" if "strong" in text else "weak"
    elif re.search(r"\b(dangerous|deadliest|kill)\b", text):
        what = "danger"
    else:
        what = "big"
    return RECORDS.get((what, where)) or RECORDS.get((what, "any"))


def _curiosity(animal, cue, reply, avoid=(), bias=0, ask=()):
    """One Entry per curiosity row, keyed by the animal and the words that ask it."""
    return entry("animal-" + re.sub(r"[^a-z0-9]+", "-", animal[0] + "-" + cue[0]),
                 (animal, cue), reply, avoid=avoid, bias=bias, ask=ask)


ENTRIES = [
    # How long it lives. The second part is the words that make it a question about a life span
    # and not another "how long" question ("how long can a penguin hold its breath" is its own
    # row below, and the word "live" is what keeps them apart).
    entry("animal-lifespan",
          (_names_with("life"),
           ("live", "lives", "lived", "lifespan", "life span", "life expectancy",
            "how old do", "how old can", "how many years")),
          _fact("life")),
    # How long it is pregnant. The names are only the animals with a `gestation` line, so a line
    # about an animal with no due date passes on rather than reaching a card about something
    # else, and a human pregnancy is not this row at all.
    entry("animal-gestation",
          (_names_with("gestation"),
           ("pregnant", "pregnancy", "gestation", "how long is a", "how long are", "how long is my",
            "how long do", "how many days", "how many weeks", "how many months", "due date",
            "when is she due", "when will she", "how far along", "give birth", "in pup",
            "is due", "due date", "due any day", "due next week", "due in", "due soon",
            "when is my", "when will my",
            "in lamb", "in foal", "in kid", "expecting", "kindle", "farrow", "whelp", "foal")),
          _fact("gestation"),
          # a line about cooking the animal, or about the food in the fridge, is the kitchen's
          # question: "how long do i roast a whole chicken" was answered "A hen is never
          # pregnant", and so were the cooking weights on the memory tests
          avoid=("cook", "cooking", "cooked", "roast", "roasted", "roasting", "bake", "baked",
                 "boil", "boiled", "poach", "poached", "fry", "fried", "grill", "grilled",
                 "oven", "air fryer", "slow cooker", "barbecue", "bbq", "thaw", "thawed",
                 "defrost", "defrosted", "reheat", "reheated", "stuffing", "carve", "carving",
                 "leftovers", "per kg", "per 500g", "per kilo", "joint", "recipe", "sausage",
                 "mince", "minced", "fillet", "breast", "thigh", "brisket", "steak", "chop",
                 "chops",
                 # the bird as dinner with no cooking verb at all: "how long do i need for the
                 # chicken", "chicken legs in a curry, how long do they simmer" and "how long do
                 # the wings take" were all "A hen is never pregnant". A cut of meat, a pot and a
                 # time are the kitchen's words, so they stand the due date down.
                 "leg", "legs", "wing", "wings", "drumstick", "drumsticks", "simmer",
                 "simmering", "stew", "stewed", "soup", "stock", "curry", "casserole", "pie",
                 "dinner", "supper", "sandwich", "how long do i need for", "time for the",
                 # a person asking about their own pregnancy, a couple trying, or a symptom in a pet is
                 # the health row or the vet question, not a due date
                 "i am pregnant", "im pregnant", "i'm pregnant", "my wife", "my girlfriend",
                 "my partner", "my husband", "human", "trying for a baby", "ivf", "period",
                 "my period", "sick", "vomiting", "not eating", "losing weight", "bleeding",
                 "water broke", "waters broke", "contractions",
                 # the life span row and the size row key "how long" as well, and this row's
                 # bias would otherwise take "how long do rabbits live" from them
                 "live", "lives", "lived", "lifespan", "life span", "life expectancy",
                 "how old", "weigh", "weighs", "weight", "big", "large", "size", "tall",
                 # nor is a puppy's first walk a due date
                 "go out", "walks", "walk", "jabs", "vaccine", "vaccinated", "vaccinations",
                 "training", "lead", "recall",
                 # and a bitch coming into season is not a pregnancy: "when will my bitch come
                 # into season" was told she was due in 63 days, which is a confident wrong answer
                 "season", "seasons", "in season", "into season", "come into", "came into",
                 "on heat", "in heat", "heat", "split heat", "silent heat"),
          bias=2),
    # How big it is, or how much it weighs.
    entry("animal-size",
          (_names_with("size"),
           ("big", "bigger", "biggest", "large", "largest", "weigh", "weighs", "weighing",
            "weight", "heavy", "heavier", "heaviest", "tall", "taller", "tallest", "long",
            "length", "size", "much does", "how big", "how large")),
          _fact("size"),
          # "how long is a blue whale" is a size, "how long do blue whales live" is not, and
          # "how long is an elephant's trunk" is its own row below
          avoid=("live", "lives", "lifespan", "life span", "how old", "how many years",
                 "trunk", "trunks", "tail", "tails", "tongue", "neck", "bone", "bones",
                 "horn", "horns", "tooth", "teeth", "tusk", "tusks")),
    # How fast it goes.
    entry("animal-speed",
          (_names_with("speed"),
           ("fast", "faster", "fastest", "run", "runs", "running", "speed", "quick", "quickly",
            "how fast")),
          _fact("speed")),
    # The records: which animal is the fastest, biggest, tallest, longest lived or strongest.
    entry("animal-record",
          (("fastest", "biggest", "largest", "tallest", "heaviest", "strongest", "weakest",
            "longest lived", "longest living", "longest-lived", "oldest", "most dangerous",
            "lives the longest", "live the longest", "lives longest", "longest life",
            "deadliest"),
           ("animal", "animals", "creature", "creatures")),
          _record),
    # What it eats. The names are only the animals that have a line in EATS, so an animal with no
    # food fact passes the question on instead of getting a card about something else.
    entry("animal-eats",
          (tuple(name for row in ANIMALS for name in row["names"]
                 if any(n in EATS for n in row["names"])), EAT_CUES),
          _eats, avoid=EAT_AVOID, bias=1, ask=EAT_ASK),
    entry("animal-record-bird",
          (("biggest", "largest", "heaviest", "tallest", "fastest"),
           ("bird", "birds")),
          _record),
    entry("animal-record-fish",
          (("fastest", "biggest", "largest"),
           ("fish", "fishes", "shark", "sharks")),
          _record),
] + [_curiosity(animal, cue, reply) for animal, cue, reply in CURIOSITIES] \
  + [_curiosity(animal, cue, reply, DIET_AVOID, bias=1, ask=DIET_ASK)
     for animal, cue, reply in DIETS] \
  + [_curiosity(animal, cue, reply, DIET_AVOID + own, bias=1, ask=DIET_ASK)
     for animal, cue, reply, own in FARM_DIETS] \
  + [entry("animal-word-" + kind,
           (_names_with(kind, WORD_ROWS), _WORD_CUES[kind]),
           _the_word(kind), avoid=_WORD_AVOID, ask=_WORD_ASK, bias=1)
     for kind in ("young", "group", "female", "male")]
