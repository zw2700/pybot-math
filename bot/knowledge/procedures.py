"""The procedures people are sent for, asked about by name.

The knowledge base holds conditions (conditions.py), symptoms (body.py), the scans (health.py)
and what to do before an appointment (appointments.py), but nothing held the procedure itself:
"what is a colonoscopy", "what happens during a vasectomy", "what is a root canal" were all
answered "That's beyond what I know well, sorry" or "I'm not sure about that one". A person who
has been handed a date for one of these wants four things, and the card is built in that order:
what it is, what happens on the day, how long it takes, and what the recovery is.

So the subject here is the name of the procedure and the second half is how the line asks about
it: the explain shapes ("what is", "what happens during", "how does it work"), the length
shapes ("how long does it take", "how long in hospital"), the pain shapes ("does it hurt", "will
i be awake"), and the recovery shapes ("how long off work", "how long to recover"). `explain=True`
lets the bare name reach the card, and `report=True` lets a person say they are having one ("i
have a colonoscopy on friday") and hear the answer rather than "Got it".

What these rows deliberately do not take: the preparation question, which is appointments.py
("do i need to fast before", "what should i bring"), a scan, which is health.py ("what is an mri
scan"), and a named condition, which is conditions.py ("what is endometriosis"). A line about
pain, bleeding or a sudden turn for the worse is nobody's card here.
"""

from .lookup import ASK_ABOUT, entry

ANSWERS = ("health",)

# How a line asks about the procedure rather than about what to do before it. The two live next
# door to each other all day - "what happens during a colonoscopy" beside "what do i need to do
# before a colonoscopy" - so the words that ask about the procedure are their own group.
_WHAT_HAPPENS = ASK_ABOUT + (
    "what is", "whats", "what are", "what happens", "what goes on", "happens during",
    "happens in", "happens on the day", "goes on during", "during", "involve", "involves",
    "explain", "tell me about", "how does it work", "how does that work", "how it works",
    "what do they do", "what will they do", "what are they doing", "what is it like",
    "does it hurt", "hurt", "painful", "pain", "awake", "sedated", "sedation", "asleep",
    "general anaesthetic", "anaesthetic", "anesthetic", "recover", "recovery", "recovering",
    "afterwards", "after it", "after the", "how long", "take", "takes", "in hospital",
    "off work", "back to work", "drive", "driving", "sore", "how many", "check up",
)

# A question of whether to have it, which card to choose instead, and a letter or a bill are not
# a request to explain the procedure: the answer to "should i have a vasectomy" is a decision,
# not four sentences about the operation.
_NOT_A_REQUEST_TO_EXPLAIN = (
    "should i", "should we", "shall i", "do i need", "do i have to", "have to", "worth it",
    "worth having", "instead", "or not", "better than", "compare", "rather than",
    "how much", "cost", "costs", "price", "private", "nhs", "waiting list", "how long is the wait",
    "cancel", "cancelled", "reschedule", "missed", "letter", "results", "my results",
)

# A procedure in a line about a sudden turn is an emergency line, and the safety card is the one
# that answers it.
_NOT_AN_EMERGENCY = (
    "chest pain", "cant breathe", "can't breathe", "cannot breathe", "unconscious",
    "not breathing", "collapsed", "collapsed at", "a&e", "999", "ambulance", "bleeding badly",
    "heavy bleeding", "suicidal", "overdose", "took an overdose",
)

# A pet, a plant and a car are somebody else's card, and the same name means nothing there.
_NOT_A_PERSON = ("dog", "dogs", "puppy", "cat", "cats", "kitten", "pet", "pets", "vet",
                 "hamster", "rabbit", "horse", "guinea pig", "plant", "plants", "car", "cars",
                 "boiler", "washing machine", "phone")


def _a_row(name, variants, reply, extra_avoid=(), bias=0):
    return entry(name,
                 (variants, _WHAT_HAPPENS),
                 reply,
                 ask=variants,
                 avoid=_NOT_A_REQUEST_TO_EXPLAIN + _NOT_AN_EMERGENCY + _NOT_A_PERSON + extra_avoid,
                 explain=True, report=True, bias=bias)


ENTRIES = []

ENTRIES.append(_a_row(
    "colonoscopy",
    ("colonoscopy", "colonoscopies", "camera up my back passage", "bowel camera"),
    "A colonoscopy is a camera on a flexible tube put up through the back passage to look all "
    "the way round the bowel, and it takes about 20 to 30 minutes. You are given sedation and "
    "pain relief through a cannula, so most people are drowsy and remember little of it, and you "
    "go home the same day once you have eaten and been to the toilet - but not driving, so bring "
    "someone. Wind and a bloated ache for a day are the usual aftermath, and the bowel prep the "
    "day before matters more than anything else: the cleaner the bowel, the more they can see."))

ENTRIES.append(_a_row(
    "endoscopy",
    ("endoscopy", "endoscopies", "gastroscopy", "camera down my throat", "camera in my stomach"),
    "An endoscopy is a thin camera on a tube passed down your throat to look at the food pipe, "
    "the stomach and the top of the bowel, and it takes 10 to 20 minutes. Your throat is numbed "
    "with a spray and you are usually offered sedation, so the gagging is the worst of it rather "
    "than pain; you go home the same day, but not driving if you took the sedation. A sore "
    "throat and a bit of wind for a day are normal, and you will be asked not to eat for about "
    "six hours before."))

ENTRIES.append(_a_row(
    "sigmoidoscopy",
    ("sigmoidoscopy", "flexible sigmoidoscopy", "sigmoidoscopies"),
    "A flexible sigmoidoscopy is a camera on a tube into the lower bowel only, about the last "
    "half metre, and it takes 10 to 15 minutes - less of a journey than a full colonoscopy. Most "
    "people have it without sedation, lying on their side, with some cramping and wind as the "
    "tube goes round the bends; you go home straight afterwards and can drive. The bowel prep is "
    "usually an enema at the hospital rather than a day of drinking the stuff."))

ENTRIES.append(_a_row(
    "cystoscopy",
    ("cystoscopy", "cystoscopies", "camera in my bladder", "camera up my urethra"),
    "A cystoscopy is a thin camera passed up the water pipe into the bladder, and it takes about "
    "5 to 10 minutes. It is done with a numbing gel, so it is uncomfortable rather than painful - "
    "a sharp sting as it goes in and a strong urge to pass water while it is there - and you can "
    "drive yourself home. Expect stinging and pinkish urine for a day or two and drink plenty of "
    "water to flush it through; ring the ward if it is bright red or you get a fever."))

ENTRIES.append(_a_row(
    "angiogram",
    ("angiogram", "angiograms", "cardiac catheter", "catheter test"),
    "An angiogram is a dye test that shows the arteries: a fine tube goes into the wrist or the "
    "groin under local anaesthetic, dye is injected, and X-rays follow it round. It takes 20 to "
    "40 minutes and does not hurt beyond the sting of the numbing injection. You rest with "
    "pressure on the puncture for a few hours, go home the same day in most cases, and should "
    "keep the arm or leg easy for 24 hours - no lifting, no driving that day."))

ENTRIES.append(_a_row(
    "angioplasty",
    ("angioplasty", "stent", "stents", "a stent put in", "balloon", "stent fitted"),
    "An angioplasty is the same tube as an angiogram, with a tiny balloon on the end that is "
    "blown up to squash the narrowed artery open, and usually a mesh stent left in to hold it "
    "there. It takes 30 to 60 minutes, you are awake with numbing at the wrist or groin, and you "
    "are usually in for the day or one night. The stent is permanent and grows a layer of the "
    "artery's own lining over itself, so it is not something that needs changing."))

ENTRIES.append(_a_row(
    "lumbar-puncture",
    ("lumbar puncture", "spinal tap", "lumbar punctures"),
    "A lumbar puncture is a needle into the lower back to draw off a sample of the fluid around "
    "the spinal cord, and it takes about 15 minutes. The skin is numbed first, so the worst is a "
    "push and a strange tingling down a leg; you lie flat for an hour or so afterwards and go "
    "home the same day. Drink plenty and keep still for the rest of the day - the headache that "
    "follows is the commonest problem, and lying flat is what settles it."))

ENTRIES.append(_a_row(
    "blood-transfusion",
    ("blood transfusion", "transfusion", "transfusions", "units of blood", "pint of blood"),
    "A blood transfusion is donated blood run into a vein through a cannula, one unit at a time, "
    "each taking about two to four hours. It is not an operation: you sit or lie while it drips, "
    "and the nurse checks your pulse, blood pressure and temperature before each unit and again "
    "at the start of it. Most people have it as a day patient, feel warmer and less breathless "
    "within a day, and the main thing to report is a rash, shivering or a sudden fever."))

ENTRIES.append(_a_row(
    "dialysis",
    ("dialysis", "haemodialysis", "hemodialysis", "kidney dialysis"),
    "Dialysis does the filtering job the kidneys cannot: your blood is taken out, run past a "
    "filter and put back, either in sessions at a unit - usually three a week, four hours each - "
    "or at home overnight. It is not painful, and people read, sleep or watch something through "
    "it; the needle going in at the start of each session is the only sharp bit, and a "
    "fistula in the arm is looked after carefully for that reason. Between sessions the work is "
    "fluids, salt and potassium, and the team sets the limits."))

ENTRIES.append(_a_row(
    "radiotherapy",
    ("radiotherapy", "radiation therapy", "radiotherapy treatment", "radiotherapy sessions"),
    "Radiotherapy is a beam of X-rays aimed at one small area to damage the cells growing out of "
    "control, and each session is short - about 10 to 20 minutes, with the treatment itself only "
    "a few minutes. It does not hurt and does not make you radioactive; you lie still on a couch "
    "under the machine, usually every weekday for a few weeks, and the planning session before "
    "the first one takes longer than the treatment. Tiredness and sore skin over the area build "
    "up over the course, and your team gives you the cream and the rules."))

ENTRIES.append(_a_row(
    "chemotherapy",
    ("chemotherapy", "chemo", "chemotherapy treatment", "chemo sessions"),
    "Chemotherapy is cancer drugs that travel through the whole body, given as a drip, as tablets "
    "or both, in cycles of a treatment day followed by a few weeks off so the body recovers. The "
    "drip itself does not hurt and takes an hour or a few depending on the drugs; a cannula or a "
    "line goes in first. The side effects that matter are the ones your team gives you drugs for "
    "in advance - sickness, a sore mouth, and above all an infection risk in the week after, so a "
    "temperature over 37.5C or feeling shivery is a phone call to the unit the same day, not a "
    "wait."))

ENTRIES.append(_a_row(
    "hysterectomy",
    ("hysterectomy", "hysterectomies", "womb removed", "womb taken out"),
    "A hysterectomy is the womb taken out, either through the tummy, through the vagina or by "
    "keyhole, and the operation takes about an hour to an hour and a half. You are asleep for it "
    "and in hospital for one to four nights depending on the route. Recovery is the long part: "
    "two weeks of taking it very easy, six weeks before lifting anything heavier than a kettle "
    "or driving on the road, and no sex or swimming for about six weeks. If the ovaries come out "
    "too, that is the menopause starting, and it can be managed."))

ENTRIES.append(_a_row(
    "keyhole-surgery",
    ("keyhole surgery", "laparoscopy", "laparoscopic surgery", "keyhole operation", "keyhole"),
    "Keyhole surgery is an operation done through two or three small cuts rather than one long "
    "one: a slim camera goes in through the belly button, the surgeon works off the screen, and "
    "the cuts are each a centimetre or so, closed with a stitch or glue. The operation takes "
    "about as long as the open version but the recovery is much shorter - often home the same "
    "day or the next, back to light normal in a week. The gas they use to make room is what "
    "leaves you with a bloated ache in the shoulders for a day or two."))

ENTRIES.append(_a_row(
    "vasectomy",
    ("vasectomy", "vasectomies", "the snip", "snipped"),
    "A vasectomy is the two tubes that carry sperm from the testicles cut and sealed, so the "
    "semen has no sperm in it; it takes about 15 to 30 minutes under local anaesthetic. You are "
    "awake, the worst is the numbing injection, and you go home the same day in loose trousers "
    "with a bag of frozen peas. Two days of taking it easy, a week before anything strenuous, and "
    "it is not instant: you need a sample checked at about 12 weeks and another clear one before "
    "you rely on it, so use something else until then."))

ENTRIES.append(_a_row(
    "root-canal",
    ("root canal", "root canal treatment", "root canals", "root canal work"),
    "A root canal is a tooth saved rather than taken out: the dentist drills in from the top, "
    "cleans the infected nerve out of the canals inside the root, and seals them. It takes one or "
    "two visits of 45 minutes to an hour and a half, and with modern numbing it feels much like a "
    "filling - the pain comes from the infection before the visit, not from the drilling. The "
    "tooth is brittle afterwards, so a crown on a back tooth is the usual last step, and some "
    "soreness for two or three days is normal."))

ENTRIES.append(_a_row(
    "knee-replacement",
    ("knee replacement", "knee replacements", "new knee", "knee op"),
    "A knee replacement takes the worn surfaces off the end of the thigh bone and the top of the "
    "shin bone and puts a metal and plastic joint in their place; the operation takes about an "
    "hour to 90 minutes under a spinal or general anaesthetic. Most people are up on it the day "
    "after with a frame, in for two to four nights, and the physio starts straight away because "
    "the bending is what needs the work. Expect swelling and a stiff, warm knee for weeks, "
    "walking sticks for about six weeks, and up to a year before it feels like your own.",
    extra_avoid=("recover", "recovery", "recovering", "off work", "back to work", "drive",
                 "driving", "how long am i off", "sick note")))

ENTRIES.append(_a_row(
    "mammogram",
    ("mammogram", "mammograms", "breast screening", "breast x-ray", "breast xray"),
    "A mammogram is an X-ray of each breast, taken by pressing it between two plates for a few "
    "seconds at a time, four pictures in all, and the whole appointment is about 20 minutes. It "
    "is uncomfortable rather than painful - a firm squeeze that stops as soon as the picture is "
    "taken - and you can drive yourself home and go back to work. The screening programme calls "
    "women every three years from 50 to 70; a recall for another look is common and mostly not "
    "cancer, because screening is meant to find the things too small to feel."))
