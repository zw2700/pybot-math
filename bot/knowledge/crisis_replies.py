"""The crisis and emergency card texts, kept as data rather than code.

These are the answers `bot/modules/safety.py` gives when a line is an emergency: the card for a
person in danger, the numbers to ring, and the one instruction that matters most for each kind of
harm. They live here, as one table keyed by meaning, so the module that decides *when* to say one
stays readable and stays under the publisher's 1 MiB file limit. Nothing in this file is logic,
and the wording is the safety lane's: moving a card does not change a word of it.
"""

REPLIES = {
    # A rope burn, a carpet burn and a mat burn are the same story: cool it, keep it clean, cover
    # what is broken, and know when it needs seeing.
    "friction_burn": (
        "A rope or carpet burn is friction rather than heat: run it under the tap for a few "
        "minutes, pat it dry, and cover it with a non-stick dressing if the skin is broken. Leave "
        "any blister whole and keep it clean for a few days. One over a joint, across a big area, "
        "or one that gets hot, red and spreading needs to be seen the same day.",
        "A rope or carpet burn is friction rather than heat: hold it under the tap for a few "
        "minutes, pat it dry, and cover it with a non-stick dressing if the skin has come off. "
        "Leave blisters whole and keep it clean for a few days. Anything over a joint, across a big "
        "area, or hot and spreading needs looking at the same day.",
    ),
    # Two sentences and the timeframe, because the timeframe is the whole point: the first days are
    # the risky stretch and the surgery can make them safe. "Do not do it alone" is the one
    # instruction that matters most and it is easy to miss.
    "alcohol_withdrawal": (
        "The first three days after stopping are the risky stretch: the shakes, sweats, a racing "
        "heart and being sick are withdrawal, and coming off it is safer with help than alone. "
        "Ring 111 today and ask about a home detox - the surgery can give medicine that stops it "
        "getting worse - and do not be alone for the next few days.",
    ),
    # Said after the card, to a person who is still shaking a turn later. Short on purpose: the
    # card has the plan, and this only says yes, that is the withdrawal and here is the next step.
    # The one question where the answer is no, and it has to say why or it reads as a rule: the
    # drink works for an hour or two and then the shakes come back harder.
    "alcohol_withdrawal_hair": (
        "No - a drink to stop the shakes or to get to sleep only works for an hour or two, and then "
        "the shakes come back harder than they were. That is the loop that ends in a seizure, and it "
        "is the reason a home detox is done with medicine instead of a drink. Ring 111 today and ask "
        "about it: a short course of tablets is what the NHS uses to make this stretch safe.",
    ),
    # Getting worse rather than better is the 111 day, and the 999 words are named so the person
    # knows which is which. It is also the answer to "im scared", which asks for the next step
    # more than for the diagnosis.
    "alcohol_withdrawal_worse": (
        "That is a frightening thing to be going through, and it is safer with someone with you. "
        "Getting worse rather than better - more shakes, a racing heart, being sick, not sleeping "
        "at all - is a 111 call today rather than a wait and see, and 999 if there is confusion, "
        "a fit, or they cannot be woken.",
    ),
    "alcohol_withdrawal_more": (
        "That is the withdrawal, and it is usually worst in the first three days and then eases. "
        "Ring 111 today and ask about medicine that makes it safe rather than riding it out, and "
        "999 if they get confused, see things or have a fit.",
    ),
    # The two questions the card invites, answered instead of passed on.
    "alcohol_withdrawal_when": (
        "The worst of it is usually over in three to five days, though sleep and mood can take a "
        "few weeks to settle. Ring 111 today if it is getting worse rather than better, and 999 for "
        "confusion, seeing or hearing things, or a fit.",
    ),
    "alcohol_withdrawal_danger": (
        "It can be: withdrawal is what causes the fits and the delirium tremens, which is why it "
        "does not wait for the morning. Ring 111 today about a home detox and medicine that makes "
        "it safe, and 999 now if there is confusion, seeing or hearing things, a fit, or they "
        "cannot keep water down.",
    ),
    # Confusion, hallucinations and fits are the delirium tremens, and the answer is the ambulance
    # and company while it comes.
    "alcohol_withdrawal_severe": (
        "That is delirium tremens and it is an emergency, not something to ride out: confusion, "
        "seeing or hearing things, or a fit a day or two after the last drink needs 999 now. Stay "
        "with them, keep the room quiet and bright enough to see by, and do not leave them alone.",
    ),
    # The numbing wears off and the slurring goes with it. No red flags in the text: a drooping
    # face or a weak limb is caught by its own pattern before this card is reached, and a card
    # that carries a 999 in it makes every line after it an emergency follow-up ("will he be ok
    # for school tomorrow" got "keep the 999 or 911 call handler"). Worded without "you" and
    # "your" because the line is as often about a child at the dentist as about the speaker.
    # A toddler's mush-mouth is usually just that age, so the card asks for the sudden part rather
    # than naming a stroke at a child.
    # No number in the words: a safety answer that names one makes every line after it an
    # emergency continuation ("will he be ok for school tomorrow" got "do what the emergency line
    # says"). The number comes on the answer to this question, not before it.
    # No number and no case noted: the drink wears off, and a line after it ("will he be ok for
    # work tomorrow") is an ordinary question, not an emergency continuation.
    "slur_drink": (
        "If it is the drink, it wears off: water, something to eat, and no driving until the "
        "speech is back to normal. Give it an hour or two, and if it has not cleared by then, or "
        "a side is weak or the face droops with it, that is not the drink: ring 999.",
    ),
    "slur_small_child": (
        "Toddlers' words come out thick a lot of the time, and on its own that is a health visitor "
        "or GP question. Has it come on suddenly, or is that how he has always sounded? A droopy "
        "side, a fever or a fit with it would change what to do.",
    ),
    "dental_numb": (
        "The numbing from a filling slurs the words for a few hours and wears off on its own; "
        "keep to soft food, and nothing hot until the feeling is back. If it is the same "
        "tomorrow, that is worth a word with the dentist.",
    ),
    # Said of a class or a sport with the words of recovery, "i cant catch my breath after spin
    # class" is a person who has just worked hard, not an ambulance. The answer says what settles
    # it and what does not.
    "breath_effort": (
        "Being that puffed after hard exercise is normal and it settles: sit down, lean forward with "
        "your hands on your knees, and breathe in through your nose and out through your mouth, a "
        "little slower each time. If it has not eased after ten minutes of sitting, or it comes with "
        "chest pain, dizziness, a racing heart or blue lips, ring 999 rather than wait.",
        "That is what hard effort does, and it comes back down: sit down, drop your shoulders and "
        "slow your breathing, and take small sips of water. Ring 111 if it is still there after ten "
        "minutes at rest, and 999 if there is chest pain, fainting or you cannot speak in "
        "sentences.",
    ),
    # A laugh emptying the lungs in short bursts is one of the few breathlessness lines that is
    # allowed to be ordinary - and it still says when it is not, because a person reading it
    # deserves the test as well as the reassurance.
    "breath_laugh": (
        "That is a laugh doing what a laugh does: the air goes out in short bursts and comes back "
        "within a few seconds, so there is nothing to worry about. Worth a word with the GP only "
        "if it also catches you when you are not laughing, or you go dizzy with it.",
        "A good laugh empties the lungs in bursts, so the breath goes for a few seconds and then "
        "comes back - that one is normal. See the GP if it happens when you are not laughing too, "
        "or if you feel faint or see stars with it.",
    ),
    "sting_watch": (
        "A sting swells where it went in and itches for a day or two: wash it, put a cold pack on "
        "for ten minutes at a time, and an antihistamine eases the itch. A swelling that keeps "
        "spreading, hives anywhere else, a puffy lip or face, or any trouble breathing is 999.",
        "Cool it, keep it clean and take an antihistamine for the itch: a wasp or bee sting is "
        "sore and swollen for a day or two and settles. Ring 999 if the swelling spreads up the "
        "arm or onto the face, the throat or breathing changes, or they feel faint.",
    ),
    "allergy_watch": (
        "Stop giving them that and note the time: a reaction to a food usually shows within "
        "minutes to a couple of hours. An antihistamine helps the itch and the hives if you have "
        "one and know it suits them, and a baby or a child with a swollen lip or a rash after a "
        "food should be seen today - ring 111 or the GP. If the tongue or throat swells, the voice "
        "changes or the breathing does, that is 999.",
        "Note what was eaten and when, because that is what a doctor will ask. An antihistamine "
        "drops the itch and the hives; a swollen lip, a puffy face or hives all over want a "
        "same-day call to 111 or the GP. A swelling tongue, a thick throat, a changed voice or "
        "trouble breathing is 999 or 911 straight away.",
    ),
    "breath_heat": (
        "That is the heat, not your lungs: sit in the shade or a cool room, loosen anything tight "
        "at the neck, drink water and put a cool wet cloth on your neck and wrists. The breath "
        "should ease within ten or fifteen minutes of cooling. If it does not, or your chest hurts, "
        "you feel confused or faint, ring 999.",
        "Heat does that: the blood goes to the skin to lose the heat, so the breath has to work "
        "harder. Get out of the sun, drink water, cool your neck and wrists, and it should settle "
        "in a quarter of an hour. If you are still fighting for it after that, or you feel faint, "
        "confused or have a chest pain, ring 999.",
    ),
    "breath_weeks": (
        "Weeks of being short of breath is worth having looked at today rather than waiting: ring 111 "
        "or your GP and say how long it has been going on, because anaemia, a chest infection and a "
        "heart that is working harder than it should all start this way. Call 999 straight away if it "
        "gets suddenly worse, comes on at rest, or you cannot finish a sentence.",
        "That is a good few days of it, so get it looked at today - ring 111 or your GP and say how "
        "long it has been going on, and mention any cough, swelling or tiredness with it. 999 straight "
        "away if it suddenly gets worse, or comes with chest pain, blue lips or being unable to speak "
        "in sentences.",
    ),
    "night_breath": (
        "Waking up in the night unable to breathe, or only breathing when propped up, needs a doctor "
        "today rather than a wait: ring 111 or your GP this morning and say it happened in your "
        "sleep. If it happens again, or you can't get your words out, that is 999.",
        "That is a same-day call, not something to sit on: ring 111 or your GP today and tell them "
        "you woke in the night short of breath, because the heart and the lungs are the two things "
        "worth checking for it. If it comes back, or the breathing is bad right now, that is 999.",
    ),
    "night_breath_child": (
        "A baby or a small child who stops breathing or gasps in his sleep needs 999 or 911 now, "
        "not an appointment - ring tonight and say he stopped breathing in his sleep. If he went "
        "blue, limp or floppy, or he is hard to wake, say that first. Keep him on his front on your "
        "arm while you wait, and start CPR and 999 together if he is not breathing at all.",
        "Ring 999 or 911 tonight for this one: a child who struggles for breath in his sleep is not "
        "something to watch until morning. Tell them how old he is and whether he went blue, limp or "
        "floppy, and stay with him - if he is not breathing properly, start CPR and keep the phone "
        "on speaker.",
    ),
    "shot": (
        "That needs 999 or 911 now, and say someone has been shot. Press hard on the wound with a "
        "cloth, add more cloths rather than lifting the one you have, and don't move them unless "
        "they are still in danger where they are.",
        "Ring 999 or 911 straight away and tell them there is a gunshot wound. Keep pressing on it "
        "with something clean and don't stop to look, and let the ambulance crew move them.",
    ),
    "fall_hip": (
        "A hip that hurts after a fall needs an X-ray today, so ring 111 or get to A&E rather than "
        "letting them walk it off. If they cannot put any weight on it, or one leg looks shorter or "
        "turned out, that is an ambulance - do not move them, ring 999 or 911.",
        "Do not try to walk on it: a hip that hurts after a fall is an X-ray today, so ring 111 or "
        "get to A&E. If it cannot take any weight, or the leg looks shortened or turned outwards, "
        "that is 999 or 911 and they should stay exactly where they are.",
    ),
    "breath_rest": (
        "That is an ambulance rather than a wait-and-see: breathlessness that comes on suddenly, or "
        "while you are sitting still, can be a clot on the lung or a heart problem, so ring 999 or "
        "911 now. Sit upright, keep still and don't drive yourself.",
        "Ring 999 or 911 now: sudden breathlessness at rest is how a clot on the lung or a heart "
        "problem shows up, and it is checked in hospital today. Sit upright and stay with someone "
        "while you wait.",
    ),
    "spiked": (
        "Get somewhere safe with someone you trust, and ring 999 or 911 straight away if you are "
        "drowsy, confused or struggling to stay awake - say you think your drink was spiked. Keep "
        "the glass if you can, and don't be on your own tonight.",
        "Don't be on your own tonight: get a friend to stay with you, and ring 999 or 911 if you are "
        "getting drowsy, sick or confused. Keep the glass if you can, and tell someone you trust "
        "what happened.",
    ),
    "allergy_now": (
        "What can you see? Swollen lips, tongue, face or throat, a hoarse voice or any trouble "
        "breathing is 999 or 911 now, and if you have an EpiPen, use it first and ring 999 after. "
        "A rash or hives with none of that swollen is an antihistamine, a sit down, and watching it "
        "for the next hour.",
        "Tell me what it looks like and I can point you: swelling of the lips, tongue or throat, a "
        "tight chest or a voice going croaky is 999 or 911 straight away, even if it seems to be "
        "settling. Itchy spots with nothing swollen is an antihistamine and a quiet hour, and "
        "anything in between is A&E rather than waiting at home.",
    ),
    "lips_swell": (
        "Ring 999 or 911 now: swelling of the lips, tongue or throat can close the airway, so say "
        "that the lips and face are swelling. Sit upright, stay with someone, and use an adrenaline "
        "pen if there is one.",
        "That is an ambulance: a swelling lip or tongue after a sting or a food can close the "
        "airway, so ring 999 or 911 now, sit upright and stay with someone. If there is an "
        "adrenaline pen, use it and say so on the call.",
    ),
    # The same ambulance when the line never says what set it off.
    "throat_exertion": (
        "Cold, dry air on a run does make the throat feel tight, and it usually eases within a few "
        "minutes of stopping - sip water and breathe through your nose for a bit. If it tightens "
        "when you are sitting still, or comes with a wheeze or a cough that lingers, get it looked "
        "at rather than pushing through.",
        "That is usually the air and the breathing rather than anything wrong: slow down, sip "
        "water, and it should settle soon after you stop. A tight throat at rest, a wheeze, or one "
        "that keeps coming back is worth a GP look.",
    ),
    "lips_tingle": (
        "Stop eating it and take an antihistamine if you have one, and watch the swelling over the "
        "next hour. If your lips, tongue or throat start to swell, your voice changes or you feel "
        "faint, that is 999 or 911 - say anaphylaxis on the call.",
        "Have no more of it - an antihistamine helps the itch, and keep half an eye on it for the "
        "next hour. Any swelling of the lips or tongue, a tight throat, a wheeze or feeling faint "
        "is 999 or 911 straight away.",
    ),
    # A tingle in the lips or the tongue with no cause in the line is the commonest tingle there
    # is, and it is not the food card: there is nothing to stop eating. It is also not a shrug -
    # the same tingle is how anaphylaxis starts - so the answer says what it usually is and what
    # to watch for, and the 999 is the change rather than the tingle.
    "lips_tingle_alone": (
        "A tingle like that on its own is usually nothing much: a cold sore starting, a new lip "
        "balm or toothpaste, something spicy, or breathing a bit fast. Keep half an eye on it for "
        "the next hour, and ring 999 or 911 if your lips or tongue start to swell, your throat "
        "feels tight, your voice changes or your breathing does - say anaphylaxis.",
        "On its own that is usually nothing - a cold sore, a new toothpaste, spice, or "
        "over-breathing. What matters is what comes next: swelling of the lips or tongue, a tight "
        "throat, a voice that has changed or a breath that is not right is 999 or 911, and say "
        "anaphylaxis.",
    ),
    "throat_tight": (
        "A throat that feels tight with nothing else going on is worth getting looked at today: "
        "ring 111 or your GP. If it keeps tightening, your voice changes, you can't swallow, or "
        "your lips or tongue start to swell, that is 999 or 911 rather than a wait.",
        "Get it seen today - 111 or the GP - and keep an eye on the swallow and the voice. A throat "
        "that is closing, a swelling lip or tongue, or any trouble breathing is 999 or 911, and say "
        "anaphylaxis on the call.",
    ),
    "lips_swell_bare": (
        "Ring 999 or 911 now: a lip, tongue or throat that is swelling or changing can close the "
        "airway and it does not always say what set it off. Say how it feels, sit upright, stay "
        "with someone, and use an adrenaline pen if there is one.",
        "That is an ambulance: a swelling lip or tongue, or a throat that feels thick, can close "
        "the airway, so ring 999 or 911 now, sit upright and stay with someone. An adrenaline pen "
        "if there is one, and say on the call which part has changed.",
    ),
    # A foraged mushroom or berry is a poison with no packet to keep: what is left of it, or a
    # photo of the plant, is what the poisons unit asks for.
    "foraged": (
        "Don't wait for symptoms: ring 111 now - 999 if they are sleepy, floppy, being sick or "
        "dribbling - and say what was eaten and about how much. Keep what is left of it, or a photo "
        "of the plant or the spot it came from, and don't make anyone vomit.",
        "Ring 111 now and say what was eaten and when, and go to A&E if they seem drowsy, sick or "
        "unsteady. Keep the rest of it, or take a photo of where it was growing, rather than "
        "washing it away - and never make them sick.",
    ),
    "heard_assault": (
        "If someone is being hurt right now, ring 999 and give the address and what you can hear - "
        "don't go in or knock. If it has stopped but you are worried, 101 or the domestic abuse "
        "line (0808 2000 247 in the UK) will tell you what to do next.",
        "Ring 999 now and say which address it is coming from and what you can hear; the police are "
        "the ones who can go in, and you should stay out of it yourself. If it stops and you are "
        "still worried, 101 takes it from there.",
    ),
    # Blood in the mouth is pressure and a dentist or A&E, not the cloth-on-a-cut reply.
    "mouth_bleed": (
        "Spit the blood out rather than swallowing it, and press a clean folded cloth or a bit of "
        "gauze on the spot that is bleeding for ten minutes. If it keeps filling your mouth, or you "
        "feel faint or pale, ring 999 or 911; otherwise a dentist or A&E should see it today.",
        "Press on the bleeding spot with a clean folded cloth for ten minutes without lifting it to "
        "look, and spit out rather than swallow what comes. Still filling your mouth after that, or "
        "feeling faint with it, is 999 or 911; a mouth that stops it needs a same-day dentist or A&E.",
    ),
    "eye_chem": (
        "Rinse that eye with cool water for at least twenty minutes, holding the lids open, and "
        "don't rub it - the rinsing is what saves the sight. Then get it looked at today: 999 or "
        "A&E, and take the bottle or its label with you.",
        "Get to water now and rinse the eye for twenty minutes with the lids held open, then go "
        "straight to A&E or ring 999 and take the container with you. Don't rub it and don't use "
        "anything but water.",
    ),
    "bone_out": (
        "That is 999 or 911, not a wait: cover the wound with a clean cloth and don't push the bone "
        "back or straighten the limb. Keep them still and warm, and don't give them anything to eat "
        "or drink.",
        "Ring 999 or 911 for that. Cover it with a clean cloth, don't try to push the bone back in, "
        "and keep still and warm until the crew arrive - nothing to eat or drink in case they need "
        "an operation.",
    ),
    "headache": (
        "A headache that comes on like a bang, and is the worst they have had, needs checking now "
        "rather than this week: ring 999 or 911 and say how fast it came on. Keep them sitting and "
        "still with someone until the ambulance arrives.",
        "Ring 999 or 911 now and describe it as a sudden, severe headache - that is the pattern that "
        "gets them seen fast. Keep them sitting and still while they wait, and have someone with them.",
    ),
    "shot_self": (
        "That needs 999 or 911 now, and tell them you have been shot. Press hard on the wound with "
        "something clean, add more cloths rather than lifting the one you have, and stay where you "
        "are until the ambulance comes.",
        "Ring 999 or 911 and say you have been shot. Keep pressing on the wound and don't stop to "
        "look at it - someone else can do that while you talk to the operator.",
    ),
    "headache_self": (
        "A headache that comes on like a bang, and is the worst you have had, needs checking now "
        "rather than this week: ring 999 or 911 and say how fast it came on. Stay sitting and still "
        "with someone until the ambulance arrives.",
        "Ring 999 or 911 now and describe it as a sudden, severe headache - that is the pattern that "
        "gets you seen fast. Stay sitting and still while you wait, and don't be on your own.",
    ),
    "cough_blood": (
        "Blood in what they cough up wants seeing today, not waiting to see if it stops: ring 111 "
        "for where to go now, and 999 or 911 straight away if it is more than a streak or they are "
        "breathless or faint.",
        "Ring 111 today and say it is blood they are coughing up, and go to A&E if it keeps coming - "
        "999 or 911 if they are breathless or faint. Take any medicine they are on with them.",
    ),
    "cough_blood_self": (
        "Blood in what you cough up wants seeing today, not waiting to see if it stops: ring 111 for "
        "where to go now, and 999 or 911 straight away if it is more than a streak, you are "
        "breathless, or you feel faint.",
        "Ring 111 today and say it is blood you are coughing up, and go to A&E if it keeps coming - "
        "999 or 911 if you are breathless or faint. Take any medicine you are on with you.",
    ),
    "vomit_blood": (
        "Blood in vomit needs an ambulance rather than a wait: ring 999 or 911 and say how much and "
        "how many times. Nothing to eat or drink, keep them awake and on their side in case they are "
        "sick again, and take any tablets or packets with you.",
        "Ring 999 or 911 and say they are vomiting blood and how often. Keep them lying on their "
        "side, awake and warm, and take the medicine packets with you - nothing by mouth meanwhile.",
    ),
    "vomit_blood_self": (
        "Blood in vomit needs an ambulance rather than a wait: ring 999 or 911 and say how much and "
        "how many times. Nothing to eat or drink, stay awake and lying on your side in case you are "
        "sick again, and have your tablets or packets ready for the crew.",
        "Ring 999 or 911 and say you are vomiting blood and how often. Lie on your side, stay awake "
        "and warm, and have the medicine packets ready - nothing by mouth meanwhile.",
    ),
    "poo_black": (
        "A poo that is black and tarry is blood that has been sitting in the gut, and it needs "
        "looking at today rather than this week: ring 111 now and say black and tarry, or ring 999 "
        "or 911 if they are pale, dizzy, faint, or the bleeding keeps coming. Iron tablets and "
        "black pudding colour it too - say so if that is the reason.",
        "Ring 111 today and say the poo has been black and tarry, and go to A&E if it keeps coming "
        "or they look pale or faint - 999 or 911 then. Take a photo of it and any medicine they are "
        "on, and mention iron tablets or black pudding if either is in the picture.",
    ),
    "poo_black_self": (
        "A poo that is black and tarry is blood that has been sitting in your gut, and it needs "
        "looking at today rather than this week: ring 111 now and say black and tarry, or 999 or "
        "911 if you are pale, dizzy or faint, or the bleeding keeps coming. Iron tablets and black "
        "pudding colour it too - say so if that is the reason.",
        "Ring 111 today and say the poo has been black and tarry, and go straight to A&E if it "
        "keeps coming or you feel faint or light-headed - 999 or 911 then. Take a photo of it and "
        "your medicine packets, and mention iron tablets or black pudding if either is in the "
        "picture.",
    ),
    "poo_blood_long": (
        "Blood that has been there for weeks or months is not an A&E job, but it does need a GP "
        "appointment in the next week or two rather than a wait-and-see: ring the surgery and say how "
        "long it has been going on and whether it is getting heavier. Ring 111 today if it gets "
        "heavier or they feel faint.",
        "Blood that has been going on for weeks or months wants a GP appointment in the next week or "
        "two rather than an A&E trip, and sooner if it is getting heavier or they are losing weight "
        "without trying. Ring 111 today if it gets heavy or they feel faint.",
    ),
    "poo_blood_long_self": (
        "Blood that has been there for weeks or months is not an A&E job, but it does need a GP "
        "appointment in the next week or two rather than a wait-and-see: ring the surgery and say how "
        "long it has been going on and whether it is getting heavier. Ring 111 today if it gets "
        "heavier or you feel faint.",
        "Blood that has been going on for weeks or months wants a GP appointment in the next week or "
        "two rather than an A&E trip, and sooner if it is getting heavier or you are losing weight "
        "without trying. Ring 111 today if it gets heavy or you feel faint.",
    ),
    "poo_black_long": (
        "A black and tarry poo that has been like that for weeks is not the bleeding-now kind that "
        "needs an ambulance, but it does need a GP appointment in the next week or two: ring the "
        "surgery and say how long it has been going on. Ring 111 today if they are pale, dizzy or "
        "faint, or the bleeding gets heavier.",
        "Black and tarry poo that has been like that for weeks wants a GP appointment in the next "
        "week or two, and mention any iron tablets, because those colour it too. Ring 111 today if "
        "they are pale, dizzy or faint, or it gets heavier.",
    ),
    "poo_black_long_self": (
        "A black and tarry poo that has been like that for weeks is not the bleeding-now kind that "
        "needs an ambulance, but it does need a GP appointment in the next week or two: ring the "
        "surgery and say how long it has been going on. Ring 111 today if you are pale, dizzy or "
        "faint, or the bleeding gets heavier.",
        "Black and tarry poo that has been like that for weeks wants a GP appointment in the next "
        "week or two, and mention any iron tablets, because those colour it too. Ring 111 today if "
        "you are pale, dizzy or faint, or it gets heavier.",
    ),
    "poo_blood": (
        "Blood in a poo is worth the same-day call rather than a wait: ring 111 today and say how "
        "much and whether it was mixed in or on the paper. Ring 999 or 911 if the bleeding is heavy, "
        "they go dizzy or pale, or there is a lot of dark blood as well.",
        "Ring 111 today and say there is blood in their poo and how much, and go to A&E without "
        "waiting if it is heavy, dark and tarry, or they feel faint. Keep the medicine packets out "
        "for whoever you speak to.",
    ),
    "poo_blood_self": (
        "Blood in a poo is worth the same-day call rather than a wait: ring 111 today and say how "
        "much and whether it was mixed in or on the paper. Ring 999 or 911 if the bleeding is heavy, "
        "or you go dizzy, pale or faint.",
        "Ring 111 today and say there is blood in your poo and how much, and go to A&E without "
        "waiting if it is heavy, dark and tarry, or you feel faint. Have your medicine packets to "
        "hand for whoever you speak to.",
    ),
    "torsion_long": (
        "A swelling that has been there a week or more is not the twisted kind that is counted in "
        "hours, but it still wants seeing today: ring 111 for where to go now, or take them to a "
        "walk-in centre. Go to A&E straight away if the pain gets severe, they are being sick, or it "
        "has gone hard or changed colour.",
        "Ring 111 today or go to a walk-in centre and say how long it has been swollen and sore; a "
        "long-standing swelling is not the twisted kind, but it needs looking at properly. A&E "
        "straight away if the pain gets severe, you are sick, or it goes hard or changes colour.",
    ),
    "torsion_long_self": (
        "A swelling that has been there a week or more is not the twisted kind that is counted in "
        "hours, but it still wants seeing today: ring 111 for where to go now, or go to a walk-in "
        "centre. A&E straight away if the pain gets severe, you are sick, or it goes hard or changes "
        "colour.",
        "Ring 111 today or go to a walk-in centre and say how long it has been swollen and sore; a "
        "long-standing swelling is not the twisted kind, but it needs looking at properly. A&E "
        "straight away if the pain gets severe, you are sick, or it goes hard or changes colour.",
    ),
    "torsion_hard": (
        "That needs A&E today, not next week: a swollen or hard testicle is checked the same day, "
        "and they should say when it started and that it is one side - if the pain came on suddenly "
        "it is the twisted kind, which has only a few hours before it is lost. Ring 999 or 911 if "
        "they are in severe pain, vomiting, or the scrotum has changed colour.",
        "Get them to A&E today and say that one side is swollen or hard and when it started; if the "
        "pain came on suddenly it is a twisted testicle, which has only a few hours before it is "
        "lost. Ring 999 or 911 if they are in severe pain, being sick, or the scrotum looks "
        "discoloured.",
    ),
    "torsion_hard_self": (
        "That needs A&E today, not next week: a swollen or hard testicle is checked the same day, "
        "and say when it started and that it is one side - if the pain came on suddenly it is the "
        "twisted kind, which has only a few hours before it is lost. Ring 999 or 911 if the pain is "
        "severe, you are being sick, or the scrotum has changed colour.",
        "Go to A&E today and say that one side is swollen or hard and when it started; if the pain "
        "came on suddenly it is a twisted testicle, which has only a few hours before it is lost. "
        "Ring 999 or 911 if the pain is severe, you are vomiting, or the scrotum looks discoloured.",
    ),
    "torsion_lump": (
        "Have a GP look at that within two weeks - a lump, or one side bigger than the other, is the "
        "fast-track referral and it is not something to sit on. Get them seen today rather than "
        "waiting if it is sore, hard or the scrotum is swollen, and to A&E straight away if the pain "
        "came on suddenly or they are being sick.",
        "Book them a GP appointment within two weeks about the lump or the size difference - that is "
        "the fast-track referral - and get them seen today instead if it is sore, hard or the "
        "scrotum is swollen. A&E straight away if the pain came on suddenly or they are being sick.",
    ),
    "torsion_lump_self": (
        "Have a GP look at that within two weeks - a lump, or one side bigger than the other, is the "
        "fast-track referral and it is not something to sit on. Go today rather than waiting if it "
        "is sore, hard or the scrotum is swollen, and to A&E straight away if the pain came on "
        "suddenly or you are being sick.",
        "Book a GP appointment within two weeks about the lump or the size difference - that is the "
        "fast-track referral - and go today instead if it is sore, hard or the scrotum is swollen. "
        "A&E straight away if the pain came on suddenly or you are being sick.",
    ),
    "torsion": (
        "That needs A&E now, not tomorrow: a testicle that is suddenly sore and swollen can be "
        "twisted, and it has to be untwisted within a few hours to be saved. Ring 999 or 911 if they "
        "are in severe pain, vomiting, or the scrotum has gone hard or changed colour; otherwise get "
        "them to the nearest A&E straight away and don't wait for it to settle.",
        "Get them to A&E straight away and say the pain came on suddenly and one side is swollen - "
        "a twisted testicle has a few hours before it is lost, so it is not a wait-and-see. Ring 999 "
        "or 911 if the pain is severe, they are being sick, or the scrotum looks hard or discoloured.",
    ),
    "torsion_self": (
        "That needs A&E now, not tomorrow: a testicle that is suddenly sore and swollen can be "
        "twisted, and it has to be untwisted within a few hours to be saved. Ring 999 or 911 if the "
        "pain is severe, you are being sick, or the scrotum has gone hard or changed colour - "
        "otherwise get yourself to the nearest A&E straight away.",
        "Go to A&E now and say the pain came on suddenly and one side is swollen - a twisted "
        "testicle has a few hours before it is lost, so it is not a wait-and-see. Ring 999 or 911 "
        "if the pain is severe, you are vomiting, or the scrotum looks hard or discoloured.",
    ),
    "pregnancy_bleed": (
        "Ring your midwife or the maternity unit today: any bleeding in pregnancy needs checking "
        "the same day, and go straight to A&E or ring 999 or 911 if it is heavy, if you have pain, "
        "or if you feel faint.",
        "That needs a call to the maternity unit today rather than waiting, because bleeding in "
        "pregnancy is always checked the same day; heavy bleeding, pain or feeling faint is 999 or "
        "911 straight away.",
    ),
    "pregnancy_bp": (
        "Ring your maternity unit now, with how many weeks you are, and describe what you have "
        "noticed: a bad headache, blurry or flashing vision, or swelling of the face and hands is "
        "checked the same day, and 999 if you feel very unwell.",
        "A bad headache, blurry or flashing vision, or swelling of the face and hands is a call to "
        "the maternity unit today rather than a wait-and-see; 999 or 911 if you feel very unwell.",
    ),
    # A shock is a "now" even when the person is standing up and talking: the supply first, then
    # the check, because the heart can go wrong hours later.
    "electric_shock": (
        "Turn the power off at the wall or the fuse box before anyone touches them, then ring 999 "
        "or 911 and say it was an electric shock. Unconscious, confused, a burn or a heartbeat that "
        "feels wrong is the ambulance; a shock that left none of those is still checked the same "
        "day, and 111 will say where.",
        "The supply goes off at the wall or the fuse box before anyone touches them, and then the "
        "shock is checked: 999 or 911 if there is a burn, confusion, a racing or fluttering "
        "heartbeat or a pregnancy, and 111 the same day for a shock that seems to have left nothing "
        "behind, because the heart can be affected hours later.",
    ),
    # A shock that put someone on the floor is the ambulance even when they are up and talking
    # again: the heart rhythm can go wrong hours later, and that is the thing this card exists for.
    "electric_shock_floor": (
        "Turn the power off at the wall or the fuse box first if it is still live, then ring 999 or "
        "911 and say a shock knocked them out: being knocked out by a shock is an ambulance even if "
        "they seem fine now, because the heart can go wrong hours later. Don't let them drive or be "
        "on their own until they have been seen, and if they are still out, check they are "
        "breathing and put them on their side.",
        "Off at the wall or the fuse box first if it is still live, then ring 999 or 911. A shock "
        "that knocked them out is checked by an ambulance however well they feel now - the heart "
        "rhythm can go wrong hours later - and someone should stay with them until help comes.",
    ),
    "electric_shock_floor_self": (
        "Don't touch the supply again - off at the wall or the fuse box - and ring 999 or 911 now, "
        "saying you were knocked out by a shock. That is an ambulance even if you feel fine, because "
        "the heart rhythm can go wrong hours later; don't drive and don't stay on your own until you "
        "have been seen.",
        "Off at the wall or the fuse box first, then ring 999 or 911 and tell them you passed out "
        "after a shock. Feeling fine now does not make it a wait-and-see - the heart can go wrong "
        "hours later - so don't drive and keep someone with you until you have been seen.",
    ),
    # A thing in a socket is the shock that has not happened yet, so the answer is the switch and
    # the tool, then what to do if there was a jolt - and the cheap fix for the next time.
    "socket_thing": (
        "Anything metal in a socket is a shock waiting to happen: switch that socket off at the "
        "wall before anyone touches it, and get the thing out with the power off, never with your "
        "fingers or a metal tool. If there was a jolt, a burn, or they were knocked out or "
        "confused, ring 111 today and 999 for a burn, confusion or a racing heartbeat; blanking "
        "plugs and an RCD on that socket are what stop the next one.",
        "That is a shock waiting to happen: off at the wall first, then take the thing out with the "
        "power off and never with a metal tool. A jolt that left a burn, confusion or a fast "
        "heartbeat is 999 or 911, and a jolt that seems to have left nothing is 111 the same day. "
        "Blanking plugs and an RCD are the fix for that socket.",
    ),
    "pregnancy_quiet": (
        "Ring your maternity unit now - a baby that has gone quiet or is moving less than usual is "
        "checked straight away, day or night, and never left to see if it picks up.",
        "Ring the maternity unit now rather than waiting: less movement than usual, or none, is "
        "always checked the same day, and they would much rather you called.",
    ),
    "pregnancy_waters": (
        "Ring your maternity unit now and tell them the waters have gone and how many weeks you "
        "are: they will say whether to come in. Ring 999 or 911 if you are bleeding, if the baby "
        "is moving less, or if you feel unwell.",
        "Ring the maternity unit straight away - they need to know the waters have broken and how "
        "many weeks you are, and 999 or 911 is right if there is bleeding, pain or less movement.",
    ),
    "pregnancy_sick_q": (
        "Feeling sick early on is very common and usually settles by around 14 weeks; small snacks "
        "through the day, ginger and sipping fluids little and often are what most people are "
        "told. If you can't keep food or drink down, ring your midwife or GP the same day.",
        "That's usually normal in the first months and eases off by 14 weeks or so - eating little "
        "and often, and keeping water by you, helps most people. Ring your midwife or GP the same "
        "day if you can't keep anything down or you're losing weight.",
    ),
    "pregnancy_sick": (
        "Ring your midwife or GP today: not being able to keep food or drink down in pregnancy is "
        "worth checking the same day, and 111 can get you seen out of hours. If you can't keep "
        "water down either, or you feel faint or dizzy, ring 999 or 911.",
        "That needs a real person today - your midwife, GP or 111 - because sickness that stops "
        "you keeping anything down can leave you dehydrated. Get help straight away if you also "
        "feel faint, dizzy, or you've stopped passing urine.",
    ),
    "self_harm": (
        "I'm really glad you told me, and you deserve help right now, not later. Please call a "
        "crisis line and stay with someone you trust: Samaritans 116 123 (UK, free, any time) or "
        "988 (US); if you've taken something, call 999 or 911.",
        "That sounds unbearable, and you don't have to carry it alone tonight. Ring a crisis "
        "line now (116 123 in the UK, 988 in the US) or your local emergency number, and tell one "
        "person near you how bad it is so they can stay with you.",
    ),
    # A lesson, a film or an assembly that named suicide, with the speaker outside it. That is a
    # topic and not the person, so it is not the crisis card - but it is not the homework advice
    # either, which is what the stand-down fell through to: "our teacher talked about suicide
    # today" was answered with how to ask a teacher about the last question on a sheet. The reply
    # says the plain thing and leaves the door open for whoever it did stay with.
    "suicide_lesson": (
        "That is a heavy thing to sit through in a lesson. If it has stayed with you, say it out "
        "loud to someone you trust - and if any of it is about you, tell me and I will stay with "
        "you on it.",
        "Those lessons can bring things up even when they are not about you. If it does, one "
        "person who knows you is worth more than a search engine, and I am here for that part of "
        "it if you want to talk it through.",
        "Fair enough - it is a hard subject to hear about at school. If any of it is about you, "
        "or about someone you know, say so and I will help you work out who to tell.",
    ),
    # First aid first, and the crisis line in the same breath: a cut that soaks through is the
    # ten minutes of pressure, and the person who made it is the one a crisis line is for.
    "self_cut_bleeding": (
        "Press a clean cloth hard on the cut and keep pressing for ten minutes without lifting it "
        "to look - lifting is what starts it again - and put a second cloth on top if it soaks "
        "through. If the bleeding is spurting, will not stop, or the cut is deep, that is 999 or "
        "911. And if you did that to yourself on purpose, you deserve real help with the rest of "
        "it too: Samaritans 116 123 (UK, free, any time) or 988 (US).",
        "That needs pressing on now: clean cloth, hard, ten minutes without lifting it to check, "
        "another cloth on top if it comes through. Deep, gaping, or still going after that is 999 "
        "or 911. If it was your own doing on purpose, a crisis line (116 123 in the UK, 988 in the "
        "US) will talk to you now, day or night.",
    ),
    # A third person who "hurt himself" and nothing else: what happened decides it, so ask.
    "hurt_himself_asked": (
        "Ask what happened: a fall, a knock in sport, or something they did on purpose - that "
        "decides the next step. If it was on purpose, ring 999 or a crisis line (116 123) now. If "
        "it is a bump or a sprain, 111 can say whether it needs looking at today.",
        "Ask them what happened: a fall, a knock in sport, or something they did on purpose - that "
        "decides the next step. If it was on purpose, ring 999 or a crisis line (116 123) now. If "
        "it is a bump or a sprain, 111 can say whether it needs looking at today.",
    ),
    "someone_else": (
        "Stay with them if you can, and ask them straight out whether they mean to kill themselves - "
        "asking does not plant the idea. Ring 999 or 911 now if they've taken something or are in "
        "danger, and a crisis line (116 123 in the UK, 988 in the US) can talk it through with either "
        "of you.",
        "Don't leave them alone, and ask them directly whether they are thinking about suicide. If "
        "they've taken anything or you're scared for them, that's 999 or 911; otherwise a crisis line "
        "(116 123 in the UK, 988 in the US) will talk to the two of you.",
    ),
    "hanging": (
        "Take the weight off their neck straight away - lift them or cut them down - and ring 999 "
        "or 911. If they're not breathing normally, start CPR and keep going until the crew arrive.",
        "Get them down or take the pressure off the neck now, then call 999 or 911. Start CPR if "
        "they're not breathing normally, and don't leave them alone.",
    ),
    # Said to the person it happened to, not about them: what to do now, and the check that is the
    # part people skip because the throat feels fine.
    "strangled_self": (
        "That is strangulation, and it is not your fault. Ring 999 or 911 now, and get seen today "
        "even if your throat feels fine - swelling can come on hours later. If it was someone "
        "close, a domestic abuse line (0808 2000 247 UK, 1-800-799-7233 US) can plan the next step "
        "with you when it is safe to talk.",
        "Ring 999 or 911 now, and get a medical check today even if you feel alright: the airway "
        "can swell hours after a hand on the throat. When you can talk safely, a domestic abuse "
        "helpline (0808 2000 247 UK, 1-800-799-7233 US) will help you work out what comes next.",
    ),
    "snake_bite": (
        "Keep them as still and calm as you can and ring 999 or 911 now, saying a snake bit them - "
        "an adder bite needs watching in hospital. Don't cut it, suck it or put a tight band on it; "
        "take off rings and watches, keep the bitten limb still and low, and don't give them food, "
        "drink or alcohol on the way.",
        "That's a 999 or 911 call now: keep them still, don't let them walk about, and don't cut, "
        "suck or strap the bite - a band makes the venom worse. Rings and watches off, the limb "
        "still and resting low, and tell the crew it was a snake.",
    ),
    "pet_hurt": (
        "Ring the vet today and describe what happened: a kick or a cord round the neck can do damage "
        "you cannot see from outside. Keep them still and warm, don't let them walk any further, and "
        "ring the emergency vet now if their breathing is odd or they are limp.",
        "That is a vet visit today - ring ahead so they are ready - and an emergency vet now if the "
        "breathing is odd, they are limp or they cannot stand. Keep them still, keep them warm, and "
        "don't let them walk about while you wait.",
    ),
    "animal_kick": (
        "Get them checked today - ring 999 if a hoof caught the head, the chest, the belly or the "
        "back, and take them to A&E otherwise. A kick puts a lot of force into a small place, and "
        "the bruise you can see is not the injury you have to worry about.",
        "That needs looking at today: 999 or 911 if the kick landed on the head, chest or belly, "
        "otherwise A&E, because a hoof can do damage inside that a bruise does not show. Keep them "
        "still and warm until someone has seen them.",
    ),
    "blind_cord": (
        "Free them straight away and cut the loop if it will not come undone, then ring 999 or 911 "
        "if there is any trouble breathing, a cough that will not stop, or they went quiet. Cut or "
        "clip every looped cord in the house at the top and keep cots and beds away from them.",
        "Get the cord off the neck now - cut it if you have to - and ring 999 or 911 if their "
        "breathing is odd, they are coughing, or they seem drowsy. After that, cut the loops out of "
        "every blind cord and move the cot away from the window.",
    ),
    # The person who is doing it, said in the first person, is the one who can stop it tonight,
    # and the reply is for them: the programme that works with people who are violent at home,
    # and 999 if someone in the house is in danger now. It says plainly what it is, because that
    # is the only useful thing to say to it.
    "abuse_own": (
        "Hitting someone you live with is abuse, and it is the thing to stop rather than a temper "
        "you have to manage. Respect (0808 802 4040 in the UK) is a free, confidential line for "
        "people who are violent or frightening at home and it will work out the next step with you; "
        "there are equivalents in most countries. If anyone in the house is in danger right now, "
        "ring 999 or 911 and tell them what has happened, and until you have spoken to someone, "
        "stay off drink and drugs, because that is what turns an argument into this.",
        "That is abuse, and the fact you are saying it is the only good sign in the line. Ring "
        "Respect on 0808 802 4040 (UK, free, confidential) or the equivalent in your country, and "
        "if someone there is in danger now, 999 or 911. Until then: put distance between you - "
        "leave the room, go for a walk - and no drink, because it is what makes the next one "
        "more likely.",
    ),
    # A vehicle has hit a person. The two things that make an injury worse before the ambulance
    # comes are moving them and giving them anything by mouth, so both are said plainly, and the
    # "seems fine" half is there because internal bleeding does not show at once.
    "struck_by_vehicle": (
        "That is a 999 or 911 call now, not a wait-and-see: say someone has been hit by a vehicle "
        "and how old they are. Don't move them unless they are still in the road or somewhere "
        "dangerous, keep them warm with something over them, and give them nothing to eat or "
        "drink. Watch their breathing and be ready to start CPR, and keep the phone on speaker so "
        "you can hear the call handler's questions. If they are up and walking, they still need "
        "A&E today: bleeding inside a belly or a chest shows up late.",
        "Ring 999 or 911 for this one and say it was a vehicle. Leave them where they are unless "
        "they are in the road - moving someone with a broken neck or a hurt spine is what makes "
        "it worse - keep them warm, and don't give them anything to eat or drink. Press firmly on "
        "anything that is bleeding and don't lift the cloth off to look. Even if they seem fine, "
        "they need to be seen today, because internal injuries do not show at once.",
    ),
    "struck_my_bike": (
        "Were you on it? That is the part that matters - a clipped bike is a write-off, but a "
        "rider who came off needs looking at today even if nothing hurts yet. If you are still on "
        "the road, get off it and behind a barrier first; then swap details, and if you are sore "
        "anywhere, shaky, or you banged your head, get seen rather than sleeping it off.",
        "Glad you are here to tell me. If you came off, check yourself over somewhere safe and get "
        "anything that hurts looked at today - the aches from a road knock turn up hours later. If "
        "you are fine, you still need the driver's details and a photo of the bike before they go.",
        "That is a fright and a half. Get yourself out of the traffic before anything else, and if "
        "you came off, sit down for a minute and check how you feel - sore, dizzy or banged on the "
        "head means getting seen today. The bike can wait; the police non-emergency line is where a "
        "hit-and-run goes if they did not stop.",
    ),
    "near_thing_over": (
        "That is what makes those so frightening - it is over in a second and you are left shaking. "
        "Sit down somewhere safe for five minutes before you ride or drive on, and if the shaking "
        "does not settle, or you keep replaying it tonight, tell someone rather than sitting with it.",
        "They never even saw you, by the sound of it. Nothing you did caused that, and if you want it "
        "on record the police non-emergency line takes reports of near misses and bad driving - write "
        "down the time, the place and the vehicle while it is fresh.",
        "That would rattle anyone. Have a hot drink and give yourself ten minutes before the next "
        "bit of the day; if you are still shaky or sore tomorrow, that is when to get checked.",
    ),
    # Somebody trapped in a car is the one emergency where the wrong instinct - pulling them out -
    # is what paralyses people, so that is the instruction the card spends itself on. The engine
    # off, nothing to smoke, something warm and a voice: the four things that can be done by a
    # person who is not trained and should be doing nothing else.
    "trapped_vehicle": (
        "Ring 999 or 911 now and say someone is trapped in a vehicle and where you are. Don't try "
        "to pull them out unless the car is on fire or they are still in the road: switch the "
        "engine off, put something warm over them, and keep talking to them so they stay awake "
        "and still. Press firmly on anything that is bleeding and don't give them anything to eat "
        "or drink while you wait. A small child shut in and the day is hot is the exception - a "
        "window can be broken now, and 999 will say which one.",
        "That is a 999 call: tell them someone is trapped in the car and how many people are hurt. "
        "Leave them where they are - pulling a person out of a wreck is how a hurt spine becomes a "
        "permanent one - turn the engine off, don't smoke near it, and keep them warm and talking. "
        "If they go quiet or their breathing changes, say so to the call handler and be ready to "
        "start CPR. A baby or small child shut in a hot car is the one you do get out: break a "
        "window away from them, or tell the handler and do as they say.",
    ),
    "abuse": (
        "What's happening to you is abuse, and it is not your fault. If you're in danger right now "
        "call 999 or 911; otherwise call a domestic abuse helpline when it's safe to talk, for "
        "example 0808 2000 247 (UK) or 1-800-799-7233 (US).",
        "I'm sorry, that shouldn't be happening to you. Please get a real person involved: 999 or "
        "911 if you're in danger now, or a domestic abuse helpline (0808 2000 247 in the UK, "
        "1-800-799-7233 in the US) that can plan it out with you.",
    ),
    # What happened years ago is not an emergency to be met with a "Got it.", and it is not a
    # 999 call either: it is a person telling you something they have carried, and the answer is
    # that it was not their fault, that the injury is real, and where to get it looked at.
    "abuse_past": (
        "Thank you for telling me, and I'm sorry - that should never have happened, and it was "
        "not your fault. If it is still with you, that is an injury rather than a weakness, and "
        "your GP can refer you for help with it; the Samaritans are on 116 123 any hour too.",
        "That is a heavy thing to have carried, and it was not your fault. Flashbacks, nightmares "
        "and flinching are what an old injury does, not a sign you are not coping, and a GP can "
        "refer you to someone who works with it. If you would rather talk tonight, 116 123 is "
        "the Samaritans, any hour.",
        "I'm glad you told me. However long ago it was, it was not your fault, and help still "
        "exists for the after-effects: your GP can refer you, and the Samaritans (116 123) or a "
        "domestic abuse line (0808 2000 247 in the UK) will talk it through with you.",
    ),
    # Not "someone in the house": "i dont feel safe at work" is the same line, and the reply
    # has to ask rather than assume where.
    "unsafe": (
        "I'm glad you said it - that is a frightening way to feel, and you don't have to sit with "
        "it alone. Tell me what is happening and who is making it unsafe; if it's happening now, "
        "call 999 or 911, and if it's someone close to you, a domestic abuse helpline (0808 2000 "
        "247 in the UK, 1-800-799-7233 in the US) can plan the next step with you when it's safe "
        "to talk.",
        "That's not something to carry on your own. Is it someone close to you, or somewhere you "
        "have to be? If there is any danger right now, ring 999 or 911; otherwise tell one person "
        "you trust tonight, and a domestic abuse helpline (0808 2000 247 UK, 1-800-799-7233 US) "
        "will know the local options - including somewhere to go.",
    ),
    "battery_bulge": (
        "Stop using it and stop charging it: a swollen battery is a fire risk, and pressing on it "
        "to make it fit is how they catch light. Don't bend or puncture it, keep it out of the sun, "
        "and take it to a repair shop or the battery bin at the tip rather than the kitchen bin. If "
        "it smokes, sparks or gets hot, get it outside onto concrete and ring 999 or 911 - water "
        "makes these worse.",
        "A battery that has swollen up is going, so stop charging it and stop using it, and don't "
        "squeeze it back into place - that is how they catch light. Keep it cool and take it to a "
        "repair shop or a battery bin at the tip, not the bin at home. Smoke, sparks or real heat "
        "means get it outside onto concrete and ring 999 or 911, and no water on it.",
    ),
    "battery_fire": (
        "Treat that as a fire in the room: unplug it if that is safe, put it somewhere it cannot set "
        "anything alight - outside on concrete is best - and get everyone out of the room. Ring 999 "
        "or 911 and say it is a lithium battery; water and a wet cloth make these worse, not better.",
        "A battery that is burning or smoking is a fire, not a hot phone: unplug it if you can do it "
        "safely, get it outside onto concrete, and keep everyone away from it. Ring 999 or 911 and "
        "say it is a lithium battery fire - don't put water on it.",
    ),
    # A vehicle fire is its own thing: "get out of the building" is not the advice for a driver,
    # and opening the bonnet feeds it.
    "vehicle_fire": (
        "Pull over and stop as soon as it is safe, switch the engine off, get everyone out and walk "
        "well clear of it - then ring 999 or 911 from a distance. Don't open the bonnet: the rush of "
        "air feeds it, and a car fire spreads fast.",
        "Get everyone out and away from it now, then ring 999 or 911 from a good distance. Don't "
        "open the bonnet - the air feeds the fire - and don't go back for anything.",
    ),
    "fire": (
        "Get out now, stay out, and call the fire service: 999 or 911. Don't stop for anything, and "
        "close doors behind you if you can.",
        "Leave the building straight away and call 999 or 911 from outside. If there's smoke, stay "
        "low and keep your mouth covered.",
    ),
    # A fire that nearly started is not the building's card, and it is not nothing either: the line
    # wants "you caught it, here is what to check" and the one number that matters if it is wrong.
    # The two rules the reply has to keep are that it never says to go back inside, and that the door
    # stays open for the real fire - "it is still burning" is answered by FIRE, not by this.
    "near_fire": (
        "Close call, and good that you caught it. Check whatever it was is properly out and cold "
        "before you leave it - and if there is any smoke, or it flares up again, that is out of the "
        "building and 999 or 911.",
        "Glad that one did not take. Keep an eye on it for a bit yet, and anything that smoulders "
        "or flares up again means get out and ring 999 or 911.",
        "That was a near thing. Let it cool right down before you put it away, and if the smell of "
        "burning does not clear or it starts smoking again, get out and call the fire service on "
        "999 or 911.",
    ),
    # The turn after the near-fire card: the person says it was nothing, and the answer is to let
    # them stop checking. No number here - the card has already given the one that matters.
    "near_fire_over": (
        "Good, then there is nothing to watch. Let it cool right down before you put it away and "
        "get on with your evening.",
        "Nice one. If it was the toaster or the grill, empty the crumb tray when it is cold - that "
        "is usually what it was.",
        "Glad to hear it. That is the end of it, then - no need to keep checking.",
    ),
    # Heat stroke is said both ways - "i have heatstroke" and "my dad has heat stroke" - so it
    # has a first-person reply and a "them" reply, rather than "get them out of the sun" for
    # someone typing about themselves.
    "heat": (
        "That's heat stroke, which gets worse fast: ring 999 or 911 now and cool them quickly - "
        "shade, cold water on the skin, a fan on them, loose clothes. Water only if they're fully "
        "awake, and don't wait to see if it passes.",
        "Heat exhaustion needs shade, water and rest; heat stroke - confused, vomiting, or stopped "
        "sweating - is 999 or 911. Cool them on the way: shade, cold water on the skin, a fan.",
    ),
    "heat_self": (
        "That's heat stroke, which gets worse fast: ring 999 or 911 now and get cooled down - "
        "shade, cold water on the skin, a fan, loose clothes - and don't wait to see if it passes.",
        "Sit in the shade with water and a cold wet towel on the skin; if you're confused, being "
        "sick or have stopped sweating, that's heat stroke, so ring 999 or 911 and keep cooling "
        "down while you wait.",
    ),
    # One reply for the whole cluster: what it is, the glass test, and the one thing to say on the
    # call. "Say you are worried about sepsis or meningitis" is what changes the ambulance's speed.
    "red_flags": (
        "That's a 999 or 911 call now: say you're worried about sepsis or meningitis, and give the "
        "temperature and how long it has been going on. While you wait, press a clear glass on the "
        "rash - if it doesn't fade, tell them that too. Don't give food or drink if they are drowsy.",
        "Ring 999 or 911 and say you're worried about sepsis or meningitis - that is the word that "
        "gets them there fast. Keep them warm, don't leave them alone, and don't give them anything "
        "to eat or drink while they are drowsy.",
    ),
    # A headache and a rash together is meningitis said without the word. The glass test is the
    # thing the person can do themselves, and the stiff neck is the sign to say on the call. Both
    # options are written without a pronoun, so they read right said about a child and about the
    # person typing.
    "rash_headache": (
        "A headache and a rash together need looking at today, not in the morning: ring 111 now "
        "and press a clear glass on the rash - if it does not fade under the glass, that is 999 or "
        "911. Say meningitis when you call, and go straight in if there is drowsiness, a stiff "
        "neck or vomiting with it.",
        "Ring 111 now and do the glass test: press a clear glass on the rash, and if the spots stay "
        "visible, that is 999 or 911. Don't wait for a morning appointment if there is drowsiness, "
        "a stiff neck, or being sick with it - and use the word meningitis on the call.",
    ),
    # A fever and a rash together: the glass test is the thing the parent can do themselves.
    "fever_rash": (
        "A fever with a rash needs them seen today: ring 111 now, and 999 or 911 if the rash does "
        "not fade when you press a glass on it, or they are drowsy or floppy. Give fluids and keep "
        "them cool, not wrapped up.",
        "Ring 111 today and press a clear glass on the rash: if it does not fade, that is 999 or "
        "911 and say so. Note the temperature and how long it has been there, and keep offering "
        "sips of water.",
    ),
    # A named illness said plainly: the word itself is the call, and the parent needs it said once.
    "named_illness": (
        "That name needs them seen today, not in the morning: ring 999 or 911 and say the word "
        "meningitis/sepsis/pneumonia yourself, plus how long it has been going on and any rash. "
        "Don't wait to see if the next dose helps.",
        "Ring 999 or 911 now and use the word you just used - sepsis, meningitis, pneumonia - "
        "because it changes how fast they come. Keep them warm and awake, and don't give anything "
        "to eat or drink if they are drowsy.",
    ),
    # A number a parent reads out: 40 is the number they ring about, and it is not small talk.
    # A young baby with a temperature is not the sepsis card: it is urgent because of the age, and
    # the parent needs the undress-and-feed instructions more than the glass test.
    "newborn_temp": (
        "A temperature of 38 or more in a baby under three months is an emergency: ring 999 now and "
        "say the age and the reading. Undress them to a vest, keep offering feeds, and don't sponge "
        "them with cold water.",
        "Ring 999 now and give the age and the number - a baby under three months with a temperature "
        "is seen straight away, whatever the reading. Strip them to a vest, keep the feeds going, and "
        "don't give them medicine without advice.",
    ),
    "pale_child_heat": (
        "Heat is the likely reason: get them out of the sun into the shade or a cool room, loosen "
        "their clothes, and give them water in small sips. If the colour is not back in half an "
        "hour, or they go floppy, confused or stop sweating while still hot, ring 111 or 999.",
        "Pale and sweaty in the heat is usually the heat itself: shade, water in small sips and no "
        "more running about for a bit. If they stay pale and clammy, go drowsy or stop "
        "sweating while still hot, ring 111 or 999 rather than waiting.",
    ),
    "pale_child_effort": (
        "That is a lot of running about, and pale and clammy afterwards is the heat leaving them: "
        "sit them down in the shade, loosen their kit and give them water in small sips. If the "
        "colour is not back in half an hour, or they are floppy, confused or still sweating with "
        "cool skin, ring 111.",
        "Pale and sweaty straight after a match is usually just the effort: cool them down, get "
        "water into them and let them sit for twenty minutes. If they stay pale and clammy, go "
        "drowsy or stop sweating while still hot, ring 111 or 999.",
    ),
    "pale_child": (
        "Pale, grey or mottled skin that comes with cold or clammy hands and feet is a child who "
        "needs looking at now: ring 999 or 911 if they are floppy, hard to wake, breathing fast or "
        "their colour is grey or blue, and ring 111 for a doctor today if they are awake and "
        "talking. Keep them warm, offer sips of water and don't leave them alone.",
        "That is a child going downhill rather than a child who is tired: ring 111 today, and 999 "
        "or 911 if they are floppy, hard to wake, breathing fast or going blue round the lips. "
        "Keep them warm, keep offering drinks and stay with them while you wait.",
    ),
    # A grown-up who has gone pale, grey or clammy has lost blood pressure, and the child's advice
    # ("keep them warm, ring 111") is the wrong way round: sitting them down and calling the
    # ambulance is the answer, and so is not giving them anything to eat or drink while a bleed or
    # a heart attack is possible.
    # A child whose colour has gone with a red sign on it - floppy, mottled, breathing fast - is
    # an ambulance, and the plain colour card below is the 111 one. This row was skipping the
    # child altogether, so "my son is mottled and cold" was told a cold is a virus.
    "pale_child_now": (
        "That is an ambulance now rather than a wait-and-see: ring 999 or 911 and say the age, "
        "the colour and whether they are floppy, hard to wake or breathing fast. Lie them on "
        "their side if they are not responding, keep them warm and don't give them anything to "
        "eat or drink while you wait.",
        "Ring 999 or 911 now and give the age and what you can see - the colour, the cold or "
        "clammy skin, and how they are breathing. Keep them warm and still, don't try to sit "
        "them up or give them a drink, and stay on the line.",
    ),
    # A grown-up who goes pale and sweaty at the gym or in the sun is hot, not shocked, and the
    # ambulance card would be a false alarm: the cooling answer is the one that fits.
    "pale_adult_effort": (
        "Sit down somewhere cool, loosen your kit and drink water in small sips - pale and sweaty "
        "straight after effort is the heat leaving you. If the colour is not back in half an hour, "
        "or you feel faint, sick or confused, ring 111 or 999 rather than pushing on.",
        "That is the effort and the heat rather than a shock: sit down, cool off and get water in. "
        "If you are still pale, clammy or light-headed in half an hour, or you faint, ring 111.",
    ),
    "pale_adult": (
        "Pale, grey or clammy skin with a cold sweat means the blood is not getting round - a "
        "bleed, shock or a heart attack. Sit them down with their head low, loosen anything tight "
        "round the neck or waist, and ring 999 or 911 now: say the colour and any chest pain, "
        "breathlessness or confusion. Don't give them food or drink, don't let them drive or walk "
        "it off, and stay with them until the ambulance comes.",
        "That colour with clammy skin is a body short of blood going round, so treat it as an "
        "emergency rather than a faint to sleep off: sit them down, keep them still and ring 999 "
        "or 911, and say if there is chest pain, a lot of blood lost, breathlessness or "
        "confusion. Nothing to eat or drink, and don't leave them on their own.",
    ),
    # The same answer for the person who is asking about themselves: "sit them down" is advice
    # about somebody else, and "i am pale and clammy" was told to open a window.
    "pale_adult_self": (
        "Sit down on the floor with your head low, loosen anything tight at your neck or waist and "
        "ring 999 or 911 now: pale, grey or clammy skin with a cold sweat means blood is not "
        "getting round, and that is a bleed, shock or a heart attack until it is checked. Don't "
        "eat or drink, don't drive yourself in, and don't be on your own.",
        "That is a call, not a rest: sit or lie down with your head low, loosen anything tight "
        "and ring 999 or 911, and say you have gone pale and clammy. If you have chest pain, have "
        "lost blood, or feel you might pass out, say that first. Don't drive and don't wait to see "
        "if it passes.",
    ),
    "child_fever": (
        "A temperature in a small child is worth a same-day check: ring 111 or your GP today and say "
        "how old they are and what the thermometer says. Keep fluids going and don't wrap them up "
        "warm, and take them to A&E rather than wait if they are floppy, hard to wake, breathing "
        "fast or a rash doesn't fade under a glass.",
        "Ring 111 or your GP today and give them the age and the number; if they are floppy, hard to "
        "wake, breathing fast or a rash doesn't fade when you press a glass on it, take them to A&E "
        "now instead of waiting. Offer drinks often and dress them lightly.",
    ),
    "high_temp": (
        "A temperature that high needs them seen today: ring 111 now, and 999 or 911 if they are "
        "drowsy, floppy, breathing fast or have a rash that doesn't fade under a glass. Give fluids "
        "and don't wrap them up warm.",
        "Ring 111 today and say the number you just gave me; if they are drowsy, floppy or hard to "
        "wake, that is 999 or 911 instead. While you wait, keep them cool, offer sips of water and "
        "check the rash with a glass.",
    ),
    # A child who found the bottle is the poison call, whatever the family calls it.
    "child_drank": (
        "That is a 999 or 911 call now: say what they drank and roughly how much, and don't try to "
        "make them sick. Keep them sitting up, keep the bottle for the crew, and watch their "
        "breathing until they arrive.",
        "Ring 999 or 911 straight away and tell them the drink and the amount - alcohol in a small "
        "child is an emergency even if they seem fine. Don't leave them alone, don't give them food, "
        "and don't try to make them sick.",
    ),
    # A fit that just happened is still an ambulance; the family's known epilepsy is a story.
    "recent_fit": (
        "A first or unexplained fit is a 999 or 911 call now, and if it happens again time it and "
        "ring again. Put them on their side on the floor, nothing in their mouth, and stay with "
        "them until they are properly awake.",
        "Ring 999 or 911 and say they have had a fit and for how long. Lie them on their side, move "
        "hard things away, time it on your phone, and don't hold them down or put anything in "
        "their mouth.",
    ),
    # The same fit, said to the person who had it: no "lie them on their side", no "time it on your
    # phone". A first fit is still the ambulance, and the things they can do alone are the ones in
    # it - not driving, not being alone, not a bath.
    "recent_fit_self": (
        "Ring 999 or 911 now and say it was your first fit and how long it lasted: a first fit is "
        "checked the same day, not next week. Don't drive, don't have a bath or shower on your own, "
        "and ask someone to stay with you while you wait.",
        "That was a fit, and a first one is a 999 or 911 call - say what happened and how long it "
        "went on. Sit down somewhere safe, don't drive, and don't be on your own until you have "
        "been seen; ring again if it starts up again.",
        "Ring 999 or 911 and tell them you have just had a fit and how long it lasted. Nothing to "
        "eat or drink yet, no driving, and keep someone with you - if it comes back before they "
        "arrive, say so on the call.",
    ),
    # Grunting is the sound of a chest working too hard, and it is easy to miss on a phone.
    "grunting_baby": (
        "Grunting is a 999 or 911 call now - it means a small chest is working hard. Keep them "
        "upright and calm, don't feed them while they are like this, and watch their breathing "
        "until the crew arrives.",
        "Ring 999 or 911 and say the baby is grunting when they breathe. Stay with them, keep them "
        "warm and upright, and if they go blue, limp or stop breathing start CPR and say so on "
        "the call.",
    ),
    # A baby too sleepy to feed is how a parent describes a baby going downhill.
    "sleepy_feed": (
        "Too sleepy to feed needs them seen today: ring 111 now, and 999 or 911 if they are hard "
        "to wake or their breathing looks wrong. Try a small feed and note the wet nappies, and "
        "don't wait for the next one.",
        "Ring 111 today and say they are too sleepy to feed and how long it has been. If you can't "
        "wake them properly, that is 999 or 911. Keep them warm, offer small feeds, and note the "
        "wet nappies for the doctor.",
    ),
    # The same emergency said about the user themselves: "my neck is stiff and my head hurts".
    # A red line running from a wound, or redness spreading from it, is lymphangitis: the
    # infection has got into the channels that drain the wound. It is the same-day call, and the
    # 999 call once a fever or a person going downhill is with it. Every shape of it was answered
    # wrongly on main - the wound watch-and-wait ("shows up two or three days after"), a shrug, and
    # once the chest-pain card - so the words are the plain ones: what it is, when to be seen, the
    # word to say on the phone, and how to tell if it is growing.
    "wound_streak": (
        "A red line running up from a wound means the infection is tracking along the channels "
        "that drain it, and that needs seeing today rather than watching: ring 111 or your GP now "
        "and say you have a spreading red line from a wound, and get a same-day appointment. Draw "
        "round the edge of the redness with a pen so you can see if it grows, keep the wound clean "
        "and uncovered, and go to A&E if the redness reaches much further before you are seen.",
        "Redness that is spreading from a wound is the infection on the move, so it is today, not "
        "next week: ring 111 or your GP and get seen the same day, and say the redness is "
        "spreading. Mark the edge with a pen so the next person can see if it has grown, and go "
        "straight to A&E if it moves quickly.",
    ),
    "wound_streak_fever": (
        "A spreading red line with a fever is 999 now: ring 999 or 911 and say you are worried "
        "about sepsis and that there is a red line spreading from a wound - that is the word that "
        "gets them there fast. Don't drive yourself, keep warm, and stay with them until the "
        "ambulance comes.",
        "A wound with a red line spreading from it and a temperature is an emergency, not a "
        "wait-and-see: ring 999 or 911 and say sepsis and spreading redness from a wound. Stay "
        "with them, keep them warm, and don't set off driving.",
    ),
    "red_flags_self": (
        "Ring 999 or 911 now and say you're worried about sepsis or meningitis. Don't drive yourself "
        "and don't wait to see if it passes: stay where you are, keep warm, and have someone with "
        "you until the ambulance comes.",
        "That combination is a 999 or 911 call, not a wait-and-see: tell them you are worried about "
        "sepsis or meningitis. Press a glass on any rash - if it doesn't fade, say so on the call.",
    ),
    # A fall in someone older, when they are up and nothing is obviously wrong. Two sentences: the
    # thing to do today, and the signs that make it today's ambulance instead.
    "old_fall": (
        "Have them looked at today even though they are up - 111 or the GP can check for a hip or a "
        "head knock that does not show at the time. Ring 999 or 911 if they cannot bear weight, are "
        "drowsy or confused, or take a blood thinner.",
        "Get that checked today rather than waiting to see: a fall at that age is worth a look for a "
        "hip or a head knock, even when they seem fine. That is 999 or 911 if they cannot put weight "
        "on it, go drowsy or confused, or are on a blood thinner.",
    ),
    "old_fall_self": (
        "Get yourself looked at today even though you are up - 111 or the GP can check for a hip or a "
        "head knock that does not show straight away. Ring 999 or 911 if you cannot put weight on it, "
        "feel drowsy or confused, or take a blood thinner.",
        "Have a proper look at that today rather than waiting to see: a fall at your age is worth "
        "checking for a hip or a head knock, even when you feel fine. That is 999 or 911 if you "
        "cannot put weight on it, feel drowsy or confused, or are on a blood thinner.",
    ),
    "intruder": (
        "Get into a room you can lock, stay quiet and call 999 or 911; don't go and confront them. "
        "If you're outside, get somewhere busy and lit and call from there.",
        "Lock yourself in one room and ring 999 or 911 - the police would rather come for nothing. "
        "Don't put yourself between them and the door.",
    ),
    "chest_anxiety": (
        "A tight chest that comes with anxiety is usually the fast breathing and the muscles "
        "between the ribs, not the heart, and it eases as the breathing slows: sit down, shoulders "
        "down, make the out-breath longer than the in-breath. Do get the first one looked at - a "
        "same-day word with 111 or your GP - and ring 999 or 911 if it comes on at rest, spreads to "
        "the arm, jaw or back, or comes with sweating, sickness or breathlessness.",
        "Most tight chests that come with stress or a low mood are the breathing, and a slow "
        "out-breath eases it within a few minutes. Sit down, drop the shoulders, breathe out for "
        "longer than you breathe in. Get the first one checked the same day - 111 or your GP - and "
        "ring 999 or 911 for pain that spreads to the arm or jaw, sweating, or breathlessness that "
        "does not settle.",
    ),
    "breath_panic": (
        "Step out of the room for a minute and sit down, shoulders down, and breathe out for "
        "longer than you breathe in. That usually eases it in a few minutes; if it does not, or "
        "there is chest pain or you feel faint, ring 999 or 911.",
        "Get out of there and sit down somewhere quiet, and slow the out-breath right down. If it "
        "has not eased in a few minutes, or there is chest pain, ring 999 or 911.",
    ),
    "choking_help": (
        "Give five sharp back blows between the shoulder blades right now, then five sharp "
        "abdominal thrusts just above the navel, and keep repeating the five and five until it "
        "clears. Call 999 or 911 now, and start CPR if they go limp.",
        "Five sharp back blows between the shoulder blades, then five abdominal thrusts - hard "
        "pulls in and up just above the navel - over and over until the airway clears or the "
        "ambulance arrives. Ring 999 or 911 first, and start CPR if they go limp.",
    ),
    "choking_self": (
        "Give yourself five sharp blows between the shoulder blades, then five hard abdominal "
        "thrusts with your fist just above your navel - or press your upper belly hard against the "
        "back of a chair. Ring 999 or 911 now and stay on the line.",
        "Hard back blows you can reach, then your own fist in and up just above the navel, or the "
        "back of a chair pressed into your upper belly. Call 999 or 911 now, even if it clears.",
    ),
    "choking_baby": (
        "A baby under one gets five sharp back blows with them face down along your forearm, then "
        "five chest thrusts with two fingers on the breastbone, and the five and five again - never "
        "abdominal thrusts. Ring 999 or 911 now, and start CPR if they go limp.",
        "Lay them face down along your forearm, head lower than the body, five sharp back blows "
        "between the shoulder blades, then turn them over for five chest thrusts with two fingers "
        "in the middle of the breastbone. Repeat the five and five, never abdominal thrusts, and "
        "call 999 or 911 now.",
    ),
    # The prevention question is not the rescue: grapes and cherry tomatoes lengthways, sausages in
    # strips, whole nuts later, and a cough that still works is the airway doing its job.
    "choke_prevent": (
        "The shape of the food does most of the work: quarter grapes and cherry tomatoes lengthways, "
        "cut sausages into strips, and keep whole nuts and hard sweets for older children. If she "
        "can still cough or cry, that is the airway clearing itself.",
        "Cut what a small airway can seal: grapes and cherry tomatoes lengthways into quarters, "
        "sausages into strips, no whole nuts yet, and sit them down to eat. A cough or a splutter "
        "means air is still getting through.",
    ),
    # Going blue is the sign that beats every other reading of the line: no air in means no
    # oxygen out, and the person may still be standing.
    "went_blue": (
        "That is an emergency: ring 999 or 911 now and stay on the line. Sit them up if they can, "
        "keep them still and warm, and if the breathing stops or they go limp, start CPR - the "
        "call handler will talk you through it.",
        "Blue lips or a blue face means the body is short of oxygen right now: ring 999 or 911 "
        "and stay on the line, and if they go limp or the breathing stops, start CPR.",
    ),
    "went_blue_self": (
        "That is an emergency: ring 999 or 911 now and stay on the line. Sit upright, keep still "
        "and undo anything tight at the neck, and tell them your lips are blue and you cannot "
        "catch your breath if that is how it is.",
        "Blue lips or a blue face means you are short of oxygen right now, so ring 999 or 911 "
        "and stay on the line rather than waiting to see if it settles.",
    ),
    # Blue lips from the cold: the colour is a warning, the fix is warmth and a careful watch.
    "blue_idiom": (
        "That is the colour a laugh or a held breath turns a face, and it goes back to normal as "
        "soon as the breath does. If it is a child holding their breath in a tantrum, stay calm "
        "and let it pass; mention it to the GP if it happens often.",
        "Holding your breath or laughing that hard turns you blue for a moment, then the colour "
        "comes back on its own - nothing to do but breathe. A child who holds their breath in a "
        "tantrum is best left to finish, and it is worth telling the GP if it keeps happening.",
    ),
    # A joke about laughing is not a crisis, and it is not a weight to carry either: the greeting
    # answer to "i was killing myself laughing yesterday" was "Ugh, that's a lot to carry".
    "laughing_kill": (
        "The laughing kind, then - I will take that over the other sort. What was so funny?",
        "Ha, good. Killed yourself laughing, not the other thing. What set you off?",
    ),
    # A near thing with a heavy object is neither a crisis nor a shrug: "i nearly killed myself
    # carrying that sofa" wants to know how they are now and what to do with a sore back. The
    # words stay off the job itself, because the same reading covers "driving home" and
    # "shovelling snow", and "let someone else take the other end" is advice about a sofa only.
    "near_thing": (
        "That sounds like a proper near thing, and I am glad it was only nearly. How are you now - "
        "anything sore? Ice it for ten minutes at a time today if so, and keep pottering gently "
        "rather than sitting still.",
        "Ugh, that could have gone badly. Go slower with that next time and give yourself a "
        "minute before you carry on; if anything aches now, ice it and keep moving gently.",
        "Glad you are alright. Rest whatever aches, ice it for ten minutes at a time today, and "
        "if a back or a knee is still sore in a few days, get it looked at.",
    ),
    "near_thing_other": (
        "That is a proper near thing, and I am glad it was only nearly. Check that they are moving "
        "everything and that their head is fine, get anything that hurts looked at today, and let "
        "them know you would rather hear about it than not.",
        "Ugh, that could have gone badly. Ask them how they are now rather than telling them to be "
        "careful, and if a knee, a wrist or a head is sore, get it seen today rather than at the end "
        "of the week.",
        "Glad they are alright. Rest and ice whatever aches, and if a sore back or knee is still "
        "there in a few days, that is a GP appointment.",
    ),
    "blue_cold": (
        "Blue lips from the cold mean warm up slowly: get out of the cold, dry off, add layers and "
        "have something warm to drink - no hot bath and no rubbing. If the colour has not gone ten "
        "minutes after you are warm, or you feel confused, drowsy or slurred, ring 111 (999 if you "
        "cannot stay awake).",
        "Get out of the cold, dry off and warm up slowly - layers, a warm drink, and no hot bath. "
        "If the colour is still there ten minutes after you are warm, or you feel confused or "
        "drowsy, ring 111 now (999 if they cannot stay awake).",
    ),
    "blue_cold_other": (
        "Blue lips from the cold mean they need warming up slowly: out of the cold, dry clothes, "
        "layers and a warm drink - no hot bath, no rubbing. If the colour is still there ten "
        "minutes after they are warm, or they are confused or drowsy, ring 111 (999 if they "
        "cannot stay awake).",
        "Bring them out of the cold and warm them up slowly: dry clothes, layers, a warm drink, no "
        "hot bath. If the colour has not gone ten minutes after they are warm, or they are "
        "confused, drowsy or slurred, ring 111 now (999 if they cannot stay awake).",
    ),
    # A hand inside a machine stays where it is: pulling it out is how the injury gets worse.
    "stuck_machine": (
        "That is an ambulance: ring 999 or 911 now. Don't pull them free and don't let anyone "
        "switch the machine on again - turn it off at the wall only if you can reach it without "
        "moving them. Keep them still and warm until help comes.",
        "Ring 999 or 911 now: don't try to pull it out, and keep the machine switched off so it "
        "cannot start again. Stay still and let them bring pain relief and the right tool.",
    ),
    "raynaud": (
        "Fingers or toes that go white, then blue, then red and sore in the cold are usually "
        "Raynaud's: keep them warm, and mention it to the GP, who can check it is nothing else. "
        "If one hand or foot goes cold, pale and painful and stays that way, that is A&E.",
        "That pattern - white, then blue, then red and burning when it warms up - is usually "
        "Raynaud's, and worth a GP word rather than a panic. Warm gloves and a warm drink help; "
        "a hand or foot that stays cold, pale and painful is the A&E trip.",
    ),
    "stuck_machine_self": (
        "Ring 999 or 911 now. Don't pull your hand out and don't let anyone switch the machine "
        "back on - if you can reach the plug or the wall switch without moving it, turn it off. "
        "Stay where you are until the ambulance comes.",
        "That is an ambulance rather than a DIY job: ring 999 or 911, leave it where it is, and "
        "keep the machine off so nobody can start it while you wait.",
    ),
    "mild_choke": (
        "If you can cough, speak or breathe, keep coughing and sip some water - that is the airway "
        "clearing itself. If you can't speak or breathe, that's a real obstruction: ring 999 or "
        "911 and give back blows.",
        "That usually sorts itself: cough it up and take small sips of water. Ring 999 or 911 if "
        "you can't speak or breathe, or if the coughing isn't shifting it.",
    ),
    "gas_left": (
        "Turn the knob off and open the windows and the back door, and don't touch a switch or a "
        "lighter to check - a spark is the whole risk. If you can smell gas at all, get everyone "
        "outside first and then ring 0800 111 999 (UK) or 911.",
        "Go and turn it off now, then open the windows and doors and leave the room while it airs. "
        "If there is any smell of gas, everyone out and ring the gas emergency line from outside: "
        "0800 111 999 in the UK, or 911.",
    ),
    # Bleach with an acid is chlorine gas, and the answer has to work for the person who has
    # already done it and for the one asking whether they can: leave the room, and never the mix.
    # Asked before it is done, the answer is the never: one sentence, one reason, one alternative.
    "bleach_mix_q": (
        "No - bleach with vinegar, ammonia or an acidic toilet cleaner gives off chlorine gas, and "
        "it is the fumes that do the damage. Use one cleaner at a time and rinse it away with plenty "
        "of water before the next, and open a window while you clean.",
        "Never at the same time: that mix makes chlorine gas, and a bathroom is a small room to "
        "breathe it in. One product at a time, rinsed off with plenty of water, is as clean and it "
        "is safe; if you have already mixed them, open the window and get out into fresh air.",
    ),
    "bleach_mix": (
        "Get out of that room and open a window on the way: bleach with vinegar, ammonia or an "
        "acidic toilet cleaner gives off chlorine gas, and it is the fumes that hurt you. Sit "
        "somewhere with fresh air and don't go back to clean it up - tip the bucket away and rinse "
        "it with plenty of water later. If your chest is tight, you keep coughing, or your eyes are "
        "streaming, ring 999 or your poison control line (111 in the UK, 1-800-222-1222 in the US).",
        "Don't stay in the room: that mix gives off chlorine gas and the fumes are the danger, so "
        "open the window, get into fresh air and leave the cleaning for later. Use one cleaner at "
        "a time, rinsed off with plenty of water, and never bleach with vinegar, ammonia or a "
        "toilet cleaner. Tight chest, coughing or streaming eyes after it is 999 or your poison "
        "control line.",
    ),
    "gas_smell": (
        "Don't switch anything on or off - no lights, no flames - and open the doors and windows "
        "on your way out. Turn the gas off at the meter if it's easy to reach, then ring the gas "
        "emergency line from outside: 0800 111 999 in the UK, or 911.",
        "Get everyone away from it: put out any flames, don't touch light switches, open the "
        "doors and windows, and turn the gas off at the meter if you can reach it. Ring 0800 111 "
        "999 (UK) or 911 from outside, and 999 straight away if anyone feels ill.",
    ),
    "co_signs": (
        "Get everyone out into fresh air straight away and ring 999 or 911, and tell them you "
        "think it's carbon monoxide. Don't go back in, and don't switch anything on or off on the "
        "way out.",
        "Treat it as carbon monoxide until you know otherwise: turn everything off, get everyone "
        "outside, and ring 999 or 911. No flames and no light switches, and don't go back in until "
        "the fire service says it's safe.",
    ),
    "co_going_off": (
        "A carbon monoxide alarm that chirps now and then is usually the battery, so change it "
        "today. If it's the full alarm going off, get everyone outside and ring the gas emergency "
        "line - 0800 111 999 in the UK, or 911 - and don't touch switches or use flames.",
        "Work out which it is: a single chirp is the battery, so change it; the full alarm means "
        "get everyone out and ring 0800 111 999 (UK) or 911, with no switches and no flames. If "
        "anyone has a headache or feels sick, treat it as the real thing and call 999 or 911.",
    ),
    "co_leak": (
        "Get everyone out into fresh air and ring 999 or 911, and say you think it's carbon "
        "monoxide. Don't go back in, and don't switch anything on or off on the way out.",
        "That's a gas you can't smell, so treat it as real: open what windows you pass, get "
        "everyone outside and ring 999 or 911. No flames, no switches, and nobody goes back in "
        "until the fire service says it's safe.",
    ),
    "co_place": (
        "Fit it near where you sleep, and by the boiler or gas fire if you have one - at head "
        "height, not tucked behind furniture or right by the cooker. Press its test button when "
        "you put it up and keep the unit until the date on the back.",
        "Put it in the hall outside the bedrooms or on the landing, and a second one near the "
        "boiler: that's where you'd be breathing the gas at night. Being at head height is enough, "
        "since the gas spreads through the room.",
    ),
    "co_test": (
        "Press the test button on the alarm itself - if it's silent, change the battery and try "
        "again - and fit a new unit when it's past the date on the back, usually five to ten "
        "years. Put it where you'd breathe at night: by the bedrooms, and by the boiler if you "
        "have one.",
        "Use the test button on the unit, not a lighter or a match, and change the battery when "
        "it chirps; after five to ten years replace the whole alarm. Fit it near where you sleep, "
        "not tucked behind furniture or right next to the cooker.",
    ),
    "co_fact": (
        "Carbon monoxide mixes evenly with the air instead of sinking, so the alarm works at "
        "breathing height and doesn't need to be on the ceiling. You can't see or smell it, which "
        "is why an alarm and a yearly boiler service are the only warning you get.",
        "It weighs about the same as air and spreads through a room, so don't rely on putting a "
        "detector high or low - anywhere at head height works. There's no smell and no colour to "
        "it, so a headache that eases in fresh air is often the first sign.",
    ),
    "co_mention": (
        "Carbon monoxide has no smell and no colour, so an alarm near where you sleep is the only "
        "warning you get: press its test button monthly, change the battery when it chirps, and "
        "replace the unit every five to ten years. If one ever sounds, or anyone has a headache "
        "with it, get everyone out and ring 999 or 911.",
        "An alarm is worth having in any home with a boiler, cooker or fire: fit it near the "
        "bedrooms, press its test button monthly, and replace the whole unit every five to ten "
        "years. The gas itself gives you a headache, dizziness or nausea before anything worse, so "
        "treat those with a boiler in the house as a reason to get out and ring 999 or 911.",
    ),
    # A bone that is only annoying wants the same-day check, not the ambulance: don't poke at it,
    # don't swallow bread after it, and don't leave it if the swallow or the voice changes.
    "bone_throat": (
        "Don't poke at it with a finger and don't try to push it down with bread. If you can still "
        "swallow your own spit and breathe, ring 111 and get it checked today; if you can't swallow "
        "spit, are drooling or fighting for breath, that's 999 or 911.",
        "Leave it alone - no fingers down the throat and no bread to push it down. Ring 111 for a "
        "same-day check if you can swallow your spit and breathe; if you can't swallow, are "
        "drooling or struggling for breath, ring 999 or 911 now.",
    ),
    "bone_throat_red": (
        "That's 999 or 911 now: a bone that stops them swallowing their own spit, or makes the "
        "breathing hard, needs it out by someone who can see it. Keep them sitting up, don't put "
        "fingers or food in, and stay with them until help comes.",
        "Ring 999 or 911 straight away - not being able to swallow spit, drooling or fighting for "
        "breath means an ambulance. Sit them upright, nothing by mouth and no fingers down the "
        "throat, and stay with them.",
    ),
    "blue": (
        "Blue or grey lips or face mean not enough oxygen is getting through: ring 999 or 911 now, "
        "keep them sitting up if that is easier for their breathing, and stay with them. Say when it "
        "started and whether there is a rash that does not fade under a glass.",
        "That colour change is a 999 or 911 call now, not a wait-and-see. Keep them sitting up "
        "if that is easier for their breathing, stay with them, and say when it started and "
        "whether there is a rash that does not fade under a glass.",
    ),
    # The reader's own lips, said in the second person: "my lips are blue" is not a stranger's
    # colour, and "keep them sitting up" reads as advice about somebody else.
    "blue_self": (
        "Blue or grey lips or face mean not enough oxygen is getting through: ring 999 or 911 now, "
        "sit yourself up so it is easier to breathe, and stay on the line. Say when it started and "
        "whether you have a rash that does not fade under a glass.",
        "That colour change is a 999 or 911 call now, not a wait-and-see. Sit up rather than lying "
        "flat, stay on the line, and say when it started and whether there is a rash that does not "
        "fade under a glass.",
    ),
    # Something up a nose or in an ear: the battery burns tissue within hours, and the ordinary
    # object is one gentle blow rather than a cotton bud.
    "object_in_head": (
        "Don't poke at it: nothing else up there, no cotton buds and no tweezers. If they can breathe "
        "through the other side, one gentle blow with the other nostril pinched and the mouth shut "
        "can shift it; if it won't come out, that is urgent care or A&E today. In an ear, nothing "
        "goes in and no drops - it needs looking at today.",
        "Leave it alone and get it looked at today: nothing else up there, no cotton buds, because "
        "poking at a bead or a pea pushes it further up. "
        "In the nose, pinch the clear nostril and ask them to blow gently once; in the ear, nothing "
        "goes in and no drops. A&E or urgent care if it will not come out.",
    ),
    "object_in_head_battery": (
        "A button battery up the nose or in an ear is A&E now, not later: it burns the tissue within "
        "hours. Don't try to pull it out or put drops in, and ring 999 or 911 if they are finding it "
        "hard to breathe.",
        "That one cannot wait for a GP: a button battery in a nose or an ear burns what it touches, "
        "so go straight to A&E and keep them upright. Don't fish for it and don't put anything in "
        "the ear. Struggling to breathe or a nosebleed that won't stop means 999 or 911.",
    ),
    "swallowed_thing": (
        "Ring 111 (or your local urgent line) today rather than waiting, and keep an identical one to "
        "show them; don't make them sick. Coughing, drooling, pain when they swallow or trouble "
        "breathing is 999 or 911 straight away.",
        "Ring 111 (or your local urgent line) today and take a spare of whatever it was with you; "
        "don't make them sick and don't give them food or drink for now. Coughing, drooling or "
        "struggling to breathe means 999 or 911 instead.",
    ),
    "electric_burn": (
        "Stop using it and unplug it if the plug is safe to touch, then put it outside on concrete "
        "or stone, away from anything that can burn - not in a bag, a bin or the car. If it smokes, "
        "sparks or catches alight, get everyone out and ring 999 or 911.",
        "Unplug it if you can do it without touching anything hot, and take the device outside onto "
        "something that can't burn; a lithium battery that is swelling or smoking can go up in "
        "seconds. Ring 999 or 911 if there are flames or smoke in the room.",
    ),
    "mild_swallowed": (
        "A mouthful of mouthwash, toothpaste or shampoo is not a poisoning: rinse your mouth out, "
        "drink some water, and don't make yourself sick. Ring 111 if you feel sick, dizzy or "
        "unsteady, and keep the bottle if you want to check what was in it.",
        "A sip or a smear of the things in the bathroom cabinet - mouthwash, toothpaste, shampoo, "
        "soap - is washed away with water, and making yourself sick does more harm than the "
        "mouthful did. 111 will talk it through if you start to feel unwell.",
    ),
    "swallowed_ordinary": (
        "That is not an emergency on its own: a crayon, a bit of chalk, a smear of toothpaste or a "
        "bit of soap goes through, so give them a drink of water, wipe out the mouth and keep an eye "
        "on them for an hour or two. Ring 111 if they are sick or you are not sure, and 999 if they "
        "get drowsy, limp, or struggle to breathe.",
        "A little of a crayon, chalk, toothpaste or soap is not a 999 call: water to drink, wipe the "
        "mouth out, and watch them for a couple of hours. 111 will talk it through with you if they "
        "are sick or you are unsure, and drowsy, limp or struggling to breathe is the point to ring "
        "999 or 911.",
    ),
    "poison": (
        "Call 999 or 911 (or your poison control line: 111 in the UK, 1-800-222-1222 in the US) "
        "now, even if they seem fine. Keep the bottle or packet and don't make them vomit.",
        "Treat this as an emergency and ring 999 or 911 straight away, and keep the container so "
        "the medics know what it was; 111 in the UK gives poisons advice if they seem well. Don't "
        "try to make anyone sick.",
    ),
    # Somebody else took the overdose: the words have to be about them, not about the user.
    "poison_other": (
        "Ring 999 or 911 now, even if they seem fine, and tell them what was taken and how much. "
        "Keep the packet or bottle, stay with them and don't try to make them sick.",
        "That's an ambulance job: ring 999 or 911 and say what they took and when. Keep the "
        "container so the crew know what it was, stay with them, and don't make them vomit.",
    ),
    # The sugar first, and the call only for the part sugar cannot fix. Said both ways, because
    # "im diabetic and i feel shaky" is the person themselves and "my dad is diabetic and confused"
    # is someone else.
    "hypo": (
        "That's a hypo, so sugar is the first thing: if they're awake and can swallow, give them a "
        "glass of juice or a full-sugar drink, or three teaspoons of sugar, then test again in ten "
        "minutes. Ring 999 or 911 if they can't swallow, have a fit or are hard to wake - nothing "
        "by mouth then.",
        "That looks like low blood sugar: if they're awake and can swallow, get something sugary "
        "into them now - juice, a full-sugar drink, or three teaspoons of sugar - and check again "
        "in ten minutes. If they can't swallow, fit or won't wake, ring 999 or 911 and don't put "
        "anything in their mouth.",
    ),
    "hypo_no_mouth": (
        "Ring 999 or 911 now: a hypo where they're fitting or won't wake needs the ambulance, not "
        "sugar by mouth. Nothing to eat or drink - if there's a glucagon injection in the house, "
        "use it while you wait, turn them on their side and stay with them.",
        "That's an emergency and the ambulance is the next step: ring 999 or 911, put nothing in "
        "their mouth, use a glucagon kit if there is one, and turn them on their side while you "
        "wait.",
    ),
    "hypo_self": (
        "That's a hypo, so get sugar into yourself now if you can swallow: a glass of juice or a "
        "full-sugar drink, or three teaspoons of sugar, then test again in ten minutes. Ring 999 "
        "or 911 if you can't swallow, have a fit or feel yourself going.",
        "Treat it as low blood sugar now: something sugary you can swallow - juice, a full-sugar "
        "drink, or three teaspoons of sugar - and test again in ten minutes. If you can't swallow "
        "or you start to fit, ring 999 or 911.",
    ),
    "fall": (
        "Don't move them and don't let them get up: ring 999 or 911 and say how they fell and from what "
        "height. Keep them warm and still, don't give them anything to eat or drink, and if they are "
        "not breathing normally start CPR.",
        "That's an ambulance, not a wait-and-see: ring 999 or 911, keep them still and warm where they "
        "landed, and don't try to sit them up or move them. Don't give them food or drink while you wait.",
    ),
    # The same fall said by the person who fell: "keep them still" reads as if it were someone else.
    "fall_self": (
        "Don't try to get up, and don't let anyone move you: ring 999 or 911 and say how you fell. Stay "
        "still and warm where you are, and don't eat or drink anything while you wait.",
        "Stay where you are and ring 999 or 911 - don't try to stand or sit up on your own. Keep warm, "
        "and don't take anything to eat or drink until someone has looked at you.",
    ),
    "fall_check": (
        "Two things decide it: can they get up, and did they hit their head? If they cannot put "
        "weight on it, are dizzy or sick, or are not quite themselves, ring 999 or 911; if they are "
        "walking about normally, rest it and get it looked at if it is still sore tomorrow.",
        "Is it just bruising, or is something not right? A person who cannot get up or put weight on "
        "it, who hit their head, or who seems confused is 999 or 911; someone who got up and is "
        "walking fine can ice it and take it easy.",
    ),
    # A fall that keeps happening is not a fall that just happened: nobody is on the floor, and
    # what stops the next one is a review of blood pressure, medicines, eyesight and balance.
    "fall_pattern": (
        "A fall that keeps happening is worth getting looked at before the next one: book the GP "
        "and say how many there have been and what brings them on. A falls review goes through "
        "blood pressure, medicines, eyesight and balance, and rails on the stairs help if that is "
        "where it happens.",
        "Falls that keep coming back are worth getting looked at rather than waiting for the next "
        "one: ask the GP about a falls review, which covers blood pressure, medicines, eyesight "
        "and balance. Loose rugs, poor lighting and no rail on the stairs are the other half of it.",
    ),
    # The same pattern said by the person it happens to.
    "fall_pattern_self": (
        "A fall that keeps happening is worth getting looked at before the next one: book the GP "
        "and ask for a falls review, and say how often it happens and what brings it on. Blood "
        "pressure, medicines, eyesight and balance are usually where the answer is.",
        "Worth getting that looked at rather than waiting for the next one: book the GP and ask "
        "about a falls review of your blood pressure, medicines, eyesight and balance. Say how "
        "many there have been and what you were doing when it happened.",
    ),
    "scald": (
        "That's past first aid, so ring 999 or 911: cool the burn under cool running water for twenty "
        "minutes and keep the rest of the body warm, and don't burst blisters, peel clothes off the skin or "
        "put anything on it. Take off any jewellery near it if it comes off easily.",
        "Ring 999 or 911 for this one: cool it under cool running water for twenty minutes while you "
        "wait, keep the rest of the body warm, and don't put ice, butter or cream on it. Cover it loosely "
        "with cling film if you can, and don't burst any blisters.",
    ),
    "pet_emergency": (
        "That needs a vet now rather than in the morning: ring the practice and say what happened, and "
        "if it is closed their line will give you the out-of-hours number. Keep the animal warm, quiet "
        "and still, don't try to make it sick, and take the packet or what is left of it with you.",
        "Ring your vet now and describe exactly what happened: a pet that cannot breathe, is bleeding or "
        "has swallowed something poisonous is one they will want to see tonight. Keep it calm and warm "
        "on the way, and bring the wrapper so they know what they are dealing with.",
        "This is a call to the vet, not a wait-and-see: say what happened and ask for the out-of-hours "
        "number if the surgery is shut. Don't give it food, water or anything to make it sick, and keep "
        "it warm and still until you go.",
    ),
    # An animal's burn is a vet's, and the person's burn card is the wrong card for it: it talks
    # about a face, hands and joints, and a dog with a scalded pad is not going to hold still under a
    # tap for twenty minutes on its own. Cool water first is the same, and the vet is the second half.
    "pet_burn": (
        "Cool it under cool running water for at least ten minutes - a pad or a nose can be held "
        "under a tap or stood in a bowl of cool water - and don't put ice, butter or cream on it. "
        "Then ring your vet today: a burn on a pad, an ear or near an eye needs looking at, and a "
        "burnt nose or a burn that has blistered is an out-of-hours call.",
        "Ten minutes of cool running water is the first thing, and a bowl of cool water does it for a "
        "pad. Nothing from the bathroom cabinet goes on it, not even a cream made for people. Ring "
        "the vet today and say what happened and what burnt it, and ring the out-of-hours line if a "
        "pad, an ear or an eye is involved or the skin has blistered.",
    ),
    # A pet that cannot get its air is a vet's night of its own: what helps on the way is being
    # still and cool, not the poison advice about bringing the packet.
    "pet_breath": (
        "Ring your vet now and say it is struggling for its breath: that is one they want to see "
        "tonight, and the practice line gives you the out-of-hours number if it is shut. Keep it "
        "still, cool and as calm as you can, don't put anything in its mouth or round its neck, and "
        "say how long it has been going on and whether it was at rest or after exercise.",
        "That is an out-of-hours call to the vet: a pet that has to gasp for air is not one to leave "
        "till morning. Carry it rather than making it walk, keep its head and chest up, keep the room "
        "cool and quiet, and don't strap anything round its chest or put your fingers in its mouth.",
        "Ring the vet now and describe the breathing, when it started and whether the gums look pale "
        "or blue: they will tell you to come in or what to do on the way. Keep it cool and still, and "
        "don't give it food, water or anything to settle it.",
    ),
    # A pet that is out of puff on the stairs is not a gasp for air, so this is the appointment
    # rather than the night: the pattern of a dog slowing down is a heart or a lung that is worth
    # finding early, and the line still says what would make it tonight.
    "pet_breath_mild": (
        "That one is the vet's rather than a wait: a pet that is puffed out on the stairs, or slower "
        "on the hill than it was a few months ago, usually has a heart or lung problem that is much "
        "easier to treat early. Book a visit this week, and ring today if it is breathless while "
        "lying down, its gums look grey or blue, or it cannot settle after a rest.",
        "Worth a vet appointment this week: slowing down on the stairs is how a dog or cat with a "
        "heart or a chest that is not right first shows it, and it is the kind of thing that is "
        "easier to help early. Ring today instead if it is breathing hard at rest or its gums look "
        "pale or blue.",
    ),
    # A fit or a collapse is a different night from "it ate something": what helps in the first
    # minutes is time it, keep it safe, don't hold it, and go in even if it passes.
    # A pet that is dying is a loss, not a crisis and not a shrug. The loss module answers the
    # lines it reads ("my dog is dying"); this is the future tense it does not, and the decision
    # to put an animal to sleep, which is the same grief a week early.
    "death_already": (
        "I'm so sorry, that is a terrible thing to have happen. Be gentle with yourself, and if it "
        "keeps sitting on you, a bereavement service like Cruse (0808 808 1677) is there for "
        "exactly this - or your GP, who can put you in touch with someone local.",
    ),
    "pet_loss": (
        "I'm sorry. Knowing it is coming does not make it any easier, and it is allowed to be "
        "awful. Ask your vet what to expect and what the signs are that say today rather than "
        "next week, and if it is today, ask someone to come with you - you do not have to be on "
        "your own for it.",
        "That is a hard thing to be carrying. Ring the vet and ask them to talk you through what "
        "happens next and how much they think the animal is suffering; that is the question "
        "people are usually too polite to ask. Be kind to yourself afterwards - a pet is family, "
        "and it deserves to be grieved like one.",
    ),
    "pet_collapse": (
        "Ring your vet now, and say when it started and whether your pet has eaten: one that will "
        "not respond to you, or has stopped moving about, is one they will want to see tonight. "
        "Keep it warm and quiet in a carrier or a box on the way and don't try to give it anything "
        "by mouth.",
        "That is a call to the vet now rather than in the morning, even if it is late. Note the "
        "time this started, keep it warm on the way and take anything it may have chewed with you. "
        "If you cannot reach your own vet, ring the out-of-hours number on their answerphone.",
        "That needs a vet tonight. Keep your pet still and warm, cover it lightly if it is cool to "
        "the touch, and ring the out-of-hours line: say what it has eaten today and when it last "
        "moved on its own.",
    ),
    # A pet with one side gone weak is having a stroke or a balance problem of its own, and "ring
    # 999 and say you think it's a stroke" is advice about the wrong patient. Same urgency, the
    # vet's number, and the time it started is the thing the vet asks for first.
    "pet_weak": (
        "That is a vet call now: one side going weak, or a head that has tilted, is how a stroke or "
        "a balance problem shows in a dog or a cat, and the sooner it is seen the more can be done. "
        "Note the time it started, keep it quiet and warm, and ring the out-of-hours line if it "
        "cannot stand or gets worse on the way.",
        "Ring your vet now rather than waiting for the morning. A weak side or a head held to one "
        "side needs examining the same day, so note when it started, carry it rather than let it "
        "walk, and use the out-of-hours number tonight if it stops eating or cannot get up.",
    ),
    "pet_fit": (
        "Ring the vet now, and time the fit if it is still going: clear the floor around it, keep the "
        "room dim and quiet, and don't hold it down or put anything in its mouth. A first fit, one "
        "longer than a few minutes, or a second one in a row means the out-of-hours number tonight; "
        "if it passes, still ring in the morning and say how long it lasted.",
        "That is a vet call today, and tonight if it is still going on: note the time it started, "
        "move furniture away from its head and keep it cool and quiet. Never put your fingers or a "
        "spoon in its mouth, and don't wrap it up tight. Ring the out-of-hours line if it goes on "
        "more than three or four minutes, or comes back.",
    ),
    "bleeding": (
        "Call 999 or 911 now. Press hard on the wound with a clean cloth and keep pressing, without "
        "lifting it to look; if you can, raise the injury above the heart.",
        # "Until help comes" and "the first ones off", not "they/them": in this reply those words
        # are the ambulance and the cloths, so the person-aware rewrite must not turn them into
        # "until she comes ... rather than removing her".
        "That's an ambulance job: ring 999 or 911. Until help comes, press firmly on the bleeding for "
        "at least ten minutes without letting go, and add cloths on top rather than taking the first "
        "ones off.",
    ),
    # Not an ambulance on its own words: press harder, add a cloth, and have it seen the same day.
    "bleeding_wont_stop": (
        "Add another cloth on top of the first and keep pressing for ten minutes without lifting it "
        "to look - lifting is what starts it again. If it still comes through, or they go pale or "
        "dizzy, that is 999 or 911; otherwise it needs seeing today, so ring 111 for the nearest "
        "walk-in or A&E.",
        "Press hard on it and put a second cloth over the first rather than taking it off to look; a "
        "cut that soaks through needs a nurse or A&E today, and 111 will say which. Pale, dizzy or "
        "faint with it means 999 or 911.",
    ),
    "stroke": (
        "Call 999 or 911 immediately and say you think it's a stroke. Note the time the symptoms "
        "started, keep the person sitting and still, and don't give them food or drink.",
        "That needs an ambulance now, not a wait-and-see: ring 999 or 911 and say you suspect a "
        "stroke. Write down the exact time it started; drugs work best in the first hours.",
    ),
    "chest": (
        "Call 999 or 911 now and describe the chest pain; say if it spreads to the arm or jaw. Sit "
        "down and rest while you wait, and unlock the door for the paramedics.",
        "Ring 999 or 911 straight away: chest pain like that needs checking today, not next week. "
        "Sit and stay still until the ambulance arrives, and don't drive yourself.",
    ),
    # Same emergency, said through the jaw or one arm with no chest in the line at all, so the
    # reply must not describe a chest the person never mentioned (gentle-chair, #safety 18903).
    "chest_limb": (
        "An arm or a jaw that aches along with sweating, feeling sick or breathlessness is a heart "
        "attack until it is checked: ring 999 or 911 now, sit down and stay still, and unlock the "
        "door for the paramedics.",
        "That arm-and-jaw ache with sweating or feeling sick is a 999 or 911 call now, not a wait "
        "and see. Sit down, stay still, and don't drive yourself there.",
    ),
    # Numbness in one arm, with no chest in the line: sudden is the stroke question, and the slow
    # kind is a trapped nerve, so the reply asks which one it is instead of talking about a chest.
    "arm_numb": (
        "A left arm that has gone numb is worth 999 or 911 if it came on suddenly, and especially "
        "with a droopy face, slurred speech or weakness on that side - say when it started, because "
        "the time matters. If it crept on over days it is usually a trapped nerve, and 111 can get "
        "you seen today.",
        "Ring 999 or 911 if that numbness arrived suddenly, or if one side of the face or the speech "
        "has gone odd too, and tell them the time it started. Numbness that has built up slowly is "
        "more often a nerve or a neck problem: 111 today, and keep the arm moving gently.",
    ),
    "floppy_soft": (
        "Going floppy as they drop off is normal baby tiredness, as long as they are themselves and "
        "feeding when awake. Ring 999 if they are floppy when awake, hard to wake, not feeding, or "
        "breathing oddly - and 111 today if you are at all unsure.",
        "Floppy on the way to sleep is usually just tiredness; babies go boneless as they nod off. "
        "What is not normal is floppy when awake, hard to wake, not feeding or a fever: 999 for "
        "those, and you can ring 111 for advice any time.",
    ),
    "floppy_child": (
        "Don't wait with a child that floppy or that hard to wake: ring 999 or 911 now, and stay on "
        "the line. Keep their airway open and them warm on their side, and watch their breathing "
        "until help comes.",
        "That needs an ambulance now, not a wait-and-see: ring 999 or 911 and say what you've "
        "noticed - floppy, limp, hard to wake, not feeding. Keep them warm, on their side, and "
        "watch their breathing while you wait.",
    ),
    "locked_in": (
        "Don't wait on this one: ring 999 or 911 and tell the operator they have shut themselves "
        "in with something to hurt themselves with. Stay by the door and keep talking, and let the "
        "police and ambulance do the breaking in.",
        "Ring 999 or 911 now and say they are locked in with the pills or a blade; stay by the door "
        "talking to them and let the police break it in - that is their job, not yours.",
    ),
    "not_breathing": (
        "That's CPR now: ring 999 or 911 on speaker, lay them flat and start 30 hard, fast "
        "compressions in the centre of the chest, then 2 rescue breaths; don't stop until help "
        "takes over.",
        "Ring 999 or 911 and start CPR straight away: 30 compressions in the centre of the chest, "
        "then 2 rescue breaths, kept going until the ambulance arrives.",
    ),
    # New breathlessness on the stairs or a hill is worth a GP check, which is what a knowledgeable
    # friend says; the 999 half is kept so the person knows what would change the answer.
    "breath_exertion": (
        "Being short of breath on the stairs or a hill, when that is new, is worth a GP check in "
        "the next week or two - they can listen to your chest and check the heart and bloods, and "
        "a cough or a wheeze is worth mentioning then. Breathless sitting still, chest pain, blue "
        "lips or a faint is 999, not a wait.",
        "That is one to have looked at: new breathlessness on the stairs or a hill deserves the GP "
        "within a week or two, and they will listen to the chest and check the heart and bloods. "
        "Chest pain, blue lips, a faint, or being breathless at rest would be 999.",
    ),
    # Breathless on the stairs with sweat or a faint feeling is not fitness: the everyday answers
    # were saying "being puffed after stairs is usually just fitness" to a line describing the
    # start of a heart attack. The number comes first, because that is the thing to do now.
    "breath_effort_heart": (
        "Ring 999 or 911 now rather than wait to see how you feel: breathlessness with sweating, "
        "clamminess or feeling faint or sick, on an effort that used to be easy, is how a heart "
        "problem starts. Sit down somewhere safe, stay on the line, and do not drive yourself.",
        "That is a call to make now, not a fitness question: being that puffed with sweat or a "
        "faint feeling, on the stairs or the hill, needs 999 or 911. Sit down, unlock the door "
        "and stay on the line, and say if there is any pain in the chest, arm or jaw.",
    ),
    "breath_meal": (
        "Being short of breath after a meal, when that is new, is worth a GP check in the next week "
        "or two: they can listen to your chest and check the heart and bloods. Breathless sitting "
        "still, chest pain, blue lips or a faint is 999, not a wait.",
        "That is one for the GP rather than an ambulance: new breathlessness after eating deserves "
        "a check in the next week or two, with the chest listened to and the heart and bloods "
        "checked. Breathless at rest, chest pain, blue lips or a faint means 999.",
    ),
    # A blocked nose or a chesty cold does explain being puffed out, but "I'm listening" is not an
    # answer to a symptom: the same-day line says what it is and what 999 would look like.
    "breath_cause": (
        "A chesty cold or a blocked nose can leave you puffed out, and it is worth a same-day word "
        "with 111 or your GP today, mentioning the breathing as well as the cold. Breathless "
        "sitting still, chest pain, blue lips or a temperature that will not come down is 999.",
        "That is one to have looked at today rather than a wait: ring 111 or your GP and say the "
        "cold comes with breathlessness, because a chest infection is the thing worth ruling out. "
        "Chest pain, blue lips, breathless at rest or a fever you cannot bring down means 999.",
    ),
    "breathing": (
        "Call 999 or 911 now. Sit upright, stay calm, and if there's an asthma inhaler or an "
        "adrenaline pen, use it as prescribed while you wait.",
        "That's an emergency: ring 999 or 911 and stay on the line; the call handler will tell you "
        "what to do. If they stop breathing normally, start CPR if you can.",
    ),
    # A breath that failed and came back still needs a person seen today, and needs 999 if it is
    # happening again. Two sentences, the number first, because that is the one thing to do now.
    "breath_past": (
        "Ring 999 or 911 now if the breath fails again or the lips look blue. If it has settled, "
        "ring 111 today and say how long the breath stopped and what set it off - a coughing fit "
        "that stops the breath is a same-day check, not a wait-and-see.",
        "Ring 111 today with what set it off and how long it lasted, and ring 999 or 911 if it "
        "happens again or the lips look blue - a breath that stopped, even for a moment, wants a "
        "doctor today.",
    ),
    "crush": (
        "Ring 999 or 911 now and say someone is trapped under something heavy: don't try to lift it "
        "off them yourself or move them, keep them warm and still, and keep talking to them until "
        "help comes.",
        "That is a 999 call: someone crushed or trapped needs the ambulance, and moving the weight "
        "or the person can make it worse. Stay with them, keep them warm, and tell the operator "
        "what has them pinned.",
    ),
    "unconscious": (
        "Call 999 or 911 now. Put them on their side in the recovery position, tilt the head back "
        "so the airway stays open, and don't leave them alone.",
        "Ring 999 or 911 straight away. Keep them on their side, check they're breathing, and stay "
        "with them until help comes.",
    ),
    # A blackout, said to the person it happened to and to the one who watched it. The composer's
    # faint line says to be seen this week, which is right for a hot room and wrong for the three
    # ways a blackout is the heart, so this card says today and says why.
    "blackout_self": (
        "A blackout is only 'just a faint' once someone has checked why, and going down at exercise, "
        "with chest pain or a racing heart, or waking up on the floor is the heart until it is "
        "ruled out: ring 999 or 911 now, and don't drive yourself anywhere.",
        "Ring 999 or 911 now and say you passed out and how long for. Passing out during exercise, "
        "with a racing heart, or coming round on the floor is not a wait-and-see, and you should "
        "not be on your own or driving until it has been checked.",
    ),
    # A blackout that keeps happening with nothing else wrong is the same-day question, not the
    # ambulance: two in a month is a GP-and-111 problem, and saying 999 to it would make an ordinary
    # line into an emergency the person has to talk themselves out of.
    "blackout_today": (
        "Blackouts that keep happening need looking into properly, and today rather than this week: "
        "ring 111 or your surgery now and say how many, what you were doing and whether you were "
        "hurt. Don't drive until it has been sorted, and if one lasts more than a minute or you are "
        "not right afterwards, that's 999.",
        "Ring 111 today and describe each one - how many, what you were doing, and whether you were "
        "hurt - because the pattern is what they need. Nothing behind the wheel until it has been "
        "checked, and 999 if one goes on or you are confused after it.",
    ),
    "blackout_other": (
        "Ring 999 or 911 now if they are still out of it, and keep them lying down on their side "
        "with the head back. If they are awake and talking, they still need to be seen today: "
        "passing out at exercise, with chest pain, or waking on the floor is the heart until a "
        "doctor has said otherwise.",
        "Keep them lying down and check they're breathing normally, and ring 999 or 911 saying they "
        "passed out and how long for. If it happened at exercise or they came round on the floor, "
        "they need to be seen today rather than this week.",
    ),
    "seizure": (
        "Call 999 or 911 now. Don't hold them down or put anything in their mouth: cushion their "
        "head, time how long it lasts, and turn them on their side once it stops.",
        "Ring 999 or 911 straight away. Move anything hard out of the way, cushion their head and "
        "time it; don't restrain them or put anything in their mouth.",
    ),
    "drowning": (
        "Call 999 or 911 now. If they're not breathing normally, start CPR and keep going until "
        "help arrives; even if they seem fine, they need checking in hospital.",
        "Ring 999 or 911 immediately and say they were in the water. Start CPR if they're not "
        "breathing, and get them checked even if they seem okay now.",
    ),
    # The reader is the one who was under the water: "get them out" is the wrong thing to say to
    # the person it happened to, so this is said to them.
    "drowning_self": (
        "Ring 999 or 911 now and say you were under the water and could not breathe: that needs "
        "checking even if you feel alright now, so don't drive yourself there.",
    ),
    "self_harm_other": (
        "Stay with them and don't leave them alone; take away anything they could use and ring 999 "
        "or 911 if they've taken something or are in immediate danger. A crisis line (116 123 in the "
        "UK, 988 in the US) can talk it through with you as well as them.",
        "Ask them straight out if they're thinking of killing themselves, and stay while they "
        "answer. Ring 999 or 911 if they're in danger now, and put a crisis line on speaker — "
        "116 123 in the UK, 988 in the US.",
    ),
    "overdose_other": (
        "Ring 999 or 911 now and say what they took and when; keep the packet or bottle for the "
        "medics and don't leave them alone. If they took it on purpose, tell the operator and put a "
        "crisis line on speaker — 116 123 in the UK, 988 in the US.",
        "Treat this as a medical emergency: call 999 or 911 and tell them what and how much was "
        "taken. Stay with them, keep the container, and if it was deliberate ask them straight out "
        "and get a crisis line on speaker (116 123 UK, 988 US).",
    ),
    "gas": (
        "Treat that as an emergency: don't switch anything on or off, get everyone outside and "
        "call the gas emergency line from there — 0800 111 999 in the UK, or 911 in the US.",
        "Get out without touching light switches, and call the gas emergency line from outside: "
        "0800 111 999 in the UK, or 911 in the US. Don't go back in until you're told it's safe.",
    ),
    "chest_work": (
        "Get that checked this week rather than tonight: chest pain on exercise needs a GP "
        "appointment. If it ever comes with crushing pain, breathlessness, sweating or pain down "
        "your arm or jaw, that's 999 or 911.",
        "Worth a GP appointment this week - chest pain when you exercise is something to have "
        "looked at. Anything crushing, spreading to the arm or jaw, or leaving you breathless means "
        "ring 999 or 911 instead.",
    ),
    "chest_slow": (
        "A tight chest that has been going on for weeks needs a GP appointment this week, not an "
        "ambulance. If it turns into crushing pain, spreads to your arm or jaw, or you get short of "
        "breath, that changes: ring 999 or 911.",
        "Book a GP appointment this week: weeks of tightness is worth looking at properly. Anything "
        "crushing, spreading to the arm or jaw, or leaving you breathless is 999 or 911 straight away.",
    ),
    # A wild animal's bite is the same small wound as a dog's: wash it, cover it, get it seen the
    # same day, and check the tetanus. "a fox bit me" reached "Got it" on main (sleek-sparrow,
    # #safety 96098).
    # An insect bite is an itch: an antihistamine, a cold flannel and hands off it, and the only
    # thing to watch for is an infection days later.
    "insect_bite": (
        "An antihistamine and a cold flannel on it settles the itch, and the one thing that matters "
        "is not scratching it open, because that is how a bite turns into a sore. Ring 111 if a red "
        "area spreads, it goes hot and tender, or you get a fever over the next few days.",
        "Wash it, put a cold flannel on it and take an antihistamine if it is driving you mad - try "
        "not to scratch, since broken skin is what gets infected. A bite that spreads red, swells up "
        "hard or comes with a temperature a few days later wants a pharmacist or 111.",
    ),
    # A tick wants out properly and then a month of watching, which is nothing main answered.
    "tick_bite": (
        "Get it out with fine tweezers or a tick tool, gripping as close to the skin as you can and "
        "pulling straight up without twisting or squeezing, then wash the spot. Over the next month, "
        "watch for a round rash spreading out from it or a fever and aching like flu - if either "
        "turns up, tell a GP you had a tick, because that is treated with antibiotics.",
        "Fine tweezers, gripped close to the skin, straight up and no twisting - a squeezed tick puts "
        "more into you. Then note the date: a spreading round rash, or a fever and aches in the next "
        "few weeks, means a GP visit and the words \"tick bite\", which is a course of antibiotics.",
    ),
    "wild_bite": (
        "Wash it under running water for five minutes, cover it with a clean dressing, and get it "
        "seen today: a bite that breaks the skin needs a tetanus check, and one on the hand, the "
        "face or over a joint goes to A&E rather than a wait. Ring 999 or 911 if the bleeding is "
        "heavy or the wound gapes.",
        "Rinse it under the tap for a good five minutes - animal bites infect easily - then cover it "
        "and get it looked at today rather than waiting to see how it goes. Tell them when your last "
        "tetanus was, and go to A&E if the bite is on a hand, the face or over a joint.",
    ),
    # A bat is the one bite where a mark that barely shows still needs a same-day call: bat rabies
    # is in the UK and the vaccine course starts straight away, so this is a phone call today, not
    # a plaster.
    "bat_bite": (
        "A bat bite or scratch needs a same-day call even if the skin barely breaks: wash it with "
        "soap under running water for fifteen minutes, then ring 111 (or your doctor) today to ask "
        "about rabies treatment. Treatment works best started straight away, so don't wait to see "
        "how it looks.",
        "Wash it under running water with soap for fifteen minutes and ring 111 today rather than "
        "tomorrow: a bat bite or scratch carries a rabies risk even when the mark is tiny, and the "
        "vaccine is a course that starts now. If you are not sure it broke the skin, ring and ask - "
        "that is what the line is for.",
    ),
    "dog_bite": (
        "Wash the bite under running water for a few minutes, then cover it with a clean dressing "
        "and have it looked at today - a bite on the face or hand goes to A&E. Ring 999 or 911 if "
        "the bleeding is heavy, the wound gapes, or the dog is still going for someone.",
        "Clean it under running water and cover it, and get it seen today: bites on the face, "
        "hands or over a joint need A&E rather than a wait, and any bite that breaks the skin needs "
        "checking for tetanus. Ring 999 or 911 if the bleeding is heavy or the wound is gaping.",
    ),
    # A bite on an animal is the vet's, and a cat's bite is the one that abscesses fastest, so the
    # cat gets the teeth said out loud and everything else gets the wound.
    # An animal's tooth is the vet's, not a dentist's: the socket advice is the right thing for a
    # person and the wrong thing for a dog, cat or rabbit, and the tooth has a few hours rather
    # than the half hour a person's does.
    "pet_tooth": (
        "That one is the vet's, not a dentist's: keep the tooth in milk and get them seen today - a "
        "tooth that goes back within a few hours has the best chance. Don't push it back in "
        "yourself, keep them calm and away from chews, and ring the emergency vet if the bleeding "
        "will not stop or their breathing changes.",
    ),
    "pet_bitten_cat": (
        "Ring the vet today rather than wait and see: a cat's teeth push bacteria deep, so a bite "
        "abscesses within a day or two, and one over a joint or on the face is the case they want "
        "to see fastest. Bathe it with cooled boiled water and salt, keep antiseptic off it and stop "
        "the cat licking it. Then report the dog to the council's dog warden with the date, time and "
        "place, and say if a person was bitten too.",
        "That is a vet visit today, not a wait-and-see: bites from a dog tear and infect, and a cat "
        "goes downhill quietly. Keep them warm and quiet on the way and ring ahead so they are ready. "
        "Report the dog to the council's dog warden as well - a dog that has attacked another animal "
        "is their job - and keep the vet's note for the report.",
    ),
    "pet_bitten": (
        "That is a vet visit today, not a wait-and-see: a bite that tears the skin infects quickly, "
        "and an animal that has been attacked often goes quiet rather than making a fuss. Bathe it "
        "with cooled boiled water and salt, keep them warm on the way and ring ahead so they are "
        "ready. Report the attacking dog to the council's dog warden with the date, time and place, "
        "and keep the vet's note for it.",
        "Ring the vet today and describe what happened, and say if the animal is limp, off its food, "
        "or the wound is swelling, because those move it up the list. Cooled boiled water and salt "
        "on the wound, nothing else on it, and no letting them lick it. Report the dog to the "
        "council's dog warden as well - a dog that has attacked another animal is their job.",
    ),
    "dog_attack": (
        "Ring 999 or 911 and don't get between them: shout loudly and, if you have to, use something "
        "solid rather than your hands. Every bite needs looking at the same day, even a small one.",
        "Call 999 or 911 now, and don't put yourself in the way — shout and use a barrier, not your "
        "arms. Bites get infected easily, so get the person seen the same day even if it looks minor.",
    ),
    # The clothes somebody is wearing are part of them, so a garment on fire is a person on fire,
    # and the laundry module's smoke-smell answer is the worst reply in the bot for it
    # (tidy-panther, #safety).
    "clothes_fire": (
        "Stop where you are, drop to the floor and roll, and smother it with anything to hand - a "
        "heavy coat, a towel, a rug - without running, which only feeds it. Then hold the burn "
        "under cool running water for twenty minutes, and ring 999 or 911 if it is bigger than "
        "their hand, if the skin is white or charred, or if they breathed any of it in.",
        "Stop, drop and roll, and smother it with a coat, a towel or a rug instead of running. "
        "Cool the burn under cool running water for twenty minutes; ring 999 or 911 if it is "
        "bigger than their hand, the skin is white or charred, or any of it was breathed in.",
    ),
    # A pan of oil alight has its own answer: water spreads it and carries it means the flames go
    # with you. The building card's "leave straight away" is safe but it is not the ten seconds
    # that decide whether the kitchen goes up.
    "pan_fire": (
        "Turn the heat off if you can reach the dial safely, cover the pan with a lid or a damp "
        "cloth and leave it where it is: never water, and never carry it outside. If it does not go "
        "out, or the flames reach the hood or the wall, get everyone out and ring 999 or 911.",
        "Heat off if you can reach it, then cover the pan with a lid or a damp cloth and leave it "
        "on the hob - water makes it worse and carrying it spreads it. If it does not go out, or "
        "the flames reach the hood, get out and ring 999 or 911.",
    ),
    "hit_in_fun": (
        "That sounds like a game that went a bit far rather than a fight. If it stung, name it "
        "when it happens - \"that actually hurt, I'm not joking\" - and most people get it. If it "
        "was aimed at you on purpose, or it keeps happening, then it isn't a joke and you don't "
        "have to take it as one.",
        "Play between two people is fine, and a slap that lands harder than it meant to is worth "
        "saying out loud there and then. If it was meant to hurt, or it happens again and again, "
        "that is not a joke, and it is fair to say so plainly.",
    ),
    # A burst appendix is an ambulance nobody can spot at home; a nail that went through a
    # shoe is a puncture; a baby off a bed is checked the same day and a baby who is sick,
    # sleepy or floppy after it is the ambulance.
    "appendix": (
        "Ring 999 or 911 now and say you think the appendix has burst: that is an ambulance, not a "
        "wait-and-see. Nothing to eat or drink, sit or lie however is least painful, and don't take "
        "a laxative or painkillers that hide it.",
        "Call 999 or 911 straight away and say the appendix may have burst; that is a hospital "
        "today and an ambulance now. Keep still, nothing by mouth, and don't take anything for the "
        "pain that would mask it.",
    ),
    "puncture": (
        "Get it looked at today at a minor injuries unit or A&E: a nail or a piece of glass that "
        "went into a foot needs cleaning out and a tetanus check even when the bleeding stops, and "
        "the hole closing over is what hides the dirt. Let it bleed a little, press on it with "
        "something clean, keep the foot up, and ring 999 if it is spurting or will not stop.",
        "That needs a minor injuries unit or A&E today rather than a plaster: a puncture traps "
        "dirt and needs cleaning and a tetanus check, and deep ones need looking at properly. Let "
        "it bleed for a moment, press on it with something clean and keep it up, and ring 999 if "
        "the blood is spurting.",
    ),
    "baby_fell": (
        "Ring 111 or take them to be seen today: a child who has fallen off a bed or a sofa is "
        "checked the same day however well they seem, and 999 now if they are being sick, sleepy, "
        "hard to wake, not feeding, or not themself. Keep them with you and watch them closely "
        "for the next 24 hours.",
        "Ring 111 today, or the GP, or take them to A&E if you would rather: a fall from a bed "
        "or a sofa is the one knock nobody can judge at home. Ring 999 instead if there is any "
        "sickness, drowsiness, floppiness or refusal to feed, and keep them with you tonight.",
    ),
    "baby_fell_red": (
        "That is a 999 call: being sick, sleepy, floppy or not themself after a fall is a head "
        "injury until a doctor says otherwise. Keep them with you, awake and warm, nothing to eat "
        "or drink, and say what happened when you ring.",
        "Ring 999 or 911 now rather than watching them for a while: after a fall, sickness, "
        "drowsiness or floppiness needs an ambulance rather than a wait. Keep them awake and with "
        "you, and don't give them anything by mouth.",
    ),
    # Sight that went days or weeks ago is urgent, but it is a clinic today rather than an
    # ambulance: the stroke card said 999 for "i cant see out of my left eye for 2 days", which is
    # a false alarm on a line that needs an eye examination this morning.
    "sight_days": (
        "Ring 111 now and ask for the eye clinic today: sight that went a few days ago needs a "
        "proper eye examination, though it is not an ambulance. Go to A&E straight away instead "
        "if the eye is red and painful, or if the sight went in the last few hours.",
    ),
}

# The alarming-but-general answers: the rash with a stiff neck, the fever that has gone wrong, the
# gas leak, the intruder, the dog attack. Kept beside the cards and out of `bot/modules/safety.py`
# so that module stays under the publisher's 1 MiB file limit. Nothing here is logic, and the
# wording is the safety lane's: moving an answer does not change a word of it.
GENERAL = {
    "pregnancy_bleed": "Any bleeding in pregnancy is checked the same day - ring the midwife or "
                       "maternity unit, and 999 or 911 if it is heavy or you feel faint.",
    "pregnancy_bp": "A bad headache, blurry vision or swelling of the face and hands in pregnancy "
                    "is the maternity unit the same day; 999 or 911 if you feel very unwell.",
    "pregnancy_quiet": "A baby moving less than usual is checked the same day, day or night - ring "
                       "the maternity unit rather than waiting to see.",
    "pregnancy_waters": "Ring the maternity unit when the waters break, with how many weeks you "
                        "are; 999 or 911 if there is bleeding or the baby is moving less.",
    "pregnancy_sick_q": "Feeling sick early in pregnancy is common and usually eases by about 14 "
                        "weeks; ring the midwife the same day if you can't keep food or drink down.",
    "pregnancy_sick": "Sickness that stops you keeping food or drink down, or that lasts all day, "
                      "is worth a call to the midwife or GP the same day; 111 sorts out an "
                      "out-of-hours appointment.",
    "self_harm": "If someone is thinking about suicide, ask them directly and stay with them; a "
                 "crisis line (116 123 in the UK, 988 in the US) can talk it through with either of "
                 "you, and 999 or 911 is right if they've taken something.",
    "swallowed_thing": "A swallowed button battery or magnet is the emergency, whatever the "
                       "object: ring 999 or 911, and never make someone sick to bring it back up.",
    "electric_burn": "A battery that has been smoking, sparking or swelling is not safe to keep or "
                     "recharge: take it outside, keep it away from anything that can burn, and take "
                     "it to a recycling centre that accepts batteries rather than the bin.",
    "blue": "Blue or grey lips, face or fingertips mean the blood is short of oxygen: that is 999 "
            "or 911 now, not a wait-and-see, whatever the cause turns out to be.",
    "fire": "Get everyone out, stay out, and call 999 or 911; smoke kills faster than flames, so "
            "stay low and check doors with the back of your hand before opening them.",
    "gas_smell": "A smell of gas: nothing that can spark, doors and windows open, the gas off at "
                 "the meter if you can, and the emergency line (0800 111 999 in the UK, or 911) "
                 "from outside.",
    "co_signs": "Carbon monoxide has no smell: a headache, dizziness or nausea that eases when you "
                "leave the room is the warning, so get out into fresh air and ring 999 or 911.",
    "co_going_off": "A single chirp is the battery, so change it; the full alarm means get everyone "
                    "out and ring the gas emergency line (0800 111 999 in the UK) or 911.",
    "co_place": "Near where you sleep and by the boiler, at head height; the gas spreads evenly, "
                "so don't worry about the ceiling.",
    "co_test": "Press the test button monthly, change the battery when it chirps, and replace the "
                "unit every five to ten years; fit it near the bedrooms and the boiler.",
    "co_fact": "Carbon monoxide mixes with the air rather than sinking, so anywhere at breathing "
               "height works; it has no smell, so the alarm is the warning.",
    "co_leak": "Carbon monoxide has no smell and no colour: a headache, dizziness or nausea that "
               "eases in fresh air is the warning, and so is a yellow instead of blue flame. Get "
               "everyone out and ring 999 or 911 or the gas emergency line, 0800 111 999 (UK).",
    "co_mention": "Yes - it can kill, and it has no smell or colour, so an alarm near where you "
                   "sleep is the only warning: test it monthly, change the battery when it chirps, "
                   "replace the unit every five to ten years, and ring 999 or 911 if it sounds.",
    "poison": "Call your poison control line straight away (111 in the UK, 1-800-222-1222 in the "
              "US) and keep the container; don't make anyone vomit.",
    "bleeding_wont_stop": "Add another cloth on top and keep pressing for ten minutes without lifting "
                          "the first off; a cut that soaks through or is still going after twenty "
                          "minutes should be seen the same day, at a walk-in centre or A&E, and 111 "
                          "will say which. Pale or dizzy with it means 999 or 911.",
    "bleeding": "Press hard on the wound with a clean cloth and don't lift it to check for at least "
                "ten minutes; if it's spurting or won't stop, that's 999 or 911.",
    "stroke": "Think F.A.S.T.: face drooping, arm weakness, slurred speech, time to call 999 or 911. "
              "Note when it started, because the first hours matter most.",
    "chest": "Sudden chest pain, especially spreading to the arm or jaw with sweating, is 999 or 911. "
             "Sit them down and don't let them drive.",
    "breathing": "Call 999 or 911 and keep them sitting upright; use their inhaler or adrenaline "
                 "pen if they have one, and start CPR if they stop breathing normally.",
    "unconscious": "Check they're breathing, put them on their side in the recovery position, and "
                   "call 999 or 911; if they're not breathing, start CPR.",
    "seizure": "Cushion their head, don't restrain them or put anything in their mouth, and time "
               "it. Call 999 or 911 if it lasts more than five minutes, it's their first, or they "
               "don't come round afterwards.",
    "abuse": "Believe them, and don't confront the abuser. A domestic abuse helpline (0808 2000 247 "
             "in the UK, 1-800-799-7233 in the US) can plan the next step safely with them.",
    "drowning": "Get them out without putting yourself in danger, call 999 or 911, and start CPR if "
                "they're not breathing normally.",
    "gas": "Don't switch anything on or off, open a window, get everyone out and call the gas "
           "emergency line from outside (0800 111 999 in the UK, 911 in the US).",
    "intruder": "If someone breaks in, don't confront them: get everyone into one room, lock the "
                "door, ring 999 or 911 and stay quiet until the police come.",
    "dog_attack": "Don't get between a dog and the person it's attacking; shout, use a barrier, and "
                  "call 999 or 911. Bites need checking the same day because infection sets in fast.",
    "head_injury": "Watch for drowsiness, confusion, vomiting, a worsening headache or clear fluid "
                   "from the nose or ears after a bang on the head — any of those is 999 or 911. "
                   "Otherwise rest, no alcohol or sport for 24 hours, and don't be alone.",
}

# What to do while help is on the way, and what to say once it has arrived: the same scene, said
# to somebody standing next to the person rather than to the person. Beside the cards for the
# same reason as `GENERAL` - the module that decides when to say one stays under the publisher's
# file limit - and not a word of it changes.
WAITING = {
    "overdose": "Stay with them, keep the packet, and tell the 999 or 911 call handler anything "
                "they took earlier; if they get sleepy or stop breathing normally, start CPR and say so.",
    "self_harm": "Stay on the phone with the crisis line and try not to be alone; if you feel you might "
                 "act on it, call 999 or 911 and tell them where you are.",
    "abuse": "Get somewhere safe and keep your phone with you; call 999 or 911 if he comes back, and a "
             "helpline can plan the next step with you when it's safe to talk.",
    "gas": "Stay outside and ring the gas emergency line from there; don't use matches, lighters or "
           "doorbells until the gas engineer says it's safe.",
    "fire": "If the stairs are clear, get out and stay out; if there's smoke in the stairwell, close "
            "yourself in a room, put a towel along the bottom of the door and call 999 or 911.",
    "choking": "Keep giving five back blows and five abdominal thrusts, and call 999 or 911 if you "
               "haven't already; start CPR if they go limp.",
    "not_breathing": ("Stay on the line with the 999 or 911 call handler and keep doing CPR — hard, "
                      "fast pushes in the centre of the chest — until the ambulance arrives or they "
                      "breathe.",
                      "Keep the pushes going, hard and fast in the middle of the chest, and let the call "
                      "handler guide you until the ambulance arrives or they breathe."),
    "poison": "Keep the container and don't make anyone sick; follow poison control's advice, and "
              "call 999 or 911 straight away if sleepiness, confusion or trouble breathing comes on.",
    "bleeding": "Keep pressing on the wound without lifting the cloth to look, and add more cloths on "
                "top if it soaks through; the ambulance crew take over from there.",
    "stroke": "Note the time the symptoms started; sitting still, and no food or drink, until the "
              "ambulance arrives.",
    "chest": "Sitting still and calm is what helps now, and leaving the door unlocked saves the "
             "paramedics time.",
    "breathing": "Sitting upright and calm is what helps, with the inhaler or adrenaline pen used as "
                 "prescribed; start CPR if the breathing stops and keep the ambulance coming.",
    "unconscious": "The ambulance is on its way: keep them on their side, check they're breathing, and "
                   "start CPR if they stop breathing.",
    "seizure": "Cushion their head, time how long it lasts, and don't restrain them or put anything in "
               "their mouth; turn them on their side once it stops and stay with them until the "
               "ambulance comes.",
    "drowning": "If they're not breathing normally, start CPR and keep going until the ambulance "
                "arrives; even if they seem fine, they need checking in hospital.",
    "intruder": "Stay behind a locked door with the 999 or 911 operator on the phone and keep it on "
                "silent until the police say it's safe; note anything you hear or see for them.",
    "dog_attack": "Stay back and keep the dog away from them; press a clean cloth on any bite that's "
                  "bleeding and keep the person warm until the ambulance comes.",
    "head_injury": "Sitting up and awake, no food and no driving; tell the ambulance call handler if "
                   "drowsiness, vomiting or memory loss comes on.",
    "hanging": "Keep them lying on their side with their neck supported and check they're breathing; "
               "start CPR if they're not, and let the ambulance crew take over from there.",
    "heat": "Somewhere cool, clothes loosened and small sips of water; if confusion or no sweating at "
            "all comes on, tell the ambulance crew straight away.",
    "chest_slow": "Don't start aspirin or any other medicine on your own for this; note when the "
                  "tightness comes and what brings it on, and take that to the GP this week. Crushing "
                  "pain, or pain down the arm or jaw, is 999 or 911 instead.",
    "wild_bite": "Wash it under the tap for five minutes and cover it, and get it seen today - a "
                 "bite that breaks the skin wants a tetanus check, and a hand or face bite wants A&E.",
    "bat_bite": "Wash it with soap under running water for fifteen minutes and ring 111 today: a bat "
                "bite carries a rabies risk even when the mark is tiny.",
    "dog_bite": "Rinse it under the tap for a few minutes and cover it with a clean dressing; get it "
                "seen today, and tell them when your last tetanus was.",
    "general": "Follow the ambulance call handler's instructions and stay with them; unlock the door "
               "and don't give them food or drink.",
}

AFTER = {
    "overdose": "Good — stay with them and keep the packet; the ambulance crew will want to know "
                "exactly what and when.",
    "self_harm": "I'm glad you're still here. Stay with someone and keep the crisis line on the phone "
                 "until you feel safe; if it gets worse, call 999 or 911.",
    "abuse": "Good — stay somewhere safe and keep your phone with you. A helpline can plan the next "
             "step with you when it's safe to talk.",
    "gas": "Stay outside until the gas emergency engineer says it's safe, and don't go back in "
            "before that.",
    "fire": "Stay outside and well clear until the fire service tells you it's safe - ring 999 or "
            "911 if nobody has come yet, and don't go back in for anything.",
    "poison": "Keep the container, and tell the ambulance crew exactly what and how much was "
              "swallowed.",
    "bleeding": "Keep the pressure on and leave the cloth in place until the paramedics take over.",
    "stroke": "Sitting still helps, and the time it started is worth writing down - the ambulance "
             "crew will ask.",
    "chest": "Resting and still until the ambulance arrives - no walking about and no driving.",
    "breathing": "If the breathing is easier, staying upright and calm is what helps, and the "
                 "ambulance crew should still check it; use the inhaler or pen again if the symptoms "
                 "come back.",
    "choking": "If they're breathing and talking again, keep them calm and sitting up and get the "
               "ambulance crew to check them; if not, keep going with back blows and thrusts.",
    "not_breathing": "If they've started breathing, put them on their side and stay with them until "
                     "the ambulance arrives; if not, keep doing CPR.",
    "unconscious": "If they're waking up, keep them on their side and calm until the ambulance "
                   "arrives.",
    "seizure": "Once it's over, turn them on their side and stay with them until the ambulance "
               "arrives.",
    "drowning": "Keep them warm and still until the ambulance arrives, even if they seem fine.",
    "intruder": "Stay put and follow the police's instructions from the 999 or 911 call; ask them to "
                "check the house, and don't touch anything the intruder may have touched.",
    "dog_attack": "Wash the bites gently and cover them, and tell the paramedics how many there are; "
                  "keep the dog away and note whose it is for the report.",
    "head_injury": "Someone should keep an eye out for 24 hours - a gentle wake every couple of hours, "
                   "no alcohol or sport - and 999 again if drowsiness, confusion or vomiting comes "
                   "on.",
    "hanging": "Stay with them and keep them still until the paramedics arrive; even if they seem "
               "better, the hospital needs to check their neck.",
    "heat": "Resting somewhere cool and drinking is what helps, and the ambulance crew should still "
            "check it if confusion comes or it returns.",
    "chest_slow": "Keep that GP appointment and keep noting when it happens; if it turns crushing, "
                  "spreads to your arm or jaw, or you get breathless at rest, ring 999 or 911.",
    "wild_bite": "Keep it covered and still get it seen today; tell them when your last tetanus was.",
    "bat_bite": "Keep the wash going and make the 111 call today; the rabies course starts now.",
    "dog_bite": "Keep it covered and clean, and still get it seen today: bites infect easily, and a "
                "bite on the face or a hand needs A&E rather than a wait.",
    "general": "Stay with them and follow the ambulance call handler's instructions until they "
               "arrive.",
}

# A swallow that has gone: the same-day call, with the airway signs named as the reason to ring for
# an ambulance instead. "i cant swallow" was "Got it. Is there anything you'd like a hand with?".
REPLIES["swallow_gone"] = (
    "A swallow that has gone is worth being seen today rather than waiting: ring 111 or your local "
    "urgent line now, because a bad throat infection behind it is treatable and gets worse if it is "
    "left. Drooling, a voice gone muffled, a lip or a tongue that is swelling, or any trouble "
    "breathing is 999 or 911 instead.",
)
