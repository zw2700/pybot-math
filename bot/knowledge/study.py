"""School and study: revising, remembering, essays, notes, and learning a language.

Everything here is data on the merged `lookup.entry` contract: one entry per thing people
ask about, keyed by the words that identify it (revising, an essay, a words-in-Spanish
question) with a reply phrased the way a helpful older student would say it. The matcher
in lookup.py picks the entry; bot/modules/answers.py turns it into a reply.

Two general mechanisms live here:
- START / ONE THING style advice is always concrete (do this today, for ten minutes),
  because "make a timetable" on its own is what the person has already failed at.
- PHRASES is a small table of everyday phrases in four languages, read by a callable
  reply, so one entry answers every "how do you say X in Y" question instead of one
  entry per phrase.
"""
import re
import unicodedata

from . import quantity
from .lookup import A_WHAT_TO_WEAR, entry
from ..understanding.normalize import BASE as ENGLISH_WORDS
from .wording import NERVES_BODY, nerves_opening

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("school-and-study", "language-and-writing")


# --- fractions -------------------------------------------------------------
# One fractions answer per operation asked, each carrying all four: "how do i divide fractions"
# used to open with "Multiplying is the easy one", which reads as a reply to another question.
# The same person asks the next operation straight after, so the other three stay in the answer.
FRACTIONS_DIVIDE = (
    "Flip the second fraction upside down and multiply: 2/3 divided by 3/5 is 2/3 x 5/3 = 10/9. "
    "Multiplying is top times top and bottom times bottom (2/3 x 3/5 = 6/15, which "
    "simplifies to 2/5), and adding or subtracting needs the same bottom number first, so "
    "1/3 + 1/4 = 4/12 + 3/12 = 7/12.")
FRACTIONS_MULTIPLY = (
    "Top times top, bottom times bottom: 2/3 x 3/5 = 6/15, which simplifies to 2/5. Dividing is "
    "the same trick with the second one flipped over, so 2/3 divided by 3/5 is 2/3 x 5/3 = 10/9. "
    "Adding and subtracting need the same bottom number first: 1/3 + 1/4 = 4/12 + 3/12 = 7/12.")
FRACTIONS_ADD = (
    "Get the same bottom number first: 1/3 + 1/4 becomes 4/12 + 3/12 = 7/12, and subtracting "
    "works the same way. Multiplying is top times top and bottom times bottom (2/3 x 3/5 = 6/15, "
    "which simplifies to 2/5); dividing flips the second one over and multiplies, so 2/3 divided "
    "by 3/5 is 2/3 x 5/3 = 10/9.")
FRACTIONS_SIMPLIFY = (
    "Divide the top and the bottom by the same number until nothing goes into both: 6/15 divide "
    "by 3 and you get 2/5. For sums, multiply top times top and bottom times bottom (2/3 x 3/5 = "
    "6/15, then simplify), divide by flipping the second fraction over (2/3 divided by 3/5 is "
    "2/3 x 5/3 = 10/9), and add or subtract once the bottom numbers match (1/3 + 1/4 = 7/12).")
FRACTIONS_FIRST = (
    (("divide", "dividing", "divided"), FRACTIONS_DIVIDE),
    (("multiply", "multiplying", "multiplied", "times"), FRACTIONS_MULTIPLY),
    (("add", "adding", "plus", "subtract", "subtracting", "subtracted", "minus"),
     FRACTIONS_ADD),
    (("simplify", "simplifying", "cancel", "lowest"), FRACTIONS_SIMPLIFY),
)


# "when should i start past papers" punted while "when do i start past papers" answered: the row
# keys the paper words and then a way of working them, and `when`/`should`/`start` were not in that
# half. The same person asking when wants the date first, not the marking, so the reply leads with
# the timing when the line asks for one and keeps the old text otherwise.
_PAST_PAPERS = (
    "Do them under timed conditions, then mark yourself against the real mark scheme - "
    "the marking is where most of the learning is. Keep a list of the question types you "
    "lose marks on and redo only those next time. If you are short of time, do the paper "
    "in your head and write full answers only for the weak sections.")
_PAST_PAPERS_WHEN = (
    "Start about six to eight weeks before the exam, one paper a week, then two a week in the "
    "last month, so the early marks still leave you time to fix what they show. Do each under "
    "timed conditions and mark it against the real mark scheme, and redo only the question "
    "types you lose marks on.")
_PAST_PAPERS_ASK_WHEN = frozenset((
    "when", "should", "start", "starting", "begin", "leave", "leaving", "left", "soon", "late",
    "early", "before", "how long", "how many weeks", "how many months"))


def _past_papers_reply(memory, reading):
    """The past-papers answer, opening with the timing when the line asks when to start."""
    line = str((reading or {}).get("text") or (reading or {}).get("norm") or "").lower()
    words = set(re.findall(r"[a-z']+", line))
    if any(word in words for word in _PAST_PAPERS_ASK_WHEN) and (
            "when" in words or "should" in words or "start" in words or "begin" in words
            or "how long" in line or "how many" in line or "soon" in words):
        return _PAST_PAPERS_WHEN
    return _PAST_PAPERS


def _fractions_reply(memory, reading):
    """The fractions answer, opening with the operation the line asks about."""
    line = str((reading or {}).get("text") or (reading or {}).get("norm") or "").lower()
    words = set(re.findall(r"[a-z']+", line))
    for asking, said in FRACTIONS_FIRST:
        if any(word in words for word in asking):
            return said
    return FRACTIONS_MULTIPLY



# --- how do you say ... ---------------------------------------------------
# concept -> {language: (phrase, pronunciation hint)}
PHRASES = {
    "toilet": {
        "portuguese": ("Onde fica a casa de banho?", "ON-dy FEE-ka a KA-za dy BAN-yo"),
        "greek": ("Poú eínai i toualéta? (πού είναι η τουαλέτα)", "poo EE-neh ee too-a-LEH-ta"),
        "turkish": ("Tuvalet nerede?", "too-va-LET NEH-reh-deh"),
        "welsh": ("Ble mae’r toiled?", "bleh mire TOY-led"),
        "japanese": ("Toire wa doko desu ka (トイレはどこですか)", "TOY-reh wah DOH-koh dess kah"),
        "chinese": ("Xǐshǒujiān zài nǎr? (洗手间在哪儿)", "shee-show-jyen dzai nar"),
        "dutch": ("Waar is het toilet?", "vaar is hut twa-LET"),
        "spanish": ("¿Dónde está el baño?", "DON-day es-TA el BAN-yo"),
        "french": ("Où sont les toilettes ?", "oo son lay twa-LET"),
        "italian": ("Dov'è il bagno?", "do-VEH eel BAN-yo"),
        "german": ("Wo ist die Toilette?", "vo ist dee toy-LET-tuh"),
        "welsh": ("Ble mae'r toiled?", "blay my-re TOY-led"),
        "irish": ("Cá bhfuil an leithreas?", "kaw will an LEH-rass"),
    },
    "thank you": {
        "portuguese": ("Obrigado (a woman says obrigada)", "oh-bree-GAH-doo"),
        "greek": ("Efcharistó (ευχαριστώ)", "ef-kha-ree-STOH"),
        "turkish": ("Teşekkürler", "teh-shek-kewr-LER"),
        "welsh": ("Diolch", "DEE-olch"),
        "japanese": ("Arigatou (ありがとう)", "a-ree-GA-toh"),
        "chinese": ("Xièxie (谢谢)", "shyeh-shyeh"),
        "dutch": ("Dank je wel", "dank yuh vel"),
        "spanish": ("Gracias", "GRA-thee-as"),
        "french": ("Merci", "mair-SEE"),
        "italian": ("Grazie", "GRAT-zee-eh"),
        "german": ("Danke", "DAN-kuh"),
        "welsh": ("Diolch", "DEE-olkh"),
        "irish": ("Go raibh maith agat", "guh rev MAH a-gut"),
        "gaelic": ("Tapadh leat", "TA-pah lat"),
    },
    "please": {
        "portuguese": ("Por favor", "por fa-VOR"),
        "greek": ("Parakaló (παρακαλώ)", "pa-ra-ka-LOH"),
        "turkish": ("Lütfen", "LEWT-fen"),
        "welsh": ("Os gwelwch yn dda", "oss gwel-ooch un thah"),
        "japanese": ("Onegaishimasu (お願いします)", "o-neh-GUY-shee-mas"),
        "chinese": ("Qǐng (请)", "ching"),
        "dutch": ("Alstublieft", "als-too-BLEEFT"),
        "spanish": ("Por favor", "por fa-VOR"),
        "french": ("S'il vous plaît", "seel voo PLEH"),
        "italian": ("Per favore", "per fa-VO-reh"),
        "german": ("Bitte", "BIT-tuh"),
        "welsh": ("Os gwelwch yn dda", "os GWEL-ookh un thah"),
        "irish": ("Le do thoil", "leh duh HULL"),
        "gaelic": ("Mas e do thoil e", "mas eh daw HOLL eh"),
    },
    "hello": {
        "portuguese": ("Olá", "oh-LAH"),
        "greek": ("Kaliméra (καλημέρα)", "ka-lee-MEH-ra"),
        "turkish": ("Merhaba", "mer-ha-BAH"),
        "welsh": ("Helo (Bore da in the morning)", "HEH-loh"),
        "japanese": ("Konnichiwa (こんにちは)", "kon-nee-CHEE-wah"),
        "chinese": ("Nǐ hǎo (你好)", "nee HOW"),
        "dutch": ("Hallo", "HAL-oh"),
        "spanish": ("Hola", "OH-la"),
        "french": ("Bonjour", "bon-ZHOOR"),
        "italian": ("Ciao", "chow"),
        "german": ("Hallo", "HAL-oh"),
        "welsh": ("Helo", "HEH-lo"),
        "irish": ("Dia dhuit", "DEE-a gwit"),
        "gaelic": ("Halò", "ha-LAW"),
    },
    "goodbye": {
        "portuguese": ("Adeus", "a-DEHS"),
        "greek": ("Antío (αντίο)", "an-DEE-oh"),
        "turkish": ("Hoşça kalın", "hosh-cha ka-LUN"),
        "welsh": ("Hwyl fawr", "hooil vowr"),
        "japanese": ("Sayounara (さようなら)", "sa-YOH-na-ra"),
        "chinese": ("Zàijiàn (再见)", "dzai-jyen"),
        "dutch": ("Tot ziens", "tot zeens"),
        "spanish": ("Adiós", "a-DYOS"),
        "french": ("Au revoir", "oh ruh-VWAR"),
        "italian": ("Arrivederci", "a-ree-veh-DAIR-chee"),
        "german": ("Auf Wiedersehen", "owf VEE-der-zayn"),
        "welsh": ("Hwyl fawr", "hooil vower"),
        "irish": ("Slán", "slawn"),
        "gaelic": ("Mar sin leat", "mar shin lat"),
    },
    "how much": {
        "portuguese": ("Quanto custa?", "KWAN-too KOOSH-ta"),
        "greek": ("Póso kánei? (πόσο κάνει)", "POH-so KA-nee"),
        "turkish": ("Ne kadar?", "neh ka-DAR"),
        "welsh": ("Faint yw hwn?", "fynt yoo hoon"),
        "japanese": ("Ikura desu ka (いくらですか)", "ee-KOO-rah dess kah"),
        "chinese": ("Duōshao qián? (多少钱)", "dwaw-shau chyen"),
        "dutch": ("Hoeveel kost het?", "hoo-VAYL kost hut"),
        "spanish": ("¿Cuánto cuesta?", "KWAN-to KWES-ta"),
        "french": ("Combien ça coûte ?", "kom-BYAN sa KOOT"),
        "italian": ("Quanto costa?", "KWAN-to KOS-ta"),
        "german": ("Was kostet das?", "vas KOS-tet das"),
        "welsh": ("Faint yw hyn?", "fynt yoo hin"),
        "irish": ("Cé mhéad?", "kay vayd"),
    },
    "the bill": {
        "spanish": ("La cuenta, por favor", "la KWEN-ta por fa-VOR"),
        "french": ("L'addition, s'il vous plaît", "la-dee-SYON seel voo PLEH"),
        "italian": ("Il conto, per favore", "eel KON-to per fa-VO-reh"),
        "german": ("Die Rechnung, bitte", "dee REKH-noong BIT-tuh"),
        "welsh": ("Y bil, os gwelwch yn dda", "uh bill os GWEL-ookh un thah"),
    },
    "sorry": {
        "spanish": ("Perdón", "per-DON"),
        "french": ("Pardon", "par-DON"),
        "italian": ("Scusi", "SKOO-zee"),
        "german": ("Entschuldigung", "ent-SHOOL-dee-goong"),
        "welsh": ("Mae'n ddrwg gen i", "mine throog gen ee"),
        "irish": ("Tá brón orm", "taw brone or-um"),
    },
    "i don't understand": {
        "spanish": ("No entiendo", "no en-TYEN-do"),
        "french": ("Je ne comprends pas", "zhuh nuh kom-PRAN pa"),
        "italian": ("Non capisco", "non ka-PEES-ko"),
        "german": ("Ich verstehe nicht", "ikh fair-SHTAY-uh nikht"),
        "welsh": ("Dw i ddim yn deall", "doo ee thim un day-al"),
        "irish": ("Ní thuigim", "nee HIG-im"),
    },
    "do you speak english": {
        "spanish": ("¿Habla inglés?", "AB-la een-GLES"),
        "french": ("Parlez-vous anglais ?", "par-lay VOO on-GLEH"),
        "italian": ("Parla inglese?", "PAR-la een-GLEH-zeh"),
        "german": ("Sprechen Sie Englisch?", "SHPREKH-en zee ENG-lish"),
        "welsh": ("Ydych chi'n siarad Saesneg?", "UD-ikh kheen SHAR-ad SICE-neg"),
    },
    "water": {
        "spanish": ("Agua", "AH-gwa"),
        "french": ("De l'eau", "duh loh"),
        "italian": ("Acqua", "AH-kwa"),
        "german": ("Wasser", "VAS-ser"),
        "welsh": ("Dŵr", "door"),
        "irish": ("Uisce", "ISH-ka"),
        "gaelic": ("Uisge", "OOSH-ka"),
    },
    "help": {
        "spanish": ("Socorro", "so-KO-ro"),
        "french": ("Au secours", "oh suh-KOOR"),
        "italian": ("Aiuto", "a-YOO-to"),
        "german": ("Hilfe", "HIL-fuh"),
        "welsh": ("Help!", "help"),
        "irish": ("Cabhair!", "KOW-ir"),
        "gaelic": ("Cuideachadh!", "KOO-jokh-ug"),
    },
    "good morning": {
        "spanish": ("Buenos días", "BWEH-nos DEE-as"),
        "french": ("Bonjour", "bon-ZHOOR"),
        "italian": ("Buongiorno", "bwon-JOR-no"),
        "german": ("Guten Morgen", "GOO-ten MOR-gen"),
        "welsh": ("Bore da", "BOR-eh da"),
        "irish": ("Maidin mhaith", "MA-jin vah"),
        "gaelic": ("Madainn mhath", "MA-din vah"),
    },
    "good night": {
        "spanish": ("Buenas noches", "BWEH-nas NO-chess"),
        "french": ("Bonne nuit", "bon NWEE"),
        "italian": ("Buonanotte", "bwo-na-NOT-teh"),
        "german": ("Gute Nacht", "GOO-tuh nakht"),
        "welsh": ("Nos da", "noss da"),
        "irish": ("Oíche mhaith", "EE-ha vah"),
    },
    "cheers": {
        "spanish": ("Salud", "sa-LOOD"),
        "french": ("Santé", "son-TAY"),
        "italian": ("Salute", "sa-LOO-teh"),
        "german": ("Prost", "prohst"),
        "welsh": ("Iechyd da", "YAKH-id da"),
        "irish": ("Sláinte", "SLAWN-cha"),
        "gaelic": ("Slàinte mhath", "SLAWN-cha vah"),
    },
}

# Welsh and Irish, for the phrases a visitor is actually asked for. Merged into the table above
# rather than given to it: `PHRASES.update({"thank you": {...}})` replaces the whole entry, and
# the first cut of this wiped Merci, Gracias, Grazie and Danke off every phrase.
WELSH_AND_IRISH = {
    "thank you": {"welsh": ("Diolch", "DEE-olch"),
                  "irish": ("Go raibh maith agat", "guh rev MAH-ut uh-gut")},
    "please": {"welsh": ("Os gwelwch yn dda", "os GWEL-ookh un thah"),
               "irish": ("Le do thoil", "leh duh HULL")},
    "hello": {"welsh": ("Helo", "HEH-loh"),
              "irish": ("Dia duit", "DEE-uh gwit")},
    "goodbye": {"welsh": ("Hwyl fawr", "hoo-il vowr"),
                "irish": ("Slán", "slawn")},
    "sorry": {"welsh": ("Mae'n ddrwg gen i", "mine throog gen ee"),
              "irish": ("Tá brón orm", "taw brone or-um")},
    "water": {"welsh": ("Dŵr", "door"),
              "irish": ("Uisce", "ISH-keh")},
}
for _concept, _by_language in WELSH_AND_IRISH.items():
    PHRASES.setdefault(_concept, {}).update(_by_language)

LANGUAGES = {
    "spanish": "Spanish", "espanol": "Spanish", "español": "Spanish",
    "french": "French", "francais": "French", "français": "French",
    "italian": "Italian", "italiano": "Italian",
    "german": "German", "deutsch": "German",
    # Welsh and Irish are asked for by name in the UK far more than Italian is, and
    # "whats thank you in welsh" had no answer at all
    "welsh": "Welsh", "cymraeg": "Welsh", "wales": "Welsh",
    "irish": "Irish", "gaeilge": "Irish", "gailge": "Irish", "as gaeilge": "Irish",
    "gaelic": "Scottish Gaelic", "scottish gaelic": "Scottish Gaelic",
    # The rest were missing too, so "how do i say thank you in japanese" reached nothing and the
    # composer's small-talk pool wrote it a note-writing tip.
    "portuguese": "Portuguese", "portugues": "Portuguese", "português": "Portuguese",
    "greek": "Greek", "turkish": "Turkish",
    "japanese": "Japanese", "chinese": "Chinese", "mandarin": "Chinese",
    "dutch": "Dutch",
}

# the phrase the person is asking about -> the PHRASES key
CONCEPTS = (
    (("toilet", "loo", "bathroom", "restroom", "bog"), "toilet"),
    (("thank", "thanks"), "thank you"),
    (("please",), "please"),
    (("hello", "hi"), "hello"),
    (("good morning",), "good morning"),
    (("good night", "goodnight"), "good night"),
    (("cheers",), "cheers"),
    (("goodbye", "bye"), "goodbye"),
    (("how much", "cost", "price"), "how much"),
    (("bill", "check", "cheque"), "the bill"),
    (("sorry", "excuse me"), "sorry"),
    (("don't understand", "dont understand", "do not understand"), "i don't understand"),
    (("speak english", "english"), "do you speak english"),
    (("water",), "water"),
    (("help",), "help"),
)


# The words a person uses to name the phrase they want. They are keys as well as a lookup
# table, so "whats thank you in welsh" reaches the phrases with no verb in it at all.
CONCEPT_WORDS = ("thank you", "thanks", "thank", "cheers", "hello", "hi", "please", "goodbye",
                 "bye", "sorry", "excuse me", "water", "help", "toilet", "loo", "bathroom",
                 "good morning", "good night", "goodnight", "how much", "the bill", "bill",
                 "dont understand", "don't understand", "do you speak english", "speak english")

# "what does diolch mean" and "what does sláinte mean" are the same table read backwards: the
# foreign word in the line names the language and the phrase, so the answer is the English.
NATIVE = {}
for _concept_name, _said_in in PHRASES.items():
    for _language, (_phrase, _say) in _said_in.items():
        # the phrase, and not each word of it: "die Rechnung" was also a key for the bare
        # German article, so "what does die mean in german" was answered "the bill"
        for _word in (_phrase, _phrase.strip("!?¿")):
            _word = _word.strip("!?¿.,").lower()
            # "help" is English as well as Welsh, and so are a few others: a word that is the
            # English phrase itself would answer "what does help mean" with a translation.
            # The same holds for a table word the engine already reads as an English word:
            # German "was" is English "was" and German "die" is English "die", and a table of
            # them made every "what was that noise" and "i mean it was fine" a translation.
            # The list is BASE, the words themselves, and not LEXICON, which also holds every
            # generated form and misspelling the fixers know ("wassing", "wasly", "wasser" came
            # in that way): a word a person asks about that happens to sit in the typo list is
            # not an English word, and "what does wasser mean" must still say water.
            if (len(_word) > 2 and _word.isalpha() and _word not in _concept_name.split()
                    and _word not in ENGLISH_WORDS):
                NATIVE.setdefault(_word, (_language, _concept_name))
                # people type sláinte and slàinte without the accent more often than with it
                _plain = "".join(c for c in unicodedata.normalize("NFKD", _word)
                                 if not unicodedata.combining(c))
                if _plain != _word and _plain not in ENGLISH_WORDS:
                    NATIVE.setdefault(_plain, (_language, _concept_name))
del _concept_name, _said_in, _language, _phrase, _say, _word, _plain


# A foreign word is often an English one as well, and the table cannot help that: German "was"
# is "how much", so every "what was the titanic", "what was the black death" and "what was the
# roman empire" was answered with a phrase card about a German price. The words are the
# translation table's, so the fence has to be the question: a line that asks what the word means,
# names the language, or is the phrase on its own.
_A_MEANING_IS_ASKED = re.compile(
    r"\bwhat\s+(?:does|do|did)\b[^?.!]{0,40}\bmean(?:s|ing)?\b"
    r"|\bmean(?:s|ing|ings)?\b"
    r"|\bhow\s+(?:do|can|would|should|could)\s+(?:you|i|we)\s+say\b"
    r"|\btranslat(?:e|ion|ions)\b", re.I)

LANGUAGE_NAMES = ("german", "french", "spanish", "italian", "welsh", "irish", "gaelic",
                  "portuguese", "greek", "polish", "dutch", "turkish", "japanese", "chinese",
                  "mandarin", "cantonese", "arabic", "russian", "hindi", "urdu", "bengali",
                  "punjabi", "somali", "romanian", "czech", "swedish", "norwegian", "danish",
                  "finnish", "korean", "thai", "vietnamese", "hebrew", "swahili", "tagalog",
                  "ukrainian", "latin", "afrikaans", "albanian", "bulgarian", "croatian",
                  "serbian", "slovak", "slovenian", "estonian", "latvian", "lithuanian",
                  "hungarian", "icelandic", "malay", "indonesian", "persian", "farsi", "kurdish",
                  "amharic", "yoruba", "zulu", "xhosa", "creole", "filipino", "sign language")


# The words that carry no meaning on their own in an English line, so a line made only of them and
# one of the table's words is the word being asked about rather than a sentence using it.
_ENGLISH_FURNITURE = frozenset((
    "a", "an", "the", "is", "are", "was", "were", "be", "am", "what", "whats", "what's", "which",
    "it", "this", "that", "these", "those", "in", "on", "of", "to", "for", "and", "or", "do",
    "does", "did", "you", "i", "we", "they", "he", "she", "mean", "means", "meaning", "say",
    "please", "so", "my", "your", "his", "her", "their", "our", "there", "here", "s"))


# The essay-ending row keys "ending", which the normaliser folds to "end", and its co-word list
# holds "how" and "what" - the two commonest ways of asking anything. So every line with the word
# "end" in it was offered the last paragraph of an essay: "what do i ask them at the end" (an
# interview), "how do i end a chat at a party". The avoid list above collects those one at a time
# and can never catch up. The row is right about an essay ending and every way of asking for one
# either names something written or names the conclusion outright, so it asks for one of the two
# rather than carrying a list of what it is not about.
_SOMETHING_WRITTEN = (
    "essay", "essays", "dissertation", "coursework", "assignment", "assignments", "report",
    "reports", "paragraph", "paragraphs", "write", "writing", "written", "thesis", "paper",
    "papers", "project", "projects", "chapter", "chapters", "story", "stories", "mark", "marks",
    "grade", "grades", "tutor", "teacher", "lecturer", "uni", "university", "college", "gcse",
    "a level", "a-level", "aqa", "edexcel", "english", "history", "politics", "sociology",
    "psychology", "biology", "geography", "question", "questions", "title",
    # a spoken ending is the one thing here that is not written, and it has no answer of its own
    # yet: standing the row down for "how do i end a speech" leaves the person with a stall, so
    # the row keeps it
    "speech", "speeches", "talk", "talks",
)
_A_CONCLUSION_SAID = ("conclusion", "conclusions", "conclude", "sum up", "summarise", "summarize",
                      "last paragraph", "final paragraph", "wrap up")


def _the_ending_is_written(understood):
    """True when the line is about the end of something written, not the end of anything."""
    clean = " ".join(str(understood.get("clean") or understood.get("text") or "").split()).lower()
    if not clean:
        return False
    for word in _A_CONCLUSION_SAID + _SOMETHING_WRITTEN:
        if re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", clean):
            return True
    return False


def _a_translation_is_asked(understood):
    """True when the line asks for the meaning of a foreign word, not when it uses an English one."""
    clean = str(understood.get("clean") or understood.get("text") or "").lower()
    if _A_MEANING_IS_ASKED.search(clean):
        return True
    # a language named in the line counts only when the line also carries one of the table's
    # words: "what was the french revolution" names French and is a history question
    words = [str(word).lower() for word in (understood.get("words") or ())]
    # the word itself, with the English around it taken away: German `was` is in this table as
    # "how much", so an English "was" says nothing about whether a phrase is being asked for
    content = [word for word in words if word not in _ENGLISH_FURNITURE]
    named = any(re.search(r"(?<![a-z])" + name + r"(?![a-z])", clean) for name in LANGUAGE_NAMES)
    if named and (any(word in NATIVE for word in content) or _A_MEANING_IS_ASKED.search(clean)
                  or re.search(r"\bsay\b|\bhow do you\b|\bhow do i\b", clean)):
        return True
    # the phrase on its own: "diolch", "bitte". Every content word has to be one of the table's
    # words, because a short English line is not a phrase: "what was apartheid" is three words
    # and German `was`.
    return bool(content) and all(word in NATIVE for word in content)


def _what_does_it_mean(memory, understood):
    """Answer "what does <foreign word> mean" from the phrases table, backwards."""
    if not _a_translation_is_asked(understood):
        return None
    clean = (understood.get("clean") or "").lower()
    for word in sorted(NATIVE, key=len, reverse=True):
        if re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", clean):
            language, concept = NATIVE[word]
            english = "I don't understand" if concept == "i don't understand" else concept
            return (f"That is {LANGUAGES[language]} for '{english}'. It is a phrase people say a "
                    "lot, so learn it whole and out loud rather than word by word, and the reply "
                    "you get back will tell you whether it landed.")
    return None


# The phrases table read backwards answers "what does diolch mean", and its keys are not all
# foreign words: `was` is German for what, `die` is German for the, and `faint`, `bore`, `tot`,
# `non` and `salute` are English (or look it). The ask half of that row is "what does", which
# scores on its words one at a time, so a bare "what" was enough - and any English line with one
# of those words in it came back as a translation. Measured on main: "what do i do if i was
# overpaid at work", "what should i do if i was sold a dodgy car", "what can i do if i was given
# the wrong medication", "what happens if i was late paying rent" and "what should i wear to a die
# party" all answered "That is German for 'how much'". So the row reads the frame itself.
_MEANING_FRAME = re.compile(r"\bwhat\s+does\b|\bwhat'?s\b|\bwhat\s+is\b|\bmean(s|ing)?\b"
                           r"|\bstand\s+for\b|\btranslate[sd]?\b|\btranslation\b")
# A word that a person also uses in English has to be asked about outright: "what does non mean"
# is a question about the word, "what is a faint line" is about a pregnancy test.
_ASKED_OUTRIGHT = re.compile(r"\bmean(s|ing)?\b|\bstand\s+for\b|\btranslate[sd]?\b"
                             r"|\bhow\s+do\s+you\s+say\b")
_ENGLISH_TOO = frozenset((
    "was", "die", "non", "tot", "mas", "nos", "dia", "per", "mar", "faint", "bore", "dank",
    "salute", "sante", "santé", "wasser", "ble"))


def _a_word_is_being_asked_about(understood):
    """True when the line asks what a word means, and the word in it is the thing asked about."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not _MEANING_FRAME.search(said):
        return False
    named = [word for word in NATIVE
             if re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", said)]
    if not named:
        return False
    if any(word not in _ENGLISH_TOO for word in named):
        return True
    # every word in the line that the table knows is an English word too, so the person is asking
    # about the English one unless the foreign language is named or the word is quoted
    return bool(_find(said, LANGUAGES)) or '"' in said or "\u201c" in said


def _find(text, table):
    for name in sorted(table, key=len, reverse=True):
        if re.search(r"\b" + re.escape(name) + r"\b", text):
            return name
    return None


def _concept(text):
    """The PHRASES key the line is asking about, with word edges respected either side."""
    for alternatives, name in CONCEPTS:
        for alternative in alternatives:
            if re.search(r"(?<![a-z])" + re.escape(alternative) + r"(?![a-z])", text):
                return name
    return None


# A language named as an adjective is not always a language question: "whats french food like"
# names French and asks about the plate, and the whole-phrases answer to "how do you say ..." is
# no answer to it. Only the plate words with no say or translate in the line stand this down, so
# "how do i say food in french" is still a phrase.
_ABOUT_THE_PLATE = re.compile(
    r"(?<![a-z])(?:food|foods|cuisine|dish|dishes|eat|eating|meals?|restaurants?)"
    r"(?![a-z])", re.I)
_SAY_OR_TRANSLATE = re.compile(
    r"(?<![a-z])(?:say|says|saying|pronounce|pronounced|translate|translated|translation|"
    r"mean|means|how do you say)(?![a-z])", re.I)


# A language named in the line is not a phrase being asked for: the third key group of the
# phrasebook rows reads "whats"/"what is", and "what was the french revolution" stems straight
# into it, so a school question was answered with "Learn French as a set of whole phrases".
_PHRASE_ASK = re.compile(
    r"\bhow\b[^?.!]{0,30}\b(?:say|pronounce|translate)\b"
    r"|\bsay\b|\bpronounce\b|\btranslat(?:e|ion|ions)\b"
    r"|\bwords?\s+for\b|\bphrase(?:s)?\s+for\b"
    # "in welsh" is the ask as well: without it "what does faint mean in welsh" was the fainting
    # first-aid card, because "faint" is not one of the concepts the phrasebook keys
    r"|\bin\s+(?:%s)\b" % "|".join(LANGUAGE_NAMES), re.I)


# The words a correction is made of, which say nothing about what is being corrected: "actually
# french", "what about spanish", "no, italian". They are taken off before a line is judged to be
# a language and nothing else. The English furniture of a question is the same kind of word, so
# it comes along rather than being written out twice.
_CORRECTION_WORDS = frozenset((
    "actually", "no", "not", "sorry", "im", "i'm", "meant", "mean", "instead", "rather",
    "then", "make", "change", "changed", "changing", "switch", "switched", "let", "lets",
    "let's", "learn", "learning", "learnt", "studying", "study", "pick", "picking",
    "choose", "choosing", "language", "languages", "one", "ones", "about", "also", "too",
    "both", "them", "other", "another", "re", "well", "decide", "deciding", "decided"))
_CORRECTION_FURNITURE = _ENGLISH_FURNITURE | _CORRECTION_WORDS


def _a_language_alone(text):
    """True when the line is a language and nothing else: `actually french`, `what about spanish`.

    A correction that swaps one language for another is a language line, and the phrasebook is
    the answer it wants. #11118's fence on "what was the french revolution" stood the phrasebook
    down for every line that named a language without a say or translate in it, so `actually
    french` after "im learning spanish" lost the French phrases and got "I'm listening - say more
    if it helps." The history question it was written for names a language among other words;
    this one has nothing else in it.
    """
    words = [word for word in re.findall(r"[a-z']+", text)
             if word not in _CORRECTION_FURNITURE]
    return bool(words) and all(word in LANGUAGE_NAMES for word in words)


def _a_phrase_is_asked(understood):
    """True when the line asks for a phrase in another language rather than mentioning one."""
    text = " ".join(str((understood or {}).get("clean")
                       or (understood or {}).get("text") or "").lower().split())
    if _PHRASE_ASK.search(text):
        return True
    # naming the phrase is the ask: "whats thank you in spanish" has no verb at all
    if _concept(text):
        return True
    # the language on its own is the ask as well: a correction that names one language and
    # nothing else is a line about that language, not a history question that mentions one
    return _a_language_alone(text)


def _say_in_language(memory, understood):
    """Answer "how do you say <phrase> in <language>" from the PHRASES table."""
    clean = (understood.get("clean") or "").lower()
    if _ABOUT_THE_PLATE.search(clean) and not _SAY_OR_TRANSLATE.search(clean):
        return None
    language = _find(clean, LANGUAGES)
    if not language:
        return None
    concept = _concept(clean)
    if not concept:
        return (f"Learn {LANGUAGES[language]} as a set of whole phrases rather than word by word, "
                "and learn them out loud: 'hello', 'please', 'thank you', 'sorry, I don't understand', "
                "'do you speak English?' and 'how much is that?' cover most of a short trip. Ask me any "
                "of those in one language and I will give you the phrase and how to say it.")
    pair = PHRASES.get(concept, {}).get(language)
    if not pair:
        # Welsh and Irish are a short list, and the others are short too: a phrase I do not have
        # is the whole-phrases answer rather than a guess or a shrug.
        return (f"Learn {LANGUAGES[language]} as a set of whole phrases rather than word by word, "
                "and learn them out loud: 'hello', 'please', 'thank you', 'sorry, I don't understand', "
                "'do you speak English?' and 'how much is that?' cover most of a short trip. Ask me any "
                "of those in one language and I will give you the phrase and how to say it.")
    phrase, say = pair
    question = concept if concept != "i don't understand" else "I don't understand"
    return (f"'{question.capitalize()}' in {LANGUAGES[language]} is {phrase} — say it roughly "
            f"\"{say}\". Learn it out loud a few times rather than reading it, and people will "
            "understand you even if the pronunciation is not perfect.")


# --- revising -------------------------------------------------------------
# A "test" is often not an exam: a blood test, a driving test and an eye test are all
# questions for someone else, so lines that mention them pass instead of getting revision
# advice.
# "30 degree heat" and "a 90 degree angle" are the other word: a degree of temperature or of turn is
# not the degree you study for, and two university rows were answering them ("how much water should
# i drink walking in 30 degree heat" got the pass-mark card).
_A_DEGREE_OF_HEAT = ("heat", "warm", "hot", "cold", "weather", "celsius", "centigrade",
                     "fahrenheit", "temperature", "thermostat", "fever", "oven",
                     "washing machine", "angle", "bend", "slope", "latitude",
                     "gas mark", "convert", "conversion", "degrees c", "degrees f")

# A number and "degrees" together is usually the weather: "wedding in italy and 35 degrees, what do
# i wear" was answered with what a degree passes at, and so was "his room is about 20 degrees" in
# the middle of a baby-sleep chat. A spelled number counts too, because the line is read twice and
# "about twenty degrees" is the same line as "about 20 degrees".
# A class of degree is written with a figure too, and it is not a reading: "is a 2:1 degree good"
# and "is a 2 2 degree bad" stood the pass-mark row down and got a punt instead, because the 1 and
# the 2 are digits in front of "degree". A figure glued to a colon or to another figure is a class,
# so the temperature needs a figure that stands on its own (khaki-key's read on #12922).
_TEMPERATURE_DEGREES = re.compile(
    r"(?<![\w:.\d])(?<!\d\s)(?:[1-9]|[1-3][0-9]|40)\s*(?:degrees?\b|deg\b|°)")
_NUMBER_WORDS = frozenset((
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
    "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred"))


def _a_number_word(words):
    for word in words:
        for part in re.split(r"[-\s]", word):
            if part in _NUMBER_WORDS:
                return True
    return False


def _the_degrees_are_heat(understood):
    """False when "N degrees" is a temperature rather than a qualification.

    A number before "degrees" is a temperature unless the line says something else about
    studying: "35 degrees in my exam" is a mark, "wedding in italy and 35 degrees" is the
    weather. The word "degree" itself cannot count as the study word, because the phrase
    carries it.
    """
    text = str(understood.get("clean") or understood.get("text") or "").lower()
    words = set(understood.get("words") or ())
    if not ({"degree", "degrees"} & words):
        return True
    if not (_TEMPERATURE_DEGREES.search(text) or _a_number_word(words)):
        return True
    if (words - {"degree", "degrees"}).intersection(_EXAM_IN_THE_WORDS):
        return True
    if re.search(r"\b(?:my|the|a|his|her|their|your)\s+degree\b|\bdegree\s+(?:in|course|exam)\b",
                 text):
        return True
    return False


# A line that fails at something, and the words that say the thing is an exam.
_FAILING = frozenset(("fail", "failed", "failing", "fails", "flunk", "flunked", "flunking"))
_EXAM_IN_THE_WORDS = frozenset((
    "exam", "exams", "examination", "gcse", "gcses", "a-level", "a-levels", "alevel", "alevels",
    "as-level", "as-levels", "mock", "mocks", "coursework", "resit", "resits", "retake",
    "retakes", "remark", "remarks", "module", "modules", "degree", "semester", "dissertation",
    "grade", "grades", "uni", "university", "college", "school", "sixth", "year", "paper",
    "papers", "results", "sats", "btec", "ib",
))


def _a_failure_of_something_else(understood):
    """True when the line fails at something that is not named as an exam.

    "i failed" is a key of the exam-resit answer, and with the "i" and "my" of its second key
    list it was enough on its own: "im learning to drive at 40" / "i failed my test twice" was
    told to speak to the school or college on results day about a resit in maths and English,
    and a swim badge went the same way. The exam words above are what makes a bare failure an
    exam question; without one, the thing they failed at is the chat's own subject.
    """
    words = [str(word).lower() for word in (understood or {}).get("words") or []]
    if not any(word in _FAILING for word in words):
        return False
    return not any(word in _EXAM_IN_THE_WORDS for word in words)


NOT_AN_EXAM = ("blood", "driving", "pregnant", "pregnancy", "swab", "urine", "hearing",
               "eye", "eyes", "sight", "allergy", "allergies", "covid", "pcr", "lateral",
               "theory", "smear",
               # a CV is revised too, and that is a job question, not a revision one
               "cv", "resume", "résumé",
               # a Test match is played, not revised for: "how many overs in a test match" was
               # given the revision timetable because the line said "test" and "how many".
               # Every cricket word stands this answer down, so a sport line keeps its rule.
               "cricket", "cricketer", "cricketers", "test match", "test matches", "wicket",
               "wickets", "innings", "bowler", "bowlers", "bowling", "batting", "batter",
               "batsman", "stumps", "ashes", "lbw",
               # "how do I test a starter motor" is a car that will not start, not a test to
               # revise for: the key group takes any "test" with any "start".
               "motor", "motors", "engine", "engines", "car", "cars", "van", "vans",

               "battery", "batteries", "lawnmower", "mower", "boiler", "starter motor",
               # "ok changing the subject, im planning a curry tonight" is the reader moving the
               # conversation on, and the word "subject" in it was read as a school subject: the
               # revision timetable answered a line about cooking dinner. A phrase that only makes
               # the switch is never a subject being studied.
               "changing the subject", "change the subject", "changed the subject",
               "change of subject", "off topic", "on a different subject",
               "onto a different subject")

# A note written *to* somebody is not a note taken in a lecture. This row keys "note" and "write",
# which is the note-taking question, and it carries a bias of 1, so it took the person's note on a
# tie: "how do i write a thank you note" was told to leave a wide margin for questions after the
# lesson, and "how do i write an apology note" the same. Both cards are already written and word
# the note from what the line names - `thanks-for-hospitality` in wording.py and
# `apology-fits-the-person` in language.py - so the phrases below only say which note this is. A
# note to a teacher, a landlord or a boss is the same kind of thing, and "note to my" covers those
# without touching "notes from my lecture", where "note" is followed by "s".
NOT_A_PERSONS_NOTE = (
    "thank you note", "thank-you note", "thankyou note", "thanks note",
    "apology note", "apologise note", "apologize note", "apologising note", "apologizing note",
    "sorry note", "condolence note", "sympathy note", "get well note", "welcome note",
    "short note", "little note", "note saying", "a note to my", "note to my", "note for my",
    "note to the", "note for the", "note to a", "note for a",
)

# "Losing track" is a focus phrase and it is also how a person says where their money went:
# "i keep losing track of what goes out" and "i keep losing track of my spending" were answered
# with the phone-in-another-room block, which is a confident reply to a question nobody asked.
# The money reading has its own row (`track-spending` in bot/knowledge/money.py) and it is the one
# the line belongs to; these words stand the focus row down so it can take the turn. A focus line
# that happens to name money is rare, and any other second group still keeps it here.
LOSING_TRACK_OF_MONEY = ("money", "spending", "spent", "spend", "budget", "budgets",
                         "outgoings", "goes out", "going out of my account", "bank", "bills",
                         "paycheck", "payday", "salary", "wages", "direct debit",
                         "direct debits", "standing order", "statement", "account",
                         "what i earn", "savings", "overdrawn", "debt", "debts"),


# "Test" is a study word and it is also a verb. "How do i test if the chicken is cooked",
# "how do i test my wifi speed", "how do i test the tenses" put a thing straight after it, and
# the thing - the food, the router, the verbs - is what the line is about; the revision plan is
# a confident wrong answer to all of them. A test to sit is named as a noun, with a preposition
# or a date after it: "my test is on friday", "a test in the morning", "revising for a test".
# The shapes below are the verb, so `revision-start` stands down and the food or the machine
# answers instead (an entry whose reply comes back empty is passed over, see `_offer` in
# bot/modules/answers.py).
TEST_AS_A_VERB = re.compile(
    r"\btest(?:ed|ing|s)?\s+(?:if|whether|that|the|a|an|my|your|our|his|her|its|this|these|"
    r"those|any|some|for|out|with|by)\b", re.I)

# "A test a week on friday" is a count of days, not the verb: the word after the article is a
# length of time, which is how people say how long they have left.
TIME_AFTER_TEST = re.compile(
    r"\btest\s+(?:a|an|one|two|three|\d+)\s+"
    r"(?:week|weeks|day|days|month|months|year|years|fortnight|hour|hours|minute|minutes)\b",
    re.I)

# What a revision line is about, which keeps "how do i test my memory" and "how do i test my
# knowledge before the exam" here: the word after "test" is the thing being learnt, not a thing
# being tested.
LEARNING_OBJECTS = frozenset("""knowledge memory learning revise revised revising revision
exam exams mock mocks vocab vocabulary spelling spellings grammar tenses reading maths math
gcse alevel a-level subject subjects topic topics syllabus paper comprehension
know knows knew remember remembers remembered learnt learned french spanish german italian
english history geography science biology chemistry physics chinese""".split())


def _a_test_of_a_thing(understood):
    """True when "test" in this line is the verb and the thing after it is the subject."""
    if not isinstance(understood, dict):
        return False
    text = understood.get("norm_text") or understood.get("clean") or ""
    if not text or not TEST_AS_A_VERB.search(str(text)):
        return False
    if TIME_AFTER_TEST.search(str(text)):
        return False
    words = {str(word).lower() for word in (understood.get("words") or [])}
    return not (words & LEARNING_OBJECTS)


def _unless_testing_a_thing(reply):
    """The reply, unless the line is testing a thing rather than revising for a test."""
    def answer(memory, understood):
        if _a_test_of_a_thing(understood):
            return ""
        return reply
    return answer


# A mock is not results day: there is no Clearing and no remark, only time to fix what the
# paper showed. Lines that say mock, predicted or practice paper are answered by the mock
# entries instead of the results-day one.
# "I keep falling asleep revising" is a sleep question: study-awake answers it.

ASLEEP = ("asleep", "falling asleep", "sleepy", "tired", "drowsy", "nodding off", "sleep")

# A memory card is about the person asking, unless the line hands the forgetting to someone
# else: "my dad forgets names all the time" and "my husband forgets names" were answered with the
# trick for remembering a new name, and "my mum cant remember words" with the vocabulary drill.
# The relative plus a forgetting word is the other subject, and the row that answers it is the one
# about a relative whose memory is going.
_OTHER_PEOPLE = frozenset((
    "dad", "dads", "father", "mum", "mums", "mother", "husband", "wife", "partner",
    "spouse", "nan", "nana", "gran", "granny", "grandma", "grandmother", "grandad",
    "granddad", "grandfather", "brother", "sister", "aunt", "auntie", "uncle",
    "father in law", "mother in law", "in laws", "other half", "boyfriend", "girlfriend"))
_FORGETTING = frozenset((
    "forget", "forgets", "forgetting", "forgot", "forgotten", "remember", "remembers",
    "remembering", "memory", "recall", "names", "name", "words"))


EXAM_NERVES = ("Going blank is your body, not your memory: breathe out longer than you breathe "
               "in for a minute and it settles. Then read the whole paper and start with the "
               "question you know best, and if a question stalls, jot the first line you can and "
               "move on. Do not spend the first five minutes trying to feel calm — just start "
               "writing.")


def _exam_nerves(memory, understood):
    """The exam nerves answer, with the body named first when the line is a symptom."""
    said = str(understood.get("clean") or understood.get("text") or "").lower()
    if any(phrase in said for phrase in NERVES_BODY):
        # the sign is the one they typed, said back to them
        return (nerves_opening(said, "before an exam", "adrenaline, not a bug") +
                ": eat something plain, take water in with you, and breathe out slowly for a "
                "minute in the queue. " + EXAM_NERVES)
    return EXAM_NERVES


def _somebody_else_forgets(understood):
    """True when the forgetting in the line belongs to another person, not the speaker."""
    words = [str(word).lower() for word in (understood or {}).get("words") or []]
    if not any(word in _FORGETTING for word in words):
        return False
    return any(word in _OTHER_PEOPLE for word in words)

# "how do i take a break from studying" and "how often should i take a break when revising" got
# the start-today answer and the test-yourself answer, because both entries key the bare word
# "how" and neither entry is about stopping. The stopping answer is study-how-long, which already
# says 25 to 45 minutes and then five to ten away from the desk.
REST_ASK = ("take a break", "take breaks", "take my break", "take a rest", "a break from",
            "break from studying", "break from revision", "break from revising", "breaks from",
            "rest from studying", "how often break", "how often should i break",
            "how long a break", "how long should i break", "break between", "breaks between",
            "should i break", "should i take a break")

# Reading the instructions for a flat pack is a manual, not a revision plan.
# "Revise" also means amend a document, and a rota, a contract, a job advert, a policy, a budget
# or an essay is a writing job rather than exam revision. Where the bare word is a school subject
# people revise, only the amend sense is listed ("contract law", "sign language", "40 Spanish
# words"); "wording" and "words" are one stem, so it is "the wording" and never bare "wording".
# a line about a paper run out of time is the exam's pacing answer, not how to start
NOT_A_START_OF_EXAMS = ("running out of time", "run out of time", "ran out of time",
                       "out of time", "no time left", "time in the exam", "time in exams",
                       "finish the paper")
NOT_REVISION = ("instructions", "assembling", "manual", "flat pack", "flatpack", "ikea",
                "rota", "rotas", "advert", "adverts", "job advert", "the wording", "its wording",
                "policy document", "policy wording", "terms and conditions", "the invoice",
                "an invoice", "before signing",
                "revise the contract", "revise a contract", "revise my contract",
                "revising the contract", "revise the lease", "revise the agreement",
                "revise the budget", "revise my budget", "revise a budget",
                "revise my essay", "revise the essay", "revise my cv", "revise my resume")

# "How do i learn a language fast" has the shape of last-minute cramming and none of the
# meaning: there is no syllabus or mark scheme for speaking Spanish, and answering it with
# exam technique reads as a mistake. A line that names a language is the language entry's.
LANGUAGE_LEARNING = ("language", "languages", "spanish", "french", "italian", "german",
                     "portuguese", "japanese", "chinese", "mandarin", "cantonese", "welsh",
                     "korean", "russian", "arabic", "dutch", "greek", "polish", "turkish",
                     "urdu", "punjabi", "hindi", "british sign language", "sign language",
                     "fluent", "fluency", "fluently", "duolingo", "bilingual")

MOCK = ("mock", "mocks", "practice paper", "practice papers", "predicted",
        "predicted grade", "predicted grades")

# How people ask for advice on doing a study task: "what's a good way to revise", "any tips
# for revising", "what is the best way to write an essay". The ask is the same handful of words
# every time, so it is written once here rather than retyped (and half forgotten) in each entry:
# revision-active answered "how do i study more effectively" and shrugged at "whats a good way to
# revise", which is the same question with a different opener.
#
# "how" is deliberately not here: the entries that want it already carry it, and "how" on its
# own is the word that pulls a line in from a neighbour once the thing has matched.
HOW_ASK = ("good way", "best way", "right way", "proper way", "way", "ways", "tips", "tip",
           "advice", "the trick")

# The subject words a general revision method stands down for: a line that names maths,
# physics or chemistry is asking how to revise that subject, which is `revision-maths`'s row.
A_SUBJECT = ("maths", "math", "mathematics", "algebra", "geometry", "trigonometry", "physics",
             "chemistry")

A_MARK_NOT_A_GRADE = ("out", "of", "than", "per", "over", "under")
COUNTED_AFTER = ("marks", "mark", "out", "%", "percent", "subjects", "hours", "years", "days",
                 "weeks", "months", "kids", "children", "grandchildren", "questions", "pages",
                 "miles", "minutes", "times", "weeks", "gcse", "gcses")


# A grade name after the number makes the number a count, not a grade: "my daughter got 3 a stars
# in her gcses" is three A*s, and the card was telling a proud parent that a 3 is below a pass at
# GCSE and offering a retake. The letter grades are the same ("6 as and 3 bs" is six); "as" is
# only counted where a letter list is being read, so "a 4 as well" keeps its grade.
GRADE_NAME = re.compile(r"^(?:a[\s*-]?stars?|a\*s?|grades?|gcses?|a[\s-]?levels?|btecs?)\b")
LETTER_GRADES = re.compile(r"^(?:as|bs|cs|ds|es|fs|us)(?:$|\s+(?:and|in)\b)")


# A count of top grades is the person's news, not a question about one grade: "my daughter got 3 a
# stars in her gcses" is a proud line, and the scale recited back to it is as cold as the scolding
# was wrong. The greeting pool says somebody's good news back, so this card stands aside for it.
TOP_GRADES = re.compile(r"\b(?:[2-9]|1[0-2])\s+a[\s*-]?stars?\b|\b(?:straight|all)\s+(?:9s|8s)"
                        r"|\b[2-9]\s+a\*s\b", re.I)


def _grade_in(clean):
    """The grade number the line is about, or None when the number is a count.

    A grade is a number on its own ("a grade 4", "got a 5 in maths"). A score is a number
    with something either side of it ("5 marks ... out of 10", "4 out of 9 in my mock"),
    and reading that as a GCSE grade tells a person their 4 out of 9 is a standard pass.
    """
    words = clean.replace(",", " ").split()
    for n, word in enumerate(words):
        match = re.fullmatch(r"([1-9])%?", word)
        if not match:
            continue
        before = words[n - 1] if n else ""
        after = words[n + 1] if n + 1 < len(words) else ""
        next_two = " ".join(words[n + 1:n + 3])
        if before in A_MARK_NOT_A_GRADE or word.endswith("%"):
            continue
        if (after in COUNTED_AFTER or next_two.startswith("a level")
                or GRADE_NAME.match(next_two) or LETTER_GRADES.match(next_two)):
            continue
        return match.group(1)
    return None


def _grade_sentence(grade):
    """What one GCSE grade is worth, in the words a person wants to hear."""
    if grade == "9":
        return "A 9 is the top grade, above the old A*."
    if grade in ("7", "8"):
        a = "An" if grade == "8" else "A"
        return f"{a} {grade} is a top grade, the old A and above."
    if grade == "6":
        return "A 6 is a good pass, about the old B."
    if grade == "5":
        return "A 5 is a strong pass, the old high C, and over the line most colleges ask for."
    if grade == "4":
        return ("A 4 is a standard pass, the old C: you are over the line most colleges ask for, "
                "and a 5 is the strong pass above it.")
    return (f"A {grade} is below a pass at GCSE. Most sixth forms and colleges take you on other "
            "subjects and have you retake English or maths alongside, and that retake is free "
            "until you are 18, so it does not close anything on its own.")


SCORE = re.compile(r"\b(\d{1,3})\b[^0-9,]{0,30}?\b(?:out of|/)\s*(\d{1,3})\b")


def _score_out_of(clean):
    """A score and the total it is out of ("4 out of 9", "5 marks out of 10"), or None.

    Half marks on a piece of work is a proportion, not a grade: the useful thing to say is how
    much of the paper that is and which questions lost the rest, because one homework score
    says nothing about where a person stands in the subject overall.
    """
    match = SCORE.search(clean)
    if not match:
        return None
    got, total = int(match.group(1)), int(match.group(2))
    if not 1 <= got <= total <= 200 or total < 5:
        return None
    return got, total, round(100 * got / total)


def _score_sentence(score):
    """How much of the paper that is, in the words a person uses about their own work."""
    got, total, percent = score
    part = "about half" if 40 <= percent <= 60 else ("most" if percent > 60 else "under half")
    return f"That is {got} out of {total}, {part} the marks."


def _grade_answer(memory, understood):
    """"Is a grade 4 bad?": what the number is worth, and what it opens up."""
    clean = (understood.get("clean") or "").lower()
    if TOP_GRADES.search(clean):
        return None
    score = _score_out_of(clean)
    if score is not None:
        return (_score_sentence(score) + " Treat that as a score rather than a grade, because a "
                "GCSE grade is where you stand across a whole subject and one piece of work "
                "cannot tell you that. Go through it and write down the questions that lost the "
                "marks, then ask your teacher for the mark scheme on the worst two, since the "
                "same kind of question is usually where the marks are next time.")
    grade = _grade_in(clean)
    if grade is None:
        # No number to explain: the scale is only worth reciting to a line about GCSE grades,
        # not to a line that mentions a number for another reason ("2 a levels and a btec").
        if not re.search(r"\b(?:gcses?|grades?|marks|score|scores|pass|passed|mocks?|exams?)\b",
                         clean):
            return None
        return ("GCSE grades run from 9 down to 1: 4 is a standard pass, 5 a strong one, and 7 "
                "to 9 are the top grades. Below 4 is not a pass yet, and English and maths can "
                "be retaken at college until you are 18. Tell me the grade and the subject and "
                "I will say what it opens up.")
    if grade >= "4":
        return (f"{_grade_sentence(grade)} English and maths are the two that colleges and "
                "employers look at first, whatever else you take.")
    return _grade_sentence(grade)


def _mock_answer(memory, understood):
    """A mock grade is a map of what to fix, not a verdict on the real exam."""
    clean = (understood.get("clean") or "").lower()
    grade = _grade_in(clean)
    score = _score_out_of(clean)
    answer = ("" if score is None else _score_sentence(score) + " ") + (
              "A mock or a predicted grade is a signal, not a verdict: find out which topics cost "
              "you the marks — the mark scheme for a mock, your teacher for a predicted grade — "
              "and give the worst two a 25-minute slot each week. Moving a grade or two in a term "
              "is normal.")
    if grade is not None:
        answer = f"{_grade_sentence(grade)} {answer}"
    if re.search(r"\buni\b|\buniversit(y|ies)\b|\bcollege\b|sixth form", clean):
        answer += (" For the university question, what counts is what the course asks for: check "
                   "two or three you like and their entry requirements, because a 6 at GCSE rarely "
                   "closes a door on its own.")
    return answer

# A teacher who seems to hate you is a feeling first and a problem second, so the answer opens
# with the feeling when the line names one. bold-wheel's review: "the person said a feeling and
# got a plan"; main's warmer "Got it" was weaker, so the feeling stays and the plan follows it.
_FEELS_WRONGED = re.compile(
    r"\bhate[sd]?\b|\bhating\b|doesn'?t like me|does not like me|dont like me|"
    r"picks? on me|picked on|shouts? at me|\bunfair\b|\bmean\b|\bharsh\b|\bganging\b")


_IS_CHILD = re.compile(r"\bson\b|\bdaughter\b|\bchild\b|\bkids?\b|\bstepson\b|"
                       r"\bstepdaughter\b|\bniece\b|\bnephew\b|\bgrandson\b|"
                       r"\bgranddaughter\b")

# The bare "hates" and "hated" are in this row's keys, and "what do i do" is in its ask, so
# any line where one thing dislikes another was answered with the advice for a strict teacher:
# "my older dog hates the new puppy, what do i do" got "a miserable way to spend a lesson" and a
# plan about handing work in on time. The row is about school, so a line that leans on the bare
# hate has to name school or somebody at it. The named keys ("teacher hates me", "picks on me")
# carry that themselves, and the reading is the filled one, so "what do i do" as the next turn of
# a school chat still finds the teacher in the turn it leans on.
_SCHOOL_THINGS = re.compile(
    r"\bteacher|\bclass\b|\bclasses\b|\blesson|\bschool|\bform tutor\b|\btutor\b|"
    r"\bhead of year\b|\bheadteacher|\bpupil|\bhomework|\bmarks\b|\bdetention|\bexcluded\b|"
    # a child who hates a subject is the parent's line about school, and the subject is the
    # only school word in it: "my daughter hates maths, what do i do" was a punt without these
    r"\bmaths\b|\bmath\b|\bmathematics\b|\benglish\b|\bscience\b|\bhistory\b|"
    r"\bgeography\b|\bchemistry\b|\bphysics\b|\bbiology\b|\bfrench\b|\bspanish\b|"
    r"\bgerman\b|\bart\b|\bmusic\b|\bdrama\b|\bcomputing\b|\bict\b|\bgcses?\b|"
    r"\ba levels?\b|\bsats\b|\bform\b|\bassembly\b|\bplayground\b")


def _a_school_line(understood):
    """False when nothing in the line is about school, so the bare hate is somebody else's."""
    read = understood if isinstance(understood, dict) else {}
    said = " ".join(str(read.get("clean") or read.get("text") or "").lower().split())
    return bool(_SCHOOL_THINGS.search(said))


def _strict_teacher(memory, understood):
    """The strict-teacher advice, with a first sentence that takes the feeling when there is one."""
    text = ""
    if isinstance(understood, dict):
        text = understood.get("norm_text") or understood.get("clean") or ""
    plan = ("Do the boring things first and most strict teachers stop being a problem: hand work "
            "in on time, sit where you are seen, and ask one question in the lesson so they know "
            "your name for the right reason. If it is personal - sarcasm, singled out, marks that "
            "do not match the work - ask for the marked work back in writing and take it to your "
            "form tutor or head of year with dates and one example, not a general complaint. Keep "
            "the tone flat and factual, because a complaint that is a feeling gets deflected and "
            "one that is a date, a thing said and a mark does not. Ask a parent to come to the "
            "meeting if you are at school.")
    if not _FEELS_WRONGED.search(text.lower()):
        return plan
    # A parent's line ("my son hates his teacher") names the child, not themselves, and the
    # advice that ends "ask a parent to come to the meeting" is nonsense to a parent.
    if _IS_CHILD.search(text.lower()):
        return ("Take it seriously, then test it before you act: ask what happens in that lesson "
                "and whether other children say the same, because most of these turn out to be "
                "about one subject or one seating plan. Then ask the school for a short meeting "
                "with the class teacher, and go to the head of year if nothing changes in a term. "
                "Ask for the marked work so the conversation is about the marks and not about "
                "whether the teacher likes him.")
    return ("That is a miserable way to spend a lesson, and it is worth testing before you believe "
            "it: most teachers who seem to hate one person are strict with the whole class. " + plan)


# How far a language is from English sets the size of the job: the same rough figure the US
# Foreign Service quotes (600 hours to a working command of Spanish or French, about four times
# that for Japanese or Mandarin) said back in the shape a person asked it, as minutes a day.
LANGUAGE_HOURS = {
    "spanish": 600, "french": 600, "italian": 600, "portuguese": 600, "dutch": 600,
    "afrikaans": 600, "swedish": 600, "norwegian": 600, "danish": 600, "romanian": 600,
    "german": 750, "welsh": 900, "irish": 900, "greek": 1100, "polish": 1100,
    "russian": 1100, "turkish": 1100, "hebrew": 1100, "hindi": 1100, "urdu": 1100,
    "punjabi": 1100, "vietnamese": 1100, "thai": 1100, "persian": 1100, "farsi": 1100,
    "japanese": 2200, "chinese": 2200, "mandarin": 2200, "cantonese": 2200,
    "korean": 2200, "arabic": 2200,
}


def _names_a_language(understood):
    """True when the line names a language, or says what it is about without naming one.

    The hours figure is only honest about a language it can name, and the row is reached by the
    verb "learn" as well as by the language words: "im learning to play the guitar" then "how
    long will it take" is read as an ask about learning a guitar, and the row answered it with
    the one figure it has - "Spanish, French or Italian", because the line had given it no
    language to say. A line about a guitar, a cook or a book says none of these words, so the
    row stands down and the answer about the guitar gets the turn.

    A line that says "language", "fluent" or "hold a conversation" asks about a language
    without naming one, and the generic figure is its answer.
    """
    if not isinstance(understood, dict):
        return False
    clean = (understood.get("clean") or understood.get("text") or "").lower()
    # The words carry what the chat has already named as well as what this line does: after "im
    # learning spanish", the line "how long until i can hold a conversation" names no language
    # and is still about one, and the figure is its answer. So does the line it leans on: "how
    # long until im good at it" says nothing about a language by itself.
    leaned = understood.get("leans_on") if isinstance(understood.get("leans_on"), dict) else {}
    said = " ".join([clean, " ".join(understood.get("words") or ()),
                     str(leaned.get("text") or ""),
                     " ".join(leaned.get("words") or ())]).lower()
    if _find(said, LANGUAGE_HOURS):
        return True
    words = set(re.findall(r"[a-z']+", said))
    return bool(words & {"language", "languages", "fluent", "fluency", "fluently", "bilingual",
                         "conversation", "conversations", "speak", "speaking", "spoken"})


def _the_language_the_chat_named(memory):
    """The language the person has already named in this chat, or "".

    A follow-up says the language once and then leans on it: "im learning spanish", "to speak to
    my wifes family", "how long until i can hold a conversation" is three lines about Spanish and
    only the first one names it. The figure said back as "Spanish, French or Italian" tells
    somebody who has already chosen a language nothing about their choice; the same figure for
    Spanish answers what they asked.
    """
    if not isinstance(memory, dict):
        return ""
    for turn in reversed((memory.get("turns") or [])[-6:]):
        said = str(turn.get("user") or "").lower() if isinstance(turn, dict) else ""
        named = _find(said, LANGUAGE_HOURS) if said else ""
        if named:
            return named
    return ""


def _language_hours(memory, understood):
    """How many hours a language takes, said in the language the person named."""
    clean = (understood.get("clean") or "").lower()
    named = _find(clean, LANGUAGE_HOURS) or _the_language_the_chat_named(memory)
    hours = LANGUAGE_HOURS.get(named or "", 600)
    where = named.capitalize() if named else "Spanish, French or Italian"
    years = max(2, round(hours / 365))
    return (f"About {hours} hours of real study to hold a proper conversation in {where} - around "
            f"{years} years at an hour a day, or three times that at twenty minutes a day, which "
            "is why a little every day beats a long weekend. A holiday and small talk come far "
            "sooner: about 100 hours, which a twice-weekly evening class reaches in a year.")



# "I keep forgetting to ring the dentist" reached the reading row on "forgetting" and "keep" and
# was told how to revise a chapter: the verb is the same but the thing forgotten is a job to do,
# and that has its own answer (a reminder written where the person already looks). So a line
# that forgets *to do* something stands the page row down unless the page is named in it.
_FORGET_TO_DO = re.compile(
    r"\bforget(?:s|ting)?\s+to\s+(?:ring|call|text|reply|post|book|pay|take|drink|eat|feed|walk|"
    r"charge|water|tidy|clean|put|send|bring|buy|collect|cancel|renew|order|email|message|"
    r"pick|do|go|get|check|ask|tell|remind|turn|lock|switch|defrost|batch|prep)\b")
_THE_PAGE = ("read", "reading", "book", "books", "chapter", "page", "pages", "textbook",
             "article", "paragraph", "notes", "revision", "revise", "study", "studying")

# "I can't remember the last time I went out" is about the year, not the page. The bare
# "cant remember" in the key above is there for "i cant remember what i read", and the two share
# every word of it: the line about the year was told to close the book and say the three points out
# loud, and the same thing happened to "i cant remember the last time i laughed", "...i slept
# well" and "...i did anything fun". What was forgotten there is not a page, so the time phrase is
# named and only a line that also names a page gets this answer.
_LAST_TIME = re.compile(
    r"\b(?:cant|dont|couldnt|doesnt|didnt|did not|do not|cannot)\s+remember\s+"
    r"(?:(?:the|a)\s+)?last\s+(?:time|night|day|week|month|year)\b")


# "how do i remember" is the question this row answers, and it names no page of its own.
_HOW_TO_REMEMBER = re.compile(
    r"\bhow\s+(?:can|do|should|would|could)?\s*(?:i|you|we|to)\s+(?:better\s+|best\s+)?"
    r"(?:remember|memorise|memorize|retain|take in)\b")


def _the_page_is_what_was_forgotten(understood):
    """True only when the line is about a page: a thing to do, or a life, is not a page.

    Every key in the row carries the bare "cant remember", so the row reached lines that name no
    page at all. "i cant remember the last time i went out" was told to close the book and say its
    three points out loud, and so were "...i laughed", "...i slept well", "i cant remember what i
    went upstairs for" and "i cant remember being this happy" - each one a line about a person's
    week, answered with revision technique. What is forgotten is named by the line, so the page
    has to be in it: "i cant remember what i read" keeps this answer, and a question asking how to
    remember keeps it too, because the key is the whole of that question.
    """
    reading = understood if isinstance(understood, dict) else {}
    text = " ".join(str(reading.get("clean") or reading.get("text") or "").lower().split())
    if any(word in text.split() for word in _THE_PAGE):
        return True
    if _HOW_TO_REMEMBER.search(text):
        return True
    if _LAST_TIME.search(text):
        return False
    # A job forgotten to be done is a thing to do, not a page: "i forgot to take the bin out".
    if _FORGET_TO_DO.search(text):
        return False
    return False


# "What is a 2:1" is a question about the class itself, and the `university-pass-mark` row answered
# it with the pass mark: "A degree passes at 40% in most UK universities...". That is the right
# answer to "what do I need to pass" and no answer at all to "what is a 2:1", which asks where the
# class sits - the band a graduate scheme or a master's course asks for. "What is the difference
# between a 2:1 and a 2:2" is the same gap asked with two names. So each class is one sentence,
# with the bands either side of it in it, and the pass mark stays in the same reply because it is
# the number the same person asks about next.
#
# The bands are the UK honours scale every university here uses. The master's awards are the same
# scale one level up, where the pass mark is 50 rather than 40, which is why they are worded apart
# from the honours degrees instead of being squashed into one list.
CLASS_BAND = {
    "first": 70,
    "2:1": 60,
    "2:2": 50,
    "third": 40,
}

CLASS_SAYS = {
    "first": (
        "a first is a first-class honours degree: a weighted average of 70% or more, the top "
        "class, and the one PhD funding usually asks for. Below it, a 2:1 is 60 to 69, a 2:2 is "
        "50 to 59, a third is 40 to 49, and a degree passes at 40% overall."),
    "2:1": (
        "a 2:1 is an upper second-class honours degree: a weighted average of 60 to 69%, the "
        "class most graduate schemes and master's courses ask for. Above it a first is 70% and "
        "up, below it a 2:2 is 50 to 59 and a third is 40 to 49, and a degree passes at 40% "
        "overall."),
    "2:2": (
        "a 2:2 is a lower second-class honours degree: a weighted average of 50 to 59%, one band "
        "below a 2:1 (60 to 69) and one above a third (40 to 49). A degree passes at 40% overall, "
        "and plenty of jobs and master's courses still take a 2:2."),
    "third": (
        "a third is a third-class honours degree: a weighted average of 40 to 49%, still honours "
        "but the lowest class, one band below a 2:2 (50 to 59). A degree passes at 40% overall."),
    "distinction": (
        "a distinction is the top award on a master's: an average of 70% or more, with a merit "
        "at 60 to 69 and a pass at 50 (a bachelor's degree passes at 40%)."),
    "merit": (
        "a merit is the middle award on a master's: an average of 60 to 69%, between a "
        "distinction (70 and up) and a pass at 50 (a bachelor's degree passes at 40%)."),
}

# A class is named by any of these, and the first two are the two ways a phone writes "2:1".
# "A first" alone is only a class when nothing else in the line makes it a year or an attempt:
# "my first year at uni" is not a question about the class, and it does not ask what one is.
CLASS_NAMES = (
    ("2:1", (r"\b2\s*:\s*1\b", r"\b2\.1\b", r"\b2\s1\b", r"\bupper second\b",
             r"\bupper-second\b")),
    ("2:2", (r"\b2\s*:\s*2\b", r"\b2\.2\b", r"\b2\s2\b", r"\blower second\b",
             r"\blower-second\b")),
    ("first", (r"\bfirst class\b", r"\bfirst-class\b", r"\b1st class\b")),
    ("third", (r"\bthird class\b", r"\bthird-class\b", r"\b3rd class\b")),
    ("distinction", (r"\bdistinction\b",)),
    ("merit", (r"\bmerit\b",)),
)
# A bare "a first" or "a third", with no year, term, attempt or choice beside it.
CLASS_ALONE = (
    ("first", re.compile(r"\b(?:a|the|my|get|got|need|want)\s+first\b")),
    ("third", re.compile(r"\b(?:a|the|my|get|got|need|want)\s+third\b")),
)
NOT_THE_CLASS = ("first year", "first term", "first attempt", "first time", "first day",
                 "first week", "first draft", "first choice", "first job", "first child",
                 "first baby", "first home", "first house", "first car", "third year",
                 "third term", "third attempt", "third time", "third week", "third child",
                 "third baby", "third party")


def _classes_named(clean):
    """The classes the line names, in the order they are written."""
    found = []
    for name, patterns in CLASS_NAMES:
        for pattern in patterns:
            match = re.search(pattern, clean)
            if match and name not in found:
                found.append((match.start(), name))
    if not found and not any(phrase in clean for phrase in NOT_THE_CLASS):
        for name, pattern in CLASS_ALONE:
            match = pattern.search(clean)
            if match and name not in found:
                found.append((match.start(), name))
    return [name for _, name in sorted(found)]


# "A low 2:1" is not the whole band: it is the half of it just above the line, and a person
# asking wants that number, because it is what a job advert or a course asks for by name.
HALF_OF_CLASS = (
    ("low", r"\blow\s+(?:2\s*:\s*1|2\.1|upper second)\b", "2:1", 60, 64),
    ("high", r"\bhigh\s+(?:2\s*:\s*1|2\.1|upper second)\b", "2:1", 65, 69),
    ("low", r"\blow\s+(?:2\s*:\s*2|2\.2|lower second)\b", "2:2", 50, 54),
    ("high", r"\bhigh\s+(?:2\s*:\s*2|2\.2|lower second)\b", "2:2", 55, 59),
)


def _half_of_class_said(clean):
    """The bottom or top half of a band, when the line asks for it by name."""
    for word, pattern, name, low, high in HALF_OF_CLASS:
        if re.search(pattern, clean):
            side = "bottom" if word == "low" else "top"
            return (f"A {word} {name} is the {side} of that band: a weighted average of "
                    f"{low} to {high}%, and it counts as a {name} on a certificate.")
    return ""


PASS_MARK = (
    "A degree passes at 40% in most UK universities (50% in Scotland, and 50% for a taught "
    "masters), and the class comes from your average, weighted by credits: 70% and up is a "
    "first, 60 to 69 a 2:1, 50 to 59 a 2:2 and 40 to 49 a third. Modules usually need 40% to "
    "count, a resit is often capped at the pass mark, and some courses need a pass in every "
    "year to carry credits forward, so check your course handbook.")


def _university_pass_mark(memory, understood):
    """What the class the line names is, or what a degree passes at when it names none.

    "How do i get a 2:1" is not this: it asks for a method, and the method is the study rows'
    answer, so a how-question keeps the pass-mark paragraph it had rather than being told what
    the class is worth.
    """
    understanding = understood or {}
    clean = str(understanding.get("clean") or "").lower()
    asks = tuple(understanding.get("asks") or ())
    classes = _classes_named(clean)
    if not classes:
        return PASS_MARK
    if "how" in asks or "steps" in asks:
        return PASS_MARK
    defines = ("definition" in asks or "compare" in asks
               or any(word in clean for word in
                      ("mean", "means", "stands for", "stand for", "difference between"))
               or any(word in clean for word in ("percentage", "percent", "what grade")))
    if not defines:
        return PASS_MARK
    half = _half_of_class_said(clean)
    if half:
        return "In UK universities, " + half[0].lower() + half[1:] + " " + "In full, " + CLASS_SAYS[classes[0]]
    said = "In UK universities, " + CLASS_SAYS[classes[0]]
    if len(classes) > 1:
        said += " " + CLASS_SAYS[classes[1]][0].upper() + CLASS_SAYS[classes[1]][1:]
        first, second = classes[0], classes[1]
        if first in CLASS_BAND and second in CLASS_BAND:
            gap = abs(CLASS_BAND[first] - CLASS_BAND[second])
            bands = "one band" if gap == 10 else f"{gap // 10} bands"
            said += (f" So the line between them is {gap} points of average, {bands}, and the "
                     "higher one is the class a course or a job asks for by name.")
    return said



ENTRIES = [
    # "do you think homework is a good idea" is an opinion question and nothing answered it: the
    # homework routine rows answer "how do I get him to do it", which is the next question, not
    # this one. The row gives both sides and then what to do about it.
    entry("homework-worth-it", (("homework", "home work", "homeworks"),
                                ("good idea", "a good idea", "worth it", "worthwhile", "useful",
                                 "point", "bad", "benefit", "help", "helps", "think", "opinion",
                                 "too much", "actually", "effective", "any good", "necessary",
                                 "good", "helps", "kids", "children"),
                                # the opinion said twice over is what beats the routine row on
                                # "is homework good for kids", which only shares the word good
                                ("good idea", "worth it", "worthwhile", "useful", "actually",
                                 "think", "opinion", "too much", "point", "benefit",
                                 "necessary", "effective", "any good", "helps")),
          "Homework earns its place in small doses: about ten minutes a night in the first years "
          "of primary, half an hour by the end of it and an hour or so at secondary, and the "
          "evidence for it is weakest for the youngest children. What makes it work is the same "
          "each night - a fixed time, a clear table, and you nearby without taking over. If it is "
          "regularly taking much longer than the school's own limit, or ending in tears, that is "
          "worth one short message to the teacher rather than a battle every evening.",
          # the word homework has to be in the line: the opinion words alone took "is a degree
          # still worth it" and "is 1500 a month too much for a mortgage" as well
          ask=("homework", "home work", "homeworks"),
          bias=1,
          # getting it done, a refusal and the maths or spelling in it are other rows' questions
          avoid=("how do i", "how to get", "get him to", "get her to", "get them to", "wont do",
                 "won t do", "refuses", "refusing", "refuse", "every night", "routine", "reward",
                 "chart", "sticker", "timetable", "times tables", "spelling", "maths", "english",
                 "revision", "revise", "exam", "concentrate", "focus", "adhd", "dyslex",
                 "teacher", "school said")),
    entry("past-papers",
          (("past paper", "past papers", "mock", "exam paper", "mark scheme"),
           ("how", "do", "use", "practice", "best", "worth", "marks", "when", "should", "start",
            "starting", "begin", "leave", "left", "soon", "many", "much", "often")),
          _past_papers_reply),
    entry("flashcards",
          (("flashcard", "flashcards", "anki", "quizlet"),
           ("how", "make", "use", "best", "worth", "many")),
          "One fact per card, question on one side, answer on the other, and no paragraphs: "
          "\"What year was the Battle of Hastings?\" not \"notes on 1066\". Review only the cards "
          "you get wrong, in short daily sessions, and make them yourself - writing them is half "
          "the memory work. Anki does the spacing for you if you prefer an app."),
    entry("mnemonics",
          (("mnemonic", "mnemonics", "memory trick", "remember a list"),
           ("how", "remember", "best", "use", "lists", "what", "whats", "mean", "meaning")),
          "Build a sentence from the first letters (Never Eat Shredded Wheat for the compass), "
          "or tie items to places on a walk round your house - the sillier the image, the better "
          "it sticks. Mnemonics are good for lists and orders, useless for understanding; use "
          "them for the facts you keep dropping."),

    # "how do i remember names" is a memory question with a technique, not a study one, and it was
    # going to the search hedge: the trick is to use the name in the first sentence and hang it on
    # something physical about the face.
    entry("remember-names",
          (("names", "name", "forget names", "remembering names", "forget peoples names"),
           ("remember", "remembering", "forget", "forgetting", "keep forgetting", "how", "best",
            "trick", "tip", "tips", "help", "never", "cant remember", "can't remember")),
          "Use the name out loud in the first minute - \"Nice to meet you, Sarah\" - and hang it on "
          "something physical: alliteration (Tall Tom), a rhyme, or a face feature. Repeating it "
          "twice early beats any trick later, and if it has gone, say so straight away: \"Sorry, "
          "your name's gone\" costs less than guessing.",
          ask=("remember", "remembering", "forget", "forgetting", "keep forgetting", "how", "best",
               "trick", "tip", "tips", "help", "never", "cant remember", "can't remember"),
          # the forgetting has to be the speaker's own: a relative whose names are going is the
          # memory-assessment question, not this trick.
          guard=lambda understood: not _somebody_else_forgets(understood),
          # A name on a form, a baby name and a name for a pet are not a memory question.
          avoid=("baby", "babies", "dog", "cat", "puppy", "kitten", "company", "business",
                 "domain", "website", "username", "password", "rename", "change my name",
                 "middle name", "surname", "spell my name", "write my name", "sign my name",
                 # a team wants a name to write on a sheet, which is the entertainment
                 # module's answer: "help us name our team" was reaching this memory card.
                 # A lost title is not a person's name: "i cant remember the name of that film"
                 # was answered here with "Use the name out loud in the first minute - 'Nice to
                 # meet you, Sarah'". The work noun is the reading, not the phrase "the name of",
                 # so "i cant remember the name of my new neighbour" stays this card's own.
                 "film", "films", "movie", "movies", "song", "songs", "tune", "book", "books",
                 "novel", "show", "series", "actor", "actress", "band", "album",
                 # The guard is the naming ask, not the noun. A bare "team" in this list
                 # stood the card down for "how do i remember the names of my team" and
                 # "remembering everyones names at the club", which are this card's own
                 # question with a group in them. These are the shapes that ask for a name.
                 "name our", "name the team", "name the quiz", "name the club",
                 "naming our", "team name", "team names", "quiz name", "quiz names",
                 "club name", "club names", "call our team", "call the team",
                 "call the quiz", "call our quiz", "call the club", "call our club",
                 "needs a name", "need a name", "name ideas", "name for our",
                 "names for our",
                 # "is forgetting names a sign of dementia" is asking about the illness, not for
                 # the trick: the memory-assessment card is the answer, and the technique for
                 # holding a new name is not.
                 "dementia", "alzheimers", "alzheimer's", "sign of", "symptom", "worried",
                 "worry", "should i be concerned", "is it normal")),
    entry("memorise-dates",
          (("dates", "timeline", "history"),
           ("remember", "memorise", "memorize", "learn", "keep forgetting")),
          "Put the dates on a blank timeline you draw yourself, and group them around a few "
          "anchor events you already know. Then link each new date to a story or a person rather "
          "than a bare number, and test yourself by covering the dates and filling them in. Ten "
          "dates you can place beat fifty you half-remember.",
          # "our dates" is the anniversary, not the Tudor kings: a partner's forgetfulness has
          # its own answer, and this card has never had an avoid list to say so.
          avoid=("my wife", "my husband", "my partner", "our dates", "our anniversary",
                 "our plans", "marriage")),
    entry("fraction-meaning",
          (("fraction", "fractions", "numerator", "denominator", "decimal"),
           ("what", "whats", "mean", "meaning", "definition", "is a", "are")),
          "A fraction is a part of a whole written as one number over another: the bottom says "
          "how many equal pieces the whole is cut into and the top says how many of those you "
          "have, so 3/4 is three pieces out of four. The one thing that trips people up is that "
          "the same amount has lots of names - 2/4 is 1/2, and 0.5 is 1/2 too - which is why you "
          "can simplify and compare them by putting them over the same bottom number.",
          # "what fraction of an hour is 20 minutes" and "20 minutes as a fraction of an hour" are
          # sums, not the definition: a fraction of a named thing is answered with the number
          # (units.py works the span out), and only the bare "what is a fraction" is this row.
          avoid=("minutes", "seconds", "as a fraction", "in a fraction", "out of", "of my",
                 "of the", "fraction of an hour is", "fraction of a day is",
                 "fraction of a week is", "fraction of a minute is"),
          bias=1),
    entry("fractions-explain",
          (("fraction", "fractions", "numerator", "denominator"),
           ("explain", "simple", "simply", "struggling", "understand", "child", "son", "daughter",
            "kid", "teach", "help")),
          "Start with something they can eat: cut an apple into four, take one piece - that is "
          "one quarter. Then show that the bottom number is how many pieces the whole was cut "
          "into and the top is how many you have. Do halves, quarters and thirds with real "
          "objects before any writing, then move to drawing them as bars of chocolate.",
          bias=1),
    entry("times-tables",
          (("times tables", "times table", "multiplication", "times by", "6 times 7"),
           ("learn", "memorise", "remember", "how", "help", "child", "quick")),
          "Do them out loud, in order, then shuffled, in two-minute bursts a few times a day - "
          "short and often beats long and rare. Learn the easy ones first (2s, 5s, 10s, then the "
          "squares) so more than half the table is familiar. The hard ones are 6x7, 7x8, 8x9; "
          "make up a silly rhyme for just those.",
          # "how do i help my son with his times tables" is the maths, not the homework routine
          bias=1),
    # A sum that comes out as a decimal was getting the long-division tutorial, because "how" in
    # the second half was enough: this entry is the method, so it wants a method word now.
    entry("long-division",
          (("long division", "division", "divide", "dividing",
            # the method's other names: a parent asks for "short division", for the bus stop it is
            # taught as, or what a remainder is, and none of those says the word "long"
            "short division", "bus stop method", "bus stop", "remainder", "remainders"),
           ("explain", "teach", "simple", "simply", "method", "child", "year old", "works",
            "stuck", "remember", "steps", "step by step", "by hand", "without a calculator",
            "show me", "work out", "help",
            # "how do i do long division" carries no method word at all: the phrase alone is
            # three points and the entry wants four, so the plainest way of asking was a shrug.
            # Only the phrase, though, never the bare verb: "do" and "do i" also carry
            # "how do i divide 3 by 8", and a sum that comes out as a decimal is not this entry.
            "do long division", "long division method", "learn", "homework", "practice",
            "practise",
            # The other names of the method carry no method word of their own: "how do i do short
            # division", "what is a remainder" and "how do i divide a big number by a small one"
            # were all a shrug. The phrases rather than the bare verbs, so a sum that comes out
            # as a decimal ("how do i divide 3 by 8") is not this entry - `avoid` below says so
            # twice, on the word and on the phrase.
            "how do i do", "how do you do", "how to do", "what is", "whats", "mean",
            "meaning", "big number", "big numbers")),
          "Long division is the same four steps over and over: divide, multiply, subtract, bring "
          "down. Take 492 divided by 4: 4 goes into 4 once (write 1), 1 x 4 = 4, subtract to get 0, "
          "bring down the 9. 4 into 9 goes twice (write 2), 2 x 4 = 8, 9 - 8 = 1, bring down the 2 "
          "to make 12. 4 into 12 is 3, so the answer is 123. Say each step out loud the first few "
          "times, and use real objects for the first example so the place value makes sense.",
          # splitting a bill, a pizza or the chores is the same verb about something else
          avoid=("decimal", "decimals", "3 by 8", "as a decimal", "two decimal places",
                 "bill", "bills", "chores", "pizza", "taxi", "rent", "custody", "excel",
                 "spreadsheet", "formula", "assets", "inheritance", "profits", "bonus",
                 "holiday", "money between", "between us", "dividing up")),
    # The four things people do to fractions, in the order they get stuck on them. The key is the
    # operation plus the word "fraction", so a meaning question ("what is a fraction") still goes
    # to fraction-meaning and a fraction-to-decimal goes to its own entry: nothing here answers a
    # line that does not name both the operation and the fraction.
    entry("fractions-sums",
          (("fraction", "fractions"),
           ("multiply", "multiplying", "multiplied", "times", "divide", "dividing",
            "divided", "add", "adding", "subtract", "subtracting", "plus", "minus",
            "common denominator", "same denominator", "simplify", "cancel down")),
          _fractions_reply,
          avoid=("decimal", "decimals", "percent", "percentage", "percentages", "what is a",
                 "whats a", "mean"),
          bias=1),
    entry("maths-word-problems",
          (("word problem", "word problems", "maths problem", "maths question"),
           ("solve", "how", "stuck", "approach", "help", "cant")),
          "Underline what the question actually asks, then write down the numbers it gives you "
          "and what units they are in. Guess the answer roughly before calculating - if your "
          "working is far off the guess, the sum is wrong, not the guess. Draw it if there is "
          "any shape, distance or time in it."),
    # The reply names a volcano, so the line has to. "science project", "school project" and a
    # bare "model" were in the key with "solar system", which made this the answer to every
    # model to build: "my son has a project about the solar system" and "how do i build a model
    # of a bridge for school" both got the bottle in a cone, and `family.school-project` - the
    # shrink-it-to-a-page advice the other subjects get - did not reach the candidates at all
    # (the red in tests.test_knowledge_family). The build shapes stay in the second half, where
    # they score, and the volcano word is what decides the row.
    entry("science-project-build",
          (("volcano", "volcanoes", "model volcano", "volcano model"),
           ("build", "make", "model", "ideas", "school", "project", "science project",
            "school project", "kids", "child", "daughter", "son", "erupt", "erupts",
            "eruption", "explain", "why", "how")),
          "For a volcano: a bottle in a cone of foil and clay, then bicarbonate of soda with "
          "vinegar and a little washing-up liquid for the eruption (red food colouring helps). "
          "The part that earns marks is the write-up: label the bottle as the magma chamber, and "
          "explain that the gas is what pushes it out. It takes an afternoon and a tray.",
          avoid=("timeline", "gantt", "project plan", "deadline", "schedule", "sprint", "client",
                 "stakeholder", "at work", "for work", "milestone", "roadmap",
                 # "what makes a volcano erupt" is the geology, not the craft: the row keys
                 # volcano with "erupt", "why" and "how" too, so the question about the real one
                 # was answered with the bottle in a cone. A line that names a build, a model or
                 # a project is still this row's.
                 # the phrases, not the stems: a bare "makes" matches "make" through the plural
                 # form, which took "how do i make a volcano" away from the very row it needs
                 "what makes", "what causes", "which makes", "that makes", "causes it",
                 "the cause", "the reason")),
    entry("spelling-test",
          (("spelling test", "spelling bee", "spellings", "spelling list", "weekly spellings",
            # "my child cant spell" and "my son is bad at spelling" name the trouble, not a
            # list, and reached the chat echo ("What has your child said about it?").
            "cant spell", "can't spell", "cannot spell", "bad at spelling", "struggles to spell",
            "struggle to spell", "spelling"),
           ("daughter", "son", "child", "kid", "kids", "practise", "practice", "help", "how",
            "ready", "test", "school", "ten words", "prepare")),
          "Five words a night, not the whole list: look at the word, say it, cover it, write it, "
          "then check it, and put the ones she gets wrong to the back of the queue. Say the word "
          "in a sentence as you test her, because a spelling she can only write in a list is not "
          "learnt yet. Ten minutes is enough, and the night before is for the five she keeps "
          "missing, not for the twenty she knows.",
          # "how do i improve my spelling" and "how do you spell X" belong to wording.py
          avoid=("how do you spell", "how do i spell", "how to spell", "spell the word",
                 "spell it", "spelling of", "improve", "improving"),
          # family.kids-homework lists "spelling test" in its key and would answer with the
          # homework routine; for a school spelling list the words are the point
          bias=2),
    entry("essay-plan",
          (("essay", "coursework", "assignment"),
           ("plan", "start", "stuck", "blank", "deadline", "how", "write", "writing")
           + HOW_ASK),
          "Make the plan first and write the essay from it: list three or four points that answer "
          "the question, put one piece of evidence under each, and put them in the order that "
          "makes the argument grow. Then write the body paragraphs first and the introduction "
          "last, when you know what you argued. Two hours of planning saves a day of staring.",
          # checking an essay for mistakes is proofreading, and that entry answers it
          avoid=("mistakes", "mistake", "grammar", "spell", "spelling", "proofread", "typo",
                 "typos", "check", "unclear", "structure of the sentence")),
    entry("proofread-help",
          (("spell check", "spellcheck", "proofread", "proof read", "check this email",
            "check my email", "check this essay", "check my essay", "check my cv"),
           ("can", "could", "you", "please", "how", "help", "this", "my")),
          "I cannot read it for you, but the check that catches most of it is reading it aloud: "
          "your ear stops on the missing word and the doubled one. Then look at four things in "
          "order - the name at the top, the ask in the first line, any number or date, and the "
          "last line. Shorten any sentence you have to read twice, and leave it for ten minutes "
          "before the last read if you can.",
          # main's essay-check already answers "how do i proofread an essay"
          avoid=("essay", "essays", "dissertation", "coursework", "assignment", "thesis")),
    entry("reading-comprehension",
          (("comprehension", "reading", "passage"),
           ("understand", "answer", "questions", "help", "improve", "exam", "better",
            "get better", "struggling", "weakest")),
          "Read the questions before the passage, so you know what to look for. Then read once "
          "for sense and go back to the lines the questions point at, quoting a few words in your "
          "answer. For \"why\" questions, answer with because plus something from the text; for "
          "\"how do you know\", quote it.",
          # a parent helping a child to read is not doing an exam paper
          avoid=("my son", "my daughter", "my kid", "my child", "bedtime", "learn to read",
                 "read to me", "reading age", "phonics", "sounding out",
                 # "how do i learn to read music" is a music question: "learn to read" is part of
                 # this row's key, so the music words have to stand it down
                 "music", "sheet music", "sight read", "sight-read", "sight reading")),
    entry("reading-with-a-child", (("reading", "read", "books", "phonics"),
                                   ("my son", "my daughter", "my kid", "my child", "bedtime",
                                    "learn to read", "reading age", "every night", "refuses",
                                    "reluctant", "help him", "help her",
                                    # "does a comic count as reading", "would audio books count
                                    # as reading": the ask is whether a medium counts, and it
                                    # names no child. Only the ask goes in the key: the medium
                                    # words were in it too, and then any line that named a comic
                                    # was a parent's question about reading practice - "i read
                                    # comics" was answered "Ten minutes a night, the same time,
                                    # with them reading out loud to you" (found on `0231e351`).
                                    # The count-as row below carries the medium words, and it is
                                    # the row that answers what was asked. What is left here is the
                                    # *practice* ask, so "is a comic ok for reading practice" still
                                    # reaches the practice card without every line that names a
                                    # comic landing on it.
                                    "count as reading", "counts as reading", "count as a book",
                                    "reading practice", "reading practise", "ok for reading",
                                    "good for reading", "for reading practice")),
          "Ten minutes a night, the same time, with them reading out loud to you: stop at the "
          "first hard word, sound it out together, and let them finish the sentence. Read the "
          "same short book twice, because the second read is where the confidence comes from, "
          "and keep a book in the car or bag for dead time. Ask one question about the story "
          "afterwards rather than testing words.",
          # The answer is a child's lesson, and an adult's own reading habit reached it through
          # "every night": "i read in bed every night and my eyes hurt" was told to have them
          # read out loud to you. The eyes and the person's own bed are what stand it down; the
          # rest of the row is left as it was, because a parent's line ("we read every night
          # but he refuses") needs it. And "how do i learn to read music" is a music question:
          # "learn to read" is one of this row's key parts, so the music words stand it down too.
          avoid=("my eyes", "eyes hurt", "eyes ache", "eyes are sore", "eye strain", "eyestrain",
                 "in bed", "my eyesight", "tired eyes", "sore eyes",
                 "music", "sheet music", "sight read", "sight-read", "sight reading",
                 "notation", "an instrument", "piano", "guitar", "violin")),
    # "would a comic count as reading", "do audio books count as reading": a yes/no ask about a
    # medium, which the entry above answers with the ten-minutes-a-night practice instead of
    # answering at all. It has to name the medium and the count-as ask, so it never takes a plain
    # "help my son read" or a "recommend a funny comic".
    entry("a-comic-counts-as-reading",
          (("count as reading", "counts as reading", "count as a book", "count as books",
            "still reading", "proper reading"),
           ("comic", "comics", "comic book", "comic books", "graphic novel", "graphic novels",
            "manga", "audio book", "audio books", "audiobook", "audiobooks", "magazine",
            "magazines", "picture book", "picture books", "kindle", "e-reader", "ereader")),
          "Yes, it counts. Comics, graphic novels, magazines and audio books all build the same "
          "thing a book does - the habit and the vocabulary - and a child who reads what they like "
          "reads far more of it than one handed a book they do not. Keep one chapter book alongside "
          "it rather than banning the comics, and ask what happened in the story afterwards. For "
          "audio books, same idea: the words go in by ear, and a paper copy of the same book helps "
          "once they can follow along.",
          bias=1),
    entry("study-breaks",
          (("pomodoro", "study breaks", "study break", "how long should i study", "how long to study",
            "breaks when studying"),
           # "what is the pomodoro technique" names no length and no study verb beyond the word
           # itself, so the method's own name carries the question words too.
           ("how", "long", "often", "best", "study", "studying", "revision", "technique",
            "method", "mean", "work")),
          "25 minutes on, 5 off, and a longer break every four blocks: the short block keeps "
          "quality up, the break is what makes it repeatable. In the break, stand up and move "
          "rather than scrolling, because a phone break turns five minutes into twenty. Stop "
          "while it is still going well, so tomorrow is easier to start.",
          # "how long should i study for" is main's study-how-long; a pomodoro rhythm is this
          # answer, and a flat pack's instructions are a manual, not revision
          avoid=("instructions", "assembling", "manual", "recipe", "flat pack", "flatpack",
                 "how long should i study", "how long should i revise", "how many hours"),
          bias=1),
    entry("study-with-adhd",
          (("adhd", "attention deficit"),
           ("study", "revise", "focus", "concentrate", "help", "tips")),
          "Make the task visible and small: one page, one timer, everything else out of the room. "
          "Body-doubling works for a lot of people - study alongside someone, in person or on a "
          "video call with mics off. Move between two or three subjects rather than forcing one, "
          "and use a paper checklist you tick, because visible progress is the fuel."),
    entry("motivation-to-study",
          (("motivation", "motivated", "pointless", "cant be bothered", "no point"),
           ("study", "revise", "school", "exam", "how", "help", "why")),
          "Motivation follows action, not the other way round: do ten minutes and decide after. "
          "Pick the subject you least dread but find easiest to start with, because a bad day is "
          "about getting one thing done, not all of it. If it has felt pointless for weeks, tell "
          "someone at school or work; that is a different problem from laziness."),
    entry("learn-to-the-test",
          (("learn", "memorise"),
           ("fast", "quickly", "overnight", "in a day", "last minute", "exam")),
          "Last-minute learning works for facts and structures, not skills: take the syllabus or "
          "mark scheme, list what is actually examinable, and learn the highest-mark items with "
          "self-testing. Sleep before the exam and skip the things you already know. Be honest "
          "with yourself - this buys a pass, not understanding.",
          # "how do i learn the job quickly" was this row: a syllabus and a mark scheme are
          # school, and there is no exam in a new job. The job words stand this row down.
          avoid=LANGUAGE_LEARNING + ("the job", "my job", "new job", "the role", "my role",
                                     "at work", "on the job", "job quickly", "the ropes",
                                     "ropes", "up to speed")),
    # "how do i stop cramming" was a shrug: the night-before row needs an exam in the line and
    # the timetable rows need "timetable", so the habit itself had nothing behind it. The week
    # is what this one is for - it says what to do with the days you still have - and the exam
    # tomorrow is handed on to the night-before rule in the last sentence, because that is a
    # different answer and the person still gets it.
    entry("stop-cramming",
          (("cram", "cramming", "crammed", "all nighter", "all-nighter", "all-nighters",
            "last minute revision", "last-minute revision", "leave it to the last minute",
            "leaving it late", "leaving everything", "leaving revision"),
           ("stop", "stops", "how", "help", "tips", "avoid", "not", "always", "every",
            "why", "end up", "keep")),
          "Make the first session tiny and today: open the topic list, pick the one you know "
          "least, and test yourself on it for ten minutes, because starting is the part that is "
          "failing rather than the studying. Then put three short sessions in the week you "
          "actually have, each ending with a self-test instead of a reread, and give each one a "
          "stopping time so it cannot drift to midnight. Testing yourself is what makes the last "
          "day calm instead of terrible; if the exam is tomorrow, pack the bag, read your "
          "one-page summary once, and sleep.",
          avoid=("no sleep", "bad sleep")),
    # "how do i practise a presentation" and "how do i rehearse a speech" got "I don't know
    # enough to answer that honestly": `school-presentation` needs a school word, the work row
    # keys nerves, and rehearsal itself - saying it out loud, to the clock - had nothing.
    entry("practise-a-talk",
          (("practise", "practice", "practising", "practicing", "rehearse", "rehearsal",
            "rehearsing", "run through", "run it through", "go through it out loud"),
           ("presentation", "talk", "speech", "pitch", "slides", "audience", "wedding",
            "best man", "bride", "groom", "interview", "assembly", "meeting", "conference")),
          "Say it out loud three times, standing up, with the slides in front of you: the first "
          "run finds the sentences that only looked fine on paper, the second is against a timer, "
          "and the third is to one person who will tell you where they lost the thread. Time it "
          "against the slot you were given and cut material rather than speed up. Write the "
          "opening sentence and the closing one out in full and keep everything between them to a "
          "few words per card, then practise stopping for a second after your last point instead "
          "of trailing off.",
          bias=1),
    entry("group-project",
          # "how do i work in a group in class" and "how do i work well in a group" are the same
          # question as "group work at school", and with the class words taken back out of the
          # ask-teacher row it was falling to a shrug.
          (("group project", "group work", "team project", "presentation with", "work in a group",
            "work well in a group", "work as a group", "group of us", "work with a group"),
           ("how", "help", "lazy", "fair", "split", "work", "handle")),
          "At the first meeting, split the work in writing with names and dates, and pick one "
          "person to hold the whole thing together. Swap drafts before the deadline so no one is "
          "the bottleneck. If someone does nothing, tell them early what you need by when; "
          "chasing at the end is where the resentment comes from."),
    entry("teach-someone",
          (("explain it to someone", "teach someone", "teach it to someone", "teaching someone",
            "feynman"),
           ("how", "best way to learn", "understand", "check", "learn")),
          "Explain it out loud to someone who does not know it, without notes. Where you stumble "
          "or reach for jargon is exactly what you do not understand yet, so go back to that bit "
          "and try again. Ten minutes of teaching yourself in the mirror is worth an hour of "
          "rereading."),
    # --- what a grade is worth ---------------------------------------------
    # "I got a grade 4, is that bad" wants the number explained, not Clearing: the same
    # words that reach the results-day entry reach this one, so it is keyed on the number
    # or the judgement (bad, good, mean, pass) rather than on "results".
    entry("grade-meaning", (("grade", "grades", "gcse", "gcses", "a level", "a-level",
                            "alevel", "alevels", "marks", "score"),
                           ("1", "2", "3", "4", "5", "6", "7", "8", "9", "bad", "good",
                            "mean", "pass", "passed", "average", "standard", "decent",
                            "changed", "compare")),
          _grade_answer, avoid=NOT_AN_EXAM + MOCK + (
                                                     # "score" is a credit word too: "my credit
                                                     # score changed" was a GCSE grade answer. The
                                                     # credit row owns its own score.
                                                     "credit score", "credit rating", "credit file",
                                                     "credit report", "credit history",
                                                     "piano", "guitar", "violin", "ballet",
                                                     "dance", "swimming", "abrsm", "trinity",
                                                     "instrument", "music", "singing", "choir",
                                                     "theory test", "driving test",
                                                     # a club has a grade too: "my football team
                                                     # is in grade 4" is not a GCSE result.
                                                     "football", "rugby", "netball", "cricket",
                                                     "hockey", "team", "league", "club",
                                                     "martial arts", "karate", "judo"), bias=2),
    entry("mock-grade", (MOCK,
                         ("1", "2", "3", "4", "5", "6", "7", "8", "9", "grade", "grades",
                          "bad", "good", "mean", "worried", "worry", "failed", "gutted",
                          "matter", "count", "what should")),
          _mock_answer, avoid=NOT_AN_EXAM, bias=2),
    entry("revision-start", (("revising", "revise", "revision", "exam", "exams", "test", "mocks",
                              "mock"),
                             ("putting off", "procrastinat", "get started", "started", "start",
                              "begin", "behind", "timetable", "schedule", "overwhelmed",
                              "how", "tips", "advice", "best", "help", "should", "weeks",
                              "soon", "coming",
                              # "whats a good way to prepare for an exam" named no work in
                              # hand, so the where-do-i-start row never saw it: preparing is the
                              # same question asked before the panic rather than during it.
                              "prepare", "preparing", "prep", "get ready",
                              # A date and no work done is the same question as "where do I
                              # start": "my exam is on friday and i havent revised" was filed
                              # away ("Noted: your exam is on friday and you haven't revised")
                              # because none of the words above are in it. The days are the ones
                              # people actually say when the exam is close.
                              # The bare days are not here on purpose: "my exam is tomorrow" is
                              # the night-before answer and "and i am nervous" is the nerves one,
                              # and both were lost when the date alone was enough. What counts
                              # is the line saying the work has not been done.
                              "havent revised", "havent started", "havent done", "havent begun",
                              "not revised", "not started", "not begun", "no revision",
                              "done nothing", "nothing yet", "done none", "havent touched",
                              "havent opened", "left it", "left everything", "not done any",
                              "in two days", "in 2 days", "in three days", "in 3 days",
                              "in a few days", "days time", "days left", "run out of time",
                              "no time")),
          _unless_testing_a_thing(
              "Start with something tiny today: open the past paper or the topic list and write "
              "down what you already know about one topic — ten minutes, that is the whole job. "
              "Then work backwards from the exam date and give each topic a day, in 25-minute "
              "blocks with a 5-minute break. The last week should be past papers under time, not "
              "reading notes."),
          # "I keep falling asleep revising" is a sleep question, not a timetable one.
          # "what time of day should i revise" is not "where do I start": the line names a time,
          # that is `study-time-of-day`'s question, so this row stands down on the time words.
          avoid=NOT_AN_EXAM + NOT_REVISION + ASLEEP + REST_ASK
          + ("time of day", "what time", "best time", "better time", "when is the best",
             # which time of day to revise is `study-time-of-day`'s question, and it is written
             # with "or" between the two times: "should i revise at night or in the morning" was
             # this row's plan.
             "at night or", "or in the morning", "or in the evening", "in the morning or",
             "morning or night", "night or morning", "evening or morning", "morning or evening")
          + NOT_A_START_OF_EXAMS,
          bias=1),
    # "make revision notes" names the notes in the middle, and the reading entry grew the word
    # "notes" too, so the phrase has to be the key here.
    entry("revision-active", (("revising", "revise", "revision", "studying", "study",
                               "revision notes", "make revision notes", "revision methods",
                               "revision techniques"),
                              ("remember", "sticks", "stays", "stuck", "head", "brain",
                               "memory", "memorise", "memorize", "reread", "rereading",
                               "notes", "method", "technique", "effective", "how", "tips",
                               "best", "help") + HOW_ASK),
          "Testing yourself is what makes things stick; rereading notes mostly feels productive "
          "without being so. Turn each topic into five questions and answer them with the book "
          "shut, then check, and redo the ones you got wrong tomorrow and again in a week. "
          "Reread only the bits you could not answer.",
          # "what is the best time of day to study" names a time, and this row read "best" as
          # "the best way" and answered with testing yourself. A line that asks which time is
          # `study-time-of-day`'s, so this one stands down on the time words.
          # A line that names a subject is that subject's question: "the best way to revise gcse
          # maths" wants working problems, not the general testing-yourself method, and with
          # HOW_ASK this row tied with `revision-maths` and won on file order.
          avoid=NOT_AN_EXAM + NOT_REVISION + ASLEEP + REST_ASK + A_SUBJECT
          + ("time of day", "best time", "better time", "what time", "when is the best")
          + NOT_A_START_OF_EXAMS, bias=1),
    # "what is active recall" and "what is spaced repetition" were both "I don't know enough to
    # answer that honestly", and the row that describes the method already existed - but putting
    # the names in its key and "what"/"is" in its second half pulled "is it better to revise in
    # the morning or at night" away from the time-of-day answer. So the names get a row of their
    # own, and its first half is nothing but the names: a line can only reach it by naming the
    # method, which is what makes it safe next to a row keyed on the word "how".
    entry("revision-method-names", (("active recall", "spaced repetition", "spaced practice",
                                     "retrieval practice", "testing yourself", "interleaving",
                                     "blurting", "leitner"),
                                    ("what", "whats", "mean", "means", "is", "explain", "about",
                                     "definition", "define", "work", "does", "do")),
          "Testing yourself is what makes things stick; rereading notes mostly feels productive "
          "without being so. Turn each topic into five questions and answer them with the book "
          "shut, then check, and redo the ones you got wrong tomorrow and again in a week. "
          "Reread only the bits you could not answer.",
          bias=1),
    entry("study-time-of-day", (("study", "studying", "revise", "revising", "revision"),
                                 ("morning", "night", "evening", "time of day", "better time",
                                  # "whats the best time to revise" and "best time to study for
                                  # exams" put `best time to` in front of the verb instead of
                                  # `is it better to`, so the row stood the revision-plan answer
                                  # down and then failed its own gate: the person got a hedge from
                                  # both. The phrase, not the bare `when`, is what is missing.
                                  "best time", "best time to", "best time of day", "good time",
                                  "right time", "when in the day", "what time of day",
                                  "what time", "which time", "what hour",
                                  "when")),
          "The time you will actually do it beats the perfect time, and for anything that needs "
          "concentration most people are sharper in the morning. Hard topics first, drilling and "
          "past papers later, and keep the last half hour before bed off screens if you can. If "
          "you are a night owl and it works, do not fight it — just do it at the same time each day.",
          avoid=NOT_AN_EXAM + ASLEEP + ("shift", "shifts", "rota", "work nights",
                                        "night shift")),
    # "how do i write a lab report" and "how do i write up a science experiment" were both
    # "I don't know enough to answer that honestly". The bare word "report" is not in the key on
    # purpose: a book report, a school report and a report for work are other jobs, and the
    # commonest false friend of all is the practical driving test.
    entry("vocab-test", (("vocabulary", "vocab", "words"),
                         ("remember", "learn", "memorise", "memorize", "test", "language",
                          "french", "spanish", "german", "italian")),
          "Learn seven to ten words at a time, out loud, and test yourself instead of reading the "
          "list: cover the English side and say the word, then swap. Put each new word in a short "
          "sentence you would actually say, and go back over yesterday's words for two minutes "
          "before adding new ones — spacing is what makes them stay.",
          # "my mum cant remember words" is somebody else's memory going, not a language drill
          guard=lambda understood: not _somebody_else_forgets(understood),
          avoid=NOT_AN_EXAM + ASLEEP, bias=1),
    entry("exam-night-before", (("exam", "exams", "test"),
                                ("night before", "tomorrow", "cram", "cramming", "evening",
                                 "sleep", "bedtime")),
          "Sleep is worth more than the extra hours of cramming: a rested brain recalls what you "
          "already know, a tired one does not. Pack your bag and the pens you need, read your "
          "one-page summary once, then stop by nine and do something that is not revision. If you "
          "really cannot settle, write down the three things you are worried about forgetting.",
          avoid=NOT_AN_EXAM, bias=1),
    entry("exam-nerves", (("exam", "exams", "test"),
                          ("nervous", "nerves", "nerve", "panic", "panicking", "blank", "anxious",
                           "freeze", "freaking", "scared", "stress", "stressed", "dread",
                           "dreading", "worried",
                           # how most people say it: the body, not the word "nerves"
                           *NERVES_BODY)),
          _exam_nerves,
          # "how do i deal with exam stress" tied revision-start, so the person panicking got the
          # timetable talk. Same score on the line, and this is the one that answers it.
          bias=1,
          avoid=NOT_AN_EXAM),
    # "what should i eat before an exam" got the start-today answer, and "what should i have for
    # breakfast on exam day" got a recipe: nothing in the knowledge base owned a plain food
    # question about the morning of an exam. It is a study question rather than a cooking one -
    # the answer is about the paper, not the plate - and the blood-test and driving-test words
    # in NOT_AN_EXAM keep it off the medical and practical-test lines.
    entry("exam-day-food", (("exam", "exams", "test", "tests", "mock", "mocks",
                            "exam day", "exam morning"),
                           ("eat", "eating", "ate", "food", "breakfast", "lunch", "drink",
                            "drinking", "water", "snack", "snacks", "coffee", "caffeine",
                            "hungry", "sugary", "energy drink")),
          "Something slow and ordinary an hour or two before, with water: porridge, toast and egg, "
          "or cereal and a banana. A sugary breakfast spikes and drops you by the second hour, "
          "which is exactly when the paper gets hard, so keep the sweet thing for the break. Take "
          "a bottle of water and a plain snack in, and if the exam is in the afternoon eat a light "
          "lunch rather than a big one - a full stomach is what makes people sleepy at 2pm. Keep the "
          "coffee you usually drink and nothing more: a double espresso you never have "
          "is what sends people to the loo twice in the first half hour.",
          # "can i bring water into the exam" is a school-rules question, and this row cannot
          # answer what a particular school allows, so it stands aside rather than guess.
          avoid=NOT_AN_EXAM
          + ("blood", "diabetes", "diabetic", "my diet", "lose weight", "thinking of food",
             "overeating", "appetite", "nausea", "sick", "vomit", "allergic", "allergy",
             "bring water", "take water", "into the exam", "into an exam", "allowed in",
             "bring in", "take in"),
          # revision-start keys the bare ask words ("should", "how", "best", "tips"), so
          # "what should i eat before an exam" tied with it on the exam and the ask, and lost the
          # food to the timetable. A line that names food and an exam is this row's, so it ranks
          # above the row that only matched the ask.
          bias=2),
    entry("essay-opening", ("essay", ("opening", "first sentence", "first line", "introduction",
                                      "start", "begin", "sentence", "hook")),
          "Answer the question in your first sentence, plainly, and let the rest of the essay back "
          "it up: \"Prisons in the 1800s did more to hide poverty than to fix it.\" No \"In this "
          "essay I will discuss\" and no dictionary definition — a marker wants to see your answer "
          "straight away.",
          avoid=NOT_AN_EXAM, bias=2),
    # "plan" is not a word of this row's: it is essay-plan's, and a line that asks how to plan
    # an essay was reaching both. bias settles the rest - a line that names the structure of an
    # essay wants the paragraph answer, while essay-plan's second group carries "how" for every
    # "how do i write my essay" and ties with it.
    entry("essay-structure", ("essay", ("structure", "paragraph", "paragraphs", "conclusion",
                                        "argue", "argument", "organise", "organize")),
          "One idea per paragraph: a sentence that says what it argues, the evidence for it, then a "
          "line saying why that matters to the question. Your conclusion should answer the "
          "question as asked, not repeat the introduction. If you are stuck, write the paragraphs' "
          "first sentences as a list first and check they add up to an argument.",
          avoid=NOT_AN_EXAM, bias=1),
    entry("essay-check", ("essay", ("proofread", "check", "mistakes", "shorter", "word count",
                                    "edit", "cut", "improve")),
          "Read it out loud, or have your computer read it aloud: the places you stumble are the "
          "places to fix. Cut every \"very\", \"really\" and \"basically\", make sure each "
          "paragraph's first sentence says its point, and check names, dates and quotes — those "
          "are what get marked down.",
          avoid=NOT_AN_EXAM),
    # keyed on the singular "note": lookup._forms("notes") includes "not", which would make
    # "I'm not sure" look like a line about notes
    entry("notes-lecture", (("note", "note-taking", "notetaking", "notes from"),
                            # A book or a chapter is the same job as a lecture, and the row read
                            # only the classroom words: "how do i take notes from a book" went to
                            # the football card, which keys "booked" and matches the front of
                            # "book". With the book named here the row fits the line as well as
                            # that one does, and bias is the tie it wins.
                            ("lecture", "lectures", "class", "lesson", "better", "take", "taking",
                             "handwriting", "laptop", "book", "books", "textbook", "textbooks",
                             "chapter", "chapters", "reading", "seminar",
                             # "how do i write good notes" was a search shrug: the row asked for
                             # a lecture, a class or the word "better", and the line says "write"
                             # and "good". Both are the note-taking question and neither can pull
                             # another row in, because this key already names notes.
                             "write", "writing", "good", "good notes")),
          "Write in your own words, in short lines, and do not try to transcribe: you are making a "
          "map to come back to, not a transcript. Leave a wide margin for questions after the "
          "lesson and add them the same evening, in five minutes, while it is still fresh. "
          "Handwriting beats typing for remembering, if it is a choice.",
          avoid=NOT_AN_EXAM + NOT_A_PERSONS_NOTE, bias=1),
    # The subject of this entry is focus itself, so the key names only words of attention: the
    # phone distraction has its own entry in routines.py, and listing "phone" here as well made
    # this one fire on "i cant hear on my phone" as soon as the line carried a second generic word.
    entry("study-distracted", (("focus", "focusing", "concentrate", "concentrating",
                                "concentrated", "distracted", "distraction", "concentration",
                                "mind wanders", "wanders", "zone out", "zoning out",
                                "lose track"),
                               # The first group is the whole subject, so the second one only has to
                               # say that the line is about getting on with something - it is not a
                               # list of study words. "how do i concentrate better" names no book,
                               # desk or revision and used to get a shrug, and so did "i cant focus
                               # at work", which is the same question asked by somebody in a job.
                               ("study", "studying", "revising", "revision", "homework", "sit down",
                                "end up", "tiktok", "youtube", "better", "worse", "work",
                                "office", "job", "desk", "task", "tasks", "mind", "wanders",
                                "keep losing", "losing track", "get on with", "get anything",
                                "get distracted", "cant", "can t", "read", "reading", "book",
                                "books", "meeting", "meetings", "conversation")),
          "Put the phone in another room — not face down, another room — and work in 25-minute "
          "blocks with a 5-minute break where you get up. Before each block, write the one thing "
          "you will finish on a scrap of paper so you do not have to decide where to start. Same "
          "desk, same time, same little ritual helps more than willpower.",
          avoid=NOT_AN_EXAM + LOSING_TRACK_OF_MONEY,
          # revision-active is a nudge of 1 too; this entry is the one that answers a
          # line about the phone, so it has to beat it rather than lose on registry order.
          bias=2),
    # "How do I concentrate better", "how do I stay focused", "my mind wanders when I read"
    # and "why can't I concentrate" were all shrugs: the focus words were only ever looked
    # for next to a study word. A line that asks about concentrating, with no subject at all,
    # is the same question as the revision one, so one general answer covers it - and the
    # revision, phone and working-from-home entries keep their own lines by bias.
    entry("concentration", (("concentrate", "concentrating", "concentration", "focus",
                             "focusing", "focused", "distracted", "distracting",
                             "distraction", "wanders", "attention", "procrastination",
                             "procrastinating", "procrastinate"),
                            ("how do i focus", "how can i focus", "how do i concentrate",
                             "how can i concentrate", "how do i stay", "how do i keep",
                             "how do i improve", "how do i pay", "how do i stop",
                             "how do i beat", "better", "improve", "improving", "stay",
                             "keep", "cant", "cannot", "why", "help", "class", "mind",
                             "anything", "beat", "pay")),
          # "work", "longer" and "read" are key words of other entries: taking them on low​ers
          # the rarity of lines like "how do i work for longer without a break" and turns a
          # real answer into a hedge. Words that are nobody else's cost nothing.
          "Mostly it is the setup, not willpower: enough sleep, food, the phone in another "
          "room and one thing open at a time. Work in 25-minute blocks on a single task "
          "written down first, because choosing where to start is half the distraction, and "
          "stand up for the break. If your mind wanders when you read, take notes by hand and "
          "say the page back to yourself in one line at the end of it.",
          # The meeting-day entry owns meetings; "focus" there is about finding the time.
          avoid=("camera", "lens", "autofocus", "photograph", "photo", "diet", "weight",
                 "good things", "road", "driving", "meeting", "meetings"),
          bias=-1),
    entry("learn-language-daily", (("learning", "learn", "learnt", "study", "picking up",
                                   "memorise", "memorize", "memorising", "memorizing",
                                   "fluent", "fluency", "fluently", "speak", "speaking"),
                                   ("language", "spanish", "french", "italian", "german",
                                    "portuguese", "japanese", "chinese", "welsh", "korean",
                                    "russian", "arabic", "dutch", "greek", "polish")),
          "Split your time in three: a few minutes going over yesterday's phrases out loud, most "
          "of it on new phrases said aloud and written down once, and a few minutes listening to "
          "something short at normal speed. Learn whole phrases you will use rather than grammar "
          "tables, and speak from the first week — even to yourself in the kitchen. One lesson or "
          "one conversation partner a week is what makes the rest work.",
          avoid=NOT_AN_EXAM, bias=1),
    # Which one to learn had no card at all. Every language entry here said how to practise or
    # how long it runs for, and "which language should i learn" reached the practise one - so the
    # person asking for a pick was told "Split your time in three: a few minutes going over
    # yesterday's phrases out loud", an answer to a question they had not asked yet.
    #
    # The key is the asking itself, written out, and there is only one group of it: a line that
    # says "which language should i learn" in any of the ordinary ways is a pick, and a line that
    # says "how do i learn french quickly" or "what language do they speak in brazil" is not.
    # "what language" alone would take the second of those, so the phrase carries the should/learn
    # with it.
    entry("pick-a-language",
          (("which language should", "what language should", "language should i",
            "languages should i", "what language to", "which language to", "what language do i",
            "which language do i", "best language to", "easiest language to",
            "hardest language to", "good language to", "useful language to",
            "most useful language", "language worth", "languages worth",
            "which language is", "what language is", "pick a language", "choose a language",
            "which language first", "what language first", "easiest language",
            "hardest language", "best language"),
           ("learn", "learning", "learnt", "study", "studying", "pick", "picking", "choose",
            "choosing", "start", "starting", "first", "worth", "recommend",
            "english speaker", "english speakers")),
          "Pick by what you will actually use it for, not by which is easiest on paper: the "
          "language of the country you visit, or of the family you are marrying into, beats any "
          "ranking. With no reason to choose, Spanish is the usual bet - about 500 million "
          "speakers, spelling that matches the sound, and a lot of cheap material - and if you "
          "already have French or Italian, the other one of the pair is the cheapest start of "
          "all. The clock is the real cost: about 600 to 750 hours of class for Spanish, French "
          "or Italian, but roughly 2,200 for Arabic, Chinese, Japanese or Korean.",
          # a phrase, a translation, an exam, a course and a place where the language is spoken
          # all name one without asking which to learn
          avoid=NOT_AN_EXAM + ("say", "says", "saying", "pronounce", "translate", "translation",
                               "phrase", "phrases", "speak", "speaks", "speaking", "spoken",
                               "in spanish", "in french", "in italian", "in german",
                               "in welsh", "in irish", "in gaelic", "in portuguese",
                               "sign language", "duolingo", "app", "apps", "lesson", "lessons",
                               "class", "classes", "course", "courses", "gcse", "a level",
                               "a-level", "degree", "university", "abroad", "moving to",
                               "live in", "holiday", "my child", "my son", "my daughter"),
          bias=2),
    # The other half of the language question, and the one with a number in it: "how long does
    # it take to learn Spanish" and "how long until I'm fluent" were both shrugs, because every
    # language entry here says how to practise and none of them says how long it runs for. The
    # person is asking for a figure, so the answer leads with the hours and turns them into
    # minutes a day, which is what makes the difference between the two answers obvious.
    entry("language-hours",
          ((LANGUAGE_LEARNING + ("learn", "learning", "learnt", "learned", "become fluent",
                                "get fluent", "pick up")),
           ("long", "hours", "years", "months", "weeks", "until", "soon", "time")),
          _language_hours,
          # the clock has to be asked for, or a plain report ("ive been learning spanish for
          # two years") would be answered with a timetable
          ask=("how long", "how many hours", "how many years", "how many months",
               "how many weeks", "how soon", "how much time", "how long until", "how long till",
               "how long before", "until i'm", "until im", "to become", "does it take"),
          # a course's hours, a week's hours and the exam senses are each somebody else's
          # question; "how many hours a week should i study spanish" is the habits answer
          avoid=NOT_AN_EXAM + ("a week", "per week", "each week", "every week", "hours a week",
                               "how often", "sign language", "translate", "translation",
                               "pronounce", "pronunciation", "spell", "spelling", "grammar",
                               "lesson", "lessons", "class", "classes", "course", "courses",
                               "app", "apps", "duolingo", "gcse", "a level", "a-level",
                               "ielts", "degree", "university",
                               # "how long have you been learning spanish" is a question about
                               # the bot, and a timetable is not the answer to it
                               "have you been", "did it take you", "you been",
                               "how long have you"),
          # The clock is what makes it this question rather than the how-to-practise one next
          # door, and "how long does it take to learn spanish" is both of them at once: the
          # practise rows are keyed on learn/language and score the same, so this one has to be
          # the more specific of the tie. It only reaches a line that names a language *and*
          # asks how long, which is what keeps the 2 honest.
          guard=_names_a_language,
          bias=2),
    entry("trip-phrases", (("phrases", "phrasebook"),
                           ("learn", "before", "holiday", "trip", "italy", "spain", "france",
                            "language", "useful")),
          "Learn these twelve and you can get through most of a holiday: hello, goodbye, please, "
          "thank you, sorry, excuse me, do you speak English, I don't understand, how much is this, "
          "the bill please, where is the toilet, and help. Say them out loud until they are "
          "automatic, because under pressure you will use what you can say without thinking.",
          avoid=NOT_AN_EXAM),
    entry("say-language", (("say", "pronounce", "translate", "translation"),
                           ("spanish", "french", "italian", "german", "espanol", "español",
                            "francais", "français", "italiano", "deutsch",
                            "portuguese", "portugues", "português", "greek", "turkish",
                            "japanese", "chinese", "mandarin", "dutch",
                            "welsh", "cymraeg", "irish", "gaeilge", "gaelic")),
          # bias 3, not 2: `end-a-conversation-leave` (friends.py) keys "say goodbye" and took
          # "how do i say goodbye in greek" on it, and a language named in the line is this
          # card's question. Welsh and Irish keep their own row below, because lengthening this
          # key cost "how do i say thank you in french" the phrasebook.
          _say_in_language, avoid=NOT_AN_EXAM, guard=_a_phrase_is_asked, bias=3),
    # Welsh and Irish are asked for by name in the UK more than Italian is, and "how do i say
    # hello in irish" reached nothing. They are their own row, not more words on the one above:
    # lengthening that key made "how do i say thank you in french" lose the phrasebook to the
    # thank-you note, which is a worse answer than the one main gives.
    entry("say-welsh-irish", (("say", "pronounce", "translate", "translation",
                               # "whats thank you in welsh" names the phrase and the language
                               # and no verb, and it hedged
                               "whats", "what is", "what's"),
                              ("welsh", "cymraeg", "wales", "irish", "gaeilge")),
          _say_in_language, avoid=NOT_AN_EXAM, guard=_a_phrase_is_asked, bias=3),
    # "whats thank you in welsh" names no verb at all, and the line with a language and a
    # phrase in it is this question whichever way it is put.
    # The language is the subject, so it goes first: with the ask in front, "how" and "bill"
    # were enough on their own, and "how do i split bills with housemates" was answered with
    # "the bill, please" in Welsh.
    # The third group is the ask, and a correction that swaps one language for another has no
    # ask in it at all: "actually french", "no, german then", "make that italian" name the
    # language and nothing else, so the row never saw them and a person correcting themselves
    # got "I'm listening - say more if it helps." The correction words are the ask here, and the
    # guard is what keeps the row off the lines that have more in them than a language.
    entry("say-language-phrase", (("spanish", "french", "italian", "german", "espanol", "español",
                                   "francais", "français", "italiano", "deutsch",
                                   "welsh", "cymraeg", "irish", "gaeilge", "gaelic"),
                                  CONCEPT_WORDS,
                                  ("whats", "what is", "what's", "how", "i need", "translate",
                                   "actually", "instead", "make that", "not", "no", "then",
                                   "what about", "about", "or", "rather", "i mean", "mean")),
          _say_in_language, avoid=NOT_AN_EXAM, guard=_a_phrase_is_asked, bias=2),
    # a foreign word in the line and a "what does that mean": the word names the language, so
    # the table answers backwards.
    entry("what-does-that-mean", (("mean", "means", "meaning", "what does", "whats"),
                                  tuple(sorted(NATIVE))),
          _what_does_it_mean,
          # The line has to be asking what a word means. "whats" on its own is the word "what"
          # read loosely, so without this the row took every "what was that noise" and every
          # "whats the cost per person" and answered with a translation of some ordinary word
          # in it. A meaning ask is a hard gate, and the key words above are what it then reads.
          ask=("mean", "means", "meaning", "translate", "translation", "stand for",
               "stands for", "what does it say", "in english"),
          # "i mean" is the filler people think out loud with, not a question about a word:
          # "i mean the price per kilo" is a shopping line, and the Italian table has "per"
          # in it as the word for "for".
          avoid=("i mean", "i meant", "meaning to say"),
          bias=1,
          # The ask above is needed and not enough: three of the words in the table are English
          # too, so "what does bore mean" was Welsh for good morning, "what does faint mean" was
          # Welsh for how much and "what does non mean" was Italian for I don't understand. The
          # guard asks whether the word in the line is the one being asked about.
          guard=_a_word_is_being_asked_about),
    entry("subjects-choose", (("choose", "choosing", "pick", "picking"),
                              ("a-levels", "alevels", "a levels", "gcses", "subjects", "degree",
                               "course", "university", "college")),
          "Pick the subjects you will still work at on a bad week, then check the entry "
          "requirements for two or three courses you might want later, because that is what closes "
          "doors rather than the subjects themselves. Keeping one essay subject and one numerical "
          "one keeps more options open than people expect. Ask a teacher you trust what they think "
          "you would enjoy, not just what you are good at.",
          avoid=NOT_AN_EXAM),
    entry("university-worth", (("university", "uni", "degree"),
                               ("worth", "going", "go", "should", "apprenticeship", "debt",
                                "better",
                                # "do i need a degree" and "what are the alternatives to
                                # university" are the same decision asked from the other side
                                "need", "needed", "necessary", "alternative", "alternatives",
                                "without a degree")),
          "It depends on what you want to do: for nursing, engineering, law or teaching the degree "
          "is the door, and for plenty of other jobs experience gets you further for less money. "
          "Compare a degree with a degree apprenticeship in the same field — earn while you learn, "
          "no fees — and look at what people actually doing the job you want studied. Ask two of "
          "them before deciding.",
          avoid=NOT_AN_EXAM + _A_DEGREE_OF_HEAT),
    # "is it worth doing an apprenticeship" and "are apprenticeships paid" were both the search
    # shrug: the choice against university had a card that needed the word "university", and the
    # how-to-apply card stands down on "worth it". This is the card for what one is and whether
    # it pays - `apprenticeship-how` above still answers how to apply for one.
    entry("apprenticeship-worth",
          (("apprenticeship", "apprenticeships", "apprentice", "degree apprenticeship",
            "higher apprenticeship", "level 2 apprenticeship", "level 3 apprenticeship"),
           ("worth", "worth it", "should", "paid", "pay", "pays", "earn", "earning", "money",
            "wage", "wages", "much", "better", "instead", "uni", "university", "degree", "what",
            "whats", "good")),
          "An apprenticeship is a paid job with the training built into the week: most of the "
          "time you work, about a fifth of it you study, and there are no tuition fees. They run "
          "from GCSE level up to degree apprenticeships in engineering, digital, nursing and "
          "accountancy, so one can stand in place of a degree - you earn while you learn and "
          "finish with experience and no student debt, but with less choice of where you study. "
          "Pay is at least the apprentice minimum wage and more on most schemes.",
          # how to apply for one is `apprenticeship-how`, which names the gov.uk service and the
          # closing dates, so the shapes that ask where to find one stand this card down.
          avoid=NOT_AN_EXAM + ("apply", "applying", "get one", "get an", "get a", "how do i get",
                               "how to get", "find one", "find an", "where do i", "search",
                               "become an", "become a", "start one", "start an", "vacancies",
                               "vacancy", "looking", "look for", "start looking")),

    entry("results-day", (("results", "grades", "gcse", "gcses", "a-level", "a level",
                           "a levels", "alevels"),
                          ("didn't", "didnt", "bad", "worse", "failed", "disappointed", "resit",
                           "clearing", "not what", "missed", "offer", "rejected", "options",
                           "now what")),
          "First, it is not the end of anything: there are more routes from here than there were "
          "before results day. If you have missed a university offer, ring the university "
          "yourself today — courses take people who call — and look at Clearing the same afternoon. "
          "For school exams, ask about a remark and about resitting in November or next summer; "
          "both are normal and neither sets you back a year if you use the time.",
          avoid=NOT_AN_EXAM + MOCK, bias=1),
    entry("study-procrastinate", (("procrastinat", "put off", "putting off", "put it off",
                                   "put things off", "cant start", "can't start", "cannot start",
                                   "keep putting", "get started", "get going"),
                                  # "keep", "stop", "jobs", "tasks" and "work" are the
                                  # procrastination verb, not a study word: "i keep putting off
                                  # calling the dentist" is not a revision question.
                                  ("study", "studying", "revising", "revision", "homework",
                                   "essay", "uni", "university", "college", "school", "coursework",
                                   "dissertation", "thesis", "assignment", "reading", "deadline",
                                   # "stop" stays: "how do i stop procrastinating" is the
                                   # question, and it cannot pull in a line without a study word.
                                   "stop")),
          "Do the smallest possible first step, not the whole job: open the book at the page and "
          "write the title and today's date, or set a timer for five minutes and let yourself do "
          "it badly. Putting it off is mostly about the task feeling too big to start, and it "
          "shrinks as soon as you are in it. Decide tonight what tomorrow's first step is, so "
          "then it is an instruction to follow rather than a choice to make.",
          # a line that names the exam and its date wants the plan, not the pep talk
          avoid=NOT_AN_EXAM + ("exam", "exams", "gcse", "gcses", "a-level", "a levels", "mocks",
                               "mock", "test", "tests"),
          bias=2),
    entry("thesis-statement", (("thesis statement", "topic sentence", "thesis"),
                               ("what", "write", "how", "example", "essay", "introduction",
                                "start", "good", "should", "my")),
          "A thesis statement is one sentence that says the claim your essay will prove, and why it "
          "matters: \"Cheaper public transport would cut city emissions more than electric cars, "
          "because most journeys are short.\" Put it at the end of your first paragraph, make it "
          "something a reasonable person could disagree with, and check that every paragraph after "
          "it is evidence for that one sentence. If a paragraph is not, either cut it or change the "
          "thesis.",
          avoid=("phd", "masters", "supervisor", "submitted", "binding", "library")),
    entry("study-timetable", (("timetable", "revision timetable", "schedule", "planner",
                               "spreadsheet", "plan", "planning"),
                              ("revision", "revise", "revising", "exam", "exams", "subject",
                               "subjects", "study", "studying", "gcse", "gcses", "a-level",
                               "a levels", "mocks")),
          "Count the days you actually have (sleep and school nights are not revision), list the "
          "topics per subject, and give each topic one block rather than one subject one day: three "
          "blocks a day is a real day's work. Put the subject you dread first, in the morning. "
          "Leave the last three days for past papers under time, and leave one day empty, because "
          "something always slips.",
          avoid=NOT_AN_EXAM, bias=2),
    entry("study-how-long", (("study", "studying", "revise", "revising", "revision", "homework"),
                             ("how long", "how many hours", "hours", "long", "blocks", "pomodoro",
                              "breaks", "break",
                              # the phrases are what a break question actually says, and the two
                              # revision entries key "how", so the phrase has to be the key
                              "take a break", "take breaks", "a break from", "break from",
                              "break between", "breaks between", "how often break",
                              "how often should i break", "how long a break",
                              "how long should i break")),
          "About 25 to 45 minutes at a time, then a proper 5 to 10 minutes away from the desk: "
          "two or three hours of that is a good day, and four is a very long one. What counts is "
          "testing yourself in the block, not the hours you sat there. If you keep losing track, "
          "set a timer for the block and stop when it goes, even mid-sentence — stopping on a "
          "problem you can pick up again makes the next start easy.",
          # "how long before an exam should i start revising" and "how many weeks before should i
          # revise" were answered with the length of a study block, which is the other question
          # with the words "how long". Where to start and how far ahead are `revision-start`'s.
          avoid=NOT_AN_EXAM + NOT_REVISION
          + ("how long before", "how long until", "how far ahead", "how early",
             "weeks before", "months before", "days before", "how long do i need",
             "how long does it take to revise", "how long should i revise for the exam"),
          # "how many hours of revision a day for gcses" and "how many hours should i revise a
          # day" tied with the row for the hours in a winter day on "hours" and "day", and lost
          # on registry order. The line names revising, so this row is the one that answers it.
          bias=2),
    # "how much homework should a 10 year old get" reached nothing on main: family.kids-homework
    # wants the word "help" or "struggling", and study-how-long wants "long". The amount is a
    # homework question, so it lives here rather than in one more copy of the routine.
    entry("homework-amount",
          (("homework", "home work"),
           ("how much", "much homework", "how long should homework", "how many minutes",
            "how many hours of homework", "how long homework")),
          "Most primary homework is 20 to 30 minutes a night by the last years at primary, and "
          "about an hour a night in year 7 and up, with a break part way. If a piece runs well "
          "past that, write a note to the teacher rather than pushing through it, because homework "
          "that takes an hour and ends in tears is usually the wrong homework.",
          # a fight at homework time is the battle script, and a nightly routine question is
          # family.kids-homework: this one is only the amount
          avoid=("wont", "won't", "will not", "refuses", "refusing", "hates", "hate", "battle",
                 "fight", "fights", "fighting", "nightmare", "sit down", "every night",
                 "help", "struggling", "struggles", "routine", "table"),
          bias=1),
    entry("study-forgetting", (("forget", "forgetting", "forgot", "cant remember",
                                "can't remember", "wont stick", "won't stick", "doesnt stick",
                                "doesn't stick"),
                               ("revise", "revising", "revision", "study", "studying", "learn",
                                "learned", "learnt", "memory", "remember", "everything")),
          "That is normal and it has a fix: what you re-read fades in a day or two, and what you "
          "test yourself on comes back. Same day, look at the topic and cover it and say it out "
          "loud; then again after two days, after a week, and after a month. Turn each topic into "
          "five questions and keep them on cards, and go through yesterday's cards for two minutes "
          "before starting anything new.",
          ask=("revise", "revising", "revision", "study", "studying", "learn", "learned",
               "learnt", "exam", "exams", "test", "tests", "school", "college", "uni",
               "university", "homework", "re-read", "reread"),
          avoid=NOT_AN_EXAM),
    # The essay subjects had no card at all: "i keep failing history" was answered with the
    # never-miss-twice streak advice, and once that row stood down on the subject words it got
    # the composer's "I doubt that's the whole picture" line, which is a shrug with warmth. The
    # method for these subjects is the past paper and the mark scheme, exactly as maths is, so
    # the card exists for the same reason and says the same kind of thing.
    entry("revision-essay-subjects",
          (("english", "english literature", "english language", "english lit", "history",
            "geography", "psychology", "sociology", "economics", "business studies",
            "religious studies", "politics", "media studies", "classics", "law a level"),
           ("revise", "revising", "revision", "exam", "exams", "test", "tests", "failing",
            "fail", "failed", "behind", "bad at", "rubbish at", "struggling", "stuck", "how",
            "better", "improve", "improving", "marks", "grade", "grades")),
          "Essay subjects are learned by writing answers, not by reading the notes again: get "
          "the mark scheme for your board, write three timed past questions a week and plan the "
          "other two in a spider diagram. Mark your own answer against the criteria and count "
          "what you missed - a point you did not make, a quote, the evaluation sentence at the "
          "end - because the marks are in the structure as much as the knowledge. Learn five "
          "specific examples or quotes per topic rather than twenty vague ones, and keep them on "
          "cards: one named case with a date beats a paragraph about 'many historians'.",
          ask=("revise", "revising", "revision", "exam", "exams", "study", "studying", "learn",
               "school", "college", "a level", "a levels", "gcse", "gcses", "test", "tests",
               "how", "better", "failing", "fail", "behind", "help", "tips"),
          # "history" is also a browser and a medical note, "english" is a language somebody
          # wants to speak, and either one on its own would answer a line that is not about
          # school: those shapes are other cards.
          avoid=("browser", "browser history", "search history", "watch history", "clear my",
                 "delete my", "cookies", "cache", "incognito", "medical history", "family history",
                 "ancestry", "genealogy", "ancestors", "my gp", "symptoms",
                 "speak english", "speaking english", "pronounce", "pronunciation", "accent",
                 "learn english", "improve my english", "fluent", "english speaking",
                 "native speaker", "another language")),
    entry("revision-maths", (("maths", "math", "mathematics", "algebra", "geometry",
                              "trigonometry", "physics", "chemistry", "biology", "science",
                              "calculations"),
                             ("revise", "revising", "revision", "exam", "exams", "test", "learn",
                              "practise", "practice", "marks", "better", "how",
                              # a subject going badly is the same help asked the other way
                              # round: "i keep failing maths what should i do" was answered by
                              # the habit row, because "keep failing" is a habit phrase and
                              # nothing in this key named failing.
                              "failing", "fail", "failed", "fails", "struggling", "struggle",
                              "behind", "bad at", "rubbish at", "slipping", "stuck")),
          "Maths and the sciences are learned by doing, not reading: work through the examples with the book open, "
          "then close it and do them again, then do past papers with the mark scheme next to you. "
          "Mark them honestly and write down the topics that lost marks; those get redone three "
          "days later. Learn the formulas by using them in questions rather than copying them out "
          "ten times, and if a topic still will not work, ask a teacher or a classmate to watch you "
          "do one question.",
          avoid=NOT_AN_EXAM, bias=2),
    entry("memorise-lines", (("memorise", "memorize", "memorising", "memorizing", "learn by heart",
                              "off by heart", "learn lines", "my lines", "lines"),
                             ("speech", "poem", "lines", "script", "play", "part", "presentation",
                              "talk", "wedding", "words", "monologue")),
          "Split it into chunks of three or four lines and learn the first word of each chunk, "
          "because that is what you will forget first. Read the chunk aloud, look away and say it, "
          "then add the next chunk and say both; record yourself and listen while walking or "
          "washing up. Say the whole thing out loud twice a day and it settles in about a week.",
          # The word "line" is in the key, so a line that asks for a line to SAY ("suggest a
          # funny opening line for my speech") was told how to memorise them: opening a speech
          # and learning one are different jobs, and speech-opener answers the first.
          avoid=NOT_AN_EXAM + ("opening line", "opening lines", "first line", "first words",
                               "opener", "icebreaker", "ice breaker", "hook", "joke", "jokes",
                               "funny")),
    # "how do i get up early to study" is about the getting up, not about what to revise.
    entry("study-mornings", (("get up", "getting up", "get out of bed", "wake up", "waking up",
                              "mornings", "morning", "alarm"),
                             ("early", "study", "studying", "revise", "revising", "revision",
                              "5am", "6am", "before school", "before work")),
          "Put the alarm across the room, and set it for the same time every day including "
          "weekends, because a lie-in on Sunday is what makes Monday impossible. Be in bed eight "
          "hours before it, and leave the book open at the page the night before so the first ten "
          "minutes need no decision. Then get up when it rings: negotiating with yourself is the "
          "part that fails.", bias=3,
          avoid=("cant sleep", "can't sleep", "insomnia", "wont wake", "wakes me", "nap",
                 "tired all", "cant get up", "can't get up",
                 # a dog's morning is the dog's: "my dog is up at 5am every morning" was the
                 # study routine, and the night-routine answer is the one that knows about dogs
                 "dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens",
                 "pet", "pets",
                 # and a baby, a toddler or a child is up at 5am for its own reason: that is a
                 # night waking, not the person's own morning routine
                 "baby", "babies", "toddler", "toddlers", "child", "children", "kid", "kids",
                 "son", "daughter", "year old", "year olds", "year-old", "yr old", "yrs old",
                 # a line that asks WHEN is the study-time entry's, not the alarm's: "is it
                 # better to study in the morning or evening" is a comparison of two times, and
                 # it was answered with the alarm across the room. The comparison words are in
                 # the line only when the person is asking which time, so the row stands down.
                 "time of day", "better time", "best time", "morning or", "evening or",
                 "or evening", "or night", "or morning", "which is better", "what time of day",
                 "better at night", "better in the morning", "better in the evening",
                 "better in the day", "study better", "revise better", "really better",
                 # the two-times comparison is written with "or" between them and often with a
                 # preposition: "is it better to study at night or in the morning" beat every
                 # phrase above because "at night or in the morning" is not "or night".
                 "at night or", "or in the morning", "or in the evening", "or in the day",
                 "in the morning or", "in the evening or", "night or morning",
                 "evening or morning", "morning or night", "morning or in",
                 "sharper",
                 # and a feeling or a symptom in the line is a question about that, not about the
                 # alarm: "i feel anxious every morning before work" was the alarm lecture, and so
                 # was "im exhausted every morning before work". Those lines have answers of their
                 # own in the chat and stomach entries, so this row stands down on them.
                 "feel", "feeling", "feels", "felt", "sick", "nauseous", "nausea",
                 "anxious", "anxiety", "panic", "panicky", "dread", "dreading",
                 "exhausted", "tired", "stress", "stressed", "worry", "worried",
                 "unhappy", "depressed", "miserable", "low mood")),
    # "suggest a funny opening line for my speech" got the memorise-the-lines answer, and
    # "i need an opener for my speech" was a shrug: write-a-toast answers how to build a speech
    # and this answers only what to say first.
    entry("speech-opener",
          # The opener nouns only: "how do i start a presentation at work" and "how do i start a
          # wedding speech" keep the answers they have (write the first thirty seconds out, and
          # the guest list), and a line that asks for a joke keeps the joke.
          (("opening line", "opening lines", "first line", "first words", "opener", "openers",
            "icebreaker", "ice breaker", "one liner", "one-liner", "hook", "open my speech",
            "open a speech", "open my talk", "open a talk", "open my presentation",
            "open a presentation"),
           ("speech", "talk", "presentation", "toast", "audience", "room", "stage",
            "best man", "maid of honour", "wedding", "assembly", "work do", "leaving do")),
          "Ask the room something it already knows the answer to, or name the one detail everyone "
          "there has seen - \"hands up who has been handed a handbag and told to hold it\" - then "
          "wait a beat before your name. Keep it under ten seconds and make the joke about you "
          "rather than anyone in the room, and if nothing comes, open with the strangest real "
          "detail of the story instead of a joke.",
          # a script, a play or a poem is read and learned, not opened, and the wording rows for
          # cards and vows own their own lines
          avoid=("poem", "poems", "script", "play", "monologue", "card", "cards", "vows",
                 "eulogy", "thank you letter"),
          bias=1),
    entry("study-awake", (("awake", "tired", "sleepy", "nodding off", "drowsy", "exhausted",
                           "asleep", "falling asleep", "sleep"),
                          ("study", "studying", "revise", "revising", "revision", "homework",
                           "lecture", "class", "stay", "staying")),
          "Stand up and move for two minutes every half hour, drink water, and put a bright light "
          "on your face — sleepiness at a desk is often boredom plus warm air. Do the hardest thing "
          "first and leave the reading for when you are flagging. If you are falling asleep at 9pm "
          "you need sleep, not coffee: an early night and an hour in the morning beats two hours "
          "of fighting it.",
          # the homework battle is a parenting question, not a sleepiness one, and "exhausting"
          # is the word that took it: "the homework battle every night is exhausting" was told to
          # stand up every half hour and put a bright light on.
          avoid=NOT_AN_EXAM + ("homework battle", "battle over homework",
                               "battles over homework", "homework is a battle",
                               "homework every night", "every night is a battle",
                               "the homework battle"),
          bias=2),
    # "i'm helping my son with maths homework" is a parent asking for the maths, not for the
    # battle script: the ask gate is the problem words only, never "help".
    entry("homework-child", (("homework",),
                             ("son", "daughter", "child", "kid", "kids", "children", "teenager",
                              "wont", "won't", "refuses", "refusing", "refused", "battle",
                              "battles", "nightmare", "help", "struggling", "struggles",
                              "fights", "every night",
                              # a child named by age is still a child: "my 7 year old will not
                              # sit down and do his homework" is the battle, and on main it
                              # reached nothing at all
                              "year old", "years old")),
          "Same time and same table every night, twenty minutes then a break, and the phone in "
          "another room — the fight is usually about the phone and the sudden start, not the work. "
          "Sit nearby doing your own quiet job rather than over their shoulder, and only help when "
          "they ask. If it is still a battle after a week, tell the teacher what you are seeing: "
          "homework that takes an hour and ends in tears is usually the wrong homework.",
          # "how do i help my kid with homework" is the same question asked as a question, so
          # the asking forms stay in; "i'm helping my son with maths homework" is a statement
          # about today's homework and must not get the battle script.
          ask=("wont", "won't", "refuses", "refusing", "refused", "hates", "battle", "battles",
               "fights", "fighting", "nightmare", "struggling", "struggles", "every night",
               # "will not sit down and do it" is the same refusal without the word "wont"
               "will not", "wont sit", "will not sit", "sit down", "get him to", "get her to",
               "get them to", "get my", "hates homework", "hate homework",
               "how do i help", "how can i help", "how to help", "how do i get him",
               "how do i get her", "what should i do about"),
          # "ok il try that" is the person taking the advice, not asking for it again: the same
          # script word for word on the next turn is the bot talking to itself.
          avoid=NOT_AN_EXAM + ("ok il try", "ok i'll try", "ill try that", "i'll try that",
                               "i will try that", "ok thanks", "thanks that helps",
                               "that helps", "will do", "ok will do", "sounds good",
                               "okay i will", "ok i will")),
    entry("essay-reference", (("reference", "references", "referencing", "cite", "citation",
                               "bibliography", "sources"),
                              ("essay", "book", "article", "website", "harvard", "style", "write",
                               "list", "how", "dissertation", "assignment", "coursework",
                               "sources")),
          "Every claim that is not yours needs the author, the year and the page, and every source "
          "you used goes in the list at the end: author, year, title, publisher (or URL and the "
          "date you looked at it). Use the exact style your course asks for — Harvard, APA and MLA "
          "differ — and copy the format from your course guide rather than from memory. Quote "
          "sparingly and put the page number in, because a quote without one is the thing markers "
          "flag.",
          ask=("essay", "assignment", "coursework", "dissertation", "university", "college",
               "school", "harvard", "apa", "mla", "book", "website", "article", "sources"),
           # "how do i reference a book in an essay" fits this row and the football card equally
           # well on their own scores, because that card keys "booked" and this line says "book";
           # the essay is what is being written, so the essay row is the one that answers.
           bias=1,
          avoid=NOT_AN_EXAM + ("job", "jobs", "application", "applications", "interview",
                               "interviews", "cv", "employer", "referee", "boss", "manager")),
    entry("learn-an-instrument-as-an-adult", (("piano", "guitar", "violin", "instrument",
                                               "instruments", "keyboard", "drums", "clarinet",
                                               "flute", "saxophone", "sax", "cello", "trumpet",
                                               "ukulele", "banjo", "recorder", "harmonica",
                                               "trombone", "viola", "double bass", "oboe",
                                               "bassoon", "harp"),
                                              ("adult", "adults", "learning", "learn", "taking up",
                                               "take up", "late", "start", "starting", "old")),
          ("It is not too late: adults pick up the theory faster than children, they just need "
           "shorter and more regular practice. Twenty minutes a day gets you a simple song in two "
           "or three months, and four chords in about a month. Have six lessons with a teacher "
           "first, so nobody has to unlearn your posture."),
          ask=("too old", "too late", "start", "starting", "take up", "taking up", "begin",
               "worth it", "should i", "can i", "advice", "think about")),
    # An evening course is the way most adults go back to learning, and the question is never
    # "what is a course": it is how many hours it eats, whether it is worth the year and what it
    # costs. The class hours are published - guided learning hours - so the first sentence can be
    # a number rather than advice to go and ask.
    entry("evening-course",
          (("evening course", "evening courses", "evening class", "evening classes",
            "night class", "night classes", "adult education", "adult course", "adult courses",
            "adult learning", "part time course", "part-time course", "part time degree",
            "part-time degree", "access course", "access to higher education",
            "college course", "community course", "evening college"),
           ("worth", "worth it", "hours", "how much work", "how much time", "how long", "start",
            "starting", "enrol", "enroll", "sign up", "beginner", "level", "fees", "fee", "cost",
            "commitment", "a week", "per week", "workload", "homework", "fit", "manage",
            # "should i do an access course" names the course and nothing else this entry keys
            "should i", "shall i", "can i", "do i need", "is it")),
          ("Most evening courses are two or three hours of class a week plus about the same again "
           "at home, so plan on one evening and four or five hours a week. Ask for the guided "
           "learning hours before you enrol, because the college has to publish them, and check "
           "the fee: in England, English and maths up to GCSE are free for anyone who does not "
           "already have them, and a first level 2 or 3 qualification is often free if you are "
           "under 23 or on a low income. At the open evening, ask what the last group went on to "
           "do - that is what tells you whether it is worth the year."),
          # "how long do i boil an egg" and "how many hours a week should i revise" are their own
          # questions, and the words "course" and "class" alone are too wide: "my course" is an
          # essay question and "in class" is a school one.
          ask=("course", "courses", "class", "classes", "college", "adult", "evening", "night",
               "worth", "hours", "workload", "should i", "shall i", "is it worth"),
          # "how much work a week would an evening course be" carries the money words ("how much",
          # "a week") and the weekly saving entry took it. The course is the subject of the line,
          # so one nudge keeps the hours answer on top without moving either entry in the file.
          bias=1,
          avoid=("essay", "essays", "coursework", "assignment", "dissertation", "exam", "exams",
                 "revision", "revise", "boil", "oven", "swim", "swimming", "running", "race",
                 "golf", "dinner", "meal", "online course", "free course online")),
    # The "am I too old" question is the entry above; this is the "how do I actually start one"
    # question, and the first step is a guitar that stays in tune and doesn't cut your fingers.
    entry("learn-guitar-first-steps", (("guitar", "guitars", "ukulele", "bass guitar",
                                        "learning guitar", "play guitar"),
                                       ("start", "starting", "beginner", "first", "learn",
                                        "learning", "app", "apps", "lessons", "teacher",
                                        "cheap", "buy", "practice", "practise", "good way",
                                        "how do i")),
          "Buy a used acoustic from a shop that sets it up for you, 80 to 150 pounds: a 30 pound "
          "supermarket one sits too high off the neck, hurts your fingers and is why people stop "
          "after a fortnight. Practise fifteen minutes a day, not an hour once a week, and learn G, "
          "C, D and Em, which is most of the songs you already like. An app is fine for a month; "
          "six lessons after that fix your hands before the habits set.",
          # "am i too old to learn" is the entry above, and a guitar being sold is not this question
          avoid=("old", "late", "sell", "selling", "repair", "string", "strings", "broken",
                 "tuning", "amp", "amplifier"),
          # "I'm trying to learn the guitar" in an introduction is a chat line, not a how-to
          ask=("how", "what", "which", "should", "is it", "is a", "is an", "any", "tip", "tips",
               "advice", "best", "good way", "worth", "start", "beginner", "cheap", "cost")),

    # Handwriting is a practice question, not a talent one, and the fixes are physical: grip,
    # paper, speed, and ten minutes a day on the letter shapes that join badly.
    entry("handwriting", (("handwriting", "hand writing", "write neatly", "neat writing",
                           "messy writing", "illegible", "joined up writing", "cursive"),
                          ("improve", "better", "messy", "neat", "neater", "legible", "fix",
                           "practice", "practise", "slow", "read", "help", "child", "children",
                           "kid", "kids", "son", "daughter", "awful", "terrible", "bad", "poor",
                           "school")),
          "Slow down by about a third for a week and use lined paper: most messy handwriting is "
          "speed, not hand shape. Then pick the two or three letters you join badly (r, n, m and "
          "your a's) and copy a paragraph a day, ten minutes, saying each letter as you write it. "
          "Check the shelf: a pen with a grip you actually hold, sitting up with both feet down and "
          "the paper turned slightly. If it is a child, check the grip first - a fist grip or a "
          "thumb over the top makes neat writing almost impossible - and use a pencil long enough "
          "to reach the table."),

    entry('school-bag',
          # A bare 'bag' is ordinary English - "i lost my bag", "packing a bag for the flight" -
          # so the row names the bag-in-school shapes and leaves the rest alone.
          (('school bag', 'schoolbag', 'book bag', 'backpack', 'rucksack',
            'bag for school', 'bag ready for school',
            'bag tidy', 'keep my bag', 'my bag tidy', 'my bag is a mess', 'bag is a mess',
            'in my bag', 'my bag is always', 'pack my bag', 'packing my bag', 'my bag packed',
            'organise my bag', 'organize my bag', 'sort my bag', 'sorting my bag'),
           ('tidy', 'tidy up', 'keep tidy', 'organise', 'organised', 'organize', 'mess', 'messy',
            'lost', 'losing', 'forget', 'forgot', 'pack', 'packing', 'everything')),
          "Pack it the night before, not in the morning: the timetable, then the books for those "
          "lessons, then the kit or the letter that has to go back. One pocket for pens, one for "
          "paper, one for the phone, and nothing loose at the bottom - a bag you can empty in one "
          "look is a bag you stop losing things in."),
    entry('ask-teacher', (('teacher', 'tutor', 'lecturer',
                           # the lesson itself names the person you would ask: "how do i ask a
                           # question in class" had no answer at all, and the same words carry
                           # "i dont understand what we did in class". The lesson words stay in
                           # THIS group only: a phrase in both groups is a pair on its own, so
                           # every "how do i ... in class" line scored four and got this row -
                           # bag tidy, group work, sit still, a raised hand, handwriting, a
                           # bully, a phone going off, each of which has its own answer.
                           'in class', 'after class', 'in the lesson', 'in a lesson',
                           'office hours', 'my class', 'in lectures'),
          # "how do i ask a teacher for help" and "how do i email my teacher" reached the
          # career table - "a teacher" is in its key for "what gcses do i need to be a teacher" -
          # and came back with the PGCE route. The asking shapes belong here, so they are named:
          # a question, a message, a word after class.
          ('ask for help', 'struggling', 'behind', 'help', 'fail', 'talk', 'email',
           'home', 'dont get it', "don't get it", 'shy', 'scared', 'nervous', 'afraid',
           'embarrassed', 'dont understand', "don't understand", 'confused', 'stuck',
           'ask', 'asked', 'asking', 'a question', 'questions', 'the question', 'message',
           'send an email', 'get help', 'extra help', 'more help',
           # saying something out loud in the lesson is the asking direction, and these lines
           # had a decent answer here before the class words left this group.
           'hand up', 'raise my hand', 'raised hand', 'wasnt picked', "wasn't picked",
           'never get picked', 'not picked',
           'answer in class', 'answering in class', 'speak up in class',
           'one to one', 'reply', 'behind on',
           # asking for feedback is the asking direction: without these the line was the
           # giving-feedback card in language.py, whose example is a manager and a late report
           'ask for feedback', 'asking for feedback', 'for feedback', 'what to improve')),
          'Ask in person after class with one specific thing ("I get the formula but I can\'t do the'
          ' last question on the sheet"), and say what you\'ve already tried. Teachers help far more'
          ' often than students expect, and an email the same day saying thank you makes them'
          ' remember you next time.',
          # A parent whose child's teacher has been in touch is not the student: that is the
          # school-email question (bot/knowledge/wording.py, email-to-teacher).
          # a lesson being noisy or a class being hard to sit in is not asking for help, and
          # "how do i stop talking in class" went from a punt to this row once the lesson words
          # joined the key
          # "in class" made every class how-to this row's. The notes, concentration and
          # attention answers each own their line, so the words that name those jobs stand this
          # one down - it costs nothing here, because the ask still has to carry ask/question/
          # message.
          avoid=("take notes", "taking notes", "make notes", "notes in class", "note taking",
                 "notes", "focus", "focusing", "pay attention", "paying attention", "attention",
                 "concentrate", "concentrating", "concentration", "listen better",
                 "revise", "revising", "revision", "revising for", "exam", "exams", "mock",
                 "mock exam", "marks", "mark scheme",
                 "stop talking", "talking in class", "chatting", "chat", "distracting",
                 "call out", "calling out", "shouting out", "loud in class", "noisy class",
                 "emailed me", "email me", "emailing me", "rang me", "called me", "my son",
                 "my daughter", "my child", "my kid", "my kids", "his teacher", "her teacher",
                 "their teacher", "parents evening", "parent evening", "parent teacher",
                 "parent-teacher", "head teacher", "headteacher", "my boy", "my girl")),
    # "how much does a masters cost" was a live-prices hedge: the pass-mark row owns the degree
    # and stands down on "how much does", the money rows own the bills of a household, and the
    # postgraduate price is a fixed range like the undergraduate one, not a live quote.
    entry("masters-cost",
          (("masters", "master's", "msc", "ma ", "mba", "postgraduate", "postgrad",
            "postgraduate degree", "taught masters"),
           ("cost", "costs", "how much", "fees", "fee", "tuition", "price", "expensive",
            "afford", "worth it", "worth", "loan", "bursary", "scholarship", "funding",
            "save up", "part time", "part-time")),
          "For a UK student, a taught masters is usually £9,000 to £15,000 for the year - around "
          "£8,000 to £12,000 for a classroom subject, £12,000 to £20,000 for a lab one, and an MBA "
          "can be £25,000 or more - plus living costs for a full-time year. A postgraduate "
          "master's loan from Student Finance covers up to about £12,500 of it, paid in three "
          "instalments, and it does not depend on your income. Ask the department about "
          "scholarships and fee waivers before you ask a bank, and check whether the course runs "
          "part time, because that spreads the cost over two years while you work.",
          # a scholarship essay is a writing ask, and the undergraduate money is its own rows
          avoid=("personal statement", "statement of purpose", "cover letter", "essay",
                 "undergraduate", "bachelors", "bachelor", "a level", "a-level",
                 "student loan", "maintenance loan", "rent", "deposit"),
          bias=1),
    entry('university-apply', (('university', 'uni', 'college application', 'personal statement', 'ucas'),
          ('apply', 'application', 'write', 'how', 'should', 'start', 'deadline')),
          "Apply on UCAS: one form, up to five courses, the personal statement and a reference, "
          "with 15 October for Oxford, Cambridge, medicine and veterinary science and mid-January "
          "for everything else. The statement is the part people worry about, and the rule is to "
          "start with the subject, not your childhood: what you have read, built or done that made "
          "you want it, then what you want to learn next. Two drafts and one reader who knows the "
          "subject beats five drafts alone.",
          # "how do i apply for a university place" is this row, not the school-place row it tied
          # with: the council form is for a school, and the university is UCAS. How long the
          # statement has to be is the length row's question.
          avoid=("how long", "how many words", "how many characters", "word count", "characters",
                 "maximum length", "how many lines",
                 # "should i go to uni" is the decision card's question (university-worth), not
                 # the application's: the apply row has "should" in its key and took it
                 "should i go", "shall i go", "is it worth", "worth it", "worth going",
                 "do i need", "not worth", "alternatives", "if i go", "whether to go"),
          bias=1),
    # "how long should a personal statement be" was the tax-deadline card, which is the wrong
    # subject and a confident one. The limits are fixed and famous, so the length is its own
    # answer rather than a line in the UCAS card (@loyal-zebra, #6152).
    # "what is ucas" was the search hedge. The name is an acronym nobody explains, so the
    # question is a definition and not an application.
    entry("what-is-ucas",
          (("ucas", "ucas form", "ucas application", "ucas account"),
           ("what is", "whats", "what's", "what does", "stand for", "mean", "means",
            "how does it work", "explain", "what do i need")),
          "UCAS is the one form that covers almost every full-time UK degree: you fill it in once, "
          "add up to five courses, write a personal statement, and a teacher or employer adds a "
          "reference. The fee is about \u00a328. The early deadline is 15 October for Oxford, "
          "Cambridge, medicine, dentistry and veterinary science, and the main one is in "
          "mid-January. Offers come back between then and May, and you pick a firm choice and an "
          "insurance one.",
          avoid=("points", "tariff", "how many points", "clearing", "personal statement length",
                 "how long", "how many words"),
          bias=1),
    entry('ucas-statement-length',
          (('personal statement',),
           ('how long', 'how many words', 'how many characters', 'word count', 'words',
            'characters', 'maximum', 'limit', 'length')),
          'Four thousand characters including spaces, or forty-seven lines - whichever you hit '
          'first - and that is one side of A4 in plain prose. Write the draft long, then cut: '
          'the sentences that say nothing ("ever since I was young") go first, then any '
          "description of the course you can read on the university's own page. Paste it into "
          'a character counter rather than guessing, and leave room for the edit.',
          avoid=('cv', 'c v', 'resume', 'r\u00e9sum\u00e9', 'tax return', 'taxes')),

    entry('maths-homework', (('maths', 'math', 'algebra', 'equation', 'equations', 'geometry', 'homework problem'),
          ('help', 'solve', 'understand', 'explain', 'how', 'stuck')),
          "Ask them to show you the first step they'd try, then work one example together and let"
          " them do the next alone: that's the bit that teaches. If they're stuck on why, not how,"
          ' draw it; almost every school maths idea has a picture (a bar for fractions, a graph for'
          ' equations).',
          # "im helping my son with maths homework" is a homework-battle line (homework-child), and
          # a homework refusal is not a maths problem
          avoid=('helping my', 'my son', 'my daughter', 'my kid', 'my child', 'my children',
                 'wont do', "won't do", 'refuses', 'battle', 'every night', 'nagging',
                 'homework-child')),
    entry('spelling-improve', (('spelling', 'spell', 'spelling mistakes', 'grammar'),
          ('improve', 'better', 'how', 'fix', 'help')),
          'Keep a list of the words you actually get wrong (not a generic list), and test yourself'
          ' on those five at a time by writing them, saying them and covering them. For the ones'
          ' that refuse to stick, break them into a silly phrase or find the small word inside the'
          ' big one (there\'s "a rat" in separate).'),
    entry('school-presentation', (('presentation', 'talk', 'speech'),
          ('school', 'class', 'students', 'assembly', 'nervous')),
          'Write the first sentence and the last sentence first, then three points in between, one'
          ' card each. Practise out loud standing up, once to a person and once to a wall, and print'
          ' the cards in big letters: looking up at people is what makes a school talk go well, and'
          " you can't look up at a phone.",
          # "how do i stop talking in class" is about being quieter in lessons, not about giving
          # a talk: "talk" plus "class" read it as a school speech, and the person was told to
          # write the first and last sentence of a presentation they were not making.
          avoid=("stop talking", "talking too much", "talk too much", "chatting", "chatty",
                 "chatter", "chatterbox", "blurt", "blurting", "keep talking", "distracting",
                 # An empty room is not a talk to give, at school either: "nobody talks to me at
                 # school" got "write the first sentence and the last sentence of your talk",
                 # because "talk" plus "school" is a speech. The same fence as the work row.
                 "nobody talks", "no one talks", "nobody speaks", "no one speaks",
                 "talks to me", "speaks to me", "talk to me", "speak to me",
                 "nobody will talk", "no one will talk")),

    # A student who talks too much in lessons had no row of its own. The chats-to-leave rows took
    # it off "stop talking" and the school-talk row off "talk" and "class", so the answer was a
    # script for ending a phone call or a plan for a speech. This is the classroom question.
    entry("talkative-in-class",
          # a lecture, a seminar and an assembly are the same room and the same ask, and the
          # fence in `TALKING_IS_NOT_A_CHAT` names all three: without them here the line was
          # stood down from the call-ending cards and had nowhere to go but an acknowledgement
          # ("stop talking in assembly") or the search hedge ("during a lecture", "in seminars")
          (("class", "classes", "classroom", "lesson", "lessons", "school", "teacher",
            "lecture", "lectures", "seminar", "seminars", "assembly", "assemblies",
            "tutor", "tutors", "tutorial", "tutorials", "playground", "playgrounds"),
           ("stop talking", "talk too much", "talking too much", "talk to much", "chat too much",
            "chatting", "chatty", "chatter", "chatterbox", "blurt", "blurting", "keep talking",
            "quiet", "quieter", "distract", "distracting", "shouting out", "too loud")),
          "Sit where the chat cannot start: front row, or beside someone you do not talk to, and "
          "ask the teacher to move you, which is a normal request and not a confession. Keep a "
          "corner of the page for the things you want to say and hold them to the end of the "
          "lesson - most of them keep, and the good ones come back to you. If it is answers "
          "blurting out, count to three and write the answer down first; the urge drops once it "
          "is on the page.",
          # a talk to give, a classmate who is unkind to them and an exam are other lines
          # `assembly` is not in this fence any more: it is a room where the talking happens, so
          # the row has to answer it. A speech or a presentation is still another line - neither
          # carries a talking word, so neither can reach this row anyway - and the rest is the
          # exam fence.
          avoid=NOT_AN_EXAM + ("classmate", "classmates", "presentation", "presentations",
                               "speech", "exam", "exams", "revision", "revise",
                               "test", "grade", "grades")),

    # "how do i memorise quotes for english lit" was a shrug: memorise-lines answers a speech
    # or a part, and a quote is a different job.
    entry("memorise-quotes",
          (("quotes", "quote", "quotations", "key quotes"),
           ("memorise", "memorize", "memorising", "learn", "remember", "english lit", "essay",
            "exam", "revise", "revision", "how")),
          "Pick eight to ten short ones you can use for more than one theme, and learn them in "
          "fours to six words rather than whole speeches - \"a plague o' both your houses\" is "
          "learnable, a fifteen-line speech is not. Say each aloud, look away and say it, then "
          "write it from memory; do three a day and cycle back through the rest. Practise the "
          "sentence you will build around it, because the quote alone earns nothing without the "
          "two lines of analysis after it.",
          avoid=NOT_AN_EXAM),

    # "i keep running out of time in exams" got an echo: nothing keyed the clock.
    entry("exam-timing",
          (("running out of time", "out of time", "time in exams", "didnt finish",
            "didn't finish", "no time left", "ran out of time", "finish the paper"),
           ("exam", "exams", "paper", "test", "revision", "how", "help", "tips", "stop")),
          "Give each question the minutes it is worth: one mark is about one minute, so a "
          "ten-mark question gets ten. Write the clock time you must move on by in the margin "
          "before you start, and move on when it arrives even if the answer is unfinished - a "
          "half answer plus the next question beats a perfect first one and three blanks. Read "
          "the whole paper first, do the question you know best, and keep the last five minutes "
          "for checking names, units and whether every question has an answer.",
          avoid=NOT_AN_EXAM,
          # the water shut-off card grew the words "running out" and outranked this one on
          # "i keep running out of time in exams", which is the exam clock and not a burst pipe
          bias=4),

    # "should i take a gap year" was "not mine to decide": it is a planning question.
    entry("gap-year",
          (("gap year", "year out", "take a year off", "defer", "deferring"),
           ("should", "worth", "take", "better", "do", "plan", "uni", "university", "offer",
            "money", "work",
            # "what is a gap year" names the thing and asks what it is: the row's own word is in
            # the first group, so the definition question is safe to accept here.
            "what is", "whats", "what's", "mean", "means", "definition", "define", "explain")),
          "It is worth it when there is a reason you can name: a paid job that builds a skill, a "
          "season abroad with the cost worked out, or time for something you could not do later. "
          "Ask your university in writing to defer - most hold the offer for one year if you ask "
          "before the start date - and keep the place in mind, because reapplying is harder than "
          "deferring. Work out the money first: a year abroad is cheap only if the flights and the "
          "first month are paid for before you go.",
          avoid=NOT_AN_EXAM),

    # "my teacher marks me down and i dont know why" was the stain-removal answer: "marks" and
    # "down" are everyday words, so this key needs the marking phrases, not the words.
    entry("marks-question",
          (("marked me down", "marks me down", "marking me down", "marks down", "low marks",
            "bad marks", "marks are low", "marked down", "unfair mark", "unfair marks",
            "marks dont make sense", "dont understand my marks", "teacher marks"),
           ("why", "teacher", "ask", "unfair", "lower", "explain", "dont know", "appeal",
            "grade", "grades", "feedback", "marked")),
          "Ask for the mark scheme, not for a favour: \"could I see which part of question 3 "
          "lost the marks?\" That is a normal request, and a good teacher will show you. Then ask "
          "for one example of what a full-mark answer looked like and rewrite that paragraph with "
          "it in front of you. If the marks still look wrong against the published scheme, ask the "
          "school for a remark in writing rather than arguing in the corridor.",
          avoid=NOT_AN_EXAM + ("stain", "washing", "shirt", "carpet", "wood", "paint")),

    # "how much does uni cost in total" was the personal statement: the money question had no home.
    entry("uni-cost",
          (("uni cost", "university cost", "cost of uni", "cost of university", "tuition fee",
            "tuition fees", "student debt", "how much does uni", "how much does university"),
           ("much", "total", "cost", "costs", "pay back", "worth", "how", "year", "all")),
          "In England the fee is £9,250 a year, so a three-year course is about £27,750, and "
          "living costs add roughly £9,000 to £12,000 a year on top. Nobody pays it up front: it "
          "is a loan repaid at 9% of what you earn above about £25,000, and what is left is "
          "written off after 40 years, so the monthly figure matters far more than the headline. "
          "Check the maintenance loan for your household income, and pay the deposit for "
          "accommodation out of the first instalment rather than a credit card.",
          avoid=NOT_AN_EXAM),
    # "how do i remember what i read" reached nothing: reading and remembering is its own skill.
    entry("remember-reading",
          (("remember what i read", "remember what i've read", "remember a book",
            "remember a chapter", "remember reading", "take notes from a book",
            "make notes from a book", "read and remember", "reading for study",
            "how do i remember",
            # the page that will not stay in: "retain what i read", "nothing i read sinks in",
            # "i read a book and cant remember any of it". These are the shapes of this same
            # question, so they belong in this key rather than in a second table answering it
            # in different words - two copies of one answer drift apart.
            "retain", "take in", "takes in", "sink in", "sinks in", "sticks",
            "cant remember what i read", "can't remember what i read",
            "dont remember what i read", "don't remember what i read",
            "forget what i read", "nothing i read",
            # "i read a book and cant remember any of it" names no word about memory that the
            # first group already had, so the plain shapes come in too; the second group keeps
            # them on the page, and this is one question, not a second answer.
            "cant remember", "can't remember", "dont remember", "don't remember",
            "remember any of it", "forget", "forgetting", "forgot"),
           ("read", "reading", "book", "chapter", "textbook", "notes", "remember", "memory",
            "revision", "revise", "study", "keep", "how", "page", "pages", "article",
            "paragraph")),
          "Read a section, then close the book and say its three points out loud before going on - "
          "rereading feels like study but the recall is what sticks. Turn each heading into a "
          "question first (\"what is a supply curve?\") and answer it from memory, then write one "
          "line per page in your own words. Come back to those lines after ten minutes, the next "
          "day and a week later, and you keep most of it with far less total time.",
          guard=_the_page_is_what_was_forgotten,
          # "cant remember" on its own is not a reading question: what is forgotten is usually a
          # person, a name or a job to do, and each of those has its own answer. So the words that
          # say what was forgotten are held out and this row keeps the page.
          avoid=("phone number", "pin", "password", "birthday", "name of", "surname",
                 "my ex", "get over", "move on", "grief", "grieving", "bereaved", "died",
                 "death", "passed away", "him", "her", "someone", "somebody", "breakup",
                 "break up", "affair", "cheated", "how to", "names", "anniversary", "word",
                 "spelling", "where i put", "where i left", "appointment", "medication",
                 "tablet", "keys", "glasses", "wallet",
                 # a kitchen line reached this row: "how do i keep a barbecue from sticking" is
                 # about a grill, and "sticks" and "keep" are both in the key above, so naming the
                 # kitchen words in the line is what keeps the page the page.
                 "barbecue", "barbecues", "bbq", "barbeque", "grill", "grilling", "pan", "pans",
                 "wok", "pasta", "rice", "dough", "pastry", "meat", "chicken", "fish",
                 # a batter in a pan is not a page either: "my crepes keep sticking" and "my
                 # pancakes keep sticking" carry both "keep" and "sticking", and were told to
                 # close the book and say its three points out loud.
                 "pancake", "pancakes", "crepe", "crepes", "batter", "waffle", "waffles",
                 "yorkshire", "yorkshires", "yorkshire pudding", "pikelet", "pikelets",
                 "cooking", "cook", "recipe", "oven", "sauce", "gravy", "soup",
                 # `sticks` and `sticking` are words of the key, and a shower curtain that sticks
                 # to you or a screen protector that will not lie flat reached this row for it.
                 # Nothing about a page is in those lines, so the things that stick stand it down.
                 # "my bread keeps sinking in the middle" reached this row on "sinking in": a
                 # loaf that drops is a bake, and the kitchen words above were about the pan
                 "bread", "loaf", "loaves", "cake", "cakes", "baking", "bake", "batter",
                 "sponge", "souffle", "risen",
                 "curtain", "curtains", "shower", "shower curtain", "screen protector", "phone",
                 "laptop", "phone screen", "cling film", "bin bag", "zip", "drawer", "door",
                 "window", "sticker", "stickers", "tape", "plaster", "saucepan", "frying pan",
                 "pasta", "rice", "pan", "pans", "dough", "pastry",
                 # A date of ours the partner forgot is a complaint about them, not a page that
                 # will not stay in: "my partner keeps forgetting our plans" is the composer's
                 # grievance line, and the reading answer here read "forgetting" as the subject.
                 "our plans", "our dates", "partner", "husband", "wife", "marriage",
                 # "how do i cancel a subscription i forgot about" reached this row on "forgot"
                 # and the bare "how" the key carries, and was told to close the book and say its
                 # three points out loud. A thing you forgot to do - a payment, a renewal, a
                 # contract - is a money or admin question, whatever the verb.
                 "subscription", "subscriptions", "cancel", "cancelling", "canceling",
                 "direct debit", "insurance", "bill", "bills", "renewal", "renew", "payment",
                 "payments", "policy",
                 # "make it stick" is about carrying something on, and it shares the word "stick"
                 # with the knowledge that sticks. A page is named in a reading line ("nothing i
                 # read sticks"), so the bare phrases are held out and the page keeps its answer.
                 "make it stick", "make it stick this time", "stick with it", "stick at it",
                 "keep at it", "keep it up", "keep going")),
    # "what should i do if i fail my exams" was getting the procrastination answer.
    entry("fail-exams",
          (("fail my exams", "failed my exams", "fail my exam", "failed my exam", "fail my a levels",
            "failed my a levels", "fail my gcses", "failed my gcses", "fail the year",
            "failed the year", "failed my degree", "fail my degree", "did badly in my exams",
            "did badly in my exam", "flunked", "i failed", "get a remark", "ask for a remark",
            "remark my exam", "a remark"),
           ("what", "should", "do", "now", "next", "resit", "retake", "remark", "appeal",
            "university", "college", "sixth form", "year", "help",
            # "i failed my exams" with nothing else is still the question
            "i", "my")),
          "Speak to your school or college on results day, not next month: they can tell you the "
          "resit date (usually November for maths and English, the following summer for most "
          "others) and whether the university or college will hold your place, which plenty will "
          "once they know. If you were a mark or two off a grade boundary, a remark can be worth "
          "it, but it can also go down, so ask the exams officer what the risk is. Failing one "
          "paper is not failing the year, and a plan made this week beats a summer of dread.",
          # the revision entries key on "exam" too, and this line names the thing that already
          # happened, so it steps in front of them
          bias=2,
          # a missed offer is results day's line: that answer says what to do about clearing and
          # the university, and this one is about resits and remarks
          avoid=NOT_AN_EXAM + ("missed my offer", "missed the offer", "missed my place",
                               "clearing", "my offer", "firm choice", "insurance choice",
                               "rejected by", "rejected me"),
          # a bare failure names no exam, so it is about the thing in front of them
          guard=lambda understood: not _a_failure_of_something_else(understood)),
    # "what is the difference between college and university" reached nothing: applying to
    # university had an answer and the choice in front of it did not.
    entry("college-or-university",
          (("college or university", "university or college", "difference between college",
            "college and university", "should i go to college", "college instead of university",
            "is college better than university", "btec or a levels",
            "sixth form or college", "what is college"),
           ("difference", "better", "worth", "should", "which", "or", "need", "instead of",
            "what", "why", "choose", "decide", "go to", "matter")),
          "College is further education: A-levels, BTECs, T-levels, apprenticeships and access "
          "courses, usually for 16 to 18 year olds and mostly free until 19. University is a "
          "degree, three or four years, with tuition loans and maintenance loans to pay for it. "
          "The route that works for most people is whichever gets you the qualification the job "
          "you want actually asks for: a trade, nursing or design can go straight from college "
          "into work, while law, medicine and teaching need the degree. College first is not a "
          "step down - an access or foundation year costs less than a wasted degree and keeps the "
          "university route open.",
          # how to apply, the student loan and the cost of university are their own answers
          avoid=("how do i apply", "ucas", "student loan", "student finance", "tuition fee",
                 "how much does university cost", "open day", "personal statement")),
    # "how do i write a conclusion" was a shrug: the essay entry answers the plan and the
    # proofreading entry the mistakes, and the last paragraph had nobody.
    entry("essay-conclusion",
          (("conclusion", "conclusions", "conclude", "ending", "sum up", "summarise",
            "summarize", "wrap up", "last paragraph", "final paragraph",
            # the essay entry answers "how do i write" for any essay word, so the ending has to
            # name itself as a phrase to beat it
            "strong conclusion", "good conclusion", "essay conclusion", "write a conclusion",
            "conclusion for", "conclusion of", "conclusion to"),
           ("essay", "essays", "dissertation", "coursework", "assignment", "report", "write",
            "writing", "how", "start", "phrases", "words", "should", "what", "need", "good",
            "strong", "help")),
          "The last paragraph is where you say what it adds up to, not what you have already "
          "said: one sentence that answers the question in the title, one on the strongest "
          "evidence that got you there, then the wider point or what should happen next. Four or "
          "five sentences is enough, with no new evidence and no new quotation - if a fact belongs "
          "in the conclusion, it belongs in the body first.",
          # the ending of anything not written is not the last paragraph of an essay; see the
          # note on _the_ending_is_written above
          guard=_the_ending_is_written,
          # a conclusion you reached about a decision is not an essay paragraph
          avoid=("i came to the conclusion", "came to the conclusion", "test", "experiment",
                 # "Ending" folds to "end", the commonest verb in the other world: "how did the
                 # first world war end in 1918" and "how did the second world war end" came back
                 # as the last-paragraph tip. An ending in history is not an ending in an essay.
                 "war", "wars", "battle", "battles", "revolution", "armistice", "trench",
                 "trenches", "empire", "1914", "1918", "1939", "1945",
                 # "ending" folds to "end", so this row took any "how do i end ..." line that
                 # had one of "how", "what" or "should" in it: "how do i end a chat at a party"
                 # was told how to write the last paragraph of an essay. An ending that is a
                 # conversation, a call or a party is not a paragraph.
                 "chat", "chats", "chatting", "conversation", "conversations", "phone call",
                 "phone calls", "party", "parties", "relationship",
                 "tenancy", "lease", "contract", "subscription", "argument", "friendship",
                 # "how do i end things with my boyfriend" was an essay conclusion too
                 "end things", "boyfriend", "girlfriend", "partner", "husband", "wife",
                 "break up", "breaking up", "divorce", "marriage", "my marriage", "fiance",
                 "fiancee",
                 "lab report", "results", "data", "conclusion of my", "doctor", "gp",
                 "diagnosis",
                 # "we both end up cross" is the verb `end`, not the noun `ending`, and a child
                 # plus homework is the homework routine's line: "im helping my son with his
                 # maths homework and we both end up cross" came here on "ending" and "help"
                 "end up", "ended up", "ends up", "ending up", "homework", "son", "daughter",
                 "child", "children", "kids", "kid", "maths", "times tables",
                 # "what is end of life care" is "ending" plus "what" like every other line
                 # here, and it was answered with how to write a last paragraph - the one line
                 # on this row that must never reach it. The words of dying and of the care that
                 # goes with it stand the essay down, so the palliative card (caring.py) and the
                 # loss composer answer instead.
                 "end of life", "end-of-life", "life care", "dying", "died", "dies",
                 "dying", "palliative", "hospice", "hospices", "terminally", "terminal",
                 "bereavement", "grief", "funeral", "my mum is", "my dad is",
                 "my mother is", "my father is",
                 # "ending" folds to "end" as well, so "how do i end a fast", "how do i end a
                 # poem" and "how do i end a sentence" were all told how to write the last
                 # paragraph of an essay. What comes after the verb is the thing being ended,
                 # and it says which card the line belongs to: a fast is the breaking-a-fast
                 # answer, a chapter or a book is a story, and a sentence is punctuation.
                 "end a fast", "end my fast", "end the fast", "end this fast",
                 "end a diet", "end my diet", "end the diet",
                 "end a poem", "end my poem", "end the poem", "end a verse",
                 "end a sentence", "end my sentence", "end a paragraph", "end my paragraph",
                 "end a chapter", "end my chapter", "end a book", "end my book",
                 "end a story", "end my story", "end a novel", "end my novel",
                 # The same verb, and the thing being ended is a conversation with someone in
                 # the room: "what do i say at the end of a job interview" and "how do i end a
                 # meeting well" were both told to write a last paragraph with one sentence that
                 # answers the question in the title. An interview, a meeting, a shift and a
                 # lesson are not paragraphs, and `work.py` has the interview family
                 # (`interview-prep`, `interview-take`, `phone-interview`, ...) to answer them.
                 "interview", "interviews", "interviewing", "interviewer", "job interview",
                 "panel", "appraisal", "one to one", "1:1",
                 "end a meeting", "end the meeting", "end my meeting", "meeting",
                 "end a shift", "end my shift", "end the shift", "end a call", "end the call"),
          # the essay-plan row keys "essay" and "write" as well, so it took "how do i write a
          # conclusion for an essay" and answered the plan for the whole essay: the line names
          # the last paragraph, so the last paragraph steps in front of it
          bias=1),
    # "what is a pass mark at university" reached the GCSE 9-to-1 answer, which is the right
    # entry for a school result and the wrong one for a degree.
    # "should i go back to uni at 40" was answered "A degree passes at 40% in most UK
    # universities": the pass-mark row keys the bare number 40, so an age read as a percentage and
    # the mature-student question had no card of its own at all. The phrases below are the age
    # said as an age; the pass-mark row takes "at 40" out of its own reach.
    entry("mature-student",
          (("go back to uni", "go back to university", "going back to uni",
            "going back to university", "back to uni", "back to university",
            "back to studying", "back to study", "mature student", "mature students",
            # college is the same question as university and it was not in the key: "should i go
            # back to college at 40" was a "Can't call that one for you" greeting
            "go back to college", "back to college", "going back to college",
            "college at 30", "college at 40", "college at 50", "evening class", "evening classes",
            "study as an adult", "degree as an adult", "evening degree", "part time degree",
            "open university", "study at night",
            # the age is written after the subject, not after "back to": "is it worth going to
            # university at 30" was answered with the cost of a 30C wash
            "university at 30", "university at 40", "university at 50", "uni at 30", "uni at 40",
            "uni at 50", "degree at 30", "degree at 40", "in my 30s", "in my 40s", "in my 50s",
            "late in life"),
           ("40", "30", "35", "45", "50", "older", "later", "at my age", "worth", "should",
            "how", "as an adult", "after kids", "after children", "career change", "money",
            "cost", "afford")),
          ("Going back later is common, and the money is the first thing to check: a "
           "full-time degree is three years without a salary, so most people do it part time, one "
           "module at a time, or with the Open University. Student finance counts you as an "
           "independent student, so your own income decides the loan, and a course can credit "
           "what you already know. Do one evening class first, before you commit to three years."),
          # what a degree passes at, what to study and how to apply are the other rows
          avoid=("pass mark", "passing mark", "pass", "passes", "percent", "percentage", "grade",
                 "grades", "classification", "2:1", "first class", "ucas", "personal statement",
                 "student loan", "tuition fee", "tuition fees", "how do i apply", "open day")),
    entry("university-pass-mark",
          (("university", "uni", "degree", "degrees", "undergraduate", "bachelors", "masters",
            "msc", "bsc", "postgrad", "postgraduate", "module", "modules", "semester",
            # a phone writes "2:1" as "2 1" and the colon is gone
            "2:1", "2.1", "2:2", "2 1", "2 2", "first class", "upper second", "lower second",
            "distinction", "merit", "classification", "pass mark", "passing mark"),
           ("pass mark", "pass", "passing", "passed", "fail", "fails", "failing", "mark", "marks",
            "40", "50", "60", "70", "percent", "percentage", "average", "need", "what",
            "how much", "grade", "grades", "worth", "count", "counts", "resit", "resubmit",
            "good", "is", "are", "dont", "mean", "means")),
          _university_pass_mark,
          # a school result, a cost or an application is a different answer
          avoid=("gcse", "gcses", "a level", "a-level", "alevel", "alevels", "sixth form",
                 "year 11", "year 10", "sats", "11+", "secondary school", "high school",
                 # what to study is the course choice, not what a degree passes at: "what
                 # should i study at university" shares "university" and "what" with this row
                 # and the class answer is no answer to it at all.
                 "what should i study", "should i study", "what to study",
                 "what should i take", "what should i do at uni",
                 "what should i do at university",
                 "tuition fee", "fees", "student loan", "student finance", "maintenance loan",
                 "how do i apply", "ucas", "personal statement", "open day", "is university",
                 "is uni", "worth going", "how much does",
                 # "is a degree worth it" is the decision card, not the pass mark
                 "worth it", "is it worth", "worth doing", "worth the money", "worth the debt",
                 # an age is not a percentage: "should i go back to uni at 40" is the mature
                 # student question, which has its own row just above
                 "at 40", "at 30", "at 50", "at 45", "in my 40s", "in my 30s", "in my 40's",
                 "go back to uni", "back to uni", "back to university", "mature student",
                 *_A_DEGREE_OF_HEAT,
                 # a route into a job is asked with a degree in it - "do i need a degree to be a
                 # social worker" is the job's entry requirements, not what a degree passes at
                 "do i need a degree", "need a degree to", "degree to be", "to be a", "to be an",
                 "become a", "become an", "get into", "qualify as", "train as",
                 # "how much is a first class stamp" was answered with what a degree passes at:
                 # the row keys "first class", and "how much" is one of its wants, so the post's
                 # word reached the degree's answer. "first class" is the train's word as well,
                 # so anything about a stamp, a letter or a seat is the post office's or the
                 # ticket's question and this row stands down for it.
                 "stamp", "stamps", "postage", "post office", "postbox", "post box",
                 "royal mail", "envelope", "envelopes", "signed for", "recorded delivery",
                 "first class stamp", "second class stamp", "first class post",
                 "second class post", "train ticket", "plane ticket", "flight", "seat",
                 "carriage", "railcard")
                 # a line that asks what to wear only says "degrees" as the weather it is dressing
                 # for: "its 35 degrees, what should i wear to a wedding" was the pass-mark card,
                 # and 35 is a heat wave, not a mark.
                 + A_WHAT_TO_WEAR,
          # a bare "what is a pass mark" ties level with the GCSE answer, which is the right one
          # for a school result: the degree answer asks the university word and wins the tie.
          bias=1,
          # "the lamb is 2.2 kilos not 2" is a slow roast with the joint weighed, and the "2.2"
          # of a degree class was the whole of the match. A figure with a unit on it is an
          # amount, not a class, so this row stands down and the cooking card answers the line.
          # a figure with a unit on it is a measurement, not a degree: "wedding in italy and 35
          # degrees, what do i wear" was answered with what a degree passes at.
          guard=lambda understood: (not quantity.a_figure_with_a_unit(understood)
                                    and _the_degrees_are_heat(understood))),

    entry("course-choice",
          (("which course", "what course", "course to study", "choose a course", "pick a course",
            "choosing a course", "which degree", "what degree", "choose a degree",
            "university course", "which university", "choose a university",
            "what to study at university", "what to study at uni",
            # the same question said with the verb in the middle: "what should i study at
            # university" was answered with what a degree passes at. Not a bare "study at
            # university", which is "how do i study at university" - the study-skills card
            "what should i study", "what should i do at university", "what should i do at uni",
            "subject to study", "what subject"),
           ("should i", "how do i", "help", "advice", "choose", "pick", "decide", "between",
            "better", "best", "worth", "difference", "study", "do")),
          "Choose on the modules in years two and three, not the course title: read them, and if "
          "half of them bore you the course is wrong whatever it is called. Then check the entry "
          "requirements against your predicted grades, the contact hours and whether a placement "
          "or a year in industry is offered, and the graduate outcomes page for where last year's "
          "students went. Go to an open day and sit in one lecture if you can, because a "
          "department feels like something on the day. Apply to five with one dream and two safe "
          "choices, and keep the one you would be happy at if the grades go wrong.",
          ask=("should i", "how do i", "help", "advice", "choose", "pick", "decide", "between",
               "better", "best", "worth", "difference", "study"),
          # whether university is worth it, and the application itself, are other answers, and
          # so is which subjects to take at school: "what subject should i study at a level" is
          # the entry-requirements card, and "what subject" alone was taking it
          avoid=("university worth", "worth it", "ucas", "personal statement", "apply", "clearing",
                 "gap year", "a level subject", "a levels to", "gcse",
                 "a level", "a levels", "a-level", "as level", "gcse", "gcses")),
    entry("clearing",
          (("clearing", "clearing place", "clearing course",
            # not "university place" on its own: "how do i apply for a university place" is the
            # UCAS row's line, and this row took it on "university" and "place".
            "a place at university", "which university", "adjustment"),
           # "how do i clear my overdraft" is the same words as "how do i clear a course": the
           # matcher reads the line's "clear" as this entry's "clearing", so "how do i" on its
           # own is not enough to reach the UCAS answer. A real question carries university,
           # ucas, course, apply, place, grades or an offer.
           ("what is", "how does", "university", "ucas", "uni", "college", "course", "apply",
            "get in", "get a place", "get onto", "find", "place", "vacancy", "vacancies",
            "missed", "grades", "worse than", "not got in", "offer", "adjustment",
            # "is clearing still open" and "when does clearing start" ask about the dates rather
            # than about how to use it, and a key needs two of its own words, so the opening
            # words are here beside the applying ones
            "open", "opens", "start", "starts", "begin", "begins", "still")),
          "Clearing is how you get a place when you have no offer or your grades missed: from "
          "July to October, search the official UCAS Clearing service for courses with vacancies, "
          "then ring the university yourself with your UCAS personal ID, your grades and the "
          "course code - an offer made on that call is a real offer. Have the list and your "
          "grades in front of you, ring three or four in one morning, and add the one you want in "
          "UCAS Track before you relax. If you already have a place and want a better one, that "
          "is adjustment, which is the same search with a deadline of five days.",
          ask=("what is", "how does", "how do i", "apply", "get", "find", "place", "vacancy",
               "missed", "grades", "when", "still", "open"),
          # results day and a failed exam are their own answers
          # "cache" is the same word as "clearing" to the matcher, so "how do i clear my cache"
          # was told about UCAS Clearing; the browser cache has its own row in technology
          # A word list of caches and drains was the first attempt and it was the wrong shape:
          # the verb is the problem, and "how do i clear my overdraft" was answered with "Clearing
          # is how you get a place when you have no offer". Nobody writes Clearing with an object
          # after it, so `clear <determiner> <noun>`, `clear out`, `clear up` and money cleared
          # without an object are the stand-down, and no noun list has to be kept up to date.
          avoid=("failed my", "resit", "remark", "a level results day", "my teacher",
                 "cache", "cached", "cookies", "browser", "chrome", "safari", "app",
                 "clear my", "clear the", "clear a", "clear an", "clear our", "clear your",
                 "clear out", "clear up", "clearing my", "clearing the", "clearing out",
                 # `clear space` is the object-after-the-verb shape with a mass noun: "how do i
                 # clear space on my phone" and "on my laptop" were reached by "clear" beside
                 # "space" and answered with a place at university
                 "clear space", "clear some space", "clear storage", "clear enough",
                 "cleared my", "cleared the", "clear some", "clear any",
                 "clear debt", "clear debts", "clear arrears", "clear balance",
                 "clear credit card", "clear loan", "clear loans", "clear mortgage",
                 "clear overdraft", "clear it",
                 # a pane of glass is not a university place: "how do i clear condensation off
                 # the windows" was answered with the Clearing card, because "clear" is room left
                 # on a drive in that line and "windows" is the operating system, and neither
                 # reading is the glass. The glass words stand the card down here and in devices.py.
                 "condensation", "condensed", "steamed up", "steaming up", "misted up",
                 "fogged up", "fogging up", "pane", "panes", "squeegee", "windscreen",
                 # "room" is the storage question: "how do i clear room on my phone" was the
                 # university card, and "clear space" above already covers the other wording
                 "clear room", "clear some room", "room on my", "room for",
                 "laptop", "computer", "junk files", "downloads")),
    entry("first-class",
          (("first class", "first in my degree", "get a first", "2:1", "2.1", "second class",
            "degree classification", "final year", "dissertation"),
           ("how do i", "how to", "get", "aim", "need", "what", "difference", "improve",
            "better", "marks", "grade", "degree", "honours", "worth", "matter")),
          "The marks come from the same three things in every module: answer the exact question "
          "that was set, argue one clear line rather than describe everything you know, and quote "
          "the reading to back it. Get the marking criteria for each module and treat it as the "
          "checklist, then use the feedback on your first essay - the same weakness costs marks "
          "three times if nobody fixes it. Go to the lectures and seminars, because the person "
          "marking it notices, and start the dissertation in the summer before final year: a "
          "first is usually decided by the dissertation and two strong modules, not by all of "
          "them.",
          ask=("how do i", "how to", "get", "aim", "need", "what", "difference", "improve",
               "better", "matter", "want", "want to", "hoping", "aiming", "trying"),
          # an essay's plan and a revision timetable are other answers, and a first aid course
          # is not a degree classification
          avoid=("a level", "gcse", "exam", "revision", "essay", "reference", "notes",
                 "first aid", "first-aid", "aid", "certificate", "course",
                 "stamp", "stamps", "postage", "post office", "letter", "parcel")),
    # --- what a lab report looks like, and the two school lines with no answer ---
    entry("lab-report",
          (("lab report", "lab reports", "write up", "write-up", "practical report",
            "experiment write up", "practical write up", "biology practical",
            "chemistry practical", "physics practical"),
           # no "structure", "start" or "help" here: those words are the essay family's, and
           # adding them to a second entry lowered essay-structure's rank enough that "how do i
           # structure an essay" fell to the planning answer
           ("how do i", "how to", "write", "writing", "sections", "layout", "format",
            "include", "need", "goes in", "as level", "a level", "gcse", "university")),
          "Write it in this order and the marks look after themselves: aim in one sentence, "
          "method in numbered steps someone else could follow, results as a table plus one graph "
          "with labelled axes and units, then a conclusion that says whether the prediction was "
          "right, then an evaluation of what went wrong. Keep the method past tense and passive "
          "('the solution was heated'), put numbers to the precision the instrument allows, and "
          "have one paragraph on sources of error with what you would change - that paragraph is "
          "the difference between a pass and a good mark. Do the graph and the evaluation first "
          "when you are short of time, because they carry the most marks.",
          ask=("how do i", "how to", "write", "writing", "sections", "layout", "format",
               "include", "need"),
          # an essay and a coursework project are their own answers
          avoid=("essay", "coursework", "dissertation", "thesis", "book report", "report on",
                 "business report", "annual report")),
    entry("sixth-form-grades",
          (("sixth form", "sixth-form", "college place", "a level place", "a level entry",
            "get into sixth form", "year 12", "year 11",
            # "what grades do i need for college" reached the driving-licence points answer
            "college", "gcse", "gcses", "a level"),
           ("what grades", "grades do i need", "grades", "requirements", "need", "entry",
            "points", "average", "enough", "to do", "get in", "apply")),
          "Most sixth forms and colleges ask for five GCSEs at grade 4 or above, including "
          "English and maths, and then a 6 or a 7 in the subjects you want to take at A level - "
          "so check the subject page, not the general prospectus, because the maths and science "
          "requirement is usually higher than the rest. If you miss the grades, ask about a "
          "level 3 course or a mixed programme, which often lets you move on to A level after a "
          "year, and apply early with a backup choice: places are offered from the autumn of "
          "year 11, not on results day.",
          ask=("what grades", "grades", "requirements", "need", "entry", "points", "enough",
               "get in", "apply"),
          # a grade on its own is the meaning question, and university entry is its own answer
          avoid=("university", "uni", "ucas", "degree", "offer", "clearing", "what does",
                 "what do my grades mean", "my grades mean",
                 # a driving licence has points, and a points total is not a school question
                 "licence", "license", "driving", "motorway", "speeding", "insurance",
                 # "how many a levels do i need" asks the number, not the grades, and "how do i
                 # apply for college" asks the form; both read this card on "a level" and "college"
                 "how many a levels", "how many a level", "how many subjects",
                 "apply for college", "applying for college", "apply to college",
                 "college application", "apply for sixth form",
                 # "how many gcses do i need to be a teacher" is the job's question
                 "nurse", "nursing", "teacher", "teaching", "vet", "veterinary", "doctor",
                 "lawyer", "solicitor", "midwife", "electrician", "to be a"),
          bias=1),
    # A parent saying their child wants to leave at 16 was acknowledged back at them ("Noted: your
    # son wants to leave school at 16") while the one thing that decides the answer went unsaid:
    # in England they have to stay in education or training until 18, and that can be a college
    # course, an apprenticeship or a job with training in the week rather than school.
    entry("leaving-school-at-16",
          (("leave school", "leaves school", "left school", "leaving school", "quit school",
            "quitting school", "drop out of school", "dropping out of school", "not stay on",
            "stay on at school", "stay at school", "sixth form", "college instead"),
           ("16", "sixteen", "at 16", "year 11", "year 12", "after gcses", "after gcse",
            "wont go", "won't go", "doesnt want", "refuses", "refusing", "should i let",
            "let him", "let her", "is it ok", "is it legal", "allowed", "have to", "must",
            "law")),
          "In England they can leave school at 16 but not stop learning: education or training "
          "has to continue until 18, and a college course, an apprenticeship or a job with "
          "accredited training in the week all count, so it does not have to be more school. "
          "The realistic routes are A levels at a sixth form, a level 2 or 3 vocational course "
          "(BTEC, T level, NVQ) at college, or an apprenticeship, which is a paid job with the "
          "training built in and usually one day a week at college. Visit one college open day "
          "together before deciding, and ask about a level 2 course if the GCSEs are shaky, "
          "because that is a stepping stone to level 3 rather than a dead end.",
          # the ways a parent brings it up: as a question ("can my daughter leave school at
          # 16"), or as a statement of what the child wants, which is the same question
          ask=("can they", "can my", "is it", "should", "do they have to", "have to", "what are",
               "what can", "options", "instead", "wants to", "want to", "doesnt want",
               "does not want", "wont", "refuses", "leave", "leaving", "quit", "drop out"),
          # a parent states it before asking: "my son wants to leave school at 16" was noted back
          # at them, so the stated line reads this row
          report=True,
          # a grade, a college application and the age-16 birthday are their own answers
          avoid=("what grades", "grades do i need", "how do i apply", "apply for college",
                 "apply to college", "ucas", "university", "uni", "a level results",
                 "gcse results", "results day", "birthday", "16th", "driving", "licence",
                 "license", "moped", "cigarettes", "alcohol", "consent", "minimum wage",
                 "national insurance")),
    entry("strict-teacher",
          (("strict teacher", "strict", "harsh teacher", "mean teacher", "unfair teacher",
            "teacher hates me", "teacher doesnt like me", "teacher doesn't like me",
            # the understanding engine splits "doesnt" into "does not", so the apostrophe form
            # above never matches the line: "my teacher doesnt like me and i dont know why" was
            # answered by the chat filler and reached no entry at all
            "does not like me", "doesnt like me", "does not like my", "dont like me",
            "picks on me", "picking on me", "picked on by", "shouted at by teacher",
            "teacher keeps",
            # a parent's line says "her teacher hates her", which names neither "my teacher"
            # nor "hates me", so the pair that carries it is "hate" and "teacher"
            "hates", "hated", "hate my teacher"),
           ("what do i do", "how do i", "deal with", "handle", "cope", "help", "should i",
            "talk to", "complain", "tell", "my teacher", "teacher", "class", "lesson")),
          _strict_teacher,
          ask=("what do i do", "how do i", "deal with", "handle", "help", "should i", "talk to",
               "complain", "tell", "hate", "hates", "picks on", "picked on", "shouts",
               "unfair", "mean", "harsh", "like me", "not like"),
          # the answered child-bullying card is the parent's question and reads the same words
          bias=1,
          # a dog that hates a puppy, a cat that hates a kitten and anything else where one
          # animal or thing dislikes another: the hate is real and it is not about a lesson
          guard=lambda understood: _a_school_line(understood),
          # a boss is the work answer, and bullying at school has its own
          avoid=("boss", "manager", "work", "my job", "colleague", "bully", "bullied",
                 "bullying", "homework", "exam",
                 # "what should i read after the hate u give" is a book, and the title's own word
                 # "hate" was enough for this row: the same steal the reading frames fence in
                 # history.NOT_A_PERSON. The title by name is the narrow fix, the frames are the
                 # general one.
                 "the hate u give", "read after", "read next", "reading next", "what to read",
                 "books like", "book like", "book after", "novel", "novels")),]

# The words that make a line about remembering rather than about the thing it names.
_REMEMBERS = ("memorise", "memorize", "memorising", "memorizing", "remember", "remembering",
              "learn", "learning", "memory", "brain", "forget", "forgetting", "forgetful",
              "revise", "revising", "revision")

# The revision advice, for the line that is about remembering. `things`, `facts` and
# `information` are the entry's key words, and they are generic nouns: a lead-in wears them too.
# "thanks, one more thing, how long do i boil an egg" is an egg question with the word `thing`
# in it, and it was answered with this revision advice; so was "one more thing - how do i clean
# the oven". A line that is about remembering names the act of remembering, learning or
# forgetting, so the entry stands down when the only thing it found is the noun.
_MEMORISE = ("Test yourself instead of rereading: cover the page, say or write what you remember, "
             "then check. That one change does more than any technique. Then space it out - the "
             "same thing tomorrow, in three days, in a week - because the forgetting and the "
             "effort of getting it back is what makes it stay. Say it out loud or write it by hand "
             "rather than only reading, link a new fact to one you already know, and sleep on it: "
             "a night's sleep is when it gets filed.")


def _memorise(memory, understood):
    """The recall method, for a line that is about remembering and not about another subject."""
    line = " " + " ".join(str(w) for w in ((understood or {}).get("norm") or
                                          (understood or {}).get("plain") or "")).lower() + " "
    if not any(word in line for word in _REMEMBERS):
        return None
    return _MEMORISE


# "how do i memorise things faster" was a hedge, and it is the plainest version of the question
# this domain exists for. `revision-active` needs a revising or studying word in the line, so a
# line that only says memorise, remember or learn reached nothing.
#
# "things" is not one of those words, and this entry had it in both key groups, so every line
# about everyday forgetting matched here and was answered with the revision method: "i keep
# forgetting things" got "Test yourself instead of rereading", which is an answer about exams to
# a person asking about their memory. The revision method is for what you chose to learn;
# `science`'s `forgetting-why` is the everyday question, and it is the one that should answer
# "why do i keep forgetting things". Nothing is lost by taking "things" out: "how do i memorise
# things faster" says memorise, and "i want to remember things better" says remember.
ENTRIES.append(entry(
    "memorise-faster",
    (("memorise", "memorize", "memorising", "memorizing", "remember", "remembering", "learn",
      "learning", "memory", "brain"),
     ("faster", "quickly", "quick", "better", "stick", "sticks", "sticking", "stuck", "forget",
      "forgetting", "keeps forgetting", "keep forgetting", "more", "improve", "sharper",
      "technique", "techniques", "trick", "tricks", "tips", "how", "best", "effective", "way")),
    _memorise,
    # the specific questions have their own answers: dates and timelines, flashcards, a spelling
    # test, and where you left something are not the general memory question
    avoid=("dates", "timeline", "history", "flashcard", "flashcards", "anki", "quizlet",
           # "how do i learn the job quickly" is the first week, not a study method: covering the
           # page and testing yourself is for what you chose to learn, and there is no exam in a
           # job. The job words stand this row down and first-day answers it.
           "the job", "my job", "new job", "the role", "my role", "at work", "on the job",
           "the ropes", "ropes", "up to speed",
           "mnemonic", "mnemonics", "spelling", "spell", "password", "passwords",
           # the phrase, not the bare word: _misspelt_avoid reads "facts" as a slip of "faces",
           # and "what is the best way to memorise facts" was turned down by its own avoid list
           "names and faces", "faces and names",
           "dream", "dreams", "where i put", "where i left", "remember to", "remind me",
           "reminder", "birthday", "anniversary", "asleep", "tired", "sleepy",
           # A relative who keeps forgetting is the parent-memory card's line, not this one:
           # "im worried about my mum she keeps forgetting things" was read as a study question
           # ("test yourself instead of rereading"), which is a different person's memory named
           # in the line. The words are the ones the parent-memory key uses, so the study card
           # stands down and that card answers. The asker's own learning is untouched:
           # "why do i keep forgetting things" and "how do i memorise things faster" stay here.
           "mum", "mom", "mother", "dad", "father", "parent", "parents", "grandma",
           "grandmother", "grandad", "grandfather", "gran", "nan", "nana", "mother in law",
           "father in law",
           # typing is a skill with its own answer, below: "how do i learn to touch type" was
           # getting the general memory method
           "touch type", "touch-type", "touch typing", "touch-typing", "typing", "keyboard",
           "wpm", "words a minute",
           # "how do i learn to drive" is a lessons question and "how do i learn to cook" is a
           # kitchen one: a named skill is not the memory trick, and this entry took both on
           # the words "learn" and "how" alone.
           "drive", "driving", "cook", "cooking", "bake", "baking", "swim", "swimming",
           "knit", "knitting", "sew", "sewing", "draw", "drawing", "dance", "dancing",
           "guitar", "piano", "drums", "violin", "ride a bike", "cycle", "cycling",
           "code", "coding", "programming", "touch typing", "juggle", "whistle",
           # Someone else forgetting is not a revision question either. "my mum keeps
           # forgetting things, is that normal" was answered with "test yourself instead of
           # rereading" because "keeps forgetting" is in this key: an older relative's memory
           # is the memory-worry answer, and so is a partner's or a parent's.
           "husband", "wife", "partner", "boyfriend", "girlfriend", "granny", "grandpa",
           "getting forgetful", "gets forgetful", "memory loss", "losing his memory",
           "losing her memory", "dementia", "alzheimers", "alzheimer's", "as you get older",
           "getting older", "my age",
           # "things" is one of this row's words, so a kitchen line that says "two things in the
           # oven" was read as a memory question: "how do i time two things in the oven" got
           # "test yourself instead of rereading". Cooking has its own row for that line now.
           "oven", "cooked", "recipe", "recipes", "dish", "dishes", "tray", "trays",
           "tin", "tins", "roast", "kitchen"),
    ask=("faster", "quickly", "quick", "better", "stick", "sticks", "sticking", "stuck",
         "forget", "forgetting", "keeps forgetting", "keep forgetting", "more", "improve",
         "sharper", "technique", "techniques", "trick", "tricks", "tips", "how", "best",
         "effective", "way")))

# Typing is a physical skill and the memory method does not teach it. Ten minutes a day on the
# home keys is the whole answer, and the accuracy-first order is what people get wrong.
ENTRIES.append(entry(
    "learn-touch-typing",
    (("touch type", "touch-type", "touch typing", "touch-typing", "typing", "wpm",
      "words a minute"),
     ("learn", "learning", "teach myself", "improve", "quicker", "speed", "properly", "proper",
      "start", "practice", "practise")),
    "Start on the home keys and do not look down: left hand on a s d f, right hand on j k l and "
    "the semicolon, thumbs on the space bar, and cover your hands with a cloth if you keep "
    "peeking. Ten to fifteen minutes a day on a free drill site, typing real sentences rather "
    "than random letters, is enough to build it. Accuracy first and speed second, because a "
    "wrong key costs more time than a slow one: most people go from about 30 to 50 words a "
    "minute in a month of daily practice, and the last stretch comes from typing your own "
    "messages rather than the drills.",
    ask=("how", "how do i", "how can i", "how to", "whats the best way", "can i", "help", "tips",
         "faster", "better"),
    # a keyboard that types the wrong letters is the keyboard entry, and a broken one is not a
    # learning question
    avoid=("wrong letters", "wrong letter", "types the wrong", "typing the wrong", "not working",
           "broken", "broke", "spilled", "sticky", "missing keys", "virtual", "on screen",
           # cleaning a keyboard is the keyboard entry's job, not a typing lesson
           "clean", "cleaning", "cleaned", "wipe", "dirty", "crumbs", "grubby", "disinfect",
           "phone keyboard", "autocorrect", "swipe",
           # one key or one character is a how-do-i-type-it question, not a learning one
           "symbol", "symbols", "special character", "special characters", "emoji", "emojis",
           "accent", "accents", "capital letter", "capital letters", "uppercase", "underscore",
           "hashtag", "slash", "asterisk", "tilde", "key combination", "shortcut", "shortcuts"),
    bias=1))

# --- studying later in life: is it sensible, and how much work is it --------
# The two things a person asks about an evening course they are thinking of taking. Both are
# asked without the course being named: "is that a sensible thing to do at my age?" comes
# straight after the turn that named it, so the reader below looks at the line and the two
# turns before it, the way the spectacles reader in clothing.py does.
_LATER_STUDY = re.compile(
    r"\b(?:course|courses|college|university|uni|degree|gcse|gcses|a[ -]?levels?|night school|"
    r"evening class|evening classes|access course|study|studying|lessons?|retrain|retraining|"
    r"qualification|qualifications|apprenticeship|masters|phd|bookkeeping|"
    r"nursing|tutor|lectures?|homework|exams?|revision|traineeship|nvq)\b")

# The commonest way of asking is with a job in the line and no age at all: "is it too late to
# become a teacher". No course word appears, so `_LATER_STUDY` cannot see it, and waiting for a
# number would leave the most asked form of the question unanswered. A change of career is the
# same question as a course, and the answer without a number is already written below.
_CAREER_CHANGE = re.compile(
    r"\b(?:too old|too late)\b[^.?!]*\b(?:become|becoming|train as|training as|retrain as|"
    r"retraining as|qualify as|qualifying as|career change|change career|change jobs|switch careers?|"
    r"switch to|move into|go into|get into)\b")

# "Am I too old to have a baby" and "at my age should I get a puppy" are the same shape as the
# course question and want other answers: a body or an animal in the line keeps them out.
_NOT_AGE_STUDY = re.compile(
    r"\b(?:baby|babies|pregnan\w*|ivf|fertility|children|kids|puppy|puppies|dog|dogs|cat|cats|"
    r"driving|drink\w*|tattoo|piercing|marathon|gym|weight|surgery|operation|"
    # an instrument at my age is the learn-an-instrument entry, which is in this file
    r"piano|guitar|violin|viola|cello|drums|instrument|instruments|keyboard|ukulele|flute|"
    # and "am i too late to start a business" is not a course
    r"business|businesses|startup|startups|company|shop|restaurant|cafe|"
    # a becoming line with a body or a family in it is another answer: "too old to become a dad"
    r"dad|father|mum|mom|mother|parent|parents|grandma|grandmother|grandad|grandfather|"
    # and one about a sport or a stage is not about a course either
    r"footballer?|athlete|olympic|rugby|boxer|boxing|singer|dancer|actor|actress|model|"
    r"influencer|youtuber|streamer)\b")


# The ways the age question is actually asked, rather than the age alone: "can i still study"
# and "is it worth it at my age" are the same question as "am i too old to study".
_AGE_ASK = re.compile(
    r"\b(?:too old|too late|at my age|my age|the age|an age|age matter|age matters|age stop|"
    r"age a problem|age hold|can i still|could i still|is it still|still worth|"
    r"worth it at|at \d{2}|in my (?:thirties|forties|fifties|sixties|seventies))\b")

_AGE_NUMBER = re.compile(r"\b(\d{2})\b")


def _study_later(memory, understood):
    """The age question about a course, which may name the course only in the turn before."""
    clean = re.sub(r"[^a-z0-9' ]+", " ", " " + str(
        understood.get("clean") or understood.get("text") or "").lower() + " ")
    if _NOT_AGE_STUDY.search(clean):
        return None
    career = bool(_CAREER_CHANGE.search(clean))
    # A course word on its own is not the question. "How do i get into university as a mature
    # student" names one, and the personal-statement answer already serves it; this reader
    # answered it with "You would not be late", which reassures instead of telling them how.
    # So the line has to ask about age, or be a change of career, which is the same question
    # with the answer already written.
    if not (_AGE_ASK.search(clean) or career):
        return None
    if not (_LATER_STUDY.search(clean) or career):
        turns = memory.get("turns")
        seen = False
        if isinstance(turns, list):
            for turn in turns[-2:]:
                if isinstance(turn, dict) and _LATER_STUDY.search(
                        str(turn.get("user") or "").lower()):
                    seen = True
        if not seen:
            return None
    match = _AGE_NUMBER.search(clean)
    age = int(match.group(1)) if match else 0
    if 18 <= age <= 90:
        # the age in their own line, so the answer is about them rather than about 41
        if age > 60:
            # past the ages the answer names, so say that plainly instead of claiming the
            # room will be full of people their age
            return (f"At {age} you would be older than most of the class, and that is normal on "
                    "these courses: what decides it is not the age but the routine - one fixed "
                    "evening in class and one more for reading, kept for the length of the "
                    "course - and a subject you will still open on a bad week. Ask the college "
                    "what share of last year's class finished, and whether any of it can be done "
                    "in the daytime or online, because that is what makes it stick.")
        opener = f"At {age} you would not be late: "
    else:
        opener = "You would not be late: "
    return (opener + "evening classes, access courses, apprenticeships and part-time degrees are "
            "full of people in their thirties, forties and fifties, and the ones who finish are "
            "the ones with a "
            "protected evening rather than the fastest readers. What decides it is the routine — "
            "one fixed evening in class and one more for reading, kept for the length of the "
            "course — and a subject you will still open on a bad week. Ask the college what share "
            "of last year's class finished, because these courses are lost to work and life far "
            "more than to age.")


# The hours question is asked both ways: with the course named ("how many hours a week is a part
# time college course") and as a follow-up that names nothing ("how much work a week would it
# be"). The second kind only counts when the line, or the turn before it, is about a course.
_COURSE_TIME = ("how much work", "how much time", "how much reading", "how many hours",
                "much study", "workload", "hours a week", "a week", "per week", "each week",
                "evenings a week", "commitment", "much effort",
                # and the plain hours question: "what would the hours be like" after a course
                "the hours", "what hours", "hours be", "hours like")

def _course_hours(memory, understood):
    clean = str(understood.get("clean") or understood.get("text") or "").lower()
    # A line that names the course is `evening-course` in this file, which already gives the
    # guided learning hours: this reader is only for the follow-up that names nothing.
    if _LATER_STUDY.search(clean):
        return None
    turns = memory.get("turns")
    if isinstance(turns, list):
        for turn in turns[-2:]:
            if not isinstance(turn, dict):
                continue
            before = str(turn.get("user") or "").lower()
            # a turn about a course, or about becoming something else: "is 50 too old to become
            # a nurse" then "what would the hours be like" is the same hours question
            if _LATER_STUDY.search(before) or _CAREER_CHANGE.search(before):
                return COURSE_HOURS
    return None


COURSE_HOURS = ("Budget two to three hours of reading and homework for every hour in class: a "
                "three-hour evening class is usually 9 to 12 hours a week including the class, "
                "and a part-time degree is 16 to 20 hours a week because it is half of a "
                "full-time course. The college has to publish those guided-learning hours on the "
                "course page, so ask for them before you enrol and pick the two evenings you "
                "would protect. Reading is what gets dropped first, so put it in the diary as an "
                "appointment rather than a hope.")


ENTRIES.append(entry(
    "study-age",
    (("at my age", "my age", "too old", "too old for", "too late", "mature student",
      "mature students", "older student", "am i too old", "is it too late", "age matter",
      "does age", "age stop me", "age too late"),
     # the second half is the question about it rather than the subject: "is that a sensible
     # thing to do" and "is it worth it" are what people type after naming the course
     ("sensible", "worth", "wise", "should i", "do it", "thing to do", "go for it", "go back",
      "study", "studying", "university", "uni", "college", "course", "retrain", "learn",
      "start", "doing",
      # the commonest form names a job and no course at all: "is it too late to become a
      # teacher". The first half of the key is what keeps these to an age question.
      "become", "becoming", "be a", "qualify", "qualifying", "career", "careers",
      "change career", "switch")),
    _study_later,
    # a retirement, a pension and a mortgage are money questions: "can i retire at 60" and
    # "can i get a mortgage at my age" are not this answer
    avoid=("retire", "retiring", "retirement", "pension", "mortgage", "bus pass", "state pension",
           "driving licence", "insurance", "job interview", "cv"),
))

ENTRIES.append(entry(
    "course-hours",
    (_COURSE_TIME,
     ("course", "courses", "college", "university", "uni", "evening class", "evening classes",
      "night school", "part time", "part-time", "degree", "study", "studying", "would it",
      "would that", "would i need", "do you think", "be",
      # the follow-up names nothing at all: "how many hours a week is that" comes straight after
      # the turn that named the course, and the reader above is what keeps it to those turns.
      "is that", "is it", "that", "it")),
    _course_hours,
    # revision hours are `study-how-long`, the sleep and shift answers are their own, and a
    # course is not a job: the second key word alone brings in "how many hours a week do i work"
    avoid=("sleep", "overtime", "shift", "shifts", "salary", "pay", "job", "jobs", "driving",
           "revise", "revising", "revision", "exam", "exams", "test", "tests", "gcse", "gcses",
           "a level", "a levels", "mocks", "homework", "work out my", "do i work"),
))

# Learning a language, which is a different question from "how do I memorise this list": the
# order (understand first, then speak, then be corrected), the daily size, and the fact that
# reading and listening do more for a beginner than grammar drills.
ENTRIES.append(entry(
    "improve-english",
    (("english", "spanish", "french", "italian", "german", "portuguese", "polish", "welsh",
      "irish", "dutch", "a language", "languages", "language"),
     ("improve", "better", "learn", "learning", "fluent", "fluently", "speak", "speaking",
      "practice", "practise", "practising", "practicing", "study", "studying", "get better",
      "conversation", "conversational")),
    "Understand more before you try to speak, and speak badly early: ten minutes of listening or "
    "reading you mostly follow, every day, does more in a month than a grammar book. Learn whole "
    "phrases rather than single words - \"could I have...\", \"I've just...\" - because they come "
    "out in the right order without you building them. Then say them: out loud on your own, to a "
    "tutor once a week if you can, or to anyone patient. Get corrected on the mistakes you make "
    "every time, not on every mistake, and keep a list of your own bad habits. Watching something "
    "you already know with subtitles in the new language is the cheapest hour there is.",
    # a spelling or grammar question about English words is its own answer, and "do you speak
    # English" is the bot introducing itself
    avoid=("spell", "spelt", "spelling", "grammar", "comma", "apostrophe", "semicolon",
           "synonym", "meaning", "means", "difference between", "pronounce", "pronunciation",
           "translate", "translation", "essay", "coursework", "gcse", "a level", "ielts",
           "exam", "test", "do you speak", "can you speak", "why is"),
    ask=("improve", "better", "learn", "learning", "fluent", "fluently", "speak", "speaking",
         "practice", "practise", "practising", "practicing", "study", "studying", "get better",
         "conversation", "conversational", "how"),
))
# "how many gcse points do i need for college" was answered by the driving-licence points entry:
# the word "points" is ordinary prose and the arithmetic question is a school one.
ENTRIES.append(entry(
    "gcse-points",
    (("gcse points", "points for college", "points for a levels",
      "how many gcses", "how many gcse", "grades do i need", "grades to get in",
      "entry requirements", "entry grades", "what grades", "which grades", "gcse grades"),
     ("how many", "how much", "need", "needs", "needed", "college", "sixth form", "a level",
      "a levels", "course", "get in", "get into", "require", "required", "points", "university")),
    "Colleges usually ask for five GCSEs at grade 4 or above, including maths and English, and a "
    "sixth form taking A levels often wants a 6 in the subjects you pick - a 6 in maths for maths, "
    "for instance. The points people talk about are just that arithmetic: a grade 4 is worth 4, so "
    "five grade 4s is 20 points, and each college publishes what it asks for. If English or maths "
    "is below 4, most colleges will let you take it alongside the course rather than turn you away,"
    " so ring admissions with the exact course and ask.",
    # a job that needs grades is the job's question, not the college arithmetic: "how many
    # gcses to be a nurse" and "what grades do i need to be a vet" reached this card, whose
    # answer is about a college place. UCAS tariff points are A-level points, so they get
    # their own entry below.
    avoid=("driving", "licence", "license", "theory test", "penalty", "speeding", "blood",
           "grade 4 mean", "what is a grade", "what does a grade",
           # "what grades" is any grades, and a thing has a grade too: "what grade of oil
           # does my car need" was a college-place card because "grade" and "need" were the
           # two key words. The material, the engine and the shopping are not a school question.
           "oil", "oils", "engine", "engines", "car", "cars", "petrol", "diesel", "fuel",
           "tyre", "tyres", "brake", "brakes", "coolant", "wood", "timber", "steel",
           "meat", "beef", "steak", "coffee", "paint", "milk", "eggs", "whisky", "wine",
           "nurse", "nursing", "teacher", "teaching", "vet", "veterinary", "doctor",
           "lawyer", "solicitor", "midwife", "electrician",
           "ucas points", "ucas tariff", "ucs points")))

# UCAS tariff points are A-level points, and the card that knew them was keyed on a typo
# ("ucs points"), so the line fell through to the application answer.
ENTRIES.append(entry(
    "ucas-points",
    (("ucas points", "ucas tariff", "ucas tariff points", "ucs points", "tariff points"),
     ("how many", "how much", "need", "needed", "do i need", "are", "is", "does", "my",
      "points", "level", "a level", "btec", "university", "course", "offer", "get")),
    "UCAS tariff points come from level 3 qualifications only, so GCSEs carry none: an A level "
    "is 48 points at grade A, 40 at B, 32 at C, 24 at D and 16 at E, and a BTEC Extended Diploma "
    "can score more than three A levels. Add them up across everything you have and compare with "
    "the course page, which usually prints both the points and the grades it asks for - when the "
    "grades are the offer, the points are only the summary.",
    # a GCSE question stays with the GCSE card
    avoid=("gcse", "gcses", "sixth form", "college place"),
    bias=2))

# "how many a levels do i need" was a shrug: the number is a real answer, and the grades card
# was the wrong place to look for it.
ENTRIES.append(entry(
    "a-levels-count",
    (("how many a levels", "how many a level", "how many subjects at a level",
      "how many subjects for a level", "three or four a levels", "four a levels",
      "how many a levels should i take"),
     ("how many", "should i take", "should i do", "need", "take", "do", "three", "four",
      "a level", "a levels", "subjects", "sixth form", "college")),
    "Three A levels is the standard full programme and what nearly every offer is written on; "
    "take four only if one is further maths, or if you are keeping a fourth for a course that "
    "asks for it, because a fourth A level rarely improves an offer and always costs marks in the "
    "other three. Two A levels plus a BTEC or an EPQ is a normal shape too - check the entry "
    "requirements for two or three courses before you choose the number.",
    avoid=("university", "uni", "ucas", "grade", "grades", "drop", "results day", "fail")))

# "what grades do i need to be a vet" reached the pet answer, because a vet is an animal doctor.
# The grades a job needs are set by the route into it, so one card names the routes - and the
# route the person asked about has to come first. A vet and a nurse hear different sentences.
_GRADES_ROUTE = (
    (("doctor", "medical school", "medicine"),
     "Medicine wants strong GCSEs, usually 5s and 6s including maths, English and a science, then "
     "A level chemistry plus one more science or maths, and some work experience in a care setting "
     "before you apply."),
    (("pharmacist", "pharmacy"),
     "Pharmacy wants A level chemistry and one other science, then the four-year MPharm and the "
     "year of training after it."),
    (("physiotherapist", "physiotherapy"),
     "Physiotherapy wants A level biology, most courses ask for a B or above at A level, and then "
     "the degree."),
    (("architect", "architecture"),
     "Architecture wants A level maths or physics, then the degree, then two years of practice "
     "before the final exam."),
    (("social worker", "social work"),
     "Social work wants GCSEs in English and maths, then a degree in social work, then "
     "registration with Social Work England."),
    (("police", "police officer"),
     "The police ask for a level 3 qualification - A levels or a BTEC both count - plus the "
     "fitness test and the background checks."),
)

# The routes main already answers better than a card like this can: nursing, teaching, veterinary,
# law, the trades, paramedic science and accountancy each have their own row on main that names the
# grades and the way in. A route table that also claimed those lines would replace a specific
# answer with a general one, so the job words in its key are only the six still unanswered.


def _job_grades(memory, understood):
    """The job the line names sets the first sentence; the advice after it is the same for all.

    A line that asks how long is answered with the years instead, from `JOB_LENGTHS`: "how long
    does it take to become a doctor" was five years of medical school answered with grades.
    """
    length = _the_length_answer((understood or {}).get("clean") or "", memory)
    if length:
        return length
    text = " " + " ".join(understood.get("words") or []) + " "
    first = ""
    for words, sentence in _GRADES_ROUTE:
        if any(" %s " % word in text for word in words):
            first = sentence
            break
    if not first:
        first = ("The route sets the grades, so there is no single number: the job names the course, "
                 "and the course names the subjects.")
    return (first + " Check the entry requirements on two or three course pages before you apply, "
            "because the subjects named there are what decide it - a grade below them is the thing "
            "to fix first, and a course that asks for less is the fallback.")


# "what grades do i need to be a vet" reached the pet answer, because a vet is an animal doctor.
ENTRIES.append(entry(
    "job-grades",
    (("what grades do i need to be a", "what gcses do i need to be a", "grades do i need to be a",
      "gcses do i need to be a", "how many gcses do i need to be a", "gcses do i need for",
      "gcses to be a", "grades to be a", "what grades for", "what gcses for",
      "what do i need to be a", "grades do i need for", "grades do i need to be an",
      "gcses do i need to be an", "what grades do i need to be an", "grades to be an",
      "how many gcses to be a", "how many gcses for"),
     # only the jobs still unanswered on main - see the note above the route table
     ("doctor", "medicine", "medical school", "pharmacist", "pharmacy", "physiotherapist",
      "physiotherapy", "architect", "architecture", "social worker", "social work", "police",
      "police officer")),
    _job_grades,
    # career-subjects is the table of what subjects each job wants and it carries "grades",
    # "gcse" and the job word too, so the two tie on "what grades do i need to be a teacher".
    # This entry is the one that names the grades the route asks for, and a bias breaks the
    # tie without widening either key.
    bias=3))

# "how do i become a social worker" has no answer on main at all, and "how do i become a doctor"
# reached a card that tells you to ring your GP. The same six routes the grades card names are the
# ones with no row of their own, and "become" or "get into" is how the person asks it. The job word
# has to be one of those six, so this cannot take a line that main already answers well - nursing,
# teaching, veterinary, law, the trades and accountancy are all left to their own rows.
ENTRIES.append(entry(
    "job-route",
    (("become", "becoming", "get into", "getting into", "qualify as", "train as", "want to be",
      "how do i become", "how i become", "what do i need to",
      # the same route asked as a yes-or-no: "do i need a degree to be a social worker"
      "do i need a degree", "need a degree to", "degree to be", "degree to become",
      "a degree to", "to be a", "to be an"),
     ("doctor", "medical school", "medicine", "pharmacist", "pharmacy", "physiotherapist",
      "physiotherapy", "architect", "architecture", "social worker", "social work", "police",
      "police officer")),
    _job_grades,
    # a pension, a course and a pupil are not a route into one of these six jobs
    avoid=("pension", "mortgage", "insurance", "credit", "ucl", "an apprentice", "apprenticeship",
           "my teacher", "my son", "my daughter", "my mum", "my dad"),
    bias=2))

# "how do i apply for college" read the sixth-form grades card, whose answer is about the grades.
ENTRIES.append(entry(
    "sixth-form-application",
    (("apply for college", "applying for college", "apply to college", "college application",
      "apply for sixth form", "apply to sixth form", "how do i apply for college"),
     ("how do i", "how can i", "do i", "when do i", "apply", "application", "deadline",
      "college", "sixth form", "place")),
    "Apply straight to the college, not through your school: every college has an online form "
    "on its own site, and for a September start the deadline is usually the spring before, with "
    "places filling from January. You apply before your GCSE results, the offer is conditional "
    "on the grades, and you confirm it on results day - so apply to two colleges if you are not "
    "sure, and ring admissions the week results come out if anything goes wrong.",
    avoid=("university", "uni", "ucas", "degree", "student finance", "job", "visa")))

# "How do I get an apprenticeship" and "when are the GCSE exams" had no answer at all: the
# degree-versus-apprenticeship entry is a decision, not a how-to, and the dates are a fact about
# the year rather than a revision plan. Both are what a school leaver or a parent asks first.
ENTRIES.append(entry(
    "apprenticeship-how",
    (("apprenticeship", "apprenticeships", "apprentice", "apprentices"),
     ("get", "getting", "find", "finding", "apply", "applying", "start", "starting", "look",
      "looking", "search", "searching", "how", "where", "become", "becoming", "want", "wanted",
      "want to", "should")),
    "Apply to them like jobs, because that is what they are: the vacancies are on the government "
    "Find an Apprenticeship service (gov.uk in England, apprenticeships.scot in Scotland, "
    "careerswales in Wales, nidirect in Northern Ireland), and big employers also advertise on "
    "their own sites with closing dates in the autumn and winter before a September start, so "
    "apply months early and to several. They come at four levels: GCSE-level, A-level, higher "
    "(the first two years of a degree) and degree, and the degree ones are competitive and want "
    "A-levels or a good BTEC. You need English and maths at GCSE for most of them, and if you "
    "missed those the employer usually puts you through them alongside the job. Pay is at least "
    "the apprentice minimum wage and rises with each year, so check the travel before you accept: "
    "a low wage plus a long commute is the thing people regret.",
    # a degree apprenticeship question is the degree-versus-apprenticeship answer, and the levy
    # is an employer's tax
    avoid=("degree apprenticeship", "degree apprenticeships", "worth it", "worth doing",
           # the hours are a fact about the job, not a way to find one, so the how-to stands
           # down and the apprentice-hours row answers that
           "how many hours", "holidays", "time off", "overtime", "part time", "shift",
           "better than", "instead of university", "rather than university", "levy",
           "my employer", "our company", "we want to hire", "i employ"),
    ask=("how", "where", "what", "can i", "do i", "should i", "want to", "looking for",
         "help me", "advice")))

EXAM_WHEN = (
    "GCSE and A-level exams run from the middle of May to the middle of June, and the exact "
    "timetable for your subjects is published by the exam board - AQA, Edexcel, OCR or WJEC - "
    "about a year ahead, with the month-by-month dates on the board's site for the year you are "
    "sitting. Your school gives you your own timetable with the room and the start time once the "
    "entries are confirmed in February, and that is the one to go by. Results come out in the "
    "middle of August on a Thursday, with A-levels a week before GCSEs, and mocks sit in "
    "November or December before that."
)


def _exam_when(memory, understood):
    """The date of the summer exams, and of the mocks, which the school sets itself."""
    clean = ((understood or {}).get("clean") or "").lower()
    if re.search(r"(?<![a-z])mocks?(?![a-z])", clean):
        return ("Your school sets its own mock dates, and they are usually in November or December "
                "of the year before, so ask your head of year for the week rather than a "
                "national one. The summer exams themselves run from the middle of May to the "
                "middle of June, and the board's timetable for your subjects is on AQA, Edexcel, "
                "OCR or WJEC's site about a year ahead.")
    return EXAM_WHEN


ENTRIES.append(entry(
    "exam-dates",
    (("gcse", "gcses", "a level", "a levels", "alevels", "national 5", "higher", "highers",
      "mock", "mocks", "exams"),
     # "dates" on its own is how the memory entry is asked for history dates, so the date
     # words here are the ones that are about an exam
     ("when", "what date", "which date", "start", "starts",
      "starting", "begin", "begins", "timetable", "timings", "how long until")),
    _exam_when,
    # results day, a bad grade and revision plans are their own answers, and a driving or a
    # blood test is not a school exam
    avoid=NOT_AN_EXAM + ("predicted", "predicted grade", "predicted grades",
                         "practice paper", "practice papers",
                         "results day", "my results", "got my results", "failed",
                         "fail", "clearing", "remark", "resit", "revise", "revising",
                         "revision", "timetable for revision", "how do i", "best way"),
    ask=("when", "what date", "which date", "dates", "how long until", "timetable"),
    bias=1))


# The subjects a job actually asks for, one table for every career, because the question wears
# a hundred phrasings ("what gcses do i need to be a nurse", "what do you need to be a vet",
# "what subjects for medicine") and the answer is a fact about the job, not about the wording.
CAREER_SUBJECTS = (
    (("nurse", "nursing"),
     "Nursing wants five GCSEs at grade 4 or above, including English, maths and a science, and "
     "then a nursing degree, a nursing associate apprenticeship or a degree apprenticeship at a "
     "trust. Most universities also ask for A-levels or a BTEC in a science or health subject, and "
     "care experience - a care home, a hospice, a hospital volunteer - is what separates people "
     "with the same grades. Check the entry requirements for each course, because they differ."),
    (("midwife", "midwifery"),
     "Midwifery asks for the same five GCSEs at grade 4 or above, English, maths and a science "
     "among them, and then a midwifery degree or one of the new midwifery apprenticeships. It is "
     "one of the most competitive courses there is, so care or maternity experience and a week "
     "spent shadowing a midwife are worth more than an extra A-level."),
    (("doctor", "medicine", "medical school", "surgeon"),
     "Medicine wants strong GCSEs, usually 5s and 6s including maths, English and science, then "
     "A-level chemistry plus one more science or maths, because nearly every medical school "
     "requires chemistry. Then it is a five-year degree, the UCAT test in the summer before you "
     "apply, and work experience or volunteering in a care setting; the interview is about what "
     "you saw there."),
    (("teacher", "teaching", "primary school teacher", "secondary school teacher"),
     "Teaching wants GCSEs at grade 4 or above in English and maths, plus a science for primary, "
     "then a degree in a subject schools teach, then a PGCE or a school-based training place - or "
     "a teaching apprenticeship, where you are paid while you train. Primary teaching takes any "
     "degree but checks your curriculum subjects, and secondary wants the subject you will teach."),
    (("vet", "veterinary", "vet school"),
     "Veterinary medicine wants A-level chemistry and usually biology, grades A or A*, and weeks "
     "of work experience with animals - a farm, a stable, a vet practice - before you apply. The "
     "degree is five years and hard to get into, so apply to two or three vet schools and have a "
     "second choice you would genuinely take."),
    (("lawyer", "law", "solicitor", "barrister", "law degree"),
     "Law takes no particular A-levels: grades and a degree matter, and any subject is fine, so "
     "pick what you will do well in. The law degree (or any degree plus the conversion course) is "
     "followed by the SQE exams for solicitors or the bar course for barristers, and the thing "
     "that gets you a training place is experience - a law centre, a solicitor's office, mooting "
     "at university."),
    (("engineer", "engineering", "mechanical engineer", "civil engineer", "electrical engineer"),
     "Engineering wants A-level maths and physics, then an accredited MEng or BEng degree, and the "
     "accreditation is the part to check because it is what leads to chartership. The other route "
     "is a degree apprenticeship with an employer, which pays from day one and ends with the same "
     "qualification, or a technician apprenticeship if you would rather start with your hands."),
    (("accountant", "accountancy", "accounting", "chartered accountant"),
     "Accountancy asks for no fixed subjects, though maths and a numerical subject help, and there "
     "are three ways in: A-levels then an AAT or ACCA/ACA training contract, a degree then the "
     "same exams, or an accountancy degree apprenticeship where the employer pays for the exams. "
     "The exams are the qualification either way, so the route with the least debt is usually the "
     "apprenticeship."),
    (("paramedic", "paramedic science"),
     "Paramedic science wants a science A-level or an access course, and usually GCSEs at grade 4 "
     "or above in English, maths and science, then a three-year paramedic science degree - or the "
     "technician route inside an ambulance service, which pays while you train. Get a first aid "
     "certificate and some time in a care or St John Ambulance role first, because the courses and "
     "the interviews both ask what you have seen."),
    (("electrician", "plumber", "plumbing", "mechanic", "chef", "carpenter",
      "bricklayer", "joiner", "gas engineer"),
     "The trades ask for no GCSEs to start, though English and maths help with the theory and "
     "employers usually want 4s in them. The way in is an apprenticeship - level 2 then level 3 "
     "with an NVQ - or a college course alongside finding an employer yourself, and for gas, "
     "electrics and heating there is a registration scheme at the end that you cannot skip. Ring "
     "local firms and ask for a trial week: that is how most people get taken on."),
)

THE_GENERAL_CAREER = (
    "Check the entry requirements on the university or college page for the exact course, because "
    "they differ more than people expect - most want five GCSEs at grade 4 or above including "
    "English and maths, and A-levels or a BTEC in a subject that fits. Pick the subjects that keep "
    "two doors open rather than one, and ask a teacher or someone doing the job now what they "
    "actually needed.")


# How long the training for each job takes, in years, because "how long does it take to become a
# nurse" and "how many years is it" ask about time and the grades are a different question. Before
# this, both were answered with subjects and entry requirements - the right information to the
# wrong question - and two turns into a conversation the line named no job at all and got a shrug.
#
# One table for every job the career rows know, so a length is written once and any row that names
# a job can ask for it: the grades rows, the route rows and the subjects rows all lead with it when
# the line asks how long. A person who has done the job before is asking about the shorter route
# back in, so each job that has one carries it as well as the route from scratch.
JOB_LENGTHS = (
    (("nurse", "nursing"),
     "Three years for a nursing degree, two for a nursing associate course, or four on a degree "
     "apprenticeship where you are paid while you train.",
     "A return-to-practice course, not the degree again: about 450 hours of supervised practice "
     "and a short theory module, which most trusts run over three to six months, and they tell "
     "you which one they take at the interview."),
    (("midwife", "midwifery"),
     "Three years for a midwifery degree, or four years on a midwifery apprenticeship, which "
     "pays while you train.",
     "A return-to-practice course of a few months supervised in a maternity unit, rather than the "
     "degree again, if you have let your registration lapse."),
    # "how long does it take to become a dentist" was the check-up card answering with the
    # length of a visit, because the line holds "how long does ... take" and the word dentist.
    # Becoming one is five years at dental school and then a training year, which is a different
    # question with a different answer.
    (("dentist", "dentistry", "dental school", "dental surgeon"),
     "Five years at dental school, then a year of dental foundation training in a practice "
     "before you can work on your own, so six years from starting to being paid as a dentist.",
     "A return-to-practice or the overseas registration exam rather than the degree again: "
     "around a year of study and supervised practice, and the General Dental Council says which "
     "route your qualification needs."),
    (("doctor", "medicine", "medical school", "surgeon"),
     "Five years at medical school, then two foundation years in a hospital before you can apply "
     "for specialty training, which runs from three to eight years depending on the field.",
     "If you qualified as a doctor abroad, the route is the PLAB exams and then a couple of years "
     "in a training post, not a second degree."),
    (("teacher", "teaching", "primary school teacher", "secondary school teacher"),
     "Three years for a degree and then one more for a PGCE or a school-based training year, so "
     "four in all, or about the same on a teaching apprenticeship, which pays.",
     "A refresher course of a few weeks rather than a second degree, if you taught before and let "
     "the registration go."),
    (("vet", "veterinary", "vet school"),
     "Five years at vet school, and there is no shorter route into it.",
     ""),
    (("lawyer", "law", "solicitor", "barrister", "law degree"),
     "Three years for a law degree, then two years of qualifying work experience while you sit "
     "the SQE exams - so four to five years in all, or a year more if you do a conversion course "
     "instead of the law degree.",
     "A conversion course of a year, then the same two years of qualifying work experience."),
    (("engineer", "engineering", "mechanical engineer", "civil engineer", "electrical engineer"),
     "Four years for an MEng, or three for a BEng and then a few years of supervised work to "
     "chartership.",
     "A degree apprenticeship of four to six years, paid throughout, which is the usual way back "
     "in if you already work in the industry."),
    (("accountant", "accountancy", "accounting", "chartered accountant"),
     "Three to four years of exams, AAT first and then ACCA or ACA, taken while you work, so you "
     "are paid from the first year.",
     "The same three to four years of exams, starting at the level you left off at, and a firm "
     "will usually take you on as a trainee while you sit them."),
    (("paramedic", "paramedic science"),
     "Three years for a paramedic science degree, or about two years as an associate ambulance "
     "practitioner inside a trust, which pays.",
     ""),
    (("pharmacist", "pharmacy"),
     "Four years for an MPharm, then a year of foundation training in a pharmacy before you "
     "register.",
     "A refresher placement and the registration assessment rather than the degree again."),
    (("physiotherapist", "physiotherapy"),
     "Three years for a physiotherapy degree, or two on an accelerated Masters if you already "
     "have a degree in a science.",
     "A return-to-practice course of a few weeks, run by the Chartered Society of Physiotherapy, "
     "if you have been out of the register."),
    (("architect", "architecture"),
     "Three years for a degree, then two years of practical experience and the Part 3 exam - "
     "seven years in all, and the Part 3 is the part people underestimate.",
     "The Part 2 and Part 3 years, on top of the experience you already have, rather than the "
     "whole degree again."),
    (("social worker", "social work"),
     "Three years for a social work degree, or two on a Masters if your first degree is in "
     "something related, and there are fast-track programmes that pay a salary while you train.",
     "A return-to-practice course of a few weeks, and the register tells you what you need."),
    (("police", "police officer"),
     "No degree is needed: you apply to a force and train on the job, or take the three-year "
     "police constable degree apprenticeship, which is paid throughout.",
     "You go back in at your previous rank where the force allows it, with a short refresher "
     "rather than the full training again."),
    # The trades are split where the length is: gas, electrics and plumbing end in a registration
    # scheme that adds a year or two, and a chef does not.
    (("electrician", "plumber", "plumbing", "gas engineer"),
     "Three to four years for a level 3 apprenticeship, which is how nearly everyone gets in, and "
     "the gas or electrics registration adds a year or two after that.",
     "A level 2 refresher and the registration assessment rather than the whole apprenticeship."),
    (("chef",),
     "Two to three years as a commis chef through an apprenticeship or a college course, and you "
     "are paid from the first week.",
     "A short refresher in a kitchen and the level 2 assessment rather than the whole thing again."),
    (("mechanic", "carpenter", "bricklayer", "joiner"),
     "Three to four years for a level 3 apprenticeship, which is how nearly everyone gets in.",
     "A short refresher and the level 2 assessment rather than the whole apprenticeship."),
)

# The shapes a line asks the length in. The row only asks this of a line that names a job, so a
# "how long" about a chicken is never near it.
_ASKS_THE_LENGTH = re.compile(
    r"(?<![a-z])(?:how many years|how many months|how long|what length|"
    r"years of study|length of the course|length of the training)(?![a-z])")

# A person who has done the job before is asking about the shorter route back in, not about
# starting again. The words can come from the line or from the line it leans on, which the
# understanding hands over as part of `clean`.
_DONE_IT_BEFORE = re.compile(
    r"(?<![a-z])(?:retrain|retraining|retrained|go back to|going back to|went back to|"
    r"return to|returning to|returned to|years ago|used to be|i was a|i used to work|"
    r"lapsed|let it lapse|on a break|career break|years out|years off|years away)(?![a-z])")


def _the_job_row(text):
    """The JOB_LENGTHS row a text names, or None."""
    words = " " + str(text or "").lower() + " "
    for names, length, returning in JOB_LENGTHS:
        for name in names:
            if re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", words):
                return names, length, returning
    return None


def _the_length_answer(clean, memory=None):
    """The years a job takes, when the line asks how long and names one, or None.

    The job is remembered in `memory["career"]` so a follow-up two turns later, which names no
    job of its own, is still answered as the first line was: "i was a nurse years ago", "do i
    need to retrain", "how long would it take" is one question about nursing.
    """
    said = str(clean or "").lower()
    row = _the_job_row(said)
    if row is not None and isinstance(memory, dict):
        memory["career"] = row[0][0]
    elif row is None and isinstance(memory, dict) and isinstance(memory.get("career"), str):
        row = _the_job_row(memory["career"])
    if row is None or not _ASKS_THE_LENGTH.search(said):
        return None
    _, length, returning = row
    if returning and _DONE_IT_BEFORE.search(said):
        return returning
    return length


def _career_subjects(memory, understood):
    """The subjects a named job asks for, from the one table, or the general advice.

    A line that asks how long gets the years first, because the length and the requirements are
    two different questions and this row was answering both with the requirements.
    """
    clean = ((understood or {}).get("clean") or "").lower()
    length = _the_length_answer(clean, memory)
    if length:
        return length
    row = _the_job_row(clean)
    if row is not None and isinstance(memory, dict):
        memory["career"] = row[0][0]
    for names, reply in CAREER_SUBJECTS:
        for name in names:
            if re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", clean):
                return reply
    return THE_GENERAL_CAREER


ENTRIES.append(entry(
    "career-subjects",
    (("gcse", "gcses", "a level", "a levels", "alevels", "subjects", "grades", "qualifications",
      "entry requirements", "requirements",
      # not the bare "points": "whats the point of a dehumidifier", "whats the point of a will"
      # and "whats the point of leaving the heating on" all reached this entry on "point" read
      # as "points", with "what" in the second part making up the rest of the score. Only the
      # shapes that ask how many are a question about entry requirements.
      "ucas points", "how many points", "points do i need", "points needed", "points for",
      # the job on its own is the question too: "what do i need to be a vet" names no exam
      "nurse", "nursing", "midwife", "midwifery", "doctor", "medicine",
      # "teacher" is not here on its own: a vaccine teaches the body, so the entry would take a
      # science question. The forms below are only ever about the job.
      "a teacher", "teachers", "primary teacher", "secondary teacher", "teacher training",
      "teach primary", "teach secondary",
      # "is teaching a good career" names the job and was the shrug, because the first group
      # wanted "teacher" and "teach primary". "teaching" is not here without the fence below:
      # teaching a dog to sit is dog training.
      "teaching",
      "vet", "veterinary", "lawyer", "solicitor", "barrister", "engineer", "engineering",
      "accountant", "accountancy", "accounting", "electrician", "plumber",
      "mechanic", "chef", "carpenter", "bricklayer", "joiner", "paramedic"),
# "to be" is not here on its own: chat-speak expands "tbh" to "to be honest", so a bare
     # "to be" turned "im a nurse on nights tbh" into a question about the subjects for nursing.
     # "be a" and "to become" are only ever about the job.
     ("need", "needs", "needed", "require", "requires", "required", "be a", "be an", "to be a",
      "to be an", "become", "becoming", "get into", "getting into", "get on", "take", "want",
      # the going-back shape asks what the requirements are, and without it the row was
      # gated out on a line that names the job and nothing else
      "go back to", "going back to", "return to", "returning to",
      "should i take", "what", "which", "for", "how",
      # the job named with the question about going into it and nothing else: "is nursing a good
      # career" and "should i go back to nursing after 10 years" were a "That's beyond what I know"
      # hedge, and the requirements are what that person needs first
      "good career", "a good career", "career", "careers", "retrain", "retraining", "retrained",
      "go back to", "back to", "return to", "job", "jobs", "worth it",
      # the going-back shape is the same question as "what do i need", and the ask gate below
      # wanted a word it never had: "should i go back to nursing after 10 years" and "return to
      # nursing after a break" are inside `ask` too, not only the key.
      "going back to", "returning to", "after 10 years", "after five years", "after 5 years",
      "after ten years", "years off", "years out", "years away")),
    _career_subjects,
    # a bad grade, results day and the revision plan are their own answers, and a driving test
    # or an eye test wants nothing from the school table
    avoid=NOT_AN_EXAM + MOCK + (
                                # "whats the point of any of it" is not a question about UCAS
                                # points: the row keys on "points" and asks for "what", so a
                                # despair line matched on a near-miss and got GCSE entry
                                # requirements (urban-orange, from the hourly watch on 356d4410,
                                # #4527). The objectless shapes - any of it, it all, all of this,
                                # point anymore - are never a question about a subject.
                                "point of any", "point of it", "point of this", "point of all",
                                "point of that", "point anymore", "no point", "any point",
                                # A season's points are not the tariff's either, and the sport
                                # cards that know them are on the same table: "how many points
                                # does an f1 win get" was this row's GCSE entry requirements
                                # while `f1-points` in sport.py was holding the right answer,
                                # and "how many points did we score" the same. The sport's own
                                # words only - "team" and "match" are left alone, because "a
                                # team" and "matching the offer" are school lines.
                                "f1", "formula 1", "formula one", "grand prix", "motogp",
                                "podium", "pole position", "try", "tries", "goal", "goals",
                                "touchdown", "conversion", "rugby", "football", "soccer",
                                "cricket", "netball", "basketball", "hockey", "tennis",
                                "league", "score", "scored", "scoring", "season",
                                # And the licence's points are the third sense: "how many points
                                # on my licence" is the driving card's line, not the tariff's.
                                "licence", "license", "penalty points", "speeding", "driving",
                                "banned", "parked", "road", "motorway", "insurance",
                                # asking a teacher for help is study.py's ask-teacher row, and
                                # the asking shapes are not a question about the entry grades:
                                # "how do i ask a teacher for help" was the PGCE answer.
                                "ask a teacher", "ask my teacher", "ask the teacher",
                                "ask a lecturer", "ask my lecturer", "ask the lecturer",
                                "ask my tutor", "ask a tutor", "email my teacher",
                                "email a teacher", "email my lecturer", "email my tutor",
                                "ask for help", "for help", "struggling", "how do i ask",
                                "a question for", "ask a question",
                                # a teacher you are unhappy with is a complaint, not a career:
                                # "how do i complain about my teacher" was the PGCE route
                                # choosing a subject is the course-choice row's line: "how do i
                                # choose my gcses" reached the entry requirements for a degree on
                                # "gcses" and "how"
                                "choose", "choosing", "choice of", "pick", "picking",
                                "my options", "options evening", "options form",
                                "complain", "complaint", "complaining", "rude", "unfair",
                                "shouted at me", "picked on", "my grades are",
                                "results day", "i got a", "got a grade", "bad grade", "failed",
                                "resit", "remark", "revise", "revising", "revision",
                                # The bare "account" and "accounts" chips that stood here are
                                # gone: `_forms` folds accountant, accountancy and accounting to
                                # the same stem as "account", so the chips kept "how do i close my
                                # amazon account" out - and also "how do i get into accounting"
                                # and "what gcses do i need to be an accountant", which are this
                                # row's own lines. The ask fence above is the guard that does the
                                # job without taking them, and the owned shapes ("my account",
                                # "current account", "account details", "gas account") are
                                # already in this list further down.
                                # "my dog needs a vet" and "the boiler needs a plumber" are a
                                # pet and a repair, not a career
                                "my dog", "my cat", "my pet", "the dog", "the cat", "puppy",
                                # "teaching" is in the subject list now, and teaching a pet or
                                # a child to do something is not a career question
                                "teach my", "teaching my", "teach a dog", "teach the dog",
                                "teach him", "teach her", "teach them", "teach it",
                                "how to teach", "teach someone", "teach me",
                                "kitten", "rabbit", "hamster", "horse", "pony", "livestock",
                                "boiler", "leak", "leaking", "dripping", "blocked", "fuse",
                                "fuse box", "rewire", "wiring", "socket", "sockets", "radiator",
                                "drain", "toilet", "tap", "shower", "washing machine",
                                # finding or hiring one is the household-fix question, not the
                                # route into the trade: "how do i find a good plumber" was the
                                # apprenticeships answer, on "plumber" plus "find a"/"how"
                                "find a", "finding a", "how do i find", "where do i find",
                                "recommend", "recommended", "recommendation", "hire", "hiring",
                                "a good plumber", "a good electrician", "a good builder",
                                "a good decorator", "a good roofer", "trustworthy",
                                "reputable", "cowboy", "quote", "quotes", "tradesperson",
                                "tradesman", "a decent plumber", "a reliable plumber",
                                "find a good", "find a reliable", "find a decent",
                                "i need a plumber", "i need an electrician",
                                "i need a mechanic", "call a plumber", "call an electrician",
                                "call a mechanic", "car needs", "car wont", "car won't",
                                # "what grade is my netball team" is a league and a piano grade
                                # is a music exam: neither of those is a question about school
                                "team", "teams", "league", "netball", "football", "rugby",
                                "hockey", "cricket", "climbing", "bouldering", "piano",
                                "guitar", "violin", "flute", "music", "ballet", "dancing",
                                "drums", "singing", "road", "path", "flight", "hotel",
                                "restaurant", "steak", "coffee", "beef", "petrol", "diesel",
                                # "what does a nurse do all day" is about the job itself
                                "what does a", "what do a", "do all day", "day to day",
                                "a day in the life",
                                # a shopping line can carry "what should i" and reach this
                                # table on the words alone: "what should i buy" after a curry
                                # got the university entry requirements. What to buy is never
                                # what a course asks for.
                                "buy", "buying", "bought", "shopping", "shop for",
                                # the bank account, the doctor's appointment and the vet bill
                                "bank", "joint", "savings", "current account", "my account",
                                "the account", "an account", "account number", "account details",
                                # the plural is the one people use for passwords and for
                                # paperwork: "how do i keep my online accounts safe" reached
                                # these entry requirements on "accounts"
                                # "accounts" on its own is gone with the singular: it folds from
                                # "accounting" too, which is why "how do i get into accounting"
                                # was the shrug on main. The owned shapes below still stand.
                                # A phrase in this list only stands the row down when its words
                                # sit together, so "my account" could not see "my facebook
                                # account" and the whole class went to the university page: an
                                # account with a name in front of it is an app or a website, not
                                # a course. The bare "account" cannot be fenced here, because
                                # "accounting" folds to it and "how do i get into accounting" is a
                                # careers line; the names are what make it an app account.
                                "my accounts", "online accounts",
                                "google", "facebook", "instagram", "snapchat", "tiktok",
                                "twitter", "linkedin", "social media", "gmail", "outlook",
                                # "what gcses do i need to be a doctor" is a career line, so a bare
                                # "a doctor" cannot be a fence; the shapes that are an appointment
                                # are named instead
                                "see a doctor", "my doctor", "the doctor", "book a doctor",
                                "book", "booking", "register with", "doctor's", "gp", "surgery",
                                "nhs", "hospital", "appointment", "waiting list", "referral",
                                "i feel", "im feeling", "i am feeling"),
    # the line has to be about getting in or about the subjects, not just carrying a "need":
    # "i need to change my bank account to the joint one" and "i need to see a doctor" both
    # reach a career word ("accountant" starts with "account") and neither is a career
    # What makes a line a question about what to study for a job, and nothing else. The bare
    # "what", "which" and "how" stood here, and they are the reason the key's "accounting" could
    # reach the careers table: `lookup._forms("accounting")` collapses to "account", so "how do i
    # close my gas account" matched accounting plus the asking word and was answered with
    # A-levels. Taking "accounting" out of the key would lose "how do i get into accounting", and
    # a bare "account" in avoid takes "what gcses do i need to be an accountant", because avoid
    # matches prefixes. A fence on the study words does neither: a line about a gas account names
    # no subject, no exam and no route in.
    ask=("become", "becoming", "be a", "be an", "to be a", "to be an", "get into",
         "getting into", "qualify", "qualified", "train", "training", "study", "studying",
         "subjects", "subject", "grades", "grade", "gcse", "gcses", "a level", "a levels",
         "alevels", "qualifications", "qualification", "requirements", "entry requirements",
         "ucas", "ucas points", "points", "degree", "university", "college", "apprenticeship",
         "course", "career", "careers", "work experience", "what does", "what do i need",
         "what will i need", "how long does",
         # the going-back shape asks what the requirements are: "should i go back to nursing
         # after 10 years" and "return to nursing after a break" name the job and the going
         # back, and with no ask word the fence below stood the row down and the line was a
         # shrug (before this branch it was the breastfeeding card).
         "go back to", "going back to", "return to", "returning to",
         # "is a job in nursing worth it" asks the same thing as "is nursing a good career"
         "job", "jobs", "worth it"),
    bias=1))

# "how many hours can i work as an apprentice" was answered with how to find an apprenticeship:
# the how-to row answers where the vacancies are, and the hours are a fact about the job.
# "what is a dissertation" and "what is a phd" met the essay-marks card and a search hedge: the
# long pieces of work have a shape of their own and nobody had written it down. Both rows are keyed
# on the thing being asked about, so a question about marks, revision or an extension keeps its own
# answer.
ENTRIES.append(entry(
    "dissertation",
    # bare "thesis" is the thesis statement of an essay, which has its own answer
    (("dissertation", "dissertations", "final year project", "final project",
      "undergraduate thesis", "masters thesis", "doctoral thesis", "capstone project"),
     ("what", "whats", "what is", "mean", "means", "definition", "how long", "how many words",
      "how do i", "how to", "start", "starting", "begin", "structure", "write", "writing",
      "word count", "length", "supervisor", "plan", "planning", "is a", "for")),
    "A dissertation is one long piece of work - usually 8,000 to 12,000 words for a bachelor's "
    "and up to 20,000 for a master's - where you answer one question of your own with evidence, "
    "rather than showing what you know about a subject. It is marked on the question, the reading "
    "and the argument, in that order. Start with a question narrow enough to answer in the word "
    "count, then a plan of four or five chapters, then read for that plan only. Book two "
    "supervisor meetings before Christmas and take a written note of what was agreed at each one: "
    "the students who fall behind are the ones who go quiet, not the ones who ask.",
    # a supervisor who never replies is a person problem, not a definition: the working-with-
    # people row answers it ("ask twice in writing, then copy one person above")
    avoid=NOT_REVISION + ("marks", "mark", "grade", "grades", "extension", "extend",
                          "deadline", "late", "penalty", "plagiarism", "reference",
                          "supervisor never", "supervisor wont", "supervisor does not",
                          "supervisor doesnt", "supervisor ignores", "supervisor is useless",
                          "supervisor is awful", "my supervisor", "my tutor never"),
    bias=1,
))

ENTRIES.append(entry(
    "phd",
    # not "masters"/"msc"/"ma": "what is a masters degree" is the degree, and it was answered
    # with three to four years of original research
    (("phd", "ph.d", "doctorate", "doctoral", "dphil", "postgraduate research", "phd thesis"),
     ("what", "whats", "what is", "mean", "means", "definition", "how long", "how many years",
      "worth it", "should i", "funding", "funded", "cost", "how do i", "apply", "difference",
      "is a", "do i need", "for")),
    "A PhD is three to four years of full-time original research under a supervisor, ending in a "
    "thesis of about 60,000 to 80,000 words and a spoken exam called a viva: it trains you to "
    "produce new knowledge, and it is not required for most jobs outside research. Look for a "
    "funded place first - a studentship pays fees and a stipend, and the funded ones are "
    "advertised on FindAPhD and on university pages - because self-funding a PhD is expensive for "
    "the career it buys. Write to a named supervisor with a two-page proposal and ask what they "
    "have funding for, rather than applying to a department in general.",
    # "should i do a phd or get a job" is the decision card's line, not the definition's, and
    # "how do i prepare for an interview for a phd" is the interview card's
    avoid=NOT_REVISION + ("marks", "grade", "grades", "essay", "revision", "exam", "gcse",
                          "a level", "child", "children", "kid", "kids", "my son", "my daughter",
                          "or get a job", "or a job", "phd or", "masters or", "or a masters",
                          "worth it", "worth the money", "worth the cost", "worth the debt", "interview",
                          # "should i do a phd", with nothing after it, is the same choice line as
                          # "should i do a phd or get a job" and was still reading the definition
                          "should i do", "should i", "is it worth", "should i bother",
                          "interview for", "prepare for an interview"),
    bias=1,
))

# "im dyslexic and reading takes forever" was a shrug. It is a study question with real answers,
# and the school and university help is what the person is asking about.
ENTRIES.append(entry(
    "dyslexia-reading",
    (("dyslexic", "dyslexia", "reading is slow", "reading takes forever", "reading takes me ages",
      "words jump", "words move on the page", "letters move", "read slowly", "slow reader"),
     ("read", "reading", "study", "studying", "revision", "revise", "exam", "exams", "uni",
      "university", "school", "college", "how do i", "help", "cope", "takes forever", "slow",
      "takes me", "struggle", "struggling")),
    "Ask for the formal help first: a dyslexia assessment at university goes through the "
    "disability service, and it unlocks extra time in exams, a reader or text-to-speech software, "
    "and often a grant for equipment - at school it is the SENCO, and it costs you nothing to ask. "
    "For the reading itself, use text-to-speech so the page reads to you while you follow with a "
    "finger, take the chapter in 20-minute blocks with the summary read first, and ask for the "
    "reading list in advance so you are never reading against a deadline. Being slow at decoding "
    "is not being slow at thinking, and the extra time is the standard fix, not a favour.",
    avoid=("my son", "my daughter", "my child", "my kid", "year old", "toddler", "baby",
           "spelling test", "handwriting"),
    bias=1,
))

# A university essay is not a work report: `missed-deadline` in work.py stands aside for
# "university", "coursework", "essay" and "dissertation" on purpose, and nothing answered them.
EXTENSION_ASK = ("extension", "extensions", "extend", "mitigating circumstances", "mitigation",
                 "extenuating circumstances", "special circumstances", "more time",
                 "late submission", "submit late", "hand in late", "extra time")
# "report" and "project" are not here on their own: "im going to miss the deadline for the
# report" is work.py's missed-deadline card, and a lab report names its own kind.
ESSAY_WORDS = ("essay", "essays", "coursework", "assignment", "assignments", "dissertation",
               "project write-up", "lab report", "thesis", "submission", "portfolio",
               "exam", "exams", "module")

ENTRIES.append(entry(
    "essay-extension",
    ((EXTENSION_ASK + ("deadline", "deadlines")),
     (ESSAY_WORDS + ("how do i", "ask", "asking", "get", "apply", "tutor", "lecturer",
                     "teacher", "professor", "module leader", "uni", "university", "school",
                     "college", "who do i", "can i", "what do i", "email", "form"))),
    "Ask the module leader or tutor before the deadline, in writing, with the date you need - and "
    "ask what the evidence rule is at your place, because it is a form with a name: mitigating "
    "circumstances, extenuating circumstances or special circumstances. Send the form and the "
    "evidence (a GP note, a letter, a hospital appointment) in one email, and keep a copy. The "
    "standard extension is a week or two for a short illness; longer or repeated problems go to "
    "the mitigating circumstances panel rather than to your tutor. Ask early: most universities "
    "will not accept a claim made after the deadline has passed, and asking costs nothing.",
    avoid=("boss", "manager", "client", "at work", "my job", "council", "tax return", "visa",
           "rent", "landlord", "planning permission", "mortgage", "insurance"),
    # an extension at work is language.py's deadline-extension and work.py's unreasonable
    # deadline: this row is only the school and university one, so it needs a study word on
    # the line and not just "deadline" and "how do i".
    ask=ESSAY_WORDS + ("mitigating circumstances", "mitigating", "extenuating", "tutor",
                       "lecturer", "module leader", "professor", "uni", "university",
                       "school", "college"),
    bias=1,
))

ENTRIES.append(entry(
    "missed-essay-deadline",
    # "missed my coursework deadline" puts a word in the middle of "missed my deadline", so the
    # piece of work is named in the first group as well as the second
    (("missed the deadline", "missed my deadline", "miss a deadline", "missed a deadline",
      "handed in late", "submitted late", "late submission", "missed the submission",
      "deadline passed", "deadline has passed", "deadline gone", "didnt submit",
      "didn't submit", "wasnt in on time", "wasn't in on time",
      "missed my coursework", "missed the coursework", "missed my essay", "missed the essay",
      "missed my assignment", "missed my submission", "coursework deadline", "essay deadline",
      "deadline for my essay", "deadline for the essay", "deadline for my coursework"),
     (ESSAY_WORDS + ("uni", "university", "school", "college", "module", "tutor", "lecturer",
                     "teacher", "what happens", "what now", "what do i do", "will i fail",
                     "fail", "penalty", "capped", "resit", "appeal", "talk to", "email"))),
    "Email the module leader today, before they chase you: say the piece is late, give the reason "
    "in one sentence and name the date you will submit. Most places take 10% off a day up to a "
    "cap of a pass mark for a few days, and the late penalty is usually shown on your marks "
    "breakdown - check your module handbook for the exact rule rather than guessing. If the "
    "reason was illness or something serious, ask for mitigating circumstances now: it can remove "
    "the late penalty and give you a resit as if for the first time. Silence is the only version "
    "where nothing can be fixed.",
    avoid=("boss", "manager", "client", "at work", "my job", "council", "tax return", "visa",
           "rent", "landlord", "planning permission", "mortgage", "insurance", "car", "mot",
           # a report for a manager, a client or a board is work.py's missed-deadline card
           "report", "the report", "the figures", "client", "board", "audit", "invoice"),
    # a line that has already missed its deadline is this card rather than the ask-in-advance one
    bias=2,
))

ENTRIES.append(entry(
    "apprentice-hours",
    (("apprentice", "apprentices", "apprenticeship", "apprenticeships"),
     ("hours", "hour", "how many hours", "how long", "time off", "holiday", "holidays",
      "overtime", "week", "a week", "work", "can i work", "allowed to work", "part time",
      "evenings", "weekends", "shifts")),
    "At least 30 hours a week of paid work, and an apprentice under 18 cannot be asked to do "
    "more than 40 hours a week or more than 8 hours a day. Everyone still counts the 28 days' "
    "paid holiday a year, bank holidays on top if the contract says so, and the off-the-job "
    "training - about a fifth of the hours - happens inside your paid time rather than after it. "
    "Overtime is allowed if you are over 18 and it is in the contract, and the 48-hour average "
    "week limit applies as it does to any job.",
    bias=1,
))

# "my essay is due tomorrow" had nothing of its own: the essay rows answer how to write one and
# the revising row answers the exam, so the commonest version of this - the deadline is on top of
# the person and nothing is written - was answered with an echo of their own words. The answer is
# the order to work in and the extension, which are the two things that decide the week.
ENTRIES.append(entry(
    "a-deadline-and-nothing-written",
    (("essay", "essays", "assignment", "assignments", "coursework", "dissertation",
      "piece of work", "thesis",
      # "i have 2000 words due monday" names the work only by its length, and that is how the
      # panicking version of this question usually arrives
      "words", "word count"),
     # only the words that say the date is on them: a weekday or "tonight" on its own is
     # somebody getting on with it ("im doing my essay tonight"), not somebody panicking
     ("due", "deadline", "deadlines", "hand in", "hand-in", "handing in", "submit",
      "submission", "last minute", "behind",
      "havent started", "haven t started", "not started", "havent done", "haven t done",
      "left it", "running out of time", "no time"),
     # the row is about the thing being late, not about how to write it well, so it needs one of
     # these as well as the subject: "how do i write a dissertation" is the other row's question
     ("due", "deadline", "hand in", "hand-in", "submit", "submission", "last minute", "behind",
      "havent started", "haven t started", "not started", "havent done", "haven t done",
      "left it", "running out of time", "no time")),
    "Work backwards from the deadline: decide the three or four points that answer the "
    "question, put a heading for each, write the middle sections badly and fast, then the "
    "introduction and the conclusion last, then read it out loud once. Ask "
    "for a short extension today rather than after the deadline and put the request in writing, "
    "because most tutors will say yes before the date and almost none can after it. A complete "
    "plain answer scores more than a perfect first half, so hand in every section, even thin.",
    # the exam, the revision timetable and the how-to-write-it rows are different questions
    avoid=("revise", "revising", "revision", "exam", "exams", "mock", "past paper", "how do i",
           "how to", "how can i", "what should i write", "structure", "introduction",
           "conclusion", "reference", "references", "citation", "cite", "plagiaris",
           "spelling", "grammar", "word count", "grade", "marks",
           # a parent asking about the child's essay is the parent row's question, and a report
           # or a project at work is the "tell them early" row's
           "my son", "my daughter", "my kid", "my child", "my boy", "my girl", "my children",
           "his teacher", "her teacher", "the teacher", "school report", "at work",
           "my boss", "to my boss", "the boss", "for work", "client"),
    bias=1,
))


# --- a child who cannot write their name yet -----------------------------------------------
# "my 5 year old cant write his name" reached nothing at all, and the turn was answered as a
# style note about numerals ("write one to nine as words"). A five-year-old's handwriting is a
# development question, and the answer is what to try and when it is worth a look.
_CHILD = ("child", "children", "kid", "kids", "son", "daughter", "boy", "girl", "toddler",
          "youngest", "eldest", "reception", "reception class", "preschool", "nursery",
          "year old", "year-old", "4 year old", "5 year old", "6 year old", "7 year old")

# A name is the one thing a parent asks about with the age in front of it, and the answer is not
# the same at three and at seven. "my son cant write his name at 6" and "my daughter is 7 and cant
# write" were both told "Five is early for a name and nothing to worry about", which at seven is
# the opposite of the truth: most children write a recognisable name by five or six, so a seven
# year old who cannot wants a look at why rather than more reassurance. One card, three openings.
_AGE_SAID = (re.compile(r"\b(\d{1,2})\s*(?:year|yr)s?[\s-]*(?:old|young)\b"),
             re.compile(r"\b(?:is|at|aged|age|turned|nearly)\s+(\d{1,2})\b"),
             re.compile(r"\b(\d{1,2})\s*(?:and|,)\s*(?:cant|can't|cannot|doesnt|doesn't|"
                        r"still|only|hasnt|hasn't)\b"))


def _the_age_of_a_child(reading):
    """The age the line gives, or None. Three is three in "my son is 3" and "my 3 year old"."""
    said = " ".join(str((reading or {}).get("clean") or "").lower().split())
    for pattern in _AGE_SAID:
        found = pattern.search(said)
        if found:
            try:
                age = int(found.group(1))
            except (TypeError, ValueError):
                continue
            if 0 < age <= 18:
                return age
    return None


_WRITING_HAND = (
    "Give the hand other work first - threading, cutting, playdough, big chalk on the path - and "
    "practise the name in short bursts with a chunky pencil and a dotted version to trace, five "
    "minutes at a time and no more.")


def the_writing_card(memory, reading):
    """The handwriting answer at the age the line names (see `_AGE_SAID`)."""
    age = _the_age_of_a_child(reading)
    if age is not None and age <= 4:
        return ("At three or four that is not late at all: the shoulder and hand are still "
                "building, and a child who cannot write their name yet is exactly on time. "
                + _WRITING_HAND + " Nobody should be sitting a four year old down to drill it, "
                "and if a five year old cannot hold a pencil or copy a circle, that is worth a "
                "word with the health visitor.")
    if age is not None and age >= 7:
        return ("At seven this is past the usual age, so get it looked at rather than practised "
                "harder: most children write a recognisable name by five or six. Ask the teacher "
                "what it looks like in class, have hearing and vision checked, and if it is just "
                "the same at school ask about handwriting practice with an occupational therapist "
                "or the SENCO. Keep the practice at home short and keep the worry off it.")
    if age is not None:
        return ("Late but still inside normal, and worth a light touch rather than a push: most "
                "children write a recognisable name between four and six. " + _WRITING_HAND +
                " Ask the teacher whether the grip looks right, and if it has not moved by the "
                "end of the year get hearing and vision checked.")
    return ("Five is early for a name and nothing to worry about: the shoulder and hand are still "
            "building, so most children get a recognisable name somewhere between four and six. "
            + _WRITING_HAND.replace("Give the hand", "Give the hand") + " Worth asking nursery or "
            "the reception teacher whether the grip is right, and worth a word with the health "
            "visitor if a child of six cannot hold a pencil or copy a circle at all.")
ENTRIES.append(entry(
    "child-cant-write-his-name",
    (_CHILD,
     ("write his name", "write her name", "write their name", "write his own name",
      "write her own name", "writes his name", "writes her name", "writing his name",
      "writing her name", "write the name", "write name", "write his", "write her",
      "cant write", "can't write", "cannot write", "cant hold a pencil", "cant hold the pencil",
      "pencil grip", "holds a pencil", "hold a pencil", "holding a pencil", "pencil properly",
      "letter formation", "write letters", "writing letters", "recognise his name",
      "recognise her name", "know his letters", "know her letters", "learn to write",
      "scribbles", "wont write", "hates writing", "hate writing")),
    the_writing_card,
    # an adult's handwriting, a spelling question and a school-place question are other rows
    avoid=("my handwriting", "handwriting", "my writing", "neater", "neatly", "spelling",
           "grammar", "signature", "copy", "font", "illegible", "my notes", "my essay",
           "school place", "choose a school", "apply for a school", "adult", "i cant write"),
    bias=1))


# --- a child who cannot sleep for the exams -------------------------------------------------
# "my daughter has exams and cant sleep" was answered "walk them back every time with the same
# short line - it's sleep time, I love you", which is the toddler-at-bedtime card: the child, the
# bed and the word sleep were all there, and the exam was not read as the reason. A parent's
# question about revision nerves is a different answer, and an older child is not walked back.
ENTRIES.append(entry(
    "child-exam-nerves",
    (("exam", "exams", "tests", "mocks", "revision", "revising", "gcses", "gcse", "a levels",
      "a level", "sats", "school tests"),
     _CHILD + ("teenager", "teenagers", "teen", "year old", "year-old", "15 year old",
               "16 year old", "17 year old", "she", "he"),
     ("cant sleep", "can't sleep", "not sleeping", "wont sleep", "won't sleep", "up late",
      "staying up", "awake", "tired", "nervous", "worried", "worry", "stressed", "stress",
      "anxious", "panic", "crying", "cries", "not eating", "off their food", "revision")),
    "Take the pressure off the night, not the work: the revision is done by then, so the job is a "
    "fixed stop time, the phone out of the room, and something that is not revision for the hour "
    "before bed. Keep the worry concrete - ask what they are most afraid of forgetting, write it "
    "down and leave it on the desk, because a written worry stops the circling. If the exams are "
    "weeks away and sleep is still gone, or they are not eating or cannot get to school, tell "
    "their tutor, because that is worth more than any technique.",
    # The symptom has to be in the line, not just the exam: "my daughter is starting exams next
    # week" carries an exam word and a child word already, so the row answered a line with no
    # complaint in it with an answer about the night (red-wasp, #answers). `ask` is the slot for
    # words the line must also carry.
    ask=("cant sleep", "can't sleep", "not sleeping", "wont sleep", "won't sleep", "up late",
         "staying up", "awake", "tired", "nervous", "worried", "worry", "stressed", "stress",
         "anxious", "panic", "crying", "cries", "not eating", "off their food", "nerves"),
    # the child in bed with no exam, the adult's own revision and an illness are other rows
    avoid=("my exams", "my revision", "im revising", "i cant sleep", "i can't sleep",
           "i am revising", "toddler", "baby", "cot", "crib", "nursery", "my exam",
           "my test", "my driving test", "blood test", "pregnancy test", "urine"),
    bias=1))
# Changing your mind about a subject or a course, once it has started, is one of the commonest
# things a person in their teens or twenties asks, and nothing owned it. On main the whole
# cluster was answered by whatever else the words touched:
#
#   is it too late to change a level subjects     -> "I don't know enough to answer that"
#   can i change my a level subjects in year 12   -> the search hedge
#   can i switch courses at uni in first year     -> the search hedge
#   i picked the wrong a levels                   -> how to choose your subjects (start again)
#   how do i change my a levels                   -> the entry requirements card
#   is it too late to change my degree            -> what a degree passes at (40%, a 2:1...)
#   i hate my uni course what can i do            -> the same pass-marks card
#   can i change my gcse options in year 10       -> the missed-their-offer / Clearing card
#   i want to drop a subject in year 12           -> the entry requirements card
#
# The question is a yes/no about timing ("is it too late") and then the move, so the answer
# starts with when it is still possible and names who to ask, at school and at university,
# because those are two different processes with the same words.
_ASKED_TO_MOVE = ("how", "what", "when", "which", "why", "can i", "could i", "should",
                  "should i", "do i", "is it", "too late", "wrong", "regret", "hate",
                  "want to", "worth it", "thinking of", "considering", "decided", "allowed",
                  "possible", "advice", "help", "best",
                  # A year is the whole ask in half this cluster: "switching courses in second
                  # year" carries no question word at all, and the move and the year together
                  # are the question.
                  "first year", "second year", "third year", "year 10", "year 11", "year 12",
                  "year 13", "halfway through", "just started", "already started")

# The announcement of a topic shift, which is this row's own words run into the line: "changing
# subject" on its own is somebody moving the conversation on. The answers module reads that line
# with the turn before it put back in ("what about changing subject"), so the shape and not the
# words has to tell the two apart: a line that is only the announcement, with nothing about a
# course, a subject name or a year of its own, asks nothing.
_THE_ANNOUNCEMENT = ("changing subject", "changing subjects", "changing the subject",
                     "changing topic", "changing the topic", "change topic", "change of subject",
                     "moving on", "next subject", "different subject", "different topic")
_LEAD_IN = ("what about", "how about", "what", "and", "but", "so", "ok", "okay", "anyway",
            "right", "well", "now", "then", "also", "plus", "just", "let us", "lets",
            "let's", "can we", "can i", "could we", "shall we", "maybe")


def _asks_to_move(understood):
    """True when the line itself asks something.

    "changing subject" on its own is somebody moving the conversation on, and the answers module
    reads that line with the turn before it put back in, which is how it reached this row: the
    line has the two words and the earlier turn has the "what". The row keys "changing subject"
    because that is how the question is typed ("changing subject at-a-level, is it too late"),
    so the difference between the two has to be read from the shape of the line, not from its
    neighbours - and not by fencing the phrase, because that fence also stood the row down for
    the question that starts with it.
    """
    said = " " + " ".join(str((understood or {}).get("plain")
                              or (understood or {}).get("text") or "").lower().split()) + " "
    bare = said.strip(" .,!?;:-\u2026")
    changed = True
    while changed:
        changed = False
        for lead in _LEAD_IN:
            if bare == lead or bare.startswith(lead + " "):
                bare = bare[len(lead):].strip(" ,")
                changed = True
    if bare in _THE_ANNOUNCEMENT:
        return False
    return any((" " + word + " ") in said or said.startswith(" " + word + " ")
               or said.rstrip().endswith(" " + word) for word in _ASKED_TO_MOVE)
ENTRIES.append(entry(
    "change-subject-or-course",
    (("change", "changing", "changed", "switch", "switching", "swap", "swapping", "transfer",
      "transferring", "move", "moving", "drop", "dropping", "quit", "quitting", "hate",
      # "too late" on its own is not this question: "do you think its too late to start now"
      # (revising, three weeks from the paper) read it and got the change-course answer, so the
      # row asks for the move itself, which every version of this question does say.
      "hating", "wrong", "regret", "regretting", "stuck with",
      # The subject card keys "a level" and "how", the pass-mark card "uni" and "course", and
      # both are wider than this row: the phrases below are the sentence this question is
      # actually asked in, and they put this row above either of them on score alone.
      "change my a level", "change a level", "change my a levels", "change a levels",
      "change my subject", "change subjects", "change my course",
      "change course", "change courses", "change my degree", "change degrees",
      # the -ing phrases are how this question is actually typed ("changing subject at
      # a-level, is it too late", "switching courses in second year"), and a bare form of the
      # verb only scores as one word
      # "changing subject" on its own is not here: it is how somebody announces a topic shift,
      # and the answers module reads that line with "what about" in front, which satisfies the
      # ask. "changing subject at-a-level, is it too late" reaches the row on "changing" and
      # "a-level" alone.
      "changing subjects", "changing course", "changing courses",
      "changing degree", "changing my degree", "changing my course", "changing my subjects",
      "switching subject", "switching subjects", "switching course", "switching courses",
      "switching degree", "switching degrees", "switching my course",
      "switch course", "switch courses", "switch degree", "switch degrees",
      "wrong a levels", "wrong a level",
      "hate my course", "hate my uni", "hate my degree", "regret my degree",
      "regret my course", "too late to change"),
     ("a level", "a levels", "a-level", "as level", "subjects", "subject", "course", "courses",
      "degree", "uni", "university", "college", "gcse", "gcses", "sixth form", "year 12",
      "year 13", "year 10", "first year", "second year", "apprenticeship")),
    ("You can usually still change it, and the sooner you ask the easier it is: at school or "
     "college, go to the head of sixth form or the exams officer, and a change is normally "
     "possible in the first two or three weeks of Year 12 - after that it is their call, and how "
     "much you would catch up that decides it. At university, ask your personal tutor or the "
     "course leader about transferring to another course at the same place before you think "
     "about leaving, which is usually easier than a fresh application through UCAS or Clearing. "
     "Changing after a full year costs money as well as time, because student finance does not "
     "normally fund a second first year."),
    # A topic shift is the same two nouns with no question in it: "changing subject" on its own
    # is somebody moving the conversation on, so the row only answers a line that asks - and
    # "changing subject at a-level, is it too late" asks.
    # The same words decide both questions - does this line ask, and does it ask the move - so
    # they are one tuple: drift between the guard and the ask would leave the guard deciding.
    ask=_ASKED_TO_MOVE,
    guard=_asks_to_move,
    # "can we change the subject" is small talk about the conversation, not a school question,
    # and the rest are the everyday things the two words "change" and "course" also name
    # `work`'s drop-a-level card is the same question asked the narrow way - one A level given
    # up, exam entry deadlines, whether three is enough - and it answers that better than this
    # row can, so it keeps those lines: "how do i drop a subject at a level" and "should my
    # daughter drop a level" were both its answer on main.
    avoid=("drop a subject", "drop my subject", "drop an a level", "drop a level",
           "drop one of my a levels", "drop one of my", "dropping a level", "dropping an a level",
           "drop as level", "quit a subject", "give up a subject", "dropping a subject",
           # The topic shift is stood down by the guard above and not by a phrase here: the
           # words of the announcement are also the start of the question ("changing subject
           # at-a-level, is it too late"), and fencing them took both to the punt.
           "change the subject", "the subject to",
           # Changing your mind about an offer is accepting or declining it, not a transfer, and
           # the card sends that person to the head of sixth form.
           "course offer", "university offer", "uni offer", "firm offer",
           "job", "jobs", "boss", "career", "careers", "my work", "at work", "address", "bank",
           "energy", "supplier", "broadband", "mobile", "insurance", "password", "email",
           "car", "boiler", "vet", "dog", "cat", "recipe", "diet", "gym", "running", "hair",
           "doctor", "medication", "dressing", "nappy", "light bulb", "bedding", "taps",
           # a course of treatment, and a change for the better in how somebody feels
           "course of", "steroids", "antibiotics", "how i feel", "my mood"),
    # the grade-meaning card keys "a-level" and "changed", so it ties with this row on
    # "changing subject at-a-level, is it too late"; the question there is the change, so a
    # bias breaks the tie without widening either key.
    bias=2,
))
# --- catching up after falling behind --------------------------------------------------------
# "how do i catch up at school" and "i missed a lot of school" were both hedges or, worse, the
# absence-penalty row: the school-absence answer is a parent's legal question, and this is the
# student's own - the work is to find the first gap and to get one adult involved. Catching up is
# not revising, so it is not the revision rows either.

CATCHING_UP = (
    "Find the first topic you stopped understanding rather than the newest one, because everything "
    "after it is built on it: go through the textbook contents or the topic list and mark the last "
    "thing that made sense. Then do three things - tell the teacher you have fallen behind and ask "
    "which two topics matter most for the next test, spend twenty minutes a day on those two only, "
    "and get one session with a classmate who is good at them. Catching up is a short list worked "
    "through patiently, not the whole course read again.")

ENTRIES.append(entry(
    "catching-up-at-school",
    # "catch up" on its own is a meeting ("catch up later" in a work chat belongs to the manager
    # catch-up row), and a bare "school" is a school to choose or a child's homework, so the
    # catching up is named as a phrase with the school in it
    # "behind on work" and "behind with work" were in this group and "work" in the next one, so
    # an adult with a backlog got a school topic list; the school is what has to be named, and a
    # person behind on their job keeps the row that picks the piece that finishes soonest.
    (("fallen behind", "fell behind", "behind at school", "behind in class",
     "catch up at school", "catch up in class", "catch up at college",
     "catch up on school", "catch up on schoolwork", "catch up on classwork",
     "catch up on lessons", "catch up on the work",
     # "catch up on everything" is not a school line: "i need to catch up on everything" was a
     # gentle "what's stopped it happening so far?" and this row answered it with a topic list,
     # so the phrase now needs the school word that follows it
     "catch up on everything at school", "catch up on everything in class",
     "catch up after being off", "catching up at school", "catching up in class",
     "missed a lot", "missed lessons",
     "missed school", "missed classes", "a lot of school", "months off school",
     "off school for months", "off school for weeks",
     "gaps in my knowledge", "dont understand anything", "don't understand anything",
     "no idea what is going on", "lost at school", "struggling at school", "struggling in class",
     "school work", "schoolwork", "classwork", "coursework"),
     ("how do i", "how", "catch up", "catching up", "help", "behind", "school", "class",
      "college", "teacher", "subject", "start", "should i", "what do i do")),
    CATCHING_UP,
    # the plain statement names no question word at all: "i missed a lot of school" was answered
    # with the absence-penalty row, because the ask gate wanted a "how" and the line has none
    ask=("how", "catch up", "catching up", "help", "behind", "start", "what do i do", "should i",
         "missed a lot", "missed school", "missed lessons", "missed classes", "a lot of school",
         "months off school", "off school for months", "off school for weeks"),
    # an illness is the health rows' question, a child who is behind is the parent's version of
    # it, an exam in three weeks is the revision rows', and behind on the rent is money's
    # A school that shuts for snow is a day to fill, not a term to catch up: "my children are off
    # school and its snowing" was answered with this row in a deck sweep until the bare "off
    # school" went, so the phrase is named only with the months and weeks that mean a term.
    avoid=("ill", "illness", "sick", "hospital", "diagnosis", "anxiety", "depressed", "depression",
           "adhd", "autism", "dyslexia", "statement", "ehcp", "sen", "expelled", "excluded",
           "bully", "bullied", "bullying", "rent", "mortgage", "bill", "bills", "credit",
           "loan", "sleep", "penalty", "fine", "council", "truancy", "attendance",
           "snow", "snowing", "snowed", "snow day", "closed", "shut", "strike", "inset day",
           "holidays", "half term", "summer holiday", "bored", "my children", "my kids",
           "the children", "the kids", "toddler", "nursery",
           # A parent asking for their child is the parent's own version of this: on base
           # "my son has missed a lot of school" was the absence-penalty row, which is the
           # answer a parent needs, and this row told them "tell the teacher you have fallen
           # behind". "my children" was already here; a son, a daughter and a teenager are the
           # same speaker.
           "son", "sons", "daughter", "daughters", "child", "teenager", "teenagers", "teen",
           "stepson", "stepdaughter", "my boy", "my girl", "his school", "her school",
           "their school", "his teacher", "her teacher", "their teacher",
           # A backlog of work is the work rows' question: "i am behind on work" was answered
           # "pick the piece of it that finishes soonest" and this row's "behind on work" and
           # "work" took it to a school topic list. A school word still reaches the row.
           "email", "emails", "inbox", "deadline", "deadlines", "boss", "job", "jobs",
           "project", "projects", "client", "clients", "paperwork", "timesheet", "overtime",
           "workload", "office", "meeting", "meetings", "shift",
           "my work", "at work", "on my work", "for work", "with work", "his work", "her work"),
    bias=1))
