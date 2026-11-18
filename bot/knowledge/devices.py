"""Storage on a computer: a Mac and a Windows PC are emptied in different places.

`technology`'s storage rows keyed on the bare words "storage", "space" and "free up" and
answered with Settings > General > iPhone Storage. That screen does not exist on a Mac or a
PC, so the commonest laptop question of all -

    how do i free up space on my mac      -> Settings > General > iPhone Storage ...

got a phone answer, and "i need to make room on my mac" got nothing at all. A Mac and a PC
are also not the same job: a Mac hides photos, iPhone backups and the Bin behind one Storage
pane, while Windows puts its leftovers under Temporary files and Storage Sense.

So this domain answers one question per machine, and reads the machine out of the line. It
passes on a line that names no computer, which leaves the phone rows and everything else in
`technology` exactly as they were.
"""
import re

from .lookup import entry

ANSWERS = ("technology",)

# The words that name the machine. A Mac line names it ("mac", "macbook", "on my Mac"); a PC
# line may name it ("windows", "pc") or only its parts ("hard drive", "ssd").
MAC = ("mac", "macs", "macbook", "macbooks", "mac book", "imac", "i mac", "mac os", "macos",
       "osx", "os x", "apple computer", "apple laptop")
PC = ("windows", "pc", "pcs", "desktop", "desktops", "laptop", "laptops", "thinkpad",
      "chromebook", "surface", "computer", "computers", "hard drive", "hard disk", "ssd",
      "disk")

# How a line talks about running out of room.
ROOM = ("storage", "space", "full", "free up", "clear", "delete", "disk", "running out",
        "make room", "room", "no space", "space left", "out of space", "no room")
ASK = ("storage", "space", "full", "free up", "clear", "delete", "disk", "room", "running out",
       "out of")
# A PC line may name Windows, or only the part that is full ("my ssd is full"), or ask how much
# is left. A bare "how do i free up space on my laptop" names no machine, so it keeps the answer
# it had: this domain only takes a line that says which machine, not one that makes us guess.
PC_ASK = ("windows", "pc", "pcs", "desktop", "disk", "hard drive", "hard disk", "ssd",
          "computer", "computers", "thinkpad", "chromebook", "surface", "space left",
          "space is left", "no space", "out of space")

# "How much room have I got" is a different answer from "how do I make room": one points at the
# screen that shows the total, the other at the steps that empty it.
CHECK = ("how much", "how full", "how many gb", "how big", "space left", "space is left",
         "no space left", "enough space", "percent", "%")

# A third key, so "how much space is left on my laptop" is a storage question and not the price
# of a laptop: the words of a question about the total are not the words of one about a fault.
# "have" and "got" are not here: with `ROOM`'s "running out" they made every "i have run out
# of flour / sugar / milk / rice / money / washing powder" a full Mac disk, because "i have run
# out of sugar" carries both. A storage question says "left", "how much" or "shows" instead.
HOW_MUCH = ("space left", "is left", "left", "shows", "how much", "how full", "how many")

# "Delete an app" is uninstalling one; "delete" on its own is a storage question. The phrases
# are what stand a storage row down, so a Mac or PC line about a full disk still gets the steps.
NOT_STORAGE = ("delete an app", "delete apps", "delete a app", "deleting an app", "delete the app",
               "delete my app", "delete an application", "delete the application", "remove an app",
               "removing an app", "uninstall", "uninstalling",
               # A calorie question about macaroni cheese is a food question, not a disk: "mac"
               # in the dish name was reaching the storage row. The same words stand down the
               # PC row, because "how many calories in mac and cheese" names no machine at all.
               "calorie", "calories", "kcal", "mac and cheese", "mac n cheese",
               "macaroni and cheese", "macaroni cheese", "macaroni",
               # a program is software, not the room left on the drive: "how do i delete a
               # program from my pc" was given the Temporary files tour. "free up space" and
               # "storage" lines still name the drive, which is what this row is for.
               "program", "programs", "uninstalled", "reinstalled",
               # "windows" and "room" are both decorating words too, so "how do i paint a room
               # with no windows" reached the steps that empty a Downloads folder. These are the
               # phrases a painter says; every real disk line keeps its answer.
               "paint a room", "painting a room", "paint the room", "paint a wall",
               "paint the walls", "paint over", "painting over", "decorating", "decorate",
               "roller", "emulsion", "undercoat", "skirting", "wallpaper", "gloss paint")
# "window" and "room" are house words before they are machine words. "its a small room with no
# window" and "my living room needs a bigger window" hold "window" for Windows and "room" for the
# room left on a drive, so a decorating line got the steps that empty a Downloads folder. Only the
# forms that cannot be about a machine go here: "make room on my mac" keeps its answer.
# A window is a pane of glass before it is an operating system: "how do i clear condensation off
# the windows" held "clear" for the room left on a drive and "windows" for the OS, so a glass line
# got the steps that empty a Downloads folder. Only forms that cannot be about a machine go here.
GLASS = ("condensation", "condensation on", "condensation off", "condensed", "steamed up",
         "steaming up", "steams up", "misted up", "misting up", "fogged up", "fogging up",
         "wet windows", "windows wet", "damp on the windows", "pane", "panes", "squeegee",
         "windscreen", "windshield", "cleaning the windows", "clean the windows",
         "clean windows")
HOUSE = ("living room", "bedroom", "bedrooms", "kitchen", "bathroom", "hallway", "conservatory",
         "floorboards", "wallpaper", "skirting", "no window", "no windows", "windowless",
         "without a window", "bigger window", "curtains", "blinds") + GLASS

PHONE = ("phone", "iphone", "ipad", "android", "tablet", "handset", "sd card", "memory card",
         "usb stick", "usb drive", "external drive", "self storage", "warehouse", "garage",
         "shed", "loft", "attic", "rent")
OTHER = ("battery", "charge", "charging", "charger", "power", "slow", "sluggish", "hot",
         "overheating", "fan", "noisy", "loud", "memory", "ram", "backup", "time machine",
         "broken", "repair", "replace", "buy", "worth", "price", "cost")

MAC_SPACE = (
    "On a Mac: Apple menu > System Settings > General > Storage, click the bar and let it finish "
    "scanning - Photos and old iPhone backups are usually the two biggest. Empty the Bin, clear "
    "the Downloads folder, and turn on Optimise Mac Storage in Photos. A phone backup can be "
    "50GB on its own: Finder > your phone > Manage Backups.")
PC_SPACE = (
    "On Windows: Settings > System > Storage, then Temporary files - Windows Update leftovers and "
    "old installers are usually a few gigabytes. Turn on Storage Sense so they go on their own, "
    "then sort the Apps list by size and move photos and videos to an external drive or OneDrive. "
    "The Downloads folder is the other quiet hog.")
BOTH_SPACE = (
    "On a Mac: Apple menu > System Settings > General > Storage, then empty the Bin and clear "
    "Downloads. On Windows: Settings > System > Storage > Temporary files, and turn on Storage "
    "Sense. Photos, videos and old installers are the biggest three either way.")
BOTH_CHECK = (
    "On a Mac: Apple menu > System Settings > General > Storage. On Windows: Settings > System > "
    "Storage. Both show what is left and what is taking it, biggest first; keep 10 to 20% free.")
MAC_CHECK = (
    "Apple menu > System Settings > General > Storage shows the bar and what is taking it, biggest "
    "first. Keep about 10 to 20% free: below that a Mac slows down and updates refuse to install.")
PC_CHECK = (
    "Settings > System > Storage shows what is left and what is taking it, biggest first. Keep "
    "about 10 to 20% free: below that Windows slows down and updates fail to install.")


SD_CARD_COPY = (
    "Copy things off it before you delete anything: a card that fills up in a camera is often a "
    "confused file table, and bulk deleting on the camera loses shots. Plug the card into a "
    "laptop with a reader, drag the photos and videos to the computer or to Google Photos, then "
    "let the camera format the card from its own menu - not the computer. A bigger card is cheap: "
    "64GB is about a tenner, and take one labelled U3 or V30 if it is for video.")
SD_CARD_BUY = (
    "64GB to 128GB is plenty for photos, and 128GB or more for video, because a minute of 4K is "
    "about 400MB. Look for U3 or V30 on the label - that is a guaranteed write speed, and it is "
    "what 4K video needs - and buy from a shop you trust rather than a marketplace stall, because "
    "fake cards report more room than they have and then lose files. SanDisk, Samsung and Lexar "
    "are the safe names; a card is cheap enough to buy two.")
_BUYING_A_CARD = ("which", "what card", "what sd", "should i buy", "should i get", "recommend",
                  "best card", "best sd", "best memory", "worth buying", "how big", "what size",
                  "which size", "for video", "for a camera", "for my camera", "buying",
                  # A card's size is the buying question however it is asked: "can i put a
                  # bigger sd card in my phone" is asking how big a card to get, and it was
                  # answered with "copy things off it before you delete anything"
                  "bigger", "larger", "bigger card", "bigger sd", "bigger memory",
                  "more space", "more storage", "upgrade", "how much space")
# A card that is going into a device is not the card that filled up in a camera: the question is
# whether there is a slot at all, and what the device does with the card once it is in. A person
# asks it with the device and a shape word and nothing else - "does my phone take an sd card" -
# so the device words are part of the subject and the slot words are how it is asked.
_CARD_INTO_A_DEVICE = ("phone", "iphone", "ipad", "tablet", "android", "samsung", "galaxy",
                       "pixel", "switch", "nintendo", "steam deck", "console", "laptop",
                       "macbook", "computer", "slot", "put in", "put a card", "bigger card",
                       "extra space", "more memory", "adoptable", "expand", "expandable")
# The same question asked as a purchase: "what size sd card do i need" has the card and the
# choosing and nothing about a slot, and it was answered with the UK-to-EU clothes table.
_A_CARD_BEING_CHOSEN = ("what size", "which size", "how big", "which card", "what card",
                        "should i buy", "should i get", "recommend", "best card", "need")
_A_CARD_ASK = ("does", "do i", "how do i", "can i", "is there a", "will it", "where")

_CARD_IN_IPHONE = (
    "There is no card slot in an iPhone, so no card goes in it: the room has to come from the "
    "phone or the cloud. Turn on iCloud Photos and Optimise iPhone Storage (Settings > Photos) "
    "and the full-size originals move off while small versions stay on the phone, then delete the "
    "videos you have already watched. If the card is a camera's, a card reader for the charging "
    "port copies the photos across.")
_CARD_IN_ANDROID = (
    "Most Android phones that still have a slot take a microSD card in the SIM tray, but recent "
    "flagships and the Pixel line have dropped it, so check the spec for your exact model first. "
    "If it has one, put the card in with the phone off and then choose: portable storage, where "
    "photos and videos go on the card, or internal storage (Settings > Storage > the card > "
    "Format as internal), where apps install there but the card is tied to that phone. 64GB or "
    "128GB labelled A1 or A2 is the right buy.")
_CARD_IN_TABLET = (
    "An iPad has no card slot, so its room comes from iCloud or from offloading photos and apps. "
    "An Android tablet usually takes a microSD, with the same choice as a phone: portable "
    "storage, or formatted as internal. A USB-C card reader copies a camera's photos across on "
    "either one.")
_CARD_IN_SWITCH = (
    "The Switch takes a microSD card under the kickstand at the back, behind the little flap: "
    "microSD only, not the full-size card a camera uses. 128GB or 256GB labelled U3 or A1 is "
    "plenty - games are 5GB to 15GB each - and after you put it in, Settings > Data Management "
    "moves the games across.")
_CARD_IN_LAPTOP = (
    "If the laptop has its own SD slot, push the card in until it clicks and it shows up as a "
    "drive; if it has none, a USB card reader is a few pounds. A card is for moving photos "
    "around rather than for more room on the laptop itself - for that an external SSD or a bigger "
    "internal drive is the answer. Copy the files across rather than working off the card, then "
    "format it in the camera.")
# The device decides the answer, and the most specific device word wins: a person who says Switch
# is not asking about a phone, and an iPhone has no slot at all where an Android usually has one.
_DEVICE_OF_THE_CARD = (("switch", "nintendo", "steam deck", "console"),
                       ("iphone",),
                       ("laptop", "macbook", "notebook"),
                       ("ipad", "tablet"),
                       ("phone", "android", "samsung", "galaxy", "pixel", "handset"))
_CARD_IN_DEVICE = {0: _CARD_IN_SWITCH, 1: _CARD_IN_IPHONE, 2: _CARD_IN_LAPTOP,
                   3: _CARD_IN_TABLET, 4: _CARD_IN_ANDROID}


# A card the phone will not read is a fault, and neither "does it have a slot" nor a camera's
# file table answers it: "my android phone wont read the sd card" was told the slot answer and
# "my phone keeps saying sd card unexpectedly removed" the wet-phone one.
_CARD_NOT_READ = ("wont read", "won't read", "wont work", "won't work", "not reading",
                  "not recognised", "not recognized", "unexpectedly removed",
                  "not detected", "card error", "not showing", "doesnt show", "doesn't show",
                  "not working", "stopped working", "keeps saying", "failed", "corrupt",
                  "damaged", "unreadable", "cant read", "can't read")
_CARD_NOT_READING = (
    "A card the phone cannot read is usually its own file system or its contacts rather than the "
    "phone: take it out, check the gold contacts are clean, and put it back with the phone off. "
    "If another device can read it, copy everything off now and format it in the phone (Settings "
    "> Storage > the card > Format); if nothing reads it, the card has failed and a new one is "
    "the only fix. A card that comes and goes is on its way out, so back it up first.")
# The room-left question about a card in a phone: the camera's advice is the wrong steps for it.
_CARD_FULL_IN_A_PHONE = (
    "Copy the photos and videos off it before you delete anything, because that is nearly all "
    "that is on it: plug the phone into a computer and drag them across, or let Google Photos "
    "upload them, then format the card in the phone under Settings > Storage. A bigger card is "
    "the real fix - 64GB or 128GB labelled A1 or A2 - and move the camera's settings so new "
    "photos and video save to the card.")


# "my phone has no sd card slot what do i do" names the slot to say there is not one, so the
# answer is not the slot one: the room comes from the cloud, or from a reader in the port.
_NO_SLOT = ("no sd card slot", "no card slot", "no sd slot", "no slot", "doesnt have a slot",
            "doesn't have a slot", "without a card slot")
_NO_CARD_SLOT = (
    "With no card slot the room has to come from the phone or the cloud: turn on Google Photos or "
    "iCloud Photos and let it back up, delete the videos you have watched and offload the apps you "
    "do not use, and let Photos keep small versions rather than originals. If it is photos on a "
    "card you need to move, a USB-C card reader or an OTG drive plugs into the charging port.")


def _the_device_of_the_card(text):
    """Which device the card is going into, or None when the line names no device."""
    for index, words in enumerate(_DEVICE_OF_THE_CARD):
        if any(word in text for word in words):
            return _CARD_IN_DEVICE[index]
    return None


def _sd_card(memory, understood):
    """A full card wants its photos copied off; a card being chosen wants a size and a speed."""
    text = _text(understood)
    if any(word in text for word in _NO_SLOT):
        return _NO_CARD_SLOT
    if any(word in text for word in _CARD_NOT_READ):
        return _CARD_NOT_READING
    in_a_device = _the_device_of_the_card(text)
    if in_a_device:
        if any(word in text for word in ("full", "no room", "no space", "filled")) and (
                "phone" in text or "android" in text or "samsung" in text or "tablet" in text
                or "galaxy" in text or "pixel" in text):
            return _CARD_FULL_IN_A_PHONE
        return in_a_device
    if any(word in text for word in _BUYING_A_CARD) and not any(
            word in text for word in ("full", "no room", "no space", "running out")):
        return SD_CARD_BUY
    return SD_CARD_COPY


def _text(understood):
    return " ".join(str(part or "") for part in
                    (understood.get("text"), understood.get("clean"))).lower()


def _names_mac(understood):
    text = _text(understood)
    return any(" " + word in " " + text or text.startswith(word) for word in MAC)


def _names_pc(understood):
    text = _text(understood)
    return any(" " + word in " " + text or text.startswith(word)
               for word in PC if word != "disk")


# A disk word without an operating system is a machine's own disk: "how do i free up disk space"
# names no Mac and no PC, and it has to keep the both-paths answer.
_DISK_WORDS = ("disk", "disc", "hard drive", "hard disk", "ssd", "disk space")


def _names_a_disk(understood):
    text = _text(understood)
    return any(word in text for word in _DISK_WORDS)


def _asking_how_much(understood):
    text = _text(understood)
    return any(word in text for word in CHECK)


def _mac_space(memory, understood):
    # "we have no room in the kitchen" and "i have no space in my flat" carry two words of the
    # key ("no room", "no space") and none of its subject, so the row scored on room alone and
    # answered a kitchen with the Mac's Storage screen. The machine has to be in the line.
    if not _names_mac(understood):
        return None
    return MAC_CHECK if _asking_how_much(understood) else MAC_SPACE


def _pc_space(memory, understood):
    # The same guard as the Mac row, and the disk words count as naming a machine, so
    # "how do i free up disk space" still gets both paths.
    if not (_names_pc(understood) or _names_mac(understood) or _names_a_disk(understood)):
        return None
    how_much = _asking_how_much(understood)
    if _names_mac(understood) and not _names_pc(understood):
        return MAC_CHECK if how_much else MAC_SPACE
    if not _names_pc(understood):
        # "how do i free up disk space" names no machine at all: give both paths rather than
        # send a Mac owner to a Windows settings page.
        return BOTH_CHECK if how_much else BOTH_SPACE
    return PC_CHECK if how_much else PC_SPACE


# A storage card is a small disk, and "my sd card is full" is the room-left question, not the
# credit-card-at-its-limit one: it was answered with a payment plan. The words that name the card
# are the subject, and running out of room is the ask, so the same row covers a memory card in a
# camera, a micro SD in a phone and a usb stick.
SD_CARD = ("sd card", "sdcard", "sd cards", "sd-cards", "micro sd", "microsd", "micro sd card",
           "memory card", "memory cards", "storage card", "flash card", "camera card",
           "photo card", "card in my camera", "card in the camera", "cards in my camera",
           "card for my camera", "card for the camera",
           # the slot itself is the subject of the question: "does an iphone have a card slot"
           # names no card and no brand of card, and was a hedge for want of one word.
           "card slot", "memory card slot", "sd card slot", "microsd slot", "slot for a card")
SIM_CARD = ("sim card", "sim cards", "simcard", "simcards", "sim")
CARD_ROOM = ("full", "no room", "no space", "space", "storage", "free up", "clear", "delete",
             "copy", "move", "moving", "running out", "out of space", "fill up", "filled up",
             "filling up", "clean up", "sort out", "back up", "backup", "how much", "room left",
             "replace", "bigger", "buy")
# A sim is not a disk: it holds the number, the contacts and the texts, and it was answering the
# card question only because it carries the word. The phone-contract lines that name a sim are
# the other question and keep their own answer.
SIM_NOT_THIS = ("sim only", "sim-only", "sim deal", "sim deals", "sim contract", "esim", "e-sim",
                "pay monthly", "pay as you go", "tariff", "rolling contract", "cheapest sim",
                "best sim", "which sim", "new sim", "order a sim", "sim free", "sim-free",
                "unlock", "network", "port my number", "switch network", "data plan",
                "upgrade", "cancel", "price", "cost", "cheap", "deal")


# "Mac" is a food as well as a machine: "a big mac", "mac and cheese". The keys here are the
# machine's name, and "how many calories in a big mac" was answered with where the storage screen
# is - the steps for a full Mac disk, to somebody asking about a burger. The words of the food
# stand the machine down for that line; a real Mac line carries none of them.
_FOOD_NOT_A_MACHINE = ("big mac", "mac and cheese", "mac cheese", "macaroni", "calorie",
                       "calories", "burger", "burgers", "mcdonalds", "mcdonald", "kfc")


def _stands_down_for_food(one):
    """A Mac entry, with the food words added to its stay-away list."""
    if not any(isinstance(part, tuple) and "mac" in part for part in one.key):
        return one
    one.avoid = one.avoid + tuple(word for word in _FOOD_NOT_A_MACHINE
                                  if word not in one.avoid)
    return one


# A phone setting the phone does itself: where you are, and who can see it. No storage words and
# no machine, so the rows above never saw it, and `money`'s "sharing is not shares" row had already
# fenced the commonest wording out (see its `avoid`: "how do i share my location with my husband"
# is a phone setting, not a pot of money). The line was left with the search hedge, which names
# nothing, and the sensible thing to name is the app the person already talks to that person in.
WHERE_I_AM = ("location", "locations", "live location", "my location", "where i am",
              "where im", "where i'm", "where i was", "where i went", "where i've been",
              "where ive been", "whereabouts", "gps", "find me",
              # a person doing the tracking is a sharing question, and "should i let my partner
              # track my phone" reached the phone-listening card the privacy rows use: the phone
              # listening is not somebody watching where you are. The bare "track me" is not here
              # on purpose - "is my phone tracking me" is the privacy card's question, and the
              # thing named as doing the tracking is what tells the two apart.
              "track my phone", "tracking my phone", "track my location",
              "tracking my location", "see where i am")
SHARE_IT = ("share", "shares", "sharing", "send", "sends", "show", "let them see",
            "let him see", "let her see", "let someone see", "track", "tracking",
            "see where", "sees where", "know where", "knows where", "find where",
            # "who can see my location" names the asking side and no verb of sharing at all, and
            # the fields that answer it are the ones this row's card already reads out
            "who can see", "can they see", "can he see", "can she see", "sees my location",
            "knows my location")
# Sharing a file, a screen, a photo or an account is not sharing where you are, and neither is a
# flat, a bill or a lift that people share: every one of those has its own answer.
NOT_WHERE_I_AM = ("file", "files", "folder", "folders", "screen", "screenshare",
                  "photos", "photo", "pictures", "picture", "album", "document", "documents",
                  "dropbox", "google drive", "onedrive", "icloud", "memory card", "usb",
                  "netflix", "spotify", "streaming", "password", "passwords", "account",
                  "wifi", "wi-fi", "printer", "flat", "house", "room", "rooms", "bill",
                  "bills", "rent", "money", "cost", "costs", "split", "custody", "car",
                  "lift", "ride", "taxi", "cooking", "toilet", "bathroom",
                  # "how do i share my location with the police" is not the app's Share
                  # live location: an emergency number passes your position to the service
                  # itself, and a report to 101 is made in words. Steps that broadcast to a
                  # contact are the wrong answer to it, so this row stands down.
                  "police", "999", "911", "112", "ambulance", "fire brigade", "emergency",
                  "emergency services", "coastguard", "mountain rescue")

# The row above teaches how to *start* sharing where you are, and a line that shares the same
# words asking for the opposite is a different question with an answer of its own in
# `technology`'s turn-off-location row: "how do i stop sharing my location" was told how to
# share it. Two words in either order is what separates them ("turn location sharing off",
# "stop my phone sharing my location"), so this reads the line rather than sitting in the avoid
# list, where a loose "off" would stand the row down for "how do i share my location off my
# phone" too.
_ASKS_TO_STOP_SHARING = re.compile(
    r"\b(?:stop|stops|stopped|stopping|quit|prevent)\b[^.?!;]{0,48}"
    r"\b(?:shar(?:e|es|ed|ing)|send(?:s|ing)?|broadcast\w*|location|gps|found|see|sees|seeing|"
    r"seen|know|knows|knowing|tracked|tracking)\b"
    r"|\b(?:turn|turns|turning|switch|switches|switching|shut|shutting)\b[^.?!;]{0,20}"
    r"\b(?:off|out)\b"
    r"|\b(?:hide|hides|hiding|hidden|disable|disables|disabling|withhold|withholding)\b"
    r"|\b(?:don'?t|dont|do not|not)\s+(?:want\s+(?:to\s+)?)?"
    r"(?:shar(?:e|ing)|be\s+(?:found|seen|tracked))\b"
    # "i dont want my ex to see where i am" and "without my husband knowing" are the same ask as
    # "how do i stop sharing my location", and the share steps are the opposite of the answer: a
    # person hiding from someone must not be told how to broadcast where they are. The want is
    # negative, and what they are asking is who can see, not how to turn it on.
    r"|\b(?:don'?t|dont|do not|doesn'?t|not)\s+(?:want|wants|wanted|like)\b[^.?!;]{0,40}"
    r"\b(?:see|sees|seeing|know|knows|knowing|find|finds|finding|track|tracks|tracking|"
    r"shar(?:e|ing))\b"
    r"|\bwithout\b[^.?!;]{0,32}\b(?:knowing|seeing|finding\s+out|being\s+seen)\b"
    r"|\b(?:nobody|no\s+one|no-one|anyone|anybody)\b[^.?!;]{0,24}"
    r"\b(?:can|could|should|will|would|must|to)\b[^.?!;]{0,16}"
    r"\b(?:see|sees|know|knows|find|track)\b"
    r"|\bkeep\b[^.?!;]{0,24}\b(?:private|secret|hidden|to\s+myself)\b"
    r"|\bwho\s+(?:else\s+)?(?:can|could)\s+see\b|\bwho\s+sees\b"
    r"|\b(?:privacy|opt out|opting out|unshare|stop sharing)\b", re.IGNORECASE)

def _not_asking_to_stop(understood):
    """True unless the line asks for sharing to stop, which the turn-off row answers."""
    if not isinstance(understood, dict):
        return True
    said = understood.get("text") or understood.get("clean") or ""
    if not said:
        said = " ".join(understood.get("words") or ())
    return not _ASKS_TO_STOP_SHARING.search(str(said))


# "How does gps know where i am" is a question about the satellites, not about sharing: the row
# below would answer it with "share it from the app you already message each other in", which is
# the answer to a different question. The thing that decides it is what the knowing is done by -
# a machine (gps, the phone, the app, location services) is the how-it-works card, a person
# ("how does my husband know where i am") is this row.
_ASKS_HOW_IT_WORKS = re.compile(
    r"\bhow\s+(?:does|do|did|is|are|can)\b[^.?!;]{0,24}"
    r"\b(?:gps|phone|iphone|android|it|this|that|app|maps?|location\s+services?|"
    r"tracking|signal|satellites?)\b[^.?!;]{0,24}"
    r"\b(?:know|knows|work|works|worked|find|finds|track|tracks|get|gets|locate|locates)\b"
    r"|\bwhat\s+is\s+gps\b", re.IGNORECASE)


# "How does my husband know where i am" is not "how do i share my location": the ask is how
# they came to know, and the honest half is that an app on the phone is already sharing it. The
# same line with an app as the knower - "how does snapchat know where i am" - is the same
# question. A machine that knows by itself (gps, the phone, location services) keeps the
# satellites card, so the roster below holds people and apps, not machines.
WHO_KNOWS = ("husband", "wife", "partner", "boyfriend", "girlfriend", "ex", "mum", "mom",
             "mother", "dad", "father", "son", "daughter", "brother", "sister", "boss",
             "friend", "friends", "someone", "somebody", "he", "she", "they", "them",
             "him", "her", "snapchat", "whatsapp", "instagram", "insta", "facebook",
             "messenger", "tiktok", "find my", "google", "life360", "app", "apps")
_ASKS_HOW_THEY_KNOW = re.compile(
    r"\bhow\s+(?:does|do|did|can|could|would|will)\s+(?:my|our|the|this|that|an?)?\s*"
    r"\b(?:" + "|".join(WHO_KNOWS) + r")\b[^.?!;]{0,26}"
    r"\b(?:know|knows|knew|knowing|see|sees|saw|seeing|find|finds|found|found\s+out|"
    r"track|tracks|tracked|tracking|locate|locates|worked\s+out|work\s+out)\b[^.?!;]{0,26}"
    r"\b(?:where\s+(?:i|im|i'?m|we)\s+(?:am|was|is|are|went|go|been|at|now|right\s+now)|"
    r"my\s+location|my\s+whereabouts)\b", re.IGNORECASE)


# The row below says how to share where you are, and a person asking whether they should is
# asking for a judgement: "should i share my location on a dating app" got the steps for
# broadcasting, which answers a question nobody asked. The steps are the answer to "how do i",
# and a "should i", "is it safe to" or "do i need to" is left to the row and the floor that
# weigh a plan rather than to the one that gives instructions.
_ASKS_WHETHER_TO_SHARE = re.compile(
    r"\b(?:should|shall|ought)\s+(?:i|we)\b|"
    r"\bis\s+it\s+(?:safe|wise|ok|okay|alright|a\s+good\s+idea|worth|sensible|risky)\b|"
    r"\bwould\s+it\s+be\b|\bdo\s+(?:i|we)\s+need\s+to\b|\bam\s+i\s+(?:safe|risky|wrong)\b|"
    r"\bbetter\s+to\b|\bany\s+(?:risk|danger)\b",
    re.IGNORECASE)

SHARE_STEPS = (
    "Share it from the app you already message each other in, because then it is live and "
    "they can see you moving. WhatsApp: open the chat, tap the + or the paperclip, choose "
    "Location, then Share live location and pick 15 minutes, 1 hour or 8 hours. iPhone: in "
    "Messages tap the person's name at the top, then Share My Location, or use Find My > "
    "People > Share My Location. Android: Google Maps > your picture > Location sharing > "
    "New share. It keeps updating until you stop it, so stop it when you are there.")


def _the_said(understood):
    """The line's own words, from whichever reading a callable is handed."""
    if understood is None:
        return ""
    if isinstance(understood, dict):
        for key in ("text", "clean", "norm_text", "plain"):
            if understood.get(key):
                return str(understood[key])
        return " ".join(str(w) for w in (understood.get("words") or ()))
    for key in ("text", "clean", "norm_text", "plain", "said"):
        said = getattr(understood, key, "")
        if said:
            return str(said)
    return str(understood)


def _asks_whether_to_share(understood):
    """True when the line asks whether to share rather than how."""
    return bool(_ASKS_WHETHER_TO_SHARE.search(_the_said(understood)))


HOW_THEY_KNOW = (
    "Somebody sees where you are because an app on the phone is sharing it, and sharing "
    "is the default in the ones people use to keep in touch: Find My on an iPhone and "
    "Google's location sharing on Android both keep reporting until they are turned off, "
    "and anyone in a family group, a shared account or a live-location message is already "
    "watching. Look at who is on the list rather than at the phone: on an iPhone Settings "
    "> Privacy & Security > Location Services, and in Google Maps your picture then "
    "Location sharing, both show who can see you and for how long, and each name can be "
    "removed from there. If nobody is on either list, a shared account or a car's app is "
    "the next place to look.")

# "can my boyfriend see where i am on his phone" is not a how-to: nobody is asking to be given
# the steps, they are asking who can already watch. The same card answers it, so the sharing row
# says that one for this shape rather than the steps.
_ASKS_WHO_CAN_SEE = re.compile(
    r"\b(?:can|could|does|do|did|is|are|has|have)\b[^?.!]{0,30}\b"
    r"(?:see|sees|know|knows|show|shows|reveal|reveals|tell|tells|track|tracking|watch|"
    r"watching)\b[^?.!]{0,25}\bwhere\s+(?:i|we)\s+"
    r"(?:am|are|was|were)\b|"
    r"\bwho\s+can\s+see\b|\bwho\s+sees\b|\bwho\s+knows\s+where\b|"
    r"\b(?:see|sees|know|knows|show|shows)\b[^?.!]{0,20}\bmy\s+(?:location|whereabouts)\b",
    re.IGNORECASE)


# "how do i let someone see where i am" is the same words in the other direction, and it wants
# the steps: the person is doing the letting, not asking who is watching them.
_ASKS_FOR_THE_STEPS = re.compile(
    r"\bhow\s+(?:do|can|would|should)\s+i\b|\bhow\s+to\b|\blet\s+(?:them|him|her|someone|"
    r"somebody|my)\b|\bmake\s+(?:them|him|her|it)\b|\bso\s+(?:they|he|she)\s+can\b",
    re.IGNORECASE)


def _asks_who_can_see(understood):
    """True when the line asks who can already see where the person is."""
    said = _the_said(understood)
    if _ASKS_FOR_THE_STEPS.search(said):
        return False
    return bool(_ASKS_WHO_CAN_SEE.search(said))


def _format_sharing_where_i_am(memory, understood):
    """The steps for sharing where you are, or what the shape of the share is when the line asks
    whether to. "should i share my location on a dating app" is a judgement, and it used to reach
    a dating-invitation card, and "is it safe to share my location with someone i met online" a
    one-off virtual card, both of them other rows reading the word "share": a how-to does not
    answer a whether-to. The setting decides how much a person sees, not whether to trust them,
    so say that much and leave the weighing to them."""
    if _asks_who_can_see(understood):
        return HOW_THEY_KNOW
    if _asks_whether_to_share(understood):
        return (
            "That is yours to weigh, and the setting decides how much they see rather than "
            "whether to trust them: live sharing keeps updating for as long as the timer runs, so "
            "they watch you move and still have it afterwards, while a location sent once says "
            "only where you were at that moment. In WhatsApp tap the + or the paperclip, choose "
            "Location, then Send your current location for the point or Share live location for "
            "15 minutes, 1 hour or 8 hours; Google Maps, your picture then Location sharing, "
            "lists every share you have running and stops any of them.")
    return SHARE_STEPS


def _not_asking_whether_to_share(understood):
    """True unless the line asks whether to share rather than how."""
    if not isinstance(understood, dict):
        return True
    said = understood.get("text") or understood.get("clean") or ""
    if not said:
        said = " ".join(understood.get("words") or ())
    return not _ASKS_WHETHER_TO_SHARE.search(str(said))


def _not_asking_how_they_know(understood):
    """True unless the line asks how somebody came to know where the person is."""
    if not isinstance(understood, dict):
        return True
    said = understood.get("text") or understood.get("clean") or ""
    if not said:
        said = " ".join(understood.get("words") or ())
    return not _ASKS_HOW_THEY_KNOW.search(str(said))


def _asks_how_they_know(understood):
    """True only when the line asks how somebody came to know where the person is."""
    return not _not_asking_how_they_know(understood)


def _not_asking_how_it_works(understood):
    """True unless the line asks how the phone knows, which the satellites card answers."""
    if not isinstance(understood, dict):
        return True
    said = understood.get("text") or understood.get("clean") or ""
    if not said:
        said = " ".join(understood.get("words") or ())
    return not _ASKS_HOW_IT_WORKS.search(str(said))


def _not_a_sharing_ask(understood):
    """The stand-downs the sharing row needs: not the opposite ask, not a how-do-they-know,
    and not the how-it-works one.

    "who can see my location" is the one exception to the first: it says nothing about turning
    anything on, and the card that answers it is the one that lists who can already see and how
    to take each name off, which is the same help the turn-off row gives from the other end.
    """
    if _asks_who_can_see(understood):
        return True
    return (_not_asking_to_stop(understood) and _not_asking_how_they_know(understood)
            and _not_asking_how_it_works(understood))


# Unfriending and blocking on a social app. "how do i block a number" and "how do i stop spam
# texts" are the phone's own rows, so a number, a caller or a text stands this one down.
SOCIAL = ("facebook", "fb", "instagram", "insta", "social media", "social", "friend",
          "friends", "someone", "somebody", "him", "her", "them", "my ex", "mum",
          "dad", "brother", "sister", "husband", "wife")
NOT_SOCIAL = ("number", "numbers", "call", "calls", "caller", "text", "texts", "sms",
              "spam", "phone", "iphone", "android", "whatsapp", "email", "e mail",
              "mail", "door", "road", "street", "pip", "drain", "chimney", "sink",
              "toilet", "wall", "garden", "parking", "drive",
              # "Blocked" is the past participle of a thing being stopped up, and that is
              # what the word means in a hospital and in a drain: "they said it was a
              # blocked artery and hes got a stent now" was sent to Facebook's Unfriend
              # button, because "blocked" is in the row's key and "dad" and "him" are in
              # its social words. A line naming one of these is not about a person being
              # blocked, whatever else it says.
              "artery", "arteries", "vein", "veins", "stent", "stents", "sinus",
              "sinuses", "airway", "bowel", "lung", "lungs", "catheter", "nose",
              "ear", "ears", "throat", "pipe", "pipes", "hose", "duct", "ducting",
              "gutter", "gully", "sewer", "filter", "filters",
              # And the other half: "my ex blocked me" is somebody telling you what was done
              # to them, and it was handed the instructions for doing it. The verb in the
              # past about the other person is what says so; "how do i block my ex" keeps
              # the row because it asks.
              "blocked me", "blocks me", "has blocked me", "have blocked me",
              "they blocked me", "he blocked me", "she blocked me", "blocked my number",
              "blocked my account", "got blocked", "been blocked", "i was blocked",
              "i am blocked", "i got blocked")

def _unfriend_or_block(memory, understood):
    """The button that was asked for first, then the other one, then how far it goes.

    "how do i unfollow my ex" was led with Unfriend, which is one step further than the
    question and ends the friendship, so the verb the person used decides the order.
    """
    if not isinstance(understood, dict):
        return None
    said = understood.get("text") or understood.get("clean") or ""
    if not said:
        said = " ".join(str(w) for w in (understood.get("words") or ()))
    line = str(said).lower()
    unfollow = re.search(r"\bunfollow", line)
    block = re.search(r"\bblock(?:ed|ing)?\b", line)
    unfriend = re.search(r"\b(?:unfriend|defriend|remove (?:a )?friend)", line)
    if unfollow and not unfriend:
        return ("On Facebook open their profile, tap Following, then Unfollow - they are not "
                "told, and it takes their posts out of your feed without ending the "
                "friendship. On Instagram it is the same two taps: their profile, then "
                "Following, then Unfollow. If you want them gone further than that, the ... "
                "menu on their profile has Block, which stops them finding you, messaging you "
                "or seeing anything you post, and you can undo it in Settings > Blocked.")
    if block and not unfriend:
        return ("Blocking stops them finding you, messaging you or seeing anything you post: "
                "open their profile, tap the ... menu, then Block. They are not told, and you "
                "can undo it in Settings > Blocked. Unfriending is the smaller step - Friends, "
                "then Unfriend - which stops the posts but still lets them message you.")
    return ("On Facebook open their profile, tap Friends, then Unfriend - they are not told. "
            "Blocking goes further: the ... menu on their profile, then Block. On Instagram "
            "open their profile, tap Following to Unfollow, or the ... menu to Block. "
            "Unfriending only stops the posts; blocking stops them finding you, messaging you "
            "or seeing anything you post, and you can undo it in Settings > Blocked.")


ENTRIES = [
    entry("share-where-i-am", (WHERE_I_AM, SHARE_IT),
          _format_sharing_where_i_am,
          ask=SHARE_IT,
          bias=1,
          # "how do i stop sharing my location" is the turn-off row's question, not this one,
          # and "how does gps know where i am" is the satellites card's
          guard=_not_a_sharing_ask,
          avoid=NOT_WHERE_I_AM),

    # The row beside it teaches how to start sharing; this one answers the ask that follows
    # from it, "how does he know where i am", which had a placeholder and, once the sharing row
    # was widened, would have been told how to broadcast to the person they are asking about.
    entry("how-they-know-where-i-am", (WHERE_I_AM, SHARE_IT + (
              "find out where", "finds out where", "found out where", "find where",
              "found where", "knew where", "saw where", "work out where",
              "worked out where", "knows my location")),
          HOW_THEY_KNOW,
          ask=("know where", "knows where", "knew where", "know where i am", "see where",
               "sees where", "saw where", "find where", "find out where", "finds out where",
               "found out where", "found where", "tracking where", "knows my location",
               "worked out where", "work out where"),
          bias=1,
          # the sharing row above is the same words in the ask direction, and the turn-off row
          # owns the person who wants it stopped
          guard=_asks_how_they_know,
          avoid=NOT_WHERE_I_AM + ("stop", "turn off", "hide", "dont want", "don't want",
                                  "without", "nobody", "no one", "private")),

    entry("unfriend-or-block-on-social",
          (("unfriend", "unfriending", "unfriended", "defriend", "unfollow", "unfollowing",
            "remove a friend", "remove friend", "remove them from my friends", "block",
            "blocking", "blocked"), SOCIAL),
          _unfriend_or_block,
          ask=("unfriend", "unfriending", "unfriended", "defriend", "unfollow", "unfollowing",
               "remove", "block", "blocking", "blocked", "how", "can i", "do i"),
          bias=1,
          avoid=NOT_SOCIAL),
    entry("mac-storage-full", (MAC, ROOM, HOW_MUCH),
          # The machine is in the line, so one row answers both questions a person asks
          # about a full disk: what is taking it, and how to get room back.
          _mac_space,
          # The guard is the machine. The key is storage words and "no room" is one of them, so
          # without this "we have no room in the kitchen" reached Apple's Storage pane and beat
          # the home row that answers it. A full disk is a question about a named machine: a line
          # that names none is either another machine's line (the PC row takes "disk", "laptop",
          # "ssd") or not a storage question at all.
          ask=MAC,
          bias=2,
          # A Mac line can carry "disk" or "computer" too ("my mac disk is full"), so only the
          # words that name another machine stand the Mac row down.
          # "delete" is in the key because "what can i delete on my mac" is a storage question,
          # but "delete an app" is uninstalling one, and that answer is not this one. The phrase
          # is held rather than the word, so the storage lines that talk about deleting keep it.
          avoid=PHONE + OTHER + HOUSE + ("windows", "pc", "pcs", "desktop", "desktops",
                                 "thinkpad",
                                 "chromebook", "surface",
                                 # "the wifi shows full bars but nothing loads" is a network
                                 # line: "full" and "shows" covered this row's two groups.
                                 "wifi", "wi-fi", "signal", "bars", "internet", "broadband",
                                 "loads", "loading", "browser",
                                 # A Big Mac is a burger, not the machine: "how many calories in a
                                 # big mac" was answered with the Storage pane on main `a2dbea5`.
                                 "big mac", "big macs") + NOT_STORAGE),
    entry("pc-storage-full", (PC, ROOM, HOW_MUCH),
          _pc_space,
          ask=PC_ASK,
          bias=1,
          avoid=PHONE + OTHER + HOUSE + MAC + NOT_STORAGE),
    # "what is the difference between an ssd and a hard drive" was a shrug on main: two parts
    # that nobody compares in words, so no row held them. The choice is the only question here,
    # and a disk with no room left is a different one - the storage rows answer that.
    entry("ssd-vs-hdd", (("ssd", "ssds", "solid state drive", "solid state", "nvme"),
                         ("hdd", "hdd's", "hard drive", "hard disk", "spinning disk", "disk",
                          "difference", "better", "faster", "slower", "worth", "upgrade",
                          "vs", "versus", "compare", "choose", "buy", "replace")),
          "An SSD has no moving parts, so the machine starts in seconds and apps open at once; a "
          "hard drive is a spinning disc and only wins on price for each gigabyte. For a laptop "
          "the SSD is the one upgrade that makes an old machine feel new - a 500GB one is cheap "
          "now and cloning the old disk across is a job a shop will do in an hour. Buy a big hard "
          "drive only for bulk storage and backups.",
          ask=("difference", "better", "faster", "slower", "worth", "upgrade", "upgrading",
               "upgrad", "vs", "versus",
               "compare", "choose", "buy", "replace", "what", "which", "should"),
          avoid=("space", "full", "free up", "left", "how much", "how many", "storage",
                 "make room", "no room", "running out", "clean up", "delete")),

    entry("sd-card-full",
          (SD_CARD, CARD_ROOM + _CARD_INTO_A_DEVICE + _A_CARD_BEING_CHOSEN),
          _sd_card,
          # The ask is the room-left question, the same question about a device ("does my phone
          # take a card", "how do i put one in") or the card being chosen. A card going into a
          # phone names the device and the slot and nothing else, so without these the row never
          # reached the line and it fell to whatever held "take" or "size".
          ask=CARD_ROOM + _CARD_INTO_A_DEVICE + _A_CARD_BEING_CHOSEN + _A_CARD_ASK, bias=3,
          avoid=("credit card", "bank card", "debit card", "payment", "pay", "owe", "debt",
                 "bill", "money", "borrow", "loan", "santander", "barclays", "halifax",
                 "gift card", "voucher", "birthday card", "christmas card", "greeting card",
                 "playing card", "card game", "loyalty card", "store card", "nectar",
                 "clubcard",
                 # How a card is formatted is the file-system question, not the room-left one:
                 # "do i need to format an sd card before i use it" was told to copy the photos
                 # off, when the answer is exFAT for a card that moves between Windows and a Mac.
                 "format", "formatted", "formatting", "exfat", "fat32", "file system")),
    # A sim card is full of messages, never photos: it stores the number, the contacts and the
    # texts. Same shelf as the sd card, and a different answer, so it is its own row.
    entry("sim-card-full", (SIM_CARD, CARD_ROOM + ("messages", "texts", "contacts", "numbers")),
          "A sim holds your number, your contacts and your texts, not photos, so what fills it "
          "is old messages. Delete the old texts first, and picture messages go first because "
          "they are big. Copy the contacts to the phone itself or to a Google or Apple account so "
          "they do not live on the card, then back up the texts you want to keep - a new sim "
          "does not bring the old messages with it.",
          ask=CARD_ROOM + ("messages", "texts", "contacts", "numbers"),
          bias=2,
          avoid=SIM_NOT_THIS + ("sim card slot", "sim tray", "no sim", "sim card is not",
                                "insert sim", "sim not working")),
]

ENTRIES = [_stands_down_for_food(one) for one in ENTRIES]
