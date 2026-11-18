"""Language and writing: spelling, the words people mix up, punctuation, and how to word a
message that is hard to send.

The answers lane owns this domain. English has a small number of traps that ordinary people
hit over and over — its and it's, affect and effect, fewer and less, the doubles in
"necessary" — and a rule answers all of them without any guessing, which is exactly the kind
of knowledge a knowledge base should hold. The second half is the writing people ask for
help with: saying no to an invitation, asking for more time, a condolence card, a complaint
letter, an apology. Each entry gives the words to use, not just advice about them.

Keys are the words being compared (both of them, so a passing mention is not enough), or the
thing being written plus what the line wants to do with it ("condolence" and "card").
"""
import re
import string

from .lookup import entry
# The animal nouns are shared with the pet rows: a toast handed to an animal is its dinner.
from .pets import ANIMAL_NOUNS
# The thank-you note is one note: the wording domain builds it from what the line names, and
# this domain answers the same question in the same words.
from .wording import thanks_note

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("language-and-writing", "school-and-study")


def _apology(memory, understood):
    words = " ".join(understood.get("words") or [])
    if any(word in words for word in ("customer", "client", "company", "order", "refund",
                                      "grovelling", "professional", "boss", "manager",
                                      "colleague", "work", "team", "staff", "late")):
        return ("Say what you did and what you'll fix, in that order, with no 'if': \"I'm sorry the "
                "order arrived late — I posted it on Tuesday and it should have been there on "
                "Thursday. I've refunded the delivery charge.\" Then one line on what changes, and "
                "leave out the 'but'.")
    return ("Say what you did, not 'if you were upset': \"I'm sorry I forgot your birthday — I had "
            "it in my head as next week and that's no excuse.\" Then say what you'll do about it, "
            "and leave out the 'but'.")


def _fewer(memory, understood):
    words = " ".join(understood.get("words") or [])
    if "money" in words or "time" in words or "water" in words:
        return ("Use 'less' for things you can't count: less time, less money, less water. "
                "Use 'fewer' for things you can: fewer people, fewer cars, fewer mistakes. "
                "'Less people' is the one people notice.")
    return ("Use 'fewer' for things you can count and 'less' for things you can't: fewer people, "
            "fewer mistakes, but less time and less money. 'Fewer people' is right; 'less people' "
            "is the mistake everyone notices.")


# A figure of speech is one question per figure: the person asked about onomatopoeia, so opening
# with irony describes a word they did not ask about. Each answer is the definition, one example,
# and nothing else; the whole list is only for a line that names none of them.
_FIGURES = (
    (("irony", "ironic", "ironically"),
     "Irony says the opposite of what is meant and lets the situation do the work: a fire station "
     "burning down, or a no-smoking sign behind the smokers. Sarcasm is the spoken, pointed "
     "version of it."),
    (("onomatopoeia", "onomatopoeic"),
     "Onomatopoeia is a word that sounds like the thing it names: splash, buzz, hiss, cuckoo, "
     "sizzle. Comics lean on it, and so does most children's poetry."),
    (("alliteration",),
     "Alliteration repeats the opening sound of nearby words: slippery slope, sweet sixteen, "
     "the wild wind. It is about the sound, not the letter - \"know nothing\" is alliteration and "
     "\"cute cat\" is not."),
    (("personification",),
     "Personification gives a thing or an idea human qualities: the wind whispered, the deadline "
     "stalked me, the kettle sulked. It turns an abstract thing into something you can picture."),
    (("hyperbole",),
     "Hyperbole is exaggeration on purpose, not meant literally: I've told you a million times, "
     "this bag weighs a ton. It works because both people know it is not true."),
    (("euphemism",),
     "A euphemism is a soft word for a hard one: passed away for died, let go for sacked, "
     "between jobs for unemployed. It spares feelings, and it can hide what happened."),
)


def _figure_of_speech(memory, understood):
    said = " ".join(str((understood or {}).get(k) or "") for k in ("clean", "text", "line")).lower()
    for words, reply in _FIGURES:
        if any(word in said for word in words):
            return reply
    return ("Irony says the opposite of what is meant (a fire station burning down); onomatopoeia "
            "is a word that sounds like the thing (splash, buzz); alliteration repeats the opening "
            "sound (slippery slope); hyperbole exaggerates on purpose (a million times). Ask me "
            "about one and I'll give you its example.")


# Two ways of asking for the same decision - "do I ring them or write?" - and the pairing is the
# gate: without "or write", "or email", "or a call" in the line it is a different question.
# Shared by the entry's key and its ask, so the row only fires on the choice being put.
_RING_OR_WRITE = ("ring or write", "call or write", "phone or write", "ring or email",
                  "call or email", "phone or email", "ring or send", "write or ring",
                  "write or call", "write or phone", "write or email", "ring or post",
                  "call or post", "text or ring", "ring or text", "ring or letter",
                  "letter or a call", "ring them or write", "call them or write",
                  "email them or ring", "or should i ring", "or should i write",
                  "or should i call", "or should i email", "ring or call", "call or ring",
                  "phone or ring", "write or send", "send or ring", "email or ring")


DASH_LOOKS = (
    (("em dash", "em-dash", "long dash", "longest"),
     "An em dash is the longest dash — like this — and it marks a break or an aside where a comma "
     "would be too quiet. On Windows hold Alt and type 0151; on a Mac it is Shift and Option and "
     "the hyphen key."),
    (("en dash", "en-dash", "minus", "range"),
     "An en dash is the middle-length dash, and its job is a range or a pair: 10–20 people, "
     "the London–Paris train. On a Mac it is Option and the hyphen key; in Word two hyphens turn "
     "into one as you type."),
    (("type", "keyboard", "how do i get", "how do i make", "shortcut"),
     "For a dash you can just write two hyphens and let the word processor turn them into one; "
     "in Word and Google Docs that happens as you type. On a Mac use Option and the hyphen key, "
     "and on Windows Alt and 0151."),
)


# A dash of something is a quantity in a kitchen and a dash between two phrases is a mark:
# "what does a dash of hot sauce mean" wants the measure, and the rule for joining words answered.
A_DASH_OF_SOMETHING = re.compile(r"\bdash(?:es)? of\b", re.I)


def _dash_is_the_mark(reading):
    """True when the line means the punctuation mark, not a dash of a liquid."""
    said = ""
    for name in ("plain", "clean", "text"):
        said = str((reading or {}).get(name) or "")
        if said:
            break
    return not A_DASH_OF_SOMETHING.search(said.lower())


def _dash_or_hyphen(memory, understood):
    """The dash the line names, or the rule that tells the two apart."""
    text = str((understood or {}).get("clean") or "").lower()
    for looks, reply in DASH_LOOKS:
        if _mentions(text, looks) or any(" " in look and look in text for look in looks):
            return reply
    return ("A hyphen joins words into one (well-known, two-year-old) and has no spaces. A dash "
            "separates a phrase for emphasis — like this — and British style usually spaces an en "
            "dash. Word processors can turn two hyphens into a dash for you.")


def _comma_rules(memory, understood):
    """The general rule, or the however one when that is the word the line names."""
    text = str((understood or {}).get("clean") or "").lower()
    if "however" in text:
        return ("Put the comma after however when it opens a sentence or a clause: 'However, the "
                "train was late.' It goes before it in the middle of one: 'the plan was fine, "
                "however late.' With two full sentences, a semicolon before and a comma after is "
                "tidier: 'I wanted to go; however, I was ill.'")
    return ("A comma marks a pause the sentence needs: between the items in a list (bread, milk, "
            "eggs), before and, but or which when a whole new clause follows, and around a name or "
            "an aside (my brother, who lives in Leeds, is coming). Read it aloud - if you would "
            "take a breath there, a comma usually belongs; if both halves could stand alone as "
            "sentences, use a full stop or a semicolon instead.")


def _end_mark(memory, understood):
    """Which mark ends the sentence the line asks about."""
    text = str((understood or {}).get("clean") or "").lower()
    if "question mark" in text or "questions mark" in text:
        return ("A question mark closes a direct question: 'where are you going?' Not an indirect "
                "one - 'she asked where I was going' keeps a full stop. One mark is enough, so "
                "never '?!' more than once in a piece of writing.")
    if "exclamation" in text:
        return ("An exclamation mark is for a real exclamation - surprise, shouting, a warning - "
                "and one per page is plenty. Use it instead of a full stop at the end of the "
                "sentence, never in the middle, and never more than one in a row.")
    return ("A full stop ends a statement, and every sentence needs one even when the next word "
            "carries on the thought. Use one rather than a comma where both halves could stand "
            "alone, and never put a space before it. A question takes a question mark and a real "
            "exclamation an exclamation mark.")


def _speak_clearly(memory, understood):
    """The filler, the mumble or the nerves: the one that is in the line."""
    text = str((understood or {}).get("clean") or "").lower()
    if _mentions(text, ("um", "ums", "erm", "er", "filler", "fillers", "like", "y'know")):
        return ("At the moment you feel an 'um' coming, close your mouth and breathe instead: a "
                "half-second of silence sounds calm and no one notices it, where a filler sounds "
                "like doubt. Record thirty seconds of yourself on your phone and count the fillers; "
                "most people halve them in a week just by hearing them once.")
    # "confidently" is the word the ask is typed with - "how do i speak more confidently" - and
    # _mentions only adds -s, -es, -ing and -ed, so it fell through to the pace sentence
    if _mentions(text, ("confident", "confidence", "confidently", "nervous", "nerves", "shaking",
                        "shaky", "wobble", "wobbly", "wavers")):
        return ("Slow down and pause at the full stops rather than at the commas, and look at one "
                "person for a whole sentence instead of sweeping the room - both read as "
                "confidence even when you are nervous. Write the first thirty seconds word for "
                "word and say it aloud five times, because getting started is the part nerves "
                "spoil.")
    return ("Slow to about two-thirds of your usual speed and finish the ends of words, which is "
            "most of what 'clear' means. Pause at the full stops instead of running the sentences "
            "together, drop your voice a little at the end of a sentence rather than letting it "
            "rise, and if you are on a call, stand up - it makes the voice carry.")


def _mentions(text, words):
    """A word, with its plural and its -ing allowed: the line says the thing, not the spelling."""
    said = re.findall(r"[a-z']+", text)
    for word in words:
        for form in (word, word + "s", word + "es", word + "ing", word + "ed"):
            if form in said:
                return True
    return False


# The everyday words and sayings people ask the meaning of: "what does ambiguous mean" and
# "what does it mean when someone says fair enough" were both heard as a request for a search
# on main. One table, one entry, keyed on the word itself - the same shape as GRAMMAR_TERMS
# below, because each of these is the same question: the meaning, then one example.
WORD_GLOSSES = {
    "ambiguous": "Ambiguous means it can be read two ways and you cannot tell which was meant: "
                 "'the meeting is at some point tomorrow' is ambiguous about the time.",
    "bittersweet": "Bittersweet is happy and sad in the same moment: the last day of a job you "
                   "loved, or a child's first day at school.",
    "cynical": "Cynical means expecting the worst of people's reasons - assuming a charity drive "
               "is really about publicity. It is different from sceptical, which just wants proof.",
    "mundane": "Mundane means ordinary and a bit dull: the mundane jobs like the washing up and "
               "the school run. It is not an insult to a person.",
    "serendipity": "Serendipity is a good thing found while looking for something else: finding "
                   "a twenty in an old coat, or meeting your best friend by taking the wrong bus.",
    "procrastinate": "To procrastinate is to put off what you meant to do today, usually by doing "
                     "something easier instead. It is about the delay, not about being lazy.",
    "gaslighting": "Gaslighting is making someone doubt their own memory of events: 'that never "
                   "happened, you're imagining it'. The point is to leave them unsure of themselves.",
    "condescending": "Condescending means talking down to someone, as if they were slower than "
                     "you: explaining the job to the person who has done it for ten years.",
    "patronising": "Patronising is the same talking-down, often with false kindness: 'well done "
                   "you!' to a competent adult. Condescending is the colder word for it.",
    "pretentious": "Pretentious means claiming more importance or taste than the thing deserves: "
                   "a menu that calls chips 'triple-cooked potato batons'.",
    "no worries": "'No worries' means it is fine and nothing is owed - an answer to an apology or "
                  "a thank you, not a warning. In Australia and New Zealand it is also the everyday "
                  "reply to 'thank you'.",
    "no hard feelings": "'No hard feelings' means you are not holding a grudge: 'you got the job and "
                        "I didn't, but no hard feelings'. It closes a disappointment without pretending "
                        "it did not sting.",
    "no offence": "'No offence' is a warning that the next thing is blunt, as in 'no offence, but the "
                  "kitchen is a mess'. It does not make an insult kind, so only say it if you would say "
                  "the same thing to their face.",
    "all good": "'All good' means nothing is wrong and there is nothing to apologise for - the relaxed "
                "answer to 'sorry I'm late' or 'thanks'. It is casual, so keep it out of a formal email.",
    "fair enough": "'Fair enough' means you accept the answer even if you would rather not - it "
                   "closes a small disagreement rather than starting one.",
    "ballpark figure": "A ballpark figure is a rough number, close enough to plan with: 'about "
                       "two thousand, give or take'. Ballpark on its own means roughly right.",
    "touch base": "To touch base is to check in briefly with someone: 'I'll touch base on Friday "
                  "about the timetable'. It is a short catch-up, not a meeting.",
    "in two minds": "To be in two minds is to be unable to choose: 'I'm in two minds about the "
                    "job'. The American version is 'on the fence'.",
    "on the fence": "To be on the fence is to have not decided yet: 'the council is still on the "
                    "fence about the bins'. Sitting on the fence means avoiding the choice.",
    "out of the loop": "To be out of the loop is to stop being told what is happening: 'I was on "
                       "leave, so I'm out of the loop on the merger'.",
    "red flag": "A red flag is a warning sign worth taking seriously: a deposit asked for before "
                "a viewing, or a new job with no contract.",
    "grey area": "A grey area is a case the rules do not clearly cover either way: taking a sick "
                 "day for a sick child. Grey in Britain, gray in America.",
    "catch 22": "A catch-22 is a rule you cannot win either way: you need experience to get the "
                "job, and you need the job to get the experience.",
    # "deja vu" is not here: main already explains it as a misfire in memory, which is a better
    # answer than the one line a gloss can give.
    "silver lining": "A silver lining is the small good thing inside a bad one: the flight was "
                     "cancelled, but you got an extra day with your family.",
    "cold feet": "To get cold feet is to lose your nerve just before a big step: the wedding is "
                 "booked and now you are panicking. It means doubt, not that you are ill.",
    "under the bus": "To throw someone under the bus is to blame them to save yourself: the "
                     "manager took the credit and then blamed the team when it failed.",
    "hindsight": "Hindsight is seeing what you should have done once it is too late: 'in hindsight "
                 "we should have booked earlier'. Hindsight is always 20/20 means it looks "
                 "obvious afterwards.",
    "cliche": "A cliche is a phrase so overused it has stopped meaning anything: 'thinking "
              "outside the box', 'at the end of the day'. Clichéd describes the phrase, not you.",
    "food for thought": "Food for thought is something worth thinking about: 'her talk on sleep "
                        "gave me food for thought'. Nothing to do with eating.",
    "the big picture": "The big picture is the whole situation rather than the detail: stepping "
                       "back to see whether the plan still makes sense.",
    # --- the words people meet in another language -----------------------------
    # "what does bonjour mean" and "what does adios mean" were both a search hedge while
    # "what does deja vu mean" answered: the table above holds English words and sayings, and
    # nothing told the bot that a greeting from another language is the same question - a plain
    # meaning and one line of use. Same table, same entry, same shape: the word, then what it
    # means and where it is said.
    "bonjour": "Bonjour is French for hello - literally 'good day'. You say it from morning until "
               "the evening, and bonsoir (good evening) after that.",
    "bonsoir": "Bonsoir is French for good evening. It takes over from bonjour once it gets dark, "
               "and it works both arriving and leaving.",
    "au revoir": "Au revoir is French for goodbye - literally 'until we see each other again'. "
                 "Bonjour when you arrive, au revoir when you go.",
    "merci": "Merci is French for thank you. Merci beaucoup is thank you very much, and the reply "
             "is je vous en prie or, informally, pas de problème.",
    "merci beaucoup": "Merci beaucoup is French for thank you very much - merci is thanks, "
                      "beaucoup is a lot.",
    "sil vous plait": "S'il vous plaît is French for please - literally 'if it pleases you'. Say it "
                      "when you ask for something, and merci when you get it.",
    "bon appetit": "Bon appétit is French for enjoy your meal - literally 'good appetite'. Said "
                   "before eating, the way people say 'enjoy' in English.",
    "ciao": "Ciao is Italian for hello and goodbye, both - you say it arriving and leaving. "
            "Arrivederci is the more formal goodbye.",
    "arrivederci": "Arrivederci is Italian for goodbye - literally 'until we see each other again'. "
                   "Ciao does the same job between friends.",
    "grazie": "Grazie is Italian for thank you. Grazie mille (a thousand thanks) is the warmer "
              "version, and prego is the reply - you're welcome.",
    "prego": "Prego is Italian for you're welcome - the answer to grazie. It also means 'please, "
             "go ahead' when someone waits for you to pass.",
    "hola": "Hola is Spanish for hello. It works all day, and buenos días (good morning), "
            "buenas tardes (afternoon) and buenas noches (evening) are the politer versions.",
    "adios": "Adiós is Spanish for goodbye. Hasta luego (see you later) is the softer way out of a "
             "conversation.",
    "gracias": "Gracias is Spanish for thank you. Muchas gracias is thanks a lot, and de nada is "
               "the reply - you're welcome.",
    "por favor": "Por favor is Spanish for please - literally 'by favour'. Gracias is the thank "
                 "you that goes with it.",
    "danke": "Danke is German for thank you. Danke schön is thanks a lot, and bitte is the reply - "
             "you're welcome, or please, depending on how it is used.",
    "bitte": "Bitte is German for please and for you're welcome, depending on the moment: bitte "
             "when you ask, bitte when you hand something over. Danke is thanks.",
    "auf wiedersehen": "Auf Wiedersehen is German for goodbye - literally 'until we see each other "
                       "again'. Tschüss is the casual version between friends.",
    "guten tag": "Guten Tag is German for good day - hello, in the middle of the day. Guten "
                 "Morgen is good morning and Guten Abend good evening.",
    "salud": "Salud is Spanish for health. It is the toast - the same job as 'cheers' - and also "
             "what you say after a sneeze.",
    "namaste": "Namaste is Hindi for hello and goodbye, said with the palms together. It means "
               "roughly 'I bow to you'.",
    "sayonara": "Sayonara is Japanese for goodbye. Konnichiwa is hello, and arigato is thank you.",
    "konnichiwa": "Konnichiwa is Japanese for hello - strictly good afternoon, though it works as a "
                  "general hello. Arigato is thank you.",
    "arigato": "Arigato is Japanese for thank you. Arigato gozaimasu is the politer, fuller form.",
    "ni hao": "Nǐ hǎo is Mandarin for hello - literally 'you good'. Xièxie (thank you) is the pair "
              "you will use most.",
    "buenos dias": "Buenos días is Spanish for good morning. Hola does for hello all day, and "
                   "buenas noches is good evening or good night.",
    "buenas noches": "Buenas noches is Spanish for good evening, and also good night when you go "
                     "to bed. Hasta mañana is see you tomorrow.",
    "hasta luego": "Hasta luego is Spanish for see you later - the everyday goodbye. Adiós is the "
                   "fuller goodbye, and hasta mañana means see you tomorrow.",
    "mucho gusto": "Mucho gusto is Spanish for pleased to meet you - literally 'much pleasure'. "
                   "The reply is igualmente, likewise.",
    "de nada": "De nada is Spanish for you're welcome - literally 'of nothing'. It answers "
               "gracias, the way 'no problem' does here.",
    "como estas": "Cómo estás is Spanish for how are you. The answer people expect is bien, "
                  "gracias (well, thanks).",
    "que pasa": "Qué pasa is Spanish for what's happening - a casual 'what's up'. Qué tal is the "
                "softer version.",
    "xiexie": "Xièxie is Mandarin for thank you. Bù kèqì (you're welcome) is the reply, and nǐ hǎo "
              "is hello.",
    "oui": "Oui is French for yes, and non is no. Oui, merci is yes please, which is the pair you "
           "will use most.",
    "d accord": "D'accord is French for okay or agreed - the sound of 'that's fine'. Say it to "
                "agree to a plan.",
    # people write it without the apostrophe and without the space
    "daccord": "D'accord is French for okay or agreed - the sound of 'that's fine'. Say it to "
               "agree to a plan.",
    "ca va": "Ça va is French for how are you, and also 'it's fine' as an answer. Ça va bien is "
             "'going well'.",
    "pas de probleme": "Pas de problème is French for no problem - both 'you're welcome' and "
                       "'that's fine'.",
    "je vous en prie": "Je vous en prie is French for you're welcome, and also 'please do' when "
                       "you hold a door. It answers merci.",
    "tschuss": "Tschüss is German for bye - the casual form between friends. Auf Wiedersehen is "
               "the formal goodbye.",
    "servus": "Servus is a greeting in southern Germany and Austria: hello, and also bye, depending "
              "on the moment.",
    "scheisse": "Scheiße is German for shit - the everyday swear word, used far more casually than "
                "in English, so hearing it is not as strong as it sounds.",
    "molto bene": "Molto bene is Italian for very good or very well - molto is very, bene is good.",
}


# The words people ask about one at a time and expect an answer for: the everyday British
# words, the ones the internet gave us, the words for feelings, and the work words that
# arrive in a letter. A separate table from WORD_GLOSSES above because they need a stricter
# entry: see EVERYDAY_WORD_MEANING below for why the guard is not on both.
EVERYDAY_WORDS = {
    # Two kinds of word were missing from this table, and both were heard the same way: as a
    # search hedge. The everyday informal words are the stronger gap, because a line that names
    # one of them was not a hedge at all but a *wrong* answer - "what does gutted mean" got the
    # bloating card from the "gut" in it, and "what does knackered mean" the tiredness card, so
    # the person was handed a page about their stomach instead of the word they asked about. The
    # word has to own its meaning, and the ask words in the entry keep a chat that only uses
    # the word from being turned into a dictionary.

    # --- the everyday British words, the ones a friend from elsewhere asks about ---
    "gutted": "Gutted means deeply disappointed: 'gutted I missed it'. It is the everyday British "
               "word for it - stronger than annoyed, milder than devastated.",
    "chuffed": "Chuffed means pleased: 'chuffed with the result'. Chuffed to bits is very pleased "
               "indeed, and not chuffed is put out.",
    "knackered": "Knackered means exhausted: 'knackered after the move'. It also means broken, as "
                 "in 'the washing machine is knackered' - the context tells you which.",
    "peckish": "Peckish means a bit hungry rather than starving: 'I'm peckish' is an invitation "
               "to a snack, not to a meal.",
    "dodgy": "Dodgy means unreliable or not to be trusted: a dodgy knee, dodgy wifi, a dodgy "
             "deal. It is a mild word, and it hedges - dodgy suggests you are not certain.",
    "cheeky": "Cheeky means pleasantly rude or a bit forward: a cheeky joke, a cheeky pint. Brits "
              "use it warmly as often as critically, so 'cheeky' is not an insult on its own.",
    "gobsmacked": "Gobsmacked means so surprised you cannot speak: 'gobsmacked when he turned up'. "
                  "Gob is slang for mouth, and you are smacked about it.",
    "faff": "A faff is a job with more fiddly steps than it is worth: 'the paperwork is such a "
            "faff'. To faff about is to spend time on small things instead of the real one.",
    "kerfuffle": "A kerfuffle is a fuss about something small: 'a right kerfuffle over the "
                 "seating'. It sounds more serious than it is.",
    "naff": "Naff means unfashionable or a bit cheap: naff souvenirs, a naff joke. It is a gentle "
            "dig rather than a real insult.",
    "nicked": "Nicked means stolen: 'someone nicked my bike'. It is also a narrow win - 'they "
              "nicked it 1-0' - and, in police talk, arrested.",
    "buzzing": "Buzzing means excited and delighted: 'buzzing for the trip'. It is the happy twin "
               "of dreading.",
    "niggling": "Niggling means small but persistent and hard to ignore: a niggling worry, a "
                "niggling pain. The size is not the point - the persistence is.",
    "miffed": "Miffed means mildly annoyed or put out: 'a bit miffed she wasn't asked'. Milder "
              "than angry, and usually about something small.",
    "cheesed off": "Cheesed off means fed up: 'cheesed off with the weather'. Brassed off and "
                   "browned off mean the same thing.",

    # --- the words the internet gave us, which people ask about in their own words ---
    "cringe": "Cringe is the wince you feel at someone else's embarrassment: 'watching him sing "
              "was pure cringe'. As a verb, the memory makes you cringe.",
    "salty": "Salty means bitter and sulky about losing or being left out: 'still salty about the "
             "game'. The food sense is the plain one - too much salt - so the joke is that the "
             "person is tasting tears.",
    "sus": "Sus means suspicious or not quite right, of a thing or a person: 'that email looks "
           "sus', 'he was acting sus all night'. It is short for suspicious.",
    "no cap": "'No cap' means no lie: 'it's the best one, no cap'. Cap is the lie and capping is "
              "exaggerating, so no cap is the promise that you mean it.",
    "vibes": "Vibes are the feeling a place or person gives off: 'good vibes', 'a bad vibe'. Not "
             "something you can measure, which is the point of the word.",
    "ghosting": "Ghosting is disappearing on someone without a word: no reply, no explanation, "
                "just silence. It is common enough in dating to have its own word.",
    "catfish": "To catfish is to invent an online identity to draw someone into a relationship: "
               "the person you have been talking to is not who the photos showed.",
    "doomscrolling": "Doomscrolling is scrolling bad news long after you have stopped taking it "
                     "in. The feed carries on; the mood does not recover.",
    "fomo": "FOMO is fear of missing out - the tug you feel seeing everyone else's weekend. It is "
            "said as a word, 'fomo', not spelled out.",
    "clickbait": "Clickbait is a headline written to get the click rather than to tell you "
                 "anything: 'you won't believe what happened next'.",
    "troll": "A troll is someone who posts to wind people up rather than to argue in good faith. "
             "Answering them is the contact they wanted.",
    "meme": "A meme is a joke or an idea copied and varied across the internet: one picture with "
            "a caption that people keep reworking.",

    # --- the words for feelings and for what people do to each other ---
    "empathy": "Empathy is feeling with someone - you can imagine how it is from inside their "
               "side. Sympathy is feeling sorry for them, which is kind but stands further away.",
    "sympathy": "Sympathy is feeling sorry for someone's trouble and saying so: 'you have my "
                "sympathy'. Empathy is the one where you feel it with them.",
    "apathy": "Apathy is not caring when caring would be reasonable - the flat 'what's the "
              "point'. It is not the same as being calm or easy-going.",
    "ambivalent": "Ambivalent means holding both feelings at once: wanting the job and dreading "
                  "it. It does not mean you do not care.",
    "indifferent": "Indifferent means it genuinely makes no difference to you either way. Being "
                   "indifferent is flatter than disliking something.",
    "boundaries": "A boundary is a limit you set on what you will do or accept: 'I don't answer "
                  "work messages after eight'. It is a rule for yourself, not a demand on someone "
                  "else - which is why saying it out loud is the hard part.",
    "closure": "Closure is the sense of an ending that lets you stop going over something: an "
               "explanation, an apology, a last conversation. Plenty of people never get it, and "
               "you can still move on without it.",
    "narcissist": "A narcissist is someone with an inflated sense of their own importance and "
                  "little room for other people's feelings. The word is used loosely in ordinary "
                  "talk; as a diagnosis it is a specific personality disorder, and only a "
                  "professional can make it.",
    # "gaslight" is not here: WORD_GLOSSES above already holds "gaslighting" for the same thing,
    # and one word, one row - two definitions of it only race each other.
    "validation": "Validation is being told that what you feel or did makes sense: 'that's "
                  "reasonable'. People want it because being disbelieved is a sting of its own.",

    # --- work words, since a letter from an employer is where most people meet them ---
    "redundancy": "Redundancy is losing your job because the role is going, not because of "
                  "anything you did: the work is cut, moved or merged. It usually means notice "
                  "plus a statutory payment based on your age and length of service.",
    "furlough": "Furlough is a temporary lay-off where your employer keeps your job but stops "
                "paying you - or the state pays part of your wage through the employer.",
    "appraisal": "An appraisal is the regular sit-down where your manager goes over your work: "
                 "what went well, what to change, and sometimes pay. Bring your own list of what "
                 "you did.",
    # "notice period" is not here: its own row already answers the length question, and it reads
    # better than a definition ("your contract decides the length - usually a week to three
    # months").

    # --- the plainer words people ask about rather than look up ---
    "paradox": "A paradox is a statement that seems to contradict itself but may still be true: "
               "'the more you learn, the less you know'.",
    "hypothetical": "Hypothetical means imagined rather than real: 'hypothetically, if I left'. "
                    "People use it to ask a question without owning it.",
    "arbitrary": "Arbitrary means decided without a rule or reason: an arbitrary deadline, an "
                 "arbitrary number. It is a criticism of how the choice was made.",
    "mitigate": "To mitigate is to make something less bad: extra drainage mitigates flooding. Do "
                "not confuse it with 'militate', which means to weigh against.",
    "inertia": "Inertia is the tendency to carry on as you were: in physics, an object's "
               "resistance to a change of movement; at home, the reason a routine outlasts its "
               "point.",
    "reiterate": "To reiterate is to say something again, usually to be sure it was heard: 'let "
                 "me reiterate the deadline'.",
    "satire": "Satire uses humour to mock something in order to change it: a sketch that makes a "
              "habit ridiculous. It is aimed at the powerful, which is what separates it from a "
              "joke at someone's expense.",
    "sarcasm": "Sarcasm is saying the opposite of what you mean with a bite to it: 'great, "
               "another meeting'. Irony is the wider pattern; sarcasm is aimed at a person.",
    "stereotype": "A stereotype is a fixed, over-simple picture of a group, applied to individuals "
                  "who may not fit it at all.",
    "prejudice": "Prejudice is judging before you know: a set view about a group of people, held "
                 "regardless of what they are actually like.",
    "discrimination": "Discrimination is treating someone worse because of who they are - their "
                      "sex, race, age, disability, religion and so on - rather than what they do.",
    "consent": "Consent is a clear yes, given freely, and it can be taken back at any point. "
               "Someone asleep, too drunk to follow what is happening, or being pressured cannot "
               "give it.",
    "placebo": "A placebo is a treatment with no active ingredient in it. People often improve "
               "anyway, which is the placebo effect, and it is why trials compare against one.",
    "kudos": "Kudos is praise and credit for something done: 'kudos for getting through that'. "
             "It is uncountable - you get kudos, not a kudo.",
    "schadenfreude": "Schadenfreude is pleasure at someone else's bad luck - German for "
                     "'harm-joy', and borrowed because it names the feeling exactly.",
    "zeitgeist": "Zeitgeist is the mood of a period: the ideas and tastes that feel typical of "
                 "the time. German for 'time-spirit'.",
}


# A definition answers only a line that asks for one. The entry's ask words are a soft filter: a
# line that names the word and wants *anything* reached it, so "im knackered all the time, what
# helps" got the meaning of knackered where the tiredness card had the answer, and "what is the
# best way to get out of a redundancy" the meaning where the question was what to do. A guard is
# the hard fence, and it takes the two shapes a meaning question actually has: the ask around the
# word ("what does gutted mean", "define faff", "the meaning of kudos"), and a plain "what is X"
# that says nothing else ("what is a narcissist") - because "what is the boundary between my
# garden and next door" is a question about the boundary, not about the word.
_A_MEANING_IS_ASKED = re.compile(
    r"\bwhat\s+(?:does|do|did)\b[^?.!]{0,40}?\bmean(?:s|ing)?\b"      # what does gutted mean
    r"|\bmean(?:s|ing|ings)?\s+of\b"                                  # the meaning of kudos
    r"|\bdefin(?:e|ed|ing|ition|itions)\b"                            # define faff
    r"|\bstands?\s+for\b"                                             # what does FOMO stand for
    r"|\brefers?\s+to\b",                                             # what does kudos refer to
    re.I)

# The lead of a plain definition question, and the words allowed between it and the word itself.
_WHAT_IS = ("what", "whats", "what's", "who", "whos", "who's", "explain", "define",
            "meaning")
_FILLER = frozenset(("is", "are", "was", "were", "s", "a", "an", "the", "of", "mean",
                     "means", "meant", "exactly", "actually", "please", "word", "term"))


def _asks_what_a_word_means(understood):
    """True when the line is asking what a word or saying means, not using it."""
    if not isinstance(understood, dict):
        return False
    clean = str(understood.get("clean") or "")
    if clean and _A_MEANING_IS_ASKED.search(clean):
        return True
    # "what is a narcissist" is the word and nothing else; "what is the best way to clean a sofa"
    # names a sofa on the way to asking something else, and the gloss table has no business there.
    words = [str(word).lower() for word in (understood.get("words") or ())]
    if not words or len(words) > 6:
        return False
    while words and (words[0] in _WHAT_IS or words[0] in _FILLER):
        words = words[1:]
    return len(words) == 1 or " ".join(words) in EVERYDAY_WORDS


def _same_word(phrase, said):
    """The table's word and the word the line said, allowing a regular ending.

    The key is written once and people say it in any form: the row is keyed on "boundaries" and
    the line says "boundary", which the scoring already reads as the same word, so the reply has
    to as well - otherwise the row is chosen and then has nothing to say, and the person got the
    fallback ("I can take a single word apart...") about a word the table holds. Only a regular
    ending counts, and only where no key is the word itself: an exact key always wins, so the
    table's own "gaslighting" is not read as "gaslight".
    """
    if len(phrase) < 4 or len(said) < 4:
        return False
    for ending in ("s", "d", "ed", "es", "ing", "ings"):
        if said == phrase + ending or phrase == said + ending:
            return True
    # a plural that changes the y: "boundary" is the word, "boundaries" is how it is often said
    if phrase.endswith("y") and said == phrase[:-1] + "ies":
        return True
    if said.endswith("y") and phrase == said[:-1] + "ies":
        return True
    return False


def _word_meaning(memory, understood, tables=(WORD_GLOSSES, EVERYDAY_WORDS)):
    # the words as words, like the grammar table: a substring test would answer "cold" inside
    # "cold feet" and "red" inside "bored".
    said = [str(word).lower() for word in ((understood or {}).get("words") or ())]
    flat = " ".join(said)
    # An exact key first, across every table: a word the table spells the way the line does is
    # that word, and an ending is only the second look.
    for table in tables:
        for phrase, reply in table.items():
            if phrase in said or (" " in phrase and phrase in flat):
                return reply
    for table in tables:
        for phrase, reply in table.items():
            if " " not in phrase and any(_same_word(phrase, word) for word in said):
                return reply
    return ASK_FOR_THE_WORD


# The reply when no table holds the word. It is the fallback rather than a definition, so a row
# that finds nothing here has nothing to say and has to stand down - see `_an_everyday_word`.
ASK_FOR_THE_WORD = ("I can take a single word or saying apart if you give me the one you are "
                    "stuck on - the meaning, then an example of it in a sentence.")


def _an_everyday_word(memory, understood):
    """The everyday table's definition, or None when the table has not got the word.

    The row's fence reads the shape of the line ("what does X mean", "define X"), and that shape
    is the same for every word there is: "what does gut mean" and "what does mean time mean" are
    that asks with words the table does not hold. Answering them with the sentence that asks for
    a word hands back an ask for the very word the person just gave - and on main the first was
    the bloating card and the second the honest hedge, so the row has to stand down and let the
    other rows read the line as they did before.
    """
    reply = _word_meaning(memory, understood, (EVERYDAY_WORDS,))
    return None if reply == ASK_FOR_THE_WORD else reply

def _paragraph(memory, understood):
    """What a paragraph is, or how long one is: the length ask wants the number first."""
    text = str((understood or {}).get("clean") or "").lower()
    if "how long" in text or "how many words" in text or "how much" in text:
        return ("Three or four sentences, about 60 to 100 words, is a good paragraph: long enough "
                "to make one point and short enough to take in at a glance. Start a new one when "
                "you move to a new idea, and if one runs past a screenful, split it where the "
                "subject changes.")
    return ("A paragraph is one idea in three or four sentences, about 60 to 100 words: long "
            "enough to make the point and short enough to take in at a glance. Start a new one "
            "when you move to a new idea, and if one runs past a screenful, split it where the "
            "subject changes.")


# ---------------------------------------------------------------------------------------------
# Asking for more time on a piece of work is one subject with a handful of shapes, and main
# answered most of them with something else. "how do i get an extension on an assignment" and "i
# missed the deadline for my essay" got the essay-plan card (list three points, write the body
# first), "can i get an extension on my dissertation" the dissertation card, "how do i get extra
# time in an exam" the revising card, and "how do i keep track of deadlines" was a shrug. The row
# that already answered "how do i ask for an extension" is this one, so the shapes are branches of
# it rather than a second row: asking before, asking after a no, having missed it, exam access
# arrangements, the extenuating-circumstances form, and the dates in the first place.
_EXT_WORDS = ("deadline", "deadlines", "extension", "extensions", "extend", "extended",
              "more time", "extra time", "late submission", "late work", "late",
              "extenuating circumstances", "mitigating circumstances", "mitigation",
              "exemptions", "exemption")
_EXT_SUBJECTS = ("essay", "assignment", "coursework", "dissertation", "thesis", "project",
                 "exam", "exams", "test", "tests", "tutor", "lecturer", "professor", "teacher",
                 "uni", "university", "college", "school", "course", "module", "marks", "mark",
                 "grade", "grades", "submit", "submission", "hand in", "hand it in", "handing")
_EXT_ILL = ("ill", "illness", "sick", "hospital", "bereavement", "died", "death", "funeral",
            "depressed", "anxiety", "mental health", "family emergency", "unwell", "flu",
            "covid", "migraine")


# "late" is this row's word for work that is past its date, and it is also the ordinary word
# for a bus, a school run and being too old to start something. So a line whose only deadline
# signal is "late" answers here only when it also names the work that is late. A school, a
# tutor or a teacher is not enough on its own: a child who is late for the school run names
# all three, and "is it too late to get any good" at 41 names none.
_EXT_LATE = re.compile(r"\blate\b")
_EXT_LATE_WORK = ("essay", "assignment", "coursework", "dissertation", "thesis", "project",
                  "exam", "exams", "test", "tests", "course", "module", "submission",
                  "submitted", "submit", "hand in", "handed in", "handing", "marks", "mark",
                  "grade", "grades", "deadline", "deadlines", "extension", "extensions",
                  "due in", "was due", "overdue", "late work", "late submission")


def _late_names_the_work(understood):
    """True unless the line's only sign of a deadline is the bare word "late"."""
    text = ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not _EXT_LATE.search(text):
        return True
    return any(word in text for word in _EXT_LATE_WORK)


def _a_deadline_extension(memory, understood):
    line = ((understood or {}).get("text") or "").lower()
    # "am i too late to get any good" is a doubt about a skill the person has just taken up, not
    # coursework: no essay, exam or course is named, and "late" only matched this row's word.
    if re.search(r"\b(?:too late|too old) to (?:get|be|become) "
                 r"(?:any )?(?:good|better|decent|anywhere)\b", line) \
            and not any(word in line for word in _EXT_SUBJECTS):
        return None
    if any(w in line for w in ("said no", "says no", "refused", "refuses", "turned me down",
                               "said i cant", "said i can't", "wouldnt give", "wouldn't give")):
        return ("Ask again in writing, once, with the date and the evidence attached - a refusal "
                "at the desk is often the person, not the rule. Then go up one step: the module "
                "leader, then the extenuating-circumstances route, which is a form the university "
                "has to consider separately from the tutor's answer. Hand in the best version you "
                "have by the original date whatever happens, because a late mark beats a zero.")
    if any(w in line for w in ("missed", "miss", "was due", "is late", "in late", "already late",
                               "past the deadline", "overdue", "didnt hand in", "didn't hand in",
                               "nowhere near done", "not done", "ran out of time", "havent done",
                               "haven't done")):
        return ("Email the tutor today, before they mark it: the date you can deliver, what you "
                "have done so far, and the reason in one sentence. Universities cap late work "
                "rather than refusing it, so a complete essay handed in now usually beats a "
                "perfect one next month - and if the reason is illness or a bereavement, ask for "
                "the extenuating-circumstances form as well, because that can lift the cap.")
    if any(w in line for w in ("extra time", "access arrangements", "special arrangements",
                               "dyslexia", "adhd", "extra 25", "rest breaks")):
        return ("Extra time in an exam is arranged months in advance, not on the day: the exams "
                "office needs evidence - a diagnosis, or a history of extra time at school - and "
                "the deadline is usually early in the year. Go to the disability or study-support "
                "service with any report you have and ask what you qualify for; 25 per cent extra "
                "time and rest breaks are the common ones, and the application is theirs to make.")
    if any(w in line for w in ("extenuating", "mitigating", "ec form", "special circumstances")):
        return ("Ask the school or module office for the extenuating-circumstances form the same "
                "week, and fill it in yourself: what happened, the dates it covered, and the "
                "evidence - a doctor's note, a hospital letter, a death notice. It goes to a "
                "panel rather than to your tutor, and it is the route that protects the mark or "
                "gives you another attempt; an extension only moves the date. Keep a copy, and "
                "note the deadline for the form, which is usually days after the assessment.")
    if any(w in line for w in _EXT_ILL):
        return ("Ask for the extension in writing now, name what happened in one line, and attach "
                "the evidence you have - a doctor's note, a hospital letter. Then ask the office "
                "for the extenuating-circumstances form: that is the route that protects the mark "
                "itself, while an extension only moves the date. Do it the same week, because "
                "most deadlines for that form are days, not weeks, after the assessment.")
    if any(w in line for w in ("keep track", "track of", "track my", "organise", "organize",
                               "planner", "diary", "reminder")):
        return ("Put every deadline in one place the day you get it - a paper week-to-view diary "
                "or the calendar on your phone - and write each one a week early as well as on "
                "the day. Then work backwards: the day you must start, not the day it is due. "
                "Five minutes every Monday moving the next fortnight into view is what stops the "
                "surprise, and check the same page for the exam dates.")
    return ("Ask before the deadline, say how much more time you need and what you'll deliver: "
            "\"I'm not going to do this justice by Friday. Could I have until Tuesday? I'd then "
            "send the finished draft rather than a thin one.\" A specific new date does the work "
            "— no long explanation of why you're behind.")
# Brackets are a punctuation mark and also a place a number is broken into: "expand the brackets",
# "the tax bracket I am in", "the 40k bracket". The maths and the money reading is not this row, so
# the fence is on the line as typed, and a digit anywhere is enough to stand it down.
_NOT_MATHS_BRACKETS = re.compile(
    r"\b(expand|expanding|simplify|simplifying|multiply|multiplying|factorise|factorize|"
    r"factorising|solve|solving|remove|removing)\b|\d|\bx\b|\bxy\b|\bequals\b|"
    r"\btax\b|\bincome\b|\bsalary\b|\bband\b|\bprice\b|\bpay\b|\bage\b|"
    r"\bearn\b|\bcup\b|\bround\b|\btournament\b|\bleague\b|\bcompetition\b|"
    # school maths is the other module's own reading: "what is a bracket in algebra", "i dont
    # understand brackets" and "double brackets" are the multiplication, not the mark.
    r"\balgebra\b|\balgebraic\b|\bmaths\b|\bmath\b|\bequations?\b|\bsimplif\w*\b|"
    r"\bpowers?\b|\bterms?\b|\bcoefficients?\b|\bnegatives?\b|\bdouble\b|\btriple\b|"
    r"\bunderstand\b|\bmultiply out\b|\bsums?\b|\bcalculate\b|\bexpressions?\b|"
    r"\bworking out\b|\bwork out\b|"
    r"\bteam\b|\bteams\b|\bplayer\b|\bplayers\b|\bknockout\b|\bqualify\b|"
    r"\bfixture\b|\bmatch\b|\bmatches\b|\bdraw\b|\bgroup\b|\bengland\b|"
    r"\bscotland\b|\bwales\b|\bireland\b|\bfinal\b|"
    # a thing fixed to a wall has a bracket too, and "what size screw for a tv bracket" was
    # answered with where the brackets go round an aside. Whatever is being fixed is the other
    # question's, so the mark keeps its answer only when nothing is being hung.
    r"\bshel(?:f|ves)\b|\bwall\b|\btv\b|\btelevision\b|\bscrews?\b|\bdrill\b|"
    r"\bfixings?\b|\bcurtains?\b|\bblinds?\b|\bmonitor\b|\bspeakers?\b|\baerial\b|"
    r"\bcupboard\b|\bwardrobe\b|\bmount\b|\bmounted\b|\bhinge\b|\bgate\b|"
    r"\bradiators?\b|\bboiler\b|\btoilet\b|\bsink\b|\bcarrier\b|\btowel rail\b")

# A bracket is also a piece of metal: a telly bracket, a shelf bracket, a curtain rail's. The one
# the person is asking about is the one the chat is on, and the reading keeps the turn before, so
# a hardware word anywhere in it stands the punctuation card down - "i want to put the tv on the
# wall" then "what bracket do i need" is not a question about a mark.
_NOT_A_PUNCTUATION_BRACKET = re.compile(
    r"\b(wall|walls|shelf|shelves|shelving|tv|telly|television|tvs|monitor|monitors|speaker|"
    r"speakers|soundbar|radiator|radiators|curtain|curtains|rail|rails|blind|blinds|pipe|pipes|"
    r"plasterboard|stud|studs|drill|screws?|screwdriver|fixings?|rawl|mount|mounts|mounted|"
    r"mounting|cistern|sink|boiler|cabinet|cabinets|wardrobe|mirror|aerial|satellite|dish|"
    r"hinges?|fence|post|posts|beam|joists?|trellis|gutter|guttering|bathroom|kitchen)\b")
# A buying frame asks for the object as well: "what bracket do i need", "which bracket should i
# buy". No question about a mark is put that way, and if the line also has a writing word in it
# ("when do i need brackets in a sentence") the mark wins - that is what the escape above is for.
_BUYING_BRACKETS = re.compile(
    r"\bneed(s|ed)?\b|\bshould i (?:get|buy|use)\b|\bbuy\b|\bwhat size\b|\bwhich one\b")
_WRITING_BRACKETS = re.compile(
    r"\bsentences?\b|\bwriting\b|\bwrote\b|\bgrammar\b|\bpunctuat\w*\b|\bessays?\b|"
    r"\bparagraphs?\b|\bcomma\b|\bsemicolon\b|\bquote\b|\bquotes\b|\bspell\w*\b|"
    r"\btext\b|\bword\b|\bwords\b|\bmarks?\b|\bmean\b|\bmeans\b|\benglish\b|"
    r"\bwriter\b|\bdraft\b|\bcopy\b|\bedit\w*\b|\bproofread\w*\b|\bstyle\b")


def _brackets_are_punctuation(reading):
    """True when the line means the mark, not a sum, a band of money or a piece of metal."""
    said = ""
    for name in ("plain", "clean", "text"):
        said = str((reading or {}).get(name) or "")
        if said:
            break
    low = said.lower()
    if _WRITING_BRACKETS.search(low):
        return True  # the line says writing, so the mark is what it is asking about
    if _NOT_A_PUNCTUATION_BRACKET.search(low) or _BUYING_BRACKETS.search(low):
        return False
    return not _NOT_MATHS_BRACKETS.search(low)


def _ellipsis_reply(memory, understood):
    return ("An ellipsis is three dots (...) and it means something has been left out or left "
            "hanging: a sentence that trails off, a pause, or words cut from a quote. Use it once "
            "in a while, not as a habit, and in British style it closes up to the word before it: "
            "'I was going to...'")


def _speech_marks_reply(memory, understood):
    return ("Speech goes in double quotation marks, and a quote inside a quote takes single ones: "
            "'She said \"I am coming\" and left.' The full stop or comma goes inside the closing "
            "mark when it belongs to the speech, and every new speaker starts a new line. Do not "
            "close the marks and carry the same speech on after a comma.")


def _list_reply(memory, understood):
    text = str((understood or {}).get("clean") or "").lower()
    if "bullet" in text:
        return ("A bulleted list needs the same lead-in for every line and no full stops if the "
                "lines are fragments: 'Bring:' then 'milk', 'eggs', 'bread'. Capitalise each line "
                "or none, and keep the grammar parallel - all nouns or all verbs, not a mix.")
    return ("A list inside a sentence takes commas, and semicolons when the items have commas of "
            "their own: 'we need flour, which is in the cupboard; eggs, which are in the fridge; "
            "and milk.' A colon introduces the list, and never after a verb: 'the things I need "
            "are milk, eggs and bread', not 'are: milk'.")

# The -us family: English gives them -es, and the old Latin -i is still in use beside it. One
# sentence for both rows that answer about it, so the pair cannot drift apart.
_PLUSES_REPLY = ("Octopuses is right in English, and octopi is the older Latin-style plural "
                 "plenty of people still use. The same -uses ending covers viruses, cactuses and "
                 "walruses; crises and analyses keep the Latin -es.")


_PLUS_FORMS = ("octopus", "octopuses", "octopi", "cactus", "cactuses", "cacti",
               "walrus", "walruses", "virus", "viruses")



def _offers_two_of_the_family(line):
    """True when the line holds two of those forms, as "is it octopuses or octopi" does.

    A shape reads the line as it was typed, so this counts spellings rather than words of the
    key: the question is which of the two to use, and one spelling on its own is not that
    question - it is the plural row's, or this row's without a plural to choose.
    """
    return len({word for word in line.split() if word in _PLUS_FORMS}) > 1


def _asks_which_of_the_two(understood):
    """True when the line offers two forms and asks which: "octopuses or octopi"."""
    return "or" in _the_words_of(understood)


# One answer for both words was written simile-first, so "what is a metaphor" opened with a
# sentence about similes: the definition asked for was the second one, and a person who does not
# know the word has no way to tell which half answers them. The row speaks about whichever of the
# two was named, and the pair answer only when both were (or neither was).
_THE_TWO_FIGURES = {
    "metaphor": ("A metaphor says a thing is another thing (her laugh was a kettle, the office is "
                 "a zoo), so the picture does the work without a 'like' in front of it. A simile "
                 "does put one in: her laugh was like a kettle. Both paint a picture; the "
                 "metaphor just claims it outright."),
    "simile": ("A simile compares one thing to another with like or as (her laugh was like a "
               "kettle, as busy as a bee). A metaphor skips those two words and says the thing "
               "is the other one (her laugh was a kettle). Both paint a picture; the simile keeps "
               "the comparison out in the open."),
}


def _the_figure_that_was_named(memory, understood):
    reading = understood or {}
    said = " ".join(str(reading.get(k) or "")
                    for k in ("clean", "text", "line", "norm_text")).lower()
    named_metaphor = "metaphor" in said
    named_simile = "simile" in said
    if named_metaphor and not named_simile:
        return _THE_TWO_FIGURES["metaphor"]
    if named_simile and not named_metaphor:
        return _THE_TWO_FIGURES["simile"]
    return ("A simile compares with like or as (her laugh was like a kettle), and a metaphor says "
            "it is the thing (her laugh was a kettle). Both make a picture; the metaphor just "
            "does it without the 'like'.")


ENTRIES = [
    # --- the words people mix up -------------------------------------------
    entry("affect-effect", (("affect", "affects", "affected"), ("effect", "effects")),
          "Affect is the verb and effect is the noun: the weather affects my mood, and the "
          "weather has an effect on my mood. A useful memory: 'cause and effect' is always the "
          "noun."),
    entry("its-its", (("its",), ("apostrophe", "difference", "correct", "grammar", "punctuation"),
                      ("its or it's", "it's or its")),
          "It's with an apostrophe always means 'it is' or 'it has': it's raining, it's been ages. "
          "Everything else is its, no apostrophe: the cat licked its paw. If you can swap in 'it "
          "is' and the sentence still works, use it's."),
    entry("your-youre", (("your",), ("youre", "apostrophe", "difference", "grammar"),
                         ("your or you're", "you're or your")),
          "You're means 'you are', so 'you're welcome' and 'you're late' take it. Your shows "
          "ownership: your coat, your turn. Read the sentence with 'you are' in it; if that sounds "
          "wrong, use your."),
    entry("their-there", (("their", "theirs"), ("there", "theyre", "apostrophe", "difference"),
                          ("their or there", "there or their", "their there theyre")),
          "They're means 'they are', their means it belongs to them, and there is a place or 'there "
          "is'. So: they're late, their car, over there. In a hurry, ask what the word is doing: "
          "person, owner or place."),
    entry("fewer-less", (("fewer",), ("less",)), _fewer),
    entry("lose-loose", (("lose", "losing", "lost"), ("loose", "looser")),
          "Lose has one o and means not winning or not being able to find something; loose has two "
          "and means not tight. Your trousers are loose, and you might lose them."),
    entry("then-than", (("then",), ("than",)),
          "Then is about time, than is about comparing: we ate, then we walked; she is taller than "
          "me. If you can put 'at that time' in place of it, it's then."),
    entry("could-of", (("could've", "could of", "should of", "would of", "couldve", "shouldve"),
                       ("could have", "should have", "would have", "correct", "grammar", "write",
                        "spell", "wrong")),
          "It's 'could have', usually shortened to could've, never 'could of'. The same goes for "
          "should've and would've: the sound is 'of' but the word is 'have'."),
    entry("practice-practise", (("practice",), ("practise", "advice", "advise")),
          "In British English the noun is practice and the verb is practise: piano practice, but I "
          "practise every day. Advice and advise work the same way: advice is the thing, advise is "
          "what you do. In American English practice does both jobs."),
    entry("who-whom", (("whom",), ("who",)),
          "Whom is only for the object of a sentence, and in everyday writing who is almost always "
          "fine. Use whom after a preposition, as in 'to whom it may concern' or 'for whom'. If it "
          "sounds stiff, rewrite the sentence instead."),
    entry("complement-compliment", (("complement",), ("compliment",)),
          "A compliment is praise; a complement completes something, like a wine that complements "
          "the meal. 'Complimentary' means free, which is why hotel soap is complimentary."),
    entry("amount-number", (("amount",), ("number", "much", "many")),
          "Use number for things you can count and amount for things you can't: a number of "
          "people, a large amount of work. 'Amount of people' is the usual slip."),
    entry("ie-eg", (("ie", "eg"), ("difference", "mean", "use")),
          "e.g. means 'for example' (think 'example given') and i.e. means 'that is' (a "
          "restatement). Both take full stops in British style, and both want a comma after them."),
    # "is it X or Y" pairs. Two words of the key have to be in the line, so a sentence
    # that uses only one of them ("we live apart", "i passed the test") is left alone; ASK
    # then makes sure the line is actually asking about the words, not using them.
    entry("alot-a-lot", (("alot",),
                         ("a lot", "one word", "two words", "spell", "spelling", "correct",
                          "write", "writing", "wrong", "is it", "should it be")),
          "It is always two words: a lot. 'Alot' is not a word, so if you would write 'a lot of "
          "'people' or 'a lot better', put the space in."),
    entry("to-too", (("too",), ("to",)),
          "To is the direction or the infinitive - to the shop, to run. Too means also or more "
          "than you want - I want to come too, it's too late. If you could swap in 'also' or "
          "'very', it's too.",
          avoid=("tired", "late", "much", "many", "young", "old", "big", "small", "hot", "cold",
                 "fast", "slow", "early", "expensive", "busy", "hard", "long", "far", "loud",
                 "noisy", "heavy", "sweet", "salty", "sharp", "tough", "soon", "often", "close",
                 # "is it too <weather word> to <go out>" is a question about the day, not about
                 # spelling: "is it too windy to put the parasol up" was told the to/too rule
                 # because the line holds both words. Any adjective after "too" is the answer to
                 # some other question, so the weather words and the things people do outdoors
                 # stay out of the spelling row.
                 "windy", "wind", "rainy", "rain", "raining", "sunny", "snowy", "snow", "wet",
                 "dry", "cloudy", "foggy", "misty", "stormy", "chilly", "warm", "cool",
                 "freezing", "boiling", "dark", "bright", "mild", "humid", "muggy", "frosty",
                 "parasol", "umbrella", "washing", "laundry", "washing line", "barbecue", "bbq",
                 "picnic", "bike", "bicycle", "cycle", "ride", "walk", "hike", "garden",
                 "outside", "outdoors", "dog", "run", "running", "plant", "plants", "paint"),
          # "is it" on its own was the whole of this ask, and it is the opening of every weather
          # question there is: the ask has to be about the words themselves.
          ask=("difference", "correct", "spell", "spelling", "grammar", "should it be",
               "do i use", "to or", "or too", "too or", "when do i use", "which is right",
               "is it spelled", "is it spelt", "spelt", "spelled")),
    entry("quiet-quite", (("quiet",), ("quite",)),
          "Quiet means little noise - a quiet street. Quite means fairly or completely - quite "
          "good, quite sure. The e and the t swap places, so check which word you meant, not "
          "which one looks right.",
          ask=("is it", "difference", "correct", "spell", "spelling", "grammar", "should it be",
               "do i use", "quiet or", "or quite")),
    entry("apart-a-part", (("apart",), ("a part",)),
          "Apart means separated - we live apart, take it apart. A part means one piece of "
          "something - a part of the team, a part of the problem. If you can drop the 'a', it's "
          "apart.",
          ask=("is it", "difference", "correct", "spell", "spelling", "grammar", "should it be",
               "do i use", "apart or", "or a part")),
    entry("everyday-every-day", (("everyday",), ("every day",)),
          "Every day, two words, means each day - I walk every day. Everyday, one word, is the "
          "adjective for ordinary - everyday shoes. If you can say 'each day', keep the space.",
          ask=("is it", "difference", "correct", "spell", "spelling", "grammar", "should it be",
               "do i use", "everyday or", "or every day")),
    entry("anyway-any-way", (("anyway",), ("any way",)),
          "Anyway means in any case - anyway, I went home. Any way means any method - is there "
          "any way to fix it. If you can put 'in any case' there, it's one word.",
          ask=("is it", "difference", "correct", "spell", "spelling", "grammar", "should it be",
               "do i use", "anyway or", "or any way")),
    entry("onto-on-to", (("onto",), ("on to",)),
          "Onto is one word when something moves onto a surface - he climbed onto the roof. Keep "
          "them apart when 'on' belongs to the verb - we carried on to the next town, hold on to "
          "it. If you can't move the 'on' away, it's one word.",
          ask=("is it", "difference", "correct", "spell", "spelling", "grammar", "should it be",
               "do i use", "onto or", "or on to")),
    entry("altogether-all-together", (("altogether",), ("all together",)),
          "All together means everyone in one place - we sang all together. Altogether means "
          "completely or in total - that's altogether different, ten pounds altogether.",
          ask=("is it", "difference", "correct", "spell", "spelling", "grammar", "should it be",
               "do i use", "altogether or", "or all together")),
    entry("desert-dessert", (("desert",), ("dessert",)),
          "Dessert is the sweet course, and it has two s's because you want more of it. Desert, "
          "one s, is sand or the verb to abandon; the stress moves too - DESSert, deSERT."),
    entry("stationery-stationary", (("stationery", "stationary"), ("stationary", "stationery")),
          "Stationery with an e is paper and pens - remember e for envelope. Stationary with an "
          "a is not moving - a stationary car."),
    entry("principal-principle", (("principal",), ("principle",)),
          "Principal means main or the head of a school; principle is a rule or belief - it's the "
          "principle of the thing. The school one is your pal: principAL, the princiPAL."),
    entry("passed-past", (("passed",), ("past",)),
          "Passed is the verb - I passed the shop, she passed the exam. Past is time before now, "
          "or beyond something - in the past, walk past the bank."),
    entry("whose-whos", (("whose",), ("who's", "whos")),
          "Whose asks who owns it - whose coat is this. Who's is short for who is or who has - "
          "who's coming? If you can say 'who is', put the apostrophe in."),
    entry("me-or-i", (("between you and i", "between you and me", "me or i", "i or me",
                       "than i", "than me", "him and me", "he and i", "him or me", "he or i",
                       "my husband and me", "my friend and me", "my friend and i",
                       "me and my"),
                      # not "say" or "use": those are ordinary words in any sentence, and they
                      # let "my husband and me are going to have a baby, what should we say to my
                      # mum" into the grammar answer. The phrase pair is what names this question.
                      ("or", "correct", "grammar", "right", "wrong")),
          "Use 'me' after a preposition or when you're the one being acted on: between you and me, "
          "she phoned me. Use 'I' only as the subject of the verb: my sister and I went. 'Between "
          "you and I' is the mistake people over-correct into."),
    entry("advice-advise", (("advice",), ("advise", "difference", "spell", "correct", "use")),
          "Advice is the noun, advise is the verb: give advice, and I'd advise you to wait. Both "
          "are said with a soft 's' in advice and a 'z' sound in advise, which is the memory "
          "hook: advi-s-e, it doe-s."),
    entry("could-care-less", (("could care less", "i could care less"),
                              ("couldn't care less", "couldnt care less", "could not care less",
                               "mean", "correct", "right", "wrong", "rude", "say")),
          "'I couldn't care less' is the one that means what it says - I care so little that I "
          "have no less to give. 'I could care less' says the opposite, though people use it that "
          "way anyway; in writing, use couldn't."),

    # --- punctuation and capitals --------------------------------------------
    entry("capital-letters", (("capitals", "capital letters", "capitalisation",
                               "capitalization", "capitalise", "capitalize",
                               "uppercase", "upper case"), ("when", "use", "rules", "which")),
          "Capitalise the first word of a sentence, names of people, places, days and months, and "
          "titles before a name: Nadia, Cardiff, Tuesday, Doctor Reid. Don't capitalise seasons, "
          "job titles on their own, or words in the middle of a sentence just because they feel "
          "important."),

    # --- spelling -----------------------------------------------------------
    entry("spell-definitely", (("definitely", "definately", "definatly"), ("spell", "spelling",
                                                                          "spelt", "correct")),
          "It's definitely: de-fin-ite-ly, with 'finite' hidden in the middle. The misspelling "
          "'definately' is the one people write most, so check for that a in the middle."),
    entry("spell-necessary", (("necessary", "neccessary", "necesary"), ("spell", "spelling",
                                                                       "spelt", "correct")),
          "It's necessary: one c, two s's. A one-collar shirt, two sleeves — one c, two s."),
    entry("spell-accommodation", (("accommodation", "accomodation"), ("spell", "spelling", "spelt",
                                                                     "correct")),
          "It's accommodation: two c's and two m's, because it has room for everyone. Same for "
          "accommodate and accommodating."),
    entry("spell-separate", (("separate", "seperate"), ("spell", "spelling", "spelt", "correct")),
          "It's separate: sep-a-rate, with 'a rat' in the middle. There is no e after the p."),
    entry("spell-receive", (("receive", "recieve"), ("spell", "spelling", "spelt", "correct")),
          "It's receive: i before e, except after c. The same rule gives believe, achieve and "
          "piece, and it is only a rule of thumb — weird, seize and their all break it."),
    entry("spell-embarrass", (("embarrass", "embarass", "embarrassed"), ("spell", "spelling",
                                                                        "spelt", "correct")),
          "It's embarrass: two r's and two s's. Think of it as being doubly awkward."),
    entry("spell-rhythm", (("rhythm", "rythm"), ("spell", "spelling", "spelt", "correct")),
          "It's rhythm: r-h-y-t-h-m, with no vowel between the y and the t. It is one of the few "
          "English words where y does the vowel's job."),
    entry("spell-restaurant", (("restaurant", "restaraunt", "restraunt", "restarant"),
                               ("spell", "spelling", "spelt", "correct")),
          "It's restaurant: r-e-s-t-a-u-r-a-n-t, with 'aunt' in the middle after the u. The usual "
          "slips are restaraunt and restraunt - remember the au, as in the French it comes from."),
    entry("spell-uk-us", (("english", "spelling", "spell"), ("british", "american", "uk",
                                                            "difference")),
          "Both are correct; just be consistent. British English uses colour, organise, centre and "
          "travelled, and American English uses color, organize, center and traveled. Most word "
          "processors can set the dictionary to the one you want."),
    entry("spell-check", (("spell", "spelling", "spelt", "misspelt", "misspelled"), ("check",
                                                                                    "correctly",
                                                                                    "autocorrect",
                                                                                    "tool",
                                                                                    "mistakes")),
          "Turn on the spell checker in whatever you're writing in and read it once more yourself: "
          "a checker catches typos but not the wrong word, so its, it's, your and you're still need "
          "your eyes."),

    # --- punctuation --------------------------------------------------------
    entry("apostrophes-plural", (("apostrophe", "apostrophes"), ("plural", "plurals", "cds",
                                                                 "apple's", "plural or")),
          "Plurals never take an apostrophe: two apples, the 1990s, CDs. Keep the apostrophe for "
          "missing letters (it's, don't) and for belonging (the dog's bowl). If it's plural, leave "
          "it out."),
    # A name ending in s is the possessive question people actually type, and none of the three
    # apostrophe entries reached it: plural is about plurals, contractions is about missing
    # letters. Phrases only for the possessive, so "where does the apostrophe go in plurals"
    # still belongs to apostrophes-plural.
    entry("apostrophe-after-s", (("apostrophe after s", "apostrophe after a name",
                                  "apostrophe after names", "apostrophe with names ending in s",
                                  "apostrophe for names ending in s", "names ending in s",
                                  "name ending in s", "names that end in s", "name ends in s",
                                  "possessive apostrophe", "apostrophe for possession",
                                  "james's", "james"),
                                 ("apostrophe", "apostrophes", "name", "names", "surname",
                                  "possessive", "belonging", "after", "ends", "ending",
                                  "s", "james", "or")),
          "Names ending in s take an apostrophe and another s: James's coat, Chris's car, the "
          "class's timetable. You will also see James' and Chris' in older British style and some "
          "publishers still print it, so either is defensible - just keep to one in the same "
          "document. It is only plurals that take no apostrophe at all: the Joneses are coming."),
    # The second group is the ask, so it needs the definition words as well: "when do i use a
    # semicolon" was answered and "what does a semicolon do" was the search hedge.
    entry("semicolon", (("semicolon", "semi-colon"),
                        ("use", "when", "instead", "comma", "do", "does", "mean", "meaning",
                         "for", "explain", "what")),
          "Use a semicolon to join two full sentences that are closely related: I missed the bus; "
          "the next one was an hour away. If a full stop would work, either is fine — a semicolon "
          "just says the two halves belong together.",
          # a semicolon in code ends a statement, which is a programmer's question, not a
          # punctuation one
          avoid=("python", "javascript", "java", " sql", "coding", "programming", "php", "css")),
    entry("i-before-e", (("i before e",), ("rule", "spell", "spelling", "except", "believe",
                                           "receive")),
          "It's i before e except after c: believe, piece, but receive, ceiling. It's only a rule "
          "of thumb, though — weird, seize, their and either all break it, so use it as a nudge "
          "and learn the exceptions you write often."),
    entry("comma-splice", (("comma", "commas"), ("splice", "joining", "two sentences", "run on",
                                                "run-on")),
          "Two complete sentences can't be held together by a comma alone. Use a full stop, a "
          "semicolon, or a comma plus and/but/because: I was late, so I skipped breakfast."),
    # The marks a person cannot name: the second half of each key is the ask, so "what does an
    # ellipsis mean" and "how do i use speech marks" - both a search hedge on main - reach the
    # answer the same way "when do i use a semicolon" does.
    entry("ellipsis", (("ellipsis", "ellipses", "three dots", "dot dot dot"),
                       ("use", "used", "when", "mean", "meaning", "do", "does", "for",
                        "writing", "what")),
          _ellipsis_reply),
    entry("brackets-punctuation", (("brackets", "bracket", "parentheses", "parenthesis"),
                                   ("use", "used", "when", "mean", "meaning", "do", "does",
                                    "for", "writing", "punctuation", "what")),
          "Brackets hold an aside the sentence would survive without: the date of a law, a "
          "translation, a word the reader may not know. Read the sentence without it - if the "
          "grammar still works, the brackets are doing their job. In British style the full stop "
          "goes outside them unless the bracket is a whole sentence of its own.",
          guard=_brackets_are_punctuation),
    entry("speech-marks", (("speech marks", "quotation marks", "quote marks", "inverted commas",
                            "double quotes", "single quotes", "quotes"),
                           ("use", "used", "when", "mean", "do", "does", "for", "writing",
                            "what", "how")),
          _speech_marks_reply,
          # a quote for a job or a price is not a question about the marks, and quoting a source
          # in an essay is that job's own card: "how do i quote someone in an essay" is about
          # choosing and embedding the quotation, not about where the marks go round dialogue.
          avoid=("how much", "price", "quote me", "insurance", "estimate", "trade", "garage",
                 "in an essay", "in my essay", "in a essay", "quote someone", "quote a source",
                 "quotation in an essay", "essay", "essays", "coursework", "dissertation",
                 "citation", "citations", "cite", "harvard", "referencing",
                 # a quote for a job, a customer or a supplier is a price
                 "job", "jobs", "for a job", "quote for", "quotes for", "customer", "customers",
                 "client", "clients", "pricing", "supplier", "suppliers", "tender", "invoice")),
    entry("list-punctuation", (("list", "lists", "bullet points", "bullets", "bulleted list"),
                               # not "colon" or "comma" here: those words in a second key make
                               # them commoner in the domain and the rarity bonus moved away from
                               # `colon-use`, which then lost "when do i use a colon in a sentence"
                               # "how" was in this half, which is in almost every question, so
                               # "how do i memorise a list quickly" was told where the commas go.
                               # The words here have to be about the writing itself.
                               ("punctuation", "punctuate", "punctuating", "write", "writing",
                                "sentence", "sentences", "grammar", "paragraph", "paragraphs")),
          _list_reply,
          # a shopping list, a to-do list, a CV and a list of steps are their own rows
          avoid=("shopping", "to do", "todo", "checklist", "packing", "steps", "chores", "cv",
                 "resume", "cover letter", "skills", "references", "interview")),
    entry("dash-hyphen", (("dash", "hyphen", "dashes", "hyphens", "em dash", "en dash",
                           "em-dash", "en-dash", "minus sign"),
                          ("difference", "use", "when", "for", "do", "does", "mean", "used",
                           "explain", "what", "type", "long", "longer", "how")),
          _dash_or_hyphen,
          # A dash of something is a quantity, not a mark: "what does a dash of hot sauce mean"
          # and "what does a dash of bitters mean" were both answered with the rule for joining
          # words together, because the measure reading of the same word is what was asked.
          guard=_dash_is_the_mark),

    # --- how to word it -----------------------------------------------------
    entry("cancel-plans-politely", (("cancel", "cancelling", "canceling", "pull out"),
                                    ("dinner", "plans", "invite", "invitation", "polite", "rude",
                                     "text", "message")),
          "Say it early, give the reason briefly, and offer the next time: \"So sorry, I need to "
          "cancel Thursday — work has landed on me. Can we do the week after? I'll book it.\" One "
          "short apology and a new date beats a long excuse.",
          # this writes the message for the person doing the cancelling, so a friend who keeps
          # cancelling on them belongs to the friend entries, not to this one
          avoid=("keeps cancelling", "keeps canceling", "keeps bailing", "always cancelling",
                 "cancels on me", "cancelled on me", "canceled on me", "cancelled again",
                 "bailed on me", "let me down", "keeps flaking", "no show", "no-show",
                 "my friend keeps", "my mate keeps", "he keeps", "she keeps", "they keep",
                 "someone keeps", "someone cancelled", "someone cancelled on")),
    entry("decline-invitation", (("decline", "declining", "turn down", "say no"), ("invitation",
                                                                                 "invite",
                                                                                 "party",
                                                                                 "wedding",
                                                                                 "offer")),
          "Thank them, say no plainly, and don't over-explain: \"Thanks so much for thinking of "
          "me, but I can't make it. I hope it goes brilliantly.\" If you'd like to keep the door "
          "open, add one line about catching up another time."),
    # "how do i rsvp to a wedding" was a hedge and "rsvp to a wedding invite" was "I'm
    # listening": the reply to an invitation has a shape - by the date, both questions answered,
    # and nothing added that was not offered - so it is a script like the two above.
    entry("rsvp-invitation", (("rsvp", "reply to the invitation", "reply to the invite",
                               "reply to a wedding invitation", "reply to a wedding invite",
                               "reply to an invitation", "respond to the invitation",
                               "respond to an invite", "respond to an invitation",
                               "answer the invitation", "answer an invitation",
                               "reply to a wedding card", "rsvp to a wedding",
                               "rsvp to the wedding", "accept the invitation", "accept an invite",
                               "how do i reply to an invite", "wedding invite",
                               "wedding invitation"),
                              ("how", "what", "do i", "should", "write", "say", "send", "back",
                               "card", "rsvp", "reply", "respond", "answer", "accept",
                               "wedding", "invitation", "invite", "date", "deadline")),
          "Reply by the date on the card, and answer both things they asked in one line: yes or "
          "no, and the meal or dietary bit. \"Thank you so much - we'd love to come. Two of us, "
          "one vegetarian, no allergies.\" If the invitation names you alone, go alone: asking to "
          "bring someone is the one thing that puts a host in an awkward spot. A no is fine and "
          "better early: \"Thank you for thinking of us, but we can't make it - I hope it's a "
          "wonderful day.\"",
          # a guest who has said yes and now wants to change the answer, and the person who is
          # not going at all, have their own entries above; this is the reply itself.
          avoid=("cancel", "cancelling", "canceling", "changed my mind", "change my mind",
                 "decline", "declining", "turn down", "say no", "said yes", "already said",
                 "cant go", "can't go", "not going", "kids", "children", "child",
                 # the host is not the guest: "how do i word a wedding invitation" was telling
                 # the person writing the card how to answer one, and "when should i send wedding
                 # invitations" did the same. These are the writing side of an invitation - word,
                 # design, print, send out, guest list - and none of them can be in a reply.
                 "word", "wording", "reword", "write my", "write our", "write the", "writing my",
                 "writing the", "send out", "send them", "send it out", "sending out", "print",
                 "printed", "printing", "printer", "design", "designer", "draft", "template",
                 "stationery", "invitation wording", "invites wording", "guest list",
                 "how many guests", "how many people", "save the date", "the invitation says",
                 # a bare "send" would take "how do i send my rsvp" down with it, so the sending
                 # of an invitation is named as a phrase
                 "send wedding", "send the invitation", "send the invitations", "send invitations",
                 "sending the invitation", "sending the invitations", "mail them", "mail out",
                 # the person asking for the replies is the host too
                 "ask for rsvps", "ask for rsvp", "asking for rsvps", "collect rsvps",
                 "chase rsvps", "chasing rsvps",
                 # "should i rsvp yes or no" is deciding, not answering: the row is the how-to,
                 # and a "whether" line keeps the "not mine to decide" answer it had. A bare
                 # "should i" cannot go in here, because "when should i rsvp to a wedding" is
                 # the how-to and names the same words.
                 "yes or no", "whether", "not sure if i should", "should i go",
                 # what the letters mean is a spelling-out question, and explains.py owns it
                 "what is rsvp", "whats rsvp", "what's rsvp", "what does rsvp", "rsvp mean",
                 "rsvp means", "rsvp stand for", "rsvp stands for"),
          # The reply itself, as royal-cap asked for: a line that only names a wedding and an
          # invitation is not this row's until it says somebody has to answer one, so
          # "how do i write a wedding invite" and "writing wedding invitations" (the host,
          # writing the card) stay with their own answers.
          ask=("reply", "rsvp", "respond", "answer", "say", "write back", "email back",
               "text back", "confirm", "accept", "decline", "let them know", "get back")),

    # The other side of the same card: the person writing the invitation is not the person
    # answering one, and on main "how do i word a wedding invitation" was a general "two or three
    # lines is plenty" and "writing wedding invitations" was the couple-as-a-pair speech card.
    entry("word-an-invitation",
          (("invitation", "invitations", "invite", "invites", "wedding invitation",
            "wedding invite", "save the date"),
           ("word", "wording", "reword", "write", "writing", "draft", "drafting", "design",
            "what to put", "what should i put", "how do i word", "how do i write", "how to word",
            "how to write")),
          ("Both names in full, the date and time written out, and the place with a postcode: then "
           "the one thing the guest has to act on - whether there is a meal to choose, whether "
           "children are invited - and an RSVP date with a name and a number to reply to. One side "
           "of a card is plenty. \"Alex and Sam would love you to join them\" does more work than "
           "three lines of poetry, and \"no gifts please\" only goes on if you mean it."),
          # the person who has to answer the card, and the words people write next to one, have
          # their own entries: rsvp-invitation, decline-invitation, the speech and the vow
          avoid=("rsvp", "reply", "replying", "respond", "responding", "answer the", "accept",
                 "decline", "declining", "turn down", "say no", "speech", "toast", "eulogy",
                 "vows", "vow", "reading", "readings", "thank you", "thankyou", "card message",
                 "christening card", "birthday card", "place card", "place cards", "menu card",
                 "order of service", "how many guests", "guest list", "seating", "table plan",
                 "when should i send", "when to send", "print", "printing", "printer",
                 # every other kind of invitation is a different card with different words, and
                 # "how do i word a birthday invitation" was told to ask about the meal
                 "birthday", "birthdays", "christening", "baptism", "baby shower", "baby's",
                 "anniversary", "hen", "hen do", "stag", "engagement", "retirement",
                 "housewarming", "house warming", "graduation", "party", "parties"),
          ask=("word", "wording", "reword", "write", "writing", "draft", "drafting", "design",
               "what to put", "what should i put"),
          bias=1),
    # "should i bring a plus one to a wedding" was "that's your call" and "what is a plus one"
    # was a search hedge. Both are one answer read off the envelope.
    entry("plus-one", (("plus one", "plus-one", "+1", "what is a plus one",
                        "what does plus one mean", "bring a partner", "bring my partner",
                        "bring my boyfriend", "bring my girlfriend", "bring my husband",
                        "bring my wife", "bring someone", "bring a friend", "bring my friend",
                        "a guest with me", "one seat"),
                       ("wedding", "invitation", "invite", "invitations", "rsvp", "should i",
                        "can i", "allowed", "ask", "asks", "said")),
          ("Read the envelope: if it names only you, or says one seat, it is just you - a plus one "
           "is only a plus one when the invitation says so or the host names your partner. Asking "
           "straight is fine and better early: \"Is there room for a plus one?\" If the answer is "
           "yes, remember the meal and the seat were counted for two from then on."),
          # the person writing the card and the person answering it are other rows
          avoid=("how many guests", "guest list", "seating", "table plan", "word", "wording",
                 "write", "writing", "print", "print the", "decline", "turn down", "say no"),
          bias=1),

    # "when should i send wedding invitations" was a search hedge: the card that writes one
    # stands down for the timing (its avoid names "when should i send"), and nothing owned the
    # when. Timing is the one part of a wedding nobody can look up in the venue's pack.
    entry("when-to-send-invitations",
          (("wedding invitation", "wedding invitations", "wedding invite", "wedding invites",
            "invitation", "invitations", "invites", "save the date", "save the dates"),
           ("send", "sends", "sending", "sent", "post", "posting", "out", "when", "how early",
            "how far in advance", "in advance", "ahead", "months before", "weeks before",
            "deadline", "how long before")),
          ("Six to eight weeks before the day is the usual rule here, and three months if people "
           "have to travel or it is a bank holiday weekend, because the invitation is asking for a "
           "yes, a meal choice and sometimes a bed. Post save-the-dates six to twelve months out, "
           "put the RSVP date three to four weeks before the wedding, and give the venue the final "
           "numbers about two weeks ahead. Chasing the people who have not answered is easier if "
           "the card names one date and one name to reply to."),
          # the wording side, the guest answering the card and the guest list are their own rows
          avoid=("word", "wording", "reword", "write", "writing", "design", "print", "printing",
                 "printer", "template", "stationery", "rsvp", "reply", "replying", "respond",
                 "accept", "decline", "plus one", "how many guests", "guest list", "seating",
                 "table plan", "speech", "thank you", "place card", "order of service",
                 "birthday", "christening", "baby shower", "funeral", "party", "parties",
                 "hen do", "stag"),
          ask=("when", "how early", "how far", "how long before", "how many weeks", "how many months",
               "weeks before", "months before", "in advance", "ahead", "too early", "too late"),
          bias=1),
    entry("deadline-extension",
          # the subject words widen this from the email-to-the-boss row it was: an essay, a
          # dissertation, a module and an exam are all shapes of the same ask
          (_EXT_WORDS,
           ("email", "ask", "asking", "lazy", "boss", "professor") + _EXT_SUBJECTS
           + ("get", "need", "needs", "how", "can i", "could i", "what do i", "should i",
              "said no", "refused", "missed", "help")),
          _a_deadline_extension,
          # the tax deadline, the census, a subscription and a passport are other rows' dates, and
          # a project plan for work is the work row's
          avoid=("tax", "hmrc", "self assessment", "vat", "census", "passport", "visa",
                 "insurance", "subscription", "renew", "renewal", "plan", "gantt", "sprint",
                 "client", "stakeholder", "roadmap", "milestone", "probation",
                 # "missed" is in the second group and "deadline" in the first, so every
                 # deadline a person can miss - a filing, a court date, a mortgage application -
                 # scored as a piece of coursework and was told to email the tutor. A line that
                 # names one of these is not a university deadline, whatever else it says.
                 "companies house", "confirmation statement", "annual return", "accounts",
                 "statutory accounts", "court", "court date", "hearing", "tribunal", "mortgage",
                 "planning permission", "landlord", "tenancy", "deposit", "council tax",
                 "insurance claim", "claim form", "warranty", "application form"),
          guard=_late_names_the_work),
    entry("condolence-message", (("condolence", "condolences", "sympathy", "sorry for your loss",
                                  "bereaved", "what do i say to someone who lost"),
                                 ("card", "write", "say", "message", "note")),
          "Name the person, say you're sorry, and mention one thing you remember or liked about "
          "them: \"I'm so sorry about your mum. She made the whole street laugh and I'll miss her. "
          "Thinking of you all.\" Keep it short, avoid 'at least' and any advice, and write it by "
          "hand if you can."),
    # A letter to somebody who has to act on it - a landlord, the council, an MP, an insurer,
    # the school - is one shape of answer, and the bot had none of them: eight of these lines
    # got the cake-piping answer ("how do i write a letter" is the same two words as a cake you
    # write on) and the rest got the Citizens Advice pointer. The entries that answer a letter
    # of their own (a cover letter, a resignation, a thank you, a complaint about a shop, a
    # condolence) keep their lines, so their names are in the avoid list here.
    # "Do I ring them or write?" is not a question about how to draft a letter, and it is not a
    # decision the bot has no business making either - it has a real answer. On main six of seven
    # way of asking it were a shrug ("Can't call that one for you, sorry") and the seventh was the
    # damp-letter template, which answers a letter nobody asked about.
    # Two ways of asking for the same decision, and the pairing is the gate: without "or write",
    # "or email", "or a call" in the line this is a different question and the row stands down.
    entry("ring-or-write", (_RING_OR_WRITE,
                            # the asking shape, so a bare two-word choice still scores: "should i
                            # ring or write" has nothing else in it but this
                            ("should i", "shall i", "do i", "is it better", "better to",
                             "would it be better", "worth", "rather", "which is better",
                             "whats better", "what is better"),
                            # what the choice is about. Not the words of the letter entry's own
                            # key (council, landlord, insurer): a word two entries use stops being
                            # rare, and the letter entry lost its rarity point to this one and
                            # gave "how do i write a letter to the council about the damp" away.
                            # `complaint` is not here: the letter row keys it, and a word two
                            # rows share stops being rare for the letter row, which then lost
                            # "how do i write a letter of complaint about a hotel" to this one
                            ("refund", "money back", "overcharged", "bill", "bills", "charge",
                             "charges", "arrears",
                             # A choice with no ask verb in it - "ring or write to the council"
                             # - matched only the pairing, and a row whose key matches one part
                             # of its own key does not score. These are the words of an
                             # addressee rather than subject words, so no other entry loses its
                             # rarity point to them, and the pairing in `ask` keeps the row off
                             # every line that is not a choice. Naming the office itself
                             # ("to the council") is what costs the letter entry its rarity on
                             # "council", so the offices stay out of it.
                             "to the", "to my", "to them", "with the", "for the")),
          ("Ring if you want it sorted this week, and write if you need a record. A call gets an "
           "answer the same day and you can ask a second question; a letter or an email is what "
           "you point to later if nothing happens. The easiest is both: ring, then send two lines "
           "saying what was agreed and by when, and keep a copy."),
          ask=(_RING_OR_WRITE,),
          avoid=("my mum", "my dad", "my ex", "my friend", "girlfriend", "boyfriend", "wife",
                 "husband", "son", "daughter", "birthday", "wedding", "invite", "invitation",
                 "cover letter", "resignation", "thank you", "condolence", "eulogy", "speech",
                 # asking someone out is not a letter to an office: "do i ring or text a girl
                 # after a date" has its own answer and it is not this one
                 "a girl", "a boy", "a date", "first date", "dating", "crush", "tinder",
                 "after a date", "asking her out", "asking him out")),
    entry("write-a-letter", (("letter", "letters", "in writing", "put it in writing",
                              "write to", "writing to", "draft a letter", "compose a letter",
                              "send a letter"),
                             ("landlord", "letting agent", "council", "mp", "msp",
                              "councillor", "hospital", "clinic", "doctor", "gp", "school",
                              "headteacher", "appeal", "insurance", "insurer", "neighbour",
                              # not "apology": the word belongs to the answer below with an
                              # example for each kind of person, and a second entry keying it
                              # costs that entry the rarity bonus it needs to win the line
                              "employer", "company", "bank", "official", "housing",
                              "council tax", "benefits", "dwp", "ombudsman", "solicitor")),
          ("Put what you want in the first line, then the facts in date order, then a deadline. "
           "\"I'm writing about the damp in the back bedroom at 14 Elm Road, which I reported on "
           "3 March. Could you send someone to look at it by 20 March?\" Name the address or the "
           "reference, keep it to one page, and say what you'll do next if nothing happens. Keep "
           "a copy, and send it by email or recorded post so you can show when it went. Ringing "
           "as well often gets an answer sooner than the letter does."),
          ask=("how", "what should i say", "write", "draft", "help", "can i", "should i"),
          # A missed bin is not a letter problem: the council's waste line answers it, and "put
          # what you want in the first line" is thinner than the thing to do. The bin words name
          # the subject, so the general letter stands down however the line is worded.
          avoid=("cover letter", "resignation", "thank you", "thanks", "reference", "cv",
                 "will", "speech", "eulogy", "sick note", "condolence", "refund",
                 "birthday", "christmas", "cake", "icing", "pipe", "love",
                 "bin", "bins", "wheelie", "bin day", "collection", "collected", "waste",
                 "recycling", "rubbish", "fly tipping",
                 # "ring or write" is which channel, not how to draft the letter: the row above
                 # answers it, and the damp template is thinner than the thing to do.
                 "or write", "or email", "or a letter", "or letter", "ring or", "call or",
                 "phone or", "or should i ring", "or should i write",
                 # a letter you cannot follow is lifeadmin's reading job: "how do i understand
                 # this letter" was handed the drafting template because "how" is in the ask.
                 "understand", "understand it", "make sense", "makes sense", "confusing",
                 "confused", "jargon", "cant follow", "dont follow", "explain it",
                 "card", "to my mum", "to my dad", "to my friend")),
    # "how do i write a formal letter" is the shape of the thing, not who it is to: the entry
    # above wants a landlord, a council or an MP, and with none of those named the line fell
    # through to the cake-piping answer ("write a letter" is also a cake you write on) and then,
    # once the icing gave it up, to the shrug. So this answers the bare formal ask and the
    # letter to a boss, which is the same job.
    entry("formal-letter", (("formal letter", "business letter", "official letter",
                             # a bare "letter" is the plainest way to ask this, and with the
                             # icing standing down it reached the shrug: who it is to decides
                             # the entry below, and the shapes that are never formal are in the
                             # avoid list
                             "letter", "letters",
                             "letter to my boss", "letter to the boss", "letter to my manager",
                             "letter to my employer", "letter to my company", "letter to the head"),
                            ("write", "writing", "draft", "drafting", "start", "starting",
                             "begin", "beginning", "format", "layout", "lay out", "set out",
                             "structure", "open", "opening", "end", "ending", "finish", "word",
                             "words", "example", "template", "how do i", "how to")),
          ("Four short paragraphs: what you want and by when, the facts in date order, what you "
           "have already tried, and what happens next if nothing changes. Put your address, their "
           "name and address and the date at the top with a subject line saying what it is about, "
           "open with 'Dear Mr Smith' or 'Dear Sir or Madam' and close with 'Yours sincerely' or "
           "'Yours faithfully', and keep the whole thing to one page."),
          ask=("how", "what", "write", "draft", "help", "need", "want", "should", "can", "start"),
          # A formal letter is also, word for word, a cake you write on and the icing entry has
          # the same two covered words; it lives in cooking.py, which is at the world's 1 MB
          # file limit, so this entry outranks it here rather than naming it in an avoid list
          # there. Two points is the whole gap on "how do i write a formal letter".
          bias=3,
          # a complaint about a shop, a resignation, a cover letter and a landlord each have
          # their own answer, and a cake you write on is not a letter
          avoid=("complaint", "complain", "refund", "resignation", "resign", "leaving my job",
                 "cv", "curriculum vitae", "cover letter", "covering letter", "reference",
                 "thank you", "thanks", "eulogy", "condolence", "sick note", "love",
                 "landlord", "letting agent", "council", "council tax", "housing", "mp", "msp",
                 "dwp", "benefits", "ombudsman", "insurance", "insurer", "school", "appeal",
                 "will", "speech", "cake", "icing", "pipe", "birthday", "christmas",
                 # a letter to your mum, your dad or a friend is not a formal letter, and
                 # main leaves those to the hedge rather than tell them to write one
                 "to my mum", "to my dad", "to my mother", "to my father", "to my friend",
                 # keeping old paper is the paper row's question, and it reaches the bare word
                 # "letters" as well: the yellowing, the musty smell and the box it lives in are
                 # asked as often as how to write one
                 "yellow", "yellowing", "yellowed", "going yellow", "gone yellow", "musty",
                 "fusty", "smell", "smells", "smelly", "fading", "faded", "foxing",
                 "store", "storing", "preserve", "keep my", "keep old",
                 "old letters", "old letter", "photos", "photographs", "postcards",
                 "keepsakes",
                 # ...and a bare "letter" also reaches three questions that already have the
                 # better answer: how to open and close one, what to put on the envelope, and
                 # what to write to somebody you do not know. Each names its own job here.
                 # the date you put on it is the date row's question, and "how do i write the
                 # date in a letter" was getting the four-paragraph complaint shape because the
                 # row carries a bias of 3 and the date row does not
                 "the date", "date on a letter", "date in a letter", "what date", "date to put",
                 "write the date",
                 "address a letter", "addressing", "envelope", "envelopes", "stamp", "stamps",
                 # scanning a letter is a document scan, in technology
                 "scan", "scans", "scanned", "scanning", "photograph a letter",
                 "post a letter", "posting", "postage", "salutation", "sign off", "signing off",
                 "dear", "to a stranger", "stranger",
                 # and the parts of a letter that have a better answer than the complaint shape:
                 # how to start one, how to end one, how to sign it, where to send it, and what
                 # to say to somebody you have never met. Each of these was taking the four-
                 # paragraph complaint answer off the bare word.
                 "start a letter", "start my letter", "start the letter", "starting a letter",
                 "begin a letter", "beginning a letter", "open a letter", "opening a letter",
                 "end a letter", "ending a letter", "finish a letter", "finishing a letter",
                 "close a letter", "closing a letter", "sign a letter", "signing a letter",
                 # ...and the bare verb is the same ask once a letter is in the line: "how do i
                 # close a formal letter", "how do i sign a formal letter" and "how do i finish
                 # a business letter" were all four paragraphs, with the words to close one
                 # nowhere in the reply
                 "close", "closing", "closed", "sign", "signed", "signing", "signature",
                 "last line", "end of a letter", "end of the letter",
                 # the opening is the same: "how do i begin an official letter" and "how do i
                 # open a business letter" were the four paragraphs, not the first line
                 "first line", "opening line", "greeting", "salutation",
                 "start", "starting", "start a", "begin", "beginning", "open", "opening",
                 "finish", "finishing",
                 "send a letter", "sending a letter", "letter to a company", "to a company",
                 "someone i dont know", "somebody i dont know", "someone i don't know",
                 "somebody i don't know",
                 # a letter you cannot follow is lifeadmin's reading job, not this one: "how do i
                 # understand this letter" has a "how do i" and a "letter" and nothing else, so
                 # the drafting shape took it.
                 "understand", "understand it", "make sense", "makes sense", "make of it",
                 "confusing", "confused", "jargon", "cant follow", "dont follow", "explain it",
                 # handling the paper is not composing it: folding it to fit an envelope, sealing
                 # it, and putting a stamp on are other answers, and the bare word "letter" was
                 # taking them.
                 "fold", "folds", "folding", "seal", "seals", "sealing", "sealed",
                 # a letter to Father Christmas is a wish list, not a formal letter: "how do i
                 # write a letter to santa" was a hedge and became four short paragraphs
                 "santa", "father christmas", "to santa",
                 # who it is to decides it, and a person or an office named in the line already
                 # has the better answer: "a letter to my daughter for her wedding" is not a
                 # complaint with a deadline, and "a letter to my bank" is write-a-letter's line
                 "daughter", "son", "child", "children", "kid", "kids", "future self",
                 "wedding", "anniversary", "wife", "husband", "partner",
                 "grandson", "granddaughter", "bank", "banks", "building society",
                 "hospital", "doctor", "gp", "solicitor", "neighbour", "neighbor",
                 # the kind of letter is a job of its own, and a bare "letter" was standing in
                 # front of three cards that answer it better: a pay rise, a request for more
                 # money, and an apology. Each of these said what it was and got four paragraphs
                 # about dates and deadlines instead (snug-ostrich, #general 55120).
                 "pay rise", "payrise", "pay raise", "more money", "salary increase",
                 "apology", "apologies")),
    entry("complaint-letter", (("complaint", "complain"), ("letter", "email", "write", "company",
                                                          "refund")),
          "Keep it to facts and what you want: what you bought, when, what went wrong, what you've "
          "already tried, and the outcome you're after, with dates and order numbers. Say what you "
          "want plainly (\"I'd like a refund of £40\") and give a deadline for a reply. Stay polite "
          "— the person reading it isn't the one who caused it.",
          # A council, a bank, an insurer or a school is not a shop and "what you bought" is the
          # wrong frame for them: the entry above answers a letter to somebody who has to act,
          # and every word here reaches a real answer without it.
          avoid=("letting agent", "council", "housing", "bank", "insurance", "insurer", "mp",
                 "msp", "councillor", "school", "employer", "ombudsman", "dwp", "benefits",
                 "council tax")),
    # The other kind of letter, and the one the icing answer used to take: "how do i write a love
    # letter" wants the sentence to open with, not a nozzle.
    # "love poem" is not here: a poem asked for by name is a verse, and the warm verse for a
    # person (`bot/knowledge/entertainment.py`) is the better answer to "write me a love poem for
    # my wife". The letter advice keeps the letter, the note and the valentine.
    # "valentine" is an occasion as well as a card, so the second group is what makes the line a
    # letter rather than a dinner, a present, an outing or a film: the ask alone ("what should i")
    # was in the key, and it took every one of them - "what should i cook for valentines day",
    # "what should i get my girlfriend for valentines", "what should we do for valentines day",
    # "what should i watch on valentines" were all answered "Say the one thing you would say out
    # loud if they were in front of you". A letter is words, so only the words stay in the key.
    entry("love-letter", (("love letter", "love note", "valentine", "valentine's",
                           "valentines", "secret admirer"),
                          ("write", "writing", "written", "say", "saying", "message", "note",
                           "card", "send", "draft", "put in", "words")),
          ("Say the one thing you would say out loud if they were in front of you, then the specific "
           "thing you noticed: \"I still think about the way you laughed at the wrong bit of that "
           "film.\" Three or four sentences is enough, no jokes at your own expense and nothing "
           "borrowed from a card. Write it by hand if you can, read it once and take out anything "
           "you would not say to their face."),
          ask=("how", "what should i", "write", "draft", "help", "can i", "should i"),
          # A valentine card is a card, and the card entry has the better line for it ("one true
          # thing you would say out loud, then stop"): the poem can keep the word valentine, the
          # card cannot, so the card words stand this entry down.
          avoid=("cake", "icing", "pipe", "broken up", "ex", "cheating", "not sure i love",
                 "falling out of love", "does he love me", "does she love me",
                 "valentine card", "valentines card", "valentine's card")),
    entry("apology-fits-the-person", (("apologise", "apologize", "apology", "apologising", "apologizing",
                               "say sorry", "said sorry", "apologise properly"),
                              ("email", "message", "text", "letter", "write", "properly", "friend",
                               "boss",
                               # the words this answer has a second example for: an apology to a
                               # customer is the order-and-refund one, and without them in the key
                               # a same-scoring message entry from another domain took the line
                               "customer", "customers", "client", "clients", "company", "order",
                               "refund", "grovelling", "professional", "colleague", "colleagues",
                               "staff",
                               # "how do i apologise at work" named the place, not the person,
                               # and fell through to the search hedge
                               "work", "at work", "office", "meeting", "team")),
          _apology),
    entry("chase-payment", (("invoice", "payment", "paid", "owed"), ("chase", "chasing", "overdue",
                                                                    "unpaid", "reminder",
                                                                    "late")),
          "Send one friendly reminder with the details: invoice number, amount, due date, and a "
          "link or the bank details again. \"Just a nudge on invoice 214 (£340), due on the 3rd — "
          "could you confirm when it's scheduled?\" If it's already overdue, add a date you'll "
          "escalate on, and keep it in writing.",
          # This row is about money somebody owes *you*. A payment of the person's own that is
          # late is the other way round - "my loan payment is overdue" was told to send a nudge
          # to a customer - and money's missed-payment row answers that one.
          avoid=("my card", "my credit card", "my debit card", "my loan", "my payment",
                 # a payment the state owes the person is not an invoice to chase: "my uc
                 # payment is late" and "my benefit payment is late" both got the nudge-to-a-
                 # customer card, and lifeadmin's benefit-payment-not-arrived answers them
                 "my benefit", "my benefits", "my uc", "my universal credit", "my pip",
                 "my esa", "my child benefit", "my tax credits", "benefit payment",
                 "benefits payment", "dwp", "jobcentre", "job centre", "hardship payment",
                 "my direct debit", "my mortgage", "my rent", "my bill", "my insurance",
                 "i missed", "i forgot", "i didnt pay", "i didn't pay", "i cant pay",
                 "i can't pay", "cant pay", "can't pay", "they charged me", "charged me",
                 "behind on",
                 # ... and so is a wage: "my boss wants me to work late every week, do i have to
                 # be paid for it" met "paid" and "late" and was told to send a nudge about
                 # invoice 214. The person is asking to be paid for their hours, which the work
                 # rows answer, and no invoice is owed to them. The phrases put "paid" where the
                 # wage is, so a late invoice ("i still have not been paid for the job") keeps
                 # the row.
                 "be paid for", "paid for it", "get paid", "am i paid", "being paid",
                 "paid overtime", "overtime", "work late", "working late", "work extra",
                 "hours i work", "for the hours")),
    entry("emojis-at-work", (("emoji", "emojis", "emoticon", "emoticons"),
                             ("work", "email", "professional", "boss", "client", "colleague",
                              "rude", "slack", "teams", "office", "meeting")),
          "One emoji, only where the tone is already warm: a thumbs-up or a smile in a work chat is "
          "fine, a string of them rarely is. Skip faces in anything to a client, in bad news, and in "
          "a first email to someone senior; a plain \"Thanks!\" or a short \"Sounds good\" carries "
          "the warmth without the risk. Never let an emoji replace the words that say what you mean, "
          "and never use a winking one to soften a real complaint."),
    entry("clear-writing", (("writing", "write"), ("clear", "clearer", "clearly", "concise",
                                                   "concisely", "shorter", "tighter",
                                                   "plain", "better", "professional",
                                                   "formal", "polished")),
          "Shorten sentences, cut the warm-up, and put the ask first: \"Could you send the file by "
          "Friday?\" beats three lines of context before the point. Use the same word for the same "
          "thing throughout, and read it aloud — anything you stumble on, rewrite.",
          avoid=("cv", "resume", "résumé")),
    # Improving your writing over months is not the same ask as making one thing clearer, which
    # clear-writing answers. Keyed on the improving words so "how do i write better" keeps its
    # answer.
    entry("writing-improve", (("writing", "write", "writer", "essays", "essay", "english"),
                              ("improve", "improving", "improvement", "better at", "get better",
                               "become better", "become a better", "practice", "practise",
                               "practising", "practicing")),
          "Write 200 words a day and edit them the next morning, when you can see what is on the "
          "page rather than what you meant: cut one sentence and rewrite one. Copy a paragraph "
          "you admire by hand once a week to feel how the sentences are built, and read your own "
          "work aloud - the place you stumble is the place to fix.",
          avoid=("handwriting", "signature", "sign", "spell", "spelling", "letter to",
                 "speaking", "speak", "spoken", "pronunciation", "accent", "listening",
                 "cover letter", "cv", "resume", "card", "cards", "email to", "text to")),
    entry("email-subject", (("subject line", "subject lines", "email subject",
                             "subject for an email"), ("write", "good", "better", "opening",
                                                       "start", "email")),
          "Say what it's about and what you need in six words or so: 'Invoice 214 — payment date?' "
          "or 'Flat 3 viewing Saturday 10am'. Put the action at the front, and don't write 'Quick "
          "question' — it tells the reader nothing."),
    entry("proofread", (("proofread", "proofreading", "proof read", "check my writing",
                         "check my email", "check an email"), ("how", "tips", "better",
                                                                  "faster", "mistakes")),
          "Read it once for what it says and once only for mistakes, and change the order - bottom "
          "to top, or aloud - so your eye stops filling in what you meant. Check names, dates and "
          "numbers against the source, then the four usual slips: its/it's, your/you're, then/than, "
          "and missing words."),
    # One example for all of these answered "how do i write a thank you note to my teacher"
    # with somebody else's afternoon and somebody else's cake, so the note is built from what
    # the line names. The thank-you after an interview is `interview-thank-you`'s in the work
    # domain: it says what to put in it and when to send it, and this note is a different note.
    entry("thank-you-note", (("thank you note", "thank you letter", "thank you card",
                             "thankyou note", "thank-you note"), ("write", "after", "say",
                                                                  "gift", "help")),
          thanks_note,
          avoid=("interview", "interviews", "interviewer", "interviewing", "job interview",
                 "panel", "recruiter", "job")),
    # "feedback" is in the key on its own, so "how do i ask my teacher for feedback" was this
    # giving card. Asking for it is the other direction and study.py's ask-teacher answers that;
    # a person named in the line is the giveaway.
    entry("give-feedback", (("feedback",), ("how", "give", "giving", "criticism", "criticise",
                                           "difficult", "badly")),
          "Name the thing, say the effect, then ask: 'Your reports land late on Fridays, so I'm "
          "guessing the plan slips - what's getting in the way?' Keep it about the work and a "
          "particular time, not their character, and give the good news just as specifically: "
          "'the client email was exactly right.'",
          # asking a panel for feedback on yourself is not giving anyone feedback, and this row
          # answered "how do i ask for feedback after an interview" with how to phrase criticism
          avoid=("for feedback", "ask for feedback", "asking for feedback", "my teacher",
                 "my lecturer", "my tutor", "my professor",
                 "after an interview", "after the interview", "after my interview", "interview",
                 "interviews", "interviewer", "interviewers",
                 # a review of a purchase is not feedback to a colleague: "how do i leave feedback
                 # for a shop" was answered with how to phrase criticism at work. The leaving words
                 # stay out of this list on purpose - "how do i leave feedback for a colleague" is
                 # this row's question, and shopping's review row outscores it on the shop lines.
                 "a shop", "for a shop", "a restaurant", "for a restaurant", "a hotel",
                 "for a hotel", "a product", "my order", "the seller", "the app",
                 "review", "reviews")),
    entry("disagree-kindly", (("disagree", "disagreement", "disagreeing"),
                              ("how", "without", "politely", "argument", "rude", "tactfully")),
          "Say what you agree with first, then the one thing you'd change: 'I'm with you on the "
          "timeline - what I'd worry about is the testing.' Use 'I think' and 'from what I've "
          "seen', keep it to one point at a time, and if it heats up, offer to take it offline."),
    entry("bad-news-email", (("bad news", "turn down a candidate", "reject an applicant",
                             "reject a candidate", "rejection", "rejected", "unsuccessful",
                             "decline a request"), ("email", "emails", "write", "writing",
                                                    "word", "wording", "letter", "letters")),
          "Give it in the first line, without a warm-up: 'I'm sorry to say we won't be going ahead "
          "with your application.' Then one plain sentence on why, if it's fair to say, and what "
          "happens next. No 'however' or 'unfortunately' to soften it - the person reads them as "
          "stalling.",
          # "what should i say when someone tells me bad news" and "what do i say to a friend who
          # got bad news" are somebody's bad day, not a rejection letter: the bare "say" and "how"
          # in the ask took them and answered with "we won't be going ahead with your application".
          # A written rejection says email or letter; comfort is somebody else's row.
          avoid=("tells me", "told me", "tells us", "told us", "someone tells", "someone told",
                 "somebody tells", "somebody told", "my friend", "my mate", "my mum", "my dad",
                 "my sister", "my brother", "my partner", "my husband", "my wife",
                 "in person", "face to face", "phone call", "on the phone", "a friend")),
    entry("congratulations-message", (("congratulations", "congrats", "well done card",
                                      "new baby message", "graduation message"), ("write",
                                                                                  "message",
                                                                                  "say", "card",
                                                                                  "text")),
          "Name what they did and what you noticed: 'The grand opening looked brilliant - I've "
          "watched you plan it for a year. Congratulations.' Three lines is plenty, and add "
          "something only you could say about them."),
    # "whats a metaphor" names one of the two and asks what it is; the difference words alone
    # left it a hedge, and it is the commoner question of the pair.
    entry("metaphor-simile", (("metaphor", "simile", "metaphors", "similes"),
                              ("difference", "mean", "means", "example", "examples",
                               "what", "whats", "what is", "definition", "define",
                               "explain", "describe")),
          _the_figure_that_was_named),
    # The words people ask about one at a time: "what does irony mean" was a shrug while the
    # metaphor/simile pair answered. One entry, because each of them is the same question: a
    # plain definition and one example that shows it.
    entry("figure-of-speech", (("irony", "ironic", "onomatopoeia", "alliteration",
                                "personification", "hyperbole", "euphemism",
                                "figure of speech", "figures of speech"),
                               ("mean", "means", "what", "define", "definition", "example",
                                "examples", "difference", "explain")),
          _figure_of_speech),
    # "what does ambiguous mean" was a search hedge while the grammar terms all answered. The
    # table above holds the everyday words and sayings, and this entry is only the ask around
    # them: a line that does not name one of those words gets nothing from here.
    entry("word-meaning", (("mean", "means", "meaning", "meanings", "define", "definition",
                            "explain", "what does", "what is", "whats", "what's", "called"),
                           tuple(WORD_GLOSSES)),
          _word_meaning,
          # a spelling question, a grammar term and a figure of speech all have their own answer
          ask=("mean", "means", "meaning", "define", "definition", "explain", "what does",
               "what is", "whats", "what's", "called"),
          avoid=("spell", "spelling", "spelt", "misspell", "grammar", "noun", "verb",
                 "adjective", "adverb", "pronoun", "preposition", "conjunction", "semicolon",
                 "apostrophe", "comma", "synonym", "metaphor", "simile", "irony", "ironic",
                 "hyphen", "bisect", "appointment", "medical",
                 # "what does the big picture mean for my pension" asks what the thing implies
                 # for the pension, not what the words mean: the topic keeps its own answer
                 "mean for", "means for", "mean for my", "means for my",
                 # a red flag stops a motor race and a football match, and a grey area on a
                 # scan is a shadow on a picture - both are the words, not the sayings
                 "formula 1", "formula one", "f1", "grand prix", "race", "racing", "football",
                 "rugby", "cricket", "match", "x ray", "x-ray", "scan", "mri", "ultrasound",
                 "chest", "lung", "lungs", "lump", "mole", "tooth", "teeth")),
    # The everyday words, in their own row because they need a fence the row above cannot take.
    # The row above answered "bonjour", "explain catch 22" and "is this a red flag", which are
    # rightly definitions and would be lost if its guard were stricter; these words, though, turn
    # up inside ordinary questions often enough that a definition every time they appear would
    # take the answer away ("im knackered all the time, what helps" was the tiredness card until a
    # plain mention of the word was read as a request for its meaning). So this row answers only a
    # line that is asking what the word means, and the word is in both key groups so it scores
    # three times and beats the row that caught one word of it by accident ("gutted" reached the
    # bloating card through the "gut" in it), the way the idiom rows do.
    entry("everyday-word-meaning",
          (tuple(EVERYDAY_WORDS), tuple(EVERYDAY_WORDS),
           ("mean", "means", "meaning", "meanings", "define", "definition", "explain",
            "what does", "what is", "whats", "what's", "called", "stand for", "refers")),
          _an_everyday_word,
          guard=_asks_what_a_word_means,
          bias=1,
          avoid=("recipe", "recipes", "cook", "cooking", "bake", "how long", "how many",
                 # a line that wants something done about it is not a request for the meaning
                 "how do i", "how can i", "what should i", "help me", "what do i do",
                 "hurts", "hurting", "pain", "painful", "sore", "ache", "aches", "aching")),
    entry("active-passive", (("active", "passive"), ("voice", "difference", "writing", "use")),
          "In the active voice the doer comes first: the dog ate my homework. In the passive the "
          "thing done to comes first: my homework was eaten. Active is usually shorter and "
          "clearer; passive earns its place when the doer doesn't matter or you'd rather not name "
          "them."),
    entry("colon-use", (("colon", "colons"), ("use", "when", "instead", "list", "semicolon",
                                             "difference", "do", "does", "mean", "meaning",
                                             "for", "used", "capital", "capitalise",
                                             "capitalize", "explain", "what")),
          "A colon introduces what explains or follows: a list, an example, a quote. \"Take three "
          "things: milk, eggs and bread.\" No capital after it unless a full sentence follows, and "
          "no colon straight after a verb - \"the things I need are milk, eggs and bread\", not "
          "\"are: milk\"."),
    entry("comma-before-but", (("comma", "commas"), ("but", "however", "before but")),
          "Put a comma before but when it joins two full sentences: \"I wanted to come, but my "
          "train was cancelled.\" When it only pairs two words or short phrases - small but strong - "
          "leave the comma out."),
    entry("start-with-and", (("start", "starting", "begin", "beginning"),
                             ("sentence", "sentences")),
          "Yes, a sentence can start with and or but - writers have done it for centuries and it "
          "reads naturally in ordinary writing. What gets noticed is doing it over and over "
          "(\"And then... And then...\"), so use it for effect rather than as a habit.",
          ask=("ok", "okay", "fine", "alright", "allowed", "correct", "wrong", "can i", "can you",
               "should i", "may i", "is it")),
    entry("apostrophe-contractions", (("dont", "dont", "cant", "wont", "doesnt", "isnt", "couldnt",
                                       "contraction", "contractions"),
                                      ("apostrophe", "apostrophes", "missing", "letters")),
          "The apostrophe goes where the letters were left out: don't for do not, can't for cannot, "
          "I'm for I am, won't for will not. That is why won't and can't don't look like the words "
          "they shorten - the old forms were woll not and can not.",
          # "dont" is how a lot of people type, and plenty of real lines say "dont" and a word that
          # stems to "letter" - "i dont understand my council tax letter", "i dont get the letter
          # from the council". Those want their own answer, so the grammar needs asking about.
          ask=("apostrophe", "apostrophes", "correct", "correctly", "right", "wrong", "need",
               "needs", "needed", "should", "where", "why", "which", "when", "how", "use",
               "used", "spell", "spelling", "spelled", "spelt", "grammar", "punctuate",
               "punctuation", "matter", "difference", "write", "writing", "written", "is",
               "are", "or")),
    entry("am-pm", (("12am", "12pm", "12 am", "12 pm", "noon", "midnight", "am or pm", "am and pm",
                     "am pm"),
                    ("mean", "correct", "is it", "which", "difference", "technically", "write",
                     "written", "how")),
          "12 am is midnight and 12 pm is noon: am runs from midnight up to just before noon, so the "
          "first minute of the day is 12:00 am. Most people write 12 noon and 12 midnight instead, "
          "which nobody argues with."),
    entry("alright-all-right", (("alright",), ("all right", "correct", "spell", "ok", "okay",
                                                "either", "wrong")),
          "All right is the form to write: two words, as in \"are you all right?\" Alright is fine "
          "in a text or a line of dialogue and most people read it without noticing, so keep it "
          "for those.",
          ask=("is it", "which", "correct", "spell", "either", "wrong", "or")),
    entry("titles-italics", (("italics", "italic", "underline", "quotation marks", "quote marks",
                              "book title", "film title", "song title", "titles"),
                             ("title", "titles", "book", "film", "song", "poem", "album",
                              "chapter", "article", "essay")),
          "Italicise whole works - book titles, films, albums, newspapers - and put quotation marks "
          "around the parts of a whole: a chapter, an article, a song, a poem. Underline instead of "
          "italicising if you are writing by hand.",
          ask=("should i", "do i", "how do i", "which", "italicise", "italicize", "use")),
    entry("numbers-in-writing", (("numbers", "number", "five", "ten", "figures"),
                                 ("essay", "writing", "write", "style", "spell", "words")),
          "Write one to nine as words and 10 and up as figures, except when a number starts a "
          "sentence - then spell it out: \"Twenty people came.\" Keep it consistent within a "
          "sentence, and use figures for money, times and measurements.",
          ask=("how", "should i", "do i", "when", "is it", "write")),
    entry("seasons-capitals", (("seasons", "season", "winter", "summer", "autumn", "spring"),
                               ("capital", "capitalise", "capitalize", "capitals", "capitalised")),
          "Seasons stay lower case: spring, summer, autumn, winter. Days and months take a capital "
          "- Monday, January - and so do holidays, as in Christmas.",
          ask=("do i", "should i", "is it", "does", "are", "capitalise", "capitalize",
               "capitalised", "capitalized")),
    entry("contractions-essay", (("contractions", "contraction"), ("essay", "writing", "formal",
                                                                  "academic", "ok", "allowed",
                                                                  "school")),
          "Contractions are fine in ordinary writing, emails and anything with a human voice, and "
          "they read as friendlier. In formal academic writing most style guides still prefer the "
          "full form - write \"do not\" rather than \"don't\" and you cannot be marked down for it.",
          ask=("is it", "are they", "can i", "should i", "ok", "allowed")),
    entry("rhetorical-question", (("rhetorical",), ("question", "mean", "what", "example",
                                                    "definition",)),
          "A rhetorical question is asked for effect, not for an answer: \"Who could blame her?\" "
          "It nudges the reader towards the answer you already have, which is why it works well as "
          "an opener and badly as a real enquiry."),
    entry("oxymoron", (("oxymoron", "oxymorons"), ("mean", "what", "example", "examples",
                                                   "definition",)),
          "An oxymoron puts two words together that fight: deafening silence, living dead, "
          "bittersweet, a small crowd. It is a deliberate contradiction, and it is different from a "
          "plain contradiction because the clash is the point."),
    entry("synonym", (("synonym", "synonyms"), ("mean", "what", "word", "for", "another word")),
          "A synonym is a word that means roughly the same as another: happy and glad, begin and "
          "start. Roughly is the important bit - glad fits \"I'm glad you came\" where happy would "
          "be too strong, so pick by the shade you want."),
    entry("spaces-after-full-stop", (("space", "spaces", "spacing"), ("full stop", "period",
                                                                     "sentence", "sentences",
                                                                     "after")),
          "One space after a full stop, not two - the double space was a typewriter habit and word "
          "processors already add the right gap. The same goes after a comma and a question mark."),
    entry("formal-date", (("date", "dates", "the date", "date in a letter", "date on a letter",
                           "what date"),
                          ("write", "writing", "written", "formally", "letter", "letter to",
                           "form", "forms", "correct", "diary", "put")),
          "Write the date in full and in one order: 10 March 2025 (British) or March 10, 2025 "
          "(American), with no th and no comma in the British form. In a letter, put it above the "
          "greeting; the ordinal - the tenth of March - is for speech.",
          ask=("how do i", "how do you", "how to", "should i", "which", "what is", "correct"),
          # the date on a letter was reaching the icing card and the four-paragraph complaint
          # shape, both of which carry a bias and this row carried none
          bias=2,
          # a date on a form is not a date on a dating app: "how do i write a dating profile" was
          # answered with the day-month order. Phrases only - a bare "dating" loose-matches
          # "date" and stood the row down for "how do i write a date formally"
          avoid=("dating app", "dating apps", "dating profile", "dating site", "online dating",
                 "first date", "on a date", "ask her out", "ask him out", "tinder", "hinge",
                 "bumble")),
    entry("homophone", (("homophone", "homophones"), ("mean", "what", "definition", "example",
                                                     "examples")),
          "Homophones sound the same but are spelt differently and mean different things: "
          "their/there/they're, to/too/two, right/write, sea/see. If swapping a word changes the "
          "sentence's meaning, you have a homophone pair - that is what the other half of these "
          "questions is about."),
    entry("grey-gray", (("grey", "gray"), ("correct", "spell", "spelling", "wrong", "either",
                                           "difference", "or")),
          "Both are right: grey is the British spelling and gray the American one, and neither is "
          "a mistake. Pick the one your reader expects and keep it the same through a piece of "
          "writing.",
          # "is it grey or gray" is the whole question; a grey coat is not
          ask=("is it", "which", "correct", "spell", "either", "wrong")),

    # --- the everyday language questions people still get a fallback for ---

    entry("comma-before-and", (("comma before and", "oxford comma", "serial comma"),
                               ("need", "should", "use", "when", "yes")),
          "Not needed for a simple list: bread, milk and eggs. Put one in when 'and' joins two "
          "complete sentences (I booked the table, and she drove), or when the list items are long "
          "enough that the reader needs the pause: we need the report signed, the photos checked, "
          "and the invoice sent."),

    # "whats an oxford comma" names the thing and asks what it is; the comma-before-and row
    # answers the "do i need one" question, so this one is keyed on the name of the comma
    # itself and never competes with it.
    entry("oxford-comma", (("oxford comma", "serial comma"),
                           ("what", "whats", "what is", "mean", "definition", "explain", "use",
                            "why", "rule", "difference", "called", "comma")),
          "It is the comma before the last item in a list: milk, eggs, and bread. British "
          "writing usually leaves it out and American keeps it, and it earns its place when it "
          "stops a misreading - I'd like to thank my parents, Ayn Rand, and God. Keep to one habit "
          "through a document either way."),

    # --- punctuation: the mark people ask about, and the one they cannot name -----------
    # "when do i use a comma" and "how do i use commas" were the search hedge while a comma
    # before and/but, a semicolon, a colon and an apostrophe all had answers: the general rule
    # was the only one missing.
    entry("comma-rules", (("comma", "commas"),
                          ("when", "use", "where", "put", "need", "go", "rule", "rules",
                           "correctly", "properly", "sentence", "pause",
                           # and the plain "what is a comma", which was a hedge next to an
                           # answered "when do i use a comma"
                           "what", "whats", "what is", "mean", "meaning", "called",
                           "explain", "definition", "why"),
                          # "however" is its own part, not one more word in the list above: a
                          # part matches on its best alternative, so a word inside that list is
                          # worth the same as "comma" and loses the line to `comma-before-but`,
                          # whose key holds "however" and earns the rarity point for "but". A
                          # line that never says it simply adds nothing to the rank.
                          ("however",)),
          _comma_rules,
          # the splice has its own answer, and "what is a comma splice" is a longer name than
          # the general rule, so it must not be read as one more comma question
          avoid=("splice", "splices", "run on", "run-on", "two sentences")),
    entry("sentence-end", (("full stop", "full-stop", "question mark", "question marks",
                            "exclamation mark", "exclamation marks"),
                           ("use", "when", "need", "sentence", "end", "instead", "how many",
                            "where",
                            # "what is an exclamation mark" is the same question as "when do i use
                            # one" and was a search hedge, because naming the mark in the key and
                            # asking how to use it were the only two halves of the row
                            "what", "whats", "what is", "whats a", "mean", "meaning", "called",
                            "explain", "definition", "for", "do", "does", "why")),
          _end_mark),
    # Speaking aloud is writing's neighbour, and the same ask: "how do i stop saying um" was a
    # shrug next to an answered "how do i give a presentation". The words in the line say which
    # of the three problems it is.
    entry("speak-clearly", (("filler", "fillers", "filler words", "um", "ums", "erm", "er",
                             "mumble", "mumbling", "mumbles", "speak", "speaking", "talk",
                             "talking", "voice", "monotone"),
                            ("clearly", "clearer", "filler", "fillers", "um", "ums", "erm",
                             "confident", "confidence", "confidently", "nervous", "nerves",
                             "stop saying",
                             # "i mumble when i talk" names the trouble in the second half, and
                             # "talk" on its own is in the first group: the phrase is what makes
                             # the line a question about the voice
                             # "when i talk" and not a bare "i talk": the bare phrase matched
                             # every "how do i talk to my teenager", which is a conversation
                             # with a person rather than the voice.
                             "when i talk", "when i speak",
                             "stop using", "mumbling", "monotone", "too fast", "too quiet",
                             "shaking", "shaky", "wobble", "wobbly", "wavers", "slowly",
                             "slower",
                             # The volume lines were riding on the bare "i speak" phrase that
                             # the teenager question needed gone: "i speak too quietly" and
                             # "how do i speak louder" were a hedge without it.
                             "too quietly", "so quietly", "more quietly", "quietly", "quieter",
                             "louder", "too loud", "too loudly", "speak louder", "talk louder",
                             "speak up", "project my voice", "project your voice",
                             # the ask named in whole words: the same word cannot count in
                             # both halves of the key, so "stop mumbling" was one match and no
                             # answer, and "i say um too much" the same.
                             "stop mumbling", "stop being", "say um", "say erm", "too much",
                             "less monotone",
                             "sound monotone", "sound", "sounds",
                             "talk fast", "speak fast", "fast when")),
          _speak_clearly,
          # a conversation with a person about a thing is not the voice: "how do i talk to my
          # boss about pay" is the pay conversation, and "speak to" plus a problem is its own ask
          avoid=("my boss", "my manager", "my landlord", "my partner", "my husband", "my wife",
                 # something loose in the mouth is not the voice: "my dentures keep falling
                 # out when i talk" is a fit problem, and "when i talk" alone took it
                 "denture", "dentures", "false teeth", "dental plate", "my plate",
                 "my tooth", "my teeth", "invisalign", "retainer",
                 "my mum", "my dad", "my son", "my daughter", "my friend", "the doctor", "gp",
                 # "talk to" and "speak to" name a conversation with a person rather than the
                 # voice: "how do i talk to my teenager about phones" scored 5 on the phrase
                 # "i talk" (3) plus "talk" (2) and got the voice exercises. The phrases are
                 # here rather than words so the typo repair never reads one as a near miss.
                 "talk to", "talking to", "talk about", "talking about", "speak to",
                 "speaking to", "speak about",
                 # somebody else's talking is a conversation to have, not the voice to train.
                 # "talk" is in the first group and "too much" in the second, so
                 # "how do i tell someone they talk too much" scored the same as a mumbling
                 # line and this row's bias=1 won it: the answer was "slow to two-thirds of
                 # your usual speed". The telling row in wording.py already has the script.
                 "talk too much", "talks too much", "talking too much", "talk over",
                 "talks over", "talking over", "interrupt", "interrupts", "interrupting",
                 "someone they", "somebody they", "someone who", "somebody who",
                 "they talk", "they speak", "keep talking",
                 # the people most often named in that question: a teenager, a child, a parent
                 # or a teacher is a conversation to have, not a voice to train
                 "teenager", "teenagers", "teen", "teens", "teenage", "kid", "kids", "child",
                 "children", "my mother", "my father", "my parents", "my sister", "my brother",
                 "my family", "teacher", "colleague", "coworker", "neighbour",
                 "the school", "the council", "about pay", "about a rise", "about money",
                 "ask for", "complaint", "complain",
                 # Saying something in a meeting is not a voice problem: "how do i speak up in
                 # meetings" and "how do i speak up at work" got the mumbling exercises, and the
                 # work module answers them now. The phrases are here, never the bare word
                 # "meeting", so "my voice shakes when i present" keeps the voice card.
                 "in meetings", "in a meeting", "at the meeting", "speak up in", "speak up at",
                 "speak in meetings", "talk in meetings", "standup", "stand-up meeting",
                 "stand up meeting", "team meeting", "contribute in",
                 # a speech, a presentation or a toast has its own answer, and it is a better one
                 # for a nervous speaker than the voice exercises
                 "in public", "public speaking", "speech", "presentation", "audience", "wedding",
                 "best man", "maid of honour", "toast", "eulogy", "interview"),
          bias=1),
    # "what is the plural of crisis" answered "octopuses is right in English" on main, because
    # the -uses row was the only row that held the word crisis. The -is words are the plural
    # row's own now (see `plural-word` below), and this row keeps the -us family it explains.
    entry("plural-octopus", (("plural", "plurals"), ("octopus", "octopi", "virus", "cactus",
                                                     "walrus")),
          _PLUSES_REPLY),
    # The same answer for the line that asks which of the two: "is it octopuses or octopi",
    # "cactuses or cacti". Those lines never say the word plural, so the row above cannot read
    # them, and two of the -us words said together is what the question is: a line that names
    # both spellings is asking which one to use. The guard keeps the row off the line that only
    # mentions two of the things ("i have two cactuses and a virus").
    entry("which-plural-of-a-us-word", (_PLUS_FORMS,), _PLUSES_REPLY, bias=2,
          shape=(_offers_two_of_the_family,), guard=_asks_which_of_the_two),

    # --- the everyday messages people ask for the words of -------------------

    # --- netiquette ----------------------------------------------------------
    entry("leaving-group-chat",
          (("group chat", "group chats", "group message", "whatsapp group", "family group",
            "group text", "facebook group"),
           # the how-to lines ("how do i leave a whatsapp group") want the stairs, and main's
           # leave-group-chat has them: this entry is the "is it rude" one, so the plain verbs
           # and the mute words stay out of the key
           ("rude", "politely", "polite", "awkward", "drama", "offend", "offending",
            "silent", "quietly", "straight out", "remove myself", "should i",
            # "without it being a thing" is the same question as "is it rude"
            "being a thing", "without it being", "without anyone", "notice", "notices",
            "noticed")),
          "Mute it first - leaving is for the chat that is genuinely noise, not for one busy week. "
          "If you do go, the quiet exit is the polite one: turn off notifications, leave, and tell "
          "anyone who matters in a private message. Only a family or work group needs a goodbye "
          "line, and one sentence does it: 'I'm going to hop out of this one, message me directly.'",
          # leaving a job, a marriage or a group of friends is a different question
          avoid=("job", "work", "boss", "husband", "wife", "partner", "marriage", "school",
                 "college", "course", "husband", "band", "choir", "running club", "cult",
                 "facebook", "admin", "invite", "add me", "create", "set up", "make a group")),

    entry("word-start-email", (("email", "message", "letter", "dear or hi", "hi or dear",
                                "dear or hello"),
                               ("start", "starting", "begin",
                                "greeting", "opening", "first",
                                "never met", "stranger",
                                # "should i write dear or hi" is
                                # the same question as "how do i
                                # start an email"
                                "dear", "hi", "hello", "dear or hi",
                                "hi or dear", "dear sir")),
          "Use the name: 'Dear Ms Okafor' if you know it and it is formal, 'Hello Sam' for "
          "anything else. Then say why you are writing in the first sentence, before any "
          "introductions. 'I hope this email finds you well' is filler that most readers skip.",
          avoid=("cover letter", "cv", "resume", "applying for", "application", "resignation",
                 "resigning", "leaving my job", "job offer", "interview")),

    # "should i use dear sir or madam" and "how do i address a letter" are the same question
    # about the opening line, and word-start-email never reached them: neither names an email or
    # a letter to start.
    entry("letter-salutation", (("dear sir", "dear madam", "dear sir or madam", "sir or madam",
                                 "dear madam or sir", "salutation", "to whom it may concern",
                                 "address a letter", "address a formal letter", "dear",
                                 # "what do i write at the start of a letter" and "how do i
                                 # begin a letter" are the same question as "how do i start a
                                 # formal letter", and the phrase is what lets this row answer
                                 # them: the shape row stands down for them and the decorating
                                 # row was answering "at the start of a letter" with buttercream
                                 "start of a letter", "the start of a letter",
                                 "start a letter", "starting a letter",
                                 "begin a letter", "beginning a letter",
                                 "beginning of a letter", "the beginning of a letter",
                                 "open a letter", "opening a letter", "opening line",
                                 "first line of a letter"),
                                ("use", "letter", "letters", "email", "formal", "start",
                                 "addressing", "address", "write", "madam", "sir", "dear",
                                 "name", "right", "rude", "ok", "okay", "polite")),
          "If you know the name, use it: 'Dear Ms Okafor' or 'Dear Dr Patel' beats any general "
          "form. 'Dear Sir or Madam' is fine when you genuinely have no name, and it pairs with "
          "'Yours faithfully'; with a name it is 'Yours sincerely'. Never 'To whom it may concern' "
          "- it reads like a circular - and check the spelling of the name, which is the thing "
          "people notice most.",
          # a card's greeting is the card's, and a message to your own boss is chat
          avoid=("card", "cards", "note", "txt", "text", "birthday", "christmas", "wedding",
                 "condolence", "thank you", "complaint", "refund", "cover letter", "cv",
                 "resume", "applying for", "resignation", "resigning", "my boss", "my landlord",
                 "my neighbour", "my teacher", "my ex", "my mum", "my dad", "my friend")),

    # The front of the envelope is a different question from the greeting, and people ask both.
    entry("envelope-addressing", (("address an envelope", "addressing an envelope",
                                   "address the envelope", "what goes on an envelope",
                                   "write an address on an envelope", "envelope"),
                                  ("address", "addressing", "write", "writing", "post", "postcode",
                                   "name", "names", "how", "where", "correctly")),
          "Name on the top line, house number and street below it, then the town, then the "
          "postcode in capitals on its own line: Ms J Patel, 14 Elm Road, Leeds, LS6 2AB. Put "
          "your own name and address on the back, and use the full name and title - Mr, Mrs, Ms "
          "or Dr - of whoever will open it."),

    # "what is a paragraph" is the same ask as "how long should a paragraph be" for most
    # people: the answer to both is one idea, three or four sentences. The reply leads with
    # what a paragraph is and keeps the length, so the second half the line asks for is still
    # there when the line only wanted the number.
    entry("paragraph-length", (("paragraph", "paragraphs"),
                                ("long", "length", "short", "how long", "should", "split",
                                 "writing", "sentences", "what is", "whats", "definition",
                                 "mean", "means", "how many", "words", "much")),
          _paragraph,
          avoid=("essay", "word count", "words should", "introduction", "conclusion")),

    entry("write-a-poem", (("poem", "poems", "poetry", "verse"),
                           ("write", "writing", "start", "begin", "good", "better", "how",
                            "short")),
          "Start with one true picture rather than a feeling - the chipped mug, the bus you "
          "missed - and write it in short plain lines you would actually say out loud. Keep the "
          "best line, cut the explaining around it, and stop one line before you want to. Ten "
          "minutes with no rhyming is a good first poem.",
          # a love poem is a card, a poetry book is a present, and "poem" in a line about
          # someone else's writing is not a request to write one
          avoid=("love poem", "valentine", "wedding", "funeral", "eulogy", "read", "reading",
                 "recommend", "book", "books", "poet", "poets")),

    entry("write-dialogue", (("dialogue", "dialog"),
                             ("write", "writing", "good", "better", "how", "natural",
                              "realistic", "story", "conversation", "start")),
          "Keep each speech short and let people interrupt, dodge and answer a different "
          "question than the one asked. Use 'said' and nothing fancier, cut the adverbs, and put "
          "a small action between speeches so the reader can see who is talking. Read it aloud "
          "in two voices: anything that sounds written, cut.",
          # "how do i get better at writing dialogue" is a dialogue question, not the general
          # improving-your-writing answer: it ties writing-improve on score and on key length,
          # and the tie goes to the entry that comes first, so it needs the nudge.
          bias=2),

    entry("use-a-thesaurus", (("thesaurus",), ("use", "how", "best", "good", "find", "word",
                                                "words", "another")),
          "Look up the plainest word in the sentence, not the cleverest: that is the one with a "
          "useful choice. Take a word you would say out loud, check it in the dictionary for the "
          "sense you mean, and leave the rest alone - a thesaurus makes writing worse when it is "
          "used to sound clever."),

    entry("use-a-dictionary", (("dictionary", "dictionaries"),
                               ("use", "how", "best", "good", "properly", "word", "words",
                                "look up", "looking up")),
          "Look up the base word rather than the ending - 'running' is under 'run' - and read "
          "the example sentence before the definition, because the example shows the word at "
          "work. Then write one sentence of your own with it the same day: a word you only read "
          "is one you lose by Friday.",
          avoid=("thesaurus", "synonym", "synonyms", "different word")),

    entry("repeating-yourself", (("repeat", "repeating", "repetitive", "repetition",
                                  "repeats"),
                                 ("writing", "write", "essay", "myself", "sentences",
                                  "words", "paragraph", "paragraphs", "story")),
          "Most repetition is the same point made twice in different words: keep the shorter "
          "one and delete the other. Vary how sentences start - if three in a row begin with "
          "'the' or 'I', rewrite two of them - and search the document for your favourite filler "
          "('really', 'just', 'important') at the end, because you will not hear it yourself.",
          # "can you repeat that" is the bot's own line, not an essay problem, and a person who
          # repeats - a toddler, a parent with dementia - is not writing an essay: confident
          # advice about an essay handed to them is worse than the shrug they get on main.
          avoid=("repeat that", "say that again", "say it again", "repeat after me",
                 "same as before", "again please", "what did you say",
                 "toddler", "child", "children", "son", "daughter", "baby", "kid", "kids",
                 "my mum", "my mom", "my dad", "nan", "grandad", "partner", "husband",
                 "wife", "speech", "hearing", "autistic", "autism", "dementia",
                 "alzheimers", "alzheimer's", "keeps saying", "same word", "sentence he",
                 "sentence she", "stutter", "stammer", "tourettes")),

    entry("word-sign-off", (("sign off", "signing off", "signoff", "sign-off", "sign", "signed",
                             "signing", "signature"),
                            # The verb that means the words at the bottom of the page is "sign
                            # off", "sign" or "signature". "close", "end" and "finish" are also
                            # how a complaint, a letter to a landlord and a letter to an MP are
                            # asked about, and there the person wants how to put the thing, not
                            # which words close it - those three are the second row below.
                            #
                            # the document has to be named: "how do i close my bank account" and
                            # "how do i sign a lease" are not letters, and the word "how" alone
                            # was letting every one of them through
                            ("letter", "letters", "email", "emails", "note", "notes", "memo",
                             "message", "formal", "best", "kind", "regards", "signature",
                             "sincerely", "faithfully")),
          "'Kind regards' or 'Best wishes' are safe for almost anything work-related, and 'Thanks' "
          "works when you have asked for something. 'Yours sincerely' only when you started with "
          "Dear Mr or Ms, and 'Yours faithfully' when you started Dear Sir or Madam.",
          # a note the doctor writes, a thank-you letter and a job application each carry their
          # own answer, and closing one is not the question that was asked
          avoid=("sick note", "fit note", "thank you", "cover letter", "covering letter",
                 "cv", "resume",
                 # and a thing you sign or close is often not a letter at all
                 "account", "accounts", "log in", "login", "sign in", "sign up", "unsubscribe",
                 "subscribe", "subscription", "subscriptions", "lease", "tenancy", "contract",
                 "deed", "passport", "cheque", "mortgage", "agreement", "licence", "license",
                 "bill", "bills",
                 # a text message is not signed off with "Yours faithfully", and ending your notes
                 # is the note-taking answer's line
                 "a text", "text message", "texting", "txt",
                 "note taking", "note-taking", "taking notes", "study notes",
                 ),
          # "how should i end a letter" and "how do i end a formal letter" were both reaching the
          # essay-conclusion entry, which also answers a closing and scores the same: the words to
          # close a letter are the more specific answer, so they win the tie.
          bias=2),

    # "how do i end a letter of complaint", "how do i close a letter to my landlord" and "what do
    # i write at the end of a letter to my mp" were the closing words once "close" and "end" were
    # in the row above, and the card that owns that letter answers the question better: a person
    # ending a complaint wants what to put in it, not which words go at the bottom (pink-nail on
    # #4752). So the ending verbs are their own row and the documents whose own card answers an
    # ending stand it down. "how do i sign off a complaint letter" keeps the words, because a
    # signature line is what "sign off" asks for and that card has nothing about one.
    entry("word-close-a-letter", (("close", "closing", "closed", "end", "ending", "finish",
                                   "finishing", "at the end", "the end of", "last line",
                                   "final line", "wrapping up"),
                                  # "business" is not here on its own: "how do i close a
                                  # business" is a company, and the letter is the word that
                                  # says a letter ("close a business letter" still keys on it)
                                  ("letter", "letters", "email", "emails", "memo", "memos",
                                   "message", "messages", "formal")),
          "'Kind regards' or 'Best wishes' are safe for almost anything work-related, and 'Thanks' "
          "works when you have asked for something. 'Yours sincerely' only when you started with "
          "Dear Mr or Ms, and 'Yours faithfully' when you started Dear Sir or Madam.",
          avoid=("thank you", "cover letter", "covering letter", "cv", "resume",
                 "account", "accounts", "log in", "login", "sign in", "sign up", "unsubscribe",
                 "subscribe", "subscription", "subscriptions", "lease", "tenancy", "contract",
                 "deed", "passport", "cheque", "mortgage", "agreement", "licence", "license",
                 "bill", "bills", "a text", "text message", "texting", "txt",
                 "note taking", "note-taking", "taking notes", "study notes", "essay", "essays",
                 # The documents whose own card answers the ending too, and only those: each
                 # of these was checked to leave the line on a real answer with the row stood
                 # down, and a document word that stood it down for a line no card answers
                 # ("how do i end a letter to the university") was a hedge or an essay
                 # conclusion instead, so it is not in this list.
                 "complaint", "complaints", "complaint letter", "letter of complaint",
                 "landlord", "landlords", "letting agent",
                 "mp", "mps", "mp's", "member of parliament",
                 "resignation", "resigning", "reference", "references", "referee",
                 "appeal", "appeals", "sick note", "fit note"),
          bias=2),

]

# --- "another word for happy", which is a writing question with a short answer ------------
# The ask is always the same shape - another word, a better word, a different word, a nicer
# way to say it - and the answer is three or four words plus the shade that separates them.
# Covering the words people actually ask for beats one clever reply: a shrug here is the
# commonest way a writing question goes wrong, because "another word for" is not a word the
# rest of the knowledge base has anything to say about.
WORD_SETS = {
    "happy": "Glad, cheerful, pleased, content, delighted. Glad is the everyday one, content "
             "means quietly satisfied, and delighted is a big thing.",
    "sad": "Unhappy, down, miserable, low, gutted. Down and low are for a flat week, miserable "
           "and gutted for something that has actually happened.",
    "big": "Large, huge, enormous, vast, sizeable. Large is neutral and fits writing; huge and "
           "enormous are the spoken ones, and vast is for space rather than a thing.",
    "small": "Little, tiny, slight, compact, minor. Tiny is smaller than little, and minor is "
             "for importance rather than size.",
    "good": "Fine, solid, strong, decent, excellent. Fine is faint praise, decent is a real "
            "compliment in speech, and excellent is for something you would single out.",
    "bad": "Poor, weak, awful, dreadful, rubbish. Poor and weak are the calm written ones; "
           "awful and rubbish are how people say it out loud.",
    "said": "Said, asked, replied, muttered, shouted, whispered. Said is invisible and usually "
            "the right word - save the others for the two or three places where how it was "
            "said matters.",
    "nice": "Kind, friendly, thoughtful, pleasant, lovely. Kind and thoughtful are about what "
            "someone did; pleasant and lovely are about how something felt.",
    "tired": "Weary, worn out, exhausted, drained, sleepy. Sleepy means ready for bed, exhausted "
             "means past it, and drained is the one after a hard week.",
    "angry": "Cross, annoyed, furious, irritated, livid. Cross is the mild everyday word, "
             "annoyed and irritated are about a thing, and furious and livid are the top end.",
    "scared": "Frightened, afraid, nervous, anxious, terrified. Nervous is before, frightened "
              "is now, and terrified is the extreme of either.",
    "beautiful": "Lovely, stunning, gorgeous, striking, handsome. Beautiful is the safe one, "
                 "stunning is a reaction, and handsome works for a building as well as a face.",
    "interesting": "Intriguing, absorbing, fascinating, notable, worth a look. Absorbing means "
                   "it held your attention, fascinating is stronger, and notable is the neutral "
                   "written one.",
    "important": "Key, vital, crucial, significant, essential. Significant is the calm report "
                 "word; crucial and essential mean it cannot be left out.",
    "difficult": "Hard, tricky, demanding, awkward, challenging. Tricky is a puzzle, demanding "
                 "is effort, and awkward is a person or a corner rather than a task.",
    "easy": "Simple, straightforward, effortless, quick, painless. Simple is about the steps, "
            "straightforward is about the instructions, and effortless is how it felt.",
    "funny": "Amusing, comical, hilarious, witty, odd. Witty is clever, hilarious is loud, and "
             "odd is the other meaning of funny.",
    "hungry": "Starving, peckish, famished, ravenous. Peckish is a bit, starving is an "
              "exaggeration everyone uses, and ravenous is the real thing.",
    "thank you": "Thanks, many thanks, thank you so much, I really appreciate it, much "
                 "appreciated. Thanks is fine in a message and the longer ones belong in a "
                 "card or after a real favour.",
    "sorry": "I apologise, my apologies, I'm sorry about that, excuse me. I apologise is the "
             "written one for a mistake, and sorry is warmer when you mean it.",
    "no": "Not this time, I can't, I'd rather not, that doesn't work for me. I'd rather not is "
          "the kindest firm one, and adding a reason of one clause is plenty.",
    "good luck": "Best of luck, all the best, fingers crossed, break a leg. Fingers crossed is "
                 "the friendly one, and break a leg is only for performers.",
    "congratulations": "Well done, nice one, many congratulations, thrilled for you. Well done "
                       "is for effort, congratulations for the news itself.",
    "delicious": "Tasty, mouthwatering, lovely, moreish, scrumptious. Tasty is the everyday one, "
                 "mouthwatering is for how it looks, and moreish means you want more of it.",
    "clever": "Bright, sharp, smart, inventive, quick. Bright and smart are the everyday ones, "
              "sharp is fast on the uptake, and inventive is about ideas.",
    "brave": "Courageous, bold, gutsy, plucky, fearless. Courageous is the formal one, bold is "
             "about a decision, and gutsy is doing it while scared.",
    "busy": "Flat out, rushed, swamped, hectic, tied up. Flat out and swamped are the spoken "
            "ones, hectic is about the day, and tied up is the polite one.",
    "great": "Excellent, brilliant, superb, terrific, first-rate. Brilliant is the British "
             "spoken one, superb is the calm written one, and terrific is louder.",
    "quick": "Fast, swift, speedy, brisk, prompt. Fast is about speed, brisk is a pace you set, "
             "and prompt means on time.",
    "i dont know": "I'm not sure, I'm not certain, I couldn't say, I'd have to check. I'd have "
                   "to check is the one that keeps you honest without sounding helpless.",
}
_SYNONYM_ASK = ("another word", "a better word", "better word", "different word", "other word",
                "word for", "another way to say", "another way of saying", "nicer way to say",
                "politer way", "more formal way", "less formal", "instead of saying",
                "synonym for", "synonyms for", "word that means", "good word for")


# The ask phrase itself is not the word being asked about: in "whats a good word for a dog" the
# only table word is "good", which belongs to the ask, and the answer is main's dog one.
_ASK_SPANS = tuple(tuple(one.split()) for one in _SYNONYM_ASK)
_CONNECTORS = ("for", "say", "saying", "means")
# A word after the one asked about is only padding: "another way to say no thanks" is about no.
_PADDING = frozenset(("thanks", "please", "then", "too", "as", "well", "again", "instead",
                      "there", "here", "somebody", "someone", "people"))
_PHRASE_KEYS = tuple(sorted((one for one in WORD_SETS if " " in one),
                            key=lambda one: -len(one.split())))


def _span_after_ask(said):
    """The words the line is asking about: everything after "another word for" and its kin."""
    end = 0
    for parts in _ASK_SPANS:
        size = len(parts)
        for start in range(len(said) - size + 1):
            if said[start:start + size] == parts and start + size > end:
                end = start + size
    if end == 0:
        # the gate matched a form this tuple spells differently ("saying" for "say"): the word
        # asked about still follows the connector, so cut there rather than reading the whole line
        for index, word in enumerate(said):
            if word in _CONNECTORS:
                end = index + 1
    return said[end:]


def _synonyms(memory, understood):
    """The set for the word the line asked about, or None so another module can answer."""
    said = [str(word).lower() for word in (understood.get("words") or ())]
    span = _span_after_ask(said)
    for start in range(len(span)):
        for key in _PHRASE_KEYS:
            parts = key.split()
            if span[start:start + len(parts)] == parts:
                rest = span[start + len(parts):]
                if all(word in _PADDING for word in rest):
                    return WORD_SETS[key]
        word = span[start]
        if word not in WORD_SETS and word.endswith("s") and word[:-1] in WORD_SETS:
            word = word[:-1]
        if word in WORD_SETS and " " not in word:
            rest = span[start + 1:]
            # "another way to say happy birthday in a card" is about the phrase, not about happy
            if all(one in _PADDING for one in rest):
                return WORD_SETS[word]
    return None


ENTRIES.append(entry("word-synonyms", (tuple(WORD_SETS) + ("synonym", "synonyms", "word"),
                                       _SYNONYM_ASK), _synonyms,
                     ask=_SYNONYM_ASK,
                     # "what does X mean" and "how do i spell X" are their own questions, and a
                     # definition of the word synonym is the dictionary entry, not this table
                     avoid=("mean", "meaning", "definition", "spell", "spelling", "spelt",
                            "pronounce", "in french", "in spanish", "in german",
                            "translation", "translate")))


# --- "whats the plural of crisis", which is a word question with a rule for its answer --------
# The ask has one shape whatever the word: "the plural of X", "whats X in the plural", "how do i
# make X plural", "X plural". The good answer is short, and it gives the pattern as well as the
# word, because the pattern is the thing the person can use again: "analyses ... the -is words
# change to -es". So the table is grouped by the rule that decides it, and every word answers with
# its group's pattern. On main a handful of words were covered and the rest shrugged ("whats the
# plural of child" got "I don't know enough to answer that honestly"), while "whats the plural of
# crisis" was answered with the sentence about octopuses.
# A word outside the table is passed over rather than guessed at, because a plural invented by a
# rule is a confident wrong answer on the words that break the rule (chief, piano, cactus). The
# everyday nouns are a list of their own instead: most words only add -s, and a table can hold a
# great many of them, which is cheaper than being wrong.
_PLURAL_GROUPS = (
    ("The -is words change to -es, as in analysis and analyses, basis and bases and thesis "
     "and theses.",
     {"crisis": "crises", "analysis": "analyses", "thesis": "theses", "basis": "bases",
      "axis": "axes", "oasis": "oases", "diagnosis": "diagnoses", "prognosis": "prognoses",
      "hypothesis": "hypotheses", "synopsis": "synopses", "emphasis": "emphases",
      "parenthesis": "parentheses", "paralysis": "paralyses", "ellipsis": "ellipses",
      "neurosis": "neuroses", "metamorphosis": "metamorphoses"}),
    ("These are the old ones with no pattern to learn: person and people, man and men, tooth and "
     "teeth.",
     {"child": "children", "person": "people", "man": "men", "woman": "women",
      "tooth": "teeth", "foot": "feet", "mouse": "mice", "goose": "geese", "ox": "oxen",
      "louse": "lice", "policeman": "policemen", "fireman": "firemen",
      "spokesman": "spokesmen", "chairman": "chairmen"}),
    ("Deer, fish, trout, aircraft and series work the same way: the word does not change at "
     "all.",
     {"sheep": "sheep", "deer": "deer", "fish": "fish", "trout": "trout",
      "salmon": "salmon", "aircraft": "aircraft", "series": "series", "species": "species",
      "offspring": "offspring", "headquarters": "headquarters"}),
    ("The -f and -fe words turn into -ves: knife and knives, wife and wives, half and halves.",
     {"knife": "knives", "wife": "wives", "life": "lives", "leaf": "leaves",
      "half": "halves", "loaf": "loaves", "shelf": "shelves", "thief": "thieves",
      "wolf": "wolves", "calf": "calves", "scarf": "scarves", "hoof": "hooves",
      "self": "selves", "elf": "elves", "wharf": "wharves", "sheaf": "sheaves"}),
    ("A short list of -o words takes -es: tomato and tomatoes, hero and heroes, echo and echoes.",
     {"potato": "potatoes", "tomato": "tomatoes", "hero": "heroes", "echo": "echoes",
      "veto": "vetoes", "torpedo": "torpedoes", "volcano": "volcanoes", "mosquito": "mosquitoes",
      "buffalo": "buffaloes", "domino": "dominoes", "cargo": "cargoes", "mango": "mangoes"}),
    ("Words ending in s, x, z, ch or sh take -es: bus and buses, box and boxes, church and "
     "churches.",
     {"bus": "buses", "box": "boxes", "church": "churches", "dish": "dishes",
      "glass": "glasses", "class": "classes", "watch": "watches", "brush": "brushes",
      "bench": "benches", "branch": "branches", "match": "matches", "quiz": "quizzes",
      "fox": "foxes", "dress": "dresses", "wish": "wishes", "kiss": "kisses",
      "bunch": "bunches", "boss": "bosses"}),
    ("A consonant then y becomes -ies: baby and babies, story and stories. A vowel then y just "
     "takes s, as in day and days.",
     {"city": "cities", "baby": "babies", "story": "stories", "country": "countries",
      "party": "parties", "family": "families", "company": "companies", "lady": "ladies",
      "puppy": "puppies", "enemy": "enemies", "hobby": "hobbies", "diary": "diaries",
      "memory": "memories", "library": "libraries", "army": "armies", "factory": "factories",
      "century": "centuries", "salary": "salaries", "berry": "berries", "supply": "supplies",
      "sky": "skies", "fly": "flies", "penny": "pennies", "trolley": "trolleys"}),
    ("Not every -f word changes: roof and roofs, chief and chiefs, safe and safes.",
     {"roof": "roofs", "chief": "chiefs", "chef": "chefs", "belief": "beliefs",
      "cliff": "cliffs", "safe": "safes", "gulf": "gulfs", "handkerchief": "handkerchiefs",
      "reef": "reefs", "proof": "proofs"}),
    ("These keep the Latin or Greek ending: medium and media, criterion and criteria, "
     "phenomenon and phenomena.",
     {"datum": "data", "medium": "media", "bacterium": "bacteria", "criterion": "criteria",
      "phenomenon": "phenomena", "curriculum": "curricula", "memorandum": "memoranda",
      "index": "indices", "appendix": "appendices", "matrix": "matrices", "vertex": "vertices",
      "formula": "formulae", "larva": "larvae"}),
)
# Words that have no plural in the everyday sense. Naming that is a better answer than inventing
# "advices", and it is what a friend would say.
_UNCOUNTABLE = {"information", "advice", "furniture", "luggage", "homework", "equipment",
                "knowledge", "money", "water", "milk", "rice", "bread", "news", "research",
                "traffic", "weather", "hair", "salt"}
# The everyday nouns that only add -s. Whatever a group above already holds is dropped, so a word
# is answered once and by the pattern that is true of it.
_PLAIN_NOUNS = """answer animal apple bag ball banana basket bath bean bed bee bike bird birthday
biscuit boat body bone bottle bowl brother building burger cake camera candle card carpet carrot
cat chair chicken chip clock coat coin computer cook corner cow cup curtain customer daughter day
desk dinner doctor dog door driver ear egg engineer evening event exam eye face fact farm farmer
father festival film finger floor flower fork friend game garden gate girl goal group guest hand
hat head hill holiday home horse hospital hotel hour house idea island jacket job journey kettle
key kid kitchen lake lamp laptop leg lesson letter light line list lunch machine map market meal
meeting message minute mirror mistake month morning mother mountain mouth movie museum name
neighbour night noise nose note nurse office onion orange page paper parent park passenger pasta
path pen pencil phone photo piano picture piece plane plate pocket point question radio receipt
restaurant ring river road room salad sandwich school scientist sea season seat sentence shop
shoulder sister site slice sofa son song spoon sport spring stair star station street student
summer sun supermarket surprise sweet table taxi teacher team teenager telephone television thing
ticket town train tree trip truck uncle vegetable village visit voice wall week weekend window
winter word worker world year zoo ant bear camel dolphin duck elephant frog giraffe insect kangaroo
lion monkey parrot penguin rabbit shark snake spider tiger whale zebra""".split()


def _plain_plurals():
    """{noun: noun + "s"} for the everyday nouns no group above already answers."""
    taken = set(_UNCOUNTABLE)
    for _pattern, words in _PLURAL_GROUPS:
        taken |= set(words)
    return {one: one + "s" for one in _PLAIN_NOUNS if one not in taken}


_PLURAL_GROUPS = _PLURAL_GROUPS + (("Most words just add s: cat and cats, plan and plans, house "
                                    "and houses.", _plain_plurals()),)


def _plurals_by_word():
    """Every word the table holds, with its plural and the pattern of its group."""
    table = {}
    for pattern, words in _PLURAL_GROUPS:
        for one, more in words.items():
            table[one] = (more, pattern)
    return table


PLURALS = _plurals_by_word()
# The plural words the table names, back to the singular, so "whats the plural of potatoes" is
# answered rather than shrugged at. Only where the two are different words: "sheep" is its own
# plural, and asking about that is a question about the singular.
PLURAL_SINGULARS = {more: one for one, (more, _pattern) in PLURALS.items() if more != one}
# The words of the ask itself, and the verb people use for it ("pluralise", "pluralize").
_PLURAL_ASK = ("plural", "plurals", "pluralise", "pluralize", "pluralised", "pluralized")
# How the ask is framed around the word: "the plural of crisis", "plural for crisis", "how do i
# make crisis plural", "whats crisis in the plural". Two words of the ask have to be in the line
# for the matcher to read it at all, and these are the ones people put there.
# "work", "made", "spelt" and "formed" are how the ask about the rule itself is worded:
# "how do plurals work", "how are plurals made", "how are plurals spelt". They are safe
# here because the row needs one of the ask words as well, and only a plural question holds
# those.
_PLURAL_ASK_FRAME = ("of", "for", "make", "say", "in", "to", "work", "works", "made", "spelt",
                     "spelled", "formed")
# A line about plurals in general, naming no word of its own: "how do i say plurals of words
# ending in y", "how do plurals work". There is no plural to give, and the rule itself is the
# answer, so the row says the whole rule instead of passing.
# "word" is here as well as "words": "whats the plural of a word ending in y" names the word
# "word", and answering "Words is the plural of word" missed the question, which is the rule.
# "plurals" is the ask said in its own plural: "how do plurals work" and "how are plurals
# made" named no word and fell to the shrug, because the general case knew the singular only.
_PLURAL_GENERAL = ("word", "words", "plurals", "nouns", "names")
_PLURAL_RULE = ("Most plurals just add s (cat, cats). Words ending in s, x, z, ch or sh take -es "
                "(bus, buses), a consonant then y becomes -ies (baby, babies), and -f or -fe "
                "turns into -ves (knife, knives).")


def _the_words_of(understood):
    """The line's own words, lowercased and with the punctuation taken off the ends."""
    return [str(one).lower().strip(string.punctuation)
            for one in (understood.get("words") or ())]


def _names_a_word_to_change(understood):
    """True when the line names a word this table has, or asks about plurals in general.

    The row is reached by the ask rather than by the word, so the guard is what keeps it off a
    plural question about a word another row answers better: "what is the plural of octopus" and
    "whats the plural of virus" belong to the row that says octopuses or octopi, and a line with
    no word of this table in it ("whats the plural of that", "how do plurals work" is the
    general case below) is no answer of this row's to give.
    """
    said = _the_words_of(understood)
    for word in said:
        if word in PLURALS or word in PLURAL_SINGULARS or word in _UNCOUNTABLE:
            return True
    if any(word in _PLURAL_GENERAL for word in said):
        return True
    # A noun the table does not hold is still covered, because the ending is the rule: the row
    # reads the word out of the line and declines it (see `_the_plural_by_its_ending`).
    return bool(_the_words_the_ask_names(understood))


# The sentence each ending gets, for a noun no group above holds. The groups are the fast path and
# these are the general one: "whats the plural of lettuce" was a search punt because lettuce is in
# no group, and every other noun in the language went the same way.
_PLURAL_RULE_SENTENCE = {
    "es": "Words ending in s, x, z, ch or sh take -es: bus and buses, box and boxes.",
    "ies": "A consonant then y becomes -ies: baby and babies, city and cities.",
    "oes": "A short list of -o words takes -es: potato and potatoes, hero and heroes.",
    "plain": "Most words just add s: cat and cats, house and houses.",
    # A borrowed -o word is the case the plain sentence explains worst: "Burritos is the plural
    # of burrito" followed by cat and house says nothing about why, and the -o split is the very
    # thing being asked. So the -o words in no list get the rule for -o words.
    "os": "A short -o word takes -es (potato and potatoes, echo and echoes); a -o word that "
          "takes a plain s does too, so it is burritos, avocados and pianos.",
}
# The -us words that also have a Latin plural people still use, which the sentence names beside
# the English one: "Cactuses is the plural of cactus, and cacti is the Latin form..."
_PLURAL_LATIN_TWIN = {"cactus": "cacti", "octopus": "octopi", "fungus": "fungi",
                      "nucleus": "nuclei", "syllabus": "syllabi"}

# The -o words that take -es. `#10028` wrote the rule and the sentence that names it ("potato and
# potatoes, hero and heroes") but the list itself never landed, so `_the_plural_by_its_ending`
# raised `NameError: name '_PLURAL_OES' is not defined` for every -o word the table does not
# already hold, and the arbiter swallows a module that raises: on main e1e39ba1 "plural of
# burrito" was the cold "Thanks for telling me" and "plural of avocado" the cold "I'm listening".
# The words below are the ones the sentence names plus the rest of the ordinary family; a word not
# here keeps the -os that most -o nouns take (photos, pianos, burritos, avocados).
# Two fixes for this same missing name landed (#11312 and #11496) and each brought its own copy of
# the list, so the second one silently won and "dingo" - which the first held - went back to
# "Dingos" while the test for it stayed red. There is one list now: the words both copies had,
# plus dingo and grotto.
_PLURAL_OES = frozenset({
    "potato", "tomato", "hero", "echo", "veto", "torpedo", "volcano", "mosquito", "buffalo",
    "domino", "cargo", "embargo", "mango", "tornado", "motto", "grotto", "dingo"})

# The nouns whose plural is the word itself. "The plural of moose is moose" is a fact no ending
# rule can reach, so the family is a list: the table holds the common ones (sheep, deer, fish,
# series) and these are the ones people ask about outside it. A word here says so rather than
# forming "mooses".
_PLURAL_SAME_WORD = {"moose", "bison", "swine", "spacecraft", "hovercraft", "salmon", "trout",
                     "cod", "grouse", "offspring", "corps", "means", "series", "species",
                     "aircraft", "deer", "sheep", "fish"}

# A word of these endings that no group holds has no plural to form: happiness, sadness,
# kindness are amounts, not counts. The money row already answers that way, and a formed
# "happinesses" is a worse answer than the sentence.
_PLURAL_NO_COUNT = ("ness",)
_PLURAL_NONE_SENTENCE = ("{Word} has no plural: it is an amount, not a count, so you would say "
                         "some {word}, or a bit of {word}.")

# Words the understanding engine hands over that are not nouns at all: a verb or an adjective
# cannot be declined, and "Hases is the plural of has" is a confident wrong answer. The general
# pattern is the honest reply, and it fails safe - a noun wrongly treated this way gets the
# pattern rather than a wrong word.
_PLURAL_NOT_A_NOUN_AT_ALL = {
    "has", "have", "had", "is", "was", "were", "be", "been", "am", "are", "do", "does", "did",
    "will", "would", "can", "could", "should", "may", "might", "must", "shall",
    "happy", "sad", "angry", "good", "bad", "nice", "big", "small", "little", "great", "lovely",
    "tired", "hungry", "thirsty", "cold", "hot", "warm", "wet", "dry", "fast", "slow", "easy",
    "hard", "difficult", "beautiful", "important", "different", "better", "best", "worse"}
_PLURAL_US_SENTENCE = "A -us word takes the English -es: virus and viruses, campus and campuses."

# The words of the ask itself, and the words that are never the noun it is about, so that
# "whats the plural of that" and "whats the plural of the word" name no noun and pass.
_PLURAL_NOT_THE_NOUN = {"the", "a", "an", "it", "that", "this", "these", "those", "there",
                        "word", "words", "noun", "nouns", "name", "names", "thing", "things",
                        "one", "ones", "and", "or", "is", "are", "was", "were", "be", "been",
                        "please", "thanks", "for", "of", "in", "to", "make", "say", "spell",
                        "spelling", "rule", "rules", "any", "some", "more", "up",
                        # the ask itself, in every way people type it: a line the understanding
                        # engine reads twice (once with the words of the line before it) used to
                        # give "Whatses is the plural of whats"
                        "what", "whats", "what's", "how", "do", "does", "did", "i", "you",
                        "we", "they", "me", "my", "tell", "give", "sentence", "sentences",
                        "about", "wrong", "right", "correct", "english",
                        # the bot has its own fact about wifi, and declining the word took that
                        # turn: a word with an answer of its own is not this row's to change
                        "wifi", "wi-fi", "internet", "broadband"}
_PLURAL_NOT_THE_NOUN |= set(_PLURAL_ASK) | set(_PLURAL_ASK_FRAME)


def _the_words_the_ask_names(understood):
    """The words the line asks the plural of, read after the ask; empty when it names none."""
    said = _the_words_of(understood)
    for at, word in enumerate(said):
        if word in _PLURAL_ASK or word in _PLURAL_ASK_FRAME:
            break
    else:
        return []
    named = [word for word in said[at + 1:]
             if word not in _PLURAL_NOT_THE_NOUN and word not in _PLURAL_ASK
             and not word.isdigit() and len(word) > 2 and word.isalpha()
             # a word the table or the -us family already holds keeps the row it has: this is
             # the general fallback for the nouns in no group, not a second owner for those
             and word not in PLURALS and word not in PLURAL_SINGULARS
             and word not in _UNCOUNTABLE and word not in _PLUS_FORMS]
    # One noun is the word to decline. Two are a phrase ("loft insulation", "mother in law"), and
    # the ending of the first word is not the plural of the phrase, so the rule is the answer -
    # not a pass, which handed the line to whichever row named the second word.
    return named


def _the_plural_by_its_ending(word):
    """The plural of a noun no group holds, and the sentence for its ending.

    Only the endings that are certain are read: -s, -x, -z, -ch, -sh take -es, a consonant then y
    becomes -ies, the -o words in the list take -es, and everything else adds s. A -f or -fe word
    is left to the group above, because half of them keep the -f (roof, chief, giraffe) and
    "giraves" is a worse answer than a punt.
    """
    if word in _PLURAL_SAME_WORD:
        return (f"{word.capitalize()} is its own plural - the same word for one and for many: "
                f"one {word}, two {word}.")
    if word.endswith(_PLURAL_NO_COUNT):
        return _PLURAL_NONE_SENTENCE.format(Word=word.capitalize(), word=word)
    if word in _PLURAL_NOT_A_NOUN_AT_ALL:
        return _PLURAL_RULE
    if word.endswith("us"):
        more = word[:-2] + "uses"
        twin = _PLURAL_LATIN_TWIN.get(word)
        if twin:
            return (f"{more.capitalize()} is the plural of {word}, and {twin} is the Latin form "
                    f"plenty of people still use. {_PLURAL_US_SENTENCE}")
        return f"{more.capitalize()} is the plural of {word}. {_PLURAL_US_SENTENCE}"
    if word.endswith(("s", "x", "z", "ch", "sh")):
        more = word + ("zes" if word.endswith("z") and not word.endswith("zz") else "es")
        rule = "es"
    elif word.endswith("y") and len(word) > 2 and word[-2] not in "aeiou":
        more, rule = word[:-1] + "ies", "ies"
    elif word.endswith("o"):
        # the list is the fast path, and a -o word in no list still has a rule of its own
        more, rule = (word + "es", "oes") if word in _PLURAL_OES else (word + "s", "os")
    else:
        more, rule = word + "s", "plain"
    return f"{more.capitalize()} is the plural of {word}. {_PLURAL_RULE_SENTENCE[rule]}"


def _plural_of(memory, understood):
    """The plural of the word the line asked about, with its pattern, or None to pass."""
    said = _the_words_of(understood)
    for word in said:
        if word in _PLURAL_GENERAL:
            continue    # "words" in "how do plurals of words work" names no word to change
        found = PLURALS.get(word)
        if found is not None:
            more, pattern = found
            if more == word:
                return (f"{word.capitalize()} is its own plural - the same word for one and for "
                        f"many: one {word}, two {word}. {pattern}")
            return f"{more.capitalize()} is the plural of {word}. {pattern}"
        one = PLURAL_SINGULARS.get(word)
        if one is not None:
            # "whats the plural of children" is a question about the singular, and the pair is a
            # better answer than a made-up plural of a plural.
            return (f"{word.capitalize()} is already plural - one {one}, two {word}. "
                    f"{PLURALS[one][1]}")
        if word in _UNCOUNTABLE:
            return (f"{word.capitalize()} has no plural in the everyday sense: you would say some "
                    f"{word}, or a bit of {word}, not {word}s.")
    for word in said:
        if word in _PLURAL_GENERAL:
            return _PLURAL_RULE
    asked = _the_words_the_ask_names(understood)
    if len(set(asked)) == 1:
        return _the_plural_by_its_ending(asked[0])
    if asked:
        return _PLURAL_RULE
    return None


# The word being changed is deliberately not a key word. A key of every noun and plural in the
# table would make each of those words less specific to every other row in this domain (the
# matcher ranks a row on the words only it asks for), and "how do i word a text cancelling dinner
# with a friend" lost its answer to the row about writing a text the moment "friend" appeared in a
# second key. The ask itself is the key, and `_plural_of` reads the word off the line; a plural
# question is the only line that holds these words, so the row reaches nothing else.
# The bias is what makes the ask win the line. The word being changed still reaches the rows about
# it - "whats the plural of tooth" found the bleeding-gums card and "how do i make box plural" the
# boxing one - and a row that named the thing score for score should not take a question about how
# the thing is spelt. Only a line that says plural pays it.
# "what is the past tense of swim" got the general tense card, which explains what a tense is and
# never says the word that was asked for, and "what is the past participle of swim" was a search
# hedge. The irregular verbs are a short closed list, so they are a table; a regular verb is the
# -ed rule. A frame word on its own is not this row's ("i feel tense", "in the past i could run"),
# which is why the key is the table and the ask, not the word tense.
IRREGULAR_VERBS = {
    "be": ("was", "been"), "become": ("became", "become"), "begin": ("began", "begun"),
    "break": ("broke", "broken"), "bring": ("brought", "brought"), "build": ("built", "built"),
    "buy": ("bought", "bought"), "catch": ("caught", "caught"), "choose": ("chose", "chosen"),
    "come": ("came", "come"), "do": ("did", "done"), "drink": ("drank", "drunk"),
    "drive": ("drove", "driven"), "eat": ("ate", "eaten"), "fall": ("fell", "fallen"),
    "feel": ("felt", "felt"), "fight": ("fought", "fought"), "find": ("found", "found"),
    "flee": ("fled", "fled"), "fly": ("flew", "flown"), "forget": ("forgot", "forgotten"),
    "get": ("got", "got"),
    "give": ("gave", "given"), "go": ("went", "gone"), "grow": ("grew", "grown"),
    "have": ("had", "had"), "hear": ("heard", "heard"), "hide": ("hid", "hidden"),
    "hold": ("held", "held"), "keep": ("kept", "kept"), "know": ("knew", "known"),
    "leave": ("left", "left"), "lose": ("lost", "lost"), "make": ("made", "made"),
    "meet": ("met", "met"), "pay": ("paid", "paid"), "put": ("put", "put"),
    "read": ("read", "read"), "ride": ("rode", "ridden"), "ring": ("rang", "rung"),
    "rise": ("rose", "risen"), "run": ("ran", "run"), "say": ("said", "said"),
    "see": ("saw", "seen"), "sell": ("sold", "sold"), "send": ("sent", "sent"),
    "sing": ("sang", "sung"), "sit": ("sat", "sat"), "sleep": ("slept", "slept"),
    "speak": ("spoke", "spoken"), "spend": ("spent", "spent"), "stand": ("stood", "stood"),
    "steal": ("stole", "stolen"), "swim": ("swam", "swum"), "take": ("took", "taken"),
    "teach": ("taught", "taught"), "tell": ("told", "told"), "think": ("thought", "thought"),
    "throw": ("threw", "thrown"), "understand": ("understood", "understood"),
    "wake": ("woke", "woken"), "wear": ("wore", "worn"), "win": ("won", "won"),
    "write": ("wrote", "written"),
    # the ones that do not change at all: "what is the past tense of cut" got "Cut -> cutted"
    "bet": ("bet", "bet"), "burst": ("burst", "burst"), "cast": ("cast", "cast"),
    "cost": ("cost", "cost"), "cut": ("cut", "cut"), "hit": ("hit", "hit"),
    "hurt": ("hurt", "hurt"), "let": ("let", "let"), "quit": ("quit", "quit"),
    "set": ("set", "set"), "shut": ("shut", "shut"), "split": ("split", "split"),
    "spread": ("spread", "spread"),
}
# The ask has to say past or participle: a bare "tense" reaches "i feel tense", and a bare "past"
# reaches "in the past i could run". Both are somebody else's line.
_PAST_ASK = ("past tense", "past simple", "past participle", "past form", "participle",
             "past of", "what is the past", "what's the past", "whats the past",
             "irregular verb", "irregular verbs")
# "how do i say" is not in that list on purpose: it brings "do" and "have" with it, so
# "how do i say no to my friend" would be a question about the verb do.
_VOWELS = "aeiou"
# British spelling doubles the l on these, and the vowel-group count cannot see why: travel and
# cancel are stressed on the first syllable and still take travelled and cancelled here, where
# American spelling has one l. A short list beats a stress rule nobody can compute from spelling.
_DOUBLED_L = {"travel", "cancel", "label", "signal", "model", "level", "dial", "patrol",
              "total", "tunnel", "fuel", "marshal", "worship", "kidnap", "handicap"}


def _line_text(understood):
    return ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()


def _regular_form(verb):
    """The past tense a regular verb takes, by the spelling rules people are taught.

    An e takes a d (hope, hoped); a consonant and a y becomes -ied (carry, carried); a one
    syllable verb ending in one vowel and one consonant doubles that consonant (stop, stopped).
    The vowel-group count is what keeps "visit" and "open" from becoming "visitted" and
    "openned"."""
    if not verb:
        return verb + "ed"
    if verb.endswith("e"):
        return verb + "d"
    if verb.endswith("y") and len(verb) > 1 and verb[-2] not in _VOWELS:
        return verb[:-1] + "ied"
    if verb in _DOUBLED_L:
        return verb + verb[-1] + "ed"
    if len(verb) > 2 and verb[-1] not in _VOWELS and verb[-1] not in "wxy":
        if verb[-2] in _VOWELS and verb[-3] not in _VOWELS:
            groups, previous = 0, False
            for letter in verb:
                vowel = letter in _VOWELS
                if vowel and not previous:
                    groups += 1
                previous = vowel
            if groups == 1:
                return verb + verb[-1] + "ed"
    return verb + "ed"


def _irregular_past(memory, understood):
    """The two forms of the verb the line names, in the words of a person asking.

    The verb is the one after "past ... of", the same way the regular row reads it. Scanning the
    line for the first table verb instead was a fault of its own: "can you tell me the past tense
    of swim" is a question about swim, and tell and do are in the table and come first, so the
    person got a confident answer about a verb they did not ask about."""
    text = _line_text(understood)
    match = _PAST_OF.search(text)
    if not match or match.group(1) not in IRREGULAR_VERBS:
        return None
    verb = match.group(1)
    past, participle = IRREGULAR_VERBS[verb]
    if participle == past:
        return ("The past tense of " + verb + " is " + past + ", and the past participle is the "
                "same: 'I " + past + " it yesterday, I have " + past + " it before.' Most verbs "
                "just add -ed (walk, walked), so the irregular ones are the ones worth learning.")
    return ("The past tense of " + verb + " is " + past + " - 'I " + past + " yesterday' - and "
            "the past participle is " + participle + ", the one that goes with have: 'I have "
            + participle + "'. Most verbs just add -ed (walk, walked), so the irregular ones are "
            "the ones worth learning.")


# A regular verb is the other half of the same homework question, and "what is the past tense of
# walk" got the general tense card too. This row reads the verb off the line and applies the rule;
# it stands down whenever the verb is in the table, because then the answer is the two forms.
_PAST_OF = re.compile(r"past (?:tense |form |participle |simple )?of (?:the verb )?([a-z]+)")


def _names_a_past_table_verb(understood):
    """The row's own question: a frame saying "past ... of", and a verb of the table after it.

    Without it the table in the key means any mention of any table verb: "when do i use past
    tense" is not the past tense of do, and "i have a question about past tense" is not the past
    tense of have."""
    match = _PAST_OF.search(_line_text(understood))
    return bool(match) and match.group(1) in IRREGULAR_VERBS


def _names_a_past_verb(understood):
    match = _PAST_OF.search(_line_text(understood))
    if not match or match.group(1) in IRREGULAR_VERBS:
        return False
    return True


# One word, two verbs: "lie" is lay/lain when you recline and lied when you tell a lie, and the
# -ed rule alone gives a learner the wrong one for the question they nearly always mean.
_TWO_VERBS = {
    "lie": ("Lie is two verbs. Lying down is lie, lay, lain: 'I lay on the bed', 'I have lain "
            "there'. Telling a lie is lie, lied, lied: 'I lied to him'. The one people get wrong "
            "is the reclining one - 'I laid on the bed' should be 'I lay on the bed', because "
            "laid is the past of lay, meaning to put something down."),
    "lay": ("Lay is laid, laid: 'I laid the table', 'I have laid it out'. The trap is that lay is "
            "also the past of lie, the lying-down verb - so 'I lay on the bed' is correct for "
            "reclining, and 'I laid the baby on the bed' is correct for putting her down. If you "
            "can replace it with put, use laid."),
}


def _regular_past(memory, understood):
    """The -ed rule, with the verb the line names."""
    match = _PAST_OF.search(_line_text(understood))
    if not match:
        return None
    verb = match.group(1)
    if verb in IRREGULAR_VERBS:
        return _irregular_past(memory, understood)
    if verb in _TWO_VERBS:
        return _TWO_VERBS[verb]
    if len(verb) > 12:
        # no English verb is this long, so the word is a name, a typo or a made-up one: say so
        # rather than put "flibbertigibbeted" in front of somebody as if it were a word
        return ("I don't know a verb '" + verb + "'. If it is a name or a made-up word the -ed "
                "rule still gives " + verb + "ed, and if it is a typo the nearest real verb is "
                "the one to take.")
    return (verb.capitalize() + " -> " + _regular_form(verb) + ". Regular verbs add -ed; after "
            "an e it is just -d (hope -> hoped), a consonant and a y becomes -ied (carry -> "
            "carried), and a one-syllable verb doubles its last letter (stop -> stopped). If none "
            "of that fits, it is irregular: swim -> swam, buy -> bought.")


ENTRIES.append(entry("regular-past", (_PAST_ASK, _PAST_ASK), _regular_past, bias=3,
                     guard=_names_a_past_verb))
ENTRIES.append(entry("irregular-past", (tuple(IRREGULAR_VERBS), _PAST_ASK), _irregular_past,
                     bias=4, guard=_names_a_past_table_verb))
ENTRIES.append(entry("plural-word", (_PLURAL_ASK, _PLURAL_ASK_FRAME), _plural_of, bias=4,
                     guard=_names_a_word_to_change))

# The parts of a sentence: "what is a verb" and "what is a noun" were both hedges on main. One
# entry answers them all, because the question is the same - name the job the word does - and the
# answer names whichever term the line used.
GRAMMAR_TERMS = {
    "noun": "A noun names a person, place or thing - Jess, Leeds, table, kindness. If you can put "
            "'the' in front of it, it is a noun.",
    "verb": "A verb is the doing or being word: run, eat, seems, is. Every sentence needs one, and "
            "the verb changes with the time - I walk today, I walked yesterday.",
    "adjective": "An adjective describes a noun: a red bus, a tired dog, an honest answer. It sits "
                 "before the noun or after 'is' - the bus is red.",
    "adverb": "An adverb says how, when or where something happened: she sang loudly, we left "
              "early, he waited outside. Many end in -ly, but not all do (soon, well, fast).",
    "pronoun": "A pronoun stands in for a noun so you are not repeating it: I, you, he, she, it, "
               "we, they, me, him, her, them. 'Sam lost Sam's keys' is why we have them.",
    "preposition": "A preposition says where or when in relation to something: in, on, under, "
                   "between, before, after, with. The cat sat on the mat - 'on' is the preposition.",
    "conjunction": "A conjunction joins words or clauses: and, but, because, although, so. 'I was "
                   "late because the bus broke down' joins two ideas with 'because'.",
    "tense": "Tense is when the verb happens: past (I cooked), present (I cook, I am cooking), "
             "future (I will cook). Pick one and keep to it within a sentence.",
    "clause": "A clause is a group of words with its own verb and subject: 'when the bus came' and "
              "'we got on'. A sentence is one or more clauses; a phrase has no verb at all.",
    "sentence": "A sentence needs a subject and a verb and makes one complete point, starting with "
                "a capital and ending with a full stop: 'The bus was late.'",
    "fronted adverbial": "A fronted adverbial is the phrase that opens a sentence and says when, "
                         "where or how: 'After lunch, we walked.' 'Slowly, the door opened.' Put a "
                         "comma after it, and make sure the thing it describes is the subject of "
                         "the sentence - 'Walking home, the rain started' says the rain was walking.",
    "split infinitive": "A split infinitive puts a word between to and the verb: 'to boldly go'. "
                        "It is not an error, whatever you were taught - split it when it reads "
                        "better and move the word when it gets clumsy: 'to go boldly'.",
    "dangling modifier": "A dangling modifier is an opening phrase that describes the wrong thing: "
                         "'Walking to work, the rain soaked me' says the rain was walking. Name "
                         "the person straight after the comma - 'Walking to work, I was soaked by "
                         "the rain' - or turn the phrase into a clause.",
    "whom": "Use whom after a preposition and where it is the one being acted on: 'to whom it may "
            "concern', 'the person whom I met'. If you can say he or she, write who; if you would "
            "say him or her, write whom. In speech who nearly always sounds right.",
    "adverbial": "An adverbial is any phrase that says when, where, how or why: 'at six', 'in the "
                 "kitchen', 'very slowly', 'because it rained'. It is not always an adverb - it "
                 "can be a whole phrase or clause.",
    "apostrophe": "An apostrophe does two jobs: it marks something missing (do not becomes don't) or "
                  "shows belonging (Jess's coat). It never makes a plain plural - two cats, not two "
                  "cat's.",
    # The marks people meet without a name for them: "what is an ampersand" and "what is that
    # wavy line called" were both a search hedge. They are terms like noun and clause, so they
    # sit in the same table and answer with the name, the meaning and where the key is.
    "hashtag": "A hashtag is the # sign used as a label: #slowcooking groups posts about one thing. "
               "On a UK keyboard it is Shift and 3, and on a phone it is on the symbols page.",
    "number sign": "The number sign is # - Shift and 3 on a UK keyboard. In the US it is how you "
                   "write a number (No. 5) and online it starts a hashtag.",
    "ampersand": "An ampersand is the & sign and it means 'and'. Write and out in a sentence; the "
                 "sign is for names and headings, like Marks & Spencer or R&D.",
    "at sign": "The at sign is @ - Shift and 2 on a UK keyboard - and it is in every email "
               "address: name@example.com.",
    "asterisk": "An asterisk is the * sign, a small star. It marks a footnote or shows anything goes "
                "(*), and on a phone keyboard it is usually behind the ?123 key.",
    "slash": "A slash is the / sign, and it mostly means 'or' (and/or) or separates the parts of a "
             "date (12/05/2024). A backslash \\ is the other way over and turns up in computer paths "
             "rather than in writing.",
    "backslash": "A backslash is the \\ sign, the mirror of a slash. It almost never belongs in "
                 "writing - it separates folders in a Windows file path, like C:\\Users\\me.",
    "underscore": "An underscore is the _ sign, the low line under a letter. It joins words in file "
                  "names and usernames (my_notes.txt); a hyphen is the shorter mark at half height.",
    "tilde": "A tilde is the ~ sign, the small wavy line. It means 'about' (~20 people came), and on "
             "most keyboards it is Shift and the hash key.",
    "pipe": "A pipe is the | sign, the upright bar. Most people call it the pipe or the vertical bar, "
            "and it separates options in a computer command; in writing a slash does the job better.",
    "caret": "A caret is the ^ sign, a small wedge above the line. In proofreading it marks where a "
             "word is to be slipped in, and in maths it means to the power of - 2^3 is eight.",
    "bullet point": "A bullet point is the dot that starts each item in a list. Keep every item to a "
                    "line, start each one the same way, and leave the full stops off short items.",
    "curly bracket": "Curly brackets { } group things in maths and code, and square brackets [ ] hold "
                     "your own words inside someone else's quotation. Round brackets ( ) take an "
                     "aside the sentence could do without.",
    "square bracket": "Square brackets [ ] hold your own words inside a quotation, and they mark a "
                      "missing word in a transcript: 'she said it was [unclear] on the tape'.",
    "angle bracket": "Angle brackets < > mark a tag in code and stand in for a word to fill in later, "
                     "as in <your name>. The plain brackets ( ) are the ones for writing.",
}
_GRAMMAR_WORDS = tuple(GRAMMAR_TERMS) + ("grammar", "parts of speech", "word class")
_GRAMMAR_ASK = ("what is", "whats", "what's", "what are", "mean", "meaning", "definition",
                "define", "explain", "difference", "example", "how do i know", "simple terms",
                "use", "uses", "when do i", "where do i", "for kids", "for a child",
                # "what is an ampersand" and "what are curly brackets called" name the mark and
                # ask for its name, which is the same question as "what does it mean"
                "called", "what do you call", "what is that", "what is this", "name of",
                "which key", "what key")


def _grammar_term(memory, understood):
    # The words as words, not as a joined string: "verb" is inside "adverb", and a joined line
    # answered "what does adverb mean" with the verb.
    said = [str(word).lower() for word in (understood.get("words") or ())]
    flat = " ".join(said)
    for phrase, reply in GRAMMAR_TERMS.items():
        # a word is compared as a word, its plural allowed: "noun" is inside "pronoun" and "verb"
        # inside "adverb", and a substring test answered "what is a pronoun" with the noun
        if phrase in said or phrase.rstrip("s") + "s" in said:
            return reply
        if " " in phrase and phrase in flat:
            return reply
    return ("The parts of a sentence, in the order they turn up: a noun names something, a verb is "
            "what it does or is, an adjective describes it, an adverb says how the doing happened, "
            "and a pronoun stands in for the noun. 'The tired dog slept badly' - dog is the noun, "
            "tired the adjective, slept the verb, badly the adverb.")


# A definition question is about the word. A line whose subject is a person who forgets, repeats
# himself or is losing his words is a question about that person, and the grammar word is only
# how the line says it: "my husband forgets what he is saying mid sentence" was answered with
# what a sentence is, which is not the thing being asked. The card stands down for those lines
# and `science.parent-memory` answers them.
_SOMEBODY_FORGETTING = re.compile(
    r"\b(?:keeps?\s+forgetting|forgets|forgetting|forgot|repeats?\s+(?:himself|herself|"
    r"themselves|itself)|cant\s+remember|can't\s+remember|mid\s+sentence|"
    r"cant\s+find\s+(?:his|her|their)\s+words|can't\s+find\s+(?:his|her|their)\s+words)\b")


def _nobody_in_the_line_is_forgetting(understood):
    """True unless the line is about a person losing their words, not about the words."""
    if not isinstance(understood, dict):
        return True
    said = " ".join(str(understood.get("clean") or understood.get("text") or "").split()).lower()
    return not _SOMEBODY_FORGETTING.search(said)


ENTRIES.append(entry("grammar-term", (_GRAMMAR_WORDS, _GRAMMAR_ASK), _grammar_term,
                     # the word pairs have their own answers, and a spelling question is not a
                     # definition question
                     avoid=("spell", "spelling", "spelt", "difference between affect",
                            "affect", "effect", "apostrophe its", "its or it's"),
                     ask=_GRAMMAR_ASK, guard=_nobody_in_the_line_is_forgetting))


# The shapes a poem takes, one answer per form, in the same way as the figures of speech. "what is
# a sonnet" was a search hedge and "what is a stanza" a different shrug, while "what is a limerick"
# wrote one; the form is a fact about the poem, so the fact is the answer.
_POEM_FORMS = (
    (("sonnet", "sonnets"),
     "A sonnet is fourteen lines in iambic pentameter - ten syllables a line, stress on every "
     "second one. Shakespeare's kind rhymes in three quatrains and a closing couplet (abab cdcd "
     "efef gg) and turns at line nine; the Italian kind splits six and eight."),
    (("stanza", "stanzas", "verse paragraph"),
     "A stanza is a group of lines set apart in a poem, the way a paragraph is in prose. Two lines "
     "are a couplet, four a quatrain, and the pattern of rhymes across them is the rhyme scheme."),
    (("free verse", "free-verse"),
     "Free verse is poetry with no fixed metre and no rhyme: the line breaks and the rhythm of the "
     "sentences do the work instead. Most modern poetry is written this way."),
    (("iambic pentameter", "iambic", "pentameter", "blank verse"),
     "Iambic pentameter is five beats of da-DUM to the line - ten syllables with the stress on "
     "every second one: 'Shall I compare thee to a summer's day'. Blank verse is that without "
     "rhyme, which is what most of Shakespeare's plays are in."),
    (("couplet", "couplets"),
     "A couplet is two lines that rhyme and usually stand together: 'Good night, good night! "
     "Parting is such sweet sorrow / That I shall say good night till it be morrow.'"),
    # "what is a ballad" was answering testicle pain, off the sound of the word; the song sense
    # and the poem sense are the same answer, because a ballad is a story told to a tune
    (("ballad", "ballads"),
     "A ballad is a story told in short verses, meant to be sung or recited: four-line stanzas "
     "that rhyme abab or abcb, with a refrain that comes back. The old folk ballads are the kind "
     "that run to a dozen verses, and pop still uses the name for a slow song about one feeling."),
)
_POEM_ASK = ("what is", "whats", "what's", "what are", "mean", "meaning", "definition", "define",
             "explain", "example", "how many lines", "structure", "form", "difference", "written",
             "write a", "poem", "poetry")


def _poem_form(memory, understood):
    said = [str(word).lower() for word in (understood.get("words") or ())]
    flat = " ".join(said)
    for word, reply in _POEM_FORMS:
        for one in word:
            if one in said or (" " in one and one in flat):
                return reply
    return ("A haiku is three lines of five, seven and five sounds; a limerick is five lines "
            "rhyming aabba with a joke in it; a sonnet is fourteen lines in iambic pentameter. Ask "
            "about one and I'll give you its shape.")


ENTRIES.append(entry("poem-form", (tuple(word for words, _ in _POEM_FORMS for word in words),
                                   _POEM_ASK), _poem_form,
                     # a poem asked for, not a poem explained: the verse cards own those lines
                     avoid=("write me", "write a poem", "write one", "about my", "for my",
                            "birthday", "wedding", "card", "funny", "sad poem", "short poem"),
                     ask=_POEM_ASK))
# Two things people write every week and the bot shrugged at: the review of a book, and an email
# that has to get an answer. Neither is a grammar question, so both live here with the other
# writing jobs rather than in a table of terms.
ENTRIES.append(entry(
    "book-review",
    (("book review", "book reviews", "review a book", "reviewing a book", "review of a book",
      "review the book", "book report"),
     ("how do i", "how", "write", "writing", "start", "structure", "what should", "should i",
      "begin", "open", "good", "help",
      # "what is a book review" asked for the shape of one and got the football yellow card,
      # because "book" is a form of "booked". The definition is the writing job too.
      "what is", "whats", "what's", "define", "definition", "what makes")),
    "Open with your verdict in one sentence, then say what the book tries to do and whether it "
    "works: a paragraph on the whole thing, a paragraph for each point you want to make with a "
    "quote or a page number, and no more than a few lines of plot. Leave the ending out, and "
    "finish with who the book suits, so the reader can decide.",
    # a film, a restaurant and an album have their own reviews, and a review of something you
    # bought is a complaint or a refund question
    avoid=("film", "movie", "tv", "netflix", "restaurant", "hotel", "album", "gig", "concert",
           "video game", "app", "product", "amazon", "perfume", "refund", "faulty", "broken",
           "return it", "one star", "bad review", "left a review")))

def _write_an_email(memory, understood):
    """The shape of an email, with the sample subject line in the world the line names.

    The card's own example was "Invoice 2144 - payment due", so "how do i email my teacher" and
    "how do i email my plumber" were answered about an invoice: right about the shape of a
    message and wrong about the person's life, which reads as a different answer altogether.
    Only the example moves; every sentence after it is the same advice.
    """
    from ..compose.draft import example_subject
    return (
        "Put the ask in the subject line and in the first sentence: \"%s\" tells them what it "
        "is before they open it. Then three or four sentences - what you want, the one or two "
        "facts they need, and by when - and a plain sign-off with your name. If you want an "
        "answer, say what happens next: \"If I do not hear back by Friday I will call.\""
        % example_subject(understood))


ENTRIES.append(entry(
    "write-an-email",
    (("email", "emails", "e-mail", "e mail", "an email to my boss", "email to a company",
      "email a company", "chase by email"),
     ("how do i", "how", "write", "writing", "subject", "structure", "what should",
      "should i", "phrase")),
    _write_an_email,
    # work.py's email-tone row already answers a formal, polite or firm email well, so this row
    # stands down and leaves those lines to it
    avoid=("start an email", "start the email", "start my email", "how do i start",
           # the question has a direction, and this row answers only one of them: an email the
           # person is about to write. A line about an email somebody sent them, or about somebody
           # not answering, is the other direction and its own card answers it - "my boss ignores
           # my emails for weeks, what should i do" was told to put the ask in the subject line,
           # and "my boss keeps sending sarky emails, how do i reply" with it.
           "ignores my email", "ignores my emails", "ignoring my email", "ignoring my emails",
           "wont reply", "won't reply", "wont answer", "won't answer", "doesnt reply",
           "doesn't reply", "not replying", "hasnt replied", "hasn't replied", "never replies",
           "no reply", "keeps sending", "keeps emailing", "sent me an email", "sent me a email",
           "sending me", "sends me", "emailed me", "email from", "emails from", "message from",
           "formal", "polite", "professional", "rude", "angry", "tone", "friendly", "blunt",
           "firm", "sounds",
           # a farewell or a last-day message is the notice card's, and a leaving do has its own
           "leaving", "leaving do", "last day", "goodbye", "farewell", "gushy", "my team",
           # an email with a named job in it has its own card - a deadline extension, a
           # resignation, a complaint, an application, a thank-you after an interview - and this
           # row was taking them all with "how do i write an email"
           "deadline", "extension", "extensions", "resign", "resigning", "quit", "notice",
           "applying", "application", "applications", "job", "jobs", "interview", "interviewer",
           "reference", "references", "cover letter", "cv",
           "complain", "complaining", "complaint", "complaints",
           # saying you are ill is the calling-in-sick answer, not the shape of an email
           "sick", "ill", "unwell", "poorly", "doctor",
           # an email that will not send, an address or a password is a technology question
           "not working", "won't send", "wont send", "bounce", "bounced", "spam", "junk",
           "inbox", "gmail", "outlook", "yahoo", "password", "hacked", "phishing", "scam",
           "set up", "setup", "sign in", "log in", "login", "account", "address", "attachment",
           "unsubscribe", "mailing list", "newsletter", "marketing",
           # "how do i stop getting so many emails" asked about the number of them and got
           # this row's subject-line advice. A line that counts the emails is the inbox
           # question (`too-many-emails`), not the writing one.
           "so many emails", "so many email", "too many emails", "fewer emails", "less email",
           "loads of emails", "hundreds of emails", "flood of emails", "emails every day",
           "emails all day", "stop getting", "stop the emails", "drowning in email",
           "swamped with email", "filter emails", "filter the emails", "sort out my emails",
           "reduce emails", "reduce the emails",
           # "how do i scan a letter and email it" is a scanner question that read `email` and
           # `how`: the scanning row answers it
           "scan", "scanner", "scanning", "scanned")))

# What happened to the person is news, not a request for writing technique. The swap reader
# rewrites a bare follow-up into the earlier question with the new words in it ("whats a good
# opening line for a book" then "i quit" is read as "whats a good opening line for a i quit"), the
# entry reached is the one already on the screen, and one sentence of it comes back under "Then
# the same holds". Nobody asks a writing card about their own notice: the card that knows the
# situation (quit-a-job-message, the money cards, the health ones) answers it, so the writing
# cards stand down for these phrases.
PERSONAL_NEWS = ("i quit", "i want to quit", "i am quitting", "im quitting", "i resigned",
                 "i got fired", "i was sacked", "i lost my job", "i got the job",
                 "i handed in my notice", "i am pregnant", "im pregnant")

# The short message is the writing job people ask for most, and "can you help me write a text to
# my boss" was the composer's "give me who it's for and the one thing you need from them" - true,
# but the person asked for the message, not for a form to fill in. A three-line shape answers it
# before they have said what it is about, and the details then only fill it in.
ENTRIES.append(entry(
    "write-a-text",
    (("text", "texts", "txt", "message", "messages", "whatsapp", "sms", "dm",
      # "how do i reply to a message" was the card-chargeback row, which keys "reply" beside
      # "how do i": answering a message is a drafting job, and the drafting card should have it
      "reply", "replies", "reply to", "text back", "respond", "response"),
     ("help me write", "help me word", "write", "writing", "draft", "word it", "wording",
      "how do i", "how", "what should",
      "how do i say", "how should i say", "what should i say", "how do i ask", "how to ask",
      "text to", "message to", "whatsapp to", "open a text",
      "start a text", "start the text")),
    "Three short lines: what it is about, what you want, and a thanks. \"Hi Sam, could we talk "
    "about the rota this week? Thursday suits me best. Thanks.\" No apology paragraph at the "
    "front, and say who you are if they may not have your number - tell me who it is for and "
    "what you need and I will write yours.",
    # an email, a letter, a card and a review are writing jobs with a card of their own, and a
    # message that already arrived is a reading question rather than a writing one
    avoid=("email", "emails", "e-mail", "e mail", "letter", "letters", "card", "cards",
           "cover letter", "cv", "resume", "essay", "assignment", "homework", "review",
           "review", "feedback", "complaint", "complaining", "resign", "resigning",
           # a message about a neighbour, a landlord or a repair is worded by the card that
           # knows the situation; the three-line text is for the everyday ask
           "loud music", "music at night", "noise at night", "landlord", "landlady",
           "boiler", "leaking", "repair",
           # a message that says you are leaving a job is the notice card's
           "leaving", "last day", "farewell", "goodbye", "my team", "notice",
           "noticed", "got a text", "got a message", "received", "from my bank", "screenshot",
           "what does it mean", "mean", "means", "spam", "scam", "phishing", "wrong number",
           "not delivered", "wont send", "won't send", "blocked", "delete", "deleted",
           # an apology that has arrived is answered, not drafted: "how do i reply to an
           # apology" and "what do i say when someone apologises" were handed this three-line
           # text, which is the message you write first, and `wording.accept-an-apology` is the
           # row for the one you are answering. A text you write to say sorry yourself keeps
           # this row.
           "reply to an apology", "respond to an apology", "answer an apology",
           "reply to a sorry", "accept an apology", "accepting an apology",
           "someone said sorry", "someone says sorry", "someone apologises",
           "someone apologized", "someone apologised", "said sorry to me", "says sorry to me",
           "apologised to me", "apologized to me", "apologises to me", "apologizes to me",
           "when someone apologises", "when someone apologized", "when someone says sorry",
           # deciding whether to send at all is the composer's question, not a drafting one
           "my ex", "an ex", "to my ex", "should i send",
           # a seller or a company that will not answer is a chargeback, and a message that will
           # not send is a phone problem
           "seller", "company", "refund", "money back", "chargeback", "charged", "paid by card",
           "ignoring", "ignored", "unresponsive", "not sending", "wont send", "won't send",
           # an invitation is an RSVP and a job offer is a career answer: both have their own card
           "invitation", "invitations", "rsvp", "wedding", "job offer", "job offers", "offer",
           "interview", "interviewer", "recruiter", "application", "accept the",
           # a register ask ("sound more professional", "more formal") is its own answer, and
           # deciding when or whether to send is a question about the situation, not the words
           "professional", "formal", "polite", "register",
           "how long", "how soon", "how often", "how many days", "first date", "second date",
           "before texting", "when to text", "should i wait", "how many texts") + PERSONAL_NEWS,
    bias=1))

# The blurb on the back of a book is a writing job of its own, and "how do i write a book
# blurb" was the yellow card. It is not the review: a review says whether to read it, a blurb
# sells it without giving the ending away, so it gets its own card rather than the review's.
ENTRIES.append(entry("book-blurb",
      (("blurb", "blurbs", "back cover", "back of the book", "jacket copy", "cover copy",
        "book description", "synopsis"),
       ("write", "writing", "written", "how do i", "how to", "book", "novel", "help",
        # "what is a blurb" is the same job asked as a definition, and it hedged
        "what is", "whats", "what's", "define", "definition")),
      "Write it in three moves: who the person is and what they want, the thing that gets in "
      "the way, and the question the reader will buy the book to answer - all in the present "
      "tense and under 200 words. Keep the climax out of it, end on the question rather than "
      "the answer, and read it aloud once: a blurb with the names of five characters in it "
      "reads like a synopsis.",
      # a synopsis of a study, a film's blurb and the school book report are other questions
      avoid=("film", "movie", "netflix", "series", "episode", "school", "book report",
             "summary", "summarise", "summarize", "essay", "assignment", "class", "teacher",
             "dissertation", "thesis", "paper", "research", "abstract"),
      bias=1))


# An obituary is the one written notice most people meet once and cold: "how do i write an
# obituary" was a shrug, and the eulogy card beside it is a speech, not a notice.
ENTRIES.append(entry("write-an-obituary",
      (("obituary", "obituaries", "death notice", "death notices", "announce a death",
        "announcement of a death", "notice of death", "in the paper", "in the newspaper"),
       ("write", "writing", "how do i", "how to", "word", "wording", "draft", "what do i put",
        "what to include", "help", "structure", "should i")),
      "Five things in the first two sentences: full name, age, where they lived, the date they "
      "died, and who they leave behind. Then one or two sentences of character - what they did "
      "for a living, what they loved, a phrase people will recognise - and the funeral or "
      "donation details at the end. Ring the funeral director first: they will word it with you "
      "and most put it on their own website free, and a local paper charges by the line.",
      # a eulogy is read aloud, a funeral question is a cost or a plan, and a will is another job
      avoid=("eulogy", "speech", "read out", "what do i say", "what to say", "condolence",
             "sympathy", "cost", "costs", "price", "how much", "pay for", "funeral plan",
             "will", "probate", "grief", "grieving", "miss her", "miss him"),
      bias=1))

# Two forms with fixed rules, and both were a hedge. Like the blurb, they are writing jobs with
# an answer rather than a matter of taste, so they get a card each.
# A line that asks for the thing itself is not asking how the form works. "give me a limerick",
# "write a limerick" and "write me a limerick" were answered with this card's rules for how to
# write one, while "how do i write a limerick", "how to write a limerick" and "tips for
# writing a limerick" are the method questions it is for. The shape of the ask, not a word in
# it, is what tells them apart, so the row has a guard rather than another fence: a line that
# opens with the writing verb and carries no method word stands this card down and the verse
# card writes the poem.
_VERSE_INSTANCE_LEAD = re.compile(
    r"^(?:please |can you |could you |will you |would you |ok |okay |so |and )*"
    r"(?:give|write|make|compose|pen|say|tell|do|recite|sing)\b")
_VERSE_METHOD_WORDS = frozenset((
    "how", "howto", "tips", "tip", "advice", "structure", "form", "forms", "rules", "rule",
    "explain", "explained", "guide", "better", "improve", "learn", "teach", "what", "whats",
    "why", "difference", "example", "examples", "start", "begin", "beginning", "method",
    "rhyme", "rhymes", "rhythm", "beats", "syllables", "lines", "write", "writing", "written"))


def _asks_for_the_verse(understood):
    """True when the line asks for a poem of this form rather than for its rules."""
    words = [str(word).lower() for word in (understood.get("words") or ())]
    if not words:
        return False
    # "write" and "writing" are in both lists on purpose: the verb opens the instance ask, and
    # any other word of the method in the line turns it back into a question about the form.
    if any(word in _VERSE_METHOD_WORDS and word not in ("write", "writing")
           for word in words):
        return False
    return bool(_VERSE_INSTANCE_LEAD.match(" ".join(words)))


ENTRIES.append(entry("write-a-limerick",
      (("limerick", "limericks", "funny poem", "silly poem", "rhyming joke"),
       # a definition question is not a request to write one: "what is a limerick" is the
       # poem-form card's line, so the asking words here are the writing ones only
       ("write", "writing", "how do i", "how to", "make up", "compose", "help", "give me",
        "can you")),
      "Five lines that rhyme AABBA, and the rhythm is the whole thing: three beats then three "
      "then three on the first two lines, two then two on the short ones, then back to three. "
      "Put a person and a place in line one (\"A fellow who lived in Peru\"), keep line five for "
      "the punchline, and read it aloud - if a beat is missing, the joke dies.",
      # a limerick is a place as well as a poem, and a joke or a song is another ask. A line
      # that names a subject ("write a limerick about my dog") is not asking how the form works:
      # the verse card writes that one, so this card stands down for it.
      avoid=("ireland", "county", "city", "accent", "joke", "song", "school", "homework",
             "essay", "assignment", "class",
             "about", "for my", "for a", "for the", "for her", "for him", "for their"),
      guard=lambda understood: not _asks_for_the_verse(understood),
      bias=1))
ENTRIES.append(entry("write-a-sonnet",
      (("sonnet", "sonnets", "shakespearean sonnet", "petrarchan sonnet"),
       ("write", "writing", "how do i", "how to", "form", "rhyme", "structure", "help",
        "give me", "can you")),
      "Fourteen lines of iambic pentameter - ten beats a line, da-DUM five times - with either "
      "ABAB CDCD EFEF GG (Shakespeare's) or ABBAABBA then a sestet (the older Italian shape). "
      "The easy way in is Shakespeare's: three quatrains that each push the idea one step "
      "further, then a couplet that turns it, so write the last two lines first.",
      # the sonnet as a set text, and an essay about one, are school questions; a sonnet about
      # something is the verse card's to write
      avoid=("essay", "analysis", "analyse", "analyze", "school", "homework", "exam",
             "revision", "class", "teacher", "shakespeare wrote", "18",
             "about", "for my", "for a", "for the", "for her", "for him", "for their"),
      bias=1))

# Two word-part terms that sat next to an answered one and got the hedge: synonym and homophone
# both had a card and prefix, suffix and antonym had none.
ENTRIES.append(entry("word-parts",
      (("prefix", "prefixes", "suffix", "suffixes", "antonym", "antonyms"),
       ("mean", "means", "what", "whats", "definition", "example", "examples", "explain",
        "difference")),
      "A prefix goes on the front of a word and a suffix on the end: un- in unhappy, -ness in "
      "happiness, and the base word (happy) is the root. An antonym is the opposite - hot and "
      "cold, early and late - which is the other half of what a synonym is, so if the word you "
      "want means the same, look for a synonym, and if it means the reverse, an antonym.",
      # a spelling question about a prefix, and a word that only passes by, keep their own cards
      avoid=("spell", "spelling", "spelt", "hyphen", "dashes", "prefix a call", "phone code",
             "dialling code", "numbers"),
      bias=1))

# A diary is a writing job with a lower bar than an essay, and "how do i write a diary" hedged
# while "how do i keep a journal" had its own answer.
ENTRIES.append(entry("write-a-diary",
      (("diary", "diaries", "diary entry", "dear diary"),
       ("how do i", "how to", "write", "writing", "start", "keep", "begin", "help")),
      "Write the date, then the one thing you would tell a friend about the day - what happened, "
      "and what you thought of it - in three or four lines and without tidying it up. Keep it "
      "where you will actually open it and write at a fixed time, because the habit is the hard "
      "part; a page of plain sentences beats a blank page waiting for a good day.",
      # a planner, an app and a school assignment are other questions
      avoid=("app", "apps", "planner", "calendar", "notebook", "buy", "gift", "present",
             "school", "assignment", "class", "teacher", "essay"),
      bias=1))


# A toast, and the summary of a book. The wedding speech card answers "speech" and "wedding";
# a toast is the shorter, looser job, and a book summary is not the blurb or the review.
# "write-a-toast" is the wording domain's card for the big speeches (a wedding, a best man, a
# retirement): three minutes, about 450 words, the opening line worked out. This one is the
# short glass raised at a table, from notes. They had the same id, and an id is the identity
# the answer module remembers between turns, so nothing that remembers an id could tell the
# two apart - and the advice differs. The id here is the card, not a new wording.
ENTRIES.append(entry("write-a-toast-few-words",
      (("toast", "toasts", "raise a glass", "say a few words", "short speech"),
       ("how do i", "how to", "write", "writing", "give", "make", "propose", "help")),
      "Two minutes is plenty: say who you are and why you are standing up, tell one story with a "
      "detail only you would know, then say the thing you actually want to say and sit down. "
      "Write the first and last line out word for word and let the middle be notes, because the "
      "room forgives a stumble and does not forgive a ramble.",
      # the wedding speech, a eulogy and a given speech are other cards
      avoid=("wedding", "bride", "groom", "best man", "eulogy", "funeral", "birthday",
             "retirement", "leaving", "how long is a speech", "450 words",
             # A toast handed to an animal is its dinner: "can i give my dog toast" and
             # "should i give my golden retriever toast" were both a speech card.
             ) + ANIMAL_NOUNS,
      bias=1))
ENTRIES.append(entry("book-summary",
      (("book summary", "summarise a book", "summarize a book", "summary of a book", "plot summary",
        "chapter summary", "summarise the book", "summarize the book"),
       ("how do i", "how to", "write", "writing", "make", "help", "notes")),
      "Go chapter by chapter before you write a line: one sentence per chapter on what changed, "
      "then join them into a paragraph that follows the argument or the plot rather than the "
      "order of the pages. Keep the ending in - a summary that hides it is a blurb - and put your "
      "own one-line judgement at the end, clearly marked as yours.",
      # the review, the blurb and an academic abstract are other jobs
      avoid=("review", "blurb", "back cover", "film", "movie", "episode", "abstract",
             "dissertation", "thesis", "paper", "essay", "school"),
      bias=1))


# The writing jobs whose own name nobody had a card for. Each line here was answered by a card
# that shares one word with it and answers something else: a "fight scene" was a row in the
# house, a "report for work" was asking the boss for a meeting, a "wedding reading" was a message
# in a card, and a "speech for school" was a wedding toast. A job that names its own thing gets a
# card of its own, keyed on that thing, and the card it borrowed stands down for the words that
# are not its own.
# A question somebody has to ask is not a sentence somebody has to write. "whats a good opening
# question" was answered with "start with a voice or a fact, not the weather": the interview row
# keys the whole phrase "opening question" and lost on bias to this card, which keys the bare word
# "opening" and needs one of "good"/"best"/"great" beside it - an ask word, not a writing one. The
# shape is what tells them apart: an opening *question* is asked of somebody, an opening line,
# sentence or chapter is written.
_AN_OPENING_QUESTION = re.compile(
    r"\b(?:opening|opener|starter|first|lead) questions?\b|\bquestion to open\b")
_AN_OPENING_IS_WRITTEN = re.compile(
    r"\b(?:book|books|story|stories|novel|chapter|essay|blog|post|article|draft|manuscript|"
    r"scripts?|write|writing|written|author|reader|readers)\b")


def _an_opening_is_written_not_asked(understood):
    """True unless the line asks for a question to ask: an interview question is not a first line."""
    reading = understood if isinstance(understood, dict) else {}
    text = str(reading.get("clean") or reading.get("text") or "").lower()
    if not _AN_OPENING_QUESTION.search(text):
        return True
    return bool(_AN_OPENING_IS_WRITTEN.search(text))


ENTRIES.append(entry("story-first-line",
      (("opening line", "opening lines", "first line", "first lines", "first sentence",
        "opening sentence", "hook", "hooks", "opening"),
       ("book", "story", "novel", "chapter", "reader", "readers", "good", "best",
        "great")),
      "Start with a voice or a fact, not the weather: \"My mother stole a car on her way to my "
      "christening\" and \"The rent was due on Friday and I had 40p\" both make a reader ask a "
      "question. One sentence, something happening or someone talking, and no throat-clearing "
      "before it. Write ten, throw eight away - the tenth is usually the one you keep.",
      ask=("what", "whats", "what's", "how", "good", "best", "any", "suggest", "give", "need"),
      avoid=("poem", "poems", "song", "lyrics", "rap", "speech", "essay", "email", "cover letter",
             "cv", "letter", "journal", "diary") + PERSONAL_NEWS,
      # The row keys the bare word "opening", so a question somebody has to ask reaches it as
      # well: see `_an_opening_is_written_not_asked`.
      guard=_an_opening_is_written_not_asked,
      bias=2))
ENTRIES.append(entry("describe-a-character",
      (("describe", "describing", "description", "describe a character", "character description",
        "character", "characters"),
       ("character", "characters", "person", "people", "book", "story", "novel",
        "dialogue")),
      "Give one thing they do and one thing they own before you describe their face: a woman who "
      "counts the stairs as she climbs them and keeps her bus tickets in a tin is a person, and "
      "\"tall, with brown hair\" is a form. Two details, one of them slightly odd, and let the "
      "reader do the rest; people remember what a character does far longer than how they look.",
      ask=("how", "what", "any", "should", "tips", "good"),
      avoid=("photo", "picture", "appearance", "haircut", "outfit", "dating profile", "cv",
             "personal statement", "job interview") + PERSONAL_NEWS,
      bias=1))
ENTRIES.append(entry("write-a-fight-scene",
      (("fight scene", "fight scenes", "action scene", "battle scene", "chase scene",
        "write a fight", "fighting scene"),
       ("scene", "scenes", "better", "describe", "good", "punchy", "fast")),
      "Keep the sentences short and the geography simple: who is where, what is in reach, and "
      "what each of them wants in the next ten seconds. Two or three blows that land badly, one "
      "thing that goes wrong - a foot in a puddle, a hand that will not close - and a cost at the "
      "end, because a fight nobody loses anything in reads like a dance.",
      ask=("how", "what", "any", "should", "help", "tips"),
      avoid=("my partner", "my husband", "my wife", "my boyfriend", "my girlfriend", "argument",
             "argue", "arguing", "row with", "he hit", "she hit", "hit me", "police", "abuse") + PERSONAL_NEWS,
      bias=1))
# A count of minutes is a length of time, and the word after it says which question it is: "the
# meeting is only ten minutes what can i eat" was answered with how to write up the minutes of a
# meeting (quality, ten-minute dinners). The avoid list could only hold the counts somebody
# thought to write ("10 minutes", "five minutes"), so every count is read here instead: a number,
# in digits or in words, sitting in front of "minutes" or "mins". The count stands the row down
# only when it is the only minute word in the line - see `_minutes_are_a_length_of_time`.
A_COUNTED_MINUTE = re.compile(
    r"\b(?:\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|"
    r"seventy|eighty|ninety|hundred|couple|few|half)"
    r"(?:\s+(?:of|more|whole|short|quick|extra|good))?\s+(?:minutes|minute|mins|min)\b")


# Every "minutes" in the line, counted or not, so the two can be compared.
EVERY_MINUTE = re.compile(r"\b(?:minutes|minute|mins|min)\b")


def _minutes_are_a_length_of_time(understood):
    """True when the line has a "minutes" that is not a count of them, so the row keeps it.

    A count is not enough to stand the row down on its own: "the meeting ran 90 minutes, how do
    i write up the minutes" counts minutes and then asks for the minutes of the meeting, and
    standing down there lost the card to a count that is not the subject. The question the
    guard asks is whether every minute word in the line is a count - only then is the line
    about a length of time and not about the record of a meeting.
    """
    text = " ".join(str((understood or {}).get("clean") or "").lower().split())
    return len(EVERY_MINUTE.findall(text)) > len(A_COUNTED_MINUTE.findall(text))


ENTRIES.append(entry("meeting-minutes",
      (("minutes", "minute taking", "take minutes", "taking minutes", "meeting notes",
        "note taking"),
       ("meeting", "meetings", "notes", "work", "actions", "decisions")),
      "Three parts and nothing else: what was decided, who is doing what by when, and what was "
      "left open. Write the decisions as they happen rather than from memory afterwards, put a "
      "name and a date against every action, and send them out the same day - minutes nobody "
      "reads by Friday are a diary.",
      ask=("how", "what", "should", "write", "take", "any"),
      avoid=("minutes walk", "minutes drive", "in minutes", "for 10", "for 20") + PERSONAL_NEWS,
      guard=_minutes_are_a_length_of_time,
      bias=1))
ENTRIES.append(entry("write-a-work-report",
      (("report", "reports", "write-up", "write up", "writeup"),
       ("work", "office", "weekly", "monthly", "quarterly", "progress", "numbers",
        "structure")),
      "Answer the question the report exists for in the first two lines, then the evidence: what "
      "you did, what it showed, what you want to happen next. Short sections with headings, one "
      "number or example per claim, and a line at the end saying what you need from the reader. "
      "Anybody who reads only the first paragraph should still know the answer.",
      ask=("how", "what", "should", "write", "any", "help"),
      avoid=("school report", "medical report", "police report", "accident report",
             "annual report", "tax return", "self assessment", "sick note", "safeguarding",
             "raise it", "speak to my boss", "talk to my boss") + PERSONAL_NEWS,
      bias=1))
ENTRIES.append(entry("wedding-reading",
      (("reading", "readings", "passage", "passages", "what to read", "poem to read",
        "something to read"),
       ("wedding", "ceremony", "church", "registry office", "read out", "choose")),
      "Pick by length and tone rather than by fame: 60 to 90 seconds, one idea, and nothing that "
      "makes the couple laugh at each other. A poem works if it is plain and short (Auden's "
      "\"Funeral Blues\" is a funeral poem - be careful), and a passage from a book the two of "
      "them love beats a sonnet nobody understands. Read it aloud twice before the day, and tell "
      "the registrar what you are reading.",
      ask=("what", "which", "how", "any", "best", "good", "should", "suggest"),
      avoid=("card", "cards", "message", "note", "wishes", "vows", "write my own", "tarot",
             "reading a book", "reading list", "reading to my") + PERSONAL_NEWS,
      bias=1))
ENTRIES.append(entry("school-speech",
      (("speech", "presentation", "assembly", "speak in assembly"),
       ("school", "class", "gcse", "students", "year 11", "leavers", "leaving assembly",
        "head boy", "head girl", "teacher", "teachers", "assembly")),
      "Open with a story about one day at that school, not with a thank-you list, and keep the "
      "whole thing to three minutes: the story, what it taught you, then the one sentence you "
      "want people to remember. Say it out loud standing up four times before the day, and put "
      "the last line on a card in your hand - a rehearsed ending is what makes a speech land.",
      ask=("how", "what", "should", "write", "any", "help"),
      avoid=("wedding", "bride", "groom", "best man", "toast", "eulogy", "funeral", "birthday",
             "retirement", "leaving do", "speech therapy", "speech delay", "speech and language") + PERSONAL_NEWS,
      bias=1))


# A caption under a photo, which people ask for far more often than for a blurb: "how do i write
# a caption" and "what should i caption my photo" were both a shrug, and "instagram" was reaching
# the cancelled-subscription card. The job is small, so the card is short: the thing in the
# picture, one detail the picture cannot show, then stop.
#
# The example used to be a sourdough loaf whatever the person had photographed, so "a caption
# for a photo of my dog in the snow" was told "Third attempt at the sourdough - this one
# actually rose". A caption is about the thing in the picture, so the subject is read out of
# the line and the example is built round it; the rule is the same either way.
_PET_PHOTO = ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "rabbit", "bunny",
              "horse", "pony", "parrot", "hamster", "guinea pig", "tortoise", "pets", "pet")
_FOOD_PHOTO = ("cake", "cakes", "bread", "loaf", "dinner", "lunch", "breakfast", "soup",
               "pie", "biscuits", "cookies", "curry", "roast", "pancakes", "sourdough",
               "pizza", "pasta", "barbecue", "bbq", "coffee", "chocolate")
_PLACE_PHOTO = ("sea", "beach", "mountain", "mountains", "hill", "hills", "sunset",
                "sunrise", "sky", "lake", "river", "city", "street", "forest", "snow",
                "holiday", "view", "garden")
# One detail per kind of picture, chosen so it fits any subject of that kind: what the picture
# cannot show is the half of the caption that makes it worth reading.
_PHOTO_DETAIL = ((
    _PET_PHOTO, "and that look it gives you just before it decides not to listen"),
    (_FOOD_PHOTO, "and it did not last the afternoon"),
    (_PLACE_PHOTO, "and nobody else was awake yet"),
)
_PHOTO_DETAIL_PEOPLE = "and the hour before anybody started posing"
_PHOTO_DETAIL_ANY = "and the part of the day nobody photographs"
_PEOPLE_PHOTO = ("me", "us", "my mum", "my mom", "my dad", "my sister", "my brother",
                 "my friend", "my friends", "family", "the kids", "my son", "my daughter",
                 "my wife", "my husband", "my partner", "my nan", "my grandma", "my grandad")


def _the_photo_of(clean):
    """What is in the picture, when the line says: "a photo of my dog in the snow"."""
    found = re.search(r"(?:photo|picture|pic|snap|shot|image)\s+(?:of|showing)\s+(.+)$", clean)
    if not found:
        return ""
    words = re.findall(r"[a-z']+", found.group(1))
    kept = []
    for word in words:
        if word in ("and", "but", "that", "which", "please", "for", "from", "on", "at"):
            break
        kept.append(word)
    while kept and kept[-1] in ("i", "me", "my", "the", "a", "an", "just", "that"):
        kept.pop()
    if not kept or len(kept) > 6:
        return ""
    subject = " ".join(kept)
    if all(word in ("my", "the", "a", "an", "our", "some") for word in kept):
        return ""
    return subject


def _the_caption_detail(subject):
    """The half of the caption the picture cannot show, chosen for the kind of picture."""
    said = " " + subject + " "
    if any(" " + word + " " in said for word in _PEOPLE_PHOTO) or re.search(
            r"\b(?:me|us|we)\b", subject):
        return _PHOTO_DETAIL_PEOPLE
    for words, detail in _PHOTO_DETAIL:
        if any(" " + word + " " in said for word in words):
            return detail
    return _PHOTO_DETAIL_ANY


def _a_caption(memory, understood):
    """The one-line caption rule, with an example built from the picture the person named."""
    clean = str((understood or {}).get("clean") or "").lower()
    subject = _the_photo_of(clean)
    if not subject:
        return ("Say what is in the picture and one thing the picture cannot show, then stop: "
                "\"Third attempt at the sourdough - this one actually rose.\" One line beats "
                "three, a joke only works if it is about the picture, and leave the hashtags to a "
                "line of their own.")
    said = subject[0].upper() + subject[1:]
    # "the cake i made" reads as a typo in a caption, so the standalone i is written as I
    typed = re.sub(r"\bi\b", "I", said)
    example = "%s, %s" % (typed, _the_caption_detail(subject))
    return ("Say what is in the picture and one thing the picture cannot show, then stop: \"%s.\" "
            "One line beats three, a joke only works if it is about the picture, and leave the "
            "hashtags to a line of their own." % example)


ENTRIES.append(entry("write-a-caption",
      (("caption", "captions", "caption my", "write a caption", "insta caption",
        "instagram caption", "photo caption", "picture caption"),
       ("how do i", "how to", "write", "writing", "what", "whats", "should i", "help", "good",
        "photo", "picture", "post", "instagram", "insta", "for")),
      _a_caption,
      # a subtitle and a closed caption are other jobs, and the app itself is a tech question
      avoid=("subtitle", "subtitles", "closed captions", "tv", "television", "film", "movie",
             "youtube", "netflix", "cancel", "subscription", "delete my account", "edit a photo",
             "photo editor", "how do i post", "instagram account", "hacked"),
      bias=1))


# --- a kind thing to say ---------------------------------------------------------------
# "say something nice about my cat", "a compliment for my wife" and "a compliment i can pay a
# stranger" were answered with "Thanks for telling me - I'm here if you want to dig into any of
# that", which is not an answer to the question at all: nothing owned the word, so the
# reflective fallback took the line. Praise has a subject, so the subject is read out of the
# line and the answer changes with it: an animal, a person you know, a stranger.
_KIND_ASKS = ("say something nice", "say something nice about", "nice about my",
              "something nice about", "compliment about my", "compliment for my",
              "something nice to say", "a nice thing to say",
              "nice thing to say", "kind thing to say", "something kind to say",
              "a compliment", "some compliments", "compliments for", "compliment for",
              "compliment about", "compliment to", "pay a compliment", "give a compliment",
              "nice things to say", "what should i say to", "something good to say")
_KIND_SUBJECTS = ("about", "for", "to", "on")
_ANIMAL_KIND = ("cat", "cats", "kitten", "dog", "dogs", "puppy", "pup", "rabbit", "bunny",
                "hamster", "horse", "pony", "parrot", "bird", "tortoise", "pet", "pets",
                "guinea pig", "ferret", "donkey", "goat", "snake", "lizard", "fish")
_STRANGER_KIND = ("stranger", "strangers", "someone i don't know", "someone i dont know",
                  "somebody i don't know", "a stranger", "people i don't know", "new person",
                  "someone new", "somebody new", "a customer", "a colleague i just met")
_BAKE_KIND = ("cake", "bake", "baking", "bread", "sourdough", "loaf", "pie", "biscuits",
              "cookies", "dinner", "cooking", "meal", "roast", "jam", "curry", "casserole",
              "barbecue", "bbq", "pizza", "brownies")
_LOOKS_KIND = ("haircut", "hair", "beard", "outfit", "dress", "coat", "glasses", "quilt",
               "jumper", "nails")
_PLACE_KIND = ("garden", "kitchen", "room", "shed", "allotment", "flowers", "plant", "plants",
               "house", "car", "flat", "bathroom", "painting", "drawing", "kitchen floor")
_PEOPLE_KIND = ("wife", "husband", "partner", "girlfriend", "boyfriend", "mum", "mom",
                "mother", "dad", "father", "son", "daughter", "child", "kid", "sister",
                "brother", "friend", "mate", "colleague", "coworker", "boss", "neighbour",
                "neighbor", "teacher", "grandma", "grandmother", "grandad", "grandfather",
                "nan", "aunt", "uncle", "cousin", "person", "someone", "somebody", "man",
                "woman", "carer", "nurse", "gp", "doctor")

# The line for an animal is about the animal, for a person about what the person does, and for
# a stranger about something they chose. One sentence each: the compliment, then why it lands.
_A_KIND_WORD = {
    "animal": ("Go on the animal and not the owner: \"He doesn't just ignore you, he audibly "
               "ignores you.\" One true thing you have watched it do beats the word cute every "
               "time, because it proves you were paying attention."),
    "person": ("Name the thing they do that nobody remarks on and say it straight: \"You're the "
               "one who keeps this group actually going.\" The specific thing is the compliment; "
               "\"you're great\" is a placeholder and they can tell."),
    "stranger": ("Pick something they chose rather than something they were born with - the "
                 "coat, the dog, the way they handled the queue - and say it in five words as you "
                 "go: \"That coat is a very good coat.\" No follow-up needed, so it does not turn "
                 "into a conversation they did not ask for."),
    "bake": ("Praise the thing they made rather than the person making it: \"That crust has a "
             "proper crackle to it.\" They know how much work went into it, so the detail is what "
             "lands; \"it's lovely\" is what people say when they did not look."),
    "looks": ("Praise the detail you can see, not the thing itself: \"That cut makes your jaw "
              "look sharp,\" not \"nice haircut.\" Say it once, plainly, and let it stand - the "
              "detail is the proof you looked."),
    "place": ("Praise the work you can see rather than the whole thing: \"That border is doing "
              "a lot of quiet work.\" The one detail you noticed is the compliment; \"it looks "
              "lovely\" is a placeholder and they can tell."),
    "someone": ("Say the one thing you actually noticed and stop: \"You always remember how "
                "everyone takes their tea.\" Praise that names a thing they did is a compliment; "
                "praise with no subject in it is noise."),
}


def _who_the_kind_word_is_for(clean):
    """Who the line is about, from the words after about/for/to, or the words anywhere in it."""
    after = re.search(r"\b(?:about|for|to)\s+(.+)$", clean)
    said = " " + (after.group(1) if after else clean) + " "
    whole = " " + clean + " "
    for place, words in (("stranger", _STRANGER_KIND), ("animal", _ANIMAL_KIND),
                         ("person", _PEOPLE_KIND), ("bake", _BAKE_KIND),
                         ("looks", _LOOKS_KIND), ("place", _PLACE_KIND)):
        if any(" " + word + " " in said for word in words):
            return place
        if any(" " + word + " " in whole for word in words):
            return place
    return "someone"


def _a_kind_word(memory, understood):
    """A compliment the person can copy, chosen for what the line says it is about."""
    clean = str((understood or {}).get("clean") or "").lower()
    return _A_KIND_WORD[_who_the_kind_word_is_for(clean)]


# "What should i say to my landlord about the rent rise" is a conversation to have, not praise,
# and the same shape is praise only when the thing after "about" is something to be pleased
# about: "what should i say to my wife about her new haircut" is a compliment, "about the noise",
# "about the workload", "about the money" and "about his behaviour" are not. Those lines have
# answers of their own (neighbour-noise, boss-too-much, money-and-partner, rent-rise), and this
# row was the compliment script for all of them because its key holds "what should i say to".
# The list is the things people raise with somebody - money, noise, workload, mess, behaviour,
# a deadline - and not a list of things worth praising. It was the other way round first, and an
# allow-list of praise loses every line nobody thought of: "say something nice about her new job"
# is exactly what this row is for, and it fell to a short "Nice one" while the list had no "job"
# in it. A complaint after "about" is the short, stable set, and the row stands down for it.
_A_MATTER_TO_RAISE = (
    "rent", "rents", "rent rise", "rent increase", "money", "pay", "wages", "overtime",
    "hours", "shifts", "rota", "workload", "noise", "noisy", "mess", "messy", "rubbish",
    "bins", "bin", "damp", "mould", "mold", "repairs", "repair", "deposit", "bill", "bills",
    "arrears", "debt", "debts", "behaviour", "behavior", "attitude", "manners", "deadline",
    "deadlines", "lateness", "chores", "boundaries", "smoking", "drinking")


def _the_matter_is_worth_praise(understood):
    """True unless the line names a thing to raise with somebody, rather than a thing to praise."""
    clean = str((understood or {}).get("clean") or "").lower()
    after = re.search(r"\babout\s+(.+)$", clean)
    if not after:
        return True
    matter = " " + " ".join(after.group(1).split()) + " "
    for word in _A_MATTER_TO_RAISE:
        if " " + word + " " in matter:
            return False
    return True


ENTRIES.append(entry("a-kind-word",
      (_KIND_ASKS,
       _KIND_SUBJECTS + ("say", "something", "nice", "kind", "compliment", "compliments",
                        "what", "should", "give", "me", "can", "i", "you")),
      _a_kind_word,
      # a spelling question about complement/compliment, a complement on a paint card and praise
      # for something somebody did well are all other answers
      avoid=("complement", "complements", "complementary", "complimentary", "paint", "colour",
             "color", "scheme", "spell", "spelling", "spelt", "mean", "means", "meaning",
             "difference between", "well done", "appraisal", "performance review", "feedback",
             "notice period", "resign", "vaccine", "insurance", "complimentary breakfast"),
      # the thing after "about" decides: a quality is praised, a matter is raised with whoever
      # it concerns, and those lines have their own answers
      guard=_the_matter_is_worth_praise,
      bias=1))


# The jobs people write every week, not once in a lifetime: a blog post, a review of something
# they bought, and getting less frightened in front of a room. All three were a shrug on a
# "how do i" line, which is the wording people use for them.
ENTRIES.append(entry("write-a-blog-post",
      (("blog post", "blog", "blogging", "article", "post about", "write a post", "blog page"),
       ("how do i", "how to", "write", "writing", "start", "starting", "good", "first", "help",
        "what should", "structure", "long")),
      "Open with the thing you found out, not with the background: \"Cheap ovens lie about their "
      "temperature\" gets read, \"Many people own ovens\" does not. One idea per post, 600 to 900 "
      "words, subheadings every few paragraphs, and end by telling the reader what to do next.",
      avoid=("blogger", "blog template", "wordpress", "squarespace", "make money", "monetise",
             "get traffic", "seo", "domain name", "hosting"),
      bias=1))

ENTRIES.append(entry("about-me-page",
      # A bio is written for a page: the bare "about me" and "about us" forms were read as an
      # ask for one whenever a line said "worrying about me" or "tell me about us", so the row
      # now names the page it is for.
      (("about me page", "about me section", "about me blurb", "write an about me",
        "writing an about me", "my about me", "about page", "about us page", "about us section",
        "about us blurb", "write an about us", "our about us", "bio", "bios", "my bio",
        "author bio", "profile bio", "biography for", "short bio", "one line bio"),
       ("write", "writing", "how do i", "what should", "what do i put", "put in", "include",
        "start", "say", "good", "better", "help")),
      "Five lines in the first person: what you do, who you do it for, one proof - a project, a "
      "number, a place you worked - and how to reach you. Cut the adjectives at the top, because "
      "\"passionate about stories\" tells a reader nothing, and write the sentence you would say "
      "if someone asked at a party what you do.",
      ask=("how", "what", "should", "which", "any", "can"),
      # a bio for a dating app, a CV and a company page are other questions, and a name is
      # remembered rather than written
      avoid=("tinder", "dating", "hinge", "bumble", "cv", "resume", "cover letter",
             "instagram", "tiktok", "twitter", "linkedin headline", "job application",
             "remember", "remembering", "memorise", "memorize"),
      bias=1))

ENTRIES.append(entry("write-a-product-review",
      (("product review", "amazon review", "review a product", "review on amazon", "leave a review",
        "write a review of", "one star review"),
       ("how do i", "how to", "write", "writing", "good", "help", "what should", "bad", "negative",
        "complaint")),
      "Say what you bought, how long you have used it and what it did well, then the one thing that "
      "went wrong, with a fact: \"the handle bent on the fourth use\". Two lines of that beats a "
      "star rating, and a fair review is far harder for a shop to dismiss than an angry one. Put it "
      "where people look and the business will see it - the order page for an online shop, Google "
      "Maps for a cafe or restaurant, TripAdvisor for a hotel - and keep the order number and any "
      "photos.",
      avoid=("book review", "book", "novel", "film review", "movie", "restaurant review",
             "how do i get", "followers", "review my cv"),
      bias=1))

ENTRIES.append(entry("public-speaking-nerves",
      (("public speaking", "presentation", "presenting", "speak in front of", "speaking in public",
        "stage fright", "talking in front of people", "speak to a room", "webinar", "viva"),
       ("better", "improve", "nervous", "nerves", "confident", "confidence", "afraid", "scared",
        "how do i", "how to", "practice", "practise", "help", "calm")),
      "Rehearse the first sixty seconds out loud until you could say it half asleep, because that is "
      "the only part your nerves will attack. Then slow down and pause at the ends of sentences "
      "rather than filling the silence - a room reads a pause as confidence, and it gives you time "
      "to breathe.",
      # "present" is two words too: a speech, and a thing you buy. The key matches the front of
      # "presentation", so "how do i split the cost of a present" was answered with the room and
      # the first sixty seconds. A gift word in the line is the other present.
      avoid=("wedding", "best man", "bridesmaid", "eulogy", "funeral", "toast", "write", "draft",
             "opening line", "joke",
             "a present", "the present", "presents for", "present for", "a gift", "the gift",
             "gifts", "cost of a present", "cost of the present", "split the cost of",
             "what to give", "what to buy", "what to get", "wrap", "wrapping"),
      bias=1))

# --- the mark someone can see but cannot name -------------------------------------------
# "what is this mark called" and "what is that wavy line called" name no mark at all, so no
# table keyed on names can reach them: the answer has to start from how the mark looks or
# which key it is on. The questions that do name a thing (a sign of a stroke, a washing label)
# are other modules' and stay with them.
_MARK_WORDS = ("mark", "marks", "symbol", "symbols", "sign", "signs", "character", "characters",
               "line", "lines", "squiggle", "squiggles", "punctuation", "key", "keys",
               "keyboard")
_MARK_ASK = ("called", "name", "do you call", "which key", "what key", "what is this",
             "what is that", "whats this", "whats that", "what does this", "what does that",
             "what is the #", "what is the *", "what is the @", "what is the ~", "what is the _",
             "what is the |")
# what the person can see, in the words they would use for it
_MARK_BY_LOOK = (
    (("wavy", "wave", "squiggle", "squiggly", "tilde", "squiggles"),
     "That is a tilde, ~. It means 'about' (~20 people came), and on most keyboards it is Shift "
     "and the hash key."),
    (("low line", "low dash", "underline", "under the letter", "under a letter", "between words"),
     "That is an underscore, _. It joins words in file names and usernames (my_notes.txt); a "
     "hyphen is the shorter mark at half height."),
    (("upright", "vertical", "tall line", "straight line"),
     "That is a pipe, |, also called the vertical bar. It separates options in a computer "
     "command; in writing a slash does the job better."),
    (("star", "little star", "star shaped"),
     "That is an asterisk, *. It marks a footnote, and on a phone keyboard it hides behind the "
     "?123 key."),
    (("wedge", "little hat", "roof", "pointing up", "arrow head"),
     "That is a caret, ^. It marks where a word is to be slipped in, and in maths it means to the "
     "power of - 2^3 is eight."),
    (("backwards", "other way", "wrong way"),
     "The one leaning the other way is a backslash, \\. It separates folders in a Windows file path "
     "like C:\\Users\\me, and it almost never belongs in writing."),
    (("over the 2", "above the 2", "at sign", "a with a circle"),
     "That is the at sign, @ - Shift and 2 on a UK keyboard, and it is in every email address."),
    (("over the 3", "above the 3", "hash", "pound", "number sign"),
     "That is the hash, # - Shift and 3 on a UK keyboard. On a phone it starts a hashtag, and in "
     "the US it labels a number."),
    (("dot", "dots", "three dots", "full stop", "period"),
     "Three dots in a row are an ellipsis (...), and it means something has been left out or the "
     "thought trails off. A single dot is a full stop."),
    (("squarish", "square", "box"), "Square brackets are [ ], and they hold your own words inside a "
                                    "quotation or a gap in a transcript."),
    (("curly", "squiggly brackets", "brace", "braces"),
     "Curly brackets are { }, and they group things in maths and in code. Round brackets ( ) take "
     "an aside the sentence could do without."),
    (("sideways v", "pointy", "arrow brackets"),
     "Angle brackets are < >. They mark a tag in code and stand in for a word to fill in later, "
     "as in <your name>."),
)


def _mark_unnamed(memory, understood):
    """The mark from the way it looks or the key it sits on, else how to describe it."""
    text = str((understood or {}).get("clean") or "").lower()
    for looks, reply in _MARK_BY_LOOK:
        # a look can be two words ("low line", "over the 2"), which the word matcher cannot see
        if _mentions(text, looks) or any(" " in look and look in text for look in looks):
            return reply
    # the mark itself may be pasted into the line
    for sign, name in (("#", "hashtag"), ("@", "at sign"), ("|", "pipe"), ("~", "tilde"),
                       ("*", "asterisk"), ("^", "caret"), ("_", "underscore")):
        if sign in text:
            return GRAMMAR_TERMS[name]
    for name, reply in GRAMMAR_TERMS.items():
        if name in text:
            return reply
    return ("Tell me which key it is on and I will name it: the tall line on the left of the "
            "keyboard is the pipe (|), the mark over 2 is the at sign (@), over 3 the hash (#), "
            "and the wavy one on the left is a tilde (~). If you can paste it into a line, I can "
            "read it too.")


ENTRIES.append(entry("mark-unnamed", (_MARK_WORDS, _MARK_ASK), _mark_unnamed,
                     # a washing label, a symptom and a road sign are that thing's question
                     avoid=("cancer", "mole", "moles", "skin", "symptom", "symptoms", "stroke",
                            "infection", "rash", "label", "labels", "care label", "washing",
                            "laundry", "tub", "instruction", "instructions", "clothes", "tag",
                            "tags", "road", "zodiac", "star sign", "birth", "period pain",
                            "periods",
                            # a mark on the body is the body's question, not a key to name
                            "arm", "arms", "leg", "legs", "back", "face", "bruise", "bruises",
                            "spot", "spots", "lump", "lumps", "mark on my", "marks on my",
                            "birthmark", "freckle", "freckles", "scar", "scars",
                            # "is forgetting names a sign of dementia" is a question about the
                            # illness: "sign" is this row's word for a mark to name, and it asked
                            # which key the mark is on. A memory sign is the memory card's.
                            "dementia", "alzheimers", "alzheimer's", "memory", "memories",
                            "forget", "forgets", "forgetting", "forgetful", "forgot",
                            "remember", "remembering"),
                     ask=_MARK_ASK))
