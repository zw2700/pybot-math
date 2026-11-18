"""The conditions people ask about by name, where the knowledge base had no card at all.

These are not complaints to hand to a pharmacist (those are complaints.py) and they are not
symptoms in a body part (those are body.py): they are the named diagnoses an adult brings to a
chat, and on the day this file was written the bot answered almost all of them with a shrug -
"what is endometriosis", "what is sleep apnoea", "what is the menopause" -
or with a neighbour's card, because a symptom row sat next door and the name itself was keyed
nowhere.

So the subject here is the name, and the second half is how the line asks about it: the explain
shapes ("what is", "tell me about", "explain"), the diagnosis shapes ("how is it diagnosed"),
the symptom shapes and the treatment shapes. `explain=True` lets the bare ask reach the name
("tell me about gallstones"), `report=True` lets a person say they have it ("i have
gallstones") and hear the answer rather than "Got it", and every card names the one thing to do
first, how long it takes, and the line where it stops being a wait-and-see question.

What these rows deliberately do not take: a cooking or pet line about a word that is also a
food or an animal, a pregnancy line (the pregnancy rows own those), and the money questions
about sick pay and benefits, which have their own cards.
"""

from .lookup import ASK_ABOUT, entry

ENTRIES = []

# The words that turn a named condition into a question about it. The name alone is not enough
# for a card that also carries a treatment, and the name plus "what is" is not enough for one
# that also answers "how long does it last".
_ASKING = ASK_ABOUT + ("what is", "whats", "what are", "explain", "tell me about", "mean",
                       "means", "symptoms", "signs", "diagnosed", "diagnosis", "test", "tests",
                       "how long", "last", "lasts", "cause", "causes", "why", "have", "got",
                       "ive", "i've", "think", "worse", "better", "cure", "cured", "serious",
                       "dangerous", "normal", "contagious", "catch", "should i", "see a doctor",
                       "gp", "hospital")

# A body that is expecting a baby has its own rows, and a named condition asked in pregnancy is a
# midwife's question, not a card read off the internet.
_PREGNANT = ("pregnant", "pregnancy", "expecting", "trimester", "weeks pregnant", "midwife",
             "trying to conceive", "ivf")
# A pet, a child's line and a plant are somebody else's card: the same name means nothing there
# and the animal or child answers are better than a condition card.
_NOT_A_PERSON = ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets", "vet",
                 "hamster", "rabbit", "horse", "guinea pig", "parrot", "fish")
_MONEY = ("sick pay", "ssp", "benefit", "benefits", "pip", "allowance", "insurance", "claim",
          "compensation")

ENTRIES.append(entry("endometriosis",
    (("endometriosis", "endo"),
     _ASKING + ("period", "periods", "pelvic", "pain", "painful", "heavy", "sex", "tummy",
                "belly", "bloating", "bowel", "poo", "fertility", "infertile", "cramps")),
    "Endometriosis is tissue like the womb lining growing outside it - most often on the "
    "ovaries, the back of the womb or the bowel - which bleeds each month with nowhere to go, so "
    "periods are very painful, sex hurts and sometimes passing stools hurts. Write down the pain "
    "and the days for two or three cycles and take that to the GP: ask straight out for a "
    "referral to gynaecology rather than waiting to be offered one, because the delay from first "
    "symptom to diagnosis is years. Hormonal treatment (the pill, a progestogen, an IUS) or "
    "surgery helps, and it does not always mean you cannot have children.",
    ask=("endometriosis", "endo"),
    avoid=_PREGNANT + _NOT_A_PERSON + _MONEY,
    explain=True, report=True, bias=1))

ENTRIES.append(entry("gallstones",
    (("gallstones", "gallstone", "gall stones", "gall stone", "gallbladder", "gall bladder"),
     _ASKING + ("pain", "ache", "attack", "colic", "nausea", "sick", "vomit", "tummy", "belly",
                "stomach", "right side", "shoulder", "back", "fatty", "after eating", "removed",
                "removal", "operation", "keyhole", "diet", "dissolve")),
    "Gallstones are stones of bile in the gallbladder, and most never cause a problem - they are "
    "found by chance and left alone. The pain they do cause is biliary colic: a severe ache under "
    "the ribs on the right, an hour or two after a fatty meal, spreading to the right shoulder "
    "blade, easing over a few hours. Go to A&E the same day if it lasts more than about five "
    "hours, or comes with a fever, yellow skin or a swollen, tender belly. Cutting fat out does "
    "not dissolve them; keyhole surgery to take the gallbladder out is the fix.",
    ask=("gallstones", "gallstone", "gall stones", "gall stone", "gallbladder", "gall bladder"),
    avoid=_PREGNANT + _NOT_A_PERSON + _MONEY + ("kidney", "kidney stone", "kidney stones"),
    explain=True, report=True, bias=1))

ENTRIES.append(entry("sinusitis",
    (("sinusitis", "sinus infection", "sinus infections", "sinus"),
     _ASKING + ("blocked", "nose", "face", "pressure", "pain", "headache", "green", "yellow",
                "discharge", "snot", "smell", "steam", "rinse", "antibiotics", "weeks")),
    "Sinusitis is the lining of the sinuses swollen by a cold, so the face aches over the cheeks "
    "and eyes, the nose is blocked with thick discharge and the smell goes dull. Most of it is "
    "viral and settles in two to three weeks on its own: steam, a salt-water rinse from a "
    "pharmacy and paracetamol do more than antibiotics, which are only worth it if it is going on "
    "ten days and getting worse or keeps coming back. See a GP if it lasts over ten days or "
    "happens more than three times a year, and go the same day if the skin around an eye swells, "
    "vision changes or there is a severe headache with a fever.",
    ask=("sinusitis", "sinus infection", "sinus infections", "sinus"),
    # how long it lasts is `lasts-sinus-infection`'s question and that card gives the number, so
    # this one stands down on the duration asks and answers the what-is-it and what-to-do lines
    avoid=_PREGNANT + _NOT_A_PERSON + _MONEY + ("how long", "how many days", "last", "lasts",
            "lasting", "duration", "still", "weeks", "days"),
    explain=True, report=True, bias=1))

ENTRIES.append(entry("diverticulitis",
    (("diverticulitis", "diverticulosis", "diverticular disease", "diverticula", "diverticulum"),
     _ASKING + ("pain", "left side", "tummy", "belly", "stomach", "fever", "temperature",
                "bowel", "poo", "constipated", "diarrhoea", "blood", "nausea", "antibiotics",
                "diet", "fibre", "seeds", "nuts", "flare", "attack")),
    "Diverticulitis is small pouches in the bowel wall becoming inflamed, and it comes on as "
    "constant pain low on the left of the tummy, often with a temperature, feeling rough and a "
    "change in the bowels. Ring the GP the same day rather than wait it out: uncomplicated cases "
    "settle in a few days with rest, fluids and painkillers, and antibiotics only if there are "
    "signs of infection. Go to A&E for severe pain, a hard belly, a high temperature or blood in "
    "the stool. Once it has settled, fibre, fluids, exercise and losing weight make another "
    "attack less likely, and seeds and nuts are not the enemy they were once thought to be.",
    ask=("diverticulitis", "diverticulosis", "diverticular disease", "diverticula",
         "diverticulum"),
    avoid=_PREGNANT + _NOT_A_PERSON + _MONEY,
    explain=True, report=True, bias=1))

ENTRIES.append(entry("varicose-veins",
    (("varicose veins", "varicose vein", "varicose", "spider veins", "thread veins"),
     _ASKING + ("leg", "legs", "aching", "heavy", "swollen", "ankles", "itch", "itchy", "pain",
                "throbbing", "standing", "stockings", "compression", "treatment", "removed",
                "laser", "ablation", "surgery", "ulcer", "bleeding")),
    "Varicose veins are valves in the leg not closing, so blood pools and the vein bulges: legs "
    "ache and feel heavy by evening, ankles swell in the heat and the skin can itch. They are "
    "rarely dangerous. Compression stockings from a pharmacy, keeping the legs up when you sit, "
    "walking and losing weight all ease the ache, and if the look of them bothers you the GP can "
    "refer you - the usual fix is a day-case procedure, laser or glue or a small stripping, not a "
    "big operation. See the GP if the skin over a vein goes brown, hard or weepy (that is heading "
    "for an ulcer) or a vein bleeds, and go the same day for a hot, red, swollen leg - that can "
    "be a clot.",
    ask=("varicose veins", "varicose vein", "varicose", "spider veins", "thread veins"),
    avoid=_PREGNANT + _NOT_A_PERSON + _MONEY,
    explain=True, report=True, bias=1))

ENTRIES.append(entry("rosacea",
    (("rosacea", "facial flushing", "flushing face"),
     _ASKING + ("face", "cheeks", "nose", "red", "redness", "flush", "flushing", "spots",
                "pustules", "burning", "stinging", "skin", "cream", "gel", "antibiotics",
                "trigger", "triggers", "worse", "alcohol", "sun", "spicy")),
    "Rosacea is a skin condition that flushes and reddens the cheeks, nose and chin, with "
    "stinging and sometimes small pus-filled spots, and it comes and goes in flares. Use a mild "
    "cleanser, a daily sunscreen (sun is the commonest trigger), and trim the other triggers: "
    "alcohol, hot drinks, spicy food, a hot shower, stress. The GP can prescribe a gel - "
    "metronidazole, azelaic acid or ivermectin - or a course of antibiotics, which calm it over "
    "weeks rather than days. It is not acne and it is not infectious. See the GP if the nose "
    "thickens or the eyes are gritty and red, because ocular rosacea is treated too.",
    ask=("rosacea", "facial flushing", "flushing face"),
    avoid=_PREGNANT + _NOT_A_PERSON + _MONEY,
    explain=True, report=True, bias=1))

ENTRIES.append(entry("labyrinthitis",
    (("labyrinthitis", "vestibular neuritis", "inner ear infection", "inner ear inflammation"),
     _ASKING + ("dizzy", "dizziness", "vertigo", "spinning", "balance", "nausea", "vomit",
                "hearing", "ear", "walking", "off balance", "how long", "last", "lasts")),
    "Labyrinthitis and vestibular neuritis are inflammation of the balance nerve, nearly always "
    "after a cold: sudden spinning vertigo with nausea, worse when you move your head, and it is "
    "vestibular neuritis if the hearing is normal and labyrinthitis if it is muffled. It is not "
    "usually dangerous but it is horrible, so see the GP the same day the first time it happens "
    "to have it checked. Anti-sickness tablets such as cyclizine from a pharmacy get you through "
    "the first few days, then gentle movement and walking help the brain retrain the balance - "
    "lying still for longer slows recovery. Go to A&E if there is weakness down one side, "
    "slurred speech, double vision or a sudden hearing loss.",
    ask=("labyrinthitis", "vestibular neuritis", "inner ear infection",
         "inner ear inflammation"),
    avoid=_PREGNANT + _NOT_A_PERSON + _MONEY,
    explain=True, report=True, bias=1))

ENTRIES.append(entry("tennis-elbow",
    (("tennis elbow", "golfer's elbow", "golfers elbow", "epicondylitis"),
     _ASKING + ("elbow", "arm", "pain", "ache", "grip", "gripping", "lift", "lifting",
                "typing", "mouse", "sore", "hurt", "hurts", "outside", "inside", "brace",
                "exercises", "physio", "how long", "last", "lasts")),
    "Tennis elbow is the tendon on the outside of the elbow overworked by gripping, lifting and "
    "typing, so the outside of the elbow aches and the grip weakens; golfer's elbow is the same "
    "on the inside. It is not a wait-and-rest injury: rest it from the thing that caused it, but "
    "keep using the arm gently, and do the eccentric exercise - a light weight or a tin, wrist "
    "slowly down and lift back with the other hand, three sets of fifteen, most days. A brace "
    "from a pharmacy helps while it settles, which takes weeks to a few months. See the GP or a "
    "physio if it is no better after six weeks, and the same day if there was a bang or the hand "
    "is numb, because that is not a tendon.",
    ask=("tennis elbow", "golfer's elbow", "golfers elbow", "epicondylitis"),
    avoid=_PREGNANT + _NOT_A_PERSON + _MONEY,
    explain=True, report=True, bias=1))

ENTRIES.append(entry("menopause",
    # "the change" is NOT a key: "what is the change in my contract" got this card, and the
    # job, the lease and the timetable all have a change too. "menopause" is the name people use.
    (("menopause", "perimenopause", "hot flushes", "hot flushes at night", "hormone replacement",
      "hrt"),
     _ASKING + ("period", "periods", "stopped", "stopping", "flushes", "flushing", "sweats",
                "night sweats", "sleep", "mood", "anxiety", "brain fog", "memory", "joints",
                "aches", "dryness", "sex", "libido", "weight", "hair", "how long", "last",
                "lasts", "start", "starts", "age", "test", "blood test", "hrt", "tablets",
                "gel", "patch", "contraception", "pregnant")),
    "The menopause is a year without a period (two years if you are under 50), and the years "
    "before it - the perimenopause, usually starting in the mid-forties - are when the flushes, "
    "night sweats, broken sleep, low mood and aching joints show up. HRT is the most effective "
    "treatment for flushes and night sweats and is safe for most women, so take the symptoms to "
    "the GP and ask about it by name rather than waiting for it to be offered. Keeping up "
    "strength work and calcium with vitamin D protects the bones, and cutting alcohol and caffeine "
    "helps the flushes. You still need contraception until that year is up, and a blood test is "
    "not needed to diagnose it over 45.",
    ask=("menopause", "perimenopause", "hot flushes", "hormone replacement", "hrt"),
    # "what are the symptoms of the menopause" is the symptom card's question (health.py lists
    # them: the periods changing, the flushes, the sleep, the mood) and this card is the what-is
    # and what-to-do one
    avoid=_PREGNANT + _NOT_A_PERSON + _MONEY + ("symptoms of", "signs of", "what are the symptoms",
            "first sign", "first signs", "early signs", "list of symptoms"),
    explain=True, report=True, bias=1))
