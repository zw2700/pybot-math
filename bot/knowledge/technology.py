"""Technology: phones, laptops, wifi, passwords and the everyday fixes people ask for.

The answers lane owns this domain. Entries are keyed by the device and the symptom
(phone + battery + drains, laptop + fan + loud) rather than by wording, so the same
advice answers "my phone dies by lunchtime" and "why does my battery drain so fast".
Each reply answers in its first sentence and gives the one or two things worth doing
first; the flat "turn it off and on" advice is only given when it really is the first
step.
"""
import re

from ..understanding.topics import the_bin_is_on_a_machine
from .lookup import entry, not_a_sleepy_body

ANSWERS = ("technology",)

# The words that make a line about a pair of spectacles rather than the glass in something. The
# phone-cracked-screen row is keyed on "glass" and needs to turn down "my glasses are scratched"
# without turning down "i cracked the glass on my phone". An avoid word cannot say that: "glasses"
# folds onto "glass" in the matcher, so it stands the row down on every glass in the house.
_SPECTACLES_IN_THE_LINE = re.compile(
    r"\b(?:glasses|eyeglasses|eye glasses|spectacles|specs|sunglasses|eyewear|optician|"
    r"opticians|lenses|contact lens|contacts)\b", re.I)

# A price asked about a phone is the price question, not a cracked screen: the key of the screen
# row holds the phone words, and "cost" in its second group, so without this guard "how much
# does a mobile phone cost" would be told to put a protector on it. What keeps a price line on the
# row is a word for damage already done, and nothing else: "how much does it cost to fix a cracked
# screen" is a person with a cracked screen, while "how much does it cost to replace a phone
# screen" is a price, and the repair-price row owns it. So the repair and replace words are
# deliberately not here even though the row's key holds them.
_PRICE_ASKED = re.compile(r"\b(?:how much|how many pounds|cheapest|price|prices|priced|cost|"
                         r"costs|worth|afford)\b", re.I)
_A_DAMAGE_IN_THE_LINE = re.compile(
    r"\b(?:crack|cracked|cracks|cracking|smashed|shattered|shattering|broke|broken|damaged|"
    r"scratch|scratches|scratched|chipped|chip|chips|craze|crazed|dented)\b", re.I)

# The other glasses in a house. They are named here rather than in an avoid list for the same
# reason as the spectacles: the word "glass" is in the key, and a line about an oven door must be
# answered by the oven, or by nothing, rather than with a screen protector. A line that names a
# phone word as well is the phone's - "the glass on my phone screen" - so the phone word wins.
_A_PHONE_WORD = re.compile(
    r"\b(?:phone|phones|iphone|iphones|mobile|mobiles|handset|smartphone|android|screen|"
    r"screens|display|protector)\b", re.I)
# What people call a handset, in one place. A row about a phone fault has to know a brand as
# well as the word "phone": "my samsung wont turn on" and "how can i restart my pixel" reached
# nothing at all, and every one of those lines is the same question. Kept to the makes sold in
# numbers here, because a key word is only worth having if people type it.
PHONE_KINDS = ("phone", "iphone", "android", "handset", "smartphone", "mobile",
               "samsung", "galaxy", "pixel", "huawei", "xiaomi", "redmi", "nokia",
               "motorola", "oneplus", "oppo")

_GLASS_IN_SOMETHING_ELSE = re.compile(
    r"\b(?:window|windows|pane|panes|oven|oven door|mirror|mirrors|windscreen|windshield|"
    r"car|fridge|freezer|table|tables|shelf|shelves|bottle|jar|vase|picture frame|shower|"
    r"cooker|hob|microwave|patio door|back door|front door|greenhouse|painting)\b", re.I)


def _the_line(understood):
    """The words of this line as typed, for a guard on the whole reading."""
    if not isinstance(understood, dict):
        return ""
    said = understood.get("clean") or understood.get("text") or understood.get("raw") or ""
    if not said:
        said = " ".join(str(one) for one in understood.get("words") or ())
    return " ".join(str(said).lower().split())


def _not_a_charging_ask(understood):
    """A laptop on the charger is the charging row's question, not the sleep choice.

    `sleep-or-shutdown` keys laptop and overnight, so "is it safe to leave my laptop charging
    overnight" was told when to shut the machine down before the laptop's own row could answer.
    """
    said = _the_line(understood)
    if "charg" not in said:
        return True
    return not re.search(r"\b(?:laptop|macbook|notebook)\b", said)


_A_SCRATCH_IN_THE_LINE = re.compile(
    r"\b(?:scratch|scratches|scratched|scuff|scuffs|scuffed|smudge|smudges|mark|marks|"
    r"hairline)\b", re.I)
_A_BREAK_IN_THE_LINE = re.compile(
    r"\b(?:crack|cracked|cracks|cracking|smashed|shattered|shattering|broke|broken|chip|"
    r"chips|chipped|shatter)\b", re.I)


def _the_glass_in_a_phone(understood):
    """Whether this line is about the glass in a phone.

    False for a pair of spectacles, for a price asked about a phone with no fault in the line,
    for a scratch or a mark with nothing broken in the line (the screen-scratch row is written
    for that, and it is the one that says the polish ruins the glass), and for another glass
    thing in the house that has no phone word in the line with it.
    """
    said = _the_line(understood)
    if _SPECTACLES_IN_THE_LINE.search(said):
        return False
    if _PRICE_ASKED.search(said) and not _A_DAMAGE_IN_THE_LINE.search(said):
        return False
    if _A_SCRATCH_IN_THE_LINE.search(said) and not _A_BREAK_IN_THE_LINE.search(said):
        return False
    if _GLASS_IN_SOMETHING_ELSE.search(said) and not _A_PHONE_WORD.search(said):
        return False
    return True

# Which machine the line itself names. Several of the answers below are a Windows way and a Mac
# way, and "mac" was in no key at all, so a MacBook battery question was answered with a Windows
# command: the steps for the named machine go first, and the other one is mentioned after them.
PLATFORM_MAC = re.compile(r"\b(?:mac|macbook|mac book|macbooks|imac|apple|os x|osx|macos)\b", re.I)
PLATFORM_WINDOWS = re.compile(r"\b(?:windows|pc|surface|chromebook)\b", re.I)


def _platform_named(reading):
    """"mac", "windows" or "" - the machine the line named, if it named one."""
    said = (reading or {}).get("text") or (reading or {}).get("clean") or ""
    said = " ".join(str(said).lower().split())
    if PLATFORM_MAC.search(said):
        return "mac"
    if PLATFORM_WINDOWS.search(said):
        return "windows"
    return ""


# A part of a computer is the computer's part. The fan and the hard drive are the two things in a
# laptop that make a noise, so this row's subject names them - and a bare "fan" is the room fan, a
# desk fan, the one over the hob. "my fan clicks" was answered here with "back the files up first"
# and "stop using it", which is alarming advice about a house fan, and the room fans the row's
# avoid list names ("desk fan", "room fan", "ceiling fan") are only the forms people type in full.
# So the fan is read as this row's only when the line names a computer as well.
COMPUTER_WORDS = re.compile(r"\b(?:laptop|laptops|computer|computers|pc|pcs|macbook|mac book|"
                            r"macbooks|desktop|desktops|hard drive|hard disk|workstation)\b", re.I)
FAN_WORDS = re.compile(r"\b(?:fan|fans)\b", re.I)


def _a_fan_is_the_computers(reading):
    """True when a fan the line names is a computer's, the only fan this row can answer for."""
    said = (reading or {}).get("text") or (reading or {}).get("clean") or ""
    said = " ".join(str(said).lower().split())
    if not FAN_WORDS.search(said):
        return True
    return bool(COMPUTER_WORDS.search(said))


def _mac_first(mac_steps, windows_steps, reading):
    """The steps for the machine the line named first, the other one after them."""
    if _platform_named(reading) == "mac":
        return mac_steps + " " + windows_steps
    return windows_steps + " " + mac_steps

# The battery-health report, in the two ways it is done: a Mac has its own panel, a Windows machine
# has a command. Which one comes first is read from the line, because getting the other machine's
# way first is worse than useless: it is a command that machine does not have.
BATTERY_HEALTH_MAC = ("On a Mac, hold Option and click the Apple menu > System Information > Power: "
                      "the cycle count and the full charge capacity sit beside the design capacity, "
                      "and under about 70% is a worn battery.")
BATTERY_HEALTH_WINDOWS = ("On Windows, open Command Prompt and run `powercfg /batteryreport` - the "
                          "report gives the design capacity and what it holds now, and under about "
                          "70% is a worn battery.")
BATTERY_HEALTH_TAIL = (" A laptop battery is usually \u00a340 to \u00a390 and most are held in with "
                       "screws, so it is worth replacing rather than buying a new machine.")


def _wifi_drops(memory, reading):
    """The wifi answer only for a line that names the wifi.

    Two words of this key are enough for `lookup.score`, and the phone word is already the
    gate, so "my phone loses charge really quickly" matched on "phone" and "loses" alone and
    was told to forget the network: the charge answer that line wants lost the tie. The wifi
    word is the other half of the question, so the answer asks for it here.
    """
    said = str((reading or {}).get("clean") or "").lower()
    if not any(word in said for word in ("wifi", "wi-fi", "wi fi", "wireless", "wlan",
                                        "network", "connection", "connect", "internet", "online",
                                        "data", "signal")):
        return None
    return (
        "Forget the network on the phone and rejoin it with the password typed fresh, since a "
        "saved network that half-connects is the commonest cause; then restart the phone and the "
        "router once. If the wifi drops when the screen is off, turn off the battery saving that "
        "sleeps wifi (on Android, Settings > Battery > Battery saver; on an iPhone, Low Power "
        "Mode), and set the wifi to stay on during sleep. A phone that drops only in one room is "
        "a coverage problem, not a phone problem.")


def _battery_health(memory, reading):
    """The battery-health check for the machine the line names, that machine's way first."""
    return _mac_first(BATTERY_HEALTH_MAC, BATTERY_HEALTH_WINDOWS, reading) + BATTERY_HEALTH_TAIL


def _empty_trash(memory, reading):
    """Emptying the bin, on the machine the line named."""
    mac = ("On a Mac, open the Bin from the Dock and press Empty in the top right, or press "
           "Command-Shift-Delete to do it from the keyboard; holding Option while you press Empty "
           "skips the question. Nothing is freed until the Bin is emptied, so a full disk is "
           "often just this.")
    windows = ("On Windows, right-click the Recycle Bin on the desktop and choose Empty Recycle "
               "Bin, or open it and press Empty Recycle Bin at the top; the files are only really "
               "gone once you do, so a full disk is often just this.")
    return _mac_first(mac, windows, reading)


def _force_quit(memory, reading):
    """Closing one stuck app, on the machine the line named."""
    mac = ("On a Mac press Command-Option-Esc, pick the app in the list and press Force Quit: that "
           "closes the one app and leaves everything else open, and if the whole Mac is stuck, "
           "hold the power button for ten seconds instead.")
    windows = ("On Windows press Ctrl-Shift-Esc for Task Manager, pick the app and choose End task: "
               "that closes the one app and leaves everything else open, and if the whole machine "
               "is stuck, hold the power button for ten seconds instead.")
    return _mac_first(mac, windows, reading)


def _default_browser(memory, reading):
    """Setting the browser that opens links, on the machine the line named."""
    mac = ("On a Mac, open System Settings > Desktop & Dock and scroll to Default web browser "
           "near the bottom (on older macOS it is Safari > Preferences > General > Default web "
           "browser). Pick the one you want from the menu and every link opens there from then on.")
    windows = ("On Windows, open Settings > Apps > Default apps, type the browser's name in the "
               "search box and choose Set default; that sends links, .html files and mail links "
               "to it.")
    return _mac_first(mac, windows, reading)


UNINSTALL_PROGRAM_MAC = ("On a Mac, open Finder > Applications, drag the app to the Bin and empty "
                         "it - some leave a folder in Library, which is harmless to leave.")
UNINSTALL_PROGRAM_WINDOWS = ("Windows: Settings > Apps > Installed apps, find it in the list and "
                             "choose Uninstall.")
UNINSTALL_PROGRAM_TAIL = (" A program that will not go usually has its own uninstall entry, under "
                          "its maker's name, in the Start menu.")


def _uninstall_program(memory, reading):
    """Uninstalling software, for the machine the line names."""
    return _mac_first(UNINSTALL_PROGRAM_MAC, UNINSTALL_PROGRAM_WINDOWS,
                      reading) + UNINSTALL_PROGRAM_TAIL


UNINSTALL_APP_MAC = ("On a Mac, open Finder > Applications and drag the app to the Bin, then empty "
                     "it - an App Store app can also go from Launchpad: hold it until the icons "
                     "wobble and press the cross.")
UNINSTALL_APP_WINDOWS = ("On Windows, open Settings > Apps > Installed apps, find it in the list "
                         "and choose Uninstall - or right-click it in the Start menu and pick "
                         "Uninstall.")
UNINSTALL_APP_PHONE = ("On an iPhone, hold the app icon and choose Remove App > Delete App; on "
                       "Android, hold it and tap Uninstall, or go Settings > Apps and pick it.")
UNINSTALL_APP_TAIL = (" That frees the storage and keeps your photos; a game that lives online "
                      "keeps your progress on its own account, so sign back in if you install it "
                      "again.")


def _uninstall_app(memory, reading):
    """Deleting an app on the machine the line names: a Mac and a PC are not phones."""
    named = _platform_named(reading)
    if named == "mac":
        return UNINSTALL_APP_MAC + UNINSTALL_APP_TAIL
    if named == "windows":
        return UNINSTALL_APP_WINDOWS + UNINSTALL_APP_TAIL
    return UNINSTALL_APP_PHONE + UNINSTALL_APP_TAIL


SOCIAL_DELETE = {
    "facebook": ("On Facebook it is Settings > Account ownership and control > Deactivation and "
                 "deletion, or the menu under your profile picture on a computer. Deactivating is "
                 "reversible and keeps your data, deleting is not, and there is a 30-day window to "
                 "change your mind."),
    "instagram": ("On Instagram it is Settings > Accounts Centre > Personal details > Account "
                  "ownership and control > Delete account, and it will ask why. Deactivating is "
                  "reversible and keeps your photos; deleting is not, and there is a 30-day window "
                  "to change your mind."),
    "tiktok": ("On TikTok it is Profile > the three lines > Settings and privacy > Account > "
               "Deactivate or delete account. Deactivating is reversible; deleting is not, and "
               "there is a 30-day window to change your mind."),
    "snapchat": ("On Snapchat it is Settings > Account Actions > Delete Account, and it asks for "
                 "your password. There is a 30-day window to log back in and cancel it."),
    "twitter": ("On X it is Settings > Your account > Deactivate your account. It is reversible "
                "for 30 days, then the account is permanently deleted."),
}


# A shop, a bank app or a cloud service closes an account on its own website, and each one hides
# the button somewhere different. These are the ones people ask for by name; anything else falls
# back to the settings-line reply below.
SERVICE_ACCOUNTS = {
    "amazon": ("On Amazon scroll to the bottom of Account & Lists > Your Account and use Close "
               "Your Amazon Account, which asks you to confirm by email. Orders and gift card "
               "balances go with it, so spend or download anything you have paid for first."),
    "ebay": ("On eBay it is Account > Close account, at the bottom of the account settings page, "
             "and it will not let you close while you have a live listing, an unpaid fee or an "
             "open case. Withdraw any money in your eBay balance first, or it is kept."),
    "paypal": ("On PayPal it is Settings > Account > Close your account, and it only lets you "
               "when the balance is zero, so move any money to your bank first. A limitation or "
               "an open dispute blocks it until that is settled."),
    "google": ("On Google it is myaccount.google.com > Data & privacy > Delete a Google service "
               "to drop just Gmail or YouTube, or Delete your account for the lot. Download what "
               "you want first with takeout.google.com, and check the address is not the recovery "
               "email for other logins."),
    "apple": ("On Apple it is privacy.apple.com > Delete your account, which needs to be done from "
              "a device signed in to the same Apple ID. Cancel any subscriptions and spend any "
              "credit first, because a deleted account cannot be restored."),
    "microsoft": ("On Microsoft it is account.microsoft.com > Close your account, and any unused "
                  "credit is lost, so use it first. Cancel Microsoft 365 and any Xbox "
                  "subscriptions beforehand, or they keep trying to charge a card."),
    "netflix": ("On Netflix the button is Cancel Membership on the account page, or "
                "netflix.com/cancelplan, and the account stays usable until the end of the month "
                "you have paid for. Download anything from the downloads list before then."),
    "spotify": ("On Spotify it is the account page > Close account at the bottom, and the free "
                "tier goes with it. Cancel any Premium plan first, or the payment keeps going "
                "while the account still opens."),
    "icloud": ("On iCloud an Apple ID is the account: delete it at privacy.apple.com and the "
               "mail, photos and backups go too. Download a copy of your data first with "
               "privacy.apple.com > Get a copy of your data."),
    "dropbox": ("On Dropbox it is Settings > Account > Delete account, and shared folders you own "
                "are deleted for everyone in them, so hand ownership over first. Download your "
                "files before you do."),
}

SERVICE_ACCOUNT_NAMES = tuple(SERVICE_ACCOUNTS) + (
    "prime", "prime video", "disney+", "disney plus", "now tv", "audible", "adobe", "office 365",
    "microsoft 365", "google one", "kindle", "youtube", "gmail", "outlook", "hotmail")


def _service_delete_reply(memory, understood):
    """Which service is being closed decides the page; the rest is one shape of advice."""
    said = (understood.get("clean") or understood.get("text") or "").lower()
    for name, line in SERVICE_ACCOUNTS.items():
        if name in said:
            return line
    return ("Close it from the service's own website in a browser rather than from the app: the "
            "button is usually the last item in your account or profile settings, called Delete or "
            "Close account. Spend or download anything you have paid for first - credit and files "
            "are lost - and shut down any subscription on the same account, or it keeps billing.")


def _social_delete_reply(memory, understood):
    """Which account is being deleted decides which settings path to give."""
    said = (understood.get("clean") or understood.get("text") or "").lower()
    for name, line in SOCIAL_DELETE.items():
        if name in said:
            return line
    return ("Do it in the app, not by deleting the icon: every app hides it under Settings > "
            "Account, usually as Deactivate (reversible) or Delete (permanent). Deactivating keeps "
            "your posts and your name; deleting does not, and most apps give you 30 days to log "
            "back in and change your mind.")


_SYMBOLS = (
    (("pound", "£", "sterling"), "£ is Shift and 3"),
    (("euro", "€"), "€ is AltGr and 4, or Ctrl and Alt and 4 where there is no AltGr key"),
    (("dollar", "$"), "$ is Shift and 4"),
    (("at sign", "at symbol", "@", "email sign"), "@ is Shift and 2"),
    (("hash", "#"), "# is the key next to Enter, on the third row up - Shift and 3 gives # on a "
                   "keyboard set to the US layout"),
    (("backslash", "\\"), "the backslash is the key directly above Enter, and Shift and that key "
                            "gives the pipe |"),
    (("forward slash", "slash", "/"), "/ is the key next to the right Shift"),
    (("underscore", "_"), "_ is Shift and the minus key"),
    (("tilde", "~"), "~ is Shift and the key left of the 1, or Option and N then space on a Mac"),
    (("degree", "°"), "there is no degree key: hold Alt and type 0176 on Windows, or Option and "
                      "Shift and 8 on a Mac"),
    (("asterisk", "star sign", "*"), "* is Shift and 8"),
    (("pipe", "|"), "| is Shift and the backslash key, above Enter"),
)


METER_READING = ("The in-home display shows what you are using now and what it has cost "
                 "today; the meter itself is the box where the supply enters, and your "
                 "supplier's app shows the same readings. A display that has gone blank is "
                 "usually the little power lead or the distance from the meter - move it closer "
                 "and leave it plugged in.")

METER_TOP_UP = ("Top up in your supplier's app, on their website or at a PayPoint shop, and the "
                "credit lands on the meter within minutes - keep the receipt until it shows. On "
                "an old key or card meter you take the key to the shop and put it back in the "
                "meter afterwards, and the in-home display then shows the new balance.")


# Putting the card in and a card that has stopped being seen are one job, asked two ways: the
# how-to wants the tray and the way round the card goes, the fault wants the contacts and the
# network record. The line says which, so the row answers both instead of shrugging at "how do i
# put a sim card in my phone".
_SIM_HOW_TO = re.compile(
    r"\b(?:put|puts|putting|insert|inserting|change|changing|swap|swapping|replace|replacing|"
    r"move|moving|fit|fitting|take|taking|remove|removing)\b", re.I)
_SIM_FAULT = re.compile(
    r"\b(?:no sim|not (?:found|recognised|recognized|detected|working|reading|seen)|says no|"
    r"error|missing|keeps saying|cannot see|doesnt see|does not see|went|stopped)\b", re.I)
_SIM_HOW_TO_REPLY = (
    "Power the phone off first, then push a paperclip or the pin that came with it into the "
    "pinhole beside the tray until it clicks and the tray slides out. The card sits in the "
    "outline with its cut corner matching the diagram on the tray, gold contacts down, and it "
    "only fits one way, so do not force it: an adapter that is too thin is the usual reason a "
    "card will not seat, and a strip of tape on the back of it fixes that. Slide the tray in "
    "flat until it is flush, then switch on and wait a minute; if it still asks for a SIM, check "
    "in Settings > Mobile Data that the plan is switched on there.")
_SIM_FAULT_REPLY = (
    "Power the phone right off, then open the SIM tray with a paperclip, take the card out "
    "and wipe the gold contacts with a dry cloth before putting it back the same way round - "
    "a card that has worked for months has usually just shifted. If the phone takes an eSIM, "
    "check in Settings > Mobile Data that the plan has not been deleted. After that, look for "
    "a carrier settings update and then Settings > General > Transfer or Reset > Reset > "
    "Reset Network Settings, which clears the network record without touching your data; a "
    "phone that still says no SIM after that has a failed tray or reader, and the network's "
    "shop will test it with their own card in a minute.")


def _sim_reply(memory, understood):
    line = str(understood.get("text") or understood.get("clean") or "")
    if _SIM_FAULT.search(line):
        return _SIM_FAULT_REPLY
    if _SIM_HOW_TO.search(line):
        return _SIM_HOW_TO_REPLY
    return _SIM_FAULT_REPLY


# A box that is full is a storage question and a box full of junk is the spam question, and
# "inbox" plus "full" answered both the same way: "my email inbox is full" got the report-it-as-
# junk card. The junk word in the line is what tells them apart.
_JUNK_SAID = re.compile(
    r"\b(?:spam|junk|unwanted|nuisance|marketing|newsletter|newsletters|phishing|scam|scams|"
    r"adverts?|advertising|cold emails?|rubbish)\b", re.I)
_A_FULL_BOX = re.compile(
    r"\b(?:inbox|mailbox|mail box|email|emails|mail)\b[^.|]{0,24}\bfull\b", re.I)


def _junk_or_a_full_box(understood):
    """The spam row answers a box full of junk; a box that is merely full belongs to storage."""
    line = str(understood.get("text") or understood.get("clean") or "")
    if _A_FULL_BOX.search(line):
        return bool(_JUNK_SAID.search(line))
    return True


def _meter_reply(memory, understood):
    """The smart meter answer the line asked for: a top-up, or a reading and a blank display."""
    said = ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(word in said for word in ("top up", "topping up", "topup", "credit", "prepayment",
                                     "prepayment meter", "key meter", "emergency credit")):
        return METER_TOP_UP
    return METER_READING
WIFI_STICKER = ("It is printed on a sticker on the back or underneath the router, unless someone "
               "changed it. A phone that has joined the wifi can show it too: on an iPhone tap the "
               "i beside the network in Settings > Wifi, and on Android it is in the network's Share "
               "menu.")

WIFI_CHANGE = ("Log in to the router - the address, a username and a password are on the sticker on "
               "the back, usually 192.168.0.1 or 192.168.1.1 - then open Wireless or Wifi settings, "
               "type the new password and save. Every device drops off and needs the new one, so do "
               "it when that is not a problem, and write it on the sticker.")

# "how do i reset my router password" is the password question with the wrong verb: a router is
# not reset with a password, so it is the admin password that has been changed and forgotten, and
# the only way back is the pinhole - which also wipes the wifi name and password. Answering it
# with the reboot was the same wrong subject as answering a factory reset with one.
WIFI_RESET = ("If the password on the sticker does not get you into the router, someone changed it: "
              "the way back is the reset hole - with the router on, push a paperclip into the hole "
              "marked Reset for 10 to 30 seconds until the lights blink, and it goes back to the "
              "sticker's password. That also wipes the wifi name and password you set, so every "
              "device needs joining again. Change the admin password on the way back in and write "
              "it on the sticker.")


# A factory reset is not a reboot, and this was answering both. Unplugging a router clears a
# dropout; it does not put the settings back, so "how do i factory reset my router" was told to
# unplug it for 30 seconds, and nobody got their wifi name and password back.
ROUTER_FACTORY = (
    "Use the reset hole, not the plug: with the router on, push a paperclip or a pin into the "
    "small hole marked Reset (or hold the Reset button) for 10 to 30 seconds, until the lights "
    "blink or the router restarts, and it goes back to the factory settings on the sticker - "
    "including the wifi name and password, so every device needs joining again. Unplugging it for "
    "30 seconds is only a reboot and keeps your settings, so try that first if it is just dropping "
    "out. Some provider routers reset from their app instead (Sky, BT and Virgin all have a button "
    "in the app), and a router they gave you may come back with the settings it shipped with.")


_ROUTER_WHERE = ("Up high, out in the open and as close to the middle of the flat as the cable "
                 "allows - on a shelf or the top of a bookcase, not on the floor, in a cupboard, "
                 "behind the TV or beside the microwave, a cordless phone or the hot water tank. "
                 "Radio waves spread out sideways and downwards from the box, so one in a corner "
                 "mostly covers the corner. The line comes in where it comes in: if that is one "
                 "end, keep the router there and add a mesh unit at the other end rather than "
                 "running a long cable.")


def _router_place(memory, understood):
    """Where the router goes, with the verdict first when the line asks whether to move it.

    "Where should i put my router" wants the place in the first sentence. "Should i move the
    router" is a yes or no, and answering it with a place leaves the person to work out whether
    that means yes - so the line that asks whether gets the yes with its condition, and the
    place still follows.
    """
    reading = understood if isinstance(understood, dict) else {}
    said = " " + " ".join(str(word).lower() for word in (reading.get("words") or [])) + " "
    if " where " not in said and (" move " in said or " moving " in said):
        return ("Yes, if it is in a cupboard, behind the TV, on the floor or at the far end of "
                "the flat, and it is worth the five minutes. " + _ROUTER_WHERE)
    return _ROUTER_WHERE


# A "booster" is a jab far more often than it is a wifi part: with "get" in the row's ask group
# it took "should i get a covid booster", and with no wifi word in it a bare "would a booster
# help" means the repeater only because the line before was about the wifi. So the row reads the
# line, then the line it follows, for the thing it is about.
_WIFI_WORD = re.compile(
    r"\b(wifi|wi fi|wireless|router|broadband|internet|signal|reception|coverage|network|"
    r"mesh|extender|repeater|hotspot|ethernet|dead spot|stream)\w*")


def _wifi_is_what_it_is_about(understood):
    """A wifi part has a wifi word in the line, or in the line it follows."""
    line = " ".join(str(word) for word in ((understood or {}).get("words") or ()))
    if _WIFI_WORD.search(line):
        return True
    lean = (understood or {}).get("leans_on") or {}
    return bool(_WIFI_WORD.search(" ".join(str(word) for word in lean.get("words") or ())))



def _wifi_password_reply(memory, understood):
    """Finding the wifi password, changing it, and getting back in are three different jobs."""
    said = ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(word in said for word in ("change", "changed", "new password", "different",
                                     "someone knows", "hacked", "forgot how")):
        return WIFI_CHANGE
    return WIFI_STICKER


# "i cant log in to my router" is the same answer as the reset hole, said in the shape of a
# statement rather than a how-to. The composer hands a statement the sentence of the answer that
# carries the move, and on a long how-to that sentence is a fragment out of context ("Change the
# admin password on the way back in ..." with nothing before it), so the statement gets its own
# short reply that stands on its own.
WIFI_LOCKED_SHORT = (
    "Then it is the reset hole: with the router on, push a paperclip into the hole marked Reset "
    "for 10 to 30 seconds and it comes back with the password on the sticker. That wipes the wifi "
    "name and password too, so every device needs joining again.")


# The second half of a factory reset is what it takes with it: "will that wipe my wifi name",
# "does it delete everything", "what do i lose". Said again as the whole how-to, the person reads
# the paragraph they just read; the wipe is the answer to the question they actually asked.
ROUTER_WIPED = (
    "Yes - it goes back to the settings it shipped with, so the wifi name and password become the "
    "ones on the sticker, the admin password becomes the sticker's again, and anything you set "
    "yourself goes: port forwards, a fixed address for a printer, a changed DNS, parental rules. "
    "Every device drops off and needs joining to the sticker's name, so note anything you set up "
    "before you do it.")
_WIPE_ASKS = ("wipe", "wipes", "lose", "losing", "loses", "delete", "deletes", "erase",
              "erases", "take away", "takes away", "what goes", "every setting", "my settings",
              "the name", "wifi name", "network name", "everything")


def _router_factory_reply(memory, understood):
    """The reset how-to, or what the reset costs when that is what is asked."""
    said = ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(word in said for word in _WIPE_ASKS):
        return ROUTER_WIPED
    return ROUTER_FACTORY


def _admin_locked_reply(memory, understood):
    """The reset hole in full for a how-to, and the short of it for a statement."""
    if (understood or {}).get("kind") == "question":
        return WIFI_RESET
    return WIFI_LOCKED_SHORT


# A dark theme is one setting on four different devices, and the reply has to start with the
# one the person is holding: "how do i turn on dark mode on my laptop" was given the iPhone
# steps first (polite-ruler at e3872430).
_DESKTOP_WORDS = ("laptop", "pc", "computer", "desktop", "windows", "chromebook", "notebook")
_MAC_WORDS = ("mac", "macbook", "imac", "mac os", "macos")
_DARK_MODE_PHONE = (
    "On an iPhone it is Settings > Display & Brightness > Dark, and Android has it under "
    "Settings > Display; both can switch themselves on at sunset under Options or Schedule. "
    "There is a Dark reader for websites too, in Safari's page menu or Chrome's Settings > "
    "Appearance.")


# The adding answer: how a card gets into the phone in the first place.
_ADD_TO_WALLET = (
    "In the bank's own app there is usually an 'Add to Apple Pay' or 'Add to Google Pay' button on "
    "the card, and it is the quickest way; otherwise open Wallet on the phone and add the card "
    "number by hand or with the camera. The bank then sends a code, and some cards need one "
    "contactless payment with the PIN before the phone version works.")


# A card that is on the phone and will not tap is the same row as adding one, and the answer is
# not the adding: the wallet is set up and the payment is failing. The line says "wont tap" and
# nothing else in the domain keys it, so on main it fell to the plumber's "spot it in minutes".
# The understanding normalises a contraction before any module sees it ("wont" arrives as "will
# not") and it strips a clause boundary to a bar, so the lack of a tap is matched on both shapes:
# the words as the person typed them and the words after the rewrite.
_TAP_PROBLEM = ("wont tap", "won't tap", "doesnt tap", "doesn't tap", "not tapping", "no tap",
                "will not tap", "does not tap", "will not work", "does not work", "not working",
                "fails", "failed", "declined", "declines", "rejected", "refused", "wont pay",
                "won't pay", "cant pay", "can't pay", "cannot pay", "can not pay", "not accepted",
                "is not accepted", "keeps failing", "no longer taps",
                # "the shop wont accept my card" is the same refusal as "my card is not
                # accepted", and without these it got the add-it-to-the-wallet answer
                "wont accept", "won't accept", "doesnt accept", "doesn't accept",
                "will not accept", "said no", "says no")
_TAP_REPLY = (
    "Nine times in ten it is the phone, not the card: the screen has to be on and unlocked, NFC "
    "(contactless) has to be switched on, and the card has to be the one set as default in "
    "Wallet - check all three and try the back of the phone flat on the reader, not the edge. If "
    "it still refuses, take the phone out of its case, and try a second till or a shop you have "
    "used before, because one terminal can be the fault. When the phone taps nowhere at all, the "
    "card itself still works: use the plastic, then remove the card in the bank app and add it "
    "again, which reissues the token - and if the app says the card is blocked, ring the bank, "
    "because a block is on the card and no amount of tapping clears it.")


# A card that cannot be paid is a debt, not a wallet: "i cant pay my credit card" and "my credit
# card is due next week and i cant pay" were both told to check the screen was unlocked and that
# NFC was on, because this row keys "card" and "pay" and reads "cant pay" as the tapped card
# failing. The wallet is the answer only when the line names it - the phone, the till, the reader -
# or when nothing in the line is about money owed. A bare "my card wont work" keeps the tap answer,
# because there the guess is the right one.
DEBT_SHAPE = ("cant pay", "can't pay", "cannot pay", "can not pay", "unable to pay", "not paid",
              # a refusal to pay is a debt too, and it was read as a card that would not tap:
              # "my ex partner wont pay the mortgage" and "my tenant wont pay rent" both got the
              # Wallet card. The wallet is named by the phone, the till or the reader, and a
              # mortgage, a rent or a tenant in the line means money owed.
              "wont pay", "won't pay", "will not pay", "stopped paying", "has not paid",
              "hasnt paid", "hasn't paid", "mortgage", "rent", "rents", "tenant", "tenants",
              "landlord", "arrears",
              "cant afford", "can't afford", "couldnt afford", "couldn't afford", "owe", "owes",
              "owed", "overdraft", "bill", "bills", "due", "payment", "payments", "balance",
              "arrears", "behind on", "missed a payment", "miss a payment", "minimum",
              # "i forgot to pay my credit card" and "what happens if i pay my credit card late"
              # have no money-owed word the guard knew, so the wallet answered a debt question.
              "forgot", "forgotten", "forget", "forgetting", "forgot to pay", "forget to pay",
              "keep forgetting", "late payment", "paid late", "pay late",
              "paying late", "payment is late", "missing a payment", "missed payment",
              # "what happens if i pay my credit card late" puts a word between "pay" and "late"
              # and the wallet took it; the phrase list cannot see across that, so the bare word
              # is here too. A card that will not tap at a till is not described as late.
              "late",
              "didnt pay", "didn't pay", "not paid", "unpaid", "overdue", "due date")
WALLET_NAMED = ("phone", "mobile", "wallet", "apple pay", "google pay", "contactless", "tap",
                "shop", "till", "card machine", "terminal", "reader", "checkout", "self service",
                "nfc", "screen", "app")


# The screens and the documents the zoom/size card is about. It is a whitelist on purpose: its
# second group was the asking words, and "how do i" is one of them, so a line with no screen in it
# at all still scored - "how do i stretch shoes that are too small" was told Ctrl and + makes it
# bigger, and that answer is certainly wrong. A word this list does not know costs a hedge, which
# is honest, where the wrong card is not.
SCREEN_NAMED = (
    "text", "texts", "font", "fonts", "writing", "letters", "zoom", "magnify", "magnified",
    "magnifier", "screen", "screens", "browser", "page", "pages", "website", "websites",
    "document", "documents", "word", "excel", "powerpoint", "laptop", "laptops", "computer",
    "computers", "desktop", "mac", "macbook", "windows", "phone", "phones", "iphone", "android",
    "ipad", "tablet", "kindle", "app", "apps", "settings", "display", "cursor", "mouse",
    "read", "reading", "tv", "television", "spreadsheet", "email",
)
_SCREEN_NAMED_RE = re.compile(r"\b(?:%s)\b" % "|".join(SCREEN_NAMED), re.I)


def _a_screen_is_named(understood):
    """True when the line names a screen, a page or a device the size card can be about."""
    understood = understood or {}
    said = " ".join(str(understood.get(key) or "")
                    for key in ("text", "norm_text", "clean", "raw"))
    return bool(_SCREEN_NAMED_RE.search(said))


# A job application, a course application and an application form are papers to fill in, not an
# app on a phone: "im stuck with my job application" was answered "Force the app closed and open
# it again", because "application" and "stuck" are two key words of the app row.
_A_PAPER_APPLICATION = re.compile(
    r"\b(?:job|course|college|uni|university|school|visa|grant|funding|rental|tenancy|"
    r"membership|passport|licen[cs]e|travel)\s+applications?\b"
    r"|\bapplications?\s+(?:form|forms|essay|letter|deadline|question)\b", re.I)


# ... unless the line puts it on a device: "the application form wont open on my phone" is a
# thing that will not open, and the app row's steps are the nearest help there is.
_ON_A_DEVICE = re.compile(r"\b(?:phone|iphone|android|app|apps|tablet|ipad|laptop|computer|"
                          r"screen|browser|website|site|download|open|opens|opening)\b", re.I)


def _an_app_not_a_paper(understood):
    """False when the application the line names is one somebody fills in."""
    understood = understood or {}
    said = " ".join(str(understood.get(key) or "")
                    for key in ("text", "norm_text", "clean", "raw"))
    if not _A_PAPER_APPLICATION.search(said):
        return True
    return bool(_ON_A_DEVICE.search(said))


# "how do i stop my cable fraying" is the care question, not the fault one: the answer there is to
# pull the plug out by the plug and stop wrapping the cable tight, and the stop-and-replace card
# threw that away. The forms tell them apart. A prevention verb with only the "-ing" or plain form
# of the damage ("stop my cable fraying", "stop my cable from fraying") is looking forward, while
# "frayed", "split", "exposed", "showing", "tape" or "still use" name a cable that is damaged
# already, so "my cable is frayed, how do i stop it getting worse" keeps the card.
CABLE_PREVENT_ASK = re.compile(
    r"\b(?:stop|stops|prevent|prevents|avoid|avoids)\b[^.?!]{0,40}?"
    r"\b(?:fraying|splitting|wearing)\b", re.I)
CABLE_DAMAGE_NOW = re.compile(
    r"\b(?:frayed|fraying?\s+wire|split|splits|splitting|exposed|bare|showing|shows|nicked|"
    r"worn|wearing\s+through|tape|taped|still\s+use|still\s+safe|shock|spark|burnt|burned|"
    r"smell|hot)\b", re.I)


def _cable_fault_not_the_care_question(understood):
    """True unless the line asks how to stop a cable fraying, which the care answer owns."""
    understood = understood or {}
    said = " ".join(str(understood.get(key) or "")
                    for key in ("text", "norm_text", "clean", "raw"))
    if not CABLE_PREVENT_ASK.search(said):
        return True
    return bool(CABLE_DAMAGE_NOW.search(said))
# The block-number card below is a screen on a phone, so the line has to be about the phone for it
# to be the answer. "how do i stop someone snoring" and "how do i stop someone smoking" name a
# person and a habit and nothing else, and they were answered "open the call or message, tap the
# name or number, then Block this Caller" off the bare "stop someone" key, because "someone" is
# also one of the row's second-group words. A line that names the phone or the block verb keeps
# the card; a line that only names the person and what they do goes where it belongs.
_A_PHONE_IN_THE_LINE = re.compile(
    r"\b(?:phone|phones|phoned|phoning|mobile|mobiles|call|calls|called|calling|ring|rings|"
    r"ringing|rang|text|texts|texted|texting|message|messages|messaging|number|numbers|"
    r"caller|callers|sim|sims|landline|voicemail|facetime|contact|contacts|"
    r"block|blocked|blocking|unblock|unblocked|unblocking|blocklist|"
    r"nuisance|withheld|telemarketer|telemarketers|scam|spam)\b")


def _the_block_is_the_phones(understood):
    """True when the line is about the phone's own block list, not about a person's habit."""
    understood = understood or {}
    said = " " + " ".join(str(understood.get(key) or "").lower()
                          for key in ("text", "norm_text", "clean", "raw")) + " "
    return bool(_A_PHONE_IN_THE_LINE.search(said))


def _a_wallet_is_named(understood):
    """False when the line is about money owed, so the tap answer stands down and the debt's row
    answers it instead."""
    understood = understood or {}
    said = " " + " ".join(str(understood.get(key) or "").lower()
                          for key in ("text", "norm_text", "clean", "raw")) + " "
    if any(" " + word in said for word in WALLET_NAMED):
        return True
    return not any(" " + word in said for word in DEBT_SHAPE)


def _card_on_a_phone(memory, understood):
    said = " ".join(str(understood.get(key) or "").lower()
                    for key in ("text", "norm_text", "clean"))
    if any(phrase in said for phrase in _TAP_PROBLEM):
        return _TAP_REPLY
    return _ADD_TO_WALLET


def _dark_mode_reply(memory, understood):
    line = (understood.get("clean") or understood.get("text") or "").lower()
    words = set(line.replace("?", " ").replace(",", " ").split())
    if words & set(_MAC_WORDS) or "macbook" in line:
        return ("On a Mac it is System Settings > Appearance > Dark, and System Settings > "
                "Displays has Night Shift for the warmer evening light. Safari follows the "
                "system, and most websites switch too, so nothing else needs setting.")
    if any(w in words for w in _DESKTOP_WORDS) or "laptop" in line:
        return ("On Windows 11 it is Settings > Personalisation > Colours and pick Dark under "
                "'Choose your mode'; Windows 10 has the same page under Settings > "
                "Personalisation > Colours. Switch on Night light there as well if the screen is "
                "the bright thing in the room at night.")
    return _DARK_MODE_PHONE


# A phone for a child is two questions, and only one of them is about age. "my daughter is 12 and
# wants a phone" and "how much should i spend on a phone for my 12 year old" were both answered by
# the screen-time card in family.py ("under two, video calls and the odd photo only"), because that
# card keys on phone + "year old" + "how much" and this one's ask list had no buying word on it: a
# parent asking what to pay for the handset got a limit on the toddler's tablet.
FIRST_PHONE_SPEND = re.compile(
    r"\b(?:spend|spending|afford|budget|price|prices|cheap|cheaper|cheapest|second hand|"
    r"secondhand|hand me down|hand me downs|sim only|pay as you go|buy|buying|bought|"
    r"which phone|what phone|wants a phone|wants one|wants a mobile|want a phone|"
    r"asking for a phone|how much|what does it cost)\b")

FIRST_PHONE_BUYING = ("Spend £100 to £200 on a used handset or a hand-me-down and a cover, "
                     "then a SIM-only deal at £6 to £10 a month in your name rather than a "
                     "contract: the price is not what makes it safe, and two years of contract on "
                     "a phone a child will probably lose is the expensive mistake. Set it up "
                     "before you hand it over - Family Link on an Android or Screen Time on an "
                     "iPhone for limits and app approvals, in-app purchases off, and one agreed "
                     "place it sleeps at night.")

FIRST_PHONE_AGE = ("Most parents wait until about 11 or 12, when a child is travelling to school "
                   "without you, and start with a cheaper handset on pay-as-you-go rather than "
                   "the newest iPhone. Set it up before you hand it over: Screen Time or Family "
                   "Link for a time limit and app approvals, turn off in-app purchases, and agree "
                   "where the phone sleeps.")


# "i cant afford a phone for my daughter" got "spend GBP 100 to GBP 200": the figure was right and
# the answer was not. A tight budget is its own reply, because the cheapest honest route is a
# refurbished handset or a hand-me-down rather than a smaller version of the same plan.
FIRST_PHONE_TIGHT = re.compile(r"\b(?:cant afford|can't afford|cannot afford|couldnt afford|"
                               r"couldn't afford|skint|no money|made redundant|money is tight|"
                               r"really cheap|as cheap as|cheapest possible)\b")

FIRST_PHONE_BUDGET = ("A refurbished handset from the maker's own store, or a used one from a "
                     "shop like CeX, is £60 to £120 with a guarantee, and a hand-me-down "
                     "from family is free: what matters is that it runs the apps the school uses "
                     "and still gets security updates, not that it is new. Pair it with a "
                     "SIM-only deal at £6 to £10 a month in your name, turn off in-app "
                     "purchases, and say plainly that this is the phone for now rather than the "
                     "phone they asked for.")


# A limit on the hours is not a price. "how much time should my daughter spend on her phone"
# matched the spend word in this key and got the £100-to-£200 answer, so the time words stand this
# entry down and leave the line to the screen-time card that answers it.
FIRST_PHONE_TIME = re.compile(r"\b(?:time|times|hours|hour|minutes|how long|screen|screens|"
                              r"usage|limits|daily|a day|per day|each day|on his phone|"
                              r"on her phone|on their phone)\b")


def _first_phone(memory, understood):
    """The money for a first phone, and the age if that is what was asked."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if FIRST_PHONE_TIME.search(said):
        return ""
    if FIRST_PHONE_TIGHT.search(said):
        return FIRST_PHONE_BUDGET
    if FIRST_PHONE_SPEND.search(said):
        return FIRST_PHONE_BUYING
    return FIRST_PHONE_AGE


def _symbol_on_the_keyboard(memory, understood):
    """The line of the answer for the symbol the person actually asked about."""
    said = (understood or {}).get("clean") or (understood or {}).get("text") or ""
    said = said.lower()
    for names, line in _SYMBOLS:
        if any(name in said for name in names):
            break
    else:
        return None  # a symbol this does not know: leave the line to a lower entry
    return ("On a UK keyboard " + line + ". If a symbol comes out as a different one, the "
            "keyboard is set to the US layout: Settings > Time & language > Language on Windows, "
            "System Settings > Keyboard > Input Sources on a Mac.")


def _to_the_tv(memory, understood):
    """A laptop to a TV is a cable; a phone is a cast. Which one was named decides the answer."""
    clean = (understood.get("clean") or "").lower()
    phone = any(word in clean for word in ("phone", "iphone", "android", "tablet", "ipad"))
    if phone:
        return ("Cast it rather than cable it: put the phone and the TV on the same wifi, open the "
                "app (YouTube, iPlayer, Netflix) and tap the Cast or AirPlay icon at the top of the "
                "video, then pick the TV. For the whole screen, iPhone use Screen Mirroring in "
                "Control Centre with an Apple TV or an AirPlay set, Android use Smart View or Cast "
                "in the quick settings. If the TV does not appear, it is the wifi band: both have "
                "to be on the same network, and a guest network or the 5GHz-only setting hides it. "
                "A Lightning or USB-C to HDMI adapter is the wired fallback and never drops.")
    return ("A cable is the reliable way: an HDMI lead from the laptop to the TV, then press Source "
            "or Input on the TV remote and pick the socket you used; a laptop with no HDMI port "
            "needs a USB-C to HDMI adapter, which does the same job. Once the picture is up, pick "
            "the TV as the sound output - the speaker icon in the Windows tray, or System Settings > "
            "Sound on a Mac - because the laptop keeps playing sound otherwise. No cable to hand "
            "and the app has a Cast icon: that works too, with both on the same wifi.")
# Somebody the person knows, doing the ringing: "my mum keeps ringing me", "he keeps calling",
# "my sister rang me again". The relation words are the understanding's own, minus the words for
# a thing (a pet, a team), because "my dog keeps barking" is not a phone call.
PERSON_WHO_RINGS = re.compile(
    r"\b(?:mum|mom|mam|mummy|dad|daddy|mother|father|parents|sister|brother|son|daughter|gran|"
    r"granny|nan|nana|grandma|grandad|grandpa|aunt|auntie|uncle|cousin|husband|wife|partner|"
    r"boyfriend|girlfriend|in laws|in-law|ex|exes|stepson|stepdaughter|friend|friends|flatmate|"
    r"housemate|roommate|colleague|coworker|boss|manager|neighbour|neighbor|landlord)\b")
# The ringing itself, with the person as the one doing it: "keeps ringing me", "rang me again",
# "called me twice". A bare "ringing" is not enough: "i keep hearing ringing in my ears" is not a
# phone, and "the doorbell keeps ringing" has already been stood down above.
RINGING_ME = re.compile(
    r"\b(?:keeps?|kept|won'?t stop)\s+(?:on\s+)?(?:ringing|calling|phoning|texting|messaging)\b"
    r"|\b(?:rings?|rang|calls?|called|phones?|phoned|texted?)\s+(?:me|us)\b"
    r"|\b(?:ringing|calling|phoning)\s+(?:me|us)\b")
# Any word that makes it a cold caller after all, whatever person the line names.
MARKETING_CALL = re.compile(
    r"\b(?:scam|scams|scammer|scammers|scammed|accident|ppi|claim|claims|marketing|cold calls?|"
    r"cold caller|nuisance|spam|silent|unknown|withheld|international|survey|surveys|insurance|"
    r"solar|windows|double glazing|hanging up|hang up|recorded|automated|robot|robocall|"
    r"sales|telesales|debt|loan|loans|bank details|fraud|fraudster|phishing)\b")
COLD_CALLS = (
    "Register free with the Telephone Preference Service (tps.org.uk) to cut marketing calls, "
    "and use the phone's own block list for the ones that keep coming: on an iPhone it is "
    "Settings > Phone > Silence Unknown Callers, on Android it is Caller ID and spam "
    "protection in the Phone app. Never press a number to \"speak to someone\" or reply to a "
    "silent call, because that proves the line is live; if the caller says they are your bank, "
    "hang up and ring the number on your card.")


def _cold_calls(memory, reading):
    """The nuisance-calls card, or None when the ringing in the line is a person they know.

    "my mum keeps ringing me", "my boss keeps calling me at the weekend" and "my neighbour keeps
    ringing me about the fence" are relationship questions, and the Telephone Preference Service
    is no use against them. A word list cannot make the call: a relation word is in both "my mum
    keeps ringing me" and "my mum keeps getting calls from a scammer", and the second is exactly
    the line the card is for. So this reads the shape instead - somebody the person knows, doing
    the ringing - and stands the entry down only then.
    """
    line = " " + " ".join(str(reading.get("clean") or reading.get("text") or "").lower().split()) + " "
    if RINGING_ME.search(line) and PERSON_WHO_RINGS.search(line) and not MARKETING_CALL.search(line):
        return None  # somebody they know is doing the ringing: not a cold caller
    return COLD_CALLS



# Where people go, in the words people use for it. A phone or internet question with one of
# these in it is about being away from home, not about the router in the hall: "no internet on
# my phone in spain" names no roaming word at all, and it is the commonest way of saying it.
ABROAD_PLACES = ("spain", "france", "italy", "greece", "portugal", "turkey", "cyprus",
                 "croatia", "malta", "morocco", "egypt", "tunisia", "dubai", "thailand",
                 "mexico", "florida", "america", "usa", "australia", "canada", "canaries",
                 "canary islands", "tenerife", "lanzarote", "fuerteventura", "majorca",
                 "mallorca", "ibiza", "menorca", "crete", "rhodes", "corfu", "algarve",
                 "barcelona", "madrid", "paris", "rome", "amsterdam", "bali")
ABROAD = ("roaming", "abroad", "overseas", "foreign") + ABROAD_PLACES
# A machine with drink or rain in it is the same first move, and the difference worth saying is
# what the liquid was: coffee and juice dry sticky, which is the job a repair shop does, while rain
# water is mostly a drying job.
_STICKY = re.compile(r"\b(?:coffee|tea|juice|cola|coke|beer|wine|milk|soup|sauce|sugary|fizzy|"
                     r"lemonade|hot chocolate)\b")


# The two asks this row answers: keeping the glass whole, and what to do now it has gone. A line
# that names the break is the second one; "how do i stop my phone screen from cracking again" and
# "how do i protect my phone screen" are the first. A scratch is neither - it has its own words in
# the key, and the protector advice is what it gets.
_PREVENTION = re.compile(r"\b(protect|protecting|protection|prevent|preventing|guard|"
                         r"shatterproof|saver)\b|\b(stop|keep|prevent)\b[^.]{0,30}\bcrack")


# The case is the one part of a phone that costs a few pounds and breaks instead of the glass, so
# a break in the case is not a break in the phone: "the case on my phone is cracked" was told to
# put a protector on the crack, and "my phone case is cracked" got a small-talk nod. The phone
# words are already this row's subject, so a case is only read here when it is named.
_THE_PHONE_CASE = re.compile(
    r"\b(?:case|cases|cover|covers|bumper|pouch|sleeve|wallet case|flip case|folio|"
    r"phone skin|casing)\b", re.I)


# "how long does a renewal take" is a duration, and the only renewal this row knows is a
# subscription, which has no processing time. The passport, licence and insurance renewal rows
# answer the duration; this row answers the cancelling, so it stands down on a duration ask that
# has nothing to cancel in it.
_A_DURATION_ASK = re.compile(
    r"\bhow long\b|\bhow many (?:days|weeks|months)\b|\bhow quickly\b|\bhow fast\b|"
    r"\bwhat date\b|\bwhen does\b", re.I)
_SOMETHING_TO_CANCEL = re.compile(
    r"\b(?:cancel|cancelling|canceling|cancelled|canceled|stop|stopping|get rid|refund|"
    r"charged|charge|trial|paying|paid)\b", re.I)


def _a_renewal_that_takes_time(reading):
    """False when the line asks how long a renewal takes and names nothing to cancel."""
    said = " " + str((reading or {}).get("clean") or (reading or {}).get("text") or "").lower() + " "
    if _A_DURATION_ASK.search(said) and not _SOMETHING_TO_CANCEL.search(said):
        return False
    return True


def _the_phone_screen(memory, reading):
    """A phone screen: one that is already cracked, or one the person wants kept whole.

    "How do i stop my phone screen from cracking again" and "how do i protect my phone screen" ask
    the question before the glass breaks, and were answered "put a protector and a case on it now,
    so the crack does not spread" - advice about a crack they have not got. It is the same screen
    and the same few pounds, so it is one row, and the line says which half of it is being asked.
    """
    said = " " + str((reading or {}).get("clean") or "").lower() + " "
    # A break in the case, not in the glass: take it off and look at the phone under it, then
    # replace the case, which is the cheap part. Nothing here says the screen is cracked.
    if _THE_PHONE_CASE.search(said) and _A_BREAK_IN_THE_LINE.search(said):
        return ("A cracked case is the cheap part going first, which is what it is for: take it "
                "off and look at the corners and the screen under it, because a case that took a "
                "fall is telling you the phone landed on its edge. Replace it - £8 to £25 buys "
                "one with a raised lip round the screen and a rigid back, and a soft silicone "
                "one cushions a drop better than a hard shell. If the phone itself is bent, or "
                "the screen has a mark that was not there before, get it looked at before the "
                "crack in the case hides something worse.")
    if not _PREVENTION.search(said):
        return ("Put a screen protector and a case on it now, so the crack does not spread or cut "
                "your finger, and back the phone up before you book a repair. A local repair shop "
                "is usually £60 to £120, well under a new phone; go to the maker if it is "
                "under warranty or water resistant.")
    return ("A tempered glass screen protector and a case with a raised lip round the screen are "
            "what keep it whole, and the two together cost £8 to £15: the protector takes the "
            "scratch or the fall and is swapped for a few pounds, which is the point of it. Keep "
            "the phone out of a pocket with keys or grit in it, and put it face down when you set "
            "it down.")


def _laptop_water(memory, reading):
    """A laptop or a desktop that got drink, rain or a spill in it.

    The one thing that must be said first, and in the first sentence, is that the power stays
    off: a wet board with current through it is what turns a drying job into a dead machine.
    """
    said = " ".join(((reading or {}).get("text") or (reading or {}).get("clean") or "").lower().split())
    if _STICKY.search(said):
        return ("Turn it off and unplug it now, and leave it off: coffee or juice dries sticky, "
                "and current through a wet board is what kills the machine. Wipe what you can "
                "reach, keep it upside down with the lid open somewhere warm for two days, then "
                "get a repair shop to clean the board, which is \u00a340 to \u00a380 rather than a "
                "new laptop.")
    return ("Turn it off and unplug the charger straight away, and do not switch it back on to "
            "see if it works: power through a wet board is what does the damage. Tip it the way "
            "the water went in, then leave it open and upside down somewhere warm and airy for two "
            "days - rice does nothing except leave grit in the ports. Back the files up the moment "
            "it runs again, and if it stays dead a repair shop's board check is \u00a340 to "
            "\u00a380.")


def _running_out_of_charge(line):
    """True when the line holds a charge level low enough that the phone needs saving.

    A phone's charge is said as a percentage, and every number between 1 and 20 is the same
    advice: switch Low Power Mode on now. The keys of `phone-nearly-flat` can only hold the few
    figures somebody typed, so the figure is read as a shape. It is capped at twenty because
    "my phone is on 80%" is a full battery, and the row already turns that line down.
    """
    for figure in re.findall(r"\b(\d{1,3})\s*(?:%|percent)", line or ""):
        if int(figure) <= 20:
            return True
    return False

# An account with a website's name in front of it is an app account, not a bank account and not a
# contract: the money and life-admin rows key on the word "account" with a general move ("close",
# "get rid of"), and they were answering "how do i close my facebook account" with the bank
# switch service and the exit fee. The rows that answer those lines are in this file, so the names
# live here and the other tables import them rather than keeping a copy.
APP_ACCOUNT_WORDS = ("facebook", "instagram", "snapchat", "tiktok", "twitter", "linkedin",
                     "social media", "google", "gmail", "amazon", "paypal", "ebay", "netflix",
                     "spotify")

# The same names again, plus the ones people pay for by the month, for the line that never says
# the word: "how do i cancel my amazon prime" and "how do i stop paying for spotify" were hedges
# because the subscription row only keys the noun. Built off the tuple above rather than written
# out again, so a name added there cannot go missing here.
# The names people pay for, which is not the same list as the names of the apps they use: a social
# account is free, so "how do i stop comparing myself to people on instagram" and "how do i stop
# checking facebook" were read as cancelling a monthly payment and told to cancel from the place
# they pay. `APP_ACCOUNT_WORDS` is the account-closing rows' list, and this row is only for money,
# so it takes the services a bill is named after and none of the rest.
PAID_SERVICES = ("amazon", "paypal", "ebay", "netflix", "spotify",
                 "amazon prime", "prime video", "prime membership", "disney+", "disney plus",
                 "now tv", "apple music", "apple tv", "youtube premium", "audible",
                 "kindle unlimited", "icloud", "google one", "dropbox", "adobe",
                 "microsoft 365", "office 365",
                 # Software sold by the year is the same shape: "should i pay for antivirus"
                 # reached three rungs of credit and a personal loan on the words "pay for", and
                 # the answer is that Windows and Android ship with it. The names sit here so the
                 # cancel row gets them too ("how do i cancel my norton").
                 "antivirus", "anti virus", "anti-virus", "virus protection", "security software",
                 "virus checker", "norton", "mcafee", "malwarebytes", "nordvpn", "expressvpn",
                 "1password", "lastpass")

# A filter is in a washing machine, a dishwasher, a tumble dryer and an extractor hood as well as
# in a vacuum, and the follow-up that names one says only "filter": "my washing machine smells" /
# "i cleaned the filter" was answered with "wash or shake out the filter every month or two ...
# a blocked filter is the usual reason a vacuum starts to smell", which is a different machine's
# advice. `vacuum-filter`'s avoid list catches a machine named in the line; this reads the machine
# the conversation is already about, which is where the person left it.
FILTER_MACHINES = ("washing machine", "washer", "washing mashine", "dishwasher", "dish washer",
                   "tumble dryer", "tumble drier", "dryer", "extractor", "cooker hood", "hood",
                   "fridge", "freezer", "coffee machine", "water filter", "kettle", "shower",
                   "tap", "pond", "aquarium", "fish tank", "car", "caravan")
VACUUM_NAMES = ("hoover", "vacuum", "henry", "dyson", "vax", "shark", "miele", "numatic")


VACUUM_FILTER = ("Wash or shake out the filter every month or two, and change it once a year - "
                 "a blocked filter is the usual reason a vacuum starts to smell and feels weak. "
                 "Most are washable: rinse under the tap, then leave them to dry for a full 24 "
                 "hours before they go back in, because a damp filter ruins the motor.")


def _vacuum_filter_reply(memory, understood):
    """The vacuum's filter, unless the filter in the room is another machine's.

    A vacuum named in the line settles it. Otherwise the line has to be the conversation's first
    mention of a filter: once the last turns are about a washer, a dryer or an extractor, "the
    filter" is that machine's and the vacuum's monthly rinse is no answer to it.
    """
    said = ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(word in said for word in VACUUM_NAMES):
        return VACUUM_FILTER
    try:
        from ..memory import topics as _topics
        heard = " ".join(_topics.context(memory, 3)).lower()
        heard += " " + str((memory or {}).get("topic") if isinstance(memory, dict) else "")
    except Exception:
        heard = ""
    if any(word in heard for word in FILTER_MACHINES):
        return ""
    return VACUUM_FILTER


# A report of waking is not a request to be woken. The alarm row keys a phrase, so "waking up at 5
# every morning", "im done with waking up at 5" and "my little one wakes up at 5 every morning"
# all matched "wake up at" and were told to open the Clock app and set an alarm: the person had
# come to say they are up at five, or that their child is. The alarm question is an instruction
# ("wake up at 6", "wake me up at 6", "set an alarm for 6"), so the form of the waking decides -
# the -ing, the third person and the past are what happens, not what is asked for. The alarm row's
# avoid list already had one shape of this ("i wake up at") and it leaked within the month, because
# a list of first-person phrases cannot hold when the subject is the part that varies.
WAKING_IS_HAPPENING = re.compile(
    r"\b(?:waking|wakes|woke)\b(?:\s+up)?\s+(?:at|about|around|before|by)\b"
    r"|\b(?:waking|wakes|woke)\b\s+(?:up\s+)?(?:every|each|early|too\s+early)\b"
    r"|\b(?:keeps?|kept|always|still|now|im|i'm|am|was|is|are|been)\s+waking\b"
    r"|\b(?:is|was|are|were|been|stays?|stayed)\s+awake\b"
    r"|\b(?:gets?|got|getting)\s+up\s+at\b", re.I)
# The same report in the base form, which is what a line about somebody else's waking looks like:
# "why does my toddler wake up at 5 every morning" arrived as a request to set an alarm and was
# told to open the Clock app. The -s of "wakes" was the only thing the pattern above knew how to
# read, so one verb form decided whether a parent's question about a child got its answer. Two
# shapes say it is a report and not an instruction: the line asks why or when somebody wakes, or
# it names whose waking it is ("my toddler wake up at 5"). Both need a word before "wake", so the
# bare instruction "wake up at 6" and "wake me up at 6" keep the alarm answer.
ASKING_ABOUT_WAKING = re.compile(
    r"\b(?:why|how come|what time)\b[^.]{0,60}\bwake?\b"
    r"|\b(?:does|do|did)\s+(?:\w+\s+){0,3}wake\b"
    r"|\b(?:my|our|his|her|their)\s+(?:\w+\s+){0,2}wake\b", re.I)


### the alarm itself, named: "my alarm wakes me up at 6 but i snooze it" is about the alarm

ALARM_ITSELF = re.compile(r"\b(?:alarm|alarms|snooze|snoozed|clock app)\b", re.I)


def _a_request_to_be_woken(understood):
    """True when the line is about the alarm or asks to be woken, false when it reports waking."""
    line = str(understood.get("clean") or understood.get("text") or "").lower()
    if ALARM_ITSELF.search(line):
        return True
    if WAKING_IS_HAPPENING.search(line) or ASKING_ABOUT_WAKING.search(line):
        return False
    return True



# Not every app is a bill. "how do i stop paying for facebook" and "how much does instagram cost"
# were cancelling-a-subscription steps and a punt, and the honest answer is that there is nothing
# to cancel - which is worth saying, because a payment going out for a free app is an in-app
# purchase or an app-store subscription, and that is a different set of steps.
FREE_PLATFORM_NAMES = (("facebook", "Facebook"), ("instagram", "Instagram"),
                       ("snapchat", "Snapchat"), ("tiktok", "TikTok"), ("twitter", "X"),
                       ("whatsapp", "WhatsApp"), ("messenger", "Messenger"),
                       ("reddit", "Reddit"), ("linkedin", "LinkedIn"),
                       ("pinterest", "Pinterest"), ("discord", "Discord"),
                       ("youtube", "YouTube"), ("google maps", "Google Maps"),
                       ("gmail", "Gmail"))


def _free_app_reply(memory, understood):
    """Name the app, say it is free, and give the steps for a payment that is not the app's."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text", "raw")).lower()
    name = "That app"
    for word, pretty in FREE_PLATFORM_NAMES:
        if word in said:
            name = pretty
            break
    return ("{0} is free: there is no subscription to cancel, so a payment going out is an in-app "
            "purchase or a subscription bought through the app store. Cancel that in Settings > "
            "your name > Subscriptions on an iPhone, or Play Store > Payments and subscriptions "
            "on Android. To leave the account itself, deactivate it in the app's settings - "
            "deactivation hides it until you sign in again, and deletion is permanent.").format(name)

# Formatting is one job on a stick, a card and a hard disk, and the only real choice is the
# file system. It had no row at all: "how do i format a usb stick" was the plug-it-in-and-drag-
# the-files card (how to use a stick, not how to empty one), "how do i format an sd card" and
# "how do i format my laptop" were the search hedge, and "how do i wipe a hard drive" and
# "how do i format a drive on windows" were the driving-lesson timetable ("Most people need
# around 45 hours of lessons plus 20 hours of private practice") because of the word drive.
_A_STICK_OR_CARD = re.compile(r"\b(?:usb|stick|sd|micro sd|memory card|card|flash|pen "
                              r"drive)\b", re.I)
_A_HARD_DISK = re.compile(r"\b(?:hard drive|hard disk|hard disc|external drive|external "
                          r"hard|ssd|drive|disk)\b", re.I)
_FORMAT_ASKS = ("format", "formats", "formatting", "reformat", "wipe", "wiping", "wiped",
                "erase", "erasing", "erased")
# The formatting has already happened and it was not what the person wanted: the question left is
# the files, so this row says nothing and the recovery row a little further down takes the turn.
# A line asking how to format, or whether a format is safe, has no such word and keeps this answer.
_FORMATTED_BY_MISTAKE = re.compile(
    r"\b(?:by mistake|by accident|accidentally|oops|wrongly|shouldn'?t have|shouldnt have|"
    r"didn'?t mean to|didnt mean to|meant to (?:keep|save)|lost (?:all )?(?:my )?(?:photos|files|"
    r"pictures|data)|every photo)", re.I)


def _format_a_drive(memory, understood):
    """A stick or card wants exFAT; a disk being sold wants the files over-written, not just
    the index taken out. A whole machine wiped clean is the factory-reset row's question."""
    clean = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _FORMATTED_BY_MISTAKE.search(clean):
        return ""
    if not _A_STICK_OR_CARD.search(clean) and _A_HARD_DISK.search(clean):
        return ("Back everything up first, because a format wipes the disk: then on Windows "
                "right-click the drive in File Explorer and choose Format (NTFS unless it is "
                "going to a Mac), or on a Mac open Disk Utility, choose the disk and click Erase. "
                "For a disk you are selling, a quick format only takes out the index and the "
                "files can still be read, so overwrite the whole disk instead - `cipher /w` in "
                "Windows, or a free tool such as DBAN.")
    return ("Pick exFAT for a stick or card that moves between Windows and a Mac, and FAT32 for "
            "one that goes in a TV, a car stereo or a camera; NTFS only if it stays on Windows. On "
            "Windows right-click the drive in File Explorer and choose Format, set the file system "
            "and tick Quick format; on a Mac open Disk Utility, choose the drive, click Erase and "
            "pick the format. It deletes everything on it, so copy anything you want to keep "
            "first - and a stick that arrives showing as unformatted is sorted out the same way.")


def _the_bin_is_the_one_on_the_computer(understood):
    """The bin in the sentence, read from the whole sentence rather than from the word.

    "the bin needs emptying" got "right-click the Recycle Bin on the desktop": the word `bin` was
    the whole reading, and the bin in that sentence is the one under the sink. A bin is a
    computer's only when the sentence says so - a recycle bin, a trash can, a laptop, a desktop, a
    disk, files - which is what `topics.the_bin_is_on_a_machine` reads from the line's own words.
    This row owns the computer's bin, so it stands down when the sentence names no machine, and
    the kitchen bin's row owns that line.
    """
    words = set((understood or {}).get("words") or ())
    if not words & {"bin", "bins"}:
        return True  # the row is reached by a name only the machine has ("trash")
    return the_bin_is_on_a_machine(understood)




# One word, three things a "bar" can be: a pressure on a gauge, the signal on a phone, or the bar
# you hold on a bicycle. A row may claim it only when the line says which, so this is the signal's
# side of that test - the words that say a phone, or the count that only a signal is said in.
_A_SIGNAL_WORDS = frozenset(("signal", "signals", "reception", "coverage", "network", "phone",
                             "phones", "mobile", "sim", "4g", "5g", "data", "call", "calls"))
_A_COUNTED_BAR = re.compile(r"\b(?:one|two|no|zero|single|any)\s+bars?\b")


def _a_signal_reading(understood):
    """False for a bare "bar" that is not a phone signal."""
    reading = understood or {}
    text = str(reading.get("clean") or reading.get("text") or "").lower()
    words = set(str(one).lower() for one in (reading.get("words") or ()))
    if words & _A_SIGNAL_WORDS:
        return True
    return _A_COUNTED_BAR.search(text) is not None


# A file deleted by mistake has two answers, and which one the person gets depends on where the
# file lived. In a folder there is a bin and a version history behind it; on a stick, a card or an
# external drive there is neither, and every write to the drive covers the space the file was in -
# so the answer there is to stop writing to it and let a tool read it.
NOWHERE_TO_KEEP_STILL = re.compile(
    r"\b(?:usb|usb stick|usb drive|memory stick|flash drive|pen drive|stick|sd card|memory card|"
    r"micro sd|external drive|external hard|hard drive|hard disk|disk|disc|drive|card)\b", re.I)
IN_A_FOLDER = re.compile(r"\b(?:word|excel|doc|docx|spreadsheet|essay|report|homework|"
                         r"presentation|powerpoint|folder|onedrive|google drive|dropbox)\b", re.I)

RECOVER_IN_A_BIN = (
    "Check the Recycle Bin on Windows or the Bin on a Mac first, and in Word or Excel open "
    "File > Info > Manage Document > Recover Unsaved Documents, which holds copies for a few "
    "days even when you never saved. If the file lived in OneDrive or Google Drive, right-"
    "click it and open Version history, or look in the drive's own bin: both keep deleted "
    "files for 30 days.")

RECOVER_ON_A_DRIVE = (
    "Stop using the {thing} now, and do not save anything else to it: a deleted file is still "
    "there under the space a new one would take, and every file you add can cover it. Plug it into "
    "a computer and run a recovery tool that only reads the {thing} - Recuva on Windows, or "
    "PhotoRec on any system, both free - and run the deep scan, because a quick one misses the "
    "older files. If it was pulled out without ejecting, the files may be there and the index "
    "damaged, so run the computer's own check (chkdsk on Windows, First Aid on a Mac) before you "
    "give up: that fixes the view of the file, not the file itself.")
A_CARD = re.compile(r"\b(?:sd card|memory card|micro sd|card|cards)\b", re.I)
A_DRIVE = re.compile(r"\b(?:external drive|external hard|hard drive|hard disk|disk|disc|drive)\b",
                     re.I)


def _recover_deleted(memory, understood):
    """The bin and the version history, or - on a stick or a card - stop writing to the drive."""
    clean = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if NOWHERE_TO_KEEP_STILL.search(clean) and not IN_A_FOLDER.search(clean):
        thing = "card" if A_CARD.search(clean) else "drive" if A_DRIVE.search(clean) else "stick"
        return RECOVER_ON_A_DRIVE.format(thing=thing)
    return RECOVER_IN_A_BIN
ENTRIES = [
    # --- letters that are not on the key -------------------------------------
    # "how do i type an accent" had no answer at all, and "accents on a laptop keyboard" got
    # the keyboard-is-broken answer: the keyboard is fine, the letter is simply not on a key.
    # Keyed on the accent and the typing, because the accent is the subject and the machine
    # only decides which steps come first.
    entry("type-an-accent",
          (("accent", "accents", "accented", "acute", "umlaut", "diaeresis", "cedilla",
            "circumflex", "grave", "tilda", "tilde over"),
           ("type", "typing", "typed", "keyboard", "letter", "letters", "write", "put",
            "key")),
          "Hold the letter down and pick the accented one from the pop-up on a Mac, an iPhone or "
          "Android. On Windows, press Windows and full stop for the symbol panel and choose it "
          "there, or hold Alt and type 0233 on the number pad for e-acute. If you need them often, "
          "add the United States-International layout (Settings > Time & language > Language): "
          "then an apostrophe and e gives e-acute, and a tilde and n gives n-tilde. A Mac calls "
          "the same layout ABC - Extended.",
          # a speaking accent is not a letter: "how do i lose my accent" belongs to nobody here,
          # and "does she have an accent" is not a typing question.
          avoid=("british", "american", "posh", "scottish", "irish", "welsh", "aussie",
                 "australian", "southern", "northern", "speak", "speaking", "pronounce",
                 "pronunciation", "lose my accent", "my accent", "thick accent",
                 "fake accent", "put on"),
          ask=("type", "typing", "typed", "keyboard", "letter", "letters", "write")),

    # --- phone battery and charging -----------------------------------------
    entry("phone-battery-replace", (("battery", "batteries"), ("cost", "price", "how much")),
          "A new phone battery is about £35 to £70 fitted at a local repair shop, and £45 to £90 "
          "from the maker (Apple, Samsung), done in an hour or two. It is worth it when the health "
          "figure is under 80% or the phone shuts down at 20%; above that, a full day out of the "
          "old battery is usually a matter of apps and brightness.",
          # a bike, a scooter and a motorbike have a battery and a price of their own, and this
          # card answered "how much does a new ebike battery cost" with a phone battery
          avoid=("laptop", "macbook", "computer", "car", "cars", "van", "vans", "vehicle",
                 "bike", "bikes", "bicycle", "bicycles", "ebike", "e-bike", "scooter",
                 "scooters", "motorbike", "motorcycle", "moped", "lorry")),
    # The words people use when the phone will not last the day: "running out of battery by
    # lunchtime" is this answer, and it was going to `phone-storage-full`, which matches the bare
    # phrase "running out" because it was written for "running out of space".
    entry("phone-battery-drain", (("battery", "charge", "charges", "charging", "phone",
                                   "loses charge", "losing charge", "charge drops",
                                   "doesnt hold charge", "doesn't hold charge", "hold charge"),
                                  ("drain", "draining", "fast", "die", "dies", "died", "dying",
                                   "last", "losing", "drops", "the day", "running out",
                                   # a drain is often told by when it happens, and "goes flat"
                                   # is how people say the battery ran out
                                   "overnight", "goes flat", "went flat", "going flat",
                                   "runs out", "run out", "ran out", "keeps dying", "dies by",
                                   "quickly", "save", "saving", "lunchtime", "by midday",
                                   "not lasting", "is bad", "is poor", "is awful", "is rubbish",
                                   "is terrible", "is shot")),
          "Check Settings > Battery for the app using the most: social and video apps in the "
          "background are usually it, so restrict background refresh and turn the screen brightness "
          "down. If the phone is two or more years old, have a look at battery health, because a "
          "worn battery drains no matter what you switch off.",
          # A car, a bike or a scooter battery that dies is a vehicle question, not a phone
          # setting: this entry answered "my e-bike battery dies quickly" with a phone tip.
          # "drops" is read loosely as drop, so "i dropped my phone in the toilet" reached this
          # entry before `phone-water` existed: water in a phone is never a battery tip.
          avoid=("water", "wet", "toilet", "sink", "bath", "pool", "soaked", "swimming",
                 "dropped in", "fell in", "spilled", "spilt",
                 "car", "cars", "van", "vans", "vehicle", "vehicles", "bike", "bicycle",
                 "bicycles", "motorbike", "motorcycle", "scooter", "moped", "e-bike", "ebike",
                 "call", "calls", "signal", "wifi", "wi-fi", "network", "screen", "cracked",
                 "storage", "space", "photos", "cost", "price", "repair", "hot", "heat",
                 # A price asked about a drain is not a phone running flat: "how much does a
                 # drain company charge" has "charge" and "drain" in it and was answered with
                 # "Check Settings > Battery for the app using the most".
                 "how much", "quote", "quotes", "callout", "call out", "what does", "what do",
                 # a drain under the house is a plumber's question, and the company that clears it
                 # is too: "what does a drain company charge" was answered with "Check Settings >
                 # Battery for the app using the most".
                 "company", "companies", "unblock", "blocked", "blockage", "pipe", "pipes",
                 "sewer", "plumber", "plumbing", "downpipe", "gully", "manhole",
                 # a watch battery that dies is a coin cell in the watch-battery row, not an app
                 # in the background: "the battery in my watch keeps dying" got "Check Settings >
                 # Battery for the app using the most".
                 "watch", "watches", "wristwatch", "watch battery",
                 # "is it bad to charge overnight" is the overnight-charging question, and
                 # "is the battery bad enough to replace" is the battery-health one
                 # the overnight words are about charging, not the clock: "my phone battery
                 # drains overnight" is a drain, so a bare "overnight" was too wide
                 "bad to", "overnight charging", "charge it overnight", "on charge overnight",
                 "leave it charging", "leave it on charge", "all night on charge",
                 # a bare "charge overnight" here stood this entry down on "my phone loses
                 # charge overnight" and "it will not hold charge overnight", which are drains.
                 # The forms make "charging" the same word as "charge", so "charging overnight"
                 # caught those lines too: what is left is the order only a habit writes.
                 # the charging-habit question is asked as a yes/no about the habit, not about
                 # the drain: "should i charge my phone overnight" has no drain word in it
                 "should i charge", "can i charge", "should i leave", "can i leave",
                 "is it bad", "is it ok", "is it okay", "ok to charge", "okay to charge",
                 # a safety ask about the habit is the habit row, not the drain tips
                 "is it safe", "safe to leave", "safe to charge", "safe to keep",
                 "fine to leave", "ok to leave",
                 "is charging overnight bad", "charging overnight bad",
                 "is overnight charging bad", "is charging all night bad",
                 "is that ok", "is that okay", "is this ok", "is this okay",
                 # a phone that was left on all night and is flat now wants the flat-phone card,
                 # not the drain advice: it is the state now, not the habit
                 "is flat", "was flat", "nearly flat", "almost flat",
                 "bad for the battery", "ruin",
                 "worth replacing", "replacement",
                 "health", "healthy",
                 "fast enough", "game", "games", "speed", "speedy",
                 "last night", "last week", "last month", "last year", "last time",
                 # a laptop that will not hold charge is the laptop's question, not a phone
                 # setting: the bare "charge" this key can hit must not take its lines
                 "laptop", "macbook", "mac book", "notebook", "computer", "pc", "desktop",
                 "chromebook"),
          # "my phone battery is rubbish" is a verdict on the battery and the drain card is the
          # answer, but the disposal row in home.py reads the word rubbish as rubbish to bin and
          # won the line. The library keeps the highest bias, so the verdict gets its own nudge.
          bias=1),
    # Where the health figure is, which is the row above the count and the row above the advice
    # on looking after it. "how do i check my battery health" reached the chemistry card, which
    # explains what a battery is instead of where the number is, so this row carries the point.
    entry("phone-battery-health", (("battery", "phone"), ("health", "healthy", "condition",
                                                          "capacity", "service", "80%", "78%",
                                                          "85%")),
          "On an iPhone it is Settings > Battery > Battery Health; on Android, Settings > Battery "
          "> Battery usage usually shows it, or use an app like AccuBattery. Below 80% of its "
          "original capacity is when a new battery is worth it, and it is usually £40 to £70.",
          bias=1,
          # A laptop's battery has its own rows, and they are the only ones that can say where
          # the figure is on a laptop: "my laptop battery drains fast, how do i keep it healthy"
          # was answered with the iPhone and Android buttons.
          avoid=("laptop", "macbook", "mac book", "notebook", "chromebook", "computer",
                 "desktop", "pc",
                 # a car battery is not a phone's: "keep a car battery healthy" was answered
                 # with the iPhone's Battery Health screen. cars.py has the 12V answer.
                 "car", "cars", "van", "vehicle", "engine", "under the bonnet", "jump start",
                 "jump leads", "starter motor", "alternator", "12v", "diesel", "petrol")),
    # The count is its own question: "how many charging cycles does a phone battery have" was
    # reaching the e-bike battery, which has nothing to say about a phone and gave the turn up.
    entry("phone-battery-cycles",
          (("battery", "phone", "iphone", "android", "handset", "tablet", "charge cycle",
            "charging cycle", "battery cycle"),
           ("charging cycle", "charging cycles", "charge cycle", "charge cycles", "cycles",
            "cycle count", "how many cycles", "cycle",
            # "charges" is the same count in the words people use, and the bare plural is not a
            # key: it met "how long does a phone take to charge" and gave the count where the
            # charging-time row belongs. The ask shapes carry the count on their own.
            "how many charges", "how many charges does", "number of charges",
            "how many times")),
          "A charge cycle is a whole 0 to 100% of use rather than one plug-in, so two top-ups "
          "from 50% add up to one, and a phone battery is rated for about 500 of them before it "
          "falls to 80% of its original capacity - roughly two years of charging once a day. "
          "Newer iPhones are rated for 1,000. The count sits under Settings > Battery > Battery "
          "Health on an iPhone.",
          # the e-bike pack answers a plain "battery" line and rates higher than the rest of
          # these rows, so the phone's count has to outrank it to be reached at all
          bias=3,
          # a pack on a bike or a battery in a car has its own rating and its own rows, and
          # "how many cycles does an ebike battery last" was read as this answer
          avoid=("ebike", "e-bike", "electric bike", "electric bicycle", "bike", "bikes",
                 "bicycle", "bicycles", "scooter", "motorbike", "motorcycle", "car", "cars",
                 "van", "lorry", "truck", "drill", "drills", "laptop", "macbook",
                 # looking after it, what is draining it and a replacement's price are other
                 # rows; "how many cycles before it dies" is still the count, so a worn-out
                 # word is not what stands this row down.
                 "look after", "care", "healthy", "drain", "drains", "runs out", "hot",
                 "swollen", "replace", "replacement", "price", "cost", "wont charge")),
    entry("phone-battery-care", (("battery", "phone", "iphone", "android", "handset"),
                                 ("look after", "care for", "take care of", "look after it",
                                  "look after the battery", "keep it healthy",
                                  "keep my battery healthy", "healthy",
                                  "prolong", "make it last", "last longer", "long life",
                                  "in good condition", "good condition")),
          "Keep it between about 20 and 80 per cent where you can, and avoid heat more than "
          "anything: a phone left on a hot dashboard loses capacity faster than one charged "
          "carefully. Slow charging overnight is fine, fast charging now and then is fine, and "
          "there is no need to run it flat or to charge it to 100 per cent to keep it honest - "
          "both are old advice for batteries that no longer exist.",
          # how healthy the battery is, what a replacement costs and what is draining it are
          # three other questions with three other answers.
          avoid=("capacity", "cycles", "80%", "replace", "new battery", "worth",
                 "swollen", "swelling", "drain", "drains", "dies", "dying", "dead", "hot",
                 "not charging", "wont charge", "charging port", "overnight",
                 "laptop", "macbook", "notebook", "computer", "car", "camera"),
          # a science answer about how batteries store charge is a different question, and
          # "the battery" with no device in the line is still this answer when it asks how to care
          # for one.
          bias=2),
    entry("phone-not-charging", (("not charging", "wont charge", "won't charge", "charging slow",
                                  "charges slowly", "charge", "plug", "cable"),
                                 ("phone", "iphone", "android", "mobile", "handset", "device")),
          "Try another cable and plug first, then clean the charging port out with a wooden "
          "toothpick, because a ball of pocket fluff is the most common cause. If it still will "
          "not take a charge, try a wireless charger to see whether it is the port.",
          avoid=("hot", "heat", "warm", "overheat", "abroad", "roaming", "holiday", "foreign",
                 "tariff", "bill", "data", "overnight", "night", "bad", "safe", "harm", "damage",
                 "ruin", "healthy", "last", "lasts", "lasting",
                 # a duration ask is the clock below, not a phone that will not take a charge:
                 # "how long to charge a phone" was answered with a cable and a toothpick
                 "how long", "how many hours", "charge time", "charging time", "take to charge",
                 "long to charge", "time to charge")),
    # "How long to charge a phone" is a clock, and the row above keyed on "charge" answered it
    # with the fix for a phone that will not charge at all: a right-topic reply with no duration
    # in it. The figure is its own answer, so this row holds the duration phrases and the row
    # above stands down on them.
    entry("phone-charge-time",
          (("phone", "iphone", "android", "handset", "mobile", "smartphone"),
           ("how long", "how many hours", "charge time", "charging time", "time to charge",
            "take to charge", "takes to charge", "long to charge", "long does it take to charge",
            "fully charged", "full charge", "charge from empty", "0 to 100")),
          "A phone goes from empty to full in about 1.5 to 2 hours on an ordinary charger, and a "
          "fast charger gets to half in about half an hour and finishes in a little over an hour. "
          "The last 20% is the slowest part on purpose - it tops up gently to look after the "
          "battery - so a phone that seems to stall near full is behaving normally.",
          # a phone that will not charge, a battery that drains, the overnight habit and the
          # count of charge cycles are four other questions with four other rows.
          avoid=("not charging", "wont charge", "won't charge", "wont take a charge", "dead",
                 "broken", "fault", "faulty", "drain", "drains", "draining", "slow", "slowly",
                 "overnight", "all night", "every night", "overheat", "hot", "cycles",
                 "laptop", "macbook", "notebook", "tablet", "ipad", "smartwatch", "watch",
                 "car", "ebike", "e-bike", "scooter", "bike", "drill", "power bank",
                 "wireless charger", "wireless charging", "warranty", "replace",
                 "replacement", "battery life")),
    # A person saying how they charge the phone is asking whether it is doing the battery harm:
    # after "how do i stop my phone battery draining so fast", "i charge it every night" was a
    # shrug (and, before the price entry stood aside, the £80 to £200 to clear a blocked drain).
    # The habit words are in the key so the line is answered as what it is - the overnight
    # question, said as a habit - and no new word is added to the keys: a new common word lowens
    # its rarity for every other entry in the domain and re-ranks lines that have nothing to do
    # with charging (it took "my phone loses charge really quickly" off the drain answer).
    entry("phone-overnight-charge", (("overnight", "all night", "every night", "each night",
                                      "nightly", "every evening", "every day"),
                                     ("charge", "charging", "charged", "plug", "plugged")),
          "Leaving a modern phone on the charger overnight is fine: it stops at full and the "
          "charger trickles nothing. The heat is what wears a battery, so take the thick case off, "
          "keep it off the duvet and out of the sun, and if you want it to last longer, use a slow "
          "charger rather than a fast one.",
          # "is charging overnight bad" is the habit question, and it scores exactly what a drain
          # told by the time of day does: the tie goes to the habit, which is the commoner line
          bias=1,
          # a battery that loses its charge is never asking about the habit
          avoid=("loses charge", "losing charge", "drops charge", "dropping charge",
                 "keeps losing", "hold charge", "holds charge",
                 # the row's answer is about a phone, and its keys are "overnight" and
                 # "charge": a laptop on the mains was told "Leaving a modern phone on the
                 # charger overnight is fine". The laptop's own row has that answer. A tablet is
                 # named here neither: there is no tablet row for the overnight ask, and standing
                 # this row down for "tablet" left the medicine card as the only tablet answer.
                 "laptop", "macbook", "notebook")),
    entry("phone-hot", (("phone", "iphone", "android", "handset"), ("hot", "overheating",
                                                                   "overheat", "warm", "heat",
                                                                   "boiling")),
          "Take the case off and stop charging it while you use it: heat plus charging is what "
          "makes a phone hot. Close the heavy games and video apps, keep it out of direct sun, and "
          "if it is hot while idle, check Settings > Battery for an app stuck running.",
          bias=2),
    # A screen that goes dim on its own is three faults the phone fixes itself, and one that a
    # person has to notice: auto-brightness following the light, low power mode, and the heat cap.
    # The battery rows key on the word battery and the hot row keys on heat, so the dimming line had
    # nothing of its own and got a shrug.
    entry("phone-screen-dim", (("phone", "iphone", "ipad", "android", "handset", "mobile",
                               "screen", "display"),
                              ("dim", "dims", "dimmed", "dimming", "dimmer", "dark", "darker",
                               "goes dark", "got dark", "brightness", "too dark", "hard to see",
                               "fades", "faded")),
          # Each sentence names its own cause, because the composer can show one of them alone:
          # "The third one is heat" arrived with no first or second on screen when the same line
          # was asked twice in a conversation.
          "Auto-brightness is the usual cause: in Settings > Display it tracks the light in the "
          "room, so the screen dims when you step out of the sun. Low power mode is the next thing "
          "to rule out: below 20 per cent battery the phone caps the brightness until you charge "
          "it. Heat does it too: a phone left in the sun or charging under a pillow dims the screen "
          "to cool itself, and it comes back once it is off the charger in a cool place. If it dims "
          "while you are holding it and the battery is fine, take the screen protector off and "
          "check for a schedule that turns the brightness down at night.",
          # a cracked screen, a phone that is hot, a dead phone and a battery question are other
          # answers, and so is the sleep advice about screens at night
          avoid=("cracked", "crack", "smashed", "broken", "cracked screen", "battery", "charge",
                 "charging", "charger", "flat", "hot", "overheating", "overheats", "wont turn on",
                 "won't turn on", "turned off", "switched off", "tv", "television", "laptop",
                 "monitor", "projector", "kindle", "camera", "photo", "photos", "sleep",
                 "bedtime", "night shift", "blue light"),
          bias=1),
    # A green or purple blotch, a bright line down the screen and a black patch that grows are the
    # panel itself failing, not a setting: nothing in Software Update or a factory reset touches
    # them, and the line that says it was answered with "thanks for telling me" because no row had
    # the words. Kept apart from the dimming row, which is the brightness the phone can fix.
    entry("phone-screen-damage", (("screen", "display", "phone", "iphone", "android", "handset",
                                   "tablet", "ipad", "lcd", "oled"),
                                  ("green", "purple", "pink", "blue", "yellow", "lines", "line",
                                   "blotch", "blotches", "patch", "patches", "spot", "spots",
                                   "stain", "stains", "bleeding", "ink", "discoloured",
                                   "discolored", "dead pixel", "dead pixels", "dead spot",
                                   "dead spots", "went green", "went purple", "tint",
                                   "stripes", "glitch", "glitchy")),
          "Green or purple blotches, a bright line and a growing black patch all mean the panel "
          "inside is damaged - a cracked layer, pressure from a case, or liquid that got in - and "
          "no setting, reset or software update will clear it. Back up and get your photos off it "
          "today, while the screen still responds, because the damaged area usually spreads. A "
          "replacement screen is usually £50 to £120 fitted on a mid-range phone and £150 to £300 "
          "on a flagship; a repair shop does it in a few hours and your data stays put.",
          # a cracked screen, a phone that will not turn on and a dim screen have their own cards
          avoid=("cracked", "crack", "smashed", "dropped", "battery", "charge", "charging",
                 # a line on the display is not a phone line: "my phone line is dead" was a
                 # screen full of green blotches, because the row keys "phone" and "line" and
                 # the dead line is the landline entry's
                 "phone line", "phone lines", "telephone line", "landline", "land line",
                 "dial tone", "dialling tone", "fixed line", "broadband",
                 "charger", "wont turn on", "won't turn on", "turned off", "switched off",
                 "dim", "dims", "dimmer", "brightness",
                 # another screen is another answer: laptop, TV and cinema prices do not apply
                 "laptop", "tv", "television", "monitor", "projector", "kindle", "camera",
                 "cinema", "film", "golf", "greenhouse", "garden", "lawn", "grass", "green bin",
                 "recycling", "traffic light", "green light", "green card", "green paper",
                 # a green background is a wallpaper or a theme, not a broken panel
                 "background", "wallpaper", "theme", "colour scheme", "color scheme",
                 "home screen colour", "icon", "icons"),
          bias=1),
    entry("dust-out-of-laptop", (("dust", "fluff", "hairy"), ("laptop", "computer", "fan",
                                                              "vent", "vents", "clean", "clear")),
          "Shut it down and unplug it, then blow short bursts of air through the side and back "
          "vents with a can of compressed air, holding the fan still with a toothpick so it does "
          "not spin. A soft brush takes the mat off the grille; if the vents are caked solid, a "
          "repair shop will open it and re-paste the processor for about £40."),
    entry("delete-social-account", (("instagram", "facebook", "tiktok", "snapchat", "twitter",
                                     "social media", "account"),
                                    ("delete", "deactivate", "quit", "close", "get rid", "remove")),
          _social_delete_reply,
          avoid=("bank", "banking", "billing", "bill", "late", "estate", "father", "mother",
                 "mum", "dad", "passed", "died", "death", "funeral", "will", "probate",
                 "membership", "gym", "contract", "insurance", "pension", "mortgage",
                 # a card account is closed by the bank, not in an app: "how do i close a
                 # credit card account" was told to look under Settings > Deactivate
                 "card", "cards", "credit card", "debit card", "overdraft", "loan",
                 # and a shop or a phone-maker is not a social network: "how do i close my
                 # amazon account" got the "Settings > Deactivate" line for an app
                 "amazon", "apple", "google", "microsoft", "paypal", "ebay", "netflix",
                 "spotify", "email", "email account", "online account", "shopping")),
    entry("close-a-service-account",
          (SERVICE_ACCOUNT_NAMES,
           ("close", "closing", "delete", "deleting", "remove", "deactivate", "cancel", "get rid",
            "shut"),
           # the word "account" is what makes it an account question: "how do i cancel netflix" is
           # the subscription card, and a shop, a bank or a club closes an account, not an app.
           # It is in the key rather than in `ask` because a storage card and a bank card both key
           # the service's name and outscored a row that only asked: "how do i delete my icloud
           # account" was answered with the Manage Account Storage list.
           ("account", "accounts")),
          _service_delete_reply,
          # `ask` gates it as well as the key group: "how do i cancel my disney plus" names a
          # service and says cancel, but with no account word it is the renewal card's line
          ask=("account", "accounts"),
          avoid=("bank", "banking", "gas", "electricity", "water", "broadband", "mobile", "phone",
                 "gym", "membership", "club", "contract", "insurance", "pension", "mortgage",
                 "council", "credit card", "debit card", "overdraft", "loan", "isa",
                 "facebook", "instagram", "tiktok", "snapchat", "twitter", "linkedin",
                 # a cloud-storage limit is not a closure: "icloud storage is full" and "google
                 # one says i am out of space" want the clear-space card
                 "storage", "space", "full", "out of space", "backup", "backing up",
                 "password", "hacked", "locked out", "sign in", "log in", "login",
                 # a subscription is cancelled where it was sold, which is the renewal card, not
                 # the steps for closing the whole account: "how do i cancel my audible
                 # subscription" was reading "cancel" and the name as an account closure
                 "subscription", "subscriptions", "renewing", "renewal", "free trial",
                 "trial", "charged")),
    entry("block-number", (("block", "blocked", "unblock", "unblocked", "unblocking", "nuisance",
                            "stop calls", "stop texts", "unknown numbers", "numbers i dont know",
                            "numbers i don't know", "withheld",
                            # "how do i stop someone ringing me" is the same screen as "how do i
                            # block a number", and the phone words alone never reached it: the
                            # line names a person, not a caller, so the stopping is keyed too.
                            # A named relative is not here - that line is about the person and
                            # the avoid below hands it back to the family rows.
                            "stop ringing", "stop calling", "stop phoning", "stop someone",
                            "stop people", "stop them calling", "stop him calling",
                            "stop her calling", "wont stop calling", "won't stop calling",
                            "keeps ringing me", "keeps calling me", "keeps phoning me"),
                           # "where is my blocked list" and "how do i view blocked contacts" are
                           # the same screen as "how do i unblock a number", and a line cannot
                           # reach them without one of the block words in the first group
                           ("number", "caller", "call", "calls", "phone", "text", "list", "lists",
                            "contact", "contacts", "someone", "people", "settings", "view", "see",
                            "ringing", "calling", "phoning", "ringing me", "calling me",
                            "phoning me")),
          "On an iPhone open the call or message, tap the name or number, then Block this Caller; "
          "on Android long-press the number in the call log and choose Block. To let someone back "
          "in, go the other way: Settings > Phone > Blocked Contacts on an iPhone, or the blocked "
          "list in the Phone app on Android, and remove them there. Report scam texts to 7726 in "
          "the UK first, and for silent nuisance calls ask your network to switch on call "
          "screening, which catches most of them.",
          guard=_the_block_is_the_phones,
          # the block list here is the phone's own, not one app's
          avoid=("whatsapp", "instagram", "facebook", "tiktok", "snapchat", "telegram", "app",
                 # A person who has gone quiet is not a number to block: "stopped texting"
                 # is a loose form of the "stop texts" key and it was answering
                 # "my friend stopped texting me back" with the block screen. The friendship
                 # answers own those lines.
                 "friend", "friends", "mate", "mates", "girlfriend", "boyfriend", "wife",
                 "husband", "partner", "crush", "ghosted", "ghosting", "went quiet",
                 "gone quiet", "not replying", "no reply", "hasnt replied", "hasn't replied",
                 "texting me back", "texted me back", "me back", "replying to me",
                 "hasnt texted", "hasn't texted",
                 # "my mum keeps ringing me at work" is about the person, not the phone's block
                 # list, and so is asking how to say it: the family rows own those.
                 "my mum", "my dad", "my mother", "my father", "my sister", "my brother",
                 "my son", "my daughter", "my gran", "my nan", "my grandma", "my grandad",
                 "mother in law", "mother-in-law", "kindly", "say it", "how do i tell")),
    entry("earbud-quiet", (("earbud", "earbuds", "headphone", "headphones", "airpods"),
                           ("quiet", "one ear", "one side", "left", "right", "silent", "volume",
                            "stopped working")),
          "Clean the mesh on the quiet side with a dry toothbrush, because earwax is the usual "
          "culprit, then check the balance in your phone's accessibility audio settings is in the "
          "middle. If it is an AirPod, take it out and put it back in the case for ten seconds; "
          "if the other one has sound, the earbud is not dead."),
    # The commonest small annoyance with a pair of wired headphones, and it had no answer. The
    # fix is the one roadies use, so it is the whole reply.
    entry("headphones-tangle",
          (("headphones", "earphones", "earbuds", "cable", "lead", "wires", "cord"),
           ("tangle", "tangles", "tangled", "tangling", "knot", "knots", "knotted", "coil",
            "coils", "wind", "wrap", "wrapped", "store", "storing", "stop")),
          "Wind them over-under: pinch the plug end, make a loop with one hand, and alternate "
          "each turn the other way so the cable lies flat instead of twisting into a spiral. Hold "
          "the coil with a Velcro tie or a loose hairband, not a tight elastic band, and put the "
          "two earbuds in a small pouch rather than a pocket full of keys. A figure-of-eight with "
          "the plugs tucked through is the other tidy way, and short or wireless headphones end "
          "the problem altogether.",
          avoid=("charge", "charging", "not working", "broken", "quiet", "one ear", "sound",
                 "volume", "bluetooth", "pair", "pairing", "replace", "buy", "best", "which",
                 # a fit that slips or aches is a different job from a cable that knots:
                 # "how do i stop my headphones hurting my ears" was getting the over-under
                 # winding instructions
                 "fall out", "falls out", "falling out", "fell out", "keep falling", "slip out",
                 "slips out", "slipping out", "wont stay", "won't stay", "stay in", "stay put",
                 "hurts", "hurt", "hurting", "pain", "painful", "ache", "aches", "aching",
                 "sore", "sore ears", "too tight", "tight", "clamp", "clamping", "squeeze",
                 "squeezing", "pressure", "uncomfortable", "comfortable", "heavy", "glasses")),
    # Two complaints, one cause: earbuds that will not stay in and a headband that presses. The
    # answer is fit, not sound, so it holds no audio words.
    entry("headphones-fit",
          (("headphones", "earphones", "earbuds", "airpods", "in ears", "in-ear", "headset",
            "head band", "headband", "earphones"),
           ("fall out", "falls out", "falling out", "fell out", "keep falling", "slip out",
            "slips out", "slipping out", "wont stay", "won't stay", "stay in", "stay put",
            "hurts", "hurt", "hurting", "pain", "painful", "ache", "aches", "aching", "sore",
            "too tight", "tight", "clamp", "clamping", "squeeze", "squeezing", "pressure",
            "uncomfortable", "comfortable", "fit", "fits", "fitting", "size")),
          "Try the other size of ear tip first: most earbuds come with three, most people are "
          "wearing one size too big, and the seal, not the loudness, is what keeps them in. Twist "
          "them in and back a little so the tip points into the ear canal rather than straight at "
          "it, and use the one earbud with the hook over the top of the ear when you are moving "
          "about. On a wired pair with buds that drop out, the small silicone wings or a foam tip "
          "cost a few pounds and hold far better. If it is the headband that aches, slide the cups "
          "so the band sits further back and the pads sit around the ear rather than pressing on "
          "it, and take them off for ten minutes every hour: a headache behind the ears is the "
          "clamp, not the volume.",
          # a cable that knots, and the audio itself, are other entries
          avoid=("tangle", "tangles", "tangled", "tangling", "knot", "knots", "coil", "wind",
                 "wrap", "wrapped", "store", "storing", "charge", "charging", "not working",
                 "broken", "quiet", "one ear", "sound", "volume", "bluetooth", "pair", "pairing",
                 "replace", "buy", "best", "which", "noise cancelling", "microphone")),
    # "teams" alone is the plural of "team", and the lookup reads it loosely, so the app only
    # answers when the line names it as one: "teams call", "ms teams", "teams app".
    entry("video-call-sound", (("video call", "video calls", "zoom", "facetime", "skype",
                                "ms teams", "microsoft teams", "teams call", "teams call on",
                                "teams meeting", "teams app", "teams video", "teams sound",
                                "teams audio", "teams mic", "teams microphone"),
                               ("hear", "heard", "sound", "microphone", "mic", "audio", "quiet",
                                "loud", "echo")),
          "In the call settings pick the right microphone and speaker instead of the default, "
          "because a monitor or headset often takes them over. Raise the input volume to about "
          "80%, sit closer to the mic, and use headphones on both ends to stop the echo; if it is "
          "an older relative, a tablet is easier than a phone."),
    # The place is the abroad word: "no internet on my phone in spain" and "how do i get
    # internet on holiday" are the same question, and the country name has to reach the row.
    entry("mobile-data-abroad", (("holiday",) + ABROAD,
                                 # A phone or data word, and nothing else: "holiday" plus
                                 # "work" was enough for this row, so a leave question and "i
                                 # work in a shop and im going on holiday" got roaming advice.
                                 ("mobile data", "data", "phone", "internet", "not working")),
          "Check roaming is on in Settings > Mobile data, and that you have a roaming pass for "
          "that country, since most UK networks charge about £2 a day in the EU and much more "
          "outside it. Then turn the phone off and on so it re-registers, and set the network "
          "selection to automatic in Mobile data > Network selection.",
          # "holiday" plus "work" is also how people ask about time off: "do i have to work
          # bank holidays" is a leave question, and the holidays answer is the work.py one.
          # A bank holiday weekend is a weekend at home: the router, not the roaming.
          # "is my phone covered on holiday" was this row's, and the person was asking their
          # insurer, not their network: the policy words stand it down so the honest punt comes
          # back rather than roaming instructions.
          avoid=("lost", "lose", "stolen", "stole", "dropped", "cracked", "left", "forgot",
                 "insured", "insurance", "insure", "cover", "covered", "covering", "policy",
                 "excess", "claim", "claims", "gadget cover", "travel insurance",
                 "bank holiday", "bank holidays", "holiday weekend", "annual leave", "time off",
                 "day off", "days off", "my job", "my boss", "employer", "entitled",
                 "entitlement", "contract", "notice period", "rota", "shift", "unpaid")),

    entry("phone-slow", (("phone", "android", "iphone", "mobile", "handset"),
                         ("slow", "slower", "sluggish", "laggy", "lag", "speed up",
                          "faster", "freezing", "stuck", "unresponsive", "old", "crawl",
                          "crawling", "clear space", "free up space", "running out of space",
                          "storage", "no space", "full")),
          "Restart it first, then clear space: a phone that is nearly full slows down badly, so "
          "delete old videos and apps you do not use. On Android, clearing the cache in Settings > "
          "Storage helps too; on an iPhone, check Settings > General > iPhone Storage for the app "
          "taking the most.",
          # a phone stuck at the logo, or one that will not boot, is the start-up entry
          avoid=("apple logo", "boot loop", "stuck on the logo", "wont turn on", "will not turn on",
                 "wont start", "will not start", "black screen", "dead",
                 # the phone is the thing being made faster, so the browser, the wifi or a charge
                 # that will not last are other entries' lines
                 "wifi", "wi-fi", "internet", "broadband", "battery", "charge", "charging",
                 "signal", "data", "hot", "overheating", "contract", "upgrade", "bill")),
    entry("laptop-storage-full", (("laptop", "computer", "pc", "mac", "macbook", "drive", "disk"),
                                  ("storage", "space", "full", "free up", "clear", "delete",
                                   "running out")),
          "Empty the Downloads folder and the bin first, then look in Settings > System > Storage "
          "(Windows) or Apple menu > System Settings > Storage (Mac) at what is biggest. Videos, "
          "old installers and a cloud folder kept offline take most of it; moving those to an "
          "external drive is the quickest big win.",
          # "running out" is the disk and the charge at once, and this row was taking the charge:
          # "my laptop keeps running out of battery" got the storage answer. The battery row owns
          # anything that says what is running out is the battery.
          # a car with a space saver wheel on is a car question, not a disk one: "can i drive it
          # with a space saver wheel on" was told to empty the Downloads folder, on "space" and
          # "drive". The space-saver and spare-wheel words close this row.
          avoid=("battery", "batteries", "charge", "charger", "charging", "dies", "dying",
                 "space saver", "spacesaver", "spare wheel", "spare tyre", "spare tire",
                 "space-saver", "car", "tyre", "wheel")),
    entry("mailbox-full", (("mailbox", "inbox", "email"), ("full", "storage", "space", "bouncing",
                                                           "cannot receive", "cant receive",
                                                           "make room", "room in", "free up space",
                                                           "clear some space", "clear space")),
          "Empty the Sent and Deleted items, then sort by size and delete the big attachments, "
          "since a handful of photos can be most of it. If you use IMAP, keep only recent mail on "
          "the device, and archive the rest to folders; a free 15GB with Gmail or Outlook is enough "
          "once the junk is gone.",
          avoid=("spam", "junk email", "unwanted", "scam", "phishing")),
    # Five faults people describe and no row answered, or the wrong row did: a phone with no SIM,
    # email that has stopped arriving, a television remote that does nothing, a touch screen that
    # has stopped responding, and a television that switches itself off. Each has a first move of
    # its own, so each is a row.
    entry("phone-no-sim",
          (("no sim", "sim not found", "sim card not", "sim not recognised", "sim not recognized",
            "sim card error", "check sim", "insert sim", "sim not detected", "sim missing",
            "says no sim", "no service sim", "sim not working", "sim card not working",
            "detecting the sim", "detect the sim", "reading the sim", "read the sim",
            "doesnt see the sim", "cant see the sim", "cannot see the sim",
            # the same job asked as a how-to: putting the card in is what a phone with no SIM
            # needs, and a shrug was the answer for "how do i put a sim card in my phone"
            "put a sim", "put the sim", "put my sim", "insert a sim", "insert the sim",
            "sim card in", "change the sim", "swap the sim", "replace the sim", "sim tray",
            "take the sim out", "remove the sim", "sim not supported",
            "sim card not supported", "clean the sim", "clean my sim"),
           ("phone", "iphone", "android", "mobile", "handset", "sim", "says", "error", "tray",
            "insert", "carrier", "network", "not working", "keeps")),
          _sim_reply,
          # unlocking a phone to another network, a lost card and a passcode are other rows
          avoid=("unlock", "unlocked", "unlocking", "network unlock", "unlock code", "carrier lock",
                 "sim only", "sim free", "sim-free", "locked to", "passcode", "pin", "puk",
                 "lost", "stolen", "i found", "found phone", "cracked", "top up", "topping up",
                 "tariff",
                 "bill", "contract", "roaming", "abroad")),
    entry("email-not-syncing",
          (("email", "emails", "mail", "gmail", "outlook", "inbox", "hotmail", "yahoo mail"),
           ("not syncing", "not coming through", "no new emails", "not arriving",
            "stopped syncing", "wont sync", "will not sync", "not updating", "not receiving",
            "not downloaded", "not downloading", "keeps saying", "not showing",
            "stopped coming", "stopped arriving", "stopped coming through",
            # "i am not getting my emails" was `too-many-emails`' line: the words for mail that
            # has not turned up were "not arriving" and "not coming through", and the everyday
            # way of saying it is "not getting"
            "not getting my email", "not getting my emails", "not getting any email",
            "not getting any emails", "not getting emails", "not getting email",
            "never getting my emails", "not had any emails", "havent had any emails",
            "nothing in my inbox", "no emails at all")),
          "Open the mail app and pull the inbox down to refresh it - a phone that has been on "
          "battery saver stops fetching quietly, so check that first, then Settings > Mail > Fetch "
          "New Data (or the account's sync setting on Android) and set it to Push or every 15 "
          "minutes. If the account is also full, mail is refused rather than delivered, so check "
          "the storage figure. When nothing has arrived for days, remove the account and add it "
          "back: the mail on the server is untouched and the last week comes down with it.",
          # a letter, a parcel and a bill are post, not mail, and the printer has its own rows
          avoid=("letter", "letters", "post", "postbox", "post office", "parcel", "delivery",
                 "stamp", "stamps", "address", "redirect", "invoice", "bill", "printer", "print",
                 "envelope", "royal mail", "junk mail", "spam mail", "mailbox", "voicemail",
                 "answerphone", "email address", "change my email", "new email address",
                 "email account for", "sign up", "newsletter", "unsubscribe", "scam", "phishing"),
          bias=1),
    entry("tv-remote-dead",
          (("remote", "remote control", "zapper"),
           ("not working", "stopped working", "wont work", "will not work", "doesnt work",
            "does not work", "not responding", "dead", "nothing happens",
            "does nothing", "did nothing", "wont do anything", "will not do anything",
            "wont change", "will not change", "wont turn the tv", "buttons", "keeps", "only works",
            "have to press", "stopped",
            # the how-to for the same job: "how do i change the batteries in my tv remote" was the
            # chemistry of a battery, and a person wants the tray and the two AAAs
            "batteries", "battery", "change the batteries", "replace the batteries",
            "new batteries", "flat battery", "flat", "died")),
          "Change both batteries - two AAA in nearly all of them, with the shape of the tray "
          "showing which way round - and check they are the right way round: a remote that needs the "
          "button pressed hard is a battery on its way out - then test it: point it at a phone "
          "camera and watch the little light on the end through the screen, which shows on a "
          "working remote and never does on a dead one. A remote that tests fine but does nothing "
          "is usually unpaired (a Bluetooth or voice remote, paired by holding the two buttons the "
          "manual names while the TV is on) or it is sending to the box rather than the set. The "
          "channel's own app will run the set while you sort it out.",
          # a car key fob is cars.py's answer, and a doorbell or a garage remote has its own
          avoid=("car", "key fob", "keyfob", "fob", "garage", "gate", "doorbell", "door", "alarm",
                 "central locking", "car key", "heating", "thermostat", "boiler", "fan", "blind",
                 "blinds", "curtain", "light", "lights", "ceiling fan", "radio controlled")),
    entry("touch-screen-dead",
          (("touch", "touchscreen", "touch screen", "screen", "display", "glass"),
           ("not responding", "not responding to touch", "wont respond", "will not respond",
            "unresponsive", "not working", "frozen", "froze", "stuck", "not reacting",
            "doesnt respond", "does not respond", "dead spot", "dead spots", "wont let me",
            "will not let me", "ignores", "no response", "stopped working",
            "stopped responding", "has stopped")),
          "Force a restart first, because a frozen digitiser is the commonest cause and nothing "
          "else works while it is frozen: on an iPhone press volume up, then volume down, then "
          "hold the side button until the Apple logo appears; on Android hold the power button for "
          "20 to 30 seconds. Then clean the glass, take off a thick screen protector or a case "
          "that presses on the edges, and dry your hands - a damp or gloved finger is not read. A "
          "screen that responds in some places and not others has a dead band in the digitiser, "
          "which is a new screen, £50 to £120 fitted on a mid-range phone.",
          # a cracked or blotchy panel, a phone that switches itself off and a phone that will not
          # come on are other rows
          avoid=("cracked", "crack", "smashed", "dropped", "blotch", "blotches", "green line",
                 "purple", "turns itself off", "switching itself off", "wont turn on",
                 "won't turn on", "black screen", "no picture", "tv", "telly", "television",
                 "monitor", "laptop", "computer", "printer", "atm", "till", "self service",
                 "kiosk", "car", "watch"),
          bias=1),
    # A laptop that will not last the day is its own question: the phone answer's settings do not
    # exist on a laptop, and the car battery answer was taking "my macbook battery dies quickly"
    # once the phone entry stopped answering it.
    entry("laptop-battery-drain", (("laptop", "macbook", "mac book", "notebook", "chromebook",
                                    "computer", "pc"),
                                   ("battery", "charge", "drain", "draining", "dies", "dying",
                                    "last", "losing", "loses", "drops", "quickly", "fast",
                                    "running out", "runs out", "save", "saving")),
          "Check what is running first: Task Manager on Windows or Activity Monitor on a Mac shows "
          "the battery-hungry app, and browsers with many tabs are usually it. Turn the brightness "
          "down, and turn off Bluetooth and the keyboard backlight when you are out. A laptop "
          "battery is good for about 300 to 500 full charges, so in Settings > Battery (or the "
          "battery menu on a Mac) check its condition: below about 80% of new, a replacement is "
          "£40 to £80 and a shop fits it in an hour.",
          # Whether to repair the laptop or replace it is `laptop-repair-or-replace`'s call, and
          # the battery figure belongs in that answer, not here.
          # A laptop that will not take a charge is the cable, which `laptop-not-charging` owns:
          # "my laptop is dead, wont even charge" ties on score and its words must decide it.
          avoid=("car", "van", "vehicle", "phone", "iphone", "android", "e-bike", "scooter",
                 "wont charge", "won't charge", "not charging", "isnt charging",
                 "isn't charging", "charging", "charger", "plug", "plugged in", "cable",
                 "worth it", "worth", "repair", "replace", "buy new", "new laptop", "buy a new",
                 "or buy", "or do i buy", "second hand",
                 # A laptop that lasts the day is a good thing to have, not a fault: "is there a
                 # laptop with a good battery" is a buying question, and this entry answered it
                 # with the drain tips for a laptop the speaker does not own yet.
                 "with a good", "a good battery", "good battery", "which laptop", "what laptop",
                 "recommend", "best laptop", "cheapest", "budget")),
    entry("laptop-not-charging", (("laptop", "macbook", "mac book", "notebook", "chromebook"),
                                 ("not charging", "wont charge", "won't charge", "charge",
                                  "charger", "plug", "power", "dead", "flat")),
          "Swap the cable first and then the brick, in that order, because the cable is the part that "
          "breaks: try the charger in another socket and check the light on the brick comes on. If "
          "the laptop only runs when plugged in, the battery has failed; a new one is £40 to £80 and "
          "a shop fits it in an hour.",
          avoid=("slow", "hot", "overheating", "battery health", "buy", "worth", "repair",
                 # "is it safe to leave my laptop charging overnight" is the habit, not a
                 # laptop that will not take a charge
                 "safe to leave", "safe to charge", "leave it charging", "leave it on charge",
                 "leave my laptop charging", "leave my laptop on charge")),
    entry("phone-wont-turn-on", (("wont turn on", "won't turn on", "wont switch on",
                                  "won't switch on", "wont start", "dead", "black screen",
                                  "screen is black", "screen went black", "screen has gone black",
                                  "screen stays black", "nothing happens", "not turning on",
                                  "not coming on",
                                  # The now-and-then forms were here for a round and they were in
                                  # the wrong row: this one's answer is "charge it for half an
                                  # hour", which is advice for a phone that is dead, and a screen
                                  # that blinks black now and then is a phone that is plainly
                                  # alive. They are phone-black-now-and-then's, below.
                                  "stuck on the apple logo", "apple logo", "stuck on the logo",
                                  "boot loop", "keeps restarting", "stuck on a black screen",
                                  # A phone that has died is this row, and "my phone has died"
                                  # was answered by the bereavement card: the same word, and the
                                  # device is what tells them apart. The phrases are spelled out
                                  # with the device in them, because a bare "has died" is the
                                  # person in "my mum has died and i need to sort her phone".
                                  # Only the tenses that name a phone dead right now are here.
                                  # "phone is dead" already has the repair-cost card, and a bare
                                  # "my phone died" is a battery that did not last the day (deck
                                  # rows phonedead-01 and dl-04): "charge it for half an hour" is
                                  # the wrong first step there, and on the follow-up turn it says
                                  # the same paragraph twice, word for word. A day and a half
                                  # later is the other reading: "my phone died yesterday" is a
                                  # phone that has been off since, which is the charger and the
                                  # power button, not the app that ran it down.
                                  "phone has died", "phone died last night",
                                  "phone died overnight", "phone died this morning",
                                  "phone died yesterday", "phone died today",
                                  "phone died this afternoon",
                                  "phone has died on me", "handset has died", "handset died",
                                  "it has died", "it died on me",
                                  "screen is blank", "screen has gone blank", "screen is frozen",
                                  "screen has frozen", "frozen screen",
                                  # A phone that is on but has stopped answering gets the same
                                  # power-button sequence, and this row's answer is the one written
                                  # for a handset - the no-power card next door talks about a
                                  # laptop's charger and power board.
                                  "frozen", "has frozen", "froze", "is frozen", "locked up",
                                  "unresponsive", "not responding", "stopped responding",
                                  "nothing works",
                                  # A restart asked for, in any wording at all. "how do i
                                  # restart my phone", "restarting my iphone", "i need to reboot my
                                  # phone" and "does a restart fix it" had no answer, because the
                                  # device rows below only knew the words for a dead handset. The
                                  # second group of this key still needs a phone word, so the
                                  # general verb can live here; the phone that restarts on its own
                                  # is the switching-off row's, and the avoid list below holds that
                                  # reading off.
                                  "restart", "restarts", "restarting", "reboot", "reboots",
                                  "rebooting", "soft reset", "a restart"),
                                 PHONE_KINDS + ("screen",)),
          "Charge it for half an hour on a cable you know works, then hold the power button for ten "
          "seconds: on an iPhone, press volume up, volume down, then hold the side button until the "
          "Apple logo shows. If nothing happens at all, try a different charger and leave it an hour "
          "before you assume the worst.",
          avoid=("webcam", "zoom", "teams", "meet", "camera", "video call", "screen share",
                 "tv", "television", "telly", "monitor", "laptop", "desktop", "computer",
                 "kindle", "watch", "projector",
                 # "the screen" with no device named is a set in the corner more often than a
                 # handset, and it is the phrase that ties this row with screen-blank's key:
                 # "the screen keeps going black" wants the source checked, not a charger.
                 "the screen", "my screen",
                 # A black screen while the call is going on is the proximity sensor, not a flat
                 # battery: the phone is plainly on, since it is in the middle of a call. That
                 # row is phone-black-in-a-call.
                 "in a call", "on a call", "during a call", "make a call", "making a call",
                 "answer a call", "answering a call", "when i answer", "when i talk",
                 "talking on the phone", "on the phone",
                 # A phone that comes on and its screen blinks is not a flat battery, and
                 # "charge it for half an hour" is the wrong thing to tell someone whose phone is
                 # already on. A screen that goes black now and then is its own row.
                 "keeps going black", "going black", "goes black", "go black", "going blank",
                 "goes blank", "flashes black", "blinks", "now and then", "on and off",
                 "every so often", "sometimes goes",
                 # A phone that is dead by the afternoon is a battery that does not last, and
                 # "charge it for half an hour" is the wrong answer to a phone that plainly
                 # turns on: the times of day and the drain words leave those lines alone.
                 "by four", "by noon", "by midday", "by lunchtime", "by the afternoon",
                 "by the morning", "every afternoon", "every day", "each day", "drains",
                 "draining", "runs out", "run out", "doesnt last", "doesn't last",
                 "lasts all day", "all day",
                 # A phone that restarts on its own is a battery or a heat fault, and
                 # "charge it for half an hour, then hold the power button" is not the answer to
                 # a handset that is plainly coming on by itself. Those lines are the
                 # switching-off row's, so the self-restart is fenced here.
                 "itself", "by itself", "on its own", "randomly", "turns itself off",
                 "turns itself on", "turned itself off", "switches itself off", "shuts itself",
                 "keeps turning off", "keeps switching off")),

    # --- phone repairs and moving on ----------------------------------------
    # The first group is the thing and the second is what happened to it or what the person is
    # deciding, and the split is what the scorer needs: a word is spent once, so a group that
    # holds both the thing and its fault spends "cracked" on the subject and never counts it
    # again. Written the other way ("glass" and "cracked" in the first group, "cracked" in the
    # second) a line that says the glass once - "i cracked the glass on my phone" - reached one
    # signal only and was answered with a nod.
    #
    # "my phone is cracked" is the same fault with the screen left unsaid, and the row has to
    # answer it. The bare word "phone" cannot do that job: the phone is also what is replaced,
    # traded in or insured, and with "phone" in the group "should i get it replaced" and "should
    # i replace my phone" were told to put a screen protector on it. So the phone is only here
    # with its fault attached - "phone cracked", "cracked phone" - and a line that names the
    # phone and nothing about its glass stays the question it was.
    entry("phone-cracked-screen", (("screen", "display", "glass",
                                    # the case is named the way people name it, so a break in
                                    # it reaches the row that knows it is the cheap part
                                    "phone case", "phone cases", "mobile case", "phone cover",
                                    "phone covers", "case on my phone", "case for my phone",
                                    "bumper case",
                                    "phone screen", "iphone screen", "mobile screen",
                                    "phone glass", "phone cracked", "cracked phone",
                                    "phone smashed", "smashed phone", "phone is cracked",
                                    "phone is smashed", "phone has cracked", "phone cracked",
                                    "cracked my phone", "cracked my iphone", "smashed my phone",
                                    "cracked the phone", "broke my screen"),
                                   ("cracked", "crack", "cracks", "smashed", "broken", "broke",
                                    "worse",
                                    "spread", "fix", "repair", "cost", "damaged",
                                    # a scratch is the same phone question as a crack - back it
                                    # up, protect it and get it quoted - and without the word
                                    # "how do i remove a scratch from my phone screen" punts
                                    "scratch", "scratches", "scratched",
                                    # deciding whether to mend it or swap it is the same phone
                                    # question: "should i replace the glass or the whole
                                    # screen" and "can i replace just the glass on my phone"
                                    # name the screen and no fault word, and the row never came
                                    # within reach of them.
                                    "replace", "replacing", "replacement", "swap",
                                    "whole screen", "new screen",
                                    # the same row asked before the glass breaks: "how do i
                                    # protect my phone screen" was a shrug, and "how do i stop my
                                    # phone screen from cracking again" was told to put a protector
                                    # on the crack it has not got yet. The words are here, and the
                                    # reply reads which of the two halves the person is asking.
                                    "protect", "protecting", "protection", "prevent", "preventing",
                                    "shatter", "shattering", "guard", "keep it safe")),
          _the_phone_screen,
          # a pair of spectacles, another glass in the house and a price asked about a phone are
          # three lines this key would otherwise take, and none of them is a cracked screen
          guard=_the_glass_in_a_phone,
          avoid=("laptop", "computer", "pc", "monitor", "tv", "television",
                 # a watch face and a tablet screen are their own rows
                 "tablet", "ipad", "watch", "smartwatch", "kindle",
                 # the phone itself, in the senses that are not its glass: trading it in,
                 # upgrading it, insuring it
                 "trade in", "trade-in", "upgrade", "insurance", "insure", "contract",
                 "pay monthly", "sim only", "trade", "sell it", "sell my phone")),
    # "my phone broke" and "my phone is broken, can it be fixed" reached the money answer, because
    # "broke" reads as skint, or a stock "Got it". The one thing a person wants is whether it can
    # be fixed and what each repair costs, so the entry triages the common faults by price.
    entry("phone-broken",
          (("phone", "iphone", "android", "handset", "mobile"),
           ("broke", "broken", "bust", "damaged", "fix", "fixed", "fixable", "repair",
            "repairable", "replace", "replacement", "new one", "dead", "smash", "smashed",
            "knackered", "not working")),
          "Nearly every phone is fixable, and every repair is cheaper than a new handset: a screen "
          "is £60 to £120 at a local shop, a battery £35 to £70, a charging port £30 to £60. Back it "
          "up to the cloud first, then get a quote from a local shop and one from the maker, and "
          "check your home insurance excess or a card's purchase protection, which sometimes covers "
          "accidental damage.",
          # a cracked screen, water in the phone, a phone that will not turn on and a phone that
          # will not charge each have their own fix; a laptop, a watch and a pair of glasses are
          # not phones at all
          avoid=("screen", "cracked", "crack", "water", "wet", "toilet", "sink", "rice",
                 "turn on", "wont turn", "will not turn", "switched off", "black screen",
                 "charge", "charging", "charger", "port", "laptop", "macbook", "computer",
                 "tablet", "ipad", "watch", "glasses", "spectacles", "headphones",
                 "contract", "insurance policy", "upgrade", "tariff", "sim", "number",
                 "backup", "back up", "data", "photos", "lost", "stolen",
                 # the cheaper-of-two choice is phone-repair-or-replace's line, not this one
                 "cheaper", "worth fixing", "or replace", "or repair", "repair or", "replace or",
                 "worth it", "worth putting",
                 # a landline is a wire into the house, not a handset to take to a shop
                 "landline", "home phone", "house phone", "phone line", "dial tone",
                 "dialling tone", "tone", "broadband", "router", "socket", "extension"),
          bias=1),
    entry("power-bank", (("power bank", "portable charger", "battery pack", "powerbank"),
                         ("buy", "good", "worth", "which", "recommend", "best", "get one",
                          "should i get", "what", "about", "travel", "flight", "plane",
                          "airport", "carry", "laptop")),
          "A power bank is worth it if you are out all day: look for 10,000mAh (about two full "
          "charges, pocket-sized) and at least 20W output, so it charges quickly rather than "
          "trickling. Anker and Belkin are the reliable ones, around £20 to £35; check it has USB-C "
          "output for a modern phone, and keep it in your hand luggage on a plane."),
    # "how do i use a power bank" is a use question, so it gets the plugging-in sentence first
    entry("power-bank-use", (("power bank", "portable charger", "battery pack", "powerbank"),
                             ("use", "how do i use", "how to use", "use it", "plug", "charge",
                              "connect", "turn on", "not working", "wont charge")),
          "Plug your phone into the power bank's output port (usually marked OUT or USB-C) with its "
          "own cable, then press the button on the bank: the lights show how much charge is left, "
          "two to four of them. If nothing happens, the port may be the input only, so try the other "
          "one, and a phone that still says it is not charging usually wants a different cable.",
          ask=("use", "how do i use", "how to use", "use it", "plug", "connect", "turn on",
               "not working", "wont charge")),
    entry("phone-lost", (("lost", "misplaced", "stolen", "find", "left", "nicked", "snatched",
                          "robbed", "mugged", "pickpocketed", "went missing", "gone missing",
                          "cant find", "cannot find", "can't find",
                          # the act in the words of someone whose phone has already gone: "someone
                          # stole my phone at the pub" names the person and the act, and neither
                          # was a word this row held, so the line reached nothing at all.
                          "stole", "stole my", "someone stole", "someone took", "took my phone",
                          "my phone is gone", "my phone has gone", "phone went missing",
                          "my phone was taken", "my phone got taken", "pinched",
                          "my phone went"),
                         ("phone", "iphone", "android",
                                                                     "device", "mobile")),
          "Use Find My on an iPhone (iCloud.com/find from any browser) or Find My Device for "
          "Android: it shows the location, rings it and can lock or wipe it remotely. Ring your "
          "network to block the SIM, and change your password for anything the phone was signed "
          "into.",
          # "i left my phone in a taxi" is this, not a bedtime question about chargers.
          avoid=("nan", "gran", "granny", "mum", "dad", "mother", "father", "husband", "wife",
                 "partner", "brother", "sister", "friend", "passed", "died", "death", "funeral",
                 "contract", "cancel", "lost my job", "lose weight", "lost weight",
                 # the phone is here and something about it has gone: a data allowance, a battery,
                 # the signal or the storage. "my mobile data has gone" and "my phone battery is
                 # gone" are those, and neither is a phone that was taken.
                 "data", "battery", "signal", "wifi", "wi-fi", "storage", "memory",
                 "photos", "contacts", "charger", "charging", "screen", "cracked",
                 "broken", "slow", "speaker", "sound", "microphone", "camera")),
    entry("new-phone-transfer", (("new phone", "upgrade", "switch phone"), ("transfer", "move",
                                                                           "photos", "contacts",
                                                                           "data", "old phone",
                                                                           "everything", "set up",
                                                                           "setup")),
          "Both phones do it for you: on an iPhone, put the new one next to the old and follow the "
          "Quick Start prompt; on Android, use the cable or the copy-apps option during setup. Do "
          "it while both are plugged in, because moving photos over wifi drains the old phone."),
    entry("tv-screen-cracked", (("tv", "television", "telly", "monitor", "screen"),
                                 ("cracked", "crack", "smashed", "broken screen", "crack in",
                                  "cracked screen", "line across", "lines across", "black patch",
                                  "smashed screen", "cracked panel")),
          "A cracked panel is not a repair, it is a new panel, and on anything under about £500 "
          "that is more than the set is worth: check the price of the same size before you book "
          "anything. If it is a line or a band rather than broken glass, power it off at the wall "
          "for a minute and check the HDMI lead first, and claim on household accidental damage "
          "cover if you have it, which is usually the cheapest way to a replacement.",
          avoid=("phone", "iphone", "android", "laptop", "tablet", "ipad", "windscreen",
                 "window", "glass", "spectacles", "glasses",
                 # a blood pressure or glucose monitor is a health device, not a screen
                 "blood pressure", "glucose", "heart", "oxygen", "thermometer", "baby", "health"),
          bias=1),
    # A TV or a monitor that goes black is the other half of the mould answer in home.py: a
    # screen and a wall both "go black", and only the surface tells them apart. _mould stands
    # down for a device with no wall, window or room named, and this row answers it. The room
    # words are in the avoid here as well, because a line that names a surface is a mould line
    # however it was worded: "the wall behind my monitor has gone black" keeps the mould spray.
    entry("screen-blank", (("tv", "television", "telly", "monitor", "screen", "display"),
                           ("gone black", "went black", "going black", "goes black",
                            "go black",
                            "blank screen", "screen is black", "black screen", "no picture",
                            "keeps going black", "black for a second", "screen goes black",
                            "screen has gone black",
                            # "my screen is blank" and "my telly has gone off" were both
                            # "I'm listening": the blank forms were here only as "blank
                            # screen", and a set that has gone off names no picture at all.
                            # The set is the subject in the first group, so a food that has
                            # gone off (the milk) never reaches this row.
                            "screen is blank", "screen has gone blank", "screen went blank",
                            "screen goes blank", "screen is white", "white screen",
                            "gone off", "has gone off", "went off", "keeps going off",
                            "turned itself off", "switched itself off", "wont come on",
                            "won't come on", "wont switch on", "won't switch on",
                            "no signal", "says no signal")),
          "Check the source before the set: press the input or source button on the remote and "
          "make sure it is on the socket the box is plugged into, then push the HDMI lead in at "
          "both ends and swap it for another one if you have a spare. If the sound carries on "
          "while the picture dies, the backlight is the usual fault on a TV; on a monitor it is "
          "more often the cable, a sleeping screen saver or the sleep timer. Power it off at the "
          "wall for a whole minute before you decide it needs repairing.",
          avoid=("phone", "iphone", "android", "handset", "laptop", "macbook", "tablet", "ipad",
                 # a computer is the laptop row's: its cure is a power button and an external
                 # display, not an input button on a remote
                 "computer", "pc", "mac",
                 "cracked", "crack", "smashed", "windscreen",
                 # a surface is a mould line, not a screen: the same words describe both
                 "mould", "mold", "damp", "wall", "walls", "ceiling", "window", "wallpaper",
                 "paint", "skirting", "grout", "tile", "tiles", "sealant", "silicone",
                 "bathroom", "bedroom", "kitchen", "room", "floor", "plaster", "woodwork",
                 "behind the"),
          ),
    entry("phone-water-resistant", (("water resistant", "water resistant", "waterproof",
                                     "water proof", "ip68", "ip67", "resistant to water",
                                     "water resistance",
                                     # "can i take it in the pool" is this question, and the
                                     # place alone never reached it: what decides is the rating,
                                     # so the places belong in this key beside the numbers.
                                     "in the pool", "in a pool", "into the pool", "in the sea",
                                     "into the sea", "in the bath", "into the bath",
                                     "in the shower", "into the shower", "in the rain",
                                     "swimming", "swim", "a swim", "the beach", "the lake",
                                     "submerged", "splash", "get it wet", "gets wet"),
                                    ("phone", "iphone", "android", "samsung", "watch", "it",
                                     "mine", "pixel", "is my")),
          "Most phones sold since about 2017 are IP67 or IP68, which means they survive a splash or "
          "a dunk in fresh water, not a swim and not the sea, and the seals weaken with age and "
          "after a repair. So rain and a wet hand are fine, and the bath, the beach and a hot shower "
          "are not; a wet charging port is the commonest way people damage one, so let it dry "
          "before you plug it in.",
          # "is it ok to swim", "can i swim" and "is it ok to go swimming" are about the person
          # going in the water, and on main 4ed19296 the bare "it" in this key read them as a
          # phone: the reply was IP67. The key's swim and pool words only mean a device when the
          # line names one, so this card answers only when a device or a rating is in the line.
          ask=("phone", "phones", "mobile", "iphone", "android", "samsung", "pixel", "device",
               "waterproof", "water proof", "water resistant", "water resistance", "ip67",
               "ip68", "watch", "smartwatch", "fitbit", "garmin", "pocket", "splash",
               "submerged"),
          # A phone that has already been in the water wants the recovery card, not the rating:
          # how far the rating goes is no use to someone whose phone is wet now.
          avoid=("watch", "smartwatch", "fitbit", "garmin", "apple watch", "fitness tracker",
                 # a waterproof jacket, coat or pair of boots is a garment question: "is a
                 # waterproof jacket worth it" was answered with the IP67 rating of a phone
                 "jacket", "jackets", "coat", "coats", "parka", "shell", "trousers", "boots",
                 "trainers", "gaiters", "fleece", "pram", "pushchair",
                 "fell in", "dropped in", "dropped it", "dropped my", "got wet", "gone in",
                 "went in", "sank", "soaked", "spilled", "spilt", "washed it",
                 # someone else put it there, and a wet phone is a wet phone whoever did it
                 "knocked", "put it in", "put my phone", "put my mobile", "in the water",
                 "baby", "babies", "newborn", "infant", "toddler", "child", "children", "kid",
                 "kids",
                 "into the water",
                 # the bare "it" in this entry's key read "how long does it take to learn to
                 # swim" as a phone line: the swimming lesson is not a waterproof rating
                 "learn to swim", "learn swimming", "swimming lessons", "swim lessons",
                 "how long does it take to learn",
                 # "is it ok to run in the rain" is about the person going out, not about the
                 # phone in their pocket: with "in the rain" in the key and the bare "it" in the
                 # second part this card won the tie and answered a running question with IP67.
                 "run", "running", "jog", "jogging", "cycle", "cycling", "walk", "walking",
                 "hike", "hiking", "commute", "commuting"),
          bias=2),
    # A watch is rated differently from a phone: 5ATM is waterproof for a swim, IP68 on a phone is
    # not, so the watch gets its own answer instead of the phone's number.
    entry("watch-water-resistant", (("watch", "smartwatch", "fitbit", "garmin", "apple watch"),
                                    ("water resistant", "waterproof", "water proof", "in water",
                                     "in the pool", "swimming", "shower", "swim", "5atm",
                                     "bath", "sea")),
          "A watch marked 5ATM or 50m is fine for a swim and a shower, 3ATM is a splash only, and "
          "IP68 means it survives a dunk rather than a swim. No watch likes hot water or soap, "
          "because steam and shampoo get past the seals, and the seals age - so a shower or a pool "
          "is fine, a hot bath or a dive is not.",
          bias=1),
    entry("phone-water", (("phone", "iphone", "android"),
                          # A phone that is already wet is asked about in the shapes people type:
                          # what happened to it ("water in my phone", "soaked"), what they want
                          # out of it ("get water out of", "dry out") and what they fear is
                          # ("ruined from water"). None of those named one of the cards' words,
                          # so the line fell through to a shrug - or, worse, to the cleaning
                          # row: "how do i get water out of my phone" was told to blot the mark
                          # and wash it at the hottest the care label allows.
                          ("in water", "in the water", "into the water",
                           "water in", "water got in", "water out of",
                           "get the water out", "get water out", "dropped in", "fell in",
                           "got wet", "wet", "soaked", "soaking", "damp", "dunked",
                           "waterlogged", "water damage", "water damaged", "ruined from water",
                           "ruined by water", "dry out", "drying out", "dried out",
                           "toilet", "sink", "bath", "puddle", "spilled", "spilt",
                           "washing machine", "through the wash", "water resistant",
                           "waterproof", "water proof", "shower", "swimming", "in the pool",
                           "dry", "submerged",
                           # The thing it fell in is not the question, but the two rows that own
                           # the thing will answer it if left to: "i dropped my phone in the
                           # toilet what do i do" was explained a cistern flap, and "should i put
                           # my phone in rice" was told to rinse rice until the water ran clear.
                           # Naming the rice and the sea in the key is what keeps the phone's own
                           # card on top of them, and the sea is where a phone must not go.
                           "rice", "in rice", "bag of rice", "sea", "in the sea", "beach",
                           "sand", "salt water", "seawater", "toilet water",
                           # the wash is the commonest way a phone gets soaked, and "washed"
                           # is not "washing machine": the phrase had to be named
                           "washed", "in the wash", "in my jeans", "left it in my jeans")),
          "Turn it off and keep it off: do not charge it, and do not put it in rice, which just "
          "adds dust. Wipe it, shake out the port gently and leave it somewhere warm and airy for "
          "at least 24 hours before you switch it on. A phone sold as water resistant (IP67 or "
          "IP68) survives a splash and a quick drop in the sink, but that rating is tested in "
          "fresh water and no maker covers liquid damage under the warranty, so keep it out of the "
          "sea, the pool and the shower.",
          # A phone in the bath is the phone's problem first, even when a cat, a dog or a toddler
          # put it there: those entries are about the animal, and this line is about the phone.
          # The same goes for the thing it fell in - a toilet, a bag of rice, the sea - because
          # those have rows of their own that say nothing about a wet phone.
          bias=3,
          # A question about taking a phone somewhere is the rating, not the recovery card: the
          # phone has not gone in yet, and "turn it off and keep it off" tells someone to dry a
          # phone that is still in their hand. "can i take my phone in the pool" got that card.
          avoid=("can i take", "can i bring", "can i use", "can i get it wet", "is it safe",
                 "is it ok to", "ok to take", "safe to take", "should i take", "shall i take",
                 "will it be ok", "will it survive"),
          # "will it be alright" after "i dropped my phone in the sink" is answered by the card
          # above, which the person is looking at: every sentence of it has been said. This is
          # the verdict written as a line of its own for that follow-up, and it is the honest
          # one - a wet phone that stays off usually comes back, and the data usually survives
          # even when the phone does not.
          outcomes=(("survives",
                     "Usually yes, if it stays off while it dries: most phones that get wet come "
                     "back once they have had their day and a half in the air, and the photos and "
                     "messages can be taken off even when the phone will not start."),)),

    # Everything else with a battery in it, in the same water: earbuds through the wash, a watch
    # in the sink, a tablet in the bath. The phone and the laptop have their own answers, and
    # these gadgets want the same first move - switch it off before anything is charged - in a
    # line short enough for someone holding a dripping device. On main bf2c9a11 every one of
    # these was a shrug or a nod: "i washed my airpods" was answered "Nice one - are you pleased
    # with it?" and "my watch got wet" with "I'm listening", which is no use to someone whose
    # watch is full of water.
    entry("wet-gadget", (("earbuds", "earbud", "airpods", "airpod", "headphones", "headphone",
                          "earphones", "watch", "smartwatch", "fitbit", "garmin", "apple watch",
                          "ipad", "tablet", "kindle", "e-reader", "ereader", "remote",
                          "remote control", "controller", "gamepad", "console", "camera",
                          "speaker", "mouse", "power bank", "charger", "hearing aid",
                          "hearing aids"),
                         ("wet", "in water", "water in", "water got in", "got water", "soaked",
                          "soaking", "spilt", "spilled", "sank", "dunked", "in the water",
                          "into the water", "washing machine",
                          "through the wash", "in the wash", "washed", "wash", "toilet", "sink",
                          "bath", "bathroom", "puddle", "pool", "sea", "river", "lake", "pond",
                          "submerged", "water damage")),
          "Turn it off if it has a switch and leave it off, and do not plug it in to charge: "
          "power through a damp board is what does the damage, not the water itself. Shake the "
          "water out, dry the "
          "outside with a cloth and leave it somewhere warm and airy with the openings facing "
          "down for two days - rice does nothing except leave grit in the ports, and a radiator "
          "or an oven is worse than the water. A wet battery can fail weeks later, so if it stops "
          "charging, or a speaker or a button misbehaves once it is dry, a repair shop is the "
          "next step.",
          bias=2,
          # how far a rating goes is a question about taking it in, not about getting it out:
          # "is my watch waterproof" and "can i swim with my airpods" are the rating cards', and
          # so is a wash of a dry machine.
          avoid=("waterproof", "water proof", "water resistant", "water resistance", "ip67",
                 "ip68", "5atm", "3atm", "swim", "swimming", "shower", "rain",
                 # a wash that has not happened yet is a cleaning question: "can i wash my
                 # earbuds" asks whether the tap is safe, and the answer is a cloth, not a
                 # recovery card for a device that is dry.
                 "can i wash", "should i wash", "is it ok to wash", "ok to wash", "safe to wash",
                 "how do i wash", "how to wash", "can i put it in water", "can i get it wet",
                 "can i put them in water", "clean",
                 "cleaning", "clean it", "wipe", "wiping", "dust", "dusty", "crumb", "crumbs",
                 "sticky", "battery life", "battery drains", "how long does the battery",
                 "strap", "band", "review", "worth it", "should i buy", "which one",
                 "price", "how much", "instructions", "manual", "connect to wifi"),
          # "will they be alright" after "i washed my airpods" asks about the buds the card above
          # is drying, and the answer is the card's own last sentence, written for the ask: a
          # device that stayed off while it dried usually comes back, and the ones that do not
          # are the ones charged while wet.
          outcomes=(("survives",
                     "Usually, yes: an earbud, a watch or a remote that stayed off while it dried "
                     "for two days works again more often than not, and the ones that never come "
                     "back are usually the ones that were charged while still damp."),)),
    # --- laptops and computers ----------------------------------------------
    # A machine that turns itself off is nearly always heat; one that keeps asking to restart has
    # an update waiting. "Only when it has been on a while" and "only with teams open" are the
    # same answer, so the heat entry takes the "under load" shapes too.
    entry("laptop-shuts-down", (("laptop", "computer", "pc", "macbook", "desktop"),
                                ("shuts itself down", "shuts down on its own", "shutting itself down",
                                 "turns itself off", "switches itself off", "powers off on its own",
                                 "keeps shutting down", "keeps turning off", "dies after",
                                 "turns off after", "cuts out after",
                                 # the same fault said as a random event: "it shuts down
                                 # randomly", "the pc reboots on its own", "it restarts by
                                 # itself". These were a sleep answer and a shrug.
                                 "shuts down randomly", "shutting down randomly",
                                 "switches off randomly", "turns off randomly",
                                 "reboots on its own", "rebooting on its own",
                                 "restarts on its own", "randomly restarts", "randomly reboots",
                                 "randomly shuts down", "randomly switches off",
                                 # a machine that restarts again and again is the same fault,
                                 # and "my laptop keeps restarting" was a chat line
                                 "keeps restarting", "keeps rebooting", "restarts all the time",
                                 "restarting all the time", "restarts again and again",
                                 "restarting again and again", "restarts every few")),
          "That is nearly always heat: clear the vents and the fan with a can of air, keep it off "
          "soft surfaces, and note whether it happens only when it has been on a while or only "
          "with a heavy app open - that points at the fan or the thermal paste rather than the "
          "battery. If it goes off with no warning and no heat, look up the crash in Event Viewer "
          "(Windows) or Console (Mac) and check the battery health, because a worn battery cannot "
          "hold a heavy load and switches the machine off.",
          bias=1),
    entry("laptop-battery-not-holding", (("laptop", "computer", "macbook", "notebook", "pc"),
                                          ("turns off when i unplug", "turns off when unplugged",
                                           "goes off when i unplug", "shuts off when i unplug",
                                           "switches off when i unplug", "dies when i unplug",
                                           "only works plugged in", "only works when plugged in",
                                           "has to stay plugged in", "without the charger",
                                           "wont turn on without the charger",
                                           "won't turn on without the charger",
                                           "not holding charge", "wont hold charge",
                                           "won't hold charge", "battery is dead")),
          "The battery has reached the end of its life, so replace it: a laptop that dies the "
          "moment the charger comes out cannot hold a load, and no setting will bring it back. "
          "Check the health number first - `powercfg /batteryreport` on Windows, System "
          "Information > Power on a Mac - because a design capacity under about 70% is a "
          "replacement, and a new one is usually £30 to £90 fitted on a Windows laptop and more on "
          "an Apple one.",
          bias=1),
    # A cracked laptop screen is a part, unlike a phone's, and the answer differs by machine.
    entry("laptop-screen-cracked", (("laptop", "macbook", "notebook", "chromebook"),
                                     ("cracked", "crack", "crack in", "smashed", "cracked screen",
                                      "lines across", "line across", "spider", "glass cracked")),
          "A laptop screen is a replaceable part, so do not replace the machine: a Windows laptop "
          "panel is usually £60 to £150 fitted at a local shop, and an Apple one is £150 to £300 "
          "through Apple or a good independent. Back the files up before it goes in, in case the "
          "screen gets worse while you wait, and check household accidental damage cover first - "
          "it often pays for the whole repair.",
          avoid=("black screen", "black", "dark", "dim", "brightness", "flicker", "flickering",
                 "blank", "went off"),
          bias=1),
    entry("laptop-restart-request", (("restart", "reboot", "start again", "restarting"),
                                     ("keeps asking", "keeps telling", "asks me", "asking me",
                                      "wants to", "wont stop", "won't stop", "every day",
                                      "all the time", "again and again", "update", "updates",
                                      "to finish", "to install")),
          "An update is waiting and will keep asking until it is done: save your work, close what "
          "you are in and let it restart once, and give it twenty minutes without touching it. If "
          "it asks again the next day, the update is failing to install - free up disk space "
          "(updates need several gigabytes) and let it run with the charger plugged in.",
          bias=1),
    entry("laptop-fan-loud", (("fan", "laptop", "macbook", "computer"),
                              ("loud", "noisy", "noise", "spinning", "whirring", "runs", "dust",
                               "clean", "mad", "revving", "constant", "constantly", "flat out",
                               "going", "loudly", "sounds like a plane",
                               "like a plane taking off", "sounds like a jet", "like a jet",
                               # once the bathroom extractor stopped taking it, "my computer fan
                               # never stops" had no answer at all: a fan that is always on is
                               # this entry. The phrases carry the word "fan" on purpose - a bare
                               # "all the time" or "always on" took "my laptop screen is glitching
                               # all the time" and "my laptop battery dies all the time" as well.
                               "fan never stops", "fan doesnt stop", "fan doesn't stop",
                               "fan is always on", "fan is on all the time", "fan on all the time",
                               "fan all the time", "fan runs all day", "fan goes all the time",
                               "fan never turns off", "fan never goes off",
                               # and a fan that comes on and off is the same overheated machine,
                               # said as what it does rather than how loud it is: "ok what about my
                               # laptop, the fan keeps coming on" was a shrug. Every phrase carries
                               # the word "fan", because a bare "comes on" is a screen waking up.
                               "fan keeps coming on", "fan comes on", "fan coming on",
                               "fan kicks in", "fan keeps kicking in", "fan spins up",
                               "fan keeps spinning up", "fan revs up", "fan keeps going off",
                               "fan starts up", "fan keeps starting up",
                               # "the fan on my laptop spins up when i open chrome" puts a word
                               # between the two, so the speed-up phrases go in without "fan"
                               "spins up", "spinning up", "revs up")),
          "It is cooling itself because it is hot, so clear the vents with a can of air and check "
          "what is using the processor in Task Manager or Activity Monitor. A four-year-old laptop "
          "often just needs the dust out and new thermal paste (about £40 at a repair shop); if the "
          "noise continues at idle, the fan bearing is going.",
          # a "fan" that names a room or an appliance is not a laptop fan
          avoid=("oven", "cooker", "extractor", "microwave", "hob", "cooker hood", "bathroom",
                 "loo", "toilet", "shower", "ceiling", "kitchen", "tumble dryer", "tumble",
                 "air con", "aircon", "heater", "boiler", "radiator", "car", "van", "desk",
                 "table fan",
                 # "how do i clean my laptop keyboard" is the keyboard answer: keeping "clean" in
                 # the noisy-fan keys stole it.
                 "keyboard", "keyboards", "keys", "crumbs", "spill", "spilled", "sticky",
                 # "how do i clean the blades of a fan" is a room fan being dusted, not a hot
                 # laptop: cleaning words with the parts of a fan in the line are not this entry
                 "blades", "blade", "grille", "guard", "pillowcase", "dusted", "dusting",
                 # a room fan that is noisy is not a hot laptop: "my fan is noisy" got the
                 # cooling-vent card. A fan named as a room or a wall fan takes the line away,
                 # while "my laptop fan is loud" still names the laptop.
                 "ceiling fan", "ceiling fans", "desk fan", "desk fans", "pedestal fan",
                 "floor fan", "tower fan", "room fan", "box fan", "wall fan", "clip fan",
                 "fan guard", "fan cage", "bathroom fan", "kitchen fan",
                 "air circulator", "extractor fan",
                 # a console's fan is `console-noisy`: "my ps5 fan is really loud" was getting the
                 # laptop's vents card
                 "playstation", "ps5", "ps4", "xbox", "nintendo", "switch", "console",
                 "games console")),
    entry("share-a-file",
          (("share", "sharing", "send a link", "give someone access", "let someone see"),
           ("file", "files", "folder", "folders", "document", "doc", "docs", "spreadsheet",
            "album", "photo album", "drive", "onedrive", "icloud", "link", "someone")),
          "In Google Drive or OneDrive, right-click the file or folder, choose Share, then set the "
          "access to Viewer and copy the link - a link on its own only works for people already "
          "signed in to your account. For photos, share the album rather than each picture. For a "
          "document two people are working on, Share and add their email as Editor instead.",
          bias=1,
          # the screen, the wifi password and a folder of photos are different jobs
          # "shares" itself cannot be an avoid word: the verb "share" blooms into it, so it
          # would stand this answer down for every line it is for. Held as phrases instead.
          avoid=("screen", "wifi", "wi-fi", "password", "hotspot", "stocks and shares",
                 "in shares", "buy shares", "sell shares", "investing", "invest in",
                 # "how do i let someone see where i am" is sharing a location, and "someone"
                 # in this row's key caught it: the answer it got was how to share a Drive
                 # folder. A line about where a person is belongs to the phone rows.
                 "where i am", "where im", "where i'm", "my location", "live location",
                 "location sharing", "my whereabouts", "whereabouts", "share my location"),
          ask=("how", "help", "want", "need", "can i", "do i")),

    entry("laptop-not-responding", (("laptop", "computer", "pc", "mac", "macbook",
                                     # a frozen kindle, tablet or chromebook is the same machine
                                     # with the same answer: force it off and start it again. The
                                     # card said "laptop" and so its key only reached laptops, and
                                     # the no-power card took every other device by default.
                                     "tablet", "ipad", "kindle", "e reader", "e-reader", "ereader",
                                     "chromebook", "surface", "desktop"),
                                    ("not responding", "frozen", "froze", "has frozen",
                                     "freezes up", "hangs", "hung up", "won't respond",
                                     "wont respond", "not responding to anything", "completely stuck",
                                     "cursor", "black screen", "locked up", "unresponsive",
                                     "nothing works", "stopped responding", "stuck",
                                     "freezing")),
          "Hold the power button for ten seconds to force it off, wait a few seconds and start it "
          "again; you lose unsaved work but nothing else. If it happens often, check free disk space "
          "and start it without the extras (Safe Mode) to see whether an update or a startup app is "
          "the cause.",
          # a phone that has frozen is the phone turn-on row's, which starts with the charge and the
          # volume-up, volume-down sequence rather than a laptop's power button
          avoid=("phone", "iphone", "android", "handset", "mobile")),
    entry("laptop-slow", (("laptop", "computer", "pc", "macbook"),
                          ("slow", "sluggish", "laggy", "slow down", "got slow", "getting slow",
                           "faster", "speed up", "speed it up", "quicker", "snappier",
                           # "my laptop is running slow" is this machine being slow, but
                           # "running" and "runs" are the loud fan row's words, and on a tie it
                           # took the line and answered a slow laptop with the dust answer. The
                           # phrase weighs more than the two loose words it is made of.
                           "running slow", "runs slow", "is slow", "running slowly",
                           "going slow", "slow to open", "slow to load", "slow to respond")),
          "Check the disk is not full (under 10% free slows Windows badly), then cut what starts "
          "with the machine: Task Manager > Startup, and turn off the things you do not need. If it "
          "has a spinning hard drive, swapping it for an SSD is the single best £40 you can spend; "
          "adding RAM helps if you always have many tabs open."),
    # Four things a Mac owner is asked about that were a shrug: a slow machine, emptying the
    # bin, an app that will not close, and the browser that opens links. They are separate
    # entries because the words are the whole question - "empty the trash" is not a slow
    # machine - and each names the machine, so a Windows line keeps its own answer.
    entry("mac-slow", (("mac", "macbook", "imac", "mac book", "apple computer", "macs"),
                       ("slow", "sluggish", "laggy", "slow down", "got slow", "getting slow",
                        "faster", "speed up", "speed it up", "quicker", "snappier")),
          "Open Activity Monitor (Applications > Utilities) and sort by % CPU, then by Memory: the "
          "app at the top is what is eating the machine, and quitting it is the whole fix more "
          "often than not. Then check disk space under the Apple menu > System Settings > General "
          "> Storage - a Mac under about 10% free slows to a crawl - and turn off what starts at "
          "login under General > Login Items. If it has been slow since an update, restarting it "
          "once clears the leftovers.",
          bias=2),
    entry("mac-empty-trash", (("trash", "trash can", "bin", "recycle bin", "rubbish bin"),
                              ("empty", "emptied", "emptying", "clear", "clearing", "delete",
                               "deleted", "how do i", "how to", "mac", "macbook", "windows",
                               "free up", "space",
                               # the machine in the sentence decides which bin is meant: "the
                               # recycle bin is full on my laptop" was the electrical-waste card
                               "laptop", "computer", "pc")),
          _empty_trash,
          guard=_the_bin_is_the_one_on_the_computer,
          # a bin day, a wheelie bin and a bin lorry are the other kind of bin
          avoid=("wheelie", "bin day", "bin collection", "bin men", "binman", "bin lorry",
                 "outside", "garden waste", "kitchen bin", "food waste", "rubbish day",
                 "bins go out", "put the bins",
                 # a bin that smells, has maggots or needs washing is the kitchen bin, and the
                 # cleaning table answers it: "how do i stop my bins smelling" was telling
                 # people to right-click the Recycle Bin on the desktop
                 "smell", "smells", "smelling", "smelly", "stink", "stinks", "stinking",
                 "maggot", "maggots", "flies", "fly", "bleach", "liner", "liners",
                 "bin bag", "bin bags", "nappy", "nappies", "compost", "under the sink", "lid",
                 # a bin in a neighbour's parking space, a bin left out on the kerb and a bin
                 # nobody emptied are all the wheelie bin: "he leaves his bins in my parking
                 # space" was answered with right-click the Recycle Bin on the desktop. Only the
                 # places and the rounds are named, never a bare "my bin" or "the bin", because
                 # an avoid phrase matches a word form and "my bins" would stand this row down for
                 # "how do i empty my bin on a mac"
                 "neighbour", "neighbours", "neighbor", "neighbors", "parking", "car park",
                 "kerbside", "kerb", "curb", "pavement", "driveway", "front garden",
                 "collected", "collection", "collect", "council", "fortnight", "fortnightly",
                 "weekly"),
          # a bin in the kitchen is washed, a bin on a computer is emptied, so the emptying words
          # are the gate: "how do i clean my bin" and "how do i wash my bin" are the cleaning
          # table's, and the desktop shapes keep this answer.
          ask=("empty", "emptied", "emptying", "clear", "clearing", "cleared", "delete",
               "deleted", "deleting", "free up", "space", "full", "mac", "macbook", "windows",
               "desktop", "trash", "recycle", "icon", "downloads", "disk", "storage",
               "see", "what is in", "whats in", "look in", "inside", "get back", "undo")),
    entry("mac-force-quit", (("force quit", "force close", "force stop", "force it to close",
                              "wont quit", "won't quit", "wont close", "won't close",
                              "app is frozen", "app frozen", "app wont close"),
                             ("app", "application", "program", "mac", "macbook", "window",
                              "how do i", "how to", "browser", "safari", "it")),
          _force_quit,
          bias=1,
          # A zip that will not close on a coat is clothing.py's stuck-zip: "wont close" alone
          # was answering a stuck zip with Task Manager. "close" here means an app, so the things
          # with a zip in them stand this row down.
          avoid=("zip", "zips", "zipper", "zippers", "coat", "jacket", "jeans", "trousers",
                 "dress", "skirt", "boots", "boot", "suitcase", "sleeping bag", "hoodie",
                 "curtain", "curtains", "wardrobe", "fastener",
                 # A mussel that will not close is a shellfish question, not a frozen window:
                 # "is it safe to eat mussels that wont close" was answered with Task Manager,
                 # which is the one place a wrong card could do harm. Anything alive that closes
                 # is the same trap as the zip, so shellfish stand this row down the same way.
                 "mussel", "mussels", "clam", "clams", "oyster", "oysters", "scallop",
                 "scallops", "shellfish", "seafood")),
    entry("default-browser-change", (("default browser", "default web browser",
                                      "default app for links", "open links in"),
                                     ("change", "set", "make", "switch", "choose", "how do i",
                                      "how to", "different", "another", "which", "mac",
                                      "windows", "iphone", "phone")),
          _default_browser,
          bias=1),
    entry("laptop-battery-health", (("laptop", "macbook", "notebook", "computer", "mac"),
                                     ("battery",)),
          _battery_health,
          bias=2,
          avoid=("good", "best", "longest", "buy", "buying", "choose", "recommend", "which",
                 "last longer", "lasts longer", "battery life", "lifespan", "how long",
                 "how much", "cost", "price", "cheap",
                 # a battery that drains while the machine is off is not a health check
                 "shut down", "shutdown", "shut it down", "while off", "closed", "lid",
                 "overnight", "goes flat", "drains",
                 # and a battery that dies quickly or will not last the day is the drain
                 # answer's, which can only get it if this one stands aside
                 "dies", "dying", "drain", "draining", "quickly", "fast", "save", "saving",
                 "running out", "runs out", "loses", "losing", "drops", "last the day",
                 # "is it worth getting a new laptop or just a new battery" is the
                 # repair-or-replace question, not a health check.
                 "new laptop", "new machine", "or just", "worth getting", "worth it",
                 "replace the laptop", "new computer")),
    # A price question wants the price first, so it gets its own first sentence.
    entry("laptop-battery-cost", (("laptop", "macbook", "notebook", "computer", "mac"),
                                  ("how much is", "how much are", "how much does", "cost",
                                   "price", "cheap", "cheapest", "how much for")),
          "£40 to £90 for the battery itself, and £60 to £120 fitted at a repair shop; the maker "
          "charges most, around £120 to £180. Most laptop batteries are held in with screws and a "
          "five-minute job on older machines, so a £60 battery and a screwdriver is usually the "
          "cheap way to get three or four more years out of it.",
          bias=2,
          # "how much does a laptop cost" is the machine, not the battery: the parts are
          # alternatives, not all required, so the battery has to be asked for.
          ask=("battery", "batteries", "replacement"),
          avoid=("phone", "iphone", "ipad", "tablet", "car", "watch", "smoke alarm", "vape")),
    entry("laptop-battery-care", (("laptop", "macbook", "notebook", "computer", "mac"),
                                  ("last longer", "lasts longer", "battery life", "lifespan",
                                   "how long does the battery", "battery last", "battery care",
                                   "look after", "healthy")),
          "Keep it cool and keep it off 100%: heat is what ages a laptop battery, so use it on a "
          "hard surface with the vents clear, and switch on the maker's charge limit (80% in the "
          "Mac or Lenovo settings, Battery care in Asus) if it mostly lives on a desk. A laptop "
          "battery lasts three to five years; expect about 500 to 1000 full charges before it "
          "drops to 80% of new.",
          avoid=("needs replacing", "replace", "replacing", "dead", "wont charge", "cost",
                 "how much", "apple care", "applecare", "warranty", "insurance", "cancel",
                 "extended cover")),
    # How long the device is worth keeping. "How long should a laptop last" and "how long do
    # phones last" were answered with the battery tips, because "last" is in the drain row's keys
    # (a laptop that will not last the day is its own question) and nothing said the clock instead.
    # One row for phone, tablet and laptop: the numbers differ only by the battery and the updates.
    entry("device-lifespan",
          # main grew its own phone lifespan row (`phone-how-long`, the security-updates answer)
          # while this was open, so the phone words are gone from here and phones keep main's
          # answer: two rows keying "phone" only race each other
          (("laptop", "macbook", "mac book", "computer", "pc", "desktop", "chromebook",
            "tablet", "ipad"),
           ("last", "lasts", "lasting", "lasted", "how long", "how many years", "years",
            "lifespan", "life span", "life expectancy", "expectancy", "how old",
            "keep it", "keep for", "keep going", "worth keeping", "worth keeping it",
            "time to replace", "due a", "due for a new", "before it dies", "before it needs")),
          "A laptop is good for about four to six years and a tablet for three to five, and the "
          "clock starts when the software updates stop rather than when it feels slow: a machine "
          "with no security fixes is the reason to change, not the speed. The battery is "
          "the exception, since £40 to £80 fits a new one to a laptop and £50 to £120 to a phone, "
          "and that alone buys another two or three years. If the case and the screen are still "
          "sound, a battery is nearly always cheaper than a replacement.",
          avoid=("battery", "batteries", "charge", "charging", "charger", "to charge",
                 "running out", "runs out", "dies", "died", "dying", "drain", "draining",
                 "slow", "sluggish", "hot", "overheat", "overheating", "fan", "noisy",
                 "screen", "cracked", "frozen", "freeze", "freezing", "restart", "update",
                 "updates", "install", "wifi", "wi-fi", "internet", "signal", "storage",
                 "space", "full", "repair", "replace", "fix", "worth fixing",
                 "should i buy", "should i get", "buy a new", "new phone", "new laptop",
                 "which", "what laptop", "what phone", "refurbished", "second hand",
                 "contract", "bill", "cheaper", "unlimited", "data",
                 # "my tablet keeps going to sleep" is the timer, not a machine on its way out:
                 # the sleep phrases stand this row down, so a tablet or an iPad that will not
                 # stay awake keeps the answer it had rather than falling to nothing.
                 "goes to sleep", "going to sleep", "keeps going to sleep", "falls asleep",
                 "keeps falling asleep", "sleeps too quickly", "sleep too quickly",
                 "sleeps too soon", "sleep timer", "sleep settings", "stop it going to sleep",
                 "stop it sleeping", "stop it from sleeping", "going to sleep on its own",
                 # "how long does a tablet last" is an iPad, and the medicine sense of "tablet"
                 # is the repeat-prescription row's: it was answering that line
                 "prescription", "repeat prescription", "chemist", "pharmacy", "medicine",
                 "medication", "pills", "dose", "dosage", "a day", "tablets a day",
                 "to take", "swallow",
                 # "my laptop keeps going to sleep" reached this row through "keep going": that
                 # is the power setting, in `laptop-keeps-sleeping`
                 "going to sleep", "goes to sleep", "keeps going to sleep", "keeps sleeping",
                 "falls asleep", "wont stay awake", "stay awake", "screen goes off",
                 "turns off the screen", "locks itself")),
    entry("laptop-repair-or-replace", (("laptop", "computer", "pc"), ("repair", "replace", "worth",
                                                                     "fix", "new one", "buy")),
          "Repair it if it is under five years old and the fault is the battery, the drive, the "
          "screen or the fan: those are £50 to £150 and give you years more use. Replace it when "
          "the motherboard or the case is gone, or when it cannot run the software you need, "
          "because those repairs cost more than the machine is worth.",
          # "should i get a console or a pc" is a choice between two things to buy, not a repair,
          # and neither is a question about cover
          avoid=("console", "consoles", "playstation", "ps5", "ps4", "xbox", "nintendo", "switch",
                 "gaming", "game", "games", "steam", "steam deck", "handheld",
                 "warranty", "warranties", "insurance", "apple care", "applecare", "care plan",
                 "cover", "protection plan", "policy")),
    entry("phone-how-long", (("phone", "iphone", "android", "handset", "mobile"),
                             ("how long", "last", "lasts", "lifespan", "how many years",
                              "before replacing", "need replacing", "worth replacing",
                              "keep it for")),
          "Most phones get security updates for five to seven years from new - an iPhone around "
          "five or six, a Samsung flagship about four, a cheap Android two or three - so a phone "
          "keeps working well for about four years, and the battery is usually what gives out "
          "first. A £50 to £90 battery swap buys two or three more years, which is far cheaper "
          "than a new handset.",
          bias=1,
          # the battery's own questions - how long it holds a charge, why it drains - are the
          # battery rows, and a repair-or-replace line is that comparison
          avoid=("battery", "batteries", "charge", "charging", "drains", "draining", "dies",
                 "dying", "holds", "repair", "fix", "broken", "cracked", "water", "replace it",
                 # "last" is the lifespan word here, and "last night" is not: "i had a proper row
                 # with my sister on the phone last night" reached this card on phone + last.
                 # A row, a call and the small hours are never how long a phone lasts.
                 "last night", "tonight", "at night",
                 # the term you are tied in for is the contract's own row: "how long does a phone
                 # contract last" was answered with the handset's security updates.
                 "contract", "contracts", "tariff", "sim only", "sim-only", "pay monthly",
                 "a row", "row with", "row about", "had a row", "proper row", "right row",
                 "argued", "arguing", "argument", "arguments",
                 "new phone", "which phone", "buy")),
    # "how long does a phone contract last" is a length question about the contract, and the row
    # above (how long a phone lasts) answered it with the handset's security updates: the phone's
    # life and the term you are tied in for are two different questions with two different
    # numbers, and people ask the second one when they are looking at the exit or the renewal.
    entry("phone-contract-length", (("contract", "contracts", "phone contract", "mobile contract",
                                    "sim only", "sim-only", "tariff", "pay monthly"),
                                   ("how long", "last", "lasts", "length", "minimum term",
                                    "how many months", "how long am i", "tied in", "tied to")),
          "A phone contract runs 12, 24 or 36 months and 24 is the usual one, and a SIM-only deal "
          "is the same shape at a lower price: 12 months, or rolling a month at a time. The "
          "minimum term is what ties you in, and it is what an early exit charge counts back from. "
          "When the term ends the contract carries on at the same monthly price rather than "
          "stopping, so ring then - the deals offered to an existing customer are cheaper than the "
          "one you are on, and if the handset is fine a SIM-only deal is about half the price.",
          # a contract being cancelled, ended, renewed or paid late is another row's, or the
          # composer's own date reading: this row is only the length of the term.
          avoid=("cancel", "cancelling", "cancellation", "end it", "end my", "ends", "ending",
                 "renew", "renewal", "notice", "pay it", "pay my", "missed", "arrears", "bill",
                 "went up", "going up", "early", "leave", "leaving", "complaint", "complain")),
    entry("phone-repair-or-replace", (("phone", "iphone", "android"),
                                      ("repair", "replace", "worth fixing", "new one", "cheaper",
                                       "new battery", "worth it",
                                       # "should i get a new phone or fix this one" names the choice
                                       # in its own words, without ever saying "repair"
                                       "fix it", "fix this", "fix my phone", "fix the phone",
                                       "or fix", "or repair")),
          "Repair it if the phone is under four years old and the fault is the screen, the battery "
          "or the charging port: £50 to £120 at a local shop, far less than a new phone. Replace it "
          "when the water damage or the logic board is the problem, or when updates have stopped, "
          "since those repairs cost more than the handset is worth.", bias=1,
          # a refurbished or second-hand handset is a buying question, not a repair one
          avoid=("refurbished", "refurb", "second hand", "second-hand", "sim only", "pay as you go",
                 "contract", "upgrade to",
                 # "fix my wifi" is a software fault, not a phone to repair or replace
                 "wifi", "wi-fi", "internet", "signal", "bluetooth", "hotspot", "password",
                 "email", "app", "apps")),
    entry("laptop-overheating", (("laptop", "computer", "pc"), ("hot", "overheating", "overheat",
                                                               "burning", "very warm")),
          "Stand it on a hard surface so the vents underneath are clear, and blow the dust out of "
          "them: a laptop on a duvet or a cushion overheats in minutes. Check the fan is actually "
          "spinning, and stop leaving it plugged in at 100% all day if the battery is swelling.",
          bias=1),
    entry("print-from-phone", (("phone", "iphone", "android", "mobile", "tablet"),
                               ("print", "printing", "printout")),
          "On an iPhone use the share button and choose Print, then pick the printer; on Android it "
          "is the three dots or the Print option in the app, and many printers need their own app "
          "such as HP Smart or Brother iPrint. Phone and printer must be on the same wifi, and "
          "AirPrint printers appear on their own with nothing to install."),
    entry("printer-not-printing", (("printer", "print"), ("not printing", "won't print", "wont print",
                                                          "jammed", "stuck", "offline", "error",
                                                          "connect", "connecting", "wont connect",
                                                          "won't connect")),
          "Switch the printer off and on at the wall, then check the queue: on Windows, Settings > "
          "Bluetooth and devices > Printers, clear anything stuck, and set it as the default "
          "printer. Nine times out of ten it is a stale job in the queue or the wrong printer "
          "selected, not a broken machine."),
    # A printer that prints, just slowly, had no answer: `printer-not-printing` keys on the words
    # of a fault, and "slow" reads as a speed rather than a failure, so the line fell through.
    entry("printer-slow",
          (("printer", "print", "printing"),
           ("slow", "slowly", "sluggish", "takes ages", "takes forever", "taking ages",
            "takes a long time", "takes a long", "long time", "hangs", "pauses",
            "stops halfway", "so slow", "quicker", "faster")),
          "Clear the queue first (Settings > Bluetooth and devices > Printers on Windows, "
          "Printers & Scanners on a Mac), because a stuck old job makes every new one crawl, and "
          "plug the printer in by cable to see whether wifi is the problem rather than the "
          "machine. After that it is the file and the setting: a photo or a long PDF takes a "
          "minute a page on a cheap inkjet, so drop the quality from Best to Normal and print a "
          "few pages at a time.",
          # the fault words stay with printer-not-printing, which is what they ask about
          avoid=("not printing", "won't print", "wont print", "jammed", "offline", "error",
                 "connect", "connecting", "won't connect", "wont connect", "stuck", "queue")),
    # "how do i change my printer ink" was the search hedge: the printer rows all key a fault
    # ("not printing", "slow", two-sided), and changing a cartridge is not a fault.
    entry("change-printer-ink",
          (("printer ink", "printer cartridge", "printer cartridges", "ink cartridge",
            "ink cartridges", "cartridge", "cartridges", "toner", "toner cartridge",
            "printer", "ink"),
           ("change", "changing", "replace", "replacing", "swap", "swap out", "run out",
            "run out of", "ran out", "refill", "refilling", "put in", "how do i", "how to",
            "fit", "installing", "compatible", "genuine", "which cartridge", "what number",
            "low", "low ink", "which ink", "what ink", "ink number")),
          "Open the lid with the printer on and wait for the cartridge carrier to slide to the "
          "middle by itself - do not pull it, because the print head parks at the edge. Press the "
          "old cartridge down and towards you until it clicks free, lift it out, then take the new "
          "one out of its packaging and pull the tape off the contacts and the nozzle before it "
          "goes in. Slide it in at the same angle until it clicks, close the lid and let the printer "
          "run its alignment page. Buy the number printed on the old cartridge (or in the printer's "
          "menu), and check the price per page rather than the box price.",
          # a printer that will not print or prints slowly is the fault rows' question
          avoid=("not printing", "won't print", "wont print", "jammed", "offline", "error",
                 "won't connect", "wont connect", "stuck", "queue", "slow", "slowly",
                 "double sided", "both sides", "photo paper", "scan", "scanner",
                 # ink on something that is not a printer is a stain: "how do i get ink out of
                 # my shirt pocket" was answered with the cartridge instructions
                 "shirt", "shirts", "tshirt", "t shirt", "clothes", "clothing", "fabric",
                 "carpet", "sofa", "couch", "stain", "stains", "pocket", "hands", "fingers",
                 "pen", "pens", "leaking", "leaked",
                 # getting a printer onto the network is not an ink question, and the key holds
                 # "how do i" for the cartridge change, so "how do i connect my printer to wifi"
                 # and "how do i add a printer to my laptop" opened this row and were told how
                 # to swap a cartridge
                 "connect", "connecting", "connection", "wifi", "wi fi", "wireless", "network",
                 "offline", "pair", "pairing", "bluetooth", "airprint", "driver", "drivers",
                 "set up a printer", "set up my printer", "set up the printer", "add a printer",
                 "add my printer", "find my printer", "not detected", "not showing", "install a printer",
                 "install my printer", "install the printer"),
          bias=1),
    # The printer on the network is its own question, and it was nobody's: "how do i connect my
    # printer to wifi" and "how do i add a printer to my laptop" opened the cartridge row (its ask
    # group holds "how do i") and were told how to swap a cartridge, and "how do i install a
    # printer driver" was a web search in one sentence.
    entry("printer-wifi",
          (("printer", "printers"),
           ("connect", "connecting", "connection", "wifi", "wi fi", "wireless", "network",
            "pair", "pairing", "airprint", "add a printer", "add my printer", "add the printer",
            "install a printer", "install my printer", "install the printer", "install a driver",
            "printer driver", "drivers", "set up a printer", "set up my printer",
            "set up the printer", "not detected", "not found", "not showing", "find my printer",
            "add it to my laptop", "add it to my computer")),
          "Put the printer on the same wifi as the laptop, from the printer's own panel: hold the "
          "wireless button until its light flashes, pick your network by name and type the "
          "password - or use the maker's app (HP Smart, Epson Smart Panel, Canon PRINT, Brother "
          "Mobile Connect), which walks you through the same thing and then finds the printer for "
          "you. The two usual reasons it fails: many printers only take the 2.4GHz band, so pick "
          "that network rather than the 5GHz one, and a guest network keeps devices from seeing "
          "each other. On the laptop, Settings > Bluetooth & devices > Printers & scanners > Add "
          "device (on a Mac, System Settings > Printers & Scanners > +). If it is still not found, "
          "print the network test page from the printer's menu and check the network name on it is "
          "the same one your laptop is on - the page also gives its IP address, which you can type "
          "into the add-a-printer box.",
          # ink and a printer that will not print are the other rows
          avoid=("ink", "cartridge", "cartridges", "toner", "jammed", "jam", "stuck", "paper",
                 "queue", "error", "scan", "scanner", "scanning", "slow", "slowly", "streaks",
                 "smudged", "photo"),
          bias=1),
    entry("print-both-sides", (("double sided", "double-sided", "both sides", "two sided",
                                "two-sided", "duplex", "on both sides of the paper"),
                               ("print", "printing", "printer", "how", "set", "make")),
          "In the print dialog open Layout (or More settings) and choose Print on Both Sides, "
          "flipping on the long edge, which is what reads like a book; on a Mac it is the Two-Sided "
          "tick in the Copies and Pages sheet. If there is no such option, the printer has no "
          "duplexer and will ask you to take the paper out and turn it over."),
    entry("parcel-address", (("parcel", "delivery", "package", "courier"),
                             ("wrong address", "address is wrong", "wrong email", "change the address",
                              "change my address", "not arrived", "went to the wrong")),
          "Ring the courier or use their app as soon as you spot it: most let you correct the "
          "address or email until the parcel is out for delivery, and a redelivery to a neighbour "
          "or a pickup point is usually free. Keep the tracking number to hand, and tell the shop "
          "you bought from if the tracking shows it delivered."),
    entry("browser-slow", (("browser", "chrome", "firefox", "safari"), ("slow", "slow down",
                                                                       "tabs", "memory",
                                                                       "laggy", "freezes")),
          "Close the tabs you are not reading: each one costs memory, and twenty open tabs will "
          "make any machine crawl. Restart the browser, then remove the extensions you do not "
          "recognise; a fresh profile or clearing the cache is the next step."),

    # --- wifi and the network ----------------------------------------------
    entry("wifi-signin", (("wifi", "wi fi", "wireless", "network", "internet"),
                          ("sign in", "sign-in", "signin", "login page", "log in page",
                           "asks me to sign in", "connect to the internet", "terms", "hotel",
                           "cafe", "airport", "guest")),
          "That is the guest sign-in page doing its job: open a browser and go to any site you "
          "have not visited, such as example.com, and the page should appear with a box for the "
          "password, room number or your email. If nothing loads, type 192.168.1.1 or 192.168.0.1 "
          "in the address bar, or ask the staff for the code; some places ask you to sign in again "
          "every hour.",
          bias=1,
          avoid=("tv", "television", "telly", "printer", "console", "xbox", "playstation",
                 "thermostat", "boiler", "oven", "doorbell", "camera", "watch", "speaker")),
    entry("wifi-dropping", (("wifi", "wi fi", "wireless", "broadband", "internet",
                            "router", "routers"),
                            ("dropping", "drops", "drop out", "drops out", "cutting out",
                             "cuts out", "cutting in and out", "disconnect", "disconnects",
                             "signal", "weak", "bedroom", "dead spot", "poor", "cut out",
                             "keeps cutting", "keeps dropping", "dropping out", "drops in and out",
                             "in and out", "keeps going off", "keeps disconnecting",
                             # A room the signal does not get to is the same answer, in the words
                             # people use for it: "my wifi doesnt reach upstairs", "how do i get
                             # wifi to reach the back bedroom" and "wifi wont reach the shed"
                             # were the punt, because none of them says "drop". The reach and the
                             # far room are what make it this question; the wifi word is still
                             # the other half of the key. A bare "coverage" is left out on
                             # purpose: "internet coverage in my area" is what is sold where they
                             # live, not a room the signal misses, so the coverage word only
                             # counts with the place it is asked about in it ("coverage in the
                             # house"); `whole house` and `cover the house` say the same thing
                             # without it.
                             "reach", "reaches", "reaching", "doesnt reach", "doesn't reach",
                             "wont reach", "won't reach", "won't get to", "wont get to",
                             "upstairs", "downstairs", "loft", "attic", "shed", "garage",
                             "back room", "spare room", "far end", "garden", "extension",
                             "whole house", "dead zone", "dead zones",
                             "blackspot", "black spot", "cover the house",
                             "coverage in the house", "coverage in my house",
                             "coverage in the home", "coverage at home",
                             "coverage in the whole house", "better coverage in")),
          "Move the router up and out in the open, not in a cupboard or behind the TV, and put it "
          "as central as the phone line allows. If one room still drops, a mesh wifi system (about "
          "£100 for two units) fixes it far better than a repeater, and switching the router to the "
          "5GHz band helps when you are close to it."),
    # "which broadband is cheapest" and "who is the cheapest broadband provider" were a hedge and
    # a router login page: nothing in the base knew that the cheap end of broadband is a social
    # tariff and a price rise, so the one question everybody asks about a provider had no answer.
    # The faults and the contract are other rows, so they are fenced out here.
    entry("broadband-cheapest",
          (("broadband", "broadband deal", "broadband deals", "fibre", "fiber", "internet provider",
            "internet", "wifi deal", "provider"),
           ("cheapest", "cheap", "cheaper", "best deal", "best deals", "best price", "lowest price",
            "which provider", "who is the cheapest", "compare", "comparison", "shop around",
            "save money", "money off", "value")),
          "Cheapest is the one you can actually get. If you claim Universal Credit, ask for a social "
          "tariff first: BT Home Essentials, Sky Broadband Basics and Virgin Essential are about "
          "£15 to £20 a month and need no new line. Otherwise compare the whole 18 months rather "
          "than the first-year price, because the price rises partway through and since January "
          "2025 the contract has to tell you the rise in pounds, not a formula, so read that "
          "figure in the summary before you sign; a cashback deal through a comparison site is "
          "often worth £60 to £100 on top. At "
          "renewal, ask for the new-customer price before you switch - it usually works.",
          avoid=("not working", "no internet", "slow", "slower", "dropping", "drops", "keeps "
                 "cutting", "cutting out", "router", "hub", "password", "wifi", "wi fi", "signal",
                 "dead spot", "booster", "extender", "mesh", "engineer", "install", "installation",
                 "moving house", "new house", "cancel", "cancelling", "cancel it", "notice",
                 "end of contract", "out of contract", "leaving", "bill", "my bill", "direct debit",
                 "price rise", "mid contract", "complaint", "no service", "outage")),
    entry("wifi-slow", (("wifi", "wi fi", "wireless", "internet", "broadband"),
                        ("slow", "speed", "slower", "not working", "nothing loads", "wont load",
                         "won't load", "full bars", "nothing will load", "not loading",
                         "pages wont load", "pages won't load", "faster", "speed up",
                         "quicker", "better speed")),
          "Test the speed on a cable or right next to the router first, because that tells you "
          "whether the problem is the broadband or the wifi. If it is the wifi, move closer, use "
          "5GHz, and check how many devices are streaming; if the cabled speed is also low, it is "
          "your provider and worth a call."),
    # How fast a connection to buy was a shrug. The answer is a count of screens rather than a
    # number in the abstract, so the same reply fits "is fibre worth it" and "how fast should my
    # broadband be". `fibre` also means the stuff in food, so the food lines stand it down.
    # The id says what the row is for: consumer.py already owns `broadband-speed` for a
    # line that tests a connection slower than advertised, and two rows with one id is a
    # duplicate the deck test refuses.
    entry("broadband-speed-to-buy",
          # Bare "fibre" is not enough to be the connection: "is fibre worth it" is as likely a
          # diet question, and a bare key handed a diet reader a card about Mbps. Every entry
          # below says the connection in the phrase.
          (("broadband", "full fibre", "fibre broadband", "fiber broadband", "fibre internet",
            "fiber internet", "fibre line", "fibre connection", "fibre deal", "fibre speeds",
            "fibre package", "fibre optic broadband", "fttp", "fttc",
            "internet speed", "connection speed", "bandwidth", "megabits", "mbps", "gigabit",
            "provider", "isps", "isp"),
           ("worth", "how fast", "what speed", "how much speed", "how many", "enough", "need",
            "should i get", "should i buy", "do i need", "better", "faster", "which", "choose",
            "cheapest", "deal", "switch", "upgrade")),
          "Count the screens that stream at once: one or two people on HD needs about 40Mbps, a "
          "house with four people streaming and gaming needs 100-200Mbps, and upload speed matters "
          "more than download if you are on video calls. Full fibre is worth it when it costs "
          "roughly what you pay now, because it uploads as fast as it downloads and the line is "
          # "if nobody works from home" made the next turn a nod: the person's "we both work from
          # home" looked like a thing already said, and the ack row answered it instead of the
          # work-from-home card. The words say the same without the phrase.
          "not shared; a cheaper part-fibre deal is fine if nobody is home all day.",
          avoid=("eat", "eating", "diet", "dietary", "constipation", "bowel", "digestion",
                 "digestive", "poo", "stool", "cereal", "beans", "vegetables", "roughage",
                 "supplement", "ibs", "bloating", "recipe", "cook")),
    entry("wifi-booster", (("booster", "repeater", "extender", "range extender"),
                           ("wifi", "wi fi", "work", "help", "worth", "better", "buy", "get")),
          "A repeater halves the speed it repeats and only helps where the signal is weak but "
          "present, so put it halfway between the router and the dead room, ideally in line of "
          "sight. If the room gets nothing at all, it will repeat nothing, and a mesh system is the "
          "better buy.",
          # a booster that is a jab is health, not wifi: "should i get a covid booster" scored on
          # this row's "booster" and its bare "get", and got the repeater
          avoid=("covid", "jab", "jabs", "jabbed", "vaccine", "vaccines", "vaccination",
                 "vaccinations", "immunisation", "immunization", "flu", "tetanus", "shot",
                 "booster jab", "booster shot", "nhs", "gp", "pharmacy", "immunity"),
          # ...and a booster named with nothing of the wifi about it, in this line or the one it
          # follows, is the jab
          guard=_wifi_is_what_it_is_about),
    entry("wifi-mesh", (("mesh", "mesh system", "mesh network"),
                        ("wifi", "wi fi", "work", "help", "worth", "better", "buy", "get",
                         "house", "home")),
          "A two or three unit mesh system (around £100 to £150) puts one unit where the router is "
          "and the others around the house, and the devices switch between them by themselves. Buy "
          "the same brand as one set rather than mixing units, and put the middle one roughly in the "
          "centre of the house."),
    entry("wifi-password", (("wifi", "wi fi", "wireless"),
                            ("password", "router", "change", "forgot", "find")),
          _wifi_password_reply,
          # a wifi password is not the password of a website or a phone
          avoid=("netflix", "email", "account", "laptop", "phone login", "work",
                 # and it is not a recommendation: "what is a good wifi router" and "which
                 # router should i get" were told where the sticker is
                 "good router", "best router", "router to buy", "router should i", "which router",
                 "what router", "new router", "buy a router", "recommend", "upgrade", "mesh",
                 "extender", "repeater", "worth buying", "worth it")),
    # Buying a router was not a question anyone answered: "what is a good wifi router" got the
    # password sticker, "which router should i get" the maker's support page. The advice is
    # short and the same for everyone, so it is a row rather than a hedge.
    entry("router-buy",
          (("router", "routers", "mesh", "wifi", "wi fi", "wireless"),
           ("good", "best", "buy", "buying", "recommend", "recommended", "which", "what",
            "should i get", "should i buy", "cheap", "upgrade", "need a new", "replace",
            "worth it", "worth buying", "faster wifi", "extender", "booster")),
          "Start with the router your provider gave you: if the speed at the router is fine and "
          "only the far rooms are slow, a mesh two-pack (about £80 to £150) beats a single "
          "expensive router. Put the main unit high and central, not in a cupboard or beside the "
          "microwave, and wire the second one back to the first with a cable if the walls are "
          "thick. Wi-Fi 6 is worth having if your devices are new; a wired connection is still "
          "the fastest answer for a TV or a desk.",
          # a password, a restart and a slow-connection question are other rows
          avoid=("password", "forgot", "restart", "reboot", "reset", "not working", "dropping",
                 "drops", "slow", "speed", "not connecting", "keeps disconnecting", "sticker",
                 # and a place is the place row's line: "where should i put my router" and
                 # "where should i put my wifi extender" ask where, not which one to buy
                 "where should i put", "where do i put", "where can i put", "where to put",
                 "where should it go", "should i put", "put my", "put the router",
                 "best place", "best position", "which room"),
          bias=1),
    # Where the router goes. "where should i put my router" and "where should the router go in my
    # flat" were a search hedge on this branch, while the answer is the place the wifi-dropping
    # row already gives second: the middle of the place, up and out in the open. A place question
    # needs the place first, so it has its own row.
    entry("where-the-router-goes",
          (("router", "routers", "wifi box", "wi fi box", "wifi router", "broadband box",
            "modem", "home hub", "internet box",
            # the same box under the other names people give it: "where do i put the wifi hub"
            # and "where do i put the smart hub" were a hedge and a search while "home hub" and
            # "internet box" were answered
            "hub", "wifi hub", "broadband hub", "smart hub", "internet hub",
            "wireless hub", "wifi router box"),
           ("where should", "where do i put", "where can i put", "where to put", "put it",
            "put the router", "where to place", "where should i place", "place it",
            "position it", "best place", "best position", "where is best", "where does it go",
            "where should it go", "where should the router go", "where does the router",
            "where does it", "where would the router", "which room", "high up",
            "move the router", "should i move", "move it", "better to put",
            "out of the way", "middle of the house", "middle of the flat", "central",
            "under the stairs", "in a cupboard", "upstairs", "downstairs",
            # how high, and the things the answer names as spoilers: "how high should i mount
            # the router" was the maker's support page, and so was "is my router ok next to the
            # microwave" although this answer already says not beside one
            "how high", "how far up", "which height", "best spot", "good spot", "in the open",
            "near the tv", "next to the tv", "by the tv", "behind the tv", "behind the telly",
            "near the telly", "next to the telly", "near the microwave",
            "next to the microwave", "near the fish tank", "next to the fish tank",
            "near the mirror", "next to the mirror", "better near", "best near")),
          _router_place,
          # a router that drops, resets or loses its password is another row
          avoid=("password", "passcode", "reset", "restart", "reboot", "not working",
                 "dropping", "drops", "slow", "speed", "extender", "booster", "repeater",
                 "mesh", "airport", "hotel", "cafe", "public", "provider", "contract",
                 "cancel", "buy", "which router", "new house", "new flat", "moving house",
                 "moving flat", "new provider",
                 # a hub is also a computer's: "can i put a usb hub in my monitor" is the ports
                 # on the back of a screen, and "put" alone was enough to reach this answer
                 "usb", "monitor", "keyboard", "mouse", "printer", "dock", "port", "ports",
                 "nas", "switch", "ethernet", "usb hub")),
    entry("router-restart", (("router", "wifi", "wi fi", "internet"),
                             ("restart", "reboot", "reset", "turning off", "not working")),
          "Unplug the router for 30 seconds, plug it back in and give it two minutes to reconnect; "
          "that clears most dropouts. If it keeps happening, check the cables are pushed fully in "
          "and note how often it drops before you ring your provider.",
          # A reset or restart is this entry's, not the password's: "how do i reset my wifi router"
          # named a wifi and a router word and nothing else, so the password entry (which lists a
          # bare "router" as one of its words) took the tie on registry order and answered with a
          # sticker on the back of the box.
          bias=1,
          # ...but a password line is not a reboot: "how do i reset my router password" named a
          # router and a reset, and the reboot answer cannot reset a password. It is the password
          # entry's line, and the pinhole is the answer the other half of the time.
          avoid=("password", "passcode", "pass code", "wifi key", "network key",
                  "log in", "login", "sign in", "admin",
                  # and a factory reset is not a reboot either: unplugging the router keeps every
                  # setting, so it never puts the wifi name and password back
                  "factory reset", "factory settings", "hard reset", "full reset",
                  "reset button", "reset hole", "pinhole", "back to factory",
                  "wipe the router", "wipe it")),
    # The reset hole, and the difference between it and the plug - see ROUTER_FACTORY. The key
    # needs a router word as well as the reset phrase, so a phone or a laptop factory reset keeps
    # its own row.
    entry("router-factory-reset", (("router", "wifi", "wi fi", "wireless", "internet",
                                    "modem", "hub", "broadband"),
                                   ("factory reset", "factory settings", "hard reset",
                                    "full reset", "reset button", "reset hole", "pinhole",
                                    "wipe the router", "back to factory", "start again")),
          _router_factory_reply,
          # "there is a reset button on my router what does it do" is a what-is question about a
          # reset button, so explain-router took it and described the box. The button is the
          # reset's, and the row already needs a router word beside the phrase.
          bias=1),
    # Locked out of the router's own admin page is the same answer as the reset hole, because the
    # pinhole is the only way back in when the password has been changed and forgotten. It is its
    # own row rather than a branch of the wifi-password callable: "how do i reset my router
    # password" names a router and a password and no wifi, and the password row's key needs a
    # wifi word as well, so the line reached nothing at all and got the punt.
    entry("router-admin-password", (("router", "wifi", "wi fi", "wireless", "modem", "hub",
                                     "admin", "broadband"),
                                    ("reset my router password", "reset the router password",
                                     "router password", "admin password", "admin login",
                                     "cant log in", "can't log in", "cannot log in",
                                     "cant login", "can't login", "locked out",
                                     "password wont work", "password won't work")),
          _admin_locked_reply),
    entry("wifi-vs-internet", (("internet", "broadband"), ("wifi", "difference", "what is")),
          "Wifi is just the radio link between your devices and the router; the internet is the "
          "connection the router brings into the house. So a wifi problem is your side (distance, "
          "walls, an old router) and an internet problem is your provider's line.",
          # "can i use my phone as a wifi hotspot instead of broadband" is a choice between two
          # ways of getting online, which home-broadband-choice answers; the difference between
          # the words is what this row is for.
          avoid=("hotspot", "hot spot", "tether", "tethering", "use my phone", "mobile data",
                 "unlimited data", "instead of", "data plan", "data allowance")),

    # A home connection is a choice people put off for months, and every shape of it was the
    # composer's shrug: "should i get broadband or use my phone" got "that's your call, not
    # mine", "do i need broadband if i have unlimited data" and "is 5g home broadband any good"
    # the search hedge, and "should i get a landline" "can't call that one for you". Nothing in
    # the line needs looking up, so each gets the trade-off and a line to go by instead.
    entry("home-broadband-price",
          (("broadband", "full fibre", "fibre", "fibre broadband", "home internet",
            "internet at home", "home wifi"),
           ("how much", "how much is", "how much does", "cost", "costs", "price", "prices",
            "per month", "a month", "monthly", "spend", "pay", "budget", "average")),
          ("Full fibre is about £25 to £35 a month for 100 to 500 Mbps, on an 18 or 24 month deal, "
           "and it jumps £10 or so once that deal ends - the price on the site is rarely the price "
           "in month 25. A social tariff is £15 to £20 a month if you claim Universal Credit or "
           "Pension Credit, and most big providers offer one quietly, so it is worth asking. Line "
           "rental only comes on top if you keep a landline."),
          bias=1,
          # a bill that has gone up, a fault, and a cancellation are each their own question
          avoid=("too high", "so high", "went up", "gone up", "going up", "not working",
                 "keeps dropping", "slower", "slow", "cancel", "cancellation", "switch",
                 "switching", "complain", "refund", "engineer", "install", "set up",
                 "should i get", "do i need", "any good", "instead")),
    entry("home-broadband-choice",
          (("broadband", "home internet", "home wifi", "fibre", "fibre broadband",
            "full fibre", "5g home broadband", "mobile broadband", "internet at home",
            "home connection"),
           ("should i get", "should i have", "do i need", "need", "worth it", "is it worth",
            "any good", "instead", "instead of", "or use my phone", "use my phone",
            "unlimited data", "mobile data", "hotspot", "hot spot", "tether", "tethering",
            "no broadband", "without broadband", "5g", "compare", "better than", "vs",
            "which is better", "settle for")),
          ("Worth it if you work or stream at home, more than one person uses the connection, or "
           "you game: a phone hotspot will do for one light user, but its data cap and the delay "
           "on a video call show up fast. 5g home broadband sits between the two - no line and no "
           "engineer, but check the coverage at your postcode and how it holds up at 8pm before "
           "you take a two-year deal. Cheapest full fibre is usually about £25 a month, and a "
           "mobile-only household pays about the same in data once two people stream."),
          bias=1,
          # the fault, the bill and the cancellation have rows of their own
          avoid=("not working", "no internet", "wont connect", "won't connect", "keeps dropping",
                 "dropping out", "slow", "slower", "cancel", "cancellation", "switch",
                 "switching", "complain", "refund", "bill", "price rise", "went up",
                 "engineer", "install", "set up", "router",
                 # "fibre" is what the body needs as well as what the cabinet brings: "im trying
                 # to eat more fibre, what should i have" was answered with a broadband deal.
                 "eat", "eating", "eaten", "food", "foods", "diet", "digestive", "digestion",
                 "bowel", "bowels", "constipation", "bloating", "roughage", "more fibre",
                 # and a speed question is the speed row's, not a yes or no about having one
                 "speed", "speeds", "mbps", "megabits", "download", "upload", "how fast",
                 "faster", "fast enough")),
    entry("home-landline",
          (("landline", "land line", "home phone", "house phone", "phone line", "fixed line",
            "copper line", "bt line"),
           ("should i get", "do i need", "need", "worth", "worth it", "any good", "still",
            "keep", "keeping", "cancel", "ditch", "get rid", "necessary", "give up",
            "without", "drop", "do i have to")),
          ("Only if something relies on it - a care alarm, a fax, or a broadband deal built on "
           "the old copper line. Calls do not need one: a full-fibre service carries the phone "
           "over the same cable, and a landline is being switched off across the UK anyway. If "
           "you keep one it is about £5 to £10 a month on top of broadband, so ask what the "
           "package costs without it before you renew."),
          bias=1,
          # a dead line, a fault and a bill are other rows' questions
          avoid=("dead", "no dial tone", "dial tone", "not working", "fault", "noise", "crackle",
                 "bill", "charged", "install", "socket", "extension", "move my number")),

    # --- a device that will not join, an app that will not open ---------------
    entry("app-wont-open",
          (("app", "apps", "application", "netflix", "iplayer", "spotify", "youtube", "whatsapp",
            "instagram", "facebook", "tiktok", "banking app", "bank app", "game"),
           # a bare "wont" or "cant" is here so the word order people use - "why wont my app
           # open" - still covers two key words, because the phrase has to be contiguous
           ("wont open", "won't open", "wont", "won't", "cant", "can't", "cannot",
            "refuses", "refusing", "wont load", "won't load", "not opening", "wont start",
            "won't start", "not working", "wont work", "won't work", "crashes", "crashing",
            "keeps closing", "closes", "freezes", "frozen", "stuck", "black screen",
            "cant get", "can't get", "cannot get", "cant run", "can't run", "wont run",
            "won't run", "not supported", "opens and closes", "stopped working",
            "has stopped working", "keeps stopping")),
          "Force the app closed and open it again first, then update it in the App Store or Play "
          "Store: an app that is behind the phone's software is the usual cause. If it still will "
          "not open, restart the phone, then check the phone has storage free (an almost-full phone "
          "cannot run apps), and as a last step delete the app and reinstall it, which keeps your "
          "account but loses anything saved only on the phone. If the store says the app needs a "
          "newer iPhone or Android version, the phone itself is the limit and no amount of "
          "reinstalling will fix it.",
          # a smart-TV app is the TV's own settings, not a phone's app store
          avoid=("tv", "television", "telly", "smart tv", "fire stick", "roku", "console",
                 "playstation", "xbox", "ps5", "ps4", "nintendo", "watch",
                 # "close" is a loose form of "closes", so "how do i close my facebook account"
                 # scored the same as an app that will not open and lost the tie-break: an
                 # account to shut or a set of steps is not a crash. A real crash line names no
                 # account ("my banking app is stuck on the logo") and still gets this answer.
                 "account", "delete", "deactivate", "quit", "log out", "sign out"),
          guard=_an_app_not_a_paper),
    entry("phone-nearly-flat",
          (("phone", "iphone", "android", "mobile", "battery"),
           ("2%", "1%", "5%", "low battery", "battery is low", "battery is really low",
            "battery is nearly dead", "no charge",
            "out of charge", "flat battery", "no battery", "nearly dead", "about to die",
            "flat", "nearly flat", "almost flat", "going flat", "is flat", "on 1 percent",
            "on 2 percent", "on ten percent", "percent left")),
          "Switch on Low Power Mode and the phone will last hours longer: Settings > Battery on an "
          "iPhone, or Battery saver in Android's settings. Turn the screen brightness down, drop "
          "5G to 4G if that is a setting you have, and ask in the nearest cafe, library or shop to "
          "plug into a socket for fifteen minutes - a short top-up is fine for the battery.",
          # a laptop on low battery, or a car battery, is another answer; so is the question
          # about keeping a phone at 80%, which asks about the charge limit, not a flat phone.
          # A bike, a scooter or a ride-on mower that will not start is not a flat phone: those
          # lines share "battery" and "flat" with this entry and got the Low Power Mode tip.
          avoid=("laptop", "macbook", "car", "van", "key fob", "smoke alarm", "watch",
                 "bike", "bicycle", "motorbike", "scooter", "moped", "ride-on", "mower",
                 "caravan", "motorhome", "boat",
                 # a lamp left on in a car is the car battery's line, not a phone's
                 "lights on", "left the lights", "headlights", "interior light", "dome light",
                 "boot light", "radio on", "alternator", "ignition",
                 "80", "80%", "keep my phone at", "charge limit", "battery health",
                 # a thermostat's cells are changed at the wall, not topped up in a cafe
                 "thermostat", "thermostats", "boiler", "heating",
                 "switches itself off", "switch itself off", "turns itself off",
                 "shuts itself off", "switches off at", "dies at"),
          # The figures people type are open-ended: the keys above list 1%, 2% and 5%, and "my
          # phone is on 4%" reached no entry at all, so the turn was acknowledged back at the
          # person ("Got it — it's on 4%.") while "my phone is nearly flat" got the answer. A
          # charge is a percentage at or below twenty; the number itself says nothing else.
          shape=(_running_out_of_charge,)),
    entry("charger-hot", (("charger", "plug", "adapter", "usb", "lead", "cable", "charging brick"),
                          ("hot", "warm", "boiling", "melting", "burning", "smell", "smells",
                           "buzzing", "hissing", "scorch",
                           # "is it safe to leave the charger plugged in overnight" is the same
                           # worry about heat, and the answer is the same one: unplug it.
                           "leave it plugged", "leave the charger", "plugged in overnight",
                           "overnight", "safe to leave")),
          "A charger that is warm is normal; one that is too hot to hold, buzzes, smells or has "
          "scorched the plug is not, so unplug it and stop using it. Replace it with a branded "
          "charger of the right wattage rather than a cheap one, do not charge a phone under a "
          "pillow or on a bed, and pull the plug out by the body, not the cable.",
          # a hot water bottle, a hot tap or a hot flush is not a charger
          avoid=("water bottle", "radiator", "oven", "kettle", "shower", "bath", "flush",
                 "weather", "heatwave", "sunburn")),
    # A cable that is frayed or split is not the same question as a cable that will not charge,
    # which is where it went: "my phone charging cable fraying" was answered "try another cable
    # and plug, then clean the charging port", "the wire on my charger is exposed" was a listening
    # line, "is it safe to tape a frayed charger" was the maker's support page, and "should i throw
    # away a frayed charging cable" was a pay-rise card. The damage is the whole answer here, so it
    # is its own row rather than a word in the hot-charger key.
    entry("cable-frayed",
          (("charger", "chargers", "cable", "cables", "lead", "leads", "usb", "usb c", "usb-c",
            "lightning", "adapter", "plug", "wire", "wires", "flex", "charging brick"),
           ("frayed", "fraying", "fray", "frays", "split", "splitting", "splits",
            "exposed", "exposed wire", "bare wire", "inner wire", "inner wires",
            "wire showing", "wires showing", "showing wire", "insulation", "worn through",
            "worn away", "rubbed through", "rubber has split", "rubber split", "nicked",
            # "is it safe to tape a frayed charger" and "can i still use it" are the same worry:
            # the wire is showing and they want to know whether it is still usable.
            "safe to tape", "tape it", "tape the", "tape a", "duct tape", "electrical tape",
            "still use it", "still use a frayed", "still safe")),
          "Stop using it and replace it: a cable with the wire showing, or the plug end split, can "
          "shock you or start a fire, and tape does not make it safe again. Unplug it first, buy a "
          "branded cable of the same type and wattage rather than the cheapest one on the app, and "
          "if the cable is fixed to the plug - a kettle, a lamp, a washing machine - have the lead "
          "replaced rather than taping it. To stop the next one fraying, pull it out by the plug and "
          "not by the wire, and do not wrap it tightly round the charger or a corner.",
          # the animal chewed through it is a pet-behaviour question while the cable is intact
          # advice, and a new cable that fell apart is the retailer's, not a fraying one.
          avoid=("dog", "puppy", "cat", "kitten", "rabbit", "hamster", "parrot",
                 "guinea pig", "chewed", "chewing", "faulty", "refund", "replace it free",
                 "warranty", "guarantee", "brand new", "came apart", "coming apart",
                 # "cable" and "frayed" are enough to score, so a mechanical cable landed here:
                 # "my bike brake cable is frayed" and "the clutch cable on my car is frayed" were
                 # told it could shock them or start a fire. A brake or a clutch cable is a
                 # mechanical part with its own answer, and nothing here is electrified. NOT the
                 # bare word "car": "my car charger is frayed" is this card's line.
                 "brake", "brakes", "braking", "clutch", "handbrake", "gear cable", "gear",
                 "gears", "throttle", "derailleur", "bicycle", "bike cable", "motorbike",
                 "motorcycle", "scooter", "chainsaw"),
          guard=_cable_fault_not_the_care_question),
    entry("found-phone-ransom",
          (("found", "someone has", "someone found", "handed in"),
           ("phone", "iphone", "mobile", "wants money", "give it back", "ransom", "reward",
            "asking for money")),
          "Do not pay: message them that the phone is blocked and report it to the police as "
          "found property, which is free and makes the phone theirs to hand in, not to sell. Lock "
          "it from Find My or Find My Device so it cannot be used, tell your network, and change "
          "the passwords for the accounts that were signed in on it.",
          # "i found a phone" is the finder's question, not the owner paying to get one back
          ask=("wants money", "asking for money", "give it back", "ransom", "reward",
               "wont give it back", "won't give it back")),
    # --- passwords accounts and safety -------------------------------------
    entry("password-manager", (("password manager", "passwords", "remember passwords",
                                "password safety", "protect passwords", "keep passwords",
                                # "how do i keep my accounts safe" is this question without the
                                # word password in it, and lifeadmin's record-keeping row took
                                # it on "accounts" and answered about tax paperwork
                                "my accounts", "online accounts", "keep my accounts",
                                "accounts safe", "accounts secure", "account safe",
                                "account secure", "protect my accounts"),
                               ("should", "use", "what", "worth", "good", "best", "how", "forget",
                                "forgetting", "keep forgetting", "remember", "too many")),
          # "Yes, use one:" answered the "should I" frame and read as a non-answer to "how do i
          # keep my passwords safe", so the sentence now names the tool first and works for both.
          "Use a password manager: it remembers a different long password for every site and fills "
          "it in, so you only need to know one strong password. Bitwarden is free and good, "
          "1Password and Dashlane are the paid ones, and your phone and browser have a decent "
          "basic one built in.",
          # a forgotten password for one site, or a hacked account, is another entry, and "what
          # makes a good password" is the strong-password entry: this one is only about the tool
          # "how do i protect my passwords" and "how do i keep my passwords safe" name the
          # thing and the worry but none of the words above, so they were a shrug: the how-do-i
          # of it is the asking, and the tool is still the answer.
          ask=("password manager", "forget", "forgetting", "keep forgetting", "remember",
               "too many passwords", "write them down", "protect", "protecting", "safe",
               # "how do i" is deliberately not here: "how do i pick a password" is the
               # strong-password entry, and a bare asking frame would take it.
               "secure", "store", "storing", "written down"),
          avoid=("change my password", "changed my password", "reset", "forgot my password",
                 "locked out", "wifi", "wi fi", "router", "hacked", "someone has my account")),
    entry("forgot-apple-id", (("apple id", "apple account", "icloud password", "apple password",
                               "apple"),
                              ("forgot", "reset", "locked out", "cant remember", "can't remember",
                               "lost", "change")),
          "Use the Forgot password link on the sign-in screen, or iforgot.apple.com, and reset it "
          "with the email address and phone number on the account; a trusted device or a friend's "
          "phone can also approve it. Nobody legitimate ever asks for your Apple ID password or a "
          "fee to unlock it, so ignore anyone who offers."),
    entry("parcel-scam", (("parcel", "delivery", "courier", "royal mail", "evri", "dpd"),
                          ("pay", "fee", "customs", "1.99", "held", "redelivery"),
                          ("text", "message", "sms", "link", "click", "email")),
          "Pay nothing and do not tap the link: couriers never ask for a small fee by text, and "
          "the 1.99 is the hook for your card details. Check the parcel on the courier's own "
          "website with the tracking number you were given, forward the text to 7726 and delete "
          "it; if you did pay, ring your bank and cancel the card.",
          avoid=("address", "wrong")),
    entry("password-reset", (("forgot", "forgotten", "can't remember", "cant remember",
                              "locked out", "won't let me in", "wont let me in"),
                             ("password", "passcode", "login", "log in", "sign in", "account")),
          "Use the \"forgot password\" link on the sign-in page and let it send a reset link to the "
          "address the account is registered to: it often lands in spam, and the link expires "
          "within the hour. Before you reset, look for a saved password in the browser or the "
          "phone's keychain, and if the account still will not open, go through the site's own "
          "account-recovery page so you know you are on the real site.",
          bias=1),
    entry("strong-password", ("password", ("strong", "secure", "remember", "make", "choose",
                                          "hacked", "good", "best", "safe", "pick", "rules")),
          "Three or four unrelated words strung together beat a short jumble of symbols: "
          "\"correct-horse-battery-staple\" is both strong and easy to type. Use a different one "
          "for each important account (email, bank), and turn on two-factor for those."),
    entry("two-factor", (("two factor", "two-factor", "2fa", "two step", "two-step", "authenticator"),
                         ("set up", "turn on", "what", "how", "use", "enable")),
          "Turn it on for your email and bank first: in the account settings it is called two-step "
          "verification or 2FA, and an authenticator app (Authy, Google Authenticator, or your "
          "phone's built-in one) is safer than a text message. Save the backup codes somewhere "
          "off the phone."),
    entry("phishing-email", (("phishing", "scam", "scam email", "fake email", "fake",
                              "suspicious", "dodgy", "spoof", "spoofed"),
                             ("email", "emails", "mail", "inbox", "link", "clicked", "click",
                              "reply", "sender", "address it came from", "attachment",
                              "outlook", "gmail"),
                             # what the mail says, so "an email saying my account is locked"
                             # reaches it: the bank answer stood down on mail words and this
                             # line then had only one key word left to stand on
                             ("saying", "says", "said", "locked", "blocked", "suspended",
                              "account", "unusual activity", "verify", "verification",
                              "details", "password")),
          "Do not click the link: open the company's site or app yourself and check the message "
          "there, which is how real banks and delivery firms contact you. Check the sender address "
          "carefully, and if you did click, change that password and ring the real company on the "
          "number from their website.",
          # A scam that arrives by email is not the "no real bank rings" answer, but that one is
          # keyed on the same two words, so this is the more specific of the two for mail.
          bias=1,
          # a text or a phone call is a different answer, and the bank one covers them well
          avoid=("text", "texts", "sms", "call", "calls", "called", "rang", "rang me", "phoned",
                 "phone", "voicemail", "whatsapp",
                 # a mailbox someone else is already inside is the hacked-account answer, and
                 # "account" is one of the words this entry needs
                 "got into", "hacked", "taken over", "someone got", "someone else", "locked out",
                 "cant get them out", "can't get them out", "changed my password")),
    entry("scam-text", (("scam", "fraud", "suspicious"), ("text", "message", "call", "phone",
                                                          "whatsapp")),
          "Do not reply, and do not use the number or link in the message; forward scam texts to "
          "7726 (free in the UK) and block the sender. If it claims to be your bank, ring the "
          "number on the back of your card, and never move money because someone on the phone told "
          "you to.",
          bias=2),
    entry("email-hacked", (("email", "account", "facebook", "instagram", "whatsapp"),
                           ("hacked", "taken over", "someone else", "logged in", "changed my password",
                            "locked out", "accessed", "got into", "got in", "broken into",
                            "get them out", "someone got")),
          "Change the password from a device you trust, then look at what the intruder set up: a "
          "recovery email, a forwarding rule, a connected app. Turn on two-factor with an app "
          "rather than a text, tell the contacts it messaged not to send money, and use the "
          "account's own report-a-hack page so it reviews the logins."),
    entry("public-wifi-banking", (("public wifi", "hotel wifi", "cafe wifi", "airport wifi",
                                   "free wifi"),
                                  ("bank", "banking", "safe", "log in", "login", "password",
                                   "money")),
          "Wait until you are on mobile data for banking, or use the bank's own app on 4G: a public "
          "network can be imitated, and the padlock on a site does not prove it is the real one. If "
          "you must use it, turn off file sharing, stick to sites you typed yourself, and log out "
          "when you finish."),
    # "how do i stop spam emails" was reaching the junk-post answer in lifeadmin, because both
    # keyed spam and stop and the post entry got there first by a hair. The inbox version names
    # the inbox, so it wins the tie outright and the post one now refuses email words.
    entry("spam-email", (("spam", "junk email", "unwanted email", "spam email", "spam emails",
                          "junk emails", "unwanted emails", "email spam", "inbox"),
                         ("stop", "reduce", "inbox", "filter", "unsubscribe", "getting", "keeps",
                          "keep", "full", "loads", "so many", "get rid")),
          "Mark it as junk rather than just deleting it, because the filter learns from that: in "
          "Gmail, Report spam and then Filter messages like these so the whole sender goes to spam "
          "from now on; in Outlook, Junk > Block sender. Unsubscribe from the newsletters you "
          "actually signed up for, and never reply or click unsubscribe on anything you do not "
          "recognise, because that confirms your address is live. A second address for shops keeps "
          "the real one off the lists.",
          bias=1, guard=_junk_or_a_full_box,
          avoid=("call", "calls", "phone", "ring", "mobile", "landline", "number", "text", "sms",
                 "post", "postal", "postman", "letterbox", "letter", "letters", "doorstep",
                 "junk mail", "delivery", "deliveries", "parcel", "leaflet", "leaflets",
                 "door", "lettershop")),
    entry("landline-dead",
          (("landline", "land line", "home phone", "house phone", "phone line", "dial tone",
            "dialling tone", "fixed line", "telephone line", "bt line", "virgin line"),
           ("dead", "no dial", "not working", "isnt working", "isn't working", "wont work",
            "won't work", "stopped working", "nothing", "silent", "no tone", "fault", "broken",
            "down", "crackle", "crackling", "static", "hum", "check", "fix", "test", "working",
            "lost", "cut off", "no sound", "why")),
          "Plug one corded phone straight into the test socket behind the master socket's faceplate, "
          "with the broadband filter out: if there is still no dial tone there, the fault is outside "
          "your house and your provider fixes it free. Ring the landline from a mobile to tell the two "
          "apart - if it rings but you hear nothing it is the handset, and if it is unobtainable or "
          "goes to voicemail it is the line. A total loss has to be repaired within two working days, "
          "so report it with that test result and ask for the refund.",
          # a mobile that is broke is the phone entry's, and a bill or a scam call is not a fault
          avoid=("mobile", "iphone", "android", "smartphone", "sim", "bill", "contract", "tariff",
                 "upgrade", "scam", "cold call", "spam", "number", "broadband only", "wifi")),
    # "silent" on its own is a phone that does not ring, not a caller who says nothing: "why does my
    # phone go silent by itself" and "does my phone alarm work on silent" were both told to block
    # the number in the call log, on the strength of "silent" plus "phone". A silent call is a
    # nuisance call, which `nuisance-calls` answers, so this row stands down on the word and
    # `phone-not-ringing` takes the phone that has gone quiet.
    entry("spam-calls", (("spam", "nuisance", "cold call", "unknown number"),
                         ("call", "calls", "ring", "rang", "number", "phone")),
          "Block the number in your phone's call log (tap it, then Block) and do not ring it back, "
          "because a missed call from an unknown number is often just checking the line is live. In "
          "the UK register free with the Telephone Preference Service, and if it keeps happening "
          "ask your network to switch on a nuisance-call filter.",
          avoid=("silent", "silent switch", "silent mode")),
    # A number nobody knows ringing, and a code nobody asked for: the first is a nuisance with a
    # switch-off, the second is somebody trying to get into an account with your number. They are
    # different kinds of line, so they are different entries, and neither is `spam-calls`, which
    # answers a nuisance caller who got through.
    entry("unknown-calls", (("numbers i dont know", "numbers i don't know", "unknown numbers",
                             "unknown number", "numbers i do not know", "withheld number",
                             "no caller id", "caller unknown"),
                            ("keep getting", "keeps", "keep", "getting", "why", "stop", "block",
                             "calls", "call", "ringing", "ring")),
          "Do not ring the number back: a missed call from a number you do not know is often just "
          "checking the line is live, and ringing it can cost you. Block each one in the call log "
          "(tap it, then Block) and ask your network for anonymous call rejection, which refuses "
          "withheld numbers. Register free with the Telephone Preference Service, and if it keeps "
          "up ask the network to switch on their nuisance-call filter.",
          bias=1),
    entry("unasked-security-codes", (("security code", "security codes", "verification code",
                                      "verification codes", "one time code", "one time codes",
                                      "otp", "log in code", "login code", "2fa code"),
                                     ("text", "texts", "texted", "sms", "message", "messages",
                                      "didnt ask", "didn't ask", "not me", "keep getting",
                                      "keeps coming", "unexpected", "out of nowhere", "asked for",
                                      "got a")),
          "Do not use that code and do not read it out to anyone: someone has your number and is "
          "trying to sign in to an account of yours or open one in your name. Change the password "
          "on the accounts tied to that number, starting with the bank and your email, and check "
          "no one has ordered a replacement SIM. If the texts keep coming, tell your network - a "
          "SIM swap is the thing to rule out first.",
          bias=1),
    entry("bank-call-scam", (("claiming to be", "someone called", "phone call", "cold call",
                              "called saying", "called me",
                              # the same call in the words people actually use for it: "someone
                              # rang saying i owe tax and must pay now" went to the self-assessment
                              # script and was told how to register with HMRC
                              "rang saying", "rang me saying", "phoned saying", "phoned me saying",
                              "someone rang", "someone phoned", "someone saying they are",
                              "saying they are from", "saying he was from", "saying she was from",
                              "got a call", "had a call", "got a phone call", "had a phone call",
                              "rang about", "rang me about", "called me about", "called about"),
                             ("bank", "hmrc", "tax office", "tax", "national insurance",
                              "ni number", "amazon", "microsoft", "police", "fraud team", "card",
                              "dvla", "court", "bailiff")),
          "Hang up, then ring the number on the back of your card, or the one on gov.uk for a tax "
          "or DVLA call: no bank, tax office or police force asks you to move money to a 'safe "
          "account', pay a bill on the phone, or confirm a PIN, and none of them threatens you "
          "with arrest. Report it to the bank's fraud line or Action Fraud, and change your online "
          "banking password from a device the caller has not touched.",
          # "what does the tax office do with my tax code" and "who do i ring at hmrc" are the tax
          # rows; this one is only the call that arrived asking for something.
          avoid=("charge", "fee", "statement", "loan", "interest", "how much", "when do i",
                 "how do i", "what is my", "tax code", "tax return", "self assessment",
                 "deadline", "rebate", "refund", "do i need", "can i claim", "my tax")),
    entry("computer-virus", (("virus", "malware", "ransomware"),
                             ("warning", "computer", "laptop", "infected", "got", "think",
                              "check")),
          "Run a full scan with the built-in tool (Windows Security, or Malwarebytes free on a "
          "Mac), let it remove what it finds and restart. A popup saying you are infected is "
          "usually the scam itself, so close the tab and never ring the number on it. If you did "
          "install something, disconnect from the internet and change your passwords from another "
          "device."),
    entry("vpn", ("vpn", ("what", "should", "need", "use", "worth", "safe", "public wifi")),
          "A VPN encrypts the traffic between you and the internet, which is worth it on hotel and "
          "cafe wifi; it does not make you anonymous. For everyday home use you do not really need "
          "one, and the free ones usually make their money from your data, so pay a few pounds for "
          "Mullvad, Proton or similar if you want one."),
    entry("backup-photos", (("backup", "back up", "lose photos", "lost photos"),
                            ("photos", "pictures", "phone", "pictures", "memory")),
          "Turn on automatic backup: iCloud or Google Photos on a phone, and OneDrive, Google Drive "
          "or an external drive on a laptop. The rule that saves people is 3-2-1: three copies, on "
          "two kinds of storage, with one of them off-site, so a lost phone is an annoyance rather "
          "than a disaster."),
    entry("cloud-storage", (("the cloud", "cloud storage", "cloud"),
                            ("what", "mean", "storage", "safe", "use", "works", "difference",
                             # "is it worth paying for cloud storage" wanted the sense of what the
                             # thing is and what it costs, and "worth" was not in the floor, so the
                             # line went to a savings ladder on the word paying
                             "worth", "worth it", "worth paying", "pay for", "paying for", "cost",
                             "costs", "price", "monthly", "subscription", "plan")),
          "The cloud just means someone else's computer: your files are copied over the internet to "
          "a data centre and synced back to your devices. It is safer than only having them on one "
          "phone, but it is not a backup unless you keep a second copy somewhere else."),
    entry("cloud-price", (("cloud storage", "icloud", "google one", "dropbox", "onedrive",
                           "the cloud", "cloud backup"),
                          ("cost", "costs", "much", "price", "prices", "pay", "paying", "worth",
                           "month", "monthly", "subscription", "plan", "how much",
                           "which one", "cheapest", "free")),
          "The paid tiers are small money: iCloud+ gives 50GB for about £1 a month and 200GB for "
          "about £3, Google One 100GB for roughly £1.60 and 200GB for about £2.50, and Dropbox "
          "starts near £10 for 2TB. A photo is about 3MB, so 200GB holds well over 50,000 of them, "
          "and most people with a full phone need that one rather than the largest. OneDrive comes "
          "free with Office if you already pay for that, and 15GB on Google is free for good.",
          # what is left is a phone full of photos, which has its own two rows
          avoid=("full", "space", "delete", "deleted", "clean", "freed", "free up", "move",
                 "transfer", "sync", "lost", "restore", "stolen"),
          # the cloud is named, so this beats the size row and the "what is it" row when the
          # question is what a plan costs. The size row has grown a cloud of its own since, and
          # "how much does cloud storage cost" went back to it on the tie, so the bias is 3.
          bias=3),
    entry("notifications-night", (("notifications", "notification", "do not disturb", "pings",
                                   "pinging", "buzzing", "alerts", "waking me up", "wakes me up",
                                   "waking me", "woke me up", "wake me up",
                                   # a phone that rings at night is the same question as one that
                                   # pings at night, and it has the same answer
                                   "phone ringing", "phones ringing", "ringing at night",
                                   "ringing all night", "ringing overnight", "ringing in the night"),
                                  ("turn off", "switch off", "switching off", "shut off",
                                   "silence", "silent", "silenced",
                                   "night", "stop", "quiet", "sleep", "bed",
                                   "phone", "iphone", "android",
                                   # the waking itself, now that the ask above makes the line
                                   # name a device or its alerts first: "notifications keep
                                   # waking me up" names no night, no stop and no phone, and
                                   # got a chat nudge instead of this answer.
                                   "wakes me", "waking me", "woke me", "woken me",
                                   "keep waking", "keeps waking", "keeps me awake",
                                   "keeping me awake", "keeps me up")),
          "Use Do Not Disturb rather than switching the phone off: pull down the control centre "
          "(or Settings > Focus on an iPhone) and set it to run overnight. Allow calls from "
          "favourites only if you want the family to get through, and leave the phone on charge "
          "across the room.",
          # A phone left in a taxi at night is not a phone to silence: the line has to be about
          # the alerts themselves, not the word "night".
          # The wake-up phrases ("wakes me up", "keep waking me") are in the key, not here: they
          # say who is being woken, not what is doing it, so they let "my toddler wakes me up
          # every night" in - and the toddler was answered with the phone's Do Not Disturb
          # setting. A device entry is only answered when the line names the device or its
          # alerts, which is what tells the phone's wake-up apart from the child's.
          ask=("notification", "notifications", "do not disturb", "pings", "pinging", "buzzing",
               "alerts", "phone", "phones", "iphone", "android", "mobiles", "mobile",
               "ringing", "phone ringing", "phones ringing", "ringtone",
               "ringing at night", "ringing all night", "ringing overnight",
               "ringing in the night", "alarm", "alarms")),
    entry("passkey", (("passkey", "passkeys"), ("what", "use", "safe", "work", "how", "better")),
          "A passkey replaces the password with your fingerprint or face, so there is nothing to "
          "type or phish: your phone or laptop holds the key and proves it is you. Turn one on "
          "wherever an account offers it, and keep the old password as the fallback for now."),
    entry("screenshot-windows", ("screenshot", (("windows", "laptop", "pc", "computer",
                                                 "keyboard"))),
          "Press the Windows key, Shift and S together: the screen dims, you drag a box around what "
          "you want and it is copied to the clipboard, ready to paste. PrtScn copies the whole "
          "screen, and Alt+PrtScn copies just the window you are in."),
    entry("screenshot-mac", ("screenshot", (("mac", "macbook", "apple"))),
          "Press Shift, Command and 4 together, then drag a box: the file lands on your desktop. "
          "Shift+Command+3 takes the whole screen, and adding Control copies it to the clipboard "
          "instead of saving a file."),
    entry("screenshot-phone", ("screenshot", (("phone", "iphone", "android", "mobile",
                                              # the brands are how people name the phone they hold,
                                              # and "how do i take a screenshot on a samsung" was
                                              # told to say which device it was on
                                              "samsung", "galaxy", "pixel", "huawei", "xiaomi",
                                              "oneplus", "motorola", "nokia", "oppo", "honor"))),
          "On an iPhone press the side button and the volume-up button together; on most Android "
          "phones it is power and volume-down, held for a second. The picture goes to Photos or "
          "Screenshots, and you can crop it there before sending."),
    # A Chromebook and a Fire tablet are neither a Windows PC nor a phone, so the three device
    # rows above gave both "It depends on the device" - a list of the devices the person had
    # just said they were not on.
    entry("screenshot-chromebook",
          (("screenshot", "screen shot", "screen grab", "print screen"),
           (("chromebook", "chrome book", "chrome os", "chromeos"))),
          "Press Ctrl and the Show windows key together - the key with the rectangles on it, where "
          "F5 sits - and the whole screen is saved to Downloads. Add Shift and you can drag a box "
          "for part of it, and Ctrl+Alt+Show windows takes just the window in front. Screenshots "
          "lose the mouse pointer unless you turn it on first."),
    entry("screenshot-kindle",
          (("screenshot", "screen shot", "screen grab", "print screen"),
           ("kindle", "kindle fire", "fire tablet", "fire hd", "amazon fire")),
          "On a Fire tablet hold the power button and volume-down together for a second, and the "
          "picture goes into the Photos app in Screenshots. An ordinary Kindle e-reader cannot take "
          "one: there is no screenshot button, so your phone's camera is the way.",
          # the word "tablet" is a pill as well, and the repeat-prescription row keys the bare
          # noun, so the screenshot has to win on a line that names both
          bias=2),
    entry("bluetooth-car", (("car", "carplay", "android auto", "stereo", "head unit"),
                            ("bluetooth", "connect", "connecting", "disconnecting", "drops",
                             "dropping", "cutting out", "pairing", "keeps disconnecting",
                             "keep disconnecting")),
          "Delete the phone from the car's own Bluetooth list and the car from the phone's, then "
          "pair again from scratch, and check the phone is allowed to connect automatically. In the "
          "car's settings turn off the options that take the audio back (auto-play, media sync), and "
          "keep the phone's wifi off if it is trying Android Auto over wifi.",
          bias=1,
          avoid=("battery", "flat", "tyre", "engine", "mot", "petrol", "diesel", "insurance")),
    entry("bluetooth-pair", (("bluetooth", "headphones", "earbuds", "earphone", "earphones",
                             "headset", "headsets", "speaker"),
                             ("pair", "connect", "pairing", "won't connect", "wont connect",
                              "not connecting", "unpair", "remove", "forget")),
          "Put the headphones in pairing mode (usually hold the power button until a light flashes), "
          "then open Bluetooth in your phone's settings and tap the name when it appears. If it is "
          "not listed, delete the old pairing from the phone and start again.",
          # a car stereo has its own entry, and so does a television: this answer is for a phone
          avoid=("car", "carplay", "android auto", "stereo", "head unit", "van", "tv",
                 "television", "telly", "sound bar")),
    entry("cast-to-tv", (("tv", "television"), ("cast", "chrome", "airplay", "hdmi", "stream",
                                                "mirror", "from my phone", "from my laptop")),
          "On an iPhone use AirPlay from the video or the Control Centre; on Android, use the Cast "
          "icon or the Google Home app; a laptop connects best with an HDMI cable. If the TV does "
          "not show up, check both are on the same wifi network, which is the usual culprit."),
    entry("group-chat-setup", (("group chat", "group message"), ("set up", "start", "family",
                                                                 "create", "add", "make",
                                                                 "easiest")),
          "For a family with an older parent, WhatsApp is the easiest: install it, add the contacts, "
          "then tap New group, name it and pick the people. Turn on their notifications for that "
          "one chat and pin it to the top of their screen, and start by sending a photo so there is "
          "something to reply to."),
    entry("screen-eyes", (("eyes", "eye", "eyestrain", "sight", "headache", "headaches",
                           "strain", "strained"),
                          ("tired", "sore", "hurt", "hurting", "aching", "blurry", "screen",
                           "monitor", "laptop", "computer", "phone", "staring")),
          "Use the 20-20-20 rule: every 20 minutes, look at something 20 feet away for 20 seconds. "
          "Turn the brightness down to match the room, sit an arm's length from the screen with the "
          "top of it at eye level, and get an eye test if headaches keep coming back, because "
          "unnoticed short sight is what makes screens tiring.",
          # "headache" against "tired" is a whole headache question on its own: "i have a
          # headache and im tired" was the 20-20-20 rule. Only a line that also names the eyes or
          # a screen is an eye-strain question, so the ask holds the entry to those words.
          ask=("eyes", "eye", "eyestrain", "sight", "screen", "screens", "monitor", "monitors",
               "laptop", "computer", "phone", "staring", "strain", "strained", "brightness"),
          # A sore-eyed line is often a feelings line ("sore from crying all afternoon") or
          # hay fever, and neither wants the 20-20-20 rule.
          avoid=("throat", "cold", "flu", "fever", "sinus", "cough", "stomach", "tooth",
                 "cry", "crying", "cried", "tears", "tearful", "sad", "upset", "allergy",
                 "allergies", "hayfever", "hay fever", "pollen", "grief", "bereavement",
                 # A glass eye is a prosthesis, not a screen: that line has its own row.
                 "glass eye", "artificial eye", "false eye", "prosthetic", "prosthetic eye",
                 "eye socket", "ocularist"),
          # A body short of sleep is not eye strain: "im so tired i cant keep my eyes open" was
          # told to look 20 feet away every 20 minutes. A screen that tires the eyes still gets
          # the rule; a person who cannot stay awake does not.
          guard=not_a_sleepy_body),
    entry("ram-needed", ("ram", ("enough", "much", "need", "how", "8gb", "16gb", "32gb",
                                 "multitasking", "upgrade", "add")),
          ("8GB of RAM is fine for browsing, email and word processing; 16GB is worth it if you "
           "keep a lot of tabs and apps open at once, or edit photos or video. On most thin laptops "
           "you cannot add it later, so buy the 16GB now if the budget stretches.",
           "8GB will not feel slow for email, browsing and Netflix, and it is the usual size at "
           "this price. Go to 16GB only if you keep twenty tabs open or edit photos and video, "
           "because most thin laptops have the memory soldered in and cannot be upgraded after.")),
    # "screen-time-limits": family.py owns "screen-time", the age bands for small children.
    # This one is the adult's own phone - "i spend too much time on my phone", "how do i stop
    # scrolling" - and the two were written under one id, so the answer depended on the
    # phrasing. The split is what the two entries key on, so neither answer is lost.
    entry("screen-time-limits", (("screen time", "phone time", "too much time", "my phone",
                                  "doomscroll", "doomscrolling", "doom scrolling",
                                  "picking up my phone", "pick up my phone",
                                  "checking my phone", "check my phone", "my hand",
                                  "kids", "children", "my son", "my daughter", "teenager", "teen"),
                          ("reduce", "cut", "limit", "stop", "hours", "much", "so much",
                           "parental", "addicted", "spend", "spending",
                           # the habit shapes: "i keep picking it up", "first thing", "in bed".
                           # They are only reached with the ask below, which names the first
                           # person, so a child's screen time cannot land here.
                           "keep", "picking", "pick", "check", "checking", "first thing",
                           "in bed", "all the time", "always", "without thinking",
                           "too high", "too long", "on average"),
                          # the first person is what makes this the adult's own phone rather
                          # than a question about a child's, and it is the only thing that
                          # tells the two entries apart: without it this one ties with the age
                          # bands in family.py and loses on registry order.
                          ("i spend too much time", "spending too much time",
                           "on my phone too much", "on my phone",
                           "my own phone", "scroll", "scrolling", "out of hand",
                           "addicted to my phone")),
          "Set a limit rather than relying on willpower: Screen Time on an iPhone or Digital "
          "Wellbeing on Android shows the real numbers and lets you cap the worst app. Keep the "
          "phone out of the bedroom and charge it in another room, which does more than any app.",
          # The answer is about your own phone, so the line has to say so: "i spend", "my
          # screen time", "scroll". A question about a child's screen time, or one that names
          # nobody ("how many hours of screen time is too much"), is the age bands in
          # family.py, and a phone that is out of storage or out of charge is another entry.
          ask=("i spend too much time", "spending too much time",
               "i'm on my phone", "im on my phone",
               "my screen time", "too much time on my phone", "my phone too much",
               "my own phone", "addicted to my phone", "cut down my screen time",
               "reduce my screen time", "cut down my phone time", "scroll", "scrolling",
               # the same line in the shapes people type it: picking the phone up without
               # meaning to, and the doomscroll in bed. Without these the entry only fired
               # when someone named the number of hours. Every one of them is first person,
               # because "my son checks his phone in bed" is the age bands' question.
               "doomscroll", "doomscrolling", "doom scrolling", "picking up my phone",
               "pick up my phone", "check my phone", "checking my phone", "on my phone all",
               "my phone in bed", "from my phone"),
          # A child's phone is the age bands in family.py, not the adult's own habit, and a
          # phone that is hot is a heat question: the habit words here are broad enough to
          # catch both, so they are turned away at the door.
          # Someone else's habit is not yours either: "my girlfriend keeps checking my phone"
          # keyed "checking my phone" and got the set-yourself-a-limit answer, which is advice
          # for the wrong person. The relationship entries in feelings.py own that line.
          avoid=("my son", "my daughter", "my child", "my teenager", "teen", "teenager", "kid",
                 "kids", "children", "child", "his phone", "her phone", "their phone",
                 "hot", "heat", "overheating", "overheat", "warm", "charge", "charging",
                 "charged", "battery",
                 # "i spend too much" is also how a person opens a money line, and "on my
                 # takeaways" scored the phone's set-yourself-a-limit answer while the food
                 # rows sat right below it. The ask above now says "time", so the phone is
                 # named; these keep the same lines off the row if a phone word comes along
                 # for the ride ("i spend too much on my phone bill").
                 "money", "takeaway", "takeaways", "takeaway food", "eating out", "groceries",
                 "shopping", "clothes", "bills", "rent",
                 # The checking is what makes it someone else's, not the person: "my partner
                 # says im on my phone too much" is still the person's own habit, and turning
                 # it away sent it to the small child's age bands.
                 # A bare "checking my phone" matches the first person too ("i keep checking
                 # my phone" is the habit this row is for), so each phrase names the person who
                 # is doing it, or the reading of a phone that is not theirs.
                 "girlfriend keeps checking", "partner keeps checking", "husband keeps checking",
                 "wife keeps checking", "boyfriend keeps checking", "gf keeps checking",
                 "through my phone", "through my messages", "through my texts",
                 "someone else",
                 # and a person named doing it to my phone: "he checks my phone every night".
                 # Not "keeps checking my phone": keeps and keep are the same word to the
                 # matcher, so it stood down "i keep checking my phone", which is this row's own.
                 "he checks my phone", "she checks my phone", "he checks his phone",
                 "she checks her phone")),
    entry("laptop-plugged-in", (("laptop", "macbook", "notebook"), ("plugged", "plugged in",
                                                                   "on charge", "charging", "mains",
                                                                   "all the time", "overnight",
                                                                   "battery healthy", "battery",
                                                                   # a laptop left running all night
                                                                   # and one switched off are the
                                                                   # same line of advice
                                                                   "off at night", "turn it off",
                                                                   "turn off", "turned off",
                                                                   "shut down", "shutting down",
                                                                   "sleep", "leave it on", "left on")),
          "Leaving a laptop on the mains is fine: it stops charging at full and runs off the "
          "adapter, and the charge limit modes on a Mac or a Lenovo do the same on purpose. What "
          "ages the battery is heat and empty-to-full cycles, so keep the vents clear and let it "
          "drain to around 20% now and then rather than worrying about the cable.",
          avoid=("charger", "not charging", "wont charge", "won't charge", "fan", "hot", "slow",
                 "frozen", "screen", "keyboard", "disk", "virus", "wifi", "good", "best",
                 "longest", "buy", "buying", "choose", "recommend", "which", "decide")),
    # "how do i connect my laptop to the tv" was getting the smart TV's wifi setup, because the
    # TV and the word connect were the whole of its key. A laptop to a telly is a cable, a sound
    # setting and, only if there is no cable, casting.
    entry("laptop-to-tv",
          (("laptop", "pc", "computer", "macbook", "chromebook", "phone", "tablet", "ipad",
            "iphone", "android"),
           ("connect to the tv", "to the tv", "to my tv", "on the tv", "on my tv", "cast",
            "casting", "mirror", "mirroring", "screen share", "screen mirroring", "hdmi",
            "big screen", "watch on the tv", "put it on the tv")),
          _to_the_tv,
          ask=("how do i", "how can i", "how to", "whats the best way", "can i", "help"),
          avoid=("no signal", "not working", "wont connect", "won't connect", "remote", "netflix",
                 "sound bar", "soundbar", "speaker", "speakers", "printer", "mouse", "keyboard",
                 "wifi", "internet", "router", "broadband", "source code", "hdmi port on my"),
          bias=1),
    entry("tv-no-power", (("tv", "television", "telly", "smart tv", "monitor"),
                          ("broken", "broke", "dead", "wont turn on", "won't turn on",
                           "wont switch on", "won't switch on", "no power",
                           "nothing happens", "stopped working", "wont come on",
                           # "whats wrong with my tv" is the whole set, and the words for it are
                           # these: the line names no part of it, so the plug is the first thing
                           # to check and this is the row that says so. Without them the line
                           # reached tonight's listings (a bare "whats") and then a card about
                           # how a screen works, neither of which is what was asked.
                           "wrong", "wrong with", "fault", "faulty", "problem with")),
          # A set that has done nothing at all is checked at the plug first, because that is what
          # is wrong most of the time and it costs nothing: the fuse in the moulded plug, the
          # standby light, and the same socket with something else in it. Past that it is the set.
          "Start at the plug: a dead set is usually the fuse in the plug or the socket, so put "
          "something else in the socket to test it and, if that works, change the 3A or 5A fuse in "
          "the TV's plug. If the standby light never comes on at all after that, the power board is "
          "the usual part, and a repair shop will quote £60 to £120 to look at it - against £250 to "
          "£500 for a new set, so an older TV is usually not worth repairing.",
          bias=1,
          # the picture, the wifi and tonight's listings are other rows, and a cracked screen is
          # its own answer
          avoid=("no signal", "signal", "picture", "cracked", "crack", "screen", "wifi",
                 "internet", "online", "apps", "remote", "sound", "speakers", "tonight",
                 "watch", "watch on", "colour", "color", "flicker", "bracket", "mount",
                 "laptop", "phone", "computer", "hdmi", "lead", "cable", "freeview",
                 "aerial", "sky", "licence",
                 # a monitor that watches a body is not a set in the corner: the blood pressure
                 # machine, the glucose meter and the baby monitor have nothing to do with a fuse
                 "blood pressure", "pressure monitor", "heart monitor", "heart rate",
                 "glucose", "sugar monitor", "thermometer", "temperature", "pulse", "oxygen",
                 "sats", "baby monitor", "sleep monitor", "activity tracker")),
    entry("tv-not-online", (("tv", "television", "telly", "smart tv", "fire stick", "roku"),
                            ("connect", "internet", "online", "wont connect", "won't connect",
                             "offline", "wifi", "network", "apps", "wont open", "won't open",
                             "wont load", "won't load", "freezes", "frozen", "keeps closing",
                             "wont start", "not working", "to work", "working", "work")),
          "Set it up in this order: the TV's own network settings first (Settings > Network, pick "
          "your wifi, type the password with the remote), then test with one built-in app. If the "
          "wifi list is empty on a smart TV, restart the router and the TV, and check the TV is on "
          "the 2.4GHz band, which older sets need; a Fire Stick or Roku plugged into the HDMI port "
          "is the cheap fix for a TV whose own apps have stopped working.",
          bias=1,
          # a laptop, a phone or a lead to the TV is the entry above, not the set's own wifi:
          # a lead from a laptop needs no network at all
          # a remote that does nothing is `tv-remote-dead`'s question, not the set's wifi: the key
          # holds "not working", which a dead remote says too
          avoid=("remote", "remote control", "zapper", "batteries", "battery",
                 "laptop", "pc", "computer", "macbook", "phone", "tablet", "ipad", "hdmi lead",
                 "hdmi cable", "hdmi", "cable", "lead", "plug in", "plugged", "adapter", "cast",
                 "casting", "mirror", "mirroring", "airplay", "chromecast", "monitor",
                 "second screen", "sound", "speakers", "soundbar", "headphone", "headphones",
                 "earbuds", "earphones", "speaker", "sound bar", "aux")),
    entry("tv-no-signal", (("no signal", "no picture", "loses signal", "losing signal",
                            "loses the signal", "keeps cutting out", "cutting out", "blank screen",
                            "says no signal", "black screen", "signal"),
                           ("tv", "telly", "television", "monitor", "projector", "freeview",
                            "sky", "sky box", "fire stick", "roku", "hdmi", "screen")),
          "Change the cable first, because a tired HDMI lead loses the picture for a second and "
          "the set shows 'no signal': unplug both ends and push them back in, then try the other "
          "HDMI port and a lead you know works. Check the input with the remote (Source or Input) "
          "so the TV is on the socket the box is in, and if it is a set-top box, aerial or "
          "satellite, restart that box at the wall rather than the TV. A set that says 'no signal' "
          "while the power light is on is nearly always the cable or the source; a picture that "
          "goes and comes back on its own is the cable or a loose aerial.",
          bias=1,
          ask=("no signal", "no picture", "losing signal", "signal", "cutting out", "blank screen",
               "black screen"),
          avoid=("phone", "iphone", "android", "mobile", "handset", "wifi", "wi fi", "router",
                 "broadband", "internet", "battery")),

    entry("link-safe", (("link", "links", "website", "site", "url", "text message", "email"),
                        ("safe", "scam", "fake", "trust", "genuine", "legit", "click",
                         "phishing")),
          "Do not click to find out: hover over the link or long-press it and read the real "
          "address, because scammers use lookalike domains like rnicrosoft.com. Check the address "
          "is exactly the company's own, with https and no extra words before the dot, and if you "
          "are still unsure, type the company's address into the browser yourself rather than "
          "using the link.",
          # money already gone to a site is a chargeback, not a link to check: "how do i get my
          # money back from a scam website" was being told how to read a URL. It is the *wanting
          # it back* that moves the line, not the buying: "i paid a fake website for a coat" was
          # still a question about the address, and standing down for "paid for" and "i bought"
          # left it with a shrug.
          avoid=("password", "wifi", "boiler", "recipe", "therapist", "train", "flight",
                 "money back", "took my money", "refund", "refunded", "get it back",
                 "cancel the payment", "charged", "reversed", "dispute",
                 "report them", "report the")),
    entry("order-not-arrived", (("order", "parcel", "delivery", "package", "online", "bought",
                                 "shop", "seller", "courier", "refund", "return",
                                 # the line often names only the tracking page, with no parcel
                                 # word at all: "tracking says delivered but nothing here" was a
                                 # nothing reply, so "tracking" is a noun here in its own right
                                 "tracking", "tracking page", "tracking number",
                                 # the carrier is named far more often than the parcel is, but a
                                 # bare "post office" also reaches its opening times and taking a
                                 # parcel back without the label, so the carrier only counts
                                 # when it is the one talking.
                                 "post office said", "post office says", "post office told me",
                                 "royal mail said", "royal mail says", "evri", "hermes", "dpd",
                                 "yodel", "parcelforce", "delivered",
                                 # NOT "delivery driver": with "damaged" in the second half it
                                 # took "the delivery driver damaged my front door", which is
                                 # consumer.py's courier-damage row - the parcel arrived and the
                                 # door is what broke.
                                 ),
                                ("not arrived", "hasnt arrived", "hasn't arrived",
                                 # "doesnt arrive" is the same fact in the present tense, and
                                 # "what should i do if my parcel doesnt arrive" was a hedge
                                 "doesnt arrive", "doesn't arrive", "never arrives",
                                 "arrived",
                                 "missing", "lost", "return", "refund", "late", "where is",
                                 "still waiting", "damaged", "track",
                                 # the tracking page is what the person is reading: "says
                                 # delivered but there's nothing here" is the whole question,
                                 # and it was reaching no entry at all
                                 "says delivered", "said delivered", "marked as delivered",
                                 "marked delivered", "nothing here", "not there", "never got it",
                                 "never got", "never received", "didn't get it", "didnt get it",
                                 "lost my parcel", "lost my order", "safe place", "left outside",
                                 "leaves it outside", "no sign of it",
                                 # "my parcel didnt arrive" was reaching post collection times:
                                 # the apostrophe is what the misspelt-avoid check forgives, the
                                 # plain wording still needs to be a key of its own
                                 "didnt arrive", "didn't arrive", "never arrived",
                                 "didnt turn up", "didn't turn up", "never turned up",
                                 # "came" is the verb people use for a parcel as often as
                                 # "arrived": "what should i do if my parcel never came" was a
                                 # hedge, because only the arrived/turned-up shapes were keyed.
                                 "never came", "hasnt come", "hasn't come", "didnt come",
                                 "didn't come", "hasnt come yet", "hasn't come yet",
                                 "not come yet", "still not come", "never come",
                                 "nothing came", "nothing turned up", "nothing arrived",
                                 "nothing was there",
                                 # a parcel left somewhere and a carrier that says it delivered
                                 # are the same question, and neither had a word in this group
                                 # to carry them: "the courier left my parcel somewhere i cant
                                 # find" and "the post office said it was delivered but nothing
                                 # came" were a chat acknowledgement and a hedge.
                                 "cant find", "can't find", "somewhere", "no sign",
                                 "royal mail", "said it was delivered",
                                 "says it was delivered", "said delivered", "says delivered",
                                 "marked as delivered")),
          "Contact the seller first rather than the courier: the contract is with the shop, and it "
          "has to refund or replace a parcel that never arrived, even if the tracking says it was "
          "delivered. Check the photo, the safe place, the bins and the neighbours first, keep the "
          "tracking page, and ask in writing for a replacement or refund within 14 days. If they "
          "stall, charge it back on the card.",
          # a driver who damaged the wall or the car is the consumer domain's claim: the parcel
          # itself is fine
          avoid=("damaged my door", "damaged my wall", "damaged my gate", "damaged my fence",
                 "damaged my car", "damaged my house", "damaged the door", "damaged the wall",
                 "knocked my wall", "knocked my gate", "hit my car", "scraped my car",
                 "dented my car",
                 "takeaway", "pizza", "chinese", "curry", "food", "restaurant", "tesco", "asda",
                 # a tax return that is late is HMRC's, not a parcel going back to the shop:
                 # "my tax return is late" got this entry because "return" and "late" are both
                 # in the key. The tax words stand it down; lifeadmin's late-return row answers.
                 "tax return", "tax returns", "self assessment", "self-assessment", "hmrc",
                 "income tax", "tax bill", "tax office",
                 # A person who gets lost on the way somewhere is not a parcel in the post:
                 # "she keeps getting lost on the way to the shop" was answered with the
                 # chargeback advice. The bare "lost" in the key stays, so "my parcel got lost"
                 # and "my order is lost" still reach this entry.
                 "gets lost", "getting lost", "lost his way", "lost her way", "lost their way",
                 "loses his way", "loses her way",
                 "laptop", "phone", "fridge", "washing machine", "sofa", "mattress", "car",
                 "furniture", "tumble dryer", "dishwasher", "oven", "coat", "shirt", "dress",
                 "shoes", "trousers", "jeans", "jumper", "trainers", "suit", "sale", "clothes",
                 # The seller is not the buyer, and "tell the seller" is advice for the person
                 # waiting. The sender's own words are the claim in lifeadmin: "can i track a
                 # parcel i sent", "i sent a parcel and the tracking has not updated" and "i
                 # sold something on ebay" were all being sent to contact the seller - who is
                 # the person reading, or a buyer waiting on them.
                 "i sent", "we sent", "i posted", "we posted", "i shipped", "i sold",
                 "parcel i sent", "parcel i posted", "the one i sent", "i have sent",
                 "i've sent", "my buyer", "buyer says")),
    entry("free-app-nothing-to-pay",
          ((("facebook", "instagram", "snapchat", "tiktok", "twitter", "whatsapp",
             "messenger", "reddit", "linkedin", "pinterest", "discord", "youtube",
             "google maps", "gmail"),
            ("stop paying", "stop paying for", "paying for", "pay for", "cost", "costs",
             "cost me", "price", "how much", "is it free", "free", "subscription",
             "subscriptions", "monthly", "charged", "charge", "am i paying", "do i have to pay",
             "do i pay", "does it cost", "bill", "cancel"))),
          _free_app_reply,
          ask=("is", "does", "do", "how", "why", "am", "the"),
          # "how do i stop paying for facebook" also reads as "pay for" + a thing to buy, which
          # is the three-rungs-of-credit row: nothing about a free account is financed, so the
          # named app wins over the money reading.
          bias=3,
          # The apps that are not free are the subscription row's, and "how do i stop paying for
          # youtube premium" is a real payment: the free tier and the paid tier share the name,
          # so a paid tier named in the line keeps this row out.
          avoid=("premium", "youtube premium", "music premium", "ad-free", "ad free",
                 "youtube tv", "youtube music", "facebook marketplace", "business account")),
    entry("cancel-subscription", (("subscription", "subscriptions", "renewing", "renewal",
                                   "charged", "free trial", "trial", "trials",
                                   # A named service is a subscription even when the word is not
                                   # in the line: "how do i cancel my netflix" and "how do i
                                   # cancel amazon prime" got "I don't know enough to answer that
                                   # honestly", and the answer above is the one they wanted. The
                                   # avoid below keeps a fault with the service out of here.
                                   "netflix", "spotify", "audible", "amazon prime", "prime video",
                                   "disney plus", "disney+", "now tv", "nowtv", "apple tv",
                                   "youtube premium", "kindle unlimited", "itunes", "sky go",
                                   "paramount plus", "discovery plus", "hayu", "britbox",
                                   # "sky tv is too expensive can i cancel" was reaching the
                                   # picture card on the bare product word "sky", which is a
                                   # picture service here and a bill there
                                   "sky", "sky tv", "sky q", "virgin media", "bt tv")
                                  # the ones people pay for without saying "subscription":
                                  # "how do i stop paying for dropbox" and "cancel my adobe"
                                  # were a debt card and a hedge
                                  + PAID_SERVICES,
                                  ("cancel", "stop", "stop paying", "get rid", "refund",
                                   "free trial", "how", "end", "before")),
          "Cancel from the place you pay, not from the app: on an iPhone it is Settings > your "
          "name > Subscriptions, on Android it is Play Store > Payments and subscriptions. A free "
          "trial that is about to renew has to be cancelled at least 24 hours before or it renews, "
          "and cancelling a subscription turns off the renewal rather than the access you paid for.",
          # "is it worth ringing the insurer before renewing" reached this entry, because
          # "renewing" and "before" are in the key and the `avoid` named the noun ("insurance")
          # but not the person. An insurer is not an app, and ringing one is not cancelling.
          avoid=("gym", "magazine", "newspaper", "tv licence", "council", "membership", "licence",
                 # an account is the account rows' line: "how do i close my netflix account" is
                 # the deletion steps, not the renewal date
                 "account", "accounts",
                 "license", "passport", "mot", "road tax", "car tax", "insurance", "visa",
                 "tenancy", "lease", "prescription", "season ticket", "driving",
                 "insurer", "insurers", "insurance company", "renewal quote",
                 # the bare "quote" is not an insurer: "cancel my subscription, i was quoted 3
                 # months free" is the subscription's own line, and disabling this entry on the
                 # noun cost it the answer. What makes a quote an insurer's is the renewal.
                 "insurance quote", "renewal quote", "quote arrived", "their quote", "my quote",
                 # a fault with the service is the streaming entry's question, not the
                 # subscription's: "netflix keeps stopping" and "spotify wont play" are not
                 # somebody asking to cancel
                 "keeps stopping", "keeps cutting", "keeps freezing", "buffering", "buffers",
                 "wont play", "won't play", "wont load", "won't load", "not working",
                 "no sound", "picture", "log in", "login", "password", "hacked",
                 "keeps logging", "down again", "wont start", "won't start",
                 # the price of the service is its own question, and "how" is in the ask group:
                 # "how much is netflix a month" was answered with the cancellation steps. Every
                 # cancel line says cancel, stop paying or get rid, so the price words close that
                 # door without touching them.
                 # the bare "price" is not here on purpose: the spelling reader takes "prime"
                 # for a slip of it, so "how do i cancel amazon prime" would have been turned
                 # down by the very entry that answers it.
                 "how much", "how many", "a month", "per month", "monthly", "a year",
                 "per year", "cost", "costs", "the price", "price of", "worth it", "cheaper",
                 "cheapest", "a deal"),
          guard=_a_renewal_that_takes_time),
    entry("clear-cache", (("cache", "storage", "space"), ("clear", "empty", "free up", "full",
                                                         "delete", "slow")),
          "Clear the cache rather than the data: on Android it is Settings > Apps > the app > "
          "Storage > Clear cache, and on an iPhone the same space goes by offloading the app "
          "(Settings > General > iPhone Storage > Offload App), which keeps your logins. In a "
          "browser, clear cached images and files only, and you stay signed in everywhere.",
          avoid=("laptop", "macbook", "windows", "computer", "pc")),
    entry("internet-down", (("internet", "broadband", "wifi", "wi fi", "connection"),
                            ("down", "offline", "outage", "no internet", "not working",
                             "stopped working", "disconnected", "nothing works")),
          "Check the router lights first: no light on the internet or WAN light means the problem is "
          "the line, so look up your provider's service status page on your phone - a postcode "
          "outage is the most common cause and needs waiting, not fiddling. If the lights are "
          "normal, unplug the router for 30 seconds and plug it back in, then try a cable; mobile "
          "data on the phone gets you back online while you wait.",
          avoid=("tv", "printer", "console", "xbox", "playstation", "watch", "doorbell",
                 "thermostat", "car", "boiler", "slow", "speed", "slower",
                 # "can i haggle my broadband down" is a price, and the word "down" made it the
                 # line-is-down answer. That is ring-about-a-price's line.
                 "haggle", "haggling", "haggled", "discount", "discounts", "better price",
                 "lower price", "cheaper", "price", "bill") + ABROAD,
          bias=1),
    entry("printer-ink", (("ink", "cartridge", "cartridges", "toner"), ("out", "empty", "ran out",
                                                                        "run out", "replace",
                                                                        "cheap", "cheaper",
                                                                        "refill", "dried",
                                                                        "streaky", "faded",
                                                                        "expensive")),
          "Compatible cartridges cost a third of the branded ones and work in most printers, so "
          "check the model number and buy those online. Before replacing one, take it out and give "
          "it a gentle shake and wipe the gold contacts with a dry cloth, which often gets a few "
          "more pages out of a cartridge that is only streaky; set the printer to draft or greyscale "
          "to make a cartridge last much longer.",
          bias=1,
          ask=("printer", "print", "inkjet", "cartridge", "cartridges", "toner")),
    # --- the everyday gaps people still ask about ---------------------------
    entry("kid-first-phone", (("kid", "kids", "child", "children", "son", "daughter", "teenager",
                               "10 year old", "11 year old", "12 year old"),
                              ("first phone", "phone", "smartphone", "mobile"),
                              # "should" is not in this part: a three-part key matches on any
                              # two of them, so "which phone should i get" was answering with
                              # the age a child should have one.
                              # "ready" on its own was enough with a child word: "my son cant
                              # wake up to get ready for work" answered with the age a child
                              # should have a phone. "ready for" stays in ask, where it gates.
                              # "set up" is not a key part on its own: with a child word it was
                              # two parts of three, so "how do i set up a savings account for my
                              # child" was the age a child should have a phone. Every line that
                              # needs it also names the phone, which is the second part; the ask
                              # list below still holds it, so "how do i set up parental controls
                              # on my son's phone" keeps its gate.
                              ("age", "how old", "too young", "safe", "safely", "parental")),
          _first_phone,
          # bias=1: the screen-time card in family.py scores the same on "phone" + "year old",
          # and this is the narrower question of the two.
          bias=1,
          ask=("first phone", "first mobile", "too young", "what age", "how old", "old enough",
               "ready for", "parental", "set up", "setup", "should i get",
               # what to pay for the handset is this card's question too
               "spend", "spending", "afford", "budget", "wants a phone", "want a phone",
               "wants one", "wants a mobile", "asking for a phone", "which phone", "what phone",
               "second hand", "hand me down", "sim only", "buy him", "buy her", "buy them",
               "buy a phone", "buy my son", "buy my daughter", "how much is a phone",
               # "how much is a good phone for a 12 year old" was the screen-time card, because
               # the age and "how much" were once enough to reach it and this card's own ask
               # words were none of them. What to pay for a child's handset is this card's
               # question, so every price shape is in the ask above.
               "how much", "how much is", "how much does", "how much for", "cost", "price",
               # "my son needs a phone for secondary school" was answered with the council's
               # school admissions page, and "my daughter needs a phone for high school" with the
               # screen-time card: needing a phone for a school run is this card's question.
               "needs a phone", "need a phone", "needs a mobile", "need a mobile"),
          # "how old is she?" in a chat about a child is a memory question, not a phone one
          avoid=("how old is she", "how old is he", "how old is it", "how old are they",
                 "how old is my son", "how old is my daughter", "how old is my kid",
                 "how old am i", "how old was i",
                 # "set up parental controls" is a how-to on a phone already owned, and the
                 # word "parental" in the ask list above was catching it
                 "parental controls", "parental control", "restrict content",
                 "content restrictions", "screen time",
                 # A child left unsupervised is the home-alone question, not a phone one.
                 # "what age can a child stay home alone" matched child + age here and got the
                 # age a child should have a phone, while the home-alone card answered
                 # "can i leave my child home alone" next to it.
                 "home alone", "left alone", "on their own", "on his own", "on her own",
                 "unsupervised",
                 # the child and the age are not a phone: "what age should my child get pocket
                 # money" matched two parts of this key and got the first-phone card, and money
                 # is one table in money.py
                 "pocket money", "allowance", "chores", "money")),
    # "how do i save a document as a pdf" was the honest shrug, and it is one of the commonest
    # small jobs there is: it is the same three steps on Word, on a Mac and on a phone. The
    # converter rows keep their own lines ("how do i convert a word document to pdf" is about
    # getting an editable file back out of a PDF), so `convert` and `edit` stand this one down.
    entry("save-as-pdf",
          (("pdf",),
           ("save", "saves", "saving", "make", "create", "make a", "export", "document",
            "spreadsheet", "email", "send", "photo", "picture", "print to", "printing to",
            "print as", "print out as")),
          "In Word or Excel use File then Save As (or Export) and pick PDF; on a Mac, File then "
          "Print and choose Save as PDF from the bottom of the print box, which works in any app; "
          "on a phone, tap Share then Print and pinch out on the preview to turn it into a PDF, or "
          "just send the page to yourself and choose PDF. A scanned sheet is the same idea in the "
          "Files or Notes app, which saves straight to PDF.",
          bias=1,
          avoid=("convert", "converting", "edit", "editable", "fill in", "sign a pdf", "password",
                 "protected", "scanned pdf", "read only", "combine", "merge", "split",
                 "compress", "reduce the size", "smaller", "shrink", "size", "too big",
                 "wont open", "corrupt")),
    entry("scan-document", (("scan", "scanner", "photocopy"),
                            ("document", "paper", "form", "letter", "passport", "receipt",
                             "sign", "email", "pdf", "phone", "photo", "photos", "picture",
                             "pictures", "old photos", "photograph", "photographs")),
          "Use the phone: the Notes app on an iPhone has Scan Document, and on Android the Files "
          "app or Google Drive has Scan, both of which straighten the page and make a PDF you can "
          "email. Lay the paper flat in good light, hold the phone still above it, and check the "
          "edges are in before saving.",
          bias=1),
    entry("clean-screen", (("clean", "cleaning", "wipe", "smudges", "smears", "fingerprints",
                            "greasy",
                            # "my tv screen has marks" was the AERIAL card (it looked at the
                            # picture, not the glass) and "how do i get smudges off the tv" was
                            # the same: a mark on a screen is a mark to wipe off.
                            "mark", "marks", "smudge", "smudged", "dirty", "dusty", "dust",
                            "sticky", "sticky marks", "scuff", "scuffs"),
                           ("screen", "display", "phone", "laptop", "monitor", "tv", "tablet")),
          "A dry microfibre cloth is all a phone screen needs, and a fingerprint-marked one comes "
          "up with a single drop of water on the cloth, never sprayed on the screen. On a laptop "
          "or TV, use water only: alcohol and kitchen spray take the coating off, and paper towels "
          "leave fine scratches.",
          bias=1,
          avoid=("case", "cover", "keyboard", "bag", "sleeve", "air vent", "vacuum", "dust",
                 "mould", "mildew", "shower", "bath", "window", "windscreen", "oven", "glass",
                 "door", "fence", "patio", "port", "charging port", "charging point", "speaker",
                 "grille", "earpiece", "lens", "camera")),
    entry("cheap-phone-deal", (("phone", "iphone", "handset", "mobile", "sim only", "sim-only",
                                "pay as you go", "payg", "contract", "airtime"),
                               ("cheapest", "cheap", "best deal", "deal", "save money", "sim only",
                                "sim-only", "pay as you go", "payg", "contract", "refurbished",
                                "upgrade", "worth")),
          "The cheapest way is usually a refurbished handset bought outright plus a SIM-only "
          "monthly plan: the same network for £8 to £15 a month instead of £30 to £50 bundled into "
          "a contract. Check the refurb is grade A or better with a 12-month warranty, and buy "
          "from the maker or a name you know rather than a marketplace seller.",
          bias=2,
          ask=("cheapest", "cheap", "deal", "deals", "sim only", "sim-only", "contract", "pay as you go",
               "payg", "save", "upgrade", "monthly", "tariff", "worth switching"),
          avoid=("battery", "charging", "screen", "cracked", "slow", "storage", "hot", "wifi",
                 "lost", "stolen", "repair", "water", "virus", "bill is", "data", "cancel",
                 "cancelling", "died", "death", "passed", "funeral", "estate", "probate",
                 "bereavement", "late father", "late mother",
                 # "how do i get out of my contract" is the leaving question, not the price one
                 "get out", "getting out", "exit", "terminate", "break the contract",
                 "break my contract", "end my contract", "leave")),
    # "how much is a phone" and "how much should i spend on a phone" were answered with the
    # screen-time limit for a child (the device word and "how much" are both in that key), and
    # every other price shape reached the honesty line, "Prices move too fast for me to know".
    # What a phone costs is a sum a knowledgeable friend can give: the three bands, and which
    # one is worth the money. The deal rows keep their lines, so "cheapest" and "sim only"
    # stand this one down.
    # A console for a child is a buying question, and it was answered with what to do after the
    # console had been bought: "my son wants a games console", "what console should i buy my son"
    # and "should i get my son an xbox" were the family-settings card, and "is a nintendo switch
    # good for a 7 year old" was the screen-time limit.
    entry("which-console-for-a-child",
          # "console" is in "games console" and "game console", so the plural and the two-word
          # forms need no listing of their own - and "games machine" was matching "board games
          # for christmas", which is the board-game card's line.
          (("console", "xbox", "playstation", "ps5", "ps4",
            "nintendo", "nintendo switch", "switch oled", "switch lite", "steam deck",
            "switch"),
           ("buy", "buying", "get", "getting", "should i", "which", "what", "good for",
            "worth", "first", "best", "recommend", "better", "wants", "want", "christmas",
            "birthday", "year old", "year old", "old", "age", "for a", "for my")),
          "Match it to the age and the room rather than to the adverts. Under about ten, a "
          "Nintendo Switch is the safe first console: it comes with a game, works handheld or on "
          "the television, and Nintendo's free parent app sets a daily limit and turns it off at "
          "bedtime. For a teenager who plays with friends online, an Xbox Series S (about £250) or "
          "a PS5 is the one to look at, and each needs a paid plan on top - Game Pass Core or PS "
          "Plus, about £7 to £11 a month - before anyone can play online at all. Whichever you "
          "pick, set it up as a child account with your email and set the spending limit before "
          "the first game is opened, because that is what stops the £50 of extras.",
          bias=3,
          # the settings and the faults after the console is in the house are other rows, and a
          # broadband or an energy switch is not a console at all
          avoid=("parental control", "parental controls", "family settings", "set up", "setting up",
                 "how do i limit", "screen time", "time limit", "not connecting", "wont connect",
                 "won't connect", "not working", "wont turn on", "won't turn on", "wifi",
                 "broadband", "provider", "energy", "tariff", "switch my", "switch to a",
                 # "switch" is also the verb in every change-your-supplier line: those are
                 # accounts, banks, heating and networks, never a games console
                 "switch bank", "switch banks", "switch account", "current account", "bank",
                 "banks", "network", "sim only", "sim-only", "heating", "boiler", "supplier",
                 "insurance", "mortgage", "job", "school", "doctor", "dentist", "vet",
                 "socket", "plug", "light", "lights", "lamp", "engine", "phone", "iphone",
                 "battery", "settings", "account", "on and off", "off and on"),
          ),
    # A phone that still works is not a repair question and not a price question: "is the new
    # iphone worth it" and "is the iphone 16 worth it" were the repair-or-replace card ("repair it
    # if the phone is under four years old"), and "should i upgrade to the new iphone", "is it
    # worth upgrading my phone" and "should i buy the new iphone or wait" were the refurbished-deal
    # card. All of them ask whether the jump is worth the money, which is a question with an
    # answer: what the person already has decides it.
    entry("new-phone-worth-it",
          # The noun has to be the phone. A bare "upgrade" in this group took "is it worth
          # upgrading my laptop", "should i upgrade my broadband" and "is it worth upgrading to a
          # heat pump", every one of which has its own answer.
          (("iphone", "phone", "smartphone", "handset", "mobile", "android", "galaxy", "pixel",
            "new phone", "new iphone", "next phone"),
           ("worth it", "worth", "worth buying", "worth the money", "worth upgrading",
            "should i upgrade", "should i wait", "wait for", "or wait", "wait another year",
            "upgrade", "upgrading", "every year", "this year", "next year", "skip",
            "hold off", "new one", "the new", "latest")),
          "Three things settle it, and none of them is the model year. If what you have still "
          "holds a charge to the evening, opens apps without a wait and still gets security "
          "updates, a new phone buys you a better camera and a nicer screen rather than a faster "
          "life, so waiting a year costs you nothing. Upgrade when the battery has gone (a service "
          "is £50 to £90 on most phones), when the updates have stopped, or when the repair costs "
          "more than the handset is worth. When you do buy, take last year's model outright: it is "
          "£250 to £400 instead of £800 to £1,200 for the same phone, with three or four years of "
          "updates still to come.",
          bias=4,
          # what the phone costs, where to buy it and what is wrong with it are other rows
          avoid=("refurbished", "refurb", "second hand", "second-hand", "sim only", "sim-only",
                 "cheapest", "cheap", "deal", "deals", "how much", "cost", "price", "contract",
                 "contracts", "tariff", "how do i sell", "sell my", "trade in", "trade-in",
                 "cracked", "crack", "broken", "not charging", "wont charge", "won't charge",
                 "battery health", "battery life", "wifi", "virus", "slow", "lost", "stolen",
                 "insurance", "repair", "replaced the screen", "water", "kid", "kids", "child",
                 "children", "son", "daughter", "year old", "parental", "screen time")),
    entry("phone-price", (("new phone", "phone", "iphone", "smartphone", "handset", "mobile",
                           "android"),
                          ("how much", "cost", "costs", "price", "prices", "spend",
                           "budget", "afford", "expensive", "pay")),
          "A good new phone is £250 to £500, a budget one £120 to £250, and a flagship £800 to "
          "£1,200; a grade-A refurb or last year's model is about half its launch price and does "
          "the same job. Buy the handset outright and pair it with a SIM-only plan at £8 to £15 a "
          "month, because a bundled contract usually costs more over two years.",
          ask=("how much", "cost", "price", "spend", "budget", "afford", "pay"),
          bias=1,
          # what a phone costs is not what is wrong with it, what it does, what it is worth
          # second-hand, or what a child may have
          avoid=("repair", "repairs", "cracked", "crack", "screen", "battery", "charging",
                 "charger", "bill", "contract", "tariff", "data", "storage", "space",
                 "lost", "stolen", "insurance", "case", "cover", "sell", "selling", "sold",
                 "worth", "trade in", "trade-in", "sim only", "sim-only", "deal", "deals",
                 "cheapest", "cheap", "refurbished", "upgrade", "photos", "camera",
                 "slow", "virus", "wifi", "wi fi", "backup", "reset", "texts", "email",
                 # a phone for a child is the first-phone row's question, at the age they ask
                 "kid", "kids", "child", "children", "son", "daughter", "teenager", "teen",
                 "year old", "school", "parental", "screen time")),
    # A machine that has stopped answering wants the same first move whether it will not come on
    # ("my tablet wont turn on") or has frozen with the power on ("my kindle is frozen") or has to
    # be restarted on purpose ("how do i restart my laptop"): hold the power button down. The
    # restart words reach here now, and a kindle and an e-reader are the same machine as a laptop
    # for this question.
    entry("laptop-no-power", (("laptop", "macbook", "notebook", "computer", "tablet", "ipad",
                               "kindle", "e reader", "e-reader", "ereader", "chromebook",
                               "surface", "desktop", "pc"),
                              ("wont turn on", "won't turn on", "wont start", "won't start",
                               "dead", "no power", "nothing happens", "black screen",
                               "restart", "restarting", "reboot", "rebooting", "soft reset",
                               "how do i restart", "how to restart",
                               # "my laptop is broken" is the same question with none of the
                               # symptoms named: a machine that has stopped is worth the reset
                               # before anything else, and the bare fault words reach here now
                               # that the refund ladder no longer takes them.
                               "broken", "broke", "stopped working", "isnt working",
                               "isn't working", "wont work", "won't work", "not working")),
          "Hold the power button down for 15 seconds with the charger plugged in, then press it "
          "once: that clears a stuck state more often than anything else. If there is no light on "
          "the charger at all, try another socket and cable; if the charger lights up but the "
          "laptop is still dead, the battery or the power board is the likely fault and a repair "
          "shop can test it in minutes.",
          bias=2,
          # "dead, won't even charge" is a charging fault: leave it to that entry, and a part of
          # the machine that has stopped (a keyboard, a fan, a speaker) is not the whole machine
          # failing to come on
          # "how often should i restart my computer" is a frequency question and the restart-computer
          # row answers it; a machine that has power and has stopped answering is the force-off row,
          # which is device-neutral, and a phone is that phone's own rows.
          avoid=("charge", "charging", "charger", "chargers",
                 "keyboard", "keypad", "touchpad", "trackpad", "mouse", "screen", "display",
                 "battery", "fan", "wifi", "wi fi", "wireless", "speaker", "speakers", "sound",
                 "port", "usb", "hinge", "drive", "storage", "webcam", "camera", "microphone",
                 "slow", "hot", "overheating", "overheats", "loud",
                 "how often", "often", "every day", "each day", "regularly", "keeps asking",
                 "asks me", "asking me", "frozen", "froze", "has frozen", "stuck",
                 "not responding", "unresponsive", "locked up",
                 "phone", "iphone", "android", "handset", "mobile")),
    entry("laptop-wifi", (("laptop", "macbook", "notebook", "computer", "pc"),
                          ("wifi", "wi fi", "wireless", "network", "internet")),
          "Turn the laptop's wifi off and on again first (the aeroplane-mode key or the wifi icon), "
          "then forget the network and rejoin it, which clears most of these. If the laptop sees "
          "no networks at all while a phone sees several, the wifi card or its driver is the "
          "problem: restart the laptop once before assuming that, and check the little wifi switch "
          "some older laptops still have on the side.",
          bias=3,
          # "my wifi keeps dropping on my phone but works on my laptop" is a question about the
          # phone, and the laptop steps below would send them to the wrong machine.
          avoid=("on my phone", "my phone", "my iphone", "my android", "iphone", "android",
                 "on the phone", "my mobile", "my tablet", "my ipad")),
    entry("video-call-freezing", (("zoom", "video call", "video calls", "facetime", "skype",
                                   "webcam", "ms teams", "microsoft teams", "teams call",
                                   "teams meeting", "teams app", "teams keeps", "teams freezes",
                                   "teams freezing", "teams is laggy", "teams lags"),
                                  ("freez", "lag", "laggy", "stutter", "frozen", "blurry",
                                   "dropping", "keeps cutting", "glitchy", "slow")),
          "Sit closer to the router or use a cable, and shut the other heavy things on the laptop: "
          "a browser with twenty tabs is usually the cause of a freezing call. Turn the video off "
          "when the sound matters more, and in Zoom or Teams set the video to a lower quality - a "
          "still picture and clear sound beats a frozen face.",
          bias=1),
    entry("phone-data-usage", (("data", "gb", "megabytes", "allowance"), ("how much", "use",
                                                                          "using", "left",
                                                                          "run out", "check",
                                                                          "month", "allowance",
                                                                          # the same ask said as a
                                                                          # problem: "how do i stop my
                                                                          # phone eating my data" has
                                                                          # the word data and no use
                                                                          # word, so it was a search,
                                                                          # and "stop" is only ever the
                                                                          # stop-the-bill sense here
                                                                          # because the first group has
                                                                          # to name data, gb or an
                                                                          # allowance
                                                                          "stop", "stopping", "eating",
                                                                          "eat", "eats", "so much",
                                                                          "too much", "wasting")),
          "The phone already counts it: Settings > Mobile data on an iPhone, or Settings > Network "
          "> Data usage on Android, shows the month's total and which apps are eating it. Video "
          "and social apps are nearly always the top two, and turning off background refresh and "
          "auto-play on mobile data usually halves it.",
          # A luggage allowance, a tax-free allowance and a phone's data allowance are different
          # allowances: "how much is the tax free allowance" was answered with the data page.
          avoid=("luggage", "baggage", "flight", "airline", "hand luggage", "checked bag",
                 "hold bag", "suitcase",
                 "tax", "taxes", "taxed", "income", "income tax", "personal allowance",
                 "tax free", "tax-free", "hmrc", "marriage",
                 # "how much is the savings allowance" is the savings one, and "how much" plus
                 # "allowance" was all this row needed to take it
                 "savings", "saving", "interest", "isa",
                 # the other allowances are money the state pays for a person, not megabytes:
                 # "how much is attendance allowance" was this card, and "how much is carers
                 # allowance" was too, because "how much" beside "allowance" is the whole key.
                 # A benefit asked about by name is never a data question, so the names are
                 # fenced out here rather than narrowing the key, which every data line needs.
                 "attendance allowance", "attendance allowence", "carers allowance",
                 "carer allowance", "carer's allowance", "carers credit", "pension credit",
                 "child benefit", "housing benefit", "universal credit", "pip", "dla",
                 "disability benefit", "disability living", "benefit", "benefits",
                 "state pension", "tax credit", "tax credits", "income support",
                 "jobseekers", "maternity allowance", "bereavement"),
          bias=1),
    entry("saved-passwords", (("saved passwords", "save passwords", "remembered passwords",
                               "password list"),
                              ("find", "see", "where", "show", "look", "forgot", "lost")),
          "Your browser or phone has them: on an iPhone it is Settings > Passwords, on a Mac Safari "
          "> Settings > Passwords, in Chrome the key icon in the address bar or chrome://password-"
          "manager, and it asks for your fingerprint or face first. Turn on the password manager "
          "built into the phone rather than letting the browser do it, and the list follows you to "
          "the next phone.",
          bias=1),
    entry("phone-no-service", (("no service", "no signal", "sos only", "no network", "no bars",
                                "cant get signal", "can't get signal"),
                               ("phone", "iphone", "android", "mobile", "handset", "data", "call",
                                "calls", "signal")),
          "Check the phone's own settings before blaming the network: airplane mode off, mobile data "
          "on, and Settings > Mobile > Network selection set to Automatic. Restart the phone, then "
          "take the SIM out and put it back. If a phone beside it has signal and yours does not, the "
          "SIM or the phone is the fault; if neither has any, the network is down.",
          bias=2,
          # A television, a monitor and a radio say "no signal" too, and the phone settings below
          # are no help with any of them.
          avoid=("battery", "charging", "charger", "hot", "water", "cracked", "screen",
                 "tv", "telly", "television", "monitor", "projector", "radio", "aerial",
                 "freeview", "sky box", "sky q", "satellite dish", "hdmi")),
    # A screen that goes black at the ear is the proximity sensor doing its job, not a fault,
    # and no row answered it: the telly took "my screen goes black when i make a call", the
    # finger-ring card took "when i ring someone my screen goes black" (a ring is a phone
    # here, not jewellery) and the rest were met with a listening prompt. The call word has
    # to be said and so does the screen, because a phone that goes black on its own is the
    # screen, power or damage row's question.
    # A screen that goes black at the ear is the proximity sensor doing its job, not a fault,
    # and no row answered it: the telly took "my screen goes black when i make a call", the
    # finger-ring card took "when i ring someone my screen goes black" (a ring is a phone
    # here, not jewellery) and the rest were met with a listening prompt. Both parts have to
    # be met: a call word, because the sensor only does this during a call, and the screen
    # going out. A phone that goes black on its own is the screen, power or damage row's.
    entry("phone-screen-on-a-call",
          (("call", "calls", "ring", "rings", "ringing", "rang", "dial", "dialled",
            "phone call", "phone calls", "on the phone", "on a call", "make a call",
            "make calls", "take a call", "takes a call", "answer a call",
            "answering a call", "answer the phone", "answering the phone",
            "to my ear", "at my ear", "against my ear", "on speaker", "on loudspeaker",
            "on speakerphone", "on speaker phone", "hands free", "handsfree",
            "while talking", "while im talking", "while i am talking", "during the call",
            "during a call"),
           ("screen goes black", "screen goes blank", "screen goes dark", "screen goes off",
            "screen turns off", "screen switches off", "screen blacks out",
            "screen is black", "screen stays black", "goes black", "go black",
            "going black", "went black", "gone black", "turns black", "goes blank",
            "went blank", "goes dark", "went dark", "goes off", "turns off",
            "switches off", "blacks out", "keeps going black", "keeps going off",
            "keeps turning off")),
          "A black screen at your ear is the phone's proximity sensor working: it turns the "
          "display off during a call so your cheek cannot tap anything, and it should come back "
          "as soon as you take the phone away. If it stays black after that, or goes black on "
          "speaker, the usual cause is a screen protector, a case or a smudge over the top edge "
          "of the phone beside the earpiece - lift the protector off and wipe that strip, then "
          "restart the phone. Still blacking out after that points at the sensor itself, which "
          "is a cheap repair rather than a new phone.",
          # another screen is another answer: the telly row sets its own picture right, and a
          # cracked or dead phone is not a phone doing something normal
          avoid=("tv", "telly", "television", "monitor", "laptop", "computer", "pc",
                 "tablet", "ipad", "remote", "hdmi", "freeview", "projector", "cinema",
                 "windscreen", "cracked", "crack", "smashed", "dropped it", "wont turn on",
                 "won't turn on", "dead", "water", "wet", "bathtub", "toilet",
                 # a display that is dead while the call still works is a broken screen, and
                 # the sensor answer would sound certain about the wrong part of the phone
                 "but the call works", "but calls work", "call still works", "calls still work",
                 "can still hear", "still hear them", "screen is dead", "screen went dead",
                 "no display", "nothing on the screen", "screen doesnt come on",
                 "screen doesn't come on", "screen has failed", "screen has gone",
                 # a ring on a finger is the first-aid card's, not a phone's: the ring words
                 # in the key above are the verb ("when i ring someone"), and a line about
                 # the jewellery says my ring, the wedding ring, or names the finger
                 "my ring", "the ring", "wedding ring", "engagement ring", "ring finger",
                 "finger", "fingers", "thumb", "knuckle", "swollen", "numb", "cut off",
                 "jeweller", "jewellery", "jewelry", "soap", "butter", "oil",
                 "doorbell", "bell",
                 # a call that comes in is not a call at the ear: a screen that goes black
                 # when the phone rings is the phone's own fault, not the sensor doing its job
                 "when the phone rings", "when the phone rang", "rings me", "rang me",
                 "someone rings", "someone rang", "incoming call", "incoming calls",
                 "gets a call", "get a call", "got a call", "when i get a call",
                 "call comes in", "call came in", "missed call", "missed calls",
                 # a call that drops or breaks up is the signal answer, whatever the screen does
                 "drops calls", "dropping calls", "drops the call", "keeps dropping",
                 "breaking up", "breaks up", "cant hear", "can't hear", "cutting out",
                 "cuts out", "bad signal", "no signal", "no service"),
          bias=2),
    entry("phone-calls-cutting-out", (("cutting out", "cuts out", "cut out", "drops calls",
                                       "dropping calls", "calls keep dropping",
                                       "call keeps dropping", "breaking up", "breaks up",
                                       "cant hear", "can't hear"),
                                      ("call", "calls", "phone", "signal", "reception"),
                                      ("phone", "iphone", "android", "mobile", "handset")),
          "Check the signal first: on a phone the call bars are not the data bars, so look at how "
          "many show while you are on a call, and if it is one or none, the fix is wifi calling "
          "(Settings > Phone > Wifi Calling on an iPhone, Phone app > Settings > Wifi calling on "
          "Android) so calls go over your broadband. Then restart the phone, take the case off if "
          "it covers the microphone, and clean the microphone hole with a dry brush - a muffled "
          "'can you hear me' at one end is usually fluff, not the network.",
          bias=1,
          ask=("call", "calls", "phone", "iphone", "android", "mobile", "handset"),
          # A video call is the laptop's question, and a car that cuts out is the garage's. A
          # quiet ring or a quiet speaker is the loudness answer, not a dropped call.
          avoid=("car", "van", "motorway", "engine", "stalled", "electricity", "power cut",
                 "louder", "volume", "loud", "quiet", "ring", "ringing", "rings", "speaker",
                 "muffled", "turn it up",
                 "wifi", "wi fi", "internet", "tv", "telly", "zoom", "facetime", "skype",
                 "teams", "webex", "video call", "video calls", "videocall", "meet call",
                 "laptop", "webcam", "toilet", "sink", "water", "wet", "dropped it",
                 "down the toilet",
                 # a call that freezes or lags is the video call's answer, and a follow-up in
                 # that conversation must not come back as this one
                 "freezing", "freezes", "frozen", "lag", "laggy", "stutter", "glitchy")),
    # A phone that rings or buzzes and whose screen never comes on: the phone is on, so "charge it
    # for half an hour" is not the answer, and the dead-battery row stands down for "the screen" and
    # "my screen" so that the telly keeps those lines. That left these two with nothing at all:
    # "my phone is on but the screen is black" and "my screen is black but the phone is on" were a
    # listening line. The phone named in the line is the difference, and here it is both keys.
    entry("phone-on-but-screen-black",
          # the phone named on its own is not enough: "my phone screen is black" is a phone that
          # may well be flat, and the charger is the answer to that. This row is for a line that
          # says the phone is on - it rings, it buzzes, it turns on.
          (("phone is on", "phone is still on", "phones on", "phone turns on", "phone comes on",
            "phone switches on", "phone rings", "phone vibrates", "phone buzzes",
            "phone responds", "on my phone"),
           ("screen is black", "black screen", "screen black", "screen stays black",
            "screen wont come on", "screen is not on", "screen is off", "nothing on the screen",
            "no picture", "screen stays off")),
          "If it rings or buzzes but the screen stays black, the phone is alive and the fault is the "
           "display or its backlight, so force a restart rather than charging it: on an iPhone press "
           "volume up, volume down, then hold the side button until the Apple logo shows; on Android "
           "hold power and volume down for ten to fifteen seconds. If it comes back, back it up "
           "straight away, because a display that has gone once usually goes again. If it stays "
           "black and it still rings, it is the screen or its connector - a repair shop job, and ask "
           "them to test it before you agree a price.",
          bias=1,
          avoid=("tv", "telly", "television", "monitor", "laptop", "computer", "pc", "watch",
                 "tablet", "ipad", "kindle", "projector",
                 "mould", "mold", "mildew", "water", "wet", "toilet", "wifi", "internet",
                 "signal", "no sound", "in a call", "on a call", "during a call", "mid call",
                 "my ear", "the ear", "keeps going black", "going black", "goes black",
                 "going blank", "now and then", "sometimes")),

    # A phone that is plainly alive, whose screen goes black now and then. This was first keyed on
    # phone-wont-turn-on, whose answer is "charge it for half an hour" - advice for a dead phone,
    # and not what a phone that is on and blinking needs. The useful things are a backup before the
    # display gets worse, and the two causes worth ruling out at home.
    entry("phone-black-now-and-then",
          (("screen", "display", "phone", "iphone", "android", "mobile", "handset"),
           ("keeps going black", "going black", "goes black", "go black", "going blank",
            "goes blank", "flashes black", "flashing black", "flickers black", "blinks",
            "blinking", "goes dark", "going dark", "now and then", "on and off", "every so often",
            "sometimes goes black", "black for a second", "black twice", "keeps blanking",
            # a screen that flickers is the same intermittent display fault said another way,
            # and it was a shrug
            "flickers", "flickering", "flicker", "flashing now and then")),
          "Back it up now, before it gets worse - a screen that blinks black is usually the "
           "display connector working loose or a battery that cannot hold its voltage, and both "
           "get worse rather than better. Then rule out the cheap causes: take the case off (a "
           "case pressing on the sleep button dims it), let it run flat and charge it to full once, "
           "and check for a software update. If it only does it in one app, that app is the fault. "
           "If it does it in calls and near your ear, it is the proximity sensor, which is normal. "
           "A phone that still blinks after a restart wants a repair shop.",
          bias=1,
          avoid=("tv", "telly", "television", "monitor", "laptop", "computer", "pc", "watch",
                 "tablet", "ipad", "kindle", "projector",
                 "the screen", "my screen",
                 "mould", "mold", "mildew", "cracked", "crack", "smashed", "water", "wet",
                 "toilet", "dropped", "wifi", "internet", "signal", "no sound",
                 "in a call", "on a call", "during a call", "mid call", "make a call",
                 "answer a call", "my ear", "the ear")),

    # (the car, the headphones and the watch all "disconnect" too, and each has its own answer:
    # the avoid list lives on the entry above, so they are left to bluetooth-car and friends)

    # A phone screen that goes black *while the call is going on* was answered with the charger,
    # because the phone row keys "black" and "phone" and nothing there asked whether the phone
    # was in use. It is the one screen-blank shape with a different cure - a proximity sensor
    # doing its job, or a case over the sensor - so it gets its own row rather than dragging the
    # charger answer in.
    entry("phone-black-in-a-call",
          # The first group is the black screen itself, not the device: with the device there and
          # "on the phone" in the second, "my kid is on the phone all evening" - a screen-time
          # question - got the sensor. The screen has to have gone black for this row at all.
          (("going black", "goes black", "go black", "gone black", "went black",
            "gets black", "turn black", "turns black", "black screen", "screen is black",
            "screen goes black", "screen keeps going black", "screen went black",
            "screen turns black"),
           ("in a call", "on a call", "during a call", "make a call", "making a call",
            "made a call", "answer a call", "answering a call", "answer the call",
            "when i answer", "when i talk", "when i am talking", "talking on the phone",
            "call someone", "calling someone", "voice call",
            # the same thing said with the call as the background: "mid call", "while i am on a
            # call", "in the middle of a call"
            "mid call", "midcall", "while i am on a call", "while im on a call",
            "in the middle of a call", "halfway through a call",
            # and the same fault described by the ear: "the screen goes black when i put it to my
            # ear", "when i take it away from my ear" - that is the sensor either way round
            "my ear", "the ear", "against my ear", "to my ear", "near my ear", "on my ear",
            "away from my ear", "off my ear")),
          "That is usually the proximity sensor working: the screen goes black when the phone is "
           "held to your ear so your cheek does not press buttons, and it lights again when you "
           "pull it away. If it stays black, take the case or the screen protector off the top "
           "edge, where the sensor sits, and give the earpiece slot a wipe with a dry cloth. "
           "Restart the phone before you buy anything, and on an iPhone turn off Settings > "
           "Accessibility > Touch > Call Audio Routing > Speaker if it is set. A screen that "
           "also goes black on its own, not in calls, is the display or the battery - a repair "
           "shop job.",
          avoid=("tv", "telly", "television", "monitor", "laptop", "computer", "pc",
                 "mould", "mold", "mildew", "cracked", "cracked screen", "smashed",
                 "water", "wet", "toilet", "wifi", "internet", "signal", "cutting out",
                 "dropping calls", "mic", "microphone", "hear me", "volume", "loud")),

    entry("phone-wifi-drops", (("wifi", "wi fi", "wireless"),
                               ("phone", "iphone", "android", "mobile", "handset", "tablet",
                                "ipad"),
                               ("dropping", "drops", "disconnects", "keeps losing", "loses",
                                "weak", "keeps cutting", "other things work",
                                "works on my laptop")),
          _wifi_drops,
          bias=1,
          # The phone word is the gate: without it "my wifi keeps dropping in the bedroom" is the
          # router's question, and this answer would send them to the wrong settings.
          ask=("phone", "iphone", "android", "mobile", "handset", "tablet", "ipad"),
          avoid=("tv", "telly", "television", "printer", "doorbell", "camera", "thermostat",
                 "hotspot", "mobile data", "wifi doorbell", "baby monitor", "calls", "call",
                 "dropping calls", "dropped calls", "water", "sink", "toilet", "wet",
                 # the car, the headphones and the watch "disconnect" too, and each has its own
                 # answer, so this one stands down for them
                 "car", "carplay", "android auto", "bluetooth", "stereo", "head unit", "van",
                 "headphones", "earbuds", "airpods", "speaker", "watch", "router", "printer",
                 # "loses" and "drops" are in this key, so "my phone loses charge overnight" was a
                 # wifi answer: a line about the battery losing charge is never about the wifi
                 "battery", "batteries", "charge", "charging", "charger", "flat")),

    entry("spam-texts", (("spam", "scam", "junk", "unwanted", "dodgy"),
                         ("texts", "text", "sms", "messages", "message", "mobile number")),
          "Forward the text to 7726 - that is the free number UK networks use for spam - then block "
          "the sender and delete it. Never reply, not even with STOP, because a reply tells them the "
          "number is live; and never use a link in one, however much it looks like your bank.",
          bias=1,
          avoid=("post", "postal", "letter", "mailbox", "parcel", "email", "call", "calls",
                 "ring", "voicemail")),
    entry("laptop-keyboard-dead", (("keyboard", "keys", "key"),
                                   ("laptop", "computer", "macbook", "stopped working", "not working",
                                    "wont type", "won't type", "dead", "stuck", "not responding",
                                    "broken")),
          "Plug in a USB keyboard: if that types, the laptop's own keyboard is the fault, and a "
          "restart plus the maker's keyboard driver from their support page fixes it more often than "
          "not. If the keys that fail are a block of them, look for a sticky key or a spill; on a "
          "Mac, check System Settings > Keyboard.",
          bias=1,
          # a door key is not a keyboard: "how do i get a broken key out of a lock" keys "key"
          # and "broken" here, and the answer is a USB keyboard
          avoid=("clean", "cleaning", "cleaner", "dust", "dusty", "crumbs", "lint", "sticky",
                 "lock", "locks", "door", "barrel", "keyhole", "snapped", "broke off", "keyway")),
    entry("clean-keyboard", (("clean", "cleaning", "dust", "crumbs", "dirty", "sticky"),
                             ("keyboard", "keys", "keycaps")),
          "Shut it down and unplug it, tip it over and shake it gently, then use a soft brush or "
          "short bursts of compressed air held at an angle, not straight down. Wipe the keycaps "
          "with a cloth just damp with isopropyl alcohol - never spray anything onto it. A key "
          "that sticks needs a drop of alcohol round its edge and a few presses, not a soaking."),
    entry("transfer-photos", (("photos", "pictures", "images", "videos"),
                              ("transfer", "move", "copy", "get them off", "send to",
                               "off my phone", "off my old phone", "off the old phone",
                               "off an old phone", "from an old phone", "old phone",
                               "get the photos", "get photos", "to my laptop", "to my computer")),
          "Install Google Photos or iCloud Photos on both and let it upload, then they are on the "
          "laptop without a cable. For a one-off, plug the phone in and open it as a drive: on "
          "Windows it appears under This PC, on a Mac use Image Capture. Copy, check the count "
          "matches, and only then delete from the phone.",
          bias=1),
    entry("popups-phone", (("pop up", "pop ups", "popup", "popups", "ads", "adverts", "notifications",
                            "browser"),
                           ("stop", "stop them", "get rid", "keep appearing", "keeps appearing",
                            "everywhere", "phone", "chrome", "safari")),
          "Almost always it is a website allowed to send notifications, or Chrome's own pop-ups: in "
          "the browser settings turn off Pop-ups and redirects, and in Site settings > Notifications "
          "remove the sites you do not recognise. Clearing browsing data once also stops the older "
          "kind. Nothing is being hacked, and you do not need any app that claims to clean it.",
          bias=1,
          avoid=("tv", "television", "telly",
                 "youtube", "instagram", "facebook", "tiktok",
                 "radio", "newspaper", "night", "waking", "wake me", "asleep", "sleep",
                 # a notification is a setting, not an advert in a page: the Do Not Disturb row
                 # below answers those, so this row keeps the pop-ups and the ads
                 "notification", "notifications", "notification settings")),
    entry("webcam-not-working", (("webcam", "camera"),
                                  ("not working", "wont work", "won't work", "not detected",
                                   "black", "blank", "no picture", "shows nothing",
                                   "not showing", "isnt working", "is not working", "frozen")),
          "Close every other app that might be holding the camera, then check the permission: on "
          "Windows, Settings > Privacy & security > Camera, and on a Mac, System Settings > "
          "Privacy & Security > Camera, and switch your app on. A laptop with a sliding shutter "
          "over the lens is the other common one. A plug-in webcam: try another USB port and "
          "another app before blaming the camera.",
          bias=1,
          avoid=("photo", "photos", "camera roll", "security camera", "doorbell", "dashcam",
                 "screenshot", "lens", "dslr")),
    entry("uninstall-apps", (("delete", "uninstall", "remove", "get rid of"),
                              ("apps", "app", "games")),
          _uninstall_app,
          bias=1,
          avoid=("email", "message", "messages", "photos", "picture", "browser history",
                 "history", "comment", "post", "account", "contact", "memory", "search")),
    entry("uninstall-programs", (("uninstall", "remove", "delete", "get rid of"),
                                 ("program", "programs", "software", "windows", "pc", "laptop",
                                  "mac", "macbook", "computer")),
          _uninstall_program,
          bias=1,
          avoid=("apps on my phone", "iphone", "android", "icon", "storage", "space", "full",
                 "free up", "memory", "slow", "running out", "virus", "malware", "ransomware",
                 # a mark on the screen is `screen-scratch`, not a program to take off: "how do i
                 # get rid of a scratch on my laptop screen" was told to open Installed apps
                 "scratch", "scratches", "scratched", "scuff", "scuffs", "smudge", "smudges",
                 "screen", "screens", "cracked screen", "marks on the screen",
                 "infected", "popup", "pop up",
                 # the window in a house is not Windows the system: the condensation, the
                 # draught, the cleaning and the blinds are home questions
                 "condensation", "condensating", "condensing", "steamed up", "steaming up",
                 "misted up", "misting up", "damp", "mould", "mold", "sill", "sills", "glazing",
                 "double glazing", "window frame", "window frames", "draught", "draughts", "draft",
                 "curtains", "blinds", "squeegee", "clean the windows", "cleaning the windows",
                 "clean my windows", "washing the windows",
                 # and nor is it a broken window: a leak, a radiator or a boiler is a house job
                 "leak", "leaks", "radiator", "radiators", "boiler", "gutter", "gutters", "roof")),
    # A scratch on a screen is a mark, not a program to remove: "how do i get rid of a scratch on my
    # laptop screen" was answered with Settings > Apps > Installed apps, choose Uninstall, because
    # `uninstall-programs` keys "get rid of" beside "laptop". The polish is the answer people are
    # looking for and it is the one that ruins the screen.
    entry("screen-scratch",
          (("scratch", "scratches", "scratched", "scuff", "scuffs", "scuffed", "hairline crack",
            "marks on the screen", "mark on the screen", "get rid of a scratch"),
           ("screen", "screens", "laptop", "phone", "mobile", "monitor", "display", "tablet",
            "ipad", "tv", "macbook")),
          "A scratch in the glass will not polish out, and toothpaste or a jeweller's rouge only "
          "turns one line into a hazy patch. Leave a shallow scratch, put a tempered-glass screen "
          "protector over it to hide it and stop it spreading, and for a phone price the glass "
          "replacement at a local repair shop first - it is usually £30 to £60 and a protector "
          "on the new screen is cheaper than a second repair. A bulge or a crack you can feel "
          "with a fingernail needs the screen replacing, not cleaning.",
          bias=1,
          avoid=("uninstall", "remove a program", "windows", "car", "windscreen", "wood", "table",
                 "furniture", "floor", "paint", "glasses", "lens", "camera lens", "cd", "dvd",
                 "itch", "itchy", "skin", "eye",
                 # a screen scratched out of the box is a return, not a repair: the arrival card
                 # answers "my tv arrived scratched" and keeps it
                 "arrived", "arrives", "came", "comes", "delivered", "delivery", "unpacked",
                 "unpacking", "brand new", "box", "parcel", "receipt", "refund", "return it",
                 "send it back", "sent it back", "warranty", "guarantee", "faulty", "days old")),
    entry("screen-brightness", (("brighter", "brightness", "too dim", "dimmer", "dim screen",
                                  "screen is dim", "screen looks dark", "cant see the screen",
                                  "can't see the screen", "too dark"),
                                 ("screen", "laptop", "phone", "display", "monitor", "ipad",
                                  "tablet", "macbook")),
          "Use the brightness keys first - the ones with a sun on them, usually F1 and F2 - and if "
          "that does nothing, Windows: Settings > System > Display, and turn off Change brightness "
          "automatically; iPhone: Settings > Accessibility > Display & Text Size and turn off Auto "
          "Brightness. On a laptop that dims when it comes off the charger, look in Settings > "
          "System > Power & battery for Battery saver.",
          avoid=("night", "evening", "dark mode", "mood", "tv", "projector")),
    # A bar on a phone is the same word as a bar on a bicycle and a bar on a boiler gauge: it is a
    # signal only when the line says so ("signal", "reception", "network", "coverage", a phone)
    # or names a weak one ("one bar", "no bars"). Without that, "flat bars or riser bars on a
    # hybrid" was told to turn on wifi calling, on "flat" reading as a flat and "bars" as signal.
    entry("mobile-signal-home", (("signal", "reception", "bars", "coverage"),
                                  ("home", "house", "indoors", "inside", "flat", "village",
                                   "at home", "poor", "bad", "weak", "rubbish", "terrible",
                                   "one bar", "keep dropping")),
          "Turn on wifi calling, which on most networks is Settings > Phone > Wi-Fi Calling: calls "
          "then come over your broadband and the signal stops mattering indoors. Keep a mobile call "
          "near a window, and ask your network for a signal box - they are free on most contracts "
          "if you can show the problem. A repeater you buy yourself only helps if there is at least "
          "one bar outdoors.",
          bias=1,
          guard=_a_signal_reading,
          avoid=("wifi", "wi fi", "router", "broadband", "mesh", "booster", "tv", "radio",
                 "bedroom", "living room", "upstairs", "downstairs")),
    entry("free-up-cloud-storage", (("icloud", "cloud storage", "google one", "cloud"),
                                     ("full", "stop paying", "paying", "keep paying", "delete",
                                      "free up", "empty", "clear", "storage", "upgrade",
                                      "cheaper", "running out")),
          "Settings > [your name] > iCloud > Manage Account Storage shows the list: photos and old "
          "device backups are almost always the top two, so delete the backups of phones you no "
          "longer own, then empty Recently Deleted. The 50GB plan is about 79p a month, and if you "
          "would rather not pay, keep photos only on the phone and turn on Optimise iPhone Storage.",
          bias=1,
          avoid=("laptop", "windows", "android", "freezer", "cupboard")),
    entry("backup-laptop", (("back up", "backup", "backups", "backing up"),
                             ("laptop", "computer", "pc", "mac", "macbook", "windows", "files",
                              "documents", "everything", "whole")),
          "Windows: plug in an external drive and turn on File History (Settings > System > Storage "
          "> Advanced storage settings > Backup options), or let OneDrive copy your Desktop, "
          "Documents and Pictures. A Mac: Time Machine with an external drive, set once. Keep the "
          "drive in a different room, and once a year try restoring one file, because a backup you "
          "have never opened is a guess.",
          bias=1,
          avoid=("photos", "pictures", "phone", "whatsapp", "icloud", "google photos")),
    # "how do i format my laptop" and "how do i format my phone" were the search hedge: the word
    # people use for a machine wiped clean is format, and the row that answers it was keyed on
    # reset and wipe only. A stick or a card is not this row - the format-a-drive row below takes
    # those by naming the stick, the card or the disk.
    entry("factory-reset", (("factory reset", "reset", "wipe", "start fresh", "back to factory",
                             "format", "formats", "formatting", "reformat"),
                            ("laptop", "computer", "phone", "iphone", "android", "mac", "macbook",
                             "windows", "tablet", "ipad", "desktop", "pc")),
          "Back up first, because a factory reset erases everything: photos, messages, and any "
          "account you have not signed out of. On Windows it is Settings > System > Recovery > Reset "
          "this PC; on an iPhone, sign out of your Apple ID first or the phone will lock; on Android, "
          "Settings > System > Reset. Then sign back in and restore from the backup.",
          bias=1,
          # a document is laid out, not wiped, so the layout answers keep those lines
          avoid=("password", "pin", "code", "router", "wifi", "hub", "boiler", "thermostat",
                 "document", "documents", "spreadsheet", "letter", "cv", "essay", "report")),
    # "memory" and "run out" are in the key because "my phone memory is full" and "i've run
    # out of space on my ipad" were shrugs: the key held the phrase "memory full", which the
    # word "memory is full" never matches. The laptop, the desktop and the car keep their own
    # answers through the avoid list below.
    entry("phone-storage-full", (("storage", "space", "memory", "out of space", "running out",
                                  "run out", "full", "always full", "no space",
                                  "running out of space", "run out of space",
                                  "running out of storage", "run out of storage",
                                  # "how do i clear room on my phone" said "room" and nothing the
                                  # key held, so the university card took it; the phrase keeps the
                                  # room noun tied to the device in the ask
                                  "room on my", "clear room", "clear some room", "room for",
                                  # "i need space on my phone" and "my mum needs more space on her
                                  # phone" are both the drive being full, and the phrase people use
                                  # for it is "need more space", not "free up": the relationship rows
                                  # were taking them on "i need space" alone
                                  "need more space", "needs more space", "need space",
                                  "needs space", "more space on", "space on my", "space on her",
                                  "space on his", "space on the",
                                  # and the same ask with the thing named after it: "i need some
                                  # space for photos on my iphone"
                                  "space for", "some space"),
                                 ("phone", "iphone", "android", "ipad", "tablet", "handset",
                                  "storage", "delete", "free up", "make room", "clean up",
                                  "clear", "out of room", "no room", "photos", "videos")),
          "Settings > General > iPhone Storage (or Storage on Android) lists what is taking the "
          "space, biggest first: it is nearly always photos and videos. Delete the videos you never "
          "watch, turn on Optimise Storage so old photos live in the cloud, and offload the apps you "
          "rarely open. Most phones can free several gigabytes that way in ten minutes.",
          bias=1,
          # "my phone is always running out of battery" runs out of charge, not of space
          # "i need to make room on my mac" is the Mac storage answer, and "mac" was not in
          # the list while "make room" was in the key
          avoid=("laptop", "computer", "macbook", "mac", "imac", "macbook pro", "macbook air",
                 "desktop", "pc", "sd card", "shed", "garage",
                 # room in an inbox is the mailbox answer's: "how do i free up space in my inbox"
                 # was getting the phone storage card
                 "inbox", "email", "emails", "mailbox", "mail box", "gmail", "outlook",
                 "loft", "attic", "kitchen", "car", "van",
                 # a phone running out of battery is not a phone running out of room
                 "battery", "charge", "charging", "charger", "power", "loses charge", "dies",
                 "dying",
                 # and a hotel room is not the room left on a phone: "the hotel has no room for
                 # us" carried "no room" for the device and "room for" for the thing it is short
                 # of, and was told which videos to delete. A booking is not a disk.
                 "hotel", "hotels", "motel", "hostel", "guest house", "guesthouse", "b&b",
                 "bed and breakfast", "booking", "overbooked", "over booked", "double booked",
                 "double-booked", "no room for us", "no room at", "walked to another hotel",
                 "gave our room away", "gave my room away")),
    entry("bigger-text", (("text", "writing", "font", "letters", "zoom", "everything", "screen"),
                          ("bigger", "larger", "too small", "size", "make it bigger",
                           "make it larger", "increase")),
          "On an iPhone it is Settings > Display & Brightness > Text Size, or Accessibility > "
          "Display & Text Size for Larger Text and Bold Text. On Android, Settings > Display > Font "
          "size, plus Display size for everything else. Most apps then follow the phone, and in a "
          "browser Ctrl and + (Cmd and + on a Mac) enlarges a page.",
          bias=1),
    entry("screen-recording", (("record", "recording", "capture"), ("screen", "my screen", "phone", "laptop")),
          "On an iPhone add Screen Recording to Control Centre (Settings > Control Centre) and tap "
          "it. On Android it is in the quick settings tiles on most phones. On a laptop, Windows has "
          "Game Bar (Windows and G) and a Mac has Shift, Cmd and 5. Everything saved goes to Photos "
          "or the desktop.",
          bias=1),
    entry("phone-value", (("old phone", "my phone", "handset", "iphone", "android",
                           "laptop", "macbook", "ipad", "tablet"),
                          ("sell", "selling", "trade in", "trade-in", "trade it in", "resale",
                           "resell", "how much is", "how much are", "worth anything")),
          "Check two things before you sell: the trade-in price from the network or the maker, and "
          "what the same model with the same storage sells for on a resale site - the private sale "
          "is often 20 to 30% more. Say the battery health and any marks honestly, sign out of your "
          "accounts and factory reset it in front of the buyer.",
          bias=1,
          avoid=("repair", "fix", "cracked", "crack", "screen", "battery", "charging", "water",
                 "virus", "slow", "how much to")),
    entry("extended-warranty", (("extended warranty", "warranty", "warranties", "insurance",
                                 "protection plan", "apple care", "applecare", "care plan",
                                 "care plus", "accidental damage"),
                                ("worth", "worth it", "should i", "buy", "need", "get")),
          "Usually no. A new appliance is already covered for a year or two by the maker, and your "
          "home contents insurance or the card you paid with often extends that for free. On a "
          "phone or a laptop the paid plan is really accidental-damage cover, and a cracked screen "
          "is £60 to £120 at a repair shop, so the plan only pays if you drop it more than once. "
          "Put the price aside instead: for most things it is cheaper to pay a repair than years "
          "of cover you never claim on.",
          bias=1,
          # "should i cover it" in a kitchen is a roasting tin, not a warranty
          # A bike is insured against theft, not against a fault: "do i need insurance for an
          # ebike" is the licence-and-rule question, and this entry was answering it with a
          # washing machine warranty.
          avoid=("car", "boiler", "house", "home insurance", "travel", "chicken", "turkey",
                 # "do i need insurance to drive" is the car cover the law makes you buy, not
                 # a plan on a gadget: the line names no car, so "drive" has to keep it out
                 "drive", "driving", "on the road", "motorbike", "moped", "van insurance",
                 "motor insurance", "insurance to drive",
                 # a bike is insured for theft, not on a washing-machine policy: the warranty
                 # row was answering "do i need insurance for an ebike" with a kitchen appliance
                 "bike", "bikes", "bicycle", "bicycles", "ebike", "ebikes", "e-bike", "e-bikes",
                 # a gap policy is the finance half of a written-off car, and it has its own row:
                 # "is gap insurance worth it" was answered here with a washing machine warranty
                 "gap insurance", "gap cover", "gap protection",
                 "electric bike", "cycling", "cyclist", "motorcycle", "scooter",
                 "van", "lorry", "holiday", "flight", "flights",
                 "roast", "cake", "dish", "pan", "pot", "food", "cook", "cooking", "meat",
                 "sauce", "gravy", "rice", "pasta", "oven", "tin", "foil",
                 # an animal's cover is the vet's question: "is pet insurance worth it" is not
                 # a warranty question, and this entry was taking it
                 "pet", "pets", "dog", "dogs", "cat", "cats", "puppy", "kitten", "vet",
                 "vets", "vet bill",
                 # a national insurance number is a money and work line, and "insurance" plus
                 # "get" was enough to sell it an extended warranty
                 "national insurance", "insurance number", "national insurance number",
                 "ni number", "tax", "pension", "p45", "p60", "paye", "self employed")),
    entry("video-call-setup", (("video call", "facetime", "zoom", "whatsapp video", "ms teams",
                                "microsoft teams", "teams call", "teams meeting", "teams app",
                                "teams video", "teams with"),
                               ("how do i", "set up", "start", "make", "call my", "first time")),
          "The easiest is WhatsApp: open the chat with the person, tap the camera icon at the top, "
          "and they get a ringing call. For an iPhone-to-iPhone call it is FaceTime in the same "
          "place. If they use Zoom, they send you a link - tap it at the time of the call, allow the "
          "camera and microphone, and you are in.",
          bias=1,
          # "teams meeting" matches "team meeting" as a word family, so "how do i speak up in a
          # team meeting" was told how to start a video call. The speaking words are the fence,
          # never "meeting" itself: setting one up is what this row is for.
          avoid=("speak up", "speak in", "speaking in", "talk more in", "point across",
                 "contribute in", "get a word in", "talked over", "spoken over", "say something")),
    entry("share-photos", (("share", "send", "album", "family"),
                           ("photos", "pictures", "album", "photo album")),
          "Use a shared album rather than sending them one by one: on an iPhone, Photos > Albums > "
          "+ > New Shared Album and invite them; on Android, Google Photos > Sharing > Shared album. "
          "Everyone can add to it and it does not fill up anybody's messages.",
          bias=2),
    entry("phone-passcode", (("passcode", "passcode on", "pin", "pin number", "face id",
                              "fingerprint", "unlock", "lock screen", "password", "screen lock",
                              "lock my phone"),
                             ("phone", "iphone", "android", "set up", "use", "secure", "safer",
                              "should i")),
          "Use a six-digit passcode with Face ID or the fingerprint, not a four-digit PIN: a six-digit "
          "code is a million combinations and the thumb is faster than typing anyway. Turn on "
          "auto-lock at 30 seconds, and check in Settings that your photos and messages are backed up "
          "so a lost phone is an annoyance rather than a loss.",
          bias=1,
          avoid=("wifi", "router", "sim", "sim only", "any network", "network unlock",
                 "unlock code", "carrier lock", "bank card", "lock on the door", "front door",
                 "email", "account", "facebook", "instagram", "laptop", "computer", "windows",
                 "change my password", "forgot", "reset",
                 # The passcode locks the handset; a person who keeps forgetting the passwords
                 # for their accounts wants the manager, and "what should i do" made this row
                 # win that line on "should i" - the second key word - while the manager stood
                 # a place behind it.
                 "forget", "forgetting", "forgets", "keep forgetting", "remember my passwords",
                 "password manager", "too many passwords", "which password", "a password for every")),
    # "how do i unlock my sim" and "how do i unlock my phone to any network" ask for the network
    # lock, not the passcode: phone-passcode owns the word unlock and answered with a six-digit
    # code. The lock that comes off the handset when the contract ends is this answer.
    entry("phone-network-unlock",
          (("unlock", "unlocked", "unlocking", "network unlock", "unlock code", "any network",
            "sim only", "sim-free", "sim free", "carrier lock", "network locked", "sim lock",
            "locked to"),
           ("sim", "phone", "iphone", "mobile", "network", "carrier", "panning",
            "get it unlocked", "can i use",
            # "my phone is locked to ee" names the network and not the word
            "ee", "o2", "vodafone", "three", "giffgaff", "lebara", "talkmobile", "sky mobile",
            "tesco mobile", "asda mobile", "smarty", "id mobile", "plusnet")),
          "Ask your network for the unlock code and it is free once your minimum term is up - "
          "Ofcom requires them to do it, so nobody should be charging you. Find the request form "
          "or the chat in your account (some networks do it in the app) and it usually lands "
          "within a couple of days; then put another network's SIM in and follow the on-screen "
          "prompt. On an iPhone, Settings - General - About showing Carrier Lock: No SIM "
          "restrictions means it is done.",
          # a passcode, a forgotten login and a stolen phone are other answers
          avoid=("passcode", "pin", "face id", "locked out", "forgot", "i forgot", "password",
                 "stolen", "lost", "found", "cracked screen", "blacklist", "icloud",
                 "screen")),
    # An iPad is the same question with different buttons, and adding "ipad" to phone-passcode's
    # key was worse than a second entry: it lowered the rarity of the shared words, which let
    # kid-first-phone answer "how do i set up parental controls on my sons phone".
    entry("ipad-passcode", (("ipad", "ipad air", "ipad pro", "ipad mini"),
                            ("passcode", "pin", "password", "lock", "screen lock", "face id",
                             "touch id", "secure", "set up")),
          "Settings > Face ID & Passcode (Touch ID & Passcode on an older one), then Turn Passcode "
          "On: choose a six-digit code, and the same screen has auto-lock and Erase Data. The "
          "passcode you type after a restart is the one that protects the backup, so keep it "
          "somewhere other than the iPad.",
          avoid=("forgot", "forgotten", "locked out", "reset", "child", "kids", "parental",
                 "screen time", "slow", "storage", "wifi", "apple id"),
          bias=1),
    entry("phone-listening", (("listening", "listening to me", "spying on me", "eavesdropping",
                               "tracking", "hearing me", "watching me", "ads following",
                               "adverts following"),
                              ("phone", "alexa", "google", "siri", "ads", "adverts", "microphone")),
          "Your phone is not secretly recording you to make adverts, but it does track a lot: turn "
          "off ad personalisation in Settings > Privacy > Tracking (iPhone) or Ads (Android), and "
          "review which apps have the microphone. The ad that seems to follow a conversation usually "
          "comes from your location, your searches and the people you are near.",
          bias=1,
          # a hacked camera is its own question, and this entry's answer is about ad tracking
          avoid=("email", "account", "facebook", "instagram", "whatsapp", "bank", "wifi",
                 "router", "password", "hacked", "hack", "hacking", "hacker", "camera",
                 "webcam", "front camera", "recording me", "recording us")),
    # "how do i stop my phone tracking me" and "how do i stop apps tracking me" were the
    # screen-time limit and a hedge, both of them wrong: nothing here said where the location
    # permission lives. `phone-listening` stays the "is it listening to me" answer and this is
    # the settings answer beside it, so the two never need the same line.
    entry("phone-tracking",
          (("tracking", "tracked", "tracking me", "track me", "tracks me", "tracking my location",
            "location tracking", "targeted ads", "targeted advertising", "ad personalisation",
            "personalised ads", "advertising id", "ad id", "knows too much", "knows too much about me",
            "knows me too well", "what my phone knows", "what my phone knows about me",
            "which apps can see my location", "apps can see my location", "ad personalisation",
            "follows me", "ads follow me", "spying on me", "permissions"),
           ("phone", "iphone", "android", "apps", "app", "google", "safari", "location",
            "settings", "privacy", "ads", "ad", "adverts", "advert", "websites", "website",
            "browser", "cookies", "advertising")),
          "Turn off the two things that actually feed it. Location: Settings > Privacy & Security > "
          "Location Services on an iPhone, Settings > Location > App permissions on Android, and set "
          "each app to While Using only - the apps that do not need it, set to Never, and turn off "
          "Precise Location for shopping and social apps. Ads: on an iPhone, Settings > Privacy & "
          "Security > Tracking and turn off Allow Apps to Request to Track, which resets everything "
          "to one opt-out; on Android, Settings > Privacy > Ads > Delete advertising ID. In a browser, "
          "turn on Prevent Cross-Site Tracking in Safari or block third-party cookies in Chrome - "
          "that is how most of it follows you from site to site. The phone is not quietly listening - "
          "the ad that follows a conversation comes from your location, your searches and the "
          "people you are near.",
          bias=1,
          # a parcel's tracking number, an order, a period app and a step count are other questions
          avoid=("tracking number", "parcel", "delivery", "delivered", "courier", "order",
                 "post office", "evri", "hermes", "royal mail", "dpd", "yodel",
                 "period", "periods", "fertility", "ovulation", "pregnancy", "contraception",
                 "step", "steps", "step count", "pedometer", "fitness", "run", "running",
                 "gym", "calories", "sleep", "weight",
                 # every other permission is its own screen and its own question: a camera or
                 # microphone line sent to the location and ads switches is told to change two
                 # things that cannot help, and "my camera app has no permission" is the
                 # camera card's line, which does not reach the word "permission"
                 "camera", "cameras", "webcam", "microphone", "microphones", "photo library",
                 "photos library", "photo album", "notifications", "notification", "contacts",
                 "files", "file access", "storage", "bluetooth", "calendar", "health data")),
    # A phone whose camera is "hacked" is a permissions question with a checkable answer, so it
    # does not share the ad-tracking entry: the indicator dot is the part that settles it.
    entry("phone-camera-hacked", (("hacked", "hack", "hacking", "hacker", "spy", "spying",
                                   "someone watching", "watching me", "recording me",
                                   "recording us", "listening to me"),
                                  ("camera", "webcam", "front camera", "microphone", "mic",
                                   "phone", "iphone", "android")),
          "Look for the dot at the top of the screen: green means the camera is on, orange means the "
          "microphone, and it only appears while an app is using it. If it shows when you are not in "
          "any app, open Settings > Privacy > Camera (Permissions on Android, Privacy & security "
          "on a laptop) and turn off every app you do not trust, then restart the phone; a camera "
          "nobody can account for is worth a backup and a factory reset rather than a new phone.",
          bias=1,
          avoid=("email", "account", "facebook", "instagram", "whatsapp", "bank", "wifi", "router",
                 "password", "website", "laptop broken", "laptop fan", "laptop slow")),
    entry("clean-charging-port", (("clean", "cleaning", "clear", "dust", "fluff", "lint", "gunk",
                                   "only works if i hold", "only works when i hold", "hold the cable",
                                   "loose", "wiggle", "wont stay in", "falls out"),
                                  ("charging port", "charger port", "usb port", "port",
                                   "lightning port", "usb-c", "charger")),
          "Look in the port with a torch: a plug of pocket fluff is why most phones stop charging. "
          "Switch the phone off, then dig it out with a wooden toothpick or a dry soft toothbrush, "
          "never a pin or a metal clip, and do not use water, alcohol or a can of air. If the plug "
          "still feels loose or the port looks burnt, a repair shop swaps it for £30 to £60.",
          bias=2),
    entry("charge-limit-80", (("stop charging", "charging past", "charge to", "limit charging",
                               "80", "85", "overcharging", "overcharge", "battery care"),
                              ("phone", "iphone", "android", "samsung", "laptop", "battery")),
          "Turn on the setting rather than watching the number: an iPhone has Settings > Battery > "
          "Charging Optimisation, and most Android phones have Protect Battery or a charge limit in "
          "Settings > Battery. Between 20% and 80% is the range a lithium battery lasts longest in, "
          "and the makers' own optimised charging gets you most of that without any effort.",
          ask=("stop", "past", "limit", "80", "85", "overcharg", "care", "how do i", "can i"),
          avoid=("car", "bike", "scooter", "vape", "toothbrush", "drill")),
    entry("airplane-mode", (("airplane mode", "flight mode", "aeroplane mode"),
                            ("what", "does", "do", "mean", "why", "how", "use")),
          "It switches off every radio at once - mobile data, wifi and Bluetooth - so the phone "
          "cannot transmit, which is why planes ask for it. It is also the fastest fix for a phone "
          "that has lost signal: turn it on for ten seconds and off again, and it re-registers with "
          "the network. You can switch wifi back on while it is on, so a flight's wifi still works.",
          bias=1),
    entry("laptop-stuck-on-logo", (("stuck", "frozen", "hangs", "hanging", "wont get past",
                                    "spinning", "loop", "boot"),
                                   ("windows logo", "apple logo", "boot", "start up", "startup",
                                    "loading", "bios", "dell", "hp", "lenovo")),
          "Force it off by holding the power button for ten seconds, unplug everything except the "
          "charger and start it again: a printer or a memory card is often what it is stuck on. If "
          "it still stops at the logo, start it in safe mode (hold Shift while it boots on Windows, "
          "or hold Shift on a Mac) and remove whatever you installed last; a machine that will not "
          "start at all needs a repair shop or the maker's recovery drive.",
          bias=1,
          avoid=("phone", "iphone", "android", "game", "tv", "playstation", "xbox")),
    entry("recover-deleted-photos", (("recover", "get back", "restore", "recover deleted",
                                      "get them back", "bring them back", "mistake"),
                                     ("deleted photos", "deleted pictures", "deleted videos",
                                      "photos i deleted", "pictures i deleted", "lost photos",
                                      "deleted them", "photos by mistake", "deleted by mistake")),
          "Check the bin first, because it keeps them for 30 days: Photos > Albums > Recently "
          "Deleted on an iPhone, or Photos > Bin on Android, and Google Photos has one too. If they "
          "are gone from there, look in the cloud account's own trash on a browser, and stop taking "
          "new photos so the space is not reused, because a recovery tool can only get back what "
          "has not been overwritten.",
          bias=1),
    entry("smart-plug", (("smart plug", "smart socket", "smart switch", "plug timer"),
                         ("what", "which", "worth", "buy", "best", "do i need", "how do",
                          "does it work", "for")),
          "A smart plug goes between the socket and the thing, and you switch it from an app or by "
          "voice; it is the cheapest way to make a lamp, a fan or a Christmas tree smart. Check it "
          "is rated for what you plug in (13A for a heater, and never for anything that must not be "
          "cut off, like an iron or an electric blanket) and that it works with what you already "
          "have, Alexa or Google or Apple Home. Around £10 to £20 each.",
          bias=1),
    entry("phone-timer", (("timer", "set a timer", "countdown", "stopwatch"),
                          ("phone", "how do i", "alarm", "clock", "cook", "eggs", "siri")),
          "Open the Clock app and tap Timer: type 10 and press Start, and on an iPhone you can say "
          "'hey Siri, set a timer for ten minutes' instead. A timer keeps running with the screen "
          "off and rings over the alarm volume, so turn that up in Settings > Sounds if it is too "
          "quiet to hear from the kitchen.",
          # the other timer in the house: "how do i set the timer on my boiler" is the heating
          # programmer, and it was answered with the phone's Clock app.
          avoid=("boiler", "heating", "thermostat", "programmer", "radiator", "immersion",
                 "water heater", "sprinkler", "irrigation", "plug timer", "christmas lights"),
          ask=("how do i", "how to", "set", "phone", "alarm", "clock", "app", "siri")),
    entry("app-refund", (("refund", "money back", "get my money back", "cancel a purchase"),
                         ("app", "apps", "in app", "game", "subscription", "purchase", "itunes",
                          "play store", "app store", "google play", "googleplay")),
          "Ask in the store, not the app: on an iPhone use reportaproblem.apple.com within 90 days, "
          "and on Android open Play Store > Payments and subscriptions > Budget and order history > "
          "Report a problem, within 48 hours. Say plainly that it was a mistake or did not work, and "
          "do not spend the money again in the meantime; children's purchases are refunded most "
          "readily when you say it was a child.",
          bias=5,
          avoid=("parcel", "order not arrived", "train", "flight", "holiday", "shop", "supermarket")),
    entry("sleep-or-shutdown", (("sleep", "shut down", "shutting down", "switch off", "turn off",
                                 "hibernate", "overnight", "leave it on", "off at night",
                                 "turn it off", "turned off", "shut it down"),
                                ("laptop", "pc", "computer", "macbook", "machine")),
          "Sleep for short breaks, shut down when it will be off for more than a day: sleep keeps "
          "your open windows and wakes in seconds, and it sips power rather than charging the "
          "battery overnight, while a full shutdown clears the memory and installs the updates it "
          "has queued. Either way a restart once a week is what keeps a machine feeling new.",
          guard=_not_a_charging_ask,
          bias=1,
          # "how do i stop my laptop going to sleep" is the power setting, not the choice
          # between sleeping and shutting down
          # "how do i turn off the camera/wifi/notifications" is a setting on a part of the
          # machine, not a question about sleep and shutdown. A machine that shuts down on its
          # own is a fault, not a choice about sleep, and it does not live here. "how do i stop my
          # laptop going to sleep" is the power setting, not this choice between the two.
          avoid=("phone", "iphone", "tv", "router", "boiler", "heating", "fridge", "freezer",
                 "going to sleep", "goes to sleep", "keeps going to sleep", "keeps sleeping",
                 "stop it sleeping", "falls asleep", "stay awake", "wont stay on", "screen goes off",
                 "screen turns off", "turns off the screen", "locks itself",
                 "camera", "webcam", "microphone", "mic", "screen", "keyboard", "wifi", "wi fi",
                 "bluetooth", "notifications", "sound", "speaker", "brightness", "location",
                 "autoplay", "auto play", "keyboard backlight", "touchpad", "trackpad",
                 "itself", "by itself", "its own", "randomly", "keeps shutting", "keeps turning",
                 "keeps switching", "microwave", "kettle", "toaster", "dishwasher", "oven",
                 "washing machine", "washer", "dryer", "tumble dryer", "appliance", "hoover",
                 "vacuum", "iron")),
    entry("touchpad-dead", (("touchpad", "trackpad", "cursor", "mouse pad", "mousepad"),
                            ("stopped", "not working", "wont work", "won't work", "dead", "frozen",
                             "jumps", "not responding")),
          "Press the touchpad-off key first - it is a squashed rectangle key in the top row on most "
          "laptops, usually F6 to F9, and an accidental tap turns it off. On Windows check Settings "
          "> Bluetooth and devices > Touchpad is on, then plug in a mouse and try; if the mouse "
          "works and the pad does not, restart with the laptop plugged in, and if the pad is still "
          "dead it is the ribbon cable, which a shop reseats cheaply.",
          bias=1),
    # A mouse is a computer part and an animal: "my mouse isnt working" was sent to a pest
    # controller, so the keys are the device words and the pest words are avoided. A keyboard is
    # the same fault in the same cable, so it shares the answer.
    entry("mouse-not-working", (("mouse", "mouse pointer", "wireless mouse"),
                                ("not working", "isnt working", "stopped working", "wont work",
                                 "won't work", "broken", "dead", "not responding", "frozen",
                                 "jumps", "jumping", "jerky", "not clicking", "wont click",
                                 "not scrolling", "wont scroll", "not connecting",
                                 "wont connect", "disconnected", "stuck", "laggy", "battery",
                                 "not moving", "jumpy", "scroll", "scrolling", "stopped scrolling",
                                 "click", "clicks", "clicking")),
          "Do the cheap things in order. If it is wireless, fresh batteries or a full charge "
          "first, then check the little switch underneath is on and unplug the receiver and put "
          "it in a different USB port - a tired port takes the mouse down with it. If it is "
          "wired, try another port and another cable before blaming the mouse. When it still "
          "does nothing, turn it over: a hair or a bit of fluff over the sensor is the commonest "
          "fault of all, so wipe the lens and use it on a plain surface rather than glass or a "
          "shiny desk. A mouse that is dead on every port is the mouse, and any cheap one will "
          "do while you decide about a repair.",
          bias=1,
          avoid=("cat", "dog", "kitchen", "loft", "attic", "shed", "garden", "trap", "traps",
                 "pest", "droppings", "chewed", "nest", "trackpad", "touchpad", "poison")),
    # A machine that sleeps too soon is neither a question about sleep-vs-shutdown nor about how
    # long it lasts: "my laptop keeps going to sleep" and "how do i stop my laptop going to sleep"
    # were answered "A laptop is good for about four to six years" (the lifespan key held "keep
    # going") and then "Sleep for short breaks, shut down when it will be off for more than a day",
    # which is a choice the person was not asking about. The timer is a setting, and this row is
    # where it is changed.
    entry("laptop-sleep-timer",
          (("goes to sleep", "going to sleep", "going to sleep", "falls asleep",
            "falling asleep", "keeps going to sleep", "keeps falling asleep", "sleeps after",
            "sleep after", "sleeps within", "sleep timer", "sleep settings", "sleep setting",
            "sleep time", "change when it sleeps", "change when my laptop sleeps",
            "stop it going to sleep", "stop it sleeping", "stop it from sleeping",
            "stop my laptop going to sleep", "stop my laptop from sleeping",
            "stop my laptop sleeping", "wont stop sleeping", "won't stop sleeping",
            # a machine named other than a laptop says the same thing: the machine word in the
            # second group keeps these out of a baby or a pet line about sleep
            "from sleeping", "from going to sleep", "stop it sleeping",
            "goes into sleep", "sleep mode", "sleep too quickly", "sleeps too quickly",
            "sleeping too quickly", "sleeps too soon", "sleeps too fast"),
           ("laptop", "laptops", "computer", "pc", "macbook", "mac book", "notebook",
            "chromebook", "machine", "screen", "display", "monitor",
            # a tablet that shuts its screen is the same setting on a smaller machine: "my tablet
            # keeps going to sleep" held the lifespan words and got "four to six years". A phone is
            # left out on purpose - "how do i stop my phone from sleeping" is as often the
            # phone-keeping-me-up line, and that card is a better answer than this one.
            "tablet", "tablets", "ipad")),
          "Change the sleep timer, not the lid. On Windows, Settings > System > Power & battery > "
          "Screen and sleep: set 'Put my device to sleep after' to Never or 30 minutes, once on "
          "battery and once plugged in. On a Mac, System Settings > Lock Screen for the display and "
          "Battery > Options for 'Prevent automatic sleeping on power adapter'. On a tablet it is "
          "Settings > Display > Screen timeout, or Auto-Lock on an iPad. If it still sleeps while "
          "you are typing, the screensaver or the maker's own power app is doing it.",
          bias=2,
          # A machine that wakes itself or will not stay asleep is the other fault, and a question
          # about the choice between sleeping and shutting down is not about the timer.
          avoid=("wakes", "waking", "woke up", "wake up", "turns itself on", "starts itself",
                 "wont stay asleep", "won't stay asleep", "wakes up", "in the night",
                 "should i shut down", "shut down or sleep", "sleep or shut down"),
          # A person falling asleep at the machine is not the machine falling asleep: "im falling
          # asleep at my laptop" was told to change the sleep timer.
          guard=not_a_sleepy_body),
    entry("laptop-waking-up", (("wakes", "waking", "woke up", "wake up", "turns itself on",
                                "starts itself", "wont stay asleep", "won't stay asleep",
                                "drains", "drain", "goes flat", "loses charge", "losing charge"),
                               ("laptop", "pc", "computer", "macbook", "screen", "lid")),
          "Turn off wake timers and the things that nudge it: on Windows search for Edit Power Plan "
          "> Change advanced power settings > Sleep > Allow wake timers > Disable, and in Device "
          "Manager untick 'Allow this device to wake the computer' on your mouse and keyboard. A "
          "laptop that lights up in the night is nearly always an update, a mouse nudged by a "
          "cat, or the lid sensor. If it still goes flat over a few days while properly shut "
          "down, that is the battery and not something waking it, so check its health first.",
          ask=("wake", "wakes", "waking", "asleep", "sleep", "itself", "night", "shut down",
               "shutdown", "closed", "lid", "overnight", "off"),
          # one point more than it had: the sleep-timer row above adds the word "sleep" to a second
          # key, which is worth a point less to both rows - and the point it lost was the one that
          # decided "my laptop wont stay asleep", which then went to the study-awake card.
          bias=3),
    entry("phone-wifi-wont-connect", (("wont connect", "won't connect", "cant connect", "can't connect",
                                       "no internet", "wont join", "won't join"),
                                      ("wifi", "wi-fi", "wireless", "network")),
          "Forget the network and rejoin it: Settings > Wifi, tap the network, Forget, then add it "
          "again with the password off the router's sticker. If other devices are fine on the same "
          "wifi, the phone is the problem, so restart the phone and check it is not set to a static "
          "IP by accident; a phone that will not connect at all while everything else does is "
          "usually too old for the newer security setting, which the router can be set to WPA2 to fix.",
          bias=1,
          avoid=("broadband", "virgin", "sky", "bt ", "provider", "bill", "tv", "printer")),
    entry("read-receipts", (("read receipt", "read receipts", "blue ticks", "seen my message"),
                             ("turn off", "turn them off", "stop", "disable", "hide", "how do i",
                              "whatsapp", "imessage", "messages")),
          "In WhatsApp it is Settings > Privacy > Read receipts, and switching it off means you stop "
          "seeing theirs as well as them seeing yours. On an iPhone it is Settings > Messages > Send "
          "Read Receipts, which can be off for everyone or on for one contact only. Blue ticks that "
          "stay grey can also just mean they have not opened the chat.",
          bias=1),
    entry("email-to-spam", (("spam", "junk", "junk folder", "spam folder"),
                            ("emails", "email", "mail", "going", "ends up", "landing", "my emails",
                             "messages")),
          "Mark one back: open the Spam or Junk folder, select a message from that sender and press "
          "'Not junk', which teaches the filter for every future one. Then add the address to your "
          "contacts, because a sender you have never written to is the commonest reason real mail "
          "lands in the bin; if you are the one sending, plain text without a picture or link in the "
          "first line gets through more often.",
          bias=1,
          # A person asking how to cut down the junk arriving in their inbox wants the other
          # answer; this one is for mail of yours that is being filed wrongly. "How do i stop my
          # emails going to spam" is still this one, so only the incoming shapes stand it down.
          avoid=("parcel", "order", "delivery", "flight", "letterbox", "door", "post", "paper",
                 "leaflet", "leaflets", "flyers", "letters", "postman",
                 # the other direction: mail arriving that you do not want is `spam-email`, and
                 # "mark it as junk" is the wrong first sentence for "how do i stop spam emails"
                 "stop spam", "stop junk", "stop getting", "stops spam", "prevent spam",
                 "reduce spam", "so much spam", "loads of spam", "getting spam", "getting junk",
                 "block spam", "stop the spam", "spam emails", "spam email", "spam arriving",
                 "unwanted emails", "block the sender", "report spam")),
    entry("storage-space-check", (("how much storage", "storage left", "storage space", "how full",
                                   "space left", "space is left", "space have i got",
                                   "space do i have", "storage do i have", "running out of space"),
                                  ("check", "see", "know", "left", "have", "phone", "laptop",
                                   "iphone", "computer", "tablet")),
          "Settings > General > iPhone Storage, or Settings > Storage on Android, shows a bar with "
          "what is left and a list biggest first. On Windows it is Settings > System > Storage, and "
          "on a Mac the Apple menu > System Settings > General > Storage. Keep about 10 to 20% free: "
          "below that phones slow down and updates refuse to install.",
          bias=1,
          avoid=("rent", "garage", "loft", "warehouse", "shed", "self storage", "attic", "unit")),
    entry("volume-button-stuck", (("volume button", "volume buttons", "volume key", "side button",
                                   "power button"),
                                  ("stuck", "sticking", "wont press", "won't press", "jam",
                                   "jammed", "not working", "broken", "loose")),
          "Clean around it with a dry soft toothbrush and a puff of air, because grit and dried "
          "sweet drink are what wedge them, and never push oil or water in. Work the button gently "
          "a few dozen times with the phone off; if it is still stuck or the phone is now stuck in "
          "a boot loop, a shop replaces the flex cable for £30 to £70. Until then the on-screen "
          "volume slider does the job.",
          bias=1),
    entry("screen-timeout", (("screen turning off", "screen turns off", "screen goes off",
                               "screen locks", "locking", "locks", "auto lock", "autolock",
                               "turns off so fast", "screen timeout", "lock screen",
                               "stays on", "screen stays",
                               # the same setting said the other way round: a screen that times
                               # out is a screen that turns itself off, and "timing out" was the
                               # phone-habit card ("put the phone in another room") instead
                               "times out", "timing out", "timed out", "time out", "goes to sleep",
                               "goes dark", "screen saver", "auto-lock"),
                              ("phone", "how do i", "stop", "fast", "quickly", "change", "increase",
                               "longer", "second", "minute", "lock",
                               # "my screen goes off while im reading" names the setting and the
                               # fault in one go, and asked for nothing else
                               # not "keeps": "my flatmate keeps locking herself out" is a
                               # door, and the word is what put the screen card on it
                               "reading", "wont", "won't", "still",
                               # "how long should" and not a bare "how long": the bare words took
                               # "my phone keeps locking while im reading a recipe" out of reach
                               # of the row that had always answered it, and the phrase is only
                               # ever the question about the setting (#9480 review)
                               "how long should", "set", "settings",
                               # the setting named with the fault and nothing else: "my iphone
                               # screen timeout is too short" names the screen and the fault and
                               # asked for nothing more, and main's key lost it when it moved
                               # "times out" into the first group
                               "too short", "short", "timeout", "iphone", "android")),
          "Android: Settings > Display > Screen timeout. iPhone: Settings > Display & Brightness > "
          "Auto-Lock. Anywhere from 30 seconds to five minutes works and a minute is the usual "
          "compromise; if you set it long, keep a passcode on, because the screen protects "
          "everything else. A phone that locks while you read is usually a screen protector "
          "confusing the sensor. Laptop: Power & battery > Screen and sleep on Windows, Lock "
          "Screen on a Mac.",
          bias=1,
          # "locked" folds to "lock" here, so "my phone is locked to ee" and "how do i unlock my
          # sim" were answered as a screen timeout: the lock they name is the network's.
          # The lock in a door or a car is not the lock on the screen either: "i locked my keys
          # in the car" and "how do i change the lock on my front door" want those answers.
          avoid=("locked to", "any network", "unlock code", "network unlock", "sim only",
                 "sim-free", "sim free", "ee", "o2", "vodafone", "three", "giffgaff", "lebara",
                 "talkmobile", "sky mobile", "tesco mobile", "asda mobile", "smarty",
                 "id mobile", "plusnet", "sim", "door", "doors", "front door", "back door",
                 "porch", "locksmith", "deadbolt", "deadlock", "yale", "mortice", "mortise",
                 "cylinder", "barrel", "padlock", "keyhole", "key", "keys", "handle",
                 "window", "windows", "garage", "shed", "gate", "gatepost", "bike", "bicycle",
                 "chain", "suitcase", "cabinet", "lock myself", "locked out", "lock out",
                 "new lock", "change the lock", "fit a lock", "broken lock",
                 # the house and the car lock too: "how do i lock my front door" and "how do i
                 # stop my car locking itself" were read as a screen timeout, since "lock" is
                 # the only word the two questions share
                 "house", "car", "cars", "boot", "bonnet", "ignition", "van", "car key",
                 # a laptop that locks while you are working is the laptop's power setting, and
                 # this card leads with Android and iPhone, which is the wrong machine for it
                 "laptop", "macbook", "mac book", "computer", "pc", "windows", "desktop")),

    entry("mobile-data-off", (("mobile data", "cellular data", "data roaming", "mobile internet"),
                              ("turn off", "turning off", "switch off", "switching off", "disable",
                               "stop", "off", "save")),
          "On an iPhone it is Settings > Mobile Data, and on Android Settings > Network and "
          "internet > SIMs (or Connections > Data usage) - the switch at the top turns it off, and "
          "wifi carries on working. Switch it off when you are near the end of the month or abroad "
          "without a pass, since that is when the charges start, and check the per-app list "
          "underneath for the one app doing all the downloading.",
          ask=("turn off", "turning off", "switch off", "switching off", "disable", "stop", "off"),
          avoid=("roaming charges", "flight", "abroad", "hotspot", "tether", "plan")),
    entry("phone-switching-off", (("switch", "switches", "switching", "turns itself off",
                                   "shutting itself down", "restarting itself",
                                   # A bare "rebooting" here took every line where someone asked
                                   # to restart their own phone: "i need to reboot my phone" was
                                   # answered "a phone that turns itself off is nearly always the
                                   # battery". The card is about a handset that restarts on its
                                   # own, so the wording that says so is the key.
                                   "reboots itself", "rebooting itself", "reboots on its own",
                                   "rebooting on its own", "restarts on its own",
                                   "restarts by itself", "restarted itself", "restarting by itself"),
                                  ("phone",) + PHONE_KINDS + ("itself", "off")),
          "A phone that turns itself off is nearly always the battery: at 20% or 30% it reads the "
          "charge wrong and shuts down, so check Battery Health, and a worn battery is £40 to £70 "
          "to replace. If it does it at full charge, take the case off and see whether it happens "
          "when it is warm, and back it up before a repair. A phone that reboots on its own every "
          "few hours can also be an app, so start it in safe mode for a day.",
          bias=1,
          avoid=("laptop", "computer", "tv", "telly", "television", "freeview", "sky box",
                 "router", "boiler", "heating", "washing machine",
                 # the water, the gas and the mains are switched off too, and the battery answer
                 # to "how do i switch off the water at the mains" is confident nonsense
                 "water", "mains", "stopcock", "tap", "taps", "plumbing", "pipe", "pipes",
                 "gas", "radiator", "fuse box", "electricity",
                 # a kettle, microwave or washer that cuts out is home's appliance-cutting-out:
                 # the battery answer has nothing to say about a door catch or a scaled element
                 "microwave", "kettle", "toaster", "dishwasher", "oven", "dryer", "tumble dryer",
                 "hoover", "vacuum", "iron", "fan", "appliance",
                 # "switch off mobile data / wifi / bluetooth" is a setting, not a fault
                 "mobile data", "data", "wifi", "wi-fi", "bluetooth", "airplane", "aeroplane",
                 "roaming", "location", "notifications", "auto rotate", "airdrop",
                 # "switch off from work" is the other sense of switch off, and the bare "off"
                 # in the second group was enough to pull the whole wind-down question here.
                 # "i work from home and i cant switch off" is that same sense with no phone
                 # fault in it at all, so the wording of the wind-down question is named too.
                 "from work", "after work", "thinking about work", "taking work home",
                 "wind down", "unwind", "relax", "fall asleep",
                 "from home", "work from home", "working from home", "work at home",
                 "cant switch off", "can't switch off", "cannot switch off",
                 "switch off from", "switch my brain", "switch my head",
                 # "switch the water off" is a valve in the house, not a battery: the plumbing
                 # words stand this entry down (alert-stork, #3333)
                 "water", "stopcock", "stop tap", "stop valve", "mains", "valve", "pipe",
                 "pipes", "plumbing", "gas", "electricity", "lectric", "fuse box", "supply")),
    entry("texts-not-sending", (("texts", "text messages", "imessages", "sms", "messages"),
                                ("not sending", "wont send", "won't send", "failed", "not going",
                                 "stuck", "not delivered", "not arriving")),
          "Check the obvious one first: signal, then mobile data off for iMessages and on for MMS, "
          "then the message centre number (Settings > Apps > Messages > Message centre). If it is "
          "one contact only, their number may now be wrong or blocked; if no text at all will send, "
          "restart the phone and try a normal-length text with no picture, because a big photo with "
          "weak signal fails silently.",
          bias=1),
    entry("find-lost-file", (("find", "finding", "lost file", "cant find", "can't find",
                              "where did", "search for"),
                             ("file", "files", "document", "documents", "folder", "spreadsheet",
                              "download", "downloads")),
          "Use the search box rather than clicking through folders: press the Windows key and type "
          "part of the name, or Cmd+Space on a Mac, and in a browser use Ctrl+J for recent "
          "downloads. Word and Excel keep their own list of recent files under File > Open > Recent, "
          "which finds a document even if it was saved in the wrong place. If it is really gone, "
          "check OneDrive or iCloud's Recently Deleted before anything else.",
          bias=1),
    entry("leave-group-chat", (("leave", "leaving", "left", "mute", "get out of", "exit",
                                "exiting"),
                               ("group chat", "group", "whatsapp group", "family group", "chat")),
          "In WhatsApp open the group, tap the name at the top, scroll down and tap Exit group; "
          "muting it instead (Mute notifications) keeps you in without the noise, which is usually "
          "the better move for a family group. On an iPhone in Messages, open the conversation, tap "
          "the faces at the top and choose Leave this Conversation. You can also just mute it for a "
          "year and nobody is told.",
          ask=("leave", "leaving", "left", "get out", "mute", "exit", "exiting", "how do i",
               "can i"),
          # "left" is the row's own verb, and it is also how a person says they were shut out:
          # "my sister left me out of the family chat" is not a question about how to exit a
          # group, it is the being-left-out card's line (family.py, `left-out-group`).
          avoid=("left me out", "left me out of", "left out of", "left us out", "leaves me out",
                 "leave me out", "leaving me out", "felt left out", "feel left out",
                 "shut out", "excluded"),
          bias=1),
    entry("unsend-email", (("unsend", "recall", "take back", "undo send", "delete a sent email",
                            # "how do i undo an email i sent" said undo and sent, both on the
                            # second part, so the entry scored nothing and the person got the shrug
                            "undo", "undo an email", "unsent", "un-send it"),
                           ("email", "mail", "gmail", "outlook", "sent",
                            # people rarely say "unsend": they say what happened, and every one
                            # of these is the same few-seconds window, not a search result.
                            "un-send", "undo", "sent by mistake", "sent to the wrong",
                            "wrong person", "wrong address", "wrong email", "shouldnt have sent",
                            "already sent"),
                           # "i sent it to the wrong person" reaches the entry on two words and
                           # the wrong-thing group is the one people type, so it counts too - but
                           # only with an email word in it: a bare "wrong" also caught "they sent
                           # me the wrong colour", which is a shop order, not a sent email.
                           ("wrongly", "mistake", "mistakenly", "by accident",
                            "wrong person", "wrong address", "wrong email",
                            "wrong attachment", "wrong recipient")),

          "You can only do it in the seconds after sending: Gmail has Undo in the little bar at the "
          "bottom (set Undo Send up to 30 seconds in Settings), Outlook has Undo Send in the same "
          "way, and Apple Mail has Undo Send if you turn the delay on. After that the honest move is "
          "a short follow-up saying you sent it by mistake and please ignore it, which reads far "
          "better than hoping.",
          bias=1,
          # "my email address is wrong on a parcel" is a delivery, not a recall: the wrong-thing
          # group would otherwise reach a parcel, an order and a form as well as a mail.
          avoid=("parcel", "parcels", "delivery", "package", "order", "postcode", "form",
                 "invoice", "receipt", "return", "returns", "size", "sizing", "shoes",
                 "ticket", "booking", "address is wrong", "wrong address on",
                 # a seller that sent the wrong thing is a consumer order, not a mail recall:
                 # "they sent me the wrong item" answered with Undo Send was a real miss
                 "seller", "item", "amazon", "ebay", "bought", "shop", "refund", "courier",
                 "delivered", "arrived", "it arrived", "my order")),
    entry("autoplay-off", (("autoplay", "auto play", "plays the next one", "keeps playing",
                            "next video plays"),
                           ("turn off", "stop", "youtube", "netflix", "spotify", "how do i",
                            "disable", "amazon", "iplayer")),
          "YouTube: tap your picture > Settings > Autoplay, or on a TV use the Autoplay switch "
          "under the video. Netflix: choose your profile > Account > Profile > Autoplay next "
          "episode. Spotify is Settings > Playback > Autoplay. Those three cover most of the "
          "annoyance; Amazon Prime has Autoplay under the player's settings cog.",
          bias=1,
          # "i already turned off auto play, what else" is a follow-up, not a request to do it
          avoid=("already", "what else", "did that", "done that", "turned it off")),
    entry("streaming-buffering", (("buffering", "keeps pausing", "keeps freezing", "stops to load",
                                   "spinning circle", "loading circle"),
                                  ("netflix", "iplayer", "tv", "streaming", "prime", "disney",
                                   "film", "programme", "youtube", "watch")),
          "Test the broadband on something else in the house: if a laptop on a cable is fine, it is "
          "the wifi, so move the router off the floor and out of a cupboard and use 5GHz for the TV. "
          "If everything buffers, it is the connection - check the speed on the router's own app at "
          "the time it happens, because slow evenings are usually the provider, and a call with "
          "those numbers gets a fault raised.",
          bias=1,
          avoid=("phone call", "call keeps", "zoom", "teams", "voice", "audio call")),
    entry("pair-tv-remote", (("remote", "remote control", "controller"),
                             # "batteries" came out of the key: "how do i change the batteries in
                             # my tv remote" is the battery-and-camera-test row's question, and
                             # this row read it as a pairing question
                             ("pair", "pairing", "not working", "stopped working", "sync",
                              "connect", "new one", "replace")),
          "Point it at the TV and hold the pairing buttons: on most Samsung sets it is the Back and "
          "Play buttons together for three seconds, on LG it is the wheel pressed for five, and a "
          "Fire Stick remote pairs from Settings > Remotes on the TV. Change the batteries first, "
          "and press a button on the TV itself to wake it, because a remote that will not pair is "
          "usually a flat pair of AAAs.",
          bias=1,
          # a remote that has stopped working at all is `tv-remote-dead`'s question - the battery
          # and the camera test come before pairing - and this row is the one that pairs
          avoid=("car", "garage", "gate", "fan", "heating", "central heating",
                 "not working", "stopped working", "doesnt work", "does not work", "dead",
                 "nothing happens", "not responding")),
    entry("change-streaming-password", (("netflix", "iplayer", "prime video", "disney", "spotify",
                                         "now tv", "sky go", "discovery"),
                                        ("password", "change my password", "sign out", "log out",
                                         "hacked", "someone else is using")),
          "Sign in on a browser and do it in Account: Netflix is Account > Security > Change "
          "password, and the same page has 'Sign out of all devices', which is the part that "
          "actually removes whoever else is watching. Do that first if the account is being used by "
          "someone else, then change the password, and check the profile list for names you do not "
          "recognise.",
          bias=1),
    # A word that names the thing leaked, not the leak itself: "my boiler is leaking what do i do"
    # is a plumber's job, and a bare "leaked" / "breach" took it and told the person to change a
    # password. Every phrase here carries what was breached or where.
    # Two halves, and both have to be there: a word for a thing being exposed, and the thing.
    # "my boiler is leaking what do i do" has the first and not the second, so it goes to the
    # plumber; "my password got leaked" and "some site leaked my password" have both and get the
    # password answer, whatever order they are said in. "hacked" is deliberately not here: the
    # account-intrusion entry below answers that line better.
    entry("password-compromised", (("leaked", "leak", "leaks", "leaking", "breached", "breach",
                                    "compromised", "exposed", "someone logged in", "logged in",
                                    "got into my account", "someone has my account",
                                    "someone has my password", "signed in from", "login from"),
                                   ("password", "passwords", "account", "accounts", "email",
                                    "emails", "bank", "details", "data", "information", "info",
                                    "card", "cards", "login", "logins")),
          "Change that password now, and change it anywhere you used the same one, because that is "
          "what gets tried next; a password manager makes that ten minutes' work rather than an "
          "afternoon. Then check the account's own security page for devices and sessions you do "
          "not recognise and sign them out, and turn on two-factor with an app rather than a text "
          "if it offers one. If money is involved, ring the bank on the number on your card.",
          bias=1,
          avoid=("wifi", "router", "netflix", "iplayer", "sky box", "laptop bios")),
    # "how do i stop my tv from switching off" is the same fault said with the wrong tense, and the
    # row missed it: the key held "turns itself off" and "going off" but not "switching off".
    entry("tv-turning-off", (("turning itself off", "turns itself off", "switches itself off",
                              "switching itself off", "from switching off",
                              "switches off on its own", "switching off on its own",
                              "switch itself off", "switched itself off",
                              "keeps switching itself off", "going off", "shuts itself down",
                              "keeps turning off", "keeps switching off", "keeps going off",
                              "turns off", "turn off after", "off after",
                              "goes off by itself", "cuts out"),
                             ("tv", "television", "telly", "screen", "soundbar")),
          "Turn off the sleep timer first - it is in Settings > General > Timers or System > Time on "
          "most sets, and an hour is the factory default on some. Then look for Auto Power Off or "
          "Auto Standby in the Eco or Power settings, which switches the set off after four idle "
          "hours on many TVs. If it still happens, unplug "
          "everything else from the TV (a games console or a Fire Stick can wake it and put it back "
          "to sleep) and check the power lead is not in a socket with a timer switch. A TV that "
          "clicks off after ten minutes is usually a power board, which a repair shop fixes for "
          "£60 to £120.",
          bias=1,
          # "turn off" is how a setting is asked about: a brightness line is not a set that
          # switches itself off, and a phone's screen timeout is `phone-switching-off`
          avoid=("brightness", "bright", "dimmer", "dim", "volume", "louder", "quieter", "mute",
                 "phone", "iphone", "android", "laptop", "computer", "night mode", "dark mode")),
    entry("webcam-blurry", (("blurry", "blurred", "fuzzy", "out of focus", "smudge", "smudged",
                             "grainy", "hazy"),
                            ("webcam", "camera", "video call", "zoom", "teams", "lens", "laptop")),
          "Clean the lens: it is a tiny piece of glass that collects fingerprints, and a dry "
          "microfibre cloth or a cotton bud with a breath on it is all it needs, never a tissue and "
          "never alcohol. Then check the camera app itself is not set to a low resolution, and that "
          "the light behind you is not the brightest thing in the frame, because a window at your "
          "back is what makes a face go dark and grainy.",
          bias=1,
          avoid=("photo", "photos", "phone camera", "night", "tv", "video doorbell")),
    entry("phone-update", (("update", "updates", "updating", "software update", "new version",
                             "security patch", "upgrade my phone"),
                            ("phone", "iphone", "android", "handset", "ios", "samsung", "pixel")),
          "Do it on wifi with the phone on charge: on an iPhone it is Settings > General > Software "
          "Update, and on Android Settings > Software update (Samsung: Settings > Software update > "
          "Download and install). Take it even when it is just a security patch, because those are "
          "the fixes that stop the known holes being used, and leave enough space free - a nearly "
          "full phone cannot unpack the update and says it is up to date when it is not.",
          bias=1,
          # the tablet, laptop and telly have their own entries
          avoid=("laptop", "macbook", "windows", "computer", "imac", "ipad", "tablet", "kindle",
                 "tv", "television", "watch", "app", "whatsapp", "car", "sat nav")),
    entry("laptop-cost", (("laptop", "macbook", "computer", "notebook"),
                           ("how much", "cost", "costs", "price", "prices", "spend", "budget",
                            "cheapest", "cheap", "expensive")),
          "£350 to £550 buys a new laptop that does everything most people need - browsing, email, "
          "video calls, streaming and office work - and £700 and up is where photo editing, big "
          "spreadsheets and gaming start to need it. Below about £250 new you are buying something "
          "that is already slow, so at that price buy a refurbished ex-business machine instead: "
          "three years old, grade A, with a warranty, for a third of new.",
          ask=("how much", "cost", "price", "spend", "budget", "cheap", "expensive"),
          bias=1,
          # the battery and the repair have their own prices
          avoid=("battery", "batteries", "repair", "fix", "insurance", "warranty", "applecare",
                 "apple care", "screen", "upgrade", "storage", "phone", "iphone", "ipad",
                 # a spec question is ram-needed and storage-space-check, not a price
                 "memory", "ram", "disk", "hard drive", "ssd", "processor", "cpu", "graphics",
                 "gb")),
    entry("keyboard-wrong-letters", (("keyboard", "keys", "typing", "type"),
                                      ("wrong letters", "wrong letter", "wrong characters",
                                       "typing the wrong", "types the wrong", "wrong keys",
                                       "garbled", "mixed up", "wrong symbols", "wrong symbol")),
          "That is the layout, not the keyboard: on Windows press the Windows key and Space to "
          "cycle back to English, or click the ENG box by the clock and pick the right one, and "
          "turn Num Lock off because it turns the right-hand letters into numbers. If it is only "
          "the @ and the quote in the wrong place, the keyboard type is set to United States when "
          "you have a United Kingdom one - change it in Settings > Time and language > Language.",
          bias=1,
          avoid=("clean", "dust", "crumbs", "spill", "coffee", "water", "dead", "not working",
                 "stopped", "remote", "piano", "guitar")),
    # The other half of the same ask: "how do i hide where i am", "who can see my location" and
    # "how do i stop someone seeing where i am" are all questions about who can see, and they name
    # the place by "where i am" rather than by "location". Without those words they reached the
    # search hedge, and one of them reached a row that tells a person how to share it.
    entry("turn-off-location", (("location", "location services", "gps", "location sharing",
                                "where i am", "where im", "whereabouts", "seeing where i am",
                                # "how do i keep my location private" is the same ask as hiding
                                # it, and no key held the word the line uses for it
                                "location private", "my location private", "location secret"),
                                ("turn off", "turning off", "switch off", "disable", "stop",
                                 "off", "hide", "private", "keeping it private",
                                 # "who can see my location" is the same ask from the other
                                 # end, and it was only a hedge: the list of who can see is on
                                 # the same screen as the switch that stops it
                                 "who can see", "who else can see", "who sees")),
          "On an iPhone it is Settings > Privacy and Security > Location Services, where you can "
          "turn the whole thing off or set each app to Never or Ask Next Time; on Android open "
          "Settings > Location > App location permissions and set the ones you do not trust to "
          "Don't allow. Leave maps and Find My on, since they are the two you want when a phone is "
          "lost, and remember a phone still knows roughly where it is from the network.",
          ask=("turn off", "turning off", "switch off", "disable", "stop", "hide", "off",
               "private", "who can see", "who else can see", "who sees"),
          avoid=("find my", "where is my phone", "lost my phone", "parcel", "delivery", "order",
                 "train", "flight", "hotel", "parking", "nearest")),
    entry("monitor-turning-off", (("monitor", "second screen", "external screen", "external display"),
                                  ("keeps turning off", "turning itself off", "turns itself off",
                                   "goes blank", "goes black", "cuts out", "flickers off",
                                   "switches off", "loses signal")),
          "Change the cable and the port first: a tired HDMI or DisplayPort lead loses the signal "
          "for a second and the monitor goes to standby, so try the other port and a lead you know "
          "works. Then stop the machine sleeping the screen - on Windows Settings > System > Power > "
          "Screen and sleep, and turn off the monitor's own power saving in its menu. A monitor "
          "that clicks off and shows 'no signal' is the cable or the graphics driver; one that goes "
          "black with the power light still on is usually the backlight, which is a repair.",
          bias=1,
          avoid=("tv", "television", "telly", "phone", "laptop screen", "backlight", "sleep timer",
                 "power cut")),
    entry("hide-number", (("hide my number", "hide the number", "withhold my number",
                            "caller id", "number withheld", "private number", "show my number"),
                           ("call", "calls", "ring", "dial", "phone", "ringing")),
          "On an iPhone it is Settings > Phone > Show My Caller ID, off; on Android open the Phone "
          "app > Settings > Calls > Additional settings > Caller ID > Hide number. Type 141 in "
          "front of a number to hide it for one call only, and 1470 to show it again. Banks and "
          "doctors ignore withheld numbers, so it is worth doing for one call rather than always.",
          ask=("hide", "withhold", "caller id", "private", "show my number", "141", "1470")),
    entry("keyboard-sounds-off", (("keyboard sound", "keyboard click", "clicking sound",
                                   "keyboard clicks", "typing sound", "click sound", "key clicks"),
                                  ("turn off", "switch off", "stop", "silent", "mute", "disable",
                                   "turn it off")),
          "On an iPhone go to Settings > Sounds and Haptics > Keyboard Feedback and turn Sound "
          "off; on Android Settings > System > Languages and input > On-screen keyboard > Gboard > "
          "Preferences, and switch off Sound on keypress. A laptop that clicks out loud is the "
          "mechanical keyboard itself, not a setting.",
          ask=("turn off", "switch off", "stop", "silent", "mute", "disable")),
    entry("hotspot", (("hotspot", "tether", "tethering", "personal hotspot",
                       "use my phone as a router", "wifi from my phone"),
                      ("use", "set up", "turn on", "work", "how", "share", "laptop", "ipad")),
          "Turn it on in Settings > Personal Hotspot on an iPhone, or Settings > Network and "
          "internet > Hotspot and tethering on Android, and set a password before you do. Other "
          "devices then see the phone's name in their wifi list. It eats data fast - a laptop "
          "update can take a gigabyte - so keep it for the odd hour and plug the phone in, since "
          "a hotspot drains the battery quickly.",
          ask=("use", "set up", "turn on", "how", "share"),
          avoid=("car", "wifi hotspot in the garden", "voucher", "cafe")),
    entry("parental-controls", (("parental controls", "parental control", "family link",
                                  "content restrictions", "restrictions", "parental"),
                                 ("phone", "iphone", "ipad", "tablet", "android", "child", "kid",
                                  "kids", "son", "daughter", "set up", "setup", "how do i",
                                  "turn on", "enable", "limit")),
          "On an iPhone it is Settings > Screen Time > Content & Privacy Restrictions: turn it on, "
          "then set the age rating for apps, block in-app purchases, and require a passcode for "
          "installs. On Android install Google Family Link and approve apps and screen time from "
          "your own phone. The one rule that matters is the passcode: use a different one from the "
          "phone's own, or a child who can unlock it can turn the limits off.",
          bias=1,
          avoid=("all evening", "all day", "too much", "so much", "addicted", "wont get off",
                 "won't get off", "get off his", "get off her", "talk to", "tv", "telly",
                 "xbox", "playstation", "nintendo")),
    entry("too-many-emails", (("email", "emails", "inbox", "newsletter", "newsletters"),
                              ("too many", "hundreds", "loads", "overwhelmed", "unsubscribe",
                               "filter", "filters", "folder", "digest", "notifications",
                               "stop", "reduce", "cut", "drowning", "keep", "getting", "sort",
                               "out of control", "control", "chaos", "cluttered", "swamped",
                               "buried", "madness", "flooded", "flood of", "overflowing",
                               # The follow-up that answers itself with a detail: "and half of
                               # them are newsletters" after "im getting so many emails" is the
                               # same question with more of the picture, and it was landing on
                               # the receipt. A share of them is a count of them.
                               "newsletters", "newsletter", "half of them", "most of them",
                               "all of them", "half of my emails", "most of my emails")),
          "Unsubscribe from everything you have not opened in a month: the link is at the foot of "
          "every newsletter, and that alone halves most inboxes. Then set one filter so the rest "
          "lands in a folder you open once a day, turn off notifications, and answer what is left "
          "in two sittings rather than all day.",
          bias=1,
          avoid=("spam", "junk", "scam", "phishing", "hacked", "password", "mailbox full",
                 "bouncing", "out of office",
                 # "my mum keeps clicking on links in emails is there a way to stop it" is the
                 # phishing question, and the number of emails is not what it is about: the
                 # person clicking is. A card about volume stands down when the line is about
                 # what is inside them - a link, a stranger, a scam, or a relative who may fall
                 # for one. The volume asks ("so many emails", "filter emails") carry none of
                 # these words, so they keep the card.
                 "click", "clicks", "clicked", "clicking", "links", "link", "scam", "scams",
                 "scammy", "phishing", "fraud", "fraudulent", "stranger", "strangers",
                 "elderly", "dementia", "vulnerable",
                 # a card about how many emails there are has nothing to say about how they are
                 # written: "my boss keeps sending sarky emails, how do i reply" is about the tone,
                 # and the key holds "keep" and "getting", which that line says too.
                 "sarky", "sarcastic", "sarcasm", "snarky", "snide", "passive aggressive",
                 "passive-aggressive", "condescending", "patronising", "patronizing",
                 "cheeky", "narky", "grumpy", "sneering", "belittling", "undermining",
                 # "my emails have stopped coming through" is mail that is not syncing: the key
                 # holds "keep" and "getting", which that line says too
                 "not syncing", "stopped syncing", "stopped coming", "not coming through",
                 "not arriving", "not updating", "not receiving", "wont sync", "will not sync",
                 # Somebody not answering is the same key as a full inbox - the word for mail
                 # and the word for frequency - and a card about volume is no help to it: "my
                 # boss keeps ignoring my emails" was told to unsubscribe from newsletters. The
                 # silence, not the person, is what stands this card down: "my boss sends me too
                 # many emails" is still a volume question and carries none of these words.
                 "ignoring my emails", "ignores my emails", "ignoring me", "ignores me",
                 "ignored my emails", "ignoring my messages", "ignores my messages",
                 "not replying", "isnt replying", "isn't replying", "stopped replying",
                 "never replies", "never replied", "hasnt replied", "hasn't replied",
                 "wont reply", "won't reply", "wont answer", "won't answer", "not answering",
                 "never answers", "doesnt answer", "doesn't answer", "no reply", "no response",
                 "getting no reply", "get no reply", "getting no answer", "heard nothing",
                 "unanswered", "unresponsive", "ghosted", "ghosting", "wont respond",
                 "won't respond", "doesnt respond", "doesn't respond", "chasing", "chased",
                 "chase them", "chase him", "chase her")),

    # --- the phone's own settings and the bill behind it ---------------------
    entry("phone-bill-too-high", (("phone bill", "mobile bill", "phone contract", "broadband bill",
                                  "internet bill", "tv bill", "landline bill", "phone", "mobile",
                                  "broadband", "sim", "data",
                                  # the telly and satellite bills are the same question and were
                                  # reaching the energy row: "my sky bill has gone up" was told to
                                  # read the meter once a day
                                  "sky", "sky tv", "sky bill", "satellite", "virgin media",
                                  "subscription", "subscriptions", "package", "sky broadband"),
                                 ("too high", "so high", "going up", "went up", "gone up",
                                  "too much", "expensive", "cheaper", "lower", "reduce", "cut",
                                  "save", "deal", "loyalty", "retention", "bill shock")),
          "Ring your provider and ask for the retention or loyalty price, and say plainly that you "
          "are looking at leaving: the deal they offer on that call is usually 20 to 30% below the "
          "list price, and a two-year recontract is what buys it, so only take it if you are happy "
          "to stay. Out of contract, you are free to go with 30 days' notice and a PAC code, which "
          "is the strongest thing to say on the call. Check the bill lines first, though: phone "
          "insurance, extra data and an add-on nobody uses are the usual culprits. If money is "
          "tight, ask about the social tariff, which most big providers now offer quietly.",
          # A phone or broadband bill that went up is this row's line and not the general
          # price-rise card: the bill is named, and this answer asks for the retention price by
          # name. The two tie on score, so the named bill is given the tie.
          bias=2,
          # gas, electricity and water bills have their own entries; a builder's quote is not a bill.
          avoid=("energy", "electricity", "gas", "water", "council tax", "quote", "boiler",
                 "car insurance", "mortgage", "rent",
                 # a child on the phone all evening is not a bill: "my son spends too much time on
                 # his phone" was being told to ring the provider about the retention price, off
                 # the word "too much" beside "phone". The screen-time answer is the one for it.
                 "too much time", "spends too much", "spending too much", "spend too much time",
                 "screen time", "addicted", "addiction", "always on", "glued to",
                 "on his phone", "on her phone", "on their phone", "on her tablet",
                 "on his tablet", "all day on",
                 # "reduce" is also how a setting is asked about: a volume or brightness line is
                 # not a bill, and "how do i reduce the volume on my phone" was being told to ring
                 # the provider for a better deal
                 "volume", "louder", "quieter", "muffled", "brightness", "bright", "dimmer",
                 "turn up", "turn down", "mute", "ringtone", "screen",
                 # a phone that is broken, wet or hacked is a repair question, and "save" in the
                 # ask list was reading "how do i save a wet phone" as a money-saving line
                 "wet", "dunked", "dropped", "smashed", "cracked", "crack", "wont turn on",
                 "won't turn on", "wont charge", "won't charge", "screen", "stuck", "virus",
                 "hacked", "rescue", "repair",
                 # a name I put in the key for the bill question was taking the cancelling
                 # question: "sky tv is too expensive can i cancel" went to the retention price
                 "cancel", "cancelling", "canceling", "cancelled", "canceled",
                 # "how do i save battery on my phone" was read as "save" on a bill because
                 # "phone" is in the key and "save" in the ask: a battery that does not last the
                 # day is a phone question, and a charger is not a bill either.
                 "battery", "batteries", "battery life", "charger", "chargers", "charging",
                 "charge", "draining", "drains", "dies quickly")),
    entry("swollen-battery", (("swollen", "swelling", "swollen battery", "bulging", "bulge",
                                "puffed up", "puffed", "expanded", "expanding"),
                               ("battery", "phone", "laptop", "handset", "back")),
          "Stop using it and stop charging it: a swollen battery is a fire risk, and pressing on it "
          "to make it fit is how they catch light. Keep it out of the sun, do not bend or puncture "
          "it, and take it to a repair shop or the battery bin at the tip rather than the kitchen "
          "bin. A new battery is usually £40 to £70 fitted, and most shops do it the same day.",
          bias=2,
          avoid=("car", "van", "campervan", "motorhome", "motorbike", "motorcycle", "bike",
                 "lipo", "drone", "solar",
                 # a swollen door, knee or ankle is not a swollen laptop battery: the symptom
                 # word is shared, the thing that is swollen is what tells them apart
                 "door", "doors", "back door", "front door", "shed", "cupboard", "frame",
                 "wood", "wooden", "hinge", "ankle", "knee", "wrist", "joint", "gland",
                 "glands", "leg", "foot", "face", "eye",
                 # "how do i expand storage on my laptop" was read as a swollen battery, because
                 # "expand" is in the key for a battery that has expanded: a machine that needs
                 # more room is the storage rows' question, and it names storage, not swelling.
                 "storage", "more storage", "space", "no space", "disk", "hard drive",
                 "ssd", "sd card", "memory", "ram", "photos", "files", "apps", "backup",
                 "bigger drive", "external drive")),
    entry("mac-antivirus", (("antivirus", "anti virus", "virus protection", "security software",
                             "malware", "virus scanner", "virus", "viruses"),
                             ("mac", "macbook", "imac", "macos", "mac os", "apple")),
          "You do not need to buy antivirus for a Mac: keep macOS updated and install only from the "
          "App Store or developers you have heard of, which covers nearly all of it. If the machine "
          "is already misbehaving, run the free Malwarebytes scan once and delete it again; the paid "
          "suites mostly slow the Mac down.",
          bias=1),
    # "what is the best free antivirus" reached the shape-only chooser and got a question back
    # ("What will you use it for most?") - the one reply that helps nobody who asked for a name.
    # A virus in Windows, Android or a phone has the same short answer, and it is not on a Mac,
    # a tomato plant or a person, so those words stand this row down.
    entry("free-antivirus", (("antivirus", "anti virus", "virus protection", "security software",
                              "virus checker", "malware", "virus scanner", "virus"),
                             ("best", "recommended", "recommend", "need", "needed", "free",
                              "worth it", "worth", "which one", "which", "should i get",
                              "should i use", "do i need", "pay for", "buy", "good")),
          ("On Windows you do not need to buy one: Microsoft Defender is built in, free and as "
           "good as the paid suites, and it updates itself. Phone and tablet: Play Protect on "
           "Android and an iPhone need nothing else. Add a free Malwarebytes scan only if "
           "something is already misbehaving. Paid antivirus mostly sells pop-ups and a slower "
           "machine, so keep it updated, install only from the store, and never ring the "
           "number in a pop-up saying your PC is infected."),
          bias=1,
          avoid=("mac", "macbook", "imac", "macos", "mac os", "apple",
                 # a virus on a plant or in a person is not software
                 "tomato", "tomatoes", "plant", "plants", "cucumber", "crop", "crops", "tree",
                 "garden", "flower", "potato", "stomach", "cold", "flu", "cough", "fever",
                 "sick", "child", "baby", "dog", "cat")),
    entry("clear-browser-history", (("clear", "delete", "wipe", "erase", "empty", "remove",
                                     "get rid of", "turn off", "stop"),
                                    ("history", "cookies", "cache", "browsing data",
                                     "search history", "autofill")),
          "In Chrome press Ctrl+Shift+Delete (Cmd+Shift+Delete on a Mac) and the clear-data box "
          "opens: pick the time range, tick history, cookies and cached files, then clear. On a "
          "phone it is the three dots or Safari's settings, then History and Website Data. "
          "Clearing cookies signs you out of most sites, so tick them only if you want that.",
          bias=1,
          # "how do i clear the cache" has its own entry, and it is the better answer
          avoid=("cache", "router", "boiler", "shed", "garage", "history of the house",
                 # "how do i stop cookies spreading" is about dough on a tray: the word "stop"
                 # and the word "cookies" are all this entry needed before, so a baking line in
                 # the same words got Ctrl+Shift+Delete. Anything that talks about baking stands
                 # aside, and the kitchen's cookie-spread answer takes it.
                 "spread", "spreading", "spreads", "dough", "bake", "baked", "baking",
                 "oven", "tray", "recipe", "butter", "flour", "chill", "fridge",
                 "batch", "biscuits")),
    entry("autocorrect-off", (("autocorrect", "auto correct", "autocorrecting", "predictive text",
                                "correct my words", "changes my words", "keeps changing my words",
                                "correcting my words", "right words", "wrong words"),
                               ("phone", "iphone", "android", "keyboard", "typing", "type",
                                "stop", "turn off", "switch off", "disable", "laptop", "text")),
          "On an iPhone it is Settings > General > Keyboard, where Auto-Correction and Predictive "
          "Text have switches of their own. On Android open the keyboard's settings (Gboard > "
          "Settings > Text correction) and turn Auto-correction off. Turning off predictive text "
          "as well is what stops whole words being swapped under your thumb."),
    entry("email-new-phone", (("email", "emails", "gmail", "outlook", "mail app", "inbox"),
                               ("new phone", "new mobile", "new handset", "new iphone",
                                "new android", "new device", "set up", "setting up", "move")),
          "Install Gmail or Outlook and sign in with the address and the password: it brings in the "
          "last 30 days and then keeps syncing, and both apps hold several accounts at once. If it "
          "is a work address, ask IT for the settings rather than guessing, because it usually needs "
          "a Microsoft or Google sign-in, not just a password.",
          bias=1,
          avoid=("spam", "junk", "scam", "phishing", "hacked", "hotmail", "account")),
    entry("screen-protector", (("screen protector", "screen guard", "tempered glass",
                                 "screen film", "phone case", "case for my phone",
                                 "case for the phone", "a case for"),
                                ("worth", "should i", "need", "get", "buy", "good", "which",
                                 "phone", "iphone", "ipad", "tablet", "case", "new")),
          "Yes, a tempered-glass one is worth the £5 to £15: it takes the scratches and the knock "
          "the screen would, and it is cheap to replace. For a drop, a case matters more than the "
          "glass, so get both, and fit the protector in a steamy bathroom so the dust settles out "
          "of the air first.",
          ask=("worth", "should i", "need", "get", "buy", "good", "any good", "which"),
          avoid=("mattress", "mattress protector", "sofa", "chair cover", "sunscreen",
                 "sun cream", "paint")),
    entry("laptop-grinding", (("grinding", "grinds", "scraping", "rattling", "rattle",
                                "clicking noise", "clicking", "buzzing", "whirring", "ticking",
                                "scrapes", "rattles", "buzzes"),
                               ("laptop", "computer", "pc", "macbook", "fan", "hard drive",
                                "hard disk")),
          "Back the files up first, then tell the two noises apart: a grinding or scraping that "
          "follows the fan's speed is the fan bearing, and a fan is £20 to £40 fitted. A regular "
          "click or a tick followed by a pause is the hard drive going, which is urgent - copy the "
          "files off now and stop using it, because those drives go from clicking to dead with no "
          "warning.",
          bias=1,
          guard=_a_fan_is_the_computers,
          # "the ceiling fan is noisy" is a house fan, not a laptop: the bare word "noise"
          # already matched here, and the room fans are named so they cannot come back.
          avoid=("kettle", "boiler", "car", "van", "washing machine", "fridge", "dishwasher",
                 "teeth", "jaw", "coffee grinder", "blender", "ceiling", "ceiling fan",
                 "extractor", "bathroom", "shower", "tower fan", "pedestal", "desk fan",
                 "standing fan", "house fan", "attic", "room fan", "oven", "fan oven", "cooker", "cookers", "hob", "microwave", "grill")),
    entry("phone-night-photos", (("photos", "photo", "pictures", "picture", "camera", "pics",
                                  "camera app"),
                                 ("night", "nights", "dark", "low light", "evening",
                                  "in the dark", "grainy")),
          "Tap the screen to set the focus and the exposure, then drag the little sun slider down a "
          "notch, because night shots are wrecked by one bright light in the frame. Brace the phone "
          "on a wall or a table and hold still while Night mode takes its couple of seconds, and "
          "turn the flash off: it lights the air rather than the subject. Clean the lens with your "
          "sleeve first, since a smeared lens is the commonest cause of bad night photos.",
          ask=("photos", "photo", "pictures", "picture", "camera", "pics"),
          avoid=("print", "prints", "printing", "send", "share", "back up", "backup", "transfer",
                 "scan", "scanning", "album", "calendar", "frame", "wallet", "passport")),
    entry("smart-watch", (("smart watch", "smartwatch", "fitbit", "apple watch", "garmin",
                            "fitness tracker", "fitness watch", "tracker"),
                           ("worth", "should i", "get", "buy", "need", "which", "better",
                            "good", "any good",
                            # "would you recommend a fitness tracker" is the same verdict as
                            # "is a fitness tracker worth it", and it got the honest shrug.
                            "recommend", "recommended", "recommendation", "recommendations")),
          "Worth it if you want steps, heart rate and messages without getting the phone out; not "
          "worth it if what you really want is a watch that runs for a week. A Garmin or Fitbit goes "
          "five days or more and an Apple Watch about one, and an Apple Watch needs an iPhone, so "
          "check the pairing before you choose.",
          avoid=("lost", "stolen", "broken", "sync", "pair", "pairing", "strap", "water")),
    entry("in-app-purchases", (("buying things", "buys things", "keeps buying", "bought something",
                                 "in app", "in-app", "purchases", "purchase", "spent money",
                                 "spending money", "charging my card", "extra charges"),
                                ("phone", "ipad", "tablet", "app", "game", "games", "child", "kid",
                                 "kids", "son", "daughter", "mine", "account")),
          "Stop it at the setting, not with a telling-off: turn on Ask to Buy in Family Sharing, or "
          "set Settings > Face ID & Passcode > iTunes & App Store purchases to Always Require, so "
          "nothing is bought without you. Then ask Apple or Google for a refund on the last 90 days "
          "of charges - both have a form for exactly this, and they usually give it back the first "
          "time.",
          bias=1,
          ask=("buying", "buys", "bought", "purchase", "purchases", "spent", "spending", "charges"),
          avoid=("house", "car", "groceries", "rent", "shopping", "clothes", "holiday")),
    entry("iphone-or-android", (("iphone or android", "android or iphone", "iphone vs android",
                                 "android vs iphone", "iphone or a samsung", "apple or android",
                                 "iphone or samsung", "android or samsung",
                                 # "is iphone better than android" and "which is better iphone or
                                 # android" are the same comparison without the word order above
                                 "better than android", "better than iphone", "better than an android",
                                 "better than an iphone", "better, iphone", "better, android",
                                 # "an android" is how people write it, and without these two the
                                 # line "should i get an iphone or an android" stood down and got
                                 # the not-mine-to-decide reply
                                 "iphone or an android", "android or an iphone"),
                                ("get", "buy", "better", "which", "choose", "should i", "recommend",
                                 "switch", "worth",
                                 # A short line names the pair and nothing else - "iphone or
                                 # android", "iphone vs android" - so the "or" or the "vs" is the
                                 # only thing saying it is a choice. Without it the line matched
                                 # nothing at all: opinions.android-iphone stands itself down for
                                 # this answer, and both keys missed.
                                 "or", "vs", "versus")),
          "iPhone if you want the long updates and everything to talk to the rest of the family's; "
          "Android if you want to spend less, get two days of battery, or keep a headphone jack. The "
          "cheapest way in is a two-year-old iPhone or a mid-range Samsung, and both last well if you "
          "put a case on them.",
          bias=1,
          avoid=("charger", "cable", "watch", "ipad", "tablet", "laptop", "mac")),
    # The other buying choice this table kept losing to a supermarket answer: "should i buy a
    # laptop or a tablet" was answered with the price per kilo of a big pack, because "tablet"
    # folds to "tablets" and "buy" was all the price-per-unit row needed.
    entry("laptop-or-tablet", (("laptop or a tablet", "tablet or a laptop", "laptop or tablet",
                                "tablet or laptop", "laptop or an ipad", "ipad or a laptop",
                                "laptop or an ipad", "chromebook or a laptop",
                                "laptop or a chromebook", "laptop or a desktop",
                                "desktop or a laptop", "laptop instead of a tablet",
                                "tablet instead of a laptop", "tablet or a chromebook",
                                "laptop or an ipad pro"),
                               ("should i", "which", "better", "buy", "buying", "get", "worth",
                                "instead", "or", "vs", "versus", "choose", "recommend",
                                "need")),
          "A laptop if you will be typing - email, essays, spreadsheets, work - and a tablet if "
          "it is mostly reading, video, calls and games on the sofa. A tablet with a keyboard "
          "costs about what a laptop does and types worse, so make it the only machine only if "
          "you truly do not type; a cheap laptop and a 300 pound tablet side by side covers the "
          "most ground for the money.",
          bias=1,
          avoid=("broken", "repair", "cracked", "battery", "charge", "charging", "charger",
                 "slow", "stolen", "screen", "return", "refund", "windows", "update")),
    entry("headphone-volume", (("headphones", "earbuds", "airpods", "earphones", "in ears"),
                               ("loud", "louder", "volume", "hearing", "safe", "too loud", "how loud",
                                "damage", "ringing")),
          "Keep it at about 60% for no more than 60 minutes at a time - that is the rule hearing "
          "specialists give, and phones now warn you when you go past it. If someone a metre away "
          "can hear your music, it is too loud; noise-cancelling earphones help because you stop "
          "turning it up over the background.",
          ask=("loud", "louder", "volume", "hearing", "safe", "damage", "ringing", "how loud")),
    entry("restart-computer", (("restart", "reboot", "turn off", "shut down", "shutdown"),
                                ("how often", "often", "should i", "does it help", "properly",
                                 "correctly", "every day", "regularly", "off at night")),
          "Restart it when it asks, and once a week if it never does: that clears the memory leaks "
          "and half-installed updates that make a machine feel tired. Shut down properly from the "
          "Start menu or the Apple menu rather than holding the power button, which is the same as "
          "pulling the plug and can leave files half-written.",
          ask=("how often", "often", "should i", "properly", "correctly", "regularly", "every day",
               "off at night", "does it help"),
          avoid=("who", "what time", "alarm", "medication", "tablet", "dose")),
    entry("delete-text-message", (("delete", "deleting", "clear", "get rid of"),
                                  ("text message", "text messages", "text", "texts", "message",
                                   "messages", "conversation", "chat")),
          "Press and hold the message and choose More or Delete, then pick the ones you want gone; "
          "on an iPhone you can also swipe left on a whole conversation in Messages to delete it "
          "all. Deleting only removes it from your phone, so the other person still has their copy, "
          "and a backup can bring it back until that backup is overwritten.",
          ask=("delete", "deleting", "clear", "get rid of", "remove"),
          avoid=("email", "inbox", "voicemail", "facebook", "instagram", "whatsapp group", "account",
                 "post", "comment", "app", "apps", "photo", "photos", "file", "files")),
    entry("stop-app-updates", (("update", "updates", "updating", "auto update", "auto-update"),
                               ("apps", "app", "play store", "app store", "google play")),
          "Turn off automatic updates in the store itself: Play Store > Settings > Network "
          "preferences > Auto-update apps > Don't auto-update, or Settings > App Store > App "
          "Updates on an iPhone. Then update in one go over wifi once a week, because the security "
          "fixes matter more than the new look.",
          ask=("auto", "automatic", "automatically", "stop", "turn off", "disable", "how do i"),
          avoid=("windows", "laptop", "computer", "mac", "phone itself", "ios", "android version")),
    entry("delete-email", (("delete", "deleting", "clear", "empty", "unsubscribe", "get rid of"),
                          ("email", "emails", "inbox", "mail", "messages")),
          "Tick the ones you want and press delete, then empty the bin or they still take up space: "
          "in Gmail that is Bin > Empty Bin Now. For the flood rather than one message, select a few "
          "and use Filter messages like these to delete or archive every sender at once, and "
          "unsubscribe instead of deleting if it is a newsletter.",
          ask=("delete", "deleting", "clear", "empty", "get rid of", "too many"),
          avoid=("text", "texts", "sms", "whatsapp", "instagram", "facebook", "account", "unlink")),
    entry("send-big-file", (("send", "share", "email", "transfer"),
                            ("big file", "large file", "huge file", "big video", "large video",
                             "too big", "too large", "big attachment", "photos to")),
          "Use a link rather than an attachment: WeTransfer or Google Drive will take 2GB free and "
          "email the other person a link that expires. For photos and video between your own "
          "devices, a shared album in Google Photos or iCloud does it without any compression.",
          ask=("send", "share", "email", "transfer", "too big", "too large"),
          avoid=("house", "car", "money", "bank", "parcel", "letter", "form")),
    entry("laptop-black-screen", (("black screen", "screen is black", "screen went black",
                                   "screen stays black", "nothing on the screen",
                                   # "my laptop screen has gone black" missed this row by one
                                   # phrase and fell to a hedge once _mould stopped claiming it.
                                   "screen has gone black", "laptop screen",
                                   "screen has gone dark", "screen has gone blank", "gone dark",
                                   "gone blank", "screen went dark", "screen is dark",
                                   "going black", "goes black", "going blank", "goes blank",
                                   "keeps going black", "keeps going blank"),
                                  ("laptop", "computer", "pc", "mac", "macbook", "monitor",
                                   "still on", "still running", "fan")),
          "It is probably asleep or on the wrong display, not dead: press a key, then try the "
          "brightness keys and Ctrl+Alt+Del, and if the fan is still running, hold the power button "
          "for ten seconds to force it off and back on. On a laptop, plug in an external monitor or "
          "shine a torch at the screen - if you can see a faint image, the backlight has failed and "
          "the screen needs replacing.",
          ask=("black", "nothing", "blank", "dark", "still on", "still running"),
          avoid=("phone", "iphone", "android", "tv", "television", "camera", "photo",
                 "dark mode", "night mode", "dark room", "brightness")),
    # A picture that flickers had no answer at all: "my monitor keeps flickering" was the
    # "thanks for telling me" line. It is nearly always the lead, the port or the refresh rate,
    # and a TV adds its own settings on top.
    entry("screen-flickering",
          (("flicker", "flickering", "flickers", "flickered", "flashing", "flashes",
            "blinking", "blinks", "picture keeps"),
           ("screen", "monitor", "display", "laptop", "pc", "computer", "tv", "telly",
            "television", "picture", "hdmi", "second monitor")),
          "A flickering picture is usually the lead or the refresh rate: reseat or swap the HDMI "
          "or DisplayPort cable, try another port at both ends, then set the refresh rate to 60Hz "
          "and update the graphics driver. On a TV, turn motion smoothing off and any eco or "
          "auto-dimming setting. If it flickers the moment the fridge or the heating clicks on, "
          "it is the wiring in the house, not the screen.",
          ask=("flicker", "flickering", "flashing", "blinking", "picture"),
          # a phone that blinks is the notification light's answer, and a flashing light on a
          # car or a boiler is a warning, not a screen
          avoid=("phone", "iphone", "android", "tablet", "mobile", "camera", "photo",
                 "indicator", "warning light", "engine light", "dashboard", "car", "van",
                 "boiler", "alarm", "light is flashing", "lights flashing"),
          bias=2),
    entry("earbuds-disconnecting", (("disconnect", "disconnecting", "disconnects", "drops out",
                                     "dropping out", "keeps cutting out", "cutting out"),
                                    ("earbuds", "airpods", "headphones", "buds", "bluetooth",
                                     "speaker", "car")),
          "Delete the pairing on both sides and pair again from scratch, then keep the phone in a "
          "pocket on the same side as the earbud - a body in the way is the commonest cause of "
          "dropouts. Charge the case fully, and if it only happens in one place, look for a busy "
          "wifi router or a microwave nearby, since both crowd the same radio band.",
          ask=("disconnect", "disconnecting", "drops out", "cutting out", "keeps dropping"),
          avoid=("wifi", "internet", "broadband", "call", "caller", "phone call")),
    entry("laptop-updates", (("update", "updates", "updating", "install updates", "nagging",
                              "keeps asking me to update", "restart to update"),
                             ("laptop", "computer", "pc", "windows", "mac", "macbook", "keeps asking",
                              "asks me", "turn off", "stop", "delay")),
          "Let it install - most of what arrives is security fixes, and the nagging stops once it "
          "is done. Do it when you are plugged in and will not need the machine for half an hour, "
          "and back up first if it is a big numbered upgrade. If it keeps coming back without "
          "finishing, free up some disk space: an update needs about 20GB to unpack.",
          bias=1,
          avoid=("phone", "iphone", "android", "app", "apps", "instagram", "whatsapp", "facebook",
                 "game", "games", "news", "job", "cv", "address", "status",
                 # a person who nags is not a laptop that nags: "how do i stop nagging my
                 # partner" was told to let the update install
                 "my partner", "my husband", "my wife", "my boyfriend", "my girlfriend",
                 "my mum", "my mom", "my dad", "my kids", "my child", "my flatmate",
                 "my friend", "my boss", "people", "someone", "somebody")),
    entry("background-apps", (("background", "background app refresh", "running in the background",
                               "apps running", "background data"),
                              ("stop", "apps", "app", "running", "close", "turn off", "drain",
                               "refresh", "battery", "data")),
          "You do not need to close them: a phone freezes an app the moment you leave it, so "
          "swiping them away actually costs battery, because the next open starts from scratch. "
          "Turn off what really runs in the background instead - Settings > General > Background "
          "App Refresh on an iPhone, Settings > Apps > [app] > Battery > Restricted on Android - "
          "and start with social, video and map apps. Notifications, location set to Always and "
          "auto-sync are the three settings that cost the most.",
          bias=1,
          ask=("background", "apps running", "running in the background"),
          avoid=("laptop", "windows", "computer", "pc", "mac", "startup", "job", "cv")),

    entry("phone-louder", (("louder", "volume", "quiet", "can't hear", "cannot hear", "cant hear",
                            "turn it up", "not loud enough", "muffled", "muffled sound",
                            "tinny", "speaker"),
                           ("phone", "speaker", "music", "calls", "ringtone", "iphone", "android",
                            "podcast", "video")),
          "Push the volume all the way up first - on a phone the media volume and the call volume "
          "are separate, so music can be loud while calls are quiet. Then take the case off and "
          "clean the speaker grille with a dry toothbrush: fluff packed into it is the usual reason "
          "a phone suddenly sounds muffled, and it is worth checking Settings > Sounds for a volume "
          "limit before you pay for a repair.",
          ask=("louder", "volume", "quiet", "hear", "turn it up", "muffled", "speaker"),
          avoid=("tv", "television", "telly", "hearing aid", "tinnitus", "car", "radio",
                 "sound bar", "alexa", "headphones", "earbuds", "airpods")),

    # --- the everyday ones a person meets before any of the above ------------
    # A phone that is asked how to charge, not why it will not: the plug is not in question, the
    # habit is, and "whats the best way to charge a phone battery" used to reach the won't-charge
    # answer and tell the person to clean the port.
    entry("phone-charging-habit", (("charge", "charging", "charger"),
                                   ("best way", "how should i charge", "how often should i charge",
                                    "is it bad to", "is it ok to", "okay to", "bad for the battery",
                                    "battery last longer", "last longer", "80 percent", "overnight",
                                    "all night", "keep it plugged in", "leave it on charge")),
          "Keep it between about 20% and 80% when you can and skip the heat: a phone left on the "
          "charger all night is fine because modern phones stop at full, but a battery kept at "
          "100% and warm ages fastest. Slow charging overnight is kinder than a fast top-up, and "
          "any charger that makes the phone hot is the one to stop using.",
          # the overnight question already has its own answer, and it says the useful thing
          # about heat, so this one stands down for it
          avoid=("wont charge", "won't charge", "not charging", "charges slowly", "charging slow",
                 "laptop", "car", "abroad", "roaming", "hot when charging",
                 "overnight", "all night", "leave it on charge", "leaving it on charge"),
          bias=1),
    entry("ipad-not-charging", (("ipad", "tablet", "kindle", "e reader", "ereader"),
                                ("not charging", "wont charge", "won't charge", "charging slow",
                                 "charges slowly", "charge", "plugged in")),
          "Try the cable and plug you know work on something else, then clean the port out with a "
          "wooden toothpick - a ball of pocket fluff is the usual cause. If the screen says 'Not "
          "charging' while it is plugged in, the cable or the port is failing; if it says nothing, "
          "the charger is. An iPad on a phone charger charges very slowly or not at all, so use the "
          "one it came with.",
          # A night on the charger is a question about the habit, and the port-cleaning answer is
          # for a device that will not take a charge at all: keying bare "charge" on "ipad" gave
          # "how do i stop my ipad charging overnight" a toothpick and a ball of pocket fluff.
          avoid=("overnight", "all night", "stop charging", "keep it charged", "leave it on",
                 "how often", "best way", "last longer", "80 percent", "80%", "bad to charge",
                 "ok to charge", "safe to charge"),
          bias=1),
    # The photos are in iCloud and the person wants the files: the answer is a download, not a
    # sync, and it is not the phone-to-laptop entry.
    entry("photos-off-icloud", (("photos", "pictures", "videos", "photos and videos"),
                                ("off icloud", "from icloud", "out of icloud", "on my laptop",
                                 "to my laptop", "to my pc", "onto my computer", "download",
                                 "downloads", "to a hard drive", "onto a drive", "stop syncing",
                                 "syncing to icloud", "sync to icloud", "uploading")),
          "Sign in at icloud.com/photos on a computer, select the ones you want and press the "
          "download arrow at the top - in batches of a few hundred, or the browser gives up. On a "
          "Mac, select them in Photos and use File > Export > Export Unmodified Original. To stop "
          "new ones uploading, turn off Settings > [your name] > iCloud > Photos on the phone "
          "first.",
          avoid=("wont", "won't", "not syncing", "wont sync", "won't sync", "stopped syncing",
                 "no longer", "storage", "full", "icloud storage", "delete", "deleted", "recover",
                 "lost", "shared album"),
          bias=1),
    # A keyboard symbol, which is one line in the manual and unanswerable from the keys alone.
    # One entry, one answer per symbol: a reply that only knows the pound sign was telling people
    # asking for the euro or the backslash that it was Shift and 3, which is a confident wrong
    # answer, so the symbol named in the line picks the line of the reply.
    entry("typing-a-symbol", (("pound sign", "euro sign", "dollar sign", "at sign", "hash sign",
                               "hash symbol", "backslash", "forward slash", "underscore",
                               "tilde", "degree sign", "pipe symbol", "asterisk"),
                              ("type", "typing", "keyboard", "how do i", "where is", "which key",
                               "cant find", "can't find", "shortcut", "sign")),
          _symbol_on_the_keyboard,
          bias=1),

    entry("mouse-jumping", (("mouse", "trackpad", "pointer", "cursor", "touchpad"),
                            ("jumps", "jumping", "jumpy", "skips", "skipping", "teleports",
                             "moves on its own", "flies", "erratic", "wont stay still",
                             "won't stay still")),
          "Take the surface out of it first: a mouse on glass, gloss or a shiny desk mat reads the "
          "movement wrongly, so put a sheet of paper under it and see if it stops. Then a new "
          "battery in a wireless mouse, the receiver moved out of a USB 3 port and into one on the "
          "front, and a wired mouse tried in the same port - if the wired one is steady, the mouse "
          "or its battery is the fault. On a laptop, a thumb or a wrist brushing the trackpad while "
          "you type is the commonest cause of a cursor that jumps.",
          bias=1),
    # Choosing a printer is a shopping question with a real answer: the ink is the cost.
    entry("choosing-printer", (("printer", "printers", "all in one"),
                               ("best", "good", "recommend", "which", "buy", "buying", "cheap",
                                "cheapest", "for home", "home use", "worth it", "should i get")),
          "For ordinary documents a cheap mono laser is the one to have: about £100, and its toner "
          "costs less per page than inkjet ink and never dries out. An inkjet is the right printer for "
          "photos and colour, but only if you print often enough that the ink does not dry out. "
          "Whatever you pick, work out the cost per page from the cartridge price and its "
          "page count - the cheapest printer is often the most expensive ink.",
          avoid=("not printing", "won't print", "wont print", "jammed", "jam", "offline", "ink",
                 "cartridge", "toner", "connect", "wireless", "setup", "set up", "install",
                 "scan", "queue", "paper"),
          bias=1),
    entry("pdf-to-word", (("pdf", "pdfs"), ("word", "doc", "docx", "editable", "edit it",
                                            "convert", "converter", "type it out")),
          "Open the PDF in Word itself (File > Open, choose the PDF) and it converts it to an "
          "editable document in one step; Google Docs does the same for free - upload it, right "
          "click, Open with > Google Docs, then File > Download > Microsoft Word. Either way a "
          "scanned PDF comes through as a picture, so you need an OCR pass (Google Docs and Adobe "
          "both do it) before any of the text can be typed over.",
          bias=1),
    entry("laptop-asks-password", (("laptop", "computer", "windows", "pc", "macbook"),
                                   ("keeps asking for my password", "asks for my password",
                                    "asking for my password", "asks for a password every time",
                                    "password every time", "wakes and asks", "asks to sign in",
                                    "asks me to sign in", "wont remember me",
                                    "won't remember me")),
          "It is asking after sleep, and that is a setting: on Windows, Settings > Accounts > "
          "Sign-in options > 'If you've been away, when should Windows require you to sign in "
          "again?' and choose Never; on a Mac, System Settings > Lock Screen and turn off 'Require "
          "password after screen saver begins'. If it asks for a password you do not know, that is "
          "the account password, so use the reset link on the sign-in screen rather than guessing.",
          avoid=("forgot", "forgotten", "reset", "locked out", "wifi", "email", "bank", "account"),
          bias=1),
    # Turning the camera off is a privacy setting, not a power one: it used to get the
    # sleep-or-shutdown answer.
    entry("laptop-camera-off", (("camera", "webcam"),
                                ("turn off", "turning off", "switch off", "disable", "cover",
                                 "block", "privacy", "stop it")),
          "On Windows, Settings > Privacy & security > Camera, and switch access off for everything "
          "or just the apps you do not trust. On a Mac it is System Settings > Screen Time > "
          "Content & Privacy. The switch on the machine itself, or a sliding shutter over the lens, "
          "is the surest way of all.",
          avoid=("not working", "wont work", "won't work", "blurry", "blurred", "upside down",
                 "black", "dark", "not showing", "zoom", "teams", "doorbell", "security camera",
                 "dash cam", "traffic")),

    # "what should i name my wifi network" was a shrug. The joke names are also a security
    # question, which is what makes this worth an answer rather than a suggestion.
    entry("wifi-name", (("wifi", "wi-fi", "wireless", "network", "router", "hotspot"),
                        ("name", "named", "naming", "call it", "call my", "call the", "rename",
                         "ssid")),
          ("Something you can say to a guest out loud and still not name the house: a joke, a "
           "film reference, or the flat number with a word after it. Anything with your surname, "
           "the road or the flat number in it tells a stranger where you live, and a name that "
           "looks like a router brand marks you out as the default password, so keep the password "
           "long and random and let the name carry the joke."),
          # the question has to be asking for a suggestion: "what is my dog called" and
          # "whats my cats name" are the memory store's, and it answers them right
          ask=("should i name", "should we name", "should i call", "should we call",
               "what should i name", "what should i call", "what to name", "what could i name",
               "suggest", "ideas", "idea", "any name", "good name", "nice name", "name for my",
               "name my", "help me name", "help me pick", "recommend", "come up with",
               "think of a name", "how do i name", "what would you call"),
          # a network that will not connect, a slow one, and what a name MEANS are other answers
          avoid=("not working", "wont connect", "won't connect", "slow", "dropping", "keeps",
                 "password", "reset", "extend", "mesh", "hidden", "guest network", "5g",
                 "meaning", "mean", "why", "band", "cat", "dog", "boat",
                 # how to change the network's name is the router how-to, not a suggestion:
                 # "how do i rename my wifi router" is printed on a sticker, so `rename` is out
                 # of the ask and every changing word is held out here
                 "rename", "renaming", "renamed", "change the name", "change my wifi",
                 "change the wifi", "change the network", "change my network", "router admin",
                 "192.168"),
          bias=1),
    # --- printing, backing up, and showing someone -------------------------
    entry("print-a-pdf", (("pdf", "pdfs"), ("print", "printing", "print it", "print them")),
          "Open the PDF and press Ctrl and P - Command and P on a Mac - then pick the printer; "
          "File > Print does the same. If you wanted a paper copy turned into a file instead, "
          "choose 'Print to PDF' in the same menu.",
          avoid=("convert", "word", "docx", "editable", "merge", "combine", "split", "sign",
                 "password", "compress", "reduce", "fill", "edit", "scan"),
          bias=1),
    # The phone backup is an iCloud setting most people have never opened, and main shrugged at
    # every wording of it.
    entry("phone-backup", (("iphone", "ipad", "phone"), ("back up", "backup", "backups",
                                                         "back it up", "back them up")),
          "On an iPhone, Settings > [your name] > iCloud > iCloud Backup and turn it on, then "
          "Back Up Now with the phone on wifi and on charge; the date of the last backup is on that "
          "same screen, and Settings > [your name] > iCloud > Manage Account > Backups shows what "
          "each one holds. Plugging it into a computer and opening Finder, or iTunes on an older "
          "machine, makes the same backup on the computer instead of in iCloud.",
          # the photos answer is its own entry, and "back up the photos on my phone" is its line
          avoid=("restore", "transfer", "move to", "whatsapp", "photos to", "icloud storage",
                 "not enough", "full", "delete", "recover", "deleted", "photo", "photos",
                 "picture", "pictures", "images", "camera roll"),
          bias=1),
    entry("share-phone-screen", (("screen", "display"), ("share", "sharing", "mirror", "mirroring",
                                                         "cast", "screencast")),
          "On an iPhone, Screen Mirroring in Control Centre sends the screen to a smart TV, and in "
          "a FaceTime or WhatsApp call the share button does it inside the call. On Android it is "
          "Cast or Smart View in the quick settings, and Zoom, Teams and Meet each have Share "
          "Screen once you are in a meeting.",
          ask=("how", "can i", "want to", "help me"),
          avoid=("zoom", "teams", "meet", "facetime", "whatsapp", "video call", "in a call",
                 "on a call"),
          bias=1),
    # Two small screens-and-sound settings that main met with a shrug or the wrong answer.
    entry("make-things-bigger", (("zoom in", "zoom out", "too small", "too big", "text size",
                                  "make the text bigger", "make the writing bigger", "magnify",
                                  "screen is too small", "cant read"),
                                 ("how do i", "laptop", "computer", "desktop", "browser",
                                  "windows", "mac", "word", "excel", "screen")),
          "In a browser or a document, Ctrl and + makes it bigger and Ctrl and - smaller, and Ctrl "
          "and 0 puts it back to normal; on a Mac it is Command and those keys. To change the size "
          "of everything on the machine, Windows has Settings > Accessibility > Text size and a Mac "
          "has System Settings > Accessibility > Display > Text size.",
          avoid=("camera", "photo", "video call", "meeting", "teams", "telescope", "binoculars",
                 "phone", "iphone", "android", "ipad", "tablet", "tv",
                 # "a pill thats too big to swallow" is a size word in a mouth, not a screen
                 "pill", "pills", "capsule", "capsules", "swallow", "swallowing",
                 # a file that is too big to send is a file question, not a zoom one: the word
                 # "bigger" is not in the line, only "too big", and "how do i" is in the ask.
                 "file", "files", "email", "attach", "attached", "attachment", "send",
                 "upload", "pdf", "video file", "photo file", "zip"),
          # the second group above is the asking words, and "how do i" is one of them, so a
          # line with no screen in it still scored on "too small": a shoe that is too small
          # was told Ctrl and + makes it bigger. The guard asks for the thing the card is
          # about, so the card is a screen card again.
          bias=1, guard=_a_screen_is_named),

    entry("tv-sound-out-of-sync", (("tv", "telly", "television", "soundbar", "sound bar"),
                                   ("out of sync", "lip sync", "lips", "delay", "behind the picture",
                                    "sound is behind", "sound and picture", "audio sync",
                                    "out of time")),
          "Sound running behind the picture is a setting, not a fault: find Audio Delay, Digital "
          "Audio Delay or Lip Sync in the TV's sound menu and add 50 to 100 milliseconds until the "
          "lips match. A soundbar or a Bluetooth speaker adds the most delay, and its own A/V Sync "
          "setting takes the rest out.",
          bias=1),
    entry("smoke-alarm-battery", (("smoke alarm", "smoke detector", "carbon monoxide alarm",
                                   "co alarm", "fire alarm"),
                                  ("battery", "batteries", "change", "replace", "beeping", "chirp",
                                   "chirping", "keeps going off")),
          "A chirp every minute or so is the low-battery warning: twist the alarm off its base, "
          "swap the battery (usually a 9V, sometimes AA) and press the test button until it sounds "
          "properly. Mains-powered alarms have a backup cell that does the same thing, and any "
          "alarm over ten years old wants replacing whole rather than mending.",
          # "keeps going off when i cook" met "keeps going off" here and got a flat-battery answer
          # about an alarm that was working perfectly. The cooking words stand this down so the
          # nuisance entry in home.py (smoke-alarm-nuisance) answers a badly placed sensor.
          avoid=("cook", "cooking", "cooked", "toast", "toasting", "grill", "grilling",
                 "oven", "hob", "fry", "frying", "roast", "roasting", "bake", "baking",
                 "shower", "steam", "kitchen"),
          bias=1),
    entry("tv-slow-to-change", (("tv", "telly", "television", "freeview", "sky box", "virgin box",
                                 "set top box"),
                                ("slow to change", "slow changing", "channels change slowly",
                                 "changing channels", "channel changes", "slow channel",
                                 "takes ages to change", "laggy menus")),
          # "my tv remote wont change channels" is the remote's own row: this one is the box
          # being slow when the buttons do work
          "Restart the box or the set at the wall and leave it a minute - a slow channel change is "
          "nearly always the software in the set-top box rather than the aerial. If the menus are "
          "slow too, free up the set's storage and uninstall apps you do not use; a retune is worth "
          "one go if only some channels are slow.",
          bias=1,
          avoid=("remote", "remote control", "zapper", "batteries", "battery", "wont work",
                 "will not work", "not working", "nothing happens")),
    # A picture that has gone funny is the set's own question, and nothing had it: "the picture
    # on the telly has gone funny" reached the *phone photo* answer, because "pictures" and
    # "gone" are that entry's key, and "the colour has gone on my tv" reached tonight's listings.
    # The telly words have to be in the line, because a phone screen has a picture too.
    entry("tv-picture", (("picture", "pictures", "colour", "color", "colours", "colors",
                          "image", "display", "screen", "tv", "telly", "television",
                          # the box is named without the screen as often as with it: "my sky box
                          # has gone funny" and "the sky box keeps going blank" both matched no
                          # subject word and punted (the second to a habit card).
                          "sky box", "sky tv", "sky q", "freeview box", "set top box",
                          "virgin box", "youview box"),
                         # no bare "sky" here either: the satellite service is "sky box" or
                         # "sky tv", and a bare "sky" is the sky outside, which belongs to
                         # science. "sky tv is too expensive can i cancel" is a bill and the
                         # cancel-subscription row has it.
                         ("tv", "telly", "television", "freeview", "sky box", "aerial",
                          "hdmi", "flicker", "flickers", "flickering", "blank", "fuzzy",
                          "grainy", "tint", "patchy", "blocks", "blocky", "pixelated",
                          "breaking up", "lines", "band", "banding", "snow", "quality",
                          "gone funny", "goes funny", "went funny", "keeps going blank",
                          "went dark", "gone dark", "gone green", "gone pink",
                          "black and white", "no colour", "no color")),
          "One channel going funny is the aerial or the box, and every channel is the set: push "
          "the aerial lead and the HDMI lead back in at both ends, then press Source and pick the "
          "socket the box is in. A lost colour or a green or pink tint is the picture mode, so "
          "reset it in Settings > Picture and check Colour is not at zero. A blotch, a band or a "
          "line that stays in the same place on every channel is the panel, so get a quote before "
          "you decide.",
          # no bare "sky": the satellite service is "sky box" or "sky tv", and the bare word is
          # the one in the line "what colour is the sky", which satisfied this row's key
          # ("picture", "colour") and its ask, and took the question off science's sky card.
          # noble-flute measured it in #understanding 68795: 2 gains, 0 losses.
          ask=("tv", "telly", "television", "freeview", "sky box", "sky tv", "smart tv", "aerial",
               "hdmi"),
          # the phone's photos, a phone screen and tonight's listings are other answers
          avoid=("phone", "iphone", "android", "mobile", "handset", "photos", "photo", "camera",
                 "bin", "deleted", "restore", "recover", "album", "whatsapp", "screenshot",
                 "wallpaper", "laptop", "monitor", "computer", "projector", "tonight",
                 "listings", "series", "film", "netflix", "sound", "out of sync", "remote",
                 # a bill is not a picture: "sky tv is too expensive can i cancel" was answered
                 # with an aerial lead here, and `cancel-subscription` owns it
                 "cancel", "cancelling", "expensive", "too much", "bill", "bills", "package",
                 "subscription", "contract", "cheaper", "cost", "price", "deal",
                 # the glass in front of the picture is a cleaning job: "my tv screen has marks"
                 # was answered with the aerial lead and the HDMI socket
                 "mark", "marks", "smudge", "smudges", "fingerprint", "fingerprints", "dirty",
                 "dusty", "clean", "cleaning", "wipe", "dust"),
          bias=1),
    # A retune is its own job, and it was a shrug: "how do i retune my tv", "the channels have
    # gone" and "i cant find bbc1" all want the same four steps.
    entry("tv-retune", (("channels", "channel", "retune", "retuning", "tune", "tuning",
                         "auto tune", "autotune", "missing channels", "bbc1", "bbc 1", "bbc2",
                         "itv", "channel 4", "channel 5"),
                        ("tv", "telly", "television", "freeview", "sky box", "virgin box",
                         "aerial", "retune", "retuning", "tuning", "lost", "gone",
                         "disappeared", "missing", "wont find", "cannot find", "cant find",
                         "moved", "number changed", "no channels")),
          "Retune from the set's own menu: Settings > Channels > Auto tuning on most sets, and "
          "on a Freeview or Sky box from its own menu instead - the box is the one to retune if "
          "the set's channels are fine. Push the aerial lead back in at both ends first, and "
          "retune again a day later after transmitter work. Channels that moved number or "
          "vanished overnight are a retune, not a broken aerial.",
          ask=("tv", "telly", "television", "freeview", "sky", "sky box", "virgin box",
               "aerial", "bbc1", "bbc 1", "bbc2", "itv", "channel 4", "channel 5"),
          avoid=("netflix", "iplayer", "youtube", "streaming", "subscription", "record",
                 "recording", "series link", "parental", "pin", "password", "volume", "sound",
                 "picture", "signal", "no signal", "slow", "laggy", "app", "apps", "delete",
                 # "my tv remote wont change channels" is the remote, not a missing channel
                 "remote", "remote control", "zapper", "batteries", "battery", "wont change",
                 "will not change", "not working", "nothing happens"),
          bias=2),
    # iPads only: a generic "tablet" is as likely to be Android, and the steps below are Apple's.
    entry("ipad-slow", (("ipad", "ipad pro", "ipad air"), ("slow", "sluggish", "laggy",
                                                           "takes ages", "taking ages",
                                                           "running slow", "very slow")),
          "Restart it first, then clear space: Settings > General > iPad Storage lists what is "
          "taking the room, and an iPad with almost no free space slows down badly. After that, "
          "Settings > General > Software Update - and if it is an old one on the newest system, "
          "that is usually the honest reason.",
          avoid=("phone", "iphone", "laptop", "mac", "wifi", "internet", "charging", "battery"),
          bias=1),

    # --- the four in the house that are not quite a phone or a laptop ---------
    # A thermostat is the one thing in the house with a schedule inside it, and this row is the
    # one question about it that is not a temperature: how to get the schedule back to normal.
    # It used to take every "how do I set the thermostat" line as well, because "set", "change",
    # "schedule" and "clock" were in the key - so "what temperature should I set my thermostat
    # to" was answered with a pinhole reset, and the temperature the person asked for was never
    # said. Setting one is home.py's heating-temperature row; this is the reset only.
    entry("thermostat-schedule", (("thermostat", "heating controls", "heating schedule", "hive",
                                   "nest", "tado", "boiler timer", "timer on the boiler"),
                                  ("reset", "resetting", "reprogram", "reprogramme", "factory",
                                   "put it back", "back to normal", "keeps resetting",
                                   "lost its schedule", "schedule has gone", "gone wrong",
                                   "wrong times", "wrong schedule", "stuck on",
                                   "wont go back", "won't go back")),
          "Find the model number on the inside of the flap and look up its reset - on most Hive and "
          "Nest units that is a pinhole or a menu option that puts the schedule back to the factory "
          "one, and then you set the times again from the app, which is much easier than on the "
          "unit. Before you reset, note the two numbers you actually care about: the times you get "
          "up and go to bed, and 18 to 20C while you are in.",
          avoid=("boiler", "pressure", "radiator", "fault", "not heating", "cold", "error",
                 "car", "engine", "oven", "fridge", "freezer", "shower", "immersion"),
          bias=1),
    entry("vacuum-filter", (("hoover", "vacuum", "vacuum cleaner", "henry", "dyson", "filter"),
                            ("clean", "cleaning", "wash", "replace", "change", "blocked", "smell",
                             "smells", "how often")),
          _vacuum_filter_reply,
          # "no suction" already has a fuller answer of its own (the air path, the hose, the bag)
          # A washing machine, a dishwasher and a tumble dryer all have a filter and none of them
          # is the vacuum's: "washing machine filter is blocked" was washed out under the tap.
          # the floor and the carpet are what the vacuum is pushed over, not its filter: "how
          # often should i vacuum the carpets" is a question about the room, and cleaning.py's
          # floor-often answers it.
          avoid=("robot", "car", "pool", "carpet cleaner", "buy", "which", "best", "price",
                 "floor", "floors", "carpet", "carpets", "rug", "rugs",
                 "cheap", "suction", "no suction", "not picking up", "wont pick up", "lost power",
                 "washing machine", "washer", "washing mashine", "dishwasher", "dish washer",
                 "tumble dryer", "tumble drier", "dryer", "extractor", "cooker hood",
                 "fridge", "freezer", "pond", "aquarium", "fish tank", "caravan",
                 "coffee machine", "water filter", "kettle", "shower", "tap"),
          bias=1),
    # Photos are the one thing people ask to get back rather than to set up.
    entry("recover-photos", (("photos", "pictures", "videos", "images"),
                             ("get back", "got back", "back", "recover", "recover deleted",
                              "deleted", "lost", "missing", "gone", "disappeared", "restore")),
          "Check the bin first: on an iPhone it is Photos > Albums > Recently Deleted, where "
          "deleted photos sit for 30 days, and on Android it is Google Photos > Library > Bin, for "
          "60 days. If they are gone from there, iCloud.com or Google Photos on a browser will show "
          "anything still in the cloud, and a backup from before the loss is the last resort.",
          avoid=("off icloud", "turn off", "stop syncing", "storage", "share", "print", "edit",
                 "crop", "old phone", "new phone", "transfer", "move to", "back up", "backup",
                 "back them up", "onto my phone", "back on my phone", "to my laptop",
                 # a picture on the telly is not a photograph on a phone: "the picture on the
                 # telly has gone funny" was answered with the deleted-photos bin
                 "telly", "television", "tv", "freeview", "aerial", "hdmi", "sky box",
                 "colour", "color", "flicker", "flickering", "blank"),
          bias=1),
    # A device passcode is not an account password: there is no link to click, and the honest
    # answer includes the wipe.
    entry("forgot-device-passcode", (("passcode", "screen password", "lock screen", "pin",
                                      "face id", "unlock"),
                                     ("forgot", "forgotten", "forget", "forgetting",
                                      "locked out", "doesnt work", "does not work",
                                      "wont accept", "wrong", "cant remember",
                                      "cannot remember", "dont know")),
          "There is no way to read the passcode back, so the device has to be wiped and set up "
          "again - but a backup makes that painless. On an iPhone or iPad, put it in recovery mode "
          "and use Finder or Apple Devices on a computer to restore it, then restore the backup; if "
          "Find My was on you may need your Apple ID password first. On Android, use Find My Device "
          "to erase it, then sign back in.",
          avoid=("wifi", "email", "bank", "facebook", "instagram", "account", "website", "login",
                 "log in", "sim"),
          bias=2),
    # --- a part to fit, a card to put on a phone, a car to charge ----------
    # "how do i change the battery in my watch" was getting the science entry about how a cell
    # works, because the word "battery" was the whole of that key.
    entry("watch-battery", (("watch", "watches", "wristwatch", "strap", "watchmaker"),
                            ("battery", "batteries", "change", "replace", "dead", "flat", "stopped",
                             "not working", "runs down",
                             # "the battery in my watch keeps dying" was answered with the phone's
                             # background apps, and a watch battery that dies is this coin cell
                             "dying", "dies", "keeps dying")),
          "A watch battery is a coin cell, usually a CR2016, CR2025 or CR2032 printed inside the "
          "back, and the number matters: a jeweller will fit the right one for a few pounds, and "
          "many watch shops do it while you wait. Doing it yourself needs a case-back tool, and a "
          "watch with a screw-down back or any water resistance is worth leaving to them, because "
          "the seal has to go back clean or it will fog up.",
          # a strap is not a cell: "how do i change my watch strap" was a battery question
          avoid=("phone", "iphone", "laptop", "car", "van", "smoke", "alarm", "charging",
                 "how does", "how do batteries", "strap", "straps", "band", "bands",
                 "bracelet", "leather", "metal",
                 # "i stopped watching it last week" is the news, not a timepiece: "watching"
                 # carries the key word "watch" and "stopped" is a battery word.
                 "watching it", "watching the", "watch the news",
                 # "how do i stop watching tv at night" is a night question, not a timepiece:
                 # "watching" carries the key word "watch". The bare verb cannot be the fence -
                 # an avoid phrase is read loosely, so "watching" alone also stood down "my
                 # watch has stopped" and "how do i change my watch battery" - so the fence is
                 # the verb with the thing being watched after it.
                 "watching tv", "watching the tv", "watching television", "watching telly",
                 "watching netflix", "watching films", "watching a film", "watching youtube",
                 "watch tv", "watch television", "watch telly", "watch netflix"),
          bias=1),
    # "how do i set up a new bank card on my phone" was answering with the age a child should
    # have a phone, because "phone" plus "set up" is that entry's key.
    entry("card-on-a-phone", (("card", "credit card", "debit card", "bank card",
                               "pay with my phone", "pay by phone", "phone in a shop",
                               "tap and pay", "pay on my phone", "contactless", "wallet",
                               # "how do i set up apple pay" named the thing and no card, so it
                               # was the search hedge on main: the wallet's own name is the
                               # clearest thing in the line.
                               "apple pay", "google pay", "mobile wallet",
                               # the wallet is already set up and the payment fails: same row,
                               # and the words that say it are the phone's, not the bank's
                               "wont tap", "won't tap", "doesnt tap", "doesn't tap",
                               "not tapping", "wont pay", "won't pay", "cant pay", "can't pay",
                               "not accepted",
                               # the shop refusing the card, said the way people say it: the
                               # words are the till's, and the row needs one of them because
                               # "pay" is not in "my card was rejected at the till"
                               "was refused", "got refused", "was rejected", "got rejected",
                               "is not accepted", "was not accepted",
                               # "my card doesnt work in the shop" tied with the consumer row
                               # and lost, so it was told faulty goods are the retailer's problem
                               "doesnt work", "doesn't work", "not working", "stops working"),
                              ("on my phone", "to my phone", "apple pay", "google pay",
                               "contactless", "wallet", "tap to pay", "add", "with my phone",
                               "in a shop", "in the shop", "at the till", "at a till",
                               "in a till", "card machine", "at the checkout", "in the checkout",
                               "pay", "tap", "wont work", "won't work")),
          _card_on_a_phone,
          ask=("how", "add", "set up", "setup", "can i", "want to", "use", "pay", "tap",
               "wont", "won't", "doesnt", "doesn't", "not working", "contactless", "wallet",
               # "my card is not accepted in the shop" is the same question as "wont work", and
               # none of the words above are in it, so it fell through to the echo.
               "accepted", "not accepted", "refused", "rejected", "says no", "error"),
          avoid=("child", "kid", "kids", "son", "daughter", "teenager", "cancel", "lost",
                 # "where did i put my wallet, i had it in the shop" is a lost thing, not a
                 # payment, and the shop words below gave it the add-it-to-the-wallet answer
                 "where did i put", "where is my", "where's my", "cant find", "cannot find",
                 "missing", "left it", "left my wallet", "dropped",
                 "add money", "top up", "topup", "load", "balance", "spend", "limit",
                 "a new card", "new card", "first card", "open an account", "bank account",
                 "stolen", "fraud", "scam", "blocked", "declined", "interest", "overdraft",
                 "balance", "loan", "credit score",
                 # The kitchen tap is not a way to pay. The row keys "tap" for "my phone wont
                 # tap", so "the tap is not working" and "the tap doesnt work" were told to check
                 # the phone's screen and its case. A tap with water in it is the plumber's tap,
                 # and the phrase is what tells the two apart without taking "tap" out of the key.
                 # phrases about the fitting, never the bare "tap": "the tap to pay doesnt work"
                 # is still this row's line, and "the tap is not working" is the plumber's
                 "kitchen tap", "bathroom tap", "hot tap", "cold tap", "mixer tap",
                 "tap is", "tap drips", "tap leaks", "tap water", "running tap",
                 "tap doesnt", "tap doesn't", "tap stopped", "tap wont", "tap won't",
                 "faucet", "shower", "loo", "toilet", "cistern", "radiator", "sink", "bath",
                 # "should i pay off my credit card or save" was getting the add-to-wallet
                 # answer, because the row keys "pay" and "card" and the question is about the
                 # debt: paying a card off is money.py's `overpay` row
                 "pay off", "paying off", "paid off", "pay mine off", "paying the minimum",
                 # "cant pay" is the wallet's when the person is at a till, and the debt's when
                 # they cannot meet the month: "i cant pay my credit card this month" was told
                 # to check the screen is unlocked and NFC is on.
                 "this month", "next month", "last month", "afford", "cant afford",
                 "struggling", "behind on", "missed a payment", "miss a payment",
                 "overdraft", "maxed", "interest", "minimum", "payment plan",
                 "payment", "manage",
                 "owe", "owes", "owing", "owed", "debt", "debts", "repay", "repaying",
                 # "wont pay" and "cant pay" are the wallet's only when the thing at the till is
                 # the card's to pay. Money a person owes a person is not paid by tapping a
                 # phone, and it is never the bank's card at fault: "my tenant wont pay rent"
                 # and "my ex partner wont pay the mortgage" were both told to check the screen
                 # was unlocked and NFC was switched on.
                 "tenant", "tenants", "landlord", "landlords", "rent", "rents",
                 "mortgage", "mortgages", "arrears",
                 "minimum payment", "monthly payment", "statement", "apr",
                 # "pay my credit card off" has "card off" in it, not "pay off", so it kept
                 # the wallet answer until the phrase went in whole
                 "pay my card off", "pay the card off", "pay my credit card off",
                 "pay my debit card off", "pay it off", "paid it off", "paying it off",
                 "pay them off", "repayment", "installments", "instalments",
                 "only the minimum", "just the minimum",
                 # and the save-or-pay question, which is a debt question with a savings word
                 "or save", "or saving", "than saving", "instead of saving", "overpay",
                 "credit card debt", "card debt", "clear the balance", "clear my balance"),
          bias=1, guard=_a_wallet_is_named),
    # A boarding pass is a printing question with a right answer: it is in the app, and paper is
    # a fallback rather than the first step.
    entry("boarding-pass", (("boarding pass", "boarding card", "boarding passes"),
                            ("print", "printing", "home", "at home", "paper", "download",
                             "where", "get", "show")),
          "Check in on the airline's app or website 24 to 48 hours before the flight and the pass "
          "appears there with a QR code - that is all most airports need, and it updates itself if "
          "the gate changes. Print it at home only if you would rather have paper or your phone "
          "battery is a worry, and the airport kiosks will print one either way.",
          bias=1),
    entry("ev-charging-home", (("electric car", "ev", "electric vehicle", "plug in hybrid"),
                               ("charge", "charging", "charger", "charge at home", "charge it at home",
                                "home charger", "install a charger", "charging point")),
          "A 7kW home charger tops a typical electric car up overnight, needs a qualified "
          "installer and a dedicated circuit, and costs roughly £800 to £1,200 fitted before any "
          "grant your country offers. A three-pin plug works but adds only about 8 to 10 miles an "
          "hour, so it suits a small daily mileage; an off-peak electricity tariff is what makes "
          "home charging cheap, so set the car to charge overnight.",
          # the cost of charging is a running cost, not the cost of having a charger fitted
          avoid=("abroad", "motorway", "public charger", "charging point near", "tesla",
                 "battery health", "range", "hybrid car worth", "lease", "buy",
                 "cost to charge", "cost of charging", "charging cost", "expensive to charge",
                 "cheap to charge", "how much is charging", "cost per mile", "pence per mile"),
          bias=1),
    entry("doorbell-camera-dead", (("doorbell", "ring doorbell", "video doorbell",
                                    "doorbell camera", "door camera"),
                                   ("not working", "wont work", "won't work", "offline", "no power",
                                    "dead", "not connecting", "no video", "black", "stopped",
                                    "not showing")),
          "A doorbell camera that drops off is nearly always the wifi: check the signal at the "
          "door with a phone, and if it is weak, move the router or add a mesh point rather than "
          "buying a new bell. Then charge or change its battery, since a low one cuts the video "
          "first, and power-cycle the chime - most of them rejoin the network within a minute.",
          # an ordinary doorbell is a chime and a button, and this answer would be nonsense for
          # it, so the line has to say it is the camera one
          ask=("camera", "video", "ring", "app", "wifi", "footage", "motion", "notification"),
          avoid=("chime", "chimes", "bell", "bells", "buzzer", "wired doorbell", "door bell",
                 "button"),
          bias=1),
    # --- the small jobs a person meets on the first day with a new machine ----------
    # A ringtone is a call, an alarm is a wake-up: same word "sound", two menus, so the two
    # entries refuse each other's words rather than one key covering both.
    entry("phone-ringtone", (("ringtone", "ring tone", "text tone", "text alert",
                              "notification sound", "sound it makes when", "sound my phone makes"),
                             ("change", "set", "different", "custom", "my own", "song", "tune",
                              "iphone", "android", "phone", "quiet")),
          "On an iPhone it is Settings > Sounds & Haptics > Ringtone (and Text Tone for messages), "
          "where Tone Store buys one and a song you own can be used for a pound or so. On Android "
          "it is Settings > Sound and vibration > Phone ringtone, and a music app can usually set "
          "any track as the ringtone from its own menu.",
          avoid=("alarm", "wake", "sleep", "smoke", "fire", "burglar", "carbon monoxide",
                 "not loud", "cant hear", "can't hear", "muffled", "vibrate", "silent mode",
                 "louder", "volume", "too quiet"),
          bias=1),
    entry("alarm-sound", (("alarm", "alarm clock", "wake me up", "wake up in the morning",
                           "waking up"),
                          ("sound", "song", "ringtone", "tune", "different", "change", "set",
                           "gentle", "quiet", "loud", "radio")),
          "In the Clock app, edit the alarm and tap Sound (iPhone) or the bell icon (Android) - on "
          "an iPhone the list ends with Pick a Song, which uses anything in your library, and on "
          "Android there is usually a plus sign to add a file. Start quiet and put the phone across "
          "the room: a gentle sound you have to get up to stop wakes you better than a loud one by "
          "the bed.",
          avoid=("smoke", "fire", "burglar", "carbon monoxide", "co alarm", "car", "house alarm",
                 "not going off", "keeps going off", "beep"),
          ask=("sound", "sounds", "song", "tune", "ringtone", "tone", "music", "bell", "gentle"),
          bias=1),
    # A file, not a jacket: clothing.py's stuck-zip owns the zipper on clothes.
    # The sound of an alarm and setting one are two answers: the sound entry is gated on a sound
    # word, so a plain "how do i set an alarm" lands here (bronze-whistle, #2434).
    entry("set-alarm", (("set an alarm", "set my alarm", "set a alarm", "alarm for", "wake me up at",
                         "wake up at", "wake up alarm", "alarm clock"),
                        ("set", "setting", "am", "pm", "clock", "phone", "iphone", "android",
                         "tomorrow", "morning", "how")),
          "Open the Clock app, tap the plus sign (Alarm > Add on Android), pick the time and the "
          "days and save. Check the alarm volume is up, since most phones use a separate alarm "
          "volume, and leave the phone off silent mode if the alarm still does not sound.",
          ask=("alarm", "am", "pm", "clock", "wake", "7", "6", "8", "5", "9", "10", "11", "4",
               "30", "morning", "tomorrow", "early"),
          avoid=("sound", "sounds", "song", "tune", "ringtone", "tone", "music", "gentle",
                 "smoke", "fire", "burglar", "carbon monoxide", "co alarm", "car", "house alarm",
                 "not going off", "keeps going off", "beep", "went off", "didnt go off",
                 "didn't go off", "snooze", "echo", "alexa", "watch", "fitbit", "nest",
                 # "how do i stop my phone waking me up at night" is the notifications
                 # question: "wake me up at" is a phrase of this key and "at night" is not an
                 # alarm time. The alarm key keeps the clock times and loses the sleep lines.
                 "waking me up", "waking me", "keep waking", "keeps waking", "stop my phone",
                 "notifications", "notification", "at night", "night", "nights", "buzzing",
                 "google home", "laptop", "computer", "pc", "speaker", "minute", "minutes",
                 "what time should",
                 # somebody who already wakes at five has a sleep question, not an alarm to
                 # set: "i wake up at 5 every morning" was told to open the Clock app
                 "i wake up at", "i wake at", "i keep waking", "keep waking up",
                 "i always wake", "i woke up at"),
          guard=_a_request_to_be_woken,
          bias=1),
    # "does my alarm work on silent" is a yes or no about the alarm, not a request to set one and
    # not a phone that will not ring: the silent switch mutes the ringer and the alarm has its own
    # volume. Its own row, because the set-alarm steps are not the answer to a question.
    entry("alarm-on-silent", (("alarm", "alarms", "alarm clock"),
                              ("on silent", "in silent mode", "silent mode", "silent switch",
                               "silent", "do not disturb", "muted", "mute")),
          "Yes, on a phone with a separate alarm volume the alarm still sounds on silent - the "
          "silent switch mutes the ringer, not the alarm. Two things defeat it: the alarm volume "
          "itself turned down (on an iPhone it follows the ringer volume, so raise that with the "
          "alarm screen open), and Do Not Disturb with alarms allowed off, which is a setting in "
          "Focus. Check both tonight by setting an alarm two minutes ahead.",
          ask=("alarm", "alarms", "silent", "mute", "muted"),
          avoid=("smoke", "fire", "burglar", "carbon monoxide", "co alarm", "car",
                 "house alarm", "not going off", "keeps going off", "set an alarm",
                 "set my alarm", "set a alarm", "wake me up", "wake up at", "sound")),
    entry("zip-file", (("zip", "zip file", "zipped", "unzip", "unzipped", "rar", "7z",
                        "compressed", "compress"),
                       ("file", "files", "folder", "document", "documents", "download", "email",
                        "attachment", "send", "open", "how", "cant", "can't")),
          "A zip is one file holding several. To open one, double-click it: Windows and macOS both "
          "unpack it into a folder beside it, no software needed. To make one on Windows, "
          "right-click the folder > Send to > Compressed (zipped) folder; on a Mac, right-click > "
          "Compress. A .rar or .7z needs a free app such as 7-Zip.",
          avoid=("zipper", "jacket", "coat", "trousers", "dress", "boots", "bag", "tent",
                 "sleeping bag", "hoodie", "zip a folder", "zip a file", "zip up", "make a zip",
                 "create a zip", "make a zip file", "too big to email", "compress a folder",
                 # "how does a zip work" is the fastener on a coat, not the archive: the file
                 # row took it because the clothing words were spelled out but the mechanism
                 # ones were not, and there is now a row that explains the fastener. Whole
                 # phrases only - "open a zip file" and "unzip this folder" keep this row, and
                 # a bare "file" in the avoid list took them away.
                 "how does a zip work", "how do zips work", "how a zip works",
                 "how does a zipper work", "how do zippers work", "zip on a",
                 "zip on my", "fastener", "coat zip", "jacket zip",
                 # a slider to replace and a zip that will not do up are the fastener too:
                 # "how do i put a new slider on a zip" was answered with how to open a zip file
                 "slider", "zip slider", "new zip", "replace the zip", "replace a zip",
                 "skirt", "wardrobe", "quilt", "duvet cover", "fly of my jeans",
                 # "how do i unjam my zip" reached this row through `zip` and `how`, and the
                 # clothing row was not asked, because its fault words are "stuck" and
                 # "jammed" and the line says neither. A zip that will not move is the
                 # fastener whatever verb the person chose, so the verbs leave this row.
                 "unjam", "unjamming", "unstick", "unsticking", "jammed", "jams",
                 "un-jam",
                 # a needle is not an archive: "how do i sew a zip in" and "how do i stop a zip
                 # coming undone" were both answered with how to unpack a .zip file, because a
                 # bare "how" and a bare "zip" were enough for this row
                 "sew", "sewing", "sewn", "stitch", "stitching", "unpick", "baste", "tack",
                 "zip foot", "fabric", "hem", "seam", "needle", "thread", "tailor",
                 "dressmaking", "coming undone", "comes undone", "keeps coming down",
                 "slides down", "wont stay up", "won't stay up",
                 # a zip fly is the trouser opening, not a compressed file: "how do i put a zip
                 # fly in" got the double-click that unpacks a .zip
                 "zip fly"),
          bias=1),
    # One entry for opening a zip, one for making one: "how do i zip a folder" was answered with
    # the double-click that unpacks it, which is the other job (bronze-whistle, #2434).
    entry("zip-a-folder", (("zip a folder", "zip a file", "zip up", "make a zip", "create a zip",
                            "make a zip file", "too big to email", "compress a folder"),
                           ("zip", "folder", "folders", "file", "files", "email", "send",
                            "attachment", "compress", "how")),
          "Right-click the folder > Send to > Compressed (zipped) folder on Windows, or right-click "
          "> Compress on a Mac, and a single .zip file appears beside it to attach to the email. "
          "Photos and videos shrink a lot, documents barely change, and an email usually stops "
          "around 20 to 25MB, so a big video needs a transfer link instead.",
          avoid=("zipper", "jacket", "coat", "trousers", "dress", "boots", "bag", "tent",
                 "sleeping bag", "hoodie"),
          bias=1),
    entry("qr-code", (("qr code", "qr codes", "scan a code", "square code"),
                      ("scan", "how", "read", "open", "camera", "menu", "phone", "restaurant",
                       "ticket", "pay")),
          "Point the camera app at it and hold still for a second - a link or a menu button pops "
          "up on the screen and you tap it; there is nothing to install. If nothing happens, the "
          "code is too close or too dark, so move back a little and add light. Treat a code on a "
          "parking meter or a sticker as suspect: a real one is printed, not stuck over.",
          bias=1),
    entry("second-monitor", (("second monitor", "second screen", "two screens", "another monitor",
                              "external monitor", "second display", "extend my screen"),
                             ("set up", "setup", "connect", "use", "laptop", "pc", "windows",
                              "mac", "macbook", "hdmi", "screen", "work")),
          "Plug it in with HDMI or USB-C and it usually just works; then press Windows key + P to "
          "choose Extend, which gives you two separate screens rather than a copy. On a Mac it is "
          "System Settings > Displays > Arrange, and the menu bar follows whichever screen you drag "
          "the white bar to. If nothing appears, try the other port and a different cable before "
          "blaming the monitor.",
          avoid=("cracked", "broken", "black", "flickering", "flicker", "dim", "fuzzy", "blurry",
                 "not turning on", "no signal", "tv", "telly"),
          bias=1),
    entry("mac-right-click", (("right click", "right-click", "secondary click"),
                              ("mac", "macbook", "trackpad", "apple", "laptop", "mouse")),
          "Two fingers on the trackpad and press, or hold Control and click: both give the "
          "right-click menu on a Mac. A two-button mouse works as it always did. To make tapping "
          "with two fingers enough on its own, turn on System Settings > Trackpad > Secondary click.",
          avoid=("copy", "paste", "windows", "phone", "ipad", "word", "excel"),
          bias=1),
    entry("mac-copy-paste", (("copy and paste", "copy paste", "cut and paste", "paste",
                              "copy something"),
                             ("mac", "macbook", "apple", "keyboard", "command", "shortcut")),
          "Command-C copies, Command-V pastes and Command-X cuts - the Command key sits either "
          "side of the space bar, where Control is on a Windows keyboard. In a Mac app the same "
          "commands are under the Edit menu if you would rather click.",
          avoid=("windows", "phone", "ipad", "iphone", "web page", "website", "text from"),
          bias=1),
    # `ask` keeps this off "how do i block a number" and the spam entries: a website is the object.
    entry("block-website", (("block", "blocked", "blocking", "unblock"),
                            ("website", "websites", "site", "sites", "web address", "internet")),
          "On a computer, put the address in the hosts file or use the router's parental controls "
          "so it covers every device in the house; a free filter such as Cloudflare's 1.1.1.1 for "
          "Families does it in one setting. On a phone, Screen Time (iPhone) or Digital Wellbeing "
          "(Android) blocks sites by name, and a browser extension does it for one browser only.",
          ask=("website", "websites", "site", "sites", "web address", "internet", "online"),
          avoid=("number", "numbers", "call", "calls", "text", "texts", "spam", "sender",
                 "contact", "email address", "someone", "ex", "person", "drain", "sink", "toilet",
                 "chimney", "road", "drive", "door"),
          bias=1),
    # --- the everyday machine jobs people ask about, second batch ------------------------
    entry("screenshot-any",
          (("screenshot", "screen shot", "screen grab", "print screen", "prtscr", "snip"),
           ("how", "take", "capture", "save", "send", "find", "grab")),
          "It depends on the device: an iPhone is the side button and volume-up together, most "
          "Android phones are power and volume-down, a Windows PC is Windows key + Shift + S, and a "
          "Mac is Shift + Command + 4 to drag a box. Say which one you are on and I will give you the "
          "exact steps for it.",
          # the three device entries answer a line that names the device; this one is for the
          # line that does not
          ask=("screenshot", "screen shot", "screen grab", "print screen", "prtscr"),
          avoid=("windows", "laptop", "pc", "computer", "mac", "macbook", "apple", "phone",
                 "iphone", "android", "mobile", "ipad", "tablet", "video", "record", "call",
                 # a Chromebook and a Fire tablet have their own rows now, and this one was
                 # answering both with the list of devices they are not on
                 "chromebook", "chrome book", "chrome os", "kindle", "kindle fire", "fire hd",
                 "fire tablet", "amazon fire")),
    entry("copy-paste-windows",
          (("copy and paste", "copy paste", "cut and paste", "paste something", "copy something",
            "how do i copy", "how do i paste"),
           ("windows", "pc", "laptop", "computer", "ctrl", "chromebook", "desktop", "how",
            "keyboard", "select", "text", "something")),
          "On a Windows laptop select what you want, press Ctrl+C to copy and Ctrl+V to paste; "
          "Ctrl+X cuts it and Ctrl+Z puts back a mistake. A Chromebook is Ctrl+C and Ctrl+V as "
          "well, and a right-click gives Copy and Paste in the menu if the keys are awkward.",
          avoid=("mac", "macbook", "apple", "command", "iphone", "ipad", "phone", "android",
                 "whatsapp", "word", "excel", "spreadsheet")),
    entry("usb-c-port",
          (("usb c", "usb-c", "usb type c", "usbc", "usb port", "usb ports"),
           ("use", "what", "charge", "charging", "plug", "connect", "port", "cable", "lead",
            "for", "how")),
          "A USB-C plug fits either way up, so there is no wrong way to push it in, and the one lead "
          "carries both power and data. On a phone or a thin laptop it is also the charging port, so "
          "the same cable charges the phone and, with a small adapter, runs a monitor or copies "
          "photos. If nothing happens, flip the plug and try another lead: cheap ones often carry "
          "power but no data.",
          ask=("usb c", "usb-c", "usb type c", "usbc", "usb port", "usb ports"),
          avoid=("usb stick", "usb drive", "memory stick", "flash drive", "printer", "hub", "dock")),
    entry("microwave-clock",
          (("microwave clock", "clock on my microwave", "time on my microwave",
            "set the clock on the microwave", "microwave time", "clock on the microwave"),
           ("set", "change", "wrong", "how", "clock", "time", "microwave", "shows")),
          "Press Clock once or twice until the hours flash, type the hour, press Clock again for the "
          "minutes, then Clock to save; on many models you hold the Clock button for three seconds "
          "first. If it will not stay set, the display is probably showing cook time rather than the "
          "clock, so press Stop or Clear once. Unplugging it for a minute and plugging it back in "
          "resets the clock on most microwaves.",
          ask=("clock", "time"),
          avoid=("oven", "bake", "roast", "defrost", "not heating", "not working", "bulb", "door",
                 "turntable", "sparking")),
    # "how do i change the time on my oven" was a shrug, while the microwave's clock right above
    # it answered. An oven clock is set two ways - the dial-and-two-buttons kind and the touch
    # panel - and both ask the same thing, so the answer gives both and how to get out.
    entry("oven-clock",
          (("oven clock", "clock on my oven", "time on my oven", "set the clock on the oven",
            "oven time", "clock on the oven", "change the time on my oven"),
           ("set", "change", "wrong", "how", "clock", "time", "oven", "shows", "reset")),
          "Hold the clock button until the hour flashes, turn or press the plus and minus to the "
          "right hour, press clock again for the minutes, then press it once more to save - the "
          "symbol on most ovens is a small clock or a bell. On a touch panel the same steps are "
          "under Settings or the clock icon, and if the display will not go into flashing it is "
          "usually still showing a timer: press the timer button to clear it first. After a power "
          "cut most ovens come back flashing 12:00 and need the same steps.",
          ask=("clock", "time"),
          avoid=("microwave", "not heating", "not working", "bulb", "door", "element", "fan",
                 "smell", "smoke", "clean", "cleaning", "how long", "temperature", "gas mark")),
    entry("descale-coffee-machine",
          (("descale", "descaling", "descaler", "scale in my coffee machine",
            "limescale in the coffee machine", "clean the inside of my coffee machine"),
           ("coffee", "machine", "espresso", "nespresso", "bean to cup", "filter machine",
            "coffee maker", "how", "with")),
          "Run the maker's descaling cycle with its own descaler, or citric acid at about 20g to a "
          "litre of warm water, then flush two full tanks of clean water through before you drink "
          "from it again. A bean-to-cup machine usually prompts you and takes 20 to 30 minutes; a "
          "filter machine is a jug job, so run the solution through and rinse twice. Vinegar works "
          "at a pinch but leaves a taste and hardens some seals.",
          ask=("coffee", "espresso", "machine", "maker"),
          avoid=("kettle", "shower", "iron", "washing machine", "dishwasher", "tap", "boiler")),
    entry("private-account",
          (("make my account private", "private account", "account private", "make my profile private",
            "private profile", "set my account to private", "keep my account private",
            # people name the app rather than the setting: "how do i make my instagram private"
            "make my instagram private", "instagram private", "make my facebook private",
            "facebook private", "facebook profile private", "instagram profile private",
            "make my tiktok private", "tiktok private",
            "make my snapchat private", "snapchat private"),
           ("how", "make", "set", "turn", "put", "instagram", "facebook", "tiktok", "snapchat",
            "account", "profile")),
          "On Instagram it is Settings > Account privacy > Private account; on Facebook, Settings > "
          "Privacy > Who can see what you share set to Friends, and on TikTok, Settings and privacy > "
          "Privacy > Private account. Private means new people have to ask to follow you, but it does "
          "not hide anything from the people already following, so check that list too.",
          ask=("private", "account", "profile"),
          avoid=("bank", "email", "whatsapp", "wifi", "router", "school", "work", "staff",
                 "business", "company")),
    entry("tv-volume",
          (("volume on my tv", "tv volume", "volume up on the tv", "turn the volume up",
            "sound is too loud", "tv is too loud", "too loud", "sound too loud",
            "adverts", "advert", "adverts are louder", "much louder",
            "turn the volume down", "turn up the volume", "turn down the volume",
            "make the tv louder", "tv is too quiet", "tv sound is too quiet",
            "sound on my tv", "mute the tv"),
           ("tv", "telly", "television", "soundbar", "sound bar", "remote", "channel")),
          "Use the TV remote's own volume rocker first and check the set is not muted; if the "
          "number moves but the sound does not, the remote is sending it to a soundbar or a Fire "
          "Stick, so point it at the TV body and try again. In the Sound menu switch off auto "
          "volume and night mode, and for one quiet channel only, look at the audio track setting "
          "- a film with a 5.1 track played through small speakers sounds quiet until it is set to "
          "stereo. If it is only the adverts that are loud, turn on Night mode or Auto Volume, "
          "because they are mixed louder than the programme on purpose.",
          ask=("volume", "louder", "quieter", "quiet", "mute", "sound", "loud"),
          avoid=("phone", "iphone", "android", "laptop", "computer", "pc", "radio", "headphones",
                 "earbuds", "doorbell", "alarm", "maths", "room", "box", "cylinder")),
    entry("monitor-wakes",
          (("monitor turns on by itself", "monitor switches on by itself", "monitor keeps waking up",
            "monitor comes on by itself", "screen turns on by itself", "monitor turns itself on",
            "monitor wakes up"),
           ("monitor", "screen", "display", "pc", "desktop", "laptop", "why", "by itself")),
          "The computer is waking the display, not the monitor doing it alone: a nudged mouse or a "
          "keypress, an overnight update, or a device on the same HDMI lead waking it through "
          "HDMI-CEC. Set the screen to sleep after five minutes (Settings > System > Power on "
          "Windows, System Settings > Displays on a Mac), switch off anything set to wake for the "
          "network, and in Command Prompt run powercfg -lastwake to see what did it.",
          ask=("monitor", "screen", "display"),
          avoid=("phone", "tv", "telly", "tablet", "brightness", "too bright", "dim", "dark",
                 "flicker", "flickering", "resolution", "second monitor")),
    entry("keep-number",
          (("keep my number", "keep the same number", "same number", "my number", "my old number",
            "switch network", "change network", "new sim", "sim only", "port my number",
            "move my number", "transfer my number", "pac code", "pac"),
           ("how", "keep", "switch", "move", "transfer", "change", "get", "new", "old",
            "network", "provider", "sim", "phone", "contract")),
          "Ask your old network for a PAC code by texting PAC to 65075: it is free, they must "
          "send it within a minute, and it lasts 30 days. Give the PAC to the new network when "
          "you order the SIM and the switch happens the next working day, usually with only a "
          "few hours without service. Do not cancel the old contract first or the number can go "
          "with it - the PAC cancels it for you.",
          ask=("keep", "switch", "move", "transfer", "change", "pac", "new sim", "new network"),
          # a lost or stolen phone, an unlocked handset and a locked screen are other questions
          avoid=("password", "pin", "unlock", "icloud", "whatsapp", "bank", "landline",
                 "voicemail", "lost", "stolen", "blocked")),
    entry("leave-phone-contract",
          (("contract", "phone contract", "mobile contract", "sim contract", "airtime",
            "phone", "mobile", "sim", "o2", "vodafone", "giffgaff", "voxi", "tesco mobile",
            "sky mobile", "ee", "three", "pac code",
            # a pay-monthly service is the same shape of question, and without these the
            # "get out of" and "should i" words handed the line to the read-it-before-you-sign
            # answer: "can i get out of my sky contract" was told about late payment clauses.
            "sky contract", "virgin media contract", "tv contract", "broadband contract"),
           ("get out", "getting out", "get out of", "cancel", "cancelling", "cancel my",
            "end", "end my", "exit", "leave", "leaving", "terminate", "break", "early",
            "early upgrade", "pay off", "remaining")),
          "Check when the minimum term ends and what the early exit figure is, then ask for both "
          "in writing: in the UK the rest of the line rental is capped at what you still owe, and "
          "a network must give you a PAC or STAC code free if you are switching or cancelling. "
          "Bundled handsets are usually paid off in full; for a TV or broadband service the same "
          "notice and exit figure apply, and there is no code. If you are out of the minimum term "
          "you can simply give 30 days' notice; inside it, ask for the figure and compare it with "
          "staying to the end.",
          ask=("get out", "getting out", "cancel", "cancelling", "end", "exit", "leave",
               "leaving", "terminate", "break", "early", "pay off"),
          # someone else's contract is not this question (tests/test_technology.py lists "how do
          # i cancel her phone contract" among the lines technology must leave alone)
          avoid=("cheap", "cheapest", "deal", "upgrade to", "bill is", "data", "unlock",
                 "her", "his", "their", "someone", "someone else", "my mum", "my dad",
                 "my son", "my daughter", "my partner", "my friend",
                 # the key word "contract" is on its own, so an energy, water, broadband,
                 # insurance or gym contract scored this mobile answer and was told to ask for a
                 # PAC code. Each of those has its own exit-fee answer.
                 "energy", "gas", "electricity", "electric", "supplier", "tariff", "kwh", "meter",
                 "water", "broadband", "internet", "landline", "insurance", "car insurance",
                 "home insurance", "gym", "gyms", "fitness", "leisure centre", "membership",
                 "lease", "tenancy", "rent",
                 # A service name on its own is not the other contract: "my sky contract" and
                 # "my virgin media contract" are lines this answer should keep, and a bare
                 # "sky" here sent them to the read-it-before-you-sign page (pearl-moth, #2470).
                 # Only the television shapes stand the service answer down.
                 "tv package", "sky tv", "sky q", "sky glass", "sky box", "sky broadband",
                 "virgin media tv", "virgin tv", "virgin media broadband",
                 # a contract with no service in the line is not a phone contract: without this
                 # "how do i get out of a contract i signed" got the PAC code answer.
                 "signed", "i signed", "business", "client", "freelance", "self employed",
                 "zero hours", "employment", "job", "apprenticeship")),

    # --- the step-by-step jobs people ask for most -----------------------------------
    entry("use-alexa", (("alexa", "echo", "echo dot", "echo show", "alexa show", "smart speaker"),
                        ("use", "set up", "setup", "ask", "do", "what can", "first", "start",
                         "works", "work", "how")),
          "Ask it the weather, set a timer or an alarm, play the radio, add something to a "
          "shopping list, or put a question to it - say \"Alexa\" first, then the ask. To set one "
          "up, plug it in, open the Alexa app and sign in, and it finds the speaker and joins your "
          "wifi; the app's Things to Try lists the rest, and the button on top mutes the "
          "microphone.",
          ask=("alexa", "echo", "smart speaker"),
          # a speaker problem, a music service and a smart bulb are other questions
          avoid=("not working", "wont", "won't", "stopped", "offline", "keeps", "says",
                 "bulb", "lights", "plug", "thermostat", "ring", "doorbell", "tv", "television",
                 "music", "spotify", "cancel", "subscription", "account hacked", "privacy")),

    entry("console-parental-controls", (("xbox", "playstation", "ps4", "ps5", "nintendo",
                                         "switch", "console", "games console"),
                                        ("parental", "controls", "restrict", "limit", "pin",
                                         "child", "kid", "kids", "son", "daughter", "teen",
                                         "teenager", "age", "spend", "time", "block",
                                         "set up", "setup", "safe")),
          "On an Xbox it is Settings > Account > Family settings > Manage family members, and the "
          "Xbox Family Settings app does the same from your phone; on a PlayStation it is "
          "Settings > Family and Parental Controls, with a 4-digit pass code on the console. On a "
          "Switch it is the Nintendo Switch Parental Controls app. Set the age rating, the daily "
          "play limit and the spending limit there, and change the console's own pass code so the "
          "settings cannot be undone.",
          ask=("xbox", "playstation", "ps4", "ps5", "nintendo", "switch", "console"),
          # `kid-first-phone` also matches "set up ... for my son": a console in the front room is
          # not a first phone, and the ask gate keeps phone lines out of this one
          bias=2,
          # a first phone, screen time and age ratings on a phone are other questions
          avoid=("phone", "iphone", "android", "ipad", "tablet", "youtube", "tiktok", "fortnite",
                 "account hacked", "granted", "game pass", "controller", "headset")),

    entry("move-files-old-laptop", (("old laptop", "old computer", "old pc", "new laptop",
                                     "new computer", "new pc", "old mac", "new mac"),
                                    ("files", "transfer", "move", "copy", "photos", "documents",
                                     "everything", "migrate", "bring", "get my", "how")),
          "Copy the lot onto an external drive or a big USB stick: on Windows open File Explorer "
          "and drag the user folder (Desktop, Documents, Pictures, Downloads) across, and the same "
          "on a Mac from Finder. If both machines work, a cloud folder does it without a drive - "
          "sign in to OneDrive, iCloud or Google Drive on the old one, let it upload, then sign in "
          "on the new one. Do the browser bookmarks and passwords through the browser's own sync, "
          "and sign out of the old machine before you get rid of it.",
          ask=("old", "new"),
          # moving WhatsApp, a phone's photos and a dead machine are other questions
          avoid=("phone", "iphone", "android", "whatsapp", "wont turn on", "won't turn on",
                 "dead", "broken", "password", "windows 11", "upgrade", "macbook air", "buy")),

    entry("email-signature", (("signature", "sign off", "my name at the bottom"),
                              ("email", "gmail", "outlook", "mail", "add", "set up", "make",
                               "put", "how")),
          "In Gmail: the gear icon > See all settings > General, scroll to Signature, create one "
          "and save, and it is added to new mail and replies. In Outlook: Settings > Mail > "
          "Compose and reply > Email signature. Keep it to your name, a phone number and one line "
          "of what you do; a logo image often shows as an attachment on other people's phones.",
          # `email-new-phone` also matches "set up ... email", and a signature is not a mail app
          # moving to a new phone, so this wins the tie on rank
          bias=2,
          ask=("email", "gmail", "outlook", "mail"),
          # a form to sign, a handwritten signature and an e-signature service are other questions
          avoid=("pdf", "document", "contract", "lease", "tenancy", "form", "sign here",
                 "electronic signature", "docusign", "handwriting", "photo", "scan")),

    entry("smart-meter", (("smart meter", "smart meters", "in home display", "ihd",
                           "electricity meter", "gas meter", "prepayment meter", "key meter",
                           "electric key", "gas key"),
                          ("read", "how", "use", "work", "works", "topping", "top up", "usage",
                           "shows", "display", "in home", "not working", "move", "switch")),
          _meter_reply,
          ask=("meter", "meters", "ihd", "display", "key meter", "electric key", "gas key"),
          # a water meter, a meter reading for a bill and a faulty boiler are other questions
          avoid=("water", "parking", "taxi", "reading for", "submit", "boiler", "radiator",
                 "landlord", "council tax", "electric car", "charger")),
    # A file deleted by mistake is the commonest office scare, and the answer depends on where it
    # lived: a file in a folder has the bin and the version history behind it, and a file on a
    # stick or a card has neither - every write to the drive covers the space the file was in, so
    # the only answer there is to stop using it and let a recovery tool read the drive. The row is
    # a callable for that reason: the same scare has two answers, and one paragraph cannot say
    # both.
    entry("recover-deleted-file",
          (("deleted", "delete", "recover", "get back", "restore", "lost", "gone", "disappeared",
            "by accident", "by mistake"),
           ("document", "documents", "file", "files", "word", "doc", "docx", "spreadsheet",
            "report", "essay", "homework", "presentation", "folder",
            # A stick, a card or an external drive is a file's home too, and the bin paragraph is
            # wrong for it: "how do i recover deleted files from a usb stick" got the how-to-use-a-
            # stick card, which says to drag files onto it - writing to the drive, which is the one
            # thing that loses them for good.
            "usb", "usb stick", "usb drive", "memory stick", "flash drive", "pen drive",
            "sd card", "memory card", "card", "external drive", "hard drive", "drive",
            "downloads", "desktop", "laptop", "computer", "pc")),
          _recover_deleted,
          # a deleted photo has its own answer, and a phone's storage is not this question either
          avoid=("photos", "photo", "pictures", "videos", "images", "storage", "full", "space",
                 "iphone", "android", "phone", "contact", "contacts", "message", "messages",
                 # "my tyre has gone flat" then "how far can i drive on it" is a motoring line:
                 # the "gone" and the "drive" of the two turns together read as a lost file on a
                 # disk, and a car's drive is not a disk at all. A car question carries one of
                 # these words and a file question does not.
                 "tyre", "tyres", "tire", "tires", "car", "cars", "van", "van", "road", "roads",
                 "motorway", "mph", "how far", "far can i", "petrol", "diesel", "fuel", "engine",
                 "brake", "brakes", "wheel", "wheels", "journey", "lane", "overtake",
                 "parking", "mechanic", "garage", "roundabout", "traffic", "rush hour")),
    # "how do i make a spreadsheet" was the search hedge ("That's beyond what I know well"): the
    # sum row below needs one of add/sum/total/formula in the line, and a person starting from
    # nothing says none of them. This is the first sheet, and its own words are the ones people
    # use for it - make, start, first, beginner.
    entry("spreadsheet-first",
          (("spreadsheet", "excel", "google sheets", "sheets", "make a table", "formula",
            "spreadsheet formulas"),
           ("how do i", "make", "start", "first", "learn", "beginner", "use", "sum", "total",
            "add up", "what is", "explain")),
          "Type your headings across the top (Date, Description, In, Out, Balance), put one thing "
          "per row underneath, and that is a working spreadsheet. A formula starts with = and uses "
          "the cell's address: =B2-C2 takes one from the other, and =SUM(D2:D30) adds a whole "
          "column, which is the two you will use most. Keep one table per sheet, freeze the top row "
          "(View > Freeze) so the headings stay put, and save it with a name you will recognise in "
          "six months.",
          avoid=("bed sheet", "sheets for a bed", "paint", "wallpaper", "duvet",
                 # A bed sheet is a sheet to a person washing it, and "how do i whiten yellowed
                 # sheets" was this card's, headings and columns and all: a laundry word in the
                 # line means the linen is meant, and a spreadsheet is never washed, bleached,
                 # ironed or dried in a tumble dryer.
                 "wash", "washing", "washed", "whiten", "whitening", "bleach", "bleaching",
                 "laundry", "yellowed", "yellow", "yellowing", "grey", "gray", "dingy",
                 "bedding", "linen", "pillowcase", "pillowcases", "bed sheets", "fitted sheet",
                 "fitted sheets", "iron", "ironing", "tumble", "tumble dry", "dryer", "soiled",
                 # "how do i start watching formula 1" keys on "formula" and "start", and the
                 # sport is not a spreadsheet.
                 "formula 1", "formula one", "f1", "grand prix", "motor racing", "racing",
                 # the parts of a spreadsheet have their own rows, and a line that names one is
                 # that row's question: this card is for the first sheet, from nothing.
                 "add up", "sum", "total", "totals", "autosum", "chart", "charts", "graph",
                 "graphs", "plot", "vlookup", "xlookup", "lookup", "pivot", "filter", "sort"),
          bias=1),
    # "how do i use vlookup" was the search hedge on main - the one formula everybody at work is
    # asked for had no card at all.
    entry("vlookup-how",
          (("vlookup", "xlookup", "lookup", "index match", "v lookup", "v-lookup"),
           ("how do i", "use", "work", "works", "explain", "not working", "error", "wrong",
            "what is", "formula", "sheet", "excel")),
          "VLOOKUP has four parts: =VLOOKUP(what you are looking for, the table, which column to "
          "bring back, FALSE). The thing you look up must be in the first column of that table, and "
          "FALSE means an exact match - leave it out and you get nonsense. =VLOOKUP(A2, Sheet2!A:C, "
          "3, FALSE) says: take A2, find it in column A of Sheet2, give me what is in column C. If "
          "it gives #N/A the values are not really equal (a number stored as text is the usual "
          "cause); if you have a newer Excel or Sheets, XLOOKUP does the same job without the "
          "first-column rule.",
          avoid=("searching for a word", "thesaurus", "dictionary"),
          bias=1),
    entry("spreadsheet-sum",
          (("add up", "adds up", "sum", "total", "totals", "autosum", "formula", "formulas",
            "running total", "equals"),
           ("spreadsheet", "excel", "google sheets", "sheets", "sheet", "column", "columns",
            "cells", "rows", "numbers")),
          "Put the cursor under the column and press AutoSum (Alt and = in Excel; the sigma in the "
          "toolbar on Google Sheets): it writes =SUM(A1:A20) for the range it finds. If the total "
          "comes out short, look for a number typed with a space or an apostrophe in front - Excel "
          "reads those as text - and the little green triangle in the corner is how it tells you.",
          ask=("add", "adds", "sum", "total", "formula", "make", "how", "get", "want", "need"),
          # a maths homework sum and a spreadsheet are not the same question
          avoid=("fractions", "algebra", "percentages", "how do i work out", "homework")),
    # The chart is the part of a spreadsheet people are asked for at work or at school, and
    # "reading-a-graph" is the science answer to a different question.
    entry("make-a-chart",
          (("chart", "charts", "graph", "graphs", "pie chart", "bar chart", "line graph",
            "plot", "plotting"),
           ("excel", "spreadsheet", "google sheets", "sheets", "sheet", "word", "powerpoint",
            "make", "create", "add", "insert", "put")),
          "Select the numbers and the header row, then Insert > Recommended Charts in Excel (or "
          "the chart button in Google Sheets) and take the simple one it offers: bars for comparing "
          "amounts, a line for change over time, a pie only for parts of one whole. If the chart "
          "comes out as one flat series or the labels are wrong, the header row was read as data - "
          "delete it and select again from the header down.",
          bias=1,
          avoid=("read", "reading", "what does this graph", "axis", "axes", "in my homework",
                 "physics", "chemistry", "maths question")),
    entry("sign-a-pdf",
          (("sign", "signature", "signed", "sign it", "fill in"),
           ("pdf", "pdfs", "form", "document", "docusign")),
          "The free way: open it in Adobe Acrobat Reader and use Fill & Sign, draw or type your "
          "signature once, then drag it onto the line and save a copy. On a Mac, Preview has Markup "
          "> Sign; on a phone, the Files app on an iPhone and Google Drive's annotate tool both do "
          "it. A phone photo of your signature pasted in is fine for most forms, but check whether "
          "a contract wants a proper e-signature service.",
          avoid=("lease", "tenancy", "contract of employment", "employment contract", "school",
                 "sign language", "sign up", "sign in")),
    entry("merge-pdfs",
          (("merge", "merging", "combine", "join", "put together", "into one"),
           ("pdf", "pdfs", "documents", "files", "pages")),
          "Every reader has a free join: in Adobe Acrobat's online Merge Files tool you pick the "
          "PDFs in order and download one file, and on a Mac Preview does it by dragging the pages' "
          "thumbnails into the first document (View > Thumbnails, then drag). On Windows, open the "
          "first PDF, choose Print, select Microsoft Print to PDF and add the other files as extra "
          "pages. Number the files first so the order comes out right."),
    entry("tv-subtitles",
          (("subtitles", "subtitle", "captions", "captioned", "closed captions", "audio description"),
           ("turn on", "switch on", "enable", "show", "get", "tv", "television", "telly", "netflix",
            "iplayer", "youtube", "prime", "app", "where")),
          "On a smart TV it lives in Settings > Accessibility as Subtitles or Captions, and on a "
          "Freeview remote press SUBTITLE while the programme is on. Inside an app it is the "
          "speech-bubble icon on the player, which only appears once something is playing. If they "
          "come back on after you turn them off, the TV's accessibility menu is the one that wins.",
          bias=1),
    entry("tv-slow-and-clunky",
          (("slow", "sluggish", "laggy", "freezes", "frozen", "takes ages", "keeps buffering",
            "stuck", "unresponsive"),
           ("smart tv", "tv", "television", "telly", "fire stick", "firestick", "roku", "apps")),
          "A smart TV slows down because of its apps and its wifi, not its screen: close what you "
          "are not using, uninstall the apps you never open, then unplug it for a minute and let "
          "it restart. If menus still crawl, it is usually the wifi - move the router closer or run "
          "an ethernet cable - and a £30 streaming stick with a fresh processor beats replacing "
          "the set.",
          avoid=("laptop", "computer", "pc", "phone", "ipad", "tablet", "wifi password",
                 "no signal", "not turning on", "remote")),
    # "how do i see who is on my wifi" was reaching a travel entry, because "see" and "on" are
    # words any line can have.
    entry("who-is-on-my-wifi",
          (("who", "someone else", "somebody else", "devices", "connected", "on my wifi",
            "on my network", "using my wifi", "using my internet", "piggybacking", "neighbours",
            "next door", "unknown device", "unknown devices", "how many"),
           ("wifi", "wi fi", "wireless", "network", "router", "broadband", "internet", "devices")),
          "Log in to the router - the address is usually 192.168.0.1 or 192.168.1.1 and the "
          "password is on the sticker on the back - and open the page called Connected Devices, "
          "Attached Devices or DHCP Client List, which names every device on the network. Anything "
          "you do not recognise: change the wifi password there and it drops off, then join your "
          "own things again. Your phone's wifi settings will also show your own connection's "
          "details if the router has no such page.",
          bias=1,
          # this lists what is on the network; a device that will not join it is a different
          # question, and "connecting" is a form of the "connected" this key needs
          avoid=("tv", "television", "telly", "fire stick", "roku", "phone", "iphone", "android",
                 "laptop", "computer", "printer", "wont connect", "won't connect",
                 "not connecting", "cant connect", "can't connect", "keeps dropping")),
    entry("office-phone",
          (("office", "work", "desk", "shop", "reception", "workplace", "open plan",
            "switchboard", "front desk", "at work", "in the office", "at the office",
            "office phone", "desk phone", "work phone", "shop phone", "reception phone",
            "office line", "desk line", "work line", "shop line", "reception line",
            "business line"),
           ("phone", "line", "ringing", "ring", "calls", "switchboard")),
          "A shared office line rings for everyone, so the fix is a rota rather than the block "
          "list: take turns to answer, put the line on voicemail for the hour you need to "
          "concentrate, and give the people who ring most a better way to reach you. If the calls "
          "are sales calls to the business, the residential Telephone Preference Service does not "
          "cover you - ask the phone provider about call filtering, and never press a number to "
          "\"speak to someone\".",
          # The ring is what makes this a call about a ringing line: without it, "how do i set up
          # my work phone" and "the office phone is broken" are setup and repair questions.
          ask=("ring", "rings", "ringing", "rang", "keeps ringing", "keep ringing",
               "kept ringing"),
          bias=1,
          # A ring on a finger and a phone that will not ring are their own questions.
          avoid=("gold", "silver", "wedding ring", "engagement ring", "diamond", "jewellery",
                 "jewelry", "necklace", "bracelet", "earring", "earrings", "finger",
                 "polish my ring", "clean my ring", "finger green",
                 "wont ring", "won't ring", "not ringing", "no ring", "broken", "repair",
                 "fix")),
    entry("nuisance-calls",
          # "how do i stop getting cold calls" reached the repeated-colds answer, because "cold"
          # and "calls" sat in one phrase and a phrase alone does not reach MIN_SCORE. Split, the
          # same line has three key words and cannot be mistaken for a runny nose. The bare "cold"
          # is gone: it also took "what can i take for a cold", "i have a cold, can i still run"
          # and "how does a fridge keep things cold". The call phrase is the only cold that rings.
          (("robocall", "robocalls", "nuisance", "cold call", "cold calls", "cold caller",
            "cold callers", "silent", "unwanted", "spam",
            "marketing", "junk", "pesky", "keeps ringing", "keep getting", "so many"),
           ("calls", "call", "callers", "ringing", "ring me", "phone calls"),
           ("stop", "block", "get rid", "fewer", "how", "can i", "what can", "reduce")),
          _cold_calls,
          # A call word is what makes this entry about a phone at all, so it is a gate and not
          # just a key part. Without it the ask words below were covered words in their own
          # right, and "cold" plus "how" plus "get rid" reached MIN_SCORE with no phone word in
          # the line: "how do i get rid of a cold fast" got the nuisance calls card.
          ask=("call", "calls", "caller", "callers", "calling", "ringing", "ring me",
               "phone calls", "robocall", "robocalls", "cold calls"),
          # "how do i stop spam calls" is the junk-mail entry's line (it covers post, email,
          # texts and calls alike), and the two shapes are a phrase apart, so this one keeps to
          # the words it names
          # "cold" is the weather and the illness far more often than it is a caller, and "can i"
          # is how people ask whether to exercise: without these, "can i run in the cold" and
          # "can i run with a cold" were both answered with the Telephone Preference Service.
          # A family member who rings too much is a boundary answer, not marketing: the family
          # entry's relation gate is what tells the two apart, and its bias makes it win where
          # both match. Shape phrases are not in this avoid list: "my friend keeps ringing me
          # late at night" and "someone keeps ringing me at night" are not relatives, so they
          # must keep the TPS answer rather than falling to whatever word is left. A relative
          # word alone must not stand this down either: "my mum keeps getting calls from a
          # scammer" and "my dad keeps getting calls about his accident" are still marketing
          # calls, and a family word used to hand them to a health or neighbour answer.
          avoid=("spam calls", "spam texts", "junk mail", "junk email", "email", "emails",
                 "texts", "text", "sms", "post", "letters",
                 "run", "running", "jog", "jogging", "outside", "weather", "freezing",
                 "cold weather", "sick", "ill", "flu", "cough", "swim", "swimming",
                 "cycle", "cycling", "gym",

                 # "cold" is in the key for "cold calls", so a cold hand was reaching this row:
                 # "how do i stop my hands getting cold" is a circulation question, and the
                 # body part stands the nuisance-call answer down.
                 "hands", "hand", "fingers", "fingertips", "feet", "foot", "toes", "nose",
                 "ears", "hands are",
                 # A ring on a finger is not a phone ringing: "ringing" is in the ask above and
                 # "ring" is a form of it, so every jewellery line came back with the Telephone
                 # Preference Service. The metal, the gem and the words around a wedding are what
                 # tell them apart, and none of them appears in a real nuisance-call line.
                 "gold", "silver", "gold ring", "silver ring", "wedding ring", "wedding band",
                 "engagement ring", "diamond", "diamonds", "jewellery", "jewelry", "necklace",
                 "necklaces", "bracelet", "bracelets", "earring", "earrings", "tarnished",
                 "tarnish", "ring size", "polish my ring", "clean my ring", "finger green",
                 "engagement", "wedding", "polish", "polishing", "clean", "cleaning",
                 # and a ring on a hob is not a phone ringing either: "how much is a new hob
                 # ring" was the phone answer on specificity alone
                 "hob", "hobs", "cooker", "oven", "burner", "burners", "hotplate", "stove",
                 "stove top", "stovetop", "cooker top",
                 # fridge/freezer and a runny nose carry the cold word without a caller
                 "fridge", "freezer", "milk",
                 # A call the person is going to make is not a nuisance call: "can i just ring
                 # them and ask for a better price" is the negotiate-your-bill line, and it was
                 # reaching the Telephone Preference Service on "ring" plus "can i". What makes
                 # the difference is an object after the verb - them, him, the bank - because
                 # nobody rings a nuisance caller on purpose.
                 "ring them", "ring him", "ring her", "ring the", "ring my", "ring your",
                 "call them", "call him", "call her", "call the", "call my", "call your",
                 "phone them", "phone him", "phone her", "phone the", "phone my",
                 "ring back", "call back", "phone back",
                 # A doorbell is not a phone, and neither is a bell on a bike: "the doorbell keeps
                 # ringing" and "someone keeps ringing my doorbell at night" were answered with the
                 # Telephone Preference Service. A person who rings is handled in the reply below,
                 # which can tell "my mum keeps ringing me" from "my mum keeps getting calls from a
                 # scammer" - a word list cannot, because a relation word is in both.
                 "doorbell", "door bell", "front door", "back door", "the bell", "bell",
                 # a work call is not a cold caller: "how do i get out of a work call" was
                 # answered with the Telephone Preference Service, because the line has a
                 # call and an ask word and nothing that says the caller is a stranger.
                 # ...but a bare "work" would do the same to "how do i stop nuisance calls at
                 # work" (and so would "at work"), so only the phrases that name the call are
                 # here: a working afternoon is still the cold-caller question.
                 "work call", "work calls", "work meeting", "work phone",
                 "meeting", "meetings", "boss", "manager", "colleague",
                 "client", "zoom", "teams", "standup", "stand-up", "interview",
                 # a market stall and a car boot sale are where people haggle, and the slip
                 # repair reads "market" as "marketing", so this entry took "how do i bargain
                 # at a market" and answered it with the Telephone Preference Service.
                 "bargain", "bargaining", "haggle", "haggling", "market stall", "car boot",
                 "boot sale", "price", "prices", "money off", "discount")),
    # People ask the bot to remind them of things all day, and the honest answer is that it
    # cannot ring a bell - but the old behaviour was worse than a shrug: "remind me to call the
    # dentist tomorrow" was read as a request for time off, because a dentist and a tomorrow are
    # what a holiday form has in it. So this entry takes the reminder itself and answers what a
    # helpful friend would: how to get the nudge that actually arrives.
    entry("remind-me",
          (("remind", "reminds", "reminder", "reminders", "remind me", "dont let me forget",
            "don't let me forget", "dont forget to", "don't forget to", "nudge me"),
           ("me", "to", "about", "set", "phone", "siri", "alexa", "google", "tomorrow",
            "tonight", "later", "monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday", "morning", "forget", "forgot", "how", "can you", "could you")),
          "I can't set an alarm or ring a bell for you, but I'll hold the thing itself here: put "
          "the job and the day in one line and it stays in the chat. For the nudge that actually "
          "arrives, use the phone in your pocket - say \"Hey Siri, remind me to call the dentist "
          "at nine tomorrow\", or on Android \"Hey Google, remind me at nine\" - and put a note "
          "where you will trip over it, on the door keys or the kettle, not on the phone you keep "
          "in your bag.",
          # a recall line is the memory's, not a reminder: "remind me what i said about the
          # dentist" is asking me to repeat it back
          # A reminder about money someone owes is not about alarms: "how do i remind someone
          # they owe me" is the asking-for-it-back question, and family.lent-money has it.
          avoid=("owes me", "owe me", "owed me", "pay me back", "repay me", "money back",
                 "lent him", "lent her", "lent them", "lent a friend",
                 "what did i", "what was i", "did i say", "did i tell", "you said", "i said",
                 "told you", "tell me again", "say again", "what have i", "who is", "who was",
                 # "remind me how to boil an egg" wants the answer, not a card: the how-to words
                 # belong to the entry that knows the six minutes.
                 # "how do i set a reminder on my phone" is a reminder question, so the how-to
                 # fence is the phrasal "how to", not every "how do i" line.
                 "how to", "how long", "how much", "how many", "what is", "recipe",
                 "temperature", "oven", "why", "why does", "why is")),
    # --- the everyday phone and till jobs ----------------------------------------
    entry("forward-text", (("forward", "pass on", "send on"),
                           ("text", "texts", "message", "messages", "sms", "whatsapp")),
          "Open the message and hold a finger on the bubble: on an iPhone tap Forward, on Android "
          "tap the three dots or More and then Forward, then pick who it goes to. A photo or a "
          "voice note forwards the same way, and a long thread is easier to screenshot.",
          ask=("text", "texts", "message", "messages", "sms", "whatsapp"),
          # forwarding an email, a parcel, or post to a new address are other questions
          avoid=("email", "emails", "inbox", "mail", "parcel", "post", "address", "landlord",
                 "rent", "call", "calls", "voicemail", "delete", "block")),

    entry("tv-turns-on", (("turns on", "turning on", "switches on", "switching on", "comes on",
                           "coming on",
                           # the same fault said with the "itself" in it: "my tv keeps turning
                           # itself on" was a chat line, because "turning on" does not match
                           # "turning itself on"
                           "turns itself on", "turning itself on", "switches itself on",
                           "switching itself on", "comes on by itself", "coming on by itself"),
                          ("tv", "television", "telly", "by itself", "on its own")),
          "It is usually the remote or a timer in the set: take the batteries out of the remote "
          "for a night, and look in Settings for a sleep timer or an auto power-on. If it comes on "
          "when you switch something else on, that is HDMI-CEC (Bravia Sync, Anynet+ or Simplink), "
          "and turning that off stops the TV following the console or the soundbar.",
          ask=("tv", "television", "telly"),
          # a set that will not come on at all is `tv-wont-turn-on`: "my tv wont turn on" was
          # getting this row, which is about a set that comes on when nobody asked
          avoid=("wont turn on", "won't turn on", "wont come on", "won't come on",
                 "not turning on", "doesnt turn on", "doesn't turn on", "no light", "dead",
                 # a laptop, a phone, a monitor or a light that comes on by itself is another
                 # repair
                 "laptop", "computer", "pc", "macbook", "phone", "light", "lights", "car",
                 "washing", "oven", "boiler", "heating", "monitor", "volume", "sound",
                 "picture", "remote", "buttons", "keeps turning off", "turns off")),

    entry("tv-wont-turn-on", (("tv", "telly", "television"),
                              ("wont turn on", "won't turn on", "wont come on", "won't come on",
                               "not turning on", "doesnt turn on", "doesn't turn on",
                               "no light", "nothing happens", "dead", "wont switch on",
                               "won't switch on")),
          "Check the plug and the socket first, then the fuse in the plug, and press the set's own "
          "power button on the side or underneath rather than the remote, because a flat remote "
          "looks exactly like a dead television. If the standby light is on but the screen stays "
          "black, shine a torch at it: a picture you can just see means the backlight has gone, "
          "which is a repair; no light at all usually means the power board.",
          bias=2,
          # a cracked screen, a set with no signal and a sound problem are other answers
          avoid=("cracked", "crack", "no signal", "sound", "volume", "picture is",
                 # "my tv remote is dead" is the remote, not the set: a flat remote looks like a
                 # dead television and this row says so in its own answer
                 "remote", "remote control", "zapper",
                 "backlight", "screen is", "laptop", "monitor", "phone")),

    # Three everyday questions that had no answer at all on main: how many years a television
    # lasts ("how long do tvs last" and "how long does a tv last" were both a shrug), how long a
    # dishwasher takes (the cycling answer took it, because "cycle" is a bike), and a phone that
    # will not ring.
    entry("tv-lifespan", (("tv", "tvs", "television", "televisions", "telly"),
                          ("how long", "how many years", "last", "lasts", "lifespan", "life",
                           "expectancy", "years", "before it dies")),
          "A modern LED set is usually good for 7 to 10 years, which is about 30,000 to 50,000 "
          "hours of watching; five hours a night is roughly seventeen years of use, so a set that "
          "dies at four is the exception and one that lasts twelve is not unusual. OLED panels "
          "fade sooner than LCD ones, and the first sign of the end is usually a band or a patch "
          "of colour that stays put. If it does go, the panel is most of the price, so replace "
          "rather than repair once it is out of warranty.",
          # a phone, a laptop and an appliance have their own life answers, and a television
          # being switched off or not coming on is a fault, not a lifespan
          avoid=("phone", "laptop", "computer", "battery", "fridge", "freezer", "washing machine",
                 "dishwasher", "boiler", "car", "tyre", "tyres", "mattress", "kettle", "remote",
                 "wont turn on", "won't turn on", "not turning on", "turning itself",
                 "turns itself", "turning off", "turns off")),
    entry("dishwasher-cycle-time", (("dishwasher", "dishwashers"),
                                    ("how long", "cycle", "programme", "program", "take",
                                     "takes", "quickest", "fastest", "shortest")),
          "An eco wash is the long one, three and a half to four hours, because it heats the water "
          "slowly and soaks rather than blasts; the standard programme is about two hours and the "
          "quick one 30 to 60 minutes. Use eco for a full load and the quick wash for a light one, "
          "and skip the pre-rinse if you are running it the same day.",
          # the machine not draining, not starting, smelly or leaking are other answers, and a
          # washing machine is not a dishwasher
          avoid=("washing machine", "not draining", "wont drain", "won't drain", "smell", "smelly",
                 "salt", "rinse aid", "wont start", "won't start", "not starting", "leaking",
                 "leak", "not filling", "dishes are still dirty", "not cleaning",
                 # "how long does a dishwasher last" is a lifespan question, and the cycle
                 # length is an answer to a different one
                 "last", "lasts", "years", "lifespan", "life expectancy",
                 # and a fitting is a job on the machine, not a wash it runs: "how long does
                 # fitting a dishwasher take" was this row's cycle times
                 "fit", "fits", "fitting", "fitted", "install", "installs", "installed",
                 "installation", "replace", "replacing", "replacement", "new one", "swap",
                 # a repair is a job on the machine too: "how long does a dishwasher repair take"
                 # was the eco programme, and the repair clock is the answer it wanted
                 "repair", "repairs", "repairing", "repaired", "mend", "mends", "mending",
                 "mended", "fix", "fixes", "fixed", "fixing", "engineer", "call out", "callout",
                 "spare part", "spare parts", "how long to fix", "long to fix")),
    entry("washing-machine-cycle-time", (("washing machine", "washer", "wash cycle",
                                          "spin cycle", "spin", "eco", "eco programme",
                                          "quick wash", "quick programme", "wash", "washing",
                                          "laundry", "laundry cycle"),
                                         ("how long", "long", "length", "hours", "hour", "minutes",
                                          "duration", "cycle", "programme", "program", "take",
                                          "takes", "last", "lasts", "quickest", "fastest",
                                          "shortest")),
          "A normal cotton wash is about two hours and an eco wash three or more, because eco "
          "heats the water slowly and soaks; the quick programme is 15 to 30 minutes and is for a "
          "small, lightly worn load, and the spin at the end of any of them is only 10 to 20 "
          "minutes. If you want it done fast, use quick with a lower spin, and run the long eco one "
          "overnight on a full load instead.",
          # a machine that will not drain, start or spin is another answer, and the dishwasher
          # has its own times
          avoid=("dishwasher", "wont drain", "won't drain", "wont spin", "won't spin",
                 "not spinning", "wont start", "won't start", "leaking", "leak", "smell",
                 "smelly", "door", "last", "lasts", "years", "lifespan",
                 # a noisy or banging machine is a fault, and the drum and door have their own
                 # answers; the washing line, the dishes and the car are not a laundry wash
                 "noisy", "noise", "loud", "bang", "banging", "rattle", "rattling", "vibrate",
                 "vibrating", "shaking", "jumping", "drum", "bearing", "wash dishes", "washing up",
                 "car", "hair", "hands", "take the washing in", "bring the washing in",
                 # a spin class is a bike class in a gym, and a spin studio or instructor is
                 # that class: the laundry row must not answer it with the length of a wash
                 "class", "classes", "gym", "exercise", "studio", "instructor", "session",
                 "membership", "memberships", "timetable", "booked", "booking",
                 # a fitting is a job on the machine, not a wash it runs
                 "fit", "fits", "fitting", "fitted", "install", "installs", "installed",
                 "installation", "replace", "replacing", "replacement", "new one", "swap",
                 # and so is a repair: "my washing machine is broken" then "how long will the
                 # repair take" was the eco cycle, when the repair clock says one visit, an hour
                 # or two, and the wait is the part
                 "repair", "repairs", "repairing", "repaired", "mend", "mends", "mending",
                 "mended", "fix", "fixes", "fixed", "fixing", "engineer", "call out", "callout",
                 "spare part", "spare parts", "how long to fix", "long to fix")),
    # A phone that is quiet is not a caller who says nothing, and it is not an alarm: the silent
    # switch (or a Focus left on) is the first thing to check for "my phone goes silent by itself"
    # and "i put my phone on silent by accident", and both were told to block the number in the
    # call log. The alarm line is `alarm-on-silent`'s, so an alarm in the line stands this down.
    entry("phone-not-ringing", (("phone", "iphone", "android", "mobile", "handset", "calls"),
                                ("not ringing", "isnt ringing", "isn't ringing", "doesnt ring",
                                 "doesn't ring", "wont ring", "won't ring", "no sound when",
                                 "straight to voicemail", "goes to voicemail", "while i am",
                                 "missed calls", "not making a sound", "stays silent",
                                 "goes silent", "go silent", "going silent", "gone silent",
                                 "is silent", "on silent", "in silent mode", "silent by itself",
                                 "keeps going quiet")),
          "Check the silent switch first: the little switch on the left side of an iPhone, or "
          "Do Not Disturb and the Focus modes on either phone, which are easy to leave on by "
          "accident. Then open the contact and make sure they are not on the block list, and check "
          "the ringtone is not set to None and the volume for ringtone is up (Android keeps a "
          "separate call volume). If it still goes straight to voicemail, that is the network: "
          "ring your provider and ask whether calls are being diverted.",
          avoid=("ringtone", "change the ring", "louder", "how do i make my phone louder",
                 "silence unknown", "block a number", "nuisance", "cold call", "scam",
                 "answer", "voicemail code", "listen to my voicemail", "alarm", "alarms",
                 "wake", "woken", "waking")),
    entry("type-emoji", (("emoji", "emojis", "smiley", "emoticon"),
                         ("type", "typing", "keyboard", "how", "get", "find", "add", "send",
                          "where")),
          "On an iPhone tap the smiley face at the bottom left of the keyboard and swipe along the "
          "categories; if it is not there, Settings > General > Keyboard > Keyboards > Add New "
          "Keyboard > Emoji. On Windows press the Windows key and the full stop together, and on a "
          "Mac it is Control, Command and Space.",
          ask=("emoji", "emojis", "smiley", "emoticon")),

    entry("self-checkout", (("self checkout", "self-checkout", "self service till",
                             "self service checkout", "scan it myself"),
                            ("use", "how", "work", "works", "pay", "bag", "first time")),
          "Scan each barcode against the glass and put the item straight in the bagging area, then "
          "pay by card at the end - you are doing the scanning, the till still adds it up. Fruit "
          "and veg you pick by name on the screen and weigh, and if it says unexpected item, move "
          "the bag aside: the assistant's handset clears it in seconds.",
          ask=("self checkout", "self-checkout", "self service", "checkout", "till")),

    entry("mute-smart-speaker", (("listening", "listens", "microphone", "mic", "recording",
                                  "records me"),
                                 ("speaker", "alexa", "echo", "google home", "nest", "siri",
                                  "homepod")),
          "Press the microphone button on the speaker: on an Echo it is the circle with a line "
          "through it on top, and it glows red when the mics are off; a Google Home or Nest has a "
          "switch at the back. Nothing is recorded while it is off, and in the Alexa app, Settings "
          "> Alexa Privacy > Review Voice History lets you delete what it already has.",
          ask=("speaker", "alexa", "echo", "google home", "nest", "microphone", "mic", "homepod"),
          # the phone listening in and a speaker that will not play are other answers
          avoid=("phone", "iphone", "android", "music", "sound", "volume", "not working",
                 "wont play", "won't play", "quiet", "tv")),

    entry("change-email-address", (("change my email", "change email", "new email address",
                                    "change email address", "different email address",
                                    "new email account", "new email"),
                                   ("how", "get", "make", "set up", "create", "want")),
          "Make the new one first - Gmail or Outlook, both free - then tell the people and the "
          "sites that matter: your bank, work, and anyone who emails you often. Keep the old "
          "address open for a couple of months instead of closing it, and set it to auto-reply "
          "with the new one, because a password reset will still go there.",
          ask=("email", "gmail", "outlook", "address", "account")),

    entry("headphones-to-tv", (("headphone", "headphones", "earphones", "earbuds", "airpods",
                                "headset"),
                               # the set has to be named, or pairing headphones to a phone comes
                               # here instead of `bluetooth-pair`
                               ("tv", "television", "telly", "sound bar", "soundbar", "at night")),
          "The quickest way is the lead: most TVs have a headphone socket at the back or side, and "
          "a long cable reaches the sofa. If the set has Bluetooth, put the headphones in pairing "
          "mode and look for them in Settings > Sound > Bluetooth on the TV - a Fire Stick and some "
          "soundbars do the pairing for a TV that has none.",
          ask=("headphone", "headphones", "earphones", "earbuds", "airpods", "headset"),
          avoid=("phone", "iphone", "android", "laptop", "pc", "computer", "quiet", "not working",
                 "wont connect", "won't connect", "one ear", "tangle")),

    entry("photo-black-and-white", (("black and white", "monochrome", "black & white"),
                                    ("photo", "photos", "picture", "pictures", "image", "camera",
                                     "make", "turn")),
          "Use the phone's own editor: open the photo in Photos or Gallery, tap Edit, then Filters "
          "or Adjust > Saturation and slide the colour all the way down. That keeps a copy you can "
          "undo, where a black-and-white camera mode throws the colour away.",
          ask=("photo", "photos", "picture", "pictures", "image", "camera")),

    entry("return-label", (("return label", "returns label", "post it back", "send it back",
                            "return parcel", "return it"),
                           ("print", "label", "post office", "qr", "how", "where", "shop")),
          "You usually do not need a printer: the retailer emails a QR code, and the Post Office or "
          "a parcel shop scans it and prints the label for you. If it is a PDF label, print it at "
          "home or at a library, tape it over the old address so the barcode is flat, and keep the "
          "receipt with the tracking number until the refund lands.",
          # the general 30-day refund law is not how to get a label printed
          bias=2,
          ask=("label", "qr", "print", "post office", "parcel", "return")),
    # --- the everyday machine jobs people ask about most --------------------------------
    entry("turn-off-phone", (("turn off my phone", "turn my phone off", "switch off my phone",
                              "switch off my iphone", "switch my iphone off", "turn off my iphone",
                              "power off my phone", "shut down my phone"),
                             ("turn", "off", "switch", "power", "shut", "phone", "iphone",
                              "android", "how")),
          "Hold the side button and the volume button together until Slide to power off appears on "
          "an iPhone; on Android hold the power button and tap Power off. A phone that will not "
          "respond needs a forced restart instead: press volume up, volume down, then hold the "
          "side button until the logo shows.",
          ask=("phone", "iphone", "android", "samsung", "mobile", "pixel"),
          avoid=("data", "wifi", "bluetooth", "notification", "location", "airplane", "pop up",
                 "ad", "alarm", "tv", "computer", "laptop", "water", "heating", "at night",
                 "mind", "racing", "sleep",
                 # "turn off my phone screen brightness" is the brightness entry's line: the
                 # screen is being dimmed, not the phone being switched off (emerald-bat)
                 "brightness", "bright", "dim", "dimmer", "screen light"),
          # the sleep lane's `switch-off` also matches "switch off ... how": a phone in the hand
          # is this question, and the ask gate keeps the racing-mind lines out of it
          bias=2),
    entry("format-a-drive", (("usb stick", "usb drive", "usb", "memory stick", "flash drive",
                              "pen drive", "usb key", "sd card", "memory card", "micro sd",
                              "card", "external drive", "external hard drive", "hard drive",
                              "hard disk", "hard disc", "ssd", "disk", "drive"),
                             _FORMAT_ASKS),
          _format_a_drive,
          bias=2,
          # the format word is the whole ask: a line that names a stick without it is how to use
          # one, and that is the usb-stick row below
          ask=_FORMAT_ASKS,
          # the documents people format are another question, and so is a cloud folder. No
          # driving word belongs here: the avoid test compares stems, so "driving" also holds
          # out "hard drive" - the format ask is what tells the two apart.
          avoid=("letter", "cv", "resume", "essay", "report", "references", "document",
                 "documents", "spreadsheet", "presentation", "homework", "google drive",
                 "onedrive", "dropbox", "cloud", "recover", "deleted")),
    entry("usb-stick", (("usb stick", "usb drive", "memory stick", "flash drive", "pen drive",
                         "usb key", "usb port"),
                        ("use", "plug", "connect", "copy", "put", "save", "files", "laptop",
                         "computer", "how", "open", "recognised", "recognized", "shows",
                         "showing", "work",
                         # a stick that is full is that stick's question, and the phone's storage
                         # answer was taking "how do i free up space on a usb stick"
                         "free up space", "space", "full", "make room", "out of space",
                         "clear space")),
          "Plug it into a USB port and it shows up as a drive in File Explorer or Finder, then drag "
          "the files onto it and eject it before pulling it out. A stick that is not seen is "
          "usually the port or the format: try another port and look for it under Disk Management "
          "on Windows, since some cheap sticks arrive unformatted.",
          # a stick with no room left is a different question, and it has its own card below:
          # "my usb stick is full" was answered with "I'm listening - say more if it helps"
          avoid=("charge", "charging", "cable", "charger", "socket", "plug socket", "extension",
                 "hdmi", "monitor", "tv", "television", "car", "radio",
                 "full", "full up", "no space", "free space", "free up", "space", "delete",
                 # A file that has gone from a stick is the recovery question, not the how-to-use-
                 # a-stick one: this card tells a person to drag files onto the drive, which is
                 # the one thing that makes a deleted file unrecoverable.
                 "deleted", "recover", "recovery", "recover deleted", "restore",
                 "lost", "gone", "disappeared", "by accident", "by mistake", "format",
                 "formatted", "wiped", "erase", "erased"),
          bias=1),
    # "how do i format an sd card" then "will it still work in my camera" was the wind-down card
    # ("Give the day a hard edge and keep it the same one"), because `camera` sits in
    # format-a-drive's avoid list and the line had nowhere else to go. It is the second half of
    # the same job: which file system to pick so the thing the card goes into can still read it.
    # Keyed on the device and the "will it still work" ask, so the drive or the format can come
    # from the line above, and fenced off from the cards that only pass through these words - a
    # SIM that moves to a new phone, a Fire Stick on a TV, a TV licence, a camcorder tape.
    entry("a-drive-still-works",
          # three parts, and any two of them are enough: the device the card goes into with the
          # ask is the follow-up ("will it still work in my camera"), and the card with the ask
          # is the line that names it ("will my sd card still work in my camera"). The device on
          # its own machine question is kept out by the words below, not by the key.
          (("camera", "camcorder", "dashcam", "car stereo", "car radio", "sat nav", "satnav",
            "drone", "printer", "switch", "nintendo", "playstation", "xbox", "tv", "television",
            "telly", "phone", "tablet", "ipad", "mp3 player"),
           ("still work", "still works", "will it work", "work in my", "work on my", "read it",
            "read them", "recognise it", "recognize it", "be read", "readable", "pick it up"),
           ("sd card", "memory card", "micro sd", "usb stick", "usb drive", "flash drive",
            "pen drive", "memory stick", "drive", "card", "stick", "format", "formatted",
            "formatting", "reformatted")),
          "Usually yes, and what decides it is the file system rather than the card: FAT32 is the "
          "safe pick for a camera, a dashcam, a car stereo, a printer or a Nintendo card slot, "
          "because that is all some of them read; exFAT is fine for a phone, a tablet, a TV or a "
          "recent camera but not for older kit; NTFS is Windows only and most cameras ignore it. "
          "A card over 32GB will not offer FAT32 on Windows, which needs its own small tool, so "
          "exFAT is the easy answer there. Put one photo on it and look at it on the device "
          "before you trust it with the rest.",
          avoid=("sim", "sim card", "network", "unlocked", "unlock", "contract", "upgrade",
                 # a device that will not work is a machine question: a cracked screen, a dead
                 # battery, no ink, a jam are all in this line's words and none of them is a card
                 "screen", "cracked", "broken", "crack", "drop", "dropped", "water", "wet",
                 "ink", "toner", "cartridge", "paper", "jam", "jammed", "app", "apps",
                 "update", "software", "wifi", "password", "account", "slow", "dead",
                 "charger", "charging", "cable", "lead", "remote", "aerial", "licence",
                 "license", "switchover", "fire stick", "fire tv", "chromecast", "roku",
                 "battery", "tape", "disc", "dvd", "blu ray", "by mistake", "by accident",
                 "lost", "gone", "deleted", "recover", "corrupt", "corrupted", "not recognised",
                 "not recognized", "size", "space", "how much", "how do i", "how to", "how can i",
                 "abroad", "another country", "overseas", "voltage", "plug", "socket", "adaptor"),
          bias=1),
    entry("email-a-photo", (("email a photo", "email photos", "send a photo in an email",
                             "attach a photo", "send photos by email", "photo too big to email"),
                            ("email", "send", "attach", "photo", "photos", "picture", "pictures",
                             "how")),
          "In the email app tap the attach or paperclip icon, pick Photos and choose the picture; a "
          "phone usually offers a size and Small or Medium is plenty for a snapshot. Most services "
          "stop at about 20 to 25MB, so for several photos send a link from Google Photos or iCloud "
          "instead of attaching them.",
          avoid=("print", "printing", "scan", "wallpaper", "frame", "passport", "visa"),
          bias=1),
    entry("keyboard-language", (("keyboard language", "keyboard layout", "foreign keyboard",
                                 "type in another language", "keyboard in french", "accents",
                                 "language", "languages", "another language"),
                                ("change", "switch", "add", "set", "language", "keyboard",
                                 "how", "type")),
          "On an iPhone or iPad it is Settings > General > Keyboard > Keyboards > Add New "
          "Keyboard, and the globe key then switches between them; on Android it is Settings > "
          "System > Languages and input. On a computer, Windows uses Windows key + Space and a Mac "
          "uses Control + Space or the flag in the menu bar.",
          # A language name is not a keyboard: "how do i learn spanish" has its own answer, so
          # the bare names came out of the key and the learning shapes stand the entry down
          # (brisk-coin, #2547).
          ask=("keyboard", "keyboards", "phone", "iphone", "android", "settings", "layout",
               "type", "typing", "accents", "key"),
          avoid=("tv", "remote", "car", "washing machine", "oven", "shopping list", "learn",
                 "learning", "speak", "speaking", "fluent", "fluently", "phrase", "phrases",
                 "pronounce", "translate", "course", "lesson", "lessons", "say hello",
                 "good at", "teach", "taught", "study", "studying",
                 # typing an emoji has its own entry, so the keyboard-with-emoji path
                 # must not take "how do i type an emoji"
                 "emoji", "emojis", "smiley", "emoticon", "emoticons"),
          bias=1),
    entry("maps-offline", (("google maps offline", "maps offline", "offline maps", "no signal maps",
                            "use maps without internet", "download a map", "download maps",
                            "download map", "map of"),
                           ("map", "maps", "offline", "download", "signal", "abroad", "how")),
          "In Google Maps tap your picture > Offline maps > Select your own map, frame the area you "
          "need and download it; it stays usable for about a year and works with the phone in "
          "airplane mode. On an iPhone, Apple Maps keeps recent routes offline and a dedicated app "
          "such as Organic Maps covers the same ground for free.",
          avoid=("paper", "road atlas", "compass"),
          bias=1),
    entry("new-folder", (("make a folder", "create a folder", "new folder", "folder on my desktop",
                          "organise my files", "organize my files"),
                         ("folder", "folders", "desktop", "files", "windows", "mac", "how",
                          "computer", "laptop")),
          "Right-click an empty part of the desktop and choose New > Folder on Windows, or "
          "right-click and choose New Folder on a Mac, then type a name. In a file window the "
          "shortcut is Ctrl + Shift + N on Windows and Shift + Command + N on a Mac.",
          avoid=("email", "inbox", "photo album", "playlist", "outlook", "gmail"),
          bias=1),
    entry("remove-virus", (("virus", "viruses", "malware", "trojan", "ransomware"),
                           ("remove", "get rid", "clean", "fix", "have", "has", "check", "real",
                            # The question asked as a yes-or-no rather than as a job: "can i get a
                            # virus on my iphone", "do iphones get viruses" and "can my phone get
                            # a virus" were all the honest shrug on main. The verb is the ask,
                            # and the phone words below are what keep a real illness out.
                            "get", "gets", "getting", "got", "catch", "catches", "caught",
                            "can i get", "can you get", "could i get", "do iphones",
                            "do phones", "do androids", "infected", "infection", "virus on")),
          "Almost always it is not a virus but a pop-up advert: close the browser tab, clear the "
          "browser data and ignore any number it tells you to ring. If the phone really is behaving "
          "oddly, run the built-in scanner (Play Protect on Android) or a reputable free scanner "
          "once, then change the passwords you used on that device.",
          # The phone only: `computer-virus` already answers a laptop with the scanner that
          # machine actually has, and a phone-worded answer to a laptop line is worse than none
          # (`how do i get rid of a virus on my laptop` was taking this at 293f5837).
          ask=("phone", "phone's", "iphone", "android", "smartphone", "tablet", "ipad"),
          avoid=("stomach", "flu", "cold", "covid", "sick", "ill", "child", "baby", "dog", "cat",
                 "antibiotic", "fever", "hospital"),
          bias=1),
    entry("dark-mode", (("dark mode", "night mode", "dark theme", "screen too bright at night",
                         "black background", "too bright", "bright at night", "bright screen",
                         "less bright"),
                        # bare "brightness" is `screen-brightness`'s word and taking it here
                        # made the word common, which let the cook glossary win a line it used
                        # to lose ("reduce the brightness on my phone")
                        ("set", "turn on", "switch", "enable", "how", "phone", "iphone",
                         "android", "screen")),
          _dark_mode_reply,
          # a wide "bright" key reaches a room light and a television: neither is a screen
          # setting, and the sleep answer is the warmer one for a phone at night (bronze-whale
          # at 51501b29).
          avoid=("camera", "photo", "tv picture", "car", "drive", "light", "lights", "lamp",
                 "bulb", "tv", "television", "monitor", "at night", "street", "headlight",
                 # the keys belong to `screen-brightness`, which is the entry for a screen being
                 # turned down rather than a request for the dark theme (bronze-whale, twice)
                 "brightness down", "turn the brightness", "brighter", "dimmer", "keys"),
          bias=1),
    entry("read-pdf-phone", (("read a pdf", "pdf on my phone", "open a pdf", "pdf file on my phone",
                              "pdf wont open"),
                             ("pdf", "read", "open", "phone", "iphone", "android", "file", "how")),
          "Tap the file in your email or downloads and it opens in the phone's own viewer, where "
          "pinching zooms and a tap hides the controls. To keep one to hand, use the Books app on "
          "an iPhone or Google Drive's PDF viewer on Android, and turn the phone sideways for a "
          "wider page.",
          avoid=("print", "printing", "sign", "edit", "merge", "convert", "word"),
          bias=1),
    # spaced repetition, or it reached nothing at all: the subject is the language, not the
    # studying, so the key needs a language or programming word as well as the asking one.
    entry("learn-to-code", (("code", "coding", "programming", "programmer", "python",
                             "javascript", "html", "css", "sql", "software developer",
                             "web development", "app development"),
                            ("learn", "learning", "start", "starting", "beginner", "beginners",
                             "begin", "from scratch", "first language", "teach myself",
                             "no experience", "where do i start", "worth learning",
                             "how long", "career", "career change", "job")),
          "Pick one language and one small thing you want to make - a page for a hobby, a script "
          "that renames files - and work through a beginner course in that language only. Python "
          "or JavaScript is the usual start; HTML and CSS first if you want to see a page you "
          "build in a browser. Code a little every day, typing examples out rather than reading "
          "them, and when you get stuck, read the error message out loud before searching for it.",
          avoid=("password", "passwords", "pin", "door code", "alarm code", "cheat code",
                 "discount code", "promo code", "postcode", "post code", "dress code",
                 "code word", "error code", "qr code", "swipe", "mortgage")),

    # A machine that got wet, and a machine that takes minutes to appear. Both were a shrug on
    # main ("my laptop got soaked in the rain", "my laptop takes about 5 minutes to turn on"), and
    # "water spilled on my laptop" was worse than a shrug: it reached `pan-boil-over`, because a
    # spilled pan and a spilled mug are the same word. The liquid entry names the machine, so the
    # hob and the kettle keep their own answer.
    entry("laptop-water", (("laptop", "laptops", "macbook", "mac book", "notebook", "computer",
                            "pc", "chromebook", "keyboard", "keyboards"),
                           ("water", "in the rain", "rain", "spilled", "spilt", "soaked",
                            "got wet", "wet", "liquid", "splash", "splashed", "dropped in",
                            "fell in", "coffee", "tea", "juice", "drink", "leaked", "leaking",
                            # The wash is the commonest way a machine gets soaked, and the
                            # laptop is the subject of the line, not the appliance it went into:
                            # "my laptop went in the wash" was answered "Sounds alright. Anything
                            # good in it?" because only the appliance's words were known. A line
                            # about the machine itself names no laptop, so it cannot land here.
                            "in the wash", "through the wash", "washed", "washing machine",
                            "in with the wash",
                            # The water a laptop falls into is not always said as "water": a
                            # bath, a sink and a toilet are where a machine goes in the house,
                            # and every one of them is the same answer. The phrase is keyed
                            # rather than the word, so "my laptop is by the sink" stays a line
                            # about where it sits.
                            "in the bath", "into the bath", "in the sink", "into the sink",
                            "in the toilet", "into the toilet", "in the basin", "in a bath",
                            "fell in the bath", "dropped in the bath", "for a swim")),
          _laptop_water,
          # `pan-boil-over` and the tea-and-coffee answer both key "spilled" and "tea", and a
          # machine with drink in it is the more urgent answer, so this one wins the tie - ahead of
          # the pan, the caffeine answer and a child's drink, which all share one of these words
          bias=4,
          # A phone in the sink is `phone-water`'s, and a spilled pan, a leaking pipe or a wet
          # coat are nobody's laptop. The wash is not on this list: "washing" folds to "wash", so
          # standing the row down on it took "my laptop went in the wash" with it, and the word
          # only ever appears next to a laptop the person is worried about.
          avoid=("phone", "iphone", "android", "tablet", "ipad", "kettle", "pan", "saucepan",
                 "hob", "boil over", "boiled over", "stopcock", "radiator", "boiler", "pipe",
                 "pipes", "plumbing",
                 "dishwasher", "coat", "jacket", "damp", "mould", "flood", "leak under",
                 "bottle", "plant", "plants", "garden", "lawn", "car", "engine", "roof", "gutter",
                 # "cup of tea" is loose-matched by "cups of", and a knocked-over mug is a spill
                 "caffeine",
                 # a wipe-down is `clean-keyboard`'s: "should i clean my keyboard with water" asks
                 # how to get the crumbs out, and a machine with drink in it says spilled or soaked
                 "clean", "cleaning", "clean it", "clean my", "wipe", "wiping", "dust", "dusty",
                 "crumb", "crumbs", "sticky", "dirty", "grubby"),
          # "will it survive" after "my laptop got coffee in it" asks about the machine the card
          # above is drying. The card's own answer is written for the first line, so the verdict
          # is written here as the line the follow-up gets.
          outcomes=(("survives",
                     "It can go either way: switched off and left alone for two days a laptop "
                     "often starts again, and if it never does a repair shop can usually still "
                     "take the files off the drive."),)),
    entry("laptop-slow-start", (("laptop", "laptops", "macbook", "mac book", "computer", "pc",
                                 "desktop", "chromebook"),
                                ("start", "starts", "starting", "turn on", "turns on", "turning on",
                                 "start up", "starts up", "boot", "booting", "come on", "log in",
                                 "login", "sign in", "startup")),
          "Cut what starts with the machine - Task Manager > Startup on Windows, Login Items on a "
          "Mac - and make sure the disk has about 10% free. If it still takes minutes, the old "
          "spinning drive is the fault and a \u00a340 SSD makes the same laptop start in seconds.",
          # Slow starting is the question and a machine that is merely slow is `laptop-slow`'s
          # answer, so the slowness is asked for rather than keyed: "my laptop is slow" has no
          # start word and must not land here.
          ask=("ages", "forever", "so long", "long time", "minutes", "slow", "sluggish",
               "takes", "take", "waiting", "waited"),
          # a machine that will not come on at all is `laptop-no-power`'s, and one that restarts
          # or wakes by itself has its own answers
          avoid=("wont turn on", "won't turn on", "wont start", "won't start", "not turning on",
                 "doesnt turn on", "doesn't turn on", "no power", "black screen", "dead",
                 "turns itself on", "switches itself on", "by itself", "on and off", "restart",
                 "restarts", "restarting", "shut down", "shuts down", "shutting down",
                 "when i start", "when i play", "game", "games", "playing", "while i", "video",
                 "render", "export", "charge", "charging", "battery", "fan", "loud", "hot",
                 "overheat")),
    # --- sound that does not come out, and speakers that will not join -------------------------
    # "my headphones have no sound" was a shrug, and the only sound answer on the shelf was the
    # science one about a pressure wave, which is what "no sound from my laptop" got.
    entry("headphones-no-sound",
          (("headphones", "headphone", "earbuds", "earbud", "airpods", "earphones", "earphone",
            "headset", "headsets", "in-ears"),
           ("no sound", "no audio", "silent", "nothing", "not working", "stopped working",
            "quiet", "cutting out", "cuts out", "crackling", "crackles", "only in one ear",
            "no sound in one ear")),
          "Check the volume on the phone rather than the headphones first, then unplug and replug "
          "the jack or forget the pairing and pair again: a headset that works on another device is "
          "the phone's setting (some phones mute Bluetooth and wired separately). If it went quiet "
          "in one ear only, the mesh over that driver is blocked with wax - brush it dry.",
          ask=("headphones", "headphone", "earbuds", "earbud", "airpods", "earphones", "headset",
               "in-ears"),
          # pairing is `bluetooth-pair`'s answer, and a one-sided earbud is `earbud-quiet`'s
          avoid=("pair", "pairing", "connect", "connecting", "won't connect", "wont connect",
                 "one side", "one ear only", "falling out", "keep falling")),
    entry("laptop-no-sound",
          (("laptop", "computer", "pc", "desktop", "monitor"),
           ("no sound", "no audio", "not making a sound", "silent", "crackling", "crackles",
            "cutting out", "cuts out", "muted", "sound is gone", "lost the sound")),
          "Click the speaker icon in the corner and check it is not muted and the right device is "
          "chosen - a laptop will happily send the sound to an HDMI lead or a headset that has gone "
          "away. Then try it with nothing plugged in: if the speakers work, the jack socket is the "
          "fault; if not, reinstall the sound driver from the maker's own site.",
          ask=("laptop", "computer", "pc", "desktop", "monitor"),
          avoid=("what is", "what are", "how does sound", "pressure wave", "travel", "physics",
                 "headphones", "earbuds", "airpods", "tv", "television", "telly", "phone")),
    # A subscription that arrives on the phone bill is stopped in two places, and the sentence
    # about the carrier belongs to this row rather than to the shared cancellation card.
    entry("subscription-on-a-bill",
          # the bare words "phone bill" are deliberately not here: a row that shares them
          # lowers the phone-bill-too-high card's own match, and "my phone bill went up again"
          # was reaching the mid-contract rise card instead (price-rise also names those bills
          # in its avoid list now, because the narrowing alone did not settle it)
          (("subscription on my phone bill", "subscription on the phone bill",
            "subscription on the phone", "third party charges", "third-party charges",
            "carrier billing", "premium rate", "charged on my phone bill",
            "charged to my phone bill", "billed through my phone", "through my carrier",
            "on my mobile bill", "charged on my bill"),
           ("subscription", "subscriptions", "cancel", "cancelling", "stop", "stops", "stopping",
            "charged", "charging", "keeps", "how do i", "how to", "bar", "block")),
          "Ask the carrier to bar third-party charges as well as stopping it in the app store: a "
          "subscription billed through the phone goes on the bill until the carrier blocks "
          "premium-rate and third-party charges, and that block is free and takes one call. Then "
          "cancel with the company too, because the carrier only stops the charge reaching your "
          "bill and the subscription itself keeps running.",
          # a plain subscription, a phone bill that went up, and a broadband contract are answers
          # of their own
          avoid=("went up", "gone up", "increase", "increased", "too high", "too much",
                 "broadband", "internet", "mobile contract", "pay monthly phone contract",
                 "how do i switch", "cheaper"),
          bias=2),
    entry("smart-speaker-setup",
          (("alexa", "echo", "echo dot", "google home", "nest mini", "nest hub", "homepod",
            "smart speaker", "hive", "siri speaker"),
           ("not responding", "not working", "won't connect", "wont connect", "not connecting",
            "offline", "not listening", "no answer", "stopped working", "set up", "setting up",
            "not turning on", "wont turn on", "keeps dropping", "blue light", "red light",
            "orange light")),
          "Unplug it for 30 seconds first, because a speaker that has lost the wifi usually comes "
          "back on its own. If it does not, open the speaker's own app and check the wifi it is meant "
          "to be on and set it up again from there - a changed router password is the commonest "
          "cause, and it wants a normal 2.4GHz network, not a phone hotspot.",
          ask=("alexa", "echo", "google home", "nest", "homepod", "speaker", "hive"),
          avoid=("cooker", "recipe", "hive rash", "car", "carplay", "stereo")),
]


# --- the words a person meets on a box, a settings screen and a scam email ----------------
# Six words that main answered with a card about something else: "what is a modem" got the
# router's answer, "what is a cookie" a biscuit recipe, "what is ransomware" the general
# malware card, and the three security ones a how-to instead of what the thing is.
_DEFINE = ("what", "whats", "what is", "what's", "mean", "means", "meaning", "define",
           "definition", "explain", "explanation", "stand for", "stands for", "do i need")

_TECH_WORDS = (
    (("modem", "modems"),
     "A modem turns the signal on the line coming into your home - fibre, cable or the phone "
     "socket - into a network connection, and the router is what shares that connection round the "
     "house. Most home boxes do both jobs in one, which is why people use the two words for the "
     "same box; the modem is the half that talks to the street.",
     # a modem that is not working is the broadband fault's question
     ("my modem", "not working", "flashing", "red light", "restart", "reset", "replace",
      "how do i")),
    (("cookie", "cookies"),
     "A cookie is a small file a website asks your browser to store: the note that keeps you "
     "signed in, the contents of your basket, or an ID that follows you between pages. It is not "
     "a program and it cannot read your files - the worst of them is tracking - and clearing them "
     "signs you out of most sites.",
     # the biscuit is the kitchen's, and a consent banner is a how-to
     ("recipe", "bake", "baking", "biscuit", "dough", "oven", "flour", "butter", "chocolate",
      "sugar", "bake", "tin", "tray", "my cookies", "accept", "banner", "how do i", "should i",
      "consent", "gdpr")),
    (("ransomware",),
     "Ransomware is a kind of malware that scrambles your files and then sells you the key: a "
     "message appears, the documents and photos will not open, and it wants money, usually in "
     "cryptocurrency. The one thing that reliably saves you is a backup you were not connected to "
     "when it struck, and paying often gets nothing back, so unplug the machine and get help "
     "before you do anything else.",
     ("my", "i have", "infected", "hit by", "attack", "attacked", "caught", "paid", "pay",
      "removal", "remove", "fix", "recover", "how do i", "should i", "protect")),
    (("phishing", "phishing email", "phishing text", "phishing message"),
     "Phishing is a fake message dressed up as your bank, a courier or HMRC to get you to log in "
     "or pay: the link goes to a page that looks right and the details go to the thief. The tell "
     "is the address it really came from and the urgency, so do not use the link - open the "
     "company's app or type the address yourself - and report it as phishing.",
     ("i got", "i clicked", "i have", "my", "what should i do", "how do i", "is this",
      "was it", "am i")),
    (("password manager", "password managers"),
     "A password manager is an app that keeps your passwords encrypted behind one master password "
     "or your face, and fills them in for you: Bitwarden, 1Password, the one built into Chrome, "
     "Safari and iCloud. It can invent a long random password for every site, which is the point - "
     "you only ever remember the one that opens the manager.",
     ("my", "which", "best", "how do i", "should i", "set up", "forgot", "lost", "family",
      "free", "recommend")),
    (("cloud storage", "cloud backup", "the cloud"),
     "Cloud storage is your files kept on someone else's servers and copied to your devices: "
     "iCloud, Google Drive, OneDrive, Dropbox. It is a copy rather than a backup if it syncs the "
     "deletion too - keep one copy that is not attached, or the ransomware or the accidental "
     "delete reaches it as well.",
     # the cloud as weather, and a specific account's storage full, are other questions
     ("weather", "sky", "rain", "forecast", "full", "storage full", "upgrade", "plan", "price",
      "cost", "my", "which", "best", "how do i", "should i")),
)

TECH_DEFINITION_ASKS = _DEFINE


def _tech_word(memory, understood):
    text = understood.get("clean") or ""
    words = understood.get("words") or []
    for keys, reply, avoid in _TECH_WORDS:
        if not any(key in text or key in words for key in keys):
            continue
        if any(word in text or word in words for word in avoid):
            continue
        return reply
    return None


ENTRIES.append(entry(
    "tech-word",
    (tuple(key for keys, _, _ in _TECH_WORDS for key in keys), TECH_DEFINITION_ASKS),
    _tech_word,
    bias=2,
    avoid=("how do i", "should i", "help me", "what can i do"),
))


# --- how many browser tabs is too many -------------------------------------------------------
# "how many tabs should i have open" was a search hedge. It is a real question about a real habit,
# and the answer is not a number from a style guide: each tab costs memory, and what hurts is the
# many-tab window rather than the count itself. The row is keyed on a window of them, so a single
# "tab" of a medicine strip, a guitar tab or the tab key stays elsewhere, and the phone rows that
# own a slow laptop keep their lines.

TOO_MANY_TABS = (
    "Aim for about ten or fewer in a window, and treat more than about twenty as a sign the work "
    "has no shape rather than a memory emergency: each tab costs a few tens of megabytes, and it "
    "is worth closing them once the machine starts swapping to disk. Group what belongs together - "
    "tab groups or a second window per project - pin the two or three you use all day, and close "
    "everything you opened to read later into a bookmark folder or a read-later list. If you keep "
    "losing the same kind of page, that is the one to pin rather than to keep finding it again.")

ENTRIES.append(entry(
    "too-many-tabs",
    (("tab", "tabs", "browser", "browser window", "chrome", "safari", "firefox", "edge"),
     ("how many", "too many", "should i have", "have open", "keep open", "open at once",
      "open all the time", "close", "speed up", "slow", "memory", "ram", "organise", "manage",
      "bookmark", "slow down my laptop", "hundreds")),
    TOO_MANY_TABS,
    ask=("tab", "tabs", "browser", "how many", "open"),
    # a tablet, a tab of a medicine strip and guitar tablature are other words entirely, and a
    # browser that will not open, one full of pop-ups or a laptop that needs speeding up in general
    # have their own rows
    avoid=("tablet", "tablets", "pill", "pills", "strip", "guitar", "tablature", "music", "song",
           "chord", "wont open", "will not open", "virus", "pop up", "popups", "history",
           "delete", "clear", "incognito", "download", "cache", "password",
           # "how many tabs of acid" is a dose, and a browser-tab answer is nonsense beside it
           "acid", "lsd", "mdma", "dose", "doses", "dosage", "microdose", "trip"),
    bias=2))
# "my usb stick is full" got "I'm listening - say more if it helps", which is the one shape of
# answer a person cannot use: the stick is full and they want the room back. The room comes from
# the big files, and a stick that says it is full while showing nothing is the fake-capacity case.
ENTRIES.append(entry(
    "usb-stick-full",
    (("usb stick", "usb drive", "memory stick", "flash drive", "pen drive", "usb key",
      "memory card", "sd card"),
     ("full", "full up", "no space", "space", "free space", "free up", "freeing", "room",
      "delete", "clear", "wont take", "cant copy", "cannot copy", "wont fit", "runs out")),
    "Sort it by size and move the videos off first: on Windows right-click the drive > Sort by > "
    "Size, on a Mac use List view and the Size column, and empty the Recycle Bin or Trash, because "
    "deleting alone frees nothing. A stick that says it is full while showing almost nothing is "
    "often a fake-capacity one from a marketplace - the real size is what h2testw or F3 report - "
    "and an old FAT32 stick cannot take a file over 4GB, so format it as exFAT if you move big "
    "videos.",
    bias=2,
    avoid=("charge", "charging", "cable", "charger", "socket", "hdmi", "monitor", "tv",
           "television", "car", "radio", "phone storage", "icloud"),
))

def _the_watch_is_marked(understood):
    """A watch line is this card's only when the line is about a mark on the glass."""
    words = {w.lower() for w in (understood.get("words") or ())}
    return bool(words & {"scratch", "scratches", "scratched", "scuff", "scuffs", "scuffed",
                         "polish", "polished", "polishing", "buff", "hairline", "mark", "marks",
                         "dull", "hazy", "haze", "worn", "crystal", "chipped"})


# A watch is not a screen: "how do i polish out a scratch on my watch" was answered with the
# phone-screen card (and, before that, with *Ida* and *Cold War*, because "polish" is also a
# country). What the scratch takes depends on the crystal, and that is the whole answer.
ENTRIES.append(entry(
    "watch-glass-scratch",
    (("watch", "watches", "watch glass", "watch face", "watch crystal", "watch screen",
      "wristwatch", "watch bezel", "scratched watch", "watch scratch", "watch scratches"),
     ("scratch", "scratches", "scratched", "scuff", "scuffs", "scuffed", "polish", "polished",
      "polishing", "buff", "hairline", "mark", "marks", "dull", "hazy", "haze", "worn",
      "fix", "fixed", "repair", "repaired", "crystal")),
    "It depends on the crystal, and the make and model tell you which: acrylic or Hesalite "
    "(many older and cheaper watches) polishes out at home with a dab of Polywatch or Brasso on a "
    "soft cloth, a mineral glass one wants a jeweller with cerium oxide - about £15 to £30 - and a "
    "sapphire crystal only scratches on a diamond or a brick, so a mark that will not lift is "
    "usually the anti-reflective coating. A scratch you can feel with a fingernail is a new "
    "crystal, £30 to £80 fitted, and worth doing before damp gets in.",
    # the mark is what makes it this card: a watch that has stopped wants a repairer, not a
    # crystal, and "how do i get a scratched watch fixed" was answered with advice on buying one
    guard=_the_watch_is_marked, bias=2,
    # A watch being watched is not a watch being scratched: "a polish film to watch",
    # "i want to watch a polish film" and "a swiss watch documentary" are films, whatever the
    # country adjective does to them, so the medium words stand this row down.
    avoid=("apple watch", "smart watch", "smartwatch", "fitbit", "garmin", "strap", "band",
           "battery", "charging", "charger", "app", "notification", "notifications", "pair",
           "film", "films", "movie", "movies", "cinema", "series", "netflix", "documentary",
           "documentaries", "on tv", "tv series", "box set", "to watch tonight"),
))

# A screen is bought, not hung: "what tv should i buy", "which tv should i get", "what size tv
# for my room" and five ways of asking what monitor to buy were the hanging-a-picture card or a
# shrug, because a telly is one of that card's subjects and the buying words ("buy", "what size",
# "which one") are in its ask. The rule is the same for a telly and a monitor: size it to the
# distance you sit, then spend on the panel. The wall questions keep the fixing card by their own
# words, so "how high should my monitor be" and "my monitor is too high" stay there.
ENTRIES.append(entry(
    "buying-a-screen",
    (("tv", "telly", "television", "tvs", "televisions", "tv set", "monitor", "monitors"),
     # the buying or sizing words are the key here rather than the ask, so a telly that will not
     # switch on and a screen whose height is being set never reach this row
     ("buy", "buying", "should i buy", "should i get", "which one", "what size", "how big",
      "how far", "how close", "distance", "worth it", "cheaper", "cheap", "best", "recommend",
      "replace", "upgrade", "new one", "choose", "working from home",
      # A screen a person already owns and finds the wrong size is the same question as one
      # being chosen, and it was not in this key: ``my monitor is too small`` got "Thanks for
      # telling me", ``my tv is too small`` got "I'm listening", and ``my telly is too small
      # for the room`` got the storage card ("Go up before you go out: a shelf over the
      # door"). The key was written in purchase verbs - buy, which one, what size - so the
      # complaint about the size was no key match at all. These are the size words themselves.
      "too small", "small", "too big", "bigger", "big", "big enough", "enough", "too far",
      "far away", "too close", "closer", "inch", "inches", "takes up")),
    # The size words are words a phone, a garden and a room all use, so they decide nothing on
    # their own: the key above needs a screen noun as well, which a telly being put somewhere
    # has and a telly being sized has not. A screen being stored, hidden or hung is the storage
    # or fixing row's question even with "small" in the line ("how do i store my tv in a small
    # flat", "how do i hide my tv cables"), and the bias here is above the storage row's so the
    # sizing answer wins the line when both rows are ticked and neither is avoided: "my telly is
    # too small for the room" is about the screen, not about the shelf.
    "Size the screen to the distance you sit, not to the budget: for a 4K set that is about one "
    "and a half times the diagonal, so 50 inches at roughly 2 metres and 65 at 2.5, and a desk "
    "monitor sits an arm's length away, which suits 24 to 27 inches. Then spend the money on the "
    "panel rather than the badge - a mid-range OLED or mini-LED beats the biggest cheap set, and "
    "a good IPS monitor beats a cheap 4K one. Check the ports you actually need (three HDMI on a "
    "telly, USB-C and a height-adjustable stand on a monitor), and skip 8K and the shop's "
    "extended warranty, which a home insurance policy or a credit card often covers already.",
    bias=3,
    # a bracket, a wall and a drill are the fixing card's question, a stopped set is repair, and
    # a screen whose place or settings are being asked about is the posture and settings rows'.
    # "Best" is in this row's key because "the best tv for the money" is a buying question, and
    # it is also how a watching question is asked, so the words the programmes card owns stand
    # this row down: "whats the best tv series on netflix" and "the best thing on telly tonight"
    # were both being told what size screen to buy. Nothing here may hold one of this row's own
    # subject words (tv, telly, monitor), or the avoid would take the row's own lines out.
    avoid=("series", "show", "shows", "film", "films", "movie", "movies", "netflix",
           "watch", "watching", "tonight", "box set", "documentary", "documentaries",
           "programme", "programmes", "episode", "episodes", "season", "seasons",
           "iplayer", "prime video", "disney plus", "whats on", "to watch",
           "wall", "walls", "bracket", "brackets", "mount", "mounting", "mounted", "hang",
           "hanging", "drill", "stud", "studs", "plasterboard", "chimney breast", "fixings",
           "too high", "too low", "how high", "how low", "height", "position",
           "wont turn on", "won't turn on", "not turning on", "no picture", "screen is black",
           "flicker", "flickers", "flickering", "fuzzy", "blurry", "cracked", "remote", "aerial",
           "broke", "broken", "repair", "fault", "faulty",
           # A telly being put somewhere is the storage row's question, and "small" is in the
           # line either way: "how do i store my tv in a small flat" was told what size screen
           # to buy, and "how do i hide my tv cables" reached the sizing card too. The place
           # words take the row out without touching a screen that is being sized.
           "store", "storing", "storage", "hide", "hiding", "cables", "cable", "shelf",
           "shelves"),
))


# --- eight cards that were deleted by mistake ---------------------------------------------
# `2296cad6` (#13078) rewrote the tail of `ENTRIES` for other work and the last eight entries in
# it went with that rewrite, so on main `phone-as-tv-remote`, `keyboard-not-typing`,
# `laptop-keeps-sleeping`, `wifi-signal-weak`, `projector-connect`, `earbuds-not-showing`,
# `smart-bulb-wont-connect` and `console-noisy` had no card at all: "my games console sounds like
# a jet" was a nod, "why is my games console so loud" was the search hedge, and a keyboard that
# types nothing was a shrug. One of them is still named by a row that stayed - `laptop-fan-loud`
# avoids `console-noisy` for a console's fan - which is the tell that the deletion was not meant.
#
# They are restored unchanged rather than reworded, because the fault was the deletion and not
# the wording. Nothing here was measured against main: a card is one or two chats out of 49,000
# in a regress sample, so a deletion of this kind does not show up there. The tests name the
# lines the eight cards exist for.

ENTRIES.append(entry(
    "phone-as-tv-remote",
    (("phone as a remote", "phone as a tv remote", "phone is a remote",
      "use my phone as a remote", "use my phone as a tv remote",
      "control my tv", "control the tv", "control my telly",
      "control the telly", "tv remote on my phone", "remote app",
      "remote on my phone", "remote for my tv", "remote for the tv"),
     ("phone", "iphone", "android", "mobile", "tv", "telly",
      "television", "use", "app", "control", "remote")),
    "Most sets have a free app that turns the phone into the remote: SmartThings for a "
    "Samsung, LG ThinQ for an LG, the Google TV or Android TV Remote app, Roku for a Roku, and "
    "the Apple TV Remote in Control Centre for an Apple TV. The phone and the TV have to be on "
    "the same wifi, and the TV has to be on. A set with no app needs an infrared blaster or a "
    "universal remote instead.",
    ask=("phone", "iphone", "android", "mobile", "app"),
    avoid=("car", "key fob", "keyfob", "fob", "garage", "gate", "doorbell", "alarm",
     "central locking", "working from home", "work from home", "remote working",
     "remote job", "hybrid")))

ENTRIES.append(entry(
    "keyboard-not-typing",
    (("keyboard", "keys", "typing"),
     ("not typing", "stopped typing", "wont type", "will not type",
      "keys not working", "keys dont work", "keys don't work",
      "some keys", "a few keys", "one key", "letters are not",
      "letters not", "types the wrong", "typing the wrong",
      "no letters", "nothing happens when i type", "stopped working",
      "not working", "dead")),
    "Test it outside the app first: press Windows key + R on Windows, or open Spotlight with "
    "Cmd + Space on a Mac. If the key does nothing there either it is the keyboard, and the "
    "usual cause is a stuck key or a spill, so unplug it or turn the laptop off and turn it "
    "upside down to dry. If the on-screen keyboard works, the built-in one has failed and a "
    "USB keyboard will do until it is fixed. Also check Filter Keys and Num Lock, which make "
    "the keyboard look broken.",
    avoid=("language", "layout", "foreign", "accent", "emoji", "emojis", "caps lock", "case",
     "symbol", "symbols", "at sign", "apostrophe", "number sign", "money", "benefit",
     "appeal", "letters from", "letter from")))

ENTRIES.append(entry(
    "laptop-keeps-sleeping",
    (("laptop", "computer", "macbook", "mac book", "notebook", "pc",
      "screen"),
     ("going to sleep", "goes to sleep", "keeps going to sleep",
      "keeps sleeping", "sleep too soon", "sleeps when",
      "sleep after", "falls asleep", "screen goes off",
      "screen turns off", "locks itself", "lock itself",
      "locking itself", "stop locking", "stop it sleeping",
      "stay awake", "wont stay on", "turns off the screen")),
    "It is the power setting, not a fault: on Windows, Settings > System > Power & sleep, set "
    "Screen to never and Sleep to never while it is plugged in; on a Mac, System Settings > "
    "Lock Screen > Turn display off on power adapter, set it to never. Windows also has a "
    "separate setting for the lock screen timeout under Personalisation > Lock screen > Screen "
    "saver, and a laptop on battery will still sleep by design.",
    avoid=("i cant sleep", "cannot sleep", "cant sleep", "insomnia", "bedtime", "tired",
     "wake up", "night", "baby", "toddler", "black screen", "blank screen", "wont turn on",
     "won't turn on", "no picture", "tv", "telly", "television", "monitor", "phone",
     "tablet"),
    # "im falling asleep at my laptop" is the person falling asleep, not the machine: this row
    # answered it with the power setting. `falls asleep` is in its keys because a laptop that
    # does it is the other fault, so the guard is what tells the two apart.
    guard=not_a_sleepy_body))

ENTRIES.append(entry(
    "wifi-signal-weak",
    (("signal", "reception"),
     ("wifi", "wi-fi", "wireless", "internet", "broadband", "router",
      "upstairs", "downstairs", "garden", "shed", "garage", "loft",
      "back bedroom", "spare room", "far room", "whole house", "house",
      "home", "stronger", "weak", "weakest", "weak signal", "bad signal",
      "poor signal", "extend", "extension", "reach", "booster", "mesh",
      "dropping", "drops", "keeps cutting")),
    "Put the router as high and as central as you can, off the floor and out of a cupboard, "
    "because a wall and a metre of height cost more signal than any gadget buys back. Then "
    "take the signal to the far end: a mesh system with two units beats a repeater, which "
    "halves the speed it repeats, and a pair of powerline adapters with a second wifi point "
    "is the cheapest fix for a solid old house. Test in the room that is bad, not beside "
    "the router.",
    avoid=("mobile signal", "phone signal", "4g", "5g", "mobile data", "three", "ee",
     "vodafone", "o2", "no service", "no signal on my phone")))

ENTRIES.append(entry(
    "projector-connect",
    (("projector", "projectors", "beamer", "big screen",
      "projector screen"),
     ("connect", "plug", "hdmi", "laptop", "computer", "pc", "how",
      "show", "display", "screen", "cable", "wireless")),
    "Run the HDMI cable from the laptop to the projector, then pick the right input on the "
    "projector's own menu. On Windows press Windows key + P and choose Duplicate (same picture "
    "on both) or Extend (a second desktop); on a Mac, System Settings > Displays > Arrange. If "
    "the laptop screen goes black instead, press Windows key + P again, because the picture is "
    "going nowhere.",
    avoid=("tv", "telly", "television", "cinema", "film", "movie", "netflix", "car",
     "headlights", "bulb", "lamp")))

ENTRIES.append(entry(
    "earbuds-not-showing",
    (("airpods", "air pods", "earbuds", "ear buds", "wireless earbuds",
      "buds", "wireless headphones", "bluetooth headphones"),
     ("not showing", "not appearing", "wont show", "will not show",
      "not listed", "not found", "cant find", "cannot find",
      "not connecting", "wont connect", "will not connect",
      "not pairing", "wont pair", "not working")),
    "Put them back in the case with the lid open and hold the button on the back (AirPods) or "
    "the case (most others) until the light flashes, because they only appear in the Bluetooth "
    "list while they are in pairing mode. If they are still not there, forget the old entry in "
    "Bluetooth, then hold the case button for 15 seconds to reset them and pair again. One bud "
    "that will not charge is usually a dirty contact in the case.",
    avoid=("car", "carplay", "android auto", "stereo", "head unit", "tv", "television",
     "telly", "sound bar", "soundbar", "wire", "wire", "3.5mm", "jack", "one ear",
     "quiet", "volume")))

ENTRIES.append(entry(
    "smart-bulb-wont-connect",
    (("smart bulb", "smart bulbs", "smart light", "smart lights",
      "smart plug", "hue", "philips hue", "led strip"),
     ("wont connect", "will not connect", "not connecting",
      "cant connect", "cannot connect", "wont pair",
      "not working", "offline", "not responding",
      "set up", "setting up", "wont join", "flashing",
      # a bulb that joins and then drops off is the same card, and the reply already answers
      # the weekly drop-off: "my smart bulbs wont stay connected" was a shrug without these.
      "stay connected", "keeps dropping", "keep dropping", "keeps disconnecting",
      "drops out", "drops off", "keeps going offline", "randomly")),
    "Almost every smart bulb only joins a 2.4GHz wifi network, so give the phone a 2.4GHz one "
    "while you set it up, and check the router has not got band steering hiding the two names. "
    "Then reset the bulb (usually five quick off-and-ons at the switch) until it flashes, and "
    "add it in its own app before anything else. A bulb that drops off every week is usually "
    "at the edge of the wifi.",
    avoid=("not lighting", "wont light", "will not light", "flickering", "flickers",
     "blown", "fuse", "fitting", "ceiling", "socket")))

ENTRIES.append(entry(
    "console-noisy",
    (("playstation", "ps5", "ps4", "xbox", "games console", "console",
      "nintendo", "switch"),
     ("loud", "noisy", "sounds like a jet", "whirring", "fan", "fans",
      "roaring", "overheating", "hot", "spinning", "loud fan",
      # the laptop's fan card has these two, and a console says the same thing: "my playstation
      # sounds like a plane" was the shrug.
      "sounds like a plane", "like a plane", "like a plane taking off",
      "too hot", "gets hot", "getting hot", "hot to touch")),
    "It is cooling itself: give it 10cm of clear air on every side, take it out of a closed "
    "cabinet, and stand it as the maker says (upright or flat, never on carpet). Then clear the "
    "dust from the vents with a vacuum on low or a can of air, held still so the fan is not "
    "spun. A console that roars within five minutes of a cold start needs its thermal paste "
    "renewing, which a repair shop does for about £50.",
    avoid=("wont turn on", "won't turn on", "no power", "parental", "controls", "account",
     "laptop", "pc", "computer", "macbook", "fridge", "boiler", "car")))
