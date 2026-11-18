"""Normalisation: turn the way people type into ordinary words, once, for every module.

The understanding lane owns this file. `normalise(text)` cleans one line:

- chat-speak and shorthand ("u", "pls", "idk", "cn u", "wats") become ordinary words;
- apostrophes people leave out ("cant", "ive", "whats") are filled back in;
- contractions are expanded ("don't" -> "do not"), so a module can match the verb;
- obvious typos are corrected with one edit against the common-word lexicon, but only when
  the correction is unambiguous: a wrong fix is worse than no fix;
- letters people stretch ("sooo", "pleeease") are collapsed;
- run-on lines are split into clauses at discourse markers ("anyway", "so", "but"), and the
  clause that carries the ask is marked as the focus.

It returns a dict; nothing here reads `memory`, so it is safe to call on any line.
"""
import itertools
import re
import unicodedata

from . import lexicon

# One word, and a measure stays one word: "1.5kg", "20%", "1,500" and "don't" are each a
# single token, so a weight is never read as "one" and "5kg".
# A short name with a number in it is one word too, because that is what it is to the person
# who typed it: "p60", "p45", "a1", "m25", "s21", "b12", "t4". Split into "p" and "60" the
# name is lost, so a knowledge entry keyed on it never matches and a question about it reads
# as a question about a number.
_MEASURE = (r"[0-9]+(?:[.,][0-9]+)*[a-z%]*"
            r"|[a-z]{1,3}[0-9]+(?:[a-z]{1,3}[0-9]*)*(?![a-z0-9])"
            r"|[a-z]+(?:'[a-z]+)*")
WORD = re.compile(_MEASURE)
# The chat words `_chat_words_said_out` spells out in `clean`: what people type, and the phrase
# a reader has to see to answer it.
SAID_OUT = {word: lexicon.CHAT[word]
            for word in lexicon.PLAIN_EXPANDS | lexicon.PLAIN_ONE_WORD
            if word in lexicon.CHAT and word not in lexicon.EXPAND}

# The chat spellings whose meaning is one ordinary word, and which are not a word themselves, are
# spelled out in `clean` too: a reader matching on the line as it was typed never met "tomorrow"
# in "is it gna rain tmoz", so the one line in eight that is typed this way reached a reader that
# was written for the words the person meant. The letters are kept as typed ("grade c", "vitamin
# c", "plan b") - the positional readers own those - and so are the spellings that are an
# ordinary word with a sense of their own: "the cause of the leak" is not "because of the leak",
# and "cos" is a lettuce. "owt" is kept because the reading already tells its two senses apart by
# the word after it - "is owt else wrong" is anything, "owt the door" is out - and folding it
# first turned "anything wrong with my car" into "out wrong with my car". Three more were measured
# and taken back out: "wif" is as often a wife as it is with ("my wif is due in july" was read as
# "your with is due"), "wtf" opening a line is an exclamation and not a question ("wtf is going on"
# stopped being "Really? Tell me what happened" and became the how-are-you reply), and a "pressie"
# for a named person is a gift for them, where "present" and "cheap" together reach the whip-round
# row ("wots a good cheap pressie for a 60 yr old woman" got the tenner-for-a-colleague answer).
CHAT_KEPT_AS_TYPED = frozenset("""
    u ur urs yr yrs urself y r n k b c d v x ar av sed prob cause cos tho owt
    wif wtf pressie pressies prezzie prezzies prezzy
    """.split())
CHAT_AS_ONE_WORD = {word: meaning for word, meaning in lexicon.CHAT.items()
                    if " " not in meaning and word not in CHAT_KEPT_AS_TYPED
                    and word not in SAID_OUT}
SAID_OUT.update(CHAT_AS_ONE_WORD)

RAW_WORD = re.compile(_MEASURE)


# What a repaired word may become: the emergency words themselves, plus the gerunds the case
# patterns read ("havin chest pains" is "having chest pains").
URGENT_WORDS = frozenset(lexicon.URGENT_MISSPELLINGS.values()) | frozenset(("having",))

_ANY_WORD = re.compile(r"[a-z]+(?:'[a-z]+)*", re.IGNORECASE)


def respell_urgent(text):
    """The line as typed, with only a misspelt emergency word put right and nothing else moved.

    The reading has `norm_text`, but that splits clauses and drops the punctuation, and the
    safety module matches apostrophes ("can't breathe") and one line, so it cannot read it.
    This keeps the line as it was typed, word for word, and only puts back a word from the
    curated emergency table: "my son swalowed a coin" -> "my son swallowed a coin". Nothing
    else in the line is touched, so a module that reads it sees exactly what it read before
    for every line that is not an emergency with a misspelt word in it.

    The one other thing put back is a family word clipped to its initials, because that is a
    word the reading knows and the module cannot: "my dd fell off the slide" was answered with
    the falls answer for an older person, and "my daughter fell off the slide" gets the two
    questions a child's fall needs. The clipped word is only read after a possessive, and only
    when the word after it does not make it a thing of that name ("my ds wont charge" is still
    the console), which is the same guard the reading puts on it.
    """
    if not isinstance(text, str) or not text:
        return ""
    fixes = lexicon.URGENT_MISSPELLINGS

    def put(match):
        word = match.group(0)
        fix = fixes.get(word.lower())
        if not fix:
            # A left-off final g is a typo class the reader already trusts ("havin", "chokin"),
            # but here it has to land on the emergency words to be worth touching: "havin chest
            # pains" is the same emergency as "having chest pains".
            guessed = fix_typo(word.lower())
            return guessed if guessed in URGENT_WORDS else word
        keep = word[:1].isupper()
        # Keep the writer's capital: "Swalowed a coin" starts a sentence.
        return fix.capitalize() if keep else fix

    return CLIPPED_FAMILY.sub(_family_put_back, _ANY_WORD.sub(put, text))


# A clipped family word after a possessive, with the two words that follow it, so the guard
# that reads a thing of that name ("my ds wont charge", "my dd bra") still applies.
CLIPPED_FAMILY = re.compile(
    r"\b(?P<owner>my|our|his|her|their)\s+(?P<word>dd|ds|dh|mil|fil|sil|bil|oh|lo)\b"
    r"(?P<rest>(?:\s+[a-z']+){0,2})", re.IGNORECASE)


def _family_put_back(match):
    """The clipped family word read as the word it stands for, or the match left as it was."""
    rest = (match.group("rest") or "").split()
    after = rest[0].lower() if rest else None
    after_after = rest[1].lower() if len(rest) > 1 else None
    family = _family_short(match.group("word").lower(), match.group("owner").lower(),
                           after, after_after)
    if not family:
        return match.group(0)
    return match.group("owner") + " " + " ".join(family) + (match.group("rest") or "")


def _doubles_its_last_letter(word):
    """"get" gives "getting" and "throb" gives "throbbing": a one-beat word that ends in a
    consonant after a single vowel writes that consonant twice before -ing and -ed.

    Only the last syllable matters to English, and this has no way to hear the stress, so it
    asks for a word of one beat - "visit" and "open" are left alone, and so are words that end
    in a letter English never doubles ("fix", "play", "snow").
    """
    if len(word) < 3 or not word.isalpha():
        return False
    if word[-3] in "aeiou" or word[-2] not in "aeiou" or word[-1] in "aeiouwxy":
        return False
    return len(re.findall(r"[aeiou]+", word)) == 1


VOWEL_SET = frozenset("aeiou")
# A y does the work of an i in the words people misspell ("worryed" is "worried"), so the
# reader that hears one letter swapped for another has to count it as a vowel.
VOWEL_SET_OR_Y = VOWEL_SET | frozenset("y")


def _drops_a_final_e(word):
    """True for a word that loses its last e before an ending: "move" is "moving", "moved".

    Every word that ends in a silent e drops it before -ed and -er, so "agree" is "agreed",
    "free" is "freed", "eye" is "eyed" and "dye" is "dyed"; a word ending in "ee" keeps both
    letters only before -ing. That is the one ending the letter before the e is the whole
    question for ("seeing", "agreeing", "freeing"), and it is named in _keeps_its_e_before_ing:
    there is no rule in English that hears it.
    """
    return word.endswith("e") and len(word) > 2


def _keeps_its_e_before_ing(word):
    """True for a word whose "ee", "ye" or "oe" keeps both letters before -ing."""
    return len(word) > 2 and word.endswith(("ee", "ye", "oe"))


def _ing_form(word):
    """The -ing form of a word that ends in an e: "moving", "agreeing", "eyeing"."""
    return word + "ing" if _keeps_its_e_before_ing(word) else word[:-1] + "ing"


def _inflections(word):
    """The everyday forms of a word, so 'likes' and 'jeans' are not 'typos'."""
    out = set()
    if len(word) < 3 or not word.isalpha():
        return out
    # A y after a consonant is an i in every ending: "worry" is "worried", never "worryed", and
    # "worrys" is not a word either. Generating those forms put "worryed", "tryed", "copyed" and
    # "studys" in the lexicon, and a word the lexicon holds is a word the fixers may not touch -
    # so "im still worryed about it" could not be read as the feeling, and the person who typed
    # it got "Thanks for telling me" where the line as spelt right gets the worry answer.
    y_for_i = word.endswith("y") and word[-2] not in VOWEL_SET
    out.add(word + "ly")
    if not y_for_i:
        out.add(word + "s")
    if _doubles_its_last_letter(word):
        # "getting", "throbbing": the doubled form is the word, so the undoubled one is not.
        out.update((word + word[-1] + "ing", word + word[-1] + "ed", word + word[-1] + "er"))
    elif _drops_a_final_e(word):
        # "move" is "moving", not "moveing": the e goes before an ending that opens with a
        # vowel, and it was being written both ways, which put "moveing" in the lexicon as a
        # word of its own. It goes before -ed and -er either way ("agreed", "freed", "dyed"),
        # which is why only the -ing form asks about the letter before the e.
        out.update((_ing_form(word), word[:-1] + "ed", word[:-1] + "er"))
    else:
        out.add(word + "ing")
        if not y_for_i:
            out.update((word + "ed", word + "er"))
    if word.endswith("e"):
        out.update((word[:-1] + "ing", word[:-1] + "ed"))
    if word.endswith("y"):
        out.update((word[:-1] + "ies", word[:-1] + "ied", word[:-1] + "ier"))
    if word.endswith("s"):
        out.add(word[:-1])
    return out


_BASE = (
    lexicon.COMMON.split() + lexicon.CORE.split()
    + " ".join(lexicon.CHAT.values()).split()
    + " ".join(lexicon.EXPAND.values()).split()
    + " ".join(lexicon.MISSPELLINGS.values()).split()
    + " ".join(lexicon.REAL_WORDS).split()
)
BASE = frozenset(_BASE)
LEXICON = BASE | frozenset(f for word in _BASE for f in _inflections(word))
COMMON_RANK = {word: i for i, word in enumerate(lexicon.CORE.split() + lexicon.COMMON.split())}

# "me" where a possessive is meant, in the one shape the pass below cannot see.
#
# `possessive_me` already repairs most of British chat-speak's possessive "me" - "me sister is
# coming at the weekend", "wher me phone", "me car wont start", "me head is banging" - and it
# knows the words that make "me" the object instead ("she told me mum died" told me that Mum
# died, "give me car keys back" is the keys). Two shapes fall outside it:
#
#   "it does me head in"   "head" is not a kin word, so the idiom that ends in "in" - do someone's
#                          head in - was read as the pronoun and the line as an acknowledgement.
#   "doin me ed in"        the "h" is clipped, so the word after "me" is not a word at all and
#   "doin me ead in"       the repair stops at "me ead" -> "my ead".
#
# So this pass carries only those two, and asks the same question the other one asks: is the thing
# the end of the phrase? "me head in" and "me ed ..." close the phrase, "me head office" and
# "me ed office" do not, and nothing here touches a line `possessive_me` already reads.
# What may follow a "me" this file thinks is a possessive: a verb, a preposition, a joiner, an
# adverb, punctuation or the end of the line. A thing can go on naming a thing ("head office",
# "car keys"), and there the "me" is somebody's object, so that word is not in the list.
ME_FOR_MY_CLOSES = frozenset("""
    is are was were am be been being isnt arent wasnt werent aint
    has have had having got gets getting get
    will wont would could should can cant cannot must might may shall
    do does did doing done dont doesnt didnt
    hurts hurt hurting aches ache aching bangs bang banging throb throbs throbbing kills kill
    feels feel feeling looks look looking smells smell smelling sounds sound sounding seems seem
    needs need wants want keeps keep kept goes go going went comes come coming came broke broken
    breaks break stopped stops started starts works worked died dies dying
    in on out off up down at to for with from by about over under around through into onto
    and or but so because as than then
    not no never still too also just again now today tomorrow yesterday tonight anymore
    all both every any some
""".split())

# The words the topics name a thing by, kept by length so a slip is one scan of the words the
# right length. `topics` fills this at import: it reads this module, so the list cannot come the
# other way round, and the repair below needs it (see `_a_thing_a_letter_short`).
THING_WORDS_BY_LENGTH = {}
# The same vocabulary flat, for the question "does the reading already know this word".
THING_WORDS = set()


def learn_thing_words(words):
    """Keep the vocabulary the topics answer for, so a thing typed a letter short is read."""
    for word in words:
        if isinstance(word, str) and word.isalpha() and len(word) > 2:
            THING_WORDS.add(word)
            THING_WORDS_BY_LENGTH.setdefault(len(word), set()).add(word)

# Phrases that must be recognised before the words are looked at separately. Longest first.
PHRASES = sorted(
    {k: v for k, v in lexicon.CHAT.items() if " " in k or "/" in k or "&" in k}.items()
    | {k: v for k, v in lexicon.MISSPELLINGS.items() if " " in k}.items(),
    key=lambda item: -len(item[0]),
)

# Words a clause can start with that mean "new thought, same conversation".
BREAKS = frozenset(
    "anyway anyways btw actually instead otherwise also plus so but then oh ok okay right now "
    "still however meanwhile finally".split()
)
PRONOUN_BASES = frozenset(
    "i it that this there here he she we they who what where how when why everyone somebody "
    "someone nobody everybody one".split()
)
ASK_WORDS = frozenset(
    "what why how when where who which whose can could should would is are do does did will "
    "have has shall may might am was were".split()
)
WANT_WORDS = frozenset(
    "want need like looking help recommend suggest advice idea ideas tip tips know wonder "
    "thinking plan trying".split()
)
# An ask can hide in the middle of a run-on line: "my back hurts can i take ibuprofen",
# "im knackered all the time what could be wrong". These are the pieces that open one.
WH_WORDS = frozenset("what why when where who which whose".split())
AUX_WORDS = frozenset(
    "is are was were am do does did can could should would will shall have has may might".split()
)
# The be-forms: in front of a person they link a clause ("the thing is i do not know").
BE_WORDS = frozenset("is are was were am".split())
SUBJECT_WORDS = frozenset("i we you they he she".split())
HOW_DEGREE = frozenset(
    "long much many often old far big soon hot cold tall early late heavy deep".split()
)
# A clause opening with one of these is already being asked, not asking again.
NO_ASK_AFTER = frozenset("that if whether what why when where who which whose how".split())
# The only words that can come between a question word and its verb ("what time should i
# come", "how much does it cost", "which one should i buy"). Any other word there is a
# subject, and a question word in front of a subject is a relative clause: "the man who
# called was rude" and "the film which i saw" are statements, not questions.
ASK_NOUNS = frozenset("""time day date week month year kind sort type colour color size
amount number temperature age price reason way one ones much many long often far""".split())
# A reporting verb or a thought in front of the question word makes it what is being talked
# about, not what is being asked: "i know what to do", "she said why she left".
REPORTING = frozenset("""know knows knew known tell tells told say says said ask asks asked
wonder wondered wondering remember remembered forget forgot decide decided sure idea clue
mean means meant matter matters question doubt explain explains argue argued arguing
disagree disagreed discuss discussed debate debated talk talked mention mentioned
consider considered""".split())
# The same when a nominal and a copula come first ("that is what i meant", "the question is
# when to start"). The reporting verbs above already cover "we argued about who should pay".
COPULAS = frozenset("is are was were am be been being".split())
NOMINAL_BEFORE_COPULA = frozenset("""this that it there here all exactly precisely just
question thing problem point issue doubt reason answer part bit main only also still really
actually probably""".split())
# A determiner, then a noun, then "who/which/whose" is a relative clause that names the thing
# rather than asking: "a present for my mum who is in hospital", "the man who called was
# rude". These are the words that can open that nominal.
DETERMINERS = frozenset("""a an the my your his her our their its this that these those
some any no every each another anyone everyone someone nobody people ones""".split())
RELATIVE = frozenset("who which whose".split())
# "who should i see", "which do i pick": the relative word is followed by an auxiliary and a
# subject, so it is an inverted question about the thing named before it, not a clause about it.
RELATIVE_ASKS = frozenset("could can should would will shall do does did".split())


FREQUENT = frozenset((lexicon.CORE + " " + lexicon.COMMON).split()[:420])
AEIOU = frozenset("aeiou")
VOWELS = "aeiou"


def _double_variants(word):
    """Words one doubled-letter change away ("recomend" -> "recommend", "untill" -> "until")."""
    out = set()
    for i, char in enumerate(word):
        if char in VOWELS + "y":
            continue
        if i + 1 < len(word) and word[i + 1] == char:
            out.add(word[:i] + word[i + 1:])          # un-double: untill -> until
        else:
            out.add(word[:i] + char + word[i:])        # double: recomend -> recommend
    return out


def _a_doubled_letter_typed_once(word):
    """Words made by writing one of this word's letters twice: "wek" -> "week".

    The vowel is left out of `_double_variants` because most of the time it is the consonant
    that doubles ("recomend"), and a doubled vowel is rarer still - but "wek", "kep" and "cok"
    are the same slip, and a vowel is what the writer left one of.
    """
    out = set()
    for i, char in enumerate(word):
        if char.isalpha():
            out.add(word[:i] + char + word[i:])
    return out


def _three_of_a_letter(word):
    """Whether one letter runs three times together, which no English word does.

    The lexicon works a word's endings out, so a word that already ends in the letter an
    ending opens with comes back with three of them: "tell" + "ly" is "tellly", "full" + "ly"
    is "fullly". Nobody types those, so three together is the mark of a word the endings made
    rather than a word, and a spelling is never bent towards one.
    """
    return any(word[at] == word[at + 1] == word[at + 2] for at in range(len(word) - 2))


def _doubled_letter_words(word):
    """The words a doubled letter would make of this one, and that the lexicon knows.

    Only for a word the lexicon does not have: an ending of a word is a word of its own
    ("planed" is not "planned"), and the lexicon's "mattres" is a plural rule run backwards
    off "mattress", so a candidate that is a word only because a word ending in -ss lost an s
    is not a word at all. That guard is what stops "matres" being read as "mattres".
    """
    if word in LEXICON:
        return []
    return [w for w in _a_doubled_letter_typed_once(word)
            if (w in BASE or (w in LEXICON and w + "s" not in BASE))
            and not _three_of_a_letter(w)]


def _ie_variants(word):
    """Words one ie/ei swap away ("recieve" -> "receive")."""
    out = set()
    for pair, other in (("ie", "ei"), ("ei", "ie")):
        start = word.find(pair)
        while start != -1:
            out.add(word[:start] + other + word[start + 2:])
            start = word.find(pair, start + 1)
    return out


# An s in front of one of these is how English words do begin ("street", "sprint", "shrug"),
# so a run of consonants that opens with one of these pairs is a shape of its own and nothing
# is missing from it.
S_CLUSTERS = "tpskmlnwhqc"


def _missing_vowel(word):
    """The words a vowel left out of the middle of a long word would make: "daughtr" ->
    "daughter", "brthday" -> "birthday", "bicycl" -> "bicycle".

    A vowel is the letter people leave out of the middle of a word they are typing fast, and
    none of the repairs the reader already has can put one back. The new vowel has to sit in a
    cluster of three or more consonants ("daughtr" has "ghtr", "brthday" has "brth"), because
    that is the shape English does not have and the vowel is the sound that is missing from it.
    Two consonants are every sound a word needs ("martin", "statin", "toast") and a cluster
    that opens with an s is English of its own ("street", "sprint"), so a vowel is never put
    there; that is what keeps a name a name and a drug a drug.

    Only a word of five letters or more is tried, and only one the lexicon does not know, so a
    real word is never touched: below five there is no room left for a misspelt word to be told
    from a real one ("thnks" is "thanks"; "thnk" is a keystroke and a word). The caller keeps
    the repair only when exactly one word of the lexicon fits.
    """
    if len(word) < 5 or word in LEXICON:
        return ()
    out = set()
    for i in range(1, len(word) + 1):
        start = i
        while start > 0 and word[start - 1] not in VOWELS:
            start -= 1
        end = i
        while end < len(word) and word[end] not in VOWELS:
            end += 1
        cluster = word[start:end]
        if len(cluster) < 3 or (cluster[0] == "s" and cluster[1] in S_CLUSTERS):
            continue
        for vowel in VOWELS:
            candidate = word[:i] + vowel + word[i:]
            if candidate in BASE:
                out.add(candidate)
    return out


def _extra_vowel(word):
    """The words a vowel typed next to another vowel would make: "radiatior" -> "radiator".

    People adding a vowel where two already meet ("ie", "ei", "io", "ue") is the one extra
    letter worth undoing: "radiatior", "cookeing". Only a long word is tried, because the
    short ones this would bend are words in their own right ("seing" is one letter from "sing",
    "seizing" from "sizing"), the last letter is never taken, because it is what makes
    "breathe" a verb and "breath" a noun, and only an e or an i is removed, which is what
    people insert. The caller keeps only the candidates the lexicon knows, and only when
    exactly one fits.
    """
    if len(word) < 8:
        return ()
    out = set()
    for i, char in enumerate(word):
        if char not in "ei" or i + 1 == len(word):
            continue
        before = word[i - 1] if i else ""
        after = word[i + 1]
        if before in VOWELS or after in VOWELS:
            out.add(word[:i] + word[i + 1:])
    return out


_A_WORDS = frozenset("cola tuna mocha salsa karma pasta data area idea".split())


def _a_said_for_an_ending(word):
    """The words an -er, -or, -ar or -ow said as a would make: "propa" -> "proper", "winda" -> "window".

    A last syllable nobody stresses comes out as an a when people write the way they talk
    ("propa", "showa", "brotha", "plumba", "docta", "simila", "winda", "narra"), and none of
    those is a word, so the lexicon can say what was meant: "my winda wont shut" was read as a
    line about nothing while the word spelled right gets the window answer. Only a word of four
    letters or more that ends in an a after a consonant is tried, so a real word ending in an a
    ("sofa", "pizza", "idea") never reaches the guess - it is in the lexicon and fix_typo stops
    there - and the few real words that are not are held below.
    """
    if word in _A_WORDS:
        # A real word that happens to end in an a: "cola" is a drink, not a colour.
        return ()
    if word.endswith("as") and len(word) >= 5:
        # "the windas wont shut" is the same guess with the plural still on it.
        stem, plural = word[:-2], "s"
    elif word.endswith("a") and len(word) >= 4:
        stem, plural = word[:-1], ""
    else:
        return ()
    if stem[-1:] in VOWELS:
        return ()
    return tuple(stem + ending + plural for ending in ("er", "or", "ar", "ow"))


def _dropped_letter(word):
    """The words a missing w would make: "kno" -> "know", "thro" -> "throw", "shado" -> "shadow".

    Only a w is put back. It is the letter people leave out of a word and never hear missing
    ("know", "throw", "shadow", "answer"), so the repair cannot turn a real word into another
    one the way a general dropped letter can; the caller keeps only the candidates the lexicon
    knows, which is what makes "kno" safe.

    A word with a w already in it keeps one: "the windo wont shut" was read as a word the reader
    did not know, so the window that will not shut was answered "Right. What have you tried so
    far?" instead of the card. The w people leave off the end is the same w wherever the other
    one sits, and the candidate still has to be a word of the lexicon, so the guard is on the
    letter the repair would add rather than on the word ("window", "willow").
    """
    if len(word) < 3 or word.endswith("w"):
        return ()
    return (word + "w",)


def _an_ing_said_as_n(word):
    """The -ing form typed with the i and the g both gone: "gettn" -> "getting".

    A word ending in three letters that are all consonants and the last of them an n is an -ing
    with nothing left of the ending but the n: "forgettn", "gettn", "sittn", "chattn". The shape
    is what makes it safe - no English word ends that way, because a syllable needs a vowel - so
    a word that has one in its last three letters ("basin", "satin", "salmon") is left alone
    even when it is not in the lexicon, and one the lexicon holds is never reached at all.

    The verb under it may double its last letter ("get" -> "getting", "sit" -> "sitting"), so
    both spellings are tried and the caller keeps the one the lexicon knows.
    """
    if (len(word) < 5 or not word.endswith("n") or word in LEXICON
            or word in lexicon.COMMON_NAMES):
        return None
    if any(char in VOWELS for char in word[-3:-1]):
        return None
    stem = word[:-1]
    forms = [stem + "ing"]
    if len(stem) > 1 and stem[-1] == stem[-2]:
        forms.append(stem[:-1] + stem[-1] + "ing")
    known = {form for form in forms if form in LEXICON}
    if len(known) == 1:
        return known.pop()
    return None


def _a_leading_h(word):
    """The word an h put back on the front would make: "eadache" -> "headache", "eart" -> "heart".

    An h at the front of a word is the letter people say and never hear, so it is the one that
    goes missing when somebody types the way they talk: "iv got a bad eadache", "my eart is
    racing", "the ouse is freezing", "i need an ospital". Only the front is tried, only a word
    that opens on a vowel, and the caller keeps only candidates the lexicon knows - which is what
    makes it safe: "eadache" is one letter from "earache" as well, and that repair reached the
    earache card, so the h is the shorter path to the word the line is about. A word the lexicon
    holds never arrives here ("edge", "and", "am" are words), and a word of three letters is
    left alone because "ed" and "ed" are not a slip of anything the bot should answer with.
    """
    if len(word) < 4 or word[:1] not in "aeiou":
        return ()
    if word.endswith("s") and word[:-1] in BASE:
        # A plural is a word of the deck's own: "18 year olds" is not "18 year holds", and it
        # is the one line of the whole deck this repair would otherwise reach.
        return ()
    return ("h" + word,)


# The few real words that keep the e before -ing: dyeing a dress is not dying, and singeing
# hair is not singing. Each one sits exactly where the repair below would put it, so they are
# named rather than left to the candidate count.
E_KEPT_WORDS = frozenset({"dyeing", "singeing", "tingeing", "swingeing"})


def _e_kept_before_ing(word):
    """The word an e kept before -ing would make: "moveing" -> "moving", "takeing" -> "taking".

    A verb that ends in an e drops it before the ending, and a fast typist writes it anyway.
    Only this ending is tried, because it is the one where the letter before the e decides
    whether the e stays ("seeing", "freeing", "canoeing" all keep it) and that is a rule the
    reader cannot hear - so the candidate has to be a word the lexicon knows and it has to be
    the only one. The four real words that do keep the e are named above.
    """
    if len(word) < 6 or not word.endswith("eing") or word in E_KEPT_WORDS:
        return ()
    shorter = word[:-4] + "ing"
    return (shorter,) if shorter in LEXICON else ()


def _swapped_pair(word):
    """The words swapping two letters typed the wrong way round would make, or ().

    "collasped" is "collapsed" with the p and the s the wrong way round, and that is how a word
    comes out when two keys are hit in the wrong order. Only a long word is tried, and the caller
    keeps the candidates the vocabulary knows and only one of them: "trail"/"trial" and
    "form"/"from" are both real words, so they never reach here, and a word with two fittings is
    left alone. Five letters is the floor, the same as the vowel reader's: "hpone" is "phone",
    and a word the bot's own answers write is not a slip at all.
    """
    if len(word) < 5 or _a_word_the_bot_writes(word):
        return ()
    out = set()
    for at in range(len(word) - 1):
        pair = word[at:at + 2]
        # Two consonants typed the wrong way round ("collasped"): a vowel in the pair is how a
        # real word becomes a different real word ("overdoes" is not "overdose", "form" is not
        # "from"), and those stay with the curated tables.
        if len(pair) < 2 or pair[0] == pair[1]:
            continue
        if pair[0] in VOWELS or pair[1] in VOWELS:
            continue
        out.add(word[:at] + word[at + 1] + word[at] + word[at + 2:])
    return out


def _two_letters_the_wrong_way_round(word):
    """The words swapping two letters typed the wrong way round would make, vowels included:
    "brithday" -> "birthday", "cra" -> "car", "aeg" -> "age", "paekd" is not one.

    This is the same slip `_swapped_pair` reads, without its two limits: that one wants a long
    word and two consonants, because in a real word a vowel pair is how one word becomes
    another ("form" is not "from", "trail" is not "trial"). Neither limit is needed when the
    typed word is not a word at all, which is what this is for: a person typing fast puts two
    keys down in the wrong order, and half the time one of them is a vowel ("brithday",
    "taht", "hte", "aeg"). Everything the lexicon holds is left alone, and the caller keeps the
    repair only when exactly one word fits, so a slip with two readings ("cra" is one swap from
    "car" and from "arc") is left as it was typed.
    """
    if len(word) < 5 or word in LEXICON or _a_word_the_bot_writes(word):
        return ()
    out = set()
    for at in range(len(word) - 1):
        pair = word[at:at + 2]
        if pair[0] == pair[1]:
            continue
        # A pair with two consonants is `_swapped_pair`'s job ("collasped"), and a pair with two
        # vowels is a slip the curated map has ("recieve"). One vowel and one consonant is the
        # shape left over: "brithday" for "birthday", "caesr" for "caesar", "cehst" for "chest".
        if (pair[0] in VOWELS) == (pair[1] in VOWELS):
            continue
        made = word[:at] + pair[1] + pair[0] + word[at + 2:]
        if made not in NO_SWAP_TO:
            out.add(made)
    return out

# Words a swapped pair may not be repaired to. "hagned" is one swap from "hanged" and from
# nothing else the bot reads, and a person who writes it almost always means "hung": the repair
# would not fix the line, it would put a confident wrong word in the bot's mouth ("hagned my
# washing out" became "hanged my washing out"), which is worse than the slip it started with.
NO_SWAP_TO = frozenset(("hanged",))


_A_WORD_THE_BOT_WRITES = None


def _words_the_bot_writes():
    """Every word the knowledge base's own keys and answers use, worked out once.

    The guard on a swapped pair is "only read a word the reader does not know as a word", and
    LEXICON cannot answer that on its own: it is the base words and the forms made from them, not
    a dictionary, so "stain", "order", "paper", "spilt" and "matters" are not in it and each is
    one swap from a word it does hold ("satin", "roder", "apper", "split", "mattres"). Read that
    way, the reader bent 138 of the deck's own lines.

    The knowledge base cannot make that mistake: its keys and answers are written by the bot, so
    every word in them is well spelled by construction - the same reasoning `tools/typo_scan.py`
    gives for scanning them. Asking it is a lazy import because the answer modules import it
    anyway, and the result is held: one build a process, about a second, and nothing after that.
    """
    global _A_WORD_THE_BOT_WRITES
    if _A_WORD_THE_BOT_WRITES is None:
        words = set()
        try:
            from bot.knowledge import entries as knowledge_entries
            from bot.knowledge import lookup as knowledge_lookup
            for entry in knowledge_entries():
                for field in ("reply", "ask", "key", "id", "domain"):
                    value = getattr(entry, field, "")
                    for text in (value if isinstance(value, (list, tuple, set)) else [value]):
                        if isinstance(text, str):
                            words.update(knowledge_lookup.tokens(text))
            _, _, known = knowledge_lookup._vocabulary(knowledge_entries())
            words.update(word for word in known if isinstance(word, str))
        except Exception:                     # the reading must stand up on its own
            pass
        _A_WORD_THE_BOT_WRITES = frozenset(
            word.lower() for word in words if word.isalpha())
    return _A_WORD_THE_BOT_WRITES


def _a_word_the_bot_writes(word):
    """Whether the knowledge base writes this word as it stands, so it is not a slip."""
    if word in lexicon.TYPED_WORDS or word in lexicon.COMMON_NAMES:
        return True
    return word in _words_the_bot_writes()


def _bones(word):
    """The consonants of a word, in order: "collapsed" and "collpsd" are both "cllpsd"."""
    return "".join(char for char in word if char not in VOWELS)


def _longest_consonant_run(word):
    """The longest stretch of letters in a word with no vowel in it.

    A vowel typed past closes a gap and leaves a run behind - "collpsd" has "psd", "bleedng"
    has "dng" - and an ordinary word hardly ever has three consonants in a row. That is what
    tells a typo from a word: "balding" and "sizing" are only two ("ld", "ng"), and they are
    words, so they must not be read as "bleeding" and "seizing" (the same bones).
    """
    run = best = 0
    for char in word:
        if char in VOWELS or char == "y":
            run = 0
        else:
            run += 1
            if run > best:
                best = run
    return best


URGENT_BONES = {}


def _an_emergency_word_left_out(word):
    """The emergency word this is with its vowels typed past, or None.

    A frightened person types fast, and the vowels are what goes: "my mum collpsd". A letter
    left out is the one typo the engine does not otherwise guess at, because a word one letter
    short of another is usually the other word - but here the only words consulted are the
    emergency vocabulary itself (lexicon.URGENT_MISSPELLINGS' values), and only when exactly
    one of them has the same consonants in the same order. "cllpsd" is "collapsed" and nothing
    else; a word whose bones fit two of them is left for the curated table.

    The word also has to look like a vowel was left out: three consonants in a row. Without
    that guard the same bones bend ordinary words into emergencies - "balding" is "bleeding"
    and "sizing" is "seizing" - and a person talking about their hair got the bleeding card.
    """
    if len(word) < 6 or word in LEXICON or _longest_consonant_run(word) < 3:
        return None
    if not URGENT_BONES:
        for known in URGENT_WORDS:
            URGENT_BONES.setdefault(_bones(known), []).append(known)
    found = [known for known in URGENT_BONES.get(_bones(word), ()) if len(known) > len(word)]
    return found[0] if len(found) == 1 else None


# The words a name comes after: "my brother is called crispin". A word there is a name, and a
# name is not a slip. A bare "call" is not one of them, because "call mi later" is a pronoun
# with the letters left out, not somebody's name.
NAME_FRAMES = frozenset("called named".split())

# The chat-speak word that is also a name. "kay" is typed for "ok" ("kay thanks") and it is
# also a name, and where a name goes the name is the reading that matters. Read as "ok", every
# line that gave a name came back wrong: "call me ok", "i go by ok", "my names ok", and "im not
# kay" - a person saying which name is not theirs - earned "Sorry to hear that. A walk and
# someone to talk to usually help more than sitting with it", the answer to feeling low.
CHAT_NAMES = frozenset(word for word in lexicon.CHAT if word in lexicon.COMMON_NAMES)
# The words a name follows when the line is about what somebody is called: the verbs that
# introduce one, the pronouns that carry it for a person who has just said it ("what shall i
# call you" - "call me kay"), and "i am", which is how a name is given.
NAME_ROLL = frozenset("""names name named go goes going by im am i'm""".split())
# The verbs a name is given after: "call me kay", "call u kay". Only these take the pronoun that
# carries a name, because "text me kay" is "text me, ok?" - the tag at the end of an ask, not a
# name - and the ask that the bot cannot send a text is the answer the line wants.
NAME_CALLS = frozenset("""call calls called calling callin name names named""".split())


def _a_name_slot(before, before_before, word):
    """True when this word stands where a name goes, so a spelling repair may not touch it.

    The lexicon makes an "-ing" out of every word it holds, so "crispin" is one letter from
    "crisping" and "justin" from "justing": the left-off-g repair read both as verbs, and the
    line came back as "Noted: your brother is called crisping" and "Your cousin justing is
    coming - noted". The store had the name right both times (`others` holds "crispin" and
    "justin"); it is the echo of the repaired line that was wrong.

    Two frames are named, and nothing else: the word after "called"/"named"/"name is", where any
    name may stand, and a known name right beside the person it belongs to ("my cousin justin").
    Only a known name is held back in the second frame, because a verb sits there too: "how do i
    stop me baby wakin up at night" and "my sister sed she would come" are both the repair
    working, and the repair stands.
    """
    if not word.isalpha() or len(word) < 2 or word in LEXICON:
        return False
    if before in NAME_FRAMES:
        return True
    if before in BE_WORDS and before_before == "name":
        return True
    if word in CHAT_NAMES and (before in NAME_ROLL
                               or (before in ("me", "you", "u") and before_before in NAME_CALLS)
                               or (before == "not"
                                   and before_before in BE_WORDS | {"im", "i"})):
        # "call me kay", "i go by kay", "my names kay", "im not kay": the s on "names" and the
        # "not" after "im" are left where they are and the next word is a name, so the chat table
        # may not read it as "ok".
        return True
    return (word in lexicon.COMMON_NAMES
            and before in KIN and before_before in POSSESSIVES)


def _dropped_g(word):
    """The -g people leave off a typed word: "doin" -> "doing", "mornin" -> "morning".

    Only when the word is not one the lexicon knows and the form with the g is, so a real
    word is never changed. The lexicon is missing ordinary -in words ("satin", "raisin"), so
    those are named in lexicon.REAL_IN: "a satin dress" must not read as "a sating dress".
    """
    if (len(word) < 4 or not word.endswith("in") or word in LEXICON
            or word in lexicon.REAL_IN or word in lexicon.COMMON_NAMES):
        return None
    longer = word + "g"
    if longer in LEXICON:
        return longer
    # "movein" is "moving": the g is not the only letter missing, because the e goes as well.
    stem = word[:-2]
    if _drops_a_final_e(stem) and len(stem) > 2:
        dropped = _ing_form(stem)
        if dropped in LEXICON:
            return dropped
    # A verb that doubles its last letter, written with one or with two: "getin" and "gettin"
    # are both "getting". The doubled spelling has to be proved a word, so the lexicon has to
    # carry it - which is what _inflections writes for a word of one beat. The verb under it
    # has to be a word too: "stalin" is one letter from a doubled -ing and "stal" is nothing,
    # so the name stays a name ("who was stalin" read as "who was stalling" and lost its
    # answer once the words a line is read by carried the repair).
    stem = word[:-2]
    if len(stem) > 3 and stem[-1] == stem[-2]:
        stem = stem[:-1]
    if _doubles_its_last_letter(stem) and (stem in BASE or stem in LEXICON):
        doubled = stem + stem[-1] + "ing"
        if doubled in LEXICON:
            return doubled
    return None


# The ones the quantifier is built on: "anyfing", "sumfing", "evryfing", "nuffing". The
# whole class is these four words and the spellings of their first half, so the repair is a
# closed list of stems rather than a guess at what a stopped th might have been. Nothing else
# in English ends in "fing" except words the lexicon already holds ("stuffing", "proofing").
STOPPED_TH_STEMS = {
    "any": "anything", "eny": "anything", "ani": "anything",
    "some": "something", "sum": "something", "som": "something", "sumn": "something",
    "every": "everything", "evry": "everything", "evrey": "everything",
    "nuf": "nothing", "nuff": "nothing", "nof": "nothing", "noff": "nothing",
    "nut": "nothing", "nuth": "nothing", "not": "nothing", "no": "nothing",
}


def _stopped_th(word):
    """The -thing word a stopped th is said as: "anyfing" -> "anything", "nuffing" -> "nothing".

    Th-stopping ("thing" said as "fing") is regular in several of the accents people type in,
    so it is a spelling a reader has to expect: "anyfing i can do at lunch" was read as nothing
    in particular and answered with the stock line about a hard day. Only a word the lexicon
    does not hold is touched, and only the four -thing words are reachable, so a line about
    "stuffing" or "waterproofing" is left alone.

    The same accents drop the g and the th: "nuffin", "anyfink" and "sumfin" are the same word
    typed three ways, and people write all three, so the ending is not just "fing". The stem
    still has to be one of the handful people write, which is what keeps "muffin", "puffins",
    "griffins" and "thinking" out: no real word is built from one of these stems.
    """
    if len(word) < 5 or word in LEXICON:
        return None
    for suffix in ("fings", "fing", "finks", "fink", "fins", "fin"):
        if word.endswith(suffix):
            stem = word[:-len(suffix)]
            break
    else:
        return None
    plural = suffix.endswith("s")
    found = STOPPED_TH_STEMS.get(stem)
    return found + "s" if found and plural else found


# The common words with the /shun/ sound that are not spelt -tion, so "fashun" is a fashion
# and not a fation. Anything outside this list is a -tion word, which is the overwhelming
# majority of the sound in English. The -ssion, -sion and -cian words are here because the
# repair has to tell them apart from the -tion ones: "mishun" is a mission and not a mition.
SHION_WORDS = frozenset("""
cushion fashion passion mission session version decision occasion discussion permission
television conclusion explosion confusion illusion vision revision division provision
suggestion tension expression compassion impression profession possession aggression
admission commission expansion extension pension mansion excursion invasion collision
emission transmission procession succession confession depression digression obsession
recession concession progression exclusion inclusion seclusion precision derision
magician musician electrician politician technician physician statistician optician
beautician mathematician paediatrician dietician clinician""".split())


def _shun_variant(word):
    """The -tion people spell the way it sounds: "infecshun" -> "infection".

    English spells the /shun/ sound at the end of a word -tion, so a typed word ending in
    "shun" (or "kshun", with the k of "infection" spelled out too) is that word, and no
    ordinary word ends that way except "shun" itself. Nothing here needs the lexicon: the whole point is a word the
    lexicon does not have ("infection" is not one of its words either).
    """
    if word in LEXICON:
        return None
    # "any suggeshuns?" is the one word with an s on the end, where the s of the plural is the
    # only letter after the sound, so the singular is repaired and the s put back.
    if word.endswith("shuns") and len(word) > 7:
        singular = _shun_variant(word[:-1])
        if singular:
            return singular + "s"
        return None
    if word.endswith("kshun"):
        # "infeckshun" spells the /k/ of "infection" with a k as well: the "ks" is the c
        stem = word[:-5]
    elif word.endswith("shun"):
        stem = word[:-4]
    else:
        return None
    if len(stem) < 2 or not stem.isalpha():
        return None
    # "Cushion", "fashion" and "decision" end in the same sound and are not -tion words, so
    # the other spellings of the sound are tried first: "cushun" is a cushion, not a cution.
    # The s of "shun" is where the sound starts, so it can belong to the word as well
    # ("suggeshun" is suggest + ion), which is why the stem is tried both with and without it.
    kept = stem + "s"
    for spelled in (stem + "shion", stem + "ssion", stem + "sion", stem + "tion",
                    kept + "tion", kept + "ssion", kept + "sion", stem + "cian"):
        if spelled in LEXICON or spelled in SHION_WORDS:
            return spelled
    return stem + "tion"


# The th sound typed as an f in a word too short for the rule below: the little words, which
# carry a line whatever else is in it. Each f spelling here is not a word of its own, so reading
# one cannot take a word away from the person.
F_TYPED_FOR_TH = {
    "fe": "the", "fis": "this", "fey": "they", "fem": "them", "fere": "there",
    "fing": "thing", "fings": "things", "fird": "third",
    "fousand": "thousand", "fousands": "thousands",
    "freat": "threat", "freaten": "threaten", "freatens": "threatens",
    "freatened": "threatened", "freatening": "threatening",
}


def _said_with_an_f(word):
    """The "th" sound typed as an "f": "fanks" -> "thanks", "froat" -> "throat".

    A swapped sound is not a slip a one-letter repair can find - "fanks" is two letters from
    "thanks" - and it is common enough that "fanks", "fink" and "froat" arrive as whole
    lines. Only the front of the word is read this way, because that is where the sound is
    swapped, and only for a word that is not a word itself whose "th" spelling the reading
    already knows: "fan", "fat", "fro" and "fort" are real words and stay as they are, and
    "sumfink" is left to the spelling tables.
    """
    # The named spellings come first: "foughts" is not a word, but the lexicon builds it from
    # "fought" and a plural, and "thousand" and "threaten" are not in it at all.
    if word in F_TYPED_FOR_TH:
        return F_TYPED_FOR_TH[word]
    if not word.isalpha() or not word.startswith("f") or word in LEXICON:
        return None
    if len(word) < 4:
        return None
    spelled = "th" + word[1:]
    # The chat spellings count as known words here too, because the fold that reads them runs on
    # the line after this: "fey" is "they" and "feyre" is "they are" by the same table that
    # reads "feyve" as "they have".
    if spelled in LEXICON or spelled in lexicon.CHAT or spelled in lexicon.EXPAND:
        return spelled
    # The sound is swapped in a word with an ending on it too, and the ending is what the
    # lexicon holds the word without: "freatens" is "threatens", "freatened" is "threatened",
    # and a safety line that reads neither is a line about something else.
    for ending in ("s", "es", "d", "ed", "ing"):
        stem = spelled[:-len(ending)]
        if spelled.endswith(ending) and len(stem) >= 5 and stem in LEXICON:
            return spelled
    # The same sound with the g left off the end, which the reading already repairs elsewhere:
    # "finkin" -> "thinkin" -> "thinking". One retry, only for the "-in" ending, so every f
    # verb gets its -ing form without a list.
    if spelled.endswith("in") and spelled + "g" in LEXICON:
        return spelled + "g"
    return None


# A word for a person or a thing, typed as the little word that sounds like it. "wif" is
# "with" in "going wif my mum", but in the place a person's name goes it is the wife: "my wif
# is due in july" was said back as "your with is due in july". Read where the line is read, not
# here - the chat table below owns "wif" and "wiff" for every other place.
A_THING_TYPED_AS_A_LITTLE_WORD = {
    "wif": "wife",
    "wiff": "wife",
}
# The words that fill the place a person or a thing goes. "a" is not one of them: "a wiff of
# smoke" is the wh word, and a thing of the person's is always "my", "our", "the" or a name.
A_THING_GOES_AFTER = frozenset("the".split())


def _said_with_an_f_anywhere(word):
    """The same swapped sound away from the front: "wif" -> "with", "teef" -> "teeth".

    The sound is swapped in the middle and at the end of a word too, and there it costs a line
    its answer rather than only its spelling: "my teef hurt" was asked "Does it come and go, or
    is it there all the time?" while "my teeth hurt" reaches the dentist, "mouf ulcers" reached
    nothing at all, "how do i clean a baff" was a shrug, and a line said back to the person
    repeated "your birfday is the 3rd of may". Only the f is touched, so the rest of the word
    must already be the word it is meant to be: the "th" spelling has to be one the engine
    knows, and the typed word must not be a word it knows ("if", "off", "half", "loaf" and
    "shelf" stay as they are). Only an f nobody could mean as an f is read, which is why this
    runs after `fix_typo` and the letters before it.
    """
    if len(word) < 3 or not word.isalpha() or "f" not in word or word in LEXICON:
        return None
    # A doubled f is only read at the end of the word, where the whole sound is the f: "baff",
    # "mouff". Inside a word the two letters are two sounds ("offers", "coffee"), and reading
    # them as one turned "offers" into "others". A w in front of it is left alone, because
    # "wiff" and "woff" are how people spell a word that begins with "wh" ("a wiff of smoke").
    if word.endswith("ff"):
        if word.startswith("w"):
            return None
        spelled = word[:-2] + "th"
        return spelled if spelled in LEXICON else None
    for at, letter in enumerate(word):
        if letter != "f":
            continue
        spelled = word[:at] + "th" + word[at + 1:]
        if spelled in LEXICON:
            return spelled
    return None


def _a_thing_where_a_thing_goes(word, before):
    """The person or thing a little word stands for in the place one goes, or None.

    "my wif" and "the wif" are the wife typed without the last letter. This has to be asked
    before the chat table, which answers `wif` with "with" wherever it appears.
    """
    if before not in POSSESSIVES and before not in A_THING_GOES_AFTER:
        return None
    thing = A_THING_TYPED_AS_A_LITTLE_WORD.get(word)
    return thing if thing in LEXICON else None


def _missing_e(word):
    """The "-ed" people type as "-d": "askd" -> "asked", "wantd" -> "wanted", "movd" -> "moved".

    A bare d is how no English word ends after a k, t, v, p, s, m, f or g, so the letter before
    it is the sign the e was dropped; after a vowel, a l, an n or an r it is how plenty of words
    end ("road", "old", "mend", "bird"), and there the repair could only bend a real word, so
    those are left to the curated MISSPELLINGS map. The form with the e also has to be one the
    lexicon knows, which is what keeps "tird" from becoming anything but "tired".
    """
    if len(word) < 4 or not word.endswith("d") or word in LEXICON:
        return None
    if word.endswith("yd"):
        # A word ending in a consonant and y takes "-ied": "worryd" -> "worried", never
        # "worryed". After a vowel the y is part of the sound ("playd"), so it is left alone.
        if word[-3] in VOWELS or word[-3] == "y":
            return None
        longer = word[:-2] + "ied"
        return longer if longer in LEXICON else None
    if word[-2] not in MISSING_E_AFTER:
        return None
    longer = word[:-1] + "ed"
    return longer if longer in LEXICON else None


def _short_double(word):
    """A short word typed with a doubled letter: "hii" -> "hi", "okk" -> "ok", "byee" -> "bye".

    Words under four letters used to be left alone, and they are where most of the one-word
    replies live. Only an un-doubled form that is a frequent word is taken, and only for a
    word the lexicon does not know, so "all" and "off" are never touched.
    """
    if len(word) < 3 or word in LEXICON:
        return None
    variants = _double_variants(word)
    if word[-1] == word[-2]:
        variants.add(word[:-1])              # a vowel too: "hii" -> "hi", "noo" -> "no"
    keep = [variant for variant in variants
            if variant in LEXICON and variant in FREQUENT]
    keep.sort(key=lambda variant: COMMON_RANK.get(variant, 10 ** 6))
    return keep[0] if keep else None




def _one_letter_apart(word, other):
    """True when `word` is `other` with one letter added, left out, swapped round or replaced
    by another vowel: the shapes people type at speed ("knackerd", "exausted", "nerveus")."""
    if abs(len(word) - len(other)) > 1:
        return False
    if len(word) == len(other):
        differ = [i for i in range(len(word)) if word[i] != other[i]]
        if len(differ) == 1:
            i = differ[0]
            return word[i] in VOWEL_SET_OR_Y and other[i] in VOWEL_SET_OR_Y
        if len(differ) == 2:
            i, j = differ
            return j == i + 1 and word[i] == other[j] and word[j] == other[i]
        return False
    short, long = (word, other) if len(word) < len(other) else (other, word)
    i = 0
    while i < len(short) and short[i] == long[i]:
        i += 1
    if i == len(short):
        # A letter on the end of a whole word is how a word grows, not how a typo looks:
        # "scare" + "d" is "scared" and "guilt" + "y" is "guilty", so "dont scare me" and
        # "guilt tripping me" would become feelings they are not. Only a letter inside counts.
        return False
    if short[i:] != long[i + 1:]:
        return False
    if word is long:
        # A letter typed into a word only makes it a stretch when it is a vowel: people hold a
        # vowel, and they drop or swap letters, but a consonant typed into a feeling word is
        # usually another word altogether - "gland" is not "glad", "strain" is not "train".
        return long[i] in VOWEL_SET
    return True


# The everyday verbs a line puts straight after its subject, as people say them. A closed list,
# so a letter out of place in one of them has one reading, and nothing else in the language is
# one edit from it.
CORE_VERBS = frozenset("""take get give make have go do say see know think want need feel look
    come wake walk work eat drink buy pay keep leave sleep live start stop try help tell ask
    call find bring wear watch read cook clean wash sit stand run drive ride""".split())
# The particles a verb of a line takes straight after it ("wake up", "get off", "give in"): where
# one stands, the word before it is the verb, and a vowel out of place in that word is read.
AFTER_A_VERB = frozenset("up off out in on back over down away".split())
# Where the verb of a line stands: right after its subject ("i tke the bus to work", "we gte
# home at 6", "they wke up early"). A subject is what says the word after it is the verb and not
# a name or a thing. "to" and "and" were tried as places as well and were taken back out: they
# put a repaired verb into a line that read fine without it, and "i wake up and mak coffee" moved
# off the coffee card and onto the buffet one.
BEFORE_A_VERB = frozenset("i we they you he she".split())


def _one_letter_wrong(word, other):
    """True when one letter added, left out, swapped with its neighbour or typed for another
    makes `other` out of `word`.

    `_one_letter_apart` says the same thing for feelings and parts, with two limits that are
    right there and wrong here: a letter typed *into* a word only counts when it is a vowel,
    and a letter typed *for* another only when both are vowels. Those limits keep "gland" from
    being "glad"; next to a closed list of the commonest verbs there is nothing to confuse it
    with, so any letter counts.
    """
    if abs(len(word) - len(other)) > 1:
        return False
    if len(word) == len(other):
        differ = [i for i in range(len(word)) if word[i] != other[i]]
        if len(differ) == 1:
            return True
        if len(differ) == 2:
            i, j = differ
            return j == i + 1 and word[i] == other[j] and word[j] == other[i]
        return False
    short, long = (word, other) if len(word) < len(other) else (other, word)
    i = 0
    while i < len(short) and short[i] == long[i]:
        i += 1
    return short[i:] == long[i + 1:]


def _a_word_the_reading_knows(word):
    """Whether the topics' vocabulary or the lexicon already holds this word or a form of it.

    "seeding" is not in the lexicon as it stands, and the bot does not write it, so a repair
    read it as "seedling" - a word bent into a different word, in a line about a lawn. The
    word, its stem and its everyday endings are asked, because the lexicon holds base words
    and the topics hold the names of things ("seed" is a seed, "seeds" and "seeded" are forms
    of it).
    """
    if _known_word(word):
        return True
    return any(_known_word(stem) for stem in _stems_of(word))


def _known_word(word):
    """Whether one word is held by the lexicon or by the topics' vocabulary."""
    return word in LEXICON or word in THING_WORDS


def _stems_of(word):
    """The words `word` could be an everyday ending of."""
    stems = set()
    if word.endswith("ing") and len(word) > 5:
        stems.update((word[:-3], word[:-3] + "e"))
    if word.endswith("ed") and len(word) > 4:
        stems.update((word[:-2], word[:-1]))
    if word.endswith("es") and len(word) > 5:
        stems.add(word[:-2])
    if word.endswith("s") and len(word) > 4:
        stems.add(word[:-1])
    return stems


def _a_thing_a_letter_short(word):
    """The thing `word` is one letter short of, or None when none or two fit.

    The same reading as `_a_core_verb_typed_wrong`, with the topics' own vocabulary as the
    closed list: a letter left out of a thing's name is the commonest slip in a line about a
    thing ("my fidge is broken", "my frige is making a noise", "how do i check my raiator"),
    and next to a list of things there is little to confuse it with. Eight household and garden
    words typed a letter short reached no card on main: "my fidge is broken" got "That would
    bother me too. Tell me what it does", "how do i clean my frige" and "how do i clean my
    caret" got the search shrug, "my biler is broken" got "Right. What have you tried so far?",
    "how do i check my raiator" and "how often should i water my grss" got "I don't know enough
    to answer that honestly", and "my feezer is frosting up" got "I'm listening — say more if it
    helps."

    The caller has already refused a real word and a name, so what is left is a word nothing
    knows. Two things one letter away still say nothing ("roter" is a router and a roster),
    which is the tie rule everywhere else.

    The letter put back is one left out of the middle, never one on either end: a letter on the
    end of a whole word is how a word grows, not how a typo looks. "repeat that step by step"
    was read as "steps" and the follow-up that repeats the last answer fell to the search
    shrug, and "wols" was read as "wools" - both a word of its own bent into a longer one.
    "step" is not in the lexicon as it stands, so the guard against a real word did not catch
    it; keeping the first and last letter does, and none of the repairs above loses one.

    A word the reading knows somewhere else is not a word missing a letter. The lexicon is a
    curated subset and not a dictionary, so the guard against a real word let 63 of the deck's
    own 9,580 words through as "slips": "on fire" became "on fibre" and lost the 999 answer,
    "we have mice" became a bolognese, "my bother", "the plans", "it moves" and "the tables"
    were bent as well. Every one of them is a word the bot writes in its own answers, or a form
    of one the topics name ("seeding" is a seed), so the reading asks both before it bends
    anything - the same guard `_a_core_verb_typed_wrong` has always had.
    """
    if len(word) < 4:
        return None
    if _a_word_the_bot_writes(word) or _a_word_the_reading_knows(word):
        return None
    fits = [w for w in THING_WORDS_BY_LENGTH.get(len(word) + 1, ())
            if w[0] == word[0] and w[-1] == word[-1] and _one_letter_wrong(word, w)]
    return fits[0] if len(fits) == 1 else None


def _a_core_verb_typed_wrong(word, before, after=None):
    """The everyday verb `word` is one letter away from, right after a subject, or None.

    "i tke the bus to work" was answered "I'm listening", "i gte home at 6" and "i hav a shower
    then work" the same, "i mak dinner at 7" nothing at all; "i wek up at 6 every morning" came
    back as "You week up at 6 every morning", because the corrector had a spelling to guess at
    and this word has a reading from where it sits. The word being read is not in the lexicon
    and is not a name, and one letter out of place in "take", "get", "have" or "make" is that
    word: nothing else in the language is one edit from exactly one of them.
    """
    if not word.isalpha() or len(word) < 3 or len(word) > 7:
        return None
    if before not in BEFORE_A_VERB:
        return None
    if word in LEXICON or word in lexicon.COMMON_NAMES or word in _words_the_bot_writes():
        return None
    found = {verb for verb in CORE_VERBS if _one_letter_wrong(word, verb)}
    if word.endswith("d"):
        # A d at the end of the word is the d of an ending, not a letter typed where another
        # one belongs: "askd" is "asked" with the e left out and "wantd" is "wanted". Cutting
        # the d off is a slip the corrector already knows ("_missing_e"), and reading it here
        # as the verb with its last letter gone turned "she askd me to leave" into "she ask".
        found.discard(word[:-1])
    if not found and after in AFTER_A_VERB:
        # A vowel typed wrong is the same slip as a letter out of place, and it is the one the
        # corrector cannot see: "i wek up at 6 every morning" came back as "You week up at 6
        # every morning", because "wek" is one letter from the noun "week" while the verb it was
        # meant to be has its consonants and its vowels wrong ("wake"). Right after a subject,
        # and with the particle the verb takes after it ("up", "off", "out"), the consonants are
        # what is left of the word: only a core verb whose consonants are these, and which is no
        # more than one letter longer, is read. The particle is what keeps "i wak to work" as it
        # was typed, where the word could have been "walk" and a reading of "wake" is a guess.
        found = {verb for verb in CORE_VERBS if _its_vowels_typed_wrong(word, verb)}
    if len(found) == 1:
        return found.pop()
    return None


def _its_vowels_typed_wrong(word, other):
    """True when `other` is `word` with a vowel (or a whole syllable) typed wrong."""
    if word == other or word[0] != other[0] or not other.startswith(word[0]):
        return False
    if abs(len(word) - len(other)) > 1:
        return False
    consonants = "".join(letter for letter in word if letter not in "aeiou")
    return consonants and consonants == "".join(letter for letter in other if letter not in "aeiou")


def _near_a_part(word):
    """The part of the body a misspelt part is, or None.

    A part is a closed list, so a word with one letter typed into it or left out of it is still
    that part: "cheast" is a chest, "tomach" a stomach, "shouldr" a shoulder, "fingr" a
    finger, "nee" a knee, "hed" a head. Two parts fit the word and it is left alone, and a
    word the lexicon knows is never bent: "and" is not a hand, "year" is not an ear. The three
    letter parts are left out, because a letter in front of one of them makes an ordinary word
    the bot's list does not hold: "hear", "wear" and "tear" are each "ear" with one letter on.
    """
    if len(word) < 3 or not word.isalpha() or word in LEXICON or word in lexicon.BODY_PARTS:
        return None
    found = set()
    for part in lexicon.BODY_PARTS:
        if len(part) < 4 or abs(len(part) - len(word)) != 1:
            continue
        short, long = (word, part) if len(word) < len(part) else (part, word)
        i = 0
        while i < len(short) and short[i] == long[i]:
            i += 1
        if short[i:] == long[i + 1:]:
            found.add(part)
    return found.pop() if len(found) == 1 else None


PART_REACH = 3


# A game named by the shape of its pitch, or by the knockabout, rather than by its own name: "we
# play five a side on sunday", "anyone up for a kickabout". The game's name is the word the topic
# rule and the knowledge base match on, so a line that names the game this way named no game at all:
# "what should i eat before playing five a side" was answered with a supper pick from the fridge,
# and the same question with "football" in it with the carbs to eat an hour before. Only the reading
# is given the name: `clean` and `plain` keep the words the person typed, which is what a reply
# quotes back.
A_SIDE = frozenset("five six seven eight nine".split())


# A line that asks about the shape of the game itself, or about finding a team to play in, is not a
# line about playing today. The knowledge base has nothing about the form of the game - reading
# "how many players in five a side" as football reached the card about the professional game and
# answered "two halves of 45 minutes, with 11 a side", a confident wrong answer where the bot had
# said it did not know - and a card about picking a club to support is no answer to somebody looking
# for a team. Both shapes keep the words they typed, and so does a statement about the game's shape
# ("eleven a side is a full match"), which is why the full game is not one of the counts read here:
# it is the same game the row about watching it is about, and the line already names it.
ABOUT_THE_FORM = re.compile(r"""
    \bhow\s+many\s+(?:players?|people|a\s+side)\b
  | \bhow\s+(?:long|many\s+halves)\b[^.]{0,40}\b(?:match|game|half|halves)\b
  | \b(?:the\s+)?rules?\b
  | \boffside\b
  | \bhow\s+big\b
  | \bpitch\s+(?:size|dimensions)\b
  | \bfull\s+(?:match|game)\b
""", re.VERBOSE | re.IGNORECASE)
FINDING_A_TEAM = re.compile(r"""
    \b(?:join|joining|find|finding|looking\s+for|sign\s+up\s+(?:for|to)|get\s+into)\b
  | \bteams?\b[^.]{0,24}\b(?:in|near|around|local)\b
  | \b(?:clubs?|leagues?)\b
""", re.VERBOSE | re.IGNORECASE)


def _a_game_named_another_way(norm, words):
    """(`norm`, `words`) with a game named by its shape read as the game's own name.

    "five a side" is a small football match and nothing else is said that way, and one word stands
    in its place so the game sits where the person put it - in their setting clause or in their ask
    - instead of being bolted onto the end of the line. The knockabout is the same game named by the
    thing you do with the ball. The game's name goes into `words` as well, because that is the list
    the knowledge base is matched on; `clean` and `plain` keep the words the person typed, which is
    what a reply quotes back.

    A line about the make-up of the game, or about finding a team, names the game without asking
    anything about playing it, so it keeps the words it typed (see `ABOUT_THE_FORM`). So does a
    line whose subject is a part of the body that hurts: "i play five a side twice a week and my
    groin is sore" has a groin answer of its own, and naming the game put a football-injury card's
    clarifying question ahead of it - the person's part is the subject, and the game is only where
    they use it.
    """
    flat = " ".join(norm)
    if ABOUT_THE_FORM.search(flat) or FINDING_A_TEAM.search(flat):
        return norm, words
    if (any(word in lexicon.BODY_PARTS for word in words)
            and any(word in lexicon.PAIN_WORDS for word in words)):
        return norm, words
    out = []
    read = []
    index = 0
    while index < len(norm):
        if (norm[index] in A_SIDE and index + 2 < len(norm)
                and norm[index + 1] == "a" and norm[index + 2] == "side"):
            out.append("football")
            read.append("football")
            index += 3
            continue
        if norm[index] == "kickabout" or (norm[index] == "kick"
                                          and norm[index + 1:index + 2] == ["about"]):
            out.append("football")
            read.append("football")
            index += 1 if norm[index] == "kickabout" else 2
            continue
        out.append(norm[index])
        index += 1
    if not read or "football" in words:
        return out, words
    return out, list(words) + ["football"]


def _parts_that_hurt(words, fixes):
    """The line with every misspelt part of the body read as that part, repairs kept in `fixes`.

    Only where the line puts the word where a part goes: right beside a word of pain ("my
    cheast hurts", "a sore stomack", "my shouldr has been aching"), or straight after "my" or
    "our" with a word of pain close behind. The place is what tells a part of the body from an
    ordinary word a letter away from one, and the bot's word list does not hold every ordinary
    word ("hear", "wear", "tear" are each a letter from "ear"; "gear" and "chip" are a letter
    from "ear" and "hip"), so the word is never repaired on the letters alone. The words looked
    for are the two the topic rule needs (`topics.BODY` and `topics.HURTS`), so the repair and
    the rule cannot disagree.
    """
    pain = [at for at, word in enumerate(words) if word in lexicon.PAIN_WORDS]
    if not pain:
        return words
    out = []
    for at, word in enumerate(words):
        part = _near_a_part(word)
        beside = at - 1 in pain or at + 1 in pain
        mine = words[at - 1:at] in (["my"], ["our"]) and any(
            abs(other - at) <= PART_REACH for other in pain)
        if part and (beside or mine):
            fixes.append((word, part))
            out.append(part)
        else:
            out.append(word)
    return out


def _where_a_state_stands(before, before_before, after, before_words=None):
    """True when the words around this one are where a feeling can be said.

    The first person is the whole of the evidence ("im knackerd", "im so exausted", "i feel
    awsome"), and for somebody else it is the be-form and what follows it: "he is worrid about
    money" is a state, "what is nappy rash" is a rash.

    Every measure word between the two is stepped back over, not one of them: "im absolutely
    exausted", "im literally exausted", "im so so exausted" and "im really very exausted" are
    the same state as "im exausted" (lilac-cherry, #5358). Walking back is what keeps the frame
    off the word list, so the next temper word nobody has thought of yet ("im utterly flabbered")
    still reads as a state.
    """
    words = [word for word in (before_words if before_words is not None
                               else (before_before, before)) if word is not None]
    if words and words[-1] in DETERMINER_IN_FRONT:
        # "work left me exausted" arrives with the "me" already repaired to "my", and there the
        # "my" is the person the state was done to. A thing is only named when nothing earlier
        # in the line was done to anybody.
        done_to = (words[-1] in POSSESSIVE_IN_FRONT
                   and any(word in CAUSES_A_STATE for word in words))
        if not done_to:
            return False
    end = len(words) - 1
    back = end
    while back >= 0 and _measures_a_state(words[back]):
        back -= 1
    if back < 0:
        # Nothing but measure words in front of it ("so exausted", "a bit nackered"), or nothing
        # at all because the word opens the line ("exausted", "exausted from work", "worrid about
        # money"): a state is what a line opens with or what a bare "so" leads to, but only where
        # a state is what the line is about, because "nappy bag" and "nappy cream" are things.
        return _opens_a_state(after)
    stands = words[back]
    if stands in BE_BEFORE_A_STATE:
        return True
    if stands in THIRD_PERSON_BE:
        return _ends_a_state(after, opening=not (back >= 1 and (words[back - 1] in PERSON_WORDS
                                                               or words[back - 1] in OBJECT_PRONOUN)))
    # "i got so exausted", "that made me exausted", "work left me exausted": a verb that says
    # something was done to somebody puts them in a state, either with the person said ("made me",
    # "left me") or without ("i got so exausted"). Without the person, the word right after the
    # verb has to be a measure word or the state has to end the clause, so "i got nappy rash" is a
    # rash and "we got nappy" is not English anyway.
    if stands in CAUSES_A_STATE:
        return back < end or _ends_a_state(after)
    if stands in OBJECT_PRONOUN and back >= 1 and words[back - 1] in CAUSES_A_STATE:
        return True
    # "work left me exausted" is typed with "me" and the possessive repair reads it as "my"
    # before this point, so the same evidence arrives as "my". Kept only where the state ends the
    # clause, because "she got my nappy bag" is a bag.
    if stands == "my" and back >= 1 and words[back - 1] in CAUSES_A_STATE:
        return _ends_a_state(after)
    # A measure phrase is two words or more ("a bit", "a little", "kind of", "a tad"), so walk
    # back over those as well - but only to a first person be-form, because in the third person
    # the same words carry a thing ("it is a nappy" is a nappy) and that is the word this repair
    # must never touch.
    wide = back
    while wide >= 0 and _measures_a_state(words[wide], wide=True):
        wide -= 1
    if wide < back and wide >= 0 and words[wide] in BE_BEFORE_A_STATE:
        return True
    # A measure phrase taken all the way back to the start of the line is the same case as a bare
    # measure word: "a bit nackered", "kind of nackered", "a little exausted" with no "im" in
    # front of them at all (gentle-chair, plucky-pomelo, #5358).
    if wide < back and wide < 0:
        return _opens_a_state(after)
    return False


# The verbs that put somebody in a state: "i got so exausted", "that made me exausted", "work
# left me exausted", "it keeps me busy". A feeling is what these lead to, so the words after one
# are a state's place - but only with the person said ("made me") or a measure word between ("i
# got so"), because "i got nappy rash" is a rash (clear-weasel, #5358).
CAUSES_A_STATE = frozenset("""got get gets getting gotten make makes made making left leave leaves
    leaving kept keep keeps keeping felt feels feel feeling found find finds find made became
    become becomes turned turns turn drove driven drive drives""".split())
# The people a state is said about when something was done to them: "made me exausted".
OBJECT_PRONOUN = frozenset("""me us him her them you u u's myself yourself himself herself
    ourselves themselves""".split())

# A state is measured with phrases as well as words: "im a bit nackered", "im a little
# exausted", "im kind of knackered", "im a tad tired". These are the function words those
# phrases are made of - a closed class, like the determiners and the prepositions - so they are
# only taken in the first person, where a bare noun cannot stand ("it is a nappy" is a thing and
# stays one).
PHRASE_MEASURES = frozenset("""a an the bit little lot lots tad touch wee kind sort of out much
    many far way right that this these those enough half twice few some more most less least
    loads bunch ton tons hell heck mega extra damn damned fricking freaking""".split())


# When a state was: "i was exausted yesterday", "i was nackered last night", "we were miserabl all
# week". A state reads the same with one of these after it as with nothing at all, and without
# them a slip with a letter missing ("exausted", "nackered") was not repaired in a line that said
# when it was - 28 of the 882 slips the understanding lane measured (#5358, tall-moth) - while a
# slip of a letter in the wrong order ("knackerd") was, because that repair does not ask the frame.
# Only the words that say when, because a state is in the past as often as it is now, and every
# one of them also ends the sentence ("i was exausted last night" says no less than "i was
# exausted"). None of them makes a thing into a state: "what is nappy rash yesterday" is nothing
# anyone writes, and the thing words this repair must leave alone are words with a noun after
# them.
TIMES_A_STATE = frozenset("""yesterday last this week weekend morning mornings night nights
    evening evenings afternoon afternoons ago monday tuesday wednesday thursday friday saturday
    sunday january february march april june july august september october november december""".split())
# What comes after a state to say when it was, but comes after a thing just as easily ("nappy
# after nappy", "nappy before bed"), so it is only a state's ending where the line already says a
# state - after a be-form with somebody in front of it, or after a verb that puts somebody in one.
AFTER_A_TIME = frozenset("""all after before until till during while once then later earlier
    afterwards""".split())


def _ends_a_state(after, opening=False):
    """True when what follows a state is where a state can end: nothing, a function word, a time.

    `opening` is for the word that opens a line: there is nothing in front of it to say a state is
    what the line is about, so a word that a thing can be followed by ("nappy after nappy") is not
    taken as the end of one.
    """
    if after is None or after == "|" or after in AFTER_A_STATE:
        return True
    if opening:
        return False
    return (after in TIMES_A_STATE or after in AFTER_A_TIME
            or after in A_STATE_THEN_A_TIME)


def _opens_a_state(after):
    """True when what follows a word that opens a line is a state rather than a thing.

    A state that opens a line is the whole of what they said ("exausted", "exausted from work",
    "worrid about money", "nackered all the time"), so it is repaired; a word that opens a line
    and is followed by a thing is part of that thing, so it is not ("nappy cream", "nappy rash",
    "nappy change", "nappy bag", "nappy bin"). Only the word right after it decides, and every
    function word - a preposition, a joiner, a time word, a determiner - says the line is about a
    state, so the list of things does not have to be written down.

    A word that says when is not one of those, because a thing is followed by one as easily as a
    state is: "nappy yesterday" is a nappy, and the line would have to say a state some other way
    ("i was nackered yesterday") before the word is read as one.
    """
    return _ends_a_state(after, opening=True) or after in NOT_A_THING


def _a_measure_spelt_wrong(word):
    """True when this is a measure word spelt wrong ("completey exausted", "absolutley terified").

    The measure words are ordinary words, so a slip in one of them is repaired anywhere; this is
    only about the frame, which cannot see that the word in front of a state is still a measure
    word with a letter missing. Only words long enough to be no other word with one letter
    different, so "realy" and "completly" count and "to" and "so" do not.

    The closed list is not the whole story, because the "-ly" is what says a word measures a state
    (`_measures_a_state`) and the words in the list above are the ones people say, not the ones
    they type. A slip that breaks the ending is then in neither: `absolutley`, `extremley`,
    `genuinly` and `realy` are none of them one letter from a word of the list, and none of them
    ends in "ly" any more, so `im absolutley terified` lost the feeling the spelled line keeps.

    The ending itself is what gets typed wrong, and it is typed wrong in one of two ways: the "l"
    and the "y" of "-ly" in the wrong order ("absolutley", "extremley") or a doubled "l" typed
    once ("totaly", "realy"). Both leave a word ending in "y" with a single "l" among its last
    three letters, which no other long word has - "safety", "memory", "quality", "mouldy",
    "floppy", "turkey" all end in a letter that is not the "l" of the ending, and the short words
    that do ("barley", "parsley", "trolley") are shorter than an adverb of that shape. The adverb
    itself is often not in the vocabulary at all ("absolutely", "extremely" are made by an ending
    rule rather than written down, and their stem is not either), so it is the shape of the ending
    that is read, and no list of adverbs is asked for and none is kept.
    """
    if not (len(word) >= 6 and word.isalpha()):
        return False
    if any(_one_letter_apart(word, measure) for measure in AMOUNT_BEFORE_A_STATE):
        return True
    if word.endswith(("aly", "lye", "yl")):
        return True
    # "The l and the y in the wrong order" also catches the words that end in "ley" of their own
    # ("barley", "parsley", "trolley"), and those are six or seven letters where an adverb of that
    # shape ("absolutely", "extremely") is nine or more.
    return len(word) >= 9 and word.endswith("ley")


def _measures_a_state(word, wide=False):
    """True when this word only says how much or how, not what.

    The measure words are a closed list of the ones people type ("so", "very", "not", "dead",
    "proper"), and any word made into an adverb with "-ly": "im absolutely exausted", "im
    literally exausted", "im utterly exausted" are the same state as "im exausted", and a list
    of intensifiers is a list somebody has to keep adding to (lilac-cherry, #5358). The "-ly"
    is what says the word is about the state rather than a thing, so "im genuinely exausted"
    reads without anybody naming "genuinely" here.
    """
    if wide and word in PHRASE_MEASURES:
        return True
    return (word in AMOUNT_BEFORE_A_STATE or word in BARE_TO
            or (len(word) >= 5 and word.endswith("ly")) or _a_measure_spelt_wrong(word))


def _a_letter_typed_twice(word):
    """The feeling a word is when one of its letters was typed twice, or None.

    "im saad", "im maad", "im loow", "im shyy", "im lonelyy": the letter that came out twice is
    one letter too many, and the word without it is a feeling. The one-edit reader in
    `_one_letter_apart` refuses these on purpose - a letter typed into a word only counts when it
    is a vowel, and a four letter word needs its feeling to be longer than it is, because a word
    that short is as often a name - and the doubled letter is not always a vowel ("lonelyy").
    Nothing is lost by reading the one slip on its own terms: the word being read is not in the
    lexicon, and the word without the doubled letter is a feeling and not a name.
    """
    if len(word) < 4 or word in lexicon.COMMON_NAMES:
        return None
    for place in range(len(word) - 1):
        if word[place] != word[place + 1]:
            continue
        shorter = word[:place] + word[place + 1:]
        if shorter in lexicon.FEELINGS:
            return shorter
    return None


# The shapes a line introduces a person in, where a word one letter short of a feeling is that
# person's name: "hi, im saad", "im saad from egypt", "saad here", "im saad (34)", "nice to
# meet you im saad". A doubled letter is the same evidence for a name as for a typo - "Saad" is
# an ordinary name - so the introduction is asked first and the doubled letter is left alone
# there. Being told "Sorry to hear that" for saying your own name is worse than the typo reaching
# the shrug, and it is permanent: the reply is stock and the person cannot tell why it happened.
INTRODUCING_A_PERSON = frozenset("""
    hi hello hey heya hiya hii hiii yo howdy greetings morning afternoon evening sup meet
""".split())
# What follows the name of the person being introduced: "saad here", "im saad from egypt".
INTRODUCING_AFTER = frozenset("here from".split())


def _an_introduction(before, before_before, after, before_words=None, after_words=None):
    """True when this word is the name a line introduces rather than a state it states.

    The five shapes are the ones a person gives their name in, and none of them is a shape a
    feeling comes in: a greeting in front of it, "this is X", an "X here" or "X from <place>"
    tail, an age after it, or a word at the front of the line that the verb after it has as its
    subject ("saad is my brother"): a state is what a line says about somebody, not what it
    says about a word.
    """
    for word in (before_words or ()):
        if word in INTRODUCING_A_PERSON:
            return True
    if after in INTRODUCING_AFTER:
        return True
    if before == "is" and before_before in ("this", "that"):
        return True
    if after == "is" and before in (None, "|"):
        # A word that opens the line and has a verb after it is the subject of that verb.
        return True
    # An age after the name, in either the shape people type it: "im saad and im 34", "im saad
    # (34)". The words after the word are only looked at where one of the two links allows it.
    if after in ("and", "|") or (after or "").isdigit():
        for word in list(after_words or ())[:3]:
            if word.isdigit():
                return True
    return False


# The states a person can be in, which are a closed list of their own: hungry and cold are
# ordinary words the lexicon holds as words, so they are not on the feeling list, and a slip of
# one of them was read as nothing at all - "im hongry" was answered "Nice to meet you, Hongry".
# Only the states said of a person are here, and only in the form the pools answer, so a slip of
# any of them reaches the word it is a slip of.
STATES_OF_A_PERSON = frozenset("""hungry thirsty starving famished peckish sleepy tired
    exhausted shattered knackered drained dizzy queasy nauseous bunged freezing frozen cold
    hot warm boiling sweaty bored lonely miserable""".split())


def _a_letter_wrong_in_a_state(word):
    """The one state word `word` is a letter away from, or None.

    This is a whole-letter test, not the vowel-only one `_a_slip_of_a_state` makes, and it is
    only asked where the line itself says the word is how the person is: a letter typed wrong
    is the ordinary slip of a state word ("hungy", "thisty", "colde"), and the state list is
    the closed one, so nothing else in the language is a letter from one of them. The word has
    to be the last word of the clause as well, because "been staring at a screen all day" is a
    letter from "starving" and is not about hunger at all.
    """
    # Only the states of a person, and only a word of five letters or more: a name is a letter
    # from a feeling far more often than a state is, and "im cory" is not "im cry".
    if len(word) < 5 or word in LEXICON or word in lexicon.COMMON_NAMES:
        return None
    found = {state for state in STATES_OF_A_PERSON
             if state[:1] == word[:1] and _a_letter_apart(word, state)}
    if len(found) == 1:
        return found.pop()
    return None


def _a_letter_apart(word, other):
    """True when one letter added, left out, doubled or swapped round makes the other word.

    This is the feeling rule's own test (`_one_letter_apart`) with the consonant let in: people
    do type "hungy" for hungry and "thisty" for thirsty, a consonant left out in the middle,
    and "dizzzy" with one letter doubled. A letter on the front or the end of a whole word is
    still not a slip, which is what keeps "im busy" out of it.
    """
    if _one_letter_apart(word, other):
        return True
    if abs(len(word) - len(other)) != 1:
        return False
    short, long = (word, other) if len(word) < len(other) else (other, word)
    return any(short == long[:i] + long[i + 1:] for i in range(1, len(long)))


def _near_a_feeling(word, before=None, before_before=None, after=None, alone=False,
                    before_words=None, after_words=None):
    """The feeling a misspelt feeling word names, or None.

    A feeling word is a closed list, so one letter out is still that feeling: "knackerd" is
    "knackered", "shatterd" is "shattered", "worrid" is "worried", "exausted" is
    "exhausted". This is the class a general spell-fixer has to refuse, because next to an
    ordinary word the shortest edit is another ordinary word; next to a feeling word there is
    nothing to confuse it with. A word that could be two feelings is left alone.

    Only where a state can stand: after a be-form, with at most one measure word between ("im so
    exausted", "she was knackerd", "i feel awsome"). Every other feeling repair in this file is
    framed like that and this one was not, so a real word the lexicon does not hold became the
    feeling anywhere in the line: "how do i change a nappy" was read as "snappy" (four deck
    lines, and the question reached the pool for a short temper), "my nappy bag is heavy" as
    "snappy bag". The frame is the second guard, after the lexicon.
    """
    if not alone and not _where_a_state_stands(before, before_before, after, before_words):
        return None
    # A word somebody uses as it stands is not a feeling with a slip in it, however close it
    # sits: "i scored a goal today" was read as "scared" and answered "I'm sorry - that's
    # frustrating", and "this place is sacred" was the same, because the state frame was right
    # and the word was one letter from the feeling. `lexicon.NOT_A_FEELING` names those words,
    # and the true slips ("exausted", "nerveus") still repair.
    if len(word) < 4 or word in LEXICON or word in lexicon.NOT_A_FEELING:
        return None
    # One letter typed twice is one letter too many, whatever the letter is, and whatever the
    # length of the word: "im saad" and "im loow" were four letter words the length rule below
    # refuses, and "im lonelyy" a consonant the vowel rule above refuses.
    twice = _a_letter_typed_twice(word)
    if twice and not _an_introduction(before, before_before, after, before_words, after_words):
        return twice
    # The short states are where a letter left out costs the answer, and they were refused here
    # by length: "im emty" and "im angy" were each answered "Nice to meet you, Emty" and
    # "Nice to meet you, Angy", while "im empty" and "im angry" get the real answer. A four
    # letter word is the shape of a name as well, so the list of names is asked first, and the
    # feeling has to be one letter longer than the word - a letter left out, never swapped in.
    if len(word) == 4:
        # A four letter word starts a phrase as often as it is a state, and only the word right
        # after it is looked at: "im tied up at work" is busy, not tired, and "im bred to run" is
        # about a dog. So a word this short is repaired only where nothing follows it.
        if after is not None and after != "|":
            return None
        if word in lexicon.COMMON_NAMES:
            return None
    # "-cious" and "-xious" are the same sound and the same slip ("ancious" is "anxious").
    # The rest of the word has to be a feeling already, so this reaches the closed list only.
    if word.endswith("cious") and word[:-5] + "xious" in lexicon.FEELINGS:
        return word[:-5] + "xious"
    # The same sound with a t heard in it: "anctious" is "anxious".
    if word.endswith("ctious") and word[:-6] + "xious" in lexicon.FEELINGS:
        return word[:-6] + "xious"

    found = sorted(feeling for feeling in lexicon.FEELINGS
                   if _one_letter_apart(word, feeling)
                   and (len(word) >= 5 or len(feeling) == len(word) + 1)
                   and not _a_consonant_left_out_of_an_ing_word(word, feeling))
    if len(found) == 1:
        return found.pop()
    # Two letters gone is the next class out, and it is the common one once the word is long:
    # "im stessd" is "stressed", "im exasted" is "exhausted", "im depresd" is "depressed". A word
    # this long has room for two letters, and the slip is always the same shape - letters left
    # out, never swapped - so the test is that the typed word is the feeling with one or two
    # letters taken out, first letter kept. Swaps and two candidates are refused, and so is a
    # name: "im stessd" is a state, "im sarah" and "im katie" are people.
    if after in (None, "|") and _the_state_is_the_whole_frame(before, before_before,
                                                              before_words):
        return the_feeling_two_letters_are_gone_from(word)
    return None


def _a_consonant_left_out_of_an_ing_word(word, feeling):
    """True when the only difference is a consonant missing from a word ending in "-ing".

    A vowel is what people leave out of an "-ing" word when the keys are under the fingers
    ("starvng", "annoyng", "depresing"), so a vowel is the whole of the slip the frame and the
    closed feeling list were built to catch. A consonant left out of an "-ing" word is an
    ordinary verb underneath instead, and the feeling on the list is another word: "staring" is
    "stare" with "-ing" on it and only the "v" of "starving" makes it a state, so "been staring
    at a screen all day" was read as "been starving at a screen all day". The frame cannot see
    the difference - "ive been exausted" and "ive been staring" stand in the same place - so the
    letter is what decides.
    """
    if not word.endswith("ing") or len(feeling) != len(word) + 1:
        return False
    i = 0
    while i < len(word) and word[i] == feeling[i]:
        i += 1
    return word[i:] == feeling[i + 1:] and feeling[i] not in VOWEL_SET


def _the_state_is_the_whole_frame(before, before_before, before_words=None):
    """True when nothing but the person or the be-form stands in front of the state.

    Two letters out is a long enough slip for two different words to be that close, and a state
    said of a thing is where the two meet: "my phone screen is cracked" is a screen, "cracked"
    being "crackered" by two letters. So this repair only reaches a line whose subject is the
    person - "im stessd", "im so stessd", "she was stessd" - and stands down the moment a thing is
    named in front of the be-form ("my phone screen is cracked", "the table leg is cracked").
    """
    words = [word for word in (before_words if before_words is not None
                               else (before_before, before)) if word]
    back = len(words) - 1
    while back >= 0 and _measures_a_state(words[back]):
        back -= 1
    return back == 0


def the_feeling_two_letters_are_gone_from(word):
    """The feeling a long word has lost two letters of, or None: "stessd" is "stressed".

    Its own function because the name store has to ask the same question: "im stessd" was read
    as a state and answered "Hi Stessd", and the name was kept for the rest of the chat
    ("whats my name" then said Stessd). A word this long has room for two letters, and the slip
    is always the same shape - letters left out, never swapped - so the test is that the typed
    word is the feeling with one or two letters taken out, first letter kept. Two candidates and
    a common name are refused: "im sarah" and "im katie" are people, not a state.
    """
    if not isinstance(word, str):
        return None
    low = word.strip().lower()
    if len(low) < 6 or low in lexicon.COMMON_NAMES:
        return None
    found = sorted(feeling for feeling in lexicon.FEELINGS if _two_letters_out(low, feeling))
    return found[0] if len(found) == 1 else None


def _two_letters_out(word, feeling):
    """`word` is `feeling` with one or two letters taken out of it, and nothing else changed."""
    if len(feeling) - len(word) not in (1, 2) or word[:1] != feeling[:1]:
        return False
    if _one_letter_apart(word, feeling):
        return False
    rest = iter(feeling)
    return all(letter in rest for letter in word)


def _feeling_without_its_ending(word):
    """"confuse" is "confused": a feeling typed with its ending left off, or None.

    "im confuse", "im annoy", "im bore" and "im excit" are how people type when the ending of
    the word they mean does not come out, and they are words already ("confuse" is a verb), so
    the misspelling fixer may not touch them - but next to "im" they are the feeling. The same
    slip costs the last letter of "nervous", "anxious" and "miserable" ("im nervou", "im anxio",
    "im miserabl"), and it can cost the whole of a longer ending - a whole "-ing", "-l" or
    "-ty": "im gratefu", "im guil", "im awfu", "im anxie", "im dread", "im mourn" and
    "im emotiona" were each answered "Nice to meet you, Gratefu". Only the closed feeling list
    is consulted, and only the endings a feeling word takes, so a name is still a name
    ("im matt", "im justin", "im anna").
    """
    if len(word) < 3 or not word.isalpha():
        return None
    known = lexicon.FEELINGS | lexicon.A_STATE
    # A word that already is the state is not a state with its ending missing: "i am hurt" is
    # hurt, not "hurting", and "cry" is cry, not "crying". The short endings never needed this
    # because no feeling is another feeling with two letters on the end.
    if word in known:
        return None
    for ending in ("ed", "d", "y", "s", "us", "e", "g", "ing", "l", "ty"):
        if word + ending in known:
            return word + ending
    return None


def reads_as_a_feeling(word):
    """True when this word is a feeling word, or a slip of one the engine repairs.

    The reading already lowers a misspelt feeling to that feeling, so a module that takes a
    bare word for a name has to ask the same question, or a person typing one word about
    themselves is welcomed by name: "im knackerd" was answered "Nice to meet you, Knackerd".
    A name that the one-edit fixer would bend is still a name ("im matt", "im justin"), and so
    is a word that only looks like a state.
    """
    if not isinstance(word, str):
        return False
    low = word.strip().strip(".,!?;:'\"()").lower()
    if not low or not low.isalpha():
        return False
    if _feeling_without_its_ending(low) or _a_letter_wrong_in_a_state(low):
        # A state word with a letter typed wrong is how they are, not what they are called.
        # This one is asked without the line in front of it, so only the words that are a letter
        # from a state and nothing else are taken: "im hungy" is not a name, "im shy" is.
        return True
    if low in lexicon.SOUNDS_LIKE_A_FEELING:
        return True
    if any(word in lexicon.FEELINGS or word in lexicon.A_STATE
           or word in STATES_OF_A_PERSON
           for word in _token(low, [], alone=True)):
        return True
    # The "-d" dropped off a feeling: "im confuse" is "im confused", "im annoye" is "im annoyed".
    # The letter is put back on the word as typed, not on the repaired one, so a name the fixer
    # bends is left alone ("ann" becomes "an", and "and" is on the feeling list).
    if low + "d" in lexicon.FEELINGS | lexicon.A_STATE:
        return True
    # A short state with a vowel left out of it is still how they are: "im spnt" is spent,
    # "im bet" is beat, "im wrn" is worn, "im wepy" is weepy. `_near_a_feeling` refuses a word
    # this short on purpose, so the repair never happens, but the name reader has to know the
    # word is a state or it welcomes the person by it: "im spnt" and "im bet" were answered
    # "Nice to meet you, Spnt" and "Nice to meet you, Bet".
    if _a_vowel_left_out_of_a_state(low):
        return True
    return False


def _a_vowel_left_out_of_a_state(word):
    """The state a short word had a vowel left out of, or None: "spnt" is "spent", "bet" is "beat".

    Only a vowel that was never typed, never a letter changed: a short word with one letter
    changed is usually another word and often somebody's name ("sid" is not "sad"), and no name
    people are given is a state with a vowel missing - the one that looked like it, "don" for
    "done", is on the common names list and is left alone. A word the lexicon knows keeps its
    own meaning ("bat" is not "beat").
    """
    if not 3 <= len(word) < 5 or not word.isalpha():
        return None
    if word in LEXICON or word in lexicon.COMMON_NAMES:
        return None
    found = sorted(state for state in lexicon.FEELINGS | lexicon.A_STATE
                   if len(state) == len(word) + 1 and word in _one_vowel_less(state))
    return found[0] if len(found) == 1 else None


def _one_vowel_less(word):
    """Every way of leaving one vowel out of the word, as a set."""
    return {word[:at] + word[at + 1:] for at, letter in enumerate(word)
            if letter in VOWEL_SET and 0 < at < len(word) - 1}


def reads_as_a_sound(word):
    """True when the word is the sound of a feeling ("board" is bored), not its spelling.

    A module that files a bare word as a name asks this as well, because "im board" is how
    somebody says they are bored, not what they are called. It is a separate question from
    `reads_as_a_feeling`, which is about the word as it is spelt, and it is the caller with the
    whole line in front of it that decides: "my name is board" names a person.
    """
    if not isinstance(word, str):
        return False
    low = word.strip().strip(".,!?;:'\"()").lower()
    if not low or not low.isalpha():
        return False
    from . import kinds
    return kinds.feeling_by_sound(low) is not None


def repaired_tokens(word):
    """What the engine reads this one token as, alone: "gd" is "good", "y" is "why".

    A module holding its own list of words that cannot be a name asks this rather than the
    private table, so "im gd" is caught by the same lists that hold "im good".
    """
    if not isinstance(word, str):
        return []
    low = word.strip().strip(".,!?;:'\"()").lower()
    if not low:
        return []
    return list(_token(low, [], alone=True))


def spelled(word):
    """What the engine's own tables read this one token as, or [] when only a guess would.

    ``repaired_tokens`` also carries the fixer's guesses, and those need the "says more than
    the word did" guard: a cut is not evidence ("ann" collapses to "an", and "an" is not a
    reason to doubt somebody's name). A curated entry is evidence on its own - the table
    says what the word stands for - so "hungrey" is "hungry" even though that is one letter
    shorter, and a module that holds its own list of words asks this rather than re-reading
    the tables.
    """
    if not isinstance(word, str):
        return []
    low = word.strip().strip(".,!?;:'\"()").lower()
    if not low:
        return []
    for table in (lexicon.CHAT, lexicon.EXPAND, lexicon.US_SPELLINGS,
                  lexicon.MISSPELLINGS, lexicon.URGENT_MISSPELLINGS):
        if low in table:
            return table[low].split()
    return []


def _unsays_the_word(word, variant):
    """True when the only change is an un-doubled consonant in front of -ing, -ed, -er, -est.

    Both spellings are English words and they say different things: "hopping" is not "hoping",
    "taping" is not "tapping", "planed" is not "planned". Which one the person meant is nowhere
    in the letters, so the doubled letter in front of an ending is left as it was typed rather
    than guessed at - "island hopping in greece" was read as "island hoping".
    """
    if len(variant) >= len(word):
        return False
    ending = next((end for end in ("ing", "est", "ed", "er") if variant.endswith(end)), "")
    if not ending:
        return False
    stem = variant[:-len(ending)]
    if len(stem) < 2:
        return False
    doubled = stem + stem[-1]
    return word == doubled + ending


def _a_word_of_the_bots(word):
    """Whether this is a word to repair *towards*: the lexicon, or a word the bot's own base writes.

    The repair vocabulary used to be the lexicon alone, so a slip in a word only the bot's cards
    use was left as typed. "rouitne" and "chloesterol" are one swapped pair from "routine" and
    "cholesterol" - both of them things the bot has a card about, and neither of them an everyday
    English word - so nothing was repaired, and the line was read as a word about nothing: the card
    missed, or the slip was said back to the person ("Same for the drippign"). The words the bot
    writes in its own keys and answers are spelled by construction (that is what
    `_words_the_bot_writes` is for), so a slip one letter from one of them is a slip of that word.
    """
    if word in NO_SWAP_TO:
        # A word the bot never puts in place of a slip, whichever class found it: "hagned my
        # washing out" is somebody's washing, not a hanging.
        return False
    return word in BASE or word in _words_the_bot_writes()


def fix_typo(word):
    """A high-confidence correction for a word that is not in the lexicon, or None.

    Only typo classes that do not collide with ordinary words are used: a doubled or
    un-doubled letter ("recomend", "untill"), an ie/ei swap ("recieve"), a left-off final
    g ("mornin") and a dropped w ("kno"). A confident wrong correction is worse than none, so one-letter
    substitutions and transpositions are left to the curated MISSPELLINGS map: with a
    lexicon this size, "three" would otherwise become "there". A test keeps that honest: a
    real word is never bent into the word the bot answers with ("stairs" is not "stars",
    "swelling" is not "spelling").
    """
    if not word.isalpha():
        return None
    if word in BASE:
        # A word the lexicon holds is a word of its own, whatever it looks like: "travelled"
        # and "traveled" are both right, and each was being read as a slip of the other.
        return None
    if word in lexicon.TYPED_WORDS:
        # A word the deck and the bot's own prose use as it stands is a word, even when it is
        # one letter from another one's doubled spelling: "bled", "wed", "telly", "lager",
        # "thee". The whole deck reads 23 turns differently without this guard, and every one
        # of them is a word bent into a wrong one.
        return None
    if word in _words_the_bot_writes():
        # A word the bot's own base writes is spelled right by construction, so it is a word of
        # its own: "stain", "order", "spilt" and "matters" are not slips of "satin", "roder",
        # "split" and "mattres". The same guard already keeps a swapped pair from reading one as
        # the other; it belongs on every class now that the bot's words are repair targets too.
        return None
    if word in lexicon.NOT_A_FEELING:
        # An everyday word one letter from a feeling is not that feeling typed with a slip, and
        # the two-letters-the-wrong-way-round reader does not know it: "sacred" is one swap from
        # "scared", so "this place is sacred" was read as a line about being frightened and
        # answered "a lot to carry". A word on this list is left as it was typed.
        return None
    if word in lexicon.COMMON_NAMES:
        # A first name is a word, to the person who has it, and nothing in the line says it is
        # a typo: "matt is my son" was noted as "mat", "ann is my sister" as "an", and the
        # repair reached the doubled letter of one and the doubled letter of the other's name.
        # The sentence a person writes about someone they know is the one thing the bot must
        # not get wrong, so a name the list holds is left as it was typed.
        return None
    shunned = _shun_variant(word)
    if shunned:
        return shunned
    stopped = _stopped_th(word)
    if stopped:
        return stopped
    short = _short_double(word)
    if short:
        return short
    doubled_once = _doubled_letter_words(word)
    if len(word) == 3 and doubled_once:
        # A three-letter word is not too short for this slip - "i need a wek off work", "im
        # trying to kep calm" - but a short word is bent only towards one of the words people
        # use most, so "cok" is a cook and nothing stranger is guessed.
        best = sorted(doubled_once, key=lambda w: COMMON_RANK.get(w, 10 ** 6))[0]
        if COMMON_RANK.get(best, 10 ** 6) < 2000:
            return best
    if len(word) < 4:
        return None
    a_thing = _a_thing_a_letter_short(word)
    if a_thing:
        return a_thing
    # A doubled letter in front of an ending is left as it was typed: the un-doubled spelling
    # says something else ("hopping" is not "hoping", "planed" is not "planned"), and which one
    # the person meant is nowhere in the letters.
    candidates = [w for w in _double_variants(word)
                  if _a_word_of_the_bots(w) and not _unsays_the_word(word, w)]
    candidates += doubled_once
    candidates += [w for w in _ie_variants(word) if _a_word_of_the_bots(w)]
    dropped = _dropped_g(word)
    if dropped:
        candidates.append(dropped)
    said_as_n = _an_ing_said_as_n(word)
    if said_as_n:
        candidates.append(said_as_n)
    candidates += [w for w in _dropped_letter(word) if _a_word_of_the_bots(w)]
    candidates += [w for w in _a_leading_h(word) if _a_word_of_the_bots(w)]
    candidates += [w for w in _extra_vowel(word) if _a_word_of_the_bots(w)]
    candidates += [w for w in _missing_vowel(word) if _a_word_of_the_bots(w)]
    # A plural is an everyday form of a word rather than a word, so "the windas" is kept when
    # the lexicon knows "windows". The singular stays a base word: letting everyday forms in
    # made "winder" (of "wind") tie with "window", and a tie is no guess at all.
    candidates += [w for w in _a_said_for_an_ending(word)
                   if w in BASE or (w.endswith("s") and w in LEXICON)]
    # A long word two letters the wrong way round is the emergency vocabulary first ("collasped"
    # is "collapsed") and the ordinary one after it, and the caller still keeps only one answer.
    candidates += [w for w in _swapped_pair(word) if _a_word_of_the_bots(w) or w in URGENT_WORDS]
    candidates += [w for w in _two_letters_the_wrong_way_round(word) if _a_word_of_the_bots(w)]
    flat_ed = _missing_e(word)
    if flat_ed:
        candidates.append(flat_ed)
    candidates += [w for w in _e_kept_before_ing(word) if w in LEXICON]
    left_out = _an_emergency_word_left_out(word)
    if left_out:
        candidates.append(left_out)
    # A letter the word does not say, and a letter typed twice.
    #
    # The t of "often", "listen", "fasten", "castle" and "whistle" is not said, so it is the
    # letter people leave out of the word. It goes back where those words have it: straight
    # before "en" or "le" and straight after a consonant. A general letter put anywhere turns
    # ordinary words into other ones ("pond" is one letter from "pound", "bush" from "brush", and
    # both are words a line is about), and with a vowel in front of the ending it would make
    # "tile" into "title".
    def _a_silent_t_put_back(typed):
        for ending in ("en", "le"):
            if typed.endswith(ending) and len(typed) > len(ending) + 1:
                if typed[-len(ending) - 1] in VOWELS:
                    continue
                yield typed[:-len(ending)] + "t" + ending

    candidates += [w for w in _a_silent_t_put_back(word) if w in BASE or w in LEXICON]
    # The doubling rule above fences every doubled pair off, because "taping" is not "tapping" -
    # but the fence belongs on a word that *is* a word as typed. "watter" is nothing, so "water"
    # loses nothing, and the line that had it keeps its card. The fence is only ever loosened for
    # a typed word the lexicon does not hold, so nothing that means something is bent.
    typed_is_a_word = word in BASE
    candidates += [w for w in _double_variants(word)
                   if w in BASE and not (typed_is_a_word and _unsays_the_word(word, w))]
    words = sorted(set(candidates), key=lambda w: COMMON_RANK.get(w, 10 ** 6))
    if not words:
        return None
    if len(words) == 1:
        return words[0]
    if COMMON_RANK.get(words[0], 10 ** 6) < 120 and COMMON_RANK.get(words[1], 10 ** 6) > 900:
        return words[0]
    return None


OPENERS = frozenset(lexicon.OPENERS.split())
WH_OPENERS = frozenset("what why when where who which whose how".split())


def _slip(word, opener):
    """How `word` is one letter away from `opener`: "missing", "extra" or None.

    A letter swapped for a different one is not counted: in a word this short a swap says
    nothing ("who" and "why" are both one swap from "whn"), while a letter added or left out
    is the shape people type at speed.
    """
    if word == opener or word[:1] != opener[:1] or abs(len(word) - len(opener)) != 1:
        return None
    short, long = (word, opener) if len(word) < len(opener) else (opener, word)
    i = 0
    while i < len(short) and short[i] == long[i]:
        i += 1
    if short[i:] != long[i + 1:]:
        return None
    return "missing" if short is word else "extra"


def fix_opener(word):
    """The opener word `word` is one letter away from, or None when none or two fit.

    Openers of two letters are only reached by un-doubling a letter ("hii" -> "hi"), because
    one letter means too little in a word that short. `normalise` only asks about a word
    nothing else knows, and only where a clause begins.
    """
    if not word.isalpha() or len(word) < 2:
        return None
    doubled = len(word) > 2 and word[-1] == word[-2]
    # Two letters are only worth a repair when they are the bones of a question word: "hw" and
    # "wy" say "how" and "why", while "ha" says nothing about being "has".
    short = len(word) == 2
    fits = []
    for opener in OPENERS:
        shape = _slip(word, opener)
        if not shape:
            continue
        if short and opener not in WH_OPENERS:
            continue
        # A letter typed twice ("heyy" -> "hey") is the only extra letter worth reading as a
        # slip: any other extra letter is usually a real word of its own, and one of those at
        # the start of a line turns a statement into a question ("hash" is not "has", "ways"
        # is not "was", "mary" is not "may", "wars" is not "was", "halve" is not "have").
        if shape == "extra" and not doubled:
            continue
        fits.append((opener, shape))
    # Several openers can be one letter away ("weres" is "were" plus one and "wheres" less
    # one). The end of a word is the part people get right, so a fit that keeps it wins; a
    # last letter typed twice ("heyy") is settled the same way.
    for test in (lambda opener: opener[-1] == word[-1],
                 lambda opener: doubled and opener[-1] == word[-2]):
        if len(fits) > 1:
            kept = [f for f in fits if test(f[0])]
            fits = kept if len(kept) == 1 else fits
        if len(fits) == 1:
            break
    return fits[0][0] if len(fits) == 1 else None


def _plain_word(word):
    """True when this is a real word the engine knows, not something it only guessed at.

    The lexicon also holds the ordinary endings of real words ("worries", "weres"), which is
    what a typo must still be allowed to reach: "weres the best place to park" is "where is",
    and only a word that is real on its own is left alone.
    """
    return word in BASE or word in lexicon.CHAT or word in lexicon.MISSPELLINGS \
        or word in lexicon.EXPAND


def _repair_openers(clauses, fixes):
    """Fix a typo in the word a clause opens with, in place.

    The opening word decides how the whole line is read: "whts the weather like tmrw" is a
    question, "thnks" a thanks, "hii" a hello, and one misspelt letter otherwise leaves the
    line looking like a statement. The repair stays very narrow: only a word no other rule
    knows, only where a clause begins (after a discourse word too: "so wy is my boiler..."),
    and only when exactly one opener is a single slip away.
    """
    for clause in clauses:
        for start in sorted({0, len(clause) - len(strip_leaders(clause))}):
            if start >= len(clause):
                continue
            word = clause[start]
            if _plain_word(word):
                continue
            fixed = fix_opener(word)
            if fixed:
                fixes.append((word, fixed))
                clause[start:start + 1] = _token(fixed, fixes)   # a chat form expands again
                break
    return clauses


def _four_spells_for(word):
    """A leading 4 inside a word is "for": "4get", "4got", "4getting", "4give", "4ever".

    People write the first syllable of a word with the digit, and the word then means
    nothing to any reader: "i keep 4getting things" came back as an echo of the line where
    "i keep forgetting things" answers. Only a 4 in front of a word the engine already knows
    is spelled out, so "i have 4 cats" and "a table for 4" are untouched, and "4tunate"
    stays as typed because "tunate" is not a word. One 4 per word is all people write
    ("4give", never "4give4"), so the rest must be letters. The words this happens to put
    the "for" in front of a g or a vowel ("forget", "forgot", "forgive", "forever"), which is
    what keeps "4night" and "4ward" from being spelled into a word that does not exist.
    """
    if len(word) < 4 or not word.startswith("4") or not word[1:].isalpha():
        return None
    rest = word[1:]
    if rest[0] not in "aeioug":
        return None
    if rest in BASE or rest in lexicon.CHAT or rest in lexicon.MISSPELLINGS or rest in LEXICON:
        return "for" + rest
    return None


def _collapse(word):
    """'sooo' -> 'so', 'pleeease' -> 'please'; a variant that is a real word, else None.

    A word stretched in two places still lands: settling every run at once would take
    "heellooo" to "helo" and throw it away, so the runs are tried in every combination.
    """
    if not re.search(r"(.)\1\1", word):
        return None
    runs = list(re.finditer(r"(.)\1+", word))
    if len(runs) > 3:
        return None
    # Every stretched letter settled at once, in every combination: "heellooo" only reads as
    # "hello" when the e and the o come back to one but the l stays doubled.
    choices = [range(1, min(3, len(match.group(0))) + 1) for match in runs]
    for lengths in itertools.product(*choices):
        variant = word
        for match, length in reversed(list(zip(runs, lengths))):
            variant = variant[:match.start()] + match.group(1) * length + variant[match.end():]
        if variant != word and variant in LEXICON:
            return variant
    return None


def _apostrophe(word):
    """Expand or settle one token that has an apostrophe."""
    if "'" not in word:
        return None
    base, _, rest = word.partition("'")
    if rest == "t" and word.endswith("n't"):
        stem = word[:-3]
        if stem == "ca":
            return ["can", "not"]
        if stem == "wo":
            return ["will", "not"]
        if stem == "sha":
            return ["shall", "not"]
        if stem == "ai":
            return ["is", "not"]
        return [stem, "not"] if stem else None
    if rest == "m":
        return [base, "am"]
    if rest == "re":
        return [base, "are"]
    if rest == "ve":
        return [base, "have"]
    if rest == "ll":
        return [base, "will"]
    if rest == "d":
        return [base, "would"] if base in PRONOUN_BASES else [base]
    if rest == "s":
        if base in PRONOUN_BASES:
            return [base, "is"]
        # A chat word or a misspelling carrying its apostrophe-s is that word and "is", not the
        # bare word: "wot's wrong with my boiler" was read as "wot" alone, so the s the person
        # typed went missing and the line reached the tradesman answer where "what is wrong with
        # my boiler" gets the boiler one. The base goes through the same tables an
        # apostrophe-free token goes through, and only when its repair is one word.
        read = (lexicon.CHAT.get(base) or lexicon.MISSPELLINGS.get(base)
                or lexicon.URGENT_MISSPELLINGS.get(base) or "")
        if read and " " not in read:
            return [read, "is"]
        return [base]
    return None


DIGIT_WORDS = dict(zip("0123456789",
                       "zero one two three four five six seven eight nine".split()))
DIGIT_WORDS.update({str(n): w for n, w in zip(
    range(10, 21),
    "ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen "
    "twenty".split())})


# People type "2" for "to" as often as for "two", and "4" for "for". The next word says
# which reading fits: "2 the shop" and "2 cook" are "to", "2 eggs" is "two", "me 2" is
# "too", "4 lunch" is "for" and "4 eggs" is "four". The number is what people mean most of
# the time, so it is the reading the digit keeps unless the next word asks for another one:
# "i have 4 cats", "meet me at 4", "party of 4" and "4 pm" are all counts.
BEFORE_WORD = frozenset("""the a an my your his her their our its this that these those
me you him us them it""".split())
BEFORE_VERB = frozenset("""go get do make see eat cook buy book call ask tell say try keep
put wear bring take watch read start stop pay save sleep work clean fix check learn study
write send order pick choose plan join find leave stay drink wash boil roast give show help
move sort turn cut fill set talk chat walk run live meet visit play listen wait come sit
stand hold pour chop stir fry bake serve mix add remove park drive catch post share print
sign email text speak change cancel return swap replace freeze heat store wrap pack load
grill steam reheat defrost tidy paint build grow plant have know""".split())
# "4" is "for" only in front of one of these: a determiner or a pronoun ("4 the kids",
# "4 my back") or a thing people do something for ("4 lunch", "4 later", "4 free").
FOR_A = frozenset("""the a an my your his her their our its this that these those
me you him us them one two three""".split())
FOR_OBJECT = frozenset("""lunch dinner tea breakfast supper brunch now later tonight
tomorrow today free once example sure good real ages fun sale keeps christmas weekend
everyone everybody nothing starters afters dessert pudding coffee cake
milk bread butter cheese sugar flour rice pasta petrol diesel fuel wine beer juice""".split())
# "4 lunch" at the start of a line is still "for lunch"; "4 tomorrow please" is four people,
# so only the food words are read that way with nothing in front of them.
FOR_MEAL = frozenset("""lunch dinner tea breakfast supper brunch starters afters dessert
pudding cake""".split())
# "for" cannot follow a be-verb, so "we are 4 today" is four today, not "for today".
BE_VERBS = frozenset("am is are was were".split())
# "2" is "too" in front of an adjective the way people say it: "2 much salt", "2 late".
TOO_A = frozenset("""much many late early soon long often hard fast big small hot cold
tired busy expensive cheap old young loud noisy sweet salty spicy easy quick heavy light
slow warm dark bright strong weak soft loud""".split())
# "2" at the end of a clause is "too" when the line already said who (or what) it is about:
# "me 2", "love it 2". After anything else it is the number: "see you at 2", "a table for 2".
TOO_AFTER = frozenset("me you us him her them i we they it".split())
# A "2" at the end of a line after one of these is "to", not "too" and not the number: "what u
# up 2" and "i will get back 2" are the same "to" as "what u up to", and read as "two" they
# reached nothing at all. "in" and "on" are left out on purpose: "im in 2" is "i'm in too".
TO_AFTER = frozenset("up down over back out round through along".split())
# A negation in front of the "2" is what makes the next word an adjective being graded rather
# than a thing being counted: "not 2 bad" and "not 2 keen" are "too", while "2 bad eggs" and
# "not 2 minutes away" are numbers. The words here are the ones a person grades that TOO_A does
# not already hold; the negation is the whole of the safety, so "2 bad eggs" is untouched.
A_NEGATION_BEFORE = frozenset("not".split())
TOO_A_GRADED = TOO_A | frozenset("""bad shabby keen happy far sure worried good pleased glad
    proud cross upset annoyed safe well fun useful handy honest bright""".split())
# A digit next to one of these is a number, not a word that sounds like it: "4 x 5" is four
# times five, and "take 2 a day" is two a day.
OPERATORS = frozenset("x * / + - plus minus times divided squared".split())
COUNTS = frozenset("a an per each".split())
# A number counts something: a plural ("4 eggs", "4 ways"), a unit ("4 months", "4 o'clock",
# "4 quid") or a word that is not a thing at all ("the 4 of us", "at 4 pm", "4 and 7", "grade 4
# in gcse maths"). In front of anything else the "4" is not counting, so it is "for": "tips 4
# sleep", "time 4 bed", "reasons 4 leaving", "advice 4 new mums", "stuck 4 childcare". Reading
# those as counts is why "any tips 4 sleep" went off as "any tips four sleep" and reached
# nothing at all.
COUNT_UNITS = frozenset("""year month week day hour minute second mile miles kilometre kilo
gram litre pint cup quid pound euro dollar pence percent point star item person people child
children man men woman women foot feet grand ton bob
yr yrs mth wks wk hr hrs min mins sec secs km cm mm kg g mg ml cl lb lbs oz ft yds yd
tsp tbsp
pack slice seat piece wheel toaster suite star speed door
january february march april may june july august september october november december
jan feb mar apr jun jul aug sep sept oct nov dec""".split())
# A number in front of one of these is a count when another noun follows it: "a 4 bed house",
# "a 3 door car". "ready 4 bed" is still "for", so the word itself never counts on its own.
COMPOUND_HEADS = frozenset("bed class bay birth seat".split())
COMPOUND_TAILS = frozenset("""house flat home room rooms car cars van cottage bungalow
door doors window windows drive suite garden""".split())
# Written after a digit, these are not things, so the digit is counting: "at 4 pm", "4 o'clock",
# "the 4 of us", "4 and 7". A clock time is the one a person types most, so its spellings are all
# here: "4pm", "4 pm", "4 o'clock", "4 o clock".
NOT_COUNTED_AFTER = frozenset("""and or but so in on at of to by as is was were for with from
about than per each every a an the my your his her their our its this that these those
more fewer less most other others another few out tomorrow today tonight now later soon twice please
am pm oclock o'clock o’clock""".split())


# A number in front of a noun that is itself followed by a noun is counting the first one: "a 4
# bedroom house", "a 4 seater car", "a 4 course meal", "a 4 poster bed". The tail is what says
# so, which keeps the purpose reading where the noun ends the line - "tips 4 sleep", "time 4
# bed", "stuck 4 childcare" - and where what follows is a time or a rate - "4 work tomorrow".
# The head of a compound says how big the thing is ("4 seater", "4 bedroom"), so an adjective
# is not one: "advice 4 new mums" is advice for them, not four new mums. And the tail has to be
# the noun the compound names, not a clause starting up again ("time 4 bed i reckon").
NOT_A_COMPOUND_HEAD = frozenset("""new old small big cheap little large lovely nice good bad
first second third last next own same whole different other another
i me you him her us them he she we they it""".split())
NOT_A_COMPOUND_TAIL = frozenset("""i we they he she it you me us them there thats that's
and or but so if when because though anyway""".split())


def _counts_a_compound(head, tail):
    """Whether a number `head tail` counts the head rather than meaning "for" it."""
    if not head or not tail or head == "|" or tail == "|":
        return False
    if head.isdigit() or tail.isdigit():
        return False
    if head in NOT_COUNTED_AFTER or tail in NOT_COUNTED_AFTER:
        return False
    if head in NOT_A_COMPOUND_HEAD or tail in NOT_A_COMPOUND_TAIL:
        return False
    if head.endswith("ing") or tail.endswith("ing"):
        return False
    return True


# Written after one of these, a number is the label of a thing rather than a purpose: a school
# year, a class, a question. "year 4 homework" is year four's homework and "class 4 teacher"
# teaches class 4, so nothing that follows can turn the number into "for". These are the words a
# number can be *in* or *on* and that are not a thing anybody asks for - you are in year 4, on
# question 4 - which is what separates them from a word that only happens to come before a digit
# ("time 4 bed", "tips 4 sleep", "stuck 4 childcare").
#
# A table, a room, a bus, a seat and a team are the other way round: they are things people ask
# for, so "table 4 two" is a booking for two and "room 4 the night" is a room for the night. Those
# stayed out of the list, because the digit after them is the purpose and the food answer needs it.
A_LABEL_BEFORE = frozenset("""year years class classes grade grades form forms level levels stage
stages part parts section sections page pages question questions chapter chapters episode episodes
lesson lessons unit units term terms step steps""".split())


# A number after one of these is how many of a thing is taken or used: "take 4 paracetamol",
# "i took 4 ibuprofen", "add 4 potatoes". "need" and "want" are not here, because "i need 4
# childcare" is the purpose and not a count.
NUMBERS_BEFORE = frozenset("""take took takes taking ate eaten eat drink drank drinks
buy bought buys get got gets use used uses add added adds gave give gives
a an the my your his her their our another first last only just""".split())


def _counts_a_thing(word):
    """Whether a number in front of this word is counting something."""
    if not word or word == "|":
        return True
    word = (word.split() or ["|"])[0]
    if word.isdigit() or word in COUNT_UNITS or word in NOT_COUNTED_AFTER:
        return True
    return len(word) > 2 and word.endswith("s") and not word.endswith(("ss", "us", "is"))


def _digit_word(token, before, after, after_after=None):
    """The word "2" or "4" stands for where it sits, or None to keep it a number.

    The next word says which reading fits: "2 the shop" and "2 cook" are "to", "2 eggs" is
    "two", "me 2" is "too", "4 lunch" is "for" and "4 eggs" is "four". The number is what
    people mean most of the time, so it is the reading the digit keeps unless the next word
    asks for another one: "i have 4 cats", "meet me at 4", "party of 4", "4 pm" and
    "we are 4 today" are all counts.
    """
    if token not in ("2", "4"):
        return None
    if (after or "").lower() in ("yr", "yrs"):
        # "a 2 yr old" counts years, and the chat table would otherwise read the `yr` as "your"
        # and turn the number into "to".
        return "two" if token == "2" else "four"
    before = before or "|"
    # The words either side are read the way the chat table reads them ("/dont/" is "do not"),
    # and the word nearest the digit is the one that decides: the last of the one before it and
    # the first of the one after it.
    spelled = lexicon.CHAT.get(before) or lexicon.EXPAND.get(before) or before
    spoken_before = (spelled.split() or ["|"])[-1]     # "dont" -> "not", the word before the digit
    after = lexicon.CHAT.get(after, after) if after else "|"
    after = (after.split() or ["|"])[0]
    number = "two" if token == "2" else "four"
    if after in OPERATORS or before in OPERATORS:
        return number
    if after in COUNTS and (before in BEFORE_VERB or before in TOO_AFTER or before == "|"):
        tail = lexicon.CHAT.get(after_after, after_after) if after_after else "|"
        tail = (tail.split() or ["|"])[0]
        if tail in A_PERIOD_FOLLOWS or tail == "|":
            return number      # "take 2 a day" is two, and "4 a week" is four
        return "for"           # "what can i do 4 a sore throat": a thing, not a rate
    if spoken_before in A_LABEL_BEFORE and not after.isdigit():
        return number          # "year 4 homework", "class 4 teacher", "table 4 tomorrow"
    if token == "2" and before in MOTION_BEFORE and after not in A_PERIOD_FOLLOWS:
        return "to"             # "going 2 spain" and "off 2 bed", but "going 2 weeks" is two
    if after in DEMONSTRATIVE:
        after_after = lexicon.CHAT.get(after_after, after_after) if after_after else "|"
        after_after = (after_after.split() or ["|"])[0]
        if after_after in A_PERIOD_FOLLOWS:
            return number      # "i did 4 this week" counts days, it is not "for this week"
    if token == "2":
        if before in TO_AFTER and (after == "|" or after in UP_TO_TAGS):
            return "to"             # "what u up 2", "back 2 mate"
        if after == "|":
            return "too" if before in TOO_AFTER else number
        if after in TOO_A:
            return "too"
        if after in BEFORE_WORD or after in BEFORE_VERB:
            return "to"
        if after in TOO_A_GRADED and spoken_before in A_NEGATION_BEFORE:
            return "too"        # "not 2 bad", "not 2 keen", "not 2 minutes" stays a count
        return number
    if before in BE_VERBS:
        return number
    if after in FOR_A:
        return "for"
    if after in FOR_OBJECT and (before != "|" or after in FOR_MEAL):
        return "for"
    if after.isdigit() and not before.isdigit():
        return "for"          # "waited 4 20 mins": a count is never written twice
    if after_after is not None:
        head = after
        tail = lexicon.CHAT.get(after_after, after_after) if after_after else "|"
        tail = (tail.split() or ["|"])[0]
        if head in COMPOUND_HEADS and tail in COMPOUND_TAILS:
            return number     # "a 4 bed house" counts the beds, "ready 4 bed" is for bed
    if before in NUMBERS_BEFORE and not _counts_a_thing(after):
        return number         # "take 4 paracetamol" is four tablets, not four for
    if after_after is not None:
        tail = lexicon.CHAT.get(after_after, after_after) if after_after else "|"
        tail = (tail.split() or ["|"])[0]
        if _counts_a_compound(after, tail):
            return number     # "a 4 bedroom house", "a 4 course meal", "a 4 seater car"
    if not _counts_a_thing(after):
        return "for"          # "tips 4 sleep", "time 4 bed", "stuck 4 childcare"
    return number


REPEAT_ONCE = frozenset("""i you we they he she it me my the a an to and of in is am are
was were do does not at on for""".split())


REPEAT_ONCE_SUBJECTS = frozenset("i you we they he she it u".split())


def _once_only(tokens):
    """Drop a word typed twice in a row when it is one a line never says twice.

    "i dunno" expands to "i i do not know" because the chat spelling carries its own "i", and
    "the the" and "to to" are the same kind of slip. An adjective or a word like "very" is kept,
    because people mean it twice.
    """
    out = []
    for token in tokens:
        if out and token == out[-1] and token in REPEAT_ONCE:
            continue
        out.append(token)
    return out


# Chat-speak drops the subject: "am off to bed" is "i am off to bed", "was thinking of quitting"
# is "i was thinking of quitting". A yes/no question turns the subject round instead ("am i too
# late", "was the film good", "have you got a minute"), so the subject is missing exactly when
# nothing that could be one follows the auxiliary. Putting the "i" back makes the rest of the
# engine read the line the way it reads "im off to bed", which is what the person meant: without
# it, "am off to bed" was read as a question and handed to the "I don't know, try a search" hedge.
AUX_OPENS = frozenset("am is are was were have has had been".split())
# The ones where the dropped subject is the person typing: "am off to bed", "was thinking of
# quitting", "have no idea". ("were shattered", "are knackered" and "has gone quiet" drop a "we"
# or a "he" that cannot be put back safely, so the reading is fixed for those, the words are not.)
DROPPED_SUBJECT_AUX = frozenset("am was have".split())
_SUBJECTS = frozenset("""i you we they he she it there that this these those one anyone someone
    everyone nobody nothing none who which what""".split())
# Words that are only ever a predicate after an auxiliary: "am off to bed", "am knackered",
# "was well worth it". Nothing that can name a thing goes in here, and "there" and the subject
# negations stay out: "is there anything for a cold" and "is nobody home" are questions.
_PREDICATE_ONLY = frozenset("""going gonna off out away back home up down well knackered
    shattered exhausted drained starving fine alright okay ok rubbish great late here""".split())
# A state of the person is a whole predicate on its own, so "am", "was" and "were" in front of one
# have lost their subject: "were hungry", "was shattered all week", "am freezing". The list is the
# states a person can be in where the feeling is what the line is about - hungry, skint, soaked -
# and not a thing the state word also names ("were down to the last tenner" is a shortage, and a
# determiner after "was" keeps it a question: "was the film good").
_A_STATE_OF_THE_PERSON = frozenset("""hungry thirsty starving famished peckish busy rushed
    freezing frozen broke skint brassic sleepy
    dizzy tired shattered knackered exhausted drained ill unwell poorly sick lousy rough
    down low fed up miserable sad happy chuffed pleased livid fuming cross annoyed upset gutted
    relieved worried anxious nervous scared frightened stressed""".split())
_SUBJECTLESS_AUX = frozenset("am was were".split())
# The words people put in front of a state and nowhere else: "were both tired", "am so relieved".
# A determiner is not one of them, so "was that ok" and "was the film good" still ask.
_STATE_FILLER = frozenset("""both so really very totally absolutely properly too all quite still
    always just completely dead kind of a bit""".split())
# What may come after the state and leave it the whole predicate. The state is the last thing said
# about the person, so what follows it is the end of the clause, an intensifier, a preposition that
# starts the reason or the time ("were tired after", "am so busy at the moment"), a determiner, a
# time word, or a joining word. A plain noun after it means the state was the first half of a
# compound and the line asks about a thing: "was sick leave ok" and "was happy hour good" were
# being read as a person saying how they feel, which was confidently wrong where the line before
# only hedged.
_STATE_TAIL = frozenset("""at in on for after before by since till until from about with around
    over through during the a an this that these those my your his her their our
    last next today tonight tomorrow yesterday week weekend morning afternoon evening night
    month year day now then again still too also already anymore lately recently though but and
    so because when while if all every up out off sick stiff rotten
    to be been being had got go going""".split())
# The auxiliaries that cannot take an "-ing" word for a subject, so one after them means the
# person was left off the front of the line.
_SUBJECTLESS_ONLY = frozenset("am was".split())
# A negation after "have" is not a subject either ("have no idea", "have nothing to wear").
_HAVE_NEGATIONS = frozenset("no none nothing".split())
# Nor is a participle: "have got a bad head", "have had a rough week" are the person saying what
# they have, with the "i" left off the front, and reading them as questions cost the health answer
# and got a search hedge instead. "have got a minute" is the one that really is the ask, so a
# request word after the thing keeps the line a question.
_HAVE_PARTICIPLES = frozenset("got had been seen made taken spent".split())
_HAVE_THING = frozenset("a an the my our his her their your some this that".split())
_HAVE_ASKING = frozenset("minute moment sec second mo chance word".split())
# What can follow a participle and leave it as the verb: "was thinking **of** quitting", "was
# making tea **and**". A determiner or a noun after the participle means the participle was naming
# a thing instead: "is cooked chicken still ok" and "is cracking your knuckles bad" ask, so they
# are left alone.
_AFTER_PARTICIPLE = frozenset("""of to for in on at with about from by up out off over through
    into onto and but so or because if when while then that than as not never ever too also
    just""".split())


def opens_without_subject(words, index):
    """True when `words[index]` is an auxiliary and nothing that can be its subject follows.

    "am off to bed" and "was thinking of quitting" have no subject; "am i too late" and "was the
    film good" do, so they are questions and are left alone.
    """
    if index >= len(words) or not words[index]:
        return False
    word = words[index]
    if word not in AUX_OPENS:
        return False
    rest = [w for w in words[index + 1:] if w != "|"]
    if not rest:
        return False
    second = rest[0]
    if second in _SUBJECTS:
        return False
    if word == "am":
        # "am" has one subject only, "I", and if it is not in the line then the person left it
        # off: "am hungry", "am skint", "am freezing", "am not sure", "am nearly done". A
        # question with "am" in it puts the pronoun back ("am i too late"), which the line above
        # has already let through, so there is nothing else a bare "am" can open. Every one of
        # those lines was read as an inverted yes/no question instead: "am hungry" got a search
        # hedge, "am skint" the money shrug, and "am freezing" the cold-weather answer.
        return True
    if second in _PREDICATE_ONLY:
        return True
    if word in _SUBJECTLESS_AUX:
        clause = []
        for word_after in words[index + 1:]:
            if word_after == "|":
                break
            clause.append(word_after)
        at = 0
        while at < len(clause) and clause[at] in _STATE_FILLER:
            # "were both tired", "am so relieved": the intensifier is not the state.
            at += 1
        if (at < len(clause) and clause[at] in _A_STATE_OF_THE_PERSON
                and (at + 1 == len(clause) or clause[at + 1] in _STATE_TAIL
                     or clause[at + 1] in _STATE_FILLER)):
            return True
    if second in _HAVE_NEGATIONS and word == "have":
        return True
    if word == "have" and second in _HAVE_PARTICIPLES and len(rest) > 2:
        # A time on the end makes it an arrangement rather than something the person has the
        # wrong way: "have got the kids tonight" is a plan, and the reply for a plan is better
        # than the note-back a dropped subject gets.
        return (rest[1] in _HAVE_THING and rest[2] not in _HAVE_ASKING
                and not any(w in TIME_WORDS for w in rest[1:]))
    if len(second) > 4 and (second.endswith("ing") or second.endswith("ed")):
        if len(rest) < 2:
            return True                   # "was shattered", "am starving"
        # "am" and "was" cannot take a gerund for a subject, so the person was left off: "was
        # thinking of quitting". "is cooking with gas cheaper" can - "cooking" is what the
        # question is about - so there the verb has to be shown by a verb after it.
        if word in _SUBJECTLESS_ONLY:
            return rest[1] in _AFTER_PARTICIPLE
        after = rest[2] if len(rest) > 2 else ""
        return rest[1] in _AFTER_PARTICIPLE and after.endswith(("ing", "ed"))
    return False


def _only_leaders_before(words, index):
    """True when this clause so far is nothing but filler ("so am off to bed").

    "he banged his head and was knocked out" has a subject in front of the "and", so nothing was
    dropped there and the line must be left alone.
    """
    start = 0
    for i in range(index):
        if words[i] == "|":
            start = i + 1
    return all(word in LEADERS for word in words[start:index])


def _lookahead(words, index, n=3):
    """The next few tokens as the reading will have them ("thinkin" -> "thinking").

    A line typed in a hurry leaves the subject off and misspells the word after it: "am thinkin
    of jackin in me job". Whether the subject is missing depends on the word the reader will see,
    not the one that was typed.
    """
    out = []
    for word in words[index + 1:index + 1 + n]:
        if word == "|":
            break
        out.append(_token(word, [])[0] if _token(word, []) else word)
    return out


def subject_missing(words, index):
    """True when the subject after this auxiliary was dropped and it was the person typing."""
    return words[index] in DROPPED_SUBJECT_AUX and opens_without_subject(words, index)


def _opener_is(word):
    """'wots'/'whatz'/'whyz' -> ['what', 'is'] / ['why', 'is'], or None.

    People run the "s" of "is" onto the question word and often spell the question word as
    they say it: "wots the best way", "whyz my boiler losing pressure". Neither half is a
    typo the other readers can find - "wots" is not one letter from an opener, and it is
    not in the spelling tables - so the line reads as news and gets a "noted" back. The
    stem is read the way the chat table reads it ("wot" -> "what"), and only a question
    word is ever completed this way.
    """
    if len(word) < 4 or word[-1] not in "sz":
        return None
    stem = word[:-1]
    if stem in WH_OPENERS:
        return [stem, "is"]
    spelled = (lexicon.CHAT.get(stem) or lexicon.EXPAND.get(stem)
               or lexicon.MISSPELLINGS.get(stem) or "").split()
    if len(spelled) == 1 and spelled[0] in WH_OPENERS:
        return [spelled[0], "is"]
    return None


# "cause" is both the chat spelling of "because" and an ordinary verb and noun: "i dont want to
# cause trouble", "it could cause problems", "what is the cause of the fire". The chat table
# answered `cause` with "because" wherever it stood, so those became "because trouble" and "the
# because of the fire". A repair belongs in the position that means it, so "because" is read only
# where the line goes on with a subject or an auxiliary - the shape that follows "because" - and
# the verb and noun keep their word.
CAUSE_A_SUBJECT_FOLLOWS = frozenset("""i im ive id ill you youre youve we were weve they theyre
    theyve he hes she shes it its that thats this these those there theres my your our his her
    their if when whenever while since as so and but or not never no nobody nothing everyone
    everybody someone something anyone anything am is are was were do does did dont doesnt did
    didnt cant cannot couldnt wont wouldnt shouldnt isnt wasnt arent hasnt havent hadnt u ur ya""".split())
# What can follow "the" and make it a clause rather than the noun's article: "cause the bus was
# late" is because the bus was late, while "cause the problem" is the verb with its object.
CAUSE_A_CLAUSE_VERB = frozenset("""is was were are am has had have will would can could did does
    do dont doesnt didnt wont cant cannot isnt wasnt arent hasnt hadnt""".split())
# A noun after "cause" is the verb's object ("cause trouble", "cause a fuss"), except after one of
# these, where the cause is the thing being asked about or described: "the cause of the fire",
# "a cause for concern".
CAUSE_BEFORE_A_NOUN = frozenset("the a an this that my your our his her their any no every some "
                                "another one".split())
# A word in front that only a verb follows: "what could cause it", "to cause trouble", "it may
# cause this". These settle the reading whatever comes after.
CAUSE_BEFORE_A_VERB = frozenset("to could would can may might must should will shall does did do "
                                "doesnt didnt dont wont cant cannot never not".split())
# A demonstrative can start a clause ("cause this is a problem") or be the verb's object ("what
# could cause this", "cause this problem"); the word after it decides.
CAUSE_A_DEMONSTRATIVE = frozenset("this that these those".split())


def _cause_in_place_is_the_verb(before, after, after_words=None):
    """Whether a typed `cause` is the verb or the noun rather than the chat spelling of because.

    A subject after it is "because" ("cause i was late", "cause my bus was late"), and so is the
    end of a line with no article in front ("i did it just cause"). Anything else keeps the word.
    """
    if before in CAUSE_BEFORE_A_VERB:
        # "what could cause it", "to cause trouble": only the verb follows these.
        return True
    if before in CAUSE_BEFORE_A_NOUN:
        # "the cause is unknown", "a cause for concern": the article makes it the noun whatever
        # follows, including the "is" that would otherwise look like a clause.
        return True
    if after in CAUSE_A_DEMONSTRATIVE:
        # "what could cause this" and "cause this problem" are the verb; "cause this is a
        # problem" and "cause that i was late" are "because".
        rest = list(after_words or ())[1:2]
        return not rest or rest[0] not in CAUSE_A_SUBJECT_FOLLOWS
    if after in CAUSE_A_SUBJECT_FOLLOWS:
        return False
    if after is None:
        # The end of a line: "i did it just cause" is because, and the noun cases were taken above.
        return False
    if after == "the" and any(word in CAUSE_A_CLAUSE_VERB
                              for word in (after_words or ())[1:4]):
        return False
    return True


def _token(word, fixes, before=None, before_before=None, after=None, alone=False,
           before_words=None, after_words=None):
    """Normalise one lower-case token to zero or more ordinary words.

    `before` is the word it follows, for the few repairs that depend on where a word sits.
    """
    if word == "cause" and _cause_in_place_is_the_verb(before, after, after_words):
        return [word]
    if before is not None:
        # The chat table turns "wif" into "with" wherever it stands; in the place a person
        # goes the same letters are the wife.
        thing = _a_thing_where_a_thing_goes(word, before)
        if thing:
            fixes.append((word, thing))
            return [thing]
    if word in DIGIT_WORDS:
        return [DIGIT_WORDS[word]]
    if word in lexicon.CHAT:
        return lexicon.CHAT[word].split()
    if word in lexicon.EXPAND:
        return lexicon.EXPAND[word].split()
    if word in lexicon.US_SPELLINGS:
        # The same word in the American spelling: the reading, the topics and the knowledge base
        # all know the British one, and the line was not misspelt, so this is not a repair - the
        # plain line keeps the spelling the person used.
        return [lexicon.US_SPELLINGS[word]]
    if word in lexicon.MISSPELLINGS:
        return lexicon.MISSPELLINGS[word].split()
    if word in lexicon.URGENT_MISSPELLINGS:
        fixes.append((word, lexicon.URGENT_MISSPELLINGS[word]))
        return [lexicon.URGENT_MISSPELLINGS[word]]
    if "'" in word:
        expanded = _apostrophe(word)
        if expanded:
            return expanded
    for_spelled = _four_spells_for(word)
    if for_spelled:
        fixes.append((word, for_spelled))
        return [for_spelled]
    collapsed = _collapse(word)
    if collapsed:
        fixes.append((word, collapsed))
        return [collapsed]
    if word in LEXICON or not word.isalpha() or len(word) < 2:
        return [word]
    opened = _opener_is(word)
    if opened:
        fixes.append((word, opened[0]))
        return opened
    pluraled = _z_for_s(word)
    if pluraled:
        fixes.append((word, pluraled))
        return [pluraled]
    ached = _ache_for_aike(word)
    if ached:
        fixes.append((word, ached))
        return [ached]
    corrected = fix_typo(word)
    if corrected:
        fixes.append((word, corrected))
        return [corrected]
    fronted = _said_with_an_f(word)
    if fronted:
        fixes.append((word, fronted))
        return [fronted]
    swapped_inside = _said_with_an_f_anywhere(word)
    if swapped_inside:
        fixes.append((word, swapped_inside))
        return [swapped_inside]
    feeling = _near_a_feeling(word, before, before_before, after, alone, before_words,
                              after_words)
    if feeling:
        fixes.append((word, feeling))
        return [feeling]
    return [word]


# A food that is written as two words and kept as one. The kitchen's pantry is keyed on the one
# word ("chickpeas", "sweetcorn"), so the two-word spelling reached it as two other foods: "chick
# peas" came back as pea soup and "sweet corn" as a line about seasoning. Only pairs that name
# one food both ways, so joining them cannot change what the line is about.
ONE_WORD_FOODS = (
    (re.compile(r"(?<![a-z])chick pea(?![a-z])"), "chickpea"),
    (re.compile(r"(?<![a-z])chick peas(?![a-z])"), "chickpeas"),
    (re.compile(r"(?<![a-z])sweet corn(?![a-z])"), "sweetcorn"),
)


def _one_word_food(clean):
    """The foods written as two words set down as the one word the pantry and answers use."""
    for pattern, one in ONE_WORD_FOODS:
        clean = pattern.sub(one, clean)
    return clean


JOINED_WORDS = re.compile(r"(?<![a-z])(?:%s)(?![a-z])"
                           % "|".join(sorted(lexicon.JOINED_WORDS, key=len, reverse=True)))


def _joined_words(clean):
    """The words people write as one and say as two, set down as the two in `clean`.

    Nothing here is a word, so there is nothing to lose by repairing it where it is written: the
    fed-up reader matches on `clean`, so "im fedup with my job" used to be a shrug while "im fed up
    with my job" got the fed-up reply.
    """
    if not JOINED_WORDS.search(clean):
        return clean
    return JOINED_WORDS.sub(lambda m: lexicon.JOINED_WORDS[m.group(0)], clean)


def _z_for_s(word):
    """A plural written with a z, where the s is a word the engine knows: "ideaz", "dogz".

    People type the plural with the letter that sounds like it - "ideaz 4 tea", "my kidz",
    "thingz" - and the line reaches nothing, so a question about dinner comes back as a
    search hedge. Only a z that stands where an s would is spelled, and only when the word
    that makes is one the engine or the knowledge base already knows, so "jazz", "quiz",
    "buzz" and every real word ending in z are left alone (a word the bot writes stops the
    lookup, and a typed z-word that is a real word is not spelled).

    The knowledge base is read as well as the lexicon because a plural is not always one of
    the lexicon's own words: "ants" is the word the pest rows answer, while the lexicon only
    holds "ant", so "antz" was left alone and "how do i get rid of antz" got the search hedge
    that its correctly spelt twin does not.
    """
    if len(word) < 4 or not word.endswith("z"):
        return None
    if word in LEXICON or _a_word_the_bot_writes(word):
        return None
    fixed = word[:-1] + "s"
    return fixed if fixed in LEXICON or _a_word_the_bot_writes(fixed) else None


def _ache_for_aike(word):
    """"headaike" is "headache": -ache written the way it is said.

    Only the tail is read, and only where the word the tail makes is one the engine knows, so
    a name or a place that happens to end in -aike is never bent into a body part.
    """
    for tail in ("aike", "ayke", "eake"):
        if word.endswith(tail) and len(word) > len(tail):
            fixed = word[:-len(tail)] + "ache"
            if fixed in LEXICON:
                return fixed
    return None


# A contraction typed with a space where the apostrophe is: "she s 84", "i m not sure", "what s
# the point", "we re going", "they ve gone", "you ll see", "he d never say", and the same slip on
# a "not" - "don t worry", "isn t it". The readers are written on the joined word, so the split
# line reached nothing: "she s 84" was answered "I'm listening - say more if it helps" where
# "shes 84" and "she's 84" were both noted. Only a pronoun can take these letters straight on,
# so a plural noun keeps its own ("the dogs ears"), and the "not" needs the joined word to be one
# the engine knows, so a real word in front of a "t" is left alone.
SPLIT_CONTRACTION = re.compile(
    r"\b(i|u|you|he|she|it|we|they|that|there|what|who|where|when|how|this|these|those|let)"
    r"\s+(s|m|re|ve|ll|d)\b(?=\s|[.,!?;:)]|$)", re.IGNORECASE)
SPLIT_NOT = re.compile(r"\b([a-z]{2,}n)\s+t\b(?=\s|[.,!?;:)]|$)", re.IGNORECASE)
# The only words English makes with a "not" are these, so the joined letters are checked against
# them: no other word takes a "t" on the end.
NOT_WORDS = frozenset("""dont doesnt didnt isnt wasnt arent werent havent hasnt hadnt cant couldnt
    shouldnt wouldnt wont mustnt neednt aint shant mightnt""".split())


def _a_contraction_typed_with_a_space(clean):
    """The line with a contraction's two halves put back together, where the halves are its own.

    "she s 84" is how "she's 84" is typed when the apostrophe is left out and the space is kept,
    and the letters after the pronoun are never a word: no line says "she s" or "i m". The
    apostrophe goes back with them, because the joined letters are a word of their own
    elsewhere - "we re based in leeds" is not "were based in leeds". The
    "not" half is joined only when the word it makes is one the engine knows, so "an t" and a
    real word in front of a stray "t" keep their letters.
    """
    if not SPLIT_CONTRACTION.search(clean) and not SPLIT_NOT.search(clean):
        return clean
    clean = SPLIT_CONTRACTION.sub(lambda m: m.group(1) + "'" + m.group(2), clean)

    def join_not(match):
        if match.group(1) + "t" not in NOT_WORDS:
            return match.group(0)
        return match.group(1) + "'t"

    return SPLIT_NOT.sub(join_not, clean)


# "what u up too", "what are you up too": the doubled o is the slip people make on "up to".
# Only after a `what` opener of the same clause, so "are you up too?" (awake as well, thanks)
# keeps its word.
UP_TOO_ASKS = re.compile(r"(\b(?:what|whats|watcha|whatcha|wotcha)\b[^.!?]{0,24}?\b)up too\b")

# A broken heart, said out as a phrase. People write it this way far more often than they type
# "heartbroken", and without this the other words in the line decided the reading: "my heart is
# broken and i dont know what to do" reached the resting heart-rate answer ("the heart beats
# faster... 60 to 100 beats a minute is normal"), and "my heart is broken over a boy" reached
# nobody at all ("Got it. Is there anything you'd like a hand with?"). The words around "heart"
# are the ones that make this safe to read as a feeling: a state (broken, breaking, shattered,
# crushed, in pieces, in bits) is how a feeling is said, while a measure or an action is a body
# ("my resting heart rate", "my heart beats faster when i run", "my heart is racing") and stays
# as it was typed. Any number of measure words is stepped over, so "my heart is so so broken"
# reads the same as "my heart is broken", and the phrase is spelled out as the feeling word so
# every reader that already knows "heartbroken" answers it.
HEART_MEASURES = """so really very too pretty quite still just totally completely absolutely
    utterly properly well a bit a little kind of sort of that this""".split()
# The states a heart is in when the line is about how the person feels, each with the feeling word
# it is spelled out as: broken, breaking, shattered, crushed, torn and the phrases that mean it
# ("in pieces", "in bits", "in two"); a heart that sank or dropped is disappointment. A heavy or
# aching heart is left to the reader that already answers it, as its own advice is better than a
# rewrite. "broken open with joy" is left alone - that is
# the other meaning of a broken heart - and so is a third person's heart ("his heart is broken"),
# which the pattern below only ever reads for "my" and "me".
HEART_FEELINGS = (
    ("heartbroken", ("broken", "breaking", "shattered", "crushed", "torn", "broke", "snapped",
                     "in pieces", "in bits", "in two")),
    ("disappointed", ("sank", "sinking", "dropped")),
)
HEART_SAID_AS_A_FEELING = tuple(
    (re.compile(
        r"(?<![a-z0-9])(?:"
        # "my heart is broken", "me heart's so broken", "my heart was in bits", "my heart aches"
        r"(?:my|me)\s+heart(?:'s|s)?\s+(?:(?:is|was|feels|felt|looks)\s+)?(?:(?:%s)\s+)*"
        r"(?:%s)\b(?!\s+open)(?:\s+(?:in\s+(?:two|bits|pieces)|into\s+(?:a\s+million\s+)?pieces"
        r"|to\s+pieces))?"
        # "she broke my heart"
        r"|(?:[a-z']+\s+)?(?:broke|breaks|breaking|broken)\s+(?:my|me)\s+heart"
        r")" % ("|".join(re.escape(word) for word in HEART_MEASURES),
                "|".join(re.escape(word) for word in states))),
     " i am " + feeling + " ")
    for feeling, states in HEART_FEELINGS)


# The same grief said without the word "heart": "im broken hearted", "my world fell apart". Two
# words a keyboard splits, or the phrase people reach for when the feeling is bigger than one
# word, and both read as no feeling at all: "im broken hearted" was answered "Thanks for telling
# me - I'm here if you want to dig into any of that" and "my world fell apart" with the shrug. The
# phrases are spelled out as the feeling word, the same way a heart is, so the readers that know
# "heartbroken" and "sad" answer them. "broken hearted" needs the word boundary on both sides so
# "a broken hearted song" is read the same, and the world one is only ever the person's own.
SAID_AS_A_FEELING = (
    (re.compile(r"(?<![a-z0-9])broken[\s-]?hearted(?![a-z0-9])"), " heartbroken "),
    (re.compile(r"(?<![a-z0-9])broken[\s-]?heart(?![a-z0-9])"), " heartbroken "),
    (re.compile(r"(?<![a-z0-9])heart[\s-]?broken(?![a-z0-9])"), " heartbroken "),
    (re.compile(r"(?<![a-z0-9])(?:my|me)\s+(?:whole\s+)?(?:world|life)\s+"
                r"(?:fell|has\s+fallen|had\s+fallen|is\s+falling|came|came\s+crashing)\s+"
                r"(?:apart|down|crashing\s+down)(?![a-z0-9])"), " i am sad "),
    # The heart idioms that name dread rather than grief. "my heart is in my mouth" and "my heart
    # is in my boots" are both the fear before something, and neither one is a heart that has been
    # broken, so the readers that answer a heart answered them with the grief card or with the
    # shrug that says the line held no feeling at all. The feeling word is the one the line means:
    # nervous. "my heart is in my throat" is the same and is spelled the same way.
    (re.compile(r"(?<![a-z0-9])(?:(?:my|me)\s+)?heart(?:'s|s)?\s+"
                r"(?:(?:is|was|feels|felt)\s+)?in\s+(?:my|me)\s+"
                r"(?:mouth|boots|throat|stomach|shoes)(?![a-z0-9])"), " i am nervous "),
    # "im crushed", "i feel crushed" - said of the person, not "i crushed my finger"
    (re.compile(r"(?<![a-z0-9])(?:im|i\s+am|i\s+feel|i\s+felt|i\s+was)\s+"
                r"(?:so\s+|really\s+|totally\s+|completely\s+|utterly\s+|absolutely\s+)?"
                r"crushed(?![a-z0-9])(?!\s+by\b)"), " i am sad "),
)


# "what was it i said i was growing" is "what did i say i was growing" with the reaching-back
# `was it` in the middle of it, and no reader downstream could see through that: the memory store's
# recall readers are all written on the plainer spelling, so the ask went to whatever the verb in
# it named. "growing" is a knowledge topic (hair grows) and "painting" is another (emulsion), so a
# turn after the chat had been told about the tomatoes the person was given the hair card. The
# wrapper is folded into the ask it carries, so the reading every module gets is the one the plain
# spelling already gets. `clean` still holds the line as it was typed, which a reply quotes.
SAID_IT = re.compile(
    r"\bwhat (?:was|is) it (?:that )?(?P<who>i|we) (?:said|told you|mentioned)\b"
    r"|\bwhat (?:was|is) it (?:that )?(?P<saying>i|we) (?:was|were|am|are) (?:saying|telling you)\b")


def _the_ask_said_plainer(text):
    """`what was it i said about the oven` -> `what did i say about the oven`.

    The `saying` half keeps its tense and its word order, because "what was i saying about the
    car" is the ask the store already answers and "what i was saying about the car" is not.
    """
    return SAID_IT.sub(
        lambda one: (f"what did {one.group('who')} say" if one.group("who")
                     else f"what {'was' if one.group('saying') == 'i' else 'were'} "
                          f"{one.group('saying')} saying"), text)


_A_CLOSING_WORD = "|".join(sorted((re.escape(word) for word in ME_FOR_MY_CLOSES),
                                  key=len, reverse=True))
_A_HEAD_IN_THE_IDIOM = re.compile(r"(?<![a-z0-9])me head(?=\s+in(?![a-z0-9]))")
_A_CLIPPED_HEAD = re.compile(
    r"(?<![a-z0-9])(?:me|my) (?:ed|ead)(?!s?(?:[a-z0-9]))"
    r"(?=\s+(?:" + _A_CLOSING_WORD + r")(?![a-z0-9])|\s*$|\s*[,.;:!?])")


def _me_for_my_pass(text):
    """`me ed in` and `me head in` -> `my head in`, the two shapes `possessive_me` misses.

    The rest of the possessive "me" is that pass's job, with its own fences (a kin word after a
    verb, the owning verbs, the prepositions), so nothing here overrides it: "she told me mum
    died" and "give me car keys back" keep their "me" because this pass never sees them.
    """
    text = _A_HEAD_IN_THE_IDIOM.sub(" my head", text)
    return _A_CLIPPED_HEAD.sub(" my head", text)

def _phrase_pass(text):
    """Replace whole phrases ("cn u", "b/c", "okey dokey") before words are split."""
    text = _me_for_my_pass(text)
    for heart, feeling in HEART_SAID_AS_A_FEELING:
        if heart.search(text):
            text = heart.sub(feeling, text)
    for pattern, feeling in SAID_AS_A_FEELING:
        if pattern.search(text):
            text = pattern.sub(feeling, text)
    for phrase, value in PHRASES:
        pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            text = re.sub(pattern, " " + value + " ", text)
    text = UP_TOO_ASKS.sub(r"\1up to", text)
    text = _the_ask_said_plainer(text)
    return text


PUNCT_BREAK = re.compile(r"\s*[,;:!?]\s*")
# A full stop between sentences also ends a clause: "we got a puppy called sam. how long ...".
# One letter before the stop is an abbreviation ("e.g."), and a digit after it is a decimal.
SENTENCE_END = re.compile(r"(?<=[a-z0-9]{2})\.(?=\s|$)")
TOKEN = re.compile(_MEASURE + r"|\|")
THOUSANDS = re.compile(r"(\d),(?=\d\d\d\b)")
# A space where the comma would go is the same thousand: "£1 000", "1 200 a month", "£1 000 000".
# It is how a lot of people type a big number, and it was read as the number and then three digits
# left over beside it - "i have £1 000 saved" was answered as a budget of one pound, because the
# money rows read "£1" and stopped at "000". Only groups of exactly three digits join, and only
# when the number starts there, so a phone number ("07700 900 123") keeps its spaces.
THOUSANDS_SAID_WITH_A_SPACE = re.compile(r"(?<!\d)(?<!\d{4} )(\d{1,3})((?:[ \u00a0]\d{3})+)(?!\d)")

# A price typed with a sign is a price with a word in it - and the sign is not a word, so nothing
# after this point saw the money at all: "i have £20 until friday" arrived as "i have 20 until
# friday", the same line typed as "i have 20 pound until friday" was answered about money. The
# sign is written out as the noun people say, so every row that matches on a money word matches
# the figure whether it was typed with a sign or spelled out.
CURRENCY_SIGNS = {"\u00a3": "quid", "$": "dollars", "\u20ac": "euros"}
# The figure can be written the English way or the European one ("1,500.50" and "1.500,50"), and
# a short way with a multiplier ("£1.5k", "£2m"), so all three are read as one amount.
CURRENCY_SIGN = re.compile(r"([\u00a3$\u20ac])\s*(\d+(?:[.,]\d+)*)\s*([km])?(?![\w])", re.I)
CURRENCY_FACTOR = {"k": 1000, "m": 1000000}
# "20p" is money too, and it is deliberately left as typed. Writing it out as "20 pence" puts
# one more word in the line, and the plain line has to keep one word for each word that was
# typed: the readers that put a repaired word back in its place line the words up by position,
# and that one extra word turned "90p" into "90pence" in a line about the price of sugar, which
# then read as a blood sugar dropping and rang the hypo alarm. The typed "p" is what the money
# readers already fence on ("\\d+\\s*p\\b"), so nothing is lost by leaving it alone.


def _the_figure(figure):
    """The number a typed amount stands for: "1,500" is 1500 and "1,50" is 1.5."""
    if "," in figure and "." in figure:
        # Both marks: the one that comes last is the decimal point, the other counts thousands.
        decimal = "," if figure.rfind(",") > figure.rfind(".") else "."
        thousands = "." if decimal == "," else ","
        figure = figure.replace(thousands, "").replace(decimal, ".")
    elif "," in figure:
        # "1,500" is a thousand and five hundred, "1,50" is one and a half.
        figure = figure.replace(",", "") if len(figure.split(",")[-1]) == 3 else figure.replace(",", ".")
    value = float(figure)
    return ("%d" % value) if value == int(value) else ("%.2f" % value).rstrip("0")


def _a_sign_is_a_word(text):
    """A currency sign in front of a figure becomes the word for it: "£20" is "20 quid"."""
    def spelled(match):
        sign, figure, scale = match.group(1), match.group(2), (match.group(3) or "").lower()
        value = float(_the_figure(figure).replace(",", ""))
        if scale:
            value = value * CURRENCY_FACTOR[scale]
        written = ("%d" % value) if value == int(value) else ("%.2f" % value)
        return written + " " + CURRENCY_SIGNS[sign]

    return CURRENCY_SIGN.sub(spelled, text)




# A thing, or the far side of a sentence: "me back is ...", "me mum 4 xmas". A word on this
# list is never a thing "me" could own, so "me" in front of it is the pronoun.
NOT_A_THING = frozenset("""
a an the this that these those my your his her its our their some any no every each another
i you he she it we they me him us them who whom whose which what when where why how
is am are was were be been being do does did have has had can could will would shall should
may might must not so as than then too also either neither nor and or but if because
while whilst until till unless whether whenever wherever though although since whereas
in on at to for with from by about into over under after before between through during
up down out off away here there now later soon again still just only even ever never always
please thanks sorry ok okay
myself yourself himself herself itself ourselves yourselves themselves
thinks
""".split())

# What follows the thing "me" owns: a be-word or an auxiliary ("me back is bad"), a number
# ("me mum 4 xmas") or a word of saying ("me mate said"). A joiner is not enough: "owed me
# money and has not paid" and "called me yesterday and" are both the pronoun.
AFTER_A_THING = BE_WORDS | AUX_WORDS | REPORTING | frozenset(DIGIT_WORDS)

# What comes in front of a possessive "me": nothing at all, a joiner that opens the next thing
# said ("and me sister is coming"), or a preposition, which has no object of its own here ("with
# me sister", "on me own", "in me head"). A verb does not: "she gave me keys" and "bought me
# lunch" are the pronoun, so the verb has to be out of the way before "me" can be "my".
BEFORE_A_THING = frozenset("""
with for about of on in at from to over under into by off near round around behind
and but so then also plus because when if or though although since
wiv wid wif abt frm
""".split())

# A person the speaker has: "me mum", "me nan", "me sister". A verb in front of "me" makes
# it the pronoun ("she gave me keys", "bought me lunch"), but a person is not a thing done for
# somebody - nobody "rang me mum" means they rang me instead - so a kin word is the one thing
# "me" owns after a verb too. It is still the pronoun when the kin word has a verb of its own
# ("she told me mum died" told me that Mum died), which is what `after` is asking about.
# The prepositions that carry the British "me" for "my" ("with me sister", "on me phone", "for
# me tea"). After one of these "me" is far more often the object of the preposition than a
# possessive - "the shop near me", "come with me" - so the word after it has to be a thing before
# it is repaired, and a word that is doing something is not one.
BEFORE_A_PREPOSITION = frozenset("""
with for about of on in at from to over under into by off near round around behind
wiv wid wif abt frm
""".split())
# A thing never ends in these: "the bus near me stopped running" was "my stopped", because any
# word after a preposition was taken as a thing to own. A plural noun never ends in "ed" or
# "ing" uninflected, so the endings are safe to use - with two guards. The first is length: a
# short word ending in "-ed" is a thing ("in me bed" was "in me bed", and "in me shed", "in me
# red coat" too), because the verbs of that shape are longer. The second is the closed list
# below, since no length tells "ceiling" from "running".
NOT_A_THING_ENDING = ("ed", "ing")
LONG_ENOUGH_TO_BE_A_VERB = {"ed": 5, "ing": 6}
# What people own that ends in "-ing": a thing, not a verb doing something. Listed because a
# noun and a verb of this shape are one word, which is how this file handles the rest of them.
ING_THINGS = frozenset("""
ceiling ceilings landing landings building buildings bedding wedding weddings pudding
puddings dressing dressings shopping evening evenings morning mornings washing parking
meeting meetings ceiling fencing railing railings
""".split())
DOING_NOT_THING = frozenset("""
shut went goes gone came come left leaves broke broken breaks keeps kept got get gives gave
said says say told tells tell makes made takes took put puts ran runs run fell falls sees saw
seen knew knows know thought thinks think found finds feel feels felt closes close opens open
stops stop starts start works work sits sit""".split())


def _is_doing_something(word):
    """True when a word after a preposition is a verb, and so nothing "me" could own."""
    if word in DOING_NOT_THING:
        return True
    for ending in NOT_A_THING_ENDING:
        if word.endswith(ending) and len(word) >= LONG_ENOUGH_TO_BE_A_VERB[ending]:
            return word not in ING_THINGS
    return False


KIN = frozenset("""
mother mum mom mam mammy mummy father dad daddy son daughter sister brother wife husband
partner nan nana granny gran grandma grandad grandpa grandmother grandfather aunt auntie uncle
cousin niece nephew kid kids child children baby toddler boyfriend girlfriend fiance fiancee
""".split())

# Never a thing "me" could own either, when the line runs on: "up to me honestly", "for me
# please", "to me first". These say how or when, not what, so "me" in front of one is the
# pronoun. The far side of a joiner is here too: "you and me both", "you and me together",
# "him and me forever" are two people, not a thing "me" owns, and the thing before it is the
# partner "me" is named with.
NOT_A_THING_AFTER = NOT_A_THING | frozenset("""
first last next once twice today tonight tomorrow yesterday afterwards afternoons personally
anyway anyhow anymore anymore later sooner honestly really actually probably maybe usually
normally mostly nearly almost quite rather fairly simply clearly obviously certainly
definitely absolutely totally completely entirely exactly precisely again yet ever still
both too either neither together alike forever
alone sometimes earlier meanwhile eventually awhile anyway
""".split())

# A word of time is never a thing "me" can own, wherever it stands: "give it to me Tuesday" and
# "he came with me Monday" are the pronoun and a day, and "he works with me part time" says how
# the work is done. The day can come after the thing too:
#
# Where a thing is not: "wait for me outside", "come with me upstairs".
TIME_WORDS = frozenset("""
monday tuesday wednesday thursday friday saturday sunday
january february march april may june july august september october november december
morning afternoon evening night tonight tomorrow today yesterday midday noon midnight
week weekend weekday month year hour minute
""".split())
PLACE_WORDS = frozenset("""
outside inside indoors outdoors upstairs downstairs home ahead nearby nowhere somewhere
anywhere everywhere
""".split())
# How, not what, in two words: "he works with me part time", "i do it full time".
NOT_A_THING_PAIR = frozenset(("part time", "full time", "half time", "day time",
                               "night time", "real time", "spare time", "free time",
                               "every time"))


# A verb whose object is the thing and never a person it is done for: nobody loses, burns,
# drops or breaks something for you, so "i lost me keys" and "i burnt me toast" are "my".
# A verb that can be done for someone ("bought me lunch", "cut me a slice") is not here, and
# the determiner guard below keeps "i cut me a slice" out even if it were.
OWNING_VERBS = frozenset("""
lost lose losing dropped drop broke broken break cut burnt burned burn forgot forget forgotten
left spilled spilt ripped tore torn smashed chipped scratched hurt banged stubbed twisted
strained scraped find finding wash washing washed ironed ironing doing doin
""".split())

# A question that asks whose something is puts "me" where "my" belongs: "wheres me keys",
# "whats me password", "where is me passport". A question word in front of the thing leaves "me"
# no verb to be the object of, so the thing is what the speaker owns. A word that is doing
# something is not a thing here - "what is me supposed to do", "whats me doing" - so a verb form
# after "me" keeps the pronoun.
# `wher`, `whers` and `wer` are the same question with a letter missing: this pass runs before
# the word repair loop, so it has to hold the typed spellings itself or "whers me keys" keeps
# "me" as the pronoun.
ASKS_WHOSE = frozenset("where wheres what whats wher whers wer wers".split())


def possessive_me(tokens):
    """'me' used for 'my' in front of a thing: "me back is killing me", "me mum 4 xmas".

    British informal writing uses "me" where "my" belongs, and it is the difference between a
    line the bot can act on and one it cannot. Only taken when what follows the thing is a
    be-word, an auxiliary, a number or a word of saying, when "me" opens the phrase it is in
    (nothing in front of it, a joiner, or a preposition: "with me sister", "in me head"), or when
    a question asks whose it is ("wheres me keys"), so an object "me" ("tell me more", "help me
    plan", "gave me keys") is never touched. A kin word is the one exception to the verb: "he
    rang me mum" and "she told me dad" own their person.

    Public because the echo says a line back with the same repair (`bot.memory`'s you()), so
    "i dont get on with me sister" is never said back as "you ... with you sister".
    """
    out = []
    for index, token in enumerate(tokens):
        if token == "me" and index + 1 < len(tokens):
            thing = tokens[index + 1]
            after = tokens[index + 2] if index + 2 < len(tokens) else None
            before = tokens[index - 1] if index else None
            before_before = tokens[index - 2] if index >= 2 else None
            asks_whose = (before in ASKS_WHOSE
                          or (before in BE_WORDS and before_before in ASKS_WHOSE))
            owns_a_person = (thing in KIN
                             and (after is None or after in AFTER_A_THING
                                  or after in BEFORE_A_THING or after in TIME_WORDS
                                  or after in PLACE_WORDS))
            owns_the_thing = (after in AFTER_A_THING
                              or before in OWNING_VERBS
                              or owns_a_person
                              # A part of the body with the word of pain after it, where "me"
                              # opens the phrase: "me belly hurts", "me tummy aches", "me
                              # stomach is bad". A word of pain was not one of the words that
                              # follow a thing, so "me belly hurts" read as the pronoun and the
                              # line as an acknowledgement, while "me head hurts" (which the
                              # body list happened to carry a be-word saying for) was repaired.
                              # Where "me" is an object it is left alone: "it gives me stomach
                              # aches" opens on no joiner, so the thing is still the pronoun's.
                              or (after in lexicon.PAIN_WORDS
                                  and (before is None or before in BEFORE_A_THING))
                              or (asks_whose and thing not in NOT_A_THING_AFTER
                                  and not thing.endswith(("ly", "ing", "ed")))
                              or ((before is None or before in BEFORE_A_THING)
                                  and thing not in NOT_A_THING_AFTER
                                  and not thing.endswith("ly")
                                  # After a preposition the word has to be a thing: a word
                                  # doing something is the verb of its own clause, and "the
                                  # shop near me shut early" owns nothing.
                                  and not (before in BEFORE_A_PREPOSITION
                                           and _is_doing_something(thing))))
            # How or where, and not what: "with me part time", "wait for me outside",
            # "give it to me Tuesday". None of those is a thing, so none is "my". A person is
            # still the person: "he rang me mum yesterday" rang my mum, and the day is when.
            how_or_when = (thing in TIME_WORDS or thing in PLACE_WORDS or after in TIME_WORDS
                           or f"{thing} {after}" in NOT_A_THING_PAIR)
            if (owns_the_thing and thing.isalpha() and len(thing) > 2
                    and thing not in NOT_A_THING and (owns_a_person or not how_or_when)):
                out.append("my")
                continue
        out.append(token)
    return out


# What goes with the sun and never with a child: "my sun cream", "our sun lounger", "her sun
# hat". After one of these the word is the star, not a person.
SUN_WORDS = frozenset("""
bed beds cream creams lounger loungers tan tans burn burns burnt burned hat hats roof roofs
light lights shine shines shining shiny screen screens glasses lotion deck decks rise set
heat trap traps flower flowers dial lamp star stroke dried dry baked bathing baked
""".split())

# Who a sun can belong to: "my son", "our son", "their son". The star belongs to nobody, so a
# possessive in front of it is the one shape that says the person was meant.
OWNING_A_PERSON = frozenset("my our their your his her me".split())
# The second half of the test, and the half that carries it: after a possessive, a person is
# followed by a verb or a copula ("my sun has got a temperature", "my sun is being bullied", "my
# sun keeps waking"), while the star is followed by a noun that goes with it ("my sun allergy",
# "my sun damage", "my sun room", "my sun visor"). A list of star words can never be finished -
# "allergy", "damage" and "room" are all missing from it - but a verb list does not have to be:
# a word that is not a verb here leaves the line exactly as a spell-check would, so a gap costs a
# gain and never buys a wrong reading.
SON_VERBS = AUX_WORDS | frozenset("""
got gotten gets get keeps keep kept went goes gone came comes coming said says saying told tells
telling feels feel felt seems seem seemed looks look looked needs need needed wants want wanted
hates hate hated loves love loved likes like liked hurts hurt hurting cuts cut broke broken breaks
started starts woke wakes woken sleeps slept eats ate eating drinks drank drinking walks walked
talks talked cries cried crying swims swam swim wont cant doesnt didnt isnt wasnt hasnt havent
couldnt wouldnt shouldnt
""".split())


def a_son_not_the_sun(tokens):
    """'"my sun has got a temperature" is about a child, so after a possessive "sun" is "son".

    "sun" and "son" are one sound, and a parent typing about a poorly child writes the star:
    "my sun has got a tempreture of 39" found no person at all and came back as a shrug, where
    "my son has ..." answers it. The star belongs to nobody - it is "the sun" - so a possessive
    in front of it is the shape that says the person was meant.

    The test is on the word after it, twice over. The star's own words fence it off ("my sun
    cream", "our sun lounger", "her sun hat", "my sun burn"), and the person needs a verb or a
    copula there ("my sun allergy" is the star on a person's skin, "my sun has a temperature" is
    the person). The verb half is what keeps a noun nobody listed safe.
    """
    out = []
    for index, token in enumerate(tokens):
        if (token in ("sun", "suns") and index
                and tokens[index - 1] in OWNING_A_PERSON):
            after = tokens[index + 1] if index + 1 < len(tokens) else None
            if after not in SUN_WORDS and after in SON_VERBS:
                out.append("son" if token == "sun" else "sons")
                continue
        out.append(token)
    return out


# A person loses weight; a waistband, a tile and a screw are loose. The two are one sound in
# most English accents, so "loose weight" is what people type, and every reader that looks for
# the losing - the weight answer, the strength answer, the "how is it going" follow-up - was
# looking for a word the line did not have: "i need to loose weight" got a paragraph on squats
# where "i need to lose weight" gets the food answer, "loosing weight is hard" got "I'm
# listening", and "ive loosed 5 pounds" got "Got it."
#
# Only a weight word after it makes it the verb, and only in a short run of the words people put
# between ("loose some weight", "loose a bit of weight", "loose 5 pounds"): a loose handle, a
# loose tile, loose change and loose tea keep their own word, because none of them is followed by
# one of these.
LOOSE_FOR_LOSE = {"loose": "lose", "looses": "loses", "loosing": "losing", "loosed": "lost"}
THE_LOSING = frozenset("""weight pounds lb lbs kilos kilo kg kgs stones stone inches inch
    centimetres centimeters cm""".split())
BEFORE_THE_LOSING = frozenset("""some a an any that the this bit little more few of
    couple coupleof stone
    # "sum" is "some" with the o left out, and it stands where "some" stands: "i gotta loose sum
    # weight b4 the weddin" was "Got it. Is there anything you'd like a hand with?" because the
    # word between "loose" and "weight" was not one the reader knew, while "i gotta lose some
    # weight before the wedding" gets the weight answer.
    sum""".split())


# A word that is a real word, so the corrector leaves it alone by design, standing in the place
# of another one that is a letter away: "pan" for "pain", "hart" for "heart", "ware" for "wear",
# "desert" for "dessert", "live" for "leave", "saw" for "sore". The lexicon holds both words, so
# `fix_typo` refuses - "a confident wrong correction is worse than none" - and the line went to
# the readers with a word in it that names something else: "i have a pan in my chest" came back
# as "Noted: you have a pan in your chest", "my chest panes are bad" as "go easy on yourself",
# "i think im having a hart attack" as "Got it", "i think hes chocked" (a woman writing about a
# choking man) as "Got it", "what can i make for desert" as a list of dinners.
#
# The other word in the line is what says which of the two is meant, so every pair here carries
# the words that decide it, and a pair with none of them in the line is left as it was typed.
# Where the two words are both everyday things - a frying pan, a pane of glass, a saw - the
# body word has to be within three words of the slip, and the words for the object ("window",
# "oven", "frying") fence the pair off, so "two panes of glass" and "the pan in the back of the
# cupboard" keep their own word.
A_PART_THE_PAIN_IS_IN = frozenset("""chest stomach tummy throat ear ears tooth teeth jaw shoulder
    shoulders hip hips neck wrist ankle elbow heel knee knees ribs rib kidney kidneys groin
    armpit chests leg legs arm arms foot feet hand hands head""".split())
# The things a pane of glass is in, and the tools a pan is: none of them is a body, so a line
# about one is not a line about a pain.
A_GLASS_OR_A_PAN = frozenset("""window windows windscreen windscreens glass door doors
    frame frames greenhouse glazing mirror mirrors skylight skylights leaded stained shutter
    shutters cupboard drawer drawers kitchen oven hob handle handles lid lids frying roasting
    saucepan nonstick teflon wok tray freezer freezers""".split())
# A part that is only a body when somebody owns it: "in my back" is the ache, "the back of the
# cupboard" and "the side of the table" are not.
A_PART_A_PERSON_OWNS = frozenset("""back side head belly gut upper lower middle shoulder
    tummy chest arm arms leg legs foot feet hand hands""".split())
A_PAIN_WORD = {"pan": "pain", "pane": "pain", "panes": "pains"}
# A pan is kept and put away; a pain is not. "i keep my pan in my chest" is a pan with a place,
# so the verb in front of it says which word it is.
A_KEEPING_A_THING = frozenset("""keep keeps kept store stored stores storing hang hangs hung
    put puts putting stick stuck stash stashed""".split())
THE_HEART_SAID_THE_OTHER_WAY = frozenset("""attack attacks racing pounding murmur murmer murmurs
    failure bypass flutter flutters palpitations transplant stent pacemaker cardiologist
    valve valves arrest disease angina ecg""".split())
# Who a choke happens to, or what it happens on. A person or a thing eaten, and nothing else: a
# wheel is chocked, a boat is chocked on a trailer, and "on" on its own says neither ("the boat is
# chocked on the trailer" is a boat on a trailer, not somebody choking). "on" was a cue here and
# cost the everyday sense of the word, so the person or the food has to be there.
A_CHOKE_SAID_THE_OTHER_WAY = frozenset("""think he she hes shes im i we they baby son daughter child
    kid kids boy girl man woman dad mum someone somebody anyone anyone food blue bit sweet grape
    nearly started being""".split())
A_THING_WORN = frozenset("""wedding funerals funeral party interview dress dressed suit suits
    shoes shoe coat coats jeans jacket jackets gym tonight outside today work smart casual
    layers boots hat""".split())
A_STATE_YOU_CAN_FEEL = frozenset("""sick ill tired low anxious depressed dizzy faint better
    worse fine ok okay good great awful terrible rough rubbish angry sad happy nervous scared
    worried guilty lonely numb hot cold shaky weepy tearful emotional strange odd funny like
    sickly unwell pleased proud relieved""".split())
A_COPULA = frozenset("""am is are was were be been get got gets getting really very quite so
    still bit too pretty rather always""".split())
BEFORE_A_JOB = frozenset(("my", "the", "this", "a"))
A_JOB = frozenset("""job jobs work role position post company school course flat house city
    country marriage""".split())
# What follows the job when the line is leaving it: a time, or the end of the clause. "i live the
# country life" is a life and not a job, and the word after it is what tells them apart: "life"
# there, "in june"/"next month" or nothing in "i live my job in june" and "i want to live my
# job".
A_TIME_TO_LEAVE = frozenset("""in next on at by from after before tomorrow tonight soon then end
    month week year monday tuesday wednesday thursday friday saturday sunday january february
    march april may june july august september october november december""".split())


def _a_slip_that_is_a_word(tokens):
    """(tokens with the word meant in them, {as typed: the word meant}) for a line that has one.

    Only the pairs above, and only where the line says which word was meant: this is the curated
    route `fix_typo` leaves open for exactly this class, not a guesser.
    """
    lowered = [token.lower() for token in tokens]
    out = list(tokens)
    slips = {}
    for index, token in enumerate(lowered):
        right = None
        before = lowered[index - 1] if index else None
        after = lowered[index + 1] if index + 1 < len(lowered) else None
        after_that = lowered[index + 2] if index + 2 < len(lowered) else None
        if token in A_PAIN_WORD:
            # "i keep my pan in my chest" is a pan with a place, "i keep getting panes in my
            # chest" is the ache: the keeping verb has to be the verb of the slip itself, with
            # a determiner between it and the word.
            kept = (before in DETERMINERS and index > 1
                    and lowered[index - 2] in A_KEEPING_A_THING)
            # A pan dropped on a foot, or a pan that hit a head, is the thing and not the ache:
            # the slip has to stand in a pain frame. "pan in my chest" has the body after it;
            # "chest panes are bad" has the body before it and a state after. "dropped the pan
            # on my foot" has the body after "on", and "the pan hit my head" has a verb after,
            # so neither is the ache.
            after_body = False
            if after == "in":
                for place in range(index + 2, min(len(lowered), index + 5)):
                    part = lowered[place]
                    if part in A_PART_THE_PAIN_IS_IN:
                        after_body = True
                        break
                    if (part in A_PART_A_PERSON_OWNS
                            and lowered[place - 1] in OWNING_A_PERSON):
                        after_body = True
                        break
            before_body = (before in A_PART_THE_PAIN_IS_IN
                           or (before in A_PART_A_PERSON_OWNS and index > 1
                               and lowered[index - 2] in OWNING_A_PERSON))
            feels = after in A_STATE_YOU_CAN_FEEL or after in A_COPULA or after in (
                "hurt", "hurts", "ache", "aches", "aching", "kill", "killing",
                "throb", "throbbing")
            pain_frame = (before_body and feels) or after_body
            if (not kept and not any(word in A_GLASS_OR_A_PAN for word in lowered)
                    and pain_frame):
                right = A_PAIN_WORD[token]
        elif token == "hart" and any(word in THE_HEART_SAID_THE_OTHER_WAY
                                     for word in lowered):
            right = "heart"
        elif (token in ("chocked", "chockes")
              and after not in DETERMINERS
              and any(word in A_CHOKE_SAID_THE_OTHER_WAY for word in lowered)):
            # A determiner after it is a thing being chocked ("i chocked the wheel on the camper"),
            # which is the everyday sense of the word and not somebody choking.
            right = "choked" if token == "chocked" else "chokes"
        elif token in ("ware", "wared") and any(word in A_THING_WORN for word in lowered):
            right = "wear" if token == "ware" else "wore"
        elif token == "desert" and before == "for":
            # "what can i make for desert" is the pudding. A desert with "the" in front of it is
            # the sand ("i came back from the desert"), and one with no "for" is left alone.
            right = "dessert"
        elif (token == "live" and after in BEFORE_A_JOB and after_that in A_JOB
              and (lowered[index + 3:index + 4] or [None])[0] in
              (A_TIME_TO_LEAVE | {None, "|"})):
            right = "leave"
        elif (token == "saw" and before in A_COPULA
              and any(part in A_PART_THE_PAIN_IS_IN for part in lowered)):
            # "my legs are saw after the gym" is the ache, not the tool: a saw is named by a
            # person, never by a body that is a thing.
            right = "sore"
        elif token == "felling" and after in A_STATE_YOU_CAN_FEEL:
            right = "feeling"
        if right and right != token:
            out[index] = right
            slips[tokens[index]] = right
    return out, slips


def loose_is_lose(tokens):
    """'"i need to loose weight" is "lose weight": nobody is loose while putting on trousers."""
    out = []
    for index, token in enumerate(tokens):
        fixed = LOOSE_FOR_LOSE.get(token)
        if fixed:
            for step in (1, 2, 3, 4):
                after = tokens[index + step] if index + step < len(tokens) else None
                if after is None:
                    break
                if after in THE_LOSING:
                    out.append(fixed)
                    break
                if after not in BEFORE_THE_LOSING and not after.isdigit():
                    break
            else:
                out.append(token)
                continue
            if out and out[-1] == fixed:
                continue
        out.append(token)
    return out


# A digit that stands for the word people type it for. "2" and "4" are "to" and "for" in
# front of a word that begins a phrase (a determiner, a pronoun, a question word): a count is
# never written before one of those, so "2 the kids", "4 my mum", "2 u" and "2 my mother" have
# to be words, while "2 cats", "2kg" and "4 of them" stay numbers.
#
# A demonstrative is both ways, and what follows it decides. A period after it makes the digit
# a count of things done in that period ("i did 4 this week", "2 this morning", "4 this
# month"); without one the demonstrative is what the person is talking about and the digit is
# the word ("thx 4 that", "do it 4 that", "what can i do 4 this cough").
DIGIT_AS_WORD = {"2": "to", "4": "for"}
# "2" after a verb of going is "to", whatever place follows: a count cannot follow one, so
# "going 2 spain", "i went 2 benidorm" and "off 2 bed" are all "to". A period is the exception,
# because "going 2 weeks without a drink" counts them.
MOTION_BEFORE = frozenset("""go goes going went gone come comes coming came back off
    goin gona gonna""".split())
DEMONSTRATIVE = frozenset(("this", "that", "these", "those"))
A_PERIOD_FOLLOWS = frozenset("""time times week weeks weekend month months year years
    morning afternoon evening night term semester summer winter spring autumn day days
    hour hours minute minutes second seconds""".split())
A_WORD_CAN_FOLLOW = frozenset((
    "the", "a", "an", "my", "your", "his", "her", "our", "their",
    "you", "u", "ur", "it", "me", "us", "him", "them", "myself",
    "what", "how", "why", "where", "when", "who",
))

# "no" is also how people type "know". A subject in front of it and a pronoun, a question
# word, a determiner or the end of the clause after it make it the verb; every other "no" is
# the word no, which is what "i have no time", "no one" and "no thanks" need.
KNOW_SUBJECT = frozenset((
    "i", "u", "you", "we", "they", "he", "she", "anyone", "any1", "ne1",
    "someone", "some1", "everyone", "every1", "ppl", "people",
))
# The words people put in front of a "no" they mean as "know" without typing a subject in
# front of them: "i dont no how to tell them", "didnt no what to say", "dno where to start".
# One of these is already a whole verb and its "not", so the "no" behind it can only be the
# verb left over - there is nothing else in the clause for it to be. Every other "no" is the
# word no, which "there is no time", "i said no" and "no thanks" need.
NOT_BEFORE_KNOW = frozenset((
    "not", "dont", "don't", "didnt", "didn't", "doesnt", "doesn't", "dnt",
    "havent", "haven't", "havnt", "aint", "ain't", "never",
))
A_VERB_CAN_FOLLOW = frozenset((
    "you", "u", "ur", "it", "me", "us", "him", "them", "i", "we", "he", "she",
    "they", "what", "how", "why", "were", "wer",
    "where", "when", "who", "that", "the", "a", "an", "my", "your", "his", "her",
    "our", "their", "something", "anything", "nothing",
    # "i dont no yet", "dont no if i can make it", "dont no about that", "dont no much about
    # cars": the verb left over after a "no" that is a "know" takes the same words a verb
    # does, and none of these can follow the word no ("there is no yet", "no if") which is
    # what keeps "there aint no milk" and "aint no way" as they are.
    "yet", "if", "whether", "about", "for", "much", "many", "anyone", "anybody",
    "anymore", "either", "myself",
))


BE_FORMS = frozenset("am is are was were".split())
HAVE_FORMS = frozenset("have has had having".split())
MODAL_FORMS = frozenset("could would should must might may ought shall will can".split())


# A contraction written without its apostrophe is often a word in its own right, and only the
# word after it says which one the person meant: "were going to spain" is "we are", while
# "we were late" and "were you there" are what they look like. The reading takes the
# contraction only where the next word leaves no other way to read the line, so a line that
# already makes sense is never rewritten. Typed flat, "were going to spain in may" lost its
# subject: the plan in it was read as a statement about nothing, so the store never noted it
# and the line got the shrug.
#
# "ill" is the same shape ("ill call you later") and is deliberately left alone here: read as
# "i will" a plan stops being an illness, which is right, but a line in the middle of a health
# conversation that stops reading as health loses the topic the next line needs, and the cold
# answer it earned turned into a lecture. A real word that also stands for two words is only
# rewritten where the reply cannot come out worse.
LEFT_OFF_CONTRACTION = {
    "were": ("we", "are"),
}
# What a contraction can be followed by and the plain word cannot: a verb the line goes on
# with, or a word that can only sit after a helper ("were both knackered").
CONTRACTION_NEXT = BEFORE_VERB | frozenset("""
    be been being have had not never also just only still both already always definitely
    probably going off back home away
    having moving getting thinking trying staying doing seeing planning hoping
    let ring phone pop drop grab manage chase quit resign hire rent lock measure weigh need
    love like want miss mean mind aim assume bet guess hope wish promise remind stay sow weed
    mow dig sand tile grout seal glue screw drill hang level varnish log batch bottle
    """.split())


# People, and the words that stand for them, so a "bin" after one is the "been" it sounds like
# ("my mums bin in hospital", "hes bin at work") and a "bin" after anything else stays a bin
# ("the bin in the garden is full", "my bin in the kitchen smells").
PLURAL_SUBJECTS = frozenset("i you we they".split())
THIRD_PERSON = frozenset("he she it".split())

PERSON_WORDS = frozenset("""
    i you he she we they it mum mums mom moms mother mother's fathers dad dads father sister
    sisters brother brothers son sons daughter daughters wife husband partner mates mate
    friend friends boss kid kids baby gran nans nan grandad grandma granny aunt uncle cousin
    neighbour neighbor neighbour's colleague doctor nurse teacher cat cats dog dogs puppy
    puppies kitten kittens rabbit rabbits hamster budgie bird birds horse horses fish
""".split())
PERSON_PREPS = frozenset("in at on to out back away off home there round around up down".split())
# What follows the "been" a "bin" stands for: a verb with its -ing or -ed on, a participle that
# has no ending, or the state somebody has been in ("my cats bin sick", "its bin awful").
HOW_FOLLOWS = frozenset("""much many long far old often big deep quick soon fast come
    did do does can could would should is are was were about of to lot""".split())
BEEN_WORDS = frozenset("""sick ill unwell poorly bad awful great good alright quiet busy
    late away round back out down off twice""".split())
# The subjects a "bin" belongs to when nothing in front of it says so: "bin thinkin bout it",
# "cats bin sick". A determiner never gets here, so "the bin" and "my bin" stay bins.
BEEN_SUBJECT = frozenset("""i you we they he she it that thats its hes shes this these those
    there which what who everything nothing something""".split())
# The word in front of the thing that has "bin": "my phones bin actin up all wk", "our boiler bin
# leaking since tuesday". The thing is not one of the person-words above, so the person rule
# never sees those lines, and the word after the "bin" has to be a verb with its -ing on (or the
# state the thing has been in) - "my bin bags", "my bin is full", "my bin needs emptying" and
# "my bin men come friday" keep their bin.
THING_POSSESSIVES = frozenset("my our your his her their its".split())
# The g people drop off a verb in a hurry: "actin", "tryin", "leakin". A word ending in "in"
# is the verb unless it is one of the few nouns that end the same way, so those keep their word
# ("my cabin bin" is a bin in a cabin, and "my cousin bin" is not a cousin who has been).
IN_NOUNS = frozenset("""
cabin robin basin margin satin ruin twin grin coin pumpkin napkin muffin raisin resin
vitamin protein aspirin insulin cousin dolphin penguin violin mandolin origin virgin cabbage
""".split())
# A thing that is a bin is a bin whatever its -ing word looks like. "my kitchen bin smelling",
# "my compost bin overflowing", "my food bin attracting flies" are a container with a problem,
# and reading the container as a thing that has *been* handed the line to a damp-room answer
# ("find the source before you treat the air"). The words in front of the "bin" name the
# container, and the verbs after it are what a container does.
BIN_CONTAINERS = frozenset("""
kitchen compost food wheelie recycling waste rubbish trash dust garden nappy nappies sharps
bathroom pedal swing carrier paper
""".split())


def _the_thing_has_been(word):
    """Whether the word after a "bin" is what a thing that has been somewhere says next."""
    plain = _plain_chat(word) if word else ""
    if not plain:
        return False
    if plain in BEEN_WORDS or plain.endswith(("ing", "ed")):
        return True
    # The word `in` itself ends in "in", so "<possessive> <thing> bin in <place>" - "my green
    # bin in the corner", "my washing bin in the corner" - was read as a thing that has *been*
    # somewhere, and both lines lost their own answer. The bare word is not a dropped g.
    return plain != "in" and plain.endswith("in") and plain not in IN_NOUNS


def _is_person(word):
    """True when this token names the person a "bin" belongs to: "mums", "hes", "my dad"."""
    if not word:
        return False
    bare = word.replace("'", "").replace("\u2019", "")
    if bare in PERSON_WORDS or bare.rstrip("s") in PERSON_WORDS:
        return True
    plain = _plain_chat(word)
    if plain in PERSON_WORDS:
        return True
    spelled = (lexicon.CHAT.get(word) or lexicon.EXPAND.get(word) or "").split()
    return bool(spelled) and spelled[0] in PERSON_WORDS


def _plain_chat(word):
    """The first word a chat spelling stands for: "shud" -> "should", "ive" -> "i"."""
    if not word:
        return ""
    spelled = lexicon.CHAT.get(word) or lexicon.EXPAND.get(word) or word
    return spelled.split()[0]


def _spells_a_helper(word):
    """True when the token in front is a helper or a "to" once its chat spelling is undone.

    "b" is the quick way of writing "be" ("gona b late", "ill b there", "will b fine"), but it
    is a letter people also name ("plan b", "vitamin b", "b side"), so it only becomes a verb
    where a verb has to be: after a helper, a form of have or be, "to", or "not".
    """
    if not word or word == "|":
        return False
    spelled = (lexicon.CHAT.get(word) or lexicon.EXPAND.get(word) or word).split()
    if not spelled:
        return False
    last = spelled[-1]
    return (last in MODAL_FORMS or last in BE_FORMS or last in HAVE_FORMS
            or last in ("to", "not"))


def _is_be(word):
    """True when the token in front is a form of "be", chat spelling or contraction included."""
    if not word:
        return False
    if word in BE_FORMS:
        return True
    spelled = lexicon.CHAT.get(word) or lexicon.EXPAND.get(word)
    return bool(spelled) and spelled.split()[-1] in BE_FORMS


# The past participles a modal helper takes, so "could of gone" is repaired and "could of" on
# its own is not: a line that names the spelling it is asking about is a question about words.
IRREGULAR_PARTICIPLES = frozenset("""
    been gone done had seen said made taken given told known written eaten drunk spoken broken
    chosen driven fallen flown forgotten got gotten hidden held kept left lost met paid put read
    run come become begun brought bought caught fought found heard meant sent shown slept spent
    stood taught thought understood won worn
""".split())


def _is_participle(word):
    """Whether this word is the verb a modal helper's "of" is standing in for "have" before."""
    if not word or word in ("|",) or word == "or":
        return False
    plain = _plain_chat(word)
    if plain.endswith("ed") or plain in IRREGULAR_PARTICIPLES:
        return True
    return False


# "my mums got a chest infection", "my dads on his own", "my nans still not well": the
# possessive written without its apostrophe and the helper dropped with it. Read word by word the
# family word looks like a plural, so the line loses the person and an answer that needs one never
# comes. Only kin a person has one of: "my kids got chickenpox" and "my brothers coming over" are
# two people as often as one, and turning them singular would put the wrong person in the line.
KIN_SINGULAR = {
    "mums": "mum", "mams": "mam", "moms": "mom", "dads": "dad",
    "husbands": "husband", "wives": "wife", "partners": "partner",
    "nans": "nan", "grans": "gran", "grandmas": "grandma", "grandads": "grandad",
    "mothers": "mother", "fathers": "father",
    "boyfriends": "boyfriend", "girlfriends": "girlfriend",
}

# What a person is doing or is: the shapes that need a helper in front of them. "got" and "had"
# take "has"; everything else takes "is". A word that is not here is left alone, which keeps a
# real possessive out of it: "my mums car", "my mums pills" are things belonging to somebody.
KIN_HAS = frozenset("got had been gone".split())
KIN_IS = frozenset("""
    on in at off out away here back home due around
    pregnant engaged married divorced retired widowed ill sick poorly unwell upset fine ok okay
    worried tired late early better worse mad angry happy sad lonely dead alive well drunk hungover
    coming going staying moving working getting having being doing feeling expecting visiting
    arriving leaving starting recovering struggling coping waiting looking planning hoping trying
    applying retraining babysitting sitting standing living travelling traveling
    """.split())
# A short filler can sit between the person and what they are doing: "my dads just retired".
KIN_FILLERS = frozenset("just still always now already recently never not really very so quite"
                        .split())
# A word in "the person is doing ___" is the start of a verb phrase, not a thing the person owns.
# The -ing words in KIN_IS are nouns too, and "my mums living room" is a room: only a following
# word that can come after a verb earns the helper. Kept to the function words and the handful of
# adverbs that sit right after one, because a miss costs nothing (the line keeps what it typed)
# and a false positive puts "is" in the middle of a noun.
CAN_FOLLOW_A_VERB = frozenset("""
    a an the this that these those my his her their our your its
    in on at to from with about for of into onto over under up down out off back home
    away around round through across along behind past near
    me him her them us it you
    and but or so because when while if then than
    today tonight tomorrow now again soon later already still just always never ever not
    late early hard well badly properly slowly quickly together alone anymore
    fine ok okay alright better worse
""".split())


def _a_gerund_reads_as_a_verb(word, after_after):
    """True when "-ing" is what the person is doing rather than the first half of a noun.

    "my dads working late" and "my mums coming to stay" are verb phrases; "my mums living room is
    tiny", "my dads sitting room needs painting" and "my mums waiting list is long" are things
    that belong to them, and an "is" in front reads as nonsense.
    """
    if not isinstance(word, str) or not word.endswith("ing") or len(word) < 5:
        return True
    if after_after in (None, "", "|"):
        return True                             # "my mums cooking" - nothing after it
    return after_after in CAN_FOLLOW_A_VERB


def _kin_needs_a_helper(token, before, after, opens_the_clause, after_after=None):
    """The family word a dropped-apostrophe possessive stands for, with its helper.

    "my mums got a chest infection" is "my mum has got a chest infection", and "my dads on his
    own" is "my dad is on his own". Only where the possessive opens the clause or follows a
    leader ("and my dads on his own"), and only in front of a word that needs a helper, so a noun
    coming next keeps the possessive as it was typed ("my mums car").
    """
    if not opens_the_clause or before != "my":
        return None
    if token not in KIN_SINGULAR:
        return None
    if after in KIN_HAS:
        return [KIN_SINGULAR[token], "has"]
    if after in KIN_IS or after == "not" or (after or "").isdigit():
        if after in KIN_IS and not _a_gerund_reads_as_a_verb(after, after_after):
            return None                        # "my mums living room", "my dads sitting room"
        return [KIN_SINGULAR[token], "is"]      # "my mums not eating", "my mums 82"
    if after in KIN_FILLERS and (after_after in KIN_IS or after_after in KIN_HAS
                                 or after_after == "not"):
        return [KIN_SINGULAR[token],
                "has" if after_after in KIN_HAS else "is"]
    return None


# The family people clip to initials in a quick message, and the one they call their partner.
# Only after a possessive: "my mil", "her oh". A bare "oh" is the word people start a line with.
FAMILY_SHRT = {
    "mil": ("mother", "in", "law"), "fil": ("father", "in", "law"),
    "sil": ("sister", "in", "law"), "bil": ("brother", "in", "law"),
    "oh": ("other", "half"), "lo": ("little", "one"),
    "dd": ("daughter",), "ds": ("son",), "dh": ("husband",),
}
# Two of those initials are also a thing somebody owns, so the word after says which one it is:
# "my ds" is the console when it is broken, charging or a game ("my ds wont charge"), and "my
# dd" is a bra size or a due date when it is in front of a size or a month ("my dd bra", "my dd
# is june", "my dd is in june"). Those keep their letters: the mistake the other way is a
# partner's own possession read back as a member of the family, which is worse than a line left
# as it was typed.
SHRT_THINGS = {
    "ds": frozenset("""broken broke charging charge charger battery screen console game games
        lite dead working works""".split()),
    "dd": frozenset("""bra cup size in january february march april may june july august
        september october november december""".split()),
}
POSSESSIVES = frozenset("my your his her our their ur me mums dads sons daughters".split())


def _family_short(token, before, after, after_after):
    """The family word a clipped initial stands for, or None to keep the letters.

    "my oh", "her mil" and "my dh" are the partner and the in-laws, and the expansion is what
    lets every entry that keys on "husband" or "daughter" answer a line typed in a hurry: "my
    dd wont sleep" was read as the person not sleeping and answered "Annoying. Is it every
    time". Only after a possessive, and only for an initial that cannot be the thing of that
    name in the line ("my ds wont charge" is a console, "my dd is in june" a due date).
    """
    if token not in FAMILY_SHRT or not _is_possessive(before):
        return None
    things = SHRT_THINGS.get(token)
    if things and (after in things or after_after in things):
        return None
    return list(FAMILY_SHRT[token])


# A count of time after the "been" a "bin" stands for: "thats bin 3 wks", "its bin months".
PERIOD_COUNTS = frozenset("""week weeks month months year years hour hours minute minutes""".split())

# A unit clipped to its first letters, which is only the unit after a count: "4 yr old",
# "2 hrs sleep", "ten mins". It cannot be spelled out everywhere - "yr" is how people type
# "your" ("yr welcome") and "hr" is the department ("should i go to hr about my manager"),
# so the count in front is what makes the reading safe. The plural forms never mean anything
# else, so they are in the chat table; these are the ones that need the word in front.
CLIPPED_UNITS = {"yr": ("year", "years"), "hr": ("hour", "hours"),
                 "min": ("minute", "minutes"), "sec": ("second", "seconds")}
# A thing named by its first letters: "how do i bleed a rad", "the rad in my bedroom is cold".
# The full word is what the questions and the pools are written in, so a line read as "rad"
# names nothing and gets "I don't know enough to answer that honestly", while the radiator
# answer sits two words away. A clipped word is only the thing when it is used as one: a word
# about a thing after it ("my rads are noisy", "the rad is cold"), or a determiner in front of
# it at the end of the line ("bleed a rad"). "thats rad mate", "pretty rad" and "a rad new
# bike" are how somebody rates something, and they are left alone. "Mic" is not here: it is a
# microphone to almost everyone who types it, and the one line that wants the microwave
# ("how do i clean the mic") is not worth answering a call about a kitchen appliance.
CLIPPED_THINGS = {"rad": ("radiator", "radiators"), "rads": ("radiator", "radiators")}
# After the clipped thing: what people say about a thing that is not working.
THING_AFTER = frozenset("""is are was were wont wont keeps keep needs need broke broken leaking leaky
    cold hot noisy warm blocked bleed bleeding clean cleaning fix fixed valve valves
    died dies dead stopped stopping working works faulty glitchy tinny quiet sounds sound
    cuts cutting muted mute drops dropped plug plugged cable battery""".split())
# A joining word after it: "i tried to bleed the rad but no water came out", "the rad and the
# pipes". Only after a determiner, because "pretty rad but expensive" is how somebody rates a
# thing and the word after it is still the rating.
THING_JOIN = frozenset("and but so though although because when if then".split())
# "the rad in my bedroom is cold": a place is named after it, and the thing in front is a
# determiner ("thats rad in a way" is still a rating).
THING_PLACE_AFTER = frozenset("in on at".split())
THING_DETERMINER = frozenset("""a an the my our your his her their its both each every no any
    this these those""".split())
THING_PLACE_WORDS = frozenset("""a an the my our your his her their its this these those that""".split())
# In front of it, at the end of the line: "bleed a rad", "fix the leaky rad".
THING_SUBJECT = frozenset("""a an the my our your his her their its this these those both
    each every no any leaky leaking cold hot noisy warm blocked old spare""".split())
A_COUNT = frozenset("""one two three four five six seven eight nine ten eleven twelve
    thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty
    sixty ninety a an couple few several hundred thousand million""".split())


def _counts_a_period(word):
    """Whether this word is a length of time, so "thats bin 3 wks" is "that has been 3 weeks"."""
    return _plain_chat(word or "") in PERIOD_COUNTS


def _is_a_count(word):
    """Whether this word is how many, so the clipped unit after it is the unit."""
    plain = _plain_chat(word or "")
    return plain.isdigit() or plain in A_COUNT


# A period written short after one of these is one of them, not many: "nxt yr", "this yr",
# "last yr", "per yr". The word in front is what makes it safe, because on its own "yr" is how
# people type "your" ("yr welcome"), and "that" and "my" are left out for the same reason -
# "is that yr coat" is a coat, not a year.
A_PARTS_OF_A_PERIOD = frozenset("""next last this every each per past coming previous
    whole""".split())


# "hr" is a word of its own as well as an hour: the HR department, the HR team. A period word in
# front of it ("this hr", "past hr") is an hour when the line is about time and the department when
# the line is about work, and the word *after* the "hr" is what tells the two apart, so both have
# to be read together: "this hr department is useless" is not "this hour department".
HR_IS_THE_DEPARTMENT_AFTER = frozenset("""department departments team teams policy policies
    advice manager managers meeting meetings issue issues people rep reps email emailed staff
    director directors""".split())


def _hr_is_the_department(after):
    """True when the word after "hr" says it is the department and not an hour."""
    return _plain_chat(after or "") in HR_IS_THE_DEPARTMENT_AFTER


def _says_one(word):
    """Whether this word in front of a length of time makes it one: "next yr", "a 3 hr flight"."""
    plain = _plain_chat(word or "")
    return plain in ("1", "a", "an", "one") or plain in A_PARTS_OF_A_PERIOD


# A unit written in its short form and put in front of a noun is one word with it: "a 3 hr
# flight", "a 20 min walk", "a 10 sec clip". The writer typed the singular, and the noun after
# it says the unit is qualifying the noun rather than being the thing counted. Every other word
# after the unit leaves it the head of the count: "4 hr", "3 hrs at the clinic", "2 hrs sleep",
# "4 yr old".
NOT_BEFORE_A_NOUN = frozenset("""a an the my your his her our their its this that these
    of in at on to for from with per and or so but then than ago later old olds off out up
    down back over about around by as if sleep nap rest wait left more less most least
    now today tonight tomorrow yesterday""".split())


def _is_a_thing_here(before, after, after_after=None):
    """Whether the clipped word beside this one is the thing it stands for.

    "my rads are noisy" and "the rad is cold" say something about it; "bleed a rad" ends with it
    after a determiner. "thats rad mate", "pretty rad" and "a rad new bike" are how somebody
    rates something, so the word after them is not one of the things said about a thing.
    """
    # The word after has to be said about a thing as it was typed: "isnt" is read as "is" by the
    # rest of the reader, and "thats pretty rad isnt it" is a rating, not a radiator.
    said_after = (after or "").lower().strip("|")
    if said_after in THING_AFTER:
        return True
    if said_after in THING_JOIN:
        return _plain_chat(before or "") in THING_SUBJECT
    if said_after in THING_PLACE_AFTER:
        if _plain_chat(before or "") not in THING_DETERMINER:
            return False
        return (after_after or "").lower().strip("|") in THING_PLACE_WORDS
    return not said_after and _plain_chat(before or "") in THING_SUBJECT


def _clipped_thing(token):
    """The full word for a clipped thing, plural when the line says so."""
    one, many = CLIPPED_THINGS[token]
    return many if token.endswith("s") else one


def _is_before_a_noun(token, after):
    """Whether the clipped unit in front of this word is qualifying a noun: "a 3 hr flight"."""
    if token.endswith("s") or not after or after == "|":
        return False
    return _plain_chat(after) not in NOT_BEFORE_A_NOUN


def _is_said_of_a_person(word):
    """Whether this word is what somebody has been: a verb with its ending on, or a state.

    "my mums bin in hospital" is a "bin" that is the "been" it sounds like, and so is "my cats
    bin sick" and "bin thinkin bout it". A bare noun is not: "the bin day", "a bin lorry".
    """
    if not word or word in ("|",) or word in PERSON_PREPS:
        return False
    plain = _plain_chat(word)
    if len(plain) > 3 and (plain.endswith("ing") or plain.endswith("ed")
                           or plain.endswith("in")):
        return True
    return plain in IRREGULAR_PARTICIPLES or plain in BEEN_WORDS


def _is_possessive(word):
    """True when the token in front owns what comes next: "my", "her", "your mums"."""
    if not word:
        return False
    bare = word.replace("'", "").replace("\u2019", "")
    return bare in POSSESSIVES


# What can follow a feeling said about yourself: nothing, or where and when. A noun after it
# ("im board games") means the word was not a feeling.
# The words that may come after a feeling: a place or a time it holds for, so "im board work" is
# "i'm bored work(ing)". "the" is not one of them: "im board the train" is *on board the train* and
# "im tried the gym" is the past tense, so a "the" after the feeling turned both into feelings.
A_FEELING_CAN_BE_FOLLOWED = frozenset("""at in on with about of today tonight now again lately
    atm tbh so as all time work home stiff shit""".split())


# The words people put between "i am" and a feeling: "im so board", "im still board".
BEFORE_A_FEELING = frozenset("""so really very well still always constantly dead proper
    pretty totally completely""".split())


def _sounds_like_a_feeling(token, before, after, before_before=None):
    """The feeling this word sounds like, in the place a feeling goes, or None.

    "im board" is "i'm bored" and "im tried" is "i'm tired". Both words are ordinary ones, so
    nothing repairs them anywhere else; the position is what makes the reading safe.
    """
    if before in BEFORE_A_FEELING:
        before = before_before
    if before not in FIRST_PERSON_BE or token not in lexicon.SOUNDS_LIKE_A_FEELING:
        return None
    if after and after not in A_FEELING_CAN_BE_FOLLOWED:
        return None
    return lexicon.SOUNDS_LIKE_A_FEELING[token]


# How people write "ain't": the apostrophe is left out, put in, or typed as a stray one.
AINT_FORMS = frozenset(("aint", "ain't", "aint'", "a'int", "ai'nt", "aint,"))
# A subject that takes "has": "she aint been", "it aint done".
HAS_SUBJECT = THIRD_PERSON | frozenset("this that there everyone somebody someone nobody".split())
AINT_PLURAL = frozenset("you we they ye these those".split())
# The letters no English word ends in before a bare d, so a d after one is a left-off e.
MISSING_E_AFTER = frozenset("ktvpsmfgxzcjq")
# Past forms people leave as the participle in speech: "we aint spoke in a year", "he aint
# broke it". They only ever help choose the expansion of "ain't", so nothing else moves.
PAST_AS_PARTICIPLE = frozenset("""spoke broke woke drank wrote rang sang began swam took gave
    ate fell forgot stole drove rode wore chose froze ran came grew knew threw flew drew""".split())


# "hv" is the fastest way to write "have" ("i hv 2 kids", "hv u got a min"), and it is also
# what a parent calls the health visitor ("ring the hv about her sleep"). Where a verb has to
# be it is the verb: after the person or a helper ("i hv", "shld hv"), in front of the person
# of a question ("hv u", "how many hv u got") and in front of "to" ("hv to go"). After a
# determiner or a possessive the only thing it names is the person - "the hv", "my hv", and
# "ask the hv to weigh him" - and that is the reading the chat table gives it.
HV_SUBJECTS = frozenset("i we you they u ye".split())
HV_HELPERS = MODAL_FORMS | frozenset("to do does did not".split())
# The first person of "to be", the one place a bare stem is how somebody feels ("im annoy") or
# a feeling typed as another word ("im board"). Only the first person is here: "is"/"was" are
# how a thing is described ("the boiler is years old", "everybody was lovely"), where the same
# letters are the word they are.
FIRST_PERSON_BE = frozenset(("im", "i'm", "i’m", "am", "m"))
# How much of it there is sits between the two and changes nothing: "im still confus", "im so
# bore", "im really annoy", "im not confuse" are the same feeling as "im confuse". These are
# only the words that measure or temper a state, and they carry the same evidence for a word
# whose last letter came off: "im so nervou", "im really miserabl", "im well tire". A word that
# names anything keeps its own reading ("im in bore water" is not a feeling, and "im at bored"
# is not a shape of English).
AMOUNT_BEFORE_A_STATE = frozenset("""just only still so really very pretty quite too not never
    always often all sometimes ever constantly honestly actually kinda rather super totally
    completely proper propper dead well awful bloody terribly""".split())

# Where a state can stand: the first person be-form a feeling is said about, and the forms people
# type for it ("im", "i'm", "am", "i been", "i feel", "i feels"). Only first person, because
# "is" and "was" carry a thing as often as a state ("what is nappy rash"), and `_near_a_feeling`
# repairs a one-letter slip of a feeling only here, with any number of measure words between the
# two (`AMOUNT_BEFORE_A_STATE`), so "im knackerd", "im so exausted" and "im absolutely exausted"
# are repaired and a nappy is a nappy.
BE_BEFORE_A_STATE = frozenset("""im i'm i\u2019m m am i been being feel feels feeling feelin felt""".split())

# A state said about somebody else ("he is worrid about money", "she was knackerd") is repaired
# too, but only where a state can stand: at the end of the clause or in front of a word like
# "about". In front of anything else the word is part of a thing, not a state - "what is nappy
# rash" is a rash, and a nappy is a nappy - so the be-form on its own is not enough.
THIRD_PERSON_BE = frozenset("""is are was were r re hes he's shes she's its it's theyre they're
    youre you're ure we're seems seem looks look""".split())
# "to" typed for "too" is one of the measure words a state is said with ("im to exausted").
BARE_TO = frozenset(("to", "two", "2"))

# A determiner in front of a word says the line is naming a thing, not saying how somebody is.
# "the nappy" and "a nappy" are nappies, and the feeling repair made them "snappy", so a person
# who had said nothing about themselves was answered "I'm sorry - that's frustrating." "that"
# is deliberately not here - "im that knackered" is how people say "so knackered" - and neither
# is a phrase measure, so "a bit nackered" still reads as the state it is.
DETERMINER_IN_FRONT = frozenset("""
a an the every each no another this these those some any
my your his her its our their
""".split())

# The possessives among them are also how "me" arrives: the repair that turns "me sister" into
# "my sister" is done before this point, so "work left me exausted" reaches here as "work left my
# exausted" and the "my" is the person the state was done to, not a thing being named.
POSSESSIVE_IN_FRONT = frozenset("my your his her its our their".split())
AFTER_A_STATE = frozenset("""about of at with by for from since because and but so that today
    tonight now lately again too enough when as than in on to not all these days these days""".split())

# What a state said about somebody else may be followed by, over and above `AFTER_A_STATE`: the
# time it held for, and the word that says it did not pass. "she was exausted after work",
# "he was knackerd last week", "they were exausted already". These are the rest of the sentence,
# not a thing the state is part of, so the repair holds in front of them exactly as it holds in
# front of nothing at all. Kept apart from `AFTER_A_STATE` because that list also answers where a
# word that opens a line stands, and a line that opens on a state has no time word in front of it.
A_STATE_THEN_A_TIME = frozenset("""after before yesterday tomorrow already last earlier later
    soon still early late ever during while whenever yet until till whole every""".split())

# "were" at the front of a line is "we are" only in front of a word that says how you are or what
# you are doing: a state ("were shattered", "were gutted", "were broke this month"), an -ing verb
# ("were thinking of getting a cat", "were driving up to scotland") or a word that leads to one
# ("were so tired", "were all gutted", "were not happy"). The state words are spelled out here
# rather than taken from `lexicon.FEELINGS`, because that list is for a typo of a feeling and this
# is a closed list of what can follow "were" for "we are".
_WERE_STATE = frozenset("""gutted shattered exhausted knackered tired worried stressed anxious
    frightened scared annoyed angry furious upset sad unhappy miserable depressed lonely bored
    happy glad pleased proud relieved grateful shattered wiped drained bushed sleepy sick ill
    unwell poorly broke skint done fine ok okay stuck sorted lost ready low""".split())
# A word that can only be the start of "we are": nobody asks a question with these after "were".
_WERE_ARE = frozenset("gonna gunna".split())
# The -ing words that are what a person is doing rather than a thing: "were getting a cat",
# "were camping near oban". A thing that ends in -ing ("were wedding photos allowed", "were
# parking available") is not here, and keeps its "were".
_WERE_DOING = frozenset("""thinking having going coming driving flying travelling traveling
    staying doing getting making taking working playing visiting eating cooking watching
    planning trying looking waiting hoping wondering moving camping hiking jogging running
    walking cycling swimming skiing sailing fishing gardening studying revising rehearsing
    baking painting decorating renovating unpacking babysitting feeling jogging""".split())
# The list above is the doings people write most, and it is closed, so every other doing kept its
# "were" and the line was read as a question about a thing: "were selling the flat", "were
# adopting a dog", "were fighting a lot" and "were arguing all the time" were all answered "I
# don't know enough to answer that honestly. A search should sort you out." The word after the
# doing is what separates the two shapes. A doing takes a determiner, a particle or a preposition
# after it ("selling the flat", "breaking up", "arguing all the time", "struggling with money"),
# and a thing that merely ends in -ing takes a noun ("wedding photos", "morning people") or an
# adjective ("parking available"), and that is a question about the thing. So any doing the engine
# knows, with one of these after it, is "we are"; a noun or an adjective there keeps the "were".
_AFTER_A_DOING = frozenset("""a an the my your our their his her its this that these those some
    any no every each another all both just still quite really very too so not up out off away
    back over down around together apart through in on at to with for from about into onto by of
    and or but because while when if i you we they he she it me us them him there here""".split())

# The words that come between "were" and the state: "were so tired", "were all gutted", "were
# not happy", "were gonna be late". The word after one of these decides it.
# The prepositions that open a place or a state after "we are": "were in york", "were near
# bristol", "were at my mums", "were up in scotland", "were on the train". At the front of a
# clause there is no subject in front of the "were", so the past tense of the plural cannot be
# what was meant, and the only other reading - a question about a thing ("were dogs allowed",
# "were parking available") - needs a noun after it, not a preposition. These lines kept their
# "were" and reached the search hedge ("were in york" was answered "I don't know enough to
# answer that honestly. A search should sort you out quickly"), while the same line with the
# apostrophe was read: "we're in york" got the acknowledgement, "we're at my mums" was noted.
_WERE_PLACE = frozenset("in at near up down out over round around on inside outside".split())
# What says the past tense was meant after all: "were in york last week" is about a week that
# has gone, and reading it as "we are in york last week" is a line nobody says. A time word
# right after the preposition keeps the "were".
_WERE_IN_THE_PAST = frozenset("""last yesterday then earlier previously ago once before
    afterwards that those""".split())
# Who a lead-in word can stand in front of in a question: "were both of them there", "were
# all of us late". These keep the "were", because the question is about who was there.
_AFTER_A_LEAD_IN_SUBJECT = frozenset("""i you we they he she it them us him her me of""".split())
_WERE_LEAD_IN = frozenset("""so not too very really all both just still quite pretty always
    never literally definitely probably already almost nearly gonna gunna about""".split())
# The finite verbs a line starts with when it starts with "were" for "where": "were is my
# wallet", "were do i put it", "were have you been".
_A_QUESTION_VERB = frozenset("""is are was were am do does did can could would should will
    shall may might must has have had""".split())


def _were_for_another_word(before, after, after_after=None):
    """What "were" at the front of a line stands for, or None to keep it as it was typed.

    The front of a line is where a question puts "were" too, so the word after it decides which
    word was meant. In front of a finite verb it can only be "where" ("were is my wallet", "were
    do i put it", "were have you been"), because that word is the verb and not a subject. In
    front of a state or a doing it is "we are" with the apostrophe left off ("were shattered",
    "were thinking of getting a cat"), and a lead-in word is looked through for the same thing
    ("were so tired", "were all gutted", "were not happy"). Every other word keeps the "were" it
    was typed with, because a question about a thing is asked the same way: "were dogs allowed",
    "were parking available", "were the kids ok", "were you at the party".

    "Were" further into the line is the past tense of the plural ("they were late", "so were
    gutted") and is never touched: only the front of a line, or the front of a clause.
    """
    if before not in (None, "|"):
        return None
    if after in (None, "|"):
        return None
    if after in _A_QUESTION_VERB:
        return ["where"]
    if after in _WERE_STATE or after in _WERE_DOING or after in _WERE_ARE:
        return ["we", "are"]
    if after in _WERE_LEAD_IN:
        if after_after in _WERE_STATE or after_after in _WERE_DOING:
            return ["we", "are"]
        if after_after is not None and _a_doing(after_after):
            return ["we", "are"]
        if after_after in _AFTER_A_LEAD_IN_SUBJECT:
            # "were both of them there", "were all of us late": a lead-in word in front of
            # who was there is a question about them, and the plain contraction would read
            # "we are both of them there". The word is kept, which is what was typed.
            return ["were"]
        return None
    if _a_doing(after) and (after_after is None or after_after in _AFTER_A_DOING):
        return ["we", "are"]
    if after in _WERE_PLACE and after_after not in _WERE_IN_THE_PAST:
        return ["we", "are"]
    return None


def _a_doing(word):
    """Whether a word ending in -ing is a doing rather than a thing: "breaking", "selling".

    Only a word the engine knows is read this way, and the g may be left off the way people type
    it ("were goin out tonight"). What follows decides which of the two it is; this says only
    that the word itself could be the doing.
    """
    if not word:
        return False
    bare = word.replace("'", "")
    if bare.endswith("ing"):
        return bare in LEXICON or bare[:-3] in LEXICON
    if bare.endswith("in") and len(bare) >= 6:
        return bare in LEXICON or bare[:-2] in LEXICON
    return False


# "what you up to" typed as a number: the question people open a message with, and nothing else.
# The same letters also name a code, a password or a username ("the wifi code is wu2", "my mate
# text me wuu2"), so the word is read where the line opens with it and left as it was typed
# anywhere else - a code keeps its answer and the question still gets one.
UP_TO_SPELLINGS = frozenset("wuu2 wu2 wyu2 wuut".split())
# The openers people type for "what are you": "watcha up to", "whatcha doing", "wotcha been up
# to". No dictionary has any of them, and the word after says which ask it is - "up to", "doing"
# and "been" are the bot's own time, and "mean" ("whatcha mean") is not - so only those repair.
# Read as written they named no ask at all: "watcha up to" got the listening line and "whatcha
# doing today" was said back to the person as news.
WHAT_ARE_YOU_SPELLINGS = frozenset("watcha whatcha wotcha watchu whatchu watchya whatchya".split())
WHAT_ARE_YOU_AFTER = frozenset("up doing doin do been".split())
# The words that turn a typed "c" into "see": the person it is addressed to, and nothing else.
LETTER_C_IS_SEE = frozenset("u ya you yeah yah".split())
UP_TO_LEADS = frozenset("""so ok okay oh ah and but well just hi hey hiya hello right then now
    anyway""".split())
# What may follow the spelling and leave it the whole question: the words people put around it
# ("wuu2 mate", "wuu2 lol", "wuu2, you ok" - the comma starts another clause), and nothing else.
UP_TO_TAGS = frozenset("""mate hun love pet duck sunshine hen flower chuck dear pal buddy friend
    guys folks all both then though now lol haha ha x xo xx""".split())
# A question opener typed onto the word after it: "isit ok to eat this", "doyou think i should",
# "shouldi take it". People glue the two words when they type quickly, and the line then has no
# opener the reading knows, so it is read as a statement and answered with the stock "is there
# anything you'd like a hand with". The two lists are closed so a real word can never be split.
GLUED_LEFT = frozenset("is do does did can could would will should have are was were am "
                       "what whats where wheres when why how hows who whos".split())
GLUED_RIGHT = frozenset("it that this there they you i we he she your my "
                        "much long many the can should do does is are will would could did".split())
GLUED_COLLAPSE = {"itthere": ["there"]}
# A name typed lower case can wear a question opener as its first letters: "dodo" is a bird,
# "isis" is a cat and "didi" is a person. Two shapes give them away, and each is worth more than
# the lines it costs, because the split turns a piece of news into a question about nothing.
GLUED_DO = frozenset("do does did".split())
GLUED_AFTER_A_DO = frozenset("is are was were am will would can could should shall may might "
                             "must wont wouldnt cant couldnt shouldnt mustnt shant mightnt".split())


def _a_doubtful_split(pieces, after=None):
    """True when the words a glued token would be cut into are a name rather than a question.

    "dodo wont eat" is "do do wont eat" and "isis is my cat" is "is is is my cat": a question
    never says its first two words the same, so a split that does is a name. "didi is coming
    round" is "did i is coming round": no do-form is followed by a be-form or a modal, so the
    opener there is a name too. A pet or a person typed lower case keeps its line as the news
    it was.
    """
    if len(pieces) > 1 and pieces[0] == pieces[1]:
        return True
    return (pieces[0] in GLUED_DO and isinstance(after, str)
            and after in GLUED_AFTER_A_DO)


# "i" typed onto the word after it, which is the same slip the question openers have and costs
# more: every distress frame a person types starts with "i", and a glued one reads as no frame at
# all - "idont want to be here", "icant go on" and "iwant to die" were each "I'm listening - say
# more if it helps" while the spaced line got the crisis card. Only a word that can follow "i" is
# in the list, and a token already in the lexicon is never split, so "ill", "ive", "iron" and
# "island" keep their meaning.
I_GLUED = frozenset("""dont cant wont didnt doesnt havent havnt couldnt shouldnt wouldnt isnt
    wasnt want feel need know think hope wish hate love miss just also really always never got
    went have had will would should could might must am was did saw live work been told said
    tried lost quit moved found bought sold left met heard broke failed cried slept woke rang
    asked felt started stopped changed forgot paid spent took gave kept began ran walked drove
    ate drank won hired retired dumped applied booked cancelled emailed phoned texted replied
    agreed signed decided hated loved missed needed wanted hoped knew thought""".split())
# The same slip with somebody else in front of the word: "wedont have any money", "youdont
# understand", "shedoesnt ring back". A word that can follow "i" can follow these, so the table is
# the same one; only the pronoun is new.
# "it" is left out on purpose: "itisnt working" and "itdoesnt matter" are fragments a reader can do
# nothing with, and the split only made them shorter ("Fair enough" to "itisnt working"). The
# speaker's own pronouns are the ones that carry a frame.
# "u" is the chat form of "you" and it is typed onto the word beside it the same way: "udont
# understand", "ucant come", "uknow what i mean". Only a token that is not a word of its own is
# looked at and the rest of it has to be a word that follows "i", so "under", "until", "usual"
# and "upset" keep their meaning.
A_PRONOUN_GLUED = ("u", "i", "we", "you", "they", "he", "she")

# The two halves of "i am" said as one word, typed onto the word after them: "imso tired",
# "imstill awake", "imdone with today", "ivegiven up". The pronoun table above reads "i" plus a
# verb, and "im" is not a pronoun, so the whole token stayed as it was: "imdone with today" was
# answered "Noted: imdone with today." - the line read back with a word no one writes - and
# "imstill awake" lost the advice "i am still awake" gets. Only the words a person really types
# after "im" and "ive" are listed, so "image", "impact", "import", "imogen" and "ivory" stay
# whole words.
A_PRONOUN_STATE = {
    "im": frozenset("""not so sorry still done going glad happy sad fine ok okay afraid worried
        tired starving hungry thirsty freezing boiling home back here sure just really trying
        working off out up sick lost confused angry upset lonely scared nervous bored at on in
        sitting lying waiting
        struggling stressed fed exhausted overwhelmed anxious depressed panicking hopeless
        worthless gutted furious annoyed irritated shattered unwell ill hurt aching shaky dizzy
        sleepless restless moody numb broke skint stuck busy late""".split()),
    "ive": frozenset("""given got been had never just tried lost done seen told said finished
        started stopped found made taken read heard watched eaten bought moved left paid spent
        decided noticed asked called checked waited worked lived known thought wanted needed
        felt learned kept written broken forgotten
        only already finally recently lately quit joined applied booked sent posted texted
        emailed ordered become grown gained""".split()),
}


_PLACES_SAID_WHOLE = [None]


def _a_place_said_whole(bare):
    """True when the whole token is a place the bot knows, so it is not a pronoun and a verb.

    "iran is in the news" is a country, and only by accident "i" + "ran"; the same is true of any
    country whose name happens to start with a pronoun. The list is the bot's own, so a verb added
    to `I_GLUED` later cannot take a country with it, and a name from `COMMON_NAMES` is refused the
    same way.
    """
    if bare in lexicon.COMMON_NAMES:
        return True
    places = _PLACES_SAID_WHOLE[0]
    if places is None:
        try:
            from bot.knowledge.geography import COUNTRIES
            places = frozenset(COUNTRIES)
        except Exception:
            places = frozenset()
        _PLACES_SAID_WHOLE[0] = places
    return bare in places


def _a_pronoun_said_together(token):
    """The pronoun and the word it is typed onto, or None.

    The apostrophe is kept, because that is how the person typed it and the readers already know
    "can't" and "don't": "ican't go on" is "i can't go on", which is the crisis line, while the
    glued token was no line at all.
    """
    bare = token.replace("'", "").replace("\u2019", "")
    if _a_place_said_whole(bare):
        return None
    for who, after in A_PRONOUN_STATE.items():
        if bare.startswith(who) and bare[len(who):] in after:
            return [who, bare[len(who):]]         # "imso", "imdone", "ivegiven"
    for who in A_PRONOUN_GLUED:
        if bare.startswith(who) and len(bare) > len(who) and bare[len(who):] in I_GLUED:
            return [who, token[len(who):]
                    if token.startswith(who) else bare[len(who):]]
    return None


def _a_state_typed_onto_im(token):
    """The state typed onto the "im", or None: "imsad" is "im sad", "imexhausted" is tired.

    The token has to be one no reader knows (the guard in `_glued_words`), so "image", "impact",
    "import", "improve", "imagine" and "immune" keep their meaning: each of them is a word. What
    is left over after the "im" has to be a state the reading already knows, which is why
    "improv" and "impressed" are left alone here and read elsewhere.
    """
    if len(token) < 4 or not token.startswith("im") or not token.islower():
        return None
    rest = token[2:]
    if rest in lexicon.STATES_SAID_ONTO_IM:
        return ["im", rest]
    return None


def _glued_words(token, after=None):
    """The two words a glued opener stands for, or None when the token is a word of its own.

    Only a token that is not in the lexicon at all is a candidate, which is what keeps "island",
    "issue", "washer", "dinner" and "cannon" whole: each of them is already a word, and a word
    keeps its meaning. The split is tried left to right by the length of the opener, so the
    longest opener that fits wins ("doesit" before "do" + "seit"). `after` is the next word of
    the line, which is what tells a name's split from a question's (_a_doubtful_split).
    """
    if len(token) < 4 or token in LEXICON or not token.islower():
        return None
    said_together = _a_pronoun_said_together(token)
    if said_together:
        return said_together                      # "idont", "icant", "ican't", "wedont"
    a_state = _a_state_typed_onto_im(token)
    if a_state:
        return a_state                            # "imsad", "imlonely", "imsuicidal"
    half, odd = divmod(len(token), 2)
    if not odd and token[:half] == token[half:]:
        # A name is often one half written twice ("didi", "dodo", "coco", "isis", "nana"), and no
        # question opener is: "didi from work rang" is news whatever word follows it, which the
        # be-form fence alone cannot tell, because a friend is followed by "from", "said" or
        # "and" at least as often as by "is".
        return None
    for cut in (6, 5, 4, 3, 2):
        if token[:cut] not in GLUED_LEFT:
            continue
        rest = token[cut:]
        if rest in GLUED_RIGHT:
            pieces = [token[:cut], rest]
            return None if _a_doubtful_split(pieces, after) else pieces
        if rest in GLUED_COLLAPSE:
            # "isitthere anything i can do" is "is there anything i can do": the `it` is a slip
            # and reading all three words keeps a word the line does not need.
            return [token[:cut]] + GLUED_COLLAPSE[rest]
        for second in (5, 4, 3, 2):
            # "isitthere" is three words, not two, and it is still one question.
            if rest[:second] in GLUED_RIGHT and rest[second:] in GLUED_RIGHT:
                pieces = [token[:cut], rest[:second], rest[second:]]
                return None if _a_doubtful_split(pieces, after) else pieces
    return None


# "the mrs" is the wife. It is how half the country says it, and the word on its own is a
# title, so it cannot go in the chat table with "missus": "Mrs Smith next door" is a neighbour
# and turning that into "wife Smith" would lose a name. The frame decides it - "the mrs", "my
# mrs", "our mrs" is a wife, and a mrs with a capital word after it is a title. The chat table
# already reads "missus" as "wife", so "me and the missus are arguing about money" reached the
# money-between-partners card while "me and the mrs are arguing about money" got "Sorry to hear
# that. What would help most right now?" - one word apart.
MRS_IS_THE_WIFE = re.compile(r"\b(the|my|our|his|her)\s+([Mm]rs)\b\.?(?!\s+[A-Z])")


def _the_mrs_is_the_wife(text):
    """A wife said as "the mrs", left alone where "mrs" is a title in front of a name."""
    return MRS_IS_THE_WIFE.sub(r"\1 wife", text)

# The words a person can already have written in front of an abbreviation that carries its own
# subject: "i dunno" is "i" and "i do not know", and the line would read "i i do not know".
_SUBJECT_SAID = frozenset(("i", "we", "you", "they", "he", "she", "it", "people", "folk",
                           "u", "ya", "yous", "everyone", "everybody", "somebody", "nobody"))


def _chat_words_said_out(clean):
    """A chat word spelled out in the line the readers match on.

    "i dont know what i wanna do" is the same statement as "i dont know what i want to do", and
    the readers that answer it are written on the words the person meant. The reading already
    spells these out (`norm`), but a reader matching on `clean` - the line as it was typed -
    never met the phrase, so the same line typed two ways got two different replies. Only the
    words in `lexicon.PLAIN_EXPANDS` are spelled out: a word that is not a word at all, whose
    repair is the phrase a reader is looking for. A contraction stays as it was typed ("dont" is
    how people write "do not", and the patterns are written on it), and so does a word whose
    spelling is somebody's name.
    """
    if not clean:
        return clean
    out = []
    for word in clean.split():
        spelled = SAID_OUT.get(word)
        # An abbreviation can carry its own subject: "dunno" is "i do not know", and after the
        # person has already written "i" the line would read "i i do not know what to do".
        before = SAID_OUT.get(out[-1].lower(), out[-1].lower()).split() if out else []
        if spelled and before and before[-1] in _SUBJECT_SAID and spelled.startswith(("i ", "I ")):
            spelled = spelled.split(" ", 1)[1]
        out.append(spelled or word)
    return " ".join(out)


# A hello typed as its initials or with the tail of the word bitten off: "gm", "gm all",
# "gmorning", "mornin", "evenin", "gday", "top of the morning". None of these is a word the
# reading knows, so no reader saw a hello in it at all: "gm" and "gm all" - the shape a group
# chat uses every morning - were answered with the flat "Thanks for telling me - I'm here if you
# want to dig into any of that", and so was "mornin". They are put back into the words people
# mean, so the greeting kind and the morning pool can see them.
#
# Only at the front of the line: "gm" is how a cook writes a gram, so "200 gm of butter" and
# "500gm flour" keep their weight. A hello with something after it is filler, like "hi" or "oh":
# "gm, boiler is leaking" is read as "boiler is leaking", because the words of the hello are not
# words the boiler answer matches and putting them in the line would bend what it says.
HELLO_SAID_SHORT = (
    ("top of the morning", "good morning"),
    ("g morning", "good morning"),
    ("gmorning", "good morning"),
    ("g'morning", "good morning"),
    ("gm", "good morning"),
    ("gday", "good day"),
    ("g'day", "good day"),
    ("mornin'", "morning"),
    ("mornin", "morning"),
    ("evenin'", "evening"),
    ("evenin", "evening"),
)
# The words a hello is said to: "gm all", "mornin everyone", "top of the morning to you". They go
# when the hello is taken off the front, or the line left is "all, any tips for a cold".
HELLO_TAIL = frozenset("all everyone everybody guys folks friends there you mate to".split())


def _a_hello_said_short(clean):
    """The line with a hello typed as initials, or with its tail bitten off, read as a hello."""
    if not clean:
        return clean
    for typed, meant in HELLO_SAID_SHORT:
        if clean == typed:
            return meant
        if not (clean.startswith(typed + " ") or clean.startswith(typed + ",")
                or clean.startswith(typed + "!")):
            continue
        words = clean[len(typed):].strip(" ,!.").split()
        while words and words[0].strip(",.!") in HELLO_TAIL:
            words.pop(0)
        rest = " ".join(words).strip(" ,!.")
        return rest or meant
    return clean


def _glued_said_apart(clean):
    """The line with every glued question opener put back into the words it stands for.

    A shortened opener is spelled out on the way: "whatsthe best way" is "what is the best way",
    not "whats the best way", because the modules read the words of the line and "whats" means
    nothing to them, while "what is" is the same two words the spaced line carries.
    """
    out = []
    words = clean.split()
    for index, token in enumerate(words):
        pieces = _glued_words(token, words[index + 1] if index + 1 < len(words) else None)
        if pieces:
            spread = lexicon.CHAT.get(pieces[0])
            if spread and " " in spread:
                pieces = spread.split() + pieces[1:]
        out.extend(pieces if pieces else [token])
    return " ".join(out)


# A whole line, or a whole sentence of it, typed with the spaces left out: "whatshouldido",
# "howdoicookrice", "mysonisill", "imsotired", "cantgetoutofbed". A phone keyboard's swipe gives
# a run like this and so does a hurried thumb, and every one of them was answered with the stock
# "Got it. Is there anything you'd like a hand with?", because no word in the run is a word the
# reading knows. "isit ok to eat this" is the same fault with one opener in front, and
# `_glued_words` above puts that right; this is the same idea for a run of three words or ten.
#
# Two things keep a real word whole. A run is only split when it opens the way a line opens - on
# a question word, on the speaker ("i", "im", "idk") or on a possessive ("my", "our") - and the
# words it is split into are words of the lexicon, so a run only ever becomes words somebody
# typed: "document" is not "do cu meant" and "whatsapp" is not "what is app", because "cu" and
# "sapp" are not words. "cupcakes", "toothache", "pushchair", "houseplant", "lunchtime",
# "behaviour", "fortnight", "bearings", "hibernate" and "presentation" open on nothing a line
# opens on, so none of them is touched at all.
RUN_ON_OPENERS = frozenset("what how why when where who which whats hows wheres whos "
                           "nothing nobody everything everyone something someone "
                           "can cant could couldnt should shouldnt would wouldnt will wont "
                           "do dont does doesnt did didnt is are was were shall".split())
RUN_ON_SELF = frozenset("i im ive id ill idk idunno cant dont didnt doesnt wont isnt arent".split())
RUN_ON_MINE = frozenset("my your his her our their".split())
# The words a run is split into: the lexicon alone, so a split is words of English and never a
# piece of a longer word ("cu", "sapp", "cument"), plus the two single letters a line has and the
# spellings people type for them ("im", "cant", "dont") which are only the words with a letter
# dropped. A run says who it is about - "what should i do", "my back hurts", "can you help me",
# "nothing is working" - so one of the pieces has to be a word for a person or a thing.
RUN_ON_WORDS = LEXICON | frozenset("""a i im ive id ill idk idunno dunno cant dont didnt
    doesnt wont isnt arent wasnt werent wouldnt couldnt shouldnt""".split())
RUN_ON_PEOPLE = frozenset("""i im ive id ill me my we us our you your he him his she her it its
    they them their there this that these those nothing nobody everything everyone something
    someone anyone no one""".split())
# How long a run has to be to be read as a clause rather than as a word. "myanmar" is "my an
# mar" to a split, and "my" is a word people open a line on, so a run of seven letters is left
# alone; "mymumisill" and "mybackhurts" are ten and eleven and are read.
RUN_ON_SELF_LONGEST = 9
# A run is split into two words or more, and the shortest a run can be is eight letters: "island",
# "insure", "inherit" and "instead" all open on "is" or "in" and are six or seven letters, so a
# shorter run is read as one word and left alone.
RUN_ON_SHORTEST = 8
# A run that ends on one of these is a word that begins with an opener: "whatever", "whenever",
# "whoever", "however" and "wherever" are one word each, and "how" and "ever" are not two.
RUN_ON_LAST_PIECES = frozenset("ever ether soever".split())


def _said_run_on(token):
    """The words a line typed without spaces is made of, or None when the token is not one."""
    if not token.isalpha():
        return None
    token = token.lower()
    if len(token) < RUN_ON_SHORTEST:
        return None
    if token in LEXICON:
        return None
    best = {0: ()}
    for start in range(len(token)):
        pieces = best.get(start)
        if pieces is None:
            continue
        for end in range(len(token), start, -1):
            piece = token[start:end]
            if piece not in RUN_ON_WORDS:
                continue
            here = pieces + (piece,)
            there = best.get(end)
            if there is None or len(here) < len(there):
                best[end] = here
    split = best.get(len(token))
    if not split or len(split) < 2:
        return None
    if split[-1] in RUN_ON_LAST_PIECES:
        return None
    if sum(1 for piece in split if len(piece) == 1) > 1:
        return None
    if split[0] in RUN_ON_SELF or split[0] in RUN_ON_MINE:
        if len(token) < RUN_ON_SELF_LONGEST or len(split) < 3:
            return None
        return list(split)
    if split[0] in RUN_ON_OPENERS:
        if not any(piece in RUN_ON_PEOPLE for piece in split):
            return None
        return list(split)
    return None


def _a_run_and_what_surrounds_it(token):
    """A token as (what comes before the letters, the letters, what comes after them).

    The letters of a run are the letters wherever a phone put a capital or a person put a
    question mark: "WhatShouldIDo" and "whatshouldido?" are the same five words as
    "whatshouldido", and all three were answered with a line that says nothing.
    """
    start = 0
    while start < len(token) and not token[start].isalpha():
        start += 1
    end = len(token)
    while end > start and not token[end - 1].isalpha():
        end -= 1
    return token[:start], token[start:end], token[end:]


def _typed_without_spaces(clean):
    """The line with any run of words typed as one long word put back into its words."""
    out = []
    for token in clean.split():
        before, letters, after = _a_run_and_what_surrounds_it(token)
        pieces = _said_run_on(letters)
        if pieces:
            spread = lexicon.CHAT.get(pieces[0])
            if spread and " " in spread:
                pieces = spread.split() + pieces[1:]
            out.extend(pieces)
            if after:
                out[-1] = out[-1] + after
            if before:
                out[0] = before + out[0]
        else:
            out.append(token)
    return " ".join(out)


# A contraction typed with a space where its apostrophe belongs: "i m 34", "i ve got a cat",
# "i ll do it tomorrow", "we re going", "i don t know", "can t breathe", "they d love it".
# The apostrophe is the only mark that was left out, so the two pieces are one word and every
# reader below is looking for that one word: on main "i m 34" kept no age, "i ve got a cat" was
# read as a line with a bare "m" and "ve" in it, "i ll do it tomorrow" was echoed back as "you ll
# do it tomorrow", and "i don t know" was the shrug every reader gives a line it cannot parse.
# The pairs are not written out by hand, because the engine already knows both spellings: the
# apostrophe-free ones are the contraction table, and the apostrophe ones are a pronoun and its
# tail. The one-letter rule is what makes a space-split contraction: something like "we re" is
# the contraction because no line puts a bare "re" after "we" for any other reason, and "so me"
# is left alone because neither piece is a letter on its own.
APOSTROPHE_TAILS = frozenset("m re ve ll d s".split())
# What a tail can follow. "this" and "one" are left out: "one s" and "this s" say nothing as
# contractions, and the possessive "one's" is not the "one is" the engine would read.
APOSTROPHE_BASES = frozenset("""i you we they he she it that there here what who where when
    why how let everyone everybody someone somebody nobody""".split())
# "i s" is left out: nobody writes "i's" for "i is", so a bare "s" after "i" is a letter, not
# a contraction.
APOSTROPHE_NOT = frozenset([("i", "s")])


def _the_said_apart_forms():
    """({pieces: the word}, one pattern) for the contractions that can be typed as two words.

    Every way of splitting the known contraction spellings into two or three pieces, kept only
    where one piece is a single letter, so the pattern can never claim two ordinary words.
    """
    forms = {}
    for joined in tuple(lexicon.EXPAND) + tuple(lexicon.TYPED_CONTRACTIONS):
        if not joined.isalpha() or not 2 <= len(joined) <= 10:
            continue
        for pieces in _the_ways_a_word_is_typed_apart(joined):
            forms.setdefault(pieces, joined)
    for base in APOSTROPHE_BASES:
        for tail in APOSTROPHE_TAILS:
            if (base, tail) in APOSTROPHE_NOT:
                continue
            one = base + "'" + tail
            if _apostrophe(one):
                forms.setdefault((base, tail), one)
    return forms


def _the_ways_a_word_is_typed_apart(joined):
    """The ways this one word arrives as two or three tokens: "dont" is "don t" or "d ont"."""
    ways = []
    for cut in range(1, len(joined)):
        first, rest = joined[:cut], joined[cut:]
        if len(first) == 1 or len(rest) == 1:
            ways.append((first, rest))
    for first_cut in range(1, len(joined) - 1):
        for second_cut in range(first_cut + 1, len(joined)):
            pieces = (joined[:first_cut], joined[first_cut:second_cut], joined[second_cut:])
            if 1 in (len(piece) for piece in pieces):
                ways.append(pieces)
    return ways


SAID_APART_FORMS = _the_said_apart_forms()
SAID_APART = re.compile(
    r"(?<![a-z])(?:%s)(?![a-z])" % "|".join(
        r"\s+".join(pieces) for pieces in sorted(SAID_APART_FORMS,
                                                  key=lambda pieces: -sum(len(p) for p in pieces))))


# A determiner in front of a bare letter is a name or a badge, not a contraction: "my i d is in
# my bag" is an identity card, and joining it into "my i'd" answers a line about paperwork with a
# line about what somebody would do.
A_LETTER_AFTER = frozenset("""my your his her their our the a an this that these those no any
    every each another some""".split())


def _said_apart(tokens):
    """The contractions typed with a space in place of the apostrophe, put back together."""
    if len(tokens) < 2:
        return tokens
    said = " ".join(tokens)
    if not SAID_APART.search(said):
        return tokens

    def put_together(match):
        before = said[:match.start()].split()
        if before and before[-1] in A_LETTER_AFTER:
            return match.group(0)
        return SAID_APART_FORMS[tuple(match.group(0).split())]

    return SAID_APART.sub(put_together, said).split()


def said_apart(line):
    """The line with a contraction typed as two words put back together: "she s" -> "she's".

    A module that matches English words rather than the engine's reading calls this so that the
    one word people typed as two arrives as one, the same shape the reading has.
    """
    line = str(line or "")
    words = line.split()
    if len(words) < 2:
        return line
    return " ".join(_said_apart(words))


# The names of the notes, so a line about the sound of music keeps its "mi": "do re mi fa sol la".
SOLFEGE = frozenset("do re mi fa sol la ti so".split())
# What "mi" is followed by when it is "me" and not "my": a line that puts somebody alongside
# the speaker ("mi and my friend went out", "mi n the dog", "mi too"). A possessive needs a
# thing to own straight after it, so these words rule "my" out.
MI_IS_ME_AFTER = frozenset("and n or nor & too either neither also".split())
# And what it is followed by in "call mi later", "send mi the link", "give mi a min": a word
# that cannot open a thing to own, so "my" has nothing to stand on. "back" and "first" are
# left out on purpose - "my back hurts", "my first day" are possessives. "know" ("let mi know
# when u land") and "alone" ("leave mi alone for a bit") are here for the same reason: neither
# one is a thing, so "my know" and "my alone" are not sentences.
MI_IS_ME_BEFORE = frozenset("""the a an this that these those later soon now again what how why
    when where if to in on at up out over please pls plz today tomorrow tonight then also
    though anyway know alone""".split())
# A word in front of "mi" that no possessive can follow: "the mi band is cheap", "a mi band",
# "this mi phone". A name is what is left, so the "mi" stays as it was typed.
MI_IS_A_NAME_AFTER = frozenset("the a an this that these those another".split())
# "text mi back", "ring mi back later tonight": the "back" is the second half of the verb
# ("text back", "ring back"), and the word in front is what says so. On its own "mi back" is a
# body: "mi back is playing up", "mi back hurts" keep "my back".
MI_BACK_VERBS = frozenset("""text ring call phone send pass get give pay email message pm
    whatsapp reply write leave take bring hand poke shout""".split())


# "ill" is "i will" in "ill go with the train", "ill take the train", "ill catch the eight
# o'clock": the word after it is a verb that needs a subject, and the line is somebody picking
# between two things. Left as it was typed, the health entry that holds "ill" and "train" claims
# it - "Use the neck rule: a runny nose, sneezing or a mild sore throat above the neck is fine
# for easy exercise" as the answer to a choice of trains. Only these three verbs, and only with
# the clause at its head, so the health lines keep their illness ("im ill", "i feel ill", "my nan
# is very ill", "still ill and i want to run") and the leaving idioms keep their words ("ill let
# you go", "ill leave you to it", "ill get going", "ill book her in tomorrow"). "get" is out
# because "ill get going" is the leaving line, and the -ing forms are out because none of them
# was ever the misfire.
ILL_GOES_ON = frozenset("go take catch".split())


def _ill_is_i_will_going(token, before, after):
    """["i", "will"] for an "ill" with a verb after it that needs a subject, or None."""
    if token != "ill" or after not in ILL_GOES_ON:
        return None
    if before is not None and before != "|" and before not in LEADERS:
        return None
    return ["i", "will"]


def _an_ill_that_is_i_will(clean):
    """`clean` with an "ill" that can only be "i will" set down as the two words.

    The readers that answer match on `clean` and `words`, so the contraction has to be put right
    where the line is written or the knowledge base still sees somebody who is ill. The same test
    as `_ill_is_i_will_going`: the verb after it needs a subject, and nothing in front of the "ill"
    is one.
    """
    words = clean.split()
    changed = False
    for index, word in enumerate(words):
        if word != "ill" or index + 1 >= len(words):
            continue
        if words[index + 1] not in ILL_GOES_ON:
            continue
        before = words[index - 1] if index else None
        if before is not None and before != "|" and before not in LEADERS:
            continue
        words[index] = "i will"
        changed = True
    return " ".join(words) if changed else clean


def _left_off_contraction(token, before, after, before_before):
    """The two words a contraction written without its apostrophe stands for, or None.

    The next word has to be one only the contraction can be followed by, and the word in
    front must leave the plain reading out: "were going to spain" reads as the contraction,
    while "we were late", "how were things" and "were you there" keep their words.
    """
    words = LEFT_OFF_CONTRACTION.get(token)
    if not words or after not in CONTRACTION_NEXT:
        return None
    # "were" is the past of be after a subject ("we were late", "how were things"), so the
    # contraction is only taken where the clause has no subject in front of it yet.
    if before is not None and before != "|":
        leaders_only = before in LEADERS and (
            before_before in (None, "|") or before_before in LEADERS)
        if not leaders_only:
            return None
    return list(words)

# The parts a person has one of. "my backs playing up", "my heads banging", "my tummys been
# off since friday": the s on the part is the possessive 's typed without its apostrophe, or
# the plural habit, and there is still only one of them. A plural part ("my knees", "my hands")
# is not in this list, so nothing that really is plural is touched.
ONE_OF_A_KIND = frozenset("""back head neck chest stomach tummy belly throat nose waist spine
    forehead tongue heart pelvis gullet""".split())
# What follows the part when the s was a possessive: the word says what the one part is doing,
# and a plural would need "are" or "were", which are left out so "our backs are aching" keeps
# its backs.
ONE_PART_AFTER = frozenset("""is was has been s keeps kept does did will would going playing
    killing hurting aching throbbing banging pounding killing""".split())


def _one_of_the_parts(token, before, after):
    """The part a typed s on one of a kind stands for: "my backs" -> "my back", or None.

    Only after a possessive, and only when the word behind it says what the one part is doing,
    so a real plural keeps its s: "my knees have been playing up" and "our backs are aching" are
    untouched, and "my backs playing up" is read as the back it is.
    """
    if not token.endswith("s") or len(token) < 4 or token[:-1] not in ONE_OF_A_KIND:
        return None
    if not _is_possessive(before):
        return None
    # An -ing word says what the part is doing; "playin" is one before the g is put back.
    if after in ONE_PART_AFTER or (after or "").endswith(("ing", "in")):
        return token[:-1]
    return None


# "veggies" is a plate of vegetables after a cooking word ("roast veggies", "steamed veggies",
# "leftover veggies") and a person after a verb of being ("3 are veggies", "the kids are
# veggies"): the word in front tells the two apart, and the diet reading is the one the answer
# tables need. Kept short on purpose - a token that is not here leaves the line as typed.
VEGGIES_AFTER = frozenset("""roast roasted roasting grilled grilling steamed steaming fried frying
    stir braised baked charred sauteed saute boiled raw leftover leftovers fresh frozen chopped
    diced sliced seasonal mixed cook cooked cooking eat eating ate""".split())


# The words "wers" is the verb "wears" after: a person doing the wearing. Anywhere else it is
# the question "where is", which is what a line that opens with it or leads into it asks.
WEARS_AFTER = frozenset("""i you u we they he she it people everyone somebody anybody
mum mums dad dads mam mother father sister brother son daughter wife husband nan gran
grandma grandad granparents mates kids children boy girl lad lass""".split())


def _wers_word(before):
    """The two words a typed "wers" stands for, from the word in front of it.

    "wers" is the e and the apostrophe gone from "where's" and the a gone from "wears", and no
    word list can say which: "wers my keys" is the lost keys, "she wers a red coat" is what she
    wears. The word in front decides, because the verb has to have a person doing the wearing
    in front of it and the question has to be at the front of its clause: after a person it is
    "wears", at the front of a line or a clause or after a lead-in word ("so wers my keys") it
    is "where is".
    """
    if before in (None, "|") or before in LEADERS:
        return ["where", "is"]
    if _plain_chat(before) in WEARS_AFTER or _is_person(before):
        return ["wears"]
    return ["where", "is"]


# The words that make a typed "sum" the arithmetic noun rather than "some" with its o left out.
# A determiner in front of it is one ("do a sum", "the sum of 5 and 3"), and so is the name of a
# lump of money or the word describing it ("the lump sum", "a tidy sum", "a large sum") - the two
# words people use for a payout, and the only place the reader of a line says "sum" for money.
SUM_THE_NOUN = frozenset("""a an the my your his her our their its this that these those another
    each every no any do did does doing done work worked works add added adds total totals
    lump round large small tidy princely big hefty cash whole same missing""".split())


# The words that keep a typed "sum" the word "sum" when they follow it: "sum up", "sum it up",
# "to sum things up" is the verb, and "sum total" is the noun. The word in front cannot say this -
# a verb has no determiner in front of it, and "to", "let me" and "can you" look like the noun's
# lead-ins - so the word after it is what decides.
SUM_STAYS_AFTER = frozenset("up it things that this them total".split())


def _sum_word(before, after=None):
    """The word a typed "sum" stands for, from the words around it.

    "sum" is "some" with the o left out, and it is also the arithmetic noun and the verb of
    adding up, and the maths reading was winning everywhere: "i gotta loose sum weight b4 the
    weddin" was read as a line about numbers, so the topic was maths-and-numbers and the "loose"
    in front of it was not repaired to "lose". A determiner or the name of a lump of money in
    front is the noun; "up", "it", "things" or a demonstrative behind is the verb ("to sum up",
    "let me sum it up", "sum up what happened"); anything else is "some" ("i need sum help with
    my cv", "can i get sum milk", "sum of us are going").
    """
    spelled = _plain_chat(before) if before not in (None, "|") else ""
    if spelled in SUM_THE_NOUN:
        return ["sum"]
    behind = _plain_chat(after) if after not in (None, "|") else ""
    if behind in SUM_STAYS_AFTER:
        return ["sum"]
    if spelled in ("in", "to") and behind not in SUM_STAYS_AFTER:
        # "in sum, the day was good" and "to sum up" are the only two of these people type; the
        # first is the noun, and the second was already sent to the verb by the word behind it.
        return ["sum"]
    return ["some"]


def _positional_word(token, before, after, after_after=None, before_before=None,
                     before_words=None):
    """The word a quickly typed token stands for, from where it sits, or the token itself.

    "w" on its own is not a word and is "with"; "2" and "4" are "to" and "for" in front of a
    phrase opener, and in front of a demonstrative unless a period follows it; "no" is "know"
    between a subject and what a verb takes; "were" at the front of a line is "where" in front
    of a verb and "we are" in front of anything else.
    """
    if (token in UP_TO_SPELLINGS
            and (before is None or before == "|" or before in UP_TO_LEADS)
            and (after is None or after == "|" or after in UP_TO_TAGS)
            and (after_after is None or after_after == "|")):
        return ["what", "you", "up", "to"]
    if token in WHAT_ARE_YOU_SPELLINGS and after in WHAT_ARE_YOU_AFTER:
        return ["what", "you"]
    if token == "w":
        return ["with"]
    if token == "c" and after in LETTER_C_IS_SEE:
        # "c u later" is a goodbye typed with the letter for the word, the way "cu" is one
        # written as a single token, and it reached the bot as a line with nothing in it: "c u"
        # got the thanks-for-telling answer and "c u later" the shrug. The letter stays the
        # letter everywhere else - "vitamin c", "plan c", "hepatitis c", "c section" - so only
        # the second person pronoun in front of it turns it into "see".
        return ["see"]
    if token == "wers":
        return _wers_word(before)
    if token == "sum":
        return _sum_word(before, after)
    if token == "were":
        spelled = _were_for_another_word(before, after, after_after)
        if spelled:
            return spelled
    if token in CLIPPED_THINGS and _is_a_thing_here(before, after, after_after):
        return [_clipped_thing(token)]
    if token in CLIPPED_UNITS and (_is_a_count(before) or _says_one(before)):
        # "4 yr old", "2 hrs sleep", "ten mins". The count in front is what makes it safe: on
        # its own "yr" is how people type "your", and "hr" is the department.
        one, many = CLIPPED_UNITS[token]
        if token == "hr" and _hr_is_the_department(after):
            return [token]        # "this hr department", "past hr policies"
        if _says_one(before) or _is_before_a_noun(token, after):
            return [one]          # "1 hr drive", "a 3 hr flight", "next yr"
        return [many]
    contraction = _left_off_contraction(token, before, after, before_before)
    if contraction:
        return contraction
    going = _ill_is_i_will_going(token, before, after)
    if going:
        return going
    feeling = _sounds_like_a_feeling(token, before, after, before_before)
    if feeling:
        return [feeling]
    read = _digit_word(token, before, after, after_after)
    if read:
        return [read]
    if token == "wdyt" and after and after != "|":
        # "wdyt about moving house". `wdyt` is "what do you think", and the line it was in got the
        # initials said back to it ("Got it - wdyt about moving house"). Only with a subject after
        # it: a bare "wdyt" leans on the last turn, and every reader the expansion reaches wants
        # the subject in the line itself.
        return ["what", "do", "you", "think"]

    one_part = _one_of_the_parts(token, before, after)
    if one_part:
        return [one_part]
    if token == "ow" and after in HOW_FOLLOWS:
        # "ow do i clean a rug", "ow much is milk": the people who drop the h drop it every time.
        # The next word is what makes it safe - "ow my head" and "ow that hurt" keep their "ow".
        return ["how"]
    if token == "bout" and before not in DETERMINERS:
        return ["about"]                          # "arguin bout money", "whats that bout"
    if token == "no" and (before in KNOW_SUBJECT or before in NOT_BEFORE_KNOW):
        # The word after is read through the chat tables first: "i dont no y" and "dont no
        # wat to do" put a typed question word behind the "no", and the raw token is not the
        # word the list holds.
        after_read = _plain_chat(after) if after and after != "|" else after
        if (after is None or after == "|" or after in A_VERB_CAN_FOLLOW
                or after_read in A_VERB_CAN_FOLLOW):
            return ["know"]
    if token == "hv":
        before_read = _plain_chat(before) if before else ""
        after_read = _plain_chat(after) if after else ""
        if before_read in DETERMINERS:
            return [token]                        # "the hv", "my hv": the health visitor
        if before_read in HV_SUBJECTS or before_read in HV_HELPERS or after_read == "to":
            return ["have"]                       # "i hv", "shld hv", "hv to go"
        if after_read in HV_SUBJECTS:
            return ["have"]                       # "hv u got a min", "how many hv u got"
    if token == "bin":
        if before in HAVE_FORMS or (before or "").endswith("ve"):
            return ["been"]                       # "i have bin", "ive bin"
        if _is_person(before) and (after in PERSON_PREPS or _is_participle(after)
                                   or _is_said_of_a_person(after)):
            return ["been"]                       # "my mums bin in hospital", "my cats bin sick"
        if before_before in THING_POSSESSIVES \
                and (_plain_chat(before) if before else "") not in BIN_CONTAINERS \
                and _the_thing_has_been(after):
            return ["been"]                       # "my phones bin actin up all wk"
        if (before in BEEN_SUBJECT or before in BE_FORMS or before in (None, "|")) \
                and (_is_said_of_a_person(after) or (after or "").isdigit()
                     or _counts_a_period(after) or _counts_a_period(after_after)
                     or (before in BEEN_SUBJECT and after in ("a", "an"))):
            # "bin thinkin bout it", "that is bin 3 wks now", "its bin two months". The word in
            # front has to be the person or the helper, so "bin day" and "the bin lorry" are bins.
            return ["been"]
    if token == "of" and _plain_chat(before) in MODAL_FORMS and _is_participle(after) \
            and before_before not in DETERMINERS:
        # "should of started", "could of been". "what should i think of" keeps its "of", because
        # a line that names the spelling it asks about is a question about words, and a
        # determiner in front makes the modal the thing itself: "a can of red paint",
        # "the will of the people" and "her might of it" are cans, wills and mights.
        return ["have"]
    if token in AINT_FORMS:
        # "ain't" is whichever helper the writer left out. "have not" when the verb that
        # follows is a participle ("i aint eaten all day", "aint got a job yet"), "am not"
        # after "i" ("i aint happy"), "are not" after a plural subject, "is not" otherwise.
        # Reading every one as "is not" gives "i is not eaten all day", and a line whose
        # negation is left as a strange helper is a line the entries that key on it miss:
        # "aint got a job yet" came back congratulating them on the job.
        if _is_participle(after) or after in PAST_AS_PARTICIPLE:
            return ["has", "not"] if before in HAS_SUBJECT else ["have", "not"]
        if _plain_chat(before) == "i":
            return ["am", "not"]
        if _plain_chat(before) in AINT_PLURAL:
            return ["are", "not"]
        return ["is", "not"]
    if token == "of" and after == "to" and _is_be(before):
        return ["off"]                        # "im of to work", "we were of to spain"
    if token == "b" and _spells_a_helper(before):
        return ["be"]                          # "gona b late", "ill b there", "should b fine"
    if (after is None or after == "|") and _where_a_state_stands(
            before, before_before, after, before_words):
        # A state word with a letter typed wrong, said of the person and nothing after it: "im
        # hungy", "im thisty", "im colde". These are not a state missing an ending, so the rule
        # below cannot see them, and a word that says how they are with nothing after it is the
        # whole of the evidence that it is how they are and not what they are called. How many
        # measure words come before it does not change that: "im so so hungy" is still hungry.
        state = _a_letter_wrong_in_a_state(token)
        if state:
            return [state]
    if before in FIRST_PERSON_BE or (before_before in FIRST_PERSON_BE
                                    and before in AMOUNT_BEFORE_A_STATE):
        # A feeling with its ending left off, right where the person says how they are: "im
        # annoy", "im bore", "im excit", "im confuse". These are words already, so the
        # misspelling fixer may not touch them, and every one of them was answered "Nice to
        # meet you, Annoy". The word in front is the whole of the evidence, so a line about a
        # bush or a tyre is left alone. One measure word may stand between the two and says
        # nothing about which word comes next: "im still confus" and "im so bore" are the same
        # feeling, "im very tire" is tired rather than a tyre, and "im so nervou about
        # tomorrow" is nervous.

        feeling = _feeling_without_its_ending(token)
        if feeling:
            return [feeling]
    kin = _kin_needs_a_helper(token, before, after,
                              before_before is None or before_before == "|"
                              or before_before in LEADERS, after_after)
    if kin:
        return kin                             # "my mums got a chest infection" -> "my mum has got"
    if token in ("yr", "yrs") and (before or "").isdigit():
        # "my 9 yr old" is nine years old, not the "nine your old" the chat table alone gives:
        # `yr` is typed for "your" too ("yr welcome"), so the number in front decides it.
        return ["years" if token.endswith("s") or after == "old" else "year"]
    family = _family_short(token, before, after, after_after)
    if family:
        # "my mil" is my mother in law, "my oh" my other half, "my dd" my daughter
        return family
    if token == "veggies" and before in VEGGIES_AFTER:
        # "roast veggies" is a plate of vegetables; "3 are veggies" is three vegetarians.
        return ["vegetables"]
    if token in ("ur", "your") and after and after in YOU_ARE_AFTER:
        # The contracted spelling, because `plain` says the line back and "Noted: you're going
        # to love this" is how a friend writes it; the reading is still "you" and "are".
        # "your" is the same two words with the apostrophe left off, and the word after it is
        # what says so: a possessive is followed by the thing it owns ("your mum", "your
        # boiler"), never by an article, a word of degree or the word for what somebody is
        # doing. Read as a possessive, "your a good bot" was answered "Got it. Is there
        # anything you'd like a hand with?" while "you are a good bot" answered the question
        # about what the bot is, and "your going to love this" came back as "Noted: your going
        # to love this". Words a possessive does take are left alone, which is why "your kind"
        # and "your right" are not in the list: "your kind of tea", "your right hand".
        return ["you're"]                      # "ur a star", "your a good bot", "your so kind"
    if token == "mi" and after in MI_IS_ME_AFTER:
        # "mi and my friend went out", "mi too": here "mi" is how "me" is typed, and the word
        # after it is what says so. A possessive with nothing to possess is not a sentence -
        # read as "my" these came out "your and your friend went out" and "Noted: your and the
        # dog", which is worse than the slip.
        return ["me"]
    if token == "mi" and before in MI_IS_A_NAME_AFTER:
        # "the mi band is cheap", "this mi phone": a possessive cannot follow a determiner, so
        # the "mi" belongs to the name of the thing and is left as it was typed.
        return [token]
    if token == "mi" and after in MI_IS_ME_BEFORE:
        # "call mi later", "send mi the link", "tell mi what u think": nothing after it can be
        # owned, so it is "me" and not "my". Read as "my" these came out "call my later".
        return ["me"]
    if token == "mi" and after == "back" and before in MI_BACK_VERBS:
        # "text mi back", "ring mi back later tonight": the verb in front makes the "back" part
        # of it, so the "mi" between them is "me". Without a verb of that kind the "back" is a
        # body and "mi back is playing up" stays "my back".
        return ["me"]
    if token == "mi" and (after is None or after == "|"):
        # The line ends on it: "who is it? mi", "thats mi", "wait for mi". A possessive has
        # nothing to stand on there, so it is "me".
        return ["me"]
    if token == "mi" and not (before in SOLFEGE
                              and (after is None or after == "|" or after in SOLFEGE)):
        # "mi" is how "my" is typed in a lot of everyday writing ("mi mum is coming round",
        # "mi tea is cold", "mi boiler is broke"), and it is not an English word, so the only
        # thing that needs keeping out of the way is the note in a run of them: "do re mi fa",
        # where "so mi boss said no" is still "my boss".
        if before is not None and before != "|" and before not in LEXICON:
            # The last piece of a name rather than the start of a phrase: "i got a xiaomi mi band",
            # "a redmi mi note". The word in front of it is not one the lexicon knows, so it is
            # the end of a made-up one and "mi" belongs with it.
            return [token]
        return ["my"]
    return [token]


# "ur" is two words typed as one, and which one it is is decided by the word after it, because
# only one of the two can stand there. A possessive takes a thing ("ur mum rang", "ur bike is
# outside", "ur washing machine is leaking"), and "you are" takes an article, a word of degree
# or the word for what somebody is doing ("ur a star", "ur so funny", "ur the best", "ur going
# to love this"). Read as "your" every time, "ur so funny" was answered "Thanks for telling me",
# "ur the best" went to the search hedge and "ur going to love this" was echoed back as
# "Noted: your going to love this".
YOU_ARE_AFTER = frozenset("""a an the such so too very really quite bloody proper
    going gonna joking kidding being not""".split())


def _join_chat_digits(tokens):
    """A chat word typed in pieces stays one word: "any1", "l8r", "2nite", and "i d k".

    The tokeniser keeps a measure together ("5kg", "1.5kg") but splits a letter run from a
    digit run, so the digit spelling of a chat word arrives in two or three pieces ("l" + "8r",
    "2" + "nite") and never reaches the chat table. Pieces are joined only into a word the
    lexicon knows, so an ordinary digit pair ("i have 4 cats", "a table for 2") is left alone,
    and a measure ("1.5kg", "20mg") is one token already and never a candidate.

    Somebody typing with one hand writes the same chat word with a space between every letter:
    "i d k", "o m g", "n e 1". Nothing read those runs, so `i d k` came out as "i'd k" and the
    line reached no card at all. Three or four one-character pieces that spell a chat word are
    joined the same way, and a run that spells nothing the lexicon knows ("c a t", "i have 4
    cats") is left exactly as typed.
    """
    joined = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        if (following is not None
                and (following[:1].isdigit() or token.isdigit())
                and (token + following in lexicon.CHAT
                     or token + following in lexicon.MISSPELLINGS)):
            joined.append(token + following)
            index += 2
            continue
        spelt = _said_apart_as_one(tokens, index)
        if spelt is not None:
            joined.append(spelt[0])
            index = spelt[1]
            continue
        joined.append(token)
        index += 1
    return joined


# A run of three or four one-character pieces that spells one chat word, in the line as typed.
_SPACED_RUN = re.compile(r"(?<![\w'])([a-z0-9](?:[ \t]+[a-z0-9]){2,3})(?![\w'])", re.IGNORECASE)


def _said_apart_as_one_word(clean):
    """Join "i d k" into "idk", and only when the run spells a word the lexicon knows.

    Longest first, so "n e 1" is read as "ne1" and not as a shorter piece of it. Two pieces are
    deliberately left alone: "i m", "didn t" and "c section" are read by the tables that expect
    them, and joining them here would take those lines away from those readers.
    """
    if not _SPACED_RUN.search(clean):
        return clean

    def join(match):
        # The run may be longer than the chat word in it: "b t w i was late" is "btw" and the
        # start of the next clause, so the longest piece that spells a word wins and the rest of
        # the run is put back exactly as typed.
        pieces = match.group(1).split()
        for length in range(len(pieces), 2, -1):
            word = "".join(pieces[:length]).lower()
            if word in lexicon.CHAT or word in lexicon.MISSPELLINGS:
                return " ".join([word] + pieces[length:])
        return match.group(0)

    return _SPACED_RUN.sub(join, clean)


# "i d k" and "o m g": three or four single characters in a row that spell one chat word.
# "i d k" and "o m g": three or four single characters in a row that spell one chat word.
_SPACED_PIECE = re.compile(r"^[a-z0-9]$")


def _said_apart_as_one(tokens, start):
    """The chat word at this position and the index after it, or None.

    Longest first, so "n e 1" is "ne1" and never a shorter piece of it, and never more than four
    pieces, because five one-character words in a row is a spelling and not a chat word.
    """
    if not _SPACED_PIECE.match(tokens[start]):
        return None
    for length in (4, 3):
        pieces = tokens[start:start + length]
        if len(pieces) < length or not all(_SPACED_PIECE.match(piece) for piece in pieces):
            continue
        word = "".join(pieces)
        if word in lexicon.CHAT or word in lexicon.MISSPELLINGS:
            return word, start + length
    return None


# "The docs" is two different things: the surgery down the road ("should she go to the docs",
# "ring the docs in the morning") and a set of papers ("send the docs to my email", "the docs are
# in the folder"). The word "doctor" is what the health answers are keyed on, so a line about the
# surgery that says "docs" reached none of them - `my mums got a chest infection should she go to
# the docs` got the search hedge while the same line with "doctor" got the pharmacist-or-GP
# answer. The verb is what tells them apart: you go, ring, call, visit or see the doctor; you send,
# print, sign or read the documents.
DOCS_VISIT = frozenset("""go goes going gone went see sees seeing saw seen visit visits visiting
    ring rings ringing rang call calls calling called phone phones phoned ask asks asking asked
    book booked appointment appointments consult surgery gp""".split())
# A line with one of these in it is about paperwork, whatever else it says.
DOCS_PAPER = frozenset("""send sends sent email emails emailed print printed download downloaded
    upload uploaded scan scanned file files folder contract contracts paperwork invoice invoices
    lease leases tax read reading sign signed attach attached share forward forwarded page pages
    pdf copy copies draft document documents solicitor mortgage insurance check checked
    through""".split())
# A document can be the thing on a screen, which a verb of going or ringing says nothing about:
# "can i see the docs on my phone" is Google Docs, not a surgery appointment. These words name
# the screen itself, and the ones in DOCS_ON say "on the screen" rather than "ring the surgery".
DOCS_SCREEN = frozenset("""tablet laptop pc screen online app apps link links browser website web
    google drive cloud portal intranet""".split())
DOCS_ON = frozenset(("on", "in", "via", "from", "as", "into"))


def _docs_on_a_screen(words):
    """Whether the line is about the docs on a screen rather than a visit to the surgery."""
    if any(word in DOCS_SCREEN for word in words):
        return True
    for index, word in enumerate(words):
        if word in ("phone", "tablet", "laptop", "pc", "screen", "file"):
            if any(back in DOCS_ON for back in words[max(0, index - 2):index]):
                return True
    return False


# The meal a person names when they say what to eat, and the words that put a word in that slot:
# "what should i have for tea", "whats for dinner", "anything after lunch". The food rows are
# keyed on the meal itself, so a meal word typed at speed costs the whole answer - "wot shud i av
# for tae" got "I don't know enough to answer that honestly. A search should sort you out
# quickly" while the same line with "tea" in it got the fifteen-minute dinner.
MEAL_WORDS = frozenset("""tea dinner supper lunch breakfast brunch snack food""".split())
FOOD_SLOT_LEAD = frozenset("""for at after before til till until round over about""".split())
# "for tee" is a golf tee as often as a cup of tea, and it is a word in its own right, so it is
# not a spelling of "tea" that this repair takes.
NOT_A_MEAL_TYPO = frozenset(("tee",))
# A meal stands at the end of the line or has the time it is for behind it: "whats for tae",
# "whats for brea tomorrow". Any other word after it means the word is not that slot's meal.
TIME_AFTER_MEAL = frozenset("time tonight tomorrow today now later".split())


def _near_a_meal(word, before, after=None):
    """The meal a misspelt word names, or None.

    Only in the slot a meal goes in (behind "for", "after", "before", ...), and only one letter
    out from one of the meals: "tae", "taa", "tay", "dinnar", "sunner". A word the lexicon knows
    is left alone, so "for two", "at tea", "for the launch" and a golf tee are untouched.

    The position is what keeps a real sentence out: the misspelt meal has to end the line or sit
    in front of a time word, because that is where a meal stands ("whats for tae", "whats for
    brea tomorrow"). Behind "for" alone it is far too easy - "ask for branch details", "for
    upper floor", "for inner peace", "for bunch of flowers" are all one letter from a meal and
    all words of their own, most of them outside the lexicon.
    """
    if not word or len(word) < 3 or word in LEXICON:
        return None
    if _plain_chat(before) not in FOOD_SLOT_LEAD:
        return None
    if after is not None and _plain_chat(after) not in TIME_AFTER_MEAL:
        return None
    if word in NOT_A_MEAL_TYPO:
        return None
    # The last letter left off is the other way people type at speed - "for lunc", "after dinn",
    # "whats for brea" - and behind the slot a meal is the only word it can be.
    for meal in sorted(MEAL_WORDS):
        if len(word) >= 4 and meal.startswith(word):
            return meal
    found = sorted(meal for meal in MEAL_WORDS if _one_letter_apart(word, meal))
    return found[0] if len(found) == 1 else None


def _a_meal_word_misspelt(clean, words):
    """Put a meal word typed at speed back in the line, in `clean` as well as the reading.

    It is repaired in `clean` for the reason the "docs" repair is: the kitchen's rows are keyed
    on the meal, so a reading fixed on its own would leave the reply where it was. The slot is
    what makes it safe - the word in front has to be the preposition a meal goes behind, and
    what follows has to be the end of the line or the time it is for - and that is what keeps a
    name out of it ("tae is coming over", "me and tae went out"). A name can sit behind "for"
    ("im waiting for tae" reads as the meal), so it is the position, not the name, that decides.
    """
    places = {}
    for index, word in enumerate(words):
        if not index:
            continue
        after = words[index + 1] if index + 1 < len(words) else None
        meal = _near_a_meal(word, words[index - 1], after)
        if meal:
            places[index] = meal
    if not places:
        return clean, words
    pieces, last = [], 0
    for index, match in enumerate(RAW_WORD.finditer(clean)):
        pieces.append(clean[last:match.start()])
        pieces.append(places.get(index, match.group(0)))
        last = match.end()
    pieces.append(clean[last:])
    for index, meal in places.items():
        words[index] = meal
    return "".join(pieces), words


def _docs_doctor(clean, words):
    """"Docs" is read as the doctor where the line is about the surgery, and left as it is.

    Only the two spellings people type for it, `doc` and `docs`, and only when a verb of going
    or ringing is within a few words on either side and the line names no paperwork at all. A
    line naming neither stays as typed: guessing one way would be worse than not guessing.

    It is the one repair made in `clean` rather than only in `plain`, because no table anywhere
    is keyed on "docs": the health answers hold "doctor" and the paperwork ones hold "pdf",
    "folder", "invoice". Repairing `plain` alone moves the reading and leaves the reply alone,
    which is where this line stood. The usual cost of repairing `clean` - a cue list that holds
    the typed form loses its match - cannot be paid here, because no list holds this one.
    """
    if not any(word in ("doc", "docs") for word in words):
        return clean, words
    if any(word in DOCS_PAPER for word in words):
        return clean, words
    if _docs_on_a_screen(words):
        return clean, words
    places = set()
    for index, word in enumerate(words):
        if word not in ("doc", "docs"):
            continue
        near = words[max(0, index - 4):index] + words[index + 1:index + 3]
        if any(other in DOCS_VISIT for other in near):
            places.add(index)
    if not places:
        return clean, words
    # The i-th match of RAW_WORD is the i-th word, so the two lists line up.
    pieces, last = [], 0
    for index, match in enumerate(RAW_WORD.finditer(clean)):
        pieces.append(clean[last:match.start()])
        pieces.append("doctor" if index in places else match.group(0))
        last = match.end()
    pieces.append(clean[last:])
    for index in places:
        words[index] = "doctor"
    return "".join(pieces), words

# A relation a person has one of keeps its "s" when a verb that takes a single person follows
# it: "my mums got a bad chest" is "my mum has got a bad chest", and the health of one woman is
# what the line is about, not several mothers. Only one-and-only relations are in the set, so
# "my kids got chickenpox" and "my sisters got married" keep the plural they mean, and only after
# a possessive, so "the mums got together" is left alone.
ONE_RELATION = frozenset("""mum mom mam mummy mommy dad daddy nan nana gran granny grandad
    grandpa granddad grandma grandmother grandfather mother father husband wife""".split())
# The verbs that take a "has" in front of them, so the possessive's "'s" comes back as a word.
HAS_FORMS = frozenset(("got", "bin", "had"))
# The words a single person is the subject of in an everyday line: a helper, "got", or one of the
# verbs a parent turns up as the subject of ("my mums said", "my mums wont eat").
# `called` and `rang` are left out on purpose: after "my mums" they are the verb of the
# sentence only when the line is about someone ringing. "my mums called janet" is the name of
# the mum, which the composer reads back to the person ("your mum's called janet"), so taking
# the "s" off there would change a name into a phone call.
ONE_RELATION_VERBS = frozenset("""got bin wont cant said says told went came goes needs wants
    keeps lives works gets thinks loves hates""".split())


# "sor" is a sore spot typed with a letter missing, and it is also the front of "sorry": a
# repair wherever the word turns up read "i am sor about that" as a sore body and answered
# "That sounds wearing..." where main shrugs. A body word names itself, so "sor" comes back as
# "sore" in front of a part of the body or after the verb that says how it is, and nowhere else.
SORE_IN_FRONT = frozenset("""is are was were been feels feel felt gets get got still""".split())
# "so", "very" and "really" come after a verb of being in "my back is very sor" and after a
# person in "im so sor i forgot", which is the apology. The word is only stepped over when a
# verb of being stands in front of it, so the apology keeps its own reading.
SORE_FILLERS = frozenset("""so very really bit little too pretty quiet that""".split())
SORE_PARTS = frozenset("""throat back head neck shoulder shoulders knee leg legs foot feet arm
    arms toe toes hip ankle wrist elbow ear ears eye eyes tooth teeth gum mouth hand hands
    finger fingers belly stomach muscle muscles chest side sides rib ribs heel heels jaw skin
    tongue sunburn""".split())


def a_sor_bit_is_sore(tokens):
    """"my throat is sor" is "my throat is sore", and "i am sor about that" is left alone."""
    out = []
    for index, token in enumerate(tokens):
        if token == "sor":
            before = tokens[index - 1] if index else None
            after = tokens[index + 1] if index + 1 < len(tokens) else None
            fills = (index > 1 and before in SORE_FILLERS
                     and tokens[index - 2] in SORE_IN_FRONT)
            if ((before is not None and (before in SORE_IN_FRONT or fills))
                    or (after is not None and after in SORE_PARTS)):
                out.append("sore")
                continue
        out.append(token)
    return out


def _one_relation_says(words):
    """"my mums got a bad chest" is "my mum has got a bad chest".

    The possessive left out its "'s", so the relation is the subject on its own: the "s" on it
    is the "has" or the "is" of the line and not a plural, and it goes when a verb that takes
    one person follows it. A verb that takes a "has" in front of it gets the "has" back, which
    is the way the line would be spelt out: "my mums had a fall" is "my mum has had a fall".
    """
    out = []
    for index, word in enumerate(words):
        after = words[index + 1] if index + 1 < len(words) else None
        if (index and after and word.endswith("s") and word[:-1] in ONE_RELATION
                and _is_possessive(words[index - 1])):
            read = _plain_chat(after)
            if read in ONE_RELATION_VERBS or read in HAVE_FORMS or read in BE_FORMS \
                    or read in MODAL_FORMS:
                out.append(word[:-1])
                if read in HAS_FORMS:
                    out.append("has")
                continue
        out.append(word)
    return out


def _ask_start(clause):
    """Where an ask begins inside a clause that did not open with one, or None.

    Only shapes that read as a real question are taken: a question word with an auxiliary
    or a degree word after it ("what could be wrong", "how long until he sleeps"), or an
    auxiliary with a subject after it ("... can i take ibuprofen"). A question word that
    introduces a reported clause ("i do not know what to do", "what to do next", "the book
    which i read") is left alone, so a feeling is still a feeling.
    """
    if not clause or clause[0] in WH_WORDS or clause[0] in AUX_WORDS:
        return None                  # the clause already opens like a question
    for start in range(1, len(clause)):
        token = clause[start]
        following = clause[start + 1] if start + 1 < len(clause) else None
        after = clause[start + 2] if start + 2 < len(clause) else None
        if following is None:
            continue
        if token in WH_WORDS:
            if following in AUX_WORDS or _a_word_between_the_ask_and_its_aux(clause, start):
                if _reported(clause, start):
                    continue
                return start
            if following in HOW_DEGREE or (following in ASK_NOUNS and after in AUX_WORDS):
                if _reported(clause, start):
                    continue
                return start
        elif token in AUX_WORDS and following in SUBJECT_WORDS:
            if clause[start - 1] in NO_ASK_AFTER:
                continue
            if clause[start - 1] in SUBJECT_WORDS:
                # "we have you down for tuesday", "they have you booked in": the auxiliary is
                # the verb of the subject already in front of it, so it opens nothing
                continue
            if token in BE_WORDS:
                # "the thing is i do not know", "my worry is i will not finish",
                # "what matters is you get there": a be-form in front of a person links a
                # clause, and a yes/no question never opens with "is i" or "was she".
                continue
            return start
    return None


# A word belongs to the question phrase in front of it rather than to a clause of its own:
# "what else do i need", "which size should i get", "what kind of paint do i need", "what
# present would she like". Cut at the auxiliary instead and the ask reads "do i need", which is
# no ask at all, so the question word is where the ask begins.
WH_QUANTIFIERS = frozenset("""else other others kind sort type size colour color number
    make model brand version flavour flavor""".split())
# What cannot stand between a question word and the auxiliary that asks it. A pronoun, a
# determiner or another verb there means the question word is reported or relative, not asked.
NOT_IN_A_QUESTION_PHRASE = frozenset("""
    i me my mine we us our you your he him his she her it its they them their
    the a an this that these those some each every which what who whom whose
    to of for in on at by with from about as than if whether there here
    do does did is are was were am be been being have has had will would shall should can
    could may might must not no never""".split()) | WH_QUANTIFIERS
# A question word asks through an auxiliary only when the auxiliary is followed by the person or
# thing that does it: "what present would she like" asks, while "she keeps forgetting where things
# are in the kitchen" and "my printer says paper jam when there is not one" report where something
# is or how something is, because the auxiliary comes after its subject rather than in front.
AFTER_AN_INVERTED_AUX = frozenset("""
    i we you he she they there it this that these those
    the a an my our your his her their some any""".split()) | SUBJECT_WORDS


def _a_word_between_the_ask_and_its_aux(clause, start):
    """True when the question word at clause[start] reaches an auxiliary over a few words.

    "what present would she like", "what sort of shoes do i need", "what party games would he
    like": the words between belong to the question, and the auxiliary that follows asks it. A
    pronoun, a determiner or a second verb between them means the question word is reported or
    relative, so that is left alone.
    """
    span = clause[start + 1:start + 6]
    for offset, word in enumerate(span):
        if word in AUX_WORDS:
            crossed = [w for w in span[:offset] if w not in WH_QUANTIFIERS
                       and w not in ("of", "for")]
            subject = clause[start + 2 + offset] if start + 2 + offset < len(clause) else None
            return (len(crossed) <= 2 and not (set(crossed) & NOT_IN_A_QUESTION_PHRASE)
                    and subject in AFTER_AN_INVERTED_AUX)
    return False


def _inverted_ask(clause, start):
    """True when the relative word is really the question: "who should i see"."""
    after = clause[start + 1:start + 3]
    return (len(after) > 1 and after[0] in RELATIVE_ASKS
            and after[1] in SUBJECT_WORDS)


def _reported(clause, start):
    """True when the question word at clause[start] reports or names rather than asks."""
    before = clause[max(0, start - 2):start]
    if not before:
        return False
    if set(before) & REPORTING:
        return True
    if (clause[start] in RELATIVE
            and not _inverted_ask(clause, start)
            and before[-1] not in AUX_WORDS and before[-1] not in WH_WORDS
            and before[-1] not in REPORTING
            and (before[-1] in DETERMINERS or len(before) > 1
                 and (before[-2] in DETERMINERS or before[-2] in NOMINAL_BEFORE_COPULA))):
        return True
    return (before[-1] in COPULAS
            and (len(before) < 2 or before[-2] in NOMINAL_BEFORE_COPULA))


def _split_ask(clauses):
    """Clauses with an ask that sits inside one moved out into a clause of its own.

    "im knackered all the time what could be wrong" becomes two clauses, so the focus, the
    kind and every module that reads the ask see the question rather than the news.
    """
    out = []
    for clause in clauses:
        start = _ask_start(clause)
        if start is None or start >= len(clause) - 1:
            out.append(clause)
            continue
        out.append(clause[:start])
        out.append(clause[start:])
    return out


# A clause can begin with one of these, so a discourse marker in front of one starts a clause.
CLAUSE_OPENERS = frozenset("""i we you they he she it this that there anyone anybody someone
    everyone somebody nobody nothing""".split())


def _opens_clause(token):
    """Can a clause of its own begin with this word?"""
    return (token in CLAUSE_OPENERS or token in SUBJECT_WORDS or token in WH_WORDS
            or token in BREAKS or token in LEADERS)


# "she's got", "he's been", "she's had a fall": the apostrophe-s after a pronoun is "has" in
# front of a participle and "is" everywhere else. English has no "she is got", so the word in
# front decides it. Only the three participles that cannot be a state are here: "she is told
# off", "he is said to be leaving", "she is known for her cakes", "she is paid weekly" and "he
# is kept busy" are all passives and right as typed, so "told", "said", "known", "paid" and
# "kept" stay out. "she is tired", "it is gone" and "the job is done" keep the "is" the same way.
HAS_AFTER = frozenset("""got been had""".split())
# Only a person in front moves the verb. "it's been a long week" is a state the speaker is in
# and reads as small talk, and "it is gone", "that is done" are states of the thing named, so
# "it", "that", "this" and "there" keep the "is" they were typed with.
HAS_SUBJECTS = frozenset("she he who".split())


def _says_has(words):
    """"she is got a cold" -> "she has got a cold": a pronoun, an "is" and a participle.

    "gone" counts only with a word after it: "she is gone to the doctors" is "she has gone to
    the doctors", while a bare "she is gone" is a person who is dead or away, which is a state
    and stays as it was typed.
    """
    for index in range(1, len(words) - 1):
        if words[index] != "is" or words[index - 1] not in HAS_SUBJECTS:
            continue
        after = words[index + 1]
        if after in HAS_AFTER or (after == "gone" and index + 2 < len(words)):
            words[index] = "has"
    return words


def _clauses(tokens):
    """Split a run-on line into clauses at punctuation and discourse markers.

    A marker only opens a clause when a clause can begin after it. "my landlord still has
    not fixed the boiler" and "i wanted to go but could not afford it" keep it: there the
    marker is part of the clause, and cutting it off left "has not fixed the boiler" and
    "could not afford it", which read as yes/no questions.
    """
    out, current = [], []
    for n, token in enumerate(tokens):
        if token == "|":
            if current:
                out.append(current)
                current = []
            continue
        following = tokens[n + 1] if n + 1 < len(tokens) else None
        if (token in BREAKS and len(current) >= 2 and following
                and _opens_clause(following)):
            out.append(current)
            current = []
            continue
        current.append(token)
    if current:
        out.append(current)
    return out


LEADERS = frozenset("""and so but also then ok okay oh well right now anyway anyways
hi hiya hey hello morning evening thanks thank thx cheers ty please just actually still
finally instead otherwise plus however meanwhile btw honestly anyway""".split())


# A line that opens on "like" is opening on a filler, and the clause behind it starts with one
# of these: "like my cat wont eat", "like im so tired", "like what should i cook". The word
# itself is a real one, so the frame is what tells the two apart: "like a sauna in here",
# "like butter", "it is like that", "like this one" and "like father like son" all keep it,
# because nothing that opens a clause follows the "like".
LIKE_STARTS_A_CLAUSE = frozenset("""
i im ive id ill me my mine we were weve us our ours you youre youve your he hes she shes it its
they theyre theyve their them
what why how when where who which whose
can cant cannot could couldnt should shouldnt would wouldnt do dont doesnt did didnt
is are was were will wont have has had havent hasnt dont didnt get got gets need needs want
wants keep keeps just never not so too always still really gonna wanna dunno idk
u ur ya yall
""".split())


def _a_leading_like_is_a_filler(clean):
    """"like my cat wont eat" is about the cat, so the "like" is not part of the line.

    People open a line with "like" the way they open it with "so" or "well", and the word is a
    real one, so it was read as a comparison and the line lost its answer: "like my cat wont
    eat" was noted back and "like my broadband keeps dropping out" got the warm line where "my
    broadband keeps dropping out" gets the router answer. Only a clause opener after it makes
    it the filler, which is what keeps a comparison out of it.
    """
    head, _, rest = clean.partition(" ")
    if head.strip(",.!?") != "like" or not rest:
        return clean
    after = rest.split(" ", 1)[0].strip(",.!?")
    if after not in LIKE_STARTS_A_CLAUSE:
        return clean
    return rest


# An exclamation after a question word is the person's surprise, not a thing the line is about.
# "what on earth", "how on earth", "what in the world": the Earth card answered "what on earth"
# with the Earth's layers, and "why on earth is my boiler not lighting" was read as a line about
# the planet instead of the boiler. Only a question word in front makes it an exclamation, so
# "the coldest place on earth" and "how old is the earth" keep their Earth. The two that name
# nothing ("the hell", "the heck") are left alone: no card reads them, and taking them out leaves
# a bare question where "Go on - what happened?" is the warmer answer.
EXCLAIMED_AFTER_A_QUESTION = re.compile(
    r"\b(what|how|why|where|who|which|when|whatever|however|whoever|whenever)\s+"
    r"(?:on\s+earth|in\s+the\s+world|the\s+dickens|the\s+blazes|on\s+god'?s\s+earth)\b")


# A line can open on an exclamation of exasperation, and the word is not the person's subject:
# "god i hate mondays" was filed as a fact about them and said back as "Noted: god you hate
# mondays.", which reads as nonsense. The same for "honestly", "ugh", "jesus", "blimey", "omg"
# and a run of them ("oh god i forgot"). The words only go when a subject follows, so "thank god
# i got out", "oh no" and "oh the bus" keep every word they have.
EXCLAMATION_OPENS = frozenset("""god honestly ugh jesus christ blimey crikey cor gosh omg
    jeez sheesh oh ah""".split())

# The exclamations that are a phrase rather than a word: "oh my god i love it", "my god i love
# it". Read before the single words, or the "my" would look like the person's own and stay.
EXCLAMATION_PHRASE = re.compile(
    r"^(?:oh\s+my\s+god|my\s+god|good\s+grief|for\s+goodness'?\s*sake|"
    r"for\s+god'?s?\s*sake)\s+")

_EXCLAMATION_SUBJECTS = frozenset("""i im ive id ill we weve youre you he hes she shes they
    theyre it its my me your our""".split())


def without_a_leading_exclamation(clean):
    """The line without the exasperation it opens on: "god i hate mondays" is "i hate mondays".

    Public because the composer says a line back in its own words and works from the line as it
    was typed, not from `clean`: "god i hate mondays" came back as "Noted: god you hate mondays."
    """
    return _an_exclamation_in_front(clean)


def _an_exclamation_in_front(clean):
    """The line without the exasperation it opens on: "god i hate mondays" is "i hate mondays"."""
    for _ in range(3):
        phrase = EXCLAMATION_PHRASE.match(clean)
        if phrase:
            rest = clean[phrase.end():]
            if rest and rest.split(" ", 1)[0].strip(",.!?;:-|") in _EXCLAMATION_SUBJECTS:
                clean = rest
                continue
            return clean
        head, _, rest = clean.partition(" ")
        if not rest or head.strip(",.!?;:-|") not in EXCLAMATION_OPENS:
            return clean
        after = rest.split(" ", 1)[0].strip(",.!?;:-|")
        if after in _EXCLAMATION_SUBJECTS or after in EXCLAMATION_OPENS:
            clean = rest
            continue
        return clean
    return clean


def _an_exclamation_is_not_a_thing(clean):
    """The line without the surprise after a question word: "what on earth" is "what".

    "wtf" is expanded to "what" (lexicon.CHAT_SPEAK), which is the same repair from the other
    side: the question about the boiler, not a warning about the planet. This one holds for the
    phrase typed out - "what on earth do i do about my boiler".
    """
    return EXCLAIMED_AFTER_A_QUESTION.sub(r"\1", clean)


def strip_leaders(clause):
    """A clause without the filler it opens with."""
    start = 0
    while start < len(clause) - 1 and clause[start] in LEADERS:
        start += 1
    return clause[start:]

# The same rule for a line of text, for the readings that match a shape against the whole line and
# so never see past the filler. A child's name and age is read as a pair in "my daughters name is
# mia and shes 6", and behind a leader - "oh and my daughter is called mia", "and my sons called
# tom, hes 9" - not one of those shapes matched, because every one of them starts at "my". A
# leader can be stacked ("oh and", "so then"), so the rule is applied until it stops.
_LEADER_WORD = re.compile(r"^\s*([A-Za-z']+)\s*[,.;:!\-\u2014]*\s*")


def without_leaders(text):
    """The line without the filler it opens with: "oh and my son is 9" -> "my son is 9"."""
    said = str(text or "")
    while True:
        match = _LEADER_WORD.match(said)
        if not match or match.group(1).lower() not in LEADERS:
            return said
        rest = said[match.end():]
        if not rest.strip():
            return said
        said = rest


# A time word ends a place phrase: "when i was at the gym last week" says the gym, not the week.
_PLACE_STOP = frozenset("""last next this that yesterday today tomorrow tonight morning
    afternoon evening night week weekend month year hour minute monday tuesday wednesday
    thursday friday saturday sunday""".split())

# The words that put a place after them: a be-form ("i was in the garden") or a verb of going
# or starting ("it began at work").
_PLACE_LEADS = frozenset("""was were is am are been being s started starts began begins
    went go goes coming came got get stays stayed lived living working""".split())


# A question word opens a question of its own wherever it sits ("even after washing what helps"),
# so it ends the clause in front of it. A bare auxiliary does not: "when i was in the garden"
# holds one, and it is part of the clause, not the start of a new one.
_WH_QUESTIONS = frozenset("what why how when where who whose which".split())


def _clause_stop(norm, index):
    """The position just past the clause that opens at `index`.

    A clause ends where the next one may open: at a conjunction, or at a question of its own.
    "it started last summer after a picnic, what should i do" gives the picnic in the background
    and leaves the ask alone.
    """
    stop = index + 1
    while (stop < len(norm) and norm[stop] not in lexicon.CLAUSE_BREAKS
           and norm[stop] not in _WH_QUESTIONS):
        stop += 1
    return stop


def background_clause(norm):
    """The positions a clause saying WHEN or WHERE something happened takes up, or an empty set.

    A line that says when or where it happened gives that time or place in a clause of its own:
    "it started this morning when i was in the garden" is about whatever started. Only a clause
    with the line's own words before it counts; a line that opens on the subordinator asks about
    it ("when should i plant tomatoes"), a reporting verb in front of it makes it the thing being
    asked about ("no i mean where did i move from"), and a line with a subject of its own keeps
    its own clauses ("the garden flooded when it rained"). The clause stops where the next one
    opens, so it never covers an ask of its own ("my feet smell even after washing what helps").
    """
    norm = list(norm)
    for index, word in enumerate(norm):
        if not index or word not in lexicon.BACKGROUND_STARTS:
            continue
        if norm[index - 1] in REPORTING:
            continue
        return set(range(index, _clause_stop(norm, index)))
    return set()


# Words that open a clause giving the reason for the rest of the line. What is inside such a
# clause is why something happened, not what the line is about: "i cant sleep because my back
# hurts" is a sleep problem, and "my back has been killing me since i moved the sofa" is the back.
REASON_STARTS = frozenset("""because cause cos cus coz since""".split())


def reason_positions(norm):
    """The positions a clause giving the reason for the line takes up, or an empty set.

    Only a clause with the line's own words before it counts, so a line that opens on the
    subordinator ("since when do i need a licence") keeps its own reading.
    """
    norm = list(norm)
    for index, word in enumerate(norm):
        if not index or word not in REASON_STARTS:
            continue
        return set(range(index, _clause_stop(norm, index)))
    return set()


def background_positions(norm):
    """The positions in this line taken by words that only say WHERE it happened.

    Those words are not what the line is about: "it started at work in the garden centre" is
    about whatever started, not about the garden, and "it started this morning when i was in the
    garden" says the same with the place inside a when-clause. Only a place phrase counts - a
    preposition and the thing it introduces - so the rest of the clause keeps its meaning:
    "i get a rash when i eat strawberries" is a health line, and "how do i stop shaking before a
    talk" is about the talk.
    """
    norm = list(norm)
    skip = set()
    spans = []
    if norm[:1] == ["it"] and len(norm) > 1 and norm[1] in lexicon.START_VERBS:
        # A line that only reports when it began has no subject of its own, so every place in it
        # is where it happened: "it started at work in the garden centre". It stops where the
        # next clause opens, so a question after it keeps its own place.
        spans.append((0, _clause_stop(norm, 1), True))
    clause = background_clause(norm)
    if clause:
        spans.append((min(clause), max(clause) + 1, False))
    for start, stop, anywhere in spans:
        index = start
        while index < stop:
            if norm[index] not in lexicon.PLACE_PREPS:
                index += 1
                continue
            # In a when-clause a place follows a be-form or a verb of going or starting: "when i
            # was in the garden". "hand in my notice" and "what happens at security" have
            # something else in front of the preposition, so what follows is the thing acted on
            # or the thing happening, not a place.
            if not anywhere and index and not (norm[index - 1] in _PLACE_LEADS
                                               or index - 1 in skip):
                index += 1
                continue
            index += 1
            taken = 0
            while (index < stop and taken < 3
                   and norm[index] not in lexicon.CLAUSE_BREAKS
                   and norm[index] not in _PLACE_STOP
                   and norm[index] not in lexicon.PLACE_PREPS):
                skip.add(index)
                index += 1
                taken += 1
    return skip


# A clause that opens "how long", "how much", "how often" is the measure word of an ask, and the
# clause splitter keeps it on its own: "how long do they stay on" reads as two clauses, "how long"
# and "do they stay on". The ask is both halves - the measure word is the one that says which kind
# of answer is wanted - so `asking` puts them back together.


def _the_measure_clause(clause):
    """True for a clause that is only a measure word, with or without its noun.

    "how long", "how much water", "how many hours sleep": the second word is the measure, and
    whatever follows it inside the clause is the thing measured, so the whole clause belongs to
    the ask that comes after it. A leading "and" or "so" is a leader, not part of the measure:
    "and how long do they stay on" is the same ask as "how long do they stay on".
    """
    stripped = strip_leaders(clause)
    return len(stripped) > 1 and stripped[0] == "how" and stripped[1] in HOW_DEGREE


def _asking(clauses, focus):
    """The clause that asks, with the measure word it was said with.

    `focus` is the clause carrying the ask, and for "how long do they stay on" that is "do they
    stay on": the measure word sits in the clause before it. A reader that reads the ask - the
    shape of the answer, or the thing the question attaches to - needs the word that says which
    measure is wanted, or a how-long reads as a yes/no. So the measure clause in front of the
    focus is joined to it here, once, rather than by every reader of the ask.

    Nothing else is added: a line with no measure word gets its focus back unchanged.
    """
    if not focus:
        return []
    at = None
    for index, clause in enumerate(clauses):
        if clause is focus:
            at = index
            break
    if at is None:
        for index, clause in enumerate(clauses):
            if clause == focus:
                at = index
                break
    if at and _the_measure_clause(clauses[at - 1]):
        return list(clauses[at - 1]) + list(focus)
    return list(focus)


def _focus(clauses):
    """The clause that carries the ask: the last one that opens like a question, else the
    last one that asks for something, else the last one with something in it."""
    for clause in reversed(clauses):
        stripped = strip_leaders(clause)
        if stripped and stripped[0] in ASK_WORDS:
            return clause
    for clause in reversed(clauses):
        if any(token in WANT_WORDS for token in clause):
            return clause
    for clause in reversed(clauses):
        stripped = strip_leaders(clause)
        if stripped:
            return clause
    return clauses[-1] if clauses else []


# Letters that carry no accent mark to strip: people type them in words they know and they
# would otherwise cut the word in two ("smorrebrod", "aeble", "plain l").
LETTERS = str.maketrans({
    "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE", "ø": "o", "Ø": "O", "ł": "l", "Ł": "L",
    "đ": "d", "Đ": "D", "ð": "d", "Ð": "D", "þ": "th", "Þ": "TH", "ß": "ss", "ı": "i",
})


def _unaccent(text):
    """The same line with every accent mark taken off ("crème" -> "creme").

    A keyboard often cannot type the accent, and one that arrives by copy or by a foreign
    keyboard used to cut the word in two at the accent ("creme fraiche" typed with accents
    read as "cr me fra che"), so the word matched nothing and the line read as a shrug.
    NFKD splits a letter from its accent and the combining marks are dropped, for every
    script, not just the words we happen to know.
    """
    split = unicodedata.normalize("NFKD", text.translate(LETTERS))
    return "".join(char for char in split if not unicodedata.combining(char))


# "what on earth is happening" is a person asking about their own day, not a question about the
# planet: the phrase between the question word and the rest is an intensifier, and the word
# "earth" in it is not a thing the line is about. Read as a noun it was enough for the entry on
# the layers of the Earth to answer "what on earth" and "wtf" (which expands to "what on
# earth") with "a thin rocky crust, a hot slow-flowing mantle ...". The same goes for "how the
# hell do i unblock this" and "why in the world would i". Only the intensifier right after the
# question word is dropped, so "life on earth", "the biggest thing on earth" and "what on earth
# is the earth made of" keep every word they are about.
_INTENSIFIER = (r"on\s+earth|in\s+the\s+world|"
                r"the\s+(?:hell|heck|devil|blazes|dickens|fuck)")
WH_INTENSIFIER = re.compile(r"^\s*(?:" + _INTENSIFIER + r")\s*$")
WH_INTENSIFIER_LINE = re.compile(
    r"(?<![a-z'])\b(what|why|when|where|who|which|whose|how)\s+(?:" + _INTENSIFIER + r")\b",
    re.I)
WH_ANY = frozenset("what why when where who which whose how".split())


def intensifier_positions(norm):
    """Where the "on earth" / "the hell" in the line sits, as indices into `norm`.

    The noun in the phrase is not a thing the line is about, so the reading gives its place to
    the caller that keeps the words nothing answers on (`background`). Only the phrase right
    after a question word counts, so "life on earth" and "the biggest thing on earth" keep
    theirs.
    """
    positions = set()
    for index, word in enumerate(norm):
        if word not in WH_ANY:
            continue
        for size in (3, 2):
            phrase = norm[index + 1:index + 1 + size]
            if len(phrase) == size and WH_INTENSIFIER.match(" ".join(phrase)):
                positions.update(range(index + 1, index + 1 + size))
                break
    return positions


# The words of the surprise as the person typed them: "on", "earth" from "what on earth". The
# surprise is taken out of `clean` before the reading is built, so asking the reading where it
# was can only ever find the half that `clean` does not touch ("the hell", never "on earth").
_TYPED_SURPRISE = re.compile(
    r"(?<![a-z'])\b(?:what|why|when|where|who|which|whose|how|whatever|however|whoever|whenever)"
    r"\s+(?:" + _INTENSIFIER + r")", re.I)


def _the_surprise_typed(text):
    """The words of the surprise after a question word, as the line was typed.

    "what on earth is happening" and "what on earth's going on" both hand over "on" and "earth",
    with the clipped is taken off: the reading no longer holds the phrase, and a caller that
    wants to know which surprise the line used has nothing else to ask.
    """
    flat = re.sub(r"[^a-z']+", " ", text.lower().replace("\u2019", "'"))
    # "wtf" is the same surprise with the letters taken out, and the lexicon reads it as
    # "what", so the words are spelled out here before the phrase is looked for.
    flat = re.sub(r"\b(?:wtf|wth|wtaf)\b", "what on earth", flat)
    words = []
    for match in _TYPED_SURPRISE.finditer(flat):
        for word in match.group(0).split()[1:]:
            word = word[:-2] if word.endswith("'s") else word
            if word not in words:
                words.append(word)
    return words


def _without_the_intensifier(norm):
    """The reading with "on earth" / "the hell" taken out from after a question word.

    The words are not what the line is about, so every reader that matches English words gets
    the line without them: "what on earth is happening" is a question about the person's day,
    not about the planet.
    """
    out = []
    index = 0
    while index < len(norm):
        word = norm[index]
        if word in WH_ANY and index + 1 < len(norm):
            phrases = intensifier_positions(norm)
            if index + 1 in phrases:
                end = index + 1
                while end < len(norm) and end in phrases:
                    end += 1
                out.append(word)
                index = end
                continue
        out.append(word)
        index += 1
    return out


# The long word a clip doubles into, and what the line has to be about for that to be the
# meaning: "mon" is a mistyped moon in a line about the night sky, and a clipped mum anywhere
# else. "mon is coming over" and "mon and dad" are people; "the mon is bright tonight" is not.
_A_CLIP = {
    "mon": ("moon", frozenset("""moon moons full half crescent phase waxing waning eclipse
        lunar sky night tonight bright light lit shines shine rises rising stars""".split())),
}


def _a_clip_kept_only_with_its_cue(plain, norm, fixes, line):
    """The reading with a clip's repair taken back when the line names nothing it is about.

    The vowel class repairs "mon" to "moon" wherever it stands, and a line about a parent loses
    its subject to it. The repair is kept when any word of the line is a cue for the long word,
    and taken back - out of the plain line, the reading and the list of repairs - when none is.
    """
    bent = dict(fixes)
    for typed, (longer, cues) in _A_CLIP.items():
        if bent.get(typed) != longer or any(word in cues for word in line):
            continue
        fixes = [pair for pair in fixes if pair[0] != typed]
        plain = [typed if word == longer else word for word in plain]
        norm = [typed if word == longer else word for word in norm]
    return plain, norm, fixes


def _fix_auxiliaries(tokens):
    """A "bin" read as "been" gets the helper English needs: "he is been" is "he has been",
    "she been in hospital" is "she has been in hospital". Nothing else is touched: a "been"
    with a helper already ("has been", "have been") is left exactly as it is."""
    if "been" not in tokens:
        return tokens
    out = []
    for index, word in enumerate(tokens):
        if word == "been" and out:
            last = out[-1]
            if last in BE_FORMS:                      # "he is been" was a contraction of has
                out[-1] = "have" if (len(out) > 1 and out[-2] in PLURAL_SUBJECTS) else "has"
            elif last in PLURAL_SUBJECTS or last in THIRD_PERSON:
                # "how have you been" already has its helper, and a question puts the subject
                # between the two: nothing to add.
                before_it = out[-2] if len(out) > 1 else None
                if before_it not in HAVE_FORMS and before_it not in BE_FORMS \
                        and before_it not in MODAL_FORMS and before_it != "not":
                    out.append("have" if last in PLURAL_SUBJECTS else "has")
        out.append(word)
    return out


# The words people put after the thing they meant: a kiss, a "please", a laugh. None of them
# says what the line is about, and left in the line they cost the answer - "what can i put on a
# burn x", "can you help me please", "what time is it lol" all came back as the search hedge
# while the same line without the tag was answered, because every reader matches the words it
# expects and one extra word at the end is enough to miss. A line of nothing but tags keeps them
# ("x", "please", "lol" on their own), and a laugh only goes when the line already asks
# something, so "that was funny lol" is still a laugh.
TAG_WORDS = frozenset("""x xx xxx xo xxo xoxo mwah kisses""".split())
# A "please" is part of how the line is said, and the reading keeps it ("yes please" is not "yes",
# "table for 4 please" keeps its please): it only goes off a line that already asks something,
# where it is the tag on the end of the ask, not the whole of it.
TAG_PLEASE = frozenset("please pls plz pls.".split())
# The same tag said as thanks. It goes only off a line that already asks something and has
# three words of its own in front of it, so "i want to say thanks" keeps the word that is the
# whole point of the line while "can you help me thanks" is still the ask for help.
TAG_THANKS = frozenset("thanks thank cheers thx ty ta".split())
TAG_QUESTION_LEADS = frozenset("""what why how when where who which whose can could should
    would will is are do does did have has am was were may might shall""".split())
TAG_GUARD_BEFORE = frozenset("""a an the this that my your his her their our for of is are was
    were be been being with than to from called named call name letter mark spot sign cross tick
    size sized equals equal and or but not no""".split())


# A line can open by saying it is about something else: "changing subject, how do i stop my bin
# smelling", "different topic: my boiler is leaking". The announcement is about the conversation,
# not about the thing being asked, and read as words it is about something: "subject" is a school
# word, so the bin was answered with the university entry requirements and "change of subject, my
# boiler is leaking" was a school line. It comes off only when the person set it off as its own
# clause (a comma, colon or dash after it) and the line goes on to say something - "changing
# subject at a-level, is it too late" keeps it, because that subject is the thing being asked
# about, and "changing subject" on its own is the whole line.
CHANGE_OF_SUBJECT = re.compile(
    # up to two of the words people start a turn with, with or without their comma: "and changing
    # subject, ...", "so anyway, change of topic, ...", "now, on a different tack, ...".
    r"^(?:(?:and|so|but|oh|ok|okay|right|now|anyway|anyways|also|plus|well)\s*,?\s*){0,3}"
    r"(?:"
    # "changing subject", "change of topic", "changing the tack"
    r"(?:changing|change\s+of|changing\s+the)\s+(?:the\s+)?(?:subject|topic|tack)"
    # "moving on to a different subject", "on to a different topic", "onto another tack"
    r"|(?:moving\s+on\s+to|on\s+to|onto|on|to)\s+(?:a\s+)?(?:new|different|another)\s+"
    r"(?:subject|topic|tack)"
    # "moving on to something else" says the same thing without naming a subject
    r"|(?:moving\s+on\s+to|on\s+to|onto)\s+something\s+else"
    # a bare "moving on" - nobody means the walking when they put a comma after it
    r"|moving\s+on"
    # "new topic", "different subject", "another tack"
    r"|(?:a\s+)?(?:new|different|another)\s+(?:subject|topic|tack)"
    r")"
    r"\s*[,;:.\u2013\u2014-]+\s*(?=\S)")


def _change_of_subject_off(clean):
    """The line without the clause that only announces a change of subject, and whether it went."""
    seen = CHANGE_OF_SUBJECT.match(clean)
    if not seen:
        return clean, False
    rest = clean[seen.end():]
    if len(RAW_WORD.findall(rest)) < 2:
        return clean, False       # nothing after the announcement but a word or two: keep both
    return rest, True


def _without_a_tag_at_the_end(clean):
    """`clean` without the tags at its end, and the tags that came off."""
    words = str(clean or "").split()
    asks = bool(words and words[0].strip(".,!?") in TAG_QUESTION_LEADS) or "?" in clean
    dropped = []
    while len(words) > 1 and words[-1].strip(".,!?") in TAG_WORDS:
        if words[-2].strip(".,!?") in TAG_GUARD_BEFORE:
            break
        dropped.insert(0, words.pop())
    while len(words) > 1 and words[-1].strip(".,!?") in TAG_PLEASE and asks:
        dropped.insert(0, words.pop())
    while len(words) > 1 and words[-1].strip(".,!?") in lexicon.LAUGHTER and asks:
        dropped.insert(0, words.pop())
    while len(words) > 3 and words[-1].strip(".,!?") in TAG_THANKS and asks:
        dropped.insert(0, words.pop())
    return " ".join(words), dropped


# A line that asks how a word is spelt is about the spelling of it, not about the thing it names.
SPELLING_ASK = frozenset("spell spells spelling spelt spelled misspelt misspelled pronounce".split())


# The endings that make one spelling another form of the same word. A line that puts two of
# them either side of "or" is asking which spelling is right, whether or not the pair is a
# repair: "is it definately or definite" offers "definite" against the slip, and "definite" is a
# word of its own, so only the shape of the two words can tell that the line is about spelling.
SPELLING_ENDINGS = ("ly", "ness", "ing", "ed", "es", "s", "d", "e")


def _spellings_of_one_word(one, other):
    """True when these two words are spellings or forms of the same word."""
    if not one or not other:
        return False
    if one == other:
        return True
    short, longer = (one, other) if len(one) <= len(other) else (other, one)
    if len(short) < 4 or not longer.startswith(short):
        return False
    return longer[len(short):] in SPELLING_ENDINGS


# A spelling question that names letters rather than spellings: "is it definately with an a or
# an e", "is it definately with one f or two", "is neccessary one c or two", "definately with a
# double f". These are the same question as "is it definately or definitely" asked the way
# people ask it, and none of them carries a word of SPELLING_ASK, so the repair took the answer
# away: "is neccessary one c or two" was told "Two. I'd take that and not think about it again."
# A letter stands for itself only next to a count ("with one f", "one c or two") or "double",
# which is the shape that separates it from "with a cold" and "a size m".
NAMED_LETTER = re.compile(
    r"\b(?:with\s+(?:an?|one|two|three|double)\s+[a-z](?![a-z])"
    r"|(?:one|two|three|a\s+double)\s+[a-z](?![a-z])\s+or\s+(?:one|two|three|an?)\b"
    r"|double\s+[a-z](?![a-z])\b"
    r"|[a-z](?<![a-z])\s+or\s+(?:two|three)\b)")


def _names_a_letter_beside_a_slip(words, fixed):
    """True when the line names a letter a few words from a slip it repaired."""
    if not fixed:
        return False
    for at, word in enumerate(words):
        if word not in fixed:
            continue
        near = " ".join(words[max(0, at - 4):at + 5])
        if NAMED_LETTER.search(near):
            return True
    return False


# The words that come before and after a short chat form when it is being named as a letter
# rather than said as a word: "the letter u is silent", "u turn", "what u's are there", "a u-boat".
_A_SHORT_WORD_IS_NAMED_BEFORE = frozenset((
    "letter", "letters", "word", "words", "vowel", "consonant", "initial", "alphabet", "grade",
    "grade", "type", "blood", "vitamin", "plan", "shape", "u", "the",
))
_A_SHORT_WORD_IS_NAMED_AFTER = frozenset((
    "turn", "turns", "turn-", "boat", "boats", "bend", "shaped", "shape", "tube", "value", "values",
))


def _a_short_word_named(short, before, after):
    """True when a short chat form is being named, not said: "a u turn", "the letter u".

    "u" is both the chat form of "you" and a letter with its own words around it, and the two
    are told apart by what stands beside it: "do a u turn", "the letter u is silent", "a u-boat",
    "what u's do i need for the exam". Everything else is the word: "how r u", "what are u
    reading", "how do i write a thank u letter".
    """
    if before in _A_SHORT_WORD_IS_NAMED_BEFORE or after in _A_SHORT_WORD_IS_NAMED_AFTER:
        return True
    return after is not None and after.endswith("'s") and short == "u"


def _asks_the_spelling(words, fixed):
    """True when the typed spelling is what the line is asking about, so it is not put right.

    Two shapes carry it, and both name the slip as the subject:

    - the question is about spelling at all: "how do you spell recieve", "how do i spell
      embarased". The spelling answers are reached from the word as it was typed, so a repaired
      word is a word they can no longer see.
    - the line offers two spellings of one word: "is it definately or definitely", "which is
      right, seperate or separate". Only a repair with the other spelling beside it counts, so
      "im tiered or just bored" is still read as tired.
    """
    if not fixed:
        return False
    if any(word in SPELLING_ASK for word in words):
        return True
    if _names_a_letter_beside_a_slip(words, fixed):
        return True
    for at, word in enumerate(words):
        if word != "or":
            continue
        before = words[at - 1] if at else ""
        after = words[at + 1] if at + 1 < len(words) else ""
        if before in fixed and after in (fixed[before], before):
            return True
        if after in fixed and before in (fixed[after], after):
            return True
        # ... or the two words are forms of one word, so "is it definately or definite" is the
        # same question as "is it definately or definitely" and keeps the slip it asks about.
        if before in fixed and _spellings_of_one_word(fixed[before], after):
            return True
        if after in fixed and _spellings_of_one_word(fixed[after], before):
            return True
    return False


# A clause that gives the owner of the day and leaves the day itself out. "its not my birthday its
# my mums" names the day once and then says whose it is, and the second clause has nothing in front
# of a day word, so every reader that looks for a relation before the day finds none and the line
# reads as the person's own day: "Happy birthday when it comes" to somebody who has just said it is
# their mum's. The day word is put back where the person left it out, and the relation is then read
# by the readers that already work - the same line with "my mums birthday" in it is greeted right.
DAY_NAMED = re.compile(r"\b(birthday|anniversary|wedding)s?\b", re.I)
OWNER_WITHOUT_THE_DAY = re.compile(
    r"\b(?:it|its|it's|that|thats|that's)(?:\s+is)?\s+(?:not\s+)?(?:my|our)\s+([a-z]+'?s)\b",
    re.I)
# What may follow the owner and still leave the day out: the end of the clause, or when it is. A
# word that the owner owns ("its my mums fault") is the day, and is left alone.
TAIL_OF_A_DAY = frozenset("""
    tomorrow today tonight soon next this on in at already too as well then
""".split())


# "can not" is the same word as "cant": the apostrophe is off and the words are apart, and the
# reading kept them apart, so a card keyed on "cant sleep" ("i cannot sleep" reaches it) missed
# the way most people type it - "i can not sleep" fell through to a pool about bad nights. The
# knowledge entries write both spellings, so the one-word form is the one nothing loses.
CAN_NOT = re.compile(r"\bcan\s+not\b")


def _can_not_as_one_word(clean):
    """The line with a "can not" typed as two words written as the one word "cant"."""
    return CAN_NOT.sub("cant", clean)


def _the_day_left_out(text):
    """The same line with the day's name put back in the clause that only names its owner."""
    named = DAY_NAMED.search(text)
    if not named:
        return text
    day = named.group(1).lower()
    pieces = []
    last = 0
    for found in OWNER_WITHOUT_THE_DAY.finditer(text):
        if found.start() < named.end():
            continue
        tail = re.split(r"[,.;:!?]", text[found.end():], 1)[0].split()
        if any(word.lower() not in TAIL_OF_A_DAY for word in tail):
            continue
        pieces.append(text[last:found.end()])
        pieces.append(" " + day)
        last = found.end()
    if not pieces:
        return text
    pieces.append(text[last:])
    return "".join(pieces)


# The same day read the other way round: the clause that says whose day it is comes first and the
# one that says it is not the speaker's comes last. "its my sons 5th not my birthday" and "our nans
# 80th is saturday not my birthday" both got "Happy birthday when it comes" - the greeting for the
# speaker - because the day word stands in the negated clause at the end and the number that says
# whose it is is only a number. The day belongs to the person named before it, so the name goes
# back onto their number and the clause that denies it is the speaker's comes off.
A_NUMBER_OF_SOMEONES_DAY = re.compile(
    r"\b(?:my|our)\s+([a-z]+\'?s?)\s+(\d+(?:st|nd|rd|th))\b", re.I)
NOT_MY_OWN_DAY = re.compile(
    r"\s*(?:,?\s*\b(?:and\s+)?not\s+(?:my|mine)\s+"
    r"(birthday|bday|anniversary|wedding)\b)", re.I)


def _a_day_named_as_not_mine(text):
    """The same line with the day moved onto the person the clause before it named."""
    negated = NOT_MY_OWN_DAY.search(text)
    if not negated:
        return text
    day = negated.group(1).lower()
    owner = None
    for found in A_NUMBER_OF_SOMEONES_DAY.finditer(text[:negated.start()]):
        if found.group(1).lower().rstrip("s") in KIN:
            owner = found
    if owner is None:
        return text
    # Only the clause that denies the day is taken off: what follows it still says when the day
    # is ("its my daughters 3rd not my birthday on saturday" keeps the saturday).
    whole = text[:owner.end()] + " " + day + text[owner.end():negated.start()] + text[negated.end():]
    return " ".join(whole.split())
# "is it ok to eat rice thats been in the fridge 3 days" is one question: the thing has already
# been kept, and how long it has been kept is the whole point. The words that say so are the place
# it sat in and the time it sat there, and neither of them is the subject - the food is. Rows that
# answer what to cook with what is left ("leftover rice" is the fried-rice recipe), what a warm pot
# may do ("rice" and "in the fridge" is the cooling row) or what the date on a bag is worth
# ("rice" and "ok to eat" is the dry-rice row) each read one of those words as their own, so each
# was answering a keeping question. The pair is read once here and a row can stand down on it.
_KEEPING_PLACES = frozenset((
    "fridge", "fridgefreezer", "refrigerator", "freezer", "cupboard", "larder", "pantry",
    "worktop", "counter", "countertop", "out", "outside", "coolbox", "coolbag", "bag"))
# A thing that has already been kept somewhere, named without the place: "can i eat leftover rice
# after 3 days" is the same question as the fridge line, and says "leftover" instead of "fridge".
_KEPT_THINGS = frozenset((
    "leftover", "leftovers", "cooked", "uneaten", "spare", "rest", "remains", "opened"))
_DAY_WORDS = frozenset((
    "day", "days", "night", "nights", "week", "weeks", "month", "months"))
_KEPT_ALREADY = frozenset(("overnight", "yesterday", "since"))
_SMALL_NUMBERS = frozenset((
    "a", "an", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "couple", "few", "several", "many", "half"))
_NUMBER_SHAPE = re.compile(r"^\d{1,3}(?:st|nd|rd|th)?$")


def _a_number(word):
    """True for "3", "2nd", "two", "a few" - the number in front of the day words."""
    return bool(_NUMBER_SHAPE.match(word)) or word in _SMALL_NUMBERS


def _kept_for(flat):
    """{"place", "time"} when the line says a thing has already been kept, else None.

    The place is the word the thing sat in ("fridge", "cupboard", "out") or None when the line
    names only the thing that was kept ("leftover rice after 3 days"). The time is the phrase
    that says how long ("3 days", "overnight", "since monday"). A line with a time and no place
    and no kept thing is not this reading: "i start my new job in 3 days" is a date.
    """
    if not flat:
        return None
    time = None
    at = None
    for index, word in enumerate(flat):
        if index + 1 < len(flat) and _a_number(word) and flat[index + 1] in _DAY_WORDS:
            time, at = "%s %s" % (word, flat[index + 1]), index
            break
        if word in _KEPT_ALREADY:
            after = flat[index + 1] if index + 1 < len(flat) else ""
            time = (word + " " + after).strip() if word == "since" and after else word
            at = index
            break
    if time is None:
        return None
    place = None
    for index, word in enumerate(flat):
        if word in _KEEPING_PLACES:
            # "a bag of rice in the cupboard for 3 months" is the bag's date, and the bag is the
            # thing the line is about rather than where it was kept, so it is not this reading.
            place = word
            break
    if place is not None:
        if abs(at - index) <= 10:
            return {"place": place, "time": time}
        return None
    if _KEPT_THINGS.intersection(flat):
        return {"place": None, "time": time}
    return None


def _only_doubles_a_letter(typed, mended):
    """True when the repair puts back a copy of a letter the person typed once.

    People do type one of a doubled letter ("recomend", "hapened") and the corrector puts it
    back, but the same guess is how a word becomes a different word: "mons" was read as "moons",
    "thres" as "threes" and "moning" as "mooning". A vowel put back where the line has three
    consonants in a row ("wndow", "kittn", "brdge") is a shape no English word has, so that
    repair is one the reader can be sure of; a doubled letter is a letter the person may never
    have meant, so it is left to `plain` and the word the readers match on stays as it was typed
    unless a misspelling list vouches for it.
    """
    if len(mended) != len(typed) + 1:
        return False
    return any(mended[at] == mended[at + 1] and mended[:at] + mended[at + 1:] == typed
               for at in range(len(mended) - 1))


def normalise(text):
    """{"text", "clean", "words", "plain", "norm", "norm_text", "fixes", "clauses", "focus",
    "asking", "signals"} for one line.

    "plain" is the line as it was typed with each word repaired in place - the same order, the
    same punctuation, no clause splitting - so a reader that matches on words gets the spelling
    the writer meant without losing anything else. "norm" is the fuller reading: clauses split,
    chat-speak and contractions expanded, digits read out.
    """
    text = text if isinstance(text, str) else ""
    # "isit ok to eat this" is "is it ok to eat this": a glued question opener is put right in
    # the line as typed, before the words are read, so `clean` and `words` carry the two words
    # the readers match on rather than one word no English line has. A capital is a name's, so a
    # token with an upper-case letter is never split ("Didi" is a person, not "did i").
    clean = _glued_said_apart(" ".join(_unaccent(text).split()))
    clean = _typed_without_spaces(clean)
    # "i d k" and "o m g": somebody typing with one hand puts a space between every letter, and
    # nothing read those runs, so `i d k` became "i'd k" from the two pieces "i d" and reached no
    # card at all. It goes in here, before the short spellings are repaired, because "i d" is
    # repaired into "i'd" further down and the pieces are gone by then.
    clean = _said_apart_as_one_word(clean)
    clean = _the_mrs_is_the_wife(clean)
    clean = " ".join(clean.lower().split())
    # A "can not" typed as two words is the one word "cant": the cards are keyed on the short
    # spelling ("the things that work" for sleep) and every entry writes both, so the line that
    # splits it missed all of them. It goes in before the chat-speak is spelled out, so a word
    # that stands for "can not be bothered" keeps the two words the phrase readers match on.
    clean = _can_not_as_one_word(clean)
    clean = _the_day_left_out(clean)   # "its my mums" is "its my mums birthday"
    clean = _a_day_named_as_not_mine(clean)   # "my sons 5th not my birthday" is his, not mine
    clean = THOUSANDS.sub(r"\1", clean)   # "1,500" is a number, not two numbers
    clean = THOUSANDS_SAID_WITH_A_SPACE.sub(   # "1 500" is one number too
        lambda m: m.group(1) + m.group(2).replace(" ", "").replace("\u00a0", ""), clean)
    clean = _one_word_food(clean)          # "chick peas" is the one word the kitchen knows
    clean = _a_leading_like_is_a_filler(clean)
    clean = _joined_words(clean)           # "fedup" is the two words the fed-up reader knows
    clean = _a_contraction_typed_with_a_space(clean)   # "she s 84" is "shes 84"
    clean = _an_exclamation_in_front(clean)         # "god i hate mondays" is "i hate mondays"
    clean = _an_exclamation_is_not_a_thing(clean)   # "what on earth" is "what"
    clean = _a_hello_said_short(clean)     # "gm" is "good morning", "mornin" is "morning"
    clean = _chat_words_said_out(clean)    # "wanna" is "want to" for the words a reader matches
    clean = _an_ill_that_is_i_will(clean)  # "ill go with the train" is "i will", not an illness
    clean, tags_at_the_end = _without_a_tag_at_the_end(clean)
    clean, change_of_subject = _change_of_subject_off(clean)
    # A price typed with a sign is a price, and the sign is not a word: "i have £20 until friday"
    # was read as "i have 20 until friday", so no row that matches on a money word saw the money,
    # while the same line typed as "i have 20 pound until friday" was answered about it. The
    # figure keeps the word people say in `words`, `plain` and `norm`, and `clean` stays the line
    # as it was typed, because the readers that want the sign itself ("£250 is how much a month")
    # find it there.
    clean, words = _a_meal_word_misspelt(clean, RAW_WORD.findall(clean))
    clean, words = _docs_doctor(clean, words)
    said = _a_sign_is_a_word(clean)
    words = RAW_WORD.findall(said)
    fixes = []
    norm = []
    plain = []
    fixed = {}
    subject_put_back = False
    sentence_ends = SENTENCE_END.sub(" | ", _phrase_pass(said))
    tokens = TOKEN.findall(PUNCT_BREAK.sub(" | ", sentence_ends))
    joined = _one_relation_says(
        a_son_not_the_sun(a_sor_bit_is_sore(
            loose_is_lose(possessive_me(_said_apart(_join_chat_digits(tokens)))))))
    joined, slips = _a_slip_that_is_a_word(joined)
    for typed, meant in slips.items():
        # The word meant is the word the readers get: `words` is handed to the knowledge base,
        # and `clean` keeps the line as it was typed, which is what a reply quotes.
        fixes.append((typed, meant))
        fixed[typed] = meant
    for index, word in enumerate(joined):
        before = joined[index - 1] if index else None
        after = joined[index + 1] if index + 1 < len(joined) else None

        if ((before is None or before == "|"
             or (before in LEADERS and _only_leaders_before(joined, index)))
                and word in DROPPED_SUBJECT_AUX
                and subject_missing([word] + _lookahead(joined, index), 0)):
            # "am off to bed" -> "i am off to bed". The typed word stays as it was in `plain`:
            # nothing was misspelt, the subject was left off.
            norm.extend(["i"] + _token(word, fixes, before))
            plain.append(word)
            subject_put_back = True
            continue
        after_after = joined[index + 2] if index + 2 < len(joined) else None
        before_before = joined[index - 2] if index >= 2 else None
        if _a_name_slot(before, before_before, word):
            # A name goes in as it was typed, and the plain line with it, so an echo says the
            # name back the way it was given.
            norm.append(word)
            plain.append(word)
            continue
        before_words = joined[max(0, index - 5):index]
        after_words = joined[index + 1:index + 4]
        verb = _a_core_verb_typed_wrong(word, before, after)
        if verb:
            # A verb typed with a letter out of place is the verb they typed, and the readers get
            # it: a repair is only handed on in `words` when it is recorded here, and the line as
            # typed stays the line a reply quotes.
            fixes.append((word, verb))
            fixed[word] = verb
        for spelled in ([verb] if verb else
                        _positional_word(word, before, after, after_after, before_before,
                                         before_words)):
            parts = _token(spelled, fixes, before, before_before, after,
                           before_words=before_words, after_words=after_words)
            # "i dunno" carries its own "i", and "the the" is a slip: a word a line never says
            # twice is dropped, and "very very tired" keeps both because people mean it.
            if parts and norm and parts[0] == norm[-1] and parts[0] in REPEAT_ONCE:
                parts = parts[1:]
            elif (len(parts) > 1 and norm and parts[0] == "i"
                  and parts[1] == "do" and norm[-1] in REPEAT_ONCE_SUBJECTS):
                parts = parts[1:]        # "u dunno" is "you do not know", not "you i do not know"
            if not parts:
                continue
            norm.extend(parts)
            # A repair goes into the plain line; an expansion ("don't" -> "do not", "2" -> "two")
            # does not, so the line reads as it was typed apart from the words that were wrong.
            # An American spelling is not a slip, so `plain` keeps the spelling they used.
            if len(parts) > 1 and spelled in lexicon.PLAIN_EXPANDS:
                # A chat word that is not a word at all, whose repair is two words the readers
                # match on: the plain line carries it too, or a reader that looks for the phrase
                # never sees it.
                plain.append(" ".join(parts))
            elif (len(parts) == 1 and spelled not in DIGIT_WORDS
                    and spelled not in lexicon.US_SPELLINGS):
                plain.append(parts[0])
                # Only a word the tables put right is the word the readers are given. The
                # corrector guesses at the rest - it reads "blink" as "blank" - and a guess is
                # not good enough to hand the knowledge base in place of what was typed.
                if parts[0] != spelled and (spelled in lexicon.MISSPELLINGS
                                            or spelled in lexicon.URGENT_MISSPELLINGS
                                            or (spelled in lexicon.SAID_SHORT
                                                and not _a_short_word_named(spelled,
                                                                           before, after))):
                    fixed[spelled] = parts[0]
                elif spelled != word and word in lexicon.STATES_WITHOUT_G:
                    # The g this pass put back is a repair, and the word the knowledge base is
                    # handed carries it: "how long can i go without eating, im starvin".
                    fixed[word] = spelled
                elif word == "bin" and parts[0] == "been":
                    # A "bin" the frame made into "been" is the word the knowledge base is handed,
                    # for the same reason as a spelling put right: the rows key on words, and one
                    # keyed on "bin" answers a line about a sick cat with a pet that has been in
                    # the washing machine ("cats bin sick twice 2day" got "towel him dry right
                    # through"). The noun keeps its word: "the bin needs emptying", "my dog fell
                    # in the bin" and "bin day" never get here, because the frame in front of the
                    # word is the whole of the test above.
                    fixed[word] = parts[0]
            else:
                # A chat-spelled contraction is a spelling slip, not an expansion: the plain line
                # gets "couldnt" for "cudnt", which is the spelling the modules match on. Only
                # the reading keeps the words apart ("could not").
                plain.append(lexicon.TYPED_CONTRACTIONS.get(spelled, spelled))
    norm = _fix_auxiliaries(_says_has(norm))
    # "on earth" and "the hell" are kept out of the reading and named in `intensifier`, because
    # a knowledge entry keyed on "earth" answered "what on earth is happening" with the layers
    # of the planet. They are still in `text` and `clean`, so nothing is lost from the line.
    intensifier = _the_surprise_typed(text)
    # What the line still holds is a different question: "on earth" is taken out of `clean`
    # before the reading is built, so a lookup that drops the surprise from its words must only
    # drop the half the line still has ("the hell"), or "what on earth is the earth made of"
    # loses the planet and gets a shrug.
    intensifier_left = [norm[index] for index in sorted(intensifier_positions(norm))]
    if not intensifier:
        intensifier = list(intensifier_left)
    if intensifier_left:
        norm = _without_the_intensifier(norm)
    # A misspelt part of the body is settled once, here, so the topic rule, the part the composer
    # keeps a pool of lines for, and every module that matches on words all read the same part.
    norm, words = _a_game_named_another_way(norm, words)
    norm = _parts_that_hurt(norm, fixes)
    if any(word in lexicon.PAIN_WORDS for word in norm):
        # The plain line carries the repairs the reading made, or a reader matching on words
        # never meets the part: only the words already settled above are put back.
        mended = dict(fixes)
        plain = [mended.get(word, word) for word in plain]
    # A three-letter word that is also the clip of an everyday one ("mon" for mum) is bent into
    # the longer word by the vowel class: "mon and dad" was read as "moon and dad", and a
    # clipped mum is far commoner than a mistyped moon. The moon is worth reading where the line
    # is about it, and only the line can say so, so the repair is kept only when a cue for the
    # long word stands somewhere in it.
    plain, norm, fixes = _a_clip_kept_only_with_its_cue(plain, norm, fixes, joined)
    clauses = _split_ask(_repair_openers(_clauses(norm), fixes))
    flat = [word for clause in clauses for word in clause]
    focus = _focus(clauses)
    asking = _asking(clauses, focus)
    signals = {
        "question_mark": "?" in text,
        "shout": sum(1 for w in text.split() if len(w) > 2 and w.isupper()) > 0,
        "laughter": any(lexicon.is_a_laugh(w) for w in norm + tags_at_the_end)
                    or bool(re.search(r"\b(?:ha\s*){2,}|\b(?:heh\s*){2,}", text)),
        "ellipsis": "..." in text or ".." in text,
        "exclamation": "!" in text,
        "empty": not words,
    }
    # The one line where a slip must stay a slip is the line that asks about the spelling itself:
    # "is it definately or definitely" and "how do you spell recieve" name the typed spelling as
    # the thing they want an answer about, and the spelling answers are reached from that
    # spelling. Handing the readers the repaired word instead took six such questions away.
    keep = _asks_the_spelling(words, fixed)
    # Every repair this pass made, whichever part of it made it: the token pass and the part of
    # the body settle their repairs in `fixes`, and `fixed` held only the ones a misspelling list
    # knew. A reader matching on `words` met the slip and not the word it meant ("my wndow wont
    # shut" reached the cupboard catch on "shut", never the window), so the repairs are collected
    # here once rather than in the one dict a single pass fills.
    settled = dict(fixed)
    for typed, mended_word in fixes:
        if typed != mended_word and " " not in mended_word \
                and (typed in fixed or not _only_doubles_a_letter(typed, mended_word)):
            settled.setdefault(typed, mended_word)
    return {
        "text": text,
        "clean": clean,
        # The words a line is read by are the words it meant: a spelling this pass put right is
        # the word the reader gets ("how do i cook qinuoa properly" is about quinoa). `clean`
        # keeps the line as it was typed, which is what a reply quoting the person reads.
        "words": list(words) if keep else [settled.get(word, word) for word in words],
        "plain": re.sub(r"\s*\|", ",", " ".join(plain)).strip(" ,"),
        "norm": flat,
        "norm_text": " | ".join(" ".join(clause) for clause in clauses) if clauses else "",
        "fixes": dict(fixes),
        "intensifier": intensifier,
        "intensifier_left": intensifier_left,
        "clauses": clauses,
        "focus": focus,
        # The ask as it was said, measure word and all: see `_asking`.
        "asking": asking,
        "signals": signals,
        "dropped_subject": subject_put_back,
        "change_of_subject": change_of_subject,
        "kept": _kept_for(flat),
    }


# "Sick with worry" is a figure of speech, and the only illness in it is the word "sick".
# Read as a symptom it earns "rest, warm drinks and an early night" for a person who is
# frightened about an exam, and "keep them home with drinks in small sips" for a child who is
# worried about school - advice for a bug nobody has. The feeling after "with" is what the word
# is doing, so the phrase is read as the feeling it stands for and the line goes on to the pool
# that answers feelings: "worried about my exam", "nervous", "guilty". A bug named in the same
# line ("sick with a bug going round", "sick with the flu") is not a feeling and keeps its illness.
# The word carrying the symptom is not always "sick": "im nauseous with worry", "shaking with
# nerves" and "ill with guilt" are the same figure of speech, and read as the body they begin
# with they earn the stomach-bug answer for a person who is frightened.
SICK_AS_FEELING = re.compile(
    r"\b(?:sick|ill|unwell|nauseous|nauseated|queasy|shaking|shaky|trembling|dizzy)"
    r"\s+(?:(?:with|from)\s+)?"
    r"(worry|worrying|worried|stress|stress(?:ed)?\s+out|fear|fright|frightened|panic\w*|"
    r"nerves|nervous|anxious|anxiety|guilt\w*|grief|shame|ashamed|dread\w*|anger|rage|"
    r"jealousy|it\s+all)\b",
    re.I)
# One feeling word back for every phrase the person used, because the pools read the adjective
# ("worried about a person" and "worried about a thing" are different pools) and not the noun.
_FEELING_WORD = {
    "worry": "worried", "worrying": "worried", "worried": "worried", "stress": "stressed",
    "stressed out": "stressed", "stressed": "stressed", "fear": "frightened",
    "fright": "frightened", "frightened": "frightened", "panic": "panicky",
    "panicking": "panicky", "panicky": "panicky", "nerve": "nervous", "nerves": "nervous",
    "nervous": "nervous", "anxious": "anxious", "anxiety": "anxious", "guilt": "guilty",
    "guilty": "guilty", "grief": "grieving", "shame": "ashamed", "ashamed": "ashamed",
    "dread": "dreading", "dreading": "dreading", "anger": "angry", "rage": "angry",
    "jealousy": "jealous", "it all": "overwhelmed",
}
# "worried sick", "scared sick", "bored sick" put the feeling in front: the word after it is
# the feeling, and "sick of" there is the same figure of speech, not an illness.
FEELING_BEFORE_SICK = re.compile(
    r"\b(?:worried|scared|frightened|terrified|bored|stressed|anxious)\s+sick\b", re.I)


def _the_feeling_word(match):
    said = " ".join(match.group(1).lower().split())
    return _FEELING_WORD.get(said, "upset")


def without_the_figure_of_speech(clean):
    """`clean` with "sick with worry" read as the feeling it stands for, for the body readers."""
    clean = FEELING_BEFORE_SICK.sub(lambda m: m.group(0).split()[0], str(clean or ""))
    return SICK_AS_FEELING.sub(_the_feeling_word, clean)


# "sugar" is two things: what goes in the tea and what the body runs on. The rest of the line says
# which, and only one of them is a health line: "my sugar was low last night" is a hypo, and it
# was read as the kitchen ("I'm listening - say more if it helps", or "cut the sugar you drink"
# for "my sugar keeps dropping at night"), while the same line with "blood" in it got the answer.
# A word of the level after "my sugar" is what says the body is meant, so that is what the whole
# engine reads, and a line that says "add", "a cup" or "brown" still means the bag in the cupboard.
SUGAR_LEVEL = frozenset("""low high dropped drop drops dropping crashed crash crashes crashing
    dipped dip dips dipped levels level reading readings rises rose rising spike spiked spiking
    fell falls falling down up""".split())
# "rose" is the one level word that is a thing as well: "my sugar rose collapsed" is the icing
# flower on a cake. It counts as a level only where it is the verb of the reading - followed by
# "to", "from", "after" and the like, or by nothing at all ("my sugar rose") - and not where a
# noun follows it.
SUGAR_AFTER_ROSE = frozenset("""to from after again overnight during before since sharply
    steadily quickly suddenly a bit so very high low all above around past 6 7 8 9""".split())
# A price or an amount of the stuff says the line is about the shopping, not about a meter: "my
# sugar went up in price", "my sugar dropped in price", "went up a pound", "down to one bag". It
# says that beside any level word, not only "up" and "down", because a price is not a reading
# whichever way it is said to have moved. And it has to sit where the level word would be followed
# by a linking word or a number, so "my sugar is up a bit", "up a lot" and "up the other day" -
# which are how people say how far the reading moved - keep it.
#
# "nothing" is deliberately not here. It is not a price: a diabetic whose sugar is "down to
# nothing" is describing the meter, and that line is a low that gets the emergency answer
# (polite-ruler, #4222). The shopping's "nothing left" is covered by the shop words around it.
SUGAR_PRICE = frozenset("""price prices cost costs pound pounds lb lbs kilo kilos bag bags packet
    packets tin tins gram grams spoon spoons teaspoon teaspoons""".split())
# Five words of tail, so "down to one bag" and "levels are down to a tin" are both in view.
# A price written in figures: "90p", "50p", "£2", "£1.50". The pence and the pound sign are what
# make it a price rather than a meter reading.
SUGAR_PRICE_SHAPE = re.compile(r"^(?:[£$€]|\d+(?:\.\d+)?p(?:ence)?$)", re.I)
# The tail takes a currency sign as well: "down to £1.50" is the price, and a tail that stopped at
# the sign read the "down" and called it a meter reading.
SUGAR_FIRST_PERSON = re.compile(
    r"\b(my|his|her|their|your)\s+sugar\b((?:\s+[a-z0-9'£$€]+){0,5})", re.I)


# A part of the body is not only said to hurt. People say how badly it is going in the words of
# a bad day instead - "my back is a joke today", "my knees are a nightmare", "my ankle is a
# mess", "my back is terrible" - and every reader that knows the part waits for a word of pain
# it never sees, so those lines fell through to "I'm sorry - that's frustrating" while "my back
# hurts" got the answer. The body readers already agree on what a word of pain is
# (`lexicon.PAIN_WORDS`) and on the parts (`lexicon.BODY_PARTS`), so the saying is read once
# here as the plain complaint it stands for, before anything reads the line.
#
# Only a part the person owns, with a be-word between it and the saying: "the back of the house
# is a mess" is the house, because "back" is followed by "of" rather than by the be-word, and a
# thing that is not a part of the body ("my sleep is a mess", "my hair is a nightmare") keeps
# the reading it has, which the knowledge base already answers.
BAD_SAYING = (r"(?:an?\s+|such\s+an?\s+|one\s+big\s+"
              r"|an?\s+(?:complete|right|total|proper|real|absolute|utter|bit\s+of\s+a|bloody)\s+)?"
              r"(?:joke|nightmare|mess|disaster|wreck|state|shambles|agony|torture|car\s+crash|"
              r"pain\s+in\s+the\s+(?:arse|bum|butt|neck|back))")
# The same thing said with one word. "sore" and "bad" are already words of pain; these are the
# rest of the ways a person says it, and none of them is ever about anything but being unwell
# when a part of the body is the subject.
BAD_WORD = (r"(?:terrible|awful|rubbish|crap|horrible|dreadful|brutal|shocking|knackered|shot|"
            r"agony|unbearable|wrecked|ruined|buggered|done\s+in)")
PART_THAT_IS_BAD = re.compile(
    r"\b(my|his|her|their|our|your)\s+("
    + "|".join(sorted(lexicon.BODY_PARTS, key=len, reverse=True))
    + r")\s+(?P<link>is|are|was|were|has\s+been|have\s+been|feels?|feels?\s+like)\s+(?:"
    + BAD_SAYING + "|" + BAD_WORD + r")\b", re.I)


# A part is said in the plural for both of its own ("my knees", "my feet"), and the verb follows
# what was typed: "my knees hurt", "my feet hurt". Two of those plurals do not end in an s.
THE_ODD_PLURALS = frozenset("feet teeth calves".split())


def _the_part_that_is_bad(match):
    part = match.group(2).lower()
    plural = part.endswith("s") or part in THE_ODD_PLURALS
    link = " ".join(str(match.group("link") or "").lower().split())
    if link in ("has been", "have been"):
        # "my back has been a nightmare for weeks" is a complaint that has gone on, and
        # "my back hurts for weeks" is not English: the tense the person used is kept, because
        # the memory keeps this line and says it back to them.
        verb = "have been hurting" if plural else "has been hurting"
        return "%s %s %s" % (match.group(1), match.group(2), verb)
    verb = "hurt" if plural else "hurts"
    return "%s %s %s" % (match.group(1), match.group(2), verb)


def _the_part_that_hurts(clean):
    """`clean` with "my back is a joke" said as "my back hurts", for the health readers."""
    return PART_THAT_IS_BAD.sub(_the_part_that_is_bad, str(clean or ""))


def _the_sugar_that_is_blood(clean):
    """`clean` with "my sugar was low" said as "my blood sugar was low", for the health readers."""
    def rewrite(match):
        tail = [word.strip(".,!?").lower() for word in match.group(2).split()]
        # A price is not a reading even when it is written in figures: "my sugar dropped to 90p",
        # "down to £1.50". Only the pence and the pound sign say so - a bare number is a meter
        # reading, which is why "my sugar is 3.9" and "dropped to 3.1" keep the blood.
        if any(SUGAR_PRICE_SHAPE.match(word) for word in tail):
            return match.group(0)
        # A number is a reading on a meter, not a spoonful: "my sugar is 3.9", "went down to 3.1".
        if any(word[:1].isdigit() for word in tail):
            return "%s blood sugar%s" % (match.group(1), match.group(2))
        near = tail[:3]
        level = [word for word in near if word in SUGAR_LEVEL]
        if level == ["rose"]:
            following = tail[tail.index("rose") + 1:]
            if following and following[0] not in SUGAR_AFTER_ROSE \
                    and not following[0][:1].isdigit():
                level = []  # "my sugar rose collapsed" is a flower, not a reading
        if level:
            for at, word in enumerate(tail):
                if word in SUGAR_LEVEL and SUGAR_PRICE & set(tail[at + 1:at + 4]):
                    return match.group(0)  # "my sugar dropped in price" is the shopping
            return "%s blood sugar%s" % (match.group(1), match.group(2))
        return match.group(0)
    return SUGAR_FIRST_PERSON.sub(rewrite, str(clean or ""))


def glued_words(token, after=None):
    """The words a glued token stands for, or None - the name a module reads.

    The reading splits these tokens for its own line, and a module that reads the line another
    way (the safety module does, in `safety._norm`) reads the same table rather than keeping one
    of its own: "whatsthe point" is the crisis line "whats the point" is, and "iwant to die" is
    "i want to die".
    """
    return _glued_words(token, after)
