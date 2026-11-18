"""The chat module's reply pools, in their own file.

`bot/modules/chat.py` was 19 KB from the upload budget alarm (`tests/test_the_upload_budget.py`
fires one percent early, at 1,038,091 of 1,048,576 bytes) and `REPLIES` is its largest flat table
at 61 KB, three times the room the file needs back. This is the move that took `safety.py`,
`cooking.py` and `family.py` under the wall: the table stays plain data, `chat.py` imports it, and
no reply changes by a character.

The import binds the same dict object, so `chat.py` still adds to it at import time (it does, for
"ill_lasting") and every reader sees one dict - there is no copy to drift.
"""

from ..compose import fallback

REPLIES = {
    "greeting": (
        "Hi! What's on your mind?",
        "Morning! How's your day going?",
        "Hello! What can I help with?",
        "Hey! What are we working on?",
        "Hi there — what do you need?",
    ),
    # A hello with the chat already running is a check-in, not a new morning: "we had a huge row
    # last night" then "hiya" should not get "Morning! How's your day going?".
    #
    # "What's next?" is fine after a row, a warning at work or a failed test; it is not fine
    # after a death, so a death in the chat is answered from `howareyou_loss` below and a hello
    # after one is left to the composer's loss module. A job lost, a pet ill or a bad week are
    # losses the check-in can ask about, because the person can still change them.
    "check_in": (
        "Hi — still here. Where were we?",
        "Hello again. What's next?",
        "Hi. Anything changed since we last spoke?",
        "Still here, if you want to carry on.",
        "Hello again — carry on where we left off?",
    ),
    # The same check-in for a person the bot has been introduced to, so the name is not lost:
    # "my name is sam" then "hi" was "Hello again. What's next?" for "Hi Sam!".
    "check_in_name": (
        "Hi {name} — still here. Where were we?",
        "{name} — hello again. What's next?",
        "Hi {name}. Anything changed since we last spoke?",
    ),
    # A how-are-you inside a conversation still asks how the bot is, and the check-in pool never
    # answers that: it points somewhere else every time, and two of those in a row have nowhere
    # to go. These answer the question and hand it back.
    # How-are-you after a death in the chat: the question is answered, gently, and handed back
    # without sending the person anywhere ("What's next?" is not a line for a bereaved chat).
    "howareyou_loss": (
        "Still here. No rush to say anything.",
        "I'm all right, thanks. More to the point — how are you doing?",
        "Getting by, thank you. How are you holding up?",
    ),
    "howareyou_mid": (
        "Still here, thanks — how are you getting on?",
        "Doing fine, thanks. How's your day going?",
        "All good here. What about you?",
    ),
    # A hello that names the part of the day gets an answer about that part of the day: the
    # morning pool answered "good evening" with "Morning!" on main.
    "greeting_morning": (
        "Morning! How's your day going?",
        "Morning — what's on your mind?",
        "Morning! What can I help with?",
    ),
    "greeting_afternoon": (
        "Afternoon! What's on your mind?",
        "Afternoon — what can I help with?",
        "Afternoon! How's your day going?",
    ),
    "greeting_evening": (
        "Evening! What's on your mind?",
        "Evening — what can I help with?",
        "Evening! How's your day been?",
    ),
    "greeting_name": (
        "Hi {name}! What's on your mind?",
        "Morning {name}! What can I help with?",
        "Hey {name}! What are we doing today?",
    ),
    "meet": (
        "Hi {name} — good to meet you. What's on your mind?",
        "Nice to meet you, {name}. What can I help with?",
        "Hello {name}! What are we doing today?",
    ),
    "howareyou": (
        "Doing well, thanks — what about you?",
        "All good here. What's keeping you busy?",
        "Can't complain. What's on your mind?",
    ),
    # The person has just answered how they are and handed the question back: "not bad, and
    # you?", "im fine thanks, yourself". The "howareyou" pool cannot answer it - it asks the
    # question the person has already asked - and the reply before this pool said neither how
    # the bot was nor took the question. So it says how the bot is, thanks them for asking, and
    # then gets back to their day. The thanks are said once: "I'm well, thanks - and thanks for
    # asking after me" said the same thing twice, and it is the pool's first line in a chat as
    # well as its second ("hbu" with nothing said yet).
    "back": (
        "All good here, thanks for asking. How has your day been?",
        "I'm well, thanks for asking. How is your day going?",
        "Nothing to complain about here, thanks. How has your day been so far?",
    ),
    # The same line with a bad day in it ("not great, and you?"): the low is answered first and
    # the question second, which is the order a friend would take them in.
    "back_low": (
        "Sorry to hear that. I'm all right, thanks for asking \u2014 what has been going on?",
        "That sounds rough. I'm fine, thanks for asking after me \u2014 what has the day been like?",
    ),
    "notmuch": (
        "Not much here either. What are you up to?",
        "Same as ever — helping, chatting. How's your day going?",
        "Not a lot. What's keeping you busy?",
    ),
    "positive": (
        "Glad to hear it.",
        "Good to know.",
        "Well, good.",
    ),
    "thanks": (
        "Any time.",
        "Glad that helped.",
        "You're welcome — shout if anything else comes up.",
        "No problem at all.",
        "Happy to help.",
        "No worries at all.",
    ),
    "bye": (
        "Bye! Take care.",
        "See you — good luck with it.",
        "Take care. Come back any time.",
        "Bye for now!",
        "Take it easy!",
    ),
    # A sign-off at night gets the night line and a sign-off in the day does not. Both used to
    # come out of one pool, so "cya later" was answered "Night! Sleep well." and "goodnight"
    # was answered "Bye! Take care." - the right words for the wrong half of the day.
    "bye_night": (
        "Night! Sleep well.",
        "Goodnight — sleep well.",
        "Sleep well. I'll be here tomorrow.",
        "Night then. Sleep well.",
    ),
    "next_up": (
        # What the person is doing next, said as they go: no question back, no "first step".
        "Go on then \u2014 enjoy it.",
        "That sounds like the right thing to do tonight.",
        "Good. I'll be here when you're back.",
        "Fair enough. Hope it does you good.",
        "Nice one. Take your time over it.",
        "Right you are \u2014 enjoy the quiet.",
    ),
    # The one pool above is all rest and quiet: "enjoy the quiet" and "hope it does you good" fit a
    # bath and an early night, and read oddly as an answer to a shift or the weekly shop. So the
    # next thing is split by what it is, and each pool says the same warm thing in the words that
    # fit it (@sleek-condor, on "im going to work now").
    "next_rest": (
        "Fair enough. Hope it does you good.",
        "Good. Take your time with it.",
        "That sounds like the right thing to do tonight.",
        "Right you are \u2014 enjoy the quiet.",
    ),
    "next_act": (
        "Go on then \u2014 hope it goes smoothly.",
        "Good. That's your next bit sorted.",
        "Right you are. Take it as it comes.",
        "Nice one. I'll be here when you're back.",
    ),
    "intent": (
        # A plan or an intention aired without a question. It must not presume a snag ("tell me
        # where it gets stuck" fits "i need to sort my pension", not "i want to bake a lemon
        # drizzle for my mum"), so each line asks about the person's own starting point.
        "Worth doing. Where are you with it so far?",
        "Good thing to take on. What's the first step from where you are?",
        "Sounds worth doing \u2014 I'm here when you want the next step.",
        "Worth doing. What would you like help with first?",
    ),
    "event": (
        "That's coming up. What do you want to get right?",
        "How ready do you feel for it?",
        "What would make it go well?",
    ),
    # A stretch of it rather than one hard day (see OVERLOAD): "get an early night" is the wrong
    # advice for a month of it, so these name the run of it and offer one thing to drop. One of
    # the four is a question, so a worn-out person is not asked one every time.
    "overloaded": (
        "Ten quiet minutes between things helps more than it sounds, and so does saying no to "
        "one thing.",
        "Non-stop weeks are the ones that catch up later. Guard one evening this week that's just "
        "yours.",
        "When it's like that, everything else can wait: food, sleep, and one thing that's only "
        "yours.",
        "A run like that wears you down before you notice. Pick the one thing you can drop this "
        "week and drop it.",
    ),
    "busy": (
        "Sounds full-on. What's taking most of it?",
        "Busy one, then. Is there anything you can drop?",
        "That's a lot at once. What would go first if you could choose?",
    ),
    "plan": (
        "Good plan. What sparked it?",
        "Nice. Tell me how it goes.",
        "Sounds like a good way to spend it.",
    ),
    # A plan that changes a medicine is a decision about a prescription, and the one plan here
    # that is not cheered: "im going to come off my antidepressants" was answered "Nice. Tell me
    # how it goes." and "im going to stop my inhalers now the hay fever has gone" with a cheer
    # too. The words and the reason are in `bot/compose/fallback.py`, next to the plan pool, so
    # the chain below this module says the same thing when a reading here stands down.
    "plan_medicine": fallback.PLAN_MEDICINE_REPLY,
    "plan_medicine_slow": fallback.PLAN_MEDICINE_SLOW_REPLY,
    "say_something": (
        "Go on \u2014 I'm listening.",
        "Of course. Take your time.",
        "Ask away \u2014 I'll do my best.",
    ),
    "sorry_talk": (
        "No need to apologise — that's what I'm here for.",
        "You're not dumping anything on me. Keep going if it helps.",
        "Don't apologise for that. I'd rather hear it than not.",
    ),
    "vague": (
        "Sometimes it's everything at once. It can stay unnamed.",
        "Fair enough — days like that are hard to pin down.",
        "That's okay. No rush to work out what it is.",
    ),
    "ack": (
        "Sounds good.",
        "Alright then — good luck with it.",
        "Nice one.",
        "Fair enough.",
        "Hope it works out.",
    ),
    # A bare request for help is a request, and this file read it as an acknowledgement: "help"
    # and "help me" got "Fair enough." - a shrug at the one line in a conversation that asks for
    # something. Every longer shape of it ("help me out", "need help", "i need some help") was
    # already answered by the fallback's "Happy to. Tell me what's going on", which is right after
    # a good day and too bright in the middle of a bad one, so the pool is here and asks the same
    # thing in a voice that fits both.
    "help_ask": (
        "Happy to help. What's the thing you're stuck on?",
        "Of course. Tell me what you need a hand with.",
        "Say what it is you're stuck on and we'll take it from there.",
        "Right — what is it you need help with?",
    ),
    # The nod after heavy news is not a nod at a plan. "my mum has cancer" then "ok" got "Alright
    # then — good luck with it." or "Sounds good." - a cheerful sign-off on the worst thing the
    # person has said, and the last thing they hear before they decide whether to keep talking.
    # Every line here leaves the floor open, and none of them asks for anything.
    "nod_after_news": (
        "Okay. I'm here if you want to come back to it.",
        "No rush. That can just sit there for now.",
        "I'm not going anywhere. Say more when you want to.",
        "Understood. Nothing about it needs doing this minute.",
    ),
    # "again", "not again": the person is saying it has happened once more, which is the whole
    # of the news. The ack pool read it as a shrug and closed the topic.
    "again": (
        "Again? That's rough.",
        "Again — that's hard going.",
        "Again. No wonder you're fed up with it.",
        "Oh no, again.",
    ),
    # A bare "again" carries no trouble of its own: after "i got engaged" it is a second
    # engagement and after "i lost my job" it is the second time, and the pool above read the
    # first as a hard going. Only the shapes that say the repeating is bad ("not again", "oh no
    # not again") get the sympathy; a bare "again" is asked what happened, which fits both.
    "again_what": (
        "Again? Go on.",
        "Again — what happened?",
        "Right, again. What's going on?",
        "Again. Say a bit more.",
    ),
    # Looking forward to something is the warmest short line there is, and it wants the warmth
    # back rather than the flat nod.
    "keen": (
        "Good — that's something to look forward to.",
        "Nice. There's a lot to be said for having it in the diary.",
        "Good. The run-up is half the fun of it.",
        "Nice one — enjoy the wait for it.",
    ),
    # A judgement with no feeling word in it. These used to land on the ack pool: "im not good
    # enough" got "Fair enough.", which reads as agreeing with them, and "thats not great" got
    # the same shrug at bad news. They are feelings, so they are answered like feelings.
    "not_enough": (
        "That's the tiredness talking, not the truth. What happened today?",
        "I doubt that's the whole picture \u2014 you're being harder on yourself than you'd be "
        "on a friend.",
        "Not true. Nobody is only their worst day. What set this off?",
    ),
    # Someone measuring themselves against a role ("a bad dad") or a word ("an idiot"). The
    # read-back the store gives these is the flattest reply there is, and a stock "sorry to
    # hear that" fits any message, so each line names what they did to themselves.
    "own_harsh": (
        "That is a hard thing to say about yourself. What happened today?",
        "You would not say it about a friend who said it about themselves. What went wrong?",
        "One bad day does not make you bad at it. What happened?",
    ),
    # The same words about a habit rather than a role: "im a bad sleeper", "im a terrible
    # dancer", "im a lousy swimmer". Nobody saying that is in distress, and the pool above told
    # them their day weighed on their life, which is the therapist line STYLE.md rules out.
    "own_described": (
        "That is closer to a habit than a fact about you, and habits are the easiest things to "
        "change.",
        "Half the people you know would say the same about themselves, and nobody thinks less of "
        "them for it.",
        "I would not take that as a verdict on you. What is the worst of it?",
    ),
    "not_fair": (
        "It isn't fair, and you don't have to be reasonable about it straight away. What happened?",
        "You're right that it isn't. Some things really aren't, and being cross about it is fair.",
        "That's a real thing to be angry about. Go on, what happened?",
    ),
    # The person was the one who was unfair: "i wasnt fair to her", "i snapped at my mum on the
    # phone" then "i wasnt fair to her". Telling them "you're right that it isn't fair" agrees
    # with the wrong thing; this takes the apology as an apology.
    "own_fault": (
        "That's the kind of thing most people only notice days later. What happened?",
        "Owning it out loud is worth something \u2014 don't turn it into a second thing to feel "
        "bad about.",
        "Then be as kind to yourself about it as you'd be to them.",
    ),
    # Nothing but a reaction to what was just said: "thats scary", "how grim", "thats so
    # annoying". The line carries no news of its own - the news is the turn before it - so the
    # reply agrees and adds one steady thing. Asking "what happened?" here asks for what the
    # person has just been told, and the pool that used to take these said "Thanks for telling
    # me" and "Got it. Is there anything you'd like a hand with?" instead.
    "react_fear": (
        "It is. Nobody would be calm about that, whatever they say.",
        "Fair. Things like that sit on you all day.",
        "Yes, and it's fair to say it out loud. Tell me if you want to work out what to do.",
    ),
    "react_bad": (
        "It is. You don't have to be sensible about it straight away.",
        "Fair enough, and no wonder it's the whole of your head right now.",
        "That's a lot to take in. Give yourself a day before deciding anything.",
    ),
    "react_annoyed": (
        "It is. Being cross about it for a bit is fair enough.",
        "Yeah \u2014 and it's the sort of thing that keeps niggling.",
        "That would wind me up too.",
    ),
    # A sigh ("oh no", "oh dear") says the news has landed and nothing more, so it cannot be
    # met with "It is." - there is no "it" in the line to agree about. It is met with the
    # news, which is why none of these name a feeling the person did not name.
    "react_sigh": (
        "I know. That's a lot to land on you.",
        "Yeah. It's fair to feel that before you do anything about it.",
        "I know. You don't have to have a plan for it yet.",
    ),
    "react_good": (
        "Glad to hear it.",
        "That's lovely news.",
        "Nice one. Say if you want a hand with the next bit.",
    ),
    # "me too", "same here", "so am i": a line that only says the turn before is true of them
    # too. It carries no subject of its own, so the pool is chosen by what was agreed with: the
    # wrong one congratulates somebody on their own complaint.
    "agree_grim": (
        "I know the feeling. It's not just you.",
        "Half the street is with you on that one.",
        "Join the club \u2014 it's grim out there.",
    ),
    # The one grumble line that names the thing itself, so it is only for a thing that spreads.
    # "my back is killing me" / "me too" got "that one gets into everything", which is not a
    # thing anyone says about a back.
    "agree_weather": (
        "You're not the only one \u2014 that one gets into everything.",
        "I know the feeling. It's not just you.",
        "Half the street is with you on that one.",
    ),
    "agree_good": (
        "Good taste \u2014 I'm with you on that.",
        "Ha, you and me both.",
        "Now we're talking. Same here.",
        "That's the right side of it to be on.",
    ),
    # Agreeing with news that is neither good nor bad: the nod is all there is to say, and it
    # says it without the question at the end that comes after every stock line.
    "agree_plain": (
        "Then we're on the same page.",
        "You and me both, then.",
        "With you on that one.",
    ),
    # "me too" said into a death is the person saying they have had it too, and no cheerful
    # line can meet it: not "Glad to hear it", and not a swap of stories either.
    "agree_loss": (
        "You as well \u2014 I'm sorry. That is a heavy thing to carry.",
        "Then you know it too. I'm sorry it happened to you as well.",
    ),
    # The funny thing may have been theirs: "my cat fell in the bath" / "thats funny" is not a
    # joke the bot told, so nothing here takes credit for it or promises another one.
    "react_funny": (
        "Ha \u2014 good.",
        "Ha, that's a good one.",
        "Ha. Fair enough.",
    ),
    "react_tired": (
        "I know. That sort of tired doesn't lift with one early night.",
        "Yeah. Worn out is the honest word for it.",
        "It is. That's the kind of tired that builds up over days.",
    ),
    "not_great": (
        "That sounds like a rough one. What's happened?",
        "That's a flat way to put bad news. What is it?",
        "Sorry to hear it. Tell me what went wrong.",
    ),
    # Saying they will do the thing we suggested ("will give it a go", "ok i will try that").
    # The plain "ack" pool opened with "Fair enough.", which is a shrug at an offer, not a
    # send-off for someone about to try something.
    "try_ack": (
        "Nice one — tell me how it goes.",
        "Good. Let me know how you get on.",
        "Hope it goes well — shout if it does not.",
        "Sounds like a plan. Tell me how it turns out.",
    ),
    "no": (
        "Fair enough.",
        "No worries — say if you change your mind.",
        "That's fine too.",
    ),
    "idk": (
        "That's okay. Say what you do know and we'll work from there.",
        "Take your time \u2014 there's no wrong answer here.",
        "That's alright. Half of these things only come clear once you say them out loud.",
    ),
    # "i dont know" is an answer to what the bot just said, so the pool is chosen by that and not
    # by the line. "No rush. If you tell me the options, I'll help you pick" was said to a person
    # who had just been asked what was taking most of their day: there were no options on the
    # table, and being offered help to pick one reads as the bot not listening.
    "idk_asked": (
        "That's alright \u2014 it's hard to put your finger on it sometimes. Say the first bit "
        "that comes to mind.",
        "No worries. Whatever comes to mind first is fine, even if it is small.",
        "That's okay. I'm not going anywhere \u2014 say as much or as little as you like.",
    ),
    # After the bot has just heard something heavy, "i dont know" is the person saying they cannot
    # name it, and naming it is the last thing to ask of them.
    "idk_heavy": (
        "That's alright. You don't have to put it into words.",
        "That's okay. Some of it is just a fog at first \u2014 say whatever bit is easiest.",
        "No pressure at all. It can sit here as it is.",
    ),
    # A choice was on the table, so this is the one pool that talks about options: it offers to
    # weigh them rather than to "pick", which is not the person's to hand over.
    "idk_choice": (
        "No rush. Say the ones in front of you and I'll help you weigh them.",
        "That's okay. Tell me what each one gives you and I'll say what I would do.",
        "Take your time \u2014 put the two side by side and the answer usually shows itself.",
    ),
    "laugh": (
        "Ha! Glad you liked it.",
        "Ha — fair enough.",
        "Glad that landed.",
    ),
    # A laugh at something of theirs rather than at the bot's joke (that is "laugh" above, which
    # takes credit for it). Half of these ask what it was, because that is the next thing a friend
    # says, and half do not, because a question at the end of every reply is a script.
    "laughing": (
        "Ha — the good kind of crying.",
        "Ha, lovely. Nothing better than a thing that gets you like that.",
        "Ha! Go on then, what was it?",
        "That's a good laugh, that. Glad it got you.",
        "Ha — the sort of laugh that sorts out a whole week.",
        "Ha. What had you going?",
    ),
    "lol": (
        "Ha!",
        "Ha, quite.",
        "Glad I'm amusing.",
    ),
    "tired": (
        "That kind of tired needs an early night, not more coffee. Put your feet up when you can.",
        "Long one? Give yourself half an hour doing nothing before the next thing.",
        "Call it early tonight if you can. Whatever is left can keep until tomorrow - it is not "
        "going anywhere.",
        "Go to bed now rather than after one more thing, if the day allows it. That one more thing "
        "is what makes tomorrow tired too.",
    ),
    "stressed": (
        "That's a lot on your plate. Pick the one thing with a real deadline and park the rest for an hour.",
        "Write it all down, then do the smallest item on the list. Stress shrinks once it's on paper.",
        "Step away from the screen for ten minutes — stress makes everything look urgent.",
    ),
    # Any illness that is not a cold: a fever, a migraine, a bug, or a plain "i feel ill". Rest,
    # fluids and sleep are true of all of them, and nothing here names a cold remedy.
    "ill": (
        "That's rotten. Take today down a gear — food, water and an early night, and don't push "
        "through it.",
        "Sorry to hear it. Sleep is the thing that actually helps; the rest is just comfort.",
        "Ugh, that's miserable. Rest properly when you can, drink more than you think you need, "
        "and give it a few days before you start worrying about it.",
    ),
    # The same illness said with the part that is running: honey and lemon is honest for a throat,
    # a cough or a cold, and the first day of a cold really is the worst of it.
    "cold": (
        "Ugh, the first day of it is the worst. Rest, warm drinks and an early night, and it is "
        "usually milder than it feels right now.",
        "That's rotten. Take it easy today — honey and lemon, and don't push through it.",
        "Sorry to hear it. Sleep is the thing that actually helps; the rest is just comfort.",
    ),
    # The part of the body a line names picks the advice, because the cold's lines are wrong for
    # the others: "honey and lemon" is no help with a migraine, and "sleep is the thing that
    # actually helps" is no answer to a night of throwing up. `bot/understanding/body.py` reads
    # the part, so a new part is a new pool here and nothing else.
    "ill_head": (
        "Water, food, a painkiller and twenty minutes away from a screen sorts most headaches. A "
        "migraine wants a dark, quiet room and something for it early. The worst headache you "
        "have ever had, or one with a weak arm, a slurred word or a stiff neck, is a same-day "
        "job for a doctor.",
        "Take something for it now rather than pushing on, drink a glass of water and lie down "
        "somewhere dark for half an hour. One that keeps coming back for days, or that wakes you "
        "up, is worth a GP appointment.",
    ),
    "ill_throat": (
        "Honey and lemon in warm water is the thing that actually soothes it, and warm drinks "
        "beat cold ones. If it hurts to swallow or you have a fever with it, get it looked at - "
        "strep needs antibiotics and the rest does not.",
        "Sore throats are mostly viral, so rest, fluids and something for the pain; it usually "
        "eases in three or four days. Worth a doctor if it is one-sided and bad, or if your voice "
        "has gone for more than a couple of weeks.",
    ),
    "ill_temperature": (
        "Fluids and paracetamol, and light clothes rather than a pile of blankets - a fever is the "
        "body doing its job, and the number matters less than how you feel. Get seen the same day "
        "if it comes with a stiff neck, a rash that does not fade under a glass, trouble "
        "breathing, or if it lasts more than three days.",
        "Rest, plenty to drink and something to bring it down; take it easy until it has been "
        "gone for a day. A fever with a stiff neck, a new rash or breathlessness is not a wait-and-"
        "see: ring someone today.",
    ),
    "ill_stomach": (
        "Sip rather than gulp: water or an oral rehydration drink, little and often, and plain "
        "toast or rice when you can face it. Get help if you cannot keep any fluid down for a "
        "day, if there is blood, or if the pain settles in one spot and gets worse.",
        "Most stomach trouble is something you ate or a bug passing through: fluids first, plain "
        "food, no dairy or alcohol until it settles. Ring a doctor if you cannot keep water down "
        "or the pain moves to one side and gets sharper.",
    ),
    "ill_chest": (
        "A chest infection that brings breathlessness, a fever or a cough with mucky stuff in it is "
        "worth getting looked at rather than riding out - and sooner if you are older, pregnant or "
        "asthmatic.",
        "Rest and fluids help, but a chesty cough with a fever or any breathlessness needs a "
        "proper listen to your chest. Ring today if breathing gets harder or your lips look pale "
        "or blue.",
    ),
    "ill_teeth": (
        "Book the dentist today rather than waiting for it to settle - pain in a tooth or a gum "
        "usually means something that needs treating, and painkillers only cover it. Until then, "
        "take ibuprofen or paracetamol and keep the area clean; do not put an aspirin against the "
        "gum. Swelling in your face or jaw, a fever with it, or a tooth you cannot bite on is a "
        "same-day call.",
        "A dentist is the answer here, not a home remedy, because this does not heal on its "
        "own: salt water rinses and a painkiller only hold it until the appointment. Ring for an "
        "urgent slot, and be seen the same day if the swelling spreads down the jaw or closes "
        "your eye.",
    ),
    "ill_ear": (
        "Something for the pain and a warm flannel against it is what helps an earache while it "
        "settles, which most do in two or three days. Do not put anything in it, cotton buds "
        "included. Get it looked at if it is still there after three days, if there is discharge, "
        "or if your hearing has gone muffled.",
        "Earache is usually a passing infection: painkillers, warmth, and no poking about inside "
        "it. A child with a sore ear and a fever, or an adult whose hearing has dropped, wants a "
        "GP rather than another night of it.",
    ),
    "anxious": (
        "Worry like that is usually mostly 'what if'. Write down what's actually at stake and it gets smaller.",
        "Nerves before something big are normal. Slow breaths for a minute genuinely help.",
        "That sounds unsettling. Is there one thing you can check or ask about that would settle it?",
    ),
    # "worried about my mum" is worry about a person, and "worried about money" is worry about a
    # thing: neither is nerves before an event, so neither gets the breathing line. The pools are
    # kept apart from "anxious" because that pool presumes something big is coming up.
    "panic": (
        "That is a frightening thing to be in the middle of, and it does pass: a panic attack "
        "usually peaks and fades within about ten minutes. Breathe out for longer than you "
        "breathe in, and stay with me.",
        "Panic attacks feel like something terrible is about to happen even when nothing "
        "changes, and they ease off on their own. Slow the out-breath, put both feet on the "
        "floor, and tell me where you are.",
        "That sounds horrible, and it will pass. Sit down if you can, name five things you can "
        "see and hear, and keep breathing out slowly. I am here.",
    ),
    "worry_person": (
        "Worrying about someone you love is heavy. What's the part that weighs on you most?",
        "That's a lot to carry, and most of it is not yours to fix. Tell me what's been happening.",
        "It's hard watching someone you love struggle, and it's allowed to get to you.",
    ),
    "worry": (
        "That's a fair thing to have on your mind. What's the part that's weighing on you most?",
        "Worry with no end date on it is the tiring kind. Say the worst case out loud and it usually gets a bit smaller.",
        "Anyone would have that on their mind. What's the bit you can actually do something about?",
    ),
    "missing": (
        "Missing someone is the price of them mattering. It comes back on its own, and the gaps "
        "between the waves get longer, even when it does not feel like it yet.",
        "Of course you do. It goes in waves, and the waves get further apart.",
        "That sounds exhausting to carry around all day. Saying it out loud to someone who knew "
        "them helps some people.",
    ),
    "sad": (
        "That's a heavy feeling, and it's fair to have it. Be kind to yourself today.",
        "Sorry to hear that. A walk and someone to talk to usually help more than sitting with it.",
        "That sounds rough. If it's been hanging around for a while, talking to someone you trust is worth it.",
    ),
    # The tears themselves. "i want to cry" and "i feel like crying" named no mood word, so
    # they were read here and answered out of the sad pool - "A walk and someone to talk to
    # usually help" - which is advice for a low that has been sitting there, not what a person
    # on the verge of tears needs to hear. These say the thing is heavy and then ask, because a
    # person who says they want to cry has a reason and has not said it yet.
    "tears": (
        "That's a lot to be holding in. What's brought it on?",
        "It sounds like something has been building. Do you want to tell me what happened?",
        "Tears like that usually mean something needs saying. Has it been building up?",
        "I'm glad you said it rather than sitting with it on your own. What's behind it?",
        "I'm here. Take your time - what's going on?",
    ),
    # Tears at a thing built to move you are not a low, so the sad pool's "be kind to yourself
    # today" is the wrong reply to them - and passing the turn on was worse: "i cried at a film
    # last night" got "That sounds rough. If you want, I can help you think through what to do
    # next", which reads as though the film had been a problem to solve. What the person has
    # said is that something got to them, so the reply says that back and asks about the thing.
    # The lines are written for a film, a song or an advert, since that is what MOVED_BY names.
    "moved": (
        "Something in it got through, then. What was it about?",
        "Nothing wrong with a bit of that. What got you?",
        "That's what the good ones are for. What was it?",
        "A bit of that does you good. What was it?",
        "They are built to do that to people, so no need to be sheepish about it. Has it been "
        "like that a while?",
    ),
    # The line after a low that says the obvious things are not working: "nothing helps",
    # "ive tried everything". It used to come back as "I'm here if you want to dig into any of
    # that", which is the bot saying nothing at the moment the person says the advice is not
    # enough. Each line either asks what has been tried or says the length of it is the thing to
    # take somewhere, because those are the two things left to do about it.
    "nothing_helps": (
        "That's the part that wears people down - trying things and none of it shifting. Has "
        "anything helped even a little?",
        "Then it is not you being bad at it. When the small things have not moved it and it has "
        "been going on for weeks, say all of that to a GP rather than trying harder alone.",
        "Fair enough. Then let's not do more of the same - what does a hard day look like just "
        "now?",
        "I'm sorry. Nothing helping is its own kind of tiring. Is there anyone near you who "
        "knows it has been like this?",
        # Not every line asks: a person who says nothing helps is often asking what to do next
        # in the same breath, and a line that names the step leaves something to answer with.
        "That is a lot of trying with nothing to show for it. If it has been like this for a few "
        "weeks, take the whole list to a GP rather than trying harder on your own.",
    ),
    # The person is not naming a mood, they are saying the days are not working: it needs a
    # warm answer and a question that fits that, not "be kind to yourself today".
    "not_coping": (
        "That's a lot to be carrying on your own. What's the heaviest part of it just now?",
        "It sounds like you're running on empty. What would take some weight off this week?",
        "I'm glad you said it out loud. Is there anyone around you who knows it's like this?",
        "When it's like that, the days get very long. Has it been like this a while, or did "
        "something happen?",
        # Not every reply ends with a question: a person who says this twice should not be
        # asked something twice.
        "That sounds properly draining. Tell me what a hard day looks like just now - sleep, "
        "people, or getting through the afternoon.",
    ),
    # "i feel rubbish today" is a bad day, not a disclosure: it takes the same shape as the sad
    # pool but it must not be told "I'm glad you said it out loud", because a flat afternoon is
    # not a confession. "i feel awful" can also be a jab or a hangover.
    "bad_day": (
        "Rubbish day. What's been the worst of it?",
        "That's a flat one. What would make today a bit easier?",
        "Sorry - that's a rotten way to feel. Has it been like that long?",
        "That sounds like a heavy day. Want to tell me what's behind it?",
        # Enough of the pool ends without a question that a person who says this twice is not
        # asked something twice.
        "It is allowed to be a bad day. Nothing needs fixing this minute.",
    ),
    # The two hedges on the answer to "how are you", kept apart from `bad_day` because neither of
    # them says the day is bad: "cant complain" answered with "Rubbish day" is the bot hearing a
    # worse week than the person described, and "hanging in there" answered with "That's a rotten
    # way to feel" is the same thing one degree louder than the person said it.
    "hedged_ok": (
        "Steady is underrated. What's the day got in it?",
        "That'll do. Anything you're looking forward to?",
        "Fair enough — no news is decent news. What are you up to?",
        "Good enough is good enough. What's been happening?",
        "Can't ask for much more than that. What's the plan?",
        "Sound. What are you doing with the rest of it?",
    ),
    "hedged_low": (
        "Sorry to hear it. What's making it that way?",
        "What's dragging it down?",
        "That's not nothing. Want to say what's up?",
        "Sounds like a long one. What's going on?",
        "Ah, that's a flat sort of day. What's behind it?",
        "Not much fun, that. Tell me what's been going on.",
    ),
    "guilty": (
        "Guilt like that usually means you care, which is not the same as having got it wrong.",
        "That kind of guilt sits heavy. Say it out loud to one person you trust and it weighs less.",
        "Feeling guilty about it is not a verdict. Be as kind to yourself as you would be to a friend telling you the same thing.",
    ),
    "lonely": (
        "That's a hard one. A message to one person you like, even a short one, usually helps.",
        "Loneliness is rough. A weekly club or class is the quickest way to see the same faces again.",
    ),
    # Being taken for granted: the reply names the thing and gives one small move, rather than
    # sympathy alone ("That sounds really hard"). Nothing about cooling off - the quarrel pool is
    # for someone who is cross with a person in front of them, and this is not a quarrel yet.
    "unappreciated": (
        "That wears you down quietly. Name one thing you want noticed and say it plainly - people "
        "rarely do it on purpose.",
        "Being taken for granted is a slow drain. Pick the one job you would most like shared and "
        "ask for that, rather than the whole list at once.",
        "It is worth saying out loud: \"I did all of that, and I would like it noticed.\" Most "
        "people take what is done quietly as fine.",
    ),
    # Back in touch, said as the small thing it is: one person, one message, no apologising for
    # the gap. A big plan ("join a club, meet people") is the reason people stay away.
    "lonely_apart": (
        "That is easy to do and hard to undo, and it takes less than it feels like: one message "
        "to the person you miss most, saying you thought of them. No apology for the gap, just "
        "the message.",
        "Friendships go quiet more than they break. Pick the one person you would most like to "
        "hear from and send them something small today \u2014 a thing they would find funny, or a "
        "day you are free.",
        "Going quiet happens to most people, and the way back is one person at a time. Ask one of "
        "them to do one specific thing on one day, and let that be the whole of it.",
    ),
    # The turn after it: "what can i do about it" is asking for the step, and the answer has to be
    # about getting back in touch rather than about a day out or a hedge.
    "lonely_step": (
        "Start with one person and one small thing: a message today saying you thought of them, "
        "and a day named for a coffee. Nothing bigger than that to begin with.",
        "Ring the person you would most like to see, or text if a call is too much, and put a day "
        "on it. One name is enough to start with.",
        "Send one message to one person this week \u2014 not an apology for being quiet, just "
        "something that says you were thinking of them. The rest gets easier after that.",
    ),
    # A denied feeling is not a feeling: "im not tired" must not get the tired advice. What is
    # left to say is short and warm, because the person just ruled something out - and it asks,
    # because a denial is nearly always narrowing the cause ("i keep waking at 4am" / "im not
    # stressed"), so the useful turn is the one that asks what it is. The old pool congratulated
    # ("Good going, then.", "Noted, and good."), which read as not listening.
    "not_feeling": (
        "Right — so what's actually going on?",
        "Fair enough — what's going on, then?",
        "Noted — so what is it, then?",
        "Right, not that one. What's behind it?",
    ),
    # A mood that has gone on for weeks is not a bad day, and the pools above presume one: the
    # "anxious" pool even presumes a date ("nerves before something big"), which reads as not
    # having listened when the person said "all the time". The persistence is the thing worth
    # answering, and the answer is the one a friend gives: say it to a GP, it is treatable, and
    # do not wait for it to lift by itself.
    "ongoing": (
        "Weeks of it is not a bad day any more, and it is worth saying to a GP rather than "
        "waiting it out: write down how long it has been going on and what has changed since it "
        "started. Talking therapy is something you can refer yourself to in most areas, and it "
        "helps more than waiting does.",
        "When it is most days rather than one, the next step is a GP appointment — that is "
        "exactly what they are for, and this is treatable at this stage. Keep the sleep and the "
        "moving about, and tell one person the whole of it rather than the edited version.",
        "That long is worth a proper look rather than more willpower: book the GP, and take a "
        "week of notes with you so you do not have to remember it all in the room. Being flat "
        "or wound up for weeks is common, and it is the kind of thing that shifts with help.",
        "Weeks of feeling like that wears anyone down. Book the GP and say how long it has been "
        "going on — and until then, one small thing a day you would still do on a bad day beats "
        "a plan you cannot keep.",
    ),
    # The pool above is written for weeks, and only a line that says how long or how often has
    # earned it: "i feel sad all the time" has, but "i keep crying" only says it happens again.
    # Answering that with "weeks of it" asserts a duration the person never gave, which is the
    # kind of not-listening a fluent reply is worst at. What is worth answering either way is the
    # coming back itself, so that is what these lines say, with the same next step.
    "recurring": (
        "The fact that it keeps coming back is worth mentioning to a GP: say how often it "
        "happens and what sets it off, and take a few notes with you.",
        "It is the coming back that makes it worth a GP appointment rather than more willpower: "
        "note when it happens and what it is like, and take the page with you.",
        "A thing that keeps coming back is worth saying out loud to someone who can help: book "
        "the GP, say how often it happens, and do not wait for it to lift by itself.",
    ),
    # The pools above are advice, and advice given twice in a row is the one thing a friend would
    # not do: "i feel anxious all the time" then "i feel low all the time" got two GP sentences
    # back to back, and the third turn got the first sentence again word for word. The person
    # keeps talking about it, so the useful move is not to say the GP a third time but to do the
    # thing the advice asked for - the notes, or the one person to tell. These lines assume the
    # last turn already made the appointment the next step (the marker in `respond`), so they
    # never have to say it again and never claim anything the person has not said.
    "recurring_next": (
        "Then the notes are the part worth doing now, since they are what makes the appointment "
        "easy: what sets it off, and how often a bad stretch comes. A page is plenty.",
        "You know the next step already, so what would make it easier to say out loud in the "
        "room - the thing that sets it off, or what a bad day is like? Both are worth a line.",
        "Rather than say the same thing twice: is there one person you could tell the whole of "
        "it to this week? Saying it aloud once makes the appointment shorter.",
    ),
    "bored": (
        "Boredom is a good excuse for a walk with a podcast — twenty minutes usually resets it.",
        "Try something with your hands: a new recipe, a jigsaw, or tidying one drawer.",
        "Put on something short and funny, or text someone you haven't spoken to in a while.",
    ),
    "annoyed": (
        "Fair enough. Say it out loud to whoever caused it, once you've cooled off.",
        "Annoying. Walk it off for ten minutes before you reply to anyone.",
        "That would wind me up too. Get it out of your system, then decide what's worth doing.",
    ),
    # A line that is cross with the person *themselves* ("im so annoyed with myself", "im so
    # cross with myself") is not annoyance at somebody else, and the pool above answers a
    # quarrel they are not having: "say it out loud to whoever caused it" and "before you reply
    # to anyone" put a second person in a line about their own mistake. Nothing here tells them
    # how to feel, and nothing here asks a question - the thing to do with a person who has just
    # been hard on themselves is to say it is smaller than they think.
    "at_myself": (
        "Being cross with yourself is a heavier thing to carry than the mistake was. It is "
        "already over, and it is not a verdict on you.",
        "That is a hard way to talk to yourself over something small. Everyone does it, and it "
        "is over already.",
        "Annoying, and still smaller than it feels right now. Give it twenty minutes and it "
        "will have shrunk to what it is.",
        "Fair enough - and go gently. The thing that went wrong has already happened; being "
        "angry about it does not undo any of it.",
        "That is the sort of thing that stays with you all evening. It was a mistake, not a "
        "measure of you.",
    ),
    "venting": (
        "That would do my head in too. Has it been going on long?",
        "Annoying. Has it been like this long, or is today just a bad one?",
        "That would get to me as well. What have you tried so far?",
        "Fair enough, that would wear anyone down. What do you want to do about it?",
    ),
    # Asked for the news, the honest answer is that there is none, and then the conversation goes
    # back to the person: "got any good news" is small talk, not a request for a briefing.
    "no_news": (
        "Nothing to report here - what's new with you?",
        "None that I know of. What's been the best bit of your week?",
        "Not much on my side. Tell me yours and I'll count it as news.",
    ),
    # A good mood is not good news: "im so happy today" and "feeling great today" have nothing
    # that happened in them, and "That's great news!" told the person an event they had not
    # mentioned. Every line here answers the mood itself, and there are four of them so a chat
    # that stays cheerful does not run the pool out and fall back to saying the line back.
    "happy": (
        "Love that. Anything nice planned to go with it?",
        "Good! That's a nice thing to hear.",
        "That's a good feeling to carry into the rest of the day.",
        "That's a good place to be. Enjoy it.",
        "Nice one. Days like that are worth noticing.",
    ),
    # The news is real and the person has just said it did not land: "i feel nothing after good
    # news", "we got good news and i feel flat". The pool above congratulates ("Good! That's a
    # nice thing to hear.") a person who has said the opposite, and the pools for a low talk
    # about a walk or a bad day, which is not what this is. What a friend says is that the two
    # things are separate and that nothing is wrong with them for it.
    "good_news_not_landed": (
        "Good news that does not land is its own strange thing, and it is more common than "
        "people say. It usually catches up in a few days.",
        "The news and the feeling can be two different things, and that is allowed. It says "
        "nothing about you that the feeling has not arrived yet.",
        "That is a hard one to sit with: the good thing is real and you cannot feel it. Give it "
        "a few days before you read anything into it.",
    ),
    # The reply to a verdict on their own life (see `_their_own_call`): the person has said how
    # they read it, so the reply agrees and adds nothing to do. No advice (there is nothing
    # broken), no sympathy (nothing sad was said) and no question (they did not ask for one).
    "own_call": (
        "Then it's the right thing for you, and nobody else's view of it counts.",
        "Good \u2014 you're the one living it, so your read on it is the one that matters.",
        "Fair enough. It's worth saying out loud when a thing works, not only when it doesn't.",
        "Then leave it as it is. Not everything that looks odd from outside feels odd from inside.",
        "Right \u2014 and you'd know better than anyone, having done it.",
        "Good. Sounds like you got that one right the first time.",
        "Then there's nothing to fix, is there. Glad it worked out.",
    ),
    # Being pleased with yourself is not the same as having good news: there is nothing coming
    # up to ask about, and "make the most of it" reads as though the good thing were luck. The
    # reply a friend gives says the person is right to be pleased, and does not add a question.
    "proud": (
        "And so you should be. Whatever it took, you did that.",
        "That's worth being pleased about — don't talk yourself out of it.",
        "Good. Hold on to that one: you earned it.",
    ),
    # Relief, kept apart from the celebration above because nothing was won and nothing was
    # announced: the thing that was expected did not happen, or it is finally over. Every line
    # asks about the thing itself, so the answer is the same for the scan that came back clear
    # and for the illness that has ended.
    "relieved": (
        "That's a weight off. What were you braced for?",
        "Relief makes sense - that sounds like it had been sitting on you a while.",
        "Good. Does it feel finished now, or is there still a bit to come?",
    ),
    "rough_day": (
        "Those days are draining. Get the food and the rest in first, and leave the rest till tomorrow.",
        "Rough one. A shower, something warm to eat and an early night usually resets it.",
        "Been one of those? Park it for tonight — most of it will look smaller in the morning.",
    ),
    # A stretch of time that will not move (see A_STRETCH_THAT_DRAGS in chat.py). Nothing is broken
    # and nothing has happened, so there is no advice to give: the reply says the length of it back
    # and asks the one thing that would break it up, or names the one thing that helps a slow
    # stretch, which is something small of their own inside it.
    "long_stretch": (
        "It drags, doesn't it. What's making it feel that long?",
        "Long ones feel longer when there's nothing in them to look forward to. Is there anything coming up?",
        "Slow stretches are their own kind of tiring. What would break this one up?",
        "Then it's a case of getting through it, one thing at a time. What's the first thing you'd "
        "take off your plate?",
        # No "week" and no "month" in here: the pool answers a term, a month and school holidays as
        # well, and "A week like that is a grind" told a person with a month of it that they had a
        # week of it (azure-canoe, #8326).
        "A stretch like that is a grind, and it does end. Put something small in it that's just "
        "for you.",
    ),
    # A mind that will not hold still (see _scattered). The person has not said what is in the
    # list, so the honest reply is one small concrete thing to do about the feeling itself, not a
    # question that asks them to explain it and not "be kind to yourself".
    "scattered": (
        "That's a lot of open tabs. Write down the three things that actually have to happen "
        "today and let the rest wait.",
        "Yeah, days like that get away from you. Ten minutes away from the screen, then one thing "
        "start to finish.",
        "Nothing goes in while it's like that. Pick the smallest real job on the list and do only "
        "that one, then look again.",
        "Food and a walk clear more of it than another coffee does. Give it twenty minutes away "
        "from the screen, then look at the list again.",
    ),
    # Not understanding something is a feeling with nothing named yet: the person cannot say
    # what they are missing, or they would have said it. So the reply is short, asks for the one
    # bit, and promises to put it plainly - not "Thanks for telling me", which is what the bot
    # says to a message it heard nothing in, and not the sad pool, which offers a walk to
    # somebody who is trying to follow a letter from the council. Nothing here presumes the
    # thing is difficult or that they are upset.
    "confused": (
        "Tell me the bit that doesn't add up and I'll put it in plain words.",
        "Which part is clear and which part is foggy? Start where it stops making sense and "
        "we'll take it from there.",
        "Say it the way it is in your head, gaps and all, and I'll untangle what I can.",
    ),
    # The line after the question, when it does not say what the missing bit was: "i thought i
    # had it and now i dont". Nothing in it names a thing to answer, and the question has already
    # asked once - so this asks where it slipped, which is the one thing that moves it on.
    "lost_thread_more": (
        "Then start at the last bit that made sense \u2014 which part was clear?",
        "Fair enough. What was the last bit that made sense before it went foggy?",
        "Then it slipped somewhere. Where did it stop lining up?",
    ),
    # "I feel like ..." names a state with no single word for it, so no word in FEELINGS
    # catches it (see _feel_like). What the person compares themselves to decides the reply:
    # too little done, too much landed on them, no idea where they are going, or nobody on
    # their side. Each line answers what they said instead of naming the feeling back at them.
    "feel_like_not_enough": (
        "You are being measured against a version of the day that nobody has. However short it "
        "feels, the list of what you actually did is longer than that voice admits.",
        "That voice gets louder the more tired you are, and it's a rotten judge. Pick the one "
        "thing that matters most today and let the rest slide.",
        "Feeling like that usually means you care about doing it well, not that you're failing "
        "at it. Nobody gets it all done; the good ones just stop scoring themselves at night.",
        "There is always one more thing that could have been done - that is true of every "
        "single person. Stopping when the day is over is the whole trick of it.",
    ),
    "feel_like_good": (
        "That's a good thing to hear. Whatever you have been doing, keep it going another week "
        "before you draw conclusions.",
        "Good. The days you feel like yourself are the ones that show you what works, so notice "
        "what is different this week.",
        "Nice one. Don't let the next flat day talk you out of this.",
    ),
    "feel_like_load": (
        "The unfairness is what wears you down, not the jobs themselves. Say that part out "
        "loud to them instead of doing one more in silence.",
        "Being the one who notices everything is a job nobody thanks you for. Put the list on "
        "the fridge and give half of it away.",
        "You're not imagining it. If it all lands on you, name it once, plainly, and see what "
        "they say.",
        "That's a fast road to resentment, and it doesn't fix itself. Say what you're carrying "
        "once, plainly, and see if they pick any of it up.",
    ),
    "feel_like_adrift": (
        "Most people don't know either — they just have a better story for it. Work out the "
        "next month before the next ten years.",
        "Not knowing what you want yet isn't a fault in you. Pick something you'd like to be "
        "true in a year and take the smallest step towards it.",
        "Plans that stick usually start with one thing you're actually curious about. What's "
        "the part of your week you'd keep if you could?",
    ),
    "feel_like_left": (
        "Groups are bad at noticing who they've left out, and being among people makes it feel "
        "worse. Message the one person you'd genuinely want to see.",
        "That's a lonely spot, and it says more about the group than about you. One good "
        "friend beats a table of polite ones.",
    ),
    "feel_like": (
        "That's a miserable place to be, and 'it'll pass' is no help. What's the worst part of "
        "it right now?",
        "That's a real thing to feel, not a mood to snap out of. Say what's behind it and we'll "
        "look at it properly.",
        "I'd be feeling it too. Is it one thing dragging on, or a pile of them at once?",
    ),
    "against_me": (
        "Some weeks are like that, and it's rarely one big thing. Name the two worst bits and "
        "we'll work out which of them are actually yours to fix.",
        "When everything goes wrong at once it's usually a run of small things, not a curse. "
        "Start with the one costing you the most.",
        "That's a rough run. The quickest way out is one fixed thing, so pick the smallest of "
        "them today.",
    ),
    # Saying what you cannot do (see _stuck). Each line names the thing the person said, so it
    # could not be pasted onto a different message, and offers one small concrete thing or one
    # gentle question — never both, and never a diagnosis.
    "stuck_mornings": (
        "Mornings that heavy are worth listening to. How long has it been like that?",
        "That's a hard way to start a day. Getting up is the worst bit of it, most days.",
        "Then aim small: up, a shower, one thing out of the house, and nothing else on the list.",
    ),
    "stuck_sleep": (
        "Sleep that won't come makes everything else twice as hard. Same getting-up time every day is the bit that steadies it.",
        "Nights like that wear you down. If it's been weeks, say so to a GP — it's common and there's real help for it.",
        "Lying there trying harder doesn't work, sadly. Get up after twenty minutes, something dull and warm, then back to bed.",
    ),
    "stuck_eating": (
        "Appetite goes when things are heavy. Little and often beats one proper meal: toast, soup, a bit of fruit.",
        "Eating nothing makes the rest of it worse. Something small every few hours is enough for now.",
    ),
    # Days, not an appetite: this is the pool for a span of two days or more, where the answer is
    # a call today rather than a plate of toast.
    "stuck_eating_days": (
        "Days without eating is the point to say it out loud to a GP, or ring 111 today if you feel faint: keep water or squash going, and something small if it will go down.",
        "Going days without eating is worth a call today rather than a wait - 111 can tell you who to see, and a bit of water or juice in the meantime is not nothing.",
    ),
    "stuck_sleep_days": (
        "Nights without sleep add up on you: tell a GP this week, and ring 111 if you are dizzy or unsteady on your feet.",
        "A run of sleepless nights is worth saying to a GP rather than riding out - keep the getting-up time fixed while you wait.",
    ),
    "stuck_people": (
        "Staying in is the easy option and it makes the day smaller. One short thing out is easier than a plan.",
        "Seeing people takes more out of you when you're low. Start with one person you don't have to perform for.",
    ),
    "stuck_work": (
        "Work that's hard to face is worth naming. Is it one thing there, or the whole idea of going in?",
        "If it's most days, that's worth telling someone — your manager, or a GP. You don't have to explain it well to ask for help.",
    ),
    "stuck_focus": (
        "Concentration goes first when you're running on empty. Ten minutes on, five off beats an hour of staring at it.",
        "Nothing goes in when you're like that. Write the one thing down and do that, then stop.",
    ),
    "stuck_effort": (
        "\"Can't be bothered\" is usually tiredness in disguise. Pick the smallest thing that would make today lighter.",
        "Then don't force it. One small thing done beats a list you'll only feel bad about.",
    ),
    "stuck": (
        "That sounds like a lot to carry. What would make today a bit lighter?",
        "That's a heavy place to be. Is there one thing that would help, even a small one?",
    ),
    "here": (
        "Yep, I'm here — what's up?",
        "Here! What's on your mind?",
        "Still here. What can I help with?",
    ),
    # The line says a question is coming and names nothing yet ("can i ask you something",
    # "i need some advice"), so the one thing to do is make it easy to go on.
    "opening": (
        "Of course — go ahead, what's on your mind?",
        "Ask away, I'm listening. What's going on?",
        "Sure. Tell me what's happening and we'll work it out together.",
    ),
    # A judgement asked with nothing said yet to judge: "is that ok", "is that fine", "will that
    # help", "is that enough". The line is a yes/no question whose whole content is the judgement,
    # so the answer is in the thing it is about - and in a fresh chat nobody has said what that
    # is. The ack pool read the judgement word as the whole line and answered "Fair enough.",
    # which agrees with nothing and answers nothing; the composer's own subject-ask covers "is
    # that normal" and the rest went to a search hedge. What a friend does is ask what it is, and
    # the judgement word says which thing to ask for: a verdict wants the thing itself, a quantity
    # wants what it has to cover, and help wants the job.
    "judge_no_subject": (
        "Depends on the thing itself - tell me what it is and I'll say what I know.",
        "I'd need the thing in front of me to call it. What are you about to do?",
        "Happy to say, but I don't know what it is yet. What's the thing?",
        "That depends on what it is, and that bit hasn't been said. Give me the thing.",
    ),
    "enough_no_subject": (
        "Enough for what? Say what it has to cover and I'll tell you whether it does.",
        "Depends what it has to cover. What's the job?",
        "That one needs the thing it's for: what are you measuring it against?",
    ),
    "too_much_no_subject": (
        "Too much for what? Say the thing it has to fit into and I'll tell you.",
        "Depends what it has to go into. What's the job?",
        "That depends on the thing itself - what are you weighing it against?",
    ),
    "for_you_no_subject": (
        "Nothing to check on my side - no diary, no plans - so it's whatever suits you.",
        "Fine by me. There's nothing on this end to work around.",
        "Works for me. Pick the time that suits you and I'll be here.",
    ),
    "help_no_subject": (
        "Help with what? Say what you're stuck on and I'll take a look.",
        "Happy to help - what's the problem?",
        "What are you trying to sort out? That's the part I can be useful on.",
    ),
    "work_no_subject": (
        "Work for what? Say what you're trying to do and I'll tell you whether it does.",
        "Depends what it has to do. What's the job?",
        "Say what it's meant to do and I'll give you a straight answer.",
    ),
}
