"""Two everyday things side by side: "what is the difference between X and Y".

People ask for the difference between two things more than almost any other shape of question -
butter or margarine, single or double cream, a counsellor or a therapist, a debit or a credit
card - and the knowledge base read those lines one word at a time. One of the two names was a
subject it knew and the other was not:

    difference between butter and margarine   -> "Got it. Is there anything you'd like a hand with?"
    difference between a calorie and a kilojoule -> "I'm listening - say more if it helps."
    difference between double cream and single cream -> "Got it. Is there anything..."
    difference between a cold sore and a mouth ulcer -> the cold-and-flu answer
    difference between hay fever and a cold   -> the pet-allergy answer
    difference between a deposit and a holding deposit -> "Got it. Is there anything..."

The cause is the shape, not the subjects. A row about butter answers "is butter better for
pastry" and a row about margarine answers "is margarine vegan", but a line that names both is
asking for the pair, and no single-subject row can answer it: whichever row wins tells you about
half the question, and the cold-and-flu row told a person with a mouth ulcer about sneezing.

So the pairs are data, one row per pair, and the row is keyed by the two names and nothing else.
It answers only when the line names both - and only when the line is comparing them, because
"difference", "different", "versus", "vs", "compare", "compared" or "or" has to be in it too.
"my tablet won't connect to my laptop" names both and is not this question, and it is not
answered here.

Names are in the key as whole phrases ("holding deposit", not "deposit"), so a pair with a
longer name wins over a pair that only shares a word with it.
"""
import re

from .lookup import entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("food-and-drink", "cooking", "health", "money", "home-and-diy", "school-and-study",
           "work", "technology", "nature-and-weather", "pets", "shopping")

# The words that make a line a comparison rather than a mention of two things, or a request to
# pick one. "Or" was here and it was too loose: "i have a boil or a cyst on my back" and "a CV or
# a cover letter for a first job" are a request for advice about the person's own case, and the
# rows that answered them answered them better than the difference between the two things does.
_COMPARING = ("difference", "different", "differ", "versus", "vs", "compare", "compared",
              "distinguish", "same")

# (one of the two, the other of the two, the reply). The reply puts the answer in the first
# sentence - which of the two is which, or which you want - and stops.
_PAIRS = (
    # ---- food and cooking ----
    (("butter",), ("margarine",),
     "Butter is churned cream; margarine is refined vegetable oil blended with water and "
     "flavouring, made to spread and bake like butter. Butter tastes better and browns better, "
     "margarine is cheaper and spreadable straight from the fridge."),
    (("single cream",), ("double cream",),
     "Single cream is about 18% fat and only pours; double cream is about 48% and whips, thickens "
     "and holds its shape. Use single for pouring over a pudding and double where it has to whip "
     "or survive being boiled."),
    (("soured cream", "sour cream"), ("creme fraiche", "crème fraîche"),
     "Sour cream is about 20% fat and sours with lactic acid, so it splits if you boil it; creme "
     "fraiche is thicker, about 30% fat, and can be boiled without splitting. Stir sour cream in "
     "off the heat, and use creme fraiche for a sauce that simmers."),
    (("gammon",), ("ham",),
     "Gammon is the cut before it is cooked - a cured hind leg of pork - and ham is what you call "
     "it once it's cooked or sold ready to eat. You buy gammon to roast, and ham to put in a "
     "sandwich."),
    (("yam", "yams"), ("sweet potato", "sweet potatoes"),
     "A true yam is a rough, bark-like tuber from Africa and Asia, drier and starchier; the orange "
     "or white-fleshed \"yam\" in most UK shops is a sweet potato. If it has smooth skin, it's a "
     "sweet potato."),
    (("shallot", "shallots"), ("onion", "onions"),
     "A shallot is a small, mild relative of the onion, grown in cloves, sweeter and gentler raw. "
     "Use shallots where you want onion flavour without the bite - dressings, sauces, or roasted "
     "whole."),
    (("stock cube", "stock cubes"), ("stock pot", "stock pots", "fresh stock"),
     "A stock cube is dried concentrate, about one per 450ml of water, and salty. A stock pot is "
     "wet ready-made stock in a tub - fresher tasting and less salty - used one pot to roughly "
     "500ml. Either is fine; taste before you season."),
    (("plain flour",), ("self raising flour", "self-raising flour"),
     "Self-raising flour has baking powder already in it, about two teaspoons for every 150g of "
     "flour; plain flour has none. Cakes and scones want self-raising, bread and pastry want "
     "plain - and you can make self-raising by adding the baking powder yourself."),
    (("baking soda", "bicarbonate of soda", "bicarb"), ("baking powder",),
     "Baking soda is pure bicarbonate of soda and needs an acid - buttermilk, lemon, yoghurt - to "
     "make something rise. Baking powder is bicarbonate with the acid already mixed in, so it "
     "works with plain liquid and is what most cake recipes mean. To swap them, use about three "
     "times as much baking powder as soda, and never the other way round."),
    # ---- money ----
    (("calorie", "calories", "kcal"), ("kilojoule", "kilojoules", "kj"),
     "A calorie is the unit most food labels in the UK still lead with; a kilojoule is the metric "
     "one, usually in brackets beside it. One calorie is about 4.2 kilojoules, so 500 kcal is "
     "roughly 2,100 kJ."),
    (("tax credit", "tax credits"), ("benefit", "benefits"),
     "A benefit is money from the government because of your circumstances or your income; a tax "
     "credit was an older means-tested benefit paid through the tax system, and most people on "
     "them are being moved to Universal Credit. If you're not sure which you're on, your award "
     "letter says."),
    (("holding deposit",), ("deposit", "tenancy deposit", "security deposit"),
     "A holding deposit is the small sum - at most a week's rent in England - that takes a place "
     "off the market while the landlord checks you. The tenancy deposit is the bigger amount you "
     "pay when you sign, and it has to be held in a government protection scheme."),
    (("interest rate",), ("apr",),
     "The interest rate is what you pay on the money you owe; the APR also folds in the fees, so "
     "it's the number to compare two loans by. The lower APR is the cheaper loan, as long as the "
     "term is the same."),
    (("credit score",), ("credit report", "credit file"),
     "The report is the file itself - your accounts, payments and any defaults, as lenders see "
     "them. The score is a number one agency makes out of that file. Check the report for "
     "mistakes, because the score only follows from it."),
    (("sole trader",), ("limited company", "ltd"),
     "A sole trader is you and the business as one: simplest to run, but you're personally liable "
     "for its debts. A limited company is a separate legal person, so your own money is protected "
     "if it fails, and in exchange you file accounts publicly at Companies House."),
    (("third party", "third party fire and theft"), ("comprehensive",),
     "Third party covers the damage you do to other people and their cars; comprehensive adds "
     "damage to your own car, fire and theft. Third party, fire and theft sits between them - "
     "cheaper than comprehensive, but your own car is only covered if it burns or is stolen."),
    (("pcp", "personal contract purchase"), ("hire purchase",),
     "PCP is a loan with a final balloon payment: you pay mostly for the car's fall in value, then "
     "hand it back, pay the lump sum, or trade it in. Hire purchase spreads the whole price over "
     "the term, and the car is yours after the last payment."),
    # ---- health ----
    (("psychiatrist",), ("psychologist",),
     "A psychiatrist is a doctor who can diagnose mental illness and prescribe medicine; a "
     "psychologist studies and treats the mind with talking therapy and usually can't prescribe. "
     "A GP can refer you to either, and which one you need depends on whether medicine is part of "
     "the question."),
    (("counsellor", "counselor"), ("therapist", "psychotherapist"),
     "In the UK the words are used much the same way - someone trained to listen and help you work "
     "something through. \"Therapist\" is the broader word and covers CBT and other set "
     "approaches; \"counsellor\" usually means a trained listener rather than a clinician. Neither "
     "title is protected by law, so check the person is accredited."),
    (("anxiety",), ("panic attack", "panic attacks"),
     "Anxiety is the background feeling - worry and tension over days and weeks; a panic attack is "
     "a short, sudden surge that peaks within minutes, with a racing heart, breathlessness and a "
     "feeling that something awful is about to happen. You can have either without the other, and "
     "both are treatable."),
    (("migraine", "migraines"), ("headache", "headaches"),
     "A headache is pain in the head; a migraine is a condition - usually one-sided, throbbing, "
     "worse with light or movement, often with nausea or a warning aura, lasting hours. If a "
     "headache sends you to a dark room more than once, it's worth asking a GP about migraine."),
    (("heart attack",), ("cardiac arrest",),
     "A heart attack is a blocked blood supply to the heart muscle - the person is usually awake, "
     "with chest pain, and needs an ambulance fast. A cardiac arrest is the heart stopping "
     "altogether: unresponsive and not breathing normally, needing CPR and a defibrillator at "
     "once - call 999 first."),
    (("food allergy", "allergy"), ("intolerance", "food intolerance"),
     "An allergy is the immune system reacting to a food: it can come on within minutes and can be "
     "dangerous, with swelling or trouble breathing, so it means strict avoidance. An intolerance "
     "is the body struggling to digest something - uncomfortable, but not dangerous - and lactose "
     "is the common one."),
    (("cold sore", "cold sores"), ("mouth ulcer", "mouth ulcers"),
     "A cold sore is the herpes virus: a tingle, then a blister, usually on the lip, crusting over "
     "in a week or so, and it's catching. A mouth ulcer is a raw round sore inside the mouth, not "
     "catching, often from a knock, stress or a sharp tooth."),
    (("hay fever", "hayfever"), ("cold", "a cold"),
     "Hay fever is an allergy to pollen - sneezing, itchy eyes and a runny nose, no temperature, "
     "and it comes back at the same time each year. A cold is an infection: a sore throat first, "
     "then a blocked nose, gone in about a week."),
    (("boil", "boils"), ("cyst", "cysts"),
     "A boil is an infection of a hair follicle - tender and hot, and it comes to a head and "
     "drains. A cyst is a closed sac under the skin, usually painless unless it gets inflamed, and "
     "it doesn't drain by itself. Neither should be squeezed."),
    (("hypo", "hypoglycaemia", "low blood sugar"), ("hyper", "hyperglycaemia", "high blood sugar"),
     "A hypo is low blood sugar - shaky, sweaty, confused - and it needs sugar fast. Hyper means "
     "high: thirsty, weeing a lot, tired over hours, and it needs insulin and advice. The hypo is "
     "the one that has to be treated in minutes."),
    (("flu", "influenza"), ("covid", "coronavirus"),
     "Flu is influenza and Covid is the coronavirus, and you can't tell them apart by symptoms - "
     "fever, cough and tiredness come with both, so a test is the only way to know. Both are worth "
     "staying home for, and both are riskier for the same people."),
    # ---- home, work and school ----
    (("state school",), ("academy", "academies", "free school"),
     "Both are state schools and free to attend. A maintained school is run by the local "
     "authority; an academy is funded directly by the government, sets its own curriculum and "
     "admissions, and is run by a trust. For a parent, the practical difference is who you "
     "complain to."),
    (("apprenticeship", "apprenticeships"), ("traineeship", "traineeships"),
     "An apprenticeship is a paid job with training and a qualification, usually one to four "
     "years. A traineeship is a short unpaid course - weeks, not years - for someone not yet ready "
     "for an apprenticeship, and it's often the step before one."),
    (("btec", "btecs"), ("a level", "a levels"),
     "A levels are exam-based and mostly academic, usually three subjects; BTECs are "
     "coursework-based and vocational, and a full BTEC is the size of three A levels. Both get you "
     "to university, and a BTEC suits a subject you'd rather do than read about."),
    (("cv",), ("cover letter", "covering letter"),
     "A CV lists what you've done - jobs, education, skills - in a page or two. A cover letter is "
     "the short note that goes with it, saying why you want this job and which bits of the CV "
     "matter for it."),
    (("mortgage broker", "broker"), ("financial adviser", "financial advisor", "ifa"),
     "A broker shops mortgages from several lenders for you and is paid a fee or commission. A "
     "financial adviser looks at the whole picture - pensions, savings, investments - and is "
     "regulated to advise on them. Use the broker for the mortgage and the adviser for the rest."),
    (("letting agent",), ("landlord",),
     "The landlord owns the place; the letting agent runs it for them - viewings, repairs, the "
     "paperwork. Your tenancy is with the landlord, so your rights are against the owner even when "
     "you deal with the agent every day."),
    (("solicitor",), ("barrister",),
     "A solicitor is who you deal with directly: contracts, conveyancing, wills, letters, and "
     "preparing a case. A barrister is the court specialist who argues it in front of a judge, and "
     "a solicitor usually instructs them for you."),
    (("optician", "opticians"), ("optometrist", "optometrists"),
     "The optometrist tests your eyes and writes the prescription; the dispensing optician makes "
     "and fits the glasses. Most high-street shops are both, so you see whoever your appointment "
     "is with."),
    (("dentist",), ("hygienist", "dental hygienist"),
     "The dentist diagnoses and treats - check-ups, fillings, crowns, extractions; the hygienist "
     "cleans, scaling and polishing and checking your gums. Most practices book you with the "
     "hygienist every six months and the dentist for the check-up."),
    # ---- tech and home kit ----
    (("tablet", "tablets", "ipad"), ("laptop", "laptops", "computer"),
     "A tablet is a touchscreen for reading, watching and browsing; a laptop has a keyboard and "
     "full software, so it's the one for typing, spreadsheets and real work. If it's your only "
     "device for work, get the laptop."),
    (("smart meter",), ("normal meter", "old meter", "traditional meter"),
     "A smart meter sends your readings to the supplier itself, so you stop reading meters, and it "
     "comes with an in-home display. An old meter needs reading by you or a visitor. Neither "
     "changes what you pay per unit."),
    (("dehumidifier",), ("air purifier",),
     "A dehumidifier takes water out of the air, which is what stops damp, condensation and "
     "mould; an air purifier filters dust, pollen and smoke out of it. Damp room, dehumidifier; "
     "allergies or a smoky street, purifier."),
    # ---- added: the pairs people ask about most that still got a shrug or a neighbour ----
    (("celsius", "centigrade"), ("fahrenheit",),
     "Celsius freezes water at 0 and boils it at 100; Fahrenheit puts the same two marks at 32 and "
     "212, so a Fahrenheit degree is the smaller one. To convert, multiply the Celsius figure by "
     "1.8 and add 32 - body heat is 37C or 98.6F, and a hot day is 30C or 86F."),
    (("sea salt",), ("table salt",),
     "Both are sodium chloride and season the same; sea salt is coarser and less dense, so a "
     "level teaspoon holds less of it, and table salt is fine, treated to run freely and has iodine "
     "added in the UK. Use table salt in baking, where it has to dissolve evenly."),
    (("whole milk",), ("semi skimmed milk", "semi-skimmed milk", "skimmed milk"),
     "Whole milk is about 3.5% fat, semi-skimmed about 1.7% and skimmed under 0.5%. Semi-skimmed "
     "has roughly half the fat and calories of whole, and the protein and calcium are much the "
     "same, so for most adults it is the swap that costs nothing."),
    (("eczema",), ("psoriasis",),
     "Eczema is dry, itchy, red skin, often in the elbow and knee creases, and it flares with soap, "
     "heat and stress. Psoriasis makes thick, silvery scaly patches, usually on elbows, knees and "
     "scalp, and it can affect the joints too. Both are treated with emollients and steroid "
     "creams, so a GP or pharmacist is the place to start."),
    (("stress",), ("burnout", "burn out", "burn-out"),
     "Stress is too much pressure while you can still see the point of what you are doing; burnout "
     "is the exhaustion that comes after months of it, when you have stopped caring and the work "
     "feels flat. Stress eases when the pressure does - burnout does not, and usually needs time "
     "off and a change, not a better week."),
    (("fixed rate", "fixed"), ("variable rate", "variable"),
     "A fixed rate stays the same for an agreed term, so the monthly payment is known from the "
     "start; a variable rate moves with the lender or the Bank of England and can fall as well as "
     "rise. Fixed buys certainty and usually costs a little more; variable is cheaper while rates "
     "are falling."),
    (("lodger", "lodgers"), ("tenant", "tenants"),
     "A lodger lives in the same home as the owner and shares the kitchen or bathroom; a tenant "
     "rents a place of their own with a tenancy and has the whole of it. A lodger can usually be "
     "asked to leave with reasonable notice, while a tenant needs a court order - so in England "
     "the word on the agreement matters as much as the money."),
    (("food processor",), ("blender",),
     "A blender is a tall jug with blades in the base, for things that pour - smoothies, soup, "
     "sauces. A food processor is a wide bowl with a blade and discs, for chopping, slicing and "
     "grating solid food like onions, nuts or pastry. Thin and liquid, blender; chunky or grated, "
     "processor."),
    (("coach", "coaches"), ("bus", "buses"),
     "A bus is the local service, stopping often along a town route and often turning up without a "
     "booking; a coach is for longer journeys between towns, with seats booked in advance, luggage "
     "in the hold and few stops. In the UK, National Express and Megabus run coaches."),
    # ---- animals and nature ----
    (("shark", "sharks"), ("dolphin", "dolphins"),
     "A shark is a fish: gills, cartilage instead of bone, and a tail that swings side to side. A "
     "dolphin is a mammal: it breathes air through a blowhole, has a skeleton, feeds its young "
     "milk, and its tail moves up and down."),
    (("moth", "moths"), ("butterfly", "butterflies"),
     "Butterflies mostly fly by day and rest with their wings folded up together; moths mostly fly "
     "at night and rest with theirs spread flat. Moths also have fatter, hairier bodies and "
     "feathery antennae rather than thin ones with a club on the end."),
)


def _with_cream(understood):
    """The line says cream somewhere: "single or double cream" is the same question as the pair,
    and "single" and "double" on their own are far too common to key anything."""
    return "cream" in ((understood or {}).get("clean") or "").lower()


def _slug(name):
    """A row id from the two names, so a duplicate pair shows up as a duplicate id."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _pair(row):
    """One pair: the two names as the two key groups, and only a comparing line reaches it."""
    first, second, said = row[0], row[1], row[2]
    # One name in each key group, never the same name in both: the line has to name both things
    # for the row to score at all, which is what makes this the answer to a comparison rather
    # than to half of one.
    return entry("difference-" + _slug(first[0]) + "-and-" + _slug(second[0]),
                 (tuple(first), tuple(second)), said, ask=_COMPARING, bias=2)


ENTRIES = [_pair(row) for row in _PAIRS]

# "Single or double cream?" names each half without repeating the noun, which the pair above
# cannot see: its key holds the whole phrase "single cream". The guard is what keeps "single" and
# "double" from answering anything else.
_ABOUT_CREAM = ("Single cream is about 18% fat and only pours; double cream is about 48% and "
                "whips, thickens and holds its shape. Use single for pouring over a pudding and "
                "double where it has to whip or survive being boiled.")
ENTRIES.append(entry("difference-single-or-double-cream", (("single",), ("double",)),
                     _ABOUT_CREAM, ask=_COMPARING, bias=2, guard=_with_cream))
