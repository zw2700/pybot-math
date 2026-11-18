"""Everyday complaints: the small things people ask "what can I do about" and get a shrug.

A pharmacist answers most of these in a minute, and that is what the reply is: the one thing
that works, how long it takes, and the line where it stops being a self-help question. The
subject names the entry and the ask is the second signal, so "what can i do about my mouth
ulcer", "mouth ulcer wont heal" and "how do i get rid of a verruca" all reach the same answer,
while "dog bite" and "my son keeps biting" stay with the entries that own them.

The subjects here are the ones the knowledge base had no entry for at all (mouth ulcer,
athlete's foot, eczema, head lice, insect bites, a wart, toothache, nausea). The complaints it
already answered - dandruff, bloating, hiccups, hair loss, a bruise, flu, a cough that will not
go - needed only the ask words in their own keys, which they take from ASK_ABOUT in
bot/knowledge/lookup.py, so "what can i do about my dandruff" reaches the dandruff answer too.
"""

import re

from .lookup import ASK_ABOUT, TOOTH_OR_GUM, TOOTH_OUT, entry

# The red flags that make any of these a doctor's question rather than a chemist's. Kept in one
# place because the same four symptoms turn several of these entries into "go now", and a line
# that carries one is not answered here at all: the safety and body modules own it.
URGENT = ("chest pain", "cant breathe", "can't breathe", "trouble breathing", "swollen face",
          "swollen throat", "swallowing", "bleeding heavily", "wont stop bleeding",
          "won't stop bleeding", "diabetic", "diabetes", "chemotherapy",
          "dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets", "vet")

# The word filling is a cake filling, a pie filling and a sandwich filling as well.
_FILLING_FOOD = ("cake", "cakes", "cupcake", "cupcakes", "muffin", "muffins", "pie", "pies",
                     "pastry", "tart", "tarts", "quiche", "sandwich", "sandwiches", "bread", "bun",
                     "buns", "doughnut", "donut", "dumpling", "dumplings", "ravioli", "pasta",
                     "lasagne", "lasagna", "torte", "choux", "eclair", "eclairs", "icing",
                     "frosting", "buttercream", "ganache", "chocolate", "lemon", "apple", "jam",
                     "cream", "cheese", "chicken", "beef", "pork", "mushroom", "spinach", "vegan",
                     "vegetarian", "recipe", "bake", "baking", "cook", "cooking", "roast")

# What follows a tooth coming out depends on what the person is about to do, and one paragraph
# cannot lead with all six. Each opening below answers the line that was asked - smoking, rinsing,
# training, eating, bleeding, the dry socket - and they share the socket-and-clot line, so the
# answer is about their question rather than about extractions in general.
_SOCKET = ("A socket is a wound: a clot forms in the first day and it is that clot you are "
           "protecting. ")


# The treatment card is the wrong first sentence for the question a parent asks once the word has
# been said: "can my child swim with a verruca" opened with a twelve-week pharmacy course, "is a
# verruca contagious" was a search hedge, and "can he do pe with it" got nothing at all. The
# catching question and the pool question are one answer, so they lead and the treatment follows.
_WART_SPORT_WORDS = ("swim", "swimming", "swimming lessons", "pool", "pools", "pe", "gym",
                     "school", "sport", "sports", "football", "rugby", "netball", "hockey",
                     "ballet", "dance", "athletics", "sports day", "trampoline", "running club",
                     "cover", "cover it", "sock", "socks", "towel", "towels", "shower",
                     "showers", "barefoot", "share", "shoes", "changing room", "locker")
_WART_CATCHING_WORDS = ("contagious", "catching", "catch", "catch it", "infectious", "infect",
                        "pass it on", "spread to", "give it to", "get it from")
_WART_CHANGED_WORDS = ("black", "blackish", "bleeding", "bleeds", "bled", "blood", "pus",
                       "oozing", "weeping", "smelly", "smells", "changed colour", "changed color",
                       "gone dark", "going dark", "turned dark")
_WART_PREGNANT_WORDS = ("pregnant", "pregnancy", "expecting", "breastfeeding")
def _warts_verrucas(memory, understood):
    """The catching answer or the pool answer, whichever was asked, and the treatment after."""
    words = " ".join(understood.get("words") or []).lower()
    if any(word in words for word in _WART_CHANGED_WORDS):
        return ("Get that one seen rather than treating it: a wart or verruca that turns black, "
                "bleeds, or weeps is worth a GP or podiatrist appointment, because a spot that "
                "changes like that is not always a wart. Keep it clean and covered until you are "
                "seen, and don't pick, file or freeze it in the meantime.")
    if any(word in words for word in _WART_PREGNANT_WORDS):
        return ("A pharmacy salicylic acid paint or patch is usually fine in pregnancy - ask the "
                "pharmacist to check it for you - and leave the freeze kits alone for now. Don't "
                "pick or file it hard, and see a podiatrist if it is painful.")
    if any(word in words for word in _WART_CATCHING_WORDS):
        return ("Yes, mildly: a verruca passes on through the flakes of rough skin it sheds on wet "
                "floors, so keep shoes on in a changing room and don't share towels or shoes, and "
                "it can spread to another spot on your own foot or hand if you pick at it. It does "
                "not mean staying out of the pool or off PE - a waterproof plaster or a swim sock "
                "covers it, and no pool or school can insist otherwise. Treat it as usual with a "
                "pharmacy paint or patch, and see a podiatrist if it is painful or spreading.")
    if any(word in words for word in _WART_SPORT_WORDS):
        return ("No need to stay out of the water, or off PE and games, with a verruca: cover it "
                "with a waterproof plaster or wear a swim sock at the pool, keep shoes on in the "
                "changing room, and don't share towels. Keep treating it with a pharmacy paint or "
                "patch, and see a podiatrist if it is painful or spreading.")
    return ("Most warts and verrucas go on their own within a year or two, and a pharmacy "
            "salicylic acid gel or medicated plaster, used every day for up to twelve weeks after "
            "a soak and a gentle file, clears most of the rest. Don't cut, pick or freeze them at "
            "home, and cover a verruca at the pool. See a podiatrist or GP if it is painful, "
            "bleeds, or you have diabetes or poor circulation in your feet.")


# "Socket" is the word the row below needs and the word a wall has too: "do i need an electrician
# for a new socket" and "how do i replace a socket" were both a clot and a dentist, because a
# socket plus "how do i" is the row's key and nothing asked whether the socket was in a mouth. The
# row's own comment says a socket in a mouth question is the socket; this is that, enforced once,
# so the fence below does not have to guess at every word a wall can be called (it was an
# `avoid` list that missed "electrician" and "replace"). A line with no "socket" in it is none of
# this row's business here - "tooth out", "extraction" and "was pulled" are unambiguous - and
# "dry socket" names the dental one outright.
# The words that say the socket is a mouth's: the tooth words and the aftercare the row itself
# answers (a taste, a throb, a clot, a rinse). "My socket is throbbing and tastes bad" is a dry
# socket with no tooth word in it, and standing the row down for that would lose a line it gets
# right today.
_A_MOUTH_ABOUT_IT = TOOTH_OR_GUM + (
    "dry socket", "extraction", "extracted", "gum", "jaw", "mouth", "clot", "clots",
    "bleed", "bleeds", "bled", "blood", "taste", "tastes", "smell", "smells", "throb",
    "throbbing", "ache", "aches", "hurts", "sore", "heal", "heals", "healing", "numb",
    "anaesthetic", "rinse", "rinsing", "salt water", "straw", "straws", "smoke", "smoking",
    "wisdom", "filling", "gap")


def _a_socket_in_a_mouth(understood):
    """False when the socket in the line is the wall's, not the one a tooth leaves."""
    text = " ".join(str((understood or {}).get("clean")
                        or (understood or {}).get("text") or "").lower().split())
    if not text:
        text = " ".join(str(word) for word in ((understood or {}).get("words") or ())).lower()
    if "socket" not in text:
        return True
    # the socket in a face is the eye's, and it is the one socket a pain word does not make a mouth
    if re.search(r"\beyes?\b", text):
        return False
    return any(" " + word + " " in " " + text + " " for word in _A_MOUTH_ABOUT_IT)


def _after_a_tooth_out(memory, understood):
    """The one thing to do about the thing they asked about, after a tooth has come out."""
    text = ((understood or {}).get("clean") or "").lower()
    words = set(text.replace("?", " ").replace(",", " ").replace(".", " ").split())

    def says(*options):
        # A whole word, or the start of one ("smok" covers smoke, smoking and smoker), and a
        # phrase read against the text: a bare substring search read "water" as "ate" and sent
        # "the gap where my tooth was hurts with cold water" to the what-to-eat answer.
        return any((option in text) if " " in option or "-" in option
                   else any(word.startswith(option) for word in words)
                   for option in options)

    if says("smok", "vape", "vaping", "e-cigarette", "ecigarette", "cigarette", "weed", "joint"):
        return ("No smoking or vaping for at least three days, and longer if you can: the sucking "
                "and the heat are the biggest single cause of a dry socket, and it is worth more "
                "than the few cigarettes. Patches or gum are fine. Alcohol and straws are the same "
                "kind of trouble for the first day, because both pull the clot loose.")
    if says("rins", "mouthwash", "salt water", "saltwater", "salt-water", "swill", "gargl"):
        return ("Not for the first 24 hours - rinsing that early washes the clot out, and the clot "
                "is what protects the bone underneath. From tomorrow, half a teaspoon of salt in a "
                "glass of warm water, four times a day after meals, and let it fall out of your "
                "mouth gently instead of spitting. Brush the rest of your teeth as normal, just "
                "steer clear of the socket for a few days.")
    if says("exercis", "gym", "run", "runn", "lift", "weights", "swim", "football", "cycl",
            "training", "workout", "work out", "sport"):
        return ("Keep it easy for two or three days: walking is fine, but hard training, heavy "
                "lifting, swimming and anything that makes you puff can start the socket bleeding "
                "again while the clot is still settling. " + _SOCKET +
                "When you do go back, build up over a week rather than straight into a best effort.")
    if says("collects food", "collect food", "food gets stuck", "gets stuck", "traps food",
            "trapped food", "bit of food", "bits of food", "food stuck"):
        return ("A gap that keeps trapping food is worth closing even years later: the food sits "
                "there and inflames the gum around it. Until it is seen, rinse hard with warm salt "
                "water after every meal, and if that is not enough ask the dentist for a plastic "
                "syringe with a curved tip to irrigate the socket. Mention it at your next "
                "check-up - a bridge, an implant or a partial denture all stop the trapping, and "
                "the dentist can tell you which suits the gap you have.")
    # A duration, not the word "still": "i had a tooth out on tuesday and the gap still aches"
    # is two days in and normal, while a week of it is worth a look.
    if says("after a week", "a week after", "a week later", "week later", "for a week",
            "weeks after", "two weeks", "ten days", "10 days", "fortnight", "last week",
            "last month", "not healing", "not healed", "hasnt healed", "hasn't healed",
            "not getting better", "getting worse", "worse not better"):
        return ("A socket that is still aching a week or more after the tooth came out, or one that "
                "is getting worse rather than better, needs looking at rather than waiting: ring "
                "the dentist and say how many days it has been, because a dry socket, a bit of "
                "tooth or bone left in the gum and an infection all need something doing. "
                "Ibuprofen or paracetamol at the dose on the pack covers the ache until you are "
                "seen, and go the same day if there is pus, a fever or swelling in your face.")
    if says("alcohol", "beer", "wine", "pint", "vodka", "spirits", "get drunk"):
        return ("Leave alcohol alone for the first day, and longer if you can: it thins the blood "
                "and softens the clot, so the socket is more likely to ooze or to lose the clot and "
                "turn into a dry socket. Water, squash and tea that is only warm are all fine, and "
                "no straws. " + _SOCKET)
    if says("eat", "ate", "eating", "food", "chew", "chewing",
            "what can i drink", "can i drink", "coffee", "tea", "fizzy"):
        return ("Cool, soft food on the other side for a day or two: yoghurt, soup that is only "
                "warm, mashed potato, scrambled egg, a banana, and plenty to drink that is not hot. "
                "Skip anything hot, crunchy or seedy that can lodge in the socket for the first few "
                "days, and leave the straws out. " + _SOCKET)
    if says("bleed", "bled", "blood"):
        return ("Spotting blood for the first day is normal; a mouthful of fresh blood is not. Bite "
                "firmly on the gauze the dentist packed, or a folded clean handkerchief, for 20 "
                "minutes without lifting it to look, and sit up rather than lying flat. If it is "
                "still bleeding after 20 minutes of steady pressure, or the bleeding restarts later "
                "in the week, ring the dentist the same day - and 111 if you cannot reach them.")
    # A bad taste with the ache, not the word "taste" on its own: "i had a tooth out and now i
    # cant taste anything" is the anaesthetic or a bruised nerve, not a dry socket.
    if says("dry socket", "tastes bad", "taste bad", "bad taste", "foul taste", "tastes foul",
            "tastes horrible", "tastes awful", "smells bad", "smell bad", "throbbing", "throb",
            "worse not better", "getting worse", "more painful"):
        return ("That is how a dry socket reads: a dull throbbing ache that starts around day two "
                "or three, often with a foul taste or smell, because the clot has come away and the "
                "bone is exposed. It does not settle on its own - ring the dentist, who puts a "
                "medicated dressing in the socket and the pain usually eases within minutes. "
                "Ibuprofen or paracetamol at the dose on the pack covers it until you are seen.")
    if says("cant taste", "can't taste", "cannot taste", "no taste", "lost my taste", "numb",
            "numbness", "tingling", "tingles", "still asleep"):
        return ("Numbness that outlasts the appointment, or a tongue that cannot taste properly, "
                "is the local anaesthetic wearing off or a small nerve near the socket that has "
                "been bruised on the way out. It usually settles over days to a few weeks. Tell "
                "the dentist if the lip, chin or tongue is still numb after two or three days, or "
                "if it is getting worse rather than better, because a nerve that is known about "
                "early is easier to look after.")
    if says("stiff", "cant open", "can't open", "cannot open", "lockjaw", "lock jaw",
            "sore jaw", "jaw ache", "jaw aches", "jaw hurts", "jaw is"):
        return ("A stiff, sore jaw for a few days after an extraction is normal - the muscle has "
                "been held open and the injection leaves it aching - and it eases over about a "
                "week. A warm pack on the outside of the cheek, soft food, and opening the mouth "
                "gently several times a day all help; do not force it wide. If you cannot open "
                "your mouth at all, the swelling is spreading under the jaw, or you have a fever, "
                "ring the dentist or 111 the same day.")
    # The length of the visit, not the healing: "how long does a wisdom tooth extraction take" is
    # the procedure's own clock, and the healing card answered it with a fortnight of gum. Asked
    # for the wait after the event ("how long does it take to heal") the healing card keeps it.
    if (says("how long", "how soon", "how much time") and
            says("take", "takes", "last", "lasts", "appointment", "procedure", "surgery",
                 "in the chair") and
            not says("heal", "healing", "healed", "ache", "aches", "pain", "sore", "swell",
                     "swelling", "bruis", "numb")):
        return ("A single tooth is out in a few minutes once the gum is numb, and the whole "
                "appointment is about 20 to 30 minutes with the numbing and the aftercare talk in "
                "it. A wisdom tooth that has to be cut out takes longer: usually 20 to 40 minutes, "
                "and up to about an hour if it is sitting deep, so ask the dentist what yours will "
                "be. " + _SOCKET)
    if says("heal", "how long", "normal", "days", "weeks", "week", "still"):
        return ("The gum closes over in about one to two weeks and the hollow fills in over the "
                "weeks after that; a dull ache that eases day by day is normal, and paracetamol or "
                "ibuprofen at the dose on the pack is enough for it. " + _SOCKET +
                "Ring the dentist if the pain gets worse after day two rather than better, or if "
                "there is pus, a fever or swelling in your face.")
    return (_SOCKET +
            "Bite on the gauze for 20 minutes, then leave it alone: no rinsing, straws, smoking or "
            "alcohol for the first day, and cool soft food on the other side. From tomorrow, warm "
            "salt-water rinses four times a day, and paracetamol or ibuprofen at the dose on the "
            "pack. Ring the dentist if it gets worse after day two instead of better, or if there "
            "is pus, a fever or swelling in your face.")


# --- an itch down below ------------------------------------------------------
# A vulva itch and a vulva that tears are the same place and two different jobs: the itch is
# usually an irritant, and the white, thin skin that splits is lichen sclerosus, which needs a
# steroid ointment and is regularly missed for years because it is put down to thrush.
_VULVAL_ITCH_CARD = (
    "An itch around the vulva with no discharge is usually something touching the skin "
    "rather than an infection: perfumed soap or shower gel, bubble bath, wet wipes, washing "
    "powder, fabric conditioner, a panty liner, tight or synthetic knickers. Wash with plain "
    "water and no soap, wear cotton and loose clothing, change out of damp gym or swim things "
    "quickly, and skip perfumed products for a fortnight - most of it settles in days. If "
    "there is also a thick white discharge it is more likely thrush, which a pharmacy can "
    "treat with a clotrimazole pessary or cream, or a fluconazole tablet if you are not "
    "pregnant. See a GP within a couple of weeks if the skin looks white and thin, splits or "
    "tears, there is a lump or bleeding, it hurts to sit, or it has not settled after a "
    "treatment: a skin condition like lichen sclerosus needs a steroid cream, and it is often "
    "missed for years. If there is also a fever, or the skin is swollen and very painful rather "
    "than itchy, get seen the same day rather than in a fortnight.")

_WHITE_SKIN = re.compile(
    r"\b(?:white patch|white patches|white skin|skin is white|white and thin|thin skin|"
    r"tears|tearing|splits|splitting|split skin|shiny skin|tight skin|shrunken)\b")
_LICHEN_CARD = (
    "White, thin, shiny skin around the vulva that tears or splits is lichen sclerosus: a skin "
    "condition, not an infection and not an STI, and it does not clear up on its own. See a GP or "
    "a sexual health clinic rather than waiting, because a strong steroid ointment settles it and "
    "untreated it can scar and tighten the skin - and it is very often put down to thrush for "
    "years before anyone looks at the skin. Meanwhile wash with water only, no soap, wipes or "
    "douching, pat dry, and use plain petroleum jelly as a barrier. Do not use a thrush cream on "
    "it unless a doctor says so, and go back if it hurts to sit or to have sex, or if you notice a "
    "lump or a bleeding patch.")


def _vulval_skin(memory, understood):
    """The skin-that-tears card, or the itch card, chosen from the line typed."""
    said = " " + re.sub(r"[^a-z0-9' -]+", " ", str(understood.get("text") or "").lower()) + " "
    if _WHITE_SKIN.search(said):
        return _LICHEN_CARD
    return _VULVAL_ITCH_CARD

# The one appointment row answers two questions, and they want different sentences first: what a
# filling is like, and how soon you can eat after one. "can i eat after a filling" was answered
# with the card about how much you eat over a day, and the row itself never said when eating is
# allowed, so the eating line gets its own opening and the rest of the reply is the same.
_FILLING_EATING = ("eat", "eating", "ate", "drink", "drinking", "food", "chew", "chewing",
                   "meal", "lunch", "dinner", "breakfast", "bite", "can i eat", "something to eat",
                   "eat after", "eating after", "when can i eat", "before i can eat")
_FILLING_WHEN = re.compile(r"\b(?:eat|eating|ate|drink|drinking|food|chew|chewing|meal|lunch|"
                           r"dinner|breakfast|bite|snack)\b", re.I)
FILLING_APPOINTMENT = (
    "A filling is done with a local anaesthetic, so you should not feel pain during it - "
    "just pressure and the drill's noise. Mild sensitivity to cold for a few days after is "
    "normal; a bite that feels high, or pain that lasts more than a week, needs another "
    "look. On the NHS a filling is band 1, the cheapest band, unless the tooth needs a "
    "root canal, and a white filling costs more privately than a silver one and looks "
    "better in a front tooth.")
FILLING_EATING_FIRST = (
    "Once the numbness has worn off - usually two to three hours, and up to six after a "
    "lower-jaw filling - you can eat again, keeping to the other side of your mouth and to "
    "soft, lukewarm food for the rest of the day: hot drinks, hard crusts and sticky things "
    "are what hurt a fresh filling. ")


def _filling_reply(memory, reading):
    """The appointment answer, or the same answer with the eating time in front of it."""
    said = str((reading or {}).get("clean") or "").lower()
    if _FILLING_WHEN.search(said) or "something to eat" in said:
        return FILLING_EATING_FIRST + FILLING_APPOINTMENT
    return FILLING_APPOINTMENT


# A time in the line takes it off the fear answer and onto the chat that asks what scares them,
# which is right when the visit is already arranged: "im dreading the dentist tomorrow" is a person
# waiting for tomorrow, not a person asking how to get there. It is wrong when the line says they
# still have to get seen - "i need to see a dentist this week and im dreading it" was the check-up
# interval card ("Most adults are told every six months") to someone who had just said they were
# dreading it. So the time words stand this row down only when the line does not say they still
# need to get there.
_A_TIME_NAMED = re.compile(
    r"\b(?:tomorrow|today|tonight|this (?:morning|afternoon|evening|week|month)|next "
    r"(?:week|month)|later today)\b", re.I)
_STILL_TO_GET_THERE = re.compile(
    r"\b(?:need|needs|want|wants|have to|has to|got to|gotta|should i|shall i|do i|"
    r"havent|haven't|not|yet)\b[^?.]{0,30}?\b(?:see|book|booked|ring|get|go|going|"
    r"register|find)\b", re.I)


def _the_visit_is_not_arranged(understood):
    """True unless the line names a time for a visit it does not say it still has to arrange."""
    said = str(understood.get("clean") or understood.get("text") or "")
    if not _A_TIME_NAMED.search(said):
        return True
    return bool(_STILL_TO_GET_THERE.search(said))


# --- an illness with a name is that illness's card --------------------------------------
# Every one of these was a shrug or somebody else's answer on main: "what is measles",
# "how long is mumps contagious" and "what is laryngitis" reached the search hedge, "what is
# scarlet fever" and "what is glandular fever" were answered by the general what-is-a-fever
# entry, because "fever" is in that row's key and the name of the illness is not, and "what is
# hand foot and mouth" was the Raynaud's answer off the words "hand", "foot" and "cold".
#
# The shape of the answer is the same for all of them - what it is, how long it is catching,
# and when to get help - so they are one entry with one row per illness, keyed by the name of
# the illness rather than by the wording of the question, and the row's own words pick the
# reply. A parent asking "is measles dangerous" and one asking "how long off school with
# measles" want the same three facts in a different order, and both get them.
CHILDHOOD_ILLNESSES = (
    (("measles",),
     "Measles is a viral illness: a high fever, cough and sore red eyes, then a blotchy rash "
     "that starts behind the ears and spreads down the body. It is caught by coughing and is "
     "infectious from about four days before the rash until four days after it appears, and it "
     "can cause pneumonia, so ring the GP the same day rather than waiting it out. Keep a child "
     "off school for those four days, and tell the GP if a pregnant woman or anyone with a weak "
     "immune system has been in contact."),
    (("mumps",),
     "Mumps swells the salivary gland in front of the ear, so the jaw and cheek look puffy on one "
     "side or both, with fever and a headache. It spreads by coughs and saliva and is infectious "
     "from about two days before the swelling until five days after it starts; in teenagers and "
     "adults it can also inflame the testicles or the ovaries. Keep a child off school for five "
     "days from the swelling, and use cold drinks and soft food if chewing hurts."),
    (("rubella", "german measles"),
     "Rubella is a mild viral illness - a fine pink rash, tender glands behind the ears and a low "
     "fever - and in a child it is often so slight it goes unnoticed. It is infectious from about "
     "a week before the rash to six days after it, and it matters mainly because it is dangerous "
     "to an unborn baby, so anyone pregnant who has been near it should ring their midwife or GP "
     "straight away. A child stays off school for six days after the rash appears."),
    (("slapped cheek", "fifth disease", "parvovirus"),
     "Slapped cheek is a virus that gives bright red cheeks, as if the child has been slapped, "
     "sometimes with a lacy pink rash on the body and a mild fever. It is most infectious in the "
     "days before the rash shows, so by the time the cheeks are red the worst is usually over, "
     "and once the child feels well they can go back to school. Tell anyone pregnant who has been "
     "in contact, because it can affect an unborn baby."),
    (("scarlet fever", "scarletina"),
     "Scarlet fever is a bacterial infection from the same germ as strep throat: a sore throat "
     "and fever, then a rough red rash like sandpaper and a strawberry-red tongue, and it needs "
     "antibiotics. It stops being infectious 24 hours after the first dose, so ring the GP the "
     "same day - untreated it can lead to rheumatic fever. A child can go back to school a day "
     "after starting the medicine if they feel well in themselves."),
    (("whooping cough", "pertussis"),
     "Whooping cough starts like a cold, then turns into fits of coughing that end in a whoop or "
     "in vomiting, and the cough can run for two to three months. It spreads by coughing and is "
     "infectious from the first symptoms until about three weeks after the coughing fits begin, "
     "or 48 hours after antibiotics; it is most dangerous to babies under six months, so ring the "
     "GP as soon as you suspect it. A newborn who has been near a case needs telling their "
     "doctor the same day."),
    (("hand foot and mouth", "hand foot mouth", "hand foot and mouth disease", "hfmd"),
     "Hand, foot and mouth is a common virus in small children: mouth ulcers, then small spots or "
     "blisters on the palms, the soles and the nappy area, with a mild fever. It spreads by "
     "coughs, saliva and nappy changes and is most infectious in the first week, but once the "
     "child is well enough to eat and drink they can go back to nursery - there is no need to "
     "wait for the spots to go. See the GP if they will not drink at all, or are drowsy."),
    (("glandular fever", "kissing disease"),
     "Glandular fever is a viral infection with a bad sore throat, swollen glands in the neck, a "
     "fever and an exhaustion that can drag on for weeks. It spreads by saliva - bottles, cups, "
     "cutlery - and the tiredness usually eases over a month or two, though it can come back for "
     "a while. No sport or heavy lifting for about four weeks, because the spleen can swell; see "
     "the GP if swallowing is very painful, they are badly unwell, or the tiredness is not "
     "lifting."),
    (("impetigo",),
     "Impetigo is a bacterial skin infection: golden, crusty sores or blisters, usually round the "
     "nose and mouth or on the hands, and it is very infectious until the sores have crusted or "
     "48 hours of antibiotics have been taken. Keep it covered, wash your hands after touching "
     "it, and do not share towels; a pharmacist or GP can give a cream or tablets. A child stays "
     "off school until the sores are crusted or treated for two days."),
    (("laryngitis",),
     "Laryngitis is inflammation of the voice box, usually after a cold or a lot of shouting: a "
     "hoarse or lost voice, a dry tickle and sometimes a sore throat, and it settles within one "
     "to two weeks. Rest the voice - do not whisper, which strains it more than talking does - "
     "drink plenty and treat it like the cold it is. See the GP if it lasts over three weeks, or "
     "if breathing or swallowing becomes hard."),
)

# The ask is how a person writes the question: the name alone is the subject, and these are the
# words that make it a question about that subject rather than a mention of it ("my brother had
# measles in 1990" is a memory, not a request).
_ILLNESS_ASK = ("what is", "what's", "whats", "what are", "what was", "mean", "means", "meaning",
                "explain", "how long", "how many days", "contagious", "infectious", "catching",
                "catch", "catch it", "spread", "spreads", "last", "lasts", "symptoms", "symptom",
                "signs", "dangerous", "serious", "bad", "worst", "treatment", "treat", "cure",
                "rash", "spots", "blisters", "fever", "temperature", "child", "children", "kid",
                "kids", "baby", "son", "daughter", "school", "nursery", "adult", "adults",
                "i have", "ive got", "i've got", "has", "have", "got", "caught", "came down with",
                "came out in", "how do you get", "how is it", "is it", "how bad", "should i worry",
                "worried", "worry", "how long off", "off school", "back to school",
                # the yardstick in a how-long question is the illness's own timetable
                "days", "weeks", "day", "week")

# The MMR, a jab and a booster are the vaccine question and have their own answers; the animal
# disease is not this one; and a hoarse voice is the voice entry's line, not the definition.
_ILLNESS_AVOID = ("mmr", "vaccine", "vaccines", "vaccination", "vaccinated", "jab", "jabs",
                  "immunisation", "immunization", "immunise", "immunize", "booster", "side effect",
                  "side effects", "cow", "cows", "cattle", "farm", "farms", "livestock", "vet",
                  "animal", "animals", "voice", "hoarse", "croaky", "lost my voice",
                  "my voice", "singing", "singer", "shout", "shouting")


def _first_named(table, said):
    """The row whose name comes earliest in the line, or None."""
    best = None
    for names, reply in table:
        for name in names:
            at = said.find(name)
            if at >= 0 and (best is None or at < best[0]):
                best = (at, reply)
    return best[1] if best else None


def _childhood_illness(memory, understood):
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return _first_named(CHILDHOOD_ILLNESSES, said)



# The abscess answer, with the tablets read for a pregnancy.
_ABSCESS_CARD = (
    "A fever, pus or a puffy face with a bad tooth or swollen gums is a spreading dental "
    "infection, so ring a dentist today - or 111 for the out-of-hours dental service - "
    "rather than waiting for it to settle. Take paracetamol or ibuprofen at the dose on the "
    "pack, keep drinking and keep the mouth clean. Go to A&E if the swelling closes your "
    "eye or spreads down your throat, or if you cannot swallow or breathe.")


def _abscess_reply(memory, understood):
    # imported inside: health imports body and body imports this file
    from .health import tablets_for_a_pregnancy
    return tablets_for_a_pregnancy(_ABSCESS_CARD, understood)


# The toothache answer, with the tablets read for a pregnancy: "i have a toothache and im
# pregnant" was told "Take paracetamol or ibuprofen". The rest of the card is right for a
# pregnancy, so only the tablets sentence changes.
_TOOTHACHE_CARD = (
    "Take paracetamol or ibuprofen at the dose on the pack and ring a dentist the same "
    "day: toothache that wakes you, or a swelling in your face, needs a dentist rather "
    "than an antibiotic, because the tooth still has to be treated. Until then keep food "
    "off that side, brush gently, and hold a cold pack against the cheek. Go to A&E if "
    "your face or throat swells and you have trouble swallowing or breathing.")


def _toothache_reply(memory, understood):
    # imported inside: health imports body and body imports this file
    from .health import tablets_for_a_pregnancy
    return tablets_for_a_pregnancy(_TOOTHACHE_CARD, understood)


ENTRIES = [
    entry("mouth-ulcers",
          (("mouth ulcer", "mouth ulcers", "ulcer in my mouth", "ulcers in my mouth",
            "ulcer on my tongue", "ulcer on my gum", "canker sore", "canker sores",
            "sore in my mouth", "sore on my tongue",
            # a bitten tongue or lip heals the same way, and it was an echo; a cut one is the
            # same sore, and "it wont heal" is the question
            "bit my tongue", "bitten my tongue", "bit my lip", "bitten my lip",
            "bit my cheek", "bit the side of my tongue", "cut my tongue", "cut my lip"),
           ASK_ABOUT + ("sore", "painful", "hurts", "hurt", "heal", "healing", "last",
                        "lasts", "keep coming", "keeps coming",
                        # "i keep getting mouth ulcers" made a statement and asked nothing
                        "keep getting", "getting", "get them", "always", "again",
                        "eating", "speak", "talking",
                        # where it is, named instead of an ask: "mouth ulcer on my tongue"
                        "tongue", "gum", "gums", "lip", "cheek", "roof of my mouth")),
          "Most mouth ulcers heal in 7 to 10 days on their own: rinse with salt water (half a "
          "teaspoon in a glass) four times a day, use a soft brush, and a pharmacy gel or "
          "lozenge such as Bonjela or Difflam numbs it enough to eat. Skip acidic, salty and "
          "very hot food, and see a dentist or GP if one lasts more than three weeks, keeps "
          "coming back, or comes with a fever.",
          avoid=URGENT + ("stomach", "leg", "legs", "foot", "feet", "ankle", "varicose",
                          "pressure sore", "cold sore", "bleeding",
                          # the tongue the row learns to answer is the one they bit or cut
                          # themselves: a tooth that cuts it is the tooth's question, and
                          # "my tooth is sharp and cuts my tongue" is a dentist's card
                          "tooth", "teeth", "molar", "molars", "denture", "dentures",
                          "sharp")),

    entry("athletes-foot",
          (("athletes foot", "athlete's foot", "athletes' foot", "athletes foot fungus",
            "tinea pedis", "fungal infection between my toes", "itchy toes", "itchy feet"),
           ASK_ABOUT + ("itchy", "itch", "itchy toes", "smell", "smelly", "peeling",
                        "cracked", "between my toes", "feet", "foot", "treat", "clear")),
          "A pharmacy antifungal cream or spray - clotrimazole or terbinafine - clears most "
          "athlete's foot in two to four weeks, and keep using it for a week after the skin "
          "looks normal or it comes back. Dry between your toes properly, change socks daily, "
          "and dust the shoes with antifungal powder. See a GP if it has not cleared in a "
          "month, or the skin is cracked, weeping or spreading up the foot.",
          avoid=URGENT + ("mouth", "toes are numb", "numb", "corn", "bunion")),

    entry("eczema",
          (("eczema", "atopic dermatitis", "eczema flare", "eczema flare up", "dry itchy skin",
            "itchy patches"),
           ASK_ABOUT + ("itchy", "itch", "flare", "flares", "flare up", "dry", "cracked",
                        "weeping", "spread", "control", "treat", "bad", "worse", "night")),
          "Use a plain emollient two or three times a day, every day, including when the skin "
          "looks fine - that is the treatment, not a moisturiser on top of it. Wash with a soap "
          "substitute instead of soap, keep nails short, and wear cotton gloves at night if you "
          "scratch in your sleep. A GP can add a steroid cream for a flare; get one seen the "
          "same week if it is weeping, crusted yellow, or spreading fast.",
          avoid=URGENT + ("mould", "damp", "washing", "detergent", "wool"),
          # "i have eczema" states the complaint and asks nothing
          report=True),

    entry("head-lice",
          (("head lice", "headlice", "headlice treatment", "nits", "lice", "lice in my hair",
            "lice in her hair", "lice in his hair", "lice comb", "lice treatment"),
           ASK_ABOUT + ("get rid", "treat", "catch", "caught", "itchy", "itching", "scratch",
                        "kill", "comb", "school", "spread", "clear",
                        # the repeat case, which named no treatment at all: "my child keeps
                        # getting head lice" reached nothing and got a GP appointment instead
                        "keeps getting", "keep getting", "keeps catching", "keeps coming back",
                        "again", "all the time", "every term", "brought home", "brings home",
                        "in the class", "whole class",
                        # the complaint stated by the parent names the child and no treatment:
                        # "my kid has nits" was given a rest-and-fluids line and "my daughter has
                        # head lice" was told that caring is tiring. The lice word is the subject,
                        # so any verb of having is enough to make it a stated complaint.
                        "has", "have", "had", "got", "found", "caught it", "my kid", "my kids",
                        "my child", "my children", "my son", "my daughter", "my girl", "my boy",
                        "kids", "children", "daughter", "son", "toddler")),
          "Wet-comb the whole head with a fine-tooth lice comb and plenty of conditioner, "
          "section by section, every three days for two weeks: that catches the lice that hatch "
          "after the first combing. A dimeticone lotion from the pharmacy works too, by "
          "smothering them, and lice cannot become resistant to that. Check every head in the "
          "house and treat only the ones with live lice.",
          avoid=URGENT + ("dog", "cat", "pubic", "body lice", "bird"),
          # "my son has headlice again" states the complaint and asks nothing, the same shape as
          # "i have eczema" - one word is spelled as two in some houses and as one in others
          report=True),

    entry("insect-bites",
          (("insect bite", "insect bites", "midge bite", "midge bites", "mosquito bite",
            "mosquito bites", "mosquito", "mosquitoes", "midges", "horsefly bite",
            "gnat bite", "sandfly bite", "bug bites", "bitten by mosquitoes",
            "covered in bites", "eaten alive"),
           ASK_ABOUT + ("itch", "itchy", "swollen", "swelling", "sore", "treat", "stop",
                        "bites", "bitten", "bit", "prevent", "repellent", "night")),
          "Wash the bite, then hold something cold on it for ten minutes, and for the itch use "
          "a pharmacy antihistamine tablet or a hydrocortisone cream - try not to scratch, "
          "because broken skin is what gets infected. Keep them off with DEET or picaridin "
          "repellent on exposed skin and cover up from late afternoon. Get a bite seen if it "
          "spreads fast, weeps, or comes with a fever or feeling fluey.",
          avoid=URGENT + ("bite me", "bit me", "bites me", "hitting", "aggressive", "bed bug",
                          "bed bugs", "tick", "ticks", "snake", "spider", "horse", "cat",
                          "dogs", "leash", "lead")),

    entry("warts-verrucas",
          (("verruca", "verrucas", "verrucae", "wart", "warts", "plantar wart", "plantar warts",
            "wart on my foot", "wart on my hand"),
           ASK_ABOUT + ("get rid", "remove", "treat", "freeze", "spread", "spreading",
                        "painful", "hurts", "foot", "feet", "hand", "finger", "swimming",
                        # what a person asks once the word is said: whether it is catching, and
                        # whether the pool, PE and the school showers are still allowed
                        "contagious", "catching", "catch", "catch it", "infectious", "pass it on",
                        "pool", "pools", "swim", "pe", "gym", "school", "shower", "showers",
                        "barefoot", "towel", "towels", "cover", "cover it", "sock", "socks",
                        "share", "shoes", "floor", "floors",
                        # a wart that changes is a see-someone question, not a treatment one,
                        # and a pregnancy line wants the pharmacy answer
                        "black", "bleeding", "bleeds", "bled", "blood", "pus", "oozing",
                        "smelly", "pregnant", "pregnancy",
                        # "i think ive got a verruca" and "have i got a wart" name it and ask
                        # nothing else, and a person who says they have one wants the answer
                        "ive got", "i have got", "i think", "think ive", "have i", "is it",
                        "got a verruca", "got a wart", "got one", "new wart", "one on my")),
          _warts_verrucas,
          avoid=URGENT + ("toad", "witch", "cow", "cauliflower")),

    entry("toothache",
          (("toothache", "tooth ache", "tooth is killing me", "tooth hurts", "tooth pain",
            "abscess", "dental abscess", "gum abscess", "tooth infection"),
           ASK_ABOUT + ("stop", "pain", "painful", "throbbing", "hurts", "hurt", "dentist",
                        "night", "wake", "swollen", "swelling", "bad", "relief", "ease",
                        "killing", "kills", "agony", "excruciating", "dental")),
          _toothache_reply,
          avoid=URGENT + ("wisdom", "braces", "gum disease", "bleeding gums",
                          # A twinge with cold is sensitive teeth, not toothache: "my tooth hurts
                          # when i drink cold water" got the paracetamol-and-ring-today card while
                          # the sensitivity row was one word away.
                          "when i drink", "cold water", "cold drink", "cold drinks",
                          "something cold", "anything cold", "ice cream", "ice lolly",
                          "sensitive", "twinge", "twinges")),

    # A mouth is not a habit: "how do i stop bleeding gums" was answered with the stop-smoking
    # plan, because the smoking entry keys on "gum" (nicotine gum) and "stop". The two are the
    # same word to the matcher and opposite questions to a person, so the mouth gets its own row.
    entry("bleeding-gums",
          # The single gum needs its own word: "my gum is swollen" and "my gums have receded"
          # name one gum and no plural phrase, so neither reached this row at all. The bare
          # "gum" is safe here only because chewing gum, gum arabic and the gum tree are all
          # in the avoid list below.
          (("gum", "gums", "bleeding gums", "gums bleed", "gums are bleeding", "my gums bleed",
            "gum disease", "gingivitis", "sore gums", "swollen gums", "receding gums",
            "gums have receded", "gums are receding", "gums hurt", "gums are sore",
            "gums are swollen", "gums look red", "blood when i brush", "bleeds when i brush"),
           ASK_ABOUT + ("brush", "brushing", "floss", "flossing", "dentist", "hygienist",
                        "stop", "every", "when", "why", "fix", "healthy", "improve", "prevent",
                        "day", "days", "week", "weeks", "better", "sign", "cause", "bad",
                        "swollen", "sore", "hurts", "hurt", "painful", "red", "blood",
                        "bleed", "bleeds", "inflamed", "tender", "receded", "receding",
                        "shrink", "shrinking", "shrunken")),
          "Gums that bleed, swell or recede are nearly always plaque left at the gumline rather "
          "than brushing too hard: brush twice a day for two minutes with the bristles angled where tooth meets "
          "gum, and clean between the teeth once a day - small interdental brushes reach more "
          "than floss for most adults, in the size your dentist shows you. Done daily, gums that "
          "bleed stop within one to two weeks, and a little blood in the first days is normal. "
          "A hygienist removes the hard tartar you cannot brush off, and smokers and people with "
          "diabetes should go sooner because the bleeding is easy to miss. Gum that has receded "
          "does not grow back, so the point is stopping it where it is. See a dentist if one patch "
          "is swollen or tender, a tooth feels loose, or there is pus or a fever.",
          avoid=URGENT + ("denture", "dentures", "false teeth", "wisdom", "baby", "babies",
                          "teething", "toddler", "braces", "gum arabic", "chewing gum",
                          # A spreading dental infection is a red flag, and the routine paragraph
                          # must not be the answer to it: a fever, pus, a puffy face or cheek, a
                          # loose tooth or trouble swallowing all need the urgent dental card.
                          "fever", "temperature", "pus", "abscess", "abscessed", "face",
                          "cheek", "puffy", "swollen face", "swollen cheek", "swallow",
                          "swallowing", "loose tooth", "tooth is loose", "wobbly tooth")),
    # Swollen gums on their own are the gumline answer above; swollen gums with a fever, pus or a
    # puffy face are a spreading infection, and the routine paragraph is the wrong thing to read.
    # The red flag is in both the key and the ask, so "my gums are swollen" alone stays above.
    entry("dental-infection",
          (("gum", "gums", "tooth", "teeth", "dental", "mouth", "gum abscess", "dental abscess"),
           ("fever", "temperature", "pus", "abscess", "abscessed", "puffy", "swollen face",
            "swollen cheek", "swelling", "cheek", "face", "swallow", "swallowing",
            "cant swallow", "can't swallow", "spreading", "eye")),
          _abscess_reply,
          ask=("fever", "temperature", "pus", "abscess", "abscessed", "puffy", "swollen face",
               "swollen cheek", "swelling", "cheek", "face", "swallow", "swallowing",
               "cant swallow", "can't swallow", "spreading", "eye"),
          bias=3,
          avoid=("nicotine", "chewing gum", "gum arabic", "gum tree", "mouth ulcer",
                 "mouth ulcers", "cold sore", "denture", "dentures")),

    # A filling is a cake filling, a pie filling and a sandwich filling as well as a dental one,
    # so every row here carries the food words in its avoid list: the kitchen lines never reach
    # them. And a filling is four different questions, not one.
    #
    # `lost` is a filling that is out or damaged now: the gap needs covering today.
    entry("dental-filling-lost",
          (("filling", "fillings"),
           ("came out", "come out", "came off", "fell out", "fallen out", "fallen off", "lost",
            "loose", "chipped", "broke", "broken", "missing", "a gap", "the gap")),
          "Ring a dentist within a day or two: a lost or broken filling leaves the tooth tender "
          "and it can chip further, and the sooner it is replaced the simpler and cheaper it "
          "usually is. Keep the gap clean with gentle brushing, chew on the other side, skip "
          "very hot, cold or sticky food, and take paracetamol or ibuprofen if it aches. A "
          "pharmacy sells a temporary filling kit to cover it for a few days. Go straight in if "
          "the tooth is badly broken or bleeding, or your face swells.",
          # a chip in a worktop, a sink, a tile or a plate is a repair, and "how do i fill a chip
          # in a laminate worktop" was coming here for the dentist
          avoid=_FILLING_FOOD + ("worktop", "worktops", "counter", "countertop", "sink", "sinks",
                                 "basin", "bath", "enamel", "tile", "tiles", "grout", "plate",
                                 "plates", "mug", "mugs", "bowl", "bowls", "glass", "glasses",
                                 "laminate", "veneer", "stone", "granite", "quartz", "marble",
                                 "skirting", "door", "doors", "floor", "wall", "walls")),
    # `needed` is the person asking whether they need one at all, which no answer can settle:
    # "a filling is done with a local anaesthetic" is an answer to a different question, and a
    # tooth that hurts to bite, or has a hole you can see, is the only thing to go on.
    entry("dental-filling-needed",
          (("filling", "fillings"),
           ("need a filling", "needs a filling", "do i need a filling", "do i need one",
            "needs doing", "need doing", "needs replacing", "needs replaced", "needs a new",
            "need one", "needs one", "need a new")),
          "Only a dentist can say whether a tooth needs a filling: they look, and sometimes "
          "X-ray, so it is worth going if it hurts to bite or to sweet and cold, if you can see "
          "a hole or a dark patch, or if food keeps catching there. The filling itself is done "
          "with a local anaesthetic, so it should not hurt beyond pressure and the noise of the "
          "drill, and mild cold sensitivity for a few days afterwards is normal.",
          avoid=_FILLING_FOOD),
    # `cost` is a price question: the money is the first sentence, not the last clause.
    entry("dental-filling-cost",
          (("filling", "fillings"),
           ("cost", "costs", "price", "how much", "expensive", "cheap", "cheapest")),
          "On the NHS in England a filling is band 1, about £28 for the course of treatment "
          "including the check-up, and it is free in Scotland and Wales if you see an NHS "
          "dentist there; a root canal is band 3, about £320. A white composite filling often "
          "costs more than a silver amalgam one on the NHS and is usually only offered on a "
          "front tooth. Privately, expect roughly £60 to £150 for a white filling.",
          avoid=_FILLING_FOOD),
    # `question` is the appointment itself, asked before it or after it. The bare words for
    # pain are deliberately not in the key: a filling already in the tooth that hurts is decay
    # under it or a bite that is too high, and that line belongs to the dentist toothache answer.
    entry("dental-filling-lifespan",
          # The key of the appointment row used to carry "how long" and "last" as well, and this
          # question got the anaesthetic answer, which never says how long anything lasts.
          (("filling", "fillings"),
           ("how long", "how many years", "last", "lasts", "lifespan", "years")),
          "A white composite filling lasts about five to seven years and a silver amalgam ten to "
          "fifteen, and a well-looked-after one can go a lot longer. Grinding your teeth, fizzy "
          "drinks and a sweet tooth all shorten it; a filling that chips, feels high or hurts to "
          "bite wants another look.",
          # a "how long" line that is about pain is the appointment row's ("how long will my
          # filling hurt"), and a cake filling is nobody's here
          # "take" is the other half of the same words: "how long does a filling take" is the
          # length of the appointment, not how long the filling lasts in the tooth, and this
          # answer ("five to seven years") was given to it. The visit's length belongs to the
          # dentist appointment answer, so the durability card stands down for the ask that
          # says the doing rather than the thing.
          avoid=_FILLING_FOOD + ("hurt", "hurts", "pain", "painful", "sore", "sensitive", "numb",
                                 "appointment", "dentist",
                                 "take", "takes", "taking", "in the chair", "procedure")),

    entry("dental-filling-question",
          (("filling", "fillings"),
           ("painful", "does a filling hurt", "is a filling painful", "will it hurt",
            "hurt having", "a filling hurt", "filling be painful", "sensitive afterwards",
            "sensitive after a filling", "numb", "afterwards", "will my filling hurt",
            "will a filling hurt", "will it hurt",
            "after a filling", "the appointment", "what happens", "white or silver",
            "white filling", "silver", "amalgam")),
          _filling_reply,
          avoid=_FILLING_FOOD),

    # What a crown or a root canal costs had no row: the answer was "Prices move too fast for me
    # to know. A quick look at the seller's own site", which is a shop. The NHS bands are fixed
    # prices, not live ones, so this is a fact the bot can hold.
    # The hole, the crumbling edge and the grey tooth after a knock are already answered by
    # `tooth-hole` in health.py, which has the decay reading and the sharp-edge line, so
    # this module keeps out of them and answers the denture that will not stay in.
    entry("dental-dentures-loose",
          (("denture", "dentures", "false teeth", "dental plate",
            "partial denture", "partial dentures", "upper denture", "lower denture",
            "my teeth are false", "my teeth arent mine", "my teeth aren't mine",
            # "my plate" alone is a dinner plate as often as a denture, so only the shapes that
            # can only be about the mouth are keys here: "my plate cracked" keeps the china
            # answer it had, and "my plate is loose" is a denture that wants a reline.
            "my plate is loose", "my plate keeps falling", "my plate falls out",
            "my plate wont stay", "my plate won't stay", "my plate rubs", "my plate hurts",
            "my plate wobbles", "my plate doesnt fit", "my plate doesn't fit",
            "my plate moves"),
           ("falling out", "falls out", "fall out", "fell out", "wont stay", "won't stay",
            "wont stay in", "won't stay in", "keeps coming out", "keeps falling out",
            "loose", "wobble", "wobbly", "rocking", "rubbing", "rubs", "sore", "sore spot",
            "hurts", "hurt", "uncomfortable", "click", "clicking", "moving",
            "talk", "talking", "eat", "eating", "new ones", "new set",
            "cracked", "crack", "cracks", "broken", "broke", "snapped", "repair", "mended",
            # a denture slipping while you speak is the fit, not a stammer: the talking rows
            # would otherwise take the line
            "falling out when i talk", "fall out when i talk", "slip when i talk",
            "slipping when i talk", "move when i talk", "clicking when i talk",
            # a sore gum under a plate is the plate, and the bleeding-gums row has "gum" in its
            # key: the phrase is what makes the line a denture question
            "hurts my gum", "hurts my gums", "sore under my plate", "sore spot under",
            "sore spot under my plate", "rubs my gum", "rubbing my gum",
            "dont fit", "don't fit", "doesnt fit", "doesn't fit", "fit properly", "fit right",
            "too tight", "too loose", "too big", "too small", "hurt to wear", "painful")),
          "Dentures that will not stay in are a fit problem, and the fix is at the dentist or "
          "the clinical dental technician who made them: ask for a reline or an adjustment, "
          "which is quick and often free within the first year. Until then a thin smear of "
          "fixative - not a thick line - holds them for the day, and taking them out at night "
          "gives the gum a rest. A sore spot under a denture usually settles in a few days once "
          "you leave them out overnight; one that is still there after a week, or a white patch "
          "or lump under the plate, should be looked at rather than filed down at home. A "
          "cracked or snapped one can be repaired: take both pieces to the technician rather "
          "than gluing it, because superglue makes a proper mend harder.",
          avoid=("price", "cost", "how much", "quote", "afford", "nhs band", "cleaning",
                 "clean", "sterilise", "sterilize", "glue", "superglue", "vase", "teeth "
                 "whitening", "lump under", "sink",
                 # a plate on the table: china, oven, dishwasher, the floor
                 "dropped", "floor", "dish", "dishes", "china", "oven", "dishwasher",
                 "microwave", "casserole", "dinner", "side plate", "tea plate")),

    entry("dental-crown-cost",
          (("crown", "crowns", "root canal", "root canal treatment", "bridge", "bridges",
            "veneer", "veneers", "denture", "dentures", "inlay", "onlay", "implant",
            "implants", "implant tooth"),
           ("cost", "costs", "price", "prices", "how much", "expensive", "cheap",
            "cheapest", "charge", "pay", "paying", "quote", "quoted", "afford")),
          "On the NHS in England a crown is band 3, about £325, and that one charge covers the "
          "whole course of treatment; a root canal is band 2 (about £75) on a front tooth and "
          "band 3 (about £325) on a back one, and a set of dentures is band 3 as well, so ask "
          "which band you are in before any work starts. Privately, "
          "expect roughly £500 to £800 for a crown, £300 to £700 for a root canal, £300 to £500 a "
          "veneer, £200 to £400 a bridge unit, and £2,000 to £2,500 for an implant including its "
          "crown, which is private work only. A written quote is normal, and nobody can price a "
          "tooth without seeing it; an NHS crown costs the same whatever tooth it is on.",
          # a crown is also a monarchy, a paper hat and a coin, and none of those cost a dentist
          avoid=("the crown", "crown estate", "crown jewels", "crown jewel", "king", "queen",
                 "royal", "royals", "monarchy", "throne", "paper crown", "christmas",
                 "birthday", "party", "gold", "golden", "tooth fairy", "chewing gum"),
          bias=2),

    entry("hair-loss-minoxidil",
          # The bald entry in science.py explains why it happens; this one is the person asking
          # what to do about it, which is a different question with a real answer.
          (("hair loss", "losing my hair", "my hair is falling out", "thinning hair",
            "balding", "going bald", "receding hairline"),
           ASK_ABOUT + ("stop", "slow", "regrow", "grow back", "treatment", "treat", "help",
                        "prevent", "much", "fast", "suddenly", "women", "woman", "man", "men")),
          "Two things are worth trying for common hair loss: minoxidil lotion or foam, bought "
          "over the counter and used twice a day, and for men a GP can prescribe finasteride - "
          "both only work while you keep using them, and both take three to six months to show. "
          "Sudden patches, loss with an itchy scaly scalp, or loss with tiredness or weight "
          "change is worth a GP visit, because that has a cause worth testing for.",
          # a line that blames dandruff for the hair is the dandruff answer's, and so is a
          # flaky scalp that is not otherwise described as hair loss
          avoid=URGENT + ("dandruff", "scalp", "flakes", "flaky", "itching scalp",
                          "washing", "shampoo", "hair dye", "wig", "haircut", "grey",
                          "greying")),

    entry("flu-at-home",
          (("flu", "influenza", "the flu", "proper flu", "flu symptoms", "have flu",
            "got the flu", "down with flu"),
           ASK_ABOUT + ("symptoms", "symptom", "high temperature", "fever", "aching", "aches",
                        "shivery", "rest", "better", "recover", "recovery", "days", "week",
                        "off work", "bed")),
          "Flu is rest and fluids for most people: stay in bed while the fever lasts, drink more "
          "than you think you need, and take paracetamol or ibuprofen for the aches at the dose "
          "on the pack. Expect two or three bad days and a tired week. Ring a GP or 111 the same "
          "day if you are breathless, have chest pain, cannot keep fluids down, or are pregnant, "
          "over 65 or have a long-term condition.",
          # "virus" and "cold" are in other entries' keys, and a laptop virus or a cold is not
          # this entry's line ("i cant breathe with this cold" is the safety module's).
          # a question about how long flu lasts is the recovery entry's, which says what drags
          # on and for how long; this one is what to do while it is happening
          avoid=URGENT + ("virus", "laptop", "computer", "pc", "phone", "stomach",
                          "norovirus", "covid", "test", "jab", "vaccine", "vaccination",
                          "cold", "colds", "chickenpox", "how long", "last", "lasts",
                          "lasting", "when will i",
                          # "can you get flu twice" is the cold-or-flu comparison, not this
                          "twice", "again", "second time", "one after another")),

    entry("nausea",
          (("nausea", "nauseous", "queasy", "feel sick all the time", "feeling sick all the time",
            "constant nausea", "nausea and vomiting"),
           ASK_ABOUT + ("stop", "constant", "morning", "all the time", "help", "ease",
                        "settle", "relief", "eat", "keep food down")),
          "Sip small amounts of water or a rehydration drink often rather than a glass at once, "
          "and eat something dry and plain - toast, crackers, a plain biscuit - before you get "
          "up if mornings are the worst. Ginger, in tea or a biscuit, settles some people. Ring "
          "a GP if it lasts more than a couple of days, if you cannot keep any fluid down, or "
          "if you are pregnant, on new medicine or have a head injury.",
          avoid=URGENT + ("car", "boat", "plane", "travel", "hangover", "chemo",
                          "morning sickness", "vomit blood", "blood")),

    # Two complaints that start with "i keep getting": the answer is not the one-off trip to the
    # pharmacy but how to stop the thing coming back, and when it stops being a pharmacy job.
    entry("cystitis",
          (("cystitis", "uti", "utis", "urine infection", "urinary infection", "water infection",
            "bladder infection", "infection in my waterworks"),
           ASK_ABOUT + ("keep getting", "keep coming", "always", "again", "think i have",
                        "have i got", "is this", "symptoms", "symptom", "burning", "stings",
                        "sting", "blood", "painful", "days", "cranberry", "contagious")),
          "Drink plenty of water, take paracetamol and pee when you need to rather than holding "
          "on - most cystitis in women settles in a day or two. See a GP or pharmacy the same "
          "day if it lasts over three days, comes with blood, a fever or back pain, or if you "
          "are pregnant, a man or a child. Three or more in a year is worth a GP review.",
          avoid=URGENT + ("dog", "cat", "stoma", "catheter")),

    entry("burning-when-peeing",
          # The symptom said out loud with no name on it: "it stings when i pee" is the same
          # question, and the two words the key needs are the burning and the peeing.
          (("burning", "burns", "burn", "stinging", "stings", "sting", "hurts", "hurting",
            "sore", "painful", "agony"),
           ("pee", "pees", "peeing", "peed", "wee", "wees", "weeing", "urine", "toilet",
            "loo", "loos", "lav")),
          "That is usually cystitis: drink plenty of water, take paracetamol and pee when you "
          "need to rather than holding on, and most cases settle in a day or two. See a GP or "
          "pharmacy the same day if it lasts over three days, comes with blood, a fever or back "
          "pain, or if you are pregnant, a man or a child. Three or more a year is worth a GP "
          "review.",
          avoid=URGENT + ("mouth", "throat", "eyes", "eye", "skin", "hand", "hands", "stomach",
                          "belly", "back", "ear", "ears", "nose", "breast", "nipple",
                          "child", "children", "kid", "kids", "son", "daughter", "baby",
                          "finger", "fingers", "toe", "toes", "foot", "feet", "leg", "legs")),

    entry("threadworms",
          (("threadworms", "threadworm", "pinworms", "pinworm", "worms", "itchy bottom",
            "itchy bum", "itchy backside", "worms in my poo"),
           ASK_ABOUT + ("how do i", "get rid", "treat", "treatment", "keep getting", "child",
                        "children", "kid", "kids", "daughter", "son", "girl", "boy",
                        "little girl", "little boy", "baby", "babies", "toddler", "have", "got",
                        "tablet", "medicine", "spread", "night", "itch", "itchy", "scratching",
                        "family", "house", "keep coming back", "coming back", "again",
                        "didnt work", "not worked", "still there", "still got")),
          "Threadworms look like tiny white threads in the poo or around the bottom, and the "
          "itch is worst at night. A pharmacy mebendazole tablet or chew for everyone in the "
          "house, repeated in two weeks, clears them: wash hands and nails before food, shower "
          "in the morning rather than at night, and wash bedding and towels hot. Under six months, ask the "
          "pharmacist. If they come back after the second dose, see a GP.",
          avoid=URGENT + ("dog", "cat", "compost", "soil", "garden", "lawn", "pond", "bird",
                          "birds", "fish", "horse", "rabbit", "hamster", "fishing", "bait")),

    # An itch down below with nothing to see was a reflective question on main: "my vagina
    # itches", "my vulva is itchy", "my labia is itchy", "my fanny itches", "my privates itch",
    # "my crotch itches", "i am itchy down there", "i have an itch in my vagina" all got
    # "That sounds wearing. Is it getting better, worse, or about the same?". Only the phrase
    # "itchy down below" reached the thrush card, and thrush is only one of the causes.
    entry("vulval-itch",
          (("vagina", "vaginal", "vulva", "vulval", "labia", "fanny", "privates", "private parts",
            "down there", "down below", "crotch", "front bottom", "my bits", "lady bits",
            "genitals"),
           ("itch", "itches", "itchy", "itching", "sore", "burning", "irritated", "irritation",
            "uncomfortable", "red", "swollen", "chafing",
            # the skin condition, said the way people say it: white patches, thin skin, skin that
            # splits and tears ("my vulva has white patches that tear" was the darning card)
            "white patch", "white patches", "white skin", "thin skin", "tears", "tearing",
            "splits", "splitting", "split skin", "shiny",
            # "my vulva skin is white and thin" names the skin, not a symptom: the phrase has to
            # be in the key or the row never sees it
            "white and thin", "thin and white", "skin is white", "skin has gone white",
            "looks white", "white and shiny")),
          _vulval_skin,
          # discharge lines belong to the thrush card, a bottom itch is threadworms or the
          # bathroom, and a mouth or a nappy is not this question
          avoid=URGENT + ("mouth", "oral", "tongue", "baby", "babies", "nappy", "nipple",
                          "breastfeeding", "bottom", "bum", "anus", "anal", "arse", "back passage",
                          "penis", "testicle", "scrotum", "discharge", "dog", "cat", "pet"),
          bias=1),

    entry("thrush",
          (("thrush", "yeast infection", "candida", "itchy down below", "itching down below",
            # the discharge is what tells thrush apart from an ordinary itch, and described
            # plainly it reached a reflective question: "my vagina itches and there is white
            # discharge"
            "white discharge", "thick white discharge", "cottage cheese discharge",
            "discharge and itch", "itch and discharge"),
           ASK_ABOUT + ("keep getting", "keep coming", "again", "treat", "tablet", "cream",
                        "pessary", "first time", "pregnant", "symptoms", "symptom", "discharge",
                        "itchy", "itch", "sore", "contagious", "catch", "pass on", "sex",
                        "normal", "cause")),
          "Thrush is an itch and a thick white discharge, and a pharmacy can treat it: a "
          "clotrimazole pessary or cream, or a fluconazole tablet if you are not pregnant. Wear "
          "cotton and loose clothing, wash with water only, and don't use perfumed soap or "
          "douches. See a GP if it is your first time, you get it four or more times a year, you "
          "are pregnant, or there is pain or bleeding.",
          avoid=URGENT + ("baby", "babies", "mouth", "nappy", "nipple", "breastfeeding")),

    # --- the mouth questions that were a shrug or the wrong answer entirely --------------------
    # "my teeth hurt when i drink cold water" was answered with the cold and flu paragraph, because
    # every word in it belongs to a cold apart from the mouth. Sensitive teeth is the question, and
    # it has a known answer.
    entry("sensitive-teeth",
          (("sensitive teeth", "teeth are sensitive", "teeth sensitive", "sensitive tooth",
            "teeth hurt when i drink", "teeth hurt with cold", "tooth hurts when i drink",
            "pain when i drink cold", "sensitive to cold", "sensitive to hot",
            "hurts to eat ice cream", "wince when i drink", "tooth is sensitive",
            # The phrase shapes people actually type, which the first list missed because it
            # wanted "drink" straight after "when i": "my teeth hurt when i have a cold drink"
            # and "my filling hurts when i drink something cold" reached no answer at all.
            "teeth hurt", "tooth hurts", "teeth ache", "tooth aches", "my filling",
            "filling hurts", "hurts when i drink", "hurts when i eat", "hurts when i bite",
            "hurts with cold", "hurts with hot", "hurts to drink", "hurts to eat",
            "sensitive to cold drinks", "twinge with cold"),
           ASK_ABOUT + ("teeth", "tooth", "mouth", "cold", "hot", "sweet", "drink", "drinking",
                        "eat", "eating", "brush", "brushing", "why", "stop", "help", "fix",
                        "dentist", "toothpaste", "enamel", "gum", "gums", "receding", "worn",
                        "grinding", "whitening", "hurt", "hurts", "pain", "painful", "ache",
                        "aches", "sharp", "twinge", "twinges")),
          "Teeth that twinge with cold are usually worn enamel or a gumline that has receded, "
          "which leaves the softer dentine underneath exposed. Start with a sensitive toothpaste "
          "(the ones with stannous fluoride or arginine) and use it as your everyday paste, "
          "spitting rather than rinsing afterwards so it stays on the teeth. Brush gently with a "
          "soft brush, wait an hour after acidic food or drink before brushing, and ask your "
          "dentist about a fluoride varnish or a filling over the exposed patch. Go sooner if the "
          "pain lasts more than a few seconds after the cold is gone, or if one tooth aches on "
          "its own at night, because that is more than sensitivity.",
          # not the bare word "teething": it is a loose form of "teeth", and it shut every
          # "my teeth ..." line out of this entry
          avoid=URGENT + ("wisdom", "braces", "baby", "babies", "is teething", "baby teething", "toddler", "child",
                          "children", "dog", "cat", "denture", "dentures", "false teeth",
                          "sensitive skin", "sensitive subject", "sensitive data",
                          # A twinge with cold is worn enamel; pain on sweet or sugary food is
                          # decay, and that one needs the dentist today. "hurts when i eat" is in
                          # this key with no qualifier, so the sweet lines were landing here.
                          "eat something sweet", "eats sweet", "eat sweet", "eating sweet",
                          "eating sweets", "eats sweets", "after eating sweet", "after sweets",
                          "eat chocolate", "eating chocolate", "eat anything", "hot food")),

    # "my breath smells" and "bad breath" were a shrug and an echo: an everyday thing with a
    # known cause and a known fix.
    entry("bad-breath",
          (("bad breath", "breath smells", "breath stinks", "smelly breath", "breath is bad",
            "halitosis", "my breath", "morning breath", "breath like",
            # the complaint without the word breath in it: "my mouth smells" was an echo, and it
            # is the same question. A phrase rather than the bare word "mouth", which belongs to
            # the ulcers, the sore mouth and the tooth answers too.
            "mouth smells", "mouth stinks", "smelly mouth", "mouth smells bad",
            "my mouth smells", "mouth is smelly", "mouth tastes bad"),
           ASK_ABOUT + ("bad", "smell", "smells", "stinks", "how do i", "stop", "fix", "why",
                        "cause", "help", "mouthwash", "gum", "gums", "tongue", "dentist",
                        "brush", "brushing", "floss", "always", "worse", "morning", "get rid")),
          "Most bad breath is bacteria on the tongue and between the teeth, not the stomach: "
          "brush twice a day, clean between the teeth once a day, and gently brush or scrape the "
          "back of the tongue. Drink water through the day, because a dry mouth is the other "
          "common cause, and cut back on coffee, alcohol and smoking. A mouthwash helps for an "
          "hour or so but does not fix the cause, and alcohol-heavy ones dry the mouth further. "
          "See a dentist if it persists after a fortnight of that, or comes with bleeding gums, a "
          "bad taste, or a tooth that hurts - gum disease and a decaying tooth both need treating "
          "rather than covering.",
          # morning breath has its own, more specific answer on main, and it is the better one
          avoid=URGENT + ("morning", "overnight", "wake up with", "woke up with",
                          # a mouth that smells of blood is a bleeding question, not a breath one
                          "blood", "bloody", "bleeding",
                          "dog", "cat", "puppy", "kitten", "horse", "budgie", "breath test",
                          "breathalyser", "breathless", "short of breath", "out of breath",
                          "cant breathe", "can't breathe", "baby", "babies", "is teething",
                          "baby teething", "toddler",
                          # garlic breath is its own row below: it does not come from the tongue,
                          # so the gum-and-brushing answer is not its answer
                          "garlic", "garlicky", "garlicy", "onion", "onions")),

    # Garlic breath is not bad breath: nothing on the tongue is the cause, so the gumline answer
    # answers a different question. "how do i get rid of garlic breath" was a shrug, and "how to
    # get rid of garlic breath fast" was told how to peel a clove.
    entry("garlic-breath",
          (("garlic", "garlicky", "garlicy", "onion", "onions", "raw onion"),
           # The second group is the breath itself, not the asking: with "why" and "how long" in
           # it this row took "why does garlic burn" and "is green garlic safe to eat".
           # Every word here names the breath itself. The speed and duration words that used to
           # sit in this group ("last", "lasts", "how long", "fast", "quick", "stays") are not
           # about a smell at all: "last time" and "why does garlic burn so fast" are the cooking
           # question, and with a bias of two they carried this row over the burn row's answer.
           # "how long does garlic breath last" still reaches it, because it says "breath".
           ("breath", "bad breath", "breathe", "breathing", "smell", "smells", "smelly",
            "stinks", "stink", "get rid of", "rid of the smell", "rid of it", "mask", "hide",
            "cover up", "gone", "goes away", "went away", "lingers", "lingering", "cure")),
          "You cannot brush garlic or onion breath away, because the smell is not on your tongue: the "
          "sulphur compounds are absorbed into the blood and come out on your breath from the "
          "lungs, so it fades over about a day whatever you do. What helps is at the meal - milk, "
          "an apple, parsley, mint or green tea blunt the compounds before they get into the blood, "
          "and cooking the garlic less hard helps too. Afterwards, brush, scrape the tongue, floss "
          "and drink water, which is good for the mouth anyway; mints and mouthwash cover it for "
          "twenty minutes. If your breath smells of garlic when you have eaten none, that is a "
          "dentist or GP question rather than this one.",
          # the food answers keep their own line: how to peel, crush, store or cook garlic, and
          # how long a bulb keeps
          # A clove that burned is the burn row's question, and it needs no fence here: with the
          # speed and duration words gone from the key above, "i burnt the garlic last time" and
          # "why does garlic burn so fast" name no breath at all, so this row cannot take them.
          # A fence on "burnt" would be wrong in the other direction - "does burnt garlic give you
          # bad breath" is a breath question and the burn row stands down for it.
          avoid=URGENT + ("peel", "peeling", "peeled", "crush", "crushed", "crushing", "chop",
                          "mince", "grow", "growing", "plant", "planting", "keep", "keeps",
                          "keeping", "store", "storing", "stored", "freeze", "frozen", "bulb",
                          "bulbs", "clove", "cloves", "sprout", "sprouts", "green",
                          "recipe", "sauce", "bread", "butter", "roast", "oil", "how much",
                          "how many", "how long to cook", "substitute", "instead", "powder",
                          "paste", "fridge", "chicken", "pasta", "curry", "soup", "dish",
                          # the hands and the board are the garlic-hands row's question
                          "hands", "hand", "fingers", "fingertips", "skin", "on my hands",
                          "off my hands", "board", "chopping board", "kitchen", "knife",
                          "gloves", "sink",
                          # the garden's garlic: "when do i lift my garlic" was told how to
                          # stop garlic breath
                          "lift", "lifting", "harvest", "harvesting", "when do i", "sow",
                          "sowing", "yellow", "leaves", "allotment", "garden", "bed", "crop",
                          "this year", "ready"),
          bias=2),

    # "my wisdom tooth is coming through" was a shrug. It is a common, specific worry with a
    # specific answer: how long it takes, what helps, and the three things that mean a dentist.
    entry("wisdom-tooth",
          (("wisdom tooth", "wisdom teeth", "back tooth", "back molar", "molar coming",
            "tooth coming through", "gum flap", "pericoronitis"),
           ASK_ABOUT + ("coming", "coming through", "hurts", "hurt", "pain", "painful", "sore",
                        "swollen", "swelling", "how long", "normal", "impacted", "take out",
                        "remove", "removed", "extraction", "dentist", "ache", "aches",
                        "bleeding", "gum", "gums", "chew", "chewing", "jaw")),
          "A wisdom tooth coming through usually takes a few weeks of aching and swelling at the "
          "back of the gum, worst in the late teens and twenties, and it often settles on its "
          "own. Rinse with warm salt water three or four times a day, keep the area clean with a "
          "small brush, and take paracetamol or ibuprofen at the dose on the pack if it is sore. "
          "See a dentist if the gum over it stays swollen and traps food, if the pain spreads to "
          "your ear or jaw, if you cannot open your mouth properly, or if there is a fever or pus "
          "- that is an infection under the flap rather than teething. A dentist decides whether "
          "it has to come out, and most do not.",
          # This row used to stand down the moment the line said "hurts", on the reasoning that a
          # hurting tooth is the toothache answer. But a wisdom tooth arriving is sore for weeks
          # and there is real advice for it, while "my wisdom tooth is coming through and hurts"
          # had no answer at all. The toothache row still keeps its own lines, which name an ache
          # or a bite rather than a tooth arriving.
          avoid=URGENT + ("toothache", "abscess", "gum boil",
                          "baby", "babies", "is teething", "baby teething", "toddler", "child",
                          "children", "dog", "cat", "puppy", "denture", "dentures")),

    # A tooth that has just come out had no answer at all: the socket, the clot, the first day of
    # not rinsing and the dry socket are one story, and every word in the question belonged to
    # another row. `TOOTH_OUT` in lookup.py is the fence the rows either side stand down on.
    entry("after-a-tooth-out",
          (("tooth out", "teeth out", "tooth removed", "teeth removed", "tooth pulled",
            "tooth extraction", "extraction", "extractions", "tooth taken out",
            "teeth taken out", "had a tooth", "had my tooth", "had two teeth", "had teeth",
            "gap where", "where my tooth", "where the tooth", "the socket", "dry socket",
            "wisdom tooth out", "wisdom teeth out", "wisdom tooth removed",
            # Not "after a tooth" or "after the extraction": "after" and "a" are words another
            # dental row's phrase already uses ("after a filling" in dental-filling-question), and
            # a word two entries use stops being specific, which cost that row a rank point and
            # handed "how long after a filling can i eat" to the pie-filling answer.
            # "my socket is throbbing and tastes bad" reached no row at all. A socket in a mouth
            # question is the socket; the plug-and-wall uses are fenced below.
            "socket", "my socket", "the socket is",
            # The passive shapes people type: "my tooth was pulled out this morning" and "i had
            # a tooth pulled yesterday" reached no row at all, because the key wanted "tooth
            # pulled" and the line says "tooth was pulled".
            "was pulled", "was taken out", "was removed", "been pulled", "been taken out",
            "hole in my gum", "hole in the gum", "hole closes", "hole closed", "hole close"),
           ("still", "heal", "healing", "healed", "heals", "ache", "aches", "aching", "hurt",
            "hurts", "hurting", "pain", "painful", "sore", "bleed", "bleeding", "bled", "eat",
            "eating", "food", "drink", "drinking", "rinse", "rinsing", "salt water", "mouthwash",
            "smoke", "smoking", "cold", "hot", "throbbing", "tastes", "taste", "smell", "swollen",
            "swelling", "infection", "pus", "exercise", "gym", "run", "jaw", "stiff", "brush",
            "brushing", "normal", "days", "week", "weeks", "dentist", "worried", "worry",
            "how long", "how do i", "how can i", "can i", "should i", "is it", "what can i",
            "what should i", "when can i", "do i",
            # a day and a time of day say the socket is fresh, which is what this row is for
            "morning", "afternoon", "evening", "yesterday", "today", "tonight", "last night",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")),
          _after_a_tooth_out,
          bias=1,
          guard=_a_socket_in_a_mouth,
          # the cost and the complaint about a dentist are other answers, and a child's, a dog's
          # or a denture wearer's mouth is somebody else's line again
          avoid=("cost", "how much", "price", "expensive", "free", "nhs", "private", "quote",
           # a cold the person has is the cold's own answer, even when a tooth is in the line
           "i have a cold", "ive got a cold", "i ve got a cold", "now i have a cold",
           "got a cold", "have had a cold", "chesty", "sneezing", "runny nose", "sore throat",
           # and a socket in a wall is an electrician's
           "plug", "plug socket", "wall socket", "electric", "electrical", "usb", "charger",
           "power", "extension", "bulb", "wiring", "fuse",
           "complain", "complaint", "refund", "negligence", "solicitor", "compensation",
           "baby", "babies", "toddler", "child", "children", "kid", "kids", "son", "daughter",
           "dog", "dogs", "cat", "cats", "puppy", "kitten", "horse",
           "denture", "dentures", "false teeth", "braces", "implant", "veneer", "whitening",
           # whether an extraction is safe in pregnancy is a question for the dentist and the
           # midwife, not aftercare
           "pregnant", "pregnancy", "expecting a baby",
           # a line that names something to read or watch is not about a mouth
           "book", "books", "novel", "read", "reading", "film", "films", "series", "podcast",
           "documentary", "watch",
           "wisdom tooth coming", "tooth coming through",
           # "do i need to take my wisdom teeth out" is the question of whether the tooth should
           # come out at all, and that decision has its own row: these are the shapes of it.
           "need to take", "need it out", "need them out", "need my tooth out",
           "need my teeth out", "take it out", "take them out", "taking it out",
           "taking them out", "have it out", "have them out", "get it out", "get them out",
           "should i have my", "should i have it", "should i have a tooth", "worth having",
           "better to have it out", "leave it alone")),

    # "im putting off going to the dentist" was "Got it." - the thing people actually want is
    # what the visit involves and how to say they are frightened.
    entry("dentist-avoidance",
          (("dentist", "dental", "check up", "checkup", "hygienist"),
           ("putting off", "avoiding", "dreading", "scared", "afraid", "terrified", "nervous",
            "anxious", "embarrassed", "ashamed", "guilty", "phobia", "dont want to go",
            "don't want to go", "hate going", "cant face", "can't face")),
          "Book the check-up and say on the phone that you are nervous and have not been for a "
          "while - practices hear it every week, and most will give you a longer first "
          "appointment, a signal to stop, and no lecture. The first visit is usually a look round "
          "and an x-ray, nothing more, and you can agree to one small thing at a time. If it "
          "helps, take headphones, agree a hand signal for a pause, and go in the morning when "
          "you are less tired. Ring the same week if a tooth is painful, a filling has come out "
          "or your gums bleed a lot, because those are quicker to fix early.",
          # how often to go is its own answer, and "i havent been in years" is that question.
          # Nerves about an appointment that is already booked, tomorrow, are the nerves: the
          # chat module holds that line on purpose (tests/test_health.py), and it is right - the
          # person is not asking how to book, they are dreading tomorrow.
          # The fear of the visit outranks the steps to being seen: "i have booked a dentist and
          # im terrified" was answered "ring the practice and ask for an urgent slot ... saying
          # it hurts" to a person who had booked and said nothing about pain.
          bias=1,
          # the time of the visit is not a stand-down on its own: see `_the_visit_is_not_arranged`
          guard=_the_visit_is_not_arranged,
          avoid=URGENT + ("havent been", "haven't been", "not been", "never been", "years",
                          "ages", "how often", "how long since",
                          "toothache", "abscess", "filling fell out", "filling came out",
                          "wisdom", "braces", "denture", "dentures", "dog", "cat", "cost",
                          "price", "how much", "nhs band", "insurance", "teeth whitening",
                          "whiten", "grind", "night guard")),

    # Three complaints that came back as "A pharmacist or your GP can answer that today": a
    # referral with nothing in it. They are the everyday pharmacist questions, so each gets the
    # one thing that works, how long it takes and the line where it stops being a chemist's.
    entry("jock-itch",
          (("jock itch", "tinea cruris", "itchy groin", "rash in my groin", "groin rash",
            "itchy balls", "itchy scrotum", "itchy inner thighs", "fungal rash in my groin"),
           ASK_ABOUT + ("itchy", "itch", "rash", "red", "spreading", "clear", "keep coming back",
                        "sweaty", "gym")),
          "Jock itch is a fungus in the crease of the groin: a pharmacy antifungal cream - "
          "clotrimazole or terbinafine - twice a day for two weeks, and carry on for a week after "
          "the rash has gone or it comes back. Wash and dry the crease first, wear loose cotton "
          "and change pants daily, and wash gym kit hot. See a GP if it spreads, weeps, or is "
          "still there after a month.",
          avoid=URGENT + ("athletes foot", "athlete's foot", "toes", "feet", "between my toes",
                          "scalp", "hair", "nail", "nails", "thrush", "vagina", "vaginal",
                          "discharge", "testicle lump", "lump", "hernia", "stitch")),

    entry("prickly-heat",
          (("prickly heat", "heat rash", "sweat rash", "sweat bumps", "rash from the heat",
            "rash in the sun", "itchy rash when hot"),
           # not "baby" or "child": a line that says "my baby has a heat rash" is read again as
           # the ask about the rash when nothing answers the first reading, so a carer word in the
           # key defeats the fence in the avoid below and a baby got the adult hydrocortisone line
           ASK_ABOUT + ("itchy", "itch", "bumps", "red", "sun", "hot",
                        "spreading", "blister", "clear")),
          "Prickly heat is sweat trapped under the skin, so the fix is cooling down: get out of "
          "the heat, a lukewarm shower, loose cotton and a fan, and let the skin dry rather than "
          "rubbing it. Calamine or a pharmacist's antihistamine settles the itch, and on a baby "
          "or a small child ask a pharmacist before using any cream. It fades in a few days; see "
          "a GP if it blisters, spreads, or comes with a fever.",
          avoid=URGENT + ("baby", "babies", "newborn", "toddler", "nappy", "diaper",
                          "sunburn", "sunburnt", "burnt", "heatstroke", "heat stroke",
                          "heat exhaustion", "dizzy", "fainted", "pregnant", "pregnancy")),

    # One entry for the whole table above: the key is every name in it, so any way of naming the
    # illness reaches this row, and the ask is what turns the name into a question.
    entry("childhood-illness",
          # The names, then the words the illness is asked or told about. A draft's second group
          # also held "a", "the", "i", "my", "it", "we", "have", "has", "got", "can" and
          # "should" - words nearly every row in the knowledge base uses. A word two rows share
          # stops being specific, and those cost the sore-throat and throat-infection rows a rank
          # point each, so "what is a throat infection" came out as globus. Only the question
          # words a person actually uses about an illness are here.
          (tuple(name for names, _ in CHILDHOOD_ILLNESSES for name in names),
           ("what", "whats", "what's", "how", "is", "does", "mean", "long", "contagious",
            "infectious", "catch", "catching", "spread", "last", "lasts", "symptoms", "signs",
            "dangerous", "serious", "treatment", "treat", "rash", "spots", "child", "children",
            "kid", "kids", "baby", "school", "nursery", "off", "vaccine", "vaccinated",
            "antibiotics")),
          _childhood_illness,
          ask=_ILLNESS_ASK,
          # a named illness outranks the general fever entry and the circulation ones that were
          # taking the words "fever" and "hand"/"foot" from these lines
          bias=2,
          # A person telling you what they have names the illness and asks nothing ("i think i
          # have measles", "ive got mumps"). Without the report counted as the second signal the
          # row never came within reach: the line scored under MIN_SCORE and the chat nod or the
          # greeting took the turn, so the card was only ever reached by "what is measles" or by a
          # line that added a word ("i have measles and a rash", "ive got measles what do i do").
          report=True,
          avoid=_ILLNESS_AVOID),
]

ANSWERS = ("health",)
