"""The reader for a thing of the person's own that is on their side of the screen.

Two shapes, one reading. A line can ask the bot to open, read, look at, fill in, print or send
something of theirs, or it can simply hand the thing over ("here's a screenshot", "the link is
www..."). Either way nothing here can see it: nothing comes through an attachment, nothing can be
opened, and there are no hands to click with. On main the first shape got the search hedge, "a
quick search online will get you a solid answer", which sends somebody to go and google their own
inbox, and the second got "Got it. Is there anything you'd like a hand with?" as though the
picture had arrived.

The pool that answers is read from the object, never invented: a link is pasted, a photo or a
screen is described, an inbox is copied from, a form is read out, a click or a print is turned
into steps, and a bare "this" is the text on their screen. Nothing here is a fact about the world.

Both readings are narrow. The ask needs the bot's own act ("can you ...", or an imperative with
"for me") and a verb only an eye or a hand can do; the handed line needs a handing word and the
family named, or a bare link. Both stand down for what the bot can do ("can you write my cv for
me", "can you type up my notes"), for a line that already holds the text ("i pasted the text
below"), for what the bot keeps of the person ("can you see my chats with you"), for an address or
a number they are giving the bot, for a message or a text (this chat, not their mail), and for any
body part, symptom or doctor's word: a rash is not a file, and the pharmacist line is the answer.

This lives in its own file because `bot/compose/fallback.py` is at the world's size limit; the
fallback imports the two readers and keeps the choosing of the line.
"""
import re

SEEING_FAMILIES = {
    "link": ("link", "links", "url", "urls", "website", "websites", "site", "sites",
             "webpage", "web page", "webpages", "page", "pages", "article", "articles",
             "tab", "tabs", "browser"),
    "photo": ("screen", "screens", "camera", "webcam", "photo", "photos", "picture",
             "pictures", "image", "images", "screenshot", "screenshots", "video", "videos",
             "clip", "clips", "notification", "notifications"),
    "voice": ("voice note", "voice notes", "voice memo", "voice memos", "voice message",
              "voice messages", "voice recording", "voice recordings", "voice clip",
              "recording", "recordings", "audio", "audio clip", "audio file", "audio message",
              "sound file", "sound clip", "memo", "memos", "voicemail", "voicemails",
              "podcast", "podcasts"),
    "inbox": ("email", "emails", "e-mail", "e-mails", "mail", "inbox", "message", "messages",
             "text", "texts", "voicemail", "voicemails", "letter", "letters", "post",
             "folder", "folders", "spam"),
    "form": ("form", "forms", "paperwork", "questionnaire", "tax return", "tax returns",
             "return form"),
    "file": ("file", "files", "document", "documents", "doc", "docs", "pdf", "pdfs",
             "spreadsheet", "spreadsheets", "essay", "essays", "cv",
             "homework", "statement", "invoice", "receipt", "contract", "attachment",
             "attachments"),
}
# What only a hand can do on the person's side: none of it happens from the chat. Writing,
# typing, copying out, suggesting and explaining are what the bot does do, so they are not here
# ("can you type out a message for my landlord" wants the words, not a click).
A_HAND_DOES_IT = re.compile(
    r"\b(?:click|clicking|tap|tapping|press|pressing|scroll|scrolling|print|printing|"
    r"scan|scanning|download|downloading|upload|uploading|"
    r"send|sending|forward|forwarding|save|saving|delete|deleting|install|installing|"
    r"access|accessing|submit|submitting|log\s+in|sign\s+in|screenshot|screenshotting|"
    r"take\s+(?:a\s+)?(?:photo|picture|screenshot)|type\s+(?:in|into)|"
    # "sign" only where it is the act of signing the thing itself ("can you sign this for me"):
    # a bare "sign" is also a sign in a shop window, which is not a hand doing something for them.
    r"sign\s+(?:it|this|that|these|those|them|for\s+(?:me|us))|"
    r"copy\s+(?:the|it|that|this|out))")
# What only an eye can do on the person's side, and only once the thing is handed over as text.
AN_EYE_READS_IT = re.compile(
    r"\b(?:open|opening|read|reading|see|seeing|view|viewing|watch|watching|find|finding|"
    r"look\s+(?:at|through|over|in|into)|"
    r"check|checking|fill(?:ing)?\s+(?:in|out)|fill|filling|complete|completing|translate|translating|"
    r"read\s+(?:out|it\s+out)?\s+what\s+(?:it|that|this)\s+says|what\s+(?:my|the)\s+\S+\s+says|"
    r"update|updating|go\s+through|get\s+into)")
# What only an ear can do on the person's side. A voice note, a recording, a podcast: the sound
# never arrives here, and "can you listen to this" used to get "that's beyond what I know well"
# with a search suggested, or a shrug.
AN_EAR_HEARS_IT = re.compile(
    r"\b(?:listen|listening|hear|hearing|play|playing|playback|transcribe|transcribing|"
    r"decipher|make\s+out)")
NO_HAND_VERB = re.compile(A_HAND_DOES_IT.pattern + "|" + AN_EYE_READS_IT.pattern + "|"
                          + AN_EAR_HEARS_IT.pattern)
# The same eye, for a bare "this/that/it" with no object named: the thing is handed over as text
# and read here. "Find" is not here - "can you find it" is a missing thing, not a page to read.
READS_HANDED_TEXT = re.compile(
    r"\b(?:open|opening|read|reading|see|seeing|view|viewing|watch|watching|"
    r"look\s+(?:at|through|over)|translate|translating|what\s+(?:it|this|that)\s+says)\b")
# "Can you", "could you", "print this for me": the ask has to be the bot's own act, not a
# request for advice about the thing.
ASKS_THE_BOT_TO_ACT = re.compile(
    r"\b(?:can|could|would|will|are|do)\s+(?:you|u)\s+(?:please\s+|just\s+|kindly\s+|also\s+)*"
    # "help me fill in this form" is the same ask as "can you fill in this form": the person wants
    # the job done, not the menu that does it, and it reached the search hedge.
    r"|\bhelp\s+(?:me|us)\b\s+(?:\S+\s+){0,3}"
    r"\S"
    # The ask said as an offer of the thing to be looked at: "have a listen to this voice memo",
    # "have a look at this photo". It is the same act asked the other way round, and the hedge it
    # used to reach ("That's beyond what I know well") assumed the bot could hear the memo.
    r"|\b(?:have\s+a\s+(?:listen|look|read|quick\s+look)|take\s+a\s+(?:listen|look|read))\b"
    r"|^\s*(?:please\s+|just\s+)?(?:open|print|read|see|check|look\s+at|fill\s+in|fill\s+out|"
    r"scan|download|upload|click|tap|press|scroll)\b[^?]*\b(?:for\s+me|please)\b")
# A line that holds the text already ("can you check this sounds right: Hi Sarah, just checking")
# has given the bot what it needs; the rewrite and reading modules answer those.
HOLDS_THE_TEXT = re.compile(r":\s*\S+(?:\s+\S+){5,}")
# What the person can do instead, one pool per family, because the way to hand it over differs.
CANNOT_SEE = {
    "link": (
        "I can't open links, sorry - nothing on my side can browse. Tell me what it says, or what "
        "you want from it, and I'll help you with that.",
        "No link opening from here, sorry. Paste the bit that matters into the chat and I'll work "
        "through it with you.",
        "I can't follow a link, sorry. Copy the words you need and send them here - I'll take it "
        "from there.",
    ),
    "photo": (
        "I can't see your screen or your photos, sorry - I only get the words you type. Describe "
        "what's there, or type out the part that matters, and I'll help.",
        "Nothing on my side can look at a photo or a screen, sorry. Tell me what it shows and what "
        "you need to know about it.",
        "I can't see pictures from here - no camera, no screen. Say what is in it and I'll tell "
        "you what I make of it.",
    ),
    "inbox": (
        "I can't get into your inbox or your messages, sorry - they're on your side. Copy the "
        "words that matter in here and I'll help you answer them.",
        "Your email is not something I can see. Paste the part you need to deal with and I'll "
        "draft the reply.",
        "I can't read your mail from here. Send me the gist of it and I'll help you work out what "
        "to say back.",
    ),
    "form": (
        "I can't fill in a form I can't see, sorry. Tell me what it asks, one line at a time, and "
        "I'll give you an answer for each.",
        "I can't write on a form from here - no hands on my side. Read me the questions and I'll "
        "give you the words; you put them in.",
    ),
    "file": (
        "I can't open files, sorry - nothing here can see or send them. Paste the text in and "
        "I'll go through it with you.",
        "Nothing here can open a file, sorry. Type in the part you want help with and I'll take "
        "it from there.",
        "I can't see a file from here, sorry - I only get what you type. Paste a bit of it in "
        "and we'll work on that.",
    ),
    "text": (
        "I can't see the page you're looking at, sorry - I only get what you type. Paste the bit "
        "you want help with and I'll go through it with you.",
        "Nothing on my side can see the text on your screen, sorry. Type in the part that matters "
        "and I'll take it from there.",
        "I only see the words you send me, sorry - not what is on your screen. Paste it in here "
        "and I'll work on that.",
    ),
    "voice": (
        "I can't hear a voice note or a recording, sorry - no ears on this end. Type the bit that "
        "matters in here and I'll work from that.",
        "Nothing on my side can play or listen to audio. Write down what was said, even roughly, "
        "and I'll take it from there.",
        "I can't listen to a recording from here - I only get what you type. Put the words in the "
        "chat and I'll help with them.",
    ),
    # The same missing ear with no recording named at all: "can you hear that noise", "can you
    # hear that bird", "can you play that song again". A voice-word pool would tell somebody
    # holding nothing to transcribe it, so the line says only what is true - nothing here hears
    # or plays anything - and asks for the sound in words.
    "sound": (
        "I can't hear anything from here, sorry - no ears and no speaker on this side. Tell me "
        "what it was like and where it came from - a knock, a bang, a hum, water, the pipes - "
        "and I'll say what usually makes that one.",
        "Nothing on my side can listen or play, sorry. Say what you noticed: how loud, how often, "
        "which room. Most house sounds have two or three usual causes and the answer narrows it.",
        "There is no microphone or speaker on this end, so I can't hear it. Describe it - a thud, "
        "a rattle, a drip, a hum - and where it comes from, and we can work it out from that.",
    ),
    # A noise has a place, and the place is the part that is actually known: what goes on in a
    # loft is not what goes on in the pipes, and neither is what happens in the garden. The pool
    # leads with the two or three usual causes, then says plainly that nothing here can hear it,
    # then asks the one thing that settles it. Without the place there is only the limit, which is
    # what "there is a strange noise coming from the loft" used to get.
    "noise_roof": (
        "Overhead is usually one of three: an animal in the loft - birds, squirrels, sometimes a "
        "rat, and it scratches and moves fast; the cold water tank filling, which is a slow "
        "gurgle; or the pipes under it, which bang once when the heating starts. I can't hear "
        "anything from here - which of those is it closest to?",
        "A noise above the ceiling most often comes from the loft: an animal moving about, the "
        "tank refilling, or pipes expanding when the heating comes on. I have no ears on this "
        "side of the chat, so the sound itself is yours to place - scratchy and quick, a gurgle, "
        "or a single bang?",
    ),
    "noise_pipes": (
        "Banging or knocking from the pipes is usually air, or water hammer when a tap shuts "
        "quickly; a hum that comes with the heating is often the pump. None of that needs a "
        "plumber today - bleeding the radiators is the first thing to try. I can't hear it from "
        "here: does it happen when the heating starts, or when a tap is turned off?",
        "A rattle or a knock in the pipework is usually air in the system or a loose clip, and a "
        "hum that follows the heating is the pump. There is nothing on this end that can listen, "
        "so tell me when it starts - with the heating, or after a tap?",
    ),
    "noise_outside": (
        "From outside the house it is usually roadworks, a boiler flue or a fan next door, or an "
        "animal - and if it keeps you awake, the council's noise team wants the times and days "
        "written down, which is what gets anything done. I can't hear any of it from here: which "
        "side of the house is it on?",
        "Sound that comes in from outside is most often work on the road, a neighbour's extractor "
        "or boiler, or an animal - and a log of times and days is what the council acts on. "
        "Nothing here can listen, so where in the house do you hear it clearest?",
    ),
    # The one noise with an answer worth giving before asking anything: a chirp at regular
    # intervals is a smoke alarm's battery, and a CO alarm is not a battery. The pool says both,
    # because getting those two the wrong way round is the only way this line can do harm.
    "beep": (
        "A chirp every minute or so is nearly always a smoke alarm asking for its battery - twist "
        "it off its base and change it today rather than waiting. A carbon monoxide alarm is a "
        "different, louder note and means out of the house and onto 0800 111 999.",
        "One beep at regular intervals is usually a smoke alarm's battery. If it is the carbon "
        "monoxide alarm instead - it says CO on it, and the sound is louder and harder to "
        "ignore - get everyone out and ring the gas emergency line on 0800 111 999.",
    ),
    "hands": (
        "I can't click, print or type on your device, sorry - I'm only words in the chat. Tell me "
        "what's on the screen and what you want to do and I'll walk you through the steps.",
        "No hands on my side, sorry: nothing here can press, print or send anything. Say what you "
        "are trying to do and I'll give you the clicks in order.",
    ),
    # No nose either, and a smell is the one the answer matters for: gas and burning are a job
    # for a phone call, not a description. The pool says which smells are urgent and what the
    # slow ones usually are, because "describe it and I'll help" on its own is the search hedge
    # with the person's own nose doing the work.
    # No eyes either, and a light in the room is the third of these: it is in front of them and
    # not here, so the useful half is what a light in that state usually means. A flashing light
    # on a machine is a code, a steady red on a boiler is a lockout, and a router's red is the
    # internet - all three are settled by the maker's own manual or status page, which is the one
    # place the rest lives.
    "light": (
        "I can't see it from here, sorry - only the words you type reach me. A light that blinks "
        "on a machine is nearly always a code: count the flashes and note what it does before "
        "repeating, and the manual or the maker's app names that pattern. On a router, red "
        "usually means no internet at all, so check the provider's status page first.",
        "Nothing on this end has eyes, sorry. Tell me what the light is on - a boiler, a router, "
        "a charger, the dashboard - and whether it flashes or stays on. A steady red on a boiler "
        "is usually a lockout and the manual's relight steps come first; a flashing pattern is a "
        "code the manual lists.",
        "I can't see the room you're in. If a bulb went with a bang or a pop it is the bulb - "
        "switch it off at the wall before you change it, and if a new one does the same, the "
        "fitting or the driver is the fault. A light on a smoke alarm that blinks about once a "
        "minute is its battery, and a street light flickering or out is the council's to fix.",
    ),
    # The lights going out is not a thing to describe: it has an answer, and the answer is the
    # consumer unit. Kept apart from the pool above so nobody with a router in front of them is
    # told to go and look at the breakers.
    "lights_out": (
        "If several lights went at once, it is a tripped breaker or RCD in the consumer unit "
        "rather than the bulbs: switch the one that is down back on, and if it trips again leave "
        "it off and get an electrician rather than holding it up.",
        "Several lights going together is a circuit, not a bulb - look in the consumer unit for "
        "the switch that is down and reset it once. If it goes again straight away, leave it off "
        "and ring an electrician; that is a fault they need to find.",
    ),
    # No power in the house or the street is not the same fault as several lights going: in a
    # street-wide cut the breakers are already up, and the one who knows is the network operator.
    # "is there a power cut in my area" is the archetype of live local information, so the line
    # names the operator's own outage map and the number, and leaves the consumer unit for the
    # case where the neighbours are lit.
    "power_cut": (
        "If the whole street is dark it is the network operator's cut, not a fault in your house: "
        "check a neighbour's lights, then your operator's live outage map - 105 in the UK - which "
        "says what is off and when it is due back. Leave the breakers alone while it is theirs.",
        "Nothing on this end can see the outage, sorry. Neighbours dark too means the network: "
        "ring 105 or open the operator's outage page and it will say how long. If you are the "
        "only one without power, then it is yours - start at the consumer unit.",
    ),
    "smell": (
        "I can't smell anything from here, sorry - only the words you type reach me. If it "
        "could be gas, get everyone out and ring the gas emergency line on 0800 111 999 before "
        "anything else; burning is usually the oven, a plug or a pan.",
        "Nothing on this end has a nose, sorry. Tell me what it is like - gas, burning, damp, "
        "drains, or something dead under the floor - and I'll say what that one usually is and "
        "who deals with it.",
        "I can't smell it from here. Gas gets everybody out of the house first and then the gas "
        "emergency line on 0800 111 999; anything else, say where it is strongest and whether "
        "it is damp, drains or burning, and I'll tell you if it is a landlord job.",
    ),
}

# A contact detail is words the bot can read and nothing it can act on: it cannot send, dial or
# save, and the receipt ("Got it. Is there anything you'd like a hand with?") reads as though the
# address had been filed somewhere. What it can do is help with the words, so the line says that
# and asks what the address is for.
CANNOT_SEE["contact"] = (
    "Nothing here can send, dial or save a contact, so an address or a number stays in this chat "
    "with me. Tell me what it is for - a message, a form, a complaint - and I'll write that out "
    "for you.",
    "I can read it, but I can't email, ring or store it: nothing leaves this chat. Say who it is "
    "for and what you want said, and I'll put the words together.",
    "No sending or calling from this end, sorry. If you say what you want done with that address "
    "or number, I'll help with the wording and you send it yourself.",
)

# The two pools the room reader can hand back, named so it reads like the sound one.
CANNOT_SMELL = CANNOT_SEE["smell"]
CANNOT_HEAR_A_BEEP = CANNOT_SEE["beep"]


# "my chats with you", "our conversation", "can you remember my name": the bot talking about
# what it keeps of the person, which is its own line and not this one.
ABOUT_WHAT_IT_KEEPS = re.compile(
    r"\b(?:with|to)\s+you\b|\bour\s+(?:chat|chats|talk|talks|conversation|conversations)\b"
    r"|\bremember\s+(?:me|my|what|anything|things)\b")


A_URL = re.compile(r"\b(?:https?://|www\.)\S+")
# A message or a text handed over is this chat, or the phone in their hand: only mail is on the
# far side of a screen the bot can name ("i sent you a message earlier" is not "I can't read your
# mail from here").
HANDED_FAMILIES = {
    "inbox": ("email", "emails", "mail", "inbox", "letter", "letters", "attachment", "attachments"),
}
HANDED_OVER = re.compile(
    r"\b(?:here'?s|here\s+(?:is|are)|attached|attaching|see\s+attached|"
    r"sent\s+you|sending\s+you|shall\s+send\s+you|screenshot\s+below|"
    r"photo\s+below|picture\s+below|"
    r"recorded\b[^.]{0,30}\bfor\s+you|"
    r"this\s+is\s+(?:a|my)\s+(?:video|recording|voice\s+note|voice\s+memo|photo|picture|"
    r"screenshot)\b)\b")


# A recording they made and are offering: "heres a voice note", "i recorded it, want to hear it",
# "its about 2 mins, can you listen", "have a listen to this". Nothing here plays it, and with no
# "this" in the line the reader above never saw it: "its about 2 mins, can you listen" got the
# search hedge. The offer is the tell, with a recording word or the length of the thing.
A_RECORDING_WORD = re.compile(
    r"\b(?:record(?:ed|ing|s)?|voice\s+note|voice\s+memo|voice\s+message|audio|podcast|memo|"
    r"taped|tape)\b", re.I)
A_LISTEN_OFFER = re.compile(
    r"\b(?:want\s+(?:me\s+)?to\s+(?:hear|listen)|(?:have|give)\s+(?:it|this|that)\s+a\s+listen|"
    r"(?:have|give)\s+a\s+listen|can\s+you\s+(?:listen|hear)\s+(?:to\s+)?(?:it|this|that)|"
    r"listen\s+to\s+it|hear\s+it|listen\s+in)\b", re.I)
A_A_LENGTH = re.compile(
    r"\b(?:about|roughly|around|like)\s+\d+\s*(?:secs?|seconds?|mins?|minutes?)\b|"
    r"\b\d+\s*(?:secs?|seconds?|mins?|minutes?)\s+(?:long|of\s+it)\b", re.I)


def a_recording_they_offer(clean):
    """The honest line for a recording the person is offering the bot, or None."""
    line = (clean or "").strip()
    if len(line.split()) > 25:
        return None
    length = A_A_LENGTH.search(line)
    if not A_LISTEN_OFFER.search(line) and not length:
        return None
    if A_RECORDING_WORD.search(line) or length:
        return CANNOT_SEE["voice"]
    return None


# An address or a number handed over: "heres my email address: sam@example.com", "my number is
# 07700 900123". `handed_you_something` steps aside for these on purpose (the bot can read them),
# and nothing else answered them, so the person got a receipt. A question about an address or a
# number is a lookup and is left alone.
A_AN_EMAIL_ADDRESS = re.compile(r"\S+@\S+\.\w+")
A_A_PHONE_NUMBER = re.compile(r"(?:\+44|\(?0)\d[\d\s\-]{8,}\d")
A_A_CONTACT_WORD = re.compile(
    r"\b(?:email|e-mail|phone|mobile|number|contact\s+details?|postcode|address)\b", re.I)
A_A_HANDOVER = re.compile(
    r"^\s*(?:o+k?|okay|so|right|anyway|and|also)?[ ,]*(?:here'?s|heres|here\s+(?:is|are)|"
    r"this\s+is|that'?s|my|our)\b"
    r"|\bmy\s+(?:email|e-?mail|phone|mobile|number|contact\s+details?|postcode|address)\s+is\b",
    re.I)
A_ASKING_FOR_IT = re.compile(
    r"^\s*(?:what|whats|what's|how|where|which|who|when|why|is|are|do|does|did|can|could|"
    r"should|would|any)\b|\?\s*$", re.I)


def a_contact_they_handed_over(clean):
    """The honest line for an address or a number handed over, or None."""
    line = (clean or "").strip()
    if len(line.split()) > 25:
        return None
    held = (A_AN_EMAIL_ADDRESS.search(line) or A_A_PHONE_NUMBER.search(line)
            or A_A_CONTACT_WORD.search(line))
    if not held:
        return None
    if not A_A_HANDOVER.search(line):
        return None
    if A_ASKING_FOR_IT.search(line) and not (A_AN_EMAIL_ADDRESS.search(line)
                                             or A_A_PHONE_NUMBER.search(line)):
        return None
    return CANNOT_SEE["contact"]


def handed_you_something(clean):
    """The honest line for a thing the person believes they have just handed over, or None.

    "here's a screenshot", "i sent you a photo", "here is the link", "the link is www.example.com/
    offer" are not asks at all, so nothing in the bot answers them and the person gets "Got it. Is
    there anything you would like a hand with?" - which reads as though the picture had arrived.
    Nothing comes through an attachment and nothing can be opened, so the line has to say that and
    ask for the words instead. A line that does hold the text ("i pasted the text below") is left
    alone: that one did come through.
    """
    if HOLDS_THE_TEXT.search(clean):
        return None
    if len(clean.split()) > 25:
        return None
    if re.search(r"\S+@\S+\.\w+|\baddress\b|\bnumber\b", clean):
        # "here's my email address", "my email is sam@example.com", "here's my number" are the
        # person handing over something the bot can keep, not a thing it is being asked to look
        # at, and the honest "I can't see your inbox" is a lie about the line.
        return None
    if A_URL.search(clean) and not re.search(r"\bhow\s+(?:do|can|should)\s+i\b", clean):
        # A link in the line is a page the bot cannot open, whether it was handed over or asked
        # about ("is this link safe www..."), so this is read before the ask guard. "how do i
        # shorten a long url" is a how-to and is left to whatever else answers it.
        return CANNOT_SEE["link"]
    if not HANDED_OVER.search(clean):
        return None
    for family in ("voice", "photo", "link", "file", "inbox", "form"):
        things = HANDED_FAMILIES.get(family) or SEEING_FAMILIES[family]
        if re.search(r"\b(?:" + "|".join(re.escape(thing) for thing in things) + r")\b", clean):
            # The family they name is the thing on their own side: a screenshot or a photo is
            # looked at, a link is opened, a file or a letter is read, a form is written on.
            return CANNOT_SEE[family]
    if ASKS_THE_BOT_TO_ACT.search(clean):
        # "heres a link to a recipe, can you make it" is decided by the thing handed over, above;
        # what is left here is an ask with no thing named, which is somebody else's reader.
        return None
    if re.search(r"\bsee\s+attached\b|\battached\s+(?:is|are)\b", clean):
        return CANNOT_SEE["file"]
    return None


# Writing a message somebody will send is the bot's own work, not an eye or a hand: "can you
# send an email for me", "can you send a text to my landlord", "can you send this message on my
# behalf". The mail word is in the inbox family, so the reader took these for an inbox it cannot
# open and answered "I can't get into your inbox - paste the words that matter in here": no help
# to somebody who has not written them yet. The fallback's drafting invite is the answer to this
# shape ("give me who it's for and what you want them to do"), so the reader stands down and
# lets it through.
WRITES_A_MESSAGE = re.compile(
    r"\b(?:can|could|would|will)\s+(?:you|u)\s+(?:please\s+|just\s+|also\s+)*"
    r"(?:\w+\s+){0,3}(?:send|write|draft|type\s+out|put|reply|forward|answer)\b")
MESSAGE_WORD = re.compile(
    r"\b(?:email|emails|e-mail|e-mails|text|texts|message|messages|note|notes|letter|letters|"
    r"reply|replies|memo)\b")
TO_A_PERSON = re.compile(
    r"\bfor\s+(?:me|us)\b|\bon\s+my\s+behalf\b"
    r"|\bto\s+(?:my|our|the|his|her|their|a)\s+[a-z]+|\b(?:someone|somebody|anyone)\b")
# Forwarding is never drafting: the message is already written, so the words are not what the
# person is short of. "can you forward the letter to my solicitor" is a hand, and the honest
# answer for it is the reader's own, not an offer to write something new.
A_FORWARD = re.compile(r"\bforward(?:ing|ed)?\b")
# A message named as theirs ("my email", "the letter") already exists, the same way.
THEIR_OWN_MESSAGE = re.compile(
    r"\b(?:my|our|the|his|her|their)\s+(?:email|e-mail|text|message|note|letter|reply|memo)s?\b")


# Who it is for, when the line says: "to my landlord", "for my boss", "to the council". "For me"
# and "on my behalf" are not this - nobody is named, so the invite still has to ask.
A_NAMED_ADDRESSEE = re.compile(
    r"\b(?:to|for|with)\s+(?:my|our|his|her|their|the|a)\s+[a-z]+"
    r"|\b(?:to|for)\s+(?:someone|somebody)\b")


def names_the_addressee(clean):
    """True when the line already says who the message is for."""
    return bool(A_NAMED_ADDRESSEE.search(clean))


def writes_the_message(clean):
    """True when the ask is for the words of a message to somebody: write it, not send it."""
    if not MESSAGE_WORD.search(clean) or not WRITES_A_MESSAGE.search(clean):
        return False
    if A_FORWARD.search(clean) or THEIR_OWN_MESSAGE.search(clean):
        return False
    return bool(TO_A_PERSON.search(clean))


# "back" is a body and also "play that audio back", "call back", "get back to". Only the body
# sense is a reason to stand down, so the word is read as a body part only when it is used as one.
BACK_AS_A_BODY = re.compile(
    r"\b(?:my|your|his|her|our|their|the|lower|upper|sore|bad)\s+back\b|"
    r"\bback\s+(?:pain|ache|aches|hurts?|spasms?|injur\w*|problem|again)\b")


def _a_body_or_a_doctor(clean):
    """True when the line names a body, a symptom or a doctor - a rash is not a file.

    "can you look at this rash" and "can you look at this thing on my leg" were answered "I can't
    open files, sorry", which takes the health card off the table; the pharmacist line is the one
    that helps. The word tables are the fallback's own, read here so the two cannot drift.
    """
    from .fallback import BODY_PARTS, HEALTH_WORDS, SYMPTOM_WORDS
    plain = set(re.findall(r"[a-z']+", clean))
    if "back" in plain and not BACK_AS_A_BODY.search(clean):
        plain.discard("back")
    return bool(plain & BODY_PARTS or plain & SYMPTOM_WORDS or plain & HEALTH_WORDS)


def _a_voice_is_named(clean):
    """A recording, a memo, a podcast: something with words in it to be written down.

    A bare "can you hear that" names no recording, so it is owed the smaller line - nothing here
    hears it - rather than "type the bit that matters", which assumes a recording that the person
    is not holding. #7519's first head sent "can you hear that noise" to the voice-note pool.
    """
    return bool(re.search(r"\b(?:" + "|".join(
        re.escape(thing) for thing in SEEING_FAMILIES["voice"]) + r")\b", clean))


# A thing that is played is not a thing to be heard: "can you play this level with me" is an
# invitation, and the sound pool answered it "I can't hear anything from here - no ears and no
# speaker on this side". The words people use for a turn of it are not `game` (found by
# @neat-pineapple on #7519), so the list is the nouns of playing and the `with me` that asks for
# company; `can you play that song again` and `can you play this record` are still sounds.
GAME_TO_PLAY = re.compile(
    r"\b(?:game|games|chess|match|quiz|level|levels|round|rounds|move|moves|puzzle|puzzles|"
    r"cards|darts|board|boards|innings|hole|holes|shot|shots|score|scores|character|"
    r"save|savegame)\b"
    r"|\bplay\s+[^.!?]{0,30}\bwith\s+me\b", re.I)


def _a_game_to_play(clean):
    """The line asks the bot to join in a game, or names a turn of one, so nothing is to be heard."""
    return bool(GAME_TO_PLAY.search(clean))


def cannot_see_your_thing(clean):
    """The honest line for a thing of theirs the bot cannot open, or None."""
    if not ASKS_THE_BOT_TO_ACT.search(clean) or not NO_HAND_VERB.search(clean):
        return None
    if HOLDS_THE_TEXT.search(clean) or ABOUT_WHAT_IT_KEEPS.search(clean):
        return None
    if len(clean.split()) > 25:
        return None
    if _a_body_or_a_doctor(clean):
        return None
    if writes_the_message(clean):
        return None
    # The longest name wins, not the first family in the table: "can you listen to this audio
    # clip" names a `clip` and an `audio clip`, and the picture pool in front of the voice pool
    # answered it "I can't see pictures from here - no camera, no screen", which is a refusal of
    # the wrong sense. A longer name is the more particular one, so it is the one being asked for.
    matched = []
    for name, things in SEEING_FAMILIES.items():
        hit = re.search(r"\b(?:" + "|".join(re.escape(thing) for thing in things) + r")\b", clean)
        if hit:
            matched.append((len(hit.group(0)), name))
    if matched:
        return CANNOT_SEE[max(matched)[1]]
    if re.search(r"\bfill(?:ing)?\b", clean) and re.search(r"\b(?:this|that)\b", clean):
        return CANNOT_SEE["form"]
    if A_HAND_DOES_IT.search(clean):
        return CANNOT_SEE["hands"]
    if re.search(r"\b(?:this|that|these|those)\b", clean) and AN_EAR_HEARS_IT.search(clean) \
            and not _a_game_to_play(clean):
        if _a_voice_is_named(clean):
            return CANNOT_SEE["voice"]
        return CANNOT_SEE["sound"]
    if re.search(r"\b(?:this|that|these|those)\b", clean) and AN_EYE_READS_IT.search(clean):
        return CANNOT_SEE["text"]
    if re.search(r"\bit\b", clean) and READS_HANDED_TEXT.search(clean):
        return CANNOT_SEE["text"]
    return None




# --- a body asked about -------------------------------------------------------
# A second reader, for the same "nothing on this side can look" but a different object: the
# person's own body, or a mark on it. "can you look at my knee", "does this look infected",
# "can you see if this is healing" and "can you tell me if this mole is ok" reached the search
# hedge, and after this file merged they reached its bare-`this` pool instead ("I can't see the
# page you're looking at"). A rash is not a page: what is wanted is not a document read out but an
# opinion on a mark on them. The stand-down in `cannot_see_your_thing` already knows a body is not
# a file; this reader is what says so.
CANNOT_SEE_YOU = (
    "I can't see it from here, sorry - only what you type reaches me. Tell me where it is, how big "
    "it is and how long it has been there, and I'll say what to watch for. A pharmacist can take a "
    "look today if you want eyes on it.",
    "Nothing on my side can look, sorry. Describe it - where it is, what it is like, whether it has "
    "changed - and I'll help you work out what to do next. A chemist will look at it for free, and "
    "today.",
    "I can't see or feel anything from here, so I can't judge it for you. Say where it is and what "
    "it is like, and I'll tell you what I would do about it; if you want it looked at today, a "
    "pharmacist is the quickest way in.",
)
# The ask: the bot's own act, or a question about how the thing looks.
A_LOOK_ASK = re.compile(
    r"\b(?:can|could|would)\s+(?:you|u)\s+(?:please\s+)?(?:look\s+(?:at|over)|"
    r"(?:have|take)\s+a\s+look(?:\s+at)?|see|check|examine|tell\s+me\s+(?:if|whether))\b"
    r"|^\s*(?:does|do|is|are)\s+(?:this|these|it|that)\b"
    r"|^\s*tell\s+me\s+(?:if|whether)\b"
    r"|\bwhat\s+does\s+(?:this|it|my)\b", re.I)
# A bare "can you look at it" is a body only when the turn before was about one.
A_LOOK_ASK_IT = re.compile(
    r"\b(?:can|could|would)\s+(?:you|u)\s+(?:please\s+)?(?:look\s+at\s+it|check\s+it|see\s+it|"
    r"have\s+a\s+look|take\s+a\s+look)\b", re.I)
# Body parts the fallback's BODY_PARTS does not carry, which are still a body.
A_MORE_BODY = frozenset((
    "tongue", "lip", "lips", "cheek", "cheeks", "chin", "forehead", "thumb", "thumbs", "thigh",
    "thighs", "shin", "shins", "calf", "calves", "heel", "heels", "palm", "palms", "scalp",
    "armpit", "armpits", "groin", "bum", "bottom", "eyelid", "eyelids", "nostril", "navel",
    "kidney", "kidneys", "lung", "lungs", "breast", "breasts", "testicle", "testicles", "penis",
))
A_MARK_ON_THEM = re.compile(
    r"\b(?:rash|rashes|lump|lumps|mole|moles|spot|spots|cut|cuts|bruise|bruises|wound|wounds|"
    r"blister|blisters|sore|sores|scar|scars|swelling|swollen|bite|bites|burn|burns|"
    r"infection|infected|healing|stitches|wart|warts|abscess|ulcer|numb)\b", re.I)


# "Back" is a body and also the word for going back to something: "is it worth going back to
# college at 40", "is it worth going back to work part time" and "should i go back to the gym"
# all start with "is it" and hold a body word, so they were answered "I can't see or feel
# anything from here, so I can't judge it for you. Say where it is and what it is like" - a
# question about a course or a job, answered as if it were a mark on their skin. The body reading
# is the one with the person's own back in the line ("my back", "lower back", "back pain",
# "back ache", "on my back", "back is"), or with no returning word at all.
GOING_BACK = re.compile(
    r"\b(?:go|goes|going|went|get|gets|getting|got|come|comes|coming|came|move|moves|moving|"
    r"moved|be|been|being|bring|brings|bringing|brought|give|gives|giving|gave|pay|pays|paying|"
    r"paid|put|puts|putting|hold|holds|holding|held|hand|hands|handing|send|sends|sending|sent|"
    r"cut|cutting|run|running|ran|turn|turns|turning|turned|look|looks|looking|looked|"
    r"walk|walks|walking|walked|drive|drives|driving|drove|fly|flies|flying|flew|sit|sits|"
    r"sitting|sat|step|steps|stepping|stepped|write|writes|writing|wrote|ring|rings|ringing|"
    r"rang|call|calls|calling|called|text|texts|texting|texted|reply|replies|replying|replied)\s+"
    r"(?:straight\s+|right\s+|all\s+the\s+way\s+)?back\b"
    r"|\bback\s+(?:to|from|at|in|on|into|with|home)\b"
    r"|\b(?:give|gives|giving|gave|pay|pays|paying|paid|put|puts|putting|hold|holds|holding|"
    r"hand|hands|handing|send|sends|sending|sent|cut|cutting)\s+(?:it|them|him|her|that|this|"
    r"me|us|the\s+\w+)\s+back\b")
MY_BACK = re.compile(
    r"\b(?:my|lower|upper|sore|aching|achy|stiff|bad|your|his|her|their)\s+back\b"
    r"|\bback\s+(?:pain|ache|aches|spasm|injury|problem|problems|hurts|is\s+sore)\b"
    r"|\bon\s+(?:my|his|her|their|your)\s+back\b|\bback\s+(?:of\s+my|of\s+his|of\s+her)\b")


def _asks_me_to_look_at_them(clean, repaired=None, memory=None):
    """A line asking the bot to look at their body, or a mark on it.

    "can you look at my knee", "can you tell me if this mole is ok", "does this look infected" and
    "what does this rash look like" all reached the search hedge, and a search engine cannot see
    their leg either. The honest line is the one the health pool already gives: nothing here can
    examine anything, and the person who can is a pharmacist, a GP or 111. A line about something
    of theirs that is not their body ("can you look at my cv") names no body and no mark, so it is
    left alone; a red flag never reaches this reader, because the safety pool answers it first.
    """
    from .fallback import BODY_PARTS, SYMPTOM_WORDS, _thread_is_about_the_body
    for line in (clean, repaired or clean):
        if not A_LOOK_ASK.search(line):
            continue
        if A_MARK_ON_THEM.search(line):
            return True
        body = set(re.findall(r"[a-z']+", line.lower())) & (BODY_PARTS | A_MORE_BODY | SYMPTOM_WORDS)
        if body:
            # A returning "back" is not a body: "is it worth going back to college at 40" holds
            # "back" and starts with "is it", and was answered as a mark on their skin.
            if (body - {"back"}) or not GOING_BACK.search(line) or MY_BACK.search(line):
                return True
        if A_LOOK_ASK_IT.search(line) and _thread_is_about_the_body(memory):
            # "my ankle is swollen and i cant tell if its sprained" then "can you look at it": the
            # body is in the turn before, so the bare "it" is a body and needs the same line.
            return True
    return False


def look_at_a_body_lines(clean, repaired=None, memory=None):
    """The pool to say for a line asking the bot to look at the person's body, or None."""
    if _asks_me_to_look_at_them(clean, repaired, memory):
        return CANNOT_SEE_YOU
    return None


# --- a thing in the room with them --------------------------------------------
# "what was that noise", "what's that smell", "whats beeping": the thing is next to the person and
# nowhere near this end. All three reached the search hedge on main - "I'm not sure about that
# one, sorry - I'd rather not guess. A quick search online will get you a solid answer" - which is
# wrong twice over: no search engine can hear the noise either, and the person is standing beside
# it rather than looking for facts about it. The bot's own two senses are already written down in
# the "sound" pool for "can you hear that"; what was missing is the line that says the thing is
# *theirs to describe* rather than something to look up, and the smell, which is worth answering
# with what matters (gas, burning) instead of a question.
# The thing itself, by stem, so that "bang", "banging" and "bangs" are one entry: a person says
# "what was that banging noise" as often as "what was that bang", and a list of exact nouns
# misses the half of them that carry the -ing.
_NOISE_OR_SMELL = (
    r"(?:noise|sound|bang|crash|thud|thump|clatter|rattl|screech|whistl|hum|buzz|ring|beep|"
    r"bleep|chirp|scream|shout|creak|groan|gurgl|drip|tick|knock|tap|pop|crack|dron|whirr|"
    r"hiss|rumbl|racket|alarm|clank|clang|siren|whine|smell|stink|pong|whiff|stench|reek|"
    r"odour|odor|fume)[a-z]*")
A_THING_IN_THE_ROOM = re.compile(
    r"^\s*what(?:'s|s)?\s+(?:was|is|were)\s+(?:that|this)\s+(?:\w+\s+){0,2}"
    + _NOISE_OR_SMELL + r"\b"
    r"|\bwhat(?:'s|s)?\s+(?:that|this)\s+(?:\w+\s+){0,2}" + _NOISE_OR_SMELL + r"\b"
    r"|\bwhat\s+is\s+(?:that|this)\s+(?:\w+\s+){0,2}" + _NOISE_OR_SMELL + r"\b"
    r"|\bwhat(?:'s|s)?\s+(?:is\s+|was\s+)?(?:beeping|ringing|humming|buzzing|rattling|"
    r"chirping|whistling|smelling|banging|clanking)\b"
    r"|\bdid\s+you\s+(?:hear|smell)\s+that\b"
    r"|\b(?:is|was)\s+that\s+a\s+\w+\s+(?:i|we)\s+can\s+hear\b", re.I)
# The same thing said as a statement rather than a question: "there is a strange noise coming
# from the loft", "theres a banging in the pipes", "there is a rattle when the heating comes on".
# It is the same thing in the room, and it was left with a placeholder because the question form
# was the only one the reader knew.
A_THING_NAMED = re.compile(
    r"\b(?:banging|bang(?:ed|s)?|crash(?:ing|ed)?|thud\w*|"
    r"thump\w*|clatter\w*|rattl(?:e|es|ing|ed)|hum(?:ming|s)?|whirr\w*|buzz(?:ing|es)?|"
    r"scrap(?:ing|es)?|scratch(?:ing|es)?|squeal(?:ing|s)?|whistl(?:e|es|ing)|dripp(?:ing|s)?|"
    r"clank(?:ing|s)?|creak(?:ing|s)?|click(?:ing|s)?|beep(?:ing|s)?|bleep(?:ing|s)?|"
    r"chirp(?:ing|s)?)\b", re.I)
# "there is a strange noise", "a sound coming from the wall" - the noise or sound word needs a
# determiner or a describing word in front of it. "sounds good", "that sounds like a plan" and
# "sounds fun" are agreement about the plan, not a thing in the room, and a bare "sounds" that
# reached the room reader turned a spa day into "there is no microphone on this end".
A_NOISE_NAMED = re.compile(
    r"\b(?:a|an|the|this|that|some|strange|funny|odd|weird|loud|quiet|faint|low|high|humming|"
    r"scraping|banging|rattling|dripping)\s+(?:\w+\s+){0,2}(?:noise|noises|sound|sounds)\b",
    re.I)
# "sounds good", "that sounds like a plan", "sounds perfect": agreement about what was just
# said, which is the small-talk reader's turn and not a thing in the room.
A_SOUNDS_AGREEING = re.compile(
    r"\bsounds?\s+(?:like|good|great|fine|ok|okay|lovely|nice|fun|perfect|ideal|brilliant|"
    r"amazing|delicious|to\s+me|about\s+right)\b", re.I)
# A bang in the market, a crash in the shares, a squeal at the end of a story: the same words,
# and none of them a thing in the room. A noise the reader can help with is one the person was
# there for - said as a question about it, or with a place, or with a verb of hearing.
A_WITNESSED = re.compile(
    r"\b(?:there(?:'s|\s+is|\s+was|\s+are|\s+were)|i\s+(?:can\s+)?hea(?:r|rd)|we\s+(?:can\s+)?"
    r"hea(?:r|rd)|can\s+you\s+hear|listen(?:ing)?|coming\s+from|from\s+the|from\s+my|in\s+the|in\s+my|"
    r"on\s+the|through\s+the|under\s+the|behind\s+the|above|below|upstairs|downstairs|outside|"
    r"next\s+door|in\s+here|in\s+there)\b", re.I)
# Where the noise is made decides what is worth saying about it, and it is also the detail the
# person has and the bot does not: the loft, the pipework, or outside the house.
A_NOISE_ABOVE = re.compile(
    # "upstairs" is not the loft: there may be a floor above with people walking on it, and an
    # animal in the roof is the wrong thing to say about a footstep.
    r"\b(?:loft|attic|roof|roofspace|rafters?|ceiling|in\s+the\s+eaves)\b", re.I)
A_NOISE_IN_THE_PIPES = re.compile(
    r"\b(?:pipes?|pipework|radiators?|taps?|cistern|water\s+tank|immersion|plumbing|"
    r"stop\s?cock|drains?)\b", re.I)
A_NOISE_OUTSIDE = re.compile(
    r"\b(?:garden|street|road|outside|alley|yard|next\s+door(?:'s)?\s+(?:garden|house)|"
    r"drive|cul-de-sac|estate)\b", re.I)

# A place and a noise verb is the same thing in the room said without the word "noise": "the
# radiators knock when the heating starts", "something is moving about in the attic". Without
# this the place branch below could never be reached by the lines that name a place most plainly.
A_NOISE_VERB = re.compile(
    r"\b(?:knock|bang|clunk|tick|creak|groan|hum|buzz|rattl|whistl|drip|gurgl|scratch|scuttl|"
    r"rustl|scrap|rumbl|thump|hammer|whin|whirr|click|pop|crackl|squeak|squeal|drum|judder|"
    r"shudder|vibrat|mov(?:e|ing)|bang(?:ing)?)\w*", re.I)

# A noise from the car, the boiler or the washer has a reader of its own that knows that machine,
# and a neighbour's noise is a different conversation: the room reader stands down for all of them.
A_MACHINE_OR_A_NEIGHBOUR = re.compile(
    r"\b(?:car|van|engine|boiler|washing\s+machine|washer|dishwasher|dryer|tumble|fridge|"
    r"freezer|motorbike|mot|bike|neighbou?rs?|next\s+door|dog|cat|baby|child|children|kids?)\b",
    re.I)
# "what's that smell called" is asking for the word for it, which is a knowledge question and not
# a thing in the room that only their own nose can settle.
A_NAME_ASK = re.compile(r"\b(?:called|named|name\s+for|word\s+for)\b", re.I)
THAT_OPENS_A_SENTENCE = re.compile(
    r"\bthat\s+(?:the|a|an|he|she|they|we|you|i|it|there|my|his|her|our|their)\b", re.I)
# The beeps, which have their own pool: a chirp at intervals is a battery.
A_BEEP_WORD = re.compile(r"\b(?:beep|beeps|beeping|chirp|chirps|chirping|bleep|bleeping)\b", re.I)
# A light in the room: a flash, a flicker, a colour on a box, or the lights going out. The words
# alone are not enough - "a light lunch" and "light work" are neither - so a light word has to be
# tied to a state word or a colour.
A_LIGHT_WORD = re.compile(
    r"\b(?:flash|flashes|flashed|flashing|flicker|flickers|flickered|flickering|blink|blinks|"
    r"blinked|blinking)\b"
    r"|\b(?:red|green|orange|amber|blue|white)\s+(?:light|led|lamp)\b"
    r"|\b(?:light|lamp|bulb|bulbs|lights|led|screen)\b[^.]{0,24}\b(?:on|off|out|gone|went|"
    r"flicker\w*|flash\w*|blink\w*|bang|popped|blew)\b"
    r"|\b(?:lights|light)\s+(?:have\s+|has\s+)?(?:gone|went)\s+off\b", re.I)
# A light in the sky, on a plane or a star is a knowledge question about the world, not a thing
# in the room that only their own eyes can settle.
A_LIGHT_OUT_THERE = re.compile(
    r"\b(?:sky|star|stars|moon|plane|meteor|shooting|satellite|aurora|rainbow|sunset|sunrise|"
    r"sun|laser|traffic|helicopter|drone)\b", re.I)
# The whole room going dark at once: a circuit, which has an answer.
LIGHTS_ARE_OUT = re.compile(
    r"\b(?:lights?|power|electric(?:ity)?)\b[^.]{0,20}\b(?:went\s+(?:off|out)|gone\s+off|"
    r"all\s+off|tripped)\b|\b(?:power\s+cut|blackout|fuse\s+box|consumer\s+unit)\b", re.I)
# A cut rather than a bulb: the supply itself, which the network operator knows about and the
# breaker box does not. Read before the lights-out reading, so a power cut is never sent to the
# consumer unit.
A_POWER_CUT = re.compile(
    r"\b(?:power\s+cut|power\s+outage|outage|blackout|no\s+power|power'?s?\s+(?:gone|off|out)|"
    r"power\s+went\s+(?:off|out)|electric(?:ity)?\s+(?:is\s+)?(?:off|gone|out|down)|"
    r"supply\s+(?:is\s+)?(?:off|down))\b", re.I)
# The street, not the house: whoever else is dark is the tell, and it is the operator's job.
A_THE_STREET = re.compile(
    r"\b(?:street|road|avenue|estate|block|area|neighbou?rs?|next\s+door|everyone|whole\s+street)"
    r"\b", re.I)
# A smell rather than a sound, wherever the smell word sits in the line.
A_SMELL_WORD = re.compile(
    r"\b(?:smell|smells|smelling|smelly|stink|stinks|stinking|pong|whiff|stench|reek|reeks|"
    r"reeking)\b", re.I)


def a_thing_in_the_room(clean):
    """The pool for a noise, a smell or a light in the room with them, or None."""
    line = (clean or "").strip()
    if A_POWER_CUT.search(line) and not A_LIGHT_OUT_THERE.search(line):
        if len(line.split()) <= 20:
            return CANNOT_SEE["power_cut"]
    if (LIGHTS_ARE_OUT.search(line) and A_THE_STREET.search(line)
            and not A_LIGHT_OUT_THERE.search(line) and len(line.split()) <= 20):
        return CANNOT_SEE["power_cut"]
    if LIGHTS_ARE_OUT.search(line) and not A_LIGHT_OUT_THERE.search(line):
        if len(line.split()) <= 20 and not A_NAME_ASK.search(line):
            return CANNOT_SEE["lights_out"]
    a_place_at_it = bool(
        (A_NOISE_ABOVE.search(line) or A_NOISE_IN_THE_PIPES.search(line)
         or A_NOISE_OUTSIDE.search(line)) and A_NOISE_VERB.search(line)
        and not THAT_OPENS_A_SENTENCE.search(line))
    if (not A_THING_IN_THE_ROOM.search(line) and not A_LIGHT_WORD.search(line)
            and not A_THING_NAMED.search(line) and not A_NOISE_NAMED.search(line)
            and not a_place_at_it):
        return None
    if A_SOUNDS_AGREEING.search(line):
        return None
    if len(line.split()) > 20:
        return None
    if A_NAME_ASK.search(line):
        return None
    if re.match(r"^\s*did\s+you\s+(?:hear|smell)\b", line) and THAT_OPENS_A_SENTENCE.search(line):
        return None
    if A_SMELL_WORD.search(line):
        return CANNOT_SMELL
    if A_BEEP_WORD.search(line):
        return CANNOT_HEAR_A_BEEP
    if A_LIGHT_WORD.search(line) and not A_LIGHT_OUT_THERE.search(line):
        return CANNOT_SEE["light"]
    # A noise from the car, the boiler or the washer has a reader of its own that knows that
    # machine, and a neighbour's noise is a different conversation - so the guard sits on the
    # sound branch only. A smell near the boiler is still a smell.
    if A_MACHINE_OR_A_NEIGHBOUR.search(line):
        return None
    # The place the noise comes from is the part that is known: what is worth saying about a
    # noise overhead is not what is worth saying about the pipes or the garden.
    if A_NOISE_ABOVE.search(line):
        return CANNOT_SEE["noise_roof"]
    if A_NOISE_IN_THE_PIPES.search(line):
        return CANNOT_SEE["noise_pipes"]
    if A_NOISE_OUTSIDE.search(line):
        return CANNOT_SEE["noise_outside"]
    # Only a noise they were there for: asked about, or placed, or heard. A bang in the market,
    # a crash in the shares and a squeal at the end of a story are the same words about
    # something else, and the sound pool would be answering the wrong conversation.
    if not A_THING_IN_THE_ROOM.search(line) and not A_WITNESSED.search(line):
        return None
    return CANNOT_SEE["sound"]


# The four replies that fit any message: two receptions for a fact, the offer to listen, and a
# nod. A line about a light in the room that gets one of these has been met with the intake form
# while the thing is in front of the person, so the light pool is worth more than the placeholder
# - but only a placeholder is ever replaced, so a reply the bot has of its own always stands.
THE_PLACEHOLDERS = (
    "got it. is there anything you'd like a hand with",
    "i'm listening",
    "thanks for telling me",
    "noted:",
    "thanks for letting me know",
    "ok - noted",
)


def _is_a_placeholder(reply):
    said = " ".join(str(reply or "").lower().replace("\u2014", "-").replace("\u2013", "-").split())
    return any(said.startswith(stem) or stem in said[:60] for stem in THE_PLACEHOLDERS)


def a_light_in_the_room_over_a_placeholder(clean, reply):
    """The light pool for a light in the room that was answered with a placeholder, else None."""
    if not _is_a_placeholder(reply):
        return None
    pool = a_thing_in_the_room(clean)
    if pool is not CANNOT_SEE["light"] and pool is not CANNOT_SEE["lights_out"]:
        return None
    return pool


def a_thing_in_the_room_over_a_placeholder(clean, reply):
    """The room pool for a noise, a smell or a light answered with a placeholder, else None.

    The light hook alone left the same hole for a sound and a smell: the statement form of the
    line ("there is a strange noise coming from the loft", "theres a beeping coming from the
    hall") is answered earlier, by the chain's own momentum pools, so the room reader in
    `fallback_pools._unknown` never runs and the person gets "Thanks for telling me - I'm here if
    you want to dig into any of that." Anything the room reader has a pool for is worth more
    than a placeholder, and only a placeholder is ever replaced.
    """
    if not _is_a_placeholder(reply):
        return None
    return a_thing_in_the_room(clean)


# --- what they said it was like -----------------------------------------------
# The room pools ask for two things: what it was like and where it came from. A person who answers
# that ("it came from the loft", "like burning", "when the heating comes on") is owed the other
# half of the exchange, and on main there was no other half: the pool was offered again, so the
# bot asked for what it had just been told. These lines answer the description with what that
# place or that quality usually means and who settles it, which is as far as honesty goes without
# hearing it. They are read only when the bot asked the question in the turn before, so no other
# line can fall into them.
_ROOM_ASKS = (
    # Only the phrases these pools use, so no other answer's follow-up can reach the lines below.
    "what it was like and where it came from",
    "what usually makes that one",
    "two or three usual causes",
    "where it comes from, and we can work it out",
    "what it is like - gas",
    "where it is strongest",
    "nothing on this end has a nose",
    "has no nose, sorry",
    "i can't smell anything from here",
    "i can't smell it from here",
    "only the words you type reach me",
    "no microphone or speaker on this end",
    "i can't hear anything from here",
    "is nearly always a smoke alarm",
    "usually a smoke alarm's battery",
    "usually a smoke alarm asking for its battery",
    "a light that blinks on a machine",
    "what the light is on",
    "the number of flashes",
    "several lights went at once",
    "several lights going together",
    "i can't see the room you're in",
    "count the flashes",
    "the provider's status page",
    "whether it flashes or stays on",
    "a light on a smoke alarm",
    "if a bulb went with a bang",
    "is the council's to fix",
    "tell me which room and how often",
    "if it is in one spot and repeats",
)
# Each family: the words in the answer, then what that usually is and what to do about it.
# The answer to "it stops for a bit then starts again" turns on what was asked: a chirp at
# intervals is a battery, but a bang, a whirr or a hum that comes and goes is a machine running a
# cycle, and telling someone to change a battery for their boiler is a wrong answer with the right
# shape. So the reading below knows which question it is answering - the bot's own last line is
# the test - and each of the two gets its own pool.
_DESCRIBED_GOES_QUIET_LINES = (
    "Something that stops for a bit and comes back is usually a warning, not a fault - most "
    "often a battery on its way out, which is the cheap thing to change first. If it comes back "
    "at the same interval as before, get it sorted today rather than sleeping through it.",
    "That pattern is what a battery does on its way out: it chirps, pauses, then chirps again. "
    "Change it now, press the test button, and if it still does it, the unit itself is at the "
    "end of its ten years and wants replacing.",
)
A_BEEP_OR_AN_ALARM = re.compile(
    r"\b(?:beep|beeps|beeping|bleep|bleeping|chirp|chirps|chirping|alarm|alarms|smoke|"
    r"carbon\s+monoxide|detector|battery|timer|clock|watch)\b")
DESCRIBED_CYCLE = (
    "A noise that comes and goes on its own is more often a machine doing its job than a fault: "
    "the boiler firing and resting, a fridge, a pump, a fan. Note what is happening either side "
    "of the quiet - the heating clicking on, water running, the fridge door - and that names the "
    "appliance.",
    "Something that starts and stops by itself is usually a cycle rather than a problem: heating "
    "and hot water run on one, and so does a fridge or a pump. Tell me what it does just before "
    "it starts and I will point at the one it is.",
)
DESCRIBED = (
    (("flash", "flashes", "flashed", "flashing", "blink", "blinks", "blinking", "a pattern",
      "in a pattern", "timed", "count"),
     ("A light that flashes in a pattern is a code, and the count is the code: the number of "
      "flashes before the pause is what the manual or the maker's app looks up. Write it down "
      "before it stops, and if the thing is under warranty ring the maker rather than opening it.",
      "Then the flashes are the thing to count - two then a pause is a different fault from five. "
      "The manual's fault table or the maker's app takes that number, and a boiler that has locked "
      "out usually wants its relight steps first.")),
    (("stays on", "stayed on", "steady", "constant", "solid", "it is on", "its on", "always on"),
     ("A light that stays on rather than flashing is usually a warning rather than a fault code: "
      "the thing is running with something it does not like - a filter, a low level, a blocked "
      "drain - and the manual's first page of warnings names it.",
      "Steady on means it has noticed something and is still working. The manual's warning list "
      "is the place to look, and if it is a boiler showing a lockout light, the relight steps in "
      "the manual come before anything else.")),
    (("the whole house", "whole house", "every room", "all of them", "all of the lights",
      "everywhere", "the lot went", "downstairs and upstairs"),
     ("Several lights going together is a circuit rather than a bulb: look in the consumer unit "
      "for the switch that is down and reset it once, and if it trips again leave it off and get "
      "an electrician - a fault that blows twice is one they need to find, not one to keep "
      "resetting.",
      "Then it is the circuit, not the lamps: one reset in the consumer unit is fine, a second "
      "trip means something on that circuit is faulty and it stays off until an electrician has "
      "seen it.")),
    (("the router", "router", "wifi", "wi-fi", "hub"),
     ("A red or amber light on the router is about the connection, not the machine: check the "
      "provider's status page for an outage in your area first, then reseat the cable from the "
      "wall, then power it off for a minute. Red on its own usually means it cannot see the "
      "internet at all.",
      "On a router, the light follows the line: the provider's outage page settles whether it is "
      "them, and a cable that has been kicked out settles whether it is you.")),
    (("stops", "stop", "goes quiet", "comes back", "comes and goes", "every so often",
      "now and then", "intermittent", "not all the time", "on and off", "once in a while",
      "after a while", "then starts", "every minute", "every hour", "every few", "at intervals",
      "repeats", "repeating", "regular"),
     _DESCRIBED_GOES_QUIET_LINES),
    (("under the sink", "drain", "drains", "plughole", "plug hole", "trap", "toilet", "bath",
      "shower", "waste", "sewer", "sink"),
     ("A smell from a drain is nearly always the trap under the sink or the bath: it holds water "
      "as a seal, and when it dries out the sewer comes back up. Pour a jug of water down it "
      "every week and the smell goes; a slow drain wants a kettle of hot water and a spoon of "
      "soda crystals, not bleach.",
      "That is the drain, not the room: the U-bend under the sink traps water to keep the sewer "
      "smell out, and a trap that has dried out lets it back. Run the taps in every sink, bath "
      "and shower once a week, and if it is still there the trap unscrews by hand with a bucket "
      "under it.")),
    (("burning", "burn", "smoke", "smoky", "plastic", "electric", "wiring", "wire", "scorch"),
     ("Burning plastic or hot wiring is the one to act on now: switch the appliance off at the "
      "wall, unplug it if you can reach the plug safely and don't use it again until somebody "
      "has looked at it. Smoke anywhere means out of the house and 999.",
      "A burning smell with nothing on fire is usually a plug, a socket or a cable getting hot. "
      "Switch it off at the wall and leave it off; an electrician will find which one in minutes, "
      "and a landlord has to send one.")),
    (("damp", "musty", "musty", "mould", "mold", "wet", "dank", "cellar", "basement"),
     ("Damp that stays is a leak or a room with no air moving through it, and painting over it "
      "brings it back within a season. Find the wall it starts at, open a window across the room "
      "for ten minutes a day, and tell the landlord in writing - damp and mould are their job "
      "under the housing health and safety rating.",
      "A musty smell is damp somewhere, often behind a unit or under a floor. Look for the "
      "tidemark - the highest line the damp has reached - because that is where the water is "
      "coming in from.")),
    (("dead", "mouse", "mice", "rat", "rats", "rodent", "rotting", "rotten", "decay"),
     ("A smell that arrives suddenly and gets worse for a week is usually a dead rodent behind a "
      "unit or under the floor. It fades on its own in two or three weeks; if it is in a wall or "
      "the floor, the landlord or a pest controller should open it up rather than you.",
      "That one is usually a mouse or a rat that died where it could not be reached. Air the "
      "room, and if it is in a cavity or under boards, ask the landlord or a pest controller to "
      "get to it - the smell does go on its own, but slowly.")),
    (("loft", "roof", "attic", "ceiling", "chimney", "eaves", "gutter"),
     ("A noise in the loft or on the roof is usually an animal: birds and squirrels start at "
      "first light, mice and rats work at night. A bird on the roof at 5am in summer is doing "
      "what birds do; scratching that goes on after dark is the one to have looked at.",
      "From the loft, the usual two are an animal (birds and squirrels at dawn, mice and rats "
      "after dark) and the pipework expanding when the heating comes on. A trap, or a landlord's "
      "pest contract, settles the first; clipping the pipes settles the second.")),
    (("radiator", "pipe", "pipes", "heating", "boiler", "hot water", "central heating",
      "clanking", "banging pipes", "knocking"),
     ("Banging pipes and radiators are usually air in the system or a pipe rubbing where it "
      "passes through a floor or a wall. Bleed the radiators with the heating off and cold, and "
      "if it is a single knock when the boiler fires, that is a valve shutting quickly.",
      "That is usually air in the heating or a loose pipe moving as it warms. Bleed the "
      "radiators - a radiator key, heating off, until water not air comes out - and if it "
      "carries on, a heating engineer clips the run so it cannot knock.")),
    (("fridge", "freezer", "washing machine", "dishwasher", "tumble", "dryer", "oven", "fan",
      "extractor", "machine"),
     ("An appliance that hums, rattles or buzzes is usually not level, or has something touching "
      "it - a pipe, a cupboard, the floor. Push it an inch away from the wall, check the feet, "
      "and if it is still there, the noise is the pump or the fan and it wants an engineer.",
      "Appliances mostly rattle because they are not level or because something is touching them "
      "when they spin. Move it clear of the wall and the cupboard, check the feet are flat on the "
      "floor, and if it stays, it is a bearing or a pump.")),
    (("door", "doors", "gate", "window", "windows", "draught", "draft", "latch", "cupboard"),
     ("A door or a window that knocks is usually a draught moving it, or a latch that has worked "
      "loose - hold each one still on a windy night and the one that stops is the one to fix. A "
      "cupboard door that does it is a hinge or a magnetic catch.",
      "That is usually wind on a door, a gate or a window, or a latch that no longer holds. Hold "
      "each one still as it happens; the one that stops is the one to adjust, and a rubber wedge "
      "does until then.")),
    (("outside", "next door", "neighbour", "neighbors", "street", "garden", "road", "alley"),
     ("Coming from outside, it is usually something in the street rather than in your walls: a "
      "fan, a fridge unit on a shop, a door, traffic. Note the time and how long it lasts - if it "
      "is after 11pm on a regular night, the council's noise team is who acts on it.",
      "From outside, the useful thing is a note of when it happens and how long it lasts, since "
      "that is what the council's noise team acts on. Record a minute of it on your phone if you "
      "can - a recording is what turns a complaint into a case.")),
    (("every morning", "at night", "at 3am", "at 5am", "5am", "3am", "night", "dawn", "morning",
      "when it rains", "when it is windy", "when the heating comes on"),
     ("The time it happens narrows it more than the sound does. Dawn is birds and the heating "
      "coming on; after dark is mice, a boiler, or a neighbour's appliance; when it rains it is a "
      "gutter or a downpipe; in wind it is a fence, a gate or a loose flashing.",
      "The time is the clue: first light is birds and the heating, after dark is animals or an "
      "appliance on a timer, rain is a gutter or downpipe, and wind is a fence or a flashing. Say "
      "which of those it is and I can take it further.")),
)
DESCRIBED_ROOM = (
    "That points at the room rather than the sound - a knock in one place at one time is usually "
    "something fixed moving, and a sound that moves about is usually air or water. Tell me which "
    "room and how often, and I'll narrow it to the one thing.",
    "Thanks - that helps. If it is in one spot and repeats, it is usually something fixed: a "
    "pipe, a board, a fitting. If it wanders round the house, it is air or water. Which is it?",
)
A_DESCRIPTION = re.compile(
    r"\b(?:it|that|the noise|the sound|the smell|its|it's)\b", re.I)


def what_they_described(clean, memory):
    """The other half of a room question: what the thing they named usually is, or None."""
    turns = memory.get("turns") or []
    before = ""
    for turn in reversed(turns):
        said = turn.get("bot") or ""
        if said:
            before = said.lower()
            break
    if not before or not any(ask in before for ask in _ROOM_ASKS):
        return None
    line = (clean or "").strip().lower()
    if not line or len(line.split()) > 20:
        return None
    for words, pool in DESCRIBED:
        if any(word in line for word in words):
            if pool == _DESCRIBED_GOES_QUIET_LINES and not A_BEEP_OR_AN_ALARM.search(before):
                return DESCRIBED_CYCLE
            return pool
    if A_DESCRIPTION.search(line):
        # Nothing named that the table knows: the fixed-or-moving question is what narrows a noise
        # that has been described but not placed, and it is still one step on from a bare "I'm
        # listening".
        return DESCRIBED_ROOM
    return None
